"""Bounded focused candidate tests, separate from production epoch evidence."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830")
OUT = Path(__file__).resolve().parent
PYTHON = "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"
SITE = "/Users/bnaskrecki/Library/Python/3.10/lib/python/site-packages"
TEST = "peano-lab/py/tests/test_peano_hydra_frontier_benchmark_candidates.py"
sys.path[:0] = [str(ROOT)]
from training.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record

if len(sys.argv) != 2 or Path(sys.argv[1]).name != sys.argv[1] or not sys.argv[1].endswith(".json"):
    raise SystemExit("usage: benchmark-tests-runner.py FRESH_RECEIPT.json")
output = OUT / sys.argv[1]
if output.exists():
    raise SystemExit("fresh test receipt required")
sources = (TEST, "training/peano_hydra/frontier_benchmark_candidates.py",
           "scripts/build_peano_hydra_benchmark_candidates.py", "training/peano_hydra/review_runtime.py")
before = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
code = "import sys;sys.path[:0]=" + repr([SITE, str(ROOT), str(ROOT / "peano-lab/py")]) + ";"
code += "import pytest;result=pytest.main(" + repr(["-q", "--maxfail=3", "--tb=short", "-p", "no:cacheprovider", TEST]) + ");"
code += "assert not {'torch','transformers','peft','tokenizers'} & set(sys.modules);raise SystemExit(result)"
command = (PYTHON, "-I", "-B", "-X", "pycache_prefix=/dev/null", "-c", code)
limits = ProcessLimits(cpu_seconds=45, wall_seconds=60, rss_bytes=1024**3, output_bytes=256 * 1024)
try:
    process = run_bounded(command, cwd=ROOT, limits=limits)
    after = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
    record = {"schema": "peano-hydra-frontier-benchmark-focused-tests-v1", "status": "failed", "process": process,
              "source_files_before": before, "source_files_after": after,
              "native_scope": "64 real constructive original-goal QEDs; explicitly synthetic epoch metadata; real rejection fixture",
              "metadata_scope": "pure no-native/no-model validation; whole-family reservation; tampering/failure retention"}
    try:
        validate_process_record(process, command=command, limits=limits, success_codes=(0,))
        if before != after:
            raise ValueError("test sources changed during execution")
        record["status"] = "passed"
    except ValueError as error:
        record["error"] = str(error)
except BaseException as error:
    record = {"schema": "peano-hydra-frontier-benchmark-focused-tests-v1", "status": "controller_failed",
              "source_files_before": before, "error": type(error).__name__ + ": " + str(error)}
with output.open("x") as stream:
    json.dump(record, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(json.dumps({"status": record["status"], "receipt": str(output), "process": record.get("process", {}).get("stdout", "")}, sort_keys=True))
raise SystemExit(0 if record["status"] == "passed" else 1)
