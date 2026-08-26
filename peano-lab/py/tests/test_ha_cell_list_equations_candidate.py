"""Focused dependency-curried body audit for the two K3B list equations.

This file intentionally performs no recursive dependency closure, no cold
empty-context replay, and no campaign integration.  It checks only the exact
expanded statement surfaces and the kernel-checked proof bodies with every
declared dependency left as an ordinary hypothesis.
"""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_cell_history_candidate import (
    make_ha_cell_history_candidate_theorems,
)
from peano_lab.library.ha_cell_list_equations_candidate import (
    make_ha_cell_list_equations_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "cell_list_zero_iff_nil",
    "cell_list_succ_iff_cell",
)
EXPECTED_DEPENDENCIES = {
    "cell_list_zero_iff_nil": ("beta_at_unique", "cell_history_nil"),
    "cell_list_succ_iff_cell": (
        "cell_history_succ_elim",
        "cell_history_extend",
    ),
}
EXPECTED_STATEMENT_RECEIPTS = {
    "cell_list_zero_iff_nil": (
        4332,
        "bef9e900318713718a2e981eb04de28fb21e4641ff4f80c2a98b1dc41af2db29",
    ),
    "cell_list_succ_iff_cell": (
        8954,
        "bb678323c7061f561ce69bb0357bf93ece948acf763503eec4763934cf50b23c",
    ),
}
EXPECTED_BODY_RECEIPTS = {
    "cell_list_zero_iff_nil": (2, 24, 33, 16, 33, 32, 0),
    "cell_list_succ_iff_cell": (2, 38, 51, 19, 51, 50, 0),
}
EXACT_CELL = "z = S ((h + t) * S (h + t) + (t + t))"


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_cell_list_equations_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _history_specs() -> dict[str, TheoremSpec]:
    specs = make_ha_cell_history_candidate_theorems(TheoremSpec)
    return {item.name: item for item in specs}


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _history_specs()


def _candidate_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


def _body_certificate(item: TheoremSpec):
    target = _candidate_target(item)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for field in fields(proof)
        if isinstance((child := getattr(proof, field.name)), Proof)
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


def test_cell_list_equation_surfaces_are_exact_closed_and_ordered() -> None:
    specs = _candidate_specs()
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert make_ha_cell_list_equations_candidate_theorems(TheoremSpec) == specs

    for item in specs:
        assert item.dependencies == EXPECTED_DEPENDENCIES[item.name]
        assert (len(item.statement), sha256(item.statement.encode()).hexdigest()) == (
            EXPECTED_STATEMENT_RECEIPTS[item.name]
        )
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert (
            formula
            == parse_formula(item.statement)
            == _closed_formula(item.statement)
        )
        assert "<->" not in item.statement
        assert all(
            macro not in item.statement
            for macro in ("BetaAt(", "Cell(", "CellHistory(", "CellListLen(")
        )
        assert "hcleq_successor_length_argument" not in item.statement

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_list_equations_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in specs)

    zero = specs[0].statement
    assert zero.startswith("forall z. (((exists hch_trace_code_zero_source ")
    assert "exists hch_trace_code_zero_target hch_trace_scale_zero_target" in zero
    assert zero.count("z = 0") == 2

    succ = specs[1].statement
    assert succ.count("exists t h.") == 2
    assert succ.count(EXACT_CELL) == 2
    for tag in (
        "succ_source_history",
        "succ_predecessor_history",
        "succ_input_history",
        "succ_target_history",
    ):
        assert (
            f"exists hch_tail_{tag} hch_successor_{tag} hch_head_{tag}"
            in succ
        )


def test_cell_list_equation_bodies_are_pinned_constructive_and_sensitive() -> None:
    specs = _candidate_specs()
    receipts = replay_candidate_bodies(specs, core=_available_specs())
    assert {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == EXPECTED_BODY_RECEIPTS

    certificates: dict[str, tuple[Proof, object]] = {}
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))
        assert all(
            command.split(maxsplit=1)[0]
            not in {"auto", "compact_arith", "ring", "simp", "use"}
            for command in item.script
        )
        certificates[item.name] = (certificate, target)

    successor = specs[1]
    assert successor.statement.count(EXACT_CELL) == 2
    reversed_cell = "z = S ((t + h) * S (t + h) + (h + h))"
    mutated = successor.statement.replace(EXACT_CELL, reversed_cell)
    certificate, _target = certificates[successor.name]
    assert not check((), certificate, _candidate_target(successor, mutated))

    zero = specs[0]
    zero_certificate, _target = certificates[zero.name]
    assert zero.statement.count("z = 0") == 2
    zero_mutation = zero.statement.replace("z = 0", "z = S 0", 1)
    assert not check((), zero_certificate, _candidate_target(zero, zero_mutation))


def test_cell_list_equation_small_reverse_history_models() -> None:
    def beta_at(code: int, scale: int, index: int, value: int) -> bool:
        modulus = 1 + (index + 1) * scale
        return value < modulus and code % modulus == value

    def cell_code(head: int, tail: int) -> int:
        shell = head + tail
        return 1 + shell * (shell + 1) + 2 * tail

    def history(code: int, length: int, trace_code: int, scale: int) -> bool:
        values = [
            trace_code % (1 + (index + 1) * scale)
            for index in range(length + 1)
        ]
        return (
            beta_at(trace_code, scale, 0, 0)
            and beta_at(trace_code, scale, length, code)
            and all(
                any(
                    values[index + 1] == cell_code(head, values[index])
                    for head in range(values[index + 1] + 1)
                )
                for index in range(length)
            )
        )

    assert history(0, 0, 0, 0)
    assert history(1, 1, 4, 1)
    assert history(5, 2, 96, 2)
    assert 1 == cell_code(0, 0)
    assert 5 == cell_code(0, 1)
    assert not history(1, 0, 0, 0)
    assert not history(6, 2, 96, 2)
