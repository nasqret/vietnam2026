"""Kernel authoring checks for actual positive absolute-determinant data."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, Or, parse_formula_with_names
from peano_lab.kernel.terms import Add, Var, Zero
from peano_lab.library import matrix_lattice_data_candidate as candidate
from peano_lab.library.matrix_lattice_data_candidate import make_matrix_lattice_data_candidate_theorems
from peano_lab.library.theorems import TheoremSpec
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from test_matrix_rank_integer_invariance_candidate import core as previous_core, rows as integer_rank_rows


EXPECTED_NAMES = (
    'matrix_lattice_absolute_difference_exists',
    'matrix_lattice_opposite_gaps_zero',
    'matrix_lattice_absolute_difference_functional',
    'matrix_lattice_absolute_nonzero_of_pair',
    'matrix_lattice_pair_nonzero_of_absolute',
    'matrix_lattice_positive_gap_integer_transport',
    'matrix_lattice_absolute_difference_integer_transport',
    'absolute_recursive_determinant_exists',
    'absolute_recursive_determinant_functional',
    'absolute_recursive_determinant_integer_transport',
    'positive_determinant_matrix_data_from_nonzero',
    'positive_determinant_matrix_data_nonzero',
    'positive_determinant_matrix_data_functional',
    'positive_determinant_matrix_data_integer_transport',
    'matrix_lattice_identity_selector_exists',
    'matrix_lattice_identity_is_selector',
    'matrix_lattice_identity_selected_natural',
    'matrix_lattice_identity_selected_signed',
    'matrix_lattice_nonzero_full_determinant_minor',
    'square_matrix_full_rank_from_nonzero_determinant',
    'positive_determinant_matrix_data_full_rank',
    'absolute_recursive_determinant_exists_unique',
    'positive_determinant_matrix_data_exists_unique',
)
EXPECTED_BODY_METRICS = dict(zip(EXPECTED_NAMES, (
    (33,13),(63,19),(76,20),(25,13),(56,21),(44,25),(102,39),(26,15),
    (102,34),(63,41),(36,24),(60,36),(75,43),(78,46),(23,14),(103,38),
    (82,34),(61,24),(136,44),(102,43),(35,21),(31,22),(44,27),
), strict=True))
EXPECTED_ROOTS = {
    'absolute_recursive_determinant_integer_transport': '8f50298612b0267d593aa106fa8722ac1edf793d563c064dc8eb3eab275d849c',
    'positive_determinant_matrix_data_from_nonzero': '71e52ed035563f3fd9d3dd4405b268c2075fb9647aa416aec13fc5ae1a32218f',
    'positive_determinant_matrix_data_integer_transport': 'f547bacaba8b888843c43400e24cfb502e99d6b14abc3f1895a77a64210217dd',
    'square_matrix_full_rank_from_nonzero_determinant': '4c54da0a9e91e210d5a9f1d93711e28706532e435a889f22a8beb470abe4bb1a',
    'positive_determinant_matrix_data_full_rank': '2d861924f0f0b78f626e57e1521a2fa6145abe7bf1eadae069ecd2a906b20b48',
    'absolute_recursive_determinant_exists_unique': '1a01953c2267c95c0c92fb0b853dade02a33fbf1dbee71af3dfa3a97378bcad8',
    'positive_determinant_matrix_data_exists_unique': '2d8c3aec5c5751dc8325a28477c9b6c7b7ddd8d8cd20bcc719d7af518bcc2676',
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return make_matrix_lattice_data_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str,TheoremSpec]:
    return previous_core()|{row.name:row for row in integer_rank_rows()}


def test_positive_matrix_data_inventory_is_exact_fresh_ordered_and_constructive() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sum(len(row.dependencies) for row in rows()) == 52
    assert sum(len(row.script) for row in rows()) == 816
    assert sha256('\n'.join(row.name for row in rows()).encode()).hexdigest() == '18f9162bf5b71d117c798edb2ac391cdd8021486690208fc91a489233ea4c54f'
    assert sum(nodes for nodes,depth in EXPECTED_BODY_METRICS.values()) == 1_456
    assert max(nodes for nodes,depth in EXPECTED_BODY_METRICS.values()) == 136
    assert max(depth for nodes,depth in EXPECTED_BODY_METRICS.values()) == 46
    available = set(core())
    for row in rows():
        _,names = parse_formula_with_names(row.statement)
        assert not names
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert not any(command in {'admit','sorry'} or 'DNE' in command or command.startswith('use ') for command in row.script)
        assert all(any(dependency in command.split() for command in row.script) for dependency in row.dependencies)
        available.add(row.name)


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_actual_matrix_data_body_passes_unchanged_kernel(name: str) -> None:
    table = {row.name:row for row in rows()}
    receipt = replay_candidate_bodies((table[name],),core=core()|table)[0]
    assert (receipt.proof_nodes,receipt.proof_depth) == EXPECTED_BODY_METRICS[name]
    shared = 1 if name == 'matrix_lattice_opposite_gaps_zero' else 0
    assert receipt.proof_objects == receipt.proof_nodes - shared
    assert receipt.reused_objects == shared
    gc.collect()


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_false_matrix_data_conclusions_are_rejected(name: str) -> None:
    table = {row.name:row for row in rows()}
    row = table[name]
    forged = replace(row,statement=f'({row.statement}) /\\ false')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,),core=core()|table)
    gc.collect()


@pytest.mark.parametrize('name', EXPECTED_ROOTS)
def test_matrix_data_principal_statements_are_exactly_pinned(name: str) -> None:
    row = next(row for row in rows() if row.name == name)
    assert sha256(row.statement.encode()).hexdigest() == EXPECTED_ROOTS[name]


@pytest.mark.parametrize('name', EXPECTED_ROOTS)
def test_matrix_data_missing_root_dependencies_are_rejected(name: str) -> None:
    table = {row.name:row for row in rows()}
    row = table[name]
    forged = replace(row,dependencies=row.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,),core=core()|table)
    gc.collect()


SURFACES = (
    (candidate.absolute_recursive_determinant_relation,('ab','ac','bb','bc','d','D')),
    (candidate.positive_determinant_matrix_data_relation,('ab','ac','bb','bc','d','D')),
    (candidate.identity_matrix_selector_relation,('b','c','length')),
)


@pytest.mark.parametrize('builder,arguments', SURFACES)
def test_matrix_data_definitions_are_exact_hygienic_surfaces(builder,arguments) -> None:
    first,names = parse_formula_with_names(builder(*arguments,tag='first'))
    second,other_names = parse_formula_with_names(builder(*arguments,tag='second'))
    assert first == second
    assert names == other_names and set(names) == set(arguments)


@pytest.mark.parametrize('builder,arguments', SURFACES)
@pytest.mark.parametrize('bad', ('','S','forall','x) -> false','ff_capture','fs_capture','mdr_capture','mdm_capture','mce_capture','mcp_capture','fom_capture','ics_capture'))
def test_matrix_data_definitions_reject_inherited_and_new_binder_capture(builder,arguments,bad) -> None:
    with pytest.raises(ValueError):
        builder(bad,*arguments[1:],tag='safe')


@pytest.mark.parametrize('builder,arguments', SURFACES)
@pytest.mark.parametrize('bad', ('','S','forall','bad tag','x) -> false',17))
def test_matrix_data_definitions_reject_malformed_tags(builder,arguments,bad) -> None:
    with pytest.raises(ValueError):
        builder(*arguments,tag=bad)


@pytest.mark.parametrize('builder,arguments', SURFACES)
def test_matrix_data_definitions_reject_argument_aliases(builder,arguments) -> None:
    with pytest.raises(ValueError):
        builder(arguments[1],*arguments[1:],tag='safe')


def _after_foralls(name: str,count: int):
    row = next(row for row in rows() if row.name == name)
    formula,names = parse_formula_with_names(row.statement)
    assert not names
    for _ in range(count):
        assert type(formula) is Forall
        formula = formula.body
    return formula


def test_positive_matrix_data_requires_both_positive_dimension_and_positive_actual_absolute_determinant() -> None:
    formula,names = parse_formula_with_names(candidate.positive_determinant_matrix_data_relation('ab','ac','bb','bc','d','D',tag='audit'))
    assert type(formula) is And and type(formula.right) is And
    assert formula.left == Imp(Eq(Var(names.index('d')),Zero()),Bot())
    assert formula.right.left == Imp(Eq(Var(names.index('D')),Zero()),Bot())
    absolute = formula.right.right
    assert type(absolute) is Exists and type(absolute.body) is Exists
    values = absolute.body.body
    assert type(values) is And and type(values.left) is Exists  # actual determinant history
    assert type(values.right) is Or
    left,right = values.right.left,values.right.right
    assert type(left) is Eq and type(right) is Eq
    assert type(left.right) is Add and type(right.right) is Add
    assert left.left == right.right.left
    assert right.left == left.right.left
    assert left.right.right == right.right.right


def test_positive_data_constructor_requires_actual_nonzero_det_but_not_assumed_data() -> None:
    formula = _after_foralls('positive_determinant_matrix_data_exists_unique',7)
    assert type(formula) is Imp
    assert formula.left == Imp(Eq(Var(2),Zero()),Bot())
    assert type(formula.right) is Imp and type(formula.right.left) is Exists
    assert type(formula.right.right) is Imp
    assert formula.right.right.left == Imp(Eq(Var(1),Var(0)),Bot())
    result = formula.right.right.right
    assert type(result) is Exists and type(result.body) is And
    assert type(result.body.left) is And and type(result.body.right) is Forall


def test_full_rank_root_includes_dimension_zero_without_a_positivity_premise() -> None:
    formula = _after_foralls('square_matrix_full_rank_from_nonzero_determinant',7)
    assert type(formula) is Imp and type(formula.left) is Exists
    assert type(formula.right) is Imp
    assert formula.right.left == Imp(Eq(Var(1),Var(0)),Bot())
    assert type(formula.right.right) is And
