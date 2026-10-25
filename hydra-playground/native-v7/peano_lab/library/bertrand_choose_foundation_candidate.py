"""Recurrence-first beta foundation for relational binomial coefficients.

The candidate surface constructs finite Pascal rectangles in two beta layers.
Each inner beta prefix is one Pascal row.  Two outer beta prefixes store the
inner row codes and scales separately, avoiding both a pairing primitive and
a flattened two-dimensional index.  ``Choose(n,k,z)`` is zero explicitly
when ``n < k`` and otherwise decodes the ``k``-th entry of row ``n`` from an
``S n`` by ``S n`` Pascal prefix.

Every helper below is untrusted authoring notation.  It expands completely to
ordinary first-order Peano arithmetic before parsing; no beta, table, choose,
comparison, function, sequence, or recursion primitive is added to the
language.  The seven rows are dependency-curried candidates and are not
registered or enrolled by this module.
"""

from __future__ import annotations

from typing import Any, Callable


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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"bcf_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Choose-foundation binder captures an argument")
    return names


def _beta_at_term(
    code: str,
    scale: str,
    index_term: str,
    value_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, variables, ("height", "quotient"))
    modulus = f"S ((S ({index_term})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value_term}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value_term}))"
    )


def _lt_term(
    left_term: str,
    right_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("lt_gap",))
    return f"exists {gap}. {gap} + S ({left_term}) = {right_term}"


def _le_term(
    left_term: str,
    right_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("le_gap",))
    return f"exists {gap}. {gap} + ({left_term}) = {right_term}"


def _pascal_zero_row_term(
    code: str,
    scale: str,
    width_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index, value, predecessor = _binders(
        tag, variables, ("index", "value", "predecessor")
    )
    owned = variables + (index, value, predecessor)
    bound = _lt_term(
        index,
        width_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
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
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({entry}) /\\ {boundary})"
    )


def _pascal_row_step_term(
    previous_code: str,
    previous_scale: str,
    code: str,
    scale: str,
    width_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index, value, predecessor, left_value, right_value = _binders(
        tag,
        variables,
        ("index", "value", "predecessor", "left", "right"),
    )
    owned = variables + (
        index,
        value,
        predecessor,
        left_value,
        right_value,
    )
    bound = _lt_term(
        index,
        width_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
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
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({entry}) /\\ {boundary})"
    )


def _pascal_table_prefix_term(
    row_code_code: str,
    row_code_scale: str,
    row_scale_code: str,
    row_scale_scale: str,
    width_term: str,
    rows_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (
        row_index,
        row_code,
        row_scale,
        predecessor,
        previous_code,
        previous_scale,
    ) = _binders(
        tag,
        variables,
        (
            "row_index",
            "row_code",
            "row_scale",
            "predecessor",
            "previous_code",
            "previous_scale",
        ),
    )
    owned = variables + (
        row_index,
        row_code,
        row_scale,
        predecessor,
        previous_code,
        previous_scale,
    )
    row_bound = _lt_term(
        row_index,
        rows_term,
        tag=f"{tag}_row_bound",
        variables=owned,
    )
    decoded_row_code = _beta_at_term(
        row_code_code,
        row_code_scale,
        row_index,
        row_code,
        tag=f"{tag}_decoded_row_code",
        variables=owned,
    )
    decoded_row_scale = _beta_at_term(
        row_scale_code,
        row_scale_scale,
        row_index,
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
        f"(({row_index} = 0 /\\ ({zero_row})) \\/ "
        f"exists {predecessor} {previous_code} {previous_scale}. "
        f"{row_index} = S {predecessor} /\\ "
        f"(({decoded_previous_code}) /\\ "
        f"(({decoded_previous_scale}) /\\ ({row_step}))))"
    )
    return (
        f"forall {row_index}. ({row_bound}) -> "
        f"exists {row_code} {row_scale}. "
        f"(({decoded_row_code}) /\\ (({decoded_row_scale}) /\\ "
        f"{row_kind}))"
    )


def _choose_relation_term(
    n: str,
    k: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (
        row_code_code,
        row_code_scale,
        row_scale_code,
        row_scale_scale,
        row_code,
        row_scale,
    ) = _binders(
        tag,
        variables,
        (
            "row_code_code",
            "row_code_scale",
            "row_scale_code",
            "row_scale_scale",
            "row_code",
            "row_scale",
        ),
    )
    owned = variables + (
        row_code_code,
        row_code_scale,
        row_scale_code,
        row_scale_scale,
        row_code,
        row_scale,
    )
    out_of_range = _lt_term(
        n,
        k,
        tag=f"{tag}_out_of_range",
        variables=owned,
    )
    in_range = _le_term(
        k,
        n,
        tag=f"{tag}_in_range",
        variables=owned,
    )
    table = _pascal_table_prefix_term(
        row_code_code,
        row_code_scale,
        row_scale_code,
        row_scale_scale,
        f"S ({n})",
        f"S ({n})",
        tag=f"{tag}_table",
        variables=owned,
    )
    decoded_row_code = _beta_at_term(
        row_code_code,
        row_code_scale,
        n,
        row_code,
        tag=f"{tag}_decoded_row_code",
        variables=owned,
    )
    decoded_row_scale = _beta_at_term(
        row_scale_code,
        row_scale_scale,
        n,
        row_scale,
        tag=f"{tag}_decoded_row_scale",
        variables=owned,
    )
    decoded_value = _beta_at_term(
        row_code,
        row_scale,
        k,
        value,
        tag=f"{tag}_decoded_value",
        variables=owned,
    )
    package = (
        f"exists {row_code_code} {row_code_scale} "
        f"{row_scale_code} {row_scale_scale} {row_code} {row_scale}. "
        f"(({table}) /\\ (({decoded_row_code}) /\\ "
        f"(({decoded_row_scale}) /\\ ({decoded_value}))))"
    )
    return (
        f"(({out_of_range}) /\\ {value} = 0) \\/ "
        f"(({in_range}) /\\ ({package}))"
    )


def _pascal_zero_row(code: str, scale: str, width: str, *, tag: str) -> str:
    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "row code"),
            (scale, "row scale"),
            (width, "row width"),
        )
    )
    return _pascal_zero_row_term(
        code, scale, width, tag=tag, variables=variables
    )


def _pascal_row_step(
    previous_code: str,
    previous_scale: str,
    code: str,
    scale: str,
    width: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (previous_code, "previous row code"),
            (previous_scale, "previous row scale"),
            (code, "row code"),
            (scale, "row scale"),
            (width, "row width"),
        )
    )
    return _pascal_row_step_term(
        previous_code,
        previous_scale,
        code,
        scale,
        width,
        tag=tag,
        variables=variables,
    )


def _pascal_table_prefix(
    row_code_code: str,
    row_code_scale: str,
    row_scale_code: str,
    row_scale_scale: str,
    width: str,
    rows: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (row_code_code, "row-code outer code"),
            (row_code_scale, "row-code outer scale"),
            (row_scale_code, "row-scale outer code"),
            (row_scale_scale, "row-scale outer scale"),
            (width, "table width"),
            (rows, "table row count"),
        )
    )
    return _pascal_table_prefix_term(
        row_code_code,
        row_code_scale,
        row_scale_code,
        row_scale_scale,
        width,
        rows,
        tag=tag,
        variables=variables,
    )


def _choose_relation(n: str, k: str, value: str, *, tag: str) -> str:
    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (n, "upper index"),
            (k, "lower index"),
            (value, "Choose value"),
        )
    )
    return _choose_relation_term(
        n, k, value, tag=tag, variables=variables
    )


def make_bertrand_choose_foundation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered recurrence-first Choose foundation."""

    zero_before = _pascal_zero_row(
        "b", "c", "w", tag="bpzre_before"
    )
    zero_after = _pascal_zero_row_term(
        "d",
        "e",
        "S (w)",
        tag="bpzre_after",
        variables=("b", "c", "w", "d", "e"),
    )
    zero_exists = _pascal_zero_row("b", "c", "w", tag="bpzrx_result")
    zero_previous = _pascal_zero_row(
        "b", "c", "w", tag="bpzrx_previous"
    )
    zero_successor = _pascal_zero_row_term(
        "b",
        "c",
        "S (w)",
        tag="bpzrx_successor",
        variables=("b", "c", "w"),
    )

    step_before = _pascal_row_step(
        "pb", "pc", "b", "c", "w", tag="bpsre_before"
    )
    step_after = _pascal_row_step_term(
        "pb",
        "pc",
        "d",
        "e",
        "S (w)",
        tag="bpsre_after",
        variables=("pb", "pc", "b", "c", "w", "d", "e"),
    )
    step_exists = _pascal_row_step(
        "pb", "pc", "b", "c", "w", tag="bpsrx_result"
    )
    step_previous = _pascal_row_step(
        "pb", "pc", "b", "c", "w", tag="bpsrx_previous"
    )
    step_successor = _pascal_row_step_term(
        "pb",
        "pc",
        "b",
        "c",
        "S (w)",
        tag="bpsrx_successor",
        variables=("pb", "pc", "b", "c", "w"),
    )

    table_before = _pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptpe_before"
    )
    table_after = _pascal_table_prefix_term(
        "db",
        "dc",
        "eb",
        "ec",
        "w",
        "S (r)",
        tag="bptpe_after",
        variables=(
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
        ),
    )
    table_exists = _pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptpx_result"
    )
    table_previous = _pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptpx_previous"
    )
    table_successor = _pascal_table_prefix_term(
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "S (r)",
        tag="bptpx_successor",
        variables=("bb", "bc", "sb", "sc", "w", "r"),
    )

    choose = _choose_relation("n", "k", "z", tag="bce_result")

    code_extension_variables = (
        "bb",
        "bc",
        "r",
        "x",
        "db",
        "dc",
        "i",
        "a",
    )
    code_extension = (
        "exists db dc. "
        f"(({_beta_at_term('db', 'dc', 'r', 'x', tag='bptpe_code_append', variables=code_extension_variables)}) /\\ "
        "forall i a. "
        f"({_lt_term('i', 'r', tag='bptpe_code_old_bound', variables=code_extension_variables)}) -> "
        f"({_beta_at_term('bb', 'bc', 'i', 'a', tag='bptpe_code_old', variables=code_extension_variables)}) -> "
        f"({_beta_at_term('db', 'dc', 'i', 'a', tag='bptpe_code_new', variables=code_extension_variables)}))"
    )
    scale_extension_variables = (
        "sb",
        "sc",
        "r",
        "x1",
        "eb",
        "ec",
        "i",
        "a",
    )
    scale_extension = (
        "exists eb ec. "
        f"(({_beta_at_term('eb', 'ec', 'r', 'x1', tag='bptpe_scale_append', variables=scale_extension_variables)}) /\\ "
        "forall i a. "
        f"({_lt_term('i', 'r', tag='bptpe_scale_old_bound', variables=scale_extension_variables)}) -> "
        f"({_beta_at_term('sb', 'sc', 'i', 'a', tag='bptpe_scale_old', variables=scale_extension_variables)}) -> "
        f"({_beta_at_term('eb', 'ec', 'i', 'a', tag='bptpe_scale_new', variables=scale_extension_variables)}))"
    )
    successor_code_extension_variables = (
        "bb",
        "bc",
        "r",
        "x3",
        "db",
        "dc",
        "i",
        "a",
    )
    successor_code_extension = (
        "exists db dc. "
        f"(({_beta_at_term('db', 'dc', 'r', 'x3', tag='bptpe_code_append', variables=successor_code_extension_variables)}) /\\ "
        "forall i a. "
        f"({_lt_term('i', 'r', tag='bptpe_code_old_bound', variables=successor_code_extension_variables)}) -> "
        f"({_beta_at_term('bb', 'bc', 'i', 'a', tag='bptpe_code_old', variables=successor_code_extension_variables)}) -> "
        f"({_beta_at_term('db', 'dc', 'i', 'a', tag='bptpe_code_new', variables=successor_code_extension_variables)}))"
    )
    successor_scale_extension_variables = (
        "sb",
        "sc",
        "r",
        "x4",
        "eb",
        "ec",
        "i",
        "a",
    )
    successor_scale_extension = (
        "exists eb ec. "
        f"(({_beta_at_term('eb', 'ec', 'r', 'x4', tag='bptpe_scale_append', variables=successor_scale_extension_variables)}) /\\ "
        "forall i a. "
        f"({_lt_term('i', 'r', tag='bptpe_scale_old_bound', variables=successor_scale_extension_variables)}) -> "
        f"({_beta_at_term('sb', 'sc', 'i', 'a', tag='bptpe_scale_old', variables=successor_scale_extension_variables)}) -> "
        f"({_beta_at_term('eb', 'ec', 'i', 'a', tag='bptpe_scale_new', variables=successor_scale_extension_variables)}))"
    )

    return (
        spec(
            "beta_pascal_zero_row_extend",
            "forall b c w. "
            f"({zero_before}) -> exists d e. ({zero_after})",
            (
                "zero_or_succ",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro b",
                "intro c",
                "intro w",
                "intro hrow",
                "specialize zero_or_succ w",
                "cases zero_or_succ",
                "specialize beta_prefix_extend w",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend 1",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "intro i",
                "intro hi",
                "have hsplit : i = w \\/ exists gap. gap + S i = w",
                "specialize finite_lt_succ_eq_or_lt w",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists 1",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                "left",
                "split",
                "trans w",
                "exact hsplit_left",
                "exact zero_or_succ_left",
                "refl",
                "specialize hrow i",
                "have hold : exists value. (((exists height. height + S value = S ((S i) * c)) /\\ exists quotient. b = quotient * S ((S i) * c) + value) /\\ ((i = 0 /\\ value = 1) \\/ exists predecessor. i = S predecessor /\\ value = 0))",
                "apply hrow",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "exists x2",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x2",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_left",
                "exact hold_witness_right",
                "cases zero_or_succ_right",
                "specialize beta_prefix_extend w",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend 0",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x1",
                "exists x2",
                "intro i",
                "intro hi",
                "have hsplit : i = w \\/ exists gap. gap + S i = w",
                "specialize finite_lt_succ_eq_or_lt w",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists 0",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                "right",
                "exists x",
                "split",
                "trans w",
                "exact hsplit_left",
                "exact zero_or_succ_right_witness",
                "refl",
                "specialize hrow i",
                "have hold : exists value. (((exists height. height + S value = S ((S i) * c)) /\\ exists quotient. b = quotient * S ((S i) * c) + value) /\\ ((i = 0 /\\ value = 1) \\/ exists predecessor. i = S predecessor /\\ value = 0))",
                "apply hrow",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "exists x3",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x3",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_left",
                "exact hold_witness_right",
            ),
            "Append the next fixed zero-row value while preserving all earlier cells.",
        ),
        spec(
            "beta_pascal_zero_row_exists",
            f"forall w. exists b c. ({zero_exists})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "beta_pascal_zero_row_extend",
            ),
            (
                "induction w",
                "exists 0",
                "exists 0",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
                f"have hprevious : exists b c. ({zero_previous})",
                "exact IH",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hnext : exists b c. ({zero_successor})",
                "specialize beta_pascal_zero_row_extend x",
                "specialize beta_pascal_zero_row_extend x1",
                "specialize beta_pascal_zero_row_extend w",
                "apply beta_pascal_zero_row_extend",
                "exact hprevious_witness_witness",
                "exact hnext",
            ),
            "Every finite width has a beta-coded Pascal zero row.",
        ),
        spec(
            "beta_pascal_row_step_extend",
            "forall pb pc b c w. "
            f"({step_before}) -> exists d e. ({step_after})",
            (
                "zero_or_succ",
                "beta_at_exists",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro pb",
                "intro pc",
                "intro b",
                "intro c",
                "intro w",
                "intro hrow",
                "specialize zero_or_succ w",
                "cases zero_or_succ",
                "specialize beta_prefix_extend w",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend 1",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "intro i",
                "intro hi",
                "have hsplit : i = w \\/ exists gap. gap + S i = w",
                "specialize finite_lt_succ_eq_or_lt w",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists 1",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                "left",
                "split",
                "trans w",
                "exact hsplit_left",
                "exact zero_or_succ_left",
                "refl",
                "specialize hrow i",
                "have hold : exists value. (((exists height. height + S value = S ((S i) * c)) /\\ exists quotient. b = quotient * S ((S i) * c) + value) /\\ ((i = 0 /\\ value = 1) \\/ exists p u v. i = S p /\\ (((exists h. h + S u = S ((S p) * pc)) /\\ exists q. pb = q * S ((S p) * pc) + u) /\\ (((exists h. h + S v = S ((S (S p)) * pc)) /\\ exists q. pb = q * S ((S (S p)) * pc) + v) /\\ value = u + v))))",
                "apply hrow",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "exists x2",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x2",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_left",
                "exact hold_witness_right",
                "cases zero_or_succ_right",
                "have hleft : exists u. ((exists h. h + S u = S ((S x) * pc)) /\\ exists q. pb = q * S ((S x) * pc) + u)",
                "specialize beta_at_exists pb",
                "specialize beta_at_exists pc",
                "specialize beta_at_exists x",
                "exact beta_at_exists",
                "cases hleft",
                "have hright : exists v. ((exists h. h + S v = S ((S (S x)) * pc)) /\\ exists q. pb = q * S ((S (S x)) * pc) + v)",
                "specialize beta_at_exists pb",
                "specialize beta_at_exists pc",
                "specialize beta_at_exists (S x)",
                "exact beta_at_exists",
                "cases hright",
                "specialize beta_prefix_extend w",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend (x1 + x2)",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x3",
                "exists x4",
                "intro i",
                "intro hi",
                "have hsplit : i = w \\/ exists gap. gap + S i = w",
                "specialize finite_lt_succ_eq_or_lt w",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists x1 + x2",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                "right",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "trans w",
                "exact hsplit_left",
                "exact zero_or_succ_right_witness",
                "split",
                "exact hleft_witness",
                "split",
                "exact hright_witness",
                "refl",
                "specialize hrow i",
                "have hold : exists value. (((exists height. height + S value = S ((S i) * c)) /\\ exists quotient. b = quotient * S ((S i) * c) + value) /\\ ((i = 0 /\\ value = 1) \\/ exists p u v. i = S p /\\ (((exists h. h + S u = S ((S p) * pc)) /\\ exists q. pb = q * S ((S p) * pc) + u) /\\ (((exists h. h + S v = S ((S (S p)) * pc)) /\\ exists q. pb = q * S ((S (S p)) * pc) + v) /\\ value = u + v))))",
                "apply hrow",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "exists x5",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x5",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_left",
                "exact hold_witness_right",
            ),
            "Append one Pascal successor-row value and preserve the prefix.",
        ),
        spec(
            "beta_pascal_row_step_exists",
            f"forall pb pc w. exists b c. ({step_exists})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "beta_pascal_row_step_extend",
            ),
            (
                "intro pb",
                "intro pc",
                "induction w",
                "exists 0",
                "exists 0",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
                f"have hprevious : exists b c. ({step_previous})",
                "exact IH",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hnext : exists b c. ({step_successor})",
                "specialize beta_pascal_row_step_extend pb",
                "specialize beta_pascal_row_step_extend pc",
                "specialize beta_pascal_row_step_extend x",
                "specialize beta_pascal_row_step_extend x1",
                "specialize beta_pascal_row_step_extend w",
                "apply beta_pascal_row_step_extend",
                "exact hprevious_witness_witness",
                "exact hnext",
            ),
            "Every previous beta row has a finite Pascal successor row.",
        ),
        spec(
            "beta_pascal_table_prefix_extend",
            "forall bb bc sb sc w r. "
            f"({table_before}) -> exists db dc eb ec. ({table_after})",
            (
                "zero_or_succ",
                "le_refl",
                "lt_to_le",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
                "beta_pascal_zero_row_exists",
                "beta_pascal_row_step_exists",
            ),
            (
                "intro bb",
                "intro bc",
                "intro sb",
                "intro sc",
                "intro w",
                "intro r",
                "intro htable",
                "specialize zero_or_succ r",
                "cases zero_or_succ",
                "have hzero : exists b c. (forall j. (exists gap. gap + S j = w) -> exists value. (((exists h. h + S value = S ((S j) * c)) /\\ exists q. b = q * S ((S j) * c) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists p. j = S p /\\ value = 0)))",
                "specialize beta_pascal_zero_row_exists w",
                "exact beta_pascal_zero_row_exists",
                "cases hzero",
                "cases hzero_witness",
                f"have hcode_extend : {code_extension}",
                "specialize beta_prefix_extend r",
                "specialize beta_prefix_extend bb",
                "specialize beta_prefix_extend bc",
                "specialize beta_prefix_extend x",
                "exact beta_prefix_extend",
                "cases hcode_extend",
                "cases hcode_extend_witness",
                "cases hcode_extend_witness_witness",
                f"have hscale_extend : {scale_extension}",
                "specialize beta_prefix_extend r",
                "specialize beta_prefix_extend sb",
                "specialize beta_prefix_extend sc",
                "specialize beta_prefix_extend x1",
                "exact beta_prefix_extend",
                "cases hscale_extend",
                "cases hscale_extend_witness",
                "cases hscale_extend_witness_witness",
                "exists x2",
                "exists x3",
                "exists x4",
                "exists x5",
                "intro i",
                "intro hi",
                "have hsplit : i = r \\/ exists gap. gap + S i = r",
                "specialize finite_lt_succ_eq_or_lt r",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists x",
                "exists x1",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hcode_extend_witness_witness_left",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hscale_extend_witness_witness_left",
                "left",
                "split",
                "trans r",
                "exact hsplit_left",
                "exact zero_or_succ_left",
                "exact hzero_witness_witness",
                "specialize htable i",
                "have hold : exists b c. (((exists h. h + S b = S ((S i) * bc)) /\\ exists q. bb = q * S ((S i) * bc) + b) /\\ (((exists h. h + S c = S ((S i) * sc)) /\\ exists q. sb = q * S ((S i) * sc) + c) /\\ (((i = 0 /\\ (forall j. (exists gap. gap + S j = w) -> exists value. (((exists h. h + S value = S ((S j) * c)) /\\ exists q. b = q * S ((S j) * c) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists p. j = S p /\\ value = 0)))) \\/ exists predecessor previous_code previous_scale. i = S predecessor /\\ (((exists h. h + S previous_code = S ((S predecessor) * bc)) /\\ exists q. bb = q * S ((S predecessor) * bc) + previous_code) /\\ (((exists h. h + S previous_scale = S ((S predecessor) * sc)) /\\ exists q. sb = q * S ((S predecessor) * sc) + previous_scale) /\\ forall j. (exists gap. gap + S j = w) -> exists value. (((exists h. h + S value = S ((S j) * c)) /\\ exists q. b = q * S ((S j) * c) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists p u v. j = S p /\\ (((exists h. h + S u = S ((S p) * previous_scale)) /\\ exists q. previous_code = q * S ((S p) * previous_scale) + u) /\\ (((exists h. h + S v = S ((S (S p)) * previous_scale)) /\\ exists q. previous_code = q * S ((S (S p)) * previous_scale) + v) /\\ value = u + v))))))))))",
                "apply htable",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_right",
                "exists x6",
                "exists x7",
                "split",
                "specialize hcode_extend_witness_witness_right i",
                "specialize hcode_extend_witness_witness_right x6",
                "apply hcode_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_left",
                "split",
                "specialize hscale_extend_witness_witness_right i",
                "specialize hscale_extend_witness_witness_right x7",
                "apply hscale_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_right_left",
                "cases hold_witness_witness_right_right",
                "left",
                "exact hold_witness_witness_right_right_left",
                "cases hold_witness_witness_right_right_right",
                "cases hold_witness_witness_right_right_right_witness",
                "cases hold_witness_witness_right_right_right_witness_witness",
                "cases hold_witness_witness_right_right_right_witness_witness_witness",
                "cases hold_witness_witness_right_right_right_witness_witness_witness_right",
                "cases hold_witness_witness_right_right_right_witness_witness_witness_right_right",
                "right",
                "exists x8",
                "exists x9",
                "exists x10",
                "split",
                "exact hold_witness_witness_right_right_right_witness_witness_witness_left",
                "have hpred_bound : exists gap. gap + S x8 = r",
                "have hi_le : exists gap. gap + i = r",
                "specialize lt_to_le i",
                "specialize lt_to_le r",
                "apply lt_to_le",
                "exact hsplit_right",
                "rewrite hold_witness_witness_right_right_right_witness_witness_witness_left at hi_le",
                "exact hi_le",
                "split",
                "specialize hcode_extend_witness_witness_right x8",
                "specialize hcode_extend_witness_witness_right x9",
                "apply hcode_extend_witness_witness_right",
                "exact hpred_bound",
                "exact hold_witness_witness_right_right_right_witness_witness_witness_right_left",
                "split",
                "specialize hscale_extend_witness_witness_right x8",
                "specialize hscale_extend_witness_witness_right x10",
                "apply hscale_extend_witness_witness_right",
                "exact hpred_bound",
                "exact hold_witness_witness_right_right_right_witness_witness_witness_right_right_left",
                "exact hold_witness_witness_right_right_right_witness_witness_witness_right_right_right",
                "cases zero_or_succ_right",
                "have hbound : exists gap. gap + S x = r",
                "rewrite zero_or_succ_right_witness",
                "specialize le_refl (S x)",
                "exact le_refl",
                "have hprevious : exists pb pc. (((exists h. h + S pb = S ((S x) * bc)) /\\ exists q. bb = q * S ((S x) * bc) + pb) /\\ (((exists h. h + S pc = S ((S x) * sc)) /\\ exists q. sb = q * S ((S x) * sc) + pc) /\\ (((x = 0 /\\ (forall j. (exists gap. gap + S j = w) -> exists value. (((exists h. h + S value = S ((S j) * pc)) /\\ exists q. pb = q * S ((S j) * pc) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists p. j = S p /\\ value = 0)))) \\/ exists predecessor previous_code previous_scale. x = S predecessor /\\ (((exists h. h + S previous_code = S ((S predecessor) * bc)) /\\ exists q. bb = q * S ((S predecessor) * bc) + previous_code) /\\ (((exists h. h + S previous_scale = S ((S predecessor) * sc)) /\\ exists q. sb = q * S ((S predecessor) * sc) + previous_scale) /\\ forall j. (exists gap. gap + S j = w) -> exists value. (((exists h. h + S value = S ((S j) * pc)) /\\ exists q. pb = q * S ((S j) * pc) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists p u v. j = S p /\\ (((exists h. h + S u = S ((S p) * previous_scale)) /\\ exists q. previous_code = q * S ((S p) * previous_scale) + u) /\\ (((exists h. h + S v = S ((S (S p)) * previous_scale)) /\\ exists q. previous_code = q * S ((S (S p)) * previous_scale) + v) /\\ value = u + v))))))))))",
                "specialize htable x",
                "apply htable",
                "exact hbound",
                "cases hprevious",
                "cases hprevious_witness",
                "cases hprevious_witness_witness",
                "cases hprevious_witness_witness_right",
                "have hstep : exists b c. (forall j. (exists gap. gap + S j = w) -> exists value. (((exists h. h + S value = S ((S j) * c)) /\\ exists q. b = q * S ((S j) * c) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists predecessor u v. j = S predecessor /\\ (((exists h. h + S u = S ((S predecessor) * x2)) /\\ exists q. x1 = q * S ((S predecessor) * x2) + u) /\\ (((exists h. h + S v = S ((S (S predecessor)) * x2)) /\\ exists q. x1 = q * S ((S (S predecessor)) * x2) + v) /\\ value = u + v)))))",
                "specialize beta_pascal_row_step_exists x1",
                "specialize beta_pascal_row_step_exists x2",
                "specialize beta_pascal_row_step_exists w",
                "exact beta_pascal_row_step_exists",
                "cases hstep",
                "cases hstep_witness",
                f"have hcode_extend : {successor_code_extension}",
                "specialize beta_prefix_extend r",
                "specialize beta_prefix_extend bb",
                "specialize beta_prefix_extend bc",
                "specialize beta_prefix_extend x3",
                "exact beta_prefix_extend",
                "cases hcode_extend",
                "cases hcode_extend_witness",
                "cases hcode_extend_witness_witness",
                f"have hscale_extend : {successor_scale_extension}",
                "specialize beta_prefix_extend r",
                "specialize beta_prefix_extend sb",
                "specialize beta_prefix_extend sc",
                "specialize beta_prefix_extend x4",
                "exact beta_prefix_extend",
                "cases hscale_extend",
                "cases hscale_extend_witness",
                "cases hscale_extend_witness_witness",
                "exists x5",
                "exists x6",
                "exists x7",
                "exists x8",
                "intro i",
                "intro hi",
                "have hsplit : i = r \\/ exists gap. gap + S i = r",
                "specialize finite_lt_succ_eq_or_lt r",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists x3",
                "exists x4",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hcode_extend_witness_witness_left",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hscale_extend_witness_witness_left",
                "right",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "trans r",
                "exact hsplit_left",
                "exact zero_or_succ_right_witness",
                "have hpred_bound : exists gap. gap + S x = r",
                "rewrite zero_or_succ_right_witness",
                "specialize le_refl (S x)",
                "exact le_refl",
                "split",
                "specialize hcode_extend_witness_witness_right x",
                "specialize hcode_extend_witness_witness_right x1",
                "apply hcode_extend_witness_witness_right",
                "exact hpred_bound",
                "exact hprevious_witness_witness_left",
                "split",
                "specialize hscale_extend_witness_witness_right x",
                "specialize hscale_extend_witness_witness_right x2",
                "apply hscale_extend_witness_witness_right",
                "exact hpred_bound",
                "exact hprevious_witness_witness_right_left",
                "exact hstep_witness_witness",
                "specialize htable i",
                "have hold : exists b c. (((exists h. h + S b = S ((S i) * bc)) /\\ exists q. bb = q * S ((S i) * bc) + b) /\\ (((exists h. h + S c = S ((S i) * sc)) /\\ exists q. sb = q * S ((S i) * sc) + c) /\\ (((i = 0 /\\ (forall j. (exists gap. gap + S j = w) -> exists value. (((exists h. h + S value = S ((S j) * c)) /\\ exists q. b = q * S ((S j) * c) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists p. j = S p /\\ value = 0)))) \\/ exists predecessor previous_code previous_scale. i = S predecessor /\\ (((exists h. h + S previous_code = S ((S predecessor) * bc)) /\\ exists q. bb = q * S ((S predecessor) * bc) + previous_code) /\\ (((exists h. h + S previous_scale = S ((S predecessor) * sc)) /\\ exists q. sb = q * S ((S predecessor) * sc) + previous_scale) /\\ forall j. (exists gap. gap + S j = w) -> exists value. (((exists h. h + S value = S ((S j) * c)) /\\ exists q. b = q * S ((S j) * c) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists p u v. j = S p /\\ (((exists h. h + S u = S ((S p) * previous_scale)) /\\ exists q. previous_code = q * S ((S p) * previous_scale) + u) /\\ (((exists h. h + S v = S ((S (S p)) * previous_scale)) /\\ exists q. previous_code = q * S ((S (S p)) * previous_scale) + v) /\\ value = u + v))))))))))",
                "apply htable",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_right",
                "exists x9",
                "exists x10",
                "split",
                "specialize hcode_extend_witness_witness_right i",
                "specialize hcode_extend_witness_witness_right x9",
                "apply hcode_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_left",
                "split",
                "specialize hscale_extend_witness_witness_right i",
                "specialize hscale_extend_witness_witness_right x10",
                "apply hscale_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_right_left",
                "cases hold_witness_witness_right_right",
                "left",
                "exact hold_witness_witness_right_right_left",
                "cases hold_witness_witness_right_right_right",
                "cases hold_witness_witness_right_right_right_witness",
                "cases hold_witness_witness_right_right_right_witness_witness",
                "cases hold_witness_witness_right_right_right_witness_witness_witness",
                "cases hold_witness_witness_right_right_right_witness_witness_witness_right",
                "cases hold_witness_witness_right_right_right_witness_witness_witness_right_right",
                "right",
                "exists x11",
                "exists x12",
                "exists x13",
                "split",
                "exact hold_witness_witness_right_right_right_witness_witness_witness_left",
                "have hpred_bound : exists gap. gap + S x11 = r",
                "have hi_le : exists gap. gap + i = r",
                "specialize lt_to_le i",
                "specialize lt_to_le r",
                "apply lt_to_le",
                "exact hsplit_right",
                "rewrite hold_witness_witness_right_right_right_witness_witness_witness_left at hi_le",
                "exact hi_le",
                "split",
                "specialize hcode_extend_witness_witness_right x11",
                "specialize hcode_extend_witness_witness_right x12",
                "apply hcode_extend_witness_witness_right",
                "exact hpred_bound",
                "exact hold_witness_witness_right_right_right_witness_witness_witness_right_left",
                "split",
                "specialize hscale_extend_witness_witness_right x11",
                "specialize hscale_extend_witness_witness_right x13",
                "apply hscale_extend_witness_witness_right",
                "exact hpred_bound",
                "exact hold_witness_witness_right_right_right_witness_witness_witness_right_right_left",
                "exact hold_witness_witness_right_right_right_witness_witness_witness_right_right_right",
            ),
            "Append one semantic Pascal row to both outer beta prefixes.",
        ),
        spec(
            "beta_pascal_table_prefix_exists",
            f"forall w r. exists bb bc sb sc. ({table_exists})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "beta_pascal_table_prefix_extend",
            ),
            (
                "intro w",
                "induction r",
                "exists 0",
                "exists 0",
                "exists 0",
                "exists 0",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
                f"have hprevious : exists bb bc sb sc. ({table_previous})",
                "exact IH",
                "cases hprevious",
                "cases hprevious_witness",
                "cases hprevious_witness_witness",
                "cases hprevious_witness_witness_witness",
                f"have hnext : exists bb bc sb sc. ({table_successor})",
                "specialize beta_pascal_table_prefix_extend x",
                "specialize beta_pascal_table_prefix_extend x1",
                "specialize beta_pascal_table_prefix_extend x2",
                "specialize beta_pascal_table_prefix_extend x3",
                "specialize beta_pascal_table_prefix_extend w",
                "specialize beta_pascal_table_prefix_extend r",
                "apply beta_pascal_table_prefix_extend",
                "exact hprevious_witness_witness_witness_witness",
                "exact hnext",
            ),
            "Every finite width and height has a nested beta Pascal table.",
        ),
        spec(
            "choose_exists",
            f"forall n k. exists z. ({choose})",
            (
                "le_or_lt",
                "beta_at_exists",
                "beta_pascal_table_prefix_exists",
            ),
            (
                "intro n",
                "intro k",
                "specialize le_or_lt k",
                "specialize le_or_lt n",
                "cases le_or_lt",
                "have htable : exists bb bc sb sc. (forall i. (exists gap. gap + S i = S n) -> exists b c. (((exists h. h + S b = S ((S i) * bc)) /\\ exists q. bb = q * S ((S i) * bc) + b) /\\ (((exists h. h + S c = S ((S i) * sc)) /\\ exists q. sb = q * S ((S i) * sc) + c) /\\ (((i = 0 /\\ (forall j. (exists gap. gap + S j = S n) -> exists value. (((exists h. h + S value = S ((S j) * c)) /\\ exists q. b = q * S ((S j) * c) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists p. j = S p /\\ value = 0)))) \\/ exists predecessor previous_code previous_scale. i = S predecessor /\\ (((exists h. h + S previous_code = S ((S predecessor) * bc)) /\\ exists q. bb = q * S ((S predecessor) * bc) + previous_code) /\\ (((exists h. h + S previous_scale = S ((S predecessor) * sc)) /\\ exists q. sb = q * S ((S predecessor) * sc) + previous_scale) /\\ forall j. (exists gap. gap + S j = S n) -> exists value. (((exists h. h + S value = S ((S j) * c)) /\\ exists q. b = q * S ((S j) * c) + value) /\\ ((j = 0 /\\ value = 1) \\/ exists p u v. j = S p /\\ (((exists h. h + S u = S ((S p) * previous_scale)) /\\ exists q. previous_code = q * S ((S p) * previous_scale) + u) /\\ (((exists h. h + S v = S ((S (S p)) * previous_scale)) /\\ exists q. previous_code = q * S ((S (S p)) * previous_scale) + v) /\\ value = u + v)))))))))))",
                "specialize beta_pascal_table_prefix_exists (S n)",
                "specialize beta_pascal_table_prefix_exists (S n)",
                "exact beta_pascal_table_prefix_exists",
                "cases htable",
                "cases htable_witness",
                "cases htable_witness_witness",
                "cases htable_witness_witness_witness",
                "have hrow_code : exists b. ((exists h. h + S b = S ((S n) * x1)) /\\ exists q. x = q * S ((S n) * x1) + b)",
                "specialize beta_at_exists x",
                "specialize beta_at_exists x1",
                "specialize beta_at_exists n",
                "exact beta_at_exists",
                "cases hrow_code",
                "have hrow_scale : exists c. ((exists h. h + S c = S ((S n) * x3)) /\\ exists q. x2 = q * S ((S n) * x3) + c)",
                "specialize beta_at_exists x2",
                "specialize beta_at_exists x3",
                "specialize beta_at_exists n",
                "exact beta_at_exists",
                "cases hrow_scale",
                "have hvalue : exists z. ((exists h. h + S z = S ((S k) * x5)) /\\ exists q. x4 = q * S ((S k) * x5) + z)",
                "specialize beta_at_exists x4",
                "specialize beta_at_exists x5",
                "specialize beta_at_exists k",
                "exact beta_at_exists",
                "cases hvalue",
                "exists x6",
                "right",
                "split",
                "exact le_or_lt_left",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "exists x4",
                "exists x5",
                "split",
                "exact htable_witness_witness_witness_witness",
                "split",
                "exact hrow_code_witness",
                "split",
                "exact hrow_scale_witness",
                "exact hvalue_witness",
                "exists 0",
                "left",
                "split",
                "exact le_or_lt_right",
                "refl",
            ),
            "The recurrence-defined Choose relation has a value for every pair.",
        ),
    )


__all__ = ["make_bertrand_choose_foundation_candidate_theorems"]
