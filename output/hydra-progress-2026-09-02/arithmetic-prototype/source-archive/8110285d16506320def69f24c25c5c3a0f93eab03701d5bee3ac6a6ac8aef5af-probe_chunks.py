"""Isolated native probes of generic polynomial chunk proposals, <=9s each."""
from pathlib import Path
import argparse
import hashlib
import json
import resource
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = ROOT / "hydra-playground"
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(HERE), str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
resource.setrlimit(resource.RLIMIT_CPU, (9, 9))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(9)

from arithmetic_search import _polynomial, _quote
from polynomial_chunks import polynomial_chunk_plan
from peano_lab.batch import MODEL_V1_COMMANDS
from peano_lab.engine.state import proof_size
from peano_lab.kernel.formulas import Eq, Forall, parse_formula_with_names, pretty_formula
from peano_lab.kernel.terms import Mul, Succ, Var
from peano_lab.ui.prove import SurfaceCapabilities, checked_surface_final
from training.peano_policy.search import _PrefixSnapshot, _canonical_goals, _new_owner, _replay

parser = argparse.ArgumentParser()
parser.add_argument("--degree", type=int, required=True)
parser.add_argument("--stage", choices=("expansion", "step"), default="expansion")
parser.add_argument("--plan-only", action="store_true")
parser.add_argument("--leaf", type=int)
parser.add_argument("--attempt", required=True)
args = parser.parse_args()
assert 2 <= args.degree <= 7
assert args.attempt.isascii() and args.attempt.replace("-", "").isalnum()
out = HERE / args.attempt
out.mkdir(exist_ok=False)


def power(term, degree):
    result = term
    for _ in range(degree - 1):
        result = Mul(result, term)
    return result


expanded = power(Succ(Var(0)), args.degree)
left = expanded if args.stage == "expansion" else Mul(
    _quote(_polynomial(power(Succ(Var(0)), args.degree - 1))), Succ(Var(0)))
equation = Eq(left, _quote(_polynomial(expanded)))
plan = polynomial_chunk_plan(equation, ["n"])
assert plan is not None, "no plan generated"
target_text = "forall n. " + pretty_formula(equation, ["n"])
commands = ("intro n",) + plan.commands
if args.leaf is not None:
    leaf = plan.obligations[args.leaf]
    target_text = leaf.get("generalized", "forall n. " + leaf["concrete"])
    if "generalized" in leaf:
        binders = target_text.removeprefix("forall ").split(".", 1)[0].split()
    else:
        binders = ["n"]
    commands = tuple("intro " + name for name in binders) + ("ring",)

metadata = {"schema": "hydra-polynomial-chunks-prototype-v1", "theorem": target_text,
    "commands": commands, "plan_only": args.plan_only, "leaf": args.leaf,
    "degree": args.degree, "stage": args.stage, "plan_obligations": plan.obligations,
    "wall_seconds": 9, "model_calls": 0, "vampire_calls": 0,
    "source_pins": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (Path(__file__), HERE / "polynomial_chunks.py", APP / "arithmetic_search.py",
                  SOURCE / "peano-lab/py/peano_lab/engine/ring.py")}}
(out / "attempt.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"theorem": target_text, "command_count": len(commands),
                  "obligation_count": len(plan.obligations), "plan_only": args.plan_only}), flush=True)
if args.plan_only:
    print(json.dumps({"commands": commands, "obligations": plan.obligations}), flush=True)
    raise SystemExit(0)

capabilities = SurfaceCapabilities(label="hydra-polynomial-chunk-prototype-no-imports",
    allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
original, names = parse_formula_with_names(target_text)
owner = _new_owner(original, names, target_text, classical=False, replay_id=0)
prefix = _PrefixSnapshot.capture(owner, commands=(), goals=_canonical_goals(owner), capabilities=capabilities)
started = time.monotonic()
rows = []
with (out / "edges.jsonl").open("x", encoding="utf-8") as stream:
    for index, command in enumerate(commands):
        step_started = time.monotonic()
        following, failed, error = _replay(original, names, target_text, prefix.commands + (command,),
            classical=False, capabilities=capabilities, replay_id=index + 1,
            prefix=prefix, expected_goals=prefix.goals)
        row = {"step": index + 1, "command": command,
               "elapsed_seconds": round(time.monotonic() - step_started, 6),
               "accepted": following is not None, "error": None if error is None else str(error)}
        if following is not None:
            row["goals_after"] = list(_canonical_goals(following))
            prefix = _PrefixSnapshot.capture(following, commands=prefix.commands + (command,),
                goals=tuple(row["goals_after"]), capabilities=capabilities)
        rows.append(row)
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        stream.flush()
        print(json.dumps({k: v for k, v in row.items() if k != "goals_after"}), flush=True)
        if following is None:
            break
    checked = prefix.state.is_done()
    nodes = None
    if checked:
        nodes = proof_size(checked_surface_final(prefix.state, original, classical=False, trace=None))
    result = {"kernel_checked": checked, "independent_batch_replay": False,
              "proof_nodes": nodes, "elapsed_seconds": round(time.monotonic() - started, 6),
              "accepted_steps": sum(row["accepted"] for row in rows),
              "attempted_steps": len(rows), "result_scope": "one original-theorem native finalizer; no second replay"}
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)
