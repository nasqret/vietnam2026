"""Dedicated-process integration of real catalogue reuse and native replay."""
from pathlib import Path
import sys
import unittest
from dataclasses import replace

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
import experimental_runtime as experimental
experimental.activate_native()
from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.ui.prove import SurfaceCapabilities
from hybrid_search import HybridLimits, search
from lemma_imports import ImportBudget
from worker import validate_request


def authority(theorem):
    return experimental.authority(theorem,{"engine":"sharing-v1","lemmas":True},
                                  MODEL_V1_COMMANDS,SurfaceCapabilities)[0]


class CertifiedSearchTests(unittest.TestCase):
    def test_three_statement_only_searches_reuse_actual_checked_certificates(self):
        examples = (
            "forall a b. (a+b=b+a) /\\ (a+0=a)",
            "forall a b. (a*b=b*a) /\\ (a*0=0)",
            "forall n. (exists k. n+n=2*k) /\\ (n=n)",
        )
        for theorem in examples:
            with self.subTest(theorem=theorem):
                caps = authority(theorem)
                result = search(theorem,capabilities=caps,limits=HybridLimits(
                    max_depth=32,max_states=128,max_tactic_attempts=256,max_expansions=32,
                    max_model_calls=0,max_vampire_calls=0,wall_seconds=12))
                self.assertEqual(result["status"],"proof",result["diagnostics"])
                self.assertTrue(result["replay"]["kernel_checked"])
                imports = [row for row in result["provenance"] if row["command"].startswith("use ")]
                self.assertGreater(len(imports),0,result["commands"])
                self.assertLessEqual(len(imports),8)
                self.assertTrue(all(row["evidence"]["strategy"] == "checked_lemma_retrieval" for row in imports))
                ledger = result["lemma_library"]["imports"]
                self.assertEqual(ledger["phases"]["independent_replay"],len(imports))
                self.assertLessEqual(ledger["attempts"],32)
                self.assertTrue(all(len(row["candidates"]) <= 4 for row in result["lemma_library"]["retrievals"]))
                self.assertEqual(result["model_calls"],0)
                self.assertEqual(result["vampire_calls"],0)

    def test_resolver_is_target_bound_and_cannot_add_disallowed_theorems(self):
        theorem = "forall a b. a+b=b+a"
        caps = authority(theorem)
        self.assertNotIn("add_comm",caps.allowed_theorems)
        with self.assertRaises(ValueError):
            replace(caps,allowed_theorems=frozenset({"add_comm"}))
        with self.assertRaises(ValueError):
            replace(caps,checked_library=None)
        result = run_proof("0=1",("use zero_add",),capabilities=caps)
        self.assertFalse(result.kernel_checked)
        self.assertIn("original target changed",str(result.error))

    def test_valid_import_cannot_prove_a_false_target(self):
        theorem = "0=1"
        caps = authority(theorem)
        result = run_proof(theorem,("use zero_add", "exact zero_add"),capabilities=caps)
        self.assertFalse(result.kernel_checked)
        self.assertNotEqual(result.status,"proved")
        self.assertEqual(caps.import_budget.accepted,1)

    def test_real_import_ledger_includes_replay_and_stops_at_32(self):
        budget = ImportBudget()
        for _ in range(24):
            budget.run("fixture",lambda: True)
        with budget.phase("independent_replay"):
            for _ in range(8):
                budget.run("fixture",lambda: True)
        executed = []
        with self.assertRaises(ValueError):
            budget.run("fixture",lambda: executed.append(True))
        self.assertEqual(executed,[])
        self.assertEqual(budget.report()["phases"],{"search":24,"independent_replay":8,"manual":0})

    def test_original_transport_contract_and_explicit_unavailability(self):
        original = {"theorem":"0=0","max_model_calls":8,"beam_width":1,"search_mode":"model"}
        self.assertNotIn("experimental",validate_request("search",original))
        with self.assertRaisesRegex(ValueError,"preserved model provider"):
            validate_request("search",{**original,"experimental":{"lemmas":True}})
        with self.assertRaisesRegex(ValueError,"eight checked imports"):
            validate_request("replay",{"theorem":"0=0","tactics":["use zero_add"]*9,
                                       "experimental":{"lemmas":True}})


if __name__ == "__main__":
    unittest.main(verbosity=2)
