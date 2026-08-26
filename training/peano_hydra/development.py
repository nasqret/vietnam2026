"""Bounded, independently checked Hydra optimization and candidate discovery.

Policies, recorded teachers, proposed theorem statements, and search results
remain untrusted.  The current frozen epoch supplies the only checked-theorem
authority, and :func:`run_hydra` independently replays every successful route.
Route comparisons describe the best *observed* checked proof, never global
optimality.  A discovered proof remains an unadmitted development candidate.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import json
import re

from peano_lab.batch import BatchResult, run_proof
from peano_lab.kernel.formulas import ParseError, parse_formula_with_names, pretty_formula
from peano_lab.ui.prove import SurfaceCapabilities
from training.peano_hydra.epoch import HydraEpoch
from training.peano_hydra.policy import (
    HydraCandidatePolicy,
    HydraPortfolioPolicy,
    PolicyHead,
    ScriptCandidatePolicy,
)
from training.peano_hydra.runner import HydraRunResult, policy_environment, run_hydra
from training.peano_policy.search import SearchLimits


DEVELOPMENT_SCHEMA = "peano-hydra-proof-development-v1"
MAX_ROUTE_COUNT = 16
MAX_TOTAL_MODEL_CALLS = 16_384
MAX_TOTAL_STATES = 65_536
MAX_TOTAL_CANDIDATES = 262_144
MAX_COMMAND_COUNT = 512
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,127}\Z")
_METAVARIABLE = re.compile(r"\?t[0-9]+\b")


class HydraDevelopmentError(ValueError):
    """An optimization or discovery crossed its reviewed evidence boundary."""


def _normalize_metavariables(goals: tuple[str, ...]) -> tuple[str, ...]:
    """Rename engine metavariables by their first visible goal occurrence."""

    names: dict[str, str] = {}

    def rename(match: re.Match[str]) -> str:
        original = match.group(0)
        if original not in names:
            names[original] = f"?t{len(names) + 1}"
        return names[original]

    return tuple(_METAVARIABLE.sub(rename, goal) for goal in goals)


class AlphaNormalizedScriptPolicy:
    """Retain exact-state priority while allowing safe metavariable α-renaming.

    The proof engine may compact unresolved ``?tN`` identifiers when a sibling
    subgoal disappears.  That cosmetic difference previously prevented a
    recorded checked route from proposing its final tactic.  Suggestions stay
    untrusted and every accepted action still crosses the unchanged kernel.
    """

    __slots__ = ("name", "_source", "_normalized")

    def __init__(self, source: ScriptCandidatePolicy) -> None:
        if type(source) is not ScriptCandidatePolicy:
            raise TypeError("normalized proof routing requires an exact checked script policy")
        self.name = f"{source.name}-metavar-alpha"
        self._source = source
        mapping: dict[tuple[str, ...], list[str]] = {}
        for record in source.recorded_states:
            normalized = _normalize_metavariables(record.goals)
            candidates = mapping.setdefault(normalized, [])
            for candidate in record.candidates:
                if candidate not in candidates:
                    candidates.append(candidate)
        self._normalized = {
            goals: tuple(candidates)
            for goals, candidates in mapping.items()
        }

    @property
    def policy_environment(self) -> dict[str, object]:
        return self._source.policy_environment

    @property
    def evaluation_identity(self) -> dict[str, object]:
        rows = [
            {"goals": list(goals), "candidates": list(candidates)}
            for goals, candidates in self._normalized.items()
        ]
        payload = json.dumps(
            rows,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return {
            "name": self.name,
            "kind": "peano-hydra-metavariable-alpha-script-policy-v1",
            "normalization": "engine-metavariable-first-visible-occurrence-v1",
            "normalized_state_count": len(rows),
            "normalized_state_sha256": hashlib.sha256(payload).hexdigest(),
            "source": self._source.evaluation_identity,
        }

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
    ) -> tuple[str, ...]:
        exact = self._source.propose(
            goals_before,
            max_candidates=max_candidates,
        )
        if exact:
            return exact
        return self._normalized.get(
            _normalize_metavariables(goals_before),
            (),
        )[:max_candidates]


def _name(value: object, *, field: str) -> str:
    if type(value) is not str or _NAME.fullmatch(value) is None:
        raise HydraDevelopmentError(f"{field} must be one safe bounded identifier")
    return value


def _canonical_theorem(source: object) -> str:
    if (
        type(source) is not str
        or not source
        or source != source.strip()
        or source.splitlines() != [source]
    ):
        raise HydraDevelopmentError("theorem must be one complete line without outer whitespace")
    try:
        formula, free_names = parse_formula_with_names(source)
    except (ParseError, RecursionError, TypeError, ValueError) as error:
        raise HydraDevelopmentError(f"theorem has an invalid formula: {error}") from None
    if free_names:
        raise HydraDevelopmentError("theorem must be closed with no free variable names")
    return pretty_formula(formula, list(free_names))


def _epoch_capabilities(epoch: HydraEpoch, capabilities: SurfaceCapabilities) -> None:
    if type(epoch) is not HydraEpoch:
        raise TypeError("epoch must be one authenticated HydraEpoch")
    if type(capabilities) is not SurfaceCapabilities:
        raise TypeError("capabilities must be one exact SurfaceCapabilities value")
    if capabilities.label != epoch.surface_label:
        raise HydraDevelopmentError("execution authority does not match the exact frozen Alpha epoch")
    if capabilities.allowed_commands is None or capabilities.allowed_theorems is None:
        raise HydraDevelopmentError("Hydra execution requires finite command and theorem allowlists")
    known = frozenset(theorem.name for theorem in epoch.theorems)
    if not capabilities.allowed_theorems <= known:
        raise HydraDevelopmentError("execution theorem authority escapes the frozen Alpha DAG")


def _verified_result(
    result: HydraRunResult,
    *,
    theorem: str,
    capabilities: SurfaceCapabilities,
) -> None:
    if type(result) is not HydraRunResult or not result.proved:
        raise HydraDevelopmentError("the candidate has no independently checked proof")
    replay = result.replay
    if (
        replay is None
        or replay.kernel_checked is not True
        or replay.status != "proved"
        or replay.theorem != theorem
        or result.theorem != theorem
        or replay.goals
        or replay.proof_nodes != result.search.certificate_nodes
        or replay.tactics_applied != len(result.commands)
        or replay.failed_tactics != 0
        or type(replay.trace) is not tuple
        or len(replay.trace) != len(result.commands) + 1
        or type(replay.trace[-1]) is not dict
        or replay.trace[-1].get("qed") is not True
        or replay.trace[-1].get("theorem") != theorem
        or result.environment != policy_environment(capabilities)
    ):
        raise HydraDevelopmentError("the candidate lost its exact original-goal kernel replay")
    if tuple(row.get("tactic") for row in replay.trace[:-1]) != result.commands:
        raise HydraDevelopmentError("the checked replay trace changed its complete tactic route")


@dataclass(frozen=True, slots=True)
class DevelopmentLimits:
    """Whole-run reservations; route limits cannot silently multiply them."""

    max_routes: int = 8
    max_total_model_calls: int = 2_048
    max_total_states: int = 8_192
    max_total_candidates: int = 32_768

    def __post_init__(self) -> None:
        boundaries = {
            "max_routes": MAX_ROUTE_COUNT,
            "max_total_model_calls": MAX_TOTAL_MODEL_CALLS,
            "max_total_states": MAX_TOTAL_STATES,
            "max_total_candidates": MAX_TOTAL_CANDIDATES,
        }
        for field, maximum in boundaries.items():
            value = getattr(self, field)
            if type(value) is not int or not 1 <= value <= maximum:
                raise HydraDevelopmentError(f"{field} must lie between 1 and {maximum}")

    def to_dict(self) -> dict[str, int]:
        return {
            "max_routes": self.max_routes,
            "max_total_model_calls": self.max_total_model_calls,
            "max_total_states": self.max_total_states,
            "max_total_candidates": self.max_total_candidates,
        }


@dataclass(frozen=True, slots=True)
class OptimizationRoute:
    """One named, fresh, bounded policy lane for the original theorem."""

    name: str
    policy_factory: Callable[[], HydraPortfolioPolicy]
    limits: SearchLimits

    def __post_init__(self) -> None:
        _name(self.name, field="optimization route")
        if not callable(self.policy_factory):
            raise TypeError("optimization route requires a fresh callable policy factory")
        if type(self.limits) is not SearchLimits:
            raise TypeError("optimization route requires exact bounded SearchLimits")


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    """The best observed verified route; no global-optimality assertion."""

    epoch_sha256: str
    theorem_name: str
    theorem: str
    routes: tuple[tuple[str, HydraRunResult], ...]
    baseline_name: str
    baseline: HydraRunResult
    winner_name: str
    winner: HydraRunResult
    limits: DevelopmentLimits

    @property
    def tactic_decisions_saved(self) -> int:
        return len(self.baseline.commands) - len(self.winner.commands)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": DEVELOPMENT_SCHEMA,
            "track": "proof_optimization",
            "epoch_sha256": self.epoch_sha256,
            "theorem_name": self.theorem_name,
            "theorem": self.theorem,
            "route_count": len(self.routes),
            "checked_route_count": sum(result.proved for _, result in self.routes),
            "baseline": {
                "name": self.baseline_name,
                "tactic_decisions": len(self.baseline.commands),
                "proof_nodes": self.baseline.search.certificate_nodes,
                "commands_sha256": self.baseline.commands_sha256,
            },
            "winner": {
                "name": self.winner_name,
                "tactic_decisions": len(self.winner.commands),
                "proof_nodes": self.winner.search.certificate_nodes,
                "commands_sha256": self.winner.commands_sha256,
            },
            "tactic_decisions_saved": self.tactic_decisions_saved,
            "limits": self.limits.to_dict(),
            "ranking": "tactic decisions, proof nodes, expanded states, exact command tuple",
            "global_optimality_claim": False,
            "research_claim_eligible": False,
        }


@dataclass(frozen=True, slots=True)
class DiscoveryProposal:
    """One closed candidate and its exact frozen prerequisite authority."""

    name: str
    theorem: str
    dependencies: tuple[str, ...]
    policy_factory: Callable[[], HydraPortfolioPolicy]
    limits: SearchLimits
    source: str = "untrusted_candidate_policy"

    def __post_init__(self) -> None:
        _name(self.name, field="discovery theorem name")
        _canonical_theorem(self.theorem)
        if type(self.dependencies) is not tuple:
            raise TypeError("discovery prerequisites must be one exact tuple")
        if any(_name(item, field="discovery prerequisite") != item for item in self.dependencies):
            raise HydraDevelopmentError("discovery prerequisite contains an invalid name")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise HydraDevelopmentError("discovery prerequisites must be unique")
        if not callable(self.policy_factory):
            raise TypeError("discovery requires a fresh callable policy factory")
        if type(self.limits) is not SearchLimits:
            raise TypeError("discovery requires exact bounded SearchLimits")
        _name(self.source, field="discovery proposal source")


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """An independent checked candidate, never automatic Alpha admission."""

    epoch_sha256: str
    proposal: DiscoveryProposal
    result: HydraRunResult

    @property
    def checked(self) -> bool:
        return self.result.proved

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": DEVELOPMENT_SCHEMA,
            "track": "proof_discovery",
            "epoch_sha256": self.epoch_sha256,
            "name": self.proposal.name,
            "theorem": self.result.theorem,
            "dependencies": list(self.proposal.dependencies),
            "source": self.proposal.source,
            "search_status": self.result.status,
            "kernel_checked": self.checked,
            "candidate_status": (
                "kernel_checked_candidate_not_admitted"
                if self.checked
                else "unknown"
            ),
            "commands": list(self.result.commands) if self.checked else [],
            "commands_sha256": self.result.commands_sha256,
            "proof_nodes": self.result.search.certificate_nodes,
            "catalog_collision_policy": "exact_source_statement_sha256_only",
            "semantic_novelty_claim": False,
            "alpha_admitted": False,
            "research_claim_eligible": False,
        }


def _reserve(routes: tuple[OptimizationRoute, ...], limits: DevelopmentLimits) -> None:
    if type(routes) is not tuple or not routes:
        raise HydraDevelopmentError("optimization needs one nonempty exact tuple of routes")
    if len(routes) > limits.max_routes:
        raise HydraDevelopmentError("optimization routes exceed their global reservation")
    if not all(type(route) is OptimizationRoute for route in routes):
        raise TypeError("optimization routes must contain exact OptimizationRoute values")
    names = tuple(route.name for route in routes)
    if len(set(names)) != len(names):
        raise HydraDevelopmentError("optimization route names must be unique")
    calls = sum(route.limits.max_model_calls for route in routes)
    states = sum(route.limits.max_states for route in routes)
    candidates = sum(
        route.limits.max_model_calls * route.limits.candidates_per_state
        for route in routes
    )
    if calls > limits.max_total_model_calls:
        raise HydraDevelopmentError("route model-call reservations exceed the global budget")
    if states > limits.max_total_states:
        raise HydraDevelopmentError("route proof-state reservations exceed the global budget")
    if candidates > limits.max_total_candidates:
        raise HydraDevelopmentError("route candidate reservations exceed the global budget")


def optimize_proof(
    epoch: HydraEpoch,
    theorem_name: str,
    routes: tuple[OptimizationRoute, ...],
    *,
    capabilities: SurfaceCapabilities,
    limits: DevelopmentLimits = DevelopmentLimits(),
) -> OptimizationResult:
    """Compare only fresh replay-checked routes to the exact enrolled theorem."""

    _epoch_capabilities(epoch, capabilities)
    if type(limits) is not DevelopmentLimits:
        raise TypeError("optimization requires exact whole-run DevelopmentLimits")
    _name(theorem_name, field="optimization theorem")
    target = epoch.theorem(theorem_name)
    if target is None:
        raise HydraDevelopmentError("optimization target is not in the frozen checked Alpha DAG")
    predecessors = frozenset(
        item.name
        for item in epoch.theorems
        if item.enrollment_index < target.enrollment_index
    )
    if not capabilities.allowed_theorems <= predecessors:
        raise HydraDevelopmentError(
            "optimization may import only strict earlier checked theorems, "
            "never its target or a descendant"
        )
    _reserve(routes, limits)
    theorem = _canonical_theorem(target.statement)
    results: list[tuple[str, HydraRunResult]] = []
    seen_policy_ids: set[int] = set()
    retained_policies: list[HydraPortfolioPolicy] = []
    for route in routes:
        policy = route.policy_factory()
        if id(policy) in seen_policy_ids:
            raise HydraDevelopmentError("optimization routes reused one mutable policy instance")
        seen_policy_ids.add(id(policy))
        retained_policies.append(policy)
        result = run_hydra(
            target.statement,
            policy,
            capabilities=capabilities,
            limits=route.limits,
            label=f"hydra-optimize-{target.name}-{route.name}",
        )
        if result.proved:
            _verified_result(result, theorem=theorem, capabilities=capabilities)
        results.append((route.name, result))
    del retained_policies
    if not results[0][1].proved:
        raise HydraDevelopmentError("optimization baseline has no independently checked proof")
    candidates = tuple(item for item in results if item[1].proved)
    if not candidates:
        raise HydraDevelopmentError("optimization produced no independently checked route")
    winner_name, winner = min(
        candidates,
        key=lambda item: (
            len(item[1].commands),
            item[1].search.certificate_nodes,
            item[1].search.states_expanded,
            item[1].commands,
        ),
    )
    baseline_name, baseline = results[0]
    return OptimizationResult(
        epoch.epoch_sha256,
        target.name,
        theorem,
        tuple(results),
        baseline_name,
        baseline,
        winner_name,
        winner,
        limits,
    )


def discover_proof(
    epoch: HydraEpoch,
    proposal: DiscoveryProposal,
    *,
    capabilities: SurfaceCapabilities,
    limits: DevelopmentLimits = DevelopmentLimits(),
) -> DiscoveryResult:
    """Check a new candidate without promotion, mutation, or novelty claims."""

    _epoch_capabilities(epoch, capabilities)
    if type(proposal) is not DiscoveryProposal:
        raise TypeError("discovery requires one exact DiscoveryProposal")
    if type(limits) is not DevelopmentLimits:
        raise TypeError("discovery requires exact whole-run DevelopmentLimits")
    if epoch.theorem(proposal.name) is not None:
        raise HydraDevelopmentError("discovery theorem name already belongs to the frozen epoch")
    if frozenset(proposal.dependencies) != capabilities.allowed_theorems:
        raise HydraDevelopmentError("discovery prerequisites and theorem allowlist must match exactly")
    source_digest = hashlib.sha256(proposal.theorem.encode("utf-8")).hexdigest()
    if any(item.statement_sha256 == source_digest for item in epoch.theorems):
        raise HydraDevelopmentError("discovery statement already appears in the frozen theorem DAG")
    reservation = OptimizationRoute(
        proposal.name,
        proposal.policy_factory,
        proposal.limits,
    )
    _reserve((reservation,), limits)
    result = run_hydra(
        proposal.theorem,
        proposal.policy_factory(),
        capabilities=capabilities,
        limits=proposal.limits,
        label=f"hydra-discovery-{proposal.name}",
    )
    if result.proved:
        _verified_result(
            result,
            theorem=_canonical_theorem(proposal.theorem),
            capabilities=capabilities,
        )
    return DiscoveryResult(epoch.epoch_sha256, proposal, result)


def recorded_route_factory(
    theorem: str,
    commands: tuple[str, ...],
    *,
    capabilities: SurfaceCapabilities,
    name: str,
) -> Callable[[], HydraCandidatePolicy]:
    """Create fresh recorded-policy lanes from newly kernel-checked traces."""

    _canonical_theorem(theorem)
    _name(name, field="recorded proof route")
    if type(capabilities) is not SurfaceCapabilities:
        raise TypeError("recorded route needs exact execution capabilities")
    if (
        type(commands) is not tuple
        or not 1 <= len(commands) <= MAX_COMMAND_COUNT
        or any(
            type(command) is not str
            or not command
            or command != command.strip()
            or command.splitlines() != [command]
            for command in commands
        )
    ):
        raise HydraDevelopmentError("recorded route needs a bounded tuple of complete tactic lines")
    route_sha256 = hashlib.sha256(
        json.dumps(list(commands), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    def fresh_policy() -> HydraCandidatePolicy:
        source: BatchResult = run_proof(
            theorem,
            commands,
            request_id=f"hydra-source-{route_sha256[:24]}",
            session_id=f"hydra-source-session-{route_sha256[:24]}",
            classical=False,
            on_error="stop",
            capabilities=capabilities,
        )
        if (
            source.status != "proved"
            or source.kernel_checked is not True
            or source.trace is None
            or source.proof_nodes is None
            or source.failed_tactics
            or source.tactics_applied != len(commands)
        ):
            raise HydraDevelopmentError("recorded route failed its original-goal source replay")
        environment = policy_environment(capabilities)
        script = ScriptCandidatePolicy.from_batch_result(
            source,
            name=f"hydra-recorded-{name}",
            policy_environment=environment,
        )
        normalized = AlphaNormalizedScriptPolicy(script)
        return HydraCandidatePolicy(
            (PolicyHead("checked-recorded-route", "symbolic", 1, normalized),),
            name=f"hydra-recorded-portfolio-{name}",
        )

    return fresh_policy


__all__ = [
    "DEVELOPMENT_SCHEMA",
    "AlphaNormalizedScriptPolicy",
    "DevelopmentLimits",
    "DiscoveryProposal",
    "DiscoveryResult",
    "HydraDevelopmentError",
    "OptimizationResult",
    "OptimizationRoute",
    "discover_proof",
    "optimize_proof",
    "recorded_route_factory",
]
