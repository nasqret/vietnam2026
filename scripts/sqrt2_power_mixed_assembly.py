"""Untrusted bounded assembly of raw canonical and checked-wave proof archives.

The accepted CV016 assembler remains frozen. This adapter adds only a raw
canonical archive reader and explicit endpoint ownership. Every retained body
is decoded and checked by the unchanged ordinary HA kernel; archive hashes,
names and old receipts are provenance, never proof authority.
"""
import gc
from hashlib import sha256
import json

from sqrt2_power_convolution_unit import FiniteSeriesCertificate
from sqrt2_power_quadratic_trace_exists import ROOT,Scope,introduce,canonical,json_hash,_inert_metrics
from sqrt2_power_quadratic_product_exists import read_archive


class MixedAssemblyError(ValueError):
    """Changed exact archive data, ownership, ordered rows, target or cap."""


def read_mixed_archive(pin,archive_path=None):
    """Return actual encoded rows, not theorem handles or unchecked axioms."""
    if pin.get("format","wave")=="wave":
        return read_archive(pin,archive_path=archive_path)
    if pin.get("format")!="raw-canonical":
        raise MixedAssemblyError("unknown actual archive format")
    from pathlib import Path
    if type(pin.get("bytes")) is not int or not 1<=pin["bytes"]<=8*1024**2:
        raise MixedAssemblyError("raw archive byte bound exceeded")
    path = ROOT/pin["path"] if archive_path is None else Path(archive_path)
    with path.open("rb") as stream:
        raw = stream.read(pin["bytes"]+1)
    if len(raw)!=pin["bytes"] or sha256(raw).hexdigest()!=pin["sha256"]:
        raise MixedAssemblyError("actual raw archive bytes changed")
    value = json.loads(raw)
    if (type(value) is not list or len(value)!=4 or value[0]!="peano-lab-bundle-v1"
            or type(value[1]) is not int or value[1]!=pin["root"]
            or type(value[3]) is not list or len(value[3])!=pin["nodes"]
            or not 1<=len(value[3])<=4096 or not 0<=value[1]<len(value[3])
            or json_hash(value[2])!=pin["target_ast_sha256"]):
        raise MixedAssemblyError("actual raw archive envelope changed")
    if raw!=canonical(value)+b"\n":
        raise MixedAssemblyError("actual raw archive is not the pinned canonical encoding")
    for old,row in enumerate(value[3]):
        if (type(row) is not list or len(row)!=4 or type(row[0]) is not int
                or type(row[2]) is not list or any(type(d) is not int or not 0<=d<old for d in row[2])
                or len(row[2])!=len(set(row[2]))):
            raise MixedAssemblyError("raw archive ordered dependency row changed")
    if value[2]!=value[3][value[1]][1]:
        raise MixedAssemblyError("raw archive root target differs from its actual row")
    return value[3]


def assemble_mixed_certificate(*,code,target,registry,helper_sources,helper_hashes,
        endpoint_sources,endpoint_owners,archives,dependencies,factories,pins,contract,
        limits=None,new_induction_count=0):
    """Exact full-row merging plus complete ordinary replay, with fixed owners.

    Explicit owners disambiguate distinct archived proofs of the same formula.
    They do not certify a formula: all ordered ancestor bodies of the selected
    proof are retained and independently checked from the final canonical data.
    """
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise MixedAssemblyError("expected unchanged BinaryDAGLimits")
    cases = [pin["case"] for pin in archives]
    if (len(cases)!=len(set(cases)) or endpoint_owners.keys()!=endpoint_sources.keys()
            or not set(endpoint_owners.values())<=set(cases)):
        raise MixedAssemblyError("each exact endpoint must have one explicit actual archive owner")
    before = pins()
    formulas = {name:parse_named(source,registry=registry) for name,source in helper_sources.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=helper_hashes:
        raise MixedAssemblyError("exact mixed-assembly helper target changed")
    formulas[code] = target
    endpoint_formulas = {name:encode_formula(parse_named(source,registry=registry)) for name,source in endpoint_sources.items()}
    rows,keys,endpoints,origins = [],{},{},{}
    total,deepest = 0,0
    for pin in archives:
        original = read_mixed_archive(pin)
        remap = {}
        for old,r in enumerate(original):
            if (type(r) is not list or len(r)!=4 or type(r[2]) is not list
                    or any(type(d) is not int or not 0<=d<old for d in r[2]) or len(r[2])!=len(set(r[2]))):
                raise MixedAssemblyError("actual mixed ancestor ordered dependencies changed")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if type(r[0]) is not int or r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise MixedAssemblyError("mixed ancestor body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        for name,formula in endpoint_formulas.items():
            if endpoint_owners[name]!=pin["case"]:
                continue
            matches = [i for i,r in enumerate(original) if r[1]==formula]
            if len(matches)!=1:
                raise MixedAssemblyError("missing or ambiguous actual owned endpoint: "+name)
            endpoints[name] = remap[matches[0]]
            origins[name] = dict(case=pin["case"],original_node=matches[0],target_ast_sha256=json_hash(formula))
        del original,remap
        gc.collect()
    if endpoints.keys()!=endpoint_sources.keys():
        raise MixedAssemblyError("missing actual mixed endpoint")
    ancestor_count = len(rows)
    for name,deps in dependencies.items():
        body = introduce(Scope(),(),deps,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise MixedAssemblyError("mixed aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in deps],encode_proof(body)])
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
    helper_indices = {name:remap[endpoints[name]] for name in dependencies}
    rows = [[rows[old][0],rows[old][1],[remap[d] for d in rows[old][2]],rows[old][3]] for old in retained]
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise MixedAssemblyError("mixed canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise MixedAssemblyError("decoded mixed target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or pins()!=before:
        raise MixedAssemblyError("mixed target/source changed during replay")
    provenance = dict(contract,source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        actual_archives=[dict(pin) for pin in archives],endpoint_archive_selection=origins,
        helper_statement_ast_sha256=dict(helper_hashes),helper_bundle_indices=helper_indices,
        new_induction_count=new_induction_count,ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return FiniteSeriesCertificate(target,bundle,payload,receipt,deepest,provenance)
