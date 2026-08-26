"""Framework-light completed-training evidence and model-v3 admission tests."""

from __future__ import annotations

import copy
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_policy.manifest import sha256_json
from training.peano_policy.training_evidence import (
    EVALUATION_LOSS_SEMANTICS,
    TRAINING_LOSS_SEMANTICS,
    FiniteGradientAudit,
    TrainingEvidenceError,
    adapter_update_audit_record,
    completed_training_evidence_record,
    read_strict_training_manifest,
    require_completed_training_evidence_for_prompt,
    reviewed_trainer_arguments_record,
    validate_completed_training_evidence,
)


def _runtime(accumulation: int = 32) -> dict[str, object]:
    return {
        "format": "peano-completion-only-trainer-runtime",
        "v": 1,
        "num_processes": 1,
        "visible_gpus": 1,
        "device": {"type": "cuda", "index": 0},
        "mixed_precision": "bf16",
        "distributed_type": {"name": "NO", "value": "NO"},
        "dynamo_backend": {"name": "NO", "value": "NO"},
        "plugins": {
            "deepspeed": False,
            "fsdp": False,
            "tensor_parallel": False,
        },
        "manual_trainer_accumulation": True,
        "configured_trainer_gradient_accumulation_steps": accumulation,
        "accelerator_backward_divisor": 1,
    }


def _trainer(*, logging_steps: int = 10) -> SimpleNamespace:
    return SimpleNamespace(
        args=SimpleNamespace(
            max_grad_norm=0.0,
            bf16=True,
            bf16_full_eval=False,
            save_strategy=SimpleNamespace(value="no"),
            eval_strategy=SimpleNamespace(value="no"),
            logging_nan_inf_filter=False,
            logging_steps=logging_steps,
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=32,
        )
    )


def _adapter_update() -> dict[str, object]:
    names = ("adapter.left", "adapter.right")
    return adapter_update_audit_record(
        trainable_parameter_names=names,
        initial_tensor_population_sha256="c" * 64,
        final_tensor_population_sha256="d" * 64,
        changed_parameter_names=("adapter.right",),
        final_finite_parameter_names=names,
    )


def _gradient_audit(steps: int = 20) -> dict[str, object]:
    audit = FiniteGradientAudit(
        expected_optimizer_steps=steps,
        trainable_parameter_names=("adapter.right", "adapter.left"),
    )
    for previous_global_step in range(steps):
        audit.observe_pre_optimizer_step(
            trainer_state_global_step=previous_global_step,
            raw_finite_gradient_parameter_names=(
                "adapter.left",
                "adapter.right",
            ),
            pre_clip_global_norm=0.5,
            post_clip_finite_gradient_parameter_names=(
                "adapter.left",
                "adapter.right",
            ),
        )
    return audit.record()


def _manifest(*, steps: int = 20, logging_steps: int = 10) -> dict[str, object]:
    metrics: dict[str, object] = {
        "train": {
            "train_loss": 0.75,
            "train_runtime": 12.5,
            "epoch": 1.0,
        },
        "eval": {
            "eval_loss": 0.8,
            "eval_runtime": 1.25,
            "epoch": 1.0,
        },
        "train_examples": 128,
        "eval_examples": 16,
        "expected_optimizer_steps": steps,
        "actual_optimizer_steps": steps,
    }
    runtime = _runtime()
    trainer_arguments = reviewed_trainer_arguments_record(
        _trainer(logging_steps=logging_steps)
    )
    adapter_sha256 = "a" * 64
    tokenizer_sha256 = "b" * 64
    history = [
        {
            "step": step,
            "loss": 1.0 / step,
            "learning_rate": 0.0001 * (steps - step) / steps,
            "epoch": step / steps,
        }
        for step in range(logging_steps, steps + 1, logging_steps)
    ]
    history.extend(
        (
            {**metrics["train"], "step": steps},
            {**metrics["eval"], "step": steps},
        )
    )
    evidence = completed_training_evidence_record(
        top_level_metrics=metrics,
        train_result_global_step=steps,
        trainer_state_global_step=steps,
        trainer_state_max_steps=steps,
        trainer_runtime=runtime,
        trainer_arguments=trainer_arguments,
        finite_gradient_audit=_gradient_audit(steps),
        adapter_update=_adapter_update(),
        logging_steps=logging_steps,
        log_history=history,
        adapter_sha256=adapter_sha256,
        tokenizer_sha256=tokenizer_sha256,
    )
    return {
        "v": 1,
        "prompt_version": 3,
        "runtime": {
            "trainer": runtime,
            "trainer_arguments": trainer_arguments,
        },
        "metrics": metrics,
        "adapter": {"sha256": adapter_sha256},
        "tokenizer": {"artifacts": {"sha256": tokenizer_sha256}},
        "inputs": {
            "schedule_preflight": {"expected_optimizer_steps": steps}
        },
        "training_evidence": evidence,
    }


def _reseal(evidence: dict[str, object]) -> None:
    evidence.pop("content_sha256", None)
    evidence["content_sha256"] = sha256_json(evidence)


def test_completed_training_evidence_binds_every_claim() -> None:
    manifest = _manifest()
    evidence = validate_completed_training_evidence(manifest)

    assert evidence == manifest["training_evidence"]
    assert evidence["status"] == "completed"
    assert evidence["steps"] == {
        "expected_optimizer_steps": 20,
        "top_level_actual_optimizer_steps": 20,
        "train_result_global_step": 20,
        "trainer_state_global_step": 20,
        "trainer_state_max_steps": 20,
    }
    assert [record["step"] for record in evidence["logging"]["records"]] == [
        10,
        20,
        20,
        20,
    ]
    assert (
        evidence["metrics"]["evaluation_loss_semantics"]
        == EVALUATION_LOSS_SEMANTICS
    )
    assert evidence["metrics"]["training_loss_semantics"] == (
        TRAINING_LOSS_SEMANTICS
    )


def test_finite_gradient_audit_uses_preincrement_trainer_state() -> None:
    audit = FiniteGradientAudit(
        expected_optimizer_steps=2,
        trainable_parameter_names=("right", "left"),
    )
    audit.observe_pre_optimizer_step(
        trainer_state_global_step=0,
        raw_finite_gradient_parameter_names=("left", "right"),
        pre_clip_global_norm=2.0,
        post_clip_finite_gradient_parameter_names=("left", "right"),
    )
    with pytest.raises(TrainingEvidenceError, match="exactly once in order"):
        audit.observe_pre_optimizer_step(
            trainer_state_global_step=0,
            raw_finite_gradient_parameter_names=("left", "right"),
            pre_clip_global_norm=2.0,
            post_clip_finite_gradient_parameter_names=("left", "right"),
        )
    audit.observe_pre_optimizer_step(
        trainer_state_global_step=1,
        raw_finite_gradient_parameter_names=("right", "left"),
        pre_clip_global_norm=1.0,
        post_clip_finite_gradient_parameter_names=("right", "left"),
    )
    record = audit.record()
    assert record["first_optimizer_step"] == 1
    assert record["last_optimizer_step"] == 2
    assert record["optimizer_steps_sha256"] == sha256_json([1, 2])


def test_finite_gradient_audit_rejects_missing_nonfinite_or_incomplete_population() -> None:
    with pytest.raises(TrainingEvidenceError, match="unique"):
        FiniteGradientAudit(
            expected_optimizer_steps=1,
            trainable_parameter_names=("same", "same"),
        )
    audit = FiniteGradientAudit(
        expected_optimizer_steps=2,
        trainable_parameter_names=("left", "right"),
    )
    with pytest.raises(TrainingEvidenceError, match="stable trainable population"):
        audit.observe_pre_optimizer_step(
            trainer_state_global_step=0,
            raw_finite_gradient_parameter_names=("left",),
            pre_clip_global_norm=1.0,
            post_clip_finite_gradient_parameter_names=("left",),
        )
    with pytest.raises(TrainingEvidenceError, match="incomplete"):
        audit.record()


@pytest.mark.parametrize(
    ("field", "bad"),
    (
        ("max_grad_norm", 1.0),
        ("bf16", False),
        ("bf16_full_eval", True),
        ("save_strategy", SimpleNamespace(value="steps")),
        ("eval_strategy", SimpleNamespace(value="steps")),
        ("logging_nan_inf_filter", True),
        ("logging_steps", 0),
        ("per_device_train_batch_size", 2),
        ("per_device_eval_batch_size", 2),
        ("gradient_accumulation_steps", 0),
    ),
)
def test_reviewed_trainer_arguments_are_observed_not_assumed(
    field: str,
    bad: object,
) -> None:
    trainer = _trainer()
    setattr(trainer.args, field, bad)
    with pytest.raises(TrainingEvidenceError):
        reviewed_trainer_arguments_record(trainer)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda evidence: evidence.__setitem__("status", "partial"),
        lambda evidence: evidence["steps"].__setitem__(
            "train_result_global_step", True
        ),
        lambda evidence: evidence["steps"].__setitem__(
            "trainer_state_max_steps", 19
        ),
        lambda evidence: evidence["runtime"].__setitem__(
            "accelerator_backward_divisor", 32
        ),
        lambda evidence: evidence["runtime"]["plugins"].__setitem__(
            "deepspeed", True
        ),
        lambda evidence: evidence["trainer_arguments"].__setitem__(
            "built_in_max_grad_norm", 1.0
        ),
        lambda evidence: evidence["trainer_arguments"].__setitem__(
            "save_strategy", "steps"
        ),
        lambda evidence: evidence["trainer_arguments"].__setitem__(
            "bf16_full_eval", True
        ),
        lambda evidence: evidence["gradients"].__setitem__(
            "raw_finite_optimizer_boundaries", 19
        ),
        lambda evidence: evidence["gradients"].__setitem__(
            "optimizer_steps_sha256", "0" * 64
        ),
        lambda evidence: evidence["adapter_update"].__setitem__(
            "changed_parameter_tensors", 0
        ),
        lambda evidence: evidence["adapter_update"].__setitem__(
            "final_tensor_population_sha256", "c" * 64
        ),
        lambda evidence: evidence["adapter_update"].__setitem__(
            "trainable_parameter_names_sha256", "0" * 64
        ),
        lambda evidence: evidence["metrics"].__setitem__(
            "training_loss_semantics", "global-token-nll"
        ),
        lambda evidence: evidence["metrics"].__setitem__(
            "evaluation_loss_semantics", "global-token-nll"
        ),
        lambda evidence: evidence["artifacts"].__setitem__(
            "adapter_sha256", "0" * 64
        ),
        lambda evidence: evidence.__setitem__(
            "hash_contract", {"algorithm": "md5", "canonicalization": "none"}
        ),
    ),
)
def test_semantic_mutations_fail_even_after_rehash(mutation: object) -> None:
    manifest = _manifest()
    evidence = manifest["training_evidence"]
    assert callable(mutation) and isinstance(evidence, dict)
    mutation(evidence)
    _reseal(evidence)

    with pytest.raises(TrainingEvidenceError):
        validate_completed_training_evidence(manifest)


@pytest.mark.parametrize("bad", (True, float("nan"), float("inf"), float("-inf")))
def test_nonfinite_and_boolean_logs_are_rejected_after_rehash(bad: object) -> None:
    manifest = _manifest()
    evidence = manifest["training_evidence"]
    assert isinstance(evidence, dict)
    logging = evidence["logging"]
    assert isinstance(logging, dict)
    records = logging["records"]
    assert isinstance(records, list)
    records[0]["loss"] = bad

    with pytest.raises(TrainingEvidenceError):
        validate_completed_training_evidence(manifest)


def test_missing_duplicate_and_out_of_order_logging_records_are_rejected() -> None:
    for operation in ("missing", "duplicate", "reordered"):
        manifest = _manifest()
        evidence = manifest["training_evidence"]
        assert isinstance(evidence, dict)
        logging = evidence["logging"]
        assert isinstance(logging, dict)
        records = logging["records"]
        assert isinstance(records, list)
        if operation == "missing":
            records.pop()
        elif operation == "duplicate":
            records.append(copy.deepcopy(records[-1]))
        else:
            records.reverse()
        logging["records_sha256"] = sha256_json(records)
        _reseal(evidence)
        with pytest.raises(TrainingEvidenceError):
            validate_completed_training_evidence(manifest)


def test_exact_schema_and_stale_content_hash_reject_mutation() -> None:
    manifest = _manifest()
    evidence = manifest["training_evidence"]
    assert isinstance(evidence, dict)
    evidence["unexpected"] = "field"
    with pytest.raises(TrainingEvidenceError, match="exact schema"):
        validate_completed_training_evidence(manifest)

    manifest = _manifest()
    evidence = manifest["training_evidence"]
    assert isinstance(evidence, dict)
    evidence["logging"]["records"][0]["loss"] = 123.0
    with pytest.raises(TrainingEvidenceError, match="stale or forged"):
        validate_completed_training_evidence(manifest)


def test_top_level_metrics_runtime_schedule_and_artifacts_are_cross_checked() -> None:
    mutations = (
        lambda manifest: manifest["metrics"]["train"].__setitem__(
            "train_loss", 9.0
        ),
        lambda manifest: manifest["metrics"]["eval"].__setitem__(
            "eval_loss", math.nan
        ),
        lambda manifest: manifest["metrics"].__setitem__(
            "actual_optimizer_steps", 19
        ),
        lambda manifest: manifest["runtime"]["trainer"].__setitem__(
            "configured_trainer_gradient_accumulation_steps", 16
        ),
        lambda manifest: manifest["inputs"]["schedule_preflight"].__setitem__(
            "expected_optimizer_steps", 19
        ),
        lambda manifest: manifest["adapter"].__setitem__("sha256", "0" * 64),
        lambda manifest: manifest["tokenizer"]["artifacts"].__setitem__(
            "sha256", "0" * 64
        ),
    )
    for mutation in mutations:
        manifest = _manifest()
        mutation(manifest)
        with pytest.raises(TrainingEvidenceError):
            validate_completed_training_evidence(manifest)


def test_builder_rejects_duplicate_logging_boundary_and_step_mismatch() -> None:
    manifest = _manifest()
    evidence = manifest["training_evidence"]
    assert isinstance(evidence, dict)
    metrics = manifest["metrics"]
    runtime = manifest["runtime"]["trainer"]
    with pytest.raises(TrainingEvidenceError, match="exactly once"):
        completed_training_evidence_record(
            top_level_metrics=metrics,
            train_result_global_step=20,
            trainer_state_global_step=20,
            trainer_state_max_steps=20,
            trainer_runtime=runtime,
            trainer_arguments=reviewed_trainer_arguments_record(_trainer()),
            finite_gradient_audit=evidence["gradients"],
            adapter_update=evidence["adapter_update"],
            logging_steps=10,
            log_history=[
                {"step": 10, "loss": 1.0, "learning_rate": 1e-4},
                {"step": 10, "loss": 0.9, "learning_rate": 0.0},
                {**metrics["train"], "step": 20},
                {**metrics["eval"], "step": 20},
            ],
            adapter_sha256="a" * 64,
            tokenizer_sha256="b" * 64,
        )
    with pytest.raises(TrainingEvidenceError, match="must agree"):
        completed_training_evidence_record(
            top_level_metrics=metrics,
            train_result_global_step=19,
            trainer_state_global_step=20,
            trainer_state_max_steps=20,
            trainer_runtime=runtime,
            trainer_arguments=reviewed_trainer_arguments_record(_trainer()),
            finite_gradient_audit=evidence["gradients"],
            adapter_update=evidence["adapter_update"],
            logging_steps=10,
            log_history=[],
            adapter_sha256="a" * 64,
            tokenizer_sha256="b" * 64,
        )


def test_only_model_v3_requires_completed_evidence() -> None:
    assert require_completed_training_evidence_for_prompt({"prompt_version": 1}) is None
    assert require_completed_training_evidence_for_prompt({"prompt_version": 2}) is None
    with pytest.raises(TrainingEvidenceError, match="exact schema"):
        require_completed_training_evidence_for_prompt({"prompt_version": 3})


def test_strict_manifest_reader_rejects_duplicate_keys_and_nonfinite_json(
    tmp_path: Path,
) -> None:
    path = tmp_path / "training-manifest.json"
    path.write_text('{"v":1,"v":1}\n', encoding="utf-8")
    with pytest.raises(TrainingEvidenceError, match="duplicate training-manifest"):
        read_strict_training_manifest(path)

    path.write_text('{"v":1,"metric":NaN}\n', encoding="utf-8")
    with pytest.raises(TrainingEvidenceError, match="forbidden non-finite"):
        read_strict_training_manifest(path)


def test_strict_manifest_reader_rejects_symlinks_and_nonobjects(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}\n", encoding="utf-8")
    link = tmp_path / "training-manifest.json"
    link.symlink_to(target)
    with pytest.raises(TrainingEvidenceError, match="cannot open|changed"):
        read_strict_training_manifest(link)

    list_path = target.with_name("list.json")
    list_path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(TrainingEvidenceError, match="root"):
        read_strict_training_manifest(list_path)

    hardlink = target.with_name("hardlink.json")
    os.link(target, hardlink)
    with pytest.raises(TrainingEvidenceError, match="bounded regular"):
        read_strict_training_manifest(target)
