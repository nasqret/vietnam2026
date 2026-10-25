#!/usr/bin/env python3
"""Bounded theorem-only HTTP experiments; one submission per case/mode, no retry.

No reference scripts are accepted or sent. Completed records are eligible for
the separate independent-replay showcase publisher, not proof certificates by
themselves. Run with isolated Python and bytecode disabled.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import signal
import sys
import time

APP = Path(__file__).resolve().parent
ROOT = APP.parent
sys.path.insert(0, str(APP))
import worker
from search_settings import PROFILES, profile
from vampire_limits import solver_limits
from evaluate_hybrid import (BoundaryError, Client, COUNTERS, MODES, StopRequested,
    TERMINAL, TransportError, cancel_owned, classify, descriptor, input_rejection,
    metrics, require, utc_now, write_json)

CASE_SCHEMA = "hydra-advanced-http-case-v1"
PLAN_SCHEMA = "hydra-advanced-http-plan-v1"
SUMMARY_SCHEMA = "hydra-advanced-http-summary-v1"
MAX_TOTAL_SECONDS = 7200
MAX_JOBS = 80
COMPARISON = ("Selected exposed classical arithmetic probes, not an unseen benchmark. "
              "Model-only retains the original search; hybrid modes use different search "
              "allocation. This is not a controlled single-variable algorithm comparison.")


def pinned_json(path, maximum=2 * 1024 * 1024):
    require(path.is_file() and not path.is_symlink(), "Expected a regular JSON file: " + str(path))
    raw = path.read_bytes()
    require(0 < len(raw) <= maximum, "JSON input exceeds its bound: " + str(path))
    value = json.loads(raw)
    require(type(value) is dict, "Expected a JSON object: " + str(path))
    return value, {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def source_pins():
    """Read metadata only; model workers independently authenticate actual weights."""
    worker.kernel_status()
    # Pin the executing backend, UI, and runner. The independent publisher is
    # deliberately excluded so it can be developed during an experiment.
    names = ("server.py", "worker.py", "model_runtime.py", "hybrid_runtime.py",
        "hybrid_search.py", "arithmetic_search.py", "finite_difference.py", "advice_memory.py", "decomposition_memory.py", "polynomial_chunks.py", "atom_polynomial.py", "proof_cost.py", "compact_dispatch.py", "algebra_plan_cost.py",
        "vampire_bridge.py", "vampire_process.py",
        "vampire_worker.py", "vampire_limits.py", "search_settings.py",
        "certificate_codec.py", "lemma_library.py", "lemma_imports.py", "experimental_runtime.py",
        "proof_planner.py", "planner_provider.py", "branch_ranker.py",
        "adviser_runtime.py", "adviser_protocol.py", "adviser_polynomials.py", "adviser_process.py",
        "adviser_worker.py", "sympy_bridge.py", "smt_bridge.py", "p9_bridge_common.py", "egraph_bridge.py", "e_bridge.py",
        "evaluate_hybrid.py", "evaluate_advanced.py", "app.js", "index.html", "styles.css")
    application = {}
    for name in names:
        require((APP / name).is_file() and not (APP / name).is_symlink(), "Missing backend source: " + name)
        application[name] = descriptor(APP / name)
    metadata_paths = [APP / ".runtime/model-ready.json", APP / ".runtime/model/manifest.json",
        ROOT / "artifacts/hydra-retention-pilot-2026-08-30/trained-model-collected-01/model/manifest.json"]
    model = {str(path.relative_to(ROOT)): descriptor(path) if path.is_file() and not path.is_symlink() else None
             for path in metadata_paths}
    vampire = {}
    for name, maximum in (("manifest.json", 64 * 1024), ("ready.json", 64 * 1024), ("vampire", 100 * 1024**2)):
        path = APP / ".runtime/vampire" / name
        if path.is_file() and not path.is_symlink():
            require(path.stat().st_size <= maximum, "Vampire metadata/binary exceeds its pin bound.")
            vampire[name] = descriptor(path)
        else:
            vampire[name] = None
    package_names = {"mlx", "mlx-metal", "mlx-lm", "transformers", "tokenizers", "numpy"}
    packages = {}
    for site in sorted((APP / ".runtime/venv/lib").glob("python*/site-packages")):
        for dist in importlib.metadata.distributions(path=[str(site)]):
            name = str(dist.metadata.get("Name", "")).lower().replace("_", "-")
            if name in package_names:
                metadata = (dist.read_text("METADATA") or "").encode()
                record = (dist.read_text("RECORD") or "").encode()
                packages[name] = {"version": dist.version, "site_packages": str(site),
                    "metadata_sha256": hashlib.sha256(metadata).hexdigest(),
                    "record_sha256": hashlib.sha256(record).hexdigest()}
    catalog = worker.SOURCE / "_deploy/hydra-retention-evaluation-recovery-source.json"
    return {"application": application, "kernel_commit": worker.SOURCE_COMMIT,
        "kernel_entrypoints": dict(worker.KERNEL_PINS), "kernel_catalog": descriptor(catalog),
        "model_metadata": model, "vampire_package": vampire, "prepared_runtime_packages": packages,
        "application_scope": "Explicit backend, UI and runner list; independent publisher and showcase data excluded.",
        "package_scope": "Versions and METADATA/RECORD hashes in the prepared worker venv; not a binary rehash.",
        "model_scope": "Metadata hashes only; actual model files are authenticated by each model-using worker.",
        "client_python": {"executable": sys.executable, "version": sys.version}}


def prepare_request(case, mode, profile_name, calls, beam, validate_statement, experimental=None):
    request = {"theorem": case["theorem"], "search_mode": mode,
               "search_profile": profile_name, "max_model_calls": calls, "beam_width": beam}
    if experimental is not None:
        request["experimental"] = experimental
    # Match HTTP transport normalization before invoking the strict one-line parser.
    normalized = worker.validate_request("search", request)
    canonical = validate_statement(normalized["theorem"])
    return request, normalized, canonical


def cleanup_seconds(profile_name):
    return max(8.0, float(solver_limits(profile_name)["wall_seconds"]) + 4.0)


def evaluate_one(client, case, request, normalized, canonical, path, deadline, context):
    started = time.monotonic()
    cleanup_reserve = cleanup_seconds(normalized["search_profile"])
    worker_seconds = worker.resource_limits("search", normalized)["wall_seconds"]
    case_deadline = min(started + worker_seconds + cleanup_reserve, deadline)
    work_deadline = case_deadline - cleanup_reserve
    record = {"schema": CASE_SCHEMA, "origin": "live_http_search", "case_id": case["id"],
        "case_metadata": {key: case[key] for key in ("title", "math", "interest", "category", "priority") if key in case},
        "expected": case.get("expected", "provable"), "input_supported": True,
        "search_mode": normalized["search_mode"], "search_profile": normalized["search_profile"],
        "request": request, "normalized_request": normalized, "canonical_theorem": canonical,
        "started_at_utc": utc_now(), "outcome": "pending", "submission_count": 0,
        "automatic_retry": False, "reference_scripts_sent_to_server": False,
        "kernel_verified": False, "run_context": context,
        "limits": {"worker_wall_seconds": worker_seconds, "cleanup_seconds": cleanup_reserve,
                   "case_wall_seconds": worker_seconds + cleanup_reserve}}
    identifier, terminal = None, False
    write_json(path, record)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, work_deadline - time.monotonic()))
    try:
        require(time.monotonic() < work_deadline, "Insufficient remaining work time.")
        record.update(submission_count=1, outcome="submitting", submitted_at_utc=utc_now())
        write_json(path, record)
        try:
            status, body = client.request("POST", "/api/search", work_deadline, request)
        except (BoundaryError, TransportError, TimeoutError, json.JSONDecodeError) as error:
            record.update(outcome="submission_outcome_unknown", error=str(error), stop_after_case=True)
            return record
        record.update(submission_http_status=status, submission_response=body)
        if status != 202 or body.get("ok") is not True:
            if status in (400, 422) and input_rejection(body):
                record.update(outcome="rejected", error=body.get("error"))
            else:
                record.update(outcome="server_failure", error=body.get("error"), stop_after_case=True)
            return record
        require(type(body.get("job_id")) is str and re.fullmatch(r"[0-9a-f]{32}", body["job_id"]),
                "Accepted submission has no valid owned job ID.")
        identifier = body["job_id"]
        record.update(job_id=identifier, outcome="running")
        write_json(path, record)
        label = case["id"] + " / " + normalized["search_mode"] + " / " + normalized["search_profile"]
        print(label + ": job " + identifier, flush=True)
        next_notice = started + 15
        while time.monotonic() < work_deadline:
            job = client.job(identifier, work_deadline)
            record.update(last_job=job, metrics=metrics(job))
            if job["state"] in TERMINAL:
                terminal = True
                record.update(classify({**case, "input_supported": True,
                    "expected": case.get("expected", "provable")}, job, canonical))
                if record["outcome"] in {"invalid_proof_claim", "invalid_server_result", "unexpected_proof"}:
                    record["stop_after_case"] = True
                return record
            if time.monotonic() >= next_notice:
                write_json(path, record)
                values = record["metrics"]["values"]
                print(label + ": " + str(round(time.monotonic()-started)) + "s; model="
                      + str(values["model_calls"]) + ", Vampire=" + str(values["vampire_calls"])
                      + ", states=" + str(values["states_expanded"]), flush=True)
                next_notice = time.monotonic() + 15
            time.sleep(min(0.75, max(0.0, work_deadline-time.monotonic())))
        record.update(outcome="timeout", error="The per-case work deadline was reached.")
    except StopRequested as error:
        record.update(outcome="interrupted", error=str(error), stop_after_case=True)
    except TimeoutError as error:
        record.update(outcome="timeout", error=str(error))
    except (BoundaryError, TransportError, json.JSONDecodeError, OSError) as error:
        record.update(outcome="server_failure", error=str(error), stop_after_case=True)
        if identifier is None and record["submission_count"]:
            record["outcome"] = "submission_outcome_unknown"
    finally:
        signal.setitimer(signal.ITIMER_REAL, max(0.001, case_deadline-time.monotonic()))
        if identifier is not None and not terminal:
            cleanup = cancel_owned(client, identifier, min(case_deadline, time.monotonic()+cleanup_reserve))
            record["cleanup"] = cleanup
            if type(cleanup.get("terminal_job")) is dict:
                record["last_job_after_cancel"] = cleanup["terminal_job"]
                record["metrics"] = metrics(cleanup["terminal_job"])
            if not cleanup["terminal_observed"]:
                record["stop_after_case"] = True
        signal.setitimer(signal.ITIMER_REAL, 0)
        record.update(finished_at_utc=utc_now(), client_elapsed_seconds=round(time.monotonic()-started, 5))
        record.setdefault("metrics", metrics({}))
        final_job = record.get("last_job_after_cancel", record.get("last_job", {}))
        result = final_job.get("result") if type(final_job.get("result")) is dict else {}
        execution = result.get("execution") if type(result.get("execution")) is dict else final_job.get("execution")
        execution = execution if type(execution) is dict else {}
        search = result.get("search") if type(result.get("search")) is dict else {}
        record["server_elapsed_seconds"] = final_job.get("elapsed_seconds")
        record["worker_elapsed_seconds"] = execution.get("elapsed_seconds")
        record["search_elapsed_seconds"] = search.get("elapsed_seconds")
        write_json(path, record)
        signal.setitimer(signal.ITIMER_REAL, max(0.001, deadline-time.monotonic()))
        print(case["id"] + " / " + normalized["search_mode"] + ": " + record["outcome"], flush=True)
    return record


def aggregate(plan, records, started, error=None, pins_unchanged=None):
    complete = (len(records) == len(plan["jobs"]) and error is None and pins_unchanged is True
                and all(r["outcome"] in {"proved", "unknown", "rejected"} for r in records))
    modes = {}
    for mode in plan["modes"]:
        selected = [r for r in records if r["search_mode"] == mode]
        counters = {}
        for key in COUNTERS:
            observed = [r["metrics"]["values"][key] for r in selected if r.get("metrics", {}).get("values", {}).get(key) is not None]
            final = sum(r.get("metrics", {}).get("sources", {}).get(key) in {"result", "result.search"} for r in selected)
            counters[key] = {"observed_total": sum(observed) if observed else None,
                "observed_cases": len(observed), "final_result_cases": final,
                "includes_partial_progress": final < len(observed)}
        timing = {key: {"observed_total": round(sum(r[key] for r in selected if type(r.get(key)) in (int, float)), 5),
                       "observed_cases": sum(type(r.get(key)) in (int, float) for r in selected)}
                  for key in ("client_elapsed_seconds", "server_elapsed_seconds", "worker_elapsed_seconds", "search_elapsed_seconds")}
        modes[mode] = {"recorded": len(selected), "outcomes": dict(Counter(r["outcome"] for r in selected)),
                       "counters": counters, "timings": timing}
    return {"schema": SUMMARY_SCHEMA, "status": "complete" if complete else "incomplete",
        "requested_jobs": len(plan["jobs"]), "recorded_jobs": len(records),
        "all_requested_cases_completed": complete, "source_pins_unchanged": pins_unchanged,
        "modes": modes, "case_files": [r["record_file"] for r in records],
        "elapsed_seconds": round(time.monotonic()-started, 5), "fatal_error": error,
        "automatic_retry": False, "benchmark_claim": False, "training_performed": False,
        "comparison_scope": COMPARISON,
        "verification_scope": "Server-reported original-goal kernel checks; independent replay belongs to the publisher.",
        "exit_observation": "Observe the actual terminal exit; writing this summary is not proof of process completion."}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--curriculum", type=Path, required=True)
    parser.add_argument("--case-ids", nargs="+", required=True)
    parser.add_argument("--modes", nargs="+", choices=MODES, default=["hybrid"])
    parser.add_argument("--profile", choices=tuple(PROFILES), default="standard")
    parser.add_argument("--max-model-calls", type=int)
    parser.add_argument("--beam-width", type=int)
    parser.add_argument("--experimental", action="store_true", help="Use the isolated sharing engine and checked lemma catalogue.")
    parser.add_argument("--no-lemmas", action="store_true", help="Disable retrieval in an experimental-engine comparison.")
    parser.add_argument("--planner",choices=("off","deterministic"),default="off",help="Select bounded structured planning on the experimental engine.")
    parser.add_argument("--ranker",choices=("off","linear-v1"),default="off",help="Select the pinned trained branch ranker on the experimental engine.")
    parser.add_argument("--advisers",nargs="*",choices=("sympy","cvc5","egg","e"),default=[],help="Select fixed shared-budget external advisers (experimental Deep only).")
    parser.add_argument("--url", default="http://127.0.0.1:8767")
    parser.add_argument("--total-seconds", type=float, default=1200)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(math.isfinite(args.total_seconds) and 30 <= args.total_seconds <= MAX_TOTAL_SECONDS,
            "Global wall limit must be between 30 and 7200 seconds.")
    require(len(set(args.modes)) == len(args.modes) and len(set(args.case_ids)) == len(args.case_ids),
            "Modes and case IDs must be distinct.")
    selected_profile = profile(args.profile)
    calls = selected_profile["default_model_calls"] if args.max_model_calls is None else args.max_model_calls
    beam = selected_profile["default_beam"] if args.beam_width is None else args.beam_width
    suite, suite_pin = pinned_json(args.curriculum.resolve())
    require(type(suite.get("cases")) is list and 1 <= len(suite["cases"]) <= 100,
            "Curriculum must contain 1 to 100 cases.")
    by_id = {case["id"]: case for case in suite["cases"]}
    require(len(by_id) == len(suite["cases"]) and all(i in by_id for i in args.case_ids), "Unknown or duplicate case ID.")
    require(all(re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", i) for i in args.case_ids), "Unsafe case ID.")
    validate_statement, *_ = worker.load_kernel()
    jobs = []
    for identifier in args.case_ids:
        for mode in args.modes:
            experimental = {"engine":"sharing-v1","lemmas":not args.no_lemmas,"planner":args.planner,
                            "ranker":args.ranker,"advisers":args.advisers} if args.experimental else None
            require(not args.no_lemmas or args.experimental, "--no-lemmas requires --experimental.")
            require(args.planner=="off" or args.experimental,"--planner requires --experimental.")
            require(args.ranker=="off" or args.experimental,"--ranker requires --experimental.")
            require(not args.advisers or (args.experimental and args.profile=="deep"),
                    "--advisers requires --experimental and --profile deep.")
            request, normalized, canonical = prepare_request(by_id[identifier], mode, args.profile, calls, beam, validate_statement, experimental)
            jobs.append({"case_id": identifier, "mode": mode, "request": request,
                         "normalized_request": normalized, "canonical_theorem": canonical})
    require(1 <= len(jobs) <= MAX_JOBS, "Run exceeds the 80-job limit.")
    client = Client(args.url)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started + args.total_seconds
    pins = source_pins()
    write_json(output / "source-pins.json", pins)
    plan = {"schema": PLAN_SCHEMA, "origin": "live_http_search", "started_at_utc": utc_now(),
        "url": client.origin, "curriculum": suite_pin, "modes": args.modes, "profile": args.profile,
        "max_model_calls": calls, "beam_width": beam, "jobs": jobs,
        "source_pins": {"file": "source-pins.json", **descriptor(output / "source-pins.json")},
        "limits": {"global_wall_seconds": args.total_seconds, "selected_profile": selected_profile,
                   "cleanup_reserve_seconds": cleanup_seconds(args.profile)},
        "ordering": "Requested case order, then mode order; no adaptive selection.",
        "comparison_scope": COMPARISON, "reference_scripts_sent_to_server": False, "automatic_retry": False}
    write_json(output / "plan.json", plan)
    context = {"plan_sha256": descriptor(output / "plan.json")["sha256"],
               "source_pins_sha256": plan["source_pins"]["sha256"]}
    records, error, unchanged = [], None, None
    write_json(output / "summary.json", aggregate(plan, records, started, "Running"))

    def stop(signum, _frame):
        if signum == signal.SIGALRM:
            raise TimeoutError("Configured wall deadline reached.")
        raise StopRequested("Interrupted by signal " + str(signum))

    previous = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM)}
    signal.setitimer(signal.ITIMER_REAL, max(0.001, deadline-time.monotonic()))
    try:
        status, body = client.request("GET", "/api/status", deadline-cleanup_seconds(args.profile))
        require(status == 200 and body.get("ok") is True and type(body.get("csrf_token")) is str
                and len(body["csrf_token"]) >= 16, "Server is not ready or has no CSRF token.")
        require(body.get("kernel_commit") == worker.SOURCE_COMMIT, "Server reports a different kernel revision.")
        client.token = body["csrf_token"]
        write_json(output / "server-status.json", {k: v for k, v in body.items() if k != "csrf_token"})
        for index, job in enumerate(jobs):
            if deadline-time.monotonic() <= cleanup_seconds(args.profile)+1:
                error = "Global ceiling leaves no work time for another job."
                break
            filename = str(index).zfill(3) + "-" + job["case_id"] + "-" + job["mode"] + ".json"
            record = evaluate_one(client, by_id[job["case_id"]], job["request"], job["normalized_request"],
                job["canonical_theorem"], output / filename, deadline, context)
            record["record_file"] = filename
            write_json(output / filename, record)
            records.append(record)
            write_json(output / "summary.json", aggregate(plan, records, started, "Running"))
            if record.get("stop_after_case"):
                error = "Stopped after " + filename + ": " + record["outcome"]
                break
    except (StopRequested, BoundaryError, TransportError, TimeoutError, OSError, ValueError) as failure:
        error = str(failure)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        # Recover an immediately persisted final record if a signal interrupted bookkeeping.
        known = {r.get("record_file") for r in records}
        for index, job in enumerate(jobs):
            filename = str(index).zfill(3) + "-" + job["case_id"] + "-" + job["mode"] + ".json"
            if filename not in known and (output / filename).is_file():
                saved, _ = pinned_json(output / filename, 4 * worker.MAX_RESULT_BYTES)
                require(saved.get("case_id") == job["case_id"] and saved.get("search_mode") == job["mode"], "Saved job identity changed.")
                saved["record_file"] = filename
                records.append(saved)
        try:
            ending = source_pins()
            write_json(output / "source-pins-after.json", ending)
            unchanged = pins == ending and descriptor(args.curriculum.resolve()) == {k: suite_pin[k] for k in ("bytes", "sha256")}
            if not unchanged:
                error = (error + "; " if error else "") + "Source/model/package metadata or curriculum changed during the run."
        except (OSError, ValueError) as failure:
            unchanged = False
            error = (error + "; " if error else "") + "Final pin check failed: " + str(failure)
        summary = aggregate(plan, records, started, error, unchanged)
        summary["case_file_pins"] = {r["record_file"]: descriptor(output / r["record_file"]) for r in records}
        write_json(output / "summary.json", summary)
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    print(str(output / "summary.json") + ": " + summary["status"], flush=True)
    return 0 if summary["status"] == "complete" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BoundaryError, OSError, ValueError) as failure:
        print(str(failure), file=sys.stderr)
        raise SystemExit(2)
