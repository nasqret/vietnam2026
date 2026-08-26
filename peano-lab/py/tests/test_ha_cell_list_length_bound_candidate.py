"""Lightweight proof-body audit for RFC deliverable 9.

This test deliberately performs no recursive dependency closure, cold
empty-context replay, campaign admission, or full-suite work.  The direct
dependencies remain ordinary hypotheses while the candidate body is replayed
and checked by the intuitionistic kernel.
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
from peano_lab.library.ha_cell_bounds_candidate import (
    make_ha_cell_bounds_candidate_theorems,
)
from peano_lab.library.ha_cell_list_equations_candidate import (
    make_ha_cell_list_equations_candidate_theorems,
)
from peano_lab.library.ha_cell_list_length_bound_candidate import (
    make_ha_cell_list_length_bound_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "cell_list_length_le_code"
EXPECTED_DEPENDENCIES = (
    "cell_list_succ_iff_cell",
    "cell_tail_lt_code",
    "zero_le",
    "succ_le_succ",
    "le_trans",
)
EXPECTED_STATEMENT_RECEIPT = (
    2754,
    "48af1df5e7ca96895308b04b48ed154ed33399424d19a38b7cb18841ac12a08a",
)
EXPECTED_BODY_RECEIPT = (5, 43, 49, 22, 49, 48, 0)
CONCLUSION = "exists k. k + l = z"


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    specs = make_ha_cell_list_length_bound_candidate_theorems(TheoremSpec)
    assert len(specs) == 1
    return specs[0]


@lru_cache(maxsize=1)
def _private_dependencies() -> dict[str, TheoremSpec]:
    specs = (
        make_ha_cell_list_equations_candidate_theorems(TheoremSpec)
        + make_ha_cell_bounds_candidate_theorems(TheoremSpec)
    )
    return {item.name: item for item in specs}


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _private_dependencies()


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


def test_cell_list_length_bound_surface_is_exact_and_private() -> None:
    item = _candidate_spec()
    assert item.name == EXPECTED_NAME
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert make_ha_cell_list_length_bound_candidate_theorems(
        TheoremSpec
    ) == (item,)
    assert (len(item.statement), sha256(item.statement.encode()).hexdigest()) == (
        EXPECTED_STATEMENT_RECEIPT
    )

    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert (
        formula
        == parse_formula(item.statement)
        == _closed_formula(item.statement)
    )
    assert item.statement.startswith("forall z l. (exists hch_trace_code_")
    assert item.statement.endswith(f"-> {CONCLUSION}")
    assert item.statement.count(CONCLUSION) == 1
    assert all(
        macro not in item.statement
        for macro in ("BetaAt(", "Cell(", "CellHistory(", "CellListLen(", "Lt(")
    )

    public = _specs_by_name()
    assert item.name not in public
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_list_length_bound_candidate" not in registry_source
    assert f'"{item.name}"' not in registry_source


def test_cell_list_length_bound_body_is_pinned_constructive_and_sensitive() -> None:
    item = _candidate_spec()
    receipts = replay_candidate_bodies((item,), core=_available_specs())
    assert len(receipts) == 1
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

    certificate, target = _body_certificate(item)
    assert check((), certificate, target)
    assert not any(type(node) is DNE for node in _walk_unique(certificate))
    assert "induction l" in item.script
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in item.script
    )
    assert all(
        marker not in command.casefold()
        for command in item.script
        for marker in ("classical", "dne", "sorry")
    )

    strengthened = item.statement.replace(CONCLUSION, "exists k. k + S l = z")
    assert strengthened != item.statement
    assert not check((), certificate, _candidate_target(item, strengthened))


def test_cell_list_length_bound_small_reverse_history_examples() -> None:
    # Exact histories already used by the list-equation audit: nil, one cell,
    # and two cells.  Their terminal codes visibly dominate their lengths.
    examples = ((0, 0), (1, 1), (5, 2))
    assert all(length <= code for code, length in examples)

    # The nearby strengthening rejected above is mathematically false at nil.
    assert not (0 + 1 <= 0)
