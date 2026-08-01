"""Focused integration tests for the model-v3 training admission path."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.config import CurriculumConfig, load_config  # noqa: E402
from training.peano_policy.contract import model_v1_environment  # noqa: E402
from training.peano_policy.manifest import artifact_directory_hash  # noqa: E402
from training.peano_policy.prompt import (  # noqa: E402
    PEANO_PROMPT_V3,
    PEANO_PROMPT_VERSION,
    ProofExample,
    prompt_contract_sha256,
    prompt_manifest_record,
    render_prompt,
)
import training.peano_policy.train as training  # noqa: E402


CONFIG_ROOT = REPOSITORY_ROOT / "training" / "peano_policy" / "configs"
BASE_CONFIG = CONFIG_ROOT / "qwen3_1_7b_smoke.toml"
ENVIRONMENT = model_v1_environment()


class _Tokenizer:
    eos_token_id = 99
    pad_token_id = 99

    def __len__(self) -> int:
        return 100

    def __call__(self, text: str, *, add_special_tokens: bool) -> dict[str, list[int]]:
        assert add_special_tokens is False
        return {"input_ids": [ord(character) % 47 for character in text]}


def _example(name: str, tactic: str = "refl") -> ProofExample:
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


def _v3_config():
    base = load_config(BASE_CONFIG)
    return replace(
        base,
        run=replace(
            base.run,
            name="qwen3-1.7b-peano-lora-v3-library",
            seed=20260729,
            max_train_samples=None,
            max_eval_samples=3,
            resume="never",
        ),
        trainer=replace(
            base.trainer,
            epochs=1.0,
            max_steps=-1,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=32,
            eval_steps=1000,
            save_steps=1000,
        ),
        generation=replace(base.generation, max_new_tokens=128),
        curriculum=CurriculumConfig(
            kind="model-v3-library-balanced-v1",
            selection_seed=20260729,
            synthetic_row_ceiling=12288,
            max_train_tokens=1_000_000,
            max_eval_tokens=1_000_000,
            max_train_squared_tokens=1_000_000_000,
            max_eval_squared_tokens=1_000_000_000,
            corpus_seal_path="checkpoints/corpora/test-seal",
            corpus_source_commit="a" * 40,
            corpus_prepare_job_id="172729",
            corpus_content_sha256="b" * 64,
        ),
    )


def test_legacy_preparation_retains_historical_caps_and_seeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_config(BASE_CONFIG)
    calls: list[tuple[Path, int | None, int]] = []
    train = _example("train")
    evaluation = _example("eval")
    attestation = {"legacy": True}

    monkeypatch.setattr(training, "attest_dataset", lambda *_: attestation)

    def fake_load(
        path: Path, *, max_samples: int | None, seed: int
    ) -> list[ProofExample]:
        calls.append((path, max_samples, seed))
        return [train if path.name == "train.jsonl" else evaluation]

    monkeypatch.setattr(training, "load_examples", fake_load)
    train_path = Path("/checked/train.jsonl")
    eval_path = Path("/checked/val.jsonl")

    prepared = training._prepare_examples(
        config, train_path=train_path, eval_path=eval_path
    )

    assert prepared == training.PreparedExamples(
        (train,), (evaluation,), attestation, None, None
    )
    assert calls == [
        (train_path, config.run.max_train_samples, config.run.seed),
        (eval_path, config.run.max_eval_samples, config.run.seed + 1),
    ]


def test_v3_preparation_uses_seal_selection_and_only_caps_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _v3_config()
    train = _example("selected")
    evaluation = _example("eval")
    eligibility_record = {"eligible": True}
    dataset_attestation = {"checked": True}
    curriculum_attestation = {"selected": True}
    calls: dict[str, object] = {}

    def fake_eligibility(seal: Path, **kwargs: object) -> SimpleNamespace:
        calls["seal"] = seal
        calls["eligibility"] = kwargs
        return SimpleNamespace(
            record=eligibility_record,
            dataset_attestation=dataset_attestation,
        )

    def fake_curriculum(path: Path, **kwargs: object) -> SimpleNamespace:
        calls["curriculum"] = (path, kwargs)
        return SimpleNamespace(
            examples=(train,),
            attestation=curriculum_attestation,
        )

    def fake_load(path: Path, **kwargs: object) -> list[ProofExample]:
        calls["eval"] = (path, kwargs)
        return [evaluation]

    monkeypatch.setattr(training, "verify_sealed_corpus_eligibility", fake_eligibility)
    monkeypatch.setattr(training, "load_curriculum", fake_curriculum)
    monkeypatch.setattr(training, "load_examples", fake_load)
    monkeypatch.setattr(
        training,
        "attest_dataset",
        lambda *_: pytest.fail("v3 must reuse the independently replayed seal"),
    )
    train_path = Path("/seal/data/train.jsonl")
    eval_path = Path("/seal/data/val.jsonl")

    prepared = training._prepare_examples(
        config, train_path=train_path, eval_path=eval_path
    )

    assert prepared == training.PreparedExamples(
        (train,),
        (evaluation,),
        dataset_attestation,
        eligibility_record,
        curriculum_attestation,
    )
    assert calls["curriculum"] == (
        train_path,
        {"seed": "20260729", "synthetic_row_ceiling": 12288},
    )
    assert calls["eval"] == (
        eval_path,
        {"max_samples": 3, "seed": 20260730},
    )


def test_tokenization_preserves_legacy_path_and_binds_v3_exact_tokens() -> None:
    train = _example("train")
    evaluation = _example("eval", "assumption")
    prepared = training.PreparedExamples(
        (train,), (evaluation,), {"checked": True}, None, None
    )
    legacy = load_config(BASE_CONFIG)

    old = training._tokenize_prepared_examples(
        legacy,
        prepared,
        _Tokenizer(),
        resolved_revision=legacy.model.revision,
    )
    assert old.tokenized_splits is None
    assert len(old.train) == len(old.evaluation) == 1

    v3 = _v3_config()
    current = training._tokenize_prepared_examples(
        v3,
        prepared,
        _Tokenizer(),
        resolved_revision=v3.model.revision,
    )
    assert current.tokenized_splits is not None
    assert current.tokenized_splits["train"]["rows"] == 1
    assert current.tokenized_splits["eval"]["rows"] == 1
    assert current.tokenized_splits["train"]["tokenizer"] == {
        "model_id": v3.model.model_id,
        "revision": v3.model.revision,
        "class": "_Tokenizer",
        "vocab_size": 100,
        "eos_token_id": 99,
        "pad_token_id": 99,
    }


def test_v3_tokenization_fails_closed_on_reviewed_budget() -> None:
    config = _v3_config()
    assert config.curriculum is not None
    config = replace(
        config,
        curriculum=replace(config.curriculum, max_train_tokens=1),
    )
    example = _example("too-large")
    prepared = training.PreparedExamples(
        (example,), (example,), {"checked": True}, {}, {}
    )

    with pytest.raises(ValueError, match="total token exposure"):
        training._tokenize_prepared_examples(
            config,
            prepared,
            _Tokenizer(),
            resolved_revision=config.model.revision,
        )


def test_prompt_v3_and_curriculum_cannot_be_disguised_as_the_other_lane() -> None:
    def attestation(version: int) -> dict[str, object]:
        return {
            "prompt_version": version,
            "prompt_contract": prompt_manifest_record(version),
            "prompt_contract_sha256": prompt_contract_sha256(version),
        }

    legacy = load_config(BASE_CONFIG)
    v3 = _v3_config()
    training._require_prompt_curriculum_alignment(
        legacy, attestation(PEANO_PROMPT_VERSION)
    )
    training._require_prompt_curriculum_alignment(v3, attestation(PEANO_PROMPT_V3))
    with pytest.raises(ValueError, match="enabled together"):
        training._require_prompt_curriculum_alignment(
            legacy, attestation(PEANO_PROMPT_V3)
        )
    with pytest.raises(ValueError, match="enabled together"):
        training._require_prompt_curriculum_alignment(
            v3, attestation(PEANO_PROMPT_VERSION)
        )


def test_final_v3_artifact_recheck_rejects_late_mode_mutation(
    tmp_path: Path,
) -> None:
    adapter = tmp_path / "adapter"
    tokenizer = tmp_path / "tokenizer"
    adapter.mkdir()
    tokenizer.mkdir()
    (adapter / "adapter_config.json").write_text("{}\n", encoding="utf-8")
    (adapter / "adapter_model.safetensors").write_bytes(b"safe")
    (tokenizer / "tokenizer.json").write_text("{}\n", encoding="utf-8")
    for directory in (adapter, tokenizer):
        for payload in directory.iterdir():
            payload.chmod(0o444)
        directory.chmod(0o555)
    adapter_artifacts = artifact_directory_hash(
        tmp_path, "adapter", require_protected=True
    )
    tokenizer_artifacts = artifact_directory_hash(
        tmp_path, "tokenizer", require_protected=True
    )
    training._verify_final_artifact_trees(
        tmp_path,
        adapter_artifacts,
        tokenizer_artifacts,
        require_protected=True,
    )

    adapter.chmod(0o500)
    try:
        with pytest.raises(ValueError, match="not protected as 0555"):
            training._verify_final_artifact_trees(
                tmp_path,
                adapter_artifacts,
                tokenizer_artifacts,
                require_protected=True,
            )
    finally:
        adapter.chmod(0o555)


def test_v3_schedule_is_exact_and_legacy_schedule_is_untouched() -> None:
    legacy = load_config(BASE_CONFIG)
    assert training._curriculum_schedule_preflight(
        legacy,
        train_rows=1,
        eval_rows=0,
        cuda_device_count=0,
        distributed_process_count=99,
    ) is None

    config = _v3_config()
    schedule = training._curriculum_schedule_preflight(
        config,
        train_rows=20_782,
        eval_rows=512,
        cuda_device_count=1,
        distributed_process_count=1,
    )
    assert schedule == {
        "format": "peano-policy-v3-training-schedule",
        "v": 1,
        "train_rows": 20_782,
        "eval_rows": 512,
        "cuda_devices": 1,
        "distributed_processes": 1,
        "epochs": 1.0,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 32,
        "effective_train_batch_size": 32,
        "micro_batches_per_epoch": 20_782,
        "optimizer_steps_per_epoch": 650,
        "expected_optimizer_steps": 650,
        "eval_steps": 1000,
        "save_steps": 1000,
        "periodic_evaluations": 0,
        "periodic_checkpoints": 0,
        "adapter_recovery": {
            "format": "peano-policy-adapter-recovery-plan",
            "v": 1,
            "artifact": "adapter-safetensors-only",
            "resumable": False,
            "optimizer_state_included": False,
            "interval_optimizer_steps": 100,
            "planned_optimizer_steps": [100, 200, 300, 400, 500, 600],
        },
    }


def test_production_v3_schedule_matches_the_measured_selected_rows() -> None:
    config = load_config(CONFIG_ROOT / "qwen3_1_7b_v3_library.toml")
    schedule = training._curriculum_schedule_preflight(
        config,
        train_rows=20_765,
        eval_rows=512,
        cuda_device_count=1,
        distributed_process_count=1,
    )
    assert schedule is not None
    assert schedule["micro_batches_per_epoch"] == 20_765
    assert schedule["optimizer_steps_per_epoch"] == 649
    assert schedule["expected_optimizer_steps"] == 649
    assert config.trainer.logging_steps == 11
    assert 649 % config.trainer.logging_steps == 0
    assert schedule["adapter_recovery"] == {
        "format": "peano-policy-adapter-recovery-plan",
        "v": 1,
        "artifact": "adapter-safetensors-only",
        "resumable": False,
        "optimizer_state_included": False,
        "interval_optimizer_steps": 100,
        "planned_optimizer_steps": [100, 200, 300, 400, 500, 600],
    }


def test_process_count_fails_closed_on_invalid_or_disagreeing_launchers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("WORLD_SIZE", "LOCAL_WORLD_SIZE", "SLURM_NTASKS"):
        monkeypatch.delenv(name, raising=False)
    assert training._declared_process_count() == 1

    monkeypatch.setenv("WORLD_SIZE", "1")
    monkeypatch.setenv("SLURM_NTASKS", "1")
    assert training._declared_process_count() == 1

    monkeypatch.setenv("LOCAL_WORLD_SIZE", "2")
    with pytest.raises(ValueError, match="declarations disagree"):
        training._declared_process_count()

    monkeypatch.setenv("LOCAL_WORLD_SIZE", "not-a-number")
    with pytest.raises(ValueError, match="positive decimal"):
        training._declared_process_count()


@pytest.mark.parametrize(
    ("change", "match"),
    [
        ({"cuda_device_count": 0}, "exactly one visible CUDA"),
        ({"cuda_device_count": 2}, "exactly one visible CUDA"),
        ({"distributed_process_count": 2}, "one distributed process"),
        ({"max_steps": 10}, "derive its schedule from epochs"),
        ({"epochs": 2.0}, "exactly one epoch"),
        ({"logging_steps": 9}, "divisible by logging_steps"),
        ({"eval_steps": 650}, "eval_steps must exceed"),
        ({"save_steps": 650}, "save_steps must exceed"),
    ],
)
def test_v3_schedule_rejects_unaudited_topology_or_periodic_work(
    change: dict[str, int | float], match: str
) -> None:
    config = _v3_config()
    cuda_device_count = change.get("cuda_device_count", 1)
    distributed_process_count = change.get("distributed_process_count", 1)
    trainer_change = {
        key: value
        for key, value in change.items()
        if key not in {"cuda_device_count", "distributed_process_count"}
    }
    if trainer_change:
        config = replace(config, trainer=replace(config.trainer, **trainer_change))

    with pytest.raises(ValueError, match=match):
        training._curriculum_schedule_preflight(
            config,
            train_rows=20_782,
            eval_rows=512,
            cuda_device_count=cuda_device_count,
            distributed_process_count=distributed_process_count,
        )


def test_train_orders_all_v3_gates_before_model_allocation() -> None:
    source = Path(training.__file__).read_text(encoding="utf-8")
    function = source[source.index("def train(") : source.index("def _parser(")]

    assert function.index("prepared = _prepare_examples(") < function.index(
        "tokenizer = AutoTokenizer.from_pretrained("
    )
    assert function.index("preparation_verification = _verify_preparation_reports(") < function.index(
        "tokenizer = AutoTokenizer.from_pretrained("
    )
    assert function.index("tokenization = _tokenize_prepared_examples(") < function.index(
        "model = AutoModelForCausalLM.from_pretrained("
    )
    assert function.index("schedule_preflight = _curriculum_schedule_preflight(") < function.index(
        "model = AutoModelForCausalLM.from_pretrained("
    )
    assert function.index("run_identity = _run_identity(") < function.index(
        "model = AutoModelForCausalLM.from_pretrained("
    )
    assert "_require_preparation_agreement(" in function
    assert "_require_preparation_files_unchanged(preparation_verification)" in function
    assert '"tokenized_splits": tokenization.tokenized_splits' in function
    assert '"schedule_preflight": schedule_preflight' in function
    assert "train_result.global_step" in function


def test_run_identity_persists_every_v3_admission_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("reviewed = true\n", encoding="utf-8")
    config = replace(_v3_config(), path=config_path)
    data = tmp_path / "data"
    data.mkdir()
    train_path = data / "train.jsonl"
    eval_path = data / "val.jsonl"
    manifest_path = data / "manifest.json"
    train_path.write_text("{}\n", encoding="utf-8")
    eval_path.write_text("{}\n", encoding="utf-8")
    manifest_path.write_text("{}\n", encoding="utf-8")
    attestation = {
        "prompt_version": PEANO_PROMPT_VERSION,
        "prompt_contract": prompt_manifest_record(PEANO_PROMPT_VERSION),
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_VERSION),
    }
    eligibility = {"eligibility_sha256": "c" * 64}
    curriculum = {"curriculum_sha256": "d" * 64}
    tokenized = {"train": {"record_sha256": "e" * 64}}
    schedule = {"expected_optimizer_steps": 650}
    source_snapshot = {"train": {"sha256": "1" * 64}}
    preparation = {"status": "verified", "reports": {}}
    job = {"scheduler": "none"}
    monkeypatch.setattr(
        training,
        "source_hash",
        lambda _: {"files": {}, "sha256": "f" * 64},
    )

    identity = training._run_identity(
        config,
        train_path=train_path,
        eval_path=eval_path,
        dataset_attestation=attestation,
        deployment={"commit": "a" * 40},
        corpus_eligibility=eligibility,
        curriculum_attestation=curriculum,
        tokenized_splits=tokenized,
        schedule_preflight=schedule,
        source_snapshot=source_snapshot,
        preparation_verification=preparation,
        job_identity=job,
    )

    assert identity["v"] == 5
    assert identity["config"]["resolved"]["curriculum"] == {
        "kind": config.curriculum.kind,
        "selection_seed": config.curriculum.selection_seed,
        "synthetic_row_ceiling": config.curriculum.synthetic_row_ceiling,
        "max_train_tokens": config.curriculum.max_train_tokens,
        "max_eval_tokens": config.curriculum.max_eval_tokens,
        "max_train_squared_tokens": config.curriculum.max_train_squared_tokens,
        "max_eval_squared_tokens": config.curriculum.max_eval_squared_tokens,
        "corpus_seal_path": config.curriculum.corpus_seal_path,
        "corpus_source_commit": config.curriculum.corpus_source_commit,
        "corpus_prepare_job_id": config.curriculum.corpus_prepare_job_id,
        "corpus_content_sha256": config.curriculum.corpus_content_sha256,
    }
    assert identity["inputs"]["dataset_attestation"] is attestation
    assert identity["inputs"]["corpus_eligibility"] is eligibility
    assert identity["inputs"]["curriculum_attestation"] is curriculum
    assert identity["inputs"]["tokenized_splits"] is tokenized
    assert identity["inputs"]["schedule_preflight"] is schedule
    assert identity["inputs"]["source_snapshot"] is source_snapshot
    assert identity["inputs"]["preparation_verification"] is preparation
    assert identity["output_directory"] is None
    assert identity["job"] is job


def _file_claim(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "configured_path": str(path),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def test_v3_source_snapshot_joins_loaded_files_to_both_authorities(
    tmp_path: Path,
) -> None:
    data = tmp_path / "data"
    data.mkdir()
    train_path = data / "train.jsonl"
    eval_path = data / "val.jsonl"
    manifest_path = data / "manifest.json"
    train_path.write_text("train\n", encoding="utf-8")
    eval_path.write_text("eval\n", encoding="utf-8")
    manifest_path.write_text("manifest\n", encoding="utf-8")
    train_claim = _file_claim(train_path)
    eval_claim = _file_claim(eval_path)
    manifest_claim = _file_claim(manifest_path)
    train_claim["rows"] = 1
    eval_claim["rows"] = 1
    eligibility = {
        "inputs": {
            "train": train_claim,
            "eval": eval_claim,
            "manifest": manifest_claim,
        }
    }
    curriculum = {
        "source": {
            "train": {
                "bytes": train_claim["bytes"],
                "rows": 1,
                "sha256": train_claim["sha256"],
            },
            "manifest": {
                "bytes": manifest_claim["bytes"],
                "sha256": manifest_claim["sha256"],
            },
        }
    }
    prepared = training.PreparedExamples(
        (_example("train"),),
        (_example("eval"),),
        {"checked": True},
        eligibility,
        curriculum,
    )

    snapshot = training._prepared_source_snapshot(
        _v3_config(),
        prepared,
        train_path=train_path,
        eval_path=eval_path,
    )
    assert snapshot["train"]["sha256"] == train_claim["sha256"]
    assert snapshot["eval"]["sha256"] == eval_claim["sha256"]

    train_path.write_text("replacement\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="differs from corpus eligibility"):
        training._prepared_source_snapshot(
            _v3_config(),
            prepared,
            train_path=train_path,
            eval_path=eval_path,
        )


def test_preparation_agreement_binds_reports_and_detects_replacement(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("reviewed\n", encoding="utf-8")
    config = replace(_v3_config(), path=config_path)
    report_paths = []
    report_identities = {}
    for role in ("eligibility", "token_audit", "runtime_smoke"):
        path = tmp_path / f"{role}.json"
        path.write_text(f"{role}\n", encoding="utf-8")
        report_paths.append(path)
        report_identities[role] = training._stable_file_identity(
            path, label=role
        )
    eligibility = {
        "seal": {"content_sha256": "a" * 64},
        "eligibility_sha256": "b" * 64,
    }
    curriculum = {"curriculum_sha256": "c" * 64}
    tokens = {
        "train": {"record_sha256": "d" * 64},
        "eval": {"record_sha256": "e" * 64},
    }
    prepared = training.PreparedExamples(
        (_example("train"),),
        (_example("eval"),),
        {"checked": True},
        eligibility,
        curriculum,
    )
    tokenization = training.PreparedTokenization((), (), tokens)
    verification = {
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "corpus_content_sha256": "a" * 64,
        "corpus_eligibility_sha256": "b" * 64,
        "curriculum_sha256": "c" * 64,
        "train_token_record_sha256": "d" * 64,
        "eval_token_record_sha256": "e" * 64,
        "reports": report_identities,
    }

    training._require_preparation_agreement(
        config, prepared, tokenization, verification
    )
    report_paths[1].write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="changed after verification"):
        training._require_preparation_files_unchanged(verification)


def test_stable_file_identity_rejects_path_replacement_during_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "report.json"
    replacement = tmp_path / "replacement.json"
    path.write_text("reviewed report\n", encoding="utf-8")
    replacement.write_text("different report\n", encoding="utf-8")
    real_lstat = training.os.lstat
    replaced = False

    def replace_before_path_recheck(value: object) -> os.stat_result:
        nonlocal replaced
        if not replaced and Path(value) == path:
            replacement.replace(path)
            replaced = True
        return real_lstat(value)

    monkeypatch.setattr(training.os, "lstat", replace_before_path_recheck)
    with pytest.raises(RuntimeError, match="changed while being hashed"):
        training._stable_file_identity(path, label="preparation report")
    assert replaced is True


def test_scheduled_v3_requires_reports_bound_to_ledger_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PEANO_CLUSTER_BACKEND", "wmi")
    monkeypatch.setenv("PEANO_PREPARE_JOB_ID", "99")
    job = {"scheduler": "slurm", "submission": {"dependency_job_id": "99"}}
    with pytest.raises(ValueError, match="requires preparation reports"):
        training._verify_preparation_reports(
            _v3_config(), None, job_identity=job
        )

    reports = training.PreparationReports(
        Path("eligibility"), Path("token"), Path("smoke"), "98"
    )
    with pytest.raises(ValueError, match="predecessor differs"):
        training._verify_preparation_reports(
            _v3_config(), reports, job_identity=job
        )
