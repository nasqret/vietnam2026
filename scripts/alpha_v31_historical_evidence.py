"""Five literal historical evidence snapshots, not a general fallback resolver.

The immutable Alpha-v30 catalogue retains its original document records. Five
current files legitimately differ from those historical bytes. These reviewed
archives recover exactly the already-pinned records without rewriting either
the catalogue or current files. Authenticating documentary bytes confers no HA,
Lean, Stable, or Alpha admission authority.

Reads reuse the frozen catalogue transport's ordinary-owner, no-follow,
size-first streaming SHA-256 checks. The unchanged per-document bound is
64 MiB; the five snapshots are individually pinned far below it.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path, PurePosixPath
import os
import re

import peano_catalog_shards as transport


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIRECTORY = "research/arithmetic-library/artifacts/alpha-v31-historical-evidence"
ARCHIVE_ROLE = "alpha_v31_historical_evidence_archive"
MAX_DOCUMENT_BYTES = 64 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class HistoricalEvidenceError(ValueError):
    """An inherited document or one of its literal archives did not verify."""


ARCHIVES = (
    {
        "original_path": "peano-lab/py/tests/test_library_editions_v19_admission.py",
        "archive_path": ARCHIVE_DIRECTORY + "/test_library_editions_v19_admission.py.snapshot",
        "bytes": 16034,
        "sha256": "2125f1e0170447ca94cfd78a8d34c4f1034d2ef0e68884ef79b9787345e36d45",
        "recovery": {
            "kind": "unchanged_current_bytes_plus_one_final_lf",
            "source_bytes": 16033,
            "source_sha256": "27b789cca2650a2c83fb0cd3eb185607111eac7075a1f44cee9cd274832ee9a1",
            "append_hex": "0a",
            "note": "The recovered bytes match the literal Alpha-v30 record; no source commit is claimed.",
        },
    },
    {
        "original_path": "peano-lab/py/tests/test_linear_congruence_complete_candidate.py",
        "archive_path": ARCHIVE_DIRECTORY + "/test_linear_congruence_complete_candidate.py.snapshot",
        "bytes": 13442,
        "sha256": "455c416e00618ecb4443da8af8f038d985308a7624431de4c63c9dcb6206c0e0",
        "recovery": {
            "kind": "unchanged_current_bytes_plus_one_final_lf",
            "source_bytes": 13441,
            "source_sha256": "8a4d2588fe63a8c13477349899040f3122b0d1226b75adbfcb926364e0088736",
            "append_hex": "0a",
            "note": "The recovered bytes match the literal Alpha-v30 record; no source commit is claimed.",
        },
    },
    {
        "original_path": "research/arithmetic-library/ha-bertrand-b6-release-tranche-rfc-v1.md",
        "archive_path": ARCHIVE_DIRECTORY + "/ha-bertrand-b6-release-tranche-rfc-v1.md.snapshot",
        "bytes": 6783,
        "sha256": "cb6a22a23f44958546eebedd9bdadb28ba466519c2951920cd2ac5f3c04760f3",
        "recovery": {
            "kind": "exact_git_blob",
            "git_blob": "4249083c8cae9c5bbcb5c00b9722de5bc66a8511",
            "note": "Exact repository object; no containing commit was found in reachable/reflog history for this path. Lines 3 and 4 retain their two trailing ASCII spaces.",
        },
    },
    {
        "original_path": "research/arithmetic-library/linear-congruence-complete-rfc-v1.md",
        "archive_path": ARCHIVE_DIRECTORY + "/linear-congruence-complete-rfc-v1.md.snapshot",
        "bytes": 6351,
        "sha256": "857da462982d7798c69ca24053378c31e52d1b58fcc401bfe99ba92aac101383",
        "recovery": {
            "kind": "unchanged_current_bytes_plus_one_final_lf",
            "source_bytes": 6350,
            "source_sha256": "ce32b9b9922e46be8abb8a61ae4a4cb3461f2dea6eeb56a65bfbc2684991cf35",
            "append_hex": "0a",
            "note": "The recovered bytes match the literal Alpha-v30 record; no source commit is claimed.",
        },
    },
    {
        "original_path": "research/arithmetic-library/wmi-qr-replay.md",
        "archive_path": ARCHIVE_DIRECTORY + "/wmi-qr-replay.md.snapshot",
        "bytes": 43290,
        "sha256": "b7774571ff25d0ab1c35707e4aa8b074b584179307bc25c2d9bcb5dc7a17f960",
        "recovery": {
            "kind": "exact_git_commit_blob",
            "git_commit": "fc835a0eb29b446f976ad1254e53c6bb96dee89e",
            "git_blob": "40d70de2d926b6a217d747242d0668454bf93d47",
            "note": "The original path in this commit supplies the exact pinned bytes; the later current-file replay log remains untouched.",
        },
    },
)


def archive_paths() -> tuple[str, ...]:
    """Return only the five fixed relative archive paths; do not read evidence."""
    return tuple(item["archive_path"] for item in ARCHIVES)


def archive_bindings() -> list[dict]:
    """Return independent copies of literal metadata, not verification receipts."""
    return deepcopy(list(ARCHIVES))


def _relative(value: object) -> str:
    if (type(value) is not str or not value or len(value) > 4096
            or any(ord(char) < 32 for char in value)
            or any(char in value for char in ("\\", ":", "*", "?", "[", "]"))
            or any(part in ("", ".", "..") for part in value.split("/"))
            or PurePosixPath(value).is_absolute()
            or PurePosixPath(value).as_posix() != value):
        raise HistoricalEvidenceError("inherited evidence requires a canonical relative ordinary-file path")
    return value


def _record(record: object) -> tuple[str, int, str]:
    if type(record) is not dict or set(record) != {"path", "bytes", "sha256", "role"}:
        raise HistoricalEvidenceError("inherited evidence requires exactly path, bytes, sha256, and role")
    path = _relative(record["path"])
    size, digest, role = record["bytes"], record["sha256"], record["role"]
    if type(size) is not int or not 0 < size <= MAX_DOCUMENT_BYTES:
        raise HistoricalEvidenceError("inherited evidence size exceeds the unchanged 64 MiB bound or is invalid")
    if type(digest) is not str or _SHA256.fullmatch(digest) is None:
        raise HistoricalEvidenceError("inherited evidence requires a lowercase SHA-256 digest")
    if type(role) is not str or not role or len(role) > 256:
        raise HistoricalEvidenceError("inherited evidence requires a nonempty document role")
    return path, size, digest


def _verified_path(relative: str, size: int, digest: str, root: Path | str) -> Path:
    _relative(relative)
    if not isinstance(root, (Path, str)):
        raise HistoricalEvidenceError("evidence root must be an ordinary filesystem path")
    try:
        # Do not resolve(): every component, including the supplied root, must
        # pass the existing no-follow open walk rather than hide a symlink.
        directory = transport._absolute_path(root)
        path = directory / relative
        transport._read_file(path, owner_uid=os.getuid(), expected_sha256=digest,
                             expected_bytes=size, capture=False)
    except (OSError, transport.CatalogError) as error:
        raise HistoricalEvidenceError(f"historical evidence did not verify: {relative}: {error}") from error
    return path


def archive_evidence_documents(root: Path | str = ROOT) -> list[dict]:
    """Authenticate all five snapshots before returning new document records."""
    records = []
    for item in ARCHIVES:
        _verified_path(item["archive_path"], item["bytes"], item["sha256"], root)
        records.append({"path": item["archive_path"], "bytes": item["bytes"],
                        "sha256": item["sha256"], "role": ARCHIVE_ROLE})
    return records


def verify_inherited_document(record: dict, *, root: Path | str = ROOT) -> Path:
    """Verify exactly a reviewed historical record or its actual current path.

    The five original paths are reserved for their literal old size and digest.
    An altered old record cannot escape to the current file, even if that file
    matches the alteration. Every other record must match its current ordinary
    file. No search, missing-file fallback, suffix rule, or hash alias exists.
    """
    path, size, digest = _record(record)
    for item in ARCHIVES:
        if path == item["original_path"]:
            if size != item["bytes"] or digest != item["sha256"]:
                raise HistoricalEvidenceError("the literal historical record changed; no fallback is permitted")
            return _verified_path(item["archive_path"], size, digest, root)
    return _verified_path(path, size, digest, root)


__all__ = [
    "ARCHIVES", "ARCHIVE_DIRECTORY", "ARCHIVE_ROLE", "MAX_DOCUMENT_BYTES",
    "HistoricalEvidenceError", "archive_paths", "archive_bindings",
    "archive_evidence_documents", "verify_inherited_document",
]
