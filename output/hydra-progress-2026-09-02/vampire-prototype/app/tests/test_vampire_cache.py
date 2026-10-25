"""Bounded exact-input suppression; synthetic transport and real native ASTs.

No model, HTTP server, solver process or full proof search is launched.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import worker
worker.load_kernel()
import vampire_bridge as bridge
import vampire_limits as policy
from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic
from peano_lab.kernel.formulas import parse_formula_with_names


def state_after(theorem, commands=()):
    target, names = parse_formula_with_names(theorem)
    state = start(target, names)
    for command in commands:
        tactic, _, args = command.partition(" ")
        state = apply_tactic(state, tactic, args)
    return state


def proof_fixture(used="hydra_h0"):
    # Dependency extraction fixture only; never a genuine external proof.
    return ("% SZS status Theorem for fixture\n% SZS output start Proof for fixture\n"
            f"fof(first,axiom,(hydra_zero = hydra_zero),file(unknown,{used})).\n"
            "fof(last,plain,($false),inference(test_only,[],[first])).\n"
            "% SZS output end Proof for fixture\n")


class FixedRunner:
    """Canonical runtime metadata without starting any subprocess."""
    def __init__(self, *, profile="research", outcome="resource_limit", omit=(), **changes):
        self.profile, self.outcome = profile, outcome
        self.changes, self.omit, self.calls = changes, omit, 0

    def __call__(self, problem):
        self.calls += 1
        timed = self.outcome == "timeout"
        resource = self.outcome == "resource_limit"
        result = {"available": True, "executed": True,
                  "status": self.outcome, "exit_code": -9 if resource else (1 if timed else 0),
                  "stdout": "% Time limit reached!\n" if timed else "", "stderr": "",
                  "problem_sha256": hashlib.sha256(problem.encode("utf-8")).hexdigest(),
                  "binary_sha256": "a" * 64, "profile": self.profile,
                  "runtime_policy": policy.RUNTIME_POLICY,
                  "solver_args": policy.solver_args(self.profile), "limits": policy.solver_limits(self.profile),
                  "termination": {"reason": "owned_child_rss_watchdog" if resource else "exit_zero"},
                  **self.changes}
        return {key: value for key, value in result.items() if key not in self.omit}


class VampireCacheTests(unittest.TestCase):
    def test_unsuccessful_repeat_is_one_actual_invocation_and_no_reused_advice(self):
        state = state_after("forall n. n = n", ("intro n",))
        for outcome, expected in (("resource_limit", "resource_limit"), ("timeout", "timeout"),
                                  ("completed", "no_refutation")):
            with self.subTest(outcome=outcome):
                runner = FixedRunner(outcome=outcome)
                advisor = bridge.VampireAdvisor(runner)
                first = advisor.advise(state, max_candidates=1)
                second = advisor.advise(state, max_candidates=24)
                self.assertEqual(first["status"], expected)
                self.assertTrue(first["cache"]["stored"])
                self.assertEqual(second["status"], "cached_unsuccessful")
                self.assertEqual(second["solver"]["invocations"], 0)
                self.assertIsNone(second["solver"]["exit_code"])
                self.assertFalse(second["solver"]["timed_out"])
                self.assertFalse(second["solver"]["resource_limited"])
                self.assertTrue(second["solver"]["availability_from_previous_attempt"])
                self.assertNotIn("binary_sha256", second["solver"])
                self.assertEqual(second["cache"]["previous_status"], expected)
                self.assertEqual(second["cache"]["previous_request"], 1)
                self.assertEqual(second["cache"]["previous_invocation"], 1)
                self.assertEqual(second["suggestions"], [])
                self.assertEqual(second["candidates"], ())
                self.assertFalse(second["kernel_checked"])
                report = advisor.report()
                self.assertEqual((report["requests"], report["actual_invocations"], report["cache_hits"]), (2, 1, 1))
                self.assertEqual(runner.calls, 1)
                self.assertEqual(report["retained_input_bytes"], len(bridge.export_state(state).text.encode("utf-8")))

    def test_renamed_context_can_only_reuse_unsuccessfulness_never_native_commands(self):
        first = state_after("forall n m. n = m -> m = n", ("intro n", "intro m", "intro h"))
        second = state_after("forall a b. a = b -> b = a", ("intro a", "intro b", "intro other"))
        self.assertEqual(bridge.export_state(first).text, bridge.export_state(second).text)
        failed = FixedRunner()
        advisor = bridge.VampireAdvisor(failed)
        advisor.advise(first)
        self.assertTrue(advisor.advise(second)["cache"]["hit"])
        self.assertEqual(failed.calls, 1)
        successful = FixedRunner(outcome="completed", stdout=proof_fixture())
        advisor = bridge.VampireAdvisor(successful)
        advice1, advice2 = advisor.advise(first), advisor.advise(second)
        self.assertIn(("symm", "exact h"), advice1["candidates"])
        self.assertIn(("symm", "exact other"), advice2["candidates"])
        self.assertTrue(all("exact h" not in row for row in advice2["candidates"]))
        self.assertFalse(advice1["cache"]["stored"])
        self.assertEqual(successful.calls, 2)
        self.assertEqual(advisor.report()["entries"], 0)

    def test_success_without_supported_native_hints_is_not_cached(self):
        runner = FixedRunner(outcome="completed", stdout=proof_fixture("hydra_goal"))
        advisor = bridge.VampireAdvisor(runner)
        state = state_after("0 = 0")
        for _ in range(2):
            result = advisor.advise(state)
            self.assertEqual(result["status"], "advisory_theorem")
            self.assertEqual(result["suggestions"], [])
            self.assertFalse(result["cache"]["stored"])
        self.assertEqual(runner.calls, 2)

    def test_full_bytes_are_the_key_even_if_reported_digests_collide(self):
        digest = "f" * 64
        a = replace(bridge.export_state(state_after("0 = 0")), sha256=digest)
        b = replace(bridge.export_state(state_after("0 = 1")), sha256=digest)
        self.assertNotEqual(a.text, b.text)
        runner = FixedRunner(problem_sha256=digest)
        advisor = bridge.VampireAdvisor(runner)
        with patch.object(bridge, "export_state", side_effect=(a, b, a)):
            results = [advisor.advise(None) for _ in range(3)]
        self.assertEqual([item["cache"]["hit"] for item in results], [False, False, True])
        self.assertEqual(runner.calls, 2)
        self.assertEqual(advisor.report()["entries"], 2)

    def test_transport_errors_partial_proofs_and_incomplete_metadata_are_not_cached(self):
        cases = (
            {"outcome": "unavailable", "executed": False, "available": False, "exit_code": None},
            {"outcome": "failed", "exit_code": 2},
            {"outcome": "failed", "exit_code": -9, "termination": {"reason": "owned_child_rss_accounting_error"}},
            {"outcome": "failed", "exit_code": -9, "stdout": "% Time limit reached!\n"},
            {"outcome": "completed", "stdout": "% SZS status Theorem for incomplete\n"},
            {"outcome": "resource_limit", "exit_code": None},
            {"outcome": "timeout", "exit_code": True},
            {"outcome": "resource_limit", "binary_sha256": None},
            {"outcome": "resource_limit", "omit": ("profile",)},
            {"outcome": "resource_limit", "omit": ("problem_sha256",)},
            {"outcome": "completed", "output_limited": True},
            {"outcome": "completed", "stdout": "x" * (bridge.MAX_OUTPUT_BYTES + 1)},
        )
        state = state_after("0 = 0")
        for changes in cases:
            with self.subTest(changes={key: str(value)[:80] for key, value in changes.items()}):
                runner = FixedRunner(**changes)
                advisor = bridge.VampireAdvisor(runner)
                for _ in range(2):
                    result = advisor.advise(state)
                    self.assertFalse(result["cache"]["hit"])
                    self.assertFalse(result["cache"]["stored"])
                    self.assertEqual(result["suggestions"], [])
                self.assertEqual(runner.calls, 2)
                self.assertEqual(advisor.report()["entries"], 0)

    def test_opaque_callbacks_are_uncached_and_bad_bindings_still_fail(self):
        state = state_after("0 = 0")
        fixed = FixedRunner()
        advisor = bridge.VampireAdvisor(lambda text: fixed(text))
        advisor.advise(state)
        advisor.advise(state)
        self.assertEqual(fixed.calls, 2)
        self.assertEqual(advisor.report()["entries"], 0)
        for changes in ({"solver_args": ["--mode", "portfolio"]},
                        {"problem_sha256": "0" * 64}, {"executed": "yes"}):
            with self.subTest(changes=changes):
                runner = FixedRunner(**changes)
                advisor = bridge.VampireAdvisor(runner)
                for _ in range(2):
                    with self.assertRaises(ValueError):
                        advisor.advise(state)
                self.assertEqual(runner.calls, 2)
                self.assertEqual(advisor.report()["entries"], 0)

    def test_runner_profile_and_search_identity_prevent_cross_scope_hits(self):
        state = state_after("0 = 0")
        original = FixedRunner()
        advisor = bridge.VampireAdvisor(original)
        advisor.advise(state)
        replacement = FixedRunner()
        advisor.runner = replacement
        self.assertFalse(advisor.advise(state)["cache"]["hit"])
        for profile in ("deep", "research"):
            replacement.profile = profile
            self.assertFalse(advisor.advise(state)["cache"]["hit"])
        self.assertEqual(advisor.report()["scope_resets"], 3)
        self.assertEqual(advisor.report()["actual_invocations"], 4)
        fresh = bridge.VampireAdvisor(replacement)
        self.assertFalse(fresh.advise(state)["cache"]["hit"])
        self.assertEqual(fresh.report()["requests"], 1)
        self.assertEqual(replacement.calls, 4)

    def test_lru_entry_bound_does_not_exceed_24(self):
        states = [state_after(f"{number} = 0") for number in range(25)]
        runner = FixedRunner()
        advisor = bridge.VampireAdvisor(runner)
        for state in states[:24]:
            advisor.advise(state)
        self.assertTrue(advisor.advise(states[0])["cache"]["hit"])
        advisor.advise(states[24])
        self.assertTrue(advisor.advise(states[0])["cache"]["hit"])
        self.assertFalse(advisor.advise(states[1])["cache"]["hit"])
        report = advisor.report()
        self.assertEqual(report["entries"], 24)
        self.assertEqual(report["evictions"], 2)
        self.assertEqual(report["stores"], 26)
        self.assertEqual(runner.calls, 26)

    def test_retained_exact_input_bytes_are_bounded_independently_of_entry_count(self):
        base = bridge.export_state(state_after("0 = 0"))
        problems = []
        for number in range(5):
            text = base.text + f"% fixture-{number} " + "x" * (60000 - len(base.text) - 13) + "\n"
            self.assertEqual(len(text.encode("utf-8")), 60000)
            problems.append(replace(base, text=text, sha256=hashlib.sha256(text.encode("utf-8")).hexdigest()))
        advisor = bridge.VampireAdvisor(FixedRunner())
        with patch.object(bridge, "export_state", side_effect=problems):
            for _ in problems:
                advisor.advise(None)
        report = advisor.report()
        self.assertEqual(report["entries"], 4)
        self.assertEqual(report["retained_input_bytes"], 240000)
        self.assertEqual(report["evictions"], 1)
        with patch.object(bridge, "MAX_CACHE_INPUT_BYTES", 100):
            runner = FixedRunner()
            advisor = bridge.VampireAdvisor(runner)
            for _ in range(2):
                self.assertFalse(advisor.advise(state_after("0 = 0"))["cache"]["stored"])
            self.assertEqual(advisor.report()["retained_input_bytes"], 0)
            self.assertEqual(runner.calls, 2)

    def test_result_mutation_cannot_seed_advice_or_change_history_and_trace_is_bounded(self):
        state = state_after("0 = 0")
        runner = FixedRunner()
        advisor = bridge.VampireAdvisor(runner)
        advisor.advise(state)
        first_hit = advisor.advise(state)
        first_hit["cache"]["previous_status"] = "forged_success"
        first_hit["suggestions"].append({"commands": ["exact fabricated"]})
        report = advisor.report()
        report["hit_records"][0]["previous_exit_code"] = 0
        for _ in range(69):
            result = advisor.advise(state)
            self.assertEqual(result["suggestions"], [])
            self.assertEqual(result["cache"]["previous_status"], "resource_limit")
            self.assertEqual(result["cache"]["previous_exit_code"], -9)
        report = advisor.report()
        self.assertEqual(len(report["hit_records"]), 64)
        self.assertEqual(report["hit_records_omitted"], 6)
        self.assertEqual(report["cache_hits"], 70)
        self.assertEqual(report["requests"], 71)
        self.assertEqual(report["actual_invocations"], runner.calls)
        self.assertEqual(runner.calls, 1)

    def test_unavailable_unsupported_and_invalid_requests_have_no_actual_launch(self):
        advisor = bridge.VampireAdvisor()
        self.assertEqual(advisor.advise(None)["status"], "unavailable")
        runner = FixedRunner()
        advisor.runner = runner
        self.assertEqual(advisor.advise(None)["status"], "unsupported_fragment")
        with self.assertRaises(ValueError):
            advisor.advise(None, max_candidates=0)
        self.assertEqual(advisor.report()["requests"], 2)
        self.assertEqual(advisor.report()["actual_invocations"], 0)
        self.assertEqual(runner.calls, 0)


if __name__ == "__main__":
    unittest.main()
