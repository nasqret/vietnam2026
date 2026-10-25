"""Bounded, evidence-honest closure planning for the Lagrange flagship.

Every selected row is pinned to the unchanged Alpha-v13 edition.  Planning a
dependency or measuring a body never changes release evidence: only an actual
empty-context proof checked by the unchanged intuitionistic kernel is accepted
as a prerequisite, and even such a proof grants no checked-use authority until
a separately reviewed, versioned admission exists.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from ..kernel.proofs import Proof
from . import editions_v13 as v13
from .frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    CheckedFrontierPromotionCertificate,
    ConstructedFrontierClosedCandidate,
    FrontierPromotionError,
    FrontierPromotionPlan,
    FrontierPromotionRow,
    construct_frontier_closed_candidate,
    construct_frontier_closed_microbatch,
    construct_frontier_shared_closed_candidate,
    frontier_pending_layers,
    frontier_promotion_plan,
)


FOUR_SQUARE_FRONTIER_ROOT = "four_square_lagrange"
FOUR_SQUARE_FRONTIER_TOTAL_COUNT = 390
FOUR_SQUARE_FRONTIER_STABLE_COUNT = 166
FOUR_SQUARE_FRONTIER_ALPHA_CLOSED_COUNT = 5
FOUR_SQUARE_FRONTIER_PENDING_COUNT = 219
FOUR_SQUARE_FRONTIER_PARENT_COUNT = 23
FOUR_SQUARE_FRONTIER_CAMPAIGN_COUNT = 196
FOUR_SQUARE_FRONTIER_EDGE_COUNT = 1_187
FOUR_SQUARE_FRONTIER_ORDERED_NAMES_SHA256 = (
    "9a94742066b28f553ad78fd675c41354a461cbe5f69f8e5df3ec36f9b055a843"
)
FOUR_SQUARE_FRONTIER_EXACT_SURFACE_SHA256 = (
    "8a92bf2d6fd4c716112d1a84994725589f696c6289e6a33d1729ea33235759d5"
)

# These nine rows have already been independently checked by the generic
# bounded promotion suite.  Their observations are diagnostics, not release
# evidence or proof objects.
FOUR_SQUARE_ESTABLISHED_PARENT_DIAGNOSTICS = (
    ("bounded_nonzero_not_divides", 140),
    ("pair_order_double_succ_length", 46),
    ("odd_half_strictly_below_modulus", 315),
    ("even_to_mod_two_zero", 55),
    ("odd_to_mod_two_one", 115),
    ("mul_le_mul", 521),
    ("two_mul_eq_add_self", 275),
    ("square_lt_successor_square", 592),
    ("mul_le_cancel_left_nonzero", 679),
)
FOUR_SQUARE_ESTABLISHED_PARENT_NAMES = tuple(
    name for name, _nodes in FOUR_SQUARE_ESTABLISHED_PARENT_DIAGNOSTICS
)

# All eighteen non-beta parent rows form an exact dependency-closed subgraph.
# A single microbatch is deliberately limited to the first sixteen.  The last
# two rows already have the independently checked 592-/679-node certificates
# displayed above; no existing limit is increased to merge them.
FOUR_SQUARE_NON_BETA_PARENT_NAMES = (
    "bounded_nonzero_not_divides",
    "mod_eq_zero_to_dvd_nonzero",
    "pair_order_double_succ_length",
    "odd_half_strictly_below_modulus",
    "even_sum_parity_cases",
    "even_sum_iff_same_parity",
    "odd_sum_parity_cases",
    "even_to_mod_two_zero",
    "odd_to_mod_two_one",
    "matching_parity_mod_two",
    "mod_two_zero_to_even",
    "mod_two_one_to_odd",
    "mod_two_preserves_parity",
    "mul_le_mul",
    "mul_shuffle_four",
    "two_mul_eq_add_self",
    "square_lt_successor_square",
    "mul_le_cancel_left_nonzero",
)
FOUR_SQUARE_NON_BETA_PARENT_MICROBATCH = (
    FOUR_SQUARE_NON_BETA_PARENT_NAMES[:MAX_FRONTIER_CLOSURE_MICROBATCH]
)

FOUR_SQUARE_BETA_PARENT_NAMES = (
    "beta_pointwise_mul_prefix_extend",
    "beta_pointwise_mul_prefix_exists",
    "beta_prefix_append_two_exists",
    "beta_division_prefix_extend",
    "beta_division_prefix_exists",
)

# Exact checked Stable direct-premise observations from the immutable Alpha-v13
# catalog. The middle and final existence rows additionally require the actual
# closed extension proof named in their fourth tuple field.
FOUR_SQUARE_BETA_PARENT_STABLE_DIRECT_LEAF_BUDGETS = (
    ("beta_pointwise_mul_prefix_extend", 30_785, 5_716, ()),
    (
        "beta_pointwise_mul_prefix_exists",
        499,
        412,
        ("beta_pointwise_mul_prefix_extend",),
    ),
    ("beta_prefix_append_two_exists", 29_122, 4_571, ()),
    ("beta_division_prefix_extend", 29_185, 4_632, ()),
    (
        "beta_division_prefix_exists",
        718,
        608,
        ("beta_division_prefix_extend",),
    ),
)

# Actual observations from five independently kernel-checked singleton
# empty-context proof batches. Their 150,981-node sum is deliberately never
# represented as one microbatch; each individual certificate obeys 125k/25k.
FOUR_SQUARE_BETA_PARENT_CHECKED_DIAGNOSTICS = (
    ("beta_pointwise_mul_prefix_extend", 30_906, 4_643),
    ("beta_pointwise_mul_prefix_exists", 31_467, 4_705),
    ("beta_prefix_append_two_exists", 29_185, 4_571),
    ("beta_division_prefix_extend", 29_317, 4_654),
    ("beta_division_prefix_exists", 30_106, 4_725),
)
FOUR_SQUARE_BETA_PARENT_STATEMENT_SHA256 = (
    (
        "beta_pointwise_mul_prefix_extend",
        "effadbb2e017f714693b0a8fe3f2353d70a99f85925ad603028899f3d95b54bb",
    ),
    (
        "beta_pointwise_mul_prefix_exists",
        "61170d1ab57371e2d19f5f39e0d8f8a69ca31b2d0918a5e33a3a10c72fba8019",
    ),
    (
        "beta_prefix_append_two_exists",
        "9731f9602faa3637a0401c45ff4afbdd46666e570e66abb52b6ea8a151cb9510",
    ),
    (
        "beta_division_prefix_extend",
        "cec6006a1941b572a48c95a09f08c4d8bf3322a3560c43f2a949767dd791ff87",
    ),
    (
        "beta_division_prefix_exists",
        "d82de890a8fdd2afd3f31bb1621391d7f8385f5ca7d8f78ca5556f6c5f40ec89",
    ),
)

# Measured after constructing sixteen actual empty-context certificates in one
# unchanged-kernel microbatch. Counts are observations, never substitutes for
# the independently checked Proof objects themselves.
FOUR_SQUARE_NON_BETA_MICROBATCH_DIAGNOSTICS = (
    ("bounded_nonzero_not_divides", 140, 138),
    ("mod_eq_zero_to_dvd_nonzero", 2_074, 1_018),
    ("pair_order_double_succ_length", 46, 43),
    ("odd_half_strictly_below_modulus", 315, 214),
    ("even_sum_parity_cases", 1_402, 858),
    ("even_sum_iff_same_parity", 1_867, 1_023),
    ("odd_sum_parity_cases", 1_496, 875),
    ("even_to_mod_two_zero", 55, 54),
    ("odd_to_mod_two_one", 115, 104),
    ("matching_parity_mod_two", 487, 341),
    ("mod_two_zero_to_even", 2_094, 1_038),
    ("mod_two_one_to_odd", 2_065, 1_012),
    ("mod_two_preserves_parity", 4_679, 1_258),
    ("mul_le_mul", 521, 348),
    ("mul_shuffle_four", 377, 311),
    ("two_mul_eq_add_self", 275, 234),
)

# Sealed direct Stable/Alpha leaf measurements and exact tactic-line counts
# for all 52 v13 campaign rows requiring no body-only prerequisites.  These
# measurements schedule replay; the unchanged kernel still checks every proof.
FOUR_SQUARE_INITIAL_CAMPAIGN_READY_COUNT = 52
FOUR_SQUARE_INITIAL_CAMPAIGN_LEAF_BUDGETS = (
    ("four_square_branch_nonzero_even_half", 0, 0, 10),
    ("four_square_prime_modular_seed_multiple", 0, 0, 11),
    ("four_square_descent_zero_centered_remainder_divides", 0, 0, 13),
    ("four_square_square_residue_prefix_bounded", 0, 0, 19),
    ("four_square_descent_modular_seed_multiplier_nonzero", 1, 1, 14),
    ("four_square_odd_prime_half_positive", 11, 11, 19),
    ("multiple_implies_balanced_zero_congruence", 17, 17, 8),
    ("signed_balance_absolute_exists", 36, 36, 25),
    ("finite_prefix_collision_succ", 40, 38, 31),
    ("four_square_descent_nonzero_square", 47, 47, 13),
    ("four_square_signed_mod_zero_swap", 73, 67, 8),
    ("four_square_signed_lower_remainder_congruent", 90, 84, 9),
    ("four_square_complement_gap_symmetry", 100, 92, 7),
    ("four_square_euler_add_swap_last", 106, 97, 11),
    ("two_square_add_swap_nested", 106, 97, 11),
    ("four_square_add_swap_right_tail", 106, 97, 11),
    ("four_square_equal_square_remainders_are_congruent", 106, 97, 21),
    ("four_square_descent_nonunit_proper_factor_not_prime", 116, 114, 23),
    ("finite_prefix_last_occurrence_collision", 148, 144, 28),
    ("four_square_descent_zero_norm_coordinates", 194, 169, 44),
    ("four_square_descent_norm_bound_forces_smaller_multiplier", 198, 191, 22),
    ("quaternion_coordinate_balance_total", 236, 230, 39),
    ("four_square_euler_four_add_shuffle", 245, 161, 13),
    ("four_square_descent_add_le_add", 245, 161, 14),
    ("four_square_signed_mod_zero_equivalent", 264, 216, 18),
    ("four_square_half_double_below_odd", 270, 248, 6),
    ("four_square_two_half_ranges_overflow_odd", 270, 248, 6),
    ("four_square_descent_below_prime_multiplier_bounded", 272, 262, 70),
    ("four_square_parity_swap_middle_coordinates", 278, 191, 10),
    ("four_square_norm_distributes", 326, 263, 9),
    ("four_square_product_shuffle", 338, 304, 23),
    ("four_square_descent_remainder_complement_exists", 341, 311, 30),
    ("four_square_parity_swap_outer_coordinates", 351, 258, 14),
    ("balanced_zero_congruence_implies_multiple", 355, 321, 17),
    ("four_square_branch_positive_half_strict", 359, 331, 16),
    ("four_square_signed_mod_zero_add", 387, 266, 18),
    ("four_square_signed_mod_zero_plus_congruent", 387, 266, 19),
    ("four_square_sum_expansion", 403, 333, 3),
    ("four_square_complementary_remainders_form_multiple", 415, 319, 21),
    ("four_square_signed_dot_positive", 484, 339, 10),
    ("four_square_signed_common_zero_cancel", 574, 442, 26),
    ("four_square_complement_prefix_preserves_injectivity", 623, 530, 67),
    ("four_square_signed_absolute_congruence_divisible", 643, 389, 31),
    ("two_square_sum_square_expands", 658, 563, 3),
    ("four_square_ordered_square_difference_factor", 731, 630, 18),
    ("four_square_signed_negative_scale_zero", 831, 623, 19),
    ("four_square_signed_cross_positive", 970, 755, 37),
    ("finite_prefix_injective_extend_fresh", 1_249, 816, 77),
    ("balanced_zero_sum_implies_squared_congruence", 1_589, 1_128, 50),
    ("four_square_cross_covered_prefix_bounded", 1_600, 1_084, 69),
    ("four_square_bounded_complement_prefix_exists", 30_870, 5_799, 123),
    ("finite_bounded_into_oversized_not_injective", 42_670, 6_599, 88),
)
FOUR_SQUARE_INITIAL_CAMPAIGN_BATCH_LEAF_BUDGETS = (
    (16, 733, 684),
    (16, 3_847, 3_310),
    (16, 9_420, 7_181),
    (4, 76_729, 14_610),
)

# Actual independent empty-context microbatch observations. Each batch was
# separately kernel-checked; sums across batches are never one proof budget.
FOUR_SQUARE_INITIAL_CAMPAIGN_CHECKED_BATCH_DIAGNOSTICS = (
    (16, 1_232, 1_125),
    (16, 4_552, 3_664),
    (16, 10_261, 5_964),
    (4, 77_161, 12_811),
)
FOUR_SQUARE_CAMPAIGN_NEXT_READY_COUNT = 41
FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_PREREQUISITES = (
    "bounded_nonzero_not_divides",
    "odd_sum_parity_cases",
    "even_to_mod_two_zero",
    "odd_to_mod_two_one",
    "matching_parity_mod_two",
    "mul_shuffle_four",
    "signed_balance_absolute_exists",
    "four_square_descent_nonzero_square",
    "four_square_add_swap_right_tail",
    "multiple_implies_balanced_zero_congruence",
)
FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES = (
    "four_square_parity_square_mod_two_self",
    "four_square_parity_odd_blocks_crossed_selection",
    "four_square_absolute_difference_total",
    "two_square_product_expands",
    "two_square_cross_product_interchange",
    "four_square_descent_product_reassociate",
    "four_square_descent_square_factor_cancel",
    "four_square_bounded_multiple_is_zero",
    "four_square_signed_cases_norm_quotient_zero_congruence",
    "four_square_additive_gap_reorder",
    "four_square_conjugate_diagonal_regroup",
    "four_square_euler_cross_swap",
    "four_square_euler_add_permute_nine",
    "four_square_euler_add_permute_six",
    "four_square_euler_add_permute_sixteen",
    "four_square_euler_add_permute_twelve",
)
FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_NODE_UPPER_BOUND = 18_284
FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_OBJECT_UPPER_BOUND = 15_428
FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_CHECKED_PREREQUISITE_DIAGNOSTICS = (
    10,
    2_973,
    2_114,
)
FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_CHECKED_DIAGNOSTICS = (
    ("four_square_parity_square_mod_two_self", 1_635, 714),
    ("four_square_parity_odd_blocks_crossed_selection", 1_577, 956),
    ("four_square_absolute_difference_total", 322, 316),
    ("two_square_product_expands", 828, 383),
    ("two_square_cross_product_interchange", 623, 335),
    ("four_square_descent_product_reassociate", 615, 327),
    ("four_square_descent_square_factor_cancel", 320, 226),
    ("four_square_bounded_multiple_is_zero", 209, 207),
    ("four_square_signed_cases_norm_quotient_zero_congruence", 62, 61),
    ("four_square_additive_gap_reorder", 525, 229),
    ("four_square_conjugate_diagonal_regroup", 767, 628),
    ("four_square_euler_cross_swap", 623, 335),
    ("four_square_euler_add_permute_nine", 419, 293),
    ("four_square_euler_add_permute_six", 309, 188),
    ("four_square_euler_add_permute_sixteen", 767, 627),
    ("four_square_euler_add_permute_twelve", 628, 497),
)
FOUR_SQUARE_CAMPAIGN_CONTINUATION_READY_COUNT = 34
FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITES = (
    "even_sum_parity_cases",
    "even_sum_iff_same_parity",
    "odd_sum_parity_cases",
    "mul_shuffle_four",
    "two_mul_eq_add_self",
    "mul_le_cancel_left_nonzero",
    "four_square_parity_odd_blocks_crossed_selection",
    "two_square_product_expands",
    "two_square_add_swap_nested",
    "four_square_product_shuffle",
    "four_square_add_swap_right_tail",
    "four_square_complement_gap_symmetry",
    "four_square_euler_cross_swap",
    "four_square_euler_add_permute_nine",
    "four_square_euler_add_permute_six",
    "four_square_euler_add_permute_sixteen",
)
FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES = (
    "four_square_parity_even_coordinate_pair_selection",
    "four_square_descent_matching_parity_sum_even",
    "two_square_product_norm_blocks",
    "two_square_absolute_difference_square_balance",
    "four_square_product_square",
    "four_square_descent_odd_centered_magnitude_half_bound",
    "four_square_complement_prefix_bounded",
    "four_square_signed_pair_cross_decomposition",
    "four_square_euler_double_cross_swap",
    "four_square_euler_three_square_expansion",
    "four_square_euler_cross_triple_expansion",
    "four_square_euler_diagonal_regroup",
)
FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_NODE_UPPER_BOUND = 18_867
FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_OBJECT_UPPER_BOUND = 13_801
FOUR_SQUARE_CAMPAIGN_CONTINUATION_NODE_UPPER_BOUND = 21_029
FOUR_SQUARE_CAMPAIGN_CONTINUATION_OBJECT_UPPER_BOUND = 15_823
FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_PREREQUISITE_DIAGNOSTICS = (
    16,
    11_374,
    7_149,
)
FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_DIAGNOSTICS = (
    ("four_square_parity_even_coordinate_pair_selection", 3_061, 1_176),
    ("four_square_descent_matching_parity_sum_even", 1_890, 1_046),
    ("two_square_product_norm_blocks", 1_170, 473),
    ("two_square_absolute_difference_square_balance", 1_194, 523),
    ("four_square_product_square", 385, 319),
    ("four_square_descent_odd_centered_magnitude_half_bound", 2_058, 1_133),
    ("four_square_complement_prefix_bounded", 645, 456),
    ("four_square_signed_pair_cross_decomposition", 788, 426),
    ("four_square_euler_double_cross_swap", 639, 351),
    ("four_square_euler_three_square_expansion", 888, 521),
    ("four_square_euler_cross_triple_expansion", 752, 394),
    ("four_square_euler_diagonal_regroup", 793, 653),
)


@dataclass(frozen=True, slots=True)
class FourSquareFrontierObligation:
    """One exact body-only obligation and its unchecked prerequisite surface."""

    name: str
    source_release: str
    statement_sha256: str
    pending_dependencies: tuple[str, ...]
    pending_parent_dependencies: tuple[str, ...]
    pending_layer: int

    @property
    def is_parent(self) -> bool:
        return self.source_release == "v12"


@dataclass(frozen=True, slots=True)
class FourSquareFrontierPlan:
    """Specialized immutable Lagrange slice; no proof authority is inferred."""

    source: FrontierPromotionPlan
    obligations: tuple[FourSquareFrontierObligation, ...]
    layers: tuple[tuple[str, ...], ...]
    parent_layers: tuple[tuple[str, ...], ...]

    @property
    def parent_obligations(self) -> tuple[FourSquareFrontierObligation, ...]:
        return tuple(item for item in self.obligations if item.is_parent)

    @property
    def campaign_obligations(self) -> tuple[FourSquareFrontierObligation, ...]:
        return tuple(item for item in self.obligations if not item.is_parent)

    @property
    def ready_parent_names(self) -> tuple[str, ...]:
        return tuple(
            item.name
            for item in self.parent_obligations
            if not item.pending_dependencies
        )

    @property
    def ready_campaign_names(self) -> tuple[str, ...]:
        return tuple(
            item.name
            for item in self.campaign_obligations
            if not item.pending_dependencies
        )


@dataclass(frozen=True, slots=True)
class FourSquareCampaignMicrobatchPlan:
    """A bounded, parent-independent scheduling plan, not a proof receipt."""

    index: int
    names: tuple[str, ...]
    direct_leaf_proof_nodes: int
    direct_leaf_proof_objects: int


@dataclass(frozen=True, slots=True)
class FourSquareCampaignMicrobatchReceipt:
    """Diagnostics from actual independently checked empty-context proofs."""

    index: int
    names: tuple[str, ...]
    proof_nodes: int
    proof_objects: int
    certificates: tuple[CheckedFrontierPromotionCertificate, ...]


def _validate_exact_source(source: FrontierPromotionPlan) -> None:
    actual = (
        source.roots,
        len(source.rows),
        len(source.stable_rows),
        len(source.alpha_closed_rows),
        len(source.pending_rows),
        len(source.unchecked_parent_rows),
        len(source.unchecked_frontier_rows),
        source.dependency_edge_count,
        source.ordered_names_sha256,
        source.exact_surface_sha256,
        source.parent_alpha_enrollment_sha256,
        source.parent_alpha_identity_sha256,
    )
    expected = (
        (FOUR_SQUARE_FRONTIER_ROOT,),
        FOUR_SQUARE_FRONTIER_TOTAL_COUNT,
        FOUR_SQUARE_FRONTIER_STABLE_COUNT,
        FOUR_SQUARE_FRONTIER_ALPHA_CLOSED_COUNT,
        FOUR_SQUARE_FRONTIER_PENDING_COUNT,
        FOUR_SQUARE_FRONTIER_PARENT_COUNT,
        FOUR_SQUARE_FRONTIER_CAMPAIGN_COUNT,
        FOUR_SQUARE_FRONTIER_EDGE_COUNT,
        FOUR_SQUARE_FRONTIER_ORDERED_NAMES_SHA256,
        FOUR_SQUARE_FRONTIER_EXACT_SURFACE_SHA256,
        v13.ALPHA_V13_ENROLLMENT_SHA256,
        v13.ALPHA_V13_IDENTITY_SHA256,
    )
    if actual != expected:
        raise FrontierPromotionError(
            "four-square frontier does not match its exact sealed Alpha-v13 slice"
        )


def _parent_layers(
    parent_rows: tuple[FrontierPromotionRow, ...],
) -> tuple[tuple[str, ...], ...]:
    remaining = {row.name for row in parent_rows}
    result: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(
            row.name
            for row in parent_rows
            if row.name in remaining
            and not any(dependency in remaining for dependency in row.dependencies)
        )
        if not ready:
            raise FrontierPromotionError(
                "four-square parent dependencies contain a cycle"
            )
        result.append(ready)
        remaining.difference_update(ready)
    return tuple(result)


def four_square_frontier_plan() -> FourSquareFrontierPlan:
    """Return the exact pinned Lagrange DAG without checking or granting proofs."""

    source = frontier_promotion_plan((FOUR_SQUARE_FRONTIER_ROOT,))
    _validate_exact_source(source)
    layers = frontier_pending_layers(plan=source)
    pending = {row.name for row in source.pending_rows}
    parents = {row.name for row in source.unchecked_parent_rows}
    positions = {
        name: layer
        for layer, names in enumerate(layers)
        for name in names
    }
    obligations = tuple(
        FourSquareFrontierObligation(
            name=row.name,
            source_release=row.source_release,
            statement_sha256=row.statement_sha256,
            pending_dependencies=tuple(
                dependency for dependency in row.dependencies if dependency in pending
            ),
            pending_parent_dependencies=tuple(
                dependency for dependency in row.dependencies if dependency in parents
            ),
            pending_layer=positions[row.name],
        )
        for row in source.pending_rows
    )
    if {item.name for item in obligations} != pending:
        raise FrontierPromotionError("four-square frontier omits a pending obligation")
    return FourSquareFrontierPlan(
        source=source,
        obligations=obligations,
        layers=layers,
        parent_layers=_parent_layers(source.unchecked_parent_rows),
    )


def four_square_hypothetical_ready_rows(
    closed_names: Sequence[str] = (),
    *,
    include_campaign: bool = True,
) -> tuple[str, ...]:
    """Plan readiness *as if* named rows were closed, without claiming proof.

    Strings supplied here are scheduling hypotheses only.  Actual constructors
    independently validate every required ``Proof`` object before replay.
    """

    if isinstance(closed_names, str) or not isinstance(closed_names, (tuple, list)):
        raise FrontierPromotionError(
            "hypothetically closed four-square rows must be a tuple or list"
        )
    if any(type(name) is not str for name in closed_names):
        raise FrontierPromotionError("four-square row names must be exact strings")
    if len(set(closed_names)) != len(closed_names):
        raise FrontierPromotionError("duplicate hypothetically closed four-square row")
    if type(include_campaign) is not bool:
        raise FrontierPromotionError("four-square campaign flag must be a boolean")
    plan = four_square_frontier_plan()
    pending = {item.name for item in plan.obligations}
    completed = set(closed_names)
    unexpected = completed.difference(pending)
    if unexpected:
        raise FrontierPromotionError(
            f"unknown hypothetically closed four-square rows: {sorted(unexpected)!r}"
        )
    return tuple(
        item.name
        for item in plan.obligations
        if item.name not in completed
        and (include_campaign or item.is_parent)
        and set(item.pending_dependencies) <= completed
    )


def _validate_parent_names(
    names: Sequence[str],
    *,
    plan: FourSquareFrontierPlan,
) -> tuple[str, ...]:
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise FrontierPromotionError("four-square parent rows must be a tuple or list")
    if not names:
        raise FrontierPromotionError("four-square parent microbatch cannot be empty")
    if len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise FrontierPromotionError(
            "four-square parent microbatch exceeds its unchanged 16-row limit"
        )
    if any(type(name) is not str for name in names):
        raise FrontierPromotionError("four-square parent row names must be exact strings")
    parents = {item.name for item in plan.parent_obligations}
    unexpected = set(names).difference(parents)
    if unexpected:
        raise FrontierPromotionError(
            f"four-square parent microbatch includes non-parent rows: {sorted(unexpected)!r}"
        )
    return tuple(names)


def construct_four_square_parent_microbatch(
    names: Sequence[str] = FOUR_SQUARE_NON_BETA_PARENT_MICROBATCH,
    *,
    prerequisites: Mapping[str, Proof] | None = None,
) -> tuple[ConstructedFrontierClosedCandidate, ...]:
    """Check actual parent proofs under unchanged 16/125k/25k hard limits."""

    selected = four_square_frontier_plan()
    ordered = _validate_parent_names(names, plan=selected)
    return construct_frontier_closed_microbatch(
        ordered,
        prerequisites=prerequisites,
        plan=selected.source,
    )


def four_square_initial_campaign_batches() -> tuple[FourSquareCampaignMicrobatchPlan, ...]:
    """Partition all 52 initially ready v13 rows into bounded Alpha-ordered batches."""

    plan = four_square_frontier_plan()
    ready = {item.name: item for item in plan.campaign_obligations if not item.pending_dependencies}
    if len(ready) != FOUR_SQUARE_INITIAL_CAMPAIGN_READY_COUNT:
        raise FrontierPromotionError("four-square initial campaign-ready count changed")
    if len(FOUR_SQUARE_INITIAL_CAMPAIGN_LEAF_BUDGETS) != len(ready):
        raise FrontierPromotionError("four-square campaign leaf observations are incomplete")

    observed: dict[str, tuple[int, int, int]] = {}
    indices = {row.name: row.alpha_index for row in plan.source.unchecked_frontier_rows}
    for name, nodes, objects, script_lines in FOUR_SQUARE_INITIAL_CAMPAIGN_LEAF_BUDGETS:
        if name in observed:
            raise FrontierPromotionError("four-square campaign leaf observation is duplicated")
        if name not in ready:
            raise FrontierPromotionError(
                f"four-square campaign row {name!r} is not independently ready"
            )
        if any(type(value) is not int or value < 0 for value in (nodes, objects, script_lines)):
            raise FrontierPromotionError("four-square campaign leaf budget is invalid")
        if len(v13.ALPHA_EDITION.by_name[name].spec.script) != script_lines:
            raise FrontierPromotionError(
                f"four-square campaign row {name!r} has an unsealed script length"
            )
        if (
            nodes >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
            or objects >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        ):
            raise FrontierPromotionError(
                f"four-square campaign row {name!r} exceeds its direct-leaf budget"
            )
        observed[name] = (nodes, objects, script_lines)
    if set(observed) != set(ready):
        raise FrontierPromotionError("four-square campaign-ready rows changed")

    ordered = tuple(
        sorted(
            observed,
            key=lambda name: (
                observed[name][0],
                observed[name][2],
                indices[name],
            ),
        )
    )
    result: list[FourSquareCampaignMicrobatchPlan] = []
    for offset in range(0, len(ordered), MAX_FRONTIER_CLOSURE_MICROBATCH):
        chunk = tuple(
            sorted(
                ordered[offset : offset + MAX_FRONTIER_CLOSURE_MICROBATCH],
                key=indices.__getitem__,
            )
        )
        nodes = sum(observed[name][0] for name in chunk)
        objects = sum(observed[name][1] for name in chunk)
        if (
            nodes >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
            or objects >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        ):
            raise FrontierPromotionError(
                "four-square campaign microbatch direct premises exceed "
                "their immutable envelope"
            )
        result.append(
            FourSquareCampaignMicrobatchPlan(
                index=len(result),
                names=chunk,
                direct_leaf_proof_nodes=nodes,
                direct_leaf_proof_objects=objects,
            )
        )
    if tuple(
        (len(batch.names), batch.direct_leaf_proof_nodes, batch.direct_leaf_proof_objects)
        for batch in result
    ) != FOUR_SQUARE_INITIAL_CAMPAIGN_BATCH_LEAF_BUDGETS:
        raise FrontierPromotionError("four-square campaign batch budget observations changed")
    return tuple(result)


def construct_four_square_campaign_microbatch(
    names: Sequence[str] | None = None,
    *,
    prerequisites: Mapping[str, Proof] | None = None,
) -> tuple[ConstructedFrontierClosedCandidate, ...]:
    """Construct actual v13 campaign proofs under unchanged aggregate limits."""

    selected = four_square_frontier_plan()
    chosen = four_square_initial_campaign_batches()[0].names if names is None else names
    if isinstance(chosen, str) or not isinstance(chosen, (tuple, list)):
        raise FrontierPromotionError("four-square campaign rows must be a tuple or list")
    if not chosen:
        raise FrontierPromotionError("four-square campaign microbatch cannot be empty")
    if len(chosen) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise FrontierPromotionError(
            "four-square campaign microbatch exceeds its unchanged 16-row limit"
        )
    if any(type(name) is not str for name in chosen):
        raise FrontierPromotionError("four-square campaign row names must be exact strings")
    campaigns = {item.name for item in selected.campaign_obligations}
    unexpected = set(chosen).difference(campaigns)
    if unexpected:
        raise FrontierPromotionError(
            f"four-square campaign microbatch includes non-campaign rows: "
            f"{sorted(unexpected)!r}"
        )
    return construct_frontier_closed_microbatch(
        chosen,
        prerequisites=prerequisites,
        plan=selected.source,
    )


def construct_four_square_initial_campaign_certificates(
    batch_indices: Sequence[int] = (0, 1, 2, 3),
    *,
    on_checked: Callable[[FourSquareCampaignMicrobatchReceipt], None] | None = None,
) -> tuple[FourSquareCampaignMicrobatchReceipt, ...]:
    """Check bounded independent campaign batches serially, returning no proofs.

    Each prechecked batch contains at most sixteen rows and must separately
    satisfy the unchanged 125,000-node / 25,000-object aggregate envelope.
    Actual proof objects are dropped before starting the next isolated batch;
    returned diagnostics confer no Alpha/Stable checked-use authority.
    """

    batches = four_square_initial_campaign_batches()
    if isinstance(batch_indices, (str, bytes)) or not isinstance(
        batch_indices, (tuple, list)
    ):
        raise FrontierPromotionError("four-square campaign batch indices must be a tuple or list")
    if not batch_indices:
        raise FrontierPromotionError("four-square campaign batch sequence cannot be empty")
    if any(type(index) is not int for index in batch_indices):
        raise FrontierPromotionError("four-square campaign batch indices must be exact integers")
    if len(set(batch_indices)) != len(batch_indices):
        raise FrontierPromotionError("four-square campaign batch index is duplicated")
    if any(index < 0 or index >= len(batches) for index in batch_indices):
        raise FrontierPromotionError("four-square campaign batch index is outside its exact plan")
    if tuple(batch_indices) != tuple(sorted(batch_indices)):
        raise FrontierPromotionError("four-square campaign batches must be dependency ordered")
    if on_checked is not None and not callable(on_checked):
        raise FrontierPromotionError("four-square campaign progress callback must be callable")

    result: list[FourSquareCampaignMicrobatchReceipt] = []
    for index in batch_indices:
        planned = batches[index]
        candidates = construct_four_square_campaign_microbatch(planned.names)
        diagnostics = tuple(candidate.diagnostics for candidate in candidates)
        actual_nodes = sum(item.proof_nodes for item in diagnostics)
        actual_objects = sum(item.proof_objects for item in diagnostics)
        if (
            actual_nodes >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
            or actual_objects >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        ):
            raise FrontierPromotionError(
                f"four-square campaign batch {index} exceeds its actual "
                "unchanged aggregate envelope"
            )
        receipt = FourSquareCampaignMicrobatchReceipt(
            index=index,
            names=planned.names,
            proof_nodes=actual_nodes,
            proof_objects=actual_objects,
            certificates=diagnostics,
        )
        result.append(receipt)
        del candidates
        if on_checked is not None:
            on_checked(receipt)
    return tuple(result)


def construct_four_square_second_layer_campaign_microbatch() -> tuple[
    tuple[CheckedFrontierPromotionCertificate, ...],
    tuple[ConstructedFrontierClosedCandidate, ...],
]:
    """Recreate ten actual premises, then check sixteen second-layer rows.

    Both dependency-ordered stages are independently bounded by the unchanged
    sixteen-row / 125,000-node / 25,000-object limits.  The second stage
    receives actual predecessor ``Proof`` objects, never diagnostic receipts;
    returned prerequisite diagnostics and sealed Alpha membership confer no
    theorem-use authority.
    """

    if (
        FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_NODE_UPPER_BOUND
        >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        or FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_OBJECT_UPPER_BOUND
        >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    ):
        raise FrontierPromotionError(
            "four-square second-layer direct proof envelope exceeds its immutable cap"
        )
    plan = four_square_frontier_plan()
    prerequisites = construct_frontier_closed_microbatch(
        FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_PREREQUISITES,
        plan=plan.source,
    )
    proof_objects = {item.name: item.certificate for item in prerequisites}
    result = construct_four_square_campaign_microbatch(
        FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES,
        prerequisites=proof_objects,
    )
    return tuple(item.diagnostics for item in prerequisites), result


def construct_four_square_continuation_campaign_microbatch() -> tuple[
    tuple[CheckedFrontierPromotionCertificate, ...],
    tuple[ConstructedFrontierClosedCandidate, ...],
]:
    """Recreate sixteen closed predecessors and check twelve new campaign rows.

    The first stage includes exactly six already proved parent rows and ten
    already proved campaign predecessors. The second stage checks only new
    Alpha-v13 campaign obligations using those actual ``Proof`` objects.
    Both stages independently obey all original microbatch constraints and
    never change existing release evidence.
    """

    if any(
        bound >= limit
        for bound, limit in (
            (
                FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_NODE_UPPER_BOUND,
                MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
            ),
            (
                FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_OBJECT_UPPER_BOUND,
                MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
            ),
            (
                FOUR_SQUARE_CAMPAIGN_CONTINUATION_NODE_UPPER_BOUND,
                MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
            ),
            (
                FOUR_SQUARE_CAMPAIGN_CONTINUATION_OBJECT_UPPER_BOUND,
                MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
            ),
        )
    ):
        raise FrontierPromotionError(
            "four-square continuation direct proof envelope exceeds its immutable cap"
        )
    plan = four_square_frontier_plan()
    prerequisites = construct_frontier_closed_microbatch(
        FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITES,
        plan=plan.source,
    )
    actual_proofs = {item.name: item.certificate for item in prerequisites}
    result = construct_four_square_campaign_microbatch(
        FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES,
        prerequisites=actual_proofs,
    )
    return tuple(item.diagnostics for item in prerequisites), result


def _validate_beta_parent_surface(
    plan: FourSquareFrontierPlan,
) -> dict[str, tuple[str, ...]]:
    obligations = {item.name: item for item in plan.parent_obligations}
    complement = set(obligations).difference(FOUR_SQUARE_NON_BETA_PARENT_NAMES)
    if complement != set(FOUR_SQUARE_BETA_PARENT_NAMES):
        raise FrontierPromotionError(
            "four-square beta parents do not match the exact pending complement"
        )
    indices = {row.name: row.alpha_index for row in plan.source.unchecked_parent_rows}
    actual_order = tuple(indices[name] for name in FOUR_SQUARE_BETA_PARENT_NAMES)
    if actual_order != tuple(sorted(actual_order)):
        raise FrontierPromotionError("four-square beta parent order is not topological")
    expected_hashes = dict(FOUR_SQUARE_BETA_PARENT_STATEMENT_SHA256)
    result: dict[str, tuple[str, ...]] = {}
    for name, stable_nodes, stable_objects, pending in (
        FOUR_SQUARE_BETA_PARENT_STABLE_DIRECT_LEAF_BUDGETS
    ):
        row = obligations.get(name)
        if row is None or row.statement_sha256 != expected_hashes.get(name):
            raise FrontierPromotionError(
                f"four-square beta parent {name!r} has an unsealed exact statement"
            )
        if row.pending_dependencies != pending:
            raise FrontierPromotionError(
                f"four-square beta parent {name!r} has changed unchecked dependencies"
            )
        if (
            stable_nodes >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
            or stable_objects >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        ):
            raise FrontierPromotionError(
                f"four-square beta parent {name!r} exceeds the sealed direct-leaf budget"
            )
        result[name] = pending
    if tuple(result) != FOUR_SQUARE_BETA_PARENT_NAMES:
        raise FrontierPromotionError("four-square beta budget observations changed order")
    return result


def construct_four_square_beta_parent_certificates(
    names: Sequence[str] = FOUR_SQUARE_BETA_PARENT_NAMES,
    *,
    prerequisites: Mapping[str, Proof] | None = None,
    on_checked: Callable[[CheckedFrontierPromotionCertificate], None] | None = None,
) -> tuple[CheckedFrontierPromotionCertificate, ...]:
    """Check exact beta parents as bounded singleton batches in Alpha order.

    Each candidate is an actual unchanged-kernel empty-context proof beneath
    the unchanged 125,000-node / 25,000-object limits.  Predecessor proof
    objects are retained only until their exact dependent existence theorem is
    checked.  Returned diagnostics and optional progress callbacks never
    contain a proof object and never confer checked-use authority.

    This is deliberately a sequence of singleton proof batches: presenting all
    five as one aggregate microbatch would incorrectly exceed its fixed node
    envelope.
    """

    plan = four_square_frontier_plan()
    pending = _validate_beta_parent_surface(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise FrontierPromotionError("four-square beta rows must be a tuple or list")
    if not names:
        raise FrontierPromotionError("four-square beta sequence cannot be empty")
    if any(type(name) is not str for name in names):
        raise FrontierPromotionError("four-square beta row names must be exact strings")
    if len(names) > len(FOUR_SQUARE_BETA_PARENT_NAMES):
        raise FrontierPromotionError("four-square beta sequence exceeds five exact rows")
    if len(set(names)) != len(names):
        raise FrontierPromotionError("four-square beta sequence repeats a parent row")
    unexpected_names = set(names).difference(pending)
    if unexpected_names:
        raise FrontierPromotionError(
            f"four-square beta sequence includes non-beta rows: "
            f"{sorted(unexpected_names)!r}"
        )
    positions = {name: index for index, name in enumerate(FOUR_SQUARE_BETA_PARENT_NAMES)}
    actual_positions = tuple(positions[name] for name in names)
    if actual_positions != tuple(sorted(actual_positions)):
        raise FrontierPromotionError("four-square beta sequence is not dependency ordered")
    if on_checked is not None and not callable(on_checked):
        raise FrontierPromotionError("four-square beta progress callback must be callable")

    provided = {} if prerequisites is None else prerequisites
    if not isinstance(provided, Mapping):
        raise FrontierPromotionError("four-square beta prerequisites must be a mapping")
    selected = set(names)
    required_external = {
        dependency
        for name in names
        for dependency in pending[name]
        if dependency not in selected
    }
    missing = required_external.difference(provided)
    unexpected = set(provided).difference(required_external)
    if missing:
        raise FrontierPromotionError(
            f"missing actual closed four-square beta prerequisites: {sorted(missing)!r}"
        )
    if unexpected:
        raise FrontierPromotionError(
            f"unexpected four-square beta prerequisite proofs: {sorted(unexpected)!r}"
        )

    retained = dict(provided)
    result: list[CheckedFrontierPromotionCertificate] = []
    for index, name in enumerate(names):
        required = {
            dependency: retained[dependency]
            for dependency in pending[name]
        }
        candidate = construct_frontier_closed_candidate(
            name,
            prerequisites=required,
            plan=plan.source,
        )
        result.append(candidate.diagnostics)
        if on_checked is not None:
            on_checked(candidate.diagnostics)
        future_dependencies = {
            dependency
            for later in names[index + 1 :]
            for dependency in pending[later]
        }
        if name in future_dependencies:
            retained[name] = candidate.certificate
        for dependency in tuple(retained):
            if dependency not in future_dependencies:
                retained.pop(dependency)
        del candidate
    return tuple(result)


def construct_four_square_shared_closed_candidate(
    name: str,
    *,
    shared_rows: Sequence[str],
    prerequisites: Mapping[str, Proof] | None = None,
) -> ConstructedFrontierClosedCandidate:
    """Check one ordinary shared-layer proof without changing release evidence."""

    selected = four_square_frontier_plan()
    if name not in {item.name for item in selected.obligations}:
        raise FrontierPromotionError(
            f"four-square shared target {name!r} is not an exact pending obligation"
        )
    return construct_frontier_shared_closed_candidate(
        name,
        shared_rows=shared_rows,
        prerequisites=prerequisites,
        plan=selected.source,
    )


__all__ = [
    "FOUR_SQUARE_BETA_PARENT_CHECKED_DIAGNOSTICS",
    "FOUR_SQUARE_BETA_PARENT_NAMES",
    "FOUR_SQUARE_BETA_PARENT_STABLE_DIRECT_LEAF_BUDGETS",
    "FOUR_SQUARE_BETA_PARENT_STATEMENT_SHA256",
    "FOUR_SQUARE_ESTABLISHED_PARENT_DIAGNOSTICS",
    "FOUR_SQUARE_ESTABLISHED_PARENT_NAMES",
    "FOUR_SQUARE_FRONTIER_ALPHA_CLOSED_COUNT",
    "FOUR_SQUARE_FRONTIER_CAMPAIGN_COUNT",
    "FOUR_SQUARE_FRONTIER_EDGE_COUNT",
    "FOUR_SQUARE_FRONTIER_EXACT_SURFACE_SHA256",
    "FOUR_SQUARE_FRONTIER_ORDERED_NAMES_SHA256",
    "FOUR_SQUARE_FRONTIER_PARENT_COUNT",
    "FOUR_SQUARE_FRONTIER_PENDING_COUNT",
    "FOUR_SQUARE_FRONTIER_ROOT",
    "FOUR_SQUARE_FRONTIER_STABLE_COUNT",
    "FOUR_SQUARE_FRONTIER_TOTAL_COUNT",
    "FOUR_SQUARE_INITIAL_CAMPAIGN_BATCH_LEAF_BUDGETS",
    "FOUR_SQUARE_INITIAL_CAMPAIGN_CHECKED_BATCH_DIAGNOSTICS",
    "FOUR_SQUARE_INITIAL_CAMPAIGN_LEAF_BUDGETS",
    "FOUR_SQUARE_INITIAL_CAMPAIGN_READY_COUNT",
    "FOUR_SQUARE_CAMPAIGN_NEXT_READY_COUNT",
    "FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES",
    "FOUR_SQUARE_CAMPAIGN_CONTINUATION_NODE_UPPER_BOUND",
    "FOUR_SQUARE_CAMPAIGN_CONTINUATION_OBJECT_UPPER_BOUND",
    "FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_DIAGNOSTICS",
    "FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_PREREQUISITE_DIAGNOSTICS",
    "FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITES",
    "FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_NODE_UPPER_BOUND",
    "FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_OBJECT_UPPER_BOUND",
    "FOUR_SQUARE_CAMPAIGN_CONTINUATION_READY_COUNT",
    "FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_NODE_UPPER_BOUND",
    "FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_OBJECT_UPPER_BOUND",
    "FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_CHECKED_DIAGNOSTICS",
    "FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_CHECKED_PREREQUISITE_DIAGNOSTICS",
    "FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES",
    "FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_PREREQUISITES",
    "FOUR_SQUARE_NON_BETA_PARENT_MICROBATCH",
    "FOUR_SQUARE_NON_BETA_MICROBATCH_DIAGNOSTICS",
    "FOUR_SQUARE_NON_BETA_PARENT_NAMES",
    "FourSquareCampaignMicrobatchPlan",
    "FourSquareCampaignMicrobatchReceipt",
    "FourSquareFrontierObligation",
    "FourSquareFrontierPlan",
    "MAX_FRONTIER_CLOSURE_MICROBATCH",
    "MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES",
    "MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS",
    "construct_four_square_beta_parent_certificates",
    "construct_four_square_campaign_microbatch",
    "construct_four_square_continuation_campaign_microbatch",
    "construct_four_square_initial_campaign_certificates",
    "construct_four_square_parent_microbatch",
    "construct_four_square_second_layer_campaign_microbatch",
    "construct_four_square_shared_closed_candidate",
    "four_square_initial_campaign_batches",
    "four_square_frontier_plan",
    "four_square_hypothetical_ready_rows",
]
