"""Full-dataset tokenizer budget gate for policy training."""

from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.prompt import PromptError
from training.peano_policy.token_audit import summarize_token_lengths


class _WordTokenizer:
    eos_token_id = 99

    def __call__(self, text: str, *, add_special_tokens: bool) -> dict[str, list[int]]:
        assert add_special_tokens is False
        return {"input_ids": list(range(1, len(text.split()) + 1))}


def _example(prompt_words: int, tactic_words: int) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=" ".join(["p"] * prompt_words),
        tactic=" ".join(["t"] * tactic_words),
    )


def test_token_audit_summarizes_every_row_without_truncation() -> None:
    report = summarize_token_lengths(
        [_example(2, 1), _example(4, 1), _example(8, 1)],
        _WordTokenizer(),
        max_length=16,
    )
    assert report == {
        "rows": 3,
        "minimum": 4,
        "median": 6,
        "p95": 10,
        "p99": 10,
        "maximum": 10,
        "mean": 6.667,
        "budget": 16,
        "headroom": 6,
    }


def test_token_audit_fails_if_any_row_would_be_truncated() -> None:
    with pytest.raises(PromptError, match="does not fit max_length"):
        summarize_token_lengths(
            [_example(2, 1), _example(15, 1)],
            _WordTokenizer(),
            max_length=16,
        )


def test_token_audit_rejects_an_empty_split() -> None:
    with pytest.raises(ValueError, match="split is empty"):
        summarize_token_lengths([], _WordTokenizer(), max_length=16)
