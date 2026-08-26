"""Cross-encoding row extensionality for recurrence-defined Pascal tables.

The sole candidate identifies corresponding decoded rows of two Pascal table
prefixes, even when the outer beta encodings, table widths, and row counts
differ.  All helper notation expands through the committed recurrence-first
Choose authoring surface into ordinary first-order Peano arithmetic.  This
module creates no language primitive, theorem authority, enrollment, or
checked-use evidence.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _beta_at_term,
    _binders,
    _identifier,
    _lt_term,
    _pascal_row_step_term,
    _pascal_table_prefix,
    _pascal_zero_row_term,
)


def _validated_variables(
    entries: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    return tuple(_identifier(value, label) for value, label in entries)


def _row_pointwise_agreement(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    left_width: str,
    right_width: str,
    *,
    tag: str,
) -> str:
    """Expand pointwise agreement of two beta-encoded finite rows."""

    variables = _validated_variables(
        (
            (left_code, "left row code"),
            (left_scale, "left row scale"),
            (right_code, "right row code"),
            (right_scale, "right row scale"),
            (left_width, "left row width"),
            (right_width, "right row width"),
        )
    )
    index, left_value, right_value = _binders(
        tag,
        variables,
        ("index", "left_value", "right_value"),
    )
    owned = variables + (index, left_value, right_value)
    left_bound = _lt_term(
        index,
        left_width,
        tag=f"{tag}_left_bound",
        variables=owned,
    )
    right_bound = _lt_term(
        index,
        right_width,
        tag=f"{tag}_right_bound",
        variables=owned,
    )
    left_entry = _beta_at_term(
        left_code,
        left_scale,
        index,
        left_value,
        tag=f"{tag}_left_entry",
        variables=owned,
    )
    right_entry = _beta_at_term(
        right_code,
        right_scale,
        index,
        right_value,
        tag=f"{tag}_right_entry",
        variables=owned,
    )
    return (
        f"forall {index} {left_value} {right_value}. "
        f"({left_bound}) -> ({right_bound}) -> "
        f"({left_entry}) -> ({right_entry}) -> "
        f"{left_value} = {right_value}"
    )


def _table_row_cell(
    row_code_code: str,
    row_code_scale: str,
    row_scale_code: str,
    row_scale_scale: str,
    width_term: str,
    row_index_term: str,
    *,
    tag: str,
) -> str:
    """Expand the semantic row package returned by one table lookup."""

    variables = _validated_variables(
        (
            (row_code_code, "row-code outer code"),
            (row_code_scale, "row-code outer scale"),
            (row_scale_code, "row-scale outer code"),
            (row_scale_scale, "row-scale outer scale"),
            (width_term, "table width"),
        )
    )
    (
        row_code,
        row_scale,
        predecessor,
        previous_code,
        previous_scale,
    ) = _binders(
        tag,
        variables,
        (
            "row_code",
            "row_scale",
            "predecessor",
            "previous_code",
            "previous_scale",
        ),
    )
    owned = variables + (
        row_code,
        row_scale,
        predecessor,
        previous_code,
        previous_scale,
    )
    decoded_row_code = _beta_at_term(
        row_code_code,
        row_code_scale,
        row_index_term,
        row_code,
        tag=f"{tag}_decoded_row_code",
        variables=owned,
    )
    decoded_row_scale = _beta_at_term(
        row_scale_code,
        row_scale_scale,
        row_index_term,
        row_scale,
        tag=f"{tag}_decoded_row_scale",
        variables=owned,
    )
    zero_row = _pascal_zero_row_term(
        row_code,
        row_scale,
        width_term,
        tag=f"{tag}_zero_row",
        variables=owned,
    )
    decoded_previous_code = _beta_at_term(
        row_code_code,
        row_code_scale,
        predecessor,
        previous_code,
        tag=f"{tag}_decoded_previous_code",
        variables=owned,
    )
    decoded_previous_scale = _beta_at_term(
        row_scale_code,
        row_scale_scale,
        predecessor,
        previous_scale,
        tag=f"{tag}_decoded_previous_scale",
        variables=owned,
    )
    row_step = _pascal_row_step_term(
        previous_code,
        previous_scale,
        row_code,
        row_scale,
        width_term,
        tag=f"{tag}_row_step",
        variables=owned,
    )
    row_kind = (
        f"(({row_index_term} = 0 /\\ ({zero_row})) \\/ "
        f"exists {predecessor} {previous_code} {previous_scale}. "
        f"{row_index_term} = S {predecessor} /\\ "
        f"(({decoded_previous_code}) /\\ "
        f"(({decoded_previous_scale}) /\\ ({row_step}))))"
    )
    return (
        f"exists {row_code} {row_scale}. "
        f"(({decoded_row_code}) /\\ (({decoded_row_scale}) /\\ "
        f"{row_kind}))"
    )


def make_bertrand_choose_table_row_functional_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated table-row extensionality candidate."""

    surface_variables = (
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "r",
        "db",
        "dc",
        "eb",
        "ec",
        "v",
        "s",
        "i",
        "b",
        "c",
        "d",
        "e",
    )
    left_table = _pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptrpf_left_table"
    )
    right_table = _pascal_table_prefix(
        "db", "dc", "eb", "ec", "v", "s", tag="bptrpf_right_table"
    )
    left_row_bound = _lt_term(
        "i",
        "r",
        tag="bptrpf_left_row_bound",
        variables=surface_variables,
    )
    right_row_bound = _lt_term(
        "i",
        "s",
        tag="bptrpf_right_row_bound",
        variables=surface_variables,
    )
    left_code_at = _beta_at_term(
        "bb",
        "bc",
        "i",
        "b",
        tag="bptrpf_left_code_at",
        variables=surface_variables,
    )
    left_scale_at = _beta_at_term(
        "sb",
        "sc",
        "i",
        "c",
        tag="bptrpf_left_scale_at",
        variables=surface_variables,
    )
    right_code_at = _beta_at_term(
        "db",
        "dc",
        "i",
        "d",
        tag="bptrpf_right_code_at",
        variables=surface_variables,
    )
    right_scale_at = _beta_at_term(
        "eb",
        "ec",
        "i",
        "e",
        tag="bptrpf_right_scale_at",
        variables=surface_variables,
    )
    agreement = _row_pointwise_agreement(
        "b", "c", "d", "e", "w", "v", tag="bptrpf_agree"
    )

    left_base_cell = _table_row_cell(
        "bb", "bc", "sb", "sc", "w", "0", tag="bptrpf_left_base"
    )
    right_base_cell = _table_row_cell(
        "db", "dc", "eb", "ec", "v", "0", tag="bptrpf_right_base"
    )
    left_step_cell = _table_row_cell(
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "S i",
        tag="bptrpf_left_step",
    )
    right_step_cell = _table_row_cell(
        "db",
        "dc",
        "eb",
        "ec",
        "v",
        "S i",
        tag="bptrpf_right_step",
    )
    base_entry_variables = surface_variables + (
        "j",
        "u",
        "y",
        "x",
        "x1",
        "x2",
        "x3",
    )
    base_left_semantic_at = _beta_at_term(
        "x",
        "x1",
        "j",
        "u",
        tag="bptrpf_base_left_semantic",
        variables=base_entry_variables,
    )
    base_right_semantic_at = _beta_at_term(
        "x2",
        "x3",
        "j",
        "y",
        tag="bptrpf_base_right_semantic",
        variables=base_entry_variables,
    )

    previous_variables = surface_variables + (
        "x",
        "x1",
        "x2",
        "x3",
        "x4",
        "x5",
        "x6",
        "x7",
        "x8",
        "x9",
    )
    previous_left_bound = _lt_term(
        "i",
        "r",
        tag="bptrpf_previous_left_bound",
        variables=previous_variables,
    )
    previous_right_bound = _lt_term(
        "i",
        "s",
        tag="bptrpf_previous_right_bound",
        variables=previous_variables,
    )
    previous_left_code_at = _beta_at_term(
        "bb",
        "bc",
        "i",
        "x5",
        tag="bptrpf_previous_left_code_at",
        variables=previous_variables,
    )
    previous_left_scale_at = _beta_at_term(
        "sb",
        "sc",
        "i",
        "x6",
        tag="bptrpf_previous_left_scale_at",
        variables=previous_variables,
    )
    previous_right_code_at = _beta_at_term(
        "db",
        "dc",
        "i",
        "x8",
        tag="bptrpf_previous_right_code_at",
        variables=previous_variables,
    )
    previous_right_scale_at = _beta_at_term(
        "eb",
        "ec",
        "i",
        "x9",
        tag="bptrpf_previous_right_scale_at",
        variables=previous_variables,
    )
    semantic_current_agreement = _row_pointwise_agreement(
        "x",
        "x1",
        "x2",
        "x3",
        "w",
        "v",
        tag="bptrpf_step_semantic_agree",
    )
    step_entry_variables = previous_variables + ("j", "u", "y")
    step_left_semantic_at = _beta_at_term(
        "x",
        "x1",
        "j",
        "u",
        tag="bptrpf_step_left_semantic",
        variables=step_entry_variables,
    )
    step_right_semantic_at = _beta_at_term(
        "x2",
        "x3",
        "j",
        "y",
        tag="bptrpf_step_right_semantic",
        variables=step_entry_variables,
    )

    script = (
        "intro bb",
        "intro bc",
        "intro sb",
        "intro sc",
        "intro w",
        "intro r",
        "intro db",
        "intro dc",
        "intro eb",
        "intro ec",
        "intro v",
        "intro s",
        "intro i",
        "induction i",
        "intro b",
        "intro c",
        "intro d",
        "intro e",
        "intro hleft_table",
        "intro hright_table",
        "intro hir",
        "intro his",
        "intro hbb",
        "intro hsb",
        "intro hdb",
        "intro heb",
        f"have hleft_row : {left_base_cell}",
        "specialize hleft_table 0",
        "apply hleft_table",
        "exact hir",
        "cases hleft_row",
        "cases hleft_row_witness",
        "cases hleft_row_witness_witness",
        "cases hleft_row_witness_witness_right",
        f"have hright_row : {right_base_cell}",
        "specialize hright_table 0",
        "apply hright_table",
        "exact his",
        "cases hright_row",
        "cases hright_row_witness",
        "cases hright_row_witness_witness",
        "cases hright_row_witness_witness_right",
        "have hb : b = x",
        "specialize beta_at_unique bb",
        "specialize beta_at_unique bc",
        "specialize beta_at_unique 0",
        "specialize beta_at_unique b",
        "specialize beta_at_unique x",
        "apply beta_at_unique",
        "exact hbb",
        "exact hleft_row_witness_witness_left",
        "have hc : c = x1",
        "specialize beta_at_unique sb",
        "specialize beta_at_unique sc",
        "specialize beta_at_unique 0",
        "specialize beta_at_unique c",
        "specialize beta_at_unique x1",
        "apply beta_at_unique",
        "exact hsb",
        "exact hleft_row_witness_witness_right_left",
        "have hd : d = x2",
        "specialize beta_at_unique db",
        "specialize beta_at_unique dc",
        "specialize beta_at_unique 0",
        "specialize beta_at_unique d",
        "specialize beta_at_unique x2",
        "apply beta_at_unique",
        "exact hdb",
        "exact hright_row_witness_witness_left",
        "have he : e = x3",
        "specialize beta_at_unique eb",
        "specialize beta_at_unique ec",
        "specialize beta_at_unique 0",
        "specialize beta_at_unique e",
        "specialize beta_at_unique x3",
        "apply beta_at_unique",
        "exact heb",
        "exact hright_row_witness_witness_right_left",
        "cases hleft_row_witness_witness_right_right",
        "cases hleft_row_witness_witness_right_right_left",
        "cases hright_row_witness_witness_right_right",
        "cases hright_row_witness_witness_right_right_left",
        "intro j",
        "intro u",
        "intro y",
        "intro hjw",
        "intro hjv",
        "intro hleft_entry",
        "intro hright_entry",
        f"have hleft_semantic : {base_left_semantic_at}",
        "rewrite <- hb",
        "rewrite <- hc",
        "rewrite <- hc",
        "exact hleft_entry",
        f"have hright_semantic : {base_right_semantic_at}",
        "rewrite <- hd",
        "rewrite <- he",
        "rewrite <- he",
        "exact hright_entry",
        "specialize beta_pascal_zero_row_pointwise_functional x",
        "specialize beta_pascal_zero_row_pointwise_functional x1",
        "specialize beta_pascal_zero_row_pointwise_functional x2",
        "specialize beta_pascal_zero_row_pointwise_functional x3",
        "specialize beta_pascal_zero_row_pointwise_functional w",
        "specialize beta_pascal_zero_row_pointwise_functional v",
        "specialize beta_pascal_zero_row_pointwise_functional j",
        "specialize beta_pascal_zero_row_pointwise_functional u",
        "specialize beta_pascal_zero_row_pointwise_functional y",
        "apply beta_pascal_zero_row_pointwise_functional",
        "exact hleft_row_witness_witness_right_right_left_right",
        "exact hright_row_witness_witness_right_right_left_right",
        "exact hjw",
        "exact hjv",
        "exact hleft_semantic",
        "exact hright_semantic",
        "cases hright_row_witness_witness_right_right_right",
        "cases hright_row_witness_witness_right_right_right_witness",
        "cases hright_row_witness_witness_right_right_right_witness_witness",
        "cases hright_row_witness_witness_right_right_right_witness_witness_witness",
        "exfalso",
        "have hbad : S x4 = 0",
        "symm",
        "exact hright_row_witness_witness_right_right_right_witness_witness_witness_left",
        "specialize succ_ne_zero x4",
        "apply succ_ne_zero",
        "exact hbad",
        "cases hleft_row_witness_witness_right_right_right",
        "cases hleft_row_witness_witness_right_right_right_witness",
        "cases hleft_row_witness_witness_right_right_right_witness_witness",
        "cases hleft_row_witness_witness_right_right_right_witness_witness_witness",
        "exfalso",
        "have hbad : S x4 = 0",
        "symm",
        "exact hleft_row_witness_witness_right_right_right_witness_witness_witness_left",
        "specialize succ_ne_zero x4",
        "apply succ_ne_zero",
        "exact hbad",
        "intro b",
        "intro c",
        "intro d",
        "intro e",
        "intro hleft_table",
        "intro hright_table",
        "intro hir",
        "intro his",
        "intro hbb",
        "intro hsb",
        "intro hdb",
        "intro heb",
        f"have hleft_row : {left_step_cell}",
        "specialize hleft_table (S i)",
        "apply hleft_table",
        "exact hir",
        "cases hleft_row",
        "cases hleft_row_witness",
        "cases hleft_row_witness_witness",
        "cases hleft_row_witness_witness_right",
        f"have hright_row : {right_step_cell}",
        "specialize hright_table (S i)",
        "apply hright_table",
        "exact his",
        "cases hright_row",
        "cases hright_row_witness",
        "cases hright_row_witness_witness",
        "cases hright_row_witness_witness_right",
        "have hb : b = x",
        "specialize beta_at_unique bb",
        "specialize beta_at_unique bc",
        "specialize beta_at_unique (S i)",
        "specialize beta_at_unique b",
        "specialize beta_at_unique x",
        "apply beta_at_unique",
        "exact hbb",
        "exact hleft_row_witness_witness_left",
        "have hc : c = x1",
        "specialize beta_at_unique sb",
        "specialize beta_at_unique sc",
        "specialize beta_at_unique (S i)",
        "specialize beta_at_unique c",
        "specialize beta_at_unique x1",
        "apply beta_at_unique",
        "exact hsb",
        "exact hleft_row_witness_witness_right_left",
        "have hd : d = x2",
        "specialize beta_at_unique db",
        "specialize beta_at_unique dc",
        "specialize beta_at_unique (S i)",
        "specialize beta_at_unique d",
        "specialize beta_at_unique x2",
        "apply beta_at_unique",
        "exact hdb",
        "exact hright_row_witness_witness_left",
        "have he : e = x3",
        "specialize beta_at_unique eb",
        "specialize beta_at_unique ec",
        "specialize beta_at_unique (S i)",
        "specialize beta_at_unique e",
        "specialize beta_at_unique x3",
        "apply beta_at_unique",
        "exact heb",
        "exact hright_row_witness_witness_right_left",
        "cases hleft_row_witness_witness_right_right",
        "cases hleft_row_witness_witness_right_right_left",
        "exfalso",
        "specialize succ_ne_zero i",
        "apply succ_ne_zero",
        "exact hleft_row_witness_witness_right_right_left_left",
        "cases hleft_row_witness_witness_right_right_right",
        "cases hleft_row_witness_witness_right_right_right_witness",
        "cases hleft_row_witness_witness_right_right_right_witness_witness",
        "cases hleft_row_witness_witness_right_right_right_witness_witness_witness",
        "cases hleft_row_witness_witness_right_right_right_witness_witness_witness_right",
        "cases hleft_row_witness_witness_right_right_right_witness_witness_witness_right_right",
        "cases hright_row_witness_witness_right_right",
        "cases hright_row_witness_witness_right_right_left",
        "exfalso",
        "specialize succ_ne_zero i",
        "apply succ_ne_zero",
        "exact hright_row_witness_witness_right_right_left_left",
        "cases hright_row_witness_witness_right_right_right",
        "cases hright_row_witness_witness_right_right_right_witness",
        "cases hright_row_witness_witness_right_right_right_witness_witness",
        "cases hright_row_witness_witness_right_right_right_witness_witness_witness",
        "cases hright_row_witness_witness_right_right_right_witness_witness_witness_right",
        "cases hright_row_witness_witness_right_right_right_witness_witness_witness_right_right",
        "have hleft_predecessor : i = x4",
        "specialize succ_injective i",
        "specialize succ_injective x4",
        "apply succ_injective",
        "exact hleft_row_witness_witness_right_right_right_witness_witness_witness_left",
        "have hright_predecessor : i = x7",
        "specialize succ_injective i",
        "specialize succ_injective x7",
        "apply succ_injective",
        "exact hright_row_witness_witness_right_right_right_witness_witness_witness_left",
        f"have hprevious_left_bound : {previous_left_bound}",
        "specialize lt_to_le (S i)",
        "specialize lt_to_le r",
        "apply lt_to_le",
        "exact hir",
        f"have hprevious_right_bound : {previous_right_bound}",
        "specialize lt_to_le (S i)",
        "specialize lt_to_le s",
        "apply lt_to_le",
        "exact his",
        f"have hprevious_left_code : {previous_left_code_at}",
        "rewrite hleft_predecessor",
        "rewrite hleft_predecessor",
        "exact hleft_row_witness_witness_right_right_right_witness_witness_witness_right_left",
        f"have hprevious_left_scale : {previous_left_scale_at}",
        "rewrite hleft_predecessor",
        "rewrite hleft_predecessor",
        (
            "exact hleft_row_witness_witness_right_right_right_witness"
            "_witness_witness_right_right_left"
        ),
        f"have hprevious_right_code : {previous_right_code_at}",
        "rewrite hright_predecessor",
        "rewrite hright_predecessor",
        "exact hright_row_witness_witness_right_right_right_witness_witness_witness_right_left",
        f"have hprevious_right_scale : {previous_right_scale_at}",
        "rewrite hright_predecessor",
        "rewrite hright_predecessor",
        (
            "exact hright_row_witness_witness_right_right_right_witness"
            "_witness_witness_right_right_left"
        ),
        f"have hcurrent_semantic : {semantic_current_agreement}",
        "specialize beta_pascal_row_step_pointwise_functional x5",
        "specialize beta_pascal_row_step_pointwise_functional x6",
        "specialize beta_pascal_row_step_pointwise_functional x8",
        "specialize beta_pascal_row_step_pointwise_functional x9",
        "specialize beta_pascal_row_step_pointwise_functional x",
        "specialize beta_pascal_row_step_pointwise_functional x1",
        "specialize beta_pascal_row_step_pointwise_functional x2",
        "specialize beta_pascal_row_step_pointwise_functional x3",
        "specialize beta_pascal_row_step_pointwise_functional w",
        "specialize beta_pascal_row_step_pointwise_functional v",
        "apply beta_pascal_row_step_pointwise_functional",
        (
            "exact hleft_row_witness_witness_right_right_right_witness"
            "_witness_witness_right_right_right"
        ),
        (
            "exact hright_row_witness_witness_right_right_right_witness"
            "_witness_witness_right_right_right"
        ),
        "specialize IH x5",
        "specialize IH x6",
        "specialize IH x8",
        "specialize IH x9",
        "apply IH",
        "exact hleft_table",
        "exact hright_table",
        "exact hprevious_left_bound",
        "exact hprevious_right_bound",
        "exact hprevious_left_code",
        "exact hprevious_left_scale",
        "exact hprevious_right_code",
        "exact hprevious_right_scale",
        "intro j",
        "intro u",
        "intro y",
        "intro hjw",
        "intro hjv",
        "intro hleft_entry",
        "intro hright_entry",
        f"have hleft_semantic : {step_left_semantic_at}",
        "rewrite <- hb",
        "rewrite <- hc",
        "rewrite <- hc",
        "exact hleft_entry",
        f"have hright_semantic : {step_right_semantic_at}",
        "rewrite <- hd",
        "rewrite <- he",
        "rewrite <- he",
        "exact hright_entry",
        "specialize hcurrent_semantic j",
        "specialize hcurrent_semantic u",
        "specialize hcurrent_semantic y",
        "apply hcurrent_semantic",
        "exact hjw",
        "exact hjv",
        "exact hleft_semantic",
        "exact hright_semantic",
    )

    return (
        spec(
            "beta_pascal_table_row_pointwise_functional",
            "forall bb bc sb sc w r db dc eb ec v s i b c d e. "
            f"({left_table}) -> ({right_table}) -> "
            f"({left_row_bound}) -> ({right_row_bound}) -> "
            f"({left_code_at}) -> ({left_scale_at}) -> "
            f"({right_code_at}) -> ({right_scale_at}) -> ({agreement})",
            (
                "beta_at_unique",
                "succ_ne_zero",
                "succ_injective",
                "lt_to_le",
                "beta_pascal_zero_row_pointwise_functional",
                "beta_pascal_row_step_pointwise_functional",
            ),
            script,
            "Corresponding decoded Pascal-table rows agree pointwise.",
        ),
    )


__all__ = ["make_bertrand_choose_table_row_functional_candidate_theorems"]
