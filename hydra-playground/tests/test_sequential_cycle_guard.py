"""CPU-only fake-provider and retained-trace checks; no native/model execution."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from sequential_cycle_guard import wrap_factory


class Provider:
    def __init__(self, owner):
        self.owner = owner
        self._report = {"actual_model_calls": 0, "generated_token_slots": 0,
                        "forward_attempts": 0, "forward_passes": 0, "attempts": []}

    def propose(self, goals, *, max_candidates):
        self.owner.proposals.append((goals, max_candidates))
        self._report.update(actual_model_calls=1, generated_token_slots=3,
            forward_attempts=3, forward_passes=3, attempts=[{"prompt_sha256": "fixture"}])
        if self.owner.error:
            raise TimeoutError("fixture provider deadline")
        return self.owner.candidates

    def report(self):
        return self._report


class Factory:
    def __init__(self, *, error=False):
        self.created, self.proposals, self.providers = [], [], []
        self.candidates = ("symm",)
        self.error = error

    def __call__(self, *args, **kwargs):
        self.created.append((args, kwargs))
        provider = Provider(self)
        self.providers.append(provider)
        return provider


class CycleGuardTests(unittest.TestCase):
    def step(self, guard, goals):
        step = guard(deadline=123.5, max_new_tokens=128, max_context_tokens=6144)
        candidates = step.propose(goals, max_candidates=1)
        return candidates, step.report()

    def test_factory_is_lazy_and_first_visit_behavior_is_unchanged(self):
        factory = Factory()
        guard = wrap_factory(factory)
        step = guard("literal option", deadline=12.0)
        self.assertEqual(factory.created, [])
        self.assertEqual(step.report()["actual_model_calls"], 0)
        goals = ["h : a = b ⊢ a = b", "⊢ c = c"]
        self.assertIs(step.propose(goals, max_candidates=1), factory.candidates)
        self.assertIs(factory.proposals[0][0], goals)
        self.assertEqual(factory.created, [(("literal option",), {"deadline": 12.0})])
        self.assertIs(step.report(), factory.providers[0].report())

    def test_two_state_cycle_has_zero_new_work_and_no_phantom_attempt(self):
        factory = Factory()
        guard = wrap_factory(factory)
        a, b = ("h : a = b ⊢ a = b",), ("h : a = b ⊢ b = a",)
        reports = [self.step(guard, goals) for goals in (a, b, a)]
        self.assertEqual(reports[2][0], ())
        report = reports[2][1]
        for name in ("actual_model_calls", "generated_token_slots", "forward_attempts", "forward_passes"):
            self.assertEqual(report[name], 0)
        self.assertEqual(report["attempts"], [])
        self.assertEqual(report["stop_reason"], "repeated_state")
        self.assertIs(report["kernel_checked"], False)
        self.assertEqual(len(factory.created), 2)
        self.assertEqual(sum(r["actual_model_calls"] for _, r in reports), 2)
        evidence = guard.report()
        self.assertEqual((evidence["visits"], evidence["distinct_states"]), (3, 2))
        self.assertEqual(evidence["repeats"][0]["first_visit"], 1)
        self.assertEqual(evidence["repeats"][0]["repeated_visit"], 3)
        self.assertFalse(evidence["is_disproof"])

    def test_entire_ordered_goals_aliases_and_literal_text_remain_distinct(self):
        factory = Factory()
        guard = wrap_factory(factory)
        states = [("h : a = b ⊢ a = b", "⊢ c = c"),
                  ("⊢ c = c", "h : a = b ⊢ a = b"),  # branch order
                  ("h : a = b ⊢ a = b", "⊢ d = d"),  # other branch
                  ("h : a = b ⊢ a = b",),             # number of goals
                  ("k : a = b ⊢ a = b",),             # hypothesis alias
                  ("h : x = y ⊢ x = y",),             # variable alias
                  ("h : a = b  ⊢ a = b",)]            # exact whitespace
        for state in states:
            self.assertEqual(self.step(guard, state)[0], ("symm",))
        self.assertEqual(len(factory.created), len(states))
        self.assertEqual(self.step(guard, list(states[0]))[0], ())

    def test_state_snapshot_survives_caller_list_mutation(self):
        factory = Factory()
        guard = wrap_factory(factory)
        goals = ["⊢ a = b"]
        self.step(guard, goals)
        goals[0] = "⊢ b = a"
        self.assertEqual(self.step(guard, ("⊢ a = b",))[0], ())
        self.assertEqual(self.step(guard, goals)[0], ("symm",))

    def test_each_request_has_fresh_state_and_report_is_detached(self):
        factory = Factory()
        first, second = wrap_factory(factory), wrap_factory(factory)
        self.step(first, ("⊢ 0 = 0",))
        self.step(first, ("⊢ 0 = 0",))
        detached = first.report()
        detached["repeats"][0]["first_visit"] = 999
        self.assertEqual(first.report()["repeats"][0]["first_visit"], 1)
        self.assertEqual(self.step(second, ("⊢ 0 = 0",))[0], ("symm",))
        self.assertEqual(len(factory.created), 2)

    def test_provider_error_retains_actual_accounting_and_propagates(self):
        factory = Factory(error=True)
        guard = wrap_factory(factory)
        step = guard(deadline=1)
        with self.assertRaisesRegex(TimeoutError, "fixture provider deadline"):
            step.propose(("⊢ a = b",), max_candidates=1)
        self.assertEqual(step.report()["actual_model_calls"], 1)
        self.assertIs(step.report(), factory.providers[0].report())
        with self.assertRaisesRegex(RuntimeError, "cannot be reused"):
            step.propose(("⊢ b = a",), max_candidates=1)
        self.assertEqual(len(factory.created), 1)

    def test_factory_error_cannot_invent_inference(self):
        def broken(**_kwargs):
            raise RuntimeError("fixture construction failure")
        step = wrap_factory(broken)(deadline=1)
        with self.assertRaisesRegex(RuntimeError, "construction failure"):
            step.propose(("⊢ 0 = 0",), max_candidates=1)
        self.assertEqual(step.report()["actual_model_calls"], 0)
        self.assertEqual(step.report()["attempts"], [])

    def test_authenticated_saved_regression_cycle_stops_before_seventh_proposal(self):
        # Retained output only. This is not a fresh model run, native replay,
        # proof-quality measurement, or alteration of the matched comparison.
        path = APP.parent / "output/hydra-wmi-integration-2026-10-21/evaluation/cached-v3-historical-01/regression-06.json"
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "c8cdc93aa91599ef412f1a65a35a63c03a3c881a8cb08287fcb97774f28b4cc7")
        trace = json.loads(raw)["result"]["last_native_result"]["trace"]
        factory = Factory()
        guard = wrap_factory(factory)
        reports = []
        for row in trace[:7]:
            candidate, report = self.step(guard, tuple(row["goals_before"]))
            reports.append(report)
        self.assertEqual(candidate, ())
        self.assertEqual(len(factory.created), 6)
        self.assertEqual(sum(r["actual_model_calls"] for r in reports), 6)
        self.assertEqual(guard.report()["repeats"][0]["first_visit"], 5)
        self.assertEqual(guard.report()["repeats"][0]["repeated_visit"], 7)
        self.assertEqual(trace[4]["tactic"], trace[5]["tactic"])
        self.assertEqual(trace[4]["goals_before"], trace[5]["goals_after"])


if __name__ == "__main__":
    unittest.main()
