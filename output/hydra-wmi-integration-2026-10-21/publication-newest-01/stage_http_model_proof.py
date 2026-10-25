"""Stage one real newest-model HTTP proof after an independent CPU replay.

No model inference is performed. Default operation writes a new staging
directory only. --publish appends the verified record and switches the manifest
last, preserving all fourteen historical proof files and entries.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import threading

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "hydra-playground"
sys.path.insert(0, str(APP))
import server
import worker
from portfolio_runtime import _validate_execution, _validate_result

MODEL_ID = "wmi-c6-long-vanilla11"
CHECKPOINT = "177501bf7b662a210b6cf6887844a282365437c781e53138ad5495f02c620a06"
EXPORT = "659f71892bacdafc7488d8b683dd8dda051dfa4b054f74ba340db4da59fd07a3"
ENVIRONMENT = "8edaaffa8edf1f6d8b187ba3ada5e87c8219374ef556031afbc103948619b69f"
SOURCE_FILES = ("server.py", "worker.py", "deployment_models.py", "search_settings.py",
                "sequential_runtime.py", "sequential_native.py", "sequential_runner.py",
                "sequential_native_sources.json", "portfolio_runtime.py")
HTTP_FILES = ("REQUEST.json", "TERMINAL_JOB.json", "SUBMITTED.json", "SUBMISSION_INTENT.json",
              "STATUS_BEFORE.json", "STATUS_AFTER.json", "SUMMARY.json", "SMOKE_CHECK.json")
TRANSITIONS = ("step", "goals_before", "focus", "tactic", "goals_after", "status", "error")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def raw_file(path, maximum=24 * 1024**2):
    require(path.is_file() and not path.is_symlink(), "Missing or linked input: " + str(path))
    before = path.stat()
    require(before.st_nlink == 1 and 0 < before.st_size <= maximum, "Input exceeds its bound")
    raw = path.read_bytes()
    after = path.stat()
    require(len(raw) == before.st_size and (before.st_mtime_ns, before.st_ctime_ns, before.st_size)
            == (after.st_mtime_ns, after.st_ctime_ns, after.st_size), "Input changed while reading")
    return raw


def pin(path):
    raw = raw_file(path)
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()


def save(path, value):
    with path.open("xb") as stream:
        stream.write(encoded(value) + b"\n")


def admit_http(records):
    """Validate saved transport evidence; never manufacture an HTTP job."""
    request = records["REQUEST.json"]
    require(worker.validate_request("search", request) == request, "Noncanonical HTTP request")
    require(request.get("model_id") == MODEL_ID and request.get("search_mode") == "portfolio"
            and request.get("search_profile") == "portfolio" and request.get("max_model_calls") == 128
            and request.get("beam_width") == 1 and "experimental" not in request, "Unexpected HTTP route")
    terminal = records["TERMINAL_JOB.json"]
    job = terminal.get("job", {})
    identifier = job.get("id")
    require(terminal.get("ok") is True and type(identifier) is str
            and re.fullmatch(r"[0-9a-f]{32}", identifier)
            and records["SUBMITTED.json"].get("ok") is True
            and records["SUBMITTED.json"].get("job_id") == identifier,
            "No matching accepted HTTP submission")
    intent, summary = records["SUBMISSION_INTENT.json"], records["SUMMARY.json"]
    require(intent.get("job_count") == 1 and intent.get("automatic_retry") is False
            and intent.get("model_inference") is True and summary.get("schema") == "hydra-portfolio-http-smoke-v1"
            and summary.get("job_id") == identifier and summary.get("state") == "completed"
            and summary.get("automatic_retry") is False and records["SMOKE_CHECK.json"].get("passed") is True,
            "Missing completed single-submission smoke evidence")
    require(job.get("state") == "completed" and job.get("error") is None, "HTTP job did not complete cleanly")
    execution, result = job.get("execution", {}), job.get("result", {})
    require(execution.get("quiescent") is True and execution.get("worker_started") is True
            and type(execution.get("elapsed_seconds")) in (int, float)
            and math.isfinite(execution["elapsed_seconds"]) and 0 <= execution["elapsed_seconds"] < 550
            and records["STATUS_AFTER.json"].get("computation_active") is False,
            "Missing bounded HTTP cleanup")
    require(result.get("execution") == execution and result.get("kind") == "portfolio"
            and result.get("original_theorem") == request["theorem"], "HTTP result binding differs")
    model, portfolio, search = result.get("model", {}), result.get("portfolio", {}), result.get("search", {})
    require(model.get("selection_id") == MODEL_ID and model.get("checkpoint_sha256") == CHECKPOINT
            and model.get("exported_adapter_sha256") == EXPORT and model.get("selected_step") == 16384,
            "Actual result uses another model")
    require(portfolio.get("selected_model_id") == MODEL_ID and portfolio.get("winner") == "sequential"
            and portfolio.get("original_theorem") == request["theorem"]
            and portfolio.get("script_combination") is False
            and portfolio.get("fallback") == {"status": "not_needed", "reason": "model_proof"},
            "Only a complete model-generated winning proof is eligible")
    phases = portfolio.get("phases")
    require(type(phases) is list and len(phases) == 1 and phases[0].get("phase") == "sequential"
            and execution.get("portfolio_phases") == phases, "Unexpected portfolio phase history")
    require(phases[0].get("request") == {**request, "search_mode": "sequential", "search_profile": "sequential"},
            "Primary worker request differs")
    validation_view = {**result, "kind": "sequential"}
    _validate_execution({**phases[0]["execution"], "result": validation_view}, "sequential")
    require(_validate_result(validation_view, "sequential", request["theorem"]), "Missing checked model proof")
    commands, provenance = result["commands"], search.get("provenance")
    require(type(search.get("model_calls")) is int and 0 < search["model_calls"] <= 128
            and result.get("model_used") is True and search.get("vampire_calls") == 0
            and result.get("proof_sources") == {"model": len(commands)}
            and type(provenance) is list and len(provenance) == len(commands)
            and all(row.get("source") == "model" and row.get("command") == command
                    for row, command in zip(provenance, commands)), "Winning model attribution differs")
    require(result.get("kernel_source_commit") == worker.SOURCE_COMMIT
            and result.get("environment_sha256") == ENVIRONMENT and result.get("classical") is False
            and all(line.split()[0] != "use" for line in commands), "Unexpected native authority")
    before = records["STATUS_BEFORE.json"].get("models", {}).get(MODEL_ID, {})
    require(before.get("available") is True and before.get("checkpoint_sha256") == CHECKPOINT
            and before.get("exported_adapter_sha256") == EXPORT, "Pre-submission model identity differs")
    return request, job, result


def validate_publication_replay(execution, original):
    require(execution.get("error") is None and execution.get("cancelled") is False
            and execution.get("quiescent") is True and execution.get("worker_started") is True
            and type(execution.get("worker_exit_code")) is int and execution["worker_exit_code"] == 0,
            "Publication replay did not exit cleanly")
    replay = execution.get("result", {})
    for key in ("theorem", "original_theorem", "commands", "goals", "proof_nodes", "kernel_source_commit", "environment_sha256",
                "classical", "tactics_requested", "tactics_applied", "engine_steps", "failed_tactics", "failed_step", "error"):
        require(replay.get(key) == original.get(key), "Publication replay differs: " + key)
    require(replay.get("kind") == "manual" and replay.get("status") == "proved" and replay.get("kernel_checked") is True
            and replay.get("model_used") is False and replay.get("proof_profile") == "sequential",
            "Missing independent native publication proof")
    old_steps = [row for row in original["trace"] if "v" in row]
    new_steps = [row for row in replay["trace"] if "v" in row]
    require(len(old_steps) == len(new_steps) == len(original["commands"])
            and all(all(old.get(k) == new.get(k) for k in TRANSITIONS)
                    for old, new in zip(old_steps, new_steps)), "Publication replay changed a proof transition")
    for key in ("qed", "theorem", "tactic_count", "proof_size"):
        require(replay["trace"][-1].get(key) == original["trace"][-1].get(key), "Publication QED differs")
    return replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http-directory", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    parser.add_argument("--terminal-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title", default="A proof generated by the newest WMI model")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode, "Use isolated Python with bytecode disabled")
    require(0 < len(args.title) <= 240, "Invalid title")
    records = {name: json.loads(raw_file(args.http_directory / name)) for name in HTTP_FILES}
    http_pins = {name: pin(args.http_directory / name) for name in HTTP_FILES}
    require(http_pins["REQUEST.json"]["sha256"] == args.request_sha256
            and http_pins["TERMINAL_JOB.json"]["sha256"] == args.terminal_sha256,
            "Actual reviewed HTTP request/result pins differ")
    request, job, result = admit_http(records)
    old = server.showcase_catalog()
    require(len(old["cases"]) == 14, "This one-record publisher expects the preserved fourteen-case gallery")
    old_raw = raw_file(server.SHOWCASE / "manifest.json", 128 * 1024)
    gallery_pins = {case["artifact_file"]: pin(server.SHOWCASE / case["artifact_file"]) for case in old["cases"]}
    code_pins = {name: pin(APP / name) for name in SOURCE_FILES}
    args.output.mkdir(parents=True, exist_ok=False)
    save(args.output / "INPUT_PINS.json", {"http": http_pins, "application": code_pins,
        "historical_gallery": gallery_pins, "historical_manifest_sha256": hashlib.sha256(old_raw).hexdigest()})
    replay_request = {"theorem": request["theorem"], "tactics": result["commands"], "proof_profile": "sequential"}
    execution = server.run_worker("replay", replay_request, threading.Event(), lambda _: None)
    save(args.output / "PUBLICATION_REPLAY.json", execution)
    replay = validate_publication_replay(execution, result)
    require(all(pin(args.http_directory / n) == p for n, p in http_pins.items())
            and all(pin(APP / n) == p for n, p in code_pins.items()), "Inputs or replay source changed")
    identifier = "wmi-long11-model-" + job["id"][:16]
    require(identifier not in {case["id"] for case in old["cases"]}, "Refusing to replace an existing gallery entry")
    now = datetime.now(timezone.utc).isoformat()
    artifact = {"schema": "hydra-showcase-proof-v1", "case_id": identifier, "theorem": request["theorem"],
        "request": request, "result": result, "verification": replay, "job_id": job["id"],
        "recorded_at_utc": None, "recorded_time_scope": "The saved HTTP response has no UTC generation timestamp.",
        "published_replay_at_utc": now, "origin": "live_http_search",
        "live_run_provenance": {"collector": "smoke_portfolio_http.py", "directory": str(args.http_directory.resolve()),
                                "files": http_pins, "automatic_retry": False, "reference_scripts_sent": False},
        "independent_replay": {"artifact": pin(args.output / "PUBLICATION_REPLAY.json"),
                               "actual_child_exit_code": execution["worker_exit_code"], "quiescent": True},
        "benchmark_claim": False, "new_mathematics_claim": False,
        "note": "One fresh theorem-only HTTP model proof, independently replayed for publication; not an accuracy benchmark."}
    raw = encoded(artifact)
    require(len(raw) <= 2 * worker.MAX_RESULT_BYTES, "Gallery artifact exceeds server bound")
    entry = {"id": identifier, "title": args.title, "display": request["theorem"],
        "description": "The newest local WMI adapter generated every winning tactic; a fresh native replay checked the complete script.",
        "theorem": request["theorem"], "canonical_theorem": result["theorem"],
        "kernel_verified": True, "independent_replay": True, "search_mode": "portfolio", "search_profile": "portfolio",
        "proof_sources": result["proof_sources"], "model_calls": result["search"]["model_calls"], "vampire_calls": 0,
        "proof_nodes": result["proof_nodes"], "proof_steps": len(result["commands"]),
        "elapsed_seconds": job["execution"]["elapsed_seconds"], "elapsed_scope": "server portfolio supervision, not client or publication replay",
        "tags": ["fresh model proof", "native checked", "exposed example"],
        "artifact_file": identifier + ".json", "artifact_sha256": hashlib.sha256(raw).hexdigest()}
    staged = args.output / "staged"
    staged.mkdir()
    with (staged / entry["artifact_file"]).open("xb") as stream:
        stream.write(raw)
    save(staged / "manifest.json", {"schema": old["schema"], "cases": [entry], "note": artifact["note"]})
    original_directory = server.SHOWCASE
    try:
        server.SHOWCASE = staged
        server.showcase_catalog()
    finally:
        server.SHOWCASE = original_directory
    summary = {"staged": True, "published": False, "case_id": identifier, "fresh_model_inference": False,
        "publication_native_replay": True, "historical_proofs_preserved": 14, "entry": entry}
    if args.publish:
        lock = original_directory / ".publish.lock"
        with lock.open("x"):
            try:
                require(raw_file(original_directory / "manifest.json") == old_raw
                        and all(pin(original_directory / n) == p for n, p in gallery_pins.items()),
                        "Historical gallery changed during staging")
                with (args.output / "previous-manifest.json").open("xb") as stream:
                    stream.write(old_raw)
                with (original_directory / entry["artifact_file"]).open("xb") as stream:
                    stream.write(raw)
                pending = original_directory / "manifest.newest.pending"
                save(pending, {**old, "cases": old["cases"] + [entry]})
                os.replace(pending, original_directory / "manifest.json")
                final = server.showcase_catalog()
                require(final["cases"][:14] == old["cases"] and len(final["cases"]) == 15
                        and all(pin(original_directory / n) == p for n, p in gallery_pins.items()),
                        "Historical evidence changed during publication")
                summary.update(published=True, manifest=pin(original_directory / "manifest.json"))
            finally:
                lock.unlink()
    save(args.output / "SUMMARY.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
