"""Box-drawing alignment: every row of a framed panel must have identical
display width.

The frames mix emoji (2 cells under Unicode 11 — the front-end activates
xterm's unicode11 addon to match) with box-drawing characters; any padding
mistake shows up as a mismatched right border.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lambda_lab.lab.webport import _ansi as A          # noqa: E402
from lambda_lab.lab.webport import alligators, ag      # noqa: E402


def top_level_panels(out: str):
    """Group framed rows into top-level panels.

    Only an outermost border starts its line with ╭/╰ — nested boxes sit
    inside │…│ rows — so panels are delimited by line-initial ╭ … ╰ pairs.
    """
    rows = [r.rstrip() for r in A.strip_ansi(out).split("\r\n") if r.strip()]
    panels, current = [], None
    for r in rows:
        head = r.lstrip()[:1]
        if head == "╭" and current is None:
            current = [r]
        elif current is not None and head in ("│", "╰", "╭"):
            current.append(r)
            if head == "╰":
                panels.append(current)
                current = None
    if current:
        panels.append(current)
    return panels


class AlignmentTests(unittest.TestCase):
    def assert_aligned(self, out: str, label: str):
        panels = top_level_panels(out)
        self.assertTrue(panels, f"{label}: no frame found")
        for panel in panels:
            widths = {A.display_width(r) for r in panel}
            self.assertEqual(
                len(widths), 1,
                f"{label}: mismatched widths {sorted(widths)} in panel:\n"
                + "\n".join(panel[:10]),
            )

    def test_alligators_simple(self):
        self.assert_aligned(alligators.handle(r"\x. x", {}), "identity")

    def test_alligators_application(self):
        self.assert_aligned(alligators.handle(r"(\x. x x) (\y. y)", {}), "application")

    def test_alligators_named_constant(self):
        self.assert_aligned(alligators.handle("AND", {}), "AND expanded")

    def test_alligators_deep_nesting(self):
        self.assert_aligned(alligators.handle(r"\f. (\x. f (x x)) (\x. f (x x))", {}), "Y-shape")

    def test_ag_panels(self):
        self.assert_aligned(ag.handle("angle_bisector", {}), "ag replay")

    def test_display_width_emoji(self):
        self.assertEqual(A.display_width("🐊"), 2)
        self.assertEqual(A.display_width("🥚 x"), 4)
        self.assertEqual(A.display_width("⇣ feeding ⇣"), 11)
        self.assertEqual(A.display_width(A.green("🐊 hungry «x»")), 13)


if __name__ == "__main__":
    unittest.main()
