"""Sound orchestration for bounded Peano Hydra candidate policies.

The policy and the search procedure are untrusted.  A successful search is
therefore replayed from the original theorem by :func:`peano_lab.batch.run_proof`.
That second execution is intentionally traced and finishes through Peano Lab's
independent kernel.  The runner publishes ``proof`` only when the search and
fresh replay agree on the theorem, command count, certificate size, logic mode,
and complete tactic/library authority.

This module does not know how a Hydra policy ranks proposals.  It consumes the
small ``CandidatePolicy`` protocol already owned by ``peano_policy.search`` so
symbolic, model, and teacher-oracle heads all cross the same verifier boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping

from peano_lab.batch import BatchResult, capability_sha256, run_proof
from peano_lab.kernel.formulas import (
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.ui.prove import SurfaceCapabilities
from training.peano_hydra.policy import HydraPortfolioPolicy
from training.peano_policy.search import (
    SearchLimits,
    SearchResult,
    SearchStatus,
    search as kernel_guided_search,
)


HYDRA_RUNNER_VERSION = 1
MAX_IDENTITY_JSON_BYTES = 1_000_000
SURFACE_MACRO_V0_INELIGIBILITY = (
    "surface-macro-v0 is pre-H0 plumbing without a registered provider "
    "attestation and raw-call evidence schema"
)


class HydraRunnerError(RuntimeError):
    """Base class for a runner failure that cannot authorize a proof."""


class HydraReplayError(HydraRunnerError):
    """A claimed search proof disagreed with its fresh traced replay."""


def _canonical_json_object(value: object, *, field: str) -> dict[str, object]:
    """Detach and validate an identity object as finite canonical JSON."""

    if type(value) is not dict:
        raise ValueError(f"{field} must be an exact JSON object")
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not canonical JSON: {exc}") from None
    if len(encoded) > MAX_IDENTITY_JSON_BYTES:
        raise ValueError(
            f"{field} exceeds the {MAX_IDENTITY_JSON_BYTES}-byte identity limit"
        )
    detached = json.loads(encoded.decode("utf-8"))
    if type(detached) is not dict:  # pragma: no cover - guarded above
        raise ValueError(f"{field} must remain a JSON object")
    return detached


def _canonical_theorem(source: str) -> str:
    if type(source) is not str or not source.strip():
        raise ValueError("theorem must be non-empty text")
    if source != source.strip() or source.splitlines() != [source]:
        raise ValueError("theorem must be exactly one line with no outer whitespace")
    try:
        formula, names = parse_formula_with_names(source)
    except RecursionError:
        raise ValueError("theorem exceeded the parser recursion boundary") from None
    except (ParseError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid theorem: {' '.join(str(exc).split())}") from None
    if names:
        raise ValueError(
            "theorem must be closed; quantify free variables explicitly: "
            + ", ".join(names)
        )
    return pretty_formula(formula, list(names))


def policy_environment(
    capabilities: SurfaceCapabilities,
    *,
    classical: bool = False,
) -> dict[str, object]:
    """Return the exact JSON identity a policy must bind before proposing.

    ``None`` capability fields mean the complete current public inventory.  The
    capability digest materializes that inventory in ``peano_lab.batch``; the
    human-readable fields here retain whether the caller deliberately selected
    a finite allowlist or the full surface.
    """

    if type(capabilities) is not SurfaceCapabilities:
        raise TypeError("capabilities must be an exact SurfaceCapabilities value")
    if type(classical) is not bool:
        raise TypeError("classical must be a Boolean")
    return {
        "classical": classical,
        "surface": capabilities.label,
        "environment_sha256": capability_sha256(capabilities),
        "capabilities": {
            "label": capabilities.label,
            "allowed_commands": (
                None
                if capabilities.allowed_commands is None
                else sorted(capabilities.allowed_commands)
            ),
            "allowed_theorems": (
                None
                if capabilities.allowed_theorems is None
                else sorted(capabilities.allowed_theorems)
            ),
        },
    }


def _policy_name(policy: HydraPortfolioPolicy) -> str:
    name = getattr(policy, "name", type(policy).__name__)
    if type(name) is not str or not name or name != name.strip():
        raise ValueError("policy name must be non-empty text with no outer whitespace")
    if name.splitlines() != [name]:
        raise ValueError("policy name must fit on one line")
    return name


def _policy_identity(
    policy: HydraPortfolioPolicy, name: str
) -> dict[str, object]:
    declared = getattr(policy, "evaluation_identity", None)
    if declared is None:
        raise ValueError("Hydra policy must declare evaluation_identity")
    identity = declared() if callable(declared) else declared
    detached = _canonical_json_object(identity, field="policy evaluation_identity")
    if detached.get("name") != name:
        raise ValueError("policy evaluation_identity must contain its exact name")
    return detached


def _declared_policy_environment(policy: HydraPortfolioPolicy) -> object | None:
    declared = getattr(policy, "policy_environment", None)
    return declared() if callable(declared) else declared


def _policy_records(policy: HydraPortfolioPolicy) -> tuple[object, ...]:
    if not hasattr(policy, "records"):
        raise ValueError("Hydra policy must expose an exact proposal records ledger")
    records = getattr(policy, "records")
    records = records() if callable(records) else records
    if type(records) is not tuple:
        raise ValueError("policy records must be an exact tuple")
    return records


def _record_dict(record: object) -> dict[str, object]:
    convert = getattr(record, "to_dict", None)
    value = convert() if callable(convert) else record
    return _canonical_json_object(value, field="proposal record")


def _degradation_reasons(
    records: tuple[dict[str, object], ...],
    result: SearchResult,
) -> tuple[str, ...]:
    """Identify provider outages without confusing tactic rejection with one.

    Candidate/tactic errors are normal proof search.  A head error or contract
    error means the checked proof (if any) remains sound, but the intended
    matched portfolio did not actually run and the row is ineligible for a
    comparison claim.
    """

    reasons: list[str] = []
    bad_statuses = {
        "error",
        "contract-error",
        "contract_error",
        "head-error",
        "head_error",
        "policy-error",
        "policy_error",
        "provider-error",
        "provider_error",
    }

    def visit(value: object, path: str) -> None:
        if type(value) is dict:
            mapping = value
            for key, child in mapping.items():
                child_path = f"{path}.{key}"
                if key in {"status", "kind", "outcome"} and type(child) is str:
                    if child.casefold() in bad_statuses:
                        reasons.append(f"{child_path}={child}")
                if key in {"contract_error", "head_error", "provider_error"}:
                    if child is not None and child is not False and child != "":
                        reasons.append(child_path)
                visit(child, child_path)
        elif type(value) is list:
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    for index, record in enumerate(records):
        visit(record, f"proposal_records[{index}]")
    for diagnostic in result.diagnostics:
        if diagnostic.kind == "policy_error":
            reasons.append(f"search:{diagnostic.kind}:{diagnostic.state_sha256}")
    return tuple(dict.fromkeys(reasons))


def _limits_dict(limits: SearchLimits) -> dict[str, int]:
    return {
        "max_depth": limits.max_depth,
        "beam_width": limits.beam_width,
        "candidates_per_state": limits.candidates_per_state,
        "max_model_calls": limits.max_model_calls,
        "max_states": limits.max_states,
    }


def _commands_sha256(commands: tuple[str, ...]) -> str:
    payload = json.dumps(
        list(commands),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class HydraRunResult:
    """One bounded search and, for a proof, its independent traced replay."""

    label: str
    status: SearchStatus
    theorem: str
    policy: str
    policy_identity: dict[str, object]
    environment: dict[str, object]
    limits: dict[str, int]
    search: SearchResult
    replay: BatchResult | None
    commands_sha256: str | None
    proposal_records: tuple[dict[str, object], ...]
    degraded: bool
    eligible_for_comparison: bool
    comparison_ineligibility_reasons: tuple[str, ...]
    degradation_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status != self.search.status:
            raise ValueError("runner status must equal the underlying search status")
        if self.status == "proof":
            if self.replay is None or self.commands_sha256 is None:
                raise ValueError("a proof result needs a binding traced replay")
        elif self.replay is not None or self.commands_sha256 is not None:
            raise ValueError("an unsuccessful search cannot publish replay proof data")
        if self.degraded is not bool(self.degradation_reasons):
            raise ValueError("degraded must exactly reflect degradation_reasons")
        if (
            type(self.degraded) is not bool
            or type(self.eligible_for_comparison) is not bool
        ):
            raise TypeError("comparison eligibility fields must be Booleans")
        if type(self.comparison_ineligibility_reasons) is not tuple or not all(
            type(reason) is str and reason
            for reason in self.comparison_ineligibility_reasons
        ):
            raise TypeError("comparison ineligibility reasons must be non-empty text")
        if self.degraded and self.eligible_for_comparison:
            raise ValueError("a degraded run cannot be comparison eligible")
        expected_eligible = not self.comparison_ineligibility_reasons
        if self.eligible_for_comparison is not expected_eligible:
            raise ValueError(
                "comparison eligibility must exactly reflect its ineligibility reasons"
            )

    @property
    def proved(self) -> bool:
        return self.status == "proof"

    @property
    def commands(self) -> tuple[str, ...]:
        return self.search.commands

    def to_dict(self, *, include_trace: bool = False) -> dict[str, object]:
        return {
            "v": HYDRA_RUNNER_VERSION,
            "label": self.label,
            "status": self.status,
            "proved": self.proved,
            "theorem": self.theorem,
            "policy": self.policy,
            "policy_identity": self.policy_identity,
            "environment": self.environment,
            "limits": self.limits,
            "commands_sha256": self.commands_sha256,
            "proposal_records": list(self.proposal_records),
            "degraded": self.degraded,
            "eligible_for_comparison": self.eligible_for_comparison,
            "comparison_ineligibility_reasons": list(
                self.comparison_ineligibility_reasons
            ),
            "degradation_reasons": list(self.degradation_reasons),
            "search": self.search.to_dict(),
            "replay": (
                None
                if self.replay is None
                else self.replay.to_dict(include_trace=include_trace)
            ),
        }


def _validate_replay(
    *,
    expected_theorem: str,
    expected_commands: tuple[str, ...],
    expected_nodes: int,
    expected_request_id: str,
    expected_session_id: str,
    expected_environment: Mapping[str, object],
    classical: bool,
    replay: BatchResult,
) -> None:
    """Reject every disagreement instead of weakening a search proof claim."""

    errors: list[str] = []
    expected_count = len(expected_commands)
    expected_environment_sha256 = expected_environment["environment_sha256"]
    expected_surface = expected_environment["surface"]

    if replay.request_id != expected_request_id:
        errors.append("request id")
    if replay.session_id != expected_session_id:
        errors.append("session id")
    if replay.status != "proved":
        errors.append(f"status {replay.status!r}")
    if replay.kernel_checked is not True:
        errors.append("kernel_checked")
    if replay.theorem != expected_theorem:
        errors.append("theorem")
    if replay.tactics_requested != expected_count:
        errors.append("requested command count")
    if replay.tactics_applied != expected_count:
        errors.append("applied command count")
    if replay.failed_tactics != 0 or replay.failed_step is not None:
        errors.append("failed command accounting")
    if replay.error_type is not None or replay.error is not None:
        errors.append("error fields")
    if replay.goals != ():
        errors.append("open goals")
    if replay.proof_nodes != expected_nodes:
        errors.append("certificate nodes")
    if replay.mode != "trace" or replay.trace is None:
        errors.append("binding trace")
    if replay.surface != expected_surface:
        errors.append("surface")
    if replay.environment_sha256 != expected_environment_sha256:
        errors.append("environment")
    if replay.classical is not classical:
        errors.append("logic mode")
    if replay.on_error != "stop":
        errors.append("transaction policy")

    if replay.trace is not None:
        footer = replay.trace[-1] if replay.trace else None
        if (
            type(footer) is not dict
            or footer.get("qed") is not True
            or footer.get("theorem") != expected_theorem
            or footer.get("proof_size") != expected_nodes
        ):
            errors.append("trace footer")
        elif footer.get("tactic_count") != expected_count:
            errors.append("trace tactic count")
        transitions = replay.trace[:-1]
        traced_commands = tuple(
            record.get("tactic") if type(record) is dict else None
            for record in transitions
        )
        if traced_commands != expected_commands:
            errors.append("executed commands")

    # The immutable tuple passed to ``run_proof`` is itself the command
    # authority.  Bind it into both identifiers and the published digest so a
    # result from another route cannot be substituted merely because it has the
    # same node count.
    digest = _commands_sha256(expected_commands)
    if digest[:24] not in expected_session_id:
        errors.append("command/session binding")

    if errors:
        raise HydraReplayError(
            "fresh traced replay disagreed with the search claim: "
            + ", ".join(errors)
        )


def run_hydra(
    theorem: str,
    policy: HydraPortfolioPolicy,
    *,
    capabilities: SurfaceCapabilities,
    classical: bool = False,
    limits: SearchLimits = SearchLimits(),
    label: str = "hydra",
) -> HydraRunResult:
    """Run bounded search and fresh traced replay under one exact authority."""

    if type(capabilities) is not SurfaceCapabilities:
        raise TypeError("capabilities must be an exact SurfaceCapabilities value")
    if type(classical) is not bool:
        raise TypeError("classical must be a Boolean")
    if type(limits) is not SearchLimits:
        raise TypeError("limits must be an exact SearchLimits value")
    if not isinstance(policy, HydraPortfolioPolicy):
        raise TypeError(
            "policy must implement the complete HydraPortfolioPolicy contract"
        )
    if type(label) is not str or not label or label != label.strip():
        raise ValueError("label must be non-empty text with no outer whitespace")
    if label.splitlines() != [label]:
        raise ValueError("label must fit on one line")

    canonical = _canonical_theorem(theorem)
    environment = policy_environment(capabilities, classical=classical)
    declared_environment = _declared_policy_environment(policy)
    if declared_environment is None:
        raise ValueError("Hydra policy must declare policy_environment")
    if declared_environment != environment:
        raise ValueError("policy environment does not match the runner authority")

    name = _policy_name(policy)
    identity = _policy_identity(policy, name)
    total_quota = getattr(policy, "total_quota", None)
    total_quota = total_quota() if callable(total_quota) else total_quota
    if total_quota is None:
        raise ValueError("Hydra policy must declare total_quota")
    if type(total_quota) is not int or total_quota < 1:
        raise ValueError("policy total_quota must be a positive integer")
    if total_quota != limits.candidates_per_state:
        raise ValueError("search candidates_per_state must equal policy total_quota")

    records_before = _policy_records(policy)
    if records_before:
        raise ValueError("Hydra policy cannot be reused with non-empty records")
    result = kernel_guided_search(
        theorem,
        policy,
        capabilities=capabilities,
        classical=classical,
        limits=limits,
    )
    if type(result) is not SearchResult:
        raise HydraRunnerError("kernel-guided search returned a malformed result")
    if result.theorem != canonical:
        raise HydraRunnerError("kernel-guided search changed the original theorem")

    records_after = _policy_records(policy)
    if records_after[: len(records_before)] != records_before:
        raise HydraRunnerError("policy proposal records changed an existing prefix")
    new_records = tuple(
        _record_dict(record)
        for record in records_after[len(records_before) :]
    )
    if _policy_name(policy) != name or _policy_identity(policy, name) != identity:
        raise HydraRunnerError("policy evaluation identity changed during search")
    if _declared_policy_environment(policy) != environment:
        raise HydraRunnerError("policy environment changed during search")
    current_quota = getattr(policy, "total_quota", None)
    current_quota = current_quota() if callable(current_quota) else current_quota
    if current_quota != total_quota:
        raise HydraRunnerError("policy total_quota changed during search")

    reasons = list(_degradation_reasons(new_records, result))
    heads = getattr(policy, "heads", None)
    if type(heads) is tuple and heads:
        expected_records = result.model_calls * len(heads)
        if len(new_records) != expected_records:
            reasons.append(
                "proposal-ledger-count:"
                f"expected-{expected_records}:observed-{len(new_records)}"
            )
    else:
        reasons.append("proposal-ledger-head-schema-unavailable")
    degradation_reasons = tuple(dict.fromkeys(reasons))
    degraded = bool(degradation_reasons)
    # This runner implements the deliberately narrow surface-macro-v0
    # bootstrap.  Clean execution is useful evidence about plumbing, but it is
    # not sufficient evidence for a Qwen/Codex or matched-compute capability
    # claim.  A later protocol must replace this fixed reason only after it
    # validates versioned provider attestations and retains raw calls/resources.
    comparison_ineligibility_reasons = (SURFACE_MACRO_V0_INELIGIBILITY,)

    if result.status != "proof":
        if result.commands or result.certificate_nodes is not None:
            raise HydraRunnerError("unsuccessful search returned proof authority")
        return HydraRunResult(
            label,
            result.status,
            canonical,
            name,
            identity,
            environment,
            _limits_dict(limits),
            result,
            None,
            None,
            new_records,
            degraded,
            False,
            comparison_ineligibility_reasons,
            degradation_reasons,
        )

    commands = result.commands
    if type(commands) is not tuple or not commands:
        raise HydraRunnerError("proved search returned no exact command tuple")
    if not all(
        type(command) is str
        and bool(command)
        and command == command.strip()
        and command.splitlines() == [command]
        for command in commands
    ):
        raise HydraRunnerError("proved search returned malformed commands")
    nodes = result.certificate_nodes
    if type(nodes) is not int or nodes < 1:
        raise HydraRunnerError("proved search returned a malformed certificate size")

    command_digest = _commands_sha256(commands)
    replay_binding = hashlib.sha256(
        json.dumps(
            [
                HYDRA_RUNNER_VERSION,
                label,
                canonical,
                command_digest,
                environment["environment_sha256"],
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    request_id = f"hydra-replay-{replay_binding[:24]}"
    # Include the command digest itself, rather than only the aggregate replay
    # digest, so the validation above can audit the binding without a private
    # dependency on peano_lab.batch._stable_session_id.
    session_id = f"peano-hydra-{command_digest[:24]}"
    replay = run_proof(
        theorem,
        commands,
        request_id=request_id,
        classical=classical,
        on_error="stop",
        capabilities=capabilities,
        session_id=session_id,
    )
    _validate_replay(
        expected_theorem=canonical,
        expected_commands=commands,
        expected_nodes=nodes,
        expected_request_id=request_id,
        expected_session_id=session_id,
        expected_environment=environment,
        classical=classical,
        replay=replay,
    )
    return HydraRunResult(
        label,
        "proof",
        canonical,
        name,
        identity,
        environment,
        _limits_dict(limits),
        result,
        replay,
        command_digest,
        new_records,
        degraded,
        False,
        comparison_ineligibility_reasons,
        degradation_reasons,
    )


__all__ = [
    "HYDRA_RUNNER_VERSION",
    "HydraReplayError",
    "HydraRunResult",
    "HydraRunnerError",
    "SURFACE_MACRO_V0_INELIGIBILITY",
    "policy_environment",
    "run_hydra",
]
