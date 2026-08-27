"""Kernel authoring tests for integer-representation-independent rank."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import Eq, Forall, Imp, parse_formula_with_names
from peano_lab.kernel.terms import Add, Var
from peano_lab.library import matrix_integer_invariance_candidate as determinant_candidate
from peano_lab.library.matrix_rank_integer_invariance_candidate import make_matrix_rank_integer_invariance_candidate_theorems
from peano_lab.library.theorems import TheoremSpec
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from test_matrix_integer_invariance_candidate import core as previous_core, rows as determinant_integer_rows
from test_matrix_integer_invariance_candidate import EXPECTED_BODY_METRICS as DETERMINANT_METRICS


EXPECTED_NAMES = (
    'matrix_integer_rectangular_index_bound',
    'matrix_integer_selected_point_at_source',
    'matrix_integer_selected_point_balance',
    'matrix_integer_selected_prefix_point_at',
    'matrix_integer_signed_selected_balance',
    'matrix_integer_selected_determinant_balance',
    'matrix_integer_nonzero_pair_transport',
    'matrix_integer_nonzero_minor_transport',
    'matrix_integer_all_minors_zero_transport',
    'rectangular_matrix_rank_integer_transport',
    'rectangular_matrix_rank_integer_invariant',
)
EXPECTED_BODY_METRICS = dict(zip(EXPECTED_NAMES, (
    (32,17),(264,46),(214,59),(49,28),(369,120),(219,123),
    (33,22),(105,62),(167,92),(150,59),(102,60),
), strict=True))
EXPECTED_ROOTS = {
    'signed_recursive_determinant_integer_invariant': 'a5587046845e712ff96b73c8fc4f54b9ecfeac5cfa224a1d537c6ce20f728dd6',
    'matrix_integer_selected_determinant_balance': 'ce316f11e1f76b73f309ed93e0edbd90a6093640070b23a2e89bde0dbad646ca',
    'matrix_integer_nonzero_minor_transport': '61dcef1f59cd2521eec297baf5fc267e5d8865ac38c93f443d25d988610f8701',
    'rectangular_matrix_rank_integer_transport': '31c60117ba9ac510fc66cbf317833db9b0133579b2f36bc93fb1393d23ec6c93',
    'rectangular_matrix_rank_integer_invariant': 'd6c74c06c5a55da7ec89d026a4658e49604b6f6b11521d1b453c8bfa16168151',
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return make_matrix_rank_integer_invariance_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str,TheoremSpec]:
    return previous_core()|{row.name:row for row in determinant_integer_rows()}


@lru_cache(maxsize=1)
def combined_rows() -> tuple[TheoremSpec, ...]:
    return (*determinant_integer_rows(),*rows())


def test_integer_invariance_inventory_is_exact_fresh_ordered_and_constructive() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sum(len(row.dependencies) for row in rows()) == 28
    assert sum(len(row.script) for row in rows()) == 721
    combined = combined_rows()
    assert len(combined) == 27
    assert sum(len(row.dependencies) for row in combined) == 68
    assert sum(len(row.script) for row in combined) == 1_929
    assert sha256('\n'.join(row.name for row in combined).encode()).hexdigest() == '7f6b47dca5abc0570871683bc2a8ec9ba10114761ae6a148d7450423fc85fae0'
    metrics = DETERMINANT_METRICS|EXPECTED_BODY_METRICS
    assert sum(nodes for nodes,depth in metrics.values()) == 3_702
    assert max(nodes for nodes,depth in metrics.values()) == 369
    assert max(depth for nodes,depth in metrics.values()) == 137
    available = set(previous_core())
    for row in combined:
        _,names = parse_formula_with_names(row.statement)
        assert not names
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert not any(command in {'admit','sorry'} or 'DNE' in command or command.startswith('use ') for command in row.script)
        assert all(any(dependency in command.split() for command in row.script) for dependency in row.dependencies)
        available.add(row.name)


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_actual_rank_integer_invariance_body_passes_unchanged_kernel(name: str) -> None:
    table = {row.name:row for row in rows()}
    receipt = replay_candidate_bodies((table[name],),core=core()|table)[0]
    assert (receipt.proof_nodes,receipt.proof_depth) == EXPECTED_BODY_METRICS[name]
    assert receipt.proof_objects == receipt.proof_nodes
    gc.collect()


@pytest.mark.parametrize('name',tuple(row.name for row in combined_rows()))
def test_false_integer_invariance_conclusions_are_rejected(name: str) -> None:
    table = {row.name:row for row in combined_rows()}
    row = table[name]
    forged = replace(row,statement=f'({row.statement}) /\\ false')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,),core=core()|table)
    gc.collect()


@pytest.mark.parametrize('name',EXPECTED_ROOTS)
def test_integer_invariance_principal_statements_are_pinned(name: str) -> None:
    row = next(row for row in combined_rows() if row.name == name)
    assert sha256(row.statement.encode()).hexdigest() == EXPECTED_ROOTS[name]


@pytest.mark.parametrize('name',EXPECTED_ROOTS)
def test_missing_integer_invariance_root_dependencies_are_rejected(name: str) -> None:
    table = {row.name:row for row in combined_rows()}
    row = table[name]
    forged = replace(row,dependencies=row.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,),core=core()|table)
    gc.collect()


SURFACE_ARGUMENTS = ('ab','ac','bb','bc','eb','ec','fb','fc','r','w')


def test_integer_matrix_equality_is_alpha_invariant_and_has_exact_free_arguments() -> None:
    first,names = parse_formula_with_names(determinant_candidate.integer_matrix_entrywise_equal_relation(*SURFACE_ARGUMENTS,tag='first'))
    second,other_names = parse_formula_with_names(determinant_candidate.integer_matrix_entrywise_equal_relation(*SURFACE_ARGUMENTS,tag='second'))
    assert names == other_names and set(names) == set(SURFACE_ARGUMENTS)
    assert first == second
    for _ in range(5):
        assert type(first) is Forall
        first = first.body
    for _ in range(5):
        assert type(first) is Imp
        first = first.right
    assert first == Eq(Add(Var(3),Var(0)),Add(Var(1),Var(2)))


@pytest.mark.parametrize('bad', ('','S','forall','x) -> false','ff_capture','fs_capture','mdr_capture','mdm_capture','mce_capture','mcp_capture','fom_capture','ics_capture'))
def test_integer_matrix_equality_rejects_all_nested_binder_capture(bad: str) -> None:
    with pytest.raises(ValueError):
        determinant_candidate.integer_matrix_entrywise_equal_relation(bad,*SURFACE_ARGUMENTS[1:],tag='safe')


@pytest.mark.parametrize('bad', ('','S','forall','bad tag','x) -> false',17))
def test_integer_matrix_equality_rejects_invalid_tags(bad) -> None:
    with pytest.raises(ValueError):
        determinant_candidate.integer_matrix_entrywise_equal_relation(*SURFACE_ARGUMENTS,tag=bad)


def test_integer_matrix_equality_rejects_argument_aliasing() -> None:
    with pytest.raises(ValueError):
        determinant_candidate.integer_matrix_entrywise_equal_relation(SURFACE_ARGUMENTS[1],*SURFACE_ARGUMENTS[1:],tag='safe')


def _after_foralls(name: str,count: int):
    row = next(row for row in combined_rows() if row.name == name)
    formula,names = parse_formula_with_names(row.statement)
    assert not names
    for _ in range(count):
        assert type(formula) is Forall
        formula = formula.body
    return formula


def test_determinant_root_requires_only_entrywise_integer_equality_and_two_actual_evaluations() -> None:
    formula = _after_foralls('signed_recursive_determinant_integer_invariant',13)
    for _ in range(3):
        assert type(formula) is Imp
        formula = formula.right
    assert formula == Eq(Add(Var(3),Var(0)),Add(Var(1),Var(2)))


def test_rank_root_requires_only_integer_equality_and_two_actual_rank_certificates() -> None:
    formula = _after_foralls('rectangular_matrix_rank_integer_invariant',12)
    for _ in range(3):
        assert type(formula) is Imp
        formula = formula.right
    assert formula == Eq(Var(1),Var(0))


def test_unsupported_component_equality_cannot_replace_integer_determinant_invariance() -> None:
    table = {row.name:row for row in combined_rows()}
    row = table['signed_recursive_determinant_integer_invariant']
    prefix = 'mdr_'
    suffix = '_determinant_integer_invariance'
    p,n,P,N = tuple(prefix+name+suffix for name in ('p','n','P','N'))
    balance = f'{p} + {N} = {P} + {n}'
    assert row.statement.count(balance) == 1
    forged = replace(row,statement=row.statement.replace(balance,f'{p} = {P}'))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,),core=core()|table)
    gc.collect()
