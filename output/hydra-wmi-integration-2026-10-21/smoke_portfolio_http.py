"""One explicit newest-model API smoke job; never retries model work.

Run only when authorized and the comparison is idle. No credentials are saved.
This is an integration smoke, not a quality benchmark or promotion decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

MODEL_ID = "wmi-c6-long-vanilla11"
CHECKPOINT = "177501bf7b662a210b6cf6887844a282365437c781e53138ad5495f02c620a06"
EXPORT = "659f71892bacdafc7488d8b683dd8dda051dfa4b054f74ba340db4da59fd07a3"
TERMINAL = {"completed", "failed", "cancelled"}
MAX_RESPONSE_BYTES = 24 * 1024**2


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def public(value):
    if isinstance(value, dict):
        return {key: public(item) for key, item in value.items() if key != "csrf_token"}
    if isinstance(value, list):
        return [public(item) for item in value]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8768)
    parser.add_argument("--output", type=Path, required=True, help="New evidence directory; must not already exist")
    parser.add_argument("--theorem", default="forall n. n = n")
    args = parser.parse_args()
    require(1024 <= args.port <= 65535, "Invalid loopback port")
    args.output.mkdir(parents=True, exist_ok=False)
    origin = "http://127.0.0.1:" + str(args.port)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    token = None
    job_id = None
    terminal = None
    post_attempted = False
    cancel_attempted = False
    started = time.monotonic()

    def save(name, value):
        raw = (json.dumps(public(value), ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode()
        path = args.output / name
        with path.open("xb") as stream:
            stream.write(raw)
        return {"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    def request(path, body=None):
        headers = {"Origin": origin, "Accept": "application/json"}
        raw = None
        if body is not None:
            raw = json.dumps(body, ensure_ascii=False).encode()
            headers.update({"Content-Type": "application/json", "X-CSRF-Token": token})
        req = urllib.request.Request(origin + path, data=raw, headers=headers)
        with opener.open(req, timeout=20) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
            require(len(data) <= MAX_RESPONSE_BYTES, "API response exceeded 24 MiB")
            value = json.loads(data)
            require(value.get("ok") is True, "API did not report success")
            return value

    def cancel_own_job():
        nonlocal cancel_attempted
        if job_id is not None and terminal is None and not cancel_attempted:
            cancel_attempted = True
            save("CANCEL_RESPONSE.json", request("/api/jobs/" + job_id + "/cancel", {}))

    try:
        before = request("/api/status")
        save("STATUS_BEFORE.json", before)
        token = before.get("csrf_token")
        require(type(token) is str and bool(token), "Missing CSRF token")
        require(before.get("computation_active") is False, "Another request is active; refusing to submit")
        model = before.get("models", {}).get(MODEL_ID, {})
        require(model.get("available") is True and model.get("selection_id") == MODEL_ID,
                "Explicit newest model is unavailable; no substitution is permitted")
        require(model.get("checkpoint_sha256") == CHECKPOINT and model.get("exported_adapter_sha256") == EXPORT
                and model.get("selected_step") == 16384, "Newest model metadata identity differs")
        require(before.get("search_modes", {}).get("portfolio", {}).get("available") is True,
                "Portfolio is unavailable")
        payload = {"theorem": args.theorem, "model_id": MODEL_ID, "search_mode": "portfolio",
                   "search_profile": "portfolio", "max_model_calls": 128, "beam_width": 1}
        save("REQUEST.json", payload)
        save("SUBMISSION_INTENT.json", {"job_count": 1, "automatic_retry": False,
             "model_inference": True, "purpose": "API integration smoke, not model-quality evidence"})
        post_attempted = True
        submitted = request("/api/search", payload)
        job_id = submitted.get("job_id")
        require(type(job_id) is str and re.fullmatch(r"[0-9a-f]{32}", job_id), "Missing submitted job id")
        save("SUBMITTED.json", submitted)
        deadline = time.monotonic() + 580
        last_event = None
        with (args.output / "PROGRESS.jsonl").open("x") as progress_file:
            while True:
                response = request("/api/jobs/" + job_id)
                job = response["job"]
                require(job.get("id") == job_id, "Job id changed")
                if job.get("state") in TERMINAL:
                    terminal = job
                    save("TERMINAL_JOB.json", response)
                    break
                event = {"state": job.get("state"), "progress": job.get("progress")}
                if event != last_event:
                    progress_file.write(json.dumps(public({**event, "elapsed_seconds": job.get("elapsed_seconds")})) + "\n")
                    progress_file.flush()
                    print(json.dumps(public(event)), flush=True)
                    last_event = event
                if time.monotonic() >= deadline:
                    cancel_own_job()
                    raise RuntimeError("Client collection deadline reached; cancellation requested, cleanup still requires verification")
                time.sleep(1)
        after = request("/api/status")
        save("STATUS_AFTER.json", after)
        execution = terminal.get("execution") or {}
        result = terminal.get("result") or {}
        portfolio = result.get("portfolio") or {}
        search = result.get("search") or {}
        summary = {"schema": "hydra-portfolio-http-smoke-v1", "job_id": job_id,
            "state": terminal.get("state"), "job_error": terminal.get("error"),
            "client_elapsed_seconds": time.monotonic() - started,
            "execution": execution, "result_status": result.get("status"),
            "kernel_checked": result.get("kernel_checked"), "commands": result.get("commands"),
            "proof_nodes": result.get("proof_nodes"), "proof_sources": result.get("proof_sources"),
            "search_counters": {key: value for key, value in search.items()
                                if type(value) in (int, float, bool) or value is None},
            "model": result.get("model"), "portfolio": portfolio,
            "computation_active_after": after.get("computation_active"),
            "quality_benchmark": False, "automatic_retry": False}
        save("SUMMARY.json", summary)
        require(terminal.get("state") == "completed" and terminal.get("error") is None,
                "Job did not complete successfully; inspect preserved evidence")
        require(execution.get("quiescent") is True and execution.get("worker_started") is True
                and execution.get("elapsed_seconds", 550) < 550, "Missing clean, bounded worker completion")
        require(result.get("kind") == "portfolio" and result.get("original_theorem") == args.theorem
                and portfolio.get("selected_model_id") == MODEL_ID, "Portfolio request binding differs")
        require(result.get("model", {}).get("checkpoint_sha256") == CHECKPOINT
                and result.get("model", {}).get("exported_adapter_sha256") == EXPORT,
                "Actual returned model identity differs")
        require(type(search.get("model_calls")) is int and search["model_calls"] > 0,
                "No actual newest-model forward call recorded")
        require(result.get("status") == "proved" and result.get("kernel_checked") is True,
                "Smoke theorem did not receive a native proof; this is not a quality comparison")
        save("SMOKE_CHECK.json", {"passed": True, "native_proof_checked_by": "supervised server workers",
             "independent_smoke_replay": False, "actual_model_calls": search["model_calls"],
             "winner": portfolio.get("winner"), "model_quality_claim": False})
        print(json.dumps({"passed": True, "job_id": job_id, "winner": portfolio.get("winner"),
                          "model_calls": search["model_calls"], "output": str(args.output)}), flush=True)
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        cancellation_error = None
        try:
            cancel_own_job()
        except Exception as cancel_exc:
            cancellation_error = str(cancel_exc)[:1000]
        save("SMOKE_FAILURE.json", {"error": str(exc)[:2000], "job_id": job_id,
             "submission_attempted": post_attempted, "cancel_attempted": cancel_attempted,
             "cancellation_error": cancellation_error,
             "cleanup_confirmed": bool(terminal and (terminal.get("execution") or {}).get("quiescent") is True),
             "automatic_retry": False, "note": "If submission was attempted without a returned job id, inspect server state; do not resubmit automatically."})
        print(json.dumps({"passed": False, "job_id": job_id, "error": str(exc)[:1000],
                          "output": str(args.output)}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
