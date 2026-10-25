"""Pure AST/algebra tests only: no tactic, kernel, model, or solver calls."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "hydra-playground"),
               str(ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py")]
from peano_lab.kernel.formulas import Eq, Exists, Forall, parse_formula_in_context, pretty_formula
from peano_lab.kernel.terms import Var
from finite_difference import propose_strengthening


def proposal(source, variables=("n",), context=()):
    target = parse_formula_in_context(source, list(variables))
    goal = SimpleNamespace(variables=variables, context=context, target=target)
    return propose_strengthening(goal, target, context)


class AlgebraOnlyTests(unittest.TestCase):
    def test_coefficients_derive_one_auxiliary_and_its_update(self):
        examples = (
            ("exists k. n*n*n = n+6*k", ((1, 1), (2, 1)), ((0, 1), (1, 1))),
            ("exists k. n*(n+1)*(n+2) = 6*k", ((0, 2), (1, 3), (2, 1)), ((0, 2), (1, 1))),
        )
        for source, auxiliary, increment in examples:
            with self.subTest(source=source):
                result = proposal(source)
                self.assertIsNotNone(result)
                self.assertEqual((result.divisor, result.common_factor, result.auxiliary_divisor), (6, 3, 2))
                self.assertEqual(result.auxiliary_coefficients, auxiliary)
                self.assertEqual(result.auxiliary_increment, increment)
                self.assertEqual(len(result.commands), 7)
                self.assertTrue(all(len(item.encode()) <= 512 for item in result.commands))
                rendered = pretty_formula(result.strengthened, ["n"])
                self.assertEqual(parse_formula_in_context(rendered, ["n"]), result.strengthened)

    def test_syntactic_projection_preserves_the_actual_source_equation(self):
        result = proposal("exists k. 6*k+n = n*n*n")
        expected = parse_formula_in_context(
            "forall z. exists k t. (6*k+z=z*z*z /\\ z*z+z=2*t)", [])
        self.assertEqual(result.strengthened, expected)
        self.assertEqual(result.commands[-2:], ("exists x", "exact hydra_fd_witness_witness_left"))

    def test_fresh_names_and_parameter_indices_follow_the_native_scope(self):
        context = (("x1", Eq(Var(0), Var(0))),)
        result = proposal("exists k. z*z*z=z+6*k", ("x", "z"), context)
        self.assertEqual(result.parameter_index, 1)
        self.assertEqual(result.commands[1], "specialize hydra_fd z")
        self.assertEqual(result.commands[-2], "exists x2")
        expected = parse_formula_in_context(
            "forall z. exists k t. (z*z*z=z+6*k /\\ z*z+z=2*t)", [])
        self.assertEqual(result.strengthened, expected)

    def test_unsupported_or_unnecessary_strengthening_is_not_repeated(self):
        for source in ("exists k. n=2*k", "exists k. n*n=n*n+6*k",
                       "exists k. (2*n+1)*(2*n+1)=1+8*k",
                       "exists k t. (n*n*n=n+6*k /\\ n*n+n=2*t)",
                       "exists k. n*n*n=5*k"):
            with self.subTest(source=source):
                self.assertIsNone(proposal(source))
        for name in ("IH", "IH1", "hydra_fd", "hydra_fd_witness"):
            self.assertIsNone(proposal("exists k. n*n*n=n+6*k", context=((name, Eq(Var(0), Var(0))),)))
        self.assertIsNone(proposal("exists k. n*n*n+m=n+6*k", ("n", "m")))


if __name__ == "__main__":
    unittest.main()
