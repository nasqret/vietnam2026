"""Static and no-network behavioral tests for the Helios control layer."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "scripts"
SLURM = REPO_ROOT / "slurm"
SHELL_FILES = (
    SCRIPTS / "helios_common.sh",
    SCRIPTS / "helios_probe.sh",
    SCRIPTS / "helios_sync_project.sh",
    SCRIPTS / "submit_slurm_job.sh",
    SCRIPTS / "helios_submit_job.sh",
    SCRIPTS / "helios_queue_report.sh",
    SLURM / "peano_cpu_smoke.sbatch",
    SLURM / "peano_gpu_gh200_smoke.sbatch",
    SLURM / "peano_prepare_training.sbatch",
    SLURM / "peano_train_qwen3_1_7b.sbatch",
    SLURM / "peano_eval_qwen3_1_7b.sbatch",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_shell_sources_parse() -> None:
    for path in SHELL_FILES:
        subprocess.run(["bash", "-n", str(path)], check=True)


def test_cluster_identity_and_fixed_project_root() -> None:
    common = _text(SCRIPTS / "helios_common.sh")
    assert '"plgnasqret@helios.cyfronet.pl"' in common
    assert '"plgccaiautore2026"' in common
    assert '"plgccaiautore2026-cpu"' in common
    assert '"plgccaiautore2026-gpu-gh200"' in common
    assert '"codex-control/projects/peano-lab-training"' in common

    control_text = "\n".join(_text(path) for path in SHELL_FILES)
    assert "HELIOS_REMOTE_PROJECT_ROOT" not in control_text
    assert "eval " not in control_text


def test_sync_preserves_expensive_outputs() -> None:
    sync = _text(SCRIPTS / "helios_sync_project.sh")
    assert "--delete-delay" in sync
    assert "protect /checkpoints/***" in sync
    assert "protect /results/***" in sync
    assert "protect /logs/***" in sync
    assert "protect /.venv-helios/***" in sync
    assert "protect /.cache/huggingface/***" in sync
    assert "exclude='/checkpoints/***'" in sync
    assert "exclude='/results/***'" in sync
    assert "exclude='/logs/***'" in sync
    assert "protect /.peano-source-provenance.tsv" in sync
    assert "git -C \"$repo_root\" status --porcelain" in sync


def test_submit_gate_and_manifest_are_explicit() -> None:
    local_wrapper = _text(SCRIPTS / "helios_submit_job.sh")
    remote_wrapper = _text(SCRIPTS / "submit_slurm_job.sh")
    for source in (local_wrapper, remote_wrapper):
        assert "--submit" in source
        assert "--confirm" in source
        assert "--afterok" in source
        assert "PEANO_HELIOS_CONFIRM_TOKEN" in source
    assert "--dependency=afterok:" in remote_wrapper
    assert "peano_helios_requires_dependency" in local_wrapper
    assert "peano_helios_requires_dependency" in remote_wrapper
    assert "sbatch_args=(--test-only)" in remote_wrapper
    assert "sbatch_args=(--parsable)" in remote_wrapper
    assert 'manifest="logs/submissions.tsv"' in remote_wrapper
    assert "dependency_job_id" in remote_wrapper
    assert "git_commit" in remote_wrapper
    assert "git_dirty" in remote_wrapper
    assert "sync_timestamp" in remote_wrapper
    assert ".peano-source-provenance.tsv" in remote_wrapper
    assert "script_sha256" in remote_wrapper


def test_smokes_pin_accounts_partition_and_current_bundle() -> None:
    cpu = _text(SLURM / "peano_cpu_smoke.sbatch")
    gpu = _text(SLURM / "peano_gpu_gh200_smoke.sbatch")
    assert "#SBATCH --account=plgccaiautore2026-cpu" in cpu
    assert "#SBATCH --account=plgccaiautore2026-gpu-gh200" in gpu
    assert "#SBATCH --partition=plgrid-gpu-gh200" in gpu
    assert "ML-bundle/25.10" in cpu
    assert "ML-bundle/25.10" in gpu
    assert "peano_lab.kernel.checker" in cpu
    assert "peano_lab.kernel.checker" in gpu
    assert "torch.cuda.is_available()" in gpu


def test_training_jobs_pin_hash_seed_environment_and_safe_artifacts() -> None:
    prepare = _text(SLURM / "peano_prepare_training.sbatch")
    train = _text(SLURM / "peano_train_qwen3_1_7b.sbatch")
    evaluate = _text(SLURM / "peano_eval_qwen3_1_7b.sbatch")
    for source in (prepare, train, evaluate):
        assert "#SBATCH --account=plgccaiautore2026-gpu-gh200" in source
        assert "#SBATCH --partition=plgrid-gpu-gh200" in source
        assert "ML-bundle/25.10" in source
    assert "requirements-helios.lock" in prepare
    assert "--system-site-packages" in prepare
    assert "--no-deps" in prepare
    assert "training.peano_policy.smoke" in prepare
    assert "qwen3_1_7b_smoke.toml" in prepare
    assert "HF_HOME=" in prepare
    assert "PEANO_JOB_SCRIPT=slurm/peano_prepare_training.sbatch" in prepare
    assert "PYTHONHASHSEED=20260728" in train
    assert "PYTHONHASHSEED=20260728" in evaluate
    assert "PEANO_JOB_SCRIPT=slurm/peano_train_qwen3_1_7b.sbatch" in train
    assert "PEANO_JOB_SCRIPT=slurm/peano_eval_qwen3_1_7b.sbatch" in evaluate
    assert "qwen3_1_7b_smoke.toml" in train
    assert "eval_trained_peano_policy.py" in evaluate
    assert "--sample" in evaluate


def test_no_network_behavioral_harness(tmp_path: Path) -> None:
    harness = Path(__file__).with_name("helios_control_harness.sh")
    env = os.environ.copy()
    env.pop("HELIOS_SSH_TARGET", None)
    completed = subprocess.run(
        ["bash", str(harness), str(REPO_ROOT), str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.stdout == "Helios control harness: OK\n"
