"""Run the unchanged adjacent controller tests without native or model execution."""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.abc
import io
import json
from pathlib import Path
import resource
import signal
import sys
import time
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
blocked = []
forbidden_imports = {
    "peano_lab", "torch", "transformers", "mlx", "numpy", "sympy", "cvc5",
    "training", "hydra_training_v5", "experimental_model",
}


class PureImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in forbidden_imports:
            blocked.append("import:" + fullname)
            raise RuntimeError("Native/framework imports forbidden in this pure gate.")
        return None


def no_execution(event, args):
    if event in {
        "subprocess.Popen", "os.system", "os.fork", "os.forkpty", "os.posix_spawn",
        "os.exec", "socket.connect", "socket.connect_ex", "socket.bind",
    }:
        blocked.append(event)
        raise RuntimeError("Subprocess/network execution forbidden in this pure gate.")


def pins():
    names = ["remote_provider_smoke.py", "remote_training_pilot.py",
             "test_remote_provider_smoke.py", "test_remote_training_pilot.py"]
    paths = [HERE / name for name in names]
    paths += [ROOT / "output/p6-prototype" / name for name in names]
    paths += [Path(__file__).resolve(), ROOT / "hydra-playground/experimental_model.py",
              ROOT / "output/hydra-implementation-2026-09-04/p6-source-bundle-04/source/hydra-playground/experimental_model.py"]
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
            for path in paths}


def main():
    before = pins()
    started = datetime.now(timezone.utc).isoformat()
    began = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    signal.alarm(30)
    sys.meta_path.insert(0, PureImports())
    sys.addaudithook(no_execution)
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_remote_*.py")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.monotonic() - began
    after = pins()
    passed = result.wasSuccessful() and result.testsRun == 16 and before == after and not blocked
    record = {
        "schema": "hydra-p6-wrapper-pure-gate-v1", "passed": passed,
        "tests": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed, "source_pins_before": before,
        "source_pins_after": after, "source_pins_unchanged": before == after,
        "blocked_execution_attempts": blocked,
        "limits": {"cpu_seconds": 15, "wall_seconds": 30},
        "scope": "Unchanged 5 smoke and 11 training-controller pure tests against revised adjacent modules; no scheduler, native, framework, model, tokenization, training, or proof execution.",
    }
    with (HERE / "pure-tests.log").open("x") as handle:
        handle.write(stream.getvalue())
    with (HERE / "pure-tests.json").open("x") as handle:
        json.dump(record, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps(record, sort_keys=True))
    signal.alarm(0)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
