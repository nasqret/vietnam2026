"""Two advisor requests, at most one actual fixed Research Vampire launch."""
from pathlib import Path
import resource
import signal
import sys
import time

OUT = Path(__file__).resolve().parent
APP = OUT.parents[2] / "hydra-playground"
sys.path.insert(0, str(APP))
assert sys.flags.isolated and sys.dont_write_bytecode
assert sys.argv[1:] == ["--mode", "search"]
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
signal.setitimer(signal.ITIMER_REAL, 24)

import worker
from vampire_limits import RUNTIME_POLICY, solver_limits
from vampire_process import VampireRunner
from vampire_bridge import CACHE_POLICY, VampireAdvisor, export_state

raw = sys.stdin.buffer.readline(worker.MAX_BODY_BYTES + 1)
request = worker.validate_request("search", worker.decode_json(raw.strip()))
assert request["search_mode"] == "symbolic" and request["search_profile"] == "research"
assert RUNTIME_POLICY == "hydra-playground-vampire-runtime-policy-v3"
assert CACHE_POLICY == "hydra-vampire-unsuccessful-exact-input-cache-v1"
assert solver_limits("research")["solver_rss_stop_bytes"] == 384 * 1024**2
worker.install_guard("search", allow_vampire=True, vampire_profile="research")
worker.load_kernel()
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic


class OneAttemptRunner:
    profile = "research"

    def __init__(self):
        self.actual = VampireRunner(self.profile)
        self.requests = 0
        self.result = None

    def __call__(self, text):
        if self.requests != 0:
            raise RuntimeError("The diagnostic refused a second underlying solver call.")
        self.requests += 1
        self.result = self.actual(text)
        return self.result


target, names = parse_formula_with_names(request["theorem"])
assert not names
state = apply_tactic(start(target, names), "intro", "")
problem = export_state(state)
assert problem.sha256 == "499ef2f6d3b361e66902ebc4f42fe13505eae0aadbd87a7b45065afcadad5704"
worker.emit("progress", {"phase": "vampire_cache_diagnostic_start", "problem_sha256": problem.sha256,
                         "profile": "research", "runtime_policy": RUNTIME_POLICY})
runner = OneAttemptRunner()
advisor = VampireAdvisor(runner)
start = time.monotonic()
first = advisor.advise(state)
first_seconds = time.monotonic() - start
second = second_seconds = None
if first["cache"]["stored"]:
    assert export_state(state).text.encode("utf-8") == problem.text.encode("utf-8")
    start = time.monotonic()
    second = advisor.advise(state)
    second_seconds = time.monotonic() - start
assert runner.requests == runner.actual.calls == 1
assert runner.result["executed"] is True
assert not any(name in sys.modules for name in ("mlx", "mlx_lm", "torch", "transformers"))
worker.emit("result", {"kind": "vampire-cache-only-diagnostic", "kernel_checked": False, "trace": [],
                       "model_invocations": 0, "search_invocations": 0,
                       "solver_invocations": runner.actual.calls, "problem_sha256": problem.sha256,
                       "first_advice": first, "second_advice": second, "cache_report": advisor.report(),
                       "first_request_seconds": first_seconds, "second_request_seconds": second_seconds,
                       "runner_result": runner.result, "runner_records": runner.actual.records})
