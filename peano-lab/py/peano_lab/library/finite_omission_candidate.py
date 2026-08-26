"""Constructive finite-omission candidates for the PairOrder campaign.

``BoundedInto(b,c,l,n)`` separates the beta prefix's domain length ``l``
from its codomain bound ``n``.  The main result is stronger than the usual
short-injection statement: every beta-coded prefix of length ``l < n`` omits
some value below ``n``, whether or not the prefix is injective or bounded.

The proof first performs a decidable bounded occurrence search.  If every
value below ``n`` occurs, it beta-codes a choice of preimage for each value.
Functionality of beta decoding makes that inverse-choice map injective.  Its
first ``S l`` entries then form an injection into ``l``; the already checked
square finite-pigeonhole theorem forces the impossible bound ``l < l``.

All relations expand immediately into unchanged first-order PA.  The specs
remain outside the public registry pending WMI discovery and admission.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at
from .finite_permutation_theorems import (
    bounded_successor_prefix,
    contains_prefix,
    injective_prefix,
    injective_successor_prefix,
    surjective_successor_prefix,
)


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
    avoid: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"fom_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated finite-omission binder captures an argument")
    return names


def _lt_term(
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, avoid, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _beta_at_term(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, avoid, ("beta_height", "beta_quotient"))
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value}))"
    )


def _bounded_into_term(
    code: str,
    scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, value = _binders(tag, avoid, ("index", "value"))
    nested_avoid = avoid + (index, value)
    index_bound = _lt_term(
        index,
        length,
        tag=f"{tag}_index_bound",
        avoid=nested_avoid,
    )
    entry = _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_entry",
        avoid=nested_avoid,
    )
    value_bound = _lt_term(
        value,
        bound,
        tag=f"{tag}_value_bound",
        avoid=nested_avoid,
    )
    return (
        f"forall {index}. ({index_bound}) -> exists {value}. "
        f"(({entry}) /\\ ({value_bound}))"
    )


def bounded_into(
    code: str,
    scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
) -> str:
    """Expand a beta prefix of domain ``length`` with values below ``bound``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (length, "domain length"),
            (bound, "codomain bound"),
        )
    )
    return _bounded_into_term(
        code,
        scale,
        length,
        bound,
        tag=tag,
        avoid=variables,
    )


def _covers_into_term(
    code: str,
    scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    value, index = _binders(tag, avoid, ("value", "index"))
    nested_avoid = avoid + (value, index)
    value_bound = _lt_term(
        value,
        bound,
        tag=f"{tag}_value_bound",
        avoid=nested_avoid,
    )
    index_bound = _lt_term(
        index,
        length,
        tag=f"{tag}_index_bound",
        avoid=nested_avoid,
    )
    entry = _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_entry",
        avoid=nested_avoid,
    )
    return (
        f"forall {value}. ({value_bound}) -> exists {index}. "
        f"(({index_bound}) /\\ ({entry}))"
    )


def covers_into(
    code: str,
    scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
) -> str:
    """Expand coverage of every value below a separate codomain bound."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (length, "domain length"),
            (bound, "codomain bound"),
        )
    )
    return _covers_into_term(
        code,
        scale,
        length,
        bound,
        tag=tag,
        avoid=variables,
    )


def _omits_into_term(
    code: str,
    scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    value, index = _binders(tag, avoid, ("value", "index"))
    nested_avoid = avoid + (value, index)
    value_bound = _lt_term(
        value,
        bound,
        tag=f"{tag}_value_bound",
        avoid=nested_avoid,
    )
    index_bound = _lt_term(
        index,
        length,
        tag=f"{tag}_index_bound",
        avoid=nested_avoid,
    )
    entry = _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_entry",
        avoid=nested_avoid,
    )
    contains = f"exists {index}. (({index_bound}) /\\ ({entry}))"
    return f"exists {value}. (({value_bound}) /\\ ~({contains}))"


def omits_into(
    code: str,
    scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
) -> str:
    """Expand existence of a missing value below ``bound``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (length, "domain length"),
            (bound, "codomain bound"),
        )
    )
    return _omits_into_term(
        code,
        scale,
        length,
        bound,
        tag=tag,
        avoid=variables,
    )


def _inverse_choice_prefix_term(
    source_code: str,
    source_scale: str,
    source_length: str,
    choice_code: str,
    choice_scale: str,
    choice_length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    value, index = _binders(tag, avoid, ("value", "index"))
    nested_avoid = avoid + (value, index)
    value_bound = _lt_term(
        value,
        choice_length,
        tag=f"{tag}_value_bound",
        avoid=nested_avoid,
    )
    choice_entry = _beta_at_term(
        choice_code,
        choice_scale,
        value,
        index,
        tag=f"{tag}_choice_entry",
        avoid=nested_avoid,
    )
    index_bound = _lt_term(
        index,
        source_length,
        tag=f"{tag}_index_bound",
        avoid=nested_avoid,
    )
    source_entry = _beta_at_term(
        source_code,
        source_scale,
        index,
        value,
        tag=f"{tag}_source_entry",
        avoid=nested_avoid,
    )
    return (
        f"forall {value}. ({value_bound}) -> exists {index}. "
        f"(({choice_entry}) /\\ (({index_bound}) /\\ ({source_entry})))"
    )


def inverse_choice_prefix(
    source_code: str,
    source_scale: str,
    source_length: str,
    choice_code: str,
    choice_scale: str,
    choice_length: str,
    *,
    tag: str,
) -> str:
    """Expand a beta-coded choice of source preimage for each target value."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (source_code, "source code"),
            (source_scale, "source scale"),
            (source_length, "source length"),
            (choice_code, "choice code"),
            (choice_scale, "choice scale"),
            (choice_length, "choice length"),
        )
    )
    return _inverse_choice_prefix_term(
        source_code,
        source_scale,
        source_length,
        choice_code,
        choice_scale,
        choice_length,
        tag=tag,
        avoid=variables,
    )


def inverse_choice_prefix_successor(
    source_code: str,
    source_scale: str,
    source_length: str,
    choice_code: str,
    choice_scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand inverse-choice data through the controlled length ``S k``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (source_code, "source code"),
            (source_scale, "source scale"),
            (source_length, "source length"),
            (choice_code, "choice code"),
            (choice_scale, "choice scale"),
            (predecessor, "choice predecessor"),
        )
    )
    return _inverse_choice_prefix_term(
        source_code,
        source_scale,
        source_length,
        choice_code,
        choice_scale,
        f"S {predecessor}",
        tag=tag,
        avoid=variables,
    )


def make_finite_omission_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered constructive finite-omission ladder."""

    search_cover = covers_into("b", "c", "l", "n", tag="search_cover")
    search_omit = omits_into("b", "c", "l", "n", tag="search_omit")
    search_previous_cover = covers_into(
        "b", "c", "l", "n", tag="search_previous_cover"
    )
    search_previous_omit = omits_into(
        "b", "c", "l", "n", tag="search_previous_omit"
    )
    search_successor_cover = _covers_into_term(
        "b",
        "c",
        "l",
        "S n",
        tag="search_successor_cover",
        avoid=("b", "c", "l", "n"),
    )
    search_top_contains = contains_prefix(
        "b", "c", "l", "n", tag="search_top_contains"
    )

    extend_contains = contains_prefix(
        "b", "c", "l", "k", tag="extend_contains"
    )
    extend_before = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "k", tag="extend_before"
    )
    extend_after = inverse_choice_prefix_successor(
        "b", "c", "l", "r", "s", "k", tag="extend_after"
    )
    extend_new_entry = _beta_at_term(
        "x1",
        "x2",
        "k",
        "x",
        tag="extend_new_entry",
        avoid=("b", "c", "l", "z", "d", "k", "x", "x1", "x2"),
    )
    extend_old_result = _inverse_choice_prefix_term(
        "b",
        "c",
        "l",
        "z",
        "d",
        "k",
        tag="extend_old_result",
        avoid=("b", "c", "l", "z", "d", "k"),
    )

    exists_cover = covers_into("b", "c", "l", "n", tag="exists_cover")
    exists_result = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="exists_result"
    )
    exists_successor_cover = _covers_into_term(
        "b",
        "c",
        "l",
        "S n",
        tag="exists_successor_cover",
        avoid=("b", "c", "l", "n"),
    )
    exists_previous_cover = covers_into(
        "b", "c", "l", "n", tag="exists_previous_cover"
    )
    exists_previous_choice = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="exists_previous_choice"
    )
    exists_successor_choice = inverse_choice_prefix_successor(
        "b", "c", "l", "z", "d", "n", tag="exists_successor_choice"
    )
    exists_top_contains = contains_prefix(
        "b", "c", "l", "n", tag="exists_top_contains"
    )

    bounded_choice = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="bounded_choice"
    )
    bounded_result = bounded_into(
        "z", "d", "n", "l", tag="bounded_result"
    )

    injective_choice = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="injective_choice"
    )
    injective_result = injective_prefix(
        "z", "d", "n", tag="injective_result"
    )
    injective_choice_left = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="injective_choice_left"
    )
    injective_choice_right = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="injective_choice_right"
    )

    impossible_cover = covers_into(
        "b", "c", "l", "n", tag="impossible_cover"
    )
    impossible_choice = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="impossible_choice"
    )
    impossible_bounded = bounded_into(
        "x", "x1", "n", "l", tag="impossible_bounded"
    )
    impossible_injective = injective_prefix(
        "x", "x1", "n", tag="impossible_injective"
    )
    impossible_small_bounded = bounded_successor_prefix(
        "x", "x1", "l", tag="impossible_small_bounded"
    )
    impossible_small_injective = injective_successor_prefix(
        "x", "x1", "l", tag="impossible_small_injective"
    )
    impossible_small_surjective = surjective_successor_prefix(
        "x", "x1", "l", tag="impossible_small_surjective"
    )
    impossible_last_entry = beta_at(
        "x", "x1", "i", "l", tag="impossible_last_entry"
    )
    impossible_stored_entry = beta_at(
        "x", "x1", "x2", "v", tag="impossible_stored_entry"
    )

    short_omit = omits_into("b", "c", "l", "n", tag="short_omit")
    short_cover = covers_into("b", "c", "l", "n", tag="short_cover")

    requested_bounded = bounded_into(
        "b", "c", "l", "n", tag="requested_bounded"
    )
    requested_injective = injective_prefix(
        "b", "c", "l", tag="requested_injective"
    )
    requested_omit = omits_into(
        "b", "c", "l", "n", tag="requested_omit"
    )

    return (
        spec(
            "finite_covers_into_or_omits",
            f"forall b c l n. ({search_cover}) \\/ ({search_omit})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "finite_contains_decidable",
                "finite_lt_succ_eq_or_lt",
                "le_succ",
                "le_refl",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "induction n",
                "left",
                "intro y",
                "intro hy",
                "exfalso",
                "cases hy",
                "have hsy : S y = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S y)",
                "apply add_eq_zero_right",
                "exact hy_witness",
                "specialize succ_ne_zero y",
                "apply succ_ne_zero",
                "exact hsy",
                f"have hprevious : ({search_previous_cover}) \\/ ({search_previous_omit})",
                "exact IH",
                "cases hprevious",
                "have htop : "
                f"({search_top_contains}) \\/ ~({search_top_contains})",
                "specialize finite_contains_decidable b",
                "specialize finite_contains_decidable c",
                "specialize finite_contains_decidable l",
                "specialize finite_contains_decidable n",
                "exact finite_contains_decidable",
                "cases htop",
                "left",
                f"have hsuccessor_cover : {search_successor_cover}",
                "intro y",
                "intro hy",
                "have hsplit : y = n \\/ exists h. h + S y = n",
                "specialize finite_lt_succ_eq_or_lt n",
                "specialize finite_lt_succ_eq_or_lt y",
                "apply finite_lt_succ_eq_or_lt",
                "exact hy",
                "cases hsplit",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact htop_left",
                "specialize hprevious_left y",
                "apply hprevious_left",
                "exact hsplit_right",
                "exact hsuccessor_cover",
                "right",
                "exists n",
                "split",
                "specialize le_refl (S n)",
                "exact le_refl",
                "exact htop_right",
                "right",
                "cases hprevious_right",
                "cases hprevious_right_witness",
                "exists x",
                "split",
                "specialize le_succ (S x)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hprevious_right_witness_left",
                "exact hprevious_right_witness_right",
            ),
            "Bounded occurrence search either covers the target interval or returns an explicit omission.",
        ),
        spec(
            "finite_inverse_choice_prefix_extend",
            f"forall b c l z d k. ({extend_contains}) -> ({extend_before}) -> "
            f"exists r s. ({extend_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro z",
                "intro d",
                "intro k",
                "intro hcontains",
                "intro hchoice",
                "cases hcontains",
                "cases hcontains_witness",
                "specialize beta_prefix_extend k",
                "specialize beta_prefix_extend z",
                "specialize beta_prefix_extend d",
                "specialize beta_prefix_extend x",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x1",
                "exists x2",
                "intro y",
                "intro hy",
                "have hsplit : y = k \\/ exists h. h + S y = k",
                "specialize finite_lt_succ_eq_or_lt k",
                "specialize finite_lt_succ_eq_or_lt y",
                "apply finite_lt_succ_eq_or_lt",
                "exact hy",
                "cases hsplit",
                "exists x",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                f"have hnew_entry : {extend_new_entry}",
                "exact beta_prefix_extend_witness_witness_left",
                "exact hnew_entry",
                "split",
                "exact hcontains_witness_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hcontains_witness_right",
                f"have hold : {extend_old_result}",
                "exact hchoice",
                "specialize hold y",
                "have hold_y : exists i. "
                "(((exists h. h + S i = S ((S y) * d)) /\\ "
                "exists q. z = q * S ((S y) * d) + i) /\\ "
                "((exists h. h + S i = l) /\\ "
                "((exists h. h + S y = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + y)))",
                "apply hold",
                "exact hsplit_right",
                "cases hold_y",
                "cases hold_y_witness",
                "exists x3",
                "split",
                "specialize beta_prefix_extend_witness_witness_right y",
                "specialize beta_prefix_extend_witness_witness_right x3",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_y_witness_left",
                "exact hold_y_witness_right",
            ),
            "Append one chosen source preimage to a beta-coded inverse-choice prefix.",
        ),
        spec(
            "finite_inverse_choice_prefix_exists",
            f"forall b c l n. ({exists_cover}) -> exists z d. ({exists_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "le_succ",
                "le_refl",
                "finite_inverse_choice_prefix_extend",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "induction n",
                "intro hcover",
                "exists 0",
                "exists 0",
                "intro y",
                "intro hy",
                "exfalso",
                "cases hy",
                "have hsy : S y = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S y)",
                "apply add_eq_zero_right",
                "exact hy_witness",
                "specialize succ_ne_zero y",
                "apply succ_ne_zero",
                "exact hsy",
                "intro hcover",
                f"have hcover_all : {exists_successor_cover}",
                "exact hcover",
                f"have hpast : {exists_previous_cover}",
                "intro y",
                "intro hy",
                "specialize hcover_all y",
                "apply hcover_all",
                "specialize le_succ (S y)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hy",
                f"have hprevious : exists z d. ({exists_previous_choice})",
                "apply IH",
                "exact hpast",
                "cases hprevious",
                "cases hprevious_witness",
                f"have htop : {exists_top_contains}",
                "specialize hcover n",
                "apply hcover",
                "specialize le_refl (S n)",
                "exact le_refl",
                f"have hnext : exists z d. ({exists_successor_choice})",
                "specialize finite_inverse_choice_prefix_extend b",
                "specialize finite_inverse_choice_prefix_extend c",
                "specialize finite_inverse_choice_prefix_extend l",
                "specialize finite_inverse_choice_prefix_extend x",
                "specialize finite_inverse_choice_prefix_extend x1",
                "specialize finite_inverse_choice_prefix_extend n",
                "apply finite_inverse_choice_prefix_extend",
                "exact htop",
                "exact hprevious_witness_witness",
                "exact hnext",
            ),
            "Full finite coverage admits a beta-coded choice of one preimage for each target value.",
        ),
        spec(
            "finite_inverse_choice_bounded_into",
            f"forall b c l z d n. ({bounded_choice}) -> ({bounded_result})",
            (),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro z",
                "intro d",
                "intro n",
                "intro hchoice",
                "intro y",
                "intro hy",
                "specialize hchoice y",
                "have hstored : exists i. "
                "(((exists h. h + S i = S ((S y) * d)) /\\ "
                "exists q. z = q * S ((S y) * d) + i) /\\ "
                "((exists h. h + S i = l) /\\ "
                "((exists h. h + S y = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + y)))",
                "apply hchoice",
                "exact hy",
                "cases hstored",
                "cases hstored_witness",
                "cases hstored_witness_right",
                "exists x",
                "split",
                "exact hstored_witness_left",
                "exact hstored_witness_right_left",
            ),
            "Every inverse-choice prefix is bounded into the source domain.",
        ),
        spec(
            "finite_inverse_choice_injective",
            f"forall b c l z d n. ({injective_choice}) -> ({injective_result})",
            ("beta_at_unique",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro z",
                "intro d",
                "intro n",
                "intro hchoice",
                "intro i",
                "intro j",
                "intro v",
                "intro hi",
                "intro hj",
                "intro hvi",
                "intro hvj",
                f"have hchoice_left : {injective_choice_left}",
                "exact hchoice",
                f"have hchoice_right : {injective_choice_right}",
                "exact hchoice",
                "specialize hchoice_left i",
                "have hleft : exists a. "
                "(((exists h. h + S a = S ((S i) * d)) /\\ "
                "exists q. z = q * S ((S i) * d) + a) /\\ "
                "((exists h. h + S a = l) /\\ "
                "((exists h. h + S i = S ((S a) * c)) /\\ "
                "exists q. b = q * S ((S a) * c) + i)))",
                "apply hchoice_left",
                "exact hi",
                "specialize hchoice_right j",
                "have hright : exists a. "
                "(((exists h. h + S a = S ((S j) * d)) /\\ "
                "exists q. z = q * S ((S j) * d) + a) /\\ "
                "((exists h. h + S a = l) /\\ "
                "((exists h. h + S j = S ((S a) * c)) /\\ "
                "exists q. b = q * S ((S a) * c) + j)))",
                "apply hchoice_right",
                "exact hj",
                "cases hleft",
                "cases hleft_witness",
                "cases hleft_witness_right",
                "cases hright",
                "cases hright_witness",
                "cases hright_witness_right",
                "have hvx : v = x",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique i",
                "specialize beta_at_unique v",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hvi",
                "exact hleft_witness_left",
                "have hvx1 : v = x1",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique j",
                "specialize beta_at_unique v",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hvj",
                "exact hright_witness_left",
                "have hxx : x = x1",
                "trans v",
                "symm",
                "exact hvx",
                "exact hvx1",
                "rewrite hxx at hleft_witness_right_right",
                "rewrite hxx at hleft_witness_right_right",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique i",
                "specialize beta_at_unique j",
                "apply beta_at_unique",
                "exact hleft_witness_right_right",
                "exact hright_witness_right_right",
            ),
            "A beta-coded choice of source preimages is injective by functionality of the source code.",
        ),
        spec(
            "finite_short_cover_impossible",
            f"forall b c l n. (exists h. h + S l = n) -> ~({impossible_cover})",
            (
                "finite_inverse_choice_prefix_exists",
                "finite_inverse_choice_bounded_into",
                "finite_inverse_choice_injective",
                "finite_bounded_injective_surjective",
                "le_trans",
                "le_succ",
                "le_refl",
                "beta_at_unique",
                "lt_irrefl_expanded",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hln",
                "intro hcover",
                f"have hchoice_exists : exists z d. ({impossible_choice})",
                "specialize finite_inverse_choice_prefix_exists b",
                "specialize finite_inverse_choice_prefix_exists c",
                "specialize finite_inverse_choice_prefix_exists l",
                "specialize finite_inverse_choice_prefix_exists n",
                "apply finite_inverse_choice_prefix_exists",
                "exact hcover",
                "cases hchoice_exists",
                "cases hchoice_exists_witness",
                f"have hbounded : {impossible_bounded}",
                "specialize finite_inverse_choice_bounded_into b",
                "specialize finite_inverse_choice_bounded_into c",
                "specialize finite_inverse_choice_bounded_into l",
                "specialize finite_inverse_choice_bounded_into x",
                "specialize finite_inverse_choice_bounded_into x1",
                "specialize finite_inverse_choice_bounded_into n",
                "apply finite_inverse_choice_bounded_into",
                "exact hchoice_exists_witness_witness",
                f"have hinjective : {impossible_injective}",
                "specialize finite_inverse_choice_injective b",
                "specialize finite_inverse_choice_injective c",
                "specialize finite_inverse_choice_injective l",
                "specialize finite_inverse_choice_injective x",
                "specialize finite_inverse_choice_injective x1",
                "specialize finite_inverse_choice_injective n",
                "apply finite_inverse_choice_injective",
                "exact hchoice_exists_witness_witness",
                f"have hbounded_all : {impossible_bounded}",
                "exact hbounded",
                f"have hbounded_small : {impossible_small_bounded}",
                "intro i",
                "intro hi",
                "have hin : exists h. h + S i = n",
                "specialize le_trans (S i)",
                "specialize le_trans (S l)",
                "specialize le_trans n",
                "apply le_trans",
                "exact hi",
                "exact hln",
                "specialize hbounded_all i",
                "have hentry : exists v. "
                "(((exists h. h + S v = S ((S i) * x1)) /\\ "
                "exists q. x = q * S ((S i) * x1) + v) /\\ "
                "exists h. h + S v = l)",
                "apply hbounded_all",
                "exact hin",
                "cases hentry",
                "cases hentry_witness",
                "exists x2",
                "split",
                "exact hentry_witness_left",
                "specialize le_succ (S x2)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hentry_witness_right",
                f"have hinjective_small : {impossible_small_injective}",
                "intro i",
                "intro j",
                "intro v",
                "intro hi",
                "intro hj",
                "intro hvi",
                "intro hvj",
                "specialize hinjective i",
                "specialize hinjective j",
                "specialize hinjective v",
                "apply hinjective",
                "specialize le_trans (S i)",
                "specialize le_trans (S l)",
                "specialize le_trans n",
                "apply le_trans",
                "exact hi",
                "exact hln",
                "specialize le_trans (S j)",
                "specialize le_trans (S l)",
                "specialize le_trans n",
                "apply le_trans",
                "exact hj",
                "exact hln",
                "exact hvi",
                "exact hvj",
                f"have hsurjective : {impossible_small_surjective}",
                "specialize finite_bounded_injective_surjective (S l)",
                "specialize finite_bounded_injective_surjective x",
                "specialize finite_bounded_injective_surjective x1",
                "apply finite_bounded_injective_surjective",
                "exact hbounded_small",
                "exact hinjective_small",
                "specialize hsurjective l",
                "have hoccurs : exists i. "
                "((exists h. h + S i = S l) /\\ "
                f"({impossible_last_entry}))",
                "apply hsurjective",
                "specialize le_refl (S l)",
                "exact le_refl",
                "cases hoccurs",
                "cases hoccurs_witness",
                "have hindex_n : exists h. h + S x2 = n",
                "specialize le_trans (S x2)",
                "specialize le_trans (S l)",
                "specialize le_trans n",
                "apply le_trans",
                "exact hoccurs_witness_left",
                "exact hln",
                "specialize hbounded x2",
                "have hstored : exists v. "
                f"(({impossible_stored_entry}) /\\ "
                "exists h. h + S v = l)",
                "apply hbounded",
                "exact hindex_n",
                "cases hstored",
                "cases hstored_witness",
                "have hlv : l = x3",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x3",
                "apply beta_at_unique",
                "exact hoccurs_witness_right",
                "exact hstored_witness_left",
                "rewrite <- hlv at hstored_witness_right",
                "specialize lt_irrefl_expanded l",
                "apply lt_irrefl_expanded",
                "exact hstored_witness_right",
            ),
            "A prefix shorter than the target interval cannot cover every target value.",
        ),
        spec(
            "finite_short_prefix_omits",
            f"forall b c l n. (exists h. h + S l = n) -> ({short_omit})",
            ("finite_covers_into_or_omits", "finite_short_cover_impossible"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hln",
                "have hsearch : "
                f"(({short_cover}) \\/ ({short_omit}))",
                "specialize finite_covers_into_or_omits b",
                "specialize finite_covers_into_or_omits c",
                "specialize finite_covers_into_or_omits l",
                "specialize finite_covers_into_or_omits n",
                "exact finite_covers_into_or_omits",
                "cases hsearch",
                "exfalso",
                "specialize finite_short_cover_impossible b",
                "specialize finite_short_cover_impossible c",
                "specialize finite_short_cover_impossible l",
                "specialize finite_short_cover_impossible n",
                "apply finite_short_cover_impossible",
                "exact hln",
                "exact hsearch_left",
                "exact hsearch_right",
            ),
            "Every beta-coded prefix shorter than n explicitly omits a value below n.",
        ),
        spec(
            "finite_bounded_into_injective_omits",
            f"forall b c l n. ({requested_bounded}) -> "
            f"({requested_injective}) -> (exists h. h + S l = n) -> "
            f"({requested_omit})",
            ("finite_short_prefix_omits",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hbounded",
                "intro hinjective",
                "intro hln",
                "specialize finite_short_prefix_omits b",
                "specialize finite_short_prefix_omits c",
                "specialize finite_short_prefix_omits l",
                "specialize finite_short_prefix_omits n",
                "apply finite_short_prefix_omits",
                "exact hln",
            ),
            "A bounded injective map from a shorter beta prefix omits a bounded codomain value; the stronger cardinal lemma makes the first two hypotheses redundant.",
        ),
    )


__all__ = [
    "bounded_into",
    "covers_into",
    "inverse_choice_prefix",
    "inverse_choice_prefix_successor",
    "make_finite_omission_candidate_theorems",
    "omits_into",
]
