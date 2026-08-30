"""Independent arithmetic contracts and hostile original-HA body checks.

Finite numerical examples diagnose guard mistakes only.  The positive proof
tests check dependency-curried ordinary HA bodies, not complete closures.
"""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import math
import re

import pytest

from peano_lab.library import coprime_divisor_decomposition_candidate as candidate
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import TheoremSpec, _closed_formula


@lru_cache(maxsize=1)
def rows():
    return candidate.make_coprime_divisor_decomposition_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    from peano_lab.library import editions_v31
    actual = editions_v31.ALPHA_CHECKED_SPECS
    assert len(actual) == len({row.name for row in actual}) == 3796
    return {row.name: row for row in actual}


def _conj(*clauses):
    return clauses[0] if len(clauses) == 1 else f"(({clauses[0]}) /\\ ({_conj(*clauses[1:])}))"


def expected_dvd(d, n, tag):
    q = 'model_quotient_' + tag
    return f'exists {q}. ({n})=({d})*{q}'


def expected_le(a, b, tag):
    gap = 'model_bound_' + tag
    return f'exists {gap}. {gap}+({a})=({b})'


def expected_coprime(a, b, tag):
    d = 'model_common_divisor_' + tag
    return (f'forall {d}. ({expected_dvd(d,a,tag+"left")}) -> '
            f'({expected_dvd(d,b,tag+"right")}) -> {d}=1')


def expected_gcd(g, a, b, tag):
    d = 'model_gcd_divisor_' + tag
    greatest = (f'forall {d}. ({expected_dvd(d,a,tag+"commonleft")}) -> '
                f'({expected_dvd(d,b,tag+"commonright")}) -> '
                f'({expected_dvd(d,g,tag+"greatest")})')
    return _conj(_conj(expected_dvd(g,a,tag+'left'), expected_dvd(g,b,tag+'right')), greatest)


def expected_pair(m, n, d, a, b, tag):
    return _conj(f'~(({a})=0)', f'~(({b})=0)',
                 expected_dvd(a,m,tag+'left'), expected_dvd(b,n,tag+'right'),
                 f'({d})=({a})*({b})')


def expected_bounds(m, n, a, b, tag):
    return _conj(expected_le(a,m,tag+'left'), expected_le(b,n,tag+'right'),
                 expected_coprime(a,b,tag+'coprime'))


def expected_cofactors(m, n, d, a, b, u, v, tag):
    return _conj(f'({m})=({a})*({u})', f'({n})=({b})*({v})',
                 f'~(({u})=0)', f'~(({v})=0)',
                 expected_le(u,m,tag+'leftbound'), expected_le(v,n,tag+'rightbound'),
                 expected_coprime(a,b,tag+'ab'), expected_coprime(a,v,tag+'av'),
                 expected_coprime(u,b,tag+'ub'), expected_coprime(u,v,tag+'uv'),
                 f'({m})*({n})=({d})*(({u})*({v}))')


NAMES = (
    'coprime_divisor_gcd_product',
    'coprime_divisor_factor_pair_coordinates',
    'coprime_divisor_factor_pair_unique',
    'coprime_divisor_factor_pair_exists',
    'coprime_divisor_factor_pair_bounds',
    'coprime_divisor_factor_pair_exists_unique',
    'coprime_divisor_factor_pair_cofactors',
    'divisor_factor_pair_quotient_product',
)
METRICS = ((51,51,29), (109,109,27), (71,71,24), (105,105,31),
           (94,94,41), (60,60,31), (186,186,39), (91,91,30))


def contract_data():
    counter = 0
    def tagged(function):
        def build(*args):
            nonlocal counter
            counter += 1
            return function(*args, tag='independent_'+str(counter))
        return build
    D,L,C,G,P,B,K = map(tagged,(expected_dvd,expected_le,expected_coprime,expected_gcd,
                               expected_pair,expected_bounds,expected_cofactors))
    return {
        NAMES[0]: ('m n d a b', ('~(d=0)',C('m','n'),D('d','m*n'),G('a','m','d'),G('b','n','d')),
                   'd=a*b'),
        NAMES[1]: ('m n d a b', (C('m','n'),P('m','n','d','a','b')),
                   _conj(G('a','m','d'),G('b','n','d'))),
        NAMES[2]: ('m n d a b c e', (C('m','n'),P('m','n','d','a','b'),P('m','n','d','c','e')),
                   '(a=c) /\\ (b=e)'),
        NAMES[3]: ('m n d', ('~(d=0)',C('m','n'),D('d','m*n')),
                   'exists a b. '+P('m','n','d','a','b')),
        NAMES[4]: ('m n d a b', ('~(m=0)','~(n=0)',C('m','n'),P('m','n','d','a','b')),
                   B('m','n','a','b')),
        NAMES[5]: ('m n d', ('~(m=0)','~(n=0)','~(d=0)',C('m','n'),D('d','m*n')),
                   'exists a b. '+_conj(P('m','n','d','a','b'),B('m','n','a','b'),
                       'forall c e. ('+P('m','n','d','c','e')+') -> ((a=c) /\\ (b=e))')),
        NAMES[6]: ('m n d a b', ('~(m=0)','~(n=0)',C('m','n'),P('m','n','d','a','b')),
                   'exists u v. '+K('m','n','d','a','b','u','v')),
        NAMES[7]: ('m n d a b u v q', (P('m','n','d','a','b'),'m=a*u','n=b*v','m*n=d*q'),
                   'q=u*v'),
    }


def format_contract(names, premises, result):
    return 'forall '+names+'. '+' -> '.join('('+part+')' for part in (*premises,result))


def exact_ast(source):
    return FormulaArena().freeze(_closed_formula(source)).to_json()


def instantiate(template, replacements, tag):
    # Independent capture-avoiding textual instantiation, checked by the parser.
    binders = tuple(dict.fromkeys(name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',template)
                                 for name in clause.split()))
    renames = {name:'model_'+tag+'_'+str(index) for index,name in enumerate(binders)}
    pattern = r"\b[A-Za-z_][A-Za-z_0-9']*"
    renamed = re.sub(pattern, lambda match:renames.get(match.group(),match.group()), template)
    return re.sub(pattern, lambda match:'('+replacements[match.group()]+')'
                  if match.group() in replacements else match.group(), renamed)


def test_exact_inventory_and_topological_ordinary_dependencies():
    assert tuple(row.name for row in rows()) == NAMES
    assert sum(len(row.dependencies) for row in rows()) == 31
    assert sum(len(row.script) for row in rows()) == 472
    assert sum(nodes for nodes,_,_ in METRICS) == 767
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(set(row.dependencies)) == len(row.dependencies)
        for dependency in row.dependencies:
            assert any(re.search(r'\b'+re.escape(dependency)+r'\b',command) for command in row.script)
        assert not any(command.startswith(('use ','admit','sorry','ring','DNE')) for command in row.script)
        available.add(row.name)
    assert candidate.__all__ == ['divisor_factor_pair_relation', 'make_coprime_divisor_decomposition_candidate_theorems']


def test_exact_ast_novelty_against_all_3796_and_new_peers():
    by_digest = {}
    for row in rows():
        encoded = exact_ast(row.statement)
        fingerprint = sha256(encoded.encode()).digest()
        assert all(encoded != other for _,other in by_digest.get(fingerprint,()))
        by_digest.setdefault(fingerprint,[]).append((row.name,encoded))
    assert len(core()) == 3796
    for row in core().values():
        encoded = exact_ast(row.statement)
        fingerprint = sha256(encoded.encode()).digest()
        assert all(encoded != other for _,other in by_digest.get(fingerprint,())), row.name
    # Hashes only select comparison buckets; canonical DAG bytes decide equality.


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_complete_independent_theorem_ast(row):
    assert exact_ast(row.statement) == exact_ast(format_contract(*contract_data()[row.name]))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
@pytest.mark.parametrize('mode',('compound','zero','repeat','large'))
def test_contextual_theorem_contracts(row,mode):
    names,_,_ = contract_data()[row.name]
    replacements = {name:('left+right' if i%2 else 'left*right') for i,name in enumerate(names.split())}
    if mode == 'zero': replacements = dict.fromkeys(replacements,'0')
    if mode == 'repeat': replacements = dict.fromkeys(replacements,'left')
    if mode == 'large': replacements = dict.fromkeys(replacements,'79228162514264337593543950335')
    actual = row.statement.split('.',1)[1]
    expected = format_contract(*contract_data()[row.name]).split('.',1)[1]
    assert exact_ast('forall left right unused. '+instantiate(actual,replacements,'actual')) == exact_ast(
        'forall left right unused. '+instantiate(expected,replacements,'expected'))


@pytest.mark.parametrize('mode',('identifiers','compound','zero','repeat','large'))
def test_public_graph_has_exact_witnessed_pair_ast(mode):
    names = ('m','n','d','a','b')
    values = names
    if mode == 'compound': values = ('m+1','n*n','a*b','S a','b+1')
    if mode == 'zero': values = ('0',)*5
    if mode == 'repeat': values = ('a',)*5
    if mode == 'large': values = ('79228162514264337593543950335',*names[1:])
    actual = candidate.divisor_factor_pair_relation(*values,tag='surface',variables=(*names,'unused'))
    expected = expected_pair(*values,tag='model_surface')
    assert exact_ast('forall '+' '.join((*names,'unused'))+'. '+actual) == exact_ast(
        'forall '+' '.join((*names,'unused'))+'. '+expected)


PUBLIC_SAMPLE = candidate.divisor_factor_pair_relation('m','n','d','a','b',tag='capture',variables=('m','n','d','a','b'))
GENERATED_BINDERS = tuple(name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',PUBLIC_SAMPLE)
                          for name in clause.split())


@pytest.mark.parametrize('binder',GENERATED_BINDERS)
def test_every_generated_binder_collision_is_rejected_even_if_unused(binder):
    with pytest.raises(ValueError):
        candidate.divisor_factor_pair_relation('m','n','d','a','b',tag='capture',
                                               variables=('m','n','d','a','b',binder))


@pytest.mark.parametrize('variables',((),['m','n','d','a','b'],('m','m','n','d','a','b'),('m','n','d','a'),('m','n','d','a','b','x y')))
def test_invalid_or_incomplete_public_context_rejected(variables):
    with pytest.raises(ValueError):
        candidate.divisor_factor_pair_relation('m','n','d','a','b',tag='surface',variables=variables)


@pytest.mark.parametrize('tag',('', 'has space', 'bad;intro', '0', 'a.b'))
def test_malformed_public_tag_rejected(tag):
    with pytest.raises(ValueError):
        candidate.divisor_factor_pair_relation('m','n','d','a','b',tag=tag,variables=('m','n','d','a','b'))


@pytest.mark.parametrize('term',('unknown','m +','m -> n','exists x. x=0'))
def test_malformed_or_unbound_public_term_rejected(term):
    with pytest.raises(ValueError):
        candidate.divisor_factor_pair_relation(term,'n','d','a','b',tag='surface',variables=('m','n','d','a','b'))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_actual_original_ha_body(row):
    try:
        receipt = replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert (receipt.proof_nodes,receipt.proof_objects,receipt.proof_depth) == METRICS[rows().index(row)]
        assert receipt.dependency_count == len(row.dependencies)
    finally:
        gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_absent_body_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,script=()),),core=core()|{r.name:r for r in rows()})


DEPENDENCIES = tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_every_dropped_dependency_rejected(row,dependency):
    altered = replace(row,dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_every_poisoned_dependency_rejected(row,dependency):
    table = core()|{r.name:r for r in rows()}
    table[dependency] = replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


def hostile_contracts():
    data = contract_data()
    result = []
    def remove(index,position,label):
        name = NAMES[index]
        names,premises,target = data[name]
        result.append((label,name,format_contract(names,tuple(p for i,p in enumerate(premises) if i != position),target)))
    for index,position,label in (
            (0,0,'gcd_product_requires_positive_divisor'),
            (0,1,'gcd_product_requires_coprime_inputs'),
            (0,2,'gcd_product_requires_actual_divisibility'),
            (0,3,'gcd_product_requires_actual_left_gcd'),
            (0,4,'gcd_product_requires_actual_right_gcd'),
            (1,0,'coordinate_recovery_requires_coprimality'),
            (2,0,'unique_pair_requires_coprimality'),
            (3,0,'positive_pair_does_not_exist_for_zero'),
            (3,2,'actual_divisor_required_for_pair_exists'),
            (4,0,'left_bound_requires_positive_left_input'),
            (4,1,'right_bound_requires_positive_right_input'),
            (6,0,'positive_left_cofactor_requires_positive_input'),
            (6,1,'positive_right_cofactor_requires_positive_input'),
            (7,1,'quotient_product_requires_left_equation'),
            (7,2,'quotient_product_requires_right_equation'),
            (7,3,'quotient_product_requires_actual_quotient')):
        remove(index,position,label)
    names,premises,_ = data[NAMES[7]]
    result.append(('quotient_is_product_not_sum',NAMES[7],format_contract(names,premises,'q=u+v')))
    return tuple(result)


@pytest.mark.parametrize('label,name,statement',hostile_contracts(),ids=lambda value:value)
def test_hostile_domain_or_equation_contract_rejected(label,name,statement):
    row = next(row for row in rows() if row.name == name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core()|{r.name:r for r in rows()})


def pair_model(m,n,d,a,b):
    return a > 0 and b > 0 and m%a == 0 and n%b == 0 and d == a*b


@pytest.mark.parametrize('m',range(1,21))
def test_exhaustive_small_positive_divisor_pairs_and_cofactors(m):
    for n in range(1,21):
        if math.gcd(m,n) != 1:
            continue
        for d in range(1,m*n+1):
            pairs = [(a,b) for a in range(1,m+1) if m%a == 0
                     for b in range(1,n+1) if n%b == 0 and d == a*b]
            if (m*n)%d:
                assert not pairs
                continue
            a,b = math.gcd(m,d),math.gcd(n,d)
            assert pairs == [(a,b)] and pair_model(m,n,d,a,b)
            u,v = m//a,n//b
            assert 0 < u <= m and 0 < v <= n
            assert m == a*u and n == b*v and m*n == d*(u*v)
            assert all(math.gcd(x,y) == 1 for x,y in ((a,b),(a,v),(u,b),(u,v)))
            assert (m*n)//d == u*v


def test_numerical_guards_and_no_same_input_coprimality_overclaim():
    assert 0 != math.gcd(2,0)*math.gcd(3,0)  # positive divisor guard
    assert 2 != math.gcd(2,2)*math.gcd(2,2)  # coprimality guard
    assert 5 != math.gcd(2,5)*math.gcd(3,5)  # actual divisibility guard
    assert pair_model(2,2,2,1,2) and pair_model(2,2,2,2,1)
    assert pair_model(0,1,2,2,1) and not 2 <= 0 and 0//2 == 0
    assert pair_model(1,0,2,1,2) and not 2 <= 0 and 0//2 == 0
    # Cofactors of one input can share a factor.  Only cross-input pairs are coprime.
    assert pair_model(4,3,2,2,1) and math.gcd(2,4//2) == 2
    assert pair_model(3,4,2,1,2) and math.gcd(2,4//2) == 2
    assert pair_model(4,9,6,2,3) and (4*9)//6 == (4//2)*(9//3) != (4//2)+(9//3)


def test_zero_inputs_are_not_silently_claimed_to_have_positive_cofactors_or_bounds():
    # The unbounded pair existence/uniqueness graph legitimately permits (0,1).
    for d in range(1,20):
        assert pair_model(0,1,d,d,1)
        assert pair_model(1,0,d,1,d)
    # Its stronger finite bounds/cofactor theorem explicitly excludes these inputs.
    for index in (4,5,6):
        premises = contract_data()[NAMES[index]][1]
        assert '~(m=0)' in premises and '~(n=0)' in premises


def test_unit_and_full_product_divisors_have_the_expected_coordinates():
    for m,n in ((1,1),(1,7),(8,1),(8,9),(25,14)):
        assert pair_model(m,n,1,1,1)
        assert pair_model(m,n,m*n,m,n)
        assert (math.gcd(m,1),math.gcd(n,1)) == (1,1)
        assert (math.gcd(m,m*n),math.gcd(n,m*n)) == (m,n)
