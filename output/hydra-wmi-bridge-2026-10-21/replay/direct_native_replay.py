#!/usr/bin/env python3
"""Explicit isolated CPU profile for exact saved WMI proof requests.

Not the public Hydra endpoint. This profile admits larger original formulas
without modifying the public protocol, original native source or checker.
Only requests in the externally pinned 50-entry allowlist can execute.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
WORKER = ROOT / "hydra-playground/worker.py"
WORKER_SHA = "e7923426cf39a68719fc79f8efc1db0cf016edf03bd79d248a94ac06235de951"
HELPER = Path(__file__).resolve().with_name("replay_saved_successes.py")
HELPER_SHA = "2737470762c70a9a44115d0ef4437809ad69854bfcd41a61d96706e7acc3ad11"
KERNEL_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
CAPABILITY_SHA = "8edaaffa8edf1f6d8b187ba3ada5e87c8219374ef556031afbc103948619b69f"
PROFILE = {"id": "hydra-wmi-saved-proof-cpu-diagnostic-v1", "max_binders": 64,
           "max_ast_nodes": 1024, "max_ast_depth": 128, "max_formula_bytes": 4096,
           "max_actions": 128, "max_action_bytes": 512, "max_numeral": 64,
           "trace_bytes": 2 * 1024**2, "output_bytes": 4 * 1024**2,
           "per_case_wall_seconds": 30, "per_case_cpu_seconds": 30,
           "batch_wall_seconds": 900, "observed_rss_bytes": 2 * 1024**3,
           "parallel_children": 1, "automatic_retry": False,
           "execution_authority": "hydra-playground-native-v1/no-imports"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()


def descriptor(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha(raw)}


def strict_json(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            require(key not in obj, "duplicate JSON field")
            obj[key] = value
        return obj

    def bad_constant(_):
        raise ValueError("non-finite JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_constant)


def load_module(name, path, expected):
    require(descriptor(path)["sha256"] == expected, "module source pin differs")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_inputs(path, expected):
    identity = descriptor(path)
    require(identity["bytes"] <= 1024**2 and identity["sha256"] == expected, "input pin differs")
    value = strict_json(path.read_bytes())
    require(value["schema"] == "hydra-wmi-direct-native-inputs-v1"
            and value["native_root"] == str(SOURCE) and len(value["allowlist"]) == 50,
            "unexpected direct native input contract")
    ids = [x["id"] for x in value["allowlist"]]
    require(len(set(ids)) == 50 and len(value["selected_ids"]) == 27
            and len(set(value["selected_ids"])) == 27 and set(value["selected_ids"]) <= set(ids)
            and value["positive_replay_control_id"] in value["selected_ids"], "input selection differs")
    return value, identity


def verify_native_inventory(inputs):
    expected = inputs["native_python_files"]
    actual_paths = {str(p.relative_to(SOURCE)) for p in (SOURCE / "peano-lab/py/peano_lab").rglob("*.py")}
    require(actual_paths == set(expected) and 1 <= len(expected) <= 512, "native Python inventory differs")
    for relative, identity in expected.items():
        p = SOURCE / relative
        require(not p.is_symlink() and p.is_file(), "native source must be a regular file")
        raw = p.read_bytes()
        require(len(raw) == identity["bytes"] and sha(raw) == identity["sha256"],
                "native source changed: " + relative)


def audit_formula(formula):
    from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, Or
    from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
    stack, count, deepest, boundest = [(formula, 1, 0)], 0, 0, 0
    while stack:
        node, depth, binders = stack.pop()
        count += 1
        deepest, boundest = max(deepest, depth), max(boundest, binders)
        require(count <= PROFILE["max_ast_nodes"] and depth <= PROFILE["max_ast_depth"],
                "outside explicit diagnostic AST resource bounds")
        kind = type(node)
        if kind is Var:
            require(type(node.index) is int and 0 <= node.index < binders, "formula is not closed")
            children = ()
        elif kind in (Zero, Bot):
            children = ()
        elif kind is Succ:
            children = (node.term,)
        elif kind in (Add, Mul, Eq, And, Or, Imp):
            children = (node.left, node.right)
        elif kind in (Exists, Forall):
            binders += 1
            require(binders <= PROFILE["max_binders"], "outside explicit diagnostic binder bound")
            boundest = max(boundest, binders)
            children = (node.body,)
        else:
            raise ValueError("unknown native AST constructor")
        stack.extend((child, depth + 1, binders) for child in children)
    return {"ast_nodes": count, "ast_depth": deepest, "maximum_bound_variables": boundest}


def run_child(args):
    require(sys.flags.isolated and sys.dont_write_bytecode, "child requires isolated Python without bytecode")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (PROFILE["output_bytes"], PROFILE["output_bytes"]))
    started = time.monotonic()

    def deadline(*_):
        raise TimeoutError("explicit diagnostic per-case deadline")
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, PROFILE["per_case_wall_seconds"])
    try:
        inputs, identity = load_inputs(args.inputs, args.inputs_sha256)
        require(args.case_id in inputs["selected_ids"], "case is not in the explicit27-entry selection")
        item = next(x for x in inputs["allowlist"] if x["id"] == args.case_id)
        request = item["request"]
        helper = load_module("hydra_saved_success_replay", HELPER, HELPER_SHA)
        helper.load_validator().check_request(request)
        require(0 < len(request["tactics"]) <= PROFILE["max_actions"], "diagnostic action limit")
        verify_native_inventory(inputs)
        worker = load_module("worker", WORKER, WORKER_SHA)
        worker.kernel_status()
        worker.install_guard("replay")
        sys.path[:0] = [str(SOURCE / "peano-lab/py"), str(SOURCE)]
        from peano_lab.batch import MODEL_V1_COMMANDS, capability_sha256, run_proof
        from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
        from peano_lab.ui.prove import SurfaceCapabilities, oversized_numeral, surface_success_trace_tactic
        formula, names = parse_formula_with_names(request["theorem"])
        require(not names and pretty_formula(formula, list(names)) == request["theorem"],
                "diagnostic requires the exact canonical closed original theorem")
        admission = audit_formula(formula)
        require(all(oversized_numeral(text, maximum=64) is None
                    for text in [request["theorem"], *request["tactics"]]), "diagnostic numeral bound")
        caps = SurfaceCapabilities(label="hydra-playground-native-v1", allowed_commands=MODEL_V1_COMMANDS,
                                   allowed_theorems=frozenset())
        require(capability_sha256(caps) == CAPABILITY_SHA, "no-imports authority changed")
        result = run_proof(request["theorem"], request["tactics"],
                           request_id="saved-wmi-" + sha(canonical(request))[:24], classical=False,
                           on_error="stop", capabilities=caps, trace_byte_limit=PROFILE["trace_bytes"])
        native = result.to_dict(include_trace=True)
        require(native["theorem"] == request["theorem"] and native["classical"] is False
                and native["environment_sha256"] == CAPABILITY_SHA, "native identity differs")
        proved = native["status"] == "proved"
        require(native["kernel_checked"] is proved, "native completion flags disagree")
        if proved:
            rows = [x for x in native["trace"] if "v" in x]
            require(not native["goals"] and native["trace"][-1].get("qed") is True
                    and native["trace"][-1].get("theorem") == request["theorem"]
                    and native["trace"][-1].get("tactic_count") == len(request["tactics"])
                    and native["tactics_requested"] == native["tactics_applied"] == len(request["tactics"])
                    and native["failed_tactics"] == 0 and len(rows) == len(request["tactics"]),
                    "native completion accounting differs")
            for index, (row, action) in enumerate(zip(rows, request["tactics"]), 1):
                require(row["step"] == index and row["status"] == "ok" and row["error"] is None
                        and row["tactic"] == surface_success_trace_tactic(action), "native action binding differs")
        verify_native_inventory(inputs)
        for name, module in tuple(sys.modules.items()):
            if name == "peano_lab" or name.startswith("peano_lab."):
                require(Path(module.__file__).resolve().is_relative_to(SOURCE), "foreign cached native module")
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        require(peak <= PROFILE["observed_rss_bytes"] and time.monotonic() - started < 30,
                "diagnostic resource bound exceeded")
        event = {"type": "result", "profile": PROFILE, "input_identity": identity,
                 "source_id": item["id"], "request_sha256": sha(canonical(request)),
                 "source_record_sha256": item["source_record_sha256"], "admission": admission,
                 "proof_accepted_in_diagnostic_profile": proved, "native_result": native,
                 "public_worker_executed": False, "kernel_source_commit": KERNEL_COMMIT,
                 "seconds": time.monotonic() - started, "peak_rss_bytes": peak}
        raw = canonical(event)
        require(len(raw) <= PROFILE["output_bytes"], "diagnostic output bound exceeded")
        sys.stdout.buffer.write(raw + b"\n")
        return 0
    except Exception as exc:
        print(json.dumps({"type": "error", "profile_id": PROFILE["id"],
                          "error_type": type(exc).__name__, "error": str(exc)[:2048]}))
        return 2
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def write_json(path, value):
    with path.open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def run_parent(args):
    require(args.output is not None and args.case_id is None, "parent needs a fresh output directory")
    inputs, identity = load_inputs(args.inputs, args.inputs_sha256)
    helper = load_module("hydra_saved_success_replay", HELPER, HELPER_SHA)
    validator = helper.load_validator()
    proof_path = Path(inputs["source_proofs"]["path"])
    require(descriptor(proof_path) == inputs["source_proofs"], "source proof report changed")
    records = [strict_json(line) for line in proof_path.read_bytes().splitlines()]
    by_id = {r["id"]: r for r in records}
    prepared = {}
    for item in inputs["allowlist"]:
        record = by_id[item["id"]]
        require(sha(canonical(record)) == item["source_record_sha256"], "allowlist source record differs")
        request, transitions = helper.validate_success(record, inputs["source_evaluated_checkpoint_sha256"], validator)
        require(request == item["request"], "allowlist raw request differs")
        if item["id"] in inputs["selected_ids"]:
            prepared[item["id"]] = (request, transitions)
    public_summary_path = Path(inputs["public_replay_summary"]["path"])
    require(descriptor(public_summary_path) == inputs["public_replay_summary"], "public replay evidence changed")
    public_summary = strict_json(public_summary_path.read_bytes())
    public = {x["source_id"]: x for x in public_summary["results"]}
    require({k for k in prepared if not public[k]["proof_accepted"]} ==
            set(inputs["selected_ids"]) - {inputs["positive_replay_control_id"]},
            "selection must be26 public-profile failures plus one successful replay control")
    verify_native_inventory(inputs)
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {"schema": "hydra-wmi-direct-native-request-v1", "inputs": identity,
                "harness": descriptor(Path(__file__).resolve()), "helper": descriptor(HELPER),
                "worker_guard": descriptor(WORKER), "profile": PROFILE,
                "selected_ids": inputs["selected_ids"], "no_model_inference": True,
                "public_worker_changed": False}
    write_json(args.output / "REQUESTS.json", manifest)
    started, outcomes = time.monotonic(), []
    for index, case_id in enumerate(inputs["selected_ids"], 1):
        remaining = PROFILE["batch_wall_seconds"] - (time.monotonic() - started)
        if remaining <= 0:
            break
        request, expected = prepared[case_id]
        directory = args.output / f"case-{index:02d}-{sha(case_id.encode())[:12]}"
        directory.mkdir()
        command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--child",
                   "--inputs", str(args.inputs.resolve()), "--inputs-sha256", args.inputs_sha256,
                   "--case-id", case_id]
        wall = time.monotonic()
        try:
            done = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=min(30, remaining), check=False)
            code, stdout, stderr = done.returncode, done.stdout, done.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
        (directory / "child.stdout.jsonl").write_bytes(stdout)
        (directory / "child.stderr.txt").write_bytes(stderr)
        try:
            events = [strict_json(line) for line in stdout.splitlines()]
            event = events[0] if len(events) == 1 and isinstance(events[0], dict) else {}
        except (ValueError, UnicodeError):
            event = {"type": "unreadable-child-output", "error": "child output is not one complete JSON event"}
        native = event.get("native_result") or {}
        accepted = code == 0 and event.get("type") == "result" and event.get("proof_accepted_in_diagnostic_profile") is True
        if event.get("type") == "result":
            require(event.get("profile") == PROFILE and event.get("source_id") == case_id
                    and event.get("request_sha256") == sha(canonical(request))
                    and event.get("input_identity") == identity, "child receipt binding differs")
        comparison = helper.compare_trajectory(expected, native)
        case = {"schema": "hydra-wmi-direct-native-case-v1", "source_id": case_id,
                "actual_process_exit_code": code, "seconds": time.monotonic() - wall,
                "proof_accepted_in_diagnostic_profile": accepted,
                "public_worker_previously_accepted": public[case_id]["proof_accepted"],
                "child_event": event, "trajectory_comparison": comparison,
                "stdout": descriptor(directory / "child.stdout.jsonl"),
                "stderr": descriptor(directory / "child.stderr.txt")}
        write_json(directory / "RESULT.json", case)
        outcomes.append({"source_id": case_id, "proof_accepted_in_diagnostic_profile": accepted,
                         "exact_trajectory_match": comparison["exact_trajectory_match"],
                         "first_divergence_step": (comparison["first_divergence"] or {}).get("step"),
                         "public_worker_previously_accepted": public[case_id]["proof_accepted"],
                         "actual_process_exit_code": code, "error": event.get("error"),
                         "result": descriptor(directory / "RESULT.json")})
        print(json.dumps({"completed": index, "total": len(prepared), **outcomes[-1]}), flush=True)
    require(descriptor(args.inputs) == identity and descriptor(proof_path) == inputs["source_proofs"],
            "input evidence changed during diagnostic")
    verify_native_inventory(inputs)
    summary = {"schema": "hydra-wmi-direct-native-summary-v1", "profile": PROFILE,
               "status": "diagnostic_completed" if len(outcomes) == len(prepared) else "batch_budget_limit",
               "requests": descriptor(args.output / "REQUESTS.json"), "cases_attempted": len(outcomes),
               "proofs_accepted_in_diagnostic_profile": sum(x["proof_accepted_in_diagnostic_profile"] for x in outcomes),
               "exact_trajectory_matches": sum(x["exact_trajectory_match"] for x in outcomes),
               "unattempted_source_ids": inputs["selected_ids"][len(outcomes):],
               "actual_exit_counts": dict(Counter(str(x["actual_process_exit_code"]) for x in outcomes)),
               "seconds": time.monotonic() - started, "results": outcomes,
               "new_model_inference": False, "live_default_changed": False,
               "scope": "Saved development proof replay in a separately named bounded CPU profile, not public-worker acceptance or fresh model generation."}
    write_json(args.output / "SUMMARY.json", summary)
    print(json.dumps({"summary": descriptor(args.output / "SUMMARY.json"),
                      "proofs_accepted_in_diagnostic_profile": summary["proofs_accepted_in_diagnostic_profile"]}), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--case-id")
    args = parser.parse_args()
    args.inputs = args.inputs.resolve()
    if args.output is not None:
        args.output = args.output.resolve()
    sys.dont_write_bytecode = True
    return run_child(args) if args.child else run_parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
