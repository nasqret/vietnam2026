"""AP038: finite exponential convolution obeys the added-argument recurrence.

Construct actual Euler tables and coefficients. The proved Euler product
rule and denominator-cleared shift law derive the recurrence below the
common cutoff. No cancellation, positive scale or infinite identity is used.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_convolution_shift import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,canonical,json_hash,
    NAMED_SOURCE as SHIFT_SOURCE,convolution_shift_source_pins,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_log_exp_witness import definition_registry as source_registry
from sqrt2_power_euler_product import HELPER_SOURCES as EULER_HELPERS,coefficient
from sqrt2_power_series_power_euler import EULER_ARCHIVE,ASSOC_ARCHIVE
from sqrt2_power_convolution_associative import HELPER_SOURCES as ASSOC_HELPERS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-convolution-recurrence-v1'
A,B,EA,EB=('ab','ac','S N'),('bb','bc','S N'),('eb','ec','S N'),('fb','fc','S N')
PARAMETERS=('d','x','y','ab','ac','bb','bc','N','i','u','v')
FIRST='NatScaledExpRecurrence(d,x,ab,ac,N)'
SECOND='NatScaledExpRecurrence(d,y,bb,bc,N)'
EULER='NatEulerPrefix(ab,ac,eb,ec,S N)'
RELATION='forall j a c. Le(j,i) -> BetaZeroExtend(ab,ac,S N,j,a) -> BetaZeroExtend(eb,ec,S N,S j,c) -> d*c=x*a'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+FIRST+' -> '+SECOND+' -> Lt(i,N) -> '+coefficient(A,B,'i','u')+' -> '+coefficient(A,B,'S i','v')+' -> ((S i)*d)*v=(x+y)*u'
TARGET_SHA256='1d0487d27421420580ddbc9e31618cfe3a90ef13648ea8c02a25c5be0e87f7e0'
HELPER_SOURCES={
    'inside':'forall b c L i a. Lt(i,L) -> BetaZeroExtend(b,c,L,i,a) -> BetaAt(b,c,i,a)',
    'euler_zero':'forall ab ac eb ec N. '+EULER+' -> BetaZeroExtend(eb,ec,S N,0,0)',
    'euler_shift':'forall d x ab ac eb ec N i. '+FIRST+' -> '+EULER+' -> Lt(i,N) -> '+RELATION,
    'arithmetic':'forall d x y i u v q r. (S i)*v=q+r -> d*q=x*u -> d*r=y*u -> ((S i)*d)*v=(x+y)*u',
}
HELPER_TARGET_SHA256={
    'inside':'260a3f34dd854c3938ee5e51c66e4ea635623880d924847b23b3750b7f1531c6',
    'euler_zero':'19bd8d51affdf593b187c47261f9af5d320e306bb78b498ac7a3e93a13c5cd1d',
    'euler_shift':'06951d5fa4537f16f59bf3343b9a5347e70f2759897ede7b77f9478bd91c8e34',
    'arithmetic':'aa67b9ce584f72d014132da379ea028f0c020c15b3424772371353a8ee8feb1e'}
SHIFT_ARCHIVE=dict(case='AP037',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-shift-v1/generation-process.json.gz',
    bytes=47643,sha256='f981f500341902867988d2b4cc728e9f2a6abb7aa26be7adaf57018f0c51b331',
    raw_bytes=560623,raw_sha256='7b4a0f851b516186e4fa4a9c80f6f72aab36caf0de975cb931f25d1e062ca56a',
    bundle_bytes=300980,bundle_sha256='66e3363a9ed58930f10db6803f0c605ec5bae24396b0b633a582fd2e26f462b3',
    nodes=131,root=130,target_ast_sha256='d3eb18cd8e8c76b563ea0fbc13a70b6de3140d1c177e036fa23a2411b01980b2')
ARCHIVES=(SHIFT_ARCHIVE,CONVOLUTION_ARCHIVE,EULER_ARCHIVE,ASSOC_ARCHIVE)
ENDPOINT_SOURCES={
    'zero_mul':'forall a. 0*a=0','mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_add':'forall a b c. a*(b+c)=a*b+a*c',
    'add_mul':'forall a b c. (a+b)*c=a*c+b*c',
    'zero_le':'forall a. Le(0,a)','succ_le_succ':'forall a b. Le(a,b) -> Le(S a,S b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'le_succ':'forall a b. Le(a,b) -> Le(a,S b)',
    'lt_not_le':'forall a b. Lt(a,b) -> Le(b,a) -> false',
    'beta_exists':'forall b c i. exists a. BetaAt(b,c,i,a)',
    'beta_unique':'forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d',
    'coefficient_exists':'forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)',
    'euler_exists':EULER_HELPERS['euler_exists'],'product_rule':EULER_HELPERS['product_rule'],
    'coefficient_swap':ASSOC_HELPERS['coefficient_swap'],'coefficient_shift':SHIFT_SOURCE,
}
ENDPOINT_OWNERS={name:'CV003' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(euler_exists='CV007',product_rule='CV007',coefficient_swap='CV014',coefficient_shift='AP037')
HELPER_DEPENDENCIES={
    'inside':('lt_not_le',),
    'euler_zero':('beta_exists','zero_le','succ_le_succ','zero_mul'),
    'euler_shift':('inside','beta_exists','beta_unique','succ_le_succ','le_trans','le_succ','mul_assoc','mul_comm'),
    'arithmetic':('mul_assoc','mul_comm','mul_add','add_mul'),
    'AP038':('euler_exists','coefficient_exists','product_rule','coefficient_swap','coefficient_shift','euler_zero','euler_shift','arithmetic'),
}


class ExpConvolutionRecurrenceError(ValueError):
    """Changed actual convolution, shared cutoff, summed argument or source."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatConvolutionCoefficient','NatEulerPrefix','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpConvolutionRecurrenceError('existing Euler/convolution definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_convolution_recurrence_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=11 or len(premises)!=5 or type(conclusion) is not Eq or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpConvolutionRecurrenceError('AP038 exact exponential convolution recurrence changed')
    return target


def source_contract():
    return dict(code='AP038',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,both_actual_input_recurrences_and_convolution_coefficients_required=True,
        shared_input_length='N+1',strict_recurrence_index_bound_required=True,
        output_recurrence='((i+1)*d)*C[i+1]=(x+y)*C[i]',
        actual_euler_tables_and_auxiliary_coefficients_constructed=True,
        zero_denominator_arguments_and_horizon_allowed=True,cancellation_used=False,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        full_convolution_tail_recurrence=False,analytic_exponential_addition=False,
        analytic_limit_claim=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_convolution_recurrence_source_pins():
    result=convolution_shift_source_pins()
    expected={'scripts/sqrt2_power_convolution_shift.py':'10e72803be0eb6b6576f9e2c3f846e24ee18dc9c0396c94da1cd7175eab9c143',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_convolution_recurrence.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpConvolutionRecurrenceError('exponential convolution source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _inside(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,OrElim
    def finish(t):
        left=t.hypothesis('inside');right=t.hypothesis('outside')
        return OrElim(t.hyp('padded'),AndElimR(left.hyp('inside')),
            BotElim(apply(specialize(right,'lt_not_le',*right.terms(('i','L'))),right.hyp('bound'),AndElimL(right.hyp('outside')))))
    return introduce(s,('b','c','L','i','a'),('bound','padded'),finish)


def _euler_zero(s,registry):
    from peano_lab.kernel.proofs import AndIntro,OrIntroL
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def chosen(t):
        N,a=t.terms(('N','a'));zero=Zero()
        bound=apply(specialize(t,'succ_le_succ',zero,N),specialize(t,'zero_le',N))
        at=apply(specialize(t,'euler',zero,a),bound,t.hyp('head'))
        at=_subst(t,registry,'BetaAt(eb,ec,0,slot)',specialize(t,'zero_mul',a),at)
        return OrIntroL(AndIntro(bound,at))
    return introduce(s,('ab','ac','eb','ec','N'),('euler',),lambda t:
        eliminate(t,specialize(t,'beta_exists',*t.terms(('ab','ac')),Zero()),('a',),'head',chosen))


def _euler_shift(s):
    from peano_lab.kernel.proofs import CongMul,EqRefl
    from peano_lab.kernel.terms import Mul,Succ
    def chosen(t):
        d,x,N,i,j,a,c,z=t.terms(('d','x','N','i','j','a','c','z'));sj=Succ(j);si=Succ(i);sn=Succ(N)
        lower=apply(specialize(t,'succ_le_succ',j,i),t.hyp('bound'))
        step_bound=apply(specialize(t,'le_trans',sj,si,N),lower,t.hyp('cutoff'))
        next_bound=apply(specialize(t,'succ_le_succ',sj,N),step_bound)
        old_bound=apply(specialize(t,'le_succ',sj,N),step_bound)
        old=apply(specialize(t,'inside',*t.terms(('ab','ac')),sn,j,a),old_bound,t.hyp('old_padded'))
        new=apply(specialize(t,'inside',*t.terms(('eb','ec')),sn,sj,c),next_bound,t.hyp('new_padded'))
        actual=apply(specialize(t,'euler',sj,z),next_bound,t.hyp('successor_entry'))
        same=apply(specialize(t,'beta_unique',*t.terms(('eb','ec')),sj,c,Mul(sj,z)),new,actual)
        adjacent=apply(specialize(t,'recurrence',j,a,z),step_bound,old,t.hyp('successor_entry'))
        return _chain(CongMul(EqRefl(d),same),_multiplicative_equal(t,Mul(d,Mul(sj,z)),Mul(Mul(sj,d),z)),adjacent)
    return introduce(s,('d','x','ab','ac','eb','ec','N','i'),('recurrence','euler','cutoff'),lambda t:
        introduce(t,('j','a','c'),('bound','old_padded','new_padded'),lambda u:
            eliminate(u,specialize(u,'beta_exists',*u.terms(('ab','ac')),Succ(u.term('j'))),('z',),'successor_entry',chosen)))


def _arithmetic(s):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        d,x,y,i,u,v,q,r=t.terms(('d','x','y','i','u','v','q','r'));si=Succ(i)
        return _chain(_multiplicative_equal(t,Mul(Mul(si,d),v),Mul(d,Mul(si,v))),
            CongMul(EqRefl(d),t.hyp('product_rule')),specialize(t,'mul_add',d,q,r),
            CongAdd(t.hyp('left_shift'),t.hyp('right_shift')),EqSym(specialize(t,'add_mul',x,y,u)))
    return introduce(s,('d','x','y','i','u','v','q','r'),('product_rule','left_shift','right_shift'),finish)


def _root(s):
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        d,x,y,N,i,u,v,q,r=t.terms(('d','x','y','N','i','u','v','q','r'));sn=Succ(N);si=Succ(i)
        a=t.terms(('ab','ac'))+(sn,);b=t.terms(('bb','bc'))+(sn,)
        ea=t.terms(('eb','ec'))+(sn,);eb=t.terms(('fb','fc'))+(sn,)
        product=apply(specialize(t,'product_rule',*(a+b+t.terms(('eb','ec','fb','fc'))+(si,v,q,r))),
            t.hyp('euler_a'),t.hyp('euler_b'),t.hyp('high'),t.hyp('left_coefficient'),t.hyp('right_coefficient'))
        head_a=apply(specialize(t,'euler_zero',*t.terms(('ab','ac','eb','ec','N'))),t.hyp('euler_a'))
        shift_a=apply(specialize(t,'euler_shift',*t.terms(('d','x','ab','ac','eb','ec','N','i'))),
            t.hyp('first_recurrence'),t.hyp('euler_a'),t.hyp('cutoff'))
        left=apply(specialize(t,'coefficient_shift',x,d,*(a+b+ea+(i,u,q))),
            head_a,shift_a,t.hyp('low'),t.hyp('left_coefficient'))
        head_b=apply(specialize(t,'euler_zero',*t.terms(('bb','bc','fb','fc','N'))),t.hyp('euler_b'))
        shift_b=apply(specialize(t,'euler_shift',*t.terms(('d','y','bb','bc','fb','fc','N','i'))),
            t.hyp('second_recurrence'),t.hyp('euler_b'),t.hyp('cutoff'))
        low_swapped=apply(specialize(t,'coefficient_swap',*(a+b+(i,u))),t.hyp('low'))
        high_swapped=apply(specialize(t,'coefficient_swap',*(a+eb+(si,r))),t.hyp('right_coefficient'))
        right=apply(specialize(t,'coefficient_shift',y,d,*(b+a+eb+(i,u,r))),head_b,shift_b,low_swapped,high_swapped)
        return apply(specialize(t,'arithmetic',*t.terms(('d','x','y','i','u','v','q','r'))),product,left,right)
    def eulers(t):
        N=t.term('N');sn=Succ(N);si=Succ(t.term('i'))
        left=t.terms(('eb','ec'))+(sn,)+t.terms(('bb','bc'))+(sn,si)
        return eliminate(t,specialize(t,'coefficient_exists',*left),('q',),'left_coefficient',lambda u:
            eliminate(u,specialize(u,'coefficient_exists',*u.terms(('ab','ac')),Succ(u.term('N')),
                *u.terms(('fb','fc')),Succ(u.term('N')),Succ(u.term('i'))),('r',),'right_coefficient',chosen))
    return introduce(s,PARAMETERS,('first_recurrence','second_recurrence','cutoff','low','high'),lambda t:
        eliminate(t,specialize(t,'euler_exists',*t.terms(('ab','ac')),Succ(t.term('N'))),('eb','ec'),'euler_a',lambda u:
            eliminate(u,specialize(u,'euler_exists',*u.terms(('bb','bc')),Succ(u.term('N'))),('fb','fc'),'euler_b',eulers)))


def prove_exp_convolution_recurrence(*,limits=None):
    registry=definition_registry()
    factories={'inside':_inside,'euler_zero':lambda s:_euler_zero(s,registry),'euler_shift':_euler_shift,'arithmetic':_arithmetic,'AP038':_root}
    return assemble_mixed_certificate(code='AP038',target=frozen_exp_convolution_recurrence_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories,pins=exp_convolution_recurrence_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
