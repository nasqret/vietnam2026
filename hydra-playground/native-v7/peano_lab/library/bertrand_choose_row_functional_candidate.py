"""Pointwise functionality for recurrence-defined Pascal rows.

The two candidates compare Pascal rows even when their beta codes, beta
scales, and declared widths differ.  Every displayed relation is expanded by
the committed recurrence-first Choose authoring helpers into ordinary
first-order Peano arithmetic before parsing.  This module adds no language
primitive, theorem authority, enrollment, or checked-use evidence.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _beta_at_term,
    _binders,
    _identifier,
    _lt_term,
    _pascal_row_step,
    _pascal_zero_row,
)


def _validated_variables(
    entries: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    return tuple(_identifier(value, label) for value, label in entries)


def _zero_row_cell(
    code: str,
    scale: str,
    index: str,
    *,
    tag: str,
) -> str:
    """Expand the value package supplied by one zero-row position."""

    variables = _validated_variables(
        (
            (code, "row code"),
            (scale, "row scale"),
            (index, "row index"),
        )
    )
    value, predecessor = _binders(
        tag,
        variables,
        ("cell_value", "cell_predecessor"),
    )
    owned = variables + (value, predecessor)
    entry = _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_entry",
        variables=owned,
    )
    boundary = (
        f"(({index} = 0 /\\ {value} = 1) \\/ "
        f"exists {predecessor}. "
        f"{index} = S {predecessor} /\\ {value} = 0)"
    )
    return f"exists {value}. (({entry}) /\\ {boundary})"


def _row_step_cell(
    previous_code: str,
    previous_scale: str,
    code: str,
    scale: str,
    index: str,
    *,
    tag: str,
) -> str:
    """Expand the value package supplied by one successor-row position."""

    variables = _validated_variables(
        (
            (previous_code, "previous row code"),
            (previous_scale, "previous row scale"),
            (code, "row code"),
            (scale, "row scale"),
            (index, "row index"),
        )
    )
    value, predecessor, left_value, right_value = _binders(
        tag,
        variables,
        ("cell_value", "cell_predecessor", "cell_left", "cell_right"),
    )
    owned = variables + (value, predecessor, left_value, right_value)
    entry = _beta_at_term(
        code,
        scale,
        index,
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
        f"{index} = S {predecessor} /\\ "
        f"(({previous_left}) /\\ (({previous_right}) /\\ "
        f"{value} = {left_value} + {right_value}))"
    )
    boundary = f"(({index} = 0 /\\ {value} = 1) \\/ {recurrence})"
    return f"exists {value}. (({entry}) /\\ {boundary})"


def make_bertrand_choose_row_functional_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered row-functionality microtranche."""

    zero_variables = ("b", "c", "d", "e", "w", "v", "i", "x", "y")
    zero_left = _pascal_zero_row("b", "c", "w", tag="bzrpf_left")
    zero_right = _pascal_zero_row("d", "e", "v", tag="bzrpf_right")
    zero_left_bound = _lt_term(
        "i", "w", tag="bzrpf_left_bound", variables=zero_variables
    )
    zero_right_bound = _lt_term(
        "i", "v", tag="bzrpf_right_bound", variables=zero_variables
    )
    zero_left_at = _beta_at_term(
        "b",
        "c",
        "i",
        "x",
        tag="bzrpf_left_at",
        variables=zero_variables,
    )
    zero_right_at = _beta_at_term(
        "d",
        "e",
        "i",
        "y",
        tag="bzrpf_right_at",
        variables=zero_variables,
    )
    zero_left_cell = _zero_row_cell(
        "b", "c", "i", tag="bzrpf_left_cell"
    )
    zero_right_cell = _zero_row_cell(
        "d", "e", "i", tag="bzrpf_right_cell"
    )

    step_outer_variables = (
        "pb",
        "pc",
        "qb",
        "qc",
        "b",
        "c",
        "d",
        "e",
        "w",
        "v",
    )
    pointwise_variables = step_outer_variables + ("i", "x", "y")
    step_left = _pascal_row_step(
        "pb", "pc", "b", "c", "w", tag="bpspf_left"
    )
    step_right = _pascal_row_step(
        "qb", "qc", "d", "e", "v", tag="bpspf_right"
    )
    previous_left_bound = _lt_term(
        "i",
        "w",
        tag="bpspf_previous_left_bound",
        variables=pointwise_variables,
    )
    previous_right_bound = _lt_term(
        "i",
        "v",
        tag="bpspf_previous_right_bound",
        variables=pointwise_variables,
    )
    previous_left_at = _beta_at_term(
        "pb",
        "pc",
        "i",
        "x",
        tag="bpspf_previous_left_at",
        variables=pointwise_variables,
    )
    previous_right_at = _beta_at_term(
        "qb",
        "qc",
        "i",
        "y",
        tag="bpspf_previous_right_at",
        variables=pointwise_variables,
    )
    previous_pointwise = (
        f"forall i x y. ({previous_left_bound}) -> "
        f"({previous_right_bound}) -> ({previous_left_at}) -> "
        f"({previous_right_at}) -> x = y"
    )
    current_left_bound = _lt_term(
        "i",
        "w",
        tag="bpspf_current_left_bound",
        variables=pointwise_variables,
    )
    current_right_bound = _lt_term(
        "i",
        "v",
        tag="bpspf_current_right_bound",
        variables=pointwise_variables,
    )
    current_left_at = _beta_at_term(
        "b",
        "c",
        "i",
        "x",
        tag="bpspf_current_left_at",
        variables=pointwise_variables,
    )
    current_right_at = _beta_at_term(
        "d",
        "e",
        "i",
        "y",
        tag="bpspf_current_right_at",
        variables=pointwise_variables,
    )
    current_pointwise = (
        f"forall i x y. ({current_left_bound}) -> "
        f"({current_right_bound}) -> ({current_left_at}) -> "
        f"({current_right_at}) -> x = y"
    )
    step_left_cell = _row_step_cell(
        "pb", "pc", "b", "c", "i", tag="bpspf_left_cell"
    )
    step_right_cell = _row_step_cell(
        "qb", "qc", "d", "e", "i", tag="bpspf_right_cell"
    )
    step_branch_variables = step_outer_variables + (
        "i",
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
    )
    branch_current_w = _lt_term(
        "S x3",
        "w",
        tag="bpspf_current_w",
        variables=step_branch_variables,
    )
    branch_current_v = _lt_term(
        "S x3",
        "v",
        tag="bpspf_current_v",
        variables=step_branch_variables,
    )
    branch_previous_w = _lt_term(
        "x3",
        "w",
        tag="bpspf_previous_w",
        variables=step_branch_variables,
    )
    branch_previous_v = _lt_term(
        "x3",
        "v",
        tag="bpspf_previous_v",
        variables=step_branch_variables,
    )
    aligned_previous = _beta_at_term(
        "qb",
        "qc",
        "x3",
        "x7",
        tag="bpspf_aligned_previous",
        variables=step_branch_variables,
    )
    aligned_current = _beta_at_term(
        "qb",
        "qc",
        "S x3",
        "x8",
        tag="bpspf_aligned_current",
        variables=step_branch_variables,
    )

    zero_script = (
        "intro b",
        "intro c",
        "intro d",
        "intro e",
        "intro w",
        "intro v",
        "intro i",
        "intro x",
        "intro y",
        "intro hleft",
        "intro hright",
        "intro hiw",
        "intro hiv",
        "intro hxi",
        "intro hyi",
        f"have hleft_value : {zero_left_cell}",
        "specialize hleft i",
        "apply hleft",
        "exact hiw",
        "cases hleft_value",
        "cases hleft_value_witness",
        f"have hright_value : {zero_right_cell}",
        "specialize hright i",
        "apply hright",
        "exact hiv",
        "cases hright_value",
        "cases hright_value_witness",
        "have hx_value : x = x1",
        "specialize beta_at_unique b",
        "specialize beta_at_unique c",
        "specialize beta_at_unique i",
        "specialize beta_at_unique x",
        "specialize beta_at_unique x1",
        "apply beta_at_unique",
        "exact hxi",
        "exact hleft_value_witness_left",
        "have hy_value : y = x2",
        "specialize beta_at_unique d",
        "specialize beta_at_unique e",
        "specialize beta_at_unique i",
        "specialize beta_at_unique y",
        "specialize beta_at_unique x2",
        "apply beta_at_unique",
        "exact hyi",
        "exact hright_value_witness_left",
        "cases hleft_value_witness_right",
        "cases hleft_value_witness_right_left",
        "cases hright_value_witness_right",
        "cases hright_value_witness_right_left",
        "trans x1",
        "exact hx_value",
        "trans 1",
        "exact hleft_value_witness_right_left_right",
        "trans x2",
        "symm",
        "exact hright_value_witness_right_left_right",
        "symm",
        "exact hy_value",
        "cases hright_value_witness_right_right",
        "cases hright_value_witness_right_right_witness",
        "exfalso",
        "have hbad : S x3 = 0",
        "trans i",
        "symm",
        "exact hright_value_witness_right_right_witness_left",
        "exact hleft_value_witness_right_left_left",
        "specialize succ_ne_zero x3",
        "apply succ_ne_zero",
        "exact hbad",
        "cases hleft_value_witness_right_right",
        "cases hleft_value_witness_right_right_witness",
        "cases hright_value_witness_right",
        "cases hright_value_witness_right_left",
        "exfalso",
        "have hbad : S x3 = 0",
        "trans i",
        "symm",
        "exact hleft_value_witness_right_right_witness_left",
        "exact hright_value_witness_right_left_left",
        "specialize succ_ne_zero x3",
        "apply succ_ne_zero",
        "exact hbad",
        "cases hright_value_witness_right_right",
        "cases hright_value_witness_right_right_witness",
        "trans x1",
        "exact hx_value",
        "trans 0",
        "exact hleft_value_witness_right_right_witness_right",
        "trans x2",
        "symm",
        "exact hright_value_witness_right_right_witness_right",
        "symm",
        "exact hy_value",
    )

    step_script = (
        "intro pb",
        "intro pc",
        "intro qb",
        "intro qc",
        "intro b",
        "intro c",
        "intro d",
        "intro e",
        "intro w",
        "intro v",
        "intro hleft",
        "intro hright",
        "intro hagree",
        "intro i",
        "intro x",
        "intro y",
        "intro hiw",
        "intro hiv",
        "intro hxi",
        "intro hyi",
        f"have hleft_value : {step_left_cell}",
        "specialize hleft i",
        "apply hleft",
        "exact hiw",
        "cases hleft_value",
        "cases hleft_value_witness",
        f"have hright_value : {step_right_cell}",
        "specialize hright i",
        "apply hright",
        "exact hiv",
        "cases hright_value",
        "cases hright_value_witness",
        "have hx_value : x = x1",
        "specialize beta_at_unique b",
        "specialize beta_at_unique c",
        "specialize beta_at_unique i",
        "specialize beta_at_unique x",
        "specialize beta_at_unique x1",
        "apply beta_at_unique",
        "exact hxi",
        "exact hleft_value_witness_left",
        "have hy_value : y = x2",
        "specialize beta_at_unique d",
        "specialize beta_at_unique e",
        "specialize beta_at_unique i",
        "specialize beta_at_unique y",
        "specialize beta_at_unique x2",
        "apply beta_at_unique",
        "exact hyi",
        "exact hright_value_witness_left",
        "cases hleft_value_witness_right",
        "cases hleft_value_witness_right_left",
        "cases hright_value_witness_right",
        "cases hright_value_witness_right_left",
        "trans x1",
        "exact hx_value",
        "trans 1",
        "exact hleft_value_witness_right_left_right",
        "trans x2",
        "symm",
        "exact hright_value_witness_right_left_right",
        "symm",
        "exact hy_value",
        "cases hright_value_witness_right_right",
        "cases hright_value_witness_right_right_witness",
        "cases hright_value_witness_right_right_witness_witness",
        "cases hright_value_witness_right_right_witness_witness_witness",
        "exfalso",
        "have hbad : S x3 = 0",
        "trans i",
        "symm",
        "exact hright_value_witness_right_right_witness_witness_witness_left",
        "exact hleft_value_witness_right_left_left",
        "specialize succ_ne_zero x3",
        "apply succ_ne_zero",
        "exact hbad",
        "cases hleft_value_witness_right_right",
        "cases hleft_value_witness_right_right_witness",
        "cases hleft_value_witness_right_right_witness_witness",
        "cases hleft_value_witness_right_right_witness_witness_witness",
        "cases hleft_value_witness_right_right_witness_witness_witness_right",
        "cases hleft_value_witness_right_right_witness_witness_witness_right_right",
        "cases hright_value_witness_right",
        "cases hright_value_witness_right_left",
        "exfalso",
        "have hbad : S x3 = 0",
        "trans i",
        "symm",
        "exact hleft_value_witness_right_right_witness_witness_witness_left",
        "exact hright_value_witness_right_left_left",
        "specialize succ_ne_zero x3",
        "apply succ_ne_zero",
        "exact hbad",
        "cases hright_value_witness_right_right",
        "cases hright_value_witness_right_right_witness",
        "cases hright_value_witness_right_right_witness_witness",
        "cases hright_value_witness_right_right_witness_witness_witness",
        "cases hright_value_witness_right_right_witness_witness_witness_right",
        "cases hright_value_witness_right_right_witness_witness_witness_right_right",
        "have hsucc : S x3 = S x6",
        "trans i",
        "symm",
        "exact hleft_value_witness_right_right_witness_witness_witness_left",
        "exact hright_value_witness_right_right_witness_witness_witness_left",
        "have hpred : x3 = x6",
        "specialize succ_injective x3",
        "specialize succ_injective x6",
        "apply succ_injective",
        "exact hsucc",
        f"have hcurrent_w : {branch_current_w}",
        "rewrite <- hleft_value_witness_right_right_witness_witness_witness_left",
        "exact hiw",
        f"have hcurrent_v : {branch_current_v}",
        "rewrite <- hleft_value_witness_right_right_witness_witness_witness_left",
        "exact hiv",
        f"have hprevious_w : {branch_previous_w}",
        "specialize lt_to_le (S x3)",
        "specialize lt_to_le w",
        "apply lt_to_le",
        "exact hcurrent_w",
        f"have hprevious_v : {branch_previous_v}",
        "specialize lt_to_le (S x3)",
        "specialize lt_to_le v",
        "apply lt_to_le",
        "exact hcurrent_v",
        f"have hright_previous : {aligned_previous}",
        "rewrite hpred",
        "rewrite hpred",
        "exact hright_value_witness_right_right_witness_witness_witness_right_left",
        f"have hright_current : {aligned_current}",
        "rewrite hpred",
        "rewrite hpred",
        (
            "exact hright_value_witness_right_right_witness_witness_witness"
            "_right_right_left"
        ),
        "have hu : x4 = x7",
        "specialize hagree x3",
        "specialize hagree x4",
        "specialize hagree x7",
        "apply hagree",
        "exact hprevious_w",
        "exact hprevious_v",
        "exact hleft_value_witness_right_right_witness_witness_witness_right_left",
        "exact hright_previous",
        "have hv : x5 = x8",
        "specialize hagree (S x3)",
        "specialize hagree x5",
        "specialize hagree x8",
        "apply hagree",
        "exact hcurrent_w",
        "exact hcurrent_v",
        (
            "exact hleft_value_witness_right_right_witness_witness_witness"
            "_right_right_left"
        ),
        "exact hright_current",
        "trans x1",
        "exact hx_value",
        "trans x4 + x5",
        (
            "exact hleft_value_witness_right_right_witness_witness_witness"
            "_right_right_right"
        ),
        "trans x7 + x8",
        "congr",
        "exact hu",
        "exact hv",
        "trans x2",
        "symm",
        (
            "exact hright_value_witness_right_right_witness_witness_witness"
            "_right_right_right"
        ),
        "symm",
        "exact hy_value",
    )

    return (
        spec(
            "beta_pascal_zero_row_pointwise_functional",
            "forall b c d e w v i x y. "
            f"({zero_left}) -> ({zero_right}) -> "
            f"({zero_left_bound}) -> ({zero_right_bound}) -> "
            f"({zero_left_at}) -> ({zero_right_at}) -> x = y",
            ("beta_at_unique", "succ_ne_zero"),
            zero_script,
            "Zero-row values agree pointwise across beta encodings and widths.",
        ),
        spec(
            "beta_pascal_row_step_pointwise_functional",
            "forall pb pc qb qc b c d e w v. "
            f"({step_left}) -> ({step_right}) -> "
            f"({previous_pointwise}) -> ({current_pointwise})",
            (
                "beta_at_unique",
                "succ_ne_zero",
                "succ_injective",
                "lt_to_le",
            ),
            step_script,
            "Pascal successor rows preserve pointwise agreement across encodings.",
        ),
    )


__all__ = ["make_bertrand_choose_row_functional_candidate_theorems"]
