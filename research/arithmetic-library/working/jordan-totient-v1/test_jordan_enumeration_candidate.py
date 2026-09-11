"""Independent finite-sweep contracts and genuine nested-beta model witnesses.

Native cases require a separately coordinated bounded lease. Model tests do
not establish either enumeration totality in HA or Jordan multiplicativity.
"""
from dataclasses import replace
from functools import lru_cache
import importlib
import importlib.util
from itertools import product
from math import factorial, prod
from pathlib import Path

import pytest

from peano_lab.library.theorems import TheoremSpec, _closed_formula

_path=Path(__file__).with_name('test_jordan_totient_candidate.py')
_loader=importlib.util.spec_from_file_location('_jordan_enumeration_independent_contracts',_path)
base=importlib.util.module_from_spec(_loader)
_loader.loader.exec_module(base)
candidate=base.candidate
And,Lt,At,Equal,Bounded,Primitive=base.And,base.Lt,base.At,base.Equal,base.Bounded,base.Primitive


def Listed(b,c,k,B,C,D,E,j):
    return 'exists en_i en_d en_e. '+And(Lt('en_i',j),
        And(At(B,C,'en_i','en_d'),At(D,E,'en_i','en_e')),
        Equal(b,c,'en_d','en_e',k))


def Scan(k,n,c,limit,B,C,D,E,j):
    def Entry(i,b,e):return And(At(B,C,i,b),At(D,E,i,e))
    sound=f'forall en_i. ({Lt("en_i",j)}) -> exists en_b en_e. '+And(
        Entry('en_i','en_b','en_e'),Bounded('en_b','en_e',k,n),Primitive(n,'en_b','en_e',k))
    distinct=(f'forall en_i en_h en_b en_e en_d en_f. ({Lt("en_i",j)}) -> '
        f'({Lt("en_h",j)}) -> ({Entry("en_i","en_b","en_e")}) -> '
        f'({Entry("en_h","en_d","en_f")}) -> ({Equal("en_b","en_e","en_d","en_f",k)}) -> en_i=en_h')
    cover=(f'forall en_z. ({Lt("en_z",limit)}) -> ({Bounded("en_z",c,k,n)}) -> '
        f'({Primitive(n,"en_z",c,k)}) -> ({Listed("en_z",c,k,B,C,D,E,j)})')
    return And(sound,distinct,cover)


def Prefix(b,c,d,e,k):
    return f'forall en_i en_a. ({Lt("en_i",k)}) -> ({At(b,c,"en_i","en_a")}) -> ({At(d,e,"en_i","en_a")})'


def Representatives(k,n,c,T):
    return f'forall en_b en_e. ({Bounded("en_b","en_e",k,n)}) -> exists en_z. '+And(
        Lt('en_z',T),Equal('en_b','en_e','en_z',c,k))


def CrtTuple(m,n,b,c,d,e,f,g,k):
    return f'forall cr_i. ({Lt("cr_i",k)}) -> exists cr_a cr_z cr_w. '+And(
        At(b,c,'cr_i','cr_a'),At(d,e,'cr_i','cr_z'),At(f,g,'cr_i','cr_w'),
        base.Mod(m,'cr_w','cr_a'),base.Mod(n,'cr_w','cr_z'))


def CanonicalCrt(m,n,b,c,d,e,f,g,k):
    return And(Bounded(f,g,k,m+'*'+n),base.PointMod(m,f,g,b,c,k),base.PointMod(n,f,g,d,e,k))


@lru_cache(None)
def rows():return (candidate.make_jordan_enumeration_candidate_theorems(TheoremSpec)
                  +candidate.make_jordan_enumeration_bridge_candidate_theorems(TheoremSpec)
                  +candidate.make_jordan_scan_candidate_theorems(TheoremSpec)
                  +candidate.make_jordan_crt_tuple_candidate_theorems(TheoremSpec)
                  +candidate.make_jordan_canonical_crt_candidate_theorems(TheoremSpec))


def contracts():
    C=base.Contract
    return (
        C('b c d e',[],Equal('b','c','d','e','0')),
        C('b c d e k',[Equal('b','c','d','e','S k')],Equal('b','c','d','e','k')),
        C('b c d e k a z',[Equal('b','c','d','e','k'),At('b','c','k','a'),At('d','e','k','z'),'a=z'],Equal('b','c','d','e','S k')),
        C('b c d e k',[],f'({Equal("b","c","d","e","k")}) \\/ ~({Equal("b","c","d","e","k")})'),
        C('b c k B C D E',[],f'~({Listed("b","c","k","B","C","D","E","0")})'),
        C('b c k B C D E j',[Listed('b','c','k','B','C','D','E','j')],Listed('b','c','k','B','C','D','E','S j')),
        C('b c k B C D E j',[],f'({Listed("b","c","k","B","C","D","E","j")}) \\/ ~({Listed("b","c","k","B","C","D","E","j")})'),
        C('k n c B C D E',[],Scan('k','n','c','0','B','C','D','E','0')),
        C('b c d e k',[Prefix('b','c','d','e','k')],Equal('b','c','d','e','k')),
        C('b c d e k i a',[Equal('b','c','d','e','k'),Lt('i','k'),At('b','c','i','a')],At('d','e','i','a')),
        C('b c d e k n',[Equal('b','c','d','e','k'),Bounded('b','c','k','n')],Bounded('d','e','k','n')),
        C('B C D E j b c',[],'exists U V W X. '+And(Equal('B','C','U','V','j'),Equal('D','E','W','X','j'),At('U','V','j','b'),At('W','X','j','c'))),
        C('b c d e k B C D E j',[Equal('b','c','d','e','k'),Listed('d','e','k','B','C','D','E','j')],Listed('b','c','k','B','C','D','E','j')),
        C('k n c t B C D E j',[Scan('k','n','c','t','B','C','D','E','j'),
          f'({Bounded("t","c","k","n")}) -> ({Primitive("n","t","c","k")}) -> ({Listed("t","c","k","B","C","D","E","j")})'],Scan('k','n','c','S t','B','C','D','E','j')),
        C('k n c T B C D E j',[Representatives('k','n','c','T'),Scan('k','n','c','T','B','C','D','E','j')],base.Enum('k','n','B','C','D','E','j')),
        C('k n c T B C D E j',['~(k=0)','~(n=0)',Representatives('k','n','c','T'),Scan('k','n','c','T','B','C','D','E','j')],base.Jordan('k','n','j')),
        C('k n c t B C D E j',[Scan('k','n','c','t','B','C','D','E','j'),Bounded('t','c','k','n'),Primitive('n','t','c','k'),
          '~('+Listed('t','c','k','B','C','D','E','j')+')'],
          'exists U V W X. '+Scan('k','n','c','S t','U','V','W','X','S j')),
        C('k n c',['~(n=0)'],'forall t. exists B C D E j. '+Scan('k','n','c','t','B','C','D','E','j')),
        C('k n',[],'exists c T. '+Representatives('k','n','c','T')),
        C('k n',['~(k=0)','~(n=0)'],'exists j. '+base.Jordan('k','n','j')),
        C('m n b c d e f g',[],CrtTuple('m','n','b','c','d','e','f','g','0')),
        C('m n b c d e f g k a z w',[CrtTuple('m','n','b','c','d','e','f','g','k'),
          At('b','c','k','a'),At('d','e','k','z'),base.Mod('m','w','a'),base.Mod('n','w','z')],
          'exists u v. '+CrtTuple('m','n','b','c','d','e','u','v','S k')),
        C('m n b c d e',['~(m=0)','~(n=0)',base.Cop('m','n')],
          'forall k. exists f g. '+CrtTuple('m','n','b','c','d','e','f','g','k')),
        C('m n b c d e f g k',[CrtTuple('m','n','b','c','d','e','f','g','k')],
          base.PointMod('m','f','g','b','c','k')),
        C('m n b c d e f g k',[CrtTuple('m','n','b','c','d','e','f','g','k')],
          base.PointMod('n','f','g','d','e','k')),
        C('n b c k',['~(n=0)'],'exists d e. '+And(Bounded('d','e','k','n'),base.PointMod('n','b','c','d','e','k'))),
        C('n b c d e f g k',[base.PointMod('n','b','c','d','e','k'),base.PointMod('n','d','e','f','g','k')],base.PointMod('n','b','c','f','g','k')),
        C('m n b c d e k',[base.Dvd('m','n'),base.PointMod('n','b','c','d','e','k')],base.PointMod('m','b','c','d','e','k')),
        C('m n b c d e k',['~(m=0)','~(n=0)',base.Cop('m','n')],
          'exists f g. '+CanonicalCrt('m','n','b','c','d','e','f','g','k')),
        C('m n b c d e k',['~(m=0)','~(n=0)',base.Cop('m','n'),Primitive('m','b','c','k'),Primitive('n','d','e','k')],
          'exists f g. '+And(CanonicalCrt('m','n','b','c','d','e','f','g','k'),Primitive('m*n','f','g','k'))),
    )


@pytest.mark.parametrize('index',range(30))
def test_exact_independent_contract(index):
    assert _closed_formula(rows()[index].statement)==_closed_formula(contracts()[index])
    assert rows()[index].script


def test_exact_provider_ownership_and_no_future_principal():
    core=dict(canonical_core())
    for row in rows():
        assert row.name not in core
        assert len(set(row.dependencies))==len(row.dependencies)
        assert set(row.dependencies)<=core.keys()
        core[row.name]=row
    assert not any('multiplicative' in r.name for r in rows())


@pytest.mark.parametrize('tag',['clean','renamed','bound_97'])
def test_public_relations_hygienically_match_independent_contracts(tag):
    assert _closed_formula('forall b c k B C D E j. '+candidate.tuple_listed_relation(
        'b','c','k','B','C','D','E','j',tag=tag))==_closed_formula(
        'forall b c k B C D E j. '+Listed('b','c','k','B','C','D','E','j'))
    assert _closed_formula('forall k n c t B C D E j. '+candidate.tuple_scan_relation(
        'k','n','c','t','B','C','D','E','j',tag=tag))==_closed_formula(
        'forall k n c t B C D E j. '+Scan('k','n','c','t','B','C','D','E','j'))


@pytest.mark.parametrize('bad',['jt_code_bad','fs_x','ff_x','a+b','0','a b'])
def test_public_binder_capture_and_nonvariable_rejected(bad):
    with pytest.raises(ValueError):candidate.tuple_listed_relation(bad,'c','k','B','C','D','E','j',tag='bad')


def model_listed(pair,k,outer,j):
    B,C,D,E=outer
    return any(base.decoded(*pair,k)==base.decoded(base.decode(B,C,i),base.decode(D,E,i),k)
               for i in range(j))


@pytest.mark.parametrize('k,n',list(product((1,2),range(1,5))))
def test_actual_code_sweep_removes_duplicates_and_constructs_enumeration(k,n):
    c=factorial(k)*n
    # Twice a genuine complete CRT period deliberately supplies duplicate codes.
    period=prod(1+(i+1)*c for i in range(k))
    limit=2*period
    retained=[]
    skipped_duplicate=0
    for z in range(limit):
        values=base.decoded(z,c,k)
        if not all(v<n for v in values) or not base.primitive(n,values):continue
        old=(*base.encode([b for b,e in retained]),*base.encode([e for b,e in retained]))
        if model_listed((z,c),k,old,len(retained)):
            skipped_duplicate+=1
            continue
        retained.append((z,c))
        actual=[base.decoded(b,e,k) for b,e in retained]
        assert len(set(actual))==len(actual)
        assert all(all(v<n for v in xs) and base.primitive(n,xs) for xs in actual)
    outer=(*base.encode([b for b,e in retained]),*base.encode([e for b,e in retained]))
    assert skipped_duplicate==len(retained)>0
    assert base.actual_enumeration(k,n,len(retained),outer)
    assert len(retained)==len(base.universe(n,k))


def test_membership_uses_decoded_coordinates_not_code_or_scale():
    first=base.encode((1,0));second=base.encode((1,0),3)
    assert first!=second
    outer=(*base.encode([first[0]]),*base.encode([first[1]]))
    assert model_listed(second,2,outer,1)
    assert not model_listed(second,2,outer,0)
    assert not model_listed(base.encode((0,1)),2,outer,1)


@pytest.mark.parametrize('k',[1,2,3])
def test_rectangular_crt_enumeration_uses_actual_nested_beta_lists(k):
    a,b=2,3
    left,right=base.universe(a,k),base.universe(b,k)
    output=[]
    for i,xs in enumerate(left):
        for j,ys in enumerate(right):
            position=i*len(right)+j
            assert divmod(position,len(right))==(i,j)
            output.append(tuple(next(z for z in range(a*b) if z%a==x and z%b==y)
                                for x,y in zip(xs,ys)))
    witness=base.encode_enumeration(output)
    assert base.actual_enumeration(k,a*b,len(left)*len(right),witness)


@lru_cache(None)
def canonical_core():
    core=dict(base.body_core())
    for name in ('matrix_rank_finite_coding_candidate','prime_field_polynomial_candidate'):
        module=importlib.import_module('peano_lab.library.'+name)
        for row in getattr(module,'make_'+name+'_theorems')(TheoremSpec):
            if row.name in core:assert _closed_formula(row.statement)==_closed_formula(core[row.name].statement)
            else:core[row.name]=row
    return core


@lru_cache(None)
def core():return canonical_core()|{r.name:r for r in rows()}


@pytest.mark.parametrize('index',range(30))
def test_native_body(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    row=rows()[index]
    receipt=replay_candidate_bodies((row,),core=core())[0]
    assert receipt.name==row.name and receipt.command_count==len(row.script)


@pytest.mark.parametrize('index',range(30))
def test_native_false_statement_rejected(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index],statement='0=1'),),core=core())


@pytest.mark.parametrize('index,dependency',[(i,d) for i,r in enumerate(rows()) for d in r.dependencies])
def test_native_removed_edge_rejected(index,dependency):
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    row=rows()[index]
    with pytest.raises(CandidateBodyError):replay_candidate_bodies(
        (replace(row,dependencies=tuple(d for d in row.dependencies if d!=dependency)),),core=core())
