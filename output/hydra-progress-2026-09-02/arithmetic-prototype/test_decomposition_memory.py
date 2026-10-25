"""Pure bounded-ledger tests: no native prover, model, solver, or HTTP imports."""
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decomposition_memory as memory_module
from decomposition_memory import DecompositionAttemptMemory


class DecompositionAttemptMemoryTests(unittest.TestCase):
    def test_only_explicit_attempt_boundary_records_an_attempt(self):
        ledger = DecompositionAttemptMemory()
        goals = ("a : Nat\nh : a = a\n⊢ a = a", "⊢ 0 = 0")
        self.assertIsNone(ledger.previously_attempted(goals, 7))
        self.assertIsNone(ledger.previously_attempted(goals, 7))
        self.assertEqual(ledger.report()["retained_goal_states"], 0)
        self.assertTrue(ledger.remember_attempt(goals, 7, 0))
        for depth in (7, 8, 160):
            self.assertEqual(ledger.previously_attempted(goals, depth).to_dict(),
                             {"plan_id": 0, "depth": 7})

    def test_smallest_recorded_depth_wins_and_lookup_does_not_reserve(self):
        ledger = DecompositionAttemptMemory()
        goals = ("⊢ a*a = a*a",)
        ledger.remember_attempt(goals, 12, 5)
        retained_bytes = ledger.report()["retained_payload_bytes"]
        self.assertIsNone(ledger.previously_attempted(goals, 4))
        self.assertIsNone(ledger.previously_attempted(goals, 4))
        self.assertEqual(ledger.previously_attempted(goals, 12).plan_id, 5)
        self.assertTrue(ledger.remember_attempt(goals, 4, 9))
        self.assertFalse(ledger.remember_attempt(goals, 6, 10))
        self.assertFalse(ledger.remember_attempt(goals, 4, 11))
        reference = ledger.previously_attempted(goals, 12)
        self.assertEqual(reference.to_dict(), {"plan_id": 9, "depth": 4})
        self.assertIsNone(ledger.previously_attempted(goals, 3))
        self.assertEqual(ledger.report()["retained_payload_bytes"], retained_bytes)
        self.assertEqual(ledger.report()["retained_goal_states"], 1)
        self.assertEqual(ledger.report()["shallower_replacements"], 1)
        with self.assertRaises(FrozenInstanceError):
            reference.depth = 0

    def test_complete_ordered_goal_tuple_including_context_and_names_is_key(self):
        ledger = DecompositionAttemptMemory()
        first = "a : Nat\nh : a = a\n⊢ a = a"
        goals = (first, "b : Nat\n⊢ b = b")
        ledger.remember_attempt(goals, 3, 2)
        equal_but_distinct = tuple([first, "b : Nat\n⊢ b = b"])
        self.assertIsNot(goals, equal_but_distinct)
        self.assertEqual(ledger.previously_attempted(equal_but_distinct, 3).plan_id, 2)
        for changed in (
            (first,),
            tuple(reversed(goals)),
            (first, "b : Nat\n⊢ b = 0"),
            ("a : Nat\n⊢ a = a", goals[1]),
            (first.replace("h :", "ih :"), goals[1]),
            (first.replace("a", "x"), goals[1]),
            (first + " ", goals[1]),
        ):
            with self.subTest(changed=changed):
                self.assertIsNone(ledger.previously_attempted(changed, 3))

    def test_diagnostic_digest_collision_does_not_merge_distinct_states(self):
        class CollidingDigest:
            def hexdigest(self):
                return "0" * 64
        ledger = DecompositionAttemptMemory()
        with patch.object(memory_module.hashlib, "sha256", return_value=CollidingDigest()):
            ledger.remember_attempt(("⊢ x = x",), 2, 6)
            ledger.remember_attempt(("⊢ y = y",), 5, 7)
        self.assertEqual(ledger.previously_attempted(("⊢ x = x",), 6).plan_id, 6)
        self.assertEqual(ledger.previously_attempted(("⊢ y = y",), 6).plan_id, 7)
        self.assertIsNone(ledger.previously_attempted(("⊢ z = z",), 6))
        self.assertEqual(ledger.report()["retained_goal_states"], 2)

    def test_entry_bound_has_no_eviction_and_allows_shallower_replacement(self):
        ledger = DecompositionAttemptMemory()
        for index in range(6):
            self.assertTrue(ledger.remember_attempt((f"goal {index}",), 10, index))
        size = ledger.report()["retained_payload_bytes"]
        self.assertFalse(ledger.remember_attempt(("goal 6",), 10, 6))
        self.assertIsNone(ledger.previously_attempted(("goal 6",), 10))
        self.assertEqual(ledger.previously_attempted(("goal 0",), 10).plan_id, 0)
        self.assertTrue(ledger.remember_attempt(("goal 0",), 2, 7))
        self.assertEqual(ledger.previously_attempted(("goal 0",), 10).plan_id, 7)
        report = ledger.report()
        self.assertEqual(report["retained_goal_states"], 6)
        self.assertEqual(report["retained_payload_bytes"], size)
        self.assertEqual(report["retention_declines"]["entries"], 1)

    def test_exact_key_byte_bound_includes_utf8_and_json_escaping(self):
        for good, oversized in (
            ("a" * 65532, "a" * 65533),
            ("😀" * 16383, "😀" * 16384),
            ("\x00" * 10922, "\x00" * 10923),
        ):
            with self.subTest(character=good[:1]):
                ledger = DecompositionAttemptMemory()
                self.assertEqual(len(json.dumps((good,), ensure_ascii=False,
                                                separators=(",", ":")).encode("utf-8")), 65536)
                self.assertTrue(ledger.remember_attempt((good,), 0, 1))
                self.assertFalse(ledger.remember_attempt((oversized,), 0, 2))
                self.assertIsNone(ledger.previously_attempted((oversized,), 0))
                self.assertEqual(ledger.report()["retained_payload_bytes"], 65536)
                self.assertEqual(ledger.report()["retention_declines"]["key_bytes"], 1)
                self.assertEqual(ledger.report()["uncacheable_checks"], 1)
        # A huge tuple is declined before trying to encode or retain it.
        ledger = DecompositionAttemptMemory()
        with patch.object(memory_module.json, "dumps", side_effect=AssertionError("unbounded encoding")):
            self.assertFalse(ledger.remember_attempt(("",) * 65536, 0, 1))

    def test_total_payload_defense_does_not_evict_or_block_existing_update(self):
        ledger = DecompositionAttemptMemory()
        # Default six 64-KiB keys cannot reach 512 KiB; exercise the independent
        # defense under a smaller test-only limit rather than weaken key bounds.
        with patch.object(memory_module, "MAX_TOTAL_BYTES", 12):
            self.assertTrue(ledger.remember_attempt(("ab",), 3, 1))
            self.assertTrue(ledger.remember_attempt(("cd",), 3, 2))
            self.assertFalse(ledger.remember_attempt(("ef",), 3, 3))
            self.assertTrue(ledger.remember_attempt(("ab",), 1, 4))
            self.assertEqual(ledger.report()["retained_payload_bytes"], 12)
        self.assertEqual(ledger.report()["retention_declines"]["total_bytes"], 1)
        self.assertEqual(ledger.previously_attempted(("ab",), 3).plan_id, 4)

    def test_diagnostics_are_bounded_copied_and_contain_no_raw_goals_or_proofs(self):
        ledger = DecompositionAttemptMemory()
        goal = "PRIVATE_GOAL_TEXT_WITH_CONTEXT"
        ledger.remember_attempt((goal,), 1, 0)
        for _ in range(100):
            ledger.previously_attempted((goal,), 1)
        report = ledger.report()
        self.assertEqual(len(report["events"]), 64)
        self.assertEqual(report["events_omitted"], 37)
        self.assertEqual(report["repeated_decompositions_skipped"], 100)
        serialized = json.dumps(report)
        self.assertNotIn(goal, serialized)
        self.assertFalse(report["tactics_cached"])
        self.assertFalse(report["proofs_cached"])
        self.assertFalse(report["kernel_authority_changed"])
        report["events"][0]["plan_id"] = 999
        report["events"].clear()
        report["retention_declines"]["entries"] = 999
        report["limits"]["entries"] = 999
        actual = ledger.report()
        self.assertEqual(actual["events"][0]["plan_id"], 0)
        self.assertEqual(actual["retention_declines"]["entries"], 0)
        self.assertEqual(actual["limits"]["entries"], 6)
        self.assertIsNone(DecompositionAttemptMemory().previously_attempted((goal,), 1))

    def test_invalid_inputs_do_not_record_attempts(self):
        ledger = DecompositionAttemptMemory()
        for goals in (None, [], ["goal"], (), (1,), ("goal", object())):
            with self.subTest(goals=goals), self.assertRaises(ValueError):
                ledger.remember_attempt(goals, 1, 0)
        for depth in (-1, True, 1.0, "1", 2**63):
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                ledger.previously_attempted(("goal",), depth)
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                ledger.remember_attempt(("goal",), depth, 0)
        for plan_id in (-1, True, 1.0, "1", 2**63):
            with self.subTest(plan_id=plan_id), self.assertRaises(ValueError):
                ledger.remember_attempt(("goal",), 1, plan_id)
        self.assertEqual(ledger.report()["retained_goal_states"], 0)
        self.assertEqual(ledger.report()["remember_requests"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
