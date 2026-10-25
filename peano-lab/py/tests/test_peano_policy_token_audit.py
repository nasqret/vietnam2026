"""Full-dataset tokenizer budget gate for policy training."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.prompt import PromptError
import training.peano_policy.token_audit as token_audit
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


def test_full_token_audit_rechecks_base_bytes_after_both_split_summaries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    events: list[str] = []
    revision = "e" * 40
    snapshot = {
        "model_id": "Qwen/Qwen3-1.7B-Base",
        "revision": revision,
        "sha256": "b" * 64,
    }
    snapshot_path = tmp_path / "hub" / "models--Qwen--Qwen3-1.7B-Base" / "snapshots" / revision
    config_path = tmp_path / "config.toml"
    train_path = tmp_path / "train.jsonl"
    eval_path = tmp_path / "val.jsonl"
    for path in (config_path, train_path, eval_path):
        path.write_text("unit\n", encoding="utf-8")
    config = SimpleNamespace(
        path=config_path,
        model=SimpleNamespace(
            model_id="Qwen/Qwen3-1.7B-Base",
            revision=revision,
            trust_remote_code=False,
        ),
        data=SimpleNamespace(
            train_path=str(train_path),
            eval_path=str(eval_path),
            max_length=32,
        ),
        run=SimpleNamespace(
            max_train_samples=None,
            max_eval_samples=None,
            seed=7,
        ),
    )

    class FakeTokenizer:
        eos_token_id = 1
        init_kwargs = {"_commit_hash": revision}

        def __len__(self) -> int:
            return 42

    class FakeAutoTokenizer:
        @staticmethod
        def from_pretrained(*args: object, **kwargs: object) -> FakeTokenizer:
            events.append("load-tokenizer")
            assert args == (str(snapshot_path),)
            assert "revision" not in kwargs
            assert "cache_dir" not in kwargs
            assert kwargs["local_files_only"] is True
            return FakeTokenizer()

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoTokenizer=FakeAutoTokenizer),
    )
    monkeypatch.setattr(
        token_audit,
        "validated_snapshot_path",
        lambda **kwargs: (snapshot_path, snapshot),
    )
    monkeypatch.setattr(
        token_audit,
        "load_examples",
        lambda path, **kwargs: ["train"] if path == train_path else ["eval"],
    )

    def summarize(examples: object, tokenizer: object, *, max_length: int) -> dict[str, int]:
        del tokenizer
        label = list(examples)[0]  # type: ignore[arg-type]
        events.append(f"summarize-{label}")
        return {"rows": 1, "budget": max_length, "headroom": 1}

    monkeypatch.setattr(token_audit, "summarize_token_lengths", summarize)

    def post_check(**kwargs: object) -> dict[str, object]:
        events.append("verify-after-audit")
        assert kwargs == {
            "model_id": "Qwen/Qwen3-1.7B-Base",
            "revision": revision,
            "hf_home": snapshot_path.parents[3],
        }
        return snapshot

    monkeypatch.setattr(token_audit, "validate_base_snapshot", post_check)

    report = token_audit.audit_config(config)

    assert events == [
        "load-tokenizer",
        "summarize-train",
        "summarize-eval",
        "verify-after-audit",
    ]
    assert report["base_snapshot"] == {
        "before_load": snapshot,
        "after_audit": snapshot,
    }
