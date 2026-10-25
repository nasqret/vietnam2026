"""One local pure metadata gate, with actual execution/provenance saved separately."""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import resource
import signal
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
SOURCES = ("gpu_saved_reload.py", "remote_recovery_control.py", "recovery_launchers.py",
           "test_gpu_recovery.py", "derive_helpers.py", "metadata_recovery.py", "run_gpu_pure_gate.py")
FORBIDDEN = {"torch", "transformers", "peft", "mlx", "jax", "tensorflow", "peano_lab", "hydra_training_v5"}


def pins():
    return {name: {"bytes": (HERE / name).stat().st_size,
                   "sha256": hashlib.sha256((HERE / name).read_bytes()).hexdigest()} for name in SOURCES}


def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "os.exec", "socket.connect", "socket.bind"}:
        raise RuntimeError("Pure recovery gate forbids process/network activity.")
    if event == "import" and str(args[0]).split(".")[0] in FORBIDDEN:
        raise RuntimeError("Pure recovery gate forbids native/framework imports.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, choices=range(1, 10), required=True)
    args = parser.parse_args()
    output = HERE / ("gpu-pure-gate-" + str(args.index).zfill(2))
    output.mkdir(exist_ok=False)
    before = pins()
    resource.setrlimit(resource.RLIMIT_CPU, (20, 25))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("Pure gate exceeded 30 seconds.")))
    signal.alarm(30)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(HERE))
    sys.addaudithook(audit)
    started = time.monotonic()
    import test_gpu_recovery
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_gpu_recovery))
    signal.alarm(0)
    after = pins()
    imported = sorted(name for name in sys.modules if name.split(".")[0] in FORBIDDEN)
    assert not imported and before == after
    text = stream.getvalue()
    assert len(text.encode()) <= 128 * 1024
    (output / "tests.txt").write_text(text)
    record = {"schema": "hydra-p6-saved-recovery-pure-gate-v1", "passed": result.wasSuccessful(),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "elapsed_seconds": time.monotonic() - started,
        "source_pins_before": before, "source_pins_after": after, "sources_unchanged": before == after,
        "native_model_solver_ssh_calls": 0, "actual_cpu_metadata_admission_performed": False,
        "all_admission_inputs_in_tests_are_synthetic": True}
    (output / "result.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: record[k] for k in ("passed", "tests", "failures", "errors", "elapsed_seconds")}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
