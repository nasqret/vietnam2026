"""CV070: construct actual denominator-cleared finite exponential terms.

The same factorial weights and weighted powers satisfy the exact adjacent
recurrence and factorial normalization. A nonzero denominator gives a
nonzero initial value. No finite-sum bound or analytic limit is asserted.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_power_weighted_prefix import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as base_registry,power_weighted_prefix_source_pins,
    NAMED_SOURCE as TERMS_SOURCE,COMPOSITION_ARCHIVE,
)
from sqrt2_power_weight_factorials import NAMED_SOURCE as FACTORIAL_SOURCE,INVARIANT as WEIGHT_INVARIANT
from sqrt2_power_normalized_composition import FACTORIAL_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-scaled-exp-terms-v1"
W,T = ("wb","wc"),("tb","tc")
FIXED = ("d","x","N")+W+T
OUTPUTS = W+T+("w0","f","p","s")
WEIGHTS = "NatExpWeightTable(d,N,wb,wc)"
TERMS = "NatPowerWeightedPrefix(x,wb,wc,tb,tc,S N)"
RECURRENCE = "NatScaledExpRecurrence(d,x,tb,tc,N)"
NORMALIZATION = "forall j t f0 p0 q. Le(j,N) -> BetaAt(tb,tc,j,t) -> Factorial(j,f0) -> Pow(d,j,p0) -> Pow(x,j,q) -> (t*f0)*p0=w0*q"
DEFINITIONS = (
    ("ND0443","NatScaledExpRecurrence",("d","x","tb","tc","N"),
     "forall j a b. Lt(j,N) -> BetaAt(tb,tc,j,a) -> BetaAt(tb,tc,S j,b) -> ((S j)*d)*b=x*a",
     ("Lt","BetaAt"),"4b867be11f4925f2ef9b08da5d0d57a195a90aa050ac4f1306024d4861b7e30e"),
)
NAMED_SOURCE = "forall d x N. ~d=0 -> exists "+" ".join(OUTPUTS)+". "+WEIGHTS+" /\\ ("+TERMS+" /\\ (BetaAt(wb,wc,0,w0) /\\ (BetaAt(tb,tc,0,w0) /\\ (~w0=0 /\\ (Factorial(N,f) /\\ (Pow(d,N,p) /\\ (w0=f*p /\\ (Sum(tb,tc,S N,s) /\\ ("+RECURRENCE+" /\\ ("+NORMALIZATION+"))))))))))"
TARGET_SHA256 = "7f9e9c6aa4b255463768b661ebe9736b133dd810525dfd27ff94dfbe3693bf1d"
HELPER_SOURCES = {
    "head":"forall x N wb wc tb tc w0. "+TERMS+" -> BetaAt(wb,wc,0,w0) -> BetaAt(tb,tc,0,w0)",
    "recurrence":"forall "+" ".join(FIXED)+". "+WEIGHTS+" -> "+TERMS+" -> "+RECURRENCE,
    "normalization":"forall "+" ".join(FIXED+("w0",))+". ("+WEIGHT_INVARIANT+") -> "+TERMS+" -> "+NORMALIZATION,
}
HELPER_TARGET_SHA256 = {
    "head":"6a3d2baaf085e7027aec448ac1ecd5d252e2fa416309d5bdc56d95337c817afd",
    "recurrence":"d98bb434ddfab36ae330c39e14be10393392409564166bf305d76622b4273644",
    "normalization":"7dacf48411e29d84bd6750a01089dab3dec66dc7f0c6c88429fe9a80eb8bcb53",
}
TERMS_ARCHIVE = dict(case="CV069",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-power-weighted-prefix-v1/generation-process.json.gz",
    bytes=28011,sha256="99ba5448b3555b66d8dcda84373071bb3b40137799c1569a92590d3dfcd1af39",
    raw_bytes=405816,raw_sha256="57114e4babc38d892a7fdefd79a9cdba04a2523439faa68f7a84ec489a0b68dd",
    bundle_bytes=219969,bundle_sha256="78c022fee7071b3379f26cdce3ad991097813fb284760516d9a31b50bd1d4c61",
    nodes=121,root=120,target_ast_sha256="ed362b7903fc9933f4dc5185589dd926c667bfdd97db615b673296a1e094fd9c")
ARCHIVES = (TERMS_ARCHIVE,FACTORIAL_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES = {
    "terms_exists":TERMS_SOURCE,"factorial_weights_exists":FACTORIAL_SOURCE,
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "power_exists":"forall d n. exists p. Pow(d,n,p)",
    "power_zero":"forall d n p. n=0 -> Pow(d,n,p) -> p=1",
    "power_step":"forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d",
    "zero_le":"forall a. Le(0,a)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "mul_one":"forall a. a*1=a","mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(terms_exists="CV069",factorial_weights_exists="CV030")
HELPER_DEPENDENCIES = {
    "head":("beta_exists","power_exists","power_zero","zero_le","succ_le_succ","mul_one"),
    "recurrence":("beta_exists","power_exists","power_step","le_succ","succ_le_succ","mul_assoc","mul_comm"),
    "normalization":("beta_exists","succ_le_succ","mul_assoc","mul_comm"),
    "CV070":("factorial_weights_exists","terms_exists","head","recurrence","normalization","zero_le"),
}


class ScaledExpTermsError(ValueError):
    """Changed common denominator, same-table recurrence or normalization."""


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
            raise ScaledExpTermsError("scaled-exp definition collision or forward dependency")
        formula = parse_named(source,params,result)
        if json_hash(encode_formula(formula))!=digest:
            raise ScaledExpTermsError("scaled-exp conservative expansion changed")
        text = pretty_formula(formula,list(params))
        d = _definition(stable_id=identifier,name=name,parameters=params,template_source=text,
            summary="Exact finite adjacent-term arithmetic recurrence, without positivity or analytic assertions.",
            category="irrationality_formal_series",conceptual_dependencies=deps)
        if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula:
            raise ScaledExpTermsError("scaled-exp definition failed exact conservative roundtrip")
        result[name] = d;ids.add(identifier);names.add(name)
    return MappingProxyType(result)


def frozen_scaled_exp_terms_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=3 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ScaledExpTermsError("CV070 exact scaled exponential term target changed")
    return target


def source_contract():
    return dict(code="CV070",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,nonzero_denominator_required=True,actual_factorial_weights_and_power_terms_constructed=True,
        same_weight_and_term_tables_throughout=True,actual_same_prefix_sum_constructed=True,
        actual_factorial_and_denominator_power_constructed=True,nonzero_initial_value_proved=True,
        exact_adjacent_recurrence=True,all_index_factorial_normalization=True,zero_argument_allowed=True,
        new_definition_ids=["ND0443"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",finite_exp_sum_bound_claimed=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def scaled_exp_terms_source_pins():
    result = power_weighted_prefix_source_pins()
    expected = {"scripts/sqrt2_power_power_weighted_prefix.py":"e5d539ceda69c7b2c2ba86c4e3f66ad899b75913e04544576cb6dd65ed4a97bb",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_scaled_exp_terms.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ScaledExpTermsError("scaled-exp source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _head(s,registry):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl
    from peano_lab.kernel.terms import Zero
    def chosen(t):
        bound = apply(specialize(t,"succ_le_succ",Zero(),t.term("N")),specialize(t,"zero_le",t.term("N")))
        value = apply(specialize(t,"terms",Zero(),*t.terms(("w0","q","a"))),bound,t.hyp("initial_weight"),t.hyp("power"),t.hyp("entry"))
        q1 = apply(specialize(t,"power_zero",t.term("x"),Zero(),t.term("q")),EqRefl(Zero()),t.hyp("power"))
        aw = _chain(value,CongMul(EqRefl(t.term("w0")),q1),specialize(t,"mul_one",t.term("w0")))
        return _subst(t,registry,"BetaAt(tb,tc,0,slot)",aw,t.hyp("entry"))
    return introduce(s,("x","N")+W+T+("w0",),("terms","initial_weight"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(T),Zero()),("a",),"entry",lambda u:
            eliminate(u,specialize(u,"power_exists",u.term("x"),Zero()),("q",),"power",chosen)))


def _recurrence(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def entry(t):
        def chosen(u):
            j,d,x,a,b,v,c = u.terms(("j","d","x","a","b","v","c"));sj = Succ(j);f = Mul(sj,d)
            jb = apply(specialize(u,"le_succ",sj,u.term("N")),u.hyp("bound"))
            sjb = apply(specialize(u,"succ_le_succ",sj,u.term("N")),u.hyp("bound"))
            av = apply(specialize(u,"terms",j,*u.terms(("w","c","a"))),jb,u.hyp("weight"),AndElimL(u.hyp("power_data")),u.hyp("entry_a"))
            bv = apply(specialize(u,"terms",sj,*u.terms(("v","e","b"))),sjb,u.hyp("next_weight"),u.hyp("next_power"),u.hyp("entry_b"))
            weight = apply(instantiate(AndElimR(u.hyp("weights")),j,*u.terms(("w","v"))),u.hyp("bound"),u.hyp("weight"),u.hyp("next_weight"))
            return _chain(CongMul(EqRefl(f),bv),CongMul(EqRefl(f),CongMul(EqRefl(v),AndElimR(u.hyp("power_data")))),
                _multiplicative_equal(u,Mul(f,Mul(v,Mul(c,x))),Mul(x,Mul(Mul(f,v),c))),
                CongMul(EqRefl(x),CongMul(EqSym(weight),EqRefl(c))),CongMul(EqRefl(x),EqSym(av)))
        return eliminate(t,specialize(t,"beta_exists",*t.terms(W+("j",))),("w",),"weight",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(W),Succ(u.term("j"))),("v",),"next_weight",lambda v:
                eliminate(v,specialize(v,"power_exists",v.term("x"),Succ(v.term("j"))),("e",),"next_power",lambda w:
                    eliminate(w,apply(specialize(w,"power_step",*w.terms(("x","j")),Succ(w.term("j")),w.term("e")),EqRefl(Succ(w.term("j"))),w.hyp("next_power")),("c",),"power_data",chosen))))
    return introduce(s,FIXED,("weights","terms"),lambda t:introduce(t,("j","a","b"),("bound","entry_a","entry_b"),entry))


def _normalization(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl
    from peano_lab.kernel.terms import Mul
    def entry(t):
        def chosen(u):
            w,q,t,f,p0 = u.terms(("w","q","t","f0","p0"))
            bound = apply(specialize(u,"succ_le_succ",*u.terms(("j","N"))),u.hyp("bound"))
            term = apply(specialize(u,"terms",*u.terms(("j","w","q","t"))),bound,u.hyp("weight"),u.hyp("argument_power"),u.hyp("entry"))
            normalization = apply(specialize(u,"weights_invariant",*u.terms(("j","w","f0","p0"))),u.hyp("bound"),u.hyp("weight"),u.hyp("factorial"),u.hyp("denominator_power"))
            return _chain(CongMul(CongMul(term,EqRefl(f)),EqRefl(p0)),
                _multiplicative_equal(u,Mul(Mul(Mul(w,q),f),p0),Mul(Mul(Mul(w,f),p0),q)),CongMul(normalization,EqRefl(q)))
        return eliminate(t,specialize(t,"beta_exists",*t.terms(W+("j",))),("w",),"weight",chosen)
    return introduce(s,FIXED+("w0",),("weights_invariant","terms"),lambda t:
        introduce(t,("j","t","f0","p0","q"),("bound","entry","factorial","denominator_power","argument_power"),entry))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        weights,terms = t.hyp("weight_data"),t.hyp("term_data")
        table = field(weights,0,7);head = field(weights,2,7);graph = AndElimL(terms)
        initial = apply(specialize(t,"head",*t.terms(("x","N")+W+T+("w0",))),graph,head)
        nonzero = apply(instantiate(field(weights,1,7),Zero(),t.term("w0")),specialize(t,"zero_le",t.term("N")),head,t.hyp("nonzero_d"))
        recurrence = apply(specialize(t,"recurrence",*t.terms(FIXED)),table,graph)
        normalization = apply(specialize(t,"normalization",*t.terms(FIXED+("w0",))),field(weights,6,7),graph)
        return witness(t.terms(OUTPUTS),conjunction(table,graph,head,initial,nonzero,field(weights,3,7),field(weights,4,7),field(weights,5,7),AndElimR(terms),recurrence,normalization))
    return introduce(s,("d","x","N"),("nonzero_d",),lambda t:
        eliminate(t,specialize(t,"factorial_weights_exists",*t.terms(("d","N"))),W+("w0","f","p"),"weight_data",lambda u:
            eliminate(u,specialize(u,"terms_exists",*u.terms(("x",)+W),Succ(u.term("N"))),T+("s",),"term_data",chosen)))


def prove_scaled_exp_terms(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV070",target=frozen_scaled_exp_terms_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"head":lambda s:_head(s,registry),"recurrence":_recurrence,"normalization":_normalization,"CV070":_root},
        pins=scaled_exp_terms_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
