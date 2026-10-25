"""Pure validation of one saved current-Hydra proof and altered metadata."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
assert args.output.resolve().parent == HERE and not args.output.exists(), "Fresh output under provider-audit required"
source = HERE / "sequential_lane.py"
spec = importlib.util.spec_from_file_location("isolated_sequential_metadata", source)
lane = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lane
spec.loader.exec_module(lane)
saved = HERE.parent / "replay/noimports-01/case-28-061dfe72dd3c/worker.stdout.jsonl"
receipt = json.loads(saved.read_text())["result"]
assert receipt["kernel_source_commit"] == lane.CURRENT_COMMIT
assert receipt["environment_sha256"] in lane.NO_IMPORT_ENVIRONMENTS
trace = [row for row in receipt["trace"] if "v" in row]
assert receipt["status"] == "proved" and receipt["tactics_applied"] == 35 and receipt["proof_nodes"] == 45


def validate(value):
    return lane.validate_native_receipt(value, theorem=receipt["theorem"], actions=receipt["commands"],
        expected_before=tuple(trace[-1]["goals_before"]), previous=trace,
        identity={"environment_sha256": receipt["environment_sha256"]},
        success_label=lambda action: " ".join(action.split()), expected_proof_nodes=receipt["proof_nodes"])


different_ids = copy.deepcopy(receipt)
different_ids.update(id="independent-request-fixture", session="independent-session-fixture")
for step in different_ids["trace"]:
    if "session" in step:
        step["session"] = "independent-session-fixture"
assert validate(different_ids)[2] is True
checks = {"different_request_and_session_metadata_accepted": True}
for name, mutate in [
    ("changed_goal_rejected", lambda r: r["trace"][10].update(goals_after=["⊢ 0 = 1"])),
    ("changed_tactic_rejected", lambda r: r["trace"][10].update(tactic="refl")),
    ("changed_certificate_nodes_rejected", lambda r: (r.update(proof_nodes=46), r["trace"][-1].update(proof_size=46))),
]:
    changed = copy.deepcopy(different_ids)
    mutate(changed)
    try:
        validate(changed)
    except ValueError:
        checks[name] = True
    else:
        raise AssertionError(name)
report = {"schema": "hydra-sequential-replay-metadata-fixture-v1", "status": "passed", "checks": checks,
          "scope": "One saved actual native receipt; metadata and rejection checks only. No new native/model execution or new proof.",
          "model_calls": 0, "native_executions": 0, "new_proofs": 0,
          "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "saved_native_receipt_sha256": hashlib.sha256(saved.read_bytes()).hexdigest()}
with args.output.open("x") as out:
    out.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
