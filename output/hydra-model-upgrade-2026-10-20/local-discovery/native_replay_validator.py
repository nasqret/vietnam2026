#!/usr/bin/env python3
"""Independently replay one canonical theorem through the deployed no-imports worker.

No model or fetched latent module is imported. Input is exactly
{"theorem": canonical_native_formula, "tactics": [unmodified_literal_actions]}.
The caller must pin this file and the worker source in its experiment manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import unicodedata

WORKER_SHA256 = "e7923426cf39a68719fc79f8efc1db0cf016edf03bd79d248a94ac06235de951"
KERNEL_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
REPLAY_ENVIRONMENT_SHA256 = "8edaaffa8edf1f6d8b187ba3ada5e87c8219374ef556031afbc103948619b69f"
MAX_BYTES = 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "Duplicate JSON key")
            value[key] = item
        return value

    def bad_constant(value):
        raise ValueError("Non-finite JSON number: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_constant)


def check_request(request):
    require(type(request) is dict and set(request) == {"theorem", "tactics"},
            "Only theorem and tactics are permitted; experimental authority is forbidden")
    theorem, tactics = request["theorem"], request["tactics"]
    require(type(theorem) is str and theorem and theorem == theorem.strip()
            and len(theorem.encode()) <= 4096, "Invalid canonical theorem input")
    require(type(tactics) is list and len(tactics) <= 160, "Invalid tactic list")
    for value in [theorem, *tactics]:
        require(type(value) is str and value and value == value.strip(),
                "Empty or whitespace-normalized input is forbidden")
        require(not any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
                        for char in value), "Control or multiline input is forbidden")
    require(all(len(line.encode()) <= 512 for line in tactics), "Tactic exceeds512bytes")


def inspect_completion(request, returncode, stdout, stderr):
    """Pure validation of a genuine worker completion; never creates a proof."""
    check_request(request)
    report = {"schema": "hydra-independent-native-replay-v1", "proof_accepted": False,
              "actual_process_exit_code": returncode, "kernel_commit": KERNEL_COMMIT,
              "expected_execution_authority": "hydra-playground-native-v1/no-imports",
              "worker_stdout": {"bytes": len(stdout), "sha256": hashlib.sha256(stdout).hexdigest()},
              "worker_stderr": {"bytes": len(stderr), "sha256": hashlib.sha256(stderr).hexdigest()},
              "request_sha256": hashlib.sha256(json.dumps(request, ensure_ascii=False,
                  sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()}
    try:
        require(len(stdout) <= MAX_BYTES and len(stderr) <= MAX_BYTES, "Oversized worker output")
        events = [strict_json(line) for line in stdout.splitlines()]
        require(len(events) == 1, "Replay requires exactly one terminal event")
        event = events[0]
        if returncode != 0:
            report.update(status="worker_error", worker_event=event)
            return report
        require(type(event) is dict and set(event) == {"type", "result"}
                and event["type"] == "result", "Missing native result event")
        result = event["result"]
        require(type(result) is dict and result.get("theorem") == request["theorem"]
                and result.get("original_theorem") == request["theorem"]
                and result.get("commands") == request["tactics"],
                "Replay must bind the exact canonical original theorem and raw action list")
        require(result.get("kind") == "manual" and result.get("model_used") is False
                and result.get("classical") is False and "experimental" not in result
                and result.get("kernel_source_commit") == KERNEL_COMMIT,
                "Replay authority, logic, source or model boundary changed")
        require(type(result.get("goals")) is list and type(result.get("trace")) is list,
                "Missing native goals or trace")
        require(all(type(step) is dict for step in result["trace"]), "Malformed native trace row")
        require(result.get("tactics_requested") == len(request["tactics"]),
                "Native requested action count differs")
        claimed = result.get("status") == "proved"
        require(result.get("kernel_checked") is claimed, "Kernel/status completion flags disagree")
        if request["tactics"]:
            require(result.get("surface") == "hydra-playground-native-v1"
                    and result.get("environment_sha256") == REPLAY_ENVIRONMENT_SHA256,
                    "Native no-imports capability identity changed")
        else:
            require(result.get("mode") == "initial-state" and not claimed,
                    "Zero actions may inspect the initial state, never manufacture QED")
        if claimed:
            trace = result["trace"]
            steps = [step for step in trace if "v" in step]
            require(not result["goals"] and trace and trace[-1].get("qed") is True
                    and trace[-1].get("theorem") == request["theorem"]
                    and trace[-1].get("tactic_count") == len(request["tactics"]),
                    "QED requires complete original-target closure and exact footer")
            require(result.get("tactics_applied") == len(request["tactics"])
                    and result.get("failed_tactics") == 0 and result.get("failed_step") is None
                    and result.get("error") is None and len(steps) == len(request["tactics"])
                    and all(step.get("status") == "ok" and step.get("error") is None
                            and step.get("step") == index for index, step in enumerate(steps, 1)),
                    "QED has incomplete or unsuccessful native action accounting")
        report.update(status="proved" if claimed else "not_proved", proof_accepted=claimed,
                      native_result=result)
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        report.update(status="invalid_completion", error=str(exc))
    return report


def replay(request, *, worker, python=sys.executable, timeout_seconds=125):
    """Run a fresh isolated native worker, returning report and unmodified outputs."""
    check_request(request)
    require(type(timeout_seconds) in {int, float} and 0 < timeout_seconds <= 125,
            "Replay needs a finite wall limit of at most125seconds")
    worker = Path(worker).resolve()
    require(hashlib.sha256(worker.read_bytes()).hexdigest() == WORKER_SHA256,
            "Worker differs from the independently pinned deployed implementation")
    started = time.monotonic()
    raw = json.dumps(request, ensure_ascii=False, allow_nan=False).encode()
    try:
        done = subprocess.run([str(python), "-I", "-B", str(worker), "--mode", "replay"],
                              input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        return ({"schema": "hydra-independent-native-replay-v1", "status": "timeout",
                 "proof_accepted": False, "actual_process_exit_code": None,
                 "seconds": time.monotonic() - started}, exc.stdout or b"", exc.stderr or b"")
    report = inspect_completion(request, done.returncode, done.stdout, done.stderr)
    require(hashlib.sha256(worker.read_bytes()).hexdigest() == WORKER_SHA256,
            "Worker changed during replay")
    report.update(seconds=time.monotonic() - started, worker_sha256=WORKER_SHA256)
    return report, done.stdout, done.stderr


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--worker", required=True, type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--timeout-seconds", type=float, default=125)
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(64 * 1024 + 1)
        require(len(raw) <= 64 * 1024, "Request exceeds64KiB")
        report, _, _ = replay(strict_json(raw), worker=args.worker, python=args.python,
                              timeout_seconds=args.timeout_seconds)
    except (ValueError, OSError) as exc:
        report = {"schema": "hydra-independent-native-replay-v1", "status": "validator_error",
                  "proof_accepted": False, "error": str(exc)}
    print(json.dumps(report, ensure_ascii=False, allow_nan=False))
    return 0 if report["status"] in {"proved", "not_proved"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
