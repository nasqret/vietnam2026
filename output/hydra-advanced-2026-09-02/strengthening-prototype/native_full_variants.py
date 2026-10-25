"""Bounded full native replay of variants of a newly discovered proof.

This reads this experiment's successful search script, regenerates the
projection from each actual target, and alpha-renames only its local binders.
It does not consult a theorem library or run a model, solver, or search.
"""
from pathlib import Path
import hashlib
import json
import re
import resource
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT / "hydra-playground")]
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(75)

import worker
worker.load_kernel()
from finite_difference import propose_strengthening
from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic
from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.ui.prove import SurfaceCapabilities

CAPABILITIES = SurfaceCapabilities(label="finite-difference-full-variant-replay",
    allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
PROOF_PATH = HERE / "integration/cubic_mod6-result.json"
original = json.loads(PROOF_PATH.read_text())
assert original["status"] == "proof" and original["kernel_checked"] is True
assert original["replay"]["status"] == "proved" and original["replay"]["kernel_checked"] is True
assert original["model_calls"] == original["vampire_calls"] == 0
connector_start = next(i for i, item in enumerate(original["commands"]) if item.startswith("suffices "))
suffix = tuple(original["commands"][connector_start + 7:])
assert suffix[0] == "intro" and suffix[1].startswith("induction ")
original_parameter = suffix[1].split()[1]


def state_after(theorem, commands):
    target, names = parse_formula_with_names(theorem)
    state = start(target, names)
    for command in commands:
        tactic, _, args = command.partition(" ")
        state = apply_tactic(state, tactic, args)
    return state


def fresh(base, used):
    name, index = base, 1
    while name in used:
        name = base + str(index)
        index += 1
    used.add(name)
    return name


def alpha_suffix(goal):
    used = set(goal.variables) | {name for name, _ in goal.context}
    parameter = fresh("fd_step", used)
    used.add("IH")
    witness = fresh("x", used)
    used.add("IH_witness")
    auxiliary = fresh("x", used)
    mapping = {original_parameter: parameter, "x": witness, "x1": auxiliary}
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(key) for key in mapping) + r")\b")
    renamed = tuple(pattern.sub(lambda match: mapping[match.group()], command) for command in suffix[1:])
    return ("intro " + parameter,) + renamed


started = time.monotonic()
rows = []
variants = (
    ("alpha_renamed", "forall q. exists r. q*q*q=q+6*r", ("intro q",)),
    ("unused_scope_parameter", "forall a b. exists c. a*a*a=a+6*c", ("intro a", "intro b")),
    ("hypothesis_name_collisions", "forall z. z=z -> z=z -> exists k. z*z*z=z+6*k",
     ("intro z", "intro x", "intro x1")),
)
for case_id, theorem, prefix in variants:
    state = state_after(theorem, prefix)
    goal = state.current()
    proposal = propose_strengthening(goal, goal.target, goal.context)
    assert proposal is not None, case_id
    commands = prefix + proposal.commands + alpha_suffix(goal)
    assert len(commands) <= 160 and all(len(line.encode()) <= 512 for line in commands)
    result = run_proof(theorem, commands, request_id=case_id, classical=False,
                       on_error="stop", capabilities=CAPABILITIES, trace_byte_limit=128 * 1024)
    record = result.to_dict(include_trace=False)
    assert result.status == "proved" and result.kernel_checked is True, (case_id, record)
    assert not result.goals
    target, names = parse_formula_with_names(theorem)
    assert record["theorem"] == pretty_formula(target, list(names))
    row = {"case_id": case_id, "actual_theorem": theorem, "commands": commands,
           "result": record, "prototype_only": True, "model_invocations": 0, "solver_invocations": 0}
    rows.append(row)
    print(json.dumps({"case_id": case_id, "status": result.status,
                      "kernel_checked": result.kernel_checked, "proof_nodes": record["proof_nodes"]}), flush=True)

false_target = "forall n. exists k. n*n*n=n+6*k+1"
rejected = run_proof(false_target, tuple(original["commands"]), request_id="wrong-full-target",
                     classical=False, on_error="stop", capabilities=CAPABILITIES, trace_byte_limit=128 * 1024)
assert rejected.status == "tactic_error" and rejected.kernel_checked is False and rejected.goals
rows.append({"case_id": "wrong_full_target", "actual_theorem": false_target,
             "commands": original["commands"], "result": rejected.to_dict(include_trace=False),
             "wrong_target_rejected": True, "model_invocations": 0, "solver_invocations": 0})

record = {"schema": "hydra-finite-difference-full-native-variants-v1", "passed": True,
          "benchmark": False, "timing_scope": "native replay variants, not a search or advisor benchmark",
          "elapsed_seconds": round(time.monotonic() - started, 6),
          "cpu_limit_seconds": 60, "wall_limit_seconds": 75,
          "prototype_sha256": hashlib.sha256((HERE / "finite_difference.py").read_bytes()).hexdigest(),
          "discovered_proof_sha256": hashlib.sha256(PROOF_PATH.read_bytes()).hexdigest(),
          "full_theorems_proved": len(variants), "false_target_rejected": True, "cases": rows}
output = HERE / "native-full-variants-result.json"
with output.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps({"status": "passed", "full_theorems_proved": len(variants),
                  "false_target_rejected": True, "elapsed_seconds": record["elapsed_seconds"],
                  "record": str(output)}), flush=True)
