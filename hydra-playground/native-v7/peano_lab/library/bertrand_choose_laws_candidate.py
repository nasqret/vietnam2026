"""Constructive functionality and boundary laws for relational Choose.

The three candidates use the recurrence-first Choose relation and its Pascal
table semantics without adding quotient notation, a function symbol, or any
new trusted primitive.  All authoring helpers below expand to ordinary
first-order Peano arithmetic before parsing.  This module does not register,
enroll, or grant checked use to any theorem.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _beta_at_term,
    _binders,
    _choose_relation,
    _choose_relation_term,
    _lt_term,
    _pascal_row_step_term,
    _pascal_zero_row_term,
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
    """Expand cross-encoding row agreement with term-valued widths."""

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


def _zero_row_cell(
    code: str,
    scale: str,
    index_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    value, predecessor = _binders(
        tag,
        variables,
        ("cell_value", "cell_predecessor"),
    )
    owned = variables + (value, predecessor)
    entry = _beta_at_term(
        code,
        scale,
        index_term,
        value,
        tag=f"{tag}_entry",
        variables=owned,
    )
    boundary = (
        f"(({index_term} = 0 /\\ {value} = 1) \\/ "
        f"exists {predecessor}. "
        f"{index_term} = S {predecessor} /\\ {value} = 0)"
    )
    return f"exists {value}. (({entry}) /\\ {boundary})"


def _row_step_cell(
    previous_code: str,
    previous_scale: str,
    code: str,
    scale: str,
    index_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    value, predecessor, left_value, right_value = _binders(
        tag,
        variables,
        ("cell_value", "cell_predecessor", "cell_left", "cell_right"),
    )
    owned = variables + (value, predecessor, left_value, right_value)
    entry = _beta_at_term(
        code,
        scale,
        index_term,
        value,
        tag=f"{tag}_entry",
        variables=owned,
    )
    previous_left = _beta_at_term(
        previous_code,
        previous_scale,
        predecessor,
        left_value,
        tag=f"{tag}_previous_left",
        variables=owned,
    )
    previous_right = _beta_at_term(
        previous_code,
        previous_scale,
        f"S ({predecessor})",
        right_value,
        tag=f"{tag}_previous_right",
        variables=owned,
    )
    recurrence = (
        f"exists {predecessor} {left_value} {right_value}. "
        f"{index_term} = S {predecessor} /\\ "
        f"(({previous_left}) /\\ (({previous_right}) /\\ "
        f"{value} = {left_value} + {right_value}))"
    )
    return (
        f"exists {value}. (({entry}) /\\ "
        f"(({index_term} = 0 /\\ {value} = 1) \\/ {recurrence}))"
    )


def _table_row_cell_term(
    row_code_code: str,
    row_code_scale: str,
    row_scale_code: str,
    row_scale_scale: str,
    width_term: str,
    row_index_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
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


def make_bertrand_choose_laws_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered initial Choose-law tranche."""

    functional_left = _choose_relation("n", "k", "x", tag="bclf_left")
    functional_right = _choose_relation("n", "k", "y", tag="bclf_right")
    functional_row_bound = _lt_term(
        "n",
        "S n",
        tag="bclf_row_bound",
        variables=("n", "k", "x", "y"),
    )
    functional_inner_bound = _lt_term(
        "k",
        "S n",
        tag="bclf_inner_bound",
        variables=("n", "k", "x", "y"),
    )
    functional_agreement = _row_pointwise_agreement_term(
        "x5",
        "x6",
        "x11",
        "x12",
        "S n",
        "S n",
        tag="bclf_semantic_agreement",
        variables=(
            "n",
            "k",
            "x",
            "y",
            "x1",
            "x2",
            "x3",
            "x4",
            "x5",
            "x6",
            "x7",
            "x8",
            "x9",
            "x10",
            "x11",
            "x12",
        ),
    )

    out_of_range_choose = _choose_relation(
        "n", "k", "z", tag="bcloor_choose"
    )
    out_of_range_bound = _lt_term(
        "n",
        "k",
        tag="bcloor_bound",
        variables=("n", "k", "z"),
    )

    zero_choose = _choose_relation_term(
        "n",
        "0",
        "z",
        tag="bclz_choose",
        variables=("n", "z"),
    )
    zero_package_variables = (
        "n",
        "z",
        "x",
        "x1",
        "x2",
        "x3",
        "x4",
        "x5",
    )
    zero_row_bound = _lt_term(
        "n",
        "S n",
        tag="bclz_row_bound",
        variables=zero_package_variables,
    )
    zero_inner_bound = _lt_term(
        "0",
        "S n",
        tag="bclz_inner_bound",
        variables=zero_package_variables,
    )
    zero_table_row = _table_row_cell_term(
        "x",
        "x1",
        "x2",
        "x3",
        "S n",
        "n",
        tag="bclz_table_row",
        variables=zero_package_variables,
    )
    zero_semantic_at = _beta_at_term(
        "x6",
        "x7",
        "0",
        "z",
        tag="bclz_semantic_at",
        variables=zero_package_variables + ("x6", "x7"),
    )
    zero_cell = _zero_row_cell(
        "x6",
        "x7",
        "0",
        tag="bclz_zero_cell",
        variables=zero_package_variables + ("x6", "x7"),
    )
    step_cell = _row_step_cell(
        "x9",
        "x10",
        "x6",
        "x7",
        "0",
        tag="bclz_step_cell",
        variables=zero_package_variables
        + ("x6", "x7", "x8", "x9", "x10"),
    )

    return (
        spec(
            "choose_functional",
            "forall n k x y. "
            f"({functional_left}) -> ({functional_right}) -> x = y",
            (
                "lt_not_le",
                "le_refl",
                "succ_le_succ",
                "beta_pascal_table_row_pointwise_functional",
            ),
            (
                "intro n",
                "intro k",
                "intro x",
                "intro y",
                "intro hleft",
                "intro hright",
                "cases hleft",
                "cases hleft_left",
                "cases hright",
                "cases hright_left",
                "trans 0",
                "exact hleft_left_right",
                "symm",
                "exact hright_left_right",
                "cases hright_right",
                "exfalso",
                "specialize lt_not_le n",
                "specialize lt_not_le k",
                "apply lt_not_le",
                "exact hleft_left_left",
                "exact hright_right_left",
                "cases hleft_right",
                "cases hright",
                "cases hright_left",
                "exfalso",
                "specialize lt_not_le n",
                "specialize lt_not_le k",
                "apply lt_not_le",
                "exact hright_left_left",
                "exact hleft_right_left",
                "cases hright_right",
                "cases hleft_right_right",
                "cases hleft_right_right_witness",
                "cases hleft_right_right_witness_witness",
                "cases hleft_right_right_witness_witness_witness",
                "cases hleft_right_right_witness_witness_witness_witness",
                "cases hleft_right_right_witness_witness_witness_witness_witness",
                (
                    "cases hleft_right_right_witness_witness_witness_witness"
                    "_witness_witness"
                ),
                (
                    "cases hleft_right_right_witness_witness_witness_witness"
                    "_witness_witness_right"
                ),
                (
                    "cases hleft_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_right"
                ),
                "cases hright_right_right",
                "cases hright_right_right_witness",
                "cases hright_right_right_witness_witness",
                "cases hright_right_right_witness_witness_witness",
                "cases hright_right_right_witness_witness_witness_witness",
                "cases hright_right_right_witness_witness_witness_witness_witness",
                (
                    "cases hright_right_right_witness_witness_witness_witness"
                    "_witness_witness"
                ),
                (
                    "cases hright_right_right_witness_witness_witness_witness"
                    "_witness_witness_right"
                ),
                (
                    "cases hright_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_right"
                ),
                f"have hrow_bound : {functional_row_bound}",
                "specialize le_refl (S n)",
                "exact le_refl",
                f"have hinner_bound : {functional_inner_bound}",
                "specialize succ_le_succ k",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hleft_right_left",
                f"have hagree : {functional_agreement}",
                "specialize beta_pascal_table_row_pointwise_functional x1",
                "specialize beta_pascal_table_row_pointwise_functional x2",
                "specialize beta_pascal_table_row_pointwise_functional x3",
                "specialize beta_pascal_table_row_pointwise_functional x4",
                "specialize beta_pascal_table_row_pointwise_functional (S n)",
                "specialize beta_pascal_table_row_pointwise_functional (S n)",
                "specialize beta_pascal_table_row_pointwise_functional x7",
                "specialize beta_pascal_table_row_pointwise_functional x8",
                "specialize beta_pascal_table_row_pointwise_functional x9",
                "specialize beta_pascal_table_row_pointwise_functional x10",
                "specialize beta_pascal_table_row_pointwise_functional (S n)",
                "specialize beta_pascal_table_row_pointwise_functional (S n)",
                "specialize beta_pascal_table_row_pointwise_functional n",
                "specialize beta_pascal_table_row_pointwise_functional x5",
                "specialize beta_pascal_table_row_pointwise_functional x6",
                "specialize beta_pascal_table_row_pointwise_functional x11",
                "specialize beta_pascal_table_row_pointwise_functional x12",
                "apply beta_pascal_table_row_pointwise_functional",
                (
                    "exact hleft_right_right_witness_witness_witness_witness"
                    "_witness_witness_left"
                ),
                (
                    "exact hright_right_right_witness_witness_witness_witness"
                    "_witness_witness_left"
                ),
                "exact hrow_bound",
                "exact hrow_bound",
                (
                    "exact hleft_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_left"
                ),
                (
                    "exact hleft_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_right_left"
                ),
                (
                    "exact hright_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_left"
                ),
                (
                    "exact hright_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_right_left"
                ),
                "specialize hagree k",
                "specialize hagree x",
                "specialize hagree y",
                "apply hagree",
                "exact hinner_bound",
                "exact hinner_bound",
                (
                    "exact hleft_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_right_right"
                ),
                (
                    "exact hright_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_right_right"
                ),
            ),
            "The recurrence-defined Choose relation is functional.",
        ),
        spec(
            "choose_out_of_range_zero",
            "forall n k z. "
            f"({out_of_range_bound}) -> ({out_of_range_choose}) -> z = 0",
            ("lt_not_le",),
            (
                "intro n",
                "intro k",
                "intro z",
                "intro hbound",
                "intro hchoose",
                "cases hchoose",
                "cases hchoose_left",
                "exact hchoose_left_right",
                "cases hchoose_right",
                "exfalso",
                "specialize lt_not_le n",
                "specialize lt_not_le k",
                "apply lt_not_le",
                "exact hbound",
                "exact hchoose_right_left",
            ),
            "An out-of-range Choose value is zero.",
        ),
        spec(
            "choose_zero",
            f"forall n z. ({zero_choose}) -> z = 1",
            (
                "zero_le",
                "lt_not_le",
                "le_refl",
                "succ_le_succ",
                "succ_ne_zero",
                "beta_at_unique",
            ),
            (
                "intro n",
                "intro z",
                "intro hchoose",
                "cases hchoose",
                "cases hchoose_left",
                "exfalso",
                "specialize lt_not_le n",
                "specialize lt_not_le 0",
                "apply lt_not_le",
                "exact hchoose_left_left",
                "specialize zero_le n",
                "exact zero_le",
                "cases hchoose_right",
                "cases hchoose_right_right",
                "cases hchoose_right_right_witness",
                "cases hchoose_right_right_witness_witness",
                "cases hchoose_right_right_witness_witness_witness",
                "cases hchoose_right_right_witness_witness_witness_witness",
                "cases hchoose_right_right_witness_witness_witness_witness_witness",
                (
                    "cases hchoose_right_right_witness_witness_witness_witness"
                    "_witness_witness"
                ),
                (
                    "cases hchoose_right_right_witness_witness_witness_witness"
                    "_witness_witness_right"
                ),
                (
                    "cases hchoose_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_right"
                ),
                f"have hrow_bound : {zero_row_bound}",
                "specialize le_refl (S n)",
                "exact le_refl",
                f"have hinner_bound : {zero_inner_bound}",
                "specialize succ_le_succ 0",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "specialize zero_le n",
                "exact zero_le",
                f"have hrow : {zero_table_row}",
                (
                    "specialize hchoose_right_right_witness_witness_witness"
                    "_witness_witness_witness_left n"
                ),
                (
                    "apply hchoose_right_right_witness_witness_witness_witness"
                    "_witness_witness_left"
                ),
                "exact hrow_bound",
                "cases hrow",
                "cases hrow_witness",
                "cases hrow_witness_witness",
                "cases hrow_witness_witness_right",
                "have hcode : x4 = x6",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique n",
                "specialize beta_at_unique x4",
                "specialize beta_at_unique x6",
                "apply beta_at_unique",
                (
                    "exact hchoose_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_left"
                ),
                "exact hrow_witness_witness_left",
                "have hscale : x5 = x7",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique x3",
                "specialize beta_at_unique n",
                "specialize beta_at_unique x5",
                "specialize beta_at_unique x7",
                "apply beta_at_unique",
                (
                    "exact hchoose_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_right_left"
                ),
                "exact hrow_witness_witness_right_left",
                f"have hvalue : {zero_semantic_at}",
                "rewrite <- hcode",
                "rewrite <- hscale",
                "rewrite <- hscale",
                (
                    "exact hchoose_right_right_witness_witness_witness_witness"
                    "_witness_witness_right_right_right"
                ),
                "cases hrow_witness_witness_right_right",
                "cases hrow_witness_witness_right_right_left",
                f"have hcell : {zero_cell}",
                "specialize hrow_witness_witness_right_right_left_right 0",
                "apply hrow_witness_witness_right_right_left_right",
                "exact hinner_bound",
                "cases hcell",
                "cases hcell_witness",
                "have hzvalue : z = x8",
                "specialize beta_at_unique x6",
                "specialize beta_at_unique x7",
                "specialize beta_at_unique 0",
                "specialize beta_at_unique z",
                "specialize beta_at_unique x8",
                "apply beta_at_unique",
                "exact hvalue",
                "exact hcell_witness_left",
                "cases hcell_witness_right",
                "cases hcell_witness_right_left",
                "trans x8",
                "exact hzvalue",
                "exact hcell_witness_right_left_right",
                "cases hcell_witness_right_right",
                "cases hcell_witness_right_right_witness",
                "exfalso",
                "have hbad : S x9 = 0",
                "symm",
                "exact hcell_witness_right_right_witness_left",
                "specialize succ_ne_zero x9",
                "apply succ_ne_zero",
                "exact hbad",
                "cases hrow_witness_witness_right_right_right",
                "cases hrow_witness_witness_right_right_right_witness",
                "cases hrow_witness_witness_right_right_right_witness_witness",
                "cases hrow_witness_witness_right_right_right_witness_witness_witness",
                (
                    "cases hrow_witness_witness_right_right_right_witness"
                    "_witness_witness_right"
                ),
                (
                    "cases hrow_witness_witness_right_right_right_witness"
                    "_witness_witness_right_right"
                ),
                f"have hcell : {step_cell}",
                (
                    "specialize hrow_witness_witness_right_right_right_witness"
                    "_witness_witness_right_right_right 0"
                ),
                (
                    "apply hrow_witness_witness_right_right_right_witness"
                    "_witness_witness_right_right_right"
                ),
                "exact hinner_bound",
                "cases hcell",
                "cases hcell_witness",
                "have hzvalue : z = x11",
                "specialize beta_at_unique x6",
                "specialize beta_at_unique x7",
                "specialize beta_at_unique 0",
                "specialize beta_at_unique z",
                "specialize beta_at_unique x11",
                "apply beta_at_unique",
                "exact hvalue",
                "exact hcell_witness_left",
                "cases hcell_witness_right",
                "cases hcell_witness_right_left",
                "trans x11",
                "exact hzvalue",
                "exact hcell_witness_right_left_right",
                "cases hcell_witness_right_right",
                "cases hcell_witness_right_right_witness",
                "cases hcell_witness_right_right_witness_witness",
                "cases hcell_witness_right_right_witness_witness_witness",
                "exfalso",
                "have hbad : S x12 = 0",
                "symm",
                "exact hcell_witness_right_right_witness_witness_witness_left",
                "specialize succ_ne_zero x12",
                "apply succ_ne_zero",
                "exact hbad",
            ),
            "The zeroth entry of every Pascal row is one.",
        ),
    )


__all__ = ["make_bertrand_choose_laws_candidate_theorems"]
