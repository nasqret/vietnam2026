"""Fail-closed presentation of explicitly indexed, historical wave evidence.

The caller must independently pin the index and its target identities. Nothing
is discovered by directory scanning. This reader checks inert bytes, protocol
consistency, archived source snapshots and structural counts, NEVER kernel or
Lean proofs. Receipts remain local observations, not theorem admissions.
"""
from __future__ import annotations

from hashlib import sha256
import gzip
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import zlib

from sqrt2_power_automation_baseline import runtime
from sqrt2_power_composition_chunks import CHUNK_PINS

ROOT = Path(__file__).resolve().parents[1]
INDEX_SCHEMA = "sqrt2-power-wave-evidence-index-v1"
WAVE_SCHEMA = "sqrt2-power-shared-proof-wave-v1"
RESULT_SCHEMA = "sqrt2-power-wave-results-v1"
MAX_RAW = 16 * 1024**2
MAX_BUNDLE = 8 * 1024**2
MAX_REPORTS = 64
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_MODULES = ("Syntax", "Substitution", "Derivation", "Semantics", "Checker", "Soundness",
            "Codec", "ProofBundle", "VerifyBundle")
_AUDIT_SHA256 = "59b5d0e5897ffac038415af3a11c61db6c8c36f990bb32b59739959813f62253"
_AUDIT_OUTPUT = ("'PeanoLab.checkBundle_derives' depends on axioms: [propext, Quot.sound]\n"
    "'PeanoLab.checkBundle_sound' depends on axioms: [propext, Classical.choice, Quot.sound]\n")
_COVERAGE = {
    "P10": ("full_fixed_P10_not_IR064", "full_fixed_child"),
    "P08-eprover": ("P08_supporting_leaf_not_full_pilot", "supporting_leaf"),
    "P08-vampire": ("P08_supporting_leaf_not_full_pilot", "supporting_leaf"),
    "P04-ground": ("full_fixed_degree7_composition_child", "full_fixed_child"),
    "P04-soundness": ("supporting_conditional_trace_soundness", "supporting_leaf"),
    "IR016": ("IR016_natural_core_not_full_irrationality", "supporting_leaf"),
    "SN001": ("signed_norm_zero_core_not_IR032", "supporting_leaf"),
    "NG001": ("universal_natural_gap_not_full_campaign", "supporting_leaf"),
    "SN002": ("signed_norm_integer_gap_not_full_IR032", "supporting_leaf"),
    "SN003": ("signed_norm_multiplicativity_not_rational_IR031", "supporting_leaf"),
    "CV001": ("universal_natural_convolution_vanishing_not_IR079", "supporting_leaf"),
    "RN002": ("rational_norm_product_denominator_not_full_IR031", "supporting_leaf"),
    "RN001": ("rational_norm_representative_transport_not_full_IR031", "supporting_leaf"),
    "SI001": ("signed_integer_binary_nonzero_not_quadratic_finite_IR046", "supporting_leaf"),
    "QN001": ("quadratic_integer_binary_nonzero_not_finite_IR046", "supporting_leaf"),
    "QF001": ("quadratic_finite_trace_nonzero_not_trace_totality_or_real_IR046", "supporting_leaf"),
    **{f"RF{n:03d}": ("full_named_rational_foundation_not_IR001", "named_rational_foundation")
       for n in range(1, 7)},
    **{name: ("complete_exact_subconjunction_child", "supporting_leaf") for name in CHUNK_PINS},
}


class EvidenceError(ValueError):
    """Unlisted, altered, oversized or internally inconsistent observation."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _same(left, right):
    return _canonical(left) == _canonical(right)


def _shape(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise EvidenceError("missing or unknown protocol fields")


def _natural(value, maximum=2**63 - 1):
    if type(value) is not int or not 0 <= value <= maximum:
        raise EvidenceError("counter is not an exact bounded natural")
    return value


def _hash(value):
    if type(value) is not str or not _HASH.fullmatch(value):
        raise EvidenceError("invalid exact SHA-256")
    return value


def _seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise EvidenceError("invalid elapsed/CPU observation")
    return value


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise EvidenceError("duplicate JSON key")
            result[key] = value
        return result
    def bad_constant(value):
        raise EvidenceError("non-finite JSON constant")
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise EvidenceError("invalid or excessively nested JSON") from exc


def _relative(value):
    if (type(value) is not str or not value or "\\" in value
        or Path(value).is_absolute() or any(part in ("", ".", "..") for part in value.split("/"))):
        raise EvidenceError("unsafe relative evidence path")
    return Path(value)


def _read_file(base, relative, maximum=MAX_RAW):
    path = Path(base)
    for part in _relative(relative).parts:
        path = path / part
        if path.is_symlink():
            raise EvidenceError("symlink in evidence path")
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                raise EvidenceError("evidence is not one bounded regular file")
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise EvidenceError("indexed evidence file is unavailable") from exc
    if (len(raw) > maximum or len(raw) != before.st_size
        or (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
        raise EvidenceError("evidence changed while reading")
    return raw


def _gunzip(base, path, maximum=MAX_RAW):
    compressed = _read_file(base, path)
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
            raw = stream.read(maximum + 1)
    except (OSError, EOFError, zlib.error) as exc:
        raise EvidenceError("invalid lossless gzip evidence") from exc
    if len(raw) > maximum:
        raise EvidenceError("decompressed evidence exceeds bound")
    return raw


def _pin(raw, pin):
    _shape(pin, ("bytes", "sha256"))
    if len(raw) != _natural(pin["bytes"], MAX_RAW) or sha256(raw).hexdigest() != _hash(pin["sha256"]):
        raise EvidenceError("pinned original bytes/hash changed")


def _indexed_report(root, entry, wave):
    fields = {"path", "bytes", "sha256"} | ({"case", "target_ast_sha256"} if wave else set())
    _shape(entry, fields)
    if wave and (type(entry["case"]) is not str or entry["case"] not in _COVERAGE):
        raise EvidenceError("unknown explicitly indexed case")
    if wave:
        _hash(entry["target_ast_sha256"])
        if entry["case"] in CHUNK_PINS and entry["target_ast_sha256"] != CHUNK_PINS[entry["case"]][1]:
            raise EvidenceError("composition child differs from its exact frozen subtree")
    raw = _read_file(root, entry["path"])
    _pin(raw, {key: entry[key] for key in ("bytes", "sha256")})
    return _json(raw), raw, Path(root) / _relative(entry["path"]).parent


def _no_admission(row, model=False):
    for key in ("IR_parents_closed", "library_admissions") + (("model_proof_search_calls",) if model else ()):
        if _natural(row.get(key)) != 0:
            raise EvidenceError("observation attempts a parent closure/admission claim")


def _source_snapshots(report, folder):
    pins, snapshots = report["source_pins"], report["source_snapshots"]
    if (type(pins) is not dict or type(snapshots) is not dict or not 1 <= len(pins) <= 128
        or set(pins) != set(snapshots)):
        raise EvidenceError("source snapshot inventory differs from source pins")
    for name, pin in pins.items():
        _relative(name)
        if snapshots[name] != "sources/" + name + ".gz":
            raise EvidenceError("source snapshot identity changed")
        _shape(pin, ("bytes", "sha256"))
        _pin(_gunzip(folder, snapshots[name], _natural(pin["bytes"], MAX_RAW)), pin)


def _validate_process(process, command=None, input_bytes=b""):
    try:
        limits = runtime().ProcessLimits(**process["limits"])
        runtime().validate_process_record(process,
            command=tuple(process["command"]) if command is None else tuple(command),
            limits=limits, input_bytes=input_bytes)
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceError("invalid original process receipt/output hashes") from exc
    return process["reason"] == "exited" and process["returncode"] == 0 and process["output_truncated"] is False


def _phase(report, folder, phase, input_bytes):
    summary = report["process_records"][phase]
    _shape(summary, ("path", "raw_sha256", "reason", "returncode", "resources"))
    if summary["path"] != phase + "-process.json.gz":
        raise EvidenceError("phase process path changed")
    raw = _gunzip(folder, summary["path"])
    if sha256(raw).hexdigest() != _hash(summary["raw_sha256"]):
        raise EvidenceError("original gzipped process bytes changed")
    process = _json(raw)
    if raw != _canonical(process):
        raise EvidenceError("process record is not the original canonical bytes")
    command = process.get("command")
    flag = "--worker" if phase == "generation" else "--replay"
    if (type(command) is not list or len(command) != 5 or command[1] != "-B"
        or Path(command[2]).name != "run_sqrt2_power_wave.py" or command[-2:] != [flag, report["case"]]):
        raise EvidenceError("worker command changed its exact phase/case")
    succeeded = _validate_process(process, command, input_bytes)
    for key in ("reason", "returncode", "resources"):
        if not _same(process[key], summary[key]):
            raise EvidenceError("process summary differs from original bytes")
    cpu, wall = (28, 40) if phase == "generation" else (20, 30)
    limits = process["limits"]
    if (limits["cpu_seconds"] != cpu or not cpu <= limits["wall_seconds"] <= wall
        or limits["rss_bytes"] != 768 * 1024**2 or limits["output_bytes"] != MAX_BUNDLE):
        raise EvidenceError("worker resource contract changed")
    value = _json(process["stdout"]) if succeeded else None
    return process, value


_PROOF_LAYOUT = {
    "hyp": (2, ()), "imp_intro": (2, (1,)), "imp_elim": (3, (1, 2)),
    "cut": (5, (3, 4)), "and_intro": (3, (1, 2)), "and_elim_l": (2, (1,)),
    "and_elim_r": (2, (1,)), "or_intro_l": (2, (1,)), "or_intro_r": (2, (1,)),
    "or_elim": (4, (1, 2, 3)), "bot_elim": (2, (1,)), "forall_intro": (2, (1,)),
    "forall_elim": (3, (1,)), "exists_intro": (3, (2,)), "exists_elim": (3, (1, 2)),
    "eq_refl": (2, ()), "eq_sym": (2, (1,)), "eq_trans": (3, (1, 2)),
    "cong_s": (2, (1,)), "cong_add": (3, (1, 2)), "cong_mul": (3, (1, 2)),
    "eq_subst": (4, (2, 3)), "axiom": (2, ()), "ind": (4, (2, 3)),
}


def _proof_count(body):
    pending, count = [(body, 1)], 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > 200000 or depth > 256 or type(node) is not list or not node or type(node[0]) is not str:
            raise EvidenceError("inert proof body exceeds its structural bound")
        layout = _PROOF_LAYOUT.get(node[0])
        if layout is None or len(node) != layout[0]:
            raise EvidenceError("unknown/classical proof constructor or arity")
        if node[0] == "hyp":
            _natural(node[1])
        if node[0] == "axiom" and node[1] not in ("PA1", "PA2", "PA3", "PA4", "PA5", "PA6"):
            raise EvidenceError("unknown inert arithmetic axiom name")
        pending.extend((node[index], depth + 1) for index in layout[1])
    return count


def _bundle(payload, digest, target_hash):
    if type(payload) is not str or len(payload.encode()) > MAX_BUNDLE:
        raise EvidenceError("canonical proof artifact exceeds bound")
    raw = payload.encode()
    if sha256(raw).hexdigest() != _hash(digest):
        raise EvidenceError("canonical bundle bytes/hash changed")
    tree = _json(raw)
    if (type(tree) is not list or len(tree) != 4 or tree[0] != "peano-lab-bundle-v1"
        or type(tree[3]) is not list or not 1 <= len(tree[3]) <= 4096):
        raise EvidenceError("invalid inert bundle envelope")
    canonical = json.dumps(tree, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode() + b"\n"
    if raw != canonical or sha256(_canonical(tree[2])).hexdigest() != target_hash:
        raise EvidenceError("noncanonical bytes or changed original target AST")
    root = _natural(tree[1], len(tree[3]) - 1)
    total = 0
    for index, node in enumerate(tree[3]):
        if type(node) is not list or len(node) != 4 or type(node[2]) is not list:
            raise EvidenceError("invalid inert local-node shape")
        dependencies = [_natural(value, index - 1) for value in node[2]]
        if len(dependencies) != len(set(dependencies)):
            raise EvidenceError("duplicate local dependency")
        count = _proof_count(node[3])
        if _natural(node[0]) < 8 * count + 16:
            raise EvidenceError("body fuel is below the original conservative allowance")
        total += count
        if total > 200000:
            raise EvidenceError("aggregate ordinary body count exceeds bound")
    if not _same(tree[3][root][1], tree[2]):
        raise EvidenceError("bundle root target differs from envelope")
    reached, pending = set(), [root]
    while pending:
        node = pending.pop()
        if node not in reached:
            reached.add(node)
            pending.extend(tree[3][node][2])
    if len(reached) != len(tree[3]):
        raise EvidenceError("bundle contains unreachable local nodes")
    return raw, dict(local_nodes=len(tree[3]), proof_nodes=total, kernel_calls=len(tree[3]), root=root)


def _external_target(tree, depth=0):
    tags = {"Var": "var", "Zero": "zero", "Succ": "succ", "Add": "add", "Mul": "mul",
            "Eq": "eq", "Bot": "bot", "And": "and", "Or": "or", "Imp": "imp",
            "Forall": "forall", "Exists": "exists"}
    if depth > 256 or type(tree) is not list or not tree or type(tree[0]) is not str or tree[0] not in tags:
        raise EvidenceError("unknown external target AST constructor")
    return [tags[tree[0]], *[(_natural(value) if type(value) is int else _external_target(value, depth + 1))
                            for value in tree[1:]]]


def _external(report, folder, target_hash):
    summary = report.get("live_external")
    if summary is None:
        return b"", None
    raw = _gunzip(folder, "live-solver-input-and-observation.json.gz")
    if sha256(raw).hexdigest() != _hash(summary["observation_sha256"]) or summary.get("HA_authority") is not False:
        raise EvidenceError("external hint bytes/authority changed")
    value = _json(raw)
    if _canonical(value) != raw:
        raise EvidenceError("noncanonical saved external observation")
    _shape(value, ("problem", "observed", "contract") if report["case"].startswith("P08-") else ("problem", "observed"))
    problem, observed = value["problem"], value["observed"]
    data = problem["input"].encode()
    if len(data) != _natural(problem["input_bytes"], 2 * 1024**2) or sha256(data).hexdigest() != _hash(problem["input_sha256"]):
        raise EvidenceError("external original input bytes changed")
    for key in ("input_sha256", "export_sha256"):
        if observed.get(key) != problem.get(key):
            raise EvidenceError("external export binding changed")
    original_export = {key: value for key, value in problem.items() if key != "export_sha256"}
    encoded_export = json.dumps(original_export, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":"), allow_nan=False).encode()
    if sha256(encoded_export).hexdigest() != problem["export_sha256"]:
        raise EvidenceError("external canonical export hash changed")
    if (sha256(_canonical(_external_target(problem["target"]["ast"]))).hexdigest() != target_hash
        or observed.get("target_ast_sha256") != problem["target"]["ast_sha256"]):
        raise EvidenceError("external conjecture is not the indexed HA target")
    if type(observed.get("source_pins")) is not dict or not observed["source_pins"]:
        raise EvidenceError("external source pins are absent")
    for name, pin in observed["source_pins"].items():
        if not _same(pin, report["source_pins"].get(name)):
            raise EvidenceError("external source pin differs from archived original sources")
    for key in ("ha_checked", "proof_log_checked", "ha_translation_verified"):
        if observed.get(key) is not False:
            raise EvidenceError("external hint claims proof authority")
    for key in ("solver_proofs_reconstructed", "model_proof_search_calls", "IR_obligations_closed"):
        if _natural(observed.get(key)) != 0:
            raise EvidenceError("external hint claims theorem reconstruction")
    if observed.get("solver") != summary.get("solver") or not _same(observed.get("observation"), summary.get("status")):
        raise EvidenceError("external solver summary changed")
    if not _same(observed.get("budget"), summary.get("budget")):
        raise EvidenceError("external resource reservation changed")
    if not _same(observed.get("capability", {}).get("binary"), summary.get("binary")):
        raise EvidenceError("external binary pin changed")
    if summary.get("binary") is not None:
        _shape(summary["binary"], ("bytes", "sha256"))
        _natural(summary["binary"]["bytes"])
        _hash(summary["binary"]["sha256"])
    if observed.get("process") is not None:
        _validate_process(observed["process"], observed.get("argv"), data)
    version = observed.get("capability", {}).get("version_probe")
    if version is not None:
        _validate_process(version)
    return raw if report["case"].startswith("P08-") else b"", summary


def _wave(root, entry, downloads):
    report, raw_report, folder = _indexed_report(root, entry, True)
    required = {"schema", "case", "source_pins", "authority", "source_snapshots", "status",
        "IR_parents_closed", "library_admissions", "independent_lean_checked", "model_proof_search_calls",
        "results", "process_records", "elapsed_wall_seconds", "budget"}
    if type(report) is not dict or set(report) not in (required, required | {"live_external"}):
        raise EvidenceError("unknown wave-report protocol fields")
    if (report["schema"] != WAVE_SCHEMA or report["case"] != entry["case"]
        or report["authority"] != "local_observation_not_library_admission"
        or report["independent_lean_checked"] is not False):
        raise EvidenceError("wave identity/authority changed")
    _no_admission(report, True)
    _seconds(report["elapsed_wall_seconds"])
    budget = report["budget"]
    _shape(budget, ("cpu_seconds", "wall_seconds", "max_workers", "rss_bytes", "note"))
    for name, expected in (('cpu_seconds', 60), ('wall_seconds', 90), ('max_workers', 1), ('rss_bytes', 768 * 1024**2)):
        if _natural(budget[name]) != expected:
            raise EvidenceError("wave resource budget changed")
    _source_snapshots(report, folder)
    records, results = report["process_records"], report["results"]
    if type(records) is not dict or set(records) not in ({"generation"}, {"generation", "fresh_replay"}) or type(results) is not dict:
        raise EvidenceError("unknown/missing process phases")
    worker_input, external = _external(report, folder, entry["target_ast_sha256"])
    generation, producer = _phase(report, folder, "generation", worker_input)
    bundle, metrics, replay = None, None, None
    if producer is None:
        if results or "fresh_replay" in records:
            raise EvidenceError("failed producer was promoted or replayed")
    else:
        _shape(producer, ("schema", "case", "status", "source_pins", "target_ast_sha256", "bundle",
            "bundle_sha256", "diagnostics", "IR_parents_closed", "model_proof_search_calls", "independent_lean_checked"))
        if (producer["schema"] != WAVE_SCHEMA or producer["case"] != entry["case"]
            or producer["status"] != "native_generated" or producer["independent_lean_checked"] is not False
            or _natural(producer["IR_parents_closed"]) != 0 or _natural(producer["model_proof_search_calls"]) != 0
            or not _same(producer["source_pins"], report["source_pins"])
            or producer["target_ast_sha256"] != entry["target_ast_sha256"]):
            raise EvidenceError("producer target/source/authority changed")
        if not _same(results.get("generation"), {key: value for key, value in producer.items() if key != "bundle"}):
            raise EvidenceError("generation summary differs from original stdout")
        if producer["diagnostics"].get("coverage") != _COVERAGE[entry["case"]][0]:
            raise EvidenceError("coverage differs from the frozen case")
        bundle, metrics = _bundle(producer["bundle"], producer["bundle_sha256"], entry["target_ast_sha256"])
        if "fresh_replay" in records:
            _, replay = _phase(report, folder, "fresh_replay", _canonical(producer))
        expected_results = {"generation"} | ({"fresh_replay"} if replay is not None else set())
        if set(results) != expected_results:
            raise EvidenceError("unchecked replay summary was injected")
        if replay is not None:
            _shape(replay, ("schema", "case", "status", "target_ast_sha256", "bundle_sha256", "source_pins",
                "local_nodes", "proof_nodes", "kernel_calls", "original_target_checked", "empty_context",
                "false_target_rejected", "forged_body_rejected", "IR_parents_closed", "library_admissions", "independent_lean_checked"))
            _no_admission(replay)
            if (replay["schema"] != WAVE_SCHEMA or replay["case"] != entry["case"]
                or replay["status"] != "fresh_ordinary_HA_checked" or replay["independent_lean_checked"] is not False
                or replay["bundle_sha256"] != producer["bundle_sha256"] or replay["target_ast_sha256"] != entry["target_ast_sha256"]
                or not _same(replay["source_pins"], report["source_pins"]) or not _same(replay, results["fresh_replay"])):
                raise EvidenceError("fresh replay differs from exact producer/source/target bytes")
            for key in ("original_target_checked", "empty_context", "false_target_rejected", "forged_body_rejected"):
                if replay[key] is not True:
                    raise EvidenceError("required fresh replay rejection/check is missing")
            if any(_natural(replay[key]) != metrics[key] for key in ("local_nodes", "proof_nodes", "kernel_calls")):
                raise EvidenceError("reported proof counts differ from inert bundle structure")
    status = "fresh_ordinary_HA_checked" if replay is not None else "not_checked"
    if report["status"] != status:
        raise EvidenceError("wave status is not justified by both original process outputs")
    report_link = "evidence/wave-report-" + entry["sha256"] + ".json.gz"
    downloads[report_link] = gzip.compress(raw_report, mtime=0)
    row = dict(case=entry["case"], attempt=folder.name, status=status, target_ast_sha256=entry["target_ast_sha256"],
        coverage=_COVERAGE[entry["case"]][0], scope=_COVERAGE[entry["case"]][1], report_path=entry["path"],
        report_sha256=entry["sha256"], report_download=report_link, independent_lean_checked=False,
        elapsed_wall_seconds=report["elapsed_wall_seconds"], source_snapshot_count=len(report["source_pins"]),
        source_pins_sha256=sha256(_canonical(report["source_pins"])).hexdigest(),
        generation_reason=generation["reason"], generation_returncode=generation["returncode"],
        IR_parents_closed=0, library_admissions=0, live_external=external)
    if replay is not None:
        digest = sha256(bundle).hexdigest()
        link = "evidence/" + digest + ".json.gz"
        downloads[link] = gzip.compress(bundle, mtime=0)
        row.update(bundle_sha256=digest, bundle_bytes=len(bundle), proof_download=link, **metrics)
    return row


def _lean(root, entry, rows, downloads):
    report, raw, folder = _indexed_report(root, entry, False)
    fields = {"schema", "authority", "stage", "lean_binary", "source_pins", "compilation", "checks",
        "status", "IR_parents_closed", "library_admissions", "mode", "toolchain_library_pins",
        "version_probe", "elapsed_wall_seconds", "measured_cpu_seconds", "limits"}
    if type(report) is not dict or set(report) not in (fields, fields | {"axiom_audit"}, fields | {"axiom_audit", "negative_controls"}):
        raise EvidenceError("unknown fresh Lean report fields")
    has_negatives = "negative_controls" in report
    if (report.get("schema") != "sqrt2-power-fresh-lean-v1"
        or report.get("authority") != "independent_local_check_not_admission"
        or report.get("mode") != "fresh_olean_closure_and_Lean_run_not_standalone_C_build"):
        raise EvidenceError("unknown independent Lean observation protocol")
    _no_admission(report)
    _shape(report["lean_binary"], ("bytes", "sha256"))
    _natural(report["lean_binary"]["bytes"])
    _hash(report["lean_binary"]["sha256"])
    libraries = report["toolchain_library_pins"]
    if type(libraries) is not dict or set(libraries) != {"Init.olean", "Lean.olean", "libleanshared.dylib",
            "libInit_shared.dylib", "libleanshared_1.dylib", "libleanshared_2.dylib"}:
        raise EvidenceError("toolchain library pin inventory changed")
    for pin in libraries.values():
        _shape(pin, ("bytes", "sha256"))
        _natural(pin["bytes"])
        _hash(pin["sha256"])
    expected_sources = {f"PeanoLab/{name}.lean" for name in _MODULES} | {"Sqrt2PowerLeanAudit.lean"}
    if type(report.get("source_pins")) is not dict or set(report["source_pins"]) != expected_sources:
        raise EvidenceError("fresh Lean source closure changed")
    for name, pin in report["source_pins"].items():
        _pin(_read_file(folder, "sources/" + name), pin)
    if report["source_pins"]["Sqrt2PowerLeanAudit.lean"]["sha256"] != _AUDIT_SHA256:
        raise EvidenceError("frozen endpoint axiom-audit source changed")
    version = report.get("version_probe")
    if not _validate_process(version) or "version 4.31.0" not in version["stdout"]:
        raise EvidenceError("fresh Lean version probe failed")
    version_command = version["command"]
    if len(version_command) != 2 or version_command[1] != "--version":
        raise EvidenceError("Lean version command changed")
    if type(report["stage"]) is not str or not Path(report["stage"]).is_absolute():
        raise EvidenceError("original fresh Lean stage is not absolute")
    stage = Path(report["stage"])
    common = [version_command[0], "-j", "1", "-M", "768", "-R", str(stage)]
    compilation = report.get("compilation")
    if type(compilation) is not list or len(compilation) > len(_MODULES):
        raise EvidenceError("invalid fresh compilation inventory")
    for index, record in enumerate(compilation):
        if type(record) is not dict or set(record) not in ({"module", "process"}, {"module", "process", "olean"}):
            raise EvidenceError("unknown compilation record fields")
        if record.get("module") != _MODULES[index]:
            raise EvidenceError("fresh compilation order changed")
        module = stage / "PeanoLab" / record["module"]
        passed = _validate_process(record["process"], common + ["-o", str(module) + ".olean", str(module) + ".lean"])
        if passed and ("olean" not in record or "declaration uses 'sorry'" in record["process"]["stdout"]):
            raise EvidenceError("compiled module lacks a genuine output pin")
        if "olean" in record:
            _shape(record["olean"], ("bytes", "sha256"))
            _natural(record["olean"]["bytes"])
            _hash(record["olean"]["sha256"])
    audit = report.get("axiom_audit")
    compiled = len(compilation) == len(_MODULES) and all(r["process"]["reason"] == "exited" and r["process"]["returncode"] == 0 for r in compilation)
    if audit is not None:
        if (not compiled or not _validate_process(audit, common + [str(stage / "Sqrt2PowerLeanAudit.lean")])
            or audit["stdout"] != _AUDIT_OUTPUT or audit["stderr"] != ""):
            raise EvidenceError("fresh Lean endpoint axiom audit failed")
    checks = report.get("checks")
    if type(checks) is not list or len(checks) > MAX_REPORTS or checks and (not compiled or audit is None):
        raise EvidenceError("Lean bundle checks lack the fresh source compilation/audit")
    by_report = {str(Path(row["report_path"]).parent): row for row in rows}
    accepted = []
    for check in checks:
        check_fields = {"case", "original_observation", "report_sha256", "bundle_sha256", "bundle_bytes",
            "nodes", "target_ast_sha256", "process", "independent_lean_checked"}
        _shape(check, check_fields | ({"root"} if has_negatives else set()))
        row = by_report.get(check.get("original_observation"))
        if row is None or row["status"] != "fresh_ordinary_HA_checked":
            raise EvidenceError("Lean refers to an unlisted or unchecked original observation")
        for key, original in (("case", "case"), ("report_sha256", "report_sha256"),
            ("bundle_sha256", "bundle_sha256"), ("bundle_bytes", "bundle_bytes"),
            ("target_ast_sha256", "target_ast_sha256"), ("nodes", "local_nodes")):
            if not _same(check.get(key), row[original]):
                raise EvidenceError("Lean check changed original report/bundle/target identity")
        if has_negatives and _natural(check["root"]) != row["root"]:
            raise EvidenceError("Lean original root identity changed")
        process = check["process"]
        expected_command = common + ["--run", str(stage / "PeanoLab/VerifyBundle.lean"),
                                     str(stage / "certificates" / (check["case"] + ".json"))]
        passed = _validate_process(process, expected_command)
        command = process["command"]
        if len(command) < 3 or command[-3] != "--run" or Path(command[-2]).name != "VerifyBundle.lean":
            raise EvidenceError("Lean process is not the original bundle endpoint")
        expected = f"ACCEPT\t{command[-1]}\tnodes={row['local_nodes']}\troot={row['root']}\n"
        actually_accepted = passed and process["stderr"] == "" and process["stdout"] == expected
        if type(check.get("independent_lean_checked")) is not bool or check["independent_lean_checked"] is not actually_accepted:
            raise EvidenceError("Lean status differs from exact successful endpoint output")
        if actually_accepted:
            accepted.append(dict(bundle_sha256=row["bundle_sha256"], target_ast_sha256=row["target_ast_sha256"],
                checked_on_case=row["case"], lean_report_sha256=entry["sha256"]))
    negatives = report.get("negative_controls", [])
    negative_summary, negatives_ok = [], True
    if has_negatives:
        if type(negatives) is not list or len(negatives) != 2 or not checks:
            raise EvidenceError("fresh Lean negative-control inventory changed")
        first = by_report[checks[0]["original_observation"]]
        original = gzip.decompress(downloads[first["proof_download"]])
        for record, kind in zip(negatives, ("false-caller-target", "forged-root-body")):
            _shape(record, ("kind", "original_bundle_sha256", "mutated_bundle_sha256", "process", "rejected"))
            if record["kind"] != kind or record["original_bundle_sha256"] != first["bundle_sha256"]:
                raise EvidenceError("negative control is not bound to its original bundle")
            tree = _json(original)
            if kind == "false-caller-target":
                tree[2] = ["bot"]
            else:
                tree[3][tree[1]][3] = ["eq_refl", ["zero"]]
            mutated = _canonical(tree) + b"\n"
            if sha256(mutated).hexdigest() != _hash(record["mutated_bundle_sha256"]):
                raise EvidenceError("negative-control mutation hash changed")
            path = str(stage / "certificates" / (kind + ".json"))
            process = record["process"]
            _validate_process(process, common + ["--run", str(stage / "PeanoLab/VerifyBundle.lean"), path])
            expected_limits = dict(cpu_seconds=5, wall_seconds=10, rss_bytes=768 * 1024**2, output_bytes=1024**2)
            if not _same(process["limits"], expected_limits):
                raise EvidenceError("negative-control resource profile changed")
            marker = process["stdout"] == "REJECT\t" + path + "\n" and process["stderr"] == ""
            rejected = (process["reason"] == "exited" and process["returncode"] == 1
                        and process["output_truncated"] is False and marker)
            if type(record["rejected"]) is not bool or record["rejected"] is not rejected:
                raise EvidenceError("negative-control rejection status differs from original output")
            negatives_ok &= rejected
            negative_summary.append(dict(kind=kind, rejected=rejected,
                original_bundle_sha256=record["original_bundle_sha256"],
                mutated_bundle_sha256=record["mutated_bundle_sha256"]))
    expected_status = ("fresh_lean_checked" if checks and len(accepted) == len(checks) else "some_checks_failed") if compiled and audit is not None else "incomplete"
    if not negatives_ok:
        expected_status = "negative_control_failed"
        accepted = []
    if report.get("status") != expected_status:
        raise EvidenceError("aggregate Lean status contradicts original checks")
    expected_limits = dict(build_cpu_hard_reservation_seconds=112, per_check_cpu_hard_reservation_seconds=21,
        rss_bytes=768 * 1024**2, max_workers=1, controller_wall_seconds=(170 if has_negatives else 150) + 30 * len(checks))
    if has_negatives:
        expected_limits["negative_controls_cpu_hard_reservation_seconds"] = 12
    if not _same(report["limits"], expected_limits):
        raise EvidenceError("fresh Lean resource profile changed")
    cpu = sum(r["process"]["resources"]["cpu_seconds"] for r in compilation + checks)
    cpu += sum(report[key]["resources"]["cpu_seconds"] for key in ("version_probe", "axiom_audit") if key in report)
    cpu += sum(record["process"]["resources"]["cpu_seconds"] for record in negatives)
    if not math.isclose(_seconds(report.get("measured_cpu_seconds")), cpu, rel_tol=1e-12, abs_tol=1e-9):
        raise EvidenceError("Lean CPU total differs from original processes")
    _seconds(report.get("elapsed_wall_seconds"))
    link = "evidence/lean-report-" + entry["sha256"] + ".json.gz"
    downloads[link] = gzip.compress(raw, mtime=0)
    return accepted, dict(report_path=entry["path"], report_sha256=entry["sha256"], report_download=link,
        status=expected_status, original_checks=len(checks), accepted_checks=len(accepted),
        mode=report["mode"], negative_controls_checked=has_negatives and negatives_ok,
        negative_controls=negative_summary, IR_parents_closed=0, library_admissions=0)


def wave_results(index, root=ROOT):
    """Return (presentation data, downloadable gzip bytes), without proof runs."""
    _shape(index, ("schema", "reports", "lean_reports"))
    if index["schema"] != INDEX_SCHEMA:
        raise EvidenceError("unknown explicit wave index schema")
    if any(type(index[key]) is not list or len(index[key]) > MAX_REPORTS for key in ("reports", "lean_reports")):
        raise EvidenceError("explicit wave index exceeds bounded inventory")
    for key in ("reports", "lean_reports"):
        for entry in index[key]:
            if type(entry) is not dict:
                raise EvidenceError("indexed entry is not an exact object")
            _relative(entry.get("path"))
    paths = [entry["path"] for key in ("reports", "lean_reports") for entry in index[key]]
    if len(paths) != len(set(paths)):
        raise EvidenceError("duplicate indexed report path")
    downloads = {}
    rows = [_wave(root, entry, downloads) for entry in index["reports"]]
    lean_reports, by_bundle = [], {}
    for entry in index["lean_reports"]:
        accepted, summary = _lean(root, entry, rows, downloads)
        lean_reports.append(summary)
        for item in accepted:
            by_bundle.setdefault((item["bundle_sha256"], item["target_ast_sha256"]), []).append(item)
    statements = {}
    for row in rows:
        if row["status"] != "fresh_ordinary_HA_checked":
            continue
        lean = by_bundle.get((row["bundle_sha256"], row["target_ast_sha256"]), [])
        row["independent_lean_checked"] = bool(lean)
        row["lean_same_byte_observations"] = lean
        group = statements.setdefault(row["target_ast_sha256"], dict(target_ast_sha256=row["target_ast_sha256"],
            scope=row["scope"], cases=[], attempts=[], independent_lean_checked=False))
        if group["scope"] != row["scope"]:
            raise EvidenceError("same mathematical target was assigned contradictory coverage")
        if row["case"] not in group["cases"]:
            group["cases"].append(row["case"])
        group["attempts"].append(row["attempt"])
        group["independent_lean_checked"] |= bool(lean)
    unique = list(statements.values())
    fresh = sum(row["status"] == "fresh_ordinary_HA_checked" for row in rows)
    view = dict(schema=RESULT_SCHEMA, authority="validated_historical_observations_not_admissions",
        index_sha256=sha256(_canonical(index)).hexdigest(), rows=rows, unique_statements=unique,
        lean_reports=lean_reports, counts=dict(attempts=len(rows), fresh_HA_attempts=fresh,
            failed_or_unchecked_attempts=len(rows)-fresh, unique_HA_statements=len(unique),
            unique_full_fixed_statements=sum(row["scope"] == "full_fixed_child" for row in unique),
            unique_supporting_statements=sum(row["scope"] == "supporting_leaf" for row in unique),
            unique_named_foundations=sum(row["scope"] == "named_rational_foundation" for row in unique),
            unique_Lean_checked_statements=sum(row["independent_lean_checked"] for row in unique)),
        kernel_checks_performed_by_reader=0, Lean_processes_started_by_reader=0,
        IR_parents_closed=0, library_admissions=0, solver_proof_logs_translated=0,
        caveat="Counts deduplicate identical target ASTs; E/V P08 are demonstrations of one supporting statement. Receipts and hashes are observations, not proof authority.")
    return view, downloads
