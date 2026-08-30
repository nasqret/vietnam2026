r"""Canonical-remainder characterization of balanced congruence.

The kernel language has neither a remainder function nor a primitive
congruence predicate.  This isolated HA candidate expands both interfaces to
the unchanged ``0, S, +, *, =`` language and proves the bridge

``Rem(m, a, r) /\ Rem(m, b, s) -> (a == b (mod m) <-> r = s)``.

No separate ``m != 0`` premise is needed: each ``Rem`` hypothesis already
contains a witness for its strict remainder bound.  The candidate is
dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_remainder_candidate import canonical_remainder


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'" for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def balanced_mod_eq(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand balanced congruence to an existential equality."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (left, "left value"),
            (right, "right value"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    left_witness = f"hcc_mod_left_{safe_tag}"
    right_witness = f"hcc_mod_right_{safe_tag}"
    if (
        left_witness == right_witness
        or {left_witness, right_witness} & set(variables)
    ):
        raise ValueError("generated balanced-congruence binder captures an argument")
    return (
        f"exists {left_witness} {right_witness}. "
        f"{left} + {modulus} * {left_witness} = "
        f"{right} + {modulus} * {right_witness}"
    )


def make_ha_canonical_congruence_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated canonical-remainder congruence bridge."""

    remainder_a = canonical_remainder("m", "a", "r", tag="left")
    remainder_b = canonical_remainder("m", "b", "s", tag="right")
    source_mod = balanced_mod_eq("m", "a", "b", tag="source")
    result_mod = balanced_mod_eq("m", "a", "b", tag="result")

    a_mod_r = balanced_mod_eq("m", "a", "r", tag="a_r")
    b_mod_s = balanced_mod_eq("m", "b", "s", tag="b_s")
    r_mod_a = balanced_mod_eq("m", "r", "a", tag="r_a")
    r_mod_b = balanced_mod_eq("m", "r", "b", tag="r_b")
    r_mod_s = balanced_mod_eq("m", "r", "s", tag="r_s")
    s_mod_b = balanced_mod_eq("m", "s", "b", tag="s_b")

    return (
        spec(
            "canonical_remainders_characterize_mod_eq",
            f"forall m a b r s. ({remainder_a}) -> ({remainder_b}) -> "
            f"((({source_mod}) -> r = s) /\\ (r = s -> ({result_mod})))",
            (
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
                "mod_eq_symm",
                "mod_eq_trans",
                "mod_eq_bounded_unique",
            ),
            (
                "intro m",
                "intro a",
                "intro b",
                "intro r",
                "intro s",
                "intro hr",
                "intro hs",
                "cases hr",
                "cases hs",
                "cases hr_left",
                "cases hs_left",
                "have hadecomp : a = x * m + r",
                "trans m * x + r",
                "exact hr_left_witness",
                "congr",
                "apply mul_comm",
                "refl",
                "have hbdecomp : b = x1 * m + s",
                "trans m * x1 + s",
                "exact hs_left_witness",
                "congr",
                "apply mul_comm",
                "refl",
                f"have har : {a_mod_r}",
                "specialize remainder_decomposition_to_mod_eq m",
                "specialize remainder_decomposition_to_mod_eq a",
                "specialize remainder_decomposition_to_mod_eq x",
                "specialize remainder_decomposition_to_mod_eq r",
                "apply remainder_decomposition_to_mod_eq",
                "exact hadecomp",
                f"have hbs : {b_mod_s}",
                "specialize remainder_decomposition_to_mod_eq m",
                "specialize remainder_decomposition_to_mod_eq b",
                "specialize remainder_decomposition_to_mod_eq x1",
                "specialize remainder_decomposition_to_mod_eq s",
                "apply remainder_decomposition_to_mod_eq",
                "exact hbdecomp",
                "split",
                "intro hab",
                f"have hra : {r_mod_a}",
                "specialize mod_eq_symm m",
                "specialize mod_eq_symm a",
                "specialize mod_eq_symm r",
                "apply mod_eq_symm",
                "exact har",
                f"have hrb : {r_mod_b}",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans r",
                "specialize mod_eq_trans a",
                "specialize mod_eq_trans b",
                "apply mod_eq_trans",
                "exact hra",
                "exact hab",
                f"have hrs : {r_mod_s}",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans r",
                "specialize mod_eq_trans b",
                "specialize mod_eq_trans s",
                "apply mod_eq_trans",
                "exact hrb",
                "exact hbs",
                "specialize mod_eq_bounded_unique m",
                "specialize mod_eq_bounded_unique r",
                "specialize mod_eq_bounded_unique s",
                "apply mod_eq_bounded_unique",
                "exact hr_right",
                "exact hs_right",
                "exact hrs",
                "intro hrs_equal",
                "rewrite hrs_equal at har",
                f"have hsb : {s_mod_b}",
                "specialize mod_eq_symm m",
                "specialize mod_eq_symm b",
                "specialize mod_eq_symm s",
                "apply mod_eq_symm",
                "exact hbs",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans a",
                "specialize mod_eq_trans s",
                "specialize mod_eq_trans b",
                "apply mod_eq_trans",
                "exact har",
                "exact hsb",
            ),
            "Two canonical remainders are equal exactly when their dividends "
            "are congruent modulo the shared modulus.",
        ),
    )


__all__ = [
    "balanced_mod_eq",
    "make_ha_canonical_congruence_candidate_theorems",
]
