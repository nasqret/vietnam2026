"""Local bounded launch/runtime regressions. Never uses a real scheduler."""
import hashlib
import json
import os
from pathlib import Path
import resource
import selectors
import signal
import subprocess
import sys
import time

ROOT = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830")
OUT = Path(__file__).absolute().parent
sys.path.insert(0, str(ROOT))

SOURCES = (
    "training/peano_hydra/frontier_pilot_launch.py", "training/peano_hydra/helios_runtime.py",
    "training/peano_hydra/posttrain.py", "training/peano_hydra/configs/qwen3_1_7b_alpha_posttrain.toml",
    "scripts/helios_hydra_frontier.sh", "scripts/run_peano_hydra_frontier.sh",
    "scripts/check_peano_hydra_frontier_runtime.py", "scripts/execute_peano_hydra_frontier_train.py",
    "scripts/preflight_peano_hydra_frontier_tokens.py",
    "scripts/prepare_peano_hydra_frontier_launch.py",
    "slurm/peano_hydra_frontier_train.sbatch", "slurm/peano_hydra_frontier_evaluate.sbatch",
    "peano-lab/py/tests/test_peano_hydra_frontier_launch.py", "peano-lab/py/tests/test_peano_hydra_helios_runtime.py",
)


def trusted_local_tests(command):
    """Reviewed tests may spawn bounded local bash/Python, never real Slurm.

    This is separate from the unchanged no-descendants proof-worker contract.
    Whole process-group RSS, output and wall time are supervised here.
    """
    limits = {"cpu_seconds_per_process": 90, "wall_seconds": 120,
              "sampled_group_rss_bytes": 1024**3, "combined_output_bytes": 256*1024}
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("LD_", "DYLD_", "PYTHON", "PYTEST", "GIT_", "SLURM_", "SBATCH_"))
                   and key not in ("BASH_ENV", "ENV")}
    environment.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONNOUSERSITE="1", PYTHONPYCACHEPREFIX="/dev/null")
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    child = subprocess.Popen(command, cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    selector, output = selectors.DefaultSelector(), {"stdout": bytearray(), "stderr": bytearray()}
    peak, observed, sampled_at, reason, error = 0, set(), 0.0, "exited", None
    try:
        for name, stream in (("stdout", child.stdout), ("stderr", child.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map() or child.poll() is None:
            now = time.monotonic()
            if now - started >= limits["wall_seconds"]:
                raise TimeoutError("whole-test wall budget exceeded")
            if now - sampled_at >= 0.05:
                sample = subprocess.run(["/bin/ps", "-axo", "pid=,pgid=,rss="], check=True,
                                        capture_output=True, timeout=1, stdin=subprocess.DEVNULL)
                if len(sample.stdout) > 4*1024**2 or len(sample.stderr) > 65536:
                    raise RuntimeError("process sampler output exceeds its bound")
                group_rss = 0
                for line in sample.stdout.splitlines():
                    pid, pgid, kib = map(int, line.split())
                    if pgid == child.pid:
                        observed.add(pid)
                        group_rss += kib * 1024
                peak = max(peak, group_rss)
                if peak > limits["sampled_group_rss_bytes"]:
                    raise MemoryError("whole-test sampled RSS budget exceeded")
                sampled_at = time.monotonic()
            for key, _ in selector.select(0.025):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                output[key.data].extend(block)
                if sum(map(len, output.values())) > limits["combined_output_bytes"]:
                    raise RuntimeError("whole-test output exceeds its bound")
        child.wait(timeout=1)
    except BaseException as failure:
        reason, error = "guard-stopped", type(failure).__name__ + ": " + str(failure)
    finally:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=5)
        selector.close()
        child.stdout.close()
        child.stderr.close()
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = usage.ru_utime + usage.ru_stime - before.ru_utime - before.ru_stime
    return {"command": command, "reason": reason, "error": error, "returncode": child.returncode,
            "limits": limits, "resources": {"cpu_seconds_with_waited_children_and_sampler": cpu,
                        "wall_seconds": time.monotonic() - started, "peak_sampled_group_rss_bytes": peak},
            "observed_process_ids": sorted(observed), "stdout": output["stdout"].decode("utf-8", "replace"),
            "stderr": output["stderr"].decode("utf-8", "replace")}


def main():
    if len(sys.argv) != 2 or Path(sys.argv[1]).name != sys.argv[1]:
        raise SystemExit("usage: check_frontier_launch.py FRESH_RECEIPT.json")
    output = OUT / sys.argv[1]
    if output.exists():
        raise SystemExit("refusing to overwrite an earlier test receipt")
    before = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}
    code = """
import sys,json,resource
resource.setrlimit(resource.RLIMIT_CPU,(90,91))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
sys.path[:0] = [
 '/Users/bnaskrecki/Library/Python/3.10/lib/python/site-packages',
 '/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830',
 '/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830/peano-lab/py',
 '/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830/peano-lab/py/tests']
import pytest
result=pytest.main(['-q','--maxfail=3','--tb=short','-p','no:cacheprovider',
 'peano-lab/py/tests/test_peano_hydra_frontier_launch.py',
 'peano-lab/py/tests/test_peano_hydra_helios_runtime.py'])
forbidden=sorted({'torch','transformers','peft','tokenizers'} & set(sys.modules))
print('FORBIDDEN_MODEL_MODULES '+json.dumps(forbidden))
assert not forbidden
raise SystemExit(result)
"""
    command = ("/Library/Frameworks/Python.framework/Versions/3.10/bin/python3", "-I", "-B",
               "-X", "pycache_prefix=/dev/null", "-c", code)
    process = trusted_local_tests(command)
    after = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}
    receipt = {"schema": "peano-hydra-frontier-launch-regressions-v1",
               "scope": "synthetic temporary inputs; mocked Slurm; no native proof or model execution",
               "sources_before": before, "sources_after": after, "sources_unchanged": before == after,
               "process": process, "passed": process["reason"] == "exited" and process["returncode"] == 0 and before == after
                   and process["resources"]["cpu_seconds_with_waited_children_and_sampler"] <= 90}
    with output.open("x") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"receipt": str(output), "passed": receipt["passed"], "resources": process["resources"],
                      "stdout": process["stdout"], "stderr": process["stderr"]}, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
