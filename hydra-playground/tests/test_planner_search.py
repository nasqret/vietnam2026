"""Real statement-only planning and failed-plan obligation preservation."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
import experimental_runtime as experimental
experimental.activate_native()
from peano_lab.batch import MODEL_V1_COMMANDS
from peano_lab.ui.prove import SurfaceCapabilities
from hybrid_search import HybridLimits,search
from proof_planner import AuxiliaryAction,PlanSpec,StepAction,compile_plan

CAPS = SurfaceCapabilities(label="hydra-sharing-native-v1",allowed_commands=MODEL_V1_COMMANDS,
                           allowed_theorems=frozenset())
LIMITS = HybridLimits(max_depth=64,max_states=1024,max_tactic_attempts=6000,max_expansions=384,
    max_frontier=128,candidates_per_state=48,max_macro_steps=8,closure_steps=16,
    max_model_calls=0,max_vampire_calls=0,wall_seconds=35)


class PlannerSearchTests(unittest.TestCase):
    def test_generated_strengthening_is_used_by_statement_only_search_and_replayed(self):
        result = search("forall n. exists k. n*n*n=n+6*k",capabilities=CAPS,limits=LIMITS,
            planner_enabled=True,planner_kernel_identity=experimental.NATIVE_MANIFEST_SHA256)
        self.assertEqual(result["status"],"proof",result["diagnostics"])
        self.assertTrue(result["replay"]["kernel_checked"])
        planning = result["structured_planning"]
        self.assertLessEqual(planning["requests"],4)
        self.assertLessEqual(planning["plans_generated"],2*planning["requests"])
        winning = [row for row in result["provenance"]
                   if row.get("evidence",{}).get("strategy")=="structured_plan"]
        self.assertTrue(winning,result["commands"])
        self.assertTrue(any(row["command"].startswith("suffices ") for row in winning),winning)
        self.assertTrue(all("planner_action" in row for row in winning))
        self.assertEqual(result["model_calls"],0)
        self.assertEqual(result["vampire_calls"],0)

    def test_failed_auxiliary_plan_never_closes_false_original_or_drops_its_obligation(self):
        def impossible(context,**_):
            try:
                return (compile_plan(PlanSpec((AuxiliaryAction("have","bogus","0=1"),
                    StepAction("refl")),"Adversarial auxiliary obligation fixture."),context),)
            except ValueError:
                return ()
        with patch("proof_planner.deterministic_plans",impossible):
            result = search("forall n. n=S n",capabilities=CAPS,
                limits=replace(LIMITS,max_tactic_attempts=128,max_states=64,max_expansions=16,
                               max_macro_steps=1,wall_seconds=8),
                planner_enabled=True,planner_kernel_identity=experimental.NATIVE_MANIFEST_SHA256)
        self.assertNotEqual(result["status"],"proof")
        self.assertIsNone(result["replay"])
        plans = result["structured_planning"]["plans"]
        self.assertTrue(plans,result["diagnostics"])
        self.assertTrue(any(row["status"]=="stopped_on_native_rejection_or_limit" for row in plans))
        self.assertTrue(any("bogus" in row.get("command","") for row in result["branches"]))
        self.assertFalse(any(row.get("status")=="proved" for row in result["branches"]))


if __name__=="__main__":
    unittest.main(verbosity=2)
