"""AP095: original n+8 samples have requested half-root comparison error.

Construct the actual powers 2^n and 2^8, factor the supplied dyadic
denominator, and reuse AP015's checked scale-cancellation body with C=18.
Both supplied finite exponential tables retain their independent positive
heads and the exact original degree (n+8)+2. No limit identity is assumed.
"""
from hashlib import sha256

from sqrt2_power_exp_log_root_half_transport import (
    ROOT,Scope,introduce,apply,specialize,conjunction,field,canonical,json_hash,_and,
    definition_registry,PARAMETERS as TRANSPORT_PARAMETERS,NAMED_SOURCE as TRANSPORT_SOURCE,
    ORIGINAL_PARAMETERS,W,Z,exp_log_root_half_transport_source_pins,
)
from sqrt2_power_approximation_record_error import (
    ERROR_ARCHIVE,approximation_record_error_source_pins,
)
from sqrt2_power_exp_sample_dyadic_error import (
    HELPER_SOURCES as ERROR_HELPERS,ENDPOINT_SOURCES as ERROR_ENDPOINTS,
)
from sqrt2_power_fixed_precision_threshold import _ground_equal,COEFFICIENT
from sqrt2_power_quadratic_trace_exists import eliminate,witness
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-requested-half-transport-v1'
PARAMETERS=('n',)+TRANSPORT_PARAMETERS[1:]
ORIGINAL_GRAPH='NatSqrt2ExpSample(n+8,'+','.join(ORIGINAL_PARAMETERS[1:])+')'
PREMISES=('~D=0',ORIGINAL_GRAPH,'~v=0',f'NatScaledExpRecurrence({Z},{W},jb,jc,(n+8)+2)',
    'BetaAt(jb,jc,0,v)','Sum(jb,jc,S((n+8)+2),z)')
PARTS=('Pow(2,n,r)','~r=0','~d=0','~w0=0','~v=0','Le(w0*z,v*y)',
    'Le(r*(v*y),r*(w0*z)+(w0*v))')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> exists r. '+_and(PARTS)
TARGET_SHA256='0b7a36d2e72c832a07f9a5512667ba40107b5b367d5a8715c776889e56a485e5'
HELPER_SOURCES={'constant_bound':'Le(18,'+COEFFICIENT+')'}
HELPER_TARGET_SHA256={'constant_bound':'154276ac9cb0dcccd67711f3b813fca24f01f3dc0a344c6c559849b71212748d'}
TRANSPORT_ARCHIVE=dict(case='AP094',
    path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-log-root-half-transport-v1/generation-process.json.gz',
    bytes=78558,sha256='8af1059828d7d3095d6542acfe982e4ce4601f6e694f1e78065ce6ca29acdde2',
    raw_bytes=1391384,raw_sha256='0997a71dbc0078b1e59e1f94df536d185ff1823fb9f78aeb1c7d77e80f71f71e',
    bundle_bytes=817481,bundle_sha256='b234e8883d2975dd2cb5ab32133703fb623196946051fffc74181f9e8a7d3f6c',
    nodes=214,root=213,target_ast_sha256='d987799164353f66ab8981951790a46ec16203c12f377c44a23181eb042ebe7a')
ARCHIVES=(TRANSPORT_ARCHIVE,ERROR_ARCHIVE)
ENDPOINT_SOURCES={'transport':TRANSPORT_SOURCE,'scale_arithmetic':ERROR_HELPERS['arithmetic'],
    **{name:ERROR_ENDPOINTS[name] for name in ('threshold','power_exists','power_add','power_nonzero','succ_ne_zero','le_trans')}}
ENDPOINT_OWNERS={name:'AP015' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS['transport']='AP094'
HELPER_DEPENDENCIES={'constant_bound':(),
    'AP095':('transport','scale_arithmetic','threshold','constant_bound','power_exists','power_add',
        'power_nonzero','succ_ne_zero','le_trans')}


class RequestedHalfTransportError(ValueError):
    """Changed original precision, retained table, denominator or error budget."""


def frozen_requested_half_transport_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    n,premises,out=strip_target(target)
    if n!=20 or len(premises)!=6 or type(out) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise RequestedHalfTransportError('AP095 exact requested-precision transport changed')
    return target


def source_contract():
    return dict(code='AP095',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=6,original_computation_graph_preserved=True,original_approximation_program_changed=False,
        original_precision='n+8',original_degree='(n+8)+2',same_degree_on_both_actual_tables=True,
        original_prefix_length='2*(n+8)+1',independent_positive_heads=True,
        actual_requested_power_constructed=True,actual_shift_power_constructed=True,
        actual_supplied_dyadic_power_factored=True,actual_AP015_scale_cancellation_body_replayed=True,
        reused_scale_arithmetic_ast_sha256='a7c53737271485b94934c473aece0dc46b01bc06fb94722136bb502ba69f7eb8',
        finite_rational_error='0<=y/w0-z/v<=1/r where r=2^n',
        only_separately_proved_nonzero_shift_cancelled=True,new_definition_ids=[],definition_admissions=0,
        new_induction_count=0,new_induction_needed=False,tiny_ground_evaluator_max_value=32,
        new_solver_arithmetic_leaf=None,deterministic_proof_constructor=True,solver_hints_are_proof_authority=False,
        analytic_identity_claimed=False,analytic_limit_claimed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def requested_half_transport_source_pins():
    result=exp_log_root_half_transport_source_pins()
    for name,pin in approximation_record_error_source_pins().items():
        if name in result and result[name]!=pin:raise RequestedHalfTransportError('inherited source disagreement')
        result[name]=pin
    expected={pin['path']:dict(bytes=pin['bytes'],sha256=pin['sha256']) for pin in ARCHIVES}
    for name in ('scripts/sqrt2_power_exp_log_root_half_transport.py','scripts/sqrt2_power_approximation_record_error.py',
            'scripts/sqrt2_power_exp_sample_dyadic_error.py','scripts/sqrt2_power_fixed_precision_threshold.py',
            'scripts/sqrt2_power_quadratic_trace_exists.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise RequestedHalfTransportError('unbound imported constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_requested_half_transport.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        pin=dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
        if len(raw)>2*1024**2 or name in expected and pin!=expected[name]:
            raise RequestedHalfTransportError('requested transport source or actual archive changed')
        result[name]=pin
    return result


def _constant_bound(s):
    from peano_lab.kernel.terms import Add,parse_term
    gap,eighteen,coefficient=map(parse_term,('11','18',COEFFICIENT))
    return witness((gap,),_ground_equal(Add(gap,eighteen),coefficient))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,eight,eighteen,coefficient=map(parse_term,('2','8','18',COEFFICIENT))
    def chosen(t):
        n,d,r,shift,w0,v,y,z=t.terms(('n','d','r','shift','w0','v','y','z'));precision=Add(n,eight)
        result=apply(specialize(t,'transport',precision,*t.terms(PARAMETERS[1:])),
            *[t.hyp(name) for name in ('scale_nonzero','original','half_positive','half_terms','half_head','half_sum')])
        threshold=apply(specialize(t,'threshold',shift),t.hyp('shift_power'))
        small=apply(specialize(t,'le_trans',eighteen,coefficient,shift),t.hyp('constant_bound'),AndElimR(threshold))
        coarse_power=AndElimL(field(field(t.hyp('original'),0,9),0,4))
        factor=apply(specialize(t,'power_add',two,n,eight,precision,r,shift,d),EqRefl(precision),
            t.hyp('dyadic_power'),t.hyp('shift_power'),coarse_power)
        rnz=apply(instantiate(apply(specialize(t,'power_nonzero',two),
            specialize(t,'succ_ne_zero',parse_term('1'))),n,r),t.hyp('dyadic_power'))
        bound=apply(specialize(t,'scale_arithmetic',d,r,shift,eighteen,Mul(v,y),Mul(w0,z),Mul(w0,v)),
            factor,AndElimL(threshold),small,field(result,6,7))
        return witness((r,),conjunction(t.hyp('dyadic_power'),rnz,field(result,0,7),field(result,3,7),
            field(result,4,7),field(result,5,7),bound))
    def dyadic(t):
        return eliminate(t,specialize(t,'power_exists',two,eight),('shift',),'shift_power',chosen)
    return introduce(s,PARAMETERS,('scale_nonzero','original','half_positive','half_terms','half_head','half_sum'),
        lambda t:eliminate(t,specialize(t,'power_exists',two,t.term('n')),('r',),'dyadic_power',dyadic))


def factories(registry):return {'constant_bound':_constant_bound,'AP095':_root}


def prove_requested_half_transport(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP095',target=frozen_requested_half_transport_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories(registry),
        pins=requested_half_transport_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
