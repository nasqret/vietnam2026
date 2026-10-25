"""Constructive decision boundary for binary generalized CRT.

The preceding M5 layers prove existence, obstruction, solution classes, and
the zero/nonzero canonical split.  This isolated M5e layer makes the remaining
binary compatibility test total.  It first extends the public nonzero-modulus
congruence decision theorem across modulus zero, then returns either compatible
residues together with a CRT solution or incompatible residues together with
a proof that no CRT solution exists.

``IsGCD``, ``ModEq`` and ``CRTSolution`` are only hygienic authoring surfaces.
They expand before parsing to ordinary first-order HA over ``0, S, +, *, =``.
Nothing in this module is registered or admitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_gcd_candidate import is_gcd
from .ha_generalized_crt_congruence_candidate import balanced_mod_eq, crt_solution


def make_ha_generalized_crt_decision_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the two-row all-modulus decision and obstruction ladder."""

    decision_variables = ("d", "a", "b")
    decision_yes = balanced_mod_eq(
        "d",
        "a",
        "b",
        tag="decision_yes",
        variables=decision_variables,
    )
    decision_no = balanced_mod_eq(
        "d",
        "a",
        "b",
        tag="decision_no",
        variables=decision_variables,
    )
    zero_forward = balanced_mod_eq(
        "0",
        "a",
        "b",
        tag="decision_zero_forward",
        variables=decision_variables,
    )
    zero_reverse = balanced_mod_eq(
        "0",
        "a",
        "b",
        tag="decision_zero_reverse",
        variables=decision_variables,
    )

    boundary_variables = ("g", "m", "n", "a", "b")
    boundary_gcd = is_gcd("g", "m", "n", tag="decision_boundary")
    boundary_compatible = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="decision_boundary_compatible",
        variables=boundary_variables,
    )
    boundary_incompatible = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="decision_boundary_incompatible",
        variables=boundary_variables,
    )
    boundary_positive_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="decision_boundary_positive",
        variables=(*boundary_variables, "x"),
    )
    boundary_negative_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="decision_boundary_negative",
        variables=(*boundary_variables, "x"),
    )
    runtime_compatible = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="decision_runtime_compatible",
        variables=boundary_variables,
    )
    runtime_incompatible = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="decision_runtime_incompatible",
        variables=boundary_variables,
    )

    return (
        spec(
            "mod_eq_decidable",
            f"forall d a b. ({decision_yes}) \\/ ~({decision_no})",
            (
                "eq_decidable",
                "mod_eq_zero_iff_eq",
                "mod_eq_decidable_nonzero",
            ),
            (
                "intro d",
                "intro a",
                "intro b",
                "have hd : d = 0 \\/ ~(d = 0)",
                "specialize eq_decidable d",
                "specialize eq_decidable 0",
                "exact eq_decidable",
                "cases hd",
                f"have hzero : ((({zero_forward}) -> a = b) /\\ "
                f"(a = b -> ({zero_reverse})))",
                "specialize mod_eq_zero_iff_eq a",
                "specialize mod_eq_zero_iff_eq b",
                "exact mod_eq_zero_iff_eq",
                "cases hzero",
                "have hab : a = b \\/ ~(a = b)",
                "specialize eq_decidable a",
                "specialize eq_decidable b",
                "exact eq_decidable",
                "cases hab",
                "left",
                "rewrite hd_left",
                "rewrite hd_left",
                "apply hzero_right",
                "exact hab_left",
                "right",
                "intro hmod",
                "rewrite hd_left at hmod",
                "rewrite hd_left at hmod",
                "apply hab_right",
                "apply hzero_left",
                "exact hmod",
                "specialize mod_eq_decidable_nonzero d",
                "specialize mod_eq_decidable_nonzero a",
                "specialize mod_eq_decidable_nonzero b",
                "apply mod_eq_decidable_nonzero",
                "exact hd_right",
            ),
            "Balanced congruence is constructively decidable for every natural modulus.",
        ),
        spec(
            "generalized_binary_crt_solution_or_obstruction",
            f"forall g m n a b. ({boundary_gcd}) -> "
            f"((({boundary_compatible}) /\\ "
            f"exists x. ({boundary_positive_solution})) \\/ "
            f"(~({boundary_incompatible}) /\\ "
            f"~(exists x. ({boundary_negative_solution}))))",
            (
                "mod_eq_decidable",
                "generalized_binary_crt_sufficient",
                "crt_incompatibility_obstructs_solution",
            ),
            (
                "intro g",
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro hgcd",
                f"have hcompat : ({runtime_compatible}) \\/ "
                f"~({runtime_incompatible})",
                "specialize mod_eq_decidable g",
                "specialize mod_eq_decidable a",
                "specialize mod_eq_decidable b",
                "apply mod_eq_decidable",
                "cases hcompat",
                "left",
                "split",
                "exact hcompat_left",
                "specialize generalized_binary_crt_sufficient g",
                "specialize generalized_binary_crt_sufficient m",
                "specialize generalized_binary_crt_sufficient n",
                "specialize generalized_binary_crt_sufficient a",
                "specialize generalized_binary_crt_sufficient b",
                "apply generalized_binary_crt_sufficient",
                "exact hgcd",
                "exact hcompat_left",
                "right",
                "split",
                "exact hcompat_right",
                "intro hsolution",
                "specialize crt_incompatibility_obstructs_solution g",
                "specialize crt_incompatibility_obstructs_solution m",
                "specialize crt_incompatibility_obstructs_solution n",
                "specialize crt_incompatibility_obstructs_solution a",
                "specialize crt_incompatibility_obstructs_solution b",
                "apply crt_incompatibility_obstructs_solution",
                "exact hgcd",
                "exact hcompat_right",
                "exact hsolution",
            ),
            "Every generalized binary CRT instance constructively returns a solution or a certified incompatibility obstruction.",
        ),
    )


__all__ = ["make_ha_generalized_crt_decision_candidate_theorems"]
