"""Actual convolution graphs and ordinary dependency-curried HA bodies."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
from itertools import accumulate
from pathlib import Path
import re
import sys

import pytest

ROOT=Path(__file__).resolve().parents[3]
if str(ROOT/'scripts') not in sys.path:
    sys.path.insert(0,str(ROOT/'scripts'))

from constructive_lower_continuation_support import closure, previous_rows
from constructive_lower_continuation_checkpoints import all_new_rows
from peano_lab.library import dirichlet_convolution_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.finite_sum_theorems import _sum_relation_terms
from peano_lab.library.gaussian_euclidean_candidate import _balance
from peano_lab.library.prime_valuation_support_candidate import _at
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_divisor_sum_reindex_candidate import _encode_beta, _lookup, _table_code, _unpair


def _conjoin(*clauses):
    result=clauses[-1]
    for clause in reversed(clauses[:-1]):
        result=f'({clause}) /\\ ({result})'
    return result


def _model_pair(a,b):
    return f'(({a})+({b}))*S(({a})+({b}))+(({b})+({b}))'


def _model_names(tag,*roles):
    return tuple('independent_'+role+'_'+tag for role in roles)


def expected_le(a,b,tag):
    gap,=_model_names(tag,'gap')
    return f'exists {gap}. {gap}+({a})=({b})'


def expected_dvd(d,n,tag):
    quotient,=_model_names(tag,'divisor_quotient')
    return f'exists {quotient}. ({n})=({d})*{quotient}'


def expected_at(F,i,z,tag):
    pb,pc,nb,nc,p,n=_model_names(tag,'pb','pc','nb','nc','positive','negative')
    packed=_model_pair(_model_pair(pb,pc),_model_pair(nb,nc))
    return f'exists {pb} {pc} {nb} {nc} {p} {n}. '+_conjoin(
        f'({F})=({packed})',_at(pb,pc,i,p,'independent_'+tag+'positive'),
        _at(nb,nc,i,n,'independent_'+tag+'negative'),_balance(z,p,n,'independent_'+tag+'value'))


def expected_table(N,F,tag):
    pb,pc,nb,nc,i,p,n,z=_model_names(tag,'pb','pc','nb','nc','index','positive','negative','value')
    packed=_model_pair(_model_pair(pb,pc),_model_pair(nb,nc))
    value=_conjoin(_at(pb,pc,i,p,'independent_'+tag+'positive'),
                   _at(nb,nc,i,n,'independent_'+tag+'negative'),_balance(z,p,n,'independent_'+tag+'value'))
    return f'exists {pb} {pc} {nb} {nc}. '+_conjoin(
        f'({F})=({packed})',f'forall {i}. ({expected_le(i,N,tag+"bound")}) -> exists {p} {n} {z}. ({value})')


def expected_signed_sum(F,l,z,tag):
    pb,pc,nb,nc,p,n=_model_names(tag,'pb','pc','nb','nc','positive_sum','negative_sum')
    packed=_model_pair(_model_pair(pb,pc),_model_pair(nb,nc))
    return f'exists {pb} {pc} {nb} {nc} {p} {n}. '+_conjoin(
        f'({F})=({packed})',_sum_relation_terms(pb,pc,l,p,tag='independent_'+tag+'positive'),
        _sum_relation_terms(nb,nc,l,n,tag='independent_'+tag+'negative'),
        _balance(z,p,n,'independent_'+tag+'value'))


def expected_signed_multiply(a,b,c,tag):
    ap,an,bp,bn,cp,cn=_model_names(tag,'ap','an','bp','bn','cp','cn')
    def decode(z,p,n,suffix):
        h,=_model_names(tag+suffix,'half')
        return f'((({z})=2*({p}) /\\ ({n})=0) \\/ exists {h}. ((({z})=2*{h}+1 /\\ ({p})=0) /\\ ({n})=S {h}))'
    return f'exists {ap} {an} {bp} {bn} {cp} {cn}. '+_conjoin(
        decode(a,ap,an,'first'),decode(b,bp,bn,'second'),decode(c,cp,cn,'product'),
        f'({ap}*{bp}+{an}*{bn})+{cn}=({ap}*{bn}+{an}*{bp})+{cp}')


def expected_entry(F,G,n,d,z,tag):
    """Independent literal summand graph; no production convolution builder."""
    q,a,b=_model_names(tag,'quotient','left','right')
    active=_conjoin(f'~(({d})=0)',f'exists {q} {a} {b}. '+_conjoin(
        f'({n})=({d})*{q}',expected_at(F,d,a,tag+'left'),
        expected_at(G,q,b,tag+'right'),expected_signed_multiply(a,b,z,tag+'product')))
    omitted=_conjoin(f'({d})=0 \\/ ~({expected_dvd(d,n,tag+"nondivisor")})',f'({z})=0')
    return f'({active}) \\/ ({omitted})'


def expected_prefix(F,G,n,l,M,tag):
    d,z=_model_names(tag,'index','entry')
    return _conjoin(expected_table(l,M,tag+'table'),
        f'forall {d} {z}. ({expected_le(d,l,tag+"bound")}) -> '
        f'({expected_at(M,d,z,tag+"lookup")}) -> ({expected_entry(F,G,n,d,z,tag+"entry")})')


def expected_convolution(F,G,n,z,tag):
    M,=_model_names(tag,'mask')
    return _conjoin(f'~(({n})=0)',f'exists {M}. '+_conjoin(
        expected_prefix(F,G,n,n,M,tag+'prefix'),expected_signed_sum(M,f'S ({n})',z,tag+'sum')))


def expected_convolution_table(N,F,G,H,tag):
    n,z=_model_names(tag,'input','output')
    return _conjoin(expected_table(N,F,tag+'left'),expected_table(N,G,tag+'right'),
        expected_table(N,H,tag+'output'),f'forall {n} {z}. ~({n}=0) -> '
        f'({expected_le(n,N,tag+"bound")}) -> ({expected_at(H,n,z,tag+"lookup")}) -> '
        f'({expected_convolution(F,G,n,z,tag+"value")})')


def expected_positive_equal(F,G,N,tag):
    d,a,b=_model_names(tag,'index','first','second')
    return (f'forall {d} {a} {b}. ~({d}=0) -> ({expected_le(d,N,tag+"bound")}) -> '
            f'({expected_at(F,d,a,tag+"first")}) -> ({expected_at(G,d,b,tag+"second")}) -> {a}={b}')


def expected_equal(F,G,l,tag):
    d,a,b=_model_names(tag,'index','first','second')
    return (f'forall {d} {a} {b}. ({expected_le("S "+d,l,tag+"bound")}) -> '
            f'({expected_at(F,d,a,tag+"first")}) -> ({expected_at(G,d,b,tag+"second")}) -> {a}={b}')


def expected_statements():
    """Every new theorem, independently assembled without factory formulas."""
    counter=0
    def tagged(function):
        def call(*args):
            nonlocal counter
            counter+=1
            return function(*args,tag='statement_'+str(counter))
        return call
    T,A,E,P,C,CT,L,D,M,PE,EQ=(tagged(function) for function in (
        expected_table,expected_at,expected_entry,expected_prefix,expected_convolution,
        expected_convolution_table,expected_le,expected_dvd,expected_signed_multiply,
        expected_positive_equal,expected_equal))
    def all_(names,*clauses):
        return 'forall '+names+'. '+' -> '.join('('+clause+')' for clause in clauses)
    def exists(names,*clauses):
        return 'exists '+names+'. '+_conjoin(*clauses)
    omitted=lambda d,n:f'({d})=0 \\/ ~({D(d,n)})'
    positive=lambda n:f'~(({n})=0)'
    statements={
        'entry_zero':all_('F G n',E('F','G','n','0','0')),
        'entry_from_quotient':all_('F G n d q a b z',positive('d'),'n=d*q',A('F','d','a'),A('G','q','b'),M('a','b','z'),E('F','G','n','d','z')),
        'entry_from_nondivisor':all_('F G n d',f'~({D("d","n")})',E('F','G','n','d','0')),
        'entry_omitted_value':all_('F G n d z',omitted('d','n'),E('F','G','n','d','z'),'z=0'),
        'entry_quotient_product':all_('F G n d q a b z',positive('d'),'n=d*q',A('F','d','a'),A('G','q','b'),E('F','G','n','d','z'),M('a','b','z')),
        'entry_functional':all_('F G n d u v',E('F','G','n','d','u'),E('F','G','n','d','v'),'u=v'),
        'entry_exists':all_('F G n d',T('0','F'),T('0','G'),exists('z',E('F','G','n','d','z'))),
        'prefix_zero_constructor':all_('F G n M',T('0','M'),A('M','0','0'),P('F','G','n','0','M')),
        'prefix_append':all_('F G n l M z',P('F','G','n','l','M'),E('F','G','n','S l','z'),exists('H',P('F','G','n','S l','H'),EQ('M','H','S l'))),
        'prefix_exists':all_('F G n l',T('0','F'),T('0','G'),exists('M',P('F','G','n','l','M'))),
        'prefix_lookup':all_('F G n l M d z',P('F','G','n','l','M'),L('d','l'),A('M','d','z'),E('F','G','n','d','z')),
        'prefix_extensional':all_('F G n l M K',P('F','G','n','l','M'),P('F','G','n','l','K'),EQ('M','K','S l')),
        'prefix_restrict':all_('F G n l k M',P('F','G','n','l','M'),L('k','l'),P('F','G','n','k','M')),
        'prefix_quotient_entry':all_('F G n l M d q a b z',P('F','G','n','l','M'),L('d','l'),positive('d'),'n=d*q',A('F','d','a'),A('G','q','b'),M('a','b','z'),A('M','d','z')),
        'prefix_omitted_entry':all_('F G n l M d',P('F','G','n','l','M'),L('d','l'),omitted('d','n'),A('M','d','0')),
        'sum_exists':all_('N F G n',T('N','F'),T('N','G'),positive('n'),L('n','N'),exists('z',C('F','G','n','z'))),
        'sum_functional':all_('F G n a b',C('F','G','n','a'),C('F','G','n','b'),'a=b'),
        'sum_exists_unique':all_('N F G n',T('N','F'),T('N','G'),positive('n'),L('n','N'),exists('z',C('F','G','n','z'),all_('w',C('F','G','n','w'),'w=z'))),
        'sum_zero_excluded':all_('F G z',C('F','G','0','z'),'false'),
        'entry_positive_source_extensional':all_('F G H K n d a b',positive('n'),PE('F','H','n'),PE('G','K','n'),L('d','n'),E('F','G','n','d','a'),E('H','K','n','d','b'),'a=b'),
        'prefix_positive_source_extensional':all_('F G H K n M P',positive('n'),PE('F','H','n'),PE('G','K','n'),P('F','G','n','n','M'),P('H','K','n','n','P'),EQ('M','P','S n')),
        'positive_source_extensional':all_('F G H K n a b',PE('F','H','n'),PE('G','K','n'),C('F','G','n','a'),C('H','K','n','b'),'a=b'),
        'positive_source_transport':all_('N F G H K n z',T('N','H'),T('N','K'),L('n','N'),PE('F','H','n'),PE('G','K','n'),C('F','G','n','z'),C('H','K','n','z')),
        'table_zero_constructor':all_('F G H',T('0','F'),T('0','G'),T('0','H'),CT('0','F','G','H')),
        'table_append':all_('N F G H z',CT('N','F','G','H'),C('F','G','S N','z'),exists('K',CT('S N','F','G','K'),EQ('H','K','S N'))),
        'table_exists':all_('N F G',T('N','F'),T('N','G'),exists('H',CT('N','F','G','H'))),
        'table_lookup':all_('N F G H n',CT('N','F','G','H'),positive('n'),L('n','N'),exists('z',A('H','n','z'),C('F','G','n','z'))),
        'table_extensional':all_('N F G H K',CT('N','F','G','H'),CT('N','F','G','K'),PE('H','K','N')),
        'table_exists_extensionally_unique':all_('N F G',T('N','F'),T('N','G'),exists('H',CT('N','F','G','H'),all_('K',CT('N','F','G','K'),PE('H','K','N')))),
        'table_restrict':all_('N J F G H',CT('N','F','G','H'),L('J','N'),CT('J','F','G','H')),
    }
    return {'dirichlet_convolution_'+name:statement for name,statement in statements.items()}


SURFACES=(
    (candidate.dirichlet_convolution_entry_relation,expected_entry,('F','G','n','d','z')),
    (candidate.dirichlet_convolution_prefix_relation,expected_prefix,('F','G','n','l','M')),
    (candidate.dirichlet_convolution_sum_relation,expected_convolution,('F','G','n','z')),
    (candidate.dirichlet_convolution_table_relation,expected_convolution_table,('N','F','G','H')),
)


@pytest.mark.parametrize('builder,model,arguments',SURFACES)
@pytest.mark.parametrize('mode',('plain','compound','large','zero','repeated'))
def test_independent_exact_public_graphs(builder,model,arguments,mode):
    context=('N','F','G','H','n','d','z','l','M')
    if mode=='compound':arguments=tuple(f'({arg})+n' if i%2==0 else f'({arg})*F' for i,arg in enumerate(arguments))
    if mode=='large':arguments=('79228162514264337593543950335',*arguments[1:])
    if mode=='zero':arguments=('0',)*len(arguments)
    if mode=='repeated':arguments=('F',)*len(arguments)
    actual=builder(*arguments,tag='contract',variables=context)
    expected=model(*arguments,tag='model')
    close='forall '+' '.join(context)+'. '
    _assert_same_ast(_closed_formula(close+actual),_closed_formula(close+expected))


@lru_cache(maxsize=1)
def core():
    inherited=(*closure.parent_snapshot().specs,*previous_rows(),*all_new_rows())
    assert len(inherited)==len({row.name for row in inherited})==3643
    assert closure.PARENT_CATALOG_SHA256=='ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7'
    return {row.name:row for row in inherited}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_dirichlet_convolution_candidate_theorems(TheoremSpec)


EXPECTED=((8,8,7),(26,26,22),(10,10,9),(66,66,32),(193,193,33),
          (72,72,30),(100,100,34),(50,50,24),(176,176,40),(62,62,26),
          (31,31,21),(49,49,25),(69,69,34),(105,105,38),(58,58,22),
          (46,46,19),(100,100,55),(39,39,23),(15,15,10),(333,332,43),
          (67,67,35),(114,114,64),(67,67,31),(28,28,21),(191,191,45),
          (80,80,25),(36,36,21),(116,116,59),(31,31,20),(123,123,44))


PRINCIPAL_STATEMENT_SHA256={
    'dirichlet_convolution_prefix_exists':'5d71df6c16221c88381a9655b865904b4e799509b1656f93618ed965a008c8bb',
    'dirichlet_convolution_sum_exists_unique':'2f33c7fba0740a4b1f9c4e429e4e2ec41a8a1290ae96ec44e2dfc103d67907fa',
    'dirichlet_convolution_positive_source_transport':'8451fcb58644a7b0856ca2eadb5460d990de8687fd517d9b0ef56847f11520dd',
    'dirichlet_convolution_table_exists_extensionally_unique':'dd3b6ce98b1cda129a5105bc176ffbb4e7ca7d9549ea61a8ddcfc53a4a1ced13',
}


def test_exact_topological_inventory_without_oracles_or_unused_dependencies():
    assert len(rows())==30
    assert sum(len(row.dependencies) for row in rows())==68
    assert sum(len(row.script) for row in rows())==1273
    assert sha256(('\n'.join(row.name for row in rows())+'\n').encode()).hexdigest()=='c4847d469c4f45e83c9b07dd36b853a9e153e51ea7655ea972846d20db28d0bb'
    available=set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        for dependency in row.dependencies:
            assert re.search(r'(?<![\w\'])'+re.escape(dependency)+r'(?![\w\'])','\n'.join(row.script))
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        available.add(row.name)
    for name,digest in PRINCIPAL_STATEMENT_SHA256.items():
        assert sha256(next(row.statement for row in rows() if row.name==name).encode()).hexdigest()==digest


def test_exact_ast_novelty_against_all_3643_prior_rows_and_each_other():
    from constructive_dirichlet_support import statement_duplicates
    assert statement_duplicates(rows())==()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_independent_complete_theorem_contract(row):
    statements=expected_statements()
    assert tuple(statements)==tuple(r.name for r in rows())
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(statements[row.name]))


@pytest.mark.parametrize('builder,model,arguments',SURFACES)
def test_every_generated_binder_rejects_whole_context_capture(builder,model,arguments):
    context=tuple(dict.fromkeys(arguments))
    source=builder(*arguments,tag='capture',variables=context)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}
    assert binders and not binders.intersection(context)
    for binder in binders:
        with pytest.raises(ValueError):
            builder(*arguments,tag='capture',variables=context+(binder,))


@pytest.mark.parametrize('builder,model,arguments',SURFACES)
@pytest.mark.parametrize('bad',('unknown','formula','division','empty','duplicate','missing','list','bad-tag','reserved-tag'))
def test_invalid_terms_contexts_and_tags_fail_closed(builder,model,arguments,bad):
    context=tuple(dict.fromkeys(arguments));tag='invalid'
    if bad=='unknown':arguments=('unknown_variable',*arguments[1:])
    if bad=='formula':arguments=('F -> false',*arguments[1:])
    if bad=='division':arguments=('F / 2',*arguments[1:])
    if bad=='empty':context=()
    if bad=='duplicate':context=context+(context[0],)
    if bad=='missing':context=context[:-1]
    if bad=='list':context=list(context)
    if bad=='bad-tag':tag='bad tag'
    if bad=='reserved-tag':tag='forall'
    with pytest.raises(ValueError):
        builder(*arguments,tag=tag,variables=context)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        checked=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert checked.name==row.name
        assert (checked.proof_nodes,checked.proof_objects,checked.proof_depth)==EXPECTED[rows().index(row)]
        assert checked.proof_nodes>0 and checked.proof_depth<=256
    except CandidateBodyError as error:
        # Do not ask pytest to render the entire 3,643-row core dictionary
        # while reporting a single honest rejected authoring certificate.
        pytest.fail(str(error),pytrace=False)
    finally:
        gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_cannot_reuse_the_body(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_missing_actual_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,script=()),),core=core()|{r.name:r for r in rows()})


DEPENDENCIES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_dropped_dependency_rejected(row,dependency):
    altered=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_poisoned_dependency_rejected(row,dependency):
    table=core()|{r.name:r for r in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


def _unproved_strengthenings():
    T=lambda N,F:expected_table(N,F,'guard_table')
    A=lambda F,i,z:expected_at(F,i,z,'guard_at')
    E=lambda F,G,n,d,z:expected_entry(F,G,n,d,z,'guard_entry')
    C=lambda F,G,n,z:expected_convolution(F,G,n,z,'guard_sum')
    CT=lambda N,F,G,H:expected_convolution_table(N,F,G,H,'guard_output')
    L=lambda a,b:expected_le(a,b,'guard_bound')
    PE=lambda F,G,N:expected_positive_equal(F,G,N,'guard_positive_equal')
    EQ=lambda F,G,l:expected_equal(F,G,l,'guard_full_equal')
    M=lambda a,b,z:expected_signed_multiply(a,b,z,'guard_product')
    return (
        ('sum_exists','zero_input',f'forall N F G n. ({T("N","F")}) -> ({T("N","G")}) -> ({L("n","N")}) -> exists z. ({C("F","G","n","z")})'),
        ('sum_exists','missing_actual_input_table',f'forall N F G n. ({T("N","F")}) -> ~(n=0) -> ({L("n","N")}) -> exists z. ({C("F","G","n","z")})'),
        ('entry_from_quotient','unwitnessed_quotient',f'forall F G n d q a b z. ~(d=0) -> ({A("F","d","a")}) -> ({A("G","q","b")}) -> ({M("a","b","z")}) -> ({E("F","G","n","d","z")})'),
        ('entry_quotient_product','zero_divisor',f'forall F G n d q a b z. n=d*q -> ({A("F","d","a")}) -> ({A("G","q","b")}) -> ({E("F","G","n","d","z")}) -> ({M("a","b","z")})'),
        ('entry_positive_source_extensional','zero_target',f'forall F G H K n d a b. ({PE("F","H","n")}) -> ({PE("G","K","n")}) -> ({L("d","n")}) -> ({E("F","G","n","d","a")}) -> ({E("H","K","n","d","b")}) -> a=b'),
        ('positive_source_extensional','one_unrelated_source',f'forall F G H K n a b. ({PE("F","H","n")}) -> ({C("F","G","n","a")}) -> ({C("H","K","n","b")}) -> a=b'),
        ('table_extensional','table_code_equality',f'forall N F G H K. ({CT("N","F","G","H")}) -> ({CT("N","F","G","K")}) -> H=K'),
        ('table_extensional','zeroth_value_equality',f'forall N F G H K. ({CT("N","F","G","H")}) -> ({CT("N","F","G","K")}) -> ({EQ("H","K","S N")})'),
    )


@pytest.mark.parametrize('suffix,case,statement',_unproved_strengthenings(),ids=lambda value:value if len(value)<80 else 'altered_formula')
def test_unproved_guard_removal_or_false_uniqueness_is_rejected(suffix,case,statement):
    row=next(row for row in rows() if row.name=='dirichlet_convolution_'+suffix)
    assert _closed_formula(statement)!=_closed_formula(row.statement)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core()|{r.name:r for r in rows()})


def _entry_value(F,G,n,d):
    if d==0 or n%d:
        return 0
    q=n//d
    assert n==d*q
    return _lookup(F,d)*_lookup(G,q)


def _actual_mask(F,G,n,l,offset):
    values=tuple(_entry_value(F,G,n,d) for d in range(l+1))
    M=_table_code(values,(offset,)*(l+1))
    assert tuple(_lookup(M,d) for d in range(l+1))==values
    return M,values


def _decode_parts(F):
    pos,neg=_unpair(F)
    pb,pc=_unpair(pos);nb,nc=_unpair(neg)
    return pb,pc,nb,nc


def _actual_sum_witness(F,l):
    """Exhibit both real beta-coded prefix traces, not just a Python sum."""
    pb,pc,nb,nc=_decode_parts(F)
    pos=tuple(pb%(1+(i+1)*pc) for i in range(l))
    neg=tuple(nb%(1+(i+1)*nc) for i in range(l))
    ptrace=tuple(accumulate(pos,initial=0));ntrace=tuple(accumulate(neg,initial=0))
    for values,trace in ((pos,ptrace),(neg,ntrace)):
        b,c=_encode_beta(trace)
        assert b%(1+c)==0
        assert all(b%(1+(i+2)*c)==b%(1+(i+1)*c)+value for i,value in enumerate(values))
        assert b%(1+(l+1)*c)==sum(values)
    return ptrace[-1]-ntrace[-1]


@pytest.mark.parametrize('n',(1,2,3,4,6,8))
@pytest.mark.parametrize('zeros',((0,0),(11,-17),(-29,37)))
def test_actual_beta_product_masks_and_signed_prefix_traces(n,zeros):
    left=(zeros[0],*tuple((-1)**i*(i+1) for i in range(1,n+1)))
    right=(zeros[1],*tuple((-1)**(i+1)*(2*i-1) for i in range(1,n+1)))
    F=_table_code(left,(3,)*(n+1));G=_table_code(right,(5,)*(n+1))
    M,values=_actual_mask(F,G,n,n,7)
    P,other=_actual_mask(F,G,n,n,13)
    assert M!=P and _decode_parts(M)!=_decode_parts(P)
    assert values==other and values[0]==0
    expected=0
    for d in range(1,n+1):
        if n%d==0:
            q=n//d
            assert 0<q<=n and n==d*q
            assert values[d]==left[d]*right[q]
            expected+=left[d]*right[q]
        else:
            assert values[d]==0
    assert _actual_sum_witness(M,n+1)==_actual_sum_witness(P,n+1)==expected
    # A wrong length misses the final positive divisor n, not a harmless zero.
    assert _actual_sum_witness(M,n+1)-_actual_sum_witness(M,n)==left[n]*right[1]


@pytest.mark.parametrize('N',(0,1,2,4,6))
@pytest.mark.parametrize('output_zero',(-101,0,103))
def test_actual_output_table_positive_uniqueness_does_not_fix_zeroth_value_or_code(N,output_zero):
    left=(97,*tuple(i-2 for i in range(1,N+1)))
    right=(-89,*tuple(3-i for i in range(1,N+1)))
    F=_table_code(left,(1,)*(N+1));G=_table_code(right,(2,)*(N+1))
    result=tuple(sum(_entry_value(F,G,n,d) for d in range(n+1)) for n in range(1,N+1))
    H=_table_code((output_zero,*result),(4,)*(N+1))
    K=_table_code((output_zero+1,*result),(7,)*(N+1))
    assert H!=K and _lookup(H,0)!=_lookup(K,0)
    for n in range(1,N+1):
        M,_=_actual_mask(F,G,n,n,8)
        assert _lookup(H,n)==_lookup(K,n)==_actual_sum_witness(M,n+1)
    for J in range(N+1):
        assert all(_lookup(H,n)==_lookup(K,n) for n in range(1,J+1))


@pytest.mark.parametrize('n,l',((0,0),(0,3),(1,0),(1,4),(4,1),(4,4),(4,7)))
def test_actual_prefix_length_is_independent_of_n_and_restricts_without_reencoding(n,l):
    bound=max(n,l)+1
    F=_table_code(tuple(i-3 for i in range(bound+1)),(2,)*(bound+1))
    G=_table_code(tuple(5-i for i in range(bound+1)),(4,)*(bound+1))
    M,values=_actual_mask(F,G,n,l,6)
    assert values[0]==0
    for k in range(l+1):
        assert tuple(_lookup(M,d) for d in range(k+1))==values[:k+1]
    if n==0 and l>0:
        assert values[1]==_lookup(F,1)*_lookup(G,0)


@pytest.mark.parametrize('n',(1,2,4,6))
def test_positive_source_transport_ignores_all_four_input_zero_values(n):
    positiveF=tuple(i-3 for i in range(1,n+1));positiveG=tuple(4-2*i for i in range(1,n+1))
    F=_table_code((11,*positiveF),(1,)*(n+1));H=_table_code((-13,*positiveF),(3,)*(n+1))
    G=_table_code((17,*positiveG),(5,)*(n+1));K=_table_code((-19,*positiveG),(7,)*(n+1))
    assert len({_lookup(code,0) for code in (F,G,H,K)})==4
    M,_=_actual_mask(F,G,n,n,2);P,_=_actual_mask(H,K,n,n,4)
    assert _actual_sum_witness(M,n+1)==_actual_sum_witness(P,n+1)


def test_zero_divisor_guard_and_actual_quotient_are_substantive():
    F=_table_code((7,2,3,5),(1,)*4);G=_table_code((11,13,17,19),(2,)*4)
    assert _entry_value(F,G,0,0)==0
    # At n=d=0, dropping d!=0 admits every quotient and incompatible products.
    assert 0==0*0==0*1
    assert _lookup(F,0)*_lookup(G,0)!=_lookup(F,0)*_lookup(G,1)
    assert _entry_value(F,G,3,2)==0
    assert 3!=2*1 and _lookup(F,2)*_lookup(G,1)!=0


def test_n_one_uses_exactly_one_product_not_input_zero_or_empty_sum():
    F=_table_code((91,-2),(4,4));G=_table_code((-97,3),(5,5))
    M,values=_actual_mask(F,G,1,1,6)
    assert values==(0,-6)
    assert _actual_sum_witness(M,2)==-6


if __name__=='__main__':
    import argparse,json,resource,signal,time
    parser=argparse.ArgumentParser()
    parser.add_argument('--body')
    parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--count',type=int,default=30)
    parser.add_argument('--pytest-select')
    options=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)
    started=time.monotonic()
    if options.pytest_select is not None:
        status=pytest.main(['-q',__file__,'-x','-k',options.pytest_select])
    else:
        if options.start<0 or options.count<1:raise SystemExit('invalid body window')
        selected=tuple(row for row in rows() if options.body is None or row.name==options.body)
        selected=selected[options.start:options.start+options.count]
        if not selected:raise SystemExit('empty or unknown body selection')
        for row in selected:
            report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
            assert (report.proof_nodes,report.proof_objects,report.proof_depth)==EXPECTED[rows().index(row)]
            print(json.dumps({'name':row.name,'nodes':report.proof_nodes,'objects':report.proof_objects,
                              'depth':report.proof_depth,'dependencies':report.dependency_count,
                              'commands':report.command_count}),flush=True)
            gc.collect()
        status=0
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'status':status,'elapsed_seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
