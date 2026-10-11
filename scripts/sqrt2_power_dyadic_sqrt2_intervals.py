"""SQ007: supplied dyadic sqrt(2) intervals are valid and nested.

At precision k+l the lower endpoint is no smaller and the upper endpoint
is no larger than at k. Every denominator is proved nonzero; neither real
square roots nor a convergence assertion occur in the conservative graph.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_dyadic_sqrt2_refinement import (
    ROOT,Scope,introduce,eliminate,witness,conjunction,apply,specialize,canonical,json_hash,
    definition_registry as dyadic_registry,dyadic_sqrt2_refinement_source_pins,PARAMETERS,
    NAMED_SOURCE as REFINEMENT_SOURCE,COMPOSITION_ARCHIVE,RATIONAL_TAIL_ARCHIVE,
)
from sqrt2_power_quadratic_trace_exists import field
from sqrt2_power_rational_tail_majorant import definition_registry as rational_registry,HELPER_SOURCES as RATIONAL_HELPERS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-dyadic-sqrt2-intervals-v1"
CONCLUSION="IRatLe(s,0,d,t,0,q) /\\ IRatLe(S t,0,q,S s,0,d)"
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". DyadicSqrt2(k,d,s) -> DyadicSqrt2(k+l,q,t) -> "+CONCLUSION
TARGET_SHA256="13d665c846b9974b8406b7dbafd3d385a28847ea32ce289f7bf5caf79f2d8a32"
HELPER_SOURCES={"orders":"forall d q s t e. ~d=0 -> ~q=0 -> q=d*e -> Le(s*e,t) -> Lt(t,(S s)*e) -> "+CONCLUSION}
HELPER_TARGET_SHA256={"orders":"c8012f4f6d279ad300c7a4cb18787f5a881d7e9debaf40dde0bdfe6aed0c17cb"}
REFINEMENT_ARCHIVE=dict(case="SQ006",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-dyadic-sqrt2-refinement-v1/generation-process.json.gz",
    bytes=24731,sha256="255f66e8baa7e59039ee504cb64b3d77af3ea5bda1b310358ea31191f6c41b99",
    raw_bytes=451207,raw_sha256="ea5f8495bfc4668f8f64b357d5a43881b91112f17533201d909b3109fce32cd3",
    bundle_bytes=271968,bundle_sha256="de94cca849970d3b9ae6794bc012b3ac94b78e32d9475c5069ca02df86f5ba33",
    nodes=131,root=130,target_ast_sha256="4c4a92be36b18b982f9f2f1196e3d2d996ddb4e94fa07479a82bc2eb01d548df")
ARCHIVES=(REFINEMENT_ARCHIVE,RATIONAL_TAIL_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={
    "refinement":REFINEMENT_SOURCE,"positive_order":RATIONAL_HELPERS["positive_order"],
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS={name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(refinement="SQ006",positive_order="CV075",power_nonzero="CV075",succ_ne_zero="CV075")
HELPER_DEPENDENCIES={
    "orders":("positive_order","mul_right_mono","mul_assoc","mul_comm"),
    "SQ007":("refinement","orders","power_nonzero","succ_ne_zero"),
}
RATIONAL_DEFINITION_PINS={
    "IRatValid":("ND0382","7e9987ee1f29f5b95b8e6fbcd6c7a859b9ded7cea9956126576fef99d76858f2"),
    "IRatLe":("ND0444","4f2c5a223cacf41df91ce383d1d5c5e498d6ed0602375998eb52a1104e3bdced"),
}


class DyadicSqrt2IntervalsError(ValueError):
    """Changed exact interval endpoints, denominator validity or source."""


def definition_registry():
    from peano_lab.library.proof_bundle import encode_formula
    registry=dict(dyadic_registry());rational=rational_registry()
    for name,(identifier,digest) in RATIONAL_DEFINITION_PINS.items():
        d=rational[name]
        if (d.stable_id!=identifier or json_hash(encode_formula(d.template_formula))!=digest
                or name in registry or identifier in {x.stable_id for x in registry.values()}
                or not set(d.conceptual_dependencies)<=registry.keys()):
            raise DyadicSqrt2IntervalsError("valid rational order identity or dependency changed")
        registry[name]=d
    return MappingProxyType(registry)


def frozen_dyadic_sqrt2_intervals_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=2 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise DyadicSqrt2IntervalsError("SQ007 exact valid nested-interval target changed")
    return target


def source_contract():
    return dict(code="SQ007",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,both_supplied_computations_preserved=True,all_rational_denominators_proved_nonzero=True,
        valid_lower_endpoint_nondecreasing=True,valid_upper_endpoint_nonincreasing=True,
        zero_precision_and_increment_allowed=True,new_induction_needed=False,
        reused_definition_ids=["PD0020","PD0051","ND0446","ND0382","ND0444"],new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        real_square_root_interpretation=False,analytic_limit_claim=False,
        closes_IR014=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def dyadic_sqrt2_intervals_source_pins():
    result=dyadic_sqrt2_refinement_source_pins()
    expected={"scripts/sqrt2_power_dyadic_sqrt2_refinement.py":"b80d4d88eac57df557fa5acf7cd4d3ec1eedeaf381387d43ca53192659ad3a97",
        "scripts/sqrt2_power_rational_tail_majorant.py":"9dc0903202c1c4922011503b997a6ad2556a8d59c8750f0a028b50da038a1776",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_dyadic_sqrt2_intervals.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise DyadicSqrt2IntervalsError("dyadic interval source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _orders(s,registry):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        d,q,lo,hi,e=t.terms(("d","q","s","t","e"));de=Mul(d,e)
        lower=apply(specialize(t,"mul_right_mono",Mul(lo,e),hi,d),t.hyp("lower"))
        lower=_subst(t,registry,"Le(slot,t*d)",_multiplicative_equal(t,Mul(Mul(lo,e),d),Mul(lo,de)),lower)
        lower=_subst(t,registry,"Le(s*slot,t*d)",EqSym(t.hyp("product")),lower)
        lower=apply(specialize(t,"positive_order",lo,hi,d,q),t.hyp("d_nonzero"),t.hyp("q_nonzero"),lower)
        upper=apply(specialize(t,"mul_right_mono",Succ(hi),Mul(Succ(lo),e),d),t.hyp("upper"))
        upper=_subst(t,registry,"Le((S t)*d,slot)",
            _multiplicative_equal(t,Mul(Mul(Succ(lo),e),d),Mul(Succ(lo),de)),upper)
        upper=_subst(t,registry,"Le((S t)*d,(S s)*slot)",EqSym(t.hyp("product")),upper)
        upper=apply(specialize(t,"positive_order",Succ(hi),Succ(lo),q,d),t.hyp("q_nonzero"),t.hyp("d_nonzero"),upper)
        return conjunction(lower,upper)
    return introduce(s,("d","q","s","t","e"),("d_nonzero","q_nonzero","product","lower","upper"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL
    from peano_lab.kernel.terms import Add,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish(t):
        k,l,d,q=t.terms(("k","l","d","q"));data=t.hyp("refined")
        nz=apply(specialize(t,"power_nonzero",two),specialize(t,"succ_ne_zero",one))
        dnz=apply(instantiate(nz,k,d),AndElimL(t.hyp("coarse")))
        qnz=apply(instantiate(nz,Add(k,l),q),AndElimL(t.hyp("fine")))
        return apply(specialize(t,"orders",*t.terms(("d","q","s","t","e"))),
            dnz,qnz,field(data,2,5),field(data,3,5),field(data,4,5))
    return introduce(s,PARAMETERS,("coarse","fine"),lambda t:
        eliminate(t,apply(specialize(t,"refinement",*t.terms(PARAMETERS)),t.hyp("coarse"),t.hyp("fine")),("e",),"refined",finish))


def prove_dyadic_sqrt2_intervals(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="SQ007",target=frozen_dyadic_sqrt2_intervals_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"orders":lambda s:_orders(s,registry),"SQ007":_root},
        pins=dyadic_sqrt2_intervals_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
