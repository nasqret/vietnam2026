"""Constructive prime-valuation predecessors for canonical factor pairing.

Every surface abbreviation expands into the unchanged first-order Peano
language.  These isolated dependency-curried candidates construct the complete
two-square iff criterion without conferring Alpha/Stable authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_central_binom_valuation_candidate import _power_valuation_term
from .bertrand_power_valuation_candidate import (
    _power_divides_terms,
    power_divides,
    power_valuation,
)
from .fermat_residue_map_candidate import prime
from .fermat_two_squares_classification_candidate import _four_three, _two_square
from .fermat_two_squares_collision_norm_candidate import _multiple
from .fermat_two_squares_factor_fold_candidate import all_prime_factor_prefix
from .finite_fold_surface import _beta_at_term, _product_relation_term, beta_at


PRIME_DIVISOR_OF_PRIME_FORCES_EQUALITY = "prime_divisor_of_prime_forces_equality"
DISTINCT_PRIME_POWER_VALUATION_ZERO = "distinct_prime_power_valuation_zero"
POSITIVE_DOUBLE_AT_LEAST_TWO = "positive_double_at_least_two"
EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR = (
    "even_positive_prime_valuation_has_square_divisor"
)
PRIME_SQUARE_DIVISIBILITY_FORCES_SUFFIX_PRIME_DIVISOR = (
    "prime_square_divisibility_forces_suffix_prime_divisor"
)
BETA_SORTED_PRIME_PREFIX_DIVISOR_EQUALS_BOUNDED_LAST = (
    "beta_sorted_prime_prefix_divisor_equals_bounded_last"
)
EVEN_VALUATION_SORTED_TERMINAL_PRIME_HAS_EQUAL_PREDECESSOR = (
    "even_valuation_sorted_terminal_prime_has_equal_predecessor"
)
PAIRING_DOUBLE_EQUALS_TWO_MUL = "pairing_double_equals_two_mul"
EVEN_DOUBLE_SUM_REFLECTS_EVEN_TAIL = "even_double_sum_reflects_even_tail"
DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX = (
    "distinct_prime_factor_even_valuation_reflects_prefix"
)
SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR = (
    "square_factor_even_valuation_reflects_cofactor"
)
THREE_MOD_FOUR_NUMBER_NOT_EQUAL_REPRESENTED = (
    "three_mod_four_number_not_equal_represented"
)
ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_REPRESENTED_PRIME = (
    "all_bad_prime_even_valuations_strip_represented_prime"
)
ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_SQUARE_FACTOR = (
    "all_bad_prime_even_valuations_strip_square_factor"
)
ALL_BAD_PRIME_EVEN_VALUATION_VALUE_EQ_TRANSPORT = (
    "all_bad_prime_even_valuation_value_eq_transport"
)
PRIME_MOD_FOUR_GOOD_OR_THREE = "prime_mod_four_good_or_three"
ALL_BAD_PRIME_EVEN_TWO_SQUARE_SUFFICIENCY_BOUNDED = (
    "all_bad_prime_even_two_square_sufficiency_bounded"
)
POSITIVE_NUMBER_WITH_EVEN_BAD_PRIME_VALUATIONS_IS_TWO_SQUARE = (
    "positive_number_with_even_bad_prime_valuations_is_two_square"
)
NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS = (
    "nonzero_two_square_iff_even_three_mod_four_prime_valuations"
)
TWO_SQUARE_IFF_ZERO_OR_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS = (
    "two_square_iff_zero_or_even_three_mod_four_prime_valuations"
)


def _sorted_prefix(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand canonical adjacent-sortedness with hygienic decoded entries."""

    index = f"ftsp_index_{tag}"
    left = f"ftsp_left_{tag}"
    right = f"ftsp_right_{tag}"
    bound = f"exists ftsp_bound_{tag}. ftsp_bound_{tag} + S (S {index}) = ({length})"
    avoid = (code, scale, index, left, right)
    first = _beta_at_term(code, scale, index, left, tag=f"ftsp_{tag}_left", avoid=avoid)
    second = _beta_at_term(
        code, scale, f"S {index}", right, tag=f"ftsp_{tag}_right", avoid=avoid
    )
    order = f"exists ftsp_order_{tag}. ftsp_order_{tag} + {left} = {right}"
    return f"forall {index}. ({bound}) -> exists {left} {right}. (({first}) /\\ (({second}) /\\ ({order})))"


def _product(code: str, scale: str, length: str, result: str, *, tag: str) -> str:
    return _product_relation_term(
        code,
        scale,
        length,
        result,
        tag=f"ftsp_{tag}",
        avoid=(code, scale, result),
    )


def _all_bad_prime_valuations_even(value: str, *, tag: str) -> str:
    """Expand constructive even valuation at every three-modulo-four prime."""

    bad_prime = f"ftsp_bad_prime_{tag}"
    exponent = f"ftsp_bad_exponent_{tag}"
    half = f"ftsp_bad_half_{tag}"
    primality = prime(bad_prime, tag=f"ftsp_{tag}_prime")
    residue = _four_three(bad_prime, tag=f"ftsp_{tag}_three")
    valuation = _power_valuation_term(
        bad_prime, value, exponent, tag=f"ftsp_{tag}_valuation"
    )
    return (
        f"forall {bad_prime} {exponent}. ({primality}) -> ({residue}) -> "
        f"({valuation}) -> exists {half}. {exponent} = {half} + {half}"
    )


def make_fermat_two_squares_pairing_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build bounded prime-divisor and even-valuation pairing prerequisites."""

    prime_p = prime("p", tag="ftsp_p")
    prime_q = prime("q", tag="ftsp_q")
    prime_divides_prime = _multiple("p", "q", tag="ftsp_prime_divides_prime")
    distinct_valuation = power_valuation("p", "q", "e", tag="ftsp_distinct")
    source_valuation = power_valuation("p", "n", "e", tag="ftsp_source")
    prime_divides_value = _multiple("p", "n", tag="ftsp_value")
    square_divides_value = _multiple("p * p", "n", tag="ftsp_square")
    selected_power = power_divides("p", "e", "n", tag="ftsp_selected")
    square_power = _power_divides_terms("p", "2", "n", tag="ftsp_second")
    suffix_divides = _multiple("p", "r", tag="ftsp_suffix")

    prefix_all_prime = all_prime_factor_prefix("b", "c", "S l", tag="ftsp_prefix")
    prefix_sorted = _sorted_prefix("b", "c", "S l", tag="prefix")
    prefix_product = _product("b", "c", "S l", "r", tag="prefix")
    prefix_last = beta_at("b", "c", "l", "q", tag="ftsp_prefix_last")
    prefix_member = beta_at("b", "c", "i", "p", tag="ftsp_prefix_member")
    upper_order = "exists ftsp_upper_gap. ftsp_upper_gap + q = p"

    full_all_prime = all_prime_factor_prefix("b", "c", "S (S l)", tag="ftsp_full")
    full_sorted = _sorted_prefix("b", "c", "S (S l)", tag="full")
    full_product = _product("b", "c", "S (S l)", "n", tag="full")
    terminal_entry = _beta_at_term(
        "b", "c", "S l", "p", tag="ftsp_terminal", avoid=("b", "c", "l", "p")
    )
    predecessor_result = beta_at("b", "c", "l", "p", tag="ftsp_predecessor")
    decomposition_entry = _beta_at_term(
        "b", "c", "S l", "t", tag="ftsp_decomposition_entry", avoid=("b", "c", "l", "t")
    )
    decomposition_product = _product("b", "c", "S l", "r", tag="decomposition")
    decomposition = (
        f"exists t r. (({decomposition_entry}) /\\ "
        f"(({decomposition_product}) /\\ n = r * t))"
    )
    sorted_left = beta_at("b", "c", "l", "u", tag="ftsp_sorted_left")
    sorted_right = _beta_at_term(
        "b", "c", "S l", "v", tag="ftsp_sorted_right", avoid=("b", "c", "l", "v")
    )
    last_sorted_pair = (
        f"exists u v. (({sorted_left}) /\\ "
        f"(({sorted_right}) /\\ (exists k. k + u = v)))"
    )
    reflected_value = power_valuation("p", "n", "e", tag="ftsp_reflected_value")
    reflected_prime = power_valuation("p", "q", "f", tag="ftsp_reflected_prime")
    reflected_product = _power_valuation_term(
        "p", "n * q", "g", tag="ftsp_reflected_product"
    )
    square_factor_valuation = power_valuation(
        "p", "z", "e", tag="ftsp_square_factor"
    )
    square_cofactor_valuation = power_valuation(
        "p", "n", "f", tag="ftsp_square_cofactor"
    )
    square_product_valuation = _power_valuation_term(
        "p", "(z * z) * n", "g", tag="ftsp_square_product"
    )
    represented_q = _two_square("q", tag="ftsp_good_prime")
    bad_p = _four_three("p", tag="ftsp_bad_distinct")
    parity_source_value = _all_bad_prime_valuations_even("n", tag="parity_source")
    parity_good_product = _all_bad_prime_valuations_even(
        "n * q", tag="parity_good_product"
    )
    parity_square_product = _all_bad_prime_valuations_even(
        "n * (z * z)", tag="parity_square_product"
    )
    parity_transport_source = _all_bad_prime_valuations_even(
        "a", tag="transport_source"
    )
    parity_transport_target = _all_bad_prime_valuations_even(
        "b", tag="transport_target"
    )
    value_parity = _all_bad_prime_valuations_even("n", tag="value")
    value_representation = _two_square("n", tag="ftsp_value_result")
    induction_bound = "exists ftsp_induction_gap. ftsp_induction_gap + n = B"

    return (
        spec(
            PRIME_DIVISOR_OF_PRIME_FORCES_EQUALITY,
            f"forall p q. ({prime_p}) -> ({prime_q}) -> "
            f"({prime_divides_prime}) -> p = q",
            ("prime_divisor_eq_one_or_self",),
            (
                "intro p",
                "intro q",
                "intro hp",
                "intro hq",
                "intro hdivides",
                "have hcases : p = 1 \\/ q = p",
                "specialize prime_divisor_eq_one_or_self q",
                "specialize prime_divisor_eq_one_or_self p",
                "apply prime_divisor_eq_one_or_self",
                "exact hq",
                "exact hdivides",
                "cases hcases",
                "exfalso",
                "cases hp",
                "apply hp_left",
                "exact hcases_left",
                "symm",
                "exact hcases_right",
            ),
            "A prime can divide another prime only when both prime values agree.",
        ),
        spec(
            DISTINCT_PRIME_POWER_VALUATION_ZERO,
            f"forall p q e. ({prime_p}) -> ({prime_q}) -> "
            f"~(p = q) -> ({distinct_valuation}) -> e = 0",
            (
                "eq_decidable",
                "power_valuation_nonzero_exponent_divides_base",
                PRIME_DIVISOR_OF_PRIME_FORCES_EQUALITY,
            ),
            (
                "intro p",
                "intro q",
                "intro e",
                "intro hp",
                "intro hq",
                "intro hdistinct",
                "intro hvaluation",
                "specialize eq_decidable e",
                "specialize eq_decidable 0",
                "cases eq_decidable",
                "exact eq_decidable_left",
                "exfalso",
                f"have hdivides : {prime_divides_prime}",
                "specialize power_valuation_nonzero_exponent_divides_base p",
                "specialize power_valuation_nonzero_exponent_divides_base q",
                "specialize power_valuation_nonzero_exponent_divides_base e",
                "apply power_valuation_nonzero_exponent_divides_base",
                "exact hvaluation",
                "exact eq_decidable_right",
                "apply hdistinct",
                "specialize prime_divisor_of_prime_forces_equality p",
                "specialize prime_divisor_of_prime_forces_equality q",
                "apply prime_divisor_of_prime_forces_equality",
                "exact hp",
                "exact hq",
                "exact hdivides",
            ),
            "The prime-power valuation of a distinct prime factor is exactly zero.",
        ),
        spec(
            POSITIVE_DOUBLE_AT_LEAST_TWO,
            "forall h. ~(h = 0) -> exists k. k + 2 = h + h",
            ("nonzero_is_succ", "add_succ_left", "add_assoc", "add_comm"),
            (
                "intro h",
                "intro hnonzero",
                "specialize nonzero_is_succ h",
                "have hsuccessor : exists k. h = S k",
                "apply nonzero_is_succ",
                "exact hnonzero",
                "cases hsuccessor",
                "exists x + x",
                "rewrite hsuccessor_witness",
                "rewrite hsuccessor_witness",
                "simp [add_succ_left, add_assoc, add_comm]",
            ),
            "The double of a positive natural has an explicit witness "
            "for being at least two.",
        ),
        spec(
            EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR,
            f"forall p n e h. ({prime_p}) -> ~(n = 0) -> "
            f"({source_valuation}) -> ({prime_divides_value}) -> "
            f"e = h + h -> ({square_divides_value})",
            (
                "prime_divisor_power_valuation_nonzero",
                POSITIVE_DOUBLE_AT_LEAST_TWO,
                "power_valuation_power_divides",
                "power_divides_exponent_antitone",
                "pow_two",
            ),
            (
                "intro p",
                "intro n",
                "intro e",
                "intro h",
                "intro hprime",
                "intro hnonzero",
                "intro hvaluation",
                "intro hdivides",
                "intro heven",
                "have hexponent : ~(e = 0)",
                "specialize prime_divisor_power_valuation_nonzero p",
                "specialize prime_divisor_power_valuation_nonzero n",
                "specialize prime_divisor_power_valuation_nonzero e",
                "intro hezero",
                "apply prime_divisor_power_valuation_nonzero",
                "exact hprime",
                "exact hnonzero",
                "exact hvaluation",
                "exact hdivides",
                "exact hezero",
                "have hhalf : ~(h = 0)",
                "intro hhalf_zero",
                "apply hexponent",
                "trans h + h",
                "exact heven",
                "rewrite hhalf_zero",
                "rewrite hhalf_zero",
                "simp",
                "have hlower : exists k. k + 2 = e",
                "specialize positive_double_at_least_two h",
                "have hdoubled : exists k. k + 2 = h + h",
                "apply positive_double_at_least_two",
                "exact hhalf",
                "rewrite <- heven at hdoubled",
                "exact hdoubled",
                f"have hselected : {selected_power}",
                "specialize power_valuation_power_divides p",
                "specialize power_valuation_power_divides n",
                "specialize power_valuation_power_divides e",
                "apply power_valuation_power_divides",
                "exact hvaluation",
                f"have hsquare : {square_power}",
                "specialize power_divides_exponent_antitone p",
                "specialize power_divides_exponent_antitone 2",
                "specialize power_divides_exponent_antitone e",
                "specialize power_divides_exponent_antitone n",
                "apply power_divides_exponent_antitone",
                "exact hlower",
                "exact hselected",
                "cases hsquare",
                "cases hsquare_witness",
                "cases hsquare_witness_right",
                "have hpower_value : x = p * p",
                "specialize pow_two p",
                "specialize pow_two 2",
                "specialize pow_two x",
                "apply pow_two",
                "refl",
                "exact hsquare_witness_left",
                "exists x1",
                "trans x * x1",
                "exact hsquare_witness_right_witness",
                "rewrite hpower_value",
                "refl",
            ),
            "A positive even valuation at a prime yields an actual "
            "constructive divisor witness for the prime square.",
        ),
        spec(
            PRIME_SQUARE_DIVISIBILITY_FORCES_SUFFIX_PRIME_DIVISOR,
            f"forall p r n. ({prime_p}) -> n = r * p -> "
            f"({square_divides_value}) -> ({suffix_divides})",
            ("prime_nonzero", "mul_left_cancel_nonzero", "mul_comm", "mul_assoc"),
            (
                "intro p",
                "intro r",
                "intro n",
                "intro hprime",
                "intro hproduct",
                "intro hsquare",
                "cases hsquare",
                "have hpnonzero : ~(p = 0)",
                "specialize prime_nonzero p",
                "intro hpzero",
                "apply prime_nonzero",
                "exact hprime",
                "exact hpzero",
                "have hbalance : p * r = p * (p * x)",
                "trans r * p",
                "apply mul_comm",
                "trans n",
                "symm",
                "exact hproduct",
                "trans (p * p) * x",
                "exact hsquare_witness",
                "apply mul_assoc",
                "exists x",
                "specialize mul_left_cancel_nonzero p",
                "specialize mul_left_cancel_nonzero r",
                "specialize mul_left_cancel_nonzero (p * x)",
                "apply mul_left_cancel_nonzero",
                "exact hpnonzero",
                "exact hbalance",
            ),
            "If a prime square divides a product with one terminal prime "
            "factor, that same prime divides the remaining prefix product.",
        ),
        spec(
            BETA_SORTED_PRIME_PREFIX_DIVISOR_EQUALS_BOUNDED_LAST,
            f"forall b c l r p q. ({prime_p}) -> ({prefix_all_prime}) -> "
            f"({prefix_sorted}) -> ({prefix_product}) -> ({prefix_last}) -> "
            f"({suffix_divides}) -> ({upper_order}) -> q = p",
            (
                "beta_prime_divisor_product_member",
                "beta_sorted_factor_le_last",
                "le_antisymm",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro r",
                "intro p",
                "intro q",
                "intro hprime",
                "intro hallprime",
                "intro hsorted",
                "intro hproduct",
                "intro hlast",
                "intro hdivides",
                "intro hupper",
                f"have hmember : exists i. "
                f"((exists k. k + S i = S l) /\\ ({prefix_member}))",
                "specialize beta_prime_divisor_product_member b",
                "specialize beta_prime_divisor_product_member c",
                "specialize beta_prime_divisor_product_member (S l)",
                "specialize beta_prime_divisor_product_member r",
                "specialize beta_prime_divisor_product_member p",
                "apply beta_prime_divisor_product_member",
                "exact hprime",
                "exact hallprime",
                "exact hproduct",
                "exact hdivides",
                "cases hmember",
                "cases hmember_witness",
                "have hlower : exists k. k + p = q",
                "specialize beta_sorted_factor_le_last b",
                "specialize beta_sorted_factor_le_last c",
                "specialize beta_sorted_factor_le_last l",
                "specialize beta_sorted_factor_le_last x",
                "specialize beta_sorted_factor_le_last p",
                "specialize beta_sorted_factor_le_last q",
                "apply beta_sorted_factor_le_last",
                "exact hmember_witness_left",
                "exact hmember_witness_right",
                "exact hlast",
                "exact hsorted",
                "specialize le_antisymm q",
                "specialize le_antisymm p",
                "apply le_antisymm",
                "exact hupper",
                "exact hlower",
            ),
            "A prime dividing a sorted prime prefix equals its terminal "
            "factor whenever that terminal factor is bounded by the prime.",
        ),
        spec(
            EVEN_VALUATION_SORTED_TERMINAL_PRIME_HAS_EQUAL_PREDECESSOR,
            f"forall b c l n p e h. ({prime_p}) -> ({full_all_prime}) -> "
            f"({full_sorted}) -> ({full_product}) -> ({terminal_entry}) -> "
            f"~(n = 0) -> ({source_valuation}) -> e = h + h -> "
            f"({predecessor_result})",
            (
                "beta_product_succ_decompose",
                "beta_at_unique",
                "mul_comm",
                EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR,
                PRIME_SQUARE_DIVISIBILITY_FORCES_SUFFIX_PRIME_DIVISOR,
                "all_prime_succ_elim_prefix",
                "sorted_succ_elim_prefix",
                "sorted_succ_elim_last",
                BETA_SORTED_PRIME_PREFIX_DIVISOR_EQUALS_BOUNDED_LAST,
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro p",
                "intro e",
                "intro h",
                "intro hprime",
                "intro hallprime",
                "intro hsorted",
                "intro hproduct",
                "intro hterminal",
                "intro hnonzero",
                "intro hvaluation",
                "intro heven",
                f"have hdecomposition : {decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose (S l)",
                "specialize beta_product_succ_decompose n",
                "apply beta_product_succ_decompose",
                "exact hproduct",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                "have hlast_equal : x = p",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique (S l)",
                "specialize beta_at_unique x",
                "specialize beta_at_unique p",
                "apply beta_at_unique",
                "exact hdecomposition_witness_witness_left",
                "exact hterminal",
                "have hfactorization : n = x1 * p",
                "trans x1 * x",
                "exact hdecomposition_witness_witness_right_right",
                "congr",
                "refl",
                "exact hlast_equal",
                f"have hprime_divides : {prime_divides_value}",
                "exists x1",
                "trans x1 * p",
                "exact hfactorization",
                "apply mul_comm",
                f"have hsquare_divides : {square_divides_value}",
                "specialize even_positive_prime_valuation_has_square_divisor p",
                "specialize even_positive_prime_valuation_has_square_divisor n",
                "specialize even_positive_prime_valuation_has_square_divisor e",
                "specialize even_positive_prime_valuation_has_square_divisor h",
                "apply even_positive_prime_valuation_has_square_divisor",
                "exact hprime",
                "exact hnonzero",
                "exact hvaluation",
                "exact hprime_divides",
                "exact heven",
                f"have hprefix_divides : {_multiple('p', 'x1', tag='ftsp_terminal_prefix_divides')}",
                "specialize prime_square_divisibility_forces_suffix_prime_divisor p",
                "specialize prime_square_divisibility_forces_suffix_prime_divisor x1",
                "specialize prime_square_divisibility_forces_suffix_prime_divisor n",
                "apply prime_square_divisibility_forces_suffix_prime_divisor",
                "exact hprime",
                "exact hfactorization",
                "exact hsquare_divides",
                f"have hprefix_prime : {prefix_all_prime}",
                "specialize all_prime_succ_elim_prefix b",
                "specialize all_prime_succ_elim_prefix c",
                "specialize all_prime_succ_elim_prefix (S l)",
                "apply all_prime_succ_elim_prefix",
                "exact hallprime",
                f"have hprefix_sorted : {prefix_sorted}",
                "specialize sorted_succ_elim_prefix b",
                "specialize sorted_succ_elim_prefix c",
                "specialize sorted_succ_elim_prefix (S l)",
                "apply sorted_succ_elim_prefix",
                "exact hsorted",
                f"have hlast_pair : {last_sorted_pair}",
                "specialize sorted_succ_elim_last b",
                "specialize sorted_succ_elim_last c",
                "specialize sorted_succ_elim_last l",
                "apply sorted_succ_elim_last",
                "exact hsorted",
                "cases hlast_pair",
                "cases hlast_pair_witness",
                "cases hlast_pair_witness_witness",
                "cases hlast_pair_witness_witness_right",
                "have hright_equal : x3 = p",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique (S l)",
                "specialize beta_at_unique x3",
                "specialize beta_at_unique p",
                "apply beta_at_unique",
                "exact hlast_pair_witness_witness_right_left",
                "exact hterminal",
                "have hupper : exists k. k + x2 = p",
                "rewrite hright_equal at hlast_pair_witness_witness_right_right",
                "exact hlast_pair_witness_witness_right_right",
                "have hpredecessor_equal : x2 = p",
                "specialize beta_sorted_prime_prefix_divisor_equals_bounded_last b",
                "specialize beta_sorted_prime_prefix_divisor_equals_bounded_last c",
                "specialize beta_sorted_prime_prefix_divisor_equals_bounded_last l",
                "specialize beta_sorted_prime_prefix_divisor_equals_bounded_last x1",
                "specialize beta_sorted_prime_prefix_divisor_equals_bounded_last p",
                "specialize beta_sorted_prime_prefix_divisor_equals_bounded_last x2",
                "apply beta_sorted_prime_prefix_divisor_equals_bounded_last",
                "exact hprime",
                "exact hprefix_prime",
                "exact hprefix_sorted",
                "exact hdecomposition_witness_witness_right_left",
                "exact hlast_pair_witness_witness_left",
                "exact hprefix_divides",
                "exact hupper",
                "rewrite hpredecessor_equal at hlast_pair_witness_witness_left",
                "rewrite hpredecessor_equal at hlast_pair_witness_witness_left",
                "exact hlast_pair_witness_witness_left",
            ),
            "In a sorted all-prime beta factorization, a terminal prime with "
            "positive even valuation has the identical immediately preceding factor.",
        ),
        spec(
            PAIRING_DOUBLE_EQUALS_TWO_MUL,
            "forall a. a + a = 2 * a",
            ("mul_succ_left", "one_mul"),
            (
                "intro a",
                "symm",
                "trans 1 * a + a",
                "apply mul_succ_left",
                "congr",
                "apply one_mul",
                "refl",
            ),
            "The additive double of a natural equals its standard "
            "multiplicative parity witness.",
        ),
        spec(
            EVEN_DOUBLE_SUM_REFLECTS_EVEN_TAIL,
            "forall a b h. (a + a) + b = h + h -> exists k. b = k + k",
            (
                PAIRING_DOUBLE_EQUALS_TWO_MUL,
                "even_sum_parity_cases",
                "even_not_odd",
            ),
            (
                "intro a",
                "intro b",
                "intro h",
                "intro heven",
                "have hsum : exists k. (a + a) + b = 2 * k",
                "exists h",
                "trans h + h",
                "exact heven",
                "apply pairing_double_equals_two_mul",
                "have hdouble : exists k. a + a = 2 * k",
                "exists a",
                "apply pairing_double_equals_two_mul",
                "have hcases : "
                "(((exists k. a + a = 2 * k) /\\ (exists k. b = 2 * k)) \\/ "
                "((exists k. a + a = 2 * k + 1) /\\ (exists k. b = 2 * k + 1)))",
                "specialize even_sum_parity_cases (a + a)",
                "specialize even_sum_parity_cases b",
                "apply even_sum_parity_cases",
                "exact hsum",
                "cases hcases",
                "cases hcases_left",
                "cases hcases_left_right",
                "exists x",
                "trans 2 * x",
                "exact hcases_left_right_witness",
                "symm",
                "apply pairing_double_equals_two_mul",
                "cases hcases_right",
                "exfalso",
                "specialize even_not_odd (a + a)",
                "apply even_not_odd",
                "exact hdouble",
                "exact hcases_right_left",
            ),
            "If an additive even block plus a tail is even, the tail has "
            "its own constructive additive half witness.",
        ),
        spec(
            DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX,
            f"forall p q n e f g. ({prime_p}) -> ({prime_q}) -> "
            "~(p = q) -> ~(n = 0) -> "
            f"({reflected_value}) -> ({reflected_prime}) -> "
            f"({reflected_product}) -> "
            "(exists h. g = h + h) -> exists h. e = h + h",
            (
                DISTINCT_PRIME_POWER_VALUATION_ZERO,
                "prime_nonzero",
                "prime_power_valuation_mul",
            ),
            (
                "intro p",
                "intro q",
                "intro n",
                "intro e",
                "intro f",
                "intro g",
                "intro hp",
                "intro hq",
                "intro hdistinct",
                "intro hnnonzero",
                "intro hnvaluation",
                "intro hqvaluation",
                "intro hproduct",
                "intro heven",
                "have hzero : f = 0",
                "specialize distinct_prime_power_valuation_zero p",
                "specialize distinct_prime_power_valuation_zero q",
                "specialize distinct_prime_power_valuation_zero f",
                "apply distinct_prime_power_valuation_zero",
                "exact hp",
                "exact hq",
                "exact hdistinct",
                "exact hqvaluation",
                "have hqnonzero : ~(q = 0)",
                "specialize prime_nonzero q",
                "intro hqzero",
                "apply prime_nonzero",
                "exact hq",
                "exact hqzero",
                "have hsum : g = e + f",
                "specialize prime_power_valuation_mul p",
                "specialize prime_power_valuation_mul n",
                "specialize prime_power_valuation_mul q",
                "specialize prime_power_valuation_mul e",
                "specialize prime_power_valuation_mul f",
                "specialize prime_power_valuation_mul g",
                "apply prime_power_valuation_mul",
                "exact hp",
                "exact hnnonzero",
                "exact hqnonzero",
                "exact hnvaluation",
                "exact hqvaluation",
                "exact hproduct",
                "rewrite hzero at hsum",
                "rewrite PA3 at hsum",
                "cases heven",
                "exists x",
                "trans g",
                "symm",
                "exact hsum",
                "exact heven_witness",
            ),
            "Removing a distinct prime singleton preserves the even "
            "valuation of every other prime in a nonzero product.",
        ),
        spec(
            SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR,
            f"forall p z n e f g. ({prime_p}) -> ~(z = 0) -> ~(n = 0) -> "
            f"({square_factor_valuation}) -> ({square_cofactor_valuation}) -> "
            f"({square_product_valuation}) -> "
            "(exists h. g = h + h) -> exists h. f = h + h",
            (
                "prime_power_valuation_square_factor_shift",
                EVEN_DOUBLE_SUM_REFLECTS_EVEN_TAIL,
            ),
            (
                "intro p",
                "intro z",
                "intro n",
                "intro e",
                "intro f",
                "intro g",
                "intro hprime",
                "intro hznonzero",
                "intro hnnonzero",
                "intro hzvaluation",
                "intro hnvaluation",
                "intro hproduct",
                "intro heven",
                "have hshift : g = (e + e) + f",
                "specialize prime_power_valuation_square_factor_shift p",
                "specialize prime_power_valuation_square_factor_shift z",
                "specialize prime_power_valuation_square_factor_shift n",
                "specialize prime_power_valuation_square_factor_shift e",
                "specialize prime_power_valuation_square_factor_shift f",
                "specialize prime_power_valuation_square_factor_shift g",
                "apply prime_power_valuation_square_factor_shift",
                "exact hprime",
                "exact hznonzero",
                "exact hnnonzero",
                "exact hzvaluation",
                "exact hnvaluation",
                "exact hproduct",
                "cases heven",
                "specialize even_double_sum_reflects_even_tail e",
                "specialize even_double_sum_reflects_even_tail f",
                "specialize even_double_sum_reflects_even_tail x",
                "apply even_double_sum_reflects_even_tail",
                "trans g",
                "symm",
                "exact hshift",
                "exact heven_witness",
            ),
            "Removing any nonzero natural-square factor preserves the "
            "even valuation of every prime in the remaining cofactor.",
        ),
        spec(
            THREE_MOD_FOUR_NUMBER_NOT_EQUAL_REPRESENTED,
            f"forall p q. ({bad_p}) -> ({represented_q}) -> ~(p = q)",
            ("sum_two_squares_not_four_mod_three",),
            (
                "intro p",
                "intro q",
                "intro hthree",
                "intro hrepresented",
                "intro hequal",
                "cases hthree",
                "cases hrepresented",
                "cases hrepresented_witness",
                "specialize sum_two_squares_not_four_mod_three x1",
                "specialize sum_two_squares_not_four_mod_three x2",
                "apply sum_two_squares_not_four_mod_three",
                "exists x",
                "trans q",
                "symm",
                "exact hrepresented_witness_witness",
                "trans p",
                "symm",
                "exact hequal",
                "exact hthree_witness",
            ),
            "A number congruent to three modulo four cannot equal any "
            "explicitly represented two-square number.",
        ),
        spec(
            ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_REPRESENTED_PRIME,
            f"forall q n. ({prime_q}) -> ({represented_q}) -> ~(n = 0) -> "
            f"({parity_good_product}) -> ({parity_source_value})",
            (
                THREE_MOD_FOUR_NUMBER_NOT_EQUAL_REPRESENTED,
                "power_valuation_exists",
                DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX,
            ),
            (
                "intro q",
                "intro n",
                "intro hqprime",
                "intro hrepresented",
                "intro hnonzero",
                "intro htotal",
                "intro p",
                "intro e",
                "intro hpprime",
                "intro hpbad",
                "intro hnvaluation",
                "have hdistinct : ~(p = q)",
                "specialize three_mod_four_number_not_equal_represented p",
                "specialize three_mod_four_number_not_equal_represented q",
                "intro hequal",
                "apply three_mod_four_number_not_equal_represented",
                "exact hpbad",
                "exact hrepresented",
                "exact hequal",
                f"have hqvaluation : exists f. ({reflected_prime})",
                "apply power_valuation_exists",
                "cases hqvaluation",
                f"have hproduct : exists g. ({reflected_product})",
                "apply power_valuation_exists",
                "cases hproduct",
                "have heven : exists h. x1 = h + h",
                "specialize htotal p",
                "specialize htotal x1",
                "apply htotal",
                "exact hpprime",
                "exact hpbad",
                "exact hproduct_witness",
                "specialize distinct_prime_factor_even_valuation_reflects_prefix p",
                "specialize distinct_prime_factor_even_valuation_reflects_prefix q",
                "specialize distinct_prime_factor_even_valuation_reflects_prefix n",
                "specialize distinct_prime_factor_even_valuation_reflects_prefix e",
                "specialize distinct_prime_factor_even_valuation_reflects_prefix x",
                "specialize distinct_prime_factor_even_valuation_reflects_prefix x1",
                "apply distinct_prime_factor_even_valuation_reflects_prefix",
                "exact hpprime",
                "exact hqprime",
                "exact hdistinct",
                "exact hnonzero",
                "exact hnvaluation",
                "exact hqvaluation_witness",
                "exact hproduct_witness",
                "exact heven",
            ),
            "Removing a represented prime singleton preserves the entire "
            "universal three-modulo-four even-valuation invariant.",
        ),
        spec(
            ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_SQUARE_FACTOR,
            "forall z n. ~(z = 0) -> ~(n = 0) -> "
            f"({parity_square_product}) -> ({parity_source_value})",
            (
                "power_valuation_exists",
                "power_valuation_value_eq_transport",
                "mul_comm",
                SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR,
            ),
            (
                "intro z",
                "intro n",
                "intro hznonzero",
                "intro hnnonzero",
                "intro htotal",
                "intro p",
                "intro f",
                "intro hpprime",
                "intro hpbad",
                "intro hnvaluation",
                f"have hzvaluation : exists e. ({square_factor_valuation})",
                "apply power_valuation_exists",
                "cases hzvaluation",
                f"have hproduct : exists g. ({square_product_valuation})",
                "apply power_valuation_exists",
                "cases hproduct",
                "have hrightvaluation : "
                f"({_power_valuation_term('p', 'n * (z * z)', 'x1', tag='ftsp_square_right_transport')})",
                "specialize power_valuation_value_eq_transport p",
                "specialize power_valuation_value_eq_transport ((z * z) * n)",
                "specialize power_valuation_value_eq_transport (n * (z * z))",
                "specialize power_valuation_value_eq_transport x1",
                "apply power_valuation_value_eq_transport",
                "apply mul_comm",
                "exact hproduct_witness",
                "have heven : exists h. x1 = h + h",
                "specialize htotal p",
                "specialize htotal x1",
                "apply htotal",
                "exact hpprime",
                "exact hpbad",
                "exact hrightvaluation",
                "specialize square_factor_even_valuation_reflects_cofactor p",
                "specialize square_factor_even_valuation_reflects_cofactor z",
                "specialize square_factor_even_valuation_reflects_cofactor n",
                "specialize square_factor_even_valuation_reflects_cofactor x",
                "specialize square_factor_even_valuation_reflects_cofactor f",
                "specialize square_factor_even_valuation_reflects_cofactor x1",
                "apply square_factor_even_valuation_reflects_cofactor",
                "exact hpprime",
                "exact hznonzero",
                "exact hnnonzero",
                "exact hzvaluation_witness",
                "exact hnvaluation",
                "exact hproduct_witness",
                "exact heven",
            ),
            "Removing a nonzero natural-square block preserves every "
            "three-modulo-four prime's constructive even-valuation invariant.",
        ),
        spec(
            ALL_BAD_PRIME_EVEN_VALUATION_VALUE_EQ_TRANSPORT,
            f"forall a b. a = b -> ({parity_transport_source}) -> "
            f"({parity_transport_target})",
            ("power_valuation_value_eq_transport",),
            (
                "intro a",
                "intro b",
                "intro hequal",
                "intro hsource",
                "intro p",
                "intro e",
                "intro hprime",
                "intro hthree",
                "intro htarget",
                "have hvaluation : "
                f"({power_valuation('p', 'a', 'e', tag='ftsp_transport_local')})",
                "specialize power_valuation_value_eq_transport p",
                "specialize power_valuation_value_eq_transport b",
                "specialize power_valuation_value_eq_transport a",
                "specialize power_valuation_value_eq_transport e",
                "apply power_valuation_value_eq_transport",
                "symm",
                "exact hequal",
                "exact htarget",
                "specialize hsource p",
                "specialize hsource e",
                "apply hsource",
                "exact hprime",
                "exact hthree",
                "exact hvaluation",
            ),
            "The universally quantified bad-prime even-valuation invariant "
            "transports constructively along equality of natural values.",
        ),
        spec(
            PRIME_MOD_FOUR_GOOD_OR_THREE,
            f"forall p. ({prime_p}) -> "
            "((p = 2 \\/ exists k. p = 4 * k + 1) \\/ "
            "exists k. p = 4 * k + 3)",
            ("prime_mod_four_trichotomy",),
            (
                "intro p",
                "intro hprime",
                "have hclasses : "
                "(p = 2 \\/ ((exists k. p = 4 * k + 1) \\/ "
                "(exists k. p = 4 * k + 3)))",
                "specialize prime_mod_four_trichotomy p",
                "apply prime_mod_four_trichotomy",
                "exact hprime",
                "cases hclasses",
                "left",
                "left",
                "exact hclasses_left",
                "cases hclasses_right",
                "left",
                "right",
                "exact hclasses_right_left",
                "right",
                "exact hclasses_right_right",
            ),
            "The constructive prime residue trichotomy splits into one "
            "represented-prime branch and one three-modulo-four branch.",
        ),
        spec(
            ALL_BAD_PRIME_EVEN_TWO_SQUARE_SUFFICIENCY_BOUNDED,
            f"forall B n. ({induction_bound}) -> ~(n = 0) -> "
            f"({value_parity}) -> ({value_representation})",
            (
                "le_zero",
                "eq_decidable",
                "prime_divisor_exists",
                PRIME_MOD_FOUR_GOOD_OR_THREE,
                "prime_two_or_one_mod_four_is_sum_of_two_squares",
                ALL_BAD_PRIME_EVEN_VALUATION_VALUE_EQ_TRANSPORT,
                ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_REPRESENTED_PRIME,
                "mul_comm",
                "proper_factor_lt",
                "le_trans",
                "le_of_succ_le_succ",
                "two_square_representation_multiplicatively_closed",
                "power_valuation_exists",
                EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR,
                "prime_nonzero",
                ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_SQUARE_FACTOR,
                "prime_square_times_nonzero_strictly_increases",
                "two_square_representation_preserved_by_square_factor",
            ),
            (
                "intro B",
                "induction B",
                "intro n",
                "intro hbound",
                "intro hnonzero",
                "intro hparity",
                "exfalso",
                "apply hnonzero",
                "specialize le_zero n",
                "apply le_zero",
                "exact hbound",
                "intro n",
                "intro hbound",
                "intro hnonzero",
                "intro hparity",
                "specialize eq_decidable n",
                "specialize eq_decidable 1",
                "cases eq_decidable",
                "exists 1",
                "exists 0",
                "rewrite eq_decidable_left",
                "norm_num",
                "have hfactor : exists p. "
                f"(({prime('p', tag='ftsp_induction_factor_prime')}) /\\ "
                "exists r. n = p * r)",
                "specialize prime_divisor_exists n",
                "apply prime_divisor_exists",
                "exact hnonzero",
                "exact eq_decidable_right",
                "cases hfactor",
                "cases hfactor_witness",
                "cases hfactor_witness_right",
                "have hprefix_nonzero : ~(x1 = 0)",
                "intro hzero",
                "apply hnonzero",
                "trans x * x1",
                "exact hfactor_witness_right_witness",
                "rewrite hzero",
                "apply PA5",
                "have hchoice : "
                "((x = 2 \\/ exists k. x = 4 * k + 1) \\/ "
                "exists k. x = 4 * k + 3)",
                "specialize prime_mod_four_good_or_three x",
                "apply prime_mod_four_good_or_three",
                "exact hfactor_witness_left",
                "cases hchoice",
                "have hrepresented_prime : "
                f"({_two_square('x', tag='ftsp_induction_good_prime')})",
                "specialize prime_two_or_one_mod_four_is_sum_of_two_squares x",
                "apply prime_two_or_one_mod_four_is_sum_of_two_squares",
                "exact hfactor_witness_left",
                "exact hchoice_left",
                "have hordered : n = x1 * x",
                "trans x * x1",
                "exact hfactor_witness_right_witness",
                "apply mul_comm",
                "have hproduct_parity : "
                f"({_all_bad_prime_valuations_even('x1 * x', tag='ftsp_induction_good_product')})",
                "specialize all_bad_prime_even_valuation_value_eq_transport n",
                "specialize all_bad_prime_even_valuation_value_eq_transport (x1 * x)",
                "apply all_bad_prime_even_valuation_value_eq_transport",
                "exact hordered",
                "exact hparity",
                "have hprefix_parity : "
                f"({_all_bad_prime_valuations_even('x1', tag='ftsp_induction_good_prefix')})",
                "specialize all_bad_prime_even_valuations_strip_represented_prime x",
                "specialize all_bad_prime_even_valuations_strip_represented_prime x1",
                "apply all_bad_prime_even_valuations_strip_represented_prime",
                "exact hfactor_witness_left",
                "exact hrepresented_prime",
                "exact hprefix_nonzero",
                "exact hproduct_parity",
                "have hnotone : ~(x = 1)",
                "cases hfactor_witness_left",
                "exact hfactor_witness_left_left",
                "have hstrict : exists k. k + S x1 = n",
                "specialize proper_factor_lt n",
                "specialize proper_factor_lt x1",
                "specialize proper_factor_lt x",
                "apply proper_factor_lt",
                "exact hnonzero",
                "exact hordered",
                "exact hnotone",
                "have hsuccessor_bound : exists k. k + S x1 = S B",
                "specialize le_trans (S x1)",
                "specialize le_trans n",
                "specialize le_trans (S B)",
                "apply le_trans",
                "exact hstrict",
                "exact hbound",
                "have hprefix_bound : exists k. k + x1 = B",
                "specialize le_of_succ_le_succ x1",
                "specialize le_of_succ_le_succ B",
                "apply le_of_succ_le_succ",
                "exact hsuccessor_bound",
                "have hprefix_representation : "
                f"({_two_square('x1', tag='ftsp_induction_good_prefix_result')})",
                "specialize IH x1",
                "apply IH",
                "exact hprefix_bound",
                "exact hprefix_nonzero",
                "exact hprefix_parity",
                "rewrite hordered",
                "specialize two_square_representation_multiplicatively_closed x1",
                "specialize two_square_representation_multiplicatively_closed x",
                "apply two_square_representation_multiplicatively_closed",
                "exact hprefix_representation",
                "exact hrepresented_prime",
                "have hvaluation : exists e. "
                f"({power_valuation('x', 'n', 'e', tag='ftsp_induction_bad_valuation')})",
                "apply power_valuation_exists",
                "cases hvaluation",
                "have heven : exists h. x2 = h + h",
                "specialize hparity x",
                "specialize hparity x2",
                "apply hparity",
                "exact hfactor_witness_left",
                "exact hchoice_right",
                "exact hvaluation_witness",
                "cases heven",
                "have hdivides : exists k. n = x * k",
                "exists x1",
                "exact hfactor_witness_right_witness",
                "have hsquare : exists r. n = (x * x) * r",
                "specialize even_positive_prime_valuation_has_square_divisor x",
                "specialize even_positive_prime_valuation_has_square_divisor n",
                "specialize even_positive_prime_valuation_has_square_divisor x2",
                "specialize even_positive_prime_valuation_has_square_divisor x3",
                "apply even_positive_prime_valuation_has_square_divisor",
                "exact hfactor_witness_left",
                "exact hnonzero",
                "exact hvaluation_witness",
                "exact hdivides",
                "exact heven_witness",
                "cases hsquare",
                "have hsquare_quotient_nonzero : ~(x4 = 0)",
                "intro hzero",
                "apply hnonzero",
                "trans (x * x) * x4",
                "exact hsquare_witness",
                "rewrite hzero",
                "apply PA5",
                "have hprime_nonzero : ~(x = 0)",
                "specialize prime_nonzero x",
                "intro hzero",
                "apply prime_nonzero",
                "exact hfactor_witness_left",
                "exact hzero",
                "have hsquare_ordered : n = x4 * (x * x)",
                "trans (x * x) * x4",
                "exact hsquare_witness",
                "apply mul_comm",
                "have hsquare_parity : "
                f"({_all_bad_prime_valuations_even('x4 * (x * x)', tag='ftsp_induction_bad_product')})",
                "specialize all_bad_prime_even_valuation_value_eq_transport n",
                "specialize all_bad_prime_even_valuation_value_eq_transport (x4 * (x * x))",
                "apply all_bad_prime_even_valuation_value_eq_transport",
                "exact hsquare_ordered",
                "exact hparity",
                "have hquotient_parity : "
                f"({_all_bad_prime_valuations_even('x4', tag='ftsp_induction_bad_prefix')})",
                "specialize all_bad_prime_even_valuations_strip_square_factor x",
                "specialize all_bad_prime_even_valuations_strip_square_factor x4",
                "apply all_bad_prime_even_valuations_strip_square_factor",
                "exact hprime_nonzero",
                "exact hsquare_quotient_nonzero",
                "exact hsquare_parity",
                "have hsquare_strict : exists k. k + S x4 = (x * x) * x4",
                "specialize prime_square_times_nonzero_strictly_increases x",
                "specialize prime_square_times_nonzero_strictly_increases x4",
                "apply prime_square_times_nonzero_strictly_increases",
                "exact hfactor_witness_left",
                "exact hsquare_quotient_nonzero",
                "rewrite <- hsquare_witness at hsquare_strict",
                "have hsquare_successor_bound : exists k. k + S x4 = S B",
                "specialize le_trans (S x4)",
                "specialize le_trans n",
                "specialize le_trans (S B)",
                "apply le_trans",
                "exact hsquare_strict",
                "exact hbound",
                "have hsquare_bound : exists k. k + x4 = B",
                "specialize le_of_succ_le_succ x4",
                "specialize le_of_succ_le_succ B",
                "apply le_of_succ_le_succ",
                "exact hsquare_successor_bound",
                "have hquotient_representation : "
                f"({_two_square('x4', tag='ftsp_induction_bad_prefix_result')})",
                "specialize IH x4",
                "apply IH",
                "exact hsquare_bound",
                "exact hsquare_quotient_nonzero",
                "exact hquotient_parity",
                "rewrite hsquare_ordered",
                "specialize two_square_representation_preserved_by_square_factor x4",
                "specialize two_square_representation_preserved_by_square_factor x",
                "apply two_square_representation_preserved_by_square_factor",
                "exact hquotient_representation",
            ),
            "Bounded constructive descent on the natural value proves "
            "sufficiency of even valuations at every three-modulo-four prime.",
        ),
        spec(
            POSITIVE_NUMBER_WITH_EVEN_BAD_PRIME_VALUATIONS_IS_TWO_SQUARE,
            f"forall n. ~(n = 0) -> ({value_parity}) -> ({value_representation})",
            ("le_refl", ALL_BAD_PRIME_EVEN_TWO_SQUARE_SUFFICIENCY_BOUNDED),
            (
                "intro n",
                "intro hnonzero",
                "intro hparity",
                "specialize all_bad_prime_even_two_square_sufficiency_bounded n",
                "specialize all_bad_prime_even_two_square_sufficiency_bounded n",
                "apply all_bad_prime_even_two_square_sufficiency_bounded",
                "specialize le_refl n",
                "exact le_refl",
                "exact hnonzero",
                "exact hparity",
            ),
            "Every nonzero natural whose three-modulo-four prime valuations "
            "are all even has an explicitly witnessed two-square representation.",
        ),
        spec(
            NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
            f"forall n. ~(n = 0) -> "
            f"((({value_representation}) -> ({value_parity})) /\\ "
            f"(({value_parity}) -> ({value_representation})))",
            (
                "three_mod_four_prime_represented_nonzero_valuation_even",
                POSITIVE_NUMBER_WITH_EVEN_BAD_PRIME_VALUATIONS_IS_TWO_SQUARE,
            ),
            (
                "intro n",
                "intro hnonzero",
                "split",
                "intro hrepresented",
                "intro p",
                "intro e",
                "intro hprime",
                "intro hthree",
                "intro hvaluation",
                "specialize three_mod_four_prime_represented_nonzero_valuation_even p",
                "specialize three_mod_four_prime_represented_nonzero_valuation_even n",
                "specialize three_mod_four_prime_represented_nonzero_valuation_even e",
                "apply three_mod_four_prime_represented_nonzero_valuation_even",
                "exact hprime",
                "exact hthree",
                "exact hnonzero",
                "exact hrepresented",
                "exact hvaluation",
                "intro hparity",
                "specialize positive_number_with_even_bad_prime_valuations_is_two_square n",
                "apply positive_number_with_even_bad_prime_valuations_is_two_square",
                "exact hnonzero",
                "exact hparity",
            ),
            "Complete nonzero Fermat two-square classification: witnessed "
            "representation is equivalent to even valuation at every "
            "three-modulo-four prime.",
        ),
        spec(
            TWO_SQUARE_IFF_ZERO_OR_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
            f"forall n. ((({value_representation}) -> "
            f"(n = 0 \\/ (~(n = 0) /\\ ({value_parity})))) /\\ "
            f"((n = 0 \\/ (~(n = 0) /\\ ({value_parity}))) -> "
            f"({value_representation})))",
            (
                "eq_decidable",
                NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
            ),
            (
                "intro n",
                "split",
                "intro hrepresented",
                "specialize eq_decidable n",
                "specialize eq_decidable 0",
                "cases eq_decidable",
                "left",
                "exact eq_decidable_left",
                "right",
                "split",
                "exact eq_decidable_right",
                "specialize nonzero_two_square_iff_even_three_mod_four_prime_valuations n",
                "have hiff : "
                f"((({value_representation}) -> ({value_parity})) /\\ "
                f"(({value_parity}) -> ({value_representation})))",
                "apply nonzero_two_square_iff_even_three_mod_four_prime_valuations",
                "exact eq_decidable_right",
                "cases hiff",
                "apply hiff_left",
                "exact hrepresented",
                "intro hcases",
                "cases hcases",
                "exists 0",
                "exists 0",
                "rewrite hcases_left",
                "norm_num",
                "cases hcases_right",
                "specialize nonzero_two_square_iff_even_three_mod_four_prime_valuations n",
                "have hiff : "
                f"((({value_representation}) -> ({value_parity})) /\\ "
                f"(({value_parity}) -> ({value_representation})))",
                "apply nonzero_two_square_iff_even_three_mod_four_prime_valuations",
                "exact hcases_right_left",
                "cases hiff",
                "apply hiff_right",
                "exact hcases_right_right",
            ),
            "Full all-natural two-square theorem, with zero explicitly "
            "separated from the nonzero even-prime-valuation criterion.",
        ),
    )


__all__ = [
    "DISTINCT_PRIME_POWER_VALUATION_ZERO",
    "BETA_SORTED_PRIME_PREFIX_DIVISOR_EQUALS_BOUNDED_LAST",
    "EVEN_VALUATION_SORTED_TERMINAL_PRIME_HAS_EQUAL_PREDECESSOR",
    "EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR",
    "POSITIVE_DOUBLE_AT_LEAST_TWO",
    "PAIRING_DOUBLE_EQUALS_TWO_MUL",
    "EVEN_DOUBLE_SUM_REFLECTS_EVEN_TAIL",
    "DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX",
    "SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR",
    "THREE_MOD_FOUR_NUMBER_NOT_EQUAL_REPRESENTED",
    "ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_REPRESENTED_PRIME",
    "ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_SQUARE_FACTOR",
    "ALL_BAD_PRIME_EVEN_VALUATION_VALUE_EQ_TRANSPORT",
    "PRIME_MOD_FOUR_GOOD_OR_THREE",
    "ALL_BAD_PRIME_EVEN_TWO_SQUARE_SUFFICIENCY_BOUNDED",
    "POSITIVE_NUMBER_WITH_EVEN_BAD_PRIME_VALUATIONS_IS_TWO_SQUARE",
    "NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS",
    "TWO_SQUARE_IFF_ZERO_OR_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS",
    "PRIME_DIVISOR_OF_PRIME_FORCES_EQUALITY",
    "PRIME_SQUARE_DIVISIBILITY_FORCES_SUFFIX_PRIME_DIVISOR",
    "make_fermat_two_squares_pairing_candidate_theorems",
]
