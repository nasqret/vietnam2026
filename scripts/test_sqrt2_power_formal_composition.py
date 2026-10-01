"""Source-only finite-composition tests; no native proof worker on import/run."""

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import unittest
from unittest.mock import patch

import sqrt2_power_formal_composition as composition


class FormalCompositionSourceTests(unittest.TestCase):
    def test_full_trace_has_every_power_coefficient_not_just_a0(self):
        rows = composition.trace_rows()
        ids = {identifier for identifier, _ in rows}
        self.assertEqual(len(rows), 106)
        self.assertEqual(len(ids), len(rows))
        self.assertEqual(len(composition.variable_names()), 106)
        for k in range(1, 8):
            for d in range(8):
                self.assertIn(f"power-{k}-{d}", ids)
        for d in range(8):
            self.assertIn(f"composition-{d}", ids)
        self.assertIn("factorial-base", ids)
        self.assertIn("positive-denominator", ids)

    def test_concrete_trace_matches_independent_rational_composition(self):
        values = composition.concrete_trace()
        inner = [Fraction(0), Fraction(2), Fraction(0), Fraction(2, 3),
                 Fraction(0), Fraction(2, 5), Fraction(0), Fraction(2, 7)]
        powers = [[Fraction(int(d == 0)) for d in range(8)]]
        for k in range(1, 8):
            powers.append([sum((inner[i] * powers[k - 1][d - i] for i in range(d + 1)), Fraction(0))
                           for d in range(8)])
        for k in range(8):
            for d in range(8):
                self.assertEqual(Fraction(values[f"p{k}_{d}"], values[f"q{k}"]), powers[k][d])
        for d in range(8):
            expected = sum((powers[k][d] / values[f"f{k}"] for k in range(8)), Fraction(0))
            self.assertEqual(Fraction(values[f"c{d}"], values["D"]), expected)
            self.assertEqual(expected, 1 if d == 0 else 2)

    def test_every_ground_trace_relation_and_conclusion_is_present_and_true(self):
        values = composition.concrete_trace()
        for identifier, tree in composition.trace_rows():
            with self.subTest(row=identifier):
                self.assertTrue(composition.evaluate(tree, values))
        ground = composition.trees()["ground_instance"]
        self.assertTrue(composition.evaluate(ground, {}))
        self.assertGreater(len(composition.source(ground)), 10000)

    def test_source_constructor_is_fixed_signature_and_hygienic(self):
        encoded = composition.encode(composition.trees()["trace_soundness"])
        for _ in range(106):
            self.assertEqual(encoded[0], "forall")
            encoded = encoded[1]
        self.assertEqual(encoded[0], "imp")
        with self.assertRaises(ValueError):
            composition.encode(composition.eq(composition.v("not_bound"), composition.n(0)))
        with self.assertRaises(ValueError):
            composition.encode(("forall", "x", ("forall", "x", composition.eq(composition.v("x"), composition.v("x")))))
        with self.assertRaises(ValueError):
            composition.encode(("mul", composition.n(1)))

    def test_nonzero_constant_and_wrong_factorial_have_genuine_hostile_traces(self):
        examples = composition.hostile_examples()
        for example in examples[:2]:
            self.assertTrue(example["all_mutated_trace_relations_hold"])
            self.assertFalse(example["conclusion_holds"])
        self.assertIn("factorial-3", examples[2]["failed_rows"])
        self.assertIn("weight-3", examples[2]["failed_rows"])

    def test_changed_nonconstant_coefficient_is_not_silently_ignored(self):
        values = deepcopy(composition.concrete_trace())
        values["p4_7"] += 1
        failures = [name for name, tree in composition.trace_rows() if not composition.evaluate(tree, values)]
        self.assertIn("power-4-7", failures)
        self.assertIn("composition-7", failures)

    def test_hashes_cover_the_actual_full_formula_and_all_106_witnesses(self):
        rows = composition.contracts()
        self.assertEqual({row["target_kind"] for row in rows}, {"ground_instance", "trace_soundness"})
        self.assertNotEqual(rows[0]["statement_ast_sha256"], rows[1]["statement_ast_sha256"])
        for row in rows:
            self.assertEqual(row["source_sha256"], sha256(row["source"].encode()).hexdigest())
            self.assertEqual(row["statement_ast_sha256"], sha256(composition.canonical(row["statement_ast"])).hexdigest())
            self.assertFalse(row["original_HA_checked"])
            self.assertFalse(row["closes_P04"])
            self.assertEqual(row["trace_witnesses"], 106)
            self.assertEqual(len(row["existing_premise_allowlist"]), 15)

    def test_existing_basis_is_exact_and_dependency_closed(self):
        rows = composition.premise_allowlist()
        names = {row["name"] for row in rows}
        self.assertEqual(names, set(composition.FROZEN_BASIS_LITERALS))
        self.assertEqual(len(names), 15)
        for row in rows:
            self.assertTrue(set(row["dependencies"]) <= names)
            self.assertEqual(row["source_file_sha256"], composition.BASIS_SOURCE_SHA256)
        self.assertEqual(set(composition.SOUNDNESS_DEPENDENCY_CLOSURE), {"mul_one", "mul_zero_left", "zero_add"})

    def test_future_variable_degree_claim_is_explicitly_unproved(self):
        future = composition.future_invariant()
        self.assertIsNone(future["kernel_certificate"])
        self.assertEqual(future["status"], "unproved_variable_degree_specification")

    def test_independently_checked_finite_low_degree_invariant(self):
        values = composition.concrete_trace()
        checked = 0
        for k in range(1, 8):
            for d in range(k):
                self.assertEqual(values[f"p{k}_{d}"], 0)
                checked += 1
        self.assertEqual(checked, 28)
        self.assertIsNone(composition.future_invariant()["kernel_certificate"])

    def test_frozen_target_rejects_changed_nonconstant_inner_coefficient(self):
        with patch.object(composition, "INNER", (0, 210, 0, 71, 0, 42, 0, 30)):
            with self.assertRaisesRegex(ValueError, "source-frozen composition target changed"):
                composition.contracts()

    def test_frozen_native_dag_dependency_is_only_a_source_pin(self):
        path = composition.ROOT / "scripts/sqrt2_power_binary_dag.py"
        self.assertEqual(sha256(path.read_bytes()).hexdigest(), composition.BINARY_DAG_SOURCE_SHA256)
        self.assertNotIn("sqrt2_power_binary_dag", composition.__dict__)
        self.assertFalse(composition.summary()["original_HA_checked"])

    def test_flat_collector_preserves_exact_ground_shape_and_hyp_order(self):
        tree = composition.trees()["ground_instance"]
        layout = composition.flat_collector_layout(tree)
        count = len(layout.leaves)
        refs = tuple(("hyp", count - 1 - i) for i in range(count))
        body = composition.materialize_collector(layout.body, refs,
                    lambda left, right: ("and_intro", left, right))
        context = tuple(reversed(layout.leaves))
        def interpret(proof):
            if proof[0] == "hyp":
                return context[proof[1]]
            return ("and", interpret(proof[1]), interpret(proof[2]))
        self.assertEqual(interpret(body), tree)
        self.assertEqual(layout.leaf_occurrences, 107)
        self.assertLessEqual(count, 107)
        self.assertEqual(composition.encode(interpret(body)), composition.encode(tree))

    def test_flat_collector_reuses_dependencies_but_not_target_occurrences(self):
        a = composition.eq(composition.n(0), composition.n(0))
        b = composition.eq(composition.n(1), composition.n(1))
        tree = ("and", ("and", a, b), a)
        layout = composition.flat_collector_layout(tree)
        self.assertEqual(layout.leaves, (a, b))
        self.assertEqual(layout.leaf_occurrences, 3)
        body = composition.materialize_collector(layout.body,
                    (("hyp", 1), ("hyp", 0)), lambda l, r: ("and_intro", l, r))
        self.assertEqual(body, ("and_intro", ("and_intro", ("hyp", 1), ("hyp", 0)), ("hyp", 1)))
        with self.assertRaises(ValueError):
            composition.materialize_collector(("leaf", 2), (a, b), tuple)
        with self.assertRaises(ValueError):
            composition.materialize_collector(("leaf", -1), (a, b), tuple)

    def test_flat_collector_diagnosis_is_not_a_measured_proof_size(self):
        diagnosis = composition.conjunction_source_diagnosis()
        self.assertEqual(diagnosis["original_internal_conjunction_targets"], 106)
        self.assertEqual(diagnosis["flat_collector_targets"], 1)
        self.assertEqual(diagnosis["removed_intermediate_target_ast_bytes"], 1598173)
        self.assertEqual(diagnosis["ground_target_ast_bytes"], 272544)
        self.assertIsNone(diagnosis["measured_certificate_size_reduction"])
        self.assertIsNone(diagnosis["full_ground_certificate_fits_budget"])


if __name__ == "__main__":
    unittest.main()
