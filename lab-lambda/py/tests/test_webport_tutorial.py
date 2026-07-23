"""Tests for the browser port of the tutorial family.

Drives ``lambda_lab.lab.webport.tutorial.handle`` directly with a plain
state dict and asserts on ANSI-stripped output.
"""

from __future__ import annotations

import re
import unittest

from lambda_lab.lab.webport import tutorial
from lambda_lab.lab.webport.data_tutorials import CHAPTERS

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(s: str) -> str:
    return ANSI.sub("", s)


def run(arg: str, state: dict) -> str:
    return plain(tutorial.handle(arg, state))


def complete_chapter(state: dict, token: str, max_lines: int = 60) -> str:
    """Start a chapter and press ENTER until it completes. Returns last output."""
    out = run(token, state)
    for _ in range(max_lines):
        if not tutorial.is_active(state):
            return out
        out = run("", state)
    raise AssertionError("chapter did not complete within the line budget")


class TestFrozenData(unittest.TestCase):
    def test_twelve_chapters_in_order(self):
        self.assertEqual(len(CHAPTERS), 12)
        self.assertEqual([ch["order"] for ch in CHAPTERS], list(range(1, 13)))

    def test_every_chapter_has_valid_steps(self):
        valid = {"narrative", "command", "lean_walk", "quiz_checkpoint", "exercise", "kb"}
        for ch in CHAPTERS:
            self.assertTrue(ch["slug"])
            self.assertTrue(ch["title"])
            self.assertGreaterEqual(len(ch["steps"]), 6)
            for step in ch["steps"]:
                self.assertIn(step["kind"], valid)

    def test_lean_sources_frozen(self):
        for ch in CHAPTERS:
            walks = [s for s in ch["steps"] if s["kind"] == "lean_walk"]
            self.assertGreaterEqual(len(walks), 1, ch["slug"])
            for s in walks:
                self.assertIn("theorem", s["lean_source"])


class TestCatalog(unittest.TestCase):
    def test_list_shows_all_chapters(self):
        out = run("", {})
        self.assertIn("Lambda Lab tutorial - chapters", out)
        for ch in CHAPTERS:
            self.assertIn(ch["title"], out)
        self.assertIn("Type `tutorial 1`, `tutorial <slug>` or `tutorial next`.", out)

    def test_list_initial_status_not_started(self):
        out = run("list", {})
        self.assertEqual(out.count("not started"), 12)

    def test_help(self):
        out = run("help", {})
        self.assertIn("Tutorial - help", out)
        self.assertIn("tutorial next", out)
        self.assertIn("tutorial reset", out)
        self.assertIn("ENTER = advance, s = skip the step, q = quit", out)

    def test_unknown_chapter(self):
        out = run("nonexistent_slug", {})
        self.assertIn("I do not know chapter `nonexistent_slug`.", out)

    def test_progress_empty(self):
        out = run("progress", {})
        self.assertIn("No recorded attempts. Start with `tutorial 1`.", out)
        self.assertIn("Tutorial progress", out)


class TestChapterFlow(unittest.TestCase):
    def test_start_by_number_shows_header_and_first_step(self):
        state = {}
        out = run("1", state)
        self.assertIn("Chapter 1: Gauss's sum: 1 + 2 + ... + n", out)
        self.assertIn("Steps: 7, time: ~12 min.", out)
        self.assertIn("Controls: ENTER = next, s = skip step, q = quit", out)
        self.assertIn("Step 1/7", out)
        self.assertIn("The Gauss anecdote", out)
        self.assertIn("Karl Friedrich Gauss", out)  # narrative body rendered
        self.assertIn("[tutorial 1/7", out)  # post prompt after narrative
        self.assertTrue(tutorial.is_active(state))

    def test_start_by_slug(self):
        state = {}
        out = run("gauss_sum", state)
        self.assertIn("Chapter 1: Gauss's sum", out)
        self.assertEqual(state[tutorial.K_STATUS]["gauss_sum"], "in_progress")

    def test_gated_step_waits_before_running(self):
        state = {}
        run("1", state)
        out = run("", state)  # advance from narrative to command step
        self.assertIn("Step 2/7", out)
        self.assertIn("[ENTER to run this step · s to skip · q to quit]", out)
        # gate phase: body not yet shown
        self.assertNotIn("Running command:", out)
        out = run("", state)  # ENTER through the gate
        self.assertIn("Running command:", out)
        self.assertIn("tour church", out)
        self.assertIn("Desktop-only step:", out)
        self.assertIn("[tutorial 2/7", out)

    def test_gate_skip_moves_to_next_step(self):
        state = {}
        run("1", state)
        run("", state)          # to command step (gate)
        out = run("s", state)   # skip at the gate
        self.assertIn("Step skipped.", out)
        self.assertIn("Step 3/7", out)
        self.assertIn("Lean term walk", out)

    def test_lean_walk_shows_source_and_live_link(self):
        state = {}
        run("1", state)
        run("", state)          # command gate
        run("s", state)         # skip command -> lean_walk gate
        out = run("", state)    # run the lean_walk step
        self.assertIn("Lean source:", out)
        self.assertIn("theorem tutorial_gauss_sum", out)
        self.assertIn("induction n with", out)
        self.assertIn("https://live.lean-lang.org/#code=", out)
        self.assertIn("desktop Lean toolchain", out)

    def test_quiz_exercise_kb_intros(self):
        state = {}
        run("1", state)
        run("", state); run("s", state)      # skip command
        run("s", state)                        # skip lean_walk -> quiz gate
        out = run("", state)                   # run quiz step
        self.assertIn("Quiz bundle: `tutorial_01_gauss`.", out)
        self.assertIn("Pass threshold: 3 correct answers.", out)
        out = run("", state)                   # advance -> exercise gate
        self.assertIn("Step 5/7", out)
        out = run("", state)                   # run exercise step
        self.assertIn("Target: game `lambda_lab_tutorial`, world `exercises`, level 1.", out)
        out = run("", state)                   # advance -> kb step (ungated)
        self.assertIn("Step 6/7", out)
        self.assertIn("kb topic history", out)

    def test_reshow_and_controls_hint(self):
        state = {}
        run("1", state)
        out = run("?", state)
        self.assertIn("Step 1/7", out)   # re-shown header
        out = run("blahblah", state)
        self.assertIn("ENTER = advance, `s` = skip, `q` = quit, `?` = re-show.", out)
        self.assertTrue(tutorial.is_active(state))

    def test_quit_saves_in_progress(self):
        state = {}
        run("2", state)
        out = run("q", state)
        self.assertIn("Leaving the tutorial. Progress saved.", out)
        self.assertFalse(tutorial.is_active(state))
        self.assertEqual(state[tutorial.K_STATUS]["sqrt2_irrational"], "in_progress")
        self.assertIn("in progress", run("list", state))

    def test_full_chapter_completion(self):
        state = {}
        out = complete_chapter(state, "1")
        self.assertIn("Chapter complete", out)
        self.assertIn("chapter `Gauss's sum: 1 + 2 + ... + n` complete", out)
        self.assertEqual(state[tutorial.K_STATUS]["gauss_sum"], "complete")
        self.assertFalse(tutorial.is_active(state))
        self.assertIn("complete", run("progress", state))

    def test_completion_status_not_downgraded_by_rerun(self):
        state = {}
        complete_chapter(state, "1")
        run("1", state)         # re-open the completed chapter
        run("q", state)
        self.assertEqual(state[tutorial.K_STATUS]["gauss_sum"], "complete")


class TestNextAndReset(unittest.TestCase):
    def test_next_opens_first_unfinished(self):
        state = {}
        out = run("next", state)
        self.assertIn("Opening chapter 1: Gauss's sum: 1 + 2 + ... + n.", out)
        self.assertIn("Chapter 1:", out)
        run("q", state)
        complete_chapter(state, "1")
        out = run("next", state)
        self.assertIn("Opening chapter 2: The square root of 2 is irrational.", out)
        run("q", state)

    def test_next_all_done(self):
        state = {}
        for ch in CHAPTERS:
            state.setdefault(tutorial.K_STATUS, {})[ch["slug"]] = "complete"
        out = run("next", state)
        self.assertIn("All chapters complete. Congratulations!", out)

    def test_reset_clears_progress(self):
        state = {}
        complete_chapter(state, "1")
        out = run("reset", state)
        self.assertIn("Progress journal cleared.", out)
        self.assertNotIn(tutorial.K_STATUS, state)
        self.assertEqual(run("list", state).count("not started"), 12)


class TestOutputHygiene(unittest.TestCase):
    def test_lines_joined_with_crlf(self):
        raw = tutorial.handle("", {})
        self.assertIn("\r\n", raw)
        self.assertNotIn("\n ", raw.replace("\r\n", ""))  # no bare newlines

    def test_all_entry_outputs_nonempty(self):
        for arg in ("", "help", "progress", "reset", "next", "1", "list"):
            self.assertTrue(plain(tutorial.handle(arg, {})).strip(), arg)


if __name__ == "__main__":
    unittest.main()
