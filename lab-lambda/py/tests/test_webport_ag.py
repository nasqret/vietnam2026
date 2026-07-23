"""Tests for the browser port of the ``ag`` (AlphaGeometry replay) command."""

from __future__ import annotations

import re
import unittest

from lambda_lab.lab.webport.ag import handle
from lambda_lab.lab.webport.data_ag import PROOFS

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(s: str) -> str:
    return _ANSI.sub("", s)


class TestAgList(unittest.TestCase):
    def test_lists_all_frozen_demos(self):
        out = plain(handle("", {}))
        self.assertIn("Available demos", out)
        for name in ("angle_bisector", "imo_p4", "isogonal"):
            self.assertIn(name, out)

    def test_list_shows_usage_hint(self):
        out = plain(handle("", {}))
        self.assertIn("ag angle_bisector", out)

    def test_unknown_demo(self):
        out = plain(handle("nope", {}))
        self.assertIn("Unknown demo: nope", out)
        self.assertIn("angle_bisector", out)
        self.assertIn("imo_p4", out)
        self.assertIn("isogonal", out)


class TestAngleBisectorReplay(unittest.TestCase):
    def setUp(self):
        self.out = plain(handle("angle_bisector", {}))

    def test_title_and_sections(self):
        self.assertIn("isosceles triangle", self.out)
        self.assertIn("Problem", self.out)
        self.assertIn("Diagram", self.out)
        self.assertIn("Auxiliary construction (LM)", self.out)
        self.assertIn("Conclusion", self.out)

    def test_all_three_steps_render_in_order(self):
        self.assertEqual(self.out.count("DD+AR step #"), 3)
        i1, i2, i3 = (self.out.index(f"DD+AR step #{i}") for i in (1, 2, 3))
        self.assertTrue(i1 < i2 < i3)

    def test_step_content(self):
        self.assertIn("AB = AC (assumption)", self.out)
        self.assertIn("SAS (side-angle-side)", self.out)
        self.assertIn("△ABD ≅ △ACD", self.out)
        self.assertIn("∠ADB = 90°", self.out)
        self.assertIn("AR module", self.out)

    def test_step_rows_labelled(self):
        for label in ("premises", "rule", "conclusion", "why"):
            self.assertIn(label, self.out)

    def test_ascii_diagram_preserved(self):
        self.assertIn("B---D----C", self.out)

    def test_final_conclusion(self):
        self.assertIn("AD ⟂ BC. ◻", self.out)

    def test_pagination_notice(self):
        self.assertIn("pauses for ENTER between steps", self.out)


class TestOtherReplays(unittest.TestCase):
    def test_imo_p4_has_four_steps(self):
        out = plain(handle("imo_p4", {}))
        self.assertEqual(out.count("DD+AR step #"), 4)
        self.assertIn("Thales", out)
        self.assertIn("tangent to Ω at A", out)
        self.assertIn("B------C", out)

    def test_isogonal_has_two_steps(self):
        out = plain(handle("isogonal", {}))
        self.assertEqual(out.count("DD+AR step #"), 2)
        self.assertIn("isogonal", out)
        self.assertIn("AR — distance algebra", out)

    def test_arg_is_stripped(self):
        out = plain(handle("  isogonal  ", {}))
        self.assertIn("DD+AR step #1", out)


class TestPlumbing(unittest.TestCase):
    def test_lines_joined_with_crlf(self):
        raw = handle("angle_bisector", {})
        self.assertIn("\r\n", raw)

    def test_state_is_untouched(self):
        state: dict = {"k": "v"}
        handle("angle_bisector", state)
        handle("", state)
        self.assertEqual(state, {"k": "v"})

    def test_frozen_data_shape(self):
        for name, data in PROOFS.items():
            self.assertIn("title", data, name)
            self.assertIn("steps", data, name)
            for step in data["steps"]:
                self.assertIn("rule", step, name)
                self.assertIn("conclusion", step, name)

    def test_step_panel_lines_align(self):
        # Step panels are pure BMP text, so stripped rows must be equal length.
        out = plain(handle("angle_bisector", {}))
        block = []
        capture = False
        for line in out.split("\r\n"):
            if "DD+AR step #2" in line:
                capture = True
            if capture:
                block.append(line)
                if line.strip().startswith("╰"):
                    break
        self.assertTrue(block, "step #2 panel not found")
        widths = {len(line) for line in block}
        self.assertEqual(len(widths), 1, block)


if __name__ == "__main__":
    unittest.main()
