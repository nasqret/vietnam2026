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
    SCRIPTS / "helios_peano_policy_repl.sh",
    SLURM / "peano_cpu_smoke.sbatch",
    SLURM / "peano_gpu_gh200_smoke.sbatch",
    SLURM / "peano_prepare_training.sbatch",
    SLURM / "peano_train_qwen3_1_7b.sbatch",
    SLURM / "peano_eval_qwen3_1_7b.sbatch",
    SLURM / "peano_prepare_v2_training.sbatch",
    SLURM / "peano_train_qwen3_1_7b_v2.sbatch",
    SLURM / "peano_eval_qwen3_1_7b_v2.sbatch",
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
    # A linked checkout stores .git as a file, not a directory.
    assert "--exclude='/.git'" in sync
    assert "--exclude='/.git/'" not in sync
    assert "--exclude='__pycache__/'" in sync
    assert "refusing to change source used by active Peano jobs" in sync
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
        assert "PYTHONNOUSERSITE=1" in source
        assert '${PYTHONPATH:+' not in source
    assert "requirements-helios.lock" in prepare
    assert "--system-site-packages" not in prepare
    assert "python3 -m venv --clear .venv-helios" in prepare
    assert "PIP_FIND_LINKS" in prepare
    assert "torch" in _text(
        REPO_ROOT / "training" / "peano_policy" / "requirements-helios.lock"
    )
    assert "--only-binary=:all:" in prepare
    assert "--no-deps" in prepare
    assert "-m pip check" in prepare
    assert 'torch.__version__ == "2.9.1+cu129"' in prepare
    assert 'torch.version.cuda == "12.9"' in prepare
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


def test_heavy_v2_chain_builds_checked_data_and_uses_the_pinned_adapter() -> None:
    prepare = _text(SLURM / "peano_prepare_v2_training.sbatch")
    train = _text(SLURM / "peano_train_qwen3_1_7b_v2.sbatch")
    evaluate = _text(SLURM / "peano_eval_qwen3_1_7b_v2.sbatch")
    common = _text(SCRIPTS / "helios_common.sh")
    for source in (prepare, train, evaluate):
        assert "#SBATCH --account=plgccaiautore2026-gpu-gh200" in source
        assert "#SBATCH --partition=plgrid-gpu-gh200" in source
        assert "ML-bundle/25.10" in source
        assert "PYTHONNOUSERSITE=1" in source
    assert "PEANO_POLICY_ROWS=100000" in prepare
    assert "PEANO_POLICY_DIR=data/peano-policy-v2" in prepare
    assert "peano-policy-v2-data" in prepare
    assert "training.peano_policy.token_audit" in prepare
    assert "training.peano_policy.smoke" in prepare
    assert "qwen3_1_7b_v2_heavy.toml" in prepare
    assert "qwen3_1_7b_v2_heavy.toml" in train
    assert "qwen3-1.7b-lora-v2-heavy" in evaluate
    assert "--max-steps 32" in evaluate
    assert "slurm/peano_train_qwen3_1_7b_v2.sbatch" in common
    assert "slurm/peano_eval_qwen3_1_7b_v2.sbatch" in common


def test_helios_repl_is_fixed_dry_by_default_and_requires_confirmation() -> None:
    launcher = SCRIPTS / "helios_peano_policy_repl.sh"
    dry = subprocess.run(
        ["bash", str(launcher)],
        text=True,
        capture_output=True,
        check=True,
    )
    assert "dry run (no SSH, no allocation)" in dry.stdout
    assert "plgrid-gpu-gh200" in dry.stdout
    assert "gpu=gh200:1" in dry.stdout

    refused = subprocess.run(
        ["bash", str(launcher), "--connect"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert refused.returncode == 2
    assert "--connect --confirm PEANO-LAB-TRAINING" in refused.stderr

    remote_bypass = subprocess.run(
        ["bash", str(launcher), "--remote-run"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert remote_bypass.returncode == 2
    assert "reserved for the fixed SSH hop" in remote_bypass.stderr


def test_helios_repl_requests_one_guarded_gh200_and_fixed_loaded_client() -> None:
    source = _text(SCRIPTS / "helios_peano_policy_repl.sh")
    assert source.count("exec srun \\") == 1
    assert '--account="$PEANO_HELIOS_GPU_ACCOUNT"' in source
    assert "--partition=plgrid-gpu-gh200" in source
    assert "--nodes=1" in source
    assert "--ntasks=1" in source
    assert "--gres=gpu:1" in source
    assert "--time=04:00:00" in source
    assert "--pty" in source
    assert 'active="$(squeue -h --me --name "$repl_job_name"' in source
    assert "flock -s 8" in source
    assert "ML-bundle/25.10" in source
    assert "PYTHONNOUSERSITE=1" in source
    assert "HF_HUB_OFFLINE=1" in source
    assert "TRANSFORMERS_OFFLINE=1" in source
    assert "scripts/peano_policy_repl.py" in source
    assert "qwen3-1.7b-lora-v2-heavy" in source
    assert "training-manifest.json" in source
    assert 'exec ssh -tt -o BatchMode=yes' in source
    assert '"$@"' not in source
    assert "pa prove" not in source


def test_helios_repl_rejects_host_option_injection_even_in_dry_run() -> None:
    environment = os.environ.copy()
    environment["HELIOS_SSH_TARGET"] = "-oProxyCommand=hostile"
    rejected = subprocess.run(
        ["bash", str(SCRIPTS / "helios_peano_policy_repl.sh"), "--test-only"],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert rejected.returncode == 2
    assert "invalid HELIOS_SSH_TARGET" in rejected.stderr


def test_helios_repl_rejects_duplicate_remote_allocation_without_srun(
    tmp_path: Path,
) -> None:
    project = tmp_path / "codex-control" / "projects" / "peano-lab-training"
    adapter = (
        project
        / "results"
        / "peano-policy"
        / "qwen3-1.7b-lora-v2-heavy"
    )
    adapter.mkdir(parents=True)
    (adapter / "training-manifest.json").write_text("{}\n", encoding="utf-8")
    commands = tmp_path / "commands"
    commands.mkdir()
    squeue = commands / "squeue"
    squeue.write_text("#!/usr/bin/env bash\nprintf '123456\\n'\n", encoding="utf-8")
    squeue.chmod(0o755)
    srun = commands / "srun"
    srun.write_text(
        "#!/usr/bin/env bash\nprintf 'srun must not execute\\n' >&2\nexit 99\n",
        encoding="utf-8",
    )
    srun.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{commands}:{environment['PATH']}",
            "SCRATCH": str(tmp_path),
            "SSH_CONNECTION": "test-client test-server",
        }
    )

    duplicate = subprocess.run(
        ["bash", str(SCRIPTS / "helios_peano_policy_repl.sh"), "--remote-run"],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert duplicate.returncode == 1
    assert "already exists: 123456" in duplicate.stderr
    assert "srun must not execute" not in duplicate.stderr


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
