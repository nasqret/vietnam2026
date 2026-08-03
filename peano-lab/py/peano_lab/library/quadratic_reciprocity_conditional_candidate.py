"""Conditional sign-free reciprocity wrappers over the green parity joins.

These candidates deliberately expose the two premises that the unfinished
orientation layer must still supply for each prime direction: a complete
Gauss QRes/parity classification and a modulo-two equality between its count
and the corresponding Eisenstein quotient sum.  Given those packages and the
exact quotient identity ``Q + U = h * k``, the existing count-sum join and
modulo-four truth tables yield the same-status and opposite-status forms of
quadratic reciprocity.

No primality or orientation premise is hidden here.  All relations expand to
ordinary first-order PA, and the candidates are constructive,
dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .quadratic_residue_surface import quadratic_residue


def _even(term: str, *, tag: str) -> str:
    return f"exists qrc_even_{tag}. {term} = 2 * qrc_even_{tag}"


def _odd(term: str, *, tag: str) -> str:
    return f"exists qrc_odd_{tag}. {term} = 2 * qrc_odd_{tag} + 1"


def _mod_two(left: str, right: str, *, tag: str) -> str:
    return (
        f"exists qrc_u_{tag} qrc_v_{tag}. "
        f"{left} + 2 * qrc_u_{tag} = {right} + 2 * qrc_v_{tag}"
    )


def _mod_four_one(term: str, *, tag: str) -> str:
    return f"exists qrc_one_{tag}. {term} = 4 * qrc_one_{tag} + 1"


def _mod_four_three(term: str, *, tag: str) -> str:
    return f"exists qrc_three_{tag}. {term} = 4 * qrc_three_{tag} + 3"


def _classification(proposition: str, count: str, *, tag: str) -> str:
    even = _even(count, tag=f"{tag}_even")
    odd = _odd(count, tag=f"{tag}_odd")
    return (
        f"(((({proposition}) -> ({even})) /\\ (({even}) -> ({proposition}))) /\\ "
        f"(((~({proposition})) -> ({odd})) /\\ (({odd}) -> ~({proposition}))))"
    )


def make_quadratic_reciprocity_conditional_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the one-mod-four and three-mod-four conditional wrappers."""

    q_pq = quadratic_residue("p", "q", tag="qrc_pq")
    q_qp = quadratic_residue("q", "p", tag="qrc_qp")
    class_e = _classification(q_pq, "e", tag="e")
    class_f = _classification(q_qp, "f", tag="f")
    e_q = _mod_two("e", "Q", tag="e_q")
    f_u = _mod_two("f", "U", tag="f_u")
    count_product = _mod_two("e + f", "h * k", tag="count_product")
    one_case = (
        f"(({_mod_four_one('p', tag='p')}) \/ "
        f"({_mod_four_one('q', tag='q')}))"
    )
    three_case = (
        f"(({_mod_four_three('p', tag='p')}) /\\ "
        f"({_mod_four_three('q', tag='q')}))"
    )
    same_status = f"((({q_pq}) /\\ ({q_qp})) \/ (~({q_pq}) /\\ ~({q_qp})))"
    opposite_status = f"((({q_pq}) /\\ ~({q_qp})) \/ (~({q_pq}) /\\ ({q_qp})))"
    common = (
        f"p = 2 * h + 1 -> q = 2 * k + 1 -> ({class_e}) -> "
        f"({class_f}) -> ({e_q}) -> ({f_u}) -> Q + U = h * k -> "
    )

    return (
        spec(
            "conditional_qres_same_status_from_oriented_gauss_counts",
            "forall p q e f Q U h k. "
            f"{common}({one_case}) -> ({same_status})",
            (
                "gauss_count_sum_mod_two_from_quotient_sums",
                "qres_same_status_from_mod_four_one",
            ),
            (
                "intro p", "intro q", "intro e", "intro f",
                "intro Q", "intro U", "intro h", "intro k",
                "intro hp", "intro hq", "intro heclass", "intro hfclass",
                "intro heq", "intro hfu", "intro hsum", "intro hone",
                f"have hcount : {count_product}",
                "specialize gauss_count_sum_mod_two_from_quotient_sums e",
                "specialize gauss_count_sum_mod_two_from_quotient_sums f",
                "specialize gauss_count_sum_mod_two_from_quotient_sums Q",
                "specialize gauss_count_sum_mod_two_from_quotient_sums U",
                "specialize gauss_count_sum_mod_two_from_quotient_sums h",
                "specialize gauss_count_sum_mod_two_from_quotient_sums k",
                "apply gauss_count_sum_mod_two_from_quotient_sums",
                "exact heq", "exact hfu", "exact hsum",
                "specialize qres_same_status_from_mod_four_one p",
                "specialize qres_same_status_from_mod_four_one q",
                "specialize qres_same_status_from_mod_four_one e",
                "specialize qres_same_status_from_mod_four_one f",
                "specialize qres_same_status_from_mod_four_one h",
                "specialize qres_same_status_from_mod_four_one k",
                "apply qres_same_status_from_mod_four_one",
                "exact hp", "exact hq", "exact heclass", "exact hfclass",
                "exact hcount", "exact hone",
            ),
            "Conditional one-mod-four reciprocity: the two cross-residue propositions have the same truth status.",
        ),
        spec(
            "conditional_qres_opposite_status_from_oriented_gauss_counts",
            "forall p q e f Q U h k. "
            f"{common}({three_case}) -> ({opposite_status})",
            (
                "gauss_count_sum_mod_two_from_quotient_sums",
                "qres_opposite_status_from_mod_four_three",
            ),
            (
                "intro p", "intro q", "intro e", "intro f",
                "intro Q", "intro U", "intro h", "intro k",
                "intro hp", "intro hq", "intro heclass", "intro hfclass",
                "intro heq", "intro hfu", "intro hsum", "intro hthree",
                f"have hcount : {count_product}",
                "specialize gauss_count_sum_mod_two_from_quotient_sums e",
                "specialize gauss_count_sum_mod_two_from_quotient_sums f",
                "specialize gauss_count_sum_mod_two_from_quotient_sums Q",
                "specialize gauss_count_sum_mod_two_from_quotient_sums U",
                "specialize gauss_count_sum_mod_two_from_quotient_sums h",
                "specialize gauss_count_sum_mod_two_from_quotient_sums k",
                "apply gauss_count_sum_mod_two_from_quotient_sums",
                "exact heq", "exact hfu", "exact hsum",
                "specialize qres_opposite_status_from_mod_four_three p",
                "specialize qres_opposite_status_from_mod_four_three q",
                "specialize qres_opposite_status_from_mod_four_three e",
                "specialize qres_opposite_status_from_mod_four_three f",
                "specialize qres_opposite_status_from_mod_four_three h",
                "specialize qres_opposite_status_from_mod_four_three k",
                "apply qres_opposite_status_from_mod_four_three",
                "exact hp", "exact hq", "exact heclass", "exact hfclass",
                "exact hcount", "exact hthree",
            ),
            "Conditional three-mod-four reciprocity: exactly one cross-residue proposition holds.",
        ),
    )


__all__ = ["make_quadratic_reciprocity_conditional_candidate_theorems"]
