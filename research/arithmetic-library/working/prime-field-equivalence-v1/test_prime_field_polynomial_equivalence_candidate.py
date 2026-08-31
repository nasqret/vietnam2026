"""Independent representation-converse and additive-congruence regressions.

Only exact source-derived predecessor statements become ordinary hypotheses
for the original conditional HA checker.  No Alpha import, saved receipt,
closed replay, independent Lean result, or admission authority is supplied.
Concrete CRT-beta models below diagnose contracts; they are not proofs.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import importlib.util
from pathlib import Path
import re
import sys

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula
from working_equivalence_support import REPRESENTATION_ALIAS, temporary_representation_alias


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FROZEN = HERE.parent / 'prime-field-euclidean-v1'
if str(ROOT / 'peano-lab/py/tests') not in sys.path:
    sys.path.insert(0, str(ROOT / 'peano-lab/py/tests'))
from test_prime_field_polynomial_candidate import (
    decode_beta, decoded_prefix, encode_beta, expected_add as Add,
    expected_and as And, expected_at as At, expected_equal as Equal,
    expected_lt as Lt, expected_prime as Prime, expected_repeat as Repeat,
    same_ast,
)
from test_prime_field_polynomial_subtraction_candidate import expected_subtract as Subtract


SOURCE_SHA256 = '929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373'
REPRESENTATION_SHA256 = 'fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a'


def load_actual_source(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Imported functions retain their actual source module after this owned
# import scope ends; no future library alias may escape pytest collection.
with temporary_representation_alias() as representation:
    candidate = load_actual_source(
        'working_prime_field_polynomial_equivalence_candidate',
        HERE / 'prime_field_polynomial_equivalence_candidate.py',
    )


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_equivalence_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_subtraction_candidate import make_prime_field_polynomial_subtraction_candidate_theorems

    predecessors = (*THEOREMS,
        *representation.make_prime_field_polynomial_representation_candidate_theorems(TheoremSpec),
        *make_prime_field_polynomial_candidate_theorems(TheoremSpec),
        *make_prime_field_polynomial_subtraction_candidate_theorems(TheoremSpec))
    result = {}
    for row in predecessors:
        assert row.name not in result or result[row.name] == row
        result[row.name] = row
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


def Le(a, b):
    return f'exists independent_equivalence_gap. independent_equivalence_gap+({a})=({b})'


def Pad(b, c, length, count, d, e):
    index, value = 'independent_padding_index', 'independent_padding_value'
    return And(Repeat(d, e, '0', count),
        f'forall {index} {value}. ({Lt(index,length)}) -> ({At(b,c,index,value)}) -> '
        f'({At(d,e,f"({count})+{index}",value)})')


def Power(b, c, length, power, value):
    index = 'independent_equivalence_position'
    inside = f'exists {index}. ({And(f"{index}+S ({power})=({length})",At(b,c,index,value))})'
    return f'({inside}) \\/ ({And(Le(length,power),f"({value})=0")})'


def Equivalent(b, c, length, d, e, other_length):
    power, left, right = 'independent_power', 'independent_left_value', 'independent_right_value'
    return (f'forall {power} {left} {right}. ({Power(b,c,length,power,left)}) -> '
            f'({Power(d,e,other_length,power,right)}) -> {left}={right}')


def contract(parameters, premises, result):
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + part + ')' for part in (*premises, result)
    )


def independent_contracts():
    result = [(('b', 'c', 'L', 't', 'd', 'e'),
               (Equivalent('b', 'c', 'L', 'd', 'e', 't+L'),),
               Pad('b', 'c', 'L', 't', 'd', 'e'))]
    for operation in (Add, Subtract):
        parameters = ('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', 't',
                      'AB', 'AC', 'BB', 'BC', 'CB', 'CC')
        premises = (Prime('p'), operation('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L'),
                    Pad('ab', 'ac', 'L', 't', 'AB', 'AC'), Pad('bb', 'bc', 'L', 't', 'BB', 'BC'),
                    operation('p', 'AB', 'AC', 'BB', 'BC', 'CB', 'CC', 't+L'))
        result.append((parameters, premises, Pad('cb', 'cc', 'L', 't', 'CB', 'CC')))
    for operation in (Add, Subtract):
        parameters = ('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L',
                      'AB', 'AC', 'BB', 'BC', 'CB', 'CC', 'K')
        premises = (Prime('p'), Equivalent('ab', 'ac', 'L', 'AB', 'AC', 'K'),
                    Equivalent('bb', 'bc', 'L', 'BB', 'BC', 'K'),
                    operation('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L'),
                    operation('p', 'AB', 'AC', 'BB', 'BC', 'CB', 'CC', 'K'))
        result.append((parameters, premises, Equivalent('cb', 'cc', 'L', 'CB', 'CC', 'K')))
    return tuple(result)


EXPECTED_NAMES = (
    'prime_field_polynomial_equivalent_implies_left_pad',
    'prime_field_polynomial_add_left_pad_output',
    'prime_field_polynomial_subtract_left_pad_output',
    'prime_field_polynomial_add_equivalent_congruent',
    'prime_field_polynomial_subtract_equivalent_congruent',
)
METRICS = ((78, 30), (92, 51), (92, 51), (195, 52), (195, 52))


def test_exact_source_pins_inventory_and_dependency_order():
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest() == SOURCE_SHA256
    assert sha256(Path(representation.__file__).read_bytes()).hexdigest() == REPRESENTATION_SHA256
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert len(rows()) == len(independent_contracts()) == 5
    assert sum(len(row.dependencies) for row in rows()) == 24
    assert sum(len(row.script) for row in rows()) == 544
    assert sum(nodes for nodes, _ in METRICS) == 652
    known = set(provider_core())
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in known and row.script
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= known
        assert all(re.search(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", '\n'.join(row.script))
                   for name in row.dependencies)
        assert not any(command.startswith(('use ', 'admit', 'sorry')) or 'DNE' in command for command in row.script)
        known.add(row.name)


@pytest.mark.parametrize('index', range(5))
def test_independent_fully_expanded_closed_contract(index):
    same_ast(_closed_formula(rows()[index].statement),
             _closed_formula(contract(*independent_contracts()[index])))


def test_converse_is_unconditional_on_primality_and_additive_claims_do_not_assume_outputs():
    parameters, premises, conclusion = independent_contracts()[0]
    assert parameters == ('b', 'c', 'L', 't', 'd', 'e') and len(premises) == 1
    assert conclusion == Pad('b', 'c', 'L', 't', 'd', 'e')
    for parameters, premises, conclusion in independent_contracts()[1:]:
        assert premises[0] == Prime('p') and len(premises) == 5
        assert conclusion not in premises
    assert not any('divisor' in row.name or 'gcd' in row.name or 'bezout' in row.name for row in rows())


def test_source_imports_only_original_helpers_and_the_frozen_representation():
    tree = ast.parse(Path(candidate.__file__).read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.ImportFrom) for node in imports)
    assert {node.module for node in imports} == {
        '__future__', 'typing', 'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate',
        'peano_lab.library.prime_field_polynomial_subtraction_candidate',
        'peano_lab.library.prime_field_tables_candidate',
    }
    assert all(node.level == 0 for node in imports)
    import peano_lab.library as library
    assert REPRESENTATION_ALIAS not in sys.modules
    assert REPRESENTATION_ALIAS.rsplit('.', 1)[1] not in vars(library)


def test_new_statements_are_distinct_from_each_other_and_selected_dependency_statements():
    # This is a direct-support check, not the separately scheduled whole-parent novelty gate.
    from peano_lab.library.formula_dag import FormulaArena

    table = body_core()
    names = set(EXPECTED_NAMES) | {name for row in rows() for name in row.dependencies}
    encoded = {name: FormulaArena().freeze(_closed_formula(table[name].statement)).to_json() for name in names}
    for name in EXPECTED_NAMES:
        assert all(encoded[name] != other for key, other in encoded.items() if key != name)


@pytest.mark.parametrize('index', range(5), ids=EXPECTED_NAMES)
def test_actual_original_ha_body_and_exact_shape(index):
    row = rows()[index]
    try:
        receipt = replay_candidate_bodies((row,), core=body_core())[0]
        assert receipt.name == row.name
        assert (receipt.dependency_count, receipt.command_count) == (len(row.dependencies), len(row.script))
        assert (receipt.proof_nodes, receipt.proof_depth) == METRICS[index]
        assert 0 < receipt.proof_objects <= receipt.proof_nodes
    finally:
        gc.collect()


@pytest.mark.parametrize('index', range(5))
@pytest.mark.parametrize('mutation', ('false_conclusion', 'missing_body', 'truncated_body'))
def test_false_or_incomplete_body_rejected(index, mutation):
    original = rows()[index]
    if mutation == 'false_conclusion':
        parameters, premises, _ = independent_contracts()[index]
        changed = replace(original, statement=contract(parameters, premises, '0=1'))
    elif mutation == 'missing_body':
        changed = replace(original, script=())
    else:
        changed = replace(original, script=original.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


EDGES = tuple((index, dependency) for index, row in enumerate(rows()) for dependency in row.dependencies)


@pytest.mark.parametrize('index,dependency', EDGES, ids=tuple(f'drop-{i:02d}' for i in range(len(EDGES))))
def test_every_removed_dependency_is_rejected(index, dependency):
    row = rows()[index]
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('index,dependency', EDGES, ids=tuple(f'poison-{i:02d}' for i in range(len(EDGES))))
def test_every_poisoned_dependency_is_rejected(index, dependency):
    table = body_core()
    table[dependency] = replace(table[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],), core=table)


def changed_contracts():
    result = []
    for index, (parameters, premises, conclusion) in enumerate(independent_contracts()):
        for position in range(len(premises)):
            result.append((index, f'removed-premise-{position}',
                           contract(parameters, premises[:position] + premises[position+1:], conclusion)))
    wrong = {
        0: (
            ('raw-codes', And('b=d', 'c=e')),
            ('unshifted-prefix', Equal('b', 'c', 'd', 'e', 'L')),
            ('unbounded-copy', 'forall i a. (' + At('b', 'c', 'i', 'a') + ') -> (' + At('d', 'e', 't+i', 'a') + ')'),
            ('all-output-zero', Repeat('d', 'e', '0', 't+L')),
        ),
        1: (('unshifted-output', Equal('cb', 'cc', 'CB', 'CC', 'L')),
            ('one-more-source-entry', Pad('cb', 'cc', 'S L', 't', 'CB', 'CC'))),
        2: (('unshifted-output', Equal('cb', 'cc', 'CB', 'CC', 'L')),
            ('one-more-source-entry', Pad('cb', 'cc', 'S L', 't', 'CB', 'CC'))),
        3: (('raw-codes', And('cb=CB', 'cc=CC')), ('same-length', 'L=K'),
            ('unshifted-output', Equal('cb', 'cc', 'CB', 'CC', 'L'))),
        4: (('raw-codes', And('cb=CB', 'cc=CC')), ('same-length', 'L=K'),
            ('unshifted-output', Equal('cb', 'cc', 'CB', 'CC', 'L'))),
    }
    for index, mutations in wrong.items():
        parameters, premises, _ = independent_contracts()[index]
        for label, conclusion in mutations:
            result.append((index, label, contract(parameters, premises, conclusion)))
    return tuple(result)


CHANGED_CONTRACTS = changed_contracts()


@pytest.mark.parametrize('index,label,statement', CHANGED_CONTRACTS,
                         ids=tuple(f'{i}-{label}' for i, label, _ in CHANGED_CONTRACTS))
def test_fixed_body_rejects_changed_guards_or_overstrong_conclusion(index, label, statement):
    # Rejection concerns this fixed checked body; not every omitted Prime guard
    # is asserted to have a numerical counterexample at every modulus.
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())


def model_power(code, length, power):
    return 0 if power >= length else decode_beta(code, length - 1 - power)


def model_equivalent(first, length, second, other_length):
    # At and above max(length,other_length), both graph branches are exterior zero.
    return all(model_power(first, length, k) == model_power(second, other_length, k)
               for k in range(max(length, other_length) + 2))


def model_pad(first, length, count, second):
    return (all(decode_beta(second, i) == 0 for i in range(count))
            and all(decode_beta(first, i) == decode_beta(second, count+i) for i in range(length)))


def model_operation(kind, p, first, second, result, length):
    for i in range(length):
        a, b, r = (decode_beta(code, i) for code in (first, second, result))
        if not all(0 <= value < p for value in (a, b, r)):
            return False
        left, right = (a+b, r) if kind == 'add' else (b+r, a)
        if left < right or (left-right) % p != 0:
            return False
        quotient = (left-right) // p
        if left != right + p*quotient:
            return False
    return True


SOURCE_VALUES = ((), (0,), (1,), (2,), (7,), (0, 0), (0, 1), (1, 0),
                 (2, 3), (0, 5, 0), (4, 0, 2))


@pytest.mark.parametrize('values', SOURCE_VALUES)
@pytest.mark.parametrize('count', (0, 1, 2, 4))
@pytest.mark.parametrize('encoding', (2, 3))
def test_actual_beta_converse_for_empty_unbounded_and_reencoded_inputs(values, count, encoding):
    source = encode_beta((*values, 11, 17), 1)
    target = encode_beta((0,)*count + (*values, 23, 29), encoding)
    length = len(values)
    assert model_equivalent(source, length, target, count+length)
    assert model_pad(source, length, count, target)
    assert decoded_prefix(source, length) == tuple(values)
    assert decode_beta(source, length) != decode_beta(target, count+length)
    assert source != target


ALIGNED_INPUTS = (((), ()), ((0,), (0,)), ((1,), (1,)),
                  ((0, 1), (1, 0)), ((2, 0, 1), (1, 1, 0)))


@pytest.mark.parametrize('kind', ('add', 'subtract'))
@pytest.mark.parametrize('p', (2, 3, 5, 7))
@pytest.mark.parametrize('values', ALIGNED_INPUTS)
@pytest.mark.parametrize('padding', ((0, 0), (0, 2), (2, 0), (1, 3)))
def test_actual_beta_aligned_operations_have_equivalent_outputs(kind, p, values, padding):
    left, right = (tuple(value % p for value in data) for data in values)
    original_padding, other_padding = padding
    a, b = (0,)*original_padding + left, (0,)*original_padding + right
    A, B = (0,)*other_padding + left, (0,)*other_padding + right
    operation = (lambda x, y: (x+y) % p) if kind == 'add' else (lambda x, y: (x-y) % p)
    c = tuple(operation(x, y) for x, y in zip(a, b, strict=True))
    C = tuple(operation(x, y) for x, y in zip(A, B, strict=True))
    first = tuple(encode_beta((*data, 11, 13), 1) for data in (a, b, c))
    second = tuple(encode_beta((*data, 17, 19), 2) for data in (A, B, C))
    L, K = len(a), len(A)
    assert model_equivalent(first[0], L, second[0], K)
    assert model_equivalent(first[1], L, second[1], K)
    assert model_operation(kind, p, *first, L)
    assert model_operation(kind, p, *second, K)
    assert model_equivalent(first[2], L, second[2], K)
    if L <= K:
        assert all(model_pad(x, L, K-L, y) for x, y in zip(first, second, strict=True))
    else:
        assert all(model_pad(y, K, L-K, x) for x, y in zip(first, second, strict=True))
    assert first[2] != second[2]
    assert decode_beta(first[2], L) != decode_beta(second[2], K)


@pytest.mark.parametrize('kind', ('add', 'subtract'))
@pytest.mark.parametrize('changed_input', (0, 1))
def test_missing_input_equivalence_has_a_real_output_counterexample(kind, changed_input):
    original = (encode_beta((0,)), encode_beta((0,)), encode_beta((0,)))
    changed = [0, 0]
    changed[changed_input] = 1
    result = (changed[0]+changed[1]) % 3 if kind == 'add' else (changed[0]-changed[1]) % 3
    other = tuple(encode_beta((value,), 2) for value in (*changed, result))
    assert model_operation(kind, 3, *original, 1)
    assert model_operation(kind, 3, *other, 1)
    assert not model_equivalent(original[changed_input], 1, other[changed_input], 1)
    assert not model_equivalent(original[2], 1, other[2], 1)


def test_a_missing_leading_zero_is_not_implied_by_unshifted_prefix_equality():
    source = encode_beta((1,))
    trailing = encode_beta((1, 0))
    assert decode_beta(source, 0) == decode_beta(trailing, 0)
    assert not model_equivalent(source, 1, trailing, 2)
    assert not model_pad(source, 1, 1, trailing)


def test_field_evaluation_equality_cannot_replace_formal_coefficient_equivalence():
    polynomial = encode_beta((1, 1, 0))
    zero = encode_beta(())
    assert all((x*x+x) % 2 == 0 for x in (0, 1))
    assert not model_equivalent(polynomial, 3, zero, 0)
    assert not model_pad(zero, 0, 3, polynomial)


def test_characteristic_two_uses_canonical_natural_one_not_signed_code_two():
    one, zero, two = (encode_beta((value,)) for value in (1, 0, 2))
    assert model_operation('add', 2, one, one, zero, 1)
    assert model_operation('subtract', 2, one, one, zero, 1)
    assert not model_operation('add', 2, two, zero, two, 1)


def test_empty_prefixes_leave_arbitrary_codes_and_outside_values_unconstrained():
    first, second = (27, 19), (31, 7)
    assert first != second
    assert model_equivalent(first, 0, second, 0)
    assert model_pad(first, 0, 0, second)
    assert model_operation('add', 2, first, first, second, 0)
    assert model_operation('subtract', 2, first, first, second, 0)
