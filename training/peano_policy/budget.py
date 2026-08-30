"""Exact token-exposure accounting for a selected Peano curriculum.

The selector decides *which* independently checked transitions may train the
policy.  This module applies the pinned tokenizer, binds the resulting token
ids, and enforces explicit linear and quadratic exposure ceilings before a GPU
model is loaded.  The quadratic total is a conservative, model-independent
proxy for attention work; it prevents a small row count from hiding a corpus
dominated by very long prompts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import hashlib
import json
from typing import Any

from .data import IGNORE_INDEX, tokenize_completion
from .prompt import ProofExample


TOKEN_BUDGET_FORMAT = "peano-policy-token-exposure"
TOKEN_BUDGET_VERSION = 1


class TokenBudgetError(ValueError):
    """A tokenized split is malformed or exceeds its reviewed budget."""


def tokenizer_identity_record(
    tokenizer: Any,
    *,
    model_id: str,
    revision: str,
) -> dict[str, object]:
    """Return the exact small tokenizer identity used by every token gate."""

    model_id = _safe_text(model_id, "tokenizer model id")
    revision = _safe_text(revision, "tokenizer revision")
    eos = getattr(tokenizer, "eos_token_id", None)
    pad = getattr(tokenizer, "pad_token_id", None)
    try:
        size = len(tokenizer)
    except (TypeError, AttributeError) as exc:
        raise TokenBudgetError("tokenizer has no finite vocabulary size") from exc
    if type(size) is not int or size < 1:
        raise TokenBudgetError("tokenizer vocabulary size must be positive")
    if type(eos) is not int or eos < 0 or type(pad) is not int or pad < 0:
        raise TokenBudgetError("tokenizer must have non-negative EOS and pad ids")
    return {
        "model_id": model_id,
        "revision": revision,
        "class": type(tokenizer).__name__,
        "vocab_size": size,
        "eos_token_id": eos,
        "pad_token_id": pad,
    }


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise TokenBudgetError(f"token evidence is not canonical JSON: {exc}") from exc


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _positive_integer(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise TokenBudgetError(f"{label} must be a positive integer")
    return value


def _safe_text(value: object, label: str) -> str:
    if (
        type(value) is not str
        or not value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise TokenBudgetError(f"{label} must be non-empty control-free text")
    return value


def _nearest_rank(sorted_values: list[int], numerator: int, denominator: int) -> int:
    index = ((len(sorted_values) - 1) * numerator + denominator - 1) // denominator
    return sorted_values[index]


def _tokenized_row_digest(
    example_id: str,
    encoded: Mapping[str, list[int]],
    supervised_tokens: int,
) -> str:
    """Bind exact ids without retaining one giant corpus-wide JSON value.

    ``tokenize_completion`` fixes the other two arrays: the attention mask is
    all ones and labels are a masked prefix followed by the last
    ``supervised_tokens`` input ids.  Hashing that suffix length and input ids
    therefore binds the full record while avoiding threefold JSON work.
    """

    return _sha256_json(
        {
            "example_id": example_id,
            "input_ids": encoded["input_ids"],
            "supervised_tokens": supervised_tokens,
        }
    )


def tokenize_split(
    examples: Iterable[ProofExample],
    tokenizer: Any,
    *,
    role: str,
    max_length: int,
    tokenizer_identity: Mapping[str, object],
    retain_encodings: bool = True,
) -> tuple[list[dict[str, list[int]]], dict[str, object]]:
    """Tokenize one exact ordered split and return encodings plus evidence."""

    role = _safe_text(role, "split role")
    max_length = _positive_integer(max_length, "max_length")
    if type(retain_encodings) is not bool:
        raise TokenBudgetError("retain_encodings must be a Boolean")
    if not isinstance(tokenizer_identity, Mapping) or not tokenizer_identity:
        raise TokenBudgetError("tokenizer identity must be a non-empty mapping")
    # Validate/detach the identity before it enters a persistent record.
    try:
        identity = json.loads(_canonical_json(dict(tokenizer_identity)))
    except json.JSONDecodeError as exc:  # pragma: no cover - canonical JSON round-trip
        raise TokenBudgetError(f"tokenizer identity cannot round-trip: {exc}") from exc

    encoded_rows: list[dict[str, list[int]]] = []
    summaries: list[dict[str, object]] = []
    observed_ids: set[str] = set()
    for position, example in enumerate(examples):
        if not isinstance(example, ProofExample):
            raise TokenBudgetError("token budget accepts ProofExample values only")
        example_id = _safe_text(example.example_id, "example id")
        if example_id in observed_ids:
            raise TokenBudgetError(f"duplicate example id {example_id!r}")
        observed_ids.add(example_id)
        encoded = tokenize_completion(example, tokenizer, max_length=max_length)
        if set(encoded) != {"input_ids", "attention_mask", "labels"}:
            raise TokenBudgetError("tokenizer produced an unexpected training record")
        sequence_tokens = len(encoded["input_ids"])
        if (
            sequence_tokens < 2
            or len(encoded["attention_mask"]) != sequence_tokens
            or len(encoded["labels"]) != sequence_tokens
        ):
            raise TokenBudgetError("tokenizer produced inconsistent sequence lengths")
        supervised_tokens = sum(
            token != IGNORE_INDEX for token in encoded["labels"]
        )
        if supervised_tokens < 1:
            raise TokenBudgetError("tokenizer produced no supervised completion")
        summaries.append(
            {
                "example_id": example_id,
                "position": position,
                "sequence_tokens": sequence_tokens,
                "supervised_tokens": supervised_tokens,
                "token_ids_sha256": _tokenized_row_digest(
                    example_id, encoded, supervised_tokens
                ),
            }
        )
        if retain_encodings:
            encoded_rows.append(encoded)

    if not summaries:
        raise TokenBudgetError(f"{role} token split is empty")
    sequence_lengths = sorted(int(row["sequence_tokens"]) for row in summaries)
    completion_lengths = sorted(int(row["supervised_tokens"]) for row in summaries)
    longest_sequence = min(
        summaries,
        key=lambda row: (-int(row["sequence_tokens"]), str(row["example_id"])),
    )
    longest_completion = min(
        summaries,
        key=lambda row: (-int(row["supervised_tokens"]), str(row["example_id"])),
    )
    total_tokens = sum(sequence_lengths)
    squared_tokens = sum(length * length for length in sequence_lengths)
    total_supervised = sum(completion_lengths)
    ordered_evidence = [
        [
            row["example_id"],
            row["sequence_tokens"],
            row["supervised_tokens"],
            row["token_ids_sha256"],
        ]
        for row in summaries
    ]
    record: dict[str, object] = {
        "format": TOKEN_BUDGET_FORMAT,
        "v": TOKEN_BUDGET_VERSION,
        "role": role,
        "tokenizer": identity,
        "max_length": max_length,
        "rows": len(summaries),
        "order_sha256": _sha256_json(
            [str(row["example_id"]) for row in summaries]
        ),
        "tokenized_rows_sha256": _sha256_json(ordered_evidence),
        "sequence": {
            "minimum": sequence_lengths[0],
            "median": _nearest_rank(sequence_lengths, 1, 2),
            "p95": _nearest_rank(sequence_lengths, 95, 100),
            "p99": _nearest_rank(sequence_lengths, 99, 100),
            "maximum": sequence_lengths[-1],
            "mean": round(total_tokens / len(sequence_lengths), 3),
            "total": total_tokens,
            "sum_squared": squared_tokens,
            "longest_example_id": longest_sequence["example_id"],
        },
        "supervision": {
            "minimum": completion_lengths[0],
            "median": _nearest_rank(completion_lengths, 1, 2),
            "p95": _nearest_rank(completion_lengths, 95, 100),
            "p99": _nearest_rank(completion_lengths, 99, 100),
            "maximum": completion_lengths[-1],
            "mean": round(total_supervised / len(completion_lengths), 3),
            "total": total_supervised,
            "longest_example_id": longest_completion["example_id"],
        },
    }
    record["record_sha256"] = _sha256_json(record)
    return encoded_rows, record


def enforce_token_budget(
    record: Mapping[str, object],
    *,
    max_total_tokens: int,
    max_sum_squared_tokens: int,
    max_supervised_tokens: int,
) -> None:
    """Fail closed when one tokenized split exceeds any reviewed ceiling."""

    if not isinstance(record, Mapping):
        raise TokenBudgetError("token budget record must be a mapping")
    if (
        record.get("format") != TOKEN_BUDGET_FORMAT
        or record.get("v") != TOKEN_BUDGET_VERSION
    ):
        raise TokenBudgetError("token budget record has the wrong format/version")
    core = dict(record)
    claimed = core.pop("record_sha256", None)
    if claimed != _sha256_json(core):
        raise TokenBudgetError("token budget record digest mismatch")
    sequence = record.get("sequence")
    supervision = record.get("supervision")
    if not isinstance(sequence, Mapping) or not isinstance(supervision, Mapping):
        raise TokenBudgetError("token budget record lacks sequence summaries")
    ceilings = {
        "total token": (
            _positive_integer(sequence.get("total"), "record total tokens"),
            _positive_integer(max_total_tokens, "max_total_tokens"),
        ),
        "quadratic token": (
            _positive_integer(
                sequence.get("sum_squared"), "record squared token total"
            ),
            _positive_integer(
                max_sum_squared_tokens, "max_sum_squared_tokens"
            ),
        ),
        "supervised completion": (
            _positive_integer(
                supervision.get("maximum"), "record maximum supervision"
            ),
            _positive_integer(max_supervised_tokens, "max_supervised_tokens"),
        ),
    }
    for label, (actual, ceiling) in ceilings.items():
        if actual > ceiling:
            raise TokenBudgetError(
                f"{label} exposure {actual} exceeds reviewed ceiling {ceiling}"
            )


__all__ = [
    "TOKEN_BUDGET_FORMAT",
    "TOKEN_BUDGET_VERSION",
    "TokenBudgetError",
    "enforce_token_budget",
    "tokenizer_identity_record",
    "tokenize_split",
]
