"""Documentary recovery/security tests, never theorem-admission evidence.

The production checks authenticate real stored archive bytes and the immutable
parent's literal document records. Disposable fixtures exercise only filesystem
and metadata rejection. No HA checker, Lean verifier, release capability, or
proof receipt is substituted or manufactured.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import sys
import time
from types import SimpleNamespace

import pytest

import alpha_v31_historical_evidence as evidence
import peano_catalog_shards as transport


EXPECTED = (
    ("peano-lab/py/tests/test_library_editions_v19_admission.py", 16034,
     "2125f1e0170447ca94cfd78a8d34c4f1034d2ef0e68884ef79b9787345e36d45"),
    ("peano-lab/py/tests/test_linear_congruence_complete_candidate.py", 13442,
     "455c416e00618ecb4443da8af8f038d985308a7624431de4c63c9dcb6206c0e0"),
    ("research/arithmetic-library/ha-bertrand-b6-release-tranche-rfc-v1.md", 6783,
     "cb6a22a23f44958546eebedd9bdadb28ba466519c2951920cd2ac5f3c04760f3"),
    ("research/arithmetic-library/linear-congruence-complete-rfc-v1.md", 6351,
     "857da462982d7798c69ca24053378c31e52d1b58fcc401bfe99ba92aac101383"),
    ("research/arithmetic-library/wmi-qr-replay.md", 43290,
     "b7774571ff25d0ab1c35707e4aa8b074b584179307bc25c2d9bcb5dc7a17f960"),
)
RSS_LIMIT = 1536 * 1024 * 1024


def _record(index=0):
    path, size, digest = EXPECTED[index]
    return {"path": path, "bytes": size, "sha256": digest, "role": "historical_test_document"}


def _ordinary_record(path="ordinary/document.md", payload=b"ordinary current documentary bytes\n"):
    return {"path": path, "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
            "role": "ordinary_inherited_document"}


def _put(root, relative, payload):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


@pytest.fixture(scope="module")
def parent_records():
    # Real immutable documentary data only; parsing it is not a proof check.
    raw, _ = transport._read_file(
        transport.DEFAULT_PARENT, owner_uid=os.getuid(),
        expected_bytes=66_503_303,
        expected_sha256="ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7")
    parent = json.loads(raw)
    assert parent["schema"] == "peano-library-alpha-snapshot-v30"
    assert parent["theorem_count"] == 3222
    assert len(parent["evidence_documents"]) == 740
    return {row["path"]: row for row in parent["evidence_documents"]}


@pytest.fixture
def files(tmp_path):
    root = tmp_path.resolve()
    for item in evidence.ARCHIVES:
        target = root / item["archive_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(evidence.ROOT / item["archive_path"], target)
        _put(root, item["original_path"], b"unrelated current bytes, not old evidence\n")
    return root


def test_exact_five_literal_bindings_and_no_executable_archive_suffix():
    assert type(evidence.ARCHIVES) is tuple and len(evidence.ARCHIVES) == 5
    assert tuple((row["original_path"], row["bytes"], row["sha256"])
                 for row in evidence.ARCHIVES) == EXPECTED
    assert len(set(evidence.archive_paths())) == 5
    for item in evidence.ARCHIVES:
        assert set(item) == {"original_path", "archive_path", "bytes", "sha256", "recovery"}
        assert item["archive_path"] == (
            "research/arithmetic-library/artifacts/alpha-v31-historical-evidence/"
            + Path(item["original_path"]).name + ".snapshot")
        assert Path(item["archive_path"]).suffix == ".snapshot"
        assert "verified" not in item and "checked_use" not in item and "stable" not in item
    assert evidence.MAX_DOCUMENT_BYTES == transport.MAX_CATALOG_BYTES == 64 * 1024 * 1024


@pytest.mark.parametrize("index", range(5))
def test_real_archives_resolve_the_exact_unchanged_parent_records(parent_records, index):
    original, size, digest = EXPECTED[index]
    record = parent_records[original]
    assert record["bytes"] == size and record["sha256"] == digest
    before = deepcopy(record)
    resolved = evidence.verify_inherited_document(record)
    assert resolved == evidence.ROOT / evidence.ARCHIVES[index]["archive_path"]
    assert resolved.stat().st_size == size
    assert sha256(resolved.read_bytes()).hexdigest() == digest
    assert record == before  # Never retarget the immutable old record itself.


def test_all_production_archive_document_records_are_fresh_verified_bytes():
    records = evidence.archive_evidence_documents()
    assert records == [
        {"path": item["archive_path"], "bytes": size, "sha256": digest,
         "role": "alpha_v31_historical_evidence_archive"}
        for item, (_, size, digest) in zip(evidence.ARCHIVES, EXPECTED, strict=True)
    ]
    assert all(set(row) == {"path", "bytes", "sha256", "role"} for row in records)


def test_returned_metadata_and_nested_recovery_records_do_not_alias_the_registry():
    before = deepcopy(evidence.ARCHIVES)
    one = evidence.archive_bindings()
    one[0]["archive_path"] = "../not-registered.snapshot"
    one[0]["recovery"]["note"] = "changed caller-owned text"
    one.pop()
    assert evidence.ARCHIVES == before
    assert evidence.archive_bindings() == list(before)
    assert evidence.archive_bindings()[0] is not evidence.ARCHIVES[0]


@pytest.mark.parametrize("index", (0, 1, 3))
def test_single_lf_recovery_metadata_reproduces_the_exact_source_byte_pin(index):
    item = evidence.ARCHIVES[index]
    recovered = (evidence.ROOT / item["archive_path"]).read_bytes()
    source = recovered[:-1]
    assert recovered[-1:] == b"\n"
    assert item["recovery"]["kind"] == "unchanged_current_bytes_plus_one_final_lf"
    assert item["recovery"]["append_hex"] == "0a"
    assert len(source) == item["recovery"]["source_bytes"]
    assert sha256(source).hexdigest() == item["recovery"]["source_sha256"]
    assert "git_commit" not in item["recovery"]


def test_git_recoveries_retain_exact_noninvented_provenance_and_spaces():
    b6, wmi = evidence.ARCHIVES[2], evidence.ARCHIVES[4]
    assert b6["recovery"]["kind"] == "exact_git_blob"
    assert b6["recovery"]["git_blob"] == "4249083c8cae9c5bbcb5c00b9722de5bc66a8511"
    assert "git_commit" not in b6["recovery"]
    lines = (evidence.ROOT / b6["archive_path"]).read_bytes().splitlines(keepends=True)
    assert lines[2] == b"Status: frozen for additive Alpha enrollment  \n"
    assert lines[3] == b"Date: 2026-08-17  \n"
    assert wmi["recovery"]["kind"] == "exact_git_commit_blob"
    assert wmi["recovery"]["git_commit"] == "fc835a0eb29b446f976ad1254e53c6bb96dee89e"
    assert wmi["recovery"]["git_blob"] == "40d70de2d926b6a217d747242d0668454bf93d47"
    # Resolving an archive never requires the old (possibly unreferenced) Git
    # object to survive a fresh clone; its stored bytes and SHA are authority.


@pytest.mark.parametrize("index", range(5))
def test_archived_record_needs_no_read_of_current_path_and_never_rewrites_it(files, index):
    item = evidence.ARCHIVES[index]
    original = files / item["original_path"]
    before = original.read_bytes()
    assert evidence.verify_inherited_document(_record(index), root=files) == files / item["archive_path"]
    assert original.read_bytes() == before
    original.unlink()  # Disposable fixture only, not the repository original.
    assert evidence.verify_inherited_document(_record(index), root=files) == files / item["archive_path"]
    assert not original.exists()


@pytest.mark.parametrize("index", range(5))
def test_reserved_original_path_cannot_be_rebound_to_even_matching_current_bytes(files, index):
    record = _record(index)
    current = (files / record["path"]).read_bytes()
    record.update(bytes=len(current), sha256=sha256(current).hexdigest())
    with pytest.raises(evidence.HistoricalEvidenceError, match="literal historical record changed"):
        evidence.verify_inherited_document(record, root=files)


@pytest.mark.parametrize("index", range(5))
@pytest.mark.parametrize("mutation", ("size", "digest"))
def test_each_literal_original_size_and_digest_is_required(files, index, mutation):
    record = _record(index)
    if mutation == "size":
        record["bytes"] += 1
    else:
        record["sha256"] = "0" * 64
    with pytest.raises(evidence.HistoricalEvidenceError, match="literal historical record changed"):
        evidence.verify_inherited_document(record, root=files)


@pytest.mark.parametrize("index", range(5))
@pytest.mark.parametrize("mutation", ("missing", "same_size", "truncated", "extra_byte"))
def test_bad_archive_never_falls_back_even_to_a_current_file_with_exact_old_bytes(files, index, mutation):
    item = evidence.ARCHIVES[index]
    archive = files / item["archive_path"]
    exact = archive.read_bytes()
    (files / item["original_path"]).write_bytes(exact)
    if mutation == "missing":
        archive.unlink()
    elif mutation == "same_size":
        archive.write_bytes(bytes((exact[0] ^ 1,)) + exact[1:])
    elif mutation == "truncated":
        archive.write_bytes(exact[:-1])
    else:
        archive.write_bytes(exact + b"\n")
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.verify_inherited_document(_record(index), root=files)
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.archive_evidence_documents(root=files)
    assert (files / item["original_path"]).read_bytes() == exact


@pytest.mark.parametrize("path", (
    "", "/absolute/document", "../escape", "a/../escape", "./document", "a/./document",
    "a//document", "a/document/", "https://example.invalid/document", "file:///document",
    "a\\document", "C:\\document", "a/*", "a/?", "a/[x]", "a/\x00document",
    "a/\ndocument", "a/\tdocument", Path("ordinary/document.md"), None, 1,
))
def test_unsafe_or_nonliteral_record_paths_fail_before_any_read(files, monkeypatch, path):
    record = _record()
    record["path"] = path
    monkeypatch.setattr(transport, "_read_file", lambda *args, **kwargs: pytest.fail("invalid path was read"))
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.verify_inherited_document(record, root=files)


@pytest.mark.parametrize("key,value", (
    ("bytes", True), ("bytes", False), ("bytes", 0), ("bytes", -1), ("bytes", 1.0),
    ("bytes", "16034"), ("bytes", None), ("bytes", 64 * 1024 * 1024 + 1),
    ("sha256", "A" * 64), ("sha256", "a" * 63), ("sha256", "a" * 65),
    ("sha256", "g" * 64), ("sha256", b"a" * 64), ("sha256", None),
    ("role", ""), ("role", None), ("role", True), ("role", 1), ("role", "x" * 257),
))
def test_invalid_field_types_and_bounds_fail_before_any_read(files, monkeypatch, key, value):
    record = _record()
    record[key] = value
    monkeypatch.setattr(transport, "_read_file", lambda *args, **kwargs: pytest.fail("invalid record was read"))
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.verify_inherited_document(record, root=files)


@pytest.mark.parametrize("mutation", ("path", "bytes", "sha256", "role", "extra_archive", "extra_recovery"))
def test_record_shape_does_not_accept_caller_supplied_archive_instructions(files, mutation):
    record = _record()
    if mutation.startswith("extra_"):
        record[mutation] = evidence.ARCHIVES[0]
    else:
        del record[mutation]
    with pytest.raises(evidence.HistoricalEvidenceError, match="exactly"):
        evidence.verify_inherited_document(record, root=files)


@pytest.mark.parametrize("record", (None, False, [], (), "old receipt.json"))
def test_nonrecord_inputs_have_no_authority(files, record):
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.verify_inherited_document(record, root=files)


def test_an_unregistered_document_must_match_its_actual_current_bytes(files):
    payload = b"ordinary current documentary bytes\n"
    record = _ordinary_record(payload=payload)
    path = _put(files, record["path"], payload)
    assert evidence.verify_inherited_document(record, root=files) == path
    path.write_bytes(b"X" + payload[1:])
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.verify_inherited_document(record, root=files)


@pytest.mark.parametrize("mutation", ("missing", "size", "digest"))
def test_unregistered_paths_do_not_resolve_by_archive_basename_or_matching_hash(files, mutation):
    item = evidence.ARCHIVES[0]
    relative = "other/" + Path(item["original_path"]).name
    record = {"path": relative, "bytes": item["bytes"], "sha256": item["sha256"], "role": "inherited"}
    if mutation == "size":
        _put(files, relative, b"different size")
    elif mutation == "digest":
        _put(files, relative, b"X" * item["bytes"])
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.verify_inherited_document(record, root=files)


@pytest.mark.parametrize("target_kind", ("archive_file", "archive_parent", "root", "current_file", "current_parent"))
def test_all_path_components_reject_symlinks_even_to_correct_owned_bytes(files, target_kind):
    if target_kind.startswith("current"):
        payload = b"ordinary current documentary bytes\n"
        record = _ordinary_record(payload=payload)
        path = _put(files, record["path"], payload)
    else:
        record = _record()
        path = files / evidence.ARCHIVES[0]["archive_path"]
    if target_kind == "root":
        linked = files.parent / (files.name + "-linked")
        linked.symlink_to(files, target_is_directory=True)
        test_root = linked
    else:
        test_root = files
        victim = path.parent if target_kind.endswith("parent") else path
        saved = victim.with_name(victim.name + "-owned-real")
        victim.rename(saved)
        victim.symlink_to(saved, target_is_directory=saved.is_dir())
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.verify_inherited_document(record, root=test_root)


@pytest.mark.parametrize("kind", ("directory", "fifo"))
def test_nonregular_archive_is_rejected_without_read_or_fifo_block(files, monkeypatch, kind):
    path = files / evidence.ARCHIVES[0]["archive_path"]
    path.unlink()
    if kind == "directory":
        path.mkdir()
    else:
        os.mkfifo(path)
    monkeypatch.setattr(transport.os, "read", lambda *args: pytest.fail("nonregular input was read"))
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.verify_inherited_document(_record(), root=files)


def test_wrong_owner_is_rejected_before_read_without_changing_file_ownership(files, monkeypatch):
    path = files / evidence.ARCHIVES[0]["archive_path"]
    inode = path.stat().st_ino
    original = os.fstat

    def foreign(fd):
        info = original(fd)
        if info.st_ino == inode:
            return SimpleNamespace(st_mode=info.st_mode, st_uid=os.getuid() + 1)
        return info

    monkeypatch.setattr(transport.os, "fstat", foreign)
    monkeypatch.setattr(transport.os, "read", lambda *args: pytest.fail("foreign-owned input was read"))
    with pytest.raises(evidence.HistoricalEvidenceError, match="owner"):
        evidence.verify_inherited_document(_record(), root=files)


@pytest.mark.parametrize("size", (16035, 64 * 1024 * 1024 + 1))
def test_wrong_size_and_sparse_oversize_fail_before_allocation(files, monkeypatch, size):
    path = files / evidence.ARCHIVES[0]["archive_path"]
    with path.open("r+b") as stream:
        stream.truncate(size)
    monkeypatch.setattr(transport.os, "read", lambda *args: pytest.fail("wrong-size bytes were allocated"))
    with pytest.raises(evidence.HistoricalEvidenceError):
        evidence.verify_inherited_document(_record(), root=files)


def test_archive_growth_after_initial_stat_fails_at_exact_initial_size(files, monkeypatch):
    path = files / evidence.ARCHIVES[0]["archive_path"]
    original = os.read
    changed = False
    requests = []

    def growing(fd, count):
        nonlocal changed
        requests.append(count)
        if not changed:
            changed = True
            with path.open("ab") as stream:
                stream.write(b"extra")
        return original(fd, count)

    monkeypatch.setattr(transport.os, "read", growing)
    with pytest.raises(evidence.HistoricalEvidenceError, match="grew"):
        evidence.verify_inherited_document(_record(), root=files)
    assert changed and max(requests) <= EXPECTED[0][1] + 1


def test_identical_byte_replacement_after_hashing_is_not_a_warm_path_success(files, monkeypatch):
    path = files / evidence.ARCHIVES[0]["archive_path"]
    original = transport._stat_file
    replacement = path.with_name(path.name + "-replacement")
    replacement.write_bytes(path.read_bytes())
    swapped = False

    def swap_then_stat(*args, **kwargs):
        nonlocal swapped
        assert not swapped
        swapped = True
        os.replace(replacement, path)  # Only this disposable owned fixture.
        return original(*args, **kwargs)

    monkeypatch.setattr(transport, "_stat_file", swap_then_stat)
    with pytest.raises(evidence.HistoricalEvidenceError, match="path changed"):
        evidence.verify_inherited_document(_record(), root=files)
    assert swapped


def test_archive_permission_failure_is_explicit_and_has_no_retry_or_fallback(files, monkeypatch):
    basename = Path(evidence.ARCHIVES[0]["archive_path"]).name
    original = os.open
    denied = []

    def deny(path, flags, *args, **kwargs):
        if path == basename:
            denied.append(path)
            raise PermissionError("synthetic denial for this owned fixture")
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(transport.os, "open", deny)
    with pytest.raises(evidence.HistoricalEvidenceError, match="synthetic denial"):
        evidence.verify_inherited_document(_record(), root=files)
    assert denied == [basename]


def test_reader_is_hash_only_and_uses_the_exact_original_limits(files, monkeypatch):
    original = transport._read_file
    calls = []
    prior_proof_imports = {name for name in sys.modules if name.startswith("peano_lab")}

    def observed(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(transport, "_read_file", observed)
    evidence.archive_evidence_documents(root=files)
    assert len(calls) == 5
    for (_path,), kwargs in calls:
        assert kwargs["owner_uid"] == os.getuid()
        assert kwargs["capture"] is False
        assert type(kwargs["expected_bytes"]) is int
        assert kwargs["expected_bytes"] <= 43290
    assert {name for name in sys.modules if name.startswith("peano_lab")} == prior_proof_imports


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Original-bounded literal historical-document regressions.")
    parser.add_argument("--pytest-select", default="")
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    status = pytest.main(["-q", "--tb=short", "-x", __file__, "-k", args.pytest_select])
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    print(json.dumps({"status": int(status), "seconds": time.monotonic() - started,
                      "peak_rss_bytes": peak, "rss_limit_passed": peak <= RSS_LIMIT,
                      "document_integrity_only": True, "proofs_verified": False}), flush=True)
    assert peak <= RSS_LIMIT
    raise SystemExit(status)
