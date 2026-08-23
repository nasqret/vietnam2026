"""Bounded constructive audit of affine-collision-to-norm transport."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library import theorems as theorem_registry
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
from peano_lab.library.fermat_two_squares_residue_grid_candidate import (
    make_fermat_two_squares_residue_grid_candidate_theorems,
)
from peano_lab.library.finite_prefix_collision_decision_candidate import (
    make_finite_prefix_collision_decision_candidate_theorems,
)
from peano_lab.library.finite_sum_pointwise_mod_candidate import (
    make_finite_sum_pointwise_mod_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "balanced_zero_congruence_implies_multiple",
    "multiple_implies_balanced_zero_congruence",
    "negative_one_scaled_square_identity",
    "negative_one_scaled_square_congruent_zero",
    "balanced_linear_congruence_implies_squared_congruence",
    "balanced_zero_sum_implies_squared_congruence",
    "negative_one_congruent_square_norm_multiple",
    "negative_one_linear_congruence_norm_multiple",
    "negative_one_opposite_linear_congruence_norm_multiple",
    "natural_absolute_difference_exists",
    "bounded_natural_absolute_difference",
    "affine_collision_difference_linear_or_opposite",
    "affine_collision_absolute_difference_norm_multiple",
    "flat_square_index_row_not_at_least_width",
    "flat_square_index_row_below_width",
)

EXPECTED_STATEMENT_SHA256 = {
    "balanced_zero_congruence_implies_multiple": "da97d00b2eecd2c9462d319751887cdae0589d04e27ebb33d765cdb999ac0199",
    "multiple_implies_balanced_zero_congruence": "ef75b17a5182d2b3829ec957f34a25cf405c5ead3c64f7d405b183f16a605521",
    "negative_one_scaled_square_identity": "41e4a9269ef8ac2f881b8629110eb2026bd8231c20f0c76c500ddbf23c08bb44",
    "negative_one_scaled_square_congruent_zero": "cf11baae902ed3b631e89adb56ba0cf4c86658766fd55285a3927ebccfb26378",
    "balanced_linear_congruence_implies_squared_congruence": "db85ef3a5b0a897666cc00cd5158039a1ca02d389153a8775bc1e2b5912ad9a9",
    "balanced_zero_sum_implies_squared_congruence": "31bba23799413d264de51d29ba643e5d85e01c07391b831bddaa26e8a348c12a",
    "negative_one_congruent_square_norm_multiple": "756aa10102d8e30f32a4d0f3050cdc59014f31deaf7513d32961f7746a71f841",
    "negative_one_linear_congruence_norm_multiple": "d3a4be6a18067b22975ffe40cc6d8e4aca7508fcdb5ce8928a6919d3e8e158ea",
    "negative_one_opposite_linear_congruence_norm_multiple": "089ab80aed5e8d591d267b348e0d6b0e13c04923ebb7042318413d037a909d4b",
    "natural_absolute_difference_exists": "0b05f0870554ffdea82ffa782af6fb413e2308c0d51ec8a00dd8743cf9182779",
    "bounded_natural_absolute_difference": "871144c940add4b7980ceab603dc41e9acec5e851fb349da1f4b47d9a935d455",
    "affine_collision_difference_linear_or_opposite": "6962e7a76144300ddde20f9aaa3a79b3b042b90b89d949c31af2886b5ed84d15",
    "affine_collision_absolute_difference_norm_multiple": "b3923688b19701526842363879c8fbd5322a62ddf4dc62df5a10f63d032b8600",
    "flat_square_index_row_not_at_least_width": "0490ae2a0034f41547b75d76ea497418bc4c55aff8adc7245159788e1a3f26e9",
    "flat_square_index_row_below_width": "a01aa77f38af17f93200b31b970224e30d912bab36ecdfaf2e9826b1a7efea6d",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_collision_norm_candidate_theorems(TheoremSpec)


def _core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_finite_sum_pointwise_mod_candidate_theorems,
        make_bertrand_floor_sqrt_total_candidate_theorems,
        make_fermat_two_squares_candidate_theorems,
        make_fermat_two_squares_pigeonhole_candidate_theorems,
        make_finite_prefix_collision_decision_candidate_theorems,
        make_fermat_two_squares_residue_grid_candidate_theorems,
    ):
        core.update((row.name, row) for row in factory(TheoremSpec))
    return core


def test_collision_norm_candidates_are_deterministic_and_isolated() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert make_fermat_two_squares_collision_norm_candidate_theorems(TheoremSpec) == rows
    assert len({row.name for row in rows}) == len(rows)
    assert all(row.name not in _specs_by_name() for row in rows)
    assert "fermat_two_squares_collision_norm_candidate" not in Path(
        theorem_registry.__file__
    ).read_text()
    assert {
        row.name: sha256(row.statement.encode()).hexdigest() for row in rows
    } == EXPECTED_STATEMENT_SHA256


def test_collision_norm_contracts_are_closed_expanded_ha() -> None:
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == parse_formula(row.statement) == _closed_formula(row.statement)
        assert all(
            token not in row.statement
            for token in ("ModEq(", "Abs(", "Collision(", "<=", "%")
        )


def test_collision_norm_bodies_are_constructive_and_kernel_checked() -> None:
    rows = _rows()
    receipts = replay_candidate_bodies(rows, core=_core())
    assert len(receipts) == len(rows)
    assert max(row.proof_nodes for row in receipts) == 358
    assert max(row.proof_depth for row in receipts) == 38
    assert all(
        "DNE" not in command
        and "by_contra" not in command
        and "classical" not in command
        and "sorry" not in command
        for row in rows
        for command in row.script
    )


@pytest.mark.parametrize("modulus", (5, 13, 17, 29, 37, 41))
def test_both_affine_sign_patterns_produce_divisible_norms(modulus: int) -> None:
    root = next(value for value in range(modulus) if (value * value + 1) % modulus == 0)
    for x in range(modulus):
        for y in range(modulus):
            if (root * x - y) % modulus == 0 or (root * x + y) % modulus == 0:
                assert (x * x + y * y) % modulus == 0
