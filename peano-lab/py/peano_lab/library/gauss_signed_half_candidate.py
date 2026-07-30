"""Isolated signed-half representative candidates for Gauss's lemma.

The two contracts in this module are authoring candidates only.  They are not
imported by the public theorem registry and must remain isolated until an
independent WMI replay closes their certificates from the empty kernel
context.

Every displayed order and congruence relation expands immediately to the
unchanged first-order language of Peano arithmetic.  In particular, the
reflected representative uses ``r + m = p`` instead of subtraction, and the
predecessor of the odd modulus ``p = 2*h+1`` is written as ``2*h``.
"""

from __future__ import annotations

from typing import Any, Callable


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _identifier_or_zero(value: str, label: str) -> str:
    if value == "0":
        return value
    return _identifier(value, label)


def _binder(tag: str, stem: str, variables: tuple[str, ...]) -> str:
    safe_tag = _identifier(tag, "binder tag")
    safe_stem = _identifier(stem, "binder stem")
    name = f"gsh_{safe_stem}_{safe_tag}"
    if name in variables:
        raise ValueError("generated signed-half binder captures an argument")
    return name


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict order ``left < right``."""

    variables = (
        _identifier_or_zero(left, "lower term"),
        _identifier(right, "upper term"),
    )
    gap = _binder(tag, "lt_gap", variables)
    return f"exists {gap}. {gap} + S {left} = {right}"


def weakly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined weak order ``left <= right``."""

    variables = (
        _identifier(left, "lower term"),
        _identifier(right, "upper term"),
    )
    gap = _binder(tag, "le_gap", variables)
    return f"exists {gap}. {gap} + {left} = {right}"


def _balanced_mod(
    modulus: str,
    left: str,
    right: str,
    *,
    variables: tuple[str, ...],
    tag: str,
) -> str:
    """Expand balanced congruence for module-owned term fragments."""

    checked_variables = tuple(
        _identifier(variable, "congruence variable") for variable in variables
    )
    checked_modulus = _identifier(modulus, "modulus")
    if checked_modulus not in checked_variables:
        raise ValueError("the modulus must be owned by the surrounding contract")
    left_witness = _binder(tag, "mod_left", checked_variables)
    right_witness = _binder(tag, "mod_right", checked_variables)
    if left_witness == right_witness:
        raise AssertionError("balanced congruence witnesses must be distinct")
    return (
        f"exists {left_witness} {right_witness}. "
        f"({left}) + {modulus} * {left_witness} = "
        f"({right}) + {modulus} * {right_witness}"
    )


def make_gauss_signed_half_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered first signed-half Gauss rung."""

    reflection_positive = strictly_below("0", "m", tag="reflection_positive")
    reflection_bounded = weakly_below("m", "h", tag="reflection_bounded")
    reflection_result = (
        f"exists m. ({reflection_positive}) /\\ "
        f"(({reflection_bounded}) /\\ r + m = p)"
    )

    product_variables = ("p", "h", "a", "x", "q", "r", "m")
    product_positive = strictly_below("0", "m", tag="product_positive")
    product_bounded = weakly_below("m", "h", tag="product_bounded")
    product_lower_mod = _balanced_mod(
        "p",
        "a * x",
        "m",
        variables=product_variables,
        tag="product_lower",
    )
    product_upper_mod = _balanced_mod(
        "p",
        "a * x",
        "(2 * h) * m",
        variables=product_variables,
        tag="product_upper",
    )
    product_result = (
        f"exists m. ({product_positive}) /\\ "
        f"(({product_bounded}) /\\ "
        f"(({product_lower_mod}) \\/ ({product_upper_mod})))"
    )

    remainder_bound = strictly_below("r", "p", tag="product_remainder")
    canonical_remainder_mod = _balanced_mod(
        "p",
        "a * x",
        "r",
        variables=("p", "h", "a", "x", "q", "r"),
        tag="canonical_remainder",
    )
    reflected_remainder_mod = _balanced_mod(
        "p",
        "r",
        "(2 * h) * x1",
        variables=("p", "h", "r", "x1"),
        tag="reflected_remainder",
    )
    reflected_product_mod = _balanced_mod(
        "p",
        "a * x",
        "(2 * h) * x1",
        variables=("p", "h", "a", "x", "r", "x1"),
        tag="reflected_product",
    )

    return (
        spec(
            "odd_upper_remainder_reflection",
            "forall p h r. p = 2 * h + 1 -> "
            f"({strictly_below('r', 'p', tag='reflection_remainder')}) -> "
            f"({strictly_below('h', 'r', tag='reflection_upper')}) -> "
            f"({reflection_result})",
            (
                "add_assoc",
                "add_comm",
                "mul_succ_left",
                "mul_zero_left",
                "zero_add",
                "add_succ_left",
                "add_right_cancel",
            ),
            (
                "intro p",
                "intro h",
                "intro r",
                "intro hp",
                "intro hrp",
                "intro hhr",
                "cases hhr",
                "cases hrp",
                "have hrm : r + S x1 = p",
                "trans S (r + x1)",
                "apply PA4",
                "trans S (x1 + r)",
                "congr",
                "apply add_comm",
                "trans x1 + S r",
                "symm",
                "apply PA4",
                "exact hrp_witness",
                "have hsum : (x + S x1) + S h = h + S h",
                "trans (x + S h) + S x1",
                "trans x + (S x1 + S h)",
                "apply add_assoc",
                "trans x + (S h + S x1)",
                "congr",
                "refl",
                "apply add_comm",
                "symm",
                "apply add_assoc",
                "trans r + S x1",
                "congr",
                "exact hhr_witness",
                "refl",
                "trans p",
                "exact hrm",
                "rewrite hp",
                "simp [mul_succ_left, mul_zero_left, zero_add, "
                "add_succ_left, add_assoc]",
                "have hmle : exists d. d + S x1 = h",
                "exists x",
                "specialize add_right_cancel (x + S x1)",
                "specialize add_right_cancel h",
                "specialize add_right_cancel (S h)",
                "apply add_right_cancel",
                "exact hsum",
                "exists (S x1)",
                "split",
                "exists x1",
                "simp",
                "split",
                "exact hmle",
                "exact hrm",
            ),
            "A residue strictly above h and below 2*h+1 has a positive reflected magnitude at most h.",
        ),
        spec(
            "gauss_pointwise_signed_half_representative",
            "forall p h a x q r. p = 2 * h + 1 -> "
            "a * x = q * p + r -> "
            f"({remainder_bound}) -> ~(r = 0) -> ({product_result})",
            (
                "add_assoc",
                "add_comm",
                "mul_succ_left",
                "mul_one",
                "le_or_lt",
                "one_le_of_ne_zero",
                "remainder_decomposition_to_mod_eq",
                "odd_upper_remainder_reflection",
                "mod_eq_trans",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro x",
                "intro q",
                "intro r",
                "intro hp",
                "intro hdecomp",
                "intro hrp",
                "intro hr0",
                f"have hcanonical : {canonical_remainder_mod}",
                "specialize remainder_decomposition_to_mod_eq p",
                "specialize remainder_decomposition_to_mod_eq (a * x)",
                "specialize remainder_decomposition_to_mod_eq q",
                "specialize remainder_decomposition_to_mod_eq r",
                "apply remainder_decomposition_to_mod_eq",
                "exact hdecomp",
                "have hsplit : (exists d. d + r = h) \\/ (exists d. d + S h = r)",
                "specialize le_or_lt r",
                "specialize le_or_lt h",
                "exact le_or_lt",
                "cases hsplit",
                "exists r",
                "split",
                "specialize one_le_of_ne_zero r",
                "apply one_le_of_ne_zero",
                "exact hr0",
                "split",
                "exact hsplit_left",
                "left",
                "exact hcanonical",
                f"have hreflection : {reflection_result}",
                "specialize odd_upper_remainder_reflection p",
                "specialize odd_upper_remainder_reflection h",
                "specialize odd_upper_remainder_reflection r",
                "apply odd_upper_remainder_reflection",
                "exact hp",
                "exact hrp",
                "exact hsplit_right",
                "cases hreflection",
                "cases hreflection_witness",
                "cases hreflection_witness_right",
                f"have hreflected_remainder : {reflected_remainder_mod}",
                "exists x1",
                "exists 1",
                "trans (r + x1) + (2 * h) * x1",
                "rewrite hp",
                "trans r + (x1 + (2 * h) * x1)",
                "simp",
                "specialize mul_succ_left (2 * h)",
                "specialize mul_succ_left x1",
                "rewrite mul_succ_left",
                "congr",
                "refl",
                "apply add_comm",
                "symm",
                "apply add_assoc",
                "rewrite hreflection_witness_right_right",
                "specialize mul_one p",
                "rewrite mul_one",
                "apply add_comm",
                f"have hreflected_product : {reflected_product_mod}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (a * x)",
                "specialize mod_eq_trans r",
                "specialize mod_eq_trans ((2 * h) * x1)",
                "apply mod_eq_trans",
                "exact hcanonical",
                "exact hreflected_remainder",
                "exists x1",
                "split",
                "exact hreflection_witness_left",
                "split",
                "exact hreflection_witness_right_left",
                "right",
                "exact hreflected_product",
            ),
            "A nonzero canonical product remainder has a positive half-range magnitude, with its sign recorded by a lower/reflected congruence disjunction.",
        ),
    )


__all__ = [
    "make_gauss_signed_half_candidate_theorems",
    "strictly_below",
    "weakly_below",
]
