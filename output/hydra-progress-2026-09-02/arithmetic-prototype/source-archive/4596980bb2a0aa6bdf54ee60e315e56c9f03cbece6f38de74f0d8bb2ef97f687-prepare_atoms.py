"""Prepare atom-preserving candidate scripts, without running native tactics."""
from pathlib import Path
import argparse
import hashlib
import json
import signal
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = ROOT / "hydra-playground"
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(HERE), str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
signal.alarm(9)

from atom_polynomial import atom_polynomial_chunk_plan
from peano_lab.kernel.formulas import Forall, parse_formula_with_names

parser = argparse.ArgumentParser()
parser.add_argument("--attempt", required=True)
args = parser.parse_args()
assert args.attempt.isascii() and args.attempt.replace("-", "").isalnum()
out = HERE / args.attempt
out.mkdir(exist_ok=False)
old = json.loads((HERE / "prepared-plans-05/plans.json").read_text())
cases = []
for case in old["cases"]:
    if case["case_id"] not in ("pythagorean_positive", "sophie_coordinates"):
        continue
    formula, _ = parse_formula_with_names(case["theorem"])
    assert type(formula) is Forall and type(formula.body) is Forall
    plan = atom_polynomial_chunk_plan(formula.body.body, ["b", "a"])
    cases.append({"case_id": case["case_id"], "theorem": case["theorem"],
        "plan_generated": plan is not None,
        "commands": None if plan is None else ["intro a", "intro b", *plan.commands],
        "analysis": None if plan is None else plan.analysis,
        "obligations": [] if plan is None else plan.obligations})
pins = {}
for path in (Path(__file__), HERE / "atom_polynomial.py", HERE / "polynomial_chunks.py", APP / "arithmetic_search.py"):
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    pins[str(path.relative_to(ROOT))] = digest
    archive = HERE / "source-archive" / (digest + "-" + path.name)
    if not archive.exists():
        with archive.open("xb") as stream:
            stream.write(data)
result = {"schema": "hydra-polynomial-atom-plans-v1", "native_execution": False,
          "proof_claims": False, "source_pins": pins, "cases": cases}
with (out / "plans.json").open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
for case in cases:
    print(json.dumps({"case_id": case["case_id"], "plan_generated": case["plan_generated"],
        "steps": None if case["commands"] is None else len(case["commands"]),
        "analysis": case["analysis"], "commands": case["commands"]}, ensure_ascii=False))
