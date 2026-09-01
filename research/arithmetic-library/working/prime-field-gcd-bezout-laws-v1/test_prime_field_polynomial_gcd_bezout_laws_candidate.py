"""Independent expanded contracts, actual beta witnesses and conditional HA.

Only pinned manual graph/integer helpers are reused from the earlier tests.
No prior proof observation is read. Native tests use the unchanged checker
and the exact frozen95 source/provider table, never an Alpha edition.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, replace
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

from peano_lab.library.prime_field_arithmetic_candidate import _public
from peano_lab.library.theorems import TheoremSpec


HERE = Path(__file__).resolve().parent
WORKING = HERE.parent
SOURCE = HERE / 'prime_field_polynomial_gcd_bezout_laws_candidate.py'
MODELS = WORKING / 'prime-field-euclidean-transport-v1/test_prime_field_polynomial_transport_models.py'
PRIOR = WORKING / 'prime-field-euclidean-closure-v1/working_euclidean_closure_support.py'
SOURCE_PIN = (15300, '76b90226e5e29fdde3d9bb49accccf8d9b4c0cc17a4de406af253e999102533c')
INPUT_PINS = (
    (MODELS, '0c814915ee8b8f6ecc8ffb945699cd4888fa4c4cf86e6b4cb077063407f5cfab'),
    (PRIOR, '2cf88350845af863835de0c96670a8f1aa96a102ef806e9a0c11b19cc8b6fb5d'),
    (WORKING / 'prime-field-aligned-add-v1/prime_field_polynomial_aligned_add_candidate.py',
     'a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db'),
    (WORKING / 'prime-field-euclidean-transport-v1/prime_field_polynomial_euclidean_transport_candidate.py',
     '9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30'),
    (WORKING / 'prime-field-bezout-backward-v1/prime_field_polynomial_bezout_backward_candidate.py',
     'c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702'),
)
PRIVATE = ('_gcd_bezout_laws_candidate_test', '_gcd_bezout_laws_manual_models',
           '_gcd_bezout_laws_frozen95_controller')
FUTURE = 'peano_lab.library.prime_field_polynomial_gcd_bezout_laws_candidate'
NAMES = tuple('prime_field_polynomial_' + stem for stem in (
    'aligned_add_empty_right', 'bezout_from_right_multiple',
    'bezout_equivalent_transport', 'bezout_common_right_divisor'))
DEPENDENCIES = (
    ('beta_repeat_exists', 'prime_field_polynomial_aligned_add_from_common',
     'matrix_rank_bounded_prefix_empty', 'prime_field_polynomial_power_coefficient_functional',
     'prime_field_polynomial_equivalent_symmetric',
     'prime_field_polynomial_zero_prefix_equivalent_empty', 'prime_field_polynomial_add_zero_right'),
    ('prime_field_polynomial_convolution_bounded', 'prime_field_polynomial_convolution_empty',
     'matrix_rank_bounded_prefix_empty', 'prime_field_polynomial_aligned_add_transport',
     'prime_field_polynomial_power_coefficient_functional',
     'prime_field_polynomial_aligned_add_empty_right'),
    ('polynomial_product_length_exists', 'prime_field_polynomial_convolution_at_length_exists',
     'prime_field_polynomial_convolution_bounded', 'prime_field_polynomial_aligned_add_transport',
     'prime_field_polynomial_equivalent_symmetric',
     'prime_field_polynomial_convolution_equivalent_congruent_right'),
    ('prime_field_polynomial_right_divides_aligned_add',
     'prime_field_polynomial_right_divides_left_product'),
)


def input_pins():
    result = {}
    for path, digest in INPUT_PINS:
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        assert sha256(raw).hexdigest() == digest
        result[str(path)] = (len(raw), digest)
    raw = SOURCE.read_bytes()
    assert not SOURCE.is_symlink() and (len(raw), sha256(raw).hexdigest()) == SOURCE_PIN
    result[str(SOURCE)] = SOURCE_PIN
    return result


def protected_bindings():
    return {name: value for name, value in sys.modules.items()
            if name in (*PRIVATE, FUTURE)
            or name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))}


def load_private(path, name, *, controller=False):
    if name in sys.modules:
        raise ValueError('the private source name already has an owner')
    before, owners = input_pins(), protected_bindings()
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    if controller:
        sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
    finally:
        if controller:
            if sys.modules.get(name) is not module:
                raise ValueError('a foreign replacement must be preserved')
            del sys.modules[name]
    assert input_pins() == before and name not in sys.modules
    after = protected_bindings()
    assert owners.keys() == after.keys()
    assert all(after[key] is value for key, value in owners.items())
    return module


candidate = load_private(SOURCE, PRIVATE[0])
models = load_private(MODELS, PRIVATE[1])
manual = models.independent
A, B, G, U, V, D = tuple((letter + 'b', letter + 'c', letter.upper())
                         for letter in ('a', 'b', 'g', 'u', 'v', 'd'))
ZERO = ('0', '0', '0')


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_gcd_bezout_laws_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def body_core():
    prior = load_private(PRIOR, PRIVATE[2], controller=True)
    old = prior.load_candidate_state()
    assert len(old.rows) == 95
    assert old.specs_sha256 == 'b2b381d67064401d3325b464396c6d156b5fc27a56639f3909dacaa60ae83994'
    core = prior.canonical_provider_table()
    for row in (*old.rows, *rows()):
        assert row.name not in core
        core[row.name] = row
    assert all(dependency in core for row in rows() for dependency in row.dependencies)
    assert not any(name.startswith('peano_lab.library.editions') for name in sys.modules)
    assert all(name not in sys.modules for name in PRIVATE)
    return core


def contracts():
    AA, BB, GG = ('ab2', 'ac2', 'A2'), ('bb2', 'bc2', 'B2'), ('gb2', 'gc2', 'G2')
    return (
        (('p', *A), (manual.prime('p'), manual.coeff('p', *A)),
         manual.aligned_add('p', *A, *ZERO, *A)),
        (('p', *A, *B, *G), (manual.prime('p'), manual.coeff('p', *B),
                            models.right_divides('p', *A, *G)),
         'exists ub uc U. ' + models.bezout('p', *A, *B, *G, *U, *ZERO)),
        (('p', *A, *B, *G, *U, *V, *AA, *BB, *GG),
         ('~(p=0)', manual.coeff('p', *AA), manual.coeff('p', *BB), manual.coeff('p', *GG),
          manual.equivalent(*A, *AA), manual.equivalent(*B, *BB), manual.equivalent(*G, *GG),
          models.bezout('p', *A, *B, *G, *U, *V)),
         models.bezout('p', *AA, *BB, *GG, *U, *V)),
        (('p', *D, *A, *B, *G, *U, *V),
         (manual.prime('p'), models.common_divisor('p', *D, *A, *B),
          models.bezout('p', *A, *B, *G, *U, *V)),
         models.right_divides('p', *D, *G)),
    )


@pytest.fixture(autouse=True)
def preserve_actual_inputs_and_module_owners():
    before, owners = input_pins(), protected_bindings()
    yield
    assert input_pins() == before
    after = protected_bindings()
    assert after.keys() == owners.keys()
    assert all(after[key] is value for key, value in owners.items())


@pytest.mark.parametrize('index', range(4))
def test_complete_contract_matches_independent_expansion(index):
    parameters, premises, result = contracts()[index]
    expected = models.contract(parameters, premises, result)
    assert manual.exact_ast(rows()[index].statement) == manual.exact_ast(expected)


def test_inventory_has_only_exact_old95_dependencies_and_no_commutativity():
    assert tuple(row.name for row in rows()) == NAMES
    assert tuple(row.dependencies for row in rows()) == DEPENDENCIES
    assert len(set(NAMES)) == 4
    assert all(type(row) is TheoremSpec and row.script for row in rows())
    assert all('commutative' not in name for row in rows() for name in row.dependencies)
    core = body_core()
    assert all(core[row.name] == row for row in rows())


def test_source_import_has_no_alpha_or_mathematical_package_alias():
    before = protected_bindings()
    assert load_private(SOURCE, PRIVATE[0]).make_prime_field_polynomial_gcd_bezout_laws_candidate_theorems(TheoremSpec) == rows()
    assert protected_bindings() == before
    assert all(name not in sys.modules for name in (*PRIVATE, FUTURE))
    tree = ast.parse(SOURCE.read_text())
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert all(name in ('__future__', 'typing') or name.startswith('peano_lab.library.') for name in imports)
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))


@pytest.mark.parametrize('name,controller', ((PRIVATE[0], False), (PRIVATE[2], True)))
def test_private_loader_rejects_foreign_owners(monkeypatch, name, controller):
    owner = object()
    monkeypatch.setitem(sys.modules, name, owner)
    with pytest.raises(ValueError, match='already has an owner'):
        load_private(PRIOR if controller else SOURCE, name, controller=controller)
    assert sys.modules[name] is owner


GRAPHS = ((candidate._aligned_add, manual.aligned_add, 10),
          (candidate._right_divides, models.right_divides, 7),
          (candidate._common_divisor, models.common_divisor, 10),
          (candidate._bezout, models.bezout, 16))


@pytest.mark.parametrize('builder,expected,arity', GRAPHS, ids=lambda x: getattr(x, '__name__', str(x)))
def test_existing_conservative_graphs_have_exact_manual_ast(builder, expected, arity):
    parameters = tuple('a' + str(i) for i in range(arity))
    scoped = 'forall ' + ' '.join(parameters) + '. '
    actual = _public(builder, parameters, tag='old_graph', variables=parameters)
    assert manual.exact_ast(scoped + actual) == manual.exact_ast(scoped + expected(*parameters))


@pytest.mark.parametrize('builder,expected,arity,index',
                         tuple((*entry, index) for entry in GRAPHS for index in range(entry[2])),
                         ids=lambda x: getattr(x, '__name__', str(x)))
def test_graph_arguments_accept_compounds_without_capture(builder, expected, arity, index):
    parameters = tuple('a' + str(i) for i in range(arity))
    arguments = list(parameters)
    arguments[index] = 'S (a0*(a1+1))'
    actual = _public(builder, tuple(arguments), tag='compound', variables=parameters)
    scoped = 'forall ' + ' '.join(parameters) + '. '
    assert manual.exact_ast(scoped + actual) == manual.exact_ast(scoped + expected(*arguments))


@pytest.mark.parametrize('builder,expected,arity', GRAPHS, ids=lambda x: getattr(x, '__name__', str(x)))
@pytest.mark.parametrize('fault', ('duplicate_context', 'undeclared_term', 'invalid_tag', 'capture'))
def test_graph_validation_rejects_capture_or_invalid_context(builder, expected, arity, fault):
    parameters = tuple('a' + str(i) for i in range(arity))
    arguments, context, tag = list(parameters), parameters, 'hostile'
    if fault == 'duplicate_context':
        context = (*parameters, parameters[0])
    elif fault == 'undeclared_term':
        arguments[0] = 'undeclared'
    elif fault == 'invalid_tag':
        tag = 'bad. tag'
    else:
        raw = _public(builder, parameters, tag=tag, variables=parameters)
        binder = re.findall(r'\b(?:forall|exists)\s+([^.]*)\.', raw)[0].split()[0]
        context = (*parameters, binder)
    with pytest.raises(ValueError):
        _public(builder, tuple(arguments), tag=tag, variables=context)


def test_models_use_actual_beta_graphs_not_candidate_or_proof_outputs():
    for helper in (models.right_divides, models.bezout, models.common_divisor,
                   manual.actual_product_model, manual.aligned_witness_model,
                   models.divides_model, models.bezout_model):
        names = {node.id for node in ast.walk(ast.parse(inspect.getsource(helper))) if isinstance(node, ast.Name)}
        assert not names.intersection({'candidate', 'rows', 'body_core', 'replay_candidate_bodies', 'receipt'})
    assert models.pin_inputs()


@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('values', ((), (0,), (1,), (0, 1), (1, 0, 1)))
def test_empty_right_sum_constructs_actual_leading_zero_representative(p, values):
    a = manual.coded(values, 3)
    empty = manual.coded((), 7)
    zero = manual.coded((0,) * len(values), 11)
    same = manual.coded(values, 13)
    assert manual.equivalent_model(empty, zero)
    assert manual.aligned_witness_model(p, a, empty, same, a, zero, same)


TERMINAL_CASES = tuple((p, A, U, B) for p in (2, 3, 5)
                       for A, U in (((), (1,)), ((0,), (1, 0)), ((1,), ()),
                                    ((0, 1), (1, 1)), ((1, 0), (p - 1,)))
                       for B in ((), (0, 0), (1, 0, 1)))


@pytest.mark.parametrize('p,A,U,B', TERMINAL_CASES)
def test_terminal_actual_quotient_and_empty_coefficient_build_bezout(p, A, U, B):
    P = models.proper_product(p, U, A)
    G = (0, 0) + models.normalize(P)
    assert models.divides_model(p, A, G, U, P, 17)
    assert models.proper_product(p, (), B) == ()
    assert models.bezout_model(p, A, B, G, U, (), P, (), 29)
    # Empty products remain genuinely length zero even for a long B.
    assert manual.actual_product_model(p, manual.coded((), 1), manual.coded(B, 2), manual.coded((), 9))
    assert not manual.actual_product_model(p, manual.coded((), 1), manual.coded(B, 2), manual.coded((0,), 9))


TRANSPORT_CASES = tuple((p, A, B, U, V, pad) for p in (2, 3, 4, 5)
                        for A, B, U, V in (((), (1,), (1,), (1,)),
                                           ((0,), (), (1, 0), ()),
                                           ((1,), (0, 1), (1, 1), (p - 1,)),
                                           ((1, 0), (1, 1), (), (1,)))
                        for pad in (0, 1, 3))


@pytest.mark.parametrize('p,A,B,U,V,pad', TRANSPORT_CASES)
def test_transport_builds_two_real_new_products_at_independent_lengths(p, A, B, U, V, pad):
    P, Q = models.proper_product(p, U, A), models.proper_product(p, V, B)
    G = models.poly_sum(p, P, Q, padding=1)
    AA, BB, GG = (0,) * pad + A, (0,) * (pad + 1) + B, (0,) * (pad + 2) + G
    PP, QQ = models.proper_product(p, U, AA), models.proper_product(p, V, BB)
    assert models.bezout_model(p, A, B, G, U, V, P, Q, 31)
    for old, new in ((A, AA), (B, BB), (G, GG), (P, PP), (Q, QQ)):
        assert manual.equivalent_model(manual.coded(old, 37), manual.coded(new, 41))
    assert models.bezout_model(p, AA, BB, GG, U, V, PP, QQ, 43)
    assert PP == models.proper_product(p, U, AA) and QQ == models.proper_product(p, V, BB)


GREATEST_CASES = tuple((p, D, S, T, U, V) for p in (2, 3, 5)
                       for D in ((), (0,), (1,), (1, 1), (0, 1))
                       for S, T, U, V in (((), (), (), ()),
                                          ((1,), (), (1, 0), (1,)),
                                          ((0, 1), (1, 1), (p - 1,), (1, 0)),
                                          ((1, 0), (p - 1, 1), (1, 1), (p - 1,))))


@pytest.mark.parametrize('p,D,S,T,U,V', GREATEST_CASES)
def test_common_divisor_witness_composes_in_left_coefficient_order(p, D, S, T, U, V):
    A, B = models.proper_product(p, S, D), models.proper_product(p, T, D)
    P, Q = models.proper_product(p, U, A), models.proper_product(p, V, B)
    G = models.poly_sum(p, P, Q, padding=1)
    quotient = models.poly_sum(p, models.proper_product(p, U, S), models.proper_product(p, V, T), padding=2)
    product = models.proper_product(p, quotient, D)
    assert models.divides_model(p, D, A, S, A, 47)
    assert models.divides_model(p, D, B, T, B, 53)
    assert models.bezout_model(p, A, B, G, U, V, P, Q, 59)
    assert models.divides_model(p, D, G, quotient, product, 61)


@pytest.mark.parametrize('attack', ('wrong_left_product', 'wrong_right_product', 'wrong_result',
                                  'wrong_quotient', 'trailing_zero_input', 'noncanonical_result'))
def test_actual_models_reject_false_products_recodings_and_quotients(attack):
    p, A, B, U, V = 5, (1, 0), (1,), (2,), (1, 1)
    P, Q = models.proper_product(p, U, A), models.proper_product(p, V, B)
    G = models.poly_sum(p, P, Q)
    assert models.bezout_model(p, A, B, G, U, V, P, Q)
    if attack == 'wrong_left_product':
        P = (*P[:-1], (P[-1] + 1) % p)
    elif attack == 'wrong_right_product':
        Q = (*Q[:-1], (Q[-1] + 1) % p)
    elif attack == 'wrong_result':
        G = (*G[:-1], (G[-1] + 1) % p)
    elif attack == 'wrong_quotient':
        U = (3,)
    elif attack == 'trailing_zero_input':
        B = (*B, 0)
    else:
        G = (*G[:-1], G[-1] + p)
    assert not models.bezout_model(p, A, B, G, U, V, P, Q)


@pytest.mark.parametrize('p', (2, 3, 5))
def test_evaluation_impostor_cannot_replace_formal_zero_result(p):
    impostor = (1,) + (0,) * (p - 2) + (p - 1, 0)
    assert all((pow(x, p, p) - x) % p == 0 for x in range(p))
    assert not manual.equivalent_model(manual.coded(impostor, 67), manual.coded((), 71))
    assert models.bezout_model(p, (1,), (), (), (), (), (), ())
    assert not models.bezout_model(p, (1,), (), impostor, (), (), (), ())


def test_bezout_greatestness_does_not_assert_common_divisor_or_normalization():
    # X= X*1 + 0*0 is Bezout data, but X does not divide the input 1.
    assert models.bezout_model(5, (1,), (), (1, 0), (1, 0), (), (1, 0), ())
    parameters, premises, result = contracts()[3]
    assert result == models.right_divides('p', *D, *G)
    assert models.common_divisor('p', *G, *A, *B) not in premises


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_native_original_conditional_body(row):
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    try:
        receipt = replay_candidate_bodies((row,), core=body_core())[0]
        assert receipt.name == row.name and receipt.command_count == len(row.script)
        assert receipt.dependency_count == len(row.dependencies)
        assert 0 < receipt.proof_objects <= receipt.proof_nodes and 0 < receipt.proof_depth <= 256
        print('GCD_BEZOUT_LAWS_BODY=' + json.dumps(asdict(receipt), sort_keys=True), flush=True)
    finally:
        gc.collect()


@pytest.mark.parametrize('index', range(4))
def test_native_rejects_false_conclusion(index):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    parameters, premises, _ = contracts()[index]
    changed = replace(rows()[index], statement=models.contract(parameters, premises, '0=1'))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_native_rejects_missing_body(row):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=()),), core=body_core())


EDGES = tuple((row, dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency', EDGES,
                         ids=lambda value: value.name if hasattr(value, 'name') else value)
def test_native_rejects_each_removed_dependency(row, dependency):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row,dependency', EDGES,
                         ids=lambda value: value.name if hasattr(value, 'name') else value)
def test_native_rejects_each_poisoned_dependency(row, dependency):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    core = dict(body_core())
    core[dependency] = replace(core[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,), core=core)


PREMISES = tuple((index, premise) for index, (_, clauses, _) in enumerate(contracts())
                 for premise in range(len(clauses)))


@pytest.mark.parametrize('index,premise', PREMISES)
def test_native_rejects_removing_an_actual_contract_premise(index, premise):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    parameters, clauses, result = contracts()[index]
    statement = models.contract(parameters, tuple(clause for i, clause in enumerate(clauses) if i != premise), result)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())
