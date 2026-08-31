"""Independent shift contracts, real beta models, and original HA body checks.

The direct provider table supplies exact ordinary dependency hypotheses only.
No Alpha import, dependency-complete replay, cached proof, independent Lean
claim or admission authority is involved.  Models are diagnostics, not proofs.
Only canonical production providers are imported: no working alias is made.
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
SOURCE = HERE / 'prime_field_polynomial_shift_candidate.py'
LIBRARY = ROOT / 'peano-lab/py/peano_lab/library'
SOURCE_SHA256 = '325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b'
PROVIDER_PINS = {
    'theorems.py': '05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919',
    'prime_field_arithmetic_candidate.py': 'd4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90',
    'prime_field_polynomial_candidate.py': '644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72',
    'prime_field_polynomial_convolution_candidate.py': '20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24',
    'prime_field_polynomial_representation_candidate.py': 'fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a',
    'prime_field_polynomial_convolution_triangular_candidate.py': 'd53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f',
    'prime_field_tables_candidate.py': '2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400',
    'finite_sum_theorems.py': '0d60b7a4fa21161def737fc6759b23e0679694052e95d97b419aa1ecb293c56e',
}


def edition_bindings():
    return {name: value for name, value in sys.modules.items()
            if name.startswith('peano_lab.library.editions_v')}


def load_candidate():
    before = edition_bindings()
    spec = importlib.util.spec_from_file_location('working_polynomial_shift_candidate', SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    after = edition_bindings()
    assert before.keys() == after.keys() and all(after[name] is value for name, value in before.items())
    return module


candidate = load_candidate()


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_shift_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    from peano_lab.library.prime_field_polynomial_representation_candidate import make_prime_field_polynomial_representation_candidate_theorems

    for name, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / name).read_bytes()).hexdigest() == digest
    result = {row.name: row for row in THEOREMS}
    for factory in (make_prime_field_arithmetic_candidate_theorems,
                    make_prime_field_polynomial_candidate_theorems,
                    make_prime_field_polynomial_convolution_candidate_theorems,
                    make_prime_field_polynomial_representation_candidate_theorems):
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


# Independently expanded first-order contracts.  None calls a production
# graph builder to manufacture its expected AST.
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


def Repeat(b, c, value, length):
    i = 'independent_repeat_index'
    return f'forall {i}. ({Lt(i,length)}) -> ({At(b,c,i,value)})'


def Shift(b, c, length, d, e):
    return And(Equal(b, c, d, e, length), At(d, e, length, '0'))


def Pad(b, c, length, i, a):
    return '(' + And(Lt(i, length), At(b, c, i, a)) + ') \\/ (' + And(Le(length, i), f'({a})=0') + ')'


def Mod(p, a, b):
    return f'exists independent_balance_left independent_balance_right. ({a})+({p})*independent_balance_left=({b})+({p})*independent_balance_right'


def Residue(p, value, residue):
    return And(Lt(residue, p), Mod(p, value, residue))


def Sum(b, c, length, total):
    u, v, i, a, h, n = ('independent_sum_code', 'independent_sum_scale', 'independent_sum_index',
                        'independent_summand', 'independent_partial', 'independent_next')
    step = f'exists {a} {h} {n}. ' + And(At(b, c, i, a), At(u, v, i, h),
                                        At(u, v, f'S ({i})', n), f'{n}={h}+{a}')
    return f'exists {u} {v}. ' + And(At(u, v, '0', '0'), At(u, v, length, total),
                                     f'forall {i}. ({Lt(i,length)}) -> ({step})')


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
SHIFTED = ('ab', 'ac', 'L', 'BB', 'BC', 'S M')
PRODUCT_PARAMETERS = ('p', *FACTORS, 'cb', 'cc', 'N', 'BB', 'BC', 'db', 'dc', 'K')


def independent_contracts():
    source_shift = Shift('bb', 'bc', 'M', 'BB', 'BC')
    old = Convolution('p', *FACTORS, 'cb', 'cc', 'N')
    new = Convolution('p', *SHIFTED, 'db', 'dc', 'K')
    old_term, new_term = Term(*FACTORS, 'i', 'j', 't'), Term(*SHIFTED, 'i', 'j', 't')
    old_coefficient = ConvolutionCoefficient('p', *FACTORS, 'i', 'r')
    new_coefficient = ConvolutionCoefficient('p', *SHIFTED, 'i', 'r')
    return (
        (('b', 'c', 'L'), (), 'exists d e. ' + Shift('b', 'c', 'L', 'd', 'e')),
        (('p', 'b', 'c', 'L', 'd', 'e'), (Prime('p'), Coeff('p', 'b', 'c', 'L'), Shift('b', 'c', 'L', 'd', 'e')), Coeff('p', 'd', 'e', 'S L')),
        (('b', 'c', 'L', 'd', 'e', 'f', 'g'), (Shift('b', 'c', 'L', 'd', 'e'), Shift('b', 'c', 'L', 'f', 'g')), Equal('d', 'e', 'f', 'g', 'S L')),
        (('b', 'c', 'L', 'd', 'e'), (Repeat('b', 'c', '0', 'L'), Shift('b', 'c', 'L', 'd', 'e')), Repeat('d', 'e', '0', 'S L')),
        (('b', 'c', 'L', 'd', 'e', 'i', 'a'), (Shift('b', 'c', 'L', 'd', 'e'), Pad('b', 'c', 'L', 'i', 'a')), Pad('d', 'e', 'S L', 'i', 'a')),
        (('b', 'c', 'L', 'd', 'e', 'i', 'a'), (Shift('b', 'c', 'L', 'd', 'e'), Pad('d', 'e', 'S L', 'i', 'a')), Pad('b', 'c', 'L', 'i', 'a')),
        ((*FACTORS, 'BB', 'BC', 'i', 'j', 't'), (source_shift,), And(f'({old_term}) -> ({new_term})', f'({new_term}) -> ({old_term})')),
        (('p', *FACTORS, 'BB', 'BC', 'i', 'r'), (source_shift,), And(f'({old_coefficient}) -> ({new_coefficient})', f'({new_coefficient}) -> ({old_coefficient})')),
        (('L', 'M', 'N', 'K'), (ProductLength('L', 'M', 'N'), '~(L=0)', '~(M=0)', ProductLength('L', 'S M', 'K')), 'K=S N'),
        (PRODUCT_PARAMETERS, ('~(p=0)', '~(L=0)', '~(M=0)', source_shift, old, new), And('K=S N', Shift('cb', 'cc', 'N', 'db', 'dc'))),
        (PRODUCT_PARAMETERS, ('~(p=0)', source_shift, old, new, 'L=0 \\/ M=0'), And(Repeat('cb', 'cc', '0', 'N'), Repeat('db', 'dc', '0', 'K'))),
        ((*PRODUCT_PARAMETERS, 'eb', 'ec'), ('~(p=0)', source_shift, old, new, Shift('cb', 'cc', 'N', 'eb', 'ec')), Equivalent('db', 'dc', 'K', 'eb', 'ec', 'S N')),
        (('p', *FACTORS, 'cb', 'cc', 'N', 'BB', 'BC'), (Prime('p'), source_shift, old),
         'exists K db dc eb ec. ' + And(new, Shift('cb', 'cc', 'N', 'eb', 'ec'), Equivalent('db', 'dc', 'K', 'eb', 'ec', 'S N'))),
        (('b', 'c', 'L', 'd', 'e'), (Shift('b', 'c', 'L', 'd', 'e'),), Power('d', 'e', 'S L', '0', '0')),
        (('b', 'c', 'L', 'd', 'e', 'k', 'a'), (Shift('b', 'c', 'L', 'd', 'e'), Power('b', 'c', 'L', 'k', 'a')), Power('d', 'e', 'S L', 'S k', 'a')),
    )


NAMES = (
    'prime_field_polynomial_shift_exists', 'prime_field_polynomial_shift_bounded',
    'prime_field_polynomial_shift_functional', 'prime_field_polynomial_shift_zero_prefix',
    'polynomial_zero_extended_shift_forward', 'polynomial_zero_extended_shift_reverse',
    'polynomial_diagonal_term_shift_right_iff', 'prime_field_convolution_coefficient_shift_right_iff',
    'polynomial_product_length_shift_right_nonempty', 'prime_field_polynomial_convolution_shift_right_nonempty',
    'prime_field_polynomial_convolution_shift_right_empty', 'prime_field_polynomial_convolution_shift_right_equivalent',
    'prime_field_polynomial_convolution_shift_right_exists', 'prime_field_polynomial_shift_power_zero',
    'prime_field_polynomial_shift_power_successor',
)
METRICS = ((19, 11), (51, 23), (115, 30), (35, 17), (70, 23), (91, 28), (161, 54), (110, 42),
           (98, 33), (310, 57), (154, 41), (338, 61), (116, 56), (28, 18), (89, 38))


def test_exact_source_inventory_and_topological_dependencies():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert len(rows()) == len(independent_contracts()) == 15
    assert sum(len(row.dependencies) for row in rows()) == 46
    assert sum(len(row.script) for row in rows()) == 1033
    known = set(provider_core())
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in known and row.script
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= known
        assert all(re.search(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", '\n'.join(row.script)) for name in row.dependencies)
        assert not any(command.startswith(('use ', 'admit', 'sorry')) or 'DNE' in command for command in row.script)
        known.add(row.name)


@pytest.mark.parametrize('index', range(15), ids=NAMES)
def test_independent_closed_fully_expanded_contract(index):
    same_ast(_closed_formula(rows()[index].statement), _closed_formula(contract(*independent_contracts()[index])))


def test_source_has_only_canonical_imports_and_preserves_edition_bindings():
    tree = ast.parse(SOURCE.read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.ImportFrom) and node.level == 0 for node in imports)
    assert {node.module for node in imports} == {
        '__future__', 'typing', 'peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate',
        'peano_lab.library.prime_field_polynomial_convolution_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate',
        'peano_lab.library.prime_field_tables_candidate',
    }
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    before = edition_bindings()
    repeated = load_candidate()
    assert Path(repeated.__file__) == SOURCE
    after = edition_bindings()
    assert before.keys() == after.keys() and all(after[name] is value for name, value in before.items())
    required = {node.module for node in imports if node.module.startswith('peano_lab.library.')}
    assert required <= sys.modules.keys()
    for filename in PROVIDER_PINS:
        name = 'peano_lab.library.' + filename.removesuffix('.py')
        if name in sys.modules:
            assert Path(sys.modules[name].__file__).resolve() == (LIBRARY / filename).resolve()


def test_direct_import_preserves_a_preloaded_edition_module_identity(monkeypatch):
    name = 'peano_lab.library.editions_v_shift_import_guard'
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, marker)
    before = edition_bindings()
    loaded = load_candidate()
    assert Path(loaded.__file__) == SOURCE
    assert sys.modules[name] is marker
    after = edition_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())


def test_only_graph_is_actual_prefix_and_zero_not_the_covariance_conclusion():
    parameters = ('b', 'c', 'L', 'd', 'e')
    actual = candidate.prime_field_polynomial_shift_relation(*parameters, tag='independent', variables=parameters)
    same_ast(_closed_formula('forall b c L d e. ' + actual), _closed_formula('forall b c L d e. ' + Shift(*parameters)))
    assert not any(word in actual for word in ('Prime', 'Convolution', 'Equivalent', 'Horner'))
    assert independent_contracts()[0][1] == ()
    assert independent_contracts()[8][1][1:3] == ('~(L=0)', '~(M=0)')
    assert independent_contracts()[11][1][0] == '~(p=0)'
    assert independent_contracts()[12][1][0] == Prime('p')
    assert not any(word in row.name for row in rows() for word in ('associative', 'gcd', 'bezout', 'euclidean_unique'))


def test_local_statement_novelty_against_exact_selected_dependency_types():
    # This is deliberately not the independently scheduled full-Alpha novelty gate.
    from peano_lab.library.formula_dag import FormulaArena

    table = body_core()
    selected = set(NAMES) | {dependency for row in rows() for dependency in row.dependencies}
    encoded = {name: FormulaArena().freeze(_closed_formula(table[name].statement)).to_json() for name in selected}
    for name in NAMES:
        assert all(encoded[name] != value for other, value in encoded.items() if other != name)


@pytest.mark.parametrize('index', range(15), ids=NAMES)
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


@pytest.mark.parametrize('index', range(15))
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
        0: (('raw-identity', 'exists d e. ' + And(Shift('b', 'c', 'L', 'd', 'e'), 'b=d', 'c=e')),
            ('all-zero', 'exists d e. ' + And(Shift('b', 'c', 'L', 'd', 'e'), Repeat('d', 'e', '0', 'S L')))),
        2: (('raw-identity', And('d=f', 'e=g')),
            ('extra-entry', Equal('d', 'e', 'f', 'g', 'S (S L)'))),
        4: (('copy-postprefix', At('b', 'c', 'i', 'a')),),
        5: (('copy-postprefix', At('b', 'c', 'i', 'a')),),
        8: (('same-length', 'K=N'),),
        9: (('raw-product-code', And('cb=db', 'cc=dc')),
            ('harmless-padding', Equivalent('cb', 'cc', 'N', 'db', 'dc', 'K'))),
        10: (('universal-successor-length', 'K=S N'),),
        11: (('universal-same-length', 'K=S N'), ('raw-shift-code', And('db=eb', 'dc=ec'))),
        12: (('assumed-shift-product', 'exists K db dc eb ec. ' + And(
            Convolution('p', *SHIFTED, 'db', 'dc', 'K'), 'K=S N', Shift('cb', 'cc', 'N', 'db', 'dc'))),),
        13: (('constant-one', Power('d', 'e', 'S L', '0', '1')),),
        14: (('no-power-shift', Power('d', 'e', 'S L', 'k', 'a')),),
    }
    for index, mutations in wrong.items():
        parameters, premises, _ = independent_contracts()[index]
        for label, conclusion in mutations:
            result.append((index, label, contract(parameters, premises, conclusion)))
    return tuple(result)


CHANGED = changed_contracts()


@pytest.mark.parametrize('index,label,statement', CHANGED, ids=tuple(f'{i}-{label}' for i, label, _ in CHANGED))
def test_fixed_body_rejects_altered_guards_or_stronger_claim(index, label, statement):
    # This is rejection by the exact fixed script, not a claim that every
    # omitted premise has a numerical counterexample for every modulus.
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())


ARGUMENTS = ('b', 'c', 'L', 'd', 'e')
COMPOUNDS = tuple((index, term) for index, name in enumerate(ARGUMENTS)
                  for term in (name + '+1', name + '*' + name, f'S ({name}+{name})', str(2**96 + 17)))


@pytest.mark.parametrize('index,term', COMPOUNDS)
def test_public_shift_expansion_preserves_compound_and_large_terms(index, term):
    arguments = (*ARGUMENTS[:index], term, *ARGUMENTS[index+1:])
    actual = candidate.prime_field_polynomial_shift_relation(*arguments, tag='compound', variables=ARGUMENTS)
    binder = 'forall ' + ' '.join(ARGUMENTS) + '. '
    same_ast(_closed_formula(binder + actual), _closed_formula(binder + Shift(*arguments)))


BINDERS = tuple(sorted({name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',
    candidate.prime_field_polynomial_shift_relation(*ARGUMENTS, tag='capture', variables=ARGUMENTS)) for name in clause.split()}))


@pytest.mark.parametrize('binder', BINDERS)
def test_every_generated_binder_rejects_unused_and_used_capture(binder):
    with pytest.raises(ValueError, match='captures'):
        candidate.prime_field_polynomial_shift_relation(*ARGUMENTS, tag='capture', variables=ARGUMENTS + (binder,))
    with pytest.raises(ValueError, match='captures'):
        candidate.prime_field_polynomial_shift_relation('b+' + binder, *ARGUMENTS[1:], tag='capture', variables=ARGUMENTS + (binder,))


@pytest.mark.parametrize('tag', ('', 'S', 'forall', 'exists', '0bad', 'has space', 'x.y', 'x/y', None, 1))
def test_invalid_shift_binder_tags_rejected(tag):
    with pytest.raises((TypeError, ValueError)):
        candidate.prime_field_polynomial_shift_relation(*ARGUMENTS, tag=tag, variables=ARGUMENTS)


@pytest.mark.parametrize('variables', ((), [], ['b', 'c', 'L', 'd', 'e'], ('b', 'c', 'L', 'd', 'e', 'b'),
                                     ('b', 'c', 'L', 'd', 'S'), ('b', 'c', 'L', 'd', 1)))
def test_invalid_or_duplicate_shift_context_rejected(variables):
    with pytest.raises((TypeError, ValueError)):
        candidate.prime_field_polynomial_shift_relation(*ARGUMENTS, tag='invalid', variables=variables)


@pytest.mark.parametrize('position', range(5))
@pytest.mark.parametrize('term', ('undeclared', 'forall x. x=x', 'b+(', 1, None))
def test_invalid_shift_term_in_every_argument_rejected(position, term):
    arguments = (*ARGUMENTS[:position], term, *ARGUMENTS[position+1:])
    with pytest.raises((TypeError, ValueError)):
        candidate.prime_field_polynomial_shift_relation(*arguments, tag='invalid', variables=ARGUMENTS)


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
    value = b % (1 + (index+1)*c)
    quotient, residue = divmod(b, 1 + (index+1)*c)
    assert residue == value and b == quotient*(1 + (index+1)*c) + value
    assert 0 <= value < 1 + (index+1)*c
    return value


def prefix(code, length):
    return tuple(beta(code, index) for index in range(length))


def model_shift(source, length, target):
    return prefix(source, length) == prefix(target, length) and beta(target, length) == 0


def zero_extended(code, length, index):
    return beta(code, index) if index < length else 0


def power(code, length, exponent):
    return beta(code, length - 1 - exponent) if exponent < length else 0


def equivalent(first, length, second, other_length):
    return all(power(first, length, k) == power(second, other_length, k)
               for k in range(max(length, other_length) + 2))


def actual_coefficient_witness(p, left, L, right, M, index, encoding=1):
    assert p > 0
    values = tuple(zero_extended(left, L, j) * zero_extended(right, M, index-j) for j in range(index+1))
    diagonal = encode_beta((*values, 47), encoding)
    partials = [0]
    for value in values:
        partials.append(partials[-1] + value)
    trace = encode_beta((*partials, 53), encoding+1)
    assert beta(trace, 0) == 0
    for j, value in enumerate(values):
        assert beta(diagonal, j) == value
        assert j + (index-j) == index
        assert beta(trace, j+1) == beta(trace, j) + value
    total = beta(trace, index+1)
    quotient, residue = divmod(total, p)
    assert 0 <= residue < p and total == residue + p*quotient
    return residue, diagonal, trace


def product_values(p, left, right):
    if not left or not right:
        return ()
    return tuple(sum(left[j]*right[i-j] for j in range(len(left)) if 0 <= i-j < len(right)) % p
                 for i in range(len(left)+len(right)-1))


RAW_VALUES = ((), (0,), (1,), (2,), (9,), (0, 0), (1, 0), (0, 3), (2, 5), (0, 7, 0), (4, 0, 2), (2**90+7,))


@pytest.mark.parametrize('values', RAW_VALUES)
@pytest.mark.parametrize('encoding', (2, 3))
def test_actual_beta_shift_changes_powers_but_preserves_zero_extended_array(values, encoding):
    L = len(values)
    source = encode_beta((*values, 17, 19))
    target = encode_beta((*values, 0, 23, 29), encoding)
    assert source != target and model_shift(source, L, target)
    assert beta(source, L) == 17 and beta(target, L+1) == 23
    assert power(target, L+1, 0) == 0
    for k in range(L+4):
        assert power(source, L, k) == power(target, L+1, k+1)
        assert zero_extended(source, L, k) == zero_extended(target, L+1, k)


PAIRS = (((), ()), ((), (1,)), ((1,), ()), ((1, 2, 1), ()), ((1,), (1,)),
         ((0,), (1, 1)), ((1, 0), (0,)), ((0, 1), (1, 0)), ((1, 2), (2, 1)),
         ((0, 2, 0), (1, 0)), ((1, 0, 1), (1, 1, 1)))


@pytest.mark.parametrize('p', (1, 2, 3, 4, 5, 7))
@pytest.mark.parametrize('values', PAIRS)
@pytest.mark.parametrize('encoding', (2, 3))
def test_actual_diagonal_sum_residue_and_empty_safe_product_covariance(p, values, encoding):
    left_values, right_values = (tuple(value % p for value in side) for side in values)
    L, M = len(left_values), len(right_values)
    left = encode_beta((*left_values, 31, 37))
    right = encode_beta((*right_values, 41, 43))
    shifted = encode_beta((*right_values, 0, 59, 61), encoding)
    assert model_shift(right, M, shifted)
    original_values = product_values(p, left_values, right_values)
    shifted_values = product_values(p, left_values, (*right_values, 0))
    N, K = len(original_values), len(shifted_values)
    original = encode_beta((*original_values, 67, 71))
    result = encode_beta((*shifted_values, 73, 79), encoding)
    comparison = encode_beta((*original_values, 0, 83, 89), encoding+1)
    assert model_shift(original, N, comparison)
    for i in range(max(N, K) + 2):
        old_residue, old_diagonal, old_trace = actual_coefficient_witness(p, left, L, right, M, i)
        new_residue, new_diagonal, new_trace = actual_coefficient_witness(p, left, L, shifted, M+1, i, encoding)
        assert old_residue == new_residue
        assert prefix(old_diagonal, i+1) == prefix(new_diagonal, i+1)
        assert prefix(old_trace, i+2) == prefix(new_trace, i+2)
        if i < N:
            assert beta(original, i) == old_residue
        else:
            assert old_residue == 0
        if i < K:
            assert beta(result, i) == new_residue
        else:
            assert new_residue == 0
    if L and M:
        assert K == N+1 and model_shift(original, N, result)
    elif L == 0:
        assert N == K == 0 and K != N+1
    else:
        assert M == N == 0 and K == L and prefix(result, K) == (0,)*K
    assert equivalent(result, K, comparison, N+1)
    assert beta(original, N) == 67 and beta(result, K) == 73 and beta(comparison, N+1) == 83


@pytest.mark.parametrize('fault', ('nonzero-trailing-entry', 'changed-preserved-prefix'))
@pytest.mark.parametrize('p', (2, 3, 5))
def test_missing_actual_shift_clauses_have_concrete_covariance_counterexamples(fault, p):
    left_values, right_values = (1, 1), (1,)
    wrong = (1, 1) if fault == 'nonzero-trailing-entry' else (0, 0)
    right, changed = encode_beta((*right_values, 17)), encode_beta((*wrong, 19), 2)
    assert not model_shift(right, 1, changed)
    original = product_values(p, left_values, right_values)
    wrong_product = product_values(p, left_values, wrong)
    comparison = encode_beta((*original, 0))
    assert not equivalent(encode_beta(wrong_product), len(wrong_product), comparison, len(original)+1)


def test_leading_padding_is_not_multiplication_by_x_and_codes_are_not_unique():
    source = encode_beta((1, 2, 17))
    shifted = encode_beta((1, 2, 0, 19), 2)
    leading = encode_beta((0, 1, 2, 23), 3)
    recoded = encode_beta((1, 2, 0, 29), 5)
    assert model_shift(source, 2, shifted) and model_shift(source, 2, recoded)
    assert shifted != recoded and beta(shifted, 3) != beta(recoded, 3)
    assert not model_shift(source, 2, leading)
    assert equivalent(source, 2, leading, 3)
    assert not equivalent(source, 2, shifted, 3)


def test_empty_right_factor_does_not_assert_successor_product_length():
    source = encode_beta((17, 19))
    shifted = encode_beta((0, 23), 2)
    assert model_shift(source, 0, shifted)
    actual_product = product_values(2, (1, 1, 1), (0,))
    assert actual_product == (0, 0, 0) and len(actual_product) != 1
    assert equivalent(encode_beta(actual_product), 3, encode_beta((0,)), 1)


def test_characteristic_two_uses_natural_one_not_signed_unit_code():
    assert product_values(2, (1, 1), (1, 0)) == (1, 1, 0)
    source = encode_beta((1, 1, 17))
    shifted = encode_beta((1, 1, 0, 19))
    assert model_shift(source, 2, shifted)
    assert all(value < 2 for value in prefix(shifted, 3))
    assert not all(value < 2 for value in prefix(encode_beta((2, 0)), 2))


def test_finite_field_function_agreement_does_not_replace_formal_coefficients():
    # X^2+X vanishes at both elements of F2, but it is not the zero polynomial.
    values = (1, 1, 0)
    for x in (0, 1):
        value = 0
        for coefficient in values:
            value = (value*x + coefficient) % 2
        assert value == 0
    assert not equivalent(encode_beta(values), 3, encode_beta((0,)), 1)
    actual_shift = encode_beta((*values, 0))
    assert model_shift(encode_beta(values), 3, actual_shift)
    assert not equivalent(actual_shift, 4, encode_beta((0,)), 1)
