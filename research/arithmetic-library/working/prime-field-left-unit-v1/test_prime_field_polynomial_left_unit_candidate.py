"""Independent native contracts, actual models and conditional HA for left units.

The frozen divisibility source supplies the exact from-product premise type;
neither type loading nor finite models accept a dependency-complete proof.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING = HERE.parent
LIBRARY = ROOT / 'peano-lab/py/peano_lab/library'
SOURCE = HERE / 'prime_field_polynomial_left_unit_candidate.py'
SOURCE_SHA256 = 'dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6'
ORACLE_PATH = WORKING / 'prime-field-divisibility-v1/test_prime_field_polynomial_divisibility_candidate.py'
ORACLE_SHA256 = '82460849735222acb22c120004226a9e0a91c0231f8ab960cc3657f0767400e3'
DIVISIBILITY_PATH = WORKING / 'prime-field-divisibility-v1/prime_field_polynomial_divisibility_candidate.py'
DIVISIBILITY_SHA256 = 'f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8'
PRIVATE_NAMES = ('working_left_unit_candidate', 'working_left_unit_oracle',
                 'working_divisibility_candidate', 'working_divisibility_oracle',
                 'working_divisibility_associativity_type', 'working_append_candidate',
                 'working_append_shift_provider', 'working_append_scalar_provider')


def protected_bindings():
    return {name: value for name, value in sys.modules.items()
            if name.startswith('peano_lab.library.editions_v') or name in PRIVATE_NAMES}


def load_file(name, path):
    before = protected_bindings()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())
    return module


assert sha256(ORACLE_PATH.read_bytes()).hexdigest() == ORACLE_SHA256
divisibility = load_file(PRIVATE_NAMES[1], ORACLE_PATH)
oracle = divisibility.oracle
candidate = load_file(PRIVATE_NAMES[0], SOURCE)
PROVIDER_PINS = {
    **divisibility.PROVIDER_PINS,
    'bertrand_power_valuation_laws_candidate.py':
        '7b95e4f2a16df3866cb3e01f17d1b455000706454a1a241948957c4548a0a17f',
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_left_unit_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.bertrand_power_valuation_laws_candidate import make_bertrand_power_valuation_law_candidate_theorems
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_padding_candidate import make_prime_field_polynomial_convolution_padding_candidate_theorems
    from peano_lab.library.prime_field_polynomial_representation_candidate import make_prime_field_polynomial_representation_candidate_theorems
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems

    for name, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / name).read_bytes()).hexdigest() == digest
    assert sha256(DIVISIBILITY_PATH.read_bytes()).hexdigest() == DIVISIBILITY_SHA256
    core = {row.name: row for row in THEOREMS}
    for factory in (make_bertrand_power_valuation_law_candidate_theorems,
                    make_prime_field_arithmetic_candidate_theorems,
                    make_prime_field_polynomial_candidate_theorems,
                    make_prime_field_polynomial_convolution_candidate_theorems,
                    make_prime_field_polynomial_convolution_padding_candidate_theorems,
                    make_prime_field_polynomial_representation_candidate_theorems,
                    make_matrix_rank_finite_coding_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in core or core[row.name] == row
            core[row.name] = row
    introduction = divisibility.rows()[0]
    assert introduction.name == 'prime_field_polynomial_right_divides_from_product'
    assert introduction.name not in core and introduction.dependencies == ()
    core[introduction.name] = introduction
    return core


def body_core():
    core = dict(provider_core())
    for row in rows():
        assert row.name not in core
        core[row.name] = row
    return core


U, A, C = ('ub', 'uc', '1'), ('ab', 'ac', 'L'), ('cb', 'cc', 'L')


def UnitWitness(p, ab, ac, length):
    return 'exists ub uc cb cc. ' + oracle.And(
        oracle.Coeff(p, 'ub', 'uc', '1'), oracle.At('ub', 'uc', '0', '1'),
        oracle.Convolution(p, 'ub', 'uc', '1', ab, ac, length, 'cb', 'cc', length),
        oracle.Equivalent('cb', 'cc', length, ab, ac, length))


def independent_contracts():
    actual = oracle.Convolution('p', *U, *A, *C)
    unit = oracle.At('ub', 'uc', '0', '1')
    inside = oracle.Lt('i', 'L')
    entry = oracle.At('ab', 'ac', 'i', 'a')
    return (
        (('ub', 'uc', *A, 'i', 'a', 't'),
         (unit, inside, entry, oracle.Term(*U, *A, 'i', '0', 't')), 't=a'),
        (('ub', 'uc', *A, 'i', 'j', 't'),
         (oracle.Le('1', 'j'), oracle.Term(*U, *A, 'i', 'j', 't')), 't=0'),
        (('ub', 'uc', *A, 'i', 'a', 'db', 'dc', 'n'),
         (unit, inside, entry, oracle.Diagonal(*U, *A, 'i', 'db', 'dc', 'S i'),
          oracle.Sum('db', 'dc', 'S i', 'n')), 'n=a'),
        (('p', 'ub', 'uc', *A, 'i', 'a', 'r'),
         (unit, inside, entry, oracle.Lt('a', 'p'),
          oracle.ConvolutionCoefficient('p', *U, *A, 'i', 'r')), 'r=a'),
        (('p', 'ub', 'uc', *A, 'cb', 'cc'), (unit, actual),
         oracle.Equal('cb', 'cc', 'ab', 'ac', 'L')),
        (('p', 'ub', 'uc', *A, 'cb', 'cc'), (unit, actual), oracle.Equivalent(*C, *A)),
        (('p', *A), (oracle.Prime('p'), oracle.Coeff('p', *A)), UnitWitness('p', *A)),
        (('p', *A), (oracle.Prime('p'), oracle.Coeff('p', *A)),
         divisibility.RightDivides('p', *A, *A)),
    )


NAMES = ('polynomial_diagonal_left_unit_first_term',
         'polynomial_diagonal_left_unit_tail_term',
         'polynomial_diagonal_left_unit_natural_sum',
         'prime_field_convolution_coefficient_left_unit',
         'prime_field_polynomial_convolution_left_unit_equal',
         'prime_field_polynomial_convolution_left_unit_equivalent',
         'prime_field_polynomial_convolution_left_unit_exists',
         'prime_field_polynomial_right_divides_reflexive')
COMMANDS = (42, 33, 135, 43, 67, 27, 81, 38)


def test_exact_source_inventory_dependency_ownership_and_pure_unchanged_kernel_language():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert tuple(len(row.script) for row in rows()) == COMMANDS
    assert sum(COMMANDS) == 466
    assert sum(len(row.dependencies) for row in rows()) == 35
    core = provider_core()
    for index, row in enumerate(rows()):
        assert row.name not in core and len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(core) | set(NAMES[:index])
        assert not any(command.startswith(('admit', 'sorry', 'use ')) for command in row.script)
        assert not any('commut' in name for name in row.dependencies)
    assert rows()[-1].dependencies[-1] == 'prime_field_polynomial_right_divides_from_product'


@pytest.mark.parametrize('index', range(8), ids=tuple(f'row{i:02d}' for i in range(8)))
def test_independent_fully_expanded_contract(index):
    oracle.same_ast(_closed_formula(rows()[index].statement),
                    _closed_formula(oracle.contract(*independent_contracts()[index])))


def test_reflexivity_reuses_exact_frozen_existing_divisibility_definition():
    expected = divisibility.candidate.prime_field_polynomial_right_divides_relation(
        'p', *A, *A, tag='unit_reuse', variables=('p', *A))
    statement = oracle.contract(('p', *A), (oracle.Prime('p'), oracle.Coeff('p', *A)), expected)
    oracle.same_ast(_closed_formula(statement), _closed_formula(rows()[-1].statement))
    assert candidate.__all__ == ['make_prime_field_polynomial_left_unit_candidate_theorems']


@pytest.mark.parametrize('name', ('peano_lab.library.editions_v_left_unit_guard', *PRIVATE_NAMES))
def test_explicit_file_loader_preserves_foreign_identity(name, monkeypatch):
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, marker)
    before = protected_bindings()
    module = load_file(PRIVATE_NAMES[0], SOURCE)
    assert Path(module.__file__) == SOURCE
    assert protected_bindings() == before and sys.modules[name] is marker


def test_canonical_provider_paths_and_source_oracle_bytes_remain_exact():
    provider_core()
    for filename, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / filename).read_bytes()).hexdigest() == digest
        name = 'peano_lab.library.' + filename.removesuffix('.py')
        if name in sys.modules:
            assert Path(sys.modules[name].__file__).resolve() == (LIBRARY / filename).resolve()
    assert sha256(ORACLE_PATH.read_bytes()).hexdigest() == ORACLE_SHA256
    assert sha256(DIVISIBILITY_PATH.read_bytes()).hexdigest() == DIVISIBILITY_SHA256


def test_source_has_no_loader_registration_new_public_definition_or_commutativity_oracle():
    tree = ast.parse(SOURCE.read_text())
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
    assert all(node.level == 0 for node in ast.walk(tree) if isinstance(node, ast.ImportFrom))
    assert not any('receipt' in command for row in rows() for command in row.script)
    assert all('gcd' not in row.name and 'bezout' not in row.name for row in rows())


def test_one_term_and_zero_tail_sums_are_actual_and_scoped():
    script = rows()[2].script
    assert any(command.startswith('have hhead :') for command in script)
    assert any(command.startswith('have htail :') for command in script)
    assert 'specialize beta_sum_exists (1)' in script
    assert 'specialize beta_sum_succ_decompose (0)' in script
    assert 'specialize polynomial_zero_tail_natural_sum_invariant (1)' in script
    assert 'specialize polynomial_zero_tail_natural_sum_invariant (i)' in script
    assert script.index('have hhead : ' + candidate._at('db', 'dc', '0', 'a', 'unit_sum_head')) < next(
        i for i, command in enumerate(script) if command.startswith('have htail :'))


def test_actual_left_unit_constructor_does_not_assume_nonempty_right_factor():
    script = rows()[6].script
    assert r'have hzero : L=0 \/ ~(L=0)' in script
    assert 'specialize prime_field_polynomial_convolution_at_length_exists (L)' in script
    assert 'specialize prime_field_polynomial_repeat_exists (1)' in script
    assert 'exists x2' in script and 'exists x3' in script
    parameters, premises, _ = independent_contracts()[6]
    assert premises == (oracle.Prime('p'), oracle.Coeff('p', *A))
    assert parameters == ('p', *A)


def test_local_statement_novelty_uses_actual_parsed_types():
    seen = [_closed_formula(row.statement) for row in provider_core().values()]
    for row in rows():
        current = _closed_formula(row.statement)
        for previous in seen:
            with pytest.raises(AssertionError):
                oracle.same_ast(current, previous)
        seen.append(current)


VALUES = ((), (0,), (1,), (0, 0), (1, 0), (0, 1), (1, 1, 0), (0, 1, 0, 1))


@pytest.mark.parametrize('values', VALUES)
@pytest.mark.parametrize('p', (2, 3, 5, 6))
@pytest.mark.parametrize('variant', (1, 3))
def test_actual_unit_beta_sum_residue_and_reflexive_witness_models(values, p, variant):
    unit = divisibility.encoded((1,), variant)
    source = divisibility.encoded(values, variant + 1)
    product = divisibility.actual_product(p, unit, source, variant + 2)
    assert product[2] == len(values)
    assert oracle.prefix(product[:2], product[2]) == values
    assert divisibility.valid_witness(p, source, source, unit, product)
    for i, a in enumerate(values):
        residue, diagonal, trace, total = oracle.actual_coefficient_witness(
            p, unit[:2], 1, source[:2], len(values), i, variant + 3)
        assert oracle.beta(diagonal, 0) == a
        assert all(oracle.beta(diagonal, j) == 0 for j in range(1, i + 1))
        assert total == a == residue == oracle.beta(trace, i + 1)
    if not values:
        assert product[2] == 0 and not oracle.prefix(product[:2], 1) == ()


@pytest.mark.parametrize('p', (2, 3, 5))
def test_nonunit_nonconstant_and_unbounded_claims_have_concrete_counterexamples(p):
    a = divisibility.encoded((1, 1), 1)
    wrong_unit = divisibility.encoded((0,), 2)
    wrong_product = divisibility.actual_product(p, wrong_unit, a, 3)
    assert not divisibility.equivalent(wrong_product, a)
    nonconstant = divisibility.encoded((1, 1), 4)
    nonconstant_product = divisibility.actual_product(p, nonconstant, a, 5)
    assert not divisibility.equivalent(nonconstant_product, a)
    unbounded = divisibility.encoded((p,), 6)
    unit = divisibility.encoded((1,), 7)
    residue, _, _, total = oracle.actual_coefficient_witness(p, unit[:2], 1, unbounded[:2], 1, 0)
    assert total == p and residue == 0 and residue != p


def test_formal_unit_identity_does_not_force_beta_code_identity_or_evaluation_equivalence():
    source = divisibility.encoded((0, 1, 1), 1)
    unit = divisibility.encoded((1,), 2)
    product = divisibility.actual_product(2, unit, source, 3)
    assert source[:2] != product[:2] and divisibility.equivalent(source, product)
    zero = divisibility.encoded((), 4)
    vanish = divisibility.encoded((1, 1, 0), 5)
    assert all((x*x + x) % 2 == 0 for x in range(2))
    assert not divisibility.equivalent(zero, vanish)


@pytest.mark.parametrize('index', range(8), ids=tuple(f'row{i:02d}' for i in range(8)))
def test_actual_original_ha_body(index):
    row = rows()[index]
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == row.name
    assert (receipt.command_count, receipt.dependency_count) == (len(row.script), len(row.dependencies))
    assert 0 < receipt.proof_objects <= receipt.proof_nodes and receipt.proof_depth > 0


@pytest.mark.parametrize('index', range(8), ids=tuple(f'row{i:02d}' for i in range(8)))
@pytest.mark.parametrize('mutation', ('false_conclusion', 'missing_body', 'truncated_body'))
def test_false_or_incomplete_body_is_rejected(index, mutation):
    row = rows()[index]
    parameters, premises, _ = independent_contracts()[index]
    changed = replace(row, statement=oracle.contract(parameters, premises, '0=1')) if mutation == 'false_conclusion' else replace(
        row, script=() if mutation == 'missing_body' else row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


EDGES = tuple((index, dependency) for index, row in enumerate(rows()) for dependency in row.dependencies)
EDGE_IDS = tuple(f'row{index:02d}-edge{position:02d}' for position, (index, _) in enumerate(EDGES))


@pytest.mark.parametrize('index,dependency', EDGES, ids=EDGE_IDS)
def test_each_removed_dependency_is_rejected(index, dependency):
    row = rows()[index]
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('index,dependency', EDGES, ids=EDGE_IDS)
def test_each_poisoned_dependency_is_rejected(index, dependency):
    core = body_core()
    core[dependency] = replace(core[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],), core=core)
