"""Focused tests for exact token-exposure accounting."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.peano_policy.budget import (
    TokenBudgetError,
    enforce_token_budget,
    tokenizer_identity_record,
    tokenize_split,
)
from training.peano_policy.contract import model_v1_environment
from training.peano_policy.prompt import ProofExample, render_prompt


ENVIRONMENT = model_v1_environment()
PROMPT_TOKEN_COUNTS: dict[str, int] = {}


class _Tokenizer:
    eos_token_id = 99
    pad_token_id = 99

    def __len__(self) -> int:
        return 100

    def __call__(self, text: str, *, add_special_tokens: bool) -> dict[str, list[int]]:
        assert add_special_tokens is False
        if text in PROMPT_TOKEN_COUNTS:
            return {"input_ids": [7] * PROMPT_TOKEN_COUNTS[text]}
        return {"input_ids": [ord(character) % 31 for character in text]}


def _example(name: str, prompt_tokens: int, tactic: str) -> ProofExample:
    prompt = render_prompt(
        goals=(f"⊢ {prompt_tokens} = {prompt_tokens}",),
        focus=0,
        environment=ENVIRONMENT,
    )
    PROMPT_TOKEN_COUNTS[prompt] = prompt_tokens
    return ProofExample(
        example_id=name,
        prompt=prompt,
        completion=f"{tactic}</tactic>",
        environment_sha256=ENVIRONMENT.sha256,
    )


def test_tokenize_split_binds_exact_ids_and_exposure() -> None:
    examples = (
        _example("b", 2, "x"),
        _example("a", 1, "xyz"),
    )
    encoded, record = tokenize_split(
        examples,
        _Tokenizer(),
        role="train",
        max_length=16,
        tokenizer_identity={"revision": "r", "vocab_size": 100},
    )

    assert [len(row["input_ids"]) for row in encoded] == [4, 5]
    assert record["rows"] == 2
    assert record["sequence"] == {
        "minimum": 4,
        "median": 5,
        "p95": 5,
        "p99": 5,
        "maximum": 5,
        "mean": 4.5,
        "total": 9,
        "sum_squared": 41,
        "longest_example_id": "a",
    }
    assert record["supervision"] == {
        "minimum": 2,
        "median": 4,
        "p95": 4,
        "p99": 4,
        "maximum": 4,
        "mean": 3.0,
        "total": 6,
        "longest_example_id": "a",
    }
    enforce_token_budget(
        record,
        max_total_tokens=9,
        max_sum_squared_tokens=41,
        max_supervised_tokens=4,
    )


def test_tokenizer_identity_is_shared_and_strict() -> None:
    assert tokenizer_identity_record(
        _Tokenizer(), model_id="model", revision="revision"
    ) == {
        "model_id": "model",
        "revision": "revision",
        "class": "_Tokenizer",
        "vocab_size": 100,
        "eos_token_id": 99,
        "pad_token_id": 99,
    }


def test_token_digest_changes_when_ids_change_without_changing_lengths() -> None:
    first = _Tokenizer()

    class Shifted(_Tokenizer):
        def __call__(self, text: str, *, add_special_tokens: bool) -> dict[str, list[int]]:
            value = super().__call__(text, add_special_tokens=add_special_tokens)
            return {"input_ids": [(token + 1) % 31 for token in value["input_ids"]]}

    examples = (_example("x", 2, "go"),)
    _, left = tokenize_split(
        examples,
        first,
        role="train",
        max_length=16,
        tokenizer_identity={"revision": "r"},
    )
    _, right = tokenize_split(
        examples,
        Shifted(),
        role="train",
        max_length=16,
        tokenizer_identity={"revision": "r"},
    )
    assert left["sequence"] == right["sequence"]
    assert left["tokenized_rows_sha256"] != right["tokenized_rows_sha256"]


@pytest.mark.parametrize(
    ("limits", "match"),
    [
        ((8, 41, 4), "total token"),
        ((9, 40, 4), "quadratic token"),
        ((9, 41, 3), "supervised completion"),
    ],
)
def test_each_budget_is_enforced(limits: tuple[int, int, int], match: str) -> None:
    _, record = tokenize_split(
            (_example("b", 2, "x"), _example("a", 1, "xyz")),
        _Tokenizer(),
        role="train",
        max_length=16,
        tokenizer_identity={"revision": "r"},
    )
    with pytest.raises(TokenBudgetError, match=match):
        enforce_token_budget(
            record,
            max_total_tokens=limits[0],
            max_sum_squared_tokens=limits[1],
            max_supervised_tokens=limits[2],
        )


def test_mutated_record_and_duplicate_examples_fail_closed() -> None:
    examples = (_example("x", 1, "go"),)
    _, record = tokenize_split(
        examples,
        _Tokenizer(),
        role="eval",
        max_length=16,
        tokenizer_identity={"revision": "r"},
    )
    mutated = deepcopy(record)
    mutated["sequence"]["total"] += 1
    with pytest.raises(TokenBudgetError, match="digest"):
        enforce_token_budget(
            mutated,
            max_total_tokens=100,
            max_sum_squared_tokens=10_000,
            max_supervised_tokens=100,
        )
    with pytest.raises(TokenBudgetError, match="duplicate"):
        tokenize_split(
            examples + examples,
            _Tokenizer(),
            role="train",
            max_length=16,
            tokenizer_identity={"revision": "r"},
        )


def test_streaming_audit_can_discard_encodings_without_changing_evidence() -> None:
    examples = (_example("x", 1, "go"), _example("y", 2, "refl"))
    retained, retained_record = tokenize_split(
        examples,
        _Tokenizer(),
        role="train",
        max_length=16,
        tokenizer_identity={"revision": "r"},
    )
    discarded, discarded_record = tokenize_split(
        examples,
        _Tokenizer(),
        role="train",
        max_length=16,
        tokenizer_identity={"revision": "r"},
        retain_encodings=False,
    )

    assert retained
    assert discarded == []
    assert discarded_record == retained_record
