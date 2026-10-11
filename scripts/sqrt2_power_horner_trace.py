"""CV032: total finite integer Horner traces and extensional uniqueness.

The recurrence is h[0]=0, h[k+1]=t*h[k]+a[k]. With ascending
coefficients, h[N] is a denominator-cleared evaluation at 1/t for t>0.
Only the finite computation and value uniqueness are asserted here.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_exponential_weights import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as base_registry,exponential_weights_source_pins,
    ENDPOINT_SOURCES as WEIGHT_ENDPOINTS,
)
from sqrt2_power_weight_factorials import WEIGHTS_ARCHIVE
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst
from sqrt2_power_quadratic_product_exists import read_archive

SCHEMA = "sqrt2-power-horner-trace-v1"
A,O,H,T = ("ab","ac"),("ob","oc"),("hb","hc"),("tb","tc")
DEFINITIONS = (
    ("ND0426","NatScaledHornerStep",("ab","ac","t","hb","hc","k"),
     "exists h a. BetaAt(hb,hc,k,h) /\\ (BetaAt(ab,ac,k,a) /\\ BetaAt(hb,hc,S k,t*h+a))",
     ("BetaAt",),"62461f37df1a4b80bfe3c1be855864e1531c90f8752c0c5abe82f959fc941258"),
    ("ND0427","NatScaledHornerTrace",("ab","ac","t","N","hb","hc"),
     "BetaAt(hb,hc,0,0) /\\ (forall k. Lt(k,N) -> NatScaledHornerStep(ab,ac,t,hb,hc,k))",
     ("BetaAt","Lt","NatScaledHornerStep"),"73e831e029e77a4ed574435c4a53ff3c85dedb5edd54729d28d2f8aa8d0b77bc"),
)


def trace(codes,length="N"):
    return "NatScaledHornerTrace("+",".join(A+("t",length)+codes)+")"


def step(codes,index="k"):
    return "NatScaledHornerStep("+",".join(A+("t",)+codes+(index,))+")"


UNIQUE = "forall k h u. Le(k,N) -> BetaAt(hb,hc,k,h) -> BetaAt(tb,tc,k,u) -> h=u"
NAMED_SOURCE = "forall ab ac t N. exists hb hc. "+trace(H)+" /\\ (forall tb tc. "+trace(T)+" -> "+UNIQUE+")"
TARGET_SHA256 = "ef5c41487529723c8676ac25e7e7972e81abf1f34730285cf1abfaae5b63ce80"
HELPER_SOURCES = {
    "step_value":"forall ab ac t hb hc k h a b. "+step(H)+" -> BetaAt(hb,hc,k,h) -> BetaAt(ab,ac,k,a) -> BetaAt(hb,hc,S k,b) -> b=t*h+a",
    "extend":"forall ab ac t N ob oc. "+trace(O)+" -> exists hb hc. "+trace(H,"S N"),
    "unique":"forall ab ac t N hb hc tb tc. "+trace(H)+" -> "+trace(T)+" -> "+UNIQUE,
}
HELPER_TARGET_SHA256 = {
    "step_value":"029cadfaac5f4186451c1a47f46a8e6d683322dea8aec65e449aef31089ade28",
    "extend":"b7bce817eed15042c2df63b85f5e8dce20f2cba2b4f06d59e4581f62c510ecec",
    "unique":"e65933a7d0089fbe5ae3abcf524a88f18c6bcaa0c7bbe9d63c646808c9982a62",
}
ARCHIVES = (WEIGHTS_ARCHIVE,)
ENDPOINT_SOURCES = {name:WEIGHT_ENDPOINTS[name] for name in (
    "beta_exists","beta_unique","beta_extend","zero_le","lt_not_le","le_refl",
    "le_succ","le_of_succ_le_succ","le_eq_or_lt","succ_le_succ")}
ENDPOINT_SOURCES["le_trans"] = "forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)"
HELPER_DEPENDENCIES = {
    "step_value":("beta_unique",),
    "extend":("beta_exists","beta_extend","zero_le","le_refl","le_succ","succ_le_succ","le_of_succ_le_succ","le_eq_or_lt"),
    "unique":("beta_unique","beta_exists","step_value","le_refl","le_succ","le_trans"),
    "CV032":("beta_extend","zero_le","lt_not_le","extend","unique"),
}


class HornerTraceError(ValueError):
    """Changed finite recurrence, conservative definition or actual source."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    result = dict(base_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    for identifier,name,params,source,deps,digest in DEFINITIONS:
        if name in result or identifier in {d.stable_id for d in result.values()} or any(d["id"]==identifier or d["name"]==name for d in parent):
            raise HornerTraceError("Horner computation alias collision")
        formula = parse_named(source,params,result)
        if json_hash(encode_formula(formula))!=digest:
            raise HornerTraceError("Horner computation exact definition changed")
        text = pretty_formula(formula,list(params))
        d = _definition(stable_id=identifier,name=name,parameters=params,template_source=text,
            summary="Finite integer Horner computation only; no polynomial or analytic identity.",
            category="irrationality_formal_series",conceptual_dependencies=deps)
        if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula or not set(deps)<=result.keys():
            raise HornerTraceError("Horner definition failed conservative roundtrip or DAG check")
        result[name] = d
    return MappingProxyType(result)


def frozen_horner_trace_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=4 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerTraceError("CV032 exact total Horner target changed")
    return target


def source_contract():
    return dict(code="CV032",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_horner_trace_constructed=True,all_in_range_values_unique=True,
        empty_prefix_and_zero_multiplier_allowed=True,code_number_uniqueness=False,
        new_definition_ids=["ND0426","ND0427"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",rational_evaluation_identity=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def horner_trace_source_pins():
    result = exponential_weights_source_pins()
    expected = {
        "scripts/sqrt2_power_exponential_weights.py":"f9e1c356636cffd2d244cd01974999b32e835f864bfdfbef4ded8e2ea26e6085",
        "scripts/sqrt2_power_weight_factorials.py":"cabf5acbe76204dc59c64130a45172440713577d2859f1672635d3a4cf6aacd7",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_horner_trace.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerTraceError("Horner source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _step_value(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ
    def chosen(t):
        fixed = t.terms(H+("k",))
        hh = apply(specialize(t,"beta_unique",*fixed,*t.terms(("v","h"))),field(t.hyp("data"),0,3),t.hyp("old"))
        aa = apply(specialize(t,"beta_unique",*t.terms(A+("k","c","a"))),field(t.hyp("data"),1,3),t.hyp("coefficient"))
        value = Add(Mul(t.term("t"),t.term("v")),t.term("c"))
        current = apply(specialize(t,"beta_unique",*t.terms(H),Succ(t.term("k")),t.term("b"),value),t.hyp("new"),field(t.hyp("data"),2,3))
        return _chain(current,CongAdd(CongMul(EqRefl(t.term("t")),hh),aa))
    return introduce(s,A+("t",)+H+("k","h","a","b"),("step","old","coefficient","new"),lambda t:
        eliminate(t,t.hyp("step"),("v","c"),"data",chosen))


def _extend(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,EqSym,OrElim
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def extended(t):
        def preserve(u,index,value,bound,old):
            return apply(instantiate(AndElimR(u.hyp("extension")),index,value),bound,old)
        initial = preserve(t,Zero(),Zero(),apply(specialize(t,"succ_le_succ",Zero(),t.term("N")),specialize(t,"zero_le",t.term("N"))),AndElimL(t.hyp("trace")))
        def next_at(u):
            def last(v):
                old = preserve(v,v.term("N"),v.term("h"),specialize(v,"le_refl",Succ(v.term("N"))),v.hyp("old"))
                output = witness(v.terms(("h","a")),conjunction(old,v.hyp("coefficient"),AndElimL(v.hyp("extension"))))
                return _subst(v,registry,step(H,"slot"),EqSym(v.hyp("last")),output)
            def earlier(v):
                def decoded(w):
                    k,N = w.terms(("k","N"))
                    first_bound = apply(specialize(w,"le_succ",Succ(k),N),w.hyp("earlier"))
                    second_bound = apply(specialize(w,"succ_le_succ",Succ(k),N),w.hyp("earlier"))
                    first = preserve(w,k,w.term("v"),first_bound,field(w.hyp("data"),0,3))
                    value = Add(Mul(w.term("t"),w.term("v")),w.term("c"))
                    second = preserve(w,Succ(k),value,second_bound,field(w.hyp("data"),2,3))
                    return witness(w.terms(("v","c")),conjunction(first,field(w.hyp("data"),1,3),second))
                old_step = apply(instantiate(AndElimR(v.hyp("trace")),v.term("k")),v.hyp("earlier"))
                return eliminate(v,old_step,("v","c"),"data",decoded)
            lower = apply(specialize(u,"le_of_succ_le_succ",*u.terms(("k","N"))),u.hyp("bound"))
            cases = apply(specialize(u,"le_eq_or_lt",*u.terms(("k","N"))),lower)
            return OrElim(cases,last(u.hypothesis("last")),earlier(u.hypothesis("earlier")))
        return witness(t.terms(H),AndIntro(initial,introduce(t,("k",),("bound",),next_at)))
    return introduce(s,A+("t","N")+O,("trace",),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(O+("N",))),("h",),"old",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(A+("N",))),("a",),"coefficient",lambda v:
                eliminate(v,specialize(v,"beta_extend",Succ(v.term("N")),*v.terms(O),Add(Mul(v.term("t"),v.term("h")),v.term("a"))),H,"extension",extended))))


def _unique(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Succ,Zero
    def base(t):
        first = apply(specialize(t,"beta_unique",*t.terms(H),Zero(),t.term("h"),Zero()),t.hyp("first"),AndElimL(t.hyp("traceH")))
        second = apply(specialize(t,"beta_unique",*t.terms(T),Zero(),t.term("u"),Zero()),t.hyp("second"),AndElimL(t.hyp("traceT")))
        return _chain(first,EqSym(second))
    def successor(t):
        def chosen(u):
            k,N = u.terms(("k","N"))
            earlier = apply(specialize(u,"le_trans",k,Succ(k),N),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            same = apply(specialize(u,"IH",*u.terms(("h0","u0"))),earlier,u.hyp("oldH"),u.hyp("oldT"))
            def value(codes,label,old,previous,new):
                st = apply(instantiate(AndElimR(u.hyp(label)),k),u.hyp("bound"))
                return apply(specialize(u,"step_value",*u.terms(A+("t",)+codes+("k",old,"a",new))),st,u.hyp(previous),u.hyp("coefficient"),u.hyp("first" if new=="h" else "second"))
            return _chain(value(H,"traceH","h0","oldH","h"),CongAdd(CongMul(EqRefl(u.term("t")),same),EqRefl(u.term("a"))),EqSym(value(T,"traceT","u0","oldT","u")))
        return eliminate(t,specialize(t,"beta_exists",*t.terms(H+("k",))),("h0",),"oldH",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(T+("k",))),("u0",),"oldT",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(A+("k",))),("a",),"coefficient",chosen)))
    motive = target
    for _ in range(8):
        motive = motive.body
    motive = motive.right.right.body
    return introduce(s,A+("t","N")+H+T,("traceH","traceT"),lambda t:
        Ind(motive,introduce(t,("h","u"),("bound","first","second"),base),
            introduce(t,("k",),("IH",),lambda u:introduce(u,("h","u"),("bound","first","second"),successor))))


def _root(s,target):
    from peano_lab.kernel.proofs import AndElimL,AndIntro,BotElim,Ind
    from peano_lab.kernel.terms import Zero
    # First construct the trace by induction, retaining uniqueness separately
    # at each length through the same conditional uniqueness proof.
    def package(t,proof,length):
        unique = introduce(t,T,("other",),lambda u:
            apply(specialize(u,"unique",*u.terms(A+("t",)),length(u),*u.terms(H+T)),
                proof(u),u.hyp("other")))
        return witness(t.terms(H),AndIntro(proof(t),unique))
    def base(t):
        def chosen(u):
            def graph(v):
                empty = introduce(v,("k",),("bound",),lambda w:
                    BotElim(apply(specialize(w,"lt_not_le",w.term("k"),Zero()),w.hyp("bound"),specialize(w,"zero_le",w.term("k")))))
                return AndIntro(AndElimL(v.hyp("extension")),empty)
            return package(u,graph,lambda _:Zero())
        return eliminate(t,specialize(t,"beta_extend",Zero(),Zero(),Zero(),Zero()),H,"extension",chosen)
    def successor(t):
        from peano_lab.kernel.terms import Succ
        return eliminate(t,t.hyp("IH"),O,"old",lambda u:
            eliminate(u,apply(specialize(u,"extend",*u.terms(A+("t","N")+O)),AndElimL(u.hyp("old"))),H,"new",
                lambda v:package(v,lambda w:w.hyp("new"),lambda w:Succ(w.term("N")))))
    motive = target.body.body.body.body
    return introduce(s,A+("t",),(),lambda t:Ind(motive,base(t),introduce(t,("N",),("IH",),successor)))


def prove_horner_trace(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry,target = definition_registry(),frozen_horner_trace_target()
    factories = {"step_value":_step_value,"extend":lambda s:_extend(s,registry),
        "unique":lambda s:_unique(s,parse_named(HELPER_SOURCES["unique"],registry=registry)),"CV032":lambda s:_root(s,target)}
    return assemble_actual_certificate(code="CV032",target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=horner_trace_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=2)
