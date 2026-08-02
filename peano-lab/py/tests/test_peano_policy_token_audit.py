"""Full-dataset tokenizer budget gate for policy training."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.config import CurriculumConfig, load_config
from training.peano_policy.contract import model_v1_environment
from training.peano_policy.prompt import ProofExample, PromptError, render_prompt
import training.peano_policy.token_audit as token_audit_module
from training.peano_policy.token_audit import audit_config, summarize_token_lengths


CONFIG_ROOT = REPOSITORY_ROOT / "training" / "peano_policy" / "configs"
BASE_CONFIG = CONFIG_ROOT / "qwen3_1_7b_smoke.toml"
TOKENIZER_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
ENVIRONMENT = model_v1_environment()


class _WordTokenizer:
    eos_token_id = 99
    pad_token_id = 99
    init_kwargs = {"_commit_hash": TOKENIZER_REVISION}

    def __call__(self, text: str, *, add_special_tokens: bool) -> dict[str, list[int]]:
        assert add_special_tokens is False
        return {"input_ids": list(range(1, len(text.split()) + 1))}

    def __len__(self) -> int:
        return 100


def _example(prompt_words: int, tactic_words: int) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=" ".join(["p"] * prompt_words),
        tactic=" ".join(["t"] * tactic_words),
    )


def _proof_example(name: str, tactic: str = "exact h") -> ProofExample:
    prompt = render_prompt(
        goals=("⊢ 0 = 0",),
        focus=0,
        environment=ENVIRONMENT,
    )
    return ProofExample(
        example_id=name,
        prompt=prompt,
        completion=f"{tactic}</tactic>",
        environment_sha256=ENVIRONMENT.sha256,
    )


def _curriculum_config(tmp_path: Path, **gates: Any) -> Any:
    train_path = tmp_path / "train.jsonl"
    eval_path = tmp_path / "val.jsonl"
    manifest_path = tmp_path / "manifest.json"
    train_path.write_text("train bytes\n", encoding="utf-8")
    eval_path.write_text("eval bytes\n", encoding="utf-8")
    manifest_path.write_text("manifest bytes\n", encoding="utf-8")
    base = load_config(BASE_CONFIG)
    curriculum = CurriculumConfig(
        kind="model-v3-library-balanced-v1",
        selection_seed=23,
        synthetic_row_ceiling=12_288,
        max_train_tokens=gates.get("max_train_tokens", 1_000_000),
        max_eval_tokens=gates.get("max_eval_tokens", 1_000_000),
        max_train_squared_tokens=gates.get(
            "max_train_squared_tokens", 1_000_000_000
        ),
        max_eval_squared_tokens=gates.get(
            "max_eval_squared_tokens", 1_000_000_000
        ),
        corpus_seal_path="checkpoints/corpora/test",
        corpus_source_commit="a" * 40,
        corpus_prepare_job_id="172729",
        corpus_content_sha256="b" * 64,
    )
    return replace(
        base,
        run=replace(
            base.run,
            name="qwen3-1.7b-peano-lora-v3-test",
            max_train_samples=None,
            max_eval_samples=1,
        ),
        data=replace(
            base.data,
            train_path=str(train_path),
            eval_path=str(eval_path),
            max_length=4096,
        ),
        generation=replace(
            base.generation,
            max_new_tokens=gates.get("max_supervised_tokens", 16),
        ),
        curriculum=curriculum,
    )


def _install_tokenizer(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(model_id: str, **kwargs: object) -> _WordTokenizer:
            calls.append({"model_id": model_id, **kwargs})
            return _WordTokenizer()

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoTokenizer=AutoTokenizer),
    )
    return calls


def _install_curriculum_loaders(
    monkeypatch: pytest.MonkeyPatch,
    config: Any,
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    train_path = Path(config.data.train_path)
    manifest_path = train_path.parent / "manifest.json"
    attestation = {
        "format": "peano-policy-v3-curriculum",
        "v": 1,
        "source": {
            "train": {
                "name": "train.jsonl",
                "bytes": train_path.stat().st_size,
                "rows": 3,
                "sha256": hashlib.sha256(train_path.read_bytes()).hexdigest(),
            },
            "manifest": {
                "name": "manifest.json",
                "bytes": manifest_path.stat().st_size,
                "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            },
        },
        "selection": {"selection_sha256": "c" * 64},
        "selected": {
            "rows": 2,
            "ordered_example_ids_sha256": "d" * 64,
            "ordered_examples_sha256": "e" * 64,
            "selection_sha256": "c" * 64,
        },
        "curriculum_sha256": "f" * 64,
    }
    eligibility_record = {
        "format": "peano-policy-v3-sealed-corpus-eligibility",
        "version": 1,
        "eligibility_sha256": "9" * 64,
    }
    dataset_attestation = {
        "format": "peano-policy-dataset-attestation",
        "v": 2,
        "independent_replay": True,
    }
    calls: list[dict[str, object]] = []

    def fake_eligibility(seal: Path, **kwargs: object) -> SimpleNamespace:
        calls.append({"loader": "eligibility", "seal": seal, **kwargs})
        return SimpleNamespace(
            record=eligibility_record,
            dataset_attestation=dataset_attestation,
        )

    def fake_curriculum(path: Path, **kwargs: object) -> SimpleNamespace:
        calls.append({"loader": "curriculum", "path": path, **kwargs})
        return SimpleNamespace(
            examples=(_proof_example("catalog:1"), _proof_example("synthetic:1")),
            attestation=attestation,
        )

    def fake_examples(path: Path, **kwargs: object) -> list[ProofExample]:
        calls.append({"loader": "examples", "path": path, **kwargs})
        return [_proof_example("eval:1")]

    monkeypatch.setattr(token_audit_module, "load_curriculum", fake_curriculum)
    monkeypatch.setattr(token_audit_module, "load_examples", fake_examples)
    monkeypatch.setattr(
        token_audit_module,
        "verify_sealed_corpus_eligibility",
        fake_eligibility,
    )
    return attestation, eligibility_record, calls


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


def test_curriculum_audit_is_self_authorizing_and_binds_exact_tokens(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _curriculum_config(tmp_path)
    tokenizer_calls = _install_tokenizer(monkeypatch)
    attestation, eligibility, loader_calls = _install_curriculum_loaders(
        monkeypatch, config
    )

    report = audit_config(config)

    assert tokenizer_calls == [
        {
            "model_id": "Qwen/Qwen3-1.7B-Base",
            "revision": TOKENIZER_REVISION,
            "use_fast": True,
            "trust_remote_code": False,
        }
    ]
    assert report["format"] == "peano-policy-token-audit"
    assert report["v"] == token_audit_module.REPORT_VERSION == 2
    assert report["status"] == "passed"
    assert report["curriculum"] == attestation
    assert report["sealed_corpus_eligibility"] == eligibility
    assert report["sealed_dataset_attestation"] == {
        "format": "peano-policy-dataset-attestation",
        "v": 2,
        "independent_replay": True,
    }
    assert report["tokenizer"] == {
        "model_id": "Qwen/Qwen3-1.7B-Base",
        "revision": TOKENIZER_REVISION,
        "class": "_WordTokenizer",
        "vocab_size": 100,
        "eos_token_id": 99,
        "pad_token_id": 99,
    }
    assert report["compute_gates"] == {
        "max_train_tokens": 1_000_000,
        "max_eval_tokens": 1_000_000,
        "max_train_squared_tokens": 1_000_000_000,
        "max_eval_squared_tokens": 1_000_000_000,
        "max_supervised_tokens": 16,
    }
    assert report["splits"]["train"]["rows"] == 2
    assert report["splits"]["eval"]["rows"] == 1
    assert report["tokenized_splits"]["train"]["rows"] == 2
    assert report["tokenized_splits"]["eval"]["rows"] == 1
    assert report["tokenized_splits"]["train"]["tokenizer"] == report["tokenizer"]
    assert len(report["tokenized_splits"]["train"]["record_sha256"]) == 64

    inputs = report["inputs"]
    for role, name in (
        ("train", "train.jsonl"),
        ("eval", "val.jsonl"),
        ("train_manifest", "manifest.json"),
        ("eval_manifest", "manifest.json"),
    ):
        path = tmp_path / name
        assert inputs[role]["bytes"] == path.stat().st_size
        assert inputs[role]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    assert loader_calls == [
        {
            "loader": "eligibility",
            "seal": REPOSITORY_ROOT / "checkpoints/corpora/test",
            "configured_train_path": Path(config.data.train_path),
            "configured_eval_path": Path(config.data.eval_path),
            "historical_source_commit": "a" * 40,
            "historical_prepare_job_id": "172729",
            "sealed_content_sha256": "b" * 64,
        },
        {
            "loader": "curriculum",
            "path": Path(config.data.train_path),
            "seed": "23",
            "synthetic_row_ceiling": 12_288,
        },
        {
            "loader": "examples",
            "path": Path(config.data.eval_path),
            "max_samples": 1,
            "seed": config.run.seed + 1,
        },
    ]


@pytest.mark.parametrize(
    ("gate", "value", "message"),
    (
        ("max_train_tokens", 1, "total token"),
        ("max_eval_tokens", 1, "total token"),
        ("max_train_squared_tokens", 1, "quadratic token"),
        ("max_eval_squared_tokens", 1, "quadratic token"),
        ("max_supervised_tokens", 2, "supervised completion"),
    ),
)
def test_curriculum_audit_fails_closed_on_each_compute_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    gate: str,
    value: int,
    message: str,
) -> None:
    config = _curriculum_config(tmp_path, **{gate: value})
    _install_tokenizer(monkeypatch)
    _install_curriculum_loaders(monkeypatch, config)

    with pytest.raises(ValueError, match=message):
        audit_config(config)


def test_curriculum_audit_forbids_legacy_train_row_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _curriculum_config(tmp_path)
    config = replace(config, run=replace(config.run, max_train_samples=1))
    _install_tokenizer(monkeypatch)

    with pytest.raises(ValueError, match="forbids train-row subsampling"):
        audit_config(config)


def test_curriculum_audit_rejects_dataset_mutation_during_tokenization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _curriculum_config(tmp_path)
    _install_tokenizer(monkeypatch)
    _install_curriculum_loaders(monkeypatch, config)

    def mutating_eval_loader(path: Path, **_kwargs: object) -> list[ProofExample]:
        path.write_text("mutated eval bytes\n", encoding="utf-8")
        return [_proof_example("eval:1")]

    monkeypatch.setattr(token_audit_module, "load_examples", mutating_eval_loader)
    with pytest.raises(RuntimeError, match="dataset bytes changed"):
        audit_config(config)


def test_curriculum_audit_rejects_attestation_for_other_source_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _curriculum_config(tmp_path)
    _install_tokenizer(monkeypatch)
    attestation, _eligibility, _calls = _install_curriculum_loaders(
        monkeypatch, config
    )
    attestation["source"]["train"]["sha256"] = "0" * 64

    with pytest.raises(RuntimeError, match="train source differs"):
        audit_config(config)


def test_legacy_audit_keeps_the_original_v1_report_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    train_path = tmp_path / "train.jsonl"
    eval_path = tmp_path / "val.jsonl"
    train_path.write_text("legacy train\n", encoding="utf-8")
    eval_path.write_text("legacy eval\n", encoding="utf-8")
    base = load_config(BASE_CONFIG)
    config = replace(
        base,
        data=replace(
            base.data,
            train_path=str(train_path),
            eval_path=str(eval_path),
            max_length=32,
        ),
    )
    _install_tokenizer(monkeypatch)
    calls: list[tuple[Path, dict[str, object]]] = []

    def fake_examples(path: Path, **kwargs: object) -> list[SimpleNamespace]:
        calls.append((path, kwargs))
        return [_example(2, 1)]

    monkeypatch.setattr(token_audit_module, "load_examples", fake_examples)

    report = audit_config(config)

    assert set(report) == {
        "format",
        "v",
        "status",
        "config",
        "tokenizer",
        "inputs",
        "splits",
    }
    assert report["v"] == token_audit_module.LEGACY_REPORT_VERSION == 1
    assert "eos_token_id" not in report["tokenizer"]
    assert set(report["inputs"]) == {"train", "eval"}
    assert all(set(value) == {"path", "sha256"} for value in report["inputs"].values())
    assert calls == [
        (
            train_path,
            {"max_samples": config.run.max_train_samples, "seed": config.run.seed},
        ),
        (
            eval_path,
            {
                "max_samples": config.run.max_eval_samples,
                "seed": config.run.seed + 1,
            },
        ),
    ]
