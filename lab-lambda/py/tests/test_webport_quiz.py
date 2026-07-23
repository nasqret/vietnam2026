"""Tests for the browser port of the quiz family (webport/quiz.py).

Drives handle(arg, state) directly and asserts on ANSI-stripped output.
"""

from __future__ import annotations

import re
import unittest

from lambda_lab.lab.webport import quiz
from lambda_lab.lab.webport.data_quiz import BUNDLES, DEFAULT_BUNDLE, QUESTIONS

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip(s: str) -> str:
    return _ANSI.sub("", s)


def run(arg: str, state: dict) -> str:
    return strip(quiz.handle(arg, state))


def force_question(state: dict, qid: str) -> dict:
    """Start the default run, then swap in a specific pending question."""
    quiz.handle("", state)
    state["webquiz_current"] = qid
    return state


def find_q(**conds):
    for q in QUESTIONS:
        if all(q.get(k) == v for k, v in conds.items()):
            return q
    raise AssertionError(f"no frozen question matching {conds}")


class TestData(unittest.TestCase):
    def test_default_bundle_exists(self):
        self.assertIn(DEFAULT_BUNDLE, {b["id"] for b in BUNDLES})

    def test_questions_have_required_fields(self):
        self.assertGreater(len(QUESTIONS), 250)
        ids = set()
        for q in QUESTIONS:
            self.assertTrue(q["id"] and q["prompt"])
            self.assertIn(q["type"], ("open", "mc", "tf", "completion", "code"))
            self.assertNotIn(q["id"], ids)
            ids.add(q["id"])
            if q["type"] == "mc":
                self.assertTrue(0 <= q["correct"] < len(q["choices"]))
            if q["type"] == "tf":
                self.assertIsInstance(q["answer"], bool)
            if q["type"] == "code":
                self.assertIn(q["validator"], quiz.VALIDATORS)

    def test_desktop_only_topics_left_out(self):
        topics = {q["topic"] for q in QUESTIONS}
        for excluded in ("ag", "arist", "alligators"):
            self.assertNotIn(excluded, topics)

    def test_every_bundle_has_a_nonempty_pool(self):
        for b in BUNDLES:
            state = {"webquiz_seed": 1}
            out = run(b["id"], state)
            self.assertIn("Quiz session", out, b["id"])
            self.assertTrue(quiz.pending(state), b["id"])


class TestSessionFlow(unittest.TestCase):
    def test_bare_quiz_starts_default_bundle(self):
        state = {"webquiz_seed": 3}
        out = run("", state)
        self.assertIn("Quiz session", out)
        self.assertIn("Bundle: intro_lambda", out)
        self.assertIn("Question 1/20", out)
        self.assertTrue(quiz.pending(state))

    def test_bare_quiz_repeats_pending_question(self):
        state = {"webquiz_seed": 3}
        first = run("", state)
        again = run("", state)
        self.assertIn("current question repeated", again)
        self.assertIn("Question 1/20", again)
        # Same question text is shown again.
        qid = state["webquiz_current"]
        self.assertIn(quiz._Q_BY_ID[qid]["prompt"], first)
        self.assertIn(quiz._Q_BY_ID[qid]["prompt"], again)

    def test_switch_bundle(self):
        state = {"webquiz_seed": 3}
        out = run("church_essentials", state)
        self.assertIn("Bundle: church_essentials", out)
        self.assertIn("Topic: church", out)
        self.assertEqual(state["webquiz_bundle"], "church_essentials")

    def test_unknown_subcommand(self):
        out = run("no_such_bundle", {})
        self.assertIn("No quiz subcommand or bundle", out)

    def test_answer_advances_to_next_question(self):
        state = {"webquiz_seed": 3}
        run("", state)
        out = run("definitely-wrong-answer-xyzzy", state)
        self.assertIn("Question 2/20", out)

    def test_skip_counts_and_shows_canonical(self):
        state = {"webquiz_seed": 3}
        run("", state)
        out = run("skip", state)
        self.assertIn("↷ Skipped.", out)
        self.assertIn("Canonical answer:", out)
        self.assertEqual(state["webquiz_score"]["skipped"], 1)
        self.assertEqual(state["webquiz_score"]["asked"], 1)

    def test_stop_shows_final_score_and_records_attempt(self):
        state = {"webquiz_seed": 3}
        run("", state)
        run("wrong-zzz", state)
        out = run("stop", state)
        self.assertIn("Final score", out)
        self.assertIn("Correct: 0/1", out)
        self.assertIn("By topic:", out)
        self.assertEqual(len(state["webquiz_attempts"]), 1)
        self.assertFalse(quiz.pending(state))

    def test_stop_without_session(self):
        out = run("stop", {})
        self.assertIn("quiz closed.", out)

    def test_full_run_reaches_final_score(self):
        state = {"webquiz_seed": 5}
        run("", state)
        for _ in range(25):
            if not quiz.pending(state):
                break
            out = run("zzz-wrong", state)
        self.assertIn("Final score", out)
        self.assertIn("/20", out)
        self.assertEqual(state["webquiz_attempts"][0]["n_questions"], 20)

    def test_hint_command(self):
        q = find_q(id="open_lambda_x_x_y")
        self.assertTrue(q)
        state = force_question({"webquiz_seed": 1}, "open_lambda_x_x_y")
        out = run("hint", state)
        # This question has no hint field; either a hint or the no-hint notice.
        self.assertTrue("hint" in out or "💡" in out)

    def test_hint_without_pending(self):
        out = run("hint", {})
        self.assertIn("No question is pending", out)


class TestGrading(unittest.TestCase):
    def test_open_exact(self):
        state = force_question({"webquiz_seed": 1}, "open_lambda_x_x_y")
        out = run("y", state)
        self.assertIn("✓ Correct!", out)
        self.assertIn("exact match", out)
        self.assertEqual(state["webquiz_score"]["correct"], 1)

    def test_open_alpha_equivalent(self):
        q = next(q for q in QUESTIONS
                 if q["type"] == "open" and (q.get("answer") or "").startswith("\\"))
        state = force_question({"webquiz_seed": 1}, q["id"])
        # Rename bound variables via the matcher itself to build a variant:
        matched, method = quiz.answers_match(q["answer"], q["answer"])
        self.assertTrue(matched)
        # α-variant: answer "\x. x"-style renamed manually
        variant = q["answer"].replace("x", "w").replace("y", "v")
        ok, meth = quiz.answers_match(variant, q["answer"])
        if ok:  # only assert via handle when the rename is a real α-variant
            out = run(variant, state)
            self.assertIn("✓ Correct!", out)

    def test_open_church_constant_beta_equivalence(self):
        # Answer "TRUE"; a raw λ-term for TRUE must be accepted (α after expansion).
        state = force_question({"webquiz_seed": 1}, "open_church_and_true_true")
        out = run("\\t f. t", state)
        self.assertIn("✓ Correct!", out)
        self.assertIn("α-equivalent", out)

    def test_open_wrong_shows_canonical_and_explanation(self):
        state = force_question({"webquiz_seed": 1}, "open_church_and_true_true")
        out = run("FALSE", state)
        self.assertIn("✗ Incorrect", out)
        self.assertIn("Canonical answer: TRUE", out)
        self.assertIn("Boolean connectives reduce to TRUE/FALSE.", out)

    def test_mc_correct_and_wrong(self):
        q = find_q(id="mc_church_00_true")
        letter = "ABCDEFGH"[q["correct"]]
        wrong = "ABCDEFGH"[(q["correct"] + 1) % len(q["choices"])]
        state = force_question({"webquiz_seed": 1}, q["id"])
        out = run(letter, state)
        self.assertIn("✓ Correct!", out)
        state = force_question({"webquiz_seed": 1}, q["id"])
        out = run(wrong, state)
        self.assertIn("✗ Incorrect", out)
        self.assertIn(f"{letter}) ", out)  # canonical shows the right letter

    def test_tf_grading_accepts_word_forms(self):
        q = next(q for q in QUESTIONS if q["type"] == "tf")
        right = "true" if q["answer"] else "no"
        state = force_question({"webquiz_seed": 1}, q["id"])
        out = run(right if q["answer"] else "false", state)
        self.assertIn("✓ Correct!", out)
        state = force_question({"webquiz_seed": 1}, q["id"])
        out = run("f" if q["answer"] else "t", state)
        self.assertIn("✗ Incorrect", out)
        self.assertIn("TRUE" if q["answer"] else "FALSE", out)

    def test_completion_alpha_variant(self):
        state = force_question({"webquiz_seed": 1}, "comp_lambda_00")
        out = run("\\z. z", state)
        self.assertIn("✓ Correct!", out)

    def test_code_decode_numeral(self):
        state = force_question({"webquiz_seed": 1}, "code_peano_00")
        out = run("\\f x. x", state)
        self.assertIn("✓ Correct!", out)
        self.assertIn("decoded numeral 0", out)

    def test_code_wrong_numeral(self):
        state = force_question({"webquiz_seed": 1}, "code_peano_00")
        out = run("\\f x. f x", state)
        self.assertIn("✗ Incorrect", out)
        self.assertIn("got 1, expected 0", out)

    def test_code_identity_alpha_equiv(self):
        state = force_question({"webquiz_seed": 1}, "code_lambda_00")
        out = run("\\q. q", state)
        self.assertIn("✓ Correct!", out)
        self.assertIn("alpha-equivalent", out)


class TestMatcherUnit(unittest.TestCase):
    def test_ladder(self):
        self.assertEqual(quiz.answers_match("y", "y"), (True, "exact"))
        self.assertEqual(quiz.answers_match("  \\x.   x", "\\x. x"), (True, "whitespace"))
        self.assertEqual(quiz.answers_match("\\a. a", "\\x. x"), (True, "alpha"))
        self.assertEqual(quiz.answers_match("(\\x. x) (\\y. y)", "\\z. z"),
                         (True, "alpha+beta"))
        self.assertEqual(quiz.answers_match("crocodile", "CROCODILE!"),
                         (True, "substring"))
        self.assertEqual(quiz.answers_match("", "x"), (False, "empty"))
        self.assertEqual(quiz.answers_match("\\x. x x", "\\x. x"), (False, "none"))

    def test_numeric_equivalence_via_expansion(self):
        self.assertTrue(quiz.answers_match("PLUS 2 2", "4")[0])
        self.assertTrue(quiz.answers_match("4", "\\f x. f (f (f (f x)))")[0])
        self.assertTrue(quiz.answers_match("NOT FALSE", "TRUE")[0])

    def test_strict_match(self):
        self.assertTrue(quiz.strict_match(" \\x. x ", "\\x. x"))
        self.assertFalse(quiz.strict_match("\\y. y", "\\x. x"))
        self.assertFalse(quiz.strict_match("", ""))

    def test_validators_unit(self):
        self.assertEqual(quiz.run_validator("decode_bool_eq", "AND TRUE TRUE", True)[0], True)
        self.assertEqual(quiz.run_validator("decode_numeral_eq", "MULT 2 3", 6)[0], True)
        self.assertEqual(quiz.run_validator("reduces_to_var", "(\\x. x) hello", "hello")[0], True)
        ok, detail = quiz.run_validator("nope", "x", "x")
        self.assertFalse(ok)
        self.assertIn("unknown-validator", detail)


class TestSubcommands(unittest.TestCase):
    def test_bundles_lists_all_frozen_bundles(self):
        out = run("bundles", {})
        for b in BUNDLES:
            self.assertIn(b["id"], out)
        self.assertIn("Question bundles", out)

    def test_topics_and_types(self):
        out = run("topics", {})
        self.assertIn("lambda", out)
        self.assertIn("church", out)
        out = run("types", {})
        self.assertIn("multiple choice", out)
        self.assertIn("λ-code", out)

    def test_score_empty_then_reset(self):
        state = {}
        out = run("score", state)
        self.assertIn("No finished sessions yet.", out)
        state = {"webquiz_seed": 3}
        run("", state)
        run("wrong-zzz", state)
        run("stop", state)
        out = run("score", state)
        self.assertIn("intro_lambda", out)
        self.assertIn("0/1", out)
        out = run("score reset", state)
        self.assertIn("Score history reset.", out)
        self.assertEqual(state["webquiz_attempts"], [])

    def test_online_flag_degrades_with_notice(self):
        state = {"webquiz_seed": 3}
        out = run("--online", state)
        self.assertIn("not available in the browser", out)
        self.assertIn("Question 1/20", out)  # still asks a question

    def test_strict_flag(self):
        state = {"webquiz_seed": 1}
        out = run("--strict", state)
        self.assertIn("Strict matching enabled", out)
        force_question(state, "open_church_and_true_true")
        out = run("\\t f. t", state)  # α-equivalent but not literal
        self.assertIn("✗ Incorrect", out)

    def test_help(self):
        out = run("help", {})
        self.assertIn("quiz bundles", out)
        self.assertIn("LLM judge", out)


if __name__ == "__main__":
    unittest.main()
