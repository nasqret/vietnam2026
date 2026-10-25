r"""Private hygienic ``ListAt`` surface for reverse exact-D06 cell histories.

This module is an authoring prototype only.  ``cell_list_at(z,i,a)`` expands
immediately to the unchanged first-order Peano language; it introduces no
kernel predicate, theorem row, registry entry, or trusted abbreviation.

Histories grow from nil toward the outermost cell.  Consequently the edge at
construction index ``j`` carries outer-head index ``i`` precisely when
``j + S i = l``.  The normative witness order is ``l b c j t u`` and the
payload is right-associated as

``CellHistory /\ (j + S i = l /\ (BetaAt(j,t) /\ (BetaAt(S j,u) /\ Cell(u,a,t))))``.
"""

from __future__ import annotations

from peano_lab.library.ha_cell_history_candidate import beta_at, cell_history


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


def _lookup_binders(
    tag: str,
    avoid: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    roles = (
        "length",
        "trace_code",
        "trace_scale",
        "edge",
        "tail",
        "successor",
    )
    names = tuple(f"hclook_{role}_{safe_tag}" for role in roles)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated cell-list lookup binder captures an argument")
    return names


def _all_internal_binders(tag: str) -> tuple[str, ...]:
    """List every subordinate binder that could shadow a caller identifier."""

    history_tag = f"{tag}_history"
    names = [
        f"hch_{role}_{history_tag}"
        for role in (
            "index",
            "gap",
            "tail",
            "successor",
            "head",
        )
    ]
    for beta_tag in (
        f"{history_tag}_start",
        f"{history_tag}_terminal",
        f"{history_tag}_current",
        f"{history_tag}_following",
        f"{tag}_current",
        f"{tag}_following",
    ):
        names.extend(
            (
                f"hch_beta_height_{beta_tag}",
                f"hch_beta_quotient_{beta_tag}",
            )
        )
    return tuple(names)


def _beta_at_successor(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand ``BetaAt(code,scale,S index,value)`` without term macros."""

    placeholder = f"hclook_following_index_argument_{tag}"
    # All supplied names have already been validated and use disjoint role
    # prefixes, so the placeholder is a fresh free identifier in this local
    # expansion.  It disappears before the enclosing formula is parsed.
    expanded = beta_at(code, scale, placeholder, value, tag=f"{tag}_following")
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("successor-index placeholder disappeared")
    return expanded.replace(placeholder, f"S {index}")


def cell_list_at(
    code: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Fully expand outer-head lookup in a beta-backed reverse cell history.

    The arguments must be identifiers.  Generated existential and subordinate
    binders are checked against all three caller names, making expansion
    deterministic and capture rejecting before the formula parser runs.
    """

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "terminal cell code"),
            (index, "outer-head index"),
            (value, "selected head"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    binders = _lookup_binders(safe_tag, variables)
    internal = _all_internal_binders(safe_tag)
    if set(variables) & set(internal):
        raise ValueError("generated lookup helper binder captures an argument")

    length, trace_code, trace_scale, edge, tail, successor = binders
    history = cell_history(
        code,
        length,
        trace_code,
        trace_scale,
        tag=f"{safe_tag}_history",
    )
    current = beta_at(
        trace_code,
        trace_scale,
        edge,
        tail,
        tag=f"{safe_tag}_current",
    )
    following = _beta_at_successor(
        trace_code,
        trace_scale,
        edge,
        successor,
        tag=safe_tag,
    )
    exact_cell = (
        f"{successor} = S (({value} + {tail}) * "
        f"S ({value} + {tail}) + ({tail} + {tail}))"
    )
    return (
        f"exists {length} {trace_code} {trace_scale} {edge} {tail} {successor}. "
        f"(({history}) /\\ ({edge} + S {index} = {length} /\\ "
        f"(({current}) /\\ (({following}) /\\ ({exact_cell})))))"
    )


__all__ = ["cell_list_at"]
