r"""Hygienic K3C validity and membership surfaces for canonical cell lists.

``CellListValid(code)`` means that ``code`` has some represented ``CellListLen``.
``ListMember(code,value)`` means that ``value`` occurs at some outer-head
``ListAt`` index.  Both helpers expand immediately to the unchanged
first-order Peano language and add no kernel predicate or trusted constant.

The surfaces deliberately quantify only the semantic length or lookup index;
the beta-history witnesses remain hidden by the already frozen K3B helpers.
"""

from __future__ import annotations

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at


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


def _binder(tag: str, role: str, avoid: tuple[str, ...]) -> str:
    safe_tag = _identifier(tag, "binder tag")
    name = f"hclist_{role}_{safe_tag}"
    if name in avoid:
        raise ValueError("generated cell-list binder captures an argument")
    return name


def cell_list_valid(code: str, *, tag: str) -> str:
    """Expand ``CellListValid(code) := exists l. CellListLen(code,l)``."""

    safe_code = _identifier(code, "cell-list code")
    safe_tag = _identifier(tag, "binder tag")
    length = _binder(safe_tag, "length", (safe_code,))
    represented = cell_list_len(
        safe_code,
        length,
        tag=f"{safe_tag}_represented_length",
    )
    return f"exists {length}. ({represented})"


def cell_list_member(code: str, value: str, *, tag: str) -> str:
    """Fully expand ``ListMember(code,value) := exists i. ListAt(code,i,value)``."""

    safe_code = _identifier(code, "cell-list code")
    safe_value = _identifier(value, "member value")
    safe_tag = _identifier(tag, "binder tag")
    index = _binder(safe_tag, "member_index", (safe_code, safe_value))
    lookup = cell_list_at(
        safe_code,
        index,
        safe_value,
        tag=f"{safe_tag}_lookup",
    )
    return f"exists {index}. ({lookup})"


__all__ = ["cell_list_member", "cell_list_valid"]
