#!/usr/bin/env python3
"""Offline bounded parser/reference audit. No model, network, solver, or imports of targets."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
CPU_SECONDS = 16
ALARM_SECONDS = 20
PARENT_SECONDS = 23


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_fresh(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def native_child():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(ALARM_SECONDS)

    def guard(event, args):
        if event.startswith("socket.") or event.startswith("subprocess.") or event in {
            "os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec"
        }:
            raise RuntimeError("Offline native audit cannot access network or spawn children")
        if event == "open":
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ):
                raise PermissionError("Native child cannot write files")
        if event == "import" and str(args[0]).split(".")[0] in {
            "torch", "transformers", "peft", "tokenizers", "mlx", "mlx_lm", "tensorflow", "jax"
        }:
            raise RuntimeError("Native audit cannot load model frameworks")

    sys.addaudithook(guard)
    sys.path[:0] = [str(SOURCE), str(SOURCE / "peano-lab/py")]
    from training.peano_hydra.protocol import validate_statement
    from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
    from peano_lab.ui.prove import SurfaceCapabilities
    from peano_lab.kernel.formulas import parse_formula_in_context
    from peano_lab.kernel.terms import _TokenStream

    payload = json.load(sys.stdin)
    theorem = payload["theorem"]
    canonical = validate_statement(theorem)
    tree = parse_formula_in_context(theorem, [])
    stack, nodes, max_depth = [(tree, 1)], 0, 0
    while stack:
        node, depth = stack.pop()
        nodes += 1
        max_depth = max(max_depth, depth)
        for name in ("body", "term", "left", "right"):
            child = getattr(node, name, None)
            if child is not None:
                stack.append((child, depth + 1))
    record = {"id": payload["id"], "canonical_theorem": canonical,
              "statement_sha256": sha(canonical.encode()), "input_accepted": True,
              "source_bytes": len(theorem.encode()), "tokens": len(_TokenStream(theorem).tokens),
              "ast_nodes": nodes, "ast_depth": max_depth}
    if "commands" in payload:
        commands = payload["commands"]
        if not 0 < len(commands) <= 64 or any(c.startswith("use ") for c in commands):
            raise ValueError("Reference command count/import policy violation")
        start = time.monotonic()
        result = run_proof(canonical, tuple(commands), classical=False, on_error="stop",
            capabilities=SurfaceCapabilities(label="hydra-advanced-private-reference-v1",
                allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset()),
            trace_byte_limit=256 * 1024).to_dict(include_trace=True)
        record.update({"native_seconds": round(time.monotonic()-start, 5),
                       "commands": commands, "native_result": result,
                       "proved": result["status"] == "proved" and result["kernel_checked"] is True
                           and result["theorem"] == canonical and result["goals"] == []})
    print(json.dumps(record, ensure_ascii=False))
    return 0


def run_child(payload):
    start = time.monotonic()
    try:
        child = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--native-child"],
            input=json.dumps(payload), text=True, capture_output=True, timeout=PARENT_SECONDS,
            cwd=HERE, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        output = {"id": payload["id"], "actual_child_exit_code": child.returncode,
                  "child_wall_seconds": round(time.monotonic()-start, 5)}
        if child.returncode == 0:
            output.update(json.loads(child.stdout))
        else:
            output.update({"infrastructure_failure": True, "stderr": child.stderr[-4000:],
                           "stdout": child.stdout[-4000:]})
        return output
    except subprocess.TimeoutExpired as error:
        return {"id": payload["id"], "parent_timeout": True,
                "actual_child_exit_code": None, "proved": False,
                "child_wall_seconds": round(time.monotonic()-start, 5),
                "error": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--native-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--curriculum", type=Path, default=HERE / "curriculum.json")
    parser.add_argument("--references", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.native_child:
        return native_child()
    if args.output is None or args.output.exists() or args.output.resolve().parent != HERE:
        raise ValueError("Use a fresh output directory directly inside candidate-research")
    raw = args.curriculum.read_bytes()
    curriculum = json.loads(raw)
    cases = curriculum["cases"]
    if not 12 <= len(cases) <= 20 or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Unexpected curriculum case count/identity")
    args.output.mkdir()
    # Reuse the already reviewed, read-only frozen-source/corpus pin audit. No native search is invoked here.
    spec = importlib.util.spec_from_file_location("existing_pin_audit", ROOT / "hydra-playground/verify_hybrid_cases.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    start = time.monotonic()
    source = helper.source_check()
    corpus, statements = helper.corpus_check()
    summary = {"schema": "hydra-advanced-native-curriculum-audit-v1", "complete": False,
               "curriculum_sha256": sha(raw), "verifier_sha256": sha(Path(__file__).read_bytes()),
               "reused_pin_helper": helper.pin(Path(helper.__file__)),
               "kernel_source": source, "corpus": corpus,
               "limits": {"per_child_cpu_seconds": CPU_SECONDS, "per_child_alarm_seconds": ALARM_SECONDS,
                          "per_child_parent_seconds": PARENT_SECONDS, "native_ring_seconds": 5},
               "model_calls": 0, "vampire_calls": 0, "network_calls": 0, "target_imports": 0,
               "benchmark_claim": False, "parser_records": [], "reference_records": []}
    by_id = {case["id"]: case for case in cases}
    try:
        for case in cases:
            record = run_child({"id": case["id"], "theorem": case["theorem"]})
            if record.get("input_accepted"):
                record["exact_train_dev_matches"] = [split for split in statements
                    if record["statement_sha256"] in statements[split]]
            summary["parser_records"].append(record)
            write_fresh(args.output / (case["id"] + ".parse.json"), record)
        if args.references:
            reference_raw = args.references.read_bytes()
            summary["references_sha256"] = sha(reference_raw)
            references = json.loads(reference_raw)["references"]
            if not 1 <= len(references) <= 6:
                raise ValueError("Reference scope is at most six bounded proofs")
            for ref in references:
                record = run_child({"id": ref["id"], "theorem": by_id[ref["id"]]["theorem"],
                                    "commands": ref["commands"]})
                record["reference_origin"] = ref["origin"]
                summary["reference_records"].append(record)
                write_fresh(args.output / (ref["id"] + ".reference.json"), record)
                print(ref["id"] + ": proved=" + str(record.get("proved", False))
                      + ", actual_child_exit=" + str(record["actual_child_exit_code"]), flush=True)
        if args.curriculum.read_bytes() != raw:
            raise ValueError("Curriculum changed during audit")
        summary["complete"] = True
    finally:
        summary["counts"] = {
            "cases": len(cases), "accepted": sum(bool(r.get("input_accepted")) for r in summary["parser_records"]),
            "exact_train_dev_matches": sum(bool(r.get("exact_train_dev_matches")) for r in summary["parser_records"]),
            "references_attempted": len(summary["reference_records"]),
            "references_proved": sum(bool(r.get("proved")) for r in summary["reference_records"])}
        summary["elapsed_seconds"] = round(time.monotonic()-start, 5)
        summary["exit_observation"] = "Child exit codes are actual; the caller must separately record the actual outer exit. Exit 1 means any parser/reference failed."
        write_fresh(args.output / "summary.json", summary)
    good = (summary["complete"] and summary["counts"]["accepted"] == len(cases)
            and summary["counts"]["references_attempted"] == summary["counts"]["references_proved"])
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
