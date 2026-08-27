"""Positive primitive Pythagorean classification in unextended Heyting arithmetic.

The inverse constructs the two natural half-factors of the odd hypotenuse and
odd leg.  They are coprime and their product is the square of the even-leg
half, so constructive coprime square-factor extraction recovers Euclid's
parameters.  Every abbreviation below expands into the original language;
positivity is explicit, unlike the historical zero-permitting primitive
triple relation.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import _identifier
from .pythagorean_fermat_four_candidate import (
    coprime_coordinates,
    primitive_pythagorean,
    pythagorean_triple,
)
from .pythagorean_primitive_candidate import (
    even_coordinate,
    odd_coordinate,
    opposite_parity,
)


def _arguments(*values: str) -> tuple[str, ...]:
    arguments = tuple(_identifier(value, "Pythagorean relation argument") for value in values)
    if any(value.startswith(("pi_", "pp_", "pff_")) for value in arguments):
        raise ValueError("Pythagorean generated binder would capture an argument")
    return arguments


def _positive(first: str, second: str, hypotenuse: str, *, tag: str) -> str:
    return (
        f"(~(({first}) = 0) /\\ (~(({second}) = 0) /\\ "
        f"(~(({hypotenuse}) = 0) /\\ "
        f"({primitive_pythagorean(first, second, hypotenuse, tag=f'pi_{tag}')}))))"
    )


def positive_primitive_pythagorean(
    first: str, second: str, hypotenuse: str, *, tag: str
) -> str:
    """Expand exactly three positive coordinates, the equation, and coprimality."""

    arguments = _arguments(first, second, hypotenuse)
    return _positive(*arguments, tag=_identifier(tag, "Pythagorean binder tag"))


def _parameters(
    first: str,
    second: str,
    hypotenuse: str,
    larger: str,
    smaller: str,
    *,
    tag: str,
) -> str:
    gap = f"pi_gap_{tag}"
    coprime = coprime_coordinates(larger, smaller, tag=f"pi_{tag}_coprime")
    parity = opposite_parity(larger, smaller, tag=f"pi_{tag}_parity")
    return (
        f"(~(({smaller}) = 0) /\\ "
        f"((exists {gap}. {gap} + S ({smaller}) = ({larger})) /\\ "
        f"(({coprime}) /\\ (({parity}) /\\ "
        f"(({hypotenuse}) = ({larger}) * ({larger}) + ({smaller}) * ({smaller}) /\\ "
        f"(({larger}) * ({larger}) = ({smaller}) * ({smaller}) + ({first}) /\\ "
        f"({second}) = 2 * (({larger}) * ({smaller}))))))))"
    )


def euclidean_parameter_witness(
    first: str,
    second: str,
    hypotenuse: str,
    larger: str,
    smaller: str,
    *,
    tag: str,
) -> str:
    """Expand positive ordered coprime opposite-parity Euclid parameters."""

    arguments = _arguments(first, second, hypotenuse, larger, smaller)
    return _parameters(*arguments, tag=_identifier(tag, "Pythagorean binder tag"))


def _either_parameters(first: str, second: str, hypotenuse: str, larger: str, smaller: str, *, tag: str) -> str:
    gap = f"pi_gap_{tag}"
    coprime = coprime_coordinates(larger, smaller, tag=f"pi_{tag}_coprime")
    parity = opposite_parity(larger, smaller, tag=f"pi_{tag}_parity")
    first_orientation = (
        f"({larger}) * ({larger}) = ({smaller}) * ({smaller}) + ({first}) /\\ "
        f"({second}) = 2 * (({larger}) * ({smaller}))"
    )
    second_orientation = (
        f"({larger}) * ({larger}) = ({smaller}) * ({smaller}) + ({second}) /\\ "
        f"({first}) = 2 * (({larger}) * ({smaller}))"
    )
    return (
        f"(~(({smaller}) = 0) /\\ "
        f"((exists {gap}. {gap} + S ({smaller}) = ({larger})) /\\ "
        f"(({coprime}) /\\ (({parity}) /\\ "
        f"(({hypotenuse}) = ({larger}) * ({larger}) + ({smaller}) * ({smaller}) /\\ "
        f"(({first_orientation}) \\/ ({second_orientation})))))))"
    )


def euclidean_parametrization(first: str, second: str, hypotenuse: str, *, tag: str) -> str:
    """Expand existence of Euclid parameters in either ordered leg orientation."""

    arguments = _arguments(first, second, hypotenuse)
    safe = _identifier(tag, "Pythagorean binder tag")
    larger, smaller = f"pi_larger_{safe}", f"pi_smaller_{safe}"
    return f"exists {larger} {smaller}. ({_either_parameters(*arguments, larger, smaller, tag=safe)})"


def _intros(names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names.split())


def _specialize(name: str, *terms: str) -> tuple[str, ...]:
    return tuple(f"specialize {name} {term}" for term in terms)


def _unpack(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_right" * depth for depth in range(count))


def _copy_common_parameters(name: str) -> tuple[str, ...]:
    return tuple(command for depth in range(5) for command in ("split", "exact " + name + "_right" * depth + "_left"))


def make_pythagorean_inverse_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Build dependency-ordered actual HA tactic bodies, without admission."""

    rows: list[Any] = []

    def add(name: str, statement: str, dependencies: tuple[str, ...], commands: tuple[str, ...], description: str) -> None:
        rows.append(spec(name, statement, dependencies, commands, description))

    cop = lambda a, b, tag: coprime_coordinates(a, b, tag=f"pi_{tag}")
    odd = lambda a, tag: odd_coordinate(a, tag=f"pi_{tag}")
    even = lambda a, tag: even_coordinate(a, tag=f"pi_{tag}")
    primitive = primitive_pythagorean("a", "b", "c", tag="pi_source")

    add(
        "pythagorean_positive_add_strict",
        "forall a b. ~(b = 0) -> exists gap. gap + S a = a + b",
        ("nonzero_is_succ", "add_comm", "add_succ_left"),
        _intros("a b hb")
        + _specialize("nonzero_is_succ", "b")
        + (
            "have hsuccessor : exists k. b = S k", "apply nonzero_is_succ", "exact hb",
            "cases hsuccessor", "exists x", "rewrite hsuccessor_witness",
            "simp [add_comm, add_succ_left]",
        ),
        "Adding a positive natural gives an explicitly witnessed strict increase.",
    )
    add(
        "pythagorean_leg_strictly_below_hypotenuse",
        "forall a b c. a * a + b * b = c * c -> ~(b = 0) -> "
        "exists gap. gap + S a = c",
        ("pythagorean_positive_add_strict", "mul_ne_zero", "square_lt_reflect"),
        _intros("a b c hequation hb")
        + (
            "have hsquare : ~(b * b = 0)", "intro hzero", "apply mul_ne_zero", "exact hb", "exact hb", "exact hzero",
            "have hstrict : exists gap. gap + S (a * a) = c * c",
            "rewrite <- hequation",
        )
        + _specialize("pythagorean_positive_add_strict", "(a * a)", "(b * b)")
        + ("apply pythagorean_positive_add_strict", "exact hsquare", "apply square_lt_reflect", "exact hstrict"),
        "Each leg of a Pythagorean triangle is strictly below the hypotenuse when the other leg is positive.",
    )
    add(
        "pythagorean_odd_ordered_difference_even",
        f"forall a c. (exists gap. gap + a = c) -> ({odd('a', 'difference_a')}) -> "
        f"({odd('c', 'difference_c')}) -> exists t. c = a + 2 * t",
        ("odd_sum_parity_cases", "even_odd_exclusive_pointwise", "add_comm"),
        _intros("a c hbound ha hc")
        + (
            "cases hbound",
            f"have hsum : {odd('a + x', 'difference_sum')}",
            "cases hc", "exists x1", "trans c", "trans x + a", "apply add_comm", "exact hbound_witness", "exact hc_witness",
            f"have hparity : {opposite_parity('a', 'x', tag='pi_difference_parity')}",
        )
        + _specialize("odd_sum_parity_cases", "a", "x")
        + (
            "apply odd_sum_parity_cases", "exact hsum", "cases hparity", "cases hparity_left", "exfalso",
            "cases hparity_left_left", "cases ha",
        )
        + _specialize("even_odd_exclusive_pointwise", "a", "x1", "x2")
        + (
            "apply even_odd_exclusive_pointwise", "exact hparity_left_left_witness", "exact ha_witness",
            "cases hparity_right", "cases hparity_right_right", "exists x1", "trans a + x", "trans x + a", "symm", "exact hbound_witness", "apply add_comm", "congr", "refl", "exact hparity_right_right_witness",
        ),
        "The natural difference of ordered odd numbers has a constructive even-half witness.",
    )
    add(
        "pythagorean_half_sum_reassociation",
        "forall a t. (a + 2 * t) + a = 2 * (a + t)",
        ("two_mul_eq_add_self", "add_assoc", "add_comm"),
        _intros("a t") + ("simp [two_mul_eq_add_self, add_assoc, add_comm]",),
        "The sum of an odd leg and its even-shifted hypotenuse is twice the upper half-factor.",
    )
    add(
        "pythagorean_half_hypotenuse_reassociation",
        "forall a t. a + 2 * t = (a + t) + t",
        ("two_mul_eq_add_self", "add_assoc"),
        _intros("a t") + ("simp [two_mul_eq_add_self, add_assoc]",),
        "The two natural half-factors add exactly to the hypotenuse.",
    )
    add(
        "pythagorean_half_product_is_square",
        "forall a c h t. a * a + (2 * h) * (2 * h) = c * c -> "
        "c = a + 2 * t -> (a + t) * t = h * h",
        (
            "four_square_ordered_square_difference_factor", "pythagorean_half_sum_reassociation",
            "four_square_product_shuffle", "four_square_product_square", "add_left_cancel",
            "mul_left_cancel_nonzero", "mul_ne_zero", "succ_ne_zero", "mul_comm",
        ),
        _intros("a c h t hequation hgap")
        + (
            "have hfactor : a * a + (2 * t) * (c + a) = c * c",
        )
        + _specialize("four_square_ordered_square_difference_factor", "a", "c", "(2 * t)")
        + (
            "apply four_square_ordered_square_difference_factor", "exact hgap",
            "have hsum : c + a = 2 * (a + t)", "rewrite hgap", "apply pythagorean_half_sum_reassociation",
            "rewrite hsum at hfactor",
            "have hcancel : (2 * h) * (2 * h) = (2 * t) * (2 * (a + t))",
        )
        + _specialize("add_left_cancel", "(a * a)", "((2 * h) * (2 * h))", "((2 * t) * (2 * (a + t)))")
        + (
            "apply add_left_cancel", "trans c * c", "exact hequation", "symm", "exact hfactor",
            "have hproduct : (2 * 2) * (h * h) = (2 * 2) * (t * (a + t))",
            "trans (2 * h) * (2 * h)", "symm", "apply four_square_product_square",
            "trans (2 * t) * (2 * (a + t))", "exact hcancel", "apply four_square_product_shuffle",
            "have hhalf : h * h = t * (a + t)",
        )
        + _specialize("mul_left_cancel_nonzero", "(2 * 2)", "(h * h)", "(t * (a + t))")
        + (
            "apply mul_left_cancel_nonzero", "intro hzero", "apply mul_ne_zero", "intro htwo", "apply succ_ne_zero", "exact htwo", "intro htwo", "apply succ_ne_zero", "exact htwo", "exact hzero", "exact hproduct",
            "trans t * (a + t)", "apply mul_comm", "symm", "exact hhalf",
        ),
        "Cancelling the exact square of two proves that the two half-factors multiply to the even-leg half-square.",
    )
    add(
        "pythagorean_half_factors_coprime",
        f"forall a c t. ({cop('a', 'c', 'half_source')}) -> c = a + 2 * t -> "
        f"({cop('a + t', 't', 'half_result')})",
        ("divides_remainder", "multiple_add", "pythagorean_half_hypotenuse_reassociation", "mul_one", "add_comm"),
        _intros("a c t hcop hgap divisor hu hv")
        + (
            "have ha : exists q. a = divisor * q",
        )
        + _specialize("divides_remainder", "divisor", "(a + t)", "t", "1", "a")
        + (
            "apply divides_remainder", "exact hu", "exact hv", "trans t + a", "apply add_comm", "congr", "symm", "apply mul_one", "refl",
            "have hc : exists q. c = divisor * q", "rewrite hgap",
        )
        + _specialize("pythagorean_half_hypotenuse_reassociation", "a", "t")
        + ("rewrite pythagorean_half_hypotenuse_reassociation",)
        + _specialize("multiple_add", "divisor", "(a + t)", "t")
        + ("apply multiple_add", "exact hu", "exact hv")
        + _specialize("hcop", "divisor")
        + ("apply hcop", "exact ha", "exact hc"),
        "Every common divisor of the two half-factors divides the original odd leg and hypotenuse, so the factors are coprime.",
    )
    add(
        "pythagorean_coprime_square_roots",
        f"forall m n. ({cop('m * m', 'n * n', 'root_source')}) -> ({cop('m', 'n', 'root_result')})",
        ("pythagorean_parameter_divisor_divides_square",),
        _intros("m n hcop divisor hm hn")
        + _specialize("hcop", "divisor")
        + (
            "apply hcop", "apply pythagorean_parameter_divisor_divides_square", "exact hm",
            "apply pythagorean_parameter_divisor_divides_square", "exact hn",
        ),
        "Coprimality of two natural squares implies coprimality of their explicit roots.",
    )
    add(
        "pythagorean_even_square_has_even_root",
        f"forall a. ({even('a * a', 'even_square')}) -> ({even('a', 'even_root')})",
        ("pythagorean_coordinate_parity_choice", "pythagorean_parameter_odd_square", "even_odd_exclusive_pointwise"),
        _intros("a heven")
        + _specialize("pythagorean_coordinate_parity_choice", "a")
        + (
            "cases pythagorean_coordinate_parity_choice", "exact pythagorean_coordinate_parity_choice_left", "exfalso",
            f"have hodd : {odd('a * a', 'square_contradiction')}",
            "apply pythagorean_parameter_odd_square", "exact pythagorean_coordinate_parity_choice_right",
            "cases heven", "cases hodd",
        )
        + _specialize("even_odd_exclusive_pointwise", "(a * a)", "x", "x1")
        + ("apply even_odd_exclusive_pointwise", "exact heven_witness", "exact hodd_witness"),
        "An explicitly even natural square has an explicitly even natural square root.",
    )
    add(
        "pythagorean_odd_square_sum_opposite_roots",
        f"forall m n. ({odd('m * m + n * n', 'odd_norm')}) -> "
        f"({opposite_parity('m', 'n', tag='pi_norm_parameters')})",
        ("odd_sum_parity_cases", "pythagorean_even_square_has_even_root", "pythagorean_odd_square_has_odd_root"),
        _intros("m n hodd")
        + (
            f"have hparity : {opposite_parity('m * m', 'n * n', tag='pi_norm_square_parity')}",
        )
        + _specialize("odd_sum_parity_cases", "(m * m)", "(n * n)")
        + (
            "apply odd_sum_parity_cases", "exact hodd", "cases hparity", "cases hparity_left", "left", "split",
            "apply pythagorean_even_square_has_even_root", "exact hparity_left_left", "apply pythagorean_odd_square_has_odd_root", "exact hparity_left_right",
            "cases hparity_right", "right", "split", "apply pythagorean_odd_square_has_odd_root", "exact hparity_right_left", "apply pythagorean_even_square_has_even_root", "exact hparity_right_right",
        ),
        "An odd sum of two squares supplies a constructive choice of opposite parity for their roots.",
    )
    add(
        "pythagorean_half_roots_coordinates",
        "forall a c t m n. c = a + 2 * t -> a + t = m * m -> t = n * n -> "
        "(c = m * m + n * n /\\ m * m = n * n + a)",
        ("pythagorean_half_hypotenuse_reassociation", "add_comm"),
        _intros("a c t m n hc hm hn")
        + (
            "split", "trans (a + t) + t", "trans a + 2 * t", "exact hc", "apply pythagorean_half_hypotenuse_reassociation", "congr", "exact hm", "exact hn",
            "trans a + t", "symm", "exact hm", "trans t + a", "apply add_comm", "congr", "exact hn", "refl",
        ),
        "The roots of the half-factors give the hypotenuse sum and the exact subtraction-free odd-leg gap.",
    )
    add(
        "pythagorean_half_roots_even_leg",
        "forall a t h m n. (a + t) * t = h * h -> a + t = m * m -> t = n * n -> "
        "2 * h = 2 * (m * n)",
        ("four_square_product_square", "square_eq_injective"),
        _intros("a t h m n hproduct hm hn")
        + (
            "have hsquares : h * h = (m * n) * (m * n)", "trans (a + t) * t", "symm", "exact hproduct",
            "trans (m * m) * (n * n)", "congr", "exact hm", "exact hn", "symm", "apply four_square_product_square",
            "congr", "refl", "apply square_eq_injective", "exact hsquares",
        ),
        "Natural square-root injectivity identifies the even leg with twice the product of the constructed parameters.",
    )
    add(
        "pythagorean_positive_gap_orders_parameters",
        "forall a m n. ~(a = 0) -> m * m = n * n + a -> exists gap. gap + S n = m",
        ("pythagorean_positive_add_strict", "square_lt_reflect"),
        _intros("a m n ha hgap")
        + ("have hstrict : exists gap. gap + S (n * n) = m * m", "rewrite hgap")
        + _specialize("pythagorean_positive_add_strict", "(n * n)", "a")
        + ("apply pythagorean_positive_add_strict", "exact ha", "apply square_lt_reflect", "exact hstrict"),
        "The positive odd leg forces the two natural square roots into the required strict Euclidean order.",
    )
    add(
        "pythagorean_positive_even_leg_parameters_nonzero",
        "forall b m n. ~(b = 0) -> b = 2 * (m * n) -> (~(m = 0) /\\ ~(n = 0))",
        ("factor_nonzero_right", "mul_zero_left"),
        _intros("b m n hb heq")
        + ("have hproduct : ~(m * n = 0)", "intro hzero")
        + _specialize("factor_nonzero_right", "b", "2", "(m * n)")
        + ("apply factor_nonzero_right", "exact hb", "exact heq", "exact hzero", "split", "intro hm", "apply hproduct", "rewrite hm", "apply mul_zero_left", "intro hn", "apply hproduct", "rewrite hn", "simp"),
        "A positive even leg forces both explicitly constructed Euclidean parameters to be positive.",
    )
    add(
        "pythagorean_odd_even_half_factors",
        f"forall a b c. ({primitive}) -> ~(b = 0) -> ({odd('a', 'half_a')}) -> "
        f"({even('b', 'half_b')}) -> exists h t. "
        f"(b = 2 * h /\\ (c = a + 2 * t /\\ "
        f"((a + t) * t = h * h /\\ ({cop('a + t', 't', 'half_coprime')}))))",
        (
            "pythagorean_primitive_hypotenuse_coprime_first_leg", "pythagorean_primitive_hypotenuse_odd",
            "pythagorean_leg_strictly_below_hypotenuse", "lt_to_le", "pythagorean_odd_ordered_difference_even",
            "pythagorean_half_product_is_square", "pythagorean_half_factors_coprime",
        ),
        _intros("a b c hp hb haodd hbeven")
        + (f"have hcop : {cop('a', 'c', 'half_pair')}",)
        + _specialize("pythagorean_primitive_hypotenuse_coprime_first_leg", "a", "b", "c")
        + ("apply pythagorean_primitive_hypotenuse_coprime_first_leg", "exact hp", f"have hcodd : {odd('c', 'half_hypotenuse')}")
        + _specialize("pythagorean_primitive_hypotenuse_odd", "a", "b", "c")
        + (
            "apply pythagorean_primitive_hypotenuse_odd", "exact hp",
            "have hbound : exists gap. gap + a = c", "apply lt_to_le",
        )
        + _specialize("pythagorean_leg_strictly_below_hypotenuse", "a", "b", "c")
        + (
            "apply pythagorean_leg_strictly_below_hypotenuse", "cases hp", "exact hp_left", "exact hb",
            "have hgap : exists t. c = a + 2 * t", "apply pythagorean_odd_ordered_difference_even", "exact hbound", "exact haodd", "exact hcodd",
            "cases hgap", "cases hbeven", "exists x1", "exists x", "split", "exact hbeven_witness", "split", "exact hgap_witness", "split",
        )
        + _specialize("pythagorean_half_product_is_square", "a", "c", "x1", "x")
        + (
            "apply pythagorean_half_product_is_square", "rewrite <- hbeven_witness", "rewrite <- hbeven_witness", "cases hp", "exact hp_left", "exact hgap_witness",
        )
        + _specialize("pythagorean_half_factors_coprime", "a", "c", "x")
        + ("apply pythagorean_half_factors_coprime", "exact hcop", "exact hgap_witness"),
        "Every positive-even-leg primitive triangle constructs both coprime half-factors and their actual square-product equation.",
    )
    add(
        "pythagorean_half_factors_extract_parameters",
        f"forall a b c h t. ~(a = 0) -> ~(b = 0) -> ({odd('c', 'extract_c')}) -> "
        f"b = 2 * h -> c = a + 2 * t -> (a + t) * t = h * h -> "
        f"({cop('a + t', 't', 'extract_source')}) -> "
        f"exists m n. ({_parameters('a', 'b', 'c', 'm', 'n', tag='extract_result')})",
        (
            "coprime_square_product_factors", "pythagorean_half_roots_coordinates", "pythagorean_half_roots_even_leg",
            "pythagorean_coprime_square_roots", "pythagorean_positive_even_leg_parameters_nonzero",
            "pythagorean_positive_gap_orders_parameters", "pythagorean_odd_square_sum_opposite_roots",
        ),
        _intros("a b c h t ha hb hcodd hbeq hceq hproduct hcop")
        + ("have hroots : exists m n. a + t = m * m /\\ t = n * n",)
        + _specialize("coprime_square_product_factors", "(a + t)", "t", "h")
        + (
            "apply coprime_square_product_factors", "exact hcop", "exact hproduct",
            "cases hroots", "cases hroots_witness", "cases hroots_witness_witness",
            "have hcoordinates : c = x * x + x1 * x1 /\\ x * x = x1 * x1 + a",
        )
        + _specialize("pythagorean_half_roots_coordinates", "a", "c", "t", "x", "x1")
        + (
            "apply pythagorean_half_roots_coordinates", "exact hceq", "exact hroots_witness_witness_left", "exact hroots_witness_witness_right",
            "cases hcoordinates", "have hleg : b = 2 * (x * x1)", "trans 2 * h", "exact hbeq",
        )
        + _specialize("pythagorean_half_roots_even_leg", "a", "t", "h", "x", "x1")
        + (
            "apply pythagorean_half_roots_even_leg", "exact hproduct", "exact hroots_witness_witness_left", "exact hroots_witness_witness_right",
            "have hpositive : ~(x = 0) /\\ ~(x1 = 0)",
        )
        + _specialize("pythagorean_positive_even_leg_parameters_nonzero", "b", "x", "x1")
        + (
            "apply pythagorean_positive_even_leg_parameters_nonzero", "exact hb", "exact hleg", "cases hpositive",
            "exists x", "exists x1", "split", "exact hpositive_right", "split",
        )
        + _specialize("pythagorean_positive_gap_orders_parameters", "a", "x", "x1")
        + (
            "apply pythagorean_positive_gap_orders_parameters", "exact ha", "exact hcoordinates_right", "split",
        )
        + _specialize("pythagorean_coprime_square_roots", "x", "x1")
        + (
            "apply pythagorean_coprime_square_roots", "rewrite <- hroots_witness_witness_left", "rewrite <- hroots_witness_witness_right", "exact hcop", "split",
        )
        + _specialize("pythagorean_odd_square_sum_opposite_roots", "x", "x1")
        + (
            "apply pythagorean_odd_square_sum_opposite_roots", "rewrite <- hcoordinates_left", "exact hcodd",
            "split", "exact hcoordinates_left", "split", "exact hcoordinates_right", "exact hleg",
        ),
        "Constructive coprime square-factor extraction recovers positive ordered coprime opposite-parity Euclid parameters and every coordinate equation.",
    )
    add(
        "pythagorean_primitive_odd_even_inverse",
        f"forall a b c. ({primitive}) -> ~(a = 0) -> ~(b = 0) -> "
        f"({odd('a', 'inverse_a')}) -> ({even('b', 'inverse_b')}) -> "
        f"exists m n. ({_parameters('a', 'b', 'c', 'm', 'n', tag='inverse_result')})",
        (
            "pythagorean_odd_even_half_factors", "pythagorean_primitive_hypotenuse_odd", "pythagorean_half_factors_extract_parameters",
        ),
        _intros("a b c hp ha hb haodd hbeven")
        + (
            "have hhalves : exists h t. "
            f"(b = 2 * h /\\ (c = a + 2 * t /\\ ((a + t) * t = h * h /\\ ({cop('a + t', 't', 'inverse_halves')}))))",
        )
        + _specialize("pythagorean_odd_even_half_factors", "a", "b", "c")
        + (
            "apply pythagorean_odd_even_half_factors", "exact hp", "exact hb", "exact haodd", "exact hbeven",
            "cases hhalves", "cases hhalves_witness", "cases hhalves_witness_witness", "cases hhalves_witness_witness_right", "cases hhalves_witness_witness_right_right",
        )
        + _specialize("pythagorean_half_factors_extract_parameters", "a", "b", "c", "x", "x1")
        + ("apply pythagorean_half_factors_extract_parameters", "exact ha", "exact hb")
        + _specialize("pythagorean_primitive_hypotenuse_odd", "a", "b", "c")
        + (
            "apply pythagorean_primitive_hypotenuse_odd", "exact hp",
            "exact hhalves_witness_witness_left", "exact hhalves_witness_witness_right_left",
            "exact hhalves_witness_witness_right_right_left", "exact hhalves_witness_witness_right_right_right",
        ),
        "Every primitive Pythagorean triangle with positive legs in odd-even order has a fully witnessed Euclidean inverse parametrization.",
    )
    add(
        "pythagorean_positive_primitive_leg_swap",
        f"forall a b c. ({_positive('a', 'b', 'c', tag='swap_source')}) -> "
        f"({_positive('b', 'a', 'c', tag='swap_result')})",
        ("pythagorean_primitive_leg_swap",),
        _intros("a b c hp") + _unpack("hp", 3)
        + (
            "split", "exact hp_right_left", "split", "exact hp_left", "split", "exact hp_right_right_left",
        )
        + _specialize("pythagorean_primitive_leg_swap", "a", "b", "c")
        + ("apply pythagorean_primitive_leg_swap", "exact hp_right_right_right"),
        "Swapping positive primitive legs preserves the full exact positive triple definition.",
    )
    inverse_branches: list[str] = []
    for parity_branch, first, second, first_nonzero, second_nonzero, odd_hyp, even_hyp, orientation in (
        ("hparity_left", "b", "a", "hp_right_left", "hp_left", "hparity_left_right", "hparity_left_left", "right"),
        ("hparity_right", "a", "b", "hp_left", "hp_right_left", "hparity_right_left", "hparity_right_right", "left"),
    ):
        inverse_branches.extend((
            f"cases {parity_branch}",
            f"have hparameters : exists m n. ({_parameters(first, second, 'c', 'm', 'n', tag='choice')})",
            *_specialize("pythagorean_primitive_odd_even_inverse", first, second, "c"),
            "apply pythagorean_primitive_odd_even_inverse",
        ))
        if first == "b":
            inverse_branches.extend((
                *_specialize("pythagorean_primitive_leg_swap", "a", "b", "c"),
                "apply pythagorean_primitive_leg_swap", "exact hp_right_right_right",
            ))
        else:
            inverse_branches.append("exact hp_right_right_right")
        inverse_branches.extend((
            f"exact {first_nonzero}", f"exact {second_nonzero}", f"exact {odd_hyp}", f"exact {even_hyp}",
            "cases hparameters", "cases hparameters_witness", *_unpack("hparameters_witness_witness", 5),
            "exists x", "exists x1", *_copy_common_parameters("hparameters_witness_witness"), orientation,
            "exact hparameters_witness_witness" + "_right" * 5,
        ))
    add(
        "pythagorean_positive_primitive_inverse",
        f"forall a b c. ({_positive('a', 'b', 'c', tag='inverse_positive')}) -> "
        f"({euclidean_parametrization('a', 'b', 'c', tag='inverse_either')})",
        ("pythagorean_primitive_legs_opposite_parity", "pythagorean_primitive_leg_swap", "pythagorean_primitive_odd_even_inverse"),
        _intros("a b c hp") + _unpack("hp", 3)
        + (f"have hparity : {opposite_parity('a', 'b', tag='pi_inverse_choice')}",)
        + _specialize("pythagorean_primitive_legs_opposite_parity", "a", "b", "c")
        + ("apply pythagorean_primitive_legs_opposite_parity", "exact hp_right_right_right", "cases hparity")
        + tuple(inverse_branches),
        "Every positive primitive ordered Pythagorean triple has positive ordered coprime opposite-parity Euclidean parameters in one of both leg orientations.",
    )
    add(
        "pythagorean_ordered_gap_positive",
        "forall a m n. ~(n = 0) -> (exists gap. gap + S n = m) -> "
        "m * m = n * n + a -> (~(m = 0) /\\ ~(a = 0))",
        ("lt_to_le", "le_zero", "square_eq_injective", "lt_irrefl_expanded"),
        _intros("a m n hn horder hgap")
        + (
            "split", "intro hm", "apply hn", "apply le_zero", "rewrite <- hm", "apply lt_to_le", "exact horder",
            "intro ha", "have hsquare : m * m = n * n", "trans n * n + a", "exact hgap", "simp [ha]",
            "have hequal : m = n", "apply square_eq_injective", "exact hsquare", "rewrite hequal at horder",
            "apply lt_irrefl_expanded", "exact horder",
        ),
        "Strictly ordered parameters with a positive smaller parameter have a positive larger parameter and a positive exact square gap.",
    )
    add(
        "pythagorean_euclidean_parameters_positive_constructor",
        f"forall a b c m n. ({_parameters('a', 'b', 'c', 'm', 'n', tag='forward_parameters')}) -> "
        f"({_positive('a', 'b', 'c', tag='forward_positive')})",
        ("pythagorean_ordered_gap_positive", "pythagorean_primitive_euclidean_constructor", "pythagorean_hypotenuse_nonzero", "mul_ne_zero", "succ_ne_zero"),
        _intros("a b c m n hp") + _unpack("hp", 6)
        + ("have hpositive : ~(m = 0) /\\ ~(a = 0)",)
        + _specialize("pythagorean_ordered_gap_positive", "a", "m", "n")
        + (
            "apply pythagorean_ordered_gap_positive", "exact hp_left", "exact hp_right_left", "exact hp_right_right_right_right_right_left", "cases hpositive",
            "split", "exact hpositive_right", "split", "intro hb", "have hevenzero : 2 * (m * n) = 0", "trans b", "symm", "exact hp_right_right_right_right_right_right", "exact hb",
            "apply mul_ne_zero", "intro htwo", "apply succ_ne_zero", "exact htwo", "intro hproduct", "apply mul_ne_zero", "exact hpositive_left", "exact hp_left", "exact hproduct", "exact hevenzero",
            "split", "intro hc",
        )
        + _specialize("pythagorean_hypotenuse_nonzero", "m", "n")
        + (
            "apply pythagorean_hypotenuse_nonzero", "exact hpositive_left", "trans c", "symm", "exact hp_right_right_right_right_left", "exact hc",
            "rewrite hp_right_right_right_right_left", "rewrite hp_right_right_right_right_left",
            "rewrite hp_right_right_right_right_right_right", "rewrite hp_right_right_right_right_right_right", "rewrite hp_right_right_right_right_right_right",
        )
        + _specialize("pythagorean_primitive_euclidean_constructor", "m", "n", "a")
        + (
            "apply pythagorean_primitive_euclidean_constructor", "exact hp_right_right_right_right_right_left", "exact hp_right_right_left", "exact hp_right_right_right_left",
        ),
        "The checked Euclidean constructor, strengthened with real positivity, supplies exactly the positive primitive triple used in the classification.",
    )
    forward_branches: list[str] = []
    for branch, first, second in (("hp_right_right_right_right_right_left", "a", "b"), ("hp_right_right_right_right_right_right", "b", "a")):
        forward_branches.extend((f"have horiented : {_parameters(first, second, 'c', 'x', 'x1', tag='forward_orientation')}",))
        forward_branches.extend(_copy_common_parameters("hp"))
        forward_branches.append(f"exact {branch}")
        if first == "b":
            forward_branches.extend((*_specialize("pythagorean_positive_primitive_leg_swap", "b", "a", "c"), "apply pythagorean_positive_primitive_leg_swap"))
        forward_branches.extend((
            *_specialize("pythagorean_euclidean_parameters_positive_constructor", first, second, "c", "x", "x1"),
            "apply pythagorean_euclidean_parameters_positive_constructor", "exact horiented",
        ))
    add(
        "pythagorean_positive_primitive_from_parameters",
        f"forall a b c. ({euclidean_parametrization('a', 'b', 'c', tag='forward_either')}) -> "
        f"({_positive('a', 'b', 'c', tag='forward_triple')})",
        ("pythagorean_euclidean_parameters_positive_constructor", "pythagorean_positive_primitive_leg_swap"),
        _intros("a b c hparameters")
        + (
            "cases hparameters", "cases hparameters_witness",
            f"have hp : {_either_parameters('a', 'b', 'c', 'x', 'x1', tag='forward_copy')}", "exact hparameters_witness_witness",
        )
        + _unpack("hp", 5)
        + ("cases hp_right_right_right_right_right",)
        + tuple(forward_branches),
        "Either canonical Euclidean leg orientation constructs a positive primitive Pythagorean triple with every positivity obligation checked.",
    )
    positive = _positive("a", "b", "c", tag="classification_positive")
    parametrized = euclidean_parametrization("a", "b", "c", tag="classification_parameters")
    add(
        "pythagorean_positive_primitive_classification",
        f"forall a b c. ((({positive}) -> ({parametrized})) /\\ (({parametrized}) -> ({positive})))",
        ("pythagorean_positive_primitive_inverse", "pythagorean_positive_primitive_from_parameters"),
        _intros("a b c")
        + ("split",)
        + _specialize("pythagorean_positive_primitive_inverse", "a", "b", "c")
        + ("exact pythagorean_positive_primitive_inverse",)
        + _specialize("pythagorean_positive_primitive_from_parameters", "a", "b", "c")
        + ("exact pythagorean_positive_primitive_from_parameters",),
        "Complete constructive classification: a positive ordered triple is primitive Pythagorean if and only if it has positive strictly ordered coprime opposite-parity Euclid parameters in either leg orientation.",
    )
    return tuple(rows)


__all__ = [
    "positive_primitive_pythagorean",
    "euclidean_parameter_witness",
    "euclidean_parametrization",
    "make_pythagorean_inverse_candidate_theorems",
]
