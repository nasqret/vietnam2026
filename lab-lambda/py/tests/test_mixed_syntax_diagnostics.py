"""Coercion blindness fix: mixing term syntax and type syntax must produce a
diagnostic that names both worlds — never a bare 'unexpected character'."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import driver  # noqa: E402


def strip(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


class MixedSyntaxDiagnostics(unittest.TestCase):
    def run_cmd(self, session, line):
        return strip(session.run(line))

    def test_arrow_in_term_positions(self):
        s = driver.LabSession()
        for cmd in ("lam \\Q -> Q", "nf \\Q -> Q", "reduce \\p -> p",
                    "equiv \\Q -> Q = \\x. x", "ch term \\Q -> Q"):
            out = self.run_cmd(s, cmd)
            self.assertIn("TYPE syntax", out, cmd)
            self.assertIn("dot", out, cmd)

    def test_unicode_arrow_in_term(self):
        out = self.run_cmd(driver.LabSession(), "nf λq → q")
        self.assertIn("TYPE syntax", out)

    def test_lean_fat_arrow_in_term(self):
        out = self.run_cmd(driver.LabSession(), "nf fun q => q")
        self.assertIn("Lean syntax", out)
        self.assertIn("ch lean", out)

    def test_lambda_in_type_positions(self):
        s = driver.LabSession()
        for cmd in ("ch type \\Q -> Q", "prove \\Q -> Q", "prove λq. q"):
            out = self.run_cmd(s, cmd)
            self.assertIn("lambda-TERM syntax", out, cmd)
            self.assertIn("ch term", out, cmd)
            if "Proof builder" in out:
                s.run("abort")

    def test_dot_in_type(self):
        out = self.run_cmd(driver.LabSession(), "prove P . Q")
        self.assertIn("dots", out)
        self.assertIn("P -> Q", out)

    def test_tactic_term_with_fat_arrow(self):
        s = driver.LabSession()
        s.run("prove P -> P")
        out = self.run_cmd(s, "exact fun p => p")
        self.assertIn("Lean syntax", out)
        s.run("abort")

    def test_valid_inputs_unaffected(self):
        s = driver.LabSession()
        self.assertIn("β-normal form", self.run_cmd(s, "nf \\q. q"))
        self.assertIn("Proof builder", self.run_cmd(s, "prove P -> Q"))
        s.run("abort")
        self.assertIn("step", self.run_cmd(s, "nf PLUS 1 1"))

    def test_plain_bad_char_message_survives(self):
        out = self.run_cmd(driver.LabSession(), "nf a % b")
        self.assertIn("Unexpected character", out)


if __name__ == "__main__":
    unittest.main()
