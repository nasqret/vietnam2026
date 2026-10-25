"""Focused native connector/scope/negative tests for the isolated prototype."""
from pathlib import Path
import resource
import signal
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(HERE), str(ROOT / "hydra-playground"), str(SOURCE), str(SOURCE / "peano-lab/py")]
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_CPU, (9, 9))
signal.alarm(9)

from polynomial_chunks import polynomial_chunk_plan
from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.kernel.formulas import Eq, Forall, Imp, parse_formula_with_names
from peano_lab.kernel.terms import Succ, Var, Zero
from peano_lab.ui.prove import SurfaceCapabilities

CAPABILITIES = SurfaceCapabilities(label="hydra-polynomial-chunk-tests-no-imports",
    allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())


class PolynomialChunksTests(unittest.TestCase):
    def checked_plan(self, theorem, introductions, variables, context=()):
        target, _ = parse_formula_with_names(theorem)
        while type(target) in (Forall, Imp):
            target = target.body if type(target) is Forall else target.right
        plan = polynomial_chunk_plan(target, variables, context)
        self.assertIsNotNone(plan)
        self.assertTrue(any(command.startswith("suffices ") for command in plan.commands))
        self.assertTrue(all(1 <= len(chunk) <= 8 for chunk in plan.chunks()))
        self.assertEqual(tuple(command for chunk in plan.chunks() for command in chunk), plan.commands)
        self.assertTrue(all(len(command.encode("utf-8")) <= 512 for command in plan.commands))
        result = run_proof(theorem, (*introductions, *plan.commands), capabilities=CAPABILITIES).to_dict()
        self.assertEqual(result["status"], "proved", result)
        self.assertIs(result["kernel_checked"], True)
        self.assertEqual(result["goals"], [])
        self.assertGreater(result["proof_nodes"], 0)
        return plan

    def test_fresh_names_do_not_capture_rigid_variables_or_hypotheses(self):
        theorem = "forall cp0 n. 0=0 -> (n*n)*(n+cp0)=n*n*n+(n*n)*cp0"
        self.checked_plan(theorem, ("intro cp0", "intro n", "intro hc1"),
            ["n", "cp0"], (("hc1", Eq(Zero(), Zero())),))

    def test_unused_scope_gap_is_preserved(self):
        theorem = "forall n spare a. (n*n)*(n+a)=n*n*n+(n*n)*a"
        self.checked_plan(theorem, ("intro n", "intro spare", "intro a"), ["a", "spare", "n"])

    def test_same_valid_connector_script_does_not_prove_false_near_miss(self):
        theorem = "forall n a. (n*n)*(n+a)=n*n*n+(n*n)*a"
        target, _ = parse_formula_with_names(theorem)
        plan = polynomial_chunk_plan(target.body.body, ["a", "n"])
        self.assertIsNotNone(plan)
        false = "forall n a. (n*n)*(n+a)=n*n*n+(n*n)*a+1"
        result = run_proof(false, ("intro n", "intro a", *plan.commands), capabilities=CAPABILITIES).to_dict()
        self.assertNotEqual(result["status"], "proved")
        self.assertIsNot(result["kernel_checked"], True)

    def test_false_identity_has_no_proposal_even_with_irrelevant_context(self):
        false = Eq(Var(0), Succ(Var(0)))
        self.assertIsNone(polynomial_chunk_plan(false, ["n"], (("h", Eq(Zero(), Zero())),)))

    def test_out_of_scope_terms_and_non_equalities_are_rejected(self):
        self.assertIsNone(polynomial_chunk_plan(Eq(Var(2), Var(2)), ["n"]))
        self.assertIsNone(polynomial_chunk_plan(Forall(Eq(Var(0), Var(0))), []))

    def test_chunk_size_bounds_are_explicit(self):
        plan = polynomial_chunk_plan(Eq(Var(0), Var(0)), ["n"])
        self.assertEqual(plan.commands, ("refl",))
        for invalid in (0, 9, True):
            with self.assertRaises(ValueError):
                plan.chunks(invalid)

    def test_cancellation_is_polled_and_no_partial_plan_escapes(self):
        self.assertIsNone(polynomial_chunk_plan(Eq(Var(0), Var(0)), ["n"], should_stop=lambda: True))
        calls = []

        def stop_after_start():
            calls.append(True)
            return len(calls) >= 2

        theorem, _ = parse_formula_with_names("forall n a. (n*n)*(n+a)=n*n*n+(n*n)*a")
        self.assertIsNone(polynomial_chunk_plan(theorem.body.body, ["a", "n"], should_stop=stop_after_start))
        self.assertGreaterEqual(len(calls), 2)

    def test_global_work_caps_and_unexpected_resource_errors(self):
        target = Eq(Var(0), Var(0))
        with patch("polynomial_chunks.MAX_ANALYSES", 0):
            self.assertIsNone(polynomial_chunk_plan(target, ["n"]))
        with patch("polynomial_chunks.MAX_CONTROL_WORK", 0):
            self.assertIsNone(polynomial_chunk_plan(target, ["n"]))
        for error in (TimeoutError("deadline"), MemoryError("allocation")):
            with patch("polynomial_chunks._polynomial", side_effect=error):
                with self.assertRaises(type(error)):
                    polynomial_chunk_plan(target, ["n"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
