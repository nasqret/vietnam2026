"""CV060: actual weighted accumulation evaluates to its finite weighted sum.

Construct the accumulation, source-row values, their pointwise products with
the weights, and a sum which is an actual evaluation of every terminal row.
No power-row, convergence, or analytic-composition premise is used.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_row_horner_values import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as row_registry,row_horner_values_source_pins,
    NAMED_SOURCE as ROW_SOURCE,HELPER_SOURCES as ROW_HELPERS,ENDPOINT_SOURCES as ROW_ENDPOINTS,
)
from sqrt2_power_finite_composition_euler import (
    definition_registry as composition_registry,finite_composition_euler_source_pins,
    HELPER_SOURCES as COMPOSITION_HELPERS,
)
from sqrt2_power_weighted_series_scaling import COMPOSITION_ARCHIVE
from sqrt2_power_weighted_series_trace import NAMED_SOURCE as WEIGHTED_SOURCE
from sqrt2_power_horner_linearity import horner_linearity_source_pins,HELPER_SOURCES as LINEAR_HELPERS
from sqrt2_power_sum_linearity import ENDPOINT_SOURCES as SUM_ENDPOINTS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-weighted-accumulation-evaluation-v1"
P,R,W,V,Z = ("pb","pc","qb","qc"),("rb","rc","sb","sc"),("wb","wc"),("vb","vc"),("zb","zc")
U,O,C = ("ub","uc"),("ob","oc"),("cb","cc")
PARAMETERS = ("H","t")+W+P+("K",)
OUTPUTS = R+V+Z+("s",)
FIXED = ("H","t")+W+P+R+V+Z+("K",)
TRACE = "NatWeightedSeriesTrace("+",".join(("H",)+W+P+R+("K",))+")"
ROW_VALUES = "NatRowHornerPrefix("+",".join(P+("t","H")+V+("K",))+")"


def product(codes,length="K"):
    return "NatPointwiseProductPrefix("+",".join(W+V+codes+(length,))+")"


def row(codes,index,values):
    return "NatPowerRow("+",".join(codes+(index,)+values)+")"


def value(codes,y):
    return "NatHornerValue("+",".join(codes+("t","H",y))+")"


DEFINITION = ("ND0439","NatPointwiseProductPrefix",W+V+Z+("K",),
    "forall i w v z. Lt(i,K) -> BetaAt(wb,wc,i,w) -> BetaAt(vb,vc,i,v) -> BetaAt(zb,zc,i,z) -> z=w*v",
    ("Lt","BetaAt"),"1848350247f45138ced109e672b88a375625f870646cbb016772eb3fb1cffcf3")
ALL_ROWS = "forall k ub uc y s. Le(k,K) -> "+row(R,"k",U)+" -> "+value(U,"y")+" -> Sum(zb,zc,k,s) -> y=s"
FINAL = "forall ub uc. "+row(R,"K",U)+" -> "+value(U,"s")
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". exists "+" ".join(OUTPUTS)+". "+TRACE+" /\\ ("+ROW_VALUES+" /\\ ("+product(Z)+" /\\ (Sum(zb,zc,K,s) /\\ ("+FINAL+"))))"
TARGET_SHA256 = "f1e9ea342059786ba3af115a2f4d0613913410b92f8bc7dbd138144349c3b7b4"
HELPER_SOURCES = {
    "linear_value":"forall alpha beta gamma ab ac bb bc cb cc t H x y z. NatLinearTriple(alpha,beta,gamma,ab,ac,bb,bc,cb,cc,H) -> NatHornerValue(ab,ac,t,H,x) -> NatHornerValue(bb,bc,t,H,y) -> NatHornerValue(cb,cc,t,H,z) -> gamma*z=alpha*x+beta*y",
    "zero_value":"forall ub uc t H y. NatZeroPrefix(ub,uc,H) -> "+value(U,"y")+" -> y=0",
    "products_extend":"forall "+" ".join(W+V+O+("K",))+". "+product(O)+" -> exists zb zc. "+product(Z,"S K"),
    "products_exists":"forall "+" ".join(W+V+("K",))+". exists zb zc. "+product(Z),
    "all_rows":"forall "+" ".join(FIXED)+". "+TRACE+" -> "+ROW_VALUES+" -> "+product(Z)+" -> "+ALL_ROWS,
}
HELPER_TARGET_SHA256 = {
    "linear_value":"2c102bc1610ca118a31cd1416236bde770793716853f10f48c576c869076b808",
    "zero_value":"4ee7d982e97722a9cd92661a4feab68d499089c260af221d9bbda259679acb0b",
    "products_extend":"e1f2cd2db0f4a981751701a9df7d4e4da2e44e1e5e88c377611a6c8cec1f8e8e",
    "products_exists":"fb18578c1b1604b66a844424fac099d101634c84752d44b722201aa4e6294e9b",
    "all_rows":"ec3da59049b79136520cf9eae31848fe8496f0a917b25d797a67b94b6ecee8be",
}
ROW_ARCHIVE = dict(case="CV059",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-row-horner-values-v1/generation-process.json.gz",
    bytes=26614,sha256="1ed39e0a0a1f0cbaed5c0db773b6a453fa61ddbcbaa0f7f524b2e676acbce6cc",
    raw_bytes=390512,raw_sha256="43dfe40305d5d54031e94050bdf4ecea4e131de8d6f1bc5b13064a917574fe26",
    bundle_bytes=214811,bundle_sha256="e1a375ba40571463ff4d30a66216e348605613a70967c04b32c9402c9d9af06a",
    nodes=115,root=114,target_ast_sha256="b2b6e620f12b84c498f8ab5190550c6d41534be74a012313e03297548ed9eefc")
LINEAR_ARCHIVE = dict(case="CV035",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-linearity-v1/generation-process.json.gz",
    bytes=22811,sha256="61c93f013242097aa5d3d738e8cca187600ef116b5a6a0f17ff6d176b390bbff",
    raw_bytes=342638,raw_sha256="9f6a2cfdba404e9243092613904591aca884db7b3db03b54db5e6af374f73c6c",
    bundle_bytes=200908,bundle_sha256="77477ae2e7d646455c9401f03bef0c0e798ef50fd7286954b938c74074793b65",
    nodes=111,root=110,target_ast_sha256="ad3d9e7f204d9e713be5a888404827c60c7a6e4a2ceca04adb2deb516e9682df")
ARCHIVES = (ROW_ARCHIVE,COMPOSITION_ARCHIVE,LINEAR_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:ROW_ENDPOINTS[name] for name in ("row_decode","beta_exists","beta_unique","beta_extend","le_refl","zero_le","lt_not_le","le_of_succ_le_succ","le_eq_or_lt")},
    "row_values_exists":ROW_SOURCE,"value_exists":ROW_HELPERS["value_exists"],"row_value_entry":ROW_HELPERS["entry"],
    "horner_linear":LINEAR_HELPERS["all_rows"],"weighted_exists":WEIGHTED_SOURCE,
    "weighted_zero":COMPOSITION_HELPERS["weighted_zero"],"weighted_graph":COMPOSITION_HELPERS["weighted_graph"],
    "one_mul":"forall a. 1*a=a","mul_zero_left":"forall a. 0*a=0",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)","le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    **{name:SUM_ENDPOINTS[name][1] for name in ("sum_exists","sum_zero","sum_decompose")},
}
ENDPOINT_OWNERS = {name:"CV059" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(horner_linear="CV035",**{name:"CV021" for name in ("weighted_exists","weighted_zero","weighted_graph","one_mul","mul_zero_left","le_succ","le_trans","sum_exists","sum_zero","sum_decompose")})
HELPER_DEPENDENCIES = {
    "linear_value":("horner_linear","le_refl"),
    "zero_value":("beta_unique","one_mul","mul_zero_left","linear_value"),
    "products_extend":("beta_exists","beta_unique","beta_extend","le_of_succ_le_succ","le_eq_or_lt"),
    "products_exists":("zero_le","lt_not_le","products_extend"),
    "all_rows":("weighted_zero","zero_value","sum_zero","sum_decompose","row_decode","value_exists","beta_exists","le_refl","le_succ","le_trans",
        "row_value_entry","weighted_graph","linear_value","one_mul"),
    "CV060":("row_values_exists","products_exists","weighted_exists","sum_exists","value_exists","all_rows","le_refl"),
}


class WeightedAccumulationEvaluationError(ValueError):
    """Changed actual weighted computation, values or separate finite sum."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    result = dict(row_registry())
    for name,d in composition_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise WeightedAccumulationEvaluationError("shared composition/evaluation definition mismatch")
        result[name] = d
    identifier,name,params,source,deps,digest = DEFINITION
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    if name in result or identifier in {d.stable_id for d in result.values()} or any(d["id"]==identifier or d["name"]==name for d in parent):
        raise WeightedAccumulationEvaluationError("pointwise product definition collision")
    formula = parse_named(source,params,result)
    if json_hash(encode_formula(formula))!=digest or not set(deps)<=result.keys():
        raise WeightedAccumulationEvaluationError("pointwise product definition or dependency changed")
    text = pretty_formula(formula,list(params))
    d = _definition(stable_id=identifier,name=name,parameters=params,template_source=text,
        summary="Pointwise product of decoded entries only; no sum or evaluation identity.",category="irrationality_formal_series",conceptual_dependencies=deps)
    if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula:
        raise WeightedAccumulationEvaluationError("pointwise product failed exact conservative roundtrip")
    result[name] = d
    return MappingProxyType(result)


def frozen_weighted_accumulation_evaluation_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=9 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise WeightedAccumulationEvaluationError("CV060 exact constructed weighted evaluation target changed")
    return target


def source_contract():
    return dict(code="CV060",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_weighted_trace_constructed=True,actual_source_row_values_constructed=True,
        actual_pointwise_products_and_sum_constructed=True,every_terminal_row_has_the_sum_as_its_horner_value=True,
        arbitrary_source_rows_and_weights=True,zero_multiplier_and_empty_lengths_allowed=True,
        new_definition_ids=["ND0439"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def weighted_accumulation_evaluation_source_pins():
    result = row_horner_values_source_pins()
    for supplied in (finite_composition_euler_source_pins(),horner_linearity_source_pins()):
        for name,pin in supplied.items():
            if name in result and result[name]!=pin:
                raise WeightedAccumulationEvaluationError("shared proof-source pin mismatch")
            result[name] = pin
    expected = {"scripts/sqrt2_power_row_horner_values.py":"9f5b54f5e26ea099916504c3e8f57f31301f49373d074412465c555410de3b91",
        "scripts/sqrt2_power_finite_composition_euler.py":"3f946b7f2c1d0f88fd4f5fba37d3ff5ff2ec76153e5abe288c95f4be5fb5ec9b",
        "scripts/sqrt2_power_horner_linearity.py":"914a08b5ebdf667c247330ca79d99e81956ff47a3c0c77195435ae8cc2113618",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_weighted_accumulation_evaluation.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise WeightedAccumulationEvaluationError("weighted evaluation source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _linear_value(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    params = ("alpha","beta","gamma","ab","ac","bb","bc","cb","cc","t","H","x","y","z")
    def chosen(t):
        invariant = apply(specialize(t,"horner_linear",*t.terms(params[:11]+("ahb","ahc","bhb","bhc","chb","chc"))),
            t.hyp("graph"),AndElimL(t.hyp("traceA")),AndElimL(t.hyp("traceB")),AndElimL(t.hyp("traceC")))
        return apply(instantiate(invariant,*t.terms(("H","x","y","z"))),specialize(t,"le_refl",t.term("H")),
            AndElimR(t.hyp("traceA")),AndElimR(t.hyp("traceB")),AndElimR(t.hyp("traceC")))
    return introduce(s,params,("graph","valueA","valueB","valueC"),lambda t:
        eliminate(t,t.hyp("valueA"),("ahb","ahc"),"traceA",lambda u:
            eliminate(u,u.hyp("valueB"),("bhb","bhc"),"traceB",lambda v:
                eliminate(v,v.hyp("valueC"),("chb","chc"),"traceC",chosen))))


def _zero_value(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        def entry(u):
            z0 = apply(specialize(u,"beta_unique",*u.terms(U+("i","z")),Zero()),u.hyp("third"),apply(specialize(u,"zeros",u.term("i")),u.hyp("bound")))
            return _chain(specialize(u,"one_mul",u.term("z")),z0,EqSym(instantiate(Axiom("PA3"),Zero())),
                CongAdd(EqSym(specialize(u,"mul_zero_left",u.term("a"))),EqSym(specialize(u,"mul_zero_left",u.term("b")))))
        graph = introduce(t,("i","a","b","z"),("bound","first","second","third"),entry)
        linear = apply(specialize(t,"linear_value",Zero(),Zero(),Succ(Zero()),*t.terms(U+U+U+("t","H","y","y","y"))),graph,t.hyp("value"),t.hyp("value"),t.hyp("value"))
        zero = specialize(t,"mul_zero_left",t.term("y"))
        return _chain(EqSym(specialize(t,"one_mul",t.term("y"))),linear,CongAdd(zero,zero),instantiate(Axiom("PA3"),Zero()))
    return introduce(s,U+("t","H","y"),("zeros","value"),chosen)


def _products_extend(s,registry):
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
                vv = apply(specialize(v,"beta_unique",*v.terms(V+("K","v","v0"))),moved(V,"v"),v.hyp("row_value"))
                zz = apply(specialize(v,"beta_unique",*v.terms(Z+("K","z")),Mul(*v.terms(("w0","v0")))),moved(Z,"z"),AndElimL(v.hyp("extension")))
                return _chain(zz,CongMul(EqSym(ww),EqSym(vv)))
            def earlier(v):
                def decoded(w):
                    relation = apply(specialize(w,"old",*w.terms(("i","w","v","d"))),w.hyp("earlier"),w.hyp("entry_w"),w.hyp("entry_v"),w.hyp("old_entry"))
                    kept = apply(instantiate(AndElimR(w.hyp("extension")),*w.terms(("i","d"))),w.hyp("earlier"),w.hyp("old_entry"))
                    same = apply(specialize(w,"beta_unique",*w.terms(Z+("i","z","d"))),w.hyp("entry_z"),kept)
                    return _chain(same,relation)
                return eliminate(v,specialize(v,"beta_exists",*v.terms(O+("i",))),("d",),"old_entry",decoded)
            bound = apply(specialize(u,"le_of_succ_le_succ",*u.terms(("i","K"))),u.hyp("bound"))
            cases = apply(specialize(u,"le_eq_or_lt",*u.terms(("i","K"))),bound)
            return OrElim(cases,last(u.hypothesis("last")),earlier(u.hypothesis("earlier")))
        return witness(t.terms(Z),introduce(t,("i","w","v","z"),("bound","entry_w","entry_v","entry_z"),entry))
    return introduce(s,W+V+O+("K",),("old",),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(W+("K",))),("w0",),"weight",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(V+("K",))),("v0",),"row_value",lambda v:
                eliminate(v,specialize(v,"beta_extend",*v.terms(("K",)+O),Mul(*v.terms(("w0","v0")))),Z,"extension",extended))))


def _products_exists(s,target):
    from peano_lab.kernel.proofs import BotElim,Ind
    from peano_lab.kernel.terms import Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("i","w","v","z"),("bound","first","second","third"),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("i"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("i"))))))
    def successor(t):
        return eliminate(t,t.hyp("IH"),O,"old",lambda u:apply(specialize(u,"products_extend",*u.terms(W+V+O+("K",))),u.hyp("old")))
    motive = target
    for _ in W+V+("K",):
        motive = motive.body
    return introduce(s,W+V,(),lambda t:Ind(motive,base(t),introduce(t,("K",),("IH",),successor)))


def _all_rows(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def base(t):
        zeros = apply(specialize(t,"weighted_zero",*t.terms(("H",)+W+P+R+("K",)+U)),t.hyp("trace"),t.hyp("row"))
        y0 = apply(specialize(t,"zero_value",*t.terms(U+("t","H","y"))),zeros,t.hyp("value"))
        s0 = apply(specialize(t,"sum_zero",*t.terms(Z+("s",))),t.hyp("sum"))
        return _chain(y0,EqSym(s0))
    def successor(t):
        def chosen(u):
            k,K = u.terms(("k","K"))
            bound = apply(specialize(u,"le_trans",k,Succ(k),K),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            previous = apply(specialize(u,"IH",*u.terms(O+("x","n"))),bound,u.hyp("previous"),u.hyp("old_value"),field(u.hyp("sum_data"),1,3))
            source = apply(specialize(u,"row_value_entry",*u.terms(P+("t","H")+V+("K","k")+C+("v0",))),
                u.hyp("row_values"),u.hyp("bound"),u.hyp("source"),u.hyp("source_value"))
            term = apply(specialize(u,"products",*u.terms(("k","w","v0","a"))),u.hyp("bound"),u.hyp("weight"),source,field(u.hyp("sum_data"),0,3))
            graph = apply(specialize(u,"weighted_graph",*u.terms(("H",)+W+P+R+("K","k")+C+O+U+("w",))),
                u.hyp("trace"),u.hyp("bound"),u.hyp("source"),u.hyp("previous"),u.hyp("row"),u.hyp("weight"))
            linear = apply(specialize(u,"linear_value",Succ(Zero()),u.term("w"),Succ(Zero()),*u.terms(O+C+U+("t","H","x","v0","y"))),
                graph,u.hyp("old_value"),u.hyp("source_value"),u.hyp("value"))
            return _chain(EqSym(specialize(u,"one_mul",u.term("y"))),linear,
                CongAdd(specialize(u,"one_mul",u.term("x")),EqRefl(Mul(*u.terms(("w","v0"))))),
                CongAdd(previous,EqSym(term)),EqSym(field(u.hyp("sum_data"),2,3)))
        return eliminate(t,apply(specialize(t,"sum_decompose",*t.terms(Z+("k","s"))),t.hyp("sum")),("a","n"),"sum_data",lambda u:
            eliminate(u,specialize(u,"row_decode",*u.terms(R+("k",))),O,"previous",lambda v:
                eliminate(v,specialize(v,"row_decode",*v.terms(P+("k",))),C,"source",lambda w:
                    eliminate(w,specialize(w,"value_exists",*w.terms(O+("t","H"))),("x",),"old_value",lambda z:
                        eliminate(z,specialize(z,"value_exists",*z.terms(C+("t","H"))),("v0",),"source_value",lambda a:
                            eliminate(a,specialize(a,"beta_exists",*a.terms(W+("k",))),("w",),"weight",chosen))))))
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.right.right.right.body
    return introduce(s,FIXED,("trace","row_values","products"),lambda t:Ind(motive,
        introduce(t,U+("y","s"),("bound","row","value","sum"),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,U+("y","s"),("bound","row","value","sum"),successor))))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL
    def chosen(t):
        def endpoint(u):
            def evaluated(v):
                invariant = apply(specialize(v,"all_rows",*v.terms(FIXED)),v.hyp("trace"),AndElimL(v.hyp("row_values")),v.hyp("products"))
                same = apply(instantiate(invariant,*v.terms(("K",)+U+("y","s"))),specialize(v,"le_refl",v.term("K")),v.hyp("row"),v.hyp("value"),v.hyp("sum"))
                return _subst(v,registry,"NatHornerValue(ub,uc,t,H,slot)",same,v.hyp("value"))
            return eliminate(u,specialize(u,"value_exists",*u.terms(U+("t","H"))),("y",),"value",evaluated)
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("trace"),AndElimL(t.hyp("row_values")),t.hyp("products"),t.hyp("sum"),introduce(t,U,("row",),endpoint)))
    return introduce(s,PARAMETERS,(),lambda t:
        eliminate(t,specialize(t,"row_values_exists",*t.terms(P+("t","H","K"))),V,"row_values",lambda u:
            eliminate(u,specialize(u,"products_exists",*u.terms(W+V+("K",))),Z,"products",lambda v:
                eliminate(v,specialize(v,"weighted_exists",*v.terms(("H",)+W+P+("K",))),R,"trace",lambda w:
                    eliminate(w,specialize(w,"sum_exists",*w.terms(Z+("K",))),("s",),"sum",chosen)))))


def prove_weighted_accumulation_evaluation(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV060",target=frozen_weighted_accumulation_evaluation_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"linear_value":_linear_value,"zero_value":_zero_value,"products_extend":lambda s:_products_extend(s,registry),
            "products_exists":lambda s:_products_exists(s,parse_named(HELPER_SOURCES["products_exists"],registry=registry)),
            "all_rows":lambda s:_all_rows(s,parse_named(HELPER_SOURCES["all_rows"],registry=registry)),"CV060":lambda s:_root(s,registry)},
        pins=weighted_accumulation_evaluation_source_pins,contract=source_contract(),limits=limits,new_induction_count=2)
