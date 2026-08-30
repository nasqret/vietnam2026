"""Successor-row decomposition for the Eisenstein Fubini argument.

The transposed rectangle total stores one ``BitCount`` for every outer row.
For an inner width ``S h``, the induction step must split that stored count
into the count on the first ``h`` entries and the final decoded bit.  This
module records that split without identifying unrelated beta codes:

* the *same* inner row code is restricted from length ``S h`` to ``h``;
* ``bit_count_succ_decompose`` supplies the reduced count and final bit; and
* the original outer beta decode is retained as provenance.

All helpers expand to ordinary first-order Peano formulas before parsing.
The theorem data are dependency-curried candidates only: they are neither
registered nor admitted by this module.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_rectangle_count_candidate import (
    eisenstein_rectangle_row_count_prefix,
    eisenstein_row_count_witness,
)
from .eisenstein_row_indicator_candidate import (
    eisenstein_cell_indicator_choice,
    eisenstein_row_indicator_prefix,
)
from .eisenstein_transposed_column_candidate import (
    eisenstein_transposed_column_entry_witness,
    eisenstein_transposed_column_prefix,
)
from .finite_fold_surface import beta_at, bit_count, repeat_relation, sum_relation


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
    names = tuple(f"efrd_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Fubini row-decomposition binder captures an argument")
    return names


def _lt_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("lt_gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _successor_row_count_split_witness_term(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    row_index: str,
    count: str,
    reduced_count: str,
    terminal_bit: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row_code, row_scale = _binders(
        tag,
        variables,
        ("row_code", "row_scale"),
    )
    successor_prefix = eisenstein_row_indicator_prefix(
        prime_p,
        prime_q,
        row_index,
        row_code,
        row_scale,
        successor,
        tag=f"efrd_{tag}_successor_prefix",
    )
    successor_count = bit_count(
        row_code,
        row_scale,
        successor,
        count,
        tag=f"efrd_{tag}_successor_count",
    )
    reduced_prefix = eisenstein_row_indicator_prefix(
        prime_p,
        prime_q,
        row_index,
        row_code,
        row_scale,
        predecessor,
        tag=f"efrd_{tag}_reduced_prefix",
    )
    terminal_entry = beta_at(
        row_code,
        row_scale,
        predecessor,
        terminal_bit,
        tag=f"efrd_{tag}_terminal_entry",
    )
    reduced_relation = bit_count(
        row_code,
        row_scale,
        predecessor,
        reduced_count,
        tag=f"efrd_{tag}_reduced_count",
    )
    return (
        f"exists {row_code} {row_scale}. "
        f"((((({successor_prefix}) /\\ ({successor_count})) /\\ "
        f"(({reduced_prefix}) /\\ ({terminal_entry}))) /\\ "
        f"((({reduced_relation}) /\\ "
        f"({terminal_bit} = 0 \\/ {terminal_bit} = 1)) /\\ "
        f"{count} = {reduced_count} + {terminal_bit})))"
    )


def eisenstein_successor_row_count_split_witness(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    row_index: str,
    count: str,
    reduced_count: str,
    terminal_bit: str,
    *,
    tag: str,
) -> str:
    """Expand one fixed reduced-count/final-bit split with inner provenance."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (predecessor, "row-width predecessor"),
            (successor, "successor row width"),
            (row_index, "row index"),
            (count, "successor row count"),
            (reduced_count, "reduced row count"),
            (terminal_bit, "terminal row bit"),
        )
    )
    return _successor_row_count_split_witness_term(
        prime_p,
        prime_q,
        predecessor,
        successor,
        row_index,
        count,
        reduced_count,
        terminal_bit,
        tag=tag,
        variables=variables,
    )


def _successor_row_count_decomposition_term(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    row_index: str,
    count: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    terminal_bit, reduced_count = _binders(
        tag, variables, ("terminal_bit", "reduced_count")
    )
    split = _successor_row_count_split_witness_term(
        prime_p,
        prime_q,
        predecessor,
        successor,
        row_index,
        count,
        reduced_count,
        terminal_bit,
        tag=f"{tag}_split",
        variables=variables + (terminal_bit, reduced_count),
    )
    return f"exists {terminal_bit} {reduced_count}. ({split})"


def eisenstein_successor_row_count_decomposition(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    row_index: str,
    count: str,
    *,
    tag: str,
) -> str:
    """Expand one fully provenanced successor-row count decomposition."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (predecessor, "row-width predecessor"),
            (successor, "successor row width"),
            (row_index, "row index"),
            (count, "successor row count"),
        )
    )
    return _successor_row_count_decomposition_term(
        prime_p,
        prime_q,
        predecessor,
        successor,
        row_index,
        count,
        tag=tag,
        variables=variables,
    )


def _successor_row_split_choices_term(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    outer_code: str,
    outer_scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row_index, count, reduced_count, terminal_bit = _binders(
        tag,
        variables,
        ("row_index", "count", "reduced_count", "terminal_bit"),
    )
    owned = variables + (row_index, count, reduced_count, terminal_bit)
    bound = _lt_term(
        row_index,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    outer_entry = beta_at(
        outer_code,
        outer_scale,
        row_index,
        count,
        tag=f"efrd_{tag}_outer_entry",
    )
    split = _successor_row_count_split_witness_term(
        prime_p,
        prime_q,
        predecessor,
        successor,
        row_index,
        count,
        reduced_count,
        terminal_bit,
        tag=f"{tag}_split",
        variables=owned,
    )
    return (
        f"forall {row_index}. ({bound}) -> "
        f"exists {count} {reduced_count} {terminal_bit}. "
        f"(({outer_entry}) /\\ ({split}))"
    )


def eisenstein_successor_row_split_choices(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    outer_code: str,
    outer_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand bounded choices of outer count/reduced count/terminal bit."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (predecessor, "row-width predecessor"),
            (successor, "successor row width"),
            (outer_code, "source outer code"),
            (outer_scale, "source outer scale"),
            (length, "outer length"),
        )
    )
    return _successor_row_split_choices_term(
        prime_p,
        prime_q,
        predecessor,
        successor,
        outer_code,
        outer_scale,
        length,
        tag=tag,
        variables=variables,
    )


def _successor_row_split_entry_term(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    outer_code: str,
    outer_scale: str,
    reduced_code: str,
    reduced_scale: str,
    terminal_code: str,
    terminal_scale: str,
    row_index: str,
    count: str,
    reduced_count: str,
    terminal_bit: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    outer_entry = beta_at(
        outer_code,
        outer_scale,
        row_index,
        count,
        tag=f"efrd_{tag}_outer_entry",
    )
    reduced_entry = beta_at(
        reduced_code,
        reduced_scale,
        row_index,
        reduced_count,
        tag=f"efrd_{tag}_reduced_entry",
    )
    terminal_entry = beta_at(
        terminal_code,
        terminal_scale,
        row_index,
        terminal_bit,
        tag=f"efrd_{tag}_terminal_entry",
    )
    split = _successor_row_count_split_witness_term(
        prime_p,
        prime_q,
        predecessor,
        successor,
        row_index,
        count,
        reduced_count,
        terminal_bit,
        tag=f"{tag}_split",
        variables=variables,
    )
    return (
        f"(((({outer_entry}) /\\ ({reduced_entry})) /\\ "
        f"({terminal_entry})) /\\ ({split}))"
    )


def _successor_row_split_prefix_term(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    outer_code: str,
    outer_scale: str,
    reduced_code: str,
    reduced_scale: str,
    terminal_code: str,
    terminal_scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row_index, count, reduced_count, terminal_bit = _binders(
        tag,
        variables,
        ("row_index", "count", "reduced_count", "terminal_bit"),
    )
    owned = variables + (row_index, count, reduced_count, terminal_bit)
    bound = _lt_term(
        row_index,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    entry = _successor_row_split_entry_term(
        prime_p,
        prime_q,
        predecessor,
        successor,
        outer_code,
        outer_scale,
        reduced_code,
        reduced_scale,
        terminal_code,
        terminal_scale,
        row_index,
        count,
        reduced_count,
        terminal_bit,
        tag=f"{tag}_entry",
        variables=owned,
    )
    return (
        f"forall {row_index}. ({bound}) -> "
        f"exists {count} {reduced_count} {terminal_bit}. "
        f"({entry})"
    )


def eisenstein_successor_row_split_prefix(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    outer_code: str,
    outer_scale: str,
    reduced_code: str,
    reduced_scale: str,
    terminal_code: str,
    terminal_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand aligned β-prefixes of reduced counts and terminal bits."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (predecessor, "row-width predecessor"),
            (successor, "successor row width"),
            (outer_code, "source outer code"),
            (outer_scale, "source outer scale"),
            (reduced_code, "reduced-count code"),
            (reduced_scale, "reduced-count scale"),
            (terminal_code, "terminal-bit code"),
            (terminal_scale, "terminal-bit scale"),
            (length, "outer length"),
        )
    )
    return _successor_row_split_prefix_term(
        prime_p,
        prime_q,
        predecessor,
        successor,
        outer_code,
        outer_scale,
        reduced_code,
        reduced_scale,
        terminal_code,
        terminal_scale,
        length,
        tag=tag,
        variables=variables,
    )


def _successor_row_split_successor_prefix(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    successor: str,
    outer_code: str,
    outer_scale: str,
    reduced_code: str,
    reduced_scale: str,
    terminal_code: str,
    terminal_scale: str,
    length_predecessor: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (predecessor, "row-width predecessor"),
            (successor, "successor row width"),
            (outer_code, "source outer code"),
            (outer_scale, "source outer scale"),
            (reduced_code, "reduced-count code"),
            (reduced_scale, "reduced-count scale"),
            (terminal_code, "terminal-bit code"),
            (terminal_scale, "terminal-bit scale"),
            (length_predecessor, "outer-length predecessor"),
        )
    )
    return _successor_row_split_prefix_term(
        prime_p,
        prime_q,
        predecessor,
        successor,
        outer_code,
        outer_scale,
        reduced_code,
        reduced_scale,
        terminal_code,
        terminal_scale,
        f"S {length_predecessor}",
        tag=tag,
        variables=variables,
    )


def make_eisenstein_fubini_row_decomposition_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the pointwise successor-row decomposition tranche."""

    successor_prefix = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "sh", tag="fubini_row_restrict_source"
    )
    reduced_prefix = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "h", tag="fubini_row_restrict_target"
    )

    row_witness = eisenstein_row_count_witness(
        "p", "q", "sh", "i", "n", tag="fubini_row_decompose_source"
    )
    row_decomposition = eisenstein_successor_row_count_decomposition(
        "p", "q", "h", "sh", "i", "n", tag="fubini_row_decompose_result"
    )

    outer_prefix = eisenstein_rectangle_row_count_prefix(
        "p",
        "q",
        "sh",
        "bb",
        "bc",
        "l",
        tag="fubini_outer_decompose_prefix",
    )
    outer_bound = _lt_term(
        "i",
        "l",
        tag="fubini_outer_decompose_bound",
        variables=("p", "q", "h", "bb", "bc", "l", "i", "n"),
    )
    outer_entry = beta_at(
        "bb", "bc", "i", "n", tag="fubini_outer_decompose_entry"
    )
    decoded_row_witness = eisenstein_row_count_witness(
        "p", "q", "sh", "i", "n", tag="fubini_outer_decompose_witness"
    )
    decoded_decomposition = eisenstein_successor_row_count_decomposition(
        "p", "q", "h", "sh", "i", "n", tag="fubini_outer_decompose_result"
    )

    split_choices = eisenstein_successor_row_split_choices(
        "p", "q", "h", "sh", "bb", "bc", "l",
        tag="fubini_row_split_choices",
    )

    prefix_before = eisenstein_successor_row_split_prefix(
        "p", "q", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc", "l",
        tag="fubini_row_split_extend_before",
    )
    last_source_entry = beta_at(
        "bb", "bc", "l", "n", tag="fubini_row_split_extend_last_source"
    )
    last_split = eisenstein_successor_row_count_split_witness(
        "p", "q", "h", "sh", "l", "n", "r", "a",
        tag="fubini_row_split_extend_last_witness",
    )
    last_choice = (
        "exists n r a. "
        f"(({last_source_entry}) /\\ ({last_split}))"
    )
    prefix_after = _successor_row_split_successor_prefix(
        "p", "q", "h", "sh", "bb", "bc", "eb", "ec", "ub", "uc", "l",
        tag="fubini_row_split_extend_after",
    )
    old_split_package = _successor_row_split_entry_term(
        "p", "q", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc",
        "i", "oldn", "oldr", "olda",
        tag="fubini_row_split_extend_old_package",
        variables=(
            "p", "q", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc",
            "i", "oldn", "oldr", "olda",
        ),
    )

    choices_all = eisenstein_successor_row_split_choices(
        "p", "q", "h", "sh", "bb", "bc", "l",
        tag="fubini_row_split_exists_all",
    )
    choices_previous = eisenstein_successor_row_split_choices(
        "p", "q", "h", "sh", "bb", "bc", "l",
        tag="fubini_row_split_exists_previous",
    )
    previous_prefix = (
        "exists db dc tb tc. "
        f"({eisenstein_successor_row_split_prefix('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'l', tag='fubini_row_split_exists_previous_prefix')})"
    )
    successor_split_prefix = (
        "exists db dc tb tc. "
        f"({_successor_row_split_successor_prefix('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'l', tag='fubini_row_split_exists_successor_prefix')})"
    )
    split_prefix_result = (
        "exists db dc tb tc. "
        f"({eisenstein_successor_row_split_prefix('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'l', tag='fubini_row_split_exists_result')})"
    )

    semantic_split_prefix = eisenstein_successor_row_split_prefix(
        "p", "q", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc", "l",
        tag="fubini_row_split_semantic_prefix",
    )
    semantic_bound = _lt_term(
        "i", "l", tag="fubini_row_split_semantic_bound",
        variables=(
            "p", "q", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc",
            "l", "i", "n", "r", "a",
        ),
    )
    semantic_source_entry = beta_at(
        "bb", "bc", "i", "n", tag="fubini_row_split_semantic_source"
    )
    semantic_reduced_entry = beta_at(
        "db", "dc", "i", "r", tag="fubini_row_split_semantic_reduced"
    )
    semantic_terminal_entry = beta_at(
        "tb", "tc", "i", "a", tag="fubini_row_split_semantic_terminal"
    )

    source_sum = sum_relation(
        "bb", "bc", "l", "T", tag="fubini_row_split_source_sum"
    )
    reduced_sum = sum_relation(
        "db", "dc", "l", "R", tag="fubini_row_split_reduced_sum"
    )
    terminal_sum = sum_relation(
        "tb", "tc", "l", "D", tag="fubini_row_split_terminal_sum"
    )

    first_cell_choice = eisenstein_cell_indicator_choice(
        "p", "q", "i", "j", "a", tag="fubini_cell_choice_unique_first"
    )
    second_cell_choice = eisenstein_cell_indicator_choice(
        "p", "q", "i", "j", "d", tag="fubini_cell_choice_unique_second"
    )

    swapped_split_prefix = eisenstein_successor_row_split_prefix(
        "q", "p", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc", "l",
        tag="fubini_terminal_column_split_prefix",
    )
    last_column_prefix = eisenstein_transposed_column_prefix(
        "p", "q", "sh", "bb", "bc", "h", "cb", "cc", "l",
        tag="fubini_terminal_column_prefix",
    )
    terminal_column_bound = _lt_term(
        "j", "l", tag="fubini_terminal_column_bound",
        variables=(
            "p", "q", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc",
            "cb", "cc", "l", "j", "a", "d",
        ),
    )
    terminal_decoded_entry = beta_at(
        "tb", "tc", "j", "a", tag="fubini_terminal_column_terminal_entry"
    )
    column_decoded_entry = beta_at(
        "cb", "cc", "j", "d", tag="fubini_terminal_column_column_entry"
    )
    last_column_sum = sum_relation(
        "cb", "cc", "l", "M", tag="fubini_terminal_column_sum"
    )

    outer_successor_prefix = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "bb", "bc", "sh",
        tag="fubini_outer_restrict_successor",
    )
    outer_reduced_prefix = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "bb", "bc", "h",
        tag="fubini_outer_restrict_reduced",
    )

    reduced_projection_prefix = eisenstein_successor_row_split_prefix(
        "p", "q", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc", "l",
        tag="fubini_reduced_projection_split",
    )
    reduced_rectangle_prefix = eisenstein_rectangle_row_count_prefix(
        "p", "q", "h", "db", "dc", "l",
        tag="fubini_reduced_projection_rectangle",
    )

    zero_width_prefix = eisenstein_rectangle_row_count_prefix(
        "p", "q", "z", "bb", "bc", "l",
        tag="fubini_zero_width_prefix",
    )
    zero_width_sum = sum_relation(
        "bb", "bc", "l", "T", tag="fubini_zero_width_sum"
    )

    return (
        spec(
            "eisenstein_row_indicator_prefix_succ_restrict",
            "forall p q i rb rc h sh. sh = S h -> "
            f"({successor_prefix}) -> ({reduced_prefix})",
            ("le_succ",),
            (
                "intro p",
                "intro q",
                "intro i",
                "intro rb",
                "intro rc",
                "intro h",
                "intro sh",
                "intro hsh",
                "intro hprefix",
                "rewrite hsh at hprefix",
                "intro j",
                "intro hj",
                "specialize hprefix j",
                "apply hprefix",
                "specialize le_succ (S j)",
                "specialize le_succ h",
                "apply le_succ",
                "exact hj",
            ),
            "A successor indicator row restricts to the same code's predecessor prefix.",
        ),
        spec(
            "eisenstein_successor_row_count_decompose",
            "forall p q h sh i n. sh = S h -> "
            f"({row_witness}) -> ({row_decomposition})",
            (
                "eisenstein_row_indicator_prefix_succ_restrict",
                "bit_count_succ_decompose",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro sh",
                "intro i",
                "intro n",
                "intro hsh",
                "intro hwitness",
                "cases hwitness",
                "cases hwitness_witness",
                "cases hwitness_witness_witness",
                f"have hprefix : {eisenstein_row_indicator_prefix('p', 'q', 'i', 'x', 'x1', 'h', tag='fubini_row_decompose_restricted')}",
                "specialize eisenstein_row_indicator_prefix_succ_restrict p",
                "specialize eisenstein_row_indicator_prefix_succ_restrict q",
                "specialize eisenstein_row_indicator_prefix_succ_restrict i",
                "specialize eisenstein_row_indicator_prefix_succ_restrict x",
                "specialize eisenstein_row_indicator_prefix_succ_restrict x1",
                "specialize eisenstein_row_indicator_prefix_succ_restrict h",
                "specialize eisenstein_row_indicator_prefix_succ_restrict sh",
                "apply eisenstein_row_indicator_prefix_succ_restrict",
                "exact hsh",
                "exact hwitness_witness_witness_left",
                "have hsplit : exists a r. "
                f"({beta_at('x', 'x1', 'h', 'a', tag='fubini_row_decompose_split_last')}) /\\ "
                f"(({bit_count('x', 'x1', 'h', 'r', tag='fubini_row_decompose_split_reduced')}) /\\ "
                "((a = 0 \\/ a = 1) /\\ n = r + a))",
                "specialize bit_count_succ_decompose x",
                "specialize bit_count_succ_decompose x1",
                "specialize bit_count_succ_decompose h",
                "specialize bit_count_succ_decompose sh",
                "specialize bit_count_succ_decompose n",
                "apply bit_count_succ_decompose",
                "exact hsh",
                "exact hwitness_witness_witness_right",
                "cases hsplit",
                "cases hsplit_witness",
                "cases hsplit_witness_witness",
                "cases hsplit_witness_witness_right",
                "cases hsplit_witness_witness_right_right",
                "exists x2",
                "exists x3",
                "exists x",
                "exists x1",
                "split",
                "split",
                "split",
                "exact hwitness_witness_witness_left",
                "exact hwitness_witness_witness_right",
                "split",
                "exact hprefix",
                "exact hsplit_witness_witness_left",
                "split",
                "split",
                "exact hsplit_witness_witness_right_left",
                "exact hsplit_witness_witness_right_right_left",
                "exact hsplit_witness_witness_right_right_right",
            ),
            "A semantic successor row count is its restricted count plus its final decoded bit.",
        ),
        spec(
            "eisenstein_rectangle_decoded_successor_row_count_decompose",
            "forall p q h sh bb bc l i n. sh = S h -> "
            f"({outer_prefix}) -> ({outer_bound}) -> ({outer_entry}) -> "
            f"({decoded_decomposition})",
            (
                "eisenstein_rectangle_decoded_row_count",
                "eisenstein_successor_row_count_decompose",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro sh",
                "intro bb",
                "intro bc",
                "intro l",
                "intro i",
                "intro n",
                "intro hsh",
                "intro hprefix",
                "intro hi",
                "intro hn",
                f"have hwitness : {decoded_row_witness}",
                "specialize eisenstein_rectangle_decoded_row_count p",
                "specialize eisenstein_rectangle_decoded_row_count q",
                "specialize eisenstein_rectangle_decoded_row_count sh",
                "specialize eisenstein_rectangle_decoded_row_count bb",
                "specialize eisenstein_rectangle_decoded_row_count bc",
                "specialize eisenstein_rectangle_decoded_row_count l",
                "specialize eisenstein_rectangle_decoded_row_count i",
                "specialize eisenstein_rectangle_decoded_row_count n",
                "apply eisenstein_rectangle_decoded_row_count",
                "exact hprefix",
                "exact hi",
                "exact hn",
                "specialize eisenstein_successor_row_count_decompose p",
                "specialize eisenstein_successor_row_count_decompose q",
                "specialize eisenstein_successor_row_count_decompose h",
                "specialize eisenstein_successor_row_count_decompose sh",
                "specialize eisenstein_successor_row_count_decompose i",
                "specialize eisenstein_successor_row_count_decompose n",
                "apply eisenstein_successor_row_count_decompose",
                "exact hsh",
                "exact hwitness",
            ),
            "A decoded successor-width outer row retains a full reduced-count/terminal-bit witness.",
        ),
        spec(
            "eisenstein_successor_row_split_choices",
            "forall p q h sh bb bc l. sh = S h -> "
            f"({outer_prefix}) -> ({split_choices})",
            ("eisenstein_successor_row_count_decompose",),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro sh",
                "intro bb",
                "intro bc",
                "intro l",
                "intro hsh",
                "intro houter",
                "intro i",
                "intro hi",
                "have hstored : exists n. "
                f"(({beta_at('bb', 'bc', 'i', 'n', tag='fubini_row_split_choices_stored_entry')}) /\\ "
                f"({eisenstein_row_count_witness('p', 'q', 'sh', 'i', 'n', tag='fubini_row_split_choices_stored_witness')}))",
                "specialize houter i",
                "apply houter",
                "exact hi",
                "cases hstored",
                "cases hstored_witness",
                "have hsplit : "
                f"{eisenstein_successor_row_count_decomposition('p', 'q', 'h', 'sh', 'i', 'x', tag='fubini_row_split_choices_decomposition')}",
                "specialize eisenstein_successor_row_count_decompose p",
                "specialize eisenstein_successor_row_count_decompose q",
                "specialize eisenstein_successor_row_count_decompose h",
                "specialize eisenstein_successor_row_count_decompose sh",
                "specialize eisenstein_successor_row_count_decompose i",
                "specialize eisenstein_successor_row_count_decompose x",
                "apply eisenstein_successor_row_count_decompose",
                "exact hsh",
                "exact hstored_witness_right",
                "cases hsplit",
                "cases hsplit_witness",
                "exists x",
                "exists x2",
                "exists x1",
                "split",
                "exact hstored_witness_left",
                "exact hsplit_witness_witness",
            ),
            "Every stored successor row constructively chooses an aligned reduced count and terminal bit.",
        ),
        spec(
            "eisenstein_successor_row_split_prefix_extend",
            "forall p q h sh bb bc db dc tb tc l. "
            f"({prefix_before}) -> ({last_choice}) -> "
            f"exists eb ec ub uc. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro db", "intro dc",
                "intro tb", "intro tc", "intro l",
                "intro hprefix", "intro hlast",
                "cases hlast", "cases hlast_witness",
                "cases hlast_witness_witness",
                "cases hlast_witness_witness_witness",
                "have hreduced_extension : exists eb ec. "
                f"(({beta_at('eb', 'ec', 'l', 'x1', tag='fubini_row_split_extend_reduced_last')}) /\\ "
                "forall i value. (exists gap. gap + S i = l) -> "
                f"({beta_at('db', 'dc', 'i', 'value', tag='fubini_row_split_extend_reduced_old')}) -> "
                f"({beta_at('eb', 'ec', 'i', 'value', tag='fubini_row_split_extend_reduced_new')}))",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend db",
                "specialize beta_prefix_extend dc",
                "specialize beta_prefix_extend x1",
                "exact beta_prefix_extend",
                "cases hreduced_extension",
                "cases hreduced_extension_witness",
                "cases hreduced_extension_witness_witness",
                "have hterminal_extension : exists ub uc. "
                f"(({beta_at('ub', 'uc', 'l', 'x2', tag='fubini_row_split_extend_terminal_last')}) /\\ "
                "forall i value. (exists gap. gap + S i = l) -> "
                f"({beta_at('tb', 'tc', 'i', 'value', tag='fubini_row_split_extend_terminal_old')}) -> "
                f"({beta_at('ub', 'uc', 'i', 'value', tag='fubini_row_split_extend_terminal_new')}))",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend tb",
                "specialize beta_prefix_extend tc",
                "specialize beta_prefix_extend x2",
                "exact beta_prefix_extend",
                "cases hterminal_extension",
                "cases hterminal_extension_witness",
                "cases hterminal_extension_witness_witness",
                "exists x3", "exists x4", "exists x5", "exists x6",
                "intro i", "intro hi",
                "have hposition : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hposition",
                "exists x", "exists x1", "exists x2",
                "split", "split", "split",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "exact hlast_witness_witness_witness_left",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "exact hreduced_extension_witness_witness_left",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "exact hterminal_extension_witness_witness_left",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "rewrite hposition_left",
                "exact hlast_witness_witness_witness_right",
                "have hold : exists oldn oldr olda. "
                f"({old_split_package})",
                "specialize hprefix i",
                "apply hprefix",
                "exact hposition_right",
                "cases hold", "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_left",
                "cases hold_witness_witness_witness_left_left",
                "exists x7", "exists x8", "exists x9",
                "split", "split", "split",
                "exact hold_witness_witness_witness_left_left_left",
                "specialize hreduced_extension_witness_witness_right i",
                "specialize hreduced_extension_witness_witness_right x8",
                "apply hreduced_extension_witness_witness_right",
                "exact hposition_right",
                "exact hold_witness_witness_witness_left_left_right",
                "specialize hterminal_extension_witness_witness_right i",
                "specialize hterminal_extension_witness_witness_right x9",
                "apply hterminal_extension_witness_witness_right",
                "exact hposition_right",
                "exact hold_witness_witness_witness_left_right",
                "exact hold_witness_witness_witness_right",
            ),
            "Append aligned reduced-count and terminal-bit entries while preserving complete row provenance.",
        ),
        spec(
            "eisenstein_successor_row_split_prefix_exists",
            "forall p q h sh bb bc l. "
            f"({choices_all}) -> ({split_prefix_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "le_succ",
                "le_refl",
                "eisenstein_successor_row_split_prefix_extend",
            ),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "induction l", "intro hchoices",
                "exists 0", "exists 0", "exists 0", "exists 0",
                "intro i", "intro hi", "exfalso", "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right", "exact hi_witness",
                "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hsi",
                "intro hchoices",
                f"have hprevious_choices : {choices_previous}",
                "intro i", "intro hi", "specialize hchoices i",
                "apply hchoices", "specialize le_succ (S i)",
                "specialize le_succ l", "apply le_succ", "exact hi",
                f"have hprevious_prefix : {previous_prefix}",
                "apply IH", "exact hprevious_choices",
                "cases hprevious_prefix", "cases hprevious_prefix_witness",
                "cases hprevious_prefix_witness_witness",
                "cases hprevious_prefix_witness_witness_witness",
                f"have hlast : {last_choice}",
                "specialize hchoices l", "apply hchoices",
                "specialize le_refl (S l)", "exact le_refl",
                f"have hnext : {successor_split_prefix}",
                "specialize eisenstein_successor_row_split_prefix_extend p",
                "specialize eisenstein_successor_row_split_prefix_extend q",
                "specialize eisenstein_successor_row_split_prefix_extend h",
                "specialize eisenstein_successor_row_split_prefix_extend sh",
                "specialize eisenstein_successor_row_split_prefix_extend bb",
                "specialize eisenstein_successor_row_split_prefix_extend bc",
                "specialize eisenstein_successor_row_split_prefix_extend x",
                "specialize eisenstein_successor_row_split_prefix_extend x1",
                "specialize eisenstein_successor_row_split_prefix_extend x2",
                "specialize eisenstein_successor_row_split_prefix_extend x3",
                "specialize eisenstein_successor_row_split_prefix_extend l",
                "apply eisenstein_successor_row_split_prefix_extend",
                "exact hprevious_prefix_witness_witness_witness_witness",
                "exact hlast",
                "exact hnext",
            ),
            "Any bounded family of successor-row splits has aligned β-coded reduced and terminal prefixes.",
        ),
        spec(
            "eisenstein_successor_rectangle_row_split_prefix_exists",
            "forall p q h sh bb bc l. sh = S h -> "
            f"({outer_prefix}) -> ({split_prefix_result})",
            (
                "eisenstein_successor_row_split_choices",
                "eisenstein_successor_row_split_prefix_exists",
            ),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro l",
                "intro hsh", "intro houter",
                f"have hchoices : {split_choices}",
                "specialize eisenstein_successor_row_split_choices p",
                "specialize eisenstein_successor_row_split_choices q",
                "specialize eisenstein_successor_row_split_choices h",
                "specialize eisenstein_successor_row_split_choices sh",
                "specialize eisenstein_successor_row_split_choices bb",
                "specialize eisenstein_successor_row_split_choices bc",
                "specialize eisenstein_successor_row_split_choices l",
                "apply eisenstein_successor_row_split_choices",
                "exact hsh", "exact houter",
                "specialize eisenstein_successor_row_split_prefix_exists p",
                "specialize eisenstein_successor_row_split_prefix_exists q",
                "specialize eisenstein_successor_row_split_prefix_exists h",
                "specialize eisenstein_successor_row_split_prefix_exists sh",
                "specialize eisenstein_successor_row_split_prefix_exists bb",
                "specialize eisenstein_successor_row_split_prefix_exists bc",
                "specialize eisenstein_successor_row_split_prefix_exists l",
                "apply eisenstein_successor_row_split_prefix_exists",
                "exact hchoices",
            ),
            "A semantic successor-width rectangle yields aligned reduced-count and terminal-bit β-prefixes.",
        ),
        spec(
            "eisenstein_successor_row_split_decoded_add",
            "forall p q h sh bb bc db dc tb tc l i n r a. "
            f"({semantic_split_prefix}) -> ({semantic_bound}) -> "
            f"({semantic_source_entry}) -> ({semantic_reduced_entry}) -> "
            f"({semantic_terminal_entry}) -> n = r + a",
            ("beta_at_unique",),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro db", "intro dc",
                "intro tb", "intro tc", "intro l", "intro i",
                "intro n", "intro r", "intro a",
                "intro hprefix", "intro hi", "intro hn", "intro hr", "intro ha",
                "have hstored : exists storedn storedr storeda. "
                f"({_successor_row_split_entry_term('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'i', 'storedn', 'storedr', 'storeda', tag='fubini_row_split_semantic_stored', variables=('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'l', 'i', 'n', 'r', 'a', 'storedn', 'storedr', 'storeda'))})",
                "specialize hprefix i", "apply hprefix", "exact hi",
                "cases hstored", "cases hstored_witness",
                "cases hstored_witness_witness",
                "cases hstored_witness_witness_witness",
                "cases hstored_witness_witness_witness_left",
                "cases hstored_witness_witness_witness_left_left",
                "have hsource_eq : x = n",
                "specialize beta_at_unique bb", "specialize beta_at_unique bc",
                "specialize beta_at_unique i", "specialize beta_at_unique x",
                "specialize beta_at_unique n", "apply beta_at_unique",
                "exact hstored_witness_witness_witness_left_left_left", "exact hn",
                "have hreduced_eq : x1 = r",
                "specialize beta_at_unique db", "specialize beta_at_unique dc",
                "specialize beta_at_unique i", "specialize beta_at_unique x1",
                "specialize beta_at_unique r", "apply beta_at_unique",
                "exact hstored_witness_witness_witness_left_left_right", "exact hr",
                "have hterminal_eq : x2 = a",
                "specialize beta_at_unique tb", "specialize beta_at_unique tc",
                "specialize beta_at_unique i", "specialize beta_at_unique x2",
                "specialize beta_at_unique a", "apply beta_at_unique",
                "exact hstored_witness_witness_witness_left_right", "exact ha",
                "cases hstored_witness_witness_witness_right",
                "cases hstored_witness_witness_witness_right_witness",
                "cases hstored_witness_witness_witness_right_witness_witness",
                "cases hstored_witness_witness_witness_right_witness_witness_right",
                "have heq : x = x1 + x2",
                "exact hstored_witness_witness_witness_right_witness_witness_right_right",
                "rewrite hsource_eq at heq",
                "rewrite hreduced_eq at heq",
                "rewrite hterminal_eq at heq",
                "exact heq",
            ),
            "Every aligned decoded successor count is exactly its decoded reduced count plus terminal bit.",
        ),
        spec(
            "eisenstein_successor_row_split_sum_add",
            "forall p q h sh bb bc db dc tb tc l R D T. "
            f"({semantic_split_prefix}) -> ({reduced_sum}) -> "
            f"({terminal_sum}) -> ({source_sum}) -> R + D = T",
            (
                "eisenstein_successor_row_split_decoded_add",
                "beta_sum_pointwise_add",
            ),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro db", "intro dc",
                "intro tb", "intro tc", "intro l",
                "intro R", "intro D", "intro T",
                "intro hprefix", "intro hreduced", "intro hterminal", "intro hsource",
                "have hpointwise : forall i r a n. "
                f"({_lt_term('i', 'l', tag='fubini_row_split_sum_pointwise_bound', variables=('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'l', 'R', 'D', 'T', 'i', 'r', 'a', 'n'))}) -> "
                f"({beta_at('db', 'dc', 'i', 'r', tag='fubini_row_split_sum_pointwise_reduced')}) -> "
                f"({beta_at('tb', 'tc', 'i', 'a', tag='fubini_row_split_sum_pointwise_terminal')}) -> "
                f"({beta_at('bb', 'bc', 'i', 'n', tag='fubini_row_split_sum_pointwise_source')}) -> n = r + a",
                "intro i", "intro r", "intro a", "intro n",
                "intro hi", "intro hr", "intro ha", "intro hn",
                "specialize eisenstein_successor_row_split_decoded_add p",
                "specialize eisenstein_successor_row_split_decoded_add q",
                "specialize eisenstein_successor_row_split_decoded_add h",
                "specialize eisenstein_successor_row_split_decoded_add sh",
                "specialize eisenstein_successor_row_split_decoded_add bb",
                "specialize eisenstein_successor_row_split_decoded_add bc",
                "specialize eisenstein_successor_row_split_decoded_add db",
                "specialize eisenstein_successor_row_split_decoded_add dc",
                "specialize eisenstein_successor_row_split_decoded_add tb",
                "specialize eisenstein_successor_row_split_decoded_add tc",
                "specialize eisenstein_successor_row_split_decoded_add l",
                "specialize eisenstein_successor_row_split_decoded_add i",
                "specialize eisenstein_successor_row_split_decoded_add n",
                "specialize eisenstein_successor_row_split_decoded_add r",
                "specialize eisenstein_successor_row_split_decoded_add a",
                "apply eisenstein_successor_row_split_decoded_add",
                "exact hprefix", "exact hi", "exact hn", "exact hr", "exact ha",
                "specialize beta_sum_pointwise_add db",
                "specialize beta_sum_pointwise_add dc",
                "specialize beta_sum_pointwise_add tb",
                "specialize beta_sum_pointwise_add tc",
                "specialize beta_sum_pointwise_add bb",
                "specialize beta_sum_pointwise_add bc",
                "specialize beta_sum_pointwise_add l",
                "specialize beta_sum_pointwise_add R",
                "specialize beta_sum_pointwise_add D",
                "specialize beta_sum_pointwise_add T",
                "apply beta_sum_pointwise_add",
                "exact hreduced", "exact hterminal", "exact hsource", "exact hpointwise",
            ),
            "The successor outer Sum is exactly the reduced-row Sum plus the terminal-bit Sum.",
        ),
        spec(
            "eisenstein_cell_indicator_choice_unique",
            "forall p q i j a d. "
            f"({first_cell_choice}) -> ({second_cell_choice}) -> a = d",
            (),
            (
                "intro p", "intro q", "intro i", "intro j", "intro a", "intro d",
                "intro ha", "intro hd",
                "cases ha",
                "cases ha_left", "cases ha_left_right",
                "cases hd",
                "cases hd_left",
                "trans 0", "exact ha_left_left", "symm", "exact hd_left_left",
                "cases hd_right", "cases hd_right_right",
                "exfalso", "apply hd_right_right_right", "exact ha_left_right_left",
                "cases ha_right", "cases ha_right_right",
                "cases hd",
                "cases hd_left", "cases hd_left_right",
                "exfalso", "apply ha_right_right_right", "exact hd_left_right_left",
                "cases hd_right",
                "trans 1", "exact ha_right_left", "symm", "exact hd_right_left",
            ),
            "The exact orientation predicate determines its zero-or-one indicator uniquely.",
        ),
        spec(
            "eisenstein_successor_terminal_bit_matches_last_column",
            "forall p q h sh bb bc db dc tb tc cb cc l j a d. "
            f"sh = S h -> ({swapped_split_prefix}) -> ({last_column_prefix}) -> "
            f"({terminal_column_bound}) -> ({terminal_decoded_entry}) -> "
            f"({column_decoded_entry}) -> a = d",
            (
                "le_refl",
                "beta_at_unique",
                "eisenstein_row_indicator_decoded_choice",
                "eisenstein_cell_indicator_choice_unique",
            ),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro db", "intro dc",
                "intro tb", "intro tc", "intro cb", "intro cc",
                "intro l", "intro j", "intro a", "intro d",
                "intro hsh", "intro hsplit", "intro hcolumn", "intro hj",
                "intro ha", "intro hd",
                "have hhsh : exists gap. gap + S h = sh",
                "rewrite hsh",
                "specialize le_refl (S h)", "exact le_refl",
                "have hsplit_stored : exists n r storeda. "
                f"({_successor_row_split_entry_term('q', 'p', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'j', 'n', 'r', 'storeda', tag='fubini_terminal_column_split_stored', variables=('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'cb', 'cc', 'l', 'j', 'a', 'd', 'n', 'r', 'storeda'))})",
                "specialize hsplit j", "apply hsplit", "exact hj",
                "cases hsplit_stored", "cases hsplit_stored_witness",
                "cases hsplit_stored_witness_witness",
                "cases hsplit_stored_witness_witness_witness",
                "cases hsplit_stored_witness_witness_witness_left",
                "cases hsplit_stored_witness_witness_witness_left_left",
                "have hstored_a_eq : x2 = a",
                "specialize beta_at_unique tb", "specialize beta_at_unique tc",
                "specialize beta_at_unique j", "specialize beta_at_unique x2",
                "specialize beta_at_unique a", "apply beta_at_unique",
                "exact hsplit_stored_witness_witness_witness_left_right", "exact ha",
                "cases hsplit_stored_witness_witness_witness_right",
                "cases hsplit_stored_witness_witness_witness_right_witness",
                "cases hsplit_stored_witness_witness_witness_right_witness_witness",
                "cases hsplit_stored_witness_witness_witness_right_witness_witness_left",
                "cases hsplit_stored_witness_witness_witness_right_witness_witness_left_left",
                "cases hsplit_stored_witness_witness_witness_right_witness_witness_left_right",
                f"have hterminal_choice : {eisenstein_cell_indicator_choice('q', 'p', 'j', 'h', 'x2', tag='fubini_terminal_column_terminal_choice')}",
                "specialize eisenstein_row_indicator_decoded_choice q",
                "specialize eisenstein_row_indicator_decoded_choice p",
                "specialize eisenstein_row_indicator_decoded_choice j",
                "specialize eisenstein_row_indicator_decoded_choice x3",
                "specialize eisenstein_row_indicator_decoded_choice x4",
                "specialize eisenstein_row_indicator_decoded_choice sh",
                "specialize eisenstein_row_indicator_decoded_choice h",
                "specialize eisenstein_row_indicator_decoded_choice x2",
                "apply eisenstein_row_indicator_decoded_choice",
                "exact hsplit_stored_witness_witness_witness_right_witness_witness_left_left_left",
                "exact hhsh",
                "exact hsplit_stored_witness_witness_witness_right_witness_witness_left_right_right",
                "have hcolumn_stored : exists storedd. "
                f"(({beta_at('cb', 'cc', 'j', 'storedd', tag='fubini_terminal_column_stored_entry')}) /\\ "
                f"({eisenstein_transposed_column_entry_witness('p', 'q', 'sh', 'bb', 'bc', 'h', 'j', 'storedd', tag='fubini_terminal_column_stored_witness')}))",
                "specialize hcolumn j", "apply hcolumn", "exact hj",
                "cases hcolumn_stored", "cases hcolumn_stored_witness",
                "have hstored_d_eq : x5 = d",
                "specialize beta_at_unique cb", "specialize beta_at_unique cc",
                "specialize beta_at_unique j", "specialize beta_at_unique x5",
                "specialize beta_at_unique d", "apply beta_at_unique",
                "exact hcolumn_stored_witness_left", "exact hd",
                "cases hcolumn_stored_witness_right",
                "cases hcolumn_stored_witness_right_witness",
                "cases hcolumn_stored_witness_right_witness_witness",
                "cases hcolumn_stored_witness_right_witness_witness_witness",
                "cases hcolumn_stored_witness_right_witness_witness_witness_left",
                "cases hcolumn_stored_witness_right_witness_witness_witness_left_left",
                f"have hcolumn_choice : {eisenstein_cell_indicator_choice('q', 'p', 'j', 'h', 'x5', tag='fubini_terminal_column_column_choice')}",
                "specialize eisenstein_row_indicator_decoded_choice q",
                "specialize eisenstein_row_indicator_decoded_choice p",
                "specialize eisenstein_row_indicator_decoded_choice j",
                "specialize eisenstein_row_indicator_decoded_choice x7",
                "specialize eisenstein_row_indicator_decoded_choice x8",
                "specialize eisenstein_row_indicator_decoded_choice sh",
                "specialize eisenstein_row_indicator_decoded_choice h",
                "specialize eisenstein_row_indicator_decoded_choice x5",
                "apply eisenstein_row_indicator_decoded_choice",
                "exact hcolumn_stored_witness_right_witness_witness_witness_left_left_right",
                "exact hhsh",
                "exact hcolumn_stored_witness_right_witness_witness_witness_right",
                "rewrite hstored_a_eq at hterminal_choice",
                "rewrite hstored_a_eq at hterminal_choice",
                "rewrite hstored_d_eq at hcolumn_choice",
                "rewrite hstored_d_eq at hcolumn_choice",
                "specialize eisenstein_cell_indicator_choice_unique q",
                "specialize eisenstein_cell_indicator_choice_unique p",
                "specialize eisenstein_cell_indicator_choice_unique j",
                "specialize eisenstein_cell_indicator_choice_unique h",
                "specialize eisenstein_cell_indicator_choice_unique a",
                "specialize eisenstein_cell_indicator_choice_unique d",
                "apply eisenstein_cell_indicator_choice_unique",
                "exact hterminal_choice", "exact hcolumn_choice",
            ),
            "The terminal-bit prefix and the constructed last column decode the same bit at every bounded row.",
        ),
        spec(
            "eisenstein_successor_terminal_prefix_to_last_column",
            "forall p q h sh bb bc db dc tb tc cb cc l j a. "
            f"sh = S h -> ({swapped_split_prefix}) -> ({last_column_prefix}) -> "
            f"({terminal_column_bound}) -> ({terminal_decoded_entry}) -> "
            f"({beta_at('cb', 'cc', 'j', 'a', tag='fubini_terminal_column_transport_result')})",
            (
                "beta_at_exists",
                "eisenstein_successor_terminal_bit_matches_last_column",
            ),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro db", "intro dc",
                "intro tb", "intro tc", "intro cb", "intro cc",
                "intro l", "intro j", "intro a",
                "intro hsh", "intro hsplit", "intro hcolumn", "intro hj", "intro ha",
                "have hdecoded : exists d. "
                f"({beta_at('cb', 'cc', 'j', 'd', tag='fubini_terminal_column_transport_existing')})",
                "specialize beta_at_exists cb", "specialize beta_at_exists cc",
                "specialize beta_at_exists j", "exact beta_at_exists",
                "cases hdecoded",
                "have heq : a = x",
                "specialize eisenstein_successor_terminal_bit_matches_last_column p",
                "specialize eisenstein_successor_terminal_bit_matches_last_column q",
                "specialize eisenstein_successor_terminal_bit_matches_last_column h",
                "specialize eisenstein_successor_terminal_bit_matches_last_column sh",
                "specialize eisenstein_successor_terminal_bit_matches_last_column bb",
                "specialize eisenstein_successor_terminal_bit_matches_last_column bc",
                "specialize eisenstein_successor_terminal_bit_matches_last_column db",
                "specialize eisenstein_successor_terminal_bit_matches_last_column dc",
                "specialize eisenstein_successor_terminal_bit_matches_last_column tb",
                "specialize eisenstein_successor_terminal_bit_matches_last_column tc",
                "specialize eisenstein_successor_terminal_bit_matches_last_column cb",
                "specialize eisenstein_successor_terminal_bit_matches_last_column cc",
                "specialize eisenstein_successor_terminal_bit_matches_last_column l",
                "specialize eisenstein_successor_terminal_bit_matches_last_column j",
                "specialize eisenstein_successor_terminal_bit_matches_last_column a",
                "specialize eisenstein_successor_terminal_bit_matches_last_column x",
                "apply eisenstein_successor_terminal_bit_matches_last_column",
                "exact hsh", "exact hsplit", "exact hcolumn", "exact hj",
                "exact ha", "exact hdecoded_witness",
                "rewrite <- heq at hdecoded_witness",
                "rewrite <- heq at hdecoded_witness",
                "exact hdecoded_witness",
            ),
            "Every terminal-prefix decode transports extensionally to the constructed last-column code.",
        ),
        spec(
            "eisenstein_successor_terminal_sum_matches_last_column",
            "forall p q h sh bb bc db dc tb tc cb cc l D M. "
            f"sh = S h -> ({swapped_split_prefix}) -> ({last_column_prefix}) -> "
            f"({terminal_sum}) -> ({last_column_sum}) -> D = M",
            (
                "eisenstein_successor_terminal_prefix_to_last_column",
                "beta_sum_transport_prefix",
                "beta_sum_functional",
            ),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro db", "intro dc",
                "intro tb", "intro tc", "intro cb", "intro cc",
                "intro l", "intro D", "intro M",
                "intro hsh", "intro hsplit", "intro hcolumn",
                "intro hterminal", "intro hcolumnsum",
                "have htransport : forall j a. "
                f"({_lt_term('j', 'l', tag='fubini_terminal_column_sum_bound', variables=('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'cb', 'cc', 'l', 'D', 'M', 'j', 'a'))}) -> "
                f"({beta_at('tb', 'tc', 'j', 'a', tag='fubini_terminal_column_sum_source_entry')}) -> "
                f"({beta_at('cb', 'cc', 'j', 'a', tag='fubini_terminal_column_sum_target_entry')})",
                "intro j", "intro a", "intro hj", "intro ha",
                "specialize eisenstein_successor_terminal_prefix_to_last_column p",
                "specialize eisenstein_successor_terminal_prefix_to_last_column q",
                "specialize eisenstein_successor_terminal_prefix_to_last_column h",
                "specialize eisenstein_successor_terminal_prefix_to_last_column sh",
                "specialize eisenstein_successor_terminal_prefix_to_last_column bb",
                "specialize eisenstein_successor_terminal_prefix_to_last_column bc",
                "specialize eisenstein_successor_terminal_prefix_to_last_column db",
                "specialize eisenstein_successor_terminal_prefix_to_last_column dc",
                "specialize eisenstein_successor_terminal_prefix_to_last_column tb",
                "specialize eisenstein_successor_terminal_prefix_to_last_column tc",
                "specialize eisenstein_successor_terminal_prefix_to_last_column cb",
                "specialize eisenstein_successor_terminal_prefix_to_last_column cc",
                "specialize eisenstein_successor_terminal_prefix_to_last_column l",
                "specialize eisenstein_successor_terminal_prefix_to_last_column j",
                "specialize eisenstein_successor_terminal_prefix_to_last_column a",
                "apply eisenstein_successor_terminal_prefix_to_last_column",
                "exact hsh", "exact hsplit", "exact hcolumn", "exact hj", "exact ha",
                "have hcolumnD : "
                f"{sum_relation('cb', 'cc', 'l', 'D', tag='fubini_terminal_column_sum_transport')}",
                "specialize beta_sum_transport_prefix tb",
                "specialize beta_sum_transport_prefix tc",
                "specialize beta_sum_transport_prefix cb",
                "specialize beta_sum_transport_prefix cc",
                "specialize beta_sum_transport_prefix l",
                "specialize beta_sum_transport_prefix D",
                "apply beta_sum_transport_prefix",
                "exact hterminal", "exact htransport",
                "specialize beta_sum_functional cb",
                "specialize beta_sum_functional cc",
                "specialize beta_sum_functional l",
                "specialize beta_sum_functional D",
                "specialize beta_sum_functional M",
                "apply beta_sum_functional",
                "exact hcolumnD", "exact hcolumnsum",
            ),
            "The terminal-bit Sum is exactly the relational count Sum of the constructed last column.",
        ),
        spec(
            "eisenstein_rectangle_row_count_prefix_succ_restrict",
            "forall p q k bb bc h sh. sh = S h -> "
            f"({outer_successor_prefix}) -> ({outer_reduced_prefix})",
            ("le_succ",),
            (
                "intro p", "intro q", "intro k", "intro bb", "intro bc",
                "intro h", "intro sh", "intro hsh", "intro hprefix",
                "rewrite hsh at hprefix",
                "intro i", "intro hi", "specialize hprefix i", "apply hprefix",
                "specialize le_succ (S i)", "specialize le_succ h",
                "apply le_succ", "exact hi",
            ),
            "A semantic outer row-count prefix restricts from successor length to predecessor length.",
        ),
        spec(
            "eisenstein_successor_row_split_reduced_rectangle_prefix",
            "forall p q h sh bb bc db dc tb tc l. "
            f"({reduced_projection_prefix}) -> ({reduced_rectangle_prefix})",
            (),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro db", "intro dc",
                "intro tb", "intro tc", "intro l", "intro hsplit",
                "intro i", "intro hi",
                "have hstored : exists n r a. "
                f"({_successor_row_split_entry_term('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'i', 'n', 'r', 'a', tag='fubini_reduced_projection_stored', variables=('p', 'q', 'h', 'sh', 'bb', 'bc', 'db', 'dc', 'tb', 'tc', 'l', 'i', 'n', 'r', 'a'))})",
                "specialize hsplit i", "apply hsplit", "exact hi",
                "cases hstored", "cases hstored_witness",
                "cases hstored_witness_witness",
                "cases hstored_witness_witness_witness",
                "cases hstored_witness_witness_witness_left",
                "cases hstored_witness_witness_witness_left_left",
                "cases hstored_witness_witness_witness_right",
                "cases hstored_witness_witness_witness_right_witness",
                "cases hstored_witness_witness_witness_right_witness_witness",
                "cases hstored_witness_witness_witness_right_witness_witness_left",
                "cases hstored_witness_witness_witness_right_witness_witness_left_right",
                "cases hstored_witness_witness_witness_right_witness_witness_right",
                "cases hstored_witness_witness_witness_right_witness_witness_right_left",
                "exists x1",
                "split",
                "exact hstored_witness_witness_witness_left_left_right",
                "exists x3", "exists x4", "split",
                "exact hstored_witness_witness_witness_right_witness_witness_left_right_left",
                "exact hstored_witness_witness_witness_right_witness_witness_right_left_left",
            ),
            "The reduced-count code in a split prefix is itself a semantic predecessor-width rectangle prefix.",
        ),
        spec(
            "eisenstein_zero_width_rectangle_sum_zero",
            "forall p q z bb bc l T. z = 0 -> "
            f"({zero_width_prefix}) -> ({zero_width_sum}) -> T = 0",
            (
                "beta_repeat_exists",
                "eisenstein_rectangle_decoded_row_count",
                "bit_count_zero",
                "beta_sum_transport_prefix",
                "beta_repeat_sum_exact",
                "mul_comm",
                "mul_zero_left",
            ),
            (
                "intro p", "intro q", "intro z", "intro bb", "intro bc",
                "intro l", "intro T", "intro hz", "intro hprefix", "intro hsum",
                "have hrepeat : exists rb rc. "
                f"({repeat_relation('rb', 'rc', 'z', 'l', tag='fubini_zero_width_repeat')})",
                "specialize beta_repeat_exists z", "specialize beta_repeat_exists l",
                "exact beta_repeat_exists",
                "cases hrepeat", "cases hrepeat_witness",
                "have hpreserve : forall i n. "
                f"({_lt_term('i', 'l', tag='fubini_zero_width_preserve_bound', variables=('p', 'q', 'z', 'bb', 'bc', 'l', 'T', 'i', 'n'))}) -> "
                f"({beta_at('bb', 'bc', 'i', 'n', tag='fubini_zero_width_preserve_source')}) -> "
                f"({beta_at('x', 'x1', 'i', 'n', tag='fubini_zero_width_preserve_target')})",
                "intro i", "intro n", "intro hi", "intro hn",
                f"have hwitness : {eisenstein_row_count_witness('p', 'q', 'z', 'i', 'n', tag='fubini_zero_width_decoded_witness')}",
                "specialize eisenstein_rectangle_decoded_row_count p",
                "specialize eisenstein_rectangle_decoded_row_count q",
                "specialize eisenstein_rectangle_decoded_row_count z",
                "specialize eisenstein_rectangle_decoded_row_count bb",
                "specialize eisenstein_rectangle_decoded_row_count bc",
                "specialize eisenstein_rectangle_decoded_row_count l",
                "specialize eisenstein_rectangle_decoded_row_count i",
                "specialize eisenstein_rectangle_decoded_row_count n",
                "apply eisenstein_rectangle_decoded_row_count",
                "exact hprefix", "exact hi", "exact hn",
                "cases hwitness", "cases hwitness_witness",
                "cases hwitness_witness_witness",
                "have hnzero : n = 0",
                "specialize bit_count_zero x2",
                "specialize bit_count_zero x3",
                "specialize bit_count_zero z",
                "specialize bit_count_zero n",
                "apply bit_count_zero",
                "exact hz",
                "exact hwitness_witness_witness_right",
                "have hzero_entry : "
                f"{beta_at('x', 'x1', 'i', 'z', tag='fubini_zero_width_repeat_entry')}",
                "specialize hrepeat_witness_witness i", "apply hrepeat_witness_witness",
                "exact hi",
                "rewrite hz at hzero_entry",
                "rewrite hz at hzero_entry",
                "rewrite hnzero",
                "rewrite hnzero",
                "exact hzero_entry",
                "have hrepeat_sum : "
                f"{sum_relation('x', 'x1', 'l', 'T', tag='fubini_zero_width_transport_sum')}",
                "specialize beta_sum_transport_prefix bb",
                "specialize beta_sum_transport_prefix bc",
                "specialize beta_sum_transport_prefix x",
                "specialize beta_sum_transport_prefix x1",
                "specialize beta_sum_transport_prefix l",
                "specialize beta_sum_transport_prefix T",
                "apply beta_sum_transport_prefix",
                "exact hsum", "exact hpreserve",
                "have hproduct : T = l * z",
                "specialize beta_repeat_sum_exact x",
                "specialize beta_repeat_sum_exact x1",
                "specialize beta_repeat_sum_exact z",
                "specialize beta_repeat_sum_exact l",
                "specialize beta_repeat_sum_exact T",
                "apply beta_repeat_sum_exact",
                "exact hrepeat_witness_witness", "exact hrepeat_sum",
                "rewrite hz at hproduct",
                "trans l * 0", "exact hproduct",
                "trans 0 * l",
                "specialize mul_comm l", "specialize mul_comm 0",
                "exact mul_comm",
                "specialize mul_zero_left l", "exact mul_zero_left",
            ),
            "Every semantic zero-width rectangle has relational outer Sum zero.",
        ),
    )


__all__ = [
    "eisenstein_successor_row_count_decomposition",
    "eisenstein_successor_row_count_split_witness",
    "eisenstein_successor_row_split_choices",
    "eisenstein_successor_row_split_prefix",
    "make_eisenstein_fubini_row_decomposition_candidate_theorems",
]
