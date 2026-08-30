"""Zero-inclusive constructive binary generalized CRT.

The M5a construction factors nonzero moduli through a relational gcd.  This
isolated boundary layer removes those nonzero assumptions without sending a
zero modulus through division.  It proves the two directed zero cases with
public relational-gcd uniqueness, dispatches the three constructive equality
branches, and combines total sufficiency with the existing necessity theorem.

All authoring surfaces expand hygienically to first-order Heyting arithmetic
over ``0, S, +, *, =``.  Nothing here is registered or admitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_gcd_candidate import is_gcd
from .ha_canonical_gcd_edges_candidate import edge_is_gcd
from .ha_generalized_crt_congruence_candidate import balanced_mod_eq, crt_solution


def make_ha_generalized_crt_zero_boundary_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the four-row all-modulus generalized-CRT boundary ladder."""

    left_variables = ("g", "n", "a", "b")
    left_gcd = edge_is_gcd("g", "0", "n", tag="zero_left_gcd")
    left_gcd_swapped = edge_is_gcd(
        "g", "n", "0", tag="zero_left_gcd_swapped"
    )
    left_gcd_base = edge_is_gcd("n", "n", "0", tag="zero_left_gcd_base")
    left_compatibility = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="zero_left_compatibility",
        variables=left_variables,
    )
    left_solution = crt_solution(
        "x",
        "0",
        "n",
        "a",
        "b",
        tag="zero_left_solution",
        variables=(*left_variables, "x"),
    )

    right_variables = ("g", "m", "a", "b")
    right_gcd = edge_is_gcd("g", "m", "0", tag="zero_right_gcd")
    right_gcd_base = edge_is_gcd("m", "m", "0", tag="zero_right_gcd_base")
    right_compatibility = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="zero_right_compatibility",
        variables=right_variables,
    )
    right_solution = crt_solution(
        "x",
        "m",
        "0",
        "a",
        "b",
        tag="zero_right_solution",
        variables=(*right_variables, "x"),
    )

    total_variables = ("g", "m", "n", "a", "b")
    total_gcd = is_gcd("g", "m", "n", tag="total_sufficiency_gcd")
    total_compatibility = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="total_sufficiency_compatibility",
        variables=total_variables,
    )
    total_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="total_sufficiency_solution",
        variables=(*total_variables, "x"),
    )

    iff_gcd = is_gcd("g", "m", "n", tag="total_iff_gcd")
    iff_forward_compatibility = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="total_iff_forward_compatibility",
        variables=total_variables,
    )
    iff_reverse_compatibility = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="total_iff_reverse_compatibility",
        variables=total_variables,
    )
    iff_forward_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="total_iff_forward_solution",
        variables=(*total_variables, "x"),
    )
    iff_reverse_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="total_iff_reverse_solution",
        variables=(*total_variables, "x"),
    )

    return (
        spec(
            "generalized_binary_crt_sufficient_zero_left",
            f"forall g n a b. ({left_gcd}) -> ({left_compatibility}) -> "
            f"exists x. ({left_solution})",
            (
                "is_gcd_symm",
                "is_gcd_zero_right",
                "is_gcd_unique",
                "mod_eq_refl",
            ),
            (
                "intro g",
                "intro n",
                "intro a",
                "intro b",
                "intro hg",
                "intro hab",
                f"have hsym : {left_gcd_swapped}",
                "specialize is_gcd_symm g",
                "specialize is_gcd_symm 0",
                "specialize is_gcd_symm n",
                "apply is_gcd_symm",
                "exact hg",
                f"have hn : {left_gcd_base}",
                "specialize is_gcd_zero_right n",
                "exact is_gcd_zero_right",
                "have hgn : g = n",
                "specialize is_gcd_unique g",
                "specialize is_gcd_unique n",
                "specialize is_gcd_unique n",
                "specialize is_gcd_unique 0",
                "apply is_gcd_unique",
                "exact hsym",
                "exact hn",
                "rewrite hgn at hab",
                "rewrite hgn at hab",
                "exists a",
                "split",
                "specialize mod_eq_refl 0",
                "specialize mod_eq_refl a",
                "exact mod_eq_refl",
                "exact hab",
            ),
            "If the left modulus is zero, gcd compatibility constructs a solution by choosing the left residue.",
        ),
        spec(
            "generalized_binary_crt_sufficient_zero_right",
            f"forall g m a b. ({right_gcd}) -> ({right_compatibility}) -> "
            f"exists x. ({right_solution})",
            (
                "is_gcd_zero_right",
                "is_gcd_unique",
                "mod_eq_symm",
                "mod_eq_refl",
            ),
            (
                "intro g",
                "intro m",
                "intro a",
                "intro b",
                "intro hg",
                "intro hab",
                f"have hm : {right_gcd_base}",
                "specialize is_gcd_zero_right m",
                "exact is_gcd_zero_right",
                "have hgm : g = m",
                "specialize is_gcd_unique g",
                "specialize is_gcd_unique m",
                "specialize is_gcd_unique m",
                "specialize is_gcd_unique 0",
                "apply is_gcd_unique",
                "exact hg",
                "exact hm",
                "rewrite hgm at hab",
                "rewrite hgm at hab",
                "exists b",
                "split",
                "specialize mod_eq_symm m",
                "specialize mod_eq_symm a",
                "specialize mod_eq_symm b",
                "apply mod_eq_symm",
                "exact hab",
                "specialize mod_eq_refl 0",
                "specialize mod_eq_refl b",
                "exact mod_eq_refl",
            ),
            "If the right modulus is zero, gcd compatibility constructs a solution by choosing the right residue.",
        ),
        spec(
            "generalized_binary_crt_sufficient",
            f"forall g m n a b. ({total_gcd}) -> ({total_compatibility}) -> "
            f"exists x. ({total_solution})",
            (
                "eq_decidable",
                "generalized_binary_crt_sufficient_zero_left",
                "generalized_binary_crt_sufficient_zero_right",
                "generalized_binary_crt_sufficient_nonzero",
            ),
            (
                "intro g",
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro hg",
                "intro hab",
                "have hmzero : m = 0 \\/ ~(m = 0)",
                "specialize eq_decidable m",
                "specialize eq_decidable 0",
                "exact eq_decidable",
                "cases hmzero",
                "rewrite hmzero_left at hg",
                "rewrite hmzero_left at hg",
                "rewrite hmzero_left",
                "rewrite hmzero_left",
                "specialize generalized_binary_crt_sufficient_zero_left g",
                "specialize generalized_binary_crt_sufficient_zero_left n",
                "specialize generalized_binary_crt_sufficient_zero_left a",
                "specialize generalized_binary_crt_sufficient_zero_left b",
                "apply generalized_binary_crt_sufficient_zero_left",
                "exact hg",
                "exact hab",
                "have hnzero : n = 0 \\/ ~(n = 0)",
                "specialize eq_decidable n",
                "specialize eq_decidable 0",
                "exact eq_decidable",
                "cases hnzero",
                "rewrite hnzero_left at hg",
                "rewrite hnzero_left at hg",
                "rewrite hnzero_left",
                "rewrite hnzero_left",
                "specialize generalized_binary_crt_sufficient_zero_right g",
                "specialize generalized_binary_crt_sufficient_zero_right m",
                "specialize generalized_binary_crt_sufficient_zero_right a",
                "specialize generalized_binary_crt_sufficient_zero_right b",
                "apply generalized_binary_crt_sufficient_zero_right",
                "exact hg",
                "exact hab",
                "specialize generalized_binary_crt_sufficient_nonzero g",
                "specialize generalized_binary_crt_sufficient_nonzero m",
                "specialize generalized_binary_crt_sufficient_nonzero n",
                "specialize generalized_binary_crt_sufficient_nonzero a",
                "specialize generalized_binary_crt_sufficient_nonzero b",
                "apply generalized_binary_crt_sufficient_nonzero",
                "exact hmzero_right",
                "exact hnzero_right",
                "exact hg",
                "exact hab",
            ),
            "Gcd compatibility constructs a common solution for arbitrary natural moduli, including zero.",
        ),
        spec(
            "generalized_binary_crt_solvable_iff",
            f"forall g m n a b. ({iff_gcd}) -> "
            f"(((exists x. ({iff_forward_solution})) -> "
            f"({iff_forward_compatibility})) /\\ "
            f"(({iff_reverse_compatibility}) -> "
            f"exists x. ({iff_reverse_solution})))",
            (
                "crt_common_solution_implies_gcd_compatible",
                "generalized_binary_crt_sufficient",
            ),
            (
                "intro g",
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro hg",
                "split",
                "intro hsolution",
                "cases hsolution",
                "specialize crt_common_solution_implies_gcd_compatible g",
                "specialize crt_common_solution_implies_gcd_compatible m",
                "specialize crt_common_solution_implies_gcd_compatible n",
                "specialize crt_common_solution_implies_gcd_compatible a",
                "specialize crt_common_solution_implies_gcd_compatible b",
                "specialize crt_common_solution_implies_gcd_compatible x",
                "apply crt_common_solution_implies_gcd_compatible",
                "exact hg",
                "exact hsolution_witness",
                "intro hcompat",
                "specialize generalized_binary_crt_sufficient g",
                "specialize generalized_binary_crt_sufficient m",
                "specialize generalized_binary_crt_sufficient n",
                "specialize generalized_binary_crt_sufficient a",
                "specialize generalized_binary_crt_sufficient b",
                "apply generalized_binary_crt_sufficient",
                "exact hg",
                "exact hcompat",
            ),
            "For arbitrary natural moduli, a binary CRT system is solvable exactly when its residues are congruent modulo a relational gcd.",
        ),
    )


__all__ = ["make_ha_generalized_crt_zero_boundary_candidate_theorems"]
