"""QH002: iterate the canonical quadratic height bound along an actual trace.

If every decoded input below L has coefficient mass at most H, a canonical
trace's decoded endpoint has mass at most N whenever the ordinary relational
Pow(H,L,N) holds. No positive-H assumption is needed. This is the finite
integer bound, not real evaluation, rational denominator control or IR072.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType

from sqrt2_power_canonical_quadratic_trace import (
    ROOT,F,U,A,B,C,Scope,at,named,forall,introduce,eliminate,field,apply,specialize,
    canonical,json_hash,_inert_metrics,trace,canonical_quadratic_trace_source_pins,
    definition_registry as canonical_registry,
)
from sqrt2_power_quadratic_product_exists import read_archive
from sqrt2_power_quadratic_product_trace import V28_ARTIFACT,V28_ARTIFACT_SIZE,V28_ARTIFACT_SHA256

SCHEMA = "sqrt2-power-quadratic-trace-height-v1"
D = ("yp","yn","zp","zn")
PARAMETERS = F+U+("L","H","N")+C
TARGET_SHA256 = "e68c7893269115ba0b6b6505c3974c336b5fb98db8d47c2d3ef227003f8a388c"
POWER_DEFINITIONS = {
    "Le": ("PD0001","5aad83c25902bc26b2fdbd296fabd3db359880ec4c568fe7e108ce1dc11dea46"),
    "Product": ("PD0014","0c80640a44f6aa5891ef273b1e877e98eeac9eac1905294ea2afc48b7888fad6"),
    "Repeat": ("PD0019","cc4b13cedf42cae46d24a19cd9d8f38d7fb0fef6139087fdb4c4c262e4955096"),
    "Pow": ("PD0020","7d41c5fb594f69e8b48825bdf74fd23ab031a03290a2a5bc42e89bb89fa2bc5f"),
}
DEFINITION_ROWS = (
    (398,"IQuadHeightBound",A+("H",),"exists h. IQuadHeight(ap,an,bp,bn,h) /\\ Le(h,H)",
     ("IQuadHeight","Le"),"An explicitly represented quadratic integer has natural coefficient mass bounded by H.",
     "6b835a88422e6f12452bbfac52f9943f77ca2b5ce6810a31bd1d4b111b8cfc44"),
    (399,"IQuadFactorHeightBound",F+("L","H"),forall(("i",)+A,
        "Lt(i,L) -> "+at(F,"i",A)+" -> "+named("IQuadHeightBound",*A,"H")),
     ("Lt","IQuadAt","IQuadHeightBound"),"Every decoded input below L satisfies the stated coefficient bound; this is a premise separate from the trace.",
     "766049489094c89cd5e6580b1a79d6658a39d5a4b8c7add9b6fb4b076890973c"),
)
NAMED_SOURCE = forall(PARAMETERS,trace(F,U,"L")+" -> "+
    named("IQuadFactorHeightBound",*F,"L","H")+" -> Pow(H,L,N) -> "+
    at(U,"L",C)+" -> "+named("IQuadHeightBound",*C,"N"))
ANCESTOR_IDS = (0,1,2,3,4,5,6,7,11,14,15,20,23,27,28,40,51,52,53,58,59,122,157,158,190,193,195)
ANCESTOR_ROWS_SHA256 = "001187a7ce841534277c33a0781cd12cb7e01ed6d4d2e197055266d60624c3ce"
ANCESTOR_ROWS_BYTES = 53866
ENDPOINT_SOURCES = {
    0: "forall a. 0+a=a",
    14: "forall a. Le(a,a)",
    15: "forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    40: "forall a b. Le(a,b) -> Le(a,S b)",
    52: "forall a b c. Le(a,b) -> Le(c*a,c*b)",
    53: "forall a b c. Le(a,b) -> Le(a*c,b*c)",
    122: "forall b c i x y. BetaAt(b,c,i,x) -> BetaAt(b,c,i,y) -> x=y",
    193: "forall a e n. e=0 -> Pow(a,e,n) -> n=1",
    195: "forall a e se n. se=S e -> Pow(a,se,n) -> exists r. Pow(a,e,r) /\\ n=r*a",
}
HEIGHT_ARCHIVE = dict(case="QH001",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-quadratic-height-v2/generation-process.json.gz",
    bytes=8498,sha256="73b79ddabbf19d790a04729cf6f6828253cd6e20534d2aa484d45f8d42c1d3bf",
    raw_bytes=104155,raw_sha256="c24e01fd6bb857f300917eb124da1029dc6f383c193364b6e8121d96c69e1b75",
    bundle_bytes=54153,bundle_sha256="d23dff4f88d369f48781cbe4293f474c6c16308a5679661b6cdd5295eb4c88ba",
    nodes=13,root=12,target_ast_sha256="b9459095385fa95c3e8d4d7ff638db6464c2053389c1921031dabfe88560f7e6")
ROOT_DEPENDENCIES = tuple(ENDPOINT_SOURCES)+("QH001",)


class TraceHeightError(ValueError):
    """Wrong expanded statement, conservative definition, proof body or cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import DEFINITIONS_BY_NAME,_definition
    from peano_lab.library.proof_bundle import encode_formula
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    registry = dict(canonical_registry())
    for name,(identifier,digest) in POWER_DEFINITIONS.items():
        definition = DEFINITIONS_BY_NAME[name]
        if (definition.stable_id!=identifier or json_hash(encode_formula(definition.template_formula))!=digest
                or not set(definition.conceptual_dependencies)<=registry.keys()):
            raise TraceHeightError("existing order/power notation changed or dependency omitted")
        registry[name] = definition
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids = {d["id"] for d in parent}|{d.stable_id for d in registry.values()}|{f"ND{i:04d}" for i in range(382,398)}
    names = {d["name"] for d in parent}|set(registry)
    for number,name,parameters,source,dependencies,summary,digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if identifier in ids or name in names or not set(dependencies)<=registry.keys():
            raise TraceHeightError("height-bound definition collision/forward dependency")
        formula = parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula))!=digest:
            raise TraceHeightError("height-bound expansion changed")
        expanded = pretty_formula(formula,list(parameters))
        definition = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=expanded,
            summary=summary,category="irrationality_quadratic_heights",conceptual_dependencies=dependencies)
        if definition.template_formula!=formula or parse_formula_in_context(expanded,list(parameters))!=formula:
            raise TraceHeightError("height-bound definition failed exact roundtrip")
        registry[name] = definition
        ids.add(identifier)
        names.add(name)
    return MappingProxyType(registry)


def frozen_quadratic_trace_height_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=23 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise TraceHeightError("QH002 original target or premise shape changed")
    return target


def source_contract():
    return dict(code="QH002",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,canonical_trace_required=True,bounded_factors_required=True,relational_power_required=True,
        positive_height_required=False,new_definition_ids=["ND0398","ND0399"],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        real_interpretation=False,rational_denominator_claim=False,closes_IR046=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def quadratic_trace_height_source_pins():
    result = canonical_quadratic_trace_source_pins()
    expected = {"scripts/sqrt2_power_canonical_quadratic_trace.py":"986caaa127c7d74fc5683aa1e58635ac5c37f36198462af9dec45168d6a7b333",
                HEIGHT_ARCHIVE["path"]:HEIGHT_ARCHIVE["sha256"]}
    for name in (*expected,"scripts/sqrt2_power_quadratic_trace_height.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(16*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>16*1024**2 or name in expected and digest!=expected[name]:
            raise TraceHeightError("QH002 actual source/archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def inert_power_rows(artifact_path=V28_ARTIFACT):
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE+1)
    if len(raw)!=V28_ARTIFACT_SIZE or sha256(raw).hexdigest()!=V28_ARTIFACT_SHA256:
        raise TraceHeightError("actual v28 archive bytes changed")
    archive = json.loads(raw)
    del raw
    if archive[0]!="peano-lab-bundle-v1" or archive[1]!=861 or len(archive[3])!=862:
        raise TraceHeightError("actual v28 archive envelope changed")
    seen,pending = set(),list(ENDPOINT_SOURCES)
    while pending:
        old = pending.pop()
        if old not in seen:
            seen.add(old)
            pending.extend(archive[3][old][2])
    ids = tuple(sorted(seen))
    rows = tuple(archive[3][old] for old in ids)
    if ids!=ANCESTOR_IDS or json_hash(rows)!=ANCESTOR_ROWS_SHA256 or len(canonical(rows))!=ANCESTOR_ROWS_BYTES:
        raise TraceHeightError("exact power/order/beta ancestor cone changed")
    registry = definition_registry()
    for old,source in ENDPOINT_SOURCES.items():
        if archive[3][old][1]!=encode_formula(parse_named(source,registry=registry)):
            raise TraceHeightError("power endpoint differs from independent exact source")
    return ids,rows


def mass(scope,names):
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    ap,an,bp,bn = scope.terms(names)
    return Add(Add(ap,an),Mul(Succ(Succ(Zero())),Add(bp,bn)))


def _root_body(target,registry):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import (Axiom,AndElimL,AndElimR,AndIntro,CongAdd,CongMul,EqRefl,EqSym,EqTrans,
        EqSubst,ExistsIntro,Ind)
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def combine_equalities(eqs):
        return CongAdd(CongAdd(eqs[0],eqs[1]),CongMul(EqRefl(Succ(Succ(Zero()))),CongAdd(eqs[2],eqs[3])))
    def decoded_equalities(s,index,first,second,left,right):
        return tuple(apply(specialize(s,122,*s.terms(U[2*k:2*k+2]),index,first[k],second[k]),
            field(left,k,4),field(right,k,4)) for k in range(4))
    def bound(s,values,proof):
        value = mass(s,values)
        return ExistsIntro(value,AndIntro(EqRefl(value),proof))
    def base(s):
        zero,one,two = Zero(),Succ(Zero()),Succ(Succ(Zero()))
        identities = decoded_equalities(s,zero,s.terms(C),(one,zero,zero,zero),s.hyp("terminal"),AndElimL(s.hyp("trace")))
        normalize = EqTrans(CongAdd(instantiate(Axiom("PA3"),one),
            CongMul(EqRefl(two),instantiate(Axiom("PA3"),zero))),
            EqTrans(CongAdd(EqRefl(one),instantiate(Axiom("PA5"),two)),instantiate(Axiom("PA3"),one)))
        n_one = apply(specialize(s,193,s.term("H"),zero,s.term("N")),EqRefl(zero),s.hyp("power"))
        equation = EqTrans(specialize(s,0,mass(s,C)),
            EqTrans(combine_equalities(identities),EqTrans(normalize,EqSym(n_one))))
        return bound(s,C,ExistsIntro(zero,equation))
    def step(s):
        length = s.term("L")
        source = apply(instantiate(AndElimR(s.hyp("trace")),length),specialize(s,14,Succ(length)))
        def decoded(t):
            prefix_power = apply(specialize(t,195,t.term("H"),t.term("L"),Succ(t.term("L")),t.term("N")),
                EqRefl(Succ(t.term("L"))),t.hyp("power"))
            def power(u):
                def old_step(v):
                    bound_lift = apply(specialize(v,40,Succ(v.term("j")),v.term("L")),v.hyp("prefix_bound"))
                    return apply(instantiate(AndElimR(v.hyp("trace")),v.term("j")),bound_lift)
                prefix_trace = AndIntro(AndElimL(u.hyp("trace")),introduce(u,("j",),("prefix_bound",),old_step))
                values = ("fa","fn","ga","gn")
                def old_factors(v):
                    bound_lift = apply(specialize(v,40,Succ(v.term("j")),v.term("L")),v.hyp("factor_bound"))
                    return apply(specialize(v,"factors",v.term("j"),*v.terms(values)),bound_lift,v.hyp("factor_at"))
                prefix_factors = introduce(u,("j",)+values,("factor_bound","factor_at"),old_factors)
                previous = apply(specialize(u,"IH",u.term("H"),u.term("M"),*u.terms(A)),prefix_trace,prefix_factors,
                    AndElimL(u.hyp("power_prefix")),field(u.hyp("step"),1,4))
                def previous_bound(v):
                    factor = apply(specialize(v,"factors",v.term("L"),*v.terms(B)),
                        specialize(v,14,Succ(v.term("L"))),field(v.hyp("step"),0,4))
                    def factor_bound(w):
                        ha,hb,M,H = w.term("ha"),w.term("hb"),w.term("M"),w.term("H")
                        local = apply(specialize(w,"QH001",*w.terms(A+B+D),ha,hb,mass(w,D)),
                            field(w.hyp("step"),3,4),AndElimL(w.hyp("previous_bound")),
                            AndElimL(w.hyp("factor_bound")),EqRefl(mass(w,D)))
                        left = apply(specialize(w,53,ha,M,hb),AndElimR(w.hyp("previous_bound")))
                        right = apply(specialize(w,52,hb,H,M),AndElimR(w.hyp("factor_bound")))
                        multiplied = apply(specialize(w,15,Mul(ha,hb),Mul(M,hb),Mul(M,H)),left,right)
                        last = apply(specialize(w,15,mass(w,D),Mul(ha,hb),Mul(M,H)),local,multiplied)
                        right_motive = parse_named("Le((yp+yn)+2*(zp+zn),bound_slot)",w.variable("bound_slot").variables,registry)
                        last_n = EqSubst(right_motive,EqSym(AndElimR(w.hyp("power_prefix"))),last)
                        identities = decoded_equalities(w,Succ(w.term("L")),w.terms(C),w.terms(D),
                            w.hyp("terminal"),field(w.hyp("step"),2,4))
                        left_motive = parse_named("Le(mass_slot,N)",w.variable("mass_slot").variables,registry)
                        terminal = EqSubst(left_motive,EqSym(combine_equalities(identities)),last_n)
                        return bound(w,C,terminal)
                    return eliminate(v,factor,("hb",),"factor_bound",factor_bound)
                return eliminate(u,previous,("ha",),"previous_bound",previous_bound)
            return eliminate(t,prefix_power,("M",),"power_prefix",power)
        return eliminate(s,source,A+B+D,"step",decoded)
    motive = target
    for _ in range(17):
        motive = motive.body
    variables,premises = ("H","N")+C,("trace","factors","power","terminal")
    def induction(s):
        base_proof = introduce(s,variables,premises,base)
        step_proof = introduce(s,("L",),("IH",),lambda t:introduce(t,variables,premises,step))
        return Ind(motive,base_proof,step_proof)
    return introduce(Scope(),(),ROOT_DEPENDENCIES,lambda s:introduce(s,F+U,(),induction))


@dataclass(frozen=True)
class QuadraticTraceHeightCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_quadratic_trace_height(*,limits=None,artifact_path=V28_ARTIFACT):
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise TraceHeightError("expected unchanged BinaryDAGLimits")
    before = quadratic_trace_height_source_pins()
    target,registry = frozen_quadratic_trace_height_target(),definition_registry()
    ids,original = inert_power_rows(artifact_path)
    endpoints = {old:new for new,old in enumerate(ids)}
    rows = [[row[0],row[1],[endpoints[d] for d in row[2]],row[3]] for row in original]
    del original
    gc.collect()
    height_rows = read_archive(HEIGHT_ARCHIVE)
    offset = len(rows)
    rows.extend([row[0],row[1],[d+offset for d in row[2]],row[3]] for row in height_rows)
    endpoints["QH001"] = offset+HEIGHT_ARCHIVE["root"]
    del height_rows
    total,deepest = 0,0
    for i,row in enumerate(rows):
        count,depth = _inert_metrics(row[3],limits)
        total,deepest = total+count,max(deepest,depth)
        if any(type(d) is not int or not 0<=d<i for d in row[2]) or type(row[0]) is not int or row[0]<8*count+16:
            raise TraceHeightError("actual ancestor dependency/fuel mismatch")
    body = _root_body(target,registry)
    count,depth = _body_metrics(body,limits)
    if total+count>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
        raise TraceHeightError("QH002 aggregate ordinary-body/node bound exceeded")
    _row_preflight(target,body,limits)
    dependencies = [endpoints[d] for d in ROOT_DEPENDENCIES]
    ancestor_total = total
    rows.append([8*count+16,encode_formula(target),dependencies,encode_proof(body)])
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise TraceHeightError("QH002 canonical payload bound exceeded")
    del rows,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise TraceHeightError("QH002 decoded target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE+1)
    if len(raw)!=V28_ARTIFACT_SIZE or sha256(raw).hexdigest()!=V28_ARTIFACT_SHA256:
        raise TraceHeightError("actual parent changed during QH002 replay")
    if receipt.target!=target or quadratic_trace_height_source_pins()!=before:
        raise TraceHeightError("QH002 target/source changed during canonical replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,finite_trace_height_bound=True,
        ancestor_original_ids=list(ids),ancestor_rows_sha256=ANCESTOR_ROWS_SHA256,
        actual_ancestor_nodes=40,actual_ancestor_body_nodes=ancestor_total,root_dependencies=dependencies,
        height_archive=dict(HEIGHT_ARCHIVE),root_induction_count=1,ring_normalizer_calls=0,solver_calls=0,
        local_have_compiler_calls=0,new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return QuadraticTraceHeightCertificate(target,bundle,payload,receipt,max(deepest,depth),provenance)
