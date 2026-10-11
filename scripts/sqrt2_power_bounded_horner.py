"""CV065: a zero-headed, bounded coefficient prefix has a finite majorant.

At base two and length k+1, construct y and p=2^k with y+D<=D*p.
The coefficient bound is a separate conservative predicate, not part of
the Horner computation graph. D=0 and k=0 are included without division.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_horner_base_comparison import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as base_registry,horner_base_comparison_source_pins,
    COMPOSITION_ARCHIVE,ENDPOINT_SOURCES as BASE_ENDPOINTS,HELPER_SOURCES as BASE_HELPERS,
)
from sqrt2_power_horner_tail_majorant import COMPARISON_ARCHIVE
from sqrt2_power_horner_splitting import ENDPOINT_SOURCES as SPLIT_ENDPOINTS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-bounded-horner-v1"
A,H = ("ab","ac"),("hb","hc")
PARAMETERS = A+("D","k")
FIXED = A+("D","N")+H
DEFINITIONS = (
    ("ND0440","NatBoundedPrefix",("ab","ac","D","N"),
     "forall i a. Lt(i,N) -> BetaAt(ab,ac,i,a) -> Le(a,D)",
     ("Lt","BetaAt","Le"),"38949a5237eb866fcc8a024279004a1b5931e9b198e3d112c070d88782f84320"),
)
ALL_PREFIXES = "forall k y p. Le(S k,N) -> BetaAt(hb,hc,S k,y) -> Pow(2,k,p) -> Le(y+D,D*p)"
NAMED_SOURCE = "forall ab ac D k. BetaAt(ab,ac,0,0) -> NatBoundedPrefix(ab,ac,D,S k) -> exists y p. NatHornerValue(ab,ac,2,S k,y) /\\ (Pow(2,k,p) /\\ Le(y+D,D*p))"
TARGET_SHA256 = "9014d749012734cecddb6aba75ab714b63794d50d28aef611ecc1a9018f2c091"
HELPER_SOURCES = {
    "step_bound":"forall D h c q y p. Le(h+D,D*q) -> Le(c,D) -> y=2*h+c -> p=q*2 -> Le(y+D,D*p)",
    "all_prefixes":"forall "+" ".join(FIXED)+". BetaAt(ab,ac,0,0) -> NatBoundedPrefix(ab,ac,D,N) -> NatScaledHornerTrace(ab,ac,2,N,hb,hc) -> "+ALL_PREFIXES,
}
HELPER_TARGET_SHA256 = {
    "step_bound":"612dfdbd90f6420d1be1a036c74079cb758b7c0c21513dfbb4bde12dff2945cb",
    "all_prefixes":"aaf4af43b31ca73c1ce2b59531d8e838d5863ebc51d921a8e4668f02da778a5f",
}
ARCHIVES = (COMPOSITION_ARCHIVE,COMPARISON_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:BASE_ENDPOINTS[name] for name in ("beta_exists","le_refl","le_succ","le_trans","power_zero","power_step","power_exists","horner_exists","step_value","zero_add","mul_comm","mul_assoc","mul_add","add_right_mono","add_left_mono")},
    "add_assoc":SPLIT_ENDPOINTS["add_assoc"],"mul_one":"forall a. a*1=a",
    "mul_left_mono":BASE_HELPERS["mul_left_mono"],
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["mul_left_mono"] = "CV063"
HELPER_DEPENDENCIES = {
    "step_bound":("add_right_mono","add_left_mono","mul_left_mono","le_trans","add_assoc","mul_add","mul_comm","mul_assoc","mul_one"),
    "all_prefixes":("power_zero","step_value","zero_add","mul_one","le_refl","le_succ","le_trans","beta_exists","power_step","step_bound"),
    "CV065":("horner_exists","beta_exists","power_exists","le_refl","all_prefixes"),
}


class BoundedHornerError(ValueError):
    """Changed explicit coefficient bound, zero head or computation data."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    result = dict(base_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids = {d["id"] for d in parent}|{d.stable_id for d in result.values()}
    names = {d["name"] for d in parent}|set(result)
    for identifier,name,params,source,deps,digest in DEFINITIONS:
        if identifier in ids or name in names or not set(deps)<=result.keys():
            raise BoundedHornerError("bounded-prefix definition collision or forward dependency")
        formula = parse_named(source,params,result)
        if json_hash(encode_formula(formula))!=digest:
            raise BoundedHornerError("bounded-prefix conservative expansion changed")
        text = pretty_formula(formula,list(params))
        d = _definition(stable_id=identifier,name=name,parameters=params,template_source=text,
            summary="Separate finite coefficient bound; no computation or analytic estimate is assumed.",
            category="irrationality_formal_series",conceptual_dependencies=deps)
        if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula:
            raise BoundedHornerError("bounded-prefix definition failed exact conservative roundtrip")
        result[name] = d;ids.add(identifier);names.add(name)
    return MappingProxyType(result)


def frozen_bounded_horner_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=4 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise BoundedHornerError("CV065 exact bounded Horner target changed")
    return target


def source_contract():
    return dict(code="CV065",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,zero_head_required=True,separate_coefficient_bound_required=True,
        actual_horner_value_and_power_constructed=True,zero_bound_allowed=True,
        length="k+1",power="2^k",inequality="y+D<=D*p",no_division=True,
        new_definition_ids=["ND0440"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def bounded_horner_source_pins():
    result = horner_base_comparison_source_pins()
    expected = {"scripts/sqrt2_power_horner_base_comparison.py":"75a1f8d6983c871186d9cc2c948b3bf9325cda92522a47791d1c4acb0ca8928c",
        "scripts/sqrt2_power_horner_tail_majorant.py":"b4a626c240b3c47d658c1d048d922736edaa1fa8710f8e5002dac05f24efe7f8",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_bounded_horner.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise BoundedHornerError("bounded Horner source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _step_bound(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        D,h,c,q,y,p = t.terms(("D","h","c","q","y","p"))
        one,two = Succ(Zero()),Succ(Succ(Zero()))
        double = _chain(specialize(t,"mul_comm",two,D),instantiate(Axiom("PA6"),D,one),CongAdd(specialize(t,"mul_one",D),EqRefl(D)))
        bounded = apply(specialize(t,"add_right_mono",c,D,D),t.hyp("coefficient_bound"))
        bounded = apply(specialize(t,"add_left_mono",Add(c,D),Add(D,D),Mul(two,h)),bounded)
        left = _chain(CongAdd(t.hyp("next_value"),EqRefl(D)),specialize(t,"add_assoc",Mul(two,h),c,D))
        right = _chain(CongAdd(EqRefl(Mul(two,h)),EqSym(double)),EqSym(specialize(t,"mul_add",two,h,D)))
        bounded = _subst(t,registry,"Le(slot,2*h+(D+D))",EqSym(left),bounded)
        bounded = _subst(t,registry,"Le(y+D,slot)",right,bounded)
        upper = apply(specialize(t,"mul_left_mono",Add(h,D),Mul(D,q),two),t.hyp("old_bound"))
        bound = apply(specialize(t,"le_trans",Add(y,D),Mul(two,Add(h,D)),Mul(two,Mul(D,q))),bounded,upper)
        final = _chain(_multiplicative_equal(t,Mul(two,Mul(D,q)),Mul(D,Mul(q,two))),CongMul(EqRefl(D),EqSym(t.hyp("next_power"))))
        return _subst(t,registry,"Le(y+D,slot)",final,bound)
    return introduce(s,("D","h","c","q","y","p"),("old_bound","coefficient_bound","next_value","next_power"),finish)


def _all_prefixes(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two = Succ(Succ(Zero()))
    def base(t):
        D,y,p = t.terms(("D","y","p"));zero = Zero()
        step = apply(instantiate(AndElimR(t.hyp("trace")),zero),t.hyp("bound"))
        y0 = _chain(apply(specialize(t,"step_value",*t.terms(A),two,*t.terms(H),zero,zero,zero,y),
            step,AndElimL(t.hyp("trace")),t.hyp("zero_head"),t.hyp("value")),
            CongAdd(instantiate(Axiom("PA5"),two),EqRefl(zero)),specialize(t,"zero_add",zero))
        p1 = apply(specialize(t,"power_zero",two,zero,p),EqRefl(zero),t.hyp("power"))
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
            next_value = apply(specialize(u,"step_value",*u.terms(A),two,*u.terms(H),sk,*u.terms(("h","c","y"))),
                step,u.hyp("old_value"),u.hyp("coefficient"),u.hyp("value"))
            return apply(specialize(u,"step_bound",*u.terms(("D","h","c","q","y","p"))),old,coefficient_bound,next_value,AndElimR(u.hyp("power_data")))
        power = apply(specialize(t,"power_step",two,t.term("k"),Succ(t.term("k")),t.term("p")),EqRefl(Succ(t.term("k"))),t.hyp("power"))
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


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndIntro
    from peano_lab.kernel.terms import Succ,Zero
    two = Succ(Succ(Zero()))
    def chosen(t):
        length = Succ(t.term("k"))
        invariant = apply(specialize(t,"all_prefixes",*t.terms(A+("D",)),length,*t.terms(H)),
            t.hyp("zero_head"),t.hyp("coefficients"),AndElimL(t.hyp("horner")))
        bound = apply(instantiate(invariant,*t.terms(("k","y","p"))),specialize(t,"le_refl",length),t.hyp("value"),t.hyp("power"))
        return witness(t.terms(("y","p")),conjunction(witness(t.terms(H),AndIntro(AndElimL(t.hyp("horner")),t.hyp("value"))),t.hyp("power"),bound))
    return introduce(s,PARAMETERS,("zero_head","coefficients"),lambda t:
        eliminate(t,specialize(t,"horner_exists",*t.terms(A),two,Succ(t.term("k"))),H,"horner",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H),Succ(u.term("k"))),("y",),"value",lambda v:
                eliminate(v,specialize(v,"power_exists",two,v.term("k")),("p",),"power",chosen))))


def prove_bounded_horner(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV065",target=frozen_bounded_horner_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"step_bound":lambda s:_step_bound(s,registry),
            "all_prefixes":lambda s:_all_prefixes(s,parse_named(HELPER_SOURCES["all_prefixes"],registry=registry),registry),"CV065":_root},
        pins=bounded_horner_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
