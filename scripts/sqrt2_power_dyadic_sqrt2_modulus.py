"""SQ008: an explicit finite dyadic Cauchy modulus, in natural arithmetic.

For actual computations s/d at k and t/q at k+l, prove both denominators
nonzero and s*q<=t*d<=s*q+q. Thus the rational increase is at most 1/d=2^-k.
The latter reading uses ordinary rational arithmetic; no real limit is assumed.
"""
from hashlib import sha256

from sqrt2_power_dyadic_sqrt2_intervals import (
    ROOT,Scope,introduce,apply,specialize,conjunction,canonical,json_hash,field,
    definition_registry,dyadic_sqrt2_intervals_source_pins,PARAMETERS,COMPOSITION_ARCHIVE,
    NAMED_SOURCE as INTERVAL_SOURCE,
)
from sqrt2_power_dyadic_sqrt2 import _and
from sqrt2_power_floor_sqrt_comparison import FLOOR_ARCHIVE
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-dyadic-sqrt2-modulus-v1"
PARTS=("~d=0","~q=0","Le(s*q,t*d)","Le(t*d,s*q+q)")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". DyadicSqrt2(k,d,s) -> DyadicSqrt2(k+l,q,t) -> "+_and(PARTS)
TARGET_SHA256="a431f58073293b4d6efa8d8122c194a4bcbaa3f8ad022a73b9f8d2a0b8182910"
HELPER_SOURCES={"positive_natural":"forall u v a b. IRatLe(u,0,a,v,0,b) -> Le(u*b,v*a)"}
HELPER_TARGET_SHA256={"positive_natural":"c772137606e8ba3158ab66657a64b25377bf3cad2d6eea9a068d326e4020c8f5"}
INTERVAL_ARCHIVE=dict(case="SQ007",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-dyadic-sqrt2-intervals-v1/generation-process.json.gz",
    bytes=25556,sha256="fdee819a3cc441e480c0f5e02fa8968deeca651ab88bb57937e20b2e2f82db98",
    raw_bytes=467548,raw_sha256="776109312926986d29c1b3de93c64565fe48ecb7c1927a8f7ad0288bc1953b4b",
    bundle_bytes=281610,bundle_sha256="662b208170553daf44e743701543229b6fc24f7f1542c2fd68db47c81d1001f3",
    nodes=134,root=133,target_ast_sha256="13d665c846b9974b8406b7dbafd3d385a28847ea32ce289f7bf5caf79f2d8a32")
ARCHIVES=(INTERVAL_ARCHIVE,COMPOSITION_ARCHIVE,FLOOR_ARCHIVE)
ENDPOINT_SOURCES={
    "intervals":INTERVAL_SOURCE,"zero_add":"forall a. 0+a=a","zero_mul":"forall a. 0*a=0",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "le_self_succ":"forall a. Le(a,S a)",
}
ENDPOINT_OWNERS={name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(intervals="SQ007",le_self_succ="SQ001")
HELPER_DEPENDENCIES={
    "positive_natural":("zero_add","zero_mul"),
    "SQ008":("intervals","positive_natural","mul_succ_left","mul_right_mono","le_trans","le_self_succ"),
}


class DyadicSqrt2ModulusError(ValueError):
    """Changed exact denominator guards, one-unit numerator error or source."""


def frozen_dyadic_sqrt2_modulus_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=2 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise DyadicSqrt2ModulusError("SQ008 exact finite dyadic modulus changed")
    return target


def source_contract():
    return dict(code="SQ008",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,both_supplied_actual_computations_preserved=True,denominator_nonzero_conclusions=True,
        exact_natural_bounds="s*q<=t*d<=s*q+q",rational_error_reading="0<=t/q-s/d<=1/d=2^(-k)",
        zero_precision_and_increment_allowed=True,ordered_finite_precision_modulus=True,
        new_induction_needed=False,reused_definition_ids=["PD0020","PD0051","ND0446","ND0382","ND0444"],
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",real_square_root_interpretation=False,
        analytic_limit_claim=False,closes_IR014=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def dyadic_sqrt2_modulus_source_pins():
    result=dyadic_sqrt2_intervals_source_pins()
    expected={"scripts/sqrt2_power_dyadic_sqrt2_intervals.py":"c9e03353b2bd23c09f826dd9fd87e8a0fa52c6d0157ab8007305e4a7a2b7241e",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_dyadic_sqrt2_modulus.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise DyadicSqrt2ModulusError("dyadic modulus source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _positive_natural(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl
    from peano_lab.kernel.terms import Mul
    def finish(t):
        u,v,a,b=t.terms(("u","v","a","b"));ub=Mul(u,b);va=Mul(v,a)
        left=_chain(CongAdd(EqRefl(ub),specialize(t,"zero_mul",a)),instantiate(Axiom("PA3"),ub))
        right=_chain(CongAdd(specialize(t,"zero_mul",b),EqRefl(va)),specialize(t,"zero_add",va))
        bound=_subst(t,registry,"Le(slot,0*b+v*a)",left,field(t.hyp("order"),2,3))
        return _subst(t,registry,"Le(u*b,slot)",right,bound)
    return introduce(s,("u","v","a","b"),("order",),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        d,root,q,out=t.terms(("d","s","q","t"))
        intervals=apply(specialize(t,"intervals",*t.terms(PARAMETERS)),t.hyp("coarse"),t.hyp("fine"))
        rational_lower=AndElimL(intervals)
        lower=apply(specialize(t,"positive_natural",root,out,d,q),rational_lower)
        upper=apply(specialize(t,"positive_natural",Succ(out),Succ(root),q,d),AndElimR(intervals))
        step=apply(specialize(t,"mul_right_mono",out,Succ(out),d),specialize(t,"le_self_succ",out))
        upper=apply(specialize(t,"le_trans",Mul(out,d),Mul(Succ(out),d),Mul(Succ(root),q)),step,upper)
        upper=_subst(t,registry,"Le(t*d,slot)",specialize(t,"mul_succ_left",root,q),upper)
        return conjunction(AndElimL(rational_lower),AndElimL(AndElimR(rational_lower)),lower,upper)
    return introduce(s,PARAMETERS,("coarse","fine"),finish)


def prove_dyadic_sqrt2_modulus(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="SQ008",target=frozen_dyadic_sqrt2_modulus_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"positive_natural":lambda s:_positive_natural(s,registry),"SQ008":lambda s:_root(s,registry)},
        pins=dyadic_sqrt2_modulus_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
