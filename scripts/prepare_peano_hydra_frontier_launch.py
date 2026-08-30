#!/usr/bin/env python3
"""Create a draft or an exactly pinned resource REQUEST; never human approval."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from training.peano_hydra import frontier_pilot_launch as gate
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--draft", action="store_true")
    modes.add_argument("--ready-request", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--review-sha256", help="external CANONICAL accepted human lineage review SHA")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        output = args.output.absolute()
        gate.require(not os.path.lexists(output), "request output must be fresh")
        gate.require(output != ROOT / gate.APPROVAL, "this tool never writes human approval")
        if args.draft:
            gate.require(args.source_commit is None and args.review_sha256 is None,
                         "draft mode does not accept source/review identity claims")
            record = gate.request_template()
        else:
            gate.require(output == ROOT / gate.REQUEST, "ready request uses its exact fixed package path")
            record = gate.ready_request(args.source_commit, args.review_sha256)
            evaluation_sha = record["payloads"][gate.INPUTS["evaluation_request"]]["sha256"]
            subprocess.run([sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null",
                            str(ROOT / "scripts/eval_peano_hydra_frontier_benchmark.py"), "--check",
                            "--request", str(ROOT / gate.INPUTS["evaluation_request"]),
                            "--expected-request-sha256", evaluation_sha], cwd=ROOT, check=True, timeout=180)
            gate.require(gate.canonical(gate.ready_request(args.source_commit, args.review_sha256))
                         == gate.canonical(record), "request inputs changed during CPU benchmark admission")
        raw = gate.canonical(record) + b"\n"
        parent = gate.directory(output.parent)
        try:
            fd = os.open(output.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(parent)
        finally:
            os.close(parent)
        print(json.dumps({"status": record["status"], "output": str(output),
                          "request_file_sha256": hashlib.sha256(raw).hexdigest(),
                          "approval_created": False, "allocation_performed": False}, sort_keys=True), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print("frontier-request: " + " ".join(str(error).split()), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
