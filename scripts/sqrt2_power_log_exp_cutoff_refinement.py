"""AP083: the actual 18*r+2 cutoff pays both log/exp refinement errors.

Replay the supplied power computations to prove 54*r<=3^(18*r+2)
and 4*r<=2^(18*r+2). Absorb AP082's two errors and cancel only
proved positive factors. No limit or change of the fixed c-program.
"""
from hashlib import sha256

from sqrt2_power_log_exp_refinement import (
    ROOT,Scope,introduce,eliminate,apply,specialize,conjunction,field,canonical,json_hash,
    definition_registry,log_exp_refinement_source_pins,NAMED_SOURCE as REFINEMENT_SOURCE,
    BOUND_ARCHIVE,
)
from sqrt2_power_half_log_precision import (
    half_log_precision_source_pins,HELPER_SOURCES as BINARY_HELPERS,
    BUDGET_ARCHIVE,COMPARISON_ARCHIVE,
)
from sqrt2_power_log_exp_budget import HELPER_SOURCES as TERNARY_HELPERS
from sqrt2_power_positive_power_comparison import ENDPOINT_SOURCES as POWER_ENDPOINTS
from sqrt2_power_quadratic_trace_exists import witness
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_fixed_precision_threshold import _ground_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-log-exp-cutoff-refinement-v1'
M='S(S(18*r))'
PARAMETERS=('r','d','e','ab','ac','bb','bc','l','x','z','p','q','N','cb','cc','eb','ec','a0','b0','u','v','P')
PREMISES=('~d=0','~e=0',f'NatAtanhPrefix(d,ab,ac,{M})',f'NatAtanhPrefix(e,bb,bc,({M})+l)',
    f'NatHornerValue(ab,ac,3,{M},x)',f'NatHornerValue(bb,bc,3,({M})+l,z)',
    f'Pow(3,{M},p)',f'Pow(3,({M})+l,q)',
    f'NatScaledExpRecurrence(d*p,3*x,cb,cc,{M})',f'NatScaledExpRecurrence(e*q,3*z,eb,ec,(S({M}))+N)',
    'BetaAt(cb,cc,0,a0)','BetaAt(eb,ec,0,b0)',f'Sum(cb,cc,S({M}),u)',f'Sum(eb,ec,S((S({M}))+N),v)',f'Pow(2,{M},P)')
CONCLUSION='~p=0 /\\ (~q=0 /\\ (~P=0 /\\ (~(d*p)=0 /\\ (~(e*q)=0 /\\ (Le(b0*u,a0*v) /\\ Le(r*(a0*v),r*(b0*u)+a0*b0))))))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='97d070681313d49334933a292e949acae3f61cc484c18b5a122d05060269d1c5'
HELPER_SOURCES={
    'budgets':f'forall r p P. Pow(3,{M},p) -> Pow(2,{M},P) -> Le((2*(9*3))*r,p) /\\ Le(2*(2*r),P)',
    'arithmetic':'forall r p P a b u v. ~p=0 -> ~P=0 -> Le((2*(9*3))*r,p) -> Le(2*(2*r),P) -> Le((p*P)*(a*v),(p*P)*(b*u)+((9*3)*P+2*p)*(a*b)) -> Le(r*(a*v),r*(b*u)+a*b)',
}
HELPER_TARGET_SHA256={'budgets':'3d88e59013879189aab050d02176901d0074e65a79222eafb0b439c0d4a667b3','arithmetic':'efd342de02539fd4660a66a24082a80fcb4ef9ea24eb57e58bce0594d9363c2f'}
REFINEMENT_ARCHIVE=dict(case='AP082',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-exp-refinement-v1/generation-process.json.gz',
    bytes=83922,sha256='ef36aa0c4ccae3b2abbf9ddcd08879e41bfeae4722465e3a999722e153359b55',
    raw_bytes=1512006,raw_sha256='8fb69065eddf8392adc748921171e9fe7e03ff7b0bcaa6cf95fb62be3c2691bd',
    bundle_bytes=892431,bundle_sha256='0261db5cc15244a1345941dd847fc8bf283af92dbb74cf19ff6a9f22168eff88',
    nodes=229,root=228,target_ast_sha256='bccfdfa515c324f3b34a5a205185f1a81d590d8d27d1b41dcba91fbbd65883cc')
PRECISION_ARCHIVE=dict(case='AP046',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-precision-v1/generation-process.json.gz',
    bytes=33965,sha256='a8aa5cf416eba42d7ac60677297def6b0b582b83effc747df788f37f1425a8cd',
    raw_bytes=213916,raw_sha256='1ced030dc8e04ad27296497367bd7f66e58f7d7cf2c99b2dd65ae63a28613f4a',
    bundle_bytes=78373,bundle_sha256='96815002d9cbada491bb67202df76d032ac56ed7b8f0c85b32d92a1406e3368a',
    nodes=37,root=36,target_ast_sha256='936a988b2a6fae61ebb3206a2a33746d5c8ad2e23501f642b0528b6b9e0e7877')
ARCHIVES=(REFINEMENT_ARCHIVE,BUDGET_ARCHIVE,PRECISION_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'refinement':REFINEMENT_SOURCE,'binary_growth':BINARY_HELPERS['growth'],
    'ternary_growth':TERNARY_HELPERS['growth'],'power_step':POWER_ENDPOINTS['power_step'],
    'le_refl':'forall a. Le(a,a)','le_succ':'forall a b. Le(a,b) -> Le(a,S b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'add_right_mono':'forall a b c. Le(a,b) -> Le(a+c,b+c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','mul_succ_left':'forall a b. (S a)*b=a*b+b',
    'one_mul':'forall a. 1*a=a','mul_nonzero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0',
    'succ_nonzero':'forall a. ~S a=0','mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(refinement='AP082',binary_growth='AP046',ternary_growth='AP033',power_step='AP010')
HELPER_DEPENDENCIES={
    'budgets':('binary_growth','ternary_growth','power_step','le_refl','le_succ','le_trans','mul_right_mono','mul_assoc','mul_comm'),
    'arithmetic':('mul_left_mono','mul_right_mono','add_left_mono','add_right_mono','le_trans','mul_assoc','mul_comm',
        'mul_add','mul_succ_left','one_mul','mul_nonzero','succ_nonzero','mul_le_cancel'),
    'AP083':('refinement','budgets','arithmetic'),
}


class LogExpCutoffRefinementError(ValueError):
    """Changed actual powers, independent computations or proved cutoff budget."""


def frozen_log_exp_cutoff_refinement_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=22 or len(premises)!=15 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LogExpCutoffRefinementError('AP083 exact cutoff refinement target changed')
    return target


def source_contract():
    return dict(code='AP083',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=15,all_actual_logarithm_exponential_and_power_computations_preserved=True,
        independent_coefficient_scales_codes_and_exp_heads_allowed=True,
        auxiliary_cutoff='M=18*r+2',fine_log_length='M+l',fine_exp_degree='M+1+N',
        budgets_proved_not_assumed=['54*r<=3^M','4*r<=2^M'],finite_error='r*(a0*v)<=r*(b0*u)+a0*b0',
        monotone_cross_value='b0*u<=a0*v',positive_factors_cancelled_only_after_proof=True,
        symbolic_precision_scale=True,zero_r_l_N_and_heads_allowed=True,
        rational_reading_requires_positive_r_and_heads=True,new_induction_count=0,new_induction_needed=False,
        new_definition_ids=[],definition_admissions=0,analytic_log_exp_identity_claimed=False,analytic_limit_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def log_exp_cutoff_refinement_source_pins():
    result=log_exp_refinement_source_pins()
    for name,pin in half_log_precision_source_pins().items():
        if name in result and result[name]!=pin:raise LogExpCutoffRefinementError('cutoff refinement source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_log_exp_refinement.py':'51d0cc8fecf2f4289ac4da3da4a21c660939dac4760580b8372443f861d3b104',
        'scripts/sqrt2_power_half_log_precision.py':'a009a1c8acc576cc5c2a244580c239aa2d82b799590b3c777b8ca77e245f7579',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_log_exp_budget.py','scripts/sqrt2_power_positive_power_comparison.py',
                 'scripts/sqrt2_power_quadratic_trace_exists.py','scripts/sqrt2_power_exp_two_sided_continuity.py',
                 'scripts/sqrt2_power_quadratic_height.py','scripts/sqrt2_power_finite_power_evaluation.py',
                 'scripts/sqrt2_power_fixed_precision_threshold.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise LogExpCutoffRefinementError('unbound cutoff refinement constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_log_exp_cutoff_refinement.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:raise LogExpCutoffRefinementError('cutoff source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _budgets(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    two,three,four,nine,fourteen,eighteen=map(parse_term,('2','3','4','9','14','18'))
    def chosen(t):
        r,p,P,q=t.terms(('r','p','P','previous'));base=Mul(eighteen,r);M=Succ(Succ(base));index=Succ(base)
        below=apply(specialize(t,'le_succ',base,base),specialize(t,'le_refl',base))
        below=apply(specialize(t,'le_succ',base,Succ(base)),below)
        above=apply(specialize(t,'ternary_growth',index,q),AndElimL(t.hyp('previous_power')))
        bound=apply(specialize(t,'le_trans',base,M,q),below,above)
        bound=apply(specialize(t,'mul_right_mono',base,q,three),bound)
        lhs=Mul(Mul(two,Mul(nine,three)),r)
        eq=_chain(CongMul(CongMul(_ground_equal(eighteen,Mul(two,nine)),EqRefl(r)),EqRefl(three)),
            _multiplicative_equal(t,Mul(Mul(Mul(two,nine),r),three),lhs))
        bound=_left(t,registry,bound,Mul(q,three),eq)
        bound=_right(t,registry,bound,lhs,EqSym(AndElimR(t.hyp('previous_power'))))
        small=witness((fourteen,),_ground_equal(Add(fourteen,four),eighteen))
        small=apply(specialize(t,'mul_right_mono',four,eighteen,r),small)
        small=_left(t,registry,small,base,_chain(CongMul(_ground_equal(four,Mul(two,two)),EqRefl(r)),specialize(t,'mul_assoc',two,two,r)))
        binary_lhs=Mul(two,Mul(two,r));upper=base
        for _ in range(3):
            small=apply(specialize(t,'le_succ',binary_lhs,upper),small);upper=Succ(upper)
        growth=apply(specialize(t,'binary_growth',M,P),t.hyp('binary_power'))
        binary=apply(specialize(t,'le_trans',binary_lhs,Succ(M),P),small,growth)
        return conjunction(bound,binary)
    def start(t):
        r,p=t.terms(('r','p'));index=Succ(Mul(eighteen,r));M=Succ(index)
        previous=apply(specialize(t,'power_step',three,index,M,p),EqRefl(M),t.hyp('ternary_power'))
        return eliminate(t,previous,('previous',),'previous_power',chosen)
    return introduce(s,('r','p','P'),('ternary_power','binary_power'),start)


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    one,two,three,nine=map(parse_term,('1','2','3','9'))
    def finish(t):
        r,p,P,a,b,u,v=t.terms(('r','p','P','a','b','u','v'));scale=Mul(p,P);av,bu,ab=Mul(a,v),Mul(b,u),Mul(a,b)
        A,B=Mul(Mul(nine,three),P),Mul(two,p);C=Add(A,B);rC=Mul(r,C)
        L,J=Mul(Mul(two,Mul(nine,three)),r),Mul(two,Mul(two,r));LP,Jp=Mul(L,P),Mul(J,p)
        first=apply(specialize(t,'mul_right_mono',L,p,P),t.hyp('log_budget'))
        second=apply(specialize(t,'mul_right_mono',J,P,p),t.hyp('exp_budget'))
        second=_right(t,registry,second,Jp,specialize(t,'mul_comm',P,p))
        first=apply(specialize(t,'add_right_mono',LP,scale,Jp),first)
        second=apply(specialize(t,'add_left_mono',Jp,scale,scale),second)
        budget=apply(specialize(t,'le_trans',Add(LP,Jp),Add(scale,Jp),Add(scale,scale)),first,second)
        normalize=_chain(CongAdd(_multiplicative_equal(t,LP,Mul(two,Mul(r,A))),_multiplicative_equal(t,Jp,Mul(two,Mul(r,B)))),
            EqSym(specialize(t,'mul_add',two,Mul(r,A),Mul(r,B))),CongMul(EqRefl(two),EqSym(specialize(t,'mul_add',r,A,B))))
        double=_chain(specialize(t,'mul_succ_left',one,scale),CongAdd(specialize(t,'one_mul',scale),EqRefl(scale)))
        budget=_left(t,registry,budget,Add(scale,scale),normalize)
        budget=_right(t,registry,budget,Mul(two,rC),EqSym(double))
        budget=apply(specialize(t,'mul_le_cancel',two,rC,scale),specialize(t,'succ_nonzero',one),budget)
        old=Add(Mul(scale,bu),Mul(C,ab));out=apply(specialize(t,'mul_left_mono',Mul(scale,av),old,r),t.hyp('error'))
        X,Y=Mul(r,av),Mul(r,bu);base=Mul(scale,Y);err=Mul(rC,ab)
        out=_left(t,registry,out,Mul(r,old),_multiplicative_equal(t,Mul(r,Mul(scale,av)),Mul(scale,X)))
        rhs=_chain(specialize(t,'mul_add',r,Mul(scale,bu),Mul(C,ab)),
            CongAdd(_multiplicative_equal(t,Mul(r,Mul(scale,bu)),base),_multiplicative_equal(t,Mul(r,Mul(C,ab)),err)))
        out=_right(t,registry,out,Mul(scale,X),rhs)
        allowance=apply(specialize(t,'mul_right_mono',rC,scale,ab),budget)
        allowance=apply(specialize(t,'add_left_mono',err,Mul(scale,ab),base),allowance)
        out=apply(specialize(t,'le_trans',Mul(scale,X),Add(base,err),Add(base,Mul(scale,ab))),out,allowance)
        out=_right(t,registry,out,Mul(scale,X),EqSym(specialize(t,'mul_add',scale,Y,ab)))
        nonzero=apply(specialize(t,'mul_nonzero',p,P),t.hyp('nonzero_p'),t.hyp('nonzero_P'))
        return apply(specialize(t,'mul_le_cancel',scale,X,Add(Y,ab)),nonzero,out)
    return introduce(s,('r','p','P','a','b','u','v'),('nonzero_p','nonzero_P','log_budget','exp_budget','error'),finish)


def _root(s):
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    eighteen=parse_term('18')
    def finish(t):
        r,d,e,ab,ac,bb,bc,l,x,z,p,q,N,cb,cc,eb,ec,a,b,u,v,P=t.terms(PARAMETERS)
        k=Succ(Mul(eighteen,r));M=Succ(k)
        result=apply(specialize(t,'refinement',d,e,ab,ac,bb,bc,k,l,x,z,p,q,M,N,cb,cc,eb,ec,a,b,u,v,P),
            *(t.hyp(name) for name in ('nonzero_d','nonzero_e','log_coarse','log_fine','value_coarse','value_fine','power_p','power_q',
                'exp_coarse','exp_fine','head_coarse','head_fine','sum_coarse','sum_fine','power_P')))
        budgets=apply(specialize(t,'budgets',r,p,P),t.hyp('power_p'),t.hyp('power_P'))
        error=apply(specialize(t,'arithmetic',r,p,P,a,b,u,v),field(result,0,7),field(result,2,7),field(budgets,0,2),field(budgets,1,2),field(result,6,7))
        return conjunction(*(field(result,i,7) for i in range(6)),error)
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','log_coarse','log_fine','value_coarse','value_fine','power_p','power_q',
        'exp_coarse','exp_fine','head_coarse','head_fine','sum_coarse','sum_fine','power_P'),finish)


def prove_log_exp_cutoff_refinement(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP083',target=frozen_log_exp_cutoff_refinement_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'budgets':lambda s:_budgets(s,registry),'arithmetic':lambda s:_arithmetic(s,registry),'AP083':_root},
        pins=log_exp_cutoff_refinement_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
