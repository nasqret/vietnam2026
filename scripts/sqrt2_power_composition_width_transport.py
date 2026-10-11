"""CV052: construct cross-width powers and weighted finite compositions.

For one actual input and one outer weight table, H<=J preserves every low
power coefficient and every weighted accumulation row through K. Four traces
are constructed. This compares coefficients only, not full evaluations/tails.
"""
from hashlib import sha256

from sqrt2_power_finite_composition_euler import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,finite_composition_euler_source_pins,
    HELPER_SOURCES as COMPOSITION_HELPERS,
)
from sqrt2_power_weighted_series_scaling import COMPOSITION_ARCHIVE
from sqrt2_power_weighted_series_trace import NAMED_SOURCE as WEIGHTED_SOURCE
from sqrt2_power_series_power_trace import HELPER_SOURCES as POWER_HELPERS
from sqrt2_power_power_width_transport import (
    NAMED_SOURCE as POWER_WIDTH_SOURCE,power_width_transport_source_pins,
)
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-composition-width-transport-v1"
A = ("ab","ac","L")
W = ("wb","wc")
P,Q = ("pb","pc","qb","qc"),("rb","rc","sb","sc")
R,S = ("tb","tc","vb","vc"),("db","dc","eb","ec")
U,V = ("ub","uc"),("fb","fc")
OLDL,OLDR = ("lb","lc"),("mb","mc")
X,Y = ("nb","nc"),("ob","oc")
PARAMETERS = A+("H","J")+W+("K",)
FIXED = ("H","J")+W+P+Q+R+S+("K",)


def row(codes,index,values):
    return "NatPowerRow("+",".join(codes+(index,)+values)+")"


def power(codes,width):
    return "NatPowerTrace("+",".join(A+(width,)+codes+("K",))+")"


def weighted(width,source,acc):
    return "NatWeightedSeriesTrace("+",".join((width,)+W+source+acc+("K",))+")"


def agrees(first,second):
    return ("forall k "+" ".join(U+V+("i","a"))+". Le(k,K) -> "+row(first,"k",U)+" -> "+row(second,"k",V)+
        " -> Lt(i,H) -> BetaAt(ub,uc,i,a) -> BetaAt(fb,fc,i,a)")


SOURCE_MATCH,OUTPUT_MATCH = agrees(P,Q),agrees(R,S)
TRACES = (power(P,"H"),power(Q,"J"),weighted("H",P,R),weighted("J",Q,S))
NAMED_SOURCE = ("forall "+" ".join(PARAMETERS)+". Le(H,J) -> exists "+" ".join(P+Q+R+S)+". "+
    TRACES[0]+" /\\ ("+TRACES[1]+" /\\ ("+TRACES[2]+" /\\ ("+TRACES[3]+" /\\ (("+SOURCE_MATCH+") /\\ ("+OUTPUT_MATCH+")))))")
TARGET_SHA256 = "47daedfb22c29d1e812581a080205cad3a0b0a394afbe6937e03886dcfd6c17e"
HELPER_SOURCES = {
    "all_rows":"forall "+" ".join(FIXED)+". Le(H,J) -> ("+SOURCE_MATCH+") -> "+TRACES[2]+" -> "+TRACES[3]+" -> "+OUTPUT_MATCH,
}
HELPER_TARGET_SHA256 = {"all_rows":"21f4112309a11e07c13e00a708c358ed1829c5833ffcc2e639f7cbdc1c9b0595"}
POWER_WIDTH_ARCHIVE = dict(case="CV051",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-power-width-transport-v3/generation-process.json.gz",
    bytes=30783,sha256="0e722af90faccf828469954b1e291e5c0ccf68fc46e1775194157f6976f6e13a",
    raw_bytes=650987,raw_sha256="00c2e2eea15d0953b19098cdc2cdae78c458abcd87ee3c749baab690ab5cb5de",
    bundle_bytes=388057,bundle_sha256="82e79e5d443ffe702660ea79c2d7ee9acfe8005212bd913d69866558ff5954bb",
    nodes=141,root=140,target_ast_sha256="d22452396ee9b966bdb17b27cd501a09a8cda4e1433e5d3885685cd54982e6eb")
ARCHIVES = (POWER_WIDTH_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES = {
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "row_decode":POWER_HELPERS["decode"],"weighted_exists":WEIGHTED_SOURCE,
    **{name:COMPOSITION_HELPERS[name] for name in ("weighted_zero","weighted_graph","weighted_value")},
    "power_width":POWER_WIDTH_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV021" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["power_width"] = "CV051"
HELPER_DEPENDENCIES = {
    "all_rows":("le_refl","le_succ","le_trans","beta_exists","beta_unique","row_decode","weighted_zero","weighted_graph","weighted_value"),
    "CV052":("power_width","weighted_exists","all_rows"),
}


class CompositionWidthTransportError(ValueError):
    """Changed actual weighted rows, shared weights, cutoff or ancestry."""


def frozen_composition_width_transport_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=8 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CompositionWidthTransportError("CV052 exact constructed cross-width composition target changed")
    return target


def source_contract():
    return dict(code="CV052",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,width_order_required=True,four_actual_traces_constructed=True,
        every_power_and_accumulation_row_preserved=True,coefficients_preserved_only_below_smaller_width=True,
        same_actual_input_and_outer_weights=True,zero_width_and_exponent_allowed=True,
        generic_weighted_transport_helper=True,new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",all_degree_product_equality=False,
        truncated_full_evaluation_equality=False,analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def composition_width_transport_source_pins():
    result = finite_composition_euler_source_pins()
    for name,pin in power_width_transport_source_pins().items():
        if name in result and result[name]!=pin:
            raise CompositionWidthTransportError("shared proof-source pins disagree")
        result[name] = pin
    expected = {"scripts/sqrt2_power_finite_composition_euler.py":"3f946b7f2c1d0f88fd4f5fba37d3ff5ff2ec76153e5abe288c95f4be5fb5ec9b",
        "scripts/sqrt2_power_weighted_series_scaling.py":"135debe011a281d6a3332f45d4c9be1c72e71bcc94d18aae37a3c3102e9d09d4",
        "scripts/sqrt2_power_power_width_transport.py":"54ffb3d275dc532e4a8d3d88eefefc1a3ccfe1ed02ce96acae3bca8a9dcecacc",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_composition_width_transport.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CompositionWidthTransportError("composition width source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _all_rows(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import EqSym,EqTrans,Ind
    from peano_lab.kernel.terms import Succ,Zero
    variables,premises = U+V+("i","a"),("bound","rowU","rowV","index","input")
    def base(t):
        zerosU = apply(specialize(t,"weighted_zero",*t.terms(("H",)+W+P+R+("K",)+U)),t.hyp("traceR"),t.hyp("rowU"))
        zerosV = apply(specialize(t,"weighted_zero",*t.terms(("J",)+W+Q+S+("K",)+V)),t.hyp("traceS"),t.hyp("rowV"))
        first = apply(instantiate(zerosU,t.term("i")),t.hyp("index"))
        large = apply(specialize(t,"le_trans",Succ(t.term("i")),*t.terms(("H","J"))),t.hyp("index"),t.hyp("width"))
        second = apply(instantiate(zerosV,t.term("i")),large)
        azero = apply(specialize(t,"beta_unique",*t.terms(U+("i","a")),Zero()),t.hyp("input"),first)
        return _subst(t,registry,"BetaAt(fb,fc,i,slot)",EqSym(azero),second)
    def successor(t):
        def finish(u):
            k,K = u.terms(("k","K"))
            old_bound = apply(specialize(u,"le_trans",k,Succ(k),K),
                apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            source_value = apply(specialize(u,"sources",k,*u.terms(X+Y+("i","c"))),
                old_bound,u.hyp("sourceP"),u.hyp("sourceQ"),u.hyp("index"),u.hyp("source_value"))
            previous_value = apply(specialize(u,"IH",*u.terms(OLDL+OLDR+("i","x"))),
                old_bound,u.hyp("previousR"),u.hyp("previousS"),u.hyp("index"),u.hyp("previous_value"))
            def graph(width,source,acc,current,previous,following,trace_label,source_label,old_label,new_label):
                return apply(specialize(u,"weighted_graph",*u.terms((width,)+W+source+acc),K,k,*u.terms(current+previous+following+("w",))),
                    u.hyp(trace_label),u.hyp("bound"),u.hyp(source_label),u.hyp(old_label),u.hyp(new_label),u.hyp("weight"))
            first_graph = graph("H",P,R,X,OLDL,U,"traceR","sourceP","previousR","rowU")
            second_graph = graph("J",Q,S,Y,OLDR,V,"traceS","sourceQ","previousS","rowV")
            large = apply(specialize(u,"le_trans",Succ(u.term("i")),*u.terms(("H","J"))),u.hyp("index"),u.hyp("width"))
            first = apply(specialize(u,"weighted_value",*u.terms(OLDL+X+U+("H","w","i","x","c","a"))),
                first_graph,u.hyp("index"),u.hyp("previous_value"),u.hyp("source_value"),u.hyp("input"))
            second = apply(specialize(u,"weighted_value",*u.terms(OLDR+Y+V+("J","w","i","x","c","b"))),
                second_graph,large,previous_value,source_value,u.hyp("output"))
            return _subst(u,registry,"BetaAt(fb,fc,i,slot)",EqSym(EqTrans(first,EqSym(second))),u.hyp("output"))
        def construct(u,position):
            rows = ((P,X,"sourceP"),(Q,Y,"sourceQ"),(R,OLDL,"previousR"),(S,OLDR,"previousS"))
            values = ((W,"k","w","weight"),(X,"i","c","source_value"),(OLDL,"i","x","previous_value"),(V,"i","b","output"))
            if position==8:
                return finish(u)
            if position<4:
                codes,names,label = rows[position]
                proof = specialize(u,"row_decode",*u.terms(codes+("k",)))
            else:
                codes,index,name,label = values[position-4]
                names = (name,)
                proof = specialize(u,"beta_exists",*u.terms(codes+(index,)))
            return eliminate(u,proof,names,label,lambda v:construct(v,position+1))
        return construct(t,0)
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.right.right.right.right.body
    return introduce(s,FIXED,("width","sources","traceR","traceS"),lambda t:Ind(motive,
        introduce(t,variables,premises,base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,variables,premises,successor))))


def _root(s):
    def chosen(t):
        preservation = apply(specialize(t,"all_rows",*t.terms(FIXED)),t.hyp("width"),field(t.hyp("powers"),2,3),t.hyp("traceR"),t.hyp("traceS"))
        return witness(t.terms(P+Q+R+S),conjunction(field(t.hyp("powers"),0,3),field(t.hyp("powers"),1,3),
            t.hyp("traceR"),t.hyp("traceS"),field(t.hyp("powers"),2,3),preservation))
    def powers(t):
        return eliminate(t,specialize(t,"weighted_exists",*t.terms(("H",)+W+P+("K",))),R,"traceR",lambda u:
            eliminate(u,specialize(u,"weighted_exists",*u.terms(("J",)+W+Q+("K",))),S,"traceS",chosen))
    return introduce(s,PARAMETERS,("width",),lambda t:
        eliminate(t,apply(specialize(t,"power_width",*t.terms(A+("H","J","K"))),t.hyp("width")),P+Q,"powers",powers))


def prove_composition_width_transport(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV052",target=frozen_composition_width_transport_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"all_rows":lambda s:_all_rows(s,parse_named(HELPER_SOURCES["all_rows"],registry=registry),registry),"CV052":_root},
        pins=composition_width_transport_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
