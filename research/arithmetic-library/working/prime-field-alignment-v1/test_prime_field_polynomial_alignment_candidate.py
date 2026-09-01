"""Independent common-representative contracts and native-beta diagnostics.

Positive body tests call the unchanged dependency-curried HA checker.  They
do not close the dependency cone, import Alpha, accept a saved receipt, or
grant admission.  The integer models below are examples, not proofs.
"""

from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass, replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
from types import ModuleType

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LIBRARY = ROOT / 'peano-lab/py/peano_lab/library'
SOURCE = HERE / 'prime_field_polynomial_alignment_candidate.py'
PRIVATE_NAME = 'working_alignment_candidate_independent_test'
FUTURE_ALIAS = 'peano_lab.library.prime_field_polynomial_alignment_candidate'

# Source/specification pins are from the actual frozen source.  The body
# shapes were reported by the author's real conditional check; every positive
# test below independently replays the original checker before comparing them.
SOURCE_PIN: tuple[int, str] | None = (
    11780, 'eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e')
SPECS_SHA256: str | None = '76b9c342744170146fcb7898cb5a20154334147578b7e01d059f01b9015d5aec'
COMMAND_COUNTS: tuple[int, ...] | None = (42, 14, 46, 50, 27, 63, 16)
BODY_SHAPES: tuple[tuple[int, int], ...] | None = (
    (53, 29), (33, 14), (112, 47), (59, 27), (64, 35), (69, 33), (23, 18))

PROVIDER_PINS = {
    'candidate_validation.py': 'de38ddb037e03bbbfec2cc48a96aae5d5dd253c190968b61d9a9f7ff28cf9a42',
    'theorems.py': '05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919',
    'prime_field_arithmetic_candidate.py': 'd4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90',
    'prime_field_polynomial_candidate.py': '644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72',
    'prime_field_polynomial_representation_candidate.py': 'fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a',
    'prime_field_tables_candidate.py': '2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400',
}


def protected_bindings():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))
            or name in (PRIVATE_NAME, FUTURE_ALIAS)}


def load_actual_source():
    before = protected_bindings()
    assert SOURCE.is_file() and not SOURCE.is_symlink()
    specification = importlib.util.spec_from_file_location(PRIVATE_NAME, SOURCE)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys()
    assert all(after[name] is value for name, value in before.items())
    assert module.__file__ == str(SOURCE) and module.__spec__.origin == str(SOURCE)
    return module


candidate = load_actual_source()


def actual_input_pins():
    paths = (SOURCE, *(LIBRARY / name for name in PROVIDER_PINS))
    result = {}
    for path in paths:
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        result[path.relative_to(ROOT).as_posix()] = (len(raw), sha256(raw).hexdigest())
    return result


@pytest.fixture(autouse=True)
def frozen_inputs_and_foreign_authority_bindings_stay_unchanged():
    before, modules = actual_input_pins(), protected_bindings()
    assert SOURCE_PIN is not None, 'awaiting the actual mathematical source freeze'
    assert before[SOURCE.relative_to(ROOT).as_posix()] == SOURCE_PIN
    for name, digest in PROVIDER_PINS.items():
        assert before[(LIBRARY / name).relative_to(ROOT).as_posix()][1] == digest
    yield
    assert actual_input_pins() == before
    after = protected_bindings()
    assert after.keys() == modules.keys() and all(after[name] is value for name, value in modules.items())


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_alignment_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library import prime_field_polynomial_representation_candidate as representation

    assert representation.__file__ == str(LIBRARY / 'prime_field_polynomial_representation_candidate.py')
    table = {row.name: row for row in THEOREMS}
    for row in representation.make_prime_field_polynomial_representation_candidate_theorems(TheoremSpec):
        assert row.name not in table or table[row.name] == row
        table[row.name] = row
    return table


def body_core():
    result = dict(provider_core())
    for row in rows():
        assert row.name not in result
        result[row.name] = row
    return result


def same_ast(left, right):
    pending, seen = [(left, right)], set()
    while pending:
        first, second = pending.pop()
        assert type(first) is type(second)
        pair = id(first), id(second)
        if pair in seen:
            continue
        seen.add(pair)
        if is_dataclass(first):
            pending.extend((getattr(first, item.name), getattr(second, item.name)) for item in fields(first))
        else:
            assert first == second


def And(*clauses):
    result = '(' + clauses[-1] + ')'
    for clause in reversed(clauses[:-1]):
        result = '(' + clause + ') /\\ (' + result + ')'
    return result


def Lt(a, b):
    return f'exists independent_alignment_gap. independent_alignment_gap+S ({a})=({b})'


def Le(a, b):
    return f'exists independent_alignment_gap. independent_alignment_gap+({a})=({b})'


def Prime(p):
    return (f'~(({p})=1) /\\ forall independent_factor_left independent_factor_right. '
            f'({p})=independent_factor_left*independent_factor_right -> '
            'independent_factor_left=1 \\/ independent_factor_right=1')


def At(b, c, i, value):
    return And(
        f'exists independent_height. independent_height+S ({value})=S ((S ({i}))*({c}))',
        f'exists independent_quotient. ({b})=independent_quotient*S ((S ({i}))*({c}))+({value})')


def Coeff(p, b, c, length):
    return ('forall independent_index. (' + Lt('independent_index', length)
            + ') -> exists independent_value. ' + And(
                At(b, c, 'independent_index', 'independent_value'), Lt('independent_value', p)))


def Power(b, c, length, power, value):
    inside = 'exists independent_position. ' + And(
        f'independent_position+S ({power})=({length})', At(b, c, 'independent_position', value))
    return '(' + inside + ') \\/ (' + And(Le(length, power), f'({value})=0') + ')'


def Equivalent(b, c, length, d, e, other_length):
    power, left, right = 'independent_power', 'independent_left', 'independent_right'
    return (f'forall {power} {left} {right}. ({Power(b,c,length,power,left)}) -> '
            f'({Power(d,e,other_length,power,right)}) -> {left}={right}')


def Common(ab, ac, L, bb, bc, M, ub, uc, vb, vc, K):
    return And(Equivalent(ab, ac, L, ub, uc, K), Equivalent(bb, bc, M, vb, vc, K))


def BoundedRepresentative(p, ab, ac, L, ub, uc, K):
    return And(Coeff(p, ub, uc, K), Equivalent(ab, ac, L, ub, uc, K))


def BoundedCommon(p, ab, ac, L, bb, bc, M, ub, uc, vb, vc, K):
    return And(Coeff(p, ub, uc, K), Coeff(p, vb, vc, K),
               Common(ab, ac, L, bb, bc, M, ub, uc, vb, vc, K))


def contract(parameters, premises, conclusion):
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + part + ')' for part in (*premises, conclusion))


A, B = ('ab', 'ac', 'L'), ('bb', 'bc', 'M')
U, V = ('ub', 'uc', 'K'), ('vb', 'vc', 'K')
PARAMETERS = (*A, *B, 'ub', 'uc', 'vb', 'vc', 'K')
EXPECTED_NAMES = (
    'prime_field_polynomial_bounded_representative_at_length_exists',
    'prime_field_polynomial_common_representatives_same_length',
    'prime_field_polynomial_common_representatives_transport',
    'prime_field_polynomial_common_representatives_at_length_exists',
    'prime_field_polynomial_common_representatives_exists',
    'prime_field_polynomial_common_representatives_functional',
    'prime_field_polynomial_common_representatives_symmetric',
)
EXPECTED_DEPENDENCIES = (
    ('prime_field_polynomial_left_pad_exists', 'prime_field_polynomial_left_pad_bounded',
     'prime_field_polynomial_left_pad_equivalent'),
    ('prime_field_polynomial_power_coefficient_functional',),
    ('prime_field_polynomial_equivalent_transitive',),
    ('prime_field_polynomial_bounded_representative_at_length_exists',),
    ('prime_field_polynomial_common_representatives_at_length_exists', 'le_add_right'),
    ('prime_field_polynomial_equivalent_symmetric', 'prime_field_polynomial_equivalent_transitive'),
    (),
)


def independent_contracts():
    D, E = ('db', 'dc', 'J'), ('eb', 'ec', 'N')
    return (
        (('p', *A, 'K'), (Prime('p'), Coeff('p', *A), Le('L', 'K')),
         'exists ub uc. ' + BoundedRepresentative('p', *A, 'ub', 'uc', 'K')),
        (('ab', 'ac', 'bb', 'bc', 'K'), (),
         Common('ab', 'ac', 'K', 'bb', 'bc', 'K', 'ab', 'ac', 'bb', 'bc', 'K')),
        ((*PARAMETERS, *D, *E),
         (Equivalent(*D, *A), Equivalent(*E, *B), Common(*PARAMETERS)),
         Common(*D, *E, 'ub', 'uc', 'vb', 'vc', 'K')),
        (('p', *A, *B, 'K'),
         (Prime('p'), Coeff('p', *A), Coeff('p', *B), Le('L', 'K'), Le('M', 'K')),
         'exists ub uc vb vc. ' + BoundedCommon('p', *PARAMETERS)),
        (('p', *A, *B), (Prime('p'), Coeff('p', *A), Coeff('p', *B)),
         'exists ub uc vb vc. ' + BoundedCommon('p', *A, *B, 'ub', 'uc', 'vb', 'vc', 'L+M')),
        ((*PARAMETERS, 'db', 'dc', 'eb', 'ec', 'J'),
         (Common(*PARAMETERS), Common(*A, *B, 'db', 'dc', 'eb', 'ec', 'J')),
         And(Equivalent(*U, 'db', 'dc', 'J'), Equivalent(*V, 'eb', 'ec', 'J'))),
        (PARAMETERS, (Common(*PARAMETERS),), Common(*B, *A, 'vb', 'vc', 'ub', 'uc', 'K')),
    )


def specs_digest(specifications):
    digest = sha256()
    for row in specifications:
        value = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(value, ensure_ascii=True, separators=(',', ':')) + '\n').encode())
    return digest.hexdigest()


def test_frozen_source_inventory_and_exact_dependency_ownership():
    assert SOURCE_PIN is not None and SPECS_SHA256 is not None and COMMAND_COUNTS is not None
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert tuple(row.dependencies for row in rows()) == EXPECTED_DEPENDENCIES
    assert tuple(len(row.script) for row in rows()) == COMMAND_COUNTS
    assert specs_digest(rows()) == SPECS_SHA256
    known = set(provider_core())
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in known and row.script
        assert len(set(row.dependencies)) == len(row.dependencies) and set(row.dependencies) <= known
        assert all(re.search(r'(?<![\w\x27])' + re.escape(name) + r'(?![\w\x27])', '\n'.join(row.script))
                   for name in row.dependencies)
        assert not any(command.startswith(('admit', 'sorry', 'use ')) or 'DNE' in command for command in row.script)
        known.add(row.name)


@pytest.mark.parametrize('index', range(7), ids=tuple(f'row{i:02d}' for i in range(7)))
def test_independent_fully_expanded_contract(index):
    same_ast(_closed_formula(rows()[index].statement),
             _closed_formula(contract(*independent_contracts()[index])))


def test_canonical_reflexivity_is_reused_not_counted_as_a_new_statement():
    canonical = provider_core()['prime_field_polynomial_power_coefficient_functional']
    same_ast(_closed_formula(canonical.statement), _closed_formula(contract(A, (), Equivalent(*A, *A))))
    assert 'prime_field_polynomial_equivalent_reflexive' not in EXPECTED_NAMES
    assert rows()[1].dependencies == ('prime_field_polynomial_power_coefficient_functional',)


def test_public_common_graph_has_exactly_two_grouped_equivalences_and_eleven_arguments():
    assert len(PARAMETERS) == len(set(PARAMETERS)) == 11
    actual = candidate.prime_field_polynomial_common_representatives_relation(
        *PARAMETERS, tag='public_common', variables=PARAMETERS)
    same_ast(parse_formula_in_context(actual, list(PARAMETERS)),
             parse_formula_in_context(Common(*PARAMETERS), list(PARAMETERS)))
    assert candidate.__all__ == ['make_prime_field_polynomial_alignment_candidate_theorems',
                                'prime_field_polynomial_common_representatives_relation']


def test_only_constructors_assume_prime_canonicality_and_at_length_bounds():
    contracts = independent_contracts()
    assert [len(item[1]) for item in contracts] == [3, 0, 3, 5, 3, 2, 1]
    assert contracts[0][1][-1] == Le('L', 'K')
    assert contracts[3][1][-2:] == (Le('L', 'K'), Le('M', 'K'))
    assert 'L+M' in contracts[4][2] and 'exists K' not in contracts[4][2]
    for index in (1, 2, 5, 6):
        assert 'p' not in contracts[index][0]
    assert not any(conclusion in premises for _, premises, conclusion in contracts)


def test_source_has_only_canonical_imports_and_no_authority_or_new_kernel_former():
    tree = ast.parse(SOURCE.read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.ImportFrom) and node.level == 0 for node in imports)
    assert {node.module for node in imports} == {
        '__future__', 'typing', 'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate',
        'peano_lab.library.prime_field_tables_candidate'}
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert not any('gcd' in row.name or 'bezout' in row.name or 'admission' in row.name for row in rows())


@pytest.mark.parametrize('name', (PRIVATE_NAME, FUTURE_ALIAS,
                                'peano_lab.library.editions_v_alignment_guard'))
def test_direct_file_loader_preserves_foreign_module_identity(name, monkeypatch):
    foreign = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, foreign)
    before = protected_bindings()
    loaded = load_actual_source()
    assert loaded is not foreign and sys.modules[name] is foreign
    after = protected_bindings()
    assert after.keys() == before.keys() and all(after[key] is value for key, value in before.items())


def test_actual_canonical_provider_paths_and_bytes_are_unchanged():
    provider_core()
    for filename, digest in PROVIDER_PINS.items():
        path = LIBRARY / filename
        assert sha256(path.read_bytes()).hexdigest() == digest
        module = sys.modules.get('peano_lab.library.' + filename.removesuffix('.py'))
        if module is not None:
            assert module.__file__ == str(path) and module.__spec__.origin == str(path)


def test_local_novelty_compares_actual_core_formulas_not_names():
    table = body_core()
    selected = set(EXPECTED_NAMES) | {name for row in rows() for name in row.dependencies}
    encoded = {name: FormulaArena().freeze(_closed_formula(table[name].statement)).to_json()
               for name in selected}
    for name in EXPECTED_NAMES:
        assert all(encoded[name] != value for other, value in encoded.items() if other != name)


@pytest.mark.parametrize('position', range(11))
@pytest.mark.parametrize('form', ('successor_sum', 'product', 'constant'))
def test_each_public_argument_accepts_real_compound_terms(position, form):
    name = PARAMETERS[position]
    term = {'successor_sum': f'S ({name}+{name})', 'product': f'{name}*{name}',
            'constant': '104729'}[form]
    arguments = (*PARAMETERS[:position], term, *PARAMETERS[position + 1:])
    actual = candidate.prime_field_polynomial_common_representatives_relation(
        *arguments, tag='compound_common', variables=PARAMETERS)
    same_ast(parse_formula_in_context(actual, list(PARAMETERS)),
             parse_formula_in_context(Common(*arguments), list(PARAMETERS)))


@pytest.mark.parametrize('term', ('undeclared', 'ab -> ab', 'ab=0', 'ab; true', '', None, 7, False))
def test_public_relation_rejects_unknown_or_injected_terms(term):
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_common_representatives_relation(
            term, *PARAMETERS[1:], tag='invalid_term', variables=PARAMETERS)


@pytest.mark.parametrize('tag', ('', 'bad tag', 'forall', 'S', None, False))
def test_public_relation_rejects_bad_binder_tags(tag):
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_common_representatives_relation(
            *PARAMETERS, tag=tag, variables=PARAMETERS)


@pytest.mark.parametrize('context', ((), [], ('ab', 'ab'), ('bad name',), ('forall',), None))
def test_public_relation_rejects_bad_variable_contexts(context):
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_common_representatives_relation(
            *PARAMETERS, tag='invalid_context', variables=context)


@pytest.mark.parametrize('arguments', (PARAMETERS[:-1], (*PARAMETERS, 'K')))
def test_public_relation_rejects_wrong_arity(arguments):
    with pytest.raises(TypeError):
        candidate.prime_field_polynomial_common_representatives_relation(
            *arguments, tag='arity', variables=PARAMETERS)


def test_every_generated_quantifier_rejects_unused_and_used_context_capture():
    builder = candidate.prime_field_polynomial_common_representatives_relation
    formula = builder(*PARAMETERS, tag='capture_common', variables=PARAMETERS)
    binders = {name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.', formula)
               for name in clause.split()}
    assert binders and not binders.intersection(PARAMETERS)
    for binder in sorted(binders):
        with pytest.raises(ValueError, match='captures'):
            builder(*PARAMETERS, tag='capture_common', variables=(*PARAMETERS, binder))
        with pytest.raises(ValueError, match='captures'):
            builder('ab+' + binder, *PARAMETERS[1:], tag='capture_common', variables=(*PARAMETERS, binder))


@pytest.mark.parametrize('index', range(7), ids=tuple(f'row{i:02d}' for i in range(7)))
def test_actual_original_ha_body_and_exact_nodes_depth(index):
    assert BODY_SHAPES is not None, 'awaiting actual original-HA body metrics'
    row = rows()[index]
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == row.name
    assert (receipt.dependency_count, receipt.command_count) == (len(row.dependencies), len(row.script))
    assert (receipt.proof_nodes, receipt.proof_depth) == BODY_SHAPES[index]
    assert 0 < receipt.proof_objects <= receipt.proof_nodes and receipt.proof_depth <= 256


@pytest.mark.parametrize('index', range(7), ids=tuple(f'row{i:02d}' for i in range(7)))
@pytest.mark.parametrize('mutation', ('false_conclusion', 'missing_body', 'truncated_body'))
def test_false_or_incomplete_body_is_rejected(index, mutation):
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


EDGES = tuple((index, dependency) for index, dependencies in enumerate(EXPECTED_DEPENDENCIES)
              for dependency in dependencies)


@pytest.mark.parametrize('index,dependency', EDGES,
                         ids=tuple(f'edge{i:02d}' for i in range(len(EDGES))))
def test_each_removed_dependency_is_rejected(index, dependency):
    row = rows()[index]
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('index,dependency', EDGES,
                         ids=tuple(f'edge{i:02d}' for i in range(len(EDGES))))
def test_each_poisoned_dependency_is_rejected(index, dependency):
    table = body_core()
    table[dependency] = replace(table[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],), core=table)


def altered_contracts():
    result = []
    contracts = independent_contracts()
    for index, (parameters, premises, conclusion) in enumerate(contracts):
        for position in range(len(premises)):
            result.append((index, f'omitted-premise-{position}', contract(
                parameters, premises[:position] + premises[position + 1:], conclusion)))
    wrong = {
        0: ('exists ub uc. ' + And(BoundedRepresentative('p', *A, 'ub', 'uc', 'K'),
                                   'ub=ab', 'uc=ac'),),
        1: ('ab=bb',),
        2: ('J=L', 'N=M'),
        3: ('exists ub uc vb vc. ' + BoundedCommon('p', *A, *B, 'ub', 'uc', 'vb', 'vc', 'S K'),),
        4: ('exists ub uc vb vc. ' + BoundedCommon('p', *A, *B, 'ub', 'uc', 'vb', 'vc', '0'),),
        5: ('K=J', And('ub=db', 'uc=dc', 'vb=eb', 'vc=ec')),
        6: (Common(*A, *B, 'vb', 'vc', 'ub', 'uc', 'K'),),
    }
    for index, conclusions in wrong.items():
        parameters, premises, _ = contracts[index]
        result.extend((index, f'other-claim-{number}', contract(parameters, premises, conclusion))
                      for number, conclusion in enumerate(conclusions))
    return tuple(result)


ALTERED_CONTRACTS = altered_contracts()


@pytest.mark.parametrize('index,label,statement', ALTERED_CONTRACTS,
                         ids=tuple(f'row{i:02d}-{label}' for i, label, _ in ALTERED_CONTRACTS))
def test_fixed_body_rejects_dropped_guards_or_other_claim(index, label, statement):
    # These are fixed-script rejection checks, not claims that every omitted
    # primality premise has a counterexample at every nonprime modulus.
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())


@lru_cache(maxsize=None)
def encode_beta(values, multiplier=1):
    """Concrete CRT witnesses; no candidate graph or proof API is consulted."""
    assert type(values) is tuple and all(type(value) is int and value >= 0 for value in values)
    assert type(multiplier) is int and multiplier > 0
    scale = multiplier * math.factorial(len(values)) * (max(values, default=0) + 1)
    code, modulus = 0, 1
    for index, value in enumerate(values):
        divisor = 1 + (index + 1) * scale
        assert math.gcd(modulus, divisor) == 1 and value < divisor
        code += modulus * (((value - code) * pow(modulus, -1, divisor)) % divisor)
        modulus *= divisor
    assert all(code % (1 + (index + 1) * scale) == value for index, value in enumerate(values))
    return code, scale


def beta_entry(code, index):
    b, c = code
    modulus = 1 + (index + 1) * c
    quotient, value = divmod(b, modulus)
    height = modulus - value - 1
    assert min(b, c, index, quotient, value, height) >= 0
    assert height + value + 1 == modulus and b == quotient * modulus + value
    return value


def prefix(code, length):
    return tuple(beta_entry(code, index) for index in range(length))


def model_power(code, length, power):
    if power >= length:
        gap = power - length
        assert gap + length == power
        return 0
    index = length - power - 1
    assert index + power + 1 == length
    return beta_entry(code, index)


def equivalent(first, length, second, other_length):
    # Both actual graph branches give exterior zero at every higher power.
    return all(model_power(first, length, k) == model_power(second, other_length, k)
               for k in range(max(length, other_length) + 2))


def common(first, length, second, other_length, left, right, K):
    return equivalent(first, length, left, K) and equivalent(second, other_length, right, K)


def coefficient_bounds(p, code, length):
    return all(beta_entry(code, i) < p for i in range(length))


def pad(code, length, count, target):
    return all(beta_entry(target, i) == 0 for i in range(count)) and all(
        beta_entry(code, i) == beta_entry(target, count + i) for i in range(length))


MODEL_INPUTS = (
    ((), ()), ((), (1,)), ((1,), ()), ((1, 0), (1,)),
    ((0, 1), (0, 0, 1)), ((0, 0), (0,)), ((2, 3, 1), (1, 2)),
    ((1, 0, 2), (0, 2, 0, 1)),
)


@pytest.mark.parametrize('values', MODEL_INPUTS)
@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('extra', (0, 2))
def test_actual_beta_upper_bound_constructors_use_leading_zeros(values, p, extra):
    av, bv = (tuple(value % p for value in valueset) for valueset in values)
    L, M = len(av), len(bv)
    K = max(L, M) + extra
    a, b = encode_beta((*av, 11, 17), 1), encode_beta((*bv, 13, 19), 2)
    u = encode_beta((0,) * (K - L) + (*av, 23, 29), 3)
    v = encode_beta((0,) * (K - M) + (*bv, 31, 37), 4)
    assert coefficient_bounds(p, a, L) and coefficient_bounds(p, b, M)
    assert pad(a, L, K - L, u) and pad(b, M, K - M, v)
    assert common(a, L, b, M, u, v, K)
    assert common(b, M, a, L, v, u, K)
    assert coefficient_bounds(p, u, K) and coefficient_bounds(p, v, K)
    assert beta_entry(a, L) != beta_entry(u, K) and beta_entry(b, M) != beta_entry(v, K)


@pytest.mark.parametrize('values', MODEL_INPUTS)
def test_actual_explicit_sum_length_witnesses_include_empty_inputs(values):
    av, bv = values
    L, M = len(av), len(bv)
    a, b = encode_beta((*av, 11)), encode_beta((*bv, 13), 2)
    u, v = encode_beta((0,) * M + (*av, 17), 3), encode_beta((0,) * L + (*bv, 19), 4)
    assert M + L == L + M
    assert common(a, L, b, M, u, v, L + M)
    assert pad(a, L, M, u) and pad(b, M, L, v)


@pytest.mark.parametrize('values,K', (
    (((0, 0, 1), (0, 1)), 1),
    (((0, 0), (0,)), 0),
    (((0, 1, 2), (0, 0, 3)), 2),
))
def test_legitimate_shorter_common_representatives_do_not_imply_length_bounds(values, K):
    av, bv = values
    a, b = encode_beta((*av, 11)), encode_beta((*bv, 13), 2)
    shorten = lambda valueset: valueset[-K:] if K else ()
    u, v = encode_beta((*shorten(av), 17), 3), encode_beta((*shorten(bv), 19), 4)
    assert common(a, len(av), b, len(bv), u, v, K)
    assert K < len(av) and K < len(bv)


@pytest.mark.parametrize('values', MODEL_INPUTS)
def test_formal_transport_and_functionality_allow_independent_recodings_and_lengths(values):
    av, bv = values
    L, M = len(av), len(bv)
    K, J = L + M, L + M + 2
    a, b = encode_beta((*av, 11)), encode_beta((*bv, 13), 2)
    u, v = encode_beta((0,) * M + (*av, 17), 3), encode_beta((0,) * L + (*bv, 19), 4)
    d, e = encode_beta((0,) * (M + 2) + (*av, 23), 5), encode_beta((0,) * (L + 2) + (*bv, 29), 6)
    assert common(a, L, b, M, u, v, K) and common(a, L, b, M, d, e, J)
    assert equivalent(u, K, d, J) and equivalent(v, K, e, J)
    assert J != K and u != d and v != e
    recoded_a = encode_beta((0, *av, 31), 7)
    recoded_b = encode_beta((0, 0, *bv, 37), 8)
    assert equivalent(recoded_a, L + 1, a, L) and equivalent(recoded_b, M + 2, b, M)
    assert common(recoded_a, L + 1, recoded_b, M + 2, u, v, K)


@pytest.mark.parametrize('side', (0, 1))
def test_each_input_equivalence_is_substantive(side):
    zero, one = encode_beta((0,)), encode_beta((1,), 2)
    originals = [zero, zero]
    originals[side] = one
    assert not common(originals[0], 1, originals[1], 1, zero, zero, 1)
    assert equivalent(originals[1 - side], 1, zero, 1)
    assert not equivalent(originals[side], 1, zero, 1)


@pytest.mark.parametrize('side', (0, 1))
def test_dropping_either_upper_bound_cannot_construct_a_nonzero_missing_power(side):
    x, zero = encode_beta((1, 0)), encode_beta(())
    first, L, second, M = (x, 2, zero, 0) if side == 0 else (zero, 0, x, 2)
    K = 1
    assert coefficient_bounds(2, first, L) and coefficient_bounds(2, second, M)
    for a in (0, 1):
        for b in (0, 1):
            assert not common(first, L, second, M, encode_beta((a,)), encode_beta((b,), 2), K)


def test_zero_modulus_exposes_the_bounded_constructor_guard_but_not_the_common_graph():
    empty, leading_zero = (27, 19), encode_beta((0,), 2)
    assert coefficient_bounds(0, empty, 0)
    assert common(empty, 0, empty, 0, leading_zero, leading_zero, 1)
    assert not coefficient_bounds(0, leading_zero, 1)


def test_field_evaluation_agreement_is_not_formal_common_representatives():
    impostor, empty = encode_beta((1, 1, 0)), encode_beta(())
    assert coefficient_bounds(2, impostor, 3)
    assert all((x * x + x) % 2 == 0 for x in (0, 1))
    assert not equivalent(impostor, 3, empty, 0)
    assert not common(impostor, 3, empty, 0, empty, empty, 0)


def test_trailing_zero_is_a_shift_and_cannot_replace_leading_zero_alignment():
    one = encode_beta((1,))
    leading, trailing = encode_beta((0, 1), 2), encode_beta((1, 0), 3)
    assert equivalent(one, 1, leading, 2) and pad(one, 1, 1, leading)
    assert not equivalent(one, 1, trailing, 2) and not pad(one, 1, 1, trailing)


def test_empty_arbitrary_codes_and_free_outside_values_are_not_silently_identified():
    a, b, u, v = (27, 19), (31, 7), (7, 0), (99, 4)
    assert len({a, b, u, v}) == 4
    assert common(a, 0, b, 0, u, v, 0)
    assert beta_entry(a, 0) != beta_entry(u, 0)


def test_same_decoded_prefix_does_not_force_either_beta_parameter():
    first, second = (202, 12), (982, 24)
    assert first[0] != second[0] and first[1] != second[1]
    assert prefix(first, 2) == prefix(second, 2) == (7, 2)
    assert equivalent(first, 2, second, 2)
    assert beta_entry(first, 2) != beta_entry(second, 2)


def test_hand_checked_beta_codes_distinguish_left_alignment_from_right_extension():
    a, b, u, v, wrong_v = (15, 6), (3, 6), (15, 6), (42, 6), (52, 6)
    assert prefix(a, 2) == (1, 2) and prefix(b, 1) == (3,)
    assert prefix(v, 2) == (0, 3) and prefix(wrong_v, 2) == (3, 0)
    assert common(a, 2, b, 1, u, v, 2)
    assert not common(a, 2, b, 1, u, wrong_v, 2)
