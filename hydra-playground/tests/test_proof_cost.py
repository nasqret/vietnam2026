"""Pure constructed-object checks: no tactics, proof search or kernel checks."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(ROOT / "hydra-playground"), str(SOURCE / "peano-lab/py")]

from proof_cost import ProofCostLimits, measure_proof
from peano_lab.kernel import proofs as p
from peano_lab.kernel.formulas import Bot, Eq
from peano_lab.kernel.terms import Succ, Zero
from peano_lab.engine.proof_reduction import LocalHave, LocalSuffices
from peano_lab.engine.state import Hole, proof_identity_metrics, proof_metrics


class ProofCostTests(unittest.TestCase):
    def test_shared_graph_matches_frozen_count_meanings(self):
        leaf = p.Hyp(0)
        pair = p.AndIntro(leaf, leaf)
        root = p.AndIntro(pair, pair)
        result = measure_proof(root, stage="partial")
        self.assertEqual(result["status"], "complete")
        self.assertEqual((result["distinct_objects"], result["structural_occurrences"], result["depth"]),
                         (3, 7, 3))
        self.assertEqual((result["structural_occurrences"], result["depth"]), proof_metrics(root))
        self.assertEqual((result["distinct_objects"], result["proof_edges"], result["reused_references"]),
                         proof_identity_metrics(root))

    def test_equal_but_distinct_objects_are_not_interned(self):
        result = measure_proof(p.AndIntro(p.Hyp(0), p.Hyp(0)), stage="partial")
        self.assertEqual(result["distinct_objects"], 3)
        self.assertEqual(result["reused_references"], 0)

    def test_depth_includes_a_deeper_path_to_an_already_seen_child(self):
        leaf = p.Hyp(0)
        shared = p.AndIntro(leaf, leaf)
        root = p.AndIntro(shared, p.ImpIntro(shared))
        result = measure_proof(root, stage="final")
        self.assertEqual(result["depth"], 4)
        self.assertEqual(result["structural_occurrences"], 8)

    def test_term_formula_payloads_are_not_counted_as_proof_objects(self):
        term = Zero()
        for _ in range(1000):
            term = Succ(term)
        result = measure_proof(p.EqRefl(term), stage="final")
        self.assertEqual((result["distinct_objects"], result["structural_occurrences"], result["depth"]),
                         (1, 1, 1))
        self.assertIn("excludes term/formula payloads", result["counts_scope"])

    def test_partial_and_final_are_independent_snapshots_not_a_prediction(self):
        equation = Eq(Zero(), Zero())
        lemma, hyp = p.EqRefl(Zero()), p.Hyp(0)
        partial = LocalHave(equation, lemma, p.EqTrans(hyp, hyp))
        separately_supplied_final = p.EqTrans(lemma, lemma)
        before = measure_proof(partial, stage="partial")
        after = measure_proof(separately_supplied_final, stage="final")
        self.assertEqual((before["stage"], after["stage"]), ("partial", "final"))
        self.assertEqual((before["distinct_objects"], after["distinct_objects"]), (4, 2))
        self.assertTrue(before["contains_local_schedulers"])
        self.assertFalse(after["contains_local_schedulers"])
        self.assertFalse(before["normalization_performed"])
        self.assertFalse(after["proof_check_performed"])

    def test_final_label_cannot_hide_engine_nodes(self):
        equation, leaf = Eq(Zero(), Zero()), p.Hyp(0)
        for root in (Hole(1), LocalHave(equation, leaf, leaf), LocalSuffices(equation, leaf, leaf)):
            with self.subTest(root=type(root).__name__):
                with self.assertRaises(ValueError):
                    measure_proof(root, stage="final")

    def test_cut_is_counted_without_erasure_or_opening_hypotheses(self):
        equation, leaf = Eq(Zero(), Zero()), p.Hyp(0)
        root = p.Cut(equation, equation, leaf, p.AndIntro(leaf, leaf))
        result = measure_proof(root, stage="final")
        self.assertEqual(result["distinct_objects"], 3)
        self.assertEqual(result["structural_occurrences"], 5)
        self.assertFalse(result["contains_local_schedulers"])

    def test_counting_a_classical_node_does_not_claim_constructive_validation(self):
        result = measure_proof(p.DNE(Bot()), stage="final")
        self.assertEqual(result["distinct_objects"], 1)
        self.assertFalse(result["proof_check_performed"])

    def test_exponentially_unfolded_graph_saturates_without_enumeration(self):
        root = p.Hyp(0)
        for _ in range(20):
            root = p.AndIntro(root, root)
        result = measure_proof(root, stage="partial", limits=ProofCostLimits(max_occurrences=10))
        self.assertEqual(result["status"], "limited")
        self.assertEqual(result["distinct_objects"], 21)
        self.assertEqual(result["depth"], 21)
        self.assertIsNone(result["structural_occurrences"])
        self.assertEqual(result["lower_bounds"]["structural_occurrences"], 11)
        self.assertFalse(result["exact"]["structural_occurrences"])
        self.assertLess(result["work_units"], 100)

    def test_object_and_depth_stops_do_not_report_partial_totals_as_exact(self):
        root = p.ImpIntro(p.ImpIntro(p.Hyp(0)))
        for limits, reason in ((ProofCostLimits(max_objects=1), "objects"),
                               (ProofCostLimits(max_depth=1), "depth"),
                               (ProofCostLimits(max_work=1), "work")):
            with self.subTest(reason=reason):
                result = measure_proof(root, stage="partial", limits=limits)
                self.assertEqual(result["reason"], reason)
                self.assertIsNone(result["distinct_objects"])
                self.assertIsNone(result["structural_occurrences"])
                self.assertIsNone(result["depth"])
                self.assertFalse(any(result["exact"].values()))

    def test_cycle_and_bad_field_shape_fail_without_recursion(self):
        cycle = p.EqSym(p.Hyp(0))
        object.__setattr__(cycle, "proof", cycle)
        self.assertEqual(measure_proof(cycle, stage="partial")["reason"], "cycle")
        malformed = p.EqRefl(p.Hyp(0))
        result = measure_proof(malformed, stage="partial")
        self.assertEqual(result["reason"], "proof_field_shape")
        self.assertIsNone(result["distinct_objects"])

    def test_unrecognized_proof_constructor_is_not_silently_a_leaf(self):
        class Unknown(p.Proof):
            pass
        result = measure_proof(Unknown(), stage="partial")
        self.assertEqual(result["status"], "unsupported")
        self.assertIsNone(result["distinct_objects"])

    def test_cancellation_is_polled_and_metrics_remain_unknown(self):
        root = p.Hyp(0)
        for _ in range(100):
            root = p.ImpIntro(root)
        polls = []

        def stop():
            polls.append(True)
            return len(polls) == 2

        result = measure_proof(root, stage="partial", should_stop=stop)
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(result["work_units"], 64)
        self.assertIsNone(result["contains_holes"])
        self.assertIsNone(result["distinct_objects"])

    def test_configuration_is_explicit_and_finitely_bounded(self):
        for options in ({"max_objects": True}, {"max_work": 0}, {"max_depth": 257},
                        {"max_occurrences": 500_001}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                ProofCostLimits(**options)
        with self.assertRaises(TypeError):
            measure_proof(p.Hyp(0))
        with self.assertRaises(ValueError):
            measure_proof(p.Hyp(0), stage="verified")


if __name__ == "__main__":
    unittest.main(verbosity=2)
