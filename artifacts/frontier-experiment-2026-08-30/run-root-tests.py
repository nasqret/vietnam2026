"""Bounded local metadata/checkpoint regression harness; no models or Slurm."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830")
ARCHIVE = Path(__file__).absolute().parent
sys.path.insert(0, str(ROOT))
from training.peano_hydra.review_runtime import ProcessLimits, run_bounded, ReviewRuntimeError

tests = ["peano-lab/py/tests/test_peano_hydra_scaling_experiment.py",
         "peano-lab/py/tests/test_peano_hydra_scaling_evaluation.py",
         "peano-lab/py/tests/test_peano_hydra_frontier_benchmark_evaluation.py"]
sources = ["training/peano_hydra/scaling_experiment.py", "training/peano_hydra/scaling_evaluation.py",
           "training/peano_hydra/frontier_benchmark_run.py", "scripts/eval_peano_hydra_frontier_benchmark.py", *tests]


def main():
    if len(sys.argv) != 2 or Path(sys.argv[1]).name != sys.argv[1] or not sys.argv[1].endswith(".json"):
        raise SystemExit("usage: run-root-tests.py FRESH_RECEIPT.json")
    target = ARCHIVE / sys.argv[1]
    if target.exists(): raise SystemExit("fresh receipt required")
    before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    paths = ["/Users/bnaskrecki/Library/Python/3.10/lib/python/site-packages", str(ROOT), str(ROOT / "peano-lab/py")]
    code = f'''import sys,json,os
sys.path[:0]={paths!r}
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
import pytest
status=pytest.main({["-q", "--maxfail=3", "--tb=short", "-p", "no:cacheprovider", *tests]!r})
forbidden=[k for k in sys.modules if k.split(".")[0] in ("torch","transformers","peft","tokenizers")]
print("NO_MODEL_MODULES "+json.dumps(forbidden))
assert not forbidden
raise SystemExit(status)
'''
    command = ("/Library/Frameworks/Python.framework/Versions/3.10/bin/python3", "-I", "-B", "-X", "pycache_prefix=/dev/null", "-c", code)
    limits = ProcessLimits(cpu_seconds=60, wall_seconds=90, rss_bytes=1024**3, output_bytes=512*1024)
    try:
        process = run_bounded(command, cwd=ROOT, limits=limits)
    except ReviewRuntimeError as error:
        process = error.record
    after = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    record = {"schema": "peano-frontier-root-regression-receipt-v1", "sources_before": before, "sources_after": after,
              "sources_unchanged": before == after, "tests": tests, "process": process,
              "scope": "real metadata/checkpoint/files; synthetic origins/human review/replay/model boundaries",
              "model_generation_performed": False, "gpu_used": False}
    with target.open("xb") as stream: stream.write((json.dumps(record, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({"receipt": str(target), "sources_unchanged": before == after, "process": process}, sort_keys=True))
    raise SystemExit(0 if process["returncode"] == 0 and before == after else 2)


if __name__ == "__main__": main()
