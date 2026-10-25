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


def observed_exit(path, expected):
    receipt = read(path)
    values = [receipt[key] for key in ("actual_exit_code", "exit_code") if key in receipt]
    assert values and all(type(value) is int and value == expected for value in values), path
    assert receipt.get("completion_chunk_id", receipt.get("completion_chunk")), path
    return {"actual_exit_code": expected, "receipt": pinned(path)}


assert not (BASE / "verification.json").exists(), "Never overwrite final verification evidence."
archives = {}
for name in ("source-v5", "source-v5-final"):
    manifest = read(BASE / name / "manifest.json")
    assert manifest["search_profile"] == "hydra-playground-hybrid-v5"
    entries = manifest["files"]
    for filename, expected in entries.items():
        relative = Path(filename)
        assert not relative.is_absolute() and ".." not in relative.parts
        assert pin(BASE / name / relative) == expected, (name, filename)
        if name == "source-v5-final":
            assert pin(APP / relative) == expected, filename
    archives[name] = {"files_verified": len(entries), "manifest": pinned(BASE / name / "manifest.json")}

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
assert not any(name in sys.modules for name in ("mlx", "mlx_lm", "torch", "transformers"))

audit_path = BASE / "final-audit-01/audit.json"
audit = read(audit_path)
audit_exit = observed_exit(BASE / "final-audit-01/actual-completion.json", 0)

# The first full-suite attempt stays failed. Only its worker subprocess tests
# were blocked by the test parent's inherited hard CPU ceiling; all ten worker
# tests passed after correcting that harness, with identical application bytes.
whole = read(BASE / "full-gate-01/result.json")
worker = read(BASE / "worker-gate-02/result.json")
assert whole == {"tests": 162, "failures": 9, "errors": 0, "skipped": 0,
    "source_pins_unchanged": True, "passed": False, "scope": whole["scope"]}
assert worker["passed"] is True and worker["tests"] == 10
assert worker["failures"] == worker["errors"] == worker["skipped"] == 0
test_pins = read(BASE / "full-gate-01/source-before.json")
assert test_pins == read(BASE / "full-gate-01/source-after.json")
assert test_pins == read(BASE / "worker-gate-02/source-before.json") == read(BASE / "worker-gate-02/source-after.json")
for filename, expected in test_pins.items():
    assert pin(APP / filename) == expected, filename
failures = re.findall(r"(?m)^FAIL: (.+)$", (BASE / "full-gate-01/output.txt").read_text())
assert len(failures) == 9 and all("(test_worker.NativeReplayTests." in value for value in failures)
assert "ValueError: not allowed to raise maximum limit" in (BASE / "full-gate-01/output.txt").read_text()
tests = {"full_suite_initial": observed_exit(BASE / "full-gate-01/actual-completion.json", 1),
         "worker_harness_correction": observed_exit(BASE / "worker-gate-02/actual-completion.json", 0),
         "same_application_and_test_source": True, "original_failure_retained": True}

# Old gallery records retain their original bytes and version attribution.
assert pin(OLD / "verification.json")["sha256"] == "f6a58ae72e4678ab4ae997aa22d911dc3231bf972cb8ae23dd51b1db0c985ed6"
old_gallery = read(OLD / "verification.json")["gallery"]
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
    "verifier": pinned(Path(__file__)), "run_audit": {"artifact": pinned(audit_path), "execution": audit_exit},
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
