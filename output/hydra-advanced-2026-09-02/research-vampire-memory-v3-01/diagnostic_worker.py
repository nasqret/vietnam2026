"""Exactly one guarded Research Vampire call; no HTTP, search, or model."""
from pathlib import Path
import json
import resource
import signal
import sys

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

raw = sys.stdin.buffer.readline(worker.MAX_BODY_BYTES + 1)
request = worker.validate_request("search", worker.decode_json(raw.strip()))
assert request["search_mode"] == "symbolic" and request["search_profile"] == "research"
assert RUNTIME_POLICY == "hydra-playground-vampire-runtime-policy-v3"
assert solver_limits("research")["solver_memory_mib"] == 256
assert solver_limits("research")["sampled_rss_bytes"] == 512 * 1024**2
assert solver_limits("research")["solver_rss_stop_bytes"] == 384 * 1024**2
worker.install_guard("search", allow_vampire=True, vampire_profile="research")
worker.load_kernel()
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic
from vampire_bridge import export_state

target, names = parse_formula_with_names(request["theorem"])
assert not names
state = apply_tactic(start(target, names), "intro", "")
problem = export_state(state)
worker.emit("progress", {"phase": "vampire_diagnostic_start", "problem_sha256": problem.sha256,
                         "profile": "research", "runtime_policy": RUNTIME_POLICY})
runner = VampireRunner("research")
result = runner(problem.text)
assert runner.calls == 1 and result["executed"] is True
assert not any(name in sys.modules for name in ("mlx", "mlx_lm", "torch", "transformers"))
worker.emit("result", {"kind": "vampire-only-diagnostic", "kernel_checked": False, "trace": [],
                       "model_invocations": 0, "solver_invocations": runner.calls,
                       "problem_sha256": problem.sha256, "runner_result": result})
