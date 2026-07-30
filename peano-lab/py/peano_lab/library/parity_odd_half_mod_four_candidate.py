"""Parity of the half in an odd modulo-four decomposition.

For ``p = 2*h+1``, the cases ``p = 4*a+1`` and ``p = 4*a+3`` identify the
half exactly as ``2*a`` and ``2*a+1``.  The final two candidates package the
existential versions as constructive biconditionals.  All predicates are
expanded equations in unchanged first-order PA; the candidates are isolated
and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable


def _even(term: str, *, tag: str) -> str:
    return f"exists poh_even_{tag}. {term} = 2 * poh_even_{tag}"


def _odd(term: str, *, tag: str) -> str:
    return f"exists poh_odd_{tag}. {term} = 2 * poh_odd_{tag} + 1"


def _mod_four_one(term: str, *, tag: str) -> str:
    return f"exists poh_one_{tag}. {term} = 4 * poh_one_{tag} + 1"


def _mod_four_three(term: str, *, tag: str) -> str:
    return f"exists poh_three_{tag}. {term} = 4 * poh_three_{tag} + 3"


def make_parity_odd_half_mod_four_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build exact and existential odd-half/modulo-four bridges."""

    even_h = _even("h", tag="half")
    odd_h = _odd("h", tag="half")
    one_p = _mod_four_one("p", tag="modulus")
    three_p = _mod_four_three("p", tag="modulus")
    even_iff_one = f"((({even_h}) -> ({one_p})) /\\ (({one_p}) -> ({even_h})))"
    odd_iff_three = (
        f"((({odd_h}) -> ({three_p})) /\\ (({three_p}) -> ({odd_h})))"
    )

    return (
        spec(
            "odd_half_of_mod4_one_exact",
            "forall p h a. p = 2 * h + 1 -> p = 4 * a + 1 -> h = 2 * a",
            ("four_mul_eq_double_double", "odd_half_unique"),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro hp",
                "intro hfour",
                "have hcanonical : p = 2 * (2 * a) + 1",
                "trans 4 * a + 1",
                "exact hfour",
                "congr",
                "apply four_mul_eq_double_double",
                "refl",
                "specialize odd_half_unique p",
                "specialize odd_half_unique h",
                "specialize odd_half_unique (2 * a)",
                "apply odd_half_unique",
                "exact hp",
                "exact hcanonical",
            ),
            "The half of a fixed odd number congruent to one modulo four is exactly even.",
        ),
        spec(
            "odd_half_of_mod4_three_exact",
            "forall p h a. p = 2 * h + 1 -> p = 4 * a + 3 -> h = 2 * a + 1",
            ("mul_add", "four_mul_eq_double_double", "odd_half_unique"),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro hp",
                "intro hfour",
                "have hcanonical : p = 2 * (2 * a + 1) + 1",
                "trans 4 * a + 3",
                "exact hfour",
                "simp [mul_add]",
                "congr",
                "congr",
                "congr",
                "apply four_mul_eq_double_double",
                "specialize odd_half_unique p",
                "specialize odd_half_unique h",
                "specialize odd_half_unique (2 * a + 1)",
                "apply odd_half_unique",
                "exact hp",
                "exact hcanonical",
            ),
            "The half of a fixed odd number congruent to three modulo four is exactly odd.",
        ),
        spec(
            "odd_half_even_iff_mod4_one",
            f"forall p h. p = 2 * h + 1 -> ({even_iff_one})",
            ("four_mul_eq_double_double", "odd_half_of_mod4_one_exact"),
            (
                "intro p",
                "intro h",
                "intro hp",
                "split",
                "intro heven",
                "cases heven",
                "exists x",
                "rewrite hp",
                "rewrite heven_witness",
                "congr",
                "symm",
                "apply four_mul_eq_double_double",
                "refl",
                "intro hone",
                "cases hone",
                "exists x",
                "specialize odd_half_of_mod4_one_exact p",
                "specialize odd_half_of_mod4_one_exact h",
                "specialize odd_half_of_mod4_one_exact x",
                "apply odd_half_of_mod4_one_exact",
                "exact hp",
                "exact hone_witness",
            ),
            "For a fixed odd decomposition, a modulo-four-one modulus is equivalent to an even half.",
        ),
        spec(
            "odd_half_odd_iff_mod4_three",
            f"forall p h. p = 2 * h + 1 -> ({odd_iff_three})",
            (
                "mul_add",
                "four_mul_eq_double_double",
                "odd_half_of_mod4_three_exact",
            ),
            (
                "intro p",
                "intro h",
                "intro hp",
                "split",
                "intro hodd",
                "cases hodd",
                "exists x",
                "rewrite hp",
                "rewrite hodd_witness",
                "simp [mul_add]",
                "congr",
                "congr",
                "congr",
                "symm",
                "apply four_mul_eq_double_double",
                "intro hthree",
                "cases hthree",
                "exists x",
                "specialize odd_half_of_mod4_three_exact p",
                "specialize odd_half_of_mod4_three_exact h",
                "specialize odd_half_of_mod4_three_exact x",
                "apply odd_half_of_mod4_three_exact",
                "exact hp",
                "exact hthree_witness",
            ),
            "For a fixed odd decomposition, a modulo-four-three modulus is equivalent to an odd half.",
        ),
    )


__all__ = ["make_parity_odd_half_mod_four_candidate_theorems"]
