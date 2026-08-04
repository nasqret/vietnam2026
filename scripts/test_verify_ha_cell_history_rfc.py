"""Lightweight structural audit for RFC HA-K3B-CELLHISTORY-1.

This test imports only the three surface-expansion helpers.  It deliberately
does not construct theorem specifications, replay tactics, close certificates,
or inspect the public theorem registry.
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
from peano_lab.library.ha_cell_history_candidate import (  # noqa: E402
    beta_at,
    cell_history,
    cell_list_len,
)


RFC_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "arithmetic-library"
    / "ha-cell-history-rfc-v1.md"
)

EXPECTED_EXPANSIONS = {
    "BetaAt(b,c,i,x)": {
        "surface": lambda: beta_at("b", "c", "i", "x", tag="rfc_v1"),
        "characters": 172,
        "formula_constructors": 5,
        "ast_nodes": 24,
        "sha256":
            "17706704196c2088288197f9d1a1bbd9c692e863f29a2e9a01abdb1252c3d243",
        "free_names": {"b", "c", "i", "x"},
    },
    "CellHistory(z,l;b,c)": {
        "surface": lambda: cell_history(
            "z", "l", "b", "c", tag="rfc_v1"
        ),
        "characters": 1_278,
        "formula_constructors": 32,
        "ast_nodes": 129,
        "sha256":
            "3bd6cd64446b6acec60b2106296d12fbafe781e9caa61246835ebfb8315b6e0b",
        "free_names": {"z", "l", "b", "c"},
    },
    "CellListLen(z,l)": {
        "surface": lambda: cell_list_len("z", "l", tag="rfc_v1"),
        "characters": 1_885,
        "formula_constructors": 34,
        "ast_nodes": 131,
        "sha256":
            "662411fc848c5f8e5daf438fd72fa195fba44d8301f448d9be750ab016bcc026",
        "free_names": {"z", "l"},
    },
}

EXPECTED_DELIVERABLES = (
    "CellHistory",
    "CellListLen",
    "cell_history_nil",
    "cell_history_extend",
    "cell_history_succ_elim",
    "cell_list_zero_iff_nil",
    "cell_list_succ_iff_cell",
    "cell_list_length_functional",
    "cell_list_length_le_code",
    "cell_list_length_total",
)


def _walk_pa_ast(node: Formula | Term):
    """Yield formula and term constructors without invoking kernel checking."""

    yield node
    for field in fields(node):
        child = getattr(node, field.name)
        if isinstance(child, (Formula, Term)):
            yield from _walk_pa_ast(child)


def _normalized(source: str) -> str:
    return " ".join(source.split())


def test_rfc_exists_and_freezes_the_k3b_boundary() -> None:
    assert RFC_PATH.is_file()
    source = RFC_PATH.read_text(encoding="utf-8")
    normalized = _normalized(source)

    assert "# RFC HA-K3B-CELLHISTORY-1" in source
    assert "**Layer:** `K3B`, a post-K4/M3 bridge; **not** part of strict K3" in source
    assert (
        "Strict K3 remains exactly **96 private rows across 21 modules**"
        in normalized
    )
    assert "Strict K3 still reports exactly 96 rows across 21 modules" in source
    assert "private proof work only; no public admission" in normalized


def test_canonical_helpers_match_frozen_hash_ast_and_free_name_receipts() -> None:
    source = RFC_PATH.read_text(encoding="utf-8")

    for label, expected in EXPECTED_EXPANSIONS.items():
        surface = expected["surface"]()
        formula, free_names = parse_formula_with_names(surface)
        nodes = tuple(_walk_pa_ast(formula))

        assert len(surface) == expected["characters"]
        assert sha256(surface.encode("utf-8")).hexdigest() == expected["sha256"]
        assert sum(isinstance(node, Formula) for node in nodes) == expected[
            "formula_constructors"
        ]
        assert len(nodes) == expected["ast_nodes"]
        assert len(free_names) == len(expected["free_names"])
        assert set(free_names) == expected["free_names"]

        receipt = (
            f"| `{label}` | {expected['characters']:,} | "
            f"{expected['formula_constructors']} | {expected['ast_nodes']} | "
            f"`{expected['sha256']}` |"
        )
        assert receipt in source


def test_reverse_edge_and_native_implication_contracts_are_frozen() -> None:
    source = RFC_PATH.read_text(encoding="utf-8")
    history = cell_history("z", "l", "b", "c", tag="rfc_v1")

    index = "hch_index_rfc_v1"
    gap = "hch_gap_rfc_v1"
    tail = "hch_tail_rfc_v1"
    successor = "hch_successor_rfc_v1"
    head = "hch_head_rfc_v1"
    assert (
        f"forall {index}. (exists {gap}. {gap} + S {index} = l) -> "
        f"exists {tail} {successor} {head}."
    ) in history
    assert f"S ((S ({index})) * c)" in history
    assert f"S ((S (S {index})) * c)" in history
    assert (
        f"{successor} = S (({head} + {tail}) * "
        f"S ({head} + {tail}) + ({tail} + {tail}))"
    ) in history
    assert (
        f"{tail} = S (({head} + {successor}) * "
        f"S ({head} + {successor})"
    ) not in history

    successor_contract = re.search(
        r"The exact contract for deliverable 7 is\s*```text\n(.*?)\n```",
        source,
        flags=re.DOTALL,
    )
    total_contract = re.search(
        r"The exact contract for deliverable 10 is\s*```text\n(.*?)\n```",
        source,
        flags=re.DOTALL,
    )
    assert successor_contract is not None
    assert total_contract is not None
    assert "<->" not in successor_contract.group(1)
    assert "<->" not in total_contract.group(1)
    assert "->" in successor_contract.group(1)
    assert "/\\" in successor_contract.group(1)
    assert total_contract.group(1).strip() == (
        "forall l. exists z. CellListLen(z,l)"
    )
    assert "accepts no `<->` syntax" in source


def test_first_ten_order_firewall_and_private_status_are_explicit() -> None:
    source = RFC_PATH.read_text(encoding="utf-8")
    section = source.split("## 4. The first ten deliverables", 1)[1].split(
        "## 5. Expected proof architecture", 1
    )[0]
    observed = tuple(
        re.findall(r"^\|\s*\d+\s*\|\s*`([^`]+)`", section, flags=re.MULTILINE)
    )
    assert observed == EXPECTED_DELIVERABLES

    forbidden = source.split("### 6.2 Forbidden dependencies", 1)[1].split(
        "## 7. Admission gates", 1
    )[0]
    for marker in (
        "`List`, `ListAt`, `Map`",
        "`Product`, `Sum`, `Range`, `Repeat`, or finite-fold theorem",
        "M4 finite CRT",
        "factorization, FTA, Wilson, Fermat, Euler, Gauss",
        "quadratic-reciprocity",
        "external list type",
        "host-language recursion presented as a proof",
        "unchecked `%`/division computation",
        "raw equality of beta codes",
        "`DNE`",
        "choice, sorry, admission, or a trusted solver result",
    ):
        assert marker in forbidden

    normalized = _normalized(source)
    assert (
        "Public admission, if desired, is a separate reviewed commit with explicit "
        "registry, catalog, snapshot, Book, and explorer receipts."
    ) in normalized
    assert "Until G7 is recorded, these remain private candidates." in normalized
    assert (
        "A closed seed theorem does not imply that lists, lookup, folds, or "
        "finite CRT have been admitted."
    ) in normalized
