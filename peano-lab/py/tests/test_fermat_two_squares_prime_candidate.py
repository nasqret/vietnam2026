"""Bounded constructive audit of final prime two-square assembly."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.library.bertrand_floor_sqrt_total_candidate import (
    make_bertrand_floor_sqrt_total_candidate_theorems,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.fermat_two_squares_candidate import (
    make_fermat_two_squares_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_collision_norm_candidate import (
    make_fermat_two_squares_collision_norm_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_pigeonhole_candidate import (
    make_fermat_two_squares_pigeonhole_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_prime_candidate import (
    make_fermat_two_squares_prime_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_residue_grid_candidate import (
    make_fermat_two_squares_residue_grid_candidate_theorems,
)
from peano_lab.library.finite_prefix_collision_decision_candidate import (
    make_finite_prefix_collision_decision_candidate_theorems,
)
from peano_lab.library.finite_sum_pointwise_mod_candidate import (
    make_finite_sum_pointwise_mod_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "absolute_difference_zero_forces_coordinate_equality",
    "nonzero_coordinate_pair_has_positive_square_norm",
    "distinct_flat_indices_have_positive_difference_norm",
    "strict_successor_coordinate_bound_is_weak_bound",
    "shared_beta_collision_remainders_equal",
    "equal_remainder_affine_values_balanced_congruent",
    "prime_floor_decoded_affine_collision_represents_prime",
    "prime_floor_affine_grid_collision_represents_prime",
    "prime_mod_four_one_is_sum_of_two_squares",
)

EXPECTED_STATEMENT_SHA256 = {
    "absolute_difference_zero_forces_coordinate_equality": "d0d51de298ebf0eaa39c0c69310daf5f481442f018348bcee268258a394b62a3",
    "nonzero_coordinate_pair_has_positive_square_norm": "036d6aecd778e3b703a7e8f92f0fbee4489ad3cdb3353caf82f4f49acc0c754b",
    "distinct_flat_indices_have_positive_difference_norm": "c9a01da9934db54da50f2d3ab22842853534bd0b90edefb5177110880bc2e6f6",
    "strict_successor_coordinate_bound_is_weak_bound": "b62ac1d5b5c772b67ab2fbb07937c1215e133a20f60b97902b8d0bc1f2d9b3be",
    "shared_beta_collision_remainders_equal": "f4c4d55d13b621de4356df1217dcc686eefbb964ff1346162c6bd041fee59b52",
    "equal_remainder_affine_values_balanced_congruent": "21dddd9aab6957fb1d16c91064be91150c6e3361fb513ae1e6c18d8c67fdd0a5",
    "prime_floor_decoded_affine_collision_represents_prime": "d53b9257efa6718cce4ba1e83a41abe7cc0996e914d3d3b61495d0b68200f7d6",
    "prime_floor_affine_grid_collision_represents_prime": "279826097cd98309eca36301d2bd35c14f2cb69d6c5b8337139f5a9981361e85",
    "prime_mod_four_one_is_sum_of_two_squares": "41ee377098bb3cc2156a1c8c5ff724d4c2bdbbd72eafa64edd141011291e5ee4",
}

EXPECTED_FLAGSHIP_DEPENDENCIES = (
    "prime_mod_four_one_bounded_divisible_two_square_norm_exists",
    "floor_sqrt_total",
    "prime_floor_affine_residue_grid_collision",
    "prime_floor_affine_grid_collision_represents_prime",
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_prime_candidate_theorems(TheoremSpec)


def _core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_finite_sum_pointwise_mod_candidate_theorems,
        make_bertrand_floor_sqrt_total_candidate_theorems,
        make_fermat_two_squares_candidate_theorems,
        make_fermat_two_squares_pigeonhole_candidate_theorems,
        make_finite_prefix_collision_decision_candidate_theorems,
        make_fermat_two_squares_residue_grid_candidate_theorems,
        make_fermat_two_squares_collision_norm_candidate_theorems,
    ):
        core.update((row.name, row) for row in factory(TheoremSpec))
    return core


def test_prime_assembly_candidates_are_isolated_and_closed() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert len({row.name for row in rows}) == len(rows)
    assert all(row.name not in _specs_by_name() for row in rows)
    assert {
        row.name: sha256(row.statement.encode()).hexdigest() for row in rows
    } == EXPECTED_STATEMENT_SHA256
    assert rows[-1].dependencies == EXPECTED_FLAGSHIP_DEPENDENCIES
    assert rows[-1].statement.startswith("forall p n. p = S n ->")
    assert rows[-1].statement.endswith("exists x y. p = x * x + y * y")
    for row in rows:
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == parse_formula(row.statement) == _closed_formula(row.statement)


def test_prime_assembly_bodies_are_constructive_and_kernel_checked() -> None:
    rows = _rows()
    receipts = replay_candidate_bodies(rows, core=_core())
    assert len(receipts) == len(rows)
    assert max(row.proof_nodes for row in receipts) == 146
    assert max(row.proof_depth for row in receipts) == 47
    flagship = receipts[-1]
    assert (
        flagship.dependency_count,
        flagship.command_count,
        flagship.proof_nodes,
        flagship.proof_depth,
    ) == (4, 45, 61, 27)
    assert all(
        "DNE" not in command and "by_contra" not in command
        and "classical" not in command and "sorry" not in command
        for row in rows for command in row.script
    )


def test_prime_flagship_certificate_rejects_false_target_mutation() -> None:
    flagship = _rows()[-1]
    available = _core() | {row.name: row for row in _rows()}

    def target(statement: str):
        result = _closed_formula(statement)
        for dependency in reversed(flagship.dependencies):
            result = Imp(_closed_formula(available[dependency].statement), result)
        return result

    genuine = target(flagship.statement)
    state = start(genuine)
    for dependency in flagship.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in flagship.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    certificate = checked_final(state, genuine)

    assert check((), certificate, genuine)
    assert not check((), certificate, target(f"({flagship.statement}) /\\ 0 = 1"))


@pytest.mark.parametrize("prime", (5, 13, 17, 29, 37, 41, 53, 61, 73, 89, 97))
def test_small_mod_four_one_primes_have_two_square_examples(prime: int) -> None:
    assert prime % 4 == 1
    assert any(a * a + b * b == prime for a in range(prime) for b in range(prime))
