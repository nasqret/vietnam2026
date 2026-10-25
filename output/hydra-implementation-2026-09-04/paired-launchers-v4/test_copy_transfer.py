"""Pure receipt gate using the actual copy result; mutation fixtures are not evidence.

Only the new guard and its call-site branch are compiled from launcher ASTs.
No launcher import, choice preparation, native/model import, or subprocess runs.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest

BASE = Path(__file__).resolve().parent.parent
CASES = (
    ("paired-launchers-v4", "paired_launchers.py", "remote_paired_control.py", "prepare"),
    ("p7-teacher-launchers-v4", "teacher_launchers.py", "remote_teacher_control.py", "bundle_inputs"),
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pinned(relative, expected):
    raw = (BASE / relative).read_bytes()
    if digest(raw) != expected:
        raise ValueError("Actual metadata fixture changed: " + relative)
    return raw


def isolated_guard(folder, local, remote, caller):
    source = (BASE / folder / local).read_bytes()
    tree = ast.parse(source)
    constants = {}
    wanted = {"PROJECT", "CAMPAIGN", "SOURCE", "MANIFEST_SHA", "ARCHIVE_SHA"}
    for node in ast.parse((BASE / folder / remote).read_bytes()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in wanted:
            exec(compile(ast.Module(body=[node], type_ignores=[]), "<pinned source constants>", "exec"), constants)
    namespace = {"control": SimpleNamespace(**{key: constants[key] for key in wanted}),
                 "json": json, "math": math, "Path": Path, "require": require,
                 "canonical": canonical, "digest": digest}
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "admit_copy_transfer")
    owner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == caller)
    branch = next(node for node in owner.body if isinstance(node, ast.If) and any(
        isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "admit_copy_transfer"
        for child in ast.walk(node)))
    gate = ast.FunctionDef(name="gate", args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=name) for name in
        ("response_raw", "transport_raw", "manifest", "transferred", "transfer", "upload")],
        kwonlyargs=[], kw_defaults=[], defaults=[]), body=[copy.deepcopy(branch)], decorator_list=[])
    program = ast.fix_missing_locations(ast.Module(body=[function, gate], type_ignores=[]))
    exec(compile(program, str(BASE / folder / local), "exec"), namespace)
    return namespace, tree, branch


class CopyTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.response_raw = pinned("combined-inference-transfer-02/stdout.json",
                                  "500872342484294f89b7f9d30d08b3f125e804dc478decd6b3b24fc87e21f504")
        cls.transport_raw = pinned("combined-inference-transfer-02/actual-completion.json",
                                   "595708972cba7128caa2a4a1f3a4781d95ce41fbca89e51ebd9df6c60560312c")
        cls.manifest = json.loads(pinned("combined-source-bundle-02/manifest.json",
                                        "ae47bb1f0b6939c3f1ca8ac406024f832fc95b50ff505cf66648e94df0e578a7"))
        cls.guards = [(case, isolated_guard(*case)) for case in CASES]

    def admit(self, response_raw, transport_raw, manifest=None, *, through_branch=False):
        for case, (namespace, _, _) in self.guards:
            with self.subTest(launcher=case[0]):
                if through_branch:
                    response, transport = json.loads(response_raw), json.loads(transport_raw)
                    namespace["gate"](response_raw, transport_raw, self.manifest if manifest is None else manifest,
                                      response, transport, response)
                else:
                    namespace["admit_copy_transfer"](response_raw, transport_raw,
                                                     self.manifest if manifest is None else manifest)

    def reject(self, response_raw, transport_raw, *, through_branch=False):
        for case, (namespace, _, _) in self.guards:
            with self.subTest(launcher=case[0]), self.assertRaises((ValueError, TypeError)):
                if through_branch:
                    response, transport = json.loads(response_raw), json.loads(transport_raw)
                    namespace["gate"](response_raw, transport_raw, self.manifest, response, transport, response)
                else:
                    namespace["admit_copy_transfer"](response_raw, transport_raw, self.manifest)

    def mutation(self, response_change=None, transport_change=None):
        response, transport = json.loads(self.response_raw), json.loads(self.transport_raw)
        if response_change:
            response_change(response)
        response_raw = canonical(response)
        # Deliberately rebind the raw bytes, so failures test semantic fields too.
        transport["stdout_sha256"] = digest(response_raw)
        if transport_change:
            transport_change(transport)
        return response_raw, canonical(transport)

    def test_actual_copy_without_remote_archive_passes_both_real_branches(self):
        response = json.loads(self.response_raw)
        self.assertIs(response["remote_archive_available"], False)
        self.assertEqual(response["archive_bytes_uploaded"], 0)
        self.admit(self.response_raw, self.transport_raw, through_branch=True)

    def test_failed_missing_false_or_unbound_transport_is_rejected(self):
        for key, value in (("actual_ssh_exit_code", 1), ("actual_ssh_exit_code", False),
                           ("stdout_sha256", "0" * 64), ("automatic_retry", True),
                           ("schema", "hydra-combined-source-upload-v1")):
            with self.subTest(key=key, value=value):
                self.reject(*self.mutation(transport_change=lambda row, k=key, v=value: row.__setitem__(k, v)))
        self.reject(self.response_raw, b"{}")
        self.reject(self.response_raw + b" ", self.transport_raw)

    def test_altered_source_provider_manifest_counts_or_maps_is_rejected(self):
        fields = {
            "completed": False, "provider_sha256": "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f",
            "manifest_sha256": "4aeb37d8ad971975a22fe7cd879c69ad35e11246dccc5d37d7a9a0c2ab899ec1",
            "manifest_raw_bytes_preserved": False, "directory": "/wrong", "source": "/wrong/source",
            "derived_from_source": "/wrong/parent", "parent_remote_manifest_sha256": "0" * 64,
            "verified_files": 1324, "verified_bytes": 112064116, "unchanged_files": 1325,
            "uploaded_payload_bytes": 1059321, "remote_archive_available": True,
            "old_whitelisted_sources_unchanged": False, "model_calls": False,
        }
        for key, value in fields.items():
            with self.subTest(key=key):
                self.reject(*self.mutation(response_change=lambda row, k=key, v=value: row.__setitem__(k, v)))
        for scope in ("paired", "teacher", "student", "teacher-paired"):
            for key in ("sha256", "content_sha256", "files"):
                with self.subTest(scope=scope, key=key):
                    self.reject(*self.mutation(response_change=lambda row, s=scope, k=key:
                        row["source_maps"][s].__setitem__(k, 1 if k == "files" else "0" * 64)))

    def test_changed_copier_payload_or_bounds_is_rejected(self):
        for key, value in (("remote_script_sha256", "0" * 64), ("wire_payload_sha256", "0" * 64),
                           ("remote_destination", "/wrong"), ("wire_payload_bytes", 0)):
            with self.subTest(key=key):
                self.reject(*self.mutation(transport_change=lambda row, k=key, v=value: row["review"].__setitem__(k, v)))
        self.reject(*self.mutation(transport_change=lambda row: row["review"]["bounds"].__setitem__("ssh_wall_seconds", 151)))

    def test_copy_and_transport_schema_mismatch_does_not_use_legacy_fallback(self):
        self.reject(*self.mutation(response_change=lambda row: row.__setitem__("schema", "hydra-combined-source-upload-v1")),
                    through_branch=True)
        self.reject(*self.mutation(transport_change=lambda row: row.__setitem__("schema", "invented-completion")),
                    through_branch=True)

    def test_duplicate_keys_nonfinite_values_and_oversized_metadata_rejected(self):
        duplicate = b'{"completed": false,' + self.response_raw.lstrip()[1:]
        nonfinite = b'{"elapsed_seconds": NaN,' + self.response_raw.lstrip()[1:]
        for response in (duplicate, nonfinite, b" " * 65537):
            with self.subTest(bytes=len(response)):
                self.reject(response, self.transport_raw)

    def test_legacy_requirements_and_all_remote_bytes_are_unchanged(self):
        helper_dumps = []
        for case, (_, tree, branch) in self.guards:
            folder, local, remote, caller = case
            prior = folder.replace("launchers-v4", "launchers-v3")
            self.assertEqual((BASE / folder / remote).read_bytes(), (BASE / prior / remote).read_bytes())
            old_tree = ast.parse((BASE / prior / local).read_bytes())
            old_owner = next(node for node in old_tree.body if isinstance(node, ast.FunctionDef) and node.name == caller)
            self.assertEqual(len(branch.orelse), 1)
            legacy_dump = ast.dump(branch.orelse[0], include_attributes=False)
            self.assertIn(legacy_dump, {ast.dump(node, include_attributes=False) for node in old_owner.body})
            old_functions = {node.name: ast.dump(node, include_attributes=False) for node in old_tree.body if isinstance(node, ast.FunctionDef)}
            new_functions = {node.name: ast.dump(node, include_attributes=False) for node in tree.body if isinstance(node, ast.FunctionDef)}
            self.assertEqual({name for name in old_functions if old_functions[name] != new_functions[name]}, {caller})
            self.assertEqual(set(new_functions) - set(old_functions), {"admit_copy_transfer"})
            helper_dumps.append(new_functions["admit_copy_transfer"])
        self.assertEqual(helper_dumps[0], helper_dumps[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
