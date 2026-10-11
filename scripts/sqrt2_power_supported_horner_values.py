"""CV057: support-complete multiplication for supplied computation witnesses.

Convolution and Horner code numbers need not equal the codes constructed by
CV056. Only their actual coefficient and endpoint values are transported.
Every premise, the extra multiplier, and the power scaling remain explicit.
"""
from hashlib import sha256

from sqrt2_power_supported_horner_product import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,canonical,json_hash,
    definition_registry,supported_horner_product_source_pins,
    NAMED_SOURCE as CONSTRUCTED_SOURCE,
)
from sqrt2_power_horner_trace import HELPER_SOURCES as HORNER_HELPERS
from sqrt2_power_horner_prefix_transport import HELPER_SOURCES as TRANSPORT_HELPERS
from sqrt2_power_natural_convolution import HELPER_SOURCES as CONVOLUTION_HELPERS
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_convolution_weights import KUMMER_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-supported-horner-values-v1"
A,B,C = ("ab","ac","L"),("bb","bc","M"),("cb","cc")
HA,HB,HC = ("ahb","ahc"),("bhb","bhc"),("chb","chc")
P = A+B+C+("r","s","t","N","q")+HA+HB+HC+("x","y","z","p")
D,DA,DB,DC = ("db","dc"),("dahb","dahc"),("dbhb","dbhc"),("dchb","dchc")
OUTPUTS = D+DA+("x0",)+DB+("y0",)+DC+("z0","p0")
PREMISES = (
    "NatZeroAfter(ab,ac,L,r)","NatZeroAfter(bb,bc,M,s)","Le(r+s,N)","N+q=L+M",
    "NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N)",
    "NatScaledHornerTrace(ab,ac,t,L,ahb,ahc)","BetaAt(ahb,ahc,L,x)",
    "NatScaledHornerTrace(bb,bc,t,M,bhb,bhc)","BetaAt(bhb,bhc,M,y)",
    "NatScaledHornerTrace(cb,cc,t,N,chb,chc)","BetaAt(chb,chc,N,z)","Pow(t,q,p)",
)
NAMED_SOURCE = "forall "+" ".join(P)+". "+" -> ".join(PREMISES+("p*z=t*(x*y)",))
TARGET_SHA256 = "77e93a327c7aa0811b3c17aa3152b979b62a19aa3ae70c957544ac810f17661a"
HELPER_SOURCES = {}
HELPER_TARGET_SHA256 = {}
PRODUCT_ARCHIVE = dict(case="CV056",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-supported-horner-product-v1/generation-process.json.gz",
    bytes=59068,sha256="2f2122ebbb0dba81855141fa03491dcc952453d4273cc572de90e7e754ba6bde",
    raw_bytes=1474754,raw_sha256="aed119ff2bfd7c6c4ca2dbcb927617a749aaf35b3402776552a2e9f8b1980a66",
    bundle_bytes=894119,bundle_sha256="7835488cb0d4b1045a1989d2979b9f5c6138e5b0fc49ed08155aa1e578decbb2",
    nodes=229,root=228,target_ast_sha256="635fb0c8045c84285d3fe940d860ef76da985384f4e0dc4f4fbb19c8fe5c1b74")
ARCHIVES = (PRODUCT_ARCHIVE,CONVOLUTION_ARCHIVE,KUMMER_ARCHIVE)
ENDPOINT_SOURCES = {
    "constructed":CONSTRUCTED_SOURCE,"horner_unique":HORNER_HELPERS["unique"],
    "trace_transport":TRANSPORT_HELPERS["transport"],"prefix_unique":CONVOLUTION_HELPERS["prefix_unique"],
    "le_refl":"forall a. Le(a,a)",
    "power_unique":"forall a n x y. Pow(a,n,x) -> Pow(a,n,y) -> x=y",
}
ENDPOINT_OWNERS = {name:"CV056" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(prefix_unique="CV003",power_unique="kummer-power-add-v1")
HELPER_DEPENDENCIES = {"CV057":tuple(ENDPOINT_SOURCES)}


class SupportedHornerValuesError(ValueError):
    """Changed support premise, actual computation or coefficient transport."""


def frozen_supported_horner_values_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=23 or len(premises)!=12 or type(conclusion) is not Eq or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SupportedHornerValuesError("CV057 exact supplied-value multiplication target changed")
    return target


def source_contract():
    return dict(code="CV057",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=12,actual_supplied_convolution_required=True,actual_supplied_horner_values_required=True,
        input_support_and_length_alignment_required=True,actual_supplied_scaling_power_required=True,
        arbitrary_code_encodings_allowed=True,code_number_equality_claimed=False,
        identity="p*z=t*(x*y)",zero_multiplier_and_empty_lengths_allowed=True,
        no_nonzero_factor_cancelled=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        arbitrary_truncated_product_equality=False,analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def supported_horner_values_source_pins():
    result = supported_horner_product_source_pins()
    expected = {"scripts/sqrt2_power_supported_horner_product.py":"a4f46a5903b53785a89e231b8b9fc5ce4b497dfec270998745290bfa1aa26afb",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_supported_horner_values.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SupportedHornerValuesError("supplied-value source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    def chosen(t):
        def unique(codes,length,left,right,trace_left,trace_right,value_left,value_right,u,v):
            invariant = apply(specialize(t,"horner_unique",*t.terms(codes+("t",length)+left+right)),trace_left,trace_right)
            return apply(instantiate(invariant,*t.terms((length,u,v))),specialize(t,"le_refl",t.term(length)),value_left,value_right)
        product = t.hyp("product")
        match = apply(specialize(t,"prefix_unique",*t.terms(A+B+D+C+("N",))),field(product,0,9),t.hyp("convolution"))
        moved = apply(specialize(t,"trace_transport",*t.terms(D+C+("t","N","N")+DC)),
            specialize(t,"le_refl",t.term("N")),match,field(product,5,9))
        xeq = unique(A[:2],"L",DA,HA,field(product,1,9),t.hyp("traceA"),field(product,2,9),t.hyp("valueA"),"x0","x")
        yeq = unique(B[:2],"M",DB,HB,field(product,3,9),t.hyp("traceB"),field(product,4,9),t.hyp("valueB"),"y0","y")
        zeq = unique(C,"N",DC,HC,moved,t.hyp("traceC"),field(product,6,9),t.hyp("valueC"),"z0","z")
        peq = apply(specialize(t,"power_unique",*t.terms(("t","q","p0","p"))),field(product,7,9),t.hyp("power"))
        identity = _subst(t,registry,"slot*z0=t*(x0*y0)",peq,field(product,8,9))
        identity = _subst(t,registry,"p*slot=t*(x0*y0)",zeq,identity)
        identity = _subst(t,registry,"p*z=t*(slot*y0)",xeq,identity)
        return _subst(t,registry,"p*z=t*(x*slot)",yeq,identity)
    return introduce(s,P,("zeroA","zeroB","cutoff","length","convolution","traceA","valueA","traceB","valueB","traceC","valueC","power"),lambda t:
        eliminate(t,apply(specialize(t,"constructed",*t.terms(A+B+("r","s","t","N","q"))),
            t.hyp("zeroA"),t.hyp("zeroB"),t.hyp("cutoff"),t.hyp("length")),OUTPUTS,"product",chosen))


def prove_supported_horner_values(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV057",target=frozen_supported_horner_values_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"CV057":lambda s:_root(s,registry)},pins=supported_horner_values_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
