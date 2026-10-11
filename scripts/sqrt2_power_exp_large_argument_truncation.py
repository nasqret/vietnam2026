"""AP055: effective truncation bounds for supplied large-argument sums.

Keep the supplied table, head at K, two sum values and actual power. Identify
AP054's constructed tail by value uniqueness, including an empty short sum.
Only finite rational-error arithmetic is asserted.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_large_argument_decay import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,canonical,json_hash,
    source_registry,exp_large_argument_decay_source_pins,NAMED_SOURCE as DECAY_SOURCE,COMPOSITION_ARCHIVE,
)
from sqrt2_power_exp_truncation import (
    HELPER_SOURCES as TRUNCATION_HELPERS,
    SPLIT_SOURCE,FUBINI_HELPERS,SPLIT_ARCHIVE,
)
from sqrt2_power_exp_two_error_bound import TRUNCATION_ARCHIVE
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-large-argument-truncation-v1'
A=('ab','ac')
PARAMETERS=('d','x','L')+A+('K','m','N','a0','s','t','p')
RECURRENCE='NatScaledExpRecurrence(d,x,ab,ac,(K+m)+N)'
PREFIX='Sum(ab,ac,K+m,s)'
WHOLE='Sum(ab,ac,S((K+m)+N),t)'
PREMISES=('~d=0','Le(x,L*d)','Le(2*L,K)',RECURRENCE,'BetaAt(ab,ac,K,a0)',PREFIX,WHOLE,'Pow(2,m,p)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> Le(s,t) /\\ Le(p*t,p*s+2*a0)'
TARGET_SHA256='6d652892aa498fb4573642b7316fc9a30f17cc0102198e2d0ca31291e5c299b0'
HELPER_SOURCES={'supplied_split':'forall ab ac M N s t u. NatAffineSum(ab,ac,M,1,S N,u) -> Sum(ab,ac,M,s) -> Sum(ab,ac,S(M+N),t) -> t=s+u'}
HELPER_TARGET_SHA256={'supplied_split':'e4e47c2284ec2a6ecb9a4c821210e7568e4bec3d9de549728755f142d2b04915'}
DECAY_ARCHIVE=dict(case='AP054',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-large-argument-decay-v1/generation-process.json.gz',
    bytes=62607,sha256='2124d8708a4fdc95bba31fa91b096bb3df8284d773280958950f5c64c8e7c63f',
    raw_bytes=596345,raw_sha256='876a59333d336a32c4fe668cef25f34878f85bab4b995d8a2060bc0c13dd6d3b',
    bundle_bytes=293917,bundle_sha256='1390d3a7c2b97fdc38e34ee664d4941d9aa338b669daa1d77b5e68f7e22d6fe5',
    nodes=138,root=137,target_ast_sha256='a11bcab301bcc1baa600ebeb7741038a4ddea68d8a679317bf9afb96a127d859')
ARCHIVES=(DECAY_ARCHIVE,SPLIT_ARCHIVE,TRUNCATION_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={'decay':DECAY_SOURCE,'splitting':SPLIT_SOURCE,
    'slice_sum_unique':FUBINI_HELPERS['slice_sum_unique'],'finish_bound':TRUNCATION_HELPERS['finish_bound'],
    'sum_unique':'forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m',
    'beta_unique':'forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d',
    'power_unique':'forall a n x y. Pow(a,n,x) -> Pow(a,n,y) -> x=y',
}
ENDPOINT_OWNERS={name:'CV061' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(decay='AP054',splitting='CV009',slice_sum_unique='CV009',finish_bound='CV100')
HELPER_DEPENDENCIES={'supplied_split':('splitting','sum_unique','slice_sum_unique'),
    'AP055':('decay','supplied_split','beta_unique','power_unique','finish_bound')}


class ExpLargeArgumentTruncationError(ValueError):
    """Changed supplied large-argument computation, cutoff, or error."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','Pow','NatAffineSum','NatRatioBoundPrefix','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpLargeArgumentTruncationError('existing large-argument truncation DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_large_argument_truncation_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=12 or len(premises)!=8 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpLargeArgumentTruncationError('AP055 exact supplied large-argument truncation changed')
    return target


def source_contract():
    return dict(code='AP055',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=8,supplied_table_head_sums_and_power_preserved=True,argument_bound='x<=L*d',
        initial_cutoff='2*L<=K',reference_head_index='K',prefix_length='K+m',whole_length='K+m+N+1',
        actual_tail_identified_by_value_uniqueness=True,finite_bounds='s<=t; p*t<=p*s+2*a0',power='p=2^m',
        uniform_in_extra_finite_horizon=True,empty_prefix_and_zero_argument_and_head_allowed=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        infinite_tail_or_exponential_claimed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_large_argument_truncation_source_pins():
    result=exp_large_argument_decay_source_pins()
    expected={'scripts/sqrt2_power_exp_large_argument_decay.py':'fea6181358f3f38eaf60b8e51a0cbff770068d45c824c42a9f9cf002c3f2a170',**{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_large_argument_truncation.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpLargeArgumentTruncationError('large-argument truncation source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _supplied_split(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqSym
    from peano_lab.kernel.terms import Add,Succ,Zero
    def chosen(t):
        M,N,z,out,u,short,tail,whole=t.terms(('M','N','s','t','u','short','tail','whole'));sn=Succ(N)
        data=t.hyp('split')
        first=apply(specialize(t,'sum_unique',*t.terms(A),M,short,z),field(data,0,4),t.hyp('prefix'))
        last=apply(specialize(t,'slice_sum_unique',*t.terms(A),M,Succ(Zero()),sn,tail,u),field(data,1,4),t.hyp('tail_sum'))
        full=_subst(t,registry,'Sum(ab,ac,slot,whole)',instantiate(Axiom('PA4'),M,N),field(data,2,4))
        same=apply(specialize(t,'sum_unique',*t.terms(A),Succ(Add(M,N)),whole,out),full,t.hyp('whole_sum'))
        return _chain(EqSym(same),field(data,3,4),CongAdd(first,last))
    return introduce(s,A+('M','N','s','t','u'),('tail_sum','prefix','whole_sum'),lambda t:
        eliminate(t,specialize(t,'splitting',*t.terms(A),t.term('M'),Succ(t.term('N'))),
            ('short','tail','whole'),'split',chosen))


def _root(s,registry):
    from peano_lab.kernel.terms import Add,Succ,Zero
    two=Succ(Succ(Zero()))
    def chosen(t):
        K,m,N,a0,p=t.terms(('K','m','N','a0','p'));data=t.hyp('tail_data')
        actual_tail=witness(t.terms(('ub','uc')),conjunction(field(data,3,9),field(data,6,9)))
        split=apply(specialize(t,'supplied_split',*t.terms(A),Add(K,m),N,*t.terms(('s','t','tail_total'))),
            actual_tail,t.hyp('prefix'),t.hyp('whole'))
        same_head=apply(specialize(t,'beta_unique',*t.terms(A),K,t.term('tail_head'),a0),field(data,1,9),t.hyp('head'))
        same_power=apply(specialize(t,'power_unique',two,m,t.term('tail_power'),p),field(data,0,9),t.hyp('power'))
        bound=_subst(t,registry,'Le(tail_power*tail_total,2*slot)',same_head,field(data,8,9))
        bound=_subst(t,registry,'Le(slot*tail_total,2*a0)',same_power,bound)
        return apply(specialize(t,'finish_bound',p,a0,*t.terms(('s','t','tail_total'))),split,bound)
    def start(t):
        data=apply(specialize(t,'decay',*t.terms(('d','x','L')+A+('K','m','N'))),
            *(t.hyp(n) for n in ('nonzero','argument','threshold','recurrence')))
        return eliminate(t,data,('tail_power','ub','uc','tail_head','omitted','tail_total'),'tail_data',chosen)
    return introduce(s,PARAMETERS,('nonzero','argument','threshold','recurrence','head','prefix','whole','power'),start)


def prove_exp_large_argument_truncation(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP055',target=frozen_exp_large_argument_truncation_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'supplied_split':lambda s:_supplied_split(s,registry),'AP055':lambda s:_root(s,registry)},
        pins=exp_large_argument_truncation_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
