"""AP080: requested precision for independently normalized rational powers.

Construct the missing denominator-product powers. Actual product and
successor identities absorb AP079's error factor into D*E. The arithmetic
budget is explicit; no cancellation, new induction or analytic axiom is used.
"""
from hashlib import sha256

from sqrt2_power_rational_power_difference import (
    ROOT,Scope,introduce,eliminate,apply,specialize,canonical,json_hash,
    definition_registry,rational_power_difference_source_pins,
    NAMED_SOURCE as DIFFERENCE_SOURCE,PRODUCT_ARCHIVE,POWER_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_product_power import NAMED_SOURCE as PRODUCT_SOURCE,HELPER_SOURCES as PRODUCT_HELPERS
from sqrt2_power_quadratic_trace_exists import conjunction,field
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-requested-power-precision-v1'
PARAMETERS=('d','e','a','b','M','g','k','u','v','D','E','C','r')
PREMISES=('~d=0','~e=0','Le(a,M*d)','Le(b,M*e)','Le(b*d,a*e+g)','Le(a*e,b*d+g)',
    'Pow(a,S k,u)','Pow(b,S k,v)','Pow(d,S k,D)','Pow(e,S k,E)','Pow(M,k,C)',
    'Le((r*(S k))*(g*C),d*e)')
BOUNDS='Le(r*(v*D),r*(u*E)+D*E) /\\ Le(r*(u*E),r*(v*D)+D*E)'
CONCLUSION='~D=0 /\\ (~E=0 /\\ ('+BOUNDS+'))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='486fc0a6d7574427552d0fefc51c3ea3d4176a018a649275113340d0cf60d1d1'
HELPER_SOURCES={'arithmetic':'forall r m g C Q D H U V. Le(V,U+m*(g*(C*Q))) -> Le((r*m)*(g*C),D) -> H=D*Q -> Le(r*V,r*U+H)'}
HELPER_TARGET_SHA256={'arithmetic':'82a07e517733496f24d7f4758cbd41f0333f4b75f5fc9e147a7a0b9fd852ab01'}
DIFFERENCE_ARCHIVE=dict(case='AP079',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-rational-power-difference-v1/generation-process.json.gz',
    bytes=49443,sha256='860f649ddf6fa8b9a7126d6bfd994e605b635e35a73df905379ae07e541c050c',
    raw_bytes=591063,raw_sha256='f17a456f06d20c8de297c301027dca1a44b2dd48a3ce1c82a0ac348addc7a05b',
    bundle_bytes=316595,bundle_sha256='3d6d57fcdb4790e5b501149babd64eeace241bc7c05a6c2f072a4ea02e463edb',
    nodes=136,root=135,target_ast_sha256='0be1195ec265753f6216218bc22c6933b86df205ce422c95f0c25df112074b61')
ARCHIVES=(DIFFERENCE_ARCHIVE,PRODUCT_ARCHIVE,POWER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'difference':DIFFERENCE_SOURCE,'product':PRODUCT_SOURCE,
    'successor_value':PRODUCT_HELPERS['successor_value'],'power_exists':'forall a n. exists p. Pow(a,n,p)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(difference='AP079',product='AP078',successor_value='AP078',power_exists='AP010')
HELPER_DEPENDENCIES={'arithmetic':('mul_left_mono','mul_right_mono','add_left_mono','le_trans','mul_add','mul_assoc','mul_comm'),
    'AP080':('difference','product','successor_value','power_exists','arithmetic','mul_comm')}


class RequestedPowerPrecisionError(ValueError):
    """Changed supplied power, precision budget or output denominator product."""


def frozen_requested_power_precision_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=13 or len(premises)!=12 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise RequestedPowerPrecisionError('AP080 exact requested rational power precision changed')
    return target


def source_contract():
    return dict(code='AP080',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=12,all_five_supplied_actual_powers_preserved=True,
        independent_argument_denominators_allowed=True,both_output_denominator_powers_proved_nonzero=True,
        denominator_product_powers_constructed=True,actual_product_and_successor_values_identified=True,
        precision_budget='(r*(k+1))*(g*C)<=d*e',symmetric_input_error='abs(b*d-a*e)<=g',
        symmetric_output_error='r*abs(v*D-u*E)<=D*E',majorant_power='C=M^k',
        output_denominators='D=d^(k+1);E=e^(k+1)',symbolic_precision_scale=True,
        zero_precision_numerators_gap_bound_and_k_allowed=True,denominator_cancellation_used=False,
        input_order_assumed=False,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_power_or_exponential_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def requested_power_precision_source_pins():
    result=rational_power_difference_source_pins()
    expected={'scripts/sqrt2_power_rational_power_difference.py':'b00a24987f9339d511e7fca0fef8f9dd365f9a543e1b272b6808dd8d6089fd47',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_product_power.py','scripts/sqrt2_power_quadratic_trace_exists.py',
                 'scripts/sqrt2_power_exp_two_sided_continuity.py','scripts/sqrt2_power_finite_power_evaluation.py',
                 'scripts/sqrt2_power_quadratic_height.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise RequestedPowerPrecisionError('unbound precision proof constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_requested_power_precision.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:raise RequestedPowerPrecisionError('power precision source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        r,m,g,C,Q,D,H,U,V=t.terms(('r','m','g','C','Q','D','H','U','V'))
        err=Mul(m,Mul(g,Mul(C,Q)));coefficient=Mul(Mul(r,m),Mul(g,C))
        rV,rU,rerr=Mul(r,V),Mul(r,U),Mul(r,err)
        result=apply(specialize(t,'mul_left_mono',V,Add(U,err),r),t.hyp('error'))
        result=_right(t,registry,result,rV,specialize(t,'mul_add',r,U,err))
        budget=apply(specialize(t,'mul_right_mono',coefficient,D,Q),t.hyp('budget'))
        budget=_left(t,registry,budget,Mul(D,Q),_multiplicative_equal(t,Mul(coefficient,Q),rerr))
        budget=_right(t,registry,budget,rerr,EqSym(t.hyp('normalization')))
        budget=apply(specialize(t,'add_left_mono',rerr,H,rU),budget)
        return apply(specialize(t,'le_trans',rV,Add(rU,rerr),Add(rU,H)),result,budget)
    return introduce(s,('r','m','g','C','Q','D','H','U','V'),('error','budget','normalization'),finish)


def _root(s):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        d,e,a,b,M,g,k,u,v,D,E,C,r,Q,H=t.terms(PARAMETERS+('Q','H'))
        de=Mul(d,e);sk=Succ(k);DE=Mul(D,E);uE=Mul(u,E);vD=Mul(v,D)
        result=apply(specialize(t,'difference',d,e,a,b,M,g,k,u,v,D,E,C,Q),
            *(t.hyp(name) for name in ('nonzero_d','nonzero_e','bound_a','bound_b','forward','backward',
                'power_a','power_b','power_d','power_e','power_M','power_de')))
        product=apply(specialize(t,'product',sk,d,e,D,E,H),t.hyp('power_d'),t.hyp('power_e'),t.hyp('power_next_de'))
        successor=apply(specialize(t,'successor_value',de,k,Q,H),t.hyp('power_de'),t.hyp('power_next_de'))
        normalization=_chain(EqSym(product),successor,specialize(t,'mul_comm',Q,de))
        forward=apply(specialize(t,'arithmetic',r,sk,g,C,Q,de,DE,uE,vD),field(result,2,4),t.hyp('budget'),normalization)
        backward=apply(specialize(t,'arithmetic',r,sk,g,C,Q,de,DE,vD,uE),field(result,3,4),t.hyp('budget'),normalization)
        return conjunction(field(result,0,4),field(result,1,4),forward,backward)
    def next_power(t):
        return eliminate(t,specialize(t,'power_exists',Mul(t.term('d'),t.term('e')),Succ(t.term('k'))),('H',),'power_next_de',finish)
    def start(t):
        return eliminate(t,specialize(t,'power_exists',Mul(t.term('d'),t.term('e')),t.term('k')),('Q',),'power_de',next_power)
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','bound_a','bound_b','forward','backward',
        'power_a','power_b','power_d','power_e','power_M','budget'),start)


def prove_requested_power_precision(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP080',target=frozen_requested_power_precision_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP080':_root},pins=requested_power_precision_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
