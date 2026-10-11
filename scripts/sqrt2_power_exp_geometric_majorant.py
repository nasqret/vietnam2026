"""AP056: every actual exponential term has an original-head majorant.

For x<=L*d and d!=0, ordinary induction proves T[k]<=L^k*T[0].
The supplied power and beta entries are retained, including L=0 and k=0.
The arithmetic step cancels only d, not the argument or its bound.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_halving_prefix_decay import (
    ROOT,Scope,introduce,eliminate,apply,specialize,canonical,json_hash,
    source_registry,halving_prefix_decay_source_pins,COMPARISON_ARCHIVE,BOUND_ARCHIVE,
    ENDPOINT_SOURCES as POWER_ENDPOINTS,
)
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-geometric-majorant-v1'
T=('tb','tc')
PARAMETERS=('k','d','x','L')+T+('N','h','a','b')
PREMISES=('~d=0','Le(x,L*d)','Le(k,N)','NatScaledExpRecurrence(d,x,tb,tc,N)',
    'BetaAt(tb,tc,0,h)','BetaAt(tb,tc,k,a)','Pow(L,k,b)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> Le(a,b*h)'
TARGET_SHA256='e86ad6b58635a4c4ece5af53c0cf336a09fc69caf323c09e6c79fea863077e79'
HELPER_SOURCES={'step':'forall d x L j a b. ~d=0 -> Le(x,L*d) -> ((S j)*d)*b=x*a -> Le(b,L*a)'}
HELPER_TARGET_SHA256={'step':'c0e586967bce833b34488deb4b359c529d6b9ada28ae5704877ef76cd0ff9547'}
ARCHIVES=(COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={**POWER_ENDPOINTS,
    'zero_le':'forall a. Le(0,a)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'mul_comm':'forall a b. a*b=b*a',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(power_zero='AP010',power_step='AP010')
HELPER_DEPENDENCIES={
    'step':('zero_le','succ_le_succ','mul_right_mono','one_mul','mul_assoc','mul_comm','le_trans','mul_le_cancel'),
    'AP056':('step','power_zero','power_step','beta_exists','beta_unique','le_refl','le_succ',
        'le_trans','one_mul','mul_left_mono','mul_assoc','mul_comm'),
}


class ExpGeometricMajorantError(ValueError):
    """Changed supplied recurrence, original head, power or index."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Pow','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpGeometricMajorantError('existing exponential majorant definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_geometric_majorant_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=10 or len(premises)!=7 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpGeometricMajorantError('AP056 exact supplied exponential geometric majorant changed')
    return target


def source_contract():
    return dict(code='AP056',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=7,supplied_recurrence_head_value_and_power_required=True,argument_bound='x<=L*d',
        index_bound='k<=N',majorant='a<=b*h, with b=L^k',reference_head_index=0,
        positive_denominator_required=True,zero_L_x_k_N_and_head_allowed=True,
        new_induction_needed=True,new_induction_count=1,new_definition_ids=[],definition_admissions=0,
        large_ground_power_materialized=False,infinite_tail_or_exponential_claimed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_geometric_majorant_source_pins():
    result=halving_prefix_decay_source_pins()
    expected={'scripts/sqrt2_power_halving_prefix_decay.py':'edc928e52e36b65e8c9ef9c06268da1c44aa6b40df7c095f2327952395dea962',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_geometric_majorant.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpGeometricMajorantError('exponential majorant source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _step(s,registry):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        d,x,L,j,a,b=t.terms(('d','x','L','j','a','b'));sj=Succ(j);one=Succ(Zero());c=Mul(sj,d)
        positive_index=apply(specialize(t,'succ_le_succ',Zero(),j),specialize(t,'zero_le',j))
        coefficient=apply(specialize(t,'mul_right_mono',one,sj,d),positive_index)
        coefficient=_left(t,registry,coefficient,c,specialize(t,'one_mul',d))
        lower=apply(specialize(t,'mul_right_mono',d,c,b),coefficient)
        lower=_right(t,registry,lower,Mul(d,b),t.hyp('recurrence'))
        upper=apply(specialize(t,'mul_right_mono',x,Mul(L,d),a),t.hyp('argument'))
        upper=_right(t,registry,upper,Mul(x,a),_multiplicative_equal(t,Mul(Mul(L,d),a),Mul(d,Mul(L,a))))
        bound=apply(specialize(t,'le_trans',Mul(d,b),Mul(x,a),Mul(d,Mul(L,a))),lower,upper)
        return apply(specialize(t,'mul_le_cancel',d,b,Mul(L,a)),t.hyp('nonzero'),bound)
    return introduce(s,('d','x','L','j','a','b'),('nonzero','argument','recurrence'),finish)


def _majorant(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    row_parameters=PARAMETERS[1:];row_hyps=('nonzero','argument','bound','recurrence','head','value','power')
    def base(t):
        L,h,a,b=t.terms(('L','h','a','b'))
        p1=apply(specialize(t,'power_zero',L,Zero(),b),EqRefl(Zero()),t.hyp('power'))
        ah=apply(specialize(t,'beta_unique',*t.terms(T),Zero(),a,h),t.hyp('value'),t.hyp('head'))
        equal=_chain(CongMul(p1,EqRefl(h)),specialize(t,'one_mul',h),EqSym(ah))
        return _right(t,registry,specialize(t,'le_refl',a),a,EqSym(equal))
    def chosen(t):
        k,d,x,L,N,h,a,b,q,previous=t.terms(('k','d','x','L','N','h','a','b','q','a_prev'));sk=Succ(k)
        earlier=apply(specialize(t,'le_trans',k,sk,N),
            apply(specialize(t,'le_succ',k,k),specialize(t,'le_refl',k)),t.hyp('bound'))
        old=apply(specialize(t,'IH',d,x,L,*t.terms(T),N,h,previous,q),t.hyp('nonzero'),t.hyp('argument'),earlier,
            t.hyp('recurrence'),t.hyp('head'),t.hyp('previous'),AndElimL(t.hyp('power_data')))
        recurrence=apply(specialize(t,'recurrence',k,previous,a),t.hyp('bound'),t.hyp('previous'),t.hyp('value'))
        step=apply(specialize(t,'step',d,x,L,k,previous,a),t.hyp('nonzero'),t.hyp('argument'),recurrence)
        lifted=apply(specialize(t,'mul_left_mono',previous,Mul(q,h),L),old)
        bound=apply(specialize(t,'le_trans',a,Mul(L,previous),Mul(L,Mul(q,h))),step,lifted)
        equal=_chain(CongMul(AndElimR(t.hyp('power_data')),EqRefl(h)),
            _multiplicative_equal(t,Mul(Mul(q,L),h),Mul(L,Mul(q,h))))
        return _right(t,registry,bound,a,EqSym(equal))
    def successor(t):
        k,L,b=t.terms(('k','L','b'))
        power=apply(specialize(t,'power_step',L,k,Succ(k),b),EqRefl(Succ(k)),t.hyp('power'))
        return eliminate(t,power,('q',),'power_data',lambda u:
            eliminate(u,specialize(u,'beta_exists',*u.terms(T),u.term('k')),('a_prev',),'previous',chosen))
    return Ind(target.body,introduce(s,row_parameters,row_hyps,base),
        introduce(s,('k',),('IH',),lambda t:introduce(t,row_parameters,row_hyps,successor)))


def prove_exp_geometric_majorant(*,limits=None):
    registry=definition_registry();target=frozen_exp_geometric_majorant_target(_registry=registry)
    return assemble_mixed_certificate(code='AP056',target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'step':lambda s:_step(s,registry),'AP056':lambda s:_majorant(s,target,registry)},
        pins=exp_geometric_majorant_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
