"""Pure P4 proposal/compiler tests: no tactics, checker, model, or solver."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(APP), str(APP / "native-v7")]

import proof_planner as planner
from finite_difference import (
    StrengtheningCancelled, propose_coupled_strengthening, propose_strengthening,
)
from peano_lab.engine.state import Goal
from peano_lab.kernel.formulas import Eq, Forall, parse_formula, parse_formula_in_context
from peano_lab.kernel.terms import Var, parse_term_in_context


COMMANDS = tuple("intro induction have suffices exists use specialize forall_elim exact apply cases rewrite trans "
                 "refl assumption split left right symm congr exfalso simp ring compact_arith".split())
KERNEL = "1" * 64
LIBRARY = "2" * 64


def context(source="n=n", *, variables=("n",), hypotheses=(), siblings=(), lemmas=(), **remaining):
    goal = Goal(tuple((name, parse_formula_in_context(formula, list(variables)))
                      for name, formula in hypotheses),
                parse_formula_in_context(source, list(variables)), variables)
    caps = planner.CapabilitySnapshot("planner-unit-authority", COMMANDS, tuple(item.name for item in lemmas))
    return planner.PlannerContext(parse_formula("forall n. n=n"), (), (goal,) + tuple(siblings), caps,
        KERNEL, LIBRARY if lemmas else "none", tuple(lemmas), ("ring exceeded its work allowance",),
        {"depth": 32, "tactic_attempts": 64, "imports": 8, **remaining}, {"distinct_objects": 17})


def compile_actions(ctx, *actions):
    return planner.compile_plan(planner.PlanSpec(tuple(actions), "A pure proposal fixture."), ctx)


class PlanCompilerTests(unittest.TestCase):
    def test_generalization_binds_parameters_and_projects_dependent_assumptions(self):
        ctx = context("n+m=m+n", variables=("m", "n"), hypotheses=(("Hm", "m=m"),))
        result = compile_actions(ctx, planner.InductionAction("n", ("m",)))
        statement = result.commands[0].split(":", 1)[1].strip()
        expected = parse_formula_in_context("forall z. z=z -> n+z=z+n", ["m", "n"])
        self.assertEqual(parse_formula_in_context(statement, ["m", "n"]), expected)
        self.assertEqual(result.commands[1:], ("specialize hydra_generalized m",
            "apply hydra_generalized", "exact Hm", "induction n"))
        self.assertEqual(result.starting_goals, ctx.goals)
        self.assertTrue(result.introduces_open_obligations)
        self.assertTrue(all(dict(step)["source"] == "heuristic" for step in result.provenance))
        self.assertTrue(all(dict(step)["kernel_checked"] is False for step in result.provenance))
        with self.assertRaises(planner.PlannerLimit):
            compile_actions(replace(ctx, remaining={"depth": 4, "tactic_attempts": 64}),
                            planner.InductionAction("n", ("m",)))

    def test_generalization_respects_preexisting_and_multiple_binders(self):
        ctx = context("forall q. n+(m+q)=(n+m)+q", variables=("n", "m"))
        result = compile_actions(ctx, planner.GeneralizeAction(("m", "n")))
        generated = parse_formula_in_context(result.commands[0].split(":", 1)[1], ["n", "m"])
        expected = parse_formula("forall x y q. y+(x+q)=(y+x)+q")
        self.assertEqual(generated, expected)
        self.assertEqual(result.commands[1:], ("specialize hydra_generalized m",
                                              "specialize hydra_generalized n", "exact hydra_generalized"))
        for names in (("missing",), ("n", "n")):
            with self.assertRaises(planner.PlannerError):
                compile_actions(ctx, planner.GeneralizeAction(names))

    def test_witness_bindings_are_ast_substitution_not_text_injection(self):
        ctx = context("exists x. x=n+k", variables=("n", "k"))
        result = compile_actions(ctx, planner.WitnessAction(planner.WitnessTemplate(
            "W+N", (("W", "k"), ("N", "n")))))
        term = parse_term_in_context(result.commands[0].partition(" ")[2], ["n", "k"])
        self.assertEqual(term, parse_term_in_context("k+n", ["n", "k"]))
        for template in (planner.WitnessTemplate("n", (("n", "k"),)),
                         planner.WitnessTemplate("missing"),
                         planner.WitnessTemplate("W", (("W", "k; refl"),))):
            with self.assertRaises(planner.PlannerError):
                compile_actions(ctx, planner.WitnessAction(template))

    def test_checked_lemma_metadata_is_explicit_scoped_and_not_an_import(self):
        lemma = planner.LemmaCandidate("fixture_reflexive", Forall(Eq(Var(0), Var(0))),
            "3" * 64, KERNEL, LIBRARY, {"distinct_objects": 2})
        ctx = context(lemmas=(lemma,))
        result = compile_actions(ctx, planner.InstantiateAction(lemma.name, ("n",), "h", "exact"))
        self.assertEqual(result.commands, ("use fixture_reflexive as h", "specialize h n", "exact h"))
        self.assertEqual(dict(result.provenance[0])["certificate_sha256"], lemma.certificate_sha256)
        self.assertEqual(result.library_identity, LIBRARY)
        for action in (planner.InstantiateAction("unselected"),
                       planner.InstantiateAction(lemma.name, ("n", "n")),
                       planner.InstantiateAction(lemma.name, alias="n")):
            with self.assertRaises(planner.PlannerError):
                compile_actions(ctx, action)
        with self.assertRaises(planner.PlannerLimit):
            compile_actions(replace(ctx, remaining={"depth": 32, "tactic_attempts": 64, "imports": 0}),
                            planner.InstantiateAction(lemma.name))
        with self.assertRaises(planner.PlannerError):
            planner.context_record(replace(ctx, library_identity="4" * 64))

    def test_auxiliary_and_routes_emit_no_tacticals_or_external_actions(self):
        ctx = context()
        result = compile_actions(ctx, planner.RouteAction(0, (
            planner.AuxiliaryAction("have", "h", "n=n"),
            planner.StepAction("refl"), planner.StepAction("exact", name="h")), "vampire"))
        self.assertEqual(result.commands, ("have h : n = n", "refl", "exact h"))
        self.assertEqual(result.backend_hints, ((0, "vampire"),))
        self.assertEqual(result.source, "heuristic")
        for action in (planner.RouteAction(1, (planner.StepAction("refl"),)),
                       planner.StepAction("focus", name="h"),
                       planner.StepAction("use", name="unknown"),
                       planner.AuxiliaryAction("have", "h", "n=n; exact h")):
            with self.assertRaises(planner.PlannerError):
                compile_actions(ctx, action)
        with self.assertRaises(planner.PlannerError):
            compile_actions(replace(ctx, capabilities=planner.CapabilitySnapshot("no-ring", ("refl",))),
                            planner.StepAction("ring"))

    def test_full_goal_context_and_identities_are_not_truncated(self):
        sibling = Goal((("Hx", Eq(Var(0), Var(0))),), Eq(Var(0), Var(0)), ("x",))
        ctx = context(siblings=(sibling,))
        record = planner.context_record(ctx)
        self.assertEqual(len(record["goals"]), 2)
        self.assertIn("Hx", record["goals"][1])
        self.assertEqual(record["recent_failures"], list(ctx.failures))
        self.assertEqual(record["certificate_cost"], {"distinct_objects": 17})
        self.assertEqual(record["remaining_budget"]["depth"], 32)
        first = compile_actions(ctx, planner.StepAction("refl"))
        second = compile_actions(replace(ctx, failures=("new failure",)), planner.StepAction("refl"))
        self.assertEqual(first.commands, second.commands)
        self.assertNotEqual(first.context_sha256, second.context_sha256)

    def test_whole_plan_limits_cancellation_and_resource_exceptions(self):
        ctx = context()
        plan = planner.PlanSpec(tuple(planner.StepAction("refl") for _ in range(16)), "Fixture.")
        compiled = planner.compile_plan(plan, ctx)
        self.assertEqual(tuple(map(len, compiled.chunks())), (8, 8))
        self.assertEqual(tuple(map(len, compiled.chunks(3))), (3, 3, 3, 3, 3, 1))
        with self.assertRaises(planner.PlannerLimit):
            compiled.chunks(9)
        with self.assertRaises(planner.PlannerLimit):
            planner.compile_plan(plan, replace(ctx, remaining={"depth": 15, "tactic_attempts": 64}))
        with patch.object(planner, "MAX_PLAN_BYTES", 8):
            with self.assertRaises(planner.PlannerLimit):
                planner.compile_plan(plan, ctx)
        with patch.object(planner, "MAX_AST_NODES", 3):
            with self.assertRaises(planner.PlannerLimit):
                compile_actions(ctx, planner.WitnessAction(planner.WitnessTemplate("n+n")))
        with self.assertRaises(planner.PlannerCancelled):
            planner.compile_plan(plan, ctx, should_stop=lambda: True)
        for error in (MemoryError, TimeoutError):
            def stop():
                raise error("fixture")
            with self.assertRaises(error):
                planner.compile_plan(plan, ctx, should_stop=stop)

    def test_strict_json_and_typed_action_rejections(self):
        ctx = context()
        accepted = planner.decode_plan_document(
            '{"v":1,"plans":[{"reason":"Try reflexivity.","actions":[{"kind":"step","tactic":"refl"}]}]}')
        self.assertEqual(planner.compile_plan(accepted[0], ctx).commands, ("refl",))
        bad_documents = (
            '{"v":1,"v":1,"plans":[]}',
            '{"v":NaN,"plans":[]}',
            '{"v":true,"plans":[]}',
            '{"v":1,"plans":[],"commands":["qed"]}',
            '```json\n{"v":1,"plans":[]}\n```',
        )
        for document in bad_documents:
            with self.subTest(document=document), self.assertRaises(planner.PlannerError):
                planner.decode_plan_document(document)
        for action in (planner.StepAction([]), planner.InductionAction("n", (12,)),
                       planner.StrengthenAction(max_auxiliaries=True),
                       planner.RouteAction(True, (planner.StepAction("refl"),))):
            with self.subTest(action=action), self.assertRaises(planner.PlannerError):
                compile_actions(ctx, action)


class CoupledProposalTests(unittest.TestCase):
    def test_two_auxiliaries_are_derived_and_old_api_is_unchanged(self):
        ctx = context("exists k. n*n*n*n*n=n+30*k")
        goal = ctx.goals[0]
        self.assertIsNone(propose_strengthening(goal, goal.target, goal.context))
        proposal = propose_coupled_strengthening(goal, goal.target, goal.context)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.divisors, (30, 6, 3))
        self.assertEqual(proposal.auxiliary_count, 2)
        self.assertEqual(len(proposal.commands), 8)
        self.assertEqual(proposal.parameter_indices, (0,))
        self.assertEqual(proposal.polynomials[2], (
            ((), 3), ((0,), 7), ((0, 0), 6), ((0, 0, 0), 2)))
        result = compile_actions(ctx, planner.StrengthenAction())
        self.assertEqual(len(result.commands), 10)
        self.assertEqual(tuple(map(len, result.chunks())), (8, 2))
        self.assertTrue(result.introduces_open_obligations)
        self.assertTrue(result.commands[-1].startswith("induction "))
        self.assertLessEqual(result.ast_nodes, 4096)
        self.assertLessEqual(result.analysis_work, planner.MAX_COMPILE_WORK)

    def test_parameter_generalization_and_fresh_projection_names_are_explicit(self):
        ctx = context("exists k. p*(n*n*n*n*n)=p*n+30*k", variables=("n", "p"),
                      hypotheses=(("x", "n=n"), ("hydra_fd_pair_before", "p=p")))
        # The old conservative repeat guard intentionally rejects any existing
        # hydra_fd prefix, so test ordinary local-name collisions separately.
        guarded = ctx.goals[0]
        self.assertIsNone(propose_coupled_strengthening(guarded, guarded.target, guarded.context))
        ctx = context("exists k. p*(n*n*n*n*n)=p*n+30*k", variables=("n", "p"),
                      hypotheses=(("x", "n=n"), ("x1", "p=p")))
        goal = ctx.goals[0]
        proposal = propose_coupled_strengthening(goal, goal.target, goal.context)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.parameter_indices, (0, 1))
        self.assertEqual(proposal.auxiliary_count, 2)
        self.assertEqual(proposal.commands[1:3], ("specialize hydra_fd_pair n", "specialize hydra_fd_pair p"))
        self.assertEqual(proposal.commands[-2], "exists x2")
        self.assertIs(type(proposal.strengthened), Forall)
        self.assertIs(type(proposal.strengthened.body), Forall)
        self.assertIsNone(propose_coupled_strengthening(goal, goal.target, goal.context,
                                                       generalize_parameters=False))

    def test_unsupported_false_or_overlarge_family_declines_and_cancel_propagates(self):
        for source in ("exists k. n*n*n*n*n=n+30*k+1", "exists k. n=2*k",
                       "exists k. n*n=n+2*k"):
            goal = context(source).goals[0]
            self.assertIsNone(propose_coupled_strengthening(goal, goal.target, goal.context))
        goal = context("exists k. n*n*n*n*n=n+30*k").goals[0]
        self.assertIsNone(propose_coupled_strengthening(goal, goal.target, goal.context, max_auxiliaries=1))
        with self.assertRaises(StrengtheningCancelled):
            propose_coupled_strengthening(goal, goal.target, goal.context, should_stop=lambda: True)
        def timeout():
            raise TimeoutError("fixture")
        with self.assertRaises(TimeoutError):
            propose_coupled_strengthening(goal, goal.target, goal.context, should_stop=timeout)

    def test_deterministic_plans_remain_symbolic_proposals(self):
        plans = planner.deterministic_plans(context("exists k. n*n*n=n+6*k"))
        self.assertTrue(plans)
        self.assertTrue(plans[0].commands[0].startswith("suffices hydra_fd_pair"))
        self.assertTrue(all(plan.source == "heuristic" for plan in plans))
        self.assertLessEqual(len(plans), 2)
        self.assertEqual(planner.deterministic_plans(context(), max_proposals=0), ())


if __name__ == "__main__":
    unittest.main()
