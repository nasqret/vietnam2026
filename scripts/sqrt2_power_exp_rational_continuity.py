"""CV099: valid rational continuity for two supplied finite exponential sums.

With positive argument denominators and initial scales, convert CV098's
natural cross-products into s/a0 <= t/b0 <= s/a0 + 9*g/(d*e).
The output preserves both actual input computations; no limit is asserted.
"""
from hashlib import sha256

from sqrt2_power_exp_cross_continuity import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,exp_cross_continuity_source_pins,PARAMETERS,
    NAMED_SOURCE as CROSS_SOURCE,PREMISES as CROSS_PREMISES,BOUND_ARCHIVE,
)
from sqrt2_power_rational_tail_majorant import (
    definition_registry,rational_tail_majorant_source_pins,HELPER_SOURCES as RATIONAL_HELPERS,
)
from sqrt2_power_composition_tail_bound import RATIONAL_TAIL_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-rational-continuity-v1"
PREMISES=CROSS_PREMISES[:2]+("~a0=0","~b0=0")+CROSS_PREMISES[2:]
LOWER="IRatLe(s,0,a0,t,0,b0)"
UPPER="IRatLe(t,0,b0,(d*e)*s+(9*g)*a0,0,(d*e)*a0)"
CONCLUSION=LOWER+" /\\ "+UPPER
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> "+CONCLUSION
TARGET_SHA256="82b80b04322470f648dfee85b1aab63cea1636dce56258cd64822934f90d7e32"
HELPER_SOURCES={"orders":"forall d e g a0 b0 s t. ~d=0 -> ~e=0 -> ~a0=0 -> ~b0=0 -> Le(b0*s,a0*t) -> Le((d*e)*(a0*t),(d*e)*(b0*s)+9*(g*(a0*b0))) -> "+CONCLUSION}
HELPER_TARGET_SHA256={"orders":"96edde7ef36cec3b622b0f820e1803d781d6bcefc2e0662ab18b7e1994c1664c"}
CROSS_ARCHIVE=dict(case="CV098",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-cross-continuity-v1/generation-process.json.gz",
    bytes=41832,sha256="e99a84d84b18f3a03e441cf9f53377ad72f291af183d407136fed3387bc1bf92",
    raw_bytes=770001,raw_sha256="cf75130bb1c25e67fcd5d19190231c5bd54b296c0599532086c47feaef0101aa",
    bundle_bytes=445508,bundle_sha256="e4d094f2bd99f93d7c2951a5a03e735e0d7ba193e0b6c117d1385ed11a50bc8d",
    nodes=156,root=155,target_ast_sha256="cd70bc49ad3f8d993f61ab9ed4f3acc069f1cd0aac88b3f00bfd88e97d93da9c")
ARCHIVES=(CROSS_ARCHIVE,RATIONAL_TAIL_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "cross_continuity":CROSS_SOURCE,"positive_order":RATIONAL_HELPERS["positive_order"],
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "add_mul":"forall a b c. (a+b)*c=a*c+b*c",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(cross_continuity="CV098",positive_order="CV075")
HELPER_DEPENDENCIES={
    "orders":("positive_order","mul_ne_zero","mul_assoc","mul_comm","add_mul"),
    "CV099":("cross_continuity","orders"),
}


class ExpRationalContinuityError(ValueError):
    """Changed actual rational normalizations, nonzero guards or error bound."""


def frozen_exp_rational_continuity_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=14 or len(premises)!=12 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRationalContinuityError("CV099 exact valid rational finite continuity changed")
    return target


def source_contract():
    return dict(code="CV099",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=12,two_supplied_recurrences_heads_and_sums_preserved=True,
        independent_argument_denominators_and_initial_scales=True,
        all_rational_denominators_proved_nonzero=True,initial_scales_required_nonzero=True,
        argument_gap="d*y=e*x+g",argument_bound="y<=2*e",
        rational_bounds="s/a0<=t/b0<=s/a0+9*g/(d*e)",finite_error="9*g/(d*e)",
        zero_arguments_gap_and_degree_allowed=True,new_induction_needed=False,
        code_number_equality_claimed=False,analytic_limit_claim=False,
        reused_definition_ids=["ND0382","ND0444"],new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def exp_rational_continuity_source_pins():
    result=exp_cross_continuity_source_pins()
    for name,pin in rational_tail_majorant_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpRationalContinuityError("rational continuity source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_cross_continuity.py":"df8ebc21517107b814a6f1e55903bb412d37a5b09917eeef6a47930b557b0bcd",
        "scripts/sqrt2_power_rational_tail_majorant.py":"9dc0903202c1c4922011503b997a6ad2556a8d59c8750f0a028b50da038a1776",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_rational_continuity.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRationalContinuityError("rational continuity source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _orders(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    nine=Zero()
    for _ in range(9):
        nine=Succ(nine)
    def finish(t):
        d,e,g,a0,b0,z,out=t.terms(("d","e","g","a0","b0","s","t"))
        de=Mul(d,e);den=Mul(de,a0);ng=Mul(nine,g);error=Mul(ng,a0);num=Add(Mul(de,z),error)
        den_nz=apply(specialize(t,"mul_ne_zero",de,a0),
            apply(specialize(t,"mul_ne_zero",d,e),t.hyp("d_nonzero"),t.hyp("e_nonzero")),t.hyp("a_nonzero"))
        lower=_subst(t,registry,"Le(slot,a0*t)",specialize(t,"mul_comm",b0,z),t.hyp("lower"))
        lower=_subst(t,registry,"Le(s*b0,slot)",specialize(t,"mul_comm",a0,out),lower)
        lower=apply(specialize(t,"positive_order",z,out,a0,b0),t.hyp("a_nonzero"),t.hyp("b_nonzero"),lower)
        upper=_subst(t,registry,"Le(slot,(d*e)*(b0*s)+9*(g*(a0*b0)))",
            _multiplicative_equal(t,Mul(de,Mul(a0,out)),Mul(out,den)),t.hyp("upper"))
        right=_chain(CongAdd(
            _multiplicative_equal(t,Mul(de,Mul(b0,z)),Mul(Mul(de,z),b0)),
            _multiplicative_equal(t,Mul(nine,Mul(g,Mul(a0,b0))),Mul(error,b0))),
            EqSym(specialize(t,"add_mul",Mul(de,z),error,b0)))
        upper=_subst(t,registry,"Le(t*((d*e)*a0),slot)",right,upper)
        upper=apply(specialize(t,"positive_order",out,num,b0,den),t.hyp("b_nonzero"),den_nz,upper)
        return conjunction(lower,upper)
    return introduce(s,("d","e","g","a0","b0","s","t"),("d_nonzero","e_nonzero","a_nonzero","b_nonzero","lower","upper"),finish)


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def finish(t):
        bounds=apply(specialize(t,"cross_continuity",*t.terms(PARAMETERS)),
            *(t.hyp(label) for label in ("d_nonzero","e_nonzero","gap","bound","recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b")))
        return apply(specialize(t,"orders",*t.terms(("d","e","g","a0","b0","s","t"))),
            *(t.hyp(label) for label in ("d_nonzero","e_nonzero","a_nonzero","b_nonzero")),AndElimL(bounds),AndElimR(bounds))
    return introduce(s,PARAMETERS,("d_nonzero","e_nonzero","a_nonzero","b_nonzero","gap","bound","recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b"),finish)


def prove_exp_rational_continuity(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV099",target=frozen_exp_rational_continuity_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"orders":lambda s:_orders(s,registry),"CV099":_root},
        pins=exp_rational_continuity_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
