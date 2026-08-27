"""Original-kernel authoring audit for genuine recursive matrix determinants.

Read the immutable parent *scripts* as data: importing every historic edition
alone costs roughly 700 MiB.  These tests still replay every candidate body;
they are not a full dependency-closure or Alpha admission receipt.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import matrix_recursive_determinant_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec


ROOT = Path(__file__).resolve().parents[3]
PARENT_CATALOG = ROOT / 'artifacts/peano-library/alpha/catalog-v26.json'
PARENT_CATALOG_SHA256 = '969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534'
EXPECTED_NAMES = (
    'matrix_recursive_node_code_exists',
    'matrix_recursive_prefix_refl',
    'matrix_recursive_prefix_trans',
    'matrix_recursive_prefix_restrict',
    'matrix_recursive_record_transport',
    'matrix_recursive_record_append',
    'matrix_recursive_empty_history',
    'matrix_recursive_children_transport',
    'matrix_recursive_step_transport',
    'matrix_recursive_history_transport',
    'matrix_recursive_history_extend',
    'matrix_recursive_zero_extension',
    'matrix_recursive_children_empty',
    'matrix_recursive_children_recode',
    'matrix_recursive_children_extend',
    'matrix_recursive_cofactor_prefix_from_recursion',
    'matrix_recursive_successor_extension',
    'matrix_recursive_all_extensions',
    'signed_recursive_determinant_exists',
    'matrix_recursive_node_code_injective',
    'matrix_recursive_record_injective',
    'matrix_recursive_history_step_at',
    'signed_recursive_determinant_zero_value',
    'signed_recursive_determinant_successor_decomposition',
)
EXPECTED_BODY_METRICS = dict(zip(EXPECTED_NAMES, (
    (24,19), (8,8), (38,25), (42,28), (42,30), (39,22),
    (17,13), (97,56), (128,74), (93,44), (97,49), (51,24),
    (27,23), (81,46), (126,61), (269,66), (136,43), (13,9),
    (48,25), (429,49), (61,41), (616,69), (60,29), (309,77),
), strict=True))


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_matrix_recursive_determinant_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    raw = PARENT_CATALOG.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_CATALOG_SHA256
    snapshot = json.loads(raw)
    assert snapshot['schema'] == 'peano-library-alpha-snapshot-v26'
    assert snapshot['checked_use_count'] == snapshot['theorem_count'] == 2_138
    assert snapshot['stable_count'] == 432
    assert all(item['checked_use'] and item['body_checked'] for item in snapshot['theorems'])
    return {
        item['name']: TheoremSpec(
            item['name'], item['statement'], tuple(item['dependencies']),
            tuple(item['script']), item['summary'],
        )
        for item in snapshot['theorems']
    }


def replay_one(name: str):
    table = {item.name: item for item in rows()}
    try:
        return replay_candidate_bodies((table[name],), core=core() | table)[0]
    finally:
        gc.collect()


def test_recursive_matrix_inventory_is_closed_fresh_ordered_and_constructive() -> None:
    assert tuple(item.name for item in rows()) == EXPECTED_NAMES
    available = set(core())
    for item in rows():
        _, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert item.name not in available
        assert set(item.dependencies) <= available
        assert item.script
        assert not any(
            command in {'sorry', 'admit'} or 'DNE' in command or command.startswith('use ')
            for command in item.script
        )
        available.add(item.name)


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_every_recursive_matrix_body_passes_unchanged_kernel(name: str) -> None:
    receipt = replay_one(name)
    assert receipt.name == name
    assert (receipt.proof_nodes, receipt.proof_depth) == EXPECTED_BODY_METRICS[name]
    expected_objects = 288 if name == 'signed_recursive_determinant_successor_decomposition' else receipt.proof_nodes
    assert receipt.proof_objects == expected_objects
    assert receipt.reused_objects == receipt.proof_nodes - expected_objects


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_a_forged_false_recursive_matrix_conclusion_is_rejected(name: str) -> None:
    table = {item.name: item for item in rows()}
    row = table[name]
    forged = replace(row, statement=f'({row.statement}) /\\ false')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=core() | table)
    gc.collect()


SURFACES = (
    (candidate.signed_determinant_node_code_relation, ('z','d','pb','pc','nb','nc','p','n')),
    (candidate.signed_determinant_history_relation, ('b','c','l')),
    (candidate.signed_recursive_determinant_relation, ('pb','pc','nb','nc','d','p','n')),
    (candidate.signed_evaluated_cofactor_relation, ('pb','pc','nb','nc','q','eb','ec','fb','fc')),
)


@pytest.mark.parametrize('builder,arguments', SURFACES)
def test_recursive_matrix_surfaces_are_exact_and_hygienic(builder, arguments) -> None:
    first, first_names = parse_formula_with_names(builder(*arguments, tag='first'))
    second, second_names = parse_formula_with_names(builder(*arguments, tag='second'))
    assert set(first_names) == set(arguments)
    assert first_names == second_names
    assert first == second


@pytest.mark.parametrize('builder,arguments', SURFACES)
@pytest.mark.parametrize('bad', ('', 'S', 'forall', 'x) -> false', 'ff_capture', 'mdr_capture'))
def test_recursive_matrix_surfaces_reject_injection_and_capture(builder, arguments, bad) -> None:
    with pytest.raises(candidate.MatrixRecursiveDeterminantError):
        builder(bad, *arguments[1:], tag='safe')


@pytest.mark.parametrize('builder,arguments', SURFACES)
def test_recursive_matrix_surfaces_reject_argument_aliasing(builder, arguments) -> None:
    with pytest.raises(candidate.MatrixRecursiveDeterminantError):
        builder(arguments[1], *arguments[1:], tag='safe')
