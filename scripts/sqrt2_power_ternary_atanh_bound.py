"""CV086: a supplied finite atanh polynomial at one third is at most one.

Prove the stronger natural bound 3*y+3*d <= d*p for the caller's actual
Horner value y and p=3^(k+1). A zero-headed 2*d-bounded coefficient table
has y+d <= d*3^k. No replacement code, division, or analytic limit is used.
"""
from hashlib import sha256

from sqrt2_power_atanh_majorant import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,atanh_majorant_source_pins,
    HELPER_SOURCES as ATANH_HELPERS,
)
from sqrt2_power_bounded_horner import ENDPOINT_SOURCES as BOUNDED_ENDPOINTS
from sqrt2_power_composition_majorant import INNER_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-ternary-atanh-bound-v1"
A,H = ("ab","ac"),("hb","hc")
PARAMETERS = ("d",)+A+("k","y","p")
FIXED = A+("D","N")+H
NAMED_SOURCE = "forall d ab ac k y p. NatAtanhPrefix(d,ab,ac,S k) -> NatHornerValue(ab,ac,3,S k,y) -> Pow(3,S k,p) -> Le(3*y+3*d,d*p)"
TARGET_SHA256 = "7a0be8c3f072412b13318d7e4c22a5a86af4e3c3a1567ad788f60fc72b41a49a"
ALL_PREFIXES = "forall k y p. Le(S k,N) -> BetaAt(hb,hc,S k,y) -> Pow(3,k,p) -> Le(y+D,D*p)"
HELPER_SOURCES = {
    "step_bound":"forall D h c q y p. Le(h+D,D*q) -> Le(c,2*D) -> y=3*h+c -> p=q*3 -> Le(y+D,D*p)",
    "all_prefixes":"forall "+" ".join(FIXED)+". BetaAt(ab,ac,0,0) -> NatBoundedPrefix(ab,ac,2*D,N) -> NatScaledHornerTrace(ab,ac,3,N,hb,hc) -> "+ALL_PREFIXES,
}
HELPER_TARGET_SHA256 = {
    "step_bound":"02f8775d9480d7a576db3f6082f8536b01c00f1804ea991833881335625331a9",
    "all_prefixes":"10cc4592db152a8258400f829855bba4bd69a05762d86d5856459e59d5a588d4",
}
ARCHIVES = (INNER_ARCHIVE,)
ENDPOINT_SOURCES = {name:BOUNDED_ENDPOINTS[name] for name in (
    "beta_exists","le_refl","le_succ","le_trans","power_zero","power_step","step_value",
    "zero_add","mul_comm","mul_assoc","mul_add","add_right_mono","add_left_mono","add_assoc","mul_left_mono","mul_one")}
ENDPOINT_SOURCES.update(prefix_bound=ATANH_HELPERS["prefix_bound"],prefix_head=ATANH_HELPERS["prefix_head"])
ENDPOINT_OWNERS = {name:"CV066" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {
    "step_bound":("add_right_mono","add_left_mono","mul_left_mono","le_trans","add_assoc","mul_add","mul_comm","mul_assoc"),
    "all_prefixes":("power_zero","step_value","zero_add","mul_one","le_refl","le_succ","le_trans","beta_exists","power_step","step_bound"),
    "CV086":("prefix_head","prefix_bound","power_step","all_prefixes","le_refl","mul_left_mono","mul_add","mul_comm","mul_assoc"),
}


class TernaryAtanhBoundError(ValueError):
    """Changed supplied finite input, actual power or denominator-cleared bound."""


def frozen_ternary_atanh_bound_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,_ = strip_target(target)
    if binders!=6 or len(premises)!=3 or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise TernaryAtanhBoundError("CV086 exact supplied ternary atanh bound changed")
    return target


def source_contract():
    return dict(code="CV086",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,supplied_atanh_coefficients_value_and_power_preserved=True,
        stronger_finite_bound="3*y+3*d<=d*p; p=3^(k+1)",
        general_zero_head_bounded_prefix_invariant="y+D<=D*3^k when coefficients<=2*D",
        zero_denominator_allowed_for_natural_bound=True,denominator_nonzero_claimed=False,
        no_division=True,analytic_limit_claim=False,analytic_logarithm_identity=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def ternary_atanh_bound_source_pins():
    result = atanh_majorant_source_pins()
    expected = {"scripts/sqrt2_power_atanh_majorant.py":"994b47e03f8b9021bef219df7f91270ad2d790f91d788be62d7839d9afdf419e",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_ternary_atanh_bound.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise TernaryAtanhBoundError("ternary atanh source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _step_bound(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        D,h,c,q,y,p = t.terms(("D","h","c","q","y","p"))
        two = Succ(Succ(Zero()));three = Succ(two)
        triple = _chain(specialize(t,"mul_comm",three,D),instantiate(Axiom("PA6"),D,two),
            CongAdd(specialize(t,"mul_comm",D,two),EqRefl(D)))
        bounded = apply(specialize(t,"add_right_mono",c,Mul(two,D),D),t.hyp("coefficient_bound"))
        bounded = apply(specialize(t,"add_left_mono",Add(c,D),Add(Mul(two,D),D),Mul(three,h)),bounded)
        left = _chain(CongAdd(t.hyp("next_value"),EqRefl(D)),specialize(t,"add_assoc",Mul(three,h),c,D))
        right = _chain(CongAdd(EqRefl(Mul(three,h)),EqSym(triple)),EqSym(specialize(t,"mul_add",three,h,D)))
        bounded = _subst(t,registry,"Le(slot,3*h+(2*D+D))",EqSym(left),bounded)
        bounded = _subst(t,registry,"Le(y+D,slot)",right,bounded)
        upper = apply(specialize(t,"mul_left_mono",Add(h,D),Mul(D,q),three),t.hyp("old_bound"))
        bound = apply(specialize(t,"le_trans",Add(y,D),Mul(three,Add(h,D)),Mul(three,Mul(D,q))),bounded,upper)
        final = _chain(_multiplicative_equal(t,Mul(three,Mul(D,q)),Mul(D,Mul(q,three))),CongMul(EqRefl(D),EqSym(t.hyp("next_power"))))
        return _subst(t,registry,"Le(y+D,slot)",final,bound)
    return introduce(s,("D","h","c","q","y","p"),("old_bound","coefficient_bound","next_value","next_power"),finish)


def _all_prefixes(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Succ,Zero
    three = Succ(Succ(Succ(Zero())))
    def base(t):
        D,y,p = t.terms(("D","y","p"));zero = Zero()
        step = apply(instantiate(AndElimR(t.hyp("trace")),zero),t.hyp("bound"))
        y0 = _chain(apply(specialize(t,"step_value",*t.terms(A),three,*t.terms(H),zero,zero,zero,y),
            step,AndElimL(t.hyp("trace")),t.hyp("zero_head"),t.hyp("value")),
            CongAdd(instantiate(Axiom("PA5"),three),EqRefl(zero)),specialize(t,"zero_add",zero))
        p1 = apply(specialize(t,"power_zero",three,zero,p),EqRefl(zero),t.hyp("power"))
        equal = _chain(CongAdd(y0,EqRefl(D)),specialize(t,"zero_add",D),
            EqSym(specialize(t,"mul_one",D)),CongMul(EqRefl(D),EqSym(p1)))
        return _subst(t,registry,"Le(y+D,slot)",equal,specialize(t,"le_refl",Add(y,D)))
    def successor(t):
        def chosen(u):
            k,N = u.terms(("k","N"));sk = Succ(k)
            earlier = apply(specialize(u,"le_trans",sk,Succ(sk),N),
                apply(specialize(u,"le_succ",sk,sk),specialize(u,"le_refl",sk)),u.hyp("bound"))
            old = apply(specialize(u,"IH",*u.terms(("h","q"))),earlier,u.hyp("old_value"),AndElimL(u.hyp("power_data")))
            coefficient_bound = apply(specialize(u,"coefficients",sk,u.term("c")),u.hyp("bound"),u.hyp("coefficient"))
            step = apply(instantiate(AndElimR(u.hyp("trace")),sk),u.hyp("bound"))
            next_value = apply(specialize(u,"step_value",*u.terms(A),three,*u.terms(H),sk,*u.terms(("h","c","y"))),
                step,u.hyp("old_value"),u.hyp("coefficient"),u.hyp("value"))
            return apply(specialize(u,"step_bound",*u.terms(("D","h","c","q","y","p"))),old,coefficient_bound,next_value,AndElimR(u.hyp("power_data")))
        power = apply(specialize(t,"power_step",three,t.term("k"),Succ(t.term("k")),t.term("p")),EqRefl(Succ(t.term("k"))),t.hyp("power"))
        return eliminate(t,power,("q",),"power_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H),Succ(u.term("k"))),("h",),"old_value",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(A),Succ(v.term("k"))),("c",),"coefficient",chosen)))
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.right.right.right.body
    row_params,row_hyps = ("y","p"),("bound","value","power")
    return introduce(s,FIXED,("zero_head","coefficients","trace"),lambda t:Ind(motive,introduce(t,row_params,row_hyps,base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,row_params,row_hyps,successor))))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    three = Succ(Succ(Succ(Zero())))
    def chosen(t):
        d,k,y,p,q = t.terms(("d","k","y","p","q"));N = Succ(k)
        head = apply(specialize(t,"prefix_head",*t.terms(("d",)+A+("k",))),t.hyp("prefix"))
        coefficients = apply(specialize(t,"prefix_bound",*t.terms(("d",)+A),N),t.hyp("prefix"))
        invariant = apply(specialize(t,"all_prefixes",*t.terms(A),d,N,*t.terms(H)),head,coefficients,AndElimL(t.hyp("trace_value")))
        bound = apply(instantiate(invariant,k,y,q),specialize(t,"le_refl",N),AndElimR(t.hyp("trace_value")),AndElimL(t.hyp("power_data")))
        scaled = apply(specialize(t,"mul_left_mono",Add(y,d),Mul(d,q),three),bound)
        scaled = _subst(t,registry,"Le(slot,3*(d*q))",specialize(t,"mul_add",three,y,d),scaled)
        same = _chain(_multiplicative_equal(t,Mul(three,Mul(d,q)),Mul(d,Mul(q,three))),
            CongMul(EqRefl(d),EqSym(AndElimR(t.hyp("power_data")))))
        return _subst(t,registry,"Le(3*y+3*d,slot)",same,scaled)
    return introduce(s,PARAMETERS,("prefix","value","power"),lambda t:
        eliminate(t,t.hyp("value"),H,"trace_value",lambda u:
            eliminate(u,apply(specialize(u,"power_step",three,u.term("k"),Succ(u.term("k")),u.term("p")),
                EqRefl(Succ(u.term("k"))),u.hyp("power")),("q",),"power_data",chosen)))


def prove_ternary_atanh_bound(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV086",target=frozen_ternary_atanh_bound_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"step_bound":lambda s:_step_bound(s,registry),
            "all_prefixes":lambda s:_all_prefixes(s,parse_named(HELPER_SOURCES["all_prefixes"],registry=registry),registry),
            "CV086":lambda s:_root(s,registry)},pins=ternary_atanh_bound_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
