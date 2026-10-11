"""QF005: construct a canonical, bounded, nonzero finite quadratic product.

Only the decoded input bounds and input nonvanishing are premises. The power
value, canonical trace and decoded endpoint are constructed. A separately
checked forgetful lemma connects canonical traces to the unchanged balanced
trace used by QF001. All ancestor bodies are embedded and freshly replayed.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from pathlib import Path

from sqrt2_power_quadratic_trace_height import (
    ROOT,F,U,A,B,C,Scope,at,named,forall,introduce,eliminate,field,apply,specialize,
    canonical,json_hash,_inert_metrics,trace,definition_registry,
    quadratic_trace_height_source_pins,V28_ARTIFACT,V28_ARTIFACT_SIZE,V28_ARTIFACT_SHA256,
)
from sqrt2_power_quadratic_trace_exists import exists,witness,conjunction,products
from sqrt2_power_quadratic_product_exists import ARCHIVES as EARLIER_ARCHIVES,read_archive

SCHEMA = "sqrt2-power-bounded-quadratic-product-v1"
PARAMETERS = F+("L","H")
WITNESSES = ("N",)+U+C
NAMED_SOURCE = forall(PARAMETERS,named("IQuadFactorHeightBound",*F,"L","H")+" -> "+
    named("IQuadNonzeroFactors",*F,"L")+" -> "+exists(WITNESSES,
        "Pow(H,L,N) /\\ ("+trace(F,U,"L")+" /\\ ("+at(U,"L",C)+" /\\ ("+
        named("IQuadHeightBound",*C,"N")+" /\\ ~(rp=rn /\\ sp=sn))))"))
TARGET_SHA256 = "dcb0b757df5bea77acb675edba870bb7cc99be0a5f700ee1782c1f55f324ec14"
BRIDGE_SOURCE = forall(F+U+("L",),trace(F,U,"L")+" -> "+named("IQuadProductTrace",*F,*U,"L"))
BRIDGE_SHA256 = "5785966bf8610ee49ec1de82801110a4b2dde653597da709cd1f0420c545d52a"
POWER_SOURCE = "forall H L. exists N. Pow(H,L,N)"
POWER_TARGET_SHA256 = "e99437f5e7cea539ae2100ab7ed6ff53f59af959d01cbf2b5b445a6ba65039af"
POWER_IDS = (0,1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,20,21,22,23,24,27,28,29,30,31,32,34,35,38,39,40,41,
    42,43,48,51,53,55,56,58,59,62,63,64,69,71,72,74,76,78,79,80,81,83,88,90,91,92,93,94,95,96,97,
    112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,
    136,138,139,140,142,143,144,145,146,147,148,149,150,151,152,153,154,187,188,189,192)
POWER_ROWS_SHA256 = "c107adc931939cd7cae37d35ef11527dadfb7c35839b53f3808378af1c95843b"
POWER_ROWS_BYTES = 165506
ARCHIVES = (EARLIER_ARCHIVES[0],
    dict(case="QF004",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-canonical-quadratic-trace-v1/generation-process.json.gz",
        bytes=19854,sha256="693c0564524b08f6073a8b9fce974a374710196340784ea6269a357a1768b252",
        raw_bytes=340866,raw_sha256="ff41d465efa851457f8cb3d5313204ca2dc0208b9ee8cbb04074cfd30e41d42d",
        bundle_bytes=207847,bundle_sha256="405d151890344410934566e315ed6ec36bf471674f0c6e78f2122b0230678d01",
        nodes=108,root=107,target_ast_sha256="9c459742c8eb742cb4958f037c3b7492a8f773e609ef0f8e1d63f541c2e0a9b1"),
    dict(case="QH002",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-quadratic-trace-height-v1/generation-process.json.gz",
        bytes=13328,sha256="c1f1f6eae3e44c2a5ecb020001d4941571a7f42d3e5c41297ca3b2ccad9ba47e",
        raw_bytes=240236,raw_sha256="1e273e99d467af646c18b20a2be12e1a3da6c155bd9fafef57a9e81d3e8cb5a5",
        bundle_bytes=141562,bundle_sha256="080feebc1b7dcc21e09c4d259e5922341b0f4267f9df0e6b52fa2135c7f70ea2",
        nodes=41,root=40,target_ast_sha256="e68c7893269115ba0b6b6505c3974c336b5fb98db8d47c2d3ef227003f8a388c"))
ROOT_DEPENDENCIES = ("power_exists","QF004","decode","QH002","QF001","canonical_trace_forget")


class BoundedProductError(ValueError):
    """Changed exact body/target, unexpected premise or resource cap failure."""


def frozen_bounded_quadratic_product_target():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Forall,Imp,Exists,And
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    body = target
    for kind,count in ((Forall,10),(Imp,2),(Exists,13)):
        for _ in range(count):
            if type(body) is not kind:
                raise BoundedProductError("QF005 original binder/premise/witness shape changed")
            body = body.consequent if kind is Imp else body.body
    if type(body) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise BoundedProductError("QF005 original exact target changed")
    return target


def source_contract():
    return dict(code="QF005",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,premises=["bounded decoded inputs","nonzero decoded inputs"],
        constructed_witnesses=list(WITNESSES),supplied_trace_required=False,supplied_power_required=False,
        supplied_terminal_required=False,positive_height_required=False,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",real_interpretation=False,
        rational_denominator_claim=False,closes_IR046=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def bounded_quadratic_product_source_pins():
    result = quadratic_trace_height_source_pins()
    expected = {"scripts/sqrt2_power_quadratic_trace_height.py":"60f92d62b7b7780b4034322f74681d7b3991e0a32818913e35d38ab75aaa8a40"}
    expected.update({p["path"]:p["sha256"] for p in ARCHIVES})
    for name in (*expected,"scripts/sqrt2_power_bounded_quadratic_product.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(16*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>16*1024**2 or name in expected and digest!=expected[name]:
            raise BoundedProductError("QF005 source/archive boundary changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def inert_power_exists_rows(artifact_path=V28_ARTIFACT):
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE+1)
    if len(raw)!=V28_ARTIFACT_SIZE or sha256(raw).hexdigest()!=V28_ARTIFACT_SHA256:
        raise BoundedProductError("actual v28 proof archive changed")
    archive = json.loads(raw)
    del raw
    if archive[0]!="peano-lab-bundle-v1" or archive[1]!=861 or len(archive[3])!=862:
        raise BoundedProductError("actual v28 proof envelope changed")
    seen,pending = set(),[192]
    while pending:
        old = pending.pop()
        if old not in seen:
            seen.add(old)
            pending.extend(archive[3][old][2])
    ids = tuple(sorted(seen))
    rows = tuple(archive[3][old] for old in ids)
    if ids!=POWER_IDS or json_hash(rows)!=POWER_ROWS_SHA256 or len(canonical(rows))!=POWER_ROWS_BYTES:
        raise BoundedProductError("actual complete power-existence cone changed")
    target = encode_formula(parse_named(POWER_SOURCE,registry=definition_registry()))
    if json_hash(target)!=POWER_TARGET_SHA256 or rows[-1][1]!=target:
        raise BoundedProductError("power-existence target differs from independent source")
    return ids,rows


def merge_actual_rows(*,limits=None,artifact_path=V28_ARTIFACT):
    from sqrt2_power_binary_dag import BinaryDAGLimits
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise BoundedProductError("expected unchanged BinaryDAGLimits")
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    def merge(ids,original):
        nonlocal total,deepest
        remap = {}
        for old,row in zip(ids,original,strict=True):
            if (type(row) is not list or len(row)!=4 or len(set(row[2]))!=len(row[2])
                    or any(type(d) is not int or d not in remap for d in row[2])):
                raise BoundedProductError("actual ancestor dependency order changed")
            new = [row[0],row[1],[remap[d] for d in row[2]],row[3]]
            key = canonical(new)
            if key not in keys:
                count,depth = _inert_metrics(new[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if (type(row[0]) is not int or row[0]<8*count+16 or total>limits.max_total_body_nodes
                        or len(rows)+2>limits.max_nodes):
                    raise BoundedProductError("QF005 unchanged ancestor bound exceeded")
                keys[key] = len(rows)
                rows.append(new)
            remap[old] = keys[key]
        return remap
    # Release the 19 MB parent envelope before loading the norm proof archive.
    ids,original = inert_power_exists_rows(artifact_path)
    mapped = merge(ids,original)
    endpoints["power_exists"] = mapped[192]
    del original,mapped
    gc.collect()
    for pin in ARCHIVES:
        original = read_archive(pin)
        mapped = merge(tuple(range(len(original))),original)
        endpoints[pin["case"]] = mapped[pin["root"]]
        if pin["case"]=="QF004":
            if json_hash(original[103][1])!="e864f274188cf0a1f8278bca5152d88bd33c4f98f7692b849517cfffb9a0318a":
                raise BoundedProductError("actual terminal decoder target changed")
            endpoints["decode"] = mapped[103]
        del original,mapped
        gc.collect()
    if len(canonical(rows))>limits.max_payload_bytes:
        raise BoundedProductError("merged actual proof rows exceed payload bound")
    return rows,endpoints,total,deepest


def _bridge_body():
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,CongAdd,EqRefl,EqSym,EqTrans
    def main(s):
        def step(t):
            original = apply(instantiate(AndElimR(t.hyp("trace")),t.term("i")),t.hyp("bound"))
            def decoded(u):
                pair = u.hyp("step")
                equations = field(pair,3,4)
                rp,rn,sp,sn = products(u)
                real = EqTrans(CongAdd(field(equations,0,4),EqRefl(rn)),
                    EqSym(CongAdd(EqRefl(rp),field(equations,1,4))))
                radical = EqTrans(CongAdd(field(equations,2,4),EqRefl(sn)),
                    EqSym(CongAdd(EqRefl(sp),field(equations,3,4))))
                return witness(u.terms(A+B+C),conjunction(field(pair,0,4),field(pair,1,4),field(pair,2,4),real,radical))
            return eliminate(t,original,A+B+C,"step",decoded)
        return AndIntro(AndElimL(s.hyp("trace")),introduce(s,("i",),("bound",),step))
    return introduce(Scope(),F+U+("L",),("trace",),main)


def _root_body():
    def main(s):
        def power(t):
            def product_trace(u):
                def decoded(v):
                    height = apply(specialize(v,"QH002",*v.terms(F+U),v.term("L"),v.term("H"),v.term("N"),*v.terms(C)),
                        v.hyp("trace"),v.hyp("bounds"),v.hyp("power"),v.hyp("value"))
                    ordinary_trace = apply(specialize(v,"canonical_trace_forget",*v.terms(F+U),v.term("L")),v.hyp("trace"))
                    nonzero = apply(specialize(v,"QF001",*v.terms(F+U),v.term("L"),*v.terms(C)),
                        ordinary_trace,v.hyp("nonzero"),v.hyp("value"))
                    return witness(v.terms(WITNESSES),conjunction(v.hyp("power"),v.hyp("trace"),v.hyp("value"),height,nonzero))
                return eliminate(u,specialize(u,"decode",*u.terms(U),u.term("L")),C,"value",decoded)
            return eliminate(t,specialize(t,"QF004",*t.terms(F),t.term("L")),U,"trace",product_trace)
        return eliminate(s,specialize(s,"power_exists",s.term("H"),s.term("L")),("N",),"power",power)
    return introduce(Scope(),(),ROOT_DEPENDENCIES,lambda s:introduce(s,PARAMETERS,("bounds","nonzero"),main))


@dataclass(frozen=True)
class BoundedQuadraticProductCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_bounded_quadratic_product(*,limits=None,artifact_path=V28_ARTIFACT):
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise BoundedProductError("expected unchanged BinaryDAGLimits")
    before = bounded_quadratic_product_source_pins()
    target,registry = frozen_bounded_quadratic_product_target(),definition_registry()
    rows,endpoints,total,deepest = merge_actual_rows(limits=limits,artifact_path=artifact_path)
    ancestor_count,ancestor_total,ancestor_sha = len(rows),total,json_hash(rows)
    bridge = parse_named(BRIDGE_SOURCE,registry=registry)
    if json_hash(encode_formula(bridge))!=BRIDGE_SHA256:
        raise BoundedProductError("canonical-trace forgetful bridge changed")
    for name,statement,dependencies,body in (
        ("canonical_trace_forget",bridge,(),_bridge_body()),
        ("QF005",target,ROOT_DEPENDENCIES,_root_body())):
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise BoundedProductError("QF005 unchanged complete body/node bound exceeded")
        _row_preflight(statement,body,limits)
        linked = [endpoints[d] for d in dependencies]
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(statement),linked,encode_proof(body)])
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise BoundedProductError("QF005 canonical payload bound exceeded")
    del rows,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise BoundedProductError("QF005 decoded original target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE+1)
    if len(raw)!=V28_ARTIFACT_SIZE or sha256(raw).hexdigest()!=V28_ARTIFACT_SHA256:
        raise BoundedProductError("actual power archive changed during replay")
    if receipt.target!=target or bounded_quadratic_product_source_pins()!=before:
        raise BoundedProductError("QF005 original target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,constructed_bounded_nonzero_product=True,
        actual_ancestor_nodes=ancestor_count,actual_ancestor_body_nodes=ancestor_total,
        merged_ancestor_rows_sha256=ancestor_sha,actual_archives=list(ARCHIVES),
        power_original_ids=list(POWER_IDS),power_rows_sha256=POWER_ROWS_SHA256,
        canonical_trace_bridge=dict(node=endpoints["canonical_trace_forget"],source=BRIDGE_SOURCE,target_ast_sha256=BRIDGE_SHA256),
        root_dependencies=[endpoints[d] for d in ROOT_DEPENDENCIES],ring_normalizer_calls=0,solver_calls=0,
        local_have_compiler_calls=0,new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return BoundedQuadraticProductCertificate(target,bundle,payload,receipt,deepest,provenance)
