"""Bounded original-kernel closures of the deferred power-valuation roots.

The independently closed search and zero-power premises contain the same
59,836-node Stable ``pow_exists`` proof.  Composing them as separate ordinary
proofs therefore exceeds the immutable 125,000-node microbatch limit, even
though their underlying proof data overlap almost completely.

This module shares that actual Stable proof through ordinary layered ``Cut``
nodes.  All local bodies are the exact unchanged Alpha-v12 scripts, all Stable
leaves are actual independently kernel-checked empty-context proofs, and both
resulting roots are checked again against their exact original formulas.  No
kernel rule, resource ceiling, Alpha evidence, or Stable membership changes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.checker import check
from ..kernel.formulas import Formula, Imp
from ..kernel.proofs import Proof
from . import editions_v12 as v12
from .bertrand_promotion import (
    MAX_BERTRAND_CLOSURE_MICROBATCH,
    MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    BertrandPromotionError,
    BertrandPromotionPlan,
    CheckedBertrandPromotionCertificate,
    ConstructedBertrandClosedCandidate,
    _sealed_promotion_plan,
    check_bertrand_promotion_certificate,
)
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayNode,
    compile_layered_replay,
)
from .theorems import _closed_formula, _primitive


BOUNDED_VALUATION_SHARED_TARGET = "bounded_power_valuation_exists"
CANONICAL_VALUATION_SHARED_TARGET = "power_valuation_exists"
VALUATION_SHARED_TARGETS = (
    BOUNDED_VALUATION_SHARED_TARGET,
    CANONICAL_VALUATION_SHARED_TARGET,
)
VALUATION_SHARED_PENDING_ROWS = (
    "power_divides_decidable",
    "power_divides_zero",
    "bounded_power_valuation_search",
    BOUNDED_VALUATION_SHARED_TARGET,
)
VALUATION_SHARED_STABLE_LEAVES = (
    "le_refl",
    "zero_le",
    "le_zero",
    "le_of_succ_le_succ",
    "le_succ",
    "le_eq_or_lt",
    "one_multiple",
    "multiple_decidable",
    "pow_exists",
    "pow_zero",
    "pow_functional",
)
VALUATION_NAIVE_BOUNDED_PROOF_NODES = 125_454
VALUATION_NAIVE_CANONICAL_PROOF_NODES = 125_470
VALUATION_REUSED_POWER_TOTALITY_PROOF_NODES = 59_836
VALUATION_SHARED_STABLE_LEAF_PROOF_NODES = 65_364
VALUATION_SHARED_STABLE_LEAF_PROOF_OBJECTS = 7_956


class ValuationSharedPromotionError(BertrandPromotionError):
    """The frozen valuation slice, actual proof, or hard resource cap failed."""


@dataclass(frozen=True, slots=True)
class ValuationSharedPromotionPlan:
    """Exact dependency slice and proof budget; planning grants no authority."""

    target: str
    pending_rows: tuple[str, ...]
    stable_leaves: tuple[str, ...]
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str

    @property
    def proof_graph_node_count(self) -> int:
        return len(self.pending_rows) + len(self.stable_leaves)

    @property
    def contextual_body_count(self) -> int:
        return len(self.pending_rows)


def _canonical_target(target: str) -> str:
    if type(target) is not str or target not in VALUATION_SHARED_TARGETS:
        raise ValuationSharedPromotionError(
            "shared valuation target must be one of the two exact deferred roots"
        )
    return target


def _canonical_rows(target: str) -> tuple[str, ...]:
    return (
        VALUATION_SHARED_PENDING_ROWS
        if target == BOUNDED_VALUATION_SHARED_TARGET
        else VALUATION_SHARED_PENDING_ROWS + (CANONICAL_VALUATION_SHARED_TARGET,)
    )


def valuation_shared_promotion_plan(
    target: str = BOUNDED_VALUATION_SHARED_TARGET,
    *,
    plan: BertrandPromotionPlan | None = None,
) -> ValuationSharedPromotionPlan:
    """Bind the exact original deferred roots without replaying any proof."""

    wanted = _canonical_target(target)
    selected = _sealed_promotion_plan(plan)
    rows = _canonical_rows(wanted)
    by_name = {row.name: row for row in selected.rows}
    if any(name not in by_name for name in rows):
        raise ValuationSharedPromotionError(
            "shared valuation theorem is outside the sealed Bertrand closure"
        )
    if any(not by_name[name].needs_closure for name in rows):
        raise ValuationSharedPromotionError(
            "shared valuation rows must remain exact body-only Alpha entries"
        )
    indices = tuple(by_name[name].alpha_index for name in rows)
    if indices != tuple(sorted(indices)) or rows[-1] != wanted:
        raise ValuationSharedPromotionError(
            "shared valuation rows are not in frozen dependency order"
        )

    table = v12.ALPHA_EDITION.by_name
    local = set(rows)
    leaves = {
        dependency
        for name in rows
        for dependency in table[name].spec.dependencies
        if dependency not in local
    }
    ordered_leaves = tuple(row.name for row in selected.rows if row.name in leaves)
    if ordered_leaves != VALUATION_SHARED_STABLE_LEAVES:
        raise ValuationSharedPromotionError(
            "shared valuation leaves changed their exact sealed Stable slice"
        )
    if any(
        table[name].evidence is not v12.EvidenceStatus.STABLE_CLOSED
        or not table[name].checked_use
        for name in ordered_leaves
    ):
        raise ValuationSharedPromotionError(
            "shared valuation leaves must all have genuine Stable authority"
        )
    if ordered_leaves.count("pow_exists") != 1:
        raise ValuationSharedPromotionError(
            "shared valuation graph must cut Stable power totality exactly once"
        )
    result = ValuationSharedPromotionPlan(
        target=wanted,
        pending_rows=rows,
        stable_leaves=ordered_leaves,
        parent_alpha_identity_sha256=selected.parent_alpha_identity_sha256,
        parent_alpha_enrollment_sha256=selected.parent_alpha_enrollment_sha256,
    )
    if result.proof_graph_node_count > MAX_BERTRAND_CLOSURE_MICROBATCH:
        raise ValuationSharedPromotionError(
            "shared valuation graph exceeds its immutable sixteen-row budget"
        )
    return result


def _sealed_shared_plan(
    target: str,
    *,
    plan: BertrandPromotionPlan,
    shared_plan: ValuationSharedPromotionPlan | None,
) -> ValuationSharedPromotionPlan:
    expected = valuation_shared_promotion_plan(target, plan=plan)
    if shared_plan is None:
        return expected
    if type(shared_plan) is not ValuationSharedPromotionPlan or shared_plan != expected:
        raise ValuationSharedPromotionError(
            "shared valuation plan does not match its exact sealed dependency slice"
        )
    return shared_plan


def _replay_exact_body(name: str, dependencies: Sequence[str]) -> tuple[Formula, Proof]:
    table = v12.ALPHA_EDITION.by_name
    specification = table[name].spec
    formula = _closed_formula(specification.statement)
    target = formula
    for dependency in reversed(dependencies):
        target = Imp(_closed_formula(table[dependency].spec.statement), target)
    try:
        state = start(target)
        for dependency in dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in specification.script:
            tactic, arguments = _primitive(command)
            if tactic == "use":
                raise ValuationSharedPromotionError(
                    f"shared valuation body {name!r} requests implicit theorem authority"
                )
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
    except ValuationSharedPromotionError:
        raise
    except (AttributeError, IndexError, RuntimeError, TypeError, ValueError) as exc:
        raise ValuationSharedPromotionError(
            f"cannot replay the exact original valuation proof body {name!r}"
        ) from exc
    if not check((), body, target):
        raise ValuationSharedPromotionError(
            f"unchanged kernel rejected the exact curried valuation body {name!r}"
        )
    return formula, body


def check_valuation_shared_candidate(
    target: str,
    certificate: Proof,
    *,
    plan: BertrandPromotionPlan | None = None,
) -> CheckedBertrandPromotionCertificate:
    """Check the exact ordinary root and both unchanged hard proof limits."""

    wanted = _canonical_target(target)
    selected = _sealed_promotion_plan(plan)
    try:
        diagnostics = check_bertrand_promotion_certificate(
            wanted,
            certificate,
            plan=selected,
        )
    except BertrandPromotionError as exc:
        raise ValuationSharedPromotionError(
            f"unchanged intuitionistic kernel rejected shared valuation root {wanted!r}"
        ) from exc
    if (
        diagnostics.proof_nodes > MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
        or diagnostics.proof_objects > MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS
    ):
        raise ValuationSharedPromotionError(
            "shared valuation proof exceeds the unchanged 125,000/25,000 limits"
        )
    return diagnostics


def construct_valuation_shared_closed_candidate(
    target: str = BOUNDED_VALUATION_SHARED_TARGET,
    *,
    plan: BertrandPromotionPlan | None = None,
    shared_plan: ValuationSharedPromotionPlan | None = None,
) -> ConstructedBertrandClosedCandidate:
    """Construct one actual deferred empty-context proof under all old caps."""

    wanted = _canonical_target(target)
    selected = _sealed_promotion_plan(plan)
    exact_plan = _sealed_shared_plan(wanted, plan=selected, shared_plan=shared_plan)
    local = set(exact_plan.pending_rows)
    leaves = set(exact_plan.stable_leaves)
    ordered = tuple(
        row.name for row in selected.rows if row.name in local or row.name in leaves
    )
    identities = {name: index for index, name in enumerate(ordered)}
    if len(ordered) != exact_plan.proof_graph_node_count:
        raise ValuationSharedPromotionError(
            "shared valuation proof graph changed its exact bounded node count"
        )

    table = v12.ALPHA_EDITION.by_name
    nodes: list[LayeredReplayNode] = []
    leaf_nodes = 0
    leaf_objects = 0
    for name in ordered:
        specification = table[name].spec
        formula = _closed_formula(specification.statement)
        if name not in local:
            actual = v12.replay(name, edition=v12.EditionName.ALPHA)
            diagnostics = check_bertrand_promotion_certificate(
                name,
                actual.certificate,
                plan=selected,
            )
            leaf_nodes += diagnostics.proof_nodes
            leaf_objects += diagnostics.proof_objects
            if (
                leaf_nodes >= MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
                or leaf_objects >= MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS
            ):
                raise ValuationSharedPromotionError(
                    "actual shared valuation Stable leaves already exceed their hard caps"
                )
            nodes.append(
                LayeredReplayNode(identities[name], formula, (), actual.certificate)
            )
            continue

        actual_formula, body = _replay_exact_body(name, specification.dependencies)
        if actual_formula != formula:
            raise ValuationSharedPromotionError(
                f"shared valuation row {name!r} changed its exact original formula"
            )
        nodes.append(
            LayeredReplayNode(
                identities[name],
                formula,
                tuple(identities[dependency] for dependency in specification.dependencies),
                body,
            )
        )

    if (
        leaf_nodes != VALUATION_SHARED_STABLE_LEAF_PROOF_NODES
        or leaf_objects != VALUATION_SHARED_STABLE_LEAF_PROOF_OBJECTS
    ):
        raise ValuationSharedPromotionError(
            "actual shared valuation Stable proof metrics differ from the frozen slice"
        )
    limits = replace(
        DEFAULT_LAYERED_REPLAY_LIMITS,
        max_body_occurrences=MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES,
        max_body_objects=MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS,
        max_total_body_occurrences=MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES,
        max_total_body_objects=MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS,
        max_candidate_proof_occurrences=(
            MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
        ),
        max_candidate_proof_objects=MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    )
    target_formula = _closed_formula(table[wanted].spec.statement)
    candidate = compile_layered_replay(
        LayeredReplayBundle(tuple(nodes), identities[wanted]),
        target_formula,
        limits=limits,
    )
    if candidate is None:
        raise ValuationSharedPromotionError(
            f"shared valuation proof for {wanted!r} exceeds its unchanged kernel "
            "or resource envelope"
        )
    diagnostics = check_valuation_shared_candidate(
        wanted,
        candidate.certificate,
        plan=selected,
    )
    return ConstructedBertrandClosedCandidate(
        wanted,
        candidate.certificate,
        diagnostics,
    )


__all__ = [
    "BOUNDED_VALUATION_SHARED_TARGET",
    "CANONICAL_VALUATION_SHARED_TARGET",
    "VALUATION_NAIVE_BOUNDED_PROOF_NODES",
    "VALUATION_NAIVE_CANONICAL_PROOF_NODES",
    "VALUATION_REUSED_POWER_TOTALITY_PROOF_NODES",
    "VALUATION_SHARED_PENDING_ROWS",
    "VALUATION_SHARED_STABLE_LEAF_PROOF_NODES",
    "VALUATION_SHARED_STABLE_LEAF_PROOF_OBJECTS",
    "VALUATION_SHARED_STABLE_LEAVES",
    "VALUATION_SHARED_TARGETS",
    "ValuationSharedPromotionError",
    "ValuationSharedPromotionPlan",
    "check_valuation_shared_candidate",
    "construct_valuation_shared_closed_candidate",
    "valuation_shared_promotion_plan",
]
