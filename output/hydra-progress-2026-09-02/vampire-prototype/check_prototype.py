"""Bounded prototype gate; never starts solver/model/HTTP/search processes."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import resource
import signal
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = ROOT / "hydra-playground"
PROTO = HERE / "app"
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
signal.alarm(30)
pins = json.loads((HERE / "source-pins-before.json").read_text())


def pin_live():
    for name, pin in pins.items():
        raw = (APP / name).read_bytes()
        if len(raw) != pin["bytes"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
            raise RuntimeError("Live bridge changed during prototype gate.")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


pin_live()
sys.path.insert(0, str(APP))
sys.path.insert(0, str(PROTO))
import vampire_bridge
if Path(vampire_bridge.__file__).resolve() != PROTO / "vampire_bridge.py":
    raise RuntimeError("Prototype bridge was not selected.")
started = time.monotonic()
suite = unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module(PROTO / "tests/test_vampire_cache.py", "prototype_cache_tests")))
suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module(APP / "tests/test_vampire_bridge.py", "existing_bridge_tests")))
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
pin_live()
summary = {"status": "passed" if result.wasSuccessful() else "failed", "tests_run": result.testsRun,
           "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
           "elapsed_seconds": time.monotonic() - started, "live_source_pins_unchanged": True,
           "actual_solver_launches": 0, "actual_model_launches": 0,
           "prototype_sha256": hashlib.sha256((PROTO / "vampire_bridge.py").read_bytes()).hexdigest()}
print(log.getvalue(), end="")
print(json.dumps(summary, sort_keys=True))
with (HERE / "unit-result.json").open("x") as output:
    json.dump(summary, output, indent=2)
    output.write("\n")
with (HERE / "unit-output.txt").open("x") as output:
    output.write(log.getvalue())
signal.alarm(0)
raise SystemExit(0 if result.wasSuccessful() else 1)
