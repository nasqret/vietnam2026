"""Scope, refusal, cancellation, and native tests for compound-atom plans."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(HERE), str(ROOT / "hydra-playground"), str(SOURCE), str(SOURCE / "peano-lab/py")]

from atom_polynomial import atom_polynomial_chunk_plan
from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.kernel.formulas import Eq, Forall, Imp, parse_formula_with_names
from peano_lab.kernel.terms import Zero
from peano_lab.ui.prove import SurfaceCapabilities

THEOREM = ("forall a b. (a*a+2*a*b)*(a*a+2*a*b)+2*b*(a+b)*(2*b*(a+b))="
           "(a*a+2*a*b+2*b*b)*(a*a+2*a*b+2*b*b)")
CAPABILITIES = SurfaceCapabilities(label="hydra-polynomial-atom-tests-no-imports",
    allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())


def equation(theorem):
    formula, _ = parse_formula_with_names(theorem)
    while type(formula) in (Forall, Imp):
        formula = formula.body if type(formula) is Forall else formula.right
    return formula


class AtomPolynomialTests(unittest.TestCase):
    def test_complete_plan_is_bounded_and_retains_compound_term(self):
        plan = atom_polynomial_chunk_plan(equation(THEOREM), ["b", "a"])
        self.assertIsNotNone(plan)
        self.assertEqual(plan.strategy, "polynomial_atoms_v1")
        self.assertGreater(plan.analysis["rewrites"], 0)
        self.assertLessEqual(plan.analysis["rewrites"], 8)
        self.assertLessEqual(plan.analysis["polynomial_analyses"], 1024)
        self.assertLessEqual(plan.analysis["control_work_units"], 131072)
        self.assertLessEqual(plan.analysis["script_bytes"], 64 * 1024)
        self.assertLessEqual(len(plan.commands), 156)
        self.assertTrue(all(1 <= len(chunk) <= 8 for chunk in plan.chunks()))
        self.assertEqual(tuple(command for chunk in plan.chunks() for command in chunk), plan.commands)
        self.assertTrue(all(len(line.encode("utf-8")) <= 512 for line in plan.commands))

    def test_false_near_miss_and_unsupported_shape_decline(self):
        self.assertIsNone(atom_polynomial_chunk_plan(equation(THEOREM + "+1"), ["b", "a"]))
        self.assertIsNone(atom_polynomial_chunk_plan(Forall(Eq(Zero(), Zero())), []))

    def test_cancellation_checks_start_and_during_analysis(self):
        target = equation(THEOREM)
        self.assertIsNone(atom_polynomial_chunk_plan(target, ["b", "a"], should_stop=lambda: True))
        calls = []

        def stop():
            calls.append(True)
            return len(calls) >= 2

        self.assertIsNone(atom_polynomial_chunk_plan(target, ["b", "a"], should_stop=stop))
        self.assertGreaterEqual(len(calls), 2)

    def test_total_budget_and_resource_errors_are_not_silenced(self):
        target = equation(THEOREM)
        with patch("polynomial_chunks.MAX_CONTROL_WORK", 0):
            self.assertIsNone(atom_polynomial_chunk_plan(target, ["b", "a"]))
        for error in (TimeoutError("stop"), MemoryError("allocation")):
            with patch("polynomial_chunks._polynomial", side_effect=error):
                with self.assertRaises(type(error)):
                    atom_polynomial_chunk_plan(target, ["b", "a"])

    def test_native_renamed_unused_scope_and_name_collisions(self):
        theorem = ("forall cp1 spare hc0. 0=0 -> "
            "(cp1*cp1+2*cp1*hc0)*(cp1*cp1+2*cp1*hc0)+"
            "2*hc0*(cp1+hc0)*(2*hc0*(cp1+hc0))="
            "(cp1*cp1+2*cp1*hc0+2*hc0*hc0)*(cp1*cp1+2*cp1*hc0+2*hc0*hc0)")
        context = (("hc3", Eq(Zero(), Zero())),)
        plan = atom_polynomial_chunk_plan(equation(theorem), ["hc0", "spare", "cp1"], context)
        self.assertIsNotNone(plan)
        commands = ("intro cp1", "intro spare", "intro hc0", "intro hc3", *plan.commands)
        result = run_proof(theorem, commands, capabilities=CAPABILITIES).to_dict()
        self.assertEqual(result["status"], "proved", result)
        self.assertIs(result["kernel_checked"], True)
        self.assertEqual(result["goals"], [])


if __name__ == "__main__":
    # Only standalone execution is constrained; importing this module into the
    # root's already guarded full suite must not change that process's limits.
    import resource
    import signal
    resource.setrlimit(resource.RLIMIT_CPU, (9, 9))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(9)
    unittest.main(verbosity=2)
