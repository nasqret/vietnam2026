"""Canonical boundary for binary generalized CRT over all natural moduli.

The M5c solution-class theorem is uniform at a zero relational lcm, but a
canonical *remainder* is not: there is no natural strictly below zero.  This
isolated M5d layer therefore proves the mathematically correct split.

* at lcm zero, every common solution is exactly equal to a fixed solution;
* at nonzero lcm, division produces the unique common solution below the lcm;
* a final constructive equality decision packages those two alternatives.

``IsGCD``, ``IsLCM``, ``ModEq``, ``CRTSolution`` and ``Below`` are only
readable authoring surfaces.  Every occurrence expands hygienically to the
unchanged first-order HA language over ``0, S, +, *, =``.  Nothing in this
module is registered or admitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_gcd_candidate import is_gcd
from .ha_generalized_crt_congruence_candidate import (
    balanced_mod_eq,
    crt_solution,
)
from .ha_relational_lcm_candidate import is_lcm


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def below(
    value: str,
    bound: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand strict order as a hygienic successor-gap witness."""

    if (
        not isinstance(variables, tuple)
        or not variables
        or len(set(variables)) != len(variables)
    ):
        raise ValueError(
            "term context must be a nonempty tuple of distinct identifiers"
        )
    checked_variables = tuple(
        _identifier(variable, "term context variable")
        for variable in variables
    )
    checked_value = _identifier(value, "bounded value")
    checked_bound = _identifier(bound, "strict bound")
    if (
        checked_value not in checked_variables
        or checked_bound not in checked_variables
    ):
        raise ValueError("Below arguments must belong to the term context")
    safe_tag = _identifier(tag, "Below tag")
    gap = f"hgcrt_below_gap_{safe_tag}"
    if gap in set(checked_variables):
        raise ValueError("generated Below binder captures an argument")
    return f"exists {gap}. {gap} + S {checked_value} = {checked_bound}"


def make_ha_generalized_crt_canonical_boundary_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the three-row zero/nonzero canonical-boundary ladder."""

    zero_variables = ("l", "m", "n", "a", "b", "x", "y")
    zero_lcm = is_lcm("l", "m", "n", tag="unique_zero")
    zero_fixed = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="unique_zero_fixed",
        variables=zero_variables,
    )
    zero_candidate = crt_solution(
        "y",
        "m",
        "n",
        "a",
        "b",
        tag="unique_zero_candidate",
        variables=zero_variables,
    )
    zero_class_candidate_forward = crt_solution(
        "y",
        "m",
        "n",
        "a",
        "b",
        tag="unique_zero_iff_forward",
        variables=zero_variables,
    )
    zero_class_candidate_reverse = crt_solution(
        "y",
        "m",
        "n",
        "a",
        "b",
        tag="unique_zero_iff_reverse",
        variables=zero_variables,
    )
    zero_class_mod_forward = balanced_mod_eq(
        "l",
        "y",
        "x",
        tag="unique_zero_mod_forward",
        variables=zero_variables,
    )
    zero_class_mod_reverse = balanced_mod_eq(
        "l",
        "y",
        "x",
        tag="unique_zero_mod_reverse",
        variables=zero_variables,
    )
    zero_class_iff = (
        f"((({zero_class_candidate_forward}) -> "
        f"({zero_class_mod_forward})) /\\ "
        f"(({zero_class_mod_reverse}) -> "
        f"({zero_class_candidate_reverse})))"
    )
    zero_mod_result = balanced_mod_eq(
        "l",
        "y",
        "x",
        tag="unique_zero_mod_result",
        variables=zero_variables,
    )

    canonical_variables = ("l", "m", "n", "a", "b", "x")
    canonical_lcm = is_lcm("l", "m", "n", tag="canonical_nonzero")
    canonical_fixed = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_nonzero_fixed",
        variables=canonical_variables,
    )
    canonical_result_variables = (*canonical_variables, "r")
    canonical_result_bound = below(
        "r",
        "l",
        tag="canonical_nonzero_result",
        variables=canonical_result_variables,
    )
    canonical_result_solution = crt_solution(
        "r",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_nonzero_result",
        variables=canonical_result_variables,
    )
    canonical_result_mod = balanced_mod_eq(
        "l",
        "r",
        "x",
        tag="canonical_nonzero_result",
        variables=canonical_result_variables,
    )
    canonical_comparison_variables = (*canonical_result_variables, "s")
    canonical_comparison_bound = below(
        "s",
        "l",
        tag="canonical_nonzero_comparison",
        variables=canonical_comparison_variables,
    )
    canonical_comparison_solution = crt_solution(
        "s",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_nonzero_comparison",
        variables=canonical_comparison_variables,
    )

    runtime_variables = (*canonical_variables, "x1", "x2")
    runtime_result_solution = crt_solution(
        "x2",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_runtime_result",
        variables=runtime_variables,
    )
    runtime_mod_x_x2 = balanced_mod_eq(
        "l",
        "x",
        "x2",
        tag="canonical_runtime_x_x2",
        variables=runtime_variables,
    )
    runtime_mod_x2_x = balanced_mod_eq(
        "l",
        "x2",
        "x",
        tag="canonical_runtime_x2_x",
        variables=runtime_variables,
    )
    runtime_class_solution_forward = crt_solution(
        "x2",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_runtime_class_forward",
        variables=runtime_variables,
    )
    runtime_class_solution_reverse = crt_solution(
        "x2",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_runtime_class_reverse",
        variables=runtime_variables,
    )
    runtime_class_mod_forward = balanced_mod_eq(
        "l",
        "x2",
        "x",
        tag="canonical_runtime_class_forward",
        variables=runtime_variables,
    )
    runtime_class_mod_reverse = balanced_mod_eq(
        "l",
        "x2",
        "x",
        tag="canonical_runtime_class_reverse",
        variables=runtime_variables,
    )
    runtime_result_class_iff = (
        f"((({runtime_class_solution_forward}) -> "
        f"({runtime_class_mod_forward})) /\\ "
        f"(({runtime_class_mod_reverse}) -> "
        f"({runtime_class_solution_reverse})))"
    )
    comparison_runtime_variables = (*runtime_variables, "s")
    runtime_comparison_solution_forward = crt_solution(
        "s",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_runtime_comparison_forward",
        variables=comparison_runtime_variables,
    )
    runtime_comparison_solution_reverse = crt_solution(
        "s",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_runtime_comparison_reverse",
        variables=comparison_runtime_variables,
    )
    runtime_comparison_mod_forward = balanced_mod_eq(
        "l",
        "s",
        "x2",
        tag="canonical_runtime_comparison_forward",
        variables=comparison_runtime_variables,
    )
    runtime_comparison_mod_reverse = balanced_mod_eq(
        "l",
        "s",
        "x2",
        tag="canonical_runtime_comparison_reverse",
        variables=comparison_runtime_variables,
    )
    runtime_comparison_class_iff = (
        f"((({runtime_comparison_solution_forward}) -> "
        f"({runtime_comparison_mod_forward})) /\\ "
        f"(({runtime_comparison_mod_reverse}) -> "
        f"({runtime_comparison_solution_reverse})))"
    )
    runtime_comparison_mod = balanced_mod_eq(
        "l",
        "s",
        "x2",
        tag="canonical_runtime_comparison_result",
        variables=comparison_runtime_variables,
    )

    boundary_variables = ("g", "l", "m", "n", "a", "b")
    boundary_gcd = is_gcd("g", "m", "n", tag="canonical_boundary")
    boundary_lcm = is_lcm("l", "m", "n", tag="canonical_boundary")
    boundary_compatibility = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="canonical_boundary_compatibility",
        variables=boundary_variables,
    )
    boundary_fixed_variables = (*boundary_variables, "x")
    boundary_fixed_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_boundary_fixed",
        variables=boundary_fixed_variables,
    )
    boundary_zero_candidate_variables = (*boundary_fixed_variables, "y")
    boundary_zero_candidate = crt_solution(
        "y",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_boundary_zero_candidate",
        variables=boundary_zero_candidate_variables,
    )
    boundary_result_variables = (*boundary_variables, "r")
    boundary_result_bound = below(
        "r",
        "l",
        tag="canonical_boundary_result",
        variables=boundary_result_variables,
    )
    boundary_result_solution = crt_solution(
        "r",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_boundary_result",
        variables=boundary_result_variables,
    )
    boundary_comparison_variables = (*boundary_result_variables, "s")
    boundary_comparison_bound = below(
        "s",
        "l",
        tag="canonical_boundary_comparison",
        variables=boundary_comparison_variables,
    )
    boundary_comparison_solution = crt_solution(
        "s",
        "m",
        "n",
        "a",
        "b",
        tag="canonical_boundary_comparison",
        variables=boundary_comparison_variables,
    )
    boundary_zero_branch = (
        f"(l = 0 /\\ exists x. (({boundary_fixed_solution}) /\\ "
        f"forall y. ({boundary_zero_candidate}) -> y = x))"
    )
    boundary_nonzero_branch = (
        f"(~(l = 0) /\\ exists r. "
        f"((({boundary_result_bound}) /\\ ({boundary_result_solution})) /\\ "
        f"forall s. ({boundary_comparison_bound}) -> "
        f"({boundary_comparison_solution}) -> s = r))"
    )
    boundary_runtime_mod = balanced_mod_eq(
        "l",
        "r",
        "x",
        tag="canonical_boundary_runtime_mod",
        variables=(*boundary_fixed_variables, "r"),
    )

    return (
        spec(
            "crt_solution_unique_lcm_zero",
            f"forall l m n a b x y. l = 0 -> ({zero_lcm}) -> "
            f"({zero_fixed}) -> ({zero_candidate}) -> y = x",
            ("crt_solution_class_iff_lcm", "mod_eq_zero_iff_eq"),
            (
                "intro l",
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro x",
                "intro y",
                "intro hl",
                "intro hlcm",
                "intro hx",
                "intro hy",
                f"have hiff : {zero_class_iff}",
                "specialize crt_solution_class_iff_lcm l",
                "specialize crt_solution_class_iff_lcm m",
                "specialize crt_solution_class_iff_lcm n",
                "specialize crt_solution_class_iff_lcm a",
                "specialize crt_solution_class_iff_lcm b",
                "specialize crt_solution_class_iff_lcm x",
                "specialize crt_solution_class_iff_lcm y",
                "apply crt_solution_class_iff_lcm",
                "exact hlcm",
                "exact hx",
                "cases hiff",
                f"have hmod : {zero_mod_result}",
                "apply hiff_left",
                "exact hy",
                "rewrite hl at hmod",
                "rewrite hl at hmod",
                "specialize mod_eq_zero_iff_eq y",
                "specialize mod_eq_zero_iff_eq x",
                "cases mod_eq_zero_iff_eq",
                "apply mod_eq_zero_iff_eq_left",
                "exact hmod",
            ),
            "At relational lcm zero, every common solution equals a fixed common solution.",
        ),
        spec(
            "crt_solution_canonical_remainder_nonzero",
            f"forall l m n a b x. ~(l = 0) -> ({canonical_lcm}) -> "
            f"({canonical_fixed}) -> exists r. "
            f"((({canonical_result_bound}) /\\ "
            f"({canonical_result_solution})) /\\ "
            f"(({canonical_result_mod}) /\\ forall s. "
            f"({canonical_comparison_bound}) -> "
            f"({canonical_comparison_solution}) -> s = r))",
            (
                "division_remainder_exists",
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
                "mod_eq_symm",
                "crt_solution_class_iff_lcm",
                "mod_eq_bounded_unique",
            ),
            (
                "intro l",
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro x",
                "intro hl",
                "intro hlcm",
                "intro hx",
                "have hdivision : exists q r. x = l * q + r /\\ "
                "exists gap. gap + S r = l",
                "specialize division_remainder_exists l",
                "specialize division_remainder_exists x",
                "apply division_remainder_exists",
                "exact hl",
                "cases hdivision",
                "cases hdivision_witness",
                "cases hdivision_witness_witness",
                "have hxdecomp : x = x1 * l + x2",
                "trans l * x1 + x2",
                "exact hdivision_witness_witness_left",
                "congr",
                "apply mul_comm",
                "refl",
                f"have hxx2 : {runtime_mod_x_x2}",
                "specialize remainder_decomposition_to_mod_eq l",
                "specialize remainder_decomposition_to_mod_eq x",
                "specialize remainder_decomposition_to_mod_eq x1",
                "specialize remainder_decomposition_to_mod_eq x2",
                "apply remainder_decomposition_to_mod_eq",
                "exact hxdecomp",
                f"have hx2x : {runtime_mod_x2_x}",
                "specialize mod_eq_symm l",
                "specialize mod_eq_symm x",
                "specialize mod_eq_symm x2",
                "apply mod_eq_symm",
                "exact hxx2",
                f"have hclass : {runtime_result_class_iff}",
                "specialize crt_solution_class_iff_lcm l",
                "specialize crt_solution_class_iff_lcm m",
                "specialize crt_solution_class_iff_lcm n",
                "specialize crt_solution_class_iff_lcm a",
                "specialize crt_solution_class_iff_lcm b",
                "specialize crt_solution_class_iff_lcm x",
                "specialize crt_solution_class_iff_lcm x2",
                "apply crt_solution_class_iff_lcm",
                "exact hlcm",
                "exact hx",
                "cases hclass",
                f"have hrsol : {runtime_result_solution}",
                "apply hclass_right",
                "exact hx2x",
                "exists x2",
                "split",
                "split",
                "exact hdivision_witness_witness_right",
                "exact hrsol",
                "split",
                "exact hx2x",
                "intro s",
                "intro hsbound",
                "intro hssol",
                f"have hclasss : {runtime_comparison_class_iff}",
                "specialize crt_solution_class_iff_lcm l",
                "specialize crt_solution_class_iff_lcm m",
                "specialize crt_solution_class_iff_lcm n",
                "specialize crt_solution_class_iff_lcm a",
                "specialize crt_solution_class_iff_lcm b",
                "specialize crt_solution_class_iff_lcm x2",
                "specialize crt_solution_class_iff_lcm s",
                "apply crt_solution_class_iff_lcm",
                "exact hlcm",
                "exact hrsol",
                "cases hclasss",
                f"have hsmod : {runtime_comparison_mod}",
                "apply hclasss_left",
                "exact hssol",
                "specialize mod_eq_bounded_unique l",
                "specialize mod_eq_bounded_unique s",
                "specialize mod_eq_bounded_unique x2",
                "apply mod_eq_bounded_unique",
                "exact hsbound",
                "exact hdivision_witness_witness_right",
                "exact hsmod",
            ),
            "At nonzero relational lcm, every solvable binary CRT system has a unique solution below the lcm.",
        ),
        spec(
            "generalized_binary_crt_canonical_boundary",
            f"forall g l m n a b. ({boundary_gcd}) -> ({boundary_lcm}) -> "
            f"({boundary_compatibility}) -> "
            f"(({boundary_zero_branch}) \\/ ({boundary_nonzero_branch}))",
            (
                "eq_decidable",
                "generalized_binary_crt_sufficient",
                "crt_solution_unique_lcm_zero",
                "crt_solution_canonical_remainder_nonzero",
            ),
            (
                "intro g",
                "intro l",
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro hg",
                "intro hl",
                "intro hab",
                f"have hexists : exists x. ({boundary_fixed_solution})",
                "specialize generalized_binary_crt_sufficient g",
                "specialize generalized_binary_crt_sufficient m",
                "specialize generalized_binary_crt_sufficient n",
                "specialize generalized_binary_crt_sufficient a",
                "specialize generalized_binary_crt_sufficient b",
                "apply generalized_binary_crt_sufficient",
                "exact hg",
                "exact hab",
                "cases hexists",
                "have hlzero : l = 0 \\/ ~(l = 0)",
                "specialize eq_decidable l",
                "specialize eq_decidable 0",
                "exact eq_decidable",
                "cases hlzero",
                "left",
                "split",
                "exact hlzero_left",
                "exists x",
                "split",
                "exact hexists_witness",
                "intro y",
                "intro hy",
                "specialize crt_solution_unique_lcm_zero l",
                "specialize crt_solution_unique_lcm_zero m",
                "specialize crt_solution_unique_lcm_zero n",
                "specialize crt_solution_unique_lcm_zero a",
                "specialize crt_solution_unique_lcm_zero b",
                "specialize crt_solution_unique_lcm_zero x",
                "specialize crt_solution_unique_lcm_zero y",
                "apply crt_solution_unique_lcm_zero",
                "exact hlzero_left",
                "exact hl",
                "exact hexists_witness",
                "exact hy",
                "right",
                "split",
                "exact hlzero_right",
                "have hcanonical : exists r. "
                f"((({below('r', 'l', tag='canonical_boundary_runtime_result', variables=(*boundary_fixed_variables, 'r'))}) /\\ "
                f"({crt_solution('r', 'm', 'n', 'a', 'b', tag='canonical_boundary_runtime_result', variables=(*boundary_fixed_variables, 'r'))})) /\\ "
                f"(({boundary_runtime_mod}) /\\ forall s. "
                f"({below('s', 'l', tag='canonical_boundary_runtime_comparison', variables=(*boundary_fixed_variables, 'r', 's'))}) -> "
                f"({crt_solution('s', 'm', 'n', 'a', 'b', tag='canonical_boundary_runtime_comparison', variables=(*boundary_fixed_variables, 'r', 's'))}) -> s = r))",
                "specialize crt_solution_canonical_remainder_nonzero l",
                "specialize crt_solution_canonical_remainder_nonzero m",
                "specialize crt_solution_canonical_remainder_nonzero n",
                "specialize crt_solution_canonical_remainder_nonzero a",
                "specialize crt_solution_canonical_remainder_nonzero b",
                "specialize crt_solution_canonical_remainder_nonzero x",
                "apply crt_solution_canonical_remainder_nonzero",
                "exact hlzero_right",
                "exact hl",
                "exact hexists_witness",
                "cases hcanonical",
                "exists x1",
                "split",
                "cases hcanonical_witness",
                "exact hcanonical_witness_left",
                "cases hcanonical_witness",
                "cases hcanonical_witness_right",
                "exact hcanonical_witness_right_right",
            ),
            "Every compatible binary CRT system has the correct canonical boundary: exact uniqueness at lcm zero or one unique bounded representative at nonzero lcm.",
        ),
    )


__all__ = [
    "below",
    "make_ha_generalized_crt_canonical_boundary_candidate_theorems",
]
