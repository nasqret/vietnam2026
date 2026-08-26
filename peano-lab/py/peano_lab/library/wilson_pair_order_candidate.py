"""Constructive PairOrder candidates for the native Wilson campaign.

The eventual Wilson proof needs a beta-coded enumeration in which every
nonendpoint inverse orbit occupies two adjacent positions.  This isolated
module deliberately starts one layer lower.  It supplies:

* an exact two-entry beta append trace;
* reflection for every entry of the extended prefix;
* a finite-omission chooser that cannot return either endpoint;
* extraction of the chosen inverse orbit from the full inverse code;
* preservation of inverse-orbit closure across the adjacent append; and
* preservation of decoded-prefix injectivity across a fresh distinct append;
* one combined choose-and-append step.

The combined step is a genuine constructive extension theorem, but it is not
yet the final PairOrder induction.  Injectivity preservation is proved as a
separate rung and still must be threaded through the combined induction; the
universal ``k+k, S(k+k)`` adjacency view required by ``adjacent_unit_pairs``
also remains separate.  Those boundaries are recorded in
``research/arithmetic-library/pair-order-encoding.md``.

All readable relations below are hygienic authoring abbreviations.  They
expand immediately to the unchanged first-order PA language.  The factory is
not registered: its dependencies include body-validated candidate theorems,
not admitted closed certificates.
"""

from __future__ import annotations

from typing import Any, Callable

from .wilson_inverse_orbit_candidate import nonendpoint
from .wilson_inverse_prefix_candidate import inverse_index, inverse_prefix, prime


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


def _identifier_or_zero(value: str, label: str) -> str:
    if value == "0":
        return value
    return _identifier(value, label)


def _binders(
    tag: str,
    avoid: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"wpo_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated pair-order binder captures an argument")
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


def _contains_term(
    code: str,
    scale: str,
    length: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (index,) = _binders(tag, avoid, ("index",))
    nested_avoid = avoid + (index,)
    bound = _lt_term(
        index,
        length,
        tag=f"{tag}_bound",
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
    return f"exists {index}. (({bound}) /\\ ({entry}))"


def _omits_value_term(
    code: str,
    scale: str,
    length: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    contains = _contains_term(
        code,
        scale,
        length,
        value,
        tag=f"{tag}_contains",
        avoid=avoid,
    )
    return f"~({contains})"


def _omits_some_term(
    code: str,
    scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (value,) = _binders(tag, avoid, ("value",))
    nested_avoid = avoid + (value,)
    value_bound = _lt_term(
        value,
        bound,
        tag=f"{tag}_value_bound",
        avoid=nested_avoid,
    )
    omitted = _omits_value_term(
        code,
        scale,
        length,
        value,
        tag=f"{tag}_omitted",
        avoid=nested_avoid,
    )
    return f"exists {value}. (({value_bound}) /\\ ({omitted}))"


def omits_value(
    code: str,
    scale: str,
    length: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand that ``value`` does not occur in the decoded finite prefix."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "beta code"),
            (scale, "beta scale"),
            (length, "prefix length"),
            (value, "omitted value"),
        )
    )
    return _omits_value_term(
        code,
        scale,
        length,
        value,
        tag=tag,
        avoid=variables,
    )


def _append_two_trace_term(
    old_code: str,
    old_scale: str,
    new_code: str,
    new_scale: str,
    length: str,
    first: str,
    second: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, value = _binders(tag, avoid, ("old_index", "old_value"))
    nested_avoid = avoid + (index, value)
    first_entry = _beta_at_term(
        new_code,
        new_scale,
        length,
        first,
        tag=f"{tag}_first",
        avoid=nested_avoid,
    )
    second_entry = _beta_at_term(
        new_code,
        new_scale,
        f"S ({length})",
        second,
        tag=f"{tag}_second",
        avoid=nested_avoid,
    )
    old_bound = _lt_term(
        index,
        length,
        tag=f"{tag}_old_bound",
        avoid=nested_avoid,
    )
    old_entry = _beta_at_term(
        old_code,
        old_scale,
        index,
        value,
        tag=f"{tag}_old_entry",
        avoid=nested_avoid,
    )
    new_entry = _beta_at_term(
        new_code,
        new_scale,
        index,
        value,
        tag=f"{tag}_new_entry",
        avoid=nested_avoid,
    )
    preservation = (
        f"forall {index} {value}. ({old_bound}) -> "
        f"({old_entry}) -> ({new_entry})"
    )
    return f"(({first_entry}) /\\ (({second_entry}) /\\ ({preservation})))"


def append_two_trace(
    old_code: str,
    old_scale: str,
    new_code: str,
    new_scale: str,
    length: str,
    first: str,
    second: str,
    *,
    tag: str,
) -> str:
    """Expand a two-entry append and exact preservation of the old prefix."""

    variables = (
        _identifier(old_code, "old beta code"),
        _identifier(old_scale, "old beta scale"),
        _identifier(new_code, "new beta code"),
        _identifier(new_scale, "new beta scale"),
        _identifier(length, "old prefix length"),
        _identifier_or_zero(first, "first appended value"),
        _identifier_or_zero(second, "second appended value"),
    )
    return _append_two_trace_term(
        *variables,
        tag=tag,
        avoid=variables,
    )


def _orbit_closed_prefix_term(
    inverse_code: str,
    inverse_scale: str,
    order_code: str,
    order_scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    position, source, mate, mate_position = _binders(
        tag,
        avoid,
        ("position", "source", "mate", "mate_position"),
    )
    nested_avoid = avoid + (position, source, mate, mate_position)
    position_bound = _lt_term(
        position,
        length,
        tag=f"{tag}_position_bound",
        avoid=nested_avoid,
    )
    source_entry = _beta_at_term(
        order_code,
        order_scale,
        position,
        source,
        tag=f"{tag}_source_entry",
        avoid=nested_avoid,
    )
    inverse_entry = _beta_at_term(
        inverse_code,
        inverse_scale,
        source,
        mate,
        tag=f"{tag}_inverse_entry",
        avoid=nested_avoid,
    )
    mate_bound = _lt_term(
        mate_position,
        length,
        tag=f"{tag}_mate_bound",
        avoid=nested_avoid,
    )
    mate_entry = _beta_at_term(
        order_code,
        order_scale,
        mate_position,
        mate,
        tag=f"{tag}_mate_entry",
        avoid=nested_avoid,
    )
    return (
        f"forall {position} {source} {mate}. ({position_bound}) -> "
        f"({source_entry}) -> ({inverse_entry}) -> exists {mate_position}. "
        f"(({mate_bound}) /\\ ({mate_entry}))"
    )


def orbit_closed_prefix(
    inverse_code: str,
    inverse_scale: str,
    order_code: str,
    order_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand closure of a used-value prefix under the decoded inverse map."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (inverse_code, "inverse beta code"),
            (inverse_scale, "inverse beta scale"),
            (order_code, "order beta code"),
            (order_scale, "order beta scale"),
            (length, "order prefix length"),
        )
    )
    return _orbit_closed_prefix_term(
        *variables,
        tag=tag,
        avoid=variables,
    )


def _nonendpoint_prefix_term(
    order_code: str,
    order_scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    position, value = _binders(tag, avoid, ("position", "value"))
    nested_avoid = avoid + (position, value)
    position_bound = _lt_term(
        position,
        length,
        tag=f"{tag}_position_bound",
        avoid=nested_avoid,
    )
    entry = _beta_at_term(
        order_code,
        order_scale,
        position,
        value,
        tag=f"{tag}_entry",
        avoid=nested_avoid,
    )
    endpoint_condition = f"(~({value} = 0) /\\ ~((S {value}) = {bound}))"
    return (
        f"forall {position} {value}. ({position_bound}) -> "
        f"({entry}) -> {endpoint_condition}"
    )


def nonendpoint_prefix(
    order_code: str,
    order_scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
) -> str:
    """Expand that every decoded used value is a nonendpoint index."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (order_code, "order beta code"),
            (order_scale, "order beta scale"),
            (length, "order prefix length"),
            (bound, "inverse interval bound"),
        )
    )
    return _nonendpoint_prefix_term(
        *variables,
        tag=tag,
        avoid=variables,
    )


def _injective_prefix_term(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    left_index, right_index, value = _binders(
        tag,
        avoid,
        ("injective_left", "injective_right", "injective_value"),
    )
    nested_avoid = avoid + (left_index, right_index, value)
    left_bound = _lt_term(
        left_index,
        length,
        tag=f"{tag}_left_bound",
        avoid=nested_avoid,
    )
    right_bound = _lt_term(
        right_index,
        length,
        tag=f"{tag}_right_bound",
        avoid=nested_avoid,
    )
    left_entry = _beta_at_term(
        code,
        scale,
        left_index,
        value,
        tag=f"{tag}_left_entry",
        avoid=nested_avoid,
    )
    right_entry = _beta_at_term(
        code,
        scale,
        right_index,
        value,
        tag=f"{tag}_right_entry",
        avoid=nested_avoid,
    )
    return (
        f"forall {left_index} {right_index} {value}. "
        f"({left_bound}) -> ({right_bound}) -> "
        f"({left_entry}) -> ({right_entry}) -> "
        f"{left_index} = {right_index}"
    )


def _append_two_reflection_term(
    old_code: str,
    old_scale: str,
    length: str,
    first: str,
    second: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    old_bound = _lt_term(
        index,
        length,
        tag=f"{tag}_old_bound",
        avoid=avoid,
    )
    old_entry = _beta_at_term(
        old_code,
        old_scale,
        index,
        value,
        tag=f"{tag}_old_entry",
        avoid=avoid,
    )
    return (
        f"(({index} = S ({length}) /\\ {value} = {second}) \\/ "
        f"(({index} = {length} /\\ {value} = {first}) \\/ "
        f"(({old_bound}) /\\ ({old_entry}))))"
    )


def make_wilson_pair_order_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered constructive PairOrder entrance ladder."""

    append_result = append_two_trace(
        "b", "c", "z", "d", "l", "a", "e", tag="append_result"
    )
    append_old_middle = _beta_at_term(
        "x",
        "x1",
        "i",
        "v",
        tag="append_old_middle",
        avoid=("b", "c", "l", "a", "e", "x", "x1", "i", "v"),
    )

    reflect_trace = append_two_trace(
        "b", "c", "z", "d", "l", "a", "e", tag="reflect_trace"
    )
    reflect_new_bound = _lt_term(
        "i",
        "S (S l)",
        tag="reflect_new_bound",
        avoid=("b", "c", "z", "d", "l", "a", "e", "i", "v"),
    )
    reflect_new_entry = _beta_at_term(
        "z",
        "d",
        "i",
        "v",
        tag="reflect_new_entry",
        avoid=("b", "c", "z", "d", "l", "a", "e", "i", "v"),
    )
    reflect_result = _append_two_reflection_term(
        "b",
        "c",
        "l",
        "a",
        "e",
        "i",
        "v",
        tag="reflect_result",
        avoid=("b", "c", "z", "d", "l", "a", "e", "i", "v"),
    )
    reflect_old_exists_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "w",
        tag="reflect_old_exists_entry",
        avoid=("b", "c", "z", "d", "l", "a", "e", "i", "v", "w"),
    )
    reflect_theorem_statement = (
        f"forall b c z d l a e. ({reflect_trace}) -> forall i v. "
        f"({reflect_new_bound}) -> ({reflect_new_entry}) -> ({reflect_result})"
    )
    choose_augmented_trace = _append_two_trace_term(
        "b",
        "c",
        "z",
        "d",
        "l",
        "0",
        "r",
        tag="choose_augmented_trace",
        avoid=("b", "c", "l", "n", "r", "z", "d"),
    )
    choose_augmented_omit = _omits_some_term(
        "x",
        "x1",
        "S (S l)",
        "n",
        tag="choose_augmented_omit",
        avoid=("b", "c", "l", "n", "r", "x", "x1"),
    )
    choose_old_omit_y = _omits_value_term(
        "b",
        "c",
        "l",
        "x2",
        tag="choose_old_omit_y",
        avoid=("b", "c", "l", "n", "r", "x", "x1", "x2"),
    )
    choose_result_bound = _lt_term(
        "y",
        "n",
        tag="choose_result_bound",
        avoid=("b", "c", "l", "n", "r", "y"),
    )
    choose_result_omit = _omits_value_term(
        "b",
        "c",
        "l",
        "y",
        tag="choose_result_omit",
        avoid=("b", "c", "l", "n", "r", "y"),
    )
    choose_result = (
        f"exists y. (({choose_result_bound}) /\\ "
        f"((~(y = 0) /\\ ~((S y) = n)) /\\ ({choose_result_omit})))"
    )

    orbit_prime = prime("p", tag="choose_orbit_prime")
    orbit_full_prefix = inverse_prefix(
        "p", "n", "u", "v", "n", tag="choose_orbit_full_prefix"
    )
    orbit_source_bound = _lt_term(
        "i",
        "n",
        tag="choose_orbit_source_bound",
        avoid=("p", "n", "u", "v", "b", "c", "l", "r", "i", "j"),
    )
    orbit_mate_bound = _lt_term(
        "j",
        "n",
        tag="choose_orbit_mate_bound",
        avoid=("p", "n", "u", "v", "b", "c", "l", "r", "i", "j"),
    )
    orbit_source_omit = _omits_value_term(
        "b",
        "c",
        "l",
        "i",
        tag="choose_orbit_source_omit",
        avoid=("p", "n", "u", "v", "b", "c", "l", "r", "i", "j"),
    )
    orbit_forward = _beta_at_term(
        "u",
        "v",
        "i",
        "j",
        tag="choose_orbit_forward",
        avoid=("p", "n", "u", "v", "b", "c", "l", "r", "i", "j"),
    )
    orbit_back = _beta_at_term(
        "u",
        "v",
        "j",
        "i",
        tag="choose_orbit_back",
        avoid=("p", "n", "u", "v", "b", "c", "l", "r", "i", "j"),
    )
    orbit_result = (
        f"exists i j. (({orbit_source_bound}) /\\ "
        f"((~(i = 0) /\\ ~((S i) = n)) /\\ "
        f"(({orbit_source_omit}) /\\ (({orbit_forward}) /\\ "
        f"(({orbit_mate_bound}) /\\ ((~(j = 0) /\\ ~((S j) = n)) /\\ "
        f"(~(i = j) /\\ ({orbit_back}))))))))"
    )
    orbit_stored_x = (
        "exists j. (("
        + _beta_at_term(
            "u",
            "v",
            "x",
            "j",
            tag="choose_orbit_stored_x_entry",
            avoid=("p", "n", "u", "v", "b", "c", "l", "r", "x", "j"),
        )
        + ") /\\ ("
        + inverse_index("p", "n", "x", "j", tag="choose_orbit_stored_x_inverse")
        + "))"
    )
    orbit_mate_nonendpoint_x = nonendpoint("x1", "n")
    orbit_back_pair_x = (
        "(("
        + _lt_term(
            "x1",
            "n",
            tag="choose_orbit_back_x_bound",
            avoid=("p", "n", "u", "v", "b", "c", "l", "r", "x", "x1"),
        )
        + ") /\\ ("
        + _beta_at_term(
            "u",
            "v",
            "x1",
            "x",
            tag="choose_orbit_back_x_entry",
            avoid=("p", "n", "u", "v", "b", "c", "l", "r", "x", "x1"),
        )
        + "))"
    )

    unused_closed = orbit_closed_prefix(
        "u", "v", "b", "c", "l", tag="unused_closed"
    )
    unused_source_omit = omits_value(
        "b", "c", "l", "i", tag="unused_source_omit"
    )
    unused_back = _beta_at_term(
        "u",
        "v",
        "j",
        "i",
        tag="unused_back",
        avoid=("u", "v", "b", "c", "l", "i", "j"),
    )
    unused_mate_omit = omits_value(
        "b", "c", "l", "j", tag="unused_mate_omit"
    )
    unused_source_occurs = _contains_term(
        "b",
        "c",
        "l",
        "i",
        tag="unused_source_occurs",
        avoid=("u", "v", "b", "c", "l", "i", "j"),
    )

    closure_trace = append_two_trace(
        "b", "c", "z", "d", "l", "a", "e", tag="closure_trace"
    )
    closure_before = orbit_closed_prefix(
        "u", "v", "b", "c", "l", tag="closure_before"
    )
    closure_forward = _beta_at_term(
        "u",
        "v",
        "a",
        "e",
        tag="closure_forward",
        avoid=("u", "v", "b", "c", "z", "d", "l", "a", "e"),
    )
    closure_back = _beta_at_term(
        "u",
        "v",
        "e",
        "a",
        tag="closure_back",
        avoid=("u", "v", "b", "c", "z", "d", "l", "a", "e"),
    )
    closure_after = _orbit_closed_prefix_term(
        "u",
        "v",
        "z",
        "d",
        "S (S l)",
        tag="closure_after",
        avoid=("u", "v", "b", "c", "z", "d", "l", "a", "e"),
    )
    closure_reflection = _append_two_reflection_term(
        "b",
        "c",
        "l",
        "a",
        "e",
        "q",
        "s",
        tag="closure_reflection",
        avoid=("u", "v", "b", "c", "z", "d", "l", "a", "e", "q", "s", "m"),
    )
    closure_reflection_bound = _lt_term(
        "q",
        "S (S l)",
        tag="closure_reflection_bound",
        avoid=("u", "v", "b", "c", "z", "d", "l", "a", "e", "q", "s", "m"),
    )
    closure_reflection_entry = _beta_at_term(
        "z",
        "d",
        "q",
        "s",
        tag="closure_reflection_entry",
        avoid=("u", "v", "b", "c", "z", "d", "l", "a", "e", "q", "s", "m"),
    )
    closure_reflection_all = (
        f"forall q s. ({closure_reflection_bound}) -> "
        f"({closure_reflection_entry}) -> ({closure_reflection})"
    )
    closure_old_occurrence = _contains_term(
        "b",
        "c",
        "l",
        "m",
        tag="closure_old_occurrence",
        avoid=("u", "v", "b", "c", "z", "d", "l", "a", "e", "q", "s", "m"),
    )

    nonendpoint_trace = append_two_trace(
        "b", "c", "z", "d", "l", "a", "e", tag="nonendpoint_trace"
    )
    nonendpoint_before = nonendpoint_prefix(
        "b", "c", "l", "n", tag="nonendpoint_before"
    )
    nonendpoint_first = nonendpoint("a", "n")
    nonendpoint_second = nonendpoint("e", "n")
    nonendpoint_after = _nonendpoint_prefix_term(
        "z",
        "d",
        "S (S l)",
        "n",
        tag="nonendpoint_after",
        avoid=("b", "c", "z", "d", "l", "n", "a", "e"),
    )
    nonendpoint_reflection = _append_two_reflection_term(
        "b",
        "c",
        "l",
        "a",
        "e",
        "q",
        "s",
        tag="nonendpoint_reflection",
        avoid=("b", "c", "z", "d", "l", "n", "a", "e", "q", "s"),
    )
    nonendpoint_reflection_bound = _lt_term(
        "q",
        "S (S l)",
        tag="nonendpoint_reflection_bound",
        avoid=("b", "c", "z", "d", "l", "n", "a", "e", "q", "s"),
    )
    nonendpoint_reflection_entry = _beta_at_term(
        "z",
        "d",
        "q",
        "s",
        tag="nonendpoint_reflection_entry",
        avoid=("b", "c", "z", "d", "l", "n", "a", "e", "q", "s"),
    )
    nonendpoint_reflection_all = (
        f"forall q s. ({nonendpoint_reflection_bound}) -> "
        f"({nonendpoint_reflection_entry}) -> ({nonendpoint_reflection})"
    )

    injective_trace = append_two_trace(
        "b", "c", "z", "d", "l", "a", "e", tag="injective_trace"
    )
    injective_before = _injective_prefix_term(
        "b",
        "c",
        "l",
        tag="injective_before",
        avoid=("b", "c", "z", "d", "l", "a", "e"),
    )
    injective_first_omit = omits_value(
        "b", "c", "l", "a", tag="injective_first_omit"
    )
    injective_second_omit = omits_value(
        "b", "c", "l", "e", tag="injective_second_omit"
    )
    injective_after = _injective_prefix_term(
        "z",
        "d",
        "S (S l)",
        tag="injective_after",
        avoid=("b", "c", "z", "d", "l", "a", "e"),
    )
    injective_left_reflection = _append_two_reflection_term(
        "b",
        "c",
        "l",
        "a",
        "e",
        "q",
        "w",
        tag="injective_left_reflection",
        avoid=("b", "c", "z", "d", "l", "a", "e", "q", "r", "w"),
    )
    injective_right_reflection = _append_two_reflection_term(
        "b",
        "c",
        "l",
        "a",
        "e",
        "r",
        "w",
        tag="injective_right_reflection",
        avoid=("b", "c", "z", "d", "l", "a", "e", "q", "r", "w"),
    )
    injective_left_bound = _lt_term(
        "q",
        "S (S l)",
        tag="injective_left_bound",
        avoid=("b", "c", "z", "d", "l", "a", "e", "q", "r", "w"),
    )
    injective_right_bound = _lt_term(
        "r",
        "S (S l)",
        tag="injective_right_bound",
        avoid=("b", "c", "z", "d", "l", "a", "e", "q", "r", "w"),
    )
    injective_left_entry = _beta_at_term(
        "z",
        "d",
        "q",
        "w",
        tag="injective_left_entry",
        avoid=("b", "c", "z", "d", "l", "a", "e", "q", "r", "w"),
    )
    injective_right_entry = _beta_at_term(
        "z",
        "d",
        "r",
        "w",
        tag="injective_right_entry",
        avoid=("b", "c", "z", "d", "l", "a", "e", "q", "r", "w"),
    )
    injective_left_reflection_all = (
        f"forall q w. ({injective_left_bound}) -> "
        f"({injective_left_entry}) -> ({injective_left_reflection})"
    )
    injective_right_reflection_all = (
        f"forall r w. ({injective_right_bound}) -> "
        f"({injective_right_entry}) -> ({injective_right_reflection})"
    )

    step_closed_before = orbit_closed_prefix(
        "u", "v", "b", "c", "l", tag="step_closed_before"
    )
    step_nonendpoint_before = nonendpoint_prefix(
        "b", "c", "l", "n", tag="step_nonendpoint_before"
    )
    step_trace = _append_two_trace_term(
        "b",
        "c",
        "z",
        "d",
        "l",
        "i",
        "j",
        tag="step_trace",
        avoid=("p", "n", "u", "v", "b", "c", "l", "r", "z", "d", "i", "j"),
    )
    step_mate_omit = _omits_value_term(
        "b",
        "c",
        "l",
        "j",
        tag="step_mate_omit",
        avoid=("p", "n", "u", "v", "b", "c", "l", "r", "z", "d", "i", "j"),
    )
    step_closed_after = _orbit_closed_prefix_term(
        "u",
        "v",
        "z",
        "d",
        "S (S l)",
        tag="step_closed_after",
        avoid=("p", "n", "u", "v", "b", "c", "l", "r", "z", "d", "i", "j"),
    )
    step_nonendpoint_after = _nonendpoint_prefix_term(
        "z",
        "d",
        "S (S l)",
        "n",
        tag="step_nonendpoint_after",
        avoid=("p", "n", "u", "v", "b", "c", "l", "r", "z", "d", "i", "j"),
    )
    step_result = (
        f"exists z d i j. (({step_trace}) /\\ "
        f"(({orbit_source_bound}) /\\ "
        f"((~(i = 0) /\\ ~((S i) = n)) /\\ "
        f"(({orbit_source_omit}) /\\ (({orbit_forward}) /\\ "
        f"(({orbit_mate_bound}) /\\ "
        f"((~(j = 0) /\\ ~((S j) = n)) /\\ "
        f"(~(i = j) /\\ (({orbit_back}) /\\ "
        f"(({step_mate_omit}) /\\ "
        f"(({step_closed_after}) /\\ ({step_nonendpoint_after}))))))))))))"
    )
    return (
        spec(
            "beta_prefix_append_two_exists",
            f"forall b c l a e. exists z d. ({append_result})",
            ("beta_prefix_extend", "le_refl", "le_succ"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro a",
                "intro e",
                "have hfirst_extend : forall k q s v. exists r t. "
                "(((exists h. h + S v = S ((S k) * t)) /\\ "
                "exists u. r = u * S ((S k) * t) + v) /\\ "
                "forall i w. (exists h. h + S i = k) -> "
                "((exists h. h + S w = S ((S i) * s)) /\\ "
                "exists u. q = u * S ((S i) * s) + w) -> "
                "((exists h. h + S w = S ((S i) * t)) /\\ "
                "exists u. r = u * S ((S i) * t) + w))",
                "exact beta_prefix_extend",
                "have hsecond_extend : forall k q s v. exists r t. "
                "(((exists h. h + S v = S ((S k) * t)) /\\ "
                "exists u. r = u * S ((S k) * t) + v) /\\ "
                "forall i w. (exists h. h + S i = k) -> "
                "((exists h. h + S w = S ((S i) * s)) /\\ "
                "exists u. q = u * S ((S i) * s) + w) -> "
                "((exists h. h + S w = S ((S i) * t)) /\\ "
                "exists u. r = u * S ((S i) * t) + w))",
                "exact beta_prefix_extend",
                "specialize hfirst_extend l",
                "specialize hfirst_extend b",
                "specialize hfirst_extend c",
                "specialize hfirst_extend a",
                "cases hfirst_extend",
                "cases hfirst_extend_witness",
                "cases hfirst_extend_witness_witness",
                "specialize hsecond_extend (S l)",
                "specialize hsecond_extend x",
                "specialize hsecond_extend x1",
                "specialize hsecond_extend e",
                "cases hsecond_extend",
                "cases hsecond_extend_witness",
                "cases hsecond_extend_witness_witness",
                "exists x2",
                "exists x3",
                "split",
                "specialize hsecond_extend_witness_witness_right l",
                "specialize hsecond_extend_witness_witness_right a",
                "apply hsecond_extend_witness_witness_right",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hfirst_extend_witness_witness_left",
                "split",
                "exact hsecond_extend_witness_witness_left",
                "intro i",
                "intro v",
                "intro hi",
                "intro hold",
                f"have hmiddle : {append_old_middle}",
                "specialize hfirst_extend_witness_witness_right i",
                "specialize hfirst_extend_witness_witness_right v",
                "apply hfirst_extend_witness_witness_right",
                "exact hi",
                "exact hold",
                "specialize hsecond_extend_witness_witness_right i",
                "specialize hsecond_extend_witness_witness_right v",
                "apply hsecond_extend_witness_witness_right",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact hmiddle",
            ),
            "Append two values at consecutive beta positions while preserving every old entry.",
        ),
        spec(
            "beta_prefix_append_two_reflect",
            f"forall b c z d l a e. ({reflect_trace}) -> forall i v. "
            f"({reflect_new_bound}) -> ({reflect_new_entry}) -> ({reflect_result})",
            (
                "finite_lt_succ_eq_or_lt",
                "beta_at_exists",
                "beta_at_unique",
            ),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro l",
                "intro a",
                "intro e",
                "intro htrace",
                "cases htrace",
                "cases htrace_right",
                "intro i",
                "intro v",
                "intro hi",
                "intro hentry",
                "have htop : i = S l \/ exists h. h + S i = S l",
                "specialize finite_lt_succ_eq_or_lt (S l)",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases htop",
                "left",
                "split",
                "exact htop_left",
                "have hive : v = e",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique (S l)",
                "specialize beta_at_unique v",
                "specialize beta_at_unique e",
                "apply beta_at_unique",
                "rewrite htop_left at hentry",
                "rewrite htop_left at hentry",
                "exact hentry",
                "exact htrace_right_left",
                "exact hive",
                "have hmiddle : i = l \/ exists h. h + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact htop_right",
                "cases hmiddle",
                "right",
                "left",
                "split",
                "exact hmiddle_left",
                "have hiva : v = a",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique l",
                "specialize beta_at_unique v",
                "specialize beta_at_unique a",
                "apply beta_at_unique",
                "rewrite hmiddle_left at hentry",
                "rewrite hmiddle_left at hentry",
                "exact hentry",
                "exact htrace_left",
                "exact hiva",
                f"have hold : exists w. ({reflect_old_exists_entry})",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists i",
                "exact beta_at_exists",
                "cases hold",
                "have hnew_old : "
                "((exists h. h + S x = S ((S i) * d)) /\\ "
                "exists q. z = q * S ((S i) * d) + x)",
                "specialize htrace_right_right i",
                "specialize htrace_right_right x",
                "apply htrace_right_right",
                "exact hmiddle_right",
                "exact hold_witness",
                "have hivx : v = x",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique i",
                "specialize beta_at_unique v",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hentry",
                "exact hnew_old",
                "right",
                "right",
                "split",
                "exact hmiddle_right",
                "rewrite <- hivx at hold_witness",
                "rewrite <- hivx at hold_witness",
                "exact hold_witness",
            ),
            "Every entry of a two-appended prefix is the second append, the first append, or an old entry.",
        ),
        spec(
            "finite_prefix_choose_unused_nonendpoint",
            "forall b c l n r. n = S r -> "
            "(exists h. h + S (S (S l)) = n) -> "
            f"({choose_result})",
            (
                "beta_prefix_append_two_exists",
                "finite_short_prefix_omits",
                "le_refl",
                "le_succ",
                "succ_injective",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro r",
                "intro hnr",
                "intro hshort",
                f"have haugmented : exists z d. ({choose_augmented_trace})",
                "specialize beta_prefix_append_two_exists b",
                "specialize beta_prefix_append_two_exists c",
                "specialize beta_prefix_append_two_exists l",
                "specialize beta_prefix_append_two_exists 0",
                "specialize beta_prefix_append_two_exists r",
                "exact beta_prefix_append_two_exists",
                "cases haugmented",
                "cases haugmented_witness",
                f"have homitted : {choose_augmented_omit}",
                "specialize finite_short_prefix_omits x",
                "specialize finite_short_prefix_omits x1",
                "specialize finite_short_prefix_omits (S (S l))",
                "specialize finite_short_prefix_omits n",
                "apply finite_short_prefix_omits",
                "exact hshort",
                "cases homitted",
                "cases homitted_witness",
                "cases haugmented_witness_witness",
                "cases haugmented_witness_witness_right",
                "exists x2",
                "split",
                "exact homitted_witness_left",
                "split",
                "split",
                "intro hxzero",
                "apply homitted_witness_right",
                "exists l",
                "split",
                "specialize le_succ (S l)",
                "specialize le_succ (S l)",
                "apply le_succ",
                "specialize le_refl (S l)",
                "exact le_refl",
                "rewrite hxzero",
                "rewrite hxzero",
                "exact haugmented_witness_witness_left",
                "intro hxlast",
                "have hxr : x2 = r",
                "specialize succ_injective x2",
                "specialize succ_injective r",
                "apply succ_injective",
                "trans n",
                "exact hxlast",
                "exact hnr",
                "apply homitted_witness_right",
                "exists (S l)",
                "split",
                "specialize le_refl (S (S l))",
                "exact le_refl",
                "rewrite hxr",
                "rewrite hxr",
                "exact haugmented_witness_witness_right_left",
                f"have hold_omit : {choose_old_omit_y}",
                "intro hold_contains",
                "cases hold_contains",
                "cases hold_contains_witness",
                "have hlift : exists h. h + S x3 = S l",
                "specialize le_succ (S x3)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hold_contains_witness_left",
                "have hlift2 : exists h. h + S x3 = S (S l)",
                "specialize le_succ (S x3)",
                "specialize le_succ (S l)",
                "apply le_succ",
                "exact hlift",
                "have hnew_entry : "
                "((exists h. h + S x2 = S ((S x3) * x1)) /\\ "
                "exists q. x = q * S ((S x3) * x1) + x2)",
                "specialize haugmented_witness_witness_right_right x3",
                "specialize haugmented_witness_witness_right_right x2",
                "apply haugmented_witness_witness_right_right",
                "exact hold_contains_witness_left",
                "exact hold_contains_witness_right",
                "apply homitted_witness_right",
                "exists x3",
                "split",
                "exact hlift2",
                "exact hnew_entry",
                "exact hold_omit",
            ),
            "By temporarily appending both endpoints, finite omission constructively selects a missing nonendpoint value.",
        ),
        spec(
            "prime_choose_unused_nonendpoint_orbit",
            f"forall p n u v b c l r. p = S n -> ({orbit_prime}) -> "
            f"({orbit_full_prefix}) -> n = S r -> "
            "(exists h. h + S (S (S l)) = n) -> "
            f"({orbit_result})",
            (
                "finite_prefix_choose_unused_nonendpoint",
                "prime_inverse_prefix_nonendpoint_mate",
                "prime_inverse_prefix_nonendpoint_not_fixed",
                "inverse_prefix_involutive",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro r",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hnr",
                "intro hshort",
                f"have hchoose : {choose_result}",
                "specialize finite_prefix_choose_unused_nonendpoint b",
                "specialize finite_prefix_choose_unused_nonendpoint c",
                "specialize finite_prefix_choose_unused_nonendpoint l",
                "specialize finite_prefix_choose_unused_nonendpoint n",
                "specialize finite_prefix_choose_unused_nonendpoint r",
                "apply finite_prefix_choose_unused_nonendpoint",
                "exact hnr",
                "exact hshort",
                "cases hchoose",
                "cases hchoose_witness",
                "cases hchoose_witness_right",
                f"have hmate_prefix : {orbit_full_prefix}",
                "exact hprefix",
                f"have hnonfixed_prefix : {orbit_full_prefix}",
                "exact hprefix",
                f"have hback_prefix : {orbit_full_prefix}",
                "exact hprefix",
                f"have hstored : {orbit_stored_x}",
                "specialize hprefix x",
                "apply hprefix",
                "exact hchoose_witness_left",
                "cases hstored",
                "cases hstored_witness",
                f"have hmate_nonendpoint : {orbit_mate_nonendpoint_x}",
                "specialize prime_inverse_prefix_nonendpoint_mate p",
                "specialize prime_inverse_prefix_nonendpoint_mate n",
                "specialize prime_inverse_prefix_nonendpoint_mate u",
                "specialize prime_inverse_prefix_nonendpoint_mate v",
                "specialize prime_inverse_prefix_nonendpoint_mate x",
                "specialize prime_inverse_prefix_nonendpoint_mate x1",
                "apply prime_inverse_prefix_nonendpoint_mate",
                "exact hpn",
                "exact hp",
                "exact hmate_prefix",
                "exact hchoose_witness_left",
                "exact hstored_witness_left",
                "exact hchoose_witness_right_left",
                "have hnonfixed : ~(x = x1)",
                "intro hxx1",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed p",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed n",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed u",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed v",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed x",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed x1",
                "apply prime_inverse_prefix_nonendpoint_not_fixed",
                "exact hpn",
                "exact hp",
                "exact hnonfixed_prefix",
                "exact hchoose_witness_left",
                "exact hstored_witness_left",
                "exact hchoose_witness_right_left",
                "exact hxx1",
                f"have hback : {orbit_back_pair_x}",
                "specialize inverse_prefix_involutive p",
                "specialize inverse_prefix_involutive n",
                "specialize inverse_prefix_involutive u",
                "specialize inverse_prefix_involutive v",
                "specialize inverse_prefix_involutive x",
                "specialize inverse_prefix_involutive x1",
                "apply inverse_prefix_involutive",
                "exact hpn",
                "exact hback_prefix",
                "exact hchoose_witness_left",
                "exact hstored_witness_left",
                "cases hback",
                "exists x",
                "exists x1",
                "split",
                "exact hchoose_witness_left",
                "split",
                "exact hchoose_witness_right_left",
                "split",
                "exact hchoose_witness_right_right",
                "split",
                "exact hstored_witness_left",
                "split",
                "exact hback_left",
                "split",
                "exact hmate_nonendpoint",
                "split",
                "exact hnonfixed",
                "exact hback_right",
            ),
            "Choose an omitted nonendpoint index and extract its distinct, nonendpoint inverse mate together with both decoded directions.",
        ),
        spec(
            "orbit_closed_unused_mate",
            f"forall u v b c l i j. ({unused_closed}) -> "
            f"({unused_source_omit}) -> ({unused_back}) -> "
            f"({unused_mate_omit})",
            (),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro j",
                "intro hclosed",
                "intro hiomit",
                "intro hback",
                "intro hjcontains",
                "cases hjcontains",
                "cases hjcontains_witness",
                f"have hioccurs : {unused_source_occurs}",
                "specialize hclosed x",
                "specialize hclosed j",
                "specialize hclosed i",
                "apply hclosed",
                "exact hjcontains_witness_left",
                "exact hjcontains_witness_right",
                "exact hback",
                "cases hioccurs",
                "cases hioccurs_witness",
                "apply hiomit",
                "exists x1",
                "split",
                "exact hioccurs_witness_left",
                "exact hioccurs_witness_right",
            ),
            "Orbit closure turns omission of one endpoint of a decoded two-cycle into omission of its mate.",
        ),
        spec(
            "beta_prefix_append_two_orbit_closed",
            f"forall u v b c z d l a e. ({closure_trace}) -> "
            f"({closure_before}) -> ({closure_forward}) -> "
            f"({closure_back}) -> ({closure_after})",
            (
                "beta_prefix_append_two_reflect",
                "beta_at_unique",
                "le_refl",
                "le_succ",
            ),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro l",
                "intro a",
                "intro e",
                "intro htrace",
                "intro hclosed",
                "intro hforward",
                "intro hback",
                f"have htrace_parts : {closure_trace}",
                "exact htrace",
                "cases htrace_parts",
                "cases htrace_parts_right",
                "intro q",
                "intro s",
                "intro m",
                "intro hq",
                "intro hsource",
                "intro hinverse",
                f"have hreflect_all : {closure_reflection_all}",
                "specialize beta_prefix_append_two_reflect b",
                "specialize beta_prefix_append_two_reflect c",
                "specialize beta_prefix_append_two_reflect z",
                "specialize beta_prefix_append_two_reflect d",
                "specialize beta_prefix_append_two_reflect l",
                "specialize beta_prefix_append_two_reflect a",
                "specialize beta_prefix_append_two_reflect e",
                "apply beta_prefix_append_two_reflect",
                "exact htrace",
                f"have hreflect : {closure_reflection}",
                "specialize hreflect_all q",
                "specialize hreflect_all s",
                "apply hreflect_all",
                "exact hq",
                "exact hsource",
                "cases hreflect",
                "cases hreflect_left",
                "have hmate_first : m = a",
                "specialize beta_at_unique u",
                "specialize beta_at_unique v",
                "specialize beta_at_unique e",
                "specialize beta_at_unique m",
                "specialize beta_at_unique a",
                "apply beta_at_unique",
                "rewrite hreflect_left_right at hinverse",
                "rewrite hreflect_left_right at hinverse",
                "exact hinverse",
                "exact hback",
                "exists l",
                "split",
                "specialize le_succ (S l)",
                "specialize le_succ (S l)",
                "apply le_succ",
                "specialize le_refl (S l)",
                "exact le_refl",
                "rewrite hmate_first",
                "rewrite hmate_first",
                "exact htrace_parts_left",
                "cases hreflect_right",
                "cases hreflect_right_left",
                "have hmate_second : m = e",
                "specialize beta_at_unique u",
                "specialize beta_at_unique v",
                "specialize beta_at_unique a",
                "specialize beta_at_unique m",
                "specialize beta_at_unique e",
                "apply beta_at_unique",
                "rewrite hreflect_right_left_right at hinverse",
                "rewrite hreflect_right_left_right at hinverse",
                "exact hinverse",
                "exact hforward",
                "exists (S l)",
                "split",
                "specialize le_refl (S (S l))",
                "exact le_refl",
                "rewrite hmate_second",
                "rewrite hmate_second",
                "exact htrace_parts_right_left",
                "cases hreflect_right_right",
                f"have hold_occurrence : {closure_old_occurrence}",
                "specialize hclosed q",
                "specialize hclosed s",
                "specialize hclosed m",
                "apply hclosed",
                "exact hreflect_right_right_left",
                "exact hreflect_right_right_right",
                "exact hinverse",
                "cases hold_occurrence",
                "cases hold_occurrence_witness",
                "exists x",
                "split",
                "have hlift : exists h. h + S x = S l",
                "specialize le_succ (S x)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hold_occurrence_witness_left",
                "specialize le_succ (S x)",
                "specialize le_succ (S l)",
                "apply le_succ",
                "exact hlift",
                "specialize htrace_parts_right_right x",
                "specialize htrace_parts_right_right m",
                "apply htrace_parts_right_right",
                "exact hold_occurrence_witness_left",
                "exact hold_occurrence_witness_right",
            ),
            "Appending both directions of a decoded two-cycle preserves orbit closure of the used prefix.",
        ),
        spec(
            "beta_prefix_append_two_nonendpoint",
            f"forall b c z d l n a e. ({nonendpoint_trace}) -> "
            f"({nonendpoint_before}) -> ({nonendpoint_first}) -> "
            f"({nonendpoint_second}) -> ({nonendpoint_after})",
            ("beta_prefix_append_two_reflect",),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro l",
                "intro n",
                "intro a",
                "intro e",
                "intro htrace",
                "intro hold_nonendpoint",
                "intro hfirst_nonendpoint",
                "intro hsecond_nonendpoint",
                "intro q",
                "intro s",
                "intro hq",
                "intro hentry",
                f"have hreflect_all : {nonendpoint_reflection_all}",
                "specialize beta_prefix_append_two_reflect b",
                "specialize beta_prefix_append_two_reflect c",
                "specialize beta_prefix_append_two_reflect z",
                "specialize beta_prefix_append_two_reflect d",
                "specialize beta_prefix_append_two_reflect l",
                "specialize beta_prefix_append_two_reflect a",
                "specialize beta_prefix_append_two_reflect e",
                "apply beta_prefix_append_two_reflect",
                "exact htrace",
                f"have hreflect : {nonendpoint_reflection}",
                "specialize hreflect_all q",
                "specialize hreflect_all s",
                "apply hreflect_all",
                "exact hq",
                "exact hentry",
                "cases hreflect",
                "cases hreflect_left",
                "rewrite hreflect_left_right",
                "rewrite hreflect_left_right",
                "exact hsecond_nonendpoint",
                "cases hreflect_right",
                "cases hreflect_right_left",
                "rewrite hreflect_right_left_right",
                "rewrite hreflect_right_left_right",
                "exact hfirst_nonendpoint",
                "cases hreflect_right_right",
                "specialize hold_nonendpoint q",
                "specialize hold_nonendpoint s",
                "apply hold_nonendpoint",
                "exact hreflect_right_right_left",
                "exact hreflect_right_right_right",
            ),
            "A two-entry append preserves the nonendpoint invariant when both appended values satisfy it.",
        ),
        spec(
            "beta_prefix_append_two_injective",
            f"forall b c z d l a e. ({injective_trace}) -> "
            f"({injective_before}) -> ({injective_first_omit}) -> "
            f"({injective_second_omit}) -> ~(a = e) -> ({injective_after})",
            ("beta_prefix_append_two_reflect",),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro l",
                "intro a",
                "intro e",
                "intro htrace",
                "intro hold_injective",
                "intro hfirst_omit",
                "intro hsecond_omit",
                "intro hdistinct",
                f"have hright_reflect_theorem : {reflect_theorem_statement}",
                "exact beta_prefix_append_two_reflect",
                "intro q",
                "intro r",
                "intro w",
                "intro hq",
                "intro hr",
                "intro hleft_entry",
                "intro hright_entry",
                f"have hleft_all : {injective_left_reflection_all}",
                "specialize beta_prefix_append_two_reflect b",
                "specialize beta_prefix_append_two_reflect c",
                "specialize beta_prefix_append_two_reflect z",
                "specialize beta_prefix_append_two_reflect d",
                "specialize beta_prefix_append_two_reflect l",
                "specialize beta_prefix_append_two_reflect a",
                "specialize beta_prefix_append_two_reflect e",
                "apply beta_prefix_append_two_reflect",
                "exact htrace",
                f"have hright_all : {injective_right_reflection_all}",
                "specialize hright_reflect_theorem b",
                "specialize hright_reflect_theorem c",
                "specialize hright_reflect_theorem z",
                "specialize hright_reflect_theorem d",
                "specialize hright_reflect_theorem l",
                "specialize hright_reflect_theorem a",
                "specialize hright_reflect_theorem e",
                "apply hright_reflect_theorem",
                "exact htrace",
                f"have hleft_class : {injective_left_reflection}",
                "specialize hleft_all q",
                "specialize hleft_all w",
                "apply hleft_all",
                "exact hq",
                "exact hleft_entry",
                f"have hright_class : {injective_right_reflection}",
                "specialize hright_all r",
                "specialize hright_all w",
                "apply hright_all",
                "exact hr",
                "exact hright_entry",
                "cases hleft_class",
                "cases hleft_class_left",
                "cases hright_class",
                "cases hright_class_left",
                "trans (S l)",
                "exact hleft_class_left_left",
                "symm",
                "exact hright_class_left_left",
                "cases hright_class_right",
                "cases hright_class_right_left",
                "exfalso",
                "apply hdistinct",
                "trans w",
                "symm",
                "exact hright_class_right_left_right",
                "exact hleft_class_left_right",
                "cases hright_class_right_right",
                "exfalso",
                "apply hsecond_omit",
                "exists r",
                "split",
                "exact hright_class_right_right_left",
                "rewrite hleft_class_left_right at hright_class_right_right_right",
                "rewrite hleft_class_left_right at hright_class_right_right_right",
                "exact hright_class_right_right_right",
                "cases hleft_class_right",
                "cases hleft_class_right_left",
                "cases hright_class",
                "cases hright_class_left",
                "exfalso",
                "apply hdistinct",
                "trans w",
                "symm",
                "exact hleft_class_right_left_right",
                "exact hright_class_left_right",
                "cases hright_class_right",
                "cases hright_class_right_left",
                "trans l",
                "exact hleft_class_right_left_left",
                "symm",
                "exact hright_class_right_left_left",
                "cases hright_class_right_right",
                "exfalso",
                "apply hfirst_omit",
                "exists r",
                "split",
                "exact hright_class_right_right_left",
                "rewrite hleft_class_right_left_right at hright_class_right_right_right",
                "rewrite hleft_class_right_left_right at hright_class_right_right_right",
                "exact hright_class_right_right_right",
                "cases hleft_class_right_right",
                "cases hright_class",
                "cases hright_class_left",
                "exfalso",
                "apply hsecond_omit",
                "exists q",
                "split",
                "exact hleft_class_right_right_left",
                "rewrite hright_class_left_right at hleft_class_right_right_right",
                "rewrite hright_class_left_right at hleft_class_right_right_right",
                "exact hleft_class_right_right_right",
                "cases hright_class_right",
                "cases hright_class_right_left",
                "exfalso",
                "apply hfirst_omit",
                "exists q",
                "split",
                "exact hleft_class_right_right_left",
                "rewrite hright_class_right_left_right at hleft_class_right_right_right",
                "rewrite hright_class_right_left_right at hleft_class_right_right_right",
                "exact hleft_class_right_right_right",
                "cases hright_class_right_right",
                "specialize hold_injective q",
                "specialize hold_injective r",
                "specialize hold_injective w",
                "apply hold_injective",
                "exact hleft_class_right_right_left",
                "exact hright_class_right_right_left",
                "exact hleft_class_right_right_right",
                "exact hright_class_right_right_right",
            ),
            "Appending two distinct values omitted by an injective old prefix preserves decoded-prefix injectivity.",
        ),
        spec(
            "prime_pair_order_choose_append",
            f"forall p n u v b c l r. p = S n -> ({orbit_prime}) -> "
            f"({orbit_full_prefix}) -> n = S r -> "
            "(exists h. h + S (S (S l)) = n) -> "
            f"({step_closed_before}) -> ({step_nonendpoint_before}) -> "
            f"({step_result})",
            (
                "prime_choose_unused_nonendpoint_orbit",
                "orbit_closed_unused_mate",
                "beta_prefix_append_two_exists",
                "beta_prefix_append_two_orbit_closed",
                "beta_prefix_append_two_nonendpoint",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro r",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hnr",
                "intro hshort",
                "intro hclosed",
                "intro hnonendpoint",
                f"have horbit : {orbit_result}",
                "specialize prime_choose_unused_nonendpoint_orbit p",
                "specialize prime_choose_unused_nonendpoint_orbit n",
                "specialize prime_choose_unused_nonendpoint_orbit u",
                "specialize prime_choose_unused_nonendpoint_orbit v",
                "specialize prime_choose_unused_nonendpoint_orbit b",
                "specialize prime_choose_unused_nonendpoint_orbit c",
                "specialize prime_choose_unused_nonendpoint_orbit l",
                "specialize prime_choose_unused_nonendpoint_orbit r",
                "apply prime_choose_unused_nonendpoint_orbit",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hnr",
                "exact hshort",
                "cases horbit",
                "cases horbit_witness",
                "cases horbit_witness_witness",
                "cases horbit_witness_witness_right",
                "cases horbit_witness_witness_right_right",
                "cases horbit_witness_witness_right_right_right",
                "cases horbit_witness_witness_right_right_right_right",
                "cases horbit_witness_witness_right_right_right_right_right",
                "cases horbit_witness_witness_right_right_right_right_right_right",
                f"have hmate_omit : {_omits_value_term('b', 'c', 'l', 'x1', tag='step_mate_omit_x1', avoid=('p', 'n', 'u', 'v', 'b', 'c', 'l', 'r', 'x', 'x1'))}",
                "intro hmate_contains",
                "specialize orbit_closed_unused_mate u",
                "specialize orbit_closed_unused_mate v",
                "specialize orbit_closed_unused_mate b",
                "specialize orbit_closed_unused_mate c",
                "specialize orbit_closed_unused_mate l",
                "specialize orbit_closed_unused_mate x",
                "specialize orbit_closed_unused_mate x1",
                "apply orbit_closed_unused_mate",
                "exact hclosed",
                "exact horbit_witness_witness_right_right_left",
                "exact horbit_witness_witness_right_right_right_right_right_right_right",
                "exact hmate_contains",
                "have happend : exists z d. "
                + _append_two_trace_term(
                    "b",
                    "c",
                    "z",
                    "d",
                    "l",
                    "x",
                    "x1",
                    tag="step_append_x",
                    avoid=("p", "n", "u", "v", "b", "c", "l", "r", "x", "x1", "z", "d"),
                ),
                "specialize beta_prefix_append_two_exists b",
                "specialize beta_prefix_append_two_exists c",
                "specialize beta_prefix_append_two_exists l",
                "specialize beta_prefix_append_two_exists x",
                "specialize beta_prefix_append_two_exists x1",
                "exact beta_prefix_append_two_exists",
                "cases happend",
                "cases happend_witness",
                f"have hclosed_after : {_orbit_closed_prefix_term('u', 'v', 'x2', 'x3', 'S (S l)', tag='step_closed_after_x', avoid=('p', 'n', 'u', 'v', 'b', 'c', 'l', 'r', 'x', 'x1', 'x2', 'x3'))}",
                "specialize beta_prefix_append_two_orbit_closed u",
                "specialize beta_prefix_append_two_orbit_closed v",
                "specialize beta_prefix_append_two_orbit_closed b",
                "specialize beta_prefix_append_two_orbit_closed c",
                "specialize beta_prefix_append_two_orbit_closed x2",
                "specialize beta_prefix_append_two_orbit_closed x3",
                "specialize beta_prefix_append_two_orbit_closed l",
                "specialize beta_prefix_append_two_orbit_closed x",
                "specialize beta_prefix_append_two_orbit_closed x1",
                "apply beta_prefix_append_two_orbit_closed",
                "exact happend_witness_witness",
                "exact hclosed",
                "exact horbit_witness_witness_right_right_right_left",
                "exact horbit_witness_witness_right_right_right_right_right_right_right",
                f"have hnonendpoint_after : {_nonendpoint_prefix_term('x2', 'x3', 'S (S l)', 'n', tag='step_nonendpoint_after_x', avoid=('p', 'n', 'u', 'v', 'b', 'c', 'l', 'r', 'x', 'x1', 'x2', 'x3'))}",
                "specialize beta_prefix_append_two_nonendpoint b",
                "specialize beta_prefix_append_two_nonendpoint c",
                "specialize beta_prefix_append_two_nonendpoint x2",
                "specialize beta_prefix_append_two_nonendpoint x3",
                "specialize beta_prefix_append_two_nonendpoint l",
                "specialize beta_prefix_append_two_nonendpoint n",
                "specialize beta_prefix_append_two_nonendpoint x",
                "specialize beta_prefix_append_two_nonendpoint x1",
                "apply beta_prefix_append_two_nonendpoint",
                "exact happend_witness_witness",
                "exact hnonendpoint",
                "exact horbit_witness_witness_right_left",
                "exact horbit_witness_witness_right_right_right_right_right_left",
                "exists x2",
                "exists x3",
                "exists x",
                "exists x1",
                "split",
                "exact happend_witness_witness",
                "split",
                "exact horbit_witness_witness_left",
                "split",
                "exact horbit_witness_witness_right_left",
                "split",
                "exact horbit_witness_witness_right_right_left",
                "split",
                "exact horbit_witness_witness_right_right_right_left",
                "split",
                "exact horbit_witness_witness_right_right_right_right_left",
                "split",
                "exact horbit_witness_witness_right_right_right_right_right_left",
                "split",
                "exact horbit_witness_witness_right_right_right_right_right_right_left",
                "split",
                "exact horbit_witness_witness_right_right_right_right_right_right_right",
                "split",
                "exact hmate_omit",
                "split",
                "exact hclosed_after",
                "exact hnonendpoint_after",
            ),
            "Constructively choose one unused inverse orbit, append its two directions adjacently, and preserve the orbit-closed nonendpoint prefix invariants.",
        ),
    )


__all__ = [
    "append_two_trace",
    "make_wilson_pair_order_candidate_theorems",
    "nonendpoint_prefix",
    "omits_value",
    "orbit_closed_prefix",
]
