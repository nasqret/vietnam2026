"""Self-contained, fail-closed H0.3 macro-protocol evidence controls.

This module is evidence plumbing, not a second macro implementation.  It
constructs typed actions through :mod:`training.peano_hydra.macros`, executes
them through the transactional runner, and retains the exact byte preimages
needed to audit the resulting hashes.  The main H0 validator supplies the
focused pytest transcript so process orchestration stays in one place.
"""

from __future__ import annotations

from base64 import b64decode
from pathlib import Path
import tempfile

from peano_lab.engine.state import proof_metrics
from peano_lab.kernel.artifact_codec import encode_artifact_bounded
from peano_lab.kernel.checker import check

from .conformance import canonical_json_bytes, digest_bytes, digest_json
from .macros import (
    DISPATCH_CALL_FORMAT,
    DISPATCH_CALL_VERSION,
    Cut,
    Dispatch,
    DispatchBounds,
    Induct,
    Rewrite,
    Split,
    Use,
    Witness,
    compile_macro,
    macro_object,
    macro_protocol_identity,
    macro_sha256,
    parse_macro,
    serialize_macro,
)
from . import macro_runner
from .macro_runner import (
    MacroExecutionError,
    MacroTrace,
    execute_macro,
    register_dispatch_subprocess,
    start_macro_session,
)


PROTOCOL_IDENTITY = {
    "format": "peano-hydra-macro-protocol",
    "v": 1,
    "id": "peano-hydra-macro-v1",
    "semantic_sha256": (
        "b5fef1ea1b85251ab7f0b8c111cb37e789f96f20771665b4f0dc8b746400552c"
    ),
    "document_sha256": (
        "6f6920d2d952251170733674a3af8da09926f4faf19215317a32bc0317d4a482"
    ),
}
FIXTURE_ROOT_SHA256 = (
    "e9e7f0f4c6e6c399de75dbea876d55b57e58a823abc85cffbcfbb519cb740c62"
)
ACCEPTED_TRACE_SHA256 = (
    "b396bae45b4aafa3efe3640bee45c337abffac02a7cb4ea4e152a918e3629a76"
)
REJECTED_TRACE_SHA256 = (
    "4cb1a4804f6260111765ce57269451d1491bb36893f1fb4b8a5ef6c7c50d1a58"
)
ADAPTER_SHA256 = "8861de39f85b1af892e8ffbadd1bcf14ec358e6aeec4c2ec9cc0c53587592412"
CONFIGURATION_SHA256 = (
    "1ed4c986119b16a62540e9e7a5c597d084a0989f74fc775bb2274f911a086a3f"
)
REQUEST_SHA256 = "f9ea6bb402de64ddbbeeb1b67b65ebf95f5e7010c0d507f7b0a2c384748abf87"
CALL_SHA256 = "af478aa919ba73ead3d798ee17625951beb5e36adf3726d2b9cdc7c9f8cef186"
CERTIFICATE_SHA256 = (
    "703a79d71660b9629a40c2890815f1a3e5d06220686c7ce6968019cd768c38c0"
)

_BOUNDS = DispatchBounds(8, 3_000, 256 * 1024 * 1024, 4_096)
_CONFIGURATION = {"fixture": "h0.3-retained-dispatch-v1"}
_ADAPTER = (
    b"#!/bin/sh\n"
    b"printf '%s' '{\"format\":\"peano-hydra-dispatch-response\","
    b"\"public_commands\":[\"refl\"],\"status\":\"theorem\","
    b"\"steps_used\":1,\"v\":1}'\n"
)


class H0MacroEvidenceError(RuntimeError):
    """A required H0.3 relation was absent or inconsistent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise H0MacroEvidenceError(message)


def _preimage(value: str | bytes) -> dict[str, object]:
    raw = value.encode("utf-8") if type(value) is str else value
    _require(type(raw) is bytes, "evidence preimage must be exact UTF-8 bytes")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise H0MacroEvidenceError("evidence preimage must be UTF-8") from error
    _require(content.encode("utf-8") == raw, "evidence preimage did not round-trip")
    return {
        "bytes": len(raw),
        "content_utf8": content,
        "encoding": "utf-8",
        "sha256": digest_bytes(raw),
    }


def _request_record(request: object) -> dict[str, object]:
    try:
        bounds = request.bounds  # type: ignore[attr-defined]
        return {
            "solver": request.solver,  # type: ignore[attr-defined]
            "premises": list(request.premises),  # type: ignore[attr-defined]
            "bounds": {
                "max_steps": bounds.max_steps,
                "max_wall_time_ms": bounds.max_wall_time_ms,
                "max_memory_bytes": bounds.max_memory_bytes,
                "max_output_bytes": bounds.max_output_bytes,
            },
            "authority": request.authority,  # type: ignore[attr-defined]
        }
    except (AttributeError, TypeError) as error:
        raise H0MacroEvidenceError("compiled Dispatch fixture is malformed") from error


def _fixture_rows() -> list[dict[str, object]]:
    actions = (
        Use("zero_add", ("0",)),
        Cut("have", "h", "0 = 0"),
        Witness("0"),
        Induct("n", "n = n"),
        Rewrite("h", "backward", "IH"),
        Split("conjunction"),
        Dispatch("h0-fixture", ("PA3",), _BOUNDS),
    )
    rows: list[dict[str, object]] = []
    for action in actions:
        canonical = serialize_macro(action)
        parsed = parse_macro(canonical)
        compiled = compile_macro(parsed, available_solvers=("h0-fixture",))
        _require(
            parsed == action
            and serialize_macro(parsed) == canonical
            and compiled.action == parsed,
            "typed macro fixture did not round-trip and compile exactly",
        )
        preimage = _preimage(canonical)
        _require(
            preimage["sha256"] == macro_sha256(parsed),
            "typed macro fixture digest is inconsistent",
        )
        rows.append(
            {
                "action": type(parsed).__name__,
                "canonical_object": macro_object(parsed),
                "canonical_preimage": preimage,
                "compilation": {
                    "public_commands": list(compiled.public_commands),
                    "dispatch": (
                        None
                        if compiled.dispatch is None
                        else _request_record(compiled.dispatch)
                    ),
                },
            }
        )
    _require(
        [row["action"] for row in rows]
        == ["Use", "Cut", "Witness", "Induct", "Rewrite", "Split", "Dispatch"]
        and digest_json(rows) == FIXTURE_ROOT_SHA256,
        "typed macro fixture content root drifted",
    )
    return rows


def _trace(trace: MacroTrace, expected: str | None = None) -> dict[str, object]:
    record = trace.to_dict()
    raw = canonical_json_bytes(record)
    rebuilt = MacroTrace.from_record(record)
    _require(
        raw == trace.canonical_json.encode("utf-8")
        and rebuilt.canonical_json == trace.canonical_json
        and digest_bytes(raw) == trace.sha256
        and (expected is None or trace.sha256 == expected),
        "macro trace failed canonical reconstruction or its frozen root drifted",
    )
    return {
        "canonical_preimage": _preimage(raw),
        "record": record,
        "root_contract": "sha256 of the exact canonical compact JSON trace record",
        "root_sha256": trace.sha256,
    }


def _accepted_trace() -> dict[str, object]:
    proposal = serialize_macro(Cut("have", "h", "0 = 0"))
    first = execute_macro(start_macro_session("0 = 0"), proposal)
    second = execute_macro(start_macro_session("0 = 0"), proposal)
    _require(
        first.certificate is None
        and first.trace.canonical_json == second.trace.canonical_json,
        "accepted macro trace is not deterministic",
    )
    return {
        "deterministic_repetitions": 2,
        "exact_match": True,
        **_trace(first.trace, ACCEPTED_TRACE_SHA256),
    }


def _rejected_trace() -> dict[str, object]:
    owner = start_macro_session("0 = 0")
    session, state = owner.session, owner.state
    history, replay = owner.state.history, owner.replay_steps
    trace_count = owner.trace.record_count
    before = macro_runner._state_record(owner)
    rejected: MacroExecutionError | None = None
    try:
        execute_macro(owner, serialize_macro(Use("add_comm", ("0", "0", "0"))))
    except MacroExecutionError as error:
        rejected = error
    _require(rejected is not None, "transactional macro control was falsely accepted")
    assertions = {
        "owner_identity_preserved": rejected.owner is owner,
        "session_identity_preserved": owner.session is session,
        "state_identity_preserved": owner.state is state,
        "history_identity_preserved": owner.state.history is history,
        "replay_identity_preserved": owner.replay_steps is replay,
        "trace_record_count_unchanged": owner.trace.record_count == trace_count,
        "canonical_state_bytes_unchanged": (
            canonical_json_bytes(macro_runner._state_record(owner))
            == canonical_json_bytes(before)
        ),
    }
    evidence = _trace(rejected.trace, REJECTED_TRACE_SHA256)
    record = evidence["record"]
    _require(
        all(assertions.values())
        and type(record) is dict
        and record["state_before"] == before
        and record["state_after"] == before,
        "rejected macro did not retain exact rollback evidence",
    )
    return {
        "unchanged_owner_assertions": assertions,
        "owner_state_preimage": _preimage(canonical_json_bytes(before)),
        **evidence,
    }


def _dispatch_trace() -> dict[str, object]:
    artifact = _preimage(_ADAPTER)
    configuration = _preimage(canonical_json_bytes(_CONFIGURATION))
    _require(
        artifact["sha256"] == ADAPTER_SHA256
        and configuration["sha256"] == CONFIGURATION_SHA256,
        "retained Dispatch adapter/configuration identity drifted",
    )
    with tempfile.TemporaryDirectory(prefix="peano-h0-macro-dispatch-") as directory:
        path = Path(directory) / "adapter"
        path.write_bytes(_ADAPTER)
        path.chmod(0o700)
        registration = register_dispatch_subprocess(
            "h0-fixture",
            artifact_kind="source",
            artifact_path=path,
            configuration=dict(_CONFIGURATION),
        )
        owner = start_macro_session("0 = 0")
        before = macro_runner._state_record(owner)
        execution = execute_macro(
            owner,
            serialize_macro(Dispatch("h0-fixture", ("PA3",), _BOUNDS)),
            dispatch_adapters={"h0-fixture": registration},
        )
    _require(
        execution.closed
        and execution.certificate is not None
        and check((), execution.certificate, owner.original_target)
        and execution.owner.original_target == owner.original_target
        and macro_runner._state_record(owner) == before,
        "Dispatch did not freshly prove the owner-held original goal",
    )
    trace = _trace(execution.trace)
    record = trace["record"]
    _require(type(record) is dict and type(record["solver"]) is dict, "missing solver trace")
    solver = record["solver"]
    request = solver["request"]
    request_preimage = _preimage(canonical_json_bytes(request))
    call = {
        "format": DISPATCH_CALL_FORMAT,
        "v": DISPATCH_CALL_VERSION,
        "adapter_identity": solver["adapter_identity"],
        "configuration": solver["adapter_configuration"],
        "request": request,
        "request_sha256": solver["request_sha256"],
        "context": solver["context"],
    }
    call_preimage = _preimage(canonical_json_bytes(call))
    _require(
        request_preimage["sha256"] == REQUEST_SHA256
        == solver["request_sha256"]
        == solver["dispatch_call_request_sha256"]
        == record["compile"]["dispatch_request_sha256"]
        and call_preimage["sha256"] == CALL_SHA256 == solver["dispatch_call_sha256"]
        and solver["adapter_identity"] == registration.identity.to_dict()
        and solver["adapter_configuration"] == _CONFIGURATION,
        "Dispatch request/call preimages are inconsistent",
    )
    raw_response = b64decode(solver["raw_response_base64"], validate=True)
    _require(
        len(raw_response) == solver["raw_response_bytes"]
        and digest_bytes(raw_response) == solver["raw_response_sha256"],
        "Dispatch response preimage is inconsistent",
    )
    nodes, depth = proof_metrics(execution.certificate)
    certificate_bytes = encode_artifact_bounded(
        8 * nodes + 16,
        owner.original_target,
        execution.certificate,
        max_bytes=macro_runner.MAX_FINAL_ARTIFACT_BYTES,
    )
    certificate = _preimage(certificate_bytes)
    final = record["final_replay"]
    _require(
        type(final) is dict
        and final["status"] == "accepted"
        and final["fresh"] is True
        and final["kernel_accepted"] is True
        and final["original_theorem"] == "0 = 0"
        and final["commands"] == ["refl"]
        and final["certificate_nodes"] == nodes
        and final["certificate_depth"] == depth
        and certificate["sha256"] == CERTIFICATE_SHA256
        == final["certificate_sha256"],
        "Dispatch fresh original-goal replay evidence drifted",
    )
    return {
        "adapter": {
            "artifact_preimage": artifact,
            "configuration": dict(_CONFIGURATION),
            "configuration_preimage": configuration,
            "identity": registration.identity.to_dict(),
        },
        "certificate_artifact_preimage": certificate,
        "dispatch_call": {"preimage": call, "canonical_preimage": call_preimage},
        "dispatch_request": {
            "preimage": request,
            "canonical_preimage": request_preimage,
        },
        "fresh_original_goal_kernel_check": {
            "accepted": True,
            "context": "empty",
            "original_theorem": "0 = 0",
        },
        "raw_response_preimage": _preimage(raw_response),
        "trace": trace,
    }


def build_h0_macro_evidence() -> dict[str, object]:
    """Build behavioral H0.3 controls without accepting asserted test results."""

    identity = macro_protocol_identity()
    _require(identity == PROTOCOL_IDENTITY, "exact macro protocol identity drifted")
    fixtures = _fixture_rows()
    result = {
        "interpretation": (
            "H0.3 protocol/conformance controls; solver status has no proof authority"
        ),
        "macro_protocol_identity": identity,
        "typed_action_fixtures": {
            "count": len(fixtures),
            "order": [row["action"] for row in fixtures],
            "root_contract": "sha256 of canonical JSON over the ordered fixture rows",
            "root_sha256": FIXTURE_ROOT_SHA256,
            "rows": fixtures,
        },
        "accepted_deterministic_trace": _accepted_trace(),
        "transactional_rejected_trace": _rejected_trace(),
        "dispatch_reconstruction": _dispatch_trace(),
    }
    canonical_json_bytes(result)
    return result


__all__ = ["H0MacroEvidenceError", "build_h0_macro_evidence"]
