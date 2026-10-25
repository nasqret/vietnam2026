"""Retain a reviewable source patch and the exact focused test sources."""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

WORK = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830")
FROZEN = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-execution-20260830")
OUT = Path(__file__).absolute().parent
ORIGINAL = Path("/Users/bnaskrecki/codex/test/vietnam2026-new-theorems")
MODIFIED = ("training/peano_hydra/scaling_freeze.py", "training/peano_hydra/scaling_experiment.py",
            "training/peano_hydra/scaling_evaluation.py", "training/peano_hydra/helios_runtime.py")
NEW = (
    "training/peano_hydra/frontier_benchmark_candidates.py", "training/peano_hydra/frontier_benchmark_audit.py",
    "training/peano_hydra/frontier_benchmark_protocol.py", "training/peano_hydra/frontier_benchmark_run.py",
    "training/peano_hydra/frontier_pilot_launch.py",
    "scripts/build_peano_hydra_benchmark_candidates.py", "scripts/check_peano_hydra_frontier_runtime.py",
    "scripts/execute_peano_hydra_frontier_train.py", "scripts/preflight_peano_hydra_frontier_tokens.py",
    "scripts/prepare_peano_hydra_frontier_launch.py", "scripts/eval_peano_hydra_frontier_benchmark.py",
    "scripts/helios_hydra_frontier.sh", "scripts/run_peano_hydra_frontier.sh",
    "slurm/peano_hydra_frontier_train.sbatch", "slurm/peano_hydra_frontier_evaluate.sbatch",
)
TESTS = (
    "test_peano_hydra_frontier_benchmark_candidates.py", "test_peano_hydra_frontier_benchmark_audit.py",
    "test_peano_hydra_frontier_benchmark_protocol.py", "test_peano_hydra_frontier_benchmark_evaluation.py",
    "test_peano_hydra_frontier_launch.py", "test_peano_hydra_helios_runtime.py",
    "test_peano_hydra_scaling_experiment.py", "test_peano_hydra_scaling_evaluation.py",
)


def item(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    patch_path, test_root, receipt_path = OUT / "implementation.patch", OUT / "test-sources", OUT / "implementation-manifest.json"
    if patch_path.exists() or test_root.exists() or receipt_path.exists(): raise SystemExit("fresh outputs required")
    assert all(item(WORK / path) == item(FROZEN / path) for path in (*MODIFIED, *NEW))
    patch = subprocess.check_output(["git", "diff", "--binary", "--", *MODIFIED], cwd=WORK)
    for name in NEW:
        assert not subprocess.run(["git", "ls-files", "--error-unmatch", "--", name], cwd=WORK,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        patch += "".join(difflib.unified_diff([], (WORK / name).read_text().splitlines(keepends=True),
                                             fromfile="/dev/null", tofile="b/" + name)).encode()
    with patch_path.open("xb") as stream: stream.write(patch)
    test_root.mkdir()
    inventory = {}
    for name in TESTS:
        source = WORK / "peano-lab/py/tests" / name
        with (test_root / name).open("xb") as stream: stream.write(source.read_bytes())
        inventory[name] = item(source)
    record = {"schema": "peano-frontier-implementation-package-v1",
        "working_copy": str(WORK),
        "work_baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WORK, text=True).strip(),
        "frozen_execution_commit": "278d80552ab55b080365ddbae0d1d49be2fdc396",
        "patch": item(patch_path), "source_files": {p: item(FROZEN / p) for p in (*MODIFIED, *NEW)},
        "test_sources": inventory, "tests_are_not_part_of_runtime_origin_scope": True,
        "original_repositories_modified": False, "patch_applied_to_original": False,
        "note": "Source patch is relative to the isolated recovery baseline; focused tests are retained separately, not native/GPU evidence."}
    with receipt_path.open("xb") as stream: stream.write((json.dumps(record, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({"patch_bytes": len(patch), "source_file_count": len(record["source_files"]),
                      "test_source_count": len(inventory), "manifest": item(receipt_path)}, sort_keys=True))


if __name__ == "__main__": main()
