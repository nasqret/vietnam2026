"""Pure binding fixtures only; no real preparation, receipt, process or network.

Constructed CPU/copy records stay in memory and are not actual evidence.
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ATTEMPTED_OPERATIONS = []


def forbid_operations(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind"}:
        ATTEMPTED_OPERATIONS.append(event)
        raise AssertionError("Pure gate attempted an external operation: " + event)


sys.addaudithook(forbid_operations)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


control = load("remote_paired_control", HERE / "remote_paired_control.py")
launcher = load("_selected_paired_launcher", HERE / "paired_launchers.py")


class SelectedBindings(unittest.TestCase):
    def setUp(self):
        self.study = json.loads((BASE / "paired-size-study-02/study.json").read_bytes())
        self.bindings = mock.patch.multiple(control, ARCHIVE_SHA="a" * 64, MANIFEST_SHA="b" * 64,
            SOURCE_MAP_SHA="c" * 64, CONTROLLER_SHA="d" * 64, MANIFEST_CONTENT_SHA="e" * 64,
            COPY_REVIEW_SHA="f" * 64, COPY_PAYLOAD_BYTES=1000, COPY_QUOTA_REQUIRED=1642)
        self.bindings.start()
        self.addCleanup(self.bindings.stop)

    def spec(self):
        return launcher.make_spec(self.study, "1" * 64, "fresh_4b", "2" * 32)

    def test_only_fresh4b_is_selected_in_local_and_remote_interfaces(self):
        spec = self.spec()
        self.assertEqual(spec["attempt"], "p6-paired-fresh-4b-v5-01")
        self.assertEqual(spec["seconds"], 1560)
        self.assertEqual(spec["scope"], "full16")
        self.assertEqual(control.ARMS, ("symbolic", "historical_1_7b", "fresh_1_7b", "fresh_4b"))
        for name in ("symbolic", "historical_1_7b", "fresh_1_7b", "fresh_8b"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    control.attempt(name)
                changed = {**spec, "arm": name}
                with self.assertRaises(ValueError):
                    control.validate_spec(changed)
                with self.assertRaises(ValueError):
                    launcher.load_prepared(name, "3" * 64)

    def test_unsealed_or_changed_source_profile_and_resources_fail_closed(self):
        spec = self.spec()
        with mock.patch.object(control, "CONTROLLER_SHA", None):
            with self.assertRaises(ValueError):
                control.validate_spec(spec)
        for field, value in (("source", control.SOURCE + "/other"), ("seconds", 2040),
                             ("wall_profile", "guarded-work-60-v1"), ("cpus", 4),
                             ("memory_gib", 128), ("case_count", 5), ("automatic_retry", True)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                control.validate_spec({**spec, field: value})

    def test_preparation_counts_one_selected_allocation_and_keeps_hard_ceiling(self):
        module = ast.parse((HERE / "paired_launchers.py").read_text())
        prepare = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "prepare")
        index = next(i for i, n in enumerate(prepare.body) if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "selected_seconds" for t in n.targets))
        fragment = ast.Module(body=prepare.body[index:index + 2], type_ignores=[])
        compiled = compile(ast.fix_missing_locations(fragment), "<actual selected-budget expressions>", "exec")
        for used in (15840, 20040):
            scope = {"control": control, "seconds": 1560, "used": used, "require": control.require}
            exec(compiled, scope)
            self.assertEqual(scope["selected_seconds"], 1560)
        with self.assertRaises(ValueError):
            exec(compiled, {"control": control, "seconds": 1560, "used": 20041, "require": control.require})
        arm_loops = [n for n in prepare.body if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                     and n.target.id == "arm"]
        self.assertEqual(len(arm_loops), 1)
        self.assertEqual(ast.unparse(arm_loops[0].iter), "control.SELECTED_ARMS")
        main = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        arm_choices = [k.value for n in ast.walk(main) if isinstance(n, ast.Call) and n.args
                       and isinstance(n.args[0], ast.Constant) and n.args[0].value == "--arm"
                       for k in n.keywords if k.arg == "choices"]
        self.assertEqual([ast.unparse(n) for n in arm_choices], ["control.SELECTED_ARMS"])

    def test_prior_fresh4b_charge_cannot_become_another_first_attempt(self):
        for attempt, accepted in (("p6-training-fresh-4b-v3-01", True),
                                  ("p6-paired-fresh-4b-v4-01", False),
                                  ("p6-paired-fresh-4b-v5-01", False)):
            ledger = {"gpu_reservations": [{"attempt": attempt}]}
            with self.subTest(attempt=attempt), mock.patch.object(launcher, "read", return_value=json.dumps(ledger).encode()), \
                 mock.patch.object(launcher, "ledger_seconds", return_value=15840), \
                 mock.patch.object(launcher, "charge_records", return_value=[]), \
                 mock.patch.object(launcher, "check_charges"):
                if accepted:
                    self.assertEqual(launcher.current_ledger("1" * 64, "fresh_4b")[2], 15840)
                else:
                    with self.assertRaises(ValueError):
                        launcher.current_ledger("1" * 64, "fresh_4b")

    def cpu_fixture(self):
        manifest = {"schema": "hydra-linux-monitor-probe-package-v1", "limits": {"cpus": 1},
            "files": {"paired_controller.py": {"sha256": control.CONTROLLER_SHA},
                      "paired_common.py": {"sha256": control.COMMON_SHA},
                      "run_probe.py": {"sha256": "9" * 64}}}
        manifest_raw = control.canonical(manifest)
        manifest_sha = control.digest(manifest_raw)
        report = {"schema": "hydra-linux-monitor-probe-result-v1", "passed": True, "error": None,
            "job_id": "123456", "sources_unchanged": True, "manifest_sha256": manifest_sha,
            "controller_sha256": control.CONTROLLER_SHA, "common_sha256": control.COMMON_SHA,
            "probe_sha256": "9" * 64, "limits": manifest["limits"], "elapsed_seconds": 2.0,
            "aggregate_cpu_seconds": 0.1, "actual_fixture_launches": 2,
            "all_owned_leaders_reaped": True, "all_groups_quiescent": True,
            "model_calls": 0, "native_calls": 0, "scheduler_queries_by_probe": 0,
            "automatic_retry": False, "full_pairing_or_proof_checked": False,
            "fixtures": [{"index": i, "passed": True, "execution": {"exit_code": 0,
                "leader_reaped": True, "quiescent": True, "termination_reason": "process_exit",
                "helper_launches": 1, "pid": 100 + i, "rss_samples": 2,
                "peak_sampled_host_rss_bytes": (8, 128)[i] * 1024**2},
                "ready": {"schema": "hydra-linux-monitor-fixture-ready-v1", "index": i,
                    "pid": 100 + i, "uid": control.UID, "requested_mappings": (1, 8192)[i],
                    "requested_bytes": (8, 128)[i] * 1024**2,
                    "observed_vma_lines": (1, 8192)[i] + 100}} for i in range(2)]}
        actual = {"schema": "hydra-linux-monitor-probe-actual-completion-v1", "job_id": "123456",
            "slurm_state": "COMPLETED", "slurm_exit_code": "0:0", "controller_sha256": control.CONTROLLER_SHA,
            "manifest_sha256": manifest_sha, "allocation": {"cpus": 1, "gpus": 0, "nodes": 1,
                "memory_bytes": 1024**3, "seconds": 60}, "actual_probe_process_exit_code": 0,
            "actual_collect_tool_exit_code": 0, "actual_collect_ssh_exit_code": 0,
            "completion_chunk": "SYNTHETIC_TEST_ONLY"}
        return manifest_raw, manifest_sha, report, actual

    def admit_cpu(self, fixture, *, edit_report=None, edit_actual=None):
        manifest_raw, manifest_sha, report, actual = copy.deepcopy(fixture)
        if edit_report:
            edit_report(report)
        report_raw = control.canonical(report)
        actual["result"] = {"bytes": len(report_raw), "sha256": control.digest(report_raw)}
        if edit_actual:
            edit_actual(actual)
        actual_raw = control.canonical(actual)
        choice = {"report": {"path": "synthetic/report.json", "sha256": control.digest(report_raw)},
                  "actual_completion": {"path": "synthetic/actual.json", "sha256": control.digest(actual_raw)}}
        with mock.patch.object(launcher, "MONITOR_PROBE_MANIFEST_SHA", manifest_sha), \
             mock.patch.object(launcher, "read", return_value=manifest_raw), \
             mock.patch.object(launcher, "evidence", side_effect=[report_raw, actual_raw]):
            return launcher.admit_monitor_probe(choice)

    def test_cpu_admission_requires_actual_matching_clean_job(self):
        admitted = self.admit_cpu(self.cpu_fixture())
        self.assertEqual(admitted["controller_sha256"], control.CONTROLLER_SHA)
        self.assertFalse(admitted["model_or_theorem_work"])

    def test_cpu_report_failure_or_different_source_and_bounds_rejected(self):
        changes = (("passed", False), ("error", {"type": "Failure"}), ("controller_sha256", "8" * 64),
                   ("sources_unchanged", False), ("elapsed_seconds", 30.001), ("aggregate_cpu_seconds", 10.001),
                   ("model_calls", 1), ("actual_fixture_launches", 1))
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.admit_cpu(self.cpu_fixture(), edit_report=lambda r: r.update({key: value}))

    def test_cpu_clean_flag_cannot_hide_bad_fixture_exit_or_cleanup(self):
        for key, value in (("exit_code", 2), ("leader_reaped", False), ("quiescent", False),
                           ("termination_reason", None), ("helper_launches", 2)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.admit_cpu(self.cpu_fixture(), edit_report=lambda r: r["fixtures"][1]["execution"].update({key: value}))

    def test_cpu_report_alone_is_not_an_actual_successful_scheduler_receipt(self):
        changes = (("slurm_state", "FAILED"), ("slurm_exit_code", "1:0"), ("job_id", "654321"),
                   ("actual_probe_process_exit_code", 1), ("actual_collect_tool_exit_code", 1),
                   ("actual_collect_ssh_exit_code", None), ("completion_chunk", ""),
                   ("result", {"bytes": 1, "sha256": "0" * 64}), ("allocation", {"gpus": 1}))
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.admit_cpu(self.cpu_fixture(), edit_actual=lambda r: r.update({key: value}))

    def test_cpu_report_needs_both_fixed_mapping_and_live_rss_observations(self):
        for field, value in (("requested_mappings", 512), ("requested_bytes", 1), ("observed_vma_lines", 0)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.admit_cpu(self.cpu_fixture(), edit_report=lambda r: r["fixtures"][1]["ready"].update({field: value}))
        with self.assertRaises(ValueError):
            self.admit_cpu(self.cpu_fixture(), edit_report=lambda r: r["fixtures"][0]["execution"].update({"rss_samples": 0}))

    def test_only_intended_helper_bodies_changed(self):
        changed = {"paired_launchers.py": {"bundle_inputs", "current_ledger", "admit_copy_transfer", "prepare", "load_prepared", "main"},
                   "remote_paired_control.py": {"validate_study", "attempt", "validate_spec"}}
        for filename, permitted in changed.items():
            def bodies(path):
                return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body
                        if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
            before, after = bodies(BASE / "paired-launchers-v5" / filename), bodies(HERE / filename)
            actual_changed = {name for name in before if after.get(name) != before[name]}
            self.assertEqual(actual_changed, permitted, filename)
        self.assertEqual(ATTEMPTED_OPERATIONS, [])
        self.assertFalse(any(n == "peano_lab" or n.startswith(("peano_lab.", "torch", "transformers", "peft", "mlx"))
                             for n in sys.modules))


class FinalPackageBindings(unittest.TestCase):
    def copy_fixture(self):
        """Evaluate just the frozen copier's two JSON expressions with fake observations."""
        stager_raw = (BASE / "stage_combined_inference_v4.py").read_bytes()
        self.assertEqual(control.digest(stager_raw), "e91ce24c01284f04595376db514bf8f3268ab220671de7f4367d4185beeddde5")
        tree = ast.parse(stager_raw)
        remote = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "REMOTE" for t in n.targets))
        remote_tree = ast.parse(remote)
        record = next(n.value for n in remote_tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "record" for t in n.targets))
        metadata = next(ast.literal_eval(n.value) for n in remote_tree.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "metadata_pins" for t in n.targets))
        manifest = json.loads((launcher.BUNDLE / "manifest.json").read_bytes())
        review = json.loads((launcher.BUNDLE / "COPY_REVIEW.json").read_bytes())
        old_raw = (BASE / "combined-source-bundle-03/manifest.json").read_bytes()
        scope = {"directory": Path(review["remote_destination"]), "source": Path(control.SOURCE),
            "old": Path(review["remote_parent"]), "metadata_pins": metadata, "manifest": manifest,
            "digest": control.digest, "canonical": control.canonical, "old_raw": old_raw,
            "original": json.loads(old_raw), "scopes": manifest["source_maps"],
            "observed": set(manifest["files"]), "total": manifest["expanded_bytes"],
            "changes": manifest["changed_files"],
            "payloads": {name: b"0" * pin["bytes"] for name, pin in review["payload_pins"].items()},
            "uploaded_metadata": {"manifest.json", "paired-source-pins.json"},
            "request_raw": b"0" * review["wire_payload_bytes"], "time": SimpleNamespace(monotonic=lambda: 1.0),
            "began": 0.0, "used": 940000, "limit": 1000000, "required": 1642}
        response = eval(compile(ast.Expression(record), "<copier JSON expression only>", "eval"), scope)
        response_raw = json.dumps(response).encode() + b"\n"
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        receipt = next(n.value for n in main.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "receipt" for t in n.targets))
        transport = eval(compile(ast.Expression(receipt), "<transport JSON expression only>", "eval"),
            {"result": SimpleNamespace(returncode=0, stdout=response_raw, stderr=b""), "started": 0.0,
             "time": SimpleNamespace(monotonic=lambda: 2.0), "review": review, "sha": control.digest})
        return response, transport, manifest

    def test_exact_copier_record_shape_is_admitted_without_running_copier(self):
        response, transport, manifest = self.copy_fixture()
        raw = json.dumps(response).encode() + b"\n"
        launcher.admit_copy_transfer(raw, control.canonical(transport), manifest)

    def test_copy_v3_wrong_delta_or_failed_transport_cannot_qualify(self):
        response, transport, manifest = self.copy_fixture()
        for key, value in (("schema", "hydra-combined-inference-source-copy-receipt-v3"),
                           ("changed_files", ["hydra-playground/hybrid_search.py"]),
                           ("unchanged_files", 1323), ("manifest_raw_bytes_preserved", False)):
            changed = {**response, key: value}
            raw = json.dumps(changed).encode() + b"\n"
            actual = {**transport, "stdout_sha256": control.digest(raw)}
            with self.subTest(key=key), self.assertRaises(ValueError):
                launcher.admit_copy_transfer(raw, control.canonical(actual), manifest)
        raw = json.dumps(response).encode() + b"\n"
        with self.assertRaises(ValueError):
            launcher.admit_copy_transfer(raw, control.canonical({**transport, "actual_ssh_exit_code": 1}), manifest)

    def test_study_changes_only_its_identity_and_source_map_and_template_stays_prospective(self):
        before = json.loads((BASE / "paired-size-study-02/study.json").read_bytes())
        after_raw = (BASE / "paired-size-study-03/study.json").read_bytes()
        after = json.loads(after_raw)
        self.assertEqual({k for k in before.keys() | after.keys() if before.get(k) != after.get(k)},
                         {"study_id", "source_pins_sha256"})
        self.assertEqual(after["source_pins_sha256"], control.SOURCE_MAP_SHA)
        self.assertEqual(set(after["arms"]), set(control.ARMS))
        choice = json.loads((BASE / "paired-choice-03/CHOICE.template.json").read_bytes())
        self.assertEqual(choice["study"]["sha256"], control.digest(after_raw))
        for field in ("transfer", "monitor_probe"):
            self.assertTrue(all(value == {"path": None, "sha256": None} for value in choice[field].values()))
        self.assertFalse(launcher.PREPARED.exists())
        self.assertEqual(ATTEMPTED_OPERATIONS, [])


if __name__ == "__main__":
    unittest.main()
