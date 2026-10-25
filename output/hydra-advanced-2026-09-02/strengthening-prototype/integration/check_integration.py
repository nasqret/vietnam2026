"""Bounded native-only v4 prototype search; not an advisor benchmark."""
from pathlib import Path
import hashlib
import json
import resource
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
APP = ROOT / "hydra-playground"
sys.path[:0] = [str(HERE), str(HERE.parent), str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
resource.setrlimit(resource.RLIMIT_CPU, (140, 140))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(150)

import hybrid_search_v4 as hybrid

PINNED = (APP / "hybrid_search.py", APP / "arithmetic_search.py",
          HERE.parent / "finite_difference.py", HERE / "hybrid_search_v4.py")


def pins():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in PINNED}


before = pins()
started = time.monotonic()
rows = []
limits = hybrid.HybridLimits(max_depth=96, max_states=512, max_tactic_attempts=2048,
    max_expansions=64, max_frontier=128, candidates_per_state=48,
    max_macro_steps=8, closure_steps=16, heuristic_burst=8,
    max_model_calls=0, max_vampire_calls=0, wall_seconds=65)
examples = (
    ("cubic_mod6", "forall n. exists k. n*n*n=n+6*k"),
    ("three_consecutive_mod6", "forall n. exists k. n*(n+1)*(n+2)=6*k"),
)
for case_id, theorem in examples:
    print(json.dumps({"phase": "starting", "case_id": case_id}), flush=True)
    result = hybrid.search(theorem, limits=limits)
    with (HERE / (case_id + "-result.json")).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    row = {"case_id": case_id, "theorem": theorem,
           **{key: result.get(key) for key in (
               "status", "kernel_checked", "certificate_nodes", "elapsed_seconds",
               "states_expanded", "states_discovered", "tactic_attempts", "limited_by",
               "model_calls", "vampire_calls", "strengthening_candidates", "strengthening_expansions")},
           "commands": result["commands"]}
    print(json.dumps(row), flush=True)
    rows.append(row)
    assert result["status"] == "proof", row
    assert result["kernel_checked"] is True
    replay = result["replay"]
    assert replay["status"] == "proved" and replay["kernel_checked"] is True
    assert replay["goals"] == [] and replay["proof_nodes"] == result["certificate_nodes"]
    assert replay["theorem"] == result["theorem"]
    assert result["model_calls"] == result["vampire_calls"] == 0
    assert result["strengthening_candidates"] == 1
    assert any(line.startswith("suffices ") for line in result["commands"])
    assert {row["source"] for row in result["provenance"]} == {"heuristic"}
    assert [row["command"] for row in result["provenance"]] == result["commands"]
    assert sum(row.get("evidence", {}).get("strategy") == "finite_difference_strengthening"
               for row in result["provenance"]) == 7

after = pins()
assert after == before
record = {"schema": "hydra-finite-difference-integration-prototype-v1",
          "passed": True, "benchmark": False, "model_invocations": 0, "solver_invocations": 0,
          "timing_scope": "bounded native-only prototype, including independent full original-theorem replay",
          "elapsed_seconds": round(time.monotonic() - started, 3),
          "source_pins_before": before, "source_pins_after": after,
          "cases": rows}
with (HERE / "integration-result.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps({"phase": "complete", "passed": True, "elapsed_seconds": record["elapsed_seconds"]}), flush=True)
