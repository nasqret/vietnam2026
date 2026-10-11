"""CV018: construct weighted natural prefixes and their convolution laws.

The pointwise relation is an output, not a premise. An ordinary beta-extension
induction constructs C[i]=alpha*A[i]+beta*B[i] at every index of the prefix.
Actual CV015 bodies then construct and relate the three convolution values.
"""
from hashlib import sha256

from sqrt2_power_convolution_linearity import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,definition_registry,convolution_linearity_source_pins,
    NAMED_SOURCE as LINEAR_SOURCE,CONVOLUTION_ARCHIVE,coefficient,
)
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst
from sqrt2_power_series_power_euler import LINEAR_ARCHIVE

SCHEMA = "sqrt2-power-series-linear-combination-v1"
P = ("alpha","beta","ab","ac","bb","bc","L")
C = ("cb","cc")
A,B,D = ("ab","ac","L"),("bb","bc","L"),("db","dc","M")
GRAPH = "NatLinearTriple(alpha,beta,1,ab,ac,bb,bc,cb,cc,L)"
COMBINATION_SOURCE = "forall "+" ".join(P)+". exists cb cc. "+GRAPH
CONVOLUTION_RESULT = "forall db dc M i. exists u v w. "+coefficient(A,D,"i","u")+" /\\ ("+coefficient(B,D,"i","v")+" /\\ ("+coefficient(C+("L",),D,"i","w")+" /\\ w=alpha*u+beta*v))"
NAMED_SOURCE = "forall "+" ".join(P)+". exists cb cc. "+GRAPH+" /\\ ("+CONVOLUTION_RESULT+")"
TARGET_SHA256 = "f7bac172808c99e0125de6a05eaa1bb261596422da0685f05dbeb18d5b9ac56b"
HELPER_SOURCES = {"combination_exists":COMBINATION_SOURCE}
HELPER_TARGET_SHA256 = {"combination_exists":"57ea51858a5814085f5ad87e9a32e373d339ec45a0b8c67ffcafed0adb6d4f55"}
ARCHIVES = (CONVOLUTION_ARCHIVE,LINEAR_ARCHIVE)
ENDPOINT_SOURCES = {
    "one_mul":"forall a. 1*a=a",
    "zero_le":"forall a. Le(0,a)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "le_eq_or_lt":"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "beta_extend":"forall N b c v. exists eb ec. BetaAt(eb,ec,N,v) /\\ (forall j a. Lt(j,N) -> BetaAt(b,c,j,a) -> BetaAt(eb,ec,j,a))",
    "convolution_linearity":LINEAR_SOURCE,
}
HELPER_DEPENDENCIES = {
    "combination_exists":("one_mul","zero_le","lt_not_le","le_of_succ_le_succ","le_eq_or_lt","beta_exists","beta_unique","beta_extend"),
    "CV018":("combination_exists","convolution_linearity","one_mul"),
}


class LinearCombinationError(ValueError):
    """Changed actual computation, target, source, dependency body or bound."""


def frozen_series_linear_combination_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LinearCombinationError("CV018 exact constructed linear-prefix target changed")
    return target


def source_contract():
    return dict(code="CV018",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_pointwise_relation_constructed=True,weighted_prefix_constructed=True,
        all_three_convolution_coefficients_constructed=True,arbitrary_weights_and_lengths=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",finite_composition_chain_rule=False,
        exp_composition_recurrence=False,analytic_limit_claim=False,closes_IR079=False,
        closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def series_linear_combination_source_pins():
    result = convolution_linearity_source_pins()
    expected = {
        "scripts/sqrt2_power_convolution_linearity.py":"0dea2d4d67beeb59c9345f35c302ce9a49d1936bd1251ffacb976def7fa93169",
        "scripts/sqrt2_power_convolution_unit.py":"d058762fb3641d5bb1e90c764c4581801feeaf0a103901811b3e82dbe3db8f16",
        "scripts/sqrt2_power_series_power_euler.py":"f00d1180a96ba497a5c961b850e660941d6c608d70ebc7071a51e53344b5205c",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_series_linear_combination.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise LinearCombinationError("linear-prefix source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _combination_exists(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,CongAdd,CongMul,EqRefl,EqSym,EqTrans,Ind,OrElim
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("i","x","y","z"),("bound","input_a","input_b","output"),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("i"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("i"))))))
    def step(t):
        def extended(u):
            def entry(v):
                def last(w):
                    alpha,beta,a,b,z = w.terms(("alpha","beta","a","b","z"))
                    inputs = tuple(_subst(w,registry,"BetaAt("+",".join(codes)+",slot,"+value+")",w.hyp("last"),w.hyp(label))
                        for codes,value,label in ((A[:2],"x","input_a"),(B[:2],"y","input_b"),(C,"z","output")))
                    ax = apply(specialize(w,"beta_unique",*w.terms(("ab","ac","L","a","x"))),w.hyp("value_a"),inputs[0])
                    by = apply(specialize(w,"beta_unique",*w.terms(("bb","bc","L","b","y"))),w.hyp("value_b"),inputs[1])
                    computed = Add(Mul(alpha,a),Mul(beta,b))
                    equal = apply(specialize(w,"beta_unique",*w.terms(C+("L",)),computed,z),AndElimL(w.hyp("extension")),inputs[2])
                    return _chain(specialize(w,"one_mul",z),EqSym(equal),CongAdd(CongMul(EqRefl(alpha),ax),CongMul(EqRefl(beta),by)))
                def earlier(w):
                    def old_value(x):
                        preserved = apply(instantiate(AndElimR(x.hyp("extension")),*x.terms(("i","h"))),x.hyp("earlier"),x.hyp("old_value"))
                        equal = apply(specialize(x,"beta_unique",*x.terms(C+("i","h","z"))),preserved,x.hyp("output"))
                        identity = apply(specialize(x,"old",*x.terms(("i","x","y","h"))),x.hyp("earlier"),x.hyp("input_a"),x.hyp("input_b"),x.hyp("old_value"))
                        return EqTrans(CongMul(EqRefl(Succ(Zero())),EqSym(equal)),identity)
                    return eliminate(w,specialize(w,"beta_exists",*w.terms(("ob","oc","i"))),("h",),"old_value",old_value)
                lower = apply(specialize(v,"le_of_succ_le_succ",*v.terms(("i","L"))),v.hyp("bound"))
                cases = apply(specialize(v,"le_eq_or_lt",*v.terms(("i","L"))),lower)
                return OrElim(cases,last(v.hypothesis("last")),earlier(v.hypothesis("earlier")))
            graph = introduce(u,("i","x","y","z"),("bound","input_a","input_b","output"),entry)
            return witness(u.terms(C),graph)
        def values(u):
            value = Add(Mul(u.term("alpha"),u.term("a")),Mul(u.term("beta"),u.term("b")))
            extension = specialize(u,"beta_extend",*u.terms(("L","ob","oc")),value)
            return eliminate(u,extension,C,"extension",extended)
        return eliminate(t,t.hyp("IH"),("ob","oc"),"old",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(("ab","ac","L"))),("a",),"value_a",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(("bb","bc","L"))),("b",),"value_b",values)))
    motive = target
    for _ in P:
        motive = motive.body
    return introduce(s,P[:-1],(),lambda t:Ind(motive,base(t),introduce(t,("L",),("IH",),step)))


def _root(s):
    from peano_lab.kernel.proofs import EqSym,EqTrans
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        def coefficients(u):
            def values(v):
                identity = EqTrans(EqSym(specialize(v,"one_mul",v.term("w"))),field(v.hyp("coefficients"),3,4))
                return witness(v.terms(("u","v","w")),conjunction(*(field(v.hyp("coefficients"),j,4) for j in range(3)),identity))
            data = apply(specialize(u,"convolution_linearity",*u.terms(P[:2]),Succ(Zero()),
                *u.terms(("ab","ac","bb","bc","cb","cc","L","db","dc","M","i"))),u.hyp("graph"))
            return eliminate(u,data,("u","v","w"),"coefficients",values)
        preservation = introduce(t,("db","dc","M","i"),(),coefficients)
        return witness(t.terms(C),conjunction(t.hyp("graph"),preservation))
    return introduce(s,P,(),lambda t:
        eliminate(t,specialize(t,"combination_exists",*t.terms(P)),C,"graph",chosen))


def prove_series_linear_combination(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"combination_exists":lambda s:_combination_exists(s,parse_named(COMBINATION_SOURCE,registry=registry),registry),"CV018":_root}
    return assemble_actual_certificate(code="CV018",target=frozen_series_linear_combination_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=series_linear_combination_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
