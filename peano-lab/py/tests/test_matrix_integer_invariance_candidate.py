"""Original-kernel authoring checks for true integer matrix semantics."""

from __future__ import annotations

from functools import lru_cache
import gc

import pytest

from peano_lab.library.matrix_integer_invariance_candidate import make_matrix_integer_invariance_candidate_theorems
from peano_lab.library.theorems import TheoremSpec
from peano_lab.library.candidate_validation import replay_candidate_bodies
from test_matrix_rank_certificate_candidate import core as rank_core, rows as rank_rows


EXPECTED_NAMES = (
    'matrix_integer_vector_equality_restrict',
    'matrix_integer_vector_equality_symmetric',
    'matrix_integer_pair_product_balance',
    'matrix_integer_pair_negation_balance',
    'matrix_integer_cofactor_term_balance',
    'matrix_integer_signed_sum_balance',
    'matrix_integer_alternating_prefix_balance',
    'matrix_integer_cofactor_fold_balance',
    'matrix_integer_minor_cell_at_source',
    'matrix_integer_minor_cell_balance',
    'matrix_integer_minor_prefix_cell_at_coordinates',
    'matrix_integer_square_index_width_nonzero',
    'matrix_integer_signed_minor_balance',
    'matrix_integer_cofactor_streams_from_recursion',
    'matrix_integer_first_row_equality',
    'signed_recursive_determinant_integer_invariant',
)
EXPECTED_BODY_METRICS = dict(zip(EXPECTED_NAMES, (
    (70,47),(62,42),(54,25),(16,11),(139,38),(123,50),(225,75),(246,137),
    (70,27),(128,44),(228,41),(18,11),(184,62),(172,74),(72,43),(191,57),
), strict=True))


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return make_matrix_integer_invariance_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str,TheoremSpec]:
    return rank_core()|{row.name:row for row in rank_rows()}


def test_integer_determinant_inventory_is_exact() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sum(len(row.dependencies) for row in rows()) == 40
    assert sum(len(row.script) for row in rows()) == 1_208


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_actual_integer_invariance_body_passes_unchanged_kernel(name: str) -> None:
    table = {row.name:row for row in rows()}
    receipt = replay_candidate_bodies((table[name],),core=core()|table)[0]
    assert (receipt.proof_nodes,receipt.proof_depth) == EXPECTED_BODY_METRICS[name]
    assert receipt.proof_objects == receipt.proof_nodes
    gc.collect()
