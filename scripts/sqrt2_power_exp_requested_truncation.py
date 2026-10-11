"""AP063: requested dyadic precision for finite large-argument truncation.

At short length K+(L*K+n+1), uniformly in the extra finite horizon, the
normalized tail is at most 2^-n. All tables and sums remain supplied data;
the auxiliary powers are constructed and only their positive scale is
cancelled. This is not an infinite remainder or analytic identification.
"""
from hashlib import sha256

from sqrt2_power_exp_normalized_truncation import (
    ROOT,Scope,introduce,eliminate,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,source_registry,exp_normalized_truncation_source_pins,
    NAMED_SOURCE as TRUNCATION_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_binary_budget import (
    NAMED_SOURCE as BUDGET_SOURCE,exp_binary_budget_source_pins,COMPARISON_ARCHIVE,
)
from sqrt2_power_quadratic_trace_exists import field
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-requested-truncation-v1'
M='S(L*K+n)'
SHORT=f'K+{M}'
H=f'({SHORT})+N'
PARAMETERS=('d','x','L','K','n','N','ab','ac','h','s','t','r')
PREMISES=('~d=0','Le(x,L*d)','Le(2*L,K)',f'NatScaledExpRecurrence(d,x,ab,ac,{H})',
    'BetaAt(ab,ac,0,h)',f'Sum(ab,ac,{SHORT},s)',f'Sum(ab,ac,S({H}),t)','Pow(2,n,r)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> ~r=0 /\\ (Le(s,t) /\\ Le(r*t,r*s+h))'
TARGET_SHA256='87d46a5afea3d3cb839af399daa22055d469c3506826aa7404168a3b15983873'
HELPER_SOURCES={'arithmetic':'forall p r B h s t. ~p=0 -> Le(2*(r*B),p) -> Le(p*t,p*s+2*(B*h)) -> Le(r*t,r*s+h)'}
HELPER_TARGET_SHA256={'arithmetic':'7d4c1b363859501bf185feb63a009100a0e314af76d6a39faf796a04131cd7f2'}
TRUNCATION_ARCHIVE=dict(case='AP057',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-normalized-truncation-v1/generation-process.json.gz',
    bytes=67570,sha256='d1c91829178a68f405c22b7a9b0eb0b6f6857195d4f0be117a05ac69e3e50856',
    raw_bytes=801026,raw_sha256='cb4089aea9cd6f88f3448559704714f3bbf25cba2f352c266a78ed901be2d525',
    bundle_bytes=422324,bundle_sha256='cc59b8f6360dec4a08b2e261e02420319cf7924020589c9285163adb763d294c',
    nodes=160,root=159,target_ast_sha256='f74987c7317766d697ca0d5792985ab700e38691f10bd6149d8c1ca141fc33b9')
BUDGET_ARCHIVE=dict(case='AP062',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-binary-budget-v1/generation-process.json.gz',
    bytes=47031,sha256='b191a276c08d29ef3917f6681491b69160ed131c79afca34c2c0369d78b38044',
    raw_bytes=518224,raw_sha256='e301d5154447e50e98a0f4a745ea4474f2ad6176454968eb4accf911b7d1706c',
    bundle_bytes=271322,bundle_sha256='39d7d7a5d5dbff58bd1267471f3e1b6de19b268d0688a7806e0e8c278173e0ad',
    nodes=129,root=128,target_ast_sha256='b028bfcd3503ce1d69225b9daa26335368cc2a1d1388058cffbf5bd29ca99c55')
ARCHIVES=(TRUNCATION_ARCHIVE,BUDGET_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'truncation':TRUNCATION_SOURCE,'budget':BUDGET_SOURCE,
    'power_exists':'forall d n. exists p. Pow(d,n,p)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_add':'forall a b c. a*(b+c)=a*b+a*c',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(truncation='AP057',budget='AP062',power_exists='AP010')
HELPER_DEPENDENCIES={
    'arithmetic':('mul_left_mono','mul_right_mono','mul_assoc','mul_comm','mul_add','add_left_mono','le_trans','mul_le_cancel'),
    'AP063':('truncation','budget','power_exists','arithmetic'),
}


class ExpRequestedTruncationError(ValueError):
    """Changed supplied tables, requested precision, cutoff or finite bound."""


def frozen_exp_requested_truncation_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=12 or len(premises)!=8 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRequestedTruncationError('AP063 exact requested-precision finite truncation changed')
    return target


def source_contract():
    return dict(code='AP063',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=8,supplied_recurrence_head_sums_and_precision_power_preserved=True,
        argument_bound='x<=L*d',initial_cutoff='2*L<=K',short_length='K+(L*K+n+1)',
        whole_degree='K+(L*K+n+1)+N',requested_scale='r=2^n',
        finite_bounds='s<=t; r*t<=r*s+h',requested_scale_proved_nonzero=True,
        auxiliary_powers_constructed_not_assumed=True,uniform_in_extra_finite_horizon=True,
        zero_arguments_heads_and_precision_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,fixed_approximation_program_changed=False,
        infinite_remainder_or_analytic_exponential_claimed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_requested_truncation_source_pins():
    result=exp_normalized_truncation_source_pins()
    for name,pin in exp_binary_budget_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpRequestedTruncationError('binary budget source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_normalized_truncation.py':'e8eb0a5f6c20ff2f4abbd5b2c55261484c40bb75f00e2cb9743fdc27be14d4fd',
        'scripts/sqrt2_power_exp_binary_budget.py':'2ae096f8f376216769c3d7b7c9dcd9542c1f694ca9c4c221c4c03f3cf1045637',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_requested_truncation.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRequestedTruncationError('requested-truncation source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        p,r,B,h,z,out=t.terms(('p','r','B','h','s','t'));two=Succ(Succ(Zero()))
        allowance=Mul(two,Mul(B,h));small=Mul(Mul(two,Mul(r,B)),h);short=Mul(p,Mul(r,z))
        upper=apply(specialize(t,'mul_left_mono',Mul(p,out),Add(Mul(p,z),allowance),r),t.hyp('upper'))
        left=_multiplicative_equal(t,Mul(r,Mul(p,out)),Mul(p,Mul(r,out)))
        right=_chain(specialize(t,'mul_add',r,Mul(p,z),allowance),
            CongAdd(_multiplicative_equal(t,Mul(r,Mul(p,z)),short),
                _multiplicative_equal(t,Mul(r,allowance),small)))
        upper=_left(t,registry,upper,Mul(r,Add(Mul(p,z),allowance)),left)
        upper=_right(t,registry,upper,Mul(p,Mul(r,out)),right)
        error=apply(specialize(t,'mul_right_mono',Mul(two,Mul(r,B)),p,h),t.hyp('budget'))
        error=apply(specialize(t,'add_left_mono',small,Mul(p,h),short),error)
        bound=apply(specialize(t,'le_trans',Mul(p,Mul(r,out)),Add(short,small),Add(short,Mul(p,h))),upper,error)
        bound=_right(t,registry,bound,Mul(p,Mul(r,out)),EqSym(specialize(t,'mul_add',p,Mul(r,z),h)))
        return apply(specialize(t,'mul_le_cancel',p,Mul(r,out),Add(Mul(r,z),h)),t.hyp('nonzero'),bound)
    return introduce(s,('p','r','B','h','s','t'),('nonzero','budget','upper'),finish)


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        d,x,L,K,n,N,h,z,out,r,p,B=t.terms(('d','x','L','K','n','N','h','s','t','r','p','B'))
        m=Succ(Add(Mul(L,K),n))
        budget=apply(specialize(t,'budget',L,K,n,B,r,p),t.hyp('majorant_power'),t.hyp('precision_power'),t.hyp('cutoff_power'))
        truncation=apply(specialize(t,'truncation',d,x,L,*t.terms(('ab','ac')),K,m,N,h,z,out,p,B),
            *(t.hyp(name) for name in ('nonzero','argument','threshold','recurrence','head','short','whole','cutoff_power','majorant_power')))
        error=apply(specialize(t,'arithmetic',p,r,B,h,z,out),field(budget,1,3),field(budget,2,3),AndElimR(truncation))
        return conjunction(field(budget,0,3),AndElimL(truncation),error)
    def start(t):
        return eliminate(t,specialize(t,'power_exists',t.term('L'),t.term('K')),('B',),'majorant_power',lambda u:
            eliminate(u,specialize(u,'power_exists',Succ(Succ(Zero())),Succ(Add(Mul(u.term('L'),u.term('K')),u.term('n')))),
                ('p',),'cutoff_power',chosen))
    return introduce(s,PARAMETERS,('nonzero','argument','threshold','recurrence','head','short','whole','precision_power'),start)


def prove_exp_requested_truncation(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP063',target=frozen_exp_requested_truncation_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP063':_root},
        pins=exp_requested_truncation_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
