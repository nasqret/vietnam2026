"""AP075: an explicit dyadic modulus for bounded finite exponential sums.

At input precision m=9*(L+1)+n+1, the checked binary budget absorbs the
constructed majorant 9^(L+1). The two supplied computations have the same
arbitrary horizon but may use different denominators, heads and table codes.
The symbolic powers are actual computations; no large numeral is expanded.
"""
from hashlib import sha256

from sqrt2_power_exp_bounded_continuity import (
    ROOT,Scope,introduce,eliminate,apply,specialize,canonical,json_hash,
    source_registry,definition_registry,exp_bounded_continuity_source_pins,
    NAMED_SOURCE as CONTINUITY_SOURCE,DATA_PREMISES,DATA_HYPS,CONCLUSION as ERROR_CONCLUSION,BOUND_ARCHIVE,
)
from sqrt2_power_exp_binary_budget import NAMED_SOURCE as BUDGET_SOURCE,exp_binary_budget_source_pins,COMPARISON_ARCHIVE
from sqrt2_power_quadratic_trace_exists import conjunction,witness,field
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-dyadic-continuity-v1'
PRECISION='S(9*(S L)+n)'
PARAMETERS=('L','d','e','x','y','g','n','N','ab','ac','bb','bc','a0','b0','s','t','r','p')
PREMISES=('~d=0','~e=0','Le(x,L*d)','Le(y,L*e)','Le(d*y,e*x+g)','Le(e*x,d*y+g)')+DATA_PREMISES+('Pow(2,n,r)',f'Pow(2,{PRECISION},p)','Le(p*g,d*e)')
CONCLUSION='~r=0 /\\ (~p=0 /\\ ('+ERROR_CONCLUSION+'))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='52a66a0660b914cf13ff19d92ee7d59293e729e8ef8813555714e427ec0646c4'
HELPER_SOURCES={'arithmetic':'forall r C p g D. Le(2*(r*C),p) -> Le(p*g,D) -> Le((r*g)*C,D)'}
HELPER_TARGET_SHA256={'arithmetic':'c20243a446ca9b396aabf32a55eb7263488b66cff2a1fdbfbf0c151ab7f720da'}
CONTINUITY_ARCHIVE=dict(case='AP074',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-bounded-continuity-v1/generation-process.json.gz',
    bytes=107102,sha256='3bf82c9d902801d2196aeb8cc0bc5a628908b0fcc679122930a2c1d9362e677f',
    raw_bytes=2167439,raw_sha256='2d97a0e29e752f66f6d57261f32ef59fe0d5e9fbba77e18f49a031ec9f4ca490',
    bundle_bytes=1281896,bundle_sha256='e8deaebfa9c117104743c0ae0298c1d8cffe8f8ccf5f713f332a46ffeb48873e',
    nodes=288,root=287,target_ast_sha256='33db4b325e45a75d8927db006e7cc1ae244b680af38c9eda0005ba8149899723')
BUDGET_ARCHIVE=dict(case='AP062',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-binary-budget-v1/generation-process.json.gz',
    bytes=47031,sha256='b191a276c08d29ef3917f6681491b69160ed131c79afca34c2c0369d78b38044',
    raw_bytes=518224,raw_sha256='e301d5154447e50e98a0f4a745ea4474f2ad6176454968eb4accf911b7d1706c',
    bundle_bytes=271322,bundle_sha256='39d7d7a5d5dbff58bd1267471f3e1b6de19b268d0688a7806e0e8c278173e0ad',
    nodes=129,root=128,target_ast_sha256='b028bfcd3503ce1d69225b9daa26335368cc2a1d1388058cffbf5bd29ca99c55')
ARCHIVES=(CONTINUITY_ARCHIVE,BUDGET_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'continuity':CONTINUITY_SOURCE,'budget':BUDGET_SOURCE,
    'power_exists':'forall d n. exists p. Pow(d,n,p)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_succ_left':'forall a b. (S a)*b=a*b+b','one_mul':'forall a. 1*a=a',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(continuity='AP074',budget='AP062',power_exists='AP010')
HELPER_DEPENDENCIES={'arithmetic':('mul_right_mono','mul_assoc','mul_comm','mul_succ_left','one_mul','le_trans'),
    'AP075':('continuity','budget','power_exists','arithmetic')}


class ExpDyadicContinuityError(ValueError):
    """Changed explicit dyadic modulus, actual tables or requested error."""


def frozen_exp_dyadic_continuity_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=18 or len(premises)!=15 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpDyadicContinuityError('AP075 exact requested dyadic finite continuity changed')
    return target


def source_contract():
    return dict(code='AP075',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=15,both_actual_recurrences_heads_sums_preserved=True,
        independent_denominators_heads_and_codes_allowed=True,argument_order_assumed=False,
        argument_bounds=['x<=L*d','y<=L*e'],input_precision='m=9*(L+1)+n+1',
        supplied_powers='r=2^n;p=2^m',both_dyadic_scales_proved_nonzero=True,
        symmetric_input_error='abs(d*y-e*x)<=g; p*g<=d*e',
        symmetric_output_error='abs(r*(a0*t)-r*(b0*s))<=a0*b0',
        actual_majorant_power_constructed=True,uniform_in_finite_horizon=True,
        zero_arguments_gap_heads_horizon_and_n_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,large_ground_power_materialized=False,
        analytic_continuity_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_dyadic_continuity_source_pins():
    result=exp_bounded_continuity_source_pins()
    for name,pin in exp_binary_budget_source_pins().items():
        if name in result and result[name]!=pin:raise ExpDyadicContinuityError('dyadic-continuity dependency source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_bounded_continuity.py':'a76036c7db0052605a4135471b79afdce70c387949745bd0e9289fb3282c7199',
        'scripts/sqrt2_power_exp_binary_budget.py':'2ae096f8f376216769c3d7b7c9dcd9542c1f694ca9c4c221c4c03f3cf1045637',**{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_dyadic_continuity.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpDyadicContinuityError('dyadic-continuity source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish(t):
        r,C,p,g,D=t.terms(('r','C','p','g','D'));u=Mul(r,C)
        twice=_chain(specialize(t,'mul_succ_left',one,u),CongAdd(specialize(t,'one_mul',u),EqRefl(u)))
        initial=witness((u,),EqSym(twice))
        bound=apply(specialize(t,'le_trans',u,Mul(two,u),p),initial,t.hyp('power_budget'))
        bound=apply(specialize(t,'mul_right_mono',u,p,g),bound)
        bound=apply(specialize(t,'le_trans',Mul(u,g),Mul(p,g),D),bound,t.hyp('input_budget'))
        return _subst(t,registry,'Le(slot,D)',_multiplicative_equal(t,Mul(u,g),Mul(Mul(r,g),C)),bound)
    return introduce(s,('r','C','p','g','D'),('power_budget','input_budget'),finish)


def _root(s,registry):
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    nine=parse_term('9')
    def chosen(t):
        L,d,e,x,y,g,n,N,a,b,u,v,r,p,C=t.terms(('L','d','e','x','y','g','n','N','a0','b0','s','t','r','p','C'))
        powers=apply(specialize(t,'budget',nine,Succ(L),n,C,r,p),t.hyp('majorant_power'),t.hyp('output_power'),t.hyp('input_power'))
        budget=apply(specialize(t,'arithmetic',r,C,p,g,Mul(d,e)),field(powers,2,3),t.hyp('input_budget'))
        estimate=apply(specialize(t,'continuity',L,d,e,x,y,g,N,*t.terms(('ab','ac','bb','bc')),a,b,u,v,C,r),
            *(t.hyp(name) for name in ('nonzero_d','nonzero_e','bound_a','bound_b','forward','backward')+DATA_HYPS),t.hyp('majorant_power'),budget)
        return conjunction(field(powers,0,3),field(powers,1,3),estimate)
    def finish(t):
        return eliminate(t,specialize(t,'power_exists',nine,Succ(t.term('L'))),('C',),'majorant_power',chosen)
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','bound_a','bound_b','forward','backward')+DATA_HYPS+('output_power','input_power','input_budget'),finish)


def prove_exp_dyadic_continuity(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP075',target=frozen_exp_dyadic_continuity_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP075':lambda s:_root(s,registry)},
        pins=exp_dyadic_continuity_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
