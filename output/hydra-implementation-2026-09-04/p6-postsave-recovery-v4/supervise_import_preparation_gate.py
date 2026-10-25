"""One fixed local preparation child; reuse the sealed owned-child RSS reader."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent / "p6-source-bundle-08"
APP = BUNDLE / "source/hydra-playground"
OUT = HERE / "import-preparation-supervision-01"
CHILD = HERE / "run_import_preparation_gate.py"
MANIFEST_SHA = "baa6c45db4fb01806a36aa188508e7cca9517a41934e5ad2f46739873722e1ff"
MAX_RSS = 2 * 1024**3
MAX_OUTPUT = 128 * 1024


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    OUT.mkdir(exist_ok=False)
    assert not (HERE / "import-preparation-gate-01").exists()
    assert sys.platform == "darwin" and sys.version_info[:2] == (3, 11)
    assert pin(BUNDLE / "manifest.json")["sha256"] == MANIFEST_SHA
    manifest = json.loads((BUNDLE / "manifest.json").read_bytes())
    guarded = (CHILD, HERE / "metadata_recovery.py", Path(__file__), APP / "vampire_process.py", APP / "vampire_limits.py")
    before = {str(path): pin(path) for path in guarded}
    for path in guarded[-2:]:
        assert before[str(path)] == manifest["files"]["hydra-playground/" + path.name]
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(APP))
    spec = importlib.util.spec_from_file_location("import4_owned_rss_reader", APP / "vampire_process.py")
    sampler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampler)
    assert sampler._resident_size(os.getpid()) > 0
    argv = [sys.executable, "-I", "-B", str(CHILD)]
    (OUT / "request.json").write_text(json.dumps({"argv": argv, "sources": before,
        "cpu_seconds": 90, "child_wall_seconds": 120, "parent_wall_seconds": 125,
        "sampled_rss_bytes": MAX_RSS, "stdout_stderr_bytes": MAX_OUTPUT,
        "no_automatic_retry": True, "actual_recovery": False}, sort_keys=True, indent=2) + "\n")
    process = None
    reason = None
    code = None
    peak = 0
    samples = 0
    reaped = False
    started = time.monotonic()
    def cancelled(*_):
        raise InterruptedError("Local preparation supervision was cancelled.")
    signal.signal(signal.SIGTERM, cancelled)
    signal.signal(signal.SIGINT, cancelled)
    with (OUT / "stdout.txt").open("xb") as stdout, (OUT / "stderr.txt").open("xb") as stderr:
        try:
            process = subprocess.Popen(argv, cwd=HERE, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                       start_new_session=True)
            while process.poll() is None:
                if time.monotonic() - started >= 125:
                    reason = "owned_preparation_wall_limit"
                    break
                if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > MAX_OUTPUT:
                    reason = "owned_preparation_output_limit"
                    break
                rss = sampler._owned_child_rss(process)
                if rss is not None:
                    samples += 1
                    peak = max(peak, rss)
                    if rss > MAX_RSS:
                        reason = "owned_preparation_rss_limit"
                        break
                time.sleep(0.05)
        except BaseException as failure:
            reason = type(failure).__name__ + ": " + str(failure)[:1000]
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                try:
                    code = process.wait(timeout=3)
                    reaped = True
                except subprocess.TimeoutExpired:
                    reason = "owned_preparation_child_not_reaped"
            if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > MAX_OUTPUT:
                reason = reason or "owned_preparation_output_limit"
    after = {str(path): pin(path) for path in guarded}
    if before != after:
        reason = reason or "preparation_sources_changed"
    child_result = HERE / "import-preparation-gate-01/result.json"
    payload = None
    if child_result.exists() and child_result.stat().st_size <= 256 * 1024:
        payload = json.loads(child_result.read_bytes())
    passed = (code == 0 and reaped and reason is None and samples > 0 and peak <= MAX_RSS
              and type(payload) is dict and payload.get("passed") is True and payload.get("error") is None
              and payload.get("sources_unchanged") is True)
    record = {"schema": "hydra-import4-owned-preparation-supervision-v1", "passed": passed,
        "actual_child_exit_code": code, "owned_child_reaped": reaped, "stop_reason": reason,
        "elapsed_seconds": time.monotonic() - started, "sampled_peak_rss_bytes": peak, "rss_samples": samples,
        "sources_before": before, "sources_after": after, "sources_unchanged": before == after,
        "child_result": pin(child_result) if child_result.exists() else None,
        "automatic_retry": False, "solver_calls": 0, "model_calls": 0, "ssh_calls": 0,
        "actual_cpu_metadata_admission_performed": False}
    with (OUT / "result.json").open("x") as stream:
        json.dump(record, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({key: record[key] for key in ("passed", "actual_child_exit_code", "owned_child_reaped",
                     "stop_reason", "elapsed_seconds", "sampled_peak_rss_bytes", "rss_samples")}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
