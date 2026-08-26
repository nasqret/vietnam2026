"""Keep Hydra's Helios GPU chain explicit, offline, and dependency guarded."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
COMMON = ROOT / "scripts" / "helios_common.sh"
PREPARE = ROOT / "slurm" / "peano_hydra_alpha_prepare.sbatch"
TRAIN = ROOT / "slurm" / "peano_hydra_alpha_train.sbatch"
EVALUATE = ROOT / "slurm" / "peano_hydra_alpha_evaluate.sbatch"


def test_alpha_cluster_sources_are_bounded_and_parse_as_shell() -> None:
    for path in (COMMON, PREPARE, TRAIN, EVALUATE):
        subprocess.run(["bash", "-n", str(path)], check=True)


def test_alpha_preparation_uses_cpu_and_never_executes_a_model() -> None:
    source = PREPARE.read_text(encoding="utf-8")

    assert "#SBATCH --account=plgccaiautore2026-cpu" in source
    assert "#SBATCH --time=00:30:00" in source
    assert "--catalog-all --catalog-limit 192 --catalog-max-decisions 16" in source
    assert "--preflight --preparation-dir" in source
    assert "--preparation-dir _deploy/hydra-posttrain --check" in source
    assert "--execute" not in source
    assert "--gres=gpu" not in source


def test_alpha_preparation_uses_native_python_without_an_arm_environment(
    tmp_path: Path,
) -> None:
    commands = tmp_path / "commands"
    commands.mkdir()
    module = commands / "module"
    module.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    module.chmod(0o755)
    python = commands / "python3"
    python.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$*" >> "$HYDRA_TEST_CALLS"\n',
        encoding="utf-8",
    )
    python.chmod(0o755)
    (tmp_path / ".peano-source-provenance.tsv").write_text(
        "a" * 40 + "\tfalse\t2026-08-26T00:00:00Z\n",
        encoding="utf-8",
    )
    log = tmp_path / "python-calls.log"
    environment = os.environ.copy()
    environment.update(
        PATH=f"{commands}:{environment['PATH']}",
        SLURM_SUBMIT_DIR=str(tmp_path),
        HYDRA_TEST_CALLS=str(log),
    )

    subprocess.run(
        ["bash", str(PREPARE)],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    calls = log.read_text(encoding="utf-8").splitlines()
    assert len(calls) == 4
    assert calls[0].startswith("scripts/prepare_peano_hydra.py ")
    assert calls[1].startswith("scripts/prepare_peano_hydra_posttrain.py ")
    assert calls[2].startswith("-m training.peano_hydra.posttrain --preflight ")
    assert calls[3].startswith("scripts/eval_peano_hydra_posttrain.py ")


def test_alpha_gpu_training_is_single_device_offline_and_output_locked() -> None:
    source = TRAIN.read_text(encoding="utf-8")

    assert "#SBATCH --account=plgccaiautore2026-gpu-gh200" in source
    assert "#SBATCH --partition=plgrid-gpu-gh200" in source
    assert "#SBATCH --gres=gpu:1" in source
    assert "#SBATCH --time=02:00:00" in source
    assert "HF_HUB_OFFLINE=1" in source
    assert "TRANSFORMERS_OFFLINE=1" in source
    assert "flock -n 9" in source
    assert "--execute --preparation-dir _deploy/hydra-posttrain" in source


def test_alpha_jobs_require_reviewed_clean_source_provenance() -> None:
    for path in (PREPARE, TRAIN, EVALUATE):
        source = path.read_text(encoding="utf-8")

        assert "source_provenance=.peano-source-provenance.tsv" in source
        assert '[ "$source_dirty" != false ]' in source
        assert "explicitly clean committed source" in source
        assert "HF_HUB_OFFLINE=1" in source
        assert "TRANSFORMERS_OFFLINE=1" in source
        assert "sbatch " not in source


def test_alpha_training_and_evaluation_require_scheduler_dependencies() -> None:
    for path, requires_dependency in (
        (PREPARE, False),
        (TRAIN, True),
        (EVALUATE, True),
    ):
        relative = path.relative_to(ROOT).as_posix()
        check = subprocess.run(
            [
                "bash",
                "-c",
                'source "$1"; peano_helios_requires_dependency "$2"',
                "hydra-cluster-test",
                str(COMMON),
                relative,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert (check.returncode == 0) is requires_dependency


def test_alpha_gpu_chain_authenticates_the_exact_same_source_predecessor() -> None:
    expected = {
        TRAIN: PREPARE,
        EVALUATE: TRAIN,
    }
    for job, predecessor in expected.items():
        result = subprocess.run(
            [
                "bash",
                "-c",
                'source "$1"; peano_helios_expected_predecessor "$2"',
                "hydra-predecessor-test",
                str(COMMON),
                job.relative_to(ROOT).as_posix(),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        assert result.stdout.strip() == predecessor.relative_to(ROOT).as_posix()

    submitter = (ROOT / "scripts" / "submit_slurm_job.sh").read_text(encoding="utf-8")
    assert "peano_helios_expected_predecessor" in submitter
    assert "Hydra predecessor has no unique submission record" in submitter
    for field in (
        "predecessor_script",
        "predecessor_workdir",
        "predecessor_commit",
        "predecessor_dirty",
        "predecessor_synced",
        "predecessor_recorded_hash",
    ):
        assert field in submitter


def test_alpha_gpu_submission_refuses_missing_predecessor_before_any_ssh() -> None:
    launcher = ROOT / "scripts" / "helios_submit_job.sh"
    for job in (TRAIN, EVALUATE):
        result = subprocess.run(
            [
                "bash",
                str(launcher),
                "--submit",
                "--confirm",
                "PEANO-LAB-TRAINING",
                job.relative_to(ROOT).as_posix(),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "require --afterok JOB_ID" in result.stderr


def test_alpha_evaluation_uses_one_gpu_and_explicit_matched_execution() -> None:
    source = EVALUATE.read_text(encoding="utf-8")

    assert "#SBATCH --account=plgccaiautore2026-gpu-gh200" in source
    assert "#SBATCH --gres=gpu:1" in source
    assert "--execute-models --trained-adapter" in source
    assert "--preparation-dir _deploy/hydra-posttrain" in source
    assert "--output" in source
