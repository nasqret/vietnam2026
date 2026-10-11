"""AP052: construct an actual finite tail past a large-argument cutoff.

For x<=L*d and M>=2*L, the supplied exponential recurrence gives a genuine
length-(N+1) slice starting at M. Its head and sum are computed, its terms
halve, and its sum is at most twice its head. All zero cutoffs are retained.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_scaled_exp_tail import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,canonical,json_hash,
    definition_registry as source_registry,HELPER_SOURCES as TAIL_HELPERS,
    ENDPOINT_SOURCES as TAIL_ENDPOINTS,RATIO_ARCHIVE,COMPOSITION_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_large_argument_ratio import NAMED_SOURCE as RATIO_SOURCE,exp_large_argument_ratio_source_pins
from sqrt2_power_scaled_exp_tail_decay import TAIL_ARCHIVE
from sqrt2_power_ratio_sum_bound import NAMED_SOURCE as SUM_SOURCE
from sqrt2_power_log_exp_witness import conjoin
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-large-argument-tail-v1'
T,U=('tb','tc'),('ub','uc')
PARAMETERS=('d','x','L')+T+('M','N')
RECURRENCE='NatScaledExpRecurrence(d,x,tb,tc,M+N)'
SLICE='NatAffineSlice(tb,tc,M,1,ub,uc,S N)'
RATIO='NatRatioBoundPrefix(ub,uc,1,S N)'
PREMISES=('~d=0','Le(x,L*d)','Le(2*L,M)',RECURRENCE)
OUTPUTS=U+('a','s')
PARTS=(SLICE,RATIO,'BetaAt(tb,tc,M,a)','BetaAt(ub,uc,0,a)','Sum(ub,uc,S N,s)','Le(s,2*a)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='bb49801153c9bc3821d1f494707843d81d2f5e20181f6172563fe79531ae95eb'
HELPER_SOURCES={
    'tail_ratio':'forall '+' '.join(PARAMETERS+U)+'. '+' -> '.join(PREMISES+(SLICE,))+' -> '+RATIO,
    'tail_head':'forall '+' '.join(T+U+('M','N','a'))+'. '+SLICE+' -> BetaAt(tb,tc,M,a) -> BetaAt(ub,uc,0,a)',
}
HELPER_TARGET_SHA256={'tail_ratio':'271840bcb01632b81af38289f755182b0c29b2f451402d186cac770052252a32',
    'tail_head':'8a25c43e9554b9509f476c36981bdd379563942bd5efbb6bae2810e448b14d61'}
STEP_ARCHIVE=dict(case='AP051',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-large-argument-ratio-v1/generation-process.json.gz',
    bytes=42413,sha256='56c4fe7152908f5d764512f0b7ad9aab9c8ca4d333831fed01d8f25283f343fd',
    raw_bytes=168835,raw_sha256='e760d60792699ee4018023852290c28623d2caef139575f3c87e450d2aca3370',
    bundle_bytes=27070,bundle_sha256='8c573ecc91ad5f0f76f2f09bf876aa3d6c442aaab055155a442382b3dc4ae9e4',
    nodes=23,root=22,target_ast_sha256='0ed9c296638e7d978dbfb8e18e70dba5fbd546cda5f0e856d746cddb49f5ba40')
ARCHIVES=(STEP_ARCHIVE,TAIL_ARCHIVE,RATIO_ARCHIVE,COMPOSITION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'ratio':RATIO_SOURCE,'slice_entry':TAIL_HELPERS['slice_entry'],
    'slice_exists':TAIL_ENDPOINTS['slice_exists'],'sum_ratio':SUM_SOURCE,
    'beta_exists':'forall b c i. exists a. BetaAt(b,c,i,a)',
    'beta_unique':'forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d',
    'le_of_succ_le_succ':'forall a b. Le(S a,S b) -> Le(a,b)',
    'le_succ':'forall a b. Le(a,b) -> Le(a,S b)',
    'succ_le_succ':'forall a b. Le(a,b) -> Le(S a,S b)',
    'zero_le':'forall a. Le(0,a)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'add_comm':'forall a b. a+b=b+a','one_mul':'forall a. 1*a=a',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(ratio='AP051',slice_entry='CV087',slice_exists='CV061',sum_ratio='CV068')
HELPER_DEPENDENCIES={
    'tail_ratio':('ratio','slice_entry','le_of_succ_le_succ','le_succ','add_left_mono','le_trans','add_comm','one_mul'),
    'tail_head':('slice_entry','beta_exists','beta_unique','succ_le_succ','zero_le'),
    'AP052':('slice_exists','beta_exists','tail_ratio','tail_head','sum_ratio'),
}


class ExpLargeArgumentTailError(ValueError):
    """Changed actual shifted computation, large-argument threshold or bound."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','NatAffineSlice','NatRatioBoundPrefix','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpLargeArgumentTailError('existing finite tail definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_large_argument_tail_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=7 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpLargeArgumentTailError('AP052 exact constructed large-argument tail changed')
    return target


def source_contract():
    return dict(code='AP052',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,argument_bound='x<=L*d',tail_start='2*L<=M',supplied_recurrence_degree='M+N',
        actual_slice_start='M',actual_slice_length='N+1',actual_head_and_sum_constructed=True,
        actual_ratio_definition='ND0441 at ratio parameter 1',finite_tail_bound='s<=2*a',
        allows_zero_L_M_N_x_and_head=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,infinite_tail_or_exponential_claimed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_large_argument_tail_source_pins():
    result=exp_large_argument_ratio_source_pins()
    expected={'scripts/sqrt2_power_exp_large_argument_ratio.py':'802c21d935e839727000fa781d27c44f40973fd7324b108aabb9842db0b6947e',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_large_argument_tail.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpLargeArgumentTailError('large-argument tail source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _tail_ratio(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    two=parse_term('2')
    def entry(t):
        d,x,L,M,N,i,a,b=t.terms(('d','x','L','M','N','i','a','b'));j=Add(M,i)
        below=apply(specialize(t,'le_of_succ_le_succ',Succ(i),N),t.hyp('bound'))
        current_bound=apply(specialize(t,'le_succ',Succ(i),N),below)
        shifted=apply(specialize(t,'add_left_mono',Succ(i),N,M),below)
        shifted=_left(t,registry,shifted,Add(M,N),instantiate(Axiom('PA4'),M,i))
        current=apply(specialize(t,'slice_entry',*t.terms(T+U),M,Succ(N),i,a),t.hyp('slice'),current_bound,t.hyp('current'))
        following=apply(specialize(t,'slice_entry',*t.terms(T+U),M,Succ(N),Succ(i),b),t.hyp('slice'),t.hyp('bound'),t.hyp('following'))
        following=_subst(t,registry,'BetaAt(tb,tc,slot,b)',instantiate(Axiom('PA4'),M,i),following)
        equation=apply(specialize(t,'recurrence',j,a,b),shifted,current,following)
        lower=witness((i,),specialize(t,'add_comm',i,M))
        lower=apply(specialize(t,'le_succ',M,j),lower)
        threshold=apply(specialize(t,'le_trans',Mul(two,L),M,Succ(j)),t.hyp('threshold'),lower)
        result=apply(specialize(t,'ratio',d,x,L,j,a,b),t.hyp('nonzero'),t.hyp('argument'),threshold,equation)
        return _right(t,registry,result,Mul(two,b),EqSym(specialize(t,'one_mul',a)))
    return introduce(s,PARAMETERS+U,('nonzero','argument','threshold','recurrence','slice'),lambda t:
        introduce(t,('i','a','b'),('bound','current','following'),entry))


def _tail_head(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        M,N,a,b=t.terms(('M','N','a','b'));zero=Zero()
        bound=apply(specialize(t,'succ_le_succ',zero,N),specialize(t,'zero_le',N))
        old=apply(specialize(t,'slice_entry',*t.terms(T+U),M,Succ(N),zero,b),t.hyp('slice'),bound,t.hyp('entry'))
        old=_subst(t,registry,'BetaAt(tb,tc,slot,b)',instantiate(Axiom('PA3'),M),old)
        same=apply(specialize(t,'beta_unique',*t.terms(T),M,b,a),old,t.hyp('head'))
        return _subst(t,registry,'BetaAt(ub,uc,0,slot)',same,t.hyp('entry'))
    return introduce(s,T+U+('M','N','a'),('slice','head'),lambda t:
        eliminate(t,specialize(t,'beta_exists',*t.terms(U),Zero()),('b',),'entry',chosen))


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ,Zero
    one=Succ(Zero())
    def ratio(t):
        return apply(specialize(t,'tail_ratio',*t.terms(PARAMETERS+U)),
            *(t.hyp(n) for n in ('nonzero','argument','threshold','recurrence','slice')))
    def head(t):
        return apply(specialize(t,'tail_head',*t.terms(T+U+('M','N','a'))),t.hyp('slice'),t.hyp('head'))
    def summed(t):
        return witness(t.terms(OUTPUTS),conjunction(t.hyp('slice'),ratio(t),t.hyp('head'),head(t),
            AndElimL(t.hyp('sum_bound')),AndElimR(t.hyp('sum_bound'))))
    def sliced(t):
        value=apply(specialize(t,'sum_ratio',*t.terms(U),one,Succ(t.term('N')),t.term('a')),ratio(t),head(t))
        return eliminate(t,value,('s',),'sum_bound',summed)
    def headed(t):
        return eliminate(t,specialize(t,'slice_exists',*t.terms(T),t.term('M'),one,Succ(t.term('N'))),U,'slice',sliced)
    return introduce(s,PARAMETERS,('nonzero','argument','threshold','recurrence'),lambda t:
        eliminate(t,specialize(t,'beta_exists',*t.terms(T),t.term('M')),('a',),'head',headed))


def prove_exp_large_argument_tail(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP052',target=frozen_exp_large_argument_tail_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'tail_ratio':lambda s:_tail_ratio(s,registry),'tail_head':lambda s:_tail_head(s,registry),'AP052':_root},
        pins=exp_large_argument_tail_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
