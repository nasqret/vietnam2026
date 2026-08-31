"""Independent scalar contracts, actual beta models, and conditional HA checks.

The selected canonical providers supply ordinary dependency hypotheses only.
No full Alpha import, dependency-complete replay, independent Lean result,
cached success or admission authority is used.  Integer models construct and
check genuine beta tables, natural sum traces and bounded residues, but are
diagnostics rather than proofs.  Every positive proof uses the original HA.
"""

from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass, replace
from functools import lru_cache
import gc
from hashlib import sha256
import importlib.util
import math
from pathlib import Path
import re
import sys
from types import ModuleType

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE / 'prime_field_polynomial_scalar_convolution_candidate.py'
LIBRARY = ROOT / 'peano-lab/py/peano_lab/library'
SOURCE_SHA256 = 'e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e'
PROVIDER_PINS = {
    'theorems.py': '05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919',
    'prime_field_arithmetic_candidate.py': 'd4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90',
    'prime_field_polynomial_candidate.py': '644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72',
    'prime_field_polynomial_convolution_candidate.py': '20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24',
    'prime_field_tables_candidate.py': '2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400',
    'finite_sum_theorems.py': '0d60b7a4fa21161def737fc6759b23e0679694052e95d97b419aa1ecb293c56e',
}


def edition_bindings():
    return {name: value for name, value in sys.modules.items()
            if name.startswith('peano_lab.library.editions_v')}


def load_candidate():
    before = edition_bindings()
    spec = importlib.util.spec_from_file_location('working_polynomial_scalar_convolution_candidate', SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    after = edition_bindings()
    assert before.keys() == after.keys() and all(after[name] is value for name, value in before.items())
    return module


candidate = load_candidate()


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_scalar_convolution_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems

    for name, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / name).read_bytes()).hexdigest() == digest
    result = {row.name: row for row in THEOREMS}
    for factory in (make_prime_field_arithmetic_candidate_theorems,
                    make_prime_field_polynomial_candidate_theorems,
                    make_prime_field_polynomial_convolution_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


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


# Independent native first-order expansions: these expected graphs never call
# candidate or provider string builders.
def And(*parts):
    result = '(' + parts[-1] + ')'
    for part in reversed(parts[:-1]):
        result = '(' + part + ') /\\ (' + result + ')'
    return result


def Lt(a, b):
    return f'exists independent_strict_gap. independent_strict_gap+S ({a})=({b})'


def Le(a, b):
    return f'exists independent_weak_gap. independent_weak_gap+({a})=({b})'


def At(b, c, i, a):
    return And(f'exists independent_height. independent_height+S ({a})=S ((S ({i}))*({c}))',
               f'exists independent_quotient. ({b})=independent_quotient*S ((S ({i}))*({c}))+({a})')


def Coeff(p, b, c, length):
    i, a = 'independent_bounded_index', 'independent_bounded_value'
    return f'forall {i}. ({Lt(i,length)}) -> exists {a}. ' + And(At(b, c, i, a), Lt(a, p))


def Equal(b, c, d, e, length):
    i, a = 'independent_equal_index', 'independent_equal_value'
    return f'forall {i} {a}. ({Lt(i,length)}) -> ({At(b,c,i,a)}) -> ({At(d,e,i,a)})'


def Repeat(b, c, value, length):
    i = 'independent_repeat_index'
    return f'forall {i}. ({Lt(i,length)}) -> ({At(b,c,i,value)})'


def Mod(p, a, b):
    return f'exists independent_balance_left independent_balance_right. ({a})+({p})*independent_balance_left=({b})+({p})*independent_balance_right'


def Residue(p, value, residue):
    return And(Lt(residue, p), Mod(p, value, residue))


def Multiply(p, k, a, b):
    return And(Lt(k, p), Lt(a, p), Residue(p, f'({k})*({a})', b))


def Scale(p, k, ab, ac, bb, bc, length):
    i, a, b = 'independent_scale_index', 'independent_scale_source', 'independent_scale_target'
    points = f'forall {i}. ({Lt(i,length)}) -> exists {a} {b}. ' + And(
        At(ab, ac, i, a), At(bb, bc, i, b), Multiply(p, k, a, b))
    return And(Lt(k, p), points)


def Pointwise(p, k, ab, ac, bb, bc, length):
    i, a, b = 'independent_point_index', 'independent_point_source', 'independent_point_target'
    return (f'forall {i} {a} {b}. ({Lt(i,length)}) -> ({At(ab,ac,i,a)}) -> '
            f'({At(bb,bc,i,b)}) -> ({Mod(p,f"({k})*({a})",b)})')


def Sum(b, c, length, total):
    u, v, i, a, h, n = ('independent_sum_code', 'independent_sum_scale', 'independent_sum_index',
                        'independent_summand', 'independent_partial', 'independent_next')
    step = f'exists {a} {h} {n}. ' + And(At(b, c, i, a), At(u, v, i, h),
                                        At(u, v, f'S ({i})', n), f'{n}={h}+{a}')
    return f'exists {u} {v}. ' + And(At(u, v, '0', '0'), At(u, v, length, total),
                                     f'forall {i}. ({Lt(i,length)}) -> ({step})')


def Pad(b, c, length, i, a):
    return '(' + And(Lt(i, length), At(b, c, i, a)) + ') \\/ (' + And(Le(length, i), f'({a})=0') + ')'


def Term(ab, ac, L, bb, bc, M, i, j, total):
    k, a, b = 'independent_complement', 'independent_term_left', 'independent_term_right'
    return f'exists {k} {a} {b}. ' + And(f'({j})+{k}=({i})', Pad(ab, ac, L, j, a),
                                         Pad(bb, bc, M, k, b), f'({total})={a}*{b}')


def Diagonal(ab, ac, L, bb, bc, M, i, d, e, length):
    j, t = 'independent_diagonal_index', 'independent_diagonal_value'
    return f'forall {j}. ({Lt(j,length)}) -> exists {t}. ' + And(At(d, e, j, t), Term(ab, ac, L, bb, bc, M, i, j, t))


def ConvolutionCoefficient(p, ab, ac, L, bb, bc, M, i, residue):
    d, e, n = 'independent_terms_code', 'independent_terms_scale', 'independent_natural_total'
    return f'exists {d} {e} {n}. ' + And(Diagonal(ab, ac, L, bb, bc, M, i, d, e, f'S ({i})'),
                                         Sum(d, e, f'S ({i})', n), Residue(p, n, residue))


def ProductLength(L, M, N):
    return '(' + And(f'({L})=0 \\/ ({M})=0', f'({N})=0') + ') \\/ (' + And(f'~(({L})=0)', f'~(({M})=0)', f'({L})+({M})=S ({N})') + ')'


def Convolution(p, ab, ac, L, bb, bc, M, cb, cc, N):
    i, r = 'independent_product_index', 'independent_product_residue'
    prefix = f'forall {i}. ({Lt(i,N)}) -> exists {r}. ' + And(At(cb, cc, i, r),
                   ConvolutionCoefficient(p, ab, ac, L, bb, bc, M, i, r))
    return And(Coeff(p, ab, ac, L), Coeff(p, bb, bc, M), ProductLength(L, M, N), prefix)


def contract(parameters, premises, conclusion):
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join('(' + item + ')' for item in (*premises, conclusion))


FACTORS = ('ab', 'ac', 'L', 'bb', 'bc', 'M')
SCALED = ('ab', 'ac', 'L', 'sb', 'sc', 'M')
PRODUCT_PARAMETERS = ('p', 'k', *FACTORS, 'sb', 'sc', 'cb', 'cc', 'N', 'db', 'dc', 'K')


def independent_contracts():
    scale = Scale('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M')
    old = Convolution('p', *FACTORS, 'cb', 'cc', 'N')
    new = Convolution('p', *SCALED, 'db', 'dc', 'K')
    output = Scale('p', 'k', 'cb', 'cc', 'eb', 'ec', 'N')
    return (
        (('p', 'k', 'ab', 'ac', 'bb', 'bc', 'L', 'u', 'v'),
         (Sum('ab', 'ac', 'L', 'u'), Sum('bb', 'bc', 'L', 'v'), Pointwise('p', 'k', 'ab', 'ac', 'bb', 'bc', 'L')),
         Mod('p', 'k*u', 'v')),
        (('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'i', 'b', 's'),
         (scale, Pad('bb', 'bc', 'M', 'i', 'b'), Pad('sb', 'sc', 'M', 'i', 's')), Mod('p', 'k*b', 's')),
        (('p', 'k', *FACTORS, 'sb', 'sc', 'i', 'j', 't', 'r'),
         (scale, Term(*FACTORS, 'i', 'j', 't'), Term(*SCALED, 'i', 'j', 'r')), Mod('p', 'k*t', 'r')),
        (('p', 'k', *FACTORS, 'sb', 'sc', 'i', 'db', 'dc', 'eb', 'ec', 'N', 'u', 'v'),
         (scale, Diagonal(*FACTORS, 'i', 'db', 'dc', 'N'), Sum('db', 'dc', 'N', 'u'),
          Diagonal(*SCALED, 'i', 'eb', 'ec', 'N'), Sum('eb', 'ec', 'N', 'v')), Mod('p', 'k*u', 'v')),
        (('p', 'k', *FACTORS, 'sb', 'sc', 'i', 'c', 'r'),
         (scale, ConvolutionCoefficient('p', *FACTORS, 'i', 'c'), ConvolutionCoefficient('p', *SCALED, 'i', 'r')),
         Multiply('p', 'k', 'c', 'r')),
        (PRODUCT_PARAMETERS, (scale, old, new),
         And('K=N', Scale('p', 'k', 'cb', 'cc', 'db', 'dc', 'N'))),
        ((*PRODUCT_PARAMETERS, 'eb', 'ec'), (scale, old, new, output),
         And('K=N', Equal('db', 'dc', 'eb', 'ec', 'N'))),
        (('p', 'k', *FACTORS, 'cb', 'cc', 'N'), ('~(p=0)', Lt('k', 'p'), old),
         'exists sb sc db dc eb ec. ' + And(scale, Convolution('p', *SCALED, 'db', 'dc', 'N'),
                                            output, Equal('db', 'dc', 'eb', 'ec', 'N'))),
        (('p', 'bb', 'bc', 'sb', 'sc', 'M'), (Scale('p', '0', 'bb', 'bc', 'sb', 'sc', 'M'),),
         Repeat('sb', 'sc', '0', 'M')),
        (('p', *FACTORS, 'sb', 'sc', 'db', 'dc', 'N'),
         ('~(p=0)', Scale('p', '0', 'bb', 'bc', 'sb', 'sc', 'M'), Convolution('p', *SCALED, 'db', 'dc', 'N')),
         Repeat('db', 'dc', '0', 'N')),
    )


NAMES = (
    'beta_sum_pointwise_mod_scale', 'polynomial_zero_extended_scale_congruent',
    'polynomial_diagonal_term_right_scale_congruent', 'polynomial_diagonal_sum_right_scale_congruent',
    'prime_field_convolution_coefficient_right_scale', 'prime_field_polynomial_convolution_right_scale',
    'prime_field_polynomial_convolution_right_scale_equal', 'prime_field_polynomial_convolution_right_scale_exists',
    'prime_field_polynomial_scale_zero_value', 'prime_field_polynomial_convolution_right_scale_zero',
)
METRICS = ((153, 43), (96, 35), (160, 47), (245, 109), (113, 56),
           (105, 48), (86, 48), (137, 58), (56, 22), (90, 53))


def test_exact_inventory_and_topological_dependency_ownership():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert len(rows()) == len(independent_contracts()) == 10
    assert sum(len(row.dependencies) for row in rows()) == 35
    known = set(provider_core())
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in known and row.script
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= known
        assert all(re.search(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", '\n'.join(row.script)) for name in row.dependencies)
        assert not any(command.startswith(('use ', 'admit', 'sorry')) or 'DNE' in command for command in row.script)
        known.add(row.name)


@pytest.mark.parametrize('index', range(10), ids=NAMES)
def test_independent_closed_fully_expanded_contract(index):
    same_ast(_closed_formula(rows()[index].statement), _closed_formula(contract(*independent_contracts()[index])))


def test_canonical_imports_preserve_all_existing_edition_identities():
    tree = ast.parse(SOURCE.read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.ImportFrom) and node.level == 0 for node in imports)
    assert {node.module for node in imports} == {
        '__future__', 'typing', 'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate',
        'peano_lab.library.prime_field_polynomial_convolution_candidate',
        'peano_lab.library.prime_field_tables_candidate',
    }
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    before = edition_bindings()
    loaded = load_candidate()
    after = edition_bindings()
    assert Path(loaded.__file__) == SOURCE
    assert before.keys() == after.keys() and all(after[name] is value for name, value in before.items())
    for filename in PROVIDER_PINS:
        name = 'peano_lab.library.' + filename.removesuffix('.py')
        if name in sys.modules:
            assert Path(sys.modules[name].__file__).resolve() == (LIBRARY / filename).resolve()


def test_direct_import_accepts_but_neither_introduces_nor_replaces_preloaded_editions(monkeypatch):
    name = 'peano_lab.library.editions_v_scalar_import_guard'
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, marker)
    before = edition_bindings()
    loaded = load_candidate()
    assert Path(loaded.__file__) == SOURCE
    after = edition_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())
    assert after[name] is marker


def test_reused_scale_is_actual_canonical_product_not_a_desired_law():
    from peano_lab.library.prime_field_polynomial_candidate import _scale, prime_field_polynomial_scale_relation

    parameters = ('p', 'k', 'ab', 'ac', 'bb', 'bc', 'L')
    actual = prime_field_polynomial_scale_relation(*parameters, tag='independent', variables=parameters)
    binder = 'forall ' + ' '.join(parameters) + '. '
    same_ast(_closed_formula(binder + actual), _closed_formula(binder + Scale(*parameters)))
    assert candidate._scale is _scale
    assert candidate.__all__ == ['make_prime_field_polynomial_scalar_convolution_candidate_theorems']
    assert not any(name.endswith('_relation') for name in vars(candidate))
    assert all('prime' not in premise.lower() and 'horner' not in premise.lower()
               for _, premises, _ in independent_contracts() for premise in premises)
    assert independent_contracts()[7][1][0] == '~(p=0)'
    assert independent_contracts()[7][1][1] == Lt('k', 'p')
    assert len(independent_contracts()[0][1]) == 3
    assert not any(word in row.name for row in rows() for word in ('associative', 'bezout', 'gcd', 'division_unique'))


def test_local_novelty_compares_actual_selected_dependency_types_only():
    # This does not replace the separately scheduled full-Alpha novelty gate.
    from peano_lab.library.formula_dag import FormulaArena

    table = body_core()
    selected = set(NAMES) | {dependency for row in rows() for dependency in row.dependencies}
    encoded = {name: FormulaArena().freeze(_closed_formula(table[name].statement)).to_json() for name in selected}
    for name in NAMES:
        assert all(encoded[name] != value for other, value in encoded.items() if other != name)


@pytest.mark.parametrize('index', range(10), ids=NAMES)
def test_actual_original_ha_body_and_exact_nodes_depth(index):
    row = rows()[index]
    try:
        receipt = replay_candidate_bodies((row,), core=body_core())[0]
        assert receipt.name == row.name
        assert (receipt.dependency_count, receipt.command_count) == (len(row.dependencies), len(row.script))
        assert (receipt.proof_nodes, receipt.proof_depth) == METRICS[index]
        assert 0 < receipt.proof_objects <= receipt.proof_nodes
    finally:
        gc.collect()


@pytest.mark.parametrize('index', range(10))
@pytest.mark.parametrize('mutation', ('false_conclusion', 'missing_body', 'truncated_body'))
def test_false_or_incomplete_body_is_rejected(index, mutation):
    row = rows()[index]
    if mutation == 'false_conclusion':
        parameters, premises, _ = independent_contracts()[index]
        changed = replace(row, statement=contract(parameters, premises, '0=1'))
    elif mutation == 'missing_body':
        changed = replace(row, script=())
    else:
        changed = replace(row, script=row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


EDGES = tuple((index, dependency) for index, row in enumerate(rows()) for dependency in row.dependencies)


@pytest.mark.parametrize('index,dependency', EDGES, ids=tuple(f'edge-{i:02d}' for i in range(len(EDGES))))
def test_each_removed_dependency_is_rejected(index, dependency):
    row = rows()[index]
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('index,dependency', EDGES, ids=tuple(f'edge-{i:02d}' for i in range(len(EDGES))))
def test_each_poisoned_dependency_is_rejected(index, dependency):
    core = body_core()
    core[dependency] = replace(core[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],), core=core)


def changed_contracts():
    result = []
    for index, (parameters, premises, conclusion) in enumerate(independent_contracts()):
        for position in range(len(premises)):
            result.append((index, f'missing-premise-{position}', contract(parameters, premises[:position] + premises[position+1:], conclusion)))
    wrong = {
        0: (('natural-total-equality', 'k*u=v'), ('unscaled-sum', Mod('p', 'u', 'v'))),
        1: (('natural-value-equality', 'k*b=s'),),
        2: (('natural-term-equality', 'k*t=r'),),
        3: (('natural-total-equality', 'k*u=v'),),
        4: (('unscaled-coefficient', 'c=r'), ('raw-natural-product', 'k*c=r')),
        5: (('successor-length', And('K=S N', Scale('p', 'k', 'cb', 'cc', 'db', 'dc', 'N'))),
            ('raw-code-identity', And('cb=db', 'cc=dc'))),
        6: (('raw-code-identity', And('db=eb', 'dc=ec')), ('extra-entry', And('K=N', Equal('db', 'dc', 'eb', 'ec', 'S N')))),
        7: (('raw-code-witness', 'exists sb sc db dc eb ec. ' + And(
            Scale('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M'), Convolution('p', *SCALED, 'db', 'dc', 'N'),
            Scale('p', 'k', 'cb', 'cc', 'eb', 'ec', 'N'), 'db=eb', 'dc=ec')),),
        8: (('outside-prefix-zero', Repeat('sb', 'sc', '0', 'S M')),),
        9: (('outside-prefix-zero', Repeat('db', 'dc', '0', 'S N')),),
    }
    for index, mutations in wrong.items():
        parameters, premises, _ = independent_contracts()[index]
        for label, conclusion in mutations:
            result.append((index, label, contract(parameters, premises, conclusion)))
    return tuple(result)


CHANGED = changed_contracts()


@pytest.mark.parametrize('index,label,statement', CHANGED, ids=tuple(f'{i}-{label}' for i, label, _ in CHANGED))
def test_fixed_body_rejects_altered_guards_or_stronger_claim(index, label, statement):
    # Exact-script rejection is not a claim that every removed premise is
    # mathematically independent for every represented length or modulus.
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())


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


def beta(code, index):
    b, c = code
    quotient, value = divmod(b, 1 + (index+1)*c)
    assert b == quotient*(1 + (index+1)*c) + value
    assert 0 <= value < 1 + (index+1)*c
    return value


def prefix(code, length):
    return tuple(beta(code, index) for index in range(length))


def congruent(p, left, right):
    return left == right if p == 0 else left % p == right % p


def actual_mod_witness(p, left, right):
    assert congruent(p, left, right)
    if p == 0:
        a = b = 0
    else:
        a, b = max(0, right-left)//p, max(0, left-right)//p
    assert left+p*a == right+p*b
    return a, b


def model_multiply(p, k, a, b):
    return 0 <= k < p and 0 <= a < p and 0 <= b < p and congruent(p, k*a, b)


def model_scale(p, k, source, target, length):
    return 0 <= k < p and all(model_multiply(p, k, beta(source, i), beta(target, i)) for i in range(length))


def actual_sum_trace(values, encoding=1):
    values = tuple(values)
    source = encode_beta((*values, 37), encoding)
    partials = [0]
    for value in values:
        partials.append(partials[-1] + value)
    trace = encode_beta((*partials, 41), encoding+1)
    assert beta(trace, 0) == 0
    for i, value in enumerate(values):
        assert beta(source, i) == value
        assert beta(trace, i+1) == beta(trace, i) + beta(source, i)
    total = beta(trace, len(values))
    assert total == sum(values)
    return source, trace, total


def zero_extended(code, length, index):
    return beta(code, index) if index < length else 0


def actual_coefficient_witness(p, left, L, right, M, index, encoding=1):
    assert p > 0
    terms = tuple(zero_extended(left, L, j) * zero_extended(right, M, index-j) for j in range(index+1))
    diagonal, trace, total = actual_sum_trace(terms, encoding)
    for j, term in enumerate(terms):
        assert j + (index-j) == index
        assert beta(diagonal, j) == term
    quotient, residue = divmod(total, p)
    assert residue < p and total == residue+p*quotient
    actual_mod_witness(p, total, residue)
    return residue, diagonal, trace, total


def product_values(p, left, right):
    if not left or not right:
        return ()
    return tuple(sum(left[j]*right[i-j] for j in range(len(left)) if 0 <= i-j < len(right)) % p
                 for i in range(len(left)+len(right)-1))


SUM_INPUTS = ((), (0,), (1,), (2, 5), (3, 0, 7), (2**40+7, 4))


@pytest.mark.parametrize('values', SUM_INPUTS)
@pytest.mark.parametrize('p', (0, 1, 2, 4, 7))
@pytest.mark.parametrize('k', (0, 1, 3, 9))
def test_actual_natural_sum_traces_transport_unbounded_scalar_congruence(values, p, k):
    target = tuple(k*value if p == 0 else (k*value) % p + (i % 3)*p for i, value in enumerate(values))
    source, old_trace, old_total = actual_sum_trace(values)
    result, new_trace, new_total = actual_sum_trace(target, 3)
    for i in range(len(values)):
        actual_mod_witness(p, k*beta(source, i), beta(result, i))
    actual_mod_witness(p, k*old_total, new_total)
    assert prefix(old_trace, len(values)+1)[-1] == old_total
    assert prefix(new_trace, len(values)+1)[-1] == new_total
    assert beta(source, len(values)) == beta(result, len(values)) == 37
    if p == 0:
        assert k*old_total == new_total


PAIRS = (((), ()), ((), (1,)), ((1,), ()), ((1, 2, 1), ()), ((1,), (1,)),
         ((0,), (1, 1)), ((1, 0), (0,)), ((0, 1), (1, 0)), ((1, 2), (2, 1)),
         ((0, 2, 0), (1, 0)), ((1, 0, 1), (1, 1, 1)))
MODULUS_SCALARS = tuple((p, k) for p in (1, 2, 3, 4, 6, 7) for k in range(p))


@pytest.mark.parametrize('values', PAIRS)
@pytest.mark.parametrize('p,k', MODULUS_SCALARS)
def test_actual_scaled_input_two_outputs_diagonal_sums_and_empty_safe_covariance(values, p, k):
    av, bv = (tuple(value % p for value in side) for side in values)
    L, M = len(av), len(bv)
    av_code, bv_code = encode_beta((*av, 43, 47)), encode_beta((*bv, 53, 59))
    sv = tuple((k*value) % p for value in bv)
    scaled = encode_beta((*sv, 61, 67), 2)
    assert model_scale(p, k, bv_code, scaled, M)
    pv, qv = product_values(p, av, bv), product_values(p, av, sv)
    tv = tuple((k*value) % p for value in pv)
    N, K = len(pv), len(qv)
    product = encode_beta((*pv, 71, 73))
    result = encode_beta((*qv, 79, 83), 3)
    comparison = encode_beta((*tv, 89, 97), 5)
    assert K == N == (L+M-1 if L and M else 0)
    assert result != comparison and bv_code != scaled
    assert model_scale(p, k, product, comparison, N)
    assert model_scale(p, k, product, result, N)
    assert prefix(result, N) == prefix(comparison, N)
    for i in range(N+3):
        c, old_diagonal, old_trace, old_total = actual_coefficient_witness(p, av_code, L, bv_code, M, i)
        r, new_diagonal, new_trace, new_total = actual_coefficient_witness(p, av_code, L, scaled, M, i, 3)
        for j in range(i+1):
            actual_mod_witness(p, k*beta(old_diagonal, j), beta(new_diagonal, j))
        assert beta(old_trace, i+1) == old_total and beta(new_trace, i+1) == new_total
        actual_mod_witness(p, k*old_total, new_total)
        assert model_multiply(p, k, c, r)
        if i < N:
            assert beta(product, i) == c and beta(result, i) == r == beta(comparison, i)
        else:
            assert c == r == 0
    assert beta(bv_code, M) == 53 and beta(scaled, M) == 61
    assert beta(result, N) == 79 and beta(comparison, N) == 89
    if k == 0:
        assert prefix(scaled, M) == (0,)*M and prefix(result, N) == (0,)*N


@pytest.mark.parametrize('p,k', ((2, 0), (2, 1), (4, 2), (6, 2), (6, 3), (7, 6)))
@pytest.mark.parametrize('left_values', ((2**42+1,), (9, 0, 2**35+3)))
def test_all_index_coefficient_law_does_not_assume_bounded_left_coefficients(p, k, left_values):
    right_values = (p-1, 1 % p)
    scaled_values = tuple((k*value) % p for value in right_values)
    left = encode_beta((*left_values, 101))
    right, scaled = encode_beta((*right_values, 103)), encode_beta((*scaled_values, 107), 2)
    assert any(value >= p for value in left_values)
    assert model_scale(p, k, right, scaled, 2)
    for i in range(len(left_values)+5):
        old, _, _, _ = actual_coefficient_witness(p, left, len(left_values), right, 2, i)
        new, _, _, _ = actual_coefficient_witness(p, left, len(left_values), scaled, 2, i, 3)
        assert model_multiply(p, k, old, new)


@pytest.mark.parametrize('p', (1, 2, 4, 6, 7))
@pytest.mark.parametrize('length', (0, 1, 3))
def test_scalar_bound_is_not_dropped_even_for_empty_prefix(p, length):
    source, target = encode_beta((0,)*length + (17,)), encode_beta((0,)*length + (19,), 2)
    assert model_scale(p, 0, source, target, length)
    assert not model_scale(p, p, source, target, length)
    assert not model_scale(p, p+1, source, target, length)
    assert not model_scale(0, 0, source, target, length)


@pytest.mark.parametrize('p', (2, 3, 4, 6, 7))
def test_missing_coefficient_and_residue_bounds_are_real_counterexamples(p):
    source = encode_beta((p+1, 17))
    canonical = encode_beta((1, 19), 2)
    assert congruent(p, p+1, 1)
    assert not model_scale(p, 1, source, canonical, 1)
    assert congruent(p, 1, p+1)
    assert not model_multiply(p, 1, 1, p+1)
    assert not model_scale(p, 1, canonical, source, 1)


@pytest.mark.parametrize('p,k,b', ((3, 2, 1), (4, 2, 1), (6, 3, 1), (7, 4, 2)))
def test_unscaled_right_input_does_not_satisfy_covariance(p, k, b):
    source = encode_beta((b, 17))
    wrong = encode_beta((b, 19), 2)
    assert not model_scale(p, k, source, wrong, 1)
    old = product_values(p, (1,), (b,))
    wrong_product = product_values(p, (1,), (b,))
    assert wrong_product != tuple((k*value) % p for value in old)


def test_scalar_transport_does_not_claim_raw_natural_sum_equality():
    left, right, scaled = encode_beta((2,)), encode_beta((2,)), encode_beta((1,), 2)
    assert model_scale(3, 2, right, scaled, 1)
    c, _, _, old_total = actual_coefficient_witness(3, left, 1, right, 1, 0)
    r, _, _, new_total = actual_coefficient_witness(3, left, 1, scaled, 1, 0, 3)
    assert old_total == 4 and new_total == 2 and 2*old_total != new_total
    actual_mod_witness(3, 2*old_total, new_total)
    assert model_multiply(3, 2, c, r)


def test_nonzero_composite_scalar_need_not_preserve_nonzero_or_degree():
    source = encode_beta((3, 1, 17))
    scaled = encode_beta((0, 2, 19), 2)
    assert model_scale(6, 2, source, scaled, 2)
    assert beta(source, 0) != 0 and beta(scaled, 0) == 0
    assert product_values(6, (1,), (3,)) == (3,)
    assert product_values(6, (1,), (0,)) == (0,)


def test_characteristic_two_uses_natural_unit_one_and_allows_scalar_zero():
    source = encode_beta((1, 1, 17))
    unit = encode_beta((1, 1, 19), 2)
    zero = encode_beta((0, 0, 23), 3)
    assert model_scale(2, 1, source, unit, 2)
    assert model_scale(2, 0, source, zero, 2)
    assert not model_scale(2, 2, source, zero, 2)
    assert product_values(2, (1, 1), (1, 1)) == (1, 0, 1)


def test_actual_outputs_are_not_unique_codes_and_postprefix_remains_free():
    source = encode_beta((1, 2, 17))
    first = encode_beta((2, 1, 19), 2)
    second = encode_beta((2, 1, 23), 3)
    assert model_scale(3, 2, source, first, 2) and model_scale(3, 2, source, second, 2)
    assert first != second and prefix(first, 2) == prefix(second, 2)
    assert beta(first, 2) != beta(second, 2)
    empty_first, empty_second = encode_beta((101,)), encode_beta((103,), 5)
    assert model_scale(3, 2, empty_first, empty_second, 0)
    assert beta(empty_first, 0) != beta(empty_second, 0)
