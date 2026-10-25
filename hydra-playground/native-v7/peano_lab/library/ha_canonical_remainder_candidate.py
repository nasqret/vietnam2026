"""Canonical quotient/remainder interface over the checked division API.

The kernel language has no remainder function.  This isolated candidate layer
therefore exposes the graph of the canonical remainder as a relation:

``Rem(m, n, r) := (exists q. n = m * q + r) /\\ r < m``.

Both the quotient witness and strict order are expanded below to unchanged
first-order Heyting arithmetic.  The candidates only reorganize the already
public ``division_remainder_exists`` and ``division_remainder_unique``
theorems.  They remain dependency-curried, unregistered, and unadmitted.
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


def canonical_remainder(
    modulus: str,
    dividend: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    """Expand ``Rem(modulus, dividend, remainder)`` to the base language."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (dividend, "dividend"),
            (remainder, "remainder"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    quotient = f"hcr_quotient_{safe_tag}"
    gap = f"hcr_gap_{safe_tag}"
    if len(set((quotient, gap))) != 2 or {quotient, gap} & set(variables):
        raise ValueError("generated canonical-remainder binder captures an argument")
    return (
        f"((exists {quotient}. {dividend} = {modulus} * {quotient} + "
        f"{remainder}) /\\ exists {gap}. {gap} + S {remainder} = {modulus})"
    )


def make_ha_canonical_remainder_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build totality, functionality, and unique-existence candidates."""

    remainder_r = canonical_remainder("m", "n", "r", tag="result")
    remainder_s = canonical_remainder("m", "n", "s", tag="comparison")
    zero_remainder = canonical_remainder(
        "m", "n", "r", tag="zero_impossible"
    )
    unique_remainder_r = canonical_remainder(
        "m", "n", "r", tag="unique_result"
    )
    unique_remainder_s = canonical_remainder(
        "m", "n", "s", tag="unique_comparison"
    )

    return (
        spec(
            "canonical_remainder_exists",
            f"forall m n. ~(m = 0) -> exists r. ({remainder_r})",
            ("division_remainder_exists",),
            (
                "intro m",
                "intro n",
                "intro hm",
                "have hdivision : exists q r. n = m * q + r /\\ "
                "exists gap. gap + S r = m",
                "specialize division_remainder_exists m",
                "specialize division_remainder_exists n",
                "apply division_remainder_exists",
                "exact hm",
                "cases hdivision",
                "cases hdivision_witness",
                "cases hdivision_witness_witness",
                "exists x1",
                "split",
                "exists x",
                "exact hdivision_witness_witness_left",
                "exact hdivision_witness_witness_right",
            ),
            "Every dividend has a canonical remainder for each nonzero modulus.",
        ),
        spec(
            "canonical_remainder_functional",
            f"forall m n r s. ({remainder_r}) -> ({remainder_s}) -> r = s",
            ("division_remainder_unique",),
            (
                "intro m",
                "intro n",
                "intro r",
                "intro s",
                "intro hr",
                "intro hs",
                "cases hr",
                "cases hs",
                "cases hr_left",
                "cases hs_left",
                "have hunique : x = x1 /\\ r = s",
                "specialize division_remainder_unique m",
                "specialize division_remainder_unique n",
                "specialize division_remainder_unique x",
                "specialize division_remainder_unique r",
                "specialize division_remainder_unique x1",
                "specialize division_remainder_unique s",
                "apply division_remainder_unique",
                "exact hr_left_witness",
                "exact hr_right",
                "exact hs_left_witness",
                "exact hs_right",
                "cases hunique",
                "exact hunique_right",
            ),
            "Canonical remainders for a fixed modulus are functional whenever they exist.",
        ),
        spec(
            "canonical_remainder_zero_impossible",
            f"forall m n r. m = 0 -> ~({zero_remainder})",
            ("succ_ne_zero",),
            (
                "intro m",
                "intro n",
                "intro r",
                "intro hm",
                "intro hrem",
                "cases hrem",
                "rewrite hm at hrem_right",
                "cases hrem_right",
                "have hsucc : S (x + r) = 0",
                "trans x + S r",
                "symm",
                "apply PA4",
                "exact hrem_right_witness",
                "specialize succ_ne_zero (x + r)",
                "apply succ_ne_zero",
                "exact hsucc",
            ),
            "The canonical-remainder relation has no inhabitant at modulus zero.",
        ),
        spec(
            "canonical_remainder_exists_unique",
            f"forall m n. ~(m = 0) -> exists r. (({unique_remainder_r}) /\\ "
            f"forall s. ({unique_remainder_s}) -> s = r)",
            (
                "canonical_remainder_exists",
                "canonical_remainder_functional",
            ),
            (
                "intro m",
                "intro n",
                "intro hm",
                f"have hexists : exists r. ({unique_remainder_r})",
                "specialize canonical_remainder_exists m",
                "specialize canonical_remainder_exists n",
                "apply canonical_remainder_exists",
                "exact hm",
                "cases hexists",
                "exists x",
                "split",
                "exact hexists_witness",
                "intro s",
                "intro hs",
                "specialize canonical_remainder_functional m",
                "specialize canonical_remainder_functional n",
                "specialize canonical_remainder_functional s",
                "specialize canonical_remainder_functional x",
                "apply canonical_remainder_functional",
                "exact hs",
                "exact hexists_witness",
            ),
            "For every nonzero modulus, the canonical remainder exists uniquely; "
            "the comparison remainder is proved equal to the chosen remainder.",
        ),
    )


__all__ = [
    "canonical_remainder",
    "make_ha_canonical_remainder_candidate_theorems",
]
