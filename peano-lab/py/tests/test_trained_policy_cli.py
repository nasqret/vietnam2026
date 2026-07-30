"""Model-free tests for arbitrary-theorem trained-policy publication."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPOSITORY_ROOT / "scripts" / "eval_trained_peano_policy.py"
SPEC = importlib.util.spec_from_file_location("_trained_policy_cli", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CLI
SPEC.loader.exec_module(CLI)

from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_HELD_OUT_POLICY_GOALS,
    model_v1_environment,
)
from training.peano_policy.prompt import (  # noqa: E402
    CapabilityIdentity,
    PromptEnvironment,
)


class _ReflPolicy:
    name = "test-refl"

    def propose(self, goals_before, *, sample, step, rng):  # type: ignore[no-untyped-def]
        del goals_before, sample, step, rng
        return "refl"


class _StopPolicy:
    name = "test-stop"

    def propose(self, goals_before, *, sample, step, rng):  # type: ignore[no-untyped-def]
        del goals_before, sample, step, rng
        return None


def _report(policy: object) -> object:
    statement = CLI._preflight_user_theorem("0=0")
    goal = CLI._user_goal(statement, model_v1_environment())
    return CLI.evaluator.evaluate(policy, (goal,), k=1, max_steps=2, seed=7)


def test_arbitrary_closed_theorem_publishes_exact_kernel_replay() -> None:
    publication, script = CLI._checked_proof_publication(_report(_ReflPolicy()))

    assert script == "pa prove 0 = 0\nrefl\nqed\n"
    assert publication["status"] == "proof"
    assert publication["commands"] == ["refl"]
    assert publication["replay"]["status"] == "proved"
    assert publication["replay"]["kernel_checked"] is True
    assert publication["proof_nodes"] == publication["replay"]["proof_nodes"]


def test_user_source_is_retained_while_publication_is_canonical() -> None:
    source = "forall n. n <= n"
    checked_source = CLI._preflight_user_theorem(source)
    goal = CLI._user_goal(checked_source, model_v1_environment())

    assert checked_source == source
    assert goal.statement == source
    assert CLI.evaluator._parse_closed_goal(goal)[2] == "∀ x. x ≤ x"


def test_no_proof_has_no_publishable_script() -> None:
    publication, script = CLI._checked_proof_publication(_report(_StopPolicy()))

    assert publication == {"status": "no-proof"}
    assert script is None


def test_forged_success_is_rejected_by_second_kernel_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        CLI,
        "verify_proof",
        lambda *args, **kwargs: SimpleNamespace(
            status="kernel_rejection",
            kernel_checked=False,
            theorem="0 = 0",
            proof_nodes=None,
            tactics_applied=0,
            failed_tactics=0,
            surface="model-v1",
            environment_sha256="0" * 64,
        ),
    )

    with pytest.raises(RuntimeError, match="failed exact kernel replay"):
        CLI._checked_proof_publication(_report(_ReflPolicy()))


@pytest.mark.parametrize(
    "statement",
    (
        "x = x",
        " 0 = 0",
        "0 = 0\n",
        "0 = \u202e0",
        "257 = 257",
        "forall . 0 = 0",
        "(" * 1_500 + "0 = 0" + ")" * 1_500,
        "S " * 2_001 + "0 = 0",
    ),
)
def test_user_theorem_preflight_rejects_unsafe_or_unbounded_input(
    statement: str,
) -> None:
    with pytest.raises(ValueError):
        CLI._preflight_user_theorem(statement)


def test_user_goal_cannot_widen_attested_model_authority() -> None:
    exact = model_v1_environment()
    changed = PromptEnvironment(
        False,
        CapabilityIdentity(
            label="model-v1",
            allowed_commands=(),
            allowed_theorems=exact.capabilities.allowed_theorems,
        ),
    )

    with pytest.raises(ValueError, match="fixed intuitionistic model-v1"):
        CLI._user_goal("0 = 0", changed)


def test_model_v3_selects_only_its_separately_sealed_unseen_goals() -> None:
    environment = SimpleNamespace(
        prompt_version=3,
        capabilities=SimpleNamespace(
            label="model-v3",
            allowed_theorems=(),
        ),
    )
    goals = CLI._selected_benchmark_goals([], environment)

    assert tuple(goal.name for goal in goals) == tuple(
        name for name, _ in MODEL_V3_HELD_OUT_POLICY_GOALS
    )
    assert all(goal.surface_profile == "model-v3" for goal in goals)
    assert not {goal.name for goal in goals} & set(
        CLI.evaluator.HELD_OUT_LADDER_NAMES
    )
    with pytest.raises(ValueError, match="unknown held-out"):
        CLI._selected_benchmark_goals(["mod5_fourth_power_one"], environment)


def test_atomic_proof_output_never_replaces_existing_text(tmp_path: Path) -> None:
    output = tmp_path / "proof.pa"
    CLI._atomic_create_text(output, "first\n")
    assert output.read_text(encoding="utf-8") == "first\n"

    with pytest.raises(FileExistsError, match="refusing to replace"):
        CLI._atomic_create_text(output, "second\n")
    assert output.read_text(encoding="utf-8") == "first\n"


def test_outputs_cannot_alias_nest_or_mutate_model_inputs(tmp_path: Path) -> None:
    adapter = tmp_path / "trained"
    with pytest.raises(ValueError, match="closed adapter"):
        CLI._validate_output_location(adapter / "adapter" / "proof.pa", adapter)
    with pytest.raises(ValueError, match="results"):
        CLI._validate_output_location(
            REPOSITORY_ROOT / "scripts" / "proof.pa",
            adapter,
        )
    CLI._validate_output_location(
        REPOSITORY_ROOT / "results" / "user-proofs" / "proof.pa",
        adapter,
    )


def test_scheduled_evaluation_is_bound_to_manifest_training_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = {
        "runtime": {
            "job": {
                "scheduler": "slurm",
                "job_id": "173100",
            }
        }
    }
    evaluation_job = {
        "scheduler": "slurm",
        "job_id": "173101",
        "submission": {"dependency_job_id": "173100"},
    }
    monkeypatch.setenv("SLURM_JOB_ID", "173101")
    monkeypatch.setenv("PEANO_TRAIN_JOB_ID", "173100")

    assert CLI._require_training_job_binding(manifest, evaluation_job) == {
        "status": "slurm-bound",
        "training_manifest_job_id": "173100",
        "evaluation_job_id": "173101",
        "dependency_job_id": "173100",
    }


@pytest.mark.parametrize(
    ("manifest_job", "dependency", "current", "predecessor"),
    (
        ("173099", "173100", "173101", "173100"),
        ("173100", "173099", "173101", "173100"),
        ("173100", "173100", "173102", "173100"),
        ("173100", "173100", "173101", "not-a-job"),
    ),
)
def test_scheduled_evaluation_rejects_every_training_job_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    manifest_job: str,
    dependency: str,
    current: str,
    predecessor: str,
) -> None:
    manifest = {
        "runtime": {
            "job": {
                "scheduler": "slurm",
                "job_id": manifest_job,
            }
        }
    }
    evaluation_job = {
        "scheduler": "slurm",
        "job_id": "173101",
        "submission": {"dependency_job_id": dependency},
    }
    monkeypatch.setenv("SLURM_JOB_ID", current)
    monkeypatch.setenv("PEANO_TRAIN_JOB_ID", predecessor)

    with pytest.raises(RuntimeError, match="training (?:predecessor|job)"):
        CLI._require_training_job_binding(manifest, evaluation_job)


def test_local_evaluation_is_explicitly_unbound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    monkeypatch.delenv("PEANO_TRAIN_JOB_ID", raising=False)

    assert CLI._require_training_job_binding({}, {"scheduler": "none"}) == {
        "status": "local-unbound"
    }


def test_scheduled_proof_request_binds_completed_manifest_without_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = {
        "runtime": {
            "job": {
                "scheduler": "slurm",
                "job_id": "173100",
            }
        }
    }
    evaluation_job = {
        "scheduler": "slurm",
        "job_id": "173105",
        "submission": {"dependency_job_id": ""},
    }
    monkeypatch.setenv("SLURM_JOB_ID", "173105")
    monkeypatch.delenv("PEANO_TRAIN_JOB_ID", raising=False)
    monkeypatch.setenv("PEANO_PROOF_REQUEST_ID", "a" * 64)

    assert CLI._require_training_job_binding(manifest, evaluation_job) == {
        "status": "slurm-proof-request-bound",
        "training_manifest_job_id": "173100",
        "evaluation_job_id": "173105",
        "dependency_job_id": None,
    }


def test_nested_or_symlink_aliased_outputs_fail_before_model_loading(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        CLI,
        "load_adapter",
        lambda *args, **kwargs: pytest.fail("adapter must not load"),
    )
    nested_report = tmp_path / "attempt"
    with pytest.raises(SystemExit) as nested:
        CLI.main(
            [
                "--adapter",
                "missing",
                "--theorem",
                "0 = 0",
                "--output",
                str(nested_report),
                "--proof-output",
                str(nested_report / "proof.pa"),
            ]
        )
    assert nested.value.code == 2

    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(SystemExit) as aliased:
        CLI.main(
            [
                "--adapter",
                "missing",
                "--theorem",
                "0 = 0",
                "--output",
                str(real / "same"),
                "--proof-output",
                str(alias / "same"),
            ]
        )
    assert aliased.value.code == 2

def test_invalid_cli_input_is_rejected_before_adapter_loading(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    called = False

    def forbidden_load(*args: object, **kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("adapter must not load")

    monkeypatch.setattr(CLI, "load_adapter", forbidden_load)
    with pytest.raises(SystemExit) as malformed:
        CLI.main(["--adapter", "missing", "--theorem", "x = x"])
    assert malformed.value.code == 2
    assert called is False

    occupied = tmp_path / "proof.pa"
    occupied.write_text("keep\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="proof script"):
        CLI.main(
            [
                "--adapter",
                "missing",
                "--theorem",
                "0 = 0",
                "--proof-output",
                str(occupied),
            ]
        )
    assert occupied.read_text(encoding="utf-8") == "keep\n"
    assert called is False


def test_arbitrary_rollout_bounds_are_checked_before_model_loading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        CLI,
        "load_adapter",
        lambda *args, **kwargs: pytest.fail("adapter must not load"),
    )
    for arguments in (
        ("--k", "257", "--sample"),
        ("--max-steps", "1025"),
        ("--k", "2"),
    ):
        with pytest.raises(SystemExit) as rejected:
            CLI.main(
                ["--adapter", "missing", "--theorem", "0 = 0", *arguments]
            )
        assert rejected.value.code == 2

    for arguments in (
        ("--k", "256", "--max-steps", "17", "--sample"),
        (
            "--k",
            "16",
            "--max-steps",
            "24",
            "--max-new-tokens",
            "1024",
            "--sample",
        ),
    ):
        with pytest.raises(SystemExit) as rejected:
            CLI.main(
                ["--adapter", "missing", "--theorem", "0 = 0", *arguments]
            )
        assert rejected.value.code == 2


@pytest.mark.parametrize(
    ("flag", "value", "message"),
    (
        ("--max-new-tokens", "1025", "max_new_tokens"),
        ("--temperature", "nan", "temperature"),
        ("--top-p", "inf", "top_p"),
    ),
)
def test_decode_overrides_are_finite_and_bounded(
    flag: str,
    value: str,
    message: str,
) -> None:
    args = CLI._parser().parse_args(
        ["--adapter", "unused", "--theorem", "0 = 0", flag, value]
    )
    manifest = {
        "generation": {"max_new_tokens": 64, "temperature": 0.8, "top_p": 0.95}
    }
    with pytest.raises(ValueError, match=message):
        CLI._decode_options(manifest, args)


@pytest.mark.parametrize(
    "arguments",
    (
        ("--theorem", "0 = 0", "--max-new-tokens", "1025"),
        ("--theorem", "0 = 0", "--temperature", "nan"),
        ("--theorem", "0 = 0", "--top-p", "inf"),
        ("--goal", "not-a-held-out-goal"),
    ),
)
def test_bad_decode_or_goal_selection_precedes_model_loading(
    arguments: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        CLI,
        "load_adapter",
        lambda *args, **kwargs: pytest.fail("adapter must not load"),
    )

    with pytest.raises(SystemExit) as rejected:
        CLI.main(["--adapter", "missing", *arguments])
    assert rejected.value.code == 2


def test_goal_and_theorem_modes_are_mutually_exclusive() -> None:
    with pytest.raises(SystemExit) as rejected:
        CLI._parser().parse_args(
            [
                "--adapter",
                "missing",
                "--goal",
                "le_total",
                "--theorem",
                "0 = 0",
            ]
        )
    assert rejected.value.code == 2


def _mock_model_runtime(
    monkeypatch: pytest.MonkeyPatch,
    policy: object,
    *,
    sources: object = None,
) -> None:
    manifest = {
        "run": {"name": "unit-test"},
        "generation": {
            "max_new_tokens": 64,
            "temperature": 0.8,
            "top_p": 0.95,
        },
    }
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
    monkeypatch.setattr(
        CLI,
        "_read_adapter_manifest_snapshot",
        lambda adapter: (manifest, "a" * 64),
    )
    monkeypatch.setattr(
        CLI,
        "_recheck_adapter_snapshot",
        lambda adapter, loaded, digest: None,
    )
    monkeypatch.setattr(
        CLI,
        "load_adapter",
        lambda *args, **kwargs: (object(), object(), manifest),
    )
    monkeypatch.setattr(
        CLI,
        "adapter_provenance",
        lambda *args, **kwargs: {"training_manifest_sha256": "a" * 64},
    )
    monkeypatch.setattr(
        CLI, "attested_training_environment", lambda manifest: model_v1_environment()
    )
    monkeypatch.setattr(CLI, "PeanoPolicyAdapter", lambda **kwargs: policy)
    monkeypatch.setattr(CLI, "runtime_identity", lambda module: {"python": "test"})
    monkeypatch.setattr(CLI, "slurm_job_identity", lambda: {"site": "test"})
    if sources is None:
        monkeypatch.setattr(CLI, "_evaluation_sources", lambda: {"sha256": "same"})
    else:
        monkeypatch.setattr(CLI, "_evaluation_sources", sources)


def test_arbitrary_no_proof_exits_one_and_creates_no_pa_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _mock_model_runtime(monkeypatch, _StopPolicy())
    report = tmp_path / "result.json"
    proof = tmp_path / "result.pa"

    status = CLI.main(
        [
            "--adapter",
            "fake-adapter",
            "--theorem",
            "0 = 0",
            "--output",
            str(report),
            "--proof-output",
            str(proof),
        ]
    )

    assert status == 1
    assert report.is_file()
    assert '"status": "no-proof"' in report.read_text(encoding="utf-8")
    assert not proof.exists()


def test_source_change_prevents_proof_or_report_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = 0

    def changing_sources() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"sha256": "before" if calls == 1 else "after"}

    _mock_model_runtime(monkeypatch, _ReflPolicy(), sources=changing_sources)
    report = tmp_path / "result.json"
    proof = tmp_path / "result.pa"

    with pytest.raises(RuntimeError, match="source changed"):
        CLI.main(
            [
                "--adapter",
                "fake-adapter",
                "--theorem",
                "0 = 0",
                "--output",
                str(report),
                "--proof-output",
                str(proof),
            ]
        )
    assert not report.exists()
    assert not proof.exists()


def test_adapter_change_prevents_proof_or_report_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _mock_model_runtime(monkeypatch, _ReflPolicy())
    checks = 0

    def changing_adapter(*args: object) -> None:
        nonlocal checks
        checks += 1
        if checks == 2:
            raise RuntimeError("adapter training manifest changed during evaluation")

    monkeypatch.setattr(CLI, "_recheck_adapter_snapshot", changing_adapter)
    report = tmp_path / "result.json"
    proof = tmp_path / "result.pa"

    with pytest.raises(RuntimeError, match="adapter training manifest changed"):
        CLI.main(
            [
                "--adapter",
                "fake-adapter",
                "--theorem",
                "0 = 0",
                "--output",
                str(report),
                "--proof-output",
                str(proof),
            ]
        )
    assert not report.exists()
    assert not proof.exists()


def test_proof_copy_failure_leaves_complete_primary_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _mock_model_runtime(monkeypatch, _ReflPolicy())
    real_create = CLI._atomic_create_text
    calls = 0

    def fail_second_create(path: Path, text: str) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise FileExistsError("simulated report publication race")
        real_create(path, text)

    monkeypatch.setattr(CLI, "_atomic_create_text", fail_second_create)
    report = tmp_path / "result.json"
    proof = tmp_path / "result.pa"

    with pytest.raises(FileExistsError, match="simulated"):
        CLI.main(
            [
                "--adapter",
                "fake-adapter",
                "--theorem",
                "0 = 0",
                "--output",
                str(report),
                "--proof-output",
                str(proof),
            ]
        )
    assert report.is_file()
    assert '"script": "pa prove 0 = 0\\nrefl\\nqed\\n"' in report.read_text(
        encoding="utf-8"
    )
    assert not proof.exists()


def test_manifest_snapshot_rejects_duplicate_keys(tmp_path: Path) -> None:
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    (adapter / "training-manifest.json").write_text(
        '{"v":1,"v":1}\n', encoding="utf-8"
    )

    with pytest.raises(ValueError, match="duplicate training-manifest key"):
        CLI._read_adapter_manifest_snapshot(adapter)
