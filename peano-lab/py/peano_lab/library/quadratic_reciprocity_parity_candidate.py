"""Constructive parity logic for the final reciprocity split.

Gauss's lemma classifies each cross-residue proposition by the parity of one
reflection count.  Eisenstein's argument supplies the parity of the sum of
the two counts.  This isolated layer connects those interfaces without using
classical propositional reasoning: an even count sum gives equal residue
status, an odd count sum gives opposite status, and the two modulo-four cases
determine the parity of the product of the odd halves.

All quadratic-residue, parity, congruence, and modulo-four relations expand
to ordinary first-order PA formula text.  Nothing is registered or admitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .quadratic_residue_surface import quadratic_residue


def _even(term: str, *, tag: str) -> str:
    return f"exists qrp_even_{tag}. {term} = 2 * qrp_even_{tag}"


def _odd(term: str, *, tag: str) -> str:
    return f"exists qrp_odd_{tag}. {term} = 2 * qrp_odd_{tag} + 1"


def _mod_two(left: str, right: str, *, tag: str) -> str:
    return (
        f"exists qrp_u_{tag} qrp_v_{tag}. "
        f"{left} + 2 * qrp_u_{tag} = {right} + 2 * qrp_v_{tag}"
    )


def _mod_four_one(term: str, *, tag: str) -> str:
    return f"exists qrp_one_{tag}. {term} = 4 * qrp_one_{tag} + 1"


def _mod_four_three(term: str, *, tag: str) -> str:
    return f"exists qrp_three_{tag}. {term} = 4 * qrp_three_{tag} + 3"


def _classification(
    proposition: str,
    count: str,
    *,
    tag: str,
) -> str:
    even = _even(count, tag=f"{tag}_even")
    odd = _odd(count, tag=f"{tag}_odd")
    return (
        f"(((({proposition}) -> ({even})) /\\ (({even}) -> ({proposition}))) /\\ "
        f"(((~({proposition})) -> ({odd})) /\\ (({odd}) -> ~({proposition}))))"
    )


def make_quadratic_reciprocity_parity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the count-parity and modulo-four reciprocity truth tables."""

    q_pq = quadratic_residue("p", "q", tag="qrp_pq")
    q_qp = quadratic_residue("q", "p", tag="qrp_qp")
    class_e = _classification(q_pq, "e", tag="e")
    class_f = _classification(q_qp, "f", tag="f")
    even_e = _even("e", tag="e_cases")
    odd_e = _odd("e", tag="e_cases")
    even_f = _even("f", tag="f_cases")
    odd_f = _odd("f", tag="f_cases")
    even_sum = _even("e + f", tag="count_sum")
    odd_sum = _odd("e + f", tag="count_sum")
    same_status = f"((({q_pq}) /\\ ({q_qp})) \\/ (~({q_pq}) /\\ ~({q_qp})))"
    opposite_status = f"((({q_pq}) /\\ ~({q_qp})) \\/ (~({q_pq}) /\\ ({q_qp})))"
    same_cases = (
        f"((({even_e}) /\\ ({even_f})) \\/ (({odd_e}) /\\ ({odd_f})))"
    )
    opposite_cases = (
        f"((({even_e}) /\\ ({odd_f})) \\/ (({odd_e}) /\\ ({even_f})))"
    )

    count_mod_product = _mod_two("e + f", "h * k", tag="count_product")
    even_product = _even("h * k", tag="half_product")
    odd_product = _odd("h * k", tag="half_product")
    even_count_transport = _even("e + f", tag="transport_count")
    even_product_transport = _even("h * k", tag="transport_product")
    odd_count_transport = _odd("e + f", tag="transport_count")
    odd_product_transport = _odd("h * k", tag="transport_product")
    even_transport_iff = (
        f"((({even_count_transport}) -> ({even_product_transport})) /\\ "
        f"(({even_product_transport}) -> ({even_count_transport})))"
    )
    odd_transport_iff = (
        f"((({odd_count_transport}) -> ({odd_product_transport})) /\\ "
        f"(({odd_product_transport}) -> ({odd_count_transport})))"
    )
    parity_transport = f"(({even_transport_iff}) /\\ ({odd_transport_iff}))"

    one_p = _mod_four_one("p", tag="p")
    one_q = _mod_four_one("q", tag="q")
    three_p = _mod_four_three("p", tag="p")
    three_q = _mod_four_three("q", tag="q")
    even_h = _even("h", tag="h")
    even_k = _even("k", tag="k")
    odd_h = _odd("h", tag="h")
    odd_k = _odd("k", tag="k")
    half_even_one_p = (
        f"((({even_h}) -> ({one_p})) /\\ (({one_p}) -> ({even_h})))"
    )
    half_even_one_q = (
        f"((({even_k}) -> ({one_q})) /\\ (({one_q}) -> ({even_k})))"
    )
    half_odd_three_p = (
        f"((({odd_h}) -> ({three_p})) /\\ (({three_p}) -> ({odd_h})))"
    )
    half_odd_three_q = (
        f"((({odd_k}) -> ({three_q})) /\\ (({three_q}) -> ({odd_k})))"
    )

    return (
        spec(
            "qres_same_status_from_even_count_sum",
            f"forall p q e f. ({class_e}) -> ({class_f}) -> "
            f"({even_sum}) -> ({same_status})",
            ("even_sum_parity_cases",),
            (
                "intro p", "intro q", "intro e", "intro f",
                "intro heclass", "intro hfclass", "intro hsum",
                "cases heclass", "cases heclass_left", "cases heclass_right",
                "cases hfclass", "cases hfclass_left", "cases hfclass_right",
                f"have hcases : {same_cases}",
                "specialize even_sum_parity_cases e",
                "specialize even_sum_parity_cases f",
                "apply even_sum_parity_cases", "exact hsum",
                "cases hcases",
                "cases hcases_left", "left", "split",
                "apply heclass_left_right", "exact hcases_left_left",
                "apply hfclass_left_right", "exact hcases_left_right",
                "cases hcases_right", "right", "split",
                "intro hpq", "apply heclass_right_right",
                "exact hcases_right_left", "exact hpq",
                "intro hqp", "apply hfclass_right_right",
                "exact hcases_right_right", "exact hqp",
            ),
            "An even sum of Gauss counts gives equal cross-residue status.",
        ),
        spec(
            "qres_opposite_status_from_odd_count_sum",
            f"forall p q e f. ({class_e}) -> ({class_f}) -> "
            f"({odd_sum}) -> ({opposite_status})",
            ("odd_sum_parity_cases",),
            (
                "intro p", "intro q", "intro e", "intro f",
                "intro heclass", "intro hfclass", "intro hsum",
                "cases heclass", "cases heclass_left", "cases heclass_right",
                "cases hfclass", "cases hfclass_left", "cases hfclass_right",
                f"have hcases : {opposite_cases}",
                "specialize odd_sum_parity_cases e",
                "specialize odd_sum_parity_cases f",
                "apply odd_sum_parity_cases", "exact hsum",
                "cases hcases",
                "cases hcases_left", "left", "split",
                "apply heclass_left_right", "exact hcases_left_left",
                "intro hqp", "apply hfclass_right_right",
                "exact hcases_left_right", "exact hqp",
                "cases hcases_right", "right", "split",
                "intro hpq", "apply heclass_right_right",
                "exact hcases_right_left", "exact hpq",
                "apply hfclass_left_right", "exact hcases_right_right",
            ),
            "An odd sum of Gauss counts gives opposite cross-residue status.",
        ),
        spec(
            "qres_same_status_from_even_half_product_mod_two",
            f"forall p q e f h k. ({class_e}) -> ({class_f}) -> "
            f"({count_mod_product}) -> ({even_product}) -> ({same_status})",
            (
                "mod_two_preserves_parity",
                "qres_same_status_from_even_count_sum",
            ),
            (
                "intro p", "intro q", "intro e", "intro f", "intro h", "intro k",
                "intro heclass", "intro hfclass", "intro hmod", "intro hproduct",
                f"have htransport : {parity_transport}",
                "specialize mod_two_preserves_parity (e + f)",
                "specialize mod_two_preserves_parity (h * k)",
                "apply mod_two_preserves_parity", "exact hmod",
                "cases htransport", "cases htransport_left",
                f"have hcount : {even_count_transport}",
                "apply htransport_left_right", "exact hproduct",
                "specialize qres_same_status_from_even_count_sum p",
                "specialize qres_same_status_from_even_count_sum q",
                "specialize qres_same_status_from_even_count_sum e",
                "specialize qres_same_status_from_even_count_sum f",
                "apply qres_same_status_from_even_count_sum",
                "exact heclass", "exact hfclass", "exact hcount",
            ),
            "Modulo-two equality with an even half product gives equal residue status.",
        ),
        spec(
            "qres_opposite_status_from_odd_half_product_mod_two",
            f"forall p q e f h k. ({class_e}) -> ({class_f}) -> "
            f"({count_mod_product}) -> ({odd_product}) -> ({opposite_status})",
            (
                "mod_two_preserves_parity",
                "qres_opposite_status_from_odd_count_sum",
            ),
            (
                "intro p", "intro q", "intro e", "intro f", "intro h", "intro k",
                "intro heclass", "intro hfclass", "intro hmod", "intro hproduct",
                f"have htransport : {parity_transport}",
                "specialize mod_two_preserves_parity (e + f)",
                "specialize mod_two_preserves_parity (h * k)",
                "apply mod_two_preserves_parity", "exact hmod",
                "cases htransport", "cases htransport_right",
                f"have hcount : {odd_count_transport}",
                "apply htransport_right_right", "exact hproduct",
                "specialize qres_opposite_status_from_odd_count_sum p",
                "specialize qres_opposite_status_from_odd_count_sum q",
                "specialize qres_opposite_status_from_odd_count_sum e",
                "specialize qres_opposite_status_from_odd_count_sum f",
                "apply qres_opposite_status_from_odd_count_sum",
                "exact heclass", "exact hfclass", "exact hcount",
            ),
            "Modulo-two equality with an odd half product gives opposite residue status.",
        ),
        spec(
            "qres_same_status_from_mod_four_one",
            f"forall p q e f h k. p = 2 * h + 1 -> q = 2 * k + 1 -> "
            f"({class_e}) -> ({class_f}) -> ({count_mod_product}) -> "
            f"(({one_p}) \\/ ({one_q})) -> ({same_status})",
            (
                "odd_half_even_iff_mod4_one",
                "even_mul_left",
                "even_mul_right",
                "qres_same_status_from_even_half_product_mod_two",
            ),
            (
                "intro p", "intro q", "intro e", "intro f", "intro h", "intro k",
                "intro hp", "intro hq", "intro heclass", "intro hfclass",
                "intro hmod", "intro hone", f"have hproduct : {even_product}",
                "cases hone",
                f"have hbridge : {half_even_one_p}",
                "specialize odd_half_even_iff_mod4_one p",
                "specialize odd_half_even_iff_mod4_one h",
                "apply odd_half_even_iff_mod4_one", "exact hp",
                "cases hbridge", f"have hhalf : {even_h}",
                "apply hbridge_right", "exact hone_left",
                "specialize even_mul_left h", "specialize even_mul_left k",
                "apply even_mul_left", "exact hhalf",
                f"have hbridge : {half_even_one_q}",
                "specialize odd_half_even_iff_mod4_one q",
                "specialize odd_half_even_iff_mod4_one k",
                "apply odd_half_even_iff_mod4_one", "exact hq",
                "cases hbridge", f"have hhalf : {even_k}",
                "apply hbridge_right", "exact hone_right",
                "specialize even_mul_right h", "specialize even_mul_right k",
                "apply even_mul_right", "exact hhalf",
                "specialize qres_same_status_from_even_half_product_mod_two p",
                "specialize qres_same_status_from_even_half_product_mod_two q",
                "specialize qres_same_status_from_even_half_product_mod_two e",
                "specialize qres_same_status_from_even_half_product_mod_two f",
                "specialize qres_same_status_from_even_half_product_mod_two h",
                "specialize qres_same_status_from_even_half_product_mod_two k",
                "apply qres_same_status_from_even_half_product_mod_two",
                "exact heclass", "exact hfclass", "exact hmod", "exact hproduct",
            ),
            "A one-mod-four input forces equal cross-residue status.",
        ),
        spec(
            "qres_opposite_status_from_mod_four_three",
            f"forall p q e f h k. p = 2 * h + 1 -> q = 2 * k + 1 -> "
            f"({class_e}) -> ({class_f}) -> ({count_mod_product}) -> "
            f"(({three_p}) /\\ ({three_q})) -> ({opposite_status})",
            (
                "odd_half_odd_iff_mod4_three",
                "odd_mul_odd",
                "qres_opposite_status_from_odd_half_product_mod_two",
            ),
            (
                "intro p", "intro q", "intro e", "intro f", "intro h", "intro k",
                "intro hp", "intro hq", "intro heclass", "intro hfclass",
                "intro hmod", "intro hthree", "cases hthree",
                f"have hpbridge : {half_odd_three_p}",
                "specialize odd_half_odd_iff_mod4_three p",
                "specialize odd_half_odd_iff_mod4_three h",
                "apply odd_half_odd_iff_mod4_three", "exact hp",
                "cases hpbridge", f"have hpodd : {odd_h}",
                "apply hpbridge_right", "exact hthree_left",
                f"have hqbridge : {half_odd_three_q}",
                "specialize odd_half_odd_iff_mod4_three q",
                "specialize odd_half_odd_iff_mod4_three k",
                "apply odd_half_odd_iff_mod4_three", "exact hq",
                "cases hqbridge", f"have hqodd : {odd_k}",
                "apply hqbridge_right", "exact hthree_right",
                f"have hproduct : {odd_product}",
                "specialize odd_mul_odd h", "specialize odd_mul_odd k",
                "apply odd_mul_odd", "exact hpodd", "exact hqodd",
                "specialize qres_opposite_status_from_odd_half_product_mod_two p",
                "specialize qres_opposite_status_from_odd_half_product_mod_two q",
                "specialize qres_opposite_status_from_odd_half_product_mod_two e",
                "specialize qres_opposite_status_from_odd_half_product_mod_two f",
                "specialize qres_opposite_status_from_odd_half_product_mod_two h",
                "specialize qres_opposite_status_from_odd_half_product_mod_two k",
                "apply qres_opposite_status_from_odd_half_product_mod_two",
                "exact heclass", "exact hfclass", "exact hmod", "exact hproduct",
            ),
            "Two three-mod-four inputs force opposite cross-residue status.",
        ),
    )


__all__ = ["make_quadratic_reciprocity_parity_candidate_theorems"]
