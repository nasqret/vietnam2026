"""Independent contracts and real-HA rejection tests for signed summand factors.

The beta-table diagnostics below are finite arithmetic checks, not proofs.
The proof cases replay the unchanged dependency-curried bodies in the original
HA checker; no complete closure, admission or publication is inferred here.
"""

from dataclasses import asdict, replace
from functools import lru_cache
import gc
from hashlib import sha256
import math
from pathlib import Path
import re

import pytest

from peano_lab.library import (
    arithmetic_multiplicative_candidate as multiplicative,
    coprime_divisor_decomposition_candidate as divisor_pairs,
    dirichlet_multiplicative_entry_candidate as candidate,
)
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_dirichlet_convolution_candidate import (
    expected_at, expected_dvd, expected_entry, expected_le,
    expected_signed_multiply, expected_table,
)
from tests.test_divisor_sum_reindex_candidate import _unpair
from tests.test_signed_table_operations_candidate import (
    decode_signed, encode_signed, model_at, model_table,
)


SOURCE_PINS = {
    'dirichlet_multiplicative_entry_candidate.py':
        'd7f55b8f25e56f8b9c5bc3f6c4b83698d5f1ad770e1e4ed77c53f12a602bd897',
    'arithmetic_multiplicative_candidate.py':
        'f4374450ec543f69093b98367c90f67f09ac15daacd1df2f90961d7b6ece4a7e',
    'coprime_divisor_decomposition_candidate.py':
        'de19bb61543f5d7ab3a1d1b675c96ae4b31c7c96b58d6107904e7188973a2e1c',
}
NAMES = (
    'signed_mul_four_factor_interchange',
    'signed_mul_nonzero_factors',
    'dirichlet_convolution_entry_nonzero_support',
    'dirichlet_multiplicative_pair_factorization',
    'dirichlet_multiplicative_pair_entry',
)
# Observed counts; object sharing is recorded, not a mathematical invariant.
METRICS = ((69,69,34),(85,85,27),(63,63,30),(342,341,59),(172,172,51))


def conjunction(*clauses):
    result = clauses[-1]
    for clause in reversed(clauses[:-1]):
        result = f'({clause}) /\\ ({result})'
    return result


def expected_coprime(a,b,tag):
    d = 'independent_common_divisor_' + tag
    return (f'forall {d}. ({expected_dvd(d,a,tag+"left")}) -> '
            f'({expected_dvd(d,b,tag+"right")}) -> {d}=1')


def expected_multiplicative(N,F,tag,*,one='2'):
    a,b,x,y,z = ('independent_law_'+role+'_'+tag
                 for role in ('left','right','first','second','product'))
    law = (f'forall {a} {b} {x} {y} {z}. ~({a}=0) -> ~({b}=0) -> '
           f'({expected_le(a+"*"+b,N,tag+"bound")}) -> '
           f'({expected_coprime(a,b,tag+"coprime")}) -> '
           f'({expected_at(F,a,x,tag+"first")}) -> ({expected_at(F,b,y,tag+"second")}) -> '
           f'({expected_at(F,a+"*"+b,z,tag+"product")}) -> '
           f'({expected_signed_multiply(x,y,z,tag+"multiply")})')
    return conjunction(f'~(({N})=0)',expected_table(N,F,tag+'table'),
                       expected_at(F,'1',one,tag+'normalization'),law)


def expected_pair(m,n,k,d,e,tag):
    return conjunction(f'~(({d})=0)',f'~(({e})=0)',
                       expected_dvd(d,m,tag+'left'),expected_dvd(e,n,tag+'right'),
                       f'({k})=({d})*({e})')


def format_contract(names,premises,target):
    return 'forall '+names+'. '+' -> '.join('('+part+')' for part in (*premises,target))


def contracts():
    counter = 0
    def tagged(function):
        def build(*arguments):
            nonlocal counter
            counter += 1
            return function(*arguments,tag='independent_entry_'+str(counter))
        return build
    M,P,E,L,C,D,K = map(tagged,(expected_multiplicative,expected_signed_multiply,
                                expected_entry,expected_le,expected_coprime,
                                expected_dvd,expected_pair))
    pair_premises = (
        M('N','F'),M('N','G'),'~(m=0)','~(n=0)',L('m*n','N'),C('m','n'),
        K('m','n','d*e','d','e'),E('F','G','m','d','left'),E('F','G','n','e','right'),
    )
    pair_names = 'N F G m n d e left right total'
    return {
        NAMES[0]: ('a b c d ab cd ac bd out',
                   (P('a','b','ab'),P('c','d','cd'),P('a','c','ac'),P('b','d','bd'),
                    P('ac','bd','out')),P('ab','cd','out')),
        NAMES[1]: ('a b z',(P('a','b','z'),'~(z=0)'),conjunction('~(a=0)','~(b=0)')),
        NAMES[2]: ('F G n d z',(E('F','G','n','d','z'),'~(z=0)'),
                   conjunction('~(d=0)',D('d','n'))),
        NAMES[3]: (pair_names,(*pair_premises,E('F','G','m*n','d*e','total')),
                   P('left','right','total')),
        NAMES[4]: (pair_names,(*pair_premises,P('left','right','total')),
                   E('F','G','m*n','d*e','total')),
    }


def exact_ast(statement):
    return FormulaArena().freeze(_closed_formula(statement)).to_json()


def instantiate(template,replacements,tag):
    # Independently rename every bound identifier before inserting any term.
    bound = tuple(dict.fromkeys(name for clause in re.findall(
        r'\b(?:forall|exists)\s+([^.]*)\.',template) for name in clause.split()))
    renamed = {name:'entry_model_'+tag+'_'+str(index) for index,name in enumerate(bound)}
    pattern = r"\b[A-Za-z_][A-Za-z_0-9']*"
    template = re.sub(pattern,lambda match:renamed.get(match.group(),match.group()),template)
    return re.sub(pattern,lambda match:'('+replacements[match.group()]+')'
                  if match.group() in replacements else match.group(),template)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_dirichlet_multiplicative_entry_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def predecessors():
    from peano_lab.library import editions_v31
    result = editions_v31.ALPHA_CHECKED_SPECS
    assert len(result) == len({row.name for row in result}) == 3796
    return result


@lru_cache(maxsize=1)
def support_rows():
    return (divisor_pairs.make_coprime_divisor_decomposition_candidate_theorems(TheoremSpec)
            + multiplicative.make_arithmetic_multiplicative_candidate_theorems(TheoremSpec))


@lru_cache(maxsize=1)
def core():
    return {row.name:row for row in (*predecessors(),*support_rows(),*rows())}


def test_exact_unchanged_source_and_declared_topology():
    for name,pin in SOURCE_PINS.items():
        assert sha256(Path(candidate.__file__).with_name(name).read_bytes()).hexdigest() == pin
    assert tuple(row.name for row in rows()) == NAMES
    assert tuple(len(row.dependencies) for row in rows()) == (4,3,0,8,4)
    assert sum(metric[0] for metric in METRICS) == 731
    available = {row.name for row in (*predecessors(),*support_rows())}
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        assert all(re.search(r"(?<![\w'])"+re.escape(name)+r"(?![\w'])",'\n'.join(row.script))
                   for name in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        available.add(row.name)
    assert candidate.__all__ == ['make_dirichlet_multiplicative_entry_candidate_theorems']


def test_exact_formula_dag_novelty_against_3796_predecessors_and_local_support():
    by_hash = {}
    for row in rows():
        encoded = exact_ast(row.statement)
        key = sha256(encoded.encode()).digest()
        assert all(encoded != previous for _,previous in by_hash.get(key,()))
        by_hash.setdefault(key,[]).append((row.name,encoded))
    for row in (*predecessors(),*support_rows()):
        encoded = exact_ast(row.statement)
        # Hashes select buckets only; full canonical FormulaDAG decides equality.
        assert all(encoded != current for _,current in by_hash.get(sha256(encoded.encode()).digest(),())), row.name


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_complete_independently_expanded_statement(row):
    assert exact_ast(row.statement) == exact_ast(format_contract(*contracts()[row.name]))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
@pytest.mark.parametrize('mode',('compound','zero','repeated','large'))
def test_independent_compound_and_capture_free_contract_instances(row,mode):
    arguments = contracts()[row.name][0].split()
    replacements = {name:('ambient_left+ambient_right' if index%2 else 'ambient_left*ambient_right')
                    for index,name in enumerate(arguments)}
    if mode == 'zero': replacements = dict.fromkeys(arguments,'0')
    if mode == 'repeated': replacements = dict.fromkeys(arguments,'ambient_left')
    if mode == 'large': replacements = dict.fromkeys(arguments,'79228162514264337593543950335')
    close = 'forall ambient_left ambient_right unused. '
    actual = instantiate(row.statement.split('.',1)[1],replacements,'actual')
    expected = instantiate(format_contract(*contracts()[row.name]).split('.',1)[1],replacements,'expected')
    assert exact_ast(close+actual) == exact_ast(close+expected)


@pytest.mark.parametrize('name',NAMES[3:])
def test_complete_contract_keeps_positive_one_not_an_arbitrary_signed_unit(name):
    names,premises,target = contracts()[name]
    changed = (expected_multiplicative('N','F','negative_unit_contract',one='1'),*premises[1:])
    actual = next(row for row in rows() if row.name == name)
    assert exact_ast(actual.statement) == exact_ast(format_contract(names,premises,target))
    assert exact_ast(actual.statement) != exact_ast(format_contract(names,changed,target))
    # Factorization uses the product laws, not normalization itself.  Therefore
    # changing an unused normalization premise is an AST contract mismatch,
    # not a claim that the original body must reject that altered proposition.


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_ha_body_exact_metrics(row,record_property):
    try:
        report = replay_candidate_bodies((row,),core=core())[0]
        expected = METRICS[rows().index(row)]
        assert (report.proof_nodes,report.proof_depth) == (expected[0],expected[2])
        assert 0 < report.proof_objects <= report.proof_nodes
        assert report.dependency_count == len(row.dependencies)
        record_property('actual_original_ha_body',asdict(report))
    except CandidateBodyError as error:
        pytest.fail(str(error)[:700],pytrace=False)
    finally:
        gc.collect()


def rejected(row,table):
    gc.collect()
    try:
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,),core=table)
    finally:
        gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_rejected(row):
    rejected(replace(row,statement='0=1'),core())


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_empty_body_rejected(row):
    rejected(replace(row,script=()),core())


EDGES = tuple((row,name) for row in rows() for name in row.dependencies)


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
@pytest.mark.parametrize('change',('drop','poison'))
def test_every_declared_dependency_required(row,dependency,change):
    table = dict(core())
    if change == 'drop':
        row = replace(row,dependencies=tuple(name for name in row.dependencies if name != dependency))
    else:
        table[dependency] = replace(table[dependency],statement='0=1')
    rejected(row,table)


def changed_contracts():
    original,result = contracts(),[]
    for name,positions in ((NAMES[1],(1,)),(NAMES[2],(1,)),
                           (NAMES[3],tuple(range(10))),(NAMES[4],(9,))):
        names,premises,target = original[name]
        for index in positions:
            changed = tuple(clause for i,clause in enumerate(premises) if i != index)
            result.append((name+'_remove_contract_field_'+str(index),name,format_contract(names,changed,target)))
    names,premises,_ = original[NAMES[0]]
    result.append(('signed_codes_are_not_natural_products',NAMES[0],format_contract(names,premises,'out=ab*cd')))
    names,premises,_ = original[NAMES[3]]
    result.append(('pair_result_is_not_code_multiplication',NAMES[3],format_contract(names,premises,'total=left*right')))
    return tuple(result)


@pytest.mark.parametrize('label,name,statement',
                         tuple(pytest.param(*case,id=case[0]) for case in changed_contracts()))
def test_changed_contract_is_not_proved_by_original_body(label,name,statement):
    original = next(row for row in rows() if row.name == name)
    rejected(replace(original,statement=statement),core())


def actual_values(table):
    code,(pb,pc,nb,nc) = table
    first,second = _unpair(code)
    assert _unpair(first) == (pb,pc) and _unpair(second) == (nb,nc)
    return lambda index:decode_signed(model_at(table,index))


def entry_value(F,G,n,d):
    if d == 0 or n%d:
        return 0
    return encode_signed(actual_values(F)(d)*actual_values(G)(n//d))


def model_multiplicative(N,F):
    value = actual_values(F)
    return (N != 0 and model_at(F,1) == 2 and
            all(value(a*b) == value(a)*value(b)
                for a in range(1,N+1) for b in range(1,N+1)
                if a*b <= N and math.gcd(a,b) == 1))


def arithmetic_value(kind,n):
    if kind == 'one': return 1
    if kind == 'identity': return n
    if kind == 'delta': return int(n == 1)
    if kind == 'character3': return 0 if n%3 == 0 else (1 if n%3 == 1 else -1)
    raise AssertionError(kind)


@pytest.mark.parametrize('factors',((1,1,1,1),(-1,-1,1,1),(-1,1,-1,1),
                                    (0,-2,3,4),(-3,2,-5,7),(2,3,-1,-4)))
def test_canonical_signed_four_factor_interchange_diagnostic(factors):
    a,b,c,d = map(encode_signed,factors)
    product = lambda first,second:encode_signed(decode_signed(first)*decode_signed(second))
    ab,cd,ac,bd = product(a,b),product(c,d),product(a,c),product(b,d)
    out = product(ac,bd)
    assert out == product(ab,cd) == encode_signed(math.prod(factors))
    if factors == (1,1,1,1):
        assert a == b == c == d == out == 2
        assert out != ab*cd


def test_nonzero_signed_factor_guard_diagnostic():
    for a in range(11):
        for b in range(11):
            z = encode_signed(decode_signed(a)*decode_signed(b))
            if z != 0:
                assert a != 0 and b != 0
    assert encode_signed(0*7) == 0
    assert encode_signed(-1) == 1 and encode_signed(1) == 2


@pytest.mark.parametrize('n',(0,1,4,6))
def test_actual_beta_nonzero_support_requires_positive_real_divisor(n):
    F = model_table((17,*(i-3 for i in range(1,9))),offset=3,endpoint=991)
    G = model_table((-19,*(4-2*i for i in range(1,9))),offset=7,endpoint=-997)
    for d in range(9):
        z = entry_value(F,G,n,d)
        if z != 0:
            assert d > 0 and n%d == 0 and n == d*(n//d)
        if d == 0 or n%d:
            assert z == 0
    # The theorem intentionally does not require n>0: positive d may divide 0.
    if n == 0:
        assert entry_value(F,G,n,1) != 0 and n == 1*0


@pytest.mark.parametrize('m,n,left_kind,right_kind',(
    (1,1,'one','one'),(1,6,'identity','character3'),(2,3,'identity','one'),
    (3,4,'character3','identity'),(4,5,'delta','character3'),(2,5,'character3','one'),
))
def test_actual_beta_pair_entries_have_real_cofactors_bounds_and_signed_products(m,n,left_kind,right_kind):
    N = m*n
    left = tuple(arithmetic_value(left_kind,i) for i in range(1,N+1))
    right = tuple(arithmetic_value(right_kind,i) for i in range(1,N+1))
    F = model_table((-23,*left),offset=3,endpoint=991)
    G = model_table((29,*right),offset=7,endpoint=-997)
    F_again = model_table((31,*left),offset=11,endpoint=-993)
    G_again = model_table((-37,*right),offset=13,endpoint=995)
    assert math.gcd(m,n) == 1 and model_multiplicative(N,F) and model_multiplicative(N,G)
    assert F[0] != F_again[0] and G[0] != G_again[0]
    for d in range(1,m+1):
        for e in range(1,n+1):
            if m%d or n%e:
                continue
            u,v = m//d,n//e
            assert u > 0 and v > 0 and m == d*u and n == e*v
            assert N == (d*e)*(u*v) and d*e <= N and u*v <= N
            assert all(math.gcd(a,b) == 1 for a,b in ((d,e),(d,v),(u,e),(u,v)))
            first,second,target = entry_value(F,G,m,d),entry_value(F,G,n,e),entry_value(F,G,N,d*e)
            assert target == encode_signed(decode_signed(first)*decode_signed(second))
            assert target == entry_value(F_again,G_again,N,d*e)
            assert first == entry_value(F_again,G_again,m,d)
            assert second == entry_value(F_again,G_again,n,e)
            if target != 0:
                assert first != 0 and second != 0


def test_pair_factorization_cannot_use_an_outside_prefix_product():
    F = model_table((17,1,2,3,4,5,7),offset=5,endpoint=0)
    G = model_table((-19,1,1,1,1,1,1),offset=7,endpoint=0)
    assert model_multiplicative(5,F) and model_multiplicative(5,G)
    assert math.gcd(2,3) == 1 and 2*3 > 5
    first,second = entry_value(F,G,2,2),entry_value(F,G,3,3)
    target = entry_value(F,G,6,6)
    assert target != encode_signed(decode_signed(first)*decode_signed(second))
    assert not model_multiplicative(6,F)


def test_pair_factorization_does_not_assume_complete_multiplicativity():
    F = model_table((17,1,2,3,3),offset=3,endpoint=0)
    G = model_table((-19,1,1,1,1),offset=5,endpoint=0)
    assert model_multiplicative(4,F) and model_multiplicative(4,G)
    assert math.gcd(2,2) != 1
    first = entry_value(F,G,2,2)
    assert entry_value(F,G,4,4) != encode_signed(decode_signed(first)**2)


def test_normalization_is_positive_one_and_zero_support_is_not_a_divisor_claim():
    F = model_table((17,-1,0,0),offset=5,endpoint=0)
    G = model_table((-19,1,1,1),offset=7,endpoint=0)
    assert model_at(F,1) == 1 and model_at(G,1) == 2
    assert not model_multiplicative(1,F) and model_multiplicative(1,G)
    assert entry_value(F,G,3,0) == entry_value(F,G,3,2) == 0
    assert 3%2 != 0
    assert not model_multiplicative(0,G)


def test_entry_source_remains_unchanged_after_diagnostics():
    for name,pin in SOURCE_PINS.items():
        assert sha256(Path(candidate.__file__).with_name(name).read_bytes()).hexdigest() == pin
