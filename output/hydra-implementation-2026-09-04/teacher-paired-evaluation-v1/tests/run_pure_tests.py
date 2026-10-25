"""Finite pure fixture gate; it refuses runtime imports and subprocess/network use."""
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

HERE = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=False)
resource.setrlimit(resource.RLIMIT_CPU, (15, 16))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(30)
forbidden = ("peano_lab", "torch", "transformers", "hydra_training_v5", "teacher_data", "teacher_student_pilot", "experimental_model", "numpy")
blocked = []


class NoRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == p or fullname.startswith(p + ".") for p in forbidden):
            blocked.append({"kind": "import", "name": fullname})
            raise RuntimeError("Runtime import forbidden in this pure gate: " + fullname)


def audit(event, args):
    if event.startswith(("subprocess.Popen", "os.fork", "os.posix_spawn", "os.system", "socket.connect", "socket.bind")):
        blocked.append({"kind": "operation", "name": event})
        raise RuntimeError("Runtime operation forbidden in this pure gate: " + event)


sys.meta_path.insert(0, NoRuntime())
sys.addaudithook(audit)
pins = lambda: {p.relative_to(HERE).as_posix(): sha256(p.read_bytes()).hexdigest()
    for p in sorted(list(HERE.glob("*.py")) + list((HERE / "tests").glob("*.py")))}
before = pins()
started = time.monotonic()
stream = io.StringIO()
suite = unittest.defaultTestLoader.discover(str(HERE / "tests"), pattern="test_*.py")
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
after = pins()
signal.alarm(0)
record = {"schema": "hydra-teacher-paired-pure-gate-v1", "passed": result.wasSuccessful() and before == after and not blocked,
    "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
    "elapsed_seconds": time.monotonic() - started, "sources_unchanged": before == after, "source_pins_before": before,
    "source_pins_after": after, "blocked_runtime_attempts": blocked, "native_proof_runs": 0, "model_calls": 0,
    "network_calls": 0, "reserved_cases_parsed": False, "constructed_fixtures_not_real_training": True}
(output / "pure-tests.log").write_text(stream.getvalue())
(output / "pure-tests.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: v for k, v in record.items() if not k.startswith("source_pins")}, sort_keys=True))
raise SystemExit(0 if record["passed"] else 1)
