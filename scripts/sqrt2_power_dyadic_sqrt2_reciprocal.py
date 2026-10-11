"""SQ010: explicit finite modulus for reciprocals of dyadic sqrt(2) values.

From supplied computations at k and k+l, prove positive reciprocal
denominators and 0<=d/s-q/t<=1/d using exact cross-multiplied inequalities.
No reciprocal real number or convergence assertion is postulated.
"""
from hashlib import sha256

from sqrt2_power_dyadic_sqrt2_square_error import (
    ROOT,Scope,introduce,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,dyadic_sqrt2_square_error_source_pins,BOUND_ARCHIVE,_and,
    NAMED_SOURCE as SQUARE_SOURCE,
)
from sqrt2_power_dyadic_sqrt2_modulus import (
    dyadic_sqrt2_modulus_source_pins,PARAMETERS,NAMED_SOURCE as MODULUS_SOURCE,
)
from sqrt2_power_quadratic_trace_exists import field
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-dyadic-sqrt2-reciprocal-v1"
PARTS=("~d=0","~s=0","~t=0","Le(q*s,d*t)","Le(d*(d*t),d*(q*s)+s*t)")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". DyadicSqrt2(k,d,s) -> DyadicSqrt2(k+l,q,t) -> "+_and(PARTS)
TARGET_SHA256="4e5333c99ca1ed711e3c4059b5352c1b5545b4d3d6ce9e26db04482a0f15cdcd"
HELPER_SOURCES={"arithmetic":"forall d s q t. Le(s*q,t*d) -> Le(t*d,s*q+q) -> Le(d,s) -> Le(q,t) -> Le(q*s,d*t) /\\ Le(d*(d*t),d*(q*s)+s*t)"}
HELPER_TARGET_SHA256={"arithmetic":"151c6d0c697e71b09038862c572b39f598a503f5e731b30d2269b4b69b5d76ba"}
MODULUS_ARCHIVE=dict(case="SQ008",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-dyadic-sqrt2-modulus-v2/generation-process.json.gz",
    bytes=25993,sha256="0e38ac8a9088425f6c512fd6299af5281c0ca8cf94fb66d638215b2b79a6bd43",
    raw_bytes=480053,raw_sha256="8f9664f8fde8ea734cee5bc31331a85ac00b19138041f82698f40ad78f00e843",
    bundle_bytes=288954,bundle_sha256="fa202c285e41ec0f1b6619dc5605fd748dba041a74efb3ee72cd9abbb5861f32",
    nodes=136,root=135,target_ast_sha256="a431f58073293b4d6efa8d8122c194a4bcbaa3f8ad022a73b9f8d2a0b8182910")
SQUARE_ARCHIVE=dict(case="SQ009",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-dyadic-sqrt2-square-error-v1/generation-process.json.gz",
    bytes=13396,sha256="47c69df09658ad4b42256f1204472159d2b7bb60bfb84b8943f6ae40a9372ac6",
    raw_bytes=167484,raw_sha256="0787377497ea9973603346d98cd09568818e25b27ec2db5758185453f287ee77",
    bundle_bytes=91493,bundle_sha256="1189e78e28fb6697459f8f7ff4696adaa4d8f739643e53c11fa82c491066e274",
    nodes=53,root=52,target_ast_sha256="c5d6445cccb9460719eff249437f8849968eaa22bcc68dc2d5615589e7873a0c")
ARCHIVES=(MODULUS_ARCHIVE,SQUARE_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "modulus":MODULUS_SOURCE,"square":SQUARE_SOURCE,
    "mul_comm":"forall a b. a*b=b*a","mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(modulus="SQ008",square="SQ009")
HELPER_DEPENDENCIES={
    "arithmetic":("mul_comm","mul_add","mul_left_mono","mul_right_mono","add_left_mono","le_trans"),
    "SQ010":("modulus","square","arithmetic"),
}


class DyadicSqrt2ReciprocalError(ValueError):
    """Changed reciprocal sign, denominator guard, exact error or source."""


def frozen_dyadic_sqrt2_reciprocal_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=2 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise DyadicSqrt2ReciprocalError("SQ010 exact supplied reciprocal-modulus target changed")
    return target


def source_contract():
    return dict(code="SQ010",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,both_supplied_actual_computations_preserved=True,all_used_denominators_proved_nonzero=True,
        reciprocal_order_reversed=True,exact_natural_upper="d*(d*t)<=d*(q*s)+s*t",
        rational_error_reading="0<=d/s-q/t<=1/d=2^(-k)",zero_precision_and_increment_allowed=True,
        new_induction_needed=False,reused_definition_ids=["PD0020","PD0051","ND0446"],
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",real_reciprocal_identity_claim=False,
        analytic_limit_claim=False,closes_IR015=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def dyadic_sqrt2_reciprocal_source_pins():
    result=dyadic_sqrt2_square_error_source_pins()
    for name,pin in dyadic_sqrt2_modulus_source_pins().items():
        if name in result and result[name]!=pin:
            raise DyadicSqrt2ReciprocalError("reciprocal source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_dyadic_sqrt2_square_error.py":"8fd7a8ae82f1cfccf25dffa649624af229c3bd11069b9dee0bb8bd6df47c66e0",
        "scripts/sqrt2_power_dyadic_sqrt2_modulus.py":"b8904d9d330caf1455cbd985d2eea11cc9bf6f8cf579f5d460aa807628998b29",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_dyadic_sqrt2_reciprocal.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise DyadicSqrt2ReciprocalError("reciprocal source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        d,root,q,out=t.terms(("d","s","q","t"));qs=Mul(q,root);dt=Mul(d,out)
        lower=_subst(t,registry,"Le(slot,t*d)",specialize(t,"mul_comm",root,q),t.hyp("lower"))
        lower=_subst(t,registry,"Le(q*s,slot)",specialize(t,"mul_comm",out,d),lower)
        upper=_subst(t,registry,"Le(slot,s*q+q)",specialize(t,"mul_comm",out,d),t.hyp("upper"))
        upper=_subst(t,registry,"Le(d*t,slot)",CongAdd(specialize(t,"mul_comm",root,q),EqRefl(q)),upper)
        fine=apply(specialize(t,"add_left_mono",q,out,qs),t.hyp("fine_range"))
        upper=apply(specialize(t,"le_trans",dt,Add(qs,q),Add(qs,out)),upper,fine)
        upper=apply(specialize(t,"mul_left_mono",dt,Add(qs,out),d),upper)
        upper=_subst(t,registry,"Le(d*(d*t),slot)",specialize(t,"mul_add",d,qs,out),upper)
        coarse=apply(specialize(t,"mul_right_mono",d,root,out),t.hyp("coarse_range"))
        coarse=apply(specialize(t,"add_left_mono",dt,Mul(root,out),Mul(d,qs)),coarse)
        upper=apply(specialize(t,"le_trans",Mul(d,dt),Add(Mul(d,qs),dt),Add(Mul(d,qs),Mul(root,out))),upper,coarse)
        return conjunction(lower,upper)
    return introduce(s,("d","s","q","t"),("lower","upper","coarse_range","fine_range"),finish)


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add
    def finish(t):
        k,l,d,root,q,out=t.terms(PARAMETERS)
        direct=apply(specialize(t,"modulus",*t.terms(PARAMETERS)),t.hyp("coarse"),t.hyp("fine"))
        coarse=apply(specialize(t,"square",k,d,root),t.hyp("coarse"))
        fine=apply(specialize(t,"square",Add(k,l),q,out),t.hyp("fine"))
        arithmetic=apply(specialize(t,"arithmetic",d,root,q,out),field(direct,2,4),field(direct,3,4),field(coarse,2,6),field(fine,2,6))
        return conjunction(field(coarse,0,6),field(coarse,1,6),field(fine,1,6),AndElimL(arithmetic),AndElimR(arithmetic))
    return introduce(s,PARAMETERS,("coarse","fine"),finish)


def prove_dyadic_sqrt2_reciprocal(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="SQ010",target=frozen_dyadic_sqrt2_reciprocal_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"arithmetic":lambda s:_arithmetic(s,registry),"SQ010":_root},
        pins=dyadic_sqrt2_reciprocal_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
