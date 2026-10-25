"""Pure source/metadata checks. No launcher import, preparation or runtime calls.

Synthetic transfer objects exist only in memory and are never evidence.
Run only after the source owner declares the new bundle/bindings stable.
"""
import ast
import base64
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parents[1]
OLD, NEW = BASE / "combined-source-bundle-02", BASE / "combined-source-bundle-03"
OLD_LAUNCH, NEW_LAUNCH = BASE / "paired-launchers-v4", BASE / "paired-launchers-v5"
CONTROL = "output/hydra-implementation-2026-09-04/paired-evaluation-v2/"
CHANGED = {CONTROL + "paired_controller.py", CONTROL + "paired_summary.py"}
CONTROLLER_SHA = "84e78193613505cab6d8d139720a5bb1b0f460db09aec3b0456fbabe4cd76e94"
SUMMARY_SHA = "27e48b363984c4591186b7cce9f855ddb86e78cbff07badcb34d2204d8c63519"
PARENT_MANIFEST_SHA = "ae47bb1f0b6939c3f1ca8ac406024f832fc95b50ff505cf66648e94df0e578a7"
NEW_MANIFEST_SHA = "bff0239d9e0c74e088118a271907da887d009acad3e3b21eca4534c1da855c08"
STUDY_SHA = "64a309de99d97b942a08cf9bb46ef8c62e2681c9f87773999b645d81838b953b"
STAGER_SHA = "8b011366c5b8ebbbb768eb81258cd1c01444ae89a7b37585d50d670cbcb7e896"
REVIEW_SHA = "91120e189257d863b1b702bc1e554f4c83162bfbce55ec03e8f044ef15c93989"
LOCAL_SHA = "35235796df4eec2e2c3788e2d4016e3abe7258811a76ba84dbee628d82a71aa8"
REMOTE_SHA = "607dc9dd04dc5d2f29565d084b89badabf38b8df0aec20a2c8aa6674edf94d4f"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(raw):
    return sha256(raw).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_bytes())


def functions(path):
    return {node.name: node for node in ast.parse(path.read_bytes()).body if isinstance(node, ast.FunctionDef)}


def ast_identity(node):
    return ast.dump(node, include_attributes=False)


def global_assignments(path):
    result = {}
    for node in ast.parse(path.read_bytes()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for item in ast.walk(target):
                    if isinstance(item, ast.Name):
                        result[item.id] = ast_identity(node)
    return result


def isolated_guard():
    """Compile only the receipt predicate and constant path/pin expressions."""
    require(digest((NEW_LAUNCH / "paired_launchers.py").read_bytes()) == LOCAL_SHA, "Local launcher changed.")
    require(digest((NEW_LAUNCH / "remote_paired_control.py").read_bytes()) == REMOTE_SHA, "Remote controller changed.")
    tree = ast.parse((NEW_LAUNCH / "paired_launchers.py").read_bytes())
    namespace = {"__builtins__": {}}
    wanted = {"PROJECT", "CAMPAIGN", "SOURCE", "MANIFEST_SHA", "ARCHIVE_SHA"}
    for node in ast.parse((NEW_LAUNCH / "remote_paired_control.py").read_bytes()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in wanted:
            require(all(isinstance(item, (ast.Assign, ast.Name, ast.Constant, ast.BinOp, ast.Add, ast.Load, ast.Store))
                        for item in ast.walk(node)), "Unexpected executable constant expression.")
            exec(compile(ast.Module(body=[node], type_ignores=[]), "<fixed constants>", "exec"), namespace)
    controls = SimpleNamespace(**{key: namespace[key] for key in wanted})
    scope = {"control": controls, "Path": Path, "json": json, "math": math,
             "canonical": canonical, "digest": digest, "require": require}
    guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "admit_copy_transfer")
    prepare = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "prepare")
    # The follow-up requires this new copy receipt unconditionally; there is
    # no legacy-upload fallback to manufacture for the copy-only source.
    branch = next(node for node in prepare.body if isinstance(node, ast.Expr)
                  and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                  and node.value.func.id == "admit_copy_transfer")
    args = ast.arguments(posonlyargs=[], args=[ast.arg(arg=name) for name in
        ("response_raw", "transport_raw", "manifest", "transferred", "transfer")],
        kwonlyargs=[], kw_defaults=[], defaults=[])
    caller = ast.FunctionDef(name="branch_gate", args=args, body=[deepcopy(branch)], decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[guard, caller], type_ignores=[])),
                 "<isolated receipt predicates>", "exec"), scope)
    return scope


def synthetic_transfer():
    """Evaluate only the producer's two final dicts, with synthetic exits/time.

    Never execute its copier, main(), subprocess helpers or preparation body.
    This checks producer/consumer compatibility, not an actual transfer.
    """
    stager_raw = (BASE / "stage_combined_inference_v3.py").read_bytes()
    require(digest(stager_raw) == STAGER_SHA, "Reviewed stager changed.")
    stager = ast.parse(stager_raw)
    remote = next(node.value.value for node in stager.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == "REMOTE" for target in node.targets))
    record_node = next(node for node in ast.parse(remote).body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "record" for target in node.targets))
    main = next(node for node in stager.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    receipt_node = next(node for node in main.body if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == "receipt" for target in node.targets))
    manifest = read_json(NEW / "manifest.json")
    old_raw = (OLD / "manifest.json").read_bytes()
    review = read_json(BASE / "p6-paired-followup-validation-01/stager-preflight.json")
    require(digest(canonical(review)) == REVIEW_SHA, "Reviewed payload metadata changed.")
    payloads = {name: (NEW / name).read_bytes() for name in review["payload_pins"]}
    require({name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in payloads.items()} == review["payload_pins"],
            "Actual local payload files differ from preflight.")
    request = {"schema": "hydra-combined-inference-source-copy-request-v3", "authority": "HYDRA_EXPERIMENT_AUTHORITY.md",
               "payloads": {name: base64.b64encode(raw).decode() for name, raw in payloads.items()}, "automatic_retry": False}
    request_raw = canonical(request)
    require(len(request_raw) == review["wire_payload_bytes"] and digest(request_raw) == review["wire_payload_sha256"],
            "Pinned wire serialization differs.")
    metadata = {"manifest.json": (len((NEW / "manifest.json").read_bytes()), NEW_MANIFEST_SHA)}
    metadata.update({name + "-source-pins.json": (pin["bytes"], pin["sha256"])
                     for name, pin in manifest["source_maps"].items()})
    scope = {"__builtins__": {"len": len, "str": str, "sum": sum, "sorted": sorted, "set": set},
             "digest": digest, "sha": digest, "canonical": canonical, "metadata_pins": metadata,
             "manifest": manifest, "original": json.loads(old_raw), "old_raw": old_raw,
             "directory": Path(review["remote_destination"]), "source": Path(review["remote_destination"]) / "source",
             "old": Path(review["remote_parent"]), "scopes": manifest["source_maps"],
             "observed": set(manifest["files"]), "total": manifest["expanded_bytes"], "changes": manifest["changed_files"],
             "payloads": payloads, "uploaded_metadata": {"manifest.json", "paired-source-pins.json"},
             "request_raw": request_raw, "time": SimpleNamespace(monotonic=lambda: 1.0), "began": 0.0,
             "used": 0, "limit": 1000000, "required": 1642}
    exec(compile(ast.Module(body=[record_node], type_ignores=[]), "<synthetic producer receipt>", "exec"), scope)
    response_raw = canonical(scope["record"])
    scope.update(result=SimpleNamespace(returncode=0, stdout=response_raw, stderr=b""), review=review, started=0.0)
    exec(compile(ast.Module(body=[receipt_node], type_ignores=[]), "<synthetic transport receipt>", "exec"), scope)
    return scope["record"], scope["receipt"], manifest


class BindingTests(unittest.TestCase):
    def test_exact_two_source_delta_and_physical_replacements(self):
        self.assertEqual(digest((OLD / "manifest.json").read_bytes()), PARENT_MANIFEST_SHA)
        self.assertEqual(digest((NEW / "manifest.json").read_bytes()), NEW_MANIFEST_SHA)
        old, new = read_json(OLD / "manifest.json"), read_json(NEW / "manifest.json")
        self.assertEqual(set(old["files"]), set(new["files"]))
        self.assertEqual(len(new["files"]), 1325)
        changed = {name for name in old["files"] if old["files"][name] != new["files"][name]}
        self.assertEqual(changed, CHANGED)
        self.assertEqual(set(new["changed_files"]), CHANGED)
        for name in CHANGED:
            raw = (NEW / "source" / name).read_bytes()
            self.assertEqual(new["files"][name], {"bytes": len(raw), "sha256": digest(raw)})
            self.assertEqual(new["changed_files"][name]["before"], old["files"][name])
            self.assertEqual(new["changed_files"][name]["after"], new["files"][name])
        self.assertEqual(new["files"][CONTROL + "paired_controller.py"]["sha256"], CONTROLLER_SHA)
        self.assertEqual(new["files"][CONTROL + "paired_summary.py"]["sha256"], SUMMARY_SHA)
        for key in ("provider_sha256", "provider_profile", "file_count"):
            self.assertEqual(new[key], old[key])

    def test_three_scopes_unchanged_and_paired_map_changes_only_two_entries(self):
        for name in ("teacher", "student", "teacher-paired"):
            filename = name + "-source-pins.json"
            self.assertEqual((NEW / filename).read_bytes(), (OLD / filename).read_bytes())
        old = read_json(OLD / "paired-source-pins.json")
        new = read_json(NEW / "paired-source-pins.json")
        self.assertEqual(set(new), set(old))
        self.assertEqual(len(new), 734)
        self.assertEqual({name for name in old if old[name] != new[name]}, CHANGED)

    def test_study_diff_is_only_new_identity_and_source_map(self):
        old = read_json(BASE / "paired-size-study-01/study.json")
        self.assertEqual(digest((BASE / "paired-size-study-02/study.json").read_bytes()), STUDY_SHA)
        new = read_json(BASE / "paired-size-study-02/study.json")
        self.assertEqual(set(new), set(old))
        self.assertEqual({key for key in old if old[key] != new[key]}, {"source_pins_sha256", "study_id"})
        self.assertEqual(new["study_id"], "paired-size-20260905-v2")
        self.assertEqual(new["source_pins_sha256"], digest(canonical(read_json(NEW / "paired-source-pins.json"))))
        self.assertEqual(new["scope"], "full16")
        self.assertEqual(new["wall_profile"], "fixed-wall-30-v1")
        self.assertEqual(new["comparison"], "fixed_native_work_guarded")

    def test_scheduler_argv_resource_and_owned_process_guards_are_unchanged(self):
        names = ("validate_spec", "reservation", "wall_string", "job_script", "fields", "tres",
                 "check_queue_row", "check_held", "submit", "release", "bounded_command")
        old, new = (functions(path / "remote_paired_control.py") for path in (OLD_LAUNCH, NEW_LAUNCH))
        for name in names:
            with self.subTest(function=name):
                self.assertEqual(ast_identity(new[name]), ast_identity(old[name]))

    def test_global_binding_diff_cannot_change_limits_or_model_identity(self):
        old, new = (global_assignments(path / "remote_paired_control.py") for path in (OLD_LAUNCH, NEW_LAUNCH))
        self.assertEqual(set(old), set(new))
        self.assertEqual({name for name in old if old[name] != new[name]},
                         {"SOURCE", "ARCHIVE_SHA", "MANIFEST_SHA", "SOURCE_MAP_SHA", "CONTROLLER_SHA"})
        old, new = (global_assignments(path / "paired_launchers.py") for path in (OLD_LAUNCH, NEW_LAUNCH))
        self.assertEqual(set(old), set(new))
        self.assertEqual({name for name in old if old[name] != new[name]}, {"BUNDLE"})

    def test_attempts_are_fresh_without_other_attempt_guard_changes(self):
        old, new = (functions(path / "remote_paired_control.py")["attempt"] for path in (OLD_LAUNCH, NEW_LAUNCH))
        old = deepcopy(old)
        changes = 0
        for node in ast.walk(old):
            if isinstance(node, ast.Constant) and node.value == "-v3-01":
                node.value = "-v4-01"
                changes += 1
        self.assertEqual(changes, 1)
        self.assertEqual(ast_identity(old), ast_identity(new))

    def test_full_charge_order_cross_family_scan_and_transport_unchanged(self):
        names = ("charge_records", "current_ledger", "make_spec", "execute_phase", "mutate_phase",
                 "integer", "ledger_seconds", "check_charges", "phase_lock", "ssh_once", "admit_training")
        old, new = (functions(path / "paired_launchers.py") for path in (OLD_LAUNCH, NEW_LAUNCH))
        for name in names:
            with self.subTest(function=name):
                self.assertEqual(ast_identity(new[name]), ast_identity(old[name]))
        patterns = [node.value for node in ast.walk(new["charge_records"])
                    if isinstance(node, ast.Constant) and isinstance(node.value, str) and "charge-intent.json" in node.value]
        self.assertEqual(len(patterns), 7)
        self.assertIn("paired-launchers-v*/prepared/arms/*/release/charge-intent.json", patterns)
        self.assertIn("p6-postsave-recovery-v*/attempts/*/release/charge-intent.json", patterns)


class TransferRejectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = isolated_guard()
        cls.response, cls.transport, cls.manifest = synthetic_transfer()

    def check(self, response=None, transport=None, *, reject=False, through_branch=False):
        response = deepcopy(self.response if response is None else response)
        transport = deepcopy(self.transport if transport is None else transport)
        response_raw = canonical(response)
        transport["stdout_sha256"] = digest(response_raw)  # Semantic negatives must not fail solely on old raw bytes.
        args = (response_raw, canonical(transport), self.manifest)
        if through_branch:
            function, args = self.scope["branch_gate"], args + (response, transport)
        else:
            function = self.scope["admit_copy_transfer"]
        if reject:
            with self.assertRaises((ValueError, TypeError)):
                function(*args)
        else:
            function(*args)

    def test_producer_receipts_pass_without_a_remote_archive(self):
        self.assertFalse(self.response["remote_archive_available"])
        self.assertEqual(self.response["uploaded_payload_files"], 4)
        self.assertEqual(self.response["unchanged_files"], 1323)
        self.check(through_branch=True)

    def test_failed_false_or_incomplete_transport_rejected(self):
        for key, value in (("actual_ssh_exit_code", 1), ("actual_ssh_exit_code", False),
                           ("automatic_retry", True), ("model_calls", 1), ("elapsed_seconds", 151)):
            with self.subTest(key=key, value=value):
                row = deepcopy(self.transport); row[key] = value
                self.check(transport=row, reject=True)
        self.check(transport={}, reject=True)

    def test_source_manifest_provider_destination_and_map_changes_rejected(self):
        for key, value in (("completed", False), ("source", "/wrong/source"), ("manifest_sha256", "0" * 64),
                           ("provider_sha256", "0" * 64), ("verified_files", 1324), ("unchanged_files", 1325),
                           ("old_whitelisted_sources_unchanged", False), ("copied_unchanged_metadata_files", [])):
            with self.subTest(key=key):
                row = deepcopy(self.response); row[key] = value
                self.check(response=row, reject=True)
        for name in ("paired", "teacher", "student", "teacher-paired"):
            row = deepcopy(self.response); row["source_maps"][name]["sha256"] = "0" * 64
            self.check(response=row, reject=True)

    def test_payload_copier_and_quota_guard_changes_rejected(self):
        for key in ("remote_script_sha256", "wire_payload_sha256"):
            row = deepcopy(self.transport); row["review"][key] = "0" * 64
            self.check(transport=row, reject=True)
        row = deepcopy(self.response); row["inode_quota_before"]["required_with_reserve"] = 0
        self.check(response=row, reject=True)

    def test_schema_mismatch_cannot_fall_back_to_a_fabricated_legacy_receipt(self):
        row = deepcopy(self.response); row["schema"] = "hydra-combined-source-upload-v1"
        self.check(response=row, reject=True, through_branch=True)
        row = deepcopy(self.transport); row["schema"] = "hydra-combined-inference-source-stage-actual-completion-v2"
        self.check(transport=row, reject=True, through_branch=True)

    def test_duplicate_nonfinite_oversized_or_raw_unbound_receipts_rejected(self):
        response, transport = canonical(self.response), canonical(self.transport)
        for raw in (b'{"completed":false,' + response[1:], b'{"elapsed_seconds":NaN,' + response[1:],
                    b" " * 65537, response + b" "):
            with self.subTest(bytes=len(raw)), self.assertRaises((ValueError, TypeError)):
                self.scope["admit_copy_transfer"](raw, transport, self.manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
