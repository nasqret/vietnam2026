"""Saved-prediction/state wiring fixture; zero model or native execution."""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
assert args.output.resolve().parent == HERE and not args.output.exists(), "Fresh output under provider-audit required"
path = HERE / "sequential_lane.py"
spec = importlib.util.spec_from_file_location("isolated_sequential_lane", path)
lane = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lane
spec.loader.exec_module(lane)
proofs = HERE.parent / "wmi-evidence/proofs.jsonl"
assert hashlib.sha256(proofs.read_bytes()).hexdigest() == "0bfad5647672fd4c45f40ab76a1e204dc801f1500a50ae3840dcc2184aa40ec2"
rows = [json.loads(line) for line in proofs.read_text().splitlines()]
successes = [row for row in rows if row["autonomous_python_kernel_proof"]]
selected = [min(successes, key=lambda row: len(row["actions"])),
            next(row for row in successes if row["id"] == "c5-0e7a4634564441e09637546d"),
            max(successes, key=lambda row: len(row["actions"]))]


class SavedTransitions:
    def __init__(self, row):
        self.row = row
        self.trace = [step for step in row["native_result"]["trace"] if "v" in step]
        self.identity = {"source_commit": None, "environment_sha256": row["environment_sha256"],
                         "allowed_theorems": "original WMI fixture authority, not current Hydra",
                         "classical": False, "fixture": True}

    def initial(self, theorem, *, deadline):
        assert theorem == self.row["formula"]
        return self.trace[0]["goals_before"]

    def success_label(self, action):
        return " ".join(action.split())

    def run_prefix(self, theorem, actions, *, deadline):
        assert theorem == self.row["formula"] and list(actions) == self.row["actions"][:len(actions)]
        count = len(actions)
        complete = count == len(self.row["actions"])
        raw = copy.deepcopy(self.row["native_result"])
        raw.update(status="proved" if complete else "open", kernel_checked=complete,
            goals=self.trace[count - 1]["goals_after"], tactics_requested=count, tactics_applied=count,
            failed_tactics=0, trace=copy.deepcopy(self.trace[:count]),
            fixture_derived_from_saved_receipt=True)
        if complete:
            raw["trace"].append(copy.deepcopy(self.row["native_result"]["trace"][-1]))
        return raw

    def independent_replay(self, *_args, **_kwargs):
        raise AssertionError("Saved fixture must never pretend to execute native replay")


def provider_factory(row):
    offset = 0

    def factory(*, deadline, max_new_tokens, max_context_tokens):
        nonlocal offset
        saved = row["steps"][offset]
        offset += 1

        class SavedProvider:
            def propose(self, goals, *, max_candidates):
                assert max_candidates == 1
                assert lane.compact_prompt(goals) == saved["prompt"]
                assert max_context_tokens == saved["generation"]["max_context_tokens"]
                assert len(saved["generation"]["decision_ids"]) <= max_new_tokens
                return (saved["decoded"]["action"],)

            def report(self):
                return {"fixture": True, "actual_model_calls": 0, "generated_token_slots": 0,
                    "saved_fixture_decision_tokens": len(saved["generation"]["decision_ids"]),
                    "attempts": [{"prompt_sha256": saved["prompt_sha256"]}]}

        return SavedProvider()

    return factory


records = []
for row in selected:
    result = lane.run(row["formula"], native=SavedTransitions(row), provider_factory=provider_factory(row), saved_fixture=True)
    assert result["status"] == "saved_fixture_complete", result
    assert result["proved"] is False and result["actual_model_calls"] == result["actual_decision_tokens"] == 0
    assert result["actions"] == row["actions"] and not result["remaining_goals"]
    records.append({"source_id": row["id"], "actions": len(result["actions"]),
                    "prompt_hashes_match": True, "result": result})

# Two concrete boundary risks: too few actions and silently dropping open goals.
row = selected[0]
limited = lane.run(row["formula"], native=SavedTransitions(row), provider_factory=provider_factory(row),
                   limits=lane.Limits(max_actions=16), saved_fixture=True)
assert limited["status"] == "action_budget" and not limited["proved"] and len(limited["actions"]) == 16


class TruncatedGoals(SavedTransitions):
    def run_prefix(self, *args, **kwargs):
        raw = super().run_prefix(*args, **kwargs)
        if len(raw["goals"]) > 1:
            raw["goals"] = raw["goals"][:1]
        return raw


row = selected[1]
truncated = lane.run(row["formula"], native=TruncatedGoals(row), provider_factory=provider_factory(row), saved_fixture=True)
assert truncated["status"] == "error" and "Remaining native goals differ" in truncated["error"] and not truncated["proved"]
report = {"schema": "hydra-saved-sequential-wiring-fixture-v1", "status": "passed",
          "scope": "Saved predictions and saved transitions only; no new model inference or native proof execution",
          "model_calls": 0, "native_executions": 0, "new_proofs": 0,
          "sequential_lane_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
          "proofs_sha256": hashlib.sha256(proofs.read_bytes()).hexdigest(), "cases": records,
          "boundary_checks": {"16_action_budget_stops": True, "discarded_open_goal_rejected": True}}
with args.output.open("x") as out:
    out.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": "passed", "saved_cases": [{"id": r["source_id"], "actions": r["actions"]} for r in records],
                  "model_calls": 0, "native_executions": 0, "new_proofs": 0, "boundary_checks": 2}))
