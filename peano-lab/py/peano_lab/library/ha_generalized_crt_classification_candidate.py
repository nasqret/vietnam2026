"""Relational-LCM classification of binary generalized-CRT solutions.

The preceding M5 layers construct a common solution exactly when the two
residues are compatible modulo a relational gcd.  This isolated M5c layer
describes every solution once one exists: two values satisfy the same binary
system exactly when they are congruent modulo any supplied relational lcm.

The proof is subtraction-free.  A total-order split exposes the directed gap
between two congruent naturals, ``factor_difference`` shows that each modulus
divides that gap, and the universal property of ``IsLCM`` combines the two
divisibility facts.  The argument is uniform at modulus zero and uses neither
classical logic nor a primitive lcm function.  All readable predicates expand
hygienically before the unchanged first-order HA kernel sees the statements.
Nothing in this module is registered or admitted.
"""

from __future__ import annotations

from typing import Any, Callable

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


def divides(
    divisor: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand divisibility with one locally owned hygienic witness."""

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
    checked_divisor = _identifier(divisor, "divisor")
    checked_value = _identifier(value, "divisible value")
    if (
        checked_divisor not in checked_variables
        or checked_value not in checked_variables
    ):
        raise ValueError("divisibility arguments must belong to the term context")
    safe_tag = _identifier(tag, "divisibility tag")
    witness = f"hgcrt_divides_factor_{safe_tag}"
    if witness in set(checked_variables):
        raise ValueError("generated divisibility binder captures an argument")
    return f"exists {witness}. {checked_value} = {checked_divisor} * {witness}"


def make_ha_generalized_crt_classification_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the four-row all-modulus solution-class ladder."""

    gap_variables = ("d", "k", "x", "y")
    gap_mod_eq = balanced_mod_eq(
        "d",
        "x",
        "y",
        tag="ordered_gap_assumption",
        variables=gap_variables,
    )
    gap_divides = divides(
        "d", "k", tag="ordered_gap_result", variables=gap_variables
    )

    merge_variables = ("l", "m", "n", "x", "y")
    merge_lcm = is_lcm("l", "m", "n", tag="merge")
    merge_mod_m = balanced_mod_eq(
        "m", "x", "y", tag="merge_m", variables=merge_variables
    )
    merge_mod_n = balanced_mod_eq(
        "n", "x", "y", tag="merge_n", variables=merge_variables
    )
    merge_mod_l = balanced_mod_eq(
        "l", "x", "y", tag="merge_l", variables=merge_variables
    )
    merge_mod_m_reverse = balanced_mod_eq(
        "m", "y", "x", tag="merge_m_reverse", variables=merge_variables
    )
    merge_mod_n_reverse = balanced_mod_eq(
        "n", "y", "x", tag="merge_n_reverse", variables=merge_variables
    )
    merge_mod_l_reverse = balanced_mod_eq(
        "l", "y", "x", tag="merge_l_reverse", variables=merge_variables
    )

    iff_lcm = is_lcm("l", "m", "n", tag="iff_pair")
    iff_mod_l_forward = balanced_mod_eq(
        "l", "x", "y", tag="iff_l_forward", variables=merge_variables
    )
    iff_mod_m_forward = balanced_mod_eq(
        "m", "x", "y", tag="iff_m_forward", variables=merge_variables
    )
    iff_mod_n_forward = balanced_mod_eq(
        "n", "x", "y", tag="iff_n_forward", variables=merge_variables
    )
    iff_mod_m_reverse = balanced_mod_eq(
        "m", "x", "y", tag="iff_m_reverse", variables=merge_variables
    )
    iff_mod_n_reverse = balanced_mod_eq(
        "n", "x", "y", tag="iff_n_reverse", variables=merge_variables
    )
    iff_mod_l_reverse = balanced_mod_eq(
        "l", "x", "y", tag="iff_l_reverse", variables=merge_variables
    )

    class_variables = ("l", "m", "n", "a", "b", "x", "y")
    class_lcm = is_lcm("l", "m", "n", tag="solution_class")
    class_fixed = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="class_fixed",
        variables=class_variables,
    )
    class_candidate_forward = crt_solution(
        "y",
        "m",
        "n",
        "a",
        "b",
        tag="class_candidate_forward",
        variables=class_variables,
    )
    class_mod_l_forward = balanced_mod_eq(
        "l", "y", "x", tag="class_l_forward", variables=class_variables
    )
    class_mod_l_reverse = balanced_mod_eq(
        "l", "y", "x", tag="class_l_reverse", variables=class_variables
    )
    class_candidate_reverse = crt_solution(
        "y",
        "m",
        "n",
        "a",
        "b",
        tag="class_candidate_reverse",
        variables=class_variables,
    )
    class_pair_m = balanced_mod_eq(
        "m", "y", "x", tag="class_pair_m", variables=class_variables
    )
    class_pair_n = balanced_mod_eq(
        "n", "y", "x", tag="class_pair_n", variables=class_variables
    )
    class_pair = f"(({class_pair_m}) /\\ ({class_pair_n}))"
    class_mod_l_aux = balanced_mod_eq(
        "l", "y", "x", tag="class_l_aux", variables=class_variables
    )
    class_iff = (
        f"((({class_mod_l_aux}) -> {class_pair}) /\\ "
        f"({class_pair} -> ({class_mod_l_aux})))"
    )

    return (
        spec(
            "mod_eq_ordered_gap_multiple",
            f"forall d k x y. k + x = y -> ({gap_mod_eq}) -> "
            f"({gap_divides})",
            ("add_comm", "add_assoc", "add_left_cancel", "factor_difference"),
            (
                "intro d",
                "intro k",
                "intro x",
                "intro y",
                "intro hgap",
                "intro hmod",
                "cases hmod",
                "cases hmod_witness",
                "rewrite <- hgap at hmod_witness_witness",
                "have hcancel : d * x1 = k + d * x2",
                "specialize add_left_cancel x",
                "specialize add_left_cancel (d * x1)",
                "specialize add_left_cancel (k + d * x2)",
                "apply add_left_cancel",
                "trans (k + x) + d * x2",
                "exact hmod_witness_witness",
                "trans (x + k) + d * x2",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
                "have hfactor : d * x1 = d * x2 + k",
                "trans k + d * x2",
                "exact hcancel",
                "apply add_comm",
                "specialize factor_difference d",
                "specialize factor_difference x1",
                "specialize factor_difference x2",
                "specialize factor_difference k",
                "apply factor_difference",
                "exact hfactor",
            ),
            "The directed gap between two congruent naturals is a multiple of the modulus.",
        ),
        spec(
            "mod_eq_lcm_merge",
            f"forall l m n x y. ({merge_lcm}) -> ({merge_mod_m}) -> "
            f"({merge_mod_n}) -> ({merge_mod_l})",
            (
                "le_total",
                "mod_eq_symm",
                "mod_eq_ordered_gap_multiple",
                "is_lcm_least",
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
            ),
            (
                "intro l",
                "intro m",
                "intro n",
                "intro x",
                "intro y",
                "intro hl",
                "intro hm",
                "intro hn",
                "have horder : x <= y \\/ y <= x",
                "specialize le_total x",
                "specialize le_total y",
                "exact le_total",
                "cases horder",
                "cases horder_left",
                "have hmk : exists q. x1 = m * q",
                "specialize mod_eq_ordered_gap_multiple m",
                "specialize mod_eq_ordered_gap_multiple x1",
                "specialize mod_eq_ordered_gap_multiple x",
                "specialize mod_eq_ordered_gap_multiple y",
                "apply mod_eq_ordered_gap_multiple",
                "exact horder_left_witness",
                "exact hm",
                "have hnk : exists q. x1 = n * q",
                "specialize mod_eq_ordered_gap_multiple n",
                "specialize mod_eq_ordered_gap_multiple x1",
                "specialize mod_eq_ordered_gap_multiple x",
                "specialize mod_eq_ordered_gap_multiple y",
                "apply mod_eq_ordered_gap_multiple",
                "exact horder_left_witness",
                "exact hn",
                "have hlk : exists q. x1 = l * q",
                "specialize is_lcm_least l",
                "specialize is_lcm_least m",
                "specialize is_lcm_least n",
                "specialize is_lcm_least x1",
                "apply is_lcm_least",
                "exact hl",
                "exact hmk",
                "exact hnk",
                "cases hlk",
                "have hdecomp : y = x2 * l + x",
                "trans x1 + x",
                "symm",
                "exact horder_left_witness",
                "rewrite hlk_witness",
                "congr",
                "apply mul_comm",
                "refl",
                f"have hyx : {merge_mod_l_reverse}",
                "specialize remainder_decomposition_to_mod_eq l",
                "specialize remainder_decomposition_to_mod_eq y",
                "specialize remainder_decomposition_to_mod_eq x2",
                "specialize remainder_decomposition_to_mod_eq x",
                "apply remainder_decomposition_to_mod_eq",
                "exact hdecomp",
                "specialize mod_eq_symm l",
                "specialize mod_eq_symm y",
                "specialize mod_eq_symm x",
                "apply mod_eq_symm",
                "exact hyx",
                "cases horder_right",
                f"have hmyx : {merge_mod_m_reverse}",
                "specialize mod_eq_symm m",
                "specialize mod_eq_symm x",
                "specialize mod_eq_symm y",
                "apply mod_eq_symm",
                "exact hm",
                f"have hnyx : {merge_mod_n_reverse}",
                "specialize mod_eq_symm n",
                "specialize mod_eq_symm x",
                "specialize mod_eq_symm y",
                "apply mod_eq_symm",
                "exact hn",
                "have hmk : exists q. x1 = m * q",
                "specialize mod_eq_ordered_gap_multiple m",
                "specialize mod_eq_ordered_gap_multiple x1",
                "specialize mod_eq_ordered_gap_multiple y",
                "specialize mod_eq_ordered_gap_multiple x",
                "apply mod_eq_ordered_gap_multiple",
                "exact horder_right_witness",
                "exact hmyx",
                "have hnk : exists q. x1 = n * q",
                "specialize mod_eq_ordered_gap_multiple n",
                "specialize mod_eq_ordered_gap_multiple x1",
                "specialize mod_eq_ordered_gap_multiple y",
                "specialize mod_eq_ordered_gap_multiple x",
                "apply mod_eq_ordered_gap_multiple",
                "exact horder_right_witness",
                "exact hnyx",
                "have hlk : exists q. x1 = l * q",
                "specialize is_lcm_least l",
                "specialize is_lcm_least m",
                "specialize is_lcm_least n",
                "specialize is_lcm_least x1",
                "apply is_lcm_least",
                "exact hl",
                "exact hmk",
                "exact hnk",
                "cases hlk",
                "have hdecomp : x = x2 * l + y",
                "trans x1 + y",
                "symm",
                "exact horder_right_witness",
                "rewrite hlk_witness",
                "congr",
                "apply mul_comm",
                "refl",
                "specialize remainder_decomposition_to_mod_eq l",
                "specialize remainder_decomposition_to_mod_eq x",
                "specialize remainder_decomposition_to_mod_eq x2",
                "specialize remainder_decomposition_to_mod_eq y",
                "apply remainder_decomposition_to_mod_eq",
                "exact hdecomp",
            ),
            "Congruence modulo both inputs merges to congruence modulo a relational lcm.",
        ),
        spec(
            "mod_eq_lcm_iff_pair",
            f"forall l m n x y. ({iff_lcm}) -> "
            f"((({iff_mod_l_forward}) -> "
            f"(({iff_mod_m_forward}) /\\ ({iff_mod_n_forward}))) /\\ "
            f"((({iff_mod_m_reverse}) /\\ ({iff_mod_n_reverse})) -> "
            f"({iff_mod_l_reverse})))",
            (
                "is_lcm_multiple_left",
                "is_lcm_multiple_right",
                "mod_eq_of_mod_eq_multiple",
                "mod_eq_lcm_merge",
            ),
            (
                "intro l",
                "intro m",
                "intro n",
                "intro x",
                "intro y",
                "intro hl",
                "split",
                "intro hxy",
                "have hml : exists q. l = m * q",
                "specialize is_lcm_multiple_left l",
                "specialize is_lcm_multiple_left m",
                "specialize is_lcm_multiple_left n",
                "apply is_lcm_multiple_left",
                "exact hl",
                "have hnl : exists q. l = n * q",
                "specialize is_lcm_multiple_right l",
                "specialize is_lcm_multiple_right m",
                "specialize is_lcm_multiple_right n",
                "apply is_lcm_multiple_right",
                "exact hl",
                "split",
                "specialize mod_eq_of_mod_eq_multiple m",
                "specialize mod_eq_of_mod_eq_multiple l",
                "specialize mod_eq_of_mod_eq_multiple x",
                "specialize mod_eq_of_mod_eq_multiple y",
                "apply mod_eq_of_mod_eq_multiple",
                "exact hml",
                "exact hxy",
                "specialize mod_eq_of_mod_eq_multiple n",
                "specialize mod_eq_of_mod_eq_multiple l",
                "specialize mod_eq_of_mod_eq_multiple x",
                "specialize mod_eq_of_mod_eq_multiple y",
                "apply mod_eq_of_mod_eq_multiple",
                "exact hnl",
                "exact hxy",
                "intro hpair",
                "cases hpair",
                "specialize mod_eq_lcm_merge l",
                "specialize mod_eq_lcm_merge m",
                "specialize mod_eq_lcm_merge n",
                "specialize mod_eq_lcm_merge x",
                "specialize mod_eq_lcm_merge y",
                "apply mod_eq_lcm_merge",
                "exact hl",
                "exact hpair_left",
                "exact hpair_right",
            ),
            "Congruence modulo a relational lcm is equivalent to congruence modulo both inputs.",
        ),
        spec(
            "crt_solution_class_iff_lcm",
            f"forall l m n a b x y. ({class_lcm}) -> ({class_fixed}) -> "
            f"((({class_candidate_forward}) -> ({class_mod_l_forward})) /\\ "
            f"(({class_mod_l_reverse}) -> ({class_candidate_reverse})))",
            (
                "crt_solution_pair_congruent",
                "mod_eq_lcm_iff_pair",
                "mod_eq_trans",
            ),
            (
                "intro l",
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro x",
                "intro y",
                "intro hl",
                "intro hx",
                "split",
                "intro hy",
                f"have hpair : {class_pair}",
                "specialize crt_solution_pair_congruent m",
                "specialize crt_solution_pair_congruent n",
                "specialize crt_solution_pair_congruent a",
                "specialize crt_solution_pair_congruent b",
                "specialize crt_solution_pair_congruent y",
                "specialize crt_solution_pair_congruent x",
                "apply crt_solution_pair_congruent",
                "exact hy",
                "exact hx",
                f"have hiff : {class_iff}",
                "specialize mod_eq_lcm_iff_pair l",
                "specialize mod_eq_lcm_iff_pair m",
                "specialize mod_eq_lcm_iff_pair n",
                "specialize mod_eq_lcm_iff_pair y",
                "specialize mod_eq_lcm_iff_pair x",
                "apply mod_eq_lcm_iff_pair",
                "exact hl",
                "cases hiff",
                "apply hiff_right",
                "exact hpair",
                "intro hlyx",
                f"have hiff2 : {class_iff}",
                "specialize mod_eq_lcm_iff_pair l",
                "specialize mod_eq_lcm_iff_pair m",
                "specialize mod_eq_lcm_iff_pair n",
                "specialize mod_eq_lcm_iff_pair y",
                "specialize mod_eq_lcm_iff_pair x",
                "apply mod_eq_lcm_iff_pair",
                "exact hl",
                "cases hiff2",
                f"have hpair2 : {class_pair}",
                "apply hiff2_left",
                "exact hlyx",
                "cases hpair2",
                "cases hx",
                "split",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans y",
                "specialize mod_eq_trans x",
                "specialize mod_eq_trans a",
                "apply mod_eq_trans",
                "exact hpair2_left",
                "exact hx_left",
                "specialize mod_eq_trans n",
                "specialize mod_eq_trans y",
                "specialize mod_eq_trans x",
                "specialize mod_eq_trans b",
                "apply mod_eq_trans",
                "exact hpair2_right",
                "exact hx_right",
            ),
            "Relative to one fixed common solution, all solutions are exactly its relational-lcm congruence class.",
        ),
    )


__all__ = [
    "divides",
    "make_ha_generalized_crt_classification_candidate_theorems",
]
