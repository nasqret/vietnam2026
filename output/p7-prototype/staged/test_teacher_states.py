"""Synthetic structural fixtures only; no fixture is a proof/admission receipt."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teacher_states as states


class NoReservations:
    def reason(self, *args):
        return None
    def goals_reason(self, goals):
        return None


def fixtures(count=32):
    cases, rows = {}, []
    for i in range(count):
        theorem = f"forall n. n+{i}=n+{i}"
        after1 = [f"n : ℕ ⊢ n+{i}=n+{i}"]
        after2 = [f"n : ℕ ⊢ n+{i}=n+{i}"]
        source = {"owner": "project", "path": f"fixture-{i}.json", "sha256": f"{i:064x}"}
        origin1 = {"branch_id": 1, "parent_id": 0, "source": "heuristic"}
        origin2 = {"branch_id": 2, "parent_id": 1, "source": "heuristic"}
        trace = [{"origin": origin1, "tactic": "intro n", "step": 1, "goals_after": after1},
                 {"origin": origin2, "tactic": "symm", "step": 2, "goals_after": after2}]
        case = {"case_id": f"fixture_{i}", "outcome": "proved", "expected": "provable",
                "canonical_theorem": theorem, "last_job": {"result": {"search": {"branches": []}}},
                "fixture_trace": trace}
        cases[source["path"]] = case
        rows.append({"schema": "hydra-native-action-attempt-v1", "id": f"row-{i}",
            "split": "train", "split_group": f"group-{i % 4}", "source": source,
            "family": f"family_{i % 4}", "template_family": f"family_{i % 4}",
            "case_id": case["case_id"], "theorem": theorem, "theorem_identity": f"theorem-{i}",
            "parent_id": 2, "all_goals_before": after2, "native_rejected": True,
            "censored": False, "action": "fixture_action", "error": "fixture rejection"})
    return cases, rows


def fixture_trace(case):
    return case["fixture_trace"], None


class SelectionTests(unittest.TestCase):
    def select(self, cases, rows, reservation=None, **kwargs):
        return states.select_records(rows, load_case=lambda source: cases[source["path"]],
            verified_trace=fixture_trace, reservation=reservation or NoReservations(), **kwargs)

    def test_exact_32_distinct_training_states_without_future_commands(self):
        cases, rows = fixtures()
        selected, report = self.select(cases, rows)
        self.assertEqual(len(selected), 32)
        self.assertEqual(len({row["id"] for row in selected}), 32)
        self.assertEqual(report["candidate_states"], 32)
        self.assertTrue(all(row["commands_before"] == ("intro n", "symm") for row in selected))
        self.assertTrue(all("completion" not in row and not row["reference_continuation_in_teacher_input"] for row in selected))
        self.assertEqual(selected, self.select(cases, list(reversed(rows)))[0])

    def test_missing_parent_is_never_replaced_by_winning_commands(self):
        cases, rows = fixtures()
        rows[0]["parent_id"] = 1234
        with self.assertRaisesRegex(ValueError, "Fewer than 32"):
            self.select(cases, rows)

    def test_validation_and_reserved_intermediate_state_are_excluded(self):
        cases, rows = fixtures()
        rows[0]["split"] = "val"
        with self.assertRaisesRegex(ValueError, "Fewer than 32"):
            self.select(cases, rows)
        rows[0]["split"] = "train"
        class Reserved(NoReservations):
            def goals_reason(self, goals):
                return "reserved" if any("n+0=" in g for g in goals) else None
        with self.assertRaisesRegex(ValueError, "Fewer than 32"):
            self.select(cases, rows, Reserved())

    def test_no_duplicate_padding_when_less_than_32(self):
        cases, rows = fixtures(31)
        rows += copy.deepcopy(rows)
        with self.assertRaisesRegex(ValueError, "Fewer than 32"):
            self.select(cases, rows)

    def test_cancellation_and_changed_source_pin_propagate(self):
        cases, rows = fixtures()
        with self.assertRaisesRegex(RuntimeError, "cancelled"):
            self.select(cases, rows, should_stop=lambda: True)
        def corrupted(source):
            raise ValueError("pinned source changed")
        with self.assertRaisesRegex(ValueError, "pinned source changed"):
            states.select_records(rows, load_case=corrupted, verified_trace=fixture_trace,
                                  reservation=NoReservations())


if __name__ == "__main__":
    unittest.main()
