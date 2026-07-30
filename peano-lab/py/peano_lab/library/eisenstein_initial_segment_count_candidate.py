"""Exact beta-coded initial-segment counts for Eisenstein rows.

For a threshold ``q`` and a prefix length ``k``, the decoded bit at the
zero-based position ``j`` is one exactly when ``S j <= q`` and is zero in
the complementary case ``q < S j``.  The two alternatives come directly
from constructive linear order.  When ``q <= k``, the prefix therefore has
exactly ``q`` ones.

Every displayed relation below expands to the unchanged first-order Peano
language before parsing.  These are dependency-curried authoring candidates:
they are deliberately not inserted into the public theorem registry and use
neither a classical principle nor a kernel extension.
"""

from __future__ import annotations

from typing import Any, Callable

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
    names = tuple(f"eis_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated initial-segment binder captures an argument")
    return names


def _le_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("le_gap",))
    return f"exists {gap}. {gap} + ({left}) = {right}"


def _lt_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("lt_gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _choice_term(
    threshold: str,
    index: str,
    bit: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    inside = _le_term(
        f"S {index}",
        threshold,
        tag=f"{tag}_inside",
        variables=variables,
    )
    outside = _lt_term(
        threshold,
        f"S {index}",
        tag=f"{tag}_outside",
        variables=variables,
    )
    return (
        f"(({bit} = 1 /\\ ({inside})) \\/ "
        f"({bit} = 0 /\\ ({outside})))"
    )


def eisenstein_initial_segment_choice(
    threshold: str,
    index: str,
    bit: str,
    *,
    tag: str,
) -> str:
    """Expand the exact one/zero choice at one zero-based position."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (threshold, "threshold"),
            (index, "index"),
            (bit, "bit"),
        )
    )
    return _choice_term(
        threshold,
        index,
        bit,
        tag=tag,
        variables=variables,
    )


def _prefix_term(
    threshold: str,
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index, bit = _binders(tag, variables, ("index", "bit"))
    owned = variables + (index, bit)
    bound = _lt_term(
        index,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    decoded = beta_at(code, scale, index, bit, tag=f"eis_{tag}_decoded")
    choice = _choice_term(
        threshold,
        index,
        bit,
        tag=f"{tag}_choice",
        variables=owned,
    )
    return (
        f"forall {index}. ({bound}) -> exists {bit}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def eisenstein_initial_segment_prefix(
    threshold: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a beta prefix with the exact threshold-bit semantics."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (threshold, "threshold"),
            (code, "code"),
            (scale, "scale"),
            (length, "length"),
        )
    )
    return _prefix_term(
        threshold,
        code,
        scale,
        length,
        tag=tag,
        variables=variables,
    )


def _successor_prefix(
    threshold: str,
    code: str,
    scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (threshold, "threshold"),
            (code, "code"),
            (scale, "scale"),
            (predecessor, "predecessor"),
        )
    )
    return _prefix_term(
        threshold,
        code,
        scale,
        f"S {predecessor}",
        tag=tag,
        variables=variables,
    )


def _all_one_prefix(
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (index,) = _binders(tag, variables, ("one_index",))
    owned = variables + (index,)
    bound = _lt_term(
        index,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    decoded = _beta_one(code, scale, index, tag=f"eis_{tag}_decoded")
    return f"forall {index}. ({bound}) -> ({decoded})"


def _beta_one(code: str, scale: str, index: str, *, tag: str) -> str:
    """Expand ``BetaAt(code,scale,index,1)`` through a private marker."""

    marker = "eisonevalue"
    expanded = beta_at(code, scale, index, marker, tag=tag)
    if expanded.count(marker) != 2:
        raise AssertionError("unexpected BetaAt value-marker multiplicity")
    return expanded.replace(marker, "1")


def make_eisenstein_initial_segment_count_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact initial-segment prefix and count ladder."""

    point_choice = eisenstein_initial_segment_choice(
        "q", "j", "bit", tag="initial_segment_point"
    )
    prefix_before = eisenstein_initial_segment_prefix(
        "q", "b", "c", "l", tag="initial_segment_extend_before"
    )
    last_choice = eisenstein_initial_segment_choice(
        "q", "l", "bit", tag="initial_segment_extend_last"
    )
    prefix_after = _successor_prefix(
        "q", "z", "d", "l", tag="initial_segment_extend_after"
    )
    old_entry = beta_at("b", "c", "j", "oldbit", tag="initial_segment_old")

    prefix_result = (
        "exists b c. "
        f"({eisenstein_initial_segment_prefix('q', 'b', 'c', 'k', tag='initial_segment_exists_result')})"
    )
    previous_prefix = (
        "exists b c. "
        f"({eisenstein_initial_segment_prefix('q', 'b', 'c', 'k', tag='initial_segment_exists_previous')})"
    )
    successor_prefix = (
        "exists b c. "
        f"({_successor_prefix('q', 'b', 'c', 'k', tag='initial_segment_exists_successor')})"
    )

    semantic_prefix = eisenstein_initial_segment_prefix(
        "q", "b", "c", "k", tag="initial_segment_semantic_source"
    )
    semantic_bound = _lt_term(
        "j",
        "k",
        tag="initial_segment_semantic_bound",
        variables=("q", "b", "c", "k", "j", "bit"),
    )
    semantic_entry = beta_at(
        "b", "c", "j", "bit", tag="initial_segment_semantic_entry"
    )
    semantic_choice = eisenstein_initial_segment_choice(
        "q", "j", "bit", tag="initial_segment_semantic_result"
    )

    bits_prefix = eisenstein_initial_segment_prefix(
        "q", "b", "c", "k", tag="initial_segment_bits_source"
    )
    all_prefix_bits = all_bits("b", "c", "k", tag="initial_segment_bits_result")

    all_one = _all_one_prefix(
        "b",
        "c",
        "k",
        tag="initial_segment_all_one_source",
        variables=("b", "c", "k", "n"),
    )
    all_one_previous = _all_one_prefix(
        "b",
        "c",
        "k",
        tag="initial_segment_all_one_previous",
        variables=("b", "c", "k", "n"),
    )
    all_one_count = bit_count(
        "b", "c", "k", "n", tag="initial_segment_all_one_count"
    )
    all_one_successor_count = bit_count(
        "b", "c", "sl", "n", tag="initial_segment_all_one_successor_count"
    )
    all_one_prefix_count = bit_count(
        "b", "c", "k", "r", tag="initial_segment_all_one_prefix_count"
    )
    all_one_last = beta_at(
        "b", "c", "k", "a", tag="initial_segment_all_one_last"
    )
    all_one_decomposition = (
        f"exists a r. ({all_one_last}) /\\ (({all_one_prefix_count}) /\\ "
        "((a = 0 \\/ a = 1) /\\ n = r + a))"
    )

    counted_prefix = eisenstein_initial_segment_prefix(
        "q", "b", "c", "k", tag="initial_segment_exact_source"
    )
    counted = bit_count(
        "b", "c", "k", "n", tag="initial_segment_exact_count"
    )
    threshold_bound = _le_term(
        "q",
        "k",
        tag="initial_segment_exact_threshold",
        variables=("q", "b", "c", "k", "n"),
    )
    functional_previous = eisenstein_initial_segment_prefix(
        "q", "b", "c", "k", tag="initial_segment_functional_previous"
    )
    functional_successor = _prefix_term(
        "q",
        "b",
        "c",
        "S k",
        tag="initial_segment_functional_successor",
        variables=("q", "b", "c", "k", "n"),
    )
    functional_all_one = _all_one_prefix(
        "b",
        "c",
        "S k",
        tag="initial_segment_functional_all_one",
        variables=("q", "b", "c", "k", "n"),
    )
    functional_last = beta_at(
        "b", "c", "k", "a", tag="initial_segment_functional_last"
    )
    functional_prefix_count = bit_count(
        "b", "c", "k", "r", tag="initial_segment_functional_prefix_count"
    )
    functional_decomposition = (
        f"exists a r. ({functional_last}) /\\ "
        f"(({functional_prefix_count}) /\\ "
        "((a = 0 \\/ a = 1) /\\ n = r + a))"
    )
    functional_last_choice = eisenstein_initial_segment_choice(
        "q", "k", "x", tag="initial_segment_functional_last_choice"
    )

    exact_prefix = eisenstein_initial_segment_prefix(
        "q", "b", "c", "k", tag="initial_segment_count_result_prefix"
    )
    exact_bound = _le_term(
        "q",
        "k",
        tag="initial_segment_count_result_bound",
        variables=("q", "b", "c", "k"),
    )
    exact_count = bit_count(
        "b", "c", "k", "q", tag="initial_segment_count_result"
    )

    return (
        spec(
            "eisenstein_initial_segment_indicator_choice",
            f"forall q j. exists bit. ({point_choice})",
            ("le_or_lt",),
            (
                "intro q",
                "intro j",
                "specialize le_or_lt (S j)",
                "specialize le_or_lt q",
                "cases le_or_lt",
                "exists 1",
                "left",
                "split",
                "refl",
                "exact le_or_lt_left",
                "exists 0",
                "right",
                "split",
                "refl",
                "exact le_or_lt_right",
            ),
            "Every position has a constructive exact threshold-indicator bit.",
        ),
        spec(
            "eisenstein_initial_segment_prefix_extend",
            "forall q b c l. "
            f"({prefix_before}) -> (exists bit. ({last_choice})) -> "
            f"exists z d. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro q",
                "intro b",
                "intro c",
                "intro l",
                "intro hprefix",
                "intro hchoice",
                "cases hchoice",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
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
                "exact hchoice_witness",
                f"have hold : exists oldbit. (({old_entry}) /\\ "
                f"({eisenstein_initial_segment_choice('q', 'j', 'oldbit', tag='initial_segment_extend_old_choice')}))",
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
            "Append one exact threshold bit while preserving the old prefix.",
        ),
        spec(
            "eisenstein_initial_segment_prefix_exists",
            f"forall q k. ({prefix_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "le_succ",
                "le_refl",
                "eisenstein_initial_segment_indicator_choice",
                "eisenstein_initial_segment_prefix_extend",
            ),
            (
                "intro q",
                "induction k",
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
                f"have hprevious : {previous_prefix}",
                "exact IH",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hlast : exists bit. ({eisenstein_initial_segment_choice('q', 'k', 'bit', tag='initial_segment_exists_last')})",
                "specialize eisenstein_initial_segment_indicator_choice q",
                "specialize eisenstein_initial_segment_indicator_choice k",
                "exact eisenstein_initial_segment_indicator_choice",
                f"have hnext : {successor_prefix}",
                "specialize eisenstein_initial_segment_prefix_extend q",
                "specialize eisenstein_initial_segment_prefix_extend x",
                "specialize eisenstein_initial_segment_prefix_extend x1",
                "specialize eisenstein_initial_segment_prefix_extend k",
                "apply eisenstein_initial_segment_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hlast",
                "exact hnext",
            ),
            "Every threshold and finite length has an exact beta-coded indicator.",
        ),
        spec(
            "eisenstein_initial_segment_prefix_all_bits",
            "forall q b c k. "
            f"({bits_prefix}) -> ({all_prefix_bits})",
            (),
            (
                "intro q",
                "intro b",
                "intro c",
                "intro k",
                "intro hprefix",
                "intro j",
                "intro hj",
                "specialize hprefix j",
                "have hstored : exists bit. "
                f"(({beta_at('b', 'c', 'j', 'bit', tag='initial_segment_bits_stored')}) /\\ "
                f"({eisenstein_initial_segment_choice('q', 'j', 'bit', tag='initial_segment_bits_choice')}))",
                "apply hprefix",
                "exact hj",
                "cases hstored",
                "cases hstored_witness",
                "exists x",
                "split",
                "exact hstored_witness_left",
                "cases hstored_witness_right",
                "cases hstored_witness_right_left",
                "right",
                "exact hstored_witness_right_left_left",
                "cases hstored_witness_right_right",
                "left",
                "exact hstored_witness_right_right_left",
            ),
            "Every exact threshold prefix is an AllBits prefix.",
        ),
        spec(
            "eisenstein_initial_segment_decoded_choice",
            "forall q b c k j bit. "
            f"({semantic_prefix}) -> ({semantic_bound}) -> "
            f"({semantic_entry}) -> ({semantic_choice})",
            ("beta_at_unique",),
            (
                "intro q",
                "intro b",
                "intro c",
                "intro k",
                "intro j",
                "intro bit",
                "intro hprefix",
                "intro hj",
                "intro hentry",
                "specialize hprefix j",
                "have hstored : exists stored. "
                f"(({beta_at('b', 'c', 'j', 'stored', tag='initial_segment_semantic_stored')}) /\\ "
                f"({eisenstein_initial_segment_choice('q', 'j', 'stored', tag='initial_segment_semantic_stored_choice')}))",
                "apply hprefix",
                "exact hj",
                "cases hstored",
                "cases hstored_witness",
                "have heq : x = bit",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
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
            "Every decoded bit recovers its exact threshold semantics.",
        ),
        spec(
            "beta_all_one_bit_count_exact",
            f"forall b c k n. ({all_one}) -> ({all_one_count}) -> n = k",
            (
                "bit_count_zero",
                "bit_count_succ_decompose",
                "all_bits_prefix_succ",
                "beta_at_unique",
                "le_succ",
                "le_refl",
            ),
            (
                "intro b",
                "intro c",
                "induction k",
                "intro n",
                "intro hone",
                "intro hcount",
                "specialize bit_count_zero b",
                "specialize bit_count_zero c",
                "specialize bit_count_zero 0",
                "specialize bit_count_zero n",
                "apply bit_count_zero",
                "refl",
                "exact hcount",
                "intro n",
                "intro hone",
                "intro hcount",
                f"have hdecomp : {all_one_decomposition}",
                "specialize bit_count_succ_decompose b",
                "specialize bit_count_succ_decompose c",
                "specialize bit_count_succ_decompose k",
                "specialize bit_count_succ_decompose (S k)",
                "specialize bit_count_succ_decompose n",
                "apply bit_count_succ_decompose",
                "refl",
                "exact hcount",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "cases hdecomp_witness_witness_right",
                "cases hdecomp_witness_witness_right_right",
                f"have hone_previous : {all_one_previous}",
                "intro j",
                "intro hj",
                "specialize hone j",
                "apply hone",
                "specialize le_succ (S j)",
                "specialize le_succ k",
                "apply le_succ",
                "exact hj",
                "have hr : x1 = k",
                "specialize IH x1",
                "apply IH",
                "exact hone_previous",
                "exact hdecomp_witness_witness_right_left",
                f"have hlast_one : {_beta_one('b', 'c', 'k', tag='initial_segment_all_one_terminal')}",
                "specialize hone k",
                "apply hone",
                "specialize le_refl (S k)",
                "exact le_refl",
                "have ha : x = 1",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique k",
                "specialize beta_at_unique x",
                "specialize beta_at_unique 1",
                "apply beta_at_unique",
                "exact hdecomp_witness_witness_left",
                "exact hlast_one",
                "rewrite hdecomp_witness_witness_right_right_right",
                "rewrite hr",
                "rewrite ha",
                "simp",
            ),
            "A length-k beta prefix consisting only of ones has BitCount k.",
        ),
        spec(
            "eisenstein_initial_segment_bit_count_functional",
            "forall q b c k n. "
            f"({counted_prefix}) -> ({threshold_bound}) -> ({counted}) -> n = q",
            (
                "le_zero",
                "le_eq_or_lt",
                "le_of_succ_le_succ",
                "le_succ",
                "le_refl",
                "lt_not_le",
                "bit_count_zero",
                "bit_count_succ_decompose",
                "eisenstein_initial_segment_decoded_choice",
                "beta_all_one_bit_count_exact",
            ),
            (
                "intro q",
                "intro b",
                "intro c",
                "induction k",
                "intro n",
                "intro hprefix",
                "intro hqk",
                "intro hcount",
                "have hq0 : q = 0",
                "specialize le_zero q",
                "apply le_zero",
                "exact hqk",
                "have hn0 : n = 0",
                "specialize bit_count_zero b",
                "specialize bit_count_zero c",
                "specialize bit_count_zero 0",
                "specialize bit_count_zero n",
                "apply bit_count_zero",
                "refl",
                "exact hcount",
                "trans 0",
                "exact hn0",
                "symm",
                "exact hq0",
                "intro n",
                "intro hprefix",
                "intro hqk",
                "intro hcount",
                "have hsplit : q = S k \/ exists gap. gap + S q = S k",
                "specialize le_eq_or_lt q",
                "specialize le_eq_or_lt (S k)",
                "apply le_eq_or_lt",
                "exact hqk",
                "cases hsplit",
                f"have hallone : {functional_all_one}",
                "intro j",
                "intro hj",
                f"have hstored : exists bit. (({beta_at('b', 'c', 'j', 'bit', tag='initial_segment_functional_stored')}) /\\ ({eisenstein_initial_segment_choice('q', 'j', 'bit', tag='initial_segment_functional_stored_choice')}))",
                "specialize hprefix j",
                "apply hprefix",
                "exact hj",
                "cases hstored",
                "cases hstored_witness",
                "cases hstored_witness_right",
                "cases hstored_witness_right_left",
                "have hbit_one : x = 1",
                "exact hstored_witness_right_left_left",
                "rewrite hbit_one at hstored_witness_left",
                "rewrite hbit_one at hstored_witness_left",
                "exact hstored_witness_left",
                "cases hstored_witness_right_right",
                "exfalso",
                "rewrite hsplit_left at hstored_witness_right_right_right",
                "specialize lt_not_le (S k)",
                "specialize lt_not_le (S j)",
                "apply lt_not_le",
                "exact hstored_witness_right_right_right",
                "exact hj",
                "have hn : n = S k",
                "specialize beta_all_one_bit_count_exact b",
                "specialize beta_all_one_bit_count_exact c",
                "specialize beta_all_one_bit_count_exact (S k)",
                "specialize beta_all_one_bit_count_exact n",
                "apply beta_all_one_bit_count_exact",
                "exact hallone",
                "exact hcount",
                "trans S k",
                "exact hn",
                "symm",
                "exact hsplit_left",
                "have hqk_previous : exists gap. gap + q = k",
                "specialize le_of_succ_le_succ q",
                "specialize le_of_succ_le_succ k",
                "apply le_of_succ_le_succ",
                "exact hsplit_right",
                f"have hprevious : {functional_previous}",
                "intro j",
                "intro hj",
                "specialize hprefix j",
                "apply hprefix",
                "specialize le_succ (S j)",
                "specialize le_succ k",
                "apply le_succ",
                "exact hj",
                f"have hdecomp : {functional_decomposition}",
                "specialize bit_count_succ_decompose b",
                "specialize bit_count_succ_decompose c",
                "specialize bit_count_succ_decompose k",
                "specialize bit_count_succ_decompose (S k)",
                "specialize bit_count_succ_decompose n",
                "apply bit_count_succ_decompose",
                "refl",
                "exact hcount",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "cases hdecomp_witness_witness_right",
                "cases hdecomp_witness_witness_right_right",
                f"have hlast_choice : {functional_last_choice}",
                "specialize eisenstein_initial_segment_decoded_choice q",
                "specialize eisenstein_initial_segment_decoded_choice b",
                "specialize eisenstein_initial_segment_decoded_choice c",
                "specialize eisenstein_initial_segment_decoded_choice (S k)",
                "specialize eisenstein_initial_segment_decoded_choice k",
                "specialize eisenstein_initial_segment_decoded_choice x",
                "apply eisenstein_initial_segment_decoded_choice",
                "exact hprefix",
                "specialize le_refl (S k)",
                "exact le_refl",
                "exact hdecomp_witness_witness_left",
                "cases hlast_choice",
                "cases hlast_choice_left",
                "exfalso",
                "specialize lt_not_le q",
                "specialize lt_not_le (S k)",
                "apply lt_not_le",
                "exact hsplit_right",
                "exact hlast_choice_left_right",
                "cases hlast_choice_right",
                "have hrq : x1 = q",
                "specialize IH x1",
                "apply IH",
                "exact hprevious",
                "exact hqk_previous",
                "exact hdecomp_witness_witness_right_left",
                "rewrite hdecomp_witness_witness_right_right_right",
                "rewrite hrq",
                "rewrite hlast_choice_right_left",
                "apply PA3",
            ),
            "The BitCount of a bounded exact initial segment is its threshold.",
        ),
        spec(
            "eisenstein_initial_segment_bit_count_exact",
            "forall q b c k. "
            f"({exact_prefix}) -> ({exact_bound}) -> ({exact_count})",
            (
                "eisenstein_initial_segment_prefix_all_bits",
                "bit_count_exists",
                "eisenstein_initial_segment_bit_count_functional",
            ),
            (
                "intro q",
                "intro b",
                "intro c",
                "intro k",
                "intro hprefix",
                "intro hqk",
                "have hallbits : " + all_bits("b", "c", "k", tag="initial_segment_exact_all_bits"),
                "specialize eisenstein_initial_segment_prefix_all_bits q",
                "specialize eisenstein_initial_segment_prefix_all_bits b",
                "specialize eisenstein_initial_segment_prefix_all_bits c",
                "specialize eisenstein_initial_segment_prefix_all_bits k",
                "apply eisenstein_initial_segment_prefix_all_bits",
                "exact hprefix",
                "have hcount : exists n. " + bit_count("b", "c", "k", "n", tag="initial_segment_exact_exists"),
                "specialize bit_count_exists b",
                "specialize bit_count_exists c",
                "specialize bit_count_exists k",
                "apply bit_count_exists",
                "exact hallbits",
                "cases hcount",
                "have hnq : x = q",
                "specialize eisenstein_initial_segment_bit_count_functional q",
                "specialize eisenstein_initial_segment_bit_count_functional b",
                "specialize eisenstein_initial_segment_bit_count_functional c",
                "specialize eisenstein_initial_segment_bit_count_functional k",
                "specialize eisenstein_initial_segment_bit_count_functional x",
                "apply eisenstein_initial_segment_bit_count_functional",
                "exact hprefix",
                "exact hqk",
                "exact hcount_witness",
                "rewrite hnq at hcount_witness",
                "rewrite hnq at hcount_witness",
                "exact hcount_witness",
            ),
            "A bounded exact initial-segment prefix has native BitCount q.",
        ),
    )


__all__ = [
    "eisenstein_initial_segment_choice",
    "eisenstein_initial_segment_prefix",
    "make_eisenstein_initial_segment_count_candidate_theorems",
]
