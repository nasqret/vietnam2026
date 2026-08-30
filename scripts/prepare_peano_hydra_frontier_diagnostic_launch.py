#!/usr/bin/env python3
"""Prepare a nonauthorizing evaluation/resource draft or exact resource request."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.dont_write_bytecode = True
sys.pycache_prefix = "/dev/null"
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]


def main(argv=None):
    from training.peano_hydra import frontier_diagnostic_launch as gate
    from training.peano_hydra import corrective_workflow as files
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--draft", action="store_true", help="resource request, never authorization")
    modes.add_argument("--draft-evaluation", action="store_true", help="explicit pending input schema")
    modes.add_argument("--ready-request", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        output = args.output.absolute()
        gate.require(not os.path.lexists(output), "request output must be fresh")
        gate.require(output != ROOT / gate.APPROVAL, "this tool never writes resource approval")
        protected = gate.output_protections(include_package=False)
        files.guard_output(output, protected=protected)
        if args.ready_request:
            gate.require(output == ROOT / gate.REQUEST, "ready request uses its exact fixed package path")
            record = gate.ready_request(args.source_commit)
            # The real CPU semantic admission is source/input-bound, but is
            # not human acceptance or an allocation. Recheck byte closure.
            gate.validate_request(record)
        else:
            gate.require(args.source_commit is None, "draft mode makes no frozen source identity claim")
            if args.draft_evaluation:
                from training.peano_hydra import frontier_diagnostic_run as runner
                record = runner.request_template()
            else:
                record = gate.request_template()
        raw = gate.canonical(record) + b"\n"
        files.guard_output(output, protected=protected)
        parent = gate.directory(output.parent)
        try:
            fd = os.open(output.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(parent)
        finally: os.close(parent)
        print(json.dumps({"status": record["status"], "output": str(output),
            "request_file_sha256": hashlib.sha256(raw).hexdigest(), "approval_created": False,
            "allocation_performed": False}, sort_keys=True), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print("frontier-diagnostic-request: " + " ".join(str(error).split())[:3000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
