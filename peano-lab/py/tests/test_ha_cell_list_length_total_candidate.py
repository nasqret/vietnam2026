"""Focused body audit for K3B ``cell_list_length_total``.

The test deliberately does not replay recursive dependency closure, admit the
candidate, or run any campaign-wide gate.  It checks the fully expanded
surface and kernel-checks only the dependency-curried proof body.
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
    cell_list_len,
    make_ha_cell_history_candidate_theorems,
)
from peano_lab.library.ha_cell_list_length_total_candidate import (
    make_ha_cell_list_length_total_candidate_theorems,
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


EXPECTED_NAME = "cell_list_length_total"
EXPECTED_DEPENDENCIES = (
    "cell_history_nil",
    "cell_constructor",
    "cell_history_extend",
)
EXPECTED_STATEMENT_RECEIPT = (
    2219,
    "8e6cea3fc40ffe051e4e3eb8af5b698e087c0f3d798fcfc628a107db1b09d765",
)
EXPECTED_BODY_RECEIPT = (3, 22, 58, 32, 58, 57, 0)
EXPECTED_CELL_CONSTRUCTOR = (
    "forall head tail. exists code. code = S "
    "((head + tail) * S (head + tail) + (tail + tail))"
)


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (item,) = make_ha_cell_list_length_total_candidate_theorems(TheoremSpec)
    return item


@lru_cache(maxsize=1)
def _dependency_specs() -> dict[str, TheoremSpec]:
    history = make_ha_cell_history_candidate_theorems(TheoremSpec)
    pair_cell = make_ha_pair_cell_seed_candidate_theorems(TheoremSpec)
    return {item.name: item for item in history + pair_cell}


def _candidate_target(statement: str | None = None):
    item = _candidate_spec()
    dependencies = _dependency_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for name in reversed(item.dependencies):
        target = Imp(_closed_formula(dependencies[name].statement), target)
    return target


def _body_certificate() -> tuple[Proof, object]:
    item = _candidate_spec()
    target = _candidate_target()
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


def test_cell_list_length_total_surface_is_exact_closed_and_private() -> None:
    item = _candidate_spec()
    expected_list = cell_list_len("z", "l", tag="length_total")

    assert item.name == EXPECTED_NAME
    assert item.statement == f"forall l. exists z. ({expected_list})"
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert (len(item.statement), sha256(item.statement.encode()).hexdigest()) == (
        EXPECTED_STATEMENT_RECEIPT
    )
    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement) == _closed_formula(item.statement)
    assert all(
        macro not in item.statement
        for macro in ("BetaAt(", "Cell(", "CellHistory(", "CellListLen(")
    )
    assert "<->" not in item.statement

    dependencies = _dependency_specs()
    assert dependencies["cell_constructor"].statement == EXPECTED_CELL_CONSTRUCTOR
    assert "induction l" in item.script
    assert "specialize cell_constructor 0" in item.script
    assert "specialize cell_history_extend 0" in item.script

    public = _specs_by_name()
    assert item.name not in public
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_list_length_total_candidate" not in registry_source
    assert f'"{item.name}"' not in registry_source


def test_cell_list_length_total_body_is_pinned_constructive_and_sensitive() -> None:
    item = _candidate_spec()
    (receipt,) = replay_candidate_bodies((item,), core=_dependency_specs())
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
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "ring", "simp", "use"}
        for command in item.script
    )

    # This stronger surface is false already at length zero: exact history
    # functionality forces its terminal code to be nil, not ``S 0``.
    expanded = cell_list_len("z", "l", tag="length_total")
    false_mutation = f"forall l. exists z. (z = S 0 /\\ ({expanded}))"
    assert not check((), certificate, _candidate_target(false_mutation))


def test_cell_list_length_total_zero_head_iteration_examples() -> None:
    def zero_head_cell(tail: int) -> int:
        return 1 + tail * (tail + 1) + 2 * tail

    values = [0]
    for _ in range(5):
        values.append(zero_head_cell(values[-1]))

    assert values[:4] == [0, 1, 5, 41]
    assert all(values[index + 1] > values[index] for index in range(5))
