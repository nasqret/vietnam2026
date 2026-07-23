"""Tests for the browser port of the ``kb`` knowledge-base command.

Drives ``lambda_lab.lab.webport.kb.handle()`` directly and asserts on
ANSI-stripped output.
"""

from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lambda_lab.lab.webport import data_kb, kb


def out(arg: str, state: dict | None = None) -> str:
    """Run one kb line and return plain (ANSI-stripped, \n-joined) text."""
    raw = kb.handle(arg, state if state is not None else {})
    return re.sub(r"\x1b\[[0-9;]*m", "", raw).replace("\r\n", "\n")


# The inline KB keys of the original browser driver; each must keep resolving
# so the driver can swap implementations cleanly.
LEGACY_BROWSER_KEYS = [
    "beta-reduction", "alpha-equivalence", "substitution", "eta",
    "normal-form", "church-rosser", "church-encoding", "church-numeral",
    "y-combinator", "curry-howard", "type-judgment", "stlc",
    "dependent-type", "s-combinator", "lean", "autoformalization", "eml",
    "free-variables", "bhk", "natural-deduction", "intuitionistic",
    "church-vs-curry", "mltt", "four-foundations", "mathlib",
    "tactic-mode", "agda", "mizar",
]


class FrozenDataTests(unittest.TestCase):
    def test_registry_sizes(self):
        self.assertEqual(len(data_kb.TOPICS), 17)
        self.assertEqual(len(data_kb.RESOURCES), 121)
        self.assertEqual(len(data_kb.BUNDLES), 7)
        self.assertEqual(len(data_kb.CONCEPTS), 28)

    def test_frozen_data_within_size_cap(self):
        size = os.path.getsize(data_kb.__file__.replace(".pyc", ".py"))
        self.assertLessEqual(size, 155 * 1024)

    def test_canonical_and_bundle_references_exist(self):
        for tid, topic in data_kb.TOPICS.items():
            for rid in topic.get("canonical", ()):
                self.assertIn(rid, data_kb.RESOURCES, f"{tid} canonical {rid}")
            for other in topic.get("related_topics", ()):
                self.assertIn(other, data_kb.TOPICS, f"{tid} related {other}")
        for bid, bundle in data_kb.BUNDLES.items():
            for rid in bundle.get("resources", ()):
                self.assertIn(rid, data_kb.RESOURCES, f"{bid} resource {rid}")

    def test_concept_see_also_targets_are_topics(self):
        for key, (_title, _body, see) in data_kb.CONCEPTS.items():
            for tid in see:
                self.assertIn(tid, data_kb.TOPICS, f"{key} -> {tid}")

    def test_resource_invariants(self):
        kinds = {"book", "paper", "course", "website", "video", "blog",
                 "thesis", "documentation", "manual"}
        for rid, r in data_kb.RESOURCES.items():
            self.assertIn(r["kind"], kinds, rid)
            self.assertTrue(1 <= r["diff"] <= 5, rid)
            self.assertTrue(r["title"], rid)
            for tid in r.get("topics", ()):
                self.assertIn(tid, data_kb.TOPICS, f"{rid} topic {tid}")

    def test_no_polish_fields_frozen(self):
        for r in data_kb.RESOURCES.values():
            self.assertNotIn("abstract_pl", r)
            self.assertNotIn("why_pl", r)


class OverviewAndHelpTests(unittest.TestCase):
    def test_empty_arg_shows_overview_with_categories(self):
        text = out("")
        self.assertIn("Knowledge Base -- a literature companion", text)
        self.assertIn("17 topics", text)
        self.assertIn("121 resources", text)
        self.assertIn("7 bundles", text)
        # topic and concept listings by category
        self.assertIn("Topics", text)
        self.assertIn("lambda-calculus", text)
        self.assertIn("Concepts", text)
        self.assertIn("beta-reduction", text)
        self.assertIn("kb help", text)

    def test_help_lists_all_subcommands(self):
        text = out("help")
        for sub in ["kb topics", "kb topic <id>", "kb show <id>", "kb open <id>",
                    "kb search <kw>", "kb random", "kb bundles", "kb bundle <id>",
                    "kb path <topic_id>", "kb stats"]:
            self.assertIn(sub, text)


class TopicsTests(unittest.TestCase):
    def test_topics_table(self):
        text = out("topics")
        self.assertIn("Topics in the knowledge base", text)
        for tid in data_kb.TOPICS:
            self.assertIn(tid, text)

    def test_topic_detail_with_see_also_links(self):
        text = out("topic curry-howard")
        self.assertIn("Curry-Howard correspondence", text)
        self.assertIn("Programs ARE proofs", text)
        # the desktop's see-also links
        self.assertIn("Related topics:", text)
        self.assertIn("lambda-calculus", text)
        self.assertIn("Related REPL commands:", text)
        # readings table with canonical marker
        self.assertIn("Recommended readings (* = canon)", text)
        self.assertIn("wadler-2015-propositions-as-types", text)

    def test_topic_canonical_resources_come_first(self):
        text = out("topic curry-howard")
        first_canon = data_kb.TOPICS["curry-howard"]["canonical"][0]
        table = text[text.index("Recommended readings"):]
        rows = [ln for ln in table.splitlines() if re.match(r"\s*\*?\s+\S", ln)]
        first_row = next(ln for ln in table.splitlines() if ln.lstrip().startswith("*"))
        self.assertIn(first_canon, first_row)
        del rows

    def test_topic_filters(self):
        # Desktop behavior: the full topic view (canonical list included) is
        # printed first, then the filtered table.
        text = out("topic combinators --kind book --difficulty 1-2")
        filtered = text.split("Recommended readings (* = canon)")[-1]
        self.assertIn("smullyan-mockingbird", filtered)
        self.assertNotIn("schonfinkel-1924-bausteine", filtered)
        self.assertNotIn("selinger-lambda-notes", filtered)  # COURSE kind

    def test_topic_bad_difficulty(self):
        self.assertIn("Invalid difficulty range: x-y", out("topic combinators --difficulty x-y"))

    def test_topic_usage_and_unknown(self):
        self.assertIn("Usage: kb topic <id>", out("topic"))
        self.assertIn("Unknown topic: zzz", out("topic zzz"))


class ShowAndOpenTests(unittest.TestCase):
    RID = "wadler-2015-propositions-as-types"

    def test_show_resource_panel(self):
        text = out(f"show {self.RID}")
        self.assertIn("Propositions as Types", text)
        self.assertIn("Philip Wadler", text)
        self.assertIn("(2/5)", text)
        self.assertIn("Abstract", text)
        self.assertIn("Why it is here", text)
        self.assertIn("Follow-up:", text)
        self.assertIn("https://doi.org/10.1145/2699407", text)

    def test_show_degrades_open_gracefully(self):
        text = out(f"show {self.RID}")
        self.assertIn("Open in a new tab:", text)
        self.assertIn("cannot launch external programs", text)

    def test_open_prints_link_with_notice(self):
        text = out(f"open {self.RID}")
        self.assertIn("cannot launch external programs", text)
        self.assertIn("https://doi.org/10.1145/2699407", text)

    def test_show_usage_and_unknown(self):
        self.assertIn("Usage: kb show <id>", out("show"))
        self.assertIn("Unknown resource: zzz", out("show zzz"))
        self.assertIn("Unknown resource: zzz", out("open zzz"))


class SearchTests(unittest.TestCase):
    def test_search_finds_title_matches(self):
        text = out("search Curry-Howard")
        self.assertIn("Search results for: Curry-Howard", text)
        self.assertIn("sorensen-urzyczyn-curry-howard", text)

    def test_find_is_an_alias(self):
        self.assertIn("Search results for: mockingbird", out("find mockingbird"))

    def test_search_author(self):
        self.assertIn("wadler", out("search Wadler").lower())

    def test_search_kind_filter(self):
        text = out("search Curry-Howard --kind book")
        for line in text.splitlines()[3:]:
            if line.strip() and not line.strip().startswith(("-", "…", "Details")):
                self.assertIn("BOOK", line)

    def test_search_difficulty_filter(self):
        text = out("search lambda --difficulty 5")
        self.assertIn("Search results", text)
        self.assertNotIn("*....", text)

    def test_search_no_hits_and_usage(self):
        self.assertIn("No matches for: qqqqzzzz", out("search qqqqzzzz"))
        self.assertIn("Usage: kb search <keyword>", out("search"))


class RandomBundlePathStatsTests(unittest.TestCase):
    def test_random_recommendation(self):
        text = out("random")
        self.assertIn("Random recommendation", text)
        self.assertIn("Abstract", text)

    def test_random_respects_topic_flag(self):
        for _ in range(5):
            self.assertIn("mizar", out("random --topic mizar"))

    def test_random_unknown_topic_is_empty(self):
        self.assertIn("nothing to recommend", out("random --topic zzz"))

    def test_bundles_table(self):
        text = out("bundles")
        self.assertIn("Reading bundles", text)
        for bid in data_kb.BUNDLES:
            self.assertIn(bid, text)

    def test_bundle_detail(self):
        text = out("bundle beginner-lambda")
        self.assertIn("Reading order", text)
        self.assertIn("Audience:", text)
        self.assertIn("beginner", text)
        for rid in data_kb.BUNDLES["beginner-lambda"]["resources"]:
            self.assertIn(rid, text)

    def test_bundle_usage_and_unknown(self):
        self.assertIn("Usage: kb bundle <id>", out("bundle"))
        self.assertIn("Unknown bundle: zzz", out("bundle zzz"))

    def test_path_canonical_first_and_max(self):
        text = out("path combinators --max 4")
        self.assertIn("Reading path: combinators", text)
        steps = [ln for ln in text.splitlines() if re.match(r"\s*\d+\s+\S", ln)]
        self.assertEqual(len(steps), 4)
        first_canon = data_kb.TOPICS["combinators"]["canonical"][0]
        self.assertIn(first_canon, steps[0])

    def test_path_usage_and_unknown(self):
        self.assertIn("Usage: kb path <topic_id>", out("path"))
        self.assertIn("Unknown topic: zzz", out("path zzz"))

    def test_stats(self):
        text = out("stats")
        self.assertIn("Knowledge base statistics", text)
        self.assertIn("Topics: 17", text)
        self.assertIn("Resources: 121", text)
        self.assertIn("Bundles: 7", text)
        for section in ["By kind", "By topic", "By difficulty", "By license"]:
            self.assertIn(section, text)


class ConceptLookupTests(unittest.TestCase):
    def test_all_legacy_browser_keys_still_resolve(self):
        for key in LEGACY_BROWSER_KEYS:
            text = out(key)
            self.assertNotIn("No entry", text, key)
            title = data_kb.CONCEPTS[key][0]
            self.assertIn(title.splitlines()[0], text, key)

    def test_concept_body_and_see_also(self):
        text = out("beta-reduction")
        self.assertIn("β-reduction", text)
        self.assertIn("(λx.t) u → t[x:=u]", text)
        self.assertIn("kb topic lambda-calculus", text)

    def test_spaces_normalize_to_hyphens(self):
        self.assertIn("Curry–Howard correspondence", out("curry howard"))

    def test_prefix_fuzzy_match(self):
        # First concept key starting with "church" (dict order, exactly like
        # the original browser KB) is church-rosser.
        self.assertIn("Church–Rosser (confluence)", out("church"))

    def test_prefix_fuzzy_match_falls_through_to_topics(self):
        # No concept key starts with "combinator", but the combinators topic does.
        text = out("combinator")
        self.assertIn("Combinators", text)
        self.assertIn("Recommended readings", text)

    def test_topic_id_lookup_without_subcommand(self):
        text = out("lambda-calculus")
        self.assertIn("Recommended readings", text)

    def test_resource_id_lookup_without_subcommand(self):
        text = out("wadler-2015-propositions-as-types")
        self.assertIn("Propositions as Types", text)
        self.assertIn("Abstract", text)

    def test_unknown_entry(self):
        text = out("nonsense-qqq-zzz")
        self.assertIn("No entry for 'nonsense-qqq-zzz'", text)
        self.assertIn("kb search <text>", text)


class HandleContractTests(unittest.TestCase):
    def test_state_is_untouched(self):
        state = {"other": 1}
        kb.handle("topic curry-howard", state)
        kb.handle("", state)
        self.assertEqual(state, {"other": 1})

    def test_state_may_be_none(self):
        self.assertIn("Knowledge Base", out("", state=None) or out(""))

    def test_bad_quoting_reports_parse_error(self):
        self.assertIn("Argument parsing error", out('search "unclosed'))

    def test_returns_crlf_joined_ansi_text(self):
        raw = kb.handle("topics", {})
        self.assertIn("\r\n", raw)
        self.assertIn("\x1b[", raw)


if __name__ == "__main__":
    unittest.main()
