"""AP091: construct positive fixed-schedule half-log samples near one root.

Choose the actual dyadic root before all later indices. Construct the finite
logarithm and factorial-normalized exponential tables, retaining every actual
witness and the AP090 cross bounds. No new definition, induction or axiom.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_fixed_half_log_root import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,field,canonical,json_hash,
    definition_registry as fixed_registry,fixed_half_log_root_source_pins,NAMED_SOURCE as FIXED_SOURCE,
)
from sqrt2_power_fixed_log_exp_witness import (
    definition_registry as witness_registry,fixed_log_exp_witness_source_pins,conjoin,
    OUTPUTS,EXP_OUTPUTS,ENDPOINT_SOURCES as WITNESS_ENDPOINTS,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-fixed-half-log-root-witness-v1'
NORMALIZATION='forall j a fj dj xj. Le(j,S(S k)) -> BetaAt(tb,tc,j,a) -> Factorial(j,fj) -> Pow(2*(d*p),j,dj) -> Pow(3*x,j,xj) -> (a*fj)*dj=h*xj'
PARTS=('~d=0','NatAtanhPrefix(d,ab,ac,S(2*k))','NatHornerValue(ab,ac,3,S(2*k),x)',
    'Pow(3,S(2*k),p)','~p=0','~(2*(d*p))=0',
    'NatExpWeightTable(2*(d*p),S(S k),wb,wc)','NatPowerWeightedPrefix(3*x,wb,wc,tb,tc,S(S(S k)))',
    'BetaAt(wb,wc,0,h)','BetaAt(tb,tc,0,h)','~h=0','Factorial(S(S k),f)','Pow(2*(d*p),S(S k),q)','h=f*q',
    'Sum(tb,tc,S(S(S k)),y)','NatScaledExpRecurrence(2*(d*p),3*x,tb,tc,S(S k))',NORMALIZATION,
    'Le(r*y,s*h+8*h)','Le(s*h,r*y+h)')
LATER_SOURCE='forall k. Le(S(S(18*r)),k) -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
NAMED_SOURCE='forall n. exists r s. Pow(2,n,r) /\\ (~r=0 /\\ (DyadicSqrt2(n,r,s) /\\ ('+LATER_SOURCE+')))'
TARGET_SHA256='9fba277808e08f9fc794a636d0be0242f1a8498dbd631870d0f88440174b708a'
FIXED_ARCHIVE=dict(case='AP090',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-v1/generation-process.json.gz',
    bytes=239332,sha256='4232c646131b73bb9b53e1d25b5a8d013da72f2929804488372b42468f15bdab',
    raw_bytes=6312545,raw_sha256='ae20c541bdcba7ec0be7191ce043f538fc0df75487e22b971741c0e18c5912fa',
    bundle_bytes=3868304,bundle_sha256='603a7c00633d251a1f6b4476247eb6e48a8d13d47b47b4dbf75b5eab5747ef8c',
    nodes=585,root=584,target_ast_sha256='41651cb7c7afc07ceb0eaeab7bf02392001a704ec0891d7bf1db0ed4aa33211f')
ARCHIVES=(FIXED_ARCHIVE,)
ENDPOINT_SOURCES={'fixed':FIXED_SOURCE,**{name:source for name,source in WITNESS_ENDPOINTS.items() if name!='fixed'}}
ENDPOINT_OWNERS={name:'AP090' for name in ENDPOINT_SOURCES}
HELPER_SOURCES={}
HELPER_TARGET_SHA256={}
HELPER_DEPENDENCIES={'AP091':tuple(ENDPOINT_SOURCES)}


class FixedHalfLogRootWitnessError(ValueError):
    """Changed actual positive witnesses, same-root order or finite errors."""


def definition_registry():
    result=dict(fixed_registry());identifiers={spec.stable_id for spec in result.values()}
    identity=('stable_id','name','parameters','template_source','template_formula','conceptual_dependencies')
    for name,spec in witness_registry().items():
        if name in result:
            if any(getattr(result[name],key)!=getattr(spec,key) for key in identity):
                raise FixedHalfLogRootWitnessError('shared definition identity changed')
            # These two old snapshots use different prose/category labels for
            # the identical Le/Lt definitions. Retain AP090's metadata exactly.
            if result[name]!=spec and name not in ('Le','Lt'):
                raise FixedHalfLogRootWitnessError('unexpected presentation metadata conflict')
        else:
            if not set(spec.conceptual_dependencies)<=result.keys() or spec.stable_id in identifiers:
                raise FixedHalfLogRootWitnessError('nonconservative witness definition merge')
            result[name]=spec;identifiers.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_fixed_half_log_root_witness_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if (binders!=1 or premises or type(conclusion) is not Exists or type(conclusion.body) is not Exists
            or json_hash(encode_formula(target))!=TARGET_SHA256):
        raise FixedHalfLogRootWitnessError('AP091 exact positive fixed-schedule root witness changed')
    return target


def source_contract():
    return dict(code='AP091',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precisions_including_zero=True,actual_root_chosen_before_arbitrary_later_index=True,
        actual_precision_power='r=2^n',root_computation_retained='DyadicSqrt2(n,r,s)',
        sufficient_threshold='18*r+2<=k',fixed_logarithm_prefix_length='2*k+1',fixed_exp_degree='k+2',
        all_logarithm_Horner_power_and_exponential_tables_constructed=True,
        positive_log_scale_argument_denominator_and_exp_head_proved=True,
        doubled_argument_denominator='2*(d*p)',head_factorization='h=(k+2)!*(2*(d*p))^(k+2)',
        every_actual_term_factorial_normalization_retained=True,
        finite_cross_bounds=['r*y<=s*h+8*h','s*h<=r*y+h'],finite_rational_error='-1/r<=y/h-s/r<=8/r',
        actual_ancestor_bodies_replayed=True,new_induction_count=0,new_induction_needed=False,
        new_solver_arithmetic_leaf_needed=False,new_definition_ids=[],definition_admissions=0,
        existing_definition_cones_merged=['AP090','AP086'],existing_support_definitions_reused=['ND0291','ND0408'],
        retained_overlap_presentation='AP090; only historical Le/Lt summary/category labels differ',
        analytic_half_log_sqrt2_identity_claimed=False,analytic_limit_claimed=False,root_quotient_accuracy_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def fixed_half_log_root_witness_source_pins():
    result=fixed_half_log_root_source_pins()
    for name,pin in fixed_log_exp_witness_source_pins().items():
        if name in result and result[name]!=pin:
            raise FixedHalfLogRootWitnessError('inherited witness source disagreement')
        result[name]=pin
    for name in (FIXED_ARCHIVE['path'],'scripts/sqrt2_power_fixed_half_log_root_witness.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        pin=dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
        if len(raw)>2*1024**2 or name==FIXED_ARCHIVE['path'] and pin!=dict(bytes=FIXED_ARCHIVE['bytes'],sha256=FIXED_ARCHIVE['sha256']):
            raise FixedHalfLogRootWitnessError('fixed witness source or archive changed')
        result[name]=pin
    return result


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    one,two,three=map(parse_term,('1','2','3'))
    def exponential(t):
        k,d,ab,ac,x,p,tb,tc,h,y=t.terms(('k','d','ab','ac','x','p','tb','tc','h','y'))
        coefficients=t.hyp('coefficient_data');data=t.hyp('exp_data')
        bounds=apply(instantiate(field(t.hyp('fixed_data'),3,4),k,d,ab,ac,x,p,tb,tc,h,y),
            t.hyp('threshold'),field(coefficients,0,3),field(coefficients,1,3),t.hyp('value'),t.hyp('power'),
            field(data,9,11),field(data,3,11),field(data,8,11))
        result=conjunction(field(coefficients,0,3),field(coefficients,1,3),t.hyp('value'),t.hyp('power'),
            field(bounds,0,4),field(bounds,1,4),*(field(data,i,11) for i in range(11)),field(bounds,2,4),field(bounds,3,4))
        return witness(t.terms(OUTPUTS),result)
    def powered(t):
        d,p,x,k=t.terms(('d','p','x','k'));length=Succ(Mul(two,k))
        pnz=apply(instantiate(apply(specialize(t,'power_nonzero',three),specialize(t,'succ_nonzero',two)),length,p),t.hyp('power'))
        product=apply(specialize(t,'mul_nonzero',d,p),field(t.hyp('coefficient_data'),0,3),pnz)
        positive=apply(specialize(t,'mul_nonzero',two,Mul(d,p)),specialize(t,'succ_nonzero',one),product)
        actual=apply(specialize(t,'exponential',Mul(two,Mul(d,p)),Mul(three,x),Succ(Succ(k))),positive)
        return eliminate(t,actual,EXP_OUTPUTS,'exp_data',exponential)
    def valued(t):
        return eliminate(t,specialize(t,'power_exists',three,Succ(Mul(two,t.term('k')))),('p',),'power',powered)
    def coefficients(t):
        return eliminate(t,specialize(t,'value_exists',*t.terms(('ab','ac')),three,Succ(Mul(two,t.term('k')))),('x',),'value',valued)
    def later(t):
        return eliminate(t,specialize(t,'atanh',Succ(Mul(two,t.term('k')))),('d','ab','ac'),'coefficient_data',coefficients)
    def precision(t):
        data=t.hyp('fixed_data');universal=introduce(t,('k',),('threshold',),later)
        return witness(t.terms(('r','s')),conjunction(*(field(data,i,4) for i in range(3)),universal))
    return introduce(s,('n',),(),lambda t:eliminate(t,specialize(t,'fixed',t.term('n')),('r','s'),'fixed_data',precision))


def prove_fixed_half_log_root_witness(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP091',target=frozen_fixed_half_log_root_witness_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP091':_root},pins=fixed_half_log_root_witness_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
