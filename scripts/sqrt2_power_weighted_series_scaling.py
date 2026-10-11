"""CV023: scalar transport through actual weighted accumulation traces.

For one arbitrary input-row family, W=d*Z pointwise implies Q[k]=d*R[k]
for corresponding actual accumulations. Construct both traces and prove the
relation at every available row. Neither nonzero d nor power rows are assumed.
"""
from hashlib import sha256

from sqrt2_power_finite_composition_euler import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,definition_registry,finite_composition_euler_source_pins,
    HELPER_SOURCES as COMPOSITION_HELPERS,ENDPOINT_SOURCES as COMPOSITION_ENDPOINTS,
)
from sqrt2_power_convolution_unit import assemble_actual_certificate
from sqrt2_power_weighted_series_trace import NAMED_SOURCE as WEIGHTED_SOURCE

SCHEMA = "sqrt2-power-weighted-series-scaling-v1"
P = ("pb","pc","qb","qc")
W,Z = ("wb","wc"),("yb","yc")
Q,R = ("tb","tc","vb","vc"),("rb","rc","sb","sc")
U,V = ("ub","uc"),("eb","ec")
FIXED = ("H",)+P+W+Z+Q+R+("d",)
INPUTS = ("H",)+P+W+Z+("d","K")


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def row(codes,index,values):
    return "NatPowerRow("+",".join(codes+(index,)+values)+")"


def trace(weights,acc,length="K"):
    return "NatWeightedSeriesTrace("+",".join(("H",)+weights+P+acc+(length,))+")"


def scaling(first,second,length):
    return "NatLinearTriple("+",".join(("d","0","1")+first+first+second+(length,))+")"


WEIGHT_RELATION = scaling(Z,W,"K")
ROW_RELATION = forall(("k",)+U+V,"Le(k,K) -> "+row(Q,"k",U)+" -> "+row(R,"k",V)+" -> "+scaling(V,U,"H"))
NAMED_SOURCE = forall(INPUTS,WEIGHT_RELATION+" -> exists "+" ".join(Q+R)+". "+trace(W,Q)+" /\\ ("+trace(Z,R)+" /\\ ("+ROW_RELATION+"))")
TARGET_SHA256 = "942e7e78560841ddb311dc397deeb9086050bd51b7d759f6926caddefd3d230d"
HELPER_SOURCES = {
    "scale_value":"forall d ab ac bb bc L i a b. "+scaling(("ab","ac"),("bb","bc"),"L")+" -> Lt(i,L) -> BetaAt(ab,ac,i,a) -> BetaAt(bb,bc,i,b) -> b=d*a",
    "fold_scale":forall(FIXED,forall(("k","K")+U+V+("i","q","r"),WEIGHT_RELATION+" -> "+trace(W,Q)+" -> "+trace(Z,R)+" -> Le(k,K) -> "+row(Q,"k",U)+" -> "+row(R,"k",V)+" -> Lt(i,H) -> BetaAt(ub,uc,i,q) -> BetaAt(eb,ec,i,r) -> q=d*r")),
}
HELPER_TARGET_SHA256 = {
    "scale_value":"2cb48af6f55f8976a78ffa539c8a2be5200f9e5be9f72e386ffc830fb86861ef",
    "fold_scale":"3d78c669071c63082183bf352a3c1521e0895097458db15167b886849d80a721",
}
COMPOSITION_ARCHIVE = dict(case="CV021",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-finite-composition-euler-v1/generation-process.json.gz",
    bytes=55480,sha256="ee834800329878f7adc14e3a5f07a90b05fe3189f371b06e5867dc7fb1118daf",
    raw_bytes=1485898,raw_sha256="915b54b37af57c074aaf1e9ee2991525ab0139f87b82807ae6aacb5d695a1403",
    bundle_bytes=909502,bundle_sha256="7e48274c5a65c371d3cc536fd0d8fdb08596ba956b8795ea96c1b30349d08688",
    nodes=208,root=207,target_ast_sha256="b8aae36bc9df2d03bb7bd14cae145075883cbe46a5eb5d5881d71b46927b2a65")
ARCHIVES = (COMPOSITION_ARCHIVE,)
ENDPOINT_SOURCES = {
    **{name:COMPOSITION_ENDPOINTS[name] for name in ("one_mul","mul_zero_left","mul_add","mul_assoc","le_refl","le_succ","le_trans","beta_exists","beta_unique","row_decode")},
    "weighted_zero":COMPOSITION_HELPERS["weighted_zero"],
    "weighted_graph":COMPOSITION_HELPERS["weighted_graph"],
    "weighted_value":COMPOSITION_HELPERS["weighted_value"],
    "weighted_exists":WEIGHTED_SOURCE,
}
HELPER_DEPENDENCIES = {
    "scale_value":("one_mul","mul_zero_left"),
    "fold_scale":("weighted_zero","beta_unique","row_decode","beta_exists","weighted_graph","weighted_value","scale_value","le_refl","le_succ","le_trans","mul_assoc","mul_add"),
    "CV023":("weighted_exists","fold_scale","one_mul","mul_zero_left"),
}


class WeightedScalingError(ValueError):
    """Changed actual scalar premise, source, target or proof body."""


def frozen_weighted_series_scaling_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=11 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise WeightedScalingError("CV023 exact constructed scalar accumulation target changed")
    return target


def source_contract():
    return dict(code="CV023",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,actual_pointwise_weight_relation_required=True,both_actual_weighted_traces_constructed=True,
        all_rows_through_terminal_related=True,arbitrary_source_rows=True,nonzero_scalar_required=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",exp_composition_recurrence=False,
        factorial_quotient_interpretation=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def weighted_series_scaling_source_pins():
    result = finite_composition_euler_source_pins()
    expected = {
        "scripts/sqrt2_power_finite_composition_euler.py":"3f946b7f2c1d0f88fd4f5fba37d3ff5ff2ec76153e5abe288c95f4be5fb5ec9b",
        "scripts/sqrt2_power_weighted_series_trace.py":"34b97b7cc1a0391e74b01db46847dd78260e751b47312acdd64fea5281958bbc",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_weighted_series_scaling.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise WeightedScalingError("weighted-scaling source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _scale_value(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        relation = apply(specialize(t,"graph",*t.terms(("i","a","a","b"))),t.hyp("bound"),t.hyp("first"),t.hyp("first"),t.hyp("second"))
        return _chain(EqSym(specialize(t,"one_mul",t.term("b"))),relation,
            CongAdd(EqRefl(Mul(t.term("d"),t.term("a"))),specialize(t,"mul_zero_left",t.term("a"))),instantiate(Axiom("PA3"),Mul(t.term("d"),t.term("a"))))
    return introduce(s,("d","ab","ac","bb","bc","L","i","a","b"),("graph","bound","first","second"),finish)


def _fold_scale(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    SOURCE,LEFT,RIGHT = ("fb","fc"),("gb","gc"),("hb","hc")
    params = ("K",)+U+V+("i","q","r")
    premises = ("weights","first_trace","second_trace","bound","first_row","second_row","index","first_value","second_value")
    def base(t):
        def zero_value(weights,acc,codes,value,trace_label,row_label,entry_label):
            zeros = apply(specialize(t,"weighted_zero",*t.terms(("H",)+weights+P+acc+("K",)+codes)),t.hyp(trace_label),t.hyp(row_label))
            zero_entry = apply(instantiate(zeros,t.term("i")),t.hyp("index"))
            return apply(specialize(t,"beta_unique",*t.terms(codes+("i",value)),Zero()),t.hyp(entry_label),zero_entry)
        q0 = zero_value(W,Q,U,"q","first_trace","first_row","first_value")
        r0 = zero_value(Z,R,V,"r","second_trace","second_row","second_value")
        return _chain(q0,EqSym(instantiate(Axiom("PA5"),t.term("d"))),CongMul(EqRefl(t.term("d")),EqSym(r0)))
    def successor(t):
        def finish(u):
            k,K,d,i,w,z,c,x,y = u.terms(("k","K","d","i","w","z","c","x","y"))
            def step_graph(weights,acc,old,new,weight,trace_label,old_label,row_label,weight_label):
                return apply(specialize(u,"weighted_graph",*u.terms(("H",)+weights+P+acc),K,k,*u.terms(SOURCE+old+new),weight),
                    u.hyp(trace_label),u.hyp("bound"),u.hyp("source_row"),u.hyp(old_label),u.hyp(row_label),u.hyp(weight_label))
            first_graph = step_graph(W,Q,LEFT,U,w,"first_trace","old_first_row","first_row","weight_w")
            second_graph = step_graph(Z,R,RIGHT,V,z,"second_trace","old_second_row","second_row","weight_z")
            first = apply(specialize(u,"weighted_value",*u.terms(LEFT+SOURCE+U+("H","w","i","x","c","q"))),
                first_graph,u.hyp("index"),u.hyp("old_first_value"),u.hyp("source_value"),u.hyp("first_value"))
            second = apply(specialize(u,"weighted_value",*u.terms(RIGHT+SOURCE+V+("H","z","i","y","c","r"))),
                second_graph,u.hyp("index"),u.hyp("old_second_value"),u.hyp("source_value"),u.hyp("second_value"))
            scalar = apply(specialize(u,"scale_value",d,*u.terms(Z+W),K,k,z,w),u.hyp("weights"),u.hyp("bound"),u.hyp("weight_z"),u.hyp("weight_w"))
            small = apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k))
            old_bound = apply(specialize(u,"le_trans",k,Succ(k),K),small,u.hyp("bound"))
            previous = apply(specialize(u,"IH",K,*u.terms(LEFT+RIGHT),i,x,y),u.hyp("weights"),u.hyp("first_trace"),u.hyp("second_trace"),old_bound,
                u.hyp("old_first_row"),u.hyp("old_second_row"),u.hyp("index"),u.hyp("old_first_value"),u.hyp("old_second_value"))
            return _chain(first,CongAdd(previous,CongMul(scalar,EqRefl(c))),
                CongAdd(EqRefl(Mul(d,y)),specialize(u,"mul_assoc",d,z,c)),
                EqSym(specialize(u,"mul_add",d,y,Mul(z,c))),CongMul(EqRefl(d),EqSym(second)))
        def construct(u,position):
            if position==8:
                return finish(u)
            if position==0:
                proof,names,label = specialize(u,"row_decode",*u.terms(Q+("k",))),LEFT,"old_first_row"
            elif position==1:
                proof,names,label = specialize(u,"row_decode",*u.terms(R+("k",))),RIGHT,"old_second_row"
            elif position==2:
                proof,names,label = specialize(u,"row_decode",*u.terms(P+("k",))),SOURCE,"source_row"
            elif position==3:
                proof,names,label = specialize(u,"beta_exists",*u.terms(W+("k",))),("w",),"weight_w"
            elif position==4:
                proof,names,label = specialize(u,"beta_exists",*u.terms(Z+("k",))),("z",),"weight_z"
            elif position==5:
                proof,names,label = specialize(u,"beta_exists",*u.terms(SOURCE+("i",))),("c",),"source_value"
            elif position==6:
                proof,names,label = specialize(u,"beta_exists",*u.terms(LEFT+("i",))),("x",),"old_first_value"
            else:
                proof,names,label = specialize(u,"beta_exists",*u.terms(RIGHT+("i",))),("y",),"old_second_value"
            return eliminate(u,proof,names,label,lambda v:construct(v,position+1))
        return construct(t,0)
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.body
    return introduce(s,FIXED,(),lambda t:
        Ind(motive,introduce(t,params,premises,base),introduce(t,("k",),("IH",),lambda u:introduce(u,params,premises,successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def chosen(t):
        def rows(u):
            def pointwise(v):
                scalar = apply(specialize(v,"fold_scale",*v.terms(FIXED+("k","K")+U+V+("i","c","a"))),
                    *(v.hyp(h) for h in ("weights","first_trace","second_trace","bound","first_row","second_row","index","third","first")))
                value = Mul(v.term("d"),v.term("a"))
                return _chain(specialize(v,"one_mul",v.term("c")),scalar,
                    EqSym(instantiate(Axiom("PA3"),value)),CongAdd(EqRefl(value),EqSym(specialize(v,"mul_zero_left",v.term("b")))))
            return introduce(u,("i","a","b","c"),("index","first","second","third"),pointwise)
        invariant = introduce(t,("k",)+U+V,("bound","first_row","second_row"),rows)
        return witness(t.terms(Q+R),conjunction(t.hyp("first_trace"),t.hyp("second_trace"),invariant))
    return introduce(s,INPUTS,("weights",),lambda t:
        eliminate(t,specialize(t,"weighted_exists",*t.terms(("H",)+W+P+("K",))),Q,"first_trace",lambda u:
            eliminate(u,specialize(u,"weighted_exists",*u.terms(("H",)+Z+P+("K",))),R,"second_trace",chosen)))


def prove_weighted_series_scaling(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"scale_value":_scale_value,"fold_scale":lambda s:_fold_scale(s,parse_named(HELPER_SOURCES["fold_scale"],registry=registry)),"CV023":_root}
    return assemble_actual_certificate(code="CV023",target=frozen_weighted_series_scaling_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=weighted_series_scaling_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
