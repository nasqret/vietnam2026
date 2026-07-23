"""Tests for the browser `prove` family - the interactive Curry-Howard proof builder.

Drives ``lambda_lab.lab.webport.prove.handle`` directly, asserting on
ANSI-stripped output.
"""

from __future__ import annotations

import re
import unittest

from lambda_lab.lab.webport import prove

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip(s: str) -> str:
    return ANSI.sub("", s).replace("\r\n", "\n")


class ProveBase(unittest.TestCase):
    def setUp(self) -> None:
        self.state: dict = {}

    def run_line(self, line: str) -> str:
        return strip(prove.handle(line, self.state))

    def start(self, prop: str) -> str:
        return self.run_line(prop)


class TestCommandMode(ProveBase):
    def test_usage_no_args(self):
        out = self.run_line("")
        self.assertIn("Usage: prove <type>, e.g. `prove P -> P`.", out)
        self.assertIn("Curry–Howard proof builder", out)
        self.assertIn("prove tactic", out)
        self.assertIn("prove lib", out)
        self.assertFalse(prove.is_active(self.state))

    def test_help_keyword(self):
        self.assertIn("Usage: prove <type>", self.run_line("help"))

    def test_parse_error(self):
        out = self.run_line("P ->")
        self.assertIn("Cannot parse type:", out)
        self.assertFalse(prove.is_active(self.state))

    def test_connective_gets_fragment_note(self):
        out = self.run_line("P ∧ Q")
        self.assertIn("Cannot parse type:", out)
        self.assertIn("implicational fragment", out)

    def test_session_word_without_session(self):
        for word in ("qed", "abort", "intro", "assumption", "undo", "hint"):
            out = self.run_line(word)
            self.assertIn("No proof in progress.", out, word)

    def test_output_uses_crlf(self):
        raw = prove.handle("", {})
        self.assertIn("\r\n", raw)


class TestSessionFlow(ProveBase):
    def test_start_session_shows_goal(self):
        out = self.start("P -> Q -> P")
        self.assertIn("Proof builder", out)
        self.assertIn("Goal 1/1", out)
        self.assertIn("Context: (empty)", out)
        self.assertIn("Target:  P → Q → P", out)
        self.assertIn("?₀", out)
        self.assertIn("Tactics: intro [name], exact <term>, apply <term>, assumption, "
                      "refine <term>, hint, undo, qed, abort.", out)
        self.assertTrue(prove.is_active(self.state))

    def test_intro_named(self):
        self.start("P -> Q -> P")
        out = self.run_line("intro p")
        self.assertIn("Context: p : P", out)
        self.assertIn("Target:  Q → P", out)
        self.assertIn("λp. ?₁", out)

    def test_intro_collision_picks_fresh_name(self):
        self.start("P -> Q -> P")
        self.run_line("intro p")
        out = self.run_line("intro p")
        self.assertIn("Context: p : P, q : Q", out)

    def test_intros_with_names(self):
        self.start("P -> Q -> P")
        out = self.run_line("intros h1 h2")
        self.assertIn("Context: h1 : P, h2 : Q", out)
        self.assertIn("Target:  P", out)

    def test_full_proof_k_combinator(self):
        self.start("P -> Q -> P")
        self.run_line("intro p")
        self.run_line("intro q")
        out = self.run_line("exact p")
        self.assertIn("All goals closed.", out)
        self.assertIn("Type qed to extract the proof term", out)
        out = self.run_line("qed")
        self.assertIn("QED.", out)
        self.assertIn("Final lambda-term: λp q. p", out)
        self.assertIn("Proves:            P → Q → P", out)
        self.assertIn("Principal type:    α → β → α", out)
        self.assertIn("Lean export/verification is desktop-only", out)
        self.assertFalse(prove.is_active(self.state))

    def test_assumption_closes_goal(self):
        self.start("P -> P")
        self.run_line("intro")
        out = self.run_line("assumption")
        self.assertIn("All goals closed.", out)
        out = self.run_line("qed")
        self.assertIn("Final lambda-term: λp. p", out)

    def test_apply_opens_subgoal(self):
        self.start("(P -> Q) -> P -> Q")
        self.run_line("intros")
        out = self.run_line("apply p")
        self.assertIn("Target:  P", out)
        out = self.run_line("assumption")
        self.assertIn("All goals closed.", out)
        out = self.run_line("qed")
        self.assertIn("Final lambda-term: λp q. p q", out)

    def test_s_combinator_proof(self):
        self.start("(P -> Q -> R) -> (P -> Q) -> P -> R")
        self.run_line("intros")
        out = self.run_line("apply p")
        self.assertIn("Goal 1/2", out)
        self.assertIn("Goal 2/2", out)
        self.run_line("assumption")
        self.run_line("apply q")
        out = self.run_line("assumption")
        self.assertIn("All goals closed.", out)
        out = self.run_line("qed")
        self.assertIn("Final lambda-term: λp q r. p r (q r)", out)
        self.assertIn("Principal type:    (α → β → γ) → (α → β) → α → γ", out)

    def test_refine_is_exact_alias(self):
        self.start("P -> P")
        self.run_line("intro h")
        out = self.run_line("refine h")
        self.assertIn("All goals closed.", out)

    def test_exact_closed_term_unifies_with_goal(self):
        # Deviation from the strict desktop check: a hint suggestion works.
        self.start("P -> P")
        hint_out = self.run_line("hint")
        self.assertIn("Hint: try `exact λp. p`.", hint_out)
        out = self.run_line("exact \\x. x")
        self.assertIn("All goals closed.", out)

    def test_qed_with_open_goals(self):
        self.start("P -> P")
        out = self.run_line("qed")
        self.assertIn("There are still open goals - cannot finish.", out)
        self.assertTrue(prove.is_active(self.state))

    def test_abort(self):
        self.start("P -> P")
        out = self.run_line("abort")
        self.assertIn("Leaving the builder.", out)
        self.assertFalse(prove.is_active(self.state))
        self.assertEqual({}, {k: v for k, v in self.state.items() if k.startswith("prove.")})

    def test_quit_alias_aborts(self):
        self.start("P -> P")
        self.run_line("q")
        self.assertFalse(prove.is_active(self.state))

    def test_empty_line_in_session(self):
        self.start("P -> P")
        self.assertEqual("", self.run_line(""))
        self.assertTrue(prove.is_active(self.state))

    def test_question_mark_shows_state(self):
        self.start("P -> Q -> P")
        self.run_line("intro p")
        out = self.run_line("?")
        self.assertIn("Goal 1/1", out)
        self.assertIn("Context: p : P", out)
        self.assertIn("Target:  Q → P", out)

    def test_undo(self):
        self.start("P -> P")
        self.run_line("intro")
        out = self.run_line("undo")
        self.assertIn("Last step undone.", out)
        self.assertIn("Target:  P → P", out)
        out = self.run_line("undo")
        self.assertIn("History is empty - nothing to undo.", out)


class TestSessionErrors(ProveBase):
    def test_intro_on_atom_goal(self):
        self.start("P -> P")
        self.run_line("intro")
        out = self.run_line("intro")
        self.assertIn("Tactic error:", out)
        self.assertIn("Goal `P` is not an implication - `intro` does not apply here.", out)

    def test_exact_unknown_term(self):
        self.start("P -> P")
        self.run_line("intro")
        out = self.run_line("exact z")
        self.assertIn("I do not know term `z` in the current context.", out)

    def test_exact_type_mismatch(self):
        self.start("P -> Q -> P")
        self.run_line("intros")
        out = self.run_line("exact q")
        self.assertIn("Term `q` has type `Q` but the goal is `P`.", out)

    def test_exact_needs_arg(self):
        self.start("P -> P")
        out = self.run_line("exact")
        self.assertIn("Tactic `exact` needs an argument, e.g. `exact p`.", out)

    def test_assumption_no_match(self):
        self.start("P -> Q")
        self.run_line("intro")
        out = self.run_line("assumption")
        self.assertIn("No hypothesis matches the goal `Q`.", out)

    def test_unknown_tactic(self):
        self.start("P -> P")
        out = self.run_line("frobnicate")
        self.assertIn("Unknown tactic `frobnicate`.", out)

    def test_encyclopedia_tactic_not_operational(self):
        self.start("P -> P")
        out = self.run_line("cases")
        self.assertIn("Unknown tactic `cases`.", out)
        self.assertIn("implicational fragment", out)
        self.assertIn("prove tactic cases", out)

    def test_hint_none_for_peirce(self):
        # Peirce's law is not intuitionistically provable.
        self.start("((P -> Q) -> P) -> P")
        self.run_line("intro")
        out = self.run_line("hint")
        self.assertIn("No automatic hint for the current goal.", out)

    def test_hint_prefers_assumption(self):
        self.start("P -> P")
        self.run_line("intro h")
        out = self.run_line("hint")
        self.assertIn("Hint: try `exact h`.", out)


class TestReference(ProveBase):
    def test_cheat_sheet(self):
        out = self.run_line("tactics")
        self.assertIn("Cheat sheet: builder tactic syntax", out)
        self.assertIn("intro [name]", out)
        self.assertIn("qed / done", out)
        self.assertIn("abort / quit / q", out)
        self.assertIn("Finish (when all goals are closed).", out)

    def test_cheat_sheet_inside_session(self):
        self.start("P -> P")
        out = self.run_line("t")
        self.assertIn("Cheat sheet: builder tactic syntax", out)
        self.assertTrue(prove.is_active(self.state))

    def test_tactic_catalog(self):
        out = self.run_line("tactic")
        self.assertIn("Encyclopedia of Lean 4 tactics", out)
        self.assertIn("intro", out)
        self.assertIn("linarith", out)
        self.assertIn("Nat.add_comm", out)
        self.assertIn("a + b = b + a", out)

    def test_tactic_entry(self):
        out = self.run_line("tactic cases")
        self.assertIn("Tactic cases", out)
        self.assertIn("Splits a hypothesis into cases", out)
        self.assertIn("(h : A ∨ B) ⊢ C", out)
        self.assertIn("implicational fragment", out)

    def test_tactic_entry_operational_has_no_note(self):
        out = self.run_line("tactic intro")
        self.assertIn("Tactic intro", out)
        self.assertNotIn("implicational fragment only", out)

    def test_tactic_unknown(self):
        out = self.run_line("tactic zzz")
        self.assertIn("Unknown tactic `zzz`. Run `prove tactic` to see the list.", out)

    def test_lib_catalog(self):
        out = self.run_line("lib")
        self.assertIn("Combinator catalogue", out)
        self.assertIn("id", out)
        self.assertIn("\\x y z. x z (y z)", out)
        self.assertIn("(not typeable in STLC)", out)

    def test_lib_entry_by_alias(self):
        out = self.run_line("lib flip")
        self.assertIn("Combinator C", out)
        self.assertIn("\\f x y. f y x", out)
        self.assertIn("(α → β → γ) → β → α → γ", out)

    def test_lib_unknown(self):
        out = self.run_line("lib nope")
        self.assertIn("Unknown combinator `nope`. Type `prove lib` to see the list.", out)


if __name__ == "__main__":
    unittest.main()
