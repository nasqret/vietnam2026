"""Lightweight body audit for private K3B list-length functionality.

This test checks only the exact expanded surface and the dependency-curried
proof body.  It performs no recursive dependency closure, no empty-context
replay, and no campaign admission work.
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
from peano_lab.library.ha_cell_functional_candidate import (
    make_ha_cell_functional_candidate_theorems,
)
from peano_lab.library.ha_cell_history_candidate import (
    make_ha_cell_history_candidate_theorems,
)
from peano_lab.library.ha_cell_list_equations_candidate import (
    make_ha_cell_list_equations_candidate_theorems,
)
from peano_lab.library.ha_cell_list_length_functional_candidate import (
    make_ha_cell_list_length_functional_candidate_theorems,
)
from peano_lab.library.ha_pair_cell_seed_candidate import (
    make_ha_pair_cell_seed_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "cell_list_length_functional"
EXPECTED_DEPENDENCIES = (
    "cell_list_zero_iff_nil",
    "cell_list_succ_iff_cell",
    "nil_not_cell",
    "cell_tail_functional",
    "zero_or_succ",
)
EXPECTED_STATEMENT_RECEIPT = (
    5517,
    "e08563402824e2af98ac5fcd56065b173da4713dd33ab96ec16fb6fc5346b8e3",
)
EXPECTED_BODY_RECEIPT = (5, 119, 163, 42, 163, 162, 0)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_cell_list_length_functional_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _support_specs() -> dict[str, TheoremSpec]:
    support: dict[str, TheoremSpec] = {}
    for factory in (
        make_ha_cell_history_candidate_theorems,
        make_ha_cell_list_equations_candidate_theorems,
        make_ha_pair_cell_seed_candidate_theorems,
        make_ha_cell_functional_candidate_theorems,
    ):
        support.update((item.name, item) for item in factory(TheoremSpec))
    return support


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _support_specs()


def _candidate_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


@lru_cache(maxsize=1)
def _body_certificate() -> tuple[Proof, object]:
    item = _candidate_specs()[0]
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


def test_cell_list_length_functional_surface_is_exact_and_private() -> None:
    specs = _candidate_specs()
    assert make_ha_cell_list_length_functional_candidate_theorems(
        TheoremSpec
    ) == specs
    assert tuple(item.name for item in specs) == (EXPECTED_NAME,)

    item = specs[0]
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
    ) == EXPECTED_STATEMENT_RECEIPT
    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement) == _closed_formula(item.statement)
    assert item.statement.startswith("forall z l m. ")
    assert item.statement.endswith(" -> l = m")
    assert "hclfun_successor_length_argument" not in item.statement
    assert all(
        macro not in item.statement
        for macro in ("BetaAt(", "Cell(", "CellHistory(", "CellListLen(")
    )

    public = _specs_by_name()
    assert item.name not in public
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_list_length_functional_candidate" not in registry_source
    assert f'"{item.name}"' not in registry_source


def test_cell_list_length_functional_body_is_pinned_and_constructive() -> None:
    item = _candidate_specs()[0]
    receipts = replay_candidate_bodies((item,), core=_available_specs())
    receipt = receipts[0]
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
    assert "induction l" in item.script
    assert "induction m" not in item.script
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "ring", "simp", "use"}
        for command in item.script
    )


def test_cell_list_length_functional_rejects_conclusion_mutations() -> None:
    item = _candidate_specs()[0]
    certificate, _target = _body_certificate()
    assert item.statement.endswith("l = m")

    successor_mutation = item.statement[: -len("l = m")] + "l = S m"
    zero_mutation = item.statement[: -len("l = m")] + "l = 0"
    assert not check((), certificate, _candidate_target(item, successor_mutation))
    assert not check((), certificate, _candidate_target(item, zero_mutation))
