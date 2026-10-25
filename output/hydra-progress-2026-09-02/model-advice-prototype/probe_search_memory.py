"""Finite native search integration probe with a clearly synthetic provider."""
from pathlib import Path
import json
import resource
import signal
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = ROOT / "hydra-playground"
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
assert sys.flags.isolated and sys.dont_write_bytecode
resource.setrlimit(resource.RLIMIT_CPU, (12, 12))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(15)
sys.path[:0] = [str(HERE), str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
import hybrid_search


class SyntheticProvider:
    def __init__(self):
        self.calls = 0
        self.goals = []

    def propose(self, goals, *, max_candidates):
        assert max_candidates == 4
        self.calls += 1
        self.goals.append(goals)
        return ("exfalso", "symm", "refl", "simp")


provider = SyntheticProvider()
result = hybrid_search.search("0 = 1", model_policy=provider,
    limits=hybrid_search.HybridLimits(max_depth=24, max_states=128,
        max_tactic_attempts=256, max_expansions=32, max_model_calls=16,
        max_vampire_calls=0, wall_seconds=8))
assert result["status"] != "proof" and result["kernel_checked"] is False
assert result["model_calls"] == provider.calls == len(provider.goals)
assert len(set(provider.goals)) == len(provider.goals)
assert result["model_repeated_prompts_skipped"] > 0
assert result["model_advice_memory"]["tactics_reused"] is False
record = {"scope": "Synthetic four-line provider with real unchanged native tactic execution; no model inference or solver invocation.",
          "theorem": result["theorem"], "status": result["status"],
          "kernel_checked": result["kernel_checked"], "synthetic_provider_calls": provider.calls,
          "states_expanded": result["states_expanded"], "elapsed_seconds": result["elapsed_seconds"],
          "model_advice_memory": result["model_advice_memory"]}
with (HERE / "native-integration-01.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps({"status": "passed", "synthetic_provider_calls": provider.calls,
                  "repeated_prompts_skipped": result["model_repeated_prompts_skipped"],
                  "native_result": result["status"]}))
