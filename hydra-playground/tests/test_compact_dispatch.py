"""Pure routing tests; no native tactic, proof search, model, or solver run."""
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
SOURCE = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(APP), str(SOURCE / "peano-lab/py")]
import compact_dispatch as dispatch
from peano_lab.engine.state import Goal, MetaVar
from peano_lab.kernel.formulas import Eq, Forall, parse_formula_in_context, parse_formula_with_names
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero


def goal(text, assumptions=()):
    target, names = parse_formula_with_names(text)
    context = tuple((name, parse_formula_in_context(formula, list(names)))
                    for name, formula in assumptions)
    return Goal(context, target, names)


class CompactDispatchTests(unittest.TestCase):
    def test_actual_recurrence_schemas_in_both_orientations(self):
        examples = (
            ("S a + b = S(a+b)", "successor_left_add"),
            ("S a * b = a*b+b", "successor_left_mul"),
            ("(offset+n)+S a = (offset+a)+S n", "offset_swap"),
            ("(2*w+v)+v = 2*(w+v)", "doubling"),
            ("a*(b+1) = a*b+a", "mul_add_one"),
            ("S((x+y)*z)*q = ((x+y)*z)*q+q", "successor_left_mul"),
        )
        for text, schema in examples:
            original = goal(text)
            for target in (original.target, Eq(original.target.right, original.target.left)):
                with self.subTest(text=text, reversed=target != original.target):
                    hint = dispatch.compact_arith_hint(original, target, original.context)
                    self.assertIsNotNone(hint)
                    self.assertEqual(hint.commands, ("compact_arith",))
                    self.assertIn(schema, hint.schemas)
                    self.assertEqual(hint.selected_assumptions, ())
                    self.assertLessEqual(hint.analysis_work, dispatch.MAX_WORK)

    def test_congruence_requires_all_children_and_pa6_transport_is_supported(self):
        examples = (
            "S((S a*b)+c)=S((a*b+b)+c)",
            "S a*S b=(a*b+b)+S a",
            "(S a*b)+((c+0)+0)=(a*b+b)+c",
            "(S a*b)*(S c+d)=(a*b+b)*S(c+d)",
        )
        for text in examples:
            with self.subTest(text=text):
                self.assertIsNotNone(dispatch.compact_arith_hint(goal(text)))
        self.assertIsNone(dispatch.compact_arith_hint(goal("(S a*b)+c=(a*b+b)+S c")))

    def test_explicit_local_equation_transport_and_reverse_selection(self):
        text = "(n+v)+v=2*(w+v)"
        for hypothesis, expected in (("n=2*w", "IH"), ("2*w=n", "<- IH")):
            current = goal(text, (("IH", hypothesis),))
            hint = dispatch.compact_arith_hint(current)
            self.assertEqual(hint.commands, (f"compact_arith [{expected}]",))
            self.assertEqual(hint.schemas, ("doubling_transport",))
            self.assertEqual(hint.selected_assumptions, (expected,))
        current = goal("(n+v)+v=2*(w+v)", (("χ'", "n=2*w"),))
        self.assertEqual(dispatch.compact_arith_hint(current).commands, ("compact_arith [χ']",))
        wrong = goal(text, (("IH", "n=2*w+1"),))
        self.assertIsNone(dispatch.compact_arith_hint(wrong))
        reverse_goal = Goal(current.context, Eq(current.target.right, current.target.left), current.variables)
        self.assertIsNone(dispatch.compact_arith_hint(reverse_goal))

    def test_unsupported_shapes_and_false_near_misses_fall_through(self):
        for text in (
            "a+b=b+a", "a*(b+c)=a*b+a*c", "a*a=a", "0=1",
            "S a*b=a*b+a", "(offset+n)+S a=(offset+a)+S(S n)",
            "(2*w+v)+v=2*(w+S v)", "a*(b+2)=a*b+a",
            "forall n. exists k. n*n*n*n*n*n*n=n+7*k",
        ):
            with self.subTest(text=text):
                self.assertIsNone(dispatch.compact_arith_hint(goal(text)))

    def test_trivial_closures_are_not_replaced_with_compact_search(self):
        for text in ("a=a", "a+0=a", "a+1=S a", "a+2=S(S a)", "a*S b=a*b+a"):
            with self.subTest(text=text):
                self.assertIsNone(dispatch.compact_arith_hint(goal(text)))

    def test_no_assumption_injection_or_ambiguous_name_selection(self):
        text = "(n+v)+v=2*(w+v)"
        for name in ("IH], ring", "IH\nrefl", "IH;refl", "x" * 65):
            with self.subTest(name=name):
                self.assertIsNone(dispatch.compact_arith_hint(goal(text, ((name, "n=2*w"),))))
        current = goal(text, (("IH", "n=2*w"), ("IH", "n=2*w")))
        self.assertIsNone(dispatch.compact_arith_hint(current))
        quantified = goal(text, (("IH", "forall z. n=2*w"),))
        self.assertIsNone(dispatch.compact_arith_hint(quantified))

    def test_metas_malformed_scope_and_ast_bounds_are_declined(self):
        for term in (MetaVar(0), Var(-1), Var(2), Var(True)):
            current = Goal((), Eq(Mul(Succ(term), Var(0)), Add(Mul(term, Var(0)), Var(0))), ("x",))
            self.assertIsNone(dispatch.compact_arith_hint(current))
        term = Var(0)
        for _ in range(dispatch.MAX_TERM_DEPTH + 1):
            term = Succ(term)
        self.assertIsNone(dispatch.compact_arith_hint(Goal((), Eq(term, term), ("x",))))
        term = Var(0)
        for _ in range(9):
            term = Add(term, term)
        self.assertIsNone(dispatch.compact_arith_hint(Goal((), Eq(term, term), ("x",))))
        self.assertIsNone(dispatch.compact_arith_hint(None))
        current = goal("S a*b=a*b+b")
        self.assertIsNone(dispatch.compact_arith_hint(Goal((), Forall(current.target), current.variables)))

    def test_fixed_work_pair_and_cancellation_limits(self):
        current = goal("S a*b=a*b+b")
        with patch.object(dispatch, "MAX_WORK", 1):
            self.assertIsNone(dispatch.compact_arith_hint(current))
        with patch.object(dispatch, "MAX_MATCH_PAIRS", 0):
            self.assertIsNone(dispatch.compact_arith_hint(current))
        self.assertIsNone(dispatch.compact_arith_hint(current, should_stop=lambda: True))
        for exception in (MemoryError, TimeoutError):
            def fail():
                raise exception("fixture: propagate resource exceptions")
            with self.subTest(exception=exception), self.assertRaises(exception):
                dispatch.compact_arith_hint(current, should_stop=fail)

    def test_hint_is_immutable_and_recognition_imports_no_prover(self):
        hint = dispatch.compact_arith_hint(goal("S a*b=a*b+b"))
        with self.assertRaises(FrozenInstanceError):
            hint.commands = ("ring",)
        # Check the dispatch source's imports without importing any certificate
        # builder. This remains valid when a larger suite has loaded the prover.
        import ast
        tree = ast.parse((APP / "compact_dispatch.py").read_text())
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for module in imports:
            self.assertFalse(any(module.startswith(prefix) for prefix in (
                "peano_lab.engine.compact_arith", "peano_lab.engine.tactics",
                "peano_lab.kernel.checker", "peano_lab.kernel.proofs", "peano_lab.library")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
