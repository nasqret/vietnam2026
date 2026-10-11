"""CV098: finite exponential continuity across independent rational scales.

Construct two actual scaled tables, align their common argument denominator
and head by ordinary equality transport, and apply CV096 to their actual sums.
The natural inequalities allow zero initial scales; rational validity is not
asserted here. No analytic accuracy is placed inside a definition.
"""
from hashlib import sha256

from sqrt2_power_exp_sum_continuity import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,exp_sum_continuity_source_pins,
    NAMED_SOURCE as CONTINUITY_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_rescaling import NAMED_SOURCE as RESCALING_SOURCE,exp_rescaling_source_pins
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-cross-continuity-v1"
A,B,U,V=("ab","ac"),("bb","bc"),("ub","uc"),("vb","vc")
FIXED=("d","e","x","y","g","N")
PARAMETERS=FIXED+A+B+("a0","b0","s","t")
GUARDS=("~d=0","~e=0","d*y=e*x+g","Le(y,2*e)")
PREMISES=GUARDS+("NatScaledExpRecurrence(d,x,ab,ac,N)","NatScaledExpRecurrence(e,y,bb,bc,N)",
    "BetaAt(ab,ac,0,a0)","BetaAt(bb,bc,0,b0)","Sum(ab,ac,S N,s)","Sum(bb,bc,S N,t)")
CONCLUSION="Le(b0*s,a0*t) /\\ Le((d*e)*(a0*t),(d*e)*(b0*s)+9*(g*(a0*b0)))"
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> "+CONCLUSION
TARGET_SHA256="cd70bc49ad3f8d993f61ab9ed4f3acc069f1cd0aac88b3f00bfd88e97d93da9c"
ALIGNED_PARAMETERS=FIXED+U+V+("a0","b0","u","v")
ALIGNED_PREMISES=GUARDS+("NatScaledExpRecurrence(d*e,e*x,ub,uc,N)","NatScaledExpRecurrence(e*d,d*y,vb,vc,N)",
    "BetaAt(ub,uc,0,b0*a0)","BetaAt(vb,vc,0,a0*b0)","Sum(ub,uc,S N,u)","Sum(vb,vc,S N,v)")
HELPER_SOURCES={
    "argument_bound":"forall d e y. Le(y,2*e) -> Le(d*y,2*(d*e))",
    "aligned":"forall "+" ".join(ALIGNED_PARAMETERS)+". "+" -> ".join(ALIGNED_PREMISES)+" -> Le(u,v) /\\ Le((d*e)*v,(d*e)*u+9*(g*(a0*b0)))",
}
HELPER_TARGET_SHA256={
    "argument_bound":"3a36a82e7f6ac6e89b3672b5af9b1b00152fef1a2a8d6bf5d83d1e6b45967fca",
    "aligned":"8e404105a09da5a5eb4635c5b8ba931ad44627923a2b685624068cdbbba1d756",
}
CONTINUITY_ARCHIVE=dict(case="CV096",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-sum-continuity-v1/generation-process.json.gz",
    bytes=39509,sha256="e75baeb07057604a6bf54d2d57587c098f40bdae035b7d2fc3f3066c67d9c253",
    raw_bytes=674168,raw_sha256="8a3abf4e8e0ede5425659037885f9080defd60ac81e16bf9adc0ee4fa14a3e6e",
    bundle_bytes=384106,bundle_sha256="ef000bac2887811708eb6851cb4a561d71102c44712840a7654723cc4543a689",
    nodes=147,root=146,target_ast_sha256="bcfe5d4711bda1d8f1b19f812c40c8a8cb6d8c2bf10fdb247fa69a32b08715d2")
RESCALING_ARCHIVE=dict(case="CV097",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-rescaling-v1/generation-process.json.gz",
    bytes=29708,sha256="dab59f1230eadfa47e7240b816d0adbdc51833b8a970355b642db17faadafd2a",
    raw_bytes=403637,raw_sha256="b75d30c804cb930a4561afba214641ab91b9c41f7fe213bf51752dccccebca68",
    bundle_bytes=215669,bundle_sha256="571d69eb382e46b1bd32c0d1a0b8ef59d2b3ca43a214e92a0e9ddcacd0191b0a",
    nodes=114,root=113,target_ast_sha256="1366d756cc52f3aeda1363ed3188f534bc5489ed2977f09a101be2c92e875243")
ARCHIVES=(CONTINUITY_ARCHIVE,RESCALING_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "continuity":CONTINUITY_SOURCE,"rescaling":RESCALING_SOURCE,
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~a*b=0",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(continuity="CV096",rescaling="CV097")
HELPER_DEPENDENCIES={
    "argument_bound":("mul_left_mono","mul_assoc","mul_comm"),
    "aligned":("continuity","argument_bound","mul_ne_zero","mul_comm"),
    "CV098":("rescaling","aligned"),
}


class ExpCrossContinuityError(ValueError):
    """Changed cross-argument gap, supplied sums, or independent normalizations."""


def frozen_exp_cross_continuity_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=14 or len(premises)!=10 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpCrossContinuityError("CV098 exact independent-scale finite continuity changed")
    return target


def source_contract():
    return dict(code="CV098",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=10,two_supplied_recurrences_heads_and_sums_preserved=True,
        independent_denominators_and_heads_allowed=True,actual_common_scale_tables_constructed=True,
        nonzero_argument_denominators_required=True,argument_gap="d*y=e*x+g",argument_bound="y<=2*e",
        common_denominator="d*e",common_initial_scale="a0*b0",monotonicity="b0*s<=a0*t",
        finite_difference="(d*e)*(a0*t)<=(d*e)*(b0*s)+9*(g*(a0*b0))",
        zero_arguments_gap_heads_and_degree_allowed=True,new_induction_needed=False,
        code_number_equality_claimed=False,rational_division_claimed=False,analytic_limit_claim=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def exp_cross_continuity_source_pins():
    result=exp_sum_continuity_source_pins()
    for name,pin in exp_rescaling_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpCrossContinuityError("independent continuity source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_sum_continuity.py":"92e7667198420bf1e508d1aafd59e29c7875a163dea8ab3e012e224b1c614f9e",
        "scripts/sqrt2_power_exp_rescaling.py":"bc2721198e4ce3580b7965152fe3b6e02b41336dde024eb543e64069844d6947",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_cross_continuity.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpCrossContinuityError("independent continuity source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _argument_bound(s,registry):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        d,e,y=t.terms(("d","e","y"));two=Succ(Succ(Zero()))
        scaled=apply(specialize(t,"mul_left_mono",y,Mul(two,e),d),t.hyp("bound"))
        normalized=_multiplicative_equal(t,Mul(d,Mul(two,e)),Mul(two,Mul(d,e)))
        return _subst(t,registry,"Le(d*y,slot)",normalized,scaled)
    return introduce(s,("d","e","y"),("bound",),finish)


def _aligned(s,registry):
    from peano_lab.kernel.terms import Mul
    def finish(t):
        d,e,x,y,g,N,a0,b0,u,v=t.terms(FIXED+("a0","b0","u","v"))
        nonzero=apply(specialize(t,"mul_ne_zero",d,e),t.hyp("nonzero_d"),t.hyp("nonzero_e"))
        recurrence=_subst(t,registry,"NatScaledExpRecurrence(slot,d*y,vb,vc,N)",
            specialize(t,"mul_comm",e,d),t.hyp("recurrence_b"))
        head=_subst(t,registry,"BetaAt(ub,uc,0,slot)",specialize(t,"mul_comm",b0,a0),t.hyp("head_a"))
        bound=apply(specialize(t,"argument_bound",d,e,y),t.hyp("bound"))
        return apply(specialize(t,"continuity",Mul(d,e),Mul(e,x),Mul(d,y),g,N,*t.terms(U+V),Mul(a0,b0),u,v),
            nonzero,t.hyp("gap"),t.hyp("recurrence_a"),recurrence,head,t.hyp("head_b"),bound,t.hyp("sum_a"),t.hyp("sum_b"))
    return introduce(s,ALIGNED_PARAMETERS,("nonzero_d","nonzero_e","gap","bound","recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b"),finish)


def _root(s,registry):
    def finish(t):
        a,b=t.hyp("scaled_a"),t.hyp("scaled_b")
        result=apply(specialize(t,"aligned",*t.terms(ALIGNED_PARAMETERS)),
            *(t.hyp(label) for label in ("nonzero_d","nonzero_e","gap","bound")),
            field(a,1,5),field(b,1,5),field(a,2,5),field(b,2,5),field(a,3,5),field(b,3,5))
        result=_subst(t,registry,"Le(slot,v) /\\ Le((d*e)*v,(d*e)*slot+9*(g*(a0*b0)))",field(a,4,5),result)
        return _subst(t,registry,"Le(b0*s,slot) /\\ Le((d*e)*slot,(d*e)*(b0*s)+9*(g*(a0*b0)))",field(b,4,5),result)
    def second(t):
        scaled=apply(specialize(t,"rescaling",*t.terms(("e","y","d","a0","N")+B+("b0","t"))),
            t.hyp("recurrence_b"),t.hyp("head_b"),t.hyp("sum_b"))
        return eliminate(t,scaled,V+("v",),"scaled_b",finish)
    def first(t):
        scaled=apply(specialize(t,"rescaling",*t.terms(("d","x","e","b0","N")+A+("a0","s"))),
            t.hyp("recurrence_a"),t.hyp("head_a"),t.hyp("sum_a"))
        return eliminate(t,scaled,U+("u",),"scaled_a",second)
    return introduce(s,PARAMETERS,("nonzero_d","nonzero_e","gap","bound","recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b"),first)


def prove_exp_cross_continuity(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV098",target=frozen_exp_cross_continuity_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"argument_bound":lambda s:_argument_bound(s,registry),"aligned":lambda s:_aligned(s,registry),"CV098":lambda s:_root(s,registry)},
        pins=exp_cross_continuity_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
