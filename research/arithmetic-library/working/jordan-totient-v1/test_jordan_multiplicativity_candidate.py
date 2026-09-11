"""Independent rectangular-count contracts; native jobs require a root lease."""
from dataclasses import replace
from functools import lru_cache
import hashlib
import importlib
import importlib.util
from itertools import product
from pathlib import Path

import pytest
from peano_lab.library.theorems import TheoremSpec,_closed_formula


def load(name,path):
    loader=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(loader);loader.loader.exec_module(result)
    return result


HERE=Path(__file__).parent
old=load('_jordan_rect_independent_old_tests',HERE/'test_jordan_enumeration_candidate.py')
source=load('_jordan_rect_source',HERE/'jordan_multiplicativity_candidate.py')
base=old.base
And,Lt,At,Equal,Bounded,Primitive=old.And,old.Lt,old.At,old.Equal,old.Bounded,old.Primitive
Enum,PointMod,Cop,Mod,Crt=base.Enum,base.PointMod,base.Cop,base.Mod,old.CanonicalCrt


def Le(a,b):return f'exists rr_gap. rr_gap+({a})=({b})'
def Entry(A,B,C,D,i,b,c):return And(At(A,B,i,b),At(C,D,i,c))


def Rect(m,n,k,A,B,C,D,u,E,F,G,H,v,P,Q,R,T,q):
    return f'forall rr_p. ({Lt("rr_p",q)}) -> exists rr_i rr_j rr_b rr_c rr_d rr_e rr_f rr_g. '+And(
        Lt('rr_i',u),Lt('rr_j',v),f'rr_p=({v})*rr_i+rr_j',
        Entry(A,B,C,D,'rr_i','rr_b','rr_c'),Entry(E,F,G,H,'rr_j','rr_d','rr_e'),
        Entry(P,Q,R,T,'rr_p','rr_f','rr_g'),Crt(m,n,'rr_b','rr_c','rr_d','rr_e','rr_f','rr_g',k),
        Primitive(m+'*'+n,'rr_f','rr_g',k))


def RectValue(m,n,k,A,B,C,D,u,E,F,G,H,v,P,Q,R,T,p,i,j,b,c,d,e,f,g):
    return And(Lt(i,u),Lt(j,v),f'{p}=({v})*({i})+({j})',Entry(A,B,C,D,i,b,c),
               Entry(E,F,G,H,j,d,e),Entry(P,Q,R,T,p,f,g),Crt(m,n,b,c,d,e,f,g,k),Primitive(m+'*'+n,f,g,k))


@lru_cache(None)
def rows():return source.make_jordan_multiplicativity_candidate_theorems(TheoremSpec)


def contracts():
    C=base.Contract
    args=('m','n','k','A','B','C','D','u','E','F','G','H','v','P','Q','R','T')
    left,right=Enum('k','m','A','B','C','D','u'),Enum('k','n','E','F','G','H','v')
    common=['~(m=0)','~(n=0)',Cop('m','n'),left,right,Rect(*args,'u*v')]
    return (
        C('u v p',[Lt('p','u*v')],'~(v=0)'),
        C('u v p i j',[Lt('p','u*v'),'p=v*i+j',Lt('j','v')],Lt('i','u')),
        C('u v i j',[Lt('i','u'),Lt('j','v')],Lt('v*i+j','u*v')),
        C('v i j r s',[Lt('j','v'),Lt('s','v'),'v*i+j=v*r+s'],'i=r /\\ j=s'),
        C('n b c d e k',[Equal('b','c','d','e','k')],PointMod('n','b','c','d','e','k')),
        C('n b c d e k',[Bounded('b','c','k','n'),Bounded('d','e','k','n'),PointMod('n','b','c','d','e','k')],Equal('b','c','d','e','k')),
        C('m n b c d e k',[Cop('m','n'),PointMod('m','b','c','d','e','k'),PointMod('n','b','c','d','e','k')],PointMod('m*n','b','c','d','e','k')),
        C('n b c d e f g h s k',[Bounded('b','c','k','n'),Bounded('d','e','k','n'),PointMod('n','f','g','b','c','k'),PointMod('n','h','s','d','e','k'),Equal('f','g','h','s','k')],Equal('b','c','d','e','k')),
        C('m n b c d e f g h s k',[Cop('m','n'),Crt('m','n','b','c','d','e','f','g','k'),Crt('m','n','b','c','d','e','h','s','k')],Equal('f','g','h','s','k')),
        C('k n A B C D j i b c',[Enum('k','n','A','B','C','D','j'),Lt('i','j'),Entry('A','B','C','D','i','b','c')],And(Bounded('b','c','k','n'),Primitive('n','b','c','k'))),
        C('k n A B C D j b c',[Enum('k','n','A','B','C','D','j'),Bounded('b','c','k','n'),Primitive('n','b','c','k')],old.Listed('b','c','k','A','B','C','D','j')),
        C('k n A B C D j i h b c d e',[Enum('k','n','A','B','C','D','j'),Lt('i','j'),Lt('h','j'),Entry('A','B','C','D','i','b','c'),Entry('A','B','C','D','h','d','e'),Equal('b','c','d','e','k')],'i=h'),
        C('m n k A B C D u E F G H v P Q R T q',['~(m=0)','~(n=0)',Cop('m','n'),Enum('k','m','A','B','C','D','u'),Enum('k','n','E','F','G','H','v'),
          Rect('m','n','k','A','B','C','D','u','E','F','G','H','v','P','Q','R','T','q'),Lt('q','u*v')],
          'exists U V W X. '+Rect('m','n','k','A','B','C','D','u','E','F','G','H','v','U','V','W','X','S q')),
        C(' '.join(args[:-4])+' q',common[:-1]+['exists P Q R T. '+Rect(*args,'q'),Lt('q','u*v')],
          'exists P Q R T. '+Rect(*args,'S q')),
        C('m n k A B C D u E F G H v',['~(m=0)','~(n=0)',Cop('m','n'),Enum('k','m','A','B','C','D','u'),Enum('k','n','E','F','G','H','v')],
          f'forall q. ({Le("q","u*v")}) -> exists P Q R T. '+Rect('m','n','k','A','B','C','D','u','E','F','G','H','v','P','Q','R','T','q')),
        C(' '.join(args)+' q p f g',[Rect(*args,'q'),Lt('p','q'),Entry('P','Q','R','T','p','f','g')],
          'exists i j b c d e. '+RectValue(*args,'p','i','j','b','c','d','e','f','g')),
        C(' '.join(args)+' i j b c d e',[Rect(*args,'u*v'),Lt('i','u'),Lt('j','v'),Entry('A','B','C','D','i','b','c'),Entry('E','F','G','H','j','d','e')],
          'exists f g. '+And(Entry('P','Q','R','T','v*i+j','f','g'),Crt('m','n','b','c','d','e','f','g','k'),Primitive('m*n','f','g','k'))),
        C('n k A B C D j b c',['~(n=0)',Enum('k','n','A','B','C','D','j'),Primitive('n','b','c','k')],
          'exists i d e. '+And(Lt('i','j'),Entry('A','B','C','D','i','d','e'),PointMod('n','b','c','d','e','k'))),
        C(' '.join(args)+' p z f g h s',[left,right,Rect(*args,'u*v'),Lt('p','u*v'),Lt('z','u*v'),Entry('P','Q','R','T','p','f','g'),Entry('P','Q','R','T','z','h','s'),Equal('f','g','h','s','k')],'p=z'),
        C(' '.join(args)+' b c',common+[Bounded('b','c','k','m*n'),Primitive('m*n','b','c','k')],old.Listed('b','c','k','P','Q','R','T','u*v')),
        C(' '.join(args),common,Enum('k','m*n','P','Q','R','T','u*v')),
        C(' '.join(args[:-4]),common[:-1],'exists P Q R T. '+Enum('k','m*n','P','Q','R','T','u*v')),
        C('k a b u v',[Cop('a','b'),base.Jordan('k','a','u'),base.Jordan('k','b','v')],base.Jordan('k','a*b','u*v')),
        C('k a b',['~(k=0)','~(a=0)','~(b=0)',Cop('a','b')],
          'exists u v w. '+And(base.Jordan('k','a','u'),base.Jordan('k','b','v'),base.Jordan('k','a*b','w'),'w=u*v')),
    )


@pytest.mark.parametrize('index',range(24))
def test_exact_expanded_contract(index):
    assert _closed_formula(rows()[index].statement)==_closed_formula(contracts()[index])


@lru_cache(None)
def inherited_core():
    result=dict(old.core())
    module=importlib.import_module('peano_lab.library.finite_modular_set_candidate')
    for row in module.make_finite_modular_set_candidate_theorems(TheoremSpec):
        if row.name in result:assert _closed_formula(row.statement)==_closed_formula(result[row.name].statement)
        else:result[row.name]=row
    return result


def test_dependency_dag_and_frozen_51_source():
    assert hashlib.sha256((HERE/'jordan_totient_candidate.py').read_bytes()).hexdigest()==source.BASE_SHA256
    core=dict(inherited_core())
    for row in rows():
        assert row.name not in core
        assert set(row.dependencies)<=core.keys()
        assert len(set(row.dependencies))==len(row.dependencies)
        core[row.name]=row


def test_flat_lookup_witnesses_do_not_capture_requested_indices():
    from peano_lab.kernel.formulas import parse_formula_with_names
    command=next(s for s in rows()[16].script if s.startswith('have hv :'))
    _,free=parse_formula_with_names(command.split(' : ',1)[1])
    assert {'v','i','j'}<=set(free)
    assert command.startswith('have hv : exists ri rj rb rc rd re rf rg.')


@pytest.mark.parametrize('u,v',tuple(product(range(5),repeat=2)))
def test_actual_rectangular_indices_and_zero_width(u,v):
    image=[v*i+j for i in range(u) for j in range(v)]
    assert image==list(range(u*v))
    for p in image:
        assert v!=0
        i,j=divmod(p,v)
        assert i<u and j<v and p==v*i+j


@pytest.mark.parametrize('m,n,k',[(1,1,1),(1,3,2),(2,3,1),(2,3,2),(3,4,2)])
def test_genuine_nested_beta_rectangular_output(m,n,k):
    left,right=base.universe(m,k),base.universe(n,k)
    L,R=base.encode_enumeration(left),base.encode_enumeration(right)
    out=[]
    for i in range(len(left)):
        for j in range(len(right)):
            a=base.decoded(base.decode(L[0],L[1],i),base.decode(L[2],L[3],i),k)
            b=base.decoded(base.decode(R[0],R[1],j),base.decode(R[2],R[3],j),k)
            out.append(tuple(next(z for z in range(m*n) if z%m==x and z%n==y) for x,y in zip(a,b)))
    actual=base.encode_enumeration(out)
    assert base.actual_enumeration(k,m*n,len(left)*len(right),actual)
    assert len(set(out))==len(out)
    assert {(tuple(z%m for z in xs),tuple(z%n for z in xs)) for xs in out}==set(product(left,right))


@lru_cache(None)
def core():return inherited_core()|{r.name:r for r in rows()}


@pytest.mark.parametrize('index',range(24))
def test_native_body(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    row=rows()[index];receipt=replay_candidate_bodies((row,),core=core())[0]
    assert receipt.name==row.name and receipt.command_count==len(row.script)


@pytest.mark.parametrize('index',range(24))
def test_native_false_target_rejected(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(rows()[index],statement='0=1'),),core=core())


@pytest.mark.parametrize('index,dependency',[(i,d) for i,r in enumerate(rows()) for d in r.dependencies])
def test_native_removed_edge_rejected(index,dependency):
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    row=rows()[index]
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(row,dependencies=tuple(d for d in row.dependencies if d!=dependency)),),core=core())
