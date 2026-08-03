"""Constructive two-dimensional Fubini for the Eisenstein rectangle.

The earlier transposed-column layer constructs a genuine column at every
bounded horizontal index, while the row-decomposition layer splits every
successor-width swapped row into its predecessor row and terminal bit.  This
module closes the remaining extensional gap.  It introduces a deliberately
small semantic outer prefix whose entries are counts of genuine transposed
columns, proves that such column counts are independent of the particular
row-count beta codes used as provenance, and then inducts on the rectangle
width.

The main universal theorem says that *any* semantic column-count prefix has
the same Sum as the swapped semantic row-count prefix.  Consequently the
specific column-count prefix constructed by the complement argument has
``M = T``; composing with ``N + M = h * k`` gives the exact Eisenstein
floor-sum identity ``N + T = h * k``.

All surface helpers expand before parsing to ordinary first-order PA.
Candidates are constructive, dependency-curried, unregistered, and
unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_division_threshold_candidate import _lt_term
from .eisenstein_fubini_row_decomposition_candidate import (
    eisenstein_successor_row_split_prefix,
)
from .eisenstein_rectangle_count_candidate import (
    eisenstein_rectangle_row_count_prefix,
)
from .eisenstein_row_indicator_candidate import (
    eisenstein_cell_indicator_choice,
)
from .eisenstein_transposed_column_candidate import (
    eisenstein_transposed_column_choices,
    eisenstein_transposed_column_entry_witness,
    eisenstein_transposed_column_prefix,
)
from .eisenstein_transposed_column_count_candidate import (
    eisenstein_transposed_column_count_prefix,
    eisenstein_transposed_column_count_witness,
)
from .finite_fold_surface import all_bits, beta_at, bit_count, sum_relation


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
    names = tuple(f"eft_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Fubini-total binder captures an argument")
    return names


def _column_count_witness_term(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
    width: str,
    count: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    column_code, column_scale = _binders(
        tag, variables, ("column_code", "column_scale")
    )
    column = eisenstein_transposed_column_prefix(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        fixed_index,
        column_code,
        column_scale,
        width,
        tag=f"eft_{tag}_column",
    )
    count_relation = bit_count(
        column_code,
        column_scale,
        width,
        count,
        tag=f"eft_{tag}_count",
    )
    return (
        f"exists {column_code} {column_scale}. "
        f"(({column}) /\\ ({count_relation}))"
    )


def eisenstein_fubini_column_count_witness(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
    width: str,
    count: str,
    *,
    tag: str,
) -> str:
    """Expand one count of a genuine provenance-carrying column."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (height, "row width"),
            (outer_code, "swapped outer code"),
            (outer_scale, "swapped outer scale"),
            (fixed_index, "fixed column index"),
            (width, "column length"),
            (count, "column count"),
        )
    )
    return _column_count_witness_term(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        fixed_index,
        width,
        count,
        tag=tag,
        variables=variables,
    )


def _column_count_prefix_term(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    count_code: str,
    count_scale: str,
    length_term: str,
    width: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    fixed_index, count = _binders(tag, variables, ("fixed_index", "count"))
    owned = variables + (fixed_index, count)
    bound = _lt_term(
        fixed_index,
        length_term,
        tag=f"eft_{tag}_bound",
        variables=owned,
    )
    decoded = beta_at(
        count_code,
        count_scale,
        fixed_index,
        count,
        tag=f"eft_{tag}_decoded",
    )
    witness = _column_count_witness_term(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        fixed_index,
        width,
        count,
        tag=f"{tag}_witness",
        variables=owned,
    )
    return (
        f"forall {fixed_index}. ({bound}) -> exists {count}. "
        f"(({decoded}) /\\ ({witness}))"
    )


def eisenstein_fubini_column_count_prefix(
    prime_p: str,
    prime_q: str,
    height: str,
    outer_code: str,
    outer_scale: str,
    count_code: str,
    count_scale: str,
    length: str,
    width: str,
    *,
    tag: str,
) -> str:
    """Expand a beta prefix of genuine transposed-column counts."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (height, "row width"),
            (outer_code, "swapped outer code"),
            (outer_scale, "swapped outer scale"),
            (count_code, "column-count code"),
            (count_scale, "column-count scale"),
            (length, "column-count length"),
            (width, "column length"),
        )
    )
    return _column_count_prefix_term(
        prime_p,
        prime_q,
        height,
        outer_code,
        outer_scale,
        count_code,
        count_scale,
        length,
        width,
        tag=tag,
        variables=variables,
    )


def _at_successor_height(expanded: str, marker: str, predecessor: str) -> str:
    """Substitute the one compound height used by the induction body."""

    if marker not in expanded:
        raise AssertionError("successor-height marker disappeared during expansion")
    return expanded.replace(marker, f"S {predecessor}")


def _successor_column_count_witness(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    outer_code: str,
    outer_scale: str,
    fixed_index: str,
    width: str,
    count: str,
    *,
    tag: str,
) -> str:
    marker = "eftsuccessorheightwitnessmarker"
    expanded = eisenstein_fubini_column_count_witness(
        prime_p,
        prime_q,
        marker,
        outer_code,
        outer_scale,
        fixed_index,
        width,
        count,
        tag=tag,
    )
    return _at_successor_height(expanded, marker, predecessor)


def _successor_column_count_prefix(
    prime_p: str,
    prime_q: str,
    predecessor: str,
    outer_code: str,
    outer_scale: str,
    count_code: str,
    count_scale: str,
    length: str,
    width: str,
    *,
    tag: str,
) -> str:
    marker = "eftsuccessorheightprefixmarker"
    expanded = eisenstein_fubini_column_count_prefix(
        prime_p,
        prime_q,
        marker,
        outer_code,
        outer_scale,
        count_code,
        count_scale,
        length,
        width,
        tag=tag,
    )
    return _at_successor_height(expanded, marker, predecessor)


def _successor_row_split_prefix(
    prime_p: str,
    prime_q: str,
    predecessor: str,
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
    marker = "eftsuccessorheightsplitmarker"
    expanded = eisenstein_successor_row_split_prefix(
        prime_p,
        prime_q,
        predecessor,
        marker,
        outer_code,
        outer_scale,
        reduced_code,
        reduced_scale,
        terminal_code,
        terminal_scale,
        length,
        tag=tag,
    )
    return _at_successor_height(expanded, marker, predecessor)


def make_eisenstein_fubini_total_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build column extensionality, universal Fubini, and the exact endpoint."""

    source_column = eisenstein_transposed_column_prefix(
        "p", "q", "hs", "bs", "cs", "i", "zs", "es", "k",
        tag="fubini_total_source_column",
    )
    target_column = eisenstein_transposed_column_prefix(
        "p", "q", "ht", "bt", "ct", "i", "zt", "et", "k",
        tag="fubini_total_target_column",
    )
    source_fixed_bound = _lt_term(
        "i", "hs", tag="fubini_total_source_fixed_bound",
        variables=("p", "q", "hs", "ht", "bs", "cs", "bt", "ct", "i", "zs", "es", "zt", "et", "k", "n", "m"),
    )
    target_fixed_bound = _lt_term(
        "i", "ht", tag="fubini_total_target_fixed_bound",
        variables=("p", "q", "hs", "ht", "bs", "cs", "bt", "ct", "i", "zs", "es", "zt", "et", "k", "n", "m"),
    )
    row_bound = _lt_term(
        "j", "k", tag="fubini_total_row_bound",
        variables=("p", "q", "h", "bb", "bc", "i", "z", "e", "k", "j", "a"),
    )
    source_count = bit_count(
        "zs", "es", "k", "n", tag="fubini_total_source_count"
    )
    target_count = bit_count(
        "zt", "et", "k", "m", tag="fubini_total_target_count"
    )

    target_outer = eisenstein_rectangle_row_count_prefix(
        "q", "p", "ht", "bt", "ct", "k",
        tag="fubini_total_retarget_outer",
    )
    source_witness = eisenstein_fubini_column_count_witness(
        "p", "q", "hs", "bs", "cs", "i", "k", "n",
        tag="fubini_total_retarget_source",
    )
    target_witness = eisenstein_fubini_column_count_witness(
        "p", "q", "ht", "bt", "ct", "i", "k", "n",
        tag="fubini_total_retarget_target",
    )

    successor_prefix = eisenstein_fubini_column_count_prefix(
        "p", "q", "sh", "bb", "bc", "db", "dc", "sh", "k",
        tag="fubini_total_restrict_successor",
    )
    predecessor_prefix = eisenstein_fubini_column_count_prefix(
        "p", "q", "sh", "bb", "bc", "db", "dc", "h", "k",
        tag="fubini_total_restrict_predecessor",
    )
    retarget_source_prefix = eisenstein_fubini_column_count_prefix(
        "p", "q", "sh", "bb", "bc", "db", "dc", "h", "k",
        tag="fubini_total_retarget_source_prefix",
    )
    retarget_target_prefix = eisenstein_fubini_column_count_prefix(
        "p", "q", "h", "rb", "rc", "db", "dc", "h", "k",
        tag="fubini_total_retarget_target_prefix",
    )
    reduced_outer = eisenstein_rectangle_row_count_prefix(
        "q", "p", "h", "rb", "rc", "k",
        tag="fubini_total_retarget_reduced_outer",
    )

    general_outer = eisenstein_rectangle_row_count_prefix(
        "q", "p", "h", "bb", "bc", "k",
        tag="fubini_total_general_outer",
    )
    general_columns = eisenstein_fubini_column_count_prefix(
        "p", "q", "h", "bb", "bc", "db", "dc", "h", "k",
        tag="fubini_total_general_columns",
    )
    general_outer_sum = sum_relation(
        "bb", "bc", "k", "T", tag="fubini_total_general_outer_sum"
    )
    general_column_sum = sum_relation(
        "db", "dc", "h", "M", tag="fubini_total_general_column_sum"
    )

    split_prefix = eisenstein_successor_row_split_prefix(
        "q", "p", "h", "sh", "bb", "bc", "rb", "rc", "tb", "tc", "k",
        tag="fubini_total_successor_split",
    )

    constructed_prefix = eisenstein_transposed_column_count_prefix(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "db", "dc", "h",
        tag="fubini_total_constructed_prefix",
    )
    forgotten_prefix = eisenstein_fubini_column_count_prefix(
        "p", "q", "h", "bb", "bc", "db", "dc", "h", "k",
        tag="fubini_total_forgotten_prefix",
    )

    first_outer = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "ab", "ac", "h",
        tag="fubini_total_identity_first_outer",
    )
    second_outer = eisenstein_rectangle_row_count_prefix(
        "q", "p", "h", "bb", "bc", "k",
        tag="fubini_total_identity_second_outer",
    )
    first_sum = sum_relation(
        "ab", "ac", "h", "N", tag="fubini_total_identity_first_sum"
    )
    second_sum = sum_relation(
        "bb", "bc", "k", "T", tag="fubini_total_identity_second_sum"
    )

    return (
        spec(
            "eisenstein_transposed_column_decoded_choice",
            "forall p q h bb bc i z e k j a. "
            f"({eisenstein_transposed_column_prefix('p', 'q', 'h', 'bb', 'bc', 'i', 'z', 'e', 'k', tag='fubini_total_decoded_choice_column')}) -> "
            f"({_lt_term('i', 'h', tag='fubini_total_decoded_choice_fixed_bound', variables=('p', 'q', 'h', 'bb', 'bc', 'i', 'z', 'e', 'k', 'j', 'a'))}) -> "
            f"({row_bound}) -> "
            f"({beta_at('z', 'e', 'j', 'a', tag='fubini_total_decoded_choice_entry')}) -> "
            f"({eisenstein_cell_indicator_choice('q', 'p', 'j', 'i', 'a', tag='fubini_total_decoded_choice_result')})",
            (
                "beta_at_unique",
                "eisenstein_row_indicator_decoded_choice",
            ),
            (
                "intro p", "intro q", "intro h", "intro bb", "intro bc",
                "intro i", "intro z", "intro e", "intro k", "intro j",
                "intro a", "intro hcolumn", "intro hi", "intro hj", "intro ha",
                "have hstored : exists d. "
                f"(({beta_at('z', 'e', 'j', 'd', tag='fubini_total_decoded_choice_stored_entry')}) /\\ "
                f"({eisenstein_transposed_column_entry_witness('p', 'q', 'h', 'bb', 'bc', 'i', 'j', 'd', tag='fubini_total_decoded_choice_stored_witness')}))",
                "specialize hcolumn j", "apply hcolumn", "exact hj",
                "cases hstored", "cases hstored_witness",
                "have hda : x = a",
                "specialize beta_at_unique z", "specialize beta_at_unique e",
                "specialize beta_at_unique j", "specialize beta_at_unique x",
                "specialize beta_at_unique a", "apply beta_at_unique",
                "exact hstored_witness_left", "exact ha",
                "cases hstored_witness_right",
                "cases hstored_witness_right_witness",
                "cases hstored_witness_right_witness_witness",
                "cases hstored_witness_right_witness_witness_witness",
                "cases hstored_witness_right_witness_witness_witness_left",
                "cases hstored_witness_right_witness_witness_witness_left_left",
                f"have hchoice : {eisenstein_cell_indicator_choice('q', 'p', 'j', 'i', 'x', tag='fubini_total_decoded_choice_stored_choice')}",
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
                "rewrite hda at hchoice", "rewrite hda at hchoice",
                "exact hchoice",
            ),
            "A decoded entry of any genuine transposed column has the exact Eisenstein cell orientation.",
        ),
        spec(
            "eisenstein_transposed_column_counts_extensional",
            "forall p q hs ht bs cs bt ct i zs es zt et k n m. "
            f"({source_column}) -> ({target_column}) -> "
            f"({source_fixed_bound}) -> ({target_fixed_bound}) -> "
            f"({source_count}) -> ({target_count}) -> n = m",
            (
                "beta_at_exists",
                "eisenstein_transposed_column_decoded_choice",
                "eisenstein_cell_indicator_choice_unique",
                "beta_sum_transport_prefix",
                "beta_sum_functional",
            ),
            (
                "intro p", "intro q", "intro hs", "intro ht",
                "intro bs", "intro cs", "intro bt", "intro ct", "intro i",
                "intro zs", "intro es", "intro zt", "intro et", "intro k",
                "intro n", "intro m", "intro hsource", "intro htarget",
                "intro his", "intro hit", "intro hn", "intro hm",
                "cases hn", "cases hm",
                "have htransport : forall j a. "
                f"({_lt_term('j', 'k', tag='fubini_total_extensional_transport_bound', variables=('p', 'q', 'hs', 'ht', 'bs', 'cs', 'bt', 'ct', 'i', 'zs', 'es', 'zt', 'et', 'k', 'n', 'm', 'j', 'a'))}) -> "
                f"({beta_at('zs', 'es', 'j', 'a', tag='fubini_total_extensional_transport_source')}) -> "
                f"({beta_at('zt', 'et', 'j', 'a', tag='fubini_total_extensional_transport_target')})",
                "intro j", "intro a", "intro hj", "intro ha",
                "have htarget_entry : exists d. "
                f"({beta_at('zt', 'et', 'j', 'd', tag='fubini_total_extensional_target_entry')})",
                "specialize beta_at_exists zt", "specialize beta_at_exists et",
                "specialize beta_at_exists j", "exact beta_at_exists",
                "cases htarget_entry",
                f"have hsource_choice : {eisenstein_cell_indicator_choice('q', 'p', 'j', 'i', 'a', tag='fubini_total_extensional_source_choice')}",
                "specialize eisenstein_transposed_column_decoded_choice p",
                "specialize eisenstein_transposed_column_decoded_choice q",
                "specialize eisenstein_transposed_column_decoded_choice hs",
                "specialize eisenstein_transposed_column_decoded_choice bs",
                "specialize eisenstein_transposed_column_decoded_choice cs",
                "specialize eisenstein_transposed_column_decoded_choice i",
                "specialize eisenstein_transposed_column_decoded_choice zs",
                "specialize eisenstein_transposed_column_decoded_choice es",
                "specialize eisenstein_transposed_column_decoded_choice k",
                "specialize eisenstein_transposed_column_decoded_choice j",
                "specialize eisenstein_transposed_column_decoded_choice a",
                "apply eisenstein_transposed_column_decoded_choice",
                "exact hsource", "exact his", "exact hj", "exact ha",
                f"have htarget_choice : {eisenstein_cell_indicator_choice('q', 'p', 'j', 'i', 'x', tag='fubini_total_extensional_target_choice')}",
                "specialize eisenstein_transposed_column_decoded_choice p",
                "specialize eisenstein_transposed_column_decoded_choice q",
                "specialize eisenstein_transposed_column_decoded_choice ht",
                "specialize eisenstein_transposed_column_decoded_choice bt",
                "specialize eisenstein_transposed_column_decoded_choice ct",
                "specialize eisenstein_transposed_column_decoded_choice i",
                "specialize eisenstein_transposed_column_decoded_choice zt",
                "specialize eisenstein_transposed_column_decoded_choice et",
                "specialize eisenstein_transposed_column_decoded_choice k",
                "specialize eisenstein_transposed_column_decoded_choice j",
                "specialize eisenstein_transposed_column_decoded_choice x",
                "apply eisenstein_transposed_column_decoded_choice",
                "exact htarget", "exact hit", "exact hj",
                "exact htarget_entry_witness",
                "have hax : a = x",
                "specialize eisenstein_cell_indicator_choice_unique q",
                "specialize eisenstein_cell_indicator_choice_unique p",
                "specialize eisenstein_cell_indicator_choice_unique j",
                "specialize eisenstein_cell_indicator_choice_unique i",
                "specialize eisenstein_cell_indicator_choice_unique a",
                "specialize eisenstein_cell_indicator_choice_unique x",
                "apply eisenstein_cell_indicator_choice_unique",
                "exact hsource_choice", "exact htarget_choice",
                "rewrite <- hax at htarget_entry_witness",
                "rewrite <- hax at htarget_entry_witness",
                "exact htarget_entry_witness",
                "have htarget_n : "
                f"{sum_relation('zt', 'et', 'k', 'n', tag='fubini_total_extensional_transported_sum')}",
                "specialize beta_sum_transport_prefix zs",
                "specialize beta_sum_transport_prefix es",
                "specialize beta_sum_transport_prefix zt",
                "specialize beta_sum_transport_prefix et",
                "specialize beta_sum_transport_prefix k",
                "specialize beta_sum_transport_prefix n",
                "apply beta_sum_transport_prefix",
                "exact hn_left", "exact htransport",
                "specialize beta_sum_functional zt",
                "specialize beta_sum_functional et",
                "specialize beta_sum_functional k",
                "specialize beta_sum_functional n",
                "specialize beta_sum_functional m",
                "apply beta_sum_functional",
                "exact htarget_n", "exact hm_left",
            ),
            "Counts of extensionally identical semantic transposed columns are equal across arbitrary provenance codes.",
        ),
        spec(
            "eisenstein_fubini_column_count_witness_retarget",
            "forall p q hs ht bs cs bt ct i k n. "
            f"({target_outer}) -> ({source_fixed_bound}) -> ({target_fixed_bound}) -> "
            f"({source_witness}) -> ({target_witness})",
            (
                "eisenstein_transposed_outer_column_choices",
                "eisenstein_transposed_column_prefix_exists",
                "eisenstein_transposed_column_prefix_all_bits",
                "bit_count_exists",
                "eisenstein_transposed_column_counts_extensional",
            ),
            (
                "intro p", "intro q", "intro hs", "intro ht",
                "intro bs", "intro cs", "intro bt", "intro ct",
                "intro i", "intro k", "intro n",
                "intro houter", "intro his", "intro hit", "intro hsource",
                "cases hsource", "cases hsource_witness",
                "cases hsource_witness_witness",
                f"have hchoices : {eisenstein_transposed_column_choices('p', 'q', 'ht', 'bt', 'ct', 'i', 'k', tag='fubini_total_retarget_choices')}",
                "specialize eisenstein_transposed_outer_column_choices p",
                "specialize eisenstein_transposed_outer_column_choices q",
                "specialize eisenstein_transposed_outer_column_choices ht",
                "specialize eisenstein_transposed_outer_column_choices k",
                "specialize eisenstein_transposed_outer_column_choices bt",
                "specialize eisenstein_transposed_outer_column_choices ct",
                "specialize eisenstein_transposed_outer_column_choices i",
                "apply eisenstein_transposed_outer_column_choices",
                "exact houter", "exact hit",
                "have hprefix : exists z e. "
                f"({eisenstein_transposed_column_prefix('p', 'q', 'ht', 'bt', 'ct', 'i', 'z', 'e', 'k', tag='fubini_total_retarget_built_prefix')})",
                "specialize eisenstein_transposed_column_prefix_exists p",
                "specialize eisenstein_transposed_column_prefix_exists q",
                "specialize eisenstein_transposed_column_prefix_exists ht",
                "specialize eisenstein_transposed_column_prefix_exists bt",
                "specialize eisenstein_transposed_column_prefix_exists ct",
                "specialize eisenstein_transposed_column_prefix_exists i",
                "specialize eisenstein_transposed_column_prefix_exists k",
                "apply eisenstein_transposed_column_prefix_exists",
                "exact hchoices",
                "cases hprefix", "cases hprefix_witness",
                f"have hallbits : {all_bits('x2', 'x3', 'k', tag='fubini_total_retarget_all_bits')}",
                "specialize eisenstein_transposed_column_prefix_all_bits p",
                "specialize eisenstein_transposed_column_prefix_all_bits q",
                "specialize eisenstein_transposed_column_prefix_all_bits ht",
                "specialize eisenstein_transposed_column_prefix_all_bits bt",
                "specialize eisenstein_transposed_column_prefix_all_bits ct",
                "specialize eisenstein_transposed_column_prefix_all_bits i",
                "specialize eisenstein_transposed_column_prefix_all_bits x2",
                "specialize eisenstein_transposed_column_prefix_all_bits x3",
                "specialize eisenstein_transposed_column_prefix_all_bits k",
                "apply eisenstein_transposed_column_prefix_all_bits",
                "exact hprefix_witness_witness", "exact hit",
                "have hcount : exists m. "
                f"({bit_count('x2', 'x3', 'k', 'm', tag='fubini_total_retarget_built_count')})",
                "specialize bit_count_exists x2", "specialize bit_count_exists x3",
                "specialize bit_count_exists k", "apply bit_count_exists",
                "exact hallbits", "cases hcount",
                "have heq : n = x4",
                "specialize eisenstein_transposed_column_counts_extensional p",
                "specialize eisenstein_transposed_column_counts_extensional q",
                "specialize eisenstein_transposed_column_counts_extensional hs",
                "specialize eisenstein_transposed_column_counts_extensional ht",
                "specialize eisenstein_transposed_column_counts_extensional bs",
                "specialize eisenstein_transposed_column_counts_extensional cs",
                "specialize eisenstein_transposed_column_counts_extensional bt",
                "specialize eisenstein_transposed_column_counts_extensional ct",
                "specialize eisenstein_transposed_column_counts_extensional i",
                "specialize eisenstein_transposed_column_counts_extensional x",
                "specialize eisenstein_transposed_column_counts_extensional x1",
                "specialize eisenstein_transposed_column_counts_extensional x2",
                "specialize eisenstein_transposed_column_counts_extensional x3",
                "specialize eisenstein_transposed_column_counts_extensional k",
                "specialize eisenstein_transposed_column_counts_extensional n",
                "specialize eisenstein_transposed_column_counts_extensional x4",
                "apply eisenstein_transposed_column_counts_extensional",
                "exact hsource_witness_witness_left",
                "exact hprefix_witness_witness", "exact his", "exact hit",
                "exact hsource_witness_witness_right", "exact hcount_witness",
                "exists x2", "exists x3", "split",
                "exact hprefix_witness_witness",
                "rewrite heq", "rewrite heq", "exact hcount_witness",
            ),
            "Rebuild a counted column over another semantic outer code without changing its count.",
        ),
        spec(
            "eisenstein_fubini_column_count_prefix_succ_restrict",
            "forall p q h sh bb bc db dc k. sh = S h -> "
            f"({successor_prefix}) -> ({predecessor_prefix})",
            ("le_succ",),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro db", "intro dc", "intro k",
                "intro hsh", "intro hprefix", "rewrite hsh at hprefix",
                "intro i", "intro hi", "specialize hprefix i", "apply hprefix",
                "specialize le_succ (S i)", "specialize le_succ h",
                "apply le_succ", "exact hi",
            ),
            "A semantic column-count prefix restricts from successor length to predecessor length.",
        ),
        spec(
            "eisenstein_fubini_column_count_prefix_retarget_predecessor",
            "forall p q h sh bb bc rb rc db dc k. sh = S h -> "
            f"({reduced_outer}) -> ({retarget_source_prefix}) -> "
            f"({retarget_target_prefix})",
            (
                "le_succ",
                "eisenstein_fubini_column_count_witness_retarget",
            ),
            (
                "intro p", "intro q", "intro h", "intro sh",
                "intro bb", "intro bc", "intro rb", "intro rc",
                "intro db", "intro dc", "intro k",
                "intro hsh", "intro houter", "intro hsource",
                "intro i", "intro hi",
                "have hstored : exists n. "
                f"(({beta_at('db', 'dc', 'i', 'n', tag='fubini_total_retarget_prefix_stored_entry')}) /\\ "
                f"({eisenstein_fubini_column_count_witness('p', 'q', 'sh', 'bb', 'bc', 'i', 'k', 'n', tag='fubini_total_retarget_prefix_stored_witness')}))",
                "specialize hsource i", "apply hsource", "exact hi",
                "cases hstored", "cases hstored_witness",
                "have his : "
                f"{_lt_term('i', 'sh', tag='fubini_total_retarget_prefix_source_bound', variables=('p', 'q', 'h', 'sh', 'bb', 'bc', 'rb', 'rc', 'db', 'dc', 'k', 'i'))}",
                "rewrite hsh",
                "specialize le_succ (S i)", "specialize le_succ h",
                "apply le_succ", "exact hi",
                f"have htarget : {eisenstein_fubini_column_count_witness('p', 'q', 'h', 'rb', 'rc', 'i', 'k', 'x', tag='fubini_total_retarget_prefix_target_witness')}",
                "specialize eisenstein_fubini_column_count_witness_retarget p",
                "specialize eisenstein_fubini_column_count_witness_retarget q",
                "specialize eisenstein_fubini_column_count_witness_retarget sh",
                "specialize eisenstein_fubini_column_count_witness_retarget h",
                "specialize eisenstein_fubini_column_count_witness_retarget bb",
                "specialize eisenstein_fubini_column_count_witness_retarget bc",
                "specialize eisenstein_fubini_column_count_witness_retarget rb",
                "specialize eisenstein_fubini_column_count_witness_retarget rc",
                "specialize eisenstein_fubini_column_count_witness_retarget i",
                "specialize eisenstein_fubini_column_count_witness_retarget k",
                "specialize eisenstein_fubini_column_count_witness_retarget x",
                "apply eisenstein_fubini_column_count_witness_retarget",
                "exact houter", "exact his", "exact hi",
                "exact hstored_witness_right",
                "exists x", "split",
                "exact hstored_witness_left", "exact htarget",
            ),
            "Retarget every predecessor column count from the successor outer code to the reduced semantic rows.",
        ),
        spec(
            "eisenstein_fubini_universal",
            "forall h p q k bb bc db dc T M. "
            f"({general_outer}) -> ({general_columns}) -> "
            f"({general_outer_sum}) -> ({general_column_sum}) -> M = T",
            (
                "beta_sum_zero",
                "eisenstein_zero_width_rectangle_sum_zero",
                "eisenstein_successor_rectangle_row_split_prefix_exists",
                "eisenstein_successor_row_split_reduced_rectangle_prefix",
                "beta_sum_exists",
                "eisenstein_successor_row_split_sum_add",
                "eisenstein_fubini_column_count_prefix_succ_restrict",
                "eisenstein_fubini_column_count_prefix_retarget_predecessor",
                "beta_sum_succ_decompose",
                "le_refl",
                "beta_at_unique",
                "eisenstein_successor_terminal_sum_matches_last_column",
            ),
            (
                "intro h", "induction h",
                "intro p", "intro q", "intro k", "intro bb", "intro bc",
                "intro db", "intro dc", "intro T", "intro M",
                "intro houter", "intro hcolumns", "intro houtersum", "intro hcolumnsum",
                "have hmzero : M = 0",
                "specialize beta_sum_zero db", "specialize beta_sum_zero dc",
                "specialize beta_sum_zero M", "apply beta_sum_zero",
                "exact hcolumnsum",
                "have htzero : T = 0",
                "specialize eisenstein_zero_width_rectangle_sum_zero q",
                "specialize eisenstein_zero_width_rectangle_sum_zero p",
                "specialize eisenstein_zero_width_rectangle_sum_zero 0",
                "specialize eisenstein_zero_width_rectangle_sum_zero bb",
                "specialize eisenstein_zero_width_rectangle_sum_zero bc",
                "specialize eisenstein_zero_width_rectangle_sum_zero k",
                "specialize eisenstein_zero_width_rectangle_sum_zero T",
                "apply eisenstein_zero_width_rectangle_sum_zero",
                "refl", "exact houter", "exact houtersum",
                "trans 0", "exact hmzero", "symm", "exact htzero",
                "intro p", "intro q", "intro k", "intro bb", "intro bc",
                "intro db", "intro dc", "intro T", "intro M",
                "intro houter", "intro hcolumns", "intro houtersum", "intro hcolumnsum",
                "have hsplit_exists : exists rb rc tb tc. "
                f"({_successor_row_split_prefix('q', 'p', 'h', 'bb', 'bc', 'rb', 'rc', 'tb', 'tc', 'k', tag='fubini_total_universal_split_exists')})",
                "specialize eisenstein_successor_rectangle_row_split_prefix_exists q",
                "specialize eisenstein_successor_rectangle_row_split_prefix_exists p",
                "specialize eisenstein_successor_rectangle_row_split_prefix_exists h",
                "specialize eisenstein_successor_rectangle_row_split_prefix_exists (S h)",
                "specialize eisenstein_successor_rectangle_row_split_prefix_exists bb",
                "specialize eisenstein_successor_rectangle_row_split_prefix_exists bc",
                "specialize eisenstein_successor_rectangle_row_split_prefix_exists k",
                "apply eisenstein_successor_rectangle_row_split_prefix_exists",
                "refl", "exact houter",
                "cases hsplit_exists", "cases hsplit_exists_witness",
                "cases hsplit_exists_witness_witness",
                "cases hsplit_exists_witness_witness_witness",
                f"have hreduced_outer : {eisenstein_rectangle_row_count_prefix('q', 'p', 'h', 'x', 'x1', 'k', tag='fubini_total_universal_reduced_outer')}",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix q",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix p",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix h",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix (S h)",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix bb",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix bc",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix x",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix x1",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix x2",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix x3",
                "specialize eisenstein_successor_row_split_reduced_rectangle_prefix k",
                "apply eisenstein_successor_row_split_reduced_rectangle_prefix",
                "exact hsplit_exists_witness_witness_witness_witness",
                "have hreduced_sum : exists R. "
                f"({sum_relation('x', 'x1', 'k', 'R', tag='fubini_total_universal_reduced_sum')})",
                "specialize beta_sum_exists x", "specialize beta_sum_exists x1",
                "specialize beta_sum_exists k", "exact beta_sum_exists",
                "cases hreduced_sum",
                "have hterminal_sum : exists D. "
                f"({sum_relation('x2', 'x3', 'k', 'D', tag='fubini_total_universal_terminal_sum')})",
                "specialize beta_sum_exists x2", "specialize beta_sum_exists x3",
                "specialize beta_sum_exists k", "exact beta_sum_exists",
                "cases hterminal_sum",
                "have hsource_add : x4 + x5 = T",
                "specialize eisenstein_successor_row_split_sum_add q",
                "specialize eisenstein_successor_row_split_sum_add p",
                "specialize eisenstein_successor_row_split_sum_add h",
                "specialize eisenstein_successor_row_split_sum_add (S h)",
                "specialize eisenstein_successor_row_split_sum_add bb",
                "specialize eisenstein_successor_row_split_sum_add bc",
                "specialize eisenstein_successor_row_split_sum_add x",
                "specialize eisenstein_successor_row_split_sum_add x1",
                "specialize eisenstein_successor_row_split_sum_add x2",
                "specialize eisenstein_successor_row_split_sum_add x3",
                "specialize eisenstein_successor_row_split_sum_add k",
                "specialize eisenstein_successor_row_split_sum_add x4",
                "specialize eisenstein_successor_row_split_sum_add x5",
                "specialize eisenstein_successor_row_split_sum_add T",
                "apply eisenstein_successor_row_split_sum_add",
                "exact hsplit_exists_witness_witness_witness_witness",
                "exact hreduced_sum_witness", "exact hterminal_sum_witness",
                "exact houtersum",
                f"have hrestricted_columns : {_successor_column_count_prefix('p', 'q', 'h', 'bb', 'bc', 'db', 'dc', 'h', 'k', tag='fubini_total_universal_restricted_columns')}",
                "specialize eisenstein_fubini_column_count_prefix_succ_restrict p",
                "specialize eisenstein_fubini_column_count_prefix_succ_restrict q",
                "specialize eisenstein_fubini_column_count_prefix_succ_restrict h",
                "specialize eisenstein_fubini_column_count_prefix_succ_restrict (S h)",
                "specialize eisenstein_fubini_column_count_prefix_succ_restrict bb",
                "specialize eisenstein_fubini_column_count_prefix_succ_restrict bc",
                "specialize eisenstein_fubini_column_count_prefix_succ_restrict db",
                "specialize eisenstein_fubini_column_count_prefix_succ_restrict dc",
                "specialize eisenstein_fubini_column_count_prefix_succ_restrict k",
                "apply eisenstein_fubini_column_count_prefix_succ_restrict",
                "refl", "exact hcolumns",
                f"have hreduced_columns : {eisenstein_fubini_column_count_prefix('p', 'q', 'h', 'x', 'x1', 'db', 'dc', 'h', 'k', tag='fubini_total_universal_reduced_columns')}",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor p",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor q",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor h",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor (S h)",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor bb",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor bc",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor x",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor x1",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor db",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor dc",
                "specialize eisenstein_fubini_column_count_prefix_retarget_predecessor k",
                "apply eisenstein_fubini_column_count_prefix_retarget_predecessor",
                "refl", "exact hreduced_outer", "exact hrestricted_columns",
                "have hsum_decompose : exists a r. "
                f"(({beta_at('db', 'dc', 'h', 'a', tag='fubini_total_universal_column_last_entry')}) /\\ "
                f"(({sum_relation('db', 'dc', 'h', 'r', tag='fubini_total_universal_column_prefix_sum')}) /\\ M = r + a))",
                "specialize beta_sum_succ_decompose db",
                "specialize beta_sum_succ_decompose dc",
                "specialize beta_sum_succ_decompose h",
                "specialize beta_sum_succ_decompose M",
                "apply beta_sum_succ_decompose", "exact hcolumnsum",
                "cases hsum_decompose", "cases hsum_decompose_witness",
                "cases hsum_decompose_witness_witness",
                "cases hsum_decompose_witness_witness_right",
                "have hih : x7 = x4",
                "specialize IH p", "specialize IH q", "specialize IH k",
                "specialize IH x", "specialize IH x1",
                "specialize IH db", "specialize IH dc",
                "specialize IH x4", "specialize IH x7", "apply IH",
                "exact hreduced_outer", "exact hreduced_columns",
                "exact hreduced_sum_witness",
                "exact hsum_decompose_witness_witness_right_left",
                "have hlast_stored : exists n. "
                f"(({beta_at('db', 'dc', 'h', 'n', tag='fubini_total_universal_last_stored_entry')}) /\\ "
                f"({_successor_column_count_witness('p', 'q', 'h', 'bb', 'bc', 'h', 'k', 'n', tag='fubini_total_universal_last_stored_witness')}))",
                "specialize hcolumns h", "apply hcolumns",
                "specialize le_refl (S h)", "exact le_refl",
                "cases hlast_stored", "cases hlast_stored_witness",
                "cases hlast_stored_witness_right",
                "cases hlast_stored_witness_right_witness",
                "cases hlast_stored_witness_right_witness_witness",
                "cases hlast_stored_witness_right_witness_witness_right",
                "have hcount_eq : x8 = x6",
                "specialize beta_at_unique db", "specialize beta_at_unique dc",
                "specialize beta_at_unique h", "specialize beta_at_unique x8",
                "specialize beta_at_unique x6", "apply beta_at_unique",
                "exact hlast_stored_witness_left",
                "exact hsum_decompose_witness_witness_left",
                "have hterminal_eq : x5 = x8",
                "specialize eisenstein_successor_terminal_sum_matches_last_column p",
                "specialize eisenstein_successor_terminal_sum_matches_last_column q",
                "specialize eisenstein_successor_terminal_sum_matches_last_column h",
                "specialize eisenstein_successor_terminal_sum_matches_last_column (S h)",
                "specialize eisenstein_successor_terminal_sum_matches_last_column bb",
                "specialize eisenstein_successor_terminal_sum_matches_last_column bc",
                "specialize eisenstein_successor_terminal_sum_matches_last_column x",
                "specialize eisenstein_successor_terminal_sum_matches_last_column x1",
                "specialize eisenstein_successor_terminal_sum_matches_last_column x2",
                "specialize eisenstein_successor_terminal_sum_matches_last_column x3",
                "specialize eisenstein_successor_terminal_sum_matches_last_column x9",
                "specialize eisenstein_successor_terminal_sum_matches_last_column x10",
                "specialize eisenstein_successor_terminal_sum_matches_last_column k",
                "specialize eisenstein_successor_terminal_sum_matches_last_column x5",
                "specialize eisenstein_successor_terminal_sum_matches_last_column x8",
                "apply eisenstein_successor_terminal_sum_matches_last_column",
                "refl", "exact hsplit_exists_witness_witness_witness_witness",
                "exact hlast_stored_witness_right_witness_witness_left",
                "exact hterminal_sum_witness",
                "exact hlast_stored_witness_right_witness_witness_right_left",
                "have htotal : M = x4 + x5",
                "rewrite hih at hsum_decompose_witness_witness_right_right",
                "rewrite <- hcount_eq at hsum_decompose_witness_witness_right_right",
                "rewrite <- hterminal_eq at hsum_decompose_witness_witness_right_right",
                "exact hsum_decompose_witness_witness_right_right",
                "trans x4 + x5", "exact htotal", "exact hsource_add",
            ),
            "Any genuine transposed-column count total equals the swapped semantic row total.",
        ),
        spec(
            "eisenstein_transposed_column_count_prefix_forget",
            "forall p q h k ab ac bb bc db dc. "
            f"({constructed_prefix}) -> ({forgotten_prefix})",
            (),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro db", "intro dc", "intro hprefix",
                "intro i", "intro hi",
                "have hstored : exists m. "
                f"(({beta_at('db', 'dc', 'i', 'm', tag='fubini_total_forget_stored_entry')}) /\\ "
                f"({eisenstein_transposed_column_count_witness('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'i', 'm', tag='fubini_total_forget_stored_witness')}))",
                "specialize hprefix i", "apply hprefix", "exact hi",
                "cases hstored", "cases hstored_witness",
                "cases hstored_witness_right",
                "cases hstored_witness_right_witness",
                "cases hstored_witness_right_witness_witness",
                "cases hstored_witness_right_witness_witness_witness",
                "cases hstored_witness_right_witness_witness_witness_left",
                "cases hstored_witness_right_witness_witness_witness_right",
                "exists x", "split",
                "exact hstored_witness_left",
                "exists x2", "exists x3", "split",
                "exact hstored_witness_right_witness_witness_witness_left_right",
                "exact hstored_witness_right_witness_witness_witness_right_left",
            ),
            "Forget complement-partition provenance while retaining every genuine transposed-column count.",
        ),
        spec(
            "eisenstein_constructed_column_total_equals_swapped_total",
            "forall p q h k ab ac bb bc db dc T M. "
            f"({second_outer}) -> ({constructed_prefix}) -> "
            f"({second_sum}) -> "
            f"({sum_relation('db', 'dc', 'h', 'M', tag='fubini_total_constructed_sum')}) -> M = T",
            (
                "eisenstein_transposed_column_count_prefix_forget",
                "eisenstein_fubini_universal",
            ),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro db", "intro dc", "intro T", "intro M",
                "intro houter", "intro hconstructed",
                "intro houtersum", "intro hcolumnsum",
                f"have hforgotten : {eisenstein_fubini_column_count_prefix('p', 'q', 'h', 'bb', 'bc', 'db', 'dc', 'h', 'k', tag='fubini_total_constructed_forgotten')}",
                "specialize eisenstein_transposed_column_count_prefix_forget p",
                "specialize eisenstein_transposed_column_count_prefix_forget q",
                "specialize eisenstein_transposed_column_count_prefix_forget h",
                "specialize eisenstein_transposed_column_count_prefix_forget k",
                "specialize eisenstein_transposed_column_count_prefix_forget ab",
                "specialize eisenstein_transposed_column_count_prefix_forget ac",
                "specialize eisenstein_transposed_column_count_prefix_forget bb",
                "specialize eisenstein_transposed_column_count_prefix_forget bc",
                "specialize eisenstein_transposed_column_count_prefix_forget db",
                "specialize eisenstein_transposed_column_count_prefix_forget dc",
                "apply eisenstein_transposed_column_count_prefix_forget",
                "exact hconstructed",
                "specialize eisenstein_fubini_universal h",
                "specialize eisenstein_fubini_universal p",
                "specialize eisenstein_fubini_universal q",
                "specialize eisenstein_fubini_universal k",
                "specialize eisenstein_fubini_universal bb",
                "specialize eisenstein_fubini_universal bc",
                "specialize eisenstein_fubini_universal db",
                "specialize eisenstein_fubini_universal dc",
                "specialize eisenstein_fubini_universal T",
                "specialize eisenstein_fubini_universal M",
                "apply eisenstein_fubini_universal",
                "exact houter", "exact hforgotten",
                "exact houtersum", "exact hcolumnsum",
            ),
            "The constructed complementary-column total is exactly the swapped semantic row total.",
        ),
        spec(
            "eisenstein_rectangle_floor_sum_identity",
            "forall p q h k ab ac bb bc N T. "
            f"({first_outer}) -> ({second_outer}) -> "
            f"({first_sum}) -> ({second_sum}) -> N + T = h * k",
            (
                "eisenstein_rectangle_plus_column_count_total",
                "eisenstein_constructed_column_total_equals_swapped_total",
            ),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro N", "intro T", "intro hfirst", "intro hsecond",
                "intro hfirstsum", "intro hsecondsum",
                "have hpartition : exists db dc M. "
                f"(({eisenstein_transposed_column_count_prefix('p', 'q', 'h', 'k', 'ab', 'ac', 'bb', 'bc', 'db', 'dc', 'h', tag='fubini_total_identity_partition_prefix')}) /\\ "
                f"(({sum_relation('db', 'dc', 'h', 'M', tag='fubini_total_identity_partition_sum')}) /\\ N + M = h * k))",
                "specialize eisenstein_rectangle_plus_column_count_total p",
                "specialize eisenstein_rectangle_plus_column_count_total q",
                "specialize eisenstein_rectangle_plus_column_count_total h",
                "specialize eisenstein_rectangle_plus_column_count_total k",
                "specialize eisenstein_rectangle_plus_column_count_total ab",
                "specialize eisenstein_rectangle_plus_column_count_total ac",
                "specialize eisenstein_rectangle_plus_column_count_total bb",
                "specialize eisenstein_rectangle_plus_column_count_total bc",
                "specialize eisenstein_rectangle_plus_column_count_total N",
                "apply eisenstein_rectangle_plus_column_count_total",
                "exact hfirst", "exact hsecond", "exact hfirstsum",
                "cases hpartition", "cases hpartition_witness",
                "cases hpartition_witness_witness",
                "cases hpartition_witness_witness_witness",
                "cases hpartition_witness_witness_witness_right",
                "have heq : x2 = T",
                "specialize eisenstein_constructed_column_total_equals_swapped_total p",
                "specialize eisenstein_constructed_column_total_equals_swapped_total q",
                "specialize eisenstein_constructed_column_total_equals_swapped_total h",
                "specialize eisenstein_constructed_column_total_equals_swapped_total k",
                "specialize eisenstein_constructed_column_total_equals_swapped_total ab",
                "specialize eisenstein_constructed_column_total_equals_swapped_total ac",
                "specialize eisenstein_constructed_column_total_equals_swapped_total bb",
                "specialize eisenstein_constructed_column_total_equals_swapped_total bc",
                "specialize eisenstein_constructed_column_total_equals_swapped_total x",
                "specialize eisenstein_constructed_column_total_equals_swapped_total x1",
                "specialize eisenstein_constructed_column_total_equals_swapped_total T",
                "specialize eisenstein_constructed_column_total_equals_swapped_total x2",
                "apply eisenstein_constructed_column_total_equals_swapped_total",
                "exact hsecond",
                "exact hpartition_witness_witness_witness_left",
                "exact hsecondsum",
                "exact hpartition_witness_witness_witness_right_left",
                "rewrite heq at hpartition_witness_witness_witness_right_right",
                "exact hpartition_witness_witness_witness_right_right",
            ),
            "The two semantic Eisenstein row totals add exactly to the rectangle area.",
        ),
    )


__all__ = [
    "eisenstein_fubini_column_count_prefix",
    "eisenstein_fubini_column_count_witness",
    "make_eisenstein_fubini_total_candidate_theorems",
]
