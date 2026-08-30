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
    from training.peano_hydra import frontier_training_launch as gate
    admission = gate.check_job_reservation(args.approval_sha256, "train")
    # Repeat the admitted-data/all64-exclusions check even when this script is
    # entered directly from the recorded scheduled job. No comparison or
    # reference-readiness record is consumed or asserted by training-only.
    subprocess.run([
        sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null",
        str(ROOT / "scripts/check_peano_hydra_frontier_training_inputs.py"),
        "--check", "--request", str(ROOT / gate.INPUTS["training_inputs"]),
        "--expected-request-sha256", admission["training_inputs_sha256"],
    ], cwd=ROOT, check=True, timeout=210)
    from training.peano_hydra.posttrain import execute
    manifest = execute(ROOT / gate.PREPARATION)
    # The unchanged trainer includes its final teacher-forced DEV loss within
    # this same hard reservation. No benchmark/search evaluation follows.
    print(str(manifest), flush=True)


if __name__ == "__main__":
    main()
