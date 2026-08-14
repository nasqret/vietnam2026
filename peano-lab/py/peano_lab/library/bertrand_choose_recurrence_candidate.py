"""Constructive Pascal recurrence for the recurrence-defined Choose relation.

The first candidate exposes one successor-cell recurrence from a decoded
Pascal table.  The second compares that predecessor row with two independent
Choose packages and obtains the interior Pascal law.  Every helper expands to
ordinary first-order Peano arithmetic; this module creates no trusted
primitive, enrollment, or checked-use authority.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _beta_at_term,
    _binders,
    _choose_relation_term,
    _le_term,
    _lt_term,
    _pascal_table_prefix,
)
from peano_lab.library.bertrand_choose_laws_candidate import (
    _row_step_cell,
    _table_row_cell_term,
)


def _successor_cell_result_term(
    row_code_code: str,
    row_code_scale: str,
    row_scale_code: str,
    row_scale_scale: str,
    row_index_term: str,
    cell_index_term: str,
    value_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand the predecessor cells and sum returned by one table step."""

    previous_code, previous_scale, left_value, right_value = _binders(
        tag,
        variables,
        ("previous_code", "previous_scale", "left_value", "right_value"),
    )
    owned = variables + (
        previous_code,
        previous_scale,
        left_value,
        right_value,
    )
    previous_code_at = _beta_at_term(
        row_code_code,
        row_code_scale,
        row_index_term,
        previous_code,
        tag=f"{tag}_previous_code_at",
        variables=owned,
    )
    previous_scale_at = _beta_at_term(
        row_scale_code,
        row_scale_scale,
        row_index_term,
        previous_scale,
        tag=f"{tag}_previous_scale_at",
        variables=owned,
    )
    left_at = _beta_at_term(
        previous_code,
        previous_scale,
        cell_index_term,
        left_value,
        tag=f"{tag}_left_at",
        variables=owned,
    )
    right_at = _beta_at_term(
        previous_code,
        previous_scale,
        f"S ({cell_index_term})",
        right_value,
        tag=f"{tag}_right_at",
        variables=owned,
    )
    return (
        f"exists {previous_code} {previous_scale} {left_value} {right_value}. "
        f"({previous_code_at}) /\\ (({previous_scale_at}) /\\ "
        f"(({left_at}) /\\ (({right_at}) /\\ "
        f"{value_term} = {left_value} + {right_value})))"
    )


def _row_pointwise_agreement_term(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    left_width_term: str,
    right_width_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand row agreement while permitting term-valued widths."""

    index, left_value, right_value = _binders(
        tag,
        variables,
        ("index", "left_value", "right_value"),
    )
    owned = variables + (index, left_value, right_value)
    left_bound = _lt_term(
        index,
        left_width_term,
        tag=f"{tag}_left_bound",
        variables=owned,
    )
    right_bound = _lt_term(
        index,
        right_width_term,
        tag=f"{tag}_right_bound",
        variables=owned,
    )
    left_at = _beta_at_term(
        left_code,
        left_scale,
        index,
        left_value,
        tag=f"{tag}_left_at",
        variables=owned,
    )
    right_at = _beta_at_term(
        right_code,
        right_scale,
        index,
        right_value,
        tag=f"{tag}_right_at",
        variables=owned,
    )
    return (
        f"forall {index} {left_value} {right_value}. "
        f"({left_bound}) -> ({right_bound}) -> "
        f"({left_at}) -> ({right_at}) -> {left_value} = {right_value}"
    )


def make_bertrand_choose_recurrence_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the table-cell bridge and bounded Pascal recurrence."""

    table_variables = (
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "r",
        "i",
        "j",
        "b",
        "c",
        "z",
    )
    table = _pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptscr_table"
    )
    row_bound = _lt_term(
        "S i",
        "r",
        tag="bptscr_row_bound",
        variables=table_variables,
    )
    cell_bound = _lt_term(
        "S j",
        "w",
        tag="bptscr_cell_bound",
        variables=table_variables,
    )
    row_code_at = _beta_at_term(
        "bb",
        "bc",
        "S i",
        "b",
        tag="bptscr_row_code_at",
        variables=table_variables,
    )
    row_scale_at = _beta_at_term(
        "sb",
        "sc",
        "S i",
        "c",
        tag="bptscr_row_scale_at",
        variables=table_variables,
    )
    current_at = _beta_at_term(
        "b",
        "c",
        "S j",
        "z",
        tag="bptscr_current_at",
        variables=table_variables,
    )
    result = _successor_cell_result_term(
        "bb",
        "bc",
        "sb",
        "sc",
        "i",
        "j",
        "z",
        tag="bptscr_result",
        variables=table_variables,
    )

    table_branch_variables = table_variables + tuple(
        f"x{index}" if index else "x" for index in range(9)
    )
    semantic_row = _table_row_cell_term(
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "S i",
        tag="bptscr_semantic_row",
        variables=table_branch_variables,
    )
    semantic_current_at = _beta_at_term(
        "x",
        "x1",
        "S j",
        "z",
        tag="bptscr_semantic_current_at",
        variables=table_branch_variables,
    )
    previous_code_at = _beta_at_term(
        "bb",
        "bc",
        "i",
        "x3",
        tag="bptscr_previous_code_at",
        variables=table_branch_variables,
    )
    previous_scale_at = _beta_at_term(
        "sb",
        "sc",
        "i",
        "x4",
        tag="bptscr_previous_scale_at",
        variables=table_branch_variables,
    )
    semantic_cell = _row_step_cell(
        "x3",
        "x4",
        "x",
        "x1",
        "S j",
        tag="bptscr_semantic_cell",
        variables=table_branch_variables,
    )
    returned_left_at = _beta_at_term(
        "x3",
        "x4",
        "j",
        "x7",
        tag="bptscr_returned_left_at",
        variables=table_branch_variables,
    )
    returned_right_at = _beta_at_term(
        "x3",
        "x4",
        "S j",
        "x8",
        tag="bptscr_returned_right_at",
        variables=table_branch_variables,
    )

    row_payload = "hrow_witness_witness"
    row_kind = f"{row_payload}_right_right"
    zero_row = f"{row_kind}_left"
    successor_row = f"{row_kind}_right"
    successor_payload = f"{successor_row}_witness_witness_witness"
    step_relation = f"{successor_payload}_right_right_right"
    cell_boundary = "hcell_witness_right"
    cell_zero = f"{cell_boundary}_left"
    cell_step = f"{cell_boundary}_right"
    cell_payload = f"{cell_step}_witness_witness_witness"

    table_script = (
        "intro bb",
        "intro bc",
        "intro sb",
        "intro sc",
        "intro w",
        "intro r",
        "intro i",
        "intro j",
        "intro b",
        "intro c",
        "intro z",
        "intro htable",
        "intro hrow_bound",
        "intro hcell_bound",
        "intro hrow_code",
        "intro hrow_scale",
        "intro hcurrent",
        f"have hrow : {semantic_row}",
        "specialize htable (S i)",
        "apply htable",
        "exact hrow_bound",
        "cases hrow",
        "cases hrow_witness",
        f"cases {row_payload}",
        f"cases {row_payload}_right",
        "have hcode : b = x",
        "specialize beta_at_unique bb",
        "specialize beta_at_unique bc",
        "specialize beta_at_unique (S i)",
        "specialize beta_at_unique b",
        "specialize beta_at_unique x",
        "apply beta_at_unique",
        "exact hrow_code",
        f"exact {row_payload}_left",
        "have hscale : c = x1",
        "specialize beta_at_unique sb",
        "specialize beta_at_unique sc",
        "specialize beta_at_unique (S i)",
        "specialize beta_at_unique c",
        "specialize beta_at_unique x1",
        "apply beta_at_unique",
        "exact hrow_scale",
        f"exact {row_payload}_right_left",
        f"cases {row_kind}",
        f"cases {zero_row}",
        "exfalso",
        "specialize succ_ne_zero i",
        "apply succ_ne_zero",
        f"exact {zero_row}_left",
        f"cases {successor_row}",
        f"cases {successor_row}_witness",
        f"cases {successor_row}_witness_witness",
        f"cases {successor_payload}",
        f"cases {successor_payload}_right",
        f"cases {successor_payload}_right_right",
        "have hpredecessor : i = x2",
        "specialize succ_injective i",
        "specialize succ_injective x2",
        "apply succ_injective",
        f"exact {successor_payload}_left",
        f"have hprevious_code : {previous_code_at}",
        "rewrite hpredecessor",
        "rewrite hpredecessor",
        f"exact {successor_payload}_right_left",
        f"have hprevious_scale : {previous_scale_at}",
        "rewrite hpredecessor",
        "rewrite hpredecessor",
        f"exact {successor_payload}_right_right_left",
        f"have hsemantic_current : {semantic_current_at}",
        "rewrite <- hcode",
        "rewrite <- hscale",
        "rewrite <- hscale",
        "exact hcurrent",
        f"have hcell : {semantic_cell}",
        f"specialize {step_relation} (S j)",
        f"apply {step_relation}",
        "exact hcell_bound",
        "cases hcell",
        "cases hcell_witness",
        "have hvalue : z = x5",
        "specialize beta_at_unique x",
        "specialize beta_at_unique x1",
        "specialize beta_at_unique (S j)",
        "specialize beta_at_unique z",
        "specialize beta_at_unique x5",
        "apply beta_at_unique",
        "exact hsemantic_current",
        "exact hcell_witness_left",
        f"cases {cell_boundary}",
        f"cases {cell_zero}",
        "exfalso",
        "specialize succ_ne_zero j",
        "apply succ_ne_zero",
        f"exact {cell_zero}_left",
        f"cases {cell_step}",
        f"cases {cell_step}_witness",
        f"cases {cell_step}_witness_witness",
        f"cases {cell_payload}",
        f"cases {cell_payload}_right",
        f"cases {cell_payload}_right_right",
        "have hcell_predecessor : j = x6",
        "specialize succ_injective j",
        "specialize succ_injective x6",
        "apply succ_injective",
        f"exact {cell_payload}_left",
        f"have hleft : {returned_left_at}",
        "rewrite hcell_predecessor",
        "rewrite hcell_predecessor",
        f"exact {cell_payload}_right_left",
        f"have hright : {returned_right_at}",
        "rewrite hcell_predecessor",
        "rewrite hcell_predecessor",
        f"exact {cell_payload}_right_right_left",
        "exists x3",
        "exists x4",
        "exists x7",
        "exists x8",
        "split",
        "exact hprevious_code",
        "split",
        "exact hprevious_scale",
        "split",
        "exact hleft",
        "split",
        "exact hright",
        "trans x5",
        "exact hvalue",
        f"exact {cell_payload}_right_right_right",
    )

    choose_variables = ("n", "k", "x", "y", "z")
    choose_bound = _lt_term(
        "k", "n", tag="bcssol_bound", variables=choose_variables
    )
    left_choose = _choose_relation_term(
        "n", "k", "x", tag="bcssol_left", variables=choose_variables
    )
    right_choose = _choose_relation_term(
        "n", "S k", "y", tag="bcssol_right", variables=choose_variables
    )
    result_choose = _choose_relation_term(
        "S n",
        "S k",
        "z",
        tag="bcssol_result",
        variables=choose_variables,
    )

    proof_variables = choose_variables + tuple(
        f"x{index}" for index in range(1, 23)
    )
    left_le = _le_term(
        "k", "n", tag="bcssol_left_le", variables=proof_variables
    )
    target_range = _le_term(
        "S k",
        "S n",
        tag="bcssol_target_range",
        variables=proof_variables,
    )
    current_row_bound = _lt_term(
        "S n",
        "S (S n)",
        tag="bcssol_current_row_bound",
        variables=proof_variables,
    )
    current_cell_bound = _lt_term(
        "S k",
        "S (S n)",
        tag="bcssol_current_cell_bound",
        variables=proof_variables,
    )
    predecessor_row_bound = _lt_term(
        "n",
        "S (S n)",
        tag="bcssol_predecessor_row_bound",
        variables=proof_variables,
    )
    source_row_bound = _lt_term(
        "n",
        "S n",
        tag="bcssol_source_row_bound",
        variables=proof_variables,
    )
    result_left_bound = _lt_term(
        "k",
        "S (S n)",
        tag="bcssol_result_left_bound",
        variables=proof_variables,
    )
    source_left_bound = _lt_term(
        "k",
        "S n",
        tag="bcssol_source_left_bound",
        variables=proof_variables,
    )
    source_right_bound = _lt_term(
        "S k",
        "S n",
        tag="bcssol_source_right_bound",
        variables=proof_variables,
    )
    recurrence_result = _successor_cell_result_term(
        "x13",
        "x14",
        "x15",
        "x16",
        "n",
        "k",
        "z",
        tag="bcssol_recurrence_result",
        variables=proof_variables,
    )
    left_agreement = _row_pointwise_agreement_term(
        "x19",
        "x20",
        "x5",
        "x6",
        "S (S n)",
        "S n",
        tag="bcssol_left_agreement",
        variables=proof_variables,
    )
    right_agreement = _row_pointwise_agreement_term(
        "x19",
        "x20",
        "x11",
        "x12",
        "S (S n)",
        "S n",
        tag="bcssol_right_agreement",
        variables=proof_variables,
    )

    left_package = "hleft_right_right" + "_witness" * 6
    right_package = "hright_right_right" + "_witness" * 6
    target_package = "htarget_right_right" + "_witness" * 6
    recurrence_package = "hrecurrence" + "_witness" * 4

    choose_script = (
        "intro n",
        "intro k",
        "intro x",
        "intro y",
        "intro z",
        "intro hbound",
        "intro hleft",
        "intro hright",
        "intro htarget",
        "cases hleft",
        "cases hleft_left",
        "exfalso",
        f"have hleft_le : {left_le}",
        "specialize lt_to_le k",
        "specialize lt_to_le n",
        "apply lt_to_le",
        "exact hbound",
        "specialize lt_not_le n",
        "specialize lt_not_le k",
        "apply lt_not_le",
        "exact hleft_left_left",
        "exact hleft_le",
        "cases hleft_right",
        "cases hleft_right_right",
        "cases hleft_right_right_witness",
        "cases hleft_right_right_witness_witness",
        "cases hleft_right_right_witness_witness_witness",
        "cases hleft_right_right_witness_witness_witness_witness",
        "cases hleft_right_right_witness_witness_witness_witness_witness",
        f"cases {left_package}",
        f"cases {left_package}_right",
        f"cases {left_package}_right_right",
        "cases hright",
        "cases hright_left",
        "exfalso",
        "specialize lt_not_le n",
        "specialize lt_not_le (S k)",
        "apply lt_not_le",
        "exact hright_left_left",
        "exact hbound",
        "cases hright_right",
        "cases hright_right_right",
        "cases hright_right_right_witness",
        "cases hright_right_right_witness_witness",
        "cases hright_right_right_witness_witness_witness",
        "cases hright_right_right_witness_witness_witness_witness",
        "cases hright_right_right_witness_witness_witness_witness_witness",
        f"cases {right_package}",
        f"cases {right_package}_right",
        f"cases {right_package}_right_right",
        f"have htarget_range : {target_range}",
        "specialize le_succ (S k)",
        "specialize le_succ n",
        "apply le_succ",
        "exact hbound",
        "cases htarget",
        "cases htarget_left",
        "exfalso",
        "specialize lt_not_le (S n)",
        "specialize lt_not_le (S k)",
        "apply lt_not_le",
        "exact htarget_left_left",
        "exact htarget_range",
        "cases htarget_right",
        "cases htarget_right_right",
        "cases htarget_right_right_witness",
        "cases htarget_right_right_witness_witness",
        "cases htarget_right_right_witness_witness_witness",
        "cases htarget_right_right_witness_witness_witness_witness",
        "cases htarget_right_right_witness_witness_witness_witness_witness",
        f"cases {target_package}",
        f"cases {target_package}_right",
        f"cases {target_package}_right_right",
        f"have hcurrent_row_bound : {current_row_bound}",
        "specialize le_refl (S (S n))",
        "exact le_refl",
        f"have hcurrent_cell_bound : {current_cell_bound}",
        "specialize succ_le_succ (S k)",
        "specialize succ_le_succ (S n)",
        "apply succ_le_succ",
        "exact htarget_range",
        f"have hrecurrence : {recurrence_result}",
        "specialize beta_pascal_table_successor_cell_recurrence x13",
        "specialize beta_pascal_table_successor_cell_recurrence x14",
        "specialize beta_pascal_table_successor_cell_recurrence x15",
        "specialize beta_pascal_table_successor_cell_recurrence x16",
        "specialize beta_pascal_table_successor_cell_recurrence (S (S n))",
        "specialize beta_pascal_table_successor_cell_recurrence (S (S n))",
        "specialize beta_pascal_table_successor_cell_recurrence n",
        "specialize beta_pascal_table_successor_cell_recurrence k",
        "specialize beta_pascal_table_successor_cell_recurrence x17",
        "specialize beta_pascal_table_successor_cell_recurrence x18",
        "specialize beta_pascal_table_successor_cell_recurrence z",
        "apply beta_pascal_table_successor_cell_recurrence",
        f"exact {target_package}_left",
        "exact hcurrent_row_bound",
        "exact hcurrent_cell_bound",
        f"exact {target_package}_right_left",
        f"exact {target_package}_right_right_left",
        f"exact {target_package}_right_right_right",
        "cases hrecurrence",
        "cases hrecurrence_witness",
        "cases hrecurrence_witness_witness",
        "cases hrecurrence_witness_witness_witness",
        f"cases {recurrence_package}",
        f"cases {recurrence_package}_right",
        f"cases {recurrence_package}_right_right",
        f"cases {recurrence_package}_right_right_right",
        f"have hpredecessor_row_bound : {predecessor_row_bound}",
        "specialize le_succ (S n)",
        "specialize le_succ (S n)",
        "apply le_succ",
        "specialize le_refl (S n)",
        "exact le_refl",
        f"have hsource_row_bound : {source_row_bound}",
        "specialize le_refl (S n)",
        "exact le_refl",
        f"have hresult_left_bound : {result_left_bound}",
        "specialize le_succ (S k)",
        "specialize le_succ (S n)",
        "apply le_succ",
        "exact htarget_range",
        f"have hsource_left_bound : {source_left_bound}",
        "exact htarget_range",
        f"have hsource_right_bound : {source_right_bound}",
        "specialize succ_le_succ (S k)",
        "specialize succ_le_succ n",
        "apply succ_le_succ",
        "exact hbound",
        f"have hleft_agreement : {left_agreement}",
        "specialize beta_pascal_table_row_pointwise_functional x13",
        "specialize beta_pascal_table_row_pointwise_functional x14",
        "specialize beta_pascal_table_row_pointwise_functional x15",
        "specialize beta_pascal_table_row_pointwise_functional x16",
        "specialize beta_pascal_table_row_pointwise_functional (S (S n))",
        "specialize beta_pascal_table_row_pointwise_functional (S (S n))",
        "specialize beta_pascal_table_row_pointwise_functional x1",
        "specialize beta_pascal_table_row_pointwise_functional x2",
        "specialize beta_pascal_table_row_pointwise_functional x3",
        "specialize beta_pascal_table_row_pointwise_functional x4",
        "specialize beta_pascal_table_row_pointwise_functional (S n)",
        "specialize beta_pascal_table_row_pointwise_functional (S n)",
        "specialize beta_pascal_table_row_pointwise_functional n",
        "specialize beta_pascal_table_row_pointwise_functional x19",
        "specialize beta_pascal_table_row_pointwise_functional x20",
        "specialize beta_pascal_table_row_pointwise_functional x5",
        "specialize beta_pascal_table_row_pointwise_functional x6",
        "apply beta_pascal_table_row_pointwise_functional",
        f"exact {target_package}_left",
        f"exact {left_package}_left",
        "exact hpredecessor_row_bound",
        "exact hsource_row_bound",
        f"exact {recurrence_package}_left",
        f"exact {recurrence_package}_right_left",
        f"exact {left_package}_right_left",
        f"exact {left_package}_right_right_left",
        "have hleft_value : x21 = x",
        "specialize hleft_agreement k",
        "specialize hleft_agreement x21",
        "specialize hleft_agreement x",
        "apply hleft_agreement",
        "exact hresult_left_bound",
        "exact hsource_left_bound",
        f"exact {recurrence_package}_right_right_left",
        f"exact {left_package}_right_right_right",
        f"have hright_agreement : {right_agreement}",
        "specialize beta_pascal_table_row_pointwise_functional x13",
        "specialize beta_pascal_table_row_pointwise_functional x14",
        "specialize beta_pascal_table_row_pointwise_functional x15",
        "specialize beta_pascal_table_row_pointwise_functional x16",
        "specialize beta_pascal_table_row_pointwise_functional (S (S n))",
        "specialize beta_pascal_table_row_pointwise_functional (S (S n))",
        "specialize beta_pascal_table_row_pointwise_functional x7",
        "specialize beta_pascal_table_row_pointwise_functional x8",
        "specialize beta_pascal_table_row_pointwise_functional x9",
        "specialize beta_pascal_table_row_pointwise_functional x10",
        "specialize beta_pascal_table_row_pointwise_functional (S n)",
        "specialize beta_pascal_table_row_pointwise_functional (S n)",
        "specialize beta_pascal_table_row_pointwise_functional n",
        "specialize beta_pascal_table_row_pointwise_functional x19",
        "specialize beta_pascal_table_row_pointwise_functional x20",
        "specialize beta_pascal_table_row_pointwise_functional x11",
        "specialize beta_pascal_table_row_pointwise_functional x12",
        "apply beta_pascal_table_row_pointwise_functional",
        f"exact {target_package}_left",
        f"exact {right_package}_left",
        "exact hpredecessor_row_bound",
        "exact hsource_row_bound",
        f"exact {recurrence_package}_left",
        f"exact {recurrence_package}_right_left",
        f"exact {right_package}_right_left",
        f"exact {right_package}_right_right_left",
        "have hright_value : x22 = y",
        "specialize hright_agreement (S k)",
        "specialize hright_agreement x22",
        "specialize hright_agreement y",
        "apply hright_agreement",
        "exact hcurrent_cell_bound",
        "exact hsource_right_bound",
        f"exact {recurrence_package}_right_right_right_left",
        f"exact {right_package}_right_right_right",
        "trans x21 + x22",
        f"exact {recurrence_package}_right_right_right_right",
        "congr",
        "exact hleft_value",
        "exact hright_value",
    )

    return (
        spec(
            "beta_pascal_table_successor_cell_recurrence",
            "forall bb bc sb sc w r i j b c z. "
            f"({table}) -> ({row_bound}) -> ({cell_bound}) -> "
            f"({row_code_at}) -> ({row_scale_at}) -> ({current_at}) -> "
            f"({result})",
            ("beta_at_unique", "succ_ne_zero", "succ_injective"),
            table_script,
            "A decoded successor table cell is the sum of predecessor cells.",
        ),
        spec(
            "choose_succ_succ_of_lt",
            "forall n k x y z. "
            f"({choose_bound}) -> ({left_choose}) -> ({right_choose}) -> "
            f"({result_choose}) -> z = x + y",
            (
                "lt_not_le",
                "lt_to_le",
                "le_refl",
                "le_succ",
                "succ_le_succ",
                "beta_pascal_table_row_pointwise_functional",
                "beta_pascal_table_successor_cell_recurrence",
            ),
            choose_script,
            "Interior Choose values satisfy Pascal's successor recurrence.",
        ),
    )


__all__ = ["make_bertrand_choose_recurrence_candidate_theorems"]
