"""Original-HA authoring and exact contracts for real affine signed slices."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
import re

import pytest

from peano_lab.library import signed_rectangular_slice_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.library.prime_valuation_support_candidate import _and
from tests.test_divisor_sum_table_candidate import _assert_same_ast,_expected_entry,_expected_sum,_expected_table
from tests.test_signed_table_operations_candidate import model_table,model_at,model_sum,beta_stream,encode_signed,decode_signed
from tests.test_signed_weighted_sum_candidate import core as previous_core,rows as weighted_rows


EXPECTED=((42,21),(61,29),(34,23),(105,44),(97,36),(82,29),(31,21),(29,14),
          (85,48),(27,17),(31,15),(60,28),(75,30),(68,29),(31,21))
ROOT_PINS={
    'signed_rectangular_slice_exists_extensionally_unique':'d0fbe7f70725333cc208f00e860d04886fafdc5fef4a36bc6e811dd88391ddd4',
    'signed_rectangular_slice_sum_exists_unique':'f107eddb02016e9261c9f110f0ee226c8c19190739e2820b53f6f804a474a128',
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_signed_rectangular_slice_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return previous_core()|{row.name:row for row in weighted_rows()}


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
    assert (report.proof_nodes,report.proof_depth)==EXPECTED[rows().index(row)]
    assert report.proof_objects<=report.proof_nodes
    assert report.proof_depth<=256
    gc.collect()


def test_native_topology_and_exact_declared_dependencies():
    available=set(core())
    assert len(rows())==15
    assert sum(len(row.dependencies) for row in rows())==37
    assert sum(len(row.script) for row in rows())==523
    assert sha256('\n'.join(row.name for row in rows()).encode()).hexdigest()=='5508e204355d5687ac5d980bf7697dd5cbeafef5101d1e2ccde7bcc3163ddced'
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


def _instantiate(template,arguments,tag):
    """Alpha-rename the independent old primitives BEFORE inserting terms.

    In particular a free rectangle dimension named n must never be captured by
    the historical component model's local negative-component binder n.
    """
    binders=tuple(dict.fromkeys(name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',template) for name in clause.split()))
    renamed={name:'model_'+tag+'_'+str(index) for index,name in enumerate(binders)}
    source=re.sub(r"\b[A-Za-z_][A-Za-z_0-9']*",lambda match:renamed.get(match.group(),match.group()),template)
    return re.sub(r"\b[A-Za-z_][A-Za-z_0-9']*",lambda match:'('+arguments[match.group()]+')' if match.group() in arguments else match.group(),source)


def expected_table(N,F,tag):
    return _instantiate(_expected_table('DOMAIN','SOURCE'),{'DOMAIN':N,'SOURCE':F},tag)


def expected_entry(F,i,z,tag):
    return _instantiate(_expected_entry('SOURCE','INDEX','VALUE'),{'SOURCE':F,'INDEX':i,'VALUE':z},tag)


def expected_sum(F,l,z,tag):
    return _instantiate(_expected_sum('SOURCE','LENGTH','VALUE'),{'SOURCE':F,'LENGTH':l,'VALUE':z},tag)


def expected_slice(F,G,o,s,l,tag):
    i,z='model_slice_index_'+tag,'model_slice_value_'+tag
    bound=f'exists model_slice_gap_{tag}. model_slice_gap_{tag}+S {i}=({l})'
    entry=_and(expected_entry(F,f'({o})+({s})*{i}',z,tag+'input'),expected_entry(G,i,z,tag+'output'))
    return _and(expected_table('0',F,tag+'source'),expected_table(l,G,tag+'target'),f'forall {i}. ({bound}) -> exists {z}. ({entry})')


def expected_slice_sum(F,o,s,l,z,tag):
    G='model_slice_table_'+tag
    return f'exists {G}. '+_and(expected_slice(F,G,o,s,l,tag+'slice'),expected_sum(G,l,z,tag+'sum'))


SURFACES=(
    (candidate.signed_rectangular_slice_relation,('F','G','o','s','l'),expected_slice),
    (candidate.signed_rectangular_slice_sum_relation,('F','o','s','l','z'),expected_slice_sum),
)


@pytest.mark.parametrize('builder,arguments,expected',SURFACES)
@pytest.mark.parametrize('mode',('identifiers','compound','huge','zero','repeated'))
def test_independently_expanded_affine_graphs(builder,arguments,expected,mode):
    context=('F','G','o','s','l','z')
    values=arguments
    if mode=='compound':values=tuple(value+'+1' if index%2==0 else value+'*'+value for index,value in enumerate(arguments))
    if mode=='huge':values=('9999999999999999999999999999999999999999',*arguments[1:])
    if mode=='zero':values=('0',)*5
    if mode=='repeated':values=('F',)*5
    actual=builder(*values,tag='contract',variables=context)
    formula=expected(*values,'independent')
    _assert_same_ast(_closed_formula('forall '+' '.join(context)+'. '+actual),_closed_formula('forall '+' '.join(context)+'. '+formula))


@pytest.mark.parametrize('builder,arguments,expected',SURFACES)
def test_every_generated_binder_rejects_capture_in_the_entire_context(builder,arguments,expected):
    context=('F','G','o','s','l','z')
    source=builder(*arguments,tag='capture',variables=context)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}
    assert binders and not binders.intersection(context)
    for name in binders:
        with pytest.raises(ValueError):builder(*arguments,tag='capture',variables=context+(name,))


@pytest.mark.parametrize('builder,arguments,expected',SURFACES)
@pytest.mark.parametrize('malformed',('unknown','syntax','empty-context','duplicate-context','missing-context','reserved-tag'))
def test_bad_terms_and_contexts_are_not_definition_oracles(builder,arguments,expected,malformed):
    context=('F','G','o','s','l','z');tag='bad'
    if malformed=='unknown':arguments=('missing',*arguments[1:])
    if malformed=='syntax':arguments=('F -> G',*arguments[1:])
    if malformed=='empty-context':context=()
    if malformed=='duplicate-context':context=context+('F',)
    if malformed=='missing-context':context=context[1:]
    if malformed=='reserved-tag':tag='forall'
    with pytest.raises(ValueError):builder(*arguments,tag=tag,variables=context)


@pytest.mark.parametrize('name',tuple(ROOT_PINS))
def test_slice_principals_construct_their_own_outputs_without_choice(name):
    if name=='signed_rectangular_slice_exists_extensionally_unique':
        equality=(f"forall i a b. (exists gap. gap+S i=l) -> ({expected_entry('G','i','a','equalfirst')}) -> "
                  f"({expected_entry('H','i','b','equalsecond')}) -> a=b")
        target='exists G. '+_and(expected_slice('F','G','o','s','l','constructed'),
                                 f"forall H. ({expected_slice('F','H','o','s','l','other')}) -> ({equality})")
    else:
        target='exists z. '+_and(expected_slice_sum('F','o','s','l','z','constructed'),
                                 f"forall w. ({expected_slice_sum('F','o','s','l','w','other')}) -> w=z")
    formula=f"forall F o s l. ({expected_table('0','F','source')}) -> ({target})"
    _assert_same_ast(_closed_formula(formula),_closed_formula(next(row.statement for row in rows() if row.name==name)))


def actual_sum_trace(table,length):
    """Diagnostic construction of the actual two natural cumulative traces."""
    _,(pb,pc,nb,nc)=table
    positive=[0];negative=[0]
    for index in range(length):
        positive.append(positive[-1]+pb%(1+(index+1)*pc))
        negative.append(negative[-1]+nb%(1+(index+1)*nc))
    bp,cp=beta_stream(positive);bn,cn=beta_stream(negative)
    assert bp%(1+cp)==bn%(1+cn)==0
    for index in range(length):
        assert bp%(1+(index+2)*cp)==bp%(1+(index+1)*cp)+pb%(1+(index+1)*pc)
        assert bn%(1+(index+2)*cn)==bn%(1+(index+1)*cn)+nb%(1+(index+1)*nc)
    result=encode_signed(bp%(1+(length+1)*cp)-bn%(1+(length+1)*cn))
    assert result==model_sum(table,length)
    return result


@pytest.mark.parametrize('offset,stride,length',((0,0,0),(4,3,0),(0,0,3),(2,0,4),(0,1,1),(0,1,4),(3,2,4),(1,3,3)))
def test_actual_beta_slice_traces_include_empty_zero_stride_and_distinct_encodings(offset,stride,length):
    extent=offset+stride*max(length-1,0)+1
    values=tuple((-1 if i%2 else 1)*(i+2) for i in range(extent))
    source=model_table(values,offset=7,endpoint=997)
    samples=tuple(decode_signed(model_at(source,offset+stride*i)) for i in range(length))
    first=model_table(samples,offset=11,endpoint=991)
    second=model_table(samples,offset=19,endpoint=-991)
    assert first[0]!=second[0] and first[1]!=second[1]
    for i in range(length):assert model_at(first,i)==model_at(second,i)==model_at(source,offset+stride*i)
    assert actual_sum_trace(first,length)==actual_sum_trace(second,length)==encode_signed(sum(samples))
    assert model_at(first,length)!=model_at(second,length)
    if length==0:assert actual_sum_trace(first,0)==0


class BoundedTestSelection:
    """Select a contiguous post--k authoring batch; never change proof limits."""
    def __init__(self,start,count):
        if start<0 or count<=0:raise ValueError('test batch must be a nonempty positive range')
        self.start,self.count=start,count

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self,config,items):
        selected=items[self.start:self.start+self.count]
        if not selected:raise pytest.UsageError('the requested bounded test batch is empty')
        omitted=items[:self.start]+items[self.start+self.count:]
        config.hook.pytest_deselected(items=omitted)
        items[:]=selected


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
