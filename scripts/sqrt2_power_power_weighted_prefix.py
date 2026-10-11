"""CV069: construct actual weighted powers and their actual finite sum.

For arbitrary coded W and natural x, construct T[j]=W[j]*x^j for j<K.
Power values are certified by the existing Pow graph, not host arithmetic.
No factorial normalization, positivity, ratio or analytic bound is assumed.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_ratio_sum_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as base_registry,ratio_sum_bound_source_pins,
    COMPOSITION_ARCHIVE,
)
from sqrt2_power_exponential_weights import ENDPOINT_SOURCES as ARITHMETIC_ENDPOINTS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-power-weighted-prefix-v1"
W,T,O = ("wb","wc"),("tb","tc"),("ob","oc")
FIXED = ("x",)+W
PARAMETERS = FIXED+("K",)


def graph(codes,length="K"):
    return "NatPowerWeightedPrefix("+",".join(FIXED+codes+(length,))+")"


DEFINITIONS = (
    ("ND0442","NatPowerWeightedPrefix",FIXED+T+("K",),
     "forall j w p t. Lt(j,K) -> BetaAt(wb,wc,j,w) -> Pow(x,j,p) -> BetaAt(tb,tc,j,t) -> t=w*p",
     ("Lt","BetaAt","Pow"),"bd2b8cdc2134fec1b1adfa3122bb75f8356634009cc137a7c15ede2ddf6fed8c"),
)
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". exists tb tc s. "+graph(T)+" /\\ Sum(tb,tc,K,s)"
TARGET_SHA256 = "ed362b7903fc9933f4dc5185589dd926c667bfdd97db615b673296a1e094fd9c"
HELPER_SOURCES = {
    "extend":"forall "+" ".join(FIXED+O+("K",))+". "+graph(O)+" -> exists tb tc. "+graph(T,"S K"),
    "prefix_exists":"forall "+" ".join(PARAMETERS)+". exists tb tc. "+graph(T),
}
HELPER_TARGET_SHA256 = {
    "extend":"68dcbe0a7719950df6bc339304bee02b0288408a41c494bc7d1a74cd73be70f6",
    "prefix_exists":"b2af815f7f19464c0a9c9fe11dcd704497375e254ae856b0151e92c434acab8f",
}
ARCHIVES = (COMPOSITION_ARCHIVE,)
ENDPOINT_SOURCES = {
    **{name:ARITHMETIC_ENDPOINTS[name] for name in ("beta_exists","beta_unique","beta_extend","zero_le","lt_not_le","le_of_succ_le_succ","le_eq_or_lt")},
    "power_exists":"forall d n. exists p. Pow(d,n,p)",
    "power_unique":"forall a n x y. Pow(a,n,x) -> Pow(a,n,y) -> x=y",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {
    "extend":("beta_exists","beta_unique","beta_extend","power_exists","power_unique","le_of_succ_le_succ","le_eq_or_lt"),
    "prefix_exists":("zero_le","lt_not_le","extend"),
    "CV069":("prefix_exists","sum_exists"),
}


class PowerWeightedPrefixError(ValueError):
    """Changed actual power graph or finite weighted computation."""


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
            raise PowerWeightedPrefixError("weighted-power definition collision or forward dependency")
        formula = parse_named(source,params,result)
        if json_hash(encode_formula(formula))!=digest:
            raise PowerWeightedPrefixError("weighted-power conservative expansion changed")
        text = pretty_formula(formula,list(params))
        d = _definition(stable_id=identifier,name=name,parameters=params,template_source=text,
            summary="Actual decoded entry times an actual power value; no sum or analytic bound.",
            category="irrationality_formal_series",conceptual_dependencies=deps)
        if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula:
            raise PowerWeightedPrefixError("weighted-power definition failed exact conservative roundtrip")
        result[name] = d;ids.add(identifier);names.add(name)
    return MappingProxyType(result)


def frozen_power_weighted_prefix_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=4 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PowerWeightedPrefixError("CV069 exact weighted-power construction target changed")
    return target


def source_contract():
    return dict(code="CV069",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_power_weighted_prefix_constructed=True,actual_same_prefix_sum_constructed=True,
        arbitrary_weight_codes=True,zero_base_and_empty_prefix_allowed=True,actual_power_graph_required=True,
        identity="T[j]=W[j]*x^j",new_definition_ids=["ND0442"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",factorial_normalization_claimed=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def power_weighted_prefix_source_pins():
    result = ratio_sum_bound_source_pins()
    expected = {"scripts/sqrt2_power_ratio_sum_bound.py":"18f2cee3fa530a2e4e658c1ac097f65710b7080776714643bff400eeca14ef15",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_power_weighted_prefix.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PowerWeightedPrefixError("weighted-power source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _extend(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqSym,OrElim
    from peano_lab.kernel.terms import Mul
    def extended(t):
        def entry(u):
            def last(v):
                def moved(codes,val):
                    return _subst(v,registry,"BetaAt("+",".join(codes+("slot",val))+")",v.hyp("last"),v.hyp("entry_"+val))
                ww = apply(specialize(v,"beta_unique",*v.terms(W+("K","w","w0"))),moved(W,"w"),v.hyp("weight"))
                pk = _subst(v,registry,"Pow(x,slot,p)",v.hyp("last"),v.hyp("entry_p"))
                pp = apply(specialize(v,"power_unique",*v.terms(("x","K","p","p0"))),pk,v.hyp("power"))
                zz = apply(specialize(v,"beta_unique",*v.terms(T+("K","t")),Mul(*v.terms(("w0","p0")))),moved(T,"t"),AndElimL(v.hyp("extension")))
                return _chain(zz,CongMul(EqSym(ww),EqSym(pp)))
            def earlier(v):
                def decoded(w):
                    relation = apply(specialize(w,"old",*w.terms(("j","w","p","z"))),w.hyp("earlier"),w.hyp("entry_w"),w.hyp("entry_p"),w.hyp("old_entry"))
                    kept = apply(instantiate(AndElimR(w.hyp("extension")),*w.terms(("j","z"))),w.hyp("earlier"),w.hyp("old_entry"))
                    same = apply(specialize(w,"beta_unique",*w.terms(T+("j","t","z"))),w.hyp("entry_t"),kept)
                    return _chain(same,relation)
                return eliminate(v,specialize(v,"beta_exists",*v.terms(O+("j",))),("z",),"old_entry",decoded)
            bound = apply(specialize(u,"le_of_succ_le_succ",*u.terms(("j","K"))),u.hyp("bound"))
            cases = apply(specialize(u,"le_eq_or_lt",*u.terms(("j","K"))),bound)
            return OrElim(cases,last(u.hypothesis("last")),earlier(u.hypothesis("earlier")))
        return witness(t.terms(T),introduce(t,("j","w","p","t"),("bound","entry_w","entry_p","entry_t"),entry))
    return introduce(s,FIXED+O+("K",),("old",),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(W+("K",))),("w0",),"weight",lambda u:
            eliminate(u,specialize(u,"power_exists",*u.terms(("x","K"))),("p0",),"power",lambda v:
                eliminate(v,specialize(v,"beta_extend",*v.terms(("K",)+O),Mul(*v.terms(("w0","p0")))),T,"extension",extended))))


def _prefix_exists(s,target):
    from peano_lab.kernel.proofs import BotElim,Ind
    from peano_lab.kernel.terms import Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("j","w","p","t"),("bound","weight","power","value"),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("j"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("j"))))))
    def successor(t):
        return eliminate(t,t.hyp("IH"),O,"old",lambda u:apply(specialize(u,"extend",*u.terms(FIXED+O+("K",))),u.hyp("old")))
    motive = target
    for _ in PARAMETERS:
        motive = motive.body
    return introduce(s,FIXED,(),lambda t:Ind(motive,base(t),introduce(t,("K",),("IH",),successor)))


def _root(s):
    from peano_lab.kernel.proofs import AndIntro
    return introduce(s,PARAMETERS,(),lambda t:
        eliminate(t,specialize(t,"prefix_exists",*t.terms(PARAMETERS)),T,"terms",lambda u:
            eliminate(u,specialize(u,"sum_exists",*u.terms(T+("K",))),("s",),"sum",lambda v:
                witness(v.terms(T+("s",)),AndIntro(v.hyp("terms"),v.hyp("sum"))))))


def prove_power_weighted_prefix(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV069",target=frozen_power_weighted_prefix_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"extend":lambda s:_extend(s,registry),
            "prefix_exists":lambda s:_prefix_exists(s,parse_named(HELPER_SOURCES["prefix_exists"],registry=registry)),"CV069":_root},
        pins=power_weighted_prefix_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
