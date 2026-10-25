"""One fixed, native-only P4 fixture with owned-process resource accounting."""
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import runpy
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
APP = ROOT / "hydra-playground"
TEST = APP / "tests/test_planner_native.py"
FROZEN = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py/peano_lab"
OUT = HERE / "native-01"
CPU_SECONDS = 30
WALL_SECONDS = 40
RSS_BYTES = 2 * 1024**3
OUTPUT_BYTES = 4 * 1024**2


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def pins():
    selected = [Path(__file__), HERE / "parameterized-cubic-request.json", TEST]
    selected.extend(APP / name for name in (
        "proof_planner.py", "planner_provider.py", "finite_difference.py", "arithmetic_search.py",
        "vampire_process.py", "vampire_limits.py", "tests/test_proof_planner.py", "tests/test_planner_provider.py",
    ))
    selected.extend(sorted((APP / "native-v7/peano_lab").rglob("*.py")))
    selected.extend(sorted((FROZEN / "kernel").glob("*.py")))
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in selected}


def worker():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(WALL_SECONDS)

    def native_only(event, args):
        if event in ("subprocess.Popen", "os.system", "os.exec", "socket.connect", "socket.bind"):
            raise RuntimeError("The P4 native gate cannot launch subprocesses or network calls.")

    sys.addaudithook(native_only)
    sys.argv = [str(TEST)]
    runpy.run_path(str(TEST), run_name="__main__")


def parent():
    OUT.mkdir(exist_ok=False)
    before = pins()
    write_json(OUT / "request.json", {
        "schema": "hydra-p4-native-gate-request-v1",
        "test": str(TEST.relative_to(ROOT)),
        "source_pins_before": before,
        "case": json.loads((HERE / "parameterized-cubic-request.json").read_text()),
        "limits": {"child_cpu_seconds": CPU_SECONDS, "wall_seconds": WALL_SECONDS,
                   "owned_child_rss_bytes": RSS_BYTES, "output_bytes": OUTPUT_BYTES,
                   "sample_interval_seconds": 0.02},
        "automatic_retry": False, "model_calls": 0, "vampire_calls": 0,
    })
    sys.path.insert(0, str(APP))
    from vampire_process import _owned_child_rss, _resident_size
    process = None
    stopped = None
    peak = 0
    began = time.monotonic()
    try:
        _resident_size(os.getpid())
        with (OUT / "worker-output.txt").open("xb") as log:
            process = subprocess.Popen(
                [sys.executable, "-I", "-B", "-u", str(Path(__file__).resolve()), "--worker"],
                cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"},
            )
            while process.poll() is None:
                rss = _owned_child_rss(process)
                if rss is not None:
                    peak = max(peak, rss)
                    if rss > RSS_BYTES:
                        stopped = "owned_child_rss"
                if time.monotonic() - began >= WALL_SECONDS:
                    stopped = stopped or "wall_seconds"
                if sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()) > OUTPUT_BYTES:
                    stopped = stopped or "output_bytes"
                if stopped:
                    if process.poll() is None:
                        process.kill()
                    break
                time.sleep(0.02)
            process.wait(timeout=5)
    except BaseException as error:
        stopped = stopped or (type(error).__name__ + ": " + str(error)[:200])
        raise
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        after = pins()
        record = {
            "schema": "hydra-p4-owned-native-gate-completion-v1",
            "actual_child_exit_code": None if process is None else process.returncode,
            "child_pid": None if process is None else process.pid,
            "owned_child_reaped": process is not None and process.returncode is not None,
            "stop_reason": stopped, "sampled_peak_owned_child_rss_bytes": peak,
            "elapsed_seconds": time.monotonic() - began,
            "source_pins_after": after, "sources_unchanged": before == after,
            "model_calls": 0, "vampire_calls": 0,
        }
        write_json(OUT / "actual-completion.json", record)
        print(json.dumps({key: value for key, value in record.items() if key != "source_pins_after"}), flush=True)
    if process.returncode != 0 or stopped or before != after:
        return 1
    records = []
    for line in (OUT / "worker-output.txt").read_text().splitlines():
        if line.startswith('{"gate":'):
            records.append(json.loads(line))
    if len(records) != 1 or not records[0].get("original_kernel_checked") or not records[0].get("independent_replay_checked"):
        return 2
    write_json(OUT / "native-result.json", records[0])
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        worker()
    elif not sys.argv[1:]:
        raise SystemExit(parent())
    else:
        raise SystemExit("This guard has one fixed test and accepts only --worker internally.")
