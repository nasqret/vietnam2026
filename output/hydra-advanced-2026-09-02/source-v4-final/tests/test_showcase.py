"""Gallery admission fails closed on stale, ambiguous or unverified artifacts.

The small synthetic transport fixture is not a mathematical proof claim.
Actual publication separately requires a completed search and native replay.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import server
import worker


class ShowcaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="hydra-showcase-test-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.patch = patch.object(server, "SHOWCASE", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        request = {"theorem": "0 = 0", "search_mode": "hybrid", "search_profile": "deep",
                   "max_model_calls": 32, "beam_width": 4}
        result = {"status": "proved", "kernel_checked": True, "theorem": "0 = 0", "goals": [],
                  "proof_nodes": 1, "commands": ["refl"], "kind": "hybrid", "trace": [],
                  "kernel_source_commit": worker.SOURCE_COMMIT, "proof_sources": {"heuristic": 1},
                  "search": {"model_calls": 0, "vampire_calls": 0}}
        self.record = {"schema": "hydra-showcase-proof-v1", "case_id": "fixture", "theorem": "0 = 0",
                       "request": request, "result": result,
                       "verification": {key: result[key] for key in ("status", "kernel_checked", "theorem", "proof_nodes")}}
        self.case = {"id": "fixture", "artifact_file": "fixture.json", "kernel_verified": True,
                     "independent_replay": True, "theorem": "0 = 0", "canonical_theorem": "0 = 0",
                     "proof_nodes": 1, "proof_steps": 1, "search_mode": "hybrid", "search_profile": "deep",
                     "proof_sources": {"heuristic": 1}, "model_calls": 0, "vampire_calls": 0}
        self.write_record()

    def write_record(self):
        raw = worker.json_bytes(self.record)
        (self.root / "fixture.json").write_bytes(raw)
        self.case["artifact_sha256"] = hashlib.sha256(raw).hexdigest()
        self.write_catalog()

    def write_catalog(self, cases=None):
        (self.root / "manifest.json").write_text(json.dumps({"schema": "hydra-verified-showcase-v1",
                                                             "cases": [self.case] if cases is None else cases}))

    def test_exact_pinned_record_is_accepted_but_changed_file_is_not_advertised(self):
        self.assertEqual(server.showcase_record("fixture"), self.record)
        (self.root / "fixture.json").write_bytes(worker.json_bytes(self.record) + b"\n")
        with self.assertRaises(server.RequestError):
            server.showcase_catalog()

    def test_claimed_success_requires_matching_independent_replay_and_counts(self):
        for category, field, value in (("verification", "kernel_checked", False),
                                      ("result", "goals", ["unproved"]),
                                      ("result", "proof_nodes", 2),
                                      ("request", "search_profile", "research")):
            with self.subTest(category=category, field=field):
                original = self.record[category][field]
                self.record[category][field] = value
                self.write_record()
                with self.assertRaises(server.RequestError):
                    server.showcase_catalog()
                self.record[category][field] = original

    def test_duplicate_and_undeclared_path_entries_are_rejected(self):
        self.write_catalog([self.case, self.case])
        with self.assertRaises(server.RequestError):
            server.showcase_catalog()
        self.case["artifact_file"] = "../worker.py"
        self.write_catalog()
        with self.assertRaises(server.RequestError):
            server.showcase_catalog()


if __name__ == "__main__":
    unittest.main()
