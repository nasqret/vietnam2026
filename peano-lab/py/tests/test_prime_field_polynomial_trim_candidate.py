"""Independent trim contracts, actual beta examples, and conditional HA checks.

The body checks introduce exact inherited statements as ordinary hypotheses.
They are not complete dependency-bundle, Lean, admission or closed-root checks.
Run this file's bounded CLI for fresh authoring windows; no kernel limits or
historical implementation are changed.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re
import resource
import signal
import sys
import time

import pytest

from peano_lab.library import prime_field_polynomial_trim_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula
from test_prime_field_polynomial_candidate import (
    decode_beta, decoded_prefix, encode_beta, expected_and, expected_at,
    expected_coeff, expected_equal, expected_lt, expected_repeat, same_ast,
)


ROOT = Path(__file__).resolve().parents[3]
MAX_RSS_BYTES = 1536 * 1024 * 1024
SOURCE_SHA256 = '1125c02fd11646efaa20963380ba1086e18551f2c89b242b8900a8043d358e4c'
EXPECTED_NAMES = (
    'prime_field_polynomial_suffix_exists',
    'prime_field_polynomial_suffix_entry',
    'prime_field_polynomial_suffix_bounded',
    'prime_field_polynomial_suffix_equal',
    'prime_field_polynomial_leading_zero_cut_exists',
    'prime_field_polynomial_trim_from_cut',
    'prime_field_polynomial_trim_exists',
    'prime_field_polynomial_trim_empty_input',
    'prime_field_polynomial_trim_output_coefficients',
    'prime_field_polynomial_trim_length_bounds',
    'prime_field_polynomial_trim_leading_source_nonzero',
    'prime_field_polynomial_trim_zero_of_empty',
    'prime_field_polynomial_trim_empty_of_zero',
    'prime_field_polynomial_trim_zero_iff',
    'prime_field_polynomial_trim_removed_le',
    'prime_field_polynomial_trim_removed_count_unique',
    'prime_field_polynomial_trim_retained_length_unique',
    'prime_field_polynomial_trim_output_equal',
    'prime_field_polynomial_trim_exists_unique',
    'prime_field_polynomial_trim_represented_degree',
    'prime_field_polynomial_trim_nonempty_degree_exists',
    'prime_field_polynomial_trim_represented_identity',
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_trim_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    # Exact ordinary factory data, not asserted truth or a reinterpreted saved
    # receipt. Only these statements enter the dependency-curried body target.
    # Full inherited-body closure is explicitly a later, separate obligation.
    from peano_lab.library.matrix_coded_product_candidate import make_matrix_coded_product_candidate_theorems
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems
    from peano_lab.library.matrix_recursive_determinant_extensional_candidate import make_matrix_recursive_determinant_extensional_candidate_theorems
    old = (*THEOREMS,
           *make_matrix_coded_product_candidate_theorems(TheoremSpec),
           *make_matrix_rank_finite_coding_candidate_theorems(TheoremSpec),
           *make_matrix_recursive_determinant_extensional_candidate_theorems(TheoremSpec))
    available = {}
    for row in old:
        if row.name in available:
            assert available[row.name] == row
        available[row.name] = row
    wanted = {name for row in rows() for name in row.dependencies} - set(EXPECTED_NAMES)
    assert wanted <= available.keys()
    return {name: available[name] for name in wanted} | {row.name: row for row in rows()}


def expected_le(a,b):
    return f'exists independent_trim_gap. independent_trim_gap+({a})=({b})'


def expected_suffix(b,c,t,d,e,length):
    i,a = 'independent_trim_index','independent_trim_value'
    return (f'forall {i} {a}. ({expected_lt(i,length)}) -> '
            f'({expected_at(b,c,f"({t})+{i}",a)}) -> ({expected_at(d,e,i,a)})')


def expected_head(b,c,index):
    a='independent_nonzero_coefficient'
    return f'exists {a}. '+expected_and(expected_at(b,c,index,a),f'~({a}=0)')


def expected_cut(b,c,length,t,m):
    return expected_and(f'({length})=({t})+({m})',expected_repeat(b,c,'0',t),
        f'({m})=0 \\/ ({expected_and(f"~(({m})=0)",expected_head(b,c,t))})')


def expected_trim(p,b,c,length,t,d,e,m,*,removed=True,normal=True):
    return expected_and(f'({length})=({t})+({m})',expected_coeff(p,b,c,length),
        expected_repeat(b,c,'0',t) if removed else '0=0',expected_suffix(b,c,t,d,e,m),
        f'({m})=0 \\/ ({expected_head(d,e,"0")})' if normal else '0=0')


def expected_degree(p,b,c,length,q):
    return expected_and(f'({length})=S ({q})',expected_coeff(p,b,c,length),expected_head(b,c,'0'))


PARAMETERS=('p','b','c','L','t','d','e','M')
OTHER=('p','b','c','L','u','f','g','N')
ALL=(*PARAMETERS,'u','f','g','N')
HYPOTHESES=f'({expected_trim(*PARAMETERS)}) -> ({expected_trim(*OTHER)}) -> '
ZERO_INPUT=expected_repeat('b','c','0','L')
UNIQUE_VALUES=expected_and('t=u','M=N',expected_equal('d','e','f','g','M'))
UNIQUE_COMPARISON=f'forall u f g N. ({expected_trim(*OTHER)}) -> ({UNIQUE_VALUES})'
CONTRACTS={
    'prime_field_polynomial_suffix_exists':f'forall b c t M. exists d e. ({expected_suffix("b","c","t","d","e","M")})',
    'prime_field_polynomial_suffix_entry':f'forall b c t d e M i a r. ({expected_suffix("b","c","t","d","e","M")}) -> ({expected_lt("i","M")}) -> ({expected_at("b","c","t+i","a")}) -> ({expected_at("d","e","i","r")}) -> r=a',
    'prime_field_polynomial_suffix_bounded':f'forall {" ".join(PARAMETERS)}. L=t+M -> ({expected_coeff("p","b","c","L")}) -> ({expected_suffix("b","c","t","d","e","M")}) -> ({expected_coeff("p","d","e","M")})',
    'prime_field_polynomial_suffix_equal':f'forall b c t d e f g M. ({expected_suffix("b","c","t","d","e","M")}) -> ({expected_suffix("b","c","t","f","g","M")}) -> ({expected_equal("d","e","f","g","M")})',
    'prime_field_polynomial_leading_zero_cut_exists':f'forall b c L. exists t M. ({expected_cut("b","c","L","t","M")})',
    'prime_field_polynomial_trim_from_cut':f'forall {" ".join(PARAMETERS)}. ({expected_coeff("p","b","c","L")}) -> ({expected_cut("b","c","L","t","M")}) -> ({expected_suffix("b","c","t","d","e","M")}) -> ({expected_trim(*PARAMETERS)})',
    'prime_field_polynomial_trim_exists':f'forall p b c L. ({expected_coeff("p","b","c","L")}) -> exists t d e M. ({expected_trim(*PARAMETERS)})',
    'prime_field_polynomial_trim_empty_input':f'forall p b c d e. ({expected_trim("p","b","c","0","0","d","e","0")})',
    'prime_field_polynomial_trim_output_coefficients':f'forall {" ".join(PARAMETERS)}. ({expected_trim(*PARAMETERS)}) -> ({expected_coeff("p","d","e","M")})',
    'prime_field_polynomial_trim_length_bounds':f'forall {" ".join(PARAMETERS)}. ({expected_trim(*PARAMETERS)}) -> ({expected_and(expected_le("t","L"),expected_le("M","L"))})',
    'prime_field_polynomial_trim_leading_source_nonzero':f'forall {" ".join(PARAMETERS)} a. ({expected_trim(*PARAMETERS)}) -> ~(M=0) -> ({expected_at("b","c","t","a")}) -> ~(a=0)',
    'prime_field_polynomial_trim_zero_of_empty':f'forall {" ".join(PARAMETERS)}. ({expected_trim(*PARAMETERS)}) -> M=0 -> ({expected_repeat("b","c","0","L")})',
    'prime_field_polynomial_trim_empty_of_zero':f'forall {" ".join(PARAMETERS)}. ({expected_trim(*PARAMETERS)}) -> ({expected_repeat("b","c","0","L")}) -> M=0',
    'prime_field_polynomial_trim_zero_iff':f'forall {" ".join(PARAMETERS)}. ({expected_trim(*PARAMETERS)}) -> '+expected_and(f'M=0 -> ({ZERO_INPUT})',f'({ZERO_INPUT}) -> M=0'),
    'prime_field_polynomial_trim_removed_le':f'forall {" ".join(ALL)}. {HYPOTHESES}({expected_le("t","u")})',
    'prime_field_polynomial_trim_removed_count_unique':f'forall {" ".join(ALL)}. {HYPOTHESES}t=u',
    'prime_field_polynomial_trim_retained_length_unique':f'forall {" ".join(ALL)}. {HYPOTHESES}M=N',
    'prime_field_polynomial_trim_output_equal':f'forall {" ".join(ALL)}. {HYPOTHESES}({expected_equal("d","e","f","g","M")})',
    'prime_field_polynomial_trim_exists_unique':f'forall p b c L. ({expected_coeff("p","b","c","L")}) -> exists t d e M. ({expected_and(expected_trim(*PARAMETERS),UNIQUE_COMPARISON)})',
    'prime_field_polynomial_trim_represented_degree':f'forall {" ".join(PARAMETERS)} q. ({expected_trim(*PARAMETERS)}) -> M=S q -> ({expected_degree("p","d","e","M","q")})',
    'prime_field_polynomial_trim_nonempty_degree_exists':f'forall {" ".join(PARAMETERS)}. ({expected_trim(*PARAMETERS)}) -> ~(M=0) -> exists q. ({expected_degree("p","d","e","M","q")})',
    'prime_field_polynomial_trim_represented_identity':f'forall p b c L q. ({expected_degree("p","b","c","L","q")}) -> ({expected_trim("p","b","c","L","0","b","c","L")})',
}


PUBLIC_CASES=(
    (candidate.prime_field_polynomial_suffix_relation,('b','c','t','d','e','M'),expected_suffix),
    (candidate.prime_field_polynomial_trim_relation,PARAMETERS,expected_trim),
)


def test_exact_inventory_and_ordinary_dependency_order():
    assert tuple(row.name for row in rows())==EXPECTED_NAMES
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest()==SOURCE_SHA256
    assert sum(len(row.dependencies) for row in rows())==51
    assert sum(len(row.script) for row in rows())==971
    assert set(CONTRACTS)==set(EXPECTED_NAMES)
    available=set(core())-set(EXPECTED_NAMES)
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in available
        assert row.script and len(set(row.dependencies))==len(row.dependencies)
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\x27])'+re.escape(dep)+r'(?![\w\x27])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry')) or 'DNE' in command for command in row.script)
        available.add(row.name)


@pytest.mark.parametrize('name',EXPECTED_NAMES)
def test_every_closed_theorem_matches_an_independent_actual_contract(name):
    row=next(row for row in rows() if row.name==name)
    same_ast(_closed_formula(row.statement),_closed_formula(CONTRACTS[name]))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES,ids=('suffix','trim'))
def test_public_graph_is_exactly_the_independent_coefficient_relation(builder,args,expected):
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*args,tag='independent',variables=args)),_closed_formula(binder+expected(*args)))


COMPOUNDS=tuple((builder,args,expected,index,term) for builder,args,expected in PUBLIC_CASES
                for index in range(len(args)) for term in (f'({args[0]})+S ({args[-1]})',str(2**90+7)))


@pytest.mark.parametrize('builder,args,expected,index,term',COMPOUNDS,
                         ids=tuple(f'compound-{i:03d}' for i in range(len(COMPOUNDS))))
def test_every_public_argument_preserves_compound_and_large_numeral_terms(builder,args,expected,index,term):
    values=(*args[:index],term,*args[index+1:])
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*values,tag='compound',variables=args)),_closed_formula(binder+expected(*values)))


CAPTURES=tuple((builder,args,binder) for builder,args,_ in PUBLIC_CASES
    for binder in sorted({name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',builder(*args,tag='capture',variables=args)) for name in clause.split()}))


@pytest.mark.parametrize('builder,args,binder',CAPTURES,
                         ids=tuple(f'capture-{i:03d}' for i in range(len(CAPTURES))))
def test_every_generated_binder_rejects_used_and_unused_whole_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=args+(binder,))
    with pytest.raises(ValueError,match='captures'):
        builder(f'{args[0]}+{binder}',*args[1:],tag='capture',variables=args+(binder,))


@pytest.mark.parametrize('builder,args,_',PUBLIC_CASES,ids=('suffix','trim'))
@pytest.mark.parametrize('context',((),[],('p','p'),('bad name',),('forall',)))
def test_invalid_context_rejected(builder,args,_,context):
    with pytest.raises(ValueError):
        builder(*('0' for _ in args),tag='invalid',variables=context)


@pytest.mark.parametrize('builder,args,_',PUBLIC_CASES,ids=('suffix','trim'))
@pytest.mark.parametrize('term',('undeclared','p -> p','p=0','p; true','',None,7,False))
def test_invalid_argument_rejected(builder,args,_,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='invalid',variables=args)


@pytest.mark.parametrize('builder,args,_',PUBLIC_CASES,ids=('suffix','trim'))
@pytest.mark.parametrize('tag',('bad tag','forall','S','',None,False))
def test_invalid_tag_rejected(builder,args,_,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


@pytest.mark.parametrize('name',EXPECTED_NAMES)
def test_each_actual_body_passes_the_original_conditional_ha_checker(name):
    row=core()[name]
    receipt=replay_candidate_bodies((row,),core=core())[0]
    assert receipt.name==name
    assert receipt.proof_nodes>0 and receipt.proof_depth<=256
    assert 0<receipt.proof_objects<=receipt.proof_nodes


@pytest.mark.parametrize('name',EXPECTED_NAMES)
@pytest.mark.parametrize('kind',('false_conclusion','truncated_body'))
def test_actual_bodies_reject_false_conclusions_and_truncated_scripts(name,kind):
    row=core()[name]
    mutant=replace(row,statement=f'({row.statement}) /\\ false') if kind=='false_conclusion' else replace(row,script=row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutant,),core=core())


EDGES=tuple((row.name,index,dep) for row in rows() for index,dep in enumerate(row.dependencies))


@pytest.mark.parametrize('name,index,dependency',EDGES,ids=tuple(f'edge-{i:03d}' for i in range(len(EDGES))))
def test_every_declared_dependency_is_needed_when_dropped(name,index,dependency):
    row=core()[name]
    assert row.dependencies[index]==dependency
    mutant=replace(row,dependencies=row.dependencies[:index]+row.dependencies[index+1:])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutant,),core=core())


@pytest.mark.parametrize('name,index,dependency',EDGES,ids=tuple(f'edge-{i:03d}' for i in range(len(EDGES))))
def test_every_declared_dependency_rejects_an_unrelated_true_statement(name,index,dependency):
    row=core()[name]
    assert row.dependencies[index]==dependency
    poisoned=core()|{dependency:replace(core()[dependency],statement='0=0')}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=poisoned)


GUARDS={
    'missing_canonical_input':('prime_field_polynomial_trim_exists',f'forall p b c L. exists t d e M. ({expected_trim(*PARAMETERS)})'),
    'output_beyond_retained_prefix':('prime_field_polynomial_trim_output_coefficients',f'forall {" ".join(PARAMETERS)}. ({expected_trim(*PARAMETERS)}) -> ({expected_coeff("p","d","e","S M")})'),
    'nonzero_at_empty_output':('prime_field_polynomial_trim_leading_source_nonzero',f'forall {" ".join(PARAMETERS)} a. ({expected_trim(*PARAMETERS)}) -> ({expected_at("b","c","t","a")}) -> ~(a=0)'),
    'raw_beta_codes_are_unique':('prime_field_polynomial_trim_output_equal',f'forall {" ".join(ALL)}. {HYPOTHESES}d=f /\\ e=g'),
    'zero_polynomial_has_degree':('prime_field_polynomial_trim_nonempty_degree_exists',f'forall {" ".join(PARAMETERS)}. ({expected_trim(*PARAMETERS)}) -> exists q. ({expected_degree("p","d","e","M","q")})'),
    'missing_normal_head':('prime_field_polynomial_trim_removed_count_unique',f'forall {" ".join(ALL)}. ({expected_trim(*PARAMETERS,normal=False)}) -> ({expected_trim(*OTHER,normal=False)}) -> t=u'),
    'missing_removed_zeroes':('prime_field_polynomial_trim_removed_count_unique',f'forall {" ".join(ALL)}. ({expected_trim(*PARAMETERS,removed=False)}) -> ({expected_trim(*OTHER,removed=False)}) -> t=u'),
    'wrong_degree_is_input_predecessor':('prime_field_polynomial_trim_represented_degree',f'forall {" ".join(PARAMETERS)} q. ({expected_trim(*PARAMETERS)}) -> L=S q -> ({expected_degree("p","d","e","M","q")})'),
}


@pytest.mark.parametrize('mutation',tuple(GUARDS))
def test_proofs_reject_weakened_guards_and_wrong_normalization_claims(mutation):
    name,statement=GUARDS[mutation]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(core()[name],statement=statement),),core=core())


def model_trim(p,source,length,removed,output,retained,*,normal=True,zeroes=True):
    return (length==removed+retained and all(decode_beta(source,i)<p for i in range(length))
            and (not zeroes or all(decode_beta(source,i)==0 for i in range(removed)))
            and all(decode_beta(output,i)==decode_beta(source,removed+i) for i in range(retained))
            and (not normal or retained==0 or decode_beta(output,0)!=0))


EXAMPLES=((),(0,),(1,),(0,0),(0,1),(0,0,1),(1,0,0),(0,1,0,1),(0,0,0,0))


@pytest.mark.parametrize('p',(2,3,5,7))
@pytest.mark.parametrize('values',EXAMPLES,ids=tuple(f'coefficients-{i:02d}' for i in range(len(EXAMPLES))))
def test_actual_beta_trims_exist_with_leading_order_zero_cases_and_nonunique_encodings(p,values):
    removed=next((i for i,a in enumerate(values) if a),len(values))
    tail=values[removed:]
    source=encode_beta(values)
    first,second=encode_beta(tail),encode_beta(tail,3)
    assert model_trim(p,source,len(values),removed,first,len(tail))
    assert model_trim(p,source,len(values),removed,second,len(tail))
    assert decoded_prefix(first,len(tail))==decoded_prefix(second,len(tail))==tail
    assert first!=second
    for cut in range(len(values)+1):
        for retained in range(len(values)+2):
            alternative=encode_beta(values[cut:])
            if model_trim(p,source,len(values),cut,alternative,retained):
                assert cut==removed and retained==len(tail)
                assert decoded_prefix(alternative,retained)==tail


@pytest.mark.parametrize('p',(0,1,2,4,7))
@pytest.mark.parametrize('source,output',(((0,0),(0,0)),((7,2),(23,9)),((1,0),(8,3))))
def test_empty_input_allows_arbitrary_codes_and_every_modulus(p,source,output):
    assert model_trim(p,source,0,0,output,0)
    assert all(not model_trim(p,source,0,t,output,m) for t,m in ((0,1),(1,0),(1,1)))


def test_zero_and_composite_moduli_do_not_hide_a_prime_assumption():
    assert model_trim(0,(0,0),0,0,(999,31),0)
    assert not model_trim(0,encode_beta((0,)),1,1,(0,0),0)
    source=encode_beta((0,0,3,2))
    assert model_trim(4,source,4,2,encode_beta((3,2)),2)
    source=encode_beta((0,0,0))
    assert model_trim(1,source,3,3,(23,7),0)


def test_actual_beta_counterexamples_justify_each_critical_guard():
    zeros=encode_beta((0,0))
    assert model_trim(2,zeros,2,2,(123,9),0)
    assert not model_trim(2,zeros,2,0,zeros,2)
    assert model_trim(2,zeros,2,0,zeros,2,normal=False)
    nonzero=encode_beta((1,1))
    assert model_trim(2,nonzero,2,0,nonzero,2)
    assert not model_trim(2,nonzero,2,1,encode_beta((1,)),1)
    assert model_trim(2,nonzero,2,1,encode_beta((1,)),1,zeroes=False)
    # Correct finite suffix, deliberately noncanonical tail outside it.
    source=encode_beta((0,1))
    output=encode_beta((1,99))
    assert model_trim(2,source,2,1,output,1)
    assert decode_beta(output,1)==99
    assert not model_trim(2,encode_beta((2,)),1,0,encode_beta((2,)),1)


@pytest.mark.parametrize('p',(2,3,5))
@pytest.mark.parametrize('values',((1,),(1,0),(0,1),(0,0,1),(0,1,0,1)))
def test_retained_length_gives_exact_represented_degree_but_zero_has_none(p,values):
    removed=next(i for i,a in enumerate(values) if a)
    tail=values[removed:]
    output=encode_beta(tail,2)
    assert model_trim(p,encode_beta(values),len(values),removed,output,len(tail))
    degree=len(tail)-1
    assert len(tail)==degree+1 and decode_beta(output,0)!=0
    assert all(decode_beta(output,i)<p for i in range(len(tail)))
    if removed:
        assert degree!=len(values)-1
    assert all(0!=q+1 for q in range(12))


# Exact AST novelty against Alpha3796 + non-admitted G00990 is performed by
# the shared prerequisite-tranche test over all85 new rows.  This focused
# file deliberately does not import a duplicate large Alpha metadata model.


def _main(arguments):
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    started=time.monotonic()
    if arguments[:1]==['--bodies']:
        start=int(arguments[1]) if len(arguments)>1 else 0
        count=int(arguments[2]) if len(arguments)>2 else len(rows())
        chosen=rows()[start:start+count]
        assert chosen
        for row in chosen:
            receipt=replay_candidate_bodies((row,),core=core())[0]
            print(json.dumps(asdict(receipt),sort_keys=True),flush=True)
        status=0
    elif arguments[:1]==['--pytest']:
        status=int(pytest.main([str(Path(__file__).resolve()),*arguments[1:]]))
    else:
        raise SystemExit('expected --bodies [START [COUNT]] or --pytest [PYTEST ARGUMENTS]')
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert 0<peak<=MAX_RSS_BYTES
    assert time.monotonic()-started<=180
    print(json.dumps({'status':status,'seconds':time.monotonic()-started,'cpu_seconds':time.process_time(),
        'peak_rss_bytes':peak,'cpu_limits':list(resource.getrlimit(resource.RLIMIT_CPU)),
        'wall_alarm_seconds':180}),flush=True)
    signal.alarm(0)
    return status


if __name__=='__main__':
    raise SystemExit(_main(sys.argv[1:]))
