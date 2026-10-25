"""Prepare an authored continuation fixture from the actual selected train set.

This script only reads/writes JSON. Run the generated native request separately
when the root schedules a native slot. No generated request claims model work,
and the native child marks authored fixtures ineligible for teacher distillation.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import stat


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--selection-sha256", required=True)
    parser.add_argument("--state-id", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args(argv)
    maximum = 2 * 1024**2
    info = args.selection.lstat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= maximum:
        raise ValueError("Expected a bounded regular selection file.")
    with args.selection.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) != info.st_size or len(raw) > maximum or sha256(raw).hexdigest() != args.selection_sha256:
        raise ValueError("The exact selected training states are required.")
    selection = json.loads(raw)
    candidates = [row for row in selection["states"]
                  if row["id"] == args.state_id and row["split"] == "train"]
    if len(candidates) != 1:
        raise ValueError("Choose one exact already-selected training state; never substitute a holdout.")
    state = candidates[0]
    if len(state["all_goals_before"]) != 1 or not state["all_goals_before"][0].split("⊢", 1)[1].strip().startswith("∀"):
        raise ValueError("The authored introduction fixture needs one remaining universal goal.")
    commands = ["intro"]
    request = {"schema": "hydra-teacher-native-request-v1", "kind": "continuation",
        "state": state, "holdout": selection["holdout"],
        "plan": {"commands": commands, "source": "manual_fixture",
                 "reason": "Authored native continuation fixture; zero model calls.",
                 "plan_sha256": sha256(canonical(["manual_fixture", state["id"], commands])).hexdigest()}}
    directory = args.output_directory
    directory.mkdir(parents=True, exist_ok=False)
    requests = {"positive.json": request,
                "wrong-original.json": {**request, "state": {**state, "theorem": state["theorem"] + " + 1"}}}
    pins = {}
    for name, value in requests.items():
        data = canonical(value) + b"\n"
        with (directory / name).open("xb") as stream:
            stream.write(data)
        pins[name] = {"bytes": len(data), "sha256": sha256(data).hexdigest()}
    record = {"schema": "hydra-authored-teacher-native-fixture-v1",
        "selection_sha256": args.selection_sha256, "source_state_id": state["id"], "requests": pins,
        "expected": {"positive.json": "proved_with_independent_replay_and_distillation_ineligible",
                     "wrong-original.json": "original_prefix_state_mismatch_rejected"},
        "native_runs": 0, "model_calls": 0, "automatic_execution": False}
    with (directory / "manifest.json").open("xb") as stream:
        stream.write(canonical(record) + b"\n")
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
