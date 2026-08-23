"""Constructive primitive Euclidean triples over unchanged first-order HA.

Every parity and coprimality relation is expanded into ordinary arithmetic.
The main endpoint proves the *forward* primitive Euclidean parametrization
from witnessed order, coprime parameters, and opposite parameter parity.  It
does not infer the inverse parametrization or Fermat's unproved descent step.
"""

from __future__ import annotations

from typing import Any, Callable

from .pythagorean_fermat_four_candidate import (
    coprime_coordinates,
    primitive_pythagorean,
    pythagorean_triple,
)


PYTHAGOREAN_PARAMETER_EVEN_SQUARE = "pythagorean_parameter_even_square"
PYTHAGOREAN_PARAMETER_ODD_SQUARE = "pythagorean_parameter_odd_square"
PYTHAGOREAN_EVEN_ODD_SQUARE_GAP_ODD = "pythagorean_even_odd_square_gap_odd"
PYTHAGOREAN_ODD_EVEN_SQUARE_GAP_ODD = "pythagorean_odd_even_square_gap_odd"
PYTHAGOREAN_OPPOSITE_PARITY_SQUARE_GAP_ODD = (
    "pythagorean_opposite_parity_square_gap_odd"
)
PYTHAGOREAN_OPPOSITE_PARITY_HYPOTENUSE_ODD = (
    "pythagorean_opposite_parity_hypotenuse_odd"
)
PYTHAGOREAN_ODD_COORDINATE_COPRIME_TWO = (
    "pythagorean_odd_coordinate_coprime_two"
)
PYTHAGOREAN_PARAMETER_DIVISOR_DIVIDES_SQUARE = (
    "pythagorean_parameter_divisor_divides_square"
)
PYTHAGOREAN_SQUARE_GAP_COPRIME_FIRST_PARAMETER = (
    "pythagorean_square_gap_coprime_first_parameter"
)
PYTHAGOREAN_SQUARE_GAP_COPRIME_SECOND_PARAMETER = (
    "pythagorean_square_gap_coprime_second_parameter"
)
PYTHAGOREAN_SQUARE_GAP_COPRIME_PARAMETER_PRODUCT = (
    "pythagorean_square_gap_coprime_parameter_product"
)
PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_LEGS = "pythagorean_primitive_euclidean_legs"
PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_CONSTRUCTOR = (
    "pythagorean_primitive_euclidean_constructor"
)
PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_FROM_ORDER = (
    "pythagorean_primitive_euclidean_from_order"
)
PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_SWAPPED_CONSTRUCTOR = (
    "pythagorean_primitive_euclidean_swapped_constructor"
)
PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_COPRIME_FIRST_LEG = (
    "pythagorean_primitive_hypotenuse_coprime_first_leg"
)
PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_COPRIME_SECOND_LEG = (
    "pythagorean_primitive_hypotenuse_coprime_second_leg"
)
PYTHAGOREAN_PRIMITIVE_PAIRWISE_COPRIME = "pythagorean_primitive_pairwise_coprime"
PYTHAGOREAN_PRIMITIVE_LEGS_NOT_BOTH_EVEN = (
    "pythagorean_primitive_legs_not_both_even"
)
PYTHAGOREAN_ODD_SQUARE_PAIR_TWO_MOD_FOUR = (
    "pythagorean_odd_square_pair_two_mod_four"
)
PYTHAGOREAN_TWO_MOD_FOUR_NOT_SQUARE = "pythagorean_two_mod_four_not_square"
PYTHAGOREAN_TRIPLE_LEGS_NOT_BOTH_ODD = "pythagorean_triple_legs_not_both_odd"
PYTHAGOREAN_COORDINATE_PARITY_CHOICE = "pythagorean_coordinate_parity_choice"
PYTHAGOREAN_PRIMITIVE_LEGS_OPPOSITE_PARITY = (
    "pythagorean_primitive_legs_opposite_parity"
)
PYTHAGOREAN_ODD_SQUARE_HAS_ODD_ROOT = "pythagorean_odd_square_has_odd_root"
PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_ODD = "pythagorean_primitive_hypotenuse_odd"
PYTHAGOREAN_PRIMITIVE_NORMAL_FORM = "pythagorean_primitive_normal_form"


def even_coordinate(value: str, *, tag: str) -> str:
    """Express an explicitly witnessed even natural without a new predicate."""

    witness = f"pp_even_{tag}"
    return f"exists {witness}. ({value}) = 2 * {witness}"


def odd_coordinate(value: str, *, tag: str) -> str:
    """Express an explicitly witnessed odd natural without a new predicate."""

    witness = f"pp_odd_{tag}"
    return f"exists {witness}. ({value}) = 2 * {witness} + 1"


def opposite_parity(first: str, second: str, *, tag: str) -> str:
    """Expand both witnessed orientations of opposite natural parity."""

    first_even = even_coordinate(first, tag=f"{tag}_first_even")
    second_odd = odd_coordinate(second, tag=f"{tag}_second_odd")
    first_odd = odd_coordinate(first, tag=f"{tag}_first_odd")
    second_even = even_coordinate(second, tag=f"{tag}_second_even")
    return (
        f"((({first_even}) /\\ ({second_odd})) \\/ "
        f"(({first_odd}) /\\ ({second_even})))"
    )


def make_pythagorean_primitive_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build actual curried HA proof bodies for primitive Euclidean triples."""

    parameters_coprime = coprime_coordinates("m", "n", tag="primitive_parameters")
    parameters_opposite = opposite_parity("m", "n", tag="primitive_parameters")
    first_gap_coprime = coprime_coordinates("d", "m", tag="gap_first_result")
    second_gap_coprime = coprime_coordinates("d", "n", tag="gap_second_result")
    product_gap_coprime = coprime_coordinates(
        "d", "m * n", tag="gap_product_result"
    )
    euclidean_legs_coprime = coprime_coordinates(
        "d", "2 * (m * n)", tag="euclidean_legs"
    )
    euclidean_primitive = primitive_pythagorean(
        "d", "2 * (m * n)", "m * m + n * n", tag="euclidean_result"
    )
    euclidean_swapped = primitive_pythagorean(
        "2 * (m * n)", "d", "m * m + n * n", tag="euclidean_swapped"
    )
    primitive = primitive_pythagorean("x", "y", "z", tag="pairwise_source")
    first_hypotenuse_coprime = coprime_coordinates(
        "x", "z", tag="first_hypotenuse_result"
    )
    second_hypotenuse_coprime = coprime_coordinates(
        "y", "z", tag="second_hypotenuse_result"
    )
    return (
        spec(
            PYTHAGOREAN_PARAMETER_EVEN_SQUARE,
            "forall m. (exists q. m = 2 * q) -> exists q. m * m = 2 * q",
            ("even_mul_left",),
            (
                "intro m",
                "intro heven",
                "specialize even_mul_left m",
                "specialize even_mul_left m",
                "apply even_mul_left",
                "exact heven",
            ),
            "The square of a witnessed even Euclidean parameter has an explicit even half.",
        ),
        spec(
            PYTHAGOREAN_PARAMETER_ODD_SQUARE,
            "forall m. (exists q. m = 2 * q + 1) -> "
            "exists q. m * m = 2 * q + 1",
            ("odd_mul_odd",),
            (
                "intro m",
                "intro hodd",
                "specialize odd_mul_odd m",
                "specialize odd_mul_odd m",
                "apply odd_mul_odd",
                "exact hodd",
                "exact hodd",
            ),
            "The square of a witnessed odd Euclidean parameter has an explicit odd half.",
        ),
        spec(
            PYTHAGOREAN_EVEN_ODD_SQUARE_GAP_ODD,
            "forall m n d. m * m = n * n + d -> "
            "(exists a. m = 2 * a) -> (exists b. n = 2 * b + 1) -> "
            "exists q. d = 2 * q + 1",
            (
                PYTHAGOREAN_PARAMETER_EVEN_SQUARE,
                PYTHAGOREAN_PARAMETER_ODD_SQUARE,
                "parity_cases",
                "odd_add_even",
                "even_odd_exclusive_pointwise",
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "intro hmeven",
                "intro hnodd",
                "have hmsquare : exists q. m * m = 2 * q",
                "apply pythagorean_parameter_even_square",
                "exact hmeven",
                "have hnsquare : exists q. n * n = 2 * q + 1",
                "apply pythagorean_parameter_odd_square",
                "exact hnodd",
                "specialize parity_cases d",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exfalso",
                "have hsumodd : exists q. n * n + d = 2 * q + 1",
                "specialize odd_add_even (n * n)",
                "specialize odd_add_even d",
                "apply odd_add_even",
                "exact hnsquare",
                "exists x",
                "exact parity_cases_witness_left",
                "cases hmsquare",
                "cases hsumodd",
                "specialize even_odd_exclusive_pointwise (m * m)",
                "specialize even_odd_exclusive_pointwise x1",
                "specialize even_odd_exclusive_pointwise x2",
                "apply even_odd_exclusive_pointwise",
                "exact hmsquare_witness",
                "trans n * n + d",
                "exact hgap",
                "exact hsumodd_witness",
                "exists x",
                "exact parity_cases_witness_right",
            ),
            "An even first parameter and odd second parameter force their witnessed square difference to be odd.",
        ),
        spec(
            PYTHAGOREAN_ODD_EVEN_SQUARE_GAP_ODD,
            "forall m n d. m * m = n * n + d -> "
            "(exists a. m = 2 * a + 1) -> (exists b. n = 2 * b) -> "
            "exists q. d = 2 * q + 1",
            (
                PYTHAGOREAN_PARAMETER_ODD_SQUARE,
                PYTHAGOREAN_PARAMETER_EVEN_SQUARE,
                "parity_cases",
                "even_add_even",
                "even_odd_exclusive_pointwise",
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "intro hmodd",
                "intro hneven",
                "have hmsquare : exists q. m * m = 2 * q + 1",
                "apply pythagorean_parameter_odd_square",
                "exact hmodd",
                "have hnsquare : exists q. n * n = 2 * q",
                "apply pythagorean_parameter_even_square",
                "exact hneven",
                "specialize parity_cases d",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exfalso",
                "have hsumeven : exists q. n * n + d = 2 * q",
                "specialize even_add_even (n * n)",
                "specialize even_add_even d",
                "apply even_add_even",
                "exact hnsquare",
                "exists x",
                "exact parity_cases_witness_left",
                "cases hsumeven",
                "cases hmsquare",
                "specialize even_odd_exclusive_pointwise (m * m)",
                "specialize even_odd_exclusive_pointwise x1",
                "specialize even_odd_exclusive_pointwise x2",
                "apply even_odd_exclusive_pointwise",
                "trans n * n + d",
                "exact hgap",
                "exact hsumeven_witness",
                "exact hmsquare_witness",
                "exists x",
                "exact parity_cases_witness_right",
            ),
            "An odd first parameter and even second parameter force their witnessed square difference to be odd.",
        ),
        spec(
            PYTHAGOREAN_OPPOSITE_PARITY_SQUARE_GAP_ODD,
            f"forall m n d. m * m = n * n + d -> "
            f"({parameters_opposite}) -> exists q. d = 2 * q + 1",
            (
                PYTHAGOREAN_EVEN_ODD_SQUARE_GAP_ODD,
                PYTHAGOREAN_ODD_EVEN_SQUARE_GAP_ODD,
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "intro hopposite",
                "cases hopposite",
                "cases hopposite_left",
                "apply pythagorean_even_odd_square_gap_odd",
                "exact hgap",
                "exact hopposite_left_left",
                "exact hopposite_left_right",
                "cases hopposite_right",
                "apply pythagorean_odd_even_square_gap_odd",
                "exact hgap",
                "exact hopposite_right_left",
                "exact hopposite_right_right",
            ),
            "Opposite-parity Euclidean parameters force the subtraction-free square-difference leg to be odd in either parity orientation.",
        ),
        spec(
            PYTHAGOREAN_OPPOSITE_PARITY_HYPOTENUSE_ODD,
            f"forall m n. ({parameters_opposite}) -> "
            "exists q. m * m + n * n = 2 * q + 1",
            (
                PYTHAGOREAN_PARAMETER_EVEN_SQUARE,
                PYTHAGOREAN_PARAMETER_ODD_SQUARE,
                "even_add_odd",
                "odd_add_even",
            ),
            (
                "intro m",
                "intro n",
                "intro hopposite",
                "cases hopposite",
                "cases hopposite_left",
                "specialize even_add_odd (m * m)",
                "specialize even_add_odd (n * n)",
                "apply even_add_odd",
                "apply pythagorean_parameter_even_square",
                "exact hopposite_left_left",
                "apply pythagorean_parameter_odd_square",
                "exact hopposite_left_right",
                "cases hopposite_right",
                "specialize odd_add_even (m * m)",
                "specialize odd_add_even (n * n)",
                "apply odd_add_even",
                "apply pythagorean_parameter_odd_square",
                "exact hopposite_right_left",
                "apply pythagorean_parameter_even_square",
                "exact hopposite_right_right",
            ),
            "The Euclidean hypotenuse is explicitly odd whenever its two parameters have opposite parity.",
        ),
        spec(
            PYTHAGOREAN_ODD_COORDINATE_COPRIME_TWO,
            f"forall d. (exists q. d = 2 * q + 1) -> "
            f"({coprime_coordinates('d', '2', tag='odd_two_result')})",
            (
                "even_odd_exclusive_pointwise",
                "prime_two",
                "prime_not_divides_coprime",
                "coprime_symm",
            ),
            (
                "intro d",
                "intro hodd",
                "have hnot : ~(exists q. d = 2 * q)",
                "intro heven",
                "cases heven",
                "cases hodd",
                "specialize even_odd_exclusive_pointwise d",
                "specialize even_odd_exclusive_pointwise x",
                "specialize even_odd_exclusive_pointwise x1",
                "apply even_odd_exclusive_pointwise",
                "exact heven_witness",
                "exact hodd_witness",
                f"have htwo : {coprime_coordinates('2', 'd', tag='odd_two_local')}",
                "specialize prime_not_divides_coprime 2",
                "specialize prime_not_divides_coprime d",
                "apply prime_not_divides_coprime",
                "exact prime_two",
                "exact hnot",
                "specialize coprime_symm 2",
                "specialize coprime_symm d",
                "apply coprime_symm",
                "exact htwo",
            ),
            "Every witnessed odd natural is coprime to two, using the actual prime-two theorem and constructive prime nondivisibility.",
        ),
        spec(
            PYTHAGOREAN_PARAMETER_DIVISOR_DIVIDES_SQUARE,
            "forall c a. (exists q. a = c * q) -> exists q. a * a = c * q",
            ("multiple_mul_right",),
            (
                "intro c",
                "intro a",
                "intro hfactor",
                "specialize multiple_mul_right c",
                "specialize multiple_mul_right a",
                "specialize multiple_mul_right a",
                "apply multiple_mul_right",
                "exact hfactor",
            ),
            "Every explicitly witnessed divisor of a parameter also divides its natural square.",
        ),
        spec(
            PYTHAGOREAN_SQUARE_GAP_COPRIME_FIRST_PARAMETER,
            f"forall m n d. m * m = n * n + d -> "
            f"({parameters_coprime}) -> ({first_gap_coprime})",
            (
                PYTHAGOREAN_PARAMETER_DIVISOR_DIVIDES_SQUARE,
                "divides_remainder",
                "mul_one",
                "add_comm",
                "coprime_mul_right",
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "intro hcoprime",
                "intro divisor",
                "intro hd",
                "intro hm",
                "have hmsquare : exists q. m * m = divisor * q",
                "specialize pythagorean_parameter_divisor_divides_square divisor",
                "specialize pythagorean_parameter_divisor_divides_square m",
                "apply pythagorean_parameter_divisor_divides_square",
                "exact hm",
                "have hnsquare : exists q. n * n = divisor * q",
                "specialize divides_remainder divisor",
                "specialize divides_remainder (m * m)",
                "specialize divides_remainder d",
                "specialize divides_remainder 1",
                "specialize divides_remainder (n * n)",
                "apply divides_remainder",
                "exact hmsquare",
                "exact hd",
                "specialize mul_one d",
                "rewrite mul_one",
                "trans n * n + d",
                "exact hgap",
                "apply add_comm",
                f"have hsquarecop : {coprime_coordinates('m', 'n * n', tag='first_square_local')}",
                "specialize coprime_mul_right m",
                "specialize coprime_mul_right n",
                "specialize coprime_mul_right n",
                "apply coprime_mul_right",
                "exact hcoprime",
                "exact hcoprime",
                "specialize hsquarecop divisor",
                "apply hsquarecop",
                "exact hm",
                "exact hnsquare",
            ),
            "A square-difference leg is coprime to the first Euclidean parameter whenever the parameters themselves are coprime.",
        ),
        spec(
            PYTHAGOREAN_SQUARE_GAP_COPRIME_SECOND_PARAMETER,
            f"forall m n d. m * m = n * n + d -> "
            f"({parameters_coprime}) -> ({second_gap_coprime})",
            (
                PYTHAGOREAN_PARAMETER_DIVISOR_DIVIDES_SQUARE,
                "multiple_add",
                "coprime_symm",
                "coprime_mul_right",
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "intro hcoprime",
                "intro divisor",
                "intro hd",
                "intro hn",
                "have hnsquare : exists q. n * n = divisor * q",
                "specialize pythagorean_parameter_divisor_divides_square divisor",
                "specialize pythagorean_parameter_divisor_divides_square n",
                "apply pythagorean_parameter_divisor_divides_square",
                "exact hn",
                "have hmsquare : exists q. m * m = divisor * q",
                "rewrite hgap",
                "specialize multiple_add divisor",
                "specialize multiple_add (n * n)",
                "specialize multiple_add d",
                "apply multiple_add",
                "exact hnsquare",
                "exact hd",
                f"have hreverse : {coprime_coordinates('n', 'm', tag='second_reverse_local')}",
                "specialize coprime_symm m",
                "specialize coprime_symm n",
                "apply coprime_symm",
                "exact hcoprime",
                f"have hsquarecop : {coprime_coordinates('n', 'm * m', tag='second_square_local')}",
                "specialize coprime_mul_right n",
                "specialize coprime_mul_right m",
                "specialize coprime_mul_right m",
                "apply coprime_mul_right",
                "exact hreverse",
                "exact hreverse",
                "specialize hsquarecop divisor",
                "apply hsquarecop",
                "exact hn",
                "exact hmsquare",
            ),
            "A square-difference leg is coprime to the second Euclidean parameter whenever the parameters themselves are coprime.",
        ),
        spec(
            PYTHAGOREAN_SQUARE_GAP_COPRIME_PARAMETER_PRODUCT,
            f"forall m n d. m * m = n * n + d -> "
            f"({parameters_coprime}) -> ({product_gap_coprime})",
            (
                PYTHAGOREAN_SQUARE_GAP_COPRIME_FIRST_PARAMETER,
                PYTHAGOREAN_SQUARE_GAP_COPRIME_SECOND_PARAMETER,
                "coprime_mul_right",
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "intro hcoprime",
                "specialize coprime_mul_right d",
                "specialize coprime_mul_right m",
                "specialize coprime_mul_right n",
                "apply coprime_mul_right",
                "specialize pythagorean_square_gap_coprime_first_parameter m",
                "specialize pythagorean_square_gap_coprime_first_parameter n",
                "specialize pythagorean_square_gap_coprime_first_parameter d",
                "apply pythagorean_square_gap_coprime_first_parameter",
                "exact hgap",
                "exact hcoprime",
                "specialize pythagorean_square_gap_coprime_second_parameter m",
                "specialize pythagorean_square_gap_coprime_second_parameter n",
                "specialize pythagorean_square_gap_coprime_second_parameter d",
                "apply pythagorean_square_gap_coprime_second_parameter",
                "exact hgap",
                "exact hcoprime",
            ),
            "A square-difference leg is coprime to the complete Euclidean parameter product.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_LEGS,
            f"forall m n d. m * m = n * n + d -> "
            f"({parameters_coprime}) -> ({parameters_opposite}) -> "
            f"({euclidean_legs_coprime})",
            (
                PYTHAGOREAN_OPPOSITE_PARITY_SQUARE_GAP_ODD,
                PYTHAGOREAN_ODD_COORDINATE_COPRIME_TWO,
                PYTHAGOREAN_SQUARE_GAP_COPRIME_PARAMETER_PRODUCT,
                "coprime_mul_right",
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "intro hcoprime",
                "intro hopposite",
                "have hodd : exists q. d = 2 * q + 1",
                "specialize pythagorean_opposite_parity_square_gap_odd m",
                "specialize pythagorean_opposite_parity_square_gap_odd n",
                "specialize pythagorean_opposite_parity_square_gap_odd d",
                "apply pythagorean_opposite_parity_square_gap_odd",
                "exact hgap",
                "exact hopposite",
                "specialize coprime_mul_right d",
                "specialize coprime_mul_right 2",
                "specialize coprime_mul_right (m * n)",
                "apply coprime_mul_right",
                "specialize pythagorean_odd_coordinate_coprime_two d",
                "apply pythagorean_odd_coordinate_coprime_two",
                "exact hodd",
                "specialize pythagorean_square_gap_coprime_parameter_product m",
                "specialize pythagorean_square_gap_coprime_parameter_product n",
                "specialize pythagorean_square_gap_coprime_parameter_product d",
                "apply pythagorean_square_gap_coprime_parameter_product",
                "exact hgap",
                "exact hcoprime",
            ),
            "Coprime opposite-parity Euclidean parameters yield genuinely coprime square-difference and doubled-product legs.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_CONSTRUCTOR,
            f"forall m n d. m * m = n * n + d -> "
            f"({parameters_coprime}) -> ({parameters_opposite}) -> "
            f"({euclidean_primitive})",
            (
                "pythagorean_euclidean_identity",
                PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_LEGS,
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "intro hcoprime",
                "intro hopposite",
                "split",
                "specialize pythagorean_euclidean_identity m",
                "specialize pythagorean_euclidean_identity n",
                "specialize pythagorean_euclidean_identity d",
                "apply pythagorean_euclidean_identity",
                "exact hgap",
                "specialize pythagorean_primitive_euclidean_legs m",
                "specialize pythagorean_primitive_euclidean_legs n",
                "specialize pythagorean_primitive_euclidean_legs d",
                "apply pythagorean_primitive_euclidean_legs",
                "exact hgap",
                "exact hcoprime",
                "exact hopposite",
            ),
            "The complete forward primitive Euclid constructor proves both the exact Pythagorean identity and coprimality of its two displayed legs.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_FROM_ORDER,
            f"forall m n. (exists gap. gap + n = m) -> "
            f"({parameters_coprime}) -> ({parameters_opposite}) -> "
            f"exists d. ({euclidean_primitive})",
            (
                "pythagorean_square_gap_from_order",
                PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_CONSTRUCTOR,
            ),
            (
                "intro m",
                "intro n",
                "intro horder",
                "intro hcoprime",
                "intro hopposite",
                "have hgap : exists d. m * m = n * n + d",
                "specialize pythagorean_square_gap_from_order m",
                "specialize pythagorean_square_gap_from_order n",
                "apply pythagorean_square_gap_from_order",
                "exact horder",
                "cases hgap",
                "exists x",
                "specialize pythagorean_primitive_euclidean_constructor m",
                "specialize pythagorean_primitive_euclidean_constructor n",
                "specialize pythagorean_primitive_euclidean_constructor x",
                "apply pythagorean_primitive_euclidean_constructor",
                "exact hgap_witness",
                "exact hcoprime",
                "exact hopposite",
            ),
            "Every witnessed ordered pair of coprime opposite-parity natural parameters constructs an actual primitive Euclidean Pythagorean triple.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_SWAPPED_CONSTRUCTOR,
            f"forall m n d. m * m = n * n + d -> "
            f"({parameters_coprime}) -> ({parameters_opposite}) -> "
            f"({euclidean_swapped})",
            (
                PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_CONSTRUCTOR,
                "pythagorean_primitive_leg_swap",
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "intro hcoprime",
                "intro hopposite",
                "specialize pythagorean_primitive_leg_swap d",
                "specialize pythagorean_primitive_leg_swap (2 * (m * n))",
                "specialize pythagorean_primitive_leg_swap (m * m + n * n)",
                "apply pythagorean_primitive_leg_swap",
                "specialize pythagorean_primitive_euclidean_constructor m",
                "specialize pythagorean_primitive_euclidean_constructor n",
                "specialize pythagorean_primitive_euclidean_constructor d",
                "apply pythagorean_primitive_euclidean_constructor",
                "exact hgap",
                "exact hcoprime",
                "exact hopposite",
            ),
            "The complete forward primitive Euclid constructor is valid in either leg orientation.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_COPRIME_FIRST_LEG,
            f"forall x y z. ({primitive}) -> ({first_hypotenuse_coprime})",
            (
                PYTHAGOREAN_PARAMETER_DIVISOR_DIVIDES_SQUARE,
                "divides_remainder",
                "mul_one",
                "coprime_mul_right",
            ),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro hprimitive",
                "cases hprimitive",
                "intro divisor",
                "intro hx",
                "intro hz",
                "have hxsquare : exists q. x * x = divisor * q",
                "specialize pythagorean_parameter_divisor_divides_square divisor",
                "specialize pythagorean_parameter_divisor_divides_square x",
                "apply pythagorean_parameter_divisor_divides_square",
                "exact hx",
                "have hzsquare : exists q. z * z = divisor * q",
                "specialize pythagorean_parameter_divisor_divides_square divisor",
                "specialize pythagorean_parameter_divisor_divides_square z",
                "apply pythagorean_parameter_divisor_divides_square",
                "exact hz",
                "have hysquare : exists q. y * y = divisor * q",
                "specialize divides_remainder divisor",
                "specialize divides_remainder (z * z)",
                "specialize divides_remainder (x * x)",
                "specialize divides_remainder 1",
                "specialize divides_remainder (y * y)",
                "apply divides_remainder",
                "exact hzsquare",
                "exact hxsquare",
                "specialize mul_one (x * x)",
                "rewrite mul_one",
                "symm",
                "exact hprimitive_left",
                f"have hsquarecop : {coprime_coordinates('x', 'y * y', tag='hypotenuse_first_square')}",
                "specialize coprime_mul_right x",
                "specialize coprime_mul_right y",
                "specialize coprime_mul_right y",
                "apply coprime_mul_right",
                "exact hprimitive_right",
                "exact hprimitive_right",
                "specialize hsquarecop divisor",
                "apply hsquarecop",
                "exact hx",
                "exact hysquare",
            ),
            "In every primitive Pythagorean triple, the first leg and hypotenuse have no nonunit common divisor.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_COPRIME_SECOND_LEG,
            f"forall x y z. ({primitive}) -> ({second_hypotenuse_coprime})",
            (
                "pythagorean_primitive_leg_swap",
                PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_COPRIME_FIRST_LEG,
            ),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro hprimitive",
                "specialize pythagorean_primitive_hypotenuse_coprime_first_leg y",
                "specialize pythagorean_primitive_hypotenuse_coprime_first_leg x",
                "specialize pythagorean_primitive_hypotenuse_coprime_first_leg z",
                "apply pythagorean_primitive_hypotenuse_coprime_first_leg",
                "specialize pythagorean_primitive_leg_swap x",
                "specialize pythagorean_primitive_leg_swap y",
                "specialize pythagorean_primitive_leg_swap z",
                "apply pythagorean_primitive_leg_swap",
                "exact hprimitive",
            ),
            "In every primitive Pythagorean triple, the second leg and hypotenuse have no nonunit common divisor.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_PAIRWISE_COPRIME,
            f"forall x y z. ({primitive}) -> "
            f"(({coprime_coordinates('x', 'y', tag='pairwise_legs')}) /\\ "
            f"(({first_hypotenuse_coprime}) /\\ "
            f"({second_hypotenuse_coprime})))",
            (
                PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_COPRIME_FIRST_LEG,
                PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_COPRIME_SECOND_LEG,
            ),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro hprimitive",
                f"have hlegs : {coprime_coordinates('x', 'y', tag='pairwise_local')}",
                "cases hprimitive",
                "exact hprimitive_right",
                "split",
                "exact hlegs",
                "split",
                "specialize pythagorean_primitive_hypotenuse_coprime_first_leg x",
                "specialize pythagorean_primitive_hypotenuse_coprime_first_leg y",
                "specialize pythagorean_primitive_hypotenuse_coprime_first_leg z",
                "apply pythagorean_primitive_hypotenuse_coprime_first_leg",
                "exact hprimitive",
                "specialize pythagorean_primitive_hypotenuse_coprime_second_leg x",
                "specialize pythagorean_primitive_hypotenuse_coprime_second_leg y",
                "specialize pythagorean_primitive_hypotenuse_coprime_second_leg z",
                "apply pythagorean_primitive_hypotenuse_coprime_second_leg",
                "exact hprimitive",
            ),
            "The two legs and hypotenuse of every primitive Pythagorean triple are pairwise coprime constructively.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_LEGS_NOT_BOTH_EVEN,
            f"forall x y z. ({primitive}) -> "
            "(exists a. x = 2 * a) -> (exists b. y = 2 * b) -> false",
            ("prime_two",),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro hprimitive",
                "intro hx",
                "intro hy",
                "cases hprimitive",
                "cases prime_two",
                "apply prime_two_left",
                "specialize hprimitive_right 2",
                "apply hprimitive_right",
                "exact hx",
                "exact hy",
            ),
            "The two legs of a primitive Pythagorean triple cannot both have even witnesses.",
        ),
        spec(
            PYTHAGOREAN_ODD_SQUARE_PAIR_TWO_MOD_FOUR,
            "forall a b. (exists i. a = 2 * i + 1) -> "
            "(exists j. b = 2 * j + 1) -> "
            "exists q. a * a + b * b = 4 * q + 2",
            (
                "odd_square_is_four_multiple_plus_one",
                "mul_add",
                "add_assoc",
                "add_comm",
            ),
            (
                "intro a",
                "intro b",
                "intro ha",
                "intro hb",
                "cases ha",
                "cases hb",
                "have hasquare : exists q. a * a = 4 * q + 1",
                "specialize odd_square_is_four_multiple_plus_one a",
                "specialize odd_square_is_four_multiple_plus_one x",
                "apply odd_square_is_four_multiple_plus_one",
                "exact ha_witness",
                "have hbsquare : exists q. b * b = 4 * q + 1",
                "specialize odd_square_is_four_multiple_plus_one b",
                "specialize odd_square_is_four_multiple_plus_one x1",
                "apply odd_square_is_four_multiple_plus_one",
                "exact hb_witness",
                "cases hasquare",
                "cases hbsquare",
                "exists x2 + x3",
                "rewrite hasquare_witness",
                "rewrite hbsquare_witness",
                "simp [mul_add, add_assoc, add_comm]",
            ),
            "The sum of two witnessed odd squares has exact residue two modulo four.",
        ),
        spec(
            PYTHAGOREAN_TWO_MOD_FOUR_NOT_SQUARE,
            "forall z q. z * z = 4 * q + 2 -> false",
            ("square_mod_four_zero_or_one", "division_remainder_unique"),
            (
                "intro z",
                "intro q",
                "intro htwo",
                "specialize square_mod_four_zero_or_one z",
                "cases square_mod_four_zero_or_one",
                "cases square_mod_four_zero_or_one_left",
                "have hunique : q = x /\\ 2 = 0",
                "specialize division_remainder_unique 4",
                "specialize division_remainder_unique (z * z)",
                "specialize division_remainder_unique q",
                "specialize division_remainder_unique 2",
                "specialize division_remainder_unique x",
                "specialize division_remainder_unique 0",
                "apply division_remainder_unique",
                "exact htwo",
                "exists 1",
                "norm_num",
                "exact square_mod_four_zero_or_one_left_witness",
                "exists 3",
                "norm_num",
                "cases hunique",
                "apply PA1",
                "exact hunique_right",
                "cases square_mod_four_zero_or_one_right",
                "have hunique : q = x /\\ 2 = 1",
                "specialize division_remainder_unique 4",
                "specialize division_remainder_unique (z * z)",
                "specialize division_remainder_unique q",
                "specialize division_remainder_unique 2",
                "specialize division_remainder_unique x",
                "specialize division_remainder_unique 1",
                "apply division_remainder_unique",
                "exact htwo",
                "exists 1",
                "norm_num",
                "exact square_mod_four_zero_or_one_right_witness",
                "exists 2",
                "norm_num",
                "cases hunique",
                "have hzero : 1 = 0",
                "apply PA2",
                "exact hunique_right",
                "apply PA1",
                "exact hzero",
            ),
            "No natural square is congruent to two modulo four, by uniqueness of bounded constructive remainders.",
        ),
        spec(
            PYTHAGOREAN_TRIPLE_LEGS_NOT_BOTH_ODD,
            f"forall a b c. ({pythagorean_triple('a', 'b', 'c')}) -> "
            "(exists i. a = 2 * i + 1) -> "
            "(exists j. b = 2 * j + 1) -> false",
            (
                PYTHAGOREAN_ODD_SQUARE_PAIR_TWO_MOD_FOUR,
                PYTHAGOREAN_TWO_MOD_FOUR_NOT_SQUARE,
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro htriple",
                "intro ha",
                "intro hb",
                "have htwo : exists q. a * a + b * b = 4 * q + 2",
                "specialize pythagorean_odd_square_pair_two_mod_four a",
                "specialize pythagorean_odd_square_pair_two_mod_four b",
                "apply pythagorean_odd_square_pair_two_mod_four",
                "exact ha",
                "exact hb",
                "cases htwo",
                "specialize pythagorean_two_mod_four_not_square c",
                "specialize pythagorean_two_mod_four_not_square x",
                "apply pythagorean_two_mod_four_not_square",
                "trans a * a + b * b",
                "symm",
                "exact htriple",
                "exact htwo_witness",
            ),
            "The two legs of any Pythagorean triple cannot both be odd, independently of primitiveness.",
        ),
        spec(
            PYTHAGOREAN_COORDINATE_PARITY_CHOICE,
            "forall a. (exists q. a = 2 * q) \\/ (exists q. a = 2 * q + 1)",
            ("parity_cases",),
            (
                "intro a",
                "specialize parity_cases a",
                "cases parity_cases",
                "cases parity_cases_witness",
                "left",
                "exists x",
                "exact parity_cases_witness_left",
                "right",
                "exists x",
                "exact parity_cases_witness_right",
            ),
            "Every natural has a constructive disjunction of explicit even and odd witnesses.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_LEGS_OPPOSITE_PARITY,
            f"forall x y z. ({primitive}) -> "
            f"({opposite_parity('x', 'y', tag='primitive_leg_result')})",
            (
                PYTHAGOREAN_COORDINATE_PARITY_CHOICE,
                PYTHAGOREAN_PRIMITIVE_LEGS_NOT_BOTH_EVEN,
                PYTHAGOREAN_TRIPLE_LEGS_NOT_BOTH_ODD,
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro hprimitive",
                "have hfirst : (exists q. a = 2 * q) \\/ "
                "(exists q. a = 2 * q + 1)",
                "specialize pythagorean_coordinate_parity_choice a",
                "exact pythagorean_coordinate_parity_choice",
                "have hsecond : (exists q. b = 2 * q) \\/ "
                "(exists q. b = 2 * q + 1)",
                "specialize pythagorean_coordinate_parity_choice b",
                "exact pythagorean_coordinate_parity_choice",
                "cases hfirst",
                "cases hsecond",
                "exfalso",
                "specialize pythagorean_primitive_legs_not_both_even a",
                "specialize pythagorean_primitive_legs_not_both_even b",
                "specialize pythagorean_primitive_legs_not_both_even c",
                "apply pythagorean_primitive_legs_not_both_even",
                "exact hprimitive",
                "exact hfirst_left",
                "exact hsecond_left",
                "left",
                "split",
                "exact hfirst_left",
                "exact hsecond_right",
                "cases hsecond",
                "right",
                "split",
                "exact hfirst_right",
                "exact hsecond_left",
                "exfalso",
                "specialize pythagorean_triple_legs_not_both_odd a",
                "specialize pythagorean_triple_legs_not_both_odd b",
                "specialize pythagorean_triple_legs_not_both_odd c",
                "apply pythagorean_triple_legs_not_both_odd",
                "cases hprimitive",
                "exact hprimitive_left",
                "exact hfirst_right",
                "exact hsecond_right",
            ),
            "Every primitive Pythagorean triple has genuinely opposite-parity legs with an explicit constructive choice of orientation.",
        ),
        spec(
            PYTHAGOREAN_ODD_SQUARE_HAS_ODD_ROOT,
            "forall z. (exists q. z * z = 2 * q + 1) -> "
            "exists q. z = 2 * q + 1",
            (
                "parity_cases",
                PYTHAGOREAN_PARAMETER_EVEN_SQUARE,
                "even_odd_exclusive_pointwise",
            ),
            (
                "intro z",
                "intro hodd",
                "specialize parity_cases z",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exfalso",
                "have heven : exists q. z * z = 2 * q",
                "specialize pythagorean_parameter_even_square z",
                "apply pythagorean_parameter_even_square",
                "exists x",
                "exact parity_cases_witness_left",
                "cases heven",
                "cases hodd",
                "specialize even_odd_exclusive_pointwise (z * z)",
                "specialize even_odd_exclusive_pointwise x1",
                "specialize even_odd_exclusive_pointwise x2",
                "apply even_odd_exclusive_pointwise",
                "exact heven_witness",
                "exact hodd_witness",
                "exists x",
                "exact parity_cases_witness_right",
            ),
            "An explicitly odd natural square has an explicitly odd natural root.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_ODD,
            f"forall x y z. ({primitive}) -> "
            "exists q. z = 2 * q + 1",
            (
                PYTHAGOREAN_PRIMITIVE_LEGS_OPPOSITE_PARITY,
                PYTHAGOREAN_OPPOSITE_PARITY_HYPOTENUSE_ODD,
                PYTHAGOREAN_ODD_SQUARE_HAS_ODD_ROOT,
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro hprimitive",
                f"have hparity : {opposite_parity('a', 'b', tag='hypotenuse_local')}",
                "specialize pythagorean_primitive_legs_opposite_parity a",
                "specialize pythagorean_primitive_legs_opposite_parity b",
                "specialize pythagorean_primitive_legs_opposite_parity c",
                "apply pythagorean_primitive_legs_opposite_parity",
                "exact hprimitive",
                "have hsum : exists q. a * a + b * b = 2 * q + 1",
                "specialize pythagorean_opposite_parity_hypotenuse_odd a",
                "specialize pythagorean_opposite_parity_hypotenuse_odd b",
                "apply pythagorean_opposite_parity_hypotenuse_odd",
                "exact hparity",
                "specialize pythagorean_odd_square_has_odd_root c",
                "apply pythagorean_odd_square_has_odd_root",
                "cases hsum",
                "exists x",
                "trans a * a + b * b",
                "cases hprimitive",
                "symm",
                "exact hprimitive_left",
                "exact hsum_witness",
            ),
            "Every primitive natural Pythagorean triple has an explicitly witnessed odd hypotenuse.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_NORMAL_FORM,
            f"forall x y z. ({primitive}) -> "
            f"(({opposite_parity('x', 'y', tag='normal_parity')}) /\\ "
            f"(({odd_coordinate('z', tag='normal_hypotenuse')}) /\\ "
            f"(({coprime_coordinates('x', 'y', tag='normal_legs')}) /\\ "
            f"(({first_hypotenuse_coprime}) /\\ "
            f"({second_hypotenuse_coprime})))))",
            (
                PYTHAGOREAN_PRIMITIVE_LEGS_OPPOSITE_PARITY,
                PYTHAGOREAN_PRIMITIVE_HYPOTENUSE_ODD,
                PYTHAGOREAN_PRIMITIVE_PAIRWISE_COPRIME,
            ),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro hprimitive",
                "split",
                "specialize pythagorean_primitive_legs_opposite_parity x",
                "specialize pythagorean_primitive_legs_opposite_parity y",
                "specialize pythagorean_primitive_legs_opposite_parity z",
                "apply pythagorean_primitive_legs_opposite_parity",
                "exact hprimitive",
                "split",
                "specialize pythagorean_primitive_hypotenuse_odd x",
                "specialize pythagorean_primitive_hypotenuse_odd y",
                "specialize pythagorean_primitive_hypotenuse_odd z",
                "apply pythagorean_primitive_hypotenuse_odd",
                "exact hprimitive",
                "specialize pythagorean_primitive_pairwise_coprime x",
                "specialize pythagorean_primitive_pairwise_coprime y",
                "specialize pythagorean_primitive_pairwise_coprime z",
                "apply pythagorean_primitive_pairwise_coprime",
                "exact hprimitive",
            ),
            "Every primitive Pythagorean triple admits its complete constructive parity and pairwise-coprimality normal form.",
        ),
    )


__all__ = [
    "even_coordinate",
    "make_pythagorean_primitive_candidate_theorems",
    "odd_coordinate",
    "opposite_parity",
]
