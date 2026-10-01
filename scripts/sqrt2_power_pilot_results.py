"""Read lossless pilot observations and derive a non-admitting results view."""
from hashlib import sha256
import gzip
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "research/arithmetic-library/sqrt2-power/observations/validated-pilot-v2"


def archive_member(archive, name):
    manifest = json.loads((archive / "manifest.json").read_bytes())
    if manifest.get("schema") != "sqrt2-power-observation-archive-v1":
        raise ValueError("unsupported observation archive")
    row = manifest["files"][name]
    relative = Path(row["path"])
    if relative.is_absolute() or ".." in relative.parts or row["bytes"] > 16*1024**2:
        raise ValueError("unsafe or oversized observation member")
    path = archive / relative
    if path.is_symlink():
        raise ValueError("observation member must not be a symlink")
    compressed = path.read_bytes()
    if len(compressed) != row["gzip_bytes"] or sha256(compressed).hexdigest() != row["gzip_sha256"]:
        raise ValueError("compressed observation changed")
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(row["bytes"]+1)
    if len(raw) != row["bytes"] or sha256(raw).hexdigest() != row["sha256"]:
        raise ValueError("original observation bytes changed")
    return raw, compressed


def process_cpu(arm):
    return sum((arm.get(k) or {}).get("resources", {}).get("cpu_seconds", 0)
               for k in ("generation_process", "fresh_replay_process"))


def observation_results(archive=ARCHIVE):
    report_raw, report_gzip = archive_member(archive, "run/report.json")
    report = json.loads(report_raw)
    if (report.get("schema") != "sqrt2-power-bounded-pilot-v1" or
        report.get("IR_parents_closed") != 0 or report.get("solver_proof_logs_translated") != 0):
        raise ValueError("unsupported pilot authority or comparison")
    frozen = json.loads(archive_member(archive, "run/contracts.json")[0])
    if [r["contract"] for r in report["rows"]] != frozen:
        raise ValueError("not the complete frozen twelve-child run")
    result = dict(schema="sqrt2-power-pilot-results-v1",
        authority="recorded_local_HA_leaf_checks_not_library_admission",
        report_sha256=sha256(report_raw).hexdigest(),
        comparison=report["comparison"], rows=[], solver_hits={k:0 for k in ("z3", "eprover", "vampire")},
        counts=report["counts"], wall_seconds=report["wall_seconds"],
        native_arm_cpu_seconds=0, solver_gated_native_cpu_seconds=0,
        external_cpu_seconds=0, setup_cpu_seconds=process_cpu(report["checked_basis"]),
        model_proof_search_calls=0, model_planning_and_engineering_tokens=None,
        solver_proof_logs_translated=0, independent_lean_checked=False,
        IR_parents_closed=0, library_admissions=0,
        large_numeral_status="P10 unresolved: original RSS stop; changed-strategy retry stopped at the internal copy-work cap. No further retry or limit increase.",
        pending="P04 finite composition, P09 confluent trace, P10 large arithmetic assembly, and P12 CApprox trace are not proved. P10 has a separately elaborated full closed statement.")
    evidence = {"evidence/report.json.gz": report_gzip}
    accepted = []
    for entry in report["rows"]:
        contract = entry["contract"]
        arm = entry.get("native_only", {})
        row = dict(pilot_id=contract["pilot_id"], parent=contract["parent"],
            source=contract["source"], interpretation=contract.get("interpretation", contract.get("reason")),
            coverage=contract["coverage"], status=arm.get("status", "not_dispatched"),
            contract_sha256=contract["contract_sha256"],
            statement_ast_sha256=contract["statement_ast_sha256"],
            solvers={}, closes_IR_parent=False)
        if row["status"] == "fresh_ordinary_HA_checked":
            receipt = arm["fresh_replay"]
            if (receipt["contract_sha256"] != contract["contract_sha256"] or
                receipt["IR_parents_closed"] != 0 or receipt["classical"] is not False or
                any(receipt[k] is not True for k in ("original_target_checked", "forged_body_rejected",
                                                     "false_target_rejected", "empty_context"))):
                raise ValueError("invalid bound replay receipt")
            raw, compressed = archive_member(archive, "run/" + arm["certificate_path"])
            if sha256(raw).hexdigest() != receipt["bundle_sha256"]:
                raise ValueError("certificate bytes differ from the replayed bytes")
            row.update(certificate_path=f"evidence/{row['pilot_id']}-native.json.gz",
                       certificate_sha256=receipt["bundle_sha256"], certificate_bytes=len(raw),
                       proof_nodes=receipt["proof_nodes"])
            evidence[row["certificate_path"]] = compressed
            accepted.append(row)
        for external in entry["external"]:
            solver = external["solver"]
            proc = external.get("process") or {}
            status = external["observation"]["solver_status"]
            row["solvers"][solver] = dict(status=status, reason=proc.get("reason"),
                                           cpu_seconds=proc.get("resources", {}).get("cpu_seconds", 0))
            if status in ("unsat", "Theorem", "Unsatisfiable"):
                result["solver_hits"][solver] += 1
            version = (external.get("capability") or {}).get("version_probe") or {}
            result["external_cpu_seconds"] += sum(p.get("resources", {}).get("cpu_seconds", 0)
                                                   for p in (proc, version))
        result["native_arm_cpu_seconds"] += process_cpu(arm)
        result["solver_gated_native_cpu_seconds"] += process_cpu(entry.get("solver_gated_reproof", {}))
        result["rows"].append(row)
    if (len(accepted) != result["counts"]["native_checked_leaves"] or
        sum(r["coverage"] == "full_pilot_contract" for r in accepted) != result["counts"]["fully_checked_pilot_contracts"] or
        sum(r["coverage"] == "supporting_subleaf_only" for r in accepted) != result["counts"]["checked_supporting_subleaves"]):
        raise ValueError("pilot counts differ from the bound per-leaf receipts")
    # A view of a recorded receipt is NOT a fresh verifier or a proof-admission
    # API. The immutable build pins the archive manifest independently.
    return result, evidence
