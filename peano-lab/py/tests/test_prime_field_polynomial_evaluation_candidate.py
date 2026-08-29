"""Exact modular-Horner contracts, hostile proofs, and concrete beta traces."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.library import prime_field_polynomial_evaluation_candidate as candidate
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from test_prime_field_polynomial_candidate import (
    assert_inventory, capture_cases, compound_cases, core, decode_beta,
    decoded_prefix, encode_beta, expected_and, expected_at, expected_coeff,
    expected_equal, expected_field_add, expected_field_mul, expected_lt,
    expected_normalization, expected_prime, expected_repeat, expected_residue,
    fresh, model_normalization, rows as coefficient_rows, same_ast,
)


SOURCE_SHA256 = '9638337f69bdc1f5491255b767dc90042244402e34ceab84902b0481c2eab802'
NAMES_SHA256 = '9f2dfee5e428f6f573839e8f3a0801716379f8b73e736b483256091ca46b0961'


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_evaluation_candidate_theorems(TheoremSpec)


def expected_step(p,b,c,t,u,v,i,*,wrong_order=False):
    a,h,j,k = 'ind_coefficient','ind_before','ind_after','ind_product'
    operation = (expected_field_mul(p,a,t,k),expected_field_add(p,h,k,j)) if wrong_order else (expected_field_mul(p,h,t,k),expected_field_add(p,k,a,j))
    return f'exists {a} {h} {j} {k}. '+expected_and(expected_at(b,c,i,a),expected_at(u,v,i,h),expected_at(u,v,f'S ({i})',j),*operation)


def expected_steps(p,b,c,t,length,u,v,*,wrong_order=False):
    return f'forall ind_index. ({expected_lt("ind_index",length)}) -> ({expected_step(p,b,c,t,u,v,"ind_index",wrong_order=wrong_order)})'


def expected_trace(p,b,c,t,length,r,u,v,*,initial='0',wrong_order=False):
    return expected_and(expected_lt(t,p),expected_at(u,v,'0',initial),expected_at(u,v,length,r),expected_steps(p,b,c,t,length,u,v,wrong_order=wrong_order))


def expected_eval(p,b,c,t,length,r,*,initial='0',wrong_order=False):
    return f'exists ind_trace_code ind_trace_scale. ({expected_trace(p,b,c,t,length,r,"ind_trace_code","ind_trace_scale",initial=initial,wrong_order=wrong_order)})'


def expected_natural_trace(b,c,t,length,n,u,v,*,wrong_order=False):
    a,h,j,i = 'ind_nat_coefficient','ind_nat_before','ind_nat_after','ind_nat_index'
    update = f'{j}={h}+{a}*({t})' if wrong_order else f'{j}={h}*({t})+{a}'
    point = f'exists {a} {h} {j}. '+expected_and(expected_at(b,c,i,a),expected_at(u,v,i,h),expected_at(u,v,f'S ({i})',j),update)
    steps = f'forall {i}. ({expected_lt(i,length)}) -> ({point})'
    return expected_and(expected_at(u,v,'0','0'),expected_at(u,v,length,n),steps)


def expected_natural(b,c,t,length,n,*,wrong_order=False):
    return f'exists ind_nat_code ind_nat_scale. ({expected_natural_trace(b,c,t,length,n,"ind_nat_code","ind_nat_scale",wrong_order=wrong_order)})'


PUBLIC_CASES = (
    (candidate.prime_field_polynomial_horner_step_relation,('p','b','c','t','u','v','i'),expected_step),
    (candidate.prime_field_polynomial_horner_steps_relation,('p','b','c','t','l','u','v'),expected_steps),
    (candidate.prime_field_polynomial_horner_trace_relation,('p','b','c','t','l','r','u','v'),expected_trace),
    (candidate.prime_field_polynomial_evaluation_relation,('p','b','c','t','l','r'),expected_eval),
)


@pytest.mark.parametrize('mutation',('none','false_conclusion','truncated_body','removed_dependency','forged_dependency'))
def test_all_actual_evaluation_bodies_and_hostile_variants_in_fresh_bounded_processes(mutation):
    report = fresh('--bodies','evaluation',mutation)
    expected = [r.name for r in rows() if mutation not in ('removed_dependency','forged_dependency') or r.dependencies]
    assert [r['name'] for r in report['receipts']] == expected
    if mutation == 'none':
        assert sum(r['proof_nodes'] for r in report['receipts']) == 1966
        assert sum(r['proof_objects'] for r in report['receipts']) == 1964
        assert max(r['proof_nodes'] for r in report['receipts']) == 349
        assert max(r['proof_depth'] for r in report['receipts']) == 55
        assert all(r['proof_depth'] <= 256 and r['proof_objects'] <= r['proof_nodes'] for r in report['receipts'])
    else:
        assert all(r['rejected'] == mutation for r in report['receipts'])


def test_exact_evaluation_inventory_and_actual_dependency_order():
    assert len(rows()) == 18
    assert sum(len(row.dependencies) for row in rows()) == 78
    assert sum(len(row.script) for row in rows()) == 1149
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest() == SOURCE_SHA256
    assert sha256(('\n'.join(row.name for row in rows())+'\n').encode()).hexdigest() == NAMES_SHA256
    assert_inventory(rows(),core() | {r.name:r for r in coefficient_rows()})
    dependencies = {name for row in rows() for name in row.dependencies}
    assert {'beta_horner_eval_exists','beta_horner_eval_empty','beta_horner_eval_successor_decompose','prime_field_polynomial_normalization_exists','prime_field_residue_add','prime_field_residue_multiply'} <= dependencies
    assert not any(any(unproved in r.name for unproved in ('polynomial_division','polynomial_gcd','irreducible','extension_field','degree')) for r in rows())


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES,ids=lambda x:x.__name__ if callable(x) else None)
def test_public_horner_graphs_match_independent_actual_operation_traces(builder,args,expected):
    binder = 'forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*args,tag='independent',variables=args)),_closed_formula(binder+expected(*args)))


@pytest.mark.parametrize('builder,args,expected,index,term',compound_cases(PUBLIC_CASES))
def test_every_horner_argument_preserves_compound_and_large_terms(builder,args,expected,index,term):
    values = (*args[:index],term,*args[index+1:])
    binder = 'forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*values,tag='compound',variables=args)),_closed_formula(binder+expected(*values)))


@pytest.mark.parametrize('builder,args,binder',capture_cases(PUBLIC_CASES))
def test_every_horner_binder_rejects_entire_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=args+(binder,))
    with pytest.raises(ValueError,match='captures'):
        builder(f'{args[0]}+{binder}',*args[1:],tag='capture',variables=args+(binder,))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('context',((),[],('p','p'),('bad name',),('forall',)))
def test_invalid_horner_context_rejected(builder,args,expected,context):
    with pytest.raises(ValueError):
        builder(*('0' for _ in args),tag='invalid',variables=context)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('term',('undeclared','p -> p','p = 0','p; true','',None,7,False))
def test_invalid_horner_term_rejected(builder,args,expected,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='invalid',variables=args)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('tag',('bad tag','forall','S','',None,False))
def test_invalid_horner_tag_rejected(builder,args,expected,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


PRINCIPAL_CONTRACTS = {
    'prime_field_polynomial_horner_canonical_step':f"forall p n t a r s. ({expected_prime('p')}) -> ({expected_lt('t','p')}) -> ({expected_lt('a','p')}) -> ({expected_residue('p','n','r')}) -> ({expected_residue('p','n*t+a','s')}) -> exists k. {expected_and(expected_field_mul('p','r','t','k'),expected_field_add('p','k','a','s'))}",
    'prime_field_polynomial_horner_trace_from_normalization':f"forall p b c t l n u v U V. ({expected_prime('p')}) -> ({expected_coeff('p','b','c','l')}) -> ({expected_lt('t','p')}) -> ({expected_natural_trace('b','c','t','l','n','u','v')}) -> ({expected_normalization('p','u','v','U','V','S l')}) -> exists r. {expected_and(expected_trace('p','b','c','t','l','r','U','V'),expected_residue('p','n','r'))}",
    'prime_field_polynomial_horner_exists':f"forall p b c t l. ({expected_prime('p')}) -> ({expected_coeff('p','b','c','l')}) -> ({expected_lt('t','p')}) -> exists r. ({expected_eval('p','b','c','t','l','r')})",
    'prime_field_polynomial_horner_input_bounds':f"forall p b c t l r. ({expected_eval('p','b','c','t','l','r')}) -> {expected_and(expected_lt('t','p'),expected_coeff('p','b','c','l'))}",
    'prime_field_polynomial_horner_empty':f"forall p b c t r. ({expected_eval('p','b','c','t','0','r')}) -> r=0",
    'prime_field_polynomial_horner_successor_decompose':f"forall p b c t l r. ({expected_eval('p','b','c','t','S l','r')}) -> exists a h k. {expected_and(expected_at('b','c','l','a'),expected_eval('p','b','c','t','l','h'),expected_field_mul('p','h','t','k'),expected_field_add('p','k','a','r'))}",
    'prime_field_polynomial_horner_transport':f"forall p b c B C t l r. ({expected_equal('b','c','B','C','l')}) -> ({expected_eval('p','b','c','t','l','r')}) -> ({expected_eval('p','B','C','t','l','r')})",
    'prime_field_polynomial_horner_normalization_residue':f"forall p b c d e t l n r. ({expected_prime('p')}) -> ({expected_normalization('p','b','c','d','e','l')}) -> ({expected_natural('b','c','t','l','n')}) -> ({expected_eval('p','d','e','t','l','r')}) -> ({expected_residue('p','n','r')})",
    'prime_field_polynomial_horner_residue':f"forall p b c t l n r. ({expected_prime('p')}) -> ({expected_natural('b','c','t','l','n')}) -> ({expected_eval('p','b','c','t','l','r')}) -> ({expected_residue('p','n','r')})",
    'prime_field_polynomial_horner_functional':f"forall p b c t l r s. ({expected_prime('p')}) -> ({expected_eval('p','b','c','t','l','r')}) -> ({expected_eval('p','b','c','t','l','s')}) -> r=s",
    'prime_field_polynomial_horner_exists_unique':f"forall p b c t l. ({expected_prime('p')}) -> ({expected_coeff('p','b','c','l')}) -> ({expected_lt('t','p')}) -> exists r. ({expected_eval('p','b','c','t','l','r')}) /\\ forall s. ({expected_eval('p','b','c','t','l','s')}) -> s=r",
    'prime_field_polynomial_horner_empty_construct':f"forall p b c t. ({expected_prime('p')}) -> ({expected_lt('t','p')}) -> ({expected_eval('p','b','c','t','0','0')})",
    'prime_field_polynomial_horner_successor_construct':f"forall p b c t l a h k r. ({expected_prime('p')}) -> ({expected_at('b','c','l','a')}) -> ({expected_eval('p','b','c','t','l','h')}) -> ({expected_field_mul('p','h','t','k')}) -> ({expected_field_add('p','k','a','r')}) -> ({expected_eval('p','b','c','t','S l','r')})",
    'prime_field_polynomial_horner_constant':f"forall p b c t a. ({expected_prime('p')}) -> ({expected_lt('t','p')}) -> ({expected_lt('a','p')}) -> ({expected_at('b','c','0','a')}) -> ({expected_eval('p','b','c','t','1','a')})",
    'prime_field_polynomial_horner_zero':f"forall p b c t l. ({expected_prime('p')}) -> ({expected_lt('t','p')}) -> ({expected_repeat('b','c','0','l')}) -> ({expected_eval('p','b','c','t','l','0')})",
    'prime_field_polynomial_normalized_horner_iff':f"forall p b c d e t l n r. ({expected_prime('p')}) -> ({expected_normalization('p','b','c','d','e','l')}) -> ({expected_lt('t','p')}) -> ({expected_natural('b','c','t','l','n')}) -> {expected_and('('+expected_eval('p','d','e','t','l','r')+') -> ('+expected_residue('p','n','r')+')','('+expected_residue('p','n','r')+') -> ('+expected_eval('p','d','e','t','l','r')+')')}",
    'prime_field_polynomial_horner_result_bounded':f"forall p b c t l r. ({expected_prime('p')}) -> ({expected_eval('p','b','c','t','l','r')}) -> ({expected_lt('r','p')})",
    'prime_field_polynomial_reduce_and_evaluate_exists':f"forall p b c t l. ({expected_prime('p')}) -> ({expected_lt('t','p')}) -> exists d e r. {expected_and(expected_normalization('p','b','c','d','e','l'),expected_eval('p','d','e','t','l','r'),'forall n. ('+expected_natural('b','c','t','l','n')+') -> ('+expected_residue('p','n','r')+')')}",
}


@pytest.mark.parametrize('name,expected',tuple(PRINCIPAL_CONTRACTS.items()),ids=tuple(PRINCIPAL_CONTRACTS))
def test_every_horner_statement_matches_its_independent_exact_contract(name,expected):
    row = next(r for r in rows() if r.name == name)
    same_ast(_closed_formula(row.statement),_closed_formula(expected))


def test_natural_horner_reuse_is_exactly_old_t12_not_a_new_result_invariant_definition():
    same_ast(_closed_formula('forall b c t l n. '+candidate._natural('b','c','t','l','n','reuse')),_closed_formula('forall b c t l n. '+expected_natural('b','c','t','l','n')))
    source = Path(candidate.__file__).read_text()
    graph_source = source[source.index('def _step('):source.index('def _natural(')]
    assert '_residue' not in graph_source and '_natural' not in graph_source
    assert '_field_mul' in graph_source and '_field_add' in graph_source


GUARD_CASES = {
    'noncanonical_base':('prime_field_polynomial_horner_exists',f"forall p b c t l. ({expected_prime('p')}) -> ({expected_coeff('p','b','c','l')}) -> 0=0 -> exists r. ({expected_eval('p','b','c','t','l','r')})"),
    'noncanonical_coefficients':('prime_field_polynomial_horner_exists',f"forall p b c t l. ({expected_prime('p')}) -> 0=0 -> ({expected_lt('t','p')}) -> exists r. ({expected_eval('p','b','c','t','l','r')})"),
    'wrong_empty_result':('prime_field_polynomial_horner_empty',f"forall p b c t r. ({expected_eval('p','b','c','t','0','r')}) -> r=1"),
    'wrong_initial_state':('prime_field_polynomial_horner_empty',f"forall p b c t r. ({expected_eval('p','b','c','t','0','r',initial='1')}) -> r=0"),
    'wrong_constant_result':('prime_field_polynomial_horner_constant',f"forall p b c t a. ({expected_prime('p')}) -> ({expected_lt('t','p')}) -> ({expected_lt('a','p')}) -> ({expected_at('b','c','0','a')}) -> ({expected_eval('p','b','c','t','1','t')})"),
    'wrong_horner_order':('prime_field_polynomial_horner_constant',f"forall p b c t a. ({expected_prime('p')}) -> ({expected_lt('t','p')}) -> ({expected_lt('a','p')}) -> ({expected_at('b','c','0','a')}) -> ({expected_eval('p','b','c','t','1','a',wrong_order=True)})"),
    'unrelated_coefficient_codes':('prime_field_polynomial_horner_normalization_residue',f"forall p b c d e t l n r. ({expected_prime('p')}) -> 0=0 -> ({expected_natural('b','c','t','l','n')}) -> ({expected_eval('p','d','e','t','l','r')}) -> ({expected_residue('p','n','r')})"),
    'wrong_natural_order':('prime_field_polynomial_horner_residue',f"forall p b c t l n r. ({expected_prime('p')}) -> ({expected_natural('b','c','t','l','n',wrong_order=True)}) -> ({expected_eval('p','b','c','t','l','r')}) -> ({expected_residue('p','n','r')})"),
}


@pytest.mark.parametrize('mutation',tuple(GUARD_CASES))
def test_horner_proofs_reject_wrong_guards_states_order_or_source_alignment(mutation):
    assert fresh('--guard','evaluation',mutation)['rejected'] == mutation


def horner_values(coefficients,t,p=None):
    values = [0]
    for a in coefficients:
        value = values[-1]*t+a
        values.append(value if p is None else value%p)
    return tuple(values)


def model_trace(p,coefficients,t,length,result,trace):
    if not (0<=t<p and decode_beta(trace,0)==0 and decode_beta(trace,length)==result):
        return False
    for i in range(length):
        a,h,j = decode_beta(coefficients,i),decode_beta(trace,i),decode_beta(trace,i+1)
        if not (0<=a<p and 0<=h<p and 0<=j<p):
            return False
        product = h*t%p
        if (product+a)%p != j:
            return False
    return True


@pytest.mark.parametrize('p',(2,3,5,7,11))
@pytest.mark.parametrize('raw',((),(0,),(1,),(0,0,0),(2,3,4),(19,0,7,25),(2**96+17,2**80+3),(0,0,1,0,2)))
def test_actual_beta_horner_traces_reduction_reencoding_and_all_canonical_bases(p,raw):
    source = encode_beta(raw)
    reduced = tuple(a%p for a in raw)
    coefficients,recoded = encode_beta(reduced),encode_beta(reduced,3)
    assert model_normalization(p,source,coefficients,len(raw))
    for t in range(p):
        natural = horner_values(raw,t)
        states = horner_values(reduced,t,p)
        assert states == tuple(value%p for value in natural)
        trace,other_trace = encode_beta(states),encode_beta(states,2)
        assert trace != other_trace
        assert decoded_prefix(trace,len(states)) == states
        assert model_trace(p,coefficients,t,len(raw),states[-1],trace)
        assert model_trace(p,recoded,t,len(raw),states[-1],other_trace)
        assert 0<=states[-1]<p and states[-1]==natural[-1]%p
        for i,a in enumerate(reduced):
            assert model_trace(p,coefficients,t,i,states[i],trace)
            product = states[i]*t%p
            assert states[i+1] == (product+a)%p


def test_real_empty_constant_zero_and_wrong_trace_boundaries():
    for p in (2,3,7):
        for t in range(p):
            assert model_trace(p,encode_beta(()),t,0,0,encode_beta((0,)))
            assert not model_trace(p,encode_beta(()),t,0,1,encode_beta((1,)))
            for a in range(p):
                assert model_trace(p,encode_beta((a,)),t,1,a,encode_beta((0,a)))
            zero = encode_beta((0,0,0,0))
            assert model_trace(p,zero,t,4,0,encode_beta((0,0,0,0,0)))
        assert not model_trace(p,encode_beta(()),p,0,0,encode_beta((0,)))
        assert not model_trace(p,encode_beta((p,)),0,1,0,encode_beta((0,0)))
    assert not model_trace(0,encode_beta(()),0,0,0,encode_beta((0,)))


def test_highest_degree_first_is_distinguished_from_reverse_or_weighted_sum_order():
    p,t,coefficients = 7,5,(2,3,4)
    actual = horner_values(coefficients,t,p)
    assert actual[-1] == (2*5**2+3*5+4)%7 == 6
    assert horner_values(tuple(reversed(coefficients)),t,p)[-1] == 5
    wrong = (0,3,4,3)  # repeatedly h+a*t modulo seven
    assert not model_trace(p,encode_beta(coefficients),t,3,wrong[-1],encode_beta(wrong))
    assert model_trace(p,encode_beta(coefficients),t,3,6,encode_beta(actual))


def test_representation_length_is_not_degree_or_polynomial_function_uniqueness():
    assert horner_values((0,0,2,3),4,7)[-1] == horner_values((2,3),4,7)[-1]
    assert len((0,0,2,3)) != len((2,3))
    # X^2+X is the zero function on F2, but not the zero coefficient vector.
    nonzero,zero = encode_beta((1,1,0)),encode_beta((0,0,0))
    assert decoded_prefix(nonzero,3) != decoded_prefix(zero,3)
    assert all(horner_values((1,1,0),t,2)[-1] == horner_values((0,0,0),t,2)[-1] for t in range(2))
