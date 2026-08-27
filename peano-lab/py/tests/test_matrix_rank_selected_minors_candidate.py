"""Actual selected-minor body checks against an immutable parent surface."""

from __future__ import annotations

from functools import lru_cache
import gc

import pytest

from peano_lab.library.matrix_rank_selected_minors_candidate import make_matrix_rank_selected_minors_candidate_theorems
from peano_lab.library.matrix_recursive_determinant_extensional_candidate import make_matrix_recursive_determinant_extensional_candidate_theorems
from peano_lab.library.theorems import TheoremSpec
from peano_lab.library.candidate_validation import replay_candidate_bodies
from test_matrix_recursive_determinant_candidate import core as parent_core, rows as determinant_rows
from test_matrix_rank_finite_coding_candidate import rows as coding_rows


EXPECTED_NAMES = (
    'matrix_rank_selected_point_exists',
    'matrix_rank_selected_point_functional',
    'matrix_rank_selected_prefix_empty',
    'matrix_rank_selected_prefix_extend',
    'matrix_rank_selected_prefix_exists_nonzero',
    'matrix_rank_selected_square_exists',
    'matrix_rank_signed_selected_square_exists',
    'matrix_rank_selected_prefix_functional',
    'matrix_rank_signed_selected_square_functional',
    'matrix_rank_selected_determinant_exists',
    'matrix_rank_selected_determinant_functional',
    'matrix_rank_selected_point_selector_transport',
    'matrix_rank_selected_prefix_selector_transport',
    'matrix_rank_signed_selected_selector_transport',
    'matrix_rank_selected_determinant_selector_transport',
    'matrix_rank_selected_nonzero_value_decidable',
    'matrix_rank_nonzero_selected_minor_decidable',
    'matrix_rank_nonzero_selected_minor_transport',
    'matrix_rank_selected_determinant_empty',
    'matrix_rank_nonzero_minor_dimension_bounds',
    'matrix_rank_nonzero_minor_empty',
)
EXPECTED_BODY_METRICS = dict(zip(EXPECTED_NAMES, (
    (51,27),(317,45),(21,18),(66,32),(65,33),(50,26),(42,23),
    (96,40),(144,57),(48,26),(185,102),(77,39),(53,42),(157,59),
    (121,73),(92,41),(63,27),(183,75),(52,29),(72,32),(86,37),
), strict=True))


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return make_matrix_rank_selected_minors_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str,TheoremSpec]:
    earlier = (*determinant_rows(),*make_matrix_recursive_determinant_extensional_candidate_theorems(TheoremSpec),*coding_rows())
    return parent_core()|{row.name:row for row in earlier}


def test_selected_minor_inventory_is_exact() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sum(len(row.dependencies) for row in rows()) == 38
    assert sum(len(row.script) for row in rows()) == 1_068


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_actual_selected_minor_body_passes_unchanged_kernel(name: str) -> None:
    table = {row.name:row for row in rows()}
    receipt = replay_candidate_bodies((table[name],),core=core()|table)[0]
    assert (receipt.proof_nodes,receipt.proof_depth) == EXPECTED_BODY_METRICS[name]
    assert receipt.proof_objects == receipt.proof_nodes
    gc.collect()
