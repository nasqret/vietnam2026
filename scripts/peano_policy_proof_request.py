#!/usr/bin/env python3
"""Create, receive, validate, and run immutable WMI theorem requests."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
from typing import Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON, Path(__file__).resolve().parent):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import eval_trained_peano_policy as trained_cli  # noqa: E402


REQUEST_VERSION = 1
MAX_REQUEST_BYTES = 16_000
MAX_REPORT_BYTES = 64_000_000
REQUEST_ROOT = REPOSITORY_ROOT / "results" / "peano-policy" / "requests"
OUTPUT_ROOT = REPOSITORY_ROOT / "results" / "peano-policy" / "user-proofs"
PROOF_LEDGER = REPOSITORY_ROOT / "logs" / "proof-requests.tsv"
PROOF_LEDGER_FIELDS = (
    "timestamp",
    "job_id",
    "request_id",
    "request_sha256",
)
REQUEST_FIELDS = (
    "created_at",
    "id",
    "k",
    "max_steps",
    "nonce",
    "sample",
    "seed",
    "theorem",
    "v",
)
_REQUEST_ID_RE = re.compile(r"[0-9a-f]{64}")
_NONCE_RE = re.compile(r"[0-9a-f]{32}")
_TIMESTAMP_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_LEDGER_TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})"
)
_JOB_ID_RE = re.compile(r"[0-9]+")


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _request_digest(record_without_id: Mapping[str, object]) -> str:
    return _sha256_bytes(_json_bytes(record_without_id))


def _validate_request_id(value: object) -> str:
    if type(value) is not str or _REQUEST_ID_RE.fullmatch(value) is None:
        raise ValueError("request id must be exactly 64 lowercase hexadecimal characters")
    return value


def _request_path(request_id: str) -> Path:
    return REQUEST_ROOT / f"{_validate_request_id(request_id)}.json"


def build_request(
    *,
    theorem: str,
    k: int,
    max_steps: int,
    seed: int,
    sample: bool,
    created_at: str | None = None,
    nonce: str | None = None,
) -> dict[str, object]:
    theorem_source = trained_cli._preflight_user_theorem(theorem)
    if type(k) is not int or not 1 <= k <= 256:
        raise ValueError("k must lie between 1 and 256")
    if type(max_steps) is not int or not 1 <= max_steps <= trained_cli.MAX_BATCH_TACTICS:
        raise ValueError(
            f"max_steps must lie between 1 and {trained_cli.MAX_BATCH_TACTICS}"
        )
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample) is not bool:
        raise TypeError("sample must be a Boolean")
    if k > 1 and not sample:
        raise ValueError("k greater than 1 requires sampled decoding")
    trained_cli._validate_search_budget(
        rollouts=k,
        max_steps=max_steps,
        max_new_tokens=None,
    )
    timestamp = created_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    request_nonce = nonce or secrets.token_hex(16)
    if _TIMESTAMP_RE.fullmatch(timestamp) is None:
        raise ValueError("request timestamp is not canonical UTC")
    if _NONCE_RE.fullmatch(request_nonce) is None:
        raise ValueError("request nonce must be 32 lowercase hexadecimal characters")
    body: dict[str, object] = {
        "created_at": timestamp,
        "k": k,
        "max_steps": max_steps,
        "nonce": request_nonce,
        "sample": sample,
        "seed": seed,
        "theorem": theorem_source,
        "v": REQUEST_VERSION,
    }
    return {"id": _request_digest(body), **body}


def validate_request(value: object, *, expected_id: str | None = None) -> dict[str, object]:
    if type(value) is not dict or tuple(sorted(value)) != REQUEST_FIELDS:
        raise ValueError("proof request has an incompatible field set")
    request_id = _validate_request_id(value.get("id"))
    if expected_id is not None and request_id != _validate_request_id(expected_id):
        raise ValueError("proof request id does not match its requested path")
    rebuilt = build_request(
        theorem=value.get("theorem"),  # type: ignore[arg-type]
        k=value.get("k"),  # type: ignore[arg-type]
        max_steps=value.get("max_steps"),  # type: ignore[arg-type]
        seed=value.get("seed"),  # type: ignore[arg-type]
        sample=value.get("sample"),  # type: ignore[arg-type]
        created_at=value.get("created_at"),  # type: ignore[arg-type]
        nonce=value.get("nonce"),  # type: ignore[arg-type]
    )
    if rebuilt != value:
        raise ValueError("proof request identity or canonical content is invalid")
    return rebuilt


def _parse_request_bytes(payload: bytes, *, expected_id: str | None = None) -> dict[str, object]:
    if not payload or len(payload) > MAX_REQUEST_BYTES:
        raise ValueError("proof request is empty or exceeds its byte limit")
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValueError(f"invalid proof-request JSON: {exc}") from None
    request = validate_request(value, expected_id=expected_id)
    if payload != _json_bytes(request):
        raise ValueError("proof request is not canonical JSON")
    return request


def _ensure_plain_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    current = path
    repository = REPOSITORY_ROOT.resolve()
    while current.resolve(strict=False) != repository:
        if current.is_symlink() or not current.is_dir():
            raise ValueError(f"request/output directory is not plain: {current}")
        current = current.parent


def _atomic_create(path: Path, payload: bytes) -> None:
    _ensure_plain_directory(path.parent)
    if os.path.lexists(path):
        raise FileExistsError(f"refusing to replace proof-request artifact: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            raise FileExistsError(
                f"refusing to replace proof-request artifact: {path}"
            ) from None
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


def receive_request(request_id: str, payload: bytes) -> tuple[Path, str]:
    request = _parse_request_bytes(payload, expected_id=request_id)
    canonical = _json_bytes(request)
    path = _request_path(request_id)
    _atomic_create(path, canonical)
    return path, _sha256_bytes(canonical)


def load_request(request_id: str) -> tuple[dict[str, object], Path, str]:
    path = _request_path(request_id)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_REQUEST_BYTES:
        raise ValueError(f"proof request is not one bounded regular file: {path}")
    payload = path.read_bytes()
    request = _parse_request_bytes(payload, expected_id=request_id)
    return request, path, _sha256_bytes(payload)


def _proof_ledger_identity(
    *,
    request_id: str,
    request_sha256: str,
) -> dict[str, object]:
    job_id = os.environ.get("SLURM_JOB_ID")
    if job_id is None or _JOB_ID_RE.fullmatch(job_id) is None:
        raise ValueError("a ledgered Slurm job id is required to run a WMI proof request")
    if not PROOF_LEDGER.is_file() or PROOF_LEDGER.is_symlink():
        raise ValueError("missing regular WMI proof-request ledger")
    with PROOF_LEDGER.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != PROOF_LEDGER_FIELDS:
            raise ValueError("WMI proof-request ledger has an incompatible header")
        matches = [dict(row) for row in reader if row.get("job_id") == job_id]
    if len(matches) != 1:
        raise ValueError("WMI proof-request ledger must contain exactly one job row")
    row = matches[0]
    if (
        row.get("request_id") != request_id
        or row.get("request_sha256") != request_sha256
        or _LEDGER_TIMESTAMP_RE.fullmatch(str(row.get("timestamp", ""))) is None
    ):
        raise ValueError("WMI proof-request ledger row does not match the request")
    return {
        "path": PROOF_LEDGER.relative_to(REPOSITORY_ROOT).as_posix(),
        "row": row,
        "row_sha256": _sha256_bytes(_json_bytes(row)),
    }


def _read_json_file(path: Path, *, maximum: int) -> tuple[dict[str, object], bytes]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > maximum:
        raise ValueError(f"result is not one bounded regular file: {path}")
    payload = path.read_bytes()
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValueError(f"invalid result JSON: {exc}") from None
    if type(value) is not dict:
        raise ValueError("result JSON must be one object")
    return value, payload


def run_request(request_id: str, adapter: Path) -> dict[str, object]:
    request, request_path, request_sha256 = load_request(request_id)
    ledger = _proof_ledger_identity(
        request_id=request_id,
        request_sha256=request_sha256,
    )
    _ensure_plain_directory(OUTPUT_ROOT)
    report = OUTPUT_ROOT / f"{request_id}.json"
    proof = OUTPUT_ROOT / f"{request_id}.pa"
    summary_path = OUTPUT_ROOT / f"{request_id}.run.json"
    for path in (report, proof, summary_path):
        if os.path.lexists(path):
            raise FileExistsError(f"refusing to replace WMI proof result: {path}")
    arguments = [
        "--adapter",
        str(adapter),
        "--theorem",
        str(request["theorem"]),
        "--k",
        str(request["k"]),
        "--max-steps",
        str(request["max_steps"]),
        "--seed",
        str(request["seed"]),
        "--output",
        str(report),
        "--proof-output",
        str(proof),
    ]
    if request["sample"] is True:
        arguments.append("--sample")
    status = trained_cli.main(arguments)
    if status not in {0, 1}:
        raise RuntimeError(f"trained prover returned an invalid status: {status}")
    report_record, report_payload = _read_json_file(report, maximum=MAX_REPORT_BYTES)
    publication = report_record.get("proof_publication")
    expected = "proof" if status == 0 else "no-proof"
    target, names = trained_cli.parse_formula_with_names(str(request["theorem"]))
    canonical_statement = trained_cli.pretty_formula(target, list(names))
    goals = report_record.get("goals")
    goal = goals[0] if type(goals) is list and len(goals) == 1 else None
    if (
        type(publication) is not dict
        or publication.get("status") != expected
        or report_record.get("seed") != request["seed"]
        or report_record.get("k") != request["k"]
        or report_record.get("max_steps") != request["max_steps"]
        or report_record.get("goal_count") != 1
        or type(goal) is not dict
        or goal.get("statement") != canonical_statement
        or goal.get("classical") is not False
        or goal.get("surface_profile") not in {"model-v1", "model-v2"}
        or goal.get("passed") is not (status == 0)
    ):
        raise RuntimeError("proof request, status, and evaluation report disagree")
    proof_record: dict[str, object] | None = None
    if status == 0:
        if not proof.is_file() or proof.is_symlink():
            raise RuntimeError("proved request did not publish one regular .pa file")
        proof_sha256 = hashlib.sha256(proof.read_bytes()).hexdigest()
        if publication.get("script_sha256") != proof_sha256:
            raise RuntimeError("published .pa file differs from its checked report")
        proof_record = {
            "path": proof.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": proof_sha256,
        }
    elif os.path.lexists(proof):
        raise RuntimeError("unproved request unexpectedly published a .pa file")
    final_request, final_path, final_sha256 = load_request(request_id)
    final_ledger = _proof_ledger_identity(
        request_id=request_id,
        request_sha256=final_sha256,
    )
    if (
        final_request != request
        or final_path != request_path
        or final_sha256 != request_sha256
        or final_ledger != ledger
    ):
        raise RuntimeError("proof request or request ledger changed during evaluation")
    summary: dict[str, object] = {
        "format": "peano-policy-wmi-proof-run",
        "v": 1,
        "status": "proved" if status == 0 else "no-proof",
        "request": {
            "id": request_id,
            "path": request_path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": request_sha256,
        },
        "request_ledger": ledger,
        "evaluation_report": {
            "path": report.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": _sha256_bytes(report_payload),
        },
        "proof": proof_record,
    }
    _atomic_create(summary_path, json.dumps(
        summary,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n")
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--theorem", required=True)
    create.add_argument("--k", type=int, default=1)
    create.add_argument("--max-steps", type=int, default=16)
    create.add_argument("--seed", type=int, default=20260728)
    create.add_argument("--sample", action="store_true")

    receive = subparsers.add_parser("receive")
    receive.add_argument("--request-id", required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--request-id", required=True)

    run = subparsers.add_parser("run")
    run.add_argument("--request-id", required=True)
    run.add_argument("--adapter", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "create":
        request = build_request(
            theorem=args.theorem,
            k=args.k,
            max_steps=args.max_steps,
            seed=args.seed,
            sample=args.sample,
        )
        sys.stdout.buffer.write(_json_bytes(request))
        return 0
    if args.command == "receive":
        payload = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        path, digest = receive_request(args.request_id, payload)
        print(json.dumps({"request": str(path), "sha256": digest}, sort_keys=True))
        return 0
    if args.command == "verify":
        _request, path, digest = load_request(args.request_id)
        print(json.dumps({"request": str(path), "sha256": digest}, sort_keys=True))
        return 0
    if args.command == "run":
        summary = run_request(args.request_id, args.adapter.resolve())
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    raise RuntimeError("unknown proof-request command")


if __name__ == "__main__":
    raise SystemExit(main())
