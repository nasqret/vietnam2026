"""Tests for the browser port of the ``ch`` family (Curry-Howard playground).

Drives ``lambda_lab.lab.webport.ch.handle`` directly and asserts on
ANSI-stripped output.
"""

import re
import unittest

from lambda_lab.lab.webport import ch
from lambda_lab.lab.webport import data_ch_explore, data_ch_library, data_ch_tactics
from lambda_lab.lab.webport.ch_stlc import (
    Arrow,
    TVar,
    find_inhabitant,
    infer,
    parse_type,
    pretty_type,
)
from lambda_lab.lab.parser import parse

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run(line, state=None):
    out = ch.handle(line, state if state is not None else {})
    return _ANSI.sub("", out).replace("\r\n", "\n")


class TestTermInference(unittest.TestCase):
    """(a) principal-type inference for untyped λ-terms (Algorithm W)."""

    def test_identity_principal_type(self):
        out = run(r"term \p. p")
        self.assertIn("λp. p", out)
        self.assertIn("α → α", out)
        self.assertIn("proof that α → α", out)

    def test_s_combinator_principal_type(self):
        out = run(r"term \x y z. x z (y z)")
        self.assertIn("(α → β → γ) → (α → β) → α → γ", out)

    def test_k_combinator_principal_type(self):
        out = run(r"term \x y. x")
        self.assertIn("α → β → α", out)

    def test_compose_principal_type(self):
        # Left-to-right renumbering: f : α → β, g : γ → α, x : γ.
        out = run(r"term \f g x. f (g x)")
        self.assertIn("(α → β) → (γ → α) → γ → β", out)

    def test_self_application_untypable(self):
        out = run(r"term \x. x x")
        self.assertIn("Term not typeable in STLC", out)

    def test_omega_untypable(self):
        out = run(r"term (\x. x x) (\x. x x)")
        self.assertIn("Term not typeable in STLC", out)

    def test_free_variables_listed(self):
        out = run(r"term \x. y")
        self.assertIn("Free variables", out)
        self.assertIn("y", out)

    def test_parse_error(self):
        out = run(r"term \p.")
        self.assertIn("Cannot parse the lambda-term", out)

    def test_usage_when_empty(self):
        out = run("term")
        self.assertIn("Usage: ch term <lambda>", out)

    def test_infer_direct_api(self):
        self.assertEqual(pretty_type(infer(parse(r"\f x. f x"))),
                         "(α → β) → α → β")


class TestTypeInhabitation(unittest.TestCase):
    """(b) type inhabitation / provability for implicational propositions."""

    def test_identity_inhabited(self):
        out = run("type P -> P")
        self.assertIn("Found proof", out)
        self.assertIn("λp. p", out)
        self.assertIn("theorem ch_proof {P : Prop} : P → P :=", out)

    def test_quoted_type_argument(self):
        out = run("type 'P -> P'")
        self.assertIn("λp. p", out)

    def test_peirce_uninhabited(self):
        out = run("type ((P -> Q) -> P) -> P")
        self.assertIn("not inhabited in intuitionistic STLC", out)
        self.assertIn("((P → Q) → P) → P", out)

    def test_weak_peirce_shape_is_inhabited(self):
        # (P -> Q) -> P -> P is intuitionistically fine (the course example).
        out = run("type (P -> Q) -> P -> P")
        self.assertIn("Found proof", out)
        self.assertIn("λp q. q", out)

    def test_k_type_inhabited(self):
        out = run("type P -> Q -> P")
        self.assertIn("λp q. p", out)

    def test_s_type_inhabited(self):
        out = run("type (P -> Q -> R) -> (P -> Q) -> P -> R")
        self.assertIn("Found proof", out)

    def test_double_negation_elim_uninhabited(self):
        # ((P -> F) -> F) -> P: classical, no constructive witness.
        out = run("type ((P -> F) -> F) -> P")
        self.assertIn("not inhabited", out)

    def test_parse_error(self):
        out = run("type P ->")
        self.assertIn("Cannot parse type", out)

    def test_usage_when_empty(self):
        out = run("type")
        self.assertIn("Usage: ch type <T>", out)

    def test_search_direct_api(self):
        self.assertIsNone(find_inhabitant(parse_type("((P -> Q) -> P) -> P")))
        self.assertIsNotNone(find_inhabitant(parse_type("P -> Q -> P")))


class TestLeanBridge(unittest.TestCase):
    def test_lean_emits_theorem(self):
        out = run(r"lean \p. p")
        self.assertIn("theorem ch_proof {α : Prop} : α → α :=", out)
        self.assertIn("fun p => p", out)
        self.assertIn("live.lean-lang.org", out)

    def test_lean_name_flag(self):
        out = run(r"lean \x y. x --name=my_k")
        self.assertIn("theorem my_k", out)

    def test_lean_untypable(self):
        out = run(r"lean \x. x x")
        self.assertIn("cannot emit theorem", out)

    def test_from_lean_roundtrip(self):
        out = run("from-lean 'fun p => p'")
        self.assertIn("λp. p", out)
        self.assertIn("α → α", out)

    def test_from_lean_application(self):
        out = run("from-lean 'fun f x => f x'")
        self.assertIn("(α → β) → α → β", out)

    def test_fromlean_alias(self):
        out = run("fromlean 'fun p => p'")
        self.assertIn("λp. p", out)

    def test_from_lean_theorem_body(self):
        out = run("from-lean 'theorem t : X := fun p => p'")
        self.assertIn("λp. p", out)

    def test_from_lean_parse_error(self):
        out = run("from-lean 'fun => x'")
        self.assertIn("Cannot parse Lean expression", out)


class TestLibrary(unittest.TestCase):
    def test_catalogue_lists_combinators(self):
        out = run("lib")
        for name in ("id", "K", "S", "B", "C", "Y", "fst", "snd", "app", "W", "O"):
            self.assertIn(name, out)
        self.assertIn("(not typeable in STLC)", out)

    def test_entry_card(self):
        out = run("lib K")
        self.assertIn("Combinator K", out)
        self.assertIn(r"\x y. x", out)
        self.assertIn("α → β → α", out)
        self.assertIn("fun x _ => x", out)
        self.assertIn("const, konst", out)

    def test_alias_lookup(self):
        out = run("lib flip")
        self.assertIn("Combinator C", out)

    def test_unknown_combinator(self):
        out = run("lib nope")
        self.assertIn("Unknown combinator `nope`", out)

    def test_library_types_are_principal(self):
        # The frozen type strings must agree with the inference engine up to
        # renaming of type variables (the desktop cards use the conventional
        # letters, e.g. B : (β → γ) → (α → β) → α → γ).
        def canon(ty):
            mapping = {}

            def go(t):
                if isinstance(t, TVar):
                    if t.name not in mapping:
                        mapping[t.name] = f"v{len(mapping)}"
                    return mapping[t.name]
                assert isinstance(t, Arrow)
                return "(" + go(t.src) + "->" + go(t.dst) + ")"

            return go(ty)

        for name in data_ch_library.canonical_names():
            entry = data_ch_library.LIBRARY[name]
            if entry["type_str"] is None:
                continue
            got = canon(infer(parse(entry["lambda_src"])))
            want = canon(parse_type(entry["type_str"]))
            self.assertEqual(got, want, f"combinator {name}")


class TestTactics(unittest.TestCase):
    def test_catalogue(self):
        out = run("tactic")
        self.assertIn("Encyclopedia of 22 Lean 4 tactics", out)
        for name in ("intro", "exact", "apply", "rw", "omega", "trivial"):
            self.assertIn(name, out)

    def test_entry_card(self):
        out = run("tactic intro")
        self.assertIn("Tactic intro", out)
        self.assertIn("named hypothesis", out)
        self.assertIn("(p : P) ⊢ Q", out)

    def test_unknown(self):
        out = run("tactic zap")
        self.assertIn("Unknown tactic `zap`", out)

    def test_all_entries_complete(self):
        for name in data_ch_tactics.names():
            entry = data_ch_tactics.lookup(name)
            for key in ("summary", "lambda_effect", "goal_effect", "when",
                        "example_goal", "example_after"):
                self.assertTrue(entry[key], f"{name}.{key} empty")


class TestBuilder(unittest.TestCase):
    def test_full_interactive_proof(self):
        st = {}
        out = run("build P -> P", st)
        self.assertIn("Goal 1/1", out)
        self.assertIn("Target", out)
        self.assertIn("P → P", out)
        self.assertIn("?₀", out)
        self.assertTrue(st.get("ch.interactive"))

        out = run("intro p", st)
        self.assertIn("p : P", out)
        self.assertIn("λp. ?₁", out)

        out = run("exact p", st)
        self.assertIn("All goals closed.", out)
        self.assertIn("λp. p", out)
        self.assertIn("theorem ch_proof", out)
        self.assertEqual(st, {})  # session fully cleaned up

    def test_apply_and_assumption(self):
        st = {}
        run("build (P -> Q -> R) -> (P -> Q) -> P -> R", st)
        out = run("intros f g x", st)
        self.assertIn("f : P → Q → R, g : P → Q, x : P", out)
        out = run("apply f", st)
        self.assertIn("Goal 1/2", out)
        self.assertIn("Goal 2/2", out)
        out = run("assumption", st)
        self.assertIn("Goal 1/1", out)
        out = run("exact g x", st)
        self.assertIn("All goals closed.", out)
        self.assertIn("λf g x. f x (g x)", out)

    def test_hint_suggests_assumption(self):
        st = {}
        run("build P -> P", st)
        run("intro p", st)
        out = run("hint", st)
        self.assertIn("Hint: try `exact p`", out)
        run("q", st)

    def test_type_mismatch_reported(self):
        st = {}
        run("build P -> Q -> P", st)
        run("intro p", st)
        run("intro q", st)
        out = run("exact q", st)
        self.assertIn("has type `Q` but the goal is `P`", out)
        run("q", st)
        self.assertEqual(st, {})

    def test_unknown_term(self):
        st = {}
        run("build P -> P", st)
        out = run("exact zz", st)
        self.assertIn("I do not know term `zz`", out)
        run("q", st)

    def test_intro_on_atom_fails(self):
        st = {}
        run("build P -> P", st)
        run("intro p", st)
        out = run("intro", st)
        self.assertIn("not an implication", out)
        run("q", st)

    def test_undo(self):
        st = {}
        run("build P -> P", st)
        run("intro p", st)
        out = run("undo", st)
        self.assertIn("Last step undone.", out)
        self.assertIn("P → P", out)
        out = run("undo", st)
        self.assertIn("History is empty", out)
        run("q", st)

    def test_done_with_open_goals(self):
        st = {}
        run("build P -> P", st)
        out = run("done", st)
        self.assertIn("still open goals", out)
        run("q", st)

    def test_cheat_sheet(self):
        st = {}
        run("build P -> P", st)
        out = run("t", st)
        self.assertIn("Cheat sheet: builder tactic syntax", out)
        self.assertIn("assumption", out)
        self.assertIn("Undo the last tactic.", out)
        run("q", st)

    def test_question_mark_shows_state(self):
        st = {}
        run("build P -> P", st)
        out = run("?", st)
        self.assertIn("Goal 1/1", out)
        run("q", st)

    def test_quit_cleans_state(self):
        st = {}
        run("build P -> P", st)
        out = run("quit", st)
        self.assertIn("Leaving the builder.", out)
        self.assertEqual(st, {})

    def test_unknown_tactic(self):
        st = {}
        run("build P -> P", st)
        out = run("frobnicate", st)
        self.assertIn("Unknown tactic `frobnicate`", out)
        run("q", st)

    def test_state_keys_use_ch_prefix(self):
        st = {}
        run("build P -> P", st)
        self.assertTrue(all(k.startswith("ch.") for k in st), st.keys())
        run("q", st)

    def test_build_parse_error(self):
        out = run("build P ->")
        self.assertIn("Cannot parse type", out)

    def test_build_usage(self):
        out = run("build")
        self.assertIn("Usage: ch build <type>", out)


class TestLeanBackedStubs(unittest.TestCase):
    def test_verify_notice_with_live_link(self):
        out = run("verify theorem t (P : Prop) : P -> P := fun p => p")
        self.assertIn("Lean toolchain", out)
        self.assertIn("not available in the browser build", out)
        self.assertIn("live.lean-lang.org", out)

    def test_verify_usage(self):
        out = run("verify")
        self.assertIn("Usage: ch verify", out)

    def test_explore_live_notice(self):
        out = run("explore --live --src 'theorem t : P := p'")
        self.assertIn("not available in the browser build", out)


class TestExplore(unittest.TestCase):
    def test_catalogue(self):
        out = run("explore")
        self.assertIn("ch explore catalogue", out)
        for slug in ("id", "K", "S", "modus_ponens", "euler_identity"):
            self.assertIn(slug, out)

    def test_catalogue_order_matches_desktop(self):
        slugs = [t["id"] for t in data_ch_explore.THEOREMS]
        self.assertEqual(slugs[:5], ["id", "K", "S", "comp", "flip"])
        self.assertEqual(len(slugs), 16)

    def test_entry_card(self):
        out = run("explore modus_ponens")
        self.assertIn("ch explore - modus_ponens", out)
        self.assertIn("Modus ponens", out)
        self.assertIn("Proof term", out)
        self.assertIn("@ application", out)
        self.assertIn("hpq : P -> Q", out)
        self.assertIn("Tactic -> subterm mapping", out)
        self.assertIn("exact hpq p", out)
        self.assertIn("Pure lambda equivalent", out)
        self.assertIn(r"\p hpq. hpq p", out)

    def test_entry_tree_indices_are_preorder(self):
        out = run("explore id")
        self.assertIn("[0] λ {a : Type}", out)
        self.assertIn("[1] λ (x : a)", out)
        self.assertIn("[2] x : a", out)

    def test_unknown_slug(self):
        out = run("explore nothere")
        self.assertIn("Unknown entry `nothere`", out)

    def test_all_entries_render(self):
        for thm in data_ch_explore.THEOREMS:
            out = run(f"explore {thm['id']}")
            self.assertIn(f"ch explore - {thm['id']}", out)


class TestDispatcher(unittest.TestCase):
    def test_overview(self):
        out = run("")
        self.assertIn("Curry-Howard playground", out)
        self.assertIn("ch term <lambda>", out)
        self.assertIn("ch build <T>", out)

    def test_unknown_subcommand(self):
        out = run("wat")
        self.assertIn("Unknown sub-command `ch wat`", out)
        self.assertIn("term, type, lib, lean, from-lean, tactic, build, verify, explore", out)

    def test_output_uses_crlf(self):
        raw = ch.handle("", {})
        self.assertIn("\r\n", raw)
        self.assertNotIn("\n ", raw.replace("\r\n", "|"))

    def test_errors_do_not_escape(self):
        # Any internal failure must come back as text, never raise.
        out = run("type " + "(" * 300 + "P" + ")" * 300)
        self.assertIsInstance(out, str)

    def test_input_length_guard(self):
        out = run("term " + "x" * 5000)
        self.assertIn("too long", out)


if __name__ == "__main__":
    unittest.main()
