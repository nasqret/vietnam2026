"""One diagnostic of the recorded first Vampire problem; no search or model."""
from pathlib import Path
import hashlib
import json
import os
import signal
import sys
import threading
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
APP = ROOT / "hydra-playground"
ORIGINAL = OUT.parent / "attempt-02/result.json"
EXPECTED_RESULT = "b268020ad74db51eb2b91048e22b35899da218082d9a1d77a4420d41f988193c"
EXPECTED_PROBLEM = "3f89e8291a73faeab4af7415b02b4ad306121794592c26aff5ade377a3157077"
sys.path.insert(0, str(APP))
import worker
import server
from vampire_process import VampireRunner, MAX_RSS, SOLVER_ARGS


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write_json(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


assert sys.flags.isolated and sys.dont_write_bytecode
assert not (OUT / "problem.p").exists(), "No automatic diagnostic retry."
server.process_snapshot()  # Fail before any solver invocation if accounting is unavailable.
assert pin(ORIGINAL)["sha256"] == EXPECTED_RESULT
original = json.loads(ORIGINAL.read_bytes())
for name, expected in original["source_pins_before"].items():
    assert pin(APP / name) == expected, "Original source pin changed: " + name
search = original["last_job"]["result"]["search"]
assert not any("stdout" in item or "stderr" in item for item in search["vampire_runs"])
branches = {item["id"]: item for item in search["branches"] if item.get("id") is not None}
path, branch_id = [], 5
while branch_id:
    assert len(path) < 32
    branch = branches[branch_id]
    path.append(branch["command"])
    branch_id = branch["parent_id"]
commands = tuple(reversed(path))
assert commands == ("intro", "intro", "intro", "cases h", "cases h_left")
worker.load_kernel()
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.batch import MODEL_V1_COMMANDS
from peano_lab.ui.prove import SurfaceCapabilities
from training.peano_policy.search import _replay, _canonical_goals, state_sha256
from vampire_bridge import export_state
theorem = original["canonical_theorem"]
target, names = parse_formula_with_names(theorem)
assert not names
capabilities = SurfaceCapabilities(label="hydra-authority-no-imports-v1",
    allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
owner, failed, error = _replay(target, names, theorem, commands, classical=False,
    capabilities=capabilities, replay_id=0)
assert owner is not None and failed is None and error is None
state_hash = state_sha256(_canonical_goals(owner))
assert state_hash == branches[5]["state_sha256"]
problem = export_state(owner.state)
assert problem.sha256 == EXPECTED_PROBLEM == search["vampire_runs"][0]["problem_sha256"]
with (OUT / "problem.p").open("x") as stream:
    stream.write(problem.text)
write_json("reconstruction.json", {"schema": "hydra-fermat-vampire-branch-reconstruction-v1",
    "original_result": {"path": str(ORIGINAL), **pin(ORIGINAL)}, "original_job_id": original["job_id"],
    "branch_id": 5, "commands": commands, "state_sha256": state_hash,
    "problem": {"path": str(OUT / "problem.p"), **pin(OUT / "problem.p")},
    "kernel_checked": False, "scope": "one original open prefix, not a theorem proof"})

# Reuse the existing fixed runner/helper. The monitor adds the same sampled
# RSS bound used by the server; it includes this process's transient ps child,
# conservatively, and never signals an observed PID. The runner owns cleanup.
stop = threading.Event()
samples, peaks, faults = [], [], []
def monitor():
    while not stop.is_set():
        try:
            rows = server.process_snapshot()
            rss = max((row[2] for row in rows.values() if row[0] == os.getpid()), default=0)
            samples.append(1)
            peaks.append(rss)
            if rss > MAX_RSS:
                raise RuntimeError("The diagnostic child exceeded the existing sampled RSS bound.")
        except Exception as error:
            faults.append(str(error))
            if not stop.is_set():
                os.kill(os.getpid(), signal.SIGUSR1)
            return
        stop.wait(0.04)

def guard(*_):
    raise RuntimeError("Diagnostic process accounting failed: " + "; ".join(faults))

previous = signal.signal(signal.SIGUSR1, guard)
watcher = threading.Thread(target=monitor, daemon=True)
runner = VampireRunner()
watcher.start()
try:
    result = runner(problem.text)  # Exactly ONE solver attempt, fixed -t 1 / -m 256.
finally:
    stop.set()
    watcher.join(timeout=3)
    signal.signal(signal.SIGUSR1, previous)
assert not watcher.is_alive() and not faults, faults
assert runner.calls == 1 and result["executed"] is True
assert result["problem_sha256"] == EXPECTED_PROBLEM
for name, expected in original["source_pins_before"].items():
    assert pin(APP / name) == expected, "Source changed during the diagnostic: " + name
with (OUT / "stdout.txt").open("x") as stream:
    stream.write(result["stdout"])
with (OUT / "stderr.txt").open("x") as stream:
    stream.write(result["stderr"])
raw = result["stdout"] + result["stderr"]
classification = ("normal_solver_time_limit" if "Time limit" in raw or "time limit" in raw
                  else "inspect_recorded_solver_output")
write_json("result.json", {"schema": "hydra-fermat-vampire-diagnostic-v1",
    "scope": "ONE additional diagnostic; separate from the four original solver runs",
    "original_job_id": original["job_id"], "original_branch_id": 5,
    "original_solver_record": search["vampire_runs"][0], "diagnostic_calls": runner.calls,
    "automatic_retry": False, "model_calls": 0, "http_requests": 0, "training_performed": False,
    "kernel_verified": False, "solver_args": SOLVER_ARGS, "runner_result": result,
    "classification": classification, "sample_count": len(samples),
    "observed_max_direct_child_rss_bytes": max(peaks, default=0), "source_pins_unchanged": True,
    "outer_exit_observation": "Obtain the actual tool completion separately; this file is not that receipt."})
print(json.dumps({"classification": classification, "diagnostic_calls": runner.calls,
    "exit_code": result["exit_code"], "elapsed_seconds": result["elapsed_seconds"],
    "problem_sha256": problem.sha256, "stdout": result["stdout"], "stderr": result["stderr"],
    "source_pins_unchanged": True}, indent=2))
