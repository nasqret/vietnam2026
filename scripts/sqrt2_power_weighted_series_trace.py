"""CV019: construct every finite weighted series-accumulation trace.

Input rows and weights are actual beta-coded tables. Accumulator row zero is
zero; row k+1 is row k plus weight[k] times input row k. No sum formula,
differentiation, power property or analytic interpretation is a definition.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_series_linear_combination import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,series_linear_combination_source_pins,
    definition_registry as linear_registry,COMBINATION_SOURCE,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_series_power_trace import (
    definition_registry as power_registry,series_power_trace_source_pins,
    HELPER_SOURCES as POWER_HELPERS,
)
from sqrt2_power_series_power_vanishing import POWER_ARCHIVE
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst

SCHEMA = "sqrt2-power-weighted-series-trace-v1"
Q = ("H","wb","wc","pb","pc","qb","qc")
B = Q[3:]
T,E = ("tb","tc","vb","vc"),("rb","rc","sb","sc")
U,V,W = ("ub","uc"),("eb","ec"),("fb","fc")


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def exists(names,source):
    return "exists "+" ".join(names)+". "+source


def row(codes,index,values):
    return "NatPowerRow("+",".join(codes+(index,)+values)+")"


def step(codes,index):
    return "NatWeightedSeriesStep("+",".join(Q+codes+(index,))+")"


def trace(codes,length):
    return "NatWeightedSeriesTrace("+",".join(Q+codes+(length,))+")"


def preserved(old,new,length):
    return forall(("i",)+U,"Lt(i,"+length+") -> "+row(old,"i",U)+" -> "+row(new,"i",U))


COMBINATION = "NatLinearTriple(1,w,1,eb,ec,ub,uc,fb,fc,H)"
DEFINITION_ROWS = (
    (419,"NatZeroPrefix",U+("H",),"forall i. Lt(i,H) -> BetaAt(ub,uc,i,0)",
     ("Lt","BetaAt"),"75cea016d0629fa88f865c8f963cdcbb382d43ef94cef48e87e30ba47033efaf"),
    (420,"NatWeightedSeriesStep",Q+T+("k",),exists(U+V+W+("w",),row(B,"k",U)+" /\\ ("+row(T,"k",V)+" /\\ ("+row(T,"S k",W)+" /\\ (BetaAt(wb,wc,k,w) /\\ "+COMBINATION+")))"),
     ("NatPowerRow","BetaAt","NatLinearTriple"),"d57be264647429157e10c65c422ef4a7b446898e2ce3a6482745df3d4f350ccb"),
    (421,"NatWeightedSeriesTrace",Q+T+("K",),"("+exists(U,row(T,"0",U)+" /\\ NatZeroPrefix(ub,uc,H)")+") /\\ ("+forall(("k",),"Lt(k,K) -> "+step(T,"k"))+")",
     ("NatPowerRow","NatZeroPrefix","Lt","NatWeightedSeriesStep"),"8992cf9708d273d4849c5027efea07928b6e4b72bed1f2462e7b65f7a90eb146"),
)
NAMED_SOURCE = forall(Q+("K",),exists(T,trace(T,"K")))
TARGET_SHA256 = "911c376cb25c2cb18aefd0e0b77325ea871669c2faefda9024ec48e53e0a0bbf"
HELPER_SOURCES = {
    "zero_exists":"forall H. exists ub uc. NatZeroPrefix(ub,uc,H)",
    "transport":forall(Q+T+E+("K",),"("+preserved(T,E,"S K")+") -> "+trace(T,"K")+" -> "+trace(E,"K")),
    "successor":forall(Q+T+("K",),trace(T,"K")+" -> "+exists(E,trace(E,"S K"))),
}
HELPER_TARGET_SHA256 = {
    "zero_exists":"7ba772c8c8483d5abb21f5e000e0a510a4b3c19fd09a010d29fcdf8f1245fec0",
    "transport":"6fe973c7c0fc3fabe3890694167e5303f48a0d7f6cb212bb0c6d509ac1ae3f90",
    "successor":"73a78f418f9380ebeefa8ecdd2d2d892ab044bac49d1ac846e29cf98aedafe3c",
}
COMBINATION_ARCHIVE = dict(case="CV018",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-series-linear-combination-v1/generation-process.json.gz",
    bytes=24657,sha256="8b20ea2b77e3ea5833f506e2f042a1ba06ef0f555ca7150693d2b3da1b536e84",
    raw_bytes=460084,raw_sha256="7c7b6334162572a5673edc1a1aeac3c0403d1511fae460645f98fe5ba551dc84",
    bundle_bytes=277534,bundle_sha256="5b951b467a3ba0decc2263327cdb596869bc977f11ed2a58fabd53aa3a7bfdc6",
    nodes=125,root=124,target_ast_sha256="f7bac172808c99e0125de6a05eaa1bb261596422da0685f05dbeb18d5b9ac56b")
ARCHIVES = (CONVOLUTION_ARCHIVE,POWER_ARCHIVE,COMBINATION_ARCHIVE)
ENDPOINT_SOURCES = {
    "one_mul":"forall a. 1*a=a",
    "mul_zero_left":"forall a. 0*a=0",
    "zero_le":"forall a. Le(0,a)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "le_refl":"forall a. Le(a,a)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "le_eq_or_lt":"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "row_decode":POWER_HELPERS["decode"],"row_extend":POWER_HELPERS["extend"],
    "combination_exists":COMBINATION_SOURCE,
}
HELPER_DEPENDENCIES = {
    "zero_exists":("combination_exists","beta_exists","one_mul","mul_zero_left"),
    "transport":("zero_le","succ_le_succ","le_succ"),
    "successor":("row_decode","beta_exists","combination_exists","row_extend","transport","le_refl","le_of_succ_le_succ","le_eq_or_lt"),
    "CV019":("zero_exists","row_extend","zero_le","lt_not_le","successor"),
}


class WeightedSeriesTraceError(ValueError):
    """Changed conservative computation, target, actual body or resource cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(power_registry())
    for name,d in linear_registry().items():
        if name in registry and (registry[name].template_formula!=d.template_formula or registry[name].stable_id!=d.stable_id):
            raise WeightedSeriesTraceError("shared conservative definition mismatch")
        registry[name] = d
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids = {d["id"] for d in parent}|{d.stable_id for d in registry.values()}
    names = {d["name"] for d in parent}|set(registry)
    for number,name,parameters,source,dependencies,digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if name in names or identifier in ids or not set(dependencies)<=registry.keys():
            raise WeightedSeriesTraceError("weighted-trace definition collision or forward edge")
        formula = parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula))!=digest:
            raise WeightedSeriesTraceError("weighted-trace exact definition expansion changed")
        text = pretty_formula(formula,list(parameters))
        d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
            summary="Actual finite weighted table accumulation only; no sum, derivative or analytic correctness clause.",
            category="irrationality_formal_series",conceptual_dependencies=dependencies)
        if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
            raise WeightedSeriesTraceError("weighted-trace conservative expansion failed exact roundtrip")
        registry[name] = d
        ids.add(identifier)
        names.add(name)
    return MappingProxyType(registry)


def frozen_weighted_series_trace_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=8 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise WeightedSeriesTraceError("CV019 exact constructed weighted-trace target changed")
    return target


def source_contract():
    return dict(code="CV019",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_accumulator_rows_constructed=True,arbitrary_weights_and_input_rows=True,
        zero_initial_row_constructed=True,actual_weighted_step_at_each_index=True,
        new_definition_ids=["ND0419","ND0420","ND0421"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",source_rows_are_powers_assumed=False,
        finite_composition_chain_rule=False,exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def weighted_series_trace_source_pins():
    result = series_linear_combination_source_pins()
    for name,pin in series_power_trace_source_pins().items():
        if name in result and result[name]!=pin:
            raise WeightedSeriesTraceError("source dependency mismatch")
        result[name] = pin
    expected = {
        "scripts/sqrt2_power_series_linear_combination.py":"068c70dd150d2057d95d62bd10aba40b9df7d00aeadfd1c8eec7ce97dd0ffa4a",
        "scripts/sqrt2_power_series_power_trace.py":"557d393791fb527361bcffb4977b0e0bad591f98a426e12d1da461643cc39422",
        "scripts/sqrt2_power_series_power_vanishing.py":"ea3e1d648fd35f5430d0e19c442bc06031b849c570ddd4b7315522eba468edab",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_weighted_series_trace.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise WeightedSeriesTraceError("weighted-trace source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _zero_exists(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqSym
    from peano_lab.kernel.terms import Zero
    def chosen(t):
        def entry(u):
            def decoded(v):
                identity = apply(specialize(v,"graph",*v.terms(("i","a","a","z"))),v.hyp("bound"),v.hyp("input"),v.hyp("input"),v.hyp("output"))
                zero = _chain(EqSym(specialize(v,"one_mul",v.term("z"))),identity,
                    CongAdd(specialize(v,"mul_zero_left",v.term("a")),specialize(v,"mul_zero_left",v.term("a"))),instantiate(Axiom("PA3"),Zero()))
                return _subst(v,registry,"BetaAt(ub,uc,i,slot)",zero,v.hyp("output"))
            return eliminate(u,specialize(u,"beta_exists",Zero(),Zero(),u.term("i")),("a",),"input",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(U+("i",))),("z",),"output",decoded))
        return witness(t.terms(U),introduce(t,("i",),("bound",),entry))
    return introduce(s,("H",),(),lambda t:
        eliminate(t,specialize(t,"combination_exists",*(Zero() for _ in range(6)),t.term("H")),U,"graph",chosen))


def _transport(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ,Zero
    def finish(t):
        def initial(u):
            bound = apply(specialize(u,"succ_le_succ",Zero(),u.term("K")),specialize(u,"zero_le",u.term("K")))
            decoded = apply(specialize(u,"preserved",Zero(),*u.terms(U)),bound,AndElimL(u.hyp("initial")))
            return witness(u.terms(U),AndIntro(decoded,AndElimR(u.hyp("initial"))))
        first = eliminate(t,AndElimL(t.hyp("trace")),U,"initial",initial)
        def later(u):
            def decoded(v):
                k,K = v.terms(("k","K"))
                left_bound = apply(specialize(v,"le_succ",Succ(k),K),v.hyp("bound"))
                right_bound = apply(specialize(v,"succ_le_succ",Succ(k),K),v.hyp("bound"))
                left = apply(specialize(v,"preserved",k,*v.terms(V)),left_bound,field(v.hyp("step"),1,5))
                right = apply(specialize(v,"preserved",Succ(k),*v.terms(W)),right_bound,field(v.hyp("step"),2,5))
                return witness(v.terms(U+V+W+("w",)),conjunction(field(v.hyp("step"),0,5),left,right,field(v.hyp("step"),3,5),field(v.hyp("step"),4,5)))
            actual = apply(instantiate(AndElimR(u.hyp("trace")),u.term("k")),u.hyp("bound"))
            return eliminate(u,actual,U+V+W+("w",),"step",decoded)
        return AndIntro(first,introduce(t,("k",),("bound",),later))
    return introduce(s,Q+T+E+("K",),("preserved","trace"),finish)


def _successor(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR,EqSym,OrElim
    from peano_lab.kernel.terms import Succ,Zero
    def extended(t):
        def transported(u):
            return apply(specialize(u,"transport",*u.terms(Q+T+E+("K",))),AndElimR(u.hyp("extension")),u.hyp("trace"))
        def later(u):
            def last(v):
                current = apply(instantiate(AndElimR(v.hyp("extension")),v.term("K"),*v.terms(V)),specialize(v,"le_refl",Succ(v.term("K"))),v.hyp("current"))
                body = witness(v.terms(U+V+W+("w",)),conjunction(v.hyp("source"),current,AndElimL(v.hyp("extension")),v.hyp("weight"),v.hyp("combination")))
                return _subst(v,registry,step(E,"slot"),EqSym(v.hyp("last")),body)
            def earlier(v):
                return apply(instantiate(AndElimR(transported(v)),v.term("k")),v.hyp("earlier"))
            lower = apply(specialize(u,"le_of_succ_le_succ",*u.terms(("k","K"))),u.hyp("bound"))
            cases = apply(specialize(u,"le_eq_or_lt",*u.terms(("k","K"))),lower)
            return OrElim(cases,last(u.hypothesis("last")),earlier(u.hypothesis("earlier")))
        return witness(t.terms(E),AndIntro(AndElimL(transported(t)),introduce(t,("k",),("bound",),later)))
    def combined(t):
        extension = specialize(t,"row_extend",*t.terms(T),Succ(t.term("K")),*t.terms(W))
        return eliminate(t,extension,E,"extension",extended)
    def weighted(t):
        output = specialize(t,"combination_exists",Succ(Zero()),t.term("w"),*t.terms(V+U+("H",)))
        return eliminate(t,output,W,"combination",combined)
    return introduce(s,Q+T+("K",),("trace",),lambda t:
        eliminate(t,specialize(t,"row_decode",*t.terms(T+("K",))),V,"current",lambda u:
            eliminate(u,specialize(u,"row_decode",*u.terms(B+("K",))),U,"source",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(("wb","wc","K"))),("w",),"weight",weighted))))


def _root(s,target):
    from peano_lab.kernel.proofs import AndIntro,AndElimL,BotElim,Ind
    from peano_lab.kernel.terms import Zero
    def base(t):
        def initial(u):
            first = witness(u.terms(U),AndIntro(AndElimL(u.hyp("extension")),u.hyp("zeros")))
            rest = introduce(u,("k",),("bound",),lambda v:BotElim(apply(specialize(v,"lt_not_le",v.term("k"),Zero()),v.hyp("bound"),specialize(v,"zero_le",v.term("k")))))
            return witness(u.terms(T),AndIntro(first,rest))
        return eliminate(t,specialize(t,"zero_exists",t.term("H")),U,"zeros",lambda u:
            eliminate(u,specialize(u,"row_extend",*(Zero() for _ in range(5)),*u.terms(U)),T,"extension",initial))
    def successor(t):
        return eliminate(t,t.hyp("IH"),T,"old",lambda u:
            apply(specialize(u,"successor",*u.terms(Q+T+("K",))),u.hyp("old")))
    motive = target
    for _ in Q+("K",):
        motive = motive.body
    return introduce(s,Q,(),lambda t:Ind(motive,base(t),introduce(t,("K",),("IH",),successor)))


def prove_weighted_series_trace(*,limits=None):
    registry,target = definition_registry(),frozen_weighted_series_trace_target()
    factories = {"zero_exists":lambda s:_zero_exists(s,registry),"transport":_transport,
        "successor":lambda s:_successor(s,registry),"CV019":lambda s:_root(s,target)}
    return assemble_actual_certificate(code="CV019",target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=weighted_series_trace_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
