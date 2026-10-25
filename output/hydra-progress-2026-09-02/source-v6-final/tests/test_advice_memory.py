"""Exact scope and finite retention checks; no inference or proof search."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import advice_memory as memory


class AdviceMemoryTests(unittest.TestCase):
    def test_all_goals_names_context_and_order_remain_significant(self):
        ledger = memory.ModelAdviceMemory()
        goals = ("n : N, h : n = 0 |- n = 0", "m : N |- m = m")
        self.assertIsNone(ledger.previously_decoded(goals))
        ledger.remember_decoded(goals, 3)
        self.assertEqual(ledger.previously_decoded(tuple(goals)), 3)
        for distinct in (goals[:1], tuple(reversed(goals)),
                         (goals[0].replace("n = 0", "n = 1"), goals[1]),
                         (goals[0].replace(" h :", " h2 :"), goals[1]),
                         (goals[0], "m : N |- m = 0")):
            with self.subTest(distinct=distinct):
                self.assertIsNone(ledger.previously_decoded(distinct))
        self.assertFalse(ledger.report()["tactics_reused"])

    def test_failed_or_missing_decode_is_not_an_earlier_model_call(self):
        ledger = memory.ModelAdviceMemory()
        for call in (0, -1, None, True, "1"):
            with self.subTest(call=call), self.assertRaises(ValueError):
                ledger.remember_decoded(("0 = 1",), call)
        self.assertIsNone(ledger.previously_decoded(("0 = 1",)))
        ledger.remember_decoded(("0 = 1",), 1)
        other_search = memory.ModelAdviceMemory()
        self.assertIsNone(other_search.previously_decoded(("0 = 1",)))

    def test_retention_and_diagnostics_remain_bounded(self):
        ledger = memory.ModelAdviceMemory()
        for index in range(memory.MAX_ENTRIES + 1):
            ledger.remember_decoded((str(index),), index + 1)
        self.assertIsNone(ledger.previously_decoded((str(memory.MAX_ENTRIES),)))
        for _ in range(memory.MAX_EVENTS + 7):
            self.assertEqual(ledger.previously_decoded(("0",)), 1)
        report = ledger.report()
        self.assertEqual(report["retained_prompts"], memory.MAX_ENTRIES)
        self.assertLessEqual(report["retained_bytes"], memory.MAX_TOTAL_BYTES)
        self.assertEqual(report["retention_declines"], 1)
        self.assertEqual(len(report["events"]), memory.MAX_EVENTS)
        self.assertEqual(report["events_omitted"], 7)
        oversized = memory.ModelAdviceMemory()
        goals = ("a" * memory.MAX_ENTRY_BYTES,)
        oversized.remember_decoded(goals, 1)
        self.assertIsNone(oversized.previously_decoded(goals))
        self.assertEqual(oversized.report()["retained_bytes"], 0)

    def test_memory_rejects_partial_or_mutable_goal_containers(self):
        ledger = memory.ModelAdviceMemory()
        for malformed in ([], ["0 = 0"], (), "0 = 0", (None,)):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                ledger.previously_decoded(malformed)


if __name__ == "__main__":
    unittest.main()
