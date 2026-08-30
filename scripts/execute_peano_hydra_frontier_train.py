#!/usr/bin/env python3
"""Enter the unchanged trainer only from the approved one-use frontier job."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--approval-sha256", required=True)
    args = parser.parse_args()
    from training.peano_hydra import frontier_pilot_launch as gate
    admission = gate.check_job_reservation(args.approval_sha256, "train")
    # Also run this when entered directly from an admitted scheduled job; a
    # non-null benchmark_review field is not semantic/reference admission.
    subprocess.run([
        sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null",
        str(ROOT / "scripts/eval_peano_hydra_frontier_benchmark.py"),
        "--check", "--request", str(ROOT / gate.INPUTS["evaluation_request"]),
        "--expected-request-sha256", admission["evaluation_request_sha256"],
    ], cwd=ROOT, check=True, timeout=180)
    from training.peano_hydra.posttrain import execute
    manifest = execute(ROOT / gate.PREPARATION)
    print(str(manifest), flush=True)


if __name__ == "__main__":
    main()
