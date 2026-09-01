"""Independent aligned-distributivity contracts and actual conditional HA.

The identity test supplies only manually expanded syntax and integer-beta
model functions, not proof fixtures or acceptance observations.  Each new
body is replayed through the unchanged conditional checker using actual
canonical dependencies and the literal working from-common constructor.
No full Alpha, dependency-complete, Lean, or admission claim is made.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import importlib.util
import inspect
import json
from pathlib import Path
import re
import sys

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import THEOREMS, TheoremSpec


HERE = Path(__file__).resolve().parent
WORKING = HERE.parent
SOURCE = HERE / 'prime_field_polynomial_aligned_distributivity_candidate.py'
MODEL_SOURCE = WORKING / 'prime-field-euclidean-identity-v1/test_prime_field_polynomial_euclidean_identity_candidate.py'
ALIGNED_SOURCE = WORKING / 'prime-field-aligned-add-v1/prime_field_polynomial_aligned_add_candidate.py'
PRIVATE_NAMES = ('_working_aligned_distributivity_candidate_test',
                 '_working_aligned_distributivity_model_test',
                 '_working_aligned_distributivity_actual_common_test')
FUTURE_ALIAS = 'peano_lab.library.prime_field_polynomial_aligned_distributivity_candidate'
SOURCE_PIN = (8518, '7d535939e24fe6d82158c485533b2ff6934f4d897b6141fde6c50b4fec9788ba')
SPECS_SHA256 = '22b9e7ed76b79f0210eee74433a965db62cc5a4b688c3ab2cf0f236b1dca5719'
COMMAND_COUNTS = (194, 195)
BODY_SHAPES = ((262, 71), (263, 71))
INPUT_PINS = (
    (MODEL_SOURCE, 'e7225749330ccd9392e584196057ab3a2547856764d25296bee775f9eb62e2c0'),
    (MODEL_SOURCE.with_name('prime_field_polynomial_euclidean_identity_candidate.py'),
     '8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77'),
    (ALIGNED_SOURCE, 'a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db'),
)
NAMES = tuple('prime_field_polynomial_aligned_convolution_' + side + '_add'
              for side in ('left', 'right'))
DEPENDENCIES = tuple((
    'prime_nonzero', 'prime_field_polynomial_' + side + '_distributive_products_exists',
    'prime_field_polynomial_aligned_add_from_common',
    'prime_field_polynomial_convolution_bounded',
    'prime_field_polynomial_convolution_equivalent_congruent_' + changing,
) for side, changing in (('left', 'right'), ('right', 'left')))
U, V, W = ('ub', 'uc', 'L'), ('vb', 'vc', 'M'), ('wb', 'wc', 'N')
D = ('db', 'dc', 'J')
P, Q, R = ('pb', 'pc', 'H'), ('qb', 'qc', 'I'), ('rb', 'rc', 'K')
PARAMETERS = ('p', *U, *V, *W, *D, *P, *Q, *R)


def protected_bindings():
    return {name: value for name, value in sys.modules.items()
            if name in (*PRIVATE_NAMES, FUTURE_ALIAS)
            or name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))}


def load_private(source, name):
    if name in sys.modules:
        raise ValueError('private source name is already owned')
    before = protected_bindings()
    assert source.is_file() and not source.is_symlink()
    specification = importlib.util.spec_from_file_location(name, source)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys()
    assert all(after[key] is value for key, value in before.items())
    assert name not in sys.modules and module.__file__ == str(source)
    return module


candidate = load_private(SOURCE, PRIVATE_NAMES[0])
independent = load_private(MODEL_SOURCE, PRIVATE_NAMES[1])
actual_common = load_private(ALIGNED_SOURCE, PRIVATE_NAMES[2])


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_aligned_distributivity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_congruence_candidate import make_prime_field_polynomial_convolution_congruence_candidate_theorems
    from peano_lab.library.prime_field_polynomial_distributivity_candidate import make_prime_field_polynomial_distributivity_candidate_theorems

    result = {row.name: row for row in THEOREMS}
    for factory in (make_prime_field_arithmetic_candidate_theorems,
                    make_prime_field_polynomial_convolution_candidate_theorems,
                    make_prime_field_polynomial_convolution_congruence_candidate_theorems,
                    make_prime_field_polynomial_distributivity_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    actual_rows = actual_common.make_prime_field_polynomial_aligned_add_candidate_theorems(TheoremSpec)
    selected = tuple(row for row in actual_rows if row.name == 'prime_field_polynomial_aligned_add_from_common')
    assert len(selected) == 1 and selected[0].dependencies == ()
    assert selected[0].name not in result
    result[selected[0].name] = selected[0]
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


def contracts():
    result = []
    for side in ('left', 'right'):
        products = tuple(independent.product('p', *(D + value if side == 'left' else value + D), *output)
                         for value, output in zip((U, V, W), (P, Q, R), strict=True))
        result.append((' '.join(PARAMETERS),
                       (independent.prime('p'), independent.aligned_add('p', *U, *V, *W), *products),
                       independent.aligned_add('p', *P, *Q, *R)))
    return tuple(result)


def specification_digest():
    digest = sha256()
    for row in rows():
        data = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(data, ensure_ascii=True, separators=(',', ':')) + '\n').encode())
    return digest.hexdigest()


def test_exact_source_and_two_row_inventory_has_only_actual_dependencies():
    raw = SOURCE.read_bytes()
    assert (len(raw), sha256(raw).hexdigest()) == SOURCE_PIN
    assert specification_digest() == SPECS_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert tuple(row.dependencies for row in rows()) == DEPENDENCIES
    assert tuple(len(row.script) for row in rows()) == COMMAND_COUNTS
    known = set(provider_core())
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in known
        assert set(row.dependencies) <= known
        assert len(row.dependencies) == len(set(row.dependencies)) == 5
        for dependency in row.dependencies:
            assert any(command == 'apply ' + dependency
                       or command.startswith('specialize ' + dependency + ' ') for command in row.script)
        known.add(row.name)


@pytest.mark.parametrize('path,expected', INPUT_PINS, ids=lambda value: value.name if isinstance(value, Path) else value)
def test_actual_source_and_plain_model_inputs_are_literal_pinned(path, expected):
    assert path.is_file() and not path.is_symlink()
    assert sha256(path.read_bytes()).hexdigest() == expected


def test_loading_sources_preserves_existing_canonical_and_foreign_module_owners():
    before = protected_bindings()
    canonical = {name: value for name, value in sys.modules.items() if name.startswith('peano_lab.library.')}
    fresh = load_private(SOURCE, PRIVATE_NAMES[0])
    assert fresh.make_prime_field_polynomial_aligned_distributivity_candidate_theorems(TheoremSpec) == rows()
    assert before == protected_bindings()
    assert all(sys.modules[name] is value for name, value in canonical.items())
    assert all(name not in sys.modules for name in PRIVATE_NAMES)


@pytest.mark.parametrize('name', PRIVATE_NAMES)
def test_private_loader_rejects_foreign_owner_without_deletion(monkeypatch, name):
    owner = object()
    monkeypatch.setitem(sys.modules, name, owner)
    with pytest.raises(ValueError, match='already owned'):
        load_private(SOURCE, name)
    assert sys.modules[name] is owner


@pytest.mark.parametrize('name', ('_common_representatives', '_aligned_witness', '_aligned_add'))
def test_grouped_definition_builder_ast_is_exactly_the_existing_definition(name):
    def syntax(path):
        nodes = [node for node in ast.parse(path.read_text()).body
                 if isinstance(node, ast.FunctionDef) and node.name == name]
        assert len(nodes) == 1
        return ast.dump(nodes[0], include_attributes=False)
    assert syntax(SOURCE) == syntax(ALIGNED_SOURCE)


def test_mathematical_source_has_no_working_import_package_alias_or_admission_call():
    tree = ast.parse(SOURCE.read_text())
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert imports == {
        '__future__', 'typing', 'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate',
        'peano_lab.library.prime_field_polynomial_convolution_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate'}
    assert not any(isinstance(node, (ast.Import, ast.With, ast.AsyncWith)) for node in ast.walk(tree))
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert candidate.__all__ == ['prime_field_polynomial_distributivity_aligned_add_relation',
                                 'make_prime_field_polynomial_aligned_distributivity_candidate_theorems']


def test_reused_model_and_syntax_functions_never_consume_body_success_data():
    for helper in (independent.aligned_add, independent.equivalent, independent.product,
                   independent.actual_product_model, independent.aligned_witness_model,
                   independent.coded, independent.decoded, independent.equivalent_model):
        names = {node.id for node in ast.walk(ast.parse(inspect.getsource(helper)))
                 if isinstance(node, ast.Name)}
        assert not names.intersection({'candidate', 'rows', 'provider_core', 'body_core',
                                       'BODY_SHAPES', 'receipt', 'replay_candidate_bodies'})
    source = ast.parse(Path(__file__).read_text())
    calls = [node for node in ast.walk(source) if isinstance(node, ast.Call)]
    replays = [node for node in calls if isinstance(node.func, ast.Name)
               and node.func.id == 'replay_candidate_bodies']
    assert len(replays) == 7
    assert all(any(keyword.arg == 'core' for keyword in call.keywords) for call in replays)
    assert all(not (isinstance(node.func, ast.Attribute) and node.func.attr in (
        'body_core', 'provider_core', 'replay_candidate_bodies')) for node in calls)


@pytest.mark.parametrize('index', range(2))
def test_independently_expanded_complete_contract(index):
    assert independent.exact_ast(rows()[index].statement) == independent.exact_ast(
        independent.format_contract(*contracts()[index]))


def test_left_and_right_orientations_are_distinct_native_contracts():
    first, second = (independent.exact_ast(row.statement) for row in rows())
    assert first != second
    assert candidate.PARAMETERS == PARAMETERS and len(PARAMETERS) == 22
    assert all(len(premises) == 5 for _, premises, _ in contracts())
    assert 'prime_field_polynomial_convolution_equivalent_congruent_right' in rows()[0].dependencies
    assert 'prime_field_polynomial_convolution_equivalent_congruent_left' in rows()[1].dependencies


@pytest.mark.parametrize('index', range(10))
def test_every_public_argument_accepts_hygienic_compound_terms(index):
    names = tuple('arg' + str(i) for i in range(10))
    args = list(names)
    args[index] = 'S (arg0*(arg1+1))'
    actual = candidate.prime_field_polynomial_distributivity_aligned_add_relation(
        *args, tag='compound', variables=names)
    scope = 'forall ' + ' '.join(names) + '. '
    assert independent.exact_ast(scope + actual) == independent.exact_ast(scope + independent.aligned_add(*args))


@pytest.mark.parametrize('fault', ('empty_context', 'list_context', 'duplicate_context',
                                  'invalid_tag', 'undeclared_term', 'nonstring_term', 'capture'))
def test_public_graph_rejects_invalid_or_capturing_contexts(fault):
    names = tuple('arg' + str(i) for i in range(10))
    args, context, tag = list(names), names, 'hostile'
    if fault == 'empty_context':
        context = ()
    elif fault == 'list_context':
        context = list(names)
    elif fault == 'duplicate_context':
        context = (*names, names[0])
    elif fault == 'invalid_tag':
        tag = 'x. false'
    elif fault == 'undeclared_term':
        args[0] = 'not_declared'
    elif fault == 'nonstring_term':
        args[0] = 1
    elif fault == 'capture':
        ordinary = candidate.prime_field_polynomial_distributivity_aligned_add_relation(
            *names, tag=tag, variables=names)
        binders = [name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.', ordinary)
                   for name in clause.split()]
        context = (*names, binders[0])
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_distributivity_aligned_add_relation(
            *args, tag=tag, variables=context)


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_original_conditional_ha_body(row):
    try:
        receipt = replay_candidate_bodies((row,), core=body_core())[0]
        assert receipt.name == row.name and receipt.dependency_count == len(row.dependencies)
        assert receipt.command_count == len(row.script)
        assert (receipt.proof_nodes, receipt.proof_depth) == BODY_SHAPES[NAMES.index(row.name)]
        assert 0 < receipt.proof_objects <= receipt.proof_nodes
        assert 0 < receipt.proof_depth <= 256
        print(receipt, flush=True)
    finally:
        gc.collect()


@pytest.mark.parametrize('index', range(2))
def test_original_checker_rejects_false_conclusion(index):
    names, premises, _ = contracts()[index]
    changed = replace(rows()[index], statement=independent.format_contract(names, premises, '0=1'))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_original_checker_rejects_missing_body(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=()),), core=body_core())


EDGES = tuple((row, dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency', EDGES,
                         ids=lambda value: value.name if hasattr(value, 'name') else value)
def test_original_checker_rejects_each_removed_dependency(row, dependency):
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row,dependency', EDGES,
                         ids=lambda value: value.name if hasattr(value, 'name') else value)
def test_original_checker_rejects_each_poisoned_dependency(row, dependency):
    core = body_core()
    core[dependency] = replace(core[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,), core=core)


@pytest.mark.parametrize('index,premise', tuple((index, premise) for index in range(2) for premise in range(5)))
def test_original_body_does_not_certify_a_guardless_changed_contract(index, premise):
    names, premises, result = contracts()[index]
    changed = replace(rows()[index], statement=independent.format_contract(
        names, tuple(clause for i, clause in enumerate(premises) if i != premise), result))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('index,attack', tuple((index, attack) for index in range(2) for attack in (
    'forced_equal_output_lengths', 'reversed_sum', 'flattened_common')))
def test_original_body_rejects_changed_length_or_sum_claim(index, attack):
    names, premises, result = contracts()[index]
    if attack == 'forced_equal_output_lengths':
        result = independent.conj(result, 'H=I', 'I=K')
    elif attack == 'reversed_sum':
        result = independent.aligned_add('p', *P, *R, *Q)
    elif attack == 'flattened_common':
        result = independent.aligned_add('p', *P, *Q, *R, grouped=False)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=independent.format_contract(
            names, premises, result)),), core=body_core())


def proper_values(p, left, right):
    if not left or not right:
        return ()
    return tuple(sum(left[j] * right[i - j] for j in range(len(left))
                     if 0 <= i - j < len(right)) % p for i in range(len(left) + len(right) - 1))


def factor_values(side, fixed, changing):
    return (fixed, changing) if side == 'left' else (changing, fixed)


def normalize(values):
    first = next((i for i, value in enumerate(values) if value), len(values))
    return values[first:]


def model_case(p, U, V, D, padding):
    length = max(len(U), len(V)) + padding
    X, Y = (0,) * (length - len(U)) + U, (0,) * (length - len(V)) + V
    T = tuple((u + v) % p for u, v in zip(X, Y, strict=True))
    W = (0,) * (padding % 3) + normalize(T)
    return U, V, W, D, X, Y, T


MODEL_CASES = tuple(dict.fromkeys(
    (p, *case, padding)
    for p in (2, 3, 5)
    for case in (
        ((), (), ()), ((), (), (1,)), ((), (1,), (1,)), ((1,), (), (1,)),
        ((), (0, 1), (1, 1)), ((0, 1), (), (1, 1)),
        ((1,), (0, 1), ()), ((1,), (0, 1), (0,)),
        ((1,), (0, 1), (1,)), ((1,), (p - 1,), (1, 0)),
        ((0, 1), (1, p - 1), (p - 1, 1)),
        ((0, 0, 1), (1, 0), (1, 0, 1)),
        ((0,), (0, 0), (p - 1, 0)), ((p - 1, 1), (1, p - 1), (1,)))
    for padding in (0, 2)))


@pytest.mark.parametrize('side', ('left', 'right'))
@pytest.mark.parametrize('p,U,V,D,padding', MODEL_CASES)
def test_actual_beta_models_construct_common_products_at_independent_lengths(side, p, U, V, D, padding):
    U, V, W, D, X, Y, T = model_case(p, U, V, D, padding)
    A, B, C = (proper_values(p, *factor_values(side, D, value)) for value in (U, V, W))
    AX, BY, CT = (proper_values(p, *factor_values(side, D, value)) for value in (X, Y, T))
    for salt in (0, 7):
        coded = independent.coded
        original = tuple(coded(value, salt + i + 1) for i, value in enumerate((U, V, W, D, A, B, C)))
        witnesses = tuple(coded(value, salt + i + 11) for i, value in enumerate((X, Y, T, AX, BY, CT)))
        u, v, w, d, a, b, c = original
        x, y, t, ax, by, ct = witnesses
        assert independent.aligned_witness_model(p, u, v, w, x, y, t)
        for value, output in ((u, a), (v, b), (w, c), (x, ax), (y, by), (t, ct)):
            factors = (d, value) if side == 'left' else (value, d)
            assert independent.actual_product_model(p, *factors, output)
        assert ax[2] == by[2] == ct[2]
        assert independent.equivalent_model(a, ax) and independent.equivalent_model(b, by)
        assert independent.fixed_add_model(p, ax, by, ct)
        assert independent.equivalent_model(ct, c)
        assert independent.aligned_witness_model(p, a, b, c, ax, by, ct)


@pytest.mark.parametrize('side', ('left', 'right'))
def test_empty_original_factor_and_positive_common_length_do_not_force_equal_product_lengths(side):
    U, V, W, D, X, Y, T = model_case(3, (), (1,), (1, 1), 2)
    P, Q, R = (proper_values(3, *factor_values(side, D, value)) for value in (U, V, W))
    PX, QX, RX = (proper_values(3, *factor_values(side, D, value)) for value in (X, Y, T))
    assert len(P) == 0 and len(Q) == 2 and len(R) == 4
    assert len(PX) == len(QX) == len(RX) == 4
    assert P == () and PX == (0, 0, 0, 0)
    assert independent.equivalent_model(independent.coded(P), independent.coded(PX))
    assert independent.aligned_witness_model(3, *(independent.coded(value) for value in (P, Q, R, PX, QX, RX)))


@pytest.mark.parametrize('side', ('left', 'right'))
@pytest.mark.parametrize('which', range(3))
def test_a_supplied_product_cannot_be_replaced_by_an_unchecked_output(side, which):
    U, V, W, D, X, Y, T = model_case(3, (1,), (0, 1), (1, 1), 0)
    originals = (U, V, W)
    products = [proper_values(3, *factor_values(side, D, value)) for value in originals]
    changed = list(products[which])
    changed[-1] = (changed[-1] + 1) % 3
    products[which] = tuple(changed)
    assert not independent.actual_product_model(
        3, *(independent.coded(value) for value in factor_values(side, D, originals[which])),
        independent.coded(products[which]))


def test_evaluation_equality_cannot_supply_the_formal_common_representative_premise():
    coded = independent.coded
    zero, nonzero = coded(()), coded((1, 1, 0))
    assert all((x * x + x) % 2 == 0 for x in range(2))
    assert not independent.equivalent_model(zero, nonzero)
    assert not independent.aligned_witness_model(2, zero, zero, zero, nonzero, nonzero, coded((0, 0, 0)))


def test_zero_modulus_examples_keep_the_canonical_guards_and_do_not_assert_prime():
    coded = independent.coded
    empty, zero = coded((), 5), coded((0,), 7)
    assert independent.aligned_witness_model(0, empty, empty, empty, empty, empty, empty)
    assert independent.actual_product_model(0, empty, empty, empty)
    assert independent.equivalent_model(empty, zero)
    assert not independent.canonical_model(0, zero)
    assert not independent.actual_product_model(0, empty, zero, empty)
    assert not independent.aligned_witness_model(0, zero, empty, empty, empty, empty, empty)
