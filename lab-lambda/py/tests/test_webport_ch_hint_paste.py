"""Regression: ch build must accept the very terms its own `hint` suggests.

The goal's atoms (P, Q) are rigid constants; a term's principal type carries
fresh variables (α, β) — `exact` must accept when the goal is an *instance*
of the principal type, not demand pretty-printed equality.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import driver  # noqa: E402


def strip(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


class ChHintPasteBack(unittest.TestCase):
    def session(self):
        return driver.LabSession()

    def test_hint_suggestion_is_accepted_by_exact(self):
        s = self.session()
        s.run("ch build P -> Q -> P")
        hint = strip(s.run("hint"))
        m = re.search(r"`exact ([^`]+)`", hint)
        self.assertIsNotNone(m, hint)
        out = strip(s.run(f"exact {m.group(1)}"))
        self.assertIn("All goals closed", out)
        self.assertIn("Final lambda-term", out)

    def test_uppercase_binder_names_are_fine(self):
        s = self.session()
        s.run("ch build P -> Q -> P")
        self.assertIn("All goals closed", strip(s.run("exact λP Q. P")))

    def test_wrong_term_still_rejected(self):
        s = self.session()
        s.run("ch build P -> Q -> P")
        out = strip(s.run("exact λp. p"))
        self.assertIn("Tactic error", out)
        s.run("quit")

    def test_polymorphic_apply_instantiates_subgoals_and_assumption_closes(self):
        s = self.session()
        s.run("ch build P -> Q -> P")
        s.run("intro p")
        s.run("intro q")
        first = strip(s.run("apply λx y. x"))
        self.assertIn("Goal 1/2", first)
        self.assertIn("P", first)          # first subgoal instantiated to P
        strip(s.run("assumption"))
        out = strip(s.run("assumption"))
        self.assertIn("All goals closed", out)

    def test_session_cleans_up_after_completion(self):
        s = self.session()
        s.run("ch build P -> Q -> P")
        s.run("exact λp q. p")
        self.assertFalse(s.webstate.get("ch.interactive"))


if __name__ == "__main__":
    unittest.main()
