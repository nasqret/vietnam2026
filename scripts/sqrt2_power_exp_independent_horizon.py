"""AP065: requested finite Cauchy accuracy across independent exponential codes.

The coarse and fine computations may use different positive denominators,
heads and beta codes at equal rational arguments. Construct the fine short
sum, prove its cross-value identity with the coarse sum, and use the actual
finite tail bound. No code equality or analytic limit is assumed.
"""
from hashlib import sha256

from sqrt2_power_exp_requested_truncation import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,source_registry,exp_requested_truncation_source_pins,
    NAMED_SOURCE as REQUESTED_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_recurrence_independence import NAMED_SOURCE as INDEPENDENCE_SOURCE,exp_recurrence_independence_source_pins
from sqrt2_power_exp_supplied_large_product import INDEPENDENCE_ARCHIVE,TWO_ERROR_ARCHIVE,CONVOLUTION_ARCHIVE,HORIZON_HELPERS
from sqrt2_power_quadratic_trace_exists import witness
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-independent-horizon-v1'
D='K+(L*K+n)'
H=f'S({D})+N'
PARAMETERS=('d','e','x','y','L','K','n','N','ab','ac','bb','bc','h','g','s','t','r')
PREMISES=('~d=0','~e=0','x*e=y*d','Le(y,L*e)','Le(2*L,K)',
    f'NatScaledExpRecurrence(d,x,ab,ac,{D})',f'NatScaledExpRecurrence(e,y,bb,bc,{H})',
    'BetaAt(ab,ac,0,h)','BetaAt(bb,bc,0,g)',f'Sum(ab,ac,S({D}),s)',f'Sum(bb,bc,S({H}),t)','Pow(2,n,r)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> ~r=0 /\\ (Le(g*s,h*t) /\\ Le(r*(h*t),r*(g*s)+h*g))'
TARGET_SHA256='650e729c29cf242dce7af6b0b54b08b896036d8256a6ec458c80134305b3ee39'
HELPER_SOURCES={'arithmetic':'forall r h g s z t. g*s=h*z -> Le(z,t) -> Le(r*t,r*z+g) -> Le(g*s,h*t) /\\ Le(r*(h*t),r*(g*s)+h*g)'}
HELPER_TARGET_SHA256={'arithmetic':'fa6e80b712be67ddd8e54d255835309fff7a3e8fd0380a89997a9130f57b47c9'}
REQUESTED_ARCHIVE=dict(case='AP063',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-requested-truncation-v1/generation-process.json.gz',
    bytes=71366,sha256='72b941cbd83f1a4739ea7c0246af1f082e36d8d72bee2dfde1058d4e31fdc449',
    raw_bytes=907695,raw_sha256='0449c63f8b97b8cc810aa733fd8634fc1809bc70bc68e2a8942f2d0a29fe8bf2',
    bundle_bytes=486928,bundle_sha256='b057dee9e4adb11a462fbfd234cd9eb053c0e7275d2c3171ed29df76a3870023',
    nodes=171,root=170,target_ast_sha256='87d46a5afea3d3cb839af399daa22055d469c3506826aa7404168a3b15983873')
ARCHIVES=(INDEPENDENCE_ARCHIVE,REQUESTED_ARCHIVE,TWO_ERROR_ARCHIVE,CONVOLUTION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'same_value':INDEPENDENCE_SOURCE,'requested':REQUESTED_SOURCE,'restrict':HORIZON_HELPERS['restrict'],
    'sum_exists':'forall b c N. exists n. Sum(b,c,N,n)',
    'le_refl':'forall a. Le(a,a)','le_succ':'forall a b. Le(a,b) -> Le(a,S b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'add_comm':'forall a b. a+b=b+a',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_add':'forall a b c. a*(b+c)=a*b+a*c',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(same_value='AP060',requested='AP063',restrict='CV101',sum_exists='CV003')
HELPER_DEPENDENCIES={'arithmetic':('mul_left_mono','mul_assoc','mul_comm','mul_add'),
    'AP065':('same_value','requested','restrict','sum_exists','le_refl','le_succ','le_trans','add_comm','arithmetic')}


class ExpIndependentHorizonError(ValueError):
    """Changed independent computations, rational argument or finite horizon."""


def frozen_exp_independent_horizon_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=17 or len(premises)!=12 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpIndependentHorizonError('AP065 exact independent-code variable-horizon accuracy changed')
    return target


def source_contract():
    return dict(code='AP065',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=12,both_supplied_recurrences_heads_codes_sums_and_precision_power_preserved=True,
        positive_denominators_required=True,rational_argument_identity='x*e=y*d',argument_bound='y<=L*e',
        initial_cutoff='2*L<=K',coarse_degree='D=K+(L*K+n)',fine_degree='(D+1)+N',
        requested_scale='r=2^n',requested_scale_proved_nonzero=True,
        cross_normalized_bounds='g*s<=h*t; r*(h*t)<=r*(g*s)+h*g',
        independent_denominators_heads_and_codes_allowed=True,fine_short_sum_constructed_not_assumed=True,
        uniform_in_extra_finite_horizon=True,zero_arguments_heads_and_precision_allowed=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        code_number_equality_claimed=False,analytic_limit_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_independent_horizon_source_pins():
    result=exp_requested_truncation_source_pins()
    for name,pin in exp_recurrence_independence_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpIndependentHorizonError('independent horizon dependency source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_requested_truncation.py':'c717b1459260df08516efabcebcbca3f69ee271c2122e67f404f8ef8cb20ebc7',
        'scripts/sqrt2_power_exp_recurrence_independence.py':'683487ceef52ea2116f955d71e185356cf15f9d82f7a27daaf9ec5871c4ca149',
        'scripts/sqrt2_power_exp_supplied_large_product.py':'1ac37df93cbfd74f08476c9584804824ddf64bd272b69fbd13c0fc9f589e360c',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_independent_horizon.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpIndependentHorizonError('independent-horizon source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(u):
        r,h,g,a,z,t=u.terms(('r','h','g','s','z','t'))
        lower=apply(specialize(u,'mul_left_mono',z,t,h),u.hyp('lower'))
        lower=_left(u,registry,lower,Mul(h,t),EqSym(u.hyp('identity')))
        upper=apply(specialize(u,'mul_left_mono',Mul(r,t),Add(Mul(r,z),g),h),u.hyp('upper'))
        left=_multiplicative_equal(u,Mul(h,Mul(r,t)),Mul(r,Mul(h,t)))
        right=_chain(specialize(u,'mul_add',h,Mul(r,z),g),
            CongAdd(_multiplicative_equal(u,Mul(h,Mul(r,z)),Mul(r,Mul(h,z))),EqRefl(Mul(h,g))),
            CongAdd(CongMul(EqRefl(r),EqSym(u.hyp('identity'))),EqRefl(Mul(h,g))))
        upper=_left(u,registry,upper,Mul(h,Add(Mul(r,z),g)),left)
        upper=_right(u,registry,upper,Mul(r,Mul(h,t)),right)
        return conjunction(lower,upper)
    return introduce(s,('r','h','g','s','z','t'),('identity','lower','upper'),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def chosen(u):
        d,e,x,y,L,K,n,N,h,g,a,t,r,z=u.terms(('d','e','x','y','L','K','n','N','h','g','s','t','r','z'))
        m=Add(Mul(L,K),n);D=Add(K,m);length=Succ(D);H=Add(length,N)
        bound=apply(specialize(u,'le_trans',D,length,H),
            apply(specialize(u,'le_succ',D,D),specialize(u,'le_refl',D)),
            witness((N,),specialize(u,'add_comm',N,length)))
        restricted=apply(specialize(u,'restrict',e,y,*u.terms(('bb','bc')),D,H),bound,u.hyp('fine_recurrence'))
        equal=apply(specialize(u,'same_value',d,e,x,y,D,*u.terms(('ab','ac','bb','bc')),h,g,a,z),
            u.hyp('d_nonzero'),u.hyp('e_nonzero'),u.hyp('argument_equal'),u.hyp('coarse_recurrence'),restricted,
            u.hyp('coarse_head'),u.hyp('fine_head'),u.hyp('coarse_sum'),u.hyp('fine_short'))
        cutoff=instantiate(Axiom('PA4'),K,m);shift=CongAdd(cutoff,EqRefl(N))
        recurrence=_subst(u,registry,'NatScaledExpRecurrence(e,y,bb,bc,slot)',EqSym(shift),u.hyp('fine_recurrence'))
        short=_subst(u,registry,'Sum(bb,bc,slot,z)',EqSym(cutoff),u.hyp('fine_short'))
        whole=_subst(u,registry,'Sum(bb,bc,S(slot),t)',EqSym(shift),u.hyp('fine_sum'))
        error=apply(specialize(u,'requested',e,y,L,K,n,N,*u.terms(('bb','bc')),g,z,t,r),
            u.hyp('e_nonzero'),u.hyp('argument'),u.hyp('threshold'),recurrence,u.hyp('fine_head'),short,whole,u.hyp('precision_power'))
        both=apply(specialize(u,'arithmetic',r,h,g,a,z,t),equal,field(error,1,3),field(error,2,3))
        return conjunction(field(error,0,3),AndElimL(both),AndElimR(both))
    def start(u):
        D=Add(u.term('K'),Add(Mul(u.term('L'),u.term('K')),u.term('n')))
        return eliminate(u,specialize(u,'sum_exists',*u.terms(('bb','bc')),Succ(D)),('z',),'fine_short',chosen)
    return introduce(s,PARAMETERS,('d_nonzero','e_nonzero','argument_equal','argument','threshold','coarse_recurrence','fine_recurrence',
        'coarse_head','fine_head','coarse_sum','fine_sum','precision_power'),start)


def prove_exp_independent_horizon(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP065',target=frozen_exp_independent_horizon_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP065':lambda s:_root(s,registry)},
        pins=exp_independent_horizon_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
