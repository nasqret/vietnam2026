"""Terminal-sum aggregation and magnitude cancellation for Gauss--Eisenstein.

This isolated tranche crosses two previously separate gates.  First it lifts
the checked pointwise congruence ``x_i == q_i+m_i+s_i (mod 2)`` to exact
beta-coded Sum endpoints.  Second it proves that the Gauss magnitude prefix
has exactly the same Sum as the canonical half range: the predecessor code
is a bounded injective reindex, aligned because canonical entry ``j`` is
``1+j``.  Additive congruence cancellation then yields

``0 == Q + E (mod 2)``,

where ``Q`` is the Eisenstein quotient sum and ``E`` the Gauss sign count.

Every authoring relation expands to unchanged first-order PA.  No theorem in
this module is registered, admitted, or closure-checked locally.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_scaled_division_candidate import scaled_successor_prefix
from .finite_division_prefix_candidate import division_prefix
from .finite_fold_surface import beta_at, bit_count, sum_relation
from .finite_permutation_theorems import bounded_prefix, injective_prefix
from .finite_product_reindex_support import aligned_prefix
from .finite_sum_pointwise_mod_candidate import _mod_eq
from .gauss_magnitude_permutation_candidate import (
    magnitude_range_prefix,
    predecessor_recode_prefix,
)
from .gauss_signed_prefix_candidate import (
    _beta_at_term,
    half_range,
    not_divides,
    prime,
    signed_half_prefix,
)
from .signed_division_parity_bridge_candidate import _odd


def make_gauss_eisenstein_sum_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build alignment, exact magnitude Sum, aggregation, and cancellation."""

    half = half_range("b", "c", "h", tag="ges_half")
    magnitude_range = magnitude_range_prefix(
        "mb", "mc", "h", "h", tag="ges_magnitude_range"
    )
    magnitude_injective = injective_prefix(
        "mb", "mc", "h", tag="ges_magnitude_injective"
    )
    recode = predecessor_recode_prefix(
        "mb", "mc", "rb", "rc", "h", tag="ges_recode"
    )
    recode_bounded = bounded_prefix("rb", "rc", "h", tag="ges_recode_bounded")
    recode_injective = injective_prefix(
        "rb", "rc", "h", tag="ges_recode_injective"
    )
    alignment = aligned_prefix(
        "rb", "rc", "b", "c", "mb", "mc", "h", tag="ges_alignment"
    )
    half_sum = sum_relation("b", "c", "h", "X", tag="ges_half_sum")
    magnitude_sum = sum_relation("mb", "mc", "h", "M", tag="ges_magnitude_sum")

    proof_map_entry = beta_at("rb", "rc", "i", "j", tag="ges_proof_map")
    proof_magnitude_succ = _beta_at_term(
        "mb",
        "mc",
        "i",
        "S j",
        tag="ges_proof_magnitude_succ",
        variables=("mb", "mc", "i", "j"),
    )
    proof_range_entry = (
        "exists m. "
        f"({beta_at('mb', 'mc', 'i', 'm', tag='ges_proof_range_entry')}) /\\ "
        "((exists g. g + S 0 = m) /\\ exists g. g + m = h)"
    )
    proof_canonical = _beta_at_term(
        "b",
        "c",
        "j",
        "1 + j",
        tag="ges_proof_canonical",
        variables=("b", "c", "j"),
    )

    signed = signed_half_prefix(
        "p", "h", "a", "b", "c", "mb", "mc", "sb", "sc", "h",
        tag="ges_signed",
    )
    prime_p = prime("p", tag="ges_prime")
    nondivisor = not_divides("p", "a", tag="ges_nondivisor")

    odd_a = _odd("a", tag="ges_scale")
    scaled = scaled_successor_prefix("a", "tb", "tc", "h", tag="ges_scaled")
    division = division_prefix(
        "p", "tb", "tc", "qb", "qc", "rb", "rc", "h", tag="ges_division"
    )
    quotient_sum = sum_relation("qb", "qc", "h", "Q", tag="ges_quotient_sum")
    sign_sum = sum_relation("sb", "sc", "h", "E", tag="ges_sign_sum")
    terminal_mod = _mod_eq("2", "X", "Q + M + E", tag="ges_terminal")
    canceled_mod = _mod_eq("2", "0", "Q + E", tag="ges_canceled")
    quotient_sign_mod = _mod_eq("2", "Q", "E", tag="ges_quotient_sign")
    sign_count = bit_count("sb", "sc", "h", "E", tag="ges_sign_count")

    index_bound = "exists g. g + S i = h"
    point_source = beta_at("b", "c", "i", "x", tag="ges_point_source")
    point_quotient = beta_at("qb", "qc", "i", "q", tag="ges_point_quotient")
    point_magnitude = beta_at("mb", "mc", "i", "m", tag="ges_point_magnitude")
    point_sign = beta_at("sb", "sc", "i", "s", tag="ges_point_sign")
    point_mod = _mod_eq("2", "x", "q + m + s", tag="ges_point_mod")
    pointwise = (
        f"forall i x q m s. ({index_bound}) -> ({point_source}) -> "
        f"({point_quotient}) -> ({point_magnitude}) -> ({point_sign}) -> "
        f"({point_mod})"
    )

    common_prefix = (
        f"p = 2 * h + 1 -> ({odd_a}) -> ({half}) -> ({scaled}) -> "
        f"({division}) -> ({signed}) -> ({half_sum}) -> ({quotient_sum}) -> "
        f"({magnitude_sum}) -> ({sign_sum})"
    )

    return (
        spec(
            "beta_magnitude_predecessor_recode_aligned_half_range",
            f"forall b c mb mc rb rc h. ({half}) -> ({magnitude_range}) -> "
            f"({recode}) -> ({alignment})",
            (
                "beta_magnitude_predecessor_recode_reflect",
                "beta_at_unique",
                "add_succ_left",
                "zero_add",
            ),
            (
                "intro b",
                "intro c",
                "intro mb",
                "intro mc",
                "intro rb",
                "intro rc",
                "intro h",
                "intro hhalf",
                "intro hrange",
                "intro hrecode",
                "intro i",
                "intro j",
                "intro v",
                "intro hi",
                "intro hmap",
                "intro hsource",
                f"have hmagnitude_succ : {proof_magnitude_succ}",
                "specialize beta_magnitude_predecessor_recode_reflect mb",
                "specialize beta_magnitude_predecessor_recode_reflect mc",
                "specialize beta_magnitude_predecessor_recode_reflect rb",
                "specialize beta_magnitude_predecessor_recode_reflect rc",
                "specialize beta_magnitude_predecessor_recode_reflect h",
                "specialize beta_magnitude_predecessor_recode_reflect h",
                "specialize beta_magnitude_predecessor_recode_reflect i",
                "specialize beta_magnitude_predecessor_recode_reflect j",
                "apply beta_magnitude_predecessor_recode_reflect",
                "exact hrange",
                "exact hrecode",
                "exact hi",
                "exact hmap",
                f"have hrange_i : {proof_range_entry}",
                "specialize hrange i",
                "apply hrange",
                "exact hi",
                "cases hrange_i",
                "cases hrange_i_witness",
                "cases hrange_i_witness_right",
                "have hmagnitude_eq : x = S j",
                "specialize beta_at_unique mb",
                "specialize beta_at_unique mc",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "specialize beta_at_unique (S j)",
                "apply beta_at_unique",
                "exact hrange_i_witness_left",
                "exact hmagnitude_succ",
                "have hj : exists g. g + S j = h",
                "rewrite <- hmagnitude_eq",
                "exact hrange_i_witness_right_right",
                f"have hcanonical : {proof_canonical}",
                "specialize hhalf j",
                "apply hhalf",
                "exact hj",
                "have hv : v = 1 + j",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique j",
                "specialize beta_at_unique v",
                "specialize beta_at_unique (1 + j)",
                "apply beta_at_unique",
                "exact hsource",
                "exact hcanonical",
                "have hone : 1 + j = S j",
                "specialize add_succ_left 0",
                "specialize add_succ_left j",
                "trans S (0 + j)",
                "exact add_succ_left",
                "congr",
                "specialize zero_add j",
                "exact zero_add",
                "have hv_succ : v = S j",
                "trans 1 + j",
                "exact hv",
                "exact hone",
                "rewrite <- hv_succ at hmagnitude_succ",
                "rewrite <- hv_succ at hmagnitude_succ",
                "exact hmagnitude_succ",
            ),
            "The magnitude-predecessor code aligns positive magnitudes with the canonical half range.",
        ),
        spec(
            "beta_magnitude_sum_permutation_exact",
            "forall b c mb mc rb rc h X M. "
            f"({half}) -> ({magnitude_range}) -> ({magnitude_injective}) -> "
            f"({recode}) -> ({half_sum}) -> ({magnitude_sum}) -> X = M",
            (
                "beta_magnitude_predecessor_recode_bounded",
                "beta_magnitude_predecessor_recode_injective",
                "beta_magnitude_predecessor_recode_aligned_half_range",
                "beta_sum_permutation_invariant",
            ),
            (
                "intro b",
                "intro c",
                "intro mb",
                "intro mc",
                "intro rb",
                "intro rc",
                "intro h",
                "intro X",
                "intro M",
                "intro hhalf",
                "intro hrange",
                "intro hinjective",
                "intro hrecode",
                "intro hhalf_sum",
                "intro hmagnitude_sum",
                f"have hbounded : {recode_bounded}",
                "specialize beta_magnitude_predecessor_recode_bounded mb",
                "specialize beta_magnitude_predecessor_recode_bounded mc",
                "specialize beta_magnitude_predecessor_recode_bounded rb",
                "specialize beta_magnitude_predecessor_recode_bounded rc",
                "specialize beta_magnitude_predecessor_recode_bounded h",
                "apply beta_magnitude_predecessor_recode_bounded",
                "exact hrange",
                "exact hrecode",
                f"have hrecode_injective : {recode_injective}",
                "specialize beta_magnitude_predecessor_recode_injective mb",
                "specialize beta_magnitude_predecessor_recode_injective mc",
                "specialize beta_magnitude_predecessor_recode_injective rb",
                "specialize beta_magnitude_predecessor_recode_injective rc",
                "specialize beta_magnitude_predecessor_recode_injective h",
                "apply beta_magnitude_predecessor_recode_injective",
                "exact hrange",
                "exact hinjective",
                "exact hrecode",
                f"have haligned : {alignment}",
                "specialize beta_magnitude_predecessor_recode_aligned_half_range b",
                "specialize beta_magnitude_predecessor_recode_aligned_half_range c",
                "specialize beta_magnitude_predecessor_recode_aligned_half_range mb",
                "specialize beta_magnitude_predecessor_recode_aligned_half_range mc",
                "specialize beta_magnitude_predecessor_recode_aligned_half_range rb",
                "specialize beta_magnitude_predecessor_recode_aligned_half_range rc",
                "specialize beta_magnitude_predecessor_recode_aligned_half_range h",
                "apply beta_magnitude_predecessor_recode_aligned_half_range",
                "exact hhalf",
                "exact hrange",
                "exact hrecode",
                "specialize beta_sum_permutation_invariant h",
                "specialize beta_sum_permutation_invariant rb",
                "specialize beta_sum_permutation_invariant rc",
                "specialize beta_sum_permutation_invariant b",
                "specialize beta_sum_permutation_invariant c",
                "specialize beta_sum_permutation_invariant mb",
                "specialize beta_sum_permutation_invariant mc",
                "specialize beta_sum_permutation_invariant X",
                "specialize beta_sum_permutation_invariant M",
                "apply beta_sum_permutation_invariant",
                "exact hbounded",
                "exact hrecode_injective",
                "exact haligned",
                "exact hhalf_sum",
                "exact hmagnitude_sum",
            ),
            "A positive magnitude permutation has exactly the canonical half-range Sum.",
        ),
        spec(
            "gauss_signed_half_magnitude_sum_equals_half_sum",
            "forall p h a b c mb mc sb sc X M. p = 2 * h + 1 -> "
            f"({prime_p}) -> ({nondivisor}) -> ({half}) -> ({signed}) -> "
            f"({half_sum}) -> ({magnitude_sum}) -> X = M",
            (
                "gauss_signed_half_magnitude_range",
                "gauss_signed_half_magnitude_injective",
                "gauss_signed_half_predecessor_recode_exists",
                "beta_magnitude_sum_permutation_exact",
            ),
            (
                "intro p", "intro h", "intro a", "intro b", "intro c",
                "intro mb", "intro mc", "intro sb", "intro sc",
                "intro X", "intro M", "intro hp", "intro hprime",
                "intro hnondiv", "intro hhalf", "intro hsigned",
                "intro hhalf_sum", "intro hmagnitude_sum",
                f"have hrange : {magnitude_range}",
                "specialize gauss_signed_half_magnitude_range p",
                "specialize gauss_signed_half_magnitude_range h",
                "specialize gauss_signed_half_magnitude_range a",
                "specialize gauss_signed_half_magnitude_range b",
                "specialize gauss_signed_half_magnitude_range c",
                "specialize gauss_signed_half_magnitude_range mb",
                "specialize gauss_signed_half_magnitude_range mc",
                "specialize gauss_signed_half_magnitude_range sb",
                "specialize gauss_signed_half_magnitude_range sc",
                "specialize gauss_signed_half_magnitude_range h",
                "apply gauss_signed_half_magnitude_range",
                "exact hsigned",
                f"have hinjective : {magnitude_injective}",
                "specialize gauss_signed_half_magnitude_injective p",
                "specialize gauss_signed_half_magnitude_injective h",
                "specialize gauss_signed_half_magnitude_injective a",
                "specialize gauss_signed_half_magnitude_injective b",
                "specialize gauss_signed_half_magnitude_injective c",
                "specialize gauss_signed_half_magnitude_injective mb",
                "specialize gauss_signed_half_magnitude_injective mc",
                "specialize gauss_signed_half_magnitude_injective sb",
                "specialize gauss_signed_half_magnitude_injective sc",
                "apply gauss_signed_half_magnitude_injective",
                "exact hp", "exact hprime", "exact hnondiv",
                "exact hhalf", "exact hsigned",
                "have hrecode_exists : exists rb rc. "
                f"({predecessor_recode_prefix('mb', 'mc', 'rb', 'rc', 'h', tag='ges_recode_exists')})",
                "specialize gauss_signed_half_predecessor_recode_exists p",
                "specialize gauss_signed_half_predecessor_recode_exists h",
                "specialize gauss_signed_half_predecessor_recode_exists a",
                "specialize gauss_signed_half_predecessor_recode_exists b",
                "specialize gauss_signed_half_predecessor_recode_exists c",
                "specialize gauss_signed_half_predecessor_recode_exists mb",
                "specialize gauss_signed_half_predecessor_recode_exists mc",
                "specialize gauss_signed_half_predecessor_recode_exists sb",
                "specialize gauss_signed_half_predecessor_recode_exists sc",
                "apply gauss_signed_half_predecessor_recode_exists",
                "exact hsigned",
                "cases hrecode_exists",
                "cases hrecode_exists_witness",
                "specialize beta_magnitude_sum_permutation_exact b",
                "specialize beta_magnitude_sum_permutation_exact c",
                "specialize beta_magnitude_sum_permutation_exact mb",
                "specialize beta_magnitude_sum_permutation_exact mc",
                "specialize beta_magnitude_sum_permutation_exact x",
                "specialize beta_magnitude_sum_permutation_exact x1",
                "specialize beta_magnitude_sum_permutation_exact h",
                "specialize beta_magnitude_sum_permutation_exact X",
                "specialize beta_magnitude_sum_permutation_exact M",
                "apply beta_magnitude_sum_permutation_exact",
                "exact hhalf", "exact hrange", "exact hinjective",
                "exact hrecode_exists_witness_witness",
                "exact hhalf_sum", "exact hmagnitude_sum",
            ),
            "Gauss signed-half data makes the magnitude Sum equal the canonical half Sum.",
        ),
        spec(
            "gauss_eisenstein_terminal_sums_mod_two",
            "forall p h a b c tb tc qb qc rb rc mb mc sb sc X Q M E. "
            f"{common_prefix} -> ({terminal_mod})",
            (
                "gauss_eisenstein_prefix_pointwise_mod_two",
                "beta_sum_pointwise_mod_three_add",
            ),
            (
                "intro p", "intro h", "intro a", "intro b", "intro c",
                "intro tb", "intro tc", "intro qb", "intro qc", "intro rb",
                "intro rc", "intro mb", "intro mc", "intro sb", "intro sc",
                "intro X", "intro Q", "intro M", "intro E",
                "intro hp", "intro ha", "intro hhalf", "intro hscaled",
                "intro hdivision", "intro hsigned", "intro hhalf_sum",
                "intro hquotient_sum", "intro hmagnitude_sum", "intro hsign_sum",
                f"have hpointwise : {pointwise}",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two p",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two h",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two a",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two b",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two c",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two tb",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two tc",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two qb",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two qc",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two rb",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two rc",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two mb",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two mc",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two sb",
                "specialize gauss_eisenstein_prefix_pointwise_mod_two sc",
                "apply gauss_eisenstein_prefix_pointwise_mod_two",
                "exact hp", "exact ha", "exact hhalf", "exact hscaled",
                "exact hdivision", "exact hsigned",
                "specialize beta_sum_pointwise_mod_three_add 2",
                "specialize beta_sum_pointwise_mod_three_add b",
                "specialize beta_sum_pointwise_mod_three_add c",
                "specialize beta_sum_pointwise_mod_three_add qb",
                "specialize beta_sum_pointwise_mod_three_add qc",
                "specialize beta_sum_pointwise_mod_three_add mb",
                "specialize beta_sum_pointwise_mod_three_add mc",
                "specialize beta_sum_pointwise_mod_three_add sb",
                "specialize beta_sum_pointwise_mod_three_add sc",
                "specialize beta_sum_pointwise_mod_three_add h",
                "specialize beta_sum_pointwise_mod_three_add X",
                "specialize beta_sum_pointwise_mod_three_add Q",
                "specialize beta_sum_pointwise_mod_three_add M",
                "specialize beta_sum_pointwise_mod_three_add E",
                "apply beta_sum_pointwise_mod_three_add",
                "exact hhalf_sum", "exact hquotient_sum", "exact hmagnitude_sum",
                "exact hsign_sum", "exact hpointwise",
            ),
            "The pointwise Gauss--Eisenstein congruence aggregates to exact terminal Sums.",
        ),
        spec(
            "gauss_eisenstein_terminal_cancel_magnitude_mod_two",
            "forall p h a b c tb tc qb qc rb rc mb mc sb sc X Q M E. "
            f"({prime_p}) -> ({nondivisor}) -> {common_prefix} -> ({canceled_mod})",
            (
                "gauss_eisenstein_terminal_sums_mod_two",
                "gauss_signed_half_magnitude_sum_equals_half_sum",
                "mod_two_cancel_middle",
            ),
            (
                "intro p", "intro h", "intro a", "intro b", "intro c",
                "intro tb", "intro tc", "intro qb", "intro qc", "intro rb",
                "intro rc", "intro mb", "intro mc", "intro sb", "intro sc",
                "intro X", "intro Q", "intro M", "intro E",
                "intro hprime", "intro hnondiv", "intro hp", "intro ha",
                "intro hhalf", "intro hscaled", "intro hdivision",
                "intro hsigned", "intro hhalf_sum", "intro hquotient_sum",
                "intro hmagnitude_sum", "intro hsign_sum",
                f"have hterminal : {terminal_mod}",
                "specialize gauss_eisenstein_terminal_sums_mod_two p",
                "specialize gauss_eisenstein_terminal_sums_mod_two h",
                "specialize gauss_eisenstein_terminal_sums_mod_two a",
                "specialize gauss_eisenstein_terminal_sums_mod_two b",
                "specialize gauss_eisenstein_terminal_sums_mod_two c",
                "specialize gauss_eisenstein_terminal_sums_mod_two tb",
                "specialize gauss_eisenstein_terminal_sums_mod_two tc",
                "specialize gauss_eisenstein_terminal_sums_mod_two qb",
                "specialize gauss_eisenstein_terminal_sums_mod_two qc",
                "specialize gauss_eisenstein_terminal_sums_mod_two rb",
                "specialize gauss_eisenstein_terminal_sums_mod_two rc",
                "specialize gauss_eisenstein_terminal_sums_mod_two mb",
                "specialize gauss_eisenstein_terminal_sums_mod_two mc",
                "specialize gauss_eisenstein_terminal_sums_mod_two sb",
                "specialize gauss_eisenstein_terminal_sums_mod_two sc",
                "specialize gauss_eisenstein_terminal_sums_mod_two X",
                "specialize gauss_eisenstein_terminal_sums_mod_two Q",
                "specialize gauss_eisenstein_terminal_sums_mod_two M",
                "specialize gauss_eisenstein_terminal_sums_mod_two E",
                "apply gauss_eisenstein_terminal_sums_mod_two",
                "exact hp", "exact ha", "exact hhalf", "exact hscaled",
                "exact hdivision", "exact hsigned", "exact hhalf_sum",
                "exact hquotient_sum", "exact hmagnitude_sum", "exact hsign_sum",
                "have hmagnitude_exact : X = M",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum p",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum h",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum a",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum b",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum c",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum mb",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum mc",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum sb",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum sc",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum X",
                "specialize gauss_signed_half_magnitude_sum_equals_half_sum M",
                "apply gauss_signed_half_magnitude_sum_equals_half_sum",
                "exact hp", "exact hprime", "exact hnondiv", "exact hhalf",
                "exact hsigned", "exact hhalf_sum", "exact hmagnitude_sum",
                "rewrite <- hmagnitude_exact at hterminal",
                "specialize mod_two_cancel_middle X",
                "specialize mod_two_cancel_middle Q",
                "specialize mod_two_cancel_middle E",
                "apply mod_two_cancel_middle",
                "exact hterminal",
            ),
            "Cancel the exact Gauss magnitude Sum: 0 == quotient Sum + sign Sum modulo two.",
        ),
        spec(
            "gauss_eisenstein_sign_count_mod_quotient_sum",
            "forall p h a b c tb tc qb qc rb rc mb mc sb sc Q E. "
            f"p = 2 * h + 1 -> ({odd_a}) -> ({prime_p}) -> ({nondivisor}) -> "
            f"({half}) -> ({scaled}) -> ({division}) -> ({signed}) -> "
            f"({sign_count}) -> ({quotient_sum}) -> ({quotient_sign_mod})",
            (
                "beta_sum_exists",
                "gauss_eisenstein_terminal_cancel_magnitude_mod_two",
                "mod_two_zero_sum_to_congruent",
            ),
            (
                "intro p", "intro h", "intro a", "intro b", "intro c",
                "intro tb", "intro tc", "intro qb", "intro qc", "intro rb",
                "intro rc", "intro mb", "intro mc", "intro sb", "intro sc",
                "intro Q", "intro E", "intro hp", "intro ha",
                "intro hprime", "intro hnondiv", "intro hhalf",
                "intro hscaled", "intro hdivision", "intro hsigned",
                "intro hsign_count", "intro hquotient_sum",
                "cases hsign_count",
                "have hhalf_sum_exists : exists X. "
                f"({sum_relation('b', 'c', 'h', 'X', tag='ges_orientation_half_sum')})",
                "specialize beta_sum_exists b",
                "specialize beta_sum_exists c",
                "specialize beta_sum_exists h",
                "exact beta_sum_exists",
                "cases hhalf_sum_exists",
                "have hmagnitude_sum_exists : exists M. "
                f"({sum_relation('mb', 'mc', 'h', 'M', tag='ges_orientation_magnitude_sum')})",
                "specialize beta_sum_exists mb",
                "specialize beta_sum_exists mc",
                "specialize beta_sum_exists h",
                "exact beta_sum_exists",
                "cases hmagnitude_sum_exists",
                f"have hcanceled : {_mod_eq('2', '0', 'Q + E', tag='ges_orientation_canceled')}",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two p",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two h",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two a",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two b",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two c",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two tb",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two tc",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two qb",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two qc",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two rb",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two rc",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two mb",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two mc",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two sb",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two sc",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two x",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two Q",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two x1",
                "specialize gauss_eisenstein_terminal_cancel_magnitude_mod_two E",
                "apply gauss_eisenstein_terminal_cancel_magnitude_mod_two",
                "exact hprime", "exact hnondiv", "exact hp", "exact ha",
                "exact hhalf", "exact hscaled", "exact hdivision",
                "exact hsigned", "exact hhalf_sum_exists_witness",
                "exact hquotient_sum", "exact hmagnitude_sum_exists_witness",
                "exact hsign_count_left",
                "specialize mod_two_zero_sum_to_congruent Q",
                "specialize mod_two_zero_sum_to_congruent E",
                "apply mod_two_zero_sum_to_congruent",
                "exact hcanceled",
            ),
            "The Gauss sign BitCount is congruent modulo two to its orientation's quotient Sum.",
        ),
    )


__all__ = ["make_gauss_eisenstein_sum_candidate_theorems"]
