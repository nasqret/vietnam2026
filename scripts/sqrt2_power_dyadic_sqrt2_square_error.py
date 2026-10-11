"""SQ009: supplied dyadic computations have positive roots and square error.

For the actual d=2^k and floor root s of 2*d^2, prove d<=s<2*d, both
values nonzero, and s^2<=2*d^2<=s^2+4*d. No limit or real identity is an axiom.
"""
from hashlib import sha256

from sqrt2_power_dyadic_sqrt2 import (
    ROOT,Scope,introduce,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,dyadic_sqrt2_source_pins,SCALED_ARCHIVE,RATIONAL_TAIL_ARCHIVE,_and,
)
from sqrt2_power_scaled_sqrt2 import HELPER_SOURCES as SCALED_HELPERS,COMPARISON_SOURCE,BOUND_ARCHIVE
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-dyadic-sqrt2-square-error-v1"
PARTS=("~d=0","~s=0","Le(d,s)","Lt(s,2*d)","Le(s*s,2*(d*d))","Le(2*(d*d),s*s+2*(2*d))")
NAMED_SOURCE="forall k d s. DyadicSqrt2(k,d,s) -> "+_and(PARTS)
TARGET_SHA256="c5d6445cccb9460719eff249437f8849968eaa22bcc68dc2d5615589e7873a0c"
HELPER_SOURCES={
    "floor_residual":"forall n s. FloorSqrt(n,s) -> Le(s*s,n) /\\ Le(n,s*s+(s+s))",
    "double_bound":"forall s d. Le(s,2*d) -> Le(s+s,2*(2*d))",
}
HELPER_TARGET_SHA256={"floor_residual":"ec74c86893629990988b39e28d15af3c39c63fc12fd1f18eabc0cf93f5c05cb4",
    "double_bound":"8e1b2ba2ddcc430cb29ecfea5208976088591a4fd6ab2d0ca97d60131d1e938e"}
ARCHIVES=(SCALED_ARCHIVE,RATIONAL_TAIL_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "arithmetic":SCALED_HELPERS["arithmetic"],"le_nonzero":SCALED_HELPERS["le_nonzero"],
    "comparison":COMPARISON_SOURCE,"power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0","le_self_succ":"forall a. Le(a,S a)",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
    "add_right_mono":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b","one_mul":"forall a. 1*a=a",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(arithmetic="SQ003",le_nonzero="SQ003",comparison="SQ003",le_self_succ="SQ003",power_nonzero="CV075",succ_ne_zero="CV075")
HELPER_DEPENDENCIES={
    "floor_residual":("mul_succ_left","add_assoc","le_of_succ_le_succ"),
    "double_bound":("add_left_mono","add_right_mono","le_trans","mul_succ_left","one_mul"),
    "SQ009":("arithmetic","comparison","le_nonzero","power_nonzero","succ_ne_zero",
        "le_self_succ","le_trans","floor_residual","double_bound","add_left_mono"),
}


class DyadicSqrt2SquareError(ValueError):
    """Changed actual computation, positivity or quantitative square residual."""


def frozen_dyadic_sqrt2_square_error_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=3 or len(premises)!=1 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise DyadicSqrt2SquareError("SQ009 exact supplied square-error target changed")
    return target


def source_contract():
    return dict(code="SQ009",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,supplied_actual_computation_preserved=True,denominator_and_root_nonzero_proved=True,
        integer_root_bounds="d<=s<2*d",integer_square_error="s*s<=2*d*d<=s*s+4*d",
        rational_error_reading="0<=2-(s/d)^2<=4/d",zero_precision_allowed=True,new_induction_needed=False,
        reused_definition_ids=["PD0020","PD0051","ND0446"],new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        real_square_root_identity_claim=False,analytic_limit_claim=False,
        closes_IR015=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def dyadic_sqrt2_square_error_source_pins():
    result=dyadic_sqrt2_source_pins()
    expected={"scripts/sqrt2_power_dyadic_sqrt2.py":"9c498535a2397cc43911427ae9cdd7e35a46b26c966e85aac294ba871e3e07dc",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_dyadic_sqrt2_square_error.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise DyadicSqrt2SquareError("dyadic square-error source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _floor_residual(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongS,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ
    def finish(t):
        n,root=t.terms(("n","s"));square=Mul(root,root);end=Add(square,Add(root,root))
        expansion=_chain(instantiate(Axiom("PA6"),Succ(root),root),
            CongAdd(specialize(t,"mul_succ_left",root,root),EqRefl(Succ(root))),
            instantiate(Axiom("PA4"),Add(square,root),root),CongS(specialize(t,"add_assoc",square,root,root)))
        upper=_subst(t,registry,"Le(S n,slot)",expansion,AndElimR(t.hyp("floor")))
        upper=apply(specialize(t,"le_of_succ_le_succ",n,end),upper)
        return conjunction(AndElimL(t.hyp("floor")),upper)
    return introduce(s,("n","s"),("floor",),finish)


def _double_bound(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish(t):
        root,d=t.terms(("s","d"));dd=Mul(two,d)
        lo=apply(specialize(t,"add_right_mono",root,dd,root),t.hyp("bound"))
        hi=apply(specialize(t,"add_left_mono",root,dd,dd),t.hyp("bound"))
        bound=apply(specialize(t,"le_trans",Add(root,root),Add(dd,root),Add(dd,dd)),lo,hi)
        double=_chain(specialize(t,"mul_succ_left",one,dd),CongAdd(specialize(t,"one_mul",dd),EqRefl(dd)))
        return _subst(t,registry,"Le(s+s,slot)",EqSym(double),bound)
    return introduce(s,("s","d"),("bound",),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish(t):
        k,d,root=t.terms(("k","d","s"));n=Mul(two,Mul(d,d));square=Mul(root,root)
        nonzero=apply(specialize(t,"power_nonzero",two),specialize(t,"succ_ne_zero",one))
        dnz=apply(instantiate(nonzero,k,d),AndElimL(t.hyp("input")))
        arithmetic=apply(specialize(t,"arithmetic",d),dnz);floor=AndElimR(t.hyp("input"))
        bounds=apply(specialize(t,"comparison",n,root,d,Mul(two,d)),floor,AndElimL(arithmetic),AndElimR(arithmetic))
        snz=apply(specialize(t,"le_nonzero",d,root),dnz,AndElimL(bounds))
        upper=apply(specialize(t,"le_trans",root,Succ(root),Mul(two,d)),specialize(t,"le_self_succ",root),AndElimR(bounds))
        doubled=apply(specialize(t,"double_bound",root,d),upper)
        lifted=apply(specialize(t,"add_left_mono",Add(root,root),Mul(two,Mul(two,d)),square),doubled)
        residual=apply(specialize(t,"floor_residual",n,root),floor)
        error=apply(specialize(t,"le_trans",n,Add(square,Add(root,root)),Add(square,Mul(two,Mul(two,d)))),AndElimR(residual),lifted)
        return conjunction(dnz,snz,AndElimL(bounds),AndElimR(bounds),AndElimL(residual),error)
    return introduce(s,("k","d","s"),("input",),finish)


def prove_dyadic_sqrt2_square_error(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="SQ009",target=frozen_dyadic_sqrt2_square_error_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"floor_residual":lambda s:_floor_residual(s,registry),"double_bound":lambda s:_double_bound(s,registry),"SQ009":lambda s:_root(s,registry)},
        pins=dyadic_sqrt2_square_error_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
