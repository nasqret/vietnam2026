"""Strict-HA constructor seed for doubled-Cantor pairs and tagged cells.

The relations in this module are the exact base-language expansions selected
by RFC ``HA-K3-PAIR-1``.  The seven candidates deliberately stop at literal
construction, output functionality for fixed components, validity of a
constructed pair, and the zero/successor boundary for one cell.  They do not
claim pair injectivity, decoding, lists, maps, or variable iteration.

Every specification is constructive, dependency-curried, unregistered, and
unadmitted.  No division, remainder, beta coding, CRT, or classical principle
is used.
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


def _tagged_names(
    tag: str,
    roles: tuple[str, ...],
    arguments: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"hpc_{role}_{safe_tag}" for role in roles)
    if set(names) & set(arguments):
        raise ValueError("generated pair/cell binder captures an argument")
    return names


def _pair_polynomial(left: str, right: str) -> str:
    left = _identifier(left, "left component")
    right = _identifier(right, "right component")
    return f"({left} + {right}) * S ({left} + {right}) + ({right} + {right})"


def pair_code(code: str, left: str, right: str) -> str:
    """Expand RFC ``HA-K3-PAIR-D01`` exactly."""

    code = _identifier(code, "pair code")
    return f"{code} = {_pair_polynomial(left, right)}"


def pair_valid(code: str, *, tag: str) -> str:
    """Expand RFC ``HA-K3-PAIR-D02`` hygienically."""

    code = _identifier(code, "pair code")
    left, right = _tagged_names(tag, ("left", "right"), (code,))
    return f"exists {left} {right}. {pair_code(code, left, right)}"


def nil_code(code: str) -> str:
    """Expand RFC ``HA-K3-PAIR-D05`` exactly."""

    code = _identifier(code, "nil code")
    return f"{code} = 0"


def cell(code: str, head: str, tail: str) -> str:
    """Expand RFC ``HA-K3-PAIR-D06`` exactly."""

    code = _identifier(code, "cell code")
    return f"{code} = S ({_pair_polynomial(head, tail)})"


def cell_valid(code: str, *, tag: str) -> str:
    """Expand RFC ``HA-K3-PAIR-D07`` hygienically."""

    code = _identifier(code, "cell code")
    head, tail = _tagged_names(tag, ("head", "tail"), (code,))
    return f"exists {head} {tail}. {cell(code, head, tail)}"


def map_entry(entry: str, key: str, value: str) -> str:
    """Expand RFC ``HA-K3-PAIR-D08`` exactly."""

    entry = _identifier(entry, "map entry code")
    return f"{entry} = {_pair_polynomial(key, value)}"


def make_ha_pair_cell_seed_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the seven literal constructor and zero-boundary candidates."""

    polynomial = _pair_polynomial("left", "right")
    cell_polynomial = _pair_polynomial("head", "tail")

    return (
        spec(
            "pair_code_constructor",
            f"forall left right. exists code. code = {polynomial}",
            (),
            (
                "intro left",
                "intro right",
                f"exists {polynomial}",
                "refl",
            ),
            "The displayed doubled-Cantor polynomial constructs a D01 pair "
            "code for any two components.",
        ),
        spec(
            "pair_code_output_functional",
            f"forall code1 code2 left right. code1 = {polynomial} -> "
            f"code2 = {polynomial} -> code1 = code2",
            (),
            (
                "intro code1",
                "intro code2",
                "intro left",
                "intro right",
                "intro hcode1",
                "intro hcode2",
                f"trans {polynomial}",
                "exact hcode1",
                "symm",
                "exact hcode2",
            ),
            "For fixed components, two D01 output codes are equal.",
        ),
        spec(
            "pair_constructor_valid",
            f"forall left right. exists valid_left valid_right. "
            f"{polynomial} = (valid_left + valid_right) * "
            "S (valid_left + valid_right) + (valid_right + valid_right)",
            (),
            (
                "intro left",
                "intro right",
                "exists left",
                "exists right",
                "refl",
            ),
            "Every literal doubled-Cantor constructor satisfies exact D02 "
            "PairValid with its original components.",
        ),
        spec(
            "cell_constructor",
            f"forall head tail. exists code. code = S ({cell_polynomial})",
            (),
            (
                "intro head",
                "intro tail",
                f"exists S ({cell_polynomial})",
                "refl",
            ),
            "One successor applied to the pair polynomial constructs an "
            "exact D06 cell.",
        ),
        spec(
            "cell_nonzero",
            f"forall code head tail. code = S ({cell_polynomial}) -> "
            "~(code = 0)",
            (),
            (
                "intro code",
                "intro head",
                "intro tail",
                "intro hcell",
                "intro hzero",
                "apply PA1",
                "trans code",
                "symm",
                "exact hcell",
                "exact hzero",
            ),
            "Every exact D06 cell code is nonzero by successor separation.",
        ),
        spec(
            "nil_not_cell",
            f"forall code head tail. code = 0 -> "
            f"code = S ({cell_polynomial}) -> false",
            ("cell_nonzero",),
            (
                "intro code",
                "intro head",
                "intro tail",
                "intro hnil",
                "intro hcell",
                "specialize cell_nonzero code",
                "specialize cell_nonzero head",
                "specialize cell_nonzero tail",
                "apply cell_nonzero",
                "exact hcell",
                "exact hnil",
            ),
            "The exact D05 nil relation and exact D06 cell relation are "
            "disjoint.",
        ),
        spec(
            "map_entry_constructor",
            "forall key value. exists entry. entry = "
            "(key + value) * S (key + value) + (value + value)",
            (),
            (
                "intro key",
                "intro value",
                "exists (key + value) * S (key + value) + (value + value)",
                "refl",
            ),
            "The D08 one-entry relation is constructible by the same "
            "doubled-Cantor polynomial; no finite-map claim is made.",
        ),
    )


__all__ = [
    "cell",
    "cell_valid",
    "make_ha_pair_cell_seed_candidate_theorems",
    "map_entry",
    "nil_code",
    "pair_code",
    "pair_valid",
]
