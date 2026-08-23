"""Bounded kernel audit of actual beta-coded affine square-root grids."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from math import isqrt
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v12, theorems as theorem_registry
from peano_lab.library.fermat_two_squares_residue_grid_candidate import (
    AFFINE_GRID_POINT_REMAINDER_EXISTS,
    BETA_AFFINE_RESIDUE_GRID_BOUNDED,
    BETA_AFFINE_RESIDUE_GRID_EXISTS,
    BETA_AFFINE_RESIDUE_GRID_EXTEND,
    EQUAL_AFFINE_REMAINDERS_BALANCED,
    PRIME_FLOOR_AFFINE_RESIDUE_GRID_COLLISION,
    PRIME_FLOOR_AFFINE_RESIDUE_GRID_EXISTS,
    make_fermat_two_squares_residue_grid_candidate_theorems,
)
from peano_lab.library.finite_prefix_collision_decision_candidate import (
    make_finite_prefix_collision_decision_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _primitive


EXPECTED_NAMES = (
    AFFINE_GRID_POINT_REMAINDER_EXISTS,
    BETA_AFFINE_RESIDUE_GRID_EXTEND,
    BETA_AFFINE_RESIDUE_GRID_EXISTS,
    BETA_AFFINE_RESIDUE_GRID_BOUNDED,
    PRIME_FLOOR_AFFINE_RESIDUE_GRID_EXISTS,
    PRIME_FLOOR_AFFINE_RESIDUE_GRID_COLLISION,
    EQUAL_AFFINE_REMAINDERS_BALANCED,
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_residue_grid_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {row.name: row for row in editions_v12.ALPHA_SPECS} | {
        row.name: row
        for row in make_finite_prefix_collision_decision_candidate_theorems(
            TheoremSpec
        )
    }


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _body(name: str):
    row = next(item for item in _rows() if item.name == name)
    dependencies = _core() | {item.name: item for item in _rows()}
    target = _closed_formula(row.statement)
    for dependency in reversed(row.dependencies):
        target = Imp(_closed_formula(dependencies[dependency].statement), target)
    state = start(target)
    for dependency in row.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in row.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _walk(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(
            child
            for field in fields(node)
            if isinstance((child := getattr(node, field.name)), Proof)
        )


def test_residue_grid_factory_is_exact_isolated_and_dependency_ordered() -> None:
    rows = _rows()
    assert rows == make_fermat_two_squares_residue_grid_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    alpha = {item.name for item in editions_v12.ALPHA_SPECS}
    seen = set(_core())
    for row in rows:
        assert row.name not in alpha
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert all(dependency in seen for dependency in row.dependencies)
        seen.add(row.name)
        formula, free_names = parse_formula_with_names(row.statement)
        assert not free_names
        assert formula == _closed_formula(row.statement)
        assert all(
            token not in row.statement
            for token in (
                "Prime(",
                "FloorSqrt(",
                "AffineResidueGrid(",
                "BetaAt(",
                "Collision(",
                "%",
                "^",
            )
        )
    assert "fermat_two_squares_residue_grid_candidate" not in Path(
        theorem_registry.__file__
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_affine_residue_grid_bodies_kernel_check_constructively(name: str) -> None:
    certificate, target = _body(name)
    nodes, depth = proof_metrics(certificate)
    assert check((), certificate, target)
    assert nodes <= 350
    assert depth <= 80
    assert all(type(node) is not DNE for node in _walk(certificate))


def test_grid_scripts_use_genuine_division_extension_and_witnessed_collision() -> None:
    commands = tuple(command for row in _rows() for command in row.script)
    assert "apply division_remainder_exists" in commands
    assert "exact beta_prefix_extend" in commands
    assert "apply floor_square_oversized_bounded_grid_collision" in commands
    assert all(not command.startswith(("auto", "ring", "use ")) for command in commands)
    assert all("DNE" not in command and "classical" not in command for command in commands)


def test_prime_square_root_affine_grids_always_have_actual_equal_residues() -> None:
    primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)
    cases = 0
    for modulus in primes:
        width = isqrt(modulus) + 1
        for root in range(modulus):
            seen: dict[int, tuple[int, int, int]] = {}
            collision = None
            for index in range(width * width):
                row, column = divmod(index, width)
                quotient, residue = divmod(root * row + column, modulus)
                assert row < width and column < width and residue < modulus
                if residue in seen:
                    old_index, old_row, old_column = seen[residue]
                    old_quotient = (root * old_row + old_column) // modulus
                    assert old_index != index
                    assert (
                        root * old_row + old_column + modulus * quotient
                        == root * row + column + modulus * old_quotient
                    )
                    collision = (old_index, index, residue)
                    break
                seen[residue] = (index, row, column)
            assert collision is not None
            cases += 1
    assert cases == sum(primes)


def test_residue_grid_rfc_distinguishes_actual_collision_from_unproved_norm() -> None:
    repository = Path(__file__).resolve().parents[3]
    rfc = (
        repository
        / "research"
        / "arithmetic-library"
        / "fermat-two-squares-residue-grid-rfc-v1.md"
    ).read_text(encoding="utf-8")
    for name in EXPECTED_NAMES:
        assert f"`{name}`" in rfc
    assert "actual distinct indices with equal affine residues" in rfc
    assert "does not claim that transport" in rfc
