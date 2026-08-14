"""One-shot, offline Vampire assistance with checked Peano reconstruction.

This is a diagnostic preview, not an H0 live-dispatch registration and not a
proof rule.  The caller supplies an exact ordered premise list, executable,
arguments, and resource bounds.  Vampire's output is retained only by hash
and status.  Success means that the adapter's ordinary public commands closed
a fresh Peano Lab session and the resulting certificate passed the independent
kernel against the original goal.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from peano_lab.engine.state import proof_metrics, start
from peano_lab.engine.trace import TraceLogger
from peano_lab.kernel.artifact_codec import encode_artifact_bounded
from peano_lab.kernel.checker import axiom_formula, check
from peano_lab.kernel.formulas import (
    ParseError,
    Formula,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.library.theorems import THEOREMS
from peano_lab.ui.prove import (
    ProofSession,
    SurfaceCapabilities,
    checked_surface_final,
    run_surface,
)

from .vampire_adapter import (
    MAX_VAMPIRE_OUTPUT_BYTES,
    MAX_VAMPIRE_WALL_TIME_MS,
    VAMPIRE_RECONSTRUCTION_CLASS,
    VAMPIRE_TRANSLATION_CLASS,
    VampireAdapterError,
    VampirePremise,
    emit_tptp_problem,
    reconstruct_public_commands,
    run_vampire,
)


VAMPIRE_ASSISTANT_FORMAT = "peano-hydra-vampire-assistant"
VAMPIRE_ASSISTANT_VERSION = 1
MAX_CERTIFICATE_ARTIFACT_BYTES = 16 * 1024 * 1024
_PA_AXIOM_NAMES = tuple(f"PA{index}" for index in range(1, 7))
_PUBLIC_THEOREMS = {spec.name: spec for spec in THEOREMS}
_PREMISE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,127}\Z")


class VampireAssistantError(ValueError):
    """The one-shot assistant request is malformed before search can start."""


def _error_text(error: BaseException | str) -> str:
    text = str(error) if isinstance(error, BaseException) else error
    return " ".join(text.split())[:2_000] or type(error).__name__


def _closed_canonical_goal(source: object) -> tuple[str, Formula]:
    if type(source) is not str or not source:
        raise VampireAssistantError("goal must be non-empty canonical Peano text")
    try:
        formula, free_names = parse_formula_with_names(source)
    except (ParseError, TypeError, ValueError, RecursionError) as exc:
        raise VampireAssistantError(f"goal is not a Peano formula: {_error_text(exc)}") from None
    if free_names:
        raise VampireAssistantError(
            "goal must be closed; free names: " + ", ".join(free_names)
        )
    canonical = pretty_formula(formula, [])
    if source != canonical:
        raise VampireAssistantError(f"goal is not canonical; expected {canonical!r}")
    return canonical, formula


def _exact_names(value: object, *, label: str) -> tuple[str, ...]:
    if type(value) is not tuple or not all(
        type(item) is str and _PREMISE_NAME.fullmatch(item) is not None
        for item in value
    ):
        raise VampireAssistantError(f"{label} must be an exact Peano-name tuple")
    if len(value) != len(set(value)):
        raise VampireAssistantError(f"{label} must not contain duplicates")
    return value


def resolve_premises(
    premise_names: tuple[str, ...],
    *,
    premise_allowlist: frozenset[str] | None = None,
) -> tuple[VampirePremise, ...]:
    """Resolve exact public names without granting access to any other fact."""

    names = _exact_names(premise_names, label="premise_names")
    if premise_allowlist is not None:
        if type(premise_allowlist) is not frozenset or not all(
            type(item) is str and _PREMISE_NAME.fullmatch(item) is not None
            for item in premise_allowlist
        ):
            raise VampireAssistantError(
                "premise_allowlist must be an exact frozenset of names or null"
            )
        masked = tuple(name for name in names if name not in premise_allowlist)
        if masked:
            raise VampireAssistantError(
                "requested premise is masked by the explicit allow-list: "
                + ", ".join(masked)
            )

    resolved: list[VampirePremise] = []
    for name in names:
        axiom = axiom_formula(name) if name in _PA_AXIOM_NAMES else None
        if axiom is not None:
            resolved.append(
                VampirePremise(name, "pa-axiom", pretty_formula(axiom, []))
            )
            continue
        spec = _PUBLIC_THEOREMS.get(name)
        if spec is None:
            raise VampireAssistantError(f"unknown public PA premise {name!r}")
        try:
            statement, free_names = parse_formula_with_names(spec.statement)
        except (ParseError, TypeError, ValueError, RecursionError) as exc:
            raise VampireAssistantError(
                f"public theorem {name!r} has a malformed statement: {_error_text(exc)}"
            ) from None
        if free_names:
            raise VampireAssistantError(
                f"public theorem {name!r} is unexpectedly open"
            )
        resolved.append(
            VampirePremise(name, "public-theorem", pretty_formula(statement, []))
        )
    return tuple(resolved)


def _new_session(goal: str, formula: Formula, *, label: str) -> ProofSession:
    return ProofSession(
        state=start(formula, ()),
        original_target=formula,
        original_names=(),
        target_source=goal,
        classical=False,
        trace=TraceLogger(session_id=label),
    )


def _run_commands(
    goal: str,
    formula: Formula,
    commands: tuple[str, ...],
    capabilities: SurfaceCapabilities,
    *,
    label: str,
) -> tuple[ProofSession | None, str | None, str | None]:
    owner = _new_session(goal, formula, label=label)
    for command in commands:
        try:
            owner = run_surface(
                owner,
                command,
                capabilities=capabilities,
                record_trace=False,
            )
        except Exception as exc:  # untrusted surface: diagnostic rejection only
            return None, command, _error_text(exc)
    if not owner.state.is_done():
        return None, None, "reconstructed commands left open Peano goals"
    return owner, None, None


def _base_record(
    goal: str,
    premise_names: tuple[str, ...],
    arguments: tuple[str, ...],
    wall_time_ms: int,
    output_bytes: int,
) -> dict[str, object]:
    return {
        "arguments": list(arguments),
        "authority": "none",
        "campaign_host_eligible": False,
        "campaign_peak_metric_eligible": False,
        "campaign_usage_metric_eligible": False,
        "certificate_depth": None,
        "certificate_nodes": None,
        "certificate_representation": None,
        "certificate_sha256": None,
        "comparison_eligible": False,
        "diagnostic": None,
        "evaluation_eligible": False,
        "executable_sha256": None,
        "exit_code": None,
        "failed_command": None,
        "format": VAMPIRE_ASSISTANT_FORMAT,
        "goal": goal,
        "h0_host_contained": False,
        "kernel_accepted": False,
        "live_dispatch_registered": False,
        "mode": "offline-diagnostic",
        "output_bytes_limit": output_bytes,
        "output_limited": False,
        "output_sha256": None,
        "premise_names": list(premise_names),
        "problem_sha256": None,
        "publication_eligible": False,
        "reconstructed_commands": [],
        "reconstruction_class": VAMPIRE_RECONSTRUCTION_CLASS,
        "resolved_premises": [],
        "retrieval_eligible": False,
        "solver_status": "not-run",
        "solver_parse_error": None,
        "status": "rejected",
        "szs_statuses": [],
        "timed_out": False,
        "training_eligible": False,
        "translation_class": VAMPIRE_TRANSLATION_CLASS,
        "v": VAMPIRE_ASSISTANT_VERSION,
        "wall_time_limit_ms": wall_time_ms,
    }


def run_vampire_assistant(
    goal: str,
    premise_names: tuple[str, ...],
    *,
    executable: str | Path,
    arguments: tuple[str, ...],
    wall_time_ms: int,
    output_bytes: int,
    premise_allowlist: frozenset[str] | None = None,
) -> dict[str, object]:
    """Run one offline search and accept only freshly kernel-checked replay."""

    canonical_goal, formula = _closed_canonical_goal(goal)
    names = _exact_names(premise_names, label="premise_names")
    if (
        type(arguments) is not tuple
        or len(arguments) > 128
        or not all(type(item) is str and item and "\x00" not in item for item in arguments)
    ):
        raise VampireAssistantError("arguments must be a bounded exact text tuple")
    try:
        argument_bytes = sum(len(item.encode("utf-8")) for item in arguments)
    except UnicodeEncodeError as exc:
        raise VampireAssistantError(f"arguments are not UTF-8: {_error_text(exc)}") from None
    if argument_bytes > 64 * 1024:
        raise VampireAssistantError("arguments exceed their byte bound")
    if (
        type(wall_time_ms) is not int
        or not 1 <= wall_time_ms <= MAX_VAMPIRE_WALL_TIME_MS
    ):
        raise VampireAssistantError("wall_time_ms is outside its exact bound")
    if (
        type(output_bytes) is not int
        or not 1 <= output_bytes <= MAX_VAMPIRE_OUTPUT_BYTES
    ):
        raise VampireAssistantError("output_bytes is outside its exact bound")
    record = _base_record(canonical_goal, names, arguments, wall_time_ms, output_bytes)

    try:
        premises = resolve_premises(names, premise_allowlist=premise_allowlist)
    except VampireAssistantError as exc:
        record["diagnostic"] = _error_text(exc)
        return record
    record["resolved_premises"] = [
        {"kind": premise.kind, "name": premise.name, "statement": premise.formula}
        for premise in premises
    ]

    try:
        problem = emit_tptp_problem(
            canonical_goal,
            premises,
            requested_premises=names,
        )
        record["problem_sha256"] = problem.sha256
        evidence = run_vampire(
            executable,
            problem,
            arguments=arguments,
            wall_time_ms=wall_time_ms,
            output_bytes=output_bytes,
        )
    except (VampireAdapterError, OSError, ValueError, TypeError) as exc:
        record["diagnostic"] = "offline Vampire invocation rejected: " + _error_text(exc)
        return record

    record.update(
        {
            "executable_sha256": evidence.executable_sha256,
            "exit_code": evidence.exit_code,
            "output_limited": evidence.output_limited,
            "output_sha256": evidence.raw_sha256,
            "solver_parse_error": evidence.parse_error,
            "solver_status": evidence.status,
            "szs_statuses": list(evidence.szs_statuses),
            "timed_out": evidence.timed_out,
        }
    )
    commands = reconstruct_public_commands(problem, evidence)
    record["reconstructed_commands"] = list(commands)
    if not commands:
        record["diagnostic"] = "Vampire evidence yielded no reconstructable public command"
        return record

    public_names = frozenset(
        premise.name for premise in premises if premise.kind == "public-theorem"
    )
    capabilities = SurfaceCapabilities(
        label="hydra-vampire-offline-v1",
        allowed_commands=frozenset(command.split(maxsplit=1)[0] for command in commands),
        allowed_theorems=public_names,
    )
    candidate, failed_command, error = _run_commands(
        canonical_goal,
        formula,
        commands,
        capabilities,
        label="peano-hydra-vampire-candidate",
    )
    if candidate is None:
        record["failed_command"] = failed_command
        record["diagnostic"] = error
        return record

    # Replay from the original target once more.  The first session is only a
    # proposal probe; neither it nor Vampire contributes proof authority.
    fresh, failed_command, error = _run_commands(
        canonical_goal,
        formula,
        commands,
        capabilities,
        label="peano-hydra-vampire-final-replay",
    )
    if fresh is None:
        record["failed_command"] = failed_command
        record["diagnostic"] = "fresh replay failed: " + (error or "unknown error")
        return record
    try:
        certificate = checked_surface_final(fresh.state, formula, classical=False)
        if not check((), certificate, formula):
            raise VampireAssistantError("fresh independent kernel rejected certificate")
        nodes, depth = proof_metrics(certificate)
        artifact = encode_artifact_bounded(
            8 * nodes + 16,
            formula,
            certificate,
            max_bytes=MAX_CERTIFICATE_ARTIFACT_BYTES,
        )
    except Exception as exc:  # final authority failure is a diagnostic rejection
        record["diagnostic"] = "fresh original-goal kernel rejection: " + _error_text(exc)
        return record

    record.update(
        {
            "certificate_depth": depth,
            "certificate_nodes": nodes,
            "certificate_representation": "peano-lab-v2",
            "certificate_sha256": hashlib.sha256(artifact).hexdigest(),
            "diagnostic": None,
            "kernel_accepted": True,
            "status": "accepted",
        }
    )
    return record


def canonical_evidence_bytes(record: dict[str, object]) -> bytes:
    """Encode one result without paths, raw transcripts, or measured timing."""

    return (
        json.dumps(
            record,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


__all__ = [
    "VAMPIRE_ASSISTANT_FORMAT",
    "VAMPIRE_ASSISTANT_VERSION",
    "VampireAssistantError",
    "resolve_premises",
    "run_vampire_assistant",
    "canonical_evidence_bytes",
]
