"""One bounded CPU prefix fixture. Root runs after its other CPU batch finishes.

No model loading or proof claim. Compare all ordered native goals rendered with
search's fresh aliases and with branch-local persistent model-visible aliases.
"""
from pathlib import Path
import hashlib
import json
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EVIDENCE = HERE.parent / "wmi-evidence"
PROOF_SHA = "0bfad5647672fd4c45f40ab76a1e204dc801f1500a50ae3840dcc2184aa40ec2"
WORKER_SHA = "e7923426cf39a68719fc79f8efc1db0cf016edf03bd79d248a94ac06235de951"
CASE = "c5-0e7a4634564441e09637546d"
FINAL_STEP = 43


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(goals):
    return "HA model-v3 library-prefix=247/247\n" + json.dumps({"focus": 0, "goals": list(goals)}, ensure_ascii=False, separators=(",", ":")) + "\nTactic:"


class HardDeadline(BaseException):
    pass


def alarm(*_args):
    raise HardDeadline("30-second state fixture deadline")


def main():
    path = EVIDENCE / "proofs.jsonl"
    assert digest(path) == PROOF_SHA
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    row = next(row for row in rows if row["id"] == CASE)
    assert row["autonomous_python_kernel_proof"] and row["steps"][FINAL_STEP - 1]["index"] == FINAL_STEP
    assert digest(REPO / "hydra-playground/worker.py") == WORKER_SHA
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(REPO / "hydra-playground"))
    import worker
    _validate, _run_proof, SurfaceCapabilities, commands, _oversized = worker.load_kernel()
    from peano_lab.batch import parse_formula_with_names
    from peano_lab.engine.trace import render_goals
    from peano_lab.ui.prove import run_surface
    from training.peano_policy.search import _new_owner, _canonical_goals
    import training.peano_policy.search as original_search
    assert Path(original_search.__file__).resolve() == worker.SOURCE / "training/peano_policy/search.py"
    summary = json.loads((EVIDENCE / "summary.json").read_text())
    pins = {name: digest(worker.SOURCE / name) for name in summary["native_source_files_sha256"]}
    caps = SurfaceCapabilities(label="hydra-authority-no-imports-v1", allowed_commands=frozenset(commands), allowed_theorems=frozenset())
    formula, names = parse_formula_with_names(row["formula"])
    owner = _new_owner(formula, names, row["formula"], classical=False, replay_id=0)
    model_aliases, observations = {}, []
    started = time.monotonic()
    for index in range(FINAL_STEP):
        expected = json.loads(row["steps"][index]["prompt"].split("\n", 2)[1])["goals"]
        canonical = list(_canonical_goals(owner))
        persistent = render_goals(owner.state, meta_names=model_aliases)
        observations.append({"step": index + 1, "canonical_matches": canonical == expected,
            "persistent_matches": persistent == expected, "goals": len(expected),
            "expected_prompt_sha256": row["steps"][index]["prompt_sha256"],
            "canonical_prompt_sha256": hashlib.sha256(compact(canonical).encode()).hexdigest(),
            "persistent_prompt_sha256": hashlib.sha256(compact(persistent).encode()).hexdigest()})
        if index + 1 == FINAL_STEP:
            final = {"wmi_goals": expected, "canonical_search_goals": canonical,
                     "persistent_model_visible_goals": persistent, "alias_map": list(model_aliases.items())}
            break
        owner = run_surface(owner, row["actions"][index], capabilities=caps, record_trace=False)
        assert owner.trace.record_count == 0
    assert all(digest(worker.SOURCE / name) == checksum for name, checksum in pins.items())
    assert digest(REPO / "hydra-playground/worker.py") == WORKER_SHA and digest(path) == PROOF_SHA
    assert all(item["persistent_matches"] for item in observations), "Current native transition differs beyond alias canonicalization"
    assert not observations[-1]["canonical_matches"], "Expected observed alias mismatch did not reproduce"
    report = {"schema": "hydra-state-render-fixture-v1", "status": "passed", "case_id": CASE,
              "actions_replayed": FINAL_STEP - 1, "native_proof_claim": False, "model_calls": 0,
              "wall_seconds": time.monotonic() - started, "native_commit": worker.SOURCE_COMMIT,
              "current_native_source_pins": pins, "worker_sha256": WORKER_SHA, "proofs_sha256": PROOF_SHA,
              "observations": observations, "final": final}
    with (HERE / "STATE_RENDER_FIXTURE.json").open("x") as out:
        out.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "passed", "case_id": CASE, "actions_replayed": FINAL_STEP - 1,
                      "canonical_mismatch_steps": [x["step"] for x in observations if not x["canonical_matches"]],
                      "all_persistent_renderings_match": True, "model_calls": 0}))


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 30)
    try:
        main()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
