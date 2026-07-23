"""Per-command help pages: every command documented, every topic renders."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import driver  # noqa: E402


def strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s).replace("\r\n", "\n")


class HelpTopicTests(unittest.TestCase):
    def setUp(self):
        self.s = driver.LabSession()

    def run_cmd(self, line):
        return strip_ansi(self.s.run(line))

    def test_every_topic_renders_with_syntax_and_examples(self):
        for topic, entry in driver.HELP_TOPICS.items():
            out = self.run_cmd(f"help {topic}")
            self.assertNotIn("No help topic", out, topic)
            self.assertIn(entry["syntax"].split()[0], out, topic)
            if entry.get("examples"):
                self.assertIn("Examples", out, topic)

    def test_every_command_has_a_topic_or_alias(self):
        cmds = {m[4:] for m in dir(self.s) if m.startswith("cmd_")}
        undocumented = {
            c for c in cmds
            if c not in driver.HELP_TOPICS and c not in driver.HELP_ALIASES
            and c not in ("commands", "red", "r")
        }
        self.assertFalse(undocumented, f"commands lacking help: {undocumented}")

    def test_alias_and_prefix_lookup(self):
        self.assertIn("reduce", self.run_cmd("help red"))
        self.assertIn("lean", self.run_cmd("help le"))
        self.assertIn("equiv", self.run_cmd("help eq"))

    def test_unknown_topic_is_graceful(self):
        out = self.run_cmd("help zzznope")
        self.assertIn("No help topic", out)

    def test_overview_advertises_topic_help(self):
        self.assertIn("help <command>", self.run_cmd("help"))

    def test_alpha_topic_teaches_the_shadowing_trap(self):
        out = self.run_cmd("help alpha")
        self.assertIn("\\x. \\x. x", out)
        self.assertIn("equiv", out)


if __name__ == "__main__":
    unittest.main()
