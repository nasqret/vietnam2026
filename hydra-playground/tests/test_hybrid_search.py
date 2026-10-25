"""Native search integration and distrust boundaries, without any model/ATP run."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
SOURCE = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
import hybrid_search as hybrid
from arithmetic_search import ArithmeticHint
from peano_lab.batch import MODEL_V1_COMMANDS
from peano_lab.kernel.formulas import Forall
from peano_lab.ui.prove import SurfaceCapabilities


class CountingPolicy:
    def __init__(self, candidates=()):
        self.calls = 0
        self.candidates = candidates
        self.goals = []

    def propose(self, goals, *, max_candidates):
        self.calls += 1
        self.goals.append(goals)
        if max_candidates != 4:
            raise AssertionError("The saved local decoder has four candidate slots.")
        return self.candidates


class ClaimingAdvisor:
    """An intentionally untrusted stand-in; this launches no external solver."""
    def __init__(self):
        self.requests = 0

    def advise(self, state):
        self.requests += 1
        return {"status": "theorem", "problem_sha256": "a" * 64,
                "solver": {"status": "theorem", "szs_status": "Theorem",
                           "available": True, "invocations": 0},
                "suggestions": [{"commands": ["refl"], "reason": "Untrusted external theorem claim."}],
                "kernel_checked": True}  # This flag must be ignored too.


def limits(**changes):
    return hybrid.HybridLimits(**{"max_states": 128, "max_tactic_attempts": 384,
        "max_expansions": 48, "max_model_calls": 2, "max_vampire_calls": 2,
        "wall_seconds": 8, **changes})


class NativeHybridTests(unittest.TestCase):
    def assert_native_proof(self, result):
        self.assertEqual(result["status"], "proof", result["diagnostics"])
        self.assertTrue(result["kernel_checked"])
        self.assertEqual(result["replay"]["status"], "proved")
        self.assertTrue(result["replay"]["kernel_checked"])
        self.assertEqual(result["replay"]["goals"], [])
        self.assertEqual(result["certificate_nodes"], result["replay"]["proof_nodes"])
        self.assertEqual([item["command"] for item in result["provenance"]], result["commands"])
        trace = [row for row in result["replay"]["trace"] if "tactic" in row]
        self.assertEqual([row["tactic"] for row in trace], result["commands"])
        self.assertEqual(result["provenance"][-1]["branch_id"],
                         next(row["id"] for row in result["branches"] if row["status"] == "proved"))

    def test_new_schema_variations_and_computed_witness(self):
        examples = (
            "forall a b c. (S(a)=S(b) /\\ S(b)=S(c)) -> S(a)=S(c)",
            "forall a b. a=b -> (S(a)=S(b) /\\ b=a)",
            "forall a. exists b. b = S(S(a+2))",
            "forall a. a=0 \\/ a=a",
            "forall a. (exists b. b=a) -> (exists c. c=a)",
        )
        for theorem in examples:
            with self.subTest(theorem=theorem):
                result = hybrid.search(theorem, limits=limits())
                self.assert_native_proof(result)
                self.assertFalse(result["model_used"])
                self.assertFalse(result["vampire_used"])
                self.assertEqual({item["source"] for item in result["provenance"]}, {"heuristic"})

    def test_easy_proof_never_loads_or_calls_advisors(self):
        class DoNotCall:
            def propose(self, *args, **kwargs):
                raise AssertionError("A deterministic proof must not load the model.")
            def advise(self, *args, **kwargs):
                raise AssertionError("A deterministic proof must not run Vampire.")
        result = hybrid.search("forall a b. a=b -> (a=b /\\ b=a)",
                               model_policy=DoNotCall(), vampire_advisor=DoNotCall(), limits=limits())
        self.assert_native_proof(result)
        self.assertEqual(result["model_advisor_calls"], 0)
        self.assertEqual(result["vampire_advisor_calls"], 0)

    def test_constructed_witnesses_and_unifying_implication_premises(self):
        examples = (
            "forall a b. (exists w. S w = b) -> exists z. S z = a + b",
            "forall a b c. (exists w. S w = b) -> exists z. S z = c + (a + b)",
            "forall a b. (exists w. b = S w) -> exists z. a + b = S z",
            "forall a b c. S (a+b) = c -> (forall z. S z = c -> b = 0) -> b = 0",
        )
        for theorem in examples:
            with self.subTest(theorem=theorem):
                result = hybrid.search(theorem, limits=limits())
                self.assert_native_proof(result)
                self.assertFalse(result["model_used"])
                self.assertFalse(result["vampire_used"])
        false_witness = hybrid.search("forall a. exists z. S z = 0",
            limits=limits(max_states=64, max_tactic_attempts=192, max_expansions=24))
        self.assertFalse(false_witness["kernel_checked"])
        self.assertIsNone(false_witness["replay"])

    def test_induction_discharges_both_native_obligations_without_ring(self):
        capabilities = SurfaceCapabilities(label="hybrid-induction-regression",
            allowed_commands=MODEL_V1_COMMANDS - {"ring", "compact_arith"}, allowed_theorems=frozenset())
        result = hybrid.search("forall n. 0+n=n", capabilities=capabilities, limits=limits())
        self.assert_native_proof(result)
        self.assertTrue(any(command.startswith("induction ") for command in result["commands"]))
        induction = next(item for item in result["branches"] if item["command"].startswith("induction ")
                         and item["status"] == "open")
        self.assertEqual(induction["open_goals"], 2)
        self.assertEqual(len(induction["goals_after"]), 2)

    def test_polynomial_induction_synthesizes_checked_modular_witnesses(self):
        # These require computed induction witnesses, not a term already present
        # in the original statement. The flipped and offset cubic equations
        # check that synthesis follows the actual goal rather than a saved title.
        theorems = (
            ("forall z. exists q. z*z=z+2*q", 4),
            ("forall a. exists b. a+3*b=a*a*a", 8),
            ("forall z. exists q. z*z*z+2*z=3*q", 8),
            ("forall n. exists k. n*n*n*n*n=n+5*k", 8),
        )
        for theorem, macro_steps in theorems:
            with self.subTest(theorem=theorem):
                result = hybrid.search(theorem, limits=limits(max_depth=64,
                    max_states=96, max_tactic_attempts=256, max_expansions=16,
                    max_macro_steps=macro_steps, wall_seconds=45))
                self.assert_native_proof(result)
                self.assertEqual(result["profile"], "hydra-playground-hybrid-v7")
                self.assertTrue(any(line.startswith("induction ") for line in result["commands"]))
                self.assertTrue(any(line.startswith("trans ") for line in result["commands"]))
                self.assertEqual(result["model_calls"], 0)
                self.assertEqual(result["vampire_calls"], 0)
                self.assertEqual({row["source"] for row in result["provenance"]}, {"heuristic"})

    def test_coupled_invariant_uses_both_local_induction_equalities(self):
        theorem = "forall n. exists t u. n*(n+1)=2*t /\\ n*(n+1)*(n+2)=6*u"
        result = hybrid.search(theorem, limits=limits(max_depth=64,
            max_states=128, max_tactic_attempts=256, max_expansions=16,
            max_macro_steps=8, closure_steps=16, wall_seconds=45))
        self.assert_native_proof(result)
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["vampire_calls"], 0)
        rewrites = {line for line in result["commands"] if line.startswith("rewrite ")}
        self.assertTrue(any("_left" in line for line in rewrites))
        self.assertTrue(any("_right" in line for line in rewrites))
        self.assertEqual(sum(line.startswith("exists ") for line in result["commands"]), 4)

    def test_generated_invariant_proves_original_divisibility_goals(self):
        # Neither statement supplies the auxiliary quadratic divisibility
        # invariant. Its projection and induction must be in the checked script.
        for theorem in (
            "forall z. exists q. z*z*z=z+6*q",
            "forall t. exists u. t*(t+1)*(t+2)=6*u",
        ):
            with self.subTest(theorem=theorem):
                result = hybrid.search(theorem, limits=limits(max_depth=96,
                    max_states=160, max_tactic_attempts=384, max_expansions=16,
                    max_macro_steps=8, closure_steps=16, heuristic_burst=8,
                    max_model_calls=0, max_vampire_calls=0, wall_seconds=60))
                self.assert_native_proof(result)
                self.assertEqual(result["profile"], "hydra-playground-hybrid-v7")
                self.assertEqual(result["strengthening_candidates"], 1)
                self.assertLessEqual(result["strengthening_expansions"], 8)
                self.assertEqual(result["model_calls"], 0)
                self.assertEqual(result["vampire_calls"], 0)
                self.assertEqual({row["source"] for row in result["provenance"]}, {"heuristic"})
                connector = [row for row in result["provenance"]
                    if row.get("evidence", {}).get("strategy") == "finite_difference_strengthening"]
                self.assertEqual(len(connector), 7)
                self.assertTrue(connector[0]["command"].startswith("suffices "))
                self.assertTrue(any(line.startswith("induction ") for line in result["commands"]))
                rewrites = [line for line in result["commands"] if line.startswith("rewrite ")]
                self.assertTrue(any("_left" in line for line in rewrites))
                self.assertTrue(any("_right" in line for line in rewrites))

    def test_strengthening_never_truncates_connector_or_trusts_wrong_goal(self):
        from peano_lab.engine.state import start
        from peano_lab.engine.tactics import apply_tactic
        from peano_lab.kernel.formulas import parse_formula_with_names

        target, names = parse_formula_with_names("forall n. exists k. n*n*n=n+6*k")
        state = apply_tactic(start(target, names), "intro", "")
        short = hybrid.heuristic_candidates(state, max_candidates=64, max_macro_steps=4)
        long = hybrid.heuristic_candidates(state, max_candidates=64, max_macro_steps=8)
        self.assertFalse(any(row.commands[0].startswith("suffices ") for row in short))
        connector = next(row for row in long if row.commands[0].startswith("suffices "))
        self.assertEqual(len(connector.commands), 7)

        # Reuse a true statement's suggested invariant against a false near
        # miss. Even an incorrectly flagged proposal must discharge the exact
        # original goal, and the search must not regenerate it on every branch.
        wrong_hint = ArithmeticHint(connector.commands, "fixture: wrong strengthening", True)
        with patch.object(hybrid, "strengthening_hints", return_value=(wrong_hint,)):
            result = hybrid.search("forall n. exists k. n*n*n=n+6*k+1",
                limits=limits(max_depth=48, max_states=48, max_tactic_attempts=96,
                    max_expansions=8, max_macro_steps=8, max_model_calls=0,
                    max_vampire_calls=0, wall_seconds=8))
        self.assertNotEqual(result["status"], "proof")
        self.assertFalse(result["kernel_checked"])
        self.assertIsNone(result["replay"])
        self.assertEqual(result["strengthening_candidates"], 1)
        self.assertTrue(any(row["command"].startswith("exact hydra_fd")
                            and row["status"] == "rejected" for row in result["branches"]))

    def test_arithmetic_proposals_cannot_prove_false_modular_claims(self):
        result = hybrid.search("forall n. exists k. n*n=n+3*k",
            limits=limits(max_states=64, max_tactic_attempts=192, max_expansions=16))
        self.assertNotEqual(result["status"], "proof")
        self.assertFalse(result["kernel_checked"])
        self.assertIsNone(result["replay"])
        # Deliberately lie in the untrusted algebra planner. Its closing flag
        # and polynomial comparison never replace the native certificate check.
        false_hint = ArithmeticHint(("ring",), "fixture: false algebra claim", True)
        with patch.object(hybrid, "arithmetic_hints", return_value=(false_hint,)):
            result = hybrid.search("forall n. n*n=n",
                limits=limits(max_states=32, max_tactic_attempts=64, max_expansions=4))
        self.assertFalse(result["kernel_checked"])
        self.assertIsNone(result["replay"])
        self.assertTrue(any(row["command"] == "ring" and row["status"] == "rejected"
                            for row in result["branches"]))

    def test_higher_budgets_are_explicit_and_defaults_do_not_increase(self):
        defaults = hybrid.HybridLimits()
        self.assertEqual((defaults.max_depth, defaults.max_states, defaults.max_model_calls,
                          defaults.max_vampire_calls, defaults.wall_seconds), (32, 256, 8, 4, 150.0))
        expanded = hybrid.HybridLimits(max_depth=160, max_states=8192,
            max_tactic_attempts=40000, max_expansions=4096, max_frontier=256,
            candidates_per_state=64, max_macro_steps=8, closure_steps=32,
            heuristic_burst=32, max_model_calls=128, max_vampire_calls=24,
            wall_seconds=600)
        self.assertEqual(expanded.max_depth, 160)
        for setting in ({"max_depth": 161}, {"max_states": 8193},
                        {"max_model_calls": 129}, {"max_vampire_calls": 25},
                        {"wall_seconds": 601}, {"wall_seconds": float("nan")},
                        {"max_states": True}):
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                hybrid.HybridLimits(**setting)

    def test_wall_expiry_does_not_claim_unused_tactic_attempt_budget(self):
        clock = [1000.0]
        validate = hybrid._validate_candidate

        def expire_during_validation(*args, **kwargs):
            result = validate(*args, **kwargs)
            clock[0] = 1002.0
            return result

        # Expire after one command is validated but before native execution.
        # This exercises the physical macro-step deadline, with no sleeps.
        with patch.object(hybrid.time, "monotonic", side_effect=lambda: clock[0]), \
                patch.object(hybrid, "_validate_candidate", side_effect=expire_during_validation):
            result = hybrid.search("0=1", limits=limits(wall_seconds=1))
        self.assertEqual(result["status"], "limit")
        self.assertEqual(result["limited_by"], ["wall_seconds"])
        self.assertEqual(result["tactic_attempts"], 0)
        self.assertFalse(result["kernel_checked"])

    def test_actual_model_edge_has_separate_provenance(self):
        model = CountingPolicy(("symm",))
        # Remove optional branch heuristics only. Prefixes, closure, model
        # invocation, native edge checks, finalizer and replay remain real.
        with patch.object(hybrid, "heuristic_candidates", return_value=()):
            result = hybrid.search("forall a b. a=b -> b=a", model_policy=model, limits=limits())
        self.assert_native_proof(result)
        self.assertEqual(model.calls, 1)
        self.assertEqual(result["model_calls"], 1)
        self.assertEqual(result["model_advisor_calls"], 1)
        self.assertEqual([item["source"] for item in result["provenance"]][-2:], ["model", "heuristic"])
        self.assertEqual(len(model.goals[0]), 1)

    def test_repeated_full_goals_do_not_spend_another_model_decode(self):
        model = CountingPolicy(("exfalso", "symm", "refl", "simp"))
        result = hybrid.search("0 = 1", model_policy=model,
            limits=limits(max_depth=24, max_states=128, max_tactic_attempts=256,
                          max_expansions=32, max_model_calls=16, max_vampire_calls=0))
        self.assertFalse(result["kernel_checked"])
        self.assertEqual(result["model_calls"], model.calls)
        self.assertEqual(len(set(model.goals)), len(model.goals))
        self.assertGreater(result["model_repeated_prompts_skipped"], 0)
        self.assertFalse(result["model_advice_memory"]["tactics_reused"])
        self.assertTrue(all(item["previous_model_call"] <= model.calls
                            for item in result["model_advice_memory"]["events"]))

    def test_false_theorems_and_external_theorem_claim_cannot_pass(self):
        for theorem in ("0=1", "forall a. S(a)=a", "forall a b. a=b"):
            with self.subTest(theorem=theorem):
                advisor = ClaimingAdvisor()
                result = hybrid.search(theorem, vampire_advisor=advisor,
                    limits=limits(max_states=64, max_tactic_attempts=192, max_expansions=24))
                self.assertNotEqual(result["status"], "proof")
                self.assertFalse(result["kernel_checked"])
                self.assertEqual(result["commands"], [])
                self.assertIsNone(result["replay"])
                self.assertLessEqual(advisor.requests, 2)
                self.assertEqual(result["vampire_calls"], 0)
                self.assertTrue(all(item["kernel_checked"] is False for item in result["advisor_results"]))

    def test_failed_lazy_loading_does_not_claim_model_inference(self):
        class FailedLoad:
            calls = 0
            def propose(self, *args, **kwargs):
                raise ValueError("fixture: model not loaded")
        with patch.object(hybrid, "heuristic_candidates", return_value=()):
            result = hybrid.search("0=1", model_policy=FailedLoad(), limits=limits())
        self.assertEqual(result["model_advisor_calls"], 1)
        self.assertEqual(result["model_calls"], 0)
        self.assertFalse(result["model_used"])
        self.assertTrue(any(item["kind"] == "model_error" for item in result["diagnostics"]))

    def test_unsupported_focused_state_does_not_disable_later_vampire_advice(self):
        class FragmentAdvisor:
            def __init__(self, first_status):
                self.first_status = first_status
                self.requests = 0

            def advise(self, state):
                self.requests += 1
                if self.requests == 1:
                    return {"status": self.first_status,
                            "solver": {"available": False, "invocations": 0}, "suggestions": []}
                return {"status": "no_refutation",
                        "solver": {"available": True, "invocations": 1}, "suggestions": []}

        def growing_branch(state, **_):
            return (hybrid._proposal(f"have extra{len(state.history)} : 0=0", "refl",
                                    reason="fixture: another open native state"),)

        for status, requests, invocations in (("unsupported_fragment", 2, 1), ("unavailable", 1, 0)):
            with self.subTest(status=status), patch.object(hybrid, "heuristic_candidates", side_effect=growing_branch):
                advisor = FragmentAdvisor(status)
                result = hybrid.search("0=1", vampire_advisor=advisor,
                    limits=limits(max_vampire_calls=2, heuristic_burst=1, max_expansions=6))
                self.assertEqual(advisor.requests, requests)
                self.assertEqual(result["vampire_calls"], invocations)
                self.assertFalse(result["kernel_checked"])

    def test_failed_macro_retains_its_valid_native_prefix(self):
        bad_tail = hybrid._proposal("symm", "intro", reason="fixture: useful edge followed by invalid introduction")
        with patch.object(hybrid, "heuristic_candidates", return_value=(bad_tail,)):
            result = hybrid.search("forall a b. a=b -> b=a", limits=limits())
        self.assert_native_proof(result)
        self.assertEqual(result["commands"][-2:], ["symm", "exact h"])
        self.assertTrue(any(item["command"] == "intro" and item["status"] == "rejected"
                            for item in result["branches"]))

    def test_model_queue_is_serviced_despite_growing_symbolic_frontier(self):
        model = CountingPolicy()
        updates = []

        def add_irrelevant_fact(state, **_):
            name = "extra" + str(len(state.history))
            return (hybrid._proposal(f"have {name} : 0=0", "refl", reason="fixture: expanding branch"),)

        with patch.object(hybrid, "heuristic_candidates", side_effect=add_irrelevant_fact):
            result = hybrid.search("0=1", model_policy=model, emit_progress=updates.append,
                limits=limits(max_model_calls=1, heuristic_burst=2, max_expansions=8))
        model_updates = [event for event in updates if event["phase"] == "model"]
        self.assertEqual(model.calls, 1)
        self.assertEqual(len(model_updates), 1)
        self.assertLessEqual(model_updates[0]["states_expanded"], 2)
        self.assertNotEqual(result["status"], "proof")

    def test_native_alpha_identity_merges_only_checked_equivalent_prefixes(self):
        def names_only(state, **_):
            if type(state.current().target) is Forall:
                return (hybrid._proposal("intro a", reason="fixture: first alpha name"),
                        hybrid._proposal("intro b", reason="fixture: second alpha name"))
            return (hybrid._proposal("refl", reason="fixture: reflexive remaining goal"),)

        with patch.object(hybrid, "_closure_candidates", return_value=()), \
                patch.object(hybrid, "heuristic_candidates", side_effect=names_only):
            result = hybrid.search("forall x. x=x", limits=limits())
        self.assert_native_proof(result)
        counters = result["state_identity"]["counters"]
        self.assertGreaterEqual(counters["duplicate_states"], 1)
        self.assertGreaterEqual(counters["renamed_states"], 1)

    def test_advisor_text_is_bounded_and_session_commands_are_rejected(self):
        model = CountingPolicy(("refl\nrefl", "classical", "use zero_add", "exists 65"))
        with patch.object(hybrid, "heuristic_candidates", return_value=()):
            result = hybrid.search("0=1", model_policy=model, limits=limits())
        self.assertFalse(result["kernel_checked"])
        self.assertEqual(result["commands"], [])
        self.assertTrue(any(item["kind"] == "invalid_candidate" for item in result["diagnostics"]))
        self.assertTrue(any(item["command"] == "use zero_add" and item["status"] == "rejected"
                            for item in result["branches"]))


if __name__ == "__main__":
    unittest.main()
