"""Soundness regression suite for the interactive proof builders.

Implements the 2026-07-24 audit's mandatory oracle and its 21 concrete
regression groups, parameterized over BOTH front ends (``prove`` and
``ch build``) — they share one engine (`proof_builder` on the `stlc_types`
kernel), and this suite pins that engine's soundness:

* P0.1 — checked finalization (no QED without re-checking the term),
* P0.2 — rigid Atoms vs. inference MetaVars,
* P0.3 — proof-wide substitution propagated to sibling goals,
* P0.4 — no smuggled free variables in tactic terms.
"""

from __future__ import annotations

import re
import unittest

from lambda_lab.lab import lc
from lambda_lab.lab.webport import ch, proof_builder, prove
from lambda_lab.lab.webport.stlc_types import (
    infer_closed,
    parse_type,
    pretty_type,
    target_is_instance_of,
)

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip(s: str) -> str:
    return ANSI.sub("", s).replace("\r\n", "\n")


# ---------------------------------------------------------------------------
# The mandatory soundness oracle (engine level)
# ---------------------------------------------------------------------------


def run_engine(prop: str, tactics):
    """Run a tactic script on the bare engine, asserting the structural
    invariants after every accepted step. Returns the final ProofState."""
    st = proof_builder.start(parse_type(prop))
    for line in tactics:
        parts = line.split(maxsplit=1)
        st = proof_builder.apply_tactic(st, parts[0], parts[1] if len(parts) > 1 else "")
        assert proof_builder.invariants_ok(st), f"invariants broken after {line!r}"
    return st


class EngineOracle(unittest.TestCase):
    """Every successful QED satisfies one shared invariant (audit §oracle)."""

    def assert_sound_qed(self, prop: str, tactics):
        st = run_engine(prop, tactics)
        term, principal_pretty = proof_builder.checked_final(st)
        self.assertIsNotNone(term)
        self.assertEqual(lc.free_vars(term), set())
        principal = infer_closed(term)
        self.assertTrue(target_is_instance_of(principal, parse_type(prop)))
        return term

    # Group 19 — positive scripts: I, K, B, C, S, W, modus ponens, whole-term
    # exact, apply, assumption, undo, hint.
    def test_I(self):
        self.assert_sound_qed("P -> P", ["intro p", "exact p"])

    def test_K(self):
        self.assert_sound_qed("P -> Q -> P", ["intros p q", "exact p"])

    def test_B_composition(self):
        self.assert_sound_qed("(Q -> R) -> (P -> Q) -> P -> R",
                              ["intros f g p", "apply f", "apply g", "exact p"])

    def test_C_flip(self):
        self.assert_sound_qed("(P -> Q -> R) -> Q -> P -> R",
                              ["intros f q p", "apply f", "exact p", "exact q"])

    def test_S(self):
        self.assert_sound_qed("(P -> Q -> R) -> (P -> Q) -> P -> R",
                              ["intros f g p", "apply f", "exact p", "apply g", "exact p"])

    def test_W_contraction(self):
        self.assert_sound_qed("(P -> P -> Q) -> P -> Q",
                              ["intros f p", "apply f", "exact p", "exact p"])

    def test_modus_ponens(self):
        self.assert_sound_qed("P -> (P -> Q) -> Q", ["intros p f", "apply f", "exact p"])

    def test_whole_term_exact(self):
        self.assert_sound_qed("P -> Q -> P", [r"exact \p q. p"])

    def test_assumption(self):
        self.assert_sound_qed("P -> Q -> Q", ["intros", "assumption"])

    def test_undo_then_redo(self):
        st = run_engine("P -> P", ["intro a", "undo", "intro p", "exact p"])
        term, _ = proof_builder.checked_final(st)
        self.assertEqual(lc.pretty(term), "λp. p")

    def test_hint_suggestion_is_checkable(self):
        st = run_engine("(Q -> R) -> (P -> Q) -> P -> R", ["intros f g p"])
        status, suggestion = proof_builder.hint(st)
        self.assertEqual(status, "exact")
        st2 = proof_builder.exact(st, suggestion)
        self.assertTrue(st2.is_done())

    # Group 9 — the slide's proof of P -> (P -> Q) -> Q.
    def test_slide_proof_accepted(self):
        self.assert_sound_qed("P -> (P -> Q) -> Q", [r"exact \p f. f p"])

    def test_slide_wrong_proof_rejected(self):
        with self.assertRaises(proof_builder.TacticError):
            run_engine("P -> (P -> Q) -> Q", [r"exact \p f. p"])


# ---------------------------------------------------------------------------
# Rigid atoms (groups 1–4)
# ---------------------------------------------------------------------------


class RigidAtoms(unittest.TestCase):
    def test_lowercase_atoms_rigid(self):
        st = run_engine("p -> q", ["intro h"])
        with self.assertRaises(proof_builder.TacticError) as cm:
            proof_builder.exact(st, "h")
        self.assertIn("has type `p` but the goal is `q`", str(cm.exception))

    def test_greek_atoms_rigid(self):
        st = run_engine("α -> β", ["intro h"])
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.exact(st, "h")

    def test_mixed_case_rigid(self):
        for prop in ("p -> Q", "P -> q"):
            st = run_engine(prop, ["intro h"])
            with self.assertRaises(proof_builder.TacticError):
                proof_builder.exact(st, "h")

    def test_digit_leading_atom_rejected(self):
        with self.assertRaises(ValueError):
            parse_type("1P -> P")

    def test_identity_on_rigid_lowercase_still_provable(self):
        st = run_engine("p -> p", ["intro h", "exact h"])
        proof_builder.checked_final(st)


# ---------------------------------------------------------------------------
# Free-variable rejection (group 5) and Peirce (group 7)
# ---------------------------------------------------------------------------


class ScopeAndPeirce(unittest.TestCase):
    def test_composite_free_vars_rejected(self):
        st = run_engine("(P -> Q) -> P -> Q", ["intros f p"])
        for tac in ("exact", "apply", "refine"):
            with self.assertRaises(proof_builder.TacticError) as cm:
                proof_builder.apply_tactic(st, tac, "f z")
            self.assertIn("unknown term variable", str(cm.exception), tac)

    def test_peirce_exploit_dead(self):
        # The audit's false-QED script: every closing move must now fail.
        st = run_engine("((P -> Q) -> P) -> P", ["intro h", "apply h", "intro p"])
        # goal is Q with p : P in context — nothing closes it
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.exact(st, "p")
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.assumption(st)

    def test_apply_wrong_target_rejected(self):
        st = run_engine("(P -> Q) -> R -> Q", ["intros f r"])
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.apply_(st, "r")  # r : R, goal Q — neither it nor result

    def test_apply_untypable_rejected(self):
        st = run_engine("P -> P", ["intro p"])
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.apply_(st, r"\x. x x")


# ---------------------------------------------------------------------------
# Sibling constraint propagation (group 6)
# ---------------------------------------------------------------------------


class SiblingPropagation(unittest.TestCase):
    def test_apply_links_sibling_goals(self):
        st = run_engine("(P -> R) -> R", ["intro h"])
        st = proof_builder.apply_(st, r"\f x. f x")
        self.assertEqual(len(st.goals), 2)
        # Closing goal 1 with h : P → R must pin the sibling's metavar to P.
        st = proof_builder.exact(st, "h")
        self.assertEqual(len(st.goals), 1)
        from lambda_lab.lab.webport.stlc_types import apply_subst
        self.assertEqual(pretty_type(apply_subst(st.goals[0].target, st.subst)), "P")

    def test_apply_links_sibling_goals_to_qed(self):
        st = run_engine("(P -> R) -> P -> R", ["intros h p"])
        st = proof_builder.apply_(st, r"\f x. f x")
        st = proof_builder.exact(st, "h")
        st = proof_builder.exact(st, "p")
        proof_builder.checked_final(st)


# ---------------------------------------------------------------------------
# checked_final refusals (group 8)
# ---------------------------------------------------------------------------


class CheckedFinalRefusals(unittest.TestCase):
    def test_open_goals_refused(self):
        st = run_engine("P -> P", ["intro p"])
        with self.assertRaises(proof_builder.InvalidProof):
            proof_builder.checked_final(st)

    def test_wrong_target_refused(self):
        # Forge a state whose term does not prove the target.
        from dataclasses import replace
        st = run_engine("P -> P", ["intro p", "exact p"])
        forged = replace(st, target=parse_type("P -> Q"))
        with self.assertRaises(proof_builder.InvalidProof) as cm:
            proof_builder.checked_final(forged)
        self.assertIn("does not instantiate", str(cm.exception))

    def test_free_term_refused(self):
        from dataclasses import replace
        st = run_engine("P -> P", ["intro p", "exact p"])
        forged = replace(st, partial=replace(st.partial, root=lc.Var("z")))
        with self.assertRaises(proof_builder.InvalidProof) as cm:
            proof_builder.checked_final(forged)
        self.assertIn("free variable", str(cm.exception))

    def test_untypable_term_refused(self):
        from dataclasses import replace
        from lambda_lab.lab.parser import parse
        st = run_engine("P -> P", ["intro p", "exact p"])
        forged = replace(st, partial=replace(st.partial, root=parse(r"\x. x x")))
        with self.assertRaises(proof_builder.InvalidProof) as cm:
            proof_builder.checked_final(forged)
        self.assertIn("not typable", str(cm.exception))

    def test_hole_term_refused(self):
        from dataclasses import replace
        st = run_engine("P -> P", ["intro p", "exact p"])
        forged = replace(st, partial=replace(st.partial, root=lc.Var("?0")))
        with self.assertRaises(proof_builder.InvalidProof):
            proof_builder.checked_final(forged)


# ---------------------------------------------------------------------------
# Hint honesty (groups 11–12)
# ---------------------------------------------------------------------------


class HintHonesty(unittest.TestCase):
    def test_contextual_hint_after_intros(self):
        st = run_engine("(Q -> R) -> (P -> Q) -> P -> R", ["intros f g p"])
        status, suggestion = proof_builder.hint(st)
        self.assertEqual(status, "exact")
        self.assertTrue(proof_builder.exact(st, suggestion).is_done())

    def test_hint_none_for_uninhabited(self):
        st = run_engine("((P -> Q) -> P) -> P", ["intro h"])
        status, _ = proof_builder.hint(st)
        self.assertEqual(status, "none")

    def test_hint_limit_for_deep_goal(self):
        prop = " -> ".join("ABCDEFGHIJKL") + " -> A"   # 12 antecedents > depth 10
        st = proof_builder.start(parse_type(prop))
        status, _ = proof_builder.hint(st)
        self.assertEqual(status, "limit")

    def test_hint_assumption(self):
        st = run_engine("P -> P", ["intro h"])
        self.assertEqual(proof_builder.hint(st), ("assumption", "h"))

    def test_hint_done(self):
        st = run_engine("P -> P", ["intro h", "exact h"])
        self.assertEqual(proof_builder.hint(st), ("done", None))


# ---------------------------------------------------------------------------
# refine contract (group 13), argument validation (groups 14–15)
# ---------------------------------------------------------------------------


class TacticArguments(unittest.TestCase):
    def test_refine_is_exact_alias(self):
        st = run_engine("P -> P", ["refine \\p. p"])
        proof_builder.checked_final(st)

    def test_refine_rejects_holes(self):
        st = proof_builder.start(parse_type("P -> P"))
        with self.assertRaises(proof_builder.TacticError) as cm:
            proof_builder.refine(st, r"\x. ?_")
        self.assertIn("alias for `exact`", str(cm.exception))

    def test_invalid_binder_rejected_state_unchanged(self):
        st = proof_builder.start(parse_type("P -> P"))
        for bad in ("?x", "1x", "x-y"):
            with self.assertRaises(proof_builder.TacticError):
                proof_builder.intro(st, bad)
        self.assertEqual(len(st.history), 0)
        self.assertEqual(len(st.goals), 1)

    def test_colliding_binder_rejected(self):
        st = run_engine("P -> P -> P", ["intro h"])
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.intro(st, "h")

    def test_surplus_arguments_rejected(self):
        st = proof_builder.start(parse_type("P -> Q -> P"))
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.intro(st, "a b")
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.assumption(st, "foo")
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.undo(st, "everything")
        self.assertEqual(len(st.history), 0)

    def test_intros_single_undo_transaction(self):
        st = run_engine("P -> Q -> R -> P", ["intros"])
        self.assertEqual(len(st.history), 1)
        st = proof_builder.undo(st)
        self.assertEqual(len(st.history), 0)
        self.assertEqual(pretty_type(st.goals[0].target), "P → Q → R → P")

    def test_intros_on_atom_errors(self):
        st = run_engine("P -> P", ["intros"])
        with self.assertRaises(proof_builder.TacticError):
            proof_builder.intros(st)


# ---------------------------------------------------------------------------
# UI harness, parameterized over `prove` and `ch build` (group 21)
# ---------------------------------------------------------------------------


class ProveUI:
    """Adapter: the standalone `prove` front end."""

    name = "prove"

    def __init__(self):
        self.state: dict = {}

    def start(self, prop: str) -> str:
        return strip(prove.handle(prop, self.state))

    def line(self, l: str) -> str:
        return strip(prove.handle(l, self.state))

    def active(self) -> bool:
        return prove.is_active(self.state)

    def engine_state(self):
        return self.state.get("prove.session")

    def finish(self) -> str:
        return self.line("qed")


class ChBuildUI:
    """Adapter: the `ch build` front end (auto-finishes on last close)."""

    name = "ch build"

    def __init__(self):
        self.state: dict = {}

    def start(self, prop: str) -> str:
        return strip(ch.handle("build " + prop, self.state))

    def line(self, l: str) -> str:
        return strip(ch.handle(l, self.state))

    def active(self) -> bool:
        return self.state.get("ch.build") is not None

    def engine_state(self):
        return self.state.get("ch.build")

    def finish(self) -> str:
        return self.line("qed")


UIS = (ProveUI, ChBuildUI)


class ParameterizedUI(unittest.TestCase):
    """Each test runs against BOTH front ends."""

    def run_script(self, ui_cls, prop, tactics):
        ui = ui_cls()
        outs = [ui.start(prop)]
        for t in tactics:
            outs.append(ui.line(t))
            st = ui.engine_state()
            if st is not None:
                self.assertTrue(proof_builder.invariants_ok(st),
                                f"[{ui_cls.name}] invariants after {t!r}")
        return ui, outs

    def assert_proves(self, prop, tactics, expect_term=None):
        for ui_cls in UIS:
            ui, outs = self.run_script(ui_cls, prop, tactics)
            out = ui.finish() if ui.active() else outs[-1]
            self.assertIn("Final lambda-term", out, f"[{ui_cls.name}] {prop}")
            self.assertFalse(ui.active(), f"[{ui_cls.name}] session should end")
            if expect_term is not None:
                self.assertIn(expect_term, out, f"[{ui_cls.name}]")

    def assert_stuck(self, prop, tactics):
        """The script must NOT produce a QED on either front end."""
        for ui_cls in UIS:
            ui, outs = self.run_script(ui_cls, prop, tactics)
            all_out = "\n".join(outs)
            if ui.active():
                out = ui.finish()
                all_out += "\n" + out
            self.assertNotIn("Final lambda-term", all_out, f"[{ui_cls.name}] {prop}")

    # positive scripts across both UIs
    def test_identity_both_uis(self):
        self.assert_proves("P -> P", ["intro p", "exact p"], "λp. p")

    def test_s_combinator_both_uis(self):
        self.assert_proves("(P -> Q -> R) -> (P -> Q) -> P -> R",
                           ["intros f g p", "apply f", "exact p", "apply g", "exact p"],
                           "λf g p. f p (g p)")

    # group 20 — negative scripts
    def test_peirce_stuck_both_uis(self):
        self.assert_stuck("((P -> Q) -> P) -> P",
                          ["intro h", "apply h", "intro p", "exact p",
                           "assumption", "qed"])

    def test_plain_implication_stuck(self):
        self.assert_stuck("P -> Q", ["intro p", "assumption", "exact p", "qed"])

    def test_double_negation_elimination_stuck(self):
        self.assert_stuck("((P -> F) -> F) -> P",
                          ["intro h", "apply h", "intro p", "assumption", "qed"])

    # group 16 — complete-line, case-sensitive meta commands
    def test_qed_with_extra_words_refused(self):
        for ui_cls in UIS:
            ui = ui_cls()
            ui.start("P -> P")
            out = ui.line("qed please")
            self.assertIn("typed alone", out, ui_cls.name)
            self.assertTrue(ui.active(), ui_cls.name)

    def test_uppercase_Q_is_not_quit(self):
        for ui_cls in UIS:
            ui = ui_cls()
            ui.start("P -> P")
            ui.line("Q")
            self.assertTrue(ui.active(), f"[{ui_cls.name}] `Q` must not quit")

    def test_premature_qed_keeps_session(self):
        for ui_cls in UIS:
            ui = ui_cls()
            ui.start("P -> P")
            out = ui.line("qed")
            self.assertIn("still open goals", out, ui_cls.name)
            self.assertTrue(ui.active(), ui_cls.name)

    # group 18 — nested prove/build refused, state untouched
    def test_nested_start_refused(self):
        for ui_cls in UIS:
            ui = ui_cls()
            ui.start("P -> P")
            ui.line("intro h")
            before = ui.engine_state()
            for nested in ("prove Q -> Q", "ch build Q -> Q"):
                ui.line(nested)
                self.assertIs(ui.engine_state(), before,
                              f"[{ui_cls.name}] {nested!r} must not touch the session")
            self.assertTrue(ui.active())


# ---------------------------------------------------------------------------
# Reserved names stay usable atoms (group 10) — prove grammar
# ---------------------------------------------------------------------------


class ReservedAtoms(unittest.TestCase):
    def prove_identity(self, atom: str):
        state: dict = {}
        out = strip(prove.handle(f"{atom} -> {atom}", state))
        self.assertTrue(prove.is_active(state), atom)
        self.assertIn(f"{atom} → {atom}", out)
        strip(prove.handle("intro h", state))
        strip(prove.handle("exact h", state))
        out = strip(prove.handle("qed", state))
        self.assertIn("Final lambda-term", out, atom)
        self.assertFalse(prove.is_active(state))

    def test_reserved_words_as_atoms(self):
        for atom in ("T", "Q", "LIB", "QED", "INTRO", "TACTICS", "DONE", "ABORT"):
            self.prove_identity(atom)

    def test_exact_subcommands_still_work(self):
        state: dict = {}
        self.assertIn("Cheat sheet", strip(prove.handle("tactics", state)))
        self.assertIn("Cheat sheet", strip(prove.handle("t", state)))
        self.assertIn("Encyclopedia", strip(prove.handle("tactic", state)))
        self.assertIn("Combinator", strip(prove.handle("lib", state)))
        self.assertIn("No proof in progress", strip(prove.handle("qed", state)))
        self.assertFalse(prove.is_active(state))


# ---------------------------------------------------------------------------
# Driver-level session ownership (group 17)
# ---------------------------------------------------------------------------


class DriverOwnership(unittest.TestCase):
    def setUp(self):
        import driver
        self.session = driver.LabSession()

    def run_line(self, line: str) -> str:
        return strip(self.session.run(line))

    def test_active_prove_owns_all_lines(self):
        self.run_line("prove P -> P")
        out = self.run_line("ch build Q -> Q")
        self.assertIn("unknown tactic", out)
        out = self.run_line("prove Q -> Q")
        self.assertIn("already in progress", out)
        self.run_line("intro h")
        self.run_line("exact h")
        out = self.run_line("qed")
        self.assertIn("Final lambda-term", out)
        # after QED ordinary commands work again
        self.assertIn("Church numeral", self.run_line("church 3"))

    def test_active_ch_build_owns_all_lines(self):
        self.run_line("ch build P -> P")
        out = self.run_line("prove Q -> Q")
        self.assertIn("already in progress", out)
        self.run_line("intro h")
        out = self.run_line("exact h")   # ch build auto-finishes
        self.assertIn("Final lambda-term", out)

    def test_quiz_blocks_new_proof(self):
        self.run_line("quiz")
        out = self.run_line("prove P -> P")
        self.assertIn("Cannot start a proof", out)
        self.run_line("stop")
        out = self.run_line("prove P -> P")
        self.assertIn("Proof builder", out)
        self.run_line("abort")


if __name__ == "__main__":
    unittest.main()
