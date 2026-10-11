"""SQ006: compatible actual dyadic sqrt(2) computations at ordered precisions.

Construct the intervening power e=2^l, prove q=d*e for the supplied coarse
and fine denominators, and locate the fine numerator in [s*e,(s+1)*e).
Neither computation nor its actual witnesses is replaced by a convenient code.
"""
from hashlib import sha256

from sqrt2_power_dyadic_sqrt2 import (
    ROOT,Scope,introduce,eliminate,witness,conjunction,apply,specialize,canonical,json_hash,
    definition_registry,dyadic_sqrt2_source_pins,COMPOSITION_ARCHIVE,RATIONAL_TAIL_ARCHIVE,_and,
)
from sqrt2_power_floor_sqrt_scaling import (
    NAMED_SOURCE as SCALING_SOURCE,floor_sqrt_scaling_source_pins,
)
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-dyadic-sqrt2-refinement-v1"
PARAMETERS=("k","l","d","s","q","t")
PARTS=("Pow(2,l,e)","~e=0","q=d*e","Le(s*e,t)","Lt(t,(S s)*e)")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". DyadicSqrt2(k,d,s) -> DyadicSqrt2(k+l,q,t) -> exists e. "+_and(PARTS)
TARGET_SHA256="4c4a92be36b18b982f9f2f1196e3d2d996ddb4e94fa07479a82bc2eb01d548df"
SCALING_ARCHIVE=dict(case="SQ005",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-floor-sqrt-scaling-v1/generation-process.json.gz",
    bytes=8842,sha256="47e637c9928e3af2f28a1bbaa1ba2c3c9a9532e11c4511e7e1486225f10d734f",
    raw_bytes=64914,raw_sha256="d38d5f91c3eb0765e321c4fd52e34976dbc1d17b746b7f971f010693fe023aaa",
    bundle_bytes=29300,bundle_sha256="281d07e71b9dffd4902db8ba8c2a02b0ae4a9073befdb0d3ed21490253c78a82",
    nodes=24,root=23,target_ast_sha256="af5a7f392980a78a1da6c3dd0057aaee1ddbfe5ffb78712c7317553f73567df8")
ARCHIVES=(SCALING_ARCHIVE,COMPOSITION_ARCHIVE,RATIONAL_TAIL_ARCHIVE)
ENDPOINT_SOURCES={
    "scaling":SCALING_SOURCE,"power_exists":"forall a k. exists d. Pow(a,k,d)",
    "power_add":"forall a e f s x y z. s=e+f -> Pow(a,e,x) -> Pow(a,f,y) -> Pow(a,s,z) -> z=x*y",
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS={name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(scaling="SQ005",power_nonzero="CV075",succ_ne_zero="CV075")
HELPER_DEPENDENCIES={"SQ006":tuple(ENDPOINT_SOURCES)}


class DyadicSqrt2RefinementError(ValueError):
    """Changed exact actual computation, precision increment or scaling factor."""


def frozen_dyadic_sqrt2_refinement_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise DyadicSqrt2RefinementError("SQ006 exact ordered dyadic-refinement target changed")
    return target


def source_contract():
    return dict(code="SQ006",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,both_supplied_actual_computations_preserved=True,precision_increment="l",
        zero_precision_and_increment_allowed=True,intervening_power_constructed=True,scale_nonzero_proved=True,
        actual_denominator_product_proved=True,integer_bounds="s*e<=t<(s+1)*e",
        reused_definition_ids=["PD0020","PD0051","ND0446"],new_definition_ids=[],definition_admissions=0,
        new_induction_needed=False,original_HA_checked=False,authority="source_contract_not_proof_authority",
        real_square_root_interpretation=False,rational_interval_width_proved=False,analytic_limit_claim=False,
        closes_IR014=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def dyadic_sqrt2_refinement_source_pins():
    result=dyadic_sqrt2_source_pins()
    for name,pin in floor_sqrt_scaling_source_pins().items():
        if name in result and result[name]!=pin:
            raise DyadicSqrt2RefinementError("dyadic-refinement source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_dyadic_sqrt2.py":"9c498535a2397cc43911427ae9cdd7e35a46b26c966e85aac294ba871e3e07dc",
        "scripts/sqrt2_power_floor_sqrt_scaling.py":"d14e423ebebf0155abead7f9a955d560a5695cac9beb492f1e77c8847db50a4f",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_dyadic_sqrt2_refinement.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise DyadicSqrt2RefinementError("dyadic-refinement source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish(t):
        k,l,d,root,q,out,e=t.terms(PARAMETERS+("e",));kl=Add(k,l)
        equality=apply(specialize(t,"power_add",two,k,l,kl,d,e,q),EqRefl(kl),
            AndElimL(t.hyp("coarse")),t.hyp("factor_power"),AndElimL(t.hyp("fine")))
        positive=apply(specialize(t,"power_nonzero",two),specialize(t,"succ_ne_zero",one))
        positive=apply(instantiate(positive,l,e),t.hyp("factor_power"))
        scaled_floor=_subst(t,registry,"FloorSqrt(2*(slot*slot),t)",equality,AndElimR(t.hyp("fine")))
        n=Mul(two,Mul(d,d));ee=Mul(e,e);de=Mul(d,e)
        normalize=_multiplicative_equal(t,Mul(two,Mul(de,de)),Mul(n,ee))
        scaled_floor=_subst(t,registry,"FloorSqrt(slot,t)",normalize,scaled_floor)
        bounds=apply(specialize(t,"scaling",n,root,e,out),positive,AndElimR(t.hyp("coarse")),scaled_floor)
        return witness((e,),conjunction(t.hyp("factor_power"),positive,equality,AndElimL(bounds),AndElimR(bounds)))
    return introduce(s,PARAMETERS,("coarse","fine"),lambda t:
        eliminate(t,specialize(t,"power_exists",two,t.term("l")),("e",),"factor_power",finish))


def prove_dyadic_sqrt2_refinement(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="SQ006",target=frozen_dyadic_sqrt2_refinement_target(),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,endpoint_owners=ENDPOINT_OWNERS,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories={"SQ006":lambda s:_root(s,registry)},
        pins=dyadic_sqrt2_refinement_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
