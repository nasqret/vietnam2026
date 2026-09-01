"""Independent contracts, native beta models and original conditional HA.

Only direct canonical factories and one exact frozen left-unit source type
are loaded.  A dependency is an ordinary hypothesis, never a saved proof or
successful checker substitute.  Finite integer models are diagnostic only;
no Alpha import, full-cone replay, Lean check, admission, or gcd claim occurs.
"""

from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass, replace
from functools import lru_cache
from hashlib import sha256
import importlib
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
LIBRARY = ROOT / 'peano-lab/py/peano_lab/library'
SOURCE = HERE / 'prime_field_polynomial_left_constant_candidate.py'
SOURCE_SHA256 = '9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a'
TAIL_SOURCE = HERE.parent / 'prime-field-left-unit-v1/prime_field_polynomial_left_unit_candidate.py'
TAIL_SOURCE_SHA256 = 'dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6'
TAIL_NAME = 'polynomial_diagonal_left_unit_tail_term'
PRIVATE_NAMES = ('working_left_constant_candidate', 'working_left_constant_tail_type')
PROVIDER_PINS = {
    'theorems.py': '05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919',
    'prime_field_arithmetic_candidate.py': 'd4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90',
    'prime_field_polynomial_candidate.py': '644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72',
    'prime_field_polynomial_convolution_candidate.py': '20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24',
    'prime_field_polynomial_convolution_padding_candidate.py': '2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007',
    'prime_field_polynomial_representation_candidate.py': 'fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a',
    'matrix_rank_finite_coding_candidate.py': '9a72aed5aa215816b5e26868c04453e0a3042486580e79a13234431b5f45952d',
    'prime_field_tables_candidate.py': '2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400',
    'candidate_validation.py': 'de38ddb037e03bbbfec2cc48a96aae5d5dd253c190968b61d9a9f7ff28cf9a42',
}
KERNEL_PATH = ROOT / 'peano-lab/py/peano_lab/kernel/checker.py'
KERNEL_SHA256 = 'd7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe'
FACTORIES = (
    ('prime_field_arithmetic_candidate', 'make_prime_field_arithmetic_candidate_theorems'),
    ('prime_field_polynomial_candidate', 'make_prime_field_polynomial_candidate_theorems'),
    ('prime_field_polynomial_convolution_candidate', 'make_prime_field_polynomial_convolution_candidate_theorems'),
    ('prime_field_polynomial_convolution_padding_candidate', 'make_prime_field_polynomial_convolution_padding_candidate_theorems'),
    ('matrix_rank_finite_coding_candidate', 'make_matrix_rank_finite_coding_candidate_theorems'),
)


def protected_bindings():
    return {name: module for name, module in sys.modules.items()
            if name.startswith('peano_lab.library.editions_v') or name in PRIVATE_NAMES}


def load_file(name, path):
    before = protected_bindings()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys()
    assert all(after[key] is value for key, value in before.items())
    return module


candidate = load_file(PRIVATE_NAMES[0], SOURCE)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_left_constant_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    for name, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / name).read_bytes()).hexdigest() == digest
    assert sha256(TAIL_SOURCE.read_bytes()).hexdigest() == TAIL_SOURCE_SHA256
    result = {row.name: row for row in THEOREMS}
    for filename, factory in FACTORIES:
        module = importlib.import_module('peano_lab.library.' + filename)
        assert Path(module.__file__).resolve() == (LIBRARY / (filename + '.py')).resolve()
        for row in getattr(module, factory)(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    source = load_file(PRIVATE_NAMES[1], TAIL_SOURCE)
    tail = next(row for row in source.make_prime_field_polynomial_left_unit_candidate_theorems(TheoremSpec)
                if row.name == TAIL_NAME)
    assert tail.name not in result
    result[tail.name] = tail
    return result


def body_core():
    result = dict(provider_core())
    for row in rows():
        assert row.name not in result
        result[row.name] = row
    return result


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


# Independent complete native expansions; none calls a candidate/provider
# relation builder.  Fresh bound names are deliberately unlike production.
def And(*parts):
    result = '(' + parts[-1] + ')'
    for part in reversed(parts[:-1]):
        result = '(' + part + ') /\\ (' + result + ')'
    return result


def Lt(a, b):
    return f'exists lc_expected_strict_gap. lc_expected_strict_gap+S ({a})=({b})'


def Le(a, b):
    return f'exists lc_expected_weak_gap. lc_expected_weak_gap+({a})=({b})'


def At(b, c, i, a):
    return And(f'exists lc_expected_height. lc_expected_height+S ({a})=S ((S ({i}))*({c}))',
               f'exists lc_expected_quotient. ({b})=lc_expected_quotient*S ((S ({i}))*({c}))+({a})')


def Coeff(p, b, c, length):
    i, a = 'lc_expected_bound_index', 'lc_expected_bound_value'
    return f'forall {i}. ({Lt(i,length)}) -> exists {a}. ' + And(At(b, c, i, a), Lt(a, p))


def Prime(p):
    a, b = 'lc_expected_factor_left', 'lc_expected_factor_right'
    return f'~(({p})=1) /\\ forall {a} {b}. ({p})={a}*{b} -> {a}=1 \\/ {b}=1'


def Mod(p, a, b):
    u, v = 'lc_expected_balance_left', 'lc_expected_balance_right'
    return f'exists {u} {v}. ({a})+({p})*{u}=({b})+({p})*{v}'


def Residue(p, value, residue):
    return And(Lt(residue, p), Mod(p, value, residue))


def Multiply(p, k, a, b):
    return And(Lt(k, p), Lt(a, p), Residue(p, f'({k})*({a})', b))


def Scale(p, k, ab, ac, bb, bc, length):
    i, a, b = 'lc_expected_scale_index', 'lc_expected_scale_source', 'lc_expected_scale_target'
    return And(Lt(k, p), f'forall {i}. ({Lt(i,length)}) -> exists {a} {b}. ' + And(
        At(ab, ac, i, a), At(bb, bc, i, b), Multiply(p, k, a, b)))


def Sum(b, c, length, total):
    u, v, i, a, h, n = ('lc_expected_sum_code', 'lc_expected_sum_scale', 'lc_expected_sum_index',
                        'lc_expected_summand', 'lc_expected_partial', 'lc_expected_next')
    step = f'exists {a} {h} {n}. ' + And(At(b, c, i, a), At(u, v, i, h),
                                        At(u, v, f'S ({i})', n), f'{n}={h}+{a}')
    return f'exists {u} {v}. ' + And(At(u, v, '0', '0'), At(u, v, length, total),
                                     f'forall {i}. ({Lt(i,length)}) -> ({step})')


def Pad(b, c, length, i, a):
    return '(' + And(Lt(i, length), At(b, c, i, a)) + ') \\/ (' + And(Le(length, i), f'({a})=0') + ')'


def Term(ab, ac, L, bb, bc, M, i, j, total):
    k, a, b = 'lc_expected_complement', 'lc_expected_term_left', 'lc_expected_term_right'
    return f'exists {k} {a} {b}. ' + And(f'({j})+{k}=({i})', Pad(ab, ac, L, j, a),
                                         Pad(bb, bc, M, k, b), f'({total})={a}*{b}')


def Diagonal(ab, ac, L, bb, bc, M, i, d, e, length):
    j, t = 'lc_expected_diagonal_index', 'lc_expected_diagonal_value'
    return f'forall {j}. ({Lt(j,length)}) -> exists {t}. ' + And(At(d, e, j, t), Term(ab, ac, L, bb, bc, M, i, j, t))


def ConvolutionCoefficient(p, ab, ac, L, bb, bc, M, i, residue):
    d, e, n = 'lc_expected_terms_code', 'lc_expected_terms_scale', 'lc_expected_natural_total'
    return f'exists {d} {e} {n}. ' + And(Diagonal(ab, ac, L, bb, bc, M, i, d, e, f'S ({i})'),
                                         Sum(d, e, f'S ({i})', n), Residue(p, n, residue))


def ProductLength(L, M, N):
    return '(' + And(f'({L})=0 \\/ ({M})=0', f'({N})=0') + ') \\/ (' + And(
        f'~(({L})=0)', f'~(({M})=0)', f'({L})+({M})=S ({N})') + ')'


def Convolution(p, ab, ac, L, bb, bc, M, cb, cc, N):
    i, r = 'lc_expected_product_index', 'lc_expected_product_residue'
    prefix = f'forall {i}. ({Lt(i,N)}) -> exists {r}. ' + And(At(cb, cc, i, r),
                   ConvolutionCoefficient(p, ab, ac, L, bb, bc, M, i, r))
    return And(Coeff(p, ab, ac, L), Coeff(p, bb, bc, M), ProductLength(L, M, N), prefix)


def contract(parameters, premises, conclusion):
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join('(' + item + ')' for item in (*premises, conclusion))


K, A, H = ('kb', 'kc', '1'), ('ab', 'ac', 'L'), ('hb', 'hc', 'L')
PARAMETERS = ('p', 'k', 'kb', 'kc', 'ab', 'ac', 'hb', 'hc', 'L')
NAMES = ('polynomial_diagonal_left_constant_first_term',
         'polynomial_diagonal_left_constant_natural_sum',
         'prime_field_convolution_coefficient_left_constant',
         'prime_field_polynomial_left_constant_product_to_scale',
         'prime_field_polynomial_scale_to_left_constant_product',
         'prime_field_polynomial_left_constant_product_exists')
# Filled only from genuine original-kernel receipts before the final freeze.
METRICS = ((78, 46), (242, 52), (56, 40), (107, 41), (185, 53), (85, 38))


def independent_contracts():
    singleton = At('kb', 'kc', '0', 'k')
    inside, entry = Lt('i', 'L'), At('ab', 'ac', 'i', 'a')
    product = Convolution('p', *K, *A, *H)
    scale = Scale('p', 'k', 'ab', 'ac', 'hb', 'hc', 'L')
    return (
        (('k', 'kb', 'kc', *A, 'i', 'a', 't'),
         (singleton, inside, entry, Term(*K, *A, 'i', '0', 't')), 't=k*a'),
        (('k', 'kb', 'kc', *A, 'i', 'a', 'db', 'dc', 'n'),
         (singleton, inside, entry, Diagonal(*K, *A, 'i', 'db', 'dc', 'S i'),
          Sum('db', 'dc', 'S i', 'n')), 'n=k*a'),
        (('p', 'k', 'kb', 'kc', *A, 'i', 'a', 'r'),
         (singleton, inside, entry, Lt('k', 'p'), Lt('a', 'p'),
          ConvolutionCoefficient('p', *K, *A, 'i', 'r')), Multiply('p', 'k', 'a', 'r')),
        (PARAMETERS, (singleton, product), scale),
        (PARAMETERS, (Prime('p'), Coeff('p', *K), singleton, scale), product),
        (('p', 'k', *A), (Prime('p'), Lt('k', 'p'), Coeff('p', *A)),
         'exists kb kc hb hc. ' + And(Coeff('p', *K), singleton, scale, product)),
    )


def test_exact_source_provider_kernel_and_local_inventory():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert sha256(KERNEL_PATH.read_bytes()).hexdigest() == KERNEL_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    core = provider_core()
    for index, row in enumerate(rows()):
        assert type(row) is TheoremSpec and row.script
        assert row.name not in core
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(core) | set(NAMES[:index])
        assert not any('commut' in name for name in row.dependencies)
        assert not any(command.startswith(('admit', 'sorry', 'use ')) for command in row.script)
    assert candidate.__all__ == ['make_prime_field_polynomial_left_constant_candidate_theorems']


@pytest.mark.parametrize('index', range(6), ids=tuple(f'row{i:02d}' for i in range(6)))
def test_independent_fully_expanded_contract(index):
    same_ast(_closed_formula(rows()[index].statement), _closed_formula(contract(*independent_contracts()[index])))


def test_frozen_value_independent_tail_is_the_exact_original_provider_type():
    parameters = ('ub', 'uc', 'ab', 'ac', 'L', 'i', 'j', 't')
    expected = contract(parameters, (Le('1', 'j'), Term('ub', 'uc', '1', *A, 'i', 'j', 't')), 't=0')
    same_ast(_closed_formula(provider_core()[TAIL_NAME].statement), _closed_formula(expected))
    assert provider_core()[TAIL_NAME].dependencies == ('polynomial_zero_extended_entry_functional', 'mul_zero_left')
    assert TAIL_NAME in rows()[1].dependencies
    assert all(name not in provider_core() for name in ('prime_field_polynomial_right_divides_reflexive',
                                                     'prime_field_polynomial_right_divides_from_product'))


@pytest.mark.parametrize('name', ('peano_lab.library.editions_v_left_constant_guard', *PRIVATE_NAMES))
def test_explicit_loaders_preserve_preexisting_module_identity(name, monkeypatch):
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, marker)
    before = protected_bindings()
    assert Path(load_file(PRIVATE_NAMES[0], SOURCE).__file__) == SOURCE
    assert Path(load_file(PRIVATE_NAMES[1], TAIL_SOURCE).__file__) == TAIL_SOURCE
    assert before.keys() == protected_bindings().keys()
    assert all(protected_bindings()[key] is value for key, value in before.items())
    assert sys.modules[name] is marker


def test_direct_provider_loading_introduces_no_edition_or_temporary_alias():
    before = protected_bindings()
    provider_core()
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[name] is value for name, value in before.items())
    for filename, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / filename).read_bytes()).hexdigest() == digest
        name = 'peano_lab.library.' + filename.removesuffix('.py')
        if name in sys.modules:
            assert Path(sys.modules[name].__file__).resolve() == (LIBRARY / filename).resolve()


def test_source_contains_no_loader_public_alias_or_authority_side_effect():
    tree = ast.parse(SOURCE.read_text())
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert all(node.level == 0 for node in imports)
    assert all(node.module in ('__future__', 'typing') or node.module.startswith('peano_lab.library.') for node in imports)
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert not any('receipt' in command or 'commut' in command for row in rows() for command in row.script)
    assert all('gcd' not in row.name and 'bezout' not in row.name for row in rows())


def test_natural_sum_actually_constructs_one_term_and_proves_all_tail_entries_zero():
    script = rows()[1].script
    assert 'specialize beta_sum_exists (1)' in script
    assert 'specialize beta_sum_succ_decompose (0)' in script
    assert 'specialize polynomial_zero_tail_natural_sum_invariant (1)' in script
    assert 'specialize polynomial_zero_tail_natural_sum_invariant (i)' in script
    assert 'specialize polynomial_diagonal_left_unit_tail_term (1+j)' in script
    assert 'intro j0' in script and script.count('intro k') == 1
    assert any(command.startswith('have hhead :') for command in script)
    assert any(command.startswith('have htail :') for command in script)


def test_product_recovery_constructs_real_coefficient_witnesses_and_splits_empty_length():
    script = rows()[4].script
    assert r'have hz : L=0 \/ ~(L=0)' in script
    assert 'specialize prime_field_convolution_coefficient_exists (1)' in script
    assert 'specialize prime_field_convolution_coefficient_exists (L)' in script
    assert any(command.startswith('have hcoefficient : exists r.') for command in script)
    assert any(command.startswith('have heq : x2=x1') for command in script)
    assert 'prime_field_polynomial_convolution_at_length_exists' not in rows()[4].dependencies
    parameters, premises, _ = independent_contracts()[4]
    assert parameters == PARAMETERS and len(premises) == 4


def test_constructor_returns_a_genuine_singleton_scale_and_product_not_assumed_output():
    script = rows()[5].script
    assert 'specialize prime_field_polynomial_repeat_exists (k)' in script
    assert 'specialize prime_field_polynomial_scale_exists (L)' in script
    assert 'prime_field_polynomial_scale_to_left_constant_product' in rows()[5].dependencies
    _, premises, result = independent_contracts()[5]
    assert premises == (Prime('p'), Lt('k', 'p'), Coeff('p', *A))
    assert result.startswith('exists kb kc hb hc.')


def test_local_statement_novelty_compares_actual_parsed_provider_contracts():
    previous = [_closed_formula(row.statement) for row in provider_core().values()]
    for row in rows():
        current = _closed_formula(row.statement)
        for old in previous:
            with pytest.raises(AssertionError):
                same_ast(current, old)
        previous.append(current)


def encode_beta(values, variant=1):
    values = tuple(values)
    assert type(variant) is int and variant > 0
    assert all(type(value) is int and value >= 0 for value in values)
    scale = (max(values, default=0) + 1) * math.factorial(max(1, len(values))) * variant
    code, product = 0, 1
    for index, value in enumerate(values):
        modulus = 1 + (index + 1) * scale
        assert value < modulus and math.gcd(product, modulus) == 1
        correction = ((value - code) * pow(product, -1, modulus)) % modulus
        code += product * correction
        product *= modulus
    return code, scale


def beta(encoded, index):
    code, scale = encoded
    quotient, value = divmod(code, 1 + (index + 1) * scale)
    assert code == quotient * (1 + (index + 1) * scale) + value
    assert 0 <= value < 1 + (index + 1) * scale
    return value


def prefix(encoded, length):
    return tuple(beta(encoded, i) for i in range(length))


def bounded(p, encoded, length):
    return all(beta(encoded, i) < p for i in range(length))


def scale_model(p, k, source, target, length):
    return 0 <= k < p and all(beta(source, i) < p and beta(target, i) < p
                               and (k * beta(source, i) - beta(target, i)) % p == 0
                               for i in range(length))


def actual_diagonal(left, L, right, M, i, variant=1):
    terms = tuple((beta(left, j) if j < L else 0)
                  * (beta(right, i - j) if i - j < M else 0) for j in range(i + 1))
    diagonal = encode_beta((*terms, 31), variant)
    partials = [0]
    for value in terms:
        partials.append(partials[-1] + value)
    trace = encode_beta((*partials, 37), variant + 1)
    assert beta(trace, 0) == 0
    for j, term in enumerate(terms):
        assert j + (i - j) == i
        assert beta(diagonal, j) == term
        assert beta(trace, j + 1) == beta(trace, j) + beta(diagonal, j)
    return terms, diagonal, trace, beta(trace, i + 1)


def actual_product(p, left, L, right, M, variant=1):
    assert p > 0 and bounded(p, left, L) and bounded(p, right, M)
    length = L + M - 1 if L and M else 0
    values = []
    witnesses = []
    for i in range(length):
        terms, diagonal, trace, total = actual_diagonal(left, L, right, M, i, variant)
        quotient, residue = divmod(total, p)
        assert 0 <= residue < p and total == residue + p * quotient
        values.append(residue)
        witnesses.append((terms, diagonal, trace, total, quotient))
    output = encode_beta((*values, 41), variant + 2)
    assert prefix(output, length) == tuple(values)
    return output, length, tuple(witnesses)


VALUES = ((), (0,), (1,), (0, 0), (1, 0), (0, 1), (2, 0, 3), (1, 2, 0, 1))
SCALARS = tuple((p, k) for p in (1, 2, 3, 4, 5, 6) for k in range(p))


@pytest.mark.parametrize('values', VALUES)
@pytest.mark.parametrize('p,k', SCALARS)
def test_actual_singleton_scalar_product_beta_diagonals_and_empty_witnesses(values, p, k):
    values = tuple(value % p for value in values)
    length = len(values)
    left = encode_beta((k, 43), 1)
    source = encode_beta((*values, 47), 2)
    expected = tuple(k * value % p for value in values)
    scaled = encode_beta((*expected, 53), 3)
    assert bounded(p, left, 1) and beta(left, 0) == k
    assert scale_model(p, k, source, scaled, length)
    product, output_length, witnesses = actual_product(p, left, 1, source, length, 4)
    assert output_length == length and prefix(product, length) == prefix(scaled, length)
    assert scale_model(p, k, source, product, length)
    assert product != scaled and beta(product, length) != beta(scaled, length)
    for i, (terms, diagonal, trace, total, quotient) in enumerate(witnesses):
        assert terms[0] == k * values[i] and all(term == 0 for term in terms[1:])
        assert total == k * values[i] == beta(trace, i + 1)
        assert total == beta(product, i) + p * quotient
        assert beta(diagonal, i + 1) == 31 and beta(trace, i + 2) == 37
    if not length:
        assert not witnesses and beta(source, 0) == 47 and beta(scaled, 0) == 53


NATURAL_VALUES = ((0,), (1,), (7, 0), (2, 3, 5), (2**40 + 1, 2))


@pytest.mark.parametrize('values', NATURAL_VALUES)
@pytest.mark.parametrize('k', (0, 1, 7, 2**31 + 3))
def test_actual_unbounded_natural_sum_is_ordered_k_times_coefficient(values, k):
    left, right = encode_beta((k, 59)), encode_beta((*values, 61), 2)
    for i, value in enumerate(values):
        terms, diagonal, trace, total = actual_diagonal(left, 1, right, len(values), i, 3)
        assert terms == (k * value,) + (0,) * i
        assert total == k * value and beta(trace, i + 1) == total
        assert beta(diagonal, 0) == k * value


@pytest.mark.parametrize('p', (2, 3, 5))
def test_noncanonical_scalar_is_rejected_even_for_empty_source(p):
    empty_a, empty_h = encode_beta((71,), 1), encode_beta((73,), 2)
    noncanonical = encode_beta((p, 79), 3)
    assert bounded(p, empty_a, 0) and bounded(p, empty_h, 0)
    assert not bounded(p, noncanonical, 1)
    assert not scale_model(p, p, empty_a, empty_h, 0)
    assert all(beta(empty_a, i) < p for i in range(0))


@pytest.mark.parametrize('p', (2, 3, 5))
def test_wrong_singleton_value_and_nonconstant_factor_have_actual_counterexamples(p):
    source = encode_beta((1, 1, 83), 1)
    zero = encode_beta((0, 0, 89), 2)
    wrong_singleton = encode_beta((1, 97), 3)
    assert scale_model(p, 0, source, zero, 2)
    wrong, length, _ = actual_product(p, wrong_singleton, 1, source, 2)
    assert length == 2 and prefix(wrong, length) != prefix(zero, length)
    nonconstant = encode_beta((1, 1, 101), 4)
    longer, new_length, _ = actual_product(p, nonconstant, 2, source, 2)
    assert new_length == 3 and new_length != length
    assert len(prefix(longer, new_length)) == 3


def test_zero_scalar_does_not_trim_nonempty_product_to_zero_length():
    left, source = encode_beta((0, 103)), encode_beta((1, 2, 1, 107), 2)
    product, length, _ = actual_product(3, left, 1, source, 3)
    assert length == 3 and prefix(product, length) == (0, 0, 0)
    assert scale_model(3, 0, source, product, length)


def test_index_guard_and_field_bounds_are_not_replaced_by_raw_integer_equality():
    left, source = encode_beta((2, 109)), encode_beta((2, 3), 2)
    _, _, _, outside_total = actual_diagonal(left, 1, source, 1, 1)
    assert outside_total == 0 != 2 * beta(source, 1)
    product, _, witnesses = actual_product(3, left, 1, source, 1)
    assert witnesses[0][3] == 4 and beta(product, 0) == 1
    assert beta(product, 0) != 2 * beta(source, 0)


def test_characteristic_two_and_formal_coefficients_do_not_mean_evaluation_identity():
    left, source = encode_beta((1, 113)), encode_beta((1, 1, 0, 127), 2)
    product, length, _ = actual_product(2, left, 1, source, 3)
    assert prefix(product, length) == (1, 1, 0)
    assert all((x * x + x) % 2 == 0 for x in range(2))
    assert prefix(product, length) != (0, 0, 0) and product != source


@pytest.mark.parametrize('index', range(6), ids=tuple(f'row{i:02d}' for i in range(6)))
def test_actual_original_ha_body(index):
    row = rows()[index]
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == row.name
    assert (receipt.command_count, receipt.dependency_count) == (len(row.script), len(row.dependencies))
    assert METRICS[index] is not None
    assert (receipt.proof_nodes, receipt.proof_depth) == METRICS[index]
    assert 0 < receipt.proof_objects <= receipt.proof_nodes and receipt.proof_depth <= 256


@pytest.mark.parametrize('index', range(6), ids=tuple(f'row{i:02d}' for i in range(6)))
@pytest.mark.parametrize('mutation', ('false_conclusion', 'missing_body', 'truncated_body'))
def test_false_or_incomplete_body_is_rejected(index, mutation):
    row = rows()[index]
    parameters, premises, _ = independent_contracts()[index]
    changed = replace(row, statement=contract(parameters, premises, '0=1')) if mutation == 'false_conclusion' else replace(
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


PREMISES = tuple((index, position) for index, (_, premises, _) in enumerate(independent_contracts())
                 for position in range(len(premises)))


@pytest.mark.parametrize('index,position', PREMISES,
                         ids=tuple(f'row{i:02d}-premise{j:02d}' for i, j in PREMISES))
def test_fixed_body_rejects_a_removed_input_clause(index, position):
    # This exact-script check does not claim mathematical independence of
    # every premise: e.g. primality is stronger than needed for some rings.
    row = rows()[index]
    parameters, premises, result = independent_contracts()[index]
    changed = replace(row, statement=contract(parameters, premises[:position] + premises[position + 1:], result))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


STRONGER = (
    (0, 'raw-coefficient', 't=a'),
    (1, 'raw-sum', 'n=a'),
    (2, 'no-residue-reduction', 'r=k*a'),
    (3, 'raw-code-equality', 'hb=ab'),
    (4, 'nonempty-output', '~(L=0)'),
    (5, 'nonzero-scalar', '~(k=0)'),
)


@pytest.mark.parametrize('index,label,result', STRONGER,
                         ids=tuple(f'row{i:02d}-{label}' for i, label, _ in STRONGER))
def test_fixed_body_rejects_false_stronger_output(index, label, result):
    parameters, premises, _ = independent_contracts()[index]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=contract(parameters, premises, result)),),
                                 core=body_core())
