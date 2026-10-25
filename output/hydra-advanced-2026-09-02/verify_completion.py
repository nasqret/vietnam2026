"""Read-only evidence audit; no proof search, model inference, or solver call.

Run after experiments and the final source snapshot are complete. This hashes
the retained receipts and authenticates model/kernel/package bytes; it does not
replace the recorded independent proof replays or actual tool exit observations.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import resource
import signal
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
APP = ROOT / "hydra-playground"
sys.path.insert(0, str(APP))
assert sys.flags.isolated and sys.dont_write_bytecode
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(180)


def read(path):
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


assert not (BASE / "verification.json").exists(), "Use a new audit path; do not overwrite evidence."
final_source = read(BASE / "source-v4-final/manifest.json")["files"]
for filename, expected in final_source.items():
    relative = Path(filename)
    assert not relative.is_absolute() and ".." not in relative.parts
    assert pin(APP / relative) == {key: expected[key] for key in ("bytes", "sha256")}, filename
import model_runtime as model
from vampire_process import package
from vampire_limits import RUNTIME_POLICY, solver_limits
from server import showcase_catalog

assert RUNTIME_POLICY == "hydra-playground-vampire-runtime-policy-v3"
assert pin(APP / "model_runtime.py")["sha256"] == "3d15371e9c5dd679fe6bea91d1d06df14ffaaba1f0e748c84266c21958a38bc5"
candidate, handle, source_pin, inputs_pin = model._load_authenticated()
artifacts = model._artifact_snapshot(handle)
quantized, quantized_pin, ready_pin = model._quantized_snapshot()
_, vampire_manifest, vampire_manifest_pin = package(verify_binary=True)
assert vampire_manifest_pin["sha256"] == "b553a839e49fe8f6e4881d124edc0ad7ee8f241403476339d8f4d07213a2151f"
assert vampire_manifest["executable"]["sha256"] == "b5168c690e0293cdac78f16d8418d7eeabcd6708f90a60cd2bf45313b6d98699"
catalog = read(model.SOURCE_CATALOG)
assert len(catalog["files"]) == 896
assert not any(name in sys.modules for name in ("mlx", "mlx_lm", "torch", "transformers"))

run_names = ("deep-hybrid-01", "standard-comparison-01", "deep-hybrid-v4-01",
             "research-hybrid-01", "negative-controls-01", "model-control-01",
             "vampire-watchdog-control-01", "research-hybrid-02")
runs, case_count = {}, 0
for name in run_names:
    directory = BASE / name
    plan, summary = read(directory / "plan.json"), read(directory / "summary.json")
    before, after = read(directory / "source-pins.json"), read(directory / "source-pins-after.json")
    receipt = read(directory / "actual-completion.json")
    assert before == after and summary["source_pins_unchanged"] is True, name
    assert plan["source_pins"] == {"file": "source-pins.json", **pin(directory / "source-pins.json")}, name
    assert summary["recorded_jobs"] == len(summary["case_files"]) == summary["requested_jobs"], name
    assert len(plan["jobs"]) == summary["requested_jobs"], name
    assert receipt["actual_exit_code"] == (2 if name == "research-hybrid-01" else 0), name
    assert summary["status"] == ("incomplete" if name == "research-hybrid-01" else "complete"), name
    assert summary["all_requested_cases_completed"] is (name != "research-hybrid-01"), name
    curriculum = plan["curriculum"]
    assert pin(Path(curriculum["path"])) == {key: curriculum[key] for key in ("bytes", "sha256")}, name
    details = []
    for index, filename in enumerate(summary["case_files"]):
        path = directory / filename
        assert path.parent == directory and path.name == filename
        assert pin(path) == summary["case_file_pins"][filename], path
        case = read(path)
        planned = plan["jobs"][index]
        assert case["case_id"] == planned["case_id"] and case["search_mode"] == planned["mode"], path
        for key in ("request", "normalized_request", "canonical_theorem"):
            assert case[key] == planned[key], (path, key)
        assert case["run_context"] == {"plan_sha256": pin(directory / "plan.json")["sha256"],
                                       "source_pins_sha256": pin(directory / "source-pins.json")["sha256"]}, path
        assert case["submission_count"] == 1 and case["automatic_retry"] is False, path
        assert case["reference_scripts_sent_to_server"] is False, path
        job = case["last_job"]
        assert job["id"] == case["job_id"] == case["submission_response"]["job_id"], path
        if name == "research-hybrid-01":
            assert job["state"] == "failed" and case["outcome"] == "server_failure" and job["result"] is None, path
        else:
            assert job["state"] == "completed" and job["error"] is None, path
            assert job["result"]["execution"]["quiescent"] is True, path
            execution = job["result"]["execution"]
            # Old v3 jobs did not expose the worker exit field. Do not invent
            # it retrospectively; their terminal protocol and quiescence are retained.
            if "worker_exit_code" in execution:
                assert execution["worker_started"] is True and execution["worker_exit_code"] == 0, path
        if job.get("result") is not None:
            assert job["result"]["theorem"] == case["canonical_theorem"], path
        if case["outcome"] == "proved":
            result = case["last_job"]["result"]
            assert case["kernel_verified"] is True and result["kernel_checked"] is True, path
            assert result["status"] == "proved" and not result["goals"], path
            assert result["execution"]["quiescent"] is True, path
        else:
            assert case["kernel_verified"] is False, path
        if case["expected"] == "not_provable":
            assert case["outcome"] != "proved", path
        details.append({"case_id": case["case_id"], "outcome": case["outcome"],
                        "proof_steps": case.get("proof_steps"), "proof_nodes": case.get("proof_nodes"),
                        "metrics": case.get("metrics"), "file": pinned(path)})
        case_count += 1
    runs[name] = {"status": summary["status"], "actual_exit_code": receipt["actual_exit_code"],
                  "source_pins_unchanged": True, "cases": details,
                  "plan": pinned(directory / "plan.json"), "summary": pinned(directory / "summary.json"),
                  "actual_completion": pinned(directory / "actual-completion.json")}

archives, archive_entries = {}, {}
for name in ("source-v3", "source-v4", "source-v4-memory-v2", "source-v4-final"):
    manifest = read(BASE / name / "manifest.json")
    entries = manifest.get("files", manifest.get("source_pins"))
    assert isinstance(entries, dict) and entries
    for filename, expected in entries.items():
        assert pin(BASE / name / filename) == {key: expected[key] for key in ("bytes", "sha256")}, (name, filename)
    archives[name] = {"files_verified": len(entries), "manifest": pinned(BASE / name / "manifest.json")}
    archive_entries[name] = entries

run_archives = {"deep-hybrid-01": "source-v3", "standard-comparison-01": "source-v3",
                "deep-hybrid-v4-01": "source-v4", "research-hybrid-01": "source-v4",
                "negative-controls-01": "source-v4-memory-v2", "model-control-01": "source-v4-memory-v2",
                "vampire-watchdog-control-01": "source-v4-final", "research-hybrid-02": "source-v4-final"}
for name, archive in run_archives.items():
    application = read(BASE / name / "source-pins.json")["application"]
    for filename, expected in application.items():
        assert filename in archive_entries[archive], (name, filename)
        assert {key: expected[key] for key in ("bytes", "sha256")} == {
            key: archive_entries[archive][filename][key] for key in ("bytes", "sha256")}, (name, filename)
    runs[name].update(source_archive=archive, archived_application_files=len(application))

gallery = showcase_catalog()
assert gallery["schema"] == "hydra-verified-showcase-v1" and len(gallery["cases"]) == 8
gallery_files = [pinned(APP / "showcase/manifest.json")]
for item in gallery["cases"]:
    assert item["kernel_verified"] is True and item["independent_replay"] is True
    record = APP / "showcase" / (item["id"] + ".json")
    assert pin(record)["sha256"] == item["artifact_sha256"]
    gallery_files.append(pinned(record))

receipt_groups = ("integration-tests-01", "integration-tests-v4", "final-focused-tests-01",
                  "watchdog-integration-tests-01", "showcase-stage-01", "showcase-stage-v4",
                  "browser-advanced-01", "browser-advanced-02", "research-vampire-memory-v2-01",
                  "research-vampire-memory-v3-01")
receipts = {name: {"record": read(BASE / name / "actual-completion.json"),
                   "file": pinned(BASE / name / "actual-completion.json")} for name in receipt_groups}
assert receipts["browser-advanced-01"]["record"]["actual_exit_code"] == 1
assert receipts["research-vampire-memory-v2-01"]["record"]["actual_exit_code"] == 2
assert all(value["record"]["actual_exit_code"] == 0 for name, value in receipts.items()
           if name not in {"browser-advanced-01", "research-vampire-memory-v2-01"})

server_status = read(BASE / "final-server-status.json")
server_receipt = read(BASE / "final-server-status-actual-completion.json")
assert server_status["server_left_running"] is True
assert server_status["status"]["computation_active"] is False
assert "csrf_token" not in server_status["status"]
assert all(mode["available"] is True for mode in server_status["status"]["search_modes"].values())
assert server_status["gallery_ids"] == [item["id"] for item in gallery["cases"]]
assert server_receipt["actual_exit_code"] == 0

result = {"schema": "hydra-advanced-completion-verification-v1", "status": "verified",
          "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
          "scope": "Artifact hashes, retained exit observations, full frozen source and model authentication; no new inference, proof search, solver, or proof replay.",
          "verifier": pinned(Path(__file__)), "case_files_verified": case_count,
          "kernel": {"commit": model.SOURCE_COMMIT, "files_verified": len(catalog["files"]),
                     "catalog": source_pin, "inputs": inputs_pin},
          "saved_model": {"manifest_sha256": model.MODEL_MANIFEST_SHA, "adapter_sha256": model.ADAPTER_SHA,
                          "adapter_and_tokenizer_verified": True, "quantized_manifest": quantized_pin,
                          "quantized_files_verified": len(quantized["files"]), "readiness": ready_pin,
                          "model_runtime": pinned(APP / "model_runtime.py"), "training_performed": False},
          "vampire": {"runtime_policy": RUNTIME_POLICY, "package_manifest": vampire_manifest_pin,
                      "binary": vampire_manifest["executable"], "research_limits": solver_limits("research")},
          "runs": runs, "source_archives": archives, "gallery": {"cases": len(gallery["cases"]), "files": gallery_files},
          "final_server_observation": {"status": pinned(BASE / "final-server-status.json"),
                                       "actual_completion": pinned(BASE / "final-server-status-actual-completion.json")},
          "retained_receipts": receipts, "report": pinned(BASE / "RESULT.md"),
          "exit_observation": "The caller must separately record this verifier's actual tool exit; this written file is not an exit receipt."}
with (BASE / "verification.json").open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print(json.dumps({"status": "verified", "case_files_verified": case_count,
                  "frozen_files_verified": len(catalog["files"]), "gallery_cases": len(gallery["cases"]),
                  "quantized_files_verified": len(quantized["files"]), "output": str(BASE / "verification.json")}))
