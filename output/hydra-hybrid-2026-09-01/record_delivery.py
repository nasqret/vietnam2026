"""Bind this completed local delivery; no training, solver, or model execution."""
from datetime import datetime, timezone
import hashlib
import http.client
import json
from pathlib import Path
import shutil
import sys

OUTPUT = Path(__file__).resolve().parent
ROOT = OUTPUT.parents[1]
APP = ROOT / "hydra-playground"
sys.path.insert(0, str(APP))
import model_runtime as runtime
import vampire_process


def descriptor(path):
    digest, length = hashlib.sha256(), 0
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            length += len(block)
            digest.update(block)
    return {"bytes": length, "sha256": digest.hexdigest()}


def read(path):
    return json.loads(path.read_bytes())


def require(value, message):
    if not value:
        raise ValueError(message)


require(not (OUTPUT / "verification.json").exists(), "Use a fresh delivery record.")
original_pins = {
    APP / "model_runtime.py": "3d15371e9c5dd679fe6bea91d1d06df14ffaaba1f0e748c84266c21958a38bc5",
    APP / "setup_model.py": "9c1c228930f8c98e35466e10cab07c7ead28564da1eb489339bb95f3cc946a5d",
    APP / "setup-requirements.txt": "f70813b58c8bf37980b4ebc20531b18e3f9577ae6d266b11cc380c3315dc298c",
    runtime.MODEL_ROOT / "manifest.json": runtime.MODEL_MANIFEST_SHA,
    runtime.MODEL_ROOT / "adapter/adapter_model.safetensors": runtime.ADAPTER_SHA,
    ROOT / "output/hydra-playground-2026-09-01/verification.json": "2eb599c93ccddc93a34948abc970f69b994528cbe7e8cda29eeecfecb95494e6",
}
unchanged = {}
for path, expected in original_pins.items():
    pin = descriptor(path)
    require(pin["sha256"] == expected, "Previously pinned bytes changed: " + str(path))
    unchanged[str(path.relative_to(ROOT))] = pin
source_pin = runtime._source_snapshot()
source_catalog = read(runtime.SOURCE_CATALOG)
quantized, quantized_pin, ready_pin = runtime._quantized_snapshot()
require(quantized_pin["sha256"] == "fc9ebb9841ecf36243f99ee408c71cd8bf6c4df968130c96af281a82fd55809c",
        "The existing compact model manifest changed.")
binary, vampire_manifest, vampire_manifest_pin = vampire_process.package(verify_binary=True)
require(vampire_manifest["executable"]["sha256"] == "b5168c690e0293cdac78f16d8418d7eeabcd6708f90a60cd2bf45313b6d98699",
        "The installed Vampire binary changed.")

experiments = {}
for name, expected_jobs, proofs in (
    ("pilot-01", 20, {"heuristic": 4, "symbolic": 4, "model": 1, "hybrid": 4}),
    ("advisers-01", 15, {"heuristic": 1, "symbolic": 1, "hybrid": 2}),
    ("advisers-02", 15, {"heuristic": 3, "symbolic": 4, "hybrid": 4}),
):
    directory = OUTPUT / name
    summary, completion = read(directory / "summary.json"), read(directory / "actual-completion.json")
    require(summary["status"] == "complete" and summary["recorded_jobs"] == expected_jobs
            and summary["all_requested_cases_recorded"] is True and completion["actual_outer_exit_code"] == 0,
            "Experiment lacks complete records and an actually observed successful exit: " + name)
    require({mode: value["positive_proofs"] for mode, value in summary["modes"].items()} == proofs,
            "Reported positive proof counts changed.")
    for filename in summary["case_files"]:
        record = read(directory / filename)
        require(record["outcome"] in {"proved", "unknown", "rejected"}, "Unexpected experiment outcome.")
        require(record["expected"] != "refutable" or record["kernel_verified"] is False,
                "A false diagnostic was incorrectly accepted.")
    if name == "advisers-02":
        require(all(descriptor(APP / filename) == pin for filename, pin in completion["files"].items()),
                "The final tested backend source changed after completion.")
    experiments[name] = {
        "actual_completion": completion,
        "positive_proofs_out_of_four": proofs,
        "artifacts": {path.name: descriptor(path) for path in sorted(directory.glob("*.json"))},
    }

browser_dir = OUTPUT / "browser-hybrid-01"
browser = read(browser_dir / "browser-hybrid.json")
cancellation = read(browser_dir / "hybrid-cancellation-ui.json")
symbolic = read(browser_dir / "symbolic-ui-result.json")
require(browser["status"] == "passed" and len(browser["checks"]) == 6, "Browser checks are incomplete.")
require(cancellation["cancelled"] is True and cancellation["computation_slot_released"] is True
        and cancellation["calls_observed_before_cancel"]["model"] >= 1
        and cancellation["manual_replay_after_cleanup"]["kernel_checked"] is True,
        "Actual hybrid cancellation or subsequent native replay was not checked.")
require(symbolic["kernel_checked"] is True and symbolic["search"]["vampire_calls"] >= 1
        and symbolic["proof_sources"].get("vampire", 0) > 0 and symbolic["execution"]["quiescent"] is True,
        "The browser did not exercise real Vampire advice and native reconstruction.")

connection = http.client.HTTPConnection("127.0.0.1", 8767, timeout=5)
try:
    connection.request("GET", "/api/status", headers={"Connection": "close"})
    response = connection.getresponse()
    require(response.status == 200, "The local delivery server is unavailable.")
    status = json.loads(response.read(65537))
finally:
    connection.close()
status.pop("csrf_token", None)
require(status.get("ok") is True and all(value["available"] is True for value in status["search_modes"].values()),
        "Not all delivered search modes are available.")

# Retain the complete small application source independently of mutable logs.
# No runtime weights, virtual environments, or historical execution trees are copied.
snapshot = OUTPUT / "source-files"
snapshot.mkdir(exist_ok=False)
files = sorted(path for path in APP.iterdir() if path.is_file() and path.suffix in {".py", ".json", ".html", ".js", ".css", ".md", ".txt", ".sh"})
files += sorted(path for path in (APP / "tests").iterdir() if path.is_file() and path.suffix in {".py", ".mjs"})
source_files = {}
for path in files:
    require(not path.is_symlink(), "Source snapshot must not follow symlinks.")
    relative = path.relative_to(APP)
    target = snapshot / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    pin = descriptor(path)
    require(descriptor(target) == pin, "Source snapshot copy failed.")
    source_files[str(relative)] = pin

record = {
    "schema": "hydra-hybrid-delivery-verification-v1", "status": "checks-passed",
    "delivery_record_attempt": 2, "recording_script": descriptor(Path(__file__)),
    "preserved_recording_failure": {"receipt": "verification-attempt01/actual-failure.json",
                                    **read(OUTPUT / "verification-attempt01/actual-failure.json")},
    "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Local functional integration and intentionally exposed engineering probes; not unseen model accuracy.",
    "search_profile": "hydra-playground-hybrid-v2", "training_performed": False,
    "remote_gpu_jobs_started": 0, "user_theorems_uploaded": False, "benchmark_claim": False,
    "numerical_equivalence_to_training": False,
    "unit_tests": {"tests": 56, "actual_exit_code": 0, "completion_chunk": "f095d8", "session_id": 35060,
                   "elapsed_seconds": 4.155, "earlier_passing_gate": {"tests": 54, "completion_chunk": "880177", "actual_exit_code": 0},
                   "preserved_earlier_failure": {"tests": 47, "passed": 46, "actual_exit_code": 1, "completion_chunk": "79e115",
                       "cause": "The file guard rejected the fixed Vampire helper's anonymous stdin pipe; fixed with a bounded existing-FIFO-FD exception.",
                       "targeted_followup": {"tests": 3, "actual_exit_code": 0, "completion_chunk": "d501d3"}}},
    "browser": {"actual_exit_code": 0, "completion_chunk": "b4a6b5", "session_id": 27352,
                "grouped_checks": browser["checks"], "isolated_profile": True, "existing_user_profile_accessed": False,
                "screenshots_visually_inspected_by_root": browser["screenshots"],
                "cancellation_counts_are_observed_progress_not_final_totals": True,
                "artifacts": {path.name: descriptor(path) for path in sorted(browser_dir.iterdir()) if path.is_file()}},
    "experiments": experiments,
    "preserved_original_bytes": unchanged,
    "frozen_kernel": {"commit": runtime.SOURCE_COMMIT, "catalog": source_pin, "files_checked": len(source_catalog["files"]),
                      "bytes_checked": sum(pin["bytes"] for pin in source_catalog["files"].values())},
    "compact_model": {"manifest": quantized_pin, "readiness": ready_pin, "files_rehashed": len(quantized["files"])},
    "vampire": {"version": "5.0.1", "manifest": vampire_manifest_pin, "executable": descriptor(binary),
                "readiness": descriptor(APP / ".runtime/vampire/ready.json"),
                "original_install_exit_code": 0, "original_install_completion_chunk": "4f231f",
                "original_version_completion_chunk": "2234b3", "original_smoke_completion_chunk": "97a85c",
                "solver_refutation_is_native_proof": False},
    "source_snapshot": {"directory": "source-files", "files": source_files},
    "report": descriptor(OUTPUT / "RESULT.md"), "recovery_note": descriptor(ROOT / "RECOVERY.md"),
    "server": {"url": "http://127.0.0.1:8767/", "tool_session_id": 68834, "launch_chunk": "f500c0", "observed_status": status},
    "own_exit_observation": "See verification-actual-completion.json, written only after the caller observes this process's actual exit.",
}
with (OUTPUT / "verification.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write("\n")
print(json.dumps({"status": record["status"], "unit_tests": 56, "http_jobs": 50,
                  "browser_grouped_checks": 6, "frozen_files_checked": len(source_catalog["files"]),
                  "source_files_archived": len(source_files), "verification": str(OUTPUT / "verification.json")}))
