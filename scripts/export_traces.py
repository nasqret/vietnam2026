#!/usr/bin/env python3
"""Validate Peano Lab v=1 traces and export deterministic train/val rows.

Raw inputs are concatenated *sessions*.  A session is one or more adjacent
version-1 tactic records followed immediately by the four-field footer from
``docs/PEANO_LAB_DESIGN.md`` section 4.  The footer deliberately has no
session id, so a footer without a preceding tactic record is ambiguous and is
rejected.

The output files contain independent transition examples, not replayable
sessions.  Every row therefore keeps the exact binding nine-field transition
schema and field order.  Session and step continuity are strict input
validation properties; deduplication may leave gaps in output step numbers.

Splitting happens by exact canonical footer theorem.  Thus every session for
one theorem belongs to one split.  Semantic duplicates (all transition fields
except ``session`` and ``step``) are removed globally and can never leak into
both splits.  Exact theorem exclusions are applied before splitting; callers
must separately account for renamed or otherwise equivalent variants.

Only the Python standard library is used so this script can run in the same
small environments as the rest of Peano Lab's data pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


TRACE_VERSION = 1
STEP_FIELDS = (
    "v",
    "session",
    "step",
    "goals_before",
    "focus",
    "tactic",
    "goals_after",
    "status",
    "error",
)
FOOTER_FIELDS = ("qed", "theorem", "proof_size", "tactic_count")
DEFAULT_SEED = "peano-lab-v1"
DEFAULT_VAL_FRACTION = 0.1


class TraceFormatError(ValueError):
    """A raw file is not a complete, clean v=1 trace stream."""


@dataclass(frozen=True)
class TraceSession:
    """One validated raw session and its source location."""

    session_id: str
    steps: tuple[dict[str, object], ...]
    footer: dict[str, object]
    source: Path
    first_line: int

    @property
    def theorem(self) -> str:
        return self.footer["theorem"]  # type: ignore[return-value]


@dataclass(frozen=True)
class ExportResult:
    """Paths and in-memory statistics produced by :func:`export_traces`."""

    train_path: Path
    val_path: Path
    stats_path: Path
    stats: dict[str, object]


def _location(path: Path, line_number: int | None = None) -> str:
    return str(path) if line_number is None else f"{path}:{line_number}"


def _fail(path: Path, line_number: int, message: str) -> TraceFormatError:
    return TraceFormatError(f"{_location(path, line_number)}: {message}")


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _decode_line(path: Path, line_number: int, line: str) -> dict[str, object]:
    if not line:
        raise _fail(path, line_number, "blank lines are not valid JSONL records")
    try:
        value = json.loads(
            line,
            object_pairs_hook=_object_from_pairs,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise _fail(path, line_number, f"invalid JSON: {exc}") from exc
    if type(value) is not dict:
        raise _fail(path, line_number, "each JSONL record must be an object")
    return value


def _is_int(value: object) -> bool:
    return type(value) is int


def _safe_text(value: object, *, nonempty: bool = False) -> bool:
    if type(value) is not str or (nonempty and not value):
        return False
    return not any(
        unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for char in value
    )


def _check_fields(
    record: Mapping[str, object],
    expected: tuple[str, ...],
    path: Path,
    line_number: int,
) -> None:
    actual = tuple(record)
    if actual != expected:
        raise _fail(
            path,
            line_number,
            "field order/set must be "
            f"{list(expected)!r}, got {list(actual)!r}",
        )


def _check_goals(
    value: object, field: str, path: Path, line_number: int
) -> list[str]:
    if type(value) is not list:
        raise _fail(path, line_number, f"{field} must be a JSON array")
    if not all(_safe_text(goal, nonempty=True) for goal in value):
        raise _fail(
            path,
            line_number,
            f"{field} must contain only non-empty control-free strings",
        )
    return value  # type: ignore[return-value]


def _validate_step(
    record: dict[str, object], path: Path, line_number: int
) -> dict[str, object]:
    _check_fields(record, STEP_FIELDS, path, line_number)

    if record["v"] != TRACE_VERSION or not _is_int(record["v"]):
        raise _fail(path, line_number, "v must be the integer 1")
    if not _safe_text(record["session"], nonempty=True):
        raise _fail(path, line_number, "session must be non-empty control-free text")
    if not _is_int(record["step"]) or record["step"] < 1:  # type: ignore[operator]
        raise _fail(path, line_number, "step must be a positive integer")

    before = _check_goals(record["goals_before"], "goals_before", path, line_number)
    after = _check_goals(record["goals_after"], "goals_after", path, line_number)
    focus = record["focus"]
    if not _is_int(focus) or focus < 0:  # type: ignore[operator]
        raise _fail(path, line_number, "focus must be a non-negative integer")
    if before and focus >= len(before):  # type: ignore[operator]
        raise _fail(path, line_number, "focus is outside goals_before")
    if not before and focus != 0:
        raise _fail(path, line_number, "focus must be zero when goals_before is empty")

    tactic = record["tactic"]
    if not _safe_text(tactic, nonempty=True) or not tactic.strip():  # type: ignore[union-attr]
        raise _fail(path, line_number, "tactic must be non-blank control-free text")
    status, error = record["status"], record["error"]
    if status == "ok":
        if error is not None:
            raise _fail(path, line_number, "an ok transition must have error: null")
    elif status == "error":
        if not _safe_text(error, nonempty=True):
            raise _fail(
                path,
                line_number,
                "an error transition needs non-empty control-free error text",
            )
        if after != before:
            raise _fail(
                path,
                line_number,
                "an error transition must be transactional (goals_after == goals_before)",
            )
    else:
        raise _fail(path, line_number, "status must be exactly 'ok' or 'error'")

    # Rebuild explicitly: output key order does not depend on decoder details.
    return {field: record[field] for field in STEP_FIELDS}


def _validate_footer(
    record: dict[str, object], path: Path, line_number: int
) -> dict[str, object]:
    _check_fields(record, FOOTER_FIELDS, path, line_number)
    if type(record["qed"]) is not bool:
        raise _fail(path, line_number, "qed must be a boolean")
    if not _safe_text(record["theorem"], nonempty=True):
        raise _fail(path, line_number, "theorem must be non-empty control-free text")
    for field in ("proof_size", "tactic_count"):
        value = record[field]
        if not _is_int(value) or value < 0:  # type: ignore[operator]
            raise _fail(path, line_number, f"{field} must be a non-negative integer")
    return {field: record[field] for field in FOOTER_FIELDS}


def _validate_footer_matches_initial_goal(
    steps: Sequence[Mapping[str, object]],
    footer: Mapping[str, object],
    path: Path,
    line_number: int,
) -> None:
    """Bind split/exclusion metadata to the session that produced it."""

    initial = steps[0]["goals_before"]
    if type(initial) is not list or len(initial) != 1:
        raise _fail(
            path,
            line_number,
            "a complete session must start from exactly one original goal",
        )
    rendered = initial[0]
    if type(rendered) is not str:
        raise _fail(path, line_number, "the initial goal must be canonical text")
    declarations, turnstile, theorem = rendered.rpartition("⊢")
    if not turnstile or not theorem.strip():
        raise _fail(
            path,
            line_number,
            "the initial goal must contain a canonical turnstile and target",
        )
    if theorem.strip() != footer["theorem"]:
        raise _fail(
            path,
            line_number,
            "footer theorem does not match the session's original goal",
        )
    prefix = declarations.strip()
    if prefix:
        entries = [entry.strip() for entry in prefix.split(",")]
        if not all(
            entry.endswith(" : ℕ") and bool(entry[: -len(" : ℕ")].strip())
            for entry in entries
        ):
            raise _fail(
                path,
                line_number,
                "an original goal may contain only free-variable declarations",
            )


def load_trace_file(path: str | os.PathLike[str]) -> tuple[TraceSession, ...]:
    """Read and strictly validate every complete session in one JSONL file."""

    source = Path(path)
    if not source.is_file():
        raise TraceFormatError(f"{source}: input is not a regular file")
    try:
        raw = source.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise TraceFormatError(f"{source}: input is not valid UTF-8") from exc
    if not raw:
        raise TraceFormatError(f"{source}: input is empty")
    if not raw.endswith("\n"):
        raise TraceFormatError(f"{source}: incomplete JSONL stream (missing final newline)")

    sessions: list[TraceSession] = []
    open_steps: list[dict[str, object]] = []
    open_session: str | None = None
    first_line = 0

    # split("\n") preserves an interior/final blank; discard only the one
    # terminator guaranteed above so dirty blank records remain visible.
    lines = raw.split("\n")[:-1]
    for line_number, line in enumerate(lines, 1):
        record = _decode_line(source, line_number, line)
        first_key = next(iter(record), None)

        if first_key == "v" or "v" in record:
            step = _validate_step(record, source, line_number)
            session_id = step["session"]
            if open_session is None:
                if step["step"] != 1:
                    raise _fail(source, line_number, "a session must begin at step 1")
                open_session = session_id  # type: ignore[assignment]
                first_line = line_number
            elif session_id != open_session:
                raise _fail(
                    source,
                    line_number,
                    f"session {open_session!r} is missing its footer before "
                    f"session {session_id!r}",
                )

            expected_step = len(open_steps) + 1
            if step["step"] != expected_step:
                raise _fail(
                    source,
                    line_number,
                    f"session {open_session!r} expected step {expected_step}, "
                    f"got {step['step']!r}",
                )
            if open_steps and step["goals_before"] != open_steps[-1]["goals_after"]:
                raise _fail(
                    source,
                    line_number,
                    f"session {open_session!r} breaks goal-state continuity",
                )
            open_steps.append(step)
            continue

        if first_key == "qed" or "qed" in record:
            footer = _validate_footer(record, source, line_number)
            if open_session is None:
                raise _fail(
                    source,
                    line_number,
                    "footer has no preceding tactic records and cannot be associated "
                    "with a session",
                )
            if footer["tactic_count"] != len(open_steps):
                raise _fail(
                    source,
                    line_number,
                    f"footer tactic_count is {footer['tactic_count']!r}, expected "
                    f"{len(open_steps)}",
                )
            if footer["qed"] is True and open_steps[-1]["goals_after"] != []:
                raise _fail(
                    source,
                    line_number,
                    "a qed footer requires the final transition to have no goals",
                )
            _validate_footer_matches_initial_goal(
                open_steps, footer, source, line_number
            )
            sessions.append(
                TraceSession(
                    session_id=open_session,
                    steps=tuple(open_steps),
                    footer=footer,
                    source=source,
                    first_line=first_line,
                )
            )
            open_steps = []
            open_session = None
            first_line = 0
            continue

        raise _fail(
            source,
            line_number,
            "record is neither an ordered v=1 transition nor an ordered footer",
        )

    if open_session is not None:
        raise TraceFormatError(
            f"{source}: session {open_session!r} beginning at line {first_line} "
            "is missing its footer"
        )
    if not sessions:
        raise TraceFormatError(f"{source}: input contains no complete sessions")
    return tuple(sessions)


def load_sessions(
    paths: Iterable[str | os.PathLike[str]],
) -> tuple[TraceSession, ...]:
    """Validate and collate files, rejecting duplicate paths/session ids."""

    normalized: list[Path] = []
    seen_paths: set[Path] = set()
    for value in paths:
        path = Path(value)
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError as exc:
            raise TraceFormatError(f"{path}: input does not exist") from exc
        if resolved in seen_paths:
            raise TraceFormatError(f"{path}: input path was supplied more than once")
        seen_paths.add(resolved)
        normalized.append(path)
    if not normalized:
        raise TraceFormatError("at least one input JSONL file is required")

    sessions: list[TraceSession] = []
    seen_sessions: dict[str, TraceSession] = {}
    for path in sorted(normalized, key=lambda item: str(item.resolve())):
        for session in load_trace_file(path):
            previous = seen_sessions.get(session.session_id)
            if previous is not None:
                raise TraceFormatError(
                    f"{session.source}:{session.first_line}: duplicate session id "
                    f"{session.session_id!r}; first seen at "
                    f"{previous.source}:{previous.first_line}"
                )
            seen_sessions[session.session_id] = session
            sessions.append(session)
    return tuple(sessions)


def _compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _line_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False) + "\n"


def _semantic_key(step: Mapping[str, object]) -> str:
    semantic = {
        field: step[field]
        for field in STEP_FIELDS
        if field not in {"session", "step"}
    }
    return _compact_json(semantic)


def _session_sort_key(session: TraceSession) -> tuple[str, str, str, int]:
    return (
        session.theorem,
        session.session_id,
        str(session.source.resolve()),
        session.first_line,
    )


def _rank(seed: str, theorem: str) -> str:
    material = f"{seed}\0{theorem}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _choose_val_theorems(
    theorems: Sequence[str], val_fraction: float, seed: str
) -> frozenset[str]:
    if type(val_fraction) not in {float, int} or isinstance(val_fraction, bool):
        raise TypeError("val_fraction must be a number")
    fraction = float(val_fraction)
    if not 0.0 <= fraction < 1.0:
        raise ValueError("val_fraction must satisfy 0 <= val_fraction < 1")
    if not _safe_text(seed, nonempty=True):
        raise ValueError("seed must be non-empty control-free text")

    ordered = sorted(set(theorems), key=lambda theorem: (_rank(seed, theorem), theorem))
    if len(ordered) < 2 or fraction == 0.0:
        return frozenset()
    count = int(len(ordered) * fraction)
    count = max(1, min(len(ordered) - 1, count))
    return frozenset(ordered[:count])


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_source_text(sessions: Iterable[TraceSession]) -> str:
    chunks: list[str] = []
    for session in sorted(sessions, key=_session_sort_key):
        chunks.extend(_line_json(step) for step in session.steps)
        chunks.append(_line_json(session.footer))
    return "".join(chunks)


def _stage_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        stream = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        )
        temporary = Path(stream.name)
        with stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        result = temporary
        temporary = None
        return result
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _reserved_backup_path(path: Path) -> Path:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".bak", dir=path.parent
    )
    os.close(descriptor)
    reserved = Path(name)
    reserved.unlink()
    return reserved


def publish_text_artifact_set(artifacts: Sequence[tuple[Path, str]]) -> None:
    """Stage all artifacts, then publish them with ordinary-failure rollback.

    A filesystem cannot atomically replace three unrelated names in one call.
    Staging first prevents encoding/write failures from changing any output;
    temporary backups restore the previous coherent set if a later replace
    fails.  ``stats.json`` is intentionally the final published member.
    """

    for path, _ in artifacts:
        path.parent.mkdir(parents=True, exist_ok=True)
        if os.path.lexists(path) and not os.path.isfile(path):
            raise ValueError(
                f"export artifact must be a regular file or absent: {path}"
            )

    staged: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    installed: list[Path] = []
    try:
        for path, content in artifacts:
            staged[path] = _stage_text(path, content)

        for path, _ in artifacts:
            if os.path.lexists(path):
                backup = _reserved_backup_path(path)
                backups[path] = backup
                os.replace(path, backup)

        for path, _ in artifacts:
            installed.append(path)
            os.replace(staged[path], path)
            staged.pop(path)
    except BaseException as original:
        rollback_errors: list[str] = []
        rollback_exceptions: list[BaseException] = []
        for path in reversed(installed):
            try:
                path.unlink(missing_ok=True)
            except BaseException as exc:
                rollback_exceptions.append(exc)
                if path not in backups and os.path.lexists(path):
                    rollback_errors.append(f"remove {path}: {exc}")
        for path, backup in reversed(tuple(backups.items())):
            if not os.path.lexists(backup):
                if os.path.lexists(path):
                    backups.pop(path)
                else:
                    rollback_errors.append(
                        f"restore {path}: both destination and backup are missing"
                    )
                continue
            try:
                os.replace(backup, path)
                backups.pop(path)
            except BaseException as exc:
                rollback_exceptions.append(exc)
                if not os.path.lexists(backup) and os.path.lexists(path):
                    backups.pop(path)
                else:
                    rollback_errors.append(f"restore {path}: {exc}")
        if rollback_errors:
            preserved = tuple(
                backup for backup in backups.values() if os.path.lexists(backup)
            )
            backups.clear()  # never delete the only recoverable old copies
            raise RuntimeError(
                "trace export failed and rollback was incomplete: "
                + "; ".join(rollback_errors)
                + "; backups preserved at "
                + ", ".join(str(path) for path in preserved)
            ) from original
        if rollback_exceptions:
            raise rollback_exceptions[0] from original
        raise
    finally:
        for temporary in (*staged.values(), *backups.values()):
            temporary.unlink(missing_ok=True)


def _paths_alias(first: Path, second: Path) -> bool:
    """Recognize spelling, symlink, hard-link, and case-folded aliases.

    ``Path.resolve`` alone is insufficient on a case-insensitive filesystem:
    an existing ``TRAIN.JSONL`` input can also be reached through the notional
    output spelling ``train.jsonl``.  ``samefile`` asks the filesystem about
    the existing objects and also covers hard links.  The lexical comparison
    remains necessary when the destination does not exist yet.
    """

    try:
        if first.resolve(strict=False) == second.resolve(strict=False):
            return True
    except (OSError, RuntimeError):
        pass
    try:
        return os.path.samefile(first, second)
    except OSError:
        return False


def export_traces(
    inputs: Iterable[str | os.PathLike[str]],
    output_dir: str | os.PathLike[str],
    *,
    val_fraction: float = DEFAULT_VAL_FRACTION,
    seed: str = DEFAULT_SEED,
    exclude_theorems: Iterable[str] = (),
) -> ExportResult:
    """Validate, filter, deduplicate, split, and write the three M9 artifacts.

    ``exclude_theorems`` contains exact canonical footer strings.  Complete
    matching sessions are omitted before deduplication and their counts remain
    visible in ``stats.json``.
    """

    sessions = load_sessions(inputs)
    # Validate split arguments even if exclusions leave no eligible sessions.
    _choose_val_theorems((), val_fraction, seed)

    excluded_set: set[str] = set()
    for theorem in exclude_theorems:
        if not _safe_text(theorem, nonempty=True):
            raise ValueError("excluded theorems must be non-empty control-free text")
        excluded_set.add(theorem)

    excluded = tuple(session for session in sessions if session.theorem in excluded_set)
    eligible = tuple(session for session in sessions if session.theorem not in excluded_set)
    theorems = sorted({session.theorem for session in eligible})
    val_theorems = _choose_val_theorems(theorems, val_fraction, seed)
    train_theorems = frozenset(theorems) - val_theorems

    # One representative per semantic transition, chosen independently of
    # input argument/file order.  Choosing only after theorem assignment makes
    # it explicit that a duplicate belongs to exactly one split.
    candidates: dict[str, list[tuple[TraceSession, dict[str, object]]]] = {}
    for session in eligible:
        for step in session.steps:
            candidates.setdefault(_semantic_key(step), []).append((session, step))

    representatives: list[tuple[str, TraceSession, dict[str, object]]] = []
    for semantic_key, choices in candidates.items():
        session, step = min(
            choices,
            key=lambda choice: (
                choice[0].theorem,
                choice[0].session_id,
                choice[1]["step"],
                str(choice[0].source.resolve()),
                choice[0].first_line,
            ),
        )
        representatives.append((semantic_key, session, step))

    representatives.sort(
        key=lambda item: (
            item[1].theorem,
            item[1].session_id,
            item[2]["step"],
            item[0],
        )
    )
    train_rows = [
        step for _, session, step in representatives if session.theorem in train_theorems
    ]
    val_rows = [
        step for _, session, step in representatives if session.theorem in val_theorems
    ]

    train_text = "".join(_line_json(row) for row in train_rows)
    val_text = "".join(_line_json(row) for row in val_rows)
    exported_rows = train_rows + val_rows
    statuses = Counter(row["status"] for row in exported_rows)
    tactic_distribution = Counter(row["tactic"] for row in exported_rows)
    total_exported = len(exported_rows)
    error_count = statuses["error"]

    eligible_transition_count = sum(len(session.steps) for session in eligible)
    excluded_transition_count = sum(len(session.steps) for session in excluded)
    source_theorems = sorted({session.theorem for session in sessions})
    excluded_present = sorted({session.theorem for session in excluded})

    stats: dict[str, object] = {
        "v": TRACE_VERSION,
        "split": {
            "method": "sha256-ranked-exact-footer-theorem-v1",
            "seed": seed,
            "val_fraction": float(val_fraction),
            "group": "exact canonical footer theorem",
        },
        "source": {
            "files": len({session.source.resolve() for session in sessions}),
            "sessions": len(sessions),
            "transitions": sum(len(session.steps) for session in sessions),
            "canonical_sessions_sha256": _sha256_text(
                _canonical_source_text(sessions)
            ),
        },
        "exclusions": {
            "requested_theorems": sorted(excluded_set),
            "matched_theorems": excluded_present,
            "sessions": len(excluded),
            "transitions": excluded_transition_count,
        },
        "deduplication": {
            "eligible_transitions": eligible_transition_count,
            "unique_transitions": total_exported,
            "duplicates_removed": eligible_transition_count - total_exported,
            "identity": "v+goals_before+focus+tactic+goals_after+status+error",
        },
        "theorem_coverage": {
            "source_count": len(source_theorems),
            "source": source_theorems,
            "eligible_count": len(theorems),
            "eligible": theorems,
            "train_count": len(train_theorems),
            "train": sorted(train_theorems),
            "val_count": len(val_theorems),
            "val": sorted(val_theorems),
        },
        "splits": {
            "train": {
                "sessions": sum(
                    session.theorem in train_theorems for session in eligible
                ),
                "records": len(train_rows),
                "sha256": _sha256_text(train_text),
            },
            "val": {
                "sessions": sum(session.theorem in val_theorems for session in eligible),
                "records": len(val_rows),
                "sha256": _sha256_text(val_text),
            },
        },
        "outcomes": {
            "ok": statuses["ok"],
            "error": error_count,
            "total": total_exported,
            "failure_ratio": error_count / total_exported if total_exported else 0.0,
        },
        "tactic_distribution": {
            tactic: tactic_distribution[tactic]
            for tactic in sorted(tactic_distribution)
        },
    }
    stats_text = json.dumps(stats, ensure_ascii=False, indent=2) + "\n"

    destination = Path(output_dir)
    train_path = destination / "train.jsonl"
    val_path = destination / "val.jsonl"
    stats_path = destination / "stats.json"
    source_paths = {session.source for session in sessions}
    for artifact in (train_path, val_path, stats_path):
        if any(_paths_alias(artifact, source) for source in source_paths):
            raise ValueError(
                f"refusing to overwrite input trace file with export artifact {artifact}"
            )
    publish_text_artifact_set(
        (
            (train_path, train_text),
            (val_path, val_text),
            (stats_path, stats_text),
        )
    )
    return ExportResult(train_path, val_path, stats_path, stats)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Peano Lab v=1 JSONL sessions and export deterministic, "
            "deduplicated train/val transition rows."
        )
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="raw JSONL trace files")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="directory for train.jsonl, val.jsonl, and stats.json",
    )
    parser.add_argument(
        "--val-fraction",
        type=float,
        default=DEFAULT_VAL_FRACTION,
        help=f"theorem-group validation fraction (default: {DEFAULT_VAL_FRACTION})",
    )
    parser.add_argument(
        "--seed",
        default=DEFAULT_SEED,
        help=f"stable split seed (default: {DEFAULT_SEED!r})",
    )
    parser.add_argument(
        "--exclude-theorem",
        action="append",
        default=[],
        metavar="FORMULA",
        help=(
            "exclude every session whose footer theorem exactly matches FORMULA; "
            "repeat for multiple held-out formulas"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = export_traces(
            args.inputs,
            args.output_dir,
            val_fraction=args.val_fraction,
            seed=args.seed,
            exclude_theorems=args.exclude_theorem,
        )
    except (OSError, RuntimeError, TraceFormatError, TypeError, ValueError) as exc:
        print(f"trace export failed: {exc}", file=sys.stderr)
        return 2

    outcomes = result.stats["outcomes"]
    splits = result.stats["splits"]
    print(
        "exported "
        f"{outcomes['total']} unique transitions "  # type: ignore[index]
        f"({splits['train']['records']} train, "  # type: ignore[index]
        f"{splits['val']['records']} val); "  # type: ignore[index]
        f"failure ratio {outcomes['failure_ratio']:.4f}"  # type: ignore[index]
    )
    print(f"stats: {result.stats_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_SEED",
    "DEFAULT_VAL_FRACTION",
    "ExportResult",
    "FOOTER_FIELDS",
    "STEP_FIELDS",
    "TRACE_VERSION",
    "TraceFormatError",
    "TraceSession",
    "export_traces",
    "load_sessions",
    "load_trace_file",
    "main",
    "publish_text_artifact_set",
]


# Backward-compatible private spelling for older tests/tools.  New producers
# use the public name so the rollback contract is shared rather than copied.
_publish_artifact_set = publish_text_artifact_set
