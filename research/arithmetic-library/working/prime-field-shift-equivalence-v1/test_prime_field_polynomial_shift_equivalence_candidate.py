"""Independent formal-shift contracts, actual beta models, and original HA.

The proof checks are dependency-curried, not complete-bundle or admission
checks. All providers are actual canonical factories plus the exact frozen
working shift source, loaded without installing package aliases. Numerical
models and test observations are never proof or publication authority.
"""

from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass, replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
import math
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
SOURCE = HERE / 'prime_field_polynomial_shift_equivalence_candidate.py'
SOURCE_SHA256 = '8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068'
SHIFT = WORKING / 'prime-field-shift-v1/prime_field_polynomial_shift_candidate.py'
FROZEN_PINS = {
    'prime-field-shift-v1/prime_field_polynomial_shift_candidate.py': '325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b',
    'prime-field-shift-v1/test_prime_field_polynomial_shift_candidate.py': '0622fb92978fcf028842aa4d9822ef61213642eb852e080f7c787dcea4bb395f',
    'prime-field-scalar-v1/prime_field_polynomial_scalar_convolution_candidate.py': 'e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e',
    'prime-field-scalar-v1/test_prime_field_polynomial_scalar_convolution_candidate.py': '881452ada0b5dc3be7d6cd00ee31dc08075b07f51d83595ee60f8cfb40d4c6e5',
    'prime-field-append-v1/prime_field_polynomial_append_candidate.py': '271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042',
    'prime-field-append-v1/test_prime_field_polynomial_append_candidate.py': '0c554b05b2c7e2c40e3b0e8044160379a3284bb173e48d59d77def0cad4272aa',
}
PROVIDER_PINS = {
    'theorems.py': '05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919',
    'prime_field_arithmetic_candidate.py': 'd4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90',
    'prime_field_polynomial_candidate.py': '644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72',
    'prime_field_polynomial_convolution_candidate.py': '20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24',
    'prime_field_polynomial_representation_candidate.py': 'fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a',
    'prime_field_tables_candidate.py': '2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400',
    'finite_sum_theorems.py': '0d60b7a4fa21161def737fc6759b23e0679694052e95d97b419aa1ecb293c56e',
}
PRIVATE_NAMES = ('working_shift_equivalence_candidate', 'working_shift_equivalence_frozen_shift')
NAME = 'prime_field_polynomial_shift_equivalent_congruent'
DEPENDENCIES = (
    'zero_or_succ', 'prime_field_polynomial_shift_power_zero',
    'prime_field_polynomial_shift_power_successor', 'prime_field_polynomial_power_coefficient_exists',
    'prime_field_polynomial_power_coefficient_functional',
)


def protected_bindings():
    return {name: value for name, value in sys.modules.items()
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


candidate = load_file(PRIVATE_NAMES[0], SOURCE)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_shift_equivalence_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def frozen_shift():
    assert sha256(SHIFT.read_bytes()).hexdigest() == FROZEN_PINS['prime-field-shift-v1/prime_field_polynomial_shift_candidate.py']
    return load_file(PRIVATE_NAMES[1], SHIFT)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_polynomial_representation_candidate import make_prime_field_polynomial_representation_candidate_theorems

    for filename, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / filename).read_bytes()).hexdigest() == digest
    core = {row.name: row for row in THEOREMS}
    for factory in (make_prime_field_polynomial_representation_candidate_theorems,
                    frozen_shift().make_prime_field_polynomial_shift_candidate_theorems):
        for row in factory(TheoremSpec):
            if row.name in core:
                assert core[row.name] == row
            core[row.name] = row
    return core


def body_core():
    return dict(provider_core())


def same_ast(left, right):
    pending, seen = [(left, right)], set()
    while pending:
        a, b = pending.pop()
        assert type(a) is type(b)
        pair = id(a), id(b)
        if pair in seen:
            continue
        seen.add(pair)
        if is_dataclass(a):
            pending.extend((getattr(a, field.name), getattr(b, field.name)) for field in fields(a))
        else:
            assert a == b


# Native expected graphs, independent of every candidate/provider constructor.
def And(*parts):
    result = '(' + parts[-1] + ')'
    for part in reversed(parts[:-1]):
        result = '(' + part + ') /\\ (' + result + ')'
    return result


def Lt(a, b):
    return f'exists strict_gap. strict_gap+S ({a})=({b})'


def Le(a, b):
    return f'exists weak_gap. weak_gap+({a})=({b})'


def At(b, c, i, a):
    return And(f'exists residue_gap. residue_gap+S ({a})=S ((S ({i}))*({c}))',
               f'exists quotient. ({b})=quotient*S ((S ({i}))*({c}))+({a})')


def Equal(b, c, d, e, length):
    return f'forall index value. ({Lt("index",length)}) -> ({At(b,c,"index","value")}) -> ({At(d,e,"index","value")})'


def Shift(b, c, length, d, e):
    return And(Equal(b, c, d, e, length), At(d, e, length, '0'))


def Power(b, c, length, power, value):
    inside = 'exists position. ' + And(f'position+S ({power})=({length})', At(b, c, 'position', value))
    outside = And(Le(length, power), f'({value})=0')
    return '(' + inside + ') \\/ (' + outside + ')'


def Equivalent(b, c, length, d, e, other_length):
    return (f'forall power left_value right_value. ({Power(b,c,length,"power","left_value")}) -> '
            f'({Power(d,e,other_length,"power","right_value")}) -> left_value=right_value')


PARAMETERS = ('b', 'c', 'L', 'd', 'e', 'M', 'ub', 'uc', 'vb', 'vc')
PREMISES = (
    Equivalent('b', 'c', 'L', 'd', 'e', 'M'),
    Shift('b', 'c', 'L', 'ub', 'uc'),
    Shift('d', 'e', 'M', 'vb', 'vc'),
)
CONCLUSION = Equivalent('ub', 'uc', 'S L', 'vb', 'vc', 'S M')


def contract(premises=PREMISES, conclusion=CONCLUSION):
    return 'forall ' + ' '.join(PARAMETERS) + '. ' + ' -> '.join('(' + part + ')' for part in (*premises, conclusion))


def test_exact_source_factory_ownership_and_dependency_order():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == (NAME,)
    assert rows()[0].dependencies == DEPENDENCIES
    assert len(rows()[0].script) == 138
    assert len(set(DEPENDENCIES)) == len(DEPENDENCIES) == 5
    assert set(DEPENDENCIES) <= body_core().keys()
    assert NAME not in body_core()


def test_independent_expanded_contract_has_no_field_or_nonempty_premise():
    same_ast(_closed_formula(rows()[0].statement), _closed_formula(contract()))
    assert candidate.PARAMETERS == PARAMETERS
    assert 'p' not in PARAMETERS and len(PREMISES) == 3
    assert not any(word in rows()[0].statement for word in ('Prime', 'Horner', 'ModEq', 'FpInv'))


def test_exact_existing_shift_expansion_and_no_new_alias_or_loader():
    parameters = ('b', 'c', 'L', 'd', 'e')
    prefix = 'forall ' + ' '.join(parameters) + '. '
    actual = candidate._shift(*parameters, 'independent')
    original = frozen_shift().prime_field_polynomial_shift_relation(*parameters, tag='independent', variables=parameters)
    same_ast(_closed_formula(prefix + actual), _closed_formula(prefix + original))
    same_ast(_closed_formula(prefix + actual), _closed_formula(prefix + Shift(*parameters)))
    tree = ast.parse(SOURCE.read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.ImportFrom) and node.level == 0 for node in imports)
    assert {node.module for node in imports} == {
        '__future__', 'typing', 'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate',
        'peano_lab.library.prime_field_tables_candidate',
    }
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert candidate.__all__ == ['make_prime_field_polynomial_shift_equivalence_candidate_theorems']
    assert not any(name.endswith('_relation') for name in vars(candidate))
    assert not any(word in NAME for word in ('associative', 'gcd', 'bezout', 'division_unique'))


@pytest.mark.parametrize('name', ('peano_lab.library.editions_v_shift_equivalence_guard', *PRIVATE_NAMES))
def test_explicit_file_loader_preserves_preexisting_module_identity(name, monkeypatch):
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, marker)
    before = protected_bindings()
    loaded = load_file(PRIVATE_NAMES[0], SOURCE)
    shifted = load_file(PRIVATE_NAMES[1], SHIFT)
    assert Path(loaded.__file__) == SOURCE and Path(shifted.__file__) == SHIFT
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())
    assert sys.modules[name] is marker


def test_canonical_provider_paths_and_all_six_frozen_companion_bytes():
    provider_core()
    for filename, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / filename).read_bytes()).hexdigest() == digest
        name = 'peano_lab.library.' + filename.removesuffix('.py')
        if name in sys.modules:
            assert Path(sys.modules[name].__file__).resolve() == (LIBRARY / filename).resolve()
    for path, digest in FROZEN_PINS.items():
        assert sha256((WORKING / path).read_bytes()).hexdigest() == digest


def test_local_novelty_against_exact_selected_types_only():
    from peano_lab.library.formula_dag import FormulaArena

    actual = FormulaArena().freeze(_closed_formula(rows()[0].statement)).to_json()
    for name in DEPENDENCIES:
        assert actual != FormulaArena().freeze(_closed_formula(body_core()[name].statement)).to_json()


def test_actual_original_ha_body_and_exact_nodes_depth():
    row = rows()[0]
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == NAME
    assert (receipt.dependency_count, receipt.command_count) == (5, 138)
    assert (receipt.proof_nodes, receipt.proof_depth) == (147, 41)
    assert 0 < receipt.proof_objects <= receipt.proof_nodes


@pytest.mark.parametrize('mutation', ('false_conclusion', 'missing_body', 'truncated_body'))
def test_false_or_incomplete_body_is_rejected(mutation):
    row = rows()[0]
    changed = replace(row, statement=contract(conclusion='0=1')) if mutation == 'false_conclusion' else replace(
        row, script=() if mutation == 'missing_body' else row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('dependency', DEPENDENCIES)
def test_each_removed_dependency_is_rejected(dependency):
    row = rows()[0]
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('dependency', DEPENDENCIES)
def test_each_poisoned_dependency_is_rejected(dependency):
    core = body_core()
    core[dependency] = replace(core[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[0],), core=core)


def changed_contracts():
    result = [(f'missing-premise-{i}', contract(PREMISES[:i] + PREMISES[i+1:])) for i in range(3)]
    for side, index, prefix, zero in (
        ('left', 1, Equal('b','c','ub','uc','L'), At('ub','uc','L','0')),
        ('right', 2, Equal('d','e','vb','vc','M'), At('vb','vc','M','0')),
    ):
        for label, weakened in (('without-zero', prefix), ('without-prefix', zero)):
            premises = PREMISES[:index] + (weakened,) + PREMISES[index+1:]
            result.append((side + '-' + label, contract(premises)))
    for label, conclusion in (
        ('raw-output-codes', And('ub=vb','uc=vc')),
        ('unshifted-right-length', Equivalent('ub','uc','S L','vb','vc','M')),
        ('unshifted-original-right', Equivalent('ub','uc','S L','d','e','M')),
    ):
        result.append((label, contract(conclusion=conclusion)))
    return tuple(result)


CHANGED = changed_contracts()


@pytest.mark.parametrize('label,statement', CHANGED, ids=tuple(label for label, _ in CHANGED))
def test_fixed_body_rejects_altered_guards_or_other_claim(label, statement):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[0], statement=statement),), core=body_core())


def encode_beta(values, multiplier=1):
    values = tuple(values)
    assert type(multiplier) is int and multiplier > 0
    assert all(type(value) is int and value >= 0 for value in values)
    scale = (max(values, default=0) + 1) * math.factorial(max(1, len(values))) * multiplier
    code, product = 0, 1
    for index, value in enumerate(values):
        modulus = 1 + (index+1)*scale
        assert value < modulus and math.gcd(product, modulus) == 1
        correction = ((value-code) * pow(product, -1, modulus)) % modulus
        code += product*correction
        product *= modulus
    return code, scale


def beta_at(code, index):
    return code[0] % (1 + (index+1)*code[1])


def at_holds(code, index, value):
    modulus = 1 + (index+1)*code[1]
    quotient, residue = divmod(code[0], modulus)
    gap = modulus-value-1
    return gap >= 0 and gap+value+1 == modulus and code[0] == quotient*modulus+value and residue == value


def prefix_equal(source, target, length):
    return all(at_holds(target, index, beta_at(source,index)) for index in range(length))


def shift_holds(source, length, target):
    return prefix_equal(source, target, length) and at_holds(target, length, 0)


def power_value(code, length, power):
    return beta_at(code, length-power-1) if power < length else 0


def power_holds(code, length, power, value):
    return any(index+power+1 == length and at_holds(code,index,value) for index in range(length)) or (
        length <= power and value == 0)


def formal_equal(left, length, right, other_length):
    return all(power_value(left,length,power) == power_value(right,other_length,power)
               for power in range(max(length,other_length)))


BASES = ((), (0,), (1,), (1,0), (0,2), (7,0,11))


@pytest.mark.parametrize('base', BASES)
@pytest.mark.parametrize('left_padding', range(3))
@pytest.mark.parametrize('right_padding', range(3))
@pytest.mark.parametrize('reencoding', range(2))
def test_actual_beta_models_with_different_lengths_and_free_exterior(base, left_padding, right_padding, reencoding):
    left_values, right_values = (0,)*left_padding+base, (0,)*right_padding+base
    length, other_length = len(left_values), len(right_values)
    left = encode_beta(left_values+(9,4), 1+reencoding)
    right = encode_beta(right_values+(3,10), 3+reencoding)
    shifted_left = encode_beta(left_values+(0,6,13), 5+reencoding)
    shifted_right = encode_beta(right_values+(0,2,15), 7+reencoding)
    assert formal_equal(left,length,right,other_length)
    assert shift_holds(left,length,shifted_left) and shift_holds(right,other_length,shifted_right)
    assert shifted_left != shifted_right
    assert beta_at(shifted_left,length+1) == 6 and beta_at(shifted_right,other_length+1) == 2
    for power in range(max(length,other_length)+5):
        a = power_value(shifted_left,length+1,power)
        b = power_value(shifted_right,other_length+1,power)
        assert power_holds(shifted_left,length+1,power,a)
        assert power_holds(shifted_right,other_length+1,power,b)
        assert a == b
        if power == 0:
            assert a == b == 0
        else:
            original_left = power_value(left,length,power-1)
            original_right = power_value(right,other_length,power-1)
            assert power_holds(left,length,power-1,original_left)
            assert power_holds(right,other_length,power-1,original_right)
            assert original_left == original_right == a == b
    assert formal_equal(shifted_left,length+1,shifted_right,other_length+1)


@pytest.mark.parametrize('removed,left,right,shifted_left,shifted_right', (
    (0,(1,),(2,),(1,0),(2,0)),
    (1,(1,),(1,),(2,0),(1,0)),
    (2,(1,),(1,),(1,1),(1,0)),
    (3,(1,),(1,),(1,0),(2,0)),
    (4,(1,),(1,),(1,0),(1,1)),
))
def test_each_actual_input_clause_has_a_concrete_counterexample(removed, left, right, shifted_left, shifted_right):
    a,b,u,v = map(encode_beta,(left,right,shifted_left,shifted_right))
    clauses = (formal_equal(a,len(left),b,len(right)),
               prefix_equal(a,u,len(left)),at_holds(u,len(left),0),
               prefix_equal(b,v,len(right)),at_holds(v,len(right),0))
    assert not clauses[removed] and all(value for index,value in enumerate(clauses) if index != removed)
    assert not formal_equal(u,len(left)+1,v,len(right)+1)


def test_both_empty_sources_allow_arbitrary_codes_but_shift_has_real_zero():
    a,b = (17,0),(100,7)
    u,v = encode_beta((0,9)),encode_beta((0,8),3)
    assert formal_equal(a,0,b,0) and shift_holds(a,0,u) and shift_holds(b,0,v)
    assert formal_equal(u,1,v,1) and at_holds(u,0,0) and at_holds(v,0,0)
    assert not shift_holds(a,0,encode_beta((1,)))


def test_empty_and_nonempty_zero_representations_remain_equivalent():
    a,b = (21,2),encode_beta((0,0,0,7))
    u,v = encode_beta((0,5)),encode_beta((0,0,0,0,6))
    assert formal_equal(a,0,b,3) and shift_holds(a,0,u) and shift_holds(b,3,v)
    assert formal_equal(u,1,v,4)


def test_shift_does_not_preserve_original_length_or_raw_output_codes():
    source = encode_beta((1,))
    left,right = encode_beta((1,0,17)),encode_beta((1,0,18),3)
    assert shift_holds(source,1,left) and shift_holds(source,1,right)
    assert formal_equal(left,2,right,2) and left != right
    assert not formal_equal(left,2,right,1) and not formal_equal(left,2,source,1)


def test_leading_zero_padding_is_not_trailing_zero_shift():
    source,leading,trailing = encode_beta((1,)),encode_beta((0,1)),encode_beta((1,0))
    assert formal_equal(source,1,leading,2)
    assert not shift_holds(source,1,leading) and shift_holds(source,1,trailing)
    assert not formal_equal(leading,2,trailing,2)


def evaluate(values, point, modulus):
    value = 0
    for coefficient in values:
        value = (point*value+coefficient) % modulus
    return value


def test_characteristic_two_evaluation_coincidence_is_not_formal_equivalence():
    square,linear = (1,0,0),(1,0)
    assert all(evaluate(square,x,2) == evaluate(linear,x,2) for x in range(2))
    a,b = encode_beta(square),encode_beta(linear)
    u,v = encode_beta(square+(0,)),encode_beta(linear+(0,))
    assert shift_holds(a,3,u) and shift_holds(b,2,v)
    assert not formal_equal(a,3,b,2) and not formal_equal(u,4,v,3)
    assert beta_at(a,0) == 1


def test_unbounded_natural_coefficients_do_not_require_a_modulus():
    a,b = encode_beta((10000,0,7)),encode_beta((0,10000,0,7))
    u,v = encode_beta((10000,0,7,0)),encode_beta((0,10000,0,7,0))
    assert formal_equal(a,3,b,4) and shift_holds(a,3,u) and shift_holds(b,4,v)
    assert formal_equal(u,4,v,5)
    assert power_value(u,4,3) == 10000
