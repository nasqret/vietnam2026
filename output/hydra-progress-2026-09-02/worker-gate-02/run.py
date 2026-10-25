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
# Parent still stops at its30CPU/90wall ceiling. The higher inherited hard
# ceiling lets each worker install its unchanged1200maximum and then its
# unchanged per-request lower limit; subprocess tests also use short timeouts.
resource.setrlimit(resource.RLIMIT_CPU, (30, 1200))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(90)
sys.path.insert(0, str(app / "tests"))
def pins():
    paths = list(app.glob("*.py")) + list((app / "tests").glob("test_*.py")) + [app / "app.js", app / "index.html", app / "styles.css"]
    return {str(p.relative_to(app)): {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)}
before = pins()
(here / "source-before.json").write_text(json.dumps(before, indent=2)+"\n")
suite = unittest.defaultTestLoader.loadTestsFromName("test_worker")
result = unittest.TextTestRunner(verbosity=2).run(suite)
after = pins()
(here / "source-after.json").write_text(json.dumps(after, indent=2)+"\n")
original = json.loads((here.parent / "full-gate-01/source-before.json").read_text())
summary = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
           "skipped": len(result.skipped), "source_pins_unchanged": before==after==original,
           "passed": result.wasSuccessful() and before==after==original,
           "scope": "Only worker tests affected by the first harness's inherited hard CPU ceiling; application/native limits and source unchanged."}
(here / "result.json").write_text(json.dumps(summary, indent=2)+"\n")
print(json.dumps(summary), flush=True)
sys.exit(0 if summary["passed"] else 1)
