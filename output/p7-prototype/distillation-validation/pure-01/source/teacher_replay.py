"""Separately scheduled native admission of actual complete P7 continuations.

Prepared only until explicitly invoked by the root. There is no model, solver,
download, library theorem import, native search, retry or synthetic proof path.
Every child replays one entire original theorem with the unchanged kernel.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

from teacher_data import (APP, ROOT, HERE, KERNEL_SHA, SELECTION_SHA, Inputs,
    bootstrap, canonical, digest, load_inputs, require, source_pins, strict_json,
    validate_fresh_replay, write_new)

CPU_SECONDS = 20
CHILD_WALL_SECONDS = 25
BATCH_WALL_SECONDS = 600
RSS_BYTES = 2 * 1024**3
MAX_OUTPUT_BYTES = 256 * 1024**2


class ReplayDeadline(BaseException):
    pass


def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= 2 * 1024**2, "Replay record exceeds its byte bound.")
    write_new(path, raw)
    return {"path": Path(path).relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def replay_sources():
    result = source_pins()
    paths = list((APP / "native-v7/peano_lab").rglob("*.py"))
    paths += [APP / "certificate_codec.py", APP / "proof_cost.py", APP / "vampire_process.py", APP / "vampire_limits.py"]
    require(len(paths) <= 600, "Native replay source set unexpectedly grew.")
    for path in paths:
        require(path.is_file() and not path.is_symlink(), "Native replay source must be a regular file.")
        result[path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
    return result


def check_kernel():
    pins = {path.name: sha256(path.read_bytes()).hexdigest()
            for path in sorted((APP / "native-v7/peano_lab/kernel").glob("*.py"))}
    require(digest({"logic": "intuitionistic", "files": pins}) == KERNEL_SHA,
            "Fresh teacher replay must use the unchanged original native kernel.")


def worker(request_path, request_sha, output):
    inputs = Inputs()
    request = inputs.json(request_path.relative_to(ROOT).as_posix(), request_sha, 256 * 1024)
    require(request.get("schema") == "hydra-teacher-fresh-replay-request-v1"
            and request.get("selection_sha256") == SELECTION_SHA,
            "Unknown fresh replay request.")
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS + 1))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
    if sys.platform == "linux":
        resource.setrlimit(resource.RLIMIT_AS, (RSS_BYTES, RSS_BYTES))

    def alarm(signum, frame):
        raise ReplayDeadline("Fresh native replay reached its fixed wall/CPU ceiling.")

    def no_external(event, arguments):
        if event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.fork", "socket.connect", "socket.bind"}:
            raise RuntimeError("Fresh native admission cannot start advisers or use a network.")

    signal.signal(signal.SIGALRM, alarm)
    signal.signal(signal.SIGXCPU, alarm)
    signal.alarm(CHILD_WALL_SECONDS)
    sys.addaudithook(no_external)
    began = time.monotonic()
    result = {"schema": "hydra-teacher-fresh-replay-result-v1", "state_id": request["state_id"],
        "native_source_sha256": request["native_source_sha256"],
        "commands_sha256": digest(request["commands"]), "kernel_identity": KERNEL_SHA,
        "kernel_checked": False, "native_transitions_recorded": 0,
        "model_calls": 0, "solver_calls": 0, "search_performed": False, "automatic_retry": False}
    try:
        bootstrap(); check_kernel()
        from export_decisions import Inputs as NativeInputs, Reservation, NativeIdentity, HOLDOUT_SHA256
        from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
        from peano_lab.ui.prove import SurfaceCapabilities
        require(request["holdout"]["sha256"] == HOLDOUT_SHA256, "Held-out reservation changed.")
        reserved = Reservation(NativeInputs(ROOT).reference(request["holdout"]), NativeIdentity())
        require(reserved.reason(request["theorem"], request["family"], request["template_family"], request["case_id"]) is None,
                "Reserved theorem/template cannot enter fresh teacher admission.")
        commands = request["commands"]
        require(type(commands) is list and 1 <= len(commands) <= 96
                and all(type(c) is str and c.isprintable() and c and len(c.encode()) <= 4096
                        and ";" not in c and c.split()[0] in MODEL_V1_COMMANDS - {"use"} for c in commands),
                "Fresh replay accepts only a bounded complete ordinary no-import script.")
        authority = SurfaceCapabilities(label="hydra-authority-no-imports-v1",
            allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())

        def progress(line):
            row = json.loads(line)
            if type(row.get("step")) is int:
                result["native_transitions_recorded"] += 1

        replay = run_proof(request["theorem"], tuple(commands), capabilities=authority,
            classical=False, on_error="stop", request_id="teacher-admit-" + request["state_id"][:16],
            trace_sink=progress, trace_byte_limit=2 * 1024**2).to_dict()
        result["replay"] = replay
        require(replay["status"] == "proved" and replay["kernel_checked"] is True and replay["goals"] == [],
                "Fresh original-theorem replay did not produce a checked proof.")
        for row in replay["trace"][:-1]:
            require(reserved.goals_reason(row["goals_before"] + row["goals_after"]) is None,
                    "Fresh proof crosses a reserved or unavailable intermediate state.")
        result.update(status="verified", kernel_checked=True)
    except (ReplayDeadline, MemoryError, TimeoutError) as error:
        result.update(status="resource_limit", error_type=type(error).__name__, error=str(error)[:512])
    except Exception as error:
        result.update(status="rejected", error_type=type(error).__name__, error=str(error)[:512])
    finally:
        signal.alarm(0)
    result["elapsed_seconds"] = time.monotonic() - began
    result["resource_limits"] = {"cpu_seconds": CPU_SECONDS, "wall_seconds": CHILD_WALL_SECONDS,
        "sampled_rss_bytes": RSS_BYTES, "network_and_subprocesses_forbidden": True}
    save(output, result)
    return 0


def child_rss(process):
    if process.poll() is not None:
        return None
    try:
        if sys.platform == "darwin":
            sys.path.insert(0, str(APP))
            from vampire_process import _owned_child_rss
            return _owned_child_rss(process)
        if sys.platform == "linux":
            import re
            text = Path(f"/proc/{process.pid}/status").read_text()
            match = re.search(r"^VmRSS:\s+(\d+) kB$", text, flags=re.M)
            require(match is not None, "Owned native replay RSS is unavailable.")
            return int(match[1]) * 1024
        raise OSError("No reviewed owned-child RSS interface for this platform.")
    except (OSError, ValueError):
        if process.poll() is not None:
            return None
        raise


def run_child(request, *, output, batch_deadline):
    output.mkdir(exist_ok=False)
    request_pin = save(output / "request.json", request)
    result_path, log_path = output / "result.json", output / "child.log"
    process = None
    began, peak, stopped = time.monotonic(), 0, None
    error, result, code = None, None, None
    try:
        with log_path.open("xb") as stream:
            require(time.monotonic() < batch_deadline - CHILD_WALL_SECONDS - 5,
                    "Insufficient bounded batch time for another complete replay attempt.")
            command = [sys.executable, "-B", str(Path(__file__)), "worker",
                "--request", str(output / "request.json"), "--request-sha256", request_pin["sha256"],
                "--output", str(result_path)]
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
            while process.poll() is None:
                rss = child_rss(process)
                if rss is not None:
                    peak = max(peak, rss)
                if peak > RSS_BYTES:
                    stopped = "owned_child_rss_limit"
                elif time.monotonic() - began > CHILD_WALL_SECONDS + 5:
                    stopped = "owned_child_wall_limit"
                elif time.monotonic() >= batch_deadline:
                    stopped = "batch_wall_limit"
                elif os.fstat(stream.fileno()).st_size > 1024**2:
                    stopped = "owned_child_log_limit"
                if stopped:
                    process.kill()
                    break
                time.sleep(0.02)
            code = process.wait(timeout=5)
        if result_path.is_file():
            result = Inputs().json(result_path.relative_to(ROOT).as_posix())
    except BaseException as failure:
        error = failure
        stopped = stopped or type(failure).__name__
    finally:
        if process is not None:
            try:
                if process.poll() is None:
                    process.kill()
                code = process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired) as failure:
                error = error or failure
                stopped = stopped or "owned_child_cleanup_failed"
        result_sha = None if result is None else sha256(result_path.read_bytes()).hexdigest()
        receipt = {"actual_exit_code": code, "quiescent": process is None or process.poll() is not None,
            "launched": process is not None, "pid": None if process is None else process.pid,
            "stopped_for": stopped, "child_result_sha256": result_sha,
            "elapsed_seconds": time.monotonic() - began, "sampled_peak_rss_bytes": peak,
            "automatic_retry": False}
        execution = save(output / "execution.json", receipt)
    if error is not None:
        raise error
    result_pin = None if result is None else {"path": result_path.relative_to(ROOT).as_posix(),
        "sha256": result_sha, "bytes": result_path.stat().st_size}
    status = result.get("status", "rejected") if result is not None and code == 0 and stopped is None else "resource_limit"
    return {"state_id": request["state_id"], "status": status, "result": result_pin, "execution": execution}, result


def _batch(args):
    before = replay_sources()
    began = time.monotonic()
    deadline = began + BATCH_WALL_SECONDS
    loaded = load_inputs(args.input_spec, expected_sha256=args.input_sha256, should_stop=lambda: time.monotonic() >= deadline)
    inputs, spec, base, base_manifest, files, selection, candidates, campaign = loaded
    output = args.output.resolve()
    require(output.is_relative_to(ROOT) and not output.exists(), "Use one new project-local fresh replay directory.")
    output.mkdir(parents=True, exist_ok=False)
    save(output / "request.json", {"input_spec": inputs.pins[args.input_spec], "source_pins": before,
        "selection_sha256": SELECTION_SHA, "positive_teacher_continuations": len(candidates),
        "batch_wall_seconds": BATCH_WALL_SECONDS, "automatic_retry": False,
        "model_calls": 0, "solver_calls": 0})
    records, failure = [], None
    try:
        for index, candidate in enumerate(candidates):
            require(sum(p.stat().st_size for p in output.rglob("*") if p.is_file()) + 4 * 1024**2 <= MAX_OUTPUT_BYTES,
                    "Fresh replay output budget exhausted.")
            state, native = candidate["state"], candidate["native"]
            request = {"schema": "hydra-teacher-fresh-replay-request-v1", "state_id": state["id"],
                "selection_sha256": SELECTION_SHA, "native_source_sha256": candidate["source"]["sha256"],
                "theorem": state["theorem"], "commands": native["commands"],
                "family": state["family"], "template_family": state["template_family"],
                "case_id": state["case_id"], "holdout": selection["holdout"]}
            item, result = run_child(request, output=output / f"{index:03d}-{state['id'][:16]}", batch_deadline=deadline)
            if item["status"] == "verified":
                validate_fresh_replay(result, candidate)
            records.append(item)
            print(json.dumps({"state_id": state["id"], "fresh_replay_status": item["status"]}), flush=True)
    except BaseException as error:
        failure = {"type": type(error).__name__, "detail": str(error)[:512]}
        raise
    finally:
        signal.alarm(0)
        after = replay_sources()
        completed = failure is None and len(records) == len(candidates) and before == after
        manifest = {"schema": "hydra-teacher-fresh-replay-batch-v1", "completed": completed,
            "input_spec_sha256": args.input_sha256, "selection_sha256": SELECTION_SHA,
            "source_pins_before": before, "source_pins_after": after, "sources_unchanged": before == after,
            "records": records, "failure": failure, "positive_teacher_continuations": len(candidates),
            "fresh_verified": sum(row["status"] == "verified" for row in records),
            "model_calls": 0, "solver_calls": 0, "search_performed": False,
            "automatic_retry": False, "elapsed_seconds": time.monotonic() - began}
        save(output / "manifest.json", manifest)
    return 0 if completed else 1


def batch(args):
    """Signals unwind through the owned-child kill/reap finally block."""
    previous = {}

    def cancel(signum, frame):
        raise ReplayDeadline("Fresh native batch reached its stop/cancel boundary.")

    try:
        for signum in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
            previous[signum] = signal.signal(signum, cancel)
        signal.alarm(BATCH_WALL_SECONDS)
        return _batch(args)
    finally:
        signal.alarm(0)
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    parent = sub.add_parser("batch")
    parent.add_argument("--input-spec", required=True)
    parent.add_argument("--input-sha256", required=True)
    parent.add_argument("--output", type=Path, required=True)
    child = sub.add_parser("worker")
    child.add_argument("--request", type=Path, required=True)
    child.add_argument("--request-sha256", required=True)
    child.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    return worker(args.request, args.request_sha256, args.output) if args.mode == "worker" else batch(args)


if __name__ == "__main__":
    raise SystemExit(main())
