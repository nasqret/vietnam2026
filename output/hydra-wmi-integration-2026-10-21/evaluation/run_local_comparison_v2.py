#!/usr/bin/env python3
"""One serial local arm. Supervisor owns deadlines; only a child loads MLX.

The input bundle deliberately contains no expected answers or reference proofs.
This additive continuation reuses the authenticated earlier historical18-case
arm, keeps every original app/input/work pin, and loads a separately pinned
newer provider. The original harness and seal remain unchanged.
Use `seal` once before inference, then `run` once for the explicit newest arm.
A killed/failed arm is incomplete and is never automatically retried.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

ARMS = {"wmi_c6_long_vanilla11_step16384": "wmi-c6-long-vanilla11"}
BASELINE_SPEC_SHA = "16d9ceb2aa8f08111a7f273a7ef90c737f725074d903c3169818aea7ce5f46ee"
CHECKPOINT_SHA = "177501bf7b662a210b6cf6887844a282365437c781e53138ad5495f02c620a06"
CONTINUATION_SHA = "49b68a29dd85beaa72427a12a456d53d9045d68f0f6c7302f254e2e5de8ae1d8"
LIMITS = {"max_actions": 128, "max_new_tokens": 128, "max_total_decision_tokens": 16384,
          "max_context_tokens": 6144, "wall_seconds": 300.0}
PHASE_SECONDS = {"load": 120, "case": 360, "finalize": 60, "between": 15, "done": 5}
APP_FILES = ("model_selection.py", "wmi_model_runtime.py", "wmi_model_config.json",
             "wmi_candidate_core.py", "wmi_mlx_loader.py", "model_runtime.py",
             "sequential_native.py", "sequential_native_sources.json", "sequential_runner.py")
INPUT_PINS = {"PRIMARY_INPUTS_12.json": "a1ec8fcff63d13c28e5b53190428440009c85c1ef527b7c3a4713b6effec940a",
              "REGRESSION_INPUTS_6.json": "90cb60699e0cffcc04c4541310ac41460e14535d6fbe9ffadbf7ca9adf2f355a"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, *, maximum=16 * 1024**2):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= maximum, "Unsafe or oversized input: " + str(path))
    raw = path.read_bytes()
    require(len(raw) <= maximum, "Input grew beyond its byte bound")
    return raw


def pin(path):
    raw = read(path)
    return {"bytes": len(raw), "sha256": digest(raw)}


def read_json(path, expected=None):
    raw = read(path)
    require(expected is None or digest(raw) == expected, "Pinned JSON changed: " + str(path))
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def bad(_):
        raise ValueError("Nonfinite JSON")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def save(path, data):
    raw = (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= 16 * 1024**2, "Result exceeds its byte bound")
    with Path(path).open("xb") as stream:
        stream.write(raw)
    return {"bytes": len(raw), "sha256": digest(raw)}


def emit(event):
    print(json.dumps(event, ensure_ascii=False, separators=(",", ":"), allow_nan=False), flush=True)


def provider_manifest(path, checksum):
    manifest = read_json(path, checksum)
    require(manifest["schema"] == "hydra-newest-local-provider-v1"
            and manifest["selection_id"] == "wmi-c6-long-vanilla11"
            and manifest["checkpoint_sha256"] == CHECKPOINT_SHA
            and manifest["selected_step"] == 16384, "Wrong newest locked candidate")
    entry = manifest["entrypoint"]
    require(Path(entry["path"]).is_absolute() and Path(entry["path"]).suffix == ".py",
            "Expected explicit absolute provider entrypoint")
    require(0 < len(manifest["files"]) <= 20, "Unbounded additive provider inventory")
    require(len({item["path"] for item in manifest["files"]}) == len(manifest["files"]),
            "Duplicate additive provider source")
    require(entry in manifest["files"], "Entrypoint missing from additive source inventory")
    for item in manifest["files"]:
        require(Path(item["path"]).is_absolute(), "Additive source path must be explicit")
        require(pin(item["path"]) == {"bytes": item["bytes"], "sha256": item["sha256"]},
                "Additive provider/config changed: " + item["path"])
    return manifest


def make_spec(args):
    require(args.baseline_spec_sha256 == BASELINE_SPEC_SHA, "Uncommitted historical baseline")
    previous = read_json(args.baseline_spec, BASELINE_SPEC_SHA)
    require(previous["schema"] == "hydra-local-matched-execution-v1"
            and previous["limits"] == LIMITS and previous["phase_hard_seconds"] == PHASE_SECONDS,
            "Historical work bounds differ")
    require(pin(previous["runner"]["path"]) == {k:previous["runner"][k] for k in ("bytes", "sha256")},
            "Original historical harness changed")
    here = Path(__file__).resolve().parent
    continuation = here / "NEWEST_CONTINUATION_PRECOMMIT.json"
    read_json(continuation, CONTINUATION_SHA)
    manifest = provider_manifest(args.provider_manifest, args.provider_manifest_sha256)
    spec = {**previous, "schema": "hydra-local-matched-execution-v2",
            "runner": {"path": str(Path(__file__).resolve()), **pin(__file__)}, "arms": ARMS,
            "baseline_spec": {"path": str(Path(args.baseline_spec).resolve()), **pin(args.baseline_spec)},
            "continuation": {"path": str(continuation), **pin(continuation)},
            "provider_manifest": {"path": str(Path(args.provider_manifest).resolve()), **pin(args.provider_manifest)},
            "provider_identity": {key:manifest[key] for key in ("selection_id", "checkpoint_sha256", "selected_step", "entrypoint", "files")},
            "trained_protocol_differences": {
                "historical_local_mlx": previous["trained_protocol_differences"]["historical_local_mlx"],
                "wmi_c6_long_vanilla11_step16384": "model-v3 compact full-library247 all-goal prompt; unmasked greedy generation; authenticated newer long seed11 adapter; current native no-import execution"}}
    repo = Path(spec["repo_root"])
    for name, expected in spec["app_files"].items():
        require(pin(repo / "hydra-playground" / name) == expected,
                "Original app changed; cannot reuse historical arm: " + name)
    result = save(args.output, spec)
    emit({"type": "sealed", "path": str(Path(args.output).resolve()), **result})


def validate_spec(path, checksum):
    spec = read_json(path, checksum)
    require(spec["schema"] == "hydra-local-matched-execution-v2" and spec["arms"] == ARMS
            and spec["limits"] == LIMITS and spec["phase_hard_seconds"] == PHASE_SECONDS,
            "Execution contract changed")
    require(spec["automatic_retry"] is False and spec["automatic_fallback"] is False
            and spec["shared_load_outside_case_time"] is True, "Execution timing/retry differs")
    require(spec["runner"] == {"path": str(Path(__file__).resolve()), **pin(__file__)}, "Harness changed")
    old = read_json(spec["baseline_spec"]["path"], BASELINE_SPEC_SHA)
    require(spec["baseline_spec"]["sha256"] == BASELINE_SPEC_SHA
            and all(spec[key] == old[key] for key in ("repo_root", "runtime_python", "native_source_root",
                                                     "app_files", "inputs", "limits", "phase_hard_seconds")),
            "Newest continuation drifted from historical input/runtime/work contract")
    read_json(spec["continuation"]["path"], CONTINUATION_SHA)
    manifest = provider_manifest(spec["provider_manifest"]["path"], spec["provider_manifest"]["sha256"])
    require(spec["provider_identity"] == {key:manifest[key] for key in ("selection_id", "checkpoint_sha256", "selected_step", "entrypoint", "files")},
            "Provider manifest differs from execution identity")
    repo = Path(spec["repo_root"])
    require(set(spec["app_files"]) == set(APP_FILES), "App source inventory differs")
    for name, expected in spec["app_files"].items():
        require(pin(repo / "hydra-playground" / name) == expected, "App source changed: " + name)
    cases = []
    for record in spec["inputs"]:
        path = Path(record["path"])
        require(path.name in INPUT_PINS and record["sha256"] == INPUT_PINS[path.name], "Uncommitted model inputs")
        value = read_json(path, record["sha256"])
        require([row["id"] for row in value["cases"]] == record["case_ids"], "Input order differs")
        for row in value["cases"]:
            require(set(row) == {"id", "theorem"} and type(row["theorem"]) is str,
                    "Model inputs must contain only neutral ID and theorem")
            cases.append({**row, "panel_id": value["panel_id"], "input_file_sha256": record["sha256"]})
    require(len(cases) == 18 and len({row["id"] for row in cases}) == 18, "Expected all18 cases exactly once")
    return spec, cases


def child_main(args):
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == "darwin", "Use existing Mac runtime Python with -I -B")
    spec, cases = validate_spec(args.spec, args.spec_sha256)
    out = Path(args.output).resolve()
    require(out.is_dir(), "Supervisor must create output directory")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path.insert(0, str(Path(spec["repo_root"]) / "hydra-playground"))
    import sequential_native
    import sequential_runner

    def offline(event, values):
        if event.startswith("socket."):
            raise PermissionError("Matched local comparison is offline")
        if event == "subprocess.Popen":
            require(sequential_native.authorized_spawn(*values), "Only exact independent native replay may spawn")
        elif event.startswith("subprocess.") or event in {"os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec"}:
            raise PermissionError("No other process or model is authorized")
        if event == "open" and isinstance(values[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(values[0])).resolve()
            require(path.name not in {"PRIVATE_EXPECTATIONS.json", "proofs.jsonl", "PANEL_COMMITMENT.json"}, "Model process may not read gold/selection evidence")
            mode, flags = values[1], values[2]
            writable = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writable:
                require(path.is_relative_to(out), "Model process cannot write outside its new result directory")
    sys.addaudithook(offline)
    started = time.monotonic()
    shared = None
    report = {"schema": "hydra-local-matched-arm-v1", "arm": args.arm, "selection_id": ARMS[args.arm],
              "spec_sha256": args.spec_sha256, "evidence_kind": "fresh_local_mlx_inference",
              "status": "started", "limits": LIMITS, "phase_hard_seconds": PHASE_SECONDS,
              "shared_load_outside_case_time": True, "cases": [], "final_custody": {"status": "not_run"}}
    try:
        native = sequential_native.NativeHost(spec["native_source_root"])
        entrypoint = spec["provider_identity"]["entrypoint"]["path"]
        module_spec = importlib.util.spec_from_file_location("hydra_newest_additive_provider", entrypoint)
        require(module_spec is not None and module_spec.loader is not None, "Cannot import pinned additive provider")
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_spec.name] = module
        module_spec.loader.exec_module(module)
        shared = module.create_policy(native.capabilities, lambda _: None)
        require(shared.selection_id == ARMS[args.arm], "Loaded provider selection differs")
        report["load_identity"] = shared.prepare()
        report["load_wall_seconds"] = time.monotonic() - started
        emit({"type": "loaded", "arm": args.arm, "seconds": report["load_wall_seconds"]})
        for row in cases:
            emit({"type": "case_start", "id": row["id"]})
            case_started = time.monotonic()
            case = shared.new_case(deadline_monotonic=case_started + LIMITS["wall_seconds"],
                                   max_calls=LIMITS["max_actions"],
                                   max_total_decision_tokens=LIMITS["max_total_decision_tokens"])
            host = sequential_native.NativeHost(spec["native_source_root"])
            result = sequential_runner.run(row["theorem"], native=host, provider_factory=case.provider_factory,
                prompt_renderer=case.prompt_renderer, limits=sequential_runner.Limits(**LIMITS))
            provider = case.report()
            require(result["actual_model_calls"] == provider["actual_model_calls"]
                    and result["actual_decision_tokens"] == provider["generated_token_slots"], "Runner/provider actual work differs")
            record = {"schema": "hydra-local-matched-case-v1", "arm": args.arm, "id": row["id"],
                      "panel_id": row["panel_id"], "input_file_sha256": row["input_file_sha256"],
                      "input_theorem_sha256": digest(row["theorem"].encode()),
                      "input_theorem": row["theorem"], "case_wall_seconds": time.monotonic() - case_started,
                      "result": result, "provider": provider}
            name = row["id"] + ".json"
            result_pin = save(out / name, record)
            summary = {"id": row["id"], "path": name, **result_pin,
                       "status": result["status"], "proved": result["proved"],
                       "actual_model_calls": result["actual_model_calls"],
                       "actual_decision_tokens": result["actual_decision_tokens"],
                       "case_wall_seconds": record["case_wall_seconds"]}
            report["cases"].append(summary)
            emit({"type": "case_done", **summary})
        report["status"] = "completed"
    except Exception as error:
        report.update(status="error", error_type=type(error).__name__, error=str(error))
    finally:
        emit({"type": "finalize_start"})
        final_started = time.monotonic()
        try:
            if shared is not None:
                report["shared_loader_final_report"] = shared.finalize()
                report["shared_loader_report_scope"] = "One-time load/custody only; all actual per-case counters are stored in case records."
            validate_spec(args.spec, args.spec_sha256)
            report["final_custody"] = {"status": "completed", "wall_seconds": time.monotonic() - final_started}
        except Exception as error:
            report.update(status="error", final_custody={"status": "error", "error_type": type(error).__name__, "error": str(error)})
        report["wall_seconds"] = time.monotonic() - started
        result_pin = save(out / "arm.json", report)
        emit({"type": "arm_done", "status": report["status"], "path": "arm.json", **result_pin})
    return 0 if report["status"] == "completed" else 1


def supervise(args):
    spec, cases = validate_spec(args.spec, args.spec_sha256)
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    command = [spec["runtime_python"], "-I", "-B", str(Path(__file__).resolve()), "child", "--arm", args.arm,
               "--spec", str(Path(args.spec).resolve()), "--spec-sha256", args.spec_sha256, "--output", str(out)]
    started = time.monotonic()
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True, bufsize=0)
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ, "stdout")
    selector.register(child.stderr, selectors.EVENT_READ, "stderr")
    phase, phase_deadline, index, active = "load", started + PHASE_SECONDS["load"], 0, None
    stdout, stderr, buffer, events, problem = bytearray(), bytearray(), bytearray(), [], None
    arm_done = None
    try:
        while selector.get_map():
            if time.monotonic() > phase_deadline:
                raise TimeoutError("External " + phase + " deadline")
            for key, _ in selector.select(timeout=min(0.25, max(0, phase_deadline - time.monotonic()))):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                target = stdout if key.data == "stdout" else stderr
                target.extend(block)
                require(len(target) <= 1024**2, "Child stream exceeds1MiB")
                if key.data != "stdout":
                    continue
                buffer.extend(block)
                while b"\n" in buffer:
                    raw, _, tail = buffer.partition(b"\n")
                    buffer[:] = tail
                    event = json.loads(raw)
                    kind = event["type"]
                    if kind == "loaded":
                        require(phase == "load", "Unexpected load completion")
                        phase = "between"
                    elif kind == "case_start":
                        require(phase == "between" and index < len(cases) and event["id"] == cases[index]["id"], "Case order/repetition differs")
                        active, phase = event["id"], "case"
                    elif kind == "case_done":
                        require(phase == "case" and event["id"] == active, "Unexpected case completion")
                        require(pin(out / event["path"]) == {"bytes": event["bytes"], "sha256": event["sha256"]}, "Case receipt changed")
                        index, active, phase = index + 1, None, "between"
                    elif kind == "finalize_start":
                        require(phase in {"load", "case", "between"}, "Unexpected finalization")
                        phase = "finalize"
                    elif kind == "arm_done":
                        require(phase == "finalize", "Unexpected arm completion")
                        require(pin(out / "arm.json") == {"bytes": event["bytes"], "sha256": event["sha256"]}, "Arm receipt changed")
                        arm_done, phase = event, "done"
                    else:
                        raise ValueError("Unknown child event")
                    phase_deadline = time.monotonic() + PHASE_SECONDS[phase]
                    event = {**event, "supervisor_wall_seconds": time.monotonic() - started}
                    events.append(event)
                    emit(event)
        require(not buffer, "Truncated child event")
        child.wait(timeout=5)
    except BaseException as error:
        problem = {"type": type(error).__name__, "message": str(error), "phase": phase, "active_case": active}
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=5)
    finally:
        selector.close()
        for name, data in (("child.stdout.jsonl", stdout), ("child.stderr.txt", stderr)):
            with (out / name).open("xb") as stream:
                stream.write(data)
    complete = problem is None and child.returncode == 0 and index == 18 and arm_done is not None and arm_done["status"] == "completed"
    observation = {"schema": "hydra-local-matched-supervisor-v1", "arm": args.arm,
                   "spec_sha256": args.spec_sha256, "command": command, "actual_pid": child.pid,
                   "actual_exit_code": child.returncode, "status": "completed" if complete else "incomplete",
                   "completed_cases": index, "required_cases": 18, "automatic_retry": False,
                   "phase_hard_seconds": PHASE_SECONDS, "wall_seconds": time.monotonic() - started,
                   "problem": problem, "arm_receipt": arm_done, "events": events,
                   "stdout": pin(out / "child.stdout.jsonl"), "stderr": pin(out / "child.stderr.txt")}
    result_pin = save(out / "supervisor.json", observation)
    emit({"type": "supervisor_done", "status": observation["status"], "path": str(out / "supervisor.json"), **result_pin})
    return 0 if complete else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="mode", required=True)
    seal = commands.add_parser("seal", allow_abbrev=False)
    seal.add_argument("--baseline-spec", required=True)
    seal.add_argument("--baseline-spec-sha256", required=True)
    seal.add_argument("--provider-manifest", required=True)
    seal.add_argument("--provider-manifest-sha256", required=True)
    seal.add_argument("--output", required=True)
    for mode in ("run", "child"):
        command = commands.add_parser(mode, allow_abbrev=False)
        command.add_argument("--arm", required=True, choices=ARMS)
        command.add_argument("--spec", required=True)
        command.add_argument("--spec-sha256", required=True)
        command.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.mode == "seal":
        make_spec(args)
        return 0
    return child_main(args) if args.mode == "child" else supervise(args)


if __name__ == "__main__":
    raise SystemExit(main())
