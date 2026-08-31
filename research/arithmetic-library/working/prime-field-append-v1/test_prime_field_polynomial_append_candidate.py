"""Independent append contracts, actual beta models, and original HA tests.

Only dependency-curried bodies are checked here. Canonical provider factories
and the exact frozen shift/scalar files supply actual dependency statements;
neither Alpha editions nor working-package aliases are installed. The integer
models construct real encodings, diagonal sums, residues, shifts, scalars and
aligned sums, but are diagnostics rather than proof/admission authority.
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
WORKING = HERE.parent
SOURCE = HERE / 'prime_field_polynomial_append_candidate.py'
LIBRARY = ROOT / 'peano-lab/py/peano_lab/library'
SOURCE_SHA256 = '271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042'
PROVIDER_PINS = {
    'theorems.py': '05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919',
    'prime_field_arithmetic_candidate.py': 'd4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90',
    'prime_field_polynomial_candidate.py': '644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72',
    'prime_field_polynomial_convolution_candidate.py': '20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24',
    'prime_field_tables_candidate.py': '2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400',
    'finite_sum_theorems.py': '0d60b7a4fa21161def737fc6759b23e0679694052e95d97b419aa1ecb293c56e',
    'prime_field_polynomial_representation_candidate.py': 'fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a',
    'prime_field_polynomial_convolution_triangular_candidate.py': 'd53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f',
    'prime_field_polynomial_distributivity_candidate.py': 'a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86',
    'prime_field_polynomial_convolution_padding_candidate.py': '2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007',
    'prime_field_polynomial_equivalence_candidate.py': '929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373',
    'matrix_rank_finite_coding_candidate.py': '9a72aed5aa215816b5e26868c04453e0a3042486580e79a13234431b5f45952d',
}
WORKING_PINS = {
    'prime-field-shift-v1/prime_field_polynomial_shift_candidate.py': '325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b',
    'prime-field-shift-v1/test_prime_field_polynomial_shift_candidate.py': '0622fb92978fcf028842aa4d9822ef61213642eb852e080f7c787dcea4bb395f',
    'prime-field-scalar-v1/prime_field_polynomial_scalar_convolution_candidate.py': 'e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e',
    'prime-field-scalar-v1/test_prime_field_polynomial_scalar_convolution_candidate.py': '881452ada0b5dc3be7d6cd00ee31dc08075b07f51d83595ee60f8cfb40d4c6e5',
}
PRIVATE_MODULE_NAMES = ('working_append_candidate', 'working_append_shift_provider', 'working_append_scalar_provider')


def protected_bindings():
    return {name: value for name, value in sys.modules.items()
            if name.startswith('peano_lab.library.editions_v') or name in PRIVATE_MODULE_NAMES}


def load_file(name, path):
    before = protected_bindings()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())
    return module


candidate = load_file(PRIVATE_MODULE_NAMES[0], SOURCE)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_append_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def frozen_working_modules():
    for name, digest in WORKING_PINS.items():
        assert sha256((WORKING / name).read_bytes()).hexdigest() == digest
    return (
        load_file(PRIVATE_MODULE_NAMES[1], WORKING / 'prime-field-shift-v1/prime_field_polynomial_shift_candidate.py'),
        load_file(PRIVATE_MODULE_NAMES[2], WORKING / 'prime-field-scalar-v1/prime_field_polynomial_scalar_convolution_candidate.py'),
    )


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    from peano_lab.library.prime_field_polynomial_representation_candidate import make_prime_field_polynomial_representation_candidate_theorems
    from peano_lab.library.prime_field_polynomial_distributivity_candidate import make_prime_field_polynomial_distributivity_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_padding_candidate import make_prime_field_polynomial_convolution_padding_candidate_theorems
    from peano_lab.library.prime_field_polynomial_equivalence_candidate import make_prime_field_polynomial_equivalence_candidate_theorems
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems

    for name, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / name).read_bytes()).hexdigest() == digest
    shift, scalar = frozen_working_modules()
    factories = (
        make_prime_field_arithmetic_candidate_theorems, make_prime_field_polynomial_candidate_theorems,
        make_prime_field_polynomial_convolution_candidate_theorems, make_prime_field_polynomial_representation_candidate_theorems,
        make_prime_field_polynomial_distributivity_candidate_theorems, make_prime_field_polynomial_convolution_padding_candidate_theorems,
        make_prime_field_polynomial_equivalence_candidate_theorems, make_matrix_rank_finite_coding_candidate_theorems,
        shift.make_prime_field_polynomial_shift_candidate_theorems, scalar.make_prime_field_polynomial_scalar_convolution_candidate_theorems,
    )
    result = {row.name: row for row in THEOREMS}
    for factory in factories:
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


# Native first-order expected graphs, expanded independently of all candidate
# and canonical provider string builders.
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


def Prime(p):
    return f'~(({p})=1) /\\ forall independent_factor_a independent_factor_b. ({p})=independent_factor_a*independent_factor_b -> independent_factor_a=1 \\/ independent_factor_b=1'


def Coeff(p, b, c, length):
    i, a = 'independent_bounded_index', 'independent_bounded_value'
    return f'forall {i}. ({Lt(i,length)}) -> exists {a}. ' + And(At(b, c, i, a), Lt(a, p))


def Equal(b, c, d, e, length):
    i, a = 'independent_equal_index', 'independent_equal_value'
    return f'forall {i} {a}. ({Lt(i,length)}) -> ({At(b,c,i,a)}) -> ({At(d,e,i,a)})'


def Shift(b, c, length, d, e):
    return And(Equal(b, c, d, e, length), At(d, e, length, '0'))


def LeftPad(b, c, length, count, d, e):
    i, a = 'independent_pad_index', 'independent_pad_value'
    zeroes = f'forall {i}. ({Lt(i,count)}) -> ({At(d,e,i,"0")})'
    copy = f'forall {i} {a}. ({Lt(i,length)}) -> ({At(b,c,i,a)}) -> ({At(d,e,f"({count})+{i}",a)})'
    return And(zeroes, copy)


def Mod(p, a, b):
    return f'exists independent_balance_left independent_balance_right. ({a})+({p})*independent_balance_left=({b})+({p})*independent_balance_right'


def Residue(p, value, residue):
    return And(Lt(residue, p), Mod(p, value, residue))


def Multiply(p, k, a, b):
    return And(Lt(k, p), Lt(a, p), Residue(p, f'({k})*({a})', b))


def FieldAdd(p, a, b, c):
    return And(Lt(a, p), Lt(b, p), Residue(p, f'({a})+({b})', c))


def Scale(p, k, ab, ac, bb, bc, length):
    i, a, b = 'independent_scale_index', 'independent_scale_source', 'independent_scale_target'
    points = f'forall {i}. ({Lt(i,length)}) -> exists {a} {b}. ' + And(
        At(ab, ac, i, a), At(bb, bc, i, b), Multiply(p, k, a, b))
    return And(Lt(k, p), points)


def Add(p, ab, ac, bb, bc, cb, cc, length):
    i, a, b, c = 'independent_add_index', 'independent_add_left', 'independent_add_right', 'independent_add_result'
    return f'forall {i}. ({Lt(i,length)}) -> exists {a} {b} {c}. ' + And(
        At(ab, ac, i, a), At(bb, bc, i, b), At(cb, cc, i, c), FieldAdd(p, a, b, c))


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


def Power(b, c, length, k, a):
    i = 'independent_power_position'
    return '(exists ' + i + '. ' + And(f'{i}+S ({k})=({length})', At(b, c, i, a)) + ') \\/ (' + And(Le(length, k), f'({a})=0') + ')'


def Equivalent(b, c, length, d, e, other_length):
    k, a, r = 'independent_power', 'independent_power_left', 'independent_power_right'
    return f'forall {k} {a} {r}. ({Power(b,c,length,k,a)}) -> ({Power(d,e,other_length,k,r)}) -> {a}={r}'


def contract(parameters, premises, conclusion):
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join('(' + item + ')' for item in (*premises, conclusion))


FACTORS = ('ab', 'ac', 'L', 'bb', 'bc', 'M')
ALIGNED_PARAMETERS = ('p', 'c', 'ab', 'ac', 'L', 'pb', 'pc', 'N')
ALIGNED_OUTPUTS = ('ub', 'uc', 'vb', 'vc', 'UB', 'UC', 'VB', 'VC', 'rb', 'rc')
RECURRENCE_PARAMETERS = ('p', *FACTORS, 'c', 'db', 'dc', 'pb', 'pc', 'N', 'qb', 'qc', 'K', *ALIGNED_OUTPUTS)
H = 'L+S N'


def alignment_parts():
    return (Shift('pb', 'pc', 'N', 'ub', 'uc'), Scale('p', 'c', 'ab', 'ac', 'vb', 'vc', 'L'),
            LeftPad('ub', 'uc', 'S N', 'L', 'UB', 'UC'), LeftPad('vb', 'vc', 'L', 'S N', 'VB', 'VC'),
            Add('p', 'UB', 'UC', 'VB', 'VC', 'rb', 'rc', H))


def independent_contracts():
    common = (Prime('p'), Coeff('p', 'bb', 'bc', 'M'), Lt('c', 'p'),
              Equal('bb', 'bc', 'db', 'dc', 'M'), At('db', 'dc', 'M', 'c'))
    shift = Shift('bb', 'bc', 'M', 'sb', 'sc')
    singleton = At('kb', 'kc', '0', 'c')
    padded = LeftPad('kb', 'kc', '1', 'M', 'tb', 'tc')
    added = Add('p', 'sb', 'sc', 'tb', 'tc', 'db', 'dc', 'S M')
    old = Convolution('p', *FACTORS, 'pb', 'pc', 'N')
    new = Convolution('p', 'ab', 'ac', 'L', 'db', 'dc', 'S M', 'qb', 'qc', 'K')
    result = Equivalent('qb', 'qc', 'K', 'rb', 'rc', H)
    return (
        (('p', 'bb', 'bc', 'M', 'c', 'db', 'dc', 'sb', 'sc', 'kb', 'kc', 'tb', 'tc'),
         (*common, shift, singleton, padded), added),
        (('p', 'bb', 'bc', 'M', 'c', 'db', 'dc'), common,
         'exists sb sc kb kc tb tc. ' + And(shift, Coeff('p', 'kb', 'kc', '1'), singleton, padded, added)),
        (('p', *FACTORS, 'c', 'db', 'dc', 'kb', 'kc', 'tb', 'tc', 'i', 'u', 'v', 'w'),
         (*common, singleton, padded, ConvolutionCoefficient('p', *FACTORS, 'i', 'u'),
          ConvolutionCoefficient('p', 'ab', 'ac', 'L', 'tb', 'tc', 'S M', 'i', 'v'),
          ConvolutionCoefficient('p', 'ab', 'ac', 'L', 'db', 'dc', 'S M', 'i', 'w')), FieldAdd('p', 'u', 'v', 'w')),
        (ALIGNED_PARAMETERS, (Prime('p'), Lt('c', 'p'), Coeff('p', 'ab', 'ac', 'L'), Coeff('p', 'pb', 'pc', 'N')),
         'exists ' + ' '.join(ALIGNED_OUTPUTS) + '. ' + And(*alignment_parts())),
        (RECURRENCE_PARAMETERS, (Prime('p'), Equal('bb', 'bc', 'db', 'dc', 'M'), At('db', 'dc', 'M', 'c'),
                                 old, new, *alignment_parts()), result),
        (('p', *FACTORS, 'c', 'pb', 'pc', 'N'), (Prime('p'), Lt('c', 'p'), old),
         'exists db dc K qb qc ' + ' '.join(ALIGNED_OUTPUTS) + '. ' + And(
             Equal('bb', 'bc', 'db', 'dc', 'M'), At('db', 'dc', 'M', 'c'), new, *alignment_parts(), result)),
    )


NAMES = (
    'prime_field_polynomial_append_shift_constant_add',
    'prime_field_polynomial_append_shift_constant_decomposition_exists',
    'prime_field_convolution_coefficient_right_append_add',
    'prime_field_polynomial_shift_scale_aligned_sum_exists',
    'prime_field_polynomial_convolution_right_append_equivalent',
    'prime_field_polynomial_convolution_right_append_exists',
)
METRICS = ((137, 44), (115, 54), (108, 60), (158, 46), (448, 88), (246, 98))


def test_exact_source_inventory_and_all_local_dependency_ownership():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert len(rows()) == len(independent_contracts()) == 6
    assert sum(len(row.dependencies) for row in rows()) == 42
    known = set(provider_core())
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in known and row.script
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= known
        assert all(re.search(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", '\n'.join(row.script)) for name in row.dependencies)
        assert not any(command.startswith(('use ', 'admit', 'sorry')) or 'DNE' in command for command in row.script)
        known.add(row.name)


@pytest.mark.parametrize('index', range(6), ids=NAMES)
def test_independent_closed_fully_expanded_contract(index):
    same_ast(_closed_formula(rows()[index].statement), _closed_formula(contract(*independent_contracts()[index])))


def test_no_new_graph_no_alias_loader_and_exact_existing_shift():
    tree = ast.parse(SOURCE.read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.ImportFrom) and node.level == 0 for node in imports)
    assert {node.module for node in imports} == {
        '__future__', 'typing', 'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate', 'peano_lab.library.prime_field_polynomial_convolution_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate', 'peano_lab.library.prime_field_tables_candidate',
    }
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert candidate.__all__ == ['make_prime_field_polynomial_append_candidate_theorems']
    assert not any(name.endswith('_relation') for name in vars(candidate))
    parameters = ('b', 'c', 'L', 'd', 'e')
    actual = candidate._shift(*parameters, 'independent')
    shift, _scalar = frozen_working_modules()
    original = shift.prime_field_polynomial_shift_relation(*parameters, tag='independent', variables=parameters)
    prefix = 'forall ' + ' '.join(parameters) + '. '
    same_ast(_closed_formula(prefix + actual), _closed_formula(prefix + original))
    same_ast(_closed_formula(prefix + actual), _closed_formula(prefix + Shift(*parameters)))
    assert all('Equivalent' not in premise and 'Horner' not in premise
               for _, premises, _ in independent_contracts() for premise in premises)
    assert not any(word in row.name for row in rows() for word in ('associative', 'gcd', 'bezout', 'division_unique'))


@pytest.mark.parametrize('name', ('peano_lab.library.editions_v_append_import_guard', *PRIVATE_MODULE_NAMES))
def test_explicit_file_loading_preserves_preexisting_module_identity(name, monkeypatch):
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, marker)
    before = protected_bindings()
    loaded = load_file(PRIVATE_MODULE_NAMES[0], SOURCE)
    shifted = load_file(PRIVATE_MODULE_NAMES[1], WORKING / 'prime-field-shift-v1/prime_field_polynomial_shift_candidate.py')
    scalar = load_file(PRIVATE_MODULE_NAMES[2], WORKING / 'prime-field-scalar-v1/prime_field_polynomial_scalar_convolution_candidate.py')
    assert Path(loaded.__file__) == SOURCE
    assert Path(shifted.__file__).parent.name == 'prime-field-shift-v1'
    assert Path(scalar.__file__).parent.name == 'prime-field-scalar-v1'
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())
    assert sys.modules[name] is marker


def test_provider_paths_are_canonical_and_frozen_working_pair_bytes_stay_exact():
    provider_core()
    for filename, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / filename).read_bytes()).hexdigest() == digest
        name = 'peano_lab.library.' + filename.removesuffix('.py')
        if name in sys.modules:
            assert Path(sys.modules[name].__file__).resolve() == (LIBRARY / filename).resolve()
    for name, digest in WORKING_PINS.items():
        assert sha256((WORKING / name).read_bytes()).hexdigest() == digest


def test_local_novelty_against_actual_selected_dependency_types_only():
    # Full edition novelty is a distinct, separately scheduled gate.
    from peano_lab.library.formula_dag import FormulaArena

    table = body_core()
    selected = set(NAMES) | {name for row in rows() for name in row.dependencies}
    encoded = {name: FormulaArena().freeze(_closed_formula(table[name].statement)).to_json() for name in selected}
    for name in NAMES:
        assert all(encoded[name] != value for other, value in encoded.items() if other != name)


@pytest.mark.parametrize('index', range(6), ids=NAMES)
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


@pytest.mark.parametrize('index', range(6), ids=tuple(f'row{i:02d}' for i in range(6)))
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
EDGE_IDS = tuple(f'row{index:02d}-edge{edge:02d}' for edge, (index, _) in enumerate(EDGES))


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


def changed_contracts():
    result = []
    for index, (parameters, premises, conclusion) in enumerate(independent_contracts()):
        for position in range(len(premises)):
            result.append((index, f'missing-premise-{position}', contract(parameters, premises[:position] + premises[position+1:], conclusion)))
    wrong = {
        0: (('old-length-only', Add('p', 'sb', 'sc', 'tb', 'tc', 'db', 'dc', 'M')),
            ('extra-entry', Add('p', 'sb', 'sc', 'tb', 'tc', 'db', 'dc', 'S (S M)'))),
        1: (('raw-old-code', 'exists sb sc kb kc tb tc. ' + And(Shift('bb', 'bc', 'M', 'sb', 'sc'), 'sb=bb', 'sc=bc')),),
        2: (('natural-residue-sum', 'u+v=w'), ('missing-constant', 'u=w')),
        3: (('unreconciled-common-length', 'exists ' + ' '.join(ALIGNED_OUTPUTS) + '. ' + And(
            *alignment_parts()[:-1], Add('p', 'UB', 'UC', 'VB', 'VC', 'rb', 'rc', 'S N'))),),
        4: (('raw-code-identity', And('qb=rb', 'qc=rc')),
            ('false-successor-product-length', And('K=S N', Equivalent('qb', 'qc', 'K', 'rb', 'rc', H))),
            ('unshifted-old-product', Equivalent('qb', 'qc', 'K', 'pb', 'pc', 'N')),
            ('unshifted-scalar-only', Equivalent('qb', 'qc', 'K', 'vb', 'vc', 'L'))),
        5: (('false-successor-product-length', 'exists db dc K qb qc ' + ' '.join(ALIGNED_OUTPUTS) + '. ' + And(
            Equal('bb', 'bc', 'db', 'dc', 'M'), At('db', 'dc', 'M', 'c'),
            Convolution('p', 'ab', 'ac', 'L', 'db', 'dc', 'S M', 'qb', 'qc', 'K'), 'K=S N')),
            ('all-zero-append', 'exists db dc. ' + And(Equal('bb', 'bc', 'db', 'dc', 'M'), At('db', 'dc', 'M', '0')))),
    }
    for index, mutations in wrong.items():
        parameters, premises, _ = independent_contracts()[index]
        for label, conclusion in mutations:
            result.append((index, label, contract(parameters, premises, conclusion)))
    return tuple(result)


CHANGED = changed_contracts()


@pytest.mark.parametrize('index,label,statement', CHANGED, ids=tuple(f'row{i:02d}-{label}' for i, label, _ in CHANGED))
def test_fixed_body_rejects_altered_guards_or_other_claim(index, label, statement):
    # Exact-script rejection does not assert numerical independence of every
    # omitted premise or that every altered statement is mathematically false.
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())


def encode_beta(values, multiplier=1):
    values = tuple(values)
    assert type(multiplier) is int and multiplier > 0
    assert all(type(value) is int and value >= 0 for value in values)
    scale = (max(values, default=0) + 1) * math.factorial(max(1, len(values))) * multiplier
    code, product = 0, 1
    for i, value in enumerate(values):
        modulus = 1 + (i+1)*scale
        assert value < modulus and math.gcd(product, modulus) == 1
        correction = ((value-code) * pow(product, -1, modulus)) % modulus
        code += product*correction
        product *= modulus
    return code, scale


def beta(code, index):
    b, c = code
    quotient, value = divmod(b, 1+(index+1)*c)
    assert b == quotient*(1+(index+1)*c)+value and 0 <= value < 1+(index+1)*c
    return value


def prefix(code, length):
    return tuple(beta(code, i) for i in range(length))


def model_shift(source, length, target):
    return prefix(source, length) == prefix(target, length) and beta(target, length) == 0


def model_left_pad(source, length, count, target):
    return prefix(target, count) == (0,)*count and all(beta(source, i) == beta(target, count+i) for i in range(length))


def model_scale(p, c, source, target, length):
    return 0 <= c < p and all(0 <= beta(source, i) < p and 0 <= beta(target, i) < p
                             and (c*beta(source, i)) % p == beta(target, i) for i in range(length))


def model_add(p, left, right, output, length):
    return all(0 <= beta(left, i) < p and 0 <= beta(right, i) < p and 0 <= beta(output, i) < p
               and (beta(left, i)+beta(right, i)) % p == beta(output, i) for i in range(length))


def power(code, length, exponent):
    return beta(code, length-1-exponent) if exponent < length else 0


def equivalent(first, length, second, other_length):
    return all(power(first, length, exponent) == power(second, other_length, exponent)
               for exponent in range(max(length, other_length)+2))


def zero_extended(code, length, i):
    return beta(code, i) if i < length else 0


def actual_coefficient_witness(p, left, L, right, M, i, encoding=1):
    assert p > 0
    values = tuple(zero_extended(left, L, j)*zero_extended(right, M, i-j) for j in range(i+1))
    diagonal = encode_beta((*values, 101), encoding)
    partials = [0]
    for value in values:
        partials.append(partials[-1]+value)
    trace = encode_beta((*partials, 103), encoding+1)
    assert beta(trace, 0) == 0
    for j, value in enumerate(values):
        assert j+(i-j) == i and beta(diagonal, j) == value
        assert beta(trace, j+1) == beta(trace, j)+beta(diagonal, j)
    total = beta(trace, i+1)
    quotient, residue = divmod(total, p)
    assert residue < p and total == residue+p*quotient
    return residue, diagonal, trace, total


def product_values(p, left, right):
    if not left or not right:
        return ()
    return tuple(sum(left[j]*right[i-j] for j in range(len(left)) if 0 <= i-j < len(right)) % p
                 for i in range(len(left)+len(right)-1))


PAIRS = (((), ()), ((), (1,)), ((1,), ()), ((1, 2, 1), ()), ((1,), (1,)),
         ((0,), (1, 1)), ((1, 0), (0,)), ((0, 1), (1, 0)), ((1, 2), (2, 1)),
         ((0, 2, 0), (1, 0)), ((1, 0, 1), (1, 1, 1)))
PRIME_SCALARS = tuple((p, c) for p in (2, 3, 5, 7) for c in range(p))


@pytest.mark.parametrize('values', PAIRS)
@pytest.mark.parametrize('p,c', PRIME_SCALARS)
def test_actual_append_construction_all_index_sums_and_aligned_formal_recurrence(values, p, c):
    av, bv = (tuple(value % p for value in side) for side in values)
    L, M = len(av), len(bv)
    left, right = encode_beta((*av, 11, 13)), encode_beta((*bv, 17, 19))
    appended_values = (*bv, c)
    appended = encode_beta((*appended_values, 23, 29), 2)
    assert prefix(appended, M) == prefix(right, M) and beta(appended, M) == c
    shifted_factor = encode_beta((*bv, 0, 31), 3)
    singleton = encode_beta((c, 37), 5)
    padded_constant = encode_beta((0,)*M+(c, 41), 7)
    assert model_shift(right, M, shifted_factor)
    assert beta(singleton, 0) == c and model_left_pad(singleton, 1, M, padded_constant)
    assert model_add(p, shifted_factor, padded_constant, appended, M+1)
    pv, qv = product_values(p, av, bv), product_values(p, av, appended_values)
    N, K = len(pv), len(qv)
    assert N == (L+M-1 if L and M else 0)
    assert K == (L+M if L else 0)
    product = encode_beta((*pv, 43, 47))
    result = encode_beta((*qv, 53, 59), 2)
    shift_values, scalar_values = (*pv, 0), tuple((c*value) % p for value in av)
    shifted = encode_beta((*shift_values, 61), 3)
    scaled = encode_beta((*scalar_values, 67), 5)
    H = L+N+1
    aligned_left_values = (0,)*L+shift_values
    aligned_right_values = (0,)*(N+1)+scalar_values
    assert len(aligned_left_values) == len(aligned_right_values) == H == N+1+L
    aligned_left = encode_beta((*aligned_left_values, 71), 7)
    aligned_right = encode_beta((*aligned_right_values, 73), 11)
    total_values = tuple((a+b) % p for a, b in zip(aligned_left_values, aligned_right_values, strict=True))
    total = encode_beta((*total_values, 79), 13)
    assert model_shift(product, N, shifted) and model_scale(p, c, left, scaled, L)
    assert model_left_pad(shifted, N+1, L, aligned_left)
    assert model_left_pad(scaled, L, N+1, aligned_right)
    assert model_add(p, aligned_left, aligned_right, total, H)
    assert equivalent(result, K, total, H)
    assert result != total and beta(result, K) == 53 and beta(total, H) == 79
    for i in range(max(N, K)+3):
        old, _old_diag, _old_trace, _old_sum = actual_coefficient_witness(p, left, L, right, M, i)
        constant, _constant_diag, _constant_trace, _constant_sum = actual_coefficient_witness(p, left, L, padded_constant, M+1, i, 3)
        new, _new_diag, _new_trace, _new_sum = actual_coefficient_witness(p, left, L, appended, M+1, i, 5)
        shifted_old, _, _, _ = actual_coefficient_witness(p, left, L, shifted_factor, M+1, i, 7)
        assert old == shifted_old and (old+constant) % p == new
        if i < N:
            assert beta(product, i) == old
        else:
            assert old == 0
        if i < K:
            assert beta(result, i) == new
        else:
            assert new == 0
    if L and M:
        assert K == N+1 and H-K == L
    elif L == 0:
        assert K == N == 0 and H == 1
    else:
        assert M == N == 0 and K == L and H == L+1
    if c == 0:
        assert model_shift(right, M, appended)
        assert equivalent(result, K, shifted, N+1)


ALIGNMENT_PAIRS = (((), ()), ((), (1, 2)), ((1, 2), ()), ((1,), (2, 1)), ((0, 1, 0), (1,)))


@pytest.mark.parametrize('values', ALIGNMENT_PAIRS)
@pytest.mark.parametrize('p,c', ((2, 0), (2, 1), (3, 2), (5, 4)))
def test_aligned_sum_constructor_has_independent_bounded_inputs_not_assumed_product(values, p, c):
    av, pv = (tuple(value % p for value in side) for side in values)
    L, N = len(av), len(pv)
    left, product = encode_beta((*av, 17)), encode_beta((*pv, 19))
    shifted_values, scalar_values = (*pv, 0), tuple(c*value % p for value in av)
    shifted, scaled = encode_beta((*shifted_values, 23), 2), encode_beta((*scalar_values, 29), 3)
    aligned_left_values, aligned_right_values = (0,)*L+shifted_values, (0,)*(N+1)+scalar_values
    aligned_left, aligned_right = encode_beta((*aligned_left_values, 31), 5), encode_beta((*aligned_right_values, 37), 7)
    values = tuple((a+b) % p for a, b in zip(aligned_left_values, aligned_right_values, strict=True))
    total = encode_beta((*values, 41), 11)
    assert model_shift(product, N, shifted) and model_scale(p, c, left, scaled, L)
    assert model_left_pad(shifted, N+1, L, aligned_left) and model_left_pad(scaled, L, N+1, aligned_right)
    assert model_add(p, aligned_left, aligned_right, total, L+N+1)
    assert all(beta(total, i) < p for i in range(L+N+1))


@pytest.mark.parametrize('fault', ('changed-old-prefix', 'changed-next-entry'))
@pytest.mark.parametrize('p', (2, 3, 5, 7))
def test_each_append_clause_has_a_concrete_formal_recurrence_counterexample(fault, p):
    original, appended, c = (1,), (1, 1), 1
    wrong = (0, 1) if fault == 'changed-old-prefix' else (1, 0)
    assert (wrong[:1] != original) == (fault == 'changed-old-prefix')
    assert (wrong[1] != c) == (fault == 'changed-next-entry')
    expected = encode_beta(product_values(p, (1,), appended))
    actual = encode_beta(product_values(p, (1,), wrong), 2)
    assert not equivalent(expected, 2, actual, 2)


@pytest.mark.parametrize('fault', ('nonzero-leading-pad', 'wrong-offset-copy', 'trailing-instead-of-leading'))
def test_alignment_padding_clauses_are_substantive(fault):
    source = encode_beta((1, 2, 17))
    target_values = {'nonzero-leading-pad': (1, 1, 2), 'wrong-offset-copy': (0, 2, 1),
                     'trailing-instead-of-leading': (1, 2, 0)}[fault]
    bad = encode_beta((*target_values, 19), 2)
    assert not model_left_pad(source, 2, 1, bad)
    assert not equivalent(source, 2, bad, 3)


@pytest.mark.parametrize('p', (2, 3, 5))
def test_scalar_bound_is_required_when_old_right_factor_is_empty(p):
    arbitrary = encode_beta((17,))
    other = encode_beta((19,), 2)
    assert model_scale(p, 0, arbitrary, other, 0)
    assert not model_scale(p, p, arbitrary, other, 0)
    appended = encode_beta((p, 23), 3)
    assert beta(appended, 0) == p and not beta(appended, 0) < p


def test_empty_right_factor_refutes_universal_successor_product_length():
    av, bv = (1, 1, 1), ()
    old, new = product_values(2, av, bv), product_values(2, av, (1,))
    assert len(old) == 0 and len(new) == 3 and len(new) != len(old)+1
    shifted = encode_beta((0, 17))
    scaled = encode_beta((*av, 19), 2)
    H = 4
    total = encode_beta((0, *av, 23), 3)
    assert model_left_pad(shifted, 1, 3, encode_beta((0, 0, 0, 0, 29)))
    assert model_left_pad(scaled, 3, 1, total)
    assert equivalent(encode_beta(new), 3, total, H)


def test_empty_left_factor_compares_empty_product_with_nonempty_zero_sum():
    assert product_values(3, (), (1, 2, 1)) == ()
    empty = encode_beta((17,))
    zero = encode_beta((0, 19), 2)
    assert equivalent(empty, 0, zero, 1)
    assert empty != zero and beta(empty, 0) != beta(zero, 0)


def test_characteristic_two_uses_natural_coefficient_one_not_signed_code_two():
    assert product_values(2, (1, 1), (1, 1)) == (1, 0, 1)
    assert model_scale(2, 1, encode_beta((1,)), encode_beta((1,), 2), 1)
    assert not model_scale(2, 2, encode_beta((1,)), encode_beta((0,), 2), 1)


def test_finite_field_function_agreement_is_not_the_formal_recurrence_conclusion():
    # X^2+X vanishes at every point of F2 but is not the formal zero polynomial.
    values = (1, 1, 0)
    for x in (0, 1):
        total = 0
        for coefficient in values:
            total = (total*x+coefficient) % 2
        assert total == 0
    assert not equivalent(encode_beta(values), 3, encode_beta((0,), 2), 1)


def test_scalar_zero_does_not_constrain_actual_entries_after_any_prefix():
    old = encode_beta((1, 17, 19))
    appended = encode_beta((1, 0, 23, 29), 2)
    assert model_shift(old, 1, appended)
    first = encode_beta((0, 31), 3)
    second = encode_beta((0, 37), 5)
    assert model_scale(2, 0, old, first, 1) and model_scale(2, 0, old, second, 1)
    assert first != second and beta(first, 1) != beta(second, 1)
