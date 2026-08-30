"""Beta-coded row indicators for the Eisenstein lattice argument.

Fix a row index ``i``.  For every column ``j < k`` this module records one
bit: ``1`` means ``p*(j+1) < q*(i+1)``, while ``0`` means the opposite strict
orientation.  The pointwise noncollision/orientation theorem makes that bit
choice constructive.  Ordinary induction and the checked beta-prefix append
theorem then encode the whole row, after which the existing ``BitCount`` fold
constructs its number of ones.

This deliberately uses one beta code per row.  It neither flattens the full
``h`` by ``k`` rectangle into a pairing-coded prefix nor nests beta codes in
another code.  A later outer layer may encode the resulting row counts, but
keeping the inner representation separate avoids choosing a pairing function
or a variable row stride before the required two-dimensional count laws have
been reviewed.

Every helper expands to the unchanged first-order language of Peano
arithmetic before parsing.  There is no predicate variable, list, matrix,
comparison, bit-count, or beta primitive in the kernel-facing statements,
and these candidates remain outside the public theorem registry.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_lattice_orientation_candidate import (
    exclusive_lattice_cell_orientation,
)
from .fermat_residue_product_candidate import prime
from .finite_fold_surface import all_bits, beta_at, bit_count


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
    names = tuple(f"eri_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Eisenstein-row binder captures an argument")
    return names


def _lt_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _cell_indicator_choice_term(
    prime_p: str,
    prime_q: str,
    row_index: str,
    column_index: str,
    bit: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    left = f"{prime_q} * S {row_index}"
    right = f"{prime_p} * S {column_index}"
    left_lt = _lt_term(
        left,
        right,
        tag=f"{tag}_left",
        variables=variables,
    )
    right_lt = _lt_term(
        right,
        left,
        tag=f"{tag}_right",
        variables=variables,
    )
    return (
        f"(({bit} = 0 /\\ (({left_lt}) /\\ ~({right_lt}))) \/ "
        f"({bit} = 1 /\\ (({right_lt}) /\\ ~({left_lt}))))"
    )


def eisenstein_cell_indicator_choice(
    prime_p: str,
    prime_q: str,
    row_index: str,
    column_index: str,
    bit: str,
    *,
    tag: str,
) -> str:
    """Expand the exact zero/one choice for one oriented lattice cell."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (row_index, "row index"),
            (column_index, "column index"),
            (bit, "indicator bit"),
        )
    )
    return _cell_indicator_choice_term(
        prime_p,
        prime_q,
        row_index,
        column_index,
        bit,
        tag=tag,
        variables=variables,
    )


def _row_indicator_choices_term(
    prime_p: str,
    prime_q: str,
    row_index: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    column, bit = _binders(tag, variables, ("column", "bit"))
    owned = variables + (column, bit)
    bound = _lt_term(
        column,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    choice = _cell_indicator_choice_term(
        prime_p,
        prime_q,
        row_index,
        column,
        bit,
        tag=f"{tag}_choice",
        variables=owned,
    )
    return f"forall {column}. ({bound}) -> exists {bit}. ({choice})"


def eisenstein_row_indicator_choices(
    prime_p: str,
    prime_q: str,
    row_index: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand the pointwise indicator choices for one bounded row."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (row_index, "row index"),
            (length, "row length"),
        )
    )
    return _row_indicator_choices_term(
        prime_p,
        prime_q,
        row_index,
        length,
        tag=tag,
        variables=variables,
    )


def _row_indicator_prefix_term(
    prime_p: str,
    prime_q: str,
    row_index: str,
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    column, bit = _binders(tag, variables, ("column", "bit"))
    owned = variables + (column, bit)
    bound = _lt_term(
        column,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    decoded = beta_at(
        code,
        scale,
        column,
        bit,
        tag=f"eri_{tag}_decoded",
    )
    choice = _cell_indicator_choice_term(
        prime_p,
        prime_q,
        row_index,
        column,
        bit,
        tag=f"{tag}_choice",
        variables=owned,
    )
    return (
        f"forall {column}. ({bound}) -> exists {bit}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def eisenstein_row_indicator_prefix(
    prime_p: str,
    prime_q: str,
    row_index: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a beta-coded row whose entries are exact orientation bits."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (row_index, "row index"),
            (code, "row code"),
            (scale, "row scale"),
            (length, "row length"),
        )
    )
    return _row_indicator_prefix_term(
        prime_p,
        prime_q,
        row_index,
        code,
        scale,
        length,
        tag=tag,
        variables=variables,
    )


def _row_indicator_successor_prefix(
    prime_p: str,
    prime_q: str,
    row_index: str,
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
            (row_index, "row index"),
            (code, "row code"),
            (scale, "row scale"),
            (predecessor, "row predecessor"),
        )
    )
    return _row_indicator_prefix_term(
        prime_p,
        prime_q,
        row_index,
        code,
        scale,
        f"S {predecessor}",
        tag=tag,
        variables=variables,
    )


def make_eisenstein_row_indicator_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the pointwise-choice, row-prefix, and row-count candidates."""

    prime_p = prime("p", tag="row_indicator_prime_p")
    prime_q = prime("q", tag="row_indicator_prime_q")
    i_bound = _lt_term(
        "i",
        "h",
        tag="row_indicator_i_bound",
        variables=("p", "q", "h", "k", "i", "j"),
    )
    j_bound = _lt_term(
        "j",
        "k",
        tag="row_indicator_j_bound",
        variables=("p", "q", "h", "k", "i", "j"),
    )
    cell_orientation = exclusive_lattice_cell_orientation(
        "p", "q", "i", "j", tag="row_indicator_point_orientation"
    )
    cell_choice = eisenstein_cell_indicator_choice(
        "p", "q", "i", "j", "bit", tag="row_indicator_point_result"
    )

    prefix_before = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "l", tag="row_indicator_extend_before"
    )
    last_choice = eisenstein_cell_indicator_choice(
        "p", "q", "i", "l", "bit", tag="row_indicator_extend_last"
    )
    prefix_after = _row_indicator_successor_prefix(
        "p", "q", "i", "z", "d", "l", tag="row_indicator_extend_after"
    )
    old_entry = beta_at(
        "rb", "rc", "j", "oldbit", tag="row_indicator_extend_old_entry"
    )

    choices_all = eisenstein_row_indicator_choices(
        "p", "q", "i", "l", tag="row_indicator_exists_all"
    )
    choices_previous = eisenstein_row_indicator_choices(
        "p", "q", "i", "l", tag="row_indicator_exists_previous_choices"
    )
    previous_prefix = (
        "exists rb rc. "
        f"({eisenstein_row_indicator_prefix('p', 'q', 'i', 'rb', 'rc', 'l', tag='row_indicator_exists_previous_prefix')})"
    )
    successor_prefix = (
        "exists rb rc. "
        f"({_row_indicator_successor_prefix('p', 'q', 'i', 'rb', 'rc', 'l', tag='row_indicator_exists_successor_prefix')})"
    )
    prefix_result = (
        "exists rb rc. "
        f"({eisenstein_row_indicator_prefix('p', 'q', 'i', 'rb', 'rc', 'l', tag='row_indicator_exists_result')})"
    )

    concrete_choices = eisenstein_row_indicator_choices(
        "p", "q", "i", "k", tag="row_indicator_concrete_choices"
    )
    concrete_prefix = (
        "exists rb rc. "
        f"({eisenstein_row_indicator_prefix('p', 'q', 'i', 'rb', 'rc', 'k', tag='row_indicator_concrete_prefix')})"
    )

    bits_prefix = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "l", tag="row_indicator_bits_prefix"
    )
    bits_entry = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "l", tag="row_indicator_bits_entry_source"
    )
    all_row_bits = all_bits("rb", "rc", "l", tag="row_indicator_all_bits")

    projection_prefix = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "l", tag="row_indicator_projection_prefix"
    )
    projection_entry = beta_at(
        "rb", "rc", "j", "bit", tag="row_indicator_projection_entry"
    )
    projection_bound = _lt_term(
        "j",
        "l",
        tag="row_indicator_projection_bound",
        variables=("p", "q", "i", "rb", "rc", "l", "j", "bit"),
    )
    projection_choice = eisenstein_cell_indicator_choice(
        "p", "q", "i", "j", "bit", tag="row_indicator_projection_choice"
    )

    counted_prefix = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "k", tag="row_indicator_counted_prefix"
    )
    count_relation = bit_count(
        "rb", "rc", "k", "n", tag="row_indicator_count_relation"
    )
    witness_bits = all_bits(
        "x", "x1", "k", tag="row_indicator_counted_witness_bits"
    )
    witness_count = bit_count(
        "x", "x1", "k", "n", tag="row_indicator_counted_witness_count"
    )
    counted_result = (
        "exists rb rc n. "
        f"(({counted_prefix}) /\\ ({count_relation}))"
    )

    common_row_prefix = (
        "forall p q h k i. p = 2 * h + 1 -> q = 2 * k + 1 -> "
        f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> ({i_bound}) -> "
    )

    return (
        spec(
            "distinct_odd_prime_half_cell_indicator_choice",
            "forall p q h k i j. p = 2 * h + 1 -> q = 2 * k + 1 -> "
            f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> "
            f"({i_bound}) -> ({j_bound}) -> exists bit. ({cell_choice})",
            ("distinct_odd_prime_half_cell_oriented",),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro i",
                "intro j",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hi",
                "intro hj",
                f"have horientation : {cell_orientation}",
                "specialize distinct_odd_prime_half_cell_oriented p",
                "specialize distinct_odd_prime_half_cell_oriented q",
                "specialize distinct_odd_prime_half_cell_oriented h",
                "specialize distinct_odd_prime_half_cell_oriented k",
                "specialize distinct_odd_prime_half_cell_oriented i",
                "specialize distinct_odd_prime_half_cell_oriented j",
                "apply distinct_odd_prime_half_cell_oriented",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "exact hj",
                "cases horientation",
                "exists 0",
                "left",
                "split",
                "refl",
                "exact horientation_left",
                "exists 1",
                "right",
                "split",
                "refl",
                "exact horientation_right",
            ),
            "Every bounded lattice cell has a constructive exact indicator bit.",
        ),
        spec(
            "eisenstein_row_indicator_prefix_extend",
            "forall p q i rb rc l. "
            f"({prefix_before}) -> (exists bit. ({last_choice})) -> "
            f"exists z d. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro p",
                "intro q",
                "intro i",
                "intro rb",
                "intro rc",
                "intro l",
                "intro hprefix",
                "intro hchoice",
                "cases hchoice",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend rb",
                "specialize beta_prefix_extend rc",
                "specialize beta_prefix_extend x",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x1",
                "exists x2",
                "intro j",
                "intro hj",
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
                "exact hchoice_witness",
                f"have hold : exists oldbit. (({old_entry}) /\\ "
                f"({eisenstein_cell_indicator_choice('p', 'q', 'i', 'j', 'oldbit', tag='row_indicator_extend_old_choice')}))",
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
            "Append one exact orientation bit while preserving the previous row prefix.",
        ),
        spec(
            "eisenstein_row_indicator_prefix_exists",
            f"forall p q i l. ({choices_all}) -> ({prefix_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "le_succ",
                "le_refl",
                "eisenstein_row_indicator_prefix_extend",
            ),
            (
                "intro p",
                "intro q",
                "intro i",
                "induction l",
                "intro hchoices",
                "exists 0",
                "exists 0",
                "intro j",
                "intro hj",
                "exfalso",
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
                f"have hprevious_choices : {choices_previous}",
                "intro j",
                "intro hj",
                "specialize hchoices j",
                "apply hchoices",
                "specialize le_succ (S j)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hj",
                f"have hprevious : {previous_prefix}",
                "apply IH",
                "exact hprevious_choices",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hlast : exists bit. ({eisenstein_cell_indicator_choice('p', 'q', 'i', 'l', 'bit', tag='row_indicator_exists_last_choice')})",
                "specialize hchoices l",
                "apply hchoices",
                "specialize le_refl (S l)",
                "exact le_refl",
                f"have hnext : {successor_prefix}",
                "specialize eisenstein_row_indicator_prefix_extend p",
                "specialize eisenstein_row_indicator_prefix_extend q",
                "specialize eisenstein_row_indicator_prefix_extend i",
                "specialize eisenstein_row_indicator_prefix_extend x",
                "specialize eisenstein_row_indicator_prefix_extend x1",
                "specialize eisenstein_row_indicator_prefix_extend l",
                "apply eisenstein_row_indicator_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hlast",
                "exact hnext",
            ),
            "Every finite family of exact cell choices has a beta-coded row prefix.",
        ),
        spec(
            "distinct_odd_prime_half_row_indicator_choices",
            f"{common_row_prefix}({concrete_choices})",
            ("distinct_odd_prime_half_cell_indicator_choice",),
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
                "intro j",
                "intro hj",
                "specialize distinct_odd_prime_half_cell_indicator_choice p",
                "specialize distinct_odd_prime_half_cell_indicator_choice q",
                "specialize distinct_odd_prime_half_cell_indicator_choice h",
                "specialize distinct_odd_prime_half_cell_indicator_choice k",
                "specialize distinct_odd_prime_half_cell_indicator_choice i",
                "specialize distinct_odd_prime_half_cell_indicator_choice j",
                "apply distinct_odd_prime_half_cell_indicator_choice",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "exact hj",
            ),
            "A fixed bounded row has a constructive exact bit choice in every column.",
        ),
        spec(
            "eisenstein_row_indicator_prefix_all_bits",
            "forall p q i rb rc l. "
            f"({bits_prefix}) -> ({all_row_bits})",
            (),
            (
                "intro p",
                "intro q",
                "intro i",
                "intro rb",
                "intro rc",
                "intro l",
                "intro hprefix",
                "intro j",
                "intro hj",
                f"have hentry : {bits_entry}",
                "exact hprefix",
                "specialize hentry j",
                "have hstored : exists bit. "
                f"(({beta_at('rb', 'rc', 'j', 'bit', tag='row_indicator_bits_stored')}) /\\ "
                f"({eisenstein_cell_indicator_choice('p', 'q', 'i', 'j', 'bit', tag='row_indicator_bits_choice')}))",
                "apply hentry",
                "exact hj",
                "cases hstored",
                "cases hstored_witness",
                "exists x",
                "split",
                "exact hstored_witness_left",
                "cases hstored_witness_right",
                "cases hstored_witness_right_left",
                "left",
                "exact hstored_witness_right_left_left",
                "cases hstored_witness_right_right",
                "right",
                "exact hstored_witness_right_right_left",
            ),
            "The beta-coded indicator projection contains only zero and one.",
        ),
        spec(
            "eisenstein_row_indicator_decoded_choice",
            "forall p q i rb rc l j bit. "
            f"({projection_prefix}) -> ({projection_bound}) -> "
            f"({projection_entry}) -> ({projection_choice})",
            ("beta_at_unique",),
            (
                "intro p",
                "intro q",
                "intro i",
                "intro rb",
                "intro rc",
                "intro l",
                "intro j",
                "intro bit",
                "intro hprefix",
                "intro hj",
                "intro hentry",
                "have hstored : exists stored. "
                f"(({beta_at('rb', 'rc', 'j', 'stored', tag='row_indicator_projection_stored')}) /\\ "
                f"({eisenstein_cell_indicator_choice('p', 'q', 'i', 'j', 'stored', tag='row_indicator_projection_stored_choice')}))",
                "specialize hprefix j",
                "apply hprefix",
                "exact hj",
                "cases hstored",
                "cases hstored_witness",
                "have heq : x = bit",
                "specialize beta_at_unique rb",
                "specialize beta_at_unique rc",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x",
                "specialize beta_at_unique bit",
                "apply beta_at_unique",
                "exact hstored_witness_left",
                "exact hentry",
                "rewrite heq at hstored_witness_right",
                "rewrite heq at hstored_witness_right",
                "exact hstored_witness_right",
            ),
            "Every decoded row bit recovers its exact strict-orientation meaning.",
        ),
        spec(
            "distinct_odd_prime_half_row_count_exists",
            f"{common_row_prefix}({counted_result})",
            (
                "distinct_odd_prime_half_row_indicator_choices",
                "eisenstein_row_indicator_prefix_exists",
                "eisenstein_row_indicator_prefix_all_bits",
                "bit_count_exists",
            ),
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
                f"have hchoices : {concrete_choices}",
                "specialize distinct_odd_prime_half_row_indicator_choices p",
                "specialize distinct_odd_prime_half_row_indicator_choices q",
                "specialize distinct_odd_prime_half_row_indicator_choices h",
                "specialize distinct_odd_prime_half_row_indicator_choices k",
                "specialize distinct_odd_prime_half_row_indicator_choices i",
                "apply distinct_odd_prime_half_row_indicator_choices",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                f"have hprefix_exists : {concrete_prefix}",
                "specialize eisenstein_row_indicator_prefix_exists p",
                "specialize eisenstein_row_indicator_prefix_exists q",
                "specialize eisenstein_row_indicator_prefix_exists i",
                "specialize eisenstein_row_indicator_prefix_exists k",
                "apply eisenstein_row_indicator_prefix_exists",
                "exact hchoices",
                "cases hprefix_exists",
                "cases hprefix_exists_witness",
                f"have hbits : {witness_bits}",
                "specialize eisenstein_row_indicator_prefix_all_bits p",
                "specialize eisenstein_row_indicator_prefix_all_bits q",
                "specialize eisenstein_row_indicator_prefix_all_bits i",
                "specialize eisenstein_row_indicator_prefix_all_bits x",
                "specialize eisenstein_row_indicator_prefix_all_bits x1",
                "specialize eisenstein_row_indicator_prefix_all_bits k",
                "apply eisenstein_row_indicator_prefix_all_bits",
                "exact hprefix_exists_witness_witness",
                f"have hcount : exists n. ({witness_count})",
                "specialize bit_count_exists x",
                "specialize bit_count_exists x1",
                "specialize bit_count_exists k",
                "apply bit_count_exists",
                "exact hbits",
                "cases hcount",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "exact hprefix_exists_witness_witness",
                "exact hcount_witness",
            ),
            "Every fixed half-rectangle row has an exact beta-coded indicator and BitCount witness.",
        ),
    )


__all__ = [
    "eisenstein_cell_indicator_choice",
    "eisenstein_row_indicator_choices",
    "eisenstein_row_indicator_prefix",
    "make_eisenstein_row_indicator_candidate_theorems",
]
