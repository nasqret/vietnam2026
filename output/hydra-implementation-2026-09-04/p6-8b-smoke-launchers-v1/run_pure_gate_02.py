"""One stdlib-only fixture gate; refuses all real subprocess/network attempts."""
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
OUT = HERE / "pure-gate-02"


def pins():
    return {path.name: {"bytes": len(path.read_bytes()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(HERE.glob("*.py"))}


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (20, 25))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
    signal.alarm(30)
    OUT.mkdir(exist_ok=False)
    before = pins()
    attempted = []
    def audit(event, _args):
        if event in {"subprocess.Popen", "os.system", "os.fork", "os.posix_spawn", "socket.connect", "socket.getaddrinfo"}:
            attempted.append(event)
            raise RuntimeError("Real process/network operation is outside this pure gate: " + event)
    sys.addaudithook(audit)
    sys.path.insert(0, str(HERE))
    import test_smoke_launchers
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_smoke_launchers)
    stream = io.StringIO()
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    after = pins()
    forbidden = [name for name in sys.modules if name.split(".")[0] in {"torch", "transformers", "peano_lab", "hydra_training_v5"}]
    record = {"schema": "hydra-p6-8b-smoke-launchers-pure-gate-v1", "tests": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
        "completed": result.wasSuccessful() and before == after and not attempted and not forbidden,
        "elapsed_seconds": time.monotonic() - started, "sources_before": before, "sources_after": after,
        "source_pins_unchanged": before == after, "real_process_or_network_attempts": attempted,
        "native_or_model_modules_imported": forbidden, "fixtures_only": True,
        "ssh_calls": 0, "gpu_allocations": 0, "model_calls": 0, "native_proof_replays": 0,
        "training_duration_selected": False, "automatic_retry": False}
    with (OUT / "stdout.txt").open("x") as target:
        target.write(stream.getvalue())
    with (OUT / "result.json").open("x") as target:
        target.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    signal.alarm(0)
    print(json.dumps({key: value for key, value in record.items() if key not in {"sources_before", "sources_after"}}, sort_keys=True), flush=True)
    if not record["completed"]:
        print(stream.getvalue(), flush=True)
    return 0 if record["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
