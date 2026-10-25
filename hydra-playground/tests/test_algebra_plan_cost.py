"""Bounded cost-only tests; objects are constructed, never proved or searched."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(ROOT / "hydra-playground"), str(SOURCE / "peano-lab/py")]

from algebra_plan_cost import AlgebraCostLimits, estimate_algebra_plan, rank_plan_indices
from peano_lab.kernel.formulas import Eq, Forall
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero


class AlgebraPlanCostTests(unittest.TestCase):
    def equation(self):
        a, b = Var(0), Var(1)
        return Eq(Add(a, b), Add(b, a))

    def test_estimate_does_not_test_whether_the_equation_is_true(self):
        false = Eq(Zero(), Succ(Zero()))
        with patch("peano_lab.kernel.checker.check", side_effect=AssertionError("no checking")):
            result = estimate_algebra_plan(false, ("ring",))
        self.assertEqual(result["status"], "estimated")
        self.assertFalse(result["proof_check_performed"])
        self.assertEqual(result["tactics_executed"], 0)
        self.assertIn("not proof objects", result["score_unit"])

    def test_syntactic_reuse_is_independent_of_python_object_sharing(self):
        shared = Add(Var(0), Var(1))
        reused = Eq(Mul(shared, shared), Mul(shared, shared))

        def fresh():
            return Add(Var(0), Var(1))

        copied = Eq(Mul(fresh(), fresh()), Mul(fresh(), fresh()))
        a = estimate_algebra_plan(reused, ("ring",))
        b = estimate_algebra_plan(copied, ("ring",))
        self.assertEqual(a["source_ast"], b["source_ast"])
        self.assertGreater(a["source_ast"]["repeated_compound_occurrences"], 0)
        self.assertGreater(a["source_ast"]["ast_occurrences"], a["source_ast"]["unique_syntax_nodes"])

    def test_command_growth_penalizes_longer_equivalent_candidate_sequences(self):
        short = estimate_algebra_plan(self.equation(), ("ring",))
        long = estimate_algebra_plan(self.equation(), ("symm", "symm", "ring"))
        self.assertGreater(long["score"], short["score"])
        self.assertEqual(long["components"]["command_growth"], 2)

    def test_existing_chunk_plan_obligation_format_and_native_ast_agree(self):
        declaration = {"kind": "abstracted_ring", "theorem": "forall a b. a+b=b+a",
                       "concrete": "ignored; not a measured intermediate state"}
        ast = Forall(Forall(self.equation()))
        by_text = estimate_algebra_plan(self.equation(), ("ring",), obligations=(declaration,))
        by_ast = estimate_algebra_plan(self.equation(), ("ring",), obligations=(ast,))
        self.assertEqual(by_text["status"], "estimated")
        self.assertEqual(by_text["ring_goal_basis"], "declared_ring_obligations")
        self.assertEqual(by_text["ring_obligations"], by_ast["ring_obligations"])
        self.assertEqual(by_text["score"], by_ast["score"])

    def test_alpha_renamed_obligations_have_identical_ast_features(self):
        a = estimate_algebra_plan(self.equation(), ("ring",),
                                  obligations=("forall a b. a+b=b+a",))
        b = estimate_algebra_plan(self.equation(), ("ring",),
                                  obligations=("forall longer fresh. longer+fresh=fresh+longer",))
        self.assertEqual(a["ring_obligations"], b["ring_obligations"])
        self.assertEqual(a["score"], b["score"])

    def test_declared_small_ring_goals_change_cost_without_claiming_a_connector(self):
        binomial = Add(Var(0), Var(1))
        power = binomial
        for _ in range(6):
            power = Mul(power, binomial)
        source = Eq(power, Var(0))  # Deliberately not an established identity.
        direct = estimate_algebra_plan(source, ("ring",))
        declared = estimate_algebra_plan(source, ("congr", "ring", "ring"),
            obligations=(self.equation(), self.equation()))
        self.assertLess(declared["score"], direct["score"])
        self.assertFalse(declared["proof_check_performed"])
        self.assertEqual(declared["source_ast"], direct["source_ast"])

    def test_budget_failure_retains_unscored_fallback_in_ranking(self):
        fallback = estimate_algebra_plan(self.equation(), ("ring",),
                                         limits=AlgebraCostLimits(max_work=1))
        other = estimate_algebra_plan(self.equation(), ("ring",))
        self.assertEqual(fallback["status"], "unavailable")
        self.assertIsNone(fallback["score"])
        ordering = rank_plan_indices((fallback, other), fallback_index=0)
        self.assertEqual(ordering, (0, 1))
        self.assertEqual(set(ordering), {0, 1})
        self.assertTrue(fallback["fallback_must_be_retained"])

    def test_equal_unknown_and_malformed_scores_never_drop_an_alternative(self):
        known = estimate_algebra_plan(self.equation(), ("ring",))
        invalid = {**known, "score": False}
        values = (None, known, dict(known), invalid)
        self.assertEqual(rank_plan_indices(values, fallback_index=0), (0, 1, 2, 3))
        self.assertEqual(rank_plan_indices((None, None), fallback_index=1), (1, 0))

    def test_complete_estimates_rank_stably_and_keep_the_existing_fallback(self):
        short = estimate_algebra_plan(self.equation(), ("ring",))
        long = estimate_algebra_plan(self.equation(), ("symm", "symm", "ring"))
        self.assertEqual(rank_plan_indices((long, short, dict(short)), fallback_index=0), (1, 2, 0))

    def test_foreign_objects_cycles_and_large_ast_are_uncosted(self):
        cycle = Add(Var(0), Zero())
        object.__setattr__(cycle, "left", cycle)
        cases = ((Eq(cycle, Zero()), AlgebraCostLimits(), "ast_cycle"),
                 (self.equation(), AlgebraCostLimits(max_ast_nodes=2), "ast_node_limit"),
                 (self.equation(), AlgebraCostLimits(max_ast_depth=1), "ast_depth_limit"),
                 (Eq(Var(64), Zero()), AlgebraCostLimits(), "variable_index"))
        for equation, limits, reason in cases:
            with self.subTest(reason=reason):
                result = estimate_algebra_plan(equation, ("ring",), limits=limits)
                self.assertIsNone(result["score"])
                self.assertEqual(result["reason"], reason)

    def test_unsafe_or_oversized_text_is_declined_before_parsing(self):
        examples = ("forall a. a=a -> a=a", "forall a. a=" + "9" * 20,
                    "(" * 49 + "a=a" + ")" * 49, "a=a\nring")
        for text in examples:
            with self.subTest(text=text[:40]), patch("algebra_plan_cost.parse_formula_with_names",
                    side_effect=AssertionError("must reject before parsing")):
                result = estimate_algebra_plan(self.equation(), ("ring",), obligations=(text,))
                self.assertEqual(result["status"], "unavailable")

    def test_obligation_mismatch_and_unmaterialized_commands_are_declined(self):
        result = estimate_algebra_plan(self.equation(), ("ring", "ring"),
                                      obligations=(self.equation(),))
        self.assertEqual(result["reason"], "ring_obligation_count")

        def infinite():
            raise AssertionError("a generator must not be consumed")
            yield "ring"

        result = estimate_algebra_plan(self.equation(), infinite())
        self.assertEqual(result["reason"], "command_count")

    def test_cancellation_has_no_score_and_no_proof_claim(self):
        result = estimate_algebra_plan(self.equation(), ("ring",), should_stop=lambda: True)
        self.assertEqual(result["status"], "cancelled")
        self.assertIsNone(result["score"])
        self.assertEqual(result["work_units"], 0)

    def test_bad_encoding_and_oversized_lines_keep_cost_unknown(self):
        for commands, obligations in ((("\ud800",), ()), ((" " * 4096,), ()),
                                     (("ring",), ("a=\ud800",))):
            result = estimate_algebra_plan(self.equation(), commands, obligations=obligations)
            self.assertEqual(result["status"], "unavailable")
            self.assertIsNone(result["score"])

    def test_configuration_and_ranking_inputs_remain_bounded(self):
        for settings in ({"max_commands": True}, {"max_ast_nodes": 4097}, {"max_work": 0}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                AlgebraCostLimits(**settings)
        for estimates, index in (((), 0), ((None,) * 9, 0), ((None,), True), ((None,), 1)):
            with self.subTest(index=index), self.assertRaises(ValueError):
                rank_plan_indices(estimates, fallback_index=index)


if __name__ == "__main__":
    unittest.main(verbosity=2)
