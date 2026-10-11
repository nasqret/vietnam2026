"""QF003: a witnessed nonzero finite product in Z[sqrt(2)].

Compose actual QF001 nonvanishing and QF002 trace-existence proof bodies.
The root also constructs a decoded terminal tuple; neither a trace nor its
terminal value is a premise. This is integer algebra, not real interpretation
or a proof of irrationality. No theorem registry or historical receipt grants
authority. The original HA kernel checks the complete merged canonical DAG.
"""
from dataclasses import dataclass
import gc
import gzip
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from sqrt2_power_quadratic_trace_exists import (
    ROOT, F, U, C, Scope, at, trace, named, forall, exists, introduce, eliminate,
    witness, conjunction, specialize, apply, definition_registry, canonical,
    json_hash, quadratic_trace_exists_source_pins, _inert_metrics,
)

SCHEMA = "sqrt2-power-quadratic-product-exists-v1"
PARAMETERS = F + ("L",)
NAMED_SOURCE = forall(PARAMETERS,
    named("IQuadNonzeroFactors", *F, "L") + " -> " + exists(U+C,
        trace(F, U, "L") + " /\\ (" + at(U, "L", C) + " /\\ ~(rp=rn /\\ sp=sn))"))
TARGET_SHA256 = "d8aa407a2364ad85cd2dec414b57462a4c78a2efe4b79b49e06a0b0bd78acb2d"
DECODE_TARGET_SHA256 = "e864f274188cf0a1f8278bca5152d88bd33c4f98f7692b849517cfffb9a0318a"
ARCHIVES = (
    dict(case="QF001", path="research/arithmetic-library/sqrt2-power/observations/shared-wave-quadratic-product-trace-v1/generation-process.json.gz",
        bytes=116784, sha256="97f79bf2f2b0d82cb2faddc5dff2e2b53070bb02102687f436604b6d720bb3b9",
        raw_bytes=5199062, raw_sha256="392685ef742c4f23a1981d4a2fbba56d979f28466293740e3f75a8b18c4caae4",
        bundle_bytes=3240416, bundle_sha256="4933e2fe5136b4c700fbe804b81d20ba2331ec53c1f0a18501bab03becf2675f",
        nodes=224, root=223, target_ast_sha256="d27f07d45ef919c5b7597e15e774478ab7ae46fc82e18fd16fa82e860df90768"),
    dict(case="QF002", path="research/arithmetic-library/sqrt2-power/observations/shared-wave-quadratic-trace-exists-v2/generation-process.json.gz",
        bytes=19998, sha256="d31257950f7bffc65448973e31020e267945dd87119c98d9a658ad04e18f8dd8",
        raw_bytes=340461, raw_sha256="ad93c09e794dd27e0966d7dc8c028d84197d8dc14ef3422fdb9637e01b8e91d5",
        bundle_bytes=207926, bundle_sha256="a27dba505ab5151a5842f58f5537219f9b5958bd3310103b98ac0dc6dff29b98",
        nodes=108, root=107, target_ast_sha256="bce1bbd903c3dd33cd47e30166931e5de2a0dde0f5d058bab6051dcfa4e6400b"),
)
ROOT_DEPENDENCIES = ("QF001", "QF002", "decode")


class ProductExistsError(ValueError):
    """Changed exact statement, archived body, source or unchanged limit."""


def frozen_quadratic_product_exists_target():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Forall, Exists, Imp, And
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE, registry=definition_registry())
    body = target
    for _ in range(9):
        if type(body) is not Forall:
            raise ProductExistsError("QF003 parameter binder shape changed")
        body = body.body
    if type(body) is not Imp:
        raise ProductExistsError("QF003 nonzero-factors premise changed")
    body = body.consequent
    for _ in range(12):
        if type(body) is not Exists:
            raise ProductExistsError("QF003 witness binder shape changed")
        body = body.body
    if type(body) is not And or json_hash(encode_formula(target)) != TARGET_SHA256:
        raise ProductExistsError("QF003 original exact target changed")
    return target


def source_contract():
    return dict(code="QF003", schema=SCHEMA, source=NAMED_SOURCE,
        statement_ast_sha256=TARGET_SHA256, parameters=list(PARAMETERS), premise_count=1,
        premise="every decoded factor below L is represented nonzero",
        existential_stream_parameters=list(U), existential_value_parameters=list(C),
        supplied_trace_required=False, supplied_terminal_value_required=False,
        starts_at_one=True, actual_beta_transitions=True,
        reused_definition_ids=["ND0390", "ND0391", "ND0392", "ND0393"],
        original_HA_checked=False, authority="source_contract_not_proof_authority",
        height_bound=False, real_interpretation=False, rational_denominator_claim=False,
        closes_IR046=False, closes_IR072=False, IR_parents_closed=0, library_admissions=0)


def quadratic_product_exists_source_pins():
    result = quadratic_trace_exists_source_pins()
    if result["scripts/sqrt2_power_quadratic_trace_exists.py"]["sha256"] != "4269d6b9a2282fad3870b408578e2894544c4b172ea76ea2891945adce25ba1a":
        raise ProductExistsError("actual QF002 producer source changed")
    for pin in ARCHIVES:
        with (ROOT / pin["path"]).open("rb") as stream:
            raw = stream.read(pin["bytes"]+1)
        if len(raw) != pin["bytes"] or sha256(raw).hexdigest() != pin["sha256"]:
            raise ProductExistsError("actual product proof archive changed")
        result[pin["path"]] = dict(bytes=len(raw), sha256=pin["sha256"])
    name = "scripts/sqrt2_power_quadratic_product_exists.py"
    raw = (ROOT / name).read_bytes()
    if len(raw) > 16*1024**2:
        raise ProductExistsError("QF003 producer source exceeds unchanged bound")
    result[name] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    return result


def read_archive(pin, archive_path=None):
    path = ROOT / pin["path"] if archive_path is None else Path(archive_path)
    with path.open("rb") as stream:
        packed = stream.read(pin["bytes"]+1)
    if len(packed) != pin["bytes"] or sha256(packed).hexdigest() != pin["sha256"]:
        raise ProductExistsError("compressed actual proof bytes changed")
    with gzip.GzipFile(fileobj=BytesIO(packed)) as stream:
        raw = stream.read(pin["raw_bytes"]+1)
    del packed
    if len(raw) != pin["raw_bytes"] or sha256(raw).hexdigest() != pin["raw_sha256"]:
        raise ProductExistsError("actual generation envelope changed")
    process = json.loads(raw)
    del raw
    output = json.loads(process["stdout"])
    del process
    if output.get("case") != pin["case"] or output.get("schema") != "sqrt2-power-shared-proof-wave-v1":
        raise ProductExistsError("actual archive owner changed")
    payload = output["bundle"]
    del output
    if (type(payload) is not str or len(payload.encode()) != pin["bundle_bytes"]
            or sha256(payload.encode()).hexdigest() != pin["bundle_sha256"]):
        raise ProductExistsError("actual canonical proof bundle changed")
    value = json.loads(payload)
    if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
            or value[1] != pin["root"] or len(value[3]) != pin["nodes"]
            or json_hash(value[2]) != pin["target_ast_sha256"] or value[2] != value[3][pin["root"]][1]):
        raise ProductExistsError("actual full proof envelope changed")
    return value[3]


def merge_actual_rows(*, limits=None):
    """Only exact full-row bytes deduplicate; dependency order is preserved."""
    from sqrt2_power_binary_dag import BinaryDAGLimits
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise ProductExistsError("expected unchanged BinaryDAGLimits")
    rows, keys, endpoints = [], {}, {}
    total, deepest = 0, 0
    for pin in ARCHIVES:
        original = read_archive(pin)
        remap = {}
        for old, row in enumerate(original):
            if (type(row) is not list or len(row) != 4 or type(row[2]) is not list
                    or len(set(row[2])) != len(row[2])
                    or any(type(d) is not int or not 0 <= d < old for d in row[2])):
                raise ProductExistsError("archived dependency order changed")
            linked = [remap[d] for d in row[2]]
            new = [row[0], row[1], linked, row[3]]
            key = canonical(new)
            if key not in keys:
                count, depth = _inert_metrics(new[3], limits)
                if type(row[0]) is not int or row[0] < 8*count+16:
                    raise ProductExistsError("actual row fuel changed")
                total, deepest = total+count, max(deepest, depth)
                if total > limits.max_total_body_nodes or len(rows)+1 >= limits.max_nodes:
                    raise ProductExistsError("merged proof exceeds unchanged body/node limits")
                keys[key] = len(rows)
                rows.append(new)
            remap[old] = keys[key]
        endpoints[pin["case"]] = remap[pin["root"]]
        if pin["case"] == "QF002":
            if json_hash(original[103][1]) != DECODE_TARGET_SHA256:
                raise ProductExistsError("actual four-component totality target changed")
            endpoints["decode"] = remap[103]
        del original, remap
        gc.collect()
    if len(canonical(rows)) > limits.max_payload_bytes:
        raise ProductExistsError("actual merged rows exceed unchanged payload limit")
    return rows, endpoints, total, deepest


def _root_body():
    def main(s):
        def supplied_trace(t):
            def supplied_value(u):
                nonzero = apply(specialize(u, "QF001", *u.terms(F+U), u.term("L"), *u.terms(C)),
                    u.hyp("trace"), u.hyp("factors"), u.hyp("value"))
                return witness(u.terms(U+C), conjunction(u.hyp("trace"), u.hyp("value"), nonzero))
            return eliminate(t, specialize(t, "decode", *t.terms(U), t.term("L")), C, "value", supplied_value)
        return eliminate(s, specialize(s, "QF002", *s.terms(F), s.term("L")), U, "trace", supplied_trace)
    return introduce(Scope(), (), ROOT_DEPENDENCIES, lambda s: introduce(s, PARAMETERS, ("factors",), main))


@dataclass(frozen=True)
class QuadraticProductExistsCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_quadratic_product_exists(*, limits=None):
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from peano_lab.library.proof_bundle import (decode_proof_bundle, encode_formula,
        encode_proof, check_proof_bundle)
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise ProductExistsError("expected unchanged BinaryDAGLimits")
    before = quadratic_product_exists_source_pins()
    target = frozen_quadratic_product_exists_target()
    rows, endpoints, total, deepest = merge_actual_rows(limits=limits)
    ancestor_count, ancestor_total, ancestor_digest = len(rows), total, json_hash(rows)
    body = _root_body()
    count, depth = _body_metrics(body, limits)
    if total+count > limits.max_total_body_nodes:
        raise ProductExistsError("aggregate QF003 ordinary-body limit exceeded")
    _row_preflight(target, body, limits)
    dependencies = [endpoints[d] for d in ROOT_DEPENDENCIES]
    rows.append([8*count+16, encode_formula(target), dependencies, encode_proof(body)])
    payload = canonical(["peano-lab-bundle-v1", len(rows)-1, encode_formula(target), rows]).decode()+"\n"
    if len(payload.encode()) > limits.max_payload_bytes:
        raise ProductExistsError("QF003 unchanged payload limit exceeded")
    del rows, body
    gc.collect()
    bundle, decoded = decode_proof_bundle(payload, limits=limits.bundle_limits())
    if decoded != target:
        raise ProductExistsError("decoded QF003 differs from original target")
    receipt = check_proof_bundle(bundle, target, limits=limits.bundle_limits())
    if receipt.target != target or quadratic_product_exists_source_pins() != before:
        raise ProductExistsError("QF003 target/source changed during canonical replay")
    provenance = dict(source_contract(), original_HA_checked=True, source_pins=before,
        canonical_bytes_replayed=True, empty_context=True, original_archives=list(ARCHIVES),
        actual_ancestor_nodes=ancestor_count, actual_ancestor_body_nodes=ancestor_total,
        merged_ancestor_rows_sha256=ancestor_digest, root_dependencies=dependencies,
        constructed_trace_and_terminal_tuple=True, integer_product_nonzero_proved=True,
        new_axioms=[], external_certificate_references=[], independent_lean_checked=False,
        solver_calls=0, local_have_compiler_calls=0, ring_normalizer_calls=0)
    return QuadraticProductExistsCertificate(target, bundle, payload, receipt, max(deepest, depth), provenance)
