"""Constructive universal-property interface for relational lcm.

The kernel language has neither an lcm function nor a primitive divisibility
predicate.  This isolated layer expands

``IsLCM(l,a,b)``

to the assertion that ``l`` is a common multiple of ``a`` and ``b`` and
divides every other common multiple.  The candidates expose the structural
API, divisibility and zero/one edge cases, and a product upper bound.  This
module alone does not claim general lcm existence.  The adjacent isolated
``ha_lcm_totality_bridge_candidate`` layer now closes that constructive step,
and the public registry admits the seven reviewed universal-property rows.
The ten convenience and edge-value rows remain isolated candidates.

Every relation occurrence expands to the unchanged first-order language
``{0,S,+,*,=}``.  All rows are constructive and dependency-curried; admission
is controlled explicitly by the public registry rather than by this factory.
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
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def is_lcm(
    lcm: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand IsLCM for identifiers and the reviewed literals zero and one."""

    for value, label in (
        (lcm, "lcm value"),
        (left, "left operand"),
        (right, "right operand"),
    ):
        if value not in {"0", "1"}:
            _identifier(value, label)
    return _expand_is_lcm(lcm, left, right, tag=tag)


def _expand_is_lcm(lcm: str, left: str, right: str, *, tag: str) -> str:
    safe_tag = _identifier(tag, "binder tag")
    names = {
        role: f"hlcm_{role}_{safe_tag}"
        for role in (
            "left_factor",
            "right_factor",
            "common",
            "left_common",
            "right_common",
            "least_factor",
        )
    }
    arguments = {value for value in (lcm, left, right) if value not in {"0", "1"}}
    if len(set(names.values())) != len(names) or set(names.values()) & arguments:
        raise ValueError("generated IsLCM binder captures an argument")

    return (
        f"(((exists {names['left_factor']}. "
        f"{lcm} = {left} * {names['left_factor']}) /\\ "
        f"(exists {names['right_factor']}. "
        f"{lcm} = {right} * {names['right_factor']})) /\\ "
        f"forall {names['common']}. "
        f"(exists {names['left_common']}. "
        f"{names['common']} = {left} * {names['left_common']}) -> "
        f"(exists {names['right_common']}. "
        f"{names['common']} = {right} * {names['right_common']}) -> "
        f"exists {names['least_factor']}. "
        f"{names['common']} = {lcm} * {names['least_factor']})"
    )


def make_ha_relational_lcm_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated relational-lcm structural and edge-case layer."""

    symmetry_source = is_lcm("l", "a", "b", tag="symmetry_source")
    symmetry_target = is_lcm("l", "b", "a", tag="symmetry_target")
    projection_left = is_lcm("l", "a", "b", tag="projection_left")
    projection_right = is_lcm("l", "a", "b", tag="projection_right")
    least_relation = is_lcm("l", "a", "b", tag="least")
    dvd_left_relation = is_lcm("b", "a", "b", tag="dvd_left")
    dvd_right_middle = is_lcm("a", "b", "a", tag="dvd_right_middle")
    dvd_right_relation = is_lcm("a", "a", "b", tag="dvd_right")
    unique_left = is_lcm("l", "a", "b", tag="unique_left")
    unique_right = is_lcm("m", "a", "b", tag="unique_right")
    zero_left_relation = is_lcm("0", "0", "b", tag="zero_left")
    zero_left_middle = is_lcm("0", "b", "0", tag="zero_left_middle")
    zero_right_relation = is_lcm("0", "a", "0", tag="zero_right")
    zero_left_value_relation = is_lcm(
        "l", "0", "b", tag="zero_left_value"
    )
    zero_right_value_relation = is_lcm(
        "l", "a", "0", tag="zero_right_value"
    )
    reflexive_relation = is_lcm("a", "a", "a", tag="reflexive")
    one_left_relation = is_lcm("b", "1", "b", tag="one_left")
    one_right_middle = is_lcm(
        "a", "1", "a", tag="one_right_middle"
    )
    one_right_relation = is_lcm("a", "a", "1", tag="one_right")
    zero_left_unique_chosen = is_lcm(
        "l", "0", "b", tag="zero_left_unique_chosen"
    )
    zero_left_unique_compared = is_lcm(
        "m", "0", "b", tag="zero_left_unique_compared"
    )
    zero_right_unique_chosen = is_lcm(
        "l", "a", "0", tag="zero_right_unique_chosen"
    )
    zero_right_unique_compared = is_lcm(
        "m", "a", "0", tag="zero_right_unique_compared"
    )

    rows = (
        spec(
            "is_lcm_symm",
            f"forall l a b. ({symmetry_source}) -> ({symmetry_target})",
            (),
            (
                "intro l",
                "intro a",
                "intro b",
                "intro h",
                "cases h",
                "cases h_left",
                "split",
                "split",
                "exact h_left_right",
                "exact h_left_left",
                "intro c",
                "intro hbc",
                "intro hac",
                "specialize h_right c",
                "apply h_right",
                "exact hac",
                "exact hbc",
            ),
            "The expanded relational lcm specification is symmetric.",
        ),
        spec(
            "is_lcm_multiple_left",
            f"forall l a b. ({projection_left}) -> exists x. l = a * x",
            (),
            (
                "intro l",
                "intro a",
                "intro b",
                "intro h",
                "cases h",
                "cases h_left",
                "exact h_left_left",
            ),
            "A relational lcm is a multiple of its left input.",
        ),
        spec(
            "is_lcm_multiple_right",
            f"forall l a b. ({projection_right}) -> exists x. l = b * x",
            (),
            (
                "intro l",
                "intro a",
                "intro b",
                "intro h",
                "cases h",
                "cases h_left",
                "exact h_left_right",
            ),
            "A relational lcm is a multiple of its right input.",
        ),
        spec(
            "is_lcm_least",
            f"forall l a b c. ({least_relation}) -> "
            "(exists x. c = a * x) -> (exists y. c = b * y) -> "
            "exists z. c = l * z",
            (),
            (
                "intro l",
                "intro a",
                "intro b",
                "intro c",
                "intro h",
                "intro ha",
                "intro hb",
                "cases h",
                "specialize h_right c",
                "apply h_right",
                "exact ha",
                "exact hb",
            ),
            "A relational lcm divides every common multiple.",
        ),
        spec(
            "is_lcm_of_dvd",
            f"forall a b. (exists q. b = a * q) -> ({dvd_left_relation})",
            ("multiple_refl",),
            (
                "intro a",
                "intro b",
                "intro hab",
                "split",
                "split",
                "exact hab",
                "specialize multiple_refl b",
                "exact multiple_refl",
                "intro c",
                "intro hca",
                "intro hcb",
                "exact hcb",
            ),
            "If the left input divides the right, the right input is an lcm.",
        ),
        spec(
            "is_lcm_of_dvd_right",
            f"forall a b. (exists q. a = b * q) -> ({dvd_right_relation})",
            ("is_lcm_of_dvd", "is_lcm_symm"),
            (
                "intro a",
                "intro b",
                "intro hba",
                f"have h : ({dvd_right_middle})",
                "specialize is_lcm_of_dvd b",
                "specialize is_lcm_of_dvd a",
                "apply is_lcm_of_dvd",
                "exact hba",
                "specialize is_lcm_symm a",
                "specialize is_lcm_symm b",
                "specialize is_lcm_symm a",
                "apply is_lcm_symm",
                "exact h",
            ),
            "If the right input divides the left, the left input is an lcm.",
        ),
        spec(
            "product_common_multiple",
            "forall a b. ((exists x. a * b = a * x) /\\ "
            "(exists y. a * b = b * y))",
            ("right_factor_divides_product",),
            (
                "intro a",
                "intro b",
                "split",
                "exists b",
                "refl",
                "specialize right_factor_divides_product a",
                "specialize right_factor_divides_product b",
                "exact right_factor_divides_product",
            ),
            "The product is a common-multiple upper bound for its factors.",
        ),
        spec(
            "is_lcm_unique",
            f"forall l m a b. ({unique_left}) -> ({unique_right}) -> l = m",
            ("multiple_antisymm",),
            (
                "intro l",
                "intro m",
                "intro a",
                "intro b",
                "intro hl",
                "intro hm",
                "cases hl",
                "cases hl_left",
                "cases hm",
                "cases hm_left",
                "have hlm : exists q. m = l * q",
                "specialize hl_right m",
                "apply hl_right",
                "exact hm_left_left",
                "exact hm_left_right",
                "have hml : exists q. l = m * q",
                "specialize hm_right l",
                "apply hm_right",
                "exact hl_left_left",
                "exact hl_left_right",
                "specialize multiple_antisymm l",
                "specialize multiple_antisymm m",
                "apply multiple_antisymm",
                "exact hlm",
                "exact hml",
            ),
            "The expanded relational lcm specification is single-valued.",
        ),
        spec(
            "is_lcm_zero_left",
            f"forall b. ({zero_left_relation})",
            ("is_lcm_zero_right", "is_lcm_symm"),
            (
                "intro b",
                f"have h : ({zero_left_middle})",
                "specialize is_lcm_zero_right b",
                "exact is_lcm_zero_right",
                "specialize is_lcm_symm 0",
                "specialize is_lcm_symm b",
                "specialize is_lcm_symm 0",
                "apply is_lcm_symm",
                "exact h",
            ),
            "Zero is an lcm of zero and every natural.",
        ),
        spec(
            "is_lcm_zero_right",
            f"forall a. ({zero_right_relation})",
            ("multiple_zero",),
            (
                "intro a",
                "split",
                "split",
                "specialize multiple_zero a",
                "exact multiple_zero",
                "specialize multiple_zero 0",
                "exact multiple_zero",
                "intro c",
                "intro hca",
                "intro hc0",
                "exact hc0",
            ),
            "Zero is an lcm of every natural and zero.",
        ),
        spec(
            "lcm_zero_left_value",
            f"forall l b. ({zero_left_value_relation}) -> l = 0",
            ("is_lcm_zero_left", "is_lcm_unique"),
            (
                "intro l",
                "intro b",
                "intro h",
                "specialize is_lcm_zero_left b",
                "specialize is_lcm_unique l",
                "specialize is_lcm_unique 0",
                "specialize is_lcm_unique 0",
                "specialize is_lcm_unique b",
                "apply is_lcm_unique",
                "exact h",
                "exact is_lcm_zero_left",
            ),
            "Every relational lcm of zero and a natural equals zero.",
        ),
        spec(
            "lcm_zero_right_value",
            f"forall l a. ({zero_right_value_relation}) -> l = 0",
            ("is_lcm_zero_right", "is_lcm_unique"),
            (
                "intro l",
                "intro a",
                "intro h",
                "specialize is_lcm_zero_right a",
                "specialize is_lcm_unique l",
                "specialize is_lcm_unique 0",
                "specialize is_lcm_unique a",
                "specialize is_lcm_unique 0",
                "apply is_lcm_unique",
                "exact h",
                "exact is_lcm_zero_right",
            ),
            "Every relational lcm of a natural and zero equals zero.",
        ),
        spec(
            "is_lcm_refl",
            f"forall a. ({reflexive_relation})",
            ("multiple_refl", "is_lcm_of_dvd"),
            (
                "intro a",
                "have h : exists q. a = a * q",
                "specialize multiple_refl a",
                "exact multiple_refl",
                "specialize is_lcm_of_dvd a",
                "specialize is_lcm_of_dvd a",
                "apply is_lcm_of_dvd",
                "exact h",
            ),
            "Every natural is a relational lcm of itself with itself.",
        ),
        spec(
            "is_lcm_one_left",
            f"forall b. ({one_left_relation})",
            ("one_multiple", "is_lcm_of_dvd"),
            (
                "intro b",
                "have h : exists q. b = 1 * q",
                "specialize one_multiple b",
                "exact one_multiple",
                "specialize is_lcm_of_dvd 1",
                "specialize is_lcm_of_dvd b",
                "apply is_lcm_of_dvd",
                "exact h",
            ),
            "Every natural is a relational lcm of one and itself.",
        ),
        spec(
            "is_lcm_one_right",
            f"forall a. ({one_right_relation})",
            ("is_lcm_one_left", "is_lcm_symm"),
            (
                "intro a",
                f"have h : ({one_right_middle})",
                "specialize is_lcm_one_left a",
                "exact is_lcm_one_left",
                "specialize is_lcm_symm a",
                "specialize is_lcm_symm 1",
                "specialize is_lcm_symm a",
                "apply is_lcm_symm",
                "exact h",
            ),
            "Every natural is a relational lcm of itself and one.",
        ),
        spec(
            "lcm_zero_left_exists_unique",
            f"forall b. exists l. (({zero_left_unique_chosen}) "
            f"/\\ forall m. ({zero_left_unique_compared}) -> m = l)",
            ("is_lcm_zero_left", "is_lcm_unique"),
            (
                "intro b",
                "exists 0",
                "split",
                "specialize is_lcm_zero_left b",
                "exact is_lcm_zero_left",
                "intro m",
                "intro hm",
                "specialize is_lcm_unique m",
                "specialize is_lcm_unique 0",
                "specialize is_lcm_unique 0",
                "specialize is_lcm_unique b",
                "apply is_lcm_unique",
                "exact hm",
                "specialize is_lcm_zero_left b",
                "exact is_lcm_zero_left",
            ),
            "Zero and a natural have the unique relational lcm value zero.",
        ),
        spec(
            "lcm_zero_right_exists_unique",
            f"forall a. exists l. (({zero_right_unique_chosen}) "
            f"/\\ forall m. ({zero_right_unique_compared}) -> m = l)",
            ("is_lcm_zero_right", "is_lcm_unique"),
            (
                "intro a",
                "exists 0",
                "split",
                "specialize is_lcm_zero_right a",
                "exact is_lcm_zero_right",
                "intro m",
                "intro hm",
                "specialize is_lcm_unique m",
                "specialize is_lcm_unique 0",
                "specialize is_lcm_unique a",
                "specialize is_lcm_unique 0",
                "apply is_lcm_unique",
                "exact hm",
                "specialize is_lcm_zero_right a",
                "exact is_lcm_zero_right",
            ),
            "A natural and zero have the unique relational lcm value zero.",
        ),
    )

    by_name = {row.name: row for row in rows}
    order = (
        "is_lcm_multiple_left",
        "is_lcm_multiple_right",
        "is_lcm_least",
        "is_lcm_symm",
        "is_lcm_unique",
        "is_lcm_zero_right",
        "is_lcm_zero_left",
        "is_lcm_of_dvd",
        "is_lcm_of_dvd_right",
        "product_common_multiple",
        "is_lcm_refl",
        "is_lcm_one_left",
        "is_lcm_one_right",
        "lcm_zero_left_value",
        "lcm_zero_right_value",
        "lcm_zero_left_exists_unique",
        "lcm_zero_right_exists_unique",
    )
    return tuple(by_name[name] for name in order)


__all__ = ["is_lcm", "make_ha_relational_lcm_candidate_theorems"]
