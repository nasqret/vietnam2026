"""Bounded strengthening proposals and their native scope/authority boundaries."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
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

    def test_context_scalar_and_command_bounds_reject_the_proposal(self):
        source = "exists k. n*n*n=n+6*k"
        context = tuple(("H" + str(index), Eq(Var(0), Var(0))) for index in range(33))
        self.assertIsNone(proposal(source, context=context))
        self.assertIsNone(proposal("exists k. n*n*n=n+66*k"))
        self.assertIsNone(proposal("exists k. n*n*n=n+6*k*k"))
        name = "p" * 512
        self.assertIsNone(proposal(f"exists k. {name}*{name}*{name}={name}+6*k", (name,)))


class NativeProjectionTests(unittest.TestCase):
    @staticmethod
    def state_after(theorem, commands):
        from peano_lab.kernel.formulas import parse_formula_with_names
        from peano_lab.engine.state import start
        from peano_lab.engine.tactics import apply_tactic
        target, names = parse_formula_with_names(theorem)
        state = start(target, names)
        for command in commands:
            tactic, _, args = command.partition(" ")
            state = apply_tactic(state, tactic, args)
        return state

    def test_projection_preserves_exact_goal_and_native_variable_scope(self):
        examples = (
            ("forall n. exists k. n*n*n=n+6*k", ("intro n",)),
            ("forall n. exists k. 6*k+n=n*n*n", ("intro n",)),
            ("forall a b. exists k. a*a*a=a+6*k", ("intro a", "intro b")),
            ("forall n. n=n -> n=n -> exists k. n*n*n=n+6*k", ("intro n", "intro x", "intro x1")),
            ("forall hydra_fd. exists k. hydra_fd*hydra_fd*hydra_fd=hydra_fd+6*k", ("intro hydra_fd",)),
        )
        for theorem, prefix in examples:
            with self.subTest(theorem=theorem):
                before = self.state_after(theorem, prefix)
                goal = before.current()
                hint = propose_strengthening(goal, goal.target, goal.context)
                self.assertIsNotNone(hint)
                after = self.state_after(theorem, prefix + hint.commands)
                self.assertEqual(after.target, before.target)
                self.assertEqual(len(after.goals), 1)
                self.assertEqual(after.current().target, hint.strengthened)
                # Projection leaves the stronger theorem to prove. A proposed
                # invariant and a successfully projected goal are not proofs.
                self.assertEqual(after.current().context, goal.context)
                self.assertEqual(after.current().variables, goal.variables)

    def test_untrusted_connector_cannot_change_the_actual_theorem(self):
        from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
        from peano_lab.ui.prove import SurfaceCapabilities
        before = self.state_after("forall n. exists k. n*n*n=n+6*k", ("intro n",))
        goal = before.current()
        hint = propose_strengthening(goal, goal.target, goal.context)
        capabilities = SurfaceCapabilities(label="finite-difference-wrong-target-test",
            allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
        result = run_proof("forall n. exists k. n*n*n=n+6*k+1", ("intro n",) + hint.commands,
            capabilities=capabilities, classical=False, on_error="stop")
        self.assertEqual(result.status, "tactic_error")
        self.assertFalse(result.kernel_checked)
        self.assertTrue(result.goals)


if __name__ == "__main__":
    unittest.main()
