from __future__ import annotations

import itertools
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import driver
from lambda_lab.lab import church, lc
from lambda_lab.lab.parser import parse


def strip_ansi(text: str) -> str:
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def nf(src: str, steps: int = 5_000):
    result = lc.normalize_checked(driver._parse_term(src), max_steps=steps)
    if not result.complete:
        raise AssertionError(f"did not normalize: {src}")
    return result.term


class AlphaAndSubstitutionTests(unittest.TestCase):
    def test_shadowing_is_not_lost(self):
        self.assertFalse(lc.alpha_eq(parse(r"\x. \y. x"), parse(r"\x. \x. x")))
        self.assertTrue(lc.alpha_eq(parse(r"\x. \x. x"), parse(r"\a. \b. b")))

    def test_capture_avoiding_substitution(self):
        result = nf(r"(\x. \y. x) y")
        self.assertEqual(lc.free_vars(result), {"y"})
        self.assertTrue(lc.alpha_eq(result, parse(r"\z. y")))


class DecoderAndConstantTests(unittest.TestCase):
    def test_shadowed_false_decodes_as_false_not_true(self):
        term = parse(r"\x. \x. x")
        self.assertIs(church.decode_bool_nf(term), False)
        self.assertEqual(church.decode_numeral_nf(term), 0)

    def test_shadowed_fake_one_is_rejected(self):
        self.assertIsNone(church.decode_numeral_nf(parse(r"\f. \f. f f")))

    def test_false_zero_ambiguity_is_explicit(self):
        self.assertIn("0 / FALSE", strip_ansi(driver.LabSession().run("decode FALSE")))

    def test_pow_zero_is_canonical_one(self):
        for base in range(5):
            self.assertEqual(church.decode_numeral_nf(nf(f"POW {base} 0")), 1)

    def test_zero_alias_is_defined(self):
        self.assertTrue(lc.alpha_eq(driver._parse_term("ZERO"), church.church(0)))

    def test_bound_constant_name_is_not_expanded(self):
        self.assertTrue(lc.alpha_eq(driver._parse_term(r"\TRUE. TRUE"), parse(r"\x. x")))

    def test_apostrophe_digit_identifier_survives(self):
        self.assertEqual(driver._parse_term("x'2"), lc.Var("x'2"))


class ReductionStatusTests(unittest.TestCase):
    def test_bare_application_is_accepted(self):
        out = strip_ansi(driver.LabSession().run("x y"))
        self.assertIn("already in β-normal form", out)

    def test_divergence_is_not_called_normal_form(self):
        out = strip_ansi(driver.LabSession().run("nf OMEGA"))
        self.assertIn("Reduction limit reached", out)
        self.assertIn("not claimed to be a normal form", out)

    def test_dynamic_ast_growth_is_bounded(self):
        out = strip_ansi(driver.LabSession().run("nf POW 24 24"))
        self.assertIn("AST size limit", out)
        self.assertIn("not claimed to be a normal form", out)

    def test_exact_trace_limit_is_complete(self):
        src = "z"
        for _ in range(driver.MAX_TRACE):
            src = rf"(\x. x) ({src})"
        out = strip_ansi(driver.LabSession().run("reduce " + src))
        self.assertIn(f"β-normal form reached in {driver.MAX_TRACE} step", out)

    def test_whnf_differs_from_nf(self):
        term = driver._parse_term(r"\x. (\y. y) z")
        whnf = lc.whnf_checked(term, max_steps=10)
        full = lc.normalize_checked(term, max_steps=10)
        self.assertEqual(whnf.steps, 0)
        self.assertEqual(full.steps, 1)
        self.assertFalse(lc.alpha_eq(whnf.term, full.term))

    def test_alpha_and_beta_equivalence_are_separate(self):
        session = driver.LabSession()
        self.assertIn("not alpha-equivalent", strip_ansi(session.run("alpha SUCC 2 = 3")))
        self.assertIn("equal β-normal forms", strip_ansi(session.run("equiv SUCC 2 = 3")))


class ChurchPropertyTests(unittest.TestCase):
    def decode_bool(self, src: str) -> bool:
        value = church.decode_bool_nf(nf(src))
        self.assertIsNotNone(value)
        return bool(value)

    def decode_num(self, src: str) -> int:
        value = church.decode_numeral_nf(nf(src))
        self.assertIsNotNone(value)
        return int(value)

    def test_boolean_truth_tables(self):
        names = {True: "TRUE", False: "FALSE"}
        binary = {
            "AND": lambda p, q: p and q,
            "OR": lambda p, q: p or q,
            "NAND": lambda p, q: not (p and q),
            "NOR": lambda p, q: not (p or q),
            "XOR": lambda p, q: p != q,
            "XNOR": lambda p, q: p == q,
            "IFF": lambda p, q: p == q,
            "IMPLIES": lambda p, q: (not p) or q,
        }
        for op, expected in binary.items():
            for p, q in itertools.product((False, True), repeat=2):
                with self.subTest(op=op, p=p, q=q):
                    self.assertEqual(self.decode_bool(f"{op} {names[p]} {names[q]}"), expected(p, q))
        for p in (False, True):
            self.assertEqual(self.decode_bool(f"NOT {names[p]}"), not p)

    def test_small_arithmetic_grid(self):
        for m, n in itertools.product(range(5), repeat=2):
            self.assertEqual(self.decode_num(f"PLUS {m} {n}"), m + n)
            self.assertEqual(self.decode_num(f"MULT {m} {n}"), m * n)
            self.assertEqual(self.decode_num(f"SUB {m} {n}"), max(0, m - n))
            self.assertEqual(self.decode_bool(f"LEQ {m} {n}"), m <= n)
            self.assertEqual(self.decode_bool(f"EQ {m} {n}"), m == n)
        for n in range(5):
            self.assertEqual(self.decode_num(f"PRED {n}"), max(0, n - 1))
            self.assertEqual(self.decode_num(f"SUCC {n}"), n + 1)
            self.assertEqual(self.decode_bool(f"ISZERO {n}"), n == 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
