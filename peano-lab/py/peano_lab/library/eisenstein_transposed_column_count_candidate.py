"""Beta-code and sum the constructed Eisenstein transposed-column counts.

The whole-column layer constructs, for each original row index ``i < h``, a
provenance-carrying transposed column whose count complements the original row
count to ``k``.  This module applies the same concrete beta-prefix induction
one level higher: it beta-codes those column counts across ``i < h`` while
retaining the original outer entry, its semantic row witness, the complete
column prefix, its ``BitCount``, and the equation ``n+m=k``.

The resulting outer code admits an ordinary relational ``Sum``.  A decoded
projection theorem recovers the exact pointwise partition needed by finite
sum additivity.  No raw beta-code equality or Fubini conclusion is asserted;
identifying this column-count sum with the swapped row-count sum remains the
genuine transpose theorem.

Every helper expands before parsing to unchanged first-order PA.  Candidates
are constructive, dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_division_threshold_candidate import _lt_term
from .eisenstein_rectangle_count_candidate import (
    eisenstein_rectangle_row_count_prefix,
    eisenstein_row_count_witness,
)
from .eisenstein_transposed_column_candidate import (
    eisenstein_transposed_column_prefix,
)
from .finite_fold_surface import beta_at, bit_count, repeat_relation, sum_relation


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
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
    names = tuple(f"etcc_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated transposed-count binder captures an argument")
    return names


def _column_count_witness_term(
    prime_p: str,
    prime_q: str,
    height: str,
    width: str,
    first_outer_code: str,
    first_outer_scale: str,
    second_outer_code: str,
    second_outer_scale: str,
    row_index: str,
    column_count: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row_count, column_code, column_scale = _binders(
        tag, variables, ("row_count", "column_code", "column_scale")
    )
    first_entry = beta_at(
        first_outer_code,
        first_outer_scale,
        row_index,
        row_count,
        tag=f"etcc_{tag}_first_entry",
    )
    row_semantics = eisenstein_row_count_witness(
        prime_p,
        prime_q,
        width,
        row_index,
        row_count,
        tag=f"etcc_{tag}_row_semantics",
    )
    column = eisenstein_transposed_column_prefix(
        prime_p,
        prime_q,
        height,
        second_outer_code,
        second_outer_scale,
        row_index,
        column_code,
        column_scale,
        width,
        tag=f"etcc_{tag}_column",
    )
    count_relation = bit_count(
        column_code,
        column_scale,
        width,
        column_count,
        tag=f"etcc_{tag}_column_count",
    )
    return (
        f"exists {row_count} {column_code} {column_scale}. "
        f"(((({first_entry}) /\\ ({row_semantics})) /\\ ({column})) /\\ "
        f"(({count_relation}) /\\ {row_count} + {column_count} = {width}))"
    )


def eisenstein_transposed_column_count_witness(
    prime_p: str,
    prime_q: str,
    height: str,
    width: str,
    first_outer_code: str,
    first_outer_scale: str,
    second_outer_code: str,
    second_outer_scale: str,
    row_index: str,
    column_count: str,
    *,
    tag: str,
) -> str:
    """Expand one column count with its row/column partition provenance."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (height, "rectangle height"),
            (width, "rectangle width"),
            (first_outer_code, "first outer code"),
            (first_outer_scale, "first outer scale"),
            (second_outer_code, "second outer code"),
            (second_outer_scale, "second outer scale"),
            (row_index, "row index"),
            (column_count, "column count"),
        )
    )
    return _column_count_witness_term(
        prime_p,
        prime_q,
        height,
        width,
        first_outer_code,
        first_outer_scale,
        second_outer_code,
        second_outer_scale,
        row_index,
        column_count,
        tag=tag,
        variables=variables,
    )


def _column_count_choices_term(
    prime_p: str,
    prime_q: str,
    height: str,
    width: str,
    first_outer_code: str,
    first_outer_scale: str,
    second_outer_code: str,
    second_outer_scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row_index, count = _binders(tag, variables, ("row_index", "count"))
    owned = variables + (row_index, count)
    bound = _lt_term(
        row_index,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    witness = _column_count_witness_term(
        prime_p,
        prime_q,
        height,
        width,
        first_outer_code,
        first_outer_scale,
        second_outer_code,
        second_outer_scale,
        row_index,
        count,
        tag=f"{tag}_witness",
        variables=owned,
    )
    return f"forall {row_index}. ({bound}) -> exists {count}. ({witness})"


def eisenstein_transposed_column_count_choices(
    prime_p: str,
    prime_q: str,
    height: str,
    width: str,
    first_outer_code: str,
    first_outer_scale: str,
    second_outer_code: str,
    second_outer_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand bounded choices of fully witnessed transposed-column counts."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (height, "rectangle height"),
            (width, "rectangle width"),
            (first_outer_code, "first outer code"),
            (first_outer_scale, "first outer scale"),
            (second_outer_code, "second outer code"),
            (second_outer_scale, "second outer scale"),
            (length, "outer length"),
        )
    )
    return _column_count_choices_term(
        prime_p,
        prime_q,
        height,
        width,
        first_outer_code,
        first_outer_scale,
        second_outer_code,
        second_outer_scale,
        length,
        tag=tag,
        variables=variables,
    )


def _column_count_prefix_term(
    prime_p: str,
    prime_q: str,
    height: str,
    width: str,
    first_outer_code: str,
    first_outer_scale: str,
    second_outer_code: str,
    second_outer_scale: str,
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row_index, count = _binders(tag, variables, ("row_index", "count"))
    owned = variables + (row_index, count)
    bound = _lt_term(
        row_index,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    decoded = beta_at(code, scale, row_index, count, tag=f"etcc_{tag}_decoded")
    witness = _column_count_witness_term(
        prime_p,
        prime_q,
        height,
        width,
        first_outer_code,
        first_outer_scale,
        second_outer_code,
        second_outer_scale,
        row_index,
        count,
        tag=f"{tag}_witness",
        variables=owned,
    )
    return (
        f"forall {row_index}. ({bound}) -> exists {count}. "
        f"(({decoded}) /\\ ({witness}))"
    )


def eisenstein_transposed_column_count_prefix(
    prime_p: str,
    prime_q: str,
    height: str,
    width: str,
    first_outer_code: str,
    first_outer_scale: str,
    second_outer_code: str,
    second_outer_scale: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a beta prefix of provenance-carrying column counts."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (height, "rectangle height"),
            (width, "rectangle width"),
            (first_outer_code, "first outer code"),
            (first_outer_scale, "first outer scale"),
            (second_outer_code, "second outer code"),
            (second_outer_scale, "second outer scale"),
            (code, "column-count code"),
            (scale, "column-count scale"),
            (length, "outer length"),
        )
    )
    return _column_count_prefix_term(
        prime_p,
        prime_q,
        height,
        width,
        first_outer_code,
        first_outer_scale,
        second_outer_code,
        second_outer_scale,
        code,
        scale,
        length,
        tag=tag,
        variables=variables,
    )


def _successor_column_count_prefix(
    prime_p: str,
    prime_q: str,
    height: str,
    width: str,
    first_outer_code: str,
    first_outer_scale: str,
    second_outer_code: str,
    second_outer_scale: str,
    code: str,
    scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"), (prime_q, "second prime"),
            (height, "rectangle height"), (width, "rectangle width"),
            (first_outer_code, "first outer code"),
            (first_outer_scale, "first outer scale"),
            (second_outer_code, "second outer code"),
            (second_outer_scale, "second outer scale"),
            (code, "column-count code"), (scale, "column-count scale"),
            (predecessor, "outer predecessor"),
        )
    )
    return _column_count_prefix_term(
        prime_p, prime_q, height, width,
        first_outer_code, first_outer_scale, second_outer_code, second_outer_scale,
        code, scale, f"S {predecessor}", tag=tag, variables=variables,
    )


def make_eisenstein_transposed_column_count_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build outer column-count coding, projection, and Sum existence."""

    first_outer = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "ab", "ac", "h", tag="column_count_first_outer"
    )
    second_outer = eisenstein_rectangle_row_count_prefix(
        "q", "p", "h", "bb", "bc", "k", tag="column_count_second_outer"
    )
    choices = eisenstein_transposed_column_count_choices(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "h",
        tag="column_count_choices",
    )
    first_entry = beta_at(
        "ab", "ac", "i", "n", tag="column_count_first_entry"
    )
    first_semantic = eisenstein_row_count_witness(
        "p", "q", "k", "i", "n", tag="column_count_first_semantic"
    )
    first_package = f"exists n. (({first_entry}) /\\ ({first_semantic}))"
    row_bound = _lt_term(
        "i", "h", tag="column_count_row_bound",
        variables=("p", "q", "h", "k", "ab", "ac", "bb", "bc", "i"),
    )

    prefix_before = eisenstein_transposed_column_count_prefix(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "db", "dc", "l",
        tag="column_count_extend_before",
    )
    last_witness = eisenstein_transposed_column_count_witness(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "l", "m",
        tag="column_count_extend_last",
    )
    prefix_after = _successor_column_count_prefix(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "u", "v", "l",
        tag="column_count_extend_after",
    )
    old_entry = beta_at(
        "db", "dc", "i", "oldcount", tag="column_count_extend_old_entry"
    )
    old_witness = eisenstein_transposed_column_count_witness(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "i", "oldcount",
        tag="column_count_extend_old_witness",
    )

    prefix_result = (
        "exists db dc. "
        f"({eisenstein_transposed_column_count_prefix('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'db', 'dc', 'h', tag='column_count_exists_result')})"
    )
    previous_choices = eisenstein_transposed_column_count_choices(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "l",
        tag="column_count_exists_previous_choices",
    )
    previous_prefix = (
        "exists db dc. "
        f"({eisenstein_transposed_column_count_prefix('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'db', 'dc', 'l', tag='column_count_exists_previous_prefix')})"
    )
    successor_prefix = (
        "exists db dc. "
        f"({_successor_column_count_prefix('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'db', 'dc', 'l', tag='column_count_exists_successor')})"
    )

    semantic_prefix = eisenstein_transposed_column_count_prefix(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "db", "dc", "h",
        tag="column_count_semantic_prefix",
    )
    decoded_entry = beta_at(
        "db", "dc", "i", "m", tag="column_count_decoded_entry"
    )
    decoded_witness = eisenstein_transposed_column_count_witness(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "i", "m",
        tag="column_count_decoded_witness",
    )
    total_sum = sum_relation(
        "db", "dc", "h", "M", tag="column_count_total_sum"
    )
    total_result = (
        "exists db dc M. "
        f"(({eisenstein_transposed_column_count_prefix('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'db', 'dc', 'h', tag='column_count_total_prefix')}) /\\ "
        f"({total_sum}))"
    )
    constant_prefix = repeat_relation(
        "kb", "kc", "k", "h", tag="column_count_constant_prefix"
    )
    constant_entry = beta_at(
        "kb", "kc", "i", "c", tag="column_count_constant_entry"
    )
    first_sum = sum_relation(
        "ab", "ac", "h", "N", tag="column_count_partition_first_sum"
    )
    partition_total_result = (
        "exists db dc M. "
        f"(({eisenstein_transposed_column_count_prefix('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'db', 'dc', 'h', tag='column_count_partition_total_prefix')}) /\\ "
        f"(({sum_relation('db', 'dc', 'h', 'M', tag='column_count_partition_total_sum')}) /\\ "
        "N + M = h * k))"
    )

    return (
        spec(
            "eisenstein_transposed_column_count_choices",
            "forall p q h k ab ac bb bc. "
            f"({first_outer}) -> ({second_outer}) -> ({choices})",
            ("eisenstein_row_transposed_column_count_partition",),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro hfirst", "intro hsecond", "intro i", "intro hi",
                f"have hrow : {first_package}",
                "specialize hfirst i", "apply hfirst", "exact hi",
                "cases hrow", "cases hrow_witness",
                "cases hrow_witness_right",
                "cases hrow_witness_right_witness",
                "cases hrow_witness_right_witness_witness",
                "have hpartition : exists z e m. "
                f"(({eisenstein_transposed_column_prefix('p', 'q', 'h', 'bb', 'bc', 'i', 'z', 'e', 'k', tag='column_count_choice_partition_prefix')}) /\\ "
                f"(({bit_count('z', 'e', 'k', 'm', tag='column_count_choice_partition_count')}) /\\ x + m = k))",
                "specialize eisenstein_row_transposed_column_count_partition p",
                "specialize eisenstein_row_transposed_column_count_partition q",
                "specialize eisenstein_row_transposed_column_count_partition h",
                "specialize eisenstein_row_transposed_column_count_partition k",
                "specialize eisenstein_row_transposed_column_count_partition i",
                "specialize eisenstein_row_transposed_column_count_partition x1",
                "specialize eisenstein_row_transposed_column_count_partition x2",
                "specialize eisenstein_row_transposed_column_count_partition bb",
                "specialize eisenstein_row_transposed_column_count_partition bc",
                "specialize eisenstein_row_transposed_column_count_partition x",
                "apply eisenstein_row_transposed_column_count_partition",
                "exact hrow_witness_right_witness_witness_left",
                "exact hrow_witness_right_witness_witness_right",
                "exact hsecond", "exact hi",
                "cases hpartition", "cases hpartition_witness",
                "cases hpartition_witness_witness",
                "cases hpartition_witness_witness_witness",
                "cases hpartition_witness_witness_witness_right",
                "exists x5", "exists x", "exists x3", "exists x4",
                "split", "split", "split",
                "exact hrow_witness_left",
                "exists x1", "exists x2",
                "exact hrow_witness_right_witness_witness",
                "exact hpartition_witness_witness_witness_left",
                "split",
                "exact hpartition_witness_witness_witness_right_left",
                "exact hpartition_witness_witness_witness_right_right",
            ),
            "Every original row index has a fully witnessed complementary column count.",
        ),
        spec(
            "eisenstein_transposed_column_count_prefix_extend",
            "forall p q h k ab ac bb bc db dc l. "
            f"({prefix_before}) -> (exists m. ({last_witness})) -> "
            f"exists u v. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro db", "intro dc", "intro l", "intro hprefix",
                "intro hlast", "cases hlast",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend db",
                "specialize beta_prefix_extend dc",
                "specialize beta_prefix_extend x",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x1", "exists x2", "intro i", "intro hi",
                "have hsplit : i = l \/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "exists x", "split",
                "rewrite hsplit_left", "rewrite hsplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                # The witness contains eight semantic occurrences of its row index.
                "rewrite hsplit_left", "rewrite hsplit_left",
                "rewrite hsplit_left", "rewrite hsplit_left",
                "rewrite hsplit_left", "rewrite hsplit_left",
                "rewrite hsplit_left", "rewrite hsplit_left",
                "exact hlast_witness",
                f"have hold : exists oldcount. (({old_entry}) /\\ ({old_witness}))",
                "specialize hprefix i", "apply hprefix", "exact hsplit_right",
                "cases hold", "cases hold_witness", "exists x3", "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x3",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right", "exact hold_witness_left",
                "exact hold_witness_right",
            ),
            "Append one fully witnessed column count to the outer count prefix.",
        ),
        spec(
            "eisenstein_transposed_column_count_prefix_exists",
            f"forall p q h k ab ac bb bc l. ({previous_choices}) -> "
            "exists db dc. "
            f"({eisenstein_transposed_column_count_prefix('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'db', 'dc', 'l', tag='column_count_exists_general_result')})",
            (
                "add_eq_zero_right", "succ_ne_zero", "le_succ", "le_refl",
                "eisenstein_transposed_column_count_prefix_extend",
            ),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "induction l", "intro hchoices",
                "exists 0", "exists 0", "intro i", "intro hi", "exfalso",
                "cases hi", "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right", "exact hi_witness",
                "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hsi",
                "intro hchoices",
                f"have hprevious : {previous_choices}",
                "intro i", "intro hi", "specialize hchoices i",
                "apply hchoices", "specialize le_succ (S i)",
                "specialize le_succ l", "apply le_succ", "exact hi",
                f"have hprefix : {previous_prefix}",
                "apply IH", "exact hprevious",
                "cases hprefix", "cases hprefix_witness",
                f"have hlast : exists m. ({eisenstein_transposed_column_count_witness('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'l', 'm', tag='column_count_exists_last')})",
                "specialize hchoices l", "apply hchoices",
                "specialize le_refl (S l)", "exact le_refl",
                f"have hnext : {successor_prefix}",
                "specialize eisenstein_transposed_column_count_prefix_extend p",
                "specialize eisenstein_transposed_column_count_prefix_extend q",
                "specialize eisenstein_transposed_column_count_prefix_extend h",
                "specialize eisenstein_transposed_column_count_prefix_extend k",
                "specialize eisenstein_transposed_column_count_prefix_extend ab",
                "specialize eisenstein_transposed_column_count_prefix_extend ac",
                "specialize eisenstein_transposed_column_count_prefix_extend bb",
                "specialize eisenstein_transposed_column_count_prefix_extend bc",
                "specialize eisenstein_transposed_column_count_prefix_extend x",
                "specialize eisenstein_transposed_column_count_prefix_extend x1",
                "specialize eisenstein_transposed_column_count_prefix_extend l",
                "apply eisenstein_transposed_column_count_prefix_extend",
                "exact hprefix_witness_witness", "exact hlast", "exact hnext",
            ),
            "Every bounded family of column-count witnesses has one outer beta prefix.",
        ),
        spec(
            "eisenstein_transposed_column_count_decoded_witness",
            "forall p q h k ab ac bb bc db dc i m. "
            f"({semantic_prefix}) -> ({row_bound}) -> ({decoded_entry}) -> "
            f"({decoded_witness})",
            ("beta_at_unique",),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro db", "intro dc", "intro i", "intro m",
                "intro hprefix", "intro hi", "intro hm",
                "have hstored : exists stored. "
                f"(({beta_at('db', 'dc', 'i', 'stored', tag='column_count_decoded_stored')}) /\\ "
                f"({eisenstein_transposed_column_count_witness('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'i', 'stored', tag='column_count_decoded_stored_witness')}))",
                "specialize hprefix i", "apply hprefix", "exact hi",
                "cases hstored", "cases hstored_witness",
                "have hsm : x = m",
                "specialize beta_at_unique db", "specialize beta_at_unique dc",
                "specialize beta_at_unique i", "specialize beta_at_unique x",
                "specialize beta_at_unique m", "apply beta_at_unique",
                "exact hstored_witness_left", "exact hm",
                "rewrite hsm at hstored_witness_right",
                "rewrite hsm at hstored_witness_right",
                "rewrite hsm at hstored_witness_right",
                "exact hstored_witness_right",
            ),
            "Every decoded column-count outer entry recovers its full partition witness.",
        ),
        spec(
            "eisenstein_transposed_column_count_total_exists",
            "forall p q h k ab ac bb bc. "
            f"({first_outer}) -> ({second_outer}) -> ({total_result})",
            (
                "eisenstein_transposed_column_count_choices",
                "eisenstein_transposed_column_count_prefix_exists",
                "beta_sum_exists",
            ),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro hfirst", "intro hsecond",
                f"have hchoices : {choices}",
                "specialize eisenstein_transposed_column_count_choices p",
                "specialize eisenstein_transposed_column_count_choices q",
                "specialize eisenstein_transposed_column_count_choices h",
                "specialize eisenstein_transposed_column_count_choices k",
                "specialize eisenstein_transposed_column_count_choices ab",
                "specialize eisenstein_transposed_column_count_choices ac",
                "specialize eisenstein_transposed_column_count_choices bb",
                "specialize eisenstein_transposed_column_count_choices bc",
                "apply eisenstein_transposed_column_count_choices",
                "exact hfirst", "exact hsecond",
                f"have hprefix : {prefix_result}",
                "specialize eisenstein_transposed_column_count_prefix_exists p",
                "specialize eisenstein_transposed_column_count_prefix_exists q",
                "specialize eisenstein_transposed_column_count_prefix_exists h",
                "specialize eisenstein_transposed_column_count_prefix_exists k",
                "specialize eisenstein_transposed_column_count_prefix_exists ab",
                "specialize eisenstein_transposed_column_count_prefix_exists ac",
                "specialize eisenstein_transposed_column_count_prefix_exists bb",
                "specialize eisenstein_transposed_column_count_prefix_exists bc",
                "specialize eisenstein_transposed_column_count_prefix_exists h",
                "apply eisenstein_transposed_column_count_prefix_exists",
                "exact hchoices",
                "cases hprefix", "cases hprefix_witness",
                "have hsum : exists M. "
                f"({sum_relation('x', 'x1', 'h', 'M', tag='column_count_total_sum_exists')})",
                "specialize beta_sum_exists x", "specialize beta_sum_exists x1",
                "specialize beta_sum_exists h", "exact beta_sum_exists",
                "cases hsum", "exists x", "exists x1", "exists x2", "split",
                "exact hprefix_witness_witness", "exact hsum_witness",
            ),
            "The provenance-carrying column counts have an exact relational outer Sum.",
        ),
        spec(
            "eisenstein_transposed_column_count_decoded_partition",
            "forall p q h k ab ac bb bc db dc i n m. "
            f"({semantic_prefix}) -> ({row_bound}) -> ({first_entry}) -> "
            f"({decoded_entry}) -> n + m = k",
            (
                "eisenstein_transposed_column_count_decoded_witness",
                "beta_at_unique",
            ),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro db", "intro dc", "intro i", "intro n", "intro m",
                "intro hprefix", "intro hi", "intro hn", "intro hm",
                f"have hwitness : {decoded_witness}",
                "specialize eisenstein_transposed_column_count_decoded_witness p",
                "specialize eisenstein_transposed_column_count_decoded_witness q",
                "specialize eisenstein_transposed_column_count_decoded_witness h",
                "specialize eisenstein_transposed_column_count_decoded_witness k",
                "specialize eisenstein_transposed_column_count_decoded_witness ab",
                "specialize eisenstein_transposed_column_count_decoded_witness ac",
                "specialize eisenstein_transposed_column_count_decoded_witness bb",
                "specialize eisenstein_transposed_column_count_decoded_witness bc",
                "specialize eisenstein_transposed_column_count_decoded_witness db",
                "specialize eisenstein_transposed_column_count_decoded_witness dc",
                "specialize eisenstein_transposed_column_count_decoded_witness i",
                "specialize eisenstein_transposed_column_count_decoded_witness m",
                "apply eisenstein_transposed_column_count_decoded_witness",
                "exact hprefix", "exact hi", "exact hm",
                "cases hwitness", "cases hwitness_witness",
                "cases hwitness_witness_witness",
                "cases hwitness_witness_witness_witness",
                "cases hwitness_witness_witness_witness_left",
                "cases hwitness_witness_witness_witness_left_left",
                "cases hwitness_witness_witness_witness_right",
                "have hroweq : x = n",
                "specialize beta_at_unique ab", "specialize beta_at_unique ac",
                "specialize beta_at_unique i", "specialize beta_at_unique x",
                "specialize beta_at_unique n", "apply beta_at_unique",
                "exact hwitness_witness_witness_witness_left_left_left",
                "exact hn",
                "rewrite hroweq at hwitness_witness_witness_witness_right_right",
                "exact hwitness_witness_witness_witness_right_right",
            ),
            "Decoded original-row and constructed-column counts partition the row width.",
        ),
        spec(
            "eisenstein_transposed_column_count_matches_decoded_constant",
            "forall p q h k ab ac bb bc db dc kb kc i n m c. "
            f"({semantic_prefix}) -> ({row_bound}) -> ({first_entry}) -> "
            f"({decoded_entry}) -> ({constant_prefix}) -> "
            f"({constant_entry}) -> n + m = c",
            (
                "eisenstein_transposed_column_count_decoded_partition",
                "beta_repeat_entry_eq",
            ),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro db", "intro dc", "intro kb", "intro kc",
                "intro i", "intro n", "intro m", "intro c",
                "intro hprefix", "intro hi", "intro hn", "intro hm",
                "intro hrepeat", "intro hc",
                "have hpartition : n + m = k",
                "specialize eisenstein_transposed_column_count_decoded_partition p",
                "specialize eisenstein_transposed_column_count_decoded_partition q",
                "specialize eisenstein_transposed_column_count_decoded_partition h",
                "specialize eisenstein_transposed_column_count_decoded_partition k",
                "specialize eisenstein_transposed_column_count_decoded_partition ab",
                "specialize eisenstein_transposed_column_count_decoded_partition ac",
                "specialize eisenstein_transposed_column_count_decoded_partition bb",
                "specialize eisenstein_transposed_column_count_decoded_partition bc",
                "specialize eisenstein_transposed_column_count_decoded_partition db",
                "specialize eisenstein_transposed_column_count_decoded_partition dc",
                "specialize eisenstein_transposed_column_count_decoded_partition i",
                "specialize eisenstein_transposed_column_count_decoded_partition n",
                "specialize eisenstein_transposed_column_count_decoded_partition m",
                "apply eisenstein_transposed_column_count_decoded_partition",
                "exact hprefix", "exact hi", "exact hn", "exact hm",
                "have hck : c = k",
                "specialize beta_repeat_entry_eq kb",
                "specialize beta_repeat_entry_eq kc",
                "specialize beta_repeat_entry_eq k",
                "specialize beta_repeat_entry_eq h",
                "specialize beta_repeat_entry_eq i",
                "specialize beta_repeat_entry_eq c",
                "apply beta_repeat_entry_eq",
                "exact hrepeat", "exact hi", "exact hc",
                "trans k", "exact hpartition", "symm", "exact hck",
            ),
            "The decoded row and column counts add to the decoded entry of any constant-k prefix.",
        ),
        spec(
            "eisenstein_rectangle_plus_column_count_total",
            "forall p q h k ab ac bb bc N. "
            f"({first_outer}) -> ({second_outer}) -> ({first_sum}) -> "
            f"({partition_total_result})",
            (
                "eisenstein_transposed_column_count_total_exists",
                "beta_repeat_sum_exists_exact",
                "eisenstein_transposed_column_count_matches_decoded_constant",
                "beta_sum_pointwise_add",
            ),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc", "intro N",
                "intro hfirst", "intro hsecond", "intro hfirst_sum",
                "have hcolumns : exists db dc M. "
                f"(({eisenstein_transposed_column_count_prefix('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'db', 'dc', 'h', tag='column_count_partition_columns_prefix')}) /\\ "
                f"({sum_relation('db', 'dc', 'h', 'M', tag='column_count_partition_columns_sum')}))",
                "specialize eisenstein_transposed_column_count_total_exists p",
                "specialize eisenstein_transposed_column_count_total_exists q",
                "specialize eisenstein_transposed_column_count_total_exists h",
                "specialize eisenstein_transposed_column_count_total_exists k",
                "specialize eisenstein_transposed_column_count_total_exists ab",
                "specialize eisenstein_transposed_column_count_total_exists ac",
                "specialize eisenstein_transposed_column_count_total_exists bb",
                "specialize eisenstein_transposed_column_count_total_exists bc",
                "apply eisenstein_transposed_column_count_total_exists",
                "exact hfirst", "exact hsecond",
                "cases hcolumns", "cases hcolumns_witness",
                "cases hcolumns_witness_witness",
                "cases hcolumns_witness_witness_witness",
                "have hconstant : exists kb kc C. "
                f"({repeat_relation('kb', 'kc', 'k', 'h', tag='column_count_partition_constant_repeat')}) /\\ "
                f"(({sum_relation('kb', 'kc', 'h', 'C', tag='column_count_partition_constant_sum')}) /\\ C = h * k)",
                "specialize beta_repeat_sum_exists_exact k",
                "specialize beta_repeat_sum_exists_exact h",
                "exact beta_repeat_sum_exists_exact",
                "cases hconstant", "cases hconstant_witness",
                "cases hconstant_witness_witness",
                "cases hconstant_witness_witness_witness",
                "cases hconstant_witness_witness_witness_right",
                "have hpointwise : forall i a z s. "
                f"({_lt_term('i', 'h', tag='column_count_partition_pointwise_bound', variables=('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'N', 'i', 'a', 'z', 's'))}) -> "
                f"({beta_at('ab', 'ac', 'i', 'a', tag='column_count_partition_pointwise_first')}) -> "
                f"({beta_at('x', 'x1', 'i', 'z', tag='column_count_partition_pointwise_column')}) -> "
                f"({beta_at('x3', 'x4', 'i', 's', tag='column_count_partition_pointwise_constant')}) -> s = a + z",
                "intro i", "intro a", "intro z", "intro s",
                "intro hi", "intro ha", "intro hz", "intro hs",
                "have hpartition : a + z = s",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant p",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant q",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant h",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant k",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant ab",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant ac",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant bb",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant bc",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant x",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant x1",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant x3",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant x4",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant i",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant a",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant z",
                "specialize eisenstein_transposed_column_count_matches_decoded_constant s",
                "apply eisenstein_transposed_column_count_matches_decoded_constant",
                "exact hcolumns_witness_witness_witness_left",
                "exact hi", "exact ha", "exact hz",
                "exact hconstant_witness_witness_witness_left", "exact hs",
                "symm", "exact hpartition",
                "have hadd : N + x2 = x5",
                "specialize beta_sum_pointwise_add ab",
                "specialize beta_sum_pointwise_add ac",
                "specialize beta_sum_pointwise_add x",
                "specialize beta_sum_pointwise_add x1",
                "specialize beta_sum_pointwise_add x3",
                "specialize beta_sum_pointwise_add x4",
                "specialize beta_sum_pointwise_add h",
                "specialize beta_sum_pointwise_add N",
                "specialize beta_sum_pointwise_add x2",
                "specialize beta_sum_pointwise_add x5",
                "apply beta_sum_pointwise_add",
                "exact hfirst_sum",
                "exact hcolumns_witness_witness_witness_right",
                "exact hconstant_witness_witness_witness_right_left",
                "exact hpointwise",
                "have htotal : N + x2 = h * k",
                "trans x5", "exact hadd",
                "exact hconstant_witness_witness_witness_right_right",
                "exists x", "exists x1", "exists x2", "split",
                "exact hcolumns_witness_witness_witness_left", "split",
                "exact hcolumns_witness_witness_witness_right", "exact htotal",
            ),
            "The original row total plus the constructed column-count total is exactly h*k.",
        ),
    )


__all__ = [
    "eisenstein_transposed_column_count_choices",
    "eisenstein_transposed_column_count_prefix",
    "eisenstein_transposed_column_count_witness",
    "make_eisenstein_transposed_column_count_candidate_theorems",
]
