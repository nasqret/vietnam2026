"""AP062: symbolic dyadic budget for an arbitrary natural argument majorant.

One ordinary induction proves L^K<=2^(L*K) for actual supplied powers,
including L=0 and K=0. Power addition and one binary successor then prove
2*(2^n*L^K)<=2^(L*K+n+1). Both dyadic scales are proved nonzero.
No large power is materialized and no analytic remainder is assumed.
"""
from hashlib import sha256

from sqrt2_power_half_log_precision import (
    ROOT,Scope,introduce,eliminate,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,half_log_precision_source_pins,COMPARISON_ARCHIVE,BOUND_ARCHIVE,
    HELPER_SOURCES as PRECISION_HELPERS,
)
from sqrt2_power_positive_power_comparison import ENDPOINT_SOURCES as POWER_ENDPOINTS,HELPER_SOURCES as COMPARISON_HELPERS
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-binary-budget-v1'
NAMED_SOURCE='forall L K n B r p. Pow(L,K,B) -> Pow(2,n,r) -> Pow(2,S(L*K+n),p) -> ~r=0 /\\ (~p=0 /\\ Le(2*(r*B),p))'
TARGET_SHA256='b028bfcd3503ce1d69225b9daa26335368cc2a1d1388058cffbf5bd29ca99c55'
HELPER_SOURCES={
    'binary_majorant':'forall K L B C. Pow(L,K,B) -> Pow(2,L*K,C) -> Le(B,C)',
    'arithmetic':'forall B C r t p. Le(B,C) -> t=C*r -> p=t*2 -> Le(2*(r*B),p)',
}
HELPER_TARGET_SHA256={
    'binary_majorant':'b3aae1892db43a3226051d0ea2c882d35010cd7840008a6319b43d26e3a3fbe9',
    'arithmetic':'ba79268b3dae1694ad4ea4d2b2b00de50b5bc0132eb27d5877e231553167e047',
}
PRECISION_ARCHIVE=dict(case='AP046',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-precision-v1/generation-process.json.gz',
    bytes=33965,sha256='a8aa5cf416eba42d7ac60677297def6b0b582b83effc747df788f37f1425a8cd',
    raw_bytes=213916,raw_sha256='1ced030dc8e04ad27296497367bd7f66e58f7d7cf2c99b2dd65ae63a28613f4a',
    bundle_bytes=78373,bundle_sha256='96815002d9cbada491bb67202df76d032ac56ed7b8f0c85b32d92a1406e3368a',
    nodes=37,root=36,target_ast_sha256='936a988b2a6fae61ebb3206a2a33746d5c8ad2e23501f642b0528b6b9e0e7877')
ARCHIVES=(COMPARISON_ARCHIVE,PRECISION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={name:POWER_ENDPOINTS[name] for name in ('power_zero','power_step','power_exists','power_add','power_nonzero')}
ENDPOINT_SOURCES.update(
    step_order=COMPARISON_HELPERS['step'],binary_growth=PRECISION_HELPERS['growth'],
    le_refl='forall a. Le(a,a)',le_succ='forall a b. Le(a,b) -> Le(a,S b)',
    le_trans='forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    succ_nonzero='forall a. ~(S a)=0',mul_left_mono='forall a b c. Le(a,b) -> Le(c*a,c*b)',
    mul_assoc='forall a b c. (a*b)*c=a*(b*c)',mul_comm='forall a b. a*b=b*a')
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:'AP010' for name in ('power_zero','power_step','power_exists','power_add','power_nonzero','step_order')})
ENDPOINT_OWNERS['binary_growth']='AP046'
HELPER_DEPENDENCIES={
    'binary_majorant':('power_zero','power_step','power_exists','power_add','binary_growth','le_refl','le_succ','le_trans','step_order'),
    'arithmetic':('mul_left_mono','mul_assoc','mul_comm'),
    'AP062':('binary_majorant','arithmetic','power_exists','power_step','power_add','power_nonzero','succ_nonzero'),
}


class ExpBinaryBudgetError(ValueError):
    """Changed actual powers, symbolic exponent or dyadic allowance."""


def frozen_exp_binary_budget_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=3 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpBinaryBudgetError('AP062 exact symbolic dyadic precision budget changed')
    return target


def source_contract():
    return dict(code='AP062',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,three_actual_supplied_powers_required=True,
        general_majorant='L^K<=2^(L*K)',precision_budget='2*(r*B)<=p',
        supplied_powers='B=L^K; r=2^n; p=2^(L*K+n+1)',both_dyadic_powers_proved_nonzero=True,
        zero_L_K_and_n_allowed=True,large_ground_power_materialized=False,
        fixed_approximation_program_changed=False,new_induction_needed=True,new_induction_count=1,
        new_definition_ids=[],definition_admissions=0,analytic_remainder_claimed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_binary_budget_source_pins():
    result=half_log_precision_source_pins()
    expected={'scripts/sqrt2_power_half_log_precision.py':'a009a1c8acc576cc5c2a244580c239aa2d82b799590b3c777b8ca77e245f7579',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_binary_budget.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpBinaryBudgetError('binary budget source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _binary_majorant(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    zero=Zero();one=Succ(zero);two=Succ(one)
    def base(t):
        L,B,C=t.terms(('L','B','C'))
        left=apply(specialize(t,'power_zero',L,zero,B),EqRefl(zero),t.hyp('majorant_power'))
        right=apply(specialize(t,'power_zero',two,Mul(L,zero),C),instantiate(Axiom('PA5'),L),t.hyp('binary_power'))
        order=_left(t,registry,specialize(t,'le_refl',one),one,EqSym(left))
        return _right(t,registry,order,B,EqSym(right))
    def chosen(t):
        K,L,B,C,b,c,f=t.terms(('K','L','B','C','previous_B','previous_C','factor'))
        old=apply(specialize(t,'IH',L,b,c),AndElimL(t.hyp('previous_majorant')),t.hyp('previous_binary'))
        growth=apply(specialize(t,'binary_growth',L,f),t.hyp('factor_power'))
        base_bound=apply(specialize(t,'le_trans',L,Succ(L),f),
            apply(specialize(t,'le_succ',L,L),specialize(t,'le_refl',L)),growth)
        order=apply(specialize(t,'step_order',L,f,b,c),base_bound,old)
        product=apply(specialize(t,'power_add',two,Mul(L,K),L,Mul(L,Succ(K)),c,f,C),
            instantiate(Axiom('PA6'),L,K),t.hyp('previous_binary'),t.hyp('factor_power'),t.hyp('binary_power'))
        order=_left(t,registry,order,Mul(c,f),EqSym(AndElimR(t.hyp('previous_majorant'))))
        return _right(t,registry,order,B,EqSym(product))
    def successor(t):
        L,K,B=t.terms(('L','K','B'))
        previous=apply(specialize(t,'power_step',L,K,Succ(K),B),EqRefl(Succ(K)),t.hyp('majorant_power'))
        return eliminate(t,previous,('previous_B',),'previous_majorant',lambda u:
            eliminate(u,specialize(u,'power_exists',two,Mul(u.term('L'),u.term('K'))),('previous_C',),'previous_binary',lambda v:
                eliminate(v,specialize(v,'power_exists',two,v.term('L')),('factor',),'factor_power',chosen)))
    return Ind(target.body,introduce(s,('L','B','C'),('majorant_power','binary_power'),base),
        introduce(s,('K',),('IH',),lambda t:introduce(t,('L','B','C'),('majorant_power','binary_power'),successor)))


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        B,C,r,q,p=t.terms(('B','C','r','t','p'));two=Succ(Succ(Zero()))
        order=apply(specialize(t,'mul_left_mono',B,C,r),t.hyp('majorant'))
        order=apply(specialize(t,'mul_left_mono',Mul(r,B),Mul(r,C),two),order)
        equal=_chain(_multiplicative_equal(t,Mul(two,Mul(r,C)),Mul(Mul(C,r),two)),
            CongMul(EqSym(t.hyp('product')),EqRefl(two)),EqSym(t.hyp('successor')))
        return _right(t,registry,order,Mul(two,Mul(r,B)),equal)
    return introduce(s,('B','C','r','t','p'),('majorant','product','successor'),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def chosen(t):
        L,K,n,B,r,p,c,q=t.terms(('L','K','n','B','r','p','C','previous'));lk=Mul(L,K);exponent=Add(lk,n)
        bound=apply(specialize(t,'binary_majorant',K,L,B,c),t.hyp('majorant_power'),t.hyp('power_C'))
        product=apply(specialize(t,'power_add',two,lk,n,exponent,c,r,q),EqRefl(exponent),
            t.hyp('power_C'),t.hyp('precision_power'),AndElimL(t.hyp('previous_power')))
        allowance=apply(specialize(t,'arithmetic',B,c,r,q,p),bound,product,AndElimR(t.hyp('previous_power')))
        nonzero=apply(specialize(t,'power_nonzero',two),specialize(t,'succ_nonzero',one))
        rnz=apply(instantiate(nonzero,n,r),t.hyp('precision_power'))
        pnz=apply(instantiate(nonzero,Succ(exponent),p),t.hyp('cutoff_power'))
        return conjunction(rnz,pnz,allowance)
    def start(t):
        L,K,n,p=t.terms(('L','K','n','p'));exponent=Add(Mul(L,K),n)
        previous=apply(specialize(t,'power_step',two,exponent,Succ(exponent),p),EqRefl(Succ(exponent)),t.hyp('cutoff_power'))
        return eliminate(t,previous,('previous',),'previous_power',lambda u:
            eliminate(u,specialize(u,'power_exists',two,Mul(u.term('L'),u.term('K'))),('C',),'power_C',chosen))
    return introduce(s,('L','K','n','B','r','p'),('majorant_power','precision_power','cutoff_power'),start)


def prove_exp_binary_budget(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry();target=frozen_exp_binary_budget_target(_registry=registry)
    helper=parse_named(HELPER_SOURCES['binary_majorant'],registry=registry)
    return assemble_mixed_certificate(code='AP062',target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'binary_majorant':lambda s:_binary_majorant(s,helper,registry),
            'arithmetic':lambda s:_arithmetic(s,registry),'AP062':_root},
        pins=exp_binary_budget_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
