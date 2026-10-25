"""K3C constructor and case theorems for canonical cell-list validity.

The readable ``CellListValid`` surface expands before parsing.  These theorem
bodies are dependency-curried Alpha authoring evidence; enrollment and
empty-context closure are separate gates.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_cell_list_membership_surface_candidate import (
    cell_list_valid,
)
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def _term_cell_list_len(code: str, term: str, *, tag: str) -> str:
    placeholder = f"hclistvalid_length_argument_{tag}"
    expanded = cell_list_len(code, placeholder, tag=tag)
    if expanded.count(placeholder) == 0:
        raise ValueError("cell-list length placeholder disappeared")
    return expanded.replace(placeholder, term)


def make_ha_cell_list_validity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ready K3C validity tranche."""

    valid_zero = cell_list_valid("z0", tag="nil_target").replace("z0", "0")
    valid_tail_source = cell_list_valid("t", tag="cell_intro_tail_source")
    valid_code_target = cell_list_valid("z", tag="cell_intro_code_target")
    exact_cell_intro = cell("z", "h", "t")
    successor_length = _term_cell_list_len(
        "z", "S x", tag="cell_intro_successor_length"
    )

    valid_cases_source = cell_list_valid("z", tag="cases_source")
    valid_tail_target = cell_list_valid("t", tag="cases_tail_target")
    cases_result = (
        f"z = 0 \\/ exists h t. (({cell('z', 'h', 't')}) /\\ "
        f"({valid_tail_target}))"
    )
    cases_motive = (
        "forall l z. "
        f"({_term_cell_list_len('z', 'l', tag='cases_motive_length')}) -> "
        f"({cases_result})"
    )
    zero_length = _term_cell_list_len("z", "0", tag="cases_zero_length")
    successor_case_length = _term_cell_list_len(
        "z", "S l", tag="cases_successor_length"
    )
    predecessor_length = _term_cell_list_len(
        "t", "l", tag="cases_predecessor_length"
    )
    successor_decomposition = (
        f"exists t h. (({cell('z', 'h', 't')}) /\\ ({predecessor_length}))"
    )

    valid_cell_elim_source = cell_list_valid("z", tag="cell_elim_source")
    valid_cell_elim_target = cell_list_valid("t", tag="cell_elim_target")
    valid_cell_elim_cases = (
        f"z = 0 \\/ exists h2 t2. (({cell('z', 'h2', 't2')}) /\\ "
        f"({cell_list_valid('t2', tag='cell_elim_cases_tail')}))"
    )

    lookup = cell_list_at("z", "i", "a", tag="lookup_valid_source")
    lookup_valid_target = cell_list_valid("z", tag="lookup_valid_target")

    return (
        spec(
            "cell_list_valid_nil",
            valid_zero,
            ("cell_history_nil",),
            (
                "exists 0",
                "exists 0",
                "exists 0",
                "exact cell_history_nil",
            ),
            "Nil is a canonical valid cell list.",
        ),
        spec(
            "cell_list_valid_cell_intro",
            "forall z h t. "
            f"({exact_cell_intro}) -> ({valid_tail_source}) -> "
            f"({valid_code_target})",
            ("cell_list_succ_iff_cell",),
            (
                "intro z",
                "intro h",
                "intro t",
                "intro hcell",
                "intro htail",
                "cases htail",
                f"have hsuccessor : {successor_length}",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell x",
                "cases cell_list_succ_iff_cell",
                "apply cell_list_succ_iff_cell_right",
                "exists t",
                "exists h",
                "split",
                "exact hcell",
                "exact htail_witness",
                "exists S x",
                "exact hsuccessor",
            ),
            "Adjoining one exact D06 outer cell preserves cell-list validity.",
        ),
        spec(
            "cell_list_valid_cases",
            f"forall z. ({valid_cases_source}) -> ({cases_result})",
            ("cell_list_zero_iff_nil", "cell_list_succ_iff_cell"),
            (
                f"have hcases : {cases_motive}",
                "intro l",
                "induction l",
                "intro z",
                "intro hlength",
                "left",
                "specialize cell_list_zero_iff_nil z",
                "cases cell_list_zero_iff_nil",
                "apply cell_list_zero_iff_nil_left",
                "exact hlength",
                "intro z",
                "intro hlength",
                f"have hdecomp : {successor_decomposition}",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell l",
                "cases cell_list_succ_iff_cell",
                "apply cell_list_succ_iff_cell_left",
                "exact hlength",
                "right",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "exists x1",
                "exists x",
                "split",
                "exact hdecomp_witness_witness_left",
                "exists l",
                "exact hdecomp_witness_witness_right",
                "intro z",
                "intro hvalid",
                "cases hvalid",
                "specialize hcases x",
                "specialize hcases z",
                "apply hcases",
                "exact hvalid_witness",
            ),
            "Every valid cell list is nil or one exact outer cell over a valid tail.",
        ),
        spec(
            "cell_list_valid_cell_elim",
            "forall z h t. "
            f"({exact_cell_intro}) -> ({valid_cell_elim_source}) -> "
            f"({valid_cell_elim_target})",
            ("cell_list_valid_cases", "nil_not_cell", "cell_functional"),
            (
                "intro z",
                "intro h",
                "intro t",
                "intro hcell",
                "intro hvalid",
                f"have hcases : {valid_cell_elim_cases}",
                "specialize cell_list_valid_cases z",
                "apply cell_list_valid_cases",
                "exact hvalid",
                "cases hcases",
                "exfalso",
                "specialize nil_not_cell z",
                "specialize nil_not_cell h",
                "specialize nil_not_cell t",
                "apply nil_not_cell",
                "exact hcases_left",
                "exact hcell",
                "cases hcases_right",
                "cases hcases_right_witness",
                "cases hcases_right_witness_witness",
                "have hcomponents : h = x /\\ t = x1",
                "specialize cell_functional z",
                "specialize cell_functional h",
                "specialize cell_functional t",
                "specialize cell_functional x",
                "specialize cell_functional x1",
                "apply cell_functional",
                "exact hcell",
                "exact hcases_right_witness_witness_left",
                "cases hcomponents",
                "rewrite hcomponents_right",
                "rewrite hcomponents_right",
                "exact hcases_right_witness_witness_right",
            ),
            "A valid exact outer cell has a valid tail.",
        ),
        spec(
            "list_at_implies_cell_list_valid",
            f"forall z i a. ({lookup}) -> ({lookup_valid_target})",
            ("list_at_domain",),
            (
                "intro z",
                "intro i",
                "intro a",
                "intro hlookup",
                "have hdomain : exists l. "
                f"(({_term_cell_list_len('z', 'l', tag='lookup_domain_length')}) /\\ "
                "exists k. k + S i = l)",
                "specialize list_at_domain z",
                "specialize list_at_domain i",
                "specialize list_at_domain a",
                "apply list_at_domain",
                "exact hlookup",
                "cases hdomain",
                "cases hdomain_witness",
                "exists x",
                "exact hdomain_witness_left",
            ),
            "Every represented lookup certifies that its code is a valid cell list.",
        ),
    )


__all__ = ["make_ha_cell_list_validity_candidate_theorems"]
