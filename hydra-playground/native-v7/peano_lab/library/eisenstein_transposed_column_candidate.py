"""Construct whole transposed columns for the Eisenstein rectangle.

The swapped outer rectangle stores one existential inner row for every
``j < k``.  Fixing ``i < h`` therefore determines a semantic column: decode
the ``i``-th bit from every swapped row and beta-code those bits across
``j < k``.  Unlike a bare pointwise witness, the column prefix below retains
the outer entry, its inner row/count witness, and the decoded cell entry at
every position, so later Fubini infrastructure can recover its provenance.

The terminal candidate compares this whole column with one fixed original
row.  Pointwise transpose complementarity and the checked complementary-count
theorem then give ``row_count + column_count = k``.  This is not yet the
two-dimensional Fubini theorem: summing these column counts and identifying
that sum with the swapped outer total remains separate work.

All helpers expand before parsing to unchanged first-order Peano arithmetic.
The candidates are constructive, dependency-curried, unregistered, and
unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_division_threshold_candidate import _lt_term
from .eisenstein_rectangle_count_candidate import (
    eisenstein_rectangle_row_count_prefix,
    eisenstein_row_count_witness,
)
from .eisenstein_row_indicator_candidate import (
    eisenstein_cell_indicator_choice,
    eisenstein_row_indicator_prefix,
)
from .finite_fold_surface import all_bits, beta_at, bit_count


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
    names = tuple(f"etc_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated transposed-column binder captures an argument")
    return names


def _column_entry_witness_term(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
    row_index: str,
    bit: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    count, row_code, row_scale = _binders(
        tag, variables, ("count", "row_code", "row_scale")
    )
    outer_entry = beta_at(
        outer_code,
        outer_scale,
        row_index,
        count,
        tag=f"etc_{tag}_outer_entry",
    )
    # The outer prefix is the swapped (q,p) rectangle.
    row = eisenstein_row_indicator_prefix(
        prime_q,
        prime_p,
        row_index,
        row_code,
        row_scale,
        height,
        tag=f"etc_{tag}_row",
    )
    count_relation = bit_count(
        row_code,
        row_scale,
        height,
        count,
        tag=f"etc_{tag}_count_relation",
    )
    inner_entry = beta_at(
        row_code,
        row_scale,
        fixed_index,
        bit,
        tag=f"etc_{tag}_inner_entry",
    )
    return (
        f"exists {count} {row_code} {row_scale}. "
        f"(((({outer_entry}) /\\ ({row})) /\\ ({count_relation})) /\\ "
        f"({inner_entry}))"
    )


def eisenstein_transposed_column_entry_witness(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
    row_index: str,
    bit: str,
    *,
    tag: str,
) -> str:
    """Expand one decoded swapped-row cell with complete outer provenance."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (height, "column height"),
            (outer_code, "swapped outer code"),
            (outer_scale, "swapped outer scale"),
            (fixed_index, "fixed column index"),
            (row_index, "swapped row index"),
            (bit, "decoded bit"),
        )
    )
    return _column_entry_witness_term(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        fixed_index,
        row_index,
        bit,
        tag=tag,
        variables=variables,
    )


def _column_choices_term(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row_index, bit = _binders(tag, variables, ("row_index", "bit"))
    owned = variables + (row_index, bit)
    bound = _lt_term(
        row_index,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    witness = _column_entry_witness_term(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        fixed_index,
        row_index,
        bit,
        tag=f"{tag}_witness",
        variables=owned,
    )
    return f"forall {row_index}. ({bound}) -> exists {bit}. ({witness})"


def eisenstein_transposed_column_choices(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand pointwise choices for a bounded transposed column."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (height, "column height"),
            (outer_code, "swapped outer code"),
            (outer_scale, "swapped outer scale"),
            (fixed_index, "fixed column index"),
            (length, "column length"),
        )
    )
    return _column_choices_term(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        fixed_index,
        length,
        tag=tag,
        variables=variables,
    )


def _column_prefix_term(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    row_index, bit = _binders(tag, variables, ("row_index", "bit"))
    owned = variables + (row_index, bit)
    bound = _lt_term(
        row_index,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    decoded = beta_at(
        code, scale, row_index, bit, tag=f"etc_{tag}_decoded"
    )
    witness = _column_entry_witness_term(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        fixed_index,
        row_index,
        bit,
        tag=f"{tag}_witness",
        variables=owned,
    )
    return (
        f"forall {row_index}. ({bound}) -> exists {bit}. "
        f"(({decoded}) /\\ ({witness}))"
    )


def eisenstein_transposed_column_prefix(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a whole beta-coded column with swapped-row provenance."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (height, "column height"),
            (outer_code, "swapped outer code"),
            (outer_scale, "swapped outer scale"),
            (fixed_index, "fixed column index"),
            (code, "column code"),
            (scale, "column scale"),
            (length, "column length"),
        )
    )
    return _column_prefix_term(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        fixed_index,
        code,
        scale,
        length,
        tag=tag,
        variables=variables,
    )


def _successor_column_prefix(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
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
            (height, "column height"),
            (outer_code, "swapped outer code"),
            (outer_scale, "swapped outer scale"),
            (fixed_index, "fixed column index"),
            (code, "column code"),
            (scale, "column scale"),
            (predecessor, "column predecessor"),
        )
    )
    return _column_prefix_term(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        fixed_index,
        code,
        scale,
        f"S {predecessor}",
        tag=tag,
        variables=variables,
    )


def make_eisenstein_transposed_column_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build semantic column construction and row/column complement counts."""

    swapped_outer = eisenstein_rectangle_row_count_prefix(
        "q", "p", "h", "bb", "bc", "k", tag="transposed_column_outer"
    )
    fixed_bound = _lt_term(
        "i",
        "h",
        tag="transposed_column_fixed_bound",
        variables=("p", "q", "h", "k", "i", "bb", "bc"),
    )
    choices = eisenstein_transposed_column_choices(
        "p", "q", "h", "bb", "bc", "i", "k", tag="transposed_column_choices"
    )
    outer_entry = beta_at(
        "bb", "bc", "j", "m", tag="transposed_column_outer_entry"
    )
    outer_semantic = eisenstein_row_count_witness(
        "q", "p", "h", "j", "m", tag="transposed_column_outer_semantic"
    )
    outer_package = (
        f"exists m. (({outer_entry}) /\\ ({outer_semantic}))"
    )

    prefix_before = eisenstein_transposed_column_prefix(
        "p", "q", "h", "bb", "bc", "i", "z", "e", "l",
        tag="transposed_column_extend_before",
    )
    last_witness = eisenstein_transposed_column_entry_witness(
        "p", "q", "h", "bb", "bc", "i", "l", "d",
        tag="transposed_column_extend_last",
    )
    prefix_after = _successor_column_prefix(
        "p", "q", "h", "bb", "bc", "i", "u", "v", "l",
        tag="transposed_column_extend_after",
    )
    old_entry = beta_at(
        "z", "e", "j", "oldbit", tag="transposed_column_extend_old_entry"
    )
    old_witness = eisenstein_transposed_column_entry_witness(
        "p", "q", "h", "bb", "bc", "i", "j", "oldbit",
        tag="transposed_column_extend_old_witness",
    )

    prefix_result = (
        "exists z e. "
        f"({eisenstein_transposed_column_prefix('p', 'q', 'h', 'bb', 'bc', 'i', 'z', 'e', 'k', tag='transposed_column_exists_result')})"
    )
    previous_choices = eisenstein_transposed_column_choices(
        "p", "q", "h", "bb", "bc", "i", "k",
        tag="transposed_column_exists_previous_choices",
    )
    previous_prefix = (
        "exists z e. "
        f"({eisenstein_transposed_column_prefix('p', 'q', 'h', 'bb', 'bc', 'i', 'z', 'e', 'k', tag='transposed_column_exists_previous_prefix')})"
    )
    successor_prefix = (
        "exists z e. "
        f"({_successor_column_prefix('p', 'q', 'h', 'bb', 'bc', 'i', 'z', 'e', 'k', tag='transposed_column_exists_successor')})"
    )

    semantic_prefix = eisenstein_transposed_column_prefix(
        "p", "q", "h", "bb", "bc", "i", "z", "e", "k",
        tag="transposed_column_semantic_prefix",
    )
    column_bits = all_bits(
        "z", "e", "k", tag="transposed_column_all_bits"
    )

    original_row = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "k", tag="transposed_column_original_row"
    )
    original_count = bit_count(
        "rb", "rc", "k", "n", tag="transposed_column_original_count"
    )
    column_count = bit_count(
        "z", "e", "k", "m", tag="transposed_column_count"
    )
    row_entry = beta_at(
        "rb", "rc", "j", "a", tag="transposed_column_row_entry"
    )
    column_entry = beta_at(
        "z", "e", "j", "d", tag="transposed_column_column_entry"
    )
    pointwise_complement = (
        "((a = 0 /\\ d = 1) \\/ (a = 1 /\\ d = 0))"
    )

    endpoint_result = (
        "exists z e m. "
        f"(({eisenstein_transposed_column_prefix('p', 'q', 'h', 'bb', 'bc', 'i', 'z', 'e', 'k', tag='transposed_column_endpoint_prefix')}) /\\ "
        f"(({bit_count('z', 'e', 'k', 'm', tag='transposed_column_endpoint_count')}) /\\ "
        "n + m = k))"
    )

    return (
        spec(
            "eisenstein_transposed_outer_column_choices",
            "forall p q h k bb bc i. "
            f"({swapped_outer}) -> ({fixed_bound}) -> ({choices})",
            ("eisenstein_rectangle_decoded_row_count", "beta_at_exists"),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro bb", "intro bc", "intro i",
                "intro houter", "intro hi", "intro j", "intro hj",
                f"have hrow : {outer_package}",
                "specialize houter j",
                "apply houter",
                "exact hj",
                "cases hrow",
                "cases hrow_witness",
                "cases hrow_witness_right",
                "cases hrow_witness_right_witness",
                "cases hrow_witness_right_witness_witness",
                f"have hbit : exists d. ({beta_at('x1', 'x2', 'i', 'd', tag='transposed_column_choice_bit')})",
                "specialize beta_at_exists x1",
                "specialize beta_at_exists x2",
                "specialize beta_at_exists i",
                "exact beta_at_exists",
                "cases hbit",
                "exists x3",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "split",
                "split",
                "exact hrow_witness_left",
                "exact hrow_witness_right_witness_witness_left",
                "exact hrow_witness_right_witness_witness_right",
                "exact hbit_witness",
            ),
            "A fixed bounded index has one provenance-carrying bit in every swapped row.",
        ),
        spec(
            "eisenstein_transposed_column_prefix_extend",
            "forall p q h bb bc i z e l. "
            f"({prefix_before}) -> (exists d. ({last_witness})) -> "
            f"exists u v. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro p", "intro q", "intro h", "intro bb", "intro bc",
                "intro i", "intro z", "intro e", "intro l",
                "intro hprefix", "intro hlast", "cases hlast",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend z",
                "specialize beta_prefix_extend e",
                "specialize beta_prefix_extend x",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x1", "exists x2", "intro j", "intro hj",
                "have hsplit : j = l \/ exists gap. gap + S j = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt j",
                "apply finite_lt_succ_eq_or_lt",
                "exact hj",
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
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hlast_witness",
                f"have hold : exists oldbit. (({old_entry}) /\\ ({old_witness}))",
                "specialize hprefix j",
                "apply hprefix",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "exists x3",
                "split",
                "specialize beta_prefix_extend_witness_witness_right j",
                "specialize beta_prefix_extend_witness_witness_right x3",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_left",
                "exact hold_witness_right",
            ),
            "Append one provenance-carrying swapped-row bit to a transposed column.",
        ),
        spec(
            "eisenstein_transposed_column_prefix_exists",
            f"forall p q h bb bc i k. ({choices}) -> ({prefix_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "le_succ",
                "le_refl",
                "eisenstein_transposed_column_prefix_extend",
            ),
            (
                "intro p", "intro q", "intro h", "intro bb", "intro bc",
                "intro i", "induction k", "intro hchoices",
                "exists 0", "exists 0", "intro j", "intro hj", "exfalso",
                "cases hj",
                "have hsj : S j = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S j)",
                "apply add_eq_zero_right",
                "exact hj_witness",
                "specialize succ_ne_zero j",
                "apply succ_ne_zero",
                "exact hsj",
                "intro hchoices",
                f"have hprevious_choices : {previous_choices}",
                "intro j", "intro hj", "specialize hchoices j",
                "apply hchoices",
                "specialize le_succ (S j)",
                "specialize le_succ k",
                "apply le_succ",
                "exact hj",
                f"have hprevious : {previous_prefix}",
                "apply IH",
                "exact hprevious_choices",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hlast : exists d. ({eisenstein_transposed_column_entry_witness('p', 'q', 'h', 'bb', 'bc', 'i', 'k', 'd', tag='transposed_column_exists_last')})",
                "specialize hchoices k",
                "apply hchoices",
                "specialize le_refl (S k)",
                "exact le_refl",
                f"have hnext : {successor_prefix}",
                "specialize eisenstein_transposed_column_prefix_extend p",
                "specialize eisenstein_transposed_column_prefix_extend q",
                "specialize eisenstein_transposed_column_prefix_extend h",
                "specialize eisenstein_transposed_column_prefix_extend bb",
                "specialize eisenstein_transposed_column_prefix_extend bc",
                "specialize eisenstein_transposed_column_prefix_extend i",
                "specialize eisenstein_transposed_column_prefix_extend x",
                "specialize eisenstein_transposed_column_prefix_extend x1",
                "specialize eisenstein_transposed_column_prefix_extend k",
                "apply eisenstein_transposed_column_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hlast",
                "exact hnext",
            ),
            "Every finite family of swapped-row cell choices has one beta-coded column.",
        ),
        spec(
            "eisenstein_transposed_column_prefix_all_bits",
            "forall p q h bb bc i z e k. "
            f"({semantic_prefix}) -> ({fixed_bound}) -> ({column_bits})",
            ("eisenstein_row_indicator_decoded_choice",),
            (
                "intro p", "intro q", "intro h", "intro bb", "intro bc",
                "intro i", "intro z", "intro e", "intro k",
                "intro hprefix", "intro hi", "intro j", "intro hj",
                f"have hstored : exists d. (({beta_at('z', 'e', 'j', 'd', tag='transposed_column_bits_stored')}) /\\ ({eisenstein_transposed_column_entry_witness('p', 'q', 'h', 'bb', 'bc', 'i', 'j', 'd', tag='transposed_column_bits_witness')}))",
                "specialize hprefix j",
                "apply hprefix",
                "exact hj",
                "cases hstored",
                "cases hstored_witness",
                "cases hstored_witness_right",
                "cases hstored_witness_right_witness",
                "cases hstored_witness_right_witness_witness",
                "cases hstored_witness_right_witness_witness_witness",
                "cases hstored_witness_right_witness_witness_witness_left",
                "cases hstored_witness_right_witness_witness_witness_left_left",
                f"have hchoice : {eisenstein_cell_indicator_choice('q', 'p', 'j', 'i', 'x', tag='transposed_column_bits_choice')}",
                "specialize eisenstein_row_indicator_decoded_choice q",
                "specialize eisenstein_row_indicator_decoded_choice p",
                "specialize eisenstein_row_indicator_decoded_choice j",
                "specialize eisenstein_row_indicator_decoded_choice x2",
                "specialize eisenstein_row_indicator_decoded_choice x3",
                "specialize eisenstein_row_indicator_decoded_choice h",
                "specialize eisenstein_row_indicator_decoded_choice i",
                "specialize eisenstein_row_indicator_decoded_choice x",
                "apply eisenstein_row_indicator_decoded_choice",
                "exact hstored_witness_right_witness_witness_witness_left_left_right",
                "exact hi",
                "exact hstored_witness_right_witness_witness_witness_right",
                "exists x",
                "split",
                "exact hstored_witness_left",
                "cases hchoice",
                "cases hchoice_left",
                "left",
                "exact hchoice_left_left",
                "cases hchoice_right",
                "right",
                "exact hchoice_right_left",
            ),
            "Every provenance-carrying transposed column is a zero/one prefix.",
        ),
        spec(
            "eisenstein_transposed_column_pointwise_complement",
            "forall p q h k i rb rc bb bc z e j a d. "
            f"({original_row}) -> ({semantic_prefix}) -> ({fixed_bound}) -> "
            f"({_lt_term('j', 'k', tag='transposed_column_pointwise_bound', variables=('p', 'q', 'h', 'k', 'i', 'rb', 'rc', 'bb', 'bc', 'z', 'e', 'j', 'a', 'd'))}) -> "
            f"({row_entry}) -> ({column_entry}) -> {pointwise_complement}",
            (
                "beta_at_unique",
                "eisenstein_transposed_decoded_cell_bits_complementary",
            ),
            (
                "intro p", "intro q", "intro h", "intro k", "intro i",
                "intro rb", "intro rc", "intro bb", "intro bc", "intro z",
                "intro e", "intro j", "intro a", "intro d",
                "intro hrow", "intro hcolumn", "intro hi", "intro hj",
                "intro ha", "intro hd",
                f"have hstored : exists stored. (({beta_at('z', 'e', 'j', 'stored', tag='transposed_column_pointwise_stored')}) /\\ ({eisenstein_transposed_column_entry_witness('p', 'q', 'h', 'bb', 'bc', 'i', 'j', 'stored', tag='transposed_column_pointwise_witness')}))",
                "specialize hcolumn j",
                "apply hcolumn",
                "exact hj",
                "cases hstored",
                "cases hstored_witness",
                "have hsd : x = d",
                "specialize beta_at_unique z",
                "specialize beta_at_unique e",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x",
                "specialize beta_at_unique d",
                "apply beta_at_unique",
                "exact hstored_witness_left",
                "exact hd",
                "cases hstored_witness_right",
                "cases hstored_witness_right_witness",
                "cases hstored_witness_right_witness_witness",
                "cases hstored_witness_right_witness_witness_witness",
                "cases hstored_witness_right_witness_witness_witness_left",
                "cases hstored_witness_right_witness_witness_witness_left_left",
                "have hcomplement : ((a = 0 /\\ x = 1) \\/ (a = 1 /\\ x = 0))",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary p",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary q",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary h",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary k",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary i",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary j",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary rb",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary rc",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary x2",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary x3",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary a",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary x",
                "apply eisenstein_transposed_decoded_cell_bits_complementary",
                "exact hrow",
                "exact hstored_witness_right_witness_witness_witness_left_left_right",
                "exact hj",
                "exact hi",
                "exact ha",
                "exact hstored_witness_right_witness_witness_witness_right",
                "rewrite hsd at hcomplement",
                "rewrite hsd at hcomplement",
                "exact hcomplement",
            ),
            "Every decoded original-row bit and constructed column bit are exact complements.",
        ),
        spec(
            "eisenstein_row_transposed_column_count_partition",
            "forall p q h k i rb rc bb bc n. "
            f"({original_row}) -> ({original_count}) -> ({swapped_outer}) -> "
            f"({fixed_bound}) -> ({endpoint_result})",
            (
                "eisenstein_transposed_outer_column_choices",
                "eisenstein_transposed_column_prefix_exists",
                "eisenstein_transposed_column_prefix_all_bits",
                "bit_count_exists",
                "eisenstein_transposed_column_pointwise_complement",
                "complementary_bit_counts_add_length",
            ),
            (
                "intro p", "intro q", "intro h", "intro k", "intro i",
                "intro rb", "intro rc", "intro bb", "intro bc", "intro n",
                "intro hrow", "intro hrow_count", "intro houter", "intro hi",
                f"have hchoices : {choices}",
                "specialize eisenstein_transposed_outer_column_choices p",
                "specialize eisenstein_transposed_outer_column_choices q",
                "specialize eisenstein_transposed_outer_column_choices h",
                "specialize eisenstein_transposed_outer_column_choices k",
                "specialize eisenstein_transposed_outer_column_choices bb",
                "specialize eisenstein_transposed_outer_column_choices bc",
                "specialize eisenstein_transposed_outer_column_choices i",
                "apply eisenstein_transposed_outer_column_choices",
                "exact houter",
                "exact hi",
                f"have hprefix : {prefix_result}",
                "specialize eisenstein_transposed_column_prefix_exists p",
                "specialize eisenstein_transposed_column_prefix_exists q",
                "specialize eisenstein_transposed_column_prefix_exists h",
                "specialize eisenstein_transposed_column_prefix_exists bb",
                "specialize eisenstein_transposed_column_prefix_exists bc",
                "specialize eisenstein_transposed_column_prefix_exists i",
                "specialize eisenstein_transposed_column_prefix_exists k",
                "apply eisenstein_transposed_column_prefix_exists",
                "exact hchoices",
                "cases hprefix",
                "cases hprefix_witness",
                f"have hallbits : {all_bits('x', 'x1', 'k', tag='transposed_column_endpoint_all_bits')}",
                "specialize eisenstein_transposed_column_prefix_all_bits p",
                "specialize eisenstein_transposed_column_prefix_all_bits q",
                "specialize eisenstein_transposed_column_prefix_all_bits h",
                "specialize eisenstein_transposed_column_prefix_all_bits bb",
                "specialize eisenstein_transposed_column_prefix_all_bits bc",
                "specialize eisenstein_transposed_column_prefix_all_bits i",
                "specialize eisenstein_transposed_column_prefix_all_bits x",
                "specialize eisenstein_transposed_column_prefix_all_bits x1",
                "specialize eisenstein_transposed_column_prefix_all_bits k",
                "apply eisenstein_transposed_column_prefix_all_bits",
                "exact hprefix_witness_witness",
                "exact hi",
                f"have hcount : exists m. ({bit_count('x', 'x1', 'k', 'm', tag='transposed_column_endpoint_count_exists')})",
                "specialize bit_count_exists x",
                "specialize bit_count_exists x1",
                "specialize bit_count_exists k",
                "apply bit_count_exists",
                "exact hallbits",
                "cases hcount",
                "have hcomplement : forall j a d. "
                f"({_lt_term('j', 'k', tag='transposed_column_endpoint_complement_bound', variables=('p', 'q', 'h', 'k', 'i', 'rb', 'rc', 'bb', 'bc', 'n', 'j', 'a', 'd'))}) -> "
                f"({beta_at('rb', 'rc', 'j', 'a', tag='transposed_column_endpoint_complement_row')}) -> "
                f"({beta_at('x', 'x1', 'j', 'd', tag='transposed_column_endpoint_complement_column')}) -> "
                "((a = 0 /\\ d = 1) \\/ (a = 1 /\\ d = 0))",
                "intro j", "intro a", "intro d", "intro hj", "intro ha", "intro hd",
                "specialize eisenstein_transposed_column_pointwise_complement p",
                "specialize eisenstein_transposed_column_pointwise_complement q",
                "specialize eisenstein_transposed_column_pointwise_complement h",
                "specialize eisenstein_transposed_column_pointwise_complement k",
                "specialize eisenstein_transposed_column_pointwise_complement i",
                "specialize eisenstein_transposed_column_pointwise_complement rb",
                "specialize eisenstein_transposed_column_pointwise_complement rc",
                "specialize eisenstein_transposed_column_pointwise_complement bb",
                "specialize eisenstein_transposed_column_pointwise_complement bc",
                "specialize eisenstein_transposed_column_pointwise_complement x",
                "specialize eisenstein_transposed_column_pointwise_complement x1",
                "specialize eisenstein_transposed_column_pointwise_complement j",
                "specialize eisenstein_transposed_column_pointwise_complement a",
                "specialize eisenstein_transposed_column_pointwise_complement d",
                "apply eisenstein_transposed_column_pointwise_complement",
                "exact hrow",
                "exact hprefix_witness_witness",
                "exact hi",
                "exact hj",
                "exact ha",
                "exact hd",
                "have hpartition : n + x2 = k",
                "specialize complementary_bit_counts_add_length rb",
                "specialize complementary_bit_counts_add_length rc",
                "specialize complementary_bit_counts_add_length x",
                "specialize complementary_bit_counts_add_length x1",
                "specialize complementary_bit_counts_add_length k",
                "specialize complementary_bit_counts_add_length n",
                "specialize complementary_bit_counts_add_length x2",
                "apply complementary_bit_counts_add_length",
                "exact hrow_count",
                "exact hcount_witness",
                "exact hcomplement",
                "exists x", "exists x1", "exists x2", "split",
                "exact hprefix_witness_witness", "split",
                "exact hcount_witness", "exact hpartition",
            ),
            "One semantic row and the constructed whole transposed column partition all k cells.",
        ),
    )


__all__ = [
    "eisenstein_transposed_column_choices",
    "eisenstein_transposed_column_entry_witness",
    "eisenstein_transposed_column_prefix",
    "make_eisenstein_transposed_column_candidate_theorems",
]
