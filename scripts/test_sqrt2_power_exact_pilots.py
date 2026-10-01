"""Regression tests for calibration code, not HA evidence or analytic proofs."""

from fractions import Fraction
from math import factorial, isqrt
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sqrt2_power_exact_pilots as pilots


class ExactPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = pilots.run_calibration()

    def test_report_is_explicitly_non_proof_evidence(self):
        self.assertEqual(self.report["authority"], "exact_arithmetic_calibration_only")
        self.assertFalse(self.report["ha_evidence"])
        self.assertFalse(self.report["tail_estimates_proved"])
        self.assertFalse(self.report["universal_claims_proved"])
        self.assertEqual(self.report["admitted_theorems"], 0)
        self.assertFalse(self.report["approximations"]["analytic_accuracy_proved"])
        self.assertFalse(self.report["approximations"]["certificate_soundness_proved"])

    def test_capprox_matches_root_contract_with_independent_power_sum(self):
        for n in (0, 1, 4, 8, 16):
            with self.subTest(n=n):
                k = n + 8
                s = Fraction(isqrt(2 * 2 ** (2 * k)), 2 ** k)
                log2 = sum((Fraction(2, (2 * j + 1) * 3 ** (2 * j + 1))
                            for j in range(k)), Fraction(0))
                t = log2 / s
                expected = sum((t ** j / factorial(j) for j in range(k + 3)), Fraction(0))
                self.assertIsInstance(pilots.c_approx(n), Fraction)
                self.assertEqual(pilots.c_approx(n), expected)
                # At finite precision this is not the interchangeable formula
                # exp(s*Log2Partial/2): the dyadic s does not square to 2.
                self.assertNotEqual(t, s * log2 / 2)

    def test_precision_and_domain_guards(self):
        for n in (-1, 17, True, Fraction(1, 2)):
            with self.subTest(n=n), self.assertRaises(ValueError):
                pilots.c_approx(n)
        for b in (0, -1):
            with self.subTest(b=b), self.assertRaises(ValueError):
                pilots.irr_cert_holds(1, b, 4)
        with self.assertRaises(ValueError):
            pilots.first_certificate(1, 1, max_precision=17)
        with self.assertRaises(ValueError):
            pilots.confluent_case(4, 0)
        with self.assertRaises(ValueError):
            pilots.confluent_case(1, 7)

    def test_certificate_boundary_is_strict(self):
        n = 4
        u = pilots.c_approx(n)
        radius = Fraction(2, 2 ** n)
        for candidate in (u, u - radius, u + radius):
            with self.subTest(candidate=candidate):
                self.assertFalse(pilots.irr_cert_holds(candidate.numerator, candidate.denominator, n))
        for candidate in (u - 2 * radius, u + 2 * radius):
            with self.subTest(candidate=candidate):
                self.assertTrue(pilots.irr_cert_holds(candidate.numerator, candidate.denominator, n))

    def test_bounded_search_can_return_none(self):
        self.assertIsNone(pilots.first_certificate(3, 2, max_precision=0))

    def test_integer_cross_multiplication_matches_ird10(self):
        for a, b in pilots.CERTIFICATE_CASES:
            for n in (0, 4, 16):
                with self.subTest(a=a, b=b, n=n):
                    u = pilots.c_approx(n)
                    e = 2 ** n
                    # Deliberately noncanonical signed pairs represent a and u.
                    ap, am = max(a, 0) + 7, max(-a, 0) + 7
                    up, um, ud = u.numerator + 11, 11, u.denominator
                    left = (b * um + ap * ud) * e
                    right = (b * up + am * ud) * e
                    encoded = left + 2 * b * ud < right or right + 2 * b * ud < left
                    self.assertEqual(encoded, pilots.irr_cert_holds(a, b, n))
                    self.assertEqual(encoded, pilots.irr_cert_holds(3 * a, 3 * b, n))

    def test_representative_certificates_are_bounded_and_minimal(self):
        rows = self.report["approximations"]["certificates"]
        self.assertEqual(len(rows), 12)
        self.assertEqual([(row["a"], row["b"]) for row in rows], list(pilots.CERTIFICATE_CASES))
        for row in rows:
            a, b, n = row["a"], row["b"], row["precision"]
            with self.subTest(a=a, b=b):
                self.assertLessEqual(n, 16)
                self.assertTrue(pilots.irr_cert_holds(a, b, n))
                self.assertTrue(all(not pilots.irr_cert_holds(a, b, earlier) for earlier in range(n)))

    def test_confluent_identity_counts_and_factorial_indexing(self):
        self.assertEqual(self.report["confluent"], dict(
            configurations=21, monomial_identities=441, selected_coefficients=21,
            factorial_indexing=21, selected_polynomial_functionals=21,
            vanishing_lower_jets=294, coefficient_bounds=315,
            denominator_scalings=315, homogeneous_sanity_checks=63))

    def test_selected_coefficient_at_both_spacing_endpoints(self):
        for spacing in (Fraction(1, 4), Fraction(1, 2)):
            for r in range(1, 4):
                for selected in range(7):
                    with self.subTest(spacing=spacing, r=r, selected=selected):
                        nodes, _, coefficients = pilots.confluent_case(r, selected, spacing)
                        product = Fraction(1)
                        for h, node in enumerate(nodes):
                            if h != selected:
                                product *= (nodes[selected] - node) ** r
                        self.assertEqual(coefficients[selected, r] * product, 1)
                        self.assertLessEqual(abs(product), 12 ** r)
                        self.assertTrue(all(abs(c) <= 2 ** (21 * r) for c in coefficients.values()))

    def test_symbolic_constants_do_not_allocate_an_auxiliary_matrix(self):
        self.assertEqual(self.report["parameter_bounds"], dict(
            symbolic_exponent_components=5, coarse_constant_checks=3,
            parameter_cases=4, small_reduction_cases=6, factorial_cases=3,
            auxiliary_matrices_allocated=0))
        self.assertEqual(pilots.exponent_ledger()["2"], (2, 33, 0, 2))
        self.assertEqual(pilots.exponent_ledger()["H"], (0, 24, 0, 0))

    def test_small_quadratic_moment_identity_counts(self):
        self.assertEqual(self.report["quadratic_moments"], dict(
            q_values=[2, 3], moment_identities=26,
            nonzero_gap_norms=42, nonvanishing_examples=4))

    def test_approximation_examples_are_finite_only(self):
        report = self.report["approximations"]
        self.assertEqual(report["precision_count"], 17)
        self.assertEqual(report["integer_sqrt_brackets"], 17)
        self.assertEqual(report["finite_coherence_checks"], 136)
        self.assertEqual(report["finite_enclosure_comparisons"], 2)


if __name__ == "__main__":
    unittest.main()
