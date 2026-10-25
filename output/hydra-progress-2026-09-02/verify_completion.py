"""Read-only final artifact authentication; never search, infer, or replay.

Run after the independent run audit, publication, browser checks, final report,
source archive and idle-server observation are complete. Actual process exits
are supplied by separate externally observed receipts, never inferred here.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import resource
import signal
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
APP = ROOT / "hydra-playground"
OLD = ROOT / "output/hydra-advanced-2026-09-02"
sys.path.insert(0, str(APP))
assert sys.flags.isolated and sys.dont_write_bytecode
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(180)


def read(path):
    assert path.is_file() and not path.is_symlink(), path
    assert path.stat().st_size <= 32 * 1024 * 1024, path
    return json.loads(path.read_bytes())


def pin(path):
    assert path.is_file() and not path.is_symlink(), path
    digest, count = hashlib.sha256(), 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            count += len(block)
    return {"bytes": count, "sha256": digest.hexdigest()}


def pinned(path):
    return {"path": str(path.relative_to(ROOT)), **pin(path)}


def safe_member(directory, name):
    assert type(name) is str and name
    relative = Path(name)
    assert not relative.is_absolute() and ".." not in relative.parts, name
    path = directory / relative
    assert not any(parent.is_symlink() for parent in (path, *path.parents)), path
    return path


def observed_exit(path, expected):
    receipt = read(path)
    values = [receipt[key] for key in ("actual_exit_code", "exit_code") if key in receipt]
    assert values and all(type(value) is int and value == expected for value in values), path
    chunks = [receipt[key] for key in ("completion_chunk_id", "completion_chunk") if key in receipt]
    assert chunks and all(type(value) is str and value and value == chunks[0] for value in chunks), path
    return {"actual_exit_code": expected, "receipt": pinned(path)}


assert not (BASE / "verification.json").exists(), "Never overwrite final verification evidence."
archives, archive_files = {}, {}
frozen_archive_sha = {
    "source-v5": "bb7b21d9ae8fd780aaa438c31d3ca5ef76f816ab708e69146547d4f21090c5e1",
    "source-v6": "73be0e8fc4aa8e37110c6faef8a2d18673e23b5854e2dc4da27e5a87f373b445",
}
for name, version in (("source-v5", "v5"), ("source-v6", "v6"), ("source-v6-final", "v6")):
    manifest = read(BASE / name / "manifest.json")
    if name in frozen_archive_sha:
        assert pin(BASE / name / "manifest.json")["sha256"] == frozen_archive_sha[name], name
    assert manifest["schema"] == "hydra-source-archive-v1"
    assert manifest["search_profile"] == "hydra-playground-hybrid-" + version
    assert manifest["vampire_runtime_policy"] == "hydra-playground-vampire-runtime-policy-v3"
    entries = manifest["files"]
    assert type(entries) is dict and entries
    for filename, expected in entries.items():
        assert pin(safe_member(BASE / name, filename)) == expected, (name, filename)
        if name == "source-v6-final":
            assert pin(safe_member(APP, filename)) == expected, filename
    archive_files[name] = entries
    archives[name] = {"files_verified": len(entries), "manifest": pinned(BASE / name / "manifest.json")}

# This earlier receipt pins the unchanged kernel, model and gallery evidence.
assert pin(OLD / "verification.json")["sha256"] == "f6a58ae72e4678ab4ae997aa22d911dc3231bf972cb8ae23dd51b1db0c985ed6"
previous = read(OLD / "verification.json")

import model_runtime as model
from server import showcase_catalog
from vampire_process import package
from vampire_limits import RUNTIME_POLICY

assert pin(APP / "model_runtime.py")["sha256"] == "3d15371e9c5dd679fe6bea91d1d06df14ffaaba1f0e748c84266c21958a38bc5"
assert RUNTIME_POLICY == "hydra-playground-vampire-runtime-policy-v3"
candidate, handle, source_pin, inputs_pin = model._load_authenticated()
artifacts = model._artifact_snapshot(handle)
quantized, quantized_pin, ready_pin = model._quantized_snapshot()
_, vampire_manifest, vampire_manifest_pin = package(verify_binary=True)
assert vampire_manifest_pin["sha256"] == "b553a839e49fe8f6e4881d124edc0ad7ee8f241403476339d8f4d07213a2151f"
assert vampire_manifest["executable"]["sha256"] == "b5168c690e0293cdac78f16d8418d7eeabcd6708f90a60cd2bf45313b6d98699"
catalog = read(model.SOURCE_CATALOG)
assert len(catalog["files"]) == 896
assert len(quantized["files"]) == 318
assert model.SOURCE_COMMIT == previous["kernel"]["commit"]
assert source_pin == previous["kernel"]["catalog"] and inputs_pin == previous["kernel"]["inputs"]
assert model.MODEL_MANIFEST_SHA == previous["saved_model"]["manifest_sha256"]
assert model.ADAPTER_SHA == previous["saved_model"]["adapter_sha256"]
assert quantized_pin == previous["saved_model"]["quantized_manifest"]
assert ready_pin == previous["saved_model"]["readiness"]
assert not any(name in sys.modules for name in ("mlx", "mlx_lm", "torch", "transformers"))

audit_path = BASE / "final-audit-01/audit.json"
audit = read(audit_path)
audit_exit = observed_exit(BASE / "final-audit-01/actual-completion.json", 0)
assert audit["schema"] == "hydra-progress-completed-runs-audit-v1"
assert audit["status"] == "complete" and audit["errors"] == []
assert type(audit["planned_case_records"]) is int and audit["planned_case_records"] == 16
assert type(audit["audited_case_records"]) is int and audit["audited_case_records"] == 16
shared_cases = ("fermat_7", "sophie_germain_nonnegative_coordinates",
                "brahmagupta_balanced_identity", "pythagorean_positive_coordinates", "parity_dichotomy")
expected_batches = {
    "baseline-v4-01": ("v4", shared_cases),
    "comparison-v5-01": ("v5", shared_cases),
    "regression-v6-01": ("v6", ("cubic_mod_6",)),
    "multivariate-v6-01": ("v6", ("multivariate_consecutive_product_even",)),
    "negative-v6-01": ("v6", ("negative_fermat_7_mod_8", "negative_sophie_germain_coefficient")),
    "adviser-v6-01": ("v6", ("successor_zero_explosion",)),
    "followup-v6-01": ("v6", ("fermat_7",)),
}
assert len(audit["batches"]) == len(expected_batches)
audited_batches = {batch["name"]: batch for batch in audit["batches"]}
assert set(audited_batches) == set(expected_batches)
for name, (version, case_ids) in expected_batches.items():
    batch = audited_batches[name]
    assert batch["version"] == version and batch["status"] == "complete", name
    assert tuple(batch["expected_case_ids"]) == case_ids, name
    assert tuple(case["case_id"] for case in batch["cases"]) == case_ids, name
    assert all(case["errors"] == [] and case["artifact_consistency_passed"] is True
               for case in batch["cases"]), name
    observed_exit(BASE / name / "actual-completion.json", 0)
assert 0 < len(audit["inputs"]) <= 512
audited_inputs = set()
for entry in audit["inputs"]:
    assert entry["path"] not in audited_inputs, entry["path"]
    assert pin(safe_member(ROOT, entry["path"])) == {key: entry[key] for key in ("bytes", "sha256")}
    audited_inputs.add(entry["path"])
for path in (BASE / "evaluation-design/audit_completed_runs.py", BASE / "source-v5/manifest.json",
             BASE / "source-v6/manifest.json", OLD / "source-v4-final/manifest.json"):
    assert str(path.relative_to(ROOT)) in audited_inputs, path


def gate_sources(name, archive):
    before = read(BASE / name / "source-before.json")
    assert type(before) is dict and before
    assert before == read(BASE / name / "source-after.json"), name
    for filename, expected in before.items():
        assert archive_files[archive].get(filename) == expected, (name, archive, filename)
    return before

# The first full-suite attempt stays failed. Only its worker subprocess tests
# were blocked by the test parent's inherited hard CPU ceiling; all ten worker
# tests passed after correcting that harness, with identical application bytes.
whole = read(BASE / "full-gate-01/result.json")
worker = read(BASE / "worker-gate-02/result.json")
assert whole == {"tests": 162, "failures": 9, "errors": 0, "skipped": 0,
    "source_pins_unchanged": True, "passed": False, "scope": whole["scope"]}
assert worker["passed"] is True and worker["tests"] == 10
assert worker["failures"] == worker["errors"] == worker["skipped"] == 0
assert worker["source_pins_unchanged"] is True
test_pins = gate_sources("full-gate-01", "source-v5")
assert test_pins == gate_sources("worker-gate-02", "source-v5")
failures = re.findall(r"(?m)^FAIL: (.+)$", (BASE / "full-gate-01/output.txt").read_text())
assert len(failures) == 9 and all("(test_worker.NativeReplayTests." in value for value in failures)
assert "ValueError: not allowed to raise maximum limit" in (BASE / "full-gate-01/output.txt").read_text()

# The v6 gate is separate evidence. Only gate-covered code/tests/UI must stay
# identical through publication; README and gallery files may change afterward.
refinement_name = "refinement-gate-v6-01"
refinement = read(BASE / refinement_name / "result.json")
assert type(refinement["tests"]) is int and refinement["tests"] == 48
assert refinement["passed"] is True and refinement["source_pins_unchanged"] is True
assert all(type(refinement[key]) is int and refinement[key] == 0 for key in ("failures", "errors", "skipped"))
refinement_pins = gate_sources(refinement_name, "source-v6")
required_v6_sources = {"decomposition_memory.py", "hybrid_search.py", "hybrid_runtime.py",
    "evaluate_advanced.py", "polynomial_chunks.py", "tests/test_decomposition_memory.py",
    "tests/test_decomposition_search_memory.py", "tests/test_polynomial_continuations.py",
    "tests/test_hybrid_search.py", "tests/test_hybrid_runtime.py", "tests/test_evaluate_advanced.py"}
assert required_v6_sources <= refinement_pins.keys()
for filename, expected in refinement_pins.items():
    assert archive_files["source-v6-final"].get(filename) == expected, filename
refinement_output = (BASE / refinement_name / "output.txt").read_text()
assert re.search(r"(?m)^Ran " + str(refinement["tests"]) + r" tests in ", refinement_output)
assert not re.findall(r"(?m)^(?:FAIL|ERROR): ", refinement_output)
assert re.search(r"(?m)^OK$", refinement_output)
tests = {
    "full_suite_initial": {**observed_exit(BASE / "full-gate-01/actual-completion.json", 1),
                           "source_archive": "source-v5", "tests": whole["tests"], "failures": whole["failures"]},
    "worker_harness_correction": {**observed_exit(BASE / "worker-gate-02/actual-completion.json", 0),
                                 "source_archive": "source-v5", "tests": worker["tests"]},
    "v6_refinement": {**observed_exit(BASE / refinement_name / "actual-completion.json", 0),
                      "source_archive": "source-v6", "tests": refinement["tests"],
                      "scope": refinement["scope"], "source_files_verified": len(refinement_pins)},
    "same_source_within_v5_worker_correction": True, "original_failure_retained": True,
    "v6_gate_is_separate_focused_evidence": True,
}
assert len(audit["gates"]) == 3
audited_gates = {gate["name"]: gate for gate in audit["gates"]}
expected_gates = {"full-gate-01": ("v5", whole, 1), "worker-gate-02": ("v5", worker, 0),
                  refinement_name: ("v6", refinement, 0)}
assert set(audited_gates) == set(expected_gates)
for name, (version, gate_result, actual_exit) in expected_gates.items():
    gate = audited_gates[name]
    assert gate["version"] == version and gate["result"] == gate_result, name
    assert gate["evidence_consistent"] is True and gate["errors"] == [], name
    assert type(gate["receipt"]["actual_exit_code"]) is int and gate["receipt"]["actual_exit_code"] == actual_exit, name

# Old gallery records retain their original bytes and version attribution.
old_gallery = previous["gallery"]
assert old_gallery["cases"] == 8
old_records = [entry for entry in old_gallery["files"] if Path(entry["path"]).name != "manifest.json"]
assert len(old_records) == 8
for entry in old_records:
    assert pin(ROOT / entry["path"]) == {key: entry[key] for key in ("bytes", "sha256")}
gallery = showcase_catalog()
assert len(gallery["cases"]) > 8
gallery_files = [pinned(APP / "showcase/manifest.json")]
for item in gallery["cases"]:
    assert item["kernel_verified"] is True and item["independent_replay"] is True
    path = APP / "showcase" / (item["id"] + ".json")
    assert pin(path)["sha256"] == item["artifact_sha256"]
    record = read(path)
    assert record["result"]["theorem"] == record["verification"]["theorem"]
    assert record["result"]["commands"] == record["verification"]["commands"]
    assert record["verification"]["kernel_checked"] is True and not record["verification"]["goals"]
    assert record["independent_replay"]["actual_child_exit_code"] == 0
    replay_pin = record["independent_replay"]["artifact"]
    replay_path = Path(replay_pin["path"])
    assert pin(replay_path) == {key: replay_pin[key] for key in ("bytes", "sha256")}
    replay = read(replay_path)
    assert replay["actual_child_exit_code"] == 0 and replay["quiescent"] is True
    gallery_files.append(pinned(path))
publication = read(BASE / "showcase-stage-01/summary.json")
assert publication["status"] == "complete" and publication["published"] is True
assert publication["new_verified_cases"] == len(gallery["cases"]) - 8
publication_exit = observed_exit(BASE / "showcase-stage-01/actual-completion.json", 0)

browser = read(BASE / "browser-advanced-01/browser-advanced.json")
assert browser["status"] == "passed" and len(browser["checks"]) == 6
assert browser["isolated_browser"] is True and browser["existing_browser_profile_used"] is False
assert not browser["page_errors"] and not browser["network_capture_errors"]
assert not browser["cleanup"]["errors"] and browser["cleanup"]["slot_released"] is True
assert browser["cleanup"]["browser_exit_confirmed"] is True
browser_exit = observed_exit(BASE / "browser-advanced-01/actual-completion.json", 0)
status = read(BASE / "final-server-status.json")
assert status["server_left_running"] is True and status["status"]["computation_active"] is False
assert "csrf_token" not in status["status"]
assert all(mode["available"] is True for mode in status["status"]["search_modes"].values())
assert status["gallery_ids"] == [item["id"] for item in gallery["cases"]]
status_exit = observed_exit(BASE / "final-server-status-actual-completion.json", 0)

result = {"schema": "hydra-progress-completion-verification-v1", "status": "verified",
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Read-only authentication and binding of completed evidence; no new model inference, solver, search or proof replay.",
    "verifier": pinned(Path(__file__)), "run_audit": {"artifact": pinned(audit_path), "execution": audit_exit,
        "planned_case_records": 16, "audited_case_records": 16, "inputs_verified": len(audited_inputs),
        "batches": [{"name": name, "version": version, "case_records": len(case_ids)}
                    for name, (version, case_ids) in expected_batches.items()],
        "paired_comparison": ["baseline-v4-01", "comparison-v5-01"]},
    "kernel": {"commit": model.SOURCE_COMMIT, "files_verified": len(catalog["files"]), "catalog": source_pin, "inputs": inputs_pin},
    "model": {"saved_manifest_sha256": model.MODEL_MANIFEST_SHA, "adapter_sha256": model.ADAPTER_SHA,
              "adapter_and_tokenizer_verified": True, "quantized_manifest": quantized_pin,
              "quantized_files_verified": len(quantized["files"]), "readiness": ready_pin,
              "training_performed": False},
    "vampire": {"runtime_policy": RUNTIME_POLICY, "manifest": vampire_manifest_pin, "executable": vampire_manifest["executable"]},
    "source_archives": archives, "tests": tests,
    "gallery": {"cases": len(gallery["cases"]), "old_records_unchanged": 8, "files": gallery_files,
                "publication": publication_exit},
    "browser": {"checks": len(browser["checks"]), "record": pinned(BASE / "browser-advanced-01/browser-advanced.json"), "execution": browser_exit},
    "final_server_observation": {"record": pinned(BASE / "final-server-status.json"), "execution": status_exit},
    "report": pinned(BASE / "RESULT.md"),
    "exit_observation": "The caller separately records the actual tool exit; this file is not an exit receipt."}
with (BASE / "verification.json").open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print(json.dumps({"status": "verified", "frozen_files_verified": len(catalog["files"]),
                  "quantized_files_verified": len(quantized["files"]), "gallery_cases": len(gallery["cases"])}))
