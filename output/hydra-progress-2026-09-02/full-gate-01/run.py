from pathlib import Path
import hashlib
import json
import resource
import signal
import sys
import unittest

root = Path(__file__).resolve().parents[3]
app = root / "hydra-playground"
here = Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_CPU, (240, 240))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(300)

def pins():
    paths = list(app.glob("*.py")) + list((app / "tests").glob("test_*.py")) + [app / "app.js", app / "index.html", app / "styles.css"]
    return {str(p.relative_to(app)): {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)}

before = pins()
(here / "source-before.json").write_text(json.dumps(before, indent=2) + "\n")
suite = unittest.defaultTestLoader.discover(str(app / "tests"))
result = unittest.TextTestRunner(verbosity=2).run(suite)
after = pins()
(here / "source-after.json").write_text(json.dumps(after, indent=2) + "\n")
summary = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
           "skipped": len(result.skipped), "source_pins_unchanged": before == after,
           "passed": result.wasSuccessful() and before == after,
           "scope": "Full native/server/worker/adviser test suite; includes one real fixed Standard Vampire smoke, no trained-model inference."}
(here / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary), flush=True)
sys.exit(0 if summary["passed"] else 1)
