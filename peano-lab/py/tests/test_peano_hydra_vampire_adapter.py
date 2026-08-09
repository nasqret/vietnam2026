"""A3 vertical slice: inert Vampire evidence and checked Peano reconstruction."""

from __future__ import annotations

from base64 import b64encode
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.engine.tactics import InvalidProof  # noqa: E402
from training.peano_hydra.macros import (  # noqa: E402
    Dispatch,
    DispatchBounds,
    serialize_macro,
)
import training.peano_hydra.macro_runner as macro_runner  # noqa: E402
from training.peano_hydra.macro_runner import (  # noqa: E402
    MacroExecutionError,
    execute_macro,
    register_dispatch_subprocess,
    start_macro_session,
)
from training.peano_hydra.vampire_adapter import (  # noqa: E402
    VAMPIRE_RECONSTRUCTION_CLASS,
    VAMPIRE_TRANSLATION_CLASS,
    VampireAdapterError,
    VampirePremise,
    dispatch_response,
    emit_tptp_problem,
    parse_vampire_output,
    reconstruct_public_commands,
    run_vampire,
)


BOUNDS = DispatchBounds(
    max_steps=20,
    max_wall_time_ms=3_000,
    max_memory_bytes=256 * 1024 * 1024,
    max_output_bytes=4_096,
)


def _pa3() -> VampirePremise:
    return VampirePremise("PA3", "pa-axiom", "∀ x. x + 0 = x")


def _solver_probe(tmp_path: Path, response: bytes):
    """A one-process frozen-Dispatch probe, not a fake proof authority."""

    path = tmp_path / "vampire-dispatch-probe.py"
    encoded = b64encode(response).decode("ascii")
    path.write_text(
        f"""#!{sys.executable}
import base64
import json
import os
import sys

call = json.load(sys.stdin)
if call["request"]["solver"] != "vampire":
    raise SystemExit(70)
os.write(1, base64.b64decode({encoded!r}))
""",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return register_dispatch_subprocess(
        "vampire",
        artifact_kind="source",
        artifact_path=path,
        configuration={
            "adapter": "a3-test-probe",
            "authority": "none",
            "real_vampire_broker_registered": False,
        },
    )


def _dispatch(tmp_path: Path, theorem: str, response: bytes):
    registration = _solver_probe(tmp_path, response)
    owner = start_macro_session(theorem)
    proposal = serialize_macro(Dispatch("vampire", (), BOUNDS))
    return owner, proposal, registration


def test_closed_pa_problem_and_symbol_map_are_byte_deterministic() -> None:
    first = emit_tptp_problem(
        "∀ x. x + 0 = x",
        (_pa3(),),
        requested_premises=("PA3",),
    )
    second = emit_tptp_problem(
        "∀ x. x + 0 = x",
        (_pa3(),),
        requested_premises=("PA3",),
    )
    expected = (
        "% peano-hydra-vampire-problem-v1\n"
        f"% translation {VAMPIRE_TRANSLATION_CLASS}\n"
        "fof(premise_0000,axiom,(! [X0] : (add(X0,z) = X0))).\n"
        "fof(goal,conjecture,(! [X0] : (add(X0,z) = X0))).\n"
    ).encode("ascii")
    assert first.tptp_bytes == second.tptp_bytes == expected
    assert first.sha256 == second.sha256 == hashlib.sha256(expected).hexdigest()
    assert first.symbol_map == (
        ("z", "term:zero"),
        ("s", "term:successor"),
        ("add", "term:addition"),
        ("mul", "term:multiplication"),
        ("premise_0000", "pa-axiom:PA3"),
        ("goal", "conjecture:original-goal"),
    )


def test_problem_emission_rejects_masked_duplicate_and_open_premises() -> None:
    with pytest.raises(VampireAdapterError, match="explicit allow-list"):
        emit_tptp_problem(
            "0 = 0",
            (_pa3(),),
            requested_premises=("PA4",),
        )
    with pytest.raises(VampireAdapterError, match="unique"):
        emit_tptp_problem("0 = 0", (_pa3(), _pa3()))
    with pytest.raises(VampireAdapterError, match="closed-formula"):
        VampirePremise("h", "public-theorem", "n = n")


def test_szs_parser_is_inert_and_conflicts_fail_to_unknown() -> None:
    forged = parse_vampire_output(b"% SZS status Theorem for forged\n")
    non_reflexive = emit_tptp_problem("0 = 1", ())
    assert forged.status == "theorem"
    assert forged.szs_statuses == ("Theorem",)
    assert forged.raw_sha256 == hashlib.sha256(forged.raw_output).hexdigest()
    assert reconstruct_public_commands(non_reflexive, forged) == ()

    conflicting = parse_vampire_output(
        b"% SZS status Theorem for x\n% SZS status CounterSatisfiable for x\n"
    )
    assert conflicting.status == "unknown"
    assert conflicting.parse_error == "Vampire emitted contradictory SZS statuses"


def test_real_subprocess_boundary_receives_exact_problem_via_fake_executable(
    tmp_path: Path,
) -> None:
    problem = emit_tptp_problem("0 = 0", ())
    executable = tmp_path / "fake-vampire.py"
    executable.write_text(
        f"""#!{sys.executable}
import hashlib
from pathlib import Path
import sys

if sys.argv[1:3] != ["--mode", "casc"]:
    raise SystemExit(71)
problem = Path(sys.argv[3]).read_bytes()
if hashlib.sha256(problem).hexdigest() != {problem.sha256!r}:
    raise SystemExit(72)
print("% SZS status Theorem for tiny")
""",
        encoding="utf-8",
    )
    executable.chmod(0o700)
    evidence = run_vampire(
        executable,
        problem,
        arguments=("--mode", "casc"),
        wall_time_ms=2_000,
        output_bytes=4_096,
    )
    assert evidence.status == "theorem"
    assert evidence.exit_code == 0
    assert evidence.timed_out is evidence.output_limited is False
    assert evidence.arguments == ("--mode", "casc")
    assert evidence.executable_sha256 == hashlib.sha256(
        executable.read_bytes()
    ).hexdigest()
    assert reconstruct_public_commands(problem, evidence) == ("refl",)
    assert VAMPIRE_RECONSTRUCTION_CLASS.endswith("public-refl-v1")


def test_subprocess_boundary_enforces_wall_and_output_ceilings(tmp_path: Path) -> None:
    problem = emit_tptp_problem("0 = 0", ())
    sleeper = tmp_path / "sleeping-vampire.py"
    sleeper.write_text(
        f"#!{sys.executable}\nimport time\ntime.sleep(10)\n",
        encoding="utf-8",
    )
    sleeper.chmod(0o700)
    timeout = run_vampire(
        sleeper,
        problem,
        wall_time_ms=50,
        output_bytes=4_096,
    )
    assert timeout.timed_out is True
    assert timeout.status == "resource-limit"
    assert timeout.exit_code is not None and timeout.exit_code != 0

    noisy = tmp_path / "noisy-vampire.py"
    noisy.write_text(
        f"#!{sys.executable}\nimport os\nos.write(1, b'x' * 8192)\n",
        encoding="utf-8",
    )
    noisy.chmod(0o700)
    limited = run_vampire(
        noisy,
        problem,
        wall_time_ms=2_000,
        output_bytes=64,
    )
    assert limited.output_limited is True
    assert limited.status == "resource-limit"
    assert len(limited.raw_output) == 64


def test_forged_szs_without_reconstruction_rolls_back_dispatch(
    tmp_path: Path,
) -> None:
    problem = emit_tptp_problem("0 = 1", ())
    evidence = parse_vampire_output(b"% SZS status Theorem for forged\n")
    response = dispatch_response(problem, evidence)
    assert json.loads(response) == {
        "format": "peano-hydra-dispatch-response",
        "public_commands": [],
        "status": "theorem",
        "steps_used": 0,
        "v": 1,
    }
    owner, proposal, registration = _dispatch(tmp_path, "0 = 1", response)
    with pytest.raises(MacroExecutionError, match="status alone has no authority") as failure:
        execute_macro(
            owner,
            proposal,
            dispatch_adapters={"vampire": registration},
        )
    assert failure.value.owner is owner
    trace = failure.value.trace.to_dict()
    assert trace["state_after"] == trace["state_before"]
    assert trace["solver"]["response_status"] == "theorem"
    assert trace["solver"]["reconstructed_commands"] == []
    assert trace["final_replay"] is None


def test_reconstructed_refl_reaches_fresh_original_goal_kernel(
    tmp_path: Path,
) -> None:
    problem = emit_tptp_problem("0 = 0", ())
    evidence = parse_vampire_output(b"% SZS status Theorem for tiny\n")
    response = dispatch_response(problem, evidence)
    owner, proposal, registration = _dispatch(tmp_path, "0 = 0", response)
    result = execute_macro(
        owner,
        proposal,
        dispatch_adapters={"vampire": registration},
    )
    assert owner.trace.record_count == 0
    assert result.closed and result.certificate is not None
    assert result.public_commands == ("refl",)
    final = result.trace.to_dict()["final_replay"]
    assert final["fresh"] is True
    assert final["original_theorem"] == "0 = 0"
    assert final["commands"] == ["refl"]
    assert final["kernel_accepted"] is True


def test_even_reconstructed_refl_cannot_bypass_fresh_kernel(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    problem = emit_tptp_problem("0 = 0", ())
    evidence = parse_vampire_output(b"% SZS status Theorem for forged\n")
    owner, proposal, registration = _dispatch(
        tmp_path, "0 = 0", dispatch_response(problem, evidence)
    )

    def reject(*args, **kwargs):
        del args, kwargs
        raise InvalidProof("forced fresh-kernel rejection")

    monkeypatch.setattr(macro_runner, "checked_surface_final", reject)
    with pytest.raises(MacroExecutionError, match="fresh original-goal") as failure:
        execute_macro(
            owner,
            proposal,
            dispatch_adapters={"vampire": registration},
        )
    assert failure.value.owner is owner
    trace = failure.value.trace.to_dict()
    assert trace["state_after"] == trace["state_before"]
    assert trace["final_replay"]["kernel_accepted"] is False
    assert trace["final_replay"]["status"] == "rejected"
