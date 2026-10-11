"""CV091: actual finite atanh truncations obey valid rational order bounds.

Retain the supplied table's constructed prefix/whole values and powers.
Every denominator is proved nonzero before asserting prefix<=whole<=prefix
plus 3/3^M. This is a finite estimate, not a definition of an analytic limit.
"""
from hashlib import sha256

from sqrt2_power_atanh_truncation import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,atanh_truncation_source_pins,NAMED_SOURCE as TRUNCATION_SOURCE,
    OUTPUTS as TRUNCATION_OUTPUTS,PARAMETERS,conjoin,
)
from sqrt2_power_rational_tail_majorant import (
    definition_registry,rational_tail_majorant_source_pins,
    HELPER_SOURCES as RATIONAL_HELPERS,ENDPOINT_SOURCES as RATIONAL_ENDPOINTS,
)
from sqrt2_power_composition_tail_bound import RATIONAL_TAIL_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-atanh-rational-truncation-v1"
OUTPUTS=("x","z","p","h")
ORDER_PARTS=("~(d*p)=0","~(d*h)=0","IRatLe(3*x,0,d*p,3*z,0,d*h)","IRatLe(3*z,0,d*h,3*x+3*d,0,d*p)")
PARTS=("NatHornerValue(ab,ac,3,M,x)","NatHornerValue(ab,ac,3,M+N,z)","Pow(3,M,p)","Pow(3,M+N,h)")+ORDER_PARTS
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~d=0 -> NatAtanhPrefix(d,ab,ac,M+N) -> exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256="c1d96e8b045d76e79bd363c41f9562f92787aaef0867562246f3d89f06132418"
HELPER_SOURCES={"orders":"forall d p h x z. ~d=0 -> ~p=0 -> ~h=0 -> Le(h*x,p*z) -> Le(p*z,h*x+d*h) -> "+conjoin(ORDER_PARTS)}
HELPER_TARGET_SHA256={"orders":"9a5c0ce1518d75ab5aed86b844855302ed0cfd93b4c8888d13fa3fba4ae623e0"}
TRUNCATION_ARCHIVE=dict(case="CV090",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-atanh-truncation-v1/generation-process.json.gz",
    bytes=36378,sha256="b37c8955b75676047285c9fdb11af75224d72fced2d4730727c9b1fb145a0452",
    raw_bytes=631452,raw_sha256="088ccea5aa7beef7a1039785af849fc05fa3623dd4a0b682ee518185cf606206",
    bundle_bytes=357579,bundle_sha256="0fdb76e370b33e761b9fd995aafbdc8a6d9bb0db5819bb8216a9d6d4ca7760c3",
    nodes=142,root=141,target_ast_sha256="fe8e75a1b92914b876b3335a496085b7cea520d900aaedca8a40e6f31ac26fa6")
ARCHIVES=(TRUNCATION_ARCHIVE,RATIONAL_TAIL_ARCHIVE)
ENDPOINT_SOURCES={name:RATIONAL_ENDPOINTS[name] for name in
    ("power_nonzero","succ_ne_zero","mul_ne_zero","mul_left_mono","mul_assoc","mul_comm")}
ENDPOINT_SOURCES.update(truncation=TRUNCATION_SOURCE,positive_order=RATIONAL_HELPERS["positive_order"],
    mul_add="forall a b c. a*(b+c)=a*b+a*c",add_mul="forall a b c. (a+b)*c=a*c+b*c")
ENDPOINT_OWNERS={name:"CV075" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(truncation="CV090",mul_add="CV090",add_mul="CV090")
HELPER_DEPENDENCIES={
    "orders":("positive_order","mul_ne_zero","mul_left_mono","mul_assoc","mul_comm","mul_add","add_mul"),
    "CV091":("truncation","orders","power_nonzero","succ_ne_zero"),
}


class AtanhRationalTruncationError(ValueError):
    """Changed actual finite input, positive normalization or rational errors."""


def frozen_atanh_rational_truncation_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=5 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise AtanhRationalTruncationError("CV091 exact valid rational truncation changed")
    return target


def source_contract():
    return dict(code="CV091",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,supplied_atanh_table_preserved=True,actual_prefix_whole_values_and_powers_constructed=True,
        all_rational_denominators_proved_nonzero=True,nonzero_denominator_required=True,
        prefix_length="M",whole_length="M+N",powers="p=3^M; h=3^(M+N)",
        rational_bounds="3*x/(d*p)<=3*z/(d*h)<=(3*x+3*d)/(d*p)",finite_error="3/3^M",
        empty_prefix_and_empty_tail_allowed=True,independent_code_equality_claimed=False,
        analytic_limit_claim=False,analytic_logarithm_identity=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def atanh_rational_truncation_source_pins():
    result=atanh_truncation_source_pins()
    for name,pin in rational_tail_majorant_source_pins().items():
        if name in result and result[name]!=pin:
            raise AtanhRationalTruncationError("rational truncation source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_atanh_truncation.py":"6d9366b12889d5eb98f47827f7e9ac216e57ed8b46300d16dde078ad51a6f4c7",
        "scripts/sqrt2_power_rational_tail_majorant.py":"9dc0903202c1c4922011503b997a6ad2556a8d59c8750f0a028b50da038a1776",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_atanh_rational_truncation.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise AtanhRationalTruncationError("rational truncation source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _orders(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    three=Succ(Succ(Succ(Zero())))
    def finish(t):
        d,p,h,x,z=t.terms(("d","p","h","x","z"))
        dp,dh=Mul(d,p),Mul(d,h);tx,tz,td=Mul(three,x),Mul(three,z),Mul(three,d)
        dpnz=apply(specialize(t,"mul_ne_zero",d,p),t.hyp("d_nonzero"),t.hyp("p_nonzero"))
        dhnz=apply(specialize(t,"mul_ne_zero",d,h),t.hyp("d_nonzero"),t.hyp("h_nonzero"))
        lower=apply(specialize(t,"mul_left_mono",Mul(h,x),Mul(p,z),td),t.hyp("lower"))
        left=_multiplicative_equal(t,Mul(td,Mul(h,x)),Mul(tx,dh))
        right=_multiplicative_equal(t,Mul(td,Mul(p,z)),Mul(tz,dp))
        lower=_subst(t,registry,"Le(slot,(3*d)*(p*z))",left,lower)
        lower=_subst(t,registry,"Le((3*x)*(d*h),slot)",right,lower)
        lower=apply(specialize(t,"positive_order",tx,tz,dp,dh),dpnz,dhnz,lower)
        upper=apply(specialize(t,"mul_left_mono",Mul(p,z),Add(Mul(h,x),dh),td),t.hyp("upper"))
        upper=_subst(t,registry,"Le(slot,(3*d)*(h*x+d*h))",right,upper)
        aligned=_chain(specialize(t,"mul_add",td,Mul(h,x),dh),CongAdd(left,EqRefl(Mul(td,dh))),
            EqSym(specialize(t,"add_mul",tx,td,dh)))
        upper=_subst(t,registry,"Le((3*z)*(d*p),slot)",aligned,upper)
        upper=apply(specialize(t,"positive_order",tz,Add(tx,td),dh,dp),dhnz,dpnz,upper)
        return conjunction(dpnz,dhnz,lower,upper)
    return introduce(s,("d","p","h","x","z"),("d_nonzero","p_nonzero","h_nonzero","lower","upper"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Add,Succ,Zero
    two=Succ(Succ(Zero()));three=Succ(two)
    def chosen(t):
        data=t.hyp("data");M,N=t.terms(("M","N"))
        nonzero=apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",two))
        pnz=apply(instantiate(nonzero,M,t.term("p")),field(data,4,12))
        hnz=apply(instantiate(nonzero,Add(M,N),t.term("h")),field(data,6,12))
        orders=apply(specialize(t,"orders",*t.terms(("d","p","h","x","z"))),t.hyp("nonzero"),pnz,hnz,field(data,10,12),field(data,11,12))
        return witness(t.terms(OUTPUTS),conjunction(*(field(data,i,12) for i in (1,3,4,6)),
            *(field(orders,i,4) for i in range(4))))
    return introduce(s,PARAMETERS,("nonzero","prefix"),lambda t:
        eliminate(t,apply(specialize(t,"truncation",*t.terms(PARAMETERS)),t.hyp("prefix")),TRUNCATION_OUTPUTS,"data",chosen))


def prove_atanh_rational_truncation(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV091",target=frozen_atanh_rational_truncation_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"orders":lambda s:_orders(s,registry),"CV091":_root},pins=atanh_rational_truncation_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
