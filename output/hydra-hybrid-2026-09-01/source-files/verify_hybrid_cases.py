#!/usr/bin/env python3
"""Check diagnostic references and exact TRAIN/DEV exclusions; never run a model.

Use a fresh output path. Each reference runs in its own bounded native process;
the caller must also observe this program's actual final exit status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

APP = Path(__file__).resolve().parent
ROOT = APP.parent
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
CATALOG = SOURCE / "_deploy/hydra-retention-evaluation-recovery-source.json"
CATALOG_SHA = "f866666c81c94a6c0c2db685c27f5dfa5c68d84508c5652d848e820caf9b741c"
SOURCE_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
CORPUS = ROOT / "_deploy/hydra-retention-execution-20260830/_deploy/hydra-retention-pilot-v1/preparation"
MANIFEST_SHA = "bb67f5f0737003d2c40b45885d7759f395f27bf0e88d358bfe1844df2a30ba21"
SUITE = APP / "hybrid-evaluation-cases.json"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    require(path.is_file() and not path.is_symlink(), "Expected a regular input: " + str(path))
    hasher = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            total += len(block)
            hasher.update(block)
    return {"bytes": total, "sha256": hasher.hexdigest()}


def source_check():
    raw = CATALOG.read_bytes()
    require(digest(raw) == CATALOG_SHA, "Preserved source catalogue changed.")
    catalog = json.loads(raw)
    require(catalog["git_commit"] == SOURCE_COMMIT, "Unexpected source revision.")
    for relative, expected in catalog["files"].items():
        require(pin(SOURCE / relative) == {key: expected[key] for key in ("bytes", "sha256")},
                "Preserved source changed: " + relative)
    return {"commit": SOURCE_COMMIT, "catalog_sha256": CATALOG_SHA,
            "files_checked": len(catalog["files"])}


def corpus_check():
    raw = (CORPUS / "manifest.json").read_bytes()
    require(digest(raw) == MANIFEST_SHA, "Original training preparation manifest changed.")
    manifest = json.loads(raw)
    records, statements = {}, {}
    for split in ("train", "dev"):
        filename = split + ".jsonl"
        path = CORPUS / filename
        hasher = hashlib.sha256()
        total, rows = 0, 0
        hashes, names = set(), set()
        with path.open("rb") as stream:
            for line in stream:
                require(len(line) <= 256 * 1024, "Oversized original corpus row.")
                hasher.update(line)
                total += len(line)
                row = json.loads(line)
                hashes.add(row["theorem_statement_sha256"])
                names.add(row["theorem_name"])
                rows += 1
        actual = {"bytes": total, "sha256": hasher.hexdigest()}
        require(actual == {key: manifest["files"][filename][key] for key in actual},
                "Original corpus bytes changed: " + split)
        require(rows == manifest["counts"][split]["rows"], "Original corpus row count changed.")
        records[split] = {"path": str(path.relative_to(ROOT)), **actual, "rows": rows,
                          "unique_statements": len(hashes), "theorem_names": len(names)}
        statements[split] = hashes
    return {"preparation_manifest_sha256": MANIFEST_SHA, "files": records}, statements


def native_child():
    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(12)

    def guard(event, args):
        if event.startswith("socket.") or event.startswith("subprocess.") or event in {
            "os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec"
        }:
            raise RuntimeError("Reference verification is offline and cannot spawn children.")
        if event == "open":
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(char in mode for char in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ):
                raise PermissionError("Reference verification is read-only.")
        if event == "import" and str(args[0]).split(".")[0] in {
            "torch", "transformers", "peft", "tokenizers", "mlx", "mlx_lm", "tensorflow", "jax"
        }:
            raise RuntimeError("Reference verification cannot load a model framework.")

    sys.addaudithook(guard)
    sys.path[:0] = [str(SOURCE), str(SOURCE / "peano-lab/py")]
    from training.peano_hydra.protocol import ProtocolError, validate_statement
    from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
    from peano_lab.ui.prove import SurfaceCapabilities

    case = json.load(sys.stdin)
    try:
        original = validate_statement(case["theorem"])
    except ProtocolError as error:
        require(case["input_supported"] is False and case["expected"] == "unknown",
                "A supposedly supported diagnostic could not be parsed.")
        print(json.dumps({"id": case["id"], "input_status": "rejected", "reason": str(error),
                          "mathematical_verdict": "unknown", "kernel_checked": False}))
        return 0
    require(case["input_supported"] is True, "Unsupported-input diagnostic unexpectedly parsed.")
    require(case["expected"] in ("provable", "refutable"), "Missing native reference expectation.")
    if case["expected"] == "refutable":
        reference = case["reference_refutation"]
        statement = validate_statement(reference["theorem"])
        require(statement == validate_statement("~(" + case["theorem"] + ")"),
                "Reference refutation is not the negation of the requested theorem.")
        tactics = reference["tactics"]
    else:
        statement, tactics = original, case["reference_tactics"]
    require(0 < len(tactics) <= 64, "Reference script exceeds the playground limit.")
    result = run_proof(statement, tuple(tactics), classical=False, on_error="stop",
                       capabilities=SurfaceCapabilities(label="hydra-hybrid-diagnostic-reference-v1",
                           allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset()),
                       trace_byte_limit=128 * 1024).to_dict(include_trace=True)
    require(result["status"] == "proved" and result["kernel_checked"] is True
            and result["theorem"] == statement and result["goals"] == [],
            case["id"] + ": native reference failed: " + str(result["error"]))
    trace_raw = json.dumps(result["trace"], sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    print(json.dumps({"id": case["id"], "input_status": "accepted", "canonical_theorem": original,
                      "statement_sha256": digest(original.encode()), "reference_statement": statement,
                      "reference_kind": "proof" if case["expected"] == "provable" else "refutation",
                      "reference_commands": tactics, "kernel_checked": True,
                      "proof_nodes": result["proof_nodes"], "trace_sha256": digest(trace_raw),
                      "trace": result["trace"]}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--suite", type=Path, default=SUITE, help="Diagnostic suite JSON (default: the original suite).")
    parser.add_argument("--output", type=Path, help="A new JSON output file; existing files are never overwritten.")
    parser.add_argument("--native-child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.native_child:
        return native_child()
    require(args.output is not None, "Specify --output with a fresh record path.")
    require(not args.output.exists(), "Output already exists; choose a fresh path.")
    started = time.monotonic()
    suite_path = args.suite.resolve()
    raw = suite_path.read_bytes()
    suite = json.loads(raw)
    require(suite["schema"] == "hydra-hybrid-diagnostic-suite-v1" and suite["benchmark_claim"] is False,
            "Unexpected diagnostic suite identity.")
    require(1 <= len(suite["cases"]) <= 16, "Diagnostic count exceeds the agreed scope.")
    require(len({case["id"] for case in suite["cases"]}) == len(suite["cases"]), "Repeated case identifier.")
    source = source_check()
    corpus, statements = corpus_check()
    records, seen = [], set()
    for case in suite["cases"]:
        begin = time.monotonic()
        process = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--native-child"],
                                 input=json.dumps(case), capture_output=True, text=True, timeout=15,
                                 cwd=APP, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        require(process.returncode == 0, case["id"] + ": child failed: " + process.stderr[-2000:])
        record = json.loads(process.stdout)
        record["actual_child_exit_code"] = process.returncode
        record["elapsed_seconds"] = round(time.monotonic() - begin, 4)
        require(record["id"] == case["id"], "Child record identity mismatch.")
        if record["input_status"] == "accepted":
            value = record["statement_sha256"]
            require(value not in seen, "Repeated canonical theorem within diagnostics.")
            seen.add(value)
            matches = [split for split in statements if value in statements[split]]
            require(not matches, case["id"] + ": copied exact canonical TRAIN/DEV statement: " + str(matches))
            record["exact_corpus_matches"] = matches
        records.append(record)
        print(case["id"] + ": checked", flush=True)
    require(suite_path.read_bytes() == raw, "Diagnostic suite changed during verification.")
    result = {"schema": "hydra-hybrid-diagnostic-reference-check-v1", "checks_passed": True,
              "suite": {"path": str(suite_path.relative_to(ROOT)), "bytes": len(raw), "sha256": digest(raw)},
              "checker": pin(Path(__file__)), "kernel_source": source, "corpus": corpus,
              "limits": {"per_reference_cpu_seconds": 8, "per_reference_alarm_seconds": 12,
                          "per_reference_parent_timeout_seconds": 15, "trace_bytes": 128 * 1024},
              "counts": {"cases": len(records), "native_positive_proofs": sum(c["expected"] == "provable" for c in suite["cases"]),
                         "native_refutations": sum(c["expected"] == "refutable" for c in suite["cases"]),
                         "unsupported_inputs": sum(c["input_supported"] is False for c in suite["cases"]),
                         "exact_train_dev_matches": 0},
              "case_records": records, "elapsed_seconds": round(time.monotonic() - started, 4),
              "model_calls": 0, "vampire_calls": 0, "training_performed": False,
              "benchmark_claim": False,
              "exit_observation": "Child exits are actual subprocess return codes; outer exit must be observed by the caller."}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(str(args.output) + ": all reference and exclusion checks passed", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
