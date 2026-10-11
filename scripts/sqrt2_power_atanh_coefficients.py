"""CV025: construct every finite denominator-cleared atanh coefficient prefix.

Even coefficients are zero; odd i satisfy i*a=2*d. A positive common
multiple and actual beta extension construct the table. No logarithm,
infinite series, convergence or analytic correctness is in these definitions.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_series_power_vanishing import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,
    canonical,json_hash,read_archive,CONVOLUTION_ARCHIVE,
    definition_registry as vanishing_registry,series_power_vanishing_source_pins,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst

SCHEMA = "sqrt2-power-atanh-coefficients-v1"
DEFINITION_ROWS = (
    ("ND0424","NatAtanhCoefficient",("d","i","a"),
     "(exists j. i=2*j /\\ a=0) \\/ (exists j. i=S(2*j) /\\ i*a=2*d)",(),"e8118f7442853464911bf8a9c4a9b1c66630665fb2906b10142041ba93e525c0"),
    ("ND0425","NatAtanhPrefix",("d","ab","ac","N"),
     "forall i a. Lt(i,N) -> BetaAt(ab,ac,i,a) -> NatAtanhCoefficient(d,i,a)",
     ("Lt","BetaAt","NatAtanhCoefficient"),"e7cb2df284d35f4a933b0a7947ce8021f387fddecc69d1e4a35757620790753d"),
)
COMMON = "(forall t. (exists h. S t+S h=S B) -> exists k. d=(S t)*k)"
PREFIX = "NatAtanhPrefix(d,ab,ac,N)"
NAMED_SOURCE = "forall N. exists d ab ac. ~d=0 /\\ ("+PREFIX+" /\\ NatZeroBefore(ab,ac,N,1))"
TARGET_SHA256 = "6a235e46d7ff57ccd23bfc381f5c48d024d739de8f78abded4fd58a37aea8dbd"
HELPER_SOURCES = {
    "parity":"forall i. (exists j. i=2*j) \\/ (exists j. i=S(2*j))",
    "entry_exists":"forall B d i. "+COMMON+" -> Lt(i,B) -> exists a. NatAtanhCoefficient(d,i,a)",
    "prefix_exists":"forall B d. "+COMMON+" -> forall N. Le(N,B) -> exists ab ac. "+PREFIX,
    "prefix_zero":"forall d ab ac N. "+PREFIX+" -> NatZeroBefore(ab,ac,N,1)",
}
HELPER_TARGET_SHA256 = {
    "parity":"1dcb5f888a562ba4bcb4153dea18a68cfc2470a537c2055913a534ecbe5e0e95",
    "entry_exists":"028de1fae1824ebd3811568ad0427bf0e9afbf3f59e97e8faf6e0b3ab16bd62f",
    "prefix_exists":"62c4ba57cb298be650e0ba2d83d3c933f37a26c6e23fdf866cc7ab281e614967",
    "prefix_zero":"8f4044aa027e095d6521106476f0dcb89cc13dd10c96549bf627551c57457b94",
}
ARCHIVES = (CONVOLUTION_ARCHIVE,)
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "mul_comm":"forall a b. a*b=b*a",
    "succ_ne_zero":"forall a. ~S a=0",
    "zero_le":"forall a. Le(0,a)",
    "le_refl":"forall a. Le(a,a)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "le_zero":"forall a. Le(a,0) -> a=0",
    "le_eq_or_lt":"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "division":"forall a n. exists q r. n=(S a)*q+r /\\ Lt(r,S a)",
    "common_multiple":"forall B. exists d. ~d=0 /\\ "+COMMON,
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "beta_extend":"forall N b c v. exists eb ec. BetaAt(eb,ec,N,v) /\\ (forall j a. Lt(j,N) -> BetaAt(b,c,j,a) -> BetaAt(eb,ec,j,a))",
}
HELPER_DEPENDENCIES = {
    "parity":("division","le_of_succ_le_succ","le_eq_or_lt","le_zero"),
    "entry_exists":("parity","le_refl","le_succ","le_trans","add_comm","mul_assoc","mul_comm"),
    "prefix_exists":("lt_not_le","zero_le","le_refl","le_succ","le_trans","le_of_succ_le_succ","le_eq_or_lt","entry_exists","beta_extend","beta_exists","beta_unique"),
    "prefix_zero":("le_of_succ_le_succ","le_zero","succ_ne_zero"),
    "CV025":("common_multiple","prefix_exists","le_refl","prefix_zero"),
}


class AtanhCoefficientsError(ValueError):
    """Changed finite coefficient computation, common denominator or proof."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(vanishing_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    for identifier,name,parameters,source,dependencies,digest in DEFINITION_ROWS:
        if name in registry or identifier in {d.stable_id for d in registry.values()} or any(d["name"]==name or d["id"]==identifier for d in parent):
            raise AtanhCoefficientsError("finite atanh coefficient alias collision")
        formula = parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula))!=digest or not set(dependencies)<=registry.keys():
            raise AtanhCoefficientsError("finite atanh coefficient expansion or dependency changed")
        text = pretty_formula(formula,list(parameters))
        definition = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
            summary="Finite parity and exact division computation; no analytic correctness assertion.",
            category="irrationality_formal_series",conceptual_dependencies=dependencies)
        if definition.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
            raise AtanhCoefficientsError("finite atanh coefficient conservative roundtrip failed")
        registry[name] = definition
    return MappingProxyType(registry)


def frozen_atanh_coefficients_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise AtanhCoefficientsError("CV025 exact constructed coefficient target changed")
    return target


def source_contract():
    return dict(code="CV025",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_finite_coefficient_table_constructed=True,
        positive_common_denominator_constructed=True,zero_order_one_proved=True,
        even_values_zero=True,odd_values_exact_division=True,
        new_definition_ids=["ND0424","ND0425"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",logarithm_identity=False,
        factorial_quotient_interpretation=False,exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def atanh_coefficients_source_pins():
    result = series_power_vanishing_source_pins()
    expected = {
        "scripts/sqrt2_power_series_power_vanishing.py":"ea3e1d648fd35f5430d0e19c442bc06031b849c570ddd4b7315522eba468edab",
        "scripts/sqrt2_power_convolution_unit.py":"d058762fb3641d5bb1e90c764c4581801feeaf0a103901811b3e82dbe3db8f16",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_atanh_coefficients.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise AtanhCoefficientsError("atanh source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _parity(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongS,EqRefl,OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def decoded(t):
        one,two = Succ(Zero()),Succ(Succ(Zero()))
        q,r = t.terms(("q","r"))
        bound = apply(specialize(t,"le_of_succ_le_succ",r,one),AndElimR(t.hyp("division_data")))
        cases = apply(specialize(t,"le_eq_or_lt",r,one),bound)
        def odd(u):
            x = Mul(two,u.term("q"))
            equation = _chain(AndElimL(u.hyp("division_data")),CongAdd(EqRefl(x),u.hyp("one")),
                instantiate(Axiom("PA4"),x,Zero()),CongS(instantiate(Axiom("PA3"),x)))
            return OrIntroR(witness((u.term("q"),),equation))
        def even(u):
            r0 = apply(specialize(u,"le_zero",u.term("r")),apply(specialize(u,"le_of_succ_le_succ",u.term("r"),Zero()),u.hyp("less")))
            x = Mul(two,u.term("q"))
            equation = _chain(AndElimL(u.hyp("division_data")),CongAdd(EqRefl(x),r0),instantiate(Axiom("PA3"),x))
            return OrIntroL(witness((u.term("q"),),equation))
        return OrElim(cases,odd(t.hypothesis("one")),even(t.hypothesis("less")))
    return introduce(s,("i",),(),lambda t:eliminate(t,specialize(t,"division",Succ(Zero()),t.term("i")),("q","r"),"division_data",decoded))


def _entry_exists(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndIntro,CongAdd,CongMul,CongS,EqRefl,EqSym,OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two = Succ(Succ(Zero()))
    def even(t):
        return eliminate(t,t.hyp("even"),("j",),"even_index",lambda u:
            witness((Zero(),),OrIntroL(witness((u.term("j"),),AndIntro(u.hyp("even_index"),EqRefl(Zero()))))))
    def odd(t):
        def index(u):
            i,B = u.terms(("i","B"))
            bound = apply(specialize(u,"le_trans",i,Succ(i),B),apply(specialize(u,"le_succ",i,i),specialize(u,"le_refl",i)),u.hyp("bound"))
            def gap(v):
                i,g,j,B = v.terms(("i","g","j","B"))
                tj = Mul(two,j)
                equation = _chain(instantiate(Axiom("PA4"),Succ(tj),g),
                    CongS(specialize(v,"add_comm",Succ(tj),g)),
                    CongS(CongAdd(EqRefl(g),EqSym(v.hyp("odd_index")))),CongS(v.hyp("gap")))
                divisible = apply(specialize(v,"common",tj),witness((g,),equation))
                def quotient(w):
                    i,k,d = w.terms(("i","k","d"))
                    ik = _chain(CongMul(w.hyp("odd_index"),EqRefl(k)),EqSym(w.hyp("divisible")))
                    value = _chain(EqSym(specialize(w,"mul_assoc",i,two,k)),
                        CongMul(specialize(w,"mul_comm",i,two),EqRefl(k)),specialize(w,"mul_assoc",two,i,k),CongMul(EqRefl(two),ik))
                    return witness((Mul(two,k),),OrIntroR(witness((w.term("j"),),AndIntro(w.hyp("odd_index"),value))))
                return eliminate(v,divisible,("k",),"divisible",quotient)
            return eliminate(u,bound,("g",),"gap",gap)
        return eliminate(t,t.hyp("odd"),("j",),"odd_index",index)
    return introduce(s,("B","d","i"),("common","bound"),lambda t:
        OrElim(specialize(t,"parity",t.term("i")),even(t.hypothesis("even")),odd(t.hypothesis("odd"))))


def _prefix_exists(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,EqSym,Ind,OrElim
    from peano_lab.kernel.terms import Succ,Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("i","a"),("index","entry"),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("i"),Zero()),u.hyp("index"),specialize(u,"zero_le",u.term("i"))))))
    def successor(t):
        def extended(u):
            def entry(v):
                lower = apply(specialize(v,"le_of_succ_le_succ",*v.terms(("i","N"))),v.hyp("index"))
                cases = apply(specialize(v,"le_eq_or_lt",*v.terms(("i","N"))),lower)
                def last(w):
                    shifted = _subst(w,registry,"BetaAt(ab,ac,slot,a)",w.hyp("last"),w.hyp("entry"))
                    equal = apply(specialize(w,"beta_unique",*w.terms(("ab","ac","N","v","a"))),AndElimL(w.hyp("extension")),shifted)
                    value = _subst(w,registry,"NatAtanhCoefficient(d,N,slot)",equal,w.hyp("coefficient"))
                    return _subst(w,registry,"NatAtanhCoefficient(d,slot,a)",EqSym(w.hyp("last")),value)
                def earlier(w):
                    def old(x):
                        preserved = apply(instantiate(AndElimR(x.hyp("extension")),*x.terms(("i","z"))),x.hyp("earlier"),x.hyp("old_value"))
                        equal = apply(specialize(x,"beta_unique",*x.terms(("ab","ac","i","z","a"))),preserved,x.hyp("entry"))
                        value = apply(specialize(x,"old",*x.terms(("i","z"))),x.hyp("earlier"),x.hyp("old_value"))
                        return _subst(x,registry,"NatAtanhCoefficient(d,i,slot)",equal,value)
                    return eliminate(w,specialize(w,"beta_exists",*w.terms(("ob","oc","i"))),("z",),"old_value",old)
                return OrElim(cases,last(v.hypothesis("last")),earlier(v.hypothesis("earlier")))
            return witness(u.terms(("ab","ac")),introduce(u,("i","a"),("index","entry"),entry))
        N,B = t.terms(("N","B"))
        old_bound = apply(specialize(t,"le_trans",N,Succ(N),B),apply(specialize(t,"le_succ",N,N),specialize(t,"le_refl",N)),t.hyp("bound"))
        return eliminate(t,apply(t.hyp("IH"),old_bound),("ob","oc"),"old",lambda u:
            eliminate(u,apply(specialize(u,"entry_exists",*u.terms(("B","d","N"))),u.hyp("common"),u.hyp("bound")),("v",),"coefficient",lambda v:
                eliminate(v,specialize(v,"beta_extend",*v.terms(("N","ob","oc","v"))),("ab","ac"),"extension",extended)))
    motive = target.body.body.right.body
    return introduce(s,("B","d"),("common",),lambda t:
        Ind(motive,introduce(t,(),("bound",),base),introduce(t,("N",),("IH",),lambda u:introduce(u,(),("bound",),successor))))


def _prefix_zero(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,EqSym,EqTrans,OrElim
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        def inside(u):
            value = apply(specialize(u,"prefix",*u.terms(("i","a"))),AndElimL(u.hyp("inside")),AndElimR(u.hyp("inside")))
            def odd(v):
                def decoded(w):
                    i0 = apply(specialize(w,"le_zero",w.term("i")),apply(specialize(w,"le_of_succ_le_succ",w.term("i"),Zero()),w.hyp("index")))
                    contradiction = apply(specialize(w,"succ_ne_zero",Mul(Succ(Succ(Zero())),w.term("j"))),EqTrans(EqSym(AndElimL(w.hyp("odd_data"))),i0))
                    return BotElim(contradiction)
                return eliminate(v,v.hyp("odd"),("j",),"odd_data",decoded)
            return OrElim(value,eliminate(u.hypothesis("even"),u.hypothesis("even").hyp("even"),("j",),"even_data",lambda v:AndElimR(v.hyp("even_data"))),odd(u.hypothesis("odd")))
        return OrElim(t.hyp("padded"),inside(t.hypothesis("inside")),AndElimR(t.hypothesis("outside").hyp("outside")))
    return introduce(s,("d","ab","ac","N"),("prefix",),lambda t:introduce(t,("i","a"),("index","padded"),finish))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def denominator(t):
        constructor = apply(specialize(t,"prefix_exists",*t.terms(("N","d"))),AndElimR(t.hyp("denominator")))
        prefix = apply(instantiate(constructor,t.term("N")),specialize(t,"le_refl",t.term("N")))
        def chosen(u):
            zero = apply(specialize(u,"prefix_zero",*u.terms(("d","ab","ac","N"))),u.hyp("prefix"))
            return witness(u.terms(("d","ab","ac")),conjunction(AndElimL(u.hyp("denominator")),u.hyp("prefix"),zero))
        return eliminate(t,prefix,("ab","ac"),"prefix",chosen)
    return introduce(s,("N",),(),lambda t:eliminate(t,specialize(t,"common_multiple",t.term("N")),("d",),"denominator",denominator))


def prove_atanh_coefficients(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"parity":_parity,"entry_exists":_entry_exists,
        "prefix_exists":lambda s:_prefix_exists(s,parse_named(HELPER_SOURCES["prefix_exists"],registry=registry),registry),
        "prefix_zero":_prefix_zero,"CV025":_root}
    return assemble_actual_certificate(code="CV025",target=frozen_atanh_coefficients_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=atanh_coefficients_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
