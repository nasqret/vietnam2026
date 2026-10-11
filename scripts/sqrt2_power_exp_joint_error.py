"""AP081: explicit input and truncation errors for independent finite sums.

Construct the fine computation's short prefix and apply AP075 there. AP063
controls its actual remaining tail. Keep the one-sided budgets separate:
one unit in the coarse-minus-fine direction, two units in the other.
"""
from hashlib import sha256

from sqrt2_power_exp_dyadic_continuity import (
    ROOT,Scope,introduce,eliminate,apply,specialize,canonical,json_hash,
    source_registry,definition_registry,exp_dyadic_continuity_source_pins,
    NAMED_SOURCE as CONTINUITY_SOURCE,PRECISION,BOUND_ARCHIVE,
)
from sqrt2_power_exp_requested_truncation import NAMED_SOURCE as TAIL_SOURCE,exp_requested_truncation_source_pins
from sqrt2_power_exp_supplied_large_product import TWO_ERROR_ARCHIVE,CONVOLUTION_ARCHIVE,HORIZON_HELPERS
from sqrt2_power_quadratic_trace_exists import conjunction,field,witness
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-joint-error-v1'
D='K+(L*K+n)'
H=f'S({D})+N'
PARAMETERS=('L','K','d','e','x','y','g','n','N','ab','ac','bb','bc','a0','b0','s','t','r','p')
PREMISES=('~d=0','~e=0','Le(x,L*d)','Le(y,L*e)','Le(2*L,K)','Le(d*y,e*x+g)','Le(e*x,d*y+g)',
    f'NatScaledExpRecurrence(d,x,ab,ac,{D})',f'NatScaledExpRecurrence(e,y,bb,bc,{H})',
    'BetaAt(ab,ac,0,a0)','BetaAt(bb,bc,0,b0)',f'Sum(ab,ac,S({D}),s)',f'Sum(bb,bc,S({H}),t)',
    'Pow(2,n,r)',f'Pow(2,{PRECISION},p)','Le(p*g,d*e)')
BOUNDS='Le(r*(b0*s),r*(a0*t)+a0*b0) /\\ Le(r*(a0*t),r*(b0*s)+2*(a0*b0))'
CONCLUSION='~r=0 /\\ (~p=0 /\\ ('+BOUNDS+'))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='7cd2d99c4a00cc142b8b0811c8a227ab0423f1aaad7a8f745af23c75e8b7b638'
HELPER_SOURCES={'arithmetic':'forall r a b s z t. Le(r*(b*s),r*(a*z)+a*b) -> Le(r*(a*z),r*(b*s)+a*b) -> Le(z,t) -> Le(r*t,r*z+b) -> Le(r*(b*s),r*(a*t)+a*b) /\\ Le(r*(a*t),r*(b*s)+2*(a*b))'}
HELPER_TARGET_SHA256={'arithmetic':'a9401517bde92e0eafd792da63014901dd6cfd7fd52d5abac43fa6b08c0461c6'}
CONTINUITY_ARCHIVE=dict(case='AP075',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-dyadic-continuity-v1/generation-process.json.gz',
    bytes=111279,sha256='f3ea6dff0a10d148fa10ec5cc05ffbbac546f39dcc2691f4f8f13f2cb6b02c76',
    raw_bytes=2279973,raw_sha256='5e63c11a163013a473c49710b8772e15ec507e61452eedb29c1feee3155171ac',
    bundle_bytes=1349580,bundle_sha256='619b8df88cde20ce381fc9c7a79e48d8c81e09e3824a99bd36b97584bee770af',
    nodes=299,root=298,target_ast_sha256='52a66a0660b914cf13ff19d92ee7d59293e729e8ef8813555714e427ec0646c4')
TAIL_ARCHIVE=dict(case='AP063',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-requested-truncation-v1/generation-process.json.gz',
    bytes=71366,sha256='72b941cbd83f1a4739ea7c0246af1f082e36d8d72bee2dfde1058d4e31fdc449',
    raw_bytes=907695,raw_sha256='0449c63f8b97b8cc810aa733fd8634fc1809bc70bc68e2a8942f2d0a29fe8bf2',
    bundle_bytes=486928,bundle_sha256='b057dee9e4adb11a462fbfd234cd9eb053c0e7275d2c3171ed29df76a3870023',
    nodes=171,root=170,target_ast_sha256='87d46a5afea3d3cb839af399daa22055d469c3506826aa7404168a3b15983873')
ARCHIVES=(CONTINUITY_ARCHIVE,TAIL_ARCHIVE,TWO_ERROR_ARCHIVE,CONVOLUTION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'continuity':CONTINUITY_SOURCE,'tail':TAIL_SOURCE,'restrict':HORIZON_HELPERS['restrict'],
    'sum_exists':'forall b c N. exists n. Sum(b,c,N,n)',
    'le_refl':'forall a. Le(a,a)','le_succ':'forall a b. Le(a,b) -> Le(a,S b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'add_right_mono':'forall a b c. Le(a,b) -> Le(a+c,b+c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','add_assoc':'forall a b c. (a+b)+c=a+(b+c)',
    'add_comm':'forall a b. a+b=b+a','mul_succ_left':'forall a b. (S a)*b=a*b+b','one_mul':'forall a. 1*a=a'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(continuity='AP075',tail='AP063',restrict='CV101',sum_exists='CV003')
HELPER_DEPENDENCIES={'arithmetic':('mul_left_mono','add_right_mono','le_trans','mul_assoc','mul_comm','mul_add','add_assoc','mul_succ_left','one_mul'),
    'AP081':('continuity','tail','restrict','sum_exists','le_refl','le_succ','le_trans','add_comm','arithmetic')}


class ExpJointError(ValueError):
    """Changed independently supplied computations, cutoffs or error budgets."""


def frozen_exp_joint_error_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=19 or len(premises)!=16 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpJointError('AP081 exact combined finite input and tail error changed')
    return target


def source_contract():
    return dict(code='AP081',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=16,both_actual_recurrences_heads_sums_and_codes_preserved=True,
        independent_denominators_heads_and_codes_allowed=True,both_dyadic_powers_preserved_and_nonzero=True,
        argument_bounds=['x<=L*d','y<=L*e'],initial_threshold='2*L<=K',
        coarse_degree='D=K+(L*K+n)',fine_degree='(D+1)+N',input_precision='9*(L+1)+n+1',
        symmetric_input_error='abs(d*y-e*x)<=g; p*g<=d*e',
        coarse_minus_fine_allowance='a0*b0',fine_minus_coarse_allowance='2*(a0*b0)',
        constructed_middle_prefix=True,input_and_tail_budgets_separate=True,
        argument_order_assumed=False,zero_arguments_heads_and_precision_allowed=True,
        uniform_in_extra_finite_horizon=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_continuity_or_limit_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_joint_error_source_pins():
    result=exp_dyadic_continuity_source_pins()
    for name,pin in exp_requested_truncation_source_pins().items():
        if name in result and result[name]!=pin:raise ExpJointError('joint-error dependency source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_dyadic_continuity.py':'a08d8f5856713b43084ad457aa45cee21401b83c27abfbfd7db176f9f0763217',
        'scripts/sqrt2_power_exp_requested_truncation.py':'c717b1459260df08516efabcebcbca3f69ee271c2122e67f404f8ef8cb20ebc7',
        'scripts/sqrt2_power_exp_supplied_large_product.py':'1ac37df93cbfd74f08476c9584804824ddf64bd272b69fbd13c0fc9f589e360c',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_quadratic_trace_exists.py','scripts/sqrt2_power_exp_two_sided_continuity.py',
                 'scripts/sqrt2_power_convolution_unit.py','scripts/sqrt2_power_finite_power_evaluation.py',
                 'scripts/sqrt2_power_quadratic_height.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise ExpJointError('unbound joint-error proof constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_exp_joint_error.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:raise ExpJointError('joint-error source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish(u):
        r,a,b,s,z,t=u.terms(('r','a','b','s','z','t'))
        az,at,bs=Mul(a,z),Mul(a,t),Mul(b,s);ab=Mul(a,b)
        raz,rat,rbs=Mul(r,az),Mul(r,at),Mul(r,bs)
        lower=apply(specialize(u,'mul_left_mono',z,t,a),u.hyp('tail_lower'))
        lower=apply(specialize(u,'mul_left_mono',az,at,r),lower)
        lower=apply(specialize(u,'add_right_mono',raz,rat,ab),lower)
        lower=apply(specialize(u,'le_trans',rbs,Add(raz,ab),Add(rat,ab)),u.hyp('input_forward'),lower)
        upper=apply(specialize(u,'mul_left_mono',Mul(r,t),Add(Mul(r,z),b),a),u.hyp('tail_upper'))
        upper=_left(u,registry,upper,Mul(a,Add(Mul(r,z),b)),_multiplicative_equal(u,Mul(a,Mul(r,t)),rat))
        exact=_chain(specialize(u,'mul_add',a,Mul(r,z),b),
            CongAdd(_multiplicative_equal(u,Mul(a,Mul(r,z)),raz),EqRefl(ab)))
        upper=_right(u,registry,upper,rat,exact)
        error=apply(specialize(u,'add_right_mono',raz,Add(rbs,ab),ab),u.hyp('input_backward'))
        upper=apply(specialize(u,'le_trans',rat,Add(raz,ab),Add(Add(rbs,ab),ab)),upper,error)
        twice=_chain(specialize(u,'mul_succ_left',one,ab),CongAdd(specialize(u,'one_mul',ab),EqRefl(ab)))
        exact=_chain(specialize(u,'add_assoc',rbs,ab,ab),CongAdd(EqRefl(rbs),EqSym(twice)))
        return conjunction(lower,_right(u,registry,upper,rat,exact))
    return introduce(s,('r','a','b','s','z','t'),('input_forward','input_backward','tail_lower','tail_upper'),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def chosen(u):
        L,K,d,e,x,y,g,n,N,ab,ac,bb,bc,a,b,s,t,r,p,z=u.terms(PARAMETERS+('z',))
        m=Add(Mul(L,K),n);D=Add(K,m);length=Succ(D);H=Add(length,N)
        bound=apply(specialize(u,'le_trans',D,length,H),
            apply(specialize(u,'le_succ',D,D),specialize(u,'le_refl',D)),
            witness((N,),specialize(u,'add_comm',N,length)))
        restricted=apply(specialize(u,'restrict',e,y,bb,bc,D,H),bound,u.hyp('fine_recurrence'))
        continuity=apply(specialize(u,'continuity',L,d,e,x,y,g,n,D,ab,ac,bb,bc,a,b,s,z,r,p),
            *(u.hyp(name) for name in ('nonzero_d','nonzero_e','bound_a','bound_b','forward','backward')),
            u.hyp('coarse_recurrence'),restricted,u.hyp('coarse_head'),u.hyp('fine_head'),u.hyp('coarse_sum'),u.hyp('fine_short'),
            u.hyp('output_power'),u.hyp('input_power'),u.hyp('input_budget'))
        cutoff=instantiate(Axiom('PA4'),K,m);shift=CongAdd(cutoff,EqRefl(N))
        recurrence=_subst(u,registry,'NatScaledExpRecurrence(e,y,bb,bc,slot)',EqSym(shift),u.hyp('fine_recurrence'))
        short=_subst(u,registry,'Sum(bb,bc,slot,z)',EqSym(cutoff),u.hyp('fine_short'))
        whole=_subst(u,registry,'Sum(bb,bc,S(slot),t)',EqSym(shift),u.hyp('fine_sum'))
        tail=apply(specialize(u,'tail',e,y,L,K,n,N,bb,bc,b,z,t,r),u.hyp('nonzero_e'),u.hyp('bound_b'),u.hyp('threshold'),
            recurrence,u.hyp('fine_head'),short,whole,u.hyp('output_power'))
        both=apply(specialize(u,'arithmetic',r,a,b,s,z,t),field(continuity,2,4),field(continuity,3,4),field(tail,1,3),field(tail,2,3))
        return conjunction(field(continuity,0,4),field(continuity,1,4),AndElimL(both),AndElimR(both))
    def start(u):
        D=Add(u.term('K'),Add(Mul(u.term('L'),u.term('K')),u.term('n')))
        return eliminate(u,specialize(u,'sum_exists',*u.terms(('bb','bc')),Succ(D)),('z',),'fine_short',chosen)
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','bound_a','bound_b','threshold','forward','backward',
        'coarse_recurrence','fine_recurrence','coarse_head','fine_head','coarse_sum','fine_sum','output_power','input_power','input_budget'),start)


def prove_exp_joint_error(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP081',target=frozen_exp_joint_error_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP081':lambda s:_root(s,registry)},pins=exp_joint_error_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
