"""Draft native integration fixtures for decomposition-attempt memory.

Not executed during preparation. The test substitutes cheap ring refusals and
untrusted planner text; every successful prefix tactic still uses native replay.
There is no model, solver, HTTP, or acceptance based on a planner claim.
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

# This works both in the output prototype and after copying into app/tests.
ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "hydra-playground" / "hybrid_search.py").is_file())
APP = ROOT / "hydra-playground"
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
import hybrid_search as hybrid
from peano_lab.kernel.formulas import Forall
from polynomial_chunks import ChunkPlan


class DecompositionSearchMemoryTests(unittest.TestCase):
    def run_fixture(self, *, initial=("intro a", "symm", "symm"),
                    commands=("symm", "symm", "intro"), max_depth=12):
        native_replay = hybrid._replay
        memory_type = hybrid.DecompositionAttemptMemory
        events = []
        ledgers = []
        native_successes = []

        class TrackingMemory(memory_type):
            def __init__(self):
                super().__init__()
                self.last_lookup = None
                self.attempted = []
                ledgers.append(self)

            def previously_attempted(self, goals, depth):
                reference = super().previously_attempted(goals, depth)
                self.last_lookup = (goals, depth, reference)
                events.append(("lookup", goals, depth, reference))
                return reference

            def remember_attempt(self, goals, depth, plan_id):
                retained = super().remember_attempt(goals, depth, plan_id)
                if retained:
                    self.attempted.append((goals, depth, plan_id))
                return retained

        def refuse_ring(*args, **kwargs):
            path = args[3]
            if path[-1] == "ring":
                return None, len(path) - 1, ValueError("fixture: inexpensive ring refusal")
            outcome = native_replay(*args, **kwargs)
            if outcome[0] is not None:
                native_successes.append(path)
            return outcome

        def candidates(state, **_):
            commands_here = initial if type(state.current().target) is Forall else ("ring",)
            return (hybrid._proposal(*commands_here, reason="fixture: native recurrent obligations"),)

        def record_planner(kind):
            self.assertEqual(len(ledgers), 1)
            lookup = ledgers[0].last_lookup
            self.assertIsNotNone(lookup, "Memory must be consulted before either expensive planner.")
            self.assertIsNone(lookup[2], "A repeated-attempt hit must suppress both planners.")
            events.append((kind, lookup[0], lookup[1], None))

        def atoms(*args, **kwargs):
            record_planner("atom_planner")
            return None

        def ordinary(*args, **kwargs):
            record_planner("polynomial_planner")
            if commands is None:
                return None
            return ChunkPlan(tuple(commands), "untrusted fixture plan", (), {})

        with patch.object(hybrid, "DecompositionAttemptMemory", TrackingMemory), \
                patch.object(hybrid, "_closure_candidates", return_value=()), \
                patch.object(hybrid, "heuristic_candidates", side_effect=candidates), \
                patch.object(hybrid, "_replay", side_effect=refuse_ring), \
                patch.object(hybrid, "atom_polynomial_chunk_plan", side_effect=atoms), \
                patch.object(hybrid, "polynomial_chunk_plan", side_effect=ordinary):
            result = hybrid.search("forall a. 0 + a = a", limits=hybrid.HybridLimits(
                max_depth=max_depth, max_states=96, max_expansions=40,
                max_tactic_attempts=160, max_macro_steps=3, heuristic_burst=8,
                max_model_calls=0, max_vampire_calls=0, wall_seconds=8))
        self.assertFalse(result["kernel_checked"])
        self.assertIsNone(result["replay"])
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["vampire_calls"], 0)
        report = result["polynomial_decomposition"]
        planner_events = [event for event in events if event[0].endswith("_planner")]
        self.assertEqual(report["planner_invocations"], len(planner_events))
        self.assertEqual(report["planning_attempts"],
                         sum(event[0] == "polynomial_planner" for event in events))
        return result, report, events, ledgers[0], native_successes

    def test_actual_recurrent_goals_skip_both_planners_but_allow_shallower_prefix(self):
        result, report, events, ledger, successes = self.run_fixture()
        self.assertTrue(any(path[-2:] == ("symm", "symm") for path in successes))
        self.assertTrue(any(row["command"] == "intro" and row["status"] == "rejected"
                            for row in result["branches"]))
        hits = [event for event in events if event[0] == "lookup" and event[3] is not None]
        self.assertGreater(len(hits), 0)
        self.assertEqual(report["repeated_decompositions_skipped"], len(hits))
        self.assertEqual(report["attempt_memory"]["repeated_decompositions_skipped"], len(hits))
        # The fixture's planners already assert that their immediately preceding
        # lookup was a miss. Check the recorded call sequence independently too.
        for index, event in enumerate(events):
            if event[0] != "lookup" or event[3] is None:
                continue
            following = events[index + 1:]
            next_lookup = next((i for i, item in enumerate(following) if item[0] == "lookup"),
                               len(following))
            self.assertFalse(any(item[0].endswith("_planner") for item in following[:next_lookup]))
        shallower = []
        best_depth = {}
        for goals, depth, plan_id in ledger.attempted:
            if goals in best_depth and depth < best_depth[goals]:
                shallower.append((goals, depth, plan_id))
            best_depth[goals] = min(depth, best_depth.get(goals, depth))
        self.assertGreater(len(shallower), 0,
                           "The retained native introduction prefix must remain eligible when shallower.")
        self.assertGreater(report["attempt_memory"]["shallower_replacements"], 0)

    def test_real_context_change_is_a_new_eligible_goal_tuple(self):
        result, report, events, ledger, successes = self.run_fixture(
            initial=("intro a", "have extra : 0 = 0", "refl"))
        self.assertTrue(any(path[-2:] == ("have extra : 0 = 0", "refl") for path in successes))
        attempted = [goals for goals, _, _ in ledger.attempted]
        self.assertTrue(any(len(goals) == 1 and "extra" in goals[0] for goals in attempted))
        self.assertTrue(any(len(goals) == 1 and "extra" not in goals[0] for goals in attempted))
        self.assertGreaterEqual(report["attempt_memory"]["retained_goal_states"], 2)

    def test_invalid_depth_declined_and_absent_plans_do_not_reserve_memory(self):
        for commands, depth, status in (
            (("symm", "classical"), 12, "invalid_plan"),
            (("symm", "symm", "intro"), 3, "remaining_depth_insufficient"),
            (None, 12, "no_plan"),
        ):
            with self.subTest(status=status):
                result, report, events, ledger, successes = self.run_fixture(
                    initial=("intro a",), commands=commands, max_depth=depth)
                self.assertTrue(report["plans"])
                self.assertEqual(report["plans"][0]["status"], status)
                self.assertEqual(report["attempt_memory"]["remember_requests"], 0)
                self.assertEqual(report["attempt_memory"]["retained_goal_states"], 0)
                self.assertEqual(report["chunks_attempted"], 0)
                self.assertEqual(report["native_steps_accepted"], 0)
                self.assertEqual(ledger.attempted, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
