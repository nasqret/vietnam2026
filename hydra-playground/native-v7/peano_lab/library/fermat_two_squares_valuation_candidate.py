"""Constructive valuation and squared-factor bridges for two-square norms.

Zero is handled separately: prime-power valuations and valuation descent are
asserted only for explicitly nonzero values.  Every convenience relation is
expanded into the unchanged first-order language ``{0,S,+,*,=}`` before the
kernel sees it.  These isolated dependency-curried candidates neither assert
the complete all-integer criterion nor grant Alpha/Stable authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_central_binom_valuation_candidate import _power_valuation_term
from .bertrand_power_valuation_candidate import power_valuation
from .fermat_residue_map_candidate import prime
from .fermat_two_squares_classification_candidate import _four_three, _two_square
from .fermat_two_squares_collision_norm_candidate import _multiple


TWO_SQUARE_SELF_SQUARE_ZERO_REFLECTS = "two_square_self_square_zero_reflects"
TWO_SQUARE_NORM_ZERO_IFF_COORDINATES_ZERO = (
    "two_square_norm_zero_iff_coordinates_zero"
)
PRIME_POWER_VALUATION_SQUARE_EVEN = "prime_power_valuation_square_even"
TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY = "two_square_common_factor_norm_identity"
TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR = (
    "two_square_common_divisor_extracts_squared_factor"
)
TWO_SQUARE_COMMON_SQUARED_FACTOR_DIVIDES_NORM = (
    "two_square_common_squared_factor_divides_norm"
)
TWO_SQUARE_REPRESENTATION_PRESERVED_BY_SQUARE_FACTOR = (
    "two_square_representation_preserved_by_square_factor"
)
THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_EXTRACTS_SQUARED_FACTOR = (
    "three_mod_four_prime_two_square_norm_extracts_squared_factor"
)
THREE_MOD_FOUR_PRIME_NONZERO_TWO_SQUARE_NORM_EXTRACTS_NONZERO_QUOTIENT = (
    "three_mod_four_prime_nonzero_two_square_norm_extracts_nonzero_quotient"
)
PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT = (
    "prime_power_valuation_square_factor_shift"
)
PRIME_POWER_VALUATION_SQUARE_FACTOR_PRESERVES_EVENNESS = (
    "prime_power_valuation_square_factor_preserves_evenness"
)
THREE_MOD_FOUR_PRIME_NONZERO_NORM_POSITIVE_VALUATION_EXTRACTS = (
    "three_mod_four_prime_nonzero_norm_positive_valuation_extracts"
)
PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES = (
    "prime_square_times_nonzero_strictly_increases"
)
THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN_BOUNDED = (
    "three_mod_four_prime_two_square_norm_valuation_even_bounded"
)
THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN = (
    "three_mod_four_prime_two_square_norm_valuation_even"
)
THREE_MOD_FOUR_PRIME_REPRESENTED_NONZERO_VALUATION_EVEN = (
    "three_mod_four_prime_represented_nonzero_valuation_even"
)


def _coordinate_extraction(*, tag: str, nonzero: bool = False) -> str:
    """Expand witnessed common-coordinate division and exact norm extraction."""

    first = f"ftsv_first_{tag}"
    second = f"ftsv_second_{tag}"
    quotient = f"{first} * {first} + {second} * {second}"
    identity = (
        f"a * a + b * b = (p * p) * ({quotient})"
    )
    conclusion = identity if not nonzero else f"(({identity}) /\\ ~(({quotient}) = 0))"
    return (
        f"exists {first} {second}. "
        f"((a = p * {first}) /\\ "
        f"((b = p * {second}) /\\ ({conclusion})))"
    )


def make_fermat_two_squares_valuation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build isolated, bounded valuation and prime-square extraction bridges."""

    prime_p = prime("p", tag="ftsv_prime")
    three_p = _four_three("p", tag="ftsv_prime")
    square_input = power_valuation("p", "a", "e", tag="ftsv_square_input")
    square_output = _power_valuation_term(
        "p", "a * a", "E", tag="ftsv_square_output"
    )
    first_divides = _multiple("p", "a", tag="ftsv_first_divides")
    second_divides = _multiple("p", "b", tag="ftsv_second_divides")
    norm_divides = _multiple("p", "a * a + b * b", tag="ftsv_norm_divides")
    square_divides = _multiple(
        "p * p", "a * a + b * b", tag="ftsv_square_divides"
    )
    extracted = _coordinate_extraction(tag="extracted")
    nonzero_extracted = _coordinate_extraction(tag="nonzero", nonzero=True)

    shift_factor = power_valuation("p", "z", "e", tag="ftsv_shift_factor")
    shift_value = power_valuation("p", "n", "f", tag="ftsv_shift_value")
    shift_product = _power_valuation_term(
        "p", "(z * z) * n", "g", tag="ftsv_shift_product"
    )
    shift_square_witness = _power_valuation_term(
        "p", "z * z", "E", tag="ftsv_shift_square_witness"
    )
    norm_valuation = _power_valuation_term(
        "p", "a * a + b * b", "e", tag="ftsv_norm_valuation"
    )
    represented_valuation = power_valuation(
        "p", "n", "e", tag="ftsv_represented_valuation"
    )
    bound = "exists ftsv_bound_gap. ftsv_bound_gap + (a * a + b * b) = B"
    induction_quotient = "x * x + x1 * x1"
    induction_quotient_valuation = _power_valuation_term(
        "p", induction_quotient, "f", tag="ftsv_induction_quotient"
    )
    induction_prime_valuation = power_valuation(
        "p", "p", "r", tag="ftsv_induction_prime"
    )
    induction_product_valuation = _power_valuation_term(
        "p",
        f"(p * p) * ({induction_quotient})",
        "e",
        tag="ftsv_induction_product",
    )
    represented_norm_valuation = _power_valuation_term(
        "p", "x * x + x1 * x1", "e", tag="ftsv_represented_norm"
    )

    return (
        spec(
            TWO_SQUARE_SELF_SQUARE_ZERO_REFLECTS,
            "forall a. a * a = 0 -> a = 0",
            ("mul_eq_zero",),
            (
                "intro a",
                "intro hzero",
                "have hsplit : a = 0 \\/ a = 0",
                "specialize mul_eq_zero a",
                "specialize mul_eq_zero a",
                "apply mul_eq_zero",
                "exact hzero",
                "cases hsplit",
                "exact hsplit_left",
                "exact hsplit_right",
            ),
            "A natural square is zero only when its coordinate is zero.",
        ),
        spec(
            TWO_SQUARE_NORM_ZERO_IFF_COORDINATES_ZERO,
            "forall a b. "
            "((a * a + b * b = 0 -> (a = 0 /\\ b = 0)) /\\ "
            "((a = 0 /\\ b = 0) -> a * a + b * b = 0))",
            (
                "add_eq_zero_left",
                "add_eq_zero_right",
                TWO_SQUARE_SELF_SQUARE_ZERO_REFLECTS,
            ),
            (
                "intro a",
                "intro b",
                "split",
                "intro hzero",
                "split",
                "apply two_square_self_square_zero_reflects",
                "specialize add_eq_zero_left (a * a)",
                "specialize add_eq_zero_left (b * b)",
                "apply add_eq_zero_left",
                "exact hzero",
                "apply two_square_self_square_zero_reflects",
                "specialize add_eq_zero_right (a * a)",
                "specialize add_eq_zero_right (b * b)",
                "apply add_eq_zero_right",
                "exact hzero",
                "intro hcoordinates",
                "cases hcoordinates",
                "simp [hcoordinates_left, hcoordinates_right]",
            ),
            "Zero is an explicit boundary: a two-square norm vanishes exactly "
            "when both natural coordinates vanish.",
        ),
        spec(
            PRIME_POWER_VALUATION_SQUARE_EVEN,
            f"forall p a e E. ({prime_p}) -> ~(a = 0) -> "
            f"({square_input}) -> ({square_output}) -> E = e + e",
            ("prime_power_valuation_mul",),
            (
                "intro p",
                "intro a",
                "intro e",
                "intro E",
                "intro hprime",
                "intro hnonzero",
                "intro hvalue",
                "intro hsquare",
                "specialize prime_power_valuation_mul p",
                "specialize prime_power_valuation_mul a",
                "specialize prime_power_valuation_mul a",
                "specialize prime_power_valuation_mul e",
                "specialize prime_power_valuation_mul e",
                "specialize prime_power_valuation_mul E",
                "apply prime_power_valuation_mul",
                "exact hprime",
                "exact hnonzero",
                "exact hnonzero",
                "exact hvalue",
                "exact hvalue",
                "exact hsquare",
            ),
            "At every prime, the valuation of a nonzero square is exactly "
            "twice the valuation of its coordinate.",
        ),
        spec(
            TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY,
            "forall p u v. (p * u) * (p * u) + (p * v) * (p * v) = "
            "(p * p) * (u * u + v * v)",
            ("mul_shuffle_four", "mul_add"),
            (
                "intro p",
                "intro u",
                "intro v",
                "trans (p * p) * (u * u) + (p * p) * (v * v)",
                "congr",
                "apply mul_shuffle_four",
                "apply mul_shuffle_four",
                "symm",
                "apply mul_add",
            ),
            "A common factor of both coordinates extracts as its exact "
            "square from their two-square norm.",
        ),
        spec(
            TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR,
            f"forall p a b. ({first_divides}) -> ({second_divides}) -> "
            f"({extracted})",
            (TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY,),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro hfirst",
                "intro hsecond",
                "cases hfirst",
                "cases hsecond",
                "exists x",
                "exists x1",
                "split",
                "exact hfirst_witness",
                "split",
                "exact hsecond_witness",
                "rewrite hfirst_witness",
                "rewrite hfirst_witness",
                "rewrite hsecond_witness",
                "rewrite hsecond_witness",
                "apply two_square_common_factor_norm_identity",
            ),
            "Two witnessed coordinate divisors provide both quotient "
            "coordinates and the exact squared-factor norm identity.",
        ),
        spec(
            TWO_SQUARE_COMMON_SQUARED_FACTOR_DIVIDES_NORM,
            f"forall p a b. ({first_divides}) -> ({second_divides}) -> "
            f"({square_divides})",
            (TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR,),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro hfirst",
                "intro hsecond",
                f"have hextraction : {extracted}",
                "specialize two_square_common_divisor_extracts_squared_factor p",
                "specialize two_square_common_divisor_extracts_squared_factor a",
                "specialize two_square_common_divisor_extracts_squared_factor b",
                "apply two_square_common_divisor_extracts_squared_factor",
                "exact hfirst",
                "exact hsecond",
                "cases hextraction",
                "cases hextraction_witness",
                "cases hextraction_witness_witness",
                "cases hextraction_witness_witness_right",
                "exists x * x + x1 * x1",
                "exact hextraction_witness_witness_right_right",
            ),
            "Any common coordinate divisor has its square as an actual "
            "divisor of the two-square norm.",
        ),
        spec(
            TWO_SQUARE_REPRESENTATION_PRESERVED_BY_SQUARE_FACTOR,
            f"forall n z. ({_two_square('n', tag='ftsv_scale_source')}) -> "
            f"({_two_square('n * (z * z)', tag='ftsv_scale_result')})",
            (
                "every_natural_square_is_sum_of_two_squares",
                "two_square_representation_multiplicatively_closed",
            ),
            (
                "intro n",
                "intro z",
                "intro hrepresented",
                f"have hsquare : {_two_square('z * z', tag='ftsv_scale_witness')}",
                "specialize every_natural_square_is_sum_of_two_squares z",
                "exact every_natural_square_is_sum_of_two_squares",
                "specialize two_square_representation_multiplicatively_closed n",
                "specialize two_square_representation_multiplicatively_closed (z * z)",
                "apply two_square_representation_multiplicatively_closed",
                "exact hrepresented",
                "exact hsquare",
            ),
            "Every represented natural remains represented after "
            "multiplication by an arbitrary natural square.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_EXTRACTS_SQUARED_FACTOR,
            f"forall p a b. ({prime_p}) -> ({three_p}) -> "
            f"({norm_divides}) -> ({extracted})",
            (
                "three_mod_four_prime_divides_two_square_norm_divides_both",
                TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR,
            ),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro hprime",
                "intro hthree",
                "intro hnorm",
                f"have hboth : ({first_divides}) /\\ ({second_divides})",
                "specialize three_mod_four_prime_divides_two_square_norm_divides_both p",
                "specialize three_mod_four_prime_divides_two_square_norm_divides_both a",
                "specialize three_mod_four_prime_divides_two_square_norm_divides_both b",
                "apply three_mod_four_prime_divides_two_square_norm_divides_both",
                "exact hprime",
                "exact hthree",
                "exact hnorm",
                "cases hboth",
                "specialize two_square_common_divisor_extracts_squared_factor p",
                "specialize two_square_common_divisor_extracts_squared_factor a",
                "specialize two_square_common_divisor_extracts_squared_factor b",
                "apply two_square_common_divisor_extracts_squared_factor",
                "exact hboth_left",
                "exact hboth_right",
            ),
            "A three-modulo-four prime dividing a two-square norm extracts "
            "as an exact prime square while preserving a represented quotient.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_NONZERO_TWO_SQUARE_NORM_EXTRACTS_NONZERO_QUOTIENT,
            f"forall p a b. ({prime_p}) -> ({three_p}) -> "
            "~(a * a + b * b = 0) -> "
            f"({norm_divides}) -> ({nonzero_extracted})",
            (THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_EXTRACTS_SQUARED_FACTOR,),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro hprime",
                "intro hthree",
                "intro hnonzero",
                "intro hnorm",
                f"have hextraction : {extracted}",
                "specialize three_mod_four_prime_two_square_norm_extracts_squared_factor p",
                "specialize three_mod_four_prime_two_square_norm_extracts_squared_factor a",
                "specialize three_mod_four_prime_two_square_norm_extracts_squared_factor b",
                "apply three_mod_four_prime_two_square_norm_extracts_squared_factor",
                "exact hprime",
                "exact hthree",
                "exact hnorm",
                "cases hextraction",
                "cases hextraction_witness",
                "cases hextraction_witness_witness",
                "cases hextraction_witness_witness_right",
                "exists x",
                "exists x1",
                "split",
                "exact hextraction_witness_witness_left",
                "split",
                "exact hextraction_witness_witness_right_left",
                "split",
                "exact hextraction_witness_witness_right_right",
                "intro hquotient_zero",
                "rewrite hquotient_zero at hextraction_witness_witness_right_right",
                "rewrite PA5 at hextraction_witness_witness_right_right",
                "apply hnonzero",
                "exact hextraction_witness_witness_right_right",
            ),
            "On the explicit nonzero domain, a three-modulo-four prime "
            "square extracts with a nonzero represented quotient.",
        ),
        spec(
            PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT,
            f"forall p z n e f g. ({prime_p}) -> ~(z = 0) -> ~(n = 0) -> "
            f"({shift_factor}) -> ({shift_value}) -> ({shift_product}) -> "
            "g = (e + e) + f",
            (
                "power_valuation_exists",
                PRIME_POWER_VALUATION_SQUARE_EVEN,
                "mul_ne_zero",
                "prime_power_valuation_mul",
            ),
            (
                "intro p",
                "intro z",
                "intro n",
                "intro e",
                "intro f",
                "intro g",
                "intro hprime",
                "intro hfactor_nonzero",
                "intro hvalue_nonzero",
                "intro hfactor",
                "intro hvalue",
                "intro hproduct",
                f"have hsquare : exists E. ({shift_square_witness})",
                "specialize power_valuation_exists p",
                "specialize power_valuation_exists (z * z)",
                "exact power_valuation_exists",
                "cases hsquare",
                "have hdoubled : x = e + e",
                "specialize prime_power_valuation_square_even p",
                "specialize prime_power_valuation_square_even z",
                "specialize prime_power_valuation_square_even e",
                "specialize prime_power_valuation_square_even x",
                "apply prime_power_valuation_square_even",
                "exact hprime",
                "exact hfactor_nonzero",
                "exact hfactor",
                "exact hsquare_witness",
                "have hsquare_nonzero : ~(z * z = 0)",
                "specialize mul_ne_zero z",
                "specialize mul_ne_zero z",
                "intro hsquare_zero",
                "apply mul_ne_zero",
                "exact hfactor_nonzero",
                "exact hfactor_nonzero",
                "exact hsquare_zero",
                "have hshift : g = x + f",
                "specialize prime_power_valuation_mul p",
                "specialize prime_power_valuation_mul (z * z)",
                "specialize prime_power_valuation_mul n",
                "specialize prime_power_valuation_mul x",
                "specialize prime_power_valuation_mul f",
                "specialize prime_power_valuation_mul g",
                "apply prime_power_valuation_mul",
                "exact hprime",
                "exact hsquare_nonzero",
                "exact hvalue_nonzero",
                "exact hsquare_witness",
                "exact hvalue",
                "exact hproduct",
                "rewrite hdoubled at hshift",
                "exact hshift",
            ),
            "Multiplying a nonzero value by a nonzero square increases "
            "its prime valuation by exactly twice the factor valuation.",
        ),
        spec(
            PRIME_POWER_VALUATION_SQUARE_FACTOR_PRESERVES_EVENNESS,
            f"forall p z n e f g k. ({prime_p}) -> ~(z = 0) -> ~(n = 0) -> "
            f"({shift_factor}) -> ({shift_value}) -> ({shift_product}) -> "
            "f = k + k -> exists h. g = h + h",
            (
                PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT,
                "add_shuffle_middle",
            ),
            (
                "intro p",
                "intro z",
                "intro n",
                "intro e",
                "intro f",
                "intro g",
                "intro k",
                "intro hprime",
                "intro hfactor_nonzero",
                "intro hvalue_nonzero",
                "intro hfactor",
                "intro hvalue",
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
                "exact hfactor_nonzero",
                "exact hvalue_nonzero",
                "exact hfactor",
                "exact hvalue",
                "exact hproduct",
                "rewrite heven at hshift",
                "exists e + k",
                "trans (e + e) + (k + k)",
                "exact hshift",
                "apply add_shuffle_middle",
            ),
            "A square-factor valuation step preserves constructive evenness "
            "of a nonzero quotient's prime valuation.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_NONZERO_NORM_POSITIVE_VALUATION_EXTRACTS,
            f"forall p a b e. ({prime_p}) -> ({three_p}) -> "
            "~(a * a + b * b = 0) -> "
            f"({norm_valuation}) -> ~(e = 0) -> ({nonzero_extracted})",
            (
                "power_valuation_nonzero_exponent_divides_base",
                THREE_MOD_FOUR_PRIME_NONZERO_TWO_SQUARE_NORM_EXTRACTS_NONZERO_QUOTIENT,
            ),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro e",
                "intro hprime",
                "intro hthree",
                "intro hnonzero",
                "intro hvaluation",
                "intro hexponent",
                f"have hdivides : {norm_divides}",
                "specialize power_valuation_nonzero_exponent_divides_base p",
                "specialize power_valuation_nonzero_exponent_divides_base (a * a + b * b)",
                "specialize power_valuation_nonzero_exponent_divides_base e",
                "apply power_valuation_nonzero_exponent_divides_base",
                "exact hvaluation",
                "exact hexponent",
                "specialize three_mod_four_prime_nonzero_two_square_norm_extracts_nonzero_quotient p",
                "specialize three_mod_four_prime_nonzero_two_square_norm_extracts_nonzero_quotient a",
                "specialize three_mod_four_prime_nonzero_two_square_norm_extracts_nonzero_quotient b",
                "apply three_mod_four_prime_nonzero_two_square_norm_extracts_nonzero_quotient",
                "exact hprime",
                "exact hthree",
                "exact hnonzero",
                "exact hdivides",
            ),
            "A positive valuation of a nonzero represented norm at a "
            "three-modulo-four prime yields an exact nonzero represented "
            "prime-square quotient.",
        ),
        spec(
            PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES,
            f"forall p q. ({prime_p}) -> ~(q = 0) -> "
            "exists k. k + S q = (p * p) * q",
            (
                "prime_two_le",
                "succ_le_mul_of_two_le_right",
                "prime_nonzero",
                "one_le_of_ne_zero",
                "mul_le_mul_left",
                "mul_one",
                "le_trans",
                "mul_assoc",
                "mul_comm",
            ),
            (
                "intro p",
                "intro q",
                "intro hprime",
                "intro hquotient",
                "have htwo : exists k. k + 2 = p",
                "specialize prime_two_le p",
                "apply prime_two_le",
                "exact hprime",
                "have hfirst : exists k. k + S q = q * p",
                "specialize succ_le_mul_of_two_le_right q",
                "specialize succ_le_mul_of_two_le_right p",
                "apply succ_le_mul_of_two_le_right",
                "exact hquotient",
                "exact htwo",
                "have hpnonzero : ~(p = 0)",
                "specialize prime_nonzero p",
                "intro hpzero",
                "apply prime_nonzero",
                "exact hprime",
                "exact hpzero",
                "have hone : exists k. k + 1 = p",
                "specialize one_le_of_ne_zero p",
                "apply one_le_of_ne_zero",
                "exact hpnonzero",
                "have hsecond : exists k. k + (q * p) * 1 = (q * p) * p",
                "specialize mul_le_mul_left 1",
                "specialize mul_le_mul_left p",
                "specialize mul_le_mul_left (q * p)",
                "apply mul_le_mul_left",
                "exact hone",
                "specialize mul_one (q * p)",
                "rewrite mul_one at hsecond",
                "have hcombined : exists k. k + S q = (q * p) * p",
                "specialize le_trans (S q)",
                "specialize le_trans (q * p)",
                "specialize le_trans ((q * p) * p)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
                "cases hcombined",
                "exists x",
                "trans (q * p) * p",
                "exact hcombined_witness",
                "trans q * (p * p)",
                "apply mul_assoc",
                "apply mul_comm",
            ),
            "Multiplication of a nonzero natural by a prime square is "
            "strictly increasing in witnessed constructive order.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN_BOUNDED,
            f"forall B p a b e. ({bound}) -> ({prime_p}) -> ({three_p}) -> "
            "~(a * a + b * b = 0) -> "
            f"({norm_valuation}) -> exists h. e = h + h",
            (
                "le_zero",
                "eq_decidable",
                THREE_MOD_FOUR_PRIME_NONZERO_NORM_POSITIVE_VALUATION_EXTRACTS,
                PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES,
                "le_trans",
                "le_of_succ_le_succ",
                "power_valuation_exists",
                "prime_nonzero",
                "power_valuation_value_eq_transport",
                PRIME_POWER_VALUATION_SQUARE_FACTOR_PRESERVES_EVENNESS,
            ),
            (
                "intro B",
                "induction B",
                "intro p",
                "intro a",
                "intro b",
                "intro e",
                "intro hbound",
                "intro hprime",
                "intro hthree",
                "intro hnonzero",
                "intro hvaluation",
                "exfalso",
                "apply hnonzero",
                "specialize le_zero (a * a + b * b)",
                "apply le_zero",
                "exact hbound",
                "intro p",
                "intro a",
                "intro b",
                "intro e",
                "intro hbound",
                "intro hprime",
                "intro hthree",
                "intro hnonzero",
                "intro hvaluation",
                "have hcases : e = 0 \\/ ~(e = 0)",
                "specialize eq_decidable e",
                "specialize eq_decidable 0",
                "exact eq_decidable",
                "cases hcases",
                "exists 0",
                "rewrite hcases_left",
                "simp",
                f"have hextraction : {nonzero_extracted}",
                "specialize three_mod_four_prime_nonzero_norm_positive_valuation_extracts p",
                "specialize three_mod_four_prime_nonzero_norm_positive_valuation_extracts a",
                "specialize three_mod_four_prime_nonzero_norm_positive_valuation_extracts b",
                "specialize three_mod_four_prime_nonzero_norm_positive_valuation_extracts e",
                "apply three_mod_four_prime_nonzero_norm_positive_valuation_extracts",
                "exact hprime",
                "exact hthree",
                "exact hnonzero",
                "exact hvaluation",
                "exact hcases_right",
                "cases hextraction",
                "cases hextraction_witness",
                "cases hextraction_witness_witness",
                "cases hextraction_witness_witness_right",
                "cases hextraction_witness_witness_right_right",
                f"have hstrict : exists k. k + S ({induction_quotient}) = "
                f"(p * p) * ({induction_quotient})",
                "specialize prime_square_times_nonzero_strictly_increases p",
                f"specialize prime_square_times_nonzero_strictly_increases ({induction_quotient})",
                "apply prime_square_times_nonzero_strictly_increases",
                "exact hprime",
                "exact hextraction_witness_witness_right_right_right",
                "rewrite <- hextraction_witness_witness_right_right_left at hstrict",
                f"have hsuccessor_bound : exists k. k + S ({induction_quotient}) = S B",
                f"specialize le_trans (S ({induction_quotient}))",
                "specialize le_trans (a * a + b * b)",
                "specialize le_trans (S B)",
                "apply le_trans",
                "exact hstrict",
                "exact hbound",
                f"have hquotient_bound : exists k. k + ({induction_quotient}) = B",
                f"specialize le_of_succ_le_succ ({induction_quotient})",
                "specialize le_of_succ_le_succ B",
                "apply le_of_succ_le_succ",
                "exact hsuccessor_bound",
                f"have hquotient_valuation : exists f. ({induction_quotient_valuation})",
                "apply power_valuation_exists",
                "cases hquotient_valuation",
                "have hquotient_even : exists h. x2 = h + h",
                "specialize IH p",
                "specialize IH x",
                "specialize IH x1",
                "specialize IH x2",
                "apply IH",
                "exact hquotient_bound",
                "exact hprime",
                "exact hthree",
                "exact hextraction_witness_witness_right_right_right",
                "exact hquotient_valuation_witness",
                "cases hquotient_even",
                f"have hprime_valuation : exists r. ({induction_prime_valuation})",
                "apply power_valuation_exists",
                "cases hprime_valuation",
                "have hpnonzero : ~(p = 0)",
                "specialize prime_nonzero p",
                "intro hpzero",
                "apply prime_nonzero",
                "exact hprime",
                "exact hpzero",
                f"have hproduct_valuation : {induction_product_valuation}",
                "specialize power_valuation_value_eq_transport p",
                "specialize power_valuation_value_eq_transport (a * a + b * b)",
                f"specialize power_valuation_value_eq_transport ((p * p) * ({induction_quotient}))",
                "specialize power_valuation_value_eq_transport e",
                "apply power_valuation_value_eq_transport",
                "exact hextraction_witness_witness_right_right_left",
                "exact hvaluation",
                "specialize prime_power_valuation_square_factor_preserves_evenness p",
                "specialize prime_power_valuation_square_factor_preserves_evenness p",
                f"specialize prime_power_valuation_square_factor_preserves_evenness ({induction_quotient})",
                "specialize prime_power_valuation_square_factor_preserves_evenness x4",
                "specialize prime_power_valuation_square_factor_preserves_evenness x2",
                "specialize prime_power_valuation_square_factor_preserves_evenness e",
                "specialize prime_power_valuation_square_factor_preserves_evenness x3",
                "apply prime_power_valuation_square_factor_preserves_evenness",
                "exact hprime",
                "exact hpnonzero",
                "exact hextraction_witness_witness_right_right_right",
                "exact hprime_valuation_witness",
                "exact hquotient_valuation_witness",
                "exact hproduct_valuation",
                "exact hquotient_even_witness",
            ),
            "Bounded natural induction proves that a three-modulo-four "
            "prime has even valuation in every nonzero represented norm "
            "below the bound.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN,
            f"forall p a b e. ({prime_p}) -> ({three_p}) -> "
            "~(a * a + b * b = 0) -> "
            f"({norm_valuation}) -> exists h. e = h + h",
            (
                "le_refl",
                THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN_BOUNDED,
            ),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro e",
                "intro hprime",
                "intro hthree",
                "intro hnonzero",
                "intro hvaluation",
                "specialize three_mod_four_prime_two_square_norm_valuation_even_bounded (a * a + b * b)",
                "specialize three_mod_four_prime_two_square_norm_valuation_even_bounded p",
                "specialize three_mod_four_prime_two_square_norm_valuation_even_bounded a",
                "specialize three_mod_four_prime_two_square_norm_valuation_even_bounded b",
                "specialize three_mod_four_prime_two_square_norm_valuation_even_bounded e",
                "apply three_mod_four_prime_two_square_norm_valuation_even_bounded",
                "specialize le_refl (a * a + b * b)",
                "exact le_refl",
                "exact hprime",
                "exact hthree",
                "exact hnonzero",
                "exact hvaluation",
            ),
            "Every three-modulo-four prime has a constructively even "
            "valuation in every explicitly nonzero two-square norm.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_REPRESENTED_NONZERO_VALUATION_EVEN,
            f"forall p n e. ({prime_p}) -> ({three_p}) -> ~(n = 0) -> "
            f"({_two_square('n', tag='ftsv_represented_source')}) -> "
            f"({represented_valuation}) -> exists h. e = h + h",
            (
                "power_valuation_value_eq_transport",
                THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN,
            ),
            (
                "intro p",
                "intro n",
                "intro e",
                "intro hprime",
                "intro hthree",
                "intro hnonzero",
                "intro hrepresented",
                "intro hvaluation",
                "cases hrepresented",
                "cases hrepresented_witness",
                "have hnorm_nonzero : ~(x * x + x1 * x1 = 0)",
                "intro hzero",
                "apply hnonzero",
                "trans x * x + x1 * x1",
                "exact hrepresented_witness_witness",
                "exact hzero",
                f"have hnorm_valuation : {represented_norm_valuation}",
                "specialize power_valuation_value_eq_transport p",
                "specialize power_valuation_value_eq_transport n",
                "specialize power_valuation_value_eq_transport (x * x + x1 * x1)",
                "specialize power_valuation_value_eq_transport e",
                "apply power_valuation_value_eq_transport",
                "exact hrepresented_witness_witness",
                "exact hvaluation",
                "specialize three_mod_four_prime_two_square_norm_valuation_even p",
                "specialize three_mod_four_prime_two_square_norm_valuation_even x",
                "specialize three_mod_four_prime_two_square_norm_valuation_even x1",
                "specialize three_mod_four_prime_two_square_norm_valuation_even e",
                "apply three_mod_four_prime_two_square_norm_valuation_even",
                "exact hprime",
                "exact hthree",
                "exact hnorm_nonzero",
                "exact hnorm_valuation",
            ),
            "Necessity direction: every prime congruent to three modulo four "
            "has an explicitly even valuation in any represented nonzero natural.",
        ),
    )


__all__ = [
    "PRIME_POWER_VALUATION_SQUARE_EVEN",
    "PRIME_POWER_VALUATION_SQUARE_FACTOR_PRESERVES_EVENNESS",
    "PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT",
    "PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES",
    "THREE_MOD_FOUR_PRIME_NONZERO_NORM_POSITIVE_VALUATION_EXTRACTS",
    "THREE_MOD_FOUR_PRIME_NONZERO_TWO_SQUARE_NORM_EXTRACTS_NONZERO_QUOTIENT",
    "THREE_MOD_FOUR_PRIME_REPRESENTED_NONZERO_VALUATION_EVEN",
    "THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_EXTRACTS_SQUARED_FACTOR",
    "THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN",
    "THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN_BOUNDED",
    "TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR",
    "TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY",
    "TWO_SQUARE_COMMON_SQUARED_FACTOR_DIVIDES_NORM",
    "TWO_SQUARE_NORM_ZERO_IFF_COORDINATES_ZERO",
    "TWO_SQUARE_REPRESENTATION_PRESERVED_BY_SQUARE_FACTOR",
    "TWO_SQUARE_SELF_SQUARE_ZERO_REFLECTS",
    "make_fermat_two_squares_valuation_candidate_theorems",
]
