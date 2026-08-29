"""Exact signed table-operation contracts and ordinary HA body regressions."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from math import factorial, gcd
import re

import pytest

from peano_lab.library import signed_table_operations_candidate as candidate
from peano_lab.library.arithmetic_table_extension_candidate import make_arithmetic_table_extension_candidate_theorems
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.divisor_sum_table_candidate import make_divisor_sum_table_candidate_theorems
from peano_lab.library.divisor_sum_algebra_candidate import make_divisor_sum_algebra_candidate_theorems
from peano_lab.library.divisor_sum_reindex_candidate import make_divisor_sum_reindex_candidate_theorems
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_mobius_value_candidate import core as parent
from tests.test_divisor_sum_table_candidate import _assert_same_ast, _expected_entry, _expected_table
from peano_lab.library.prime_valuation_support_candidate import _and


EXPECTED=((27,18),(42,23),(102,30),(98,33),(36,24),(78,34),(102,30),(98,33),
          (36,24),(78,34),(70,25),(74,28),(33,22),(63,31),(150,46),(113,36),(31,20),
          (150,46),(113,36),(31,20),(114,40),(91,32),(28,19))
ROOT_PINS={
    'signed_table_add_exists_extensionally_unique':'993d774742a26b57c7d03d6d8c483fa0d69fd36e785e0eb72385c989bf1a3065',
    'signed_table_multiply_exists_extensionally_unique':'e545ed562de151ca5c6f0be2092ebe7f0383df70d418340b78e384c4fe856fae',
    'signed_table_scalar_exists_extensionally_unique':'ab9954f8f2a293ddade9a4cfff5ba1b94d62d0f32d68c8628130ee518a425f82',
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_signed_table_operations_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    factories=(make_divisor_sum_table_candidate_theorems,make_divisor_sum_algebra_candidate_theorems,
               make_divisor_sum_reindex_candidate_theorems,make_arithmetic_table_extension_candidate_theorems)
    return parent() | {row.name:row for factory in factories for row in factory(TheoremSpec)}


@pytest.mark.parametrize('row',rows(),ids=lambda r:r.name)
def test_original_kernel_body(row):
    try:
        report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==EXPECTED[rows().index(row)]
        assert report.proof_objects<=report.proof_nodes
        assert report.proof_depth<=256
    finally:
        gc.collect()


def test_additive_native_topology_and_used_dependencies():
    available=set(core())
    assert len(rows())==23
    assert sum(len(r.dependencies) for r in rows())==68
    assert sum(len(r.script) for r in rows())==1150
    assert sha256('\n'.join(r.name for r in rows()).encode()).hexdigest()=='06433139260ea75cf25eb87c6fbdb276bef3a6a2312aa0c05171bd7301e5a336'
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)
    assert {r.name:sha256(r.statement.encode()).hexdigest() for r in rows() if r.name in ROOT_PINS}==ROOT_PINS


@pytest.mark.parametrize('row',rows(),ids=lambda r:r.name)
def test_false_target_fails_original_kernel(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{r.name:r for r in rows()})


DEPENDENCIES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda v:v.name if hasattr(v,'name') else v)
def test_dropped_dependency_cannot_be_used(row,dependency):
    altered=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda v:v.name if hasattr(v,'name') else v)
def test_poisoned_dependency_cannot_substitute_for_exact_statement(row,dependency):
    table=core()|{r.name:r for r in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


def _expected_decode(z,p,n,tag):
    h='model_half_'+tag
    return f'((({z})=2*({p}) /\\ ({n})=0) \\/ exists {h}. ((({z})=2*{h}+1 /\\ ({p})=0) /\\ ({n})=S {h}))'


def expected_signed_operation(a,b,c,*,multiply):
    equation=('(ap*bp+an*bn)+cn=(ap*bn+an*bp)+cp' if multiply else '(ap+bp)+cn=(an+bn)+cp')
    return 'exists ap an bp bn cp cn. '+_and(_expected_decode(a,'ap','an','left'),_expected_decode(b,'bp','bn','right'),_expected_decode(c,'cp','cn','output'),equation)


def expected_binary(F,G,H,l,*,multiply):
    entry=_and(_expected_entry(F,'i','u'),_expected_entry(G,'i','v'),_expected_entry(H,'i','w'),expected_signed_operation('u','v','w',multiply=multiply))
    return _and(_expected_table(l,F),_expected_table(l,G),_expected_table(l,H),
                f'forall i. (exists gap. gap+S i=({l})) -> exists u v w. ({entry})')


def expected_scalar(a,F,G,l):
    entry=_and(_expected_entry(F,'i','u'),_expected_entry(G,'i','v'),expected_signed_operation(a,'u','v',multiply=True))
    return _and(_expected_table(l,F),_expected_table(l,G),
                f'forall i. (exists gap. gap+S i=({l})) -> exists u v. ({entry})')


def expected_table_equal(F,G,l):
    return f'forall i u v. (exists gap. gap+S i=({l})) -> ({_expected_entry(F,"i","u")}) -> ({_expected_entry(G,"i","v")}) -> u=v'


SURFACES=(
    (candidate.signed_table_pointwise_add_relation,('F','G','H','l'),False),
    (candidate.signed_table_pointwise_multiply_relation,('F','G','H','l'),True),
    (candidate.signed_table_scalar_multiply_relation,('a','F','G','l'),None),
)


@pytest.mark.parametrize('kind',('add','multiply','scalar'))
@pytest.mark.parametrize('unique',(False,True))
def test_principal_table_constructors_have_no_supplied_output_or_choice_premise(kind,unique):
    scalar=kind=='scalar'
    symbols=('a','F') if scalar else ('F','G')
    inputs=('F',) if scalar else ('F','G')
    relation=lambda output:expected_scalar('a','F',output,'l') if scalar else expected_binary('F','G',output,'l',multiply=kind=='multiply')
    result=relation('H')
    if unique:result=_and(result,f'forall K. ({relation("K")}) -> ({expected_table_equal("H","K","l")})')
    formula='forall '+' '.join(('l',*symbols))+'. '+' -> '.join('('+_expected_table('l',table)+')' for table in inputs)+' -> exists H. ('+result+')'
    name='signed_table_'+kind+'_exists'+('_extensionally_unique' if unique else '')
    _assert_same_ast(_closed_formula(formula),_closed_formula(next(r.statement for r in rows() if r.name==name)))


@pytest.mark.parametrize('builder,arguments,multiply',SURFACES)
@pytest.mark.parametrize('mode',('identifiers','compound','huge','zero','repeated'))
def test_independently_expanded_public_graphs(builder,arguments,multiply,mode):
    context=('a','F','G','H','l')
    values=arguments
    if mode=='compound':values=tuple(value+'+1' if i%2==0 else value+'*'+value for i,value in enumerate(arguments))
    if mode=='huge':values=('9999999999999999999999999999999999999999',*arguments[1:])
    if mode=='zero':values=('0',)*4
    if mode=='repeated':values=('F','F','F','l')
    actual=builder(*values,tag='contract',variables=context)
    expected=expected_scalar(*values) if multiply is None else expected_binary(*values,multiply=multiply)
    _assert_same_ast(_closed_formula('forall '+' '.join(context)+'. '+actual),_closed_formula('forall '+' '.join(context)+'. '+expected))


@pytest.mark.parametrize('builder,arguments,multiply',SURFACES)
def test_all_generated_binders_reject_full_context_capture(builder,arguments,multiply):
    context=('a','F','G','H','l')
    source=builder(*arguments,tag='capture',variables=context)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}
    assert binders and not binders.intersection(context)
    for name in binders:
        with pytest.raises(ValueError):
            builder(*arguments,tag='capture',variables=context+(name,))


@pytest.mark.parametrize('builder,arguments,multiply',SURFACES)
@pytest.mark.parametrize('malformed',('unknown','syntax','empty-context','duplicate-context','missing-context','reserved-tag'))
def test_malformed_terms_or_contexts_rejected(builder,arguments,multiply,malformed):
    context=('a','F','G','H','l');tag='bad'
    if malformed=='unknown':arguments=('missing',*arguments[1:])
    if malformed=='syntax':arguments=('F -> G',*arguments[1:])
    if malformed=='empty-context':context=()
    if malformed=='duplicate-context':context=context+('F',)
    if malformed=='missing-context':context=context[:-1]
    if malformed=='reserved-tag':tag='forall'
    with pytest.raises(ValueError):
        builder(*arguments,tag=tag,variables=context)


def encode_signed(value):
    return 2*value if value>=0 else -2*value-1


def decode_signed(code):
    return code//2 if code%2==0 else -(code//2+1)


def beta_stream(values):
    """Independent finite CRT construction of actual natural beta entries."""
    values=tuple(values)
    if not values:return (0,1)
    scale=factorial(len(values))*(max(values)+1)
    moduli=tuple(1+(i+1)*scale for i in range(len(values)))
    product=1
    for modulus in moduli:
        assert gcd(product,modulus)==1
        product*=modulus
    code=sum(value*(product//modulus)*pow(product//modulus,-1,modulus)
             for value,modulus in zip(values,moduli,strict=True))%product
    assert tuple(code%modulus for modulus in moduli)==values
    return code,scale


def model_table(values,offset=0,endpoint=0):
    values=(*tuple(values),endpoint)
    positive=tuple(max(value,0)+offset for value in values)
    negative=tuple(max(-value,0)+offset for value in values)
    pb,pc=beta_stream(positive);nb,nc=beta_stream(negative)
    pair=lambda a,b:(a+b)*(a+b+1)+2*b
    return pair(pair(pb,pc),pair(nb,nc)),(pb,pc,nb,nc)


def model_at(table,index):
    _,(pb,pc,nb,nc)=table
    return encode_signed(pb%(1+(index+1)*pc)-nb%(1+(index+1)*nc))


def model_sum(table,length):
    _,(pb,pc,nb,nc)=table
    return encode_signed(sum(pb%(1+(i+1)*pc) for i in range(length))-sum(nb%(1+(i+1)*nc) for i in range(length)))


@pytest.mark.parametrize('left,right',(((),()),((0,),(0,)),((2,),(-3,)),((-4,1),(6,-8)),((3,-1,0),(2,5,-7))))
@pytest.mark.parametrize('scalar',(-3,-1,0,1,4))
def test_actual_beta_models_do_not_identify_table_representatives(left,right,scalar):
    first=model_table(left,offset=3,endpoint=991)
    second=model_table(right,offset=7,endpoint=-997)
    added=tuple(a+b for a,b in zip(left,right,strict=True))
    multiplied=tuple(a*b for a,b in zip(left,right,strict=True))
    scaled=tuple(scalar*a for a in left)
    for values in (added,multiplied,scaled):
        a=model_table(values,offset=5,endpoint=13)
        b=model_table(values,offset=11,endpoint=-19)
        assert a[0]!=b[0] and a[1]!=b[1]
        assert [model_at(a,i) for i in range(len(values))]==[model_at(b,i) for i in range(len(values))]
        assert model_sum(a,len(values))==model_sum(b,len(values))==encode_signed(sum(values))
    assert decode_signed(model_sum(model_table(added),len(left)))==decode_signed(model_sum(first,len(left)))+decode_signed(model_sum(second,len(right)))


if __name__=='__main__':
    import argparse,json,resource,signal,sys,time
    parser=argparse.ArgumentParser();parser.add_argument('--body');parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int,default=4);parser.add_argument('--pytest-select')
    arguments=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    if arguments.pytest_select is not None:
        status=pytest.main(['-q',__file__,'-k',arguments.pytest_select])
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        assert peak<=1536*1024*1024
        print(json.dumps({'pytest_status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
        raise SystemExit(status)
    selected=tuple(r for r in rows() if r.name==arguments.body) if arguments.body else rows()[arguments.start:arguments.start+arguments.count]
    if not selected:raise SystemExit('unknown theorem body')
    for row in selected:
        report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==EXPECTED[rows().index(row)]
        print(json.dumps({'name':row.name,'nodes':report.proof_nodes,'depth':report.proof_depth,'objects':report.proof_objects}),flush=True)
        gc.collect()
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'bodies':len(selected),'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
