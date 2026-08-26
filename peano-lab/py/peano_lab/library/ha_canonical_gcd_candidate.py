"""Canonical-value interface over the checked relational gcd API.

The kernel language has no gcd function or primitive divisibility predicate.
This isolated HA3 layer keeps gcd relational and expands

``IsGCD(g,a,b)``

to the unchanged first-order language ``{0,S,+,*,=}``.  The public library
already proves that the relation is total and single-valued.  The candidates
below expose those facts in a canonical argument order and package them as
unique existence.  They remain dependency-curried, unregistered, and
unadmitted.
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
            character.isalnum() or character in "_'" for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def is_gcd(
    gcd: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand ``IsGCD(gcd,left,right)`` to the base HA language."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (gcd, "gcd value"),
            (left, "left operand"),
            (right, "right operand"),
        )
    )
    gcd, left, right = variables
    safe_tag = _identifier(tag, "binder tag")
    binders = tuple(
        f"hag_{stem}_{safe_tag}"
        for stem in (
            "left_factor",
            "right_factor",
            "divisor",
            "common_left",
            "common_right",
            "greatest_factor",
        )
    )
    if len(set(binders)) != len(binders) or set(binders) & set(variables):
        raise ValueError("generated IsGCD binder captures an argument")
    (
        left_factor,
        right_factor,
        divisor,
        common_left,
        common_right,
        greatest_factor,
    ) = binders
    return (
        f"(((exists {left_factor}. {left} = {gcd} * {left_factor}) /\\ "
        f"(exists {right_factor}. {right} = {gcd} * {right_factor})) /\\ "
        f"forall {divisor}. (exists {common_left}. "
        f"{left} = {divisor} * {common_left}) -> "
        f"(exists {common_right}. {right} = {divisor} * {common_right}) -> "
        f"exists {greatest_factor}. {gcd} = {divisor} * {greatest_factor})"
    )


def unique_gcd(left: str, right: str, *, tag: str) -> str:
    """Expand unique existence of a relational gcd value."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "left operand"), (right, "right operand"))
    )
    left, right = variables
    safe_tag = _identifier(tag, "binder tag")
    chosen = f"hag_chosen_{safe_tag}"
    comparison = f"hag_comparison_{safe_tag}"
    if chosen == comparison or {chosen, comparison} & set(variables):
        raise ValueError("generated unique-gcd binder captures an argument")
    chosen_relation = is_gcd(
        chosen,
        left,
        right,
        tag=f"{safe_tag}_chosen_relation",
    )
    compared_relation = is_gcd(
        comparison,
        left,
        right,
        tag=f"{safe_tag}_compared_relation",
    )
    return (
        f"exists {chosen}. (({chosen_relation}) /\\ forall {comparison}. "
        f"({compared_relation}) -> {comparison} = {chosen})"
    )


def make_ha_canonical_gcd_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build totality, functionality, and unique-existence candidates."""

    existence_relation = is_gcd("g", "a", "b", tag="existence")
    functional_left = is_gcd("g", "a", "b", tag="functional_left")
    functional_right = is_gcd("h", "a", "b", tag="functional_right")
    unique_relation = unique_gcd("a", "b", tag="package")

    return (
        spec(
            "canonical_gcd_exists",
            f"forall a b. exists g. ({existence_relation})",
            ("gcd_exists_relational",),
            (
                "intro a",
                "intro b",
                "specialize gcd_exists_relational a",
                "specialize gcd_exists_relational b",
                "exact gcd_exists_relational",
            ),
            "Every pair of naturals has a value satisfying the expanded "
            "relational gcd specification.",
        ),
        spec(
            "canonical_gcd_functional",
            f"forall a b g h. ({functional_left}) -> "
            f"({functional_right}) -> g = h",
            ("is_gcd_unique",),
            (
                "intro a",
                "intro b",
                "intro g",
                "intro h",
                "intro hg",
                "intro hh",
                "specialize is_gcd_unique g",
                "specialize is_gcd_unique h",
                "specialize is_gcd_unique a",
                "specialize is_gcd_unique b",
                "apply is_gcd_unique",
                "exact hg",
                "exact hh",
            ),
            "The expanded relational gcd specification is single-valued.",
        ),
        spec(
            "canonical_gcd_exists_unique",
            f"forall a b. ({unique_relation})",
            ("canonical_gcd_exists", "canonical_gcd_functional"),
            (
                "intro a",
                "intro b",
                f"have hexists : exists g. ({existence_relation})",
                "specialize canonical_gcd_exists a",
                "specialize canonical_gcd_exists b",
                "exact canonical_gcd_exists",
                "cases hexists",
                "exists x",
                "split",
                "exact hexists_witness",
                "intro h",
                "intro hh",
                "specialize canonical_gcd_functional a",
                "specialize canonical_gcd_functional b",
                "specialize canonical_gcd_functional h",
                "specialize canonical_gcd_functional x",
                "apply canonical_gcd_functional",
                "exact hh",
                "exact hexists_witness",
            ),
            "Every pair of naturals has exactly one relational gcd value.",
        ),
    )


__all__ = [
    "is_gcd",
    "make_ha_canonical_gcd_candidate_theorems",
    "unique_gcd",
]
