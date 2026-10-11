"""SQ005: positive integer rescaling preserves the floor-root bracket.

If s=floor(sqrt(n)) and t=floor(sqrt(n*e^2)), e!=0, then
s*e<=t<(s+1)*e. This is the finite nested-bracket step, not a real limit.
"""
from hashlib import sha256

from sqrt2_power_scaled_sqrt2 import (
    ROOT,Scope,introduce,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,scaled_sqrt2_source_pins,FLOOR_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE,
    COMPARISON_SOURCE,
)
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-floor-sqrt-scaling-v1"
NAMED_SOURCE="forall n s e t. ~e=0 -> FloorSqrt(n,s) -> FloorSqrt(n*(e*e),t) -> Le(s*e,t) /\\ Lt(t,(S s)*e)"
TARGET_SHA256="af5a7f392980a78a1da6c3dd0057aaee1ddbfe5ffb78712c7317553f73567df8"
HELPER_SOURCES={"mul_strict":"forall a b c. Lt(a,b) -> ~c=0 -> Lt(a*c,b*c)"}
HELPER_TARGET_SHA256={"mul_strict":"24628a0a90f5b83f8f628dcd9fe32e04d660daee6b2ed788b1ef30a87adfbced"}
ARCHIVES=(FLOOR_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "comparison":COMPARISON_SOURCE,
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "mul_lt_succ_left":"forall a b. ~a=0 -> Lt(a*b,a*(S b))",
    "lt_le_trans":"forall a b c. Lt(a,b) -> Le(b,c) -> Lt(a,c)",
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(comparison="SQ002",mul_lt_succ_left="SQ001",lt_le_trans="SQ001")
HELPER_DEPENDENCIES={
    "mul_strict":("mul_right_mono","mul_lt_succ_left","lt_le_trans","mul_comm"),
    "SQ005":("comparison","mul_right_mono","mul_strict","mul_ne_zero","mul_assoc","mul_comm"),
}


class FloorSqrtScalingError(ValueError):
    """Changed scale, strict positivity, actual floor computation or bound."""


def frozen_floor_sqrt_scaling_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=4 or len(premises)!=3 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FloorSqrtScalingError("SQ005 exact positive rescaling target changed")
    return target


def source_contract():
    return dict(code="SQ005",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,positive_scale_required=True,two_supplied_actual_floor_roots_preserved=True,
        arbitrary_natural_input=True,zero_input_and_root_allowed=True,integer_bounds="s*e<=t<(s+1)*e",
        new_induction_needed=False,reused_definition_ids=["PD0001","PD0002","PD0051"],
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",real_square_root_interpretation=False,
        analytic_limit_claim=False,closes_IR014=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def floor_sqrt_scaling_source_pins():
    result=scaled_sqrt2_source_pins()
    expected={"scripts/sqrt2_power_scaled_sqrt2.py":"0efd0071acdea8b96a65b3f577fa6fa3737adbca633cb22299bd571614991d98",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_floor_sqrt_scaling.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FloorSqrtScalingError("square-root rescaling source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _mul_strict(s,registry):
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        a,b,c=t.terms(("a","b","c"))
        strict=apply(specialize(t,"mul_lt_succ_left",c,a),t.hyp("nonzero"))
        strict=_subst(t,registry,"Lt(slot,c*(S a))",specialize(t,"mul_comm",c,a),strict)
        strict=_subst(t,registry,"Lt(a*c,slot)",specialize(t,"mul_comm",c,Succ(a)),strict)
        bound=apply(specialize(t,"mul_right_mono",Succ(a),b,c),t.hyp("strict"))
        return apply(specialize(t,"lt_le_trans",Mul(a,c),Mul(Succ(a),c),Mul(b,c)),strict,bound)
    return introduce(s,("a","b","c"),("strict","nonzero"),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        n,root,e,out=t.terms(("n","s","e","t"));ee=Mul(e,e)
        lo,hi=Mul(root,e),Mul(Succ(root),e)
        lower=apply(specialize(t,"mul_right_mono",Mul(root,root),n,ee),AndElimL(t.hyp("floor")))
        lower=_subst(t,registry,"Le(slot,n*(e*e))",
            _multiplicative_equal(t,Mul(Mul(root,root),ee),Mul(lo,lo)),lower)
        enz=apply(specialize(t,"mul_ne_zero",e,e),t.hyp("nonzero"),t.hyp("nonzero"))
        upper=apply(specialize(t,"mul_strict",n,Mul(Succ(root),Succ(root)),ee),AndElimR(t.hyp("floor")),enz)
        upper=_subst(t,registry,"Lt(n*(e*e),slot)",
            _multiplicative_equal(t,Mul(Mul(Succ(root),Succ(root)),ee),Mul(hi,hi)),upper)
        return apply(specialize(t,"comparison",Mul(n,ee),out,lo,hi),t.hyp("scaled_floor"),lower,upper)
    return introduce(s,("n","s","e","t"),("nonzero","floor","scaled_floor"),finish)


def prove_floor_sqrt_scaling(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="SQ005",target=frozen_floor_sqrt_scaling_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"mul_strict":lambda s:_mul_strict(s,registry),"SQ005":lambda s:_root(s,registry)},
        pins=floor_sqrt_scaling_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
