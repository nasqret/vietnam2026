"""CV002: every finite denominator-cleared log-exp recurrence has fixed coefficients.

The single conservative alias contains only the two initial entries and the
three-term recurrence, not its claimed solution. Induction proves all positive
coefficients equal to twice the initial numerator. This is a universal natural
table theorem, not proof that exponential composition satisfies the recurrence,
not an analytic limit argument, and not IR072. Run proof production only under
the root-owned bounded wave supervisor.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType

from sqrt2_power_quadratic_trace_exists import (
    ROOT, Scope, introduce, eliminate, field, apply, specialize,
    canonical, json_hash, _inert_metrics, quadratic_trace_exists_source_pins,
    V28_ARTIFACT, V28_ARTIFACT_SIZE, V28_ARTIFACT_SHA256,
)

SCHEMA = "sqrt2-power-logexp-recurrence-v1"
DEFINITION_SOURCE = (
    "BetaAt(b,c,0,D) /\\ (BetaAt(b,c,1,2*D) /\\ "
    "(forall k u v w. Lt(S(S k),L) -> BetaAt(b,c,k,u) -> "
    "BetaAt(b,c,S k,v) -> BetaAt(b,c,S(S k),w) -> (S(S k))*w=k*u+2*v))"
)
DEFINITION_SHA256 = "8e24a631017bbe614de882637fe2e89c02f096704c315b62b13a4764092b1f14"
NAMED_SOURCE = (
    "forall b c L D i v. NatExpAtanhRecurrence(b,c,L,D) -> "
    "Lt(i,L) -> BetaAt(b,c,i,v) -> "
    "((i=0 /\\ v=D) \\/ (exists k. i=S k /\\ v=2*D))"
)
TARGET_SHA256 = "798208f708ff6a1d8a5d5d279698ac3f19608a2c01a96bd5059fa4b582a9520a"
INVARIANT_SOURCE = (
    "forall b c L D. NatExpAtanhRecurrence(b,c,L,D) -> "
    "forall i a v. Lt(S i,L) -> BetaAt(b,c,i,a) -> BetaAt(b,c,S i,v) -> "
    "(i*a=i*(2*D) /\\ v=2*D)"
)
INVARIANT_SHA256 = "6365ae4fbf04fbbc1f2f4bc327fecb2b4dae517683291b1fef6bd5a677025397"
BASE_DEFINITIONS = {
    "Le": ("PD0001","5aad83c25902bc26b2fdbd296fabd3db359880ec4c568fe7e108ce1dc11dea46"),
    "Lt": ("PD0002","d7bdf8ed287c3672fa78951c9cabe8f8814d7fcf1fb1ffcfee2d0d3b41251531"),
    "BetaAt": ("PD0013","b2a23ea9cf6373c9ee8a9c2a74cbcffde69a806b04ed3f831e7a9b00d445bdeb"),
}
ENDPOINT_SOURCES = {
    4: "forall a. 0*a=0",
    11: "forall a b c. (a+b)*c=a*c+b*c",
    12: "forall a. ~(S a=0)",
    14: "forall a. Le(a,a)",
    15: "forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    23: "forall n. n=0 \\/ exists k. n=S k",
    40: "forall a b. Le(a,b) -> Le(a,S b)",
    65: "forall a b c. ~(a=0) -> a*b=a*c -> b=c",
    121: "forall b c i. exists x. BetaAt(b,c,i,x)",
    122: "forall b c i x y. BetaAt(b,c,i,x) -> BetaAt(b,c,i,y) -> x=y",
}
ANCESTOR_IDS = (0,1,2,3,4,5,6,7,11,12,14,15,20,21,22,23,27,28,40,51,55,56,58,59,64,65,119,121,122)
ANCESTOR_ROWS_SHA256 = "33f3bdccd96a83951facbcfafaa8d8d9d8ba342f3cc74441386b0e29233b7158"
ANCESTOR_ROWS_BYTES = 34489
INVARIANT_DEPENDENCIES = (4,11,12,14,15,40,65,121,122)
ROOT_DEPENDENCIES = (23,121,122,"invariant")


class RecurrenceError(ValueError):
    """Changed formula, exact ancestor bytes, conservative expansion or cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named, PARENT, PARENT_SHA256
    from peano_lab.library.defined_syntax import DEFINITIONS_BY_NAME, _definition
    from peano_lab.library.proof_bundle import encode_formula
    from peano_lab.kernel.formulas import pretty_formula, parse_formula_in_context
    result = {}
    for name,(identifier,digest) in BASE_DEFINITIONS.items():
        d = DEFINITIONS_BY_NAME[name]
        if (d.stable_id!=identifier or json_hash(encode_formula(d.template_formula))!=digest
                or not set(d.conceptual_dependencies)<=result.keys()):
            raise RecurrenceError("historical order/beta definition or DAG changed")
        result[name] = d
    raw = PARENT.read_bytes()
    if len(raw)!=1501384 or sha256(raw).hexdigest()!=PARENT_SHA256:
        raise RecurrenceError("historical definition inventory changed")
    parent = json.loads(raw)["reviewed_definitions"]
    name,identifier,parameters = "NatExpAtanhRecurrence","ND0400",("b","c","L","D")
    if any(d["id"]==identifier or d["name"]==name for d in parent):
        raise RecurrenceError("local recurrence alias collides with a historical definition")
    formula = parse_named(DEFINITION_SOURCE,parameters,result)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise RecurrenceError("recurrence definition exact expansion changed")
    text = pretty_formula(formula,list(parameters))
    d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
        summary="Two initial coefficients and the denominator-cleared finite log-exponential recurrence; no solution clause.",
        category="irrationality_formal_series",conceptual_dependencies=("BetaAt","Lt"))
    if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
        raise RecurrenceError("conservative recurrence expansion failed roundtrip")
    result[name] = d
    return MappingProxyType(result)


def frozen_logexp_recurrence_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Or
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=6 or len(premises)!=3 or type(conclusion) is not Or or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise RecurrenceError("CV002 frozen universal recurrence target changed")
    return target


def source_contract():
    return dict(code="CV002",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,arbitrary_length=True,denominator_cleared_natural_coefficients=True,
        actual_recurrence_required=True,actual_decoded_entry_required=True,positive_D_required=False,
        new_definition_ids=["ND0400"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",exp_composition_satisfies_recurrence=False,
        analytic_limit_claim=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def logexp_recurrence_source_pins():
    result = quadratic_trace_exists_source_pins()
    name = "scripts/sqrt2_power_quadratic_trace_exists.py"
    if result[name]["sha256"]!="4269d6b9a2282fad3870b408578e2894544c4b172ea76ea2891945adce25ba1a":
        raise RecurrenceError("exact ordinary proof-bookkeeping source changed")
    name = "scripts/sqrt2_power_logexp_recurrence.py"
    with (ROOT/name).open("rb") as stream:
        raw = stream.read(2*1024**2+1)
    if len(raw)>2*1024**2:
        raise RecurrenceError("source snapshot exceeds its bound")
    result[name] = dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
    return result


def inert_recurrence_rows(artifact_path=V28_ARTIFACT):
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE+1)
    if len(raw)!=V28_ARTIFACT_SIZE or sha256(raw).hexdigest()!=V28_ARTIFACT_SHA256:
        raise RecurrenceError("actual arithmetic archive bytes changed")
    data = json.loads(raw)
    del raw
    if data[0]!="peano-lab-bundle-v1" or data[1]!=861 or len(data[3])!=862:
        raise RecurrenceError("arithmetic archive envelope changed")
    seen,pending = set(),list(ENDPOINT_SOURCES)
    while pending:
        old = pending.pop()
        if type(old) is not int or not 0<=old<862:
            raise RecurrenceError("invalid actual ancestor index")
        if old not in seen:
            row = data[3][old]
            if len(row)!=4 or len(row[2])!=len(set(row[2])) or any(type(d) is not int or not 0<=d<old for d in row[2]):
                raise RecurrenceError("invalid ordered ancestor dependencies")
            seen.add(old)
            pending.extend(row[2])
    ids = tuple(sorted(seen))
    rows = tuple(data[3][i] for i in ids)
    if ids!=ANCESTOR_IDS or json_hash(rows)!=ANCESTOR_ROWS_SHA256 or len(canonical(rows))!=ANCESTOR_ROWS_BYTES:
        raise RecurrenceError("exact recurrence ancestor cone changed")
    registry = definition_registry()
    for i,source in ENDPOINT_SOURCES.items():
        if data[3][i][1]!=encode_formula(parse_named(source,registry=registry)):
            raise RecurrenceError("actual arithmetic endpoint differs from frozen statement")
    return ids,rows


def _invariant_body(target):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import (Axiom,AndIntro,AndElimL,AndElimR,CongAdd,CongMul,CongS,
        EqRefl,EqSym,EqTrans,Ind)
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def base(s):
        zero,one,two = Zero(),Succ(Zero()),Succ(Succ(Zero()))
        mass = Mul(two,s.term("D"))
        first = EqTrans(specialize(s,4,s.term("a")),EqSym(specialize(s,4,mass)))
        second = apply(specialize(s,122,*s.terms(("b","c")),one,s.term("v"),mass),
            s.hyp("next"),field(s.hyp("recurrence"),1,3))
        return AndIntro(first,second)
    def step(s):
        def decoded(t):
            i,a,v,u,L = t.terms(("i","a","v","u","L"))
            two = Succ(Succ(Zero()))
            mass = Mul(two,t.term("D"))
            ss,s3 = Succ(Succ(i)),Succ(Succ(Succ(i)))
            smaller = apply(specialize(t,15,ss,s3,L),
                apply(specialize(t,40,ss,ss),specialize(t,14,ss)),t.hyp("bound"))
            previous = apply(specialize(t,"IH",u,a),smaller,t.hyp("prior"),t.hyp("current"))
            recurrence = apply(instantiate(field(t.hyp("recurrence"),2,3),i,u,a,v),
                t.hyp("bound"),t.hyp("prior"),t.hyp("current"),t.hyp("next"))
            # k+2 = S(S k), without ring normalization or closed-law copying.
            add_two = EqTrans(instantiate(Axiom("PA4"),i,Succ(Zero())),
                EqTrans(CongS(instantiate(Axiom("PA4"),i,Zero())),
                        CongS(CongS(instantiate(Axiom("PA3"),i)))))
            rhs = EqTrans(CongAdd(AndElimL(previous),CongMul(EqRefl(two),AndElimR(previous))),
                EqTrans(EqSym(specialize(t,11,i,two,mass)),CongMul(add_two,EqRefl(mass))))
            last = apply(specialize(t,65,ss,v,mass),specialize(t,12,Succ(i)),EqTrans(recurrence,rhs))
            return AndIntro(CongMul(EqRefl(Succ(i)),AndElimR(previous)),last)
        return eliminate(s,specialize(s,121,*s.terms(("b","c")),s.term("i")),("u",),"prior",decoded)
    # After four parameters and the recurrence premise, induction quantifies i.
    motive = target
    for _ in range(4):
        motive = motive.body
    motive = motive.right.body
    def induction(s):
        base_proof = introduce(s,("a","v"),("bound","current","next"),base)
        step_proof = introduce(s,("i",),("IH",),lambda t:
            introduce(t,("a","v"),("bound","current","next"),step))
        return Ind(motive,base_proof,step_proof)
    return introduce(Scope(),(),INVARIANT_DEPENDENCIES,lambda s:
        introduce(s,("b","c","L","D"),("recurrence",),induction))


def _root_body(registry):
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import (AndIntro,AndElimR,EqSubst,ExistsIntro,OrIntroL,OrIntroR,OrElim)
    from peano_lab.kernel.terms import Succ,Zero
    def finish(s):
        def transport(t,source,hypothesis):
            motive = parse_named(source,t.variable("index_slot").variables,registry)
            return EqSubst(motive,t.hyp("index"),t.hyp(hypothesis))
        def at_zero(t):
            decoded = transport(t,"BetaAt(b,c,index_slot,v)","entry")
            equation = apply(specialize(t,122,*t.terms(("b","c")),Zero(),t.term("v"),t.term("D")),
                decoded,field(t.hyp("recurrence"),0,3))
            return OrIntroL(AndIntro(t.hyp("index"),equation))
        def successor(t):
            def predecessor(u):
                proof = apply(specialize(u,"invariant",*u.terms(("b","c","L","D"))),u.hyp("recurrence"))
                from sqrt2_power_native import instantiate
                last = apply(instantiate(proof,*u.terms(("k","a","v"))),
                    transport(u,"Lt(index_slot,L)","bound"),u.hyp("prior"),
                    transport(u,"BetaAt(b,c,index_slot,v)","entry"))
                return OrIntroR(ExistsIntro(u.term("k"),AndIntro(u.hyp("index"),AndElimR(last))))
            return eliminate(t,specialize(t,121,*t.terms(("b","c")),t.term("k")),("a",),"prior",predecessor)
        right = s.hypothesis("successor")
        return OrElim(specialize(s,23,s.term("i")),at_zero(s.hypothesis("index")),
            eliminate(right,right.hyp("successor"),("k",),"index",successor))
    return introduce(Scope(),(),ROOT_DEPENDENCIES,lambda s:
        introduce(s,("b","c","L","D","i","v"),("recurrence","bound","entry"),finish))


@dataclass(frozen=True)
class LogExpRecurrenceCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_logexp_recurrence(*,limits=None,artifact_path=V28_ARTIFACT):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise RecurrenceError("expected unchanged BinaryDAGLimits")
    before = logexp_recurrence_source_pins()
    registry,target = definition_registry(),frozen_logexp_recurrence_target()
    invariant = parse_named(INVARIANT_SOURCE,registry=registry)
    if json_hash(encode_formula(invariant))!=INVARIANT_SHA256:
        raise RecurrenceError("exact all-indices induction invariant changed")
    ids,old_rows = inert_recurrence_rows(artifact_path)
    endpoints = {old:new for new,old in enumerate(ids)}
    rows = [[r[0],r[1],[endpoints[d] for d in r[2]],r[3]] for r in old_rows]
    del old_rows
    gc.collect()
    total,deepest = 0,0
    for i,row in enumerate(rows):
        count,depth = _inert_metrics(row[3],limits)
        total,deepest = total+count,max(deepest,depth)
        if type(row[0]) is not int or row[0]<8*count+16:
            raise RecurrenceError("actual ancestor fuel does not cover its body")
    ancestor_total = total
    for name,formula,dependencies,body in (
        ("invariant",invariant,INVARIANT_DEPENDENCIES,_invariant_body(invariant)),
        ("CV002",target,ROOT_DEPENDENCIES,_root_body(registry)),
    ):
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise RecurrenceError("recurrence aggregate ordinary-body/node bound exceeded")
        _row_preflight(formula,body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formula),[endpoints[d] for d in dependencies],encode_proof(body)])
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise RecurrenceError("recurrence canonical payload bound exceeded")
    del rows,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise RecurrenceError("recurrence decoded target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE+1)
    if len(raw)!=V28_ARTIFACT_SIZE or sha256(raw).hexdigest()!=V28_ARTIFACT_SHA256:
        raise RecurrenceError("actual parent changed during recurrence replay")
    if receipt.target!=target or logexp_recurrence_source_pins()!=before:
        raise RecurrenceError("recurrence source/target changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,all_coefficient_indices=True,
        actual_ancestor_nodes=len(ids),actual_ancestor_body_nodes=ancestor_total,
        ancestor_original_ids=list(ids),ancestor_rows_sha256=ANCESTOR_ROWS_SHA256,
        invariant_statement_ast_sha256=INVARIANT_SHA256,root_induction_count=1,
        ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,new_axioms=[],
        external_certificate_references=[],independent_lean_checked=False)
    return LogExpRecurrenceCertificate(target,bundle,payload,receipt,deepest,provenance)
