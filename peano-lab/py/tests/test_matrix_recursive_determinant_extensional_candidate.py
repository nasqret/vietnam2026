"""Exact unrestricted determinant endpoints and actual matrix extensionality.

Candidate bodies are checked with explicit dependency hypotheses; final
release admission must additionally check their complete proof closure.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library import matrix_recursive_determinant_extensional_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec
from test_matrix_recursive_determinant_candidate import core as parent_core, rows as construction_rows


EXPECTED_NAMES = (
    'matrix_recursive_lt_add_left',
    'matrix_recursive_flattened_index_bound',
    'matrix_recursive_quotient_row_bound',
    'matrix_recursive_minor_cell_transport',
    'matrix_recursive_minor_prefix_transport',
    'matrix_recursive_minor_prefix_functional',
    'matrix_recursive_signed_minor_extensional',
    'matrix_recursive_alternating_prefix_transport',
    'matrix_recursive_alternating_fold_transport',
    'matrix_recursive_alternating_fold_extensional',
    'matrix_recursive_matrix_equality_refl',
    'matrix_recursive_initial_row_prefix',
    'matrix_recursive_cofactor_streams_from_functionality',
    'matrix_recursive_determinant_extensional',
    'signed_recursive_determinant_functional',
    'signed_recursive_determinant_exists_unique',
    'signed_recursive_determinant_from_evaluated_cofactors',
    'signed_recursive_determinant_cofactor_equation',
    'signed_recursive_determinant_empty',
    'signed_recursive_determinant_empty_equation',
)
EXPECTED_BODY_METRICS = dict(zip(EXPECTED_NAMES, (
    (15,11), (31,16), (41,22), (63,32), (70,37), (495,49),
    (80,37), (113,53), (152,90), (76,56), (33,14), (52,31),
    (364,70), (225,59), (92,53), (37,27), (707,62), (108,44),
    (46,21), (81,29),
), strict=True))
EXPECTED_ROOTS = {
    'matrix_recursive_determinant_extensional': 'dace324499adf4c189d80c2baf86a14f915f992f0e2e40e0c7cf832f86df3167',
    'signed_recursive_determinant_functional': 'e74f2e95ad138c1a12439ed2b74415cd5a0fd02218ebbe7ed5a32e615b53ef52',
    'signed_recursive_determinant_exists_unique': 'bf78d0b39617ddaabf5e7b617a4e5474ee57d308c14d296de7a54e93d42d0dbc',
    'signed_recursive_determinant_cofactor_equation': '584c7cd696d0844f5748f21a45f4a408b3a321ad64097c2a5bebfc623194970d',
    'signed_recursive_determinant_empty_equation': 'cd74d5fd1dda41357c2a9cbbbec952fe1d8bcd2c3d9c7b21f85b4125daba7cb0',
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_matrix_recursive_determinant_extensional_candidate_theorems(TheoremSpec)


def core() -> dict[str, TheoremSpec]:
    return parent_core() | {item.name: item for item in construction_rows()}


def test_extensional_inventory_is_fresh_ordered_closed_and_constructive() -> None:
    assert tuple(item.name for item in rows()) == EXPECTED_NAMES
    assert len(construction_rows()) == 24
    assert sum(len(item.dependencies) for item in rows()) == 51
    assert sum(len(item.script) for item in rows()) == 1_193
    combined = (*construction_rows(), *rows())
    assert len(combined) == 44
    assert sum(len(item.dependencies) for item in combined) == 104
    assert sum(len(item.script) for item in combined) == 2_611
    assert sha256('\n'.join(item.name for item in combined).encode()).hexdigest() == (
        '06dd3bc157a99bd9a7aafac8208ea5daf82682d346160be137dc68878cb44aa9'
    )
    available = set(core())
    for item in rows():
        _, names = parse_formula_with_names(item.statement)
        assert not names
        assert item.name not in available
        assert set(item.dependencies) <= available
        assert not any(
            command in {'sorry','admit'} or 'DNE' in command or command.startswith('use ')
            for command in item.script
        )
        assert all(any(dependency in command.split() for command in item.script) for dependency in item.dependencies)
        available.add(item.name)


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_every_extensional_matrix_body_passes_unchanged_kernel(name: str) -> None:
    table = {item.name: item for item in rows()}
    receipt = replay_candidate_bodies((table[name],),core=core() | table)[0]
    assert receipt.name == name
    assert (receipt.proof_nodes, receipt.proof_depth) == EXPECTED_BODY_METRICS[name]
    assert receipt.proof_objects == receipt.proof_nodes
    gc.collect()


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_false_extensional_conclusions_are_rejected(name: str) -> None:
    table = {item.name: item for item in rows()}
    row = table[name]
    forged = replace(row,statement=f'({row.statement}) /\\ false')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,),core=core() | table)
    gc.collect()


@pytest.mark.parametrize('name', EXPECTED_ROOTS)
def test_every_principal_endpoint_has_its_exact_reviewed_statement(name: str) -> None:
    row = next(item for item in rows() if item.name == name)
    assert sha256(row.statement.encode()).hexdigest() == EXPECTED_ROOTS[name]


@pytest.mark.parametrize('name', EXPECTED_ROOTS)
def test_missing_root_proof_dependencies_are_rejected(name: str) -> None:
    table = {item.name: item for item in rows()}
    row = table[name]
    forged = replace(row,dependencies=row.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,),core=core() | table)
    gc.collect()


def _after_foralls(name: str, count: int):
    row = next(item for item in rows() if item.name == name)
    formula, names = parse_formula_with_names(row.statement)
    assert not names
    for _ in range(count):
        assert type(formula) is Forall
        formula = formula.body
    return formula


def test_exists_unique_has_no_assumed_recursion_or_dimension_bound() -> None:
    formula = _after_foralls('signed_recursive_determinant_exists_unique',5)
    assert type(formula) is Exists
    assert type(formula.body) is Exists
    result = formula.body.body
    assert type(result) is And
    assert type(result.left) is Exists  # actual history, not a bare numerical sum
    assert type(result.right) is Forall
    assert type(result.right.body) is Forall
    assert type(result.right.body.body) is Imp


def test_unconditional_functionality_takes_only_two_actual_evaluations() -> None:
    formula = _after_foralls('signed_recursive_determinant_functional',9)
    assert type(formula) is Imp and type(formula.left) is Exists
    assert type(formula.right) is Imp and type(formula.right.left) is Exists
    assert type(formula.right.right) is And


@pytest.mark.parametrize('name,count', (
    ('signed_recursive_determinant_cofactor_equation',7),
    ('signed_recursive_determinant_empty_equation',6),
))
def test_both_recursive_boundary_equations_are_genuine_iffs(name: str, count: int) -> None:
    formula = _after_foralls(name,count)
    assert type(formula) is And
    assert type(formula.left) is Imp
    assert type(formula.right) is Imp
    assert formula.left.left == formula.right.right
    assert formula.left.right == formula.right.left


def test_signed_matrix_equality_is_a_hygienic_finite_entry_relation() -> None:
    arguments = ('pb','pc','nb','nc','qb','qc','rb','rc','d')
    first, names = parse_formula_with_names(candidate.signed_matrix_prefix_equality_relation(*arguments,tag='first'))
    second, other_names = parse_formula_with_names(candidate.signed_matrix_prefix_equality_relation(*arguments,tag='second'))
    assert set(names) == set(arguments)
    assert names == other_names
    assert first == second
    assert type(first) is And
    assert type(first.left) is Forall and type(first.right) is Forall


@pytest.mark.parametrize('bad', ('', 'S', 'forall', 'x) -> false', 'ff_capture', 'mdr_capture'))
def test_matrix_equality_rejects_formula_injection_or_capture(bad: str) -> None:
    with pytest.raises(ValueError):
        candidate.signed_matrix_prefix_equality_relation(bad,'pc','nb','nc','qb','qc','rb','rc','d',tag='safe')
