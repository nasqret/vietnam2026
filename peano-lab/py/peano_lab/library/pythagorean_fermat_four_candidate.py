"""Constructive Pythagorean parametrization and Fermat-four descent foundations.

All relations expand into ordinary first-order arithmetic.  Euclid's forward
constructor is proved from the already checked Brahmagupta identity; the
Fermat-four endpoint remains explicitly conditional on constructing an actual
strictly decreasing counterexample.  No converse classification, primitive
constructor, unconditional Fermat theorem, or release authority is inferred.
"""

from __future__ import annotations

from typing import Any, Callable


PYTHAGOREAN_DOUBLE_PRODUCT = "pythagorean_double_product"
PYTHAGOREAN_EUCLIDEAN_IDENTITY = "pythagorean_euclidean_identity"
PYTHAGOREAN_EUCLIDEAN_CONSTRUCTOR = "pythagorean_euclidean_constructor"
PYTHAGOREAN_EUCLIDEAN_SWAPPED_CONSTRUCTOR = (
    "pythagorean_euclidean_swapped_constructor"
)
PYTHAGOREAN_EUCLIDEAN_EVEN_LEG = "pythagorean_euclidean_even_leg"
PYTHAGOREAN_EUCLIDEAN_EVEN_LEG_NOT_ODD = (
    "pythagorean_euclidean_even_leg_not_odd"
)
PYTHAGOREAN_DIFFERENCE_WITNESS_UNIQUE = "pythagorean_difference_witness_unique"
PYTHAGOREAN_SQUARE_GAP_FROM_ORDER = "pythagorean_square_gap_from_order"
PYTHAGOREAN_EUCLIDEAN_FROM_ORDER = "pythagorean_euclidean_from_order"
PYTHAGOREAN_HYPOTENUSE_NONZERO = "pythagorean_hypotenuse_nonzero"
PYTHAGOREAN_COPRIME_SWAP = "pythagorean_coprime_swap"
PYTHAGOREAN_LEG_SWAP = "pythagorean_leg_swap"
PYTHAGOREAN_PRIMITIVE_LEG_SWAP = "pythagorean_primitive_leg_swap"
FERMAT_FOUR_COUNTEREXAMPLE_IS_PYTHAGOREAN = (
    "fermat_four_counterexample_is_pythagorean"
)
FERMAT_FOUR_BOUNDED_DESCENT = "fermat_four_bounded_descent"
FERMAT_FOUR_NO_SQUARE_FROM_DESCENT = "fermat_four_no_square_from_descent"
FERMAT_FOUR_NO_FOURTH_FROM_DESCENT = "fermat_four_no_fourth_from_descent"


def pythagorean_triple(first: str, second: str, hypotenuse: str) -> str:
    """Expand the exact natural Pythagorean equation."""

    return (
        f"({first}) * ({first}) + ({second}) * ({second}) = "
        f"({hypotenuse}) * ({hypotenuse})"
    )


def coprime_coordinates(first: str, second: str, *, tag: str) -> str:
    """Expand coprimality directly, without adding a trusted gcd predicate."""

    divisor = f"pff_divisor_{tag}"
    left = f"pff_left_{tag}"
    right = f"pff_right_{tag}"
    return (
        f"forall {divisor}. (exists {left}. ({first}) = {divisor} * {left}) -> "
        f"(exists {right}. ({second}) = {divisor} * {right}) -> {divisor} = 1"
    )


def primitive_pythagorean(
    first: str, second: str, hypotenuse: str, *, tag: str
) -> str:
    """Expand a Pythagorean triple with explicitly coprime natural legs."""

    return (
        f"(({pythagorean_triple(first, second, hypotenuse)}) /\\ "
        f"({coprime_coordinates(first, second, tag=tag)}))"
    )


def fermat_four_counterexample(
    first: str, second: str, hypotenuse: str, *, tag: str
) -> str:
    """Expand a positive counterexample to the stronger square-hypotenuse claim."""

    del tag
    return (
        f"(~(({first}) = 0) /\\ "
        f"(~(({second}) = 0) /\\ "
        f"(~(({hypotenuse}) = 0) /\\ "
        f"(({first}) * ({first}) * ({first}) * ({first}) + "
        f"({second}) * ({second}) * ({second}) * ({second}) = "
        f"({hypotenuse}) * ({hypotenuse})))))"
    )


def fermat_four_strict_descent(*, tag: str) -> str:
    """Expose the one unproved Fermat-four obligation as an exact HA formula."""

    first = f"pff_first_{tag}"
    second = f"pff_second_{tag}"
    hypotenuse = f"pff_hypotenuse_{tag}"
    smaller_first = f"pff_smaller_first_{tag}"
    smaller_second = f"pff_smaller_second_{tag}"
    smaller_hypotenuse = f"pff_smaller_hypotenuse_{tag}"
    gap = f"pff_gap_{tag}"
    current = fermat_four_counterexample(
        first, second, hypotenuse, tag=f"{tag}_current"
    )
    smaller = fermat_four_counterexample(
        smaller_first,
        smaller_second,
        smaller_hypotenuse,
        tag=f"{tag}_smaller",
    )
    return (
        f"forall {first} {second} {hypotenuse}. ({current}) -> "
        f"exists {smaller_first} {smaller_second} {smaller_hypotenuse}. "
        f"(({smaller}) /\\ "
        f"(exists {gap}. {gap} + S {smaller_hypotenuse} = {hypotenuse}))"
    )


def make_pythagorean_fermat_four_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build genuine forward Pythagorean proofs and conditional descent bridges."""

    triple = pythagorean_triple("x", "y", "z")
    swapped = pythagorean_triple("y", "x", "z")
    euclid = pythagorean_triple("d", "2 * (m * n)", "m * m + n * n")
    euclid_swapped = pythagorean_triple("2 * (m * n)", "d", "m * m + n * n")
    primitive = primitive_pythagorean("x", "y", "z", tag="source")
    primitive_swapped = primitive_pythagorean("y", "x", "z", tag="swapped")
    counterexample = fermat_four_counterexample("a", "b", "h", tag="bounded")
    descent = fermat_four_strict_descent(tag="bounded")
    return (
        spec(
            PYTHAGOREAN_DOUBLE_PRODUCT,
            "forall m n. m * n + n * m = 2 * (m * n)",
            ("mul_comm", "mul_succ_left", "one_mul"),
            (
                "intro m",
                "intro n",
                "trans m * n + m * n",
                "congr",
                "refl",
                "apply mul_comm",
                "symm",
                "trans 1 * (m * n) + m * n",
                "apply mul_succ_left",
                "congr",
                "apply one_mul",
                "refl",
            ),
            "The two symmetric Euclidean cross products are exactly twice their natural product.",
        ),
        spec(
            PYTHAGOREAN_EUCLIDEAN_IDENTITY,
            f"forall m n d. m * m = n * n + d -> ({euclid})",
            (
                "brahmagupta_fibonacci_two_square_identity",
                "add_comm",
                PYTHAGOREAN_DOUBLE_PRODUCT,
            ),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "have hidentity : "
                "(m * m + n * n) * (n * n + m * m) = "
                "(m * n + n * m) * (m * n + n * m) + d * d",
                "specialize brahmagupta_fibonacci_two_square_identity m",
                "specialize brahmagupta_fibonacci_two_square_identity n",
                "specialize brahmagupta_fibonacci_two_square_identity n",
                "specialize brahmagupta_fibonacci_two_square_identity m",
                "specialize brahmagupta_fibonacci_two_square_identity d",
                "apply brahmagupta_fibonacci_two_square_identity",
                "left",
                "exact hgap",
                "have hsum : n * n + m * m = m * m + n * n",
                "apply add_comm",
                "rewrite hsum at hidentity",
                "specialize pythagorean_double_product m",
                "specialize pythagorean_double_product n",
                "rewrite pythagorean_double_product at hidentity",
                "rewrite pythagorean_double_product at hidentity",
                "trans (2 * (m * n)) * (2 * (m * n)) + d * d",
                "apply add_comm",
                "symm",
                "exact hidentity",
            ),
            "Euclid's subtraction-free Pythagorean identity follows from the witnessed square difference and the checked Brahmagupta identity.",
        ),
        spec(
            PYTHAGOREAN_EUCLIDEAN_CONSTRUCTOR,
            f"forall m n. (exists d. m * m = n * n + d) -> "
            f"exists d. ({euclid})",
            (PYTHAGOREAN_EUCLIDEAN_IDENTITY,),
            (
                "intro m",
                "intro n",
                "intro hgap",
                "cases hgap",
                "exists x",
                "apply pythagorean_euclidean_identity",
                "exact hgap_witness",
            ),
            "Every witnessed natural square difference constructs an explicit Euclidean Pythagorean triple.",
        ),
        spec(
            PYTHAGOREAN_LEG_SWAP,
            f"forall x y z. ({triple}) -> ({swapped})",
            ("add_comm",),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro htriple",
                "trans x * x + y * y",
                "apply add_comm",
                "exact htriple",
            ),
            "Swapping the two legs of a natural Pythagorean triple preserves its exact equation.",
        ),
        spec(
            PYTHAGOREAN_EUCLIDEAN_SWAPPED_CONSTRUCTOR,
            f"forall m n d. m * m = n * n + d -> ({euclid_swapped})",
            (PYTHAGOREAN_EUCLIDEAN_IDENTITY, PYTHAGOREAN_LEG_SWAP),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro hgap",
                "apply pythagorean_leg_swap",
                "apply pythagorean_euclidean_identity",
                "exact hgap",
            ),
            "Euclid's explicit constructor supplies either canonical ordering of its odd/difference and doubled-product legs.",
        ),
        spec(
            PYTHAGOREAN_EUCLIDEAN_EVEN_LEG,
            "forall m n. exists q. 2 * (m * n) = 2 * q",
            (),
            (
                "intro m",
                "intro n",
                "exists m * n",
                "refl",
            ),
            "The Euclidean cross-product leg has an exact, explicitly witnessed even half.",
        ),
        spec(
            PYTHAGOREAN_EUCLIDEAN_EVEN_LEG_NOT_ODD,
            "forall m n q. 2 * (m * n) = 2 * q + 1 -> false",
            ("even_odd_exclusive_k1",),
            (
                "intro m",
                "intro n",
                "intro q",
                "intro hodd",
                "specialize even_odd_exclusive_k1 (2 * (m * n))",
                "specialize even_odd_exclusive_k1 (m * n)",
                "specialize even_odd_exclusive_k1 q",
                "apply even_odd_exclusive_k1",
                "refl",
                "exact hodd",
            ),
            "The explicitly even Euclidean cross-product coordinate cannot simultaneously have an odd witness.",
        ),
        spec(
            PYTHAGOREAN_DIFFERENCE_WITNESS_UNIQUE,
            "forall m n d e. m * m = n * n + d -> "
            "m * m = n * n + e -> d = e",
            ("add_left_cancel",),
            (
                "intro m",
                "intro n",
                "intro d",
                "intro e",
                "intro hd",
                "intro he",
                "specialize add_left_cancel (n * n)",
                "specialize add_left_cancel d",
                "specialize add_left_cancel e",
                "apply add_left_cancel",
                "trans m * m",
                "symm",
                "exact hd",
                "exact he",
            ),
            "The natural Euclidean square-difference coordinate is unique without subtraction or classical choice.",
        ),
        spec(
            PYTHAGOREAN_SQUARE_GAP_FROM_ORDER,
            "forall m n. (exists gap. gap + n = m) -> "
            "exists d. m * m = n * n + d",
            ("mul_le_mul", "add_comm"),
            (
                "intro m",
                "intro n",
                "intro hbound",
                "have hsquare : exists gap. gap + n * n = m * m",
                "apply mul_le_mul",
                "exact hbound",
                "exact hbound",
                "cases hsquare",
                "exists x",
                "trans x + n * n",
                "symm",
                "exact hsquare_witness",
                "apply add_comm",
            ),
            "Every witnessed natural parameter inequality n≤m produces the exact subtraction-free square-difference witness m²=n²+d.",
        ),
        spec(
            PYTHAGOREAN_EUCLIDEAN_FROM_ORDER,
            f"forall m n. (exists gap. gap + n = m) -> "
            f"exists d. ({euclid})",
            (PYTHAGOREAN_SQUARE_GAP_FROM_ORDER, PYTHAGOREAN_EUCLIDEAN_CONSTRUCTOR),
            (
                "intro m",
                "intro n",
                "intro hbound",
                "apply pythagorean_euclidean_constructor",
                "apply pythagorean_square_gap_from_order",
                "exact hbound",
            ),
            "Every ordered pair of natural Euclidean parameters constructs a witnessed Pythagorean triple without subtraction or a supplied square-difference hypothesis.",
        ),
        spec(
            PYTHAGOREAN_HYPOTENUSE_NONZERO,
            "forall m n. ~(m = 0) -> ~(m * m + n * n = 0)",
            ("add_eq_zero_left", "mul_eq_zero"),
            (
                "intro m",
                "intro n",
                "intro hnonzero",
                "intro hsum",
                "have hsquare : m * m = 0",
                "specialize add_eq_zero_left (m * m)",
                "specialize add_eq_zero_left (n * n)",
                "apply add_eq_zero_left",
                "exact hsum",
                "have hsplit : m = 0 \\/ m = 0",
                "apply mul_eq_zero",
                "exact hsquare",
                "cases hsplit",
                "apply hnonzero",
                "exact hsplit_left",
                "apply hnonzero",
                "exact hsplit_right",
            ),
            "A nonzero first Euclidean parameter yields a genuinely nonzero natural hypotenuse.",
        ),
        spec(
            PYTHAGOREAN_COPRIME_SWAP,
            f"forall x y. ({coprime_coordinates('x', 'y', tag='swap_forward')}) "
            f"-> ({coprime_coordinates('y', 'x', tag='swap_backward')})",
            (),
            (
                "intro x",
                "intro y",
                "intro hcoprime",
                "intro divisor",
                "intro hright",
                "intro hleft",
                "specialize hcoprime divisor",
                "apply hcoprime",
                "exact hleft",
                "exact hright",
            ),
            "Natural common-divisor coprimality is symmetric with no gcd choice or excluded middle.",
        ),
        spec(
            PYTHAGOREAN_PRIMITIVE_LEG_SWAP,
            f"forall x y z. ({primitive}) -> ({primitive_swapped})",
            (PYTHAGOREAN_LEG_SWAP, PYTHAGOREAN_COPRIME_SWAP),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro hprimitive",
                "cases hprimitive",
                "split",
                "apply pythagorean_leg_swap",
                "exact hprimitive_left",
                "apply pythagorean_coprime_swap",
                "exact hprimitive_right",
            ),
            "Primitive Pythagorean triples remain primitive after swapping their legs, with coprimality proved by explicit common-divisor witnesses.",
        ),
        spec(
            FERMAT_FOUR_COUNTEREXAMPLE_IS_PYTHAGOREAN,
            "forall a b h. "
            "a * a * a * a + b * b * b * b = h * h -> "
            f"({pythagorean_triple('a * a', 'b * b', 'h')})",
            ("fourth_power_regroup",),
            (
                "intro a",
                "intro b",
                "intro h",
                "intro hequation",
                "have hfirst : a * a * a * a = (a * a) * (a * a)",
                "apply fourth_power_regroup",
                "have hsecond : b * b * b * b = (b * b) * (b * b)",
                "apply fourth_power_regroup",
                "rewrite hfirst at hequation",
                "rewrite hsecond at hequation",
                "exact hequation",
            ),
            "A positive fourth-power square counterexample necessarily supplies a Pythagorean triple whose two legs are natural squares.",
        ),
        spec(
            FERMAT_FOUR_BOUNDED_DESCENT,
            f"forall B h a b. (exists gap. gap + h = B) -> "
            f"({descent}) -> ~({counterexample})",
            ("le_zero", "le_trans", "le_of_succ_le_succ"),
            (
                "intro B",
                "induction B",
                "intro h",
                "intro a",
                "intro b",
                "intro hbound",
                "intro hstep",
                "intro hcounter",
                "cases hcounter",
                "cases hcounter_right",
                "cases hcounter_right_right",
                "apply hcounter_right_right_left",
                "specialize le_zero h",
                "apply le_zero",
                "exact hbound",
                "intro h",
                "intro a",
                "intro b",
                "intro hbound",
                "intro hstep",
                "intro hcounter",
                "have hsmaller : exists first second smaller. "
                f"(({fermat_four_counterexample('first', 'second', 'smaller', tag='smaller')}) /\\ "
                "(exists gap. gap + S smaller = h))",
                "specialize hstep a",
                "specialize hstep b",
                "specialize hstep h",
                "apply hstep",
                "exact hcounter",
                "cases hsmaller",
                "cases hsmaller_witness",
                "cases hsmaller_witness_witness",
                "cases hsmaller_witness_witness_witness",
                "have hsuccessor_bound : exists gap. gap + S x2 = S B",
                "specialize le_trans (S x2)",
                "specialize le_trans h",
                "specialize le_trans (S B)",
                "apply le_trans",
                "exact hsmaller_witness_witness_witness_right",
                "exact hbound",
                "have hsmaller_bound : exists gap. gap + x2 = B",
                "specialize le_of_succ_le_succ x2",
                "specialize le_of_succ_le_succ B",
                "apply le_of_succ_le_succ",
                "exact hsuccessor_bound",
                "specialize IH x2",
                "specialize IH x",
                "specialize IH x1",
                "apply IH",
                "exact hsmaller_bound",
                "exact hstep",
                "exact hsmaller_witness_witness_witness_left",
            ),
            "Ordinary bounded natural induction rejects every positive Fermat-four counterexample once an exact strictly smaller counterexample constructor is supplied.",
        ),
        spec(
            FERMAT_FOUR_NO_SQUARE_FROM_DESCENT,
            f"({descent}) -> forall a b h. ~({counterexample})",
            (FERMAT_FOUR_BOUNDED_DESCENT, "le_refl"),
            (
                "intro hstep",
                "intro a",
                "intro b",
                "intro h",
                "intro hcounter",
                "specialize fermat_four_bounded_descent h",
                "specialize fermat_four_bounded_descent h",
                "specialize fermat_four_bounded_descent a",
                "specialize fermat_four_bounded_descent b",
                "apply fermat_four_bounded_descent",
                "apply le_refl",
                "exact hstep",
                "exact hcounter",
            ),
            "The stronger no-fourth-powers-sum-to-a-square theorem follows constructively from precisely one explicit, still-unproved strict descent premise.",
        ),
        spec(
            FERMAT_FOUR_NO_FOURTH_FROM_DESCENT,
            f"({descent}) -> forall a b h. "
            "~(a = 0) -> ~(b = 0) -> ~(h = 0) -> "
            "~(a * a * a * a + b * b * b * b = h * h * h * h)",
            (
                FERMAT_FOUR_NO_SQUARE_FROM_DESCENT,
                "fourth_power_regroup",
                "mul_eq_zero",
            ),
            (
                "intro hstep",
                "intro a",
                "intro b",
                "intro h",
                "intro ha",
                "intro hb",
                "intro hh",
                "intro hequation",
                f"have hno_square : forall a b h. ~({counterexample})",
                "apply fermat_four_no_square_from_descent",
                "exact hstep",
                "specialize hno_square a",
                "specialize hno_square b",
                "specialize hno_square (h * h)",
                "apply hno_square",
                "split",
                "exact ha",
                "split",
                "exact hb",
                "split",
                "intro hsquare",
                "have hsplit : h = 0 \\/ h = 0",
                "apply mul_eq_zero",
                "exact hsquare",
                "cases hsplit",
                "apply hh",
                "exact hsplit_left",
                "apply hh",
                "exact hsplit_right",
                "specialize fourth_power_regroup h",
                "rewrite fourth_power_regroup at hequation",
                "exact hequation",
            ),
            "Fermat's exponent-four equation is impossible if, and only insofar as, the explicitly stated stronger square-hypotenuse strict-descent obligation is proved.",
        ),
    )


__all__ = [
    "FERMAT_FOUR_BOUNDED_DESCENT",
    "FERMAT_FOUR_COUNTEREXAMPLE_IS_PYTHAGOREAN",
    "FERMAT_FOUR_NO_FOURTH_FROM_DESCENT",
    "FERMAT_FOUR_NO_SQUARE_FROM_DESCENT",
    "PYTHAGOREAN_DIFFERENCE_WITNESS_UNIQUE",
    "PYTHAGOREAN_COPRIME_SWAP",
    "PYTHAGOREAN_DOUBLE_PRODUCT",
    "PYTHAGOREAN_EUCLIDEAN_CONSTRUCTOR",
    "PYTHAGOREAN_EUCLIDEAN_EVEN_LEG",
    "PYTHAGOREAN_EUCLIDEAN_EVEN_LEG_NOT_ODD",
    "PYTHAGOREAN_EUCLIDEAN_FROM_ORDER",
    "PYTHAGOREAN_EUCLIDEAN_IDENTITY",
    "PYTHAGOREAN_EUCLIDEAN_SWAPPED_CONSTRUCTOR",
    "PYTHAGOREAN_HYPOTENUSE_NONZERO",
    "PYTHAGOREAN_LEG_SWAP",
    "PYTHAGOREAN_PRIMITIVE_LEG_SWAP",
    "PYTHAGOREAN_SQUARE_GAP_FROM_ORDER",
    "coprime_coordinates",
    "fermat_four_counterexample",
    "fermat_four_strict_descent",
    "make_pythagorean_fermat_four_candidate_theorems",
    "primitive_pythagorean",
    "pythagorean_triple",
]
