"""Bounded native checks for the proposal connector, not a search benchmark."""
from pathlib import Path
import hashlib
import json
import resource
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "hydra-playground"), str(HERE)]
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(45)

import worker
worker.load_kernel()
from finite_difference import propose_strengthening
from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic
from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.ui.prove import SurfaceCapabilities

CAPABILITIES = SurfaceCapabilities(label="finite-difference-prototype-native",
    allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())


def state_after(theorem, commands):
    target, names = parse_formula_with_names(theorem)
    state = start(target, names)
    for command in commands:
        tactic, _, args = command.partition(" ")
        state = apply_tactic(state, tactic, args)
    return state


started = time.monotonic()
rows = []
examples = (
    ("forall n. exists k. n*n*n=n+6*k", ("intro n",)),
    ("forall n. exists k. 6*k+n=n*n*n", ("intro n",)),
    ("forall n m. exists k. n*n*n=n+6*k", ("intro n", "intro m")),
    ("forall n. n=n -> n=n -> exists k. n*n*n=n+6*k", ("intro n", "intro x", "intro x1")),
    ("forall hydra_fd. exists k. hydra_fd*hydra_fd*hydra_fd=hydra_fd+6*k", ("intro hydra_fd",)),
    ("forall n. exists k. n*(n+1)*(n+2)=6*k", ("intro n",)),
)
for theorem, prefix in examples:
    state = state_after(theorem, prefix)
    goal = state.current()
    hint = propose_strengthening(goal, goal.target, goal.context)
    assert hint is not None, theorem
    result = run_proof(theorem, prefix + hint.commands, request_id="finite-difference-connector",
                       classical=False, on_error="stop", capabilities=CAPABILITIES,
                       trace_byte_limit=128 * 1024)
    after = state_after(theorem, prefix + hint.commands)
    assert len(after.goals) == 1 and after.current().target == hint.strengthened, theorem
    assert after.target == state.target
    assert result.status == "open" and not result.kernel_checked, result.to_dict(include_trace=False)
    rows.append({"theorem": theorem, "prefix": prefix, "commands": hint.commands,
                 "residual_goal": pretty_formula(after.current().target, list(after.current().variables)),
                 "connector_checked": True, "theorem_proved": False})

# A deliberately wrong, untrusted proposal must not prove a near-miss target.
truth = "forall n. exists k. n*n*n=n+6*k"
false_target = "forall n. exists k. n*n*n=n+6*k+1"
state = state_after(truth, ("intro n",))
goal = state.current()
hint = propose_strengthening(goal, goal.target, goal.context)
rejected = run_proof(false_target, ("intro n",) + hint.commands,
                     request_id="finite-difference-wrong-target", classical=False,
                     on_error="stop", capabilities=CAPABILITIES, trace_byte_limit=128 * 1024)
assert rejected.status == "tactic_error" and not rejected.kernel_checked
assert rejected.goals
rows.append({"theorem": false_target, "wrong_proposal_rejected": True,
             "status": rejected.status, "theorem_proved": False})

record = {"schema": "hydra-finite-difference-native-connector-prototype-v1",
          "benchmark": False, "timing_scope": "isolated connector prototype; concurrent baseline may be running",
          "elapsed_seconds": round(time.monotonic() - started, 6),
          "cpu_limit_seconds": 30, "wall_limit_seconds": 45,
          "prototype_sha256": hashlib.sha256((HERE / "finite_difference.py").read_bytes()).hexdigest(),
          "cases": rows, "passed": True, "full_theorems_proved": 0}
path = HERE / "native-connector-result.json"
with path.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps({"status": "passed", "connector_variants": len(examples),
                  "wrong_target_rejected": True, "elapsed_seconds": record["elapsed_seconds"],
                  "record": str(path)}))
