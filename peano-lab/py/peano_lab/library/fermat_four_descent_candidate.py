"""Constructive Fermat-four descent over the unchanged first-order HA kernel.

The public relations are conservative authoring abbreviations.  The proofs
construct gcd normalization, square-factor witnesses, and a genuinely smaller
counterexample before invoking the existing induction theorem.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_gcd_candidate import _identifier, is_gcd
from .pythagorean_fermat_four_candidate import (
    coprime_coordinates,
    fermat_four_counterexample,
    fermat_four_strict_descent,
    primitive_pythagorean,
)
from .pythagorean_inverse_candidate import _parameters
from .pythagorean_primitive_candidate import opposite_parity


class FermatFourDescentError(ValueError):
    """A conservative definition would capture one of its free arguments."""


def primitive_four_counterexample(first: str, second: str, height: str, *, tag: str) -> str:
    """Expand a positive fourth-power counterexample with coprime bases."""
    values = (first, second, height)
    try:
        for value in values:
            _identifier(value, "counterexample coordinate")
        _identifier(tag, "binder tag")
    except ValueError as error:
        raise FermatFourDescentError(str(error)) from error
    if len(set(values)) != len(values) or any(value.startswith("pff_") for value in values):
        raise FermatFourDescentError("coordinates must be distinct and cannot capture generated binders")
    return (
        f"(({fermat_four_counterexample(first, second, height, tag=tag)}) /\\ "
        f"({coprime_coordinates(first, second, tag=tag)}))"
    )


def fermat_four_descent_witness(first: str, second: str, height: str, upper: str, *, tag: str) -> str:
    """Expand an actual positive counterexample and its strictly smaller height."""
    values = (first, second, height, upper)
    try:
        for value in values:
            _identifier(value, "descent coordinate")
        _identifier(tag, "binder tag")
    except ValueError as error:
        raise FermatFourDescentError(str(error)) from error
    if len(set(values)) != len(values) or any(value.startswith(("pff_", "ffd_")) for value in values):
        raise FermatFourDescentError("coordinates must be distinct and cannot capture generated binders")
    return (
        f"(({fermat_four_counterexample(first, second, height, tag=tag)}) /\\ "
        f"(exists ffd_gap_{tag}. ffd_gap_{tag} + S {height} = {upper}))"
    )


def fermat_four_trivial_solution(first: str, second: str, height: str, *, tag: str) -> str:
    """Expand all natural exponent-four solutions, including their zero boundary."""
    try:
        for value in (first, second, height):
            _identifier(value, "solution coordinate")
        _identifier(tag, "binder tag")
    except ValueError as error:
        raise FermatFourDescentError(str(error)) from error
    return f"((({first}) = 0 /\\ ({second}) = ({height})) \\/ (({second}) = 0 /\\ ({first}) = ({height})))"


def _apply(name: str, *arguments: str) -> tuple[str, ...]:
    return tuple(f"specialize {name} ({argument})" for argument in arguments) + (f"apply {name}",)


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _coprime(left: str, right: str, tag: str) -> str:
    return coprime_coordinates(left, right, tag=f"ffd_{tag}")


def make_fermat_four_descent_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Return dependency-ordered real tactic bodies, with no assumed descent."""
    return (
        spec(
            "fermat_four_product_nonzero",
            "forall a b. ~(a = 0) -> ~(b = 0) -> ~(a * b = 0)",
            ("mul_eq_zero",),
            _intro("a", "b", "ha", "hb", "hzero")
            + ("have hcases : a = 0 \\/ b = 0",)
            + _apply("mul_eq_zero", "a", "b")
            + ("exact hzero", "cases hcases", "apply ha", "exact hcases_left", "apply hb", "exact hcases_right"),
            "The product of two nonzero naturals is nonzero, by the checked zero-product disjunction.",
        ),
        spec(
            "fermat_four_square_nonzero",
            "forall a. ~(a = 0) -> ~(a * a = 0)",
            ("fermat_four_product_nonzero",),
            _intro("a", "ha", "hzero") + _apply("fermat_four_product_nonzero", "a", "a") + ("exact ha", "exact ha", "exact hzero"),
            "A positive coordinate has a positive square.",
        ),
        spec(
            "fermat_four_coprime_squares",
            f"forall a b. ({_coprime('a','b','square_source')}) -> ({_coprime('a * a','b * b','square_result')})",
            ("coprime_mul_left", "coprime_mul_right"),
            _intro("a", "b", "hcoprime")
            + (f"have hright : {_coprime('a','b * b','square_middle')}",)
            + _apply("coprime_mul_right", "a", "b", "b")
            + ("exact hcoprime", "exact hcoprime")
            + _apply("coprime_mul_left", "a", "a", "b * b")
            + ("exact hright", "exact hright"),
            "Coprime natural bases have coprime squares, with no prime-factorization assumption.",
        ),
        spec(
            "fermat_four_scaled_fourth_identity",
            "forall d a. ((d * a) * (d * a)) * ((d * a) * (d * a)) = "
            "((d * d) * (d * d)) * ((a * a) * (a * a))",
            ("four_square_product_square",),
            _intro("d", "a")
            + ("trans ((d * d) * (a * a)) * ((d * d) * (a * a))", "congr",
               "apply four_square_product_square", "apply four_square_product_square",
               "apply four_square_product_square"),
            "Scaling a fourth power exposes the fourth power of its scale by two explicit product-square identities.",
        ),
        spec(
            "fermat_four_scaled_equation",
            "forall a b h d A B. a = d * A -> b = d * B -> "
            "a * a * a * a + b * b * b * b = h * h -> "
            "h * h = ((d * d) * (d * d)) * ((A * A) * (A * A) + (B * B) * (B * B))",
            ("fermat_four_counterexample_is_pythagorean", "fermat_four_scaled_fourth_identity", "mul_add"),
            _intro("a", "b", "h", "d", "A", "B", "ha", "hb", "hequation")
            + ("have heq : (a * a) * (a * a) + (b * b) * (b * b) = h * h",)
            + _apply("fermat_four_counterexample_is_pythagorean", "a", "b", "h")
            + ("exact hequation",) + ("rewrite ha at heq",) * 4 + ("rewrite hb at heq",) * 4 + (
               "have hA : ((d * A) * (d * A)) * ((d * A) * (d * A)) = ((d * d) * (d * d)) * ((A * A) * (A * A))",
               "apply fermat_four_scaled_fourth_identity",
               "have hB : ((d * B) * (d * B)) * ((d * B) * (d * B)) = ((d * d) * (d * d)) * ((B * B) * (B * B))",
               "apply fermat_four_scaled_fourth_identity", "rewrite hA at heq", "rewrite hB at heq",
               "trans ((d * d) * (d * d)) * ((A * A) * (A * A)) + ((d * d) * (d * d)) * ((B * B) * (B * B))",
               "symm", "exact heq", "symm", "apply mul_add"),
            "A common scale on the two bases produces an exact fourth-power divisor of the squared hypotenuse.",
        ),
        spec(
            "fermat_four_cancel_scaled_equation",
            "forall d A B H h. ~(d = 0) -> h = (d * d) * H -> "
            "h * h = ((d * d) * (d * d)) * ((A * A) * (A * A) + (B * B) * (B * B)) -> "
            "A * A * A * A + B * B * B * B = H * H",
            ("fermat_four_square_nonzero", "four_square_product_square", "mul_left_cancel_nonzero", "fourth_power_regroup"),
            _intro("d", "A", "B", "H", "h", "hd", "hh", "hequation")
            + ("have hdsquare : ~(d * d = 0)", "intro hzero")
            + _apply("fermat_four_square_nonzero", "d") + ("exact hd", "exact hzero",
               "have hdfourth : ~((d * d) * (d * d) = 0)", "intro hzero")
            + _apply("fermat_four_square_nonzero", "d * d") + ("exact hdsquare", "exact hzero",
               "have hnorm : (A * A) * (A * A) + (B * B) * (B * B) = H * H")
            + _apply("mul_left_cancel_nonzero", "(d * d) * (d * d)", "(A * A) * (A * A) + (B * B) * (B * B)", "H * H")
            + ("exact hdfourth", "trans h * h", "symm", "exact hequation", "rewrite hh", "rewrite hh", "apply four_square_product_square",
               "trans (A * A) * (A * A) + (B * B) * (B * B)", "congr",
               "apply fourth_power_regroup", "apply fourth_power_regroup", "exact hnorm"),
            "Cancelling the positive fourth-power scale returns an actual smaller-scale fourth-power counterexample equation.",
        ),
        spec(
            "fermat_four_lt_add_positive",
            "forall a b. ~(b = 0) -> exists k. k + S a = a + b",
            ("nonzero_is_succ", "add_comm", "add_succ_left"),
            _intro("a", "b", "hb")
            + ("have hs : exists k. b = S k", "apply nonzero_is_succ", "exact hb", "cases hs", "exists x",
               "rewrite hs_witness", "trans S (x + a)", "apply PA4", "trans S (a + x)", "congr", "apply add_comm", "symm", "apply PA4"),
            "Adding a nonzero natural strictly increases every natural, with an explicit gap witness.",
        ),
        spec(
            "fermat_four_root_lt_norm",
            "forall u m n h. ~(u = 0) -> ~(n = 0) -> m = u * u -> h = m * m + n * n -> exists k. k + S u = h",
            ("le_scaled_nonzero", "fermat_four_square_nonzero", "fermat_four_lt_add_positive", "lt_of_le_of_lt", "le_trans"),
            _intro("u", "m", "n", "h", "hu", "hn", "hm", "hh")
            + ("have hum : exists k. k + u = m", "rewrite hm")
            + _apply("le_scaled_nonzero", "u", "u")
            + ("exact hu", "have hmpositive : ~(m = 0)", "intro hzero", "rewrite hm at hzero")
            + _apply("fermat_four_square_nonzero", "u") + ("exact hu", "exact hzero",
               "have hms : exists k. k + m = m * m")
            + _apply("le_scaled_nonzero", "m", "m")
            + ("exact hmpositive", "have hus : exists k. k + u = m * m")
            + _apply("le_trans", "u", "m", "m * m")
            + ("exact hum", "exact hms", "rewrite hh")
            + _apply("lt_of_le_of_lt", "u", "m * m", "m * m + n * n")
            + ("exact hus", "apply fermat_four_lt_add_positive", "intro hzero")
            + _apply("fermat_four_square_nonzero", "n") + ("exact hn", "exact hzero"),
            "The square root of the first Euclidean parameter lies strictly below its positive norm, giving the descent measure.",
        ),
        spec(
            "fermat_four_even_square_root",
            "forall a. (exists k. a * a = 2 * k) -> exists k. a = 2 * k",
            ("parity_cases", "pythagorean_parameter_odd_square", "even_odd_exclusive_pointwise"),
            _intro("a", "hsquare")
            + ("specialize parity_cases a", "cases parity_cases", "cases parity_cases_witness",
               "exists x", "exact parity_cases_witness_left", "exfalso",
               "have hodd : exists k. a * a = 2 * k + 1", "apply pythagorean_parameter_odd_square",
               "exists x", "exact parity_cases_witness_right", "cases hsquare", "cases hodd")
            + _apply("even_odd_exclusive_pointwise", "a * a", "x1", "x2")
            + ("exact hsquare_witness", "exact hodd_witness"),
            "An even square has an explicitly even root, proved by constructive parity cases.",
        ),
        spec(
            "fermat_four_double_product_commute",
            "forall m n. m * (2 * n) = 2 * (m * n)",
            ("mul_assoc", "mul_comm"),
            _intro("m", "n")
            + ("trans (m * 2) * n", "symm", "apply mul_assoc", "trans (2 * m) * n", "congr",
               "apply mul_comm", "refl", "apply mul_assoc"),
            "The factor two may pass a natural factor using explicit associativity and commutativity.",
        ),
        spec(
            "fermat_four_odd_double_square_factors",
            f"forall m n y. ({_coprime('m','n','double_source')}) -> "
            "(exists k. m = 2 * k + 1) -> y * y = 2 * (m * n) -> "
            "exists u v. (m = u * u /\\ n = 2 * (v * v))",
            ("pythagorean_odd_coordinate_coprime_two", "coprime_mul_right", "coprime_square_product_factors",
             "fermat_four_double_product_commute", "fermat_four_even_square_root", "mul_left_cancel_nonzero",
             "four_square_product_square", "mul_assoc", "succ_ne_zero"),
            _intro("m", "n", "y", "hcoprime", "hm", "hequation")
            + (f"have hm2 : {_coprime('m','2','double_two')}", "apply pythagorean_odd_coordinate_coprime_two", "exact hm",
               f"have hm2n : {_coprime('m','2 * n','double_product')}")
            + _apply("coprime_mul_right", "m", "2", "n")
            + ("exact hm2", "exact hcoprime", "have hparts : exists u v. (m = u * u /\\ 2 * n = v * v)")
            + _apply("coprime_square_product_factors", "m", "2 * n", "y")
            + ("exact hm2n", "trans 2 * (m * n)", "apply fermat_four_double_product_commute", "symm", "exact hequation",
               "cases hparts", "cases hparts_witness", "cases hparts_witness_witness",
               "have hhalf : exists k. x1 = 2 * k", "apply fermat_four_even_square_root", "exists n", "symm",
               "exact hparts_witness_witness_right", "cases hhalf", "exists x", "exists x2", "split",
               "exact hparts_witness_witness_left")
            + _apply("mul_left_cancel_nonzero", "2", "n", "2 * (x2 * x2)")
            + ("intro hzero", "specialize succ_ne_zero 1", "apply succ_ne_zero", "exact hzero",
               "trans x1 * x1", "exact hparts_witness_witness_right", "rewrite hhalf_witness", "rewrite hhalf_witness",
               "trans (2 * 2) * (x2 * x2)", "apply four_square_product_square", "apply mul_assoc"),
            "A square twice a coprime product with odd first factor supplies an actual square first factor and twice-square second factor.",
        ),
        spec(
            "fermat_four_primitive_normalization",
            f"forall a b h. ({fermat_four_counterexample('a','b','h',tag='normalize_source')}) -> "
            "exists A B H. "
            f"(({primitive_four_counterexample('A','B','H',tag='normalize_result')}) /\\ (exists k. k + H = h))",
            ("gcd_exists_relational", "is_gcd_nonzero_coprime_quotients", "fermat_four_scaled_equation",
             "square_divides_square_root", "factor_nonzero_right", "fermat_four_cancel_scaled_equation",
             "fermat_four_square_nonzero", "le_scaled_nonzero"),
            _intro("a", "b", "h", "hcounter")
            + ("cases hcounter", "cases hcounter_right", "cases hcounter_right_right",
               f"have hg : exists g. {is_gcd('g','a','b',tag='ffd_normalize_gcd')}", "apply gcd_exists_relational", "cases hg",
               "have hquot : exists A B. ((a = x * A /\\ b = x * B) /\\ ((~(x = 0) /\\ ~(A = 0)) /\\ "
               f"(~(B = 0) /\\ ({_coprime('A','B','normalize_quotient')}))))")
            + _apply("is_gcd_nonzero_coprime_quotients", "x", "a", "b")
            + ("exact hcounter_left", "exact hcounter_right_left", "exact hg_witness",
               "cases hquot", "cases hquot_witness", "cases hquot_witness_witness", "cases hquot_witness_witness_left",
               "cases hquot_witness_witness_right", "cases hquot_witness_witness_right_left", "cases hquot_witness_witness_right_right",
               "have hscaled : h * h = ((x * x) * (x * x)) * ((x1 * x1) * (x1 * x1) + (x2 * x2) * (x2 * x2))")
            + _apply("fermat_four_scaled_equation", "a", "b", "h", "x", "x1", "x2")
            + ("exact hquot_witness_witness_left_left", "exact hquot_witness_witness_left_right", "exact hcounter_right_right_right",
               "have hdiv : exists H. h = (x * x) * H")
            + _apply("square_divides_square_root", "x * x", "h")
            + ("exists (x1 * x1) * (x1 * x1) + (x2 * x2) * (x2 * x2)", "exact hscaled", "cases hdiv",
               "have hheight : ~(x3 = 0)", "intro hzero")
            + _apply("factor_nonzero_right", "h", "x * x", "x3")
            + ("exact hcounter_right_right_left", "exact hdiv_witness", "exact hzero",
               "exists x1", "exists x2", "exists x3", "split", "split", "split",
               "exact hquot_witness_witness_right_left_right", "split", "exact hquot_witness_witness_right_right_left",
               "split", "exact hheight")
            + _apply("fermat_four_cancel_scaled_equation", "x", "x1", "x2", "x3", "h")
            + ("exact hquot_witness_witness_right_left_left", "exact hdiv_witness", "exact hscaled",
               "exact hquot_witness_witness_right_right_right", "rewrite hdiv_witness")
            + _apply("le_scaled_nonzero", "x * x", "x3")
            + ("intro hzero",)
            + _apply("fermat_four_square_nonzero", "x")
            + ("exact hquot_witness_witness_right_left_left", "exact hzero"),
            "Every positive fourth-power counterexample constructively reduces to coprime positive bases without increasing the hypotenuse.",
        ),
        spec(
            "fermat_four_nested_primitive_triangle",
            f"forall a m n. ({_coprime('m','n','nested_parameters')}) -> m * m = n * n + a * a -> "
            f"({primitive_pythagorean('a','n','m',tag='ffd_nested_result')})",
            ("pythagorean_square_gap_coprime_second_parameter", "crt_coprime_divisor_pair", "mul_one", "add_comm"),
            _intro("a", "m", "n", "hcoprime", "hgap")
            + (f"have hsquare : {_coprime('a * a','n','nested_square')}",)
            + _apply("pythagorean_square_gap_coprime_second_parameter", "m", "n", "a * a")
            + ("exact hgap", "exact hcoprime", "split", "trans n * n + a * a", "apply add_comm", "symm", "exact hgap")
            + _apply("crt_coprime_divisor_pair", "a * a", "n", "a", "n")
            + ("exact hsquare", "exists a", "refl", "exists 1", "symm", "apply mul_one"),
            "The square odd leg in the first parametrization exposes a second primitive Pythagorean triangle on the unsquared base.",
        ),
        spec(
            "fermat_four_second_parameter_descent",
            f"forall u m n v r s h. ~(u = 0) -> ~(n = 0) -> ({_coprime('r','s','second_parameters')}) -> "
            "m = u * u -> n = 2 * (v * v) -> m = r * r + s * s -> n = 2 * (r * s) -> h = m * m + n * n -> "
            f"exists A B. ({fermat_four_descent_witness('A','B','u','h',tag='second_result')})",
            ("mul_left_cancel_nonzero", "succ_ne_zero", "coprime_square_product_factors", "factor_nonzero_left", "factor_nonzero_right",
             "fourth_power_regroup", "fermat_four_root_lt_norm"),
            _intro("u", "m", "n", "v", "r", "s", "h", "hu", "hn", "hcoprime", "hm", "hnv", "hmrs", "hnrs", "hh")
            + ("have hproduct : r * s = v * v",)
            + _apply("mul_left_cancel_nonzero", "2", "r * s", "v * v")
            + ("intro hzero", "specialize succ_ne_zero 1", "apply succ_ne_zero", "exact hzero", "trans n", "symm", "exact hnrs", "exact hnv",
               "have hsquares : exists A B. (r = A * A /\\ s = B * B)")
            + _apply("coprime_square_product_factors", "r", "s", "v")
            + ("exact hcoprime", "exact hproduct", "cases hsquares", "cases hsquares_witness", "cases hsquares_witness_witness",
               "have hrspositive : ~(r * s = 0)", "intro hzero")
            + _apply("factor_nonzero_right", "n", "2", "r * s")
            + ("exact hn", "exact hnrs", "exact hzero", "have hr : ~(r = 0)", "intro hzero")
            + _apply("factor_nonzero_left", "r * s", "r", "s")
            + ("exact hrspositive", "refl", "exact hzero", "have hs : ~(s = 0)", "intro hzero")
            + _apply("factor_nonzero_right", "r * s", "r", "s")
            + ("exact hrspositive", "refl", "exact hzero", "exists x", "exists x1", "split", "split", "intro hzero")
            + _apply("factor_nonzero_left", "r", "x", "x")
            + ("exact hr", "exact hsquares_witness_witness_left", "exact hzero", "split", "intro hzero")
            + _apply("factor_nonzero_left", "s", "x1", "x1")
            + ("exact hs", "exact hsquares_witness_witness_right", "exact hzero", "split", "exact hu",
               "trans (x * x) * (x * x) + (x1 * x1) * (x1 * x1)", "congr", "apply fourth_power_regroup", "apply fourth_power_regroup",
               "trans r * r + s * s", "congr", "congr", "symm", "exact hsquares_witness_witness_left", "symm", "exact hsquares_witness_witness_left",
               "congr", "symm", "exact hsquares_witness_witness_right", "symm", "exact hsquares_witness_witness_right", "trans m", "symm", "exact hmrs", "exact hm")
            + _apply("fermat_four_root_lt_norm", "u", "m", "n", "h")
            + ("exact hu", "exact hn", "exact hm", "exact hh"),
            "The second coprime parameter splitting constructs two positive fourth-power bases with square height strictly below the original norm.",
        ),
        spec(
            "fermat_four_primitive_square_triangle",
            f"forall a b h. ({primitive_four_counterexample('a','b','h',tag='triangle_source')}) -> "
            f"({primitive_pythagorean('a * a','b * b','h',tag='ffd_square_triangle')})",
            ("fermat_four_counterexample_is_pythagorean", "fermat_four_coprime_squares"),
            _intro("a", "b", "h", "hprimitive")
            + ("cases hprimitive", "cases hprimitive_left", "cases hprimitive_left_right", "cases hprimitive_left_right_right", "split",
               "apply fermat_four_counterexample_is_pythagorean", "exact hprimitive_left_right_right_right",
               "apply fermat_four_coprime_squares", "exact hprimitive_right"),
            "A primitive fourth-power counterexample is an actual primitive triangle with square legs.",
        ),
        spec(
            "fermat_four_primitive_counterexample_swap",
            f"forall a b h. ({primitive_four_counterexample('a','b','h',tag='swap_source')}) -> "
            f"({primitive_four_counterexample('b','a','h',tag='swap_result')})",
            ("add_comm", "coprime_symm"),
            _intro("a", "b", "h", "hprimitive")
            + ("cases hprimitive", "cases hprimitive_left", "cases hprimitive_left_right", "cases hprimitive_left_right_right",
               "split", "split", "exact hprimitive_left_right_left", "split", "exact hprimitive_left_left", "split",
               "exact hprimitive_left_right_right_left", "trans a * a * a * a + b * b * b * b", "apply add_comm",
               "exact hprimitive_left_right_right_right", "apply coprime_symm", "exact hprimitive_right"),
            "Swapping the positive fourth-power bases preserves the primitive counterexample relation.",
        ),
        spec(
            "fermat_four_primitive_odd_even_descent",
            f"forall a b h. ({primitive_four_counterexample('a','b','h',tag='oriented_source')}) -> "
            "(exists k. a * a = 2 * k + 1) -> (exists k. b * b = 2 * k) -> "
            f"exists A B H. ({fermat_four_descent_witness('A','B','H','h',tag='oriented_result')})",
            ("fermat_four_primitive_square_triangle", "pythagorean_primitive_odd_even_inverse", "fermat_four_square_nonzero",
             "fermat_four_nested_primitive_triangle", "pythagorean_primitive_hypotenuse_odd", "fermat_four_odd_double_square_factors",
             "pythagorean_positive_even_leg_parameters_nonzero", "factor_nonzero_left", "pythagorean_odd_square_has_odd_root",
             "fermat_four_second_parameter_descent"),
            _intro("a", "b", "h", "hprimitive", "haodd", "hbeven")
            + ("cases hprimitive", "cases hprimitive_left", "cases hprimitive_left_right", "cases hprimitive_left_right_right",
               f"have htriangle : {primitive_pythagorean('a * a','b * b','h',tag='ffd_oriented_triangle')}",
               "apply fermat_four_primitive_square_triangle", "exact hprimitive",
               f"have hfirst : exists m n. ({_parameters('a * a','b * b','h','m','n',tag='ffd_first_inverse')})")
            + _apply("pythagorean_primitive_odd_even_inverse", "a * a", "b * b", "h")
            + ("exact htriangle", "intro hzero")
            + _apply("fermat_four_square_nonzero", "a")
            + ("exact hprimitive_left_left", "exact hzero", "intro hzero")
            + _apply("fermat_four_square_nonzero", "b")
            + ("exact hprimitive_left_right_left", "exact hzero", "exact haodd", "exact hbeven",
               "cases hfirst", "cases hfirst_witness", "cases hfirst_witness_witness", "cases hfirst_witness_witness_right",
               "cases hfirst_witness_witness_right_right", "cases hfirst_witness_witness_right_right_right",
               "cases hfirst_witness_witness_right_right_right_right", "cases hfirst_witness_witness_right_right_right_right_right",
               f"have hnested : {primitive_pythagorean('a','x1','x',tag='ffd_oriented_nested')}")
            + _apply("fermat_four_nested_primitive_triangle", "a", "x", "x1")
            + ("exact hfirst_witness_witness_right_right_left", "exact hfirst_witness_witness_right_right_right_right_right_left",
               "have hmodd : exists k. x = 2 * k + 1")
            + _apply("pythagorean_primitive_hypotenuse_odd", "a", "x1", "x")
            + ("exact hnested", "have hdouble : exists u v. (x = u * u /\\ x1 = 2 * (v * v))")
            + _apply("fermat_four_odd_double_square_factors", "x", "x1", "b")
            + ("exact hfirst_witness_witness_right_right_left", "exact hmodd", "exact hfirst_witness_witness_right_right_right_right_right_right",
               "cases hdouble", "cases hdouble_witness", "cases hdouble_witness_witness",
               "have hparameterspositive : ~(x = 0) /\\ ~(x1 = 0)")
            + _apply("pythagorean_positive_even_leg_parameters_nonzero", "b * b", "x", "x1")
            + ("intro hzero",)
            + _apply("fermat_four_square_nonzero", "b")
            + ("exact hprimitive_left_right_left", "exact hzero", "exact hfirst_witness_witness_right_right_right_right_right_right",
               "cases hparameterspositive", "have hupositive : ~(x2 = 0)", "intro hzero")
            + _apply("factor_nonzero_left", "x", "x2", "x2")
            + ("exact hparameterspositive_left", "exact hdouble_witness_witness_left", "exact hzero",
               f"have hsecond : exists r s. ({_parameters('a','x1','x','r','s',tag='ffd_second_inverse')})")
            + _apply("pythagorean_primitive_odd_even_inverse", "a", "x1", "x")
            + ("exact hnested", "exact hprimitive_left_left", "exact hfirst_witness_witness_left",
               "apply pythagorean_odd_square_has_odd_root", "exact haodd", "exists x3 * x3", "exact hdouble_witness_witness_right",
               "cases hsecond", "cases hsecond_witness", "cases hsecond_witness_witness", "cases hsecond_witness_witness_right",
               "cases hsecond_witness_witness_right_right", "cases hsecond_witness_witness_right_right_right",
               "cases hsecond_witness_witness_right_right_right_right", "cases hsecond_witness_witness_right_right_right_right_right",
               f"have hsmaller : exists A B. ({fermat_four_descent_witness('A','B','x2','h',tag='oriented_smaller')})")
            + _apply("fermat_four_second_parameter_descent", "x2", "x", "x1", "x3", "x4", "x5", "h")
            + ("exact hupositive", "exact hfirst_witness_witness_left", "exact hsecond_witness_witness_right_right_left",
               "exact hdouble_witness_witness_left", "exact hdouble_witness_witness_right", "exact hsecond_witness_witness_right_right_right_right_left",
               "exact hsecond_witness_witness_right_right_right_right_right_right", "exact hfirst_witness_witness_right_right_right_right_left",
               "cases hsmaller", "cases hsmaller_witness", "exists x6", "exists x7", "exists x2", "exact hsmaller_witness_witness"),
            "Two actual primitive Pythagorean inversions and coprime square splittings construct a strictly smaller positive Fermat-four counterexample.",
        ),
        spec(
            "fermat_four_primitive_descent",
            f"forall a b h. ({primitive_four_counterexample('a','b','h',tag='primitive_descent_source')}) -> "
            f"exists A B H. ({fermat_four_descent_witness('A','B','H','h',tag='primitive_descent_result')})",
            ("fermat_four_primitive_square_triangle", "pythagorean_primitive_legs_opposite_parity",
             "fermat_four_primitive_counterexample_swap", "fermat_four_primitive_odd_even_descent"),
            _intro("a", "b", "h", "hprimitive")
            + (f"have htriangle : {primitive_pythagorean('a * a','b * b','h',tag='ffd_primitive_descent_triangle')}",
               "apply fermat_four_primitive_square_triangle", "exact hprimitive",
               f"have hparity : {opposite_parity('a * a','b * b',tag='ffd_primitive_descent_parity')}")
            + _apply("pythagorean_primitive_legs_opposite_parity", "a * a", "b * b", "h")
            + ("exact htriangle", "cases hparity", "cases hparity_left")
            + _apply("fermat_four_primitive_odd_even_descent", "b", "a", "h")
            + ("apply fermat_four_primitive_counterexample_swap", "exact hprimitive", "exact hparity_left_right", "exact hparity_left_left",
               "cases hparity_right")
            + _apply("fermat_four_primitive_odd_even_descent", "a", "b", "h")
            + ("exact hprimitive", "exact hparity_right_left", "exact hparity_right_right"),
            "Constructive parity selection orients every primitive counterexample and constructs a strictly smaller counterexample.",
        ),
        spec(
            "fermat_four_strict_descent_proved",
            fermat_four_strict_descent(tag="proved"),
            ("fermat_four_primitive_normalization", "fermat_four_primitive_descent", "lt_of_lt_of_le"),
            _intro("a", "b", "h", "hcounter")
            + ("have hnormalized : exists A B H. "
               f"(({primitive_four_counterexample('A','B','H',tag='strict_normalized')}) /\\ (exists k. k + H = h))",)
            + _apply("fermat_four_primitive_normalization", "a", "b", "h")
            + ("exact hcounter", "cases hnormalized", "cases hnormalized_witness", "cases hnormalized_witness_witness",
               "cases hnormalized_witness_witness_witness",
               f"have hsmaller : exists A B H. ({fermat_four_descent_witness('A','B','H','x2',tag='strict_smaller')})")
            + _apply("fermat_four_primitive_descent", "x", "x1", "x2")
            + ("exact hnormalized_witness_witness_witness_left", "cases hsmaller", "cases hsmaller_witness", "cases hsmaller_witness_witness",
               "cases hsmaller_witness_witness_witness", "exists x3", "exists x4", "exists x5", "split", "exact hsmaller_witness_witness_witness_left")
            + _apply("lt_of_lt_of_le", "x5", "x2", "h")
            + ("exact hsmaller_witness_witness_witness_right", "exact hnormalized_witness_witness_witness_right"),
            "Every positive fourth-power square counterexample constructs an actual positive counterexample with strictly smaller height; no descent premise remains.",
        ),
        spec(
            "fermat_four_no_square",
            f"forall a b h. ~({fermat_four_counterexample('a','b','h',tag='no_square')})",
            ("fermat_four_no_square_from_descent", "fermat_four_strict_descent_proved"),
            ("apply fermat_four_no_square_from_descent", "exact fermat_four_strict_descent_proved"),
            "Unconditional Fermat-four square obstruction follows by the already checked constructive induction theorem and the actual decreasing witness construction.",
        ),
        spec(
            "fermat_four_no_fourth",
            "forall a b h. ~(a = 0) -> ~(b = 0) -> ~(h = 0) -> "
            "~(a * a * a * a + b * b * b * b = h * h * h * h)",
            ("fermat_four_no_fourth_from_descent", "fermat_four_strict_descent_proved"),
            ("apply fermat_four_no_fourth_from_descent", "exact fermat_four_strict_descent_proved"),
            "Fermat's last theorem for exponent four holds unconditionally for every positive natural triple in unchanged Heyting arithmetic.",
        ),
        spec(
            "fermat_four_equation_height_nonzero",
            "forall a b h. ~(a = 0) -> a * a * a * a + b * b * b * b = h * h -> ~(h = 0)",
            ("fermat_four_square_nonzero", "fourth_power_regroup", "add_eq_zero_left", "mul_zero_left"),
            _intro("a", "b", "h", "ha", "hequation", "hzero")
            + ("have hsquare : ~(a * a = 0)", "intro hz")
            + _apply("fermat_four_square_nonzero", "a")
            + ("exact ha", "exact hz", "have hfourth : ~((a * a) * (a * a) = 0)", "intro hz")
            + _apply("fermat_four_square_nonzero", "a * a")
            + ("exact hsquare", "exact hz", "apply hfourth", "trans a * a * a * a", "symm", "apply fourth_power_regroup")
            + _apply("add_eq_zero_left", "a * a * a * a", "b * b * b * b")
            + ("trans h * h", "exact hequation", "simp [hzero, mul_zero_left]"),
            "A nonzero first fourth-power summand forces the square hypotenuse to be nonzero, so its positivity need not be assumed.",
        ),
        spec(
            "fermat_four_square_solutions_have_zero_coordinate",
            "forall a b h. a * a * a * a + b * b * b * b = h * h -> (a = 0 \\/ b = 0)",
            ("eq_decidable", "fermat_four_no_square", "fermat_four_equation_height_nonzero"),
            _intro("a", "b", "h", "hequation")
            + ("have hacases : a = 0 \\/ ~(a = 0)", "apply eq_decidable", "cases hacases", "left", "exact hacases_left",
               "have hbcases : b = 0 \\/ ~(b = 0)", "apply eq_decidable", "cases hbcases", "right", "exact hbcases_left", "exfalso")
            + _apply("fermat_four_no_square", "a", "b", "h")
            + ("split", "exact hacases_right", "split", "exact hbcases_right", "split", "intro hzero")
            + _apply("fermat_four_equation_height_nonzero", "a", "b", "h")
            + ("exact hacases_right", "exact hequation", "exact hzero", "exact hequation"),
            "Every natural solution of a fourth-power sum equal to a square has a zero summand, including the entire zero boundary.",
        ),
        spec(
            "fermat_four_solutions_have_zero_coordinate",
            "forall a b h. a * a * a * a + b * b * b * b = h * h * h * h -> (a = 0 \\/ b = 0)",
            ("fermat_four_square_solutions_have_zero_coordinate", "fourth_power_regroup"),
            _intro("a", "b", "h", "hequation")
            + _apply("fermat_four_square_solutions_have_zero_coordinate", "a", "b", "h * h")
            + ("trans h * h * h * h", "exact hequation", "apply fourth_power_regroup"),
            "Fermat exponent four has no nontrivial natural solution, without any separate positivity assumptions.",
        ),
        spec(
            "fermat_four_complete_classification",
            "forall a b h. "
            f"((a * a * a * a + b * b * b * b = h * h * h * h -> ({fermat_four_trivial_solution('a','b','h',tag='classify_forward')})) /\\ "
            f"(({fermat_four_trivial_solution('a','b','h',tag='classify_backward')}) -> a * a * a * a + b * b * b * b = h * h * h * h))",
            ("fermat_four_solutions_have_zero_coordinate", "square_eq_injective", "fourth_power_regroup", "mul_zero_left", "zero_add"),
            _intro("a", "b", "h")
            + ("split", "intro hequation", "have hzero : a = 0 \\/ b = 0", "apply fermat_four_solutions_have_zero_coordinate", "exact hequation",
               "cases hzero", "left", "split", "exact hzero_left", "apply square_eq_injective", "apply square_eq_injective",
               "trans b * b * b * b", "symm", "apply fourth_power_regroup", "trans h * h * h * h", "trans a * a * a * a + b * b * b * b",
               "symm", "simp [hzero_left, mul_zero_left, zero_add]", "exact hequation", "apply fourth_power_regroup",
               "right", "split", "exact hzero_right", "apply square_eq_injective", "apply square_eq_injective",
               "trans a * a * a * a", "symm", "apply fourth_power_regroup", "trans h * h * h * h", "trans a * a * a * a + b * b * b * b",
               "symm", "simp [hzero_right, mul_zero_left, zero_add]", "exact hequation", "apply fourth_power_regroup",
               "intro htrivial", "cases htrivial", "cases htrivial_left", "simp [htrivial_left_left, htrivial_left_right, mul_zero_left, zero_add]",
               "cases htrivial_right", "simp [htrivial_right_left, htrivial_right_right, mul_zero_left, zero_add]"),
            "The complete constructive classification is exact: a fourth-power solution has one zero base and its other base equal to the height, and every such triple is a solution.",
        ),
        spec(
            "fermat_four_positive_sum_not_square",
            "forall x y z. ~(x = 0) -> ~(y = 0) -> ~(x * x * x * x + y * y * y * y = z * z)",
            ("fermat_four_square_solutions_have_zero_coordinate",),
            _intro("x", "y", "z", "hx", "hy", "hequation")
            + ("have hzero : x = 0 \\/ y = 0",)
            + _apply("fermat_four_square_solutions_have_zero_coordinate", "x", "y", "z")
            + ("exact hequation", "cases hzero", "apply hx", "exact hzero_left", "apply hy", "exact hzero_right"),
            "Exact campaign G078: the sum of two positive fourth powers is never a square, for every natural z including zero.",
        ),
    )


__all__ = [
    "FermatFourDescentError",
    "primitive_four_counterexample",
    "fermat_four_descent_witness",
    "fermat_four_trivial_solution",
    "make_fermat_four_descent_candidate_theorems",
]
