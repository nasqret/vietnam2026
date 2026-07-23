"""The free-variable guardrail: constant-shaped names that are neither
built-ins nor session defs get a hint (lost `let` after reload, or a typo)."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import driver  # noqa: E402


def strip(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


class UndefinedNameHintTests(unittest.TestCase):
    def test_equiv_with_lost_let_shows_hint(self):
        out = strip(driver.LabSession().run("equiv MIN 4 2 = 2"))
        self.assertIn("different β-normal forms", out)
        self.assertIn("MIN: not defined here", out)
        self.assertIn("Reloading clears definitions", out)

    def test_defined_name_silences_hint(self):
        s = driver.LabSession()
        s.run(r"let MIN = \m. \n. IF (LEQ m n) m n")
        out = strip(s.run("equiv MIN 4 2 = 2"))
        self.assertIn("equal β-normal forms", out)
        self.assertNotIn("⚠", out)

    def test_typoed_constant_caught_in_nf(self):
        out = strip(driver.LabSession().run("nf TRU"))
        self.assertIn("TRU: not defined here", out)

    def test_lowercase_free_vars_stay_silent(self):
        for cmd in ("nf x y", "reduce \\x. x y z", "whnf f a"):
            out = strip(driver.LabSession().run(cmd))
            self.assertNotIn("⚠", out, cmd)

    def test_reduce_decode_whnf_all_hint(self):
        for cmd in ("reduce MIN 1 0", "decode MYNUM", "whnf FOO x"):
            out = strip(driver.LabSession().run(cmd))
            self.assertIn("not defined here", out, cmd)

    def test_bound_uppercase_names_do_not_hint(self):
        # \TRUE. TRUE binds the name — no free constant-shaped variable remains
        out = strip(driver.LabSession().run("nf \\MIN. MIN"))
        self.assertNotIn("⚠", out)


if __name__ == "__main__":
    unittest.main()
