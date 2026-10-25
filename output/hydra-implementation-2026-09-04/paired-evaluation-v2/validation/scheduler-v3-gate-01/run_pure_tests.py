"""Re-run unchanged constructed controller tests; forbid real execution."""
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
CONTROL = HERE.parents[1]
ROOT = CONTROL.parents[2]
blocked = []


class PureImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in {
            "peano_lab", "hybrid_search", "experimental_model", "torch", "transformers",
            "mlx", "numpy", "sympy", "cvc5", "training", "hydra_training_v5",
        }:
            blocked.append("import:" + fullname)
            raise RuntimeError("Runtime/native imports are forbidden in the pure controller gate.")
        return None


def no_execution(event, args):
    if event in {"subprocess.Popen", "os.system", "os.fork", "os.forkpty", "os.posix_spawn",
                 "os.exec", "os.kill", "os.killpg", "socket.connect", "socket.connect_ex", "socket.bind"}:
        blocked.append(event)
        raise RuntimeError("Actual process/network execution is forbidden in this pure gate.")


def source_pins():
    manifest = json.loads((CONTROL / "DERIVATION.json").read_bytes())
    result = {}
    for name, expected in manifest["files"].items():
        for base, key in ((CONTROL, "sha256"), (CONTROL.with_name("paired-evaluation-prototype"), "original_sha256")):
            path = base / name
            digest = sha256(path.read_bytes()).hexdigest()
            if digest != expected[key]:
                raise ValueError("Changed copied or original source: " + str(path))
            result[str(path.relative_to(ROOT))] = digest
    result[str(Path(__file__).resolve().relative_to(ROOT))] = sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main():
    before = source_pins()
    started = datetime.now(timezone.utc).isoformat()
    began = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    signal.alarm(30)
    sys.meta_path.insert(0, PureImports())
    sys.addaudithook(no_execution)
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(CONTROL / "tests"), pattern="test_paired_controller.py")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    import paired_common
    import paired_controller
    helper = paired_controller.scheduler_helpers()
    helper_bound = helper.PROVIDER_SHA == paired_common.PROVIDER_SHA == "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
    after = source_pins()
    passed = result.wasSuccessful() and result.testsRun == 42 and before == after and helper_bound and not blocked
    record = {"schema": "hydra-paired-v2-pure-gate-v1", "passed": passed,
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": time.monotonic() - began,
        "source_pins_before": before, "source_pins_after": after,
        "source_pins_unchanged": before == after, "adjacent_scheduler_helper_bound": helper_bound,
        "blocked_execution_attempts": blocked,
        "scope": "42 unchanged pure constructed-record tests and metadata-only adjacent helper import; no native/model/scheduler/child/reserved-case execution.",
        "limits": {"cpu_seconds": 15, "wall_seconds": 30}}
    with (HERE / "pure-tests.log").open("x") as handle:
        handle.write(stream.getvalue())
    with (HERE / "pure-tests.json").open("x") as handle:
        json.dump(record, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({key: value for key, value in record.items() if not key.startswith("source_pins_")}, sort_keys=True))
    signal.alarm(0)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
