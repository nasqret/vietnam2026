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
            old_entry, old_artifact = deepcopy(entry), deepcopy(artifact)
            old_entry.update(id="existing-example", artifact_file="existing-example.json")
            old_artifact["case_id"] = "existing-example"
            old_raw = publisher.json_bytes(old_artifact)
            old_entry["artifact_sha256"] = publisher.hashlib.sha256(old_raw).hexdigest()
            (target / old_entry["artifact_file"]).write_bytes(old_raw)
            put(target / "manifest.json", {"schema": "hydra-verified-showcase-v1", "cases": [old_entry]})
            with patch.object(publisher, "APP", base / "test-app"):
                receipt = publisher.publish(stage, output)
            self.assertTrue(receipt["published"])
            self.assertEqual(len(publisher.validate_staged(target)["cases"]), 2)
            self.assertEqual(publisher.validate_staged(target)["cases"][0], old_entry)
            self.assertEqual((target / old_entry["artifact_file"]).read_bytes(), old_raw)
            self.assertFalse((target / ".publish.lock").exists())
            self.assertTrue((output / "previous-manifest.json").is_file())


class ExperimentalPublisherTests(unittest.TestCase):
    """Constructed evidence, never an assertion that these synthetic scripts prove anything."""
    def fixture(self, base, *, lemmas=False, adviser=None, planner=False, historical=False):
        path, record = ShowcasePublisherTests().fixture(base)
        options = {"engine": "sharing-v1", "lemmas": lemmas, "planner": "deterministic" if planner else "off",
                   "ranker": "off", "advisers": [] if adviser is None else [adviser]}
        request = record["request"]
        request.update(search_profile="deep", max_model_calls=16, beam_width=4, experimental=options)
        record.update(search_profile="deep", normalized_request=worker.validate_request("search", request))
        result = record["last_job"]["result"]
        result.update(settings_profile="deep")
        result["execution"].update(worker_started=True, worker_exit_code=0)
        search = result["search"]
        pin = {"bytes": 1, "sha256": "4"*64}
        snapshot = {"profile": "hydra-experimental-certified-v1", "native_source": {"bytes": 1, "sha256": "1"*64},
            "library_manifest": {"bytes": 3, "sha256": "2"*64} if lemmas else None,
            "library_certificates": {"zero_add": "a"*64, "add_comm": "b"*64} if lemmas else {},
            "reservation": {"bytes": 4, "sha256": "3"*64} if lemmas else None, "ranker": None,
            "replay_sources": {name: dict(pin) for name in publisher.REPLAY_SOURCE_FILES},
            "kernel_entrypoints": dict(worker.KERNEL_PINS)}
        app = {name: dict(pin) for name in publisher.REPLAY_SOURCE_FILES if name != "publish_showcase.py"}
        app.update({name: dict(pin) for name in ("hybrid_search.py", "adviser_worker.py", "adviser_process.py",
            "adviser_protocol.py", "adviser_polynomials.py", "sympy_bridge.py", "smt_bridge.py",
            "vampire_bridge.py", "vampire_process.py", "vampire_limits.py", "p9_bridge_common.py", "egraph_bridge.py", "e_bridge.py")})
        search["application_source_pins"] = app
        preload = {"all_entries_checked_before_return": True, "certificates_checked": 2,
                   "native_kernel_checks": 2, "manifest_bytes_read": 3, "certificate_bytes_read": 20,
                   "catalogue_bytes_read": 23}
        search["experimental"] = {**options, "profile": snapshot["profile"], "native_source": snapshot["native_source"],
                                  "library_source": {"manifest": snapshot["library_manifest"], "preload_verification": preload} if lemmas else None}
        search["lemma_library"] = None
        if lemmas:
            target = "5"*64
            search["lemma_library"] = {"manifest_sha256": "2"*64, "target_sha256": target,
                "capability_label": "hydra-certified-lemmas-v1-"+publisher.canonical_sha({
                    "profile": "hydra-certified-lemmas-v1", "manifest": "2"*64, "target": target}),
                "available_names": ["zero_add", "add_comm"], "imports": self.ledger([], "independent_replay")}
        search["structured_planning"] = {"enabled": planner, "plans": [], "requests_detail": [], "chunk_steps": 8}
        search["branch_ranker"] = {"enabled": False, "artifact_sha256": None}
        search["proof_cost"] = {"final": {"policy": "hydra-proof-cost-observation-v1", "stage": "final",
            "status": "complete", "distinct_objects": 1, "structural_occurrences": 1,
            "exact": {"distinct_objects": True, "structural_occurrences": True}}}
        if adviser is not None:
            self.add_helper(record, snapshot, adviser)
        if historical:
            for key in ("planner", "ranker", "advisers"):
                request["experimental"].pop(key)
                record["normalized_request"]["experimental"].pop(key)
                search["experimental"].pop(key)
            search.pop("structured_planning")
            search.pop("branch_ranker")
        put(base / "source-pins.json", {"kernel_commit": worker.SOURCE_COMMIT,
             "kernel_entrypoints": dict(worker.KERNEL_PINS), "application": app})
        self.save(path, record)
        return path, record, snapshot

    def save(self, path, record):
        plan = json.loads((path.parent / "plan.json").read_text())
        plan["source_pins"] = publisher.descriptor(path.parent / "source-pins.json")
        plan["jobs"][0]["request"] = record["request"]
        put(path.parent / "plan.json", plan)
        record["run_context"] = {"plan_sha256": publisher.descriptor(path.parent / "plan.json")["sha256"],
                                 "source_pins_sha256": publisher.descriptor(path.parent / "source-pins.json")["sha256"]}
        put(path, record)
        summary = json.loads((path.parent / "summary.json").read_text())
        summary["case_file_pins"][path.name] = publisher.descriptor(path)
        put(path.parent / "summary.json", summary)

    def inspect(self, path, snapshot):
        with patch.object(publisher, "experimental_snapshot", return_value=deepcopy(snapshot)):
            return publisher.inspect_live_record(path, lambda _: "0 = 0")

    def candidate(self, base, **kwargs):
        path, _, snapshot = self.fixture(base, **kwargs)
        return self.inspect(path, snapshot)

    def ledger(self, names, phase):
        return {"policy": "hydra-checked-import-budget-v1", "attempts": len(names), "accepted": len(names), "rejected": 0,
            "max_attempts": 32, "max_imports_per_proof": 8,
            "phases": {key: len(names) if key == phase else 0 for key in ("search", "independent_replay", "manual")},
            "records": [{"name": name, "phase": phase, "status": "native_accepted"} for name in names]}

    def replay(self, candidate):
        replay = ShowcasePublisherTests().replay_fixture(candidate)
        admission = candidate["experimental_authority"]
        options, snapshot, library = admission["options"], admission["snapshot"], admission["recorded_library"]
        commands = sorted(["intro", "use", "apply", "refl", "ring"])
        replay["publication_authority"] = {"selection": deepcopy(options), "snapshot": deepcopy(snapshot), "allowed_commands": commands}
        label = "hydra-sharing-native-v1" if library is None else library["capability_label"]
        capability = {"label": label, "allowed_commands": commands,
                      "allowed_theorems": [] if library is None else sorted(library["available_names"])}
        metadata = {**options, "profile": snapshot["profile"], "native_source_sha256": snapshot["native_source"]["sha256"],
            "library_source": deepcopy(candidate["result"]["search"]["experimental"]["library_source"]), "imports": None}
        if library is not None:
            names = [line.split()[1] for line in candidate["result"]["commands"] if line.startswith("use ")]
            metadata["imports"] = self.ledger(names, "manual")
        replay["result"].update(surface=label, environment_sha256=publisher.canonical_sha(capability), experimental=metadata)
        return replay

    def add_helper(self, record, snapshot, backend):
        result = record["last_job"]["result"]
        search = result["search"]
        helper_names = ["adviser_worker.py", "adviser_process.py", "adviser_protocol.py", "vampire_process.py", "vampire_limits.py"]
        helper_names += (["p9_bridge_common.py", "egraph_bridge.py" if backend == "egg" else "e_bridge.py"]
            + (["vampire_bridge.py"] if backend == "e" else []) if backend in {"egg", "e"} else
            ["adviser_polynomials.py", "sympy_bridge.py" if backend == "sympy" else "smt_bridge.py"])
        identity = {"backend": backend, "helper_sha256": search["application_source_pins"]["adviser_worker.py"]["sha256"],
                    "helper_sources_sha256": publisher.canonical_sha({name: search["application_source_pins"][name] for name in helper_names})}
        source = {"input_sha256": "6"*64, "context_sha256": "7"*64}
        result["proof_sources"] = {backend: 1}
        search["provenance"] = [{"command": "refl", "source": backend, "evidence": {
            "strategy": "external_native_reconstruction", **source}}]
        search[backend+"_calls"] = 1
        search["advisor_results"] = [{"backend": backend, "invocations": 1, "kernel_checked": False,
                                      "identity": identity, **source}]
        search["external_advisers"] = {"actual_launches_by_backend": {backend: 1},
            "authority_identity": publisher.canonical_sha({"native": snapshot["native_source"], "checked_library": snapshot["library_manifest"] or "none"}),
            "controller_requests": 1, "requests_by_backend": {backend: 1},
            "shared": {"accounting_complete": True, "active_request": None, "requests": 1,
                "actual_launches": 1, "known_actual_launches": 1, "cache_hits": 0,
                "records": [{"backend": backend, "actual_launches": 1, "status": "completed", "cache_hit": False,
                             "quiescent": True, "exit_code": 0, "identity": identity, **source}]},
            "runners": {backend: [{"executed": True, "status": "completed", "quiescent": True,
                                   "exit_code": 0, "identity": identity, "input_sha256": source["input_sha256"]}]}}

    def test_replay_preserves_explicit_engine_selection_and_old_defaults(self):
        for historical in (False, True):
            with self.subTest(historical=historical), tempfile.TemporaryDirectory() as directory:
                candidate = self.candidate(Path(directory), lemmas=True, historical=historical)
                self.assertTrue(candidate["replay_request"]["experimental"]["lemmas"])
                self.assertEqual(candidate["replay_request"]["experimental"]["advisers"], [])
                entry, artifact, _ = publisher.make_entry(candidate, self.replay(candidate), {})
                self.assertEqual(entry["proof_sources"], {"heuristic": 1})
                self.assertEqual(artifact["request"], candidate["request"])
                self.assertEqual("planner" in artifact["request"]["experimental"], not historical)

    def test_tampered_request_engine_library_kernel_and_source_pins_are_rejected(self):
        changes = [
            lambda r: r["last_job"]["result"]["search"]["experimental"].update(lemmas=True),
            lambda r: r["last_job"]["result"]["search"]["experimental"].update(native_source={"bytes": 1, "sha256": "f"*64}),
            lambda r: r["last_job"]["result"]["search"]["application_source_pins"]["worker.py"].update(sha256="f"*64),
            lambda r: r["last_job"]["result"]["execution"].update(worker_exit_code=-9),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                path, record, snapshot = self.fixture(Path(directory))
                change(record)
                self.save(path, record)
                with self.assertRaises(ValueError):
                    self.inspect(path, snapshot)

    def test_no_legacy_fallback_for_an_experimental_result(self):
        with tempfile.TemporaryDirectory() as directory:
            path, record, snapshot = self.fixture(Path(directory))
            record["request"].pop("experimental")
            record["normalized_request"].pop("experimental")
            self.save(path, record)
            with self.assertRaisesRegex(ValueError, "explicit request authority"):
                self.inspect(path, snapshot)

    def test_fresh_target_bound_library_surface_and_source_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = self.candidate(Path(directory), lemmas=True)
            for change in (
                lambda r: r["result"].update(surface="other-target"),
                lambda r: r["result"].update(environment_sha256="f"*64),
                lambda r: r["publication_authority"]["snapshot"].update(reservation={"bytes": 4, "sha256": "f"*64}),
                lambda r: r["result"]["experimental"].update(lemmas=False),
            ):
                replay = self.replay(candidate)
                change(replay)
                with self.assertRaises(ValueError):
                    publisher.make_entry(candidate, replay, {})

    def test_import_and_apply_are_not_double_counted_and_preload_is_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = self.candidate(Path(directory), lemmas=True)
            result = candidate["result"]
            result["commands"] = ["use zero_add as h", "apply h"]
            result["proof_sources"] = {"heuristic": 2}
            result["search"]["provenance"] = [{"command": line, "source": "heuristic", "evidence": {
                "strategy": "checked_lemma_retrieval", "lemma": "zero_add", "certificate_sha256": "a"*64}} for line in result["commands"]]
            result["search"]["lemma_library"]["imports"] = self.ledger(["zero_add"], "independent_replay")
            entry, artifact, _ = publisher.make_entry(candidate, self.replay(candidate), {})
            imported = artifact["independent_replay"]["experimental_authority"]["checked_imports"]
            self.assertEqual(entry["proof_steps"], 2)
            self.assertEqual(imported["winning_commands"], 1)
            self.assertEqual(imported["fresh_replay_preload"]["native_kernel_checks"], 2)
            result["search"]["provenance"][0]["evidence"]["certificate_sha256"] = "f"*64
            with self.assertRaisesRegex(ValueError, "different or excluded certificate"):
                publisher.make_entry(candidate, self.replay(candidate), {})

    def test_missing_fresh_preload_and_wrong_import_ledger_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = self.candidate(Path(directory), lemmas=True)
            for change in (
                lambda r: r["result"]["experimental"]["library_source"]["preload_verification"].update(native_kernel_checks=0),
                lambda r: r["result"]["experimental"]["imports"].update(attempts=99),
            ):
                replay = self.replay(candidate)
                change(replay)
                with self.assertRaises(ValueError):
                    publisher.make_entry(candidate, replay, {})

    def test_four_helpers_need_matching_actual_receipts_not_just_a_badge(self):
        for name in ("sympy", "cvc5", "egg", "e"):
            with self.subTest(backend=name), tempfile.TemporaryDirectory() as directory:
                candidate = self.candidate(Path(directory), adviser=name)
                entry, artifact, _ = publisher.make_entry(candidate, self.replay(candidate), {})
                self.assertEqual(entry["proof_sources"], {name: 1})
                self.assertEqual(artifact["adviser_contributions"]["actual_launches_by_backend"], {name: 1})
                candidate["result"]["search"]["external_advisers"]["runners"][name][0]["exit_code"] = -9
                with self.assertRaisesRegex(ValueError, "completed, reaped helper"):
                    publisher.make_entry(candidate, self.replay(candidate), {})

    def test_cache_and_wrong_context_cannot_manufacture_a_helper_winning_step(self):
        changes = [
            lambda s: s["external_advisers"]["shared"]["records"][0].update(cache_hit=True),
            lambda s: s["external_advisers"]["shared"]["records"][0].update(context_sha256="f"*64),
            lambda s: s["external_advisers"]["shared"].update(accounting_complete=False),
            lambda s: s.update(sympy_calls=0),
            lambda s: s["advisor_results"][0].update(input_sha256="f"*64),
            lambda s: s["external_advisers"]["shared"]["records"][0]["identity"].update(helper_sources_sha256="f"*64),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                candidate = self.candidate(Path(directory), adviser="sympy")
                change(candidate["result"]["search"])
                with self.assertRaises(ValueError):
                    publisher.make_entry(candidate, self.replay(candidate), {})

    def test_launched_helpers_with_no_winning_step_do_not_gain_contribution_credit(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = self.candidate(Path(directory), adviser="egg")
            candidate["result"]["proof_sources"] = {"heuristic": 1}
            candidate["result"]["search"]["provenance"] = [{"command": "refl", "source": "heuristic"}]
            entry, artifact, _ = publisher.make_entry(candidate, self.replay(candidate), {})
            self.assertEqual(entry["proof_sources"], {"heuristic": 1})
            self.assertEqual(artifact["adviser_contributions"]["actual_launches_by_backend"], {"egg": 1})

    def test_fresh_occurrences_do_not_claim_to_remeasure_original_sharing(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = self.candidate(Path(directory))
            _, artifact, _ = publisher.make_entry(candidate, self.replay(candidate), {})
            self.assertEqual(artifact["certificate_cost"]["original_distinct_objects"], 1)
            self.assertEqual(artifact["certificate_cost"]["fresh_replay_structural_occurrences"], 1)
            self.assertIsNone(artifact["certificate_cost"]["fresh_replay_distinct_objects"])
            candidate["result"]["search"]["proof_cost"]["final"]["structural_occurrences"] = 2
            with self.assertRaisesRegex(ValueError, "occurrences disagree"):
                publisher.make_entry(candidate, self.replay(candidate), {})

    def test_structured_plan_checks_exact_command_context_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = self.candidate(Path(directory), planner=True)
            replay = self.replay(candidate)
            authority = publisher.validate_experimental_replay(candidate, replay)
            cap = authority["capability"]
            report = candidate["result"]["search"]["structured_planning"]
            context = {"complete_synthetic_context": True}
            action = {"kind": "native", "command": "refl"}
            plan = {"id": 0, "request": 1, "commands": ["refl"], "actions": [action],
                "plan_sha256": publisher.hashlib.sha256(b"refl\n").hexdigest(),
                "context_sha256": publisher.canonical_sha(context), "library_identity": "none",
                "capability_identity": publisher.canonical_sha({"label": cap["label"], "commands": cap["allowed_commands"], "theorems": []}),
                "source": "heuristic", "native_source": "heuristic"}
            report.update(plans=[plan], requests_detail=[{"request": 1, "context": context, "actual_model_calls": 0}])
            candidate["result"]["search"]["provenance"] = [{"command": "refl", "source": "heuristic", "macro_step": 1,
                "planner_action": action, "evidence": {"strategy": "structured_plan", "plan_id": "0", "chunk": "1",
                    "plan_sha256": plan["plan_sha256"], "planner_source": "heuristic"}}]
            _, artifact, _ = publisher.make_entry(candidate, replay, {})
            self.assertEqual(artifact["structured_plan_contributions"]["winning_steps"], 1)
            plan["context_sha256"] = "f"*64
            with self.assertRaisesRegex(ValueError, "exact recorded context"):
                publisher.make_entry(candidate, replay, {})

    def test_parent_replay_uses_exact_experimental_payload_without_a_real_child(self):
        class Child:
            pid = 424244
            returncode = 0
            payload = None
            def poll(self):
                return self.returncode
            def communicate(self, **kwargs):
                self.payload = kwargs.get("input")
                return b'{"result":{}}', b""
        child = Child()
        request = {"theorem": "0=0", "tactics": ["refl"], "experimental": {"engine": "sharing-v1", "lemmas": False}}
        with patch.object(server, "process_snapshot", return_value={}), \
             patch.object(publisher.subprocess, "Popen", return_value=child):
            publisher.run_replay(request, time.monotonic()+120)
        self.assertEqual(json.loads(child.payload)["request"], request)


if __name__ == "__main__":
    unittest.main()
