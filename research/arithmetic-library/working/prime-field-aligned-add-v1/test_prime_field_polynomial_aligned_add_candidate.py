"""Independent actual-alignment contracts, beta models and conditional checks.

The expanded contracts below do not call candidate formula builders. Positive
checks replay the unchanged HA checker with actual named direct premises;
they are not whole-cone, Lean, ordinary-principal or Alpha acceptance.
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
SOURCE = HERE / 'prime_field_polynomial_aligned_add_candidate.py'
ALIGNMENT_SOURCE = HERE.parent / 'prime-field-alignment-v1/prime_field_polynomial_alignment_candidate.py'
SOURCE_PIN = (20704, 'a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db')
ALIGNMENT_PIN = (11780, 'eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e')
SPECS_SHA256 = 'b8ce285a000180baef6318db67202fc4fa258ae5bd6aabecfc098236f9588339'
COMMAND_COUNTS = (41, 19, 54, 93, 68, 117, 87, 146, 28)
# Author-observed shapes are compared only after actual independent replay.
BODY_SHAPES = ((41, 36), (40, 26), (86, 37), (278, 131), (229, 102),
               (168, 61), (111, 48), (172, 65), (80, 46))
PRIVATE_NAMES = ('working_aligned_add_independent_source', 'working_aligned_add_independent_alignment')
FUTURE_NAMES = ('peano_lab.library.prime_field_polynomial_aligned_add_candidate',
                'peano_lab.library.prime_field_polynomial_alignment_candidate')
PROVIDER_PINS = {
    'candidate_validation.py': 'de38ddb037e03bbbfec2cc48a96aae5d5dd253c190968b61d9a9f7ff28cf9a42',
    'theorems.py': '05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919',
    'prime_field_arithmetic_candidate.py': 'd4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90',
    'prime_field_polynomial_candidate.py': '644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72',
    'prime_field_polynomial_representation_candidate.py': 'fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a',
    'prime_field_polynomial_equivalence_candidate.py': '929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373',
    'prime_field_polynomial_subtraction_candidate.py': 'd08562b26c683a891e58a4b10faa495867d7487054b1ee7c99f091dd1c707b2b',
    'prime_field_tables_candidate.py': '2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400',
}


def protected_bindings():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))
            or name in (*PRIVATE_NAMES, *FUTURE_NAMES)}


def load_actual(path, name):
    before = protected_bindings()
    assert path.is_file() and not path.is_symlink()
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys()
    assert all(after[key] is value for key, value in before.items())
    assert module.__file__ == str(path) and module.__spec__.origin == str(path)
    return module


candidate = load_actual(SOURCE, PRIVATE_NAMES[0])
alignment = load_actual(ALIGNMENT_SOURCE, PRIVATE_NAMES[1])


def actual_input_pins():
    result = {}
    for path in (SOURCE, ALIGNMENT_SOURCE, *(LIBRARY / name for name in PROVIDER_PINS)):
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        result[path.relative_to(ROOT).as_posix()] = (len(raw), sha256(raw).hexdigest())
    return result


@pytest.fixture(autouse=True)
def frozen_sources_and_foreign_authority_bindings_are_preserved():
    before, modules = actual_input_pins(), protected_bindings()
    assert before[SOURCE.relative_to(ROOT).as_posix()] == SOURCE_PIN
    assert before[ALIGNMENT_SOURCE.relative_to(ROOT).as_posix()] == ALIGNMENT_PIN
    assert all(before[(LIBRARY / name).relative_to(ROOT).as_posix()][1] == digest
               for name, digest in PROVIDER_PINS.items())
    yield
    assert actual_input_pins() == before
    after = protected_bindings()
    assert after.keys() == modules.keys()
    assert all(after[name] is value for name, value in modules.items())


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_aligned_add_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library import prime_field_polynomial_candidate as polynomial
    from peano_lab.library import prime_field_polynomial_representation_candidate as representation
    from peano_lab.library import prime_field_polynomial_equivalence_candidate as equivalence
    from peano_lab.library import prime_field_polynomial_subtraction_candidate as subtraction

    result = {row.name: row for row in THEOREMS}
    for module, factory in (
        (polynomial, polynomial.make_prime_field_polynomial_candidate_theorems),
        (representation, representation.make_prime_field_polynomial_representation_candidate_theorems),
        (equivalence, equivalence.make_prime_field_polynomial_equivalence_candidate_theorems),
        (subtraction, subtraction.make_prime_field_polynomial_subtraction_candidate_theorems),
        (alignment, alignment.make_prime_field_polynomial_alignment_candidate_theorems),
    ):
        expected = ALIGNMENT_SOURCE if module is alignment else LIBRARY / (module.__name__.split('.')[-1]+'.py')
        assert module.__file__ == str(expected)
        for row in factory(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
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
        first, second = pending.pop()
        assert type(first) is type(second)
        pair = id(first), id(second)
        if pair in seen:
            continue
        seen.add(pair)
        if is_dataclass(first):
            pending.extend((getattr(first, field.name), getattr(second, field.name)) for field in fields(first))
        else:
            assert first == second


def And(*clauses):
    result = '('+clauses[-1]+')'
    for clause in reversed(clauses[:-1]):
        result = '('+clause+') /\\ ('+result+')'
    return result


def Lt(a, b):
    return f'exists independent_gap. independent_gap+S ({a})=({b})'


def Le(a, b):
    return f'exists independent_gap. independent_gap+({a})=({b})'


def Prime(p):
    return (f'~(({p})=1) /\\ forall independent_factor_left independent_factor_right. '
            f'({p})=independent_factor_left*independent_factor_right -> '
            'independent_factor_left=1 \\/ independent_factor_right=1')


def At(b, c, i, value):
    return And(
        f'exists independent_height. independent_height+S ({value})=S ((S ({i}))*({c}))',
        f'exists independent_quotient. ({b})=independent_quotient*S ((S ({i}))*({c}))+({value})')


def Coeff(p, b, c, length):
    return ('forall independent_index. ('+Lt('independent_index', length)
            +') -> exists independent_value. '+And(
                At(b, c, 'independent_index', 'independent_value'), Lt('independent_value', p)))


def Power(b, c, length, power, value):
    inside = 'exists independent_position. '+And(
        f'independent_position+S ({power})=({length})', At(b, c, 'independent_position', value))
    return '('+inside+') \\/ ('+And(Le(length, power), f'({value})=0')+')'


def Equivalent(b, c, length, d, e, other_length):
    k, a, r = 'independent_power', 'independent_left', 'independent_right'
    return f'forall {k} {a} {r}. ({Power(b,c,length,k,a)}) -> ({Power(d,e,other_length,k,r)}) -> {a}={r}'


def Common(ab, ac, L, bb, bc, M, ub, uc, vb, vc, K):
    return And(Equivalent(ab, ac, L, ub, uc, K), Equivalent(bb, bc, M, vb, vc, K))


def FieldAdd(p, a, b, r):
    congruence = (f'exists independent_offset_left independent_offset_right. '
                  f'({a})+({b})+({p})*independent_offset_left=({r})+({p})*independent_offset_right')
    return And(Lt(a, p), Lt(b, p), And(Lt(r, p), congruence))


def FixedAdd(p, ab, ac, bb, bc, rb, rc, length):
    i, a, b, r = 'independent_add_i', 'independent_add_a', 'independent_add_b', 'independent_add_r'
    return f'forall {i}. ({Lt(i,length)}) -> exists {a} {b} {r}. '+And(
        At(ab, ac, i, a), At(bb, bc, i, b), At(rb, rc, i, r), FieldAdd(p, a, b, r))


def FixedSubtract(p, ab, ac, bb, bc, rb, rc, length):
    i, a, b, r = 'independent_sub_i', 'independent_sub_a', 'independent_sub_b', 'independent_sub_r'
    return f'forall {i}. ({Lt(i,length)}) -> exists {a} {b} {r}. '+And(
        At(ab, ac, i, a), At(bb, bc, i, b), At(rb, rc, i, r), FieldAdd(p, b, r, a))


def AlignedAdd(p, ab, ac, L, bb, bc, M, rb, rc, N):
    ub, uc, vb, vc, tb, tc, K = (
        'independent_u_code', 'independent_u_scale', 'independent_v_code', 'independent_v_scale',
        'independent_t_code', 'independent_t_scale', 'independent_common_length')
    witness = And(Common(ab, ac, L, bb, bc, M, ub, uc, vb, vc, K),
                  FixedAdd(p, ub, uc, vb, vc, tb, tc, K), Equivalent(tb, tc, K, rb, rc, N))
    return And(Coeff(p, ab, ac, L), Coeff(p, bb, bc, M), Coeff(p, rb, rc, N),
               f'exists {ub} {uc} {vb} {vc} {tb} {tc} {K}. '+witness)


def AlignedSubtract(p, ab, ac, L, bb, bc, M, rb, rc, N):
    return AlignedAdd(p, bb, bc, M, rb, rc, N, ab, ac, L)


def contract(parameters, premises, conclusion):
    return 'forall '+' '.join(parameters)+'. '+' -> '.join('('+part+')' for part in (*premises, conclusion))


A, B, R = ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('rb', 'rc', 'N')
PARAMETERS = ('p', *A, *B, *R)
WITNESSES = ('ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'K')
U, V, T = ('ub', 'uc', 'K'), ('vb', 'vc', 'K'), ('tb', 'tc', 'K')
FIXED_PARAMETERS = ('p', 'ab', 'ac', 'bb', 'bc', 'rb', 'rc', 'K')
EXPECTED_NAMES = tuple('prime_field_polynomial_'+stem for stem in (
    'aligned_add_from_common', 'aligned_add_bounded', 'aligned_add_from_fixed',
    'aligned_add_transport', 'aligned_add_commutative', 'aligned_add_functional',
    'aligned_add_exists', 'aligned_add_realize', 'aligned_subtract_from_fixed'))
EXPECTED_DEPENDENCIES = (
    (),
    (),
    ('prime_field_polynomial_add_bounded', 'prime_field_polynomial_aligned_add_from_common',
     'prime_field_polynomial_common_representatives_same_length', 'prime_field_polynomial_power_coefficient_functional'),
    ('prime_field_polynomial_aligned_add_from_common',
     'prime_field_polynomial_common_representatives_transport', 'prime_field_polynomial_equivalent_transitive'),
    ('prime_field_polynomial_aligned_add_from_common', 'prime_field_polynomial_common_representatives_symmetric',
     'prime_field_polynomial_add_commutative'),
    ('prime_field_polynomial_common_representatives_functional', 'prime_field_polynomial_add_equivalent_congruent',
     'prime_field_polynomial_equivalent_symmetric', 'prime_field_polynomial_equivalent_transitive'),
    ('prime_field_polynomial_common_representatives_exists', 'prime_field_polynomial_add_exists', 'prime_nonzero',
     'prime_field_polynomial_add_bounded', 'prime_field_polynomial_aligned_add_from_common',
     'prime_field_polynomial_power_coefficient_functional'),
    ('prime_field_polynomial_add_exists', 'prime_nonzero', 'prime_field_polynomial_aligned_add_from_fixed',
     'prime_field_polynomial_aligned_add_transport', 'prime_field_polynomial_equivalent_symmetric',
     'prime_field_polynomial_aligned_add_functional', 'prime_field_polynomial_add_transport',
     'prime_field_polynomial_equivalent_implies_equal_same_length'),
    ('prime_field_polynomial_aligned_add_from_fixed', 'prime_field_polynomial_subtract_recover_add'),
)


def independent_contracts():
    D, E, F, S = ('db', 'dc', 'J'), ('eb', 'ec', 'H'), ('fb', 'fc', 'I'), ('sb', 'sc', 'J')
    same = ('p', 'ab', 'ac', 'K', 'bb', 'bc', 'K', 'rb', 'rc', 'K')
    return (
        ((*PARAMETERS, *WITNESSES),
         (Coeff('p', *A), Coeff('p', *B), Coeff('p', *R),
          Common(*A, *B, 'ub', 'uc', 'vb', 'vc', 'K'),
          FixedAdd('p', 'ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'K'), Equivalent(*T, *R)),
         AlignedAdd(*PARAMETERS)),
        (PARAMETERS, (AlignedAdd(*PARAMETERS),), And(Coeff('p', *A), Coeff('p', *B), Coeff('p', *R))),
        (FIXED_PARAMETERS, (FixedAdd(*FIXED_PARAMETERS),), AlignedAdd(*same)),
        ((*PARAMETERS, *D, *E, *F),
         (Coeff('p', *D), Coeff('p', *E), Coeff('p', *F), Equivalent(*D, *A),
          Equivalent(*E, *B), Equivalent(*R, *F), AlignedAdd(*PARAMETERS)),
         AlignedAdd('p', *D, *E, *F)),
        (PARAMETERS, (AlignedAdd(*PARAMETERS),), AlignedAdd('p', *B, *A, *R)),
        ((*PARAMETERS, *S),
         (Prime('p'), AlignedAdd(*PARAMETERS), AlignedAdd('p', *A, *B, *S)), Equivalent(*R, *S)),
        (('p', *A, *B), (Prime('p'), Coeff('p', *A), Coeff('p', *B)),
         'exists rb rc. '+AlignedAdd('p', *A, *B, 'rb', 'rc', 'L+M')),
        ((*PARAMETERS, *WITNESSES),
         (Prime('p'), AlignedAdd(*PARAMETERS), Coeff('p', *U), Coeff('p', *V), Coeff('p', *T),
          Common(*A, *B, 'ub', 'uc', 'vb', 'vc', 'K'), Equivalent(*R, *T)),
         FixedAdd('p', 'ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'K')),
        (FIXED_PARAMETERS, (FixedSubtract(*FIXED_PARAMETERS),), AlignedSubtract(*same)),
    )


def specs_digest(specifications):
    digest = sha256()
    for row in specifications:
        value = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(value, ensure_ascii=True, separators=(',', ':'))+'\n').encode())
    return digest.hexdigest()


def test_actual_frozen_source_inventory_and_direct_provider_ownership():
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert tuple(row.dependencies for row in rows()) == EXPECTED_DEPENDENCIES
    assert tuple(len(row.script) for row in rows()) == COMMAND_COUNTS
    assert specs_digest(rows()) == SPECS_SHA256 and sum(map(len, EXPECTED_DEPENDENCIES)) == 30
    core = body_core()
    for row in rows():
        assert all(name in core for name in row.dependencies)
        assert all(name not in EXPECTED_NAMES or EXPECTED_NAMES.index(name) < EXPECTED_NAMES.index(row.name)
                   for name in row.dependencies)
    assert not any(name.startswith('peano_lab.library.editions') for name in sys.modules)


@pytest.mark.parametrize('index', range(9), ids=lambda index: f'row{index:02d}')
def test_each_independent_fully_expanded_contract(index):
    expected = contract(*independent_contracts()[index])
    same_ast(_closed_formula(rows()[index].statement), _closed_formula(expected))


def test_relation_builders_match_independent_common_group_and_subtraction_permutation():
    for builder, expected in (
        (candidate.prime_field_polynomial_aligned_add_relation, AlignedAdd(*PARAMETERS)),
        (candidate.prime_field_polynomial_aligned_subtract_relation, AlignedSubtract(*PARAMETERS)),
    ):
        actual = builder(*PARAMETERS, tag='exact_builder', variables=PARAMETERS)
        same_ast(parse_formula_in_context(actual, list(PARAMETERS)),
                 parse_formula_in_context(expected, list(PARAMETERS)))
    permuted = candidate.prime_field_polynomial_aligned_add_relation(
        'p', *B, *R, *A, tag='literal_permutation', variables=PARAMETERS)
    subtraction = candidate.prime_field_polynomial_aligned_subtract_relation(
        *PARAMETERS, tag='literal_permutation', variables=PARAMETERS)
    assert subtraction == permuted


def test_novelty_is_local_exact_ast_not_a_name_or_full_alpha_claim():
    claims = [_closed_formula(row.statement) for row in rows()]
    canonical = provider_core()
    dependencies = {name for row in rows() for name in row.dependencies if name not in EXPECTED_NAMES}
    dependency_formulas = [_closed_formula(canonical[name].statement) for name in sorted(dependencies)]
    keys = [json.dumps(FormulaArena().freeze(formula).to_json(), sort_keys=True) for formula in claims]
    old_keys = {json.dumps(FormulaArena().freeze(formula).to_json(), sort_keys=True)
                for formula in dependency_formulas}
    assert len(keys) == len(set(keys)) == 9
    assert not set(keys) & old_keys


def test_source_imports_are_canonical_and_no_checker_or_graph_oracle_is_added():
    tree = ast.parse(SOURCE.read_text())
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert all(name in {
        '__future__', 'typing', 'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate',
        'peano_lab.library.prime_field_polynomial_subtraction_candidate'} for name in imports)
    calls = {node.func.id for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    assert not calls.intersection({'replay', 'check_proof', 'check_bundle', 'compile_proof',
                                   'require_live', 'register_axiom', 'eval', 'exec'})


@pytest.mark.parametrize('name', (*PRIVATE_NAMES, *FUTURE_NAMES, 'peano_lab.library.editions_v33'))
def test_direct_file_loader_preserves_foreign_modules(name, monkeypatch):
    foreign = ModuleType(name)
    with monkeypatch.context() as scoped:
        scoped.setitem(sys.modules, name, foreign)
        loaded = load_actual(SOURCE, name)
        assert loaded is not foreign and sys.modules[name] is foreign


BUILDERS = (candidate.prime_field_polynomial_aligned_add_relation,
            candidate.prime_field_polynomial_aligned_subtract_relation)


@pytest.mark.parametrize('builder', BUILDERS, ids=('add', 'subtract'))
@pytest.mark.parametrize('position', range(10))
@pytest.mark.parametrize('form', ('successor_sum', 'product', 'zero'))
def test_every_public_argument_accepts_real_compound_terms(builder, position, form):
    arguments = list(PARAMETERS)
    value = arguments[position]
    arguments[position] = {'successor_sum': f'S ({value}+1)',
                           'product': f'({value})*({value})', 'zero': '0'}[form]
    expanded = builder(*arguments, tag='compound', variables=PARAMETERS)
    independent = (AlignedAdd if builder is BUILDERS[0] else AlignedSubtract)(*arguments)
    same_ast(parse_formula_in_context(expanded, list(PARAMETERS)),
             parse_formula_in_context(independent, list(PARAMETERS)))


@pytest.mark.parametrize('builder', BUILDERS, ids=('add', 'subtract'))
@pytest.mark.parametrize('term', ('undeclared', 'p -> p', 'p=0', 'p; true', '', None, 7, False))
def test_public_builders_reject_nonterms_and_injection(builder, term):
    with pytest.raises((ValueError, TypeError)):
        builder(term, *PARAMETERS[1:], tag='badterm', variables=PARAMETERS)


@pytest.mark.parametrize('builder', BUILDERS, ids=('add', 'subtract'))
@pytest.mark.parametrize('tag', ('', 'bad tag', 'forall', 'S', None, False))
def test_public_builders_reject_bad_binder_tags(builder, tag):
    with pytest.raises((ValueError, TypeError)):
        builder(*PARAMETERS, tag=tag, variables=PARAMETERS)


@pytest.mark.parametrize('builder', BUILDERS, ids=('add', 'subtract'))
@pytest.mark.parametrize('context', ((), [], ('p', 'p'), ('bad name',), ('forall',), None))
def test_public_builders_reject_bad_contexts(builder, context):
    with pytest.raises((ValueError, TypeError)):
        builder(*PARAMETERS, tag='badcontext', variables=context)


@pytest.mark.parametrize('builder', BUILDERS, ids=('add', 'subtract'))
@pytest.mark.parametrize('arguments', (PARAMETERS[:-1], (*PARAMETERS, 'N')))
def test_public_builders_reject_wrong_arity(builder, arguments):
    with pytest.raises(TypeError):
        builder(*arguments, tag='arity', variables=PARAMETERS)


@pytest.mark.parametrize('builder', BUILDERS, ids=('add', 'subtract'))
def test_every_generated_binder_rejects_actual_or_unused_context_capture(builder):
    source = builder(*PARAMETERS, tag='capture', variables=PARAMETERS)
    binders = {name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.', source)
               for name in clause.split()}
    assert len(binders) > 20 and not binders.intersection(PARAMETERS)
    for binder in sorted(binders):
        with pytest.raises(ValueError, match='captures'):
            builder(*PARAMETERS, tag='capture', variables=(*PARAMETERS, binder))
        arguments = (binder, *PARAMETERS[1:])
        with pytest.raises(ValueError, match='captures'):
            builder(*arguments, tag='capture', variables=(*PARAMETERS, binder))


@pytest.mark.parametrize('index', range(9), ids=lambda index: f'row{index:02d}')
def test_actual_original_ha_body_and_exact_shape(index):
    row = rows()[index]
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == row.name
    assert (receipt.dependency_count, receipt.command_count) == (len(row.dependencies), len(row.script))
    assert (receipt.proof_nodes, receipt.proof_depth) == BODY_SHAPES[index]
    assert 0 < receipt.proof_objects <= receipt.proof_nodes and receipt.proof_depth <= 256


@pytest.mark.parametrize('index', range(9), ids=lambda index: f'row{index:02d}')
@pytest.mark.parametrize('mutation', ('false_conclusion', 'missing_body', 'truncated_body'))
def test_false_or_incomplete_body_is_rejected(index, mutation):
    row = rows()[index]
    if mutation == 'false_conclusion':
        parameters, premises, _ = independent_contracts()[index]
        changed = replace(row, statement=contract(parameters, premises, '0=1'))
    else:
        changed = replace(row, script=() if mutation == 'missing_body' else row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


EDGES = tuple((index, name) for index, dependencies in enumerate(EXPECTED_DEPENDENCIES)
              for name in dependencies)


@pytest.mark.parametrize('index,dependency', EDGES, ids=lambda value: str(value))
def test_each_removed_dependency_is_rejected(index, dependency):
    row = rows()[index]
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('index,dependency', EDGES, ids=lambda value: str(value))
def test_each_poisoned_dependency_is_rejected(index, dependency):
    table = body_core()
    table[dependency] = replace(table[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],), core=table)


def altered_contracts():
    contracts, result = independent_contracts(), []
    for index, (parameters, premises, conclusion) in enumerate(contracts):
        for position in range(len(premises)):
            result.append((index, f'omit{position}', contract(
                parameters, premises[:position]+premises[position+1:], conclusion)))
    wrong = {
        0: (AlignedSubtract(*PARAMETERS),),
        1: ('L=M', And('ab=bb', 'ac=bc')),
        2: (AlignedAdd('p', 'ab', 'ac', 'K', 'bb', 'bc', 'K', 'rb', 'rc', 'S K'),),
        3: (AlignedSubtract('p', 'db', 'dc', 'J', 'eb', 'ec', 'H', 'fb', 'fc', 'I'),),
        4: (AlignedAdd('p', *R, *B, *A),),
        5: ('N=J', And('rb=sb', 'rc=sc')),
        6: ('exists rb rc. '+AlignedAdd('p', *A, *B, 'rb', 'rc', '0'),),
        7: (FixedAdd('p', 'ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'S K'), 'rb=tb'),
        8: (AlignedAdd('p', 'ab', 'ac', 'K', 'bb', 'bc', 'K', 'rb', 'rc', 'K'),),
    }
    for index, conclusions in wrong.items():
        parameters, premises, _ = contracts[index]
        result.extend((index, f'other{number}', contract(parameters, premises, conclusion))
                      for number, conclusion in enumerate(conclusions))
    return tuple(result)


ALTERED_CONTRACTS = altered_contracts()


@pytest.mark.parametrize('index,label,statement', ALTERED_CONTRACTS,
                         ids=tuple(f'row{index:02d}-{label}' for index, label, _ in ALTERED_CONTRACTS))
def test_fixed_body_rejects_removed_guards_or_different_claim(index, label, statement):
    # Fixed-body failure does not claim every unproved weaker theorem is false.
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())


@lru_cache(maxsize=None)
def encode_beta(values, multiplier=1):
    assert type(values) is tuple and all(type(value) is int and value >= 0 for value in values)
    assert type(multiplier) is int and multiplier > 0
    scale = multiplier*math.factorial(len(values))*(max(values, default=0)+1)
    code, modulus = 0, 1
    for index, value in enumerate(values):
        divisor = 1+(index+1)*scale
        assert math.gcd(modulus, divisor) == 1 and value < divisor
        code += modulus*(((value-code)*pow(modulus, -1, divisor)) % divisor)
        modulus *= divisor
    assert all(code % (1+(index+1)*scale) == value for index, value in enumerate(values))
    return code, scale


def beta_entry(code, index):
    b, c = code
    divisor = 1+(index+1)*c
    quotient, value = divmod(b, divisor)
    height = divisor-value-1
    assert min(b, c, index, quotient, value, height) >= 0
    assert height+value+1 == divisor and b == quotient*divisor+value
    return value


def prefix(code, length):
    return tuple(beta_entry(code, i) for i in range(length))


def coefficient_bounds(p, code, length):
    return all(beta_entry(code, i) < p for i in range(length))


def power(code, length, k):
    if k >= length:
        assert (k-length)+length == k
        return 0
    index = length-k-1
    assert index+k+1 == length
    return beta_entry(code, index)


def equivalent(a, L, b, M):
    return all(power(a, L, k) == power(b, M, k) for k in range(max(L, M)+2))


def common(a, L, b, M, u, v, K):
    return equivalent(a, L, u, K) and equivalent(b, M, v, K)


def field_add(p, a, b, r):
    if not all(0 <= value < p for value in (a, b, r)):
        return False
    if (a+b-r) % p:
        return False
    difference = (a+b-r)//p
    left, right = max(-difference, 0), max(difference, 0)
    assert a+b+p*left == r+p*right and min(left, right) >= 0
    return True


def fixed_add(p, a, b, r, K):
    return all(field_add(p, beta_entry(a, i), beta_entry(b, i), beta_entry(r, i)) for i in range(K))


def aligned_add_model(p, a, L, b, M, r, N, u, v, t, K):
    return (coefficient_bounds(p, a, L) and coefficient_bounds(p, b, M)
            and coefficient_bounds(p, r, N) and common(a, L, b, M, u, v, K)
            and fixed_add(p, u, v, t, K) and equivalent(t, K, r, N))


def trim(values):
    index = 0
    while index < len(values) and values[index] == 0:
        index += 1
    return values[index:]


def model_witnesses(p, av, bv, K, *, output_padding=0):
    short_a, short_b = trim(av), trim(bv)
    assert K >= max(len(short_a), len(short_b))
    uv, vv = (0,)*(K-len(short_a))+short_a, (0,)*(K-len(short_b))+short_b
    tv = tuple((a+b) % p for a, b in zip(uv, vv))
    rv = (0,)*output_padding+trim(tv)
    return (encode_beta(av), encode_beta(bv, 2), encode_beta(rv, 3), len(rv),
            encode_beta(uv, 4), encode_beta(vv, 5), encode_beta(tv, 6))


MODEL_INPUTS = (
    ((), ()), ((), (1,)), ((1,), ()), ((1, 0), (1,)),
    ((0, 1), (0, 0, 1)), ((0, 0), (0,)), ((2, 3, 1), (1, 2)),
    ((1, 0, 2), (0, 2, 0, 1)),
)


@pytest.mark.parametrize('values', MODEL_INPUTS)
@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('padding', (0, 2))
def test_actual_unequal_length_sum_and_independent_output_beta_witnesses(values, p, padding):
    av, bv = (tuple(value % p for value in part) for part in values)
    L, M, K = len(av), len(bv), len(av)+len(bv)
    a, b, r, N, u, v, t = model_witnesses(p, av, bv, K, output_padding=padding)
    assert aligned_add_model(p, a, L, b, M, r, N, u, v, t, K)
    assert aligned_add_model(p, b, M, a, L, r, N, v, u, t, K)
    assert prefix(u, K) == (0,)*(K-L)+av
    assert prefix(v, K) == (0,)*(K-M)+bv


@pytest.mark.parametrize('values', MODEL_INPUTS)
@pytest.mark.parametrize('p', (2, 5))
def test_formal_functionality_and_realization_at_shorter_or_longer_common_lengths(values, p):
    av, bv = (tuple(value % p for value in part) for part in values)
    minimum = max(len(trim(av)), len(trim(bv)))
    first = model_witnesses(p, av, bv, minimum)
    second = model_witnesses(p, av, bv, minimum+2, output_padding=3)
    a, b, r, N, u, v, t = first
    aa, bb, rr, J, uu, vv, tt = second
    assert aligned_add_model(p, a, len(av), b, len(bv), r, N, u, v, t, minimum)
    assert aligned_add_model(p, aa, len(av), bb, len(bv), rr, J, uu, vv, tt, minimum+2)
    assert equivalent(r, N, rr, J)
    assert common(a, len(av), b, len(bv), uu, vv, minimum+2)
    assert equivalent(r, N, tt, minimum+2) and fixed_add(p, uu, vv, tt, minimum+2)
    recoded_a, recoded_b, recoded_r = encode_beta(av, 7), encode_beta(bv, 8), encode_beta(prefix(r, N), 9)
    assert aligned_add_model(p, recoded_a, len(av), recoded_b, len(bv), recoded_r, N,
                             u, v, t, minimum)


@pytest.mark.parametrize('p', (2, 3, 4, 5))
@pytest.mark.parametrize('values', MODEL_INPUTS)
def test_actual_fixed_subtraction_supplies_literal_B_plus_R_equals_A(p, values):
    av, bv = (tuple(value % p for value in part) for part in values)
    K = max(len(av), len(bv))
    av, bv = (0,)*(K-len(av))+av, (0,)*(K-len(bv))+bv
    rv = tuple((a-b) % p for a, b in zip(av, bv))
    a, b, r = encode_beta(av), encode_beta(bv, 2), encode_beta(rv, 3)
    assert all(field_add(p, y, z, x) for x, y, z in zip(av, bv, rv))
    assert aligned_add_model(p, b, K, r, K, a, K, b, r, a, K)


def test_common_witnesses_may_be_legitimately_shorter_than_all_originals():
    av, bv = (0, 0, 1), (0, 0, 0, 1)
    a, b, r, N, u, v, t = model_witnesses(3, av, bv, 1, output_padding=3)
    assert 1 < len(av) and 1 < len(bv) and 1 < N
    assert aligned_add_model(3, a, len(av), b, len(bv), r, N, u, v, t, 1)


@pytest.mark.parametrize('which', ('left', 'right', 'output'))
def test_all_three_original_canonical_guards_matter_at_zero_modulus(which):
    empty, padded_zero = (27, 19), encode_beta((0,))
    a, L, b, M, r, N = empty, 0, empty, 0, empty, 0
    if which == 'left':
        a, L = padded_zero, 1
    elif which == 'right':
        b, M = padded_zero, 1
    else:
        r, N = padded_zero, 1
    assert common(a, L, b, M, empty, empty, 0)
    assert fixed_add(0, empty, empty, empty, 0) and equivalent(empty, 0, r, N)
    assert not aligned_add_model(0, a, L, b, M, r, N, empty, empty, empty, 0)


def test_empty_originals_and_witnesses_have_unrestricted_codes_even_at_modulus_zero():
    a, b, r, u, v, t = (27, 19), (31, 7), (17, 4), (0, 1), (55, 6), (13, 0)
    assert len({a, b, r, u, v, t}) == 6
    assert aligned_add_model(0, a, 0, b, 0, r, 0, u, v, t, 0)


def test_field_evaluation_impostor_is_not_an_input_or_output_equivalence():
    impostor, empty = encode_beta((1, 1, 0)), encode_beta(())
    assert all((x*x+x) % 2 == 0 for x in (0, 1))
    assert coefficient_bounds(2, impostor, 3)
    assert not equivalent(impostor, 3, empty, 0)
    assert not aligned_add_model(2, impostor, 3, empty, 0, empty, 0, empty, empty, empty, 0)
    assert not aligned_add_model(2, empty, 0, empty, 0, impostor, 3, empty, empty, empty, 0)


def test_right_zero_extension_is_not_harmless_alignment():
    a, zero = encode_beta((1,)), encode_beta(())
    wrong, correct = encode_beta((1, 0)), encode_beta((0, 1))
    z2 = encode_beta((0, 0))
    assert aligned_add_model(2, a, 1, zero, 0, a, 1, correct, z2, correct, 2)
    assert not aligned_add_model(2, a, 1, zero, 0, a, 1, wrong, z2, wrong, 2)


def test_correct_equivalences_do_not_replace_the_actual_sum_clause():
    one, zero = encode_beta((1,)), encode_beta((0,))
    assert common(one, 1, one, 1, one, one, 1)
    assert equivalent(one, 1, one, 1) and not fixed_add(2, one, one, one, 1)
    assert not aligned_add_model(2, one, 1, one, 1, one, 1, one, one, one, 1)
    assert aligned_add_model(2, one, 1, one, 1, zero, 1, one, one, zero, 1)


def test_raw_beta_codes_and_output_lengths_are_not_functionally_unique():
    a, zero, other = encode_beta((1,)), encode_beta(()), encode_beta((0, 1), 2)
    assert a != other
    assert aligned_add_model(3, a, 1, zero, 0, a, 1, a, encode_beta((0,)), a, 1)
    assert aligned_add_model(3, a, 1, zero, 0, other, 2,
                             other, encode_beta((0, 0)), other, 2)
    assert equivalent(a, 1, other, 2)
