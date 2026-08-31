"""Independent divisibility contracts/models and original conditional HA.

The frozen associativity source supplies only an exact premise type here.
Neither this conditional replay nor a finite model admits a theorem to Alpha.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
import json
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
SOURCE = HERE / 'prime_field_polynomial_divisibility_candidate.py'
SOURCE_SHA256 = 'f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8'
ORACLE_PATH = WORKING / 'prime-field-append-v1/test_prime_field_polynomial_append_candidate.py'
ORACLE_SHA256 = '0c554b05b2c7e2c40e3b0e8044160379a3284bb173e48d59d77def0cad4272aa'
ASSOCIATIVITY_PATH = WORKING / 'prime-field-associativity-induction-v1/prime_field_polynomial_associativity_induction_candidate.py'
ASSOCIATIVITY_SHA256 = '8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c'
ASSOCIATIVITY_NAME = 'prime_field_polynomial_convolution_associative_equivalent'
PRIVATE_NAMES = ('working_divisibility_candidate', 'working_divisibility_oracle',
                 'working_divisibility_associativity_type', 'working_append_candidate',
                 'working_append_shift_provider', 'working_append_scalar_provider')


def protected_bindings():
    return {name: module for name, module in sys.modules.items()
            if name.startswith('peano_lab.library.editions_v') or name in PRIVATE_NAMES}


def load_file(name, path):
    before = protected_bindings()
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())
    return module


assert sha256(ORACLE_PATH.read_bytes()).hexdigest() == ORACLE_SHA256
oracle = load_file(PRIVATE_NAMES[1], ORACLE_PATH)
candidate = load_file(PRIVATE_NAMES[0], SOURCE)
PROVIDER_PINS = {
    **oracle.PROVIDER_PINS,
    'prime_field_polynomial_convolution_congruence_candidate.py':
        'effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70',
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_divisibility_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_congruence_candidate import make_prime_field_polynomial_convolution_congruence_candidate_theorems
    from peano_lab.library.prime_field_polynomial_representation_candidate import make_prime_field_polynomial_representation_candidate_theorems
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems

    for name, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / name).read_bytes()).hexdigest() == digest
    assert sha256(ASSOCIATIVITY_PATH.read_bytes()).hexdigest() == ASSOCIATIVITY_SHA256
    association = load_file(PRIVATE_NAMES[2], ASSOCIATIVITY_PATH)
    core = {row.name: row for row in THEOREMS}
    for factory in (make_prime_field_arithmetic_candidate_theorems, make_prime_field_polynomial_candidate_theorems,
                    make_prime_field_polynomial_convolution_candidate_theorems,
                    make_prime_field_polynomial_convolution_congruence_candidate_theorems,
                    make_prime_field_polynomial_representation_candidate_theorems,
                    make_matrix_rank_finite_coding_candidate_theorems,
                    association.make_prime_field_polynomial_associativity_induction_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in core or core[row.name] == row
            core[row.name] = row
    return core


def body_core():
    core = dict(provider_core())
    for row in rows():
        assert row.name not in core
        core[row.name] = row
    return core


# This expansion is independent of the candidate builder and uses the frozen
# independently authored native coefficient/convolution/power graphs.
def RightDivides(p, db, dc, D, ab, ac, L):
    return oracle.And(oracle.Coeff(p, ab, ac, L),
        'exists quotient_b quotient_c quotient_length product_b product_c product_length. '
        + oracle.And(oracle.Convolution(p, 'quotient_b', 'quotient_c', 'quotient_length',
                                        db, dc, D, 'product_b', 'product_c', 'product_length'),
                     oracle.Equivalent('product_b', 'product_c', 'product_length', ab, ac, L)))


D, A, B, E = ('db', 'dc', 'D'), ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('eb', 'ec', 'E')
Q, P = ('qb', 'qc', 'Q'), ('pb', 'pc', 'P')


def independent_contracts():
    empty = ('ab', 'ac', '0')
    return (
        (('p', *D, *A, *Q, *P), (oracle.Coeff('p', *A), oracle.Convolution('p', *Q, *D, *P),
                                oracle.Equivalent(*P, *A)), RightDivides('p', *D, *A)),
        (('p', *D, *A), (RightDivides('p', *D, *A),), oracle.Coeff('p', *D)),
        (('p', *D, *A), (RightDivides('p', *D, *A),), oracle.Coeff('p', *A)),
        (('p', *D, *A, *B), (oracle.Coeff('p', *B), RightDivides('p', *D, *A),
                            oracle.Equivalent(*A, *B)), RightDivides('p', *D, *B)),
        (('p', *D, 'ab', 'ac'), (oracle.Coeff('p', *D),), RightDivides('p', *D, *empty)),
        (('p', *D, *A, *E), ('~(p=0)', oracle.Coeff('p', *E), oracle.Equivalent(*D, *E),
                            RightDivides('p', *D, *A)), RightDivides('p', *E, *A)),
        (('p', *D, *A, *B), (oracle.Prime('p'), RightDivides('p', *D, *A),
                            RightDivides('p', *A, *B)), RightDivides('p', *D, *B)),
    )


NAMES = tuple('prime_field_polynomial_right_divides_' + name for name in (
    'from_product', 'divisor_bounded', 'dividend_bounded', 'equivalent_target',
    'empty', 'equivalent_divisor', 'transitive'))
COMMANDS = (27, 20, 10, 49, 56, 103, 222)


def test_source_order_inventory_and_only_earlier_or_actual_provider_dependencies():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert tuple(len(row.script) for row in rows()) == COMMANDS
    assert sum(COMMANDS) == 487
    assert sum(len(row.dependencies) for row in rows()) == 20
    core = provider_core()
    for index, row in enumerate(rows()):
        assert row.name not in core and len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(core) | set(NAMES[:index])
        assert not any(command.startswith(('admit', 'sorry', 'use ')) for command in row.script)
    assert ASSOCIATIVITY_NAME in rows()[-1].dependencies
    assert all(ASSOCIATIVITY_NAME not in row.dependencies for row in rows()[:-1])


@pytest.mark.parametrize('index', range(7), ids=tuple(f'row{i:02d}' for i in range(7)))
def test_independent_fully_expanded_contract(index):
    oracle.same_ast(_closed_formula(rows()[index].statement),
                    _closed_formula(oracle.contract(*independent_contracts()[index])))


def test_public_builder_is_exact_conservative_expansion_with_canonical_target():
    parameters = ('p', *D, *A)
    actual = candidate.prime_field_polynomial_right_divides_relation(
        *parameters, tag='independent', variables=parameters)
    prefix = 'forall ' + ' '.join(parameters) + '. '
    oracle.same_ast(_closed_formula(prefix + actual),
                    _closed_formula(prefix + RightDivides(*parameters)))
    assert 'forall' in actual and 'exists' in actual and 'Horner' not in actual


@pytest.mark.parametrize('name', ('peano_lab.library.editions_v_divisibility_guard', *PRIVATE_NAMES))
def test_explicit_file_loader_preserves_foreign_identity(name, monkeypatch):
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, marker)
    before = protected_bindings()
    module = load_file(PRIVATE_NAMES[0], SOURCE)
    assert Path(module.__file__) == SOURCE
    assert protected_bindings() == before and sys.modules[name] is marker


def test_canonical_providers_and_frozen_type_oracle_inputs_remain_exact():
    provider_core()
    for filename, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / filename).read_bytes()).hexdigest() == digest
        name = 'peano_lab.library.' + filename.removesuffix('.py')
        if name in sys.modules:
            assert Path(sys.modules[name].__file__).resolve() == (LIBRARY / filename).resolve()
    assert sha256(ORACLE_PATH.read_bytes()).hexdigest() == ORACLE_SHA256
    assert sha256(ASSOCIATIVITY_PATH.read_bytes()).hexdigest() == ASSOCIATIVITY_SHA256


def test_source_has_no_loader_registration_or_quotient_code_identity_claim():
    tree = ast.parse(SOURCE.read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.ImportFrom) and node.level == 0 for node in imports)
    assert {node.module for node in imports} == {
        '__future__', 'typing', 'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate',
        'peano_lab.library.prime_field_polynomial_convolution_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate',
    }
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert candidate.__all__ == ['make_prime_field_polynomial_divisibility_candidate_theorems',
                               'prime_field_polynomial_right_divides_relation']
    assert not any('receipt' in command for row in rows() for command in row.script)
    assert all('gcd' not in row.name and 'bezout' not in row.name for row in rows())


@pytest.mark.parametrize('position', range(7))
def test_public_builder_rejects_unknown_or_injected_term(position):
    parameters = ('p', *D, *A)
    bad = list(parameters)
    bad[position] = 'outside_context'
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_right_divides_relation(
            *bad, tag='badterm', variables=parameters)


@pytest.mark.parametrize('role', ('qb', 'qc', 'qlen', 'pb', 'pc', 'plen'))
def test_public_builder_rejects_each_witness_capture(role):
    parameters = ('p', *D, *A)
    variables = (*parameters, 'pfrd_' + role + '_capture')
    with pytest.raises(ValueError, match='captures a context variable'):
        candidate.prime_field_polynomial_right_divides_relation(
            *parameters, tag='capture', variables=variables)


@pytest.mark.parametrize('context', ((), ['p'], ('p', 'p'), ('p', 'not a name')))
def test_public_builder_rejects_bad_context(context):
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_right_divides_relation(
            '0', '0', '0', '0', '0', '0', '0', tag='badcontext', variables=context)


def test_three_actual_intermediates_and_exact_associativity_orientation():
    script = rows()[-1].script
    length_goals = [command for command in script if command.startswith('have h') and '_length :' in command]
    actual_goals = [command for command in script if command.startswith('have h') and '_product :' in command]
    assert len(length_goals) == len(actual_goals) == 3
    specialized = tuple(command for command in script
                        if command.startswith('specialize ' + ASSOCIATIVITY_NAME + ' '))
    assert specialized == tuple('specialize ' + ASSOCIATIVITY_NAME + ' (' + term + ')' for term in (
        'p', 'x6', 'x7', 'x8', 'x', 'x1', 'x2', 'x13', 'x14', 'x12',
        *D, 'x3', 'x4', 'x5', 'x16', 'x17', 'x15', 'x19', 'x20', 'x18'))
    assert not any('commut' in dependency for dependency in rows()[-1].dependencies)


def test_local_novelty_compares_actual_parsed_types_not_names():
    from peano_lab.library.formula_dag import FormulaArena

    def digest(statement):
        encoded = FormulaArena().freeze(_closed_formula(statement)).to_json()
        return sha256(json.dumps(encoded, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    old = {digest(row.statement) for row in provider_core().values()}
    new = [digest(row.statement) for row in rows()]
    assert len(set(new)) == len(new) == 7 and not old.intersection(new)


def test_transitivity_specializations_live_in_separate_local_scopes():
    script = rows()[-1].script
    declaration = next(i for i, command in enumerate(script)
                       if command.startswith('have htarget_equivalent : '))
    calls = [i for i, command in enumerate(script)
             if command == 'apply prime_field_polynomial_equivalent_transitive']
    packaging = script.index('apply prime_field_polynomial_right_divides_from_product')
    assert len(calls) == 2 and declaration < calls[0] < packaging < calls[1]
    assert script[-1] == 'exact htarget_equivalent'


def encoded(values, variant=1):
    values = tuple(values)
    # A genuine unbounded extra entry is outside the represented polynomial.
    return (*oracle.encode_beta((*values, 97 + variant), variant), len(values))


def bounded(p, code):
    return all(0 <= oracle.beta(code[:2], i) < p for i in range(code[2]))


def equivalent(first, second):
    return oracle.equivalent(first[:2], first[2], second[:2], second[2])


def actual_product(p, left, right, variant=1):
    assert bounded(p, left) and bounded(p, right)
    values = oracle.product_values(p, oracle.prefix(left[:2], left[2]),
                                   oracle.prefix(right[:2], right[2]))
    output = encoded(values, variant)
    assert output[2] == (left[2] + right[2] - 1 if left[2] and right[2] else 0)
    for index, value in enumerate(values):
        residue, diagonal, trace, total = oracle.actual_coefficient_witness(
            p, left[:2], left[2], right[:2], right[2], index, variant + 1)
        assert residue == value and total == oracle.beta(trace, index + 1)
        assert all(oracle.beta(diagonal, j) == oracle.zero_extended(left[:2], left[2], j)
                   * oracle.zero_extended(right[:2], right[2], index - j) for j in range(index + 1))
    return output


def valid_witness(p, divisor, target, quotient, product):
    if not all(bounded(p, code) for code in (divisor, target, quotient, product)):
        return False
    values = oracle.product_values(p, oracle.prefix(quotient[:2], quotient[2]),
                                   oracle.prefix(divisor[:2], divisor[2]))
    return oracle.prefix(product[:2], product[2]) == values and equivalent(product, target)


TRIPLES = (((), (), ()), ((), (1,), (1,)), ((1,), (), (1,)), ((1,), (1,), ()),
           ((0,), (1,), (1,)), ((1, 0), (1, 1), (1, 0)),
           ((0, 1), (1, 0), (0, 1)), ((1, 1), (1, 1), (1, 1)))


@pytest.mark.parametrize('values', TRIPLES)
@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('padding', (0, 2))
def test_actual_beta_transitivity_witnesses_with_independent_padding(values, p, padding):
    d_values, q1_values, q2_values = values
    divisor, quotient1, quotient2 = (encoded(items, variant) for variant, items in
                                    enumerate((d_values, q1_values, q2_values), 1))
    product1 = actual_product(p, quotient1, divisor, 4)
    target1 = encoded((0,) * padding + oracle.prefix(product1[:2], product1[2]), 5)
    assert valid_witness(p, divisor, target1, quotient1, product1)
    product2 = actual_product(p, quotient2, target1, 6)
    target2 = encoded((0,) * (2 - padding) + oracle.prefix(product2[:2], product2[2]), 7)
    assert valid_witness(p, target1, target2, quotient2, product2)
    composite = actual_product(p, quotient2, quotient1, 8)
    result = actual_product(p, composite, divisor, 9)
    mixed = actual_product(p, quotient2, product1, 10)
    assert equivalent(result, mixed) and equivalent(mixed, product2)
    assert valid_witness(p, divisor, target2, composite, result)
    replacement = encoded((0, 0) + d_values, 11)
    replacement_product = actual_product(p, quotient1, replacement, 12)
    assert equivalent(divisor, replacement)
    assert valid_witness(p, replacement, target1, quotient1, replacement_product)


@pytest.mark.parametrize('p', (0, 1, 2, 5))
@pytest.mark.parametrize('variant', (1, 3))
def test_actual_empty_quotient_retains_zero_modulus_and_empty_divisor_cases(p, variant):
    divisor = encoded((), variant) if p == 0 else encoded((0, 0), variant)
    empty = encoded((), variant + 1)
    result = actual_product(p, empty, divisor, variant + 2)
    assert valid_witness(p, divisor, empty, empty, result)


def test_raw_code_equality_and_finite_field_function_agreement_are_not_the_relation():
    divisor, quotient = encoded((1, 1), 1), encoded((1,), 2)
    product = actual_product(2, quotient, divisor, 3)
    recoded = encoded((0, 1, 1), 4)
    assert product[:2] != recoded[:2] and product[2] != recoded[2]
    assert valid_witness(2, divisor, recoded, quotient, product)
    zero = encoded((), 5)
    vanishing_function = encoded((1, 1, 0), 6)  # X^2 + X over F_2.
    assert all((x*x + x) % 2 == 0 for x in range(2))
    assert not equivalent(zero, vanishing_function)
    assert not valid_witness(2, zero, vanishing_function, quotient, zero)


@pytest.mark.parametrize('index', range(7), ids=tuple(f'row{i:02d}' for i in range(7)))
def test_actual_original_ha_body(index):
    row = rows()[index]
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == row.name
    assert (receipt.command_count, receipt.dependency_count) == (len(row.script), len(row.dependencies))
    assert 0 < receipt.proof_objects <= receipt.proof_nodes and receipt.proof_depth > 0


@pytest.mark.parametrize('index', range(7), ids=tuple(f'row{i:02d}' for i in range(7)))
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
