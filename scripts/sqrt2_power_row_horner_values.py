"""CV059: construct an actual Horner-value prefix for arbitrary coded rows.

The two conservative aliases describe finite computations only. Totality and
value extensionality are proved, without requiring rows to be powers and
without adding a weighted-sum or analytic identity to their definitions.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_finite_power_evaluation import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as base_registry,finite_power_evaluation_source_pins,
)
from sqrt2_power_horner_trace import NAMED_SOURCE as HORNER_SOURCE,HELPER_SOURCES as HORNER_HELPERS
from sqrt2_power_series_power_trace import HELPER_SOURCES as ROW_HELPERS
from sqrt2_power_exponential_weights import ENDPOINT_SOURCES as WEIGHT_ENDPOINTS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-row-horner-values-v1"
P,U,O,V,E = ("pb","pc","qb","qc"),("ub","uc"),("ob","oc"),("vb","vc"),("eb","ec")
FIXED = P+("t","H")
PARAMETERS = FIXED+("K",)


def graph(codes,length="K"):
    return "NatRowHornerPrefix("+",".join(FIXED+codes+(length,))+")"


def row(codes,index="k"):
    return "NatPowerRow("+",".join(P+(index,)+codes)+")"


def value(codes,y="y"):
    return "NatHornerValue("+",".join(codes+("t","H",y))+")"


def cell(codes,index="k"):
    return "exists ub uc y. "+row(U,index)+" /\\ ("+value(U)+" /\\ BetaAt("+",".join(codes+(index,"y"))+"))"


DEFINITIONS = (
    ("ND0437","NatHornerValue",("ab","ac","t","H","y"),
     "exists hb hc. NatScaledHornerTrace(ab,ac,t,H,hb,hc) /\\ BetaAt(hb,hc,H,y)",
     ("NatScaledHornerTrace","BetaAt"),"bbb9f8f844ecce855a545f4a4819801a344d4bfa0329fd4bd57b606f5126603b"),
    ("ND0438","NatRowHornerPrefix",FIXED+V+("K",),"forall k. Lt(k,K) -> "+cell(V),
     ("Lt","NatPowerRow","NatHornerValue","BetaAt"),"0e4d62a58576cde4e8911e5c6454132785a900cf684ce176fad14720fc866bec"),
)
EXTENSIONAL = "forall k ub uc y. Lt(k,K) -> "+row(U)+" -> "+value(U)+" -> BetaAt(vb,vc,k,y)"
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". exists vb vc. "+graph(V)+" /\\ ("+EXTENSIONAL+")"
TARGET_SHA256 = "b2b6e620f12b84c498f8ab5190550c6d41534be74a012313e03297548ed9eefc"
HELPER_SOURCES = {
    "value_exists":"forall ub uc t H. exists y. "+value(U),
    "value_unique":"forall ub uc t H x y. "+value(U,"x")+" -> "+value(U)+" -> x=y",
    "row_value_unique":"forall "+" ".join(P+("k",)+U+O+("t","H","x","y"))+". "+row(U)+" -> "+row(O)+" -> "+value(U,"x")+" -> "+value(O)+" -> x=y",
    "entry":"forall "+" ".join(FIXED+V+("K","k")+U+("y",))+". "+graph(V)+" -> Lt(k,K) -> "+row(U)+" -> "+value(U)+" -> BetaAt(vb,vc,k,y)",
    "successor":"forall "+" ".join(FIXED+V+("K",))+". "+graph(V)+" -> exists eb ec. "+graph(E,"S K"),
    "prefix_exists":"forall "+" ".join(PARAMETERS)+". exists vb vc. "+graph(V),
}
HELPER_TARGET_SHA256 = {
    "value_exists":"262bcc2b21866ebb25d6a192c39a028f9d2dc596579b2fd3385e09dbd45be55b",
    "value_unique":"1ad4e6db521ac5652fd78f1a5a1f184e049b0e0961441bb110d2ed0bfec5d502",
    "row_value_unique":"dac7ed7326765db8690f5e04ab30d7cd62c2602eef3d03f8b6d4122b5bddc1ce",
    "entry":"0ec60254acda23960521b9ffedae0950a36058252d12214833bb9fcdc0700ad5",
    "successor":"46b30618ada24ed2ddc4ed07a4f43335c6d373c275ca6cec027333a77732d527",
    "prefix_exists":"bf5dd25f8b85f5c0756a272384d5b98e45ba9c20a88e1189e0a689fd8ee6f552",
}
EVALUATION_ARCHIVE = dict(case="CV058",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-finite-power-evaluation-v2/generation-process.json.gz",
    bytes=69937,sha256="b286e5af2b40c60b90432ec16a9928f05b3efb598cfcefa8a9416697fb9ce1cf",
    raw_bytes=1815672,raw_sha256="40657724ebae92080d32e6678a283ca46467ddd7d383ad385ef0074e9a9d032a",
    bundle_bytes=1100998,bundle_sha256="fd1e3c3606821577e5c30e547c3fd17f3f7408f9fdb3083854024f19f3b756a1",
    nodes=253,root=252,target_ast_sha256="5106a1fb454a028ea96ed82dcd34c652807316d25e5009ec9a5c5f7191df4689")
ARCHIVES = (EVALUATION_ARCHIVE,)
ENDPOINT_SOURCES = {
    "horner_exists":HORNER_SOURCE,"horner_unique":HORNER_HELPERS["unique"],"row_decode":ROW_HELPERS["decode"],
    "beta_exists":WEIGHT_ENDPOINTS["beta_exists"],"beta_extend":WEIGHT_ENDPOINTS["beta_extend"],
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "le_refl":"forall a. Le(a,a)","zero_le":"forall a. Le(0,a)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "le_eq_or_lt":"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)",
}
ENDPOINT_OWNERS = {name:"CV058" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {
    "value_exists":("horner_exists","beta_exists"),
    "value_unique":("horner_unique","le_refl"),
    "row_value_unique":("beta_unique","value_unique"),
    "entry":("row_value_unique",),
    "successor":("row_decode","value_exists","beta_extend","le_of_succ_le_succ","le_eq_or_lt"),
    "prefix_exists":("zero_le","lt_not_le","successor"),
    "CV059":("prefix_exists","entry"),
}


class RowHornerValuesError(ValueError):
    """Changed actual-value graph, row decoding or conservative expansion."""


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
            raise RowHornerValuesError("row-value definition collision or forward dependency")
        formula = parse_named(source,params,result)
        if json_hash(encode_formula(formula))!=digest:
            raise RowHornerValuesError("row-value conservative expansion changed")
        text = pretty_formula(formula,list(params))
        d = _definition(stable_id=identifier,name=name,parameters=params,template_source=text,
            summary="Actual finite Horner computation and row decoding, not a polynomial or analytic identity.",
            category="irrationality_formal_series",conceptual_dependencies=deps)
        if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula:
            raise RowHornerValuesError("row-value definition failed exact conservative roundtrip")
        result[name] = d;ids.add(identifier);names.add(name)
    return MappingProxyType(result)


def frozen_row_horner_values_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise RowHornerValuesError("CV059 exact constructed row-value prefix target changed")
    return target


def source_contract():
    return dict(code="CV059",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_row_value_prefix_constructed=True,extensional_all_actual_values=True,
        arbitrary_encoded_rows_allowed=True,power_trace_required=False,
        zero_multiplier_and_empty_lengths_allowed=True,code_number_uniqueness=False,
        new_definition_ids=["ND0437","ND0438"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",weighted_accumulation_identity=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def row_horner_values_source_pins():
    result = finite_power_evaluation_source_pins()
    expected = {"scripts/sqrt2_power_finite_power_evaluation.py":"6c7c7cab1eceb7d10dcfa678ffa9f7245e4a197d966ee3050d547cf5ff804fac",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_row_horner_values.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise RowHornerValuesError("row-value source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _value_exists(s):
    from peano_lab.kernel.proofs import AndElimL,AndIntro
    def chosen(t):
        return witness((t.term("y"),),witness(t.terms(("hb","hc")),AndIntro(AndElimL(t.hyp("horner")),t.hyp("value"))))
    return introduce(s,U+("t","H"),(),lambda t:
        eliminate(t,specialize(t,"horner_exists",*t.terms(U+("t","H"))),("hb","hc"),"horner",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(("hb","hc","H"))),("y",),"value",chosen)))


def _value_unique(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def chosen(t):
        invariant = apply(specialize(t,"horner_unique",*t.terms(U+("t","H","hb","hc","ib","ic"))),
            AndElimL(t.hyp("first_data")),AndElimL(t.hyp("second_data")))
        return apply(instantiate(invariant,*t.terms(("H","x","y"))),specialize(t,"le_refl",t.term("H")),AndElimR(t.hyp("first_data")),AndElimR(t.hyp("second_data")))
    return introduce(s,U+("t","H","x","y"),("first","second"),lambda t:
        eliminate(t,t.hyp("first"),("hb","hc"),"first_data",lambda u:
            eliminate(u,u.hyp("second"),("ib","ic"),"second_data",chosen)))


def _row_value_unique(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def chosen(t):
        first = apply(specialize(t,"beta_unique",*t.terms(P[:2]+("k","ub","ob"))),AndElimL(t.hyp("rowU")),AndElimL(t.hyp("rowO")))
        second = apply(specialize(t,"beta_unique",*t.terms(P[2:]+("k","uc","oc"))),AndElimR(t.hyp("rowU")),AndElimR(t.hyp("rowO")))
        moved = _subst(t,registry,"NatHornerValue(slot,uc,t,H,x)",first,t.hyp("valueU"))
        moved = _subst(t,registry,"NatHornerValue(ob,slot,t,H,x)",second,moved)
        return apply(specialize(t,"value_unique",*t.terms(O+("t","H","x","y"))),moved,t.hyp("valueO"))
    return introduce(s,P+("k",)+U+O+("t","H","x","y"),("rowU","rowO","valueU","valueO"),chosen)


def _entry(s,registry):
    def chosen(t):
        same = apply(specialize(t,"row_value_unique",*t.terms(P+("k",)+O+U+("t","H","z","y"))),
            field(t.hyp("data"),0,3),t.hyp("row"),field(t.hyp("data"),1,3),t.hyp("value"))
        return _subst(t,registry,"BetaAt(vb,vc,k,slot)",same,field(t.hyp("data"),2,3))
    return introduce(s,FIXED+V+("K","k")+U+("y",),("graph","bound","row","value"),lambda t:
        eliminate(t,apply(specialize(t,"graph",t.term("k")),t.hyp("bound")),O+("z",),"data",chosen))


def _successor(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqSym,OrElim
    def chosen(t):
        def pointwise(u):
            def last(v):
                data = witness(v.terms(U+("y",)),conjunction(v.hyp("row"),v.hyp("value"),AndElimL(v.hyp("extension"))))
                return _subst(v,registry,cell(E,"slot"),EqSym(v.hyp("last")),data)
            def earlier(v):
                def decoded(w):
                    entry = apply(instantiate(AndElimR(w.hyp("extension")),*w.terms(("k","z"))),w.hyp("earlier"),field(w.hyp("old"),2,3))
                    return witness(w.terms(O+("z",)),conjunction(field(w.hyp("old"),0,3),field(w.hyp("old"),1,3),entry))
                return eliminate(v,apply(specialize(v,"graph",v.term("k")),v.hyp("earlier")),O+("z",),"old",decoded)
            lower = apply(specialize(u,"le_of_succ_le_succ",*u.terms(("k","K"))),u.hyp("bound"))
            cases = apply(specialize(u,"le_eq_or_lt",*u.terms(("k","K"))),lower)
            return OrElim(cases,last(u.hypothesis("last")),earlier(u.hypothesis("earlier")))
        return witness(t.terms(E),introduce(t,("k",),("bound",),pointwise))
    return introduce(s,FIXED+V+("K",),("graph",),lambda t:
        eliminate(t,specialize(t,"row_decode",*t.terms(P+("K",))),U,"row",lambda u:
            eliminate(u,specialize(u,"value_exists",*u.terms(U+("t","H"))),("y",),"value",lambda v:
                eliminate(v,specialize(v,"beta_extend",*v.terms(("K",)+V+("y",))),E,"extension",chosen))))


def _prefix_exists(s,target):
    from peano_lab.kernel.proofs import BotElim,Ind
    from peano_lab.kernel.terms import Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("k",),("bound",),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("k"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("k"))))))
    def successor(t):
        return eliminate(t,t.hyp("IH"),V,"graph",lambda u:apply(specialize(u,"successor",*u.terms(FIXED+V+("K",))),u.hyp("graph")))
    motive = target
    for _ in PARAMETERS:
        motive = motive.body
    return introduce(s,FIXED,(),lambda t:Ind(motive,base(t),introduce(t,("K",),("IH",),successor)))


def _root(s):
    from peano_lab.kernel.proofs import AndIntro
    def chosen(t):
        invariant = introduce(t,("k",)+U+("y",),("bound","row","value"),lambda u:
            apply(specialize(u,"entry",*u.terms(FIXED+V+("K","k")+U+("y",))),u.hyp("graph"),u.hyp("bound"),u.hyp("row"),u.hyp("value")))
        return witness(t.terms(V),AndIntro(t.hyp("graph"),invariant))
    return introduce(s,PARAMETERS,(),lambda t:
        eliminate(t,specialize(t,"prefix_exists",*t.terms(PARAMETERS)),V,"graph",chosen))


def prove_row_horner_values(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV059",target=frozen_row_horner_values_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"value_exists":_value_exists,"value_unique":_value_unique,"row_value_unique":lambda s:_row_value_unique(s,registry),
            "entry":lambda s:_entry(s,registry),"successor":lambda s:_successor(s,registry),
            "prefix_exists":lambda s:_prefix_exists(s,parse_named(HELPER_SOURCES["prefix_exists"],registry=registry)),"CV059":_root},
        pins=row_horner_values_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
