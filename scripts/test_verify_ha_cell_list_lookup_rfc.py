"""Lightweight structural audit for the K3B cell-list lookup RFC.

The audit imports only the private ``ListAt`` surface-expansion helper and the
PA syntax dataclasses.  It deliberately does not build the theorem registry,
replay tactics, close certificates, or perform any unbounded semantic search.
"""

from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
from pathlib import Path
import re
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.kernel.formulas import Formula, parse_formula_with_names  # noqa: E402
from peano_lab.kernel.terms import Term  # noqa: E402
from peano_lab.library.ha_cell_list_lookup_surface_candidate import (  # noqa: E402
    cell_list_at,
)


RFC_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "arithmetic-library"
    / "ha-cell-list-lookup-rfc-v1.md"
)

LIST_AT_RECEIPT = {
    "characters": 3_331,
    "formula_constructors": 54,
    "ast_nodes": 210,
    "sha256":
        "b83d91b6ec8e6b83fe637e1533c72beef54c7e7a4b41f1518bce8785cc9f11ce",
    "free_names": ("z", "i", "a"),
}

EXPECTED_RUNGS = (
    "ListAt",
    "cell_history_extend_preserves_prefix",
    "list_at_domain",
    "list_at_head_iff",
    "list_at_succ_iff",
    "list_at_external_bound",
    "list_at_exists",
    "list_at_functional",
    "list_at_history_independent",
    "cell_list_extensional",
)

EXPECTED_HEAD_CONTRACT = """forall z a.
  ((ListAt(z,0,a) ->
    exists t l. Cell(z,a,t) /\\ CellListLen(t,l)) /\\
   ((exists t l. Cell(z,a,t) /\\ CellListLen(t,l)) ->
    ListAt(z,0,a)))"""

EXPECTED_SUCCESSOR_CONTRACT = """forall z i a.
  ((ListAt(z,S i,a) ->
    exists t h. Cell(z,h,t) /\\ ListAt(t,i,a)) /\\
   ((exists t h. Cell(z,h,t) /\\ ListAt(t,i,a)) ->
    ListAt(z,S i,a)))"""


def _walk_pa_ast(node: Formula | Term):
    """Yield formula and term constructors without kernel checking."""

    yield node
    for field in fields(node):
        child = getattr(node, field.name)
        if isinstance(child, (Formula, Term)):
            yield from _walk_pa_ast(child)


def _normalized(source: str) -> str:
    return " ".join(source.split())


def _numbered_rung_tables(source: str):
    """Return every contiguous Markdown-table run numbered one through ten."""

    rows = tuple(
        (int(number), name, tail)
        for number, name, tail in re.findall(
            r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|(.*)\|\s*$",
            source,
            flags=re.MULTILINE,
        )
    )
    for start in range(max(0, len(rows) - 9)):
        candidate = rows[start : start + 10]
        if tuple(number for number, _, _ in candidate) == tuple(range(1, 11)):
            yield candidate


def _fenced_contract(source: str, needle: str) -> str:
    matches = tuple(
        block
        for block in re.findall(
            r"```text\n(.*?)\n```",
            source,
            flags=re.DOTALL,
        )
        if needle in block
    )
    assert len(matches) == 1, (
        f"expected exactly one fenced contract containing {needle!r}"
    )
    return matches[0]


def test_list_at_surface_matches_the_frozen_receipt() -> None:
    assert RFC_PATH.is_file()
    source = RFC_PATH.read_text(encoding="utf-8")
    expansion = cell_list_at("z", "i", "a", tag="surface_v1")
    formula, free_names = parse_formula_with_names(expansion)
    nodes = tuple(_walk_pa_ast(formula))

    assert len(expansion) == LIST_AT_RECEIPT["characters"]
    assert (
        sum(isinstance(node, Formula) for node in nodes)
        == LIST_AT_RECEIPT["formula_constructors"]
    )
    assert len(nodes) == LIST_AT_RECEIPT["ast_nodes"]
    assert sha256(expansion.encode("utf-8")).hexdigest() == (
        LIST_AT_RECEIPT["sha256"]
    )
    assert free_names == LIST_AT_RECEIPT["free_names"]

    receipt = (
        "| `ListAt(z,i,a)` | 3,331 | 54 | 210 | "
        f"`{LIST_AT_RECEIPT['sha256']}` | `z,i,a` |"
    )
    assert receipt in source


def test_rfc_freezes_the_exact_ten_rung_order_and_definition_boundary() -> None:
    source = RFC_PATH.read_text(encoding="utf-8")
    matching_tables = tuple(
        table
        for table in _numbered_rung_tables(source)
        if tuple(name for _, name, _ in table) == EXPECTED_RUNGS
    )
    assert len(matching_tables) == 1

    first_tail = _normalized(matching_tables[0][0][2]).replace("`", "").lower()
    assert "definition" in first_tail
    ladder_prose = _normalized(source).replace("`", "")
    assert "D02 is a definition, not a theorem row" in ladder_prose


def test_head_and_successor_equivalences_are_native_conjunctions() -> None:
    source = RFC_PATH.read_text(encoding="utf-8")
    head = _fenced_contract(source, "ListAt(z,0,a)")
    successor = _fenced_contract(source, "ListAt(z,S i,a)")

    assert _normalized(head) == _normalized(EXPECTED_HEAD_CONTRACT)
    assert _normalized(successor) == _normalized(EXPECTED_SUCCESSOR_CONTRACT)
    for contract in (head, successor):
        assert contract.count("->") == 2
        assert "/\\" in contract
        assert "<->" not in contract

    prose = _normalized(source).lower()
    assert "conjunctions of implications" in prose
    assert "there is no native `<->`" in prose


def test_rfc_keeps_the_lookup_ladder_private_unregistered_and_unadmitted() -> None:
    source = RFC_PATH.read_text(encoding="utf-8")
    plain = _normalized(source.replace("`", "")).lower()
    assert "every theorem remains private, unregistered, and unadmitted" in plain
