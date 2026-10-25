from pathlib import Path
import hashlib
import io
import json
import resource
import signal
import sys
import unittest

root = Path(__file__).resolve().parents[3]
app = root / "hydra-playground"
here = Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_CPU, (90, 1200))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(120)
sys.path.insert(0, str(app / "tests"))


def pins():
    paths = list(app.glob("*.py")) + list((app / "tests").glob("test_*.py"))
    paths += [app / "app.js", app / "index.html", app / "styles.css"]
    return {str(p.relative_to(app)): {"bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)}


before = pins()
with (here / "source-before.json").open("x") as stream:
    json.dump(before, stream, indent=2)
    stream.write("\n")
names = ["test_decomposition_memory", "test_decomposition_search_memory",
         "test_polynomial_continuations", "test_hybrid_search",
         "test_hybrid_runtime", "test_evaluate_advanced"]
suite = unittest.defaultTestLoader.loadTestsFromNames(names)
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
with (here / "output.txt").open("x") as stream:
    stream.write(log.getvalue())
print(log.getvalue(), end="", flush=True)
after = pins()
with (here / "source-after.json").open("x") as stream:
    json.dump(after, stream, indent=2)
    stream.write("\n")
summary = {"tests": result.testsRun, "failures": len(result.failures),
           "errors": len(result.errors), "skipped": len(result.skipped),
           "source_pins_unchanged": before == after,
           "passed": result.wasSuccessful() and before == after,
           "scope": "Focused v6 decomposition-memory integration and existing native search, continuation, runtime and evaluator regressions. Includes statement-only Pythagorean discovery and independent native replay; advisers are test doubles, no trained inference or actual solver."}
with (here / "result.json").open("x") as stream:
    json.dump(summary, stream, indent=2)
    stream.write("\n")
print(json.dumps(summary), flush=True)
sys.exit(0 if summary["passed"] else 1)
