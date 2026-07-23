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


class CommandSurfaceTests(unittest.TestCase):
    """Drive the REPL command surface end-to-end through LabSession.run."""

    def test_peano_shows_succ_zero_nesting(self):
        out = strip_ansi(driver.LabSession().run("peano 3"))
        self.assertIn("SUCC (SUCC (SUCC (ZERO)))", out)
        self.assertIn("Church:", out)

    def test_peano_rejects_out_of_range(self):
        session = driver.LabSession()
        for bad in ("peano 25", "peano -1"):
            with self.subTest(cmd=bad):
                self.assertIn(f"Use 0..{driver.MAX_NUMERAL}.", strip_ansi(session.run(bad)))

    def test_lean_snippet_and_alias_emit_code_and_live_link(self):
        session = driver.LabSession()
        for cmd in ("lean s_comb", "lean s-combinator"):
            with self.subTest(cmd=cmd):
                out = strip_ansi(session.run(cmd))
                self.assertIn("theorem s_combinator", out)
                self.assertIn("https://live.lean-lang.org/#code=", out)

    def test_lean_unknown_name_lists_snippets(self):
        out = strip_ansi(driver.LabSession().run("lean nosuch"))
        self.assertIn("No baked snippet named 'nosuch'", out)
        for key in ("add_comm", "modus_ponens", "s_comb"):
            self.assertIn(key, out)

    def test_kb_exact_entry(self):
        self.assertIn("η-conversion", strip_ansi(driver.LabSession().run("kb eta")))

    def test_kb_prefix_fallback(self):
        out = strip_ansi(driver.LabSession().run("kb church"))
        self.assertNotIn("No entry", out)
        self.assertIn("Church", out)

    def test_kb_unknown_topic_errors(self):
        self.assertIn("No entry for 'nosuch'", strip_ansi(driver.LabSession().run("kb nosuch")))

    @staticmethod
    def _current_question(session):
        from lambda_lab.lab.webport import quiz as web_quiz
        qid = session.webstate.get("webquiz_current")
        return web_quiz._Q_BY_ID[qid] if qid else None

    @staticmethod
    def _correct_answer(q):
        if q["type"] == "mc":
            return chr(ord("A") + q["correct"])
        if q["type"] == "tf":
            return "true" if q["answer"] else "false"
        if q["type"] == "completion":
            return q["answers"][0]
        return q.get("answer") or q.get("expected")

    def test_quiz_accepts_the_correct_answer(self):
        session = driver.LabSession()
        session.webstate["webquiz_seed"] = 7   # deterministic queue
        out = strip_ansi(session.run("quiz"))
        self.assertIn("Question 1/", out)
        answer = self._correct_answer(self._current_question(session))
        self.assertIn("Correct", strip_ansi(session.run(answer)))

    def test_quiz_accepts_alpha_variant_of_term_answer(self):
        session = driver.LabSession()
        session.webstate["webquiz_seed"] = 7
        session.run("quiz")
        # advance until an open question whose expected answer is a λ-term
        for _ in range(40):
            q = self._current_question(session)
            if q is None:
                break
            expected = str(q.get("answer") or q.get("expected") or "")
            if q["type"] == "open" and "\\" in expected:
                renamed = expected.replace("x", "w").replace("y", "v")
                out = strip_ansi(session.run(renamed))
                self.assertIn("Correct", out)
                return
            session.run("quiz skip")
        self.skipTest("no open λ-term question reachable in this queue")

    def test_quiz_rejects_wrong_answer_and_shows_canonical(self):
        session = driver.LabSession()
        session.webstate["webquiz_seed"] = 7
        session.run("quiz")
        q = self._current_question(session)
        wrong = "Z" if q["type"] == "mc" else "definitely-wrong-42"
        out = strip_ansi(session.run(wrong))
        self.assertTrue("Incorrect" in out or "Invalid" in out, out[:200])

    def test_quiz_stop_closes(self):
        session = driver.LabSession()
        session.run("quiz")
        self.assertIn("quiz closed", strip_ansi(session.run("quiz stop")))

    def test_equiv_omega_is_inconclusive(self):
        out = strip_ansi(driver.LabSession().run("equiv OMEGA = OMEGA"))
        self.assertIn("Inconclusive", out)

    def test_bare_eq_term_reduces_instead_of_hitting_equiv(self):
        # Regression: an undocumented `cmd_eq = cmd_equiv` alias used to shadow
        # the EQ constant, so `EQ 1 1` errored instead of reducing.
        out = strip_ansi(driver.LabSession().run("EQ 1 1"))
        self.assertNotIn("expected two terms separated by '='", out)
        self.assertIn("TRUE", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
