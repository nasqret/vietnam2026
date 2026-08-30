"""K3C constructor, elimination, and transport laws for list membership.

Membership is the conservative surface ``exists i. ListAt(code,i,value)``.
All theorem statements are fully expanded before parsing, and the bodies are
dependency-curried Alpha authoring evidence until a separate v2 enrollment
and empty-context closure gate is completed.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_cell_list_membership_surface_candidate import (
    cell_list_member,
    cell_list_valid,
)
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def _term_cell_list_len(code_term: str, term: str, *, tag: str) -> str:
    code_placeholder = f"hclistmember_code_argument_{tag}"
    length_placeholder = f"hclistmember_length_argument_{tag}"
    expanded = cell_list_len(code_placeholder, length_placeholder, tag=tag)
    if expanded.count(code_placeholder) == 0:
        raise ValueError("cell-list code placeholder disappeared")
    if expanded.count(length_placeholder) == 0:
        raise ValueError("cell-list length placeholder disappeared")
    return expanded.replace(code_placeholder, code_term).replace(
        length_placeholder, term
    )


def _term_cell_list_member(code_term: str, value: str, *, tag: str) -> str:
    placeholder = f"hclistmember_code_argument_{tag}"
    expanded = cell_list_member(placeholder, value, tag=tag)
    if expanded.count(placeholder) == 0:
        raise ValueError("cell-list code placeholder disappeared")
    return expanded.replace(placeholder, code_term)


def _term_list_at(
    code: str,
    index_term: str,
    value: str,
    *,
    tag: str,
) -> str:
    placeholder = f"hclistmember_index_argument_{tag}"
    expanded = cell_list_at(code, placeholder, value, tag=tag)
    if expanded.count(placeholder) == 0:
        raise ValueError("lookup index placeholder disappeared")
    return expanded.replace(placeholder, index_term)


def make_ha_cell_list_membership_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the first dependency-ordered K3C membership tranche."""

    nil_member = _term_cell_list_member("0", "a", tag="nil_source")
    nil_domain_length = _term_cell_list_len(
        "0", "l", tag="nil_domain_length"
    )
    nil_zero_length = _term_cell_list_len(
        "0", "0", tag="nil_zero_length"
    )

    exact_cell = cell("z", "h", "t")
    valid_tail = cell_list_valid("t", tag="head_intro_valid_tail")
    member_code_head = cell_list_member("z", "h", tag="head_intro_target")
    zero_head_lookup = _term_list_at("z", "0", "h", tag="head_intro_lookup")
    head_step = (
        f"exists t0 l0. (({cell('z', 'h', 't0')}) /\\ "
        f"({_term_cell_list_len('t0', 'l0', tag='head_intro_step_length')}))"
    )

    member_tail_source = cell_list_member("t", "a", tag="tail_intro_source")
    member_code_tail = cell_list_member("z", "a", tag="tail_intro_target")
    successor_lookup = _term_list_at(
        "z", "S x", "a", tag="tail_intro_successor_lookup"
    )
    successor_step = (
        f"exists t0 h0. (({cell('z', 'h0', 't0')}) /\\ "
        f"({_term_list_at('t0', 'x', 'a', tag='tail_intro_step_lookup')}))"
    )

    member_elim_source = cell_list_member("z", "a", tag="elim_source")
    member_elim_tail = cell_list_member("t", "a", tag="elim_tail_target")
    member_elim_result = f"a = h \\/ ({member_elim_tail})"
    member_elim_motive = (
        "forall i z h t a. "
        f"({cell('z', 'h', 't')}) -> "
        f"({_term_list_at('z', 'i', 'a', tag='elim_motive_lookup')}) -> "
        f"({member_elim_result})"
    )
    base_head = (
        f"exists t0 l0. (({cell('z', 'a', 't0')}) /\\ "
        f"({_term_cell_list_len('t0', 'l0', tag='elim_base_length')}))"
    )
    step_tail = (
        f"exists t0 h0. (({cell('z', 'h0', 't0')}) /\\ "
        f"({_term_list_at('t0', 'i', 'a', tag='elim_step_lookup')}))"
    )

    member_iff_source = cell_list_member("z", "a", tag="cell_iff_source")
    member_iff_tail = cell_list_member("t", "a", tag="cell_iff_tail")
    member_iff_target = cell_list_member("z", "a", tag="cell_iff_target")
    member_iff_disjunction = f"a = h \\/ ({member_iff_tail})"

    length_z = cell_list_len("z", "l", tag="transport_length_z")
    length_w = cell_list_len("w", "l", tag="transport_length_w")
    member_z = cell_list_member("z", "a", tag="transport_member_z")
    member_w = cell_list_member("w", "a", tag="transport_member_w")
    lookup_z = cell_list_at("z", "i", "x", tag="transport_lookup_z")
    lookup_w = cell_list_at("w", "i", "y", tag="transport_lookup_w")
    pointwise = (
        "forall i x y. (exists k. k + S i = l) -> "
        f"({lookup_z}) -> ({lookup_w}) -> x = y"
    )
    local_lookup_w = cell_list_at(
        "w", "x", "d", tag="transport_local_lookup_w"
    )

    member_domain_source = cell_list_member("z", "a", tag="domain_source")
    member_domain_target = cell_list_valid("z", tag="domain_target")

    return (
        spec(
            "list_member_implies_cell_list_valid",
            f"forall z a. ({member_domain_source}) -> ({member_domain_target})",
            ("list_at_implies_cell_list_valid",),
            (
                "intro z",
                "intro a",
                "intro hmember",
                "cases hmember",
                "specialize list_at_implies_cell_list_valid z",
                "specialize list_at_implies_cell_list_valid x",
                "specialize list_at_implies_cell_list_valid a",
                "apply list_at_implies_cell_list_valid",
                "exact hmember_witness",
            ),
            "Every list member carries a canonical cell-list validity witness.",
        ),
        spec(
            "list_member_nil_false",
            f"forall a. ({nil_member}) -> false",
            (
                "list_at_domain",
                "cell_list_zero_iff_nil",
                "cell_list_length_functional",
                "add_eq_zero_right",
                "succ_ne_zero",
            ),
            (
                "intro a",
                "intro hmember",
                "cases hmember",
                f"have hdomain : exists l. (({nil_domain_length}) /\\ "
                "exists k. k + S x = l)",
                "specialize list_at_domain 0",
                "specialize list_at_domain x",
                "specialize list_at_domain a",
                "apply list_at_domain",
                "exact hmember_witness",
                "cases hdomain",
                "cases hdomain_witness",
                "cases hdomain_witness_right",
                f"have hnil : {nil_zero_length}",
                "specialize cell_list_zero_iff_nil 0",
                "cases cell_list_zero_iff_nil",
                "apply cell_list_zero_iff_nil_right",
                "refl",
                "have hlength : x1 = 0",
                "specialize cell_list_length_functional 0",
                "specialize cell_list_length_functional x1",
                "specialize cell_list_length_functional 0",
                "apply cell_list_length_functional",
                "exact hdomain_witness_left",
                "exact hnil",
                "rewrite hlength at hdomain_witness_right_witness",
                "have hsucc : S x = 0",
                "specialize add_eq_zero_right x2",
                "specialize add_eq_zero_right (S x)",
                "apply add_eq_zero_right",
                "exact hdomain_witness_right_witness",
                "specialize succ_ne_zero x",
                "apply succ_ne_zero",
                "exact hsucc",
            ),
            "Nil has no represented list member.",
        ),
        spec(
            "list_member_cell_intro_head",
            "forall z h t. "
            f"({exact_cell}) -> ({valid_tail}) -> ({member_code_head})",
            ("list_at_head_iff",),
            (
                "intro z",
                "intro h",
                "intro t",
                "intro hcell",
                "intro hvalid",
                "cases hvalid",
                f"have hlookup : {zero_head_lookup}",
                "specialize list_at_head_iff z",
                "specialize list_at_head_iff h",
                "cases list_at_head_iff",
                "apply list_at_head_iff_right",
                "exists t",
                "exists x",
                "split",
                "exact hcell",
                "exact hvalid_witness",
                "exists 0",
                "exact hlookup",
            ),
            "The outer head of a cell over a valid tail is a member.",
        ),
        spec(
            "list_member_cell_intro_tail",
            "forall z h t a. "
            f"({exact_cell}) -> ({member_tail_source}) -> ({member_code_tail})",
            ("list_at_succ_iff",),
            (
                "intro z",
                "intro h",
                "intro t",
                "intro a",
                "intro hcell",
                "intro hmember",
                "cases hmember",
                f"have hlookup : {successor_lookup}",
                "specialize list_at_succ_iff z",
                "specialize list_at_succ_iff x",
                "specialize list_at_succ_iff a",
                "cases list_at_succ_iff",
                "apply list_at_succ_iff_right",
                "exists t",
                "exists h",
                "split",
                "exact hcell",
                "exact hmember_witness",
                "exists S x",
                "exact hlookup",
            ),
            "Every member of a tail remains a member after adjoining one head.",
        ),
        spec(
            "list_member_cell_elim",
            "forall z h t a. "
            f"({exact_cell}) -> ({member_elim_source}) -> "
            f"({member_elim_result})",
            ("list_at_head_iff", "list_at_succ_iff", "cell_functional"),
            (
                f"have helim : {member_elim_motive}",
                "intro i",
                "induction i",
                "intro z",
                "intro h",
                "intro t",
                "intro a",
                "intro hcell",
                "intro hlookup",
                f"have hhead : {base_head}",
                "specialize list_at_head_iff z",
                "specialize list_at_head_iff a",
                "cases list_at_head_iff",
                "apply list_at_head_iff_left",
                "exact hlookup",
                "cases hhead",
                "cases hhead_witness",
                "cases hhead_witness_witness",
                "have hcomponents : h = a /\\ t = x",
                "specialize cell_functional z",
                "specialize cell_functional h",
                "specialize cell_functional t",
                "specialize cell_functional a",
                "specialize cell_functional x",
                "apply cell_functional",
                "exact hcell",
                "exact hhead_witness_witness_left",
                "cases hcomponents",
                "left",
                "symm",
                "exact hcomponents_left",
                "intro z",
                "intro h",
                "intro t",
                "intro a",
                "intro hcell",
                "intro hlookup",
                f"have hstep : {step_tail}",
                "specialize list_at_succ_iff z",
                "specialize list_at_succ_iff i",
                "specialize list_at_succ_iff a",
                "cases list_at_succ_iff",
                "apply list_at_succ_iff_left",
                "exact hlookup",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                "have hcomponents : h = x1 /\\ t = x",
                "specialize cell_functional z",
                "specialize cell_functional h",
                "specialize cell_functional t",
                "specialize cell_functional x1",
                "specialize cell_functional x",
                "apply cell_functional",
                "exact hcell",
                "exact hstep_witness_witness_left",
                "cases hcomponents",
                "right",
                "rewrite hcomponents_right",
                "rewrite hcomponents_right",
                "exists i",
                "exact hstep_witness_witness_right",
                "intro z",
                "intro h",
                "intro t",
                "intro a",
                "intro hcell",
                "intro hmember",
                "cases hmember",
                "specialize helim x",
                "specialize helim z",
                "specialize helim h",
                "specialize helim t",
                "specialize helim a",
                "apply helim",
                "exact hcell",
                "exact hmember_witness",
            ),
            "A member of a nonempty cell list is its head or a member of its tail.",
        ),
        spec(
            "list_member_cell_iff",
            "forall z h t a. "
            f"({exact_cell}) -> ({valid_tail}) -> "
            f"((({member_iff_source}) -> ({member_iff_disjunction})) /\\ "
            f"(({member_iff_disjunction}) -> ({member_iff_target})))",
            (
                "list_member_cell_elim",
                "list_member_cell_intro_head",
                "list_member_cell_intro_tail",
            ),
            (
                "intro z",
                "intro h",
                "intro t",
                "intro a",
                "intro hcell",
                "intro hvalid",
                "split",
                "intro hmember",
                "specialize list_member_cell_elim z",
                "specialize list_member_cell_elim h",
                "specialize list_member_cell_elim t",
                "specialize list_member_cell_elim a",
                "apply list_member_cell_elim",
                "exact hcell",
                "exact hmember",
                "intro hcases",
                "cases hcases",
                "rewrite hcases_left",
                "rewrite hcases_left",
                "specialize list_member_cell_intro_head z",
                "specialize list_member_cell_intro_head h",
                "specialize list_member_cell_intro_head t",
                "apply list_member_cell_intro_head",
                "exact hcell",
                "exact hvalid",
                "specialize list_member_cell_intro_tail z",
                "specialize list_member_cell_intro_tail h",
                "specialize list_member_cell_intro_tail t",
                "specialize list_member_cell_intro_tail a",
                "apply list_member_cell_intro_tail",
                "exact hcell",
                "exact hcases_right",
            ),
            "Membership in a represented outer cell is head equality or tail membership.",
        ),
        spec(
            "list_member_pointwise_transport",
            "forall z w l a. "
            f"({length_z}) -> ({length_w}) -> ({pointwise}) -> "
            f"({member_z}) -> ({member_w})",
            ("list_at_external_bound", "list_at_exists"),
            (
                "intro z",
                "intro w",
                "intro l",
                "intro a",
                "intro hlength_z",
                "intro hlength_w",
                "intro hpointwise",
                "intro hmember",
                "cases hmember",
                "have hbound : exists k. k + S x = l",
                "specialize list_at_external_bound z",
                "specialize list_at_external_bound l",
                "specialize list_at_external_bound x",
                "specialize list_at_external_bound a",
                "apply list_at_external_bound",
                "exact hlength_z",
                "exact hmember_witness",
                f"have hwitness : exists d. ({local_lookup_w})",
                "specialize list_at_exists w",
                "specialize list_at_exists l",
                "specialize list_at_exists x",
                "apply list_at_exists",
                "exact hlength_w",
                "exact hbound",
                "cases hwitness",
                "have heq : a = x1",
                "specialize hpointwise x",
                "specialize hpointwise a",
                "specialize hpointwise x1",
                "apply hpointwise",
                "exact hbound",
                "exact hmember_witness",
                "exact hwitness_witness",
                "rewrite heq",
                "rewrite heq",
                "exists x",
                "exact hwitness_witness",
            ),
            "Pointwise-equal represented lists transport membership constructively.",
        ),
    )


__all__ = ["make_ha_cell_list_membership_candidate_theorems"]
