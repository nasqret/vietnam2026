"""Nested beta representation of the Eisenstein half-rectangle count.

The inner layer assigns each fixed row ``i`` its own beta-coded orientation
bits and a ``BitCount`` value.  This module beta-codes only those row-count
values across ``i < h``.  A semantic outer entry therefore says that its
decoded natural is the count of *some* row code satisfying the exact inner
row-indicator relation.  The row codes remain existential at each entry:
raw equality of beta codes is never used as equality of represented rows.

This nested representation avoids a pairing function and avoids flattening
the ``h`` by ``k`` rectangle.  Once the outer prefix exists, the already
checked beta-sum relation supplies a total of its decoded row counts.  This
module deliberately stops at that total; identifying it with either of the
classical floor sums belongs to a later counting argument.

All surface helpers expand before parsing to ordinary first-order Peano
arithmetic.  No list, matrix, function, comparison, beta, sum, or bit-count
primitive reaches the kernel, and these candidates are not publicly
registered.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_row_indicator_candidate import (
    eisenstein_row_indicator_prefix,
)
from .fermat_residue_product_candidate import prime
from .finite_fold_surface import beta_at, bit_count, sum_relation


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'" for character in value[1:]
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
    names = tuple(f"erc_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Eisenstein-count binder captures an argument")
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


def _le_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("le_gap",))
    return f"exists {gap}. {gap} + ({left}) = {right}"


def _row_count_witness_term(
    prime_p: str,
    prime_q: str,
    column_half: str,
    row_index: str,
    count: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row_code, row_scale = _binders(
        tag, variables, ("row_code", "row_scale")
    )
    row_prefix = eisenstein_row_indicator_prefix(
        prime_p,
        prime_q,
        row_index,
        row_code,
        row_scale,
        column_half,
        tag=f"erc_{tag}_row",
    )
    row_count = bit_count(
        row_code,
        row_scale,
        column_half,
        count,
        tag=f"erc_{tag}_count",
    )
    return (
        f"exists {row_code} {row_scale}. "
        f"(({row_prefix}) /\\ ({row_count}))"
    )


def eisenstein_row_count_witness(
    prime_p: str,
    prime_q: str,
    column_half: str,
    row_index: str,
    count: str,
    *,
    tag: str,
) -> str:
    """Expand that ``count`` is the BitCount of one exact indicator row."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (column_half, "column half"),
            (row_index, "row index"),
            (count, "row count"),
        )
    )
    return _row_count_witness_term(
        prime_p,
        prime_q,
        column_half,
        row_index,
        count,
        tag=tag,
        variables=variables,
    )


def _row_count_choices_term(
    prime_p: str,
    prime_q: str,
    column_half: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row, count = _binders(tag, variables, ("row", "count"))
    owned = variables + (row, count)
    bound = _lt_term(
        row,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    witness = _row_count_witness_term(
        prime_p,
        prime_q,
        column_half,
        row,
        count,
        tag=f"{tag}_witness",
        variables=owned,
    )
    return f"forall {row}. ({bound}) -> exists {count}. ({witness})"


def eisenstein_rectangle_row_count_choices(
    prime_p: str,
    prime_q: str,
    column_half: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand semantic row-count choices for a bounded row interval."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (column_half, "column half"),
            (length, "row-count length"),
        )
    )
    return _row_count_choices_term(
        prime_p,
        prime_q,
        column_half,
        length,
        tag=tag,
        variables=variables,
    )


def _row_count_prefix_term(
    prime_p: str,
    prime_q: str,
    column_half: str,
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row, count = _binders(tag, variables, ("row", "count"))
    owned = variables + (row, count)
    bound = _lt_term(
        row,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    decoded = beta_at(
        code,
        scale,
        row,
        count,
        tag=f"erc_{tag}_decoded",
    )
    witness = _row_count_witness_term(
        prime_p,
        prime_q,
        column_half,
        row,
        count,
        tag=f"{tag}_witness",
        variables=owned,
    )
    return (
        f"forall {row}. ({bound}) -> exists {count}. "
        f"(({decoded}) /\\ ({witness}))"
    )


def eisenstein_rectangle_row_count_prefix(
    prime_p: str,
    prime_q: str,
    column_half: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a beta prefix of semantic row-count witnesses."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (column_half, "column half"),
            (code, "outer code"),
            (scale, "outer scale"),
            (length, "row-count length"),
        )
    )
    return _row_count_prefix_term(
        prime_p,
        prime_q,
        column_half,
        code,
        scale,
        length,
        tag=tag,
        variables=variables,
    )


def _row_count_successor_prefix(
    prime_p: str,
    prime_q: str,
    column_half: str,
    code: str,
    scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (column_half, "column half"),
            (code, "outer code"),
            (scale, "outer scale"),
            (predecessor, "row-count predecessor"),
        )
    )
    return _row_count_prefix_term(
        prime_p,
        prime_q,
        column_half,
        code,
        scale,
        f"S {predecessor}",
        tag=tag,
        variables=variables,
    )


def make_eisenstein_rectangle_count_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the nested row-count prefix and rectangle-total candidates."""

    prime_p = prime("p", tag="rectangle_count_prime_p")
    prime_q = prime("q", tag="rectangle_count_prime_q")
    row_bound = _lt_term(
        "i",
        "h",
        tag="rectangle_count_row_bound",
        variables=("p", "q", "h", "k", "l", "i"),
    )
    bounded_row = _lt_term(
        "i",
        "l",
        tag="rectangle_count_bounded_row",
        variables=("p", "q", "h", "k", "l", "i"),
    )
    length_bound = _le_term(
        "l",
        "h",
        tag="rectangle_count_length_bound",
        variables=("p", "q", "h", "k", "l", "i"),
    )

    point_package = (
        "exists rb rc n. "
        f"(({eisenstein_row_indicator_prefix('p', 'q', 'i', 'rb', 'rc', 'k', tag='rectangle_count_point_row')}) /\\ "
        f"({bit_count('rb', 'rc', 'k', 'n', tag='rectangle_count_point_count')}))"
    )
    point_witness = eisenstein_row_count_witness(
        "p", "q", "k", "i", "n", tag="rectangle_count_point_witness"
    )

    prefix_before = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "cb", "cc", "l", tag="rectangle_count_extend_before"
    )
    last_witness = eisenstein_row_count_witness(
        "p", "q", "k", "l", "n", tag="rectangle_count_extend_last"
    )
    prefix_after = _row_count_successor_prefix(
        "p", "q", "k", "z", "d", "l", tag="rectangle_count_extend_after"
    )
    old_entry = beta_at(
        "cb", "cc", "i", "oldcount", tag="rectangle_count_extend_old_entry"
    )

    choices_all = eisenstein_rectangle_row_count_choices(
        "p", "q", "k", "l", tag="rectangle_count_exists_all"
    )
    choices_previous = eisenstein_rectangle_row_count_choices(
        "p", "q", "k", "l", tag="rectangle_count_exists_previous_choices"
    )
    previous_prefix = (
        "exists cb cc. "
        f"({eisenstein_rectangle_row_count_prefix('p', 'q', 'k', 'cb', 'cc', 'l', tag='rectangle_count_exists_previous_prefix')})"
    )
    successor_prefix = (
        "exists cb cc. "
        f"({_row_count_successor_prefix('p', 'q', 'k', 'cb', 'cc', 'l', tag='rectangle_count_exists_successor_prefix')})"
    )
    prefix_result = (
        "exists cb cc. "
        f"({eisenstein_rectangle_row_count_prefix('p', 'q', 'k', 'cb', 'cc', 'l', tag='rectangle_count_exists_result')})"
    )

    bounded_choices = eisenstein_rectangle_row_count_choices(
        "p", "q", "k", "l", tag="rectangle_count_bounded_choices"
    )
    bounded_prefix = (
        "exists cb cc. "
        f"({eisenstein_rectangle_row_count_prefix('p', 'q', 'k', 'cb', 'cc', 'l', tag='rectangle_count_bounded_prefix')})"
    )
    full_prefix = (
        "exists cb cc. "
        f"({eisenstein_rectangle_row_count_prefix('p', 'q', 'k', 'cb', 'cc', 'h', tag='rectangle_count_full_prefix')})"
    )

    projection_prefix = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "cb", "cc", "l", tag="rectangle_count_projection_prefix"
    )
    projection_bound = _lt_term(
        "i",
        "l",
        tag="rectangle_count_projection_bound",
        variables=("p", "q", "k", "cb", "cc", "l", "i", "n"),
    )
    projection_entry = beta_at(
        "cb", "cc", "i", "n", tag="rectangle_count_projection_entry"
    )
    projection_witness = eisenstein_row_count_witness(
        "p", "q", "k", "i", "n", tag="rectangle_count_projection_witness"
    )

    total_prefix = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "cb", "cc", "h", tag="rectangle_count_total_prefix"
    )
    total_sum = sum_relation(
        "cb", "cc", "h", "total", tag="rectangle_count_total_sum"
    )
    total_result = (
        "exists cb cc total. "
        f"(({total_prefix}) /\\ ({total_sum}))"
    )

    common = (
        "p = 2 * h + 1 -> q = 2 * k + 1 -> "
        f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> "
    )

    return (
        spec(
            "distinct_odd_prime_half_row_count_choice",
            f"forall p q h k i. {common}({row_bound}) -> "
            f"exists n. ({point_witness})",
            ("distinct_odd_prime_half_row_count_exists",),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro i",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hi",
                f"have hpackage : {point_package}",
                "specialize distinct_odd_prime_half_row_count_exists p",
                "specialize distinct_odd_prime_half_row_count_exists q",
                "specialize distinct_odd_prime_half_row_count_exists h",
                "specialize distinct_odd_prime_half_row_count_exists k",
                "specialize distinct_odd_prime_half_row_count_exists i",
                "apply distinct_odd_prime_half_row_count_exists",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "cases hpackage",
                "cases hpackage_witness",
                "cases hpackage_witness_witness",
                "exists x2",
                "exists x",
                "exists x1",
                "exact hpackage_witness_witness_witness",
            ),
            "Each bounded row has one semantic row-count witness.",
        ),
        spec(
            "eisenstein_rectangle_row_count_prefix_extend",
            "forall p q k cb cc l. "
            f"({prefix_before}) -> (exists n. ({last_witness})) -> "
            f"exists z d. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro p",
                "intro q",
                "intro k",
                "intro cb",
                "intro cc",
                "intro l",
                "intro hprefix",
                "intro hchoice",
                "cases hchoice",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend cb",
                "specialize beta_prefix_extend cc",
                "specialize beta_prefix_extend x",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x1",
                "exists x2",
                "intro i",
                "intro hi",
                "have hsplit : i = l \/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists x",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hchoice_witness",
                f"have hold : exists oldcount. (({old_entry}) /\\ "
                f"({eisenstein_row_count_witness('p', 'q', 'k', 'i', 'oldcount', tag='rectangle_count_extend_old_witness')}))",
                "specialize hprefix i",
                "apply hprefix",
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
            "Append one semantic row count while preserving all earlier rows.",
        ),
        spec(
            "eisenstein_rectangle_row_count_prefix_exists",
            f"forall p q k l. ({choices_all}) -> ({prefix_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "le_succ",
                "le_refl",
                "eisenstein_rectangle_row_count_prefix_extend",
            ),
            (
                "intro p",
                "intro q",
                "intro k",
                "induction l",
                "intro hchoices",
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
                "intro hchoices",
                f"have hprevious_choices : {choices_previous}",
                "intro i",
                "intro hi",
                "specialize hchoices i",
                "apply hchoices",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                f"have hprevious : {previous_prefix}",
                "apply IH",
                "exact hprevious_choices",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hlast : exists n. ({eisenstein_row_count_witness('p', 'q', 'k', 'l', 'n', tag='rectangle_count_exists_last')})",
                "specialize hchoices l",
                "apply hchoices",
                "specialize le_refl (S l)",
                "exact le_refl",
                f"have hnext : {successor_prefix}",
                "specialize eisenstein_rectangle_row_count_prefix_extend p",
                "specialize eisenstein_rectangle_row_count_prefix_extend q",
                "specialize eisenstein_rectangle_row_count_prefix_extend k",
                "specialize eisenstein_rectangle_row_count_prefix_extend x",
                "specialize eisenstein_rectangle_row_count_prefix_extend x1",
                "specialize eisenstein_rectangle_row_count_prefix_extend l",
                "apply eisenstein_rectangle_row_count_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hlast",
                "exact hnext",
            ),
            "Every finite family of semantic row counts has an outer beta prefix.",
        ),
        spec(
            "distinct_odd_prime_half_row_count_choices_bounded",
            f"forall p q h k l. {common}({length_bound}) -> "
            f"({bounded_choices})",
            ("lt_of_lt_of_le", "distinct_odd_prime_half_row_count_choice"),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro l",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hlh",
                "intro i",
                "intro hil",
                f"have hih : {row_bound}",
                "specialize lt_of_lt_of_le i",
                "specialize lt_of_lt_of_le l",
                "specialize lt_of_lt_of_le h",
                "apply lt_of_lt_of_le",
                "exact hil",
                "exact hlh",
                "specialize distinct_odd_prime_half_row_count_choice p",
                "specialize distinct_odd_prime_half_row_count_choice q",
                "specialize distinct_odd_prime_half_row_count_choice h",
                "specialize distinct_odd_prime_half_row_count_choice k",
                "specialize distinct_odd_prime_half_row_count_choice i",
                "apply distinct_odd_prime_half_row_count_choice",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hih",
            ),
            "Every prefix length at most h has semantic row-count choices.",
        ),
        spec(
            "distinct_odd_prime_half_row_count_prefix_exists_bounded",
            f"forall p q h k l. {common}({length_bound}) -> "
            f"({bounded_prefix})",
            (
                "distinct_odd_prime_half_row_count_choices_bounded",
                "eisenstein_rectangle_row_count_prefix_exists",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro l",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hlh",
                f"have hchoices : {bounded_choices}",
                "specialize distinct_odd_prime_half_row_count_choices_bounded p",
                "specialize distinct_odd_prime_half_row_count_choices_bounded q",
                "specialize distinct_odd_prime_half_row_count_choices_bounded h",
                "specialize distinct_odd_prime_half_row_count_choices_bounded k",
                "specialize distinct_odd_prime_half_row_count_choices_bounded l",
                "apply distinct_odd_prime_half_row_count_choices_bounded",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hlh",
                "specialize eisenstein_rectangle_row_count_prefix_exists p",
                "specialize eisenstein_rectangle_row_count_prefix_exists q",
                "specialize eisenstein_rectangle_row_count_prefix_exists k",
                "specialize eisenstein_rectangle_row_count_prefix_exists l",
                "apply eisenstein_rectangle_row_count_prefix_exists",
                "exact hchoices",
            ),
            "Every bounded initial set of rows has a semantic count prefix.",
        ),
        spec(
            "distinct_odd_prime_half_row_count_prefix_exists",
            f"forall p q h k. {common}({full_prefix})",
            (
                "le_refl",
                "distinct_odd_prime_half_row_count_prefix_exists_bounded",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                f"have hle : {_le_term('h', 'h', tag='rectangle_count_full_reflexive', variables=('p', 'q', 'h', 'k'))}",
                "specialize le_refl h",
                "exact le_refl",
                "specialize distinct_odd_prime_half_row_count_prefix_exists_bounded p",
                "specialize distinct_odd_prime_half_row_count_prefix_exists_bounded q",
                "specialize distinct_odd_prime_half_row_count_prefix_exists_bounded h",
                "specialize distinct_odd_prime_half_row_count_prefix_exists_bounded k",
                "specialize distinct_odd_prime_half_row_count_prefix_exists_bounded h",
                "apply distinct_odd_prime_half_row_count_prefix_exists_bounded",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hle",
            ),
            "All h rows have one outer beta prefix of semantic counts.",
        ),
        spec(
            "eisenstein_rectangle_decoded_row_count",
            "forall p q k cb cc l i n. "
            f"({projection_prefix}) -> ({projection_bound}) -> "
            f"({projection_entry}) -> ({projection_witness})",
            ("beta_at_unique",),
            (
                "intro p",
                "intro q",
                "intro k",
                "intro cb",
                "intro cc",
                "intro l",
                "intro i",
                "intro n",
                "intro hprefix",
                "intro hi",
                "intro hentry",
                "have hstored : exists stored. "
                f"(({beta_at('cb', 'cc', 'i', 'stored', tag='rectangle_count_projection_stored')}) /\\ "
                f"({eisenstein_row_count_witness('p', 'q', 'k', 'i', 'stored', tag='rectangle_count_projection_stored_witness')}))",
                "specialize hprefix i",
                "apply hprefix",
                "exact hi",
                "cases hstored",
                "cases hstored_witness",
                "have heq : x = n",
                "specialize beta_at_unique cb",
                "specialize beta_at_unique cc",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "specialize beta_at_unique n",
                "apply beta_at_unique",
                "exact hstored_witness_left",
                "exact hentry",
                "rewrite heq at hstored_witness_right",
                "rewrite heq at hstored_witness_right",
                "exact hstored_witness_right",
            ),
            "Every decoded outer entry is semantically a BitCount of its row.",
        ),
        spec(
            "distinct_odd_prime_half_rectangle_total_exists",
            f"forall p q h k. {common}({total_result})",
            (
                "distinct_odd_prime_half_row_count_prefix_exists",
                "beta_sum_exists",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                f"have hprefix : {full_prefix}",
                "specialize distinct_odd_prime_half_row_count_prefix_exists p",
                "specialize distinct_odd_prime_half_row_count_prefix_exists q",
                "specialize distinct_odd_prime_half_row_count_prefix_exists h",
                "specialize distinct_odd_prime_half_row_count_prefix_exists k",
                "apply distinct_odd_prime_half_row_count_prefix_exists",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "cases hprefix",
                "cases hprefix_witness",
                f"have hsum : exists total. ({sum_relation('x', 'x1', 'h', 'total', tag='rectangle_count_total_witness_sum')})",
                "specialize beta_sum_exists x",
                "specialize beta_sum_exists x1",
                "specialize beta_sum_exists h",
                "exact beta_sum_exists",
                "cases hsum",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "exact hprefix_witness_witness",
                "exact hsum_witness",
            ),
            "The nested row counts have a native beta-sum rectangle total.",
        ),
    )


__all__ = [
    "eisenstein_rectangle_row_count_choices",
    "eisenstein_rectangle_row_count_prefix",
    "eisenstein_row_count_witness",
    "make_eisenstein_rectangle_count_candidate_theorems",
]
