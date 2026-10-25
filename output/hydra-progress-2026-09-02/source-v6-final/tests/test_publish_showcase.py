"""Synthetic, temporary provenance fixtures only; no native/HTTP/model/solver jobs."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import publish_showcase as publisher
import evaluate_advanced as experiments
import server
import worker


def put(path, value):
    path.write_bytes(publisher.json_bytes(value))


class ShowcasePublisherTests(unittest.TestCase):
    def fixture(self, directory):
        path = directory / "000-fixture-heuristic.json"
        request = {"theorem": "0=0", "max_model_calls": 8, "beam_width": 1,
                   "search_mode": "heuristic", "search_profile": "standard"}
        normalized = worker.validate_request("search", request)
        jobid = "a" * 32
        result = {"kind": "heuristic", "status": "proved", "kernel_checked": True,
            "theorem": "0 = 0", "goals": [], "commands": ["refl"], "proof_nodes": 1,
            "kernel_source_commit": worker.SOURCE_COMMIT, "settings_profile": "standard",
            "proof_sources": {"heuristic": 1}, "search": {"model_calls": 0, "vampire_calls": 0,
                "provenance": [{"command": "refl", "source": "heuristic"}]},
            "execution": {"quiescent": True, "elapsed_seconds": 0.1}}
        put(directory / "source-pins.json", {"kernel_commit": worker.SOURCE_COMMIT})
        plan = {"schema": experiments.PLAN_SCHEMA, "origin": "live_http_search",
            "source_pins": publisher.descriptor(directory / "source-pins.json"),
            "reference_scripts_sent_to_server": False,
            "jobs": [{"case_id": "fixture", "mode": "heuristic", "request": request,
                      "canonical_theorem": "0 = 0"}]}
        put(directory / "plan.json", plan)
        record = {"schema": experiments.CASE_SCHEMA, "origin": "live_http_search",
            "record_file": path.name, "case_id": "fixture", "case_metadata": {"title": "SYNTHETIC TEST FIXTURE"},
            "expected": "provable", "outcome": "proved", "automatic_retry": False,
            "reference_scripts_sent_to_server": False, "request": request,
            "normalized_request": normalized, "canonical_theorem": "0 = 0",
            "search_mode": "heuristic", "search_profile": "standard",
            "run_context": {"plan_sha256": publisher.descriptor(directory / "plan.json")["sha256"],
                            "source_pins_sha256": publisher.descriptor(directory / "source-pins.json")["sha256"]},
            "job_id": jobid, "submission_count": 1, "submission_http_status": 202,
            "submission_response": {"ok": True, "job_id": jobid},
            "submitted_at_utc": "2026-01-01T00:00:00+00:00", "finished_at_utc": "2026-01-01T00:00:01+00:00",
            "server_elapsed_seconds": 0.2,
            "last_job": {"id": jobid, "state": "completed", "result": result, "error": None}}
        put(path, record)
        summary = {"schema": experiments.SUMMARY_SCHEMA, "status": "complete",
                   "source_pins_unchanged": True, "case_file_pins": {path.name: publisher.descriptor(path)}}
        put(directory / "summary.json", summary)
        return path, record

    def candidate(self, directory):
        path, record = self.fixture(directory)
        return publisher.inspect_live_record(path, lambda _: "0 = 0")

    def replay_fixture(self, candidate):
        result = candidate["result"]
        return {"actual_child_exit_code": 0, "native_seconds": 0.01, "quiescent": True,
            "result": {"status": "proved", "kernel_checked": True, "goals": [],
                "theorem": result["theorem"], "commands": list(result["commands"]),
                "proof_nodes": result["proof_nodes"], "kernel_source_commit": worker.SOURCE_COMMIT}}

    def test_reference_audit_is_ineligible_even_if_it_contains_a_checked_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.json"
            put(path, {"schema": "hydra-advanced-native-curriculum-audit-v1", "kernel_checked": True})
            with self.assertRaisesRegex(ValueError, "reference/manual audits"):
                publisher.inspect_live_record(path, lambda s: s)

    def test_completed_live_provenance_is_bound_to_plan_and_final_file_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path, record = self.fixture(Path(directory))
            self.assertTrue(publisher.inspect_live_record(path, lambda _: "0 = 0")["eligible"])
            record["submission_count"] = 2
            put(path, record)
            with self.assertRaisesRegex(ValueError, "exact case-file hash"):
                publisher.inspect_live_record(path, lambda _: "0 = 0")

    def test_running_or_changed_source_run_cannot_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path, record = self.fixture(base)
            summary = json.loads((base / "summary.json").read_text())
            summary["source_pins_unchanged"] = None
            put(base / "summary.json", summary)
            with self.assertRaisesRegex(ValueError, "not finalized"):
                publisher.inspect_live_record(path, lambda _: "0 = 0")

    def test_full_replay_script_and_node_count_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = self.candidate(Path(directory))
            for field, value in (("commands", ["simp"]), ("proof_nodes", 2), ("kernel_checked", False)):
                replay = self.replay_fixture(candidate)
                replay["result"][field] = value
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, "Fresh independent replay"):
                    publisher.make_entry(candidate, replay, {})

    def test_step_sources_are_derived_from_commands_not_advisor_call_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = self.candidate(Path(directory))
            result = candidate["result"]
            result["search"]["model_calls"] = 8
            self.assertEqual(publisher.proof_sources(result)[0], {"heuristic": 1})
            result["proof_sources"] = {"model": 1}
            with self.assertRaisesRegex(ValueError, "Step-source counts"):
                publisher.proof_sources(result)

    def test_missing_original_model_step_attribution_is_not_fabricated(self):
        result = {"kind": "model", "commands": ["intro n", "refl"], "search": {"model_calls": 4}}
        sources, notes = publisher.proof_sources(result)
        self.assertEqual(sources, {"unattributed": 2})
        self.assertTrue(notes)

    def test_parent_rss_supervision_kills_only_the_owned_mock_child_and_records_exit(self):
        class Child:
            pid = 424242
            returncode = None
            def kill(self):
                self.returncode = -9
            def poll(self):
                return self.returncode
            def communicate(self, **kwargs):
                return b"", b""
        child = Child()
        rows = {child.pid: (123, child.pid, 3 * 1024**3, ("owned-birth",))}
        with patch.object(server, "process_snapshot", side_effect=[{}, rows, {}]), \
             patch.object(server, "_kill", side_effect=lambda process, known: process.kill()) as kill, \
             patch.object(publisher.subprocess, "Popen", return_value=child):
            replay = publisher.run_replay({"theorem": "0=0", "tactics": ["refl"]}, time.monotonic()+120)
        self.assertEqual(replay["actual_child_exit_code"], -9)
        self.assertEqual(replay["peak_sampled_rss_bytes"], 3 * 1024**3)
        self.assertIn("2 GiB", replay["supervision_error"])
        self.assertTrue(replay["quiescent"])
        self.assertIs(kill.call_args.args[0], child)
        self.assertEqual(set(kill.call_args.args[1]), {child.pid})

    def test_missing_process_accounting_blocks_native_spawn(self):
        with patch.object(server, "process_snapshot", side_effect=RuntimeError("ps denied")), \
             patch.object(publisher.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(RuntimeError, "ps denied"):
                publisher.run_replay({"theorem": "0=0", "tactics": ["refl"]}, time.monotonic()+120)
        spawn.assert_not_called()

    def test_curation_allows_only_editorial_fields_and_keeps_execution_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            candidate = self.candidate(base)
            path = base / "curation.json"
            curation = {"schema": "hydra-showcase-curation-v1", "cases": {"fixture": {
                "title": "Curated title", "display": "0 = 0", "description": "Public copy", "tags": ["arithmetic"]}}}
            put(path, curation)
            overrides, pin = publisher.read_curation(path)
            entry, artifact, _ = publisher.make_entry(candidate, self.replay_fixture(candidate), {}, overrides, pin)
            self.assertEqual(entry["title"], "Curated title")
            self.assertEqual(entry["proof_nodes"], 1)
            self.assertIn("heuristic", entry["tags"])
            self.assertIn("exposed probe", entry["tags"])
            self.assertEqual(artifact["curation"]["file"]["sha256"], publisher.descriptor(path)["sha256"])
            curation["cases"]["fixture"]["proof_nodes"] = 999
            put(path, curation)
            with self.assertRaisesRegex(ValueError, "only title"):
                publisher.read_curation(path)

    def test_staged_record_matches_server_contract_and_mismatched_badges_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            candidate = self.candidate(base)
            entry, artifact, raw = publisher.make_entry(candidate, self.replay_fixture(candidate), {})
            stage = base / "stage"
            stage.mkdir()
            (stage / entry["artifact_file"]).write_bytes(raw)
            manifest = {"schema": "hydra-verified-showcase-v1", "cases": [entry], "note": "SYNTHETIC TEST"}
            put(stage / "manifest.json", manifest)
            self.assertEqual(publisher.validate_staged(stage)["cases"][0]["proof_sources"], {"heuristic": 1})
            manifest["cases"][0]["model_calls"] = 99
            put(stage / "manifest.json", manifest)
            with self.assertRaises(server.RequestError):
                publisher.validate_staged(stage)

    def test_publication_only_writes_explicit_temporary_destination_and_preserves_old_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            candidate = self.candidate(base)
            entry, artifact, raw = publisher.make_entry(candidate, self.replay_fixture(candidate), {})
            stage, target, output = base / "stage", base / "test-app/showcase", base / "publication"
            stage.mkdir()
            target.mkdir(parents=True)
            output.mkdir()
            (stage / entry["artifact_file"]).write_bytes(raw)
            put(stage / "manifest.json", {"schema": "hydra-verified-showcase-v1", "cases": [entry]})
            put(target / "manifest.json", {"schema": "hydra-verified-showcase-v1", "cases": []})
            with patch.object(publisher, "APP", base / "test-app"):
                receipt = publisher.publish(stage, output)
            self.assertTrue(receipt["published"])
            self.assertEqual(len(publisher.validate_staged(target)["cases"]), 1)
            self.assertFalse((target / ".publish.lock").exists())
            self.assertTrue((output / "previous-manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
