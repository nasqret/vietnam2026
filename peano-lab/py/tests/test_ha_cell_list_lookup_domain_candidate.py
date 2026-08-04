"""Focused body audit for the private K3B ``list_at_domain`` projection."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, Proof
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_cell_list_lookup_domain_candidate import (
    make_ha_cell_list_lookup_domain_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _primitive


EXPECTED_NAME = "list_at_domain"
EXPECTED_STATEMENT_RECEIPT = (
    5_903,
    "065291362205b70ef41fff597d1d8762bff06ce7d3a5bead5dbcd8b97ea8a240",
)
EXPECTED_BODY_RECEIPT = (0, 19, 39, 23, 39, 38, 0)


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (item,) = make_ha_cell_list_lookup_domain_candidate_theorems(TheoremSpec)
    return item


def _body_certificate(statement: str | None = None) -> tuple[Proof, object]:
    item = _candidate_spec()
    target = _closed_formula(item.statement if statement is None else statement)
    state = start(target)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_unique(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(_proof_children(node))


def _beta(code: int, scale: int, index: int, value: int) -> bool:
    modulus = 1 + (index + 1) * scale
    return value < modulus and code % modulus == value


def _cell(head: int, tail: int) -> int:
    shell = head + tail
    return 1 + shell * (shell + 1) + 2 * tail


def _history(values: tuple[int, ...], code: int, scale: int) -> bool:
    return (
        values[0] == 0
        and _beta(code, scale, 0, 0)
        and _beta(code, scale, len(values) - 1, values[-1])
        and all(
            any(
                values[index + 1] == _cell(head, values[index])
                for head in range(values[index + 1] + 1)
            )
            for index in range(len(values) - 1)
        )
    )


def _lookup(
    values: tuple[int, ...],
    code: int,
    scale: int,
    outer_index: int,
    value: int,
) -> bool:
    length = len(values) - 1
    return _history(values, code, scale) and any(
        edge + outer_index + 1 == length
        and _beta(code, scale, edge, values[edge])
        and _beta(code, scale, edge + 1, values[edge + 1])
        and values[edge + 1] == _cell(value, values[edge])
        for edge in range(length)
    )


def test_list_at_domain_surface_is_exact_closed_and_private() -> None:
    item = _candidate_spec()
    assert make_ha_cell_list_lookup_domain_candidate_theorems(
        TheoremSpec
    ) == (item,)
    assert item.name == EXPECTED_NAME
    assert item.dependencies == ()
    assert (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
    ) == EXPECTED_STATEMENT_RECEIPT

    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement) == _closed_formula(
        item.statement
    )
    assert all(
        token not in item.statement
        for token in (
            "BetaAt(",
            "Cell(",
            "CellHistory(",
            "CellListLen(",
            "ListAt(",
            "%",
            "<",
        )
    )
    assert item.statement.startswith("forall z i a.")
    assert item.statement.count("exists l.") == 1
    assert item.statement.count("exists k. k + S i = l") == 1
    assert item.script.count("exists x") == 1
    assert item.script.count("exists x3") == 1

    registry_source = (
        Path(__file__).parents[1]
        / "peano_lab"
        / "library"
        / "theorems.py"
    ).read_text(encoding="utf-8")
    assert "ha_cell_list_lookup_domain_candidate" not in registry_source
    assert f'"{item.name}"' not in registry_source


def test_list_at_domain_body_is_pinned_dne_free_and_mutation_sensitive() -> None:
    item = _candidate_spec()
    (receipt,) = replay_candidate_bodies((item,), core={})
    assert (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    ) == EXPECTED_BODY_RECEIPT

    certificate, target = _body_certificate()
    assert check((), certificate, target)
    assert not any(type(node) is DNE for node in _walk_unique(certificate))
    assert not any(type(node) is Cut for node in _walk_unique(certificate))
    assert {
        command.split(maxsplit=1)[0] for command in item.script
    } <= {"intro", "cases", "exists", "split", "exact"}

    old = "exists k. k + S i = l"
    new = "exists k. k + S (S i) = l"
    assert item.statement.count(old) == 1
    mutated = item.statement.replace(old, new)
    assert not check((), certificate, _closed_formula(mutated))


def test_list_at_domain_small_model_returns_length_and_native_bound() -> None:
    # Distinct-head reverse trace 0 -> Cell(1,0)=3 -> Cell(0,3)=19,
    # encoded as residues 0,3,19 modulo 9,17,25 by (code,scale)=(819,8).
    values = (0, 3, 19)
    assert _history(values, 819, 8)
    length = 2
    for outer_index, head, edge in ((0, 0, 1), (1, 1, 0)):
        assert _lookup(values, 819, 8, outer_index, head)
        assert edge + outer_index + 1 == length
    assert not _lookup(values, 819, 8, 0, 1)
    assert not _lookup(values, 819, 8, 1, 0)
    assert not _lookup(values, 819, 8, 2, 0)
