"""CV011: extend an actual prefix sum across an explicitly zero tail.

The root constructs the longer Sum witness from the supplied shorter one and
actual zero-valued tail lookups. Weighted linearity proves a zero table has
zero sum; CV009 splits the longer computation. No new induction or axiom.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256

from sqrt2_power_sum_splitting import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,
    canonical,json_hash,_inert_metrics,read_archive,definition_registry,
    sum_splitting_source_pins,NAMED_SOURCE as SPLIT_SOURCE,_subst,
)
from sqrt2_power_convolution_commutative import SPLIT_ARCHIVE
from sqrt2_power_euler_product import LINEARITY_ARCHIVE
from sqrt2_power_sum_linearity import LINEARITY_SOURCE

SCHEMA = "sqrt2-power-sum-zero-tail-v1"
NAMED_SOURCE = (
    "forall ab ac m n x. Sum(ab,ac,m,x) -> "
    "(forall j. Lt(j,n) -> BetaAt(ab,ac,m+j,0)) -> Sum(ab,ac,m+n,x)"
)
TARGET_SHA256 = "a7f186fd8bb8fecb316c79650a437ffc8e7c8a66e971c9cdf9740c56e26fe28e"
ZERO_SUM_SOURCE = "forall b c N x. Sum(b,c,N,x) -> (forall i a. Lt(i,N) -> BetaAt(b,c,i,a) -> a=0) -> x=0"
ZERO_SUM_SHA256 = "13aae5acde76c06d071c8f3fca004eaf0ae253713d62645665646e83d052d75a"
ENDPOINT_SOURCES = {
    "mul_zero_left":"forall a. 0*a=0",
    "one_mul":"forall a. 1*a=a",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "sum_unique":"forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m",
    "linearity":LINEARITY_SOURCE,
    "splitting":SPLIT_SOURCE,
}
HELPER_DEPENDENCIES = {
    "zero_sum":("linearity","mul_zero_left","one_mul"),
    "CV011":("splitting","zero_sum","sum_unique","beta_unique","one_mul"),
}


class SumZeroTailError(ValueError):
    """Changed actual zero-tail premise, checked body or resource ceiling."""


def frozen_sum_zero_tail_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SumZeroTailError("CV011 exact zero-tail transport target changed")
    return target


def source_contract():
    return dict(code="CV011",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,actual_prefix_sum_required=True,actual_zero_tail_required=True,
        longer_sum_witness_constructed=True,arbitrary_split_lengths=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",natural_convolution_associativity=False,
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def sum_zero_tail_source_pins():
    result = sum_splitting_source_pins()
    expected = {
        "scripts/sqrt2_power_sum_splitting.py":"aa629a6c5eddabbd880ccf615b0bc897fa77da7965c1a37b056016a9611c3c3c",
        "scripts/sqrt2_power_convolution_commutative.py":"d1d4ce7c0e78c03ba5961710b048fe11bcb3dd481afd2e79d5cc2b418b0412a3",
        SPLIT_ARCHIVE["path"]:SPLIT_ARCHIVE["sha256"],
    }
    for name in (*expected,"scripts/sqrt2_power_sum_zero_tail.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SumZeroTailError("zero-tail source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _zero_sum(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym,EqTrans
    from peano_lab.kernel.terms import Succ,Zero
    def right_zero(t,a,b):
        return EqTrans(CongAdd(specialize(t,"mul_zero_left",a),specialize(t,"mul_zero_left",b)),instantiate(Axiom("PA3"),Zero()))
    def finish(t):
        def pointwise(u):
            actual_zero = apply(specialize(u,"zero",*u.terms(("i","w"))),u.hyp("bound"),u.hyp("third"))
            left = EqTrans(CongMul(EqRefl(Succ(Zero())),actual_zero),instantiate(Axiom("PA5"),Succ(Zero())))
            return EqTrans(left,EqSym(right_zero(u,u.term("u"),u.term("v"))))
        relation = introduce(t,("i","u","v","w"),("bound","first","second","third"),pointwise)
        result = apply(specialize(t,"linearity",Zero(),Zero(),Succ(Zero()),
            *t.terms(("b","c","b","c","b","c","N","x","x","x"))),t.hyp("sum"),t.hyp("sum"),t.hyp("sum"),relation)
        return EqTrans(EqSym(specialize(t,"one_mul",t.term("x"))),EqTrans(result,right_zero(t,t.term("x"),t.term("x"))))
    return introduce(s,("b","c","N","x"),("sum","zero"),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,Axiom,CongAdd,EqRefl,EqTrans
    def decoded(t):
        def tail(u):
            def pointwise(v):
                source = apply(instantiate(AndElimL(v.hyp("tail")),*v.terms(("j","a"))),v.hyp("bound"),v.hyp("entry"))
                index = CongAdd(EqRefl(v.term("m")),specialize(v,"one_mul",v.term("j")))
                actual = _subst(v,registry,"BetaAt(ab,ac,slot,a)",index,source)
                from peano_lab.kernel.terms import Add,Zero
                return apply(specialize(v,"beta_unique",*v.terms(("ab","ac")),Add(v.term("m"),v.term("j")),v.term("a"),Zero()),
                    actual,apply(specialize(v,"zero_tail",v.term("j")),v.hyp("bound")))
            zero = apply(specialize(u,"zero_sum",*u.terms(("ub","uc","n","v"))),AndElimR(u.hyp("tail")),introduce(u,("j","a"),("bound","entry"),pointwise))
            same = apply(specialize(u,"sum_unique",*u.terms(("ab","ac","m","u","x"))),field(u.hyp("split"),0,4),u.hyp("prefix"))
            total = EqTrans(field(u.hyp("split"),3,4),EqTrans(CongAdd(same,zero),instantiate(Axiom("PA3"),u.term("x"))))
            return _subst(u,registry,"Sum(ab,ac,m+n,slot)",total,field(u.hyp("split"),2,4))
        return eliminate(t,field(t.hyp("split"),1,4),("ub","uc"),"tail",tail)
    return introduce(s,("ab","ac","m","n","x"),("prefix","zero_tail"),lambda t:
        eliminate(t,specialize(t,"splitting",*t.terms(("ab","ac","m","n"))),("u","v","w"),"split",decoded))


@dataclass(frozen=True)
class SumZeroTailCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_sum_zero_tail(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise SumZeroTailError("expected unchanged BinaryDAGLimits")
    before = sum_zero_tail_source_pins()
    registry,target = definition_registry(),frozen_sum_zero_tail_target()
    zero_sum = parse_named(ZERO_SUM_SOURCE,registry=registry)
    if json_hash(encode_formula(zero_sum))!=ZERO_SUM_SHA256:
        raise SumZeroTailError("exact pointwise-zero sum helper changed")
    formulas = dict(zero_sum=zero_sum,CV011=target)
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    for pin in (SPLIT_ARCHIVE,LINEARITY_ARCHIVE):
        original = read_archive(pin)
        remap = {}
        for old,r in enumerate(original):
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise SumZeroTailError("actual ancestor ordered dependencies changed")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise SumZeroTailError("merged ancestor body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        for name,source in ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=registry))
            matches = [i for i,r in enumerate(original) if r[1]==formula]
            if len(matches)>1:
                raise SumZeroTailError("ambiguous actual endpoint: "+name)
            if matches:
                if name in endpoints and endpoints[name]!=remap[matches[0]]:
                    raise SumZeroTailError("shared actual endpoint bodies disagree")
                endpoints[name] = remap[matches[0]]
        del original,remap
        gc.collect()
    if endpoints.keys()!=ENDPOINT_SOURCES.keys():
        raise SumZeroTailError("missing actual zero-tail ancestor endpoint")
    ancestor_count = len(rows)
    for name,factory in (("zero_sum",_zero_sum),("CV011",lambda s:_root(s,registry))):
        dependencies = HELPER_DEPENDENCIES[name]
        body = introduce(Scope(),(),dependencies,factory)
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise SumZeroTailError("zero-tail aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in dependencies],encode_proof(body)])
    reached,pending = set(),[len(rows)-1]
    while pending:
        old = pending.pop()
        if old not in reached:
            reached.add(old)
            pending.extend(rows[old][2])
    retained = tuple(sorted(reached))
    remap = {old:new for new,old in enumerate(retained)}
    ancestors = tuple(old for old in retained if old<ancestor_count)
    ancestor_total = sum(_inert_metrics(rows[old][3],limits)[0] for old in ancestors)
    helper_indices = {name:remap[endpoints[name]] for name in HELPER_DEPENDENCIES}
    rows = [[rows[old][0],rows[old][1],[remap[d] for d in rows[old][2]],rows[old][3]] for old in retained]
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise SumZeroTailError("zero-tail canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise SumZeroTailError("decoded zero-tail target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or sum_zero_tail_source_pins()!=before:
        raise SumZeroTailError("zero-tail target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,all_zero_tail_sum_transport=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        splitting_archive=dict(SPLIT_ARCHIVE),linearity_archive=dict(LINEARITY_ARCHIVE),
        helper_statement_ast_sha256=dict(zero_sum=ZERO_SUM_SHA256),helper_bundle_indices=helper_indices,
        new_induction_count=0,ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return SumZeroTailCertificate(target,bundle,payload,receipt,deepest,provenance)
