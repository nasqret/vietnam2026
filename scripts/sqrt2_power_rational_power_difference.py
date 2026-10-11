"""AP079: power errors for independently normalized nonnegative rationals.

Construct actual powers of the cross-numerators and their common bound.
AP078 identifies their values; AP077 supplies the symmetric estimate. Keep
the supplied denominator powers and prove them nonzero. No cancellation or
equality of table codes is assumed.
"""
from hashlib import sha256

from sqrt2_power_symmetric_power_difference import (
    ROOT,Scope,introduce,eliminate,apply,specialize,canonical,json_hash,
    definition_registry,symmetric_power_difference_source_pins,
    NAMED_SOURCE as SYMMETRIC_SOURCE,POWER_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_product_power import NAMED_SOURCE as PRODUCT_SOURCE,product_power_source_pins
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-rational-power-difference-v1'
PARAMETERS=('d','e','a','b','M','g','k','u','v','D','E','C','Q')
PREMISES=('~d=0','~e=0','Le(a,M*d)','Le(b,M*e)','Le(b*d,a*e+g)','Le(a*e,b*d+g)',
    'Pow(a,S k,u)','Pow(b,S k,v)','Pow(d,S k,D)','Pow(e,S k,E)','Pow(M,k,C)','Pow(d*e,k,Q)')
ERROR='(S k)*(g*(C*Q))'
BOUNDS=f'Le(v*D,u*E+{ERROR}) /\\ Le(u*E,v*D+{ERROR})'
CONCLUSION='~D=0 /\\ (~E=0 /\\ ('+BOUNDS+'))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='0be1195ec265753f6216218bc22c6933b86df205ce422c95f0c25df112074b61'
SYMMETRIC_ARCHIVE=dict(case='AP077',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-symmetric-power-difference-v1/generation-process.json.gz',
    bytes=35645,sha256='4a883e3e915fd9fdcb5c33eb7f2780f611084aed784089d32e5ce5c34de71d46',
    raw_bytes=269316,raw_sha256='85553d0742cfe1e82c2ba76d7645b927f5bd8dd63aac4946e842ae3a5e373410',
    bundle_bytes=113033,bundle_sha256='b720ef339bcbf9658387bf1a1dabbffa5358cdb0d304477734ed87996d1644aa',
    nodes=41,root=40,target_ast_sha256='9f376fc95073195bee675f73105660651b69555fbeb652e7cd0ed1e8550cdc98')
PRODUCT_ARCHIVE=dict(case='AP078',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-product-power-v1/generation-process.json.gz',
    bytes=44115,sha256='a5117b1a77bd3c3df71814dbd0daf638f3c129b93f65aeeae87c83ae073bdeeb',
    raw_bytes=459925,raw_sha256='081c44d1fe051a45e9a8315b469ab2c96bd703891fcd1f319c5802d93689ace7',
    bundle_bytes=237676,bundle_sha256='8ad49de00359af56d8e961c650663dca0440bcb9e90492d10df23c9cf564327a',
    nodes=121,root=120,target_ast_sha256='5f37e55e15971ec0ef5bcf1a9435c0ed369dbe1f3b53b3fa089c6e8ee4a2294c')
ARCHIVES=(SYMMETRIC_ARCHIVE,PRODUCT_ARCHIVE,POWER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'symmetric':SYMMETRIC_SOURCE,'product':PRODUCT_SOURCE,
    'power_exists':'forall a n. exists p. Pow(a,n,p)',
    'power_nonzero':'forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(symmetric='AP077',product='AP078',power_exists='AP010',power_nonzero='AP010')
HELPER_DEPENDENCIES={'AP079':tuple(ENDPOINT_SOURCES)}


class RationalPowerDifferenceError(ValueError):
    """Changed actual rational normalization, denominator positivity or error."""


def frozen_rational_power_difference_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=13 or len(premises)!=12 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise RationalPowerDifferenceError('AP079 exact independently normalized rational power bound changed')
    return target


def source_contract():
    return dict(code='AP079',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=12,all_six_actual_powers_preserved=True,both_positive_argument_denominators_preserved=True,
        independent_argument_denominators_allowed=True,both_output_denominator_powers_proved_nonzero=True,
        actual_cross_numerator_and_bound_powers_constructed=True,argument_bounds=['a<=M*d','b<=M*e'],
        symmetric_input_error='abs(b*d-a*e)<=g',symmetric_output_error='abs(v*D-u*E)<=(k+1)*g*(C*Q)',
        error_powers='C=M^k;Q=(d*e)^k',output_denominators='D=d^(k+1);E=e^(k+1)',
        input_order_assumed=False,zero_numerators_gap_bound_and_k_allowed=True,
        denominator_cancellation_used=False,code_number_equality_claimed=False,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        analytic_power_or_exponential_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def rational_power_difference_source_pins():
    result=symmetric_power_difference_source_pins()
    for name,pin in product_power_source_pins().items():
        if name in result and result[name]!=pin:raise RationalPowerDifferenceError('rational-power dependency source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_symmetric_power_difference.py':'a3cdd3c508617314fc17967f07406178ca3e2333cf79c43f90327793f7082275',
        'scripts/sqrt2_power_product_power.py':'c000339f0464a5d337211fa7918916bed72fffaeed24fc7b1c14357ab9c35741',**{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_rational_power_difference.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:raise RationalPowerDifferenceError('rational-power source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        d,e,a,b,M,g,k,u,v,D,E,C,Q,X,Y,R=t.terms(PARAMETERS+('X','Y','R'))
        sk=Succ(k);de=Mul(d,e);top=Mul(M,de)
        first=apply(specialize(t,'mul_right_mono',a,Mul(M,d),e),t.hyp('bound_a'))
        first=_subst(t,registry,'Le(a*e,slot)',_multiplicative_equal(t,Mul(Mul(M,d),e),top),first)
        second=apply(specialize(t,'mul_right_mono',b,Mul(M,e),d),t.hyp('bound_b'))
        second=_subst(t,registry,'Le(b*d,slot)',_multiplicative_equal(t,Mul(Mul(M,e),d),top),second)
        result=apply(specialize(t,'symmetric',Mul(a,e),Mul(b,d),top,g,k,X,Y,R),first,second,
            t.hyp('forward'),t.hyp('backward'),t.hyp('power_cross_a'),t.hyp('power_cross_b'),t.hyp('power_reference'))
        exactX=apply(specialize(t,'product',sk,a,e,u,E,X),t.hyp('power_a'),t.hyp('power_e'),t.hyp('power_cross_a'))
        exactY=apply(specialize(t,'product',sk,b,d,v,D,Y),t.hyp('power_b'),t.hyp('power_d'),t.hyp('power_cross_b'))
        exactR=apply(specialize(t,'product',k,M,de,C,Q,R),t.hyp('power_M'),t.hyp('power_de'),t.hyp('power_reference'))
        result=_subst(t,registry,'Le(Y,slot+(S k)*(g*R)) /\\ Le(slot,Y+(S k)*(g*R))',exactX,result)
        result=_subst(t,registry,'Le(slot,u*E+(S k)*(g*R)) /\\ Le(u*E,slot+(S k)*(g*R))',exactY,result)
        result=_subst(t,registry,'Le(v*D,u*E+(S k)*(g*slot)) /\\ Le(u*E,v*D+(S k)*(g*slot))',exactR,result)
        positiveD=apply(instantiate(apply(specialize(t,'power_nonzero',d),t.hyp('nonzero_d')),sk,D),t.hyp('power_d'))
        positiveE=apply(instantiate(apply(specialize(t,'power_nonzero',e),t.hyp('nonzero_e')),sk,E),t.hyp('power_e'))
        return conjunction(positiveD,positiveE,result)
    def second(t):
        top=Mul(t.term('M'),Mul(t.term('d'),t.term('e')))
        return eliminate(t,specialize(t,'power_exists',top,t.term('k')),('R',),'power_reference',finish)
    def first(t):
        return eliminate(t,specialize(t,'power_exists',Mul(t.term('b'),t.term('d')),Succ(t.term('k'))),('Y',),'power_cross_b',second)
    def start(t):
        return eliminate(t,specialize(t,'power_exists',Mul(t.term('a'),t.term('e')),Succ(t.term('k'))),('X',),'power_cross_a',first)
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','bound_a','bound_b','forward','backward',
        'power_a','power_b','power_d','power_e','power_M','power_de'),start)


def prove_rational_power_difference(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP079',target=frozen_rational_power_difference_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP079':lambda s:_root(s,registry)},pins=rational_power_difference_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
