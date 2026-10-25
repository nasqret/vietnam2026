"""One-shot F7 memory diagnostic under the existing owned-process supervisor.

The only substitution is a fixed diagnostic worker script, as in the existing
lifecycle fixtures. Process ownership, RSS/output monitoring, cancellation,
group cleanup, and the real fixed-profile subprocess audit remain unchanged.
"""
from pathlib import Path
import hashlib
import json
import resource
import sys
import threading
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
APP = ROOT / "hydra-playground"
ORIGINAL = OUT.parent / "research-hybrid-01/000-fermat_7-hybrid.json"
sys.path.insert(0, str(APP))
assert sys.flags.isolated and sys.dont_write_bytecode
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

import server
import worker
from vampire_limits import RUNTIME_POLICY, solver_args, solver_limits
from vampire_process import metadata_status, package


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write_json(name, value):
    with (OUT / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


assert not (OUT / "plan.json").exists(), "This diagnostic may not be automatically retried."
server.process_snapshot()  # Fail closed before any solver starts if accounting is unavailable.
assert RUNTIME_POLICY == "hydra-playground-vampire-runtime-policy-v2"
limits = solver_limits("research")
assert (limits["solver_seconds"], limits["cpu_seconds"], limits["wall_seconds"],
        limits["solver_memory_mib"], limits["sampled_rss_bytes"]) == (15, 16, 18, 256, 512 * 1024**2)
_, manifest, manifest_pin = package(verify_binary=True)
original = json.loads(ORIGINAL.read_bytes())
assert original["case_id"] == "fermat_7" and original["outcome"] == "server_failure"
progress = original["last_job"]["progress"]
assert progress["phase"] == "vampire" and progress["branch_id"] == progress["depth"] == 1
request = {"theorem": original["normalized_request"]["theorem"], "search_mode": "symbolic",
           "search_profile": "research", "max_model_calls": 32, "beam_width": 8}
# The model-budget field is required by the unchanged transport validator;
# this fixed worker has no model or search path and never uses that field.
assert worker.validate_request("search", request) == request
worker.load_kernel()
from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic
from vampire_bridge import export_state
target, names = parse_formula_with_names(request["theorem"])
assert not names
state = apply_tactic(start(target, names), "intro", "")
problem = export_state(state)
files = ("server.py", "worker.py", "search_settings.py", "vampire_limits.py",
         "vampire_process.py", "vampire_worker.py", "vampire_bridge.py")
before = {name: pin(APP / name) for name in files}
plan = {"schema": "hydra-research-vampire-memory-diagnostic-plan-v2",
        "scope": "ONE new solver-only diagnostic, separate from both failed hybrid jobs",
        "automatic_retry": False, "solver_invocation_limit": 1,
        "model_invocations": 0, "search_invocations": 0, "http_requests": 0,
        "original_case": {"path": str(ORIGINAL), **pin(ORIGINAL)},
        "original_job_id": original["job_id"], "original_branch_id": 1,
        "prefix": ["intro"], "canonical_theorem": pretty_formula(target, list(names)),
        "problem_sha256": problem.sha256, "request": request,
        "runtime_policy": RUNTIME_POLICY, "solver_args": solver_args("research"), "limits": limits,
        "package_manifest": manifest_pin, "binary": manifest["executable"],
        "package_metadata": metadata_status("research"), "source_pins_before": before,
        "diagnostic_worker": pin(OUT / "diagnostic_worker.py"),
        "supervisor": "existing server.run_worker; fixed diagnostic worker only",
        "supervisor_cancellation_seconds": 26, "native_theorem_proved": False}
write_json("plan.json", plan)
with (OUT / "problem.p").open("x", encoding="utf-8") as stream:
    stream.write(problem.text)

cancel = threading.Event()
watchdog = threading.Timer(26, cancel.set)
events = []
watchdog.start()
try:
    with patch.object(server, "WORKER", OUT / "diagnostic_worker.py"):
        outcome = server.run_worker("search", request, cancel, lambda event: events.append(event))
finally:
    watchdog.cancel()
    watchdog.join(timeout=2)
after = {name: pin(APP / name) for name in files}
final = outcome.get("result")
runner_result = final.get("runner_result") if final else None
if runner_result:
    for channel in ("stdout", "stderr"):
        with (OUT / (channel + ".txt")).open("x", encoding="utf-8") as stream:
            stream.write(runner_result[channel])
valid = (outcome.get("quiescent") is True and not outcome.get("error")
         and not outcome.get("cancelled") and outcome.get("worker_exit_code") == 0
         and before == after and final is not None and final.get("solver_invocations") == 1
         and final.get("model_invocations") == 0 and final.get("kernel_checked") is False
         and final.get("problem_sha256") == problem.sha256
         and 0 < outcome.get("peak_sampled_solver_rss_bytes", 0) <= limits["sampled_rss_bytes"]
         and type(runner_result) is dict
         and runner_result.get("executed") is True and type(runner_result.get("exit_code")) is int)
record = {"schema": "hydra-research-vampire-memory-diagnostic-v2", "passed": bool(valid),
          "scope": plan["scope"], "automatic_retry": False, "native_theorem_proved": False,
          "runtime_policy": RUNTIME_POLICY, "problem_sha256": problem.sha256,
          "source_pins_before": before, "source_pins_after": after,
          "source_pins_unchanged": before == after, "progress_events": events, "outcome": outcome,
          "actual_tool_exit": "Record the actual tool completion separately; this file is not that receipt."}
write_json("result.json", record)
print(json.dumps({"passed": bool(valid), "runtime_policy": RUNTIME_POLICY,
                  "worker_exit_code": outcome.get("worker_exit_code"),
                  "solver_exit_code": runner_result.get("exit_code") if runner_result else None,
                  "solver_status": runner_result.get("status") if runner_result else None,
                  "solver_termination": runner_result.get("termination") if runner_result else None,
                  "peak_sampled_solver_rss_bytes": outcome.get("peak_sampled_solver_rss_bytes"),
                  "elapsed_seconds": outcome.get("elapsed_seconds"),
                  "quiescent": outcome.get("quiescent"), "error": outcome.get("error"),
                  "record": str(OUT / "result.json")}), flush=True)
raise SystemExit(0 if valid else 2)
