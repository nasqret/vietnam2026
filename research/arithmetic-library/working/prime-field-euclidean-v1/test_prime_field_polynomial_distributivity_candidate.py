"""Independent formal contracts and original conditional HA for distributivity.

These direct-provider tests do not manufacture a closed proof, Lean result,
publication capability, or admission.  Model checks use actual CRT beta codes
and actual antidiagonal/sum witnesses, not merely equal polynomial evaluations.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
import importlib.util
import itertools
import math
from pathlib import Path
import re

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import THEOREMS, TheoremSpec


DIRECTORY = Path(__file__).parent


def load_file(name, filename):
    source = DIRECTORY / filename
    loader = importlib.util.spec_from_file_location(name, source)
    assert loader is not None and loader.loader is not None
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


candidate = load_file('working_polynomial_distributivity_candidate',
                      'prime_field_polynomial_distributivity_candidate.py')
independent = load_file('working_distributivity_independent_syntax',
                        'test_prime_field_polynomial_convolution_triangular_candidate.py')
at, lt, conj = independent.at, independent.lt, independent.conj
pad, term, diagonal = independent.pad, independent.term, independent.diagonal
finite_sum, coefficient, field_add = independent.finite_sum, independent.coefficient, independent.add
exact_ast, format_contract = independent.exact_ast, independent.format_contract


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_distributivity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.finite_sum_theorems import make_finite_sum_theorems
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    from peano_lab.library.prime_field_polynomial_subtraction_candidate import make_prime_field_polynomial_subtraction_candidate_theorems

    result = {row.name: row for row in THEOREMS}
    for factory in (make_finite_sum_theorems, make_prime_field_arithmetic_candidate_theorems,
                    make_prime_field_polynomial_candidate_theorems,
                    make_prime_field_polynomial_convolution_candidate_theorems,
                    make_prime_field_polynomial_subtraction_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


def mod(p, a, b):
    return f'exists independent_mod_u independent_mod_v. ({a})+({p})*independent_mod_u=({b})+({p})*independent_mod_v'


def polynomial_add(p, ab, ac, bb, bc, cb, cc, length):
    return (f'forall independent_add_i. ({lt("independent_add_i",length)}) -> '
            'exists independent_add_a independent_add_b independent_add_c. ' + conj(
                at(ab, ac, 'independent_add_i', 'independent_add_a'),
                at(bb, bc, 'independent_add_i', 'independent_add_b'),
                at(cb, cc, 'independent_add_i', 'independent_add_c'),
                field_add(p, 'independent_add_a', 'independent_add_b', 'independent_add_c')))


def polynomial_subtract(p, ab, ac, bb, bc, cb, cc, length):
    return (f'forall independent_sub_i. ({lt("independent_sub_i",length)}) -> '
            'exists independent_sub_a independent_sub_b independent_sub_c. ' + conj(
                at(ab, ac, 'independent_sub_i', 'independent_sub_a'),
                at(bb, bc, 'independent_sub_i', 'independent_sub_b'),
                at(cb, cc, 'independent_sub_i', 'independent_sub_c'),
                field_add(p, 'independent_sub_b', 'independent_sub_c', 'independent_sub_a')))


def coefficients(p, b, c, length):
    return (f'forall independent_coeff_i. ({lt("independent_coeff_i",length)}) -> '
            'exists independent_coeff_a. ' + conj(at(b, c, 'independent_coeff_i', 'independent_coeff_a'),
                                                 lt('independent_coeff_a', p)))


def product_length(left, right, length):
    empty = conj(f'({left})=0 \\/ ({right})=0', f'({length})=0')
    positive = conj(f'~(({left})=0)', f'~(({right})=0)', f'({left})+({right})=S ({length})')
    return f'({empty}) \\/ ({positive})'


def prefix(p, ab, ac, L, bb, bc, M, cb, cc, length):
    return (f'forall independent_prefix_i. ({lt("independent_prefix_i",length)}) -> '
            'exists independent_prefix_r. ' + conj(at(cb, cc, 'independent_prefix_i', 'independent_prefix_r'),
                coefficient(p, ab, ac, L, bb, bc, M, 'independent_prefix_i', 'independent_prefix_r')))


def convolution(p, ab, ac, L, bb, bc, M, cb, cc, length):
    return conj(coefficients(p, ab, ac, L), coefficients(p, bb, bc, M), product_length(L, M, length),
                prefix(p, ab, ac, L, bb, bc, M, cb, cc, length))


PARAMETERS = 'p ab ac bb bc cb cc L db dc M'
OPERANDS = (('ab', 'ac'), ('bb', 'bc'), ('cb', 'cc'))
ADD = polynomial_add('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L')
SUBTRACT = polynomial_subtract('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L')
OUTPUTS = (('ub', 'uc'), ('vb', 'vc'), ('wb', 'wc'))
OUTPUT_PARAMETERS = 'ub uc vb vc wb wc N'


def factors(side, code, scale):
    return ('db', 'dc', 'M', code, scale, 'L') if side == 'left' else (code, scale, 'L', 'db', 'dc', 'M')


def contracts():
    pointwise = ('forall i a b c. ' + ''.join('(' + hypothesis + ') -> ' for hypothesis in (
        lt('i', 'L'), at('ab', 'ac', 'i', 'a'), at('bb', 'bc', 'i', 'b'), at('cb', 'cc', 'i', 'c'),
    )) + '(' + mod('p', 'a+b', 'c') + ')')
    result = [
        ('p ab ac bb bc cb cc L A B C', (
            finite_sum('ab', 'ac', 'L', 'A'), finite_sum('bb', 'bc', 'L', 'B'),
            finite_sum('cb', 'cc', 'L', 'C'), pointwise,
        ), mod('p', 'A+B', 'C')),
        ('p ab ac bb bc cb cc L i a b r', (
            ADD, pad('ab', 'ac', 'L', 'i', 'a'), pad('bb', 'bc', 'L', 'i', 'b'),
            pad('cb', 'cc', 'L', 'i', 'r'),
        ), mod('p', 'a+b', 'r')),
    ]
    for side in ('left', 'right'):
        result.append((PARAMETERS + ' i j u v w', (
            ADD, *(term(*factors(side, b, c), 'i', 'j', value)
                   for (b, c), value in zip(OPERANDS, ('u', 'v', 'w'), strict=True)),
        ), mod('p', 'u+v', 'w')))
    for side in ('left', 'right'):
        premises = [ADD]
        for (b, c), (tb, tc), value in zip(OPERANDS, (('ub', 'uc'), ('vb', 'vc'), ('wb', 'wc')),
                                          ('u', 'v', 'w'), strict=True):
            premises.extend((diagonal(*factors(side, b, c), 'i', tb, tc, 'N'),
                             finite_sum(tb, tc, 'N', value)))
        result.append((PARAMETERS + ' i N ub uc vb vc wb wc u v w', tuple(premises), mod('p', 'u+v', 'w')))
    for side in ('left', 'right'):
        result.append((PARAMETERS + ' i u v w', (
            ADD, *(coefficient('p', *factors(side, b, c), 'i', value)
                   for (b, c), value in zip(OPERANDS, ('u', 'v', 'w'), strict=True)),
        ), field_add('p', 'u', 'v', 'w')))
    for operation in ('add', 'subtract'):
        graph, source = (polynomial_add, ADD) if operation == 'add' else (polynomial_subtract, SUBTRACT)
        for side in ('left', 'right'):
            result.append((PARAMETERS + ' ' + OUTPUT_PARAMETERS, (
                source, *(prefix('p', *factors(side, b, c), ob, oc, 'N')
                          for (b, c), (ob, oc) in zip(OPERANDS, OUTPUTS, strict=True)),
            ), graph('p', 'ub', 'uc', 'vb', 'vc', 'wb', 'wc', 'N')))
    for operation in ('add', 'subtract'):
        graph, source = (polynomial_add, ADD) if operation == 'add' else (polynomial_subtract, SUBTRACT)
        for side in ('left', 'right'):
            result.append((PARAMETERS + ' ' + OUTPUT_PARAMETERS, (
                source, *(convolution('p', *factors(side, b, c), ob, oc, 'N')
                          for (b, c), (ob, oc) in zip(OPERANDS, OUTPUTS, strict=True)),
            ), graph('p', 'ub', 'uc', 'vb', 'vc', 'wb', 'wc', 'N')))
    for side in ('left', 'right'):
        products = tuple(convolution('p', *factors(side, b, c), ob, oc, 'N')
                         for (b, c), (ob, oc) in zip(OPERANDS, OUTPUTS, strict=True))
        result.append((PARAMETERS, ('~(p=0)', coefficients('p', 'db', 'dc', 'M'), ADD),
                       'exists N ub uc vb vc wb wc. ' + conj(
                           *products, polynomial_add('p', 'ub', 'uc', 'vb', 'vc', 'wb', 'wc', 'N'))))
    return tuple(result)


def test_exact_ordered_dependency_topology():
    known = set(provider_core())
    assert len(rows()) == len(contracts())
    for row in rows():
        assert row.name not in known
        assert row.script
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= known
        known.add(row.name)


NAMES = (
    'beta_sum_pointwise_mod_add',
    'polynomial_zero_extended_add_congruent',
    'polynomial_diagonal_term_left_add_congruent',
    'polynomial_diagonal_term_right_add_congruent',
    'polynomial_diagonal_sum_left_add_congruent',
    'polynomial_diagonal_sum_right_add_congruent',
    'prime_field_convolution_coefficient_left_add',
    'prime_field_convolution_coefficient_right_add',
    'prime_field_convolution_prefix_left_add',
    'prime_field_convolution_prefix_right_add',
    'prime_field_convolution_prefix_left_subtract',
    'prime_field_convolution_prefix_right_subtract',
    'prime_field_polynomial_convolution_left_add',
    'prime_field_polynomial_convolution_right_add',
    'prime_field_polynomial_convolution_left_subtract',
    'prime_field_polynomial_convolution_right_subtract',
    'prime_field_polynomial_left_distributive_products_exists',
    'prime_field_polynomial_right_distributive_products_exists',
)
METRICS = ((225,54),(130,41),(234,58),(235,58),(327,126),(327,126),(141,68),(141,68),
           (79,54),(79,54),(174,100),(174,100),(176,100),(176,100),(176,100),(176,100),
           (157,58),(157,58))


def test_exact_inventory_and_kernel_language():
    assert tuple(row.name for row in rows()) == NAMES
    assert len(rows()) == len(METRICS) == 18
    assert sum(len(row.dependencies) for row in rows()) == 54
    assert sum(len(row.script) for row in rows()) == 1636
    for row in rows():
        assert row.name not in row.dependencies
        assert all(isinstance(command, str) and command for command in row.script)
        assert all(command.split()[0] not in ('admit', 'sorry', 'axiom', 'native_decide') for command in row.script)
        assert re.fullmatch(r'[A-Za-z0-9_\s().+*=~\\/<>-]+', row.statement)
        exact_ast(row.statement)


@pytest.mark.parametrize('index', range(len(rows())))
def test_independently_expanded_contract(index):
    assert exact_ast(rows()[index].statement) == exact_ast(format_contract(*contracts()[index]))


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_original_ha_body(row):
    try:
        receipt = replay_candidate_bodies((row,), core=body_core())[0]
        assert receipt.name == row.name
        assert receipt.dependency_count == len(row.dependencies)
        assert receipt.command_count == len(row.script)
        assert (receipt.proof_nodes, receipt.proof_depth) == METRICS[rows().index(row)]
        assert 0 < receipt.proof_objects <= receipt.proof_nodes
        assert 0 < receipt.proof_depth <= receipt.proof_nodes
        print(receipt, flush=True)
    finally:
        gc.collect()


@pytest.mark.parametrize('index', range(len(rows())))
def test_false_conclusion_is_rejected(index):
    names, premises, _ = contracts()[index]
    changed = replace(rows()[index], statement=format_contract(names, premises, '0=1'))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_missing_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=()),), core=body_core())


EDGES = tuple((row, dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency', EDGES, ids=lambda value: value.name if hasattr(value, 'name') else value)
def test_each_removed_dependency_is_rejected(row, dependency):
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row,dependency', EDGES, ids=lambda value: value.name if hasattr(value, 'name') else value)
def test_each_poisoned_dependency_is_rejected(row, dependency):
    table = body_core()
    table[dependency] = replace(table[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,), core=table)


def hostile_contracts():
    result = []
    data = contracts()
    for index, label, omitted in (
        (0, 'sum_relation_not_an_assumed_numeric_endpoint', 0),
        (0, 'pointwise_congruence_is_required', 3),
        (1, 'actual_coefficient_addition_is_required', 0),
        (1, 'padded_total_entry_is_required', 3),
        (2, 'actual_first_term_is_required', 1),
        (3, 'actual_second_term_is_required', 2),
        (4, 'actual_first_diagonal_is_required', 1),
        (5, 'actual_third_sum_is_required', 6),
        (6, 'actual_canonical_total_coefficient_is_required', 3),
        (7, 'actual_coefficient_addition_is_required', 0),
        (8, 'actual_total_prefix_is_required', 3),
        (9, 'actual_second_prefix_is_required', 2),
        (10, 'subtraction_is_not_unspecified_zero_padding', 0),
        (11, 'actual_first_product_is_required', 1),
        (16, 'constructor_retains_its_nonzero_modulus_contract', 0),
        (17, 'constructor_retains_its_canonical_fixed_input_contract', 1),
    ):
        names, premises, conclusion = data[index]
        result.append((index, label, format_contract(names, tuple(
            premise for i, premise in enumerate(premises) if i != omitted), conclusion)))
    for index in (0, 2, 3, 4, 5, 6, 7):
        names, premises, _ = data[index]
        result.append((index, 'modular_addition_does_not_mean_natural_equality',
                       format_contract(names, premises, 'A+B=C' if index == 0 else 'u+v=w')))
    for index in (8, 9, 10, 11):
        names, premises, _ = data[index]
        result.append((index, 'no_equality_of_raw_product_codes',
                       format_contract(names, premises, 'ub=wb')))
        graph = polynomial_add if index < 10 else polynomial_subtract
        result.append((index, 'product_prefix_does_not_constrain_the_next_entry',
                       format_contract(names, premises, graph('p', 'ub', 'uc', 'vb', 'vc', 'wb', 'wc', 'S N'))))
    return tuple(result)


@pytest.mark.parametrize('index,label,statement', hostile_contracts(), ids=lambda value: value if isinstance(value,str) and len(value)<100 else None)
def test_stronger_or_guardless_algebra_claims_are_rejected(index, label, statement):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())


def encode_beta(values, salt=0):
    """Independent exact CRT model input, never proof authority."""
    values = tuple(values)
    if not values:
        return salt, 1
    scale = math.factorial(len(values)) * (max(values) + 1)
    code, period = 0, 1
    for i, value in enumerate(values):
        modulus = 1 + (i+1)*scale
        assert 0 <= value < modulus and math.gcd(period, modulus) == 1
        code += period * ((value-code)*pow(period, -1, modulus) % modulus)
        period *= modulus
    return code+salt*period, scale


def beta_value(code, i):
    return code[0] % (1+(i+1)*code[1])


def actual_sum(values):
    table = encode_beta(values)
    partials = tuple(itertools.accumulate(values, initial=0))
    trace = encode_beta(partials, salt=1)
    assert beta_value(trace, 0) == 0
    for i, value in enumerate(values):
        assert beta_value(table, i) == value
        assert beta_value(trace, i+1) == beta_value(trace, i)+beta_value(table, i)
    assert beta_value(trace, len(values)) == sum(values)
    return sum(values)


def congruence_witness(p, left, right):
    assert p > 0 and (left-right) % p == 0
    u, v = (max(right-left, 0)//p, max(left-right, 0)//p)
    assert left+p*u == right+p*v
    return u, v


def product_prefix_model(p, left, right, length, salt=0):
    assert p > 0 and length >= 0
    assert all(0 <= a < p for a in (*left, *right))
    # The exterior entries are deliberately nonzero and noncanonical; the
    # convolution definition reads them as padded zero, not as actual input.
    left_code = encode_beta((*left, p+3), salt=salt)
    right_code = encode_beta((*right, p+4), salt=salt+1)
    values, diagonals = [], []
    for i in range(length):
        terms = []
        for j in range(i+1):
            k = i-j
            assert j+k == i
            a = beta_value(left_code, j) if j < len(left) else 0
            b = beta_value(right_code, k) if k < len(right) else 0
            terms.append(a*b)
        total = actual_sum(terms)
        value = total % p
        assert 0 <= value < p
        congruence_witness(p, total, value)
        values.append(value)
        diagonals.append(tuple(terms))
    result_code = encode_beta((*values, p+7), salt=salt+2)
    assert all(beta_value(result_code, i) == value for i, value in enumerate(values))
    assert beta_value(result_code, length) == p+7
    return tuple(values), tuple(diagonals), result_code


MODEL_CASES = tuple(dict.fromkeys((p, A, B, D, side) for p in (1,2,3,5,6)
    for A,B in (
        ((), ()), ((0,), (0,)), ((p-1,), (1 % p,)),
        ((1 % p,0), (p-1,1 % p)), ((0,p-1,1 % p), (1 % p,1 % p,p-1)),
    )
    for D in ((), (0,), (1 % p,), (p-1,1 % p))
    for side in ('left', 'right')))


@pytest.mark.parametrize('p,A,B,D,side', MODEL_CASES)
def test_actual_beta_terms_sums_residues_and_product_laws(p, A, B, D, side):
    total = tuple((a+b) % p for a,b in zip(A,B,strict=True))
    difference = tuple((a-b) % p for a,b in zip(A,B,strict=True))
    proper = len(A)+len(D)-1 if A and D else 0
    for length in dict.fromkeys((0, 1, proper, proper+2)):
        products = []
        for index, operand in enumerate((A, B, total, difference)):
            factors_pair = (D, operand) if side == 'left' else (operand, D)
            products.append(product_prefix_model(p, *factors_pair, length, salt=index))
        u,v,w,d = (product[0] for product in products)
        assert tuple((a+b) % p for a,b in zip(u,v,strict=True)) == w
        assert tuple((a-b) % p for a,b in zip(u,v,strict=True)) == d
        assert tuple((a+b) % p for a,b in zip(v,d,strict=True)) == u
        for i in range(length):
            for a,b,c in zip(*(product[1][i] for product in products[:3]),strict=True):
                congruence_witness(p, a+b, c)
            congruence_witness(p, actual_sum(products[0][1][i])+actual_sum(products[1][1][i]),
                               actual_sum(products[2][1][i]))
        if proper == 0:
            assert all(value == 0 for values in (u,v,w,d) for value in values)
        if length > proper:
            assert all(value == 0 for values in (u,v,w,d) for value in values[proper:])


@pytest.mark.parametrize('values', ((),(0,),(1,),(2,1),(1,0,1)))
def test_equal_coefficient_prefixes_do_not_identify_codes_or_exterior_entries(values):
    first = encode_beta((*values,7), salt=0)
    second = encode_beta((*values,9), salt=2)
    assert first != second
    assert all(beta_value(first,i) == beta_value(second,i) for i in range(len(values)))
    assert beta_value(first,len(values)) != beta_value(second,len(values))


@pytest.mark.parametrize('p', (2,3,5))
def test_distributivity_is_not_merely_equality_of_field_evaluations(p):
    nonzero = (1,)+(0,)*(p-2)+(p-1,0)  # X^p-X in highest-degree-first order.
    zero = (0,)*len(nonzero)
    assert nonzero != zero
    source, target = encode_beta(nonzero), encode_beta(zero)
    assert beta_value(source,0) == 1 and beta_value(target,0) == 0
    for x in range(p):
        accumulator = 0
        for value in nonzero:
            accumulator = (accumulator*x+value) % p
        assert accumulator == 0


def test_characteristic_two_identity_is_natural_one_not_signed_code_two():
    values, _, _ = product_prefix_model(2, (1,), (1,), 1)
    assert values == (1,)
    assert 1 % 2 == 1 and 2 % 2 == 0


def test_actual_modular_distribution_does_not_claim_natural_sum_equality():
    u, _, _ = product_prefix_model(3, (1,), (2,), 1)
    v, _, _ = product_prefix_model(3, (1,), (2,), 1)
    w, _, _ = product_prefix_model(3, (1,), (1,), 1)
    assert u[0]+v[0] == 4 and w[0] == 1
    congruence_witness(3, u[0]+v[0], w[0])


def test_raw_diagonal_positions_distinguish_the_two_multiplication_sides():
    _, left, _ = product_prefix_model(5, (1,2), (2,2), 2)
    _, right, _ = product_prefix_model(5, (2,2), (1,2), 2)
    assert left[1][0] == 2 and right[1][0] == 4


@pytest.mark.parametrize('p,left,right,length', ((0,(0,),(0,),1),(2,(2,),(1,),1),(3,(1,),(3,),1),(2,(1,),(1,),-1)))
def test_model_rejects_invalid_residue_domains(p,left,right,length):
    with pytest.raises(AssertionError):
        product_prefix_model(p,left,right,length)
