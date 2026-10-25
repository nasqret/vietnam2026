"""Native integration for compact routing, fallback, and observed proof costs."""
from pathlib import Path
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
SOURCE = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
import hybrid_search as hybrid
from peano_lab.batch import MODEL_V1_COMMANDS
from peano_lab.ui.prove import SurfaceCapabilities


THEOREM = "forall a b n. (a+n)+S b=(a+b)+S n"


def limits():
    return hybrid.HybridLimits(max_states=64, max_expansions=24,
        max_tactic_attempts=192, max_model_calls=0, max_vampire_calls=0,
        wall_seconds=8)


class CompactSearchTests(unittest.TestCase):
    def test_real_compact_proof_has_checked_provenance_and_measured_cost(self):
        result = hybrid.search(THEOREM, limits=limits())
        self.assertEqual(result["status"], "proof", result["diagnostics"])
        self.assertTrue(result["replay"]["kernel_checked"])
        self.assertEqual(result["replay"]["goals"], [])
        self.assertEqual(result["commands"][-1], "compact_arith")
        self.assertEqual(result["provenance"][-1]["source"], "heuristic")
        self.assertEqual(result["provenance"][-1]["evidence"]["strategy"], "compact_arith_dispatch")
        self.assertEqual(result["compact_arith_attempts"], 1)
        self.assertEqual(result["compact_arith_accepted"], 1)
        self.assertEqual(result["compact_arith_rejected"], 0)
        cost = result["proof_cost"]["final"]
        self.assertEqual(cost["stage"], "final")
        self.assertEqual(cost["status"], "complete")
        self.assertEqual(cost["structural_occurrences"], result["certificate_nodes"])
        self.assertLessEqual(cost["distinct_objects"], cost["structural_occurrences"])
        self.assertFalse(cost["proof_check_performed"])
        self.assertIsNone(result["proof_cost"]["best_partial"])
        for key in ("transition_seconds", "finalization_seconds", "independent_replay_seconds"):
            self.assertGreaterEqual(result["native_timing"][key], 0)

    def test_disallowed_compact_tactic_keeps_native_fallback_available(self):
        authority = SurfaceCapabilities(label="compact-disallowed-integration",
            allowed_commands=MODEL_V1_COMMANDS - {"compact_arith"}, allowed_theorems=frozenset())
        result = hybrid.search(THEOREM, capabilities=authority, limits=limits())
        self.assertEqual(result["status"], "proof", result["diagnostics"])
        self.assertTrue(result["replay"]["kernel_checked"])
        self.assertNotIn("compact_arith", result["commands"])
        self.assertEqual(result["compact_arith_attempts"], 0)
        self.assertIn("ring", result["commands"])

    def test_false_recurrence_is_not_a_proof_or_a_final_cost(self):
        result = hybrid.search("forall a b n. (a+n)+S b=(a+b)+n", limits=limits())
        self.assertNotEqual(result["status"], "proof")
        self.assertFalse(result["kernel_checked"])
        self.assertIsNone(result["replay"])
        self.assertIsNone(result["proof_cost"]["final"])
        self.assertEqual(result["proof_cost"]["best_partial"]["stage"], "partial")
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["vampire_calls"], 0)


if __name__ == "__main__":
    unittest.main()
