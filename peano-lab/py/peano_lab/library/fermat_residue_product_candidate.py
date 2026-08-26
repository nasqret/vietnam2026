"""Static, isolated Fermat range-product candidates for QR-2.

This module is an unverified authoring candidate.  It is deliberately absent
from the public theorem registry until a separate content-addressed replay
checks every script, closes every certificate in the empty kernel context,
and records stable resource receipts.

All readable relations below expand immediately to the unchanged first-order
Peano language.  ``Range``, ``Product``, ``BetaAt``, ``Prime``, ``Coprime``,
and strict order are not parser syntax or kernel constants.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation, range_relation


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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"frp_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Fermat-product binder captures an argument")
    return names


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict order ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def coprime(left: str, right: str, *, tag: str) -> str:
    """Expand the common-divisor definition of coprimality."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "left operand"), (right, "right operand"))
    )
    divisor, left_factor, right_factor = _binders(
        tag,
        variables,
        ("divisor", "left_factor", "right_factor"),
    )
    return (
        f"forall {divisor}. (exists {left_factor}. "
        f"{left} = {divisor} * {left_factor}) -> "
        f"(exists {right_factor}. {right} = {divisor} * {right_factor}) -> "
        f"{divisor} = 1"
    )


def prime(value: str, *, tag: str) -> str:
    """Expand primality through nontrivial factor pairs."""

    variable = _identifier(value, "prime candidate")
    left, right = _binders(tag, (variable,), ("prime_left", "prime_right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def range_one(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand ``Range(code,scale,1,length)`` without accepting term input."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "range code"),
            (scale, "range scale"),
            (length, "range length"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    (start_marker,) = _binders(safe_tag, variables, ("range_start",))
    expanded = range_relation(
        code,
        scale,
        start_marker,
        length,
        tag=f"frp_range_{safe_tag}",
    )
    if expanded.count(start_marker) != 2:
        raise AssertionError("unexpected consecutive-Range expansion")
    return expanded.replace(start_marker, "1")


def pointwise_coprime(
    code: str,
    scale: str,
    length: str,
    modulus: str,
    *,
    tag: str,
) -> str:
    """Expand coprimality of every decoded factor in a bounded prefix."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "factor code"),
            (scale, "factor scale"),
            (length, "factor length"),
            (modulus, "modulus"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    index, factor = _binders(safe_tag, variables, ("index", "factor"))
    bounded = strictly_below(
        index,
        length,
        tag=f"{safe_tag}_bound",
    )
    decoded = beta_at(
        code,
        scale,
        index,
        factor,
        tag=f"frp_{safe_tag}_decoded",
    )
    factor_coprime = coprime(
        factor,
        modulus,
        tag=f"{safe_tag}_coprime",
    )
    return (
        f"forall {index} {factor}. ({bounded}) -> ({decoded}) -> "
        f"({factor_coprime})"
    )


def make_fermat_residue_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the static, dependency-ordered three-rung QR-2 candidate."""

    range_entry = range_one("b", "c", "l", tag="entry")
    entry_bound = strictly_below("i", "l", tag="entry_bound")
    decoded_entry = beta_at("b", "c", "i", "x", tag="frp_entry")

    pointwise = pointwise_coprime("b", "c", "l", "m", tag="pointwise")
    product = product_relation("b", "c", "l", "z", tag="pointwise_product")
    prefix_pointwise = pointwise_coprime(
        "b",
        "c",
        "l",
        "m",
        tag="pointwise_prefix",
    )
    final_factor = beta_at("b", "c", "l", "p", tag="frp_final_factor")
    prefix_product = product_relation(
        "b",
        "c",
        "l",
        "r",
        tag="pointwise_prefix_product",
    )
    product_decomposition = (
        f"exists p r. ({final_factor}) /\\ "
        f"(({prefix_product}) /\\ z = r * p)"
    )

    prime_p = prime("p", tag="prime_p")
    prime_range = range_one("b", "c", "n", tag="prime_range")
    prime_product = product_relation(
        "b",
        "c",
        "n",
        "F",
        tag="prime_product",
    )
    prime_pointwise = pointwise_coprime(
        "b",
        "c",
        "n",
        "p",
        tag="prime_pointwise",
    )
    prime_factor_coprime = coprime("p", "x", tag="prime_factor")

    return (
        spec(
            "beta_range_one_entry_eq_succ",
            f"forall b c l i x. ({range_entry}) -> ({entry_bound}) -> "
            f"({decoded_entry}) -> x = S i",
            ("beta_range_entry_eq", "add_succ_left", "zero_add"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro x",
                "intro hrange",
                "intro hi",
                "intro hx",
                "have hraw : x = 1 + i",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq 1",
                "specialize beta_range_entry_eq l",
                "specialize beta_range_entry_eq i",
                "specialize beta_range_entry_eq x",
                "apply beta_range_entry_eq",
                "exact hrange",
                "exact hi",
                "exact hx",
                "have hone : 1 + i = S i",
                "trans S (0 + i)",
                "specialize add_succ_left 0",
                "specialize add_succ_left i",
                "exact add_succ_left",
                "congr",
                "specialize zero_add i",
                "exact zero_add",
                "trans 1 + i",
                "exact hraw",
                "exact hone",
            ),
            "A decoded entry of the range 1,...,l is the successor of its index.",
        ),
        spec(
            "beta_product_pointwise_coprime",
            f"forall m b c l z. ({pointwise}) -> ({product}) -> "
            f"({coprime('z', 'm', tag='pointwise_result')})",
            (
                "beta_product_zero",
                "beta_product_succ_decompose",
                "le_succ",
                "le_refl",
                "coprime_one_left",
                "coprime_mul_left",
            ),
            (
                "intro m",
                "intro b",
                "intro c",
                "induction l",
                "intro z",
                "intro hpw",
                "intro hproduct",
                "have hz : z = 1",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero z",
                "apply beta_product_zero",
                "exact hproduct",
                "rewrite hz",
                "specialize coprime_one_left m",
                "exact coprime_one_left",
                "intro z",
                "intro hpw",
                "intro hproduct",
                f"have hdecomp : {product_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose z",
                "apply beta_product_succ_decompose",
                "exact hproduct",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "cases hdecomp_witness_witness_right",
                f"have hpw_prefix : {prefix_pointwise}",
                "intro i",
                "intro x2",
                "intro hi",
                "intro hx2",
                "specialize hpw i",
                "specialize hpw x2",
                "apply hpw",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact hx2",
                f"have hprefix : {coprime('x1', 'm', tag='prefix_result')}",
                "specialize IH x1",
                "apply IH",
                "exact hpw_prefix",
                "exact hdecomp_witness_witness_right_left",
                f"have hfactor : {coprime('x', 'm', tag='last_factor')}",
                "specialize hpw l",
                "specialize hpw x",
                "apply hpw",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hdecomp_witness_witness_left",
                "rewrite hdecomp_witness_witness_right_right",
                "specialize coprime_mul_left x1",
                "specialize coprime_mul_left x",
                "specialize coprime_mul_left m",
                "apply coprime_mul_left",
                "exact hprefix",
                "exact hfactor",
            ),
            "A finite product of factors pointwise coprime to m is coprime to m.",
        ),
        spec(
            "prime_range_product_coprime",
            f"forall p n b c F. p = S n -> ({prime_p}) -> "
            f"({prime_range}) -> ({prime_product}) -> "
            f"({coprime('F', 'p', tag='prime_product_result')})",
            (
                "beta_range_one_entry_eq_succ",
                "beta_product_pointwise_coprime",
                "succ_ne_zero",
                "succ_le_succ",
                "divisor_le_nonzero",
                "lt_not_le",
                "prime_not_divides_coprime",
                "coprime_symm",
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro F",
                "intro hpn",
                "intro hp",
                "intro hrange",
                "intro hproduct",
                f"have hpointwise : {prime_pointwise}",
                "intro i",
                "intro x",
                "intro hi",
                "intro hx",
                "have hvalue : x = S i",
                "specialize beta_range_one_entry_eq_succ b",
                "specialize beta_range_one_entry_eq_succ c",
                "specialize beta_range_one_entry_eq_succ n",
                "specialize beta_range_one_entry_eq_succ i",
                "specialize beta_range_one_entry_eq_succ x",
                "apply beta_range_one_entry_eq_succ",
                "exact hrange",
                "exact hi",
                "exact hx",
                "have hx0 : ~(x = 0)",
                "intro hxzero",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "trans x",
                "symm",
                "exact hvalue",
                "exact hxzero",
                "have hxltp : exists h. h + S x = p",
                "rewrite hvalue",
                "rewrite hpn",
                "specialize succ_le_succ (S i)",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hi",
                "have hnotdiv : ~(exists k. x = p * k)",
                "intro hdiv",
                "have hle : exists k. k + p = x",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero x",
                "apply divisor_le_nonzero",
                "exact hx0",
                "exact hdiv",
                "specialize lt_not_le x",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact hxltp",
                "exact hle",
                f"have hpx : {prime_factor_coprime}",
                "specialize prime_not_divides_coprime p",
                "specialize prime_not_divides_coprime x",
                "apply prime_not_divides_coprime",
                "exact hp",
                "exact hnotdiv",
                "specialize coprime_symm p",
                "specialize coprime_symm x",
                "apply coprime_symm",
                "exact hpx",
                "specialize beta_product_pointwise_coprime p",
                "specialize beta_product_pointwise_coprime b",
                "specialize beta_product_pointwise_coprime c",
                "specialize beta_product_pointwise_coprime n",
                "specialize beta_product_pointwise_coprime F",
                "apply beta_product_pointwise_coprime",
                "exact hpointwise",
                "exact hproduct",
            ),
            "The product 1*...*(p-1) is coprime to a prime p.",
        ),
    )


__all__ = [
    "coprime",
    "make_fermat_residue_product_candidate_theorems",
    "pointwise_coprime",
    "prime",
    "range_one",
    "strictly_below",
]
