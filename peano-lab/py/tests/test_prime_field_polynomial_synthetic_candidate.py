"""Independent contracts and real-HA body tests for synthetic division.

Candidate-body acceptance leaves dependencies as ordinary hypotheses. The
separate checkpoint must close those dependencies and run compiled Lean.
Finite beta-code examples are diagnostics, never theorem evidence.
"""

from dataclasses import replace
from functools import lru_cache
import re

import pytest

from peano_lab.library import prime_field_polynomial_synthetic_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.matrix_coded_product_candidate import make_matrix_coded_product_candidate_theorems
from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems
from peano_lab.library.prime_field_polynomial_evaluation_candidate import make_prime_field_polynomial_evaluation_candidate_theorems
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula
from test_prime_field_polynomial_candidate import (
    assert_inventory, capture_cases, compound_cases, decode_beta, encode_beta,
    expected_and, expected_at, expected_coeff, expected_equal, expected_field_add,
    expected_field_mul, expected_lt, expected_prime, same_ast,
)
from test_prime_field_polynomial_evaluation_candidate import expected_eval, expected_trace, horner_values, model_trace


NAMES = (
    'prime_field_polynomial_horner_trace_prefix',
    'prime_field_polynomial_horner_trace_state_bounded',
    'prime_field_polynomial_synthetic_exists',
    'prime_field_polynomial_synthetic_remainder_execution',
    'prime_field_polynomial_synthetic_quotient_entry',
    'prime_field_polynomial_synthetic_quotient_bounded',
    'prime_field_polynomial_synthetic_remainder_bounded',
    'prime_field_polynomial_synthetic_functional',
    'prime_field_polynomial_horner_constant_value',
    'prime_field_polynomial_horner_transition_values',
    'prime_field_polynomial_synthetic_leading_coefficient',
    'prime_field_polynomial_synthetic_middle_coefficients',
    'prime_field_polynomial_synthetic_final_coefficient',
    'prime_field_polynomial_synthetic_represented_degree',
    'prime_field_polynomial_synthetic_constant',
    'prime_field_polynomial_synthetic_exists_unique',
    'prime_field_polynomial_synthetic_zero_remainder_iff',
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_synthetic_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    # Exact original source specifications supply hypothesis types only.
    # This intentionally avoids loading a large edition or saved receipt.
    return {r.name:r for r in (*THEOREMS,
        *make_matrix_coded_product_candidate_theorems(TheoremSpec),
        *make_matrix_rank_finite_coding_candidate_theorems(TheoremSpec),
        *make_prime_field_polynomial_evaluation_candidate_theorems(TheoremSpec),
        *rows())}


def expected_le(a,b):
    return f'exists independent_le_gap. independent_le_gap+({a})=({b})'


def expected_slice(u,v,qb,qc,n,*,offset='1'):
    i,s,t='independent_slice_index','independent_slice_source','independent_slice_target'
    return (f'forall {i} {s} {t}. ({expected_lt(i,n)}) -> '
            f'({expected_at(u,v,f"({offset})+1*{i}",s)}) -> '
            f'({expected_at(qb,qc,i,t)}) -> {t}={s}')


def expected_synthetic(p,b,c,a,n,qb,qc,r,*,offset='1',initial='0',wrong_order=False):
    u,v='independent_synthetic_history','independent_synthetic_scale'
    return f'exists {u} {v}. '+expected_and(
        expected_trace(p,b,c,a,f'S ({n})',r,u,v,initial=initial,wrong_order=wrong_order),
        expected_slice(u,v,qb,qc,n,offset=offset))


def expected_degree(p,b,c,length,d):
    return expected_and(f'({length})=S ({d})',expected_coeff(p,b,c,length),
        'exists independent_leading. '+expected_and(
            expected_at(b,c,'0','independent_leading'),'~(independent_leading=0)'))


def contract(names,premises,result):
    return 'forall '+names+'. '+' -> '.join('('+part+')' for part in (*premises,result))


def contracts():
    P,C,E,A,H,T,D,S = (expected_prime,expected_coeff,expected_eval,expected_at,
                       expected_lt,expected_trace,expected_degree,expected_synthetic)
    fixed=S('p','b','c','a','n','qb','qc','r')
    positive=S('p','b','c','a','S n','qb','qc','r')
    recurrence=lambda h,v,r:'exists k. '+expected_and(expected_field_mul('p',h,'a','k'),expected_field_add('p','k',v,r))
    return {
        NAMES[0]:contract('p b c a l r u v n h',(T('p','b','c','a','l','r','u','v'),expected_le('n','l'),A('u','v','n','h')),E('p','b','c','a','n','h')),
        NAMES[1]:contract('p b c a l r u v n h',(P('p'),T('p','b','c','a','l','r','u','v'),expected_le('n','l'),A('u','v','n','h')),H('h','p')),
        NAMES[2]:contract('p b c a n',(P('p'),C('p','b','c','S n'),H('a','p')),'exists qb qc r. ('+fixed+')'),
        NAMES[3]:contract('p b c a n qb qc r',(fixed,),E('p','b','c','a','S n','r')),
        NAMES[4]:contract('p b c a n qb qc r i h',(fixed,H('i','n'),A('qb','qc','i','h')),E('p','b','c','a','S i','h')),
        NAMES[5]:contract('p b c a n qb qc r',(P('p'),fixed),C('p','qb','qc','n')),
        NAMES[6]:contract('p b c a n qb qc r',(P('p'),fixed),H('r','p')),
        NAMES[7]:contract('p b c a n qb qc r Qb Qc s',(P('p'),fixed,S('p','b','c','a','n','Qb','Qc','s')),expected_and('r=s',expected_equal('qb','qc','Qb','Qc','n'))),
        NAMES[8]:contract('p b c a r v',(P('p'),E('p','b','c','a','1','r'),A('b','c','0','v')),'r=v'),
        NAMES[9]:contract('p b c a i h v r',(P('p'),E('p','b','c','a','i','h'),E('p','b','c','a','S i','r'),A('b','c','i','v')),recurrence('h','v','r')),
        NAMES[10]:contract('p b c a n qb qc r v',(P('p'),positive,A('b','c','0','v')),A('qb','qc','0','v')),
        NAMES[11]:contract('p b c a n qb qc r i h j v',(P('p'),positive,H('i','n'),A('qb','qc','i','h'),A('qb','qc','S i','j'),A('b','c','S i','v')),recurrence('h','v','j')),
        NAMES[12]:contract('p b c a n qb qc r h v',(P('p'),positive,A('qb','qc','n','h'),A('b','c','S n','v')),recurrence('h','v','r')),
        NAMES[13]:contract('p b c a n qb qc r',(P('p'),D('p','b','c','S (S n)','S n'),positive),D('p','qb','qc','S n','n')),
        NAMES[14]:contract('p b c a qb qc r v',(P('p'),S('p','b','c','a','0','qb','qc','r'),A('b','c','0','v')),'r=v'),
        NAMES[15]:contract('p b c a n',(P('p'),C('p','b','c','S n'),H('a','p')),
            'exists qb qc r. '+expected_and(fixed,'forall Qb Qc s. ('+S('p','b','c','a','n','Qb','Qc','s')+') -> '+expected_and('s=r',expected_equal('Qb','Qc','qb','qc','n')))),
        NAMES[16]:contract('p b c a n qb qc r',(P('p'),fixed),expected_and(
            'r=0 -> ('+E('p','b','c','a','S n','0')+')',
            '('+E('p','b','c','a','S n','0')+') -> r=0')),
    }


def test_exact_inventory_and_actual_dependency_order():
    assert tuple(r.name for r in rows())==NAMES
    inherited={name:r for name,r in core().items() if name not in NAMES}
    assert_inventory(rows(),inherited)
    assert candidate.__all__==['prime_field_polynomial_synthetic_division_relation',
                              'make_prime_field_polynomial_synthetic_candidate_theorems']
    assert not any('polynomial_gcd' in name or 'irreducible' in name or 'extension_field' in name for name in NAMES)


@pytest.mark.parametrize('name,expected',tuple(contracts().items()))
def test_every_statement_matches_an_independently_written_contract(name,expected):
    same_ast(_closed_formula(next(r.statement for r in rows() if r.name==name)),_closed_formula(expected))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_every_actual_body_in_original_ha(row):
    receipt=replay_candidate_bodies((row,),core=core())[0]
    assert receipt.name==row.name and receipt.proof_nodes>0
    assert receipt.proof_depth<=256


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
@pytest.mark.parametrize('mutation',('false_conclusion','truncated_body'))
def test_wrong_conclusion_and_incomplete_body_are_rejected(row,mutation):
    changed=(replace(row,statement=f'({row.statement}) /\\ false') if mutation=='false_conclusion'
             else replace(row,script=row.script[:-1]))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core())


EDGES=tuple((row,index) for row in rows() for index in range(len(row.dependencies)))


@pytest.mark.parametrize('row,index',EDGES,ids=lambda value:value.name if isinstance(value,TheoremSpec) else str(value))
@pytest.mark.parametrize('mutation',('removed','poisoned'))
def test_every_declared_dependency_is_used_with_its_actual_type(row,index,mutation):
    dependency=row.dependencies[index]
    changed=replace(row,dependencies=row.dependencies[:index]+row.dependencies[index+1:]) if mutation=='removed' else row
    table=core() if mutation=='removed' else core()|{dependency:replace(core()[dependency],statement='0=0')}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=table)


ARGS=('p','b','c','a','n','qb','qc','r')
PUBLIC=((candidate.prime_field_polynomial_synthetic_division_relation,ARGS,expected_synthetic),)


def test_public_graph_is_exactly_execution_and_actual_slice_not_an_algebraic_result():
    formula=candidate.prime_field_polynomial_synthetic_division_relation(*ARGS,tag='independent',variables=ARGS)
    same_ast(_closed_formula('forall '+' '.join(ARGS)+'. '+formula),
             _closed_formula('forall '+' '.join(ARGS)+'. '+expected_synthetic(*ARGS)))
    for wrong in ('0','2'):
        assert _closed_formula('forall '+' '.join(ARGS)+'. '+formula)!=_closed_formula(
            'forall '+' '.join(ARGS)+'. '+expected_synthetic(*ARGS,offset=wrong))


@pytest.mark.parametrize('builder,args,expected,index,term',compound_cases(PUBLIC))
def test_compound_and_large_numeral_arguments_remain_exact(builder,args,expected,index,term):
    actual=(*args[:index],term,*args[index+1:])
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*actual,tag='compound',variables=args)),
             _closed_formula(binder+expected(*actual)))


@pytest.mark.parametrize('builder,args,binder',capture_cases(PUBLIC))
def test_entire_context_capture_is_rejected(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=args+(binder,))
    with pytest.raises(ValueError,match='captures'):
        builder(args[0]+'+'+binder,*args[1:],tag='capture',variables=args+(binder,))


@pytest.mark.parametrize('bad',('undeclared','a -> a','a=0','',None,False,7))
def test_bad_terms_rejected(bad):
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_synthetic_division_relation(bad,*ARGS[1:],tag='bad',variables=ARGS)


@pytest.mark.parametrize('context',((),[],('p','p'),('bad name',),('forall',)))
def test_bad_contexts_rejected(context):
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_synthetic_division_relation(*('0' for _ in ARGS),tag='bad',variables=context)


@pytest.mark.parametrize('tag',('bad tag','forall','S','',None,False))
def test_bad_tags_rejected(tag):
    with pytest.raises(ValueError):
        candidate.prime_field_polynomial_synthetic_division_relation(*ARGS,tag=tag,variables=ARGS)


def model_synthetic(p,source,a,n,quotient,r,history):
    return model_trace(p,source,a,n+1,r,history) and all(
        decode_beta(quotient,i)==decode_beta(history,i+1) for i in range(n))


@pytest.mark.parametrize('p',(2,3,5,7,11))
@pytest.mark.parametrize('raw',((0,),(1,),(0,0),(1,1),(3,0,7),(0,0,2,1),(19,7,0,29)))
def test_actual_beta_encodings_coefficient_identities_and_remainder(p,raw):
    values=tuple(v%p for v in raw)
    n=len(values)-1
    source=encode_beta(values)
    for a in range(p):
        states=horner_values(values,a,p)
        q=states[1:-1]
        quotient,history=encode_beta(q),encode_beta(states)
        otherq,otherh=encode_beta(q,3),encode_beta(states,2)
        r=states[-1]
        assert model_synthetic(p,source,a,n,quotient,r,history)
        assert model_synthetic(p,encode_beta(values,2),a,n,otherq,r,otherh)
        assert all(0<=v<p for v in (*q,r))
        # Independent coefficient reconstruction of (X-a)Q+r.
        if n:
            reconstructed=[q[0]]
            reconstructed.extend((q[i]-a*q[i-1])%p for i in range(1,n))
            reconstructed.append((r-a*q[-1])%p)
            assert tuple(reconstructed)==values
            if values[0]!=0:
                assert q[0]!=0 and len(q)-1==len(values)-2
        else:
            assert q==() and r==values[0]
        assert (r==0)==(sum(v*pow(a,len(values)-1-i,p) for i,v in enumerate(values))%p==0)
        assert not model_synthetic(p,source,a,n,quotient,(r+1)%p,history)
        assert not model_synthetic(p,source,p,n,quotient,r,history)


def test_no_modulus_zero_execution_and_no_false_empty_input_claim():
    assert not model_synthetic(0,(0,0),0,0,(0,0),0,(0,0))
    # The relation is explicitly about a nonempty input S n, not length n.
    assert all('S (' in candidate._synthetic('p','b','c','a','n','qb','qc','r',tag)
               for tag in ('contract','diagnostic'))


@pytest.mark.parametrize('offset',('0','2'))
def test_wrong_quotient_shift_rejected_by_original_entry_body(offset):
    row=rows()[4]
    altered=contract('p b c a n qb qc r i h',(
        expected_synthetic('p','b','c','a','n','qb','qc','r',offset=offset),
        expected_lt('i','n'),expected_at('qb','qc','i','h')),
        expected_eval('p','b','c','a','S i','h'))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=altered),),core=core())


def test_missing_nonzero_leading_degree_guard_rejected():
    row=rows()[13]
    altered=contract('p b c a n qb qc r',(
        expected_prime('p'),expected_coeff('p','b','c','S (S n)'),
        expected_synthetic('p','b','c','a','S n','qb','qc','r')),
        expected_degree('p','qb','qc','S n','n'))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=altered),),core=core())
