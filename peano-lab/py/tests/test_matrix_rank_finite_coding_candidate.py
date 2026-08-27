"""Body-level checks, not release admission, for complete finite rank search."""

from __future__ import annotations

from functools import lru_cache
import gc

import pytest

from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems
from peano_lab.library.theorems import TheoremSpec
from peano_lab.library.candidate_validation import replay_candidate_bodies
from test_matrix_recursive_determinant_candidate import core


EXPECTED_NAMES = (
    'matrix_rank_bounded_prefix_value',
    'matrix_rank_common_multiple_divides',
    'matrix_rank_beta_moduli_common_multiple',
    'matrix_rank_recode_congruences_exists',
    'matrix_rank_bounded_recode_in_fixed_box',
    'matrix_rank_uniform_beta_prefix_box_exists',
    'matrix_rank_no_index_below_zero',
    'matrix_rank_prefix_equality_symmetric',
    'matrix_rank_bounded_prefix_transport',
    'matrix_rank_injective_prefix_transport',
    'matrix_rank_injective_prefix_decidable',
    'matrix_rank_bounded_prefix_empty',
    'matrix_rank_bounded_prefix_drop_last',
    'matrix_rank_bounded_prefix_extend',
    'matrix_rank_bounded_prefix_decidable',
    'matrix_rank_selector_transport',
    'matrix_rank_selector_decidable',
    'matrix_rank_selector_dimension_bound',
    'matrix_rank_selector_empty',
)
EXPECTED_BODY_METRICS = dict(zip(EXPECTED_NAMES, (
    (30,21),(26,15),(50,29),(26,16),(125,46),(56,27),(11,8),
    (54,24),(27,18),(53,28),(47,19),(14,11),(25,17),(31,18),
    (78,31),(73,30),(33,13),(26,17),(34,18),
), strict=True))


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return make_matrix_rank_finite_coding_candidate_theorems(TheoremSpec)


def test_finite_coding_inventory_is_exact() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sum(len(row.dependencies) for row in rows()) == 49
    assert sum(len(row.script) for row in rows()) == 568


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_actual_finite_coding_body_passes_unchanged_kernel(name: str) -> None:
    table = {row.name:row for row in rows()}
    receipt = replay_candidate_bodies((table[name],),core=core()|table)[0]
    assert (receipt.proof_nodes,receipt.proof_depth) == EXPECTED_BODY_METRICS[name]
    assert receipt.proof_objects == receipt.proof_nodes
    gc.collect()
