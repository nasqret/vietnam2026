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
EXTRA_SOURCES = frozenset({"sympy", "cvc5", "egg", "e"})
EXPERIMENTAL_OPTIONS = frozenset({"engine", "lemmas", "planner", "ranker", "advisers"})
REPLAY_SOURCE_FILES = ("publish_showcase.py", "worker.py", "model_runtime.py", "experimental_runtime.py",
                      "certificate_codec.py", "lemma_library.py", "lemma_imports.py")
NOTE = ("Selected, exposed classical arithmetic examples from completed local searches. "
        "Every displayed script passed a fresh independent Peano-kernel replay. "
        "Step sources and advisor calls are reported separately; no unseen-accuracy or new-mathematics claim.")


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()


def read_record(path, maximum=4 * worker.MAX_RESULT_BYTES):
    return experiments.pinned_json(path, maximum)


def matches_pin(path, pin):
    return type(pin) is dict and descriptor(path) == {key: pin.get(key) for key in ("bytes", "sha256")}


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def valid_sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def experimental_snapshot(options):
    """Hash replay authority only; no native import, checker, solver or model."""
    import experimental_runtime as runtime
    native = runtime.native_snapshot()
    library = runtime.library_snapshot() if options["lemmas"] else None
    entries, reservation = {}, None
    if library is not None:
        catalog, _ = runtime.pinned._small(runtime.LIBRARY / "manifest.json", maximum=8*1024*1024,
                                         expected=library["sha256"])
        entries = {entry["name"]: entry["certificate"]["sha256"] for entry in catalog["entries"]}
        _, reservation = runtime.pinned._small(runtime.RESERVATION, maximum=128*1024,
                                               expected=runtime.RESERVATION_SHA256)
    ranker = None
    if options["ranker"] != "off":
        _, ranker = runtime.pinned._small(runtime.RANKER, maximum=65536, expected=runtime.RANKER_SHA256)
    return {"profile": runtime.PROFILE, "native_source": native, "library_manifest": library,
            "library_certificates": entries, "reservation": reservation, "ranker": ranker,
            "replay_sources": {name: runtime.pinned._fingerprint(APP / name, 512*1024)
                               for name in REPLAY_SOURCE_FILES},
            "kernel_entrypoints": dict(worker.KERNEL_PINS)}


def experimental_admission(normalized, result, pins):
    options, search = normalized.get("experimental"), result.get("search", {})
    recorded = search.get("experimental")
    if options is None:
        require(recorded is None, "Experimental result cannot be replayed without its explicit request authority.")
        return None
    require(type(recorded) is dict and set(recorded) <= EXPERIMENTAL_OPTIONS | {
        "profile", "native_source", "library_source"}, "Unknown experimental result authority fields.")
    selection = {key: value for key, value in recorded.items() if key in EXPERIMENTAL_OPTIONS}
    replay_selection = worker.validate_request("replay", {
        "theorem": normalized["theorem"], "tactics": result["commands"], "experimental": selection})["experimental"]
    require(replay_selection == options, "Recorded experimental selection differs from the live request.")
    snapshot = experimental_snapshot(options)
    require(recorded.get("profile") == snapshot["profile"]
            and recorded.get("native_source") == snapshot["native_source"]
            and pins.get("kernel_entrypoints") == snapshot["kernel_entrypoints"]
            and result.get("execution", {}).get("worker_started") is True
            and type(result.get("execution", {}).get("worker_exit_code")) is int
            and result["execution"]["worker_exit_code"] == 0,
            "Experimental native/kernel authority does not match the pinned replay engine.")
    app, used = pins.get("application", {}), search.get("application_source_pins")
    required = set(REPLAY_SOURCE_FILES) - {"publish_showcase.py"}
    require(type(used) is dict and required <= set(used) and len(used) <= 64
            and all(type(name) is str and re.fullmatch(r"[a-z0-9_]+\.py", name)
                    and type(pin) is dict and set(pin) == {"bytes", "sha256"}
                    and type(pin["bytes"]) is int and pin["bytes"] > 0 and valid_sha(pin["sha256"])
                    and app.get(name) == pin for name, pin in used.items()),
            "Experimental result source pins disagree with the finalized HTTP run.")
    library, source = search.get("lemma_library"), recorded.get("library_source")
    if options["lemmas"]:
        require(type(source) is dict and source.get("manifest") == snapshot["library_manifest"]
                and type(library) is dict and library.get("manifest_sha256") == snapshot["library_manifest"]["sha256"]
                and valid_sha(library.get("target_sha256")), "Checked-library manifest or original target is missing/mismatched.")
        names = library.get("available_names")
        require(type(names) is list and len(names) <= 128 and len(set(names)) == len(names)
                and set(names) <= set(snapshot["library_certificates"]), "Invalid checked-library name inventory.")
        label = "hydra-certified-lemmas-v1-" + canonical_sha({"profile": "hydra-certified-lemmas-v1",
            "manifest": library["manifest_sha256"], "target": library["target_sha256"]})
        require(library.get("capability_label") == label, "Checked-library capability is not bound to its target and manifest.")
    else:
        require(source is None and library is None, "Disabled checked library supplied import authority.")
    planner = search.get("structured_planning")
    ranker = search.get("branch_ranker")
    require((planner is None and options["planner"] == "off") or type(planner) is dict
            and planner.get("enabled") is (options["planner"] != "off"), "Structured-planner selection mismatch.")
    require((ranker is None and options["ranker"] == "off") or type(ranker) is dict
            and ranker.get("enabled") is (options["ranker"] != "off")
            and ranker.get("artifact_sha256") == (None if snapshot["ranker"] is None else snapshot["ranker"]["sha256"]),
            "Branch-ranker selection/artifact mismatch.")
    return {"options": options, "snapshot": snapshot, "recorded_library": library,
            "scope": "Historical search sources are bound to their run; fresh replay uses the exact native/library edition and current pinned replay wrapper."}


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
    # Older P2 records predate explicit planner/ranker/adviser default fields.
    # Re-normalize both records, preserving every explicit setting and the raw request.
    require(worker.validate_request("search", record.get("normalized_request")) == normalized
            and record.get("canonical_theorem") == canonical,
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
    replay_input = {"theorem": request["theorem"], "tactics": commands}
    if normalized.get("experimental") is not None:
        replay_input["experimental"] = normalized["experimental"]
    replay_request = worker.validate_request("replay", replay_input)
    require(replay_request["tactics"] == commands, "Returned proof commands are not canonical tactic lines.")
    authority = experimental_admission(normalized, result, pins)
    require(type(record.get("submitted_at_utc")) is str and type(record.get("finished_at_utc")) is str,
            "Missing live run timestamps.")
    return {"eligible": True, "record": record, "result": result, "request": request,
            "normalized": normalized, "canonical": canonical, "provenance": provenance,
            "replay_request": replay_request, "experimental_authority": authority}


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
    options = request.get("experimental")
    authority = experimental_snapshot(options) if options is not None else None
    result = worker.replay(request)
    publication_authority = None
    if authority is not None:
        require(experimental_snapshot(options) == authority, "Replay authority changed during independent verification.")
        _, _, _, commands, _ = worker.load_kernel(options)
        publication_authority = {"snapshot": authority, "allowed_commands": sorted(commands),
                                 "selection": options}
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    require(rss <= worker.LIMITS["manual"]["rss_bytes"], "Independent replay exceeded the peak RSS bound.")
    output = {"result": result, "native_seconds": round(time.monotonic()-started, 6),
              "peak_rss_bytes": rss, "kernel_commit": worker.SOURCE_COMMIT,
              "model_calls": 0, "vampire_calls": 0, "network_calls": 0,
              "external_adviser_launches": 0, "publication_authority": publication_authority}
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
                    and item.get("source") in {"model", "heuristic", "vampire"} | EXTRA_SOURCES
                    for item, command in zip(provenance, commands)),
            "Winning-path command provenance is missing or inconsistent.")
    counts = dict(Counter(item["source"] for item in provenance))
    require(counts == result.get("proof_sources"), "Step-source counts disagree with the winning path.")
    return counts, []


def import_ledger(ledger, names, phase, available):
    require(type(ledger) is dict and ledger.get("policy") == "hydra-checked-import-budget-v1"
            and ledger.get("max_attempts") == 32 and ledger.get("max_imports_per_proof") == 8,
            "Missing or changed checked-import budget.")
    rows = ledger.get("records")
    require(type(rows) is list and len(rows) <= 32
            and all(type(row) is dict and row.get("name") in available
                    and row.get("phase") in {"search", "independent_replay", "manual"}
                    and row.get("status") in {"native_accepted", "rejected_or_interrupted"} for row in rows),
            "Checked-import ledger contains unaccounted or unauthorized attempts.")
    phases = {key: sum(row["phase"] == key for row in rows) for key in ("search", "independent_replay", "manual")}
    require(ledger.get("attempts") == len(rows) and ledger.get("phases") == phases
            and ledger.get("accepted") == sum(row["status"] == "native_accepted" for row in rows)
            and ledger.get("rejected") == sum(row["status"] == "rejected_or_interrupted" for row in rows)
            and [row["name"] for row in rows if row["phase"] == phase] == names
            and all(row["status"] == "native_accepted" for row in rows if row["phase"] == phase),
            "Checked-import totals or full winning-script replay imports disagree.")
    if phase == "manual":
        require(len(rows) == len(names), "Fresh replay import ledger contains unrelated calls.")


def checked_preload(source, snapshot):
    require(type(source) is dict and source.get("manifest") == snapshot["library_manifest"],
            "Replay changed its checked-library manifest.")
    counts = source.get("preload_verification", {})
    require(counts.get("all_entries_checked_before_return") is True
            and counts.get("certificates_checked") == len(snapshot["library_certificates"])
            and counts.get("native_kernel_checks") == counts.get("certificates_checked")
            and counts.get("manifest_bytes_read") == snapshot["library_manifest"]["bytes"]
            and type(counts.get("certificate_bytes_read")) is int and counts["certificate_bytes_read"] > 0
            and counts.get("catalogue_bytes_read") == counts["certificate_bytes_read"] + counts["manifest_bytes_read"],
            "Checked-library preload verification is missing or internally inconsistent.")
    return counts


def validate_experimental_replay(candidate, replay):
    admission = candidate.get("experimental_authority")
    if admission is None:
        require(not set(candidate["result"].get("proof_sources", {})) & EXTRA_SOURCES,
                "External-helper step attribution requires explicit experimental authority.")
        return None
    authority, verification = replay.get("publication_authority", {}), replay["result"]
    snapshot, options = admission["snapshot"], admission["options"]
    require(authority.get("snapshot") == snapshot and authority.get("selection") == options,
            "Fresh replay source/library/reservation authority differs from admission.")
    commands = authority.get("allowed_commands")
    require(type(commands) is list and 1 <= len(commands) <= 128
            and all(type(command) is str and re.fullmatch(r"[a-z_]+", command) for command in commands)
            and commands == sorted(set(commands)), "Fresh replay did not report a finite command authority.")
    metadata = verification.get("experimental", {})
    require(set(metadata) == EXPERIMENTAL_OPTIONS | {"profile", "native_source_sha256", "library_source", "imports"}
            and all(metadata.get(key) == value for key, value in options.items())
            and metadata.get("profile") == snapshot["profile"]
            and metadata.get("native_source_sha256") == snapshot["native_source"]["sha256"],
            "Fresh replay changed the experimental selection or native identity.")
    library = admission["recorded_library"]
    label = "hydra-sharing-native-v1" if library is None else library["capability_label"]
    available = [] if library is None else library["available_names"]
    environment = {"label": label, "allowed_commands": commands, "allowed_theorems": sorted(available)}
    require(verification.get("surface") == label and verification.get("environment_sha256") == canonical_sha(environment),
            "Fresh replay does not match the original target-bound capability and excluded-library inventory.")
    imports = [command.split()[1] for command in candidate["result"]["commands"] if command.startswith("use ")]
    require(len(imports) <= 8 and set(imports) <= set(available), "Winning script imports unavailable checked lemmas.")
    original_preload = fresh_preload = None
    if library is None:
        require(metadata["library_source"] is None and metadata["imports"] is None,
                "Disabled library gained authority during replay.")
    else:
        import_ledger(library.get("imports"), imports, "independent_replay", available)
        import_ledger(metadata.get("imports"), imports, "manual", available)
        original_preload = checked_preload(candidate["result"]["search"]["experimental"]["library_source"], snapshot)
        fresh_preload = checked_preload(metadata["library_source"], snapshot)
        for item in candidate["result"]["search"]["provenance"]:
            evidence = item.get("evidence", {})
            if evidence.get("strategy") == "checked_lemma_retrieval":
                require(evidence.get("lemma") in available and evidence.get("certificate_sha256")
                        == snapshot["library_certificates"][evidence["lemma"]],
                        "Checked-lemma step cites a different or excluded certificate.")
    return {"authority": authority, "capability": environment,
            "checked_imports": {"winning_commands": len(imports), "names": imports,
                "original_ledger": None if library is None else library["imports"],
                "fresh_replay_ledger": metadata["imports"],
                "original_preload": original_preload, "fresh_replay_preload": fresh_preload},
            "scope": "One full original-theorem replay; imported certificates were eagerly checked and each use was separately admitted."}


def adviser_contributions(candidate):
    """Calls, cache hits and winning steps are different observed quantities."""
    search, admission = candidate["result"]["search"], candidate.get("experimental_authority")
    shared_record = search.get("external_advisers")
    if shared_record is None:
        require(not set(candidate["result"].get("proof_sources", {})) & EXTRA_SOURCES,
                "External winning steps have no actual execution accounting.")
        return None
    require(admission is not None and type(shared_record) is dict, "Shared adviser accounting lacks experimental authority.")
    options, snapshot = admission["options"], admission["snapshot"]
    selected = set(options["advisers"]) | ({"vampire"} if candidate["normalized"]["search_mode"] == "symbolic" else set())
    shared, actual = shared_record.get("shared", {}), shared_record.get("actual_launches_by_backend")
    rows = shared.get("records")
    require(shared_record.get("authority_identity") == canonical_sha({"native": snapshot["native_source"],
            "checked_library": snapshot["library_manifest"] or "none"})
            and shared.get("accounting_complete") is True and shared.get("active_request") is None
            and type(rows) is list and len(rows) <= 12 and shared.get("requests") == len(rows)
            and type(actual) is dict and set(actual) <= selected
            and all(type(value) is int and value >= 0 for value in actual.values()),
            "Incomplete or mismatched shared-adviser authority/accounting.")
    require(all(type(row) is dict and row.get("backend") in selected
                and type(row.get("actual_launches")) is int and row["actual_launches"] in (0, 1)
                and type(row.get("cache_hit")) is bool and row.get("quiescent") is True for row in rows),
            "Unaccounted shared-adviser execution or cleanup.")
    require(all(actual.get(name, 0) == sum(row["actual_launches"] for row in rows if row["backend"] == name)
                and search.get(name + "_calls") == actual.get(name, 0) for name in selected)
            and sum(actual.values()) == shared.get("actual_launches") == shared.get("known_actual_launches")
            and shared.get("cache_hits") == sum(row["cache_hit"] for row in rows)
            and all(not row["cache_hit"] or row["actual_launches"] == 0 for row in rows),
            "Actual shared-adviser launches/cache hits disagree with recorded counters.")
    for item in search["provenance"]:
        name = item["source"]
        if name not in EXTRA_SOURCES:
            continue
        evidence = item.get("evidence", {})
        require(name in selected and evidence.get("strategy") == "external_native_reconstruction"
                and valid_sha(evidence.get("input_sha256")) and valid_sha(evidence.get("context_sha256")),
                "External winning step has no exact input/context attribution.")
        matches = [row for row in rows if row["backend"] == name and row.get("status") == "completed"
            and row["actual_launches"] == 1 and not row["cache_hit"] and row.get("exit_code") == 0
            and all(row.get(key) == evidence[key] for key in ("input_sha256", "context_sha256"))]
        helper_names = ["adviser_worker.py", "adviser_process.py", "adviser_protocol.py",
                        "vampire_process.py", "vampire_limits.py"]
        helper_names += (["p9_bridge_common.py", "egraph_bridge.py" if name == "egg" else "e_bridge.py"]
                         + (["vampire_bridge.py"] if name == "e" else []) if name in {"egg", "e"} else
                         ["adviser_polynomials.py", "sympy_bridge.py" if name == "sympy" else "smt_bridge.py"])
        pins = search["application_source_pins"]
        require(set(helper_names) <= set(pins), "External helper's source inventory is absent from the live run.")
        helper_hash = canonical_sha({key: pins[key] for key in helper_names})
        require(all(type(row.get("identity")) is dict and row["identity"].get("backend") == name
                    and row["identity"].get("helper_sha256") == pins["adviser_worker.py"]["sha256"]
                    and row["identity"].get("helper_sources_sha256") == helper_hash for row in matches),
                "External helper identity differs from the recorded search source pins.")
        require(any(any(run.get("executed") is True and run.get("status") == "completed"
                        and run.get("exit_code") == 0 and run.get("quiescent") is True
                        and run.get("input_sha256") == row["input_sha256"] and run.get("identity") == row.get("identity")
                        for run in shared_record.get("runners", {}).get(name, []))
                    and any(advice.get("backend") == name and advice.get("invocations") == 1
                            and advice.get("kernel_checked") is False and advice.get("identity") == row.get("identity")
                            and all(advice.get(key) == row[key] for key in ("input_sha256", "context_sha256"))
                            for advice in search.get("advisor_results", [])) for row in matches),
                "External winning step is not backed by a completed, reaped helper and matching advice receipt.")
    return {"actual_launches_by_backend": actual, "controller_requests": shared_record.get("controller_requests"),
            "requests_by_backend": shared_record.get("requests_by_backend"), "cache_hits": shared["cache_hits"],
            "scope": "Original search only; helper completion is advisory. The fresh native replay launches no advisers."}


def planned_contributions(candidate, replay_authority):
    search = candidate["result"]["search"]
    selected = [item for item in search.get("provenance", []) if item.get("evidence", {}).get("strategy") == "structured_plan"]
    if not selected:
        return {"winning_steps": 0, "winning_imports": 0, "plans": []}
    report = search.get("structured_planning", {})
    require(replay_authority is not None and report.get("enabled") is True
            and type(report.get("plans")) is list and len(report["plans"]) <= 8
            and type(report.get("chunk_steps")) is int and 1 <= report["chunk_steps"] <= 8,
            "Structured winning steps have no bounded native plan evidence.")
    capability = replay_authority["capability"]
    caps_sha = canonical_sha({"label": capability["label"], "commands": capability["allowed_commands"],
                             "theorems": capability["allowed_theorems"]})
    snapshot = candidate["experimental_authority"]["snapshot"]
    library_sha = "none" if snapshot["library_manifest"] is None else snapshot["library_manifest"]["sha256"]
    used = set()
    for item in selected:
        evidence = item["evidence"]
        index, chunk = int(evidence["plan_id"]), int(evidence["chunk"])
        require(0 <= index < len(report["plans"]) and chunk >= 1
                and type(item.get("macro_step")) is int and 1 <= item["macro_step"] <= report["chunk_steps"],
                "Invalid structured-plan command offset.")
        plan = report["plans"][index]
        commands, actions = plan.get("commands"), plan.get("actions")
        require(type(commands) is list and 1 <= len(commands) <= 32
                and all(type(command) is str for command in commands)
                and type(actions) is list and len(actions) == len(commands), "Missing complete compiled plan commands/actions.")
        offset = (chunk - 1) * report["chunk_steps"] + item["macro_step"] - 1
        require(offset < len(commands) and commands[offset] == item["command"] and actions[offset] == item.get("planner_action")
                and plan.get("plan_sha256") == evidence.get("plan_sha256")
                == hashlib.sha256(("\n".join(commands) + "\n").encode()).hexdigest()
                and plan.get("capability_identity") == caps_sha and plan.get("library_identity") == library_sha
                and plan.get("source") == evidence.get("planner_source")
                and plan.get("native_source") == item["source"], "Structured-plan provenance differs from its actual checked command.")
        requests = [row for row in report.get("requests_detail", []) if row.get("request") == plan.get("request")]
        require(len(requests) == 1 and type(requests[0].get("context")) is dict
                and canonical_sha(requests[0]["context"]) == plan.get("context_sha256"),
                "Structured plan lacks its exact recorded context.")
        require(plan["source"] == "heuristic" and item["source"] == "heuristic"
                or plan["source"] == "planner_model" and item["source"] == "model"
                and type(requests[0].get("actual_model_calls")) is int and requests[0]["actual_model_calls"] > 0,
                "Structured-plan model attribution lacks an actual decode.")
        used.add(index)
    return {"winning_steps": len(selected), "winning_imports": sum(item["command"].startswith("use ") for item in selected),
            "plans": sorted(used), "scope": "Checked commands on the winning path, not every generated plan or helper request."}


def certificate_observation(original, verification):
    observed = original["search"].get("proof_cost", {}).get("final")
    if observed is not None:
        require(type(observed) is dict and observed.get("policy") == "hydra-proof-cost-observation-v1"
                and observed.get("stage") == "final", "Unknown final certificate observation.")
        if observed.get("exact", {}).get("structural_occurrences") is True:
            require(observed.get("structural_occurrences") == verification["proof_nodes"],
                    "Original certificate occurrences disagree with independent replay.")
    return {"original_final_observation": observed,
            "original_distinct_objects": None if observed is None or observed.get("exact", {}).get("distinct_objects") is not True
                else observed.get("distinct_objects"),
            "fresh_replay_structural_occurrences": verification["proof_nodes"], "fresh_replay_distinct_objects": None,
            "scope": "Distinct objects/depth describe the original search certificate only. Fresh replay independently checks the full proof and its occurrence count; it does not remeasure DAG sharing."}


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
    for key in ("model_calls", "vampire_calls", "sympy_calls", "cvc5_calls", "egg_calls", "e_calls"):
        value = search.get(key)
        require(value is None or type(value) is int and value >= 0, "Invalid actual advisor counter.")
    for name in ("model", "vampire"):
        require(not sources.get(name, 0) or type(search.get(name + "_calls")) is int
                and search[name + "_calls"] > 0, "Winning adviser steps require an observed actual call.")
    replay_authority = validate_experimental_replay(candidate, replay)
    advisors = adviser_contributions(candidate)
    plans = planned_contributions(candidate, replay_authority)
    cost = certificate_observation(result, verification)
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
                               "native_seconds": replay.get("native_seconds"),
                               "experimental_authority": replay_authority},
        "certificate_cost": cost, "adviser_contributions": advisors, "structured_plan_contributions": plans,
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
        summary["replay_source_files"] = {name: descriptor(APP / name) for name in REPLAY_SOURCE_FILES}
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
                require(all(matches_pin(Path(candidate["provenance"][name]["path"]), candidate["provenance"][name])
                            for name in ("case_record", "plan", "summary", "source_pins")),
                        "Finalized live input changed during independent replay.")
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
        require(summary["replay_source_files"] == {name: descriptor(APP / name) for name in REPLAY_SOURCE_FILES},
                "Publisher/replay wrapper sources changed during staging.")
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
