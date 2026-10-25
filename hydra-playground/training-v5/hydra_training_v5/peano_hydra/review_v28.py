"""Versioned Alpha-v28 reference and hotspot calibration evidence.

The workflow never trains a model, changes a split, grants human approval, or
seals a benchmark. Fresh reference checks and native cold-pass diagnostics are
separate from whether a reviewed model-facing lineage split actually exists.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time

from .cold_replay_v28 import (
    ALPHA_V28_EPOCH, HOTSPOT_NAMES,
    CERTIFICATE_SCHEMA, COLD_REPLAY_SCHEMA, CertificateLimits,
    build_cold_replay_plan, replay_cold_target,
)
from .conformance import build_conformance_cases, check_native_cases, conformance_manifest
from .epoch import freeze_epoch
from .frontier import _pairs, canonical, decode, digest, read_bytes
from .protocol import development_profile
from .reference import (
    BATCH_SIZE, MODULES, build_reference,
    check_reference_cases, inspect_reference, stage_reference,
    validate_build_receipt, validate_reference_identity, validate_reference_provenance,
    validate_reference_results,
)
from .review_runtime import ProcessLimits, run_bounded, validate_process_record
from .review_inputs_v28 import (
    ancillary_input_closure, check_ancillary_inputs, validate_ancillary_inputs,
)
from .review_sources_v28 import check_recorded_source_bytes, source_identity, validate_sources


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_peano_hydra_review_v28.py"
SCHEMA = "peano-hydra-reference-cold-review-v28-v2"
MAX_BYTES = 64 * 1024**2
COLD_LIMITS = ProcessLimits(wall_seconds=45, cpu_seconds=30)
NATIVE_LIMITS = ProcessLimits(wall_seconds=30, cpu_seconds=20)
COLD_LEDGER_SCHEMA = "peano-hydra-cold-review-ledger-v28-v1"
MODES = ("reference-only", "native-hotspots", "full-plan-only")
FALSE_CLAIMS = ("model_training_authorized", "independent_human_review_granted",
                "h0_complete", "h1_complete", "sealed_benchmark", "research_claim_eligible")
PLAN_FIELDS = {
    "schema", "status", "mode", "source", "execution_root", "profile", "epoch_sha256",
    "reference", "reference_project", "conformance", "cold_plan", "cold_selection",
    "cold_wall_budget", "parallel_workers", "native_limits", "reserved_reference_processes",
    "worker_reservations", "whole_controller_guard", "model_calls", "solver_calls", "data_written",
    "ancillary_inputs", "plan_sha256", *FALSE_CLAIMS,
}
REPORT_FIELDS = {
    "schema", "status", "started_at", "finished_at", "plan", "cases", "plan_sha256",
    "evidence", "summary", "model_calls", "solver_calls", "report_sha256", *FALSE_CLAIMS,
}


class HydraReviewError(ValueError):
    """Missing or inconsistent review evidence must not authorize progression."""


def read_record(path: Path) -> dict[str, object]:
    return decode(read_bytes(path, limit=MAX_BYTES), limit=MAX_BYTES)


def _relative(path: Path) -> str:
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT):
        raise HydraReviewError("automatic review inputs must stay inside the selected repository")
    return resolved.relative_to(ROOT).as_posix()


def _same(actual: object, expected: object) -> bool:
    """Canonical equality does not confuse JSON booleans with integer counts."""
    return canonical(actual) == canonical(expected)


def _execution_root(value: object) -> str:
    # Historical execution paths need not exist during archive verification.
    # They describe saved commands; they are never executed or used as inputs.
    if (type(value) is not str or not 1 <= len(value.encode("utf-8")) <= 4096
        or not Path(value).is_absolute() or Path(value).as_posix() != value
        or ".." in Path(value).parts or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise HydraReviewError("execution root must be one canonical absolute historical path")
    return value


def _worker_command(execution_root: str) -> tuple[str, ...]:
    return (sys.executable, "-I", "-B", str(Path(_execution_root(execution_root)) / "scripts/check_peano_hydra_review_v28.py"), "--worker")


def _signed(record: dict[str, object], field: str) -> None:
    if type(record) is not dict:
        raise HydraReviewError("evidence must be one exact JSON object")
    unsigned = dict(record)
    if unsigned.pop(field, None) != digest(unsigned):
        raise HydraReviewError(f"evidence digest differs: {field}")


def cold_selection(cold_plan: dict[str, object], scope: str) -> dict[str, object]:
    if scope not in {"none", "hotspots", "full"}:
        raise HydraReviewError("v28 cold scope must be none, hotspots, or full")
    by_name = {row["name"]: row["enrollment_index"] for row in cold_plan["targets"]}
    if scope == "hotspots" and not all(name in by_name for name in HOTSPOT_NAMES):
        raise HydraReviewError("a retained historical hotspot is absent from the exact v28 inventory")
    indices = ([] if scope == "none" else sorted(by_name[name] for name in HOTSPOT_NAMES)
               if scope == "hotspots" else list(range(cold_plan["target_count"])))
    batches = [[index] for index in indices] if scope != "full" else cold_plan["batches"]
    return {"scope": scope, "indices": indices, "batches": batches, "passes": 2,
            "selected_targets": len(indices), "reserved_batches": 2 * len(batches),
            "limits": COLD_LIMITS.to_dict(),
            "sampling": "two previously resource-limited named targets; not representative or a benchmark",
            "full_epoch_required_for_cold_gate": True, "automatic_retries": False}


def worker_reservations(mode: str, cases: tuple, selection: dict[str, object]) -> dict[str, object]:
    native = int(mode == "reference-only")
    builds = len(MODULES) + 1 if native else 0
    checks = (len(cases) + BATCH_SIZE - 1) // BATCH_SIZE if native else 0
    cold = selection["reserved_batches"] if mode == "native-hotspots" else 0
    return {"native_fixture_workers": native, "lean_build_workers": builds,
            "lean_fixture_workers": checks, "cold_workers": cold,
            "workers": native + builds + checks + cold,
            "sum_worker_wall_seconds": native * 30 + builds * 120 + checks * 45 + cold * 45,
            "sum_worker_cpu_seconds": native * 20 + builds * 90 + checks * 30 + cold * 30,
            "max_worker_rss_bytes": 1024**3, "max_stream_bytes": 1024**2,
            "parallel_workers": 1, "gpu_workers": 0, "automatic_retries": False}


def _whole_guard(mode: str) -> dict[str, object]:
    # These are proposed enclosing supervision requirements, never a receipt
    # that the controller or a human has supplied an external process guard.
    return {"required_for_execution": True, "implemented_by_this_controller": False,
            "suggested_wall_seconds": 2400 if mode == "reference-only" else 900,
            "suggested_aggregate_cpu_seconds": 1800 if mode == "reference-only" else 180,
            "suggested_group_rss_bytes": 2 * 1024**3,
            "suggested_aggregate_output_bytes": 64 * 1024**2,
            "measurement_is_not_authorization": True}


def _reference_v28(identity: dict[str, object]) -> None:
    validate_reference_identity(identity)
    if (identity["project_toolchain_pin"] != "leanprover/lean4:v4.31.0"
        or identity["matches_project_toolchain_pin"] is not True
        or not re.fullmatch(r"Lean \(version 4\.31\.0(?:,[^\r\n]*)?\)", identity["compiler_version"])):
        raise HydraReviewError("v28 reference requires the actual pinned Lean 4.31.0 compiler")


def build_review_plan(
    *, mode: str = "native-hotspots", reference_project: Path | None = None,
    lean_binary: Path | None = None, cold_batch_size: int = 1, cold_wall_budget: int = 900,
) -> dict[str, object]:
    if mode not in MODES:
        raise HydraReviewError("unknown v28 review mode")
    if type(cold_wall_budget) is not int or not 30 <= cold_wall_budget <= 3600:
        raise HydraReviewError("whole cold-stage wall budget must lie in [30,3600] seconds")
    if mode == "reference-only":
        if not isinstance(reference_project, Path) or not isinstance(lean_binary, Path):
            raise HydraReviewError("reference-only planning requires an explicit companion and Lean binary")
        reference = inspect_reference(reference_project, lean_binary)
        _reference_v28(reference)
        project = str(reference_project.resolve(strict=True))
    else:
        if reference_project is not None or lean_binary is not None:
            raise HydraReviewError("native/planning mode does not accept or inspect a Lean environment")
        reference, project = None, None
    epoch = freeze_epoch()
    cases = build_conformance_cases()
    if len(cases) != 1321:
        raise HydraReviewError("v28 calibration must not silently expand the original 1321 fixtures")
    cold = build_cold_replay_plan(epoch, batch_size=cold_batch_size,
                                 selected_names=HOTSPOT_NAMES if mode == "native-hotspots" else ())
    scope = {"reference-only": "none", "native-hotspots": "hotspots", "full-plan-only": "full"}[mode]
    selection = cold_selection(cold, scope)
    reservations = worker_reservations(mode, cases, selection)
    plan = {"schema": SCHEMA, "status": "planned", "mode": mode,
            "source": source_identity(), "execution_root": str(ROOT), "profile": development_profile(),
            "epoch_sha256": epoch.epoch_sha256, "reference": reference, "reference_project": project,
            "conformance": conformance_manifest(cases, epoch_sha256=epoch.epoch_sha256),
            "cold_plan": cold, "cold_selection": selection, "cold_wall_budget": cold_wall_budget,
            "parallel_workers": 1, "native_limits": NATIVE_LIMITS.to_dict(),
            "reserved_reference_processes": reservations["lean_build_workers"] + reservations["lean_fixture_workers"],
            "worker_reservations": reservations, "whole_controller_guard": _whole_guard(mode),
            "ancillary_inputs": ancillary_input_closure(mode),
            "model_calls": 0, "solver_calls": 0, "data_written": False,
            **{key: False for key in FALSE_CLAIMS}}
    plan["plan_sha256"] = digest(plan)
    if len(canonical(plan)) > MAX_BYTES:
        raise HydraReviewError("v28 review plan exceeds its unchanged 64-MiB artifact cap")
    return plan


def validate_plan(plan: dict[str, object], *, live_sources: bool = True) -> None:
    if type(plan) is not dict or set(plan) != PLAN_FIELDS:
        raise HydraReviewError("v28 plan has missing or unknown fields")
    _signed(plan, "plan_sha256")
    if len(canonical(plan)) > MAX_BYTES:
        raise HydraReviewError("v28 plan exceeds its artifact bound")
    mode = plan["mode"]
    if (mode not in MODES or plan["schema"] != SCHEMA or plan["status"] != "planned"
        or plan["epoch_sha256"] != ALPHA_V28_EPOCH
        or type(plan["parallel_workers"]) is not int or plan["parallel_workers"] != 1
        or not _same(plan["native_limits"], NATIVE_LIMITS.to_dict())
        or any(plan[key] is not False for key in ("data_written", *FALSE_CLAIMS))
        or type(plan["model_calls"]) is not int or plan["model_calls"] != 0
        or type(plan["solver_calls"]) is not int or plan["solver_calls"] != 0
        or type(plan["cold_wall_budget"]) is not int or not 30 <= plan["cold_wall_budget"] <= 3600):
        raise HydraReviewError("v28 plan changed its epoch, claims, or resource boundary")
    _execution_root(plan["execution_root"])
    validate_ancillary_inputs(plan["ancillary_inputs"], mode=mode)
    if live_sources:
        validate_sources(plan["source"])
    if mode == "reference-only":
        _reference_v28(plan["reference"])
        _execution_root(plan["reference_project"])
        if live_sources:
            validate_reference_provenance(Path(plan["reference_project"]), plan["reference"])
    elif plan["reference"] is not None or plan["reference_project"] is not None:
        raise HydraReviewError("native/planning mode cannot borrow reference readiness")
    epoch = freeze_epoch()
    cases = build_conformance_cases()
    cold = build_cold_replay_plan(epoch, batch_size=plan["cold_plan"]["batch_size"],
                                 selected_names=HOTSPOT_NAMES if mode == "native-hotspots" else ())
    scope = {"reference-only": "none", "native-hotspots": "hotspots", "full-plan-only": "full"}[mode]
    selection = cold_selection(cold, scope)
    reservations = worker_reservations(mode, cases, selection)
    if (len(cases) != 1321 or not _same(plan["profile"], development_profile())
        or not _same(plan["cold_plan"], cold) or not _same(plan["cold_selection"], selection)
        or not _same(plan["conformance"], conformance_manifest(cases, epoch_sha256=epoch.epoch_sha256))
        or not _same(plan["worker_reservations"], reservations)
        or not _same(plan["whole_controller_guard"], _whole_guard(mode))
        or type(plan["reserved_reference_processes"]) is not int
        or plan["reserved_reference_processes"] != reservations["lean_build_workers"] + reservations["lean_fixture_workers"]):
        raise HydraReviewError("v28 plan changed its complete original inventory, fixtures, selection or reservations")


def write_once(path: Path, data: bytes) -> dict[str, object]:
    if len(data) > MAX_BYTES:
        raise HydraReviewError("retained review artifact exceeds its byte reservation")
    import os
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return {"path": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _case_archive(cases: tuple) -> bytes:
    return b"".join(canonical({"case_id": case.case_id, "artifact_base64": base64.b64encode(case.artifact).decode("ascii")}) + b"\n" for case in cases)


def worker(request: dict[str, object]) -> None:
    common = {"schema", "mode", "source", "epoch_sha256", "profile_sha256", "ancillary_inputs"}
    extra = {"case_manifest_sha256"} if request.get("mode") == "native" else {
        "targets", "pass_number", "batch_number", "edition_identity_sha256", "certificate_limits"}
    if (set(request) != common | extra or request["schema"] != SCHEMA
        or request["mode"] not in {"native", "cold"}):
        raise HydraReviewError("internal review worker request differs")
    # The controller authenticates the complete historical Git inventory
    # before and after the run. Workers recheck exact bytes without spawning
    # Git subprocesses under their no-descendant resource contract.
    check_recorded_source_bytes(request["source"])
    if (request["epoch_sha256"] != ALPHA_V28_EPOCH
        or request["profile_sha256"] != development_profile()["profile_sha256"]):
        raise HydraReviewError("review worker profile changed")
    input_mode = "native-hotspots" if request["mode"] == "cold" else "reference-only"
    inputs_before = check_ancillary_inputs(request["ancillary_inputs"], mode=input_mode, root=ROOT)
    if request["mode"] == "native":
        cases = build_conformance_cases()
        manifest = conformance_manifest(cases, epoch_sha256=request["epoch_sha256"])
        if manifest["manifest_sha256"] != request["case_manifest_sha256"]:
            raise HydraReviewError("native worker fixture manifest differs")
        sys.stdout.buffer.write(canonical(check_native_cases(cases)) + b"\n")
        sys.stdout.buffer.flush()
        return
    if (type(request["targets"]) is not list or not 1 <= len(request["targets"]) <= 16
        or any(type(target) is not dict or target.get("name") not in HOTSPOT_NAMES
               for target in request["targets"])
        or type(request["pass_number"]) is not int or request["pass_number"] not in (1, 2)
        or type(request["batch_number"]) is not int or request["batch_number"] < 0):
        raise HydraReviewError("cold worker batch/pass reservation differs")
    for target in request["targets"]:
        try:
            receipt = replay_cold_target(target, epoch_sha256=request["epoch_sha256"],
                                         edition_identity_sha256=request["edition_identity_sha256"],
                                         limits=CertificateLimits(**request["certificate_limits"]))
        except Exception as error:
            receipt = {"status": "unknown", "kernel_checked": False,
                       "name": target["name"], "enrollment_index": target["enrollment_index"],
                       "target_sha256": target["target_sha256"], "error_type": type(error).__name__,
                       "error": " ".join(str(error).split())[:2000]}
        if check_ancillary_inputs(request["ancillary_inputs"], mode=input_mode, root=ROOT) != inputs_before:
            raise HydraReviewError("ancillary proof inputs changed during the native worker")
        record = {"pass_number": request["pass_number"], "batch_number": request["batch_number"],
                  "receipt": receipt}
        sys.stdout.buffer.write(canonical(record) + b"\n")
        sys.stdout.buffer.flush()


def _request(plan: dict[str, object], mode: str, **extra) -> dict[str, object]:
    return {"schema": SCHEMA, "mode": mode, "source": plan["source"],
            "epoch_sha256": plan["epoch_sha256"], "profile_sha256": plan["profile"]["profile_sha256"],
            "ancillary_inputs": plan["ancillary_inputs"], **extra}


def _cold_request(plan: dict[str, object], pass_number: int, batch_number: int, indices: list[int]) -> dict[str, object]:
    cold = plan["cold_plan"]
    return _request(plan, "cold", targets=[cold["selected_targets"][str(index)] for index in indices],
                    pass_number=pass_number, batch_number=batch_number,
                    edition_identity_sha256=cold["edition_identity_sha256"],
                    certificate_limits=cold["certificate_limits"])


def _sha(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def validate_cold_receipt(plan: dict[str, object], target: dict[str, object], receipt: dict[str, object]) -> None:
    """Bind every positive or unknown to one originally assigned exact target."""
    if type(receipt) is not dict:
        raise HydraReviewError("cold receipt must be one object")
    for key in ("name", "enrollment_index", "target_sha256"):
        if key not in receipt or not _same(receipt[key], target[key]):
            raise HydraReviewError("cold worker output changed the original target")
    if receipt.get("kernel_checked") is False:
        if (set(receipt) != {"status", "kernel_checked", "name", "enrollment_index", "target_sha256", "error_type", "error"}
            or receipt["status"] != "unknown" or type(receipt["error_type"]) is not str
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", receipt["error_type"]) is None
            or type(receipt["error"]) is not str or len(receipt["error"]) > 2000
            or " ".join(receipt["error"].split()) != receipt["error"]):
            raise HydraReviewError("unknown cold result changed its bounded diagnostic contract")
        return
    fields = {
        "schema", "status", "kernel_checked", "epoch_sha256", "edition_identity_sha256",
        "target_sha256", "name", "enrollment_index", "membership", "statement_sha256",
        "script_sha256", "dependencies_sha256", "original_formula_sha256", "certificate",
        "certificate_limits", "kernel_mode", "empty_context", "independent_recheck_calls",
        "runtime_internal_kernel_calls", "all_scripts_regenerated", "lean_companion_invoked",
        "model_calls", "solver_calls", "research_claim_eligible", "receipt_sha256",
    }
    if set(receipt) != fields:
        raise HydraReviewError("cold proof receipt has missing or unknown fields")
    _signed(receipt, "receipt_sha256")
    expected = {
        "schema": COLD_REPLAY_SCHEMA, "status": "checked", "kernel_checked": True,
        "epoch_sha256": plan["epoch_sha256"],
        "edition_identity_sha256": plan["cold_plan"]["edition_identity_sha256"],
        "certificate_limits": plan["cold_plan"]["certificate_limits"], "kernel_mode": "intuitionistic",
        "empty_context": True, "independent_recheck_calls": 1, "runtime_internal_kernel_calls": None,
        "all_scripts_regenerated": False, "lean_companion_invoked": False,
        "model_calls": 0, "solver_calls": 0, "research_claim_eligible": False,
    }
    expected.update({key: target[key] for key in ("membership", "statement_sha256", "script_sha256", "dependencies_sha256")})
    if not _same({key: receipt[key] for key in expected}, expected) or not _sha(receipt["original_formula_sha256"]):
        raise HydraReviewError("cold proof receipt changed its original theorem or checking authority")
    certificate = receipt["certificate"]
    if (type(certificate) is not dict or set(certificate) != {
        "schema", "sha256", "proof_nodes", "proof_depth", "annotation_nodes", "envelope_depth",
        "proof_objects", "proof_edges", "syntax_objects", "sharing_independent_digest", "dne_objects",
    } or certificate["schema"] != CERTIFICATE_SCHEMA or not _sha(certificate["sha256"])
        or certificate["sharing_independent_digest"] is not True
        or type(certificate["dne_objects"]) is not int or certificate["dne_objects"] != 0):
        raise HydraReviewError("cold certificate identity or constructive boundary differs")
    limits = plan["cold_plan"]["certificate_limits"]
    for key in ("proof_nodes", "proof_depth", "annotation_nodes", "envelope_depth", "proof_objects", "syntax_objects"):
        if type(certificate[key]) is not int or not (0 if key == "annotation_nodes" else 1) <= certificate[key] <= limits["max_" + key]:
            raise HydraReviewError("cold certificate exceeds a structural reservation")
    if (type(certificate["proof_edges"]) is not int
        or not certificate["proof_objects"] - 1 <= certificate["proof_edges"] <= 3 * certificate["proof_objects"]
        or not certificate["proof_objects"] <= certificate["syntax_objects"] <= certificate["proof_objects"] + certificate["annotation_nodes"]
        or certificate["proof_objects"] > certificate["proof_nodes"]
        or certificate["proof_depth"] > certificate["proof_nodes"]
        or certificate["proof_depth"] > certificate["envelope_depth"]):
        raise HydraReviewError("cold certificate structural/object diagnostics contradict each other")


def _decode_cold_worker(plan: dict[str, object], pass_number: int, batch_number: int,
                        indices: list[int], result: dict[str, object], *, execution_root: str) -> list[dict[str, object]]:
    request = _cold_request(plan, pass_number, batch_number, indices)
    validate_process_record(result, command=_worker_command(execution_root),
                            limits=COLD_LIMITS, input_bytes=canonical(request))
    successful = result["reason"] == "exited" and result["returncode"] == 0
    # Only LF-framed, complete records survive a killed or truncated worker.
    # str.splitlines would also accept Unicode separators not used by the protocol.
    lines = result["stdout"].split("\n")
    complete, tail = lines[:-1], lines[-1]
    targets = request["targets"]
    if len(complete) > len(targets) or (successful and (tail or len(complete) != len(targets))):
        raise HydraReviewError("cold worker returned extra, duplicate, or missing targets")
    rows = []
    for target, line in zip(targets, complete):
        item = decode(line.encode("utf-8"), limit=1024**2)
        if (set(item) != {"pass_number", "batch_number", "receipt"}
            or type(item["pass_number"]) is not int or item["pass_number"] != pass_number
            or type(item["batch_number"]) is not int or item["batch_number"] != batch_number):
            raise HydraReviewError("cold worker output changed its assigned batch")
        validate_cold_receipt(plan, target, item["receipt"])
        rows.append(item)
    return rows


def _cold_schedule(plan: dict[str, object]) -> list[tuple[int, int, list[int]]]:
    return [(number, index, indices) for number in (1, 2)
            for index, indices in enumerate(plan["cold_selection"]["batches"])]


def run_cold(plan: dict[str, object], *, progress=None, archive: Path | None = None) -> dict[str, object]:
    if plan["mode"] != "native-hotspots" or plan["cold_selection"]["scope"] != "hotspots":
        raise HydraReviewError("full cold execution has no reviewed measured envelope")
    started = time.monotonic()
    deadline = started + plan["cold_wall_budget"]
    inputs_before = check_ancillary_inputs(plan["ancillary_inputs"], mode=plan["mode"], root=ROOT)
    rows, batches = [], []
    schedule = _cold_schedule(plan)
    for pass_number, batch_number, indices in schedule:
        if check_ancillary_inputs(plan["ancillary_inputs"], mode=plan["mode"], root=ROOT) != inputs_before:
            raise HydraReviewError("ancillary proof inputs changed before a native worker")
        request_bytes = canonical(_cold_request(plan, pass_number, batch_number, indices))
        launched = time.monotonic()
        if deadline - launched < COLD_LIMITS.wall_seconds:
            break
        result = run_bounded(_worker_command(str(ROOT)), cwd=ROOT,
                              limits=COLD_LIMITS, input_bytes=request_bytes)
        if archive is not None:
            write_once(archive / f"cold-worker-pass-{pass_number}-batch-{batch_number}.json",
                       canonical(result) + b"\n")
        if check_ancillary_inputs(plan["ancillary_inputs"], mode=plan["mode"], root=ROOT) != inputs_before:
            raise HydraReviewError("ancillary proof inputs changed during a native worker")
        completed = _decode_cold_worker(plan, pass_number, batch_number, indices, result, execution_root=str(ROOT))
        rows.extend(completed)
        batches.append({"pass_number": pass_number, "batch_number": batch_number,
                        "indices": indices, "started_wall_seconds": launched - started,
                        "worker": result, "completed_targets": len(completed)})
        if progress:
            progress("cold_replay", len(batches), len(schedule),
                     f"pass {pass_number}, {len(completed)}/{len(indices)} receipts, {result['reason']}")
    if check_ancillary_inputs(plan["ancillary_inputs"], mode=plan["mode"], root=ROOT) != inputs_before:
        raise HydraReviewError("ancillary proof inputs changed during cold calibration")
    elapsed = time.monotonic() - started
    ledger = {"schema": COLD_LEDGER_SCHEMA, "execution_root": str(ROOT), "batches": batches, "rows": rows,
              "wall_seconds": elapsed, "wall_budget": plan["cold_wall_budget"],
              "stop_reason": "completed" if len(batches) == len(schedule) else "wall-budget-insufficient-for-next-worker",
              "summary": summarize_cold(plan, rows, batches, wall_seconds=elapsed)}
    validate_cold_ledger(plan, ledger, execution_root=str(ROOT))
    return ledger


def _cold_positive_projection(receipt: dict[str, object]) -> dict[str, object]:
    # Heap aliasing can differ across fresh interpreters; the actual proof's
    # structural Merkle digest, occurrence counts, and all authority fields may not.
    result = {key: value for key, value in receipt.items() if key not in {"receipt_sha256", "certificate"}}
    result["certificate"] = {key: value for key, value in receipt["certificate"].items()
                             if key not in {"proof_objects", "proof_edges", "syntax_objects"}}
    return result


def summarize_cold(plan: dict[str, object], rows: list[dict], batches: list[dict], *, wall_seconds: float) -> dict[str, object]:
    selection = plan["cold_selection"]
    passes = []
    for number in (1, 2):
        selected = [row["receipt"] for row in rows if row["pass_number"] == number]
        checked = [row for row in selected if row["kernel_checked"]]
        projection = [_cold_positive_projection(row) for row in checked]
        complete = [row["enrollment_index"] for row in checked] == selection["indices"]
        passes.append({"pass": number, "checked": len(checked), "unknown": len(selected) - len(checked),
                       "not_completed": selection["selected_targets"] - len(selected),
                       "ordered_root_sha256": digest(projection) if complete and checked else None,
                       "partial_root_sha256": digest(projection), "all_selected_checked": complete and bool(checked)})
    failures = sum(batch["worker"]["reason"] != "exited" or batch["worker"]["returncode"] != 0 for batch in batches)
    matching = all(item["all_selected_checked"] for item in passes) and passes[0]["ordered_root_sha256"] == passes[1]["ordered_root_sha256"]
    return {"scope": selection["scope"], "selected_targets": selection["selected_targets"],
            "full_epoch_targets": plan["cold_plan"]["target_count"], "passes": passes,
            "matching_complete_selected_passes": matching, "worker_failures": failures,
            "batches_run": len(batches), "batches_reserved": selection["reserved_batches"],
            "whole_stage_within_budget": wall_seconds <= plan["cold_wall_budget"],
            "full_epoch_replayed_twice": False,
            "all_scripts_regenerated": False, "model_calls": 0, "solver_calls": 0}


def validate_cold_ledger(plan: dict[str, object], ledger: dict[str, object], *, execution_root: str | None = None) -> None:
    expected_root = _execution_root(plan["execution_root"] if execution_root is None else execution_root)
    if (type(ledger) is not dict or set(ledger) != {
        "schema", "execution_root", "batches", "rows", "summary", "wall_seconds", "wall_budget", "stop_reason",
    } or ledger["schema"] != COLD_LEDGER_SCHEMA or ledger["execution_root"] != expected_root
        or type(ledger["batches"]) is not list
        or type(ledger["rows"]) is not list or type(ledger["wall_budget"]) is not int
        or ledger["wall_budget"] != plan["cold_wall_budget"]
        or type(ledger["wall_seconds"]) not in {int, float}
        or not math.isfinite(ledger["wall_seconds"]) or ledger["wall_seconds"] < 0):
        raise HydraReviewError("cold ledger changed its exact schema or resource reservation")
    schedule = _cold_schedule(plan)
    if len(ledger["batches"]) > len(schedule):
        raise HydraReviewError("cold ledger exceeded its reserved batches")
    expected_stop = "completed" if len(ledger["batches"]) == len(schedule) else "wall-budget-insufficient-for-next-worker"
    if ledger["stop_reason"] != expected_stop:
        raise HydraReviewError("cold ledger changed its stop condition")
    if (len(ledger["batches"]) < len(schedule)
        and ledger["wall_seconds"] < max(0, plan["cold_wall_budget"] - COLD_LIMITS.wall_seconds)):
        raise HydraReviewError("cold ledger claims budget exhaustion before its next-worker reservation was exhausted")
    rows, identities, elapsed, previous_finish = [], set(), 0.0, 0.0
    for batch, (number, index, indices) in zip(ledger["batches"], schedule):
        if (type(batch) is not dict or set(batch) != {
            "pass_number", "batch_number", "indices", "worker", "completed_targets", "started_wall_seconds",
        }
            or not _same({key: batch[key] for key in ("pass_number", "batch_number", "indices")},
                         {"pass_number": number, "batch_number": index, "indices": indices})):
            raise HydraReviewError("cold batches must be an exact ordered prefix of the two reserved passes")
        launched = batch["started_wall_seconds"]
        if (type(launched) not in {int, float} or not math.isfinite(launched) or launched < 0
            or launched + 1e-6 < previous_finish
            or launched + COLD_LIMITS.wall_seconds > plan["cold_wall_budget"]):
            raise HydraReviewError("cold workers overlap or started without their whole-stage reservation")
        completed = _decode_cold_worker(plan, number, index, indices, batch["worker"], execution_root=expected_root)
        if type(batch["completed_targets"]) is not int or batch["completed_targets"] != len(completed):
            raise HydraReviewError("cold batch count differs from its exact worker rows")
        for row in completed:
            key = (number, row["receipt"]["enrollment_index"])
            if key in identities:
                raise HydraReviewError("cold ledger duplicates a pass/target identity")
            identities.add(key)
        rows.extend(completed)
        elapsed += batch["worker"]["resources"]["wall_seconds"]
        previous_finish = launched + batch["worker"]["resources"]["wall_seconds"]
    if ledger["wall_seconds"] + 1e-6 < max(elapsed, previous_finish):
        raise HydraReviewError("cold stage duration is shorter than its sequential workers")
    if not _same(rows, ledger["rows"]):
        raise HydraReviewError("cold ledger rows differ from their exact ordered worker outputs")
    summary = summarize_cold(plan, rows, ledger["batches"], wall_seconds=ledger["wall_seconds"])
    if not _same(ledger["summary"], summary):
        raise HydraReviewError("cold summary differs from its validated complete/partial ledger")


def compare_cold_reproduction(plan: dict[str, object], old: dict[str, object], fresh: dict[str, object]) -> int:
    validate_cold_ledger(plan, old)
    validate_cold_ledger(plan, fresh, execution_root=str(ROOT))
    # Uniqueness and exact assignment have already been checked; only now is a
    # lookup safe. Every retained positive must reproduce. Unknowns need not.
    checked_before = {(row["pass_number"], row["receipt"]["name"]): row["receipt"]
                      for row in old["rows"] if row["receipt"]["kernel_checked"]}
    checked_now = {(row["pass_number"], row["receipt"]["name"]): row["receipt"]
                   for row in fresh["rows"] if row["receipt"]["kernel_checked"]}
    for key, receipt in checked_before.items():
        other = checked_now.get(key)
        if other is None or not _same(_cold_positive_projection(receipt), _cold_positive_projection(other)):
            raise HydraReviewError("independent cold replay failed to reproduce a retained positive")
    return len(checked_before)


def _evidence_names(plan):
    return ({"native", "native_worker", "reference_build", "reference_results"}
            if plan["mode"] == "reference-only" else {"cold"})


def _execute_checks(plan: dict[str, object], directory: Path, *, reference_source: Path | None,
                    progress=None) -> dict[str, object]:
    if plan["mode"] == "native-hotspots":
        return {"cold": run_cold(plan, progress=progress, archive=directory)}
    if plan["mode"] != "reference-only":
        raise HydraReviewError("full cold execution is unbudgeted and unavailable")
    cases = build_conformance_cases()
    native_worker = run_bounded(_worker_command(str(ROOT)), cwd=ROOT, limits=NATIVE_LIMITS,
                               input_bytes=canonical(_request(plan, "native",
                               case_manifest_sha256=plan["conformance"]["manifest_sha256"])))
    write_once(directory / "native-worker-observed.json", canonical(native_worker) + b"\n")
    if native_worker["reason"] != "exited" or native_worker["returncode"] != 0:
        raise HydraReviewError("native fixture worker did not complete within its unchanged reservation")
    native = decode(native_worker["stdout"].encode(), limit=8 * 1024**2)
    validate_native_evidence(plan, native, native_worker, cases, execution_root=str(ROOT))
    reference_dir = directory / "reference-build"
    stage_reference(reference_source, reference_dir, plan["reference"])
    build = build_reference(reference_dir, plan["reference"], progress=progress)
    write_once(directory / "reference-build-observed.json", canonical(build) + b"\n")
    reference = check_reference_cases(reference_dir, plan["reference"], build, cases, progress=progress)
    write_once(directory / "reference-results-observed.json", canonical(reference) + b"\n")
    if reference["status"] != "passed":
        raise HydraReviewError("independent Lean disagreed with exact fixture expectations")
    return {"native": native, "native_worker": native_worker, "reference_build": build,
            "reference_results": reference}


def validate_native_evidence(plan: dict[str, object], native: dict[str, object], result: dict[str, object], cases: tuple,
                             *, execution_root: str | None = None) -> None:
    request = _request(plan, "native", case_manifest_sha256=plan["conformance"]["manifest_sha256"])
    expected_root = plan["execution_root"] if execution_root is None else execution_root
    validate_process_record(result, command=_worker_command(expected_root),
                            limits=NATIVE_LIMITS, input_bytes=canonical(request), success_codes=(0,))
    _signed(native, "report_sha256")
    if (result["stderr"] or not _same(decode(result["stdout"].encode(), limit=8 * 1024**2), native)
        or not _same(native, check_native_cases(cases)) or native["all_expected_results"] is not True):
        raise HydraReviewError("native evidence differs from its exact worker bytes and freshly decoded fixtures")


def review_summary(plan: dict[str, object], results: dict[str, object]) -> dict[str, object]:
    result = {"mode": plan["mode"], "epoch_sha256": ALPHA_V28_EPOCH,
              "full_epoch_targets": plan["cold_plan"]["target_count"],
              "outside_replay_profile_count": len(plan["cold_plan"]["outside_replay_profile"]),
              "reference_compiler_matches_pin": False, "reference_cases_matched": 0,
              "full_epoch_replayed_twice": False, "lineage_review_performed": False,
              "independent_human_review_granted": False, "cold": None}
    if plan["mode"] == "reference-only":
        result.update(reference_compiler_matches_pin=True,
                      reference_cases_matched=results["reference_results"]["case_count"],
                      positive_formulas=plan["conformance"]["distinct_positive_formula_count"],
                      native_positive_accepts=results["native"]["positive_certificates_accepted"],
                      native_mutations_rejected=results["native"]["certificate_mutations_rejected"])
    else:
        result["cold"] = results["cold"]["summary"]
    return result


def validate_report_header(report: dict[str, object]) -> None:
    if type(report) is not dict or set(report) != REPORT_FIELDS:
        raise HydraReviewError("review report has missing or unknown fields")
    _signed(report, "report_sha256")
    if (report["schema"] != SCHEMA or report["status"] != "completed-with-open-gates"
        or type(report["model_calls"]) is not int or report["model_calls"] != 0
        or type(report["solver_calls"]) is not int or report["solver_calls"] != 0
        or any(report[key] is not False for key in ("model_training_authorized", "independent_human_review_granted",
                                                   "h0_complete", "h1_complete", "sealed_benchmark", "research_claim_eligible"))):
        raise HydraReviewError("review report promoted incomplete research gates")
    dates = []
    for field in ("started_at", "finished_at"):
        value = report[field]
        if type(value) is not str or len(value) > 64:
            raise HydraReviewError("review timestamps must be explicit UTC observations")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as error:
            raise HydraReviewError("review timestamp is malformed") from error
        if parsed.tzinfo != timezone.utc:
            raise HydraReviewError("review timestamps must include UTC timezone")
        dates.append(parsed)
    if dates[1] < dates[0]:
        raise HydraReviewError("review completion precedes its start")


def validate_saved_results(plan: dict[str, object], report: dict[str, object], results: dict[str, object]) -> None:
    if type(results) is not dict or set(results) != _evidence_names(plan):
        raise HydraReviewError("v28 review has an incomplete or borrowed evidence inventory")
    if plan["mode"] == "reference-only":
        cases = build_conformance_cases()
        validate_native_evidence(plan, results["native"], results["native_worker"], cases)
        validate_build_receipt(plan["reference"], results["reference_build"])
        validate_reference_results(plan["reference"], results["reference_results"], cases)
        if results["reference_results"]["status"] != "passed":
            raise HydraReviewError("saved reference conformance did not pass")
    elif plan["mode"] == "native-hotspots":
        validate_cold_ledger(plan, results["cold"])
    else:
        raise HydraReviewError("a full planning inventory cannot become executed evidence")
    if not _same(report["summary"], review_summary(plan, results)):
        raise HydraReviewError("review summary differs from its actual original evidence")


def _fresh_directory(directory: Path) -> Path:
    # Refuse symlink traversal and overwrite. Parent directory must pre-exist;
    # no implicit recursive creation can redirect retained evidence elsewhere.
    if not directory.is_absolute():
        directory = Path.cwd() / directory
    if directory.exists() or directory.is_symlink():
        raise HydraReviewError("review requires a fresh output directory")
    if directory.parent.resolve(strict=True) != directory.parent:
        raise HydraReviewError("review output ancestors must be canonical real directories")
    directory.mkdir(mode=0o700)
    return directory


def execute_review(plan: dict[str, object], directory: Path, *, progress=None) -> dict[str, object]:
    """Run only the pinned calibration under additional external group supervision.

    Worker CPU/wall/RSS/output limits are enforced here. The enclosing controller
    guard recorded in the plan must be supplied by the invoking local runner;
    this function never writes a receipt claiming such supervision happened.
    """
    if plan.get("mode") == "full-plan-only":
        raise HydraReviewError("full cold execution has no measured/reviewed resource envelope")
    validate_plan(plan)
    if (plan["source"] != source_identity() or plan["source"]["git_dirty"] is not False
        or plan["execution_root"] != str(ROOT)):
        raise HydraReviewError("execution requires its exact clean committed v28 source plan")
    inputs_before = check_ancillary_inputs(plan["ancillary_inputs"], mode=plan["mode"], root=ROOT)
    directory = _fresh_directory(directory)
    plan_file = write_once(directory / "plan.json", canonical(plan) + b"\n")
    case_file = write_once(directory / "cases.jsonl", _case_archive(build_conformance_cases()))
    started = datetime.now(timezone.utc).isoformat()
    try:
        reference_source = None
        if plan["mode"] == "reference-only":
            reference_source = directory / "reference-source"
            stage_reference(Path(plan["reference_project"]), reference_source, plan["reference"])
        results = _execute_checks(plan, directory, reference_source=reference_source, progress=progress)
        if check_ancillary_inputs(plan["ancillary_inputs"], mode=plan["mode"], root=ROOT) != inputs_before:
            raise HydraReviewError("ancillary proof inputs changed during v28 review execution")
        validate_plan(plan)
        if plan["source"] != source_identity():
            raise HydraReviewError("source changed during v28 review execution")
        evidence = {name: write_once(directory / f"{name}.json", canonical(value) + b"\n")
                    for name, value in results.items()}
        report = {"schema": SCHEMA, "status": "completed-with-open-gates", "started_at": started,
                  "finished_at": datetime.now(timezone.utc).isoformat(), "plan": plan_file, "cases": case_file,
                  "plan_sha256": plan["plan_sha256"], "evidence": evidence,
                  "summary": review_summary(plan, results), "model_calls": 0, "solver_calls": 0,
                  **{key: False for key in FALSE_CLAIMS}}
        report["report_sha256"] = digest(report)
        validate_report_header(report)
        validate_saved_results(plan, report, results)
        write_once(directory / "report.json", canonical(report) + b"\n")
        return report
    except BaseException as error:
        # Preserve the fresh directory and all partial artifacts. No cleanup,
        # retry, enlarged limit, or completed evidence on a failing path.
        failure = {"schema": SCHEMA, "status": "failed-with-open-gates", "plan_sha256": plan["plan_sha256"],
                   "error_type": type(error).__name__, "error": str(error)[:4000],
                   "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
                   **{key: False for key in FALSE_CLAIMS}}
        write_once(directory / "failure.json", canonical(failure) + b"\n")
        raise


def load_saved_review(directory: Path, *, report_sha256: str):
    """Validate a raw externally pinned archive without replaying or relabeling it."""
    directory = directory.resolve(strict=True)
    raw = read_bytes(directory / "report.json", limit=MAX_BYTES)
    if not _sha(report_sha256) or hashlib.sha256(raw).hexdigest() != report_sha256:
        raise HydraReviewError("saved review differs from its external raw report pin")
    report = decode(raw, limit=MAX_BYTES)
    validate_report_header(report)
    def checked(descriptor, name):
        if (type(descriptor) is not dict or set(descriptor) != {"path", "bytes", "sha256"}
            or descriptor["path"] != name or type(descriptor["bytes"]) is not int
            or not 0 <= descriptor["bytes"] <= MAX_BYTES or not _sha(descriptor["sha256"])):
            raise HydraReviewError("review artifact descriptor differs from its exact file")
        body = read_bytes(directory / name, limit=MAX_BYTES)
        if len(body) != descriptor["bytes"] or hashlib.sha256(body).hexdigest() != descriptor["sha256"]:
            raise HydraReviewError("saved review artifact bytes changed")
        return body
    plan = decode(checked(report["plan"], "plan.json"), limit=MAX_BYTES)
    if report["plan_sha256"] != plan["plan_sha256"]:
        raise HydraReviewError("review report changed its plan identity")
    validate_plan(plan)
    if checked(report["cases"], "cases.jsonl") != _case_archive(build_conformance_cases()):
        raise HydraReviewError("original conformance fixtures changed")
    if type(report["evidence"]) is not dict or set(report["evidence"]) != _evidence_names(plan):
        raise HydraReviewError("review evidence inventory is incomplete")
    results = {name: decode(checked(value, f"{name}.json"), limit=MAX_BYTES)
               for name, value in report["evidence"].items()}
    validate_saved_results(plan, report, results)
    return plan, report, results


def verify_review(directory: Path, fresh_directory: Path, *, report_sha256: str, progress=None):
    """Independently repeat one calibration, retaining every fresh artifact.

    This is agent-executed reproduction, never independent human review or a
    complete H0/H1 gate. No original artifact is changed or copied as evidence.
    """
    plan, report, old = load_saved_review(directory, report_sha256=report_sha256)
    original = directory.resolve(strict=True)
    fresh_path = fresh_directory.absolute()
    if fresh_path == original or original in fresh_path.parents or fresh_path in original.parents:
        raise HydraReviewError("independent reproduction requires a disjoint fresh archive")
    fresh_report = execute_review(plan, fresh_directory, progress=progress)
    fresh_raw = read_bytes(fresh_directory / "report.json", limit=MAX_BYTES)
    _, _, fresh = load_saved_review(fresh_directory, report_sha256=hashlib.sha256(fresh_raw).hexdigest())
    reproduced = 0
    if plan["mode"] == "reference-only":
        if (not _same(old["native"], fresh["native"])
            or not _same(old["reference_results"]["cases"], fresh["reference_results"]["cases"])
            or not _same(old["reference_build"]["axiom_footprint"], fresh["reference_build"]["axiom_footprint"])
            or not _same(old["reference_build"]["compiled_files"], fresh["reference_build"]["compiled_files"])):
            raise HydraReviewError("independent reference/native reproduction differs")
    else:
        reproduced = compare_cold_reproduction(plan, old["cold"], fresh["cold"])
    result = {"schema": "peano-hydra-reference-cold-reproduction-v28-v1", "status": "passed",
              "original_report_file_sha256": report_sha256,
              "fresh_report_file_sha256": hashlib.sha256(fresh_raw).hexdigest(),
              "original_report_sha256": report["report_sha256"],
              "fresh_report_sha256": fresh_report["report_sha256"],
              "cold_positive_receipts_reproduced": reproduced,
              "fresh_reference_rebuilt": plan["mode"] == "reference-only",
              "full_epoch_replayed_twice": False, "model_calls": 0, "solver_calls": 0,
              **{key: False for key in FALSE_CLAIMS}}
    result["verification_sha256"] = digest(result)
    write_once(fresh_directory / "verification.json", canonical(result) + b"\n")
    return result
