"""K4 boundary laws for the canonical relational-gcd interface.

The public arithmetic library already contains the constructor
``IsGCD(a,a,0)`` and one-way symmetry of ``IsGCD``.  This isolated layer does
not duplicate those facts.  Instead it turns the zero and one boundary cases
into equality characterizations and exposes the function-style consequence
of symmetry for independently chosen relational gcd witnesses.

The kernel language still has no gcd function.  Every occurrence of
``IsGCD`` below is expanded to ``{0,S,+,*,=}``; the helper accepts only
identifiers and the two reviewed boundary literals ``0`` and ``1``.  All
candidates remain dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable


_RESERVED = {"S", "bot", "exists", "false", "forall"}
_BOUNDARY_LITERALS = {"0", "1"}


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


def _edge_operand(value: str, label: str) -> str:
    if value in _BOUNDARY_LITERALS:
        return value
    return _identifier(value, label)


def edge_is_gcd(
    gcd: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand ``IsGCD(gcd,left,right)`` at an identifier/0/1 boundary.

    The general canonical-gcd helper intentionally accepts identifiers only.
    This narrower companion admits exactly the constants needed by the edge
    API, rather than interpolating arbitrary unparsed term strings.
    """

    gcd = _identifier(gcd, "gcd value")
    left = _edge_operand(left, "left operand")
    right = _edge_operand(right, "right operand")
    safe_tag = _identifier(tag, "binder tag")
    binders = tuple(
        f"hage_{stem}_{safe_tag}"
        for stem in (
            "left_factor",
            "right_factor",
            "divisor",
            "common_left",
            "common_right",
            "greatest_factor",
        )
    )
    free_identifiers = {
        value
        for value in (gcd, left, right)
        if value not in _BOUNDARY_LITERALS
    }
    if len(set(binders)) != len(binders) or set(binders) & free_identifiers:
        raise ValueError("generated edge-IsGCD binder captures an argument")
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
        f"(exists {common_right}. "
        f"{right} = {divisor} * {common_right}) -> "
        f"exists {greatest_factor}. "
        f"{gcd} = {divisor} * {greatest_factor})"
    )


def make_ha_canonical_gcd_edges_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the five nonredundant canonical-gcd boundary candidates."""

    zero_right_assumption = edge_is_gcd(
        "g", "a", "0", tag="zero_right_assumption"
    )
    zero_right_result = edge_is_gcd(
        "g", "a", "0", tag="zero_right_result"
    )
    zero_left_assumption = edge_is_gcd(
        "g", "0", "a", tag="zero_left_assumption"
    )
    zero_left_result = edge_is_gcd(
        "g", "0", "a", tag="zero_left_result"
    )
    one_left_assumption = edge_is_gcd(
        "g", "1", "a", tag="one_left_assumption"
    )
    one_left_result = edge_is_gcd(
        "g", "1", "a", tag="one_left_result"
    )
    one_right_assumption = edge_is_gcd(
        "g", "a", "1", tag="one_right_assumption"
    )
    one_right_result = edge_is_gcd(
        "g", "a", "1", tag="one_right_result"
    )
    swap_left = edge_is_gcd("g", "a", "b", tag="swap_left")
    swap_right = edge_is_gcd("h", "b", "a", tag="swap_right")

    return (
        spec(
            "canonical_gcd_zero_right_iff",
            f"forall a g. (({zero_right_assumption}) -> g = a) /\\ "
            f"(g = a -> ({zero_right_result}))",
            ("is_gcd_zero_right", "canonical_gcd_functional"),
            (
                "intro a",
                "intro g",
                "split",
                "intro hg",
                "specialize canonical_gcd_functional a",
                "specialize canonical_gcd_functional 0",
                "specialize canonical_gcd_functional g",
                "specialize canonical_gcd_functional a",
                "apply canonical_gcd_functional",
                "exact hg",
                "specialize is_gcd_zero_right a",
                "exact is_gcd_zero_right",
                "intro h",
                "rewrite h",
                "rewrite h",
                "rewrite h",
                "specialize is_gcd_zero_right a",
                "exact is_gcd_zero_right",
            ),
            "A relational gcd of a and zero is exactly a, in both directions.",
        ),
        spec(
            "canonical_gcd_zero_left_iff",
            f"forall a g. (({zero_left_assumption}) -> g = a) /\\ "
            f"(g = a -> ({zero_left_result}))",
            ("is_gcd_symm", "canonical_gcd_zero_right_iff"),
            (
                "intro a",
                "intro g",
                "split",
                "intro hg",
                "have hright : "
                f"({edge_is_gcd('g', 'a', '0', tag='zero_left_as_right')})",
                "specialize is_gcd_symm g",
                "specialize is_gcd_symm 0",
                "specialize is_gcd_symm a",
                "apply is_gcd_symm",
                "exact hg",
                "specialize canonical_gcd_zero_right_iff a",
                "specialize canonical_gcd_zero_right_iff g",
                "cases canonical_gcd_zero_right_iff",
                "apply canonical_gcd_zero_right_iff_left",
                "exact hright",
                "intro h",
                "rewrite h",
                "rewrite h",
                "rewrite h",
                "have hright : "
                f"({edge_is_gcd('a', 'a', '0', tag='zero_left_base')})",
                "specialize canonical_gcd_zero_right_iff a",
                "specialize canonical_gcd_zero_right_iff a",
                "cases canonical_gcd_zero_right_iff",
                "apply canonical_gcd_zero_right_iff_right",
                "refl",
                "specialize is_gcd_symm a",
                "specialize is_gcd_symm a",
                "specialize is_gcd_symm 0",
                "apply is_gcd_symm",
                "exact hright",
            ),
            "A relational gcd of zero and a is exactly a, in both directions.",
        ),
        spec(
            "canonical_gcd_one_left_iff",
            f"forall a g. (({one_left_assumption}) -> g = 1) /\\ "
            f"(g = 1 -> ({one_left_result}))",
            (
                "is_gcd_dvd_left",
                "divisor_one",
                "one_multiple",
                "is_gcd_of_dvd",
            ),
            (
                "intro a",
                "intro g",
                "split",
                "intro hg",
                "have hd : exists x. 1 = g * x",
                "specialize is_gcd_dvd_left g",
                "specialize is_gcd_dvd_left 1",
                "specialize is_gcd_dvd_left a",
                "apply is_gcd_dvd_left",
                "exact hg",
                "specialize divisor_one g",
                "apply divisor_one",
                "exact hd",
                "intro h",
                "rewrite h",
                "rewrite h",
                "rewrite h",
                "have hd : exists q. a = 1 * q",
                "specialize one_multiple a",
                "exact one_multiple",
                "specialize is_gcd_of_dvd 1",
                "specialize is_gcd_of_dvd a",
                "apply is_gcd_of_dvd",
                "exact hd",
            ),
            "A relational gcd of one and a is exactly one, in both directions.",
        ),
        spec(
            "canonical_gcd_one_right_iff",
            f"forall a g. (({one_right_assumption}) -> g = 1) /\\ "
            f"(g = 1 -> ({one_right_result}))",
            ("is_gcd_symm", "canonical_gcd_one_left_iff"),
            (
                "intro a",
                "intro g",
                "split",
                "intro hg",
                "have hleft : "
                f"({edge_is_gcd('g', '1', 'a', tag='one_right_as_left')})",
                "specialize is_gcd_symm g",
                "specialize is_gcd_symm a",
                "specialize is_gcd_symm 1",
                "apply is_gcd_symm",
                "exact hg",
                "specialize canonical_gcd_one_left_iff a",
                "specialize canonical_gcd_one_left_iff g",
                "cases canonical_gcd_one_left_iff",
                "apply canonical_gcd_one_left_iff_left",
                "exact hleft",
                "intro h",
                "have hleft : "
                f"({edge_is_gcd('g', '1', 'a', tag='one_right_base')})",
                "specialize canonical_gcd_one_left_iff a",
                "specialize canonical_gcd_one_left_iff g",
                "cases canonical_gcd_one_left_iff",
                "apply canonical_gcd_one_left_iff_right",
                "exact h",
                "specialize is_gcd_symm g",
                "specialize is_gcd_symm 1",
                "specialize is_gcd_symm a",
                "apply is_gcd_symm",
                "exact hleft",
            ),
            "A relational gcd of a and one is exactly one, in both directions.",
        ),
        spec(
            "canonical_gcd_swap_functional",
            f"forall a b g h. ({swap_left}) -> ({swap_right}) -> g = h",
            ("is_gcd_symm", "canonical_gcd_functional"),
            (
                "intro a",
                "intro b",
                "intro g",
                "intro h",
                "intro hg",
                "intro hh",
                "have hh_swapped : "
                f"({edge_is_gcd('h', 'a', 'b', tag='swap_right_back')})",
                "specialize is_gcd_symm h",
                "specialize is_gcd_symm b",
                "specialize is_gcd_symm a",
                "apply is_gcd_symm",
                "exact hh",
                "specialize canonical_gcd_functional a",
                "specialize canonical_gcd_functional b",
                "specialize canonical_gcd_functional g",
                "specialize canonical_gcd_functional h",
                "apply canonical_gcd_functional",
                "exact hg",
                "exact hh_swapped",
            ),
            "Relational gcd witnesses for swapped inputs have the same value.",
        ),
    )


__all__ = [
    "edge_is_gcd",
    "make_ha_canonical_gcd_edges_candidate_theorems",
]
