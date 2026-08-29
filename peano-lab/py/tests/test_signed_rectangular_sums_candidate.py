"""Ordinary-kernel and independently stated contracts for finite signed Fubini."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import pytest

from peano_lab.library import signed_rectangular_sums_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.library.prime_valuation_support_candidate import _and
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_signed_rectangular_slice_candidate import (
    core as slice_core,rows as slice_rows,expected_table,expected_entry,expected_sum,
    expected_slice_sum,actual_sum_trace,BoundedTestSelection,
)
from tests.test_signed_table_operations_candidate import model_table,model_at,encode_signed,decode_signed


EXPECTED=((44,23),(63,31),(36,25),(131,54),(99,38),(93,33),(37,25),(33,18),(95,54),
          (37,25),(29,19),(149,39),(51,30),(144,48),(213,48),(100,34),(47,27))
ROOT_PINS={
    'signed_rectangular_row_sums_exists_extensionally_unique':'569840ec13f17c1453d77ba6fe32c85f118240b2fdba55d5ef035fa8b249e5f5',
    'signed_rectangular_sum_exists_unique':'9b245f658835b10db273dc4753e86e65be5eccc6d2f4e7d29eea62663a0c9833',
    'signed_rectangular_fubini':'74787482d51c759b2472790323be3c54494bbf97fab08de48afce458898fd14d',
    'signed_rectangular_fubini_exists':'438e430f2b7689b3318149e7112187f3611e7eb3c0147e76479fb5aec365f819',
    'signed_rectangular_row_major_fubini':'df286640d573e43c4ce8fc84ed9a405eb4568577f4f683001adb7ae8324ff3ec',
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_signed_rectangular_sums_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return slice_core()|{row.name:row for row in slice_rows()}


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
    assert (report.proof_nodes,report.proof_depth)==EXPECTED[rows().index(row)]
    assert report.proof_objects<=report.proof_nodes
    assert report.proof_depth<=256
    gc.collect()


def test_native_topology_and_exact_declared_dependencies():
    available=set(core())
    assert len(rows())==17
    assert sum(len(row.dependencies) for row in rows())==55
    assert sum(len(row.script) for row in rows())==870
    assert sha256('\n'.join(row.name for row in rows()).encode()).hexdigest()=='fe63f731aa38ac09a0fe5144a7394a58e8e2193a0d8003ca63f12015867ee948'
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)
    assert {row.name:sha256(row.statement.encode()).hexdigest() for row in rows() if row.name in ROOT_PINS}==ROOT_PINS


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_fails_the_original_kernel(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{r.name:r for r in rows()})


DEPENDENCIES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_dropped_dependency_cannot_be_used(row,dependency):
    changed=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_poisoned_dependency_cannot_replace_its_actual_statement(row,dependency):
    table=core()|{r.name:r for r in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


def expected_rows(F,R,o,s,t,m,n,tag):
    i,z='model_row_index_'+tag,'model_row_value_'+tag
    bound=f'exists model_row_gap_{tag}. model_row_gap_{tag}+S {i}=({m})'
    entry=_and(expected_entry(R,i,z,tag+'entry'),expected_slice_sum(F,f'({o})+({s})*{i}',t,n,z,tag+'row'))
    return _and(expected_table('0',F,tag+'source'),expected_table(m,R,tag+'table'),f'forall {i}. ({bound}) -> exists {z}. ({entry})')


def expected_rectangle(F,o,s,t,m,n,z,tag):
    R='model_rows_'+tag
    return f'exists {R}. '+_and(expected_rows(F,R,o,s,t,m,n,tag+'rows'),expected_sum(R,m,z,tag+'sum'))


def expected_fubini_witnesses(F,R,C,o,s,t,m,n,z,tag):
    return _and(expected_rows(F,R,o,s,t,m,n,tag+'rows'),expected_rows(F,C,o,t,s,n,m,tag+'columns'),
                expected_sum(R,m,z,tag+'row_sum'),expected_sum(C,n,z,tag+'column_sum'))


SURFACES=(
    (candidate.signed_rectangular_row_sums_relation,('F','R','o','s','t','m','n'),expected_rows),
    (candidate.signed_rectangular_sum_relation,('F','o','s','t','m','n','z'),expected_rectangle),
)


@pytest.mark.parametrize('builder,arguments,expected',SURFACES)
@pytest.mark.parametrize('mode',('identifiers','compound','huge','zero','repeated'))
def test_independently_expanded_rectangular_graphs(builder,arguments,expected,mode):
    context=('F','R','o','s','t','m','n','z')
    values=arguments
    if mode=='compound':values=tuple(value+'+1' if index%2==0 else value+'*'+value for index,value in enumerate(arguments))
    if mode=='huge':values=('9999999999999999999999999999999999999999',*arguments[1:])
    if mode=='zero':values=('0',)*7
    if mode=='repeated':values=('F',)*7
    actual=builder(*values,tag='contract',variables=context)
    _assert_same_ast(_closed_formula('forall '+' '.join(context)+'. '+actual),
                     _closed_formula('forall '+' '.join(context)+'. '+expected(*values,'independent')))


@pytest.mark.parametrize('builder,arguments,expected',SURFACES)
def test_every_generated_binder_rejects_capture_in_the_entire_context(builder,arguments,expected):
    context=('F','R','o','s','t','m','n','z')
    source=builder(*arguments,tag='capture',variables=context)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}
    assert binders and not binders.intersection(context)
    for name in binders:
        with pytest.raises(ValueError):builder(*arguments,tag='capture',variables=context+(name,))


@pytest.mark.parametrize('builder,arguments,expected',SURFACES)
@pytest.mark.parametrize('malformed',('unknown','syntax','empty-context','duplicate-context','missing-context','reserved-tag'))
def test_bad_terms_and_contexts_are_not_definition_oracles(builder,arguments,expected,malformed):
    context=('F','R','o','s','t','m','n','z');tag='bad'
    if malformed=='unknown':arguments=('missing',*arguments[1:])
    if malformed=='syntax':arguments=('F -> R',*arguments[1:])
    if malformed=='empty-context':context=()
    if malformed=='duplicate-context':context=context+('F',)
    if malformed=='missing-context':context=context[1:]
    if malformed=='reserved-tag':tag='forall'
    with pytest.raises(ValueError):builder(*arguments,tag=tag,variables=context)


@pytest.mark.parametrize('name',tuple(ROOT_PINS))
def test_principals_have_actual_row_column_tables_and_no_sum_oracle(name):
    source=expected_table('0','F','source')
    quantifiers='forall F o s t m n. '
    if name=='signed_rectangular_row_sums_exists_extensionally_unique':
        equal=(f"forall i a b. (exists gap. gap+S i=m) -> ({expected_entry('R','i','a','equalfirst')}) -> "
               f"({expected_entry('Q','i','b','equalsecond')}) -> a=b")
        target='exists R. '+_and(expected_rows('F','R','o','s','t','m','n','constructed'),
                                 f"forall Q. ({expected_rows('F','Q','o','s','t','m','n','other')}) -> ({equal})")
        formula=quantifiers+f'({source}) -> ({target})'
    elif name=='signed_rectangular_sum_exists_unique':
        target='exists z. '+_and(expected_rectangle('F','o','s','t','m','n','z','constructed'),
                                 f"forall w. ({expected_rectangle('F','o','s','t','m','n','w','other')}) -> w=z")
        formula=quantifiers+f'({source}) -> ({target})'
    elif name=='signed_rectangular_fubini':
        formula=(f"forall m F o s t n a b. ({expected_rectangle('F','o','s','t','m','n','a','rows')}) -> "
                 f"({expected_rectangle('F','o','t','s','n','m','b','columns')}) -> a=b")
    elif name=='signed_rectangular_fubini_exists':
        formula=quantifiers+f"({source}) -> exists R C z. ({expected_fubini_witnesses('F','R','C','o','s','t','m','n','z','witnesses')})"
    else:
        formula=f"forall F m n. ({expected_table('m*n','F','source')}) -> exists R C z. ({expected_fubini_witnesses('F','R','C','0','n','1','m','n','z','rowmajor')})"
    _assert_same_ast(_closed_formula(formula),_closed_formula(next(row.statement for row in rows() if row.name==name)))


@pytest.mark.parametrize('outer', (True,False))
def test_both_zero_dimensions_are_unconditionally_covered(outer):
    if outer:
        name='signed_rectangular_sum_zero_outer';variables='F o s t n z';m,n='0','n'
    else:
        name='signed_rectangular_sum_zero_inner';variables='F o s t m z';m,n='m','0'
    formula=f"forall {variables}. ({expected_rectangle('F','o','s','t',m,n,'z','zero')}) -> z=0"
    _assert_same_ast(_closed_formula(formula),_closed_formula(next(row.statement for row in rows() if row.name==name)))


@pytest.mark.parametrize('m,n',((0,0),(0,3),(4,0),(1,1),(2,3),(3,2),(3,3),(1,4)))
@pytest.mark.parametrize('o,s,t',((0,1,1),(2,3,1),(0,0,2),(1,2,0),(3,0,0)))
def test_actual_beta_rows_columns_and_cumulative_traces_agree(m,n,o,s,t):
    extent=o+s*max(m-1,0)+t*max(n-1,0)+1
    values=tuple((-1 if i%2 else 1)*(i+2) for i in range(extent))
    source=model_table(values,offset=17,endpoint=313)
    row_values=[];column_values=[]
    for i in range(m):
        samples=tuple(decode_signed(model_at(source,(o+s*i)+t*j)) for j in range(n))
        extracted=model_table(samples,offset=5+i,endpoint=991)
        assert all(model_at(extracted,j)==model_at(source,(o+s*i)+t*j) for j in range(n))
        row_values.append(decode_signed(actual_sum_trace(extracted,n)))
    for j in range(n):
        samples=tuple(decode_signed(model_at(source,(o+t*j)+s*i)) for i in range(m))
        extracted=model_table(samples,offset=11+j,endpoint=-997)
        assert all(model_at(extracted,i)==model_at(source,(o+t*j)+s*i) for i in range(m))
        column_values.append(decode_signed(actual_sum_trace(extracted,m)))
    row_table=model_table(row_values,offset=7,endpoint=997)
    column_table=model_table(column_values,offset=19,endpoint=-991)
    other_row_table=model_table(row_values,offset=23,endpoint=-313)
    assert row_table[0]!=other_row_table[0] and row_table[1]!=other_row_table[1]
    assert actual_sum_trace(row_table,m)==actual_sum_trace(other_row_table,m)==actual_sum_trace(column_table,n)
    assert actual_sum_trace(row_table,m)==encode_signed(sum(values[o+s*i+t*j] for i in range(m) for j in range(n)))
    if m==0 or n==0:assert actual_sum_trace(row_table,m)==0


def test_all_32_statement_asts_are_distinct_from_every_3518_prior_statement():
    root=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(root/'scripts'))
    import constructive_lower_continuation_support as support
    from peano_lab.library import campaign_bottom_layer_closure as closure
    import constructive_bottom_layer_checkpoints as first
    import constructive_lower_tier_checkpoints as second
    assert len(closure.parent_snapshot().specs)==3222
    assert sum(item.frontier_count for item in first.CHECKPOINTS)==170
    assert len(second.all_new_rows())==126
    assert support.statement_duplicates((*slice_rows(),*rows()))==()


if __name__=='__main__':
    import argparse,resource,signal,sys,time
    parser=argparse.ArgumentParser();parser.add_argument('--body');parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int,default=3);parser.add_argument('--pytest-select');parser.add_argument('--case-start',type=int,default=0);parser.add_argument('--case-count',type=int)
    arguments=parser.parse_args();resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    if arguments.pytest_select is not None:
        plugins=[] if arguments.case_count is None else [BoundedTestSelection(arguments.case_start,arguments.case_count)]
        status=pytest.main(['-q',__file__,'-k',arguments.pytest_select],plugins=plugins)
    else:
        selected=tuple(row for row in rows() if row.name==arguments.body) if arguments.body else rows()[arguments.start:arguments.start+arguments.count]
        if not selected:raise SystemExit('unknown theorem body')
        for row in selected:
            report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
            assert (report.proof_nodes,report.proof_depth)==EXPECTED[rows().index(row)]
            print(json.dumps({'name':row.name,'nodes':report.proof_nodes,'depth':report.proof_depth,'objects':report.proof_objects}),flush=True)
            gc.collect()
        status=0
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
