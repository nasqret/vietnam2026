"""H0.3 transactional macro execution and adversarial subprocess probes."""

from __future__ import annotations

from base64 import b64decode
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.engine.tactics import InvalidProof  # noqa: E402
from peano_lab.ui.prove import (  # noqa: E402
    SURFACE_COMMAND_NAMES,
    SURFACE_THEOREM_NAMES,
    SurfaceCapabilities,
    run_surface,
)
from training.peano_hydra.macros import (  # noqa: E402
    MACRO_FORMAT,
    MAX_MACRO_BYTES,
    Cut,
    Dispatch,
    DispatchBounds,
    Induct,
    Rewrite,
    Split,
    Use,
    Witness,
    macro_protocol_identity,
    serialize_macro,
)
import training.peano_hydra.macro_runner as macro_runner  # noqa: E402
from training.peano_hydra.macro_runner import (  # noqa: E402
    DISPATCH_ADAPTER_IDENTITY_FORMAT,
    DISPATCH_ADAPTER_IDENTITY_VERSION,
    DispatchAdapterIdentity,
    DispatchAdapterRegistration,
    DispatchProtocolError,
    MacroExecutionError,
    MacroOwner,
    MacroRunnerError,
    MacroTrace,
    execute_macro,
    register_dispatch_subprocess,
    start_macro_session,
)


BOUNDS = DispatchBounds(
    max_steps=20,
    max_wall_time_ms=3_000,
    max_memory_bytes=256 * 1024 * 1024,
    max_output_bytes=4_096,
)


def _probe(tmp_path: Path, **configuration: object) -> DispatchAdapterRegistration:
    """Create one direct-exec adapter speaking only the frozen JSON protocol."""

    probe = tmp_path / "dispatch-probe.py"
    probe.write_text(
        f"""#!{sys.executable}
import hashlib
import json
import os
import sys
import time

call = json.load(sys.stdin)
canonical_request = json.dumps(
    call["request"], ensure_ascii=False, allow_nan=False,
    sort_keys=True, separators=(",", ":"),
).encode("utf-8")
if hashlib.sha256(canonical_request).hexdigest() != call["request_sha256"]:
    raise SystemExit(70)
configuration = call["configuration"]
if "expected_theorem" in configuration:
    if call["context"]["original_theorem"] != configuration["expected_theorem"]:
        raise SystemExit(71)
if "expected_premise" in configuration:
    premises = call["context"]["premises"]
    if not premises or premises[0]["name"] != configuration["expected_premise"]:
        raise SystemExit(72)
mode = configuration.get("mode", "response")
if mode == "sleep":
    time.sleep(configuration.get("seconds", 10))
elif mode == "oversize":
    os.write(1, b"x" * configuration["bytes"])
    raise SystemExit(0)
elif mode == "memory":
    allocation = bytearray(configuration["bytes"])
    allocation[0] = 1
    time.sleep(configuration.get("seconds", 10))
elif mode == "fork":
    try:
        child = os.fork()
    except OSError:
        configuration["status"] = "unknown"
    else:
        if child == 0:
            os._exit(0)
        os.waitpid(child, 0)
        raise SystemExit(73)
elif mode == "raw":
    os.write(1, configuration["raw"].encode("utf-8"))
    raise SystemExit(0)

response = {{
    "format": "peano-hydra-dispatch-response",
    "v": 1,
    "status": configuration.get("status", "theorem"),
    "steps_used": configuration.get("steps_used", 1),
    "public_commands": configuration.get("commands", ["refl"]),
}}
wire = json.dumps(
    response, ensure_ascii=False, allow_nan=False,
    sort_keys=True, separators=(",", ":"),
).encode("utf-8")
os.write(1, wire)
""",
        encoding="utf-8",
    )
    probe.chmod(0o700)
    return register_dispatch_subprocess(
        "test-solver",
        artifact_kind="source",
        artifact_path=probe,
        configuration=dict(configuration),
    )


def _execute_dispatch(
    tmp_path: Path,
    *,
    theorem: str = "0 = 0",
    premises: tuple[str, ...] = (),
    bounds: DispatchBounds = BOUNDS,
    **configuration: object,
):
    registration = _probe(tmp_path, **configuration)
    owner = start_macro_session(theorem)
    result = execute_macro(
        owner,
        serialize_macro(Dispatch("test-solver", premises, bounds)),
        dispatch_adapters={"test-solver": registration},
    )
    return result, registration, owner


def _run(theorem: str, action):
    return execute_macro(start_macro_session(theorem), serialize_macro(action))


@pytest.mark.parametrize(
    ("theorem", "action", "expected_goals"),
    [
        ("0 = 0", Use("zero_add", ("0",)), 1),
        ("0 = 0", Cut("have", "h", "0 = 0"), 2),
        ("0 = 0", Cut("suffices", "h", "0 = 0"), 2),
        ("exists n. n = n", Witness("0"), 1),
        ("forall n. n = n", Induct("n", "n = n"), 2),
        ("0 = 0 /\\ 0 = 0", Split("conjunction"), 2),
        ("0 = 0 \\/ 0 = 1", Split("left"), 1),
        ("0 = 1 \\/ 0 = 0", Split("right"), 1),
    ],
)
def test_every_nonsolver_macro_uses_public_surface(
    theorem: str, action: object, expected_goals: int
) -> None:
    result = _run(theorem, action)
    assert len(result.owner.state.goals) == expected_goals
    assert result.certificate is None
    trace = result.trace.to_dict()
    assert trace["outcome"] == {"status": "accepted", "error": None}
    assert trace["final_replay"] is None
    assert all("state_summary" in row and "state" not in row for row in trace["intermediate_states"])


def test_rewrite_resolves_only_visible_equations() -> None:
    owner = start_macro_session("0 = 1 -> 0 = 0")
    owner = owner.with_session(
        run_surface(
            owner.session,
            "intro h",
            capabilities=owner.capabilities,
            record_trace=False,
        )
    )
    result = execute_macro(owner, serialize_macro(Rewrite("h", "forward")))
    assert result.trace.to_dict()["state_after"]["goals"] == ["h : 0 = 1 ⊢ 1 = 0"]
    with pytest.raises(MacroExecutionError, match="not a visible") as failure:
        execute_macro(owner, serialize_macro(Rewrite("hidden", "forward")))
    assert failure.value.owner is owner


def test_multicommand_failure_rolls_back_state_history_and_trace() -> None:
    owner = start_macro_session("0 = 0")
    state, replay, trace_count = owner.state, owner.replay_steps, owner.trace.record_count
    with pytest.raises(MacroExecutionError, match="universally quantified") as failure:
        execute_macro(owner, serialize_macro(Use("add_comm", ("0", "0", "0"))))
    assert failure.value.owner is owner
    assert owner.state is state and owner.replay_steps is replay
    assert owner.trace.record_count == trace_count
    evidence = failure.value.trace.to_dict()
    assert evidence["state_after"] == evidence["state_before"]
    assert [row["command"] for row in evidence["intermediate_states"]] == [
        "use add_comm",
        "specialize add_comm 0",
        "specialize add_comm 0",
    ]


def test_unknown_version_and_oversize_raw_are_inert_and_transactional() -> None:
    owner = start_macro_session("0 = 0")
    proposal = json.dumps(
        {"format": MACRO_FORMAT, "v": 2, "action": "Witness", "term": "0"}
    )
    with pytest.raises(MacroExecutionError, match="unsupported macro version") as failure:
        execute_macro(owner, proposal)
    assert failure.value.trace.to_dict()["compile"]["status"] == "not-attempted"

    huge = " " * (MAX_MACRO_BYTES + 1)
    with pytest.raises(MacroExecutionError, match="exceeds") as failure:
        execute_macro(owner, huge)
    raw = failure.value.trace.to_dict()["raw_proposal"]
    payload = huge.encode("utf-8")
    assert raw["text"] is raw["base64"] is None
    assert raw["bytes"] == len(payload)
    assert raw["sha256"] == hashlib.sha256(payload).hexdigest()


def _set_sha256(names: frozenset[str]) -> str:
    wire = json.dumps(sorted(names), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(wire).hexdigest()


def test_trace_binds_profile_theorem_logic_and_stable_capability_identity() -> None:
    trace = _run("0 = 0", Cut("have", "h", "0 = 0")).trace.to_dict()
    environment = trace["environment"]
    assert environment["logic"] == "intuitionistic"
    assert environment["classical"] is False
    assert environment["original_theorem"] == "0 = 0"
    assert environment["owner_capability_identity"]["label"] == "full"
    assert environment["effective_command_capability"]["sha256"] == _set_sha256(SURFACE_COMMAND_NAMES)
    assert environment["effective_theorem_capability"]["sha256"] == _set_sha256(SURFACE_THEOREM_NAMES)
    assert environment["macro_protocol_identity"] == macro_protocol_identity()


def test_capability_is_owned_and_prior_replay_is_checked_against_it() -> None:
    restricted = SurfaceCapabilities(
        label="macro-no-library",
        allowed_commands=frozenset({"use"}),
        allowed_theorems=frozenset(),
    )
    owner = start_macro_session("0 = 0", capabilities=restricted)
    with pytest.raises(MacroExecutionError, match="unavailable"):
        execute_macro(owner, serialize_macro(Use("zero_add")))
    with pytest.raises(MacroRunnerError, match="capability identity mismatch"):
        replace(owner, capability_identity_json="{}")

    full = start_macro_session("0 = 0 -> 0 = 0")
    advanced = full.with_session(
        run_surface(
            full.session,
            "intro h",
            capabilities=full.capabilities,
            record_trace=False,
        )
    )
    no_intro = SurfaceCapabilities(
        label="no-intro",
        allowed_commands=frozenset({"refl"}),
        allowed_theorems=frozenset(),
    )
    forged = MacroOwner(
        advanced.session,
        no_intro,
        macro_runner._canonical_json(macro_runner._capability_identity(no_intro)),
        advanced.semantic_profile_identity_json,
    )
    with pytest.raises(MacroRunnerError, match="incompatible"):
        execute_macro(forged, serialize_macro(Split("left")))


def test_dispatch_identity_is_derived_and_callbacks_are_not_registrable(tmp_path: Path) -> None:
    registration = _probe(tmp_path)
    identity = registration.identity
    assert identity.format == DISPATCH_ADAPTER_IDENTITY_FORMAT
    assert identity.v == DISPATCH_ADAPTER_IDENTITY_VERSION
    assert DispatchAdapterIdentity.from_object(identity.to_dict()) == identity
    assert identity.artifact_sha256 == hashlib.sha256(Path(registration.artifact_path).read_bytes()).hexdigest()
    with pytest.raises((TypeError, DispatchProtocolError)):
        DispatchAdapterRegistration(identity, object(), "{}")  # type: ignore[arg-type]


def test_dispatch_registry_and_identity_mismatch_fail_closed(tmp_path: Path) -> None:
    owner = start_macro_session("0 = 0")
    proposal = serialize_macro(Dispatch("test-solver", (), BOUNDS))
    with pytest.raises(DispatchProtocolError, match="provenance registration"):
        execute_macro(owner, proposal, dispatch_adapters={"test-solver": object()})  # type: ignore[dict-item]
    registration = _probe(tmp_path)
    Path(registration.artifact_path).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    Path(registration.artifact_path).chmod(0o700)
    with pytest.raises(DispatchProtocolError, match="identity mismatch"):
        execute_macro(owner, proposal, dispatch_adapters={"test-solver": registration})


def test_registry_reconstructs_and_rejects_forged_exact_registration(
    tmp_path: Path,
) -> None:
    real = _probe(tmp_path)
    owner = start_macro_session("0 = 0")
    proposal = serialize_macro(Dispatch("test-solver", (), BOUNDS))

    def forged_registration(
        identity: DispatchAdapterIdentity,
        artifact_path: str,
        configuration_json: str,
    ) -> DispatchAdapterRegistration:
        forged = object.__new__(DispatchAdapterRegistration)
        object.__setattr__(forged, "identity", identity)
        object.__setattr__(forged, "artifact_path", artifact_path)
        object.__setattr__(forged, "configuration_json", configuration_json)
        return forged

    noncanonical = '{ "commands": ["refl"] }'
    noncanonical_identity = DispatchAdapterIdentity(
        "test-solver",
        "source",
        real.identity.artifact_sha256,
        hashlib.sha256(noncanonical.encode("utf-8")).hexdigest(),
    )
    forged = forged_registration(
        noncanonical_identity,
        real.artifact_path,
        noncanonical,
    )
    with pytest.raises(DispatchProtocolError, match="not canonical"):
        execute_macro(
            owner,
            proposal,
            dispatch_adapters={"test-solver": forged},
        )

    relative = forged_registration(real.identity, "dispatch-probe.py", "{}")
    with pytest.raises(DispatchProtocolError, match="must be absolute"):
        execute_macro(
            owner,
            proposal,
            dispatch_adapters={"test-solver": relative},
        )

    Path(real.artifact_path).chmod(0o600)
    nonexecutable = forged_registration(real.identity, real.artifact_path, "{}")
    with pytest.raises(DispatchProtocolError, match="executable"):
        execute_macro(
            owner,
            proposal,
            dispatch_adapters={"test-solver": nonexecutable},
        )
    assert owner.trace.record_count == 0


def test_detached_dispatch_reconstructs_and_freshly_kernel_checks(tmp_path: Path) -> None:
    result, registration, original = _execute_dispatch(
        tmp_path,
        premises=("PA3",),
        expected_theorem="0 = 0",
        expected_premise="PA3",
    )
    assert result.closed and result.certificate is not None
    assert result.public_commands == ("refl",)
    assert original.trace.record_count == 0
    solver = result.trace.to_dict()["solver"]
    assert solver["authority"] == "untrusted-status-reconstruction-required"
    assert solver["request_sha256"] == solver["dispatch_call_request_sha256"]
    assert solver["request_sha256"] == result.trace.to_dict()["compile"]["dispatch_request_sha256"]
    assert solver["adapter_identity"] == registration.identity.to_dict()
    assert solver["adapter_configuration"] == registration.configuration
    assert solver["step_accounting"] == "untrusted-adapter-reported-not-host-enforced"
    call = macro_runner._dispatch_call_record(
        adapter_identity=solver["adapter_identity"],
        configuration=solver["adapter_configuration"],
        request=solver["request"],
        request_sha256=solver["request_sha256"],
        context=solver["context"],
    )
    assert hashlib.sha256(
        macro_runner._canonical_json(call).encode("utf-8")
    ).hexdigest() == solver["dispatch_call_sha256"]
    raw = b64decode(solver["raw_response_base64"], validate=True)
    assert hashlib.sha256(raw).hexdigest() == solver["raw_response_sha256"]
    assert solver["host_usage"]["process_limit"] == 1
    assert solver["host_usage"]["peak_processes"] <= 1
    assert solver["host_usage"]["campaign_host_eligible"] is sys.platform.startswith("linux")
    final = result.trace.to_dict()["final_replay"]
    assert final["kernel_accepted"] is True
    assert final["original_theorem"] == "0 = 0"
    assert final["commands"] == ["refl"]
    assert final["certificate_nodes"] == final["certificate_depth"] == 1


@pytest.mark.parametrize(
    ("configuration", "message"),
    [
        ({"commands": []}, "status alone has no authority"),
        ({"commands": ["qed"]}, "hidden/session command"),
        ({"commands": [" refl"]}, "canonical physical line"),
        ({"commands": ["refl"], "steps_used": 21}, "steps_used 21 exceeds"),
        (
            {"commands": ["refl", "refl"], "steps_used": 1},
            "step accounting is smaller",
        ),
        ({"commands": ["refl"] * 257, "steps_used": 257}, "more than 256 commands"),
        ({"status": "forged-proof"}, "registered v1 enum"),
    ],
)
def test_untrusted_status_and_commands_have_no_authority(
    tmp_path: Path, configuration: dict[str, object], message: str
) -> None:
    registration = _probe(tmp_path, **configuration)
    owner = start_macro_session("0 = 0")
    with pytest.raises(MacroExecutionError, match=message) as failure:
        execute_macro(
            owner,
            serialize_macro(Dispatch("test-solver", (), BOUNDS)),
            dispatch_adapters={"test-solver": registration},
        )
    assert failure.value.owner is owner
    trace = failure.value.trace.to_dict()
    assert trace["state_after"] == trace["state_before"]
    assert owner.trace.record_count == 0


def test_dispatch_rejects_noncanonical_response_and_counts_command_bytes(tmp_path: Path) -> None:
    noncanonical = json.dumps(
        {
            "format": "peano-hydra-dispatch-response",
            "v": 1,
            "status": "theorem",
            "steps_used": 1,
            "public_commands": ["refl"],
        }
    )
    with pytest.raises(MacroExecutionError, match="not canonical"):
        _execute_dispatch(tmp_path, mode="raw", raw=noncanonical)

    canonical = json.dumps(
        {
            "format": "peano-hydra-dispatch-response",
            "v": 1,
            "status": "theorem",
            "steps_used": 1,
            "public_commands": ["refl"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    tight = DispatchBounds(20, 3_000, 256 * 1024 * 1024, len(canonical) + 3)
    with pytest.raises(MacroExecutionError, match="raw response plus reconstructed"):
        _execute_dispatch(tmp_path, bounds=tight)


def test_malformed_dispatch_shape_retains_raw_and_host_evidence(tmp_path: Path) -> None:
    owner = start_macro_session("0 = 0")
    registration = _probe(tmp_path, mode="raw", raw="{}")
    with pytest.raises(MacroExecutionError, match="registered v1 fields") as failure:
        execute_macro(
            owner,
            serialize_macro(Dispatch("test-solver", (), BOUNDS)),
            dispatch_adapters={"test-solver": registration},
        )
    assert failure.value.owner is owner
    trace = failure.value.trace.to_dict()
    assert trace["state_after"] == trace["state_before"]
    solver = trace["solver"]
    raw = b64decode(solver["raw_response_base64"], validate=True)
    assert raw == b"{}"
    assert solver["raw_response_bytes"] == 2
    assert solver["raw_response_sha256"] == hashlib.sha256(raw).hexdigest()
    assert solver["host_usage"] is not None
    assert solver["host_usage"]["output_bytes"] == 2


def test_global_output_plus_one_is_bounded_rejection_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bounds = DispatchBounds(
        20,
        3_000,
        256 * 1024 * 1024,
        macro_runner.MAX_DISPATCH_OUTPUT_BYTES,
    )
    raw = b"x" * macro_runner.MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES
    memory_enforcement = (
        "linux-rlimit-as-data+sampled-leader-rss"
        if sys.platform.startswith("linux")
        else "darwin-sampled-leader-rss-only"
    )
    usage = macro_runner.DispatchHostUsage(
        wall_time_ms=1,
        output_bytes=len(raw),
        reconstructed_command_bytes=0,
        max_observed_rss_bytes=0,
        peak_processes=1,
        exit_code=-25,
        timed_out=False,
        wall_limit_ms=bounds.max_wall_time_ms,
        memory_limit_bytes=bounds.max_memory_bytes,
        output_limit_bytes=bounds.max_output_bytes,
        process_limit=1,
        memory_enforcement=memory_enforcement,
        process_enforcement="rlimit-nproc-one",
        campaign_host_eligible=sys.platform.startswith("linux"),
    )

    def reject_over_limit(*args, **kwargs):
        del args, kwargs
        raise macro_runner._DispatchHostFailure(
            "dispatch subprocess exceeded its output bound",
            raw_response=raw,
            host_usage=usage,
        )

    monkeypatch.setattr(macro_runner, "_invoke_dispatch_subprocess", reject_over_limit)
    owner = start_macro_session("0 = 0")
    registration = _probe(tmp_path)
    with pytest.raises(MacroExecutionError, match="output bound") as failure:
        execute_macro(
            owner,
            serialize_macro(Dispatch("test-solver", (), bounds)),
            dispatch_adapters={"test-solver": registration},
        )
    assert failure.value.owner is owner
    trace = failure.value.trace.to_dict()
    assert trace["state_after"] == trace["state_before"]
    assert trace["solver"]["raw_response_bytes"] == len(raw)
    assert len(
        b64decode(trace["solver"]["raw_response_base64"], validate=True)
    ) == len(raw)
    MacroTrace.from_record(trace)


@pytest.mark.parametrize(
    ("configuration", "bounds", "message"),
    [
        (
            {"mode": "sleep", "seconds": 10},
            DispatchBounds(20, 80, 256 * 1024 * 1024, 4_096),
            "wall-time bound",
        ),
        (
            {"mode": "oversize", "bytes": 16_384},
            DispatchBounds(20, 3_000, 256 * 1024 * 1024, 512),
            "output bound|unsuccessfully|not strict UTF-8 JSON",
        ),
        (
            {"mode": "memory", "bytes": 128 * 1024 * 1024},
            DispatchBounds(20, 3_000, 32 * 1024 * 1024, 4_096),
            "memory bound|unsuccessfully",
        ),
    ],
)
def test_host_enforces_wall_output_and_memory_bounds(
    tmp_path: Path,
    configuration: dict[str, object],
    bounds: DispatchBounds,
    message: str,
) -> None:
    with pytest.raises(MacroExecutionError, match=message) as failure:
        _execute_dispatch(tmp_path, bounds=bounds, **configuration)
    evidence = failure.value.trace.to_dict()["solver"]
    assert evidence["error"]
    if evidence["host_usage"] is not None:
        assert evidence["host_usage"]["memory_limit_bytes"] == bounds.max_memory_bytes
        assert evidence["host_usage"]["output_limit_bytes"] == bounds.max_output_bytes
        assert evidence["host_usage"]["wall_limit_ms"] == bounds.max_wall_time_ms


def test_host_blocks_adapter_fork_attempt(tmp_path: Path) -> None:
    result, _, _ = _execute_dispatch(tmp_path, mode="fork")
    assert result.closed
    solver = result.trace.to_dict()["solver"]
    assert solver["response_status"] == "unknown"
    assert solver["host_usage"]["process_enforcement"] == "rlimit-nproc-one"
    assert solver["host_usage"]["peak_processes"] <= 1


def test_missing_dispatch_premise_rejects_before_process_invocation(tmp_path: Path) -> None:
    registration = _probe(tmp_path)
    owner = start_macro_session("0 = 0")
    with pytest.raises(MacroExecutionError, match="premise 'invented' is unavailable") as failure:
        execute_macro(
            owner,
            serialize_macro(Dispatch("test-solver", ("invented",), BOUNDS)),
            dispatch_adapters={"test-solver": registration},
        )
    solver = failure.value.trace.to_dict()["solver"]
    assert solver["adapter_configuration"] == registration.configuration
    assert solver["dispatch_call_request_sha256"] is None
    assert solver["dispatch_call_sha256"] is None
    assert solver["raw_response_bytes"] is None
    assert solver["host_usage"] is None


def test_fresh_replay_rejection_rolls_back_after_solver_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registration = _probe(tmp_path)
    owner = start_macro_session("0 = 0")

    def reject_final(*args, **kwargs):
        del args, kwargs
        raise InvalidProof("deliberate fresh-kernel rejection")

    monkeypatch.setattr(macro_runner, "checked_surface_final", reject_final)
    with pytest.raises(MacroExecutionError, match="fresh original-goal") as failure:
        execute_macro(
            owner,
            serialize_macro(Dispatch("test-solver", (), BOUNDS)),
            dispatch_adapters={"test-solver": registration},
        )
    trace = failure.value.trace.to_dict()
    assert failure.value.owner is owner
    assert trace["state_after"] == trace["state_before"]
    assert trace["final_replay"]["status"] == "rejected"
    assert trace["final_replay"]["kernel_accepted"] is False


def test_cumulative_owner_limit_rejects_before_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = start_macro_session("0 = 0 /\\ 0 = 0")
    monkeypatch.setattr(macro_runner, "MAX_OWNER_REPLAY_STEPS", 0)
    with pytest.raises(MacroExecutionError, match="cumulative replay-step") as failure:
        execute_macro(owner, serialize_macro(Split("conjunction")))
    assert failure.value.trace.to_dict()["intermediate_states"] == []


def test_trace_is_canonical_deterministic_and_recomputes_relations() -> None:
    proposal = serialize_macro(Cut("have", "h", "0 = 0"))
    first = execute_macro(start_macro_session("0 = 0"), proposal).trace
    second = execute_macro(start_macro_session("0 = 0"), proposal).trace
    assert first.canonical_json == second.canonical_json
    assert first.sha256 == second.sha256
    assert first.jsonl() == first.canonical_json + "\n"

    attacks = []
    for mutation in (
        lambda row: row["environment"].pop("semantic_profile_identity"),
        lambda row: row["environment"].__setitem__("original_theorem", "0 = 1"),
        lambda row: row["environment"].__setitem__("owner_capability_sha256", "0" * 64),
        lambda row: row["parse"].__setitem__("canonical_sha256", "0" * 64),
        lambda row: row["state_before"].__setitem__("closed", True),
        lambda row: row["state_after"].__setitem__("goals_sha256", "0" * 64),
        lambda row: row["intermediate_states"][0]["state_summary"].__setitem__("history_length", 9),
    ):
        forged = copy.deepcopy(first.to_dict())
        mutation(forged)
        attacks.append(forged)
    for forged in attacks:
        with pytest.raises((TypeError, ValueError, DispatchProtocolError, MacroRunnerError)):
            MacroTrace.from_record(forged)


@pytest.mark.parametrize(
    ("constant", "mutated"),
    [
        ("MACRO_TRACE_FORMAT", "peano-hydra-macro-trace-v2"),
        ("MACRO_TRACE_VERSION", 2),
        ("DISPATCH_ADAPTER_IDENTITY_FORMAT", "peano-hydra-dispatch-adapter-v2"),
        ("DISPATCH_ADAPTER_IDENTITY_VERSION", 2),
        ("DISPATCH_CALL_FORMAT", "peano-hydra-dispatch-call-v2"),
        ("DISPATCH_CALL_VERSION", 2),
        ("DISPATCH_RESPONSE_FORMAT", "peano-hydra-dispatch-response-v2"),
        ("DISPATCH_RESPONSE_VERSION", 2),
    ],
)
def test_registered_contract_pins_runner_owned_trace_and_adapter_identity(
    monkeypatch: pytest.MonkeyPatch,
    constant: str,
    mutated: object,
) -> None:
    monkeypatch.setattr(macro_runner, constant, mutated)
    with pytest.raises(MacroRunnerError, match="identity drifted"):
        macro_runner._validate_registered_trace_contract()


@pytest.mark.parametrize(
    "constant",
    ["MAX_DISPATCH_CALL_BYTES", "MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES"],
)
def test_registered_contract_pins_runner_owned_evidence_limits(
    monkeypatch: pytest.MonkeyPatch,
    constant: str,
) -> None:
    monkeypatch.setattr(macro_runner, constant, getattr(macro_runner, constant) + 1)
    with pytest.raises(MacroRunnerError, match="evidence limits drifted"):
        macro_runner._validate_registered_trace_contract()


def test_registered_contract_pins_resource_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forged = copy.deepcopy(macro_runner._DISPATCH_RESOURCE_SEMANTICS)
    forged["steps_used"]["host_enforced"] = True
    monkeypatch.setattr(macro_runner, "_DISPATCH_RESOURCE_SEMANTICS", forged)
    with pytest.raises(MacroRunnerError, match="resource semantics drifted"):
        macro_runner._validate_registered_trace_contract()


def test_solver_trace_rejects_mutated_bounds_identity_and_final_metrics(tmp_path: Path) -> None:
    trace = _execute_dispatch(tmp_path, premises=("PA3",))[0].trace.to_dict()
    for mutation in (
        lambda row: row["solver"]["request"]["bounds"].__setitem__("max_steps", 19),
        lambda row: row["solver"].__setitem__("dispatch_call_request_sha256", "0" * 64),
        lambda row: row["solver"]["adapter_identity"].__setitem__("artifact_sha256", "0" * 64),
        lambda row: row["solver"]["adapter_configuration"].__setitem__("forged", True),
        lambda row: row["solver"].__setitem__("adapter_configuration", []),
        lambda row: row["solver"].__setitem__("dispatch_call_sha256", "0" * 64),
        lambda row: (
            row["solver"].__setitem__("dispatch_call_sha256", None),
            row["solver"].__setitem__("dispatch_call_request_sha256", None),
        ),
        lambda row: row["solver"].__setitem__("step_accounting", "host-enforced"),
        lambda row: row["solver"]["host_usage"].__setitem__("memory_limit_bytes", 1),
        lambda row: row["solver"]["host_usage"].__setitem__(
            "campaign_host_eligible",
            not row["solver"]["host_usage"]["campaign_host_eligible"],
        ),
        lambda row: row["solver"]["host_usage"].__setitem__("wall_limit_ms", 1),
        lambda row: row["solver"]["host_usage"].__setitem__("wall_time_ms", 3_001),
        lambda row: row["solver"]["host_usage"].__setitem__("output_limit_bytes", 1),
        lambda row: row["solver"].__setitem__("response_status", "unknown"),
        lambda row: row["solver"]["context"]["premises"][0].__setitem__("formula", "0 = 1"),
        lambda row: row["final_replay"].__setitem__("certificate_nodes", 2),
        lambda row: row["final_replay"].__setitem__("certificate_sha256", "0" * 64),
        lambda row: row["final_replay"].__setitem__("original_theorem", "0 = 1"),
    ):
        forged = copy.deepcopy(trace)
        mutation(forged)
        with pytest.raises((TypeError, ValueError, DispatchProtocolError, MacroRunnerError)):
            MacroTrace.from_record(forged)


def test_trace_cannot_promote_status_only_or_rehash_fabricated_state(tmp_path: Path) -> None:
    registration = _probe(tmp_path, commands=[])
    owner = start_macro_session("0 = 0")
    with pytest.raises(MacroExecutionError) as failure:
        execute_macro(
            owner,
            serialize_macro(Dispatch("test-solver", (), BOUNDS)),
            dispatch_adapters={"test-solver": registration},
        )
    promoted = failure.value.trace.to_dict()
    promoted["outcome"] = {"status": "accepted", "error": None}
    promoted["solver"]["error"] = None
    with pytest.raises((TypeError, ValueError, DispatchProtocolError, MacroRunnerError)):
        MacroTrace.from_record(promoted)

    accepted = _run("0 = 0", Cut("have", "h", "0 = 0")).trace.to_dict()
    forged = copy.deepcopy(accepted)
    forged["state_after"]["history"][0]["args"] = "forged"
    state_payload = {
        key: forged["state_after"][key]
        for key in macro_runner._STATE_FIELDS
        if key != "state_sha256"
    }
    forged["state_after"]["state_sha256"] = macro_runner._json_sha256(
        "peano-hydra-macro-state-v1", state_payload
    )
    with pytest.raises((TypeError, ValueError, DispatchProtocolError, MacroRunnerError)):
        MacroTrace.from_record(forged)


def test_all_error_fields_enforce_frozen_text_bounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    traces_and_paths: list[tuple[dict[str, object], tuple[str, ...]]] = []

    owner = start_macro_session("0 = 0")
    with pytest.raises(MacroExecutionError) as parse_failure:
        execute_macro(owner, "not-json")
    traces_and_paths.append((parse_failure.value.trace.to_dict(), ("parse", "error")))
    traces_and_paths.append((parse_failure.value.trace.to_dict(), ("outcome", "error")))

    restricted = SurfaceCapabilities(
        label="no-library",
        allowed_commands=frozenset({"use"}),
        allowed_theorems=frozenset(),
    )
    with pytest.raises(MacroExecutionError) as compile_failure:
        execute_macro(
            start_macro_session("0 = 0", capabilities=restricted),
            serialize_macro(Use("zero_add")),
        )
    traces_and_paths.append(
        (compile_failure.value.trace.to_dict(), ("compile", "error"))
    )

    registration = _probe(tmp_path, commands=[])
    with pytest.raises(MacroExecutionError) as solver_failure:
        execute_macro(
            owner,
            serialize_macro(Dispatch("test-solver", (), BOUNDS)),
            dispatch_adapters={"test-solver": registration},
        )
    traces_and_paths.append((solver_failure.value.trace.to_dict(), ("solver", "error")))

    def reject_final(*args, **kwargs):
        del args, kwargs
        raise InvalidProof("deliberate final rejection")

    monkeypatch.setattr(macro_runner, "checked_surface_final", reject_final)
    registration = _probe(tmp_path)
    with pytest.raises(MacroExecutionError) as final_failure:
        execute_macro(
            owner,
            serialize_macro(Dispatch("test-solver", (), BOUNDS)),
            dispatch_adapters={"test-solver": registration},
        )
    traces_and_paths.append(
        (final_failure.value.trace.to_dict(), ("final_replay", "error"))
    )

    for trace, path in traces_and_paths:
        forged = copy.deepcopy(trace)
        target = forged
        for component in path[:-1]:
            target = target[component]  # type: ignore[index,assignment]
        target[path[-1]] = "x" * 2_001  # type: ignore[index]
        with pytest.raises((TypeError, ValueError, DispatchProtocolError)):
            MacroTrace.from_record(forged)


def test_trace_cumulative_byte_limit_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    trace = _run("0 = 0", Cut("have", "h", "0 = 0")).trace.to_dict()
    monkeypatch.setattr(macro_runner, "MAX_MACRO_TRACE_BYTES", 128)
    with pytest.raises(ValueError, match="cumulative byte limit"):
        MacroTrace.from_record(trace)
