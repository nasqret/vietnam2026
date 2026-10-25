"""Scheduled P4 native gate; authored completion is not a model/search win.

Run separately under the host's bounded native-process guard. The generated
plan contains the generalization/projection and induction opening; a small
explicit test completion proves its remaining obligations. Nothing runs at
module import. No model, solver, remote call, or proof search is used.
"""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(APP), str(APP / "native-v7")]
FROZEN = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py/peano_lab"

from proof_planner import (
    AuxiliaryAction, CapabilitySnapshot, PlannerContext, PlanSpec,
    StrengthenAction, compile_plan,
)
from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import InvalidProof, TacticError
from peano_lab.engine.trace import TraceLogger
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.ui.prove import (
    ProofSession, SurfaceCapabilities, checked_surface_final, run_surface,
)


THEOREM = "forall p n. exists k. n*n*n+6*p=n+6*k"
INITIAL = ("intro p", "intro n")
MANUAL_COMPLETION = (
    "intro p_base", "exists p_base", "exists 0", "split", "simp", "simp",
    "intro p_step", "specialize IH p_step", "cases IH", "cases IH_witness", "cases IH_witness_witness",
    "exists (x+x1)", "exists (x1+hydra_induction+1)", "split",
    "trans ((hydra_induction*hydra_induction*hydra_induction+6*p_step)+3*(hydra_induction*hydra_induction+hydra_induction)+1)",
    "ring", "rewrite IH_witness_witness_left", "rewrite IH_witness_witness_right", "ring",
    "trans (hydra_induction*hydra_induction+hydra_induction+(2*hydra_induction+2))",
    "ring", "rewrite IH_witness_witness_right", "ring",
)
AUTHORITY = SurfaceCapabilities(label="planner-native-fixture", allowed_commands=MODEL_V1_COMMANDS,
                                allowed_theorems=frozenset())


def owner_for(theorem, session):
    target, names = parse_formula_with_names(theorem)
    return ProofSession(start(target, names), target, names, theorem, False,
                        TraceLogger(session_id=session))


class NativePlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original = {p.name: p.read_bytes() for p in (FROZEN / "kernel").glob("*.py")}
        current = {p.name: p.read_bytes() for p in (APP / "native-v7/peano_lab/kernel").glob("*.py")}
        if not original or original != current:
            raise AssertionError("the planner must use the unchanged original kernel")
        cls.kernel_identity = sha256(json.dumps({"logic": "intuitionistic", "files": {
            name: sha256(content).hexdigest() for name, content in original.items()}},
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        name = "peano_lab.kernel._p4_original_checker"
        spec = importlib.util.spec_from_file_location(name, FROZEN / "kernel/checker.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        cls.original_check = staticmethod(module.check)

    def context(self, owner):
        return PlannerContext(owner.original_target, owner.original_names, owner.state.goals,
            CapabilitySnapshot.from_native(AUTHORITY), self.kernel_identity,
            remaining={"depth": 94, "tactic_attempts": 256})

    def test_generated_parameterized_induction_is_checked_and_fully_replayed(self):
        owner = owner_for(THEOREM, "p4-native-first")
        for command in INITIAL:
            owner = run_surface(owner, command, capabilities=AUTHORITY)
        plan = compile_plan(PlanSpec((StrengthenAction(parameter="n"),),
            "Generate a parameterized divisibility invariant, then open induction."), self.context(owner))
        self.assertEqual(len(plan.commands), 10)
        self.assertEqual(tuple(map(len, plan.chunks())), (8, 2))
        self.assertEqual(plan.starting_goals, owner.state.goals)
        for chunk in plan.chunks():
            for command in chunk:
                owner = run_surface(owner, command, capabilities=AUTHORITY)
        # The planner has not proved anything: base and successor are still
        # open, and both retain the generalized parameter's forall binder.
        self.assertEqual(len(owner.state.goals), 2)
        with self.assertRaises(InvalidProof):
            checked_surface_final(owner.state, owner.original_target)
        for command in MANUAL_COMPLETION:
            owner = run_surface(owner, command, capabilities=AUTHORITY)
        certificate = checked_surface_final(owner.state, owner.original_target)
        self.assertTrue(self.original_check((), certificate, owner.original_target))
        complete = INITIAL + plan.commands + MANUAL_COMPLETION
        replay = run_proof(THEOREM, complete, capabilities=AUTHORITY, request_id="p4-native-independent-replay")
        self.assertEqual(replay.status, "proved", replay.error)
        self.assertTrue(replay.kernel_checked)
        self.assertEqual(replay.goals, ())
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        self.assertEqual(replay.proof_nodes, nodes)
        print(json.dumps({"gate": "parameterized_cubic", "theorem": THEOREM,
            "commands": complete, "generated_plan_steps": len(plan.commands),
            "manual_completion_steps": len(MANUAL_COMPLETION), "whole_script_steps": len(complete),
            "original_kernel_checked": True, "independent_replay_checked": replay.kernel_checked,
            "structural_occurrences": nodes, "distinct_objects": objects,
            "proof_depth": depth, "edges": edges, "reused_references": reused,
            "kernel_identity": self.kernel_identity, "model_calls": 0, "vampire_calls": 0,
            "claim_scope": "generated-plan plus authored native completion; not a search or model win"},
            ensure_ascii=False))
        false = run_proof("forall p n. exists k. n*n*n+6*p=n+6*k+1", complete,
                           capabilities=AUTHORITY, request_id="p4-native-false-target")
        self.assertFalse(false.kernel_checked)
        self.assertNotEqual(false.status, "proved")

    def test_failed_auxiliary_plan_cannot_leak_a_hypothesis_or_skip_a_sibling(self):
        owner = owner_for("0=0 /\\ 1=1", "p4-native-failure-boundary")
        owner = run_surface(owner, "split", capabilities=AUTHORITY)
        sibling = owner.state.goals[1]
        plan = compile_plan(PlanSpec((AuxiliaryAction("have", "bad", "0=1"),),
            "Intentionally false auxiliary statement used only as a rejection fixture."), self.context(owner))
        after = run_surface(owner, plan.commands[0], capabilities=AUTHORITY)
        self.assertEqual(len(after.state.goals), 3)
        self.assertEqual(after.state.goals[-1], sibling)
        self.assertNotIn("bad", dict(after.state.goals[0].context))
        saved_state = after.state
        with self.assertRaises(TacticError):
            run_surface(after, "exact bad", capabilities=AUTHORITY)
        self.assertIs(after.state, saved_state)
        with self.assertRaises(InvalidProof):
            checked_surface_final(after.state, after.original_target)


if __name__ == "__main__":
    unittest.main()
