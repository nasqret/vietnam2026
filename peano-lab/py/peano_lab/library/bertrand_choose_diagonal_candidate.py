"""Fused diagonal boundary semantics and the relational Choose self law.

The first candidate proves, in one induction over a decoded Pascal-table row,
that its diagonal entry is one and every in-width entry above the diagonal is
zero.  The second candidate projects the diagonal component from the table
package embedded in ``Choose(n,n,z)``.  All notation expands to ordinary
first-order Peano arithmetic; this module creates no trusted primitive,
authority enrollment, or checked-use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _beta_at_term,
    _binders,
    _choose_relation,
    _lt_term,
    _pascal_table_prefix,
)
from peano_lab.library.bertrand_choose_laws_candidate import (
    _row_step_cell,
    _table_row_cell_term,
    _zero_row_cell,
)


def _diagonal_boundary_term(
    code: str,
    scale: str,
    width_term: str,
    row_index_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand diagonal-one and above-diagonal-zero for one finite row."""

    diagonal_value, above_index, above_value = _binders(
        tag,
        variables,
        ("diagonal_value", "above_index", "above_value"),
    )
    owned = variables + (diagonal_value, above_index, above_value)
    diagonal_bound = _lt_term(
        row_index_term,
        width_term,
        tag=f"{tag}_diagonal_bound",
        variables=owned,
    )
    diagonal_at = _beta_at_term(
        code,
        scale,
        row_index_term,
        diagonal_value,
        tag=f"{tag}_diagonal_at",
        variables=owned,
    )
    above_order = _lt_term(
        row_index_term,
        above_index,
        tag=f"{tag}_above_order",
        variables=owned,
    )
    above_bound = _lt_term(
        above_index,
        width_term,
        tag=f"{tag}_above_bound",
        variables=owned,
    )
    above_at = _beta_at_term(
        code,
        scale,
        above_index,
        above_value,
        tag=f"{tag}_above_at",
        variables=owned,
    )
    return (
        f"((({diagonal_bound}) -> forall {diagonal_value}. "
        f"({diagonal_at}) -> {diagonal_value} = 1) /\\ "
        f"forall {above_index} {above_value}. "
        f"({above_order}) -> ({above_bound}) -> "
        f"({above_at}) -> {above_value} = 0)"
    )


def _row_boundary_family(
    outer_code: str,
    outer_scale: str,
    outer_scale_code: str,
    outer_scale_scale: str,
    width_term: str,
    row_index_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand the IH family after its row-bound premise is discharged."""

    row_code, row_scale = _binders(
        tag,
        variables,
        ("row_code", "row_scale"),
    )
    family_variables = variables + (row_code, row_scale)
    code_at = _beta_at_term(
        outer_code,
        outer_scale,
        row_index_term,
        row_code,
        tag=f"{tag}_code_at",
        variables=family_variables,
    )
    scale_at = _beta_at_term(
        outer_scale_code,
        outer_scale_scale,
        row_index_term,
        row_scale,
        tag=f"{tag}_scale_at",
        variables=family_variables,
    )
    boundary = _diagonal_boundary_term(
        row_code,
        row_scale,
        width_term,
        row_index_term,
        tag=f"{tag}_boundary",
        variables=family_variables,
    )
    return (
        f"forall {row_code} {row_scale}. "
        f"({code_at}) -> ({scale_at}) -> ({boundary})"
    )


def make_bertrand_choose_diagonal_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered fused boundary and Choose-self rows."""

    surface_variables = (
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "r",
        "i",
        "b",
        "c",
        "j",
        "z",
    )
    table = _pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptdb_table"
    )
    row_bound = _lt_term(
        "i",
        "r",
        tag="bptdb_row_bound",
        variables=surface_variables,
    )
    row_code_at = _beta_at_term(
        "bb",
        "bc",
        "i",
        "b",
        tag="bptdb_row_code_at",
        variables=surface_variables,
    )
    row_scale_at = _beta_at_term(
        "sb",
        "sc",
        "i",
        "c",
        tag="bptdb_row_scale_at",
        variables=surface_variables,
    )
    boundary = _diagonal_boundary_term(
        "b",
        "c",
        "w",
        "i",
        tag="bptdb_boundary",
        variables=surface_variables,
    )

    base_variables = surface_variables + ("x", "x1", "x2", "x3", "x4")
    base_row = _table_row_cell_term(
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "0",
        tag="bptdb_base_row",
        variables=base_variables,
    )
    base_diagonal_semantic_at = _beta_at_term(
        "x",
        "x1",
        "0",
        "z",
        tag="bptdb_base_diagonal_semantic",
        variables=base_variables,
    )
    base_diagonal_cell = _zero_row_cell(
        "x",
        "x1",
        "0",
        tag="bptdb_base_diagonal_cell",
        variables=base_variables,
    )
    base_above_semantic_at = _beta_at_term(
        "x",
        "x1",
        "j",
        "z",
        tag="bptdb_base_above_semantic",
        variables=base_variables,
    )
    base_above_cell = _zero_row_cell(
        "x",
        "x1",
        "j",
        tag="bptdb_base_above_cell",
        variables=base_variables,
    )

    step_variables = surface_variables + (
        "x",
        "x1",
        "x2",
        "x3",
        "x4",
        "x5",
        "x6",
        "x7",
        "x8",
    )
    step_row = _table_row_cell_term(
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "S i",
        tag="bptdb_step_row",
        variables=step_variables,
    )
    previous_row_bound = _lt_term(
        "i",
        "r",
        tag="bptdb_previous_row_bound",
        variables=step_variables,
    )
    previous_code_at = _beta_at_term(
        "bb",
        "bc",
        "i",
        "x3",
        tag="bptdb_previous_code_at",
        variables=step_variables,
    )
    previous_scale_at = _beta_at_term(
        "sb",
        "sc",
        "i",
        "x4",
        tag="bptdb_previous_scale_at",
        variables=step_variables,
    )
    previous_family = _row_boundary_family(
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "i",
        tag="bptdb_previous_family",
        variables=step_variables,
    )
    previous_boundary = _diagonal_boundary_term(
        "x3",
        "x4",
        "w",
        "i",
        tag="bptdb_previous_boundary",
        variables=step_variables,
    )
    step_diagonal_semantic_at = _beta_at_term(
        "x",
        "x1",
        "S i",
        "z",
        tag="bptdb_step_diagonal_semantic",
        variables=step_variables,
    )
    step_diagonal_cell = _row_step_cell(
        "x3",
        "x4",
        "x",
        "x1",
        "S i",
        tag="bptdb_step_diagonal_cell",
        variables=step_variables,
    )
    previous_diagonal_bound = _lt_term(
        "i",
        "w",
        tag="bptdb_previous_diagonal_bound",
        variables=step_variables,
    )
    previous_diagonal_family_at = _beta_at_term(
        "x3",
        "x4",
        "i",
        "z",
        tag="bptdb_previous_diagonal_family",
        variables=step_variables,
    )
    strict_successor = _lt_term(
        "i",
        "S i",
        tag="bptdb_strict_successor",
        variables=step_variables,
    )
    step_previous_left_at = _beta_at_term(
        "x3",
        "x4",
        "i",
        "x7",
        tag="bptdb_step_previous_left",
        variables=step_variables,
    )
    step_previous_right_at = _beta_at_term(
        "x3",
        "x4",
        "S i",
        "x8",
        tag="bptdb_step_previous_right",
        variables=step_variables,
    )
    step_above_semantic_at = _beta_at_term(
        "x",
        "x1",
        "j",
        "z",
        tag="bptdb_step_above_semantic",
        variables=step_variables,
    )
    step_above_cell = _row_step_cell(
        "x3",
        "x4",
        "x",
        "x1",
        "j",
        tag="bptdb_step_above_cell",
        variables=step_variables,
    )
    shifted_above_order = _lt_term(
        "S i",
        "S x6",
        tag="bptdb_shifted_above_order",
        variables=step_variables,
    )
    previous_left_order = _lt_term(
        "i",
        "x6",
        tag="bptdb_previous_left_order",
        variables=step_variables,
    )
    previous_right_order = _lt_term(
        "i",
        "S x6",
        tag="bptdb_previous_right_order",
        variables=step_variables,
    )
    previous_left_bound = _lt_term(
        "x6",
        "w",
        tag="bptdb_previous_left_bound",
        variables=step_variables,
    )
    previous_right_bound = _lt_term(
        "S x6",
        "w",
        tag="bptdb_previous_right_bound",
        variables=step_variables,
    )
    above_previous_left_at = _beta_at_term(
        "x3",
        "x4",
        "x6",
        "x7",
        tag="bptdb_above_previous_left",
        variables=step_variables,
    )
    above_previous_right_at = _beta_at_term(
        "x3",
        "x4",
        "S x6",
        "x8",
        tag="bptdb_above_previous_right",
        variables=step_variables,
    )

    row_payload = "hrow_witness_witness"
    row_kind = f"{row_payload}_right_right"
    zero_kind = f"{row_kind}_left"
    successor_kind = f"{row_kind}_right"
    successor_payload = f"{successor_kind}_witness_witness_witness"
    step_relation = f"{successor_payload}_right_right_right"
    cell_boundary = "hcell_witness_right"
    cell_zero = f"{cell_boundary}_left"
    cell_recurrence = f"{cell_boundary}_right"
    cell_recurrence_payload = f"{cell_recurrence}_witness_witness_witness"

    boundary_script = (
        "intro bb",
        "intro bc",
        "intro sb",
        "intro sc",
        "intro w",
        "intro r",
        "intro htable",
        "intro i",
        "induction i",
        "intro hir",
        "intro b",
        "intro c",
        "intro hbb",
        "intro hsb",
        f"have hrow : {base_row}",
        "specialize htable 0",
        "apply htable",
        "exact hir",
        "cases hrow",
        "cases hrow_witness",
        f"cases {row_payload}",
        f"cases {row_payload}_right",
        "have hcode : b = x",
        "specialize beta_at_unique bb",
        "specialize beta_at_unique bc",
        "specialize beta_at_unique 0",
        "specialize beta_at_unique b",
        "specialize beta_at_unique x",
        "apply beta_at_unique",
        "exact hbb",
        f"exact {row_payload}_left",
        "have hscale : c = x1",
        "specialize beta_at_unique sb",
        "specialize beta_at_unique sc",
        "specialize beta_at_unique 0",
        "specialize beta_at_unique c",
        "specialize beta_at_unique x1",
        "apply beta_at_unique",
        "exact hsb",
        f"exact {row_payload}_right_left",
        f"cases {row_kind}",
        f"cases {zero_kind}",
        "split",
        "intro hiw",
        "intro z",
        "intro htarget",
        f"have hsemantic : {base_diagonal_semantic_at}",
        "rewrite <- hcode",
        "rewrite <- hscale",
        "rewrite <- hscale",
        "exact htarget",
        f"have hcell : {base_diagonal_cell}",
        f"specialize {zero_kind}_right 0",
        f"apply {zero_kind}_right",
        "exact hiw",
        "cases hcell",
        "cases hcell_witness",
        "have hvalue : z = x2",
        "specialize beta_at_unique x",
        "specialize beta_at_unique x1",
        "specialize beta_at_unique 0",
        "specialize beta_at_unique z",
        "specialize beta_at_unique x2",
        "apply beta_at_unique",
        "exact hsemantic",
        "exact hcell_witness_left",
        f"cases {cell_boundary}",
        f"cases {cell_zero}",
        "trans x2",
        "exact hvalue",
        f"exact {cell_zero}_right",
        f"cases {cell_recurrence}",
        f"cases {cell_recurrence}_witness",
        "exfalso",
        "have hbad : S x3 = 0",
        "symm",
        f"exact {cell_recurrence}_witness_left",
        "specialize succ_ne_zero x3",
        "apply succ_ne_zero",
        "exact hbad",
        "intro j",
        "intro z",
        "intro hij",
        "intro hjw",
        "intro htarget",
        f"have hsemantic : {base_above_semantic_at}",
        "rewrite <- hcode",
        "rewrite <- hscale",
        "rewrite <- hscale",
        "exact htarget",
        f"have hcell : {base_above_cell}",
        f"specialize {zero_kind}_right j",
        f"apply {zero_kind}_right",
        "exact hjw",
        "cases hcell",
        "cases hcell_witness",
        "have hvalue : z = x2",
        "specialize beta_at_unique x",
        "specialize beta_at_unique x1",
        "specialize beta_at_unique j",
        "specialize beta_at_unique z",
        "specialize beta_at_unique x2",
        "apply beta_at_unique",
        "exact hsemantic",
        "exact hcell_witness_left",
        f"cases {cell_boundary}",
        f"cases {cell_zero}",
        "cases hij",
        "have hbad : S 0 = 0",
        "specialize add_eq_zero_right x3",
        "specialize add_eq_zero_right (S 0)",
        "apply add_eq_zero_right",
        "trans j",
        "exact hij_witness",
        f"exact {cell_zero}_left",
        "exfalso",
        "specialize succ_ne_zero 0",
        "apply succ_ne_zero",
        "exact hbad",
        f"cases {cell_recurrence}",
        f"cases {cell_recurrence}_witness",
        "trans x2",
        "exact hvalue",
        f"exact {cell_recurrence}_witness_right",
        f"cases {successor_kind}",
        f"cases {successor_kind}_witness",
        f"cases {successor_kind}_witness_witness",
        f"cases {successor_payload}",
        "exfalso",
        "have hbad : S x2 = 0",
        "symm",
        f"exact {successor_payload}_left",
        "specialize succ_ne_zero x2",
        "apply succ_ne_zero",
        "exact hbad",
        "intro hir",
        "intro b",
        "intro c",
        "intro hbb",
        "intro hsb",
        f"have hrow : {step_row}",
        "specialize htable (S i)",
        "apply htable",
        "exact hir",
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
        "exact hbb",
        f"exact {row_payload}_left",
        "have hscale : c = x1",
        "specialize beta_at_unique sb",
        "specialize beta_at_unique sc",
        "specialize beta_at_unique (S i)",
        "specialize beta_at_unique c",
        "specialize beta_at_unique x1",
        "apply beta_at_unique",
        "exact hsb",
        f"exact {row_payload}_right_left",
        f"cases {row_kind}",
        f"cases {zero_kind}",
        "exfalso",
        "specialize succ_ne_zero i",
        "apply succ_ne_zero",
        f"exact {zero_kind}_left",
        f"cases {successor_kind}",
        f"cases {successor_kind}_witness",
        f"cases {successor_kind}_witness_witness",
        f"cases {successor_payload}",
        f"cases {successor_payload}_right",
        f"cases {successor_payload}_right_right",
        "have hpredecessor : i = x2",
        "specialize succ_injective i",
        "specialize succ_injective x2",
        "apply succ_injective",
        f"exact {successor_payload}_left",
        f"have hprevious_row_bound : {previous_row_bound}",
        "specialize lt_to_le (S i)",
        "specialize lt_to_le r",
        "apply lt_to_le",
        "exact hir",
        f"have hprevious_code : {previous_code_at}",
        "rewrite hpredecessor",
        "rewrite hpredecessor",
        f"exact {successor_payload}_right_left",
        f"have hprevious_scale : {previous_scale_at}",
        "rewrite hpredecessor",
        "rewrite hpredecessor",
        f"exact {successor_payload}_right_right_left",
        f"have hprevious_family : {previous_family}",
        "apply IH",
        "exact hprevious_row_bound",
        f"have hprevious_boundary : {previous_boundary}",
        "specialize hprevious_family x3",
        "specialize hprevious_family x4",
        "apply hprevious_family",
        "exact hprevious_code",
        "exact hprevious_scale",
        "cases hprevious_boundary",
        "split",
        "intro hiw",
        "intro z",
        "intro htarget",
        f"have hsemantic : {step_diagonal_semantic_at}",
        "rewrite <- hcode",
        "rewrite <- hscale",
        "rewrite <- hscale",
        "exact htarget",
        f"have hcell : {step_diagonal_cell}",
        f"specialize {step_relation} (S i)",
        f"apply {step_relation}",
        "exact hiw",
        "cases hcell",
        "cases hcell_witness",
        "have hvalue : z = x5",
        "specialize beta_at_unique x",
        "specialize beta_at_unique x1",
        "specialize beta_at_unique (S i)",
        "specialize beta_at_unique z",
        "specialize beta_at_unique x5",
        "apply beta_at_unique",
        "exact hsemantic",
        "exact hcell_witness_left",
        f"cases {cell_boundary}",
        f"cases {cell_zero}",
        "exfalso",
        "specialize succ_ne_zero i",
        "apply succ_ne_zero",
        f"exact {cell_zero}_left",
        f"cases {cell_recurrence}",
        f"cases {cell_recurrence}_witness",
        f"cases {cell_recurrence}_witness_witness",
        f"cases {cell_recurrence_payload}",
        f"cases {cell_recurrence_payload}_right",
        f"cases {cell_recurrence_payload}_right_right",
        "have hcell_predecessor : i = x6",
        "specialize succ_injective i",
        "specialize succ_injective x6",
        "apply succ_injective",
        f"exact {cell_recurrence_payload}_left",
        f"have hleft_at : {step_previous_left_at}",
        "rewrite hcell_predecessor",
        "rewrite hcell_predecessor",
        f"exact {cell_recurrence_payload}_right_left",
        f"have hright_at : {step_previous_right_at}",
        "rewrite hcell_predecessor",
        "rewrite hcell_predecessor",
        f"exact {cell_recurrence_payload}_right_right_left",
        f"have hprevious_diagonal_bound : {previous_diagonal_bound}",
        "specialize lt_to_le (S i)",
        "specialize lt_to_le w",
        "apply lt_to_le",
        "exact hiw",
        "have hdiagonal_family : forall z. "
        f"({previous_diagonal_family_at}) "
        "-> z = 1",
        "apply hprevious_boundary_left",
        "exact hprevious_diagonal_bound",
        "have hleft_one : x7 = 1",
        "specialize hdiagonal_family x7",
        "apply hdiagonal_family",
        "exact hleft_at",
        f"have hstrict_successor : {strict_successor}",
        "specialize le_refl (S i)",
        "exact le_refl",
        "have hright_zero : x8 = 0",
        "specialize hprevious_boundary_right (S i)",
        "specialize hprevious_boundary_right x8",
        "apply hprevious_boundary_right",
        "exact hstrict_successor",
        "exact hiw",
        "exact hright_at",
        "trans x5",
        "exact hvalue",
        f"rewrite {cell_recurrence_payload}_right_right_right",
        "simp [hleft_one, hright_zero]",
        "intro j",
        "intro z",
        "intro hij",
        "intro hjw",
        "intro htarget",
        f"have hsemantic : {step_above_semantic_at}",
        "rewrite <- hcode",
        "rewrite <- hscale",
        "rewrite <- hscale",
        "exact htarget",
        f"have hcell : {step_above_cell}",
        f"specialize {step_relation} j",
        f"apply {step_relation}",
        "exact hjw",
        "cases hcell",
        "cases hcell_witness",
        "have hvalue : z = x5",
        "specialize beta_at_unique x",
        "specialize beta_at_unique x1",
        "specialize beta_at_unique j",
        "specialize beta_at_unique z",
        "specialize beta_at_unique x5",
        "apply beta_at_unique",
        "exact hsemantic",
        "exact hcell_witness_left",
        f"cases {cell_boundary}",
        f"cases {cell_zero}",
        "cases hij",
        "have hbad : S (S i) = 0",
        "specialize add_eq_zero_right x6",
        "specialize add_eq_zero_right (S (S i))",
        "apply add_eq_zero_right",
        "trans j",
        "exact hij_witness",
        f"exact {cell_zero}_left",
        "exfalso",
        "specialize succ_ne_zero (S i)",
        "apply succ_ne_zero",
        "exact hbad",
        f"cases {cell_recurrence}",
        f"cases {cell_recurrence}_witness",
        f"cases {cell_recurrence}_witness_witness",
        f"cases {cell_recurrence_payload}",
        f"cases {cell_recurrence_payload}_right",
        f"cases {cell_recurrence_payload}_right_right",
        f"have hshifted_order : {shifted_above_order}",
        "rewrite <- hcell_witness_right_right_witness_witness_witness_left",
        "exact hij",
        f"have hprevious_left_order : {previous_left_order}",
        "specialize le_of_succ_le_succ (S i)",
        "specialize le_of_succ_le_succ x6",
        "apply le_of_succ_le_succ",
        "exact hshifted_order",
        f"have hprevious_right_order : {previous_right_order}",
        "specialize lt_to_le (S i)",
        "specialize lt_to_le (S x6)",
        "apply lt_to_le",
        "exact hshifted_order",
        f"have hprevious_right_bound : {previous_right_bound}",
        "rewrite <- hcell_witness_right_right_witness_witness_witness_left",
        "exact hjw",
        f"have hprevious_left_bound : {previous_left_bound}",
        "specialize lt_to_le (S x6)",
        "specialize lt_to_le w",
        "apply lt_to_le",
        "exact hprevious_right_bound",
        f"have hleft_at : {above_previous_left_at}",
        f"exact {cell_recurrence_payload}_right_left",
        f"have hright_at : {above_previous_right_at}",
        f"exact {cell_recurrence_payload}_right_right_left",
        "have hleft_zero : x7 = 0",
        "specialize hprevious_boundary_right x6",
        "specialize hprevious_boundary_right x7",
        "apply hprevious_boundary_right",
        "exact hprevious_left_order",
        "exact hprevious_left_bound",
        "exact hleft_at",
        "have hright_zero : x8 = 0",
        "specialize hprevious_boundary_right (S x6)",
        "specialize hprevious_boundary_right x8",
        "apply hprevious_boundary_right",
        "exact hprevious_right_order",
        "exact hprevious_right_bound",
        "exact hright_at",
        "trans x5",
        "exact hvalue",
        f"rewrite {cell_recurrence_payload}_right_right_right",
        "simp [hleft_zero, hright_zero]",
    )

    choose = _choose_relation("n", "n", "z", tag="bcs_choose")
    choose_variables = (
        "n",
        "z",
        "x",
        "x1",
        "x2",
        "x3",
        "x4",
        "x5",
    )
    (choose_family_index,) = _binders(
        "bcs_table_family",
        choose_variables,
        ("row_index",),
    )
    choose_family_variables = choose_variables + (choose_family_index,)
    choose_family_bound = _lt_term(
        choose_family_index,
        "S n",
        tag="bcs_table_family_bound",
        variables=choose_family_variables,
    )
    choose_table_rows = _row_boundary_family(
        "x",
        "x1",
        "x2",
        "x3",
        "S n",
        choose_family_index,
        tag="bcs_table_family_rows",
        variables=choose_family_variables,
    )
    choose_table_family = (
        f"forall {choose_family_index}. ({choose_family_bound}) -> "
        f"({choose_table_rows})"
    )
    choose_bound = _lt_term(
        "n",
        "S n",
        tag="bcs_row_bound",
        variables=choose_variables,
    )
    choose_boundary = _diagonal_boundary_term(
        "x4",
        "x5",
        "S n",
        "n",
        tag="bcs_boundary",
        variables=choose_variables,
    )
    choose_row_family = _row_boundary_family(
        "x",
        "x1",
        "x2",
        "x3",
        "S n",
        "n",
        tag="bcs_row_family",
        variables=choose_variables,
    )
    choose_diagonal_family_at = _beta_at_term(
        "x4",
        "x5",
        "n",
        "z",
        tag="bcs_diagonal_family",
        variables=choose_variables,
    )
    choose_package = "hchoose_right_right_witness_witness_witness"
    choose_package += "_witness_witness_witness"

    choose_script = (
        "intro n",
        "intro z",
        "intro hchoose",
        "cases hchoose",
        "cases hchoose_left",
        "exfalso",
        "specialize lt_irrefl_expanded n",
        "apply lt_irrefl_expanded",
        "exact hchoose_left_left",
        "cases hchoose_right",
        "cases hchoose_right_right",
        "cases hchoose_right_right_witness",
        "cases hchoose_right_right_witness_witness",
        "cases hchoose_right_right_witness_witness_witness",
        "cases hchoose_right_right_witness_witness_witness_witness",
        "cases hchoose_right_right_witness_witness_witness_witness_witness",
        f"cases {choose_package}",
        f"cases {choose_package}_right",
        f"cases {choose_package}_right_right",
        f"have hbound : {choose_bound}",
        "specialize le_refl (S n)",
        "exact le_refl",
        f"have htable_family : {choose_table_family}",
        "specialize beta_pascal_table_diagonal_boundary x",
        "specialize beta_pascal_table_diagonal_boundary x1",
        "specialize beta_pascal_table_diagonal_boundary x2",
        "specialize beta_pascal_table_diagonal_boundary x3",
        "specialize beta_pascal_table_diagonal_boundary (S n)",
        "specialize beta_pascal_table_diagonal_boundary (S n)",
        "apply beta_pascal_table_diagonal_boundary",
        f"exact {choose_package}_left",
        f"have hrow_family : {choose_row_family}",
        "specialize htable_family n",
        "apply htable_family",
        "exact hbound",
        f"have hboundary : {choose_boundary}",
        "specialize hrow_family x4",
        "specialize hrow_family x5",
        "apply hrow_family",
        f"exact {choose_package}_right_left",
        f"exact {choose_package}_right_right_left",
        "cases hboundary",
        "have hdiagonal : forall z. "
        f"({choose_diagonal_family_at}) "
        "-> z = 1",
        "apply hboundary_left",
        "exact hbound",
        "specialize hdiagonal z",
        "apply hdiagonal",
        f"exact {choose_package}_right_right_right",
    )

    return (
        spec(
            "beta_pascal_table_diagonal_boundary",
            "forall bb bc sb sc w r. "
            f"({table}) -> forall i. ({row_bound}) -> forall b c. "
            f"({row_code_at}) -> ({row_scale_at}) -> ({boundary})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "succ_injective",
                "le_of_succ_le_succ",
                "lt_to_le",
                "le_refl",
                "beta_at_unique",
            ),
            boundary_script,
            "Every decoded Pascal row has diagonal one and zeros above it.",
        ),
        spec(
            "choose_self",
            f"forall n z. ({choose}) -> z = 1",
            (
                "lt_irrefl_expanded",
                "le_refl",
                "beta_pascal_table_diagonal_boundary",
            ),
            choose_script,
            "The recurrence-defined diagonal binomial coefficient is one.",
        ),
    )


__all__ = ["make_bertrand_choose_diagonal_candidate_theorems"]
