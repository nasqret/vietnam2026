"""Bounded audit of the exact single-hypothesis Lagrange descent bridge."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256

from peano_lab.kernel.formulas import Forall, Imp, parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.four_square_bounded_seed_candidate import (
    make_four_square_bounded_seed_candidate_theorems,
)
from peano_lab.library.four_square_descent_candidate import (
    make_four_square_descent_candidate_theorems,
)
from peano_lab.library.four_square_lagrange_bridge_candidate import (
    FOUR_SQUARE_DESCENT_BELOW_PRIME_MULTIPLIER_BOUNDED,
    FOUR_SQUARE_LAGRANGE_FROM_BOUNDED_STRICT_DESCENT,
    FOUR_SQUARE_LAGRANGE_FROM_STRICT_DESCENT,
    FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT,
    FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT_AND_SEED,
    FOUR_SQUARE_PRIME_FROM_STRICT_DESCENT,
    make_four_square_lagrange_bridge_candidate_theorems,
)
from peano_lab.library.four_square_lagrange_candidate import (
    make_four_square_lagrange_candidate_theorems,
)
from peano_lab.library.four_square_residue_intersection_candidate import (
    make_four_square_residue_intersection_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    FOUR_SQUARE_PRIME_FROM_STRICT_DESCENT,
    FOUR_SQUARE_LAGRANGE_FROM_STRICT_DESCENT,
    FOUR_SQUARE_DESCENT_BELOW_PRIME_MULTIPLIER_BOUNDED,
    FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT_AND_SEED,
    FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT,
    FOUR_SQUARE_LAGRANGE_FROM_BOUNDED_STRICT_DESCENT,
)
PINNED_ENDPOINTS = {
    FOUR_SQUARE_PRIME_FROM_STRICT_DESCENT:
        "a0db9304ae96fb7094a9722321341b08818fdf0514b9534ec6a81b8340561809",
    FOUR_SQUARE_LAGRANGE_FROM_STRICT_DESCENT:
        "9f7dff900d6c44b4dc8eed887ea9b29811d79882645ba7d2264f60765c503dea",
    FOUR_SQUARE_DESCENT_BELOW_PRIME_MULTIPLIER_BOUNDED:
        "a859665b34b9b4fe4a17761cfb13a739f224883b872fdd96e5470aa0ec86107b",
    FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT_AND_SEED:
        "4fad58441392e29c5159e6249605bffdb4c3303289e0db0bad8e6ac36f40c1e0",
    FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT:
        "cb2ad9ffade4799a2ad2f720eb1201d4844a9e2195898b99da708d8c03cb2654",
    FOUR_SQUARE_LAGRANGE_FROM_BOUNDED_STRICT_DESCENT:
        "1c950fd851415f84bc19ab5370d15465211e4cfcb280ae2594cef84bf5c47ed1",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_lagrange_bridge_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    result = {row.name: row for row in editions_v12.ALPHA_SPECS}
    for factory in (
        make_four_square_lagrange_candidate_theorems,
        make_four_square_descent_candidate_theorems,
        make_four_square_residue_intersection_candidate_theorems,
        make_four_square_bounded_seed_candidate_theorems,
    ):
        result.update((row.name, row) for row in factory(TheoremSpec))
    return result


def test_lagrange_bridge_candidates_are_closed_and_release_isolated() -> None:
    seen: set[str] = set()
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    assert _rows() == make_four_square_lagrange_bridge_candidate_theorems(TheoremSpec)
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in _specs_by_name()
        assert row.name not in editions_v12.ALPHA_EDITION.by_name
        assert set(row.dependencies) <= set(_core()) | seen
        seen.add(row.name)


def test_lagrange_bridge_bodies_are_independently_kernel_checked() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(receipt.proof_nodes for receipt in receipts) < 250
    assert max(receipt.proof_depth for receipt in receipts) < 75


def test_lagrange_bridge_retains_only_the_actual_strict_descent_hypothesis() -> None:
    prime, universal, _bounded_induction, _bounded_seed, bounded_prime, bounded_all = (
        _rows()
    )
    prime_formula = _closed_formula(prime.statement)
    universal_formula = _closed_formula(universal.statement)

    assert isinstance(prime_formula, Imp)
    assert isinstance(universal_formula, Imp)
    assert isinstance(prime_formula.antecedent, Forall)
    assert isinstance(universal_formula.antecedent, Forall)
    assert isinstance(prime_formula.consequent, Forall)
    assert isinstance(universal_formula.consequent, Forall)
    assert "four_square_prime_modular_seed" in prime.dependencies
    assert "four_square_prime_from_strict_descent" in universal.dependencies
    assert "four_square_prime_bounded_modular_seed" in bounded_prime.dependencies
    assert "four_square_prime_from_bounded_strict_descent" in bounded_all.dependencies
    assert " -> forall n." in universal.statement
    assert {
        row.name: sha256(row.statement.encode()).hexdigest()
        for row in _rows()
    } == PINNED_ENDPOINTS
