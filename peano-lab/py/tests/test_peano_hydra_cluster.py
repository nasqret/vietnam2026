"""Keep Hydra's Helios GPU chain explicit, offline, and dependency guarded."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
COMMON = ROOT / "scripts" / "helios_common.sh"
PREPARE = ROOT / "slurm" / "peano_hydra_alpha_prepare.sbatch"
TRAIN = ROOT / "slurm" / "peano_hydra_alpha_train.sbatch"
EVALUATE = ROOT / "slurm" / "peano_hydra_alpha_evaluate.sbatch"
CHAIN = ROOT / "scripts" / "helios_hydra_chain.sh"


def test_alpha_cluster_sources_are_bounded_and_parse_as_shell() -> None:
    for path in (COMMON, PREPARE, TRAIN, EVALUATE, CHAIN):
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


@pytest.fixture
def chain_runtime(tmp_path: Path):
    """Run the actual chain script with isolated Git, SSH, and submitter stubs."""
    project = tmp_path / "local checkout"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    for path in (CHAIN, COMMON):
        shutil.copyfile(path, scripts / path.name)
    commands = tmp_path / "commands"
    commands.mkdir()
    calls = tmp_path / "calls.log"
    scratch = tmp_path / "scratch"
    remote = scratch / "codex-control" / "projects" / "peano-lab-training"
    remote.mkdir(parents=True)
    provenance = remote / ".peano-source-provenance.tsv"
    commit = "a" * 40
    provenance.write_text(commit + "\tfalse\t2026-08-26T00:00:00Z\n", encoding="utf-8")

    def executable(path: Path, source: str) -> None:
        path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + source, encoding="utf-8")
        path.chmod(0o755)

    executable(
        commands / "git",
        '''printf 'git %s\\n' "$*" >> "$HYDRA_CHAIN_CALLS"
[ "$1" = -C ] && [ "$2" = "$HYDRA_CHAIN_REPO" ] || exit 96
shift 2
case "$*" in
  'rev-parse --show-toplevel') printf '%s\\n' "$HYDRA_CHAIN_REPO" ;;
  'rev-parse HEAD') printf '%s\\n' "$HYDRA_CHAIN_COMMIT" ;;
  'status --porcelain --untracked-files=all')
    [ "${HYDRA_CHAIN_GIT_FAIL:-}" != 1 ] || exit 12
    [ "${HYDRA_CHAIN_DIRTY:-}" != 1 ] || printf ' M unreviewed.py\\n'
    ;;
  *) exit 97 ;;
esac
''',
    )
    executable(
        commands / "ssh",
        '''printf 'ssh %s\\n' "$*" >> "$HYDRA_CHAIN_CALLS"
[ "${!#}" = "bash -l -s -- $HYDRA_CHAIN_COMMIT" ] || exit 98
export SCRATCH="$HYDRA_CHAIN_SCRATCH"
exec bash -s -- "$HYDRA_CHAIN_COMMIT"
''',
    )
    executable(
        scripts / "helios_submit_job.sh",
        '''printf 'wrapper %s\\n' "$*" >> "$HYDRA_CHAIN_CALLS"
if [ "$1" = --test-only ]; then
  printf 'test-only accepted %s\\n' "$2"
  exit 0
fi
case "${!#}" in
  slurm/peano_hydra_alpha_prepare.sbatch) stage=prepare; job_id=101 ;;
  slurm/peano_hydra_alpha_train.sbatch) stage=train; job_id=202 ;;
  slurm/peano_hydra_alpha_evaluate.sbatch) stage=evaluate; job_id=303 ;;
  *) exit 99 ;;
esac
if [ "${HYDRA_CHAIN_FAIL_STAGE:-}" = "$stage" ]; then
  printf 'scheduler rejected %s\\n' "$stage" >&2
  exit 7
fi
if [ "${HYDRA_CHAIN_BAD_STAGE:-}" = "$stage" ]; then
  printf 'submitted job_id=not-a-job\\n'
elif [ "${HYDRA_CHAIN_DUPLICATE_STAGE:-}" = "$stage" ]; then
  printf 'submitted job_id=%s\\nsubmitted job_id=%s\\n' "$job_id" "$job_id"
else
  printf 'submitted job_id=%s\\nmanifest=logs/submissions.tsv\\n' "$job_id"
fi
''',
    )
    environment = os.environ.copy()
    environment.update(
        PATH=f"{commands}:{environment['PATH']}",
        HELIOS_SSH_TARGET="reviewed-helios",
        HYDRA_CHAIN_CALLS=str(calls),
        HYDRA_CHAIN_REPO=str(project),
        HYDRA_CHAIN_COMMIT=commit,
        HYDRA_CHAIN_SCRATCH=str(scratch),
    )

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(scripts / CHAIN.name), *args], cwd=tmp_path,
            env=environment, capture_output=True, text=True, check=False,
        )

    def recorded_calls() -> list[str]:
        return calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []

    return SimpleNamespace(
        run=run, calls=recorded_calls, environment=environment,
        provenance=provenance, commit=commit,
    )


def test_hydra_chain_defaults_to_only_three_scheduler_tests(chain_runtime) -> None:
    result = chain_runtime.run()

    assert result.returncode == 0, result.stderr
    assert "chain_status=test-only" in result.stdout
    assert chain_runtime.calls() == [
        "wrapper --test-only slurm/peano_hydra_alpha_prepare.sbatch",
        "wrapper --test-only slurm/peano_hydra_alpha_train.sbatch",
        "wrapper --test-only slurm/peano_hydra_alpha_evaluate.sbatch",
    ]


@pytest.mark.parametrize("args", [
    ("--submit",),
    ("--submit", "--confirm", "WRONG-PROJECT"),
    ("--confirm", "PEANO-LAB-TRAINING"),
    ("--submit", "--test-only"),
    ("--submit", "--confirm", "PEANO-LAB-TRAINING", "--afterok", "123"),
])
def test_hydra_chain_requires_unambiguous_confirmation_before_any_call(
    chain_runtime, args: tuple[str, ...],
) -> None:
    result = chain_runtime.run(*args)

    assert result.returncode == 2
    assert chain_runtime.calls() == []


def test_hydra_chain_submits_exact_ids_without_waiting_between_jobs(chain_runtime) -> None:
    result = chain_runtime.run("--submit", "--confirm", "PEANO-LAB-TRAINING")

    assert result.returncode == 0, result.stderr
    calls = chain_runtime.calls()
    submissions = [call for call in calls if call.startswith("wrapper ")]
    assert submissions == [
        "wrapper --submit --confirm PEANO-LAB-TRAINING slurm/peano_hydra_alpha_prepare.sbatch",
        "wrapper --submit --confirm PEANO-LAB-TRAINING --afterok 101 slurm/peano_hydra_alpha_train.sbatch",
        "wrapper --submit --confirm PEANO-LAB-TRAINING --afterok 202 slurm/peano_hydra_alpha_evaluate.sbatch",
    ]
    assert calls[-3:] == submissions
    assert len([call for call in calls if call.startswith("ssh ")]) == 1
    assert "chain_status=submitted" in result.stdout
    assert "prepare_job_id=101\ntrain_job_id=202\nevaluate_job_id=303" in result.stdout


@pytest.mark.parametrize("failure", ["dirty", "git-status-failed", "different-commit", "remote-dirty", "extra-row"])
def test_hydra_chain_rejects_unreviewed_or_unsynced_source(chain_runtime, failure: str) -> None:
    if failure == "dirty":
        chain_runtime.environment["HYDRA_CHAIN_DIRTY"] = "1"
    elif failure == "git-status-failed":
        chain_runtime.environment["HYDRA_CHAIN_GIT_FAIL"] = "1"
    elif failure == "different-commit":
        chain_runtime.provenance.write_text("b" * 40 + "\tfalse\t2026-08-26T00:00:00Z\n", encoding="utf-8")
    elif failure == "remote-dirty":
        chain_runtime.provenance.write_text(chain_runtime.commit + "\ttrue\t2026-08-26T00:00:00Z\n", encoding="utf-8")
    else:
        chain_runtime.provenance.write_text(
            chain_runtime.provenance.read_text(encoding="utf-8") + "unexpected trailing content",
            encoding="utf-8",
        )

    result = chain_runtime.run("--submit", "--confirm", "PEANO-LAB-TRAINING")

    assert result.returncode != 0
    assert not any(call.startswith("wrapper ") for call in chain_runtime.calls())
    if failure in {"dirty", "git-status-failed"}:
        assert not any(call.startswith("ssh ") for call in chain_runtime.calls())


@pytest.mark.parametrize("stage,accepted", [
    ("prepare", []),
    ("train", ["prepare_job_id=101"]),
    ("evaluate", ["prepare_job_id=101", "train_job_id=202"]),
])
def test_hydra_chain_stops_on_failure_and_reports_partial_acceptance(
    chain_runtime, stage: str, accepted: list[str],
) -> None:
    chain_runtime.environment["HYDRA_CHAIN_FAIL_STAGE"] = stage

    result = chain_runtime.run("--submit", "--confirm", "PEANO-LAB-TRAINING")

    assert result.returncode == 7
    assert "chain_status=partial" in result.stderr
    assert f"failed_stage={stage}" in result.stderr
    assert "not cancelled" in result.stderr
    for job in accepted:
        assert job in result.stderr
    submissions = [call for call in chain_runtime.calls() if call.startswith("wrapper ")]
    assert len(submissions) == len(accepted) + 1
    assert f"{stage}_job_id=unconfirmed" in result.stderr


@pytest.mark.parametrize("variable", ["HYDRA_CHAIN_BAD_STAGE", "HYDRA_CHAIN_DUPLICATE_STAGE"])
def test_hydra_chain_never_uses_a_malformed_or_ambiguous_predecessor_id(
    chain_runtime, variable: str,
) -> None:
    chain_runtime.environment[variable] = "train"

    result = chain_runtime.run("--submit", "--confirm", "PEANO-LAB-TRAINING")

    assert result.returncode == 1
    assert "no unique valid accepted job ID" in result.stderr
    assert "prepare_job_id=101" in result.stderr
    assert "train_job_id=unconfirmed" in result.stderr
    assert len([call for call in chain_runtime.calls() if call.startswith("wrapper ")]) == 2
