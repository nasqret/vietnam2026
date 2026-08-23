"""Bounded constructive audit of witnessed finite-prefix collision decisions."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from math import isqrt
from pathlib import Path

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.fermat_two_squares_pigeonhole_candidate import (
    make_fermat_two_squares_pigeonhole_candidate_theorems,
)
from peano_lab.library.finite_prefix_collision_decision_candidate import (
    make_finite_prefix_collision_decision_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "finite_prefix_collision_succ",
    "finite_prefix_last_occurrence_collision",
    "finite_prefix_injective_extend_fresh",
    "finite_prefix_collision_or_injective",
    "finite_bounded_into_oversized_collision",
    "floor_square_oversized_bounded_grid_collision",
)

EXPECTED_DEPENDENCIES = {
    "finite_prefix_collision_succ": ("le_succ",),
    "finite_prefix_last_occurrence_collision": (
        "le_succ",
        "le_refl",
        "lt_irrefl_expanded",
    ),
    "finite_prefix_injective_extend_fresh": (
        "finite_lt_succ_eq_or_lt",
        "beta_at_unique",
    ),
    "finite_prefix_collision_or_injective": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "finite_prefix_collision_succ",
        "beta_at_exists",
        "finite_contains_decidable",
        "finite_prefix_last_occurrence_collision",
        "finite_prefix_injective_extend_fresh",
    ),
    "finite_bounded_into_oversized_collision": (
        "finite_prefix_collision_or_injective",
        "finite_bounded_into_collision_from_constructive_decision",
    ),
    "floor_square_oversized_bounded_grid_collision": (
        "floor_square_successor_grid_strictly_exceeds_input",
        "finite_bounded_into_oversized_collision",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "finite_prefix_collision_succ": (
        "6506acac7052763736d25d84ab1e3dc9551dcb84b4910c1f8c0b02038346da73"
    ),
    "finite_prefix_last_occurrence_collision": (
        "6f41c7660af957b0400eb5c9abefe9ee3b6f57c81275ffd7f4acad75022ca97c"
    ),
    "finite_prefix_injective_extend_fresh": (
        "761add2a291714c08e3e5e448fa94540e2d5bbf40f8b53df031a424cd8135561"
    ),
    "finite_prefix_collision_or_injective": (
        "34cd81f2d760771a7c74c6067f2356df3048d25a5212b2688f65cd77c5abae22"
    ),
    "finite_bounded_into_oversized_collision": (
        "e6c0e6e5bd4b20bbb77b1e9071a39b63d8a908fd317c8be56bfe2ccfb8b77ee1"
    ),
    "floor_square_oversized_bounded_grid_collision": (
        "d81e62ee6c37b580c87421ba7d9d9cbf1cf153cd7d3866f76ac01e27fe1fc6ed"
    ),
}

# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_BODY_RECEIPTS = {
    "finite_prefix_collision_succ": (1, 31, 78, 35, 78, 77, 0),
    "finite_prefix_last_occurrence_collision": (3, 28, 57, 27, 57, 56, 0),
    "finite_prefix_injective_extend_fresh": (2, 77, 124, 32, 124, 123, 0),
    "finite_prefix_collision_or_injective": (7, 60, 76, 25, 76, 75, 0),
    "finite_bounded_into_oversized_collision": (2, 17, 43, 24, 43, 42, 0),
    "floor_square_oversized_bounded_grid_collision": (2, 19, 44, 26, 44, 43, 0),
}

_BODY_DEADLINE_SECONDS = 20


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_finite_prefix_collision_decision_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    core.update(
        (item.name, item)
        for item in make_fermat_two_squares_pigeonhole_candidate_theorems(TheoremSpec)
    )
    return core


def _available_specs() -> dict[str, TheoremSpec]:
    return _dependency_core() | {item.name: item for item in _candidate_specs()}


def _curried_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


@lru_cache(maxsize=None)
def _body_certificate(name: str):
    item = next(item for item in _candidate_specs() if item.name == name)
    target = _curried_target(item)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _walk_unique(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        for item in fields(current):
            child = getattr(current, item.name)
            if isinstance(child, Proof):
                pending.append(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"finite collision replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_collision_factory_is_exact_deterministic_and_registry_isolated() -> None:
    first = _candidate_specs()

    assert make_finite_prefix_collision_decision_candidate_theorems(TheoremSpec) == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    assert "finite_prefix_collision_decision_candidate" not in Path(
        theorem_registry.__file__
    ).read_text()


def test_collision_contracts_are_closed_expanded_first_order_ha() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "BetaAt(",
                "BoundedInto(",
                "Collision(",
                "FloorSqrt(",
                "InjectivePrefix(",
                "<",
                "<=",
                "%",
            )
        )

    decision, rectangular, grid = _candidate_specs()[-3:]
    assert decision.statement.startswith("forall b c l.")
    assert rectangular.statement.startswith("forall b c l m.")
    assert grid.statement.startswith("forall b c l p s. l = S s * S s ->")
    for item in (rectangular, grid):
        assert "exists ftsp_first_fpcd_generic" in item.statement
        assert "~(ftsp_first_fpcd_generic = ftsp_second_fpcd_generic)" in item.statement


def test_collision_scripts_are_constructive_and_explicit() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)

    assert "induction l" in commands
    assert "specialize finite_contains_decidable b" in commands
    assert "apply finite_prefix_last_occurrence_collision" in commands
    assert "apply finite_prefix_injective_extend_fresh" in commands
    assert "apply finite_bounded_into_collision_from_constructive_decision" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_collision_bodies_are_independently_kernel_checked_and_bounded() -> None:
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs(), core=_dependency_core())
    observed = {
        item.name: (
            item.dependency_count,
            item.command_count,
            item.proof_nodes,
            item.proof_depth,
            item.proof_objects,
            item.proof_edges,
            item.reused_objects,
        )
        for item in receipts
    }
    assert observed == EXPECTED_BODY_RECEIPTS
    assert max(item.proof_nodes for item in receipts) == 124
    assert max(item.proof_depth for item in receipts) == 35


def test_collision_certificates_are_dne_free_and_reject_false_targets() -> None:
    for item in _candidate_specs():
        certificate, target = _body_certificate(item.name)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))
        assert not check(
            (),
            certificate,
            _curried_target(item, f"({item.statement}) /\\ 0 = 1"),
        )


@pytest.mark.parametrize("modulus", range(1, 24))
def test_oversized_square_grids_have_distinct_actual_collision_indices(
    modulus: int,
) -> None:
    side = isqrt(modulus) + 1
    length = side * side
    values = tuple(index % modulus for index in range(length))
    collisions = tuple(
        (first, second, values[first])
        for first in range(length)
        for second in range(first + 1, length)
        if values[first] == values[second]
    )

    assert length > modulus
    assert all(value < modulus for value in values)
    assert collisions
    first, second, value = collisions[0]
    assert first < length
    assert second < length
    assert first != second
    assert values[first] == value == values[second]
