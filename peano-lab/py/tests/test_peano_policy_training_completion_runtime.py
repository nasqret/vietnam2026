"""Live tensor/callback contracts used by model-v3 training completion."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import os
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

torch = pytest.importorskip("torch")

from training.peano_policy.train import (  # noqa: E402
    _FiniteGradientCallbackMixin,
    _claim_fresh_output_directory,
    _require_output_directory_unchanged,
    _require_recovery_filesystem_unchanged,
    _trainable_tensor_population_snapshot,
    _verify_recovery_filesystem_for_training,
)
from training.peano_policy.recovery import (  # noqa: E402
    run_recovery_publication_preflight,
)
from training.peano_policy.training_evidence import (  # noqa: E402
    FiniteGradientAudit,
    TrainingEvidenceError,
)


class _TwoParameterModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.left = torch.nn.Parameter(torch.tensor([1.0, 2.0]))
        self.right = torch.nn.Parameter(torch.tensor([3.0]))


def _named(model: torch.nn.Module) -> list[tuple[str, object]]:
    return [
        (name, parameter)
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    ]


def test_tensor_population_fingerprint_detects_one_real_update() -> None:
    model = _TwoParameterModel()
    initial = _trainable_tensor_population_snapshot(torch, _named(model))
    with torch.no_grad():
        model.right.add_(0.25)
    final = _trainable_tensor_population_snapshot(torch, _named(model))

    assert initial.names == ("left", "right") == final.names
    assert initial.population_sha256 != final.population_sha256
    before = dict(initial.record_hashes)
    after = dict(final.record_hashes)
    assert [name for name in final.names if before[name] != after[name]] == [
        "right"
    ]


def test_tensor_population_fingerprint_rejects_nonfinite_or_duplicate_names() -> None:
    model = _TwoParameterModel()
    model.left.data[0] = float("nan")
    with pytest.raises(TrainingEvidenceError, match="non-finite"):
        _trainable_tensor_population_snapshot(torch, _named(model))

    parameter = torch.nn.Parameter(torch.tensor([1.0]))
    with pytest.raises(TrainingEvidenceError, match="unique"):
        _trainable_tensor_population_snapshot(
            torch,
            [("same", parameter), ("same", parameter)],
        )


def test_pre_optimizer_callback_audits_raw_clips_strictly_and_audits_postclip() -> None:
    model = _TwoParameterModel()
    named = _named(model)
    model.left.grad = torch.tensor([3.0, 4.0])
    model.right.grad = torch.tensor([0.0])
    audit = FiniteGradientAudit(
        expected_optimizer_steps=1,
        trainable_parameter_names=(name for name, _ in named),
    )
    callback = _FiniteGradientCallbackMixin(
        torch=torch,
        named_parameters=named,
        audit=audit,
    )
    control = object()
    returned = callback.on_pre_optimizer_step(
        object(),
        SimpleNamespace(is_world_process_zero=True, global_step=0),
        control,
        model=model,
    )

    assert returned is control
    record = audit.record()
    assert record["observed_optimizer_boundaries"] == 1
    assert record["records"][0]["pre_clip_global_norm"] == pytest.approx(5.0)
    post_norm = torch.linalg.vector_norm(
        torch.cat([parameter.grad.flatten() for _, parameter in named])
    )
    assert float(post_norm) <= 1.000001


@pytest.mark.parametrize("failure", ["missing", "nonfinite"])
def test_pre_optimizer_callback_rejects_bad_raw_gradient_before_clip(
    failure: str,
) -> None:
    model = _TwoParameterModel()
    named = _named(model)
    model.left.grad = torch.ones_like(model.left)
    model.right.grad = (
        None
        if failure == "missing"
        else torch.tensor([float("inf")])
    )
    audit = FiniteGradientAudit(
        expected_optimizer_steps=1,
        trainable_parameter_names=(name for name, _ in named),
    )
    callback = _FiniteGradientCallbackMixin(
        torch=torch,
        named_parameters=named,
        audit=audit,
    )
    pattern = "missing" if failure == "missing" else "non-finite"
    with pytest.raises(TrainingEvidenceError, match=pattern):
        callback.on_pre_optimizer_step(
            object(),
            SimpleNamespace(is_world_process_zero=True, global_step=0),
            object(),
            model=model,
        )
    with pytest.raises(TrainingEvidenceError, match="incomplete"):
        audit.record()


def test_training_runner_wires_clip_before_recovery_and_manifest_admission() -> None:
    source = (ROOT / "training" / "peano_policy" / "train.py").read_text(
        encoding="utf-8"
    )
    finite_callback = source.index("callbacks.append(\n            FiniteGradientCallback(")
    recovery_callback = source.index("callbacks.append(\n            AdapterRecoveryCallback(")
    train_call = source.index("train_result = trainer.train(")
    final_population = source.index("final_tensor_population =")
    final_save = source.index("model.save_pretrained(adapter_staging")
    adapter_publication = source.index(
        "publish_staged_directory_noreplace(adapter_staging, adapter_output)"
    )
    post_serialization = source.index("post_serialization_tensor_population =")
    post_evaluation = source.index("post_evaluation_tensor_population =")
    evidence = source.index("training_evidence = completed_training_evidence_record(")
    capture = source.index("in_memory_policy = capture_in_memory_policy(")
    release = source.index("del callbacks, named_trainable, trainer, model, tokenizer")
    admission = source.index("adapter_admission = admit_saved_adapter(")
    final_artifact_recheck = source.rindex("_verify_final_artifact_trees(")
    publication = source.index("write_manifest_noreplace(manifest_path, manifest)")

    assert finite_callback < recovery_callback < train_call
    assert (
        train_call
        < final_population
        < final_save
        < adapter_publication
        < post_serialization
        < post_evaluation
        < evidence
        < capture
        < release
        < admission
        < final_artifact_recheck
        < publication
    )
    assert "max_grad_norm=(0.0 if schedule_preflight is not None else 1.0)" in source
    assert '"trainer_arguments": trainer_arguments' in source
    assert '"training_evidence": training_evidence' in source
    assert '"adapter_admission": adapter_admission' in source
    assert source.count(
        "require_protected=(schedule_preflight is not None)"
    ) == 3


def test_training_binds_live_recovery_probe_on_exact_output_filesystem(
    tmp_path: Path,
) -> None:
    output_parent = tmp_path / "results" / "peano-policy"
    probe_root = output_parent / "recovery-publication-preflights"
    probe_root.mkdir(parents=True)
    output_dir = output_parent / "adapter-run"
    report = tmp_path / "recovery.json"
    run_recovery_publication_preflight(probe_root, report_path=report)

    verification = _verify_recovery_filesystem_for_training(
        SimpleNamespace(curriculum=object()),
        report,
        output_dir=output_dir,
        job_identity={"scheduler": "none"},
    )
    assert verification is not None
    assert verification["report"]["path"] == str(report.resolve())
    _require_recovery_filesystem_unchanged(verification)


def test_training_claims_one_output_inode_and_rejects_path_or_mode_swap(
    tmp_path: Path,
) -> None:
    output = tmp_path / "results" / "one-shot"
    identity = _claim_fresh_output_directory(output)
    _require_output_directory_unchanged(identity)

    output.chmod(0o755)
    with pytest.raises(RuntimeError, match="changed during"):
        _require_output_directory_unchanged(identity)
    output.chmod(0o700)
    _require_output_directory_unchanged(identity)

    displaced = output.with_name("displaced")
    output.rename(displaced)
    os.symlink(displaced, output, target_is_directory=True)
    with pytest.raises(RuntimeError, match="changed during"):
        _require_output_directory_unchanged(identity)


def test_scheduled_v3_requires_recovery_probe_and_legacy_rejects_one(
    tmp_path: Path,
) -> None:
    output_parent = tmp_path / "results" / "peano-policy"
    output_parent.mkdir(parents=True)
    output_dir = output_parent / "adapter-run"
    with pytest.raises(ValueError, match="requires a recovery filesystem"):
        _verify_recovery_filesystem_for_training(
            SimpleNamespace(curriculum=object()),
            None,
            output_dir=output_dir,
            job_identity={"scheduler": "slurm"},
        )
    with pytest.raises(ValueError, match="only for model-v3"):
        _verify_recovery_filesystem_for_training(
            SimpleNamespace(curriculum=None),
            tmp_path / "report.json",
            output_dir=output_dir,
            job_identity={"scheduler": "none"},
        )


def test_wmi_training_script_runs_and_passes_no_replace_preflight() -> None:
    source = (
        ROOT / "slurm" / "peano_wmi_train_qwen3_1_7b_v3.sbatch"
    ).read_text(encoding="utf-8")
    run = source.index("scripts/preflight_recovery_publication.py run")
    verify = source.index("scripts/preflight_recovery_publication.py verify")
    train = source.index("-m training.peano_policy.train")
    assert run < verify < train
    assert "--recovery-publication-preflight-report" in source
    assert "recovery-publication-preflights" in source
    assert ".qwen3-1.7b-v3-training.lock" in source
    assert "flock -n 9" in source
