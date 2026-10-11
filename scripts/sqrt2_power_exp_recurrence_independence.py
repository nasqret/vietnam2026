"""AP060: bound-free value independence of actual exponential recurrences.

Equal rational arguments and positive denominators force cross-equality of
each decoded term. One ordinary induction proves this without any argument
bound or head cancellation. Existing pointwise linearity then gives the same
cross-equality for the two supplied finite sums, including zero heads.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_rescaling import (
    ROOT,Scope,introduce,eliminate,apply,specialize,canonical,json_hash,
    definition_registry as source_registry,exp_rescaling_source_pins,
    BOUND_ARCHIVE,LINEARITY_ARCHIVE,LINEARITY_SOURCE,
)
from sqrt2_power_composition_recurrence import RECURRENCE_ARCHIVE
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-recurrence-independence-v1'
A,B=('ab','ac'),('bb','bc')
FIXED=('d','e','x','y','N')+A+B+('h','g')
COMMON=('~d=0','~e=0','x*e=y*d',
    'NatScaledExpRecurrence(d,x,ab,ac,N)','NatScaledExpRecurrence(e,y,bb,bc,N)',
    'BetaAt(ab,ac,0,h)','BetaAt(bb,bc,0,g)')
COMMON_HYPS=('d_nonzero','e_nonzero','argument_equal','recurrence_a','recurrence_b','head_a','head_b')
PARAMETERS=FIXED+('s','t')
PREMISES=COMMON+('Sum(ab,ac,S N,s)','Sum(bb,bc,S N,t)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> g*s=h*t'
TARGET_SHA256='7beddbf0b9c56535b34cc9097c02c1dd441a5ba9cb163ee87131584651dfc897'
TERM_PARAMETERS=('j',)+FIXED+('a','b')
TERM_PREMISES=COMMON+('Le(j,N)','BetaAt(ab,ac,j,a)','BetaAt(bb,bc,j,b)')
GRAPH='NatLinearTriple(g,0,h,ab,ac,ab,ac,bb,bc,S N)'
HELPER_SOURCES={
    'cross_step':'forall c d e x y h g a b u v. ~c=0 -> ~d=0 -> ~e=0 -> x*e=y*d -> (c*d)*u=x*a -> (c*e)*v=y*b -> g*a=h*b -> g*u=h*v',
    'term_cross':'forall '+' '.join(TERM_PARAMETERS)+'. '+' -> '.join(TERM_PREMISES)+' -> g*a=h*b',
    'graph':'forall '+' '.join(FIXED)+'. '+' -> '.join(COMMON)+' -> '+GRAPH,
}
HELPER_TARGET_SHA256={
    'cross_step':'78c89d99883e2bc349d39adad40de867157d597b73424fa0a4aa24c1248808bd',
    'term_cross':'85d8ed5150710aa188ce1472104c35e1ce9415cccc20810cbb322898f916de7d',
    'graph':'59a760f32c4c04c374f19de2bac8aeda17b82d69cf809a357f92ecebad17ebdb',
}
ARCHIVES=(BOUND_ARCHIVE,RECURRENCE_ARCHIVE,LINEARITY_ARCHIVE)
ENDPOINT_SOURCES={
    'beta_exists':'forall b c i. exists a. BetaAt(b,c,i,a)',
    'beta_unique':'forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d',
    'le_refl':'forall a. Le(a,a)','le_succ':'forall a b. Le(a,b) -> Le(a,S b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'le_of_succ':'forall a b. Le(S a,S b) -> Le(a,b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_nonzero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0',
    'succ_nonzero':'forall a. ~(S a)=0','zero_mul':'forall a. 0*a=0',
    'mul_cancel':'forall a b c. ~a=0 -> a*b=a*c -> b=c',
    'linearity':LINEARITY_SOURCE,
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(mul_cancel='CV002',linearity='CV006')
HELPER_DEPENDENCIES={
    'cross_step':('mul_assoc','mul_comm','mul_nonzero','mul_cancel'),
    'term_cross':('cross_step','beta_exists','beta_unique','mul_comm','le_refl','le_succ','le_trans','succ_nonzero'),
    'graph':('term_cross','le_of_succ','zero_mul'),
    'AP060':('graph','linearity','zero_mul'),
}


class ExpRecurrenceIndependenceError(ValueError):
    """Changed argument equality, actual tables, sums or guarded cancellation."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','NatScaledExpRecurrence','NatLinearTriple']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpRecurrenceIndependenceError('existing recurrence-independence definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_recurrence_independence_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=13 or len(premises)!=9 or type(conclusion) is not Eq or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRecurrenceIndependenceError('AP060 exact unrestricted recurrence value identity changed')
    return target


def source_contract():
    return dict(code='AP060',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=9,both_supplied_recurrences_heads_and_sums_required=True,
        rational_argument_identity='x*e=y*d',natural_sum_identity='g*s=h*t',
        positive_denominators_required=True,argument_upper_bound_required=False,
        head_positivity_required=False,zero_arguments_heads_and_horizon_allowed=True,
        code_number_equality_claimed=False,new_induction_needed=True,new_induction_count=1,
        new_definition_ids=[],definition_admissions=0,large_ground_power_materialized=False,
        analytic_exponential_identity_claimed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_recurrence_independence_source_pins():
    result=exp_rescaling_source_pins()
    expected={'scripts/sqrt2_power_exp_rescaling.py':'bc2721198e4ce3580b7965152fe3b6e02b41336dde024eb543e64069844d6947',
        'scripts/sqrt2_power_composition_recurrence.py':'8989d3b556c1b00602e75b34807a98b5d730864271edfacf329c6898863f9547',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_recurrence_independence.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRecurrenceIndependenceError('recurrence independence source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _cross_step(s):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        c,d,e,x,y,h,g,a,b,u,v=t.terms(('c','d','e','x','y','h','g','a','b','u','v'))
        coefficient=Mul(Mul(c,d),e);left=Mul(g,u);right=Mul(h,v);xe=Mul(x,e)
        equality=_chain(
            _multiplicative_equal(t,Mul(coefficient,left),Mul(g,Mul(e,Mul(Mul(c,d),u)))),
            CongMul(EqRefl(g),CongMul(EqRefl(e),t.hyp('step_a'))),
            _multiplicative_equal(t,Mul(g,Mul(e,Mul(x,a))),Mul(xe,Mul(g,a))),
            CongMul(EqRefl(xe),t.hyp('previous')),
            CongMul(t.hyp('argument_equal'),EqRefl(Mul(h,b))),
            _multiplicative_equal(t,Mul(Mul(y,d),Mul(h,b)),Mul(h,Mul(d,Mul(y,b)))),
            CongMul(EqRefl(h),CongMul(EqRefl(d),EqSym(t.hyp('step_b')))),
            _multiplicative_equal(t,Mul(h,Mul(d,Mul(Mul(c,e),v))),Mul(coefficient,right)))
        cd=apply(specialize(t,'mul_nonzero',c,d),t.hyp('c_nonzero'),t.hyp('d_nonzero'))
        nonzero=apply(specialize(t,'mul_nonzero',Mul(c,d),e),cd,t.hyp('e_nonzero'))
        return apply(specialize(t,'mul_cancel',coefficient,left,right),nonzero,equality)
    return introduce(s,('c','d','e','x','y','h','g','a','b','u','v'),
        ('c_nonzero','d_nonzero','e_nonzero','argument_equal','step_a','step_b','previous'),finish)


def _term_cross(s,target):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Succ,Zero
    row_parameters=TERM_PARAMETERS[1:];row_hyps=COMMON_HYPS+('bound','entry_a','entry_b')
    def base(t):
        h,g,a,b=t.terms(('h','g','a','b'))
        ah=apply(specialize(t,'beta_unique',*t.terms(A),Zero(),a,h),t.hyp('entry_a'),t.hyp('head_a'))
        bg=apply(specialize(t,'beta_unique',*t.terms(B),Zero(),b,g),t.hyp('entry_b'),t.hyp('head_b'))
        return _chain(CongMul(EqRefl(g),ah),specialize(t,'mul_comm',g,h),EqSym(CongMul(EqRefl(h),bg)))
    def chosen(t):
        j,d,e,x,y,N,h,g,a,b,old_a,old_b=t.terms(('j','d','e','x','y','N','h','g','a','b','old_a','old_b'));sj=Succ(j)
        earlier=apply(specialize(t,'le_trans',j,sj,N),
            apply(specialize(t,'le_succ',j,j),specialize(t,'le_refl',j)),t.hyp('bound'))
        old=apply(specialize(t,'IH',*t.terms(FIXED),old_a,old_b),
            *(t.hyp(name) for name in COMMON_HYPS),earlier,t.hyp('previous_a'),t.hyp('previous_b'))
        reca=apply(specialize(t,'recurrence_a',j,old_a,a),t.hyp('bound'),t.hyp('previous_a'),t.hyp('entry_a'))
        recb=apply(specialize(t,'recurrence_b',j,old_b,b),t.hyp('bound'),t.hyp('previous_b'),t.hyp('entry_b'))
        return apply(specialize(t,'cross_step',sj,d,e,x,y,h,g,old_a,old_b,a,b),
            specialize(t,'succ_nonzero',j),t.hyp('d_nonzero'),t.hyp('e_nonzero'),t.hyp('argument_equal'),reca,recb,old)
    def successor(t):
        return eliminate(t,specialize(t,'beta_exists',*t.terms(A),t.term('j')),('old_a',),'previous_a',lambda u:
            eliminate(u,specialize(u,'beta_exists',*u.terms(B),u.term('j')),('old_b',),'previous_b',chosen))
    return Ind(target.body,introduce(s,row_parameters,row_hyps,base),
        introduce(s,('j',),('IH',),lambda t:introduce(t,row_parameters,row_hyps,successor)))


def _graph(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def entry(t):
        i,N,g,a,unused,b=t.terms(('i','N','g','av','unused','bv'))
        bound=apply(specialize(t,'le_of_succ',i,N),t.hyp('in_range'))
        equal=apply(specialize(t,'term_cross',i,*t.terms(FIXED),a,b),
            *(t.hyp(name) for name in COMMON_HYPS),bound,t.hyp('a_value'),t.hyp('b_value'))
        return _chain(EqSym(equal),EqSym(instantiate(Axiom('PA3'),Mul(g,a))),
            EqSym(CongAdd(EqRefl(Mul(g,a)),specialize(t,'zero_mul',unused))))
    return introduce(s,FIXED,COMMON_HYPS,lambda t:
        introduce(t,('i','av','unused','bv'),('in_range','a_value','a_duplicate','b_value'),entry))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(u):
        h,g,N,left,right=u.terms(('h','g','N','s','t'))
        graph=apply(specialize(u,'graph',*u.terms(FIXED)),*(u.hyp(name) for name in COMMON_HYPS))
        equal=apply(specialize(u,'linearity',g,Zero(),h,*u.terms(A+A+B),Succ(N),left,left,right),
            u.hyp('sum_a'),u.hyp('sum_a'),u.hyp('sum_b'),graph)
        return EqSym(_chain(equal,CongAdd(EqRefl(Mul(g,left)),specialize(u,'zero_mul',left)),
            instantiate(Axiom('PA3'),Mul(g,left))))
    return introduce(s,PARAMETERS,COMMON_HYPS+('sum_a','sum_b'),finish)


def prove_exp_recurrence_independence(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry();target=frozen_exp_recurrence_independence_target(_registry=registry)
    term_target=parse_named(HELPER_SOURCES['term_cross'],registry=registry)
    return assemble_mixed_certificate(code='AP060',target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'cross_step':_cross_step,'term_cross':lambda s:_term_cross(s,term_target),'graph':_graph,'AP060':_root},
        pins=exp_recurrence_independence_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
