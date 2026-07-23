"""Tests for the browser port of the ``alligators`` command."""

from __future__ import annotations

import re
import unittest

from lambda_lab.lab.webport import _ansi
from lambda_lab.lab.webport.alligators import handle

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(s: str) -> str:
    return _ANSI.sub("", s)


class TestAlligatorsHandle(unittest.TestCase):
    def test_empty_arg_shows_usage(self):
        out = plain(handle("", {}))
        self.assertIn("Usage: alligators <term>", out)

    def test_whitespace_arg_shows_usage(self):
        out = plain(handle("   ", {}))
        self.assertIn("Usage: alligators <term>", out)

    def test_variable_is_an_egg(self):
        out = plain(handle("x", {}))
        self.assertIn("🥚 x", out)
        self.assertIn("Alligator Eggs view", out)

    def test_lambda_is_a_hungry_alligator(self):
        out = plain(handle("\\x. x", {}))
        self.assertIn("hungry «x»", out)
        self.assertIn("🥚 x", out)

    def test_application_is_a_family_with_feeding_arrow(self):
        out = plain(handle("(\\x. x) y", {}))
        self.assertIn("family (application)", out)
        self.assertIn("⇣ feeding ⇣", out)
        self.assertIn("hungry «x»", out)
        self.assertIn("🥚 y", out)

    def test_constant_true_expands_to_lambdas(self):
        out = plain(handle("TRUE", {}))
        self.assertIn("hungry «t»", out)
        self.assertIn("hungry «f»", out)
        self.assertIn("🥚 t", out)

    def test_numeral_expands_to_church_numeral(self):
        out = plain(handle("2", {}))
        self.assertIn("hungry «f»", out)
        self.assertIn("hungry «x»", out)
        self.assertIn("🥚 x", out)

    def test_legend_is_shown(self):
        out = plain(handle("x", {}))
        self.assertIn("every green square is a hungry alligator", out)
        self.assertIn("An egg (🥚) is a variable", out)

    def test_parse_error(self):
        out = plain(handle("(", {}))
        self.assertTrue(out.startswith("Parse error:"), out)

    def test_negative_numeral_rejected(self):
        out = plain(handle("-3", {}))
        self.assertIn("must be non-negative", out)

    def test_oversized_numeral_rejected(self):
        out = plain(handle("99", {}))
        self.assertIn("too large for the browser", out)

    def test_huge_term_hits_node_cap(self):
        out = plain(handle(" ".join(["x"] * 500), {}))
        self.assertIn("too many alligators", out)

    def test_lines_joined_with_crlf(self):
        raw = handle("\\x. x", {})
        self.assertIn("\r\n", raw)

    def test_state_is_untouched(self):
        state: dict = {"other": 1}
        handle("\\x. x", state)
        self.assertEqual(state, {"other": 1})

    def test_nested_boxes_for_church_numeral_2_shape(self):
        # λf x. f (f x): outer panel + two hungry boxes + application families.
        out = plain(handle("(\\f x. f (f x))", {}))
        self.assertEqual(out.count("hungry «f»"), 1)
        self.assertEqual(out.count("hungry «x»"), 1)
        self.assertEqual(out.count("family (application)"), 2)


class TestBoxRenderer(unittest.TestCase):
    def test_ascii_box_lines_align(self):
        rows = _ansi.box(["short", "a longer line"], title="T", border_fn=_ansi.green, pad_x=2)
        widths = {len(plain(r)) for r in rows}
        self.assertEqual(len(widths), 1, rows)
        self.assertTrue(plain(rows[0]).startswith("╭"))
        self.assertTrue(plain(rows[-1]).startswith("╰"))

    def test_box_title_embedded_in_top_border(self):
        rows = _ansi.box(["body"], title="Hello", pad_x=1)
        self.assertIn("Hello", plain(rows[0]))


if __name__ == "__main__":
    unittest.main()
