"""Structural builder-row ingestion and completion-only tokenization.

The adjacent manifest binds bytes and row redundancy.  It is not by itself an
independent replay attestation; :mod:`training.peano_policy.attest` performs
that mandatory pre-training gate from the raw trace and metadata artifacts.
"""

from __future__ import annotations

import hashlib
import heapq
import json
from pathlib import Path
import random
from typing import Any, Mapping, Protocol

from .prompt import (
    PEANO_PROMPT_V3,
    TASK,
    CapabilityIdentity,
    PromptEnvironment,
    PromptError,
    ProofExample,
    parse_prompt,
    prompt_manifest_record,
    prompt_version_from_manifest,
    render_prompt,
    validate_completion,
)
from .contract import (
    environment_record,
    model_v3_prefix_environment,
    prompt_environment,
)

from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.library.theorems import THEOREMS


IGNORE_INDEX = -100
DATASET_FORMAT = "peano-lab-next-tactic"
DATASET_VERSION = 1
TRACE_VERSION = 1
SPLITS = ("train", "val", "test")
MAX_DATASET_LINE_BYTES = 1_000_000
ROW_FIELDS = (
    "v",
    "task",
    "env",
    "surface",
    "environment_sha256",
    "classical",
    "capabilities",
    "split",
    "session",
    "step",
    "formula",
    "theorem",
    "family",
    "lineage",
    "state",
    "focus",
    "prompt",
    "completion",
    "metadata",
)


class TokenizerLike(Protocol):
    eos_token_id: int | None

    def __call__(
        self, text: str, *, add_special_tokens: bool
    ) -> Mapping[str, list[int]]: ...


def dataset_manifest_path(dataset_path: Path) -> Path:
    """Return the builder manifest which authorizes a split artifact."""

    return dataset_path.parent / "manifest.json"


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _decode_json(text: str, *, location: str) -> object:
    try:
        return json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise PromptError(f"{location}: invalid JSON: {exc}") from exc


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _nonempty_text(label: str, value: object) -> str:
    if type(value) is not str or not value:
        raise PromptError(f"{label} must be non-empty text")
    return value


def _integer(label: str, value: object, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise PromptError(f"{label} must be an integer >= {minimum}")
    return value


def _load_manifest(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise PromptError(
            f"missing replay-validation manifest {path}; raw trace-v1 files "
            "are not positive SFT data"
        )
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PromptError(f"{path}: manifest is not valid UTF-8") from exc
    value = _decode_json(raw, location=str(path))
    if type(value) is not dict:
        raise PromptError(f"{path}: manifest must be an object")
    if value.get("format") != DATASET_FORMAT or value.get("version") != DATASET_VERSION:
        raise PromptError(f"{path}: unsupported dataset format/version")
    if value.get("trace_version") != TRACE_VERSION:
        raise PromptError(f"{path}: unsupported source trace version")

    prompt = value.get("prompt")
    try:
        prompt_version_from_manifest(prompt)
    except PromptError as exc:
        raise PromptError(f"{path}: {exc}") from exc

    source = value.get("source")
    replay = value.get("replay")
    if type(source) is not dict or type(replay) is not dict:
        raise PromptError(f"{path}: missing source/replay provenance")
    qed_sessions = source.get("qed_true_sessions")
    attempted = replay.get("attempted_qed_sessions")
    accepted = replay.get("accepted_kernel_checked_sessions")
    positives = replay.get("positive_rows")
    if not all(type(item) is int and item >= 0 for item in (
        qed_sessions,
        attempted,
        accepted,
        positives,
    )):
        raise PromptError(f"{path}: malformed replay provenance counters")
    if qed_sessions != attempted or attempted != accepted:
        raise PromptError(
            f"{path}: not every QED source session survived checked replay"
        )
    return value


def load_dataset_manifest(path: Path) -> dict[str, object]:
    """Load the structural builder manifest used by the training attestor."""

    return _load_manifest(path)


def _manifest_environments(manifest: Mapping[str, object]) -> set[tuple[str, str, bool, str]]:
    records = manifest.get("environments")
    try:
        expected_prompt_version = prompt_version_from_manifest(manifest.get("prompt"))
    except PromptError as exc:
        raise PromptError(f"manifest prompt: {exc}") from exc
    if type(records) is not list or not records:
        raise PromptError("dataset manifest has no verified environments")
    result: set[tuple[str, str, bool, str]] = set()
    for index, record in enumerate(records, 1):
        if type(record) is not dict:
            raise PromptError(f"manifest environment {index} must be an object")
        try:
            capabilities = CapabilityIdentity.from_record(record.get("capabilities"))
        except PromptError as exc:
            raise PromptError(f"manifest environment {index}: {exc}") from exc
        classical = record.get("classical")
        if type(classical) is not bool:
            raise PromptError(f"manifest environment {index}: classical must be Boolean")
        try:
            environment = prompt_environment(classical, capabilities)
        except (TypeError, ValueError) as exc:
            raise PromptError(f"manifest environment {index}: {exc}") from None
        if environment.prompt_version != expected_prompt_version:
            raise PromptError(
                f"manifest environment {index}: prompt version mismatch"
            )
        if record.get("surface") != capabilities.label:
            raise PromptError(f"manifest environment {index}: surface mismatch")
        if record.get("environment_sha256") != environment.sha256:
            raise PromptError(f"manifest environment {index}: capability hash mismatch")
        expected_record = environment_record(environment)
        if set(record) != {*expected_record, "sessions"} or any(
            record.get(key) != value for key, value in expected_record.items()
        ):
            raise PromptError(
                f"manifest environment {index}: checked authority mismatch"
            )
        _integer(
            f"manifest environment {index} sessions",
            record.get("sessions"),
            minimum=1,
        )
        result.add(
            (
                capabilities.label,
                environment.sha256,
                classical,
                environment.text,
            )
        )
    return result


def example_from_record(record: Mapping[str, Any], line_number: int) -> ProofExample:
    """Validate one *builder output row*, never a raw transition record."""

    location = f"line {line_number}"
    if type(record) is not dict:
        raise PromptError(f"{location}: JSON value must be an object")
    if tuple(record) != ROW_FIELDS:
        raise PromptError(
            f"{location}: expected replay-validated builder row fields, got "
            f"{list(record)!r}"
        )
    if record["v"] != DATASET_VERSION or type(record["v"]) is not int:
        raise PromptError(f"{location}: unsupported dataset row version")
    if record["task"] != TASK:
        raise PromptError(f"{location}: task must be {TASK!r}")
    split = record["split"]
    if split not in SPLITS or type(split) is not str:
        raise PromptError(f"{location}: invalid split")
    session = _nonempty_text(f"{location} session", record["session"])
    step = _integer(f"{location} step", record["step"], minimum=1)
    for field in ("formula", "theorem", "family", "lineage"):
        _nonempty_text(f"{location} {field}", record[field])
    if type(record["metadata"]) is not dict:
        raise PromptError(f"{location}: metadata must be an object")

    try:
        capabilities = CapabilityIdentity.from_record(record["capabilities"])
    except PromptError as exc:
        raise PromptError(f"{location}: {exc}") from exc
    classical = record["classical"]
    if type(classical) is not bool:
        raise PromptError(f"{location}: classical must be a Boolean")
    try:
        environment = prompt_environment(classical, capabilities)
    except (TypeError, ValueError) as exc:
        raise PromptError(f"{location}: {exc}") from None
    if record["surface"] != capabilities.label:
        raise PromptError(f"{location}: surface/capability label mismatch")
    if record["environment_sha256"] != environment.sha256:
        raise PromptError(f"{location}: environment capability hash mismatch")
    if record["env"] != environment.text:
        raise PromptError(f"{location}: environment text mismatch")
    identity_field = "library_identity_sha256"
    identity_present = identity_field in record["metadata"]
    row_identity = record["metadata"].get(identity_field)
    if environment.library_sha256 is None:
        if identity_present:
            raise PromptError(
                f"{location}: model-v1 row must not claim a library identity"
            )
    elif not identity_present or row_identity != environment.library_sha256:
        raise PromptError(
            f"{location}: row checked-library identity mismatch"
        )
    if environment.prompt_version == PEANO_PROMPT_V3:
        v3_metadata = {
            "library_full_identity_sha256": (
                environment.library_full_identity_sha256
            ),
            "library_prefix_length": environment.library_prefix_length,
            "library_size": environment.library_full_length,
        }
        if any(
            record["metadata"].get(key) != value
            for key, value in v3_metadata.items()
        ):
            raise PromptError(f"{location}: model-v3 prefix metadata mismatch")
        if record["metadata"].get("trajectory") == (
            "catalog-predecessor-prefix-v1"
        ):
            index = record["metadata"].get("library_target_index")
            if type(index) is not int or not 0 <= index < len(THEOREMS):
                raise PromptError(f"{location}: invalid model-v3 target index")
            spec = THEOREMS[index]
            formula, free_names = parse_formula_with_names(spec.statement)
            if free_names:
                raise PromptError(f"{location}: model-v3 target is not closed")
            if (
                record["theorem"] != spec.name
                or record["metadata"].get("library_target_name") != spec.name
                or record["formula"] != pretty_formula(formula, [])
                or environment != model_v3_prefix_environment(index)
            ):
                raise PromptError(
                    f"{location}: model-v3 target/prefix binding mismatch"
                )

    state = record["state"]
    focus = record["focus"]
    try:
        expected_prompt = render_prompt(
            goals=state,
            focus=focus,
            environment=environment,
        )
    except PromptError as exc:
        raise PromptError(f"{location}: {exc}") from exc
    prompt = record["prompt"]
    if prompt != expected_prompt:
        raise PromptError(
            f"{location}: stored prompt does not match state/environment fields"
        )
    parsed = parse_prompt(prompt)
    if (
        tuple(state) != parsed.goals
        or focus != parsed.focus
        or parsed.environment != environment.text
    ):
        raise PromptError(f"{location}: prompt round-trip mismatch")
    try:
        validate_completion(record["completion"])
        return ProofExample(
            example_id=f"{session}:{step}",
            prompt=prompt,
            completion=record["completion"],
            environment_sha256=environment.sha256,
        )
    except PromptError as exc:
        raise PromptError(f"{location}: {exc}") from exc


def load_examples(
    path: Path,
    *,
    max_samples: int | None = None,
    seed: int = 0,
    manifest_path: Path | None = None,
) -> list[ProofExample]:
    """Load one structurally validated builder split, then shuffle deterministically."""

    if max_samples is not None and (type(max_samples) is not int or max_samples <= 0):
        raise ValueError("max_samples must be a positive integer or None")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    split = path.stem
    if split not in SPLITS:
        raise PromptError("dataset split filename must be train.jsonl, val.jsonl, or test.jsonl")
    manifest_source = manifest_path or dataset_manifest_path(path)
    manifest = _load_manifest(manifest_source)
    verified_environments = _manifest_environments(manifest)

    splits = manifest.get("splits")
    if type(splits) is not dict or tuple(splits) != SPLITS:
        raise PromptError(f"{manifest_source}: malformed canonical split table")
    if type(splits.get(split)) is not dict:
        raise PromptError(f"{manifest_source}: missing {split} split provenance")
    split_record = splits[split]
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PromptError(f"cannot read dataset split {path}: {exc}") from exc
    if split_record.get("sha256") != digest.hexdigest():
        raise PromptError(f"{path}: split hash does not match replay manifest")
    examples: list[ProofExample] = []
    sample_heap: list[tuple[int, int, ProofExample]] = []
    row_count = 0
    try:
        with path.open("rb") as stream:
            for line_number, raw_line in enumerate(stream, 1):
                if len(raw_line) > MAX_DATASET_LINE_BYTES:
                    raise PromptError(
                        f"{path}:{line_number}: row exceeds the "
                        f"{MAX_DATASET_LINE_BYTES}-byte limit"
                    )
                if not raw_line.endswith(b"\n"):
                    raise PromptError(f"{path}: split must be complete JSONL")
                if raw_line == b"\n":
                    raise PromptError(f"{path}:{line_number}: blank JSONL record")
                try:
                    text = raw_line[:-1].decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise PromptError(
                        f"{path}:{line_number}: split is not valid UTF-8"
                    ) from exc
                decoded = _decode_json(text, location=f"{path}:{line_number}")
                if type(decoded) is not dict:
                    raise PromptError(f"{path}:{line_number}: row must be an object")
                example = example_from_record(decoded, line_number)
                if decoded["split"] != split:
                    raise PromptError(
                        f"{path}:{line_number}: row belongs to another split"
                    )
                identity = (
                    decoded["surface"],
                    decoded["environment_sha256"],
                    decoded["classical"],
                    decoded["env"],
                )
                if identity not in verified_environments:
                    raise PromptError(
                        f"{path}:{line_number}: row environment lacks manifest provenance"
                    )
                row_count += 1
                if max_samples is None:
                    examples.append(example)
                else:
                    rank = int.from_bytes(
                        hashlib.sha256(
                            json.dumps(
                                [seed, example.example_id],
                                ensure_ascii=False,
                                separators=(",", ":"),
                            ).encode("utf-8")
                        ).digest(),
                        "big",
                    )
                    item = (-rank, -line_number, example)
                    if len(sample_heap) < max_samples:
                        heapq.heappush(sample_heap, item)
                    elif item > sample_heap[0]:
                        heapq.heapreplace(sample_heap, item)
    except OSError as exc:
        raise PromptError(f"cannot read dataset split {path}: {exc}") from exc
    if max_samples is not None:
        examples = [item[2] for item in sample_heap]
    expected_rows = split_record.get("rows")
    if type(expected_rows) is not int or expected_rows != row_count:
        raise PromptError(f"{path}: row count does not match replay manifest")
    replay = manifest["replay"]
    total_rows = 0
    for split_name in SPLITS:
        part = splits[split_name]
        if type(part) is not dict:
            raise PromptError(
                f"{manifest_source}: malformed {split_name} split provenance"
            )
        rows = part.get("rows")
        digest = part.get("sha256")
        if (
            type(rows) is not int
            or rows < 0
            or type(digest) is not str
            or len(digest) != 64
        ):
            raise PromptError(
                f"{manifest_source}: malformed {split_name} split counters/hash"
            )
        total_rows += rows
    if replay.get("positive_rows") != total_rows:
        raise PromptError("dataset manifest positive-row total is inconsistent")
    random.Random(seed).shuffle(examples)
    return examples


def tokenize_completion(
    example: ProofExample,
    tokenizer: TokenizerLike,
    *,
    max_length: int,
) -> dict[str, list[int]]:
    """Tokenize the stored prefix/completion and mask every prefix token."""

    if max_length <= 1:
        raise ValueError("max_length must be greater than one")
    eos = tokenizer.eos_token_id
    if type(eos) is not int or eos < 0:
        raise PromptError("tokenizer must define a non-negative eos_token_id")
    prompt_ids = list(
        tokenizer(example.prompt, add_special_tokens=False)["input_ids"]
    )
    # ``</tactic>`` is the dataset envelope delimiter, not a model action.
    # Supervise exactly the parsed tactic followed by EOS so inference returns
    # the same Peano Lab command with no markup attached.
    completion_ids = list(
        tokenizer(example.tactic, add_special_tokens=False)["input_ids"]
    )
    if not prompt_ids:
        raise PromptError("tokenizer produced no prompt tokens")
    if not completion_ids:
        raise PromptError("tokenizer produced no completion tokens")
    target_ids = completion_ids + [eos]
    if len(prompt_ids) + len(target_ids) > max_length:
        raise PromptError(
            "prompt plus completion does not fit max_length; refusing to drop "
            "the task/environment prefix"
        )
    input_ids = prompt_ids + target_ids
    return {
        "input_ids": input_ids,
        "attention_mask": [1] * len(input_ids),
        "labels": [IGNORE_INDEX] * len(prompt_ids) + target_ids,
    }


__all__ = [
    "DATASET_FORMAT",
    "DATASET_VERSION",
    "IGNORE_INDEX",
    "MAX_DATASET_LINE_BYTES",
    "ROW_FIELDS",
    "dataset_manifest_path",
    "example_from_record",
    "load_examples",
    "load_dataset_manifest",
    "tokenize_completion",
]
