"""Bounded Lucas promotion with shared *already-closed* Stable proof bodies.

This changes no release authority: every leaf is an actual empty-context
certificate, every contextual body is the exact sealed Alpha-v13 script, and
the resulting ordinary proof must pass the unchanged intuitionistic kernel.
Already-closed Stable rows count towards the same immutable 16-body cap.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence

from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.formulas import Imp
from ..kernel.proofs import Proof
from . import editions_v13 as v13
from .frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    ConstructedFrontierClosedCandidate,
    FrontierPromotionError,
    FrontierPromotionPlan,
    _sealed_plan,
    check_frontier_promotion_certificate,
    construct_frontier_closed_microbatch,
    frontier_promotion_plan,
)
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayNode,
    compile_layered_replay,
)
from .theorems import _closed_formula, _primitive


LUCAS_MIXED_TARGET = "choose_prime_divides_between"
LUCAS_MIXED_PENDING_ROWS = (
    "beta_pascal_zero_row_extend",
    "beta_pascal_zero_row_exists",
    "beta_pascal_row_step_extend",
    "beta_pascal_row_step_exists",
    "beta_pascal_table_prefix_extend",
    "beta_pascal_table_prefix_exists",
    "choose_exists",
    "choose_self_of_eq",
    "choose_weighted_vertical",
    "choose_factorial_bridge",
    LUCAS_MIXED_TARGET,
)
LUCAS_MIXED_STABLE_ROWS = (
    "beta_prefix_product_trace_exists",
    "beta_product_exists",
    "beta_range_succ_extend",
    "beta_range_exists",
    "factorial_exists",
)
LUCAS_MIXED_OBSERVED_STABLE_LEAF_NODES = 42_391
LUCAS_MIXED_OBSERVED_STABLE_LEAF_OBJECTS = 10_413
LUCAS_CAMPAIGN_EXPECTED_COUNT = 44
LUCAS_CAMPAIGN_INITIAL_MICROBATCH = (
    "lucas_digit_chain_initial_code_exists",
    "lucas_digit_chain_empty",
    "lucas_digit_chain_empty_exists",
    "lucas_digit_chain_extend",
    "lucas_choose_prefix_empty",
    "lucas_digit_chain_initial_value",
    "lucas_choose_prefix_point",
    "lucas_choose_lower_eq_transport",
    "lucas_prime_block_zero_reassociation",
    "lucas_prime_block_successor_reassociation",
    "lucas_positive_digit_has_bounded_complement",
    "lucas_divisible_implies_zero_mod",
    "lucas_predecessor_digit_below_base",
    "lucas_prime_plus_index_nonzero",
    "lucas_add_positive_index_strict",
    "lucas_modular_backward_product_fold",
)
LUCAS_CAMPAIGN_INITIAL_OBSERVED_DIRECT_STABLE_NODES = 66_162
LUCAS_CAMPAIGN_INITIAL_OBSERVED_DIRECT_STABLE_OBJECTS = 14_824
LUCAS_CAMPAIGN_SECOND_MICROBATCH = (
    "lucas_digit_chain_exists",
    "lucas_prime_digit_nonzero_quotient_strict",
    "lucas_choose_zero_index_is_one",
    "lucas_choose_zero_upper_positive_is_zero",
    "lucas_pascal_congruence_step",
    "lucas_positive_lower_quotient_exceeds_upper_digit",
    "lucas_multidigit_congruence_from_one_step",
)
LUCAS_CAMPAIGN_THIRD_MICROBATCH = (
    "lucas_prime_digit_chain_exists",
    "lucas_prime_digit_chain_nonzero_index_bound",
    "lucas_prime_digit_chain_terminal_zero",
    "lucas_positive_lower_quotient_digit_coefficient_zero",
    "lucas_zero_upper_quotient_high_column_vanishes",
    "lucas_terminating_multidigit_theorem_from_one_step",
)
LUCAS_CAMPAIGN_FOURTH_MICROBATCH = (
    "lucas_terminating_prime_digit_chain_exists",
)


@dataclass(frozen=True, slots=True)
class LucasMixedPromotionPlan:
    """Exact sealed mixed slice; planning/receipt observations are not proofs."""

    target: str
    pending_rows: tuple[str, ...]
    stable_rows: tuple[str, ...]
    checked_leaves: tuple[str, ...]
    pending_leaves: tuple[str, ...]
    parent_alpha_identity_sha256: str

    @property
    def contextual_body_count(self) -> int:
        return len(self.pending_rows) + len(self.stable_rows)


@dataclass(frozen=True, slots=True)
class LucasCampaignClosureRow:
    """One unchanged Alpha-v13 Lucas campaign body and its exact dependencies."""

    alpha_index: int
    name: str
    checked_dependencies: tuple[str, ...]
    parent_dependencies: tuple[str, ...]
    campaign_dependencies: tuple[str, ...]

    @property
    def ready_without_candidates(self) -> bool:
        return not self.parent_dependencies and not self.campaign_dependencies


@dataclass(frozen=True, slots=True)
class LucasCampaignClosurePlan:
    """Planning evidence only: no sealed Alpha-v13 checked authority changes."""

    rows: tuple[LucasCampaignClosureRow, ...]
    parent_names: tuple[str, ...]
    parent_alpha_identity_sha256: str

    @property
    def initially_ready_rows(self) -> tuple[LucasCampaignClosureRow, ...]:
        return tuple(row for row in self.rows if row.ready_without_candidates)


def lucas_campaign_closure_plan(
    *, plan: FrontierPromotionPlan | None = None
) -> LucasCampaignClosurePlan:
    selected = _sealed_plan(
        frontier_promotion_plan(("lucas_theorem",)) if plan is None else plan
    )
    if selected.roots != ("lucas_theorem",):
        raise FrontierPromotionError("Lucas campaign plan requires its exact sealed root")
    frontier = tuple(
        row for row in selected.pending_rows if row.source_release == "v13"
    )
    if len(frontier) != LUCAS_CAMPAIGN_EXPECTED_COUNT:
        raise FrontierPromotionError("Lucas campaign row count differs from sealed Alpha-v13")
    parents = tuple(
        row.name for row in selected.pending_rows if row.source_release == "v12"
    )
    if len(parents) != 30:
        raise FrontierPromotionError("Lucas old-parent row count differs from sealed Alpha-v13")
    table = v13.ALPHA_EDITION.by_name
    parent_set = set(parents)
    frontier_set = {row.name for row in frontier}
    result = []
    for row in frontier:
        dependencies = table[row.name].spec.dependencies
        checked = tuple(name for name in dependencies if table[name].checked_use)
        old = tuple(name for name in dependencies if name in parent_set)
        campaign = tuple(name for name in dependencies if name in frontier_set)
        if len(checked) + len(old) + len(campaign) != len(dependencies):
            raise FrontierPromotionError("Lucas campaign dependency escapes its sealed slice")
        result.append(
            LucasCampaignClosureRow(
                row.alpha_index, row.name, checked, old, campaign
            )
        )
    return LucasCampaignClosurePlan(
        tuple(result), parents, selected.parent_alpha_identity_sha256
    )


def construct_lucas_campaign_closed_microbatch(
    names: Sequence[str] = LUCAS_CAMPAIGN_INITIAL_MICROBATCH,
    *,
    prerequisites: Mapping[str, Proof] | None = None,
    plan: FrontierPromotionPlan | None = None,
) -> tuple[ConstructedFrontierClosedCandidate, ...]:
    """Construct exact campaign proofs under unchanged *aggregate* hard caps."""

    selected = _sealed_plan(
        frontier_promotion_plan(("lucas_theorem",)) if plan is None else plan
    )
    campaign = lucas_campaign_closure_plan(plan=selected)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise FrontierPromotionError("Lucas campaign rows must be a tuple or list")
    if not set(names) <= {row.name for row in campaign.rows}:
        raise FrontierPromotionError("Lucas microbatch contains a noncampaign theorem")
    return construct_frontier_closed_microbatch(
        names, prerequisites=prerequisites, plan=selected
    )


def lucas_campaign_ready_after(
    closed_campaign: Sequence[str],
    *,
    closed_parents: Sequence[str] = (),
    plan: FrontierPromotionPlan | None = None,
) -> tuple[LucasCampaignClosureRow, ...]:
    """Exact dependency-ready planning; names themselves convey no proof authority."""

    campaign = lucas_campaign_closure_plan(plan=plan)
    if isinstance(closed_campaign, str) or not isinstance(closed_campaign, (tuple, list)):
        raise FrontierPromotionError("closed Lucas campaign names must be a tuple or list")
    if isinstance(closed_parents, str) or not isinstance(closed_parents, (tuple, list)):
        raise FrontierPromotionError("closed Lucas parent names must be a tuple or list")
    if any(type(name) is not str for name in tuple(closed_campaign) + tuple(closed_parents)):
        raise FrontierPromotionError("closed Lucas theorem names must be exact strings")
    finished = set(closed_campaign)
    parents = set(closed_parents)
    if len(finished) != len(closed_campaign) or len(parents) != len(closed_parents):
        raise FrontierPromotionError("closed Lucas scheduler names must not repeat")
    if not finished <= {row.name for row in campaign.rows}:
        raise FrontierPromotionError("closed Lucas campaign scheduler contains a foreign row")
    if not parents <= set(campaign.parent_names):
        raise FrontierPromotionError("closed Lucas parent scheduler contains a foreign row")
    return tuple(
        row
        for row in campaign.rows
        if row.name not in finished
        and set(row.campaign_dependencies) <= finished
        and set(row.parent_dependencies) <= parents
    )


def lucas_mixed_promotion_plan(
    target: str = LUCAS_MIXED_TARGET,
    *,
    pending_rows: Sequence[str] = LUCAS_MIXED_PENDING_ROWS,
    stable_rows: Sequence[str] = LUCAS_MIXED_STABLE_ROWS,
    plan: FrontierPromotionPlan | None = None,
) -> LucasMixedPromotionPlan:
    selected = _sealed_plan(
        frontier_promotion_plan(("lucas_theorem",)) if plan is None else plan
    )
    if type(target) is not str:
        raise FrontierPromotionError("mixed Lucas target must be an exact string")
    if isinstance(pending_rows, str) or not isinstance(pending_rows, (tuple, list)):
        raise FrontierPromotionError("mixed Lucas pending rows must be a tuple or list")
    if isinstance(stable_rows, str) or not isinstance(stable_rows, (tuple, list)):
        raise FrontierPromotionError("mixed Lucas Stable rows must be a tuple or list")
    pending = tuple(pending_rows)
    stable = tuple(stable_rows)
    if any(type(name) is not str for name in pending + stable):
        raise FrontierPromotionError("mixed Lucas theorem names must be exact strings")
    if not pending or pending[-1] != target:
        raise FrontierPromotionError("mixed Lucas target must be the final pending body")
    if len(pending) + len(stable) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise FrontierPromotionError("mixed Lucas contextual body count exceeds its cap")
    if len(set(pending + stable)) != len(pending) + len(stable):
        raise FrontierPromotionError("mixed Lucas slice repeats a contextual theorem")

    rows = {row.name: row for row in selected.rows}
    if not set(pending + stable) <= set(rows):
        raise FrontierPromotionError("mixed Lucas row lies outside the sealed root slice")
    if any(not rows[name].needs_closure for name in pending):
        raise FrontierPromotionError("mixed Lucas pending row already has checked use")
    if any(
        rows[name].evidence != v13.EvidenceStatus.STABLE_CLOSED.value
        for name in stable
    ):
        raise FrontierPromotionError("mixed Lucas contextual Stable row is not closed")
    if tuple(rows[name].alpha_index for name in pending) != tuple(
        sorted(rows[name].alpha_index for name in pending)
    ):
        raise FrontierPromotionError("mixed Lucas pending rows are not dependency ordered")
    if tuple(rows[name].alpha_index for name in stable) != tuple(
        sorted(rows[name].alpha_index for name in stable)
    ):
        raise FrontierPromotionError("mixed Lucas Stable rows are not dependency ordered")

    local = set(pending + stable)
    leaves = {
        dependency
        for name in local
        for dependency in v13.ALPHA_EDITION.by_name[name].spec.dependencies
        if dependency not in local
    }
    ordered = tuple(row.name for row in selected.rows if row.name in leaves)
    return LucasMixedPromotionPlan(
        target=target,
        pending_rows=pending,
        stable_rows=stable,
        checked_leaves=tuple(name for name in ordered if rows[name].checked_use),
        pending_leaves=tuple(name for name in ordered if rows[name].needs_closure),
        parent_alpha_identity_sha256=selected.parent_alpha_identity_sha256,
    )


def construct_lucas_mixed_closed_candidate(
    target: str = LUCAS_MIXED_TARGET,
    *,
    pending_rows: Sequence[str] = LUCAS_MIXED_PENDING_ROWS,
    stable_rows: Sequence[str] = LUCAS_MIXED_STABLE_ROWS,
    prerequisites: Mapping[str, Proof] | None = None,
    plan: FrontierPromotionPlan | None = None,
) -> ConstructedFrontierClosedCandidate:
    """Construct one genuinely checked ordinary proof under the old hard caps."""

    selected = _sealed_plan(
        frontier_promotion_plan(("lucas_theorem",)) if plan is None else plan
    )
    mixed = lucas_mixed_promotion_plan(
        target, pending_rows=pending_rows, stable_rows=stable_rows, plan=selected
    )
    provided = {} if prerequisites is None else prerequisites
    if not isinstance(provided, Mapping):
        raise FrontierPromotionError("mixed Lucas prerequisites must be a mapping")
    required = set(mixed.pending_leaves)
    missing = required.difference(provided)
    unexpected = set(provided).difference(required)
    if missing:
        raise FrontierPromotionError(
            f"missing independently closed mixed Lucas leaves: {sorted(missing)!r}"
        )
    if unexpected:
        raise FrontierPromotionError(
            f"unexpected mixed Lucas prerequisite proofs: {sorted(unexpected)!r}"
        )

    local = set(mixed.pending_rows + mixed.stable_rows)
    leaves = set(mixed.pending_leaves + mixed.checked_leaves)
    ordered = tuple(row.name for row in selected.rows if row.name in local or row.name in leaves)
    identities = {name: index for index, name in enumerate(ordered)}
    table = v13.ALPHA_EDITION.by_name
    nodes: list[LayeredReplayNode] = []
    leaf_nodes = 0
    leaf_objects = 0
    for name in ordered:
        exact = table[name].spec
        formula = _closed_formula(exact.statement)
        if name not in local:
            proof = (
                v13.replay(name, edition=v13.EditionName.ALPHA).certificate
                if table[name].checked_use
                else provided[name]
            )
            receipt = check_frontier_promotion_certificate(name, proof, plan=selected)
            leaf_nodes += receipt.proof_nodes
            leaf_objects += receipt.proof_objects
            if leaf_nodes >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES:
                raise FrontierPromotionError("mixed Lucas leaves exceed the proof-node cap")
            if leaf_objects >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS:
                raise FrontierPromotionError("mixed Lucas leaves exceed the proof-object cap")
            nodes.append(LayeredReplayNode(identities[name], formula, (), proof))
            continue

        body_target = formula
        for dependency in reversed(exact.dependencies):
            body_target = Imp(_closed_formula(table[dependency].spec.statement), body_target)
        try:
            state = start(body_target)
            for dependency in exact.dependencies:
                state = apply_tactic(state, "intro", dependency)
            for command in exact.script:
                tactic, arguments = _primitive(command)
                if tactic == "use":
                    raise FrontierPromotionError(
                        f"mixed Lucas body {name!r} attempts implicit theorem authority"
                    )
                state = apply_tactic(state, tactic, arguments)
            body = checked_final(state, body_target)
        except FrontierPromotionError:
            raise
        except (AttributeError, IndexError, RuntimeError, TypeError, ValueError) as exc:
            raise FrontierPromotionError(
                f"cannot replay the exact sealed mixed Lucas body {name!r}"
            ) from exc
        nodes.append(
            LayeredReplayNode(
                identities[name],
                formula,
                tuple(identities[dependency] for dependency in exact.dependencies),
                body,
            )
        )

    limits = replace(
        DEFAULT_LAYERED_REPLAY_LIMITS,
        max_body_occurrences=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
        max_body_objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
        max_total_body_occurrences=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
        max_total_body_objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
        max_candidate_proof_occurrences=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
        max_candidate_proof_objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    )
    formula = _closed_formula(table[target].spec.statement)
    candidate = compile_layered_replay(
        LayeredReplayBundle(tuple(nodes), identities[target]), formula, limits=limits
    )
    if candidate is None:
        raise FrontierPromotionError(
            f"mixed Lucas candidate {target!r} violates its unchanged kernel/resource cap"
        )
    receipt = check_frontier_promotion_certificate(target, candidate.certificate, plan=selected)
    return ConstructedFrontierClosedCandidate(target, candidate.certificate, receipt)
