#!/usr/bin/env python3
"""Verify one exact predecessor row in the append-only WMI job ledger."""

from __future__ import annotations

import re
from pathlib import Path
import sys


FIELDS = (
    "timestamp",
    "job_id",
    "script",
    "dependency_job_id",
    "workdir",
    "git_commit",
    "git_dirty",
    "sync_timestamp",
    "script_sha256",
)
MAX_LEDGER_BYTES = 16 * 1024 * 1024
MAX_FIELD_CHARS = 4_096


class LedgerError(ValueError):
    """The submission ledger is malformed or does not bind the predecessor."""


def _safe_field(value: str) -> bool:
    return len(value) <= MAX_FIELD_CHARS and not any(
        ord(character) < 32 or ord(character) == 127 for character in value
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    if path.is_symlink() or not path.is_file():
        raise LedgerError("submission ledger is not one regular file")
    raw = path.read_bytes()
    if len(raw) > MAX_LEDGER_BYTES:
        raise LedgerError("submission ledger exceeds the byte limit")
    if not raw or not raw.endswith(b"\n") or b"\r" in raw or b"\0" in raw:
        raise LedgerError("submission ledger is not complete canonical TSV")
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise LedgerError("submission ledger is not UTF-8") from exc
    if not lines or tuple(lines[0].split("\t")) != FIELDS:
        raise LedgerError("submission ledger has an incompatible header")

    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(lines[1:], 2):
        values = line.split("\t")
        if len(values) != len(FIELDS) or not all(_safe_field(value) for value in values):
            raise LedgerError(f"submission ledger row {line_number} is malformed")
        row = dict(zip(FIELDS, values, strict=True))
        script_path = Path(row["script"])
        workdir_path = Path(row["workdir"])
        if (
            re.fullmatch(r"[0-9TZ:+-]+", row["timestamp"]) is None
            or re.fullmatch(r"[0-9]+", row["job_id"]) is None
            or (
                row["dependency_job_id"]
                and re.fullmatch(r"[0-9]+", row["dependency_job_id"]) is None
            )
            or not row["script"]
            or script_path.is_absolute()
            or ".." in script_path.parts
            or re.fullmatch(r"[A-Za-z0-9._/-]+", row["script"]) is None
            or not workdir_path.is_absolute()
            or re.fullmatch(r"[0-9a-f]{40}", row["git_commit"]) is None
            or row["git_dirty"] not in {"true", "false"}
            or re.fullmatch(r"[0-9TZ:+-]+", row["sync_timestamp"]) is None
            or re.fullmatch(r"[0-9a-f]{64}", row["script_sha256"]) is None
        ):
            raise LedgerError(f"submission ledger row {line_number} is malformed")
        rows.append(row)
    return rows


def verify_predecessor(
    path: Path,
    *,
    job_id: str,
    script: str,
    workdir: str,
    commit: str,
    sync_timestamp: str,
    script_sha256: str,
) -> None:
    matches = [row for row in read_rows(path) if row["job_id"] == job_id]
    if len(matches) != 1:
        raise LedgerError("dependency is absent or duplicated")
    row = matches[0]
    expected = {
        "script": script,
        "workdir": workdir,
        "git_commit": commit,
        "git_dirty": "false",
        "sync_timestamp": sync_timestamp,
        "script_sha256": script_sha256,
    }
    if any(row[name] != value for name, value in expected.items()):
        raise LedgerError("dependency belongs to a different source chain")


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 7:
        raise SystemExit(
            "usage: verify_wmi_submission_predecessor.py "
            "LEDGER JOB_ID SCRIPT WORKDIR COMMIT SYNC_TIMESTAMP SCRIPT_SHA256"
        )
    path, job_id, script, workdir, commit, sync_timestamp, script_sha256 = arguments
    try:
        verify_predecessor(
            Path(path),
            job_id=job_id,
            script=script,
            workdir=workdir,
            commit=commit,
            sync_timestamp=sync_timestamp,
            script_sha256=script_sha256,
        )
    except (LedgerError, OSError) as exc:
        print(f"WMI dependency verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
