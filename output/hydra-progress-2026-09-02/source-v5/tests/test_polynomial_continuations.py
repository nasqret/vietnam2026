"""Continuation scheduling/distrust tests with real native edge checking.

The one injected ring refusal exercises the fallback deterministically without
building an expensive large certificate. The supplied plans are test advice;
all other tactics, the original-theorem finalizer and replay are real.
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
SOURCE = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
import hybrid_search as hybrid
from peano_lab.kernel.formulas import Forall
from polynomial_chunks import ChunkPlan


class PolynomialContinuationTests(unittest.TestCase):
    def test_compound_polynomial_proof_is_found_from_the_statement_only(self):
        theorem = ("forall a b. (a*a+2*a*b)*(a*a+2*a*b)+(2*b*(a+b))*(2*b*(a+b))="
                   "(a*a+2*a*b+2*b*b)*(a*a+2*a*b+2*b*b)")
        result = hybrid.search(theorem, limits=hybrid.HybridLimits(
            max_depth=32, max_states=128, max_expansions=24,
            max_tactic_attempts=384, max_macro_steps=4,
            max_model_calls=0, max_vampire_calls=0, wall_seconds=45))
        self.assertEqual(result["status"], "proof", result["diagnostics"])
        self.assertTrue(result["kernel_checked"])
        self.assertTrue(result["replay"]["kernel_checked"])
        self.assertEqual(result["replay"]["theorem"], result["theorem"])
        self.assertEqual(result["replay"]["goals"], [])
        self.assertLessEqual(len(result["commands"]), 32)
        self.assertTrue(any(row.get("evidence", {}).get("planner") == "polynomial_atoms_v1"
                            for row in result["provenance"]))
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["vampire_calls"], 0)

    def run_plan(self, commands, *, max_depth=24):
        replay = hybrid._replay
        refused = []

        def refuse_first_ring(*args, **kwargs):
            path = args[3]
            if path[-1] == "ring" and not refused:
                refused.append(path)
                return None, len(path) - 1, ValueError("fixture: bounded ring refusal")
            return replay(*args, **kwargs)

        def candidates(state, **_):
            command = "intro a" if type(state.current().target) is Forall else "ring"
            return (hybrid._proposal(command, reason="fixture: reach the fallback"),)

        plan = ChunkPlan(tuple(commands), "untrusted test plan", (), {})
        with patch.object(hybrid, "_closure_candidates", return_value=()), \
                patch.object(hybrid, "heuristic_candidates", side_effect=candidates), \
                patch.object(hybrid, "_replay", side_effect=refuse_first_ring), \
                patch.object(hybrid, "polynomial_chunk_plan", return_value=plan):
            result = hybrid.search("forall a. 0 + a = a", limits=hybrid.HybridLimits(
                max_depth=max_depth, max_states=64, max_expansions=24,
                max_tactic_attempts=100, max_macro_steps=2, heuristic_burst=8,
                max_model_calls=0, max_vampire_calls=0, wall_seconds=8))
        self.assertEqual(len(refused), 1)
        return result

    def test_multiple_chunks_finish_only_through_full_native_replay(self):
        result = self.run_plan(("trans (a + 0)", "ring", "simp"))
        self.assertEqual(result["status"], "proof", result["diagnostics"])
        self.assertTrue(result["kernel_checked"])
        self.assertTrue(result["replay"]["kernel_checked"])
        self.assertEqual(result["replay"]["theorem"], result["theorem"])
        self.assertEqual(result["replay"]["goals"], [])
        self.assertEqual(result["commands"], ["intro a", "trans (a + 0)", "ring", "simp"])
        report = result["polynomial_decomposition"]
        self.assertEqual(report["chunks_attempted"], 2)
        self.assertEqual(report["native_steps_accepted"], 3)
        self.assertEqual(report["plans"][0]["status"], "original_theorem_verified")
        self.assertFalse(report["trusted_as_proof"])
        self.assertEqual({row["source"] for row in result["provenance"]}, {"heuristic"})
        self.assertEqual([row["evidence"]["chunk"] for row in result["provenance"][1:]],
                         ["1", "1", "2"])

    def test_failed_chunk_discards_its_remainder(self):
        result = self.run_plan(("trans (a + 0)", "intro", "have leak : 0 = 0", "refl"))
        report = result["polynomial_decomposition"]
        self.assertEqual(report["plans"][0]["status"], "sequence_stopped")
        self.assertEqual(report["plans"][0]["native_steps_accepted"], 1)
        self.assertFalse(any(row["command"] == "have leak : 0 = 0" for row in result["branches"]))
        self.assertTrue(any(row["command"] == "intro" and row["status"] == "rejected"
                            for row in result["branches"]))

    def test_whole_plan_is_checked_for_authority_and_remaining_depth(self):
        for commands, depth, expected in (
            (("trans (a + 0)", "ring", "classical"), 24, "invalid_plan"),
            (("trans (a + 0)", "ring", "simp"), 3, "remaining_depth_insufficient"),
        ):
            with self.subTest(commands=commands, depth=depth):
                result = self.run_plan(commands, max_depth=depth)
                report = result["polynomial_decomposition"]
                self.assertEqual(report["plans"][0]["status"], expected)
                self.assertEqual(report["chunks_attempted"], 0)
                self.assertEqual(report["native_steps_accepted"], 0)
                self.assertFalse(any(row["command"] == "trans (a + 0)" for row in result["branches"]))


if __name__ == "__main__":
    unittest.main()
