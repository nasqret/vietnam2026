"""Static square-one classification candidate for the Wilson route.

The single theorem in this module classifies the bounded solutions of
``x * x == 1 (mod p)`` for a prime successor ``p = S n``.  Every surface
predicate expands to the unchanged first-order Peano language, and the
factory is deliberately absent from the public theorem registry pending a
content-addressed WMI discovery replay and a separate receipt-pinned
admission replay.
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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"wsq_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated square-one binder captures an argument")
    return names


def positive(value: str, *, tag: str) -> str:
    """Expand the witness-defined strict inequality ``0 < value``."""

    variable = _identifier(value, "positive value")
    (gap,) = _binders(tag, (variable,), ("positive_gap",))
    return f"exists {gap}. {gap} + 1 = {value}"


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict inequality ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("strict_gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def prime(value: str, *, tag: str) -> str:
    """Expand primality through the nonunit factor-pair definition."""

    variable = _identifier(value, "prime candidate")
    left, right = _binders(tag, (variable,), ("prime_left", "prime_right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def square_one_mod(modulus: str, value: str, *, tag: str) -> str:
    """Expand balanced congruence ``value * value == 1 (mod modulus)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((modulus, "modulus"), (value, "square root"))
    )
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("mod_left", "mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"{value} * {value} + {modulus} * {left_witness} = "
        f"1 + {modulus} * {right_witness}"
    )


def make_wilson_square_one_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated bounded square-one classification candidate."""

    prime_p = prime("p", tag="prime")
    positive_x = positive("x", tag="positive")
    bounded_x = strictly_below("x", "p", tag="bounded")
    square_mod_one = square_one_mod("p", "x", tag="square_one")

    return (
        spec(
            "prime_bounded_square_one_cases",
            f"forall p n x. p = S n -> ({prime_p}) -> "
            f"({positive_x}) -> ({bounded_x}) -> ({square_mod_one}) -> "
            "x = 1 \\/ x = n",
            (
                "ne_zero_of_one_le",
                "nonzero_is_succ",
                "mul_succ_left",
                "add_assoc",
                "add_comm",
                "add_left_cancel",
                "factor_difference",
                "euclid_prime_dvd_product",
                "le_succ_self",
                "lt_of_le_of_lt",
                "zero_or_succ",
                "divisor_le_nonzero",
                "lt_not_le",
                "succ_ne_zero",
                "le_antisymm",
                "succ_injective",
            ),
            (
                "intro p",
                "intro n",
                "intro x",
                "intro hpn",
                "intro hp",
                "intro hxpos",
                "intro hxlt",
                "intro hsquaremod",
                "cases hp",
                f"have hprime : {prime_p}",
                "split",
                "exact hp_left",
                "exact hp_right",
                "have hx0 : ~(x = 0)",
                "specialize ne_zero_of_one_le x",
                "intro hxzero",
                "apply ne_zero_of_one_le",
                "exact hxpos",
                "exact hxzero",
                "have hxpred : exists t. x = S t",
                "specialize nonzero_is_succ x",
                "apply nonzero_is_succ",
                "exact hx0",
                "cases hxpred",
                "have hsquare : x * x = 1 + x1 * S (S x1)",
                "rewrite hxpred_witness",
                "rewrite hxpred_witness",
                "specialize mul_succ_left x1",
                "specialize mul_succ_left (S x1)",
                "trans x1 * S x1 + S x1",
                "exact mul_succ_left",
                "trans S (x1 * S x1 + x1)",
                "apply PA4",
                "trans (x1 * S x1 + x1) + 1",
                "symm",
                "trans S ((x1 * S x1 + x1) + 0)",
                "apply PA4",
                "congr",
                "apply PA3",
                "trans 1 + (x1 * S x1 + x1)",
                "apply add_comm",
                "congr",
                "refl",
                "symm",
                "apply PA6",
                "cases hsquaremod",
                "cases hsquaremod_witness",
                "have hcancel : x1 * S (S x1) + p * x2 = p * x3",
                "specialize add_left_cancel 1",
                "specialize add_left_cancel (x1 * S (S x1) + p * x2)",
                "specialize add_left_cancel (p * x3)",
                "apply add_left_cancel",
                "trans (1 + x1 * S (S x1)) + p * x2",
                "symm",
                "apply add_assoc",
                "trans x * x + p * x2",
                "congr",
                "symm",
                "exact hsquare",
                "refl",
                "trans 1 + p * x3",
                "exact hsquaremod_witness_witness",
                "refl",
                "have hfactor : p * x3 = p * x2 + x1 * S (S x1)",
                "trans x1 * S (S x1) + p * x2",
                "symm",
                "exact hcancel",
                "apply add_comm",
                "have hproduct : exists w. x1 * S (S x1) = p * w",
                "specialize factor_difference p",
                "specialize factor_difference x3",
                "specialize factor_difference x2",
                "specialize factor_difference (x1 * S (S x1))",
                "apply factor_difference",
                "exact hfactor",
                "have hsplit : (exists u. x1 = p * u) \\/ exists v. S (S x1) = p * v",
                "specialize euclid_prime_dvd_product p",
                "specialize euclid_prime_dvd_product x1",
                "specialize euclid_prime_dvd_product (S (S x1))",
                "apply euclid_prime_dvd_product",
                "exact hprime",
                "exact hproduct",
                "cases hsplit",
                "have htx : exists k. k + x1 = x",
                "rewrite hxpred_witness",
                "specialize le_succ_self x1",
                "exact le_succ_self",
                "have htp : exists k. k + S x1 = p",
                "specialize lt_of_le_of_lt x1",
                "specialize lt_of_le_of_lt x",
                "specialize lt_of_le_of_lt p",
                "apply lt_of_le_of_lt",
                "exact htx",
                "exact hxlt",
                "have htcase : x1 = 0 \\/ exists t. x1 = S t",
                "specialize zero_or_succ x1",
                "exact zero_or_succ",
                "cases htcase",
                "left",
                "trans S x1",
                "exact hxpred_witness",
                "rewrite htcase_left",
                "refl",
                "cases htcase_right",
                "have ht0 : ~(x1 = 0)",
                "intro htzero",
                "rewrite htcase_right_witness at htzero",
                "apply PA1",
                "exact htzero",
                "have hpt : exists k. k + p = x1",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero x1",
                "apply divisor_le_nonzero",
                "exact ht0",
                "exact hsplit_left",
                "exfalso",
                "specialize lt_not_le x1",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact htp",
                "exact hpt",
                "right",
                "have hfactor0 : ~(S (S x1) = 0)",
                "specialize succ_ne_zero (S x1)",
                "exact succ_ne_zero",
                "have hpfactor : exists k. k + p = S (S x1)",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero (S (S x1))",
                "apply divisor_le_nonzero",
                "exact hfactor0",
                "exact hsplit_right",
                "have hfactorp : exists k. k + S (S x1) = p",
                "rewrite <- hxpred_witness",
                "exact hxlt",
                "have hpeq : p = S (S x1)",
                "specialize le_antisymm p",
                "specialize le_antisymm (S (S x1))",
                "apply le_antisymm",
                "exact hpfactor",
                "exact hfactorp",
                "have hpred_eq : S x1 = n",
                "specialize succ_injective (S x1)",
                "specialize succ_injective n",
                "apply succ_injective",
                "trans p",
                "symm",
                "exact hpeq",
                "exact hpn",
                "trans S x1",
                "exact hxpred_witness",
                "exact hpred_eq",
            ),
            "A bounded square root of one modulo a prime is one or the prime predecessor.",
        ),
    )


__all__ = [
    "make_wilson_square_one_candidate_theorems",
    "positive",
    "prime",
    "square_one_mod",
    "strictly_below",
]
