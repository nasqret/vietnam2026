"""Run only the output-only prototype's mocked profile/memory tests."""
from pathlib import Path
import hashlib
import json
import resource
import signal
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = HERE / "app"
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(15)
sys.path[:0] = [str(APP), str(APP / "tests"),
               str(ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py")]
before = json.loads((HERE / "source-pins-before.json").read_text())
for name, expected in before.items():
    raw = (ROOT / "hydra-playground" / name).read_bytes()
    assert {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} == expected
suite = unittest.defaultTestLoader.discover(str(APP / "tests"), pattern="test_vampire_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
for name, expected in before.items():
    raw = (ROOT / "hydra-playground" / name).read_bytes()
    assert {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} == expected
raise SystemExit(0 if result.wasSuccessful() else 1)
