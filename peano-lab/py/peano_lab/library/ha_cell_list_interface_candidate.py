"""K3C totality, equality, and decomposition interface for canonical lists.

These five rows complement the validity and membership API without adding a
new object-language symbol.  Every ``CellListLen`` and ``ListAt`` occurrence
is expanded before parsing.  The bodies are dependency-curried authoring
evidence; Alpha v2 enrollment and cold closure are separate gates.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def _bound(index: str, length: str) -> str:
    return f"exists k. k + S {index} = {length}"


def _zero_lookup(code: str, value: str, *, tag: str) -> str:
    marker = f"hclistinterface_zero_argument_{tag}"
    expanded = cell_list_at(code, marker, value, tag=tag)
    if expanded.count(marker) == 0:
        raise ValueError("zero-index placeholder disappeared")
    return expanded.replace(marker, "0")


def _successor_length(code: str, predecessor: str, *, tag: str) -> str:
    marker = f"hclistinterface_successor_argument_{tag}"
    expanded = cell_list_len(code, marker, tag=tag)
    if expanded.count(marker) == 0:
        raise ValueError("successor-length placeholder disappeared")
    return expanded.replace(marker, f"S {predecessor}")


def _pointwise(length: str, left: str, right: str, *, tag: str) -> str:
    left_lookup = cell_list_at(left, "i", "a", tag=f"{tag}_left")
    right_lookup = cell_list_at(right, "i", "d", tag=f"{tag}_right")
    return (
        f"forall i a d. ({_bound('i', length)}) -> "
        f"({left_lookup}) -> ({right_lookup}) -> a = d"
    )


def make_ha_cell_list_interface_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered K3C semantic interface."""

    length = cell_list_len("z", "l", tag="interface_unique_length")
    lookup_a = cell_list_at("z", "i", "a", tag="interface_unique_a")
    lookup_d = cell_list_at("z", "i", "d", tag="interface_unique_d")

    nonempty_length = _successor_length(
        "z", "l", tag="interface_nonempty_length"
    )
    nonempty_lookup = _zero_lookup(
        "z", "a", tag="interface_nonempty_lookup"
    )
    nonempty_decomposition = (
        f"exists t h. (({cell('z', 'h', 't')}) /\\ "
        f"({cell_list_len('t', 'x', tag='interface_nonempty_tail')}))"
    )
    head_decomposition = (
        f"exists t l. (({cell('z', 'x', 't')}) /\\ "
        f"({cell_list_len('t', 'l', tag='interface_head_tail')}))"
    )

    equal_left_lookup = cell_list_at(
        "z", "i", "a", tag="interface_equal_left"
    )
    equal_right_lookup = cell_list_at(
        "w", "i", "d", tag="interface_equal_right"
    )

    extensional_left_length = cell_list_len(
        "z", "l", tag="interface_extensional_left_length"
    )
    extensional_right_length = cell_list_len(
        "w", "l", tag="interface_extensional_right_length"
    )
    extensional_pointwise = _pointwise(
        "l", "z", "w", tag="interface_extensional_pointwise"
    )

    decomposition_length = _successor_length(
        "z", "l", tag="interface_decomposition_length"
    )
    decomposition_tail_length = cell_list_len(
        "t", "l", tag="interface_decomposition_tail_length"
    )
    decomposition_cell = cell("z", "h", "t")
    decomposition_other_cell = cell("z", "h2", "t2")

    return (
        spec(
            "list_at_exists_unique",
            "forall z l i. "
            f"({length}) -> ({_bound('i', 'l')}) -> "
            f"exists a. (({lookup_a}) /\\ forall d. ({lookup_d}) -> d = a)",
            ("list_at_exists", "list_at_functional"),
            (
                "intro z",
                "intro l",
                "intro i",
                "intro hlength",
                "intro hbound",
                f"have hexists : exists a. ({lookup_a})",
                "specialize list_at_exists z",
                "specialize list_at_exists l",
                "specialize list_at_exists i",
                "apply list_at_exists",
                "exact hlength",
                "exact hbound",
                "cases hexists",
                "exists x",
                "split",
                "exact hexists_witness",
                "intro d",
                "intro hlookup_d",
                "specialize list_at_functional z",
                "specialize list_at_functional i",
                "specialize list_at_functional d",
                "specialize list_at_functional x",
                "apply list_at_functional",
                "exact hlookup_d",
                "exact hexists_witness",
            ),
            "Every in-range cell-list index has exactly one value.",
        ),
        spec(
            "cell_list_nonempty_iff_head_exists",
            "forall z. (((exists l. ("
            + nonempty_length
            + ")) -> exists a. ("
            + nonempty_lookup
            + ")) /\\ ((exists a. ("
            + nonempty_lookup
            + ")) -> exists l. ("
            + nonempty_length
            + ")))",
            ("list_at_head_iff", "cell_list_succ_iff_cell"),
            (
                "intro z",
                "split",
                "intro hnonempty",
                "cases hnonempty",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell x",
                "cases cell_list_succ_iff_cell",
                f"have hdecomp : {nonempty_decomposition}",
                "apply cell_list_succ_iff_cell_left",
                "exact hnonempty_witness",
                "cases hdecomp",
                "cases hdecomp_witness",
                "exists x2",
                "specialize list_at_head_iff z",
                "specialize list_at_head_iff x2",
                "cases list_at_head_iff",
                "apply list_at_head_iff_right",
                "exists x1",
                "exists x",
                "exact hdecomp_witness_witness",
                "intro hhead",
                "cases hhead",
                "specialize list_at_head_iff z",
                "specialize list_at_head_iff x",
                "cases list_at_head_iff",
                f"have hdecomp : {head_decomposition}",
                "apply list_at_head_iff_left",
                "exact hhead_witness",
                "cases hdecomp",
                "cases hdecomp_witness",
                "exists x2",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell x2",
                "cases cell_list_succ_iff_cell",
                "apply cell_list_succ_iff_cell_right",
                "exists x1",
                "exists x",
                "exact hdecomp_witness_witness",
            ),
            "A represented cell list is nonempty exactly when its head exists.",
        ),
        spec(
            "cell_list_code_eq_lookup_values",
            "forall z w i a d. z = w -> "
            f"({equal_left_lookup}) -> ({equal_right_lookup}) -> a = d",
            ("list_at_functional",),
            (
                "intro z",
                "intro w",
                "intro i",
                "intro a",
                "intro d",
                "intro hcode",
                "intro hleft",
                "intro hright",
                "rewrite hcode at hleft",
                "rewrite hcode at hleft",
                "specialize list_at_functional w",
                "specialize list_at_functional i",
                "specialize list_at_functional a",
                "specialize list_at_functional d",
                "apply list_at_functional",
                "exact hleft",
                "exact hright",
            ),
            "Equal cell-list codes return equal values at every common lookup index.",
        ),
        spec(
            "cell_list_code_eq_iff_pointwise",
            "forall z w l. "
            f"({extensional_left_length}) -> ({extensional_right_length}) -> "
            f"((z = w -> ({extensional_pointwise})) /\\ "
            f"(({extensional_pointwise}) -> z = w))",
            ("cell_list_code_eq_lookup_values", "cell_list_extensional"),
            (
                "intro z",
                "intro w",
                "intro l",
                "intro hleft_length",
                "intro hright_length",
                "split",
                "intro hcode",
                "intro i",
                "intro a",
                "intro d",
                "intro hbound",
                "intro hleft",
                "intro hright",
                "specialize cell_list_code_eq_lookup_values z",
                "specialize cell_list_code_eq_lookup_values w",
                "specialize cell_list_code_eq_lookup_values i",
                "specialize cell_list_code_eq_lookup_values a",
                "specialize cell_list_code_eq_lookup_values d",
                "apply cell_list_code_eq_lookup_values",
                "exact hcode",
                "exact hleft",
                "exact hright",
                "intro hpointwise",
                "specialize cell_list_extensional z",
                "specialize cell_list_extensional w",
                "specialize cell_list_extensional l",
                "apply cell_list_extensional",
                "exact hleft_length",
                "exact hright_length",
                "exact hpointwise",
            ),
            "For equal-length cell lists, code equality is equivalent to pointwise equality.",
        ),
        spec(
            "cell_list_decompose_unique",
            "forall z l. "
            f"({decomposition_length}) -> exists h t. "
            f"(({decomposition_cell}) /\\ (({decomposition_tail_length}) /\\ "
            f"forall h2 t2. ({decomposition_other_cell}) -> "
            "(h2 = h /\\ t2 = t)))",
            ("cell_list_succ_iff_cell", "cell_functional"),
            (
                "intro z",
                "intro l",
                "intro hlength",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell l",
                "cases cell_list_succ_iff_cell",
                "have hdecomp : exists t h. "
                f"(({cell('z', 'h', 't')}) /\\ "
                f"({cell_list_len('t', 'l', tag='interface_decomposition_source')}))",
                "apply cell_list_succ_iff_cell_left",
                "exact hlength",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "exists x1",
                "exists x",
                "split",
                "exact hdecomp_witness_witness_left",
                "split",
                "exact hdecomp_witness_witness_right",
                "intro h2",
                "intro t2",
                "intro hcell",
                "specialize cell_functional z",
                "specialize cell_functional h2",
                "specialize cell_functional t2",
                "specialize cell_functional x1",
                "specialize cell_functional x",
                "apply cell_functional",
                "exact hcell",
                "exact hdecomp_witness_witness_left",
            ),
            "A nonempty represented list has a unique outer-cell decomposition.",
        ),
    )


__all__ = ["make_ha_cell_list_interface_candidate_theorems"]
