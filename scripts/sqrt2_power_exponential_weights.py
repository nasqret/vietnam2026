"""CV022: construct denominator-cleared outer weights and prove nonvanishing.

w[N]=1; w[j]=((j+1)*d)*w[j+1]. Construct at N+1 by scaling the old
prefix by (N+1)*d and appending one. Factorial/quotient interpretation is
deliberately separate. Zero d is allowed for construction, not nonvanishing.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_series_linear_combination import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,definition_registry as linear_registry,
    series_linear_combination_source_pins,COMBINATION_SOURCE,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_weighted_series_trace import COMBINATION_ARCHIVE
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst

SCHEMA = "sqrt2-power-exponential-weights-v1"
DEFINITION_PARAMETERS = ("d","N","wb","wc")
DEFINITION_SOURCE = "BetaAt(wb,wc,N,1) /\\ (forall j a b. Lt(j,N) -> BetaAt(wb,wc,j,a) -> BetaAt(wb,wc,S j,b) -> a=((S j)*d)*b)"
DEFINITION_SHA256 = "6bc1c042359a4532d8f0401029df93eced9696c1fc91249109f5ccc257e6efcc"


def weights(codes,length="N"):
    return "NatExpWeightTable("+",".join(("d",length)+codes)+")"


def positive(codes,length="N"):
    return "forall j a. Le(j,"+length+") -> BetaAt("+",".join(codes)+",j,a) -> ~d=0 -> ~a=0"


W,O,C = ("wb","wc"),("ob","oc"),("cb","cc")
NAMED_SOURCE = "forall d N. exists wb wc. "+weights(W)+" /\\ ("+positive(W)+")"
TARGET_SHA256 = "67f4d5cffffb0e5b5dd1f559eb6b6d8cd2dbb5ac23bdeb79d580326b4cf5a880"
SCALING = "NatLinearTriple(f,0,1,ob,oc,ob,oc,cb,cc,N)"
PRESERVED = "forall j a. Lt(j,N) -> BetaAt(cb,cc,j,a) -> BetaAt(wb,wc,j,a)"
HELPER_SOURCES = {
    "scaled_extension":"forall f ob oc cb cc wb wc N j x y. "+SCALING+" -> ("+PRESERVED+") -> Lt(j,N) -> BetaAt(ob,oc,j,x) -> BetaAt(wb,wc,j,y) -> y=f*x",
    "scale_adjacent":"forall f g x y a b. x=g*y -> a=f*x -> b=f*y -> a=g*b",
    "successor":"forall d N ob oc. "+weights(O)+" -> ("+positive(O)+") -> exists wb wc. "+weights(W,"S N")+" /\\ ("+positive(W,"S N")+")",
}
HELPER_TARGET_SHA256 = {
    "scaled_extension":"76a644c4457e36209d5a5257e0842e989f7af358539155174372aef837ae5166",
    "scale_adjacent":"17eb637cf37c1732c766182e2fdbf63417f8eedf2053d37cc367804ca9b6d107",
    "successor":"563edaf51745e53d3cc310faa3e0b001168a0e3ae97521263cd003b3901a832c",
}
ARCHIVES = (CONVOLUTION_ARCHIVE,COMBINATION_ARCHIVE)
ENDPOINT_SOURCES = {
    "one_mul":"forall a. 1*a=a",
    "mul_one":"forall a. a*1=a",
    "mul_zero_left":"forall a. 0*a=0",
    "mul_comm":"forall a b. a*b=b*a",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
    "succ_ne_zero":"forall a. ~S a=0",
    "zero_le":"forall a. Le(0,a)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "le_refl":"forall a. Le(a,a)",
    "le_zero":"forall a. Le(a,0) -> a=0",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "le_eq_or_lt":"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "beta_extend":"forall N b c v. exists eb ec. BetaAt(eb,ec,N,v) /\\ (forall j a. Lt(j,N) -> BetaAt(b,c,j,a) -> BetaAt(eb,ec,j,a))",
    "combination_exists":COMBINATION_SOURCE,
}
HELPER_DEPENDENCIES = {
    "scaled_extension":("beta_exists","beta_unique","one_mul","mul_zero_left"),
    "scale_adjacent":("mul_assoc","mul_comm"),
    "successor":("combination_exists","beta_extend","scaled_extension","beta_exists","beta_unique","le_refl","le_of_succ_le_succ","le_eq_or_lt","le_succ","succ_le_succ","scale_adjacent","mul_ne_zero","succ_ne_zero"),
    "CV022":("beta_extend","beta_unique","zero_le","lt_not_le","le_zero","succ_ne_zero","successor"),
}


class ExponentialWeightsError(ValueError):
    """Changed finite computation, positivity premise, actual body or bound."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(linear_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    name,identifier = "NatExpWeightTable","ND0423"
    if name in registry or identifier in {d.stable_id for d in registry.values()} or any(d["name"]==name or d["id"]==identifier for d in parent):
        raise ExponentialWeightsError("weight computation alias collision")
    formula = parse_named(DEFINITION_SOURCE,DEFINITION_PARAMETERS,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise ExponentialWeightsError("weight computation exact expansion changed")
    text = pretty_formula(formula,list(DEFINITION_PARAMETERS))
    d = _definition(stable_id=identifier,name=name,parameters=DEFINITION_PARAMETERS,template_source=text,
        summary="Terminal-one finite reverse product computation; no positivity, factorial or exponential assertion.",
        category="irrationality_formal_series",conceptual_dependencies=("Lt","BetaAt"))
    if d.template_formula!=formula or parse_formula_in_context(text,list(DEFINITION_PARAMETERS))!=formula:
        raise ExponentialWeightsError("weight computation failed exact conservative roundtrip")
    registry[name] = d
    return MappingProxyType(registry)


def frozen_exponential_weights_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=2 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExponentialWeightsError("CV022 exact constructed weight target changed")
    return target


def source_contract():
    return dict(code="CV022",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_weight_table_constructed=True,zero_denominator_allowed_for_construction=True,
        nonzero_denominator_required_only_for_entry_nonvanishing=True,all_entries_through_terminal_nonzero=True,
        new_definition_ids=["ND0423"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",factorial_quotient_interpretation=False,
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def exponential_weights_source_pins():
    result = series_linear_combination_source_pins()
    expected = {
        "scripts/sqrt2_power_series_linear_combination.py":"068c70dd150d2057d95d62bd10aba40b9df7d00aeadfd1c8eec7ce97dd0ffa4a",
        "scripts/sqrt2_power_weighted_series_trace.py":"34b97b7cc1a0391e74b01db46847dd78260e751b47312acdd64fea5281958bbc",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_exponential_weights.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExponentialWeightsError("weight source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _scaled_extension(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def decoded(t):
        relation = apply(specialize(t,"scaling",*t.terms(("j","x","x","v"))),t.hyp("bound"),t.hyp("input"),t.hyp("input"),t.hyp("middle"))
        preserved = apply(specialize(t,"preserved",*t.terms(("j","v"))),t.hyp("bound"),t.hyp("middle"))
        same = apply(specialize(t,"beta_unique",*t.terms(W+("j","y","v"))),t.hyp("output"),preserved)
        return _chain(same,EqSym(specialize(t,"one_mul",t.term("v"))),relation,
            CongAdd(EqRefl(Mul(t.term("f"),t.term("x"))),specialize(t,"mul_zero_left",t.term("x"))),instantiate(Axiom("PA3"),Mul(t.term("f"),t.term("x"))))
    return introduce(s,("f",)+O+C+W+("N","j","x","y"),("scaling","preserved","bound","input","output"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(C+("j",))),("v",),"middle",decoded))


def _scale_adjacent(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    def finish(t):
        f,g,y = t.terms(("f","g","y"))
        return _chain(t.hyp("first"),CongMul(EqRefl(f),t.hyp("adjacent")),
            EqSym(specialize(t,"mul_assoc",f,g,y)),CongMul(specialize(t,"mul_comm",f,g),EqRefl(y)),
            specialize(t,"mul_assoc",g,f,y),CongMul(EqRefl(g),EqSym(t.hyp("second"))))
    return introduce(s,("f","g","x","y","a","b"),("adjacent","first","second"),finish)


def _successor(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR,CongMul,CongS,EqRefl,EqSym,EqTrans,OrElim
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def factor(t):
        return Mul(Succ(t.term("N")),t.term("d"))
    def scaled(t,index,x,y,bound,old,new):
        return apply(specialize(t,"scaled_extension",factor(t),*t.terms(O+C+W),Succ(t.term("N")),index,x,y),
            t.hyp("scaling"),AndElimR(t.hyp("extension")),bound,old,new)
    def extended(t):
        def adjacent(u):
            def last(v):
                N,a,b = v.terms(("N","a","b"))
                first = _subst(v,registry,"BetaAt(wb,wc,slot,a)",v.hyp("last"),v.hyp("first"))
                second = _subst(v,registry,"BetaAt(wb,wc,slot,b)",CongS(v.hyp("last")),v.hyp("second"))
                ae = scaled(v,N,Succ(Zero()),a,specialize(v,"le_refl",Succ(N)),AndElimL(v.hyp("old_weights")),first)
                be = apply(specialize(v,"beta_unique",*v.terms(W),Succ(N),b,Succ(Zero())),second,AndElimL(v.hyp("extension")))
                value = EqTrans(ae,CongMul(EqRefl(factor(v)),EqSym(be)))
                return _subst(v,registry,"a=((S slot)*d)*b",EqSym(v.hyp("last")),value)
            def earlier(v):
                def values(w):
                    j,N,x,y,a,b = w.terms(("j","N","x","y","a","b"))
                    next_bound = apply(specialize(w,"succ_le_succ",Succ(j),N),w.hyp("earlier"))
                    ae = scaled(w,j,x,a,w.hyp("bound"),w.hyp("previous_x"),w.hyp("first"))
                    be = scaled(w,Succ(j),y,b,next_bound,w.hyp("previous_y"),w.hyp("second"))
                    old = apply(instantiate(AndElimR(w.hyp("old_weights")),j,x,y),w.hyp("earlier"),w.hyp("previous_x"),w.hyp("previous_y"))
                    return apply(specialize(w,"scale_adjacent",factor(w),Mul(Succ(j),w.term("d")),x,y,a,b),old,ae,be)
                return eliminate(v,specialize(v,"beta_exists",*v.terms(O+("j",))),("x",),"previous_x",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(O),Succ(w.term("j"))),("y",),"previous_y",values))
            lower = apply(specialize(u,"le_of_succ_le_succ",*u.terms(("j","N"))),u.hyp("bound"))
            cases = apply(specialize(u,"le_eq_or_lt",*u.terms(("j","N"))),lower)
            return OrElim(cases,last(u.hypothesis("last")),earlier(u.hypothesis("earlier")))
        graph = AndIntro(AndElimL(t.hyp("extension")),introduce(t,("j","a","b"),("bound","first","second"),adjacent))
        def nonzero(u):
            def last(v):
                at_end = _subst(v,registry,"BetaAt(wb,wc,slot,a)",v.hyp("last"),v.hyp("entry"))
                equal = apply(specialize(v,"beta_unique",*v.terms(W),Succ(v.term("N")),v.term("a"),Succ(Zero())),at_end,AndElimL(v.hyp("extension")))
                return _subst(v,registry,"~slot=0",EqSym(equal),specialize(v,"succ_ne_zero",Zero()))
            def earlier(v):
                def decoded(w):
                    j,N,x = w.terms(("j","N","x"))
                    lower = apply(specialize(w,"le_of_succ_le_succ",j,N),w.hyp("earlier"))
                    old_nonzero = apply(specialize(w,"old_nonzero",j,x),lower,w.hyp("previous"),w.hyp("denominator"))
                    factor_nonzero = apply(specialize(w,"mul_ne_zero",Succ(N),w.term("d")),specialize(w,"succ_ne_zero",N),w.hyp("denominator"))
                    product_nonzero = apply(specialize(w,"mul_ne_zero",factor(w),x),factor_nonzero,old_nonzero)
                    equal = scaled(w,j,x,w.term("a"),w.hyp("earlier"),w.hyp("previous"),w.hyp("entry"))
                    return _subst(w,registry,"~slot=0",EqSym(equal),product_nonzero)
                return eliminate(v,specialize(v,"beta_exists",*v.terms(O+("j",))),("x",),"previous",decoded)
            cases = apply(specialize(u,"le_eq_or_lt",u.term("j"),Succ(u.term("N"))),u.hyp("bound"))
            return OrElim(cases,last(u.hypothesis("last")),earlier(u.hypothesis("earlier")))
        positivity = introduce(t,("j","a"),("bound","entry","denominator"),nonzero)
        return witness(t.terms(W),AndIntro(graph,positivity))
    def combined(t):
        extension = specialize(t,"beta_extend",Succ(t.term("N")),*t.terms(C),Succ(Zero()))
        return eliminate(t,extension,W,"extension",extended)
    return introduce(s,("d","N")+O,("old_weights","old_nonzero"),lambda t:
        eliminate(t,specialize(t,"combination_exists",factor(t),Zero(),*t.terms(O+O),Succ(t.term("N"))),C,"scaling",combined))


def _root(s,target,registry):
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR,BotElim,EqSym,Ind
    from peano_lab.kernel.terms import Succ,Zero
    def base(t):
        def initial(u):
            adjacent = introduce(u,("j","a","b"),("bound","first","second"),lambda v:
                BotElim(apply(specialize(v,"lt_not_le",v.term("j"),Zero()),v.hyp("bound"),specialize(v,"zero_le",v.term("j")))))
            graph = AndIntro(AndElimL(u.hyp("extension")),adjacent)
            def positive(v):
                zero = apply(specialize(v,"le_zero",v.term("j")),v.hyp("bound"))
                at_zero = _subst(v,registry,"BetaAt(wb,wc,slot,a)",zero,v.hyp("entry"))
                same = apply(specialize(v,"beta_unique",*v.terms(W),Zero(),v.term("a"),Succ(Zero())),at_zero,AndElimL(v.hyp("extension")))
                return _subst(v,registry,"~slot=0",EqSym(same),specialize(v,"succ_ne_zero",Zero()))
            positivity = introduce(u,("j","a"),("bound","entry","denominator"),positive)
            return witness(u.terms(W),AndIntro(graph,positivity))
        return eliminate(t,specialize(t,"beta_extend",Zero(),Zero(),Zero(),Succ(Zero())),W,"extension",initial)
    def step(t):
        return eliminate(t,t.hyp("IH"),O,"previous",lambda u:
            apply(specialize(u,"successor",*u.terms(("d","N")+O)),AndElimL(u.hyp("previous")),AndElimR(u.hyp("previous"))))
    return introduce(s,("d",),(),lambda t:
        Ind(target.body.body,base(t),introduce(t,("N",),("IH",),step)))


def prove_exponential_weights(*,limits=None):
    registry,target = definition_registry(),frozen_exponential_weights_target()
    factories = {"scaled_extension":_scaled_extension,"scale_adjacent":_scale_adjacent,
        "successor":lambda s:_successor(s,registry),"CV022":lambda s:_root(s,target,registry)}
    return assemble_actual_certificate(code="CV022",target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=exponential_weights_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
