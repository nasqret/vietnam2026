"""CV037: interpret an actual Horner endpoint as an actual weighted sum.

Supplied W satisfies W[N]=1 and W[j]=t*W[j+1]; supplied Q satisfies
Q[j]=A[j]*W[j+1]. Construct the Horner endpoint r and prove Sum(Q,N,r).
Existence of W and Q is not assumed silently or asserted by this theorem.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_horner_trace import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as horner_registry,horner_trace_source_pins,
    NAMED_SOURCE as HORNER_SOURCE,HELPER_SOURCES as HORNER_HELPERS,
)
from sqrt2_power_geometric_horner import HORNER_ARCHIVE
from sqrt2_power_periodic_convolution import COMM_ARCHIVE,CONVOLUTION_ARCHIVE
from sqrt2_power_convolution_commutative import ENDPOINT_SOURCES as SUM_ENDPOINTS
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive
from sqrt2_power_convolution_unit import _subst

SCHEMA = "sqrt2-power-horner-weighted-sum-v1"
A,W,Q,H = ("ab","ac"),("wb","wc"),("qb","qc"),("hb","hc")
PARAMETERS = A+("t","N")+W+Q
DEFINITIONS = (
    ("ND0428","NatGeometricWeightTable",("t","N","wb","wc"),
     "BetaAt(wb,wc,N,1) /\\ (forall j a b. Lt(j,N) -> BetaAt(wb,wc,j,a) -> BetaAt(wb,wc,S j,b) -> a=t*b)",
     ("BetaAt","Lt"),"9f23a078dad02bcaea1fa537a0511f1d9d606295c7eed9be2491c7b811fd5104"),
    ("ND0429","NatHornerWeightedPrefix",A+W+Q+("N",),
     "forall j a b c. Lt(j,N) -> BetaAt(ab,ac,j,a) -> BetaAt(wb,wc,S j,b) -> BetaAt(qb,qc,j,c) -> c=a*b",
     ("BetaAt","Lt"),"0142e7164b99c6f1ca9deaa2303cb5aa309d788de48b7797bcf77378d02643ed"),
)
WEIGHTS = "NatGeometricWeightTable(t,N,wb,wc)"
PRODUCTS = "NatHornerWeightedPrefix(ab,ac,wb,wc,qb,qc,N)"
TRACE = "NatScaledHornerTrace(ab,ac,t,N,hb,hc)"
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+WEIGHTS+" -> "+PRODUCTS+" -> exists hb hc r. "+TRACE+" /\\ (BetaAt(hb,hc,N,r) /\\ Sum(qb,qc,N,r))"
TARGET_SHA256 = "6f5222fbdb659a953b151731a5f8b309685813f395efda3e55af160b5757bfd8"
HELPER_SOURCES = {
    "shuffle":"forall t h a w. (t*h+a)*w=h*(t*w)+a*w",
    "invariant":"forall "+" ".join(PARAMETERS+H)+". "+WEIGHTS+" -> "+PRODUCTS+" -> "+TRACE+" -> forall k h w s. Le(k,N) -> BetaAt(hb,hc,k,h) -> BetaAt(wb,wc,k,w) -> Sum(qb,qc,k,s) -> h*w=s",
}
HELPER_TARGET_SHA256 = {
    "shuffle":"b4cb0c1b9e96c2867fbdb1c04b2466f35bc0b8d1a164528e30f6f353411965c2",
    "invariant":"b5e7c5e852b41e5a1c05569b4f8f0eaf55497c3e4ed6a1c50b29a652bf6850f6",
}
ARCHIVES = (HORNER_ARCHIVE,COMM_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {name:SUM_ENDPOINTS[name] for name in ("beta_exists","beta_unique","sum_exists","sum_zero","sum_decompose","mul_comm")}
ENDPOINT_SOURCES.update(horner_exists=HORNER_SOURCE,step_value=HORNER_HELPERS["step_value"],
    le_refl="forall a. Le(a,a)",le_succ="forall a b. Le(a,b) -> Le(a,S b)",
    le_trans="forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",mul_assoc="forall a b c. (a*b)*c=a*(b*c)",
    add_mul="forall a b c. (a+b)*c=a*c+b*c",mul_one="forall a. a*1=a",mul_zero_left="forall a. 0*a=0")
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:"CV010" for name in ("sum_exists","sum_zero","sum_decompose")})
ENDPOINT_OWNERS.update(horner_exists="CV032",step_value="CV032")
HELPER_DEPENDENCIES = {
    "shuffle":("add_mul","mul_assoc","mul_comm"),
    "invariant":("beta_unique","mul_zero_left","sum_zero","sum_decompose","beta_exists","le_refl","le_succ","le_trans","step_value","shuffle"),
    "CV037":("horner_exists","beta_exists","sum_exists","invariant","le_refl","mul_one"),
}


class HornerWeightedSumError(ValueError):
    """Changed finite weights, product relation or exact ordinary proof."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    result = dict(horner_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    for identifier,name,params,source,deps,digest in DEFINITIONS:
        if name in result or identifier in {d.stable_id for d in result.values()} or any(d["id"]==identifier or d["name"]==name for d in parent):
            raise HornerWeightedSumError("weighted Horner alias collision")
        formula = parse_named(source,params,result)
        if json_hash(encode_formula(formula))!=digest:
            raise HornerWeightedSumError("weighted Horner definition changed")
        text = pretty_formula(formula,list(params))
        d = _definition(stable_id=identifier,name=name,parameters=params,template_source=text,
            summary="Finite weight or product computation graph only; no sum/evaluation identity.",
            category="irrationality_formal_series",conceptual_dependencies=deps)
        if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula or not set(deps)<=result.keys():
            raise HornerWeightedSumError("weighted Horner definition failed conservative roundtrip or DAG check")
        result[name] = d
    return MappingProxyType(result)


def frozen_horner_weighted_sum_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=8 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerWeightedSumError("CV037 exact weighted sum interpretation changed")
    return target


def source_contract():
    return dict(code="CV037",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,actual_geometric_weights_required=True,actual_pointwise_products_required=True,
        weights_or_products_constructed=False,horner_trace_and_endpoint_constructed=True,
        actual_sum_for_same_endpoint_proved=True,zero_multiplier_and_empty_prefix_allowed=True,
        new_definition_ids=["ND0428","ND0429"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",power_interpretation_of_weights=False,
        multiplication_evaluation_identity=False,analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def horner_weighted_sum_source_pins():
    result = horner_trace_source_pins()
    expected = {"scripts/sqrt2_power_horner_trace.py":"32feca5a71d2b82367e6321d7a276c8c7de0f0fbf9b97513e22e816f80ee0328",
        "scripts/sqrt2_power_geometric_horner.py":"6179fa42c4437ed53db78fdc4f806d281d4774b58544150c7007dcfa3b656adc",
        "scripts/sqrt2_power_periodic_convolution.py":"aeb95ee2da8e89f07b421c9e743d2bf87e8a765505d9c919df70b51d3ce2c02d",
        "scripts/sqrt2_power_convolution_commutative.py":"d1d4ce7c0e78c03ba5961710b048fe11bcb3dd481afd2e79d5cc2b418b0412a3",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_horner_weighted_sum.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerWeightedSumError("weighted Horner source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _shuffle(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl
    from peano_lab.kernel.terms import Mul
    def finish(t):
        factor,h,a,w = t.terms(("t","h","a","w"))
        return _chain(specialize(t,"add_mul",Mul(factor,h),a,w),
            CongAdd(CongMul(specialize(t,"mul_comm",factor,h),EqRefl(w)),EqRefl(Mul(a,w))),
            CongAdd(specialize(t,"mul_assoc",h,factor,w),EqRefl(Mul(a,w))))
    return introduce(s,("t","h","a","w"),(),finish)


def _invariant(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def base(t):
        h0 = apply(specialize(t,"beta_unique",*t.terms(H),Zero(),t.term("h"),Zero()),t.hyp("value"),AndElimL(t.hyp("trace")))
        s0 = apply(specialize(t,"sum_zero",*t.terms(Q+("s",))),t.hyp("sum"))
        return _chain(CongMul(h0,EqRefl(t.term("w"))),specialize(t,"mul_zero_left",t.term("w")),EqSym(s0))
    def successor(t):
        def chosen(u):
            k,N,t0,h0,w0,w,a = u.terms(("k","N","t","h0","w0","w","a"))
            earlier = apply(specialize(u,"le_trans",k,Succ(k),N),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            previous = apply(specialize(u,"IH",*u.terms(("h0","w0","r"))),earlier,u.hyp("old_value"),u.hyp("old_weight"),field(u.hyp("sum_data"),1,3))
            adjacent = apply(instantiate(AndElimR(u.hyp("weights")),k,w0,w),u.hyp("bound"),u.hyp("old_weight"),u.hyp("weight"))
            product = apply(specialize(u,"products",k,a,w,u.term("q")),u.hyp("bound"),u.hyp("coefficient"),u.hyp("weight"),field(u.hyp("sum_data"),0,3))
            st = apply(instantiate(AndElimR(u.hyp("trace")),k),u.hyp("bound"))
            horner = apply(specialize(u,"step_value",*u.terms(A),t0,*u.terms(H),k,h0,a,u.term("h")),
                st,u.hyp("old_value"),u.hyp("coefficient"),u.hyp("value"))
            return _chain(CongMul(horner,EqRefl(w)),specialize(u,"shuffle",t0,h0,a,w),
                CongAdd(CongMul(EqRefl(h0),EqSym(adjacent)),EqSym(product)),
                CongAdd(previous,EqRefl(u.term("q"))),EqSym(field(u.hyp("sum_data"),2,3)))
        decomposition = apply(specialize(t,"sum_decompose",*t.terms(Q+("k","s"))),t.hyp("sum"))
        return eliminate(t,decomposition,("q","r"),"sum_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H+("k",))),("h0",),"old_value",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(W+("k",))),("w0",),"old_weight",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(A+("k",))),("a",),"coefficient",chosen))))
    motive = target
    for _ in PARAMETERS+H:
        motive = motive.body
    motive = motive.right.right.right.body
    return introduce(s,PARAMETERS+H,("weights","products","trace"),lambda t:Ind(motive,
        introduce(t,("h","w","s"),("bound","value","weight","sum"),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,("h","w","s"),("bound","value","weight","sum"),successor))))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        graph = AndElimL(t.hyp("horner"))
        invariant = apply(specialize(t,"invariant",*t.terms(PARAMETERS+H)),t.hyp("weights"),t.hyp("products"),graph)
        terminal = apply(instantiate(invariant,t.term("N"),t.term("r"),Succ(Zero()),t.term("s")),
            specialize(t,"le_refl",t.term("N")),t.hyp("value"),AndElimL(t.hyp("weights")),t.hyp("sum"))
        equality = _chain(EqSym(terminal),specialize(t,"mul_one",t.term("r")))
        actual_sum = _subst(t,registry,"Sum(qb,qc,N,slot)",equality,t.hyp("sum"))
        return witness(t.terms(H+("r",)),conjunction(graph,t.hyp("value"),actual_sum))
    return introduce(s,PARAMETERS,("weights","products"),lambda t:
        eliminate(t,specialize(t,"horner_exists",*t.terms(A+("t","N"))),H,"horner",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H+("N",))),("r",),"value",lambda v:
                eliminate(v,specialize(v,"sum_exists",*v.terms(Q+("N",))),("s",),"sum",chosen))))


def prove_horner_weighted_sum(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"shuffle":_shuffle,"invariant":lambda s:_invariant(s,parse_named(HELPER_SOURCES["invariant"],registry=registry)),"CV037":lambda s:_root(s,registry)}
    return assemble_mixed_certificate(code="CV037",target=frozen_horner_weighted_sum_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,
        pins=horner_weighted_sum_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
