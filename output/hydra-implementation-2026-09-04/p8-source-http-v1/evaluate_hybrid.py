#!/usr/bin/env python3
"""Run bounded local HTTP comparisons; each search is submitted at most once.

Example:
  python3 -I -B hydra-playground/evaluate_hybrid.py \
    --modes heuristic symbolic --first 4 --output output/hydra-comparison-01

Only case.theorem is sent to the prover, never a reference proof. These are
exposed, agent-authored engineering diagnostics, not an unseen benchmark or a
single-variable comparison with the preserved model-only search algorithm.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import signal
import sys
import time
from urllib.parse import urlsplit

APP = Path(__file__).resolve().parent
SUITE = APP / "hybrid-evaluation-cases.json"
REFERENCES = APP / "hybrid-evaluation-reference-check.json"
MODES = ("model", "heuristic", "symbolic", "hybrid")
TERMINAL = {"completed", "failed", "cancelled"}
UNKNOWN = {"unknown", "exhausted", "limit", "budget_exhausted", "open", "unproved"}
MAX_RESPONSE = 2 * 1024 * 1024
CLEANUP_SECONDS = 8.0
COUNTERS = ("model_calls", "model_decode_attempts", "model_advisor_calls",
            "vampire_calls", "vampire_advisor_calls", "tactic_attempts", "candidates_executed",
            "states_expanded", "states_discovered", "forward_passes", "generated_token_steps",
            "depth_reached", "compact_arith_attempts", "compact_arith_accepted", "compact_arith_rejected")


class BoundaryError(ValueError):
    pass


class StopRequested(Exception):
    pass


class TransportError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise BoundaryError(message)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def descriptor(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write_json(path, value):
    """Only replace files inside the fresh directory owned by this invocation."""
    temporary = path.with_suffix(path.suffix + ".pending")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    os.replace(temporary, path)


class Client:
    def __init__(self, origin):
        parsed = urlsplit(origin)
        require(parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
                and parsed.username is None and parsed.password is None
                and parsed.path in ("", "/") and not parsed.query and not parsed.fragment
                and parsed.port is not None and 1024 <= parsed.port <= 65535,
                "The evaluation URL must be http://127.0.0.1:PORT with no extra URL components.")
        self.port = parsed.port
        self.origin = "http://127.0.0.1:" + str(self.port)
        self.token = None

    def request(self, method, path, deadline, payload=None):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("The HTTP request deadline was reached.")
        # HTTPConnection connects directly: no proxies and no redirect following.
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=min(5.0, remaining))
        headers = {"Origin": self.origin, "Accept": "application/json", "Connection": "close"}
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
            headers["X-CSRF-Token"] = self.token or ""
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            length = response.getheader("Content-Length")
            require(length is not None and length.isdigit() and int(length) <= MAX_RESPONSE,
                    "The server response has no bounded Content-Length.")
            chunks, received = [], 0
            while received < int(length):
                require(time.monotonic() < deadline, "The HTTP response exceeded its deadline.")
                if connection.sock is not None:
                    connection.sock.settimeout(min(5.0, max(0.001, deadline - time.monotonic())))
                block = response.read1(min(65536, int(length) - received))
                require(bool(block), "The HTTP response ended before its declared length.")
                received += len(block)
                chunks.append(block)
            require(time.monotonic() < deadline, "The HTTP response exceeded its deadline.")
            value = json.loads(b"".join(chunks))
            require(type(value) is dict, "The server did not return a JSON object.")
            return response.status, value
        except TimeoutError:
            raise
        except (OSError, http.client.HTTPException) as error:
            raise TransportError(str(error)) from error
        finally:
            connection.close()

    def job(self, identifier, deadline):
        status, body = self.request("GET", "/api/jobs/" + identifier, deadline)
        require(status == 200 and body.get("ok") is True and type(body.get("job")) is dict,
                "Job polling failed: HTTP " + str(status) + " " + str(body.get("error", "")))
        job = body["job"]
        require(job.get("id") == identifier and job.get("state") in TERMINAL | {"queued", "running"},
                "The job identity or state is invalid.")
        return job


def error_text(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False) if value is not None else ""


def input_rejection(body):
    if body.get("error_kind") in {"invalid_input", "parse_error", "invalid_theorem"}:
        return True
    message = error_text(body.get("error", ""))
    return any(fragment in message for fragment in (
        "invalid or open development formula:", "Quantify all free variables explicitly.",
        "Theorem exceeds 4096 UTF-8 bytes.", "Theorem must be non-empty text.",
    ))


def metrics(job):
    result = job.get("result") if type(job.get("result")) is dict else {}
    search = result.get("search") if type(result.get("search")) is dict else {}
    progress = job.get("progress") if type(job.get("progress")) is dict else {}
    values, sources = {}, {}
    for key in COUNTERS:
        values[key], sources[key] = None, None
        for name, scope in (("result.search", search), ("result", result), ("last_progress", progress)):
            value = scope.get(key)
            if type(value) is int and value >= 0:
                values[key], sources[key] = value, name
                break
    return {"values": values, "sources": sources,
            "proof_cost": search.get("proof_cost"), "native_timing": search.get("native_timing"),
            "last_progress_is_partial": any(source == "last_progress" for source in sources.values()),
            "missing_counters_are_not_zero": True}


def classify(case, job, canonical):
    state = job["state"]
    if state == "cancelled":
        return {"outcome": "cancelled", "kernel_verified": False}
    if state == "failed":
        if input_rejection(job):
            return {"outcome": "rejected", "kernel_verified": False,
                    "expected_rejection": case["input_supported"] is False}
        return {"outcome": "server_failure", "kernel_verified": False, "error": job.get("error")}
    result = job.get("result")
    if type(result) is not dict:
        return {"outcome": "invalid_server_result", "kernel_verified": False,
                "error": "Completed job has no result object."}
    if not case["input_supported"]:
        return {"outcome": "unsupported_input_accepted", "kernel_verified": False,
                "error": "The supposedly unsupported input reached a search result."}
    if result.get("theorem") != canonical:
        return {"outcome": "invalid_server_result", "kernel_verified": False,
                "error": "Result is not bound to the requested canonical theorem."}
    claims_proof = result.get("status") in {"proved", "proof"} or result.get("kernel_checked") is True
    if claims_proof:
        valid = (result.get("status") in {"proved", "proof"} and result.get("kernel_checked") is True
                 and result.get("goals") == [] and type(result.get("proof_nodes")) is int
                 and result["proof_nodes"] > 0 and type(result.get("commands")) is list
                 and bool(result["commands"]))
        if not valid:
            return {"outcome": "invalid_proof_claim", "kernel_verified": False,
                    "error": "Proof status lacks a complete, kernel-checked original-theorem result."}
        return {"outcome": "proved" if case["expected"] == "provable" else "unexpected_proof",
                "kernel_verified": True, "proof_nodes": result["proof_nodes"],
                "proof_steps": len(result["commands"])}
    if result.get("status") in UNKNOWN and result.get("kernel_checked") is False:
        return {"outcome": "unknown", "kernel_verified": False, "search_status": result["status"]}
    return {"outcome": "invalid_server_result", "kernel_verified": False,
            "error": "Completed job has an unrecognized proof/search status."}


def cancel_owned(client, identifier, deadline):
    cleanup = {"job_id": identifier, "cancel_attempted": False, "terminal_observed": False}
    if time.monotonic() >= deadline:
        cleanup["error"] = "No time remained for cancellation."
        return cleanup
    try:
        cleanup["cancel_attempted"] = True
        status, body = client.request("POST", "/api/jobs/" + identifier + "/cancel", deadline, {})
        cleanup["cancel_http_status"] = status
        cleanup["cancel_response"] = body
        if status != 200 or body.get("ok") is not True:
            return cleanup
        while time.monotonic() < deadline:
            job = client.job(identifier, deadline)
            if job["state"] in TERMINAL:
                cleanup["terminal_observed"] = True
                cleanup["terminal_job"] = job
                return cleanup
            time.sleep(min(0.25, max(0.0, deadline - time.monotonic())))
    except (StopRequested, BoundaryError, TransportError, TimeoutError, json.JSONDecodeError) as error:
        cleanup["error"] = str(error)
    return cleanup


def evaluate_one(client, case, mode, canonical, path, total_deadline, job_seconds):
    started = time.monotonic()
    job_deadline = min(started + job_seconds, total_deadline)
    work_deadline = job_deadline - CLEANUP_SECONDS
    request = {"theorem": case["theorem"], "max_model_calls": 8, "beam_width": 1, "search_mode": mode}
    record = {"schema": "hydra-hybrid-http-case-v1", "case_id": case["id"], "search_mode": mode,
              "expected": case["expected"], "input_supported": case["input_supported"],
              "request": request, "started_at_utc": utc_now(), "outcome": "pending",
              "automatic_retry": False, "submission_count": 0, "kernel_verified": False}
    identifier, terminal = None, False
    interrupted = False
    write_json(path, record)
    # A timer also bounds a peer that sends headers/body bytes too slowly for
    # an ordinary socket inactivity timeout. Cleanup has its own reserved time.
    signal.setitimer(signal.ITIMER_REAL, max(0.001, work_deadline - time.monotonic()))
    try:
        require(time.monotonic() < work_deadline, "Not enough time remains for a bounded job.")
        record["submission_count"] = 1
        record["outcome"] = "submitting"
        write_json(path, record)
        try:
            status, body = client.request("POST", "/api/search", work_deadline, request)
        except (BoundaryError, TransportError, TimeoutError, json.JSONDecodeError) as error:
            record.update(outcome="submission_outcome_unknown", error=str(error), stop_after_case=True)
            return record
        record["submission_http_status"] = status
        record["submission_response"] = body
        if status != 202 or body.get("ok") is not True:
            if status in (400, 422) and input_rejection(body):
                record.update(outcome="rejected", expected_rejection=case["input_supported"] is False)
            else:
                record.update(outcome="server_failure", error=body.get("error"))
                if status in (403, 404, 409, 429) or status >= 500:
                    record["stop_after_case"] = True
            return record
        require(type(body.get("job_id")) is str and re.fullmatch(r"[0-9a-f]{32}", body["job_id"]),
                "Accepted submission has no valid owned job ID.")
        identifier = body["job_id"]
        record.update(job_id=identifier, outcome="running")
        write_json(path, record)
        print(case["id"] + " / " + mode + ": job " + identifier, flush=True)
        next_notice = started + 15
        while time.monotonic() < work_deadline:
            job = client.job(identifier, work_deadline)
            record["last_job"] = job
            record["metrics"] = metrics(job)
            if job["state"] in TERMINAL:
                terminal = True
                record.update(classify(case, job, canonical))
                if record["outcome"] in {"invalid_proof_claim", "unexpected_proof", "invalid_server_result"}:
                    record["stop_after_case"] = True
                return record
            if time.monotonic() >= next_notice:
                write_json(path, record)
                values = record["metrics"]["values"]
                print(case["id"] + " / " + mode + ": " + str(round(time.monotonic() - started))
                      + "s, model_calls=" + str(values["model_calls"])
                      + ", vampire_calls=" + str(values["vampire_calls"]), flush=True)
                next_notice = time.monotonic() + 15
            time.sleep(min(0.75, max(0.0, work_deadline - time.monotonic())))
        record.update(outcome="timeout", error="The case reached its bounded deadline.")
    except StopRequested as error:
        interrupted = True
        record.update(outcome="interrupted", error=str(error), stop_after_case=True)
    except TimeoutError as error:
        record.update(outcome="timeout", error=str(error))
    except (BoundaryError, TransportError, json.JSONDecodeError) as error:
        record.update(outcome="server_failure", error=str(error), stop_after_case=True)
        if identifier is None and record["submission_count"] == 1:
            record["outcome"] = "submission_outcome_unknown"
    finally:
        remaining = job_deadline - time.monotonic()
        signal.setitimer(signal.ITIMER_REAL, max(0.0, remaining))
        if identifier is not None and not terminal:
            cleanup = cancel_owned(client, identifier, min(job_deadline, time.monotonic() + CLEANUP_SECONDS))
            record["cleanup"] = cleanup
            if type(cleanup.get("terminal_job")) is dict:
                record["last_job_after_cancel"] = cleanup["terminal_job"]
                record["metrics"] = metrics(cleanup["terminal_job"])
            if not cleanup["terminal_observed"]:
                record["stop_after_case"] = True
        # Preserve the final record even when the work/cancellation deadline
        # has expired. No new HTTP operation occurs during this bookkeeping.
        signal.setitimer(signal.ITIMER_REAL, 0)
        record["finished_at_utc"] = utc_now()
        record["client_elapsed_seconds"] = round(time.monotonic() - started, 4)
        if "metrics" not in record:
            record["metrics"] = metrics({})
        final_job = record.get("last_job_after_cancel", record.get("last_job", {}))
        record["server_elapsed_seconds"] = final_job.get("elapsed_seconds")
        final_result = final_job.get("result") if type(final_job.get("result")) is dict else {}
        search = final_result.get("search") if type(final_result.get("search")) is dict else {}
        record["search_elapsed_seconds"] = search.get("elapsed_seconds")
        write_json(path, record)
        signal.setitimer(signal.ITIMER_REAL, max(0.0, total_deadline - time.monotonic()))
        print(case["id"] + " / " + mode + ": " + record["outcome"], flush=True)
    if interrupted:
        record["interrupt_observed"] = True
        write_json(path, record)
    return record


def aggregate(plan, records, started, fatal_error):
    complete_outcomes = {"proved", "unknown", "rejected"}
    complete = (len(records) == len(plan["jobs"]) and fatal_error is None
                and all(record["outcome"] in complete_outcomes for record in records)
                and all(record.get("expected_rejection", True) for record in records))
    modes = {}
    for mode in plan["modes"]:
        selected = [record for record in records if record["search_mode"] == mode]
        totals = {}
        for key in COUNTERS:
            observed = [record["metrics"]["values"][key] for record in selected
                        if record.get("metrics", {}).get("values", {}).get(key) is not None]
            final = [record for record in selected if record.get("metrics", {}).get("sources", {}).get(key)
                     in {"result", "result.search"}]
            totals[key] = {"observed_total": sum(observed) if observed else None,
                           "observed_cases": len(observed), "final_result_cases": len(final),
                           "includes_partial_progress": len(final) < len(observed)}
        modes[mode] = {"requested": sum(job["mode"] == mode for job in plan["jobs"]),
                       "recorded": len(selected), "outcomes": dict(Counter(record["outcome"] for record in selected)),
                       "positive_proofs": sum(record["expected"] == "provable" and record["outcome"] == "proved"
                                              for record in selected),
                       "kernel_verified_records": sum(record.get("kernel_verified") is True for record in selected),
                       "client_elapsed_seconds": round(sum(record.get("client_elapsed_seconds", 0) for record in selected), 4),
                       "counters": totals}
    return {"schema": "hydra-hybrid-http-summary-v1", "status": "complete" if complete else "incomplete",
            "all_requested_cases_recorded": len(records) == len(plan["jobs"]),
            "requested_jobs": len(plan["jobs"]), "recorded_jobs": len(records), "modes": modes,
            "elapsed_seconds": round(time.monotonic() - started, 4), "fatal_error": fatal_error,
            "case_files": [record["record_file"] for record in records],
            "automatic_retry": False, "training_performed": False, "benchmark_claim": False,
            "comparison_scope": plan["comparison_scope"],
            "verification_scope": "Server-reported native kernel acceptance with theorem/terminal checks; "
                                  "this HTTP runner does not independently rerun the kernel.",
            "exit_observation": "Caller must observe the actual outer process exit; a written summary alone is not completion."}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--suite", type=Path, default=SUITE, help="Diagnostic suite JSON (default: the original suite).")
    parser.add_argument("--references", type=Path, default=REFERENCES,
                        help="Matching native reference audit JSON (default: the original audit).")
    parser.add_argument("--url", default="http://127.0.0.1:8767")
    parser.add_argument("--modes", nargs="+", choices=MODES, default=list(MODES))
    cases_group = parser.add_mutually_exclusive_group()
    cases_group.add_argument("--case-ids", nargs="+")
    cases_group.add_argument("--first", type=int, help="First N supported cases in declared suite order (default: 4).")
    parser.add_argument("--output", type=Path, required=True, help="A fresh output directory.")
    parser.add_argument("--total-seconds", type=float, default=1200)
    parser.add_argument("--job-seconds", type=float, default=190)
    args = parser.parse_args()
    require(math.isfinite(args.total_seconds) and 20 <= args.total_seconds <= 1200,
            "Total wall ceiling must be between 20 and 1200 seconds.")
    require(math.isfinite(args.job_seconds) and 15 <= args.job_seconds <= 190,
            "Per-job wall ceiling must be between 15 and 190 seconds.")
    require(len(set(args.modes)) == len(args.modes), "A mode may be requested only once.")
    client = Client(args.url)
    suite_path, references_path = args.suite.resolve(), args.references.resolve()
    suite = json.loads(suite_path.read_bytes())
    references = json.loads(references_path.read_bytes())
    require(suite["schema"] == "hydra-hybrid-diagnostic-suite-v1" and suite["benchmark_claim"] is False,
            "Unexpected diagnostic suite.")
    require(references.get("checks_passed") is True
            and descriptor(suite_path) == {key: references["suite"][key] for key in ("bytes", "sha256")},
            "The suite no longer matches its verified native reference record.")
    canonical = {case["id"]: case.get("canonical_theorem") for case in references["case_records"]}
    by_id = {case["id"]: case for case in suite["cases"]}
    if args.case_ids is not None:
        require(len(set(args.case_ids)) == len(args.case_ids) and all(identifier in by_id for identifier in args.case_ids),
                "Case IDs must be distinct IDs in the declared suite.")
        selected = [by_id[identifier] for identifier in args.case_ids]
    else:
        first = 4 if args.first is None else args.first
        supported = [case for case in suite["cases"] if case["input_supported"]]
        require(1 <= first <= len(supported), "First-N count exceeds the supported suite cases.")
        selected = supported[:first]
    require(all(re.fullmatch(r"[a-z0-9_]{1,80}", case["id"]) for case in selected), "Unsafe case identifier.")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started + args.total_seconds
    jobs = [{"case_id": case["id"], "mode": mode} for case in selected for mode in args.modes]
    plan = {"schema": "hydra-hybrid-http-plan-v1", "started_at_utc": utc_now(), "url": client.origin,
            "suite": {"path": str(suite_path), **descriptor(suite_path)},
            "reference_check": {"path": str(references_path), **descriptor(references_path)},
            "runner": descriptor(Path(__file__)), "modes": args.modes, "jobs": jobs,
            "limits": {"total_wall_seconds": args.total_seconds, "per_job_wall_seconds": args.job_seconds,
                       "cleanup_reserve_seconds": CLEANUP_SECONDS, "max_model_calls": 8, "beam_width": 1},
            "ordering": "Declared case order, then declared mode order; no adaptive case selection.",
            "comparison_scope": "End-to-end exposed diagnostic comparison. Model-only uses the preserved original search; "
                                "hybrid modes use different symbolic search allocation. This is not a controlled "
                                "single-algorithm-variable experiment, nor an unseen generalization benchmark.",
            "reference_scripts_sent_to_server": False, "automatic_retry": False}
    records, fatal_error = [], None
    write_json(output / "plan.json", plan)
    write_json(output / "summary.json", aggregate(plan, records, started, "Evaluation is still running."))

    def stop(signum, _frame):
        if signum == signal.SIGALRM:
            raise TimeoutError("The configured wall deadline was reached.")
        raise StopRequested("Stopped by signal " + str(signum) + ".")

    previous_handlers = {signum: signal.signal(signum, stop)
                         for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM)}
    signal.setitimer(signal.ITIMER_REAL, max(0.001, deadline - time.monotonic()))
    try:
        status, server = client.request("GET", "/api/status", deadline - CLEANUP_SECONDS)
        require(status == 200 and server.get("ok") is True and type(server.get("csrf_token")) is str
                and len(server["csrf_token"]) >= 16, "The local server is not ready or has no CSRF token.")
        client.token = server["csrf_token"]
        write_json(output / "server-status.json", {key: value for key, value in server.items() if key != "csrf_token"})
        for index, job in enumerate(jobs):
            if time.monotonic() >= deadline - CLEANUP_SECONDS - 1:
                fatal_error = "The total wall ceiling leaves no time for another bounded job."
                break
            filename = str(index).zfill(3) + "-" + job["case_id"] + "-" + job["mode"] + ".json"
            record = evaluate_one(client, by_id[job["case_id"]], job["mode"], canonical.get(job["case_id"]),
                                  output / filename, deadline, args.job_seconds)
            record["record_file"] = filename
            write_json(output / filename, record)
            records.append(record)
            write_json(output / "summary.json", aggregate(plan, records, started, "Evaluation is still running."))
            if record.get("stop_after_case"):
                fatal_error = "Stopped after " + job["case_id"] + " / " + job["mode"] + ": " + record["outcome"]
                break
    except (StopRequested, BoundaryError, TransportError, TimeoutError, OSError, json.JSONDecodeError) as error:
        fatal_error = str(error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        # A terminal file may already have been saved before an outer client
        # exception. Include such a record rather than silently omitting it.
        known = {record.get("record_file") for record in records}
        for index, job in enumerate(jobs):
            filename = str(index).zfill(3) + "-" + job["case_id"] + "-" + job["mode"] + ".json"
            path = output / filename
            if filename in known or not path.is_file():
                continue
            try:
                saved = json.loads(path.read_bytes())
                require(saved.get("case_id") == job["case_id"] and saved.get("search_mode") == job["mode"],
                        "Saved case record identity changed.")
                saved["record_file"] = filename
                saved["recovered_after_client_failure"] = True
                records.append(saved)
            except (OSError, ValueError) as error:
                fatal_error = (fatal_error or "") + " Cannot read the saved case record: " + str(error)
        summary = aggregate(plan, records, started, fatal_error)
        write_json(output / "summary.json", summary)
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
    print(str(output / "summary.json") + ": " + summary["status"], flush=True)
    return 0 if summary["status"] == "complete" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BoundaryError, OSError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
