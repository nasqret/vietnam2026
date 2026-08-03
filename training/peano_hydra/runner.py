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

from dataclasses import dataclass, field
import hashlib
import json
from typing import Mapping

from peano_lab.batch import BatchResult, capability_sha256, run_proof
from peano_lab.ui.prove import MAX_INPUT, SurfaceCapabilities, oversized_numeral
from training.peano_hydra.policy import (
    HYDRA_POLICY_VERSION,
    HydraPortfolioPolicy,
    ProposalRecord,
)
from training.peano_hydra.profile import (
    canonical_profile_theorem,
    evidence_kind as profile_evidence_kind,
    semantic_profile_sha256 as registered_semantic_profile_sha256,
)
from training.peano_policy.search import (
    SearchDiagnostic,
    SearchLimits,
    SearchResult,
    SearchStatus,
    search as kernel_guided_search,
)


HYDRA_RUNNER_VERSION = 2
MAX_IDENTITY_JSON_BYTES = 1_000_000
_ENVIRONMENT_FIELDS = frozenset(
    {
        "classical",
        "surface",
        "environment_sha256",
        "semantic_profile_sha256",
        "capabilities",
    }
)
_CAPABILITY_FIELDS = frozenset(
    {"label", "allowed_commands", "allowed_theorems"}
)
_LIMIT_FIELDS = frozenset(
    {
        "max_depth",
        "beam_width",
        "candidates_per_state",
        "max_model_calls",
        "max_states",
    }
)
_POLICY_IDENTITY_FIELDS = frozenset(
    {
        "name",
        "kind",
        "v",
        "semantic_profile_sha256",
        "merge",
        "quota_reallocation",
        "heads",
        "environment",
    }
)
_HEAD_IDENTITY_FIELDS = frozenset(
    {
        "name",
        "role",
        "quota",
        "gating",
        "semantic_profile_sha256",
        "identity_sha256",
        "policy",
    }
)
_PROPOSAL_FIELDS = frozenset(
    {
        "portfolio_call",
        "head",
        "role",
        "head_identity_sha256",
        "semantic_profile_sha256",
        "goals",
        "state_sha256",
        "quota",
        "requested",
        "outcome",
        "candidates",
        "accepted_candidates",
        "suppressed_duplicates",
        "response_sha256",
        "error_type",
        "error",
    }
)
_RUN_BINDING_UNSET = object()
SURFACE_MACRO_V0_INELIGIBILITY = (
    "surface-macro-v0 is pre-H0.3 plumbing without a registered provider "
    "attestation and raw-call evidence schema"
)
SURFACE_MACRO_V0_EVIDENCE_INELIGIBILITY = (
    "surface-macro-v0 is not a peano-hydra-result-v1 evidence bundle: it "
    "does not retain the certificate hash/depth, kernel identity, or closed "
    "run/replay evidence hashes required by the semantic profile"
)
SURFACE_MACRO_V0_UNKNOWN_EVIDENCE_INELIGIBILITY = (
    "surface-macro-v0 is not a peano-hydra-result-v1 unknown-evidence bundle: "
    "it does not retain the required unknown reason or closed original-theorem "
    "and run-evidence hashes"
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


def _registered_profile(value: object) -> str:
    expected = registered_semantic_profile_sha256()
    if type(value) is not str or value != expected:
        raise ValueError(
            "semantic_profile_sha256 must equal the registered Hydra profile"
        )
    return value


def _name_allowlist(label: str, value: object) -> frozenset[str] | None:
    if value is None:
        return None
    if type(value) is not list or not all(
        type(item) is str and item for item in value
    ):
        raise ValueError(f"{label} must be null or an array of non-empty names")
    if value != sorted(value) or len(value) != len(set(value)):
        raise ValueError(f"{label} must be sorted and unique")
    return frozenset(value)


def _capabilities_from_environment(
    value: object,
    *,
    expected_profile: str,
) -> tuple[dict[str, object], SurfaceCapabilities]:
    environment = _canonical_json_object(value, field="run environment")
    if set(environment) != _ENVIRONMENT_FIELDS:
        raise ValueError("run environment has non-canonical fields")
    if environment.get("semantic_profile_sha256") != expected_profile:
        raise ValueError("run environment has a different semantic profile")
    if environment.get("classical") is not False:
        raise ValueError("run environment is not intuitionistic")
    capabilities = environment.get("capabilities")
    if type(capabilities) is not dict or set(capabilities) != _CAPABILITY_FIELDS:
        raise ValueError("run environment capabilities are malformed")
    surface = environment.get("surface")
    if type(surface) is not str or not surface or capabilities.get("label") != surface:
        raise ValueError("run environment surface identity is malformed")
    authority = SurfaceCapabilities(
        label=surface,
        allowed_commands=_name_allowlist(
            "run environment allowed_commands",
            capabilities.get("allowed_commands"),
        ),
        allowed_theorems=_name_allowlist(
            "run environment allowed_theorems",
            capabilities.get("allowed_theorems"),
        ),
    )
    digest = environment.get("environment_sha256")
    if type(digest) is not str or digest != capability_sha256(authority):
        raise ValueError("run environment capability digest is malformed")
    return environment, authority


def _json_sha256(value: object) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"value is not strict JSON: {exc}") from None
    return hashlib.sha256(encoded).hexdigest()


def _limits_from_record(value: object) -> tuple[dict[str, object], SearchLimits]:
    limits = _canonical_json_object(value, field="run limits")
    if set(limits) != _LIMIT_FIELDS:
        raise ValueError("run limits have non-canonical fields")
    try:
        authority = SearchLimits(
            max_depth=limits["max_depth"],
            beam_width=limits["beam_width"],
            candidates_per_state=limits["candidates_per_state"],
            max_model_calls=limits["max_model_calls"],
            max_states=limits["max_states"],
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"run limits are malformed: {exc}") from None
    if limits != _limits_dict(authority):  # rejects bool-as-int and subclasses
        raise ValueError("run limits do not round-trip through SearchLimits")
    return limits, authority


def _validate_policy_identity_record(
    value: object,
    *,
    expected_name: str,
    expected_environment: dict[str, object],
    expected_profile: str,
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    identity = _canonical_json_object(value, field="run policy_identity")
    if set(identity) != _POLICY_IDENTITY_FIELDS:
        raise ValueError("run policy_identity has non-canonical fields")
    if identity.get("name") != expected_name:
        raise ValueError("run policy and policy_identity names disagree")
    if (
        identity.get("kind") != "peano-hydra-candidate-policy-v2"
        or identity.get("v") != HYDRA_POLICY_VERSION
        or identity.get("merge") != "declared-head-order-stable-first-wins-v1"
        or identity.get("quota_reallocation") is not False
    ):
        raise ValueError("run policy_identity has an unsupported portfolio schema")
    if identity.get("semantic_profile_sha256") != expected_profile:
        raise ValueError("run policy has a different semantic profile")
    if identity.get("environment") != expected_environment:
        raise ValueError("run policy identity and environment disagree")

    raw_heads = identity.get("heads")
    if type(raw_heads) is not list or not raw_heads:
        raise ValueError("run policy_identity needs a non-empty head list")
    heads: list[dict[str, object]] = []
    names: set[str] = set()
    for raw in raw_heads:
        head = _canonical_json_object(raw, field="run policy head")
        if set(head) != _HEAD_IDENTITY_FIELDS:
            raise ValueError("run policy head has non-canonical fields")
        name = head.get("name")
        if type(name) is not str or not name or name != name.strip() or "\n" in name:
            raise ValueError("run policy head name is malformed")
        if name in names:
            raise ValueError("run policy head names must be unique")
        names.add(name)
        if head.get("role") not in {"macro", "symbolic", "control"}:
            raise ValueError("run policy head role is malformed")
        quota = head.get("quota")
        if type(quota) is not int or quota < 1:
            raise ValueError("run policy head quota is malformed")
        if head.get("semantic_profile_sha256") != expected_profile:
            raise ValueError("run policy head has a different semantic profile")
        gating = head.get("gating")
        if type(gating) is not dict or set(gating) != {"state_sha256_allowlist"}:
            raise ValueError("run policy head gate is malformed")
        allowlist = gating["state_sha256_allowlist"]
        if allowlist is not None and (
            type(allowlist) is not list
            or allowlist != sorted(allowlist)
            or len(allowlist) != len(set(allowlist))
            or not all(
                type(item) is str
                and len(item) == 64
                and all(character in "0123456789abcdef" for character in item)
                for item in allowlist
            )
        ):
            raise ValueError("run policy head gate allowlist is malformed")
        provider = head.get("policy")
        if type(provider) is not dict or not provider:
            raise ValueError("run policy head provider identity is malformed")
        if provider.get("semantic_profile_sha256") != expected_profile:
            raise ValueError("run policy provider has a different semantic profile")
        expected_head_digest = _json_sha256(
            {
                "v": HYDRA_POLICY_VERSION,
                "semantic_profile_sha256": expected_profile,
                "name": name,
                "role": head["role"],
                "quota": quota,
                "gating": gating,
                "environment": expected_environment,
                "policy": provider,
            }
        )
        if head.get("identity_sha256") != expected_head_digest:
            raise ValueError("run policy head identity digest is malformed")
        heads.append(head)
    return identity, tuple(heads)


def _validate_proposal_records(
    values: object,
    *,
    heads: tuple[dict[str, object], ...],
    expected_profile: str,
    model_calls: int,
) -> tuple[dict[str, object], ...]:
    if type(values) is not tuple:
        raise TypeError("run proposal_records must be an exact tuple")
    head_by_name = {head["name"]: head for head in heads}
    head_rank = {head["name"]: index for index, head in enumerate(heads)}
    detached_records: list[dict[str, object]] = []
    last_key = (0, -1)
    call_state: dict[int, tuple[tuple[str, ...], str]] = {}
    seen_by_call: dict[int, set[str]] = {}
    seen_head_calls: set[tuple[int, str]] = set()

    for value in values:
        record = _canonical_json_object(value, field="run proposal record")
        if set(record) != _PROPOSAL_FIELDS:
            raise ValueError("run proposal record has non-canonical fields")
        if record.get("semantic_profile_sha256") != expected_profile:
            raise ValueError("run proposal record has a different semantic profile")
        goals = record.get("goals")
        candidates = record.get("candidates")
        accepted = record.get("accepted_candidates")
        if type(goals) is not list or type(candidates) is not list or type(accepted) is not list:
            raise ValueError("run proposal record arrays are malformed")
        try:
            checked = ProposalRecord(
                portfolio_call=record["portfolio_call"],
                head=record["head"],
                role=record["role"],
                head_identity_sha256=record["head_identity_sha256"],
                semantic_profile_sha256=record["semantic_profile_sha256"],
                goals=tuple(goals),
                state_sha256=record["state_sha256"],
                quota=record["quota"],
                requested=record["requested"],
                outcome=record["outcome"],
                candidates=tuple(candidates),
                accepted_candidates=tuple(accepted),
                suppressed_duplicates=record["suppressed_duplicates"],
                response_sha256=record["response_sha256"],
                error_type=record["error_type"],
                error=record["error"],
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"run proposal record is malformed: {exc}") from None
        if checked.to_record() != record:
            raise ValueError("run proposal record failed its canonical round trip")

        call = checked.portfolio_call
        if call > model_calls:
            raise ValueError("run proposal record exceeds the search model-call count")
        head = head_by_name.get(checked.head)
        if head is None:
            raise ValueError("run proposal record names an undeclared policy head")
        if (
            checked.role != head["role"]
            or checked.quota != head["quota"]
            or checked.head_identity_sha256 != head["identity_sha256"]
        ):
            raise ValueError("run proposal record disagrees with its policy head")
        call_head = (call, checked.head)
        if call_head in seen_head_calls:
            raise ValueError("run proposal ledger repeats one head in one call")
        seen_head_calls.add(call_head)
        ordering_key = (call, head_rank[checked.head])
        if ordering_key <= last_key:
            raise ValueError("run proposal ledger is not in canonical call/head order")
        last_key = ordering_key
        state = (checked.goals, checked.state_sha256)
        if call in call_state and call_state[call] != state:
            raise ValueError("run proposal heads disagree on their complete state")
        call_state[call] = state

        if checked.outcome == "ok":
            if checked.response_sha256 != _json_sha256(list(checked.candidates)):
                raise ValueError("run proposal response digest is malformed")
            seen = seen_by_call.setdefault(call, set())
            expected_accepted: list[str] = []
            duplicates = 0
            for candidate in checked.candidates:
                if candidate in seen:
                    duplicates += 1
                else:
                    seen.add(candidate)
                    expected_accepted.append(candidate)
            if (
                checked.accepted_candidates != tuple(expected_accepted)
                or checked.suppressed_duplicates != duplicates
            ):
                raise ValueError("run proposal merge accounting is malformed")
        elif checked.outcome == "gated" and (
            checked.error_type is not None or checked.error is not None
        ):
            raise ValueError("a gated proposal cannot claim an error")
        detached_records.append(record)
    return tuple(detached_records)


def _validate_search_accounting(
    result: object,
    *,
    expected_theorem: str,
    limits: SearchLimits,
) -> SearchResult:
    if type(result) is not SearchResult:
        raise TypeError("run search must be an exact SearchResult")
    if result.status not in {"proof", "exhausted", "limit"}:
        raise ValueError("run search status is outside proof | exhausted | limit")
    result.__post_init__()
    if result.theorem != expected_theorem:
        raise ValueError("run search changed the original theorem")
    if type(result.commands) is not tuple or not all(
        type(command) is str
        and bool(command)
        and command == command.strip()
        and command.splitlines() == [command]
        for command in result.commands
    ):
        raise ValueError("run search commands are malformed")
    if type(result.diagnostics) is not tuple or not all(
        type(item) is SearchDiagnostic for item in result.diagnostics
    ):
        raise ValueError("run search diagnostics are malformed")
    for diagnostic in result.diagnostics:
        if (
            type(diagnostic.kind) is not str
            or not diagnostic.kind
            or diagnostic.kind != diagnostic.kind.strip()
            or diagnostic.kind.splitlines() != [diagnostic.kind]
            or type(diagnostic.depth) is not int
            or not 0 <= diagnostic.depth <= limits.max_depth
            or type(diagnostic.state_sha256) is not str
            or len(diagnostic.state_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in diagnostic.state_sha256
            )
            or type(diagnostic.message) is not str
            or not diagnostic.message
            or diagnostic.message.splitlines() != [diagnostic.message]
            or (
                diagnostic.command is not None
                and (
                    type(diagnostic.command) is not str
                    or not diagnostic.command
                    or diagnostic.command != diagnostic.command.strip()
                    or diagnostic.command.splitlines() != [diagnostic.command]
                )
            )
        ):
            raise ValueError("run search diagnostic fields are malformed")
    counters = (
        result.model_calls,
        result.states_expanded,
        result.states_discovered,
        result.candidates_executed,
        result.frontier_peak,
        result.depth_reached,
    )
    if not all(type(value) is int and value >= 0 for value in counters):
        raise ValueError("run search counters must be non-negative integers")
    if result.model_calls != result.states_expanded:
        raise ValueError("run search model-call and expansion counts disagree")
    if result.model_calls > limits.max_model_calls:
        raise ValueError("run search exceeds its model-call limit")
    if not 1 <= result.states_discovered <= limits.max_states:
        raise ValueError("run search state count is outside its limit")
    if result.states_expanded > result.states_discovered:
        raise ValueError("run search expanded more states than it discovered")
    if not 1 <= result.frontier_peak <= limits.beam_width:
        raise ValueError("run search frontier peak is outside its beam limit")
    if result.depth_reached > limits.max_depth:
        raise ValueError("run search depth exceeds its limit")
    if result.candidates_executed > (
        result.model_calls * limits.candidates_per_state
    ):
        raise ValueError("run search candidate count exceeds its declared quota")
    if result.status == "proof":
        if len(result.commands) != result.depth_reached:
            raise ValueError("run proof command count and reached depth disagree")
        if type(result.certificate_nodes) is not int or result.certificate_nodes < 1:
            raise ValueError("run proof has a malformed certificate size")
    return result


def policy_environment(
    capabilities: SurfaceCapabilities,
    *,
    semantic_profile_sha256: str,
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
    profile_digest = _registered_profile(semantic_profile_sha256)
    if classical:
        raise ValueError("the registered Hydra semantic profile is intuitionistic")
    return {
        "classical": classical,
        "surface": capabilities.label,
        "environment_sha256": capability_sha256(capabilities),
        "semantic_profile_sha256": profile_digest,
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
    policy: HydraPortfolioPolicy,
    name: str,
    expected_profile: str,
) -> dict[str, object]:
    declared = getattr(policy, "evaluation_identity", None)
    if declared is None:
        raise ValueError("Hydra policy must declare evaluation_identity")
    identity = declared() if callable(declared) else declared
    detached = _canonical_json_object(identity, field="policy evaluation_identity")
    if detached.get("name") != name:
        raise ValueError("policy evaluation_identity must contain its exact name")
    if detached.get("semantic_profile_sha256") != expected_profile:
        raise ValueError(
            "policy evaluation_identity has a different semantic profile"
        )
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


def _record_dict(record: object, expected_profile: str) -> dict[str, object]:
    convert = getattr(record, "to_dict", None)
    value = convert() if callable(convert) else record
    detached = _canonical_json_object(value, field="proposal record")
    if detached.get("semantic_profile_sha256") != expected_profile:
        raise ValueError("proposal record has a different semantic profile")
    return detached


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


def _replay_identity(
    *,
    label: str,
    theorem: str,
    command_digest: str,
    environment: Mapping[str, object],
    semantic_profile_sha256: str,
) -> tuple[str, str]:
    replay_binding = hashlib.sha256(
        json.dumps(
            [
                HYDRA_RUNNER_VERSION,
                label,
                theorem,
                command_digest,
                environment["environment_sha256"],
                semantic_profile_sha256,
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return (
        f"hydra-replay-{semantic_profile_sha256[:12]}-{replay_binding[:12]}",
        f"peano-hydra-{semantic_profile_sha256[:12]}-{command_digest[:24]}",
    )


@dataclass(frozen=True, slots=True)
class HydraRunResult:
    """One bounded search and, for a proof, its independent traced replay."""

    label: str
    status: SearchStatus
    theorem: str
    semantic_profile_sha256: str
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
    _publication_binding_sha256: object = field(
        default=_RUN_BINDING_UNSET,
        repr=False,
    )

    def _current_publication_binding_sha256(self) -> str:
        return _json_sha256(
            {
                "v": HYDRA_RUNNER_VERSION,
                "label": self.label,
                "status": self.status,
                "theorem": self.theorem,
                "semantic_profile_sha256": self.semantic_profile_sha256,
                "policy": self.policy,
                "policy_identity": self.policy_identity,
                "environment": self.environment,
                "limits": self.limits,
                "search": self.search.to_dict(),
                "replay": (
                    None
                    if self.replay is None
                    else self.replay.to_dict(include_trace=True)
                ),
                "commands_sha256": self.commands_sha256,
                "proposal_records": list(self.proposal_records),
                "degraded": self.degraded,
                "eligible_for_comparison": self.eligible_for_comparison,
                "comparison_ineligibility_reasons": list(
                    self.comparison_ineligibility_reasons
                ),
                "degradation_reasons": list(self.degradation_reasons),
            }
        )

    def __post_init__(self) -> None:
        for label, value in (("run label", self.label), ("run policy", self.policy)):
            if (
                type(value) is not str
                or not value
                or value != value.strip()
                or value.splitlines() != [value]
            ):
                raise ValueError(f"{label} must be one non-empty canonical line")
        profile_digest = _registered_profile(self.semantic_profile_sha256)
        environment, _ = _capabilities_from_environment(
            self.environment,
            expected_profile=profile_digest,
        )
        limits, limit_authority = _limits_from_record(self.limits)
        if canonical_profile_theorem(self.theorem) != self.theorem:
            raise ValueError("run theorem is not in canonical profile form")
        search = _validate_search_accounting(
            self.search,
            expected_theorem=self.theorem,
            limits=limit_authority,
        )
        if self.status != search.status:
            raise ValueError("runner status must equal the underlying search status")
        policy_identity, heads = _validate_policy_identity_record(
            self.policy_identity,
            expected_name=self.policy,
            expected_environment=environment,
            expected_profile=profile_digest,
        )
        if sum(head["quota"] for head in heads) != limit_authority.candidates_per_state:
            raise ValueError("run policy head quotas disagree with its search limit")
        proposal_records = _validate_proposal_records(
            self.proposal_records,
            heads=heads,
            expected_profile=profile_digest,
            model_calls=search.model_calls,
        )
        object.__setattr__(self, "environment", environment)
        object.__setattr__(self, "limits", limits)
        object.__setattr__(self, "policy_identity", policy_identity)
        object.__setattr__(self, "proposal_records", proposal_records)
        if self.status == "proof":
            if type(self.replay) is not BatchResult or self.commands_sha256 is None:
                raise ValueError("a proof result needs a binding traced replay")
            expected_command_digest = _commands_sha256(search.commands)
            if self.commands_sha256 != expected_command_digest:
                raise ValueError("run command digest does not match its commands")
            nodes = search.certificate_nodes
            if type(nodes) is not int or nodes < 1:
                raise ValueError("run proof has a malformed certificate size")
            request_id, session_id = _replay_identity(
                label=self.label,
                theorem=self.theorem,
                command_digest=expected_command_digest,
                environment=environment,
                semantic_profile_sha256=profile_digest,
            )
            _validate_replay(
                expected_theorem=self.theorem,
                expected_commands=search.commands,
                expected_nodes=nodes,
                expected_request_id=request_id,
                expected_session_id=session_id,
                expected_environment=environment,
                expected_semantic_profile_sha256=profile_digest,
                classical=False,
                replay=self.replay,
            )
        elif self.replay is not None or self.commands_sha256 is not None:
            raise ValueError("an unsuccessful search cannot publish replay proof data")
        if (
            type(self.degraded) is not bool
            or type(self.eligible_for_comparison) is not bool
        ):
            raise TypeError("comparison eligibility fields must be Booleans")
        expected_degradation = list(_degradation_reasons(proposal_records, search))
        expected_records = search.model_calls * len(heads)
        if len(proposal_records) != expected_records:
            expected_degradation.append(
                "proposal-ledger-count:"
                f"expected-{expected_records}:observed-{len(proposal_records)}"
            )
        expected_degradation_tuple = tuple(dict.fromkeys(expected_degradation))
        if (
            type(self.degradation_reasons) is not tuple
            or self.degradation_reasons != expected_degradation_tuple
            or self.degraded is not bool(expected_degradation_tuple)
        ):
            raise ValueError("run degradation fields do not match retained evidence")
        if (
            self.eligible_for_comparison is not False
            or self.comparison_ineligibility_reasons
            != (SURFACE_MACRO_V0_INELIGIBILITY,)
        ):
            raise ValueError(
                "surface-macro-v0 must remain explicitly comparison-ineligible"
            )
        current_binding = self._current_publication_binding_sha256()
        retained_binding = self._publication_binding_sha256
        if retained_binding is _RUN_BINDING_UNSET:
            object.__setattr__(
                self,
                "_publication_binding_sha256",
                current_binding,
            )
        elif type(retained_binding) is not str or retained_binding != current_binding:
            raise HydraRunnerError(
                "run publication fields changed after their original binding"
            )

    @property
    def proved(self) -> bool:
        return self.status == "proof"

    @property
    def evidence_kind(self) -> str:
        """Map search completion to the profile's claimable evidence kinds."""

        return profile_evidence_kind(
            proved=self.proved,
            kernel_checked=(
                self.replay is not None and self.replay.kernel_checked is True
            ),
        )

    @property
    def commands(self) -> tuple[str, ...]:
        return self.search.commands

    def to_dict(self, *, include_trace: bool = False) -> dict[str, object]:
        # Frozen dataclasses can still contain mutable JSON objects.  Recheck
        # and detach them at the publication boundary so post-construction
        # relabeling cannot enter an evidence artifact.
        self.__post_init__()
        if self.proved:
            assert self.replay is not None  # established by __post_init__
            assert self.commands_sha256 is not None
            assert self.search.certificate_nodes is not None
            environment, authority = _capabilities_from_environment(
                self.environment,
                expected_profile=self.semantic_profile_sha256,
            )
            request_id, session_id = _replay_identity(
                label=self.label,
                theorem=self.theorem,
                command_digest=self.commands_sha256,
                environment=environment,
                semantic_profile_sha256=self.semantic_profile_sha256,
            )
            fresh = run_proof(
                self.theorem,
                self.commands,
                request_id=request_id,
                classical=False,
                on_error="stop",
                capabilities=authority,
                session_id=session_id,
            )
            _validate_replay(
                expected_theorem=self.theorem,
                expected_commands=self.commands,
                expected_nodes=self.search.certificate_nodes,
                expected_request_id=request_id,
                expected_session_id=session_id,
                expected_environment=environment,
                expected_semantic_profile_sha256=self.semantic_profile_sha256,
                classical=False,
                replay=fresh,
            )
            if fresh.to_dict(include_trace=True) != self.replay.to_dict(
                include_trace=True
            ):
                raise HydraReplayError(
                    "publication replay differs from the retained Hydra replay"
                )
        payload = {
            "v": HYDRA_RUNNER_VERSION,
            "label": self.label,
            "status": self.status,
            "proved": self.proved,
            "evidence_kind": self.evidence_kind,
            "profile_evidence_schema": {
                "format": "peano-hydra-result",
                "v": 1,
                "schema_status": "required-field-draft",
                "claim_kind": self.evidence_kind,
                "conformant": False,
                "ineligibility_reason": (
                    SURFACE_MACRO_V0_EVIDENCE_INELIGIBILITY
                    if self.proved
                    else SURFACE_MACRO_V0_UNKNOWN_EVIDENCE_INELIGIBILITY
                ),
            },
            "theorem": self.theorem,
            "semantic_profile_sha256": self.semantic_profile_sha256,
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
        try:
            detached = json.loads(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise HydraRunnerError(
                f"run publication record is not strict JSON: {exc}"
            ) from None
        if type(detached) is not dict:  # pragma: no cover - literal invariant
            raise HydraRunnerError("run publication record is not an object")
        return detached


def _validate_replay(
    *,
    expected_theorem: str,
    expected_commands: tuple[str, ...],
    expected_nodes: int,
    expected_request_id: str,
    expected_session_id: str,
    expected_environment: Mapping[str, object],
    expected_semantic_profile_sha256: str,
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
    if expected_semantic_profile_sha256[:12] not in expected_request_id:
        errors.append("profile/request binding")
    if expected_semantic_profile_sha256[:12] not in expected_session_id:
        errors.append("profile/session binding")

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
    semantic_profile_sha256: str,
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

    profile_digest = _registered_profile(semantic_profile_sha256)
    if type(theorem) is not str:
        raise TypeError("theorem must be text")
    if len(theorem) > MAX_INPUT:
        raise ValueError(f"theorem exceeds {MAX_INPUT} characters")
    dangerous_numeral = oversized_numeral(theorem)
    if dangerous_numeral is not None:
        raise ValueError(
            f"theorem contains resource-dangerous numeral {dangerous_numeral}"
        )
    canonical = canonical_profile_theorem(theorem)
    environment = policy_environment(
        capabilities,
        semantic_profile_sha256=profile_digest,
        classical=classical,
    )
    declared_environment = _declared_policy_environment(policy)
    if declared_environment is None:
        raise ValueError("Hydra policy must declare policy_environment")
    if declared_environment != environment:
        raise ValueError("policy environment does not match the runner authority")

    name = _policy_name(policy)
    identity = _policy_identity(policy, name, profile_digest)
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
        _record_dict(record, profile_digest)
        for record in records_after[len(records_before) :]
    )
    if (
        _policy_name(policy) != name
        or _policy_identity(policy, name, profile_digest) != identity
    ):
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
            label=label,
            status=result.status,
            theorem=canonical,
            semantic_profile_sha256=profile_digest,
            policy=name,
            policy_identity=identity,
            environment=environment,
            limits=_limits_dict(limits),
            search=result,
            replay=None,
            commands_sha256=None,
            proposal_records=new_records,
            degraded=degraded,
            eligible_for_comparison=False,
            comparison_ineligibility_reasons=comparison_ineligibility_reasons,
            degradation_reasons=degradation_reasons,
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
    request_id, session_id = _replay_identity(
        label=label,
        theorem=canonical,
        command_digest=command_digest,
        environment=environment,
        semantic_profile_sha256=profile_digest,
    )
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
        expected_semantic_profile_sha256=profile_digest,
        classical=classical,
        replay=replay,
    )
    return HydraRunResult(
        label=label,
        status="proof",
        theorem=canonical,
        semantic_profile_sha256=profile_digest,
        policy=name,
        policy_identity=identity,
        environment=environment,
        limits=_limits_dict(limits),
        search=result,
        replay=replay,
        commands_sha256=command_digest,
        proposal_records=new_records,
        degraded=degraded,
        eligible_for_comparison=False,
        comparison_ineligibility_reasons=comparison_ineligibility_reasons,
        degradation_reasons=degradation_reasons,
    )


__all__ = [
    "HYDRA_RUNNER_VERSION",
    "HydraReplayError",
    "HydraRunResult",
    "HydraRunnerError",
    "SURFACE_MACRO_V0_EVIDENCE_INELIGIBILITY",
    "SURFACE_MACRO_V0_INELIGIBILITY",
    "SURFACE_MACRO_V0_UNKNOWN_EVIDENCE_INELIGIBILITY",
    "policy_environment",
    "run_hydra",
]
