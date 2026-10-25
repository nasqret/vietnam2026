#!/usr/bin/env python3
"""Stage independently replayed proofs from finalized live HTTP experiments.

Default: write a fresh staging directory only. --publish additionally appends
the verified records to the local app showcase after every check succeeds.
Reference audits, manual proofs, running jobs and unverified results are never
eligible. This is a curator for exposed classical probes, not a benchmark.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time

APP = Path(__file__).resolve().parent
ROOT = APP.parent
sys.path.insert(0, str(APP))
import worker
import evaluate_advanced as experiments
from evaluate_hybrid import BoundaryError, StopRequested, descriptor, require, utc_now, write_json

MAX_INPUTS = 24
MAX_TOTAL_SECONDS = 3600
MAX_REPLAY_SECONDS = 120
MAX_RECORD_BYTES = 2 * worker.MAX_RESULT_BYTES
NOTE = ("Selected, exposed classical arithmetic examples from completed local searches. "
        "Every displayed script passed a fresh independent Peano-kernel replay. "
        "Step sources and advisor calls are reported separately; no unseen-accuracy or new-mathematics claim.")


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()


def read_record(path, maximum=4 * worker.MAX_RESULT_BYTES):
    return experiments.pinned_json(path, maximum)


def matches_pin(path, pin):
    return type(pin) is dict and descriptor(path) == {key: pin.get(key) for key in ("bytes", "sha256")}


def inspect_live_record(path, validate_statement):
    """Bind a proof candidate to a finalized, single-submission HTTP run."""
    record, record_pin = read_record(path)
    require(record.get("schema") == experiments.CASE_SCHEMA and record.get("origin") == "live_http_search",
            "Only evaluate_advanced live HTTP case records are eligible; reference/manual audits are forbidden.")
    require(record.get("record_file") == path.name, "Case record filename changed.")
    plan, plan_pin = read_record(path.parent / "plan.json")
    summary, summary_pin = read_record(path.parent / "summary.json")
    pins, pins_pin = read_record(path.parent / "source-pins.json")
    context = record.get("run_context", {})
    require(plan.get("schema") == experiments.PLAN_SCHEMA and plan.get("origin") == "live_http_search"
            and summary.get("schema") == experiments.SUMMARY_SCHEMA,
            "Missing matching HTTP run plan/summary.")
    require(summary.get("status") in {"complete", "incomplete"}
            and summary.get("source_pins_unchanged") is True
            and matches_pin(path, summary.get("case_file_pins", {}).get(path.name)),
            "Live run is not finalized with unchanged source and an exact case-file hash.")
    require(context.get("plan_sha256") == plan_pin["sha256"]
            and context.get("source_pins_sha256") == pins_pin["sha256"]
            and matches_pin(path.parent / "source-pins.json", plan.get("source_pins"))
            and pins.get("kernel_commit") == worker.SOURCE_COMMIT,
            "Run/source provenance hashes do not match.")
    require(record.get("automatic_retry") is False and record.get("reference_scripts_sent_to_server") is False
            and plan.get("reference_scripts_sent_to_server") is False,
            "Record is not bound to theorem-only, no-retry search.")
    request = record.get("request")
    normalized = worker.validate_request("search", request)
    canonical = validate_statement(normalized["theorem"])
    require(record.get("normalized_request") == normalized and record.get("canonical_theorem") == canonical,
            "Recorded request normalization/canonical theorem differs.")
    require(any(job.get("case_id") == record.get("case_id") and job.get("mode") == normalized["search_mode"]
                and job.get("request") == request and job.get("canonical_theorem") == canonical
                for job in plan.get("jobs", [])), "Case/request is absent from the immutable run plan.")
    require(record.get("search_mode") == normalized["search_mode"]
            and record.get("search_profile") == normalized["search_profile"], "Mode/profile mismatch.")
    provenance = {"case_record": record_pin, "plan": plan_pin, "summary": summary_pin, "source_pins": pins_pin,
                  "run_status": summary["status"], "recorded_source_pins": pins}
    if record.get("expected") != "provable" or record.get("outcome") != "proved":
        return {"eligible": False, "reason": "Not a positive completed proof record.",
                "record": record, "provenance": provenance}
    identifier = record.get("job_id")
    submission = record.get("submission_response", {})
    job = record.get("last_job", {})
    result = job.get("result")
    require(type(identifier) is str and re.fullmatch(r"[0-9a-f]{32}", identifier)
            and record.get("submission_count") == 1 and record.get("submission_http_status") == 202
            and submission.get("ok") is True and submission.get("job_id") == identifier,
            "Proof has no single accepted owned HTTP submission.")
    require(job.get("id") == identifier and job.get("state") == "completed" and job.get("error") is None
            and type(result) is dict and result.get("execution", {}).get("quiescent") is True,
            "The owned HTTP job did not finish with confirmed worker cleanup.")
    require(result.get("status") == "proved" and result.get("kernel_checked") is True
            and result.get("theorem") == canonical and result.get("goals") == []
            and type(result.get("proof_nodes")) is int and result["proof_nodes"] > 0
            and result.get("kind") == normalized["search_mode"]
            and result.get("settings_profile", "standard") == normalized["search_profile"],
            "Live proof claim/theorem/mode/profile is inconsistent.")
    commands = result.get("commands")
    require(type(commands) is list and 0 < len(commands) <= worker.LIMITS["tactics"],
            "Missing or oversized full returned proof script.")
    replay_request = worker.validate_request("replay", {"theorem": request["theorem"], "tactics": commands})
    require(replay_request["tactics"] == commands, "Returned proof commands are not canonical tactic lines.")
    require(type(record.get("submitted_at_utc")) is str and type(record.get("finished_at_utc")) is str,
            "Missing live run timestamps.")
    return {"eligible": True, "record": record, "result": result, "request": request,
            "normalized": normalized, "canonical": canonical, "provenance": provenance,
            "replay_request": replay_request}


def native_child():
    """Fresh offline interpreter, full returned script, frozen kernel only."""
    require(sys.flags.isolated and sys.dont_write_bytecode, "Use isolated Python with bytecode disabled.")
    payload = worker.decode_json(sys.stdin.buffer.read(worker.MAX_BODY_BYTES + 1))
    wall = payload.get("wall_seconds")
    require(type(wall) in (int, float) and math.isfinite(wall) and 1 <= wall <= MAX_REPLAY_SECONDS,
            "Invalid replay wall bound.")
    request = worker.validate_request("replay", payload.get("request"))
    resource.setrlimit(resource.RLIMIT_CPU, (math.ceil(wall), math.ceil(wall)))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    def timeout(_signum, _frame):
        raise TimeoutError("Independent replay wall limit reached.")
    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, wall)
    started = time.monotonic()
    worker.install_guard("replay")
    result = worker.replay(request)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    require(rss <= worker.LIMITS["manual"]["rss_bytes"], "Independent replay exceeded the peak RSS bound.")
    output = {"result": result, "native_seconds": round(time.monotonic()-started, 6),
              "peak_rss_bytes": rss, "kernel_commit": worker.SOURCE_COMMIT,
              "model_calls": 0, "vampire_calls": 0, "network_calls": 0}
    raw = json_bytes(output)
    require(len(raw) <= MAX_RECORD_BYTES, "Independent replay output exceeds its bound.")
    sys.stdout.buffer.write(raw + b"\n")
    return 0


def run_replay(request, deadline):
    import server
    wall = min(MAX_REPLAY_SECONDS, deadline-time.monotonic()-4)
    require(wall >= 1, "Global replay budget exhausted.")
    server.process_snapshot()  # Fail closed before starting native work if accounting is unavailable.
    started = time.monotonic()
    process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--native-child"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        cwd=APP, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    payload = json_bytes({"request": request, "wall_seconds": wall})
    result = {"actual_child_pid": process.pid, "wall_limit_seconds": wall, "automatic_retry": False,
              "rss_limit_bytes": worker.LIMITS["manual"]["rss_bytes"],
              "rss_measurement": "Parent samples the owned process group every approximately 0.1s; not an instantaneous hard cap.",
              "peak_sampled_rss_bytes": 0, "quiescent": False}
    stdout, stderr = b"", b""
    known = {}
    next_notice = started + 15
    try:
        while True:
            remaining = min(started+wall+2, deadline)-time.monotonic()
            if remaining <= 0:
                result["parent_timeout"] = True
                process.kill()  # This exact unreaped child only; the guard forbids descendants.
                stdout, stderr = process.communicate(timeout=2)
                break
            rows = server.process_snapshot()
            owned = server.owned_processes(rows, process.pid, known, unreaped=process.returncode is None)
            known.update(owned)
            rss = sum(rows[pid][2] for pid in owned if pid in rows)
            result["peak_sampled_rss_bytes"] = max(result["peak_sampled_rss_bytes"], rss)
            if set(owned) - {process.pid}:
                result["supervision_error"] = "Independent native replay attempted an unauthorized child process."
                server._kill(process, known)
                stdout, stderr = process.communicate(timeout=2)
                break
            if rss > result["rss_limit_bytes"]:
                result["supervision_error"] = "Independent replay exceeded the sampled 2 GiB RSS limit."
                server._kill(process, known)
                stdout, stderr = process.communicate(timeout=2)
                break
            try:
                stdout, stderr = process.communicate(input=payload, timeout=min(0.1, remaining))
                break
            except subprocess.TimeoutExpired:
                payload = None
                if time.monotonic() >= next_notice:
                    print("Independent replay: " + str(round(time.monotonic()-started)) + "s", flush=True)
                    next_notice = time.monotonic() + 15
    except StopRequested as failure:
        result.update(interrupted=True, error=str(failure))
    except (OSError, RuntimeError, subprocess.SubprocessError) as failure:
        result["supervision_error"] = str(failure)
    finally:
        if process.poll() is None:
            try:
                server._kill(process, known)
            except (OSError, RuntimeError, subprocess.SubprocessError) as failure:
                result["supervision_error"] = "Owned replay cleanup failed: " + str(failure)
            stdout, stderr = process.communicate(timeout=2)
        result.update(actual_child_exit_code=process.returncode,
                      child_wall_seconds=round(time.monotonic()-started, 6))
        try:
            rows = server.process_snapshot()
            remaining_owned = server.owned_processes(rows, process.pid, known)
            if remaining_owned:
                server._kill(process, known)
                rows = server.process_snapshot()
            result["quiescent"] = server.group_is_empty(rows, process.pid)
            if not result["quiescent"]:
                result["supervision_error"] = "Native replay process group did not quiesce."
        except (OSError, RuntimeError, subprocess.SubprocessError) as failure:
            result["supervision_error"] = "Replay cleanup could not be confirmed: " + str(failure)
    require(len(stdout) <= MAX_RECORD_BYTES and len(stderr) <= 64 * 1024, "Replay process output exceeded its bound.")
    result["stderr"] = stderr.decode("utf-8", errors="replace")
    if process.returncode == 0:
        decoded = json.loads(stdout)
        require(type(decoded) is dict, "Replay child returned no JSON object.")
        result.update(decoded)
    else:
        result["stdout"] = stdout.decode("utf-8", errors="replace")
    return result


def proof_sources(result):
    """Verify step-level attribution; preserve missing original-model attribution."""
    commands = result["commands"]
    search = result.get("search", {})
    provenance = search.get("provenance")
    if provenance is None and result.get("kind") == "model" and result.get("proof_sources") is None:
        return {"unattributed": len(commands)}, ["Original model-only search has no step-level provenance; all steps remain unattributed."]
    require(type(provenance) is list and len(provenance) == len(commands)
            and all(type(item) is dict and item.get("command") == command
                    and item.get("source") in {"model", "heuristic", "vampire"}
                    for item, command in zip(provenance, commands)),
            "Winning-path command provenance is missing or inconsistent.")
    counts = dict(Counter(item["source"] for item in provenance))
    require(counts == result.get("proof_sources"), "Step-source counts disagree with the winning path.")
    return counts, []


def read_curation(path):
    """Editorial fields only; no proof, request, timing, or counter overrides."""
    if path is None:
        return {}, None
    value, pin = read_record(path, 256 * 1024)
    require(set(value) == {"schema", "cases"} and value["schema"] == "hydra-showcase-curation-v1"
            and type(value["cases"]) is dict and len(value["cases"]) <= 100,
            "Curation must be {schema: hydra-showcase-curation-v1, cases: {curriculum_case_id: editorial_fields}}.")
    limits = {"title": 240, "display": 1024, "description": 1200}
    for identifier, fields in value["cases"].items():
        require(type(identifier) is str and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", identifier)
                and type(fields) is dict and set(fields) <= set(limits) | {"tags"},
                "Curation may override only title, display, description and tags.")
        for name, maximum in limits.items():
            if name in fields:
                require(type(fields[name]) is str and 0 < len(fields[name]) <= maximum,
                        "Invalid curation " + name + ".")
        if "tags" in fields:
            require(type(fields["tags"]) is list and len(fields["tags"]) <= 8
                    and all(type(tag) is str and 0 < len(tag) <= 48 for tag in fields["tags"]),
                    "Curation tags must be at most eight short strings.")
    return value["cases"], pin


def make_entry(candidate, replay, replay_pin, curation=None, curation_pin=None):
    source = candidate["record"]
    original = candidate["result"]
    verification = replay.get("result", {})
    require(replay.get("actual_child_exit_code") == 0 and replay.get("quiescent") is True
            and not replay.get("supervision_error") and verification.get("status") == "proved"
            and verification.get("kernel_checked") is True and verification.get("goals") == []
            and verification.get("theorem") == candidate["canonical"]
            and verification.get("commands") == original["commands"]
            and verification.get("proof_nodes") == original["proof_nodes"]
            and verification.get("kernel_source_commit") == worker.SOURCE_COMMIT,
            "Fresh independent replay does not verify the complete returned script and exact proof claim.")
    result = deepcopy(original)
    sources, notes = proof_sources(result)
    if result.get("proof_sources") is None:
        result["proof_sources"] = sources
    if result.get("kernel_source_commit") is None and result.get("kind") == "model":
        require(result.get("model", {}).get("kernel_source_commit") == worker.SOURCE_COMMIT,
                "Original model identity has no matching frozen kernel commit.")
        result["kernel_source_commit"] = worker.SOURCE_COMMIT
        notes.append("Top-level kernel commit copied from matching original model identity and independent replay.")
    require(result.get("kernel_source_commit") == worker.SOURCE_COMMIT, "Saved result names a different kernel.")
    search = result.get("search")
    require(type(search) is dict, "Saved result lacks search counters.")
    for key in ("model_calls", "vampire_calls"):
        value = search.get(key)
        require(value is None or type(value) is int and value >= 0, "Invalid actual advisor counter.")
    metadata = source.get("case_metadata", {})
    mode, profile = candidate["normalized"]["search_mode"], candidate["normalized"]["search_profile"]
    identifier = source["case_id"][:48] + "-" + mode + "-" + profile + "-" + source["job_id"][:8]
    require(re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", identifier), "Showcase ID exceeds its bound.")
    elapsed = source.get("server_elapsed_seconds")
    require(type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0,
            "Missing server elapsed time; client/replay time is not a substitute.")
    artifact = {"schema": "hydra-showcase-proof-v1", "case_id": identifier,
        "curriculum_case_id": source["case_id"], "theorem": candidate["request"]["theorem"],
        "request": candidate["request"], "result": result, "verification": verification,
        "recorded_at_utc": source["finished_at_utc"], "published_replay_at_utc": utc_now(),
        "job_id": source["job_id"], "live_run_provenance": candidate["provenance"],
        "independent_replay": {"artifact": replay_pin, "actual_child_exit_code": replay["actual_child_exit_code"],
                               "native_seconds": replay.get("native_seconds")},
        "display_adaptations": notes, "benchmark_claim": False, "new_mathematics_claim": False,
        "curation": {"file": curation_pin, "applied_fields": (curation or {}).get(source["case_id"], {})},
        "counter_scope": "Actual saved counters; missing values remain null, never inferred as zero.",
        "note": NOTE}
    entry = {"id": identifier, "title": str(metadata.get("title", source["case_id"]))[:240],
        "display": str(metadata.get("math", candidate["request"]["theorem"]))[:1024],
        "description": str(metadata.get("interest", "A completed theorem-only local search with an independent native replay."))[:1200],
        "theorem": candidate["request"]["theorem"], "canonical_theorem": candidate["canonical"],
        "kernel_verified": True, "independent_replay": True,
        "search_mode": mode, "search_profile": profile, "proof_sources": sources,
        "model_calls": search.get("model_calls"), "vampire_calls": search.get("vampire_calls"),
        "proof_nodes": result["proof_nodes"], "proof_steps": len(result["commands"]),
        "elapsed_seconds": elapsed, "elapsed_scope": "server HTTP job, not client or independent replay",
        "tags": [mode, profile, "classical arithmetic", "exposed probe"],
        "artifact_file": identifier + ".json"}
    overrides = (curation or {}).get(source["case_id"], {})
    require(type(overrides) is dict and set(overrides) <= {"title", "display", "description", "tags"},
            "Curation cannot override proof/request/counter fields.")
    entry.update(overrides)
    entry["tags"] = list(dict.fromkeys(entry["tags"] + [mode, profile, "exposed probe"]))
    raw = json_bytes(artifact)
    require(len(raw) <= MAX_RECORD_BYTES, "Showcase record exceeds the server limit.")
    entry["artifact_sha256"] = hashlib.sha256(raw).hexdigest()
    return entry, artifact, raw


def validate_staged(directory):
    import server
    previous = server.SHOWCASE
    try:
        server.SHOWCASE = directory
        return server.showcase_catalog()
    finally:
        server.SHOWCASE = previous


def publish(staged, output):
    """Append without overwriting existing proof records; manifest switches last."""
    import server
    destination = APP / "showcase"
    require(destination.is_dir() and not destination.is_symlink(), "App showcase directory is unavailable.")
    lock = destination / ".publish.lock"
    with lock.open("x") as stream:
        stream.write(str(os.getpid()))
    try:
        old_manifest, _ = read_record(destination / "manifest.json", 128 * 1024)
        old = validate_staged(destination)
        new = validate_staged(staged)
        by_id = {case["id"]: case for case in old["cases"]}
        for case in new["cases"]:
            require(case["id"] not in by_id or by_id[case["id"]] == case, "Refusing to replace an existing showcase proof.")
            by_id[case["id"]] = case
        require(len(by_id) <= MAX_INPUTS, "Merged showcase exceeds the 24-case bound.")
        manifest = {"schema": "hydra-verified-showcase-v1", "cases": list(by_id.values()), "note": NOTE}
        require(len(json_bytes(manifest)) <= 128 * 1024, "Merged manifest exceeds the server limit.")
        write_json(output / "previous-manifest.json", old_manifest)
        for case in new["cases"]:
            target = destination / case["artifact_file"]
            raw = (staged / case["artifact_file"]).read_bytes()
            require(hashlib.sha256(raw).hexdigest() == case["artifact_sha256"], "Staged artifact changed.")
            if target.exists():
                require(target.is_file() and not target.is_symlink() and target.stat().st_nlink == 1
                        and target.read_bytes() == raw,
                        "Refusing to replace an existing artifact.")
            else:
                with target.open("xb") as stream:
                    stream.write(raw)
        # A failed earlier copy can leave only unreferenced files, never badges.
        temporary = destination / "manifest.json.pending"
        with temporary.open("xb") as stream:
            stream.write(json_bytes(manifest))
        os.replace(temporary, destination / "manifest.json")
        validate_staged(destination)
        return {"published": True, "manifest": descriptor(destination / "manifest.json"),
                "new_verified_cases": len(new["cases"]), "total_cases": len(manifest["cases"])}
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--native-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--records", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, help="Fresh staging/evidence directory; never the app showcase.")
    parser.add_argument("--curation", type=Path, help="Optional editorial-only JSON keyed by curriculum_case_id.")
    parser.add_argument("--total-seconds", type=float, default=1200)
    parser.add_argument("--publish", action="store_true", help="Explicitly append verified staged results to the local app showcase.")
    args = parser.parse_args()
    if args.native_child:
        return native_child()
    require(args.records and 1 <= len(args.records) <= MAX_INPUTS and args.output is not None,
            "Supply 1 to 24 actual live case records and a fresh output directory.")
    require(math.isfinite(args.total_seconds) and 10 <= args.total_seconds <= MAX_TOTAL_SECONDS,
            "Publisher global wall bound must be between 10 and 3600 seconds.")
    paths = [path.resolve() for path in args.records]
    require(len(set(paths)) == len(paths), "Repeated live case record.")
    output = args.output.resolve()
    require(output != APP / "showcase" and APP / "showcase" not in output.parents,
            "Stage outside the live showcase directory.")
    output.mkdir(parents=True, exist_ok=False)
    staged, evidence = output / "showcase", output / "replays"
    staged.mkdir()
    evidence.mkdir()
    started = time.monotonic()
    deadline = started + args.total_seconds
    summary = {"schema": "hydra-showcase-publication-v1", "status": "running", "published": False,
        "started_at_utc": utc_now(), "publisher": descriptor(Path(__file__)),
        "source_record_paths": [str(path) for path in paths], "records": [],
        "publish_requested": args.publish, "model_calls": 0, "vampire_calls": 0,
        "native_replay_processes": 0, "benchmark_claim": False, "note": NOTE}
    write_json(output / "summary.json", summary)
    entries, failures = [], []
    def stop(signum, _frame):
        raise StopRequested("Publisher stopped by signal " + str(signum))
    previous = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        curation, curation_pin = read_curation(args.curation.resolve() if args.curation else None)
        summary["curation"] = curation_pin
        # Authenticate the complete frozen native tree without replaying library targets.
        from verify_hybrid_cases import source_check
        summary["kernel_source"] = source_check()
        validate_statement, *_ = worker.load_kernel()
        for index, path in enumerate(paths):
            item = {"path": str(path), "status": "checking"}
            summary["records"].append(item)
            try:
                require(time.monotonic() < deadline-4, "Publisher global deadline reached.")
                candidate = inspect_live_record(path, validate_statement)
                item["source_pin"] = candidate["provenance"]["case_record"]
                if not candidate["eligible"]:
                    item.update(status="not_eligible", reason=candidate["reason"])
                    continue
                summary["native_replay_processes"] += 1
                replay = run_replay(candidate["replay_request"], deadline)
                replay_path = evidence / (str(index).zfill(3) + "-native-replay.json")
                write_json(replay_path, replay)
                replay_pin = {"path": str(replay_path), **descriptor(replay_path)}
                item.update(replay=replay_pin, actual_child_exit_code=replay["actual_child_exit_code"])
                if replay.get("interrupted"):
                    item["status"] = "interrupted"
                    raise StopRequested(replay.get("error", "Interrupted independent replay."))
                entry, artifact, raw = make_entry(candidate, replay, replay_pin, curation, curation_pin)
                with (staged / entry["artifact_file"]).open("xb") as stream:
                    stream.write(raw)
                entries.append(entry)
                item.update(status="verified", showcase_id=entry["id"], replay=replay_pin,
                            actual_child_exit_code=replay["actual_child_exit_code"], proof_nodes=entry["proof_nodes"])
                print(path.name + ": independently verified, " + str(entry["proof_nodes"]) + " nodes", flush=True)
            except (BoundaryError, OSError, ValueError, RuntimeError, KeyError, TypeError, AttributeError,
                    subprocess.SubprocessError) as failure:
                item.update(status="rejected", error=str(failure))
                failures.append(str(path) + ": " + str(failure))
            finally:
                write_json(output / "summary.json", summary)
        manifest = {"schema": "hydra-verified-showcase-v1", "cases": entries, "note": NOTE}
        require(len(json_bytes(manifest)) <= 128 * 1024, "Staged manifest exceeds its server bound.")
        with (staged / "manifest.json").open("xb") as stream:
            stream.write(json_bytes(manifest))
        validate_staged(staged)
        require(curation_pin is None or matches_pin(Path(curation_pin["path"]), curation_pin),
                "Editorial curation file changed during independent replay.")
        summary["staged_manifest"] = {"path": str(staged / "manifest.json"), **descriptor(staged / "manifest.json")}
        if args.publish:
            require(not failures and entries, "Publication requires at least one verified proof and no rejected input/replay.")
            summary.update(publish(staged, output))
        summary["status"] = "complete" if not failures else "incomplete"
    except (StopRequested, BoundaryError, OSError, ValueError, RuntimeError, KeyError, TypeError, AttributeError,
            subprocess.SubprocessError) as failure:
        failures.append(str(failure))
        summary["status"] = "incomplete"
    finally:
        summary.update(finished_at_utc=utc_now(), elapsed_seconds=round(time.monotonic()-started, 6),
                       failures=failures, verified_cases=len(entries),
                       exit_observation="Caller must observe the actual outer CLI exit; child exits are recorded in replay evidence.")
        write_json(output / "summary.json", summary)
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    print(str(output / "summary.json") + ": " + summary["status"], flush=True)
    return 0 if summary["status"] == "complete" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BoundaryError, OSError, ValueError, TimeoutError) as failure:
        print(str(failure), file=sys.stderr)
        raise SystemExit(2)
