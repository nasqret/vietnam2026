"""SQ002: square bounds locate a supplied actual integer floor root.

From a^2 <= n < b^2 and FloorSqrt(n,s), prove a <= s < b. Natural
decidable order is replayed from HA bodies, not imported as classical logic.
"""
from hashlib import sha256

from sqrt2_power_floor_sqrt import (
    ROOT,Scope,introduce,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,floor_sqrt_source_pins,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-floor-sqrt-comparison-v1"
NAMED_SOURCE="forall n s a b. FloorSqrt(n,s) -> Le(a*a,n) -> Lt(n,b*b) -> Le(a,s) /\\ Lt(s,b)"
TARGET_SHA256="87748e18b800d65594ab1288e0586b089302a29354fd0c34e978ab8a54a76e5a"
HELPER_SOURCES={"square_mono":"forall a b. Le(a,b) -> Le(a*a,b*b)"}
HELPER_TARGET_SHA256={"square_mono":"c3d604d481dbef800ed95f7786c05d1e7507c2f2dffa8d81b0be79dc1300638d"}
FLOOR_ARCHIVE=dict(case="SQ001",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-floor-sqrt-v1/generation-process.json.gz",
    bytes=7357,sha256="f751c8912378cc9b26567fc7899e61d760d50ee2d4734389f1fcaff757f613d5",
    raw_bytes=59080,raw_sha256="51be5f8b736265a073ce6e5283e124751fb910d9ad00a72bbee7b9330de85bec",
    bundle_bytes=29866,bundle_sha256="c67e379ff1997694a46682d276a9f81661370a42a311190580828229450435de",
    nodes=31,root=30,target_ast_sha256="da6b93cc7d0f9f4458be509f5f2405cac0063f79ab70acfef60768c09a0f2d5c")
ARCHIVES=(FLOOR_ARCHIVE,)
ENDPOINT_SOURCES={
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "le_or_lt":"forall a b. Le(a,b) \\/ Lt(b,a)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
}
ENDPOINT_OWNERS={name:"SQ001" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES={
    "square_mono":("mul_left_mono","mul_right_mono","le_trans"),
    "SQ002":("square_mono","le_or_lt","le_trans","lt_not_le"),
}


class FloorSqrtComparisonError(ValueError):
    """Changed exact square bounds, archive dependency or proof contract."""


def frozen_floor_sqrt_comparison_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=4 or len(premises)!=3 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FloorSqrtComparisonError("SQ002 exact square-comparison target changed")
    return target


def source_contract():
    return dict(code="SQ002",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,supplied_actual_floor_root_preserved=True,
        both_square_bound_premises_preserved=True,lower_bound_nonstrict=True,upper_bound_strict=True,
        zero_input_allowed=True,natural_decidable_order_replayed=True,new_induction_needed=False,
        reused_definition_ids=["PD0001","PD0002","PD0051"],new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        real_square_root_or_dyadic_accuracy_claim=False,analytic_limit_claim=False,
        closes_IR013=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def floor_sqrt_comparison_source_pins():
    result=floor_sqrt_source_pins()
    expected={"scripts/sqrt2_power_floor_sqrt.py":"157a35dec84285067445a04a7c2f03b748d2a8602da90a97365bcd6f3c289136",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        "scripts/sqrt2_power_convolution_unit.py":"d058762fb3641d5bb1e90c764c4581801feeaf0a103901811b3e82dbe3db8f16",
        "scripts/sqrt2_power_quadratic_product_exists.py":"c20c38bfceb78fa16c236925024a43c12624b2df23937bb1c1e9f54393d49017",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_floor_sqrt_comparison.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FloorSqrtComparisonError("floor-comparison source or actual proof archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _square_mono(s):
    from peano_lab.kernel.terms import Mul
    def finish(t):
        a,b=t.terms(("a","b"))
        left=apply(specialize(t,"mul_right_mono",a,b,a),t.hyp("bound"))
        right=apply(specialize(t,"mul_left_mono",a,b,b),t.hyp("bound"))
        return apply(specialize(t,"le_trans",Mul(a,a),Mul(b,a),Mul(b,b)),left,right)
    return introduce(s,("a","b"),("bound",),finish)


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,OrElim
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        n,root,a,b=t.terms(("n","s","a","b"))
        lower_yes=t.hypothesis("lower_yes");lower_no=t.hypothesis("lower_no")
        larger_square=apply(specialize(lower_no,"square_mono",Succ(root),a),lower_no.hyp("lower_no"))
        larger_square=apply(specialize(lower_no,"le_trans",Mul(Succ(root),Succ(root)),Mul(a,a),n),larger_square,lower_no.hyp("square_lower"))
        contradiction=apply(specialize(lower_no,"lt_not_le",n,Mul(Succ(root),Succ(root))),AndElimR(lower_no.hyp("floor")),larger_square)
        lower=OrElim(specialize(t,"le_or_lt",a,root),lower_yes.hyp("lower_yes"),BotElim(contradiction))
        upper_no=t.hypothesis("upper_no");upper_yes=t.hypothesis("upper_yes")
        smaller_square=apply(specialize(upper_no,"square_mono",b,root),upper_no.hyp("upper_no"))
        smaller_square=apply(specialize(upper_no,"le_trans",Mul(b,b),Mul(root,root),n),smaller_square,AndElimL(upper_no.hyp("floor")))
        contradiction=apply(specialize(upper_no,"lt_not_le",n,Mul(b,b)),upper_no.hyp("square_upper"),smaller_square)
        upper=OrElim(specialize(t,"le_or_lt",b,root),BotElim(contradiction),upper_yes.hyp("upper_yes"))
        return conjunction(lower,upper)
    return introduce(s,("n","s","a","b"),("floor","square_lower","square_upper"),finish)


def prove_floor_sqrt_comparison(*,limits=None):
    return assemble_mixed_certificate(code="SQ002",target=frozen_floor_sqrt_comparison_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"square_mono":_square_mono,"SQ002":_root},pins=floor_sqrt_comparison_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
