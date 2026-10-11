"""CV078: weighted transport requires only agreement of consumed source rows.

An accumulation of K terms reads rows k<K, not the unused row k=K.
All supplied accumulation rows through K preserve their coefficients below H,
for H<=J and the same actual weight codes. No code equality is inferred.
"""
from hashlib import sha256

from sqrt2_power_supplied_composition_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,supplied_composition_bound_source_pins,
)
from sqrt2_power_composition_width_transport import (
    W,P,Q,R,S,U,V,OLDL,OLDR,X,Y,FIXED,TRACES,SOURCE_MATCH,OUTPUT_MATCH,
    ENDPOINT_SOURCES as TRANSPORT_ENDPOINTS,COMPOSITION_ARCHIVE,
)
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-consumed-row-transport-v1"
CONSUMED_MATCH = SOURCE_MATCH.replace("Le(k,K)","Lt(k,K)")
NAMED_SOURCE = "forall "+" ".join(FIXED)+". Le(H,J) -> ("+CONSUMED_MATCH+") -> "+TRACES[2]+" -> "+TRACES[3]+" -> "+OUTPUT_MATCH
TARGET_SHA256 = "2f33ca6e896147c1f9c2b66a154e0be06e18e77fd718ba4123744b81650ed78d"
HELPER_SOURCES,HELPER_TARGET_SHA256 = {},{}
ARCHIVES = (COMPOSITION_ARCHIVE,)
ENDPOINT_SOURCES = {name:TRANSPORT_ENDPOINTS[name] for name in (
    "le_refl","le_succ","le_trans","beta_exists","beta_unique","row_decode","weighted_zero","weighted_graph","weighted_value")}
ENDPOINT_OWNERS = {name:"CV021" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {"CV078":tuple(ENDPOINT_SOURCES)}


class ConsumedRowTransportError(ValueError):
    """Changed consumed-row range, common weights or coefficient transport."""


def frozen_consumed_row_transport_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=21 or len(premises)!=4 or type(conclusion) is not Forall or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConsumedRowTransportError("CV078 exact consumed-source transport changed")
    return target


def source_contract():
    return dict(code="CV078",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,width_order_required=True,source_rows_required="k<K",
        accumulated_rows_proved="k<=K",unused_source_row_agreement_required=False,
        same_actual_weight_codes=True,supplied_accumulation_traces_required=True,
        low_coefficient_transport_only=True,zero_width_and_zero_horizon_allowed=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",code_number_equality_claimed=False,
        analytic_limit_claim=False,closes_IR072=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,
        IR_parents_closed=0,library_admissions=0)


def consumed_row_transport_source_pins():
    result = supplied_composition_bound_source_pins()
    expected = {"scripts/sqrt2_power_supplied_composition_bound.py":"291e01b84c94ae8482097626133077e987713f4b5e1d0f370e7bd88c3d50121b",
        "scripts/sqrt2_power_composition_width_transport.py":"9e94d8d92cdbebc2f7333bee9e6230503ffbe32f8c2d00177d5ccfc5ebfc82ae",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_consumed_row_transport.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConsumedRowTransportError("consumed-row source or actual archive changed")
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
                u.hyp("bound"),u.hyp("sourceP"),u.hyp("sourceQ"),u.hyp("index"),u.hyp("source_value"))
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


def prove_consumed_row_transport(*,limits=None):
    registry = definition_registry();target = frozen_consumed_row_transport_target()
    return assemble_mixed_certificate(code="CV078",target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"CV078":lambda s:_all_rows(s,target,registry)},pins=consumed_row_transport_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
