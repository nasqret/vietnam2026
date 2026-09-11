"""Independent exact contracts and real beta-tuple cardinality fixtures.

Native tests are conditional HA diagnostics, not closed proofs or admission.
Run them only after the root coordinator grants the bounded heavy slot.
"""
from dataclasses import replace
from functools import lru_cache
import importlib
import importlib.util
from itertools import product
from math import factorial, gcd
from pathlib import Path
import sys

import pytest

from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


SOURCE = Path(__file__).with_name('jordan_totient_candidate.py')
loader = importlib.util.spec_from_file_location('_independent_jordan_source', SOURCE)
candidate = importlib.util.module_from_spec(loader)
loader.loader.exec_module(candidate)


@lru_cache(None)
def rows():
    return candidate.make_jordan_totient_candidate_theorems(TheoremSpec)


def And(*xs):
    return xs[0] if len(xs)==1 else '(('+xs[0]+') /\\ ('+And(*xs[1:])+'))'


def Lt(a,b): return f'exists zz_gap. zz_gap+S ({a})=({b})'
def Dvd(d,n): return f'exists zz_factor. ({n})=({d})*zz_factor'
def Cop(a,b): return f'forall zz_divisor. ({Dvd("zz_divisor",a)}) -> ({Dvd("zz_divisor",b)}) -> zz_divisor=1'
def Mod(n,a,b): return f'exists zz_l zz_r. ({a})+({n})*zz_l=({b})+({n})*zz_r'
def At(b,c,i,v):
    modulus=f'S ((S ({i}))*({c}))'
    return f'((exists zz_h. zz_h+S ({v})={modulus}) /\\ exists zz_q. ({b})=zz_q*{modulus}+({v}))'


def Bounded(b,c,k,n):
    return f'forall zz_i. ({Lt("zz_i",k)}) -> exists zz_a. '+And(At(b,c,'zz_i','zz_a'),Lt('zz_a',n))


def Equal(b,c,d,e,k):
    return f'forall zz_i zz_a zz_z. ({Lt("zz_i",k)}) -> ({At(b,c,"zz_i","zz_a")}) -> ({At(d,e,"zz_i","zz_z")}) -> zz_a=zz_z'


def AllDvd(q,b,c,k):
    return f'forall zz_i zz_a. ({Lt("zz_i",k)}) -> ({At(b,c,"zz_i","zz_a")}) -> ({Dvd(q,"zz_a")})'


def Primitive(n,b,c,k):
    return f'forall zz_d. ({Dvd("zz_d",n)}) -> ({AllDvd("zz_d",b,c,k)}) -> zz_d=1'


def DivisorTest(n,b,c,k,d):
    return f'({Dvd(d,n)}) -> ({AllDvd(d,b,c,k)}) -> ({d})=1'


def PrimitiveUpTo(n,b,c,k,L):
    return f'forall zz_div. ({Lt("zz_div",L)}) -> ({DivisorTest(n,b,c,k,"zz_div")})'


def PointMod(n,b,c,d,e,k):
    return f'forall zz_i zz_a zz_z. ({Lt("zz_i",k)}) -> ({At(b,c,"zz_i","zz_a")}) -> ({At(d,e,"zz_i","zz_z")}) -> ({Mod(n,"zz_a","zz_z")})'


def Enum(k,n,B,C,D,E,j):
    def Entry(i,b,c):return And(At(B,C,i,b),At(D,E,i,c))
    sound=f'forall zz_idx. ({Lt("zz_idx",j)}) -> exists zz_b zz_c. '+And(Entry('zz_idx','zz_b','zz_c'),Bounded('zz_b','zz_c',k,n),Primitive(n,'zz_b','zz_c',k))
    complete=f'forall zz_b zz_c. ({Bounded("zz_b","zz_c",k,n)}) -> ({Primitive(n,"zz_b","zz_c",k)}) -> exists zz_idx zz_dcode zz_escale. '+And(Lt('zz_idx',j),Entry('zz_idx','zz_dcode','zz_escale'),Equal('zz_b','zz_c','zz_dcode','zz_escale',k))
    distinct=f'forall zz_idx zz_other zz_b zz_c zz_dcode zz_escale. ({Lt("zz_idx",j)}) -> ({Lt("zz_other",j)}) -> ({Entry("zz_idx","zz_b","zz_c")}) -> ({Entry("zz_other","zz_dcode","zz_escale")}) -> ({Equal("zz_b","zz_c","zz_dcode","zz_escale",k)}) -> zz_idx=zz_other'
    return And(sound,complete,distinct)


def Jordan(k,n,j):
    return And(f'~(({k})=0)',f'~(({n})=0)',f'exists zz_B zz_C zz_D zz_E. {Enum(k,n,"zz_B","zz_C","zz_D","zz_E",j)}')


def Contract(vs,premises,target):
    return 'forall '+vs+'. '+''.join('('+p+') -> ' for p in premises)+target


def contracts():
    return (
        Contract('b c k',[],Equal('b','c','b','c','k')),
        Contract('b c d e k',[Equal('b','c','d','e','k')],Equal('d','e','b','c','k')),
        Contract('b c d e f g k',[Equal('b','c','d','e','k'),Equal('d','e','f','g','k')],Equal('b','c','f','g','k')),
        Contract('q b c d e k',[Equal('b','c','d','e','k'),AllDvd('q','b','c','k')],AllDvd('q','d','e','k')),
        Contract('n b c d e k',[Equal('b','c','d','e','k'),Primitive('n','b','c','k')],Primitive('n','d','e','k')),
        Contract('n m b c k',[Dvd('n','m'),Primitive('m','b','c','k')],Primitive('n','b','c','k')),
        Contract('q r b c k',[Dvd('q','r'),AllDvd('r','b','c','k')],AllDvd('q','b','c','k')),
        Contract('b c k',[],Primitive('1','b','c','k')),
        Contract('n j',[],'~('+Jordan('0','n','j')+')'),
        Contract('k j',[],'~('+Jordan('k','0','j')+')'),
        Contract('a b B C k',['~(a=0)','~(b=0)',Cop('a','b'),Primitive('a','B','C','k'),Primitive('b','B','C','k')],Primitive('a*b','B','C','k')),
        Contract('a b B C k',[Primitive('a*b','B','C','k')],And(Primitive('a','B','C','k'),Primitive('b','B','C','k'))),
        Contract('n d a z',[Dvd('d','n'),Dvd('d','a'),Mod('n','a','z')],Dvd('d','z')),
        Contract('n b c d e k',[PointMod('n','b','c','d','e','k')],PointMod('n','d','e','b','c','k')),
        Contract('n b c d e k',[PointMod('n','b','c','d','e','k'),Primitive('n','b','c','k')],Primitive('n','d','e','k')),
        Contract('d b c',[],AllDvd('d','b','c','0')),
        Contract('d b c k a',[AllDvd('d','b','c','k'),At('b','c','k','a'),Dvd('d','a')],AllDvd('d','b','c','S k')),
        Contract('d b c k',[],f'({AllDvd("d","b","c","k")}) \\/ ~({AllDvd("d","b","c","k")})'),
        Contract('n b c k d',[],f'({DivisorTest("n","b","c","k","d")}) \\/ ~({DivisorTest("n","b","c","k","d")})'),
        Contract('n b c k L',[],f'({PrimitiveUpTo("n","b","c","k","L")}) \\/ ~({PrimitiveUpTo("n","b","c","k","L")})'),
        Contract('n b c k',['~(n=0)'],f'({Primitive("n","b","c","k")}) \\/ ~({Primitive("n","b","c","k")})'),
    )


@pytest.mark.parametrize('index',range(21))
def test_independent_complete_contract(index):
    assert _closed_formula(rows()[index].statement)==_closed_formula(contracts()[index])


def test_exact_requested_target_and_no_claimed_final_row():
    target=Contract('k a b',[And('~(k=0)','~(a=0)','~(b=0)',Cop('a','b'))],
                    'exists u v w. '+And(Jordan('k','a','u'),Jordan('k','b','v'),Jordan('k','a*b','w'),'w=u*v'))
    assert _closed_formula(candidate.multiplicativity_contract())==_closed_formula(target)
    assert not any('multiplicative' in row.name for row in rows())


@pytest.mark.parametrize('tag',['independent','renamed','another_tag'])
def test_conservative_definition_alpha_renaming(tag):
    assert _closed_formula('forall k n j. '+candidate.jordan_totient_relation('k','n','j',tag=tag))==_closed_formula('forall k n j. '+Jordan('k','n','j'))


@pytest.mark.parametrize('bad',['jt_index_a','fs_h_a','ff_code','a b','S n','n+1','forall'])
def test_public_capture_and_nonidentifier_rejection(bad):
    with pytest.raises(ValueError):candidate.jordan_totient_relation(bad,'n','j',tag='a')


def test_no_alpha_or_source_module_alias():
    assert not any(name.startswith('peano_lab.library.editions') for name in sys.modules)
    assert '_independent_jordan_source' not in sys.modules


def encode(values, factor=1):
    """Independent constructive CRT beta encoding of a concrete tuple."""
    values=tuple(values)
    scale=factor*factorial(len(values))*(max(values,default=0)+1)
    code,modulus=0,1
    for i,value in enumerate(values):
        m=1+(i+1)*scale
        assert 0<=value<m and gcd(modulus,m)==1
        step=((value-code)*pow(modulus,-1,m))%m
        code+=modulus*step;modulus*=m
    assert tuple(decode(code,scale,i) for i in range(len(values)))==values
    return code,scale


def decode(code,scale,i):return code%(1+(i+1)*scale)
def decoded(code,scale,k):return tuple(decode(code,scale,i) for i in range(k))


def primitive(n,values):
    assert n>0
    return all(d==1 for d in range(1,n+1) if n%d==0 and all(x%d==0 for x in values))


def universe(n,k):return [xs for xs in product(range(n),repeat=k) if primitive(n,xs)]


def encode_enumeration(tuples,factor=1):
    pairs=[encode(xs,factor) for xs in tuples]
    return (*encode([b for b,c in pairs]),*encode([c for b,c in pairs]))


def actual_enumeration(k,n,j,witness):
    if k==0 or n==0:return False
    B,C,D,E=witness
    values=[decoded(decode(B,C,i),decode(D,E,i),k) for i in range(j)]
    return (all(all(v<n for v in xs) and primitive(n,xs) for xs in values)
            and len(set(values))==j and set(values)==set(universe(n,k)))


@pytest.mark.parametrize('n',range(1,5))
@pytest.mark.parametrize('k',[1,2])
def test_actual_beta_enumeration_sound_complete_and_encoding_independent(n,k):
    xs=universe(n,k);first=encode_enumeration(xs);second=encode_enumeration(xs,2)
    assert actual_enumeration(k,n,len(xs),first)
    assert actual_enumeration(k,n,len(xs),second)
    assert first!=second
    assert not actual_enumeration(k,n,len(xs)+1,first)
    assert not actual_enumeration(k,n,len(xs)-1,first)


@pytest.mark.parametrize('a,b',[(1,1),(1,4),(2,3),(3,4),(4,5)])
@pytest.mark.parametrize('k',[1,2,3])
def test_actual_coordinate_crt_bijection_and_cardinality(a,b,k):
    source=universe(a*b,k);left=universe(a,k);right=universe(b,k)
    image=[(tuple(v%a for v in xs),tuple(v%b for v in xs)) for xs in source]
    assert len(set(image))==len(source)
    assert set(image)==set(product(left,right))
    assert len(source)==len(left)*len(right)
    for pair in image:
        inverse=tuple(next(t for t in range(a*b) if t%a==x and t%b==y) for x,y in zip(*pair))
        assert inverse in source


def test_collective_primitive_is_not_coordinatewise_unit():
    assert primitive(6,(2,3))
    assert all(gcd(6,v)!=1 for v in (2,3))
    assert len(universe(6,2))==24
    assert len(universe(6,2))!=len(universe(6,1))**2


def test_modulus_one_zero_tuple_and_non_coprime_counterexample():
    assert universe(1,3)==[(0,0,0)]
    assert len(universe(4,2))==12 and len(universe(2,2))**2==9
    assert not actual_enumeration(0,1,1,encode_enumeration([()]))
    assert not actual_enumeration(1,0,0,encode_enumeration([]))


def test_duplicate_encoding_is_not_duplicate_tuple_and_incomplete_lists_fail():
    xs=universe(2,2)
    assert not actual_enumeration(2,2,2,encode_enumeration(xs[:2]))
    assert not actual_enumeration(2,2,4,encode_enumeration(xs+[xs[0]]))
    assert not actual_enumeration(2,2,1,encode_enumeration([(0,0)]))


@lru_cache(None)
def body_core():
    result=dict(_specs_by_name())
    for module,factory in (
        ('coprime_divisor_decomposition_candidate','make_coprime_divisor_decomposition_candidate_theorems'),
        ('linear_congruence_complete_candidate','make_linear_congruence_complete_candidate_theorems'),
    ):
        for row in getattr(importlib.import_module('peano_lab.library.'+module),factory)(TheoremSpec):
            if row.name in result:assert _closed_formula(row.statement)==_closed_formula(result[row.name].statement)
            else:result[row.name]=row
    return result|{row.name:row for row in rows()}


@pytest.mark.parametrize('index',range(21))
def test_native_body(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    row=rows()[index];receipt=replay_candidate_bodies((row,),core=body_core())[0]
    assert receipt.name==row.name and receipt.command_count==len(row.script)


@pytest.mark.parametrize('index',range(21))
def test_native_false_conclusion_rejected(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index],statement='0=1'),),core=body_core())


EDGES=[(i,d) for i,row in enumerate(rows()) for d in row.dependencies]


@pytest.mark.parametrize('index,dependency',EDGES)
def test_native_removed_dependency_rejected(index,dependency):
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    row=rows()[index]
    bad=replace(row,dependencies=tuple(d for d in row.dependencies if d!=dependency))
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((bad,),core=body_core())
