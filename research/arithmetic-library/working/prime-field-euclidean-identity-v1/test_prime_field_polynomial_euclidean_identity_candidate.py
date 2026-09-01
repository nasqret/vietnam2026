"""Independent contracts, beta-code models, and conditional original HA.

The old division test contributes only its manually written native graph
expansions and integer model functions.  Its proof fixtures, receipts,
provider tables, and proof tests are never called.  New proof tests use the
unchanged conditional-body checker with exact current source dependencies;
they are not dependency-complete, Lean, admission, or publication claims.
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

from peano_lab.kernel.formulas import And, Exists, Forall
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING = HERE.parent
SOURCE = HERE / 'prime_field_polynomial_euclidean_identity_candidate.py'
ALIGNED_SOURCE = WORKING / 'prime-field-aligned-add-v1/prime_field_polynomial_aligned_add_candidate.py'
OLD = WORKING / 'prime-field-euclidean-v1'
PRIVATE_NAME = '_working_euclidean_identity_candidate_test'
INDEPENDENT_NAME = '_working_euclidean_identity_manual_graphs_test'
FUTURE_ALIAS = 'peano_lab.library.prime_field_polynomial_euclidean_identity_candidate'
NAMES = (
    'prime_field_polynomial_add_trim_aligned',
    'prime_field_polynomial_division_execution_aligned_identity',
)
SOURCE_PIN = (11235, '8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77')
SPECS_SHA256 = 'f992bc15fd84b7f3ba9b0f28c0219cb97a53c47c669a9563b087e7a3c535ab27'
COMMAND_COUNTS = (84, 152)
BODY_SHAPES = ((87, 47), (194, 54))
DEPENDENCIES = (
    ('prime_field_polynomial_add_bounded',
     'prime_field_polynomial_trim_output_coefficients',
     'prime_field_polynomial_equivalent_symmetric',
     'prime_field_polynomial_trim_equivalent',
     'prime_field_polynomial_power_coefficient_functional'),
    ('prime_field_polynomial_division_coefficient_identity',
     'prime_field_polynomial_add_bounded',
     'prime_field_polynomial_convolution_empty', 'lt_not_le', 'zero_le',
     'prime_field_polynomial_add_trim_aligned',
     'prime_field_polynomial_equivalent_symmetric',
     'prime_field_polynomial_zero_prefix_equivalent_empty',
     'prime_field_polynomial_power_coefficient_functional'),
)
MANUAL_INPUT_PINS = {
    'test_prime_field_polynomial_division_candidate.py':
        'c4f7555b19e88789c4a561ec5b66d1f9487f44a32b388f2beea90f9ec42eed3b',
    'test_prime_field_polynomial_convolution_triangular_candidate.py':
        'e6bf4d2a0b2b00336b8d83b4ffe5d068e34e3d5bd44e8af4b995ca2723289822',
    'prime_field_polynomial_division_candidate.py':
        'edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2',
    'prime_field_polynomial_convolution_triangular_candidate.py':
        'd53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f',
}


def protected_bindings():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))
            or name in (PRIVATE_NAME, INDEPENDENT_NAME, FUTURE_ALIAS)}


def load_private(source, name):
    """Execute actual inert source without acquiring any sys.modules entry."""
    if name in sys.modules:
        raise ValueError('private mathematical import name already has an owner')
    before = protected_bindings()
    assert source.is_file() and not source.is_symlink()
    specification = importlib.util.spec_from_file_location(name, source)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys()
    assert all(after[key] is value for key, value in before.items())
    assert name not in sys.modules
    assert module.__file__ == str(source)
    return module


candidate = load_private(SOURCE, PRIVATE_NAME)
independent = load_private(OLD / 'test_prime_field_polynomial_division_candidate.py', INDEPENDENT_NAME)

conj = independent.conj
at = independent.at
le = independent.le
coeff = independent.coeff
trim = independent.trim
product = independent.product
polynomial_add = independent.polynomial_add
execution = independent.execution
prime = independent.prime
format_contract = independent.format_contract
exact_ast = independent.exact_ast


def power_coefficient(b, c, length, power, value):
    inside = 'exists independent_identity_position. ' + conj(
        f'independent_identity_position+S ({power})=({length})',
        at(b, c, 'independent_identity_position', value))
    outside = conj(le(length, power), f'({value})=0')
    return f'({inside}) \\/ ({outside})'


def equivalent(b, c, length, d, e, other_length):
    k, a, r = ('independent_identity_' + role for role in ('power', 'left', 'right'))
    return f'forall {k} {a} {r}. (' + power_coefficient(b, c, length, k, a) + ') -> (' \
        + power_coefficient(d, e, other_length, k, r) + f') -> {a}={r}'


def common_representatives(ab, ac, L, bb, bc, M, ub, uc, vb, vc, K):
    return conj(equivalent(ab, ac, L, ub, uc, K), equivalent(bb, bc, M, vb, vc, K))


def aligned_add(p, ab, ac, L, bb, bc, M, rb, rc, N, *, grouped=True):
    ub, uc, vb, vc, tb, tc, K = ('independent_aligned_' + role
                                 for role in ('ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'K'))
    common = common_representatives(ab, ac, L, bb, bc, M, ub, uc, vb, vc, K)
    add = polynomial_add(p, ub, uc, vb, vc, tb, tc, K)
    output = equivalent(tb, tc, K, rb, rc, N)
    inner = conj(common, add, output) if grouped else conj(
        equivalent(ab, ac, L, ub, uc, K), equivalent(bb, bc, M, vb, vc, K), add, output)
    return conj(coeff(p, ab, ac, L), coeff(p, bb, bc, M), coeff(p, rb, rc, N),
                f'exists {ub} {uc} {vb} {vc} {tb} {tc} {K}. {inner}')


def contracts():
    trim_names = 'p pb pc N xb xc ub uc ab ac L t rb rc R'
    execution_names = 'p ab ac L bb bc d qb qc q rb rc R'
    return (
        (trim_names,
         (coeff('p', 'pb', 'pc', 'N'),
          equivalent('pb', 'pc', 'N', 'xb', 'xc', 'L'),
          polynomial_add('p', 'xb', 'xc', 'ub', 'uc', 'ab', 'ac', 'L'),
          trim('p', 'ub', 'uc', 'L', 't', 'rb', 'rc', 'R')),
         aligned_add('p', 'pb', 'pc', 'N', 'rb', 'rc', 'R', 'ab', 'ac', 'L')),
        (execution_names,
         (prime('p'), execution(*execution_names.split())),
         'exists pb pc N. ' + conj(
             product('p', 'qb', 'qc', 'q', 'bb', 'bc', 'S d', 'pb', 'pc', 'N'),
             aligned_add('p', 'pb', 'pc', 'N', 'rb', 'rc', 'R', 'ab', 'ac', 'L'))),
    )


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_euclidean_identity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    from peano_lab.library.prime_field_polynomial_division_candidate import make_prime_field_polynomial_division_candidate_theorems
    from peano_lab.library.prime_field_polynomial_representation_candidate import make_prime_field_polynomial_representation_candidate_theorems
    from peano_lab.library.prime_field_polynomial_trim_candidate import make_prime_field_polynomial_trim_candidate_theorems

    result = {row.name: row for row in THEOREMS}
    for factory in (make_prime_field_polynomial_candidate_theorems,
                    make_prime_field_polynomial_convolution_candidate_theorems,
                    make_prime_field_polynomial_division_candidate_theorems,
                    make_prime_field_polynomial_representation_candidate_theorems,
                    make_prime_field_polynomial_trim_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


def test_source_import_has_no_alpha_capability_or_package_alias_side_effect():
    before = protected_bindings()
    canonical = {name: value for name, value in sys.modules.items()
                 if name.startswith('peano_lab.library.')}
    fresh = load_private(SOURCE, PRIVATE_NAME)
    assert fresh is not candidate
    assert fresh.make_prime_field_polynomial_euclidean_identity_candidate_theorems(TheoremSpec) == rows()
    assert before == protected_bindings()
    assert all(sys.modules[name] is value for name, value in canonical.items())
    assert PRIVATE_NAME not in sys.modules and INDEPENDENT_NAME not in sys.modules


def test_private_loader_rejects_and_preserves_foreign_owner(monkeypatch):
    owner = object()
    monkeypatch.setitem(sys.modules, PRIVATE_NAME, owner)
    with pytest.raises(ValueError, match='already has an owner'):
        load_private(SOURCE, PRIVATE_NAME)
    assert sys.modules[PRIVATE_NAME] is owner


def test_mathematical_source_imports_only_canonical_graph_helpers():
    tree = ast.parse(SOURCE.read_text())
    modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert modules == {
        '__future__', 'typing',
        'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate',
        'peano_lab.library.prime_field_polynomial_convolution_candidate',
        'peano_lab.library.prime_field_polynomial_division_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate',
        'peano_lab.library.prime_field_polynomial_trim_candidate',
        'peano_lab.library.prime_field_tables_candidate',
    }
    assert not any(isinstance(node, (ast.Import, ast.With, ast.AsyncWith)) for node in ast.walk(tree))
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert candidate.__all__ == [
        'prime_field_polynomial_euclidean_aligned_add_relation',
        'make_prime_field_polynomial_euclidean_identity_candidate_theorems']


@pytest.mark.parametrize('name', ('_common_representatives', '_aligned_witness', '_aligned_add'))
def test_exact_literal_helper_ast_matches_fixed_grouped_alignment_builder(name):
    def find(source):
        matches = [node for node in ast.parse(source.read_text()).body
                   if isinstance(node, ast.FunctionDef) and node.name == name]
        assert len(matches) == 1
        return ast.dump(matches[0], include_attributes=False)
    assert find(SOURCE) == find(ALIGNED_SOURCE)


@pytest.mark.parametrize('name,expected', tuple(MANUAL_INPUT_PINS.items()))
def test_frozen_manual_graph_and_model_inputs_are_byte_exact(name, expected):
    path = OLD / name
    assert path.is_file() and not path.is_symlink()
    assert sha256(path.read_bytes()).hexdigest() == expected


def test_only_plain_independent_graphs_and_integer_models_are_reused():
    helpers = (independent.execution, independent.trim, independent.product,
               independent.polynomial_add, independent.coeff, independent.prime,
               independent.encode_beta, independent.beta_value,
               independent.assert_actual_beta_sum, independent.model_division)
    for helper in helpers:
        tree = ast.parse(inspect.getsource(helper))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        assert not names.intersection({'candidate', 'rows', 'provider_core', 'body_core',
                                       'replay_candidate_bodies', 'METRICS', 'receipts'})
    # Our actual body tests use their own exact canonical provider table.
    assert body_core.__module__ == __name__
    assert provider_core.__module__ == __name__


def test_exact_two_row_topology_and_real_dependency_use():
    known = set(provider_core())
    raw = SOURCE.read_bytes()
    assert (len(raw), sha256(raw).hexdigest()) == SOURCE_PIN
    assert tuple(row.name for row in rows()) == NAMES
    assert tuple(row.dependencies for row in rows()) == DEPENDENCIES
    assert tuple(len(row.script) for row in rows()) == COMMAND_COUNTS
    assert specification_digest() == SPECS_SHA256
    for row in rows():
        assert row.name not in known
        assert type(row) is TheoremSpec and type(row.script) is tuple and row.script
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= known
        for dependency in row.dependencies:
            assert any(command in ('apply ' + dependency, 'exact ' + dependency)
                       or command.startswith('specialize ' + dependency + ' ')
                       for command in row.script)
        known.add(row.name)


@pytest.mark.parametrize('index', range(2))
def test_independently_expanded_complete_contract(index):
    assert exact_ast(rows()[index].statement) == exact_ast(format_contract(*contracts()[index]))


def test_common_representatives_remains_a_grouped_subtree_not_a_flattened_clause_list():
    names = tuple('arg' + str(index) for index in range(10))
    good = candidate.prime_field_polynomial_euclidean_aligned_add_relation(
        *names, tag='grouped', variables=names)
    scope = 'forall ' + ' '.join(names) + '. '
    assert exact_ast(scope + good) != exact_ast(scope + aligned_add(*names, grouped=False))
    node = _closed_formula(scope + good)
    for _ in names:
        assert type(node) is Forall
        node = node.body
    for _ in range(3):
        assert type(node) is And
        node = node.right
    for _ in range(7):
        assert type(node) is Exists
        node = node.body
    assert type(node) is And and type(node.left) is And
    assert type(node.left.left) is Forall and type(node.left.right) is Forall
    assert type(node.right) is And and type(node.right.left) is Forall


def test_helper_has_no_prime_premise_and_principal_keeps_actual_execution():
    helper, main = contracts()
    assert len(helper[1]) == 4 and len(main[1]) == 2
    assert exact_ast(format_contract(main[0], (main[1][0],), main[2])) != exact_ast(rows()[1].statement)
    assert exact_ast(format_contract(helper[0], (prime('p'), *helper[1]), helper[2])) != exact_ast(rows()[0].statement)
    assert main[2].startswith('exists pb pc N.')
    assert 'prime_field_polynomial_division_coefficient_identity' in rows()[1].dependencies
    assert 'prime_field_polynomial_convolution_empty' in rows()[1].dependencies
    assert 'prime_field_polynomial_zero_prefix_equivalent_empty' in rows()[1].dependencies


def test_public_aligned_graph_matches_independent_native_expansion():
    names = tuple('arg' + str(index) for index in range(10))
    actual = candidate.prime_field_polynomial_euclidean_aligned_add_relation(
        *names, tag='public', variables=names)
    scope = 'forall ' + ' '.join(names) + '. '
    assert exact_ast(scope + actual) == exact_ast(scope + aligned_add(*names))


@pytest.mark.parametrize('index', range(10))
def test_every_public_argument_accepts_compound_terms_without_capture(index):
    names = tuple('arg' + str(i) for i in range(10))
    arguments = list(names)
    arguments[index] = 'S (arg0*(arg1+1))'
    actual = candidate.prime_field_polynomial_euclidean_aligned_add_relation(
        *arguments, tag='compound', variables=names)
    scope = 'forall ' + ' '.join(names) + '. '
    assert exact_ast(scope + actual) == exact_ast(scope + aligned_add(*arguments))


@pytest.mark.parametrize('fault', ('empty_context', 'list_context', 'duplicate_context',
                                  'invalid_tag', 'undeclared_term', 'nonstring_term', 'capture'))
def test_public_graph_rejects_invalid_or_capturing_inputs(fault):
    names = tuple('arg' + str(i) for i in range(10))
    arguments, context, tag = list(names), names, 'hostile'
    if fault == 'empty_context':
        context = ()
    elif fault == 'list_context':
        context = list(names)
    elif fault == 'duplicate_context':
        context = (*names, names[0])
    elif fault == 'invalid_tag':
        tag = 'x. false'
    elif fault == 'undeclared_term':
        arguments[0] = 'undeclared'
    elif fault == 'nonstring_term':
        arguments[0] = 0
    elif fault == 'capture':
        ordinary = candidate.prime_field_polynomial_euclidean_aligned_add_relation(
            *names, tag=tag, variables=names)
        binders = [name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.', ordinary)
                   for name in clause.split()]
        context = (*names, binders[0])
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_euclidean_aligned_add_relation(
            *arguments, tag=tag, variables=context)


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_original_conditional_ha_body(row):
    try:
        receipt = replay_candidate_bodies((row,), core=body_core())[0]
        assert receipt.name == row.name
        assert receipt.dependency_count == len(row.dependencies)
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
    changed = replace(rows()[index], statement=format_contract(names, premises, '0=1'))
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


REMOVED_PREMISES = tuple((index, premise) for index, (_, premises, _) in enumerate(contracts())
                         for premise in range(len(premises)))


@pytest.mark.parametrize('index,premise', REMOVED_PREMISES)
def test_original_body_does_not_certify_a_guardless_changed_contract(index, premise):
    names, premises, result = contracts()[index]
    changed = replace(rows()[index], statement=format_contract(
        names, tuple(clause for i, clause in enumerate(premises) if i != premise), result))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


def hostile_results():
    names, premises, _ = contracts()[1]
    ambient = 'exists pb pc. ' + conj(
        product('p', 'qb', 'qc', 'q', 'bb', 'bc', 'S d', 'pb', 'pc', 'L'),
        aligned_add('p', 'pb', 'pc', 'L', 'rb', 'rc', 'R', 'ab', 'ac', 'L'))
    reversed_sum = 'exists pb pc N. ' + conj(
        product('p', 'qb', 'qc', 'q', 'bb', 'bc', 'S d', 'pb', 'pc', 'N'),
        aligned_add('p', 'pb', 'pc', 'N', 'ab', 'ac', 'L', 'rb', 'rc', 'R'))
    flattened = 'exists pb pc N. ' + conj(
        product('p', 'qb', 'qc', 'q', 'bb', 'bc', 'S d', 'pb', 'pc', 'N'),
        aligned_add('p', 'pb', 'pc', 'N', 'rb', 'rc', 'R', 'ab', 'ac', 'L', grouped=False))
    return tuple((label, format_contract(names, premises, result)) for label, result in (
        ('proper_product_is_not_always_ambient_length', ambient),
        ('identity_orientation_is_A_equals_product_plus_R', reversed_sum),
        ('grouped_common_representatives_is_exact_native_syntax', flattened)))


@pytest.mark.parametrize('label,statement', hostile_results(), ids=lambda value: value if len(value) < 100 else None)
def test_original_body_does_not_certify_a_changed_product_or_identity(label, statement):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[1], statement=statement),), core=body_core())


def coded(values, salt=0):
    values = tuple(values)
    b, c = independent.encode_beta(values, salt)
    return b, c, len(values)


def decoded(poly):
    b, c, length = poly
    return tuple(independent.beta_value((b, c), i) for i in range(length))


def canonical_model(p, poly):
    return all(0 <= value < p for value in decoded(poly))


def power_model(poly, k):
    b, c, length = poly
    return independent.beta_value((b, c), length - 1 - k) if k < length else 0


def equivalent_model(left, right):
    # All larger powers have the explicit zero exterior branch, so this
    # finite integer-model comparison covers the complete formal functions.
    return all(power_model(left, k) == power_model(right, k)
               for k in range(max(left[2], right[2]) + 1))


def fixed_add_model(p, left, right, result):
    return (left[2] == right[2] == result[2]
            and all(canonical_model(p, poly) for poly in (left, right, result))
            and all((a + b) % p == r for a, b, r in zip(
                decoded(left), decoded(right), decoded(result), strict=True)))


def aligned_witness_model(p, left, right, result, U, V, T):
    return (all(canonical_model(p, poly) for poly in (left, right, result))
            and U[2] == V[2] == T[2]
            and equivalent_model(left, U) and equivalent_model(right, V)
            and fixed_add_model(p, U, V, T) and equivalent_model(T, result))


def actual_product_model(p, left, right, result):
    if not canonical_model(p, left) or not canonical_model(p, right):
        return False
    L, M, N = left[2], right[2], result[2]
    if L == 0 or M == 0:
        return N == 0
    if N != L + M - 1:
        return False
    A, B, P = decoded(left), decoded(right), decoded(result)
    for i, value in enumerate(P):
        terms = [(A[j] if j < L else 0) * (B[i - j] if i - j < M else 0)
                 for j in range(i + 1)]
        total = independent.assert_actual_beta_sum(terms)
        if not 0 <= value < p or total % p != value:
            return False
    return True


def trim_model(p, original, cut, result):
    U, R = decoded(original), decoded(result)
    return (original[2] == cut + result[2] and canonical_model(p, original)
            and U[:cut] == (0,) * cut and U[cut:] == R and (not R or R[0] != 0))


MODEL_CASES = tuple(independent.MODEL_CASES)


@pytest.mark.parametrize('p,A,B', MODEL_CASES)
def test_actual_beta_division_has_proper_product_and_grouped_aligned_witnesses(p, A, B):
    Q, ambient, residual, cut, R = independent.model_division(p, A, B)
    proper = ambient if Q else ()
    for salt in (0, 3):
        qa, bb, pp = coded(Q, salt + 1), coded(B, salt + 2), coded(proper, salt + 3)
        aa, rr = coded(A, salt + 4), coded(R, salt + 5)
        X, U, T = coded(ambient, salt + 6), coded(residual, salt + 7), coded(A, salt + 8)
        assert actual_product_model(p, qa, bb, pp)
        assert trim_model(p, U, cut, rr)
        assert equivalent_model(pp, X) and equivalent_model(rr, U)
        assert fixed_add_model(p, X, U, T)
        assert aligned_witness_model(p, pp, rr, aa, X, U, T)
        assert all(canonical_model(p, poly) for poly in (pp, rr, aa))
        assert aa[:2] != T[:2] and decoded(aa) == decoded(T)
        assert pp[2] == (len(Q) + len(B) - 1 if Q else 0)
        assert (pp[2] == len(A)) if Q else (decoded(X) == (0,) * len(A))


@pytest.mark.parametrize('p,X,U,padding', (
    (0, (), (), 0), (1, (0, 0), (0, 0), 1),
    (2, (1, 0), (0, 1), 2), (4, (0, 3), (0, 2), 0),
    (6, (0, 2, 1), (0, 0, 5), 1), (9, (0, 0, 8), (0, 3, 8), 3)))
def test_trim_add_helper_models_do_not_add_an_unneeded_prime_premise(p, X, U, padding):
    cut = next((i for i, value in enumerate(U) if value), len(U))
    trim_x = next((i for i, value in enumerate(X) if value), len(X))
    P, R = (0,) * padding + X[trim_x:], U[cut:]
    A = tuple((a + b) % p for a, b in zip(X, U, strict=True))
    pp, xx, uu, aa, rr = (coded(values, salt) for salt, values in enumerate((P, X, U, A, R)))
    assert canonical_model(p, pp) and equivalent_model(pp, xx)
    assert fixed_add_model(p, xx, uu, aa) and trim_model(p, uu, cut, rr)
    assert aligned_witness_model(p, pp, rr, aa, xx, uu, aa)


def test_nonempty_dividend_can_have_a_genuinely_empty_proper_product():
    Q, P, U, cut, R = independent.model_division(3, (1,), (1, 0, 1))
    assert (Q, P, U, cut, R) == ((), (0,), (1,), 0, (1,))
    empty, ambient = coded(Q, 1), coded(P, 2)
    assert empty[2] != ambient[2] and equivalent_model(empty, ambient)
    assert actual_product_model(3, coded(Q, 3), coded((1, 0, 1), 4), empty)
    assert not actual_product_model(3, coded(Q, 3), coded((1, 0, 1), 4), ambient)


def test_empty_input_and_zero_remainder_do_not_receive_a_spurious_degree_or_entry():
    for A, B in (((), (1,)), ((), (1, 1)), ((0, 0), (1,)), ((1, 0, 1), (1, 1))):
        Q, P, U, cut, R = independent.model_division(2, A, B)
        assert not R and cut == len(U)
        proper = P if Q else ()
        assert actual_product_model(2, coded(Q, 1), coded(B, 2), coded(proper, 3))
        assert aligned_witness_model(2, coded(proper, 3), coded((), 4), coded(A, 5),
                                     coded(P, 6), coded(U, 7), coded(A, 8))


def test_trim_is_left_padding_and_not_right_padding_in_highest_first_order():
    _, P, U, cut, R = independent.model_division(3, (1, 0), (1, 1))
    assert P == (1, 1) and U == (0, 2) and cut == 1 and R == (2,)
    assert equivalent_model(coded(R), coded((0,) * cut + R))
    assert not equivalent_model(coded(R), coded(R + (0,) * cut))
    assert not aligned_witness_model(3, coded(P), coded(R), coded((1, 0)),
                                     coded(P), coded(R + (0,) * cut), coded((1, 0)))


def test_zero_modulus_equivalence_cannot_replace_original_canonical_guards():
    empty, zero = coded((), 3), coded((0,), 7)
    assert equivalent_model(empty, zero)
    assert canonical_model(0, empty) and not canonical_model(0, zero)
    assert aligned_witness_model(0, empty, empty, empty, empty, empty, empty)
    assert not aligned_witness_model(0, zero, empty, empty, empty, empty, empty)
    assert not aligned_witness_model(0, empty, zero, empty, empty, empty, empty)
    assert not aligned_witness_model(0, empty, empty, zero, empty, empty, empty)


def test_formal_equality_is_stronger_than_evaluation_equality_over_the_field():
    polynomial, zero = (1, 1, 0), ()  # X^2+X has both F_2 values zero.
    def evaluate(values, x, p):
        result = 0
        for value in values:
            result = (result * x + value) % p
        return result
    assert all(evaluate(polynomial, x, 2) == evaluate(zero, x, 2) for x in range(2))
    assert not equivalent_model(coded(polynomial), coded(zero))


def test_unit_rescaling_is_not_formal_equivalence_or_raw_code_equality():
    first, recoded, scaled = coded((0, 1), 0), coded((1,), 3), coded((2,), 4)
    assert first[:2] != recoded[:2] and equivalent_model(first, recoded)
    assert not equivalent_model(first, scaled)
    assert 3 * 2 % 5 == 1  # A unit witness does not change the formal coefficient claim.


@pytest.mark.parametrize('attack', (
    'product_coefficient', 'product_length', 'remainder_coefficient', 'output_coefficient',
    'common_left', 'common_right', 'sum_not_actual', 'sum_not_equivalent_to_output'))
def test_actual_witness_models_reject_changed_data(attack):
    p, A, B = 3, (1, 0), (1, 1)
    Q, P, U, _, R = independent.model_division(p, A, B)
    pp, rr, aa, xx, uu, tt = [coded(values, index + 1)
                             for index, values in enumerate((P, R, A, P, U, A))]
    if attack == 'product_coefficient':
        pp = coded((1, 2))
    elif attack == 'product_length':
        pp = coded((0, *P))
    elif attack == 'remainder_coefficient':
        rr = coded((1,))
    elif attack == 'output_coefficient':
        aa = coded((1, 1))
    elif attack == 'common_left':
        xx = coded((0, 1))
    elif attack == 'common_right':
        uu = coded((2, 0))
    elif attack == 'sum_not_actual':
        tt = coded((1, 1))
    elif attack == 'sum_not_equivalent_to_output':
        pp, xx, tt = coded((1, 2)), coded((1, 2)), coded((1, 1))
    accepted = actual_product_model(p, coded(Q), coded(B), pp) and aligned_witness_model(
        p, pp, rr, aa, xx, uu, tt)
    assert not accepted


@pytest.mark.parametrize('p,A,B', (
    (0, (), (1,)), (1, (), (0,)), (4, (1,), (1,)),
    (6, (1,), (2,)), (2, (2,), (1,)), (3, (1,), (0,)),
    (3, (), ()), (3, (1, 2), (0, 1))))
def test_division_model_retains_prime_canonical_and_nonzero_divisor_requirements(p, A, B):
    with pytest.raises(ValueError):
        independent.model_division(p, A, B)


def test_test_surface_never_uses_default_full_edition_or_accepting_proof_mocks():
    tree = ast.parse(Path(__file__).read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    replays = [node for node in calls if isinstance(node.func, ast.Name)
               and node.func.id == 'replay_candidate_bodies']
    assert len(replays) == 7
    assert all(any(keyword.arg == 'core' for keyword in node.keywords) for node in replays)
    assert all(not (isinstance(node.func, ast.Attribute) and node.func.attr in (
        'body_core', 'provider_core', 'replay_candidate_bodies')) for node in calls)
    source_text = SOURCE.read_text()
    assert not re.search(r'\b(?:admit|sorry|axiom|cheat)\b', source_text, re.IGNORECASE)


def specification_digest():
    """Portable source data only, never a successful proof or admission token."""
    digest = sha256()
    for row in rows():
        data = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(data, ensure_ascii=True, separators=(',', ':')) + '\n').encode())
    return digest.hexdigest()
