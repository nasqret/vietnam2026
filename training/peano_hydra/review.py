"""Executable, fail-closed evidence for Hydra's next human review gate.

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
import tempfile
import time

from .cold_replay import (
    CERTIFICATE_SCHEMA, COLD_REPLAY_SCHEMA, CertificateLimits,
    build_cold_replay_plan, replay_cold_target,
)
from .conformance import build_conformance_cases, check_native_cases, conformance_manifest
from .epoch import freeze_epoch
from .frontier import _pairs, canonical, decode, digest, read_bytes
from .lineage_review import build_lineage_review
from .protocol import development_profile
from .reference import (
    BATCH_SIZE, MODULES, build_reference,
    check_reference_cases, inspect_reference, stage_reference,
    validate_build_receipt, validate_reference_identity, validate_reference_provenance,
    validate_reference_results,
)
from .review_runtime import ProcessLimits, run_bounded, validate_process_record
from .review_sources import check_recorded_source_bytes, source_identity, validate_sources


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_peano_hydra_review.py"
SCHEMA = "peano-hydra-reference-lineage-review-v1"
MAX_BYTES = 64 * 1024**2
DEFAULT_DEVELOPMENT = Path("artifacts/peano-hydra/development-2026-08-27")
COLD_LIMITS = ProcessLimits(wall_seconds=45, cpu_seconds=30)
NATIVE_LIMITS = ProcessLimits(wall_seconds=30, cpu_seconds=20)
COLD_LEDGER_SCHEMA = "peano-hydra-cold-review-ledger-v1"
EVIDENCE_NAMES = {"native", "native_worker", "reference_build", "reference_results", "cold"}
PLAN_FIELDS = {
    "schema", "status", "source", "profile", "epoch_sha256", "development_directory",
    "development_plan_sha256", "preparation_directories", "allocation_input", "lineage_review",
    "reference", "reference_project", "conformance", "cold_plan", "cold_selection",
    "cold_wall_budget", "parallel_workers", "native_limits", "reserved_reference_processes",
    "model_calls", "solver_calls", "data_written", "model_training_authorized",
    "independent_human_review_granted", "h0_complete", "h1_complete", "sealed_benchmark",
    "research_claim_eligible", "plan_sha256",
}
REPORT_FIELDS = {
    "schema", "status", "started_at", "finished_at", "plan", "cases", "plan_sha256",
    "evidence", "summary", "model_calls", "solver_calls", "model_training_authorized",
    "independent_human_review_granted", "h0_complete", "h1_complete", "sealed_benchmark",
    "research_claim_eligible", "report_sha256",
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


def read_allocations(path: Path) -> list[dict[str, str]]:
    def invalid(value: str) -> None:
        raise HydraReviewError(f"non-finite allocation value: {value}")
    try:
        value = json.loads(read_bytes(path, limit=1024**2), object_pairs_hook=_pairs,
                           parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise HydraReviewError(f"invalid standalone allocation JSON: {error}") from None
    if type(value) is not list:
        raise HydraReviewError("allocations must be one standalone JSON array")
    return value


def _signed(record: dict[str, object], field: str) -> None:
    if type(record) is not dict:
        raise HydraReviewError("evidence must be one exact JSON object")
    unsigned = dict(record)
    if unsigned.pop(field, None) != digest(unsigned):
        raise HydraReviewError(f"evidence digest differs: {field}")


def _development(directory: Path) -> dict[str, object]:
    directory = ROOT / _relative(directory)
    report = read_record(directory / "report.json")
    plan_bytes = read_bytes(directory / "plan.json", limit=MAX_BYTES)
    plan = decode(plan_bytes, limit=MAX_BYTES)
    _signed(report, "report_sha256")
    _signed(plan, "plan_sha256")
    if (report["status"] != "completed" or report["plan_sha256"] != plan["plan_sha256"]
        or report["plan"] != {"path": "plan.json", "bytes": len(plan_bytes), "sha256": hashlib.sha256(plan_bytes).hexdigest()}
        or report["research_claim_eligible"] is not False):
        raise HydraReviewError("original DEV plan is not its exact archived completed input")
    return plan


def cold_selection(cold_plan: dict[str, object], scope: str) -> dict[str, object]:
    if scope not in {"none", "sample", "full"}:
        raise HydraReviewError("cold scope must be none, sample, or full")
    count = cold_plan["target_count"]
    indices = [] if scope == "none" else (
        sorted({index * (count - 1) // 15 for index in range(16)}) if scope == "sample" else list(range(count)))
    # Calibration is deliberately per-target-cold, not a favorable reordering
    # or a claim to cover every provider. Full passes use the frozen batches.
    batches = [[index] for index in indices] if scope != "full" else cold_plan["batches"]
    return {"scope": scope, "indices": indices, "batches": batches, "passes": 2,
            "selected_targets": len(indices), "reserved_batches": 2 * len(batches),
            "limits": COLD_LIMITS.to_dict(), "sampling": "16 fixed enrollment-order quantiles; not a statistical benchmark",
            "full_epoch_required_for_cold_gate": True, "automatic_retries": False}


def build_review_plan(
    *, reference_project: Path, lean_binary: Path, development_directory: Path = DEFAULT_DEVELOPMENT,
    cold_scope: str = "sample", cold_batch_size: int = 1, allocations: list[dict[str, str]] | None = None,
    cold_wall_budget: int = 900,
) -> dict[str, object]:
    if type(cold_wall_budget) is not int or not 30 <= cold_wall_budget <= 3600:
        raise HydraReviewError("whole cold-stage wall budget must lie in [30,3600] seconds")
    original = _development(development_directory)
    epoch = freeze_epoch()
    preparation_dirs = tuple(Path(entry["preparation_directory"]) for entry in original["preparation_audits"])
    for path in preparation_dirs:
        _relative(path)
    lineage = build_lineage_review(
        epoch, benchmark=original["benchmark"],
        audit_receipts=tuple(entry["audit"] for entry in original["preparation_audits"]),
        preparation_dirs=preparation_dirs, allocations=allocations, original_source=original["source"],
    )
    cases = build_conformance_cases()
    conformance = conformance_manifest(cases, epoch_sha256=epoch.epoch_sha256)
    cold_plan = build_cold_replay_plan(epoch, batch_size=cold_batch_size)
    selection = cold_selection(cold_plan, cold_scope)
    reference = inspect_reference(reference_project, lean_binary)
    plan = {
        "schema": SCHEMA, "status": "planned", "source": source_identity(),
        "profile": development_profile(), "epoch_sha256": epoch.epoch_sha256,
        "development_directory": _relative(development_directory), "development_plan_sha256": original["plan_sha256"],
        "preparation_directories": [str(path) for path in preparation_dirs],
        "allocation_input": allocations, "lineage_review": lineage,
        "reference": reference, "reference_project": str(reference_project.resolve()),
        "conformance": conformance, "cold_plan": cold_plan, "cold_selection": selection,
        "cold_wall_budget": cold_wall_budget, "parallel_workers": 1,
        "native_limits": NATIVE_LIMITS.to_dict(),
        "reserved_reference_processes": len(MODULES) + 1 + (len(cases) + BATCH_SIZE - 1) // BATCH_SIZE,
        "model_calls": 0, "solver_calls": 0, "data_written": False,
        "model_training_authorized": False, "independent_human_review_granted": False,
        "h0_complete": False, "h1_complete": False, "sealed_benchmark": False,
        "research_claim_eligible": False,
    }
    plan["plan_sha256"] = digest(plan)
    if len(canonical(plan)) > MAX_BYTES:
        raise HydraReviewError("review plan exceeds the 64-MiB whole-run reservation")
    return plan


def validate_plan(plan: dict[str, object], *, live_audits: bool = True) -> None:
    if type(plan) is not dict or set(plan) != PLAN_FIELDS:
        raise HydraReviewError("review plan has missing or unknown fields")
    _signed(plan, "plan_sha256")
    validate_sources(plan["source"])
    if (plan["schema"] != SCHEMA or plan["status"] != "planned"
        or type(plan["parallel_workers"]) is not int or plan["parallel_workers"] != 1
        or not _same(plan["native_limits"], NATIVE_LIMITS.to_dict())
        or any(plan[key] is not False for key in (
            "data_written", "model_training_authorized", "independent_human_review_granted",
            "h0_complete", "h1_complete", "sealed_benchmark", "research_claim_eligible"))
        or type(plan["model_calls"]) is not int or plan["model_calls"] != 0
        or type(plan["solver_calls"]) is not int or plan["solver_calls"] != 0
        or type(plan["cold_wall_budget"]) is not int or not 30 <= plan["cold_wall_budget"] <= 3600):
        raise HydraReviewError("review plan changed its claim or resource boundary")
    validate_reference_identity(plan["reference"])
    if (type(plan["reference_project"]) is not str or not Path(plan["reference_project"]).is_absolute()
        or str(Path(plan["reference_project"]).resolve(strict=True)) != plan["reference_project"]):
        raise HydraReviewError("reference project path is not its exact declared local input")
    validate_reference_provenance(Path(plan["reference_project"]), plan["reference"])
    if (type(plan["development_directory"]) is not str
        or _relative(ROOT / plan["development_directory"]) != plan["development_directory"]
        or type(plan["preparation_directories"]) is not list
        or not 1 <= len(plan["preparation_directories"]) <= 8):
        raise HydraReviewError("review development inputs are not canonical repository-local paths")
    for path in plan["preparation_directories"]:
        if type(path) is not str or str((ROOT / _relative(Path(path))).resolve()) != path:
            raise HydraReviewError("review preparation inputs are not exact repository-local paths")
    epoch = freeze_epoch()
    cases = build_conformance_cases()
    if (plan["epoch_sha256"] != epoch.epoch_sha256 or not _same(plan["profile"], development_profile())
        or not _same(plan["cold_plan"], build_cold_replay_plan(epoch, batch_size=plan["cold_plan"]["batch_size"]))
        or not _same(plan["cold_selection"], cold_selection(plan["cold_plan"], plan["cold_selection"]["scope"]))
        or not _same(plan["conformance"], conformance_manifest(cases, epoch_sha256=epoch.epoch_sha256))):
        raise HydraReviewError("review changed its frozen epoch, profile, fixtures, or cold selection")
    if (type(plan["reserved_reference_processes"]) is not int
        or plan["reserved_reference_processes"] != len(MODULES) + 1 + (len(cases) + BATCH_SIZE - 1) // BATCH_SIZE):
        raise HydraReviewError("review reference reservation differs from its exact module/case inventory")
    if live_audits:
        original = _development(ROOT / plan["development_directory"])
        if (original["plan_sha256"] != plan["development_plan_sha256"]
            or plan["preparation_directories"] != [entry["preparation_directory"] for entry in original["preparation_audits"]]):
            raise HydraReviewError("review changed its original development/preparation inputs")
        reviewed = build_lineage_review(
            epoch, benchmark=original["benchmark"],
            audit_receipts=tuple(entry["audit"] for entry in original["preparation_audits"]),
            preparation_dirs=tuple(Path(path) for path in plan["preparation_directories"]),
            allocations=plan["allocation_input"], original_source=original["source"],
        )
        if not _same(reviewed, plan["lineage_review"]):
            raise HydraReviewError("lineage review changed under independent live re-audit")


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
    common = {"schema", "mode", "source", "epoch_sha256", "profile_sha256"}
    extra = {"case_manifest_sha256"} if request.get("mode") == "native" else {
        "targets", "pass_number", "batch_number", "edition_identity_sha256", "certificate_limits"}
    if (set(request) != common | extra or request["schema"] != SCHEMA
        or request["mode"] not in {"native", "cold"}):
        raise HydraReviewError("internal review worker request differs")
    # The controller authenticates the complete historical Git inventory
    # before and after the run. Workers recheck exact bytes without spawning
    # Git subprocesses under their no-descendant resource contract.
    check_recorded_source_bytes(request["source"])
    if request["profile_sha256"] != development_profile()["profile_sha256"]:
        raise HydraReviewError("review worker profile changed")
    if request["mode"] == "native":
        cases = build_conformance_cases()
        manifest = conformance_manifest(cases, epoch_sha256=request["epoch_sha256"])
        if manifest["manifest_sha256"] != request["case_manifest_sha256"]:
            raise HydraReviewError("native worker fixture manifest differs")
        sys.stdout.buffer.write(canonical(check_native_cases(cases)) + b"\n")
        sys.stdout.buffer.flush()
        return
    if (type(request["targets"]) is not list or not 1 <= len(request["targets"]) <= 16
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
        record = {"pass_number": request["pass_number"], "batch_number": request["batch_number"],
                  "receipt": receipt}
        sys.stdout.buffer.write(canonical(record) + b"\n")
        sys.stdout.buffer.flush()


def _request(plan: dict[str, object], mode: str, **extra) -> dict[str, object]:
    return {"schema": SCHEMA, "mode": mode, "source": plan["source"],
            "epoch_sha256": plan["epoch_sha256"], "profile_sha256": plan["profile"]["profile_sha256"], **extra}


def _cold_request(plan: dict[str, object], pass_number: int, batch_number: int, indices: list[int]) -> dict[str, object]:
    cold = plan["cold_plan"]
    return _request(plan, "cold", targets=[cold["targets"][index] for index in indices],
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
                        indices: list[int], result: dict[str, object]) -> list[dict[str, object]]:
    request = _cold_request(plan, pass_number, batch_number, indices)
    validate_process_record(result, command=(sys.executable, str(SCRIPT), "--worker"),
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


def run_cold(plan: dict[str, object], *, progress=None) -> dict[str, object]:
    started = time.monotonic()
    deadline = started + plan["cold_wall_budget"]
    rows, batches = [], []
    schedule = _cold_schedule(plan)
    for pass_number, batch_number, indices in schedule:
        request_bytes = canonical(_cold_request(plan, pass_number, batch_number, indices))
        launched = time.monotonic()
        if deadline - launched < COLD_LIMITS.wall_seconds:
            break
        result = run_bounded((sys.executable, str(SCRIPT), "--worker"), cwd=ROOT,
                              limits=COLD_LIMITS, input_bytes=request_bytes)
        completed = _decode_cold_worker(plan, pass_number, batch_number, indices, result)
        rows.extend(completed)
        batches.append({"pass_number": pass_number, "batch_number": batch_number,
                        "indices": indices, "started_wall_seconds": launched - started,
                        "worker": result, "completed_targets": len(completed)})
        if progress:
            progress("cold_replay", len(batches), len(schedule),
                     f"pass {pass_number}, {len(completed)}/{len(indices)} receipts, {result['reason']}")
    elapsed = time.monotonic() - started
    ledger = {"schema": COLD_LEDGER_SCHEMA, "batches": batches, "rows": rows,
              "wall_seconds": elapsed, "wall_budget": plan["cold_wall_budget"],
              "stop_reason": "completed" if len(batches) == len(schedule) else "wall-budget-insufficient-for-next-worker",
              "summary": summarize_cold(plan, rows, batches, wall_seconds=elapsed)}
    validate_cold_ledger(plan, ledger)
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
            "full_epoch_replayed_twice": selection["scope"] == "full" and matching and failures == 0 and wall_seconds <= plan["cold_wall_budget"],
            "all_scripts_regenerated": False, "model_calls": 0, "solver_calls": 0}


def validate_cold_ledger(plan: dict[str, object], ledger: dict[str, object]) -> None:
    if (type(ledger) is not dict or set(ledger) != {
        "schema", "batches", "rows", "summary", "wall_seconds", "wall_budget", "stop_reason",
    } or ledger["schema"] != COLD_LEDGER_SCHEMA or type(ledger["batches"]) is not list
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
        completed = _decode_cold_worker(plan, number, index, indices, batch["worker"])
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
    validate_cold_ledger(plan, fresh)
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


def _execute_checks(plan: dict[str, object], directory: Path, *, reference_source: Path, progress=None) -> dict[str, object]:
    cases = build_conformance_cases()
    native_worker = run_bounded((sys.executable, str(SCRIPT), "--worker"), cwd=ROOT,
                                limits=NATIVE_LIMITS, input_bytes=canonical(_request(
                                    plan, "native", case_manifest_sha256=plan["conformance"]["manifest_sha256"])))
    if native_worker["reason"] != "exited" or native_worker["returncode"] != 0:
        raise HydraReviewError(f"native conformance worker did not complete: {native_worker['reason']}, exit {native_worker['returncode']}: {native_worker['stderr']}")
    native = decode(native_worker["stdout"].encode(), limit=8 * 1024**2)
    validate_native_evidence(plan, native, native_worker, cases)
    reference_dir = directory / "reference-build"
    stage_reference(reference_source, reference_dir, plan["reference"])
    build = build_reference(reference_dir, plan["reference"], progress=progress)
    reference = check_reference_cases(reference_dir, plan["reference"], build, cases, progress=progress)
    if reference["status"] != "passed":
        raise HydraReviewError("independent reference disagreed with conformance expectations: " + str(reference["mismatches"]))
    cold = run_cold(plan, progress=progress)
    return {"native": native, "native_worker": native_worker, "reference_build": build,
            "reference_results": reference, "cold": cold}


def validate_native_evidence(plan: dict[str, object], native: dict[str, object], result: dict[str, object], cases: tuple) -> None:
    request = _request(plan, "native", case_manifest_sha256=plan["conformance"]["manifest_sha256"])
    validate_process_record(result, command=(sys.executable, str(SCRIPT), "--worker"),
                            limits=NATIVE_LIMITS, input_bytes=canonical(request), success_codes=(0,))
    _signed(native, "report_sha256")
    if (result["stderr"] or not _same(decode(result["stdout"].encode(), limit=8 * 1024**2), native)
        or not _same(native, check_native_cases(cases)) or native["all_expected_results"] is not True):
        raise HydraReviewError("native evidence differs from its exact worker bytes and freshly decoded fixtures")


def review_summary(plan: dict[str, object], results: dict[str, object]) -> dict[str, object]:
    return {"positive_formulas": plan["conformance"]["distinct_positive_formula_count"],
            "native_positive_accepts": results["native"]["positive_certificates_accepted"],
            "native_mutations_rejected": results["native"]["certificate_mutations_rejected"],
            "reference_cases_matched": results["reference_results"]["case_count"],
            "reference_compiler_matches_pin": plan["reference"]["matches_project_toolchain_pin"],
            "lineage_status": plan["lineage_review"]["status"],
            "unexposed_structural_dev_components": plan["lineage_review"]["feasibility"]["unexposed_structural_component_count"],
            "cold": results["cold"]["summary"]}


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
    """Validate all saved evidence before spending resources on reproduction."""
    if type(results) is not dict or set(results) != EVIDENCE_NAMES:
        raise HydraReviewError("review has an incomplete evidence inventory")
    cases = build_conformance_cases()
    validate_native_evidence(plan, results["native"], results["native_worker"], cases)
    validate_build_receipt(plan["reference"], results["reference_build"])
    validate_reference_results(plan["reference"], results["reference_results"], cases)
    if results["reference_results"]["status"] != "passed":
        raise HydraReviewError("saved reference conformance did not pass")
    validate_cold_ledger(plan, results["cold"])
    if not _same(report["summary"], review_summary(plan, results)):
        raise HydraReviewError("review summary differs from its validated evidence and frozen plan")


def execute_review(plan: dict[str, object], directory: Path, *, progress=None) -> dict[str, object]:
    validate_plan(plan)
    if plan["source"]["git_dirty"] or plan["source"] != source_identity():
        raise HydraReviewError("execution requires its exact clean committed source plan")
    if directory.exists() or directory.is_symlink():
        raise HydraReviewError("review execution requires a fresh output directory")
    directory = directory.resolve()
    directory.mkdir(parents=True, mode=0o700)
    plan_file = write_once(directory / "plan.json", canonical(plan) + b"\n")
    case_file = write_once(directory / "cases.jsonl", _case_archive(build_conformance_cases()))
    started = datetime.now(timezone.utc).isoformat()
    # Retain the exact small independent source files, never prebuilt oleans.
    stage_reference(Path(plan["reference_project"]), directory / "reference-source", plan["reference"])
    results = _execute_checks(plan, directory, reference_source=directory / "reference-source", progress=progress)
    validate_plan(plan)
    if plan["source"] != source_identity():
        raise HydraReviewError("source changed during review execution")
    evidence = {name: write_once(directory / f"{name}.json", canonical(value) + b"\n") for name, value in results.items()}
    report = {
        "schema": SCHEMA, "status": "completed-with-open-gates", "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(), "plan": plan_file, "cases": case_file,
        "plan_sha256": plan["plan_sha256"], "evidence": evidence,
        "summary": review_summary(plan, results),
        "model_calls": 0, "solver_calls": 0, "model_training_authorized": False,
        "independent_human_review_granted": False, "h0_complete": False, "h1_complete": False,
        "sealed_benchmark": False, "research_claim_eligible": False,
    }
    report["report_sha256"] = digest(report)
    validate_report_header(report)
    validate_saved_results(plan, report, results)
    write_once(directory / "report.json", canonical(report) + b"\n")
    return report


def verify_review(directory: Path, *, progress=None) -> dict[str, object]:
    directory = directory.resolve(strict=True)
    report = read_record(directory / "report.json")
    validate_report_header(report)
    def checked(descriptor: dict[str, object], expected_name: str) -> bytes:
        if (type(descriptor) is not dict or set(descriptor) != {"path", "bytes", "sha256"}
            or descriptor["path"] != expected_name or type(descriptor["bytes"]) is not int
            or not 0 <= descriptor["bytes"] <= MAX_BYTES or not _sha(descriptor["sha256"])):
            raise HydraReviewError("review evidence descriptor differs from its exact reserved file")
        raw = read_bytes(directory / descriptor["path"], limit=MAX_BYTES)
        if len(raw) != descriptor["bytes"] or hashlib.sha256(raw).hexdigest() != descriptor["sha256"]:
            raise HydraReviewError("review evidence bytes differ")
        return raw
    plan = decode(checked(report["plan"], "plan.json"), limit=MAX_BYTES)
    if report["plan_sha256"] != plan["plan_sha256"]:
        raise HydraReviewError("review report changed its plan identity")
    validate_plan(plan)
    if checked(report["cases"], "cases.jsonl") != _case_archive(build_conformance_cases()):
        raise HydraReviewError("retained exact conformance fixtures changed")
    if type(report["evidence"]) is not dict or set(report["evidence"]) != EVIDENCE_NAMES:
        raise HydraReviewError("review report has an incomplete evidence inventory")
    old = {name: decode(checked(value, f"{name}.json"), limit=MAX_BYTES) for name, value in report["evidence"].items()}
    validate_saved_results(plan, report, old)
    with tempfile.TemporaryDirectory(prefix="hydra-reference-review-verify-") as temporary:
        fresh = _execute_checks(plan, Path(temporary), reference_source=directory / "reference-source", progress=progress)
    if (not _same(old["native"], fresh["native"])
        or not _same(old["reference_results"]["cases"], fresh["reference_results"]["cases"])
        or not _same(old["reference_build"]["axiom_footprint"], fresh["reference_build"]["axiom_footprint"])
        or not _same(old["reference_build"]["compiled_files"], fresh["reference_build"]["compiled_files"])):
        raise HydraReviewError("independent reference/native recheck differs from saved outcomes")
    # Reproducibility applies to every previously checked original theorem;
    # a timeout is not a negative fact which must be reproduced as a timeout.
    reproduced = compare_cold_reproduction(plan, old["cold"], fresh["cold"])
    validate_plan(plan)
    return {"status": "passed", "report_sha256": report["report_sha256"],
            "reference_cases_rechecked": len(fresh["reference_results"]["cases"]),
            "cold_positive_receipts_reproduced": reproduced,
            "live_lineage_audits_repeated": True, "fresh_reference_rebuilt": True,
            "model_calls": 0, "solver_calls": 0, "h0_complete": False,
            "model_training_authorized": False, "research_claim_eligible": False}
