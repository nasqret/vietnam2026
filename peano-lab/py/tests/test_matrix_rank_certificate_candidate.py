"""Original-kernel candidate checks for genuine finite rectangular rank."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, Or, parse_formula_with_names
from peano_lab.kernel.terms import Var
from peano_lab.library import matrix_rank_certificate_candidate as candidate
from peano_lab.library import matrix_rank_finite_coding_candidate as coding
from peano_lab.library import matrix_rank_selected_minors_candidate as selected
from peano_lab.library.matrix_rank_certificate_candidate import make_matrix_rank_certificate_candidate_theorems
from peano_lab.library.theorems import TheoremSpec
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from test_matrix_rank_selected_minors_candidate import core as previous_core, rows as selected_rows
from test_matrix_rank_finite_coding_candidate import rows as coding_rows, EXPECTED_BODY_METRICS as CODING_METRICS
from test_matrix_rank_selected_minors_candidate import EXPECTED_BODY_METRICS as SELECTED_METRICS
from test_matrix_recursive_determinant_candidate import core as immutable_parent_core, rows as construction_rows
from test_matrix_recursive_determinant_extensional_candidate import rows as extensional_rows


EXPECTED_NAMES = (
    'matrix_rank_selected_column_search_decidable',
    'matrix_rank_selected_box_search_decidable',
    'matrix_rank_nonzero_minor_recode_in_box',
    'matrix_rank_nonzero_minor_of_box_search',
    'matrix_rank_nonzero_minor_decidable',
    'matrix_rank_le_successor_cases',
    'matrix_rank_maximal_nonzero_prefix_exists',
    'matrix_rank_all_minors_zero_from_absence',
    'matrix_rank_absence_from_all_minors_zero',
    'rectangular_matrix_rank_certificate_exists',
    'rectangular_matrix_rank_functional',
    'rectangular_matrix_rank_exists_unique',
    'rectangular_matrix_rank_successor_minors_zero',
    'rectangular_matrix_rank_zero_rows',
    'rectangular_matrix_rank_zero_columns',
)
EXPECTED_BODY_METRICS = dict(zip(EXPECTED_NAMES, (
    (93,32),(93,32),(74,44),(37,27),(73,34),(24,12),(134,44),
    (45,35),(78,44),(83,30),(153,63),(34,24),(44,27),(130,30),(149,31),
), strict=True))
EXPECTED_ROOTS = {
    'matrix_rank_uniform_beta_prefix_box_exists': '15c6b9386a3c36f27f5f5a76d419c121b626d7c50820bf597df47f419e21b10d',
    'matrix_rank_nonzero_minor_decidable': 'c812aebcf57562a0329c87152300bcdb9869df14ea5b6a8dfe4c369c6894ef35',
    'rectangular_matrix_rank_certificate_exists': 'b15d9a29141b595d7e4ab2d4fe79f2769f1383c6577f6d7dc5a663589ba01162',
    'rectangular_matrix_rank_functional': '353acf899f374f9e1f1c6b712706581aa5f0e6b788149b8bec3c2a93ae7e7e4f',
    'rectangular_matrix_rank_exists_unique': '677f945b5341792d5b2281cc8948922456c461c1aeeec880c452199df7d178f1',
    'rectangular_matrix_rank_successor_minors_zero': '3f79bf62134e5de89064d0a4181a1e00ff647b3b309498c1b127c30da468de9d',
    'rectangular_matrix_rank_zero_rows': '765ceba74046ef82f0240d2a0ff9f0dbd14c825fe4925c863ca410aa789dab09',
    'rectangular_matrix_rank_zero_columns': '309d9d31028f91e3bb963f6909368a416b3a33469bfd6e6330a515b38a43a850',
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return make_matrix_rank_certificate_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str,TheoremSpec]:
    return previous_core()|{row.name:row for row in selected_rows()}


@lru_cache(maxsize=1)
def all_rank_rows() -> tuple[TheoremSpec, ...]:
    return (*coding_rows(),*selected_rows(),*rows())


def test_rank_inventory_is_exact_fresh_ordered_closed_and_constructive() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sum(len(row.dependencies) for row in rows()) == 38
    assert sum(len(row.script) for row in rows()) == 709
    combined = all_rank_rows()
    assert len(combined) == 55
    assert sum(len(row.dependencies) for row in combined) == 125
    assert sum(len(row.script) for row in combined) == 2_345
    assert sha256('\n'.join(row.name for row in combined).encode()).hexdigest() == '2fd23d962c15888ebacae62d9f8a718f376e0287cfc0a992abbcb42b38e645ad'
    metrics = CODING_METRICS | SELECTED_METRICS | EXPECTED_BODY_METRICS
    assert sum(nodes for nodes,depth in metrics.values()) == 4_104
    assert max(nodes for nodes,depth in metrics.values()) == 317
    assert max(depth for nodes,depth in metrics.values()) == 102
    available = set(immutable_parent_core())|{row.name for row in (*construction_rows(),*extensional_rows())}
    for row in combined:
        _,free_names = parse_formula_with_names(row.statement)
        assert not free_names
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert row.script
        assert not any(command in {'admit','sorry'} or 'DNE' in command or command.startswith('use ') for command in row.script)
        assert all(any(dependency in command.split() for command in row.script) for dependency in row.dependencies)
        available.add(row.name)


@pytest.mark.parametrize('name', EXPECTED_NAMES)
def test_actual_rank_certificate_body_passes_unchanged_kernel(name: str) -> None:
    table = {row.name:row for row in rows()}
    receipt = replay_candidate_bodies((table[name],),core=core()|table)[0]
    assert (receipt.proof_nodes,receipt.proof_depth) == EXPECTED_BODY_METRICS[name]
    assert receipt.proof_objects == receipt.proof_nodes
    gc.collect()


@pytest.mark.parametrize('name', tuple(row.name for row in all_rank_rows()))
def test_forged_false_rank_conclusions_are_rejected(name: str) -> None:
    table = {row.name:row for row in all_rank_rows()}
    row = table[name]
    forged = replace(row,statement=f'({row.statement}) /\\ false')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,),core=core()|table)
    gc.collect()


@pytest.mark.parametrize('name', EXPECTED_ROOTS)
def test_exact_rank_principal_statement_pins(name: str) -> None:
    row = next(row for row in all_rank_rows() if row.name == name)
    assert sha256(row.statement.encode()).hexdigest() == EXPECTED_ROOTS[name]


@pytest.mark.parametrize('name', EXPECTED_ROOTS)
def test_rank_root_missing_dependencies_are_rejected(name: str) -> None:
    table = {row.name:row for row in all_rank_rows()}
    row = table[name]
    forged = replace(row,dependencies=row.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,),core=core()|table)
    gc.collect()


SURFACES = (
    (coding.uniform_beta_prefix_box_relation,('scale','limit','length','bound')),
    (coding.finite_matrix_selector_relation,('code','scale','length','bound')),
    (selected.signed_selected_submatrix_relation,('pb','pc','nb','nc','w','rb','rc','cb','cc','q','ub','uc','vb','vc')),
    (selected.signed_selected_determinant_relation,('pb','pc','nb','nc','w','rb','rc','cb','cc','q','p','n')),
    (selected.nonzero_selected_minor_relation,('pb','pc','nb','nc','r','w','q','rb','rc','cb','cc')),
    (selected.nonzero_matrix_minor_relation,('pb','pc','nb','nc','r','w','q')),
    (candidate.all_signed_minors_zero_relation,('pb','pc','nb','nc','r','w','q')),
    (candidate.rectangular_matrix_rank_relation,('pb','pc','nb','nc','r','w','rank')),
)


@pytest.mark.parametrize('builder,arguments', SURFACES)
def test_rank_definitions_are_hygienic_first_order_surfaces(builder,arguments) -> None:
    first,names = parse_formula_with_names(builder(*arguments,tag='first'))
    second,other_names = parse_formula_with_names(builder(*arguments,tag='second'))
    assert names == other_names
    assert set(names) == set(arguments)
    assert first == second


@pytest.mark.parametrize('builder,arguments', SURFACES)
@pytest.mark.parametrize('bad', ('','S','forall','x) -> false','ff_capture','fs_capture','mdr_capture','mdm_capture','mce_capture','mcp_capture','fom_capture'))
def test_rank_definitions_reject_formula_injection_and_all_nested_capture_prefixes(builder,arguments,bad) -> None:
    with pytest.raises(ValueError):
        builder(bad,*arguments[1:],tag='safe')


@pytest.mark.parametrize('builder,arguments', SURFACES)
def test_rank_definitions_reject_argument_aliasing(builder,arguments) -> None:
    with pytest.raises(ValueError):
        builder(arguments[1],*arguments[1:],tag='safe')


@pytest.mark.parametrize('builder,arguments', SURFACES)
@pytest.mark.parametrize('bad', ('','S','forall','bad tag','x) -> false',17))
def test_rank_definitions_reject_malformed_binder_tags(builder,arguments,bad) -> None:
    with pytest.raises(ValueError):
        builder(*arguments,tag=bad)


def _after_foralls(name: str,count: int):
    row = next(row for row in all_rank_rows() if row.name == name)
    formula,names = parse_formula_with_names(row.statement)
    assert not names
    for _ in range(count):
        assert type(formula) is Forall
        formula = formula.body
    return formula


def test_uniform_code_box_is_chosen_before_arbitrary_source_codes() -> None:
    formula = _after_foralls('matrix_rank_uniform_beta_prefix_box_exists',2)
    assert type(formula) is Exists and type(formula.body) is Exists
    box = formula.body.body
    assert type(box) is And
    assert type(box.right) is Forall and type(box.right.body) is Forall
    assert type(box.right.body.body) is Imp
    assert type(box.right.body.body.right) is Exists


def test_actual_nonzero_minor_search_has_no_assumed_decidability_premise() -> None:
    formula = _after_foralls('matrix_rank_nonzero_minor_decidable',7)
    assert type(formula) is Or and type(formula.left) is Exists
    assert formula.right == Imp(formula.left,Bot())


def test_nonzero_is_signed_difference_nonzero_not_either_component() -> None:
    formula,_ = parse_formula_with_names(selected.nonzero_selected_minor_relation('pb','pc','nb','nc','r','w','q','rb','rc','cb','cc',tag='audit'))
    value = formula.right.right
    assert type(value) is Exists and type(value.body) is Exists
    assert value.body.body.right == Imp(Eq(Var(1),Var(0)),Bot())
    assert type(value.body.body.left) is Exists  # actual selected matrix and determinant


def test_rank_exists_unique_is_unconditional_and_contains_all_higher_actual_minors() -> None:
    formula = _after_foralls('rectangular_matrix_rank_exists_unique',6)
    assert type(formula) is Exists and type(formula.body) is And
    rank = formula.body.left
    assert type(rank) is And and type(rank.left) is Exists  # rank <= rows
    assert type(rank.right.left) is Exists  # rank <= columns
    assert type(rank.right.right.left) is Exists  # actual nonzero minor
    higher = rank.right.right.right
    assert type(higher) is Forall and type(higher.body) is Imp
    zero = higher.body.right
    for _ in range(6):
        assert type(zero) is Forall
        zero = zero.body
    for _ in range(3):
        assert type(zero) is Imp
        zero = zero.right
    assert zero == Eq(Var(1),Var(0))
    assert type(formula.body.right) is Forall
    assert type(formula.body.right.body) is Imp
