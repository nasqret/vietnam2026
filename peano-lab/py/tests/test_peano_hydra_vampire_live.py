"""Focused A3.2 tests for the transactional live Vampire preview."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel.checker import check  # noqa: E402
from peano_lab.ui.prove import run_surface  # noqa: E402
import training.peano_hydra.vampire_live as vampire_live  # noqa: E402
from training.peano_hydra.macro_runner import start_macro_session  # noqa: E402
from training.peano_hydra.vampire_live import (  # noqa: E402
    VAMPIRE_LIVE_MODE,
    VampireLiveAccepted,
    VampireLiveBounds,
    VampireLiveFailure,
    VampireLiveSolver,
    VampireLiveTrace,
    run_vampire_live,
)


def _executable(tmp_path: Path, body: str, *, name: str = "fake-vampire.py") -> Path:
    path = tmp_path / name
    path.write_text(
        f"#!{sys.executable}\n" + body,
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def _solver(
    executable: Path,
    *,
    wall_ms: int = 3_000,
    output_bytes: int = 4_096,
    memory_bytes: int = 512 * 1024 * 1024,
) -> VampireLiveSolver:
    return VampireLiveSolver(
        str(executable.resolve()),
        hashlib.sha256(executable.read_bytes()).hexdigest(),
        VAMPIRE_LIVE_MODE,
        VampireLiveBounds(
            max_wall_time_ms=wall_ms,
            max_cpu_time_seconds=2,
            max_memory_bytes=memory_bytes,
            max_output_bytes=output_bytes,
        ),
    )


def _theorem_executable(tmp_path: Path) -> Path:
    return _executable(
        tmp_path,
        """import os
from pathlib import Path
import sys

assert sys.argv[1:3] == ["--mode", "vampire"]
assert Path(sys.argv[3]).name == "problem.p"
assert Path(sys.argv[3]).parent.resolve() == Path.cwd().resolve()
assert Path(os.environ["HOME"]).resolve() == Path.cwd().resolve()
assert Path(os.environ["TMPDIR"]).resolve() == Path.cwd().resolve()
assert os.environ["LANG"] == os.environ["LC_ALL"] == "C"
assert b"fof(goal,conjecture," in Path(sys.argv[3]).read_bytes()
print("% SZS status Theorem for live_preview")
""",
    )


def _assert_unchanged(owner, state, replay, trace_count: int) -> None:
    assert owner.state is state
    assert owner.replay_steps is replay
    assert owner.trace.record_count == trace_count


def test_live_pa3_runs_the_binary_and_commits_only_after_fresh_kernel_replay(
    tmp_path: Path,
) -> None:
    executable = _theorem_executable(tmp_path)
    owner = start_macro_session("∀ x. x + 0 = x")
    state, replay, trace_count = owner.state, owner.replay_steps, owner.trace.record_count

    result = run_vampire_live(owner, ("PA3",), _solver(executable))

    assert type(result) is VampireLiveAccepted
    assert result.owner is not owner
    assert result.owner.state.is_done()
    assert result.public_commands == ("apply PA3",)
    assert result.certificate is not None
    assert check((), result.certificate, owner.original_target)
    assert result.closed is True
    assert result.kernel_accepted is True
    assert result.open_progress is False
    _assert_unchanged(owner, state, replay, trace_count)
    trace = result.trace.to_dict()
    assert trace["outcome"] == {"error": None, "phase": None, "status": "accepted"}
    assert trace["authority"]["proof_authority"] is False
    assert trace["authority"]["candidate"] is True
    assert trace["problem"]["sha256"] == hashlib.sha256(
        __import__("base64").b64decode(trace["problem"]["tptp_base64"])
    ).hexdigest()
    assert trace["process"]["copied_executable_sha256"] == hashlib.sha256(
        executable.read_bytes()
    ).hexdigest()
    assert trace["process"]["leader_observed"] is True
    assert trace["process"]["leader_observation_samples"] >= 1
    assert trace["kernel"]["status"] == "accepted"
    assert trace["kernel"]["fresh"] is True
    assert trace["kernel"]["kernel_accepted"] is True


def test_live_two_pa_axiom_conjunction_reconstructs_three_public_commands(
    tmp_path: Path,
) -> None:
    theorem = "(∀ x. x + 0 = x) ∧ (∀ x. x · 0 = 0)"
    owner = start_macro_session(theorem)

    result = run_vampire_live(
        owner,
        ("PA3", "PA5"),
        _solver(_theorem_executable(tmp_path)),
    )

    assert type(result) is VampireLiveAccepted
    assert result.owner.state.is_done()
    assert result.public_commands == ("split", "apply PA3", "apply PA5")
    assert result.trace.to_dict()["premises"]["resolved"] == [
        {"formula": "∀ x. x + 0 = x", "kind": "pa-axiom", "name": "PA3"},
        {"formula": "∀ x. x · 0 = 0", "kind": "pa-axiom", "name": "PA5"},
    ]


def test_live_public_theorem_is_resolved_then_imported_on_the_public_surface(
    tmp_path: Path,
) -> None:
    owner = start_macro_session("∀ x. 0 + x = x")

    result = run_vampire_live(
        owner,
        ("zero_add",),
        _solver(_theorem_executable(tmp_path)),
    )

    assert type(result) is VampireLiveAccepted
    assert result.owner.state.is_done()
    assert result.public_commands == ("use zero_add", "apply zero_add")
    assert result.trace.to_dict()["premises"]["resolved"] == [
        {
            "formula": "∀ x. 0 + x = x",
            "kind": "public-theorem",
            "name": "zero_add",
        }
    ]


def test_live_can_commit_explicit_open_progress_without_claiming_kernel_qed(
    tmp_path: Path,
) -> None:
    initial = start_macro_session(
        "(∀ x. x + 0 = x) ∧ (∀ x. x · 0 = 0)"
    )
    split_session = run_surface(
        initial.session,
        "split",
        capabilities=initial.capabilities,
        record_trace=False,
    )
    owner = initial.with_session(split_session)

    result = run_vampire_live(
        owner,
        ("PA3",),
        _solver(_theorem_executable(tmp_path)),
    )

    assert type(result) is VampireLiveAccepted
    assert result.owner is not owner
    assert result.closed is False
    assert result.kernel_accepted is False
    assert result.open_progress is True
    assert result.certificate is None
    assert result.public_commands == ("apply PA3",)
    assert result.trace.to_dict()["kernel"] == {
        "attempted": False,
        "error": None,
        "fresh_original_goal_replay": True,
        "status": "not-required-open-successor",
    }


def test_forged_theorem_status_cannot_prove_false_and_rolls_back_identically(
    tmp_path: Path,
) -> None:
    owner = start_macro_session("0 = 1")
    state, replay, trace_count = owner.state, owner.replay_steps, owner.trace.record_count

    result = run_vampire_live(
        owner,
        (),
        _solver(_theorem_executable(tmp_path)),
    )

    assert type(result) is VampireLiveFailure
    assert result.owner is owner
    assert result.phase == "reconstruction"
    assert "no authority" in result.error
    _assert_unchanged(owner, state, replay, trace_count)
    trace = result.trace.to_dict()
    assert trace["process"]["solver_status"] == "theorem"
    assert trace["commands"]["public_commands"] == []
    assert trace["owner_after"] == trace["owner_before"]
    assert trace["kernel"]["attempted"] is False


def test_invalid_explicit_premise_name_is_a_structured_identical_owner_failure(
    tmp_path: Path,
) -> None:
    owner = start_macro_session("0 = 0")

    result = run_vampire_live(
        owner,
        ("PA3; qed",),
        _solver(_theorem_executable(tmp_path)),
    )

    assert type(result) is VampireLiveFailure
    assert result.owner is owner
    assert result.phase == "premises"
    assert result.trace.to_dict()["premises"]["names"] == ["PA3; qed"]
    assert result.trace.to_dict()["process"] is None


def test_wrong_reconstruction_and_open_focused_goal_both_fail_transactionally(
    tmp_path: Path,
) -> None:
    executable = _theorem_executable(tmp_path)
    owner = start_macro_session(
        "(∀ x. x + 0 = x) ∧ (∀ x. ∀ y. x + S y = S (x + y))"
    )
    state, replay, trace_count = owner.state, owner.replay_steps, owner.trace.record_count
    wrong = run_vampire_live(owner, ("PA3", "PA5"), _solver(executable))
    assert type(wrong) is VampireLiveFailure
    assert wrong.owner is owner
    assert wrong.phase == "reconstruction"
    assert len(wrong.trace.to_dict()["commands"]["intermediate_states"]) == 2
    _assert_unchanged(owner, state, replay, trace_count)

    quantified = start_macro_session("∀ x. x = x")
    open_session = run_surface(
        quantified.session,
        "intro x",
        capabilities=quantified.capabilities,
        record_trace=False,
    )
    open_owner = quantified.with_session(open_session)
    open_result = run_vampire_live(open_owner, (), _solver(executable))
    assert type(open_result) is VampireLiveFailure
    assert open_result.owner is open_owner
    assert open_result.phase == "goal"
    assert "closed focused goal" in open_result.error

    implication = start_macro_session("0 = 0 → 0 = 0")
    contextual_session = run_surface(
        implication.session,
        "intro h",
        capabilities=implication.capabilities,
        record_trace=False,
    )
    contextual_owner = implication.with_session(contextual_session)
    contextual_result = run_vampire_live(
        contextual_owner,
        (),
        _solver(executable),
    )
    assert type(contextual_result) is VampireLiveFailure
    assert contextual_result.owner is contextual_owner
    assert contextual_result.phase == "goal"


@pytest.mark.parametrize(
    ("body", "wall_ms", "output_bytes", "flag"),
    [
        ("import time\ntime.sleep(1)\n", 30, 4_096, "timed_out"),
        ("import os\nos.write(1, b'x' * 8192)\n", 3_000, 128, "output_limited"),
    ],
)
def test_wall_and_output_limits_fail_closed_with_retained_process_evidence(
    tmp_path: Path,
    body: str,
    wall_ms: int,
    output_bytes: int,
    flag: str,
) -> None:
    owner = start_macro_session("0 = 0")
    executable = _executable(tmp_path, body)

    result = run_vampire_live(
        owner,
        (),
        _solver(executable, wall_ms=wall_ms, output_bytes=output_bytes),
    )

    assert type(result) is VampireLiveFailure
    assert result.owner is owner
    assert result.phase == "process"
    assert result.trace.to_dict()["process"][flag] is True
    assert result.trace.to_dict()["owner_after"] == result.trace.to_dict()["owner_before"]


def test_output_one_byte_below_ceiling_is_accepted_but_exact_ceiling_is_exhausted(
    tmp_path: Path,
) -> None:
    raw = b"% SZS status Theorem for boundary\n"
    executable = _executable(
        tmp_path,
        f"import os\nos.write(1, {raw!r})\n",
    )
    accepted_owner = start_macro_session("0 = 0")
    accepted = run_vampire_live(
        accepted_owner,
        (),
        _solver(executable, output_bytes=len(raw) + 1),
    )
    assert type(accepted) is VampireLiveAccepted
    assert accepted.public_commands == ("refl",)
    assert accepted.trace.to_dict()["process"]["retained_output_bytes"] == len(raw)
    assert accepted.trace.to_dict()["process"]["observed_output_bytes"] == len(raw)
    assert accepted.trace.to_dict()["process"]["output_limited"] is False

    exact_owner = start_macro_session("0 = 0")
    exact = run_vampire_live(
        exact_owner,
        (),
        _solver(executable, output_bytes=len(raw)),
    )
    assert type(exact) is VampireLiveFailure
    assert exact.owner is exact_owner
    assert exact.phase == "process"
    assert exact.trace.to_dict()["process"]["retained_output_bytes"] == len(raw)
    assert exact.trace.to_dict()["process"]["observed_output_bytes"] == len(raw)
    assert exact.trace.to_dict()["process"]["output_limited"] is True


def test_one_process_rlimit_blocks_solver_fork_and_failure_keeps_owner(
    tmp_path: Path,
) -> None:
    executable = _executable(
        tmp_path,
        """import subprocess
import sys
try:
    subprocess.run([sys.executable, "-c", "pass"], check=True)
except OSError:
    raise SystemExit(86)
raise SystemExit(87)
""",
    )
    owner = start_macro_session("0 = 0")

    result = run_vampire_live(owner, (), _solver(executable))

    assert type(result) is VampireLiveFailure
    assert result.owner is owner
    assert result.phase == "process"
    process = result.trace.to_dict()["process"]
    assert process["exit_code"] == 86
    assert process["leader_observation_samples"] >= 1
    assert process["containment"]["process_enforcement"] == (
        "rlimit-nproc-one"
    )
    assert process["containment"]["process_observation"] == (
        "leader-liveness-only-no-group-enumeration"
    )


def test_mode_portfolio_and_executable_digest_are_pinned(tmp_path: Path) -> None:
    executable = _theorem_executable(tmp_path)
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    bounds = VampireLiveBounds(1_000, 1, 512 * 1024 * 1024, 4_096)
    with pytest.raises(ValueError, match="standard"):
        VampireLiveSolver(str(executable.resolve()), digest, ("--mode", "casc"), bounds)
    with pytest.raises(ValueError, match="portfolio"):
        VampireLiveSolver(
            str(executable.resolve()),
            digest,
            ("--mode", "vampire", "--portfolio", "fast"),
            bounds,
        )
    with pytest.raises(ValueError, match="trusted host-owned"):
        VampireLiveSolver(
            str(executable.resolve()),
            digest,
            VAMPIRE_LIVE_MODE,
            bounds,
            False,
        )

    owner = start_macro_session("0 = 0")
    forged = VampireLiveSolver(
        str(executable.resolve()),
        "0" * 64,
        VAMPIRE_LIVE_MODE,
        bounds,
    )
    result = run_vampire_live(owner, (), forged)
    assert type(result) is VampireLiveFailure
    assert result.owner is owner
    assert result.phase == "process"
    assert "identity mismatch" in result.error


@pytest.mark.parametrize(
    ("path", "replacement", "match"),
    [
        (("problem", "sha256"), "0" * 64, "TPTP digest"),
        (("problem", "tptp_base64"), "eA==", "TPTP byte accounting"),
        (("process", "raw_output_sha256"), "0" * 64, "raw-output digest"),
        (("process", "retained_output_bytes"), 999, "output accounting"),
        (
            ("process", "copied_executable_sha256"),
            "0" * 64,
            "copied executable differs",
        ),
        (("process", "wall_time_ms"), 9_999, "wall-time accounting"),
        (("solver", "bounds", "max_processes"), 2, "trace bounds are invalid"),
        (
            ("solver", "host_owned_trusted_configuration"),
            False,
            "not trusted host configuration",
        ),
        (("kernel", "kernel_accepted"), False, "lacks kernel authority"),
    ],
)
def test_trace_rejects_mutated_problem_process_solver_and_kernel_evidence(
    tmp_path: Path,
    path: tuple[str, ...],
    replacement: object,
    match: str,
) -> None:
    accepted = run_vampire_live(
        start_macro_session("∀ x. x + 0 = x"),
        ("PA3",),
        _solver(_theorem_executable(tmp_path)),
    )
    assert type(accepted) is VampireLiveAccepted
    record = deepcopy(accepted.trace.to_dict())
    cursor = record
    for field in path[:-1]:
        cursor = cursor[field]
    cursor[path[-1]] = replacement

    with pytest.raises(ValueError, match=match):
        VampireLiveTrace.from_record(record)


def test_trace_regenerates_tptp_instead_of_trusting_mutually_rehashed_bytes(
    tmp_path: Path,
) -> None:
    import base64

    accepted = run_vampire_live(
        start_macro_session("∀ x. x + 0 = x"),
        ("PA3",),
        _solver(_theorem_executable(tmp_path)),
    )
    assert type(accepted) is VampireLiveAccepted
    record = deepcopy(accepted.trace.to_dict())
    raw = base64.b64decode(record["problem"]["tptp_base64"])
    altered = raw.replace(b"% peano-hydra", b"% xeano-hydra", 1)
    assert len(altered) == len(raw) and altered != raw
    record["problem"]["tptp_base64"] = base64.b64encode(altered).decode("ascii")
    record["problem"]["sha256"] = hashlib.sha256(altered).hexdigest()
    record["problem"]["bytes"] = len(altered)

    with pytest.raises(ValueError, match="do not reconstruct"):
        VampireLiveTrace.from_record(record)


def test_trace_itself_rejects_a_mutated_failure_rollback_owner(tmp_path: Path) -> None:
    executable = _theorem_executable(tmp_path)
    owner = start_macro_session("0 = 1")
    failed = run_vampire_live(
        owner,
        (),
        _solver(executable),
    )
    assert type(failed) is VampireLiveFailure
    closed = run_vampire_live(
        start_macro_session("0 = 0"),
        (),
        _solver(executable),
    )
    assert type(closed) is VampireLiveAccepted
    record = deepcopy(failed.trace.to_dict())
    record["owner_after"] = closed.trace.to_dict()["owner_after"]

    with pytest.raises(ValueError, match="did not roll back exactly"):
        VampireLiveTrace.from_record(record)


def test_forced_fresh_kernel_rejection_rolls_back_identically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Rejected(RuntimeError):
        record = {
            "commands": ["apply PA3"],
            "error": "forced kernel rejection",
            "fresh": True,
            "kernel_accepted": False,
            "status": "rejected",
        }

    monkeypatch.setattr(
        vampire_live,
        "_fresh_final_replay",
        lambda owner: (_ for _ in ()).throw(Rejected("forced kernel rejection")),
    )
    owner = start_macro_session("∀ x. x + 0 = x")
    state, replay, trace_count = owner.state, owner.replay_steps, owner.trace.record_count

    result = run_vampire_live(
        owner,
        ("PA3",),
        _solver(_theorem_executable(tmp_path)),
    )

    assert type(result) is VampireLiveFailure
    assert result.owner is owner
    assert result.phase == "kernel"
    assert result.trace.to_dict()["kernel"]["status"] == "rejected"
    _assert_unchanged(owner, state, replay, trace_count)
