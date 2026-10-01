"""Small adapter/contract tests. Parsing is not native proof replay."""

from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import sys
import unittest

import sqrt2_power_pilot_instances as instances
from sqrt2_power_exact_pilots import c_approx


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "peano-lab/py"))
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.kernel.terms import Add, Mul, Succ, Zero, parse_term


def term_value(term):
    if type(term) is Zero:
        return 0
    if type(term) is Succ:
        return term_value(term.term) + 1
    if type(term) is Add:
        return term_value(term.left) + term_value(term.right)
    if type(term) is Mul:
        return term_value(term.left) * term_value(term.right)
    raise AssertionError("unexpected non-closed term")


class PilotInstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = instances.build_pilot_instances()
        cls.pilots = {row["id"]: row for row in cls.inventory["pilots"]}

    def test_no_subleaf_or_host_trace_is_claimed_as_a_completed_pilot(self):
        self.assertEqual(self.inventory["completed_pilots"], 0)
        self.assertEqual(self.inventory["completed_parents"], 0)
        for pilot in self.pilots.values():
            self.assertEqual(pilot["fully_elaborated_pilot"], pilot["id"] == "P10")
            self.assertFalse(pilot["closes_pilot"])
            self.assertFalse(pilot["closes_parent"])
            self.assertTrue(pilot["outstanding_bridges"])
            for source in pilot["sources"]:
                self.assertFalse(source["ha_checked"])
                self.assertFalse(source["closes_pilot"])

    def test_fixed_naturals_use_only_portable_terms(self):
        for value in (0, 1, 15, 16, 256, 257, 2 ** 88, 2 ** 88 - 1, 3 ** 111):
            with self.subTest(value=value):
                source = instances.nat_term(value)
                self.assertEqual(term_value(parse_term(source)), value)
                self.assertNotIn("**", source)
                self.assertNotIn("^", source)
        with self.assertRaises(ValueError):
            instances.nat_term(1 << 8192)

    def test_every_immediate_formula_parses_with_no_free_names(self):
        mutation = self.pilots["P09"]["mutation"]
        self.assertLessEqual(Fraction(1, 4), Fraction(*mutation["L0"]))
        self.assertLessEqual(Fraction(*mutation["L0"]), Fraction(1, 2))
        self.assertEqual(mutation["at_L0_one_third_value"], [7, 1])
        for pilot in self.pilots.values():
            self.assertEqual(pilot["fully_elaborated_pilot"], pilot["id"] == "P10")
            for source in pilot["sources"]:
                with self.subTest(id=source["id"]):
                    _, names = parse_formula_with_names(source["formula"])
                    self.assertEqual(names, ())

    def test_p04_contains_a_real_composition_and_nonzero_constant_control(self):
        row = self.pilots["P04"]
        self.assertEqual(row["composition_prefix"], [[1, 1]] + [[2, 1]] * 7)
        self.assertEqual(row["constant_power_rows"][0]["coefficient"], [1, 1])
        self.assertTrue(all(entry["coefficient"] == [0, 1] for entry in row["constant_power_rows"][1:]))
        self.assertNotEqual(row["mutation"]["scaled_constant"], row["mutation"]["expected_scale"])
        self.assertIn("a = 0 ->", row["sources"][0]["formula"])

    def test_p08_keeps_guards_but_reports_the_power_graph_gap(self):
        row = self.pilots["P08"]
        formula = row["sources"][0]["formula"]
        self.assertIn("dp = dm -> bot", formula)
        for denominator in ("dd", "ud", "vd"):
            self.assertIn(denominator, formula)
        self.assertIn("manifest rejection", row["mutation"]["nonzero_guard_removal"])
        self.assertEqual(row["mutation"]["sign_flip_counterexample"]["wrong_sum"], 2)

    def test_p09_exact_coefficients_and_factorial_indexing(self):
        row = self.pilots["P09"]
        expected = {(0, 0): Fraction(-1, 2160), (1, 0): Fraction(1, 240),
                    (2, 0): Fraction(-1, 48), (3, 0): Fraction(0),
                    (3, 1): Fraction(-1, 36), (4, 0): Fraction(1, 48),
                    (5, 0): Fraction(-1, 240), (6, 0): Fraction(1, 2160)}
        found = {(entry["node"], entry["derivative"]): Fraction(*entry["coefficient"])
                 for entry in row["coefficients"]}
        self.assertEqual(found, expected)
        self.assertEqual(row["common_denominator"], 2160)
        self.assertEqual(row["full_clearing_scale"], 5040 * 720 ** 7)
        self.assertEqual(row["exact_functional_value"], [1, 1])
        selected = next(entry for entry in row["coefficients"] if entry["derivative"] == 1)
        self.assertEqual(selected["normalized_monomial_jet"], 7 * 3 ** 6)
        self.assertEqual(row["mutation"]["L0"], [1, 3])
        self.assertEqual(row["mutation"]["at_L0_one_third_value"], [7, 1])
        self.assertFalse(row["mutation"]["equals_one"])

    def test_p10_closed_constants_and_all_binary_carries(self):
        row = self.pilots["P10"]
        self.assertEqual(row["left"] + row["difference"], row["right"])
        self.assertEqual(row["right"], 2 ** 88)
        self.assertFalse(row["mutation"]["exact_inequality_holds"])
        for column in row["binary_addition_columns"]:
            self.assertEqual(column["a"] + column["b"] + column["carry"],
                             column["result"] + 2 * column["next_carry"])
        self.assertTrue(row["sources"][0]["formula"].startswith("exists delta."))

    def test_p12_trace_matches_the_authoritative_finite_sequence(self):
        row = self.pilots["P12"]
        trace = row["trace"]
        self.assertEqual((trace["n"], trace["k"], trace["exp_degree"]), (6, 14, 16))
        self.assertEqual(Fraction(*trace["approximation"]), c_approx(6))
        self.assertTrue(instances.validate_p12_trace(trace))
        numerator, denominator = trace["approximation"]
        self.assertEqual(row["comparison"]["left"], (3 * 2 ** 6 + 4) * denominator)
        self.assertEqual(row["comparison"]["right"], 2 * 2 ** 6 * numerator)
        self.assertGreater(2 * Fraction(numerator, denominator) - 3, Fraction(4, 2 ** 6))
        self.assertGreaterEqual(row["comparison"]["strict_witness"], 0)
        self.assertEqual(row["comparison"]["left"] + row["comparison"]["strict_witness"] + 1,
                         row["comparison"]["right"])

    def test_p12_mutated_trace_is_rejected(self):
        trace = deepcopy(self.pilots["P12"]["trace"])
        trace["rational_steps"][3]["output"][0] += 1
        with self.assertRaisesRegex(ValueError, "differs"):
            instances.validate_p12_trace(trace)
        with self.assertRaises(ValueError):
            next(instances.p12_trace_sources(trace))

    def test_p12_trace_operations_are_exact_and_generated_sources_are_closed(self):
        trace = self.pilots["P12"]["trace"]
        for row in trace["integer_steps"]:
            self.assertEqual(row["inputs"][0] * row["inputs"][1], row["output"])
        for row in trace["rational_steps"]:
            left, right = map(lambda value: Fraction(*value), row["inputs"])
            actual = {"add": lambda: left + right, "mul": lambda: left * right,
                      "div": lambda: left / right}[row["operation"]]()
            self.assertEqual(actual, Fraction(*row["output"]))
        count = 0
        for source in instances.p12_trace_sources(trace):
            _, names = parse_formula_with_names(source["formula"])
            self.assertEqual(names, ())
            count += 1
        self.assertGreater(count, len(trace["integer_steps"]) + len(trace["rational_steps"]))


if __name__ == "__main__":
    unittest.main()
