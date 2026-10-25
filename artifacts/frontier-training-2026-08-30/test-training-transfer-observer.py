"""Synthetic filesystem/protocol rejection checks; no SSH or Slurm execution."""
import ast
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

ARCHIVE = Path(__file__).absolute().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ARCHIVE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


t = load("tested_transfer", "transfer-frontier-training.py")
r = t.r
observer = load("tested_observer", "observe-frontier-training.py")
observer_remote = load("tested_observer_remote", "observe-frontier-training-remote.py")


def pin(raw):
    return {"bytes": len(raw), "sha256": r.sha(raw)}


def fixture():
    sources = {"training/fixture.py": b"print('fixture')\n"}
    payloads = {r.PACKAGE + "/data.json": b'{"synthetic":true}\n'}
    sources_map = {name: pin(raw) for name, raw in sources.items()}
    payloads_map = {name: pin(raw) for name, raw in payloads.items()}
    request = {"schema": "peano-hydra-frontier-training-resource-request-v1",
               "status": "ready-for-explicit-resource-approval", "profile": r.PROFILE, "run_id": r.RUN_ID,
               "source_commit": "a" * 40, "source_files": sources_map, "payloads": payloads_map,
               "payloads_sha256": r.sha(r.canonical(payloads_map)),
               "reservations": {"train": {"seconds": 7200, "gpus": 1, "cpus": 8, "memory_gib": 64}},
               "maximum_aggregate_gpu_seconds": 7200, "maximum_concurrent_gpus": 1,
               "automatic_retry": False, "resume": False, "refunds": False}
    request_raw = r.canonical(request) + b"\n"
    approval = {"schema": "peano-hydra-frontier-training-resource-approval-v1", "profile": r.PROFILE,
                "run_id": r.RUN_ID, "approved": True, "approval_reference": "SYNTHETIC FIXTURE ONLY",
                "request_file_sha256": r.sha(request_raw)}
    approval_raw = r.canonical(approval) + b"\n"
    stamp = "2026-08-30T03:00:00Z"
    provenance = "a" * 40 + "\tfalse\t" + stamp + "\n"
    contents = dict(sources, **payloads)
    contents.update({r.REQUEST: request_raw, r.APPROVAL: approval_raw, r.PROVENANCE: provenance.encode()})
    files = {name: pin(raw) for name, raw in contents.items()}
    record = {"schema": r.SCHEMA, "profile": r.PROFILE, "run_id": r.RUN_ID, "local_root": r.LOCAL_ROOT,
              "remote_root": r.REMOTE_ROOT, "source_commit": "a" * 40,
              "request_sha256": r.sha(request_raw), "approval_sha256": r.sha(approval_raw),
              "user_instruction_sha256": r.USER_INSTRUCTION_SHA256, "created_at_utc": stamp,
              "source_files": sources_map, "payloads": payloads_map, "files": files,
              "file_modes": {name: 0o600 for name in files}, "order": r.expected_order(files),
              "file_count": len(files), "total_bytes": sum(item["bytes"] for item in files.values()),
              "provenance": provenance, "helper_sha256": "b" * 64, "remote_helper_sha256": "c" * 64,
              "limits": dict(t.BOUNDS)}
    return record, contents


def stream(record, contents):
    raw = r.canonical(record) + b"\n"
    body = r.MAGIC + struct.pack(">Q", len(raw)) + raw + b"".join(contents[name] for name in record["order"])
    return body, r.sha(raw)


@contextlib.contextmanager
def destination():
    with tempfile.TemporaryDirectory(prefix="transfer-synthetic-", dir=ARCHIVE) as temp:
        path = Path(temp) / "fresh-experiment"
        with mock.patch.object(r, "REMOTE_ROOT", str(path)):
            yield path


def receive(record, contents):
    raw, expected = stream(record, contents)
    progress = {"files_written": 0, "bytes_written": 0, "destination_created": False}
    return r.receive(io.BytesIO(raw), expected, progress), progress


class TransferSafety(unittest.TestCase):
    def test_exact_fresh_copy_no_extra_control_file(self):
        with destination() as path:
            record, contents = fixture()
            result, progress = receive(record, contents)
            self.assertEqual(result["status"], "transferred-and-rehashed")
            self.assertTrue(progress["destination_created"])
            actual = {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}
            self.assertEqual(actual, contents)
            self.assertEqual((path / r.PROVENANCE).read_text(), record["provenance"])
            self.assertFalse((path / ".git").exists())

    def test_existing_destination_is_never_adopted(self):
        with destination() as path:
            path.mkdir()
            (path / "untouched").write_bytes(b"old")
            with self.assertRaises(FileExistsError):
                receive(*fixture())
            self.assertEqual((path / "untouched").read_bytes(), b"old")

    def test_symlink_destination_does_not_redirect_writes(self):
        with destination() as path:
            old = path.parent / "old"
            old.mkdir()
            path.symlink_to(old, target_is_directory=True)
            with self.assertRaises(FileExistsError):
                receive(*fixture())
            self.assertEqual(list(old.iterdir()), [])

    def test_wrong_inventory_pin_precedes_directory_creation(self):
        with destination() as path:
            record, contents = fixture()
            raw, _ = stream(record, contents)
            with self.assertRaisesRegex(ValueError, "inventory bytes"):
                r.receive(io.BytesIO(raw), "0" * 64, {})
            self.assertFalse(path.exists())

    def test_wrong_approval_bytes_precede_directory_creation(self):
        with destination() as path:
            record, contents = fixture()
            contents[r.APPROVAL] = contents[r.APPROVAL].replace(b"true", b"null")
            with self.assertRaisesRegex(ValueError, "control bytes"):
                receive(record, contents)
            self.assertFalse(path.exists())

    def test_changed_file_is_rejected_and_partial_file_retained(self):
        with destination() as path:
            record, contents = fixture()
            name = "training/fixture.py"
            contents[name] = b"x" * len(contents[name])
            with self.assertRaisesRegex(ValueError, "received file SHA"):
                receive(record, contents)
            self.assertTrue(path.exists())
            self.assertEqual((path / name).read_bytes(), contents[name])
            self.assertFalse((path / r.PROVENANCE).exists())

    def test_truncation_preserves_incomplete_output(self):
        with destination() as path:
            record, contents = fixture()
            raw, expected = stream(record, contents)
            with self.assertRaisesRegex(ValueError, "truncated"):
                r.receive(io.BytesIO(raw[:-4]), expected, {"files_written": 0, "bytes_written": 0})
            self.assertTrue(path.exists())

    def test_extra_trailing_bytes_fail(self):
        with destination():
            record, contents = fixture()
            raw, expected = stream(record, contents)
            with self.assertRaisesRegex(ValueError, "trailing"):
                r.receive(io.BytesIO(raw + b"unexpected"), expected, {"files_written": 0, "bytes_written": 0})

    def test_unknown_post_copy_file_fails_closed_inventory(self):
        with destination() as path:
            original = r.write_stream_file
            def add_extra(tree, name, *args):
                original(tree, name, *args)
                if name == r.PROVENANCE:
                    (path / "extra.txt").write_bytes(b"extra")
            with mock.patch.object(r, "write_stream_file", side_effect=add_extra):
                with self.assertRaisesRegex(ValueError, "exact file inventory"):
                    receive(*fixture())

    def test_path_traversal_links_binary_files_and_bounds_rejected(self):
        for name in ("../escape", "/absolute", "a//b", "a/./b", "a/.git/config", "adapter/model.safetensors", "a\\b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                r.relative(name)
        with self.assertRaises(ValueError):
            r.descriptor({"bytes": r.MAX_FILE + 1, "sha256": "a" * 64})
        with self.assertRaises(ValueError):
            r.descriptor({"bytes": True, "sha256": "a" * 64})

    def test_duplicate_json_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            r.decode(b'{"key":1,"key":2}')

    def test_source_hardlinks_and_symlinks_rejected(self):
        with tempfile.TemporaryDirectory(prefix="transfer-synthetic-", dir=ARCHIVE) as temp:
            root = Path(temp)
            (root / "data.json").write_bytes(b"data")
            os.link(root / "data.json", root / "hard.json")
            (root / "sym.json").symlink_to(root / "data.json")
            tree = r.Tree(temp)
            try:
                for name in ("data.json", "hard.json", "sym.json"):
                    with self.subTest(name=name), self.assertRaises((ValueError, OSError)):
                        tree.fingerprint(name)
            finally:
                tree.close()

    def test_bundle_fd_offset_resets_before_subprocess_streaming(self):
        with tempfile.TemporaryDirectory(prefix="transfer-synthetic-", dir=ARCHIVE) as temp:
            path = Path(temp) / "bundle.bin"
            raw = b"0123456789" * 1000
            path.write_bytes(raw)
            handle, _ = t.bundle_open(path, pin(raw))
            try:
                self.assertEqual(r.exact(handle, 19), raw[:19])
                handle.seek(0)
                self.assertEqual(os.lseek(handle.fileno(), 0, os.SEEK_CUR), 0)
                self.assertEqual(os.read(handle.fileno(), 20), raw[:20])
            finally:
                handle.close()

    def test_bundle_growth_is_rejected_before_unbounded_read(self):
        with tempfile.TemporaryDirectory(prefix="transfer-synthetic-", dir=ARCHIVE) as temp:
            path = Path(temp) / "bundle.bin"
            path.write_bytes(b"original")
            original_read = os.read
            seen = []
            def changed_read(fd, size):
                if not seen:
                    seen.append(True)
                    with path.open("ab") as output:
                        output.write(b"unexpected-growth")
                return original_read(fd, size)
            with mock.patch.object(t.os, "read", side_effect=changed_read):
                with self.assertRaisesRegex(ValueError, "grew beyond"):
                    t.bundle_open(path, pin(b"original"))

    def test_subprocess_output_overflow_is_bounded_and_retained(self):
        import sys
        result = t.bounded([sys.executable, "-I", "-B", "-c", "import os; os.write(1,b'\\x00'*600000)"], timeout=5)
        self.assertIn("output bound", result["reason"])
        self.assertEqual(len(result["stdout"]), 512 * 1024)
        self.assertLess(len(r.canonical(result)), r.MAX_JSON)

    def test_remote_syntax_is_python36(self):
        for filename in ("transfer-frontier-training-remote.py", "observe-frontier-training-remote.py"):
            ast.parse((ARCHIVE / filename).read_text(), feature_version=(3, 6))


def submitted():
    return {"status": "submitted", "profile": r.PROFILE, "run_id": r.RUN_ID, "jobs": {"train": "123456"},
            "reserved_gpu_seconds": 7200, "maximum_concurrent_gpus": 1, "automatic_retry": False,
            "resume": False, "refunds": False, "ledger": "logs/hydra-frontier-training-v1.jsonl",
            "outputs": {"adapter": observer.ADAPTER}}


class ObservationSafety(unittest.TestCase):
    def test_exact_final_submitted_record_only(self):
        result = submitted()
        raw = r.canonical({"returncode": 0, "stdout": "metadata checked\n" + json.dumps(result) + "\n"})
        self.assertEqual(observer.submitted_record(raw)["jobs"], {"train": "123456"})

    def test_wrong_profile_ambiguous_and_unsafe_job_rejected(self):
        for change in ({"profile": "peano-hydra-frontier-v1"}, {"jobs": {"train": "1;touch bad"}},
                       {"jobs": {"train": "123", "evaluate": "456"}}, {"reserved_gpu_seconds": 9000}):
            result = dict(submitted(), **change)
            raw = r.canonical({"returncode": 0, "stdout": json.dumps(result)})
            with self.subTest(change=change), self.assertRaises(ValueError):
                observer.submitted_record(raw)
        with self.assertRaises(ValueError):
            observer.submitted_record(r.canonical({"returncode": 0, "stdout": (json.dumps(submitted()) + "\n") * 2}))

    def test_failed_launch_is_not_a_job_reference(self):
        with self.assertRaises(ValueError):
            observer.submitted_record(r.canonical({"returncode": 1, "stdout": json.dumps(submitted())}))

    def test_read_only_log_tail_is_bounded_and_metadata_checked(self):
        with tempfile.TemporaryDirectory(prefix="observer-synthetic-", dir=ARCHIVE) as temp:
            root = Path(temp)
            (root / "logs").mkdir()
            raw = b"not-the-tail" * 10000 + b"the final line\n"
            (root / "logs/example.out").write_bytes(raw)
            with mock.patch.object(observer_remote, "ROOT", temp):
                actual, info = observer_remote.read("logs/example.out", 65536, tail=True)
                self.assertEqual(actual, raw[-65536:])
                self.assertEqual(info["file_bytes_at_open"], len(raw))
                self.assertEqual(observer_remote.read("missing/file", 1024, optional=True)[0], None)
                (root / "logs/link").symlink_to(root / "logs/example.out")
                with self.assertRaises(OSError):
                    observer_remote.read("logs/link", 65536, tail=True)

    def test_controller_identity_mismatch_is_reported(self):
        observations = {"controller": {"returncode": 0, "reason": "exited", "stdout": "JobId=123456 WorkDir=/other"},
                        "accounting": {"returncode": 0, "reason": "exited", "stdout": ""}}
        result = observer_remote.scheduler_identity(observations, "123456")
        self.assertIn("WorkDir differs", result["integrity_issues"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
