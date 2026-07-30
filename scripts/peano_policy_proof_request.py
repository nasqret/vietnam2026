#!/usr/bin/env python3
"""Create, receive, validate, and run immutable WMI theorem requests."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
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
from training.peano_policy.prompt import prompt_contract_sha256  # noqa: E402


REQUEST_VERSION = 2
LEGACY_REQUEST_VERSION = 1
SEARCH_MODE = "kernel-guided-search"
DEFAULT_MAX_STEPS = 32
DEFAULT_MAX_NEW_TOKENS = 96
DEFAULT_SEARCH_BEAM_WIDTH = 4
DEFAULT_SEARCH_CANDIDATES_PER_STATE = 4
DEFAULT_SEARCH_MAX_MODEL_CALLS = 128
DEFAULT_SEARCH_MAX_STATES = 2_048
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
LEGACY_REQUEST_FIELDS = (
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
REQUEST_FIELDS = (
    "created_at",
    "id",
    "max_new_tokens",
    "max_steps",
    "mode",
    "nonce",
    "sample",
    "search_beam_width",
    "search_candidates_per_state",
    "search_max_model_calls",
    "search_max_states",
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
    max_new_tokens: int,
    max_steps: int,
    seed: int,
    sample: bool,
    search_beam_width: int,
    search_candidates_per_state: int,
    search_max_model_calls: int,
    search_max_states: int,
    created_at: str | None = None,
    nonce: str | None = None,
) -> dict[str, object]:
    theorem_source = trained_cli._preflight_user_theorem(theorem)
    if type(max_new_tokens) is not int or not (
        1 <= max_new_tokens <= trained_cli.MAX_POLICY_NEW_TOKENS
    ):
        raise ValueError(
            "max_new_tokens must lie between 1 and "
            f"{trained_cli.MAX_POLICY_NEW_TOKENS}"
        )
    if type(max_steps) is not int or not (
        1 <= max_steps <= trained_cli.MAX_SEARCH_DEPTH
    ):
        raise ValueError(
            f"max_steps must lie between 1 and {trained_cli.MAX_SEARCH_DEPTH}"
        )
    search_bounds = (
        (
            "search_beam_width",
            search_beam_width,
            trained_cli.MAX_POLICY_SEARCH_BEAM,
        ),
        (
            "search_candidates_per_state",
            search_candidates_per_state,
            trained_cli.MAX_CANDIDATES_PER_MODEL_CALL,
        ),
        (
            "search_max_model_calls",
            search_max_model_calls,
            trained_cli.MAX_POLICY_MODEL_CALLS,
        ),
        (
            "search_max_states",
            search_max_states,
            trained_cli.MAX_POLICY_SEARCH_STATES,
        ),
    )
    for name, value, maximum in search_bounds:
        if type(value) is not int or not 1 <= value <= maximum:
            raise ValueError(f"{name} must lie between 1 and {maximum}")
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in [0, 2^63)")
    if type(sample) is not bool:
        raise TypeError("sample must be a Boolean")
    limits = trained_cli.SearchLimits(
        max_depth=max_steps,
        beam_width=search_beam_width,
        candidates_per_state=search_candidates_per_state,
        max_model_calls=search_max_model_calls,
        max_states=search_max_states,
    )
    trained_cli._validate_kernel_search_budget(
        limits,
        goal_count=1,
        max_new_tokens=max_new_tokens,
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
        "max_new_tokens": max_new_tokens,
        "max_steps": max_steps,
        "mode": SEARCH_MODE,
        "nonce": request_nonce,
        "sample": sample,
        "search_beam_width": search_beam_width,
        "search_candidates_per_state": search_candidates_per_state,
        "search_max_model_calls": search_max_model_calls,
        "search_max_states": search_max_states,
        "seed": seed,
        "theorem": theorem_source,
        "v": REQUEST_VERSION,
    }
    return {"id": _request_digest(body), **body}


def _build_legacy_request(
    *,
    theorem: str,
    k: int,
    max_steps: int,
    seed: int,
    sample: bool,
    created_at: str,
    nonce: str,
) -> dict[str, object]:
    """Rebuild a v1 request without changing its identity or rollout meaning."""

    theorem_source = trained_cli._preflight_user_theorem(theorem)
    if type(k) is not int or not 1 <= k <= 256:
        raise ValueError("k must lie between 1 and 256")
    if type(max_steps) is not int or not (
        1 <= max_steps <= trained_cli.MAX_BATCH_TACTICS
    ):
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
    if _TIMESTAMP_RE.fullmatch(created_at) is None:
        raise ValueError("request timestamp is not canonical UTC")
    if _NONCE_RE.fullmatch(nonce) is None:
        raise ValueError("request nonce must be 32 lowercase hexadecimal characters")
    body: dict[str, object] = {
        "created_at": created_at,
        "k": k,
        "max_steps": max_steps,
        "nonce": nonce,
        "sample": sample,
        "seed": seed,
        "theorem": theorem_source,
        "v": LEGACY_REQUEST_VERSION,
    }
    return {"id": _request_digest(body), **body}


def validate_request(value: object, *, expected_id: str | None = None) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError("proof request must be one object")
    version = value.get("v")
    expected_fields = (
        LEGACY_REQUEST_FIELDS
        if type(version) is int and version == LEGACY_REQUEST_VERSION
        else REQUEST_FIELDS
        if type(version) is int and version == REQUEST_VERSION
        else None
    )
    if expected_fields is None:
        raise ValueError("proof request has an unsupported version")
    if tuple(sorted(value)) != expected_fields:
        raise ValueError("proof request has an incompatible field set")
    request_id = _validate_request_id(value.get("id"))
    if expected_id is not None and request_id != _validate_request_id(expected_id):
        raise ValueError("proof request id does not match its requested path")
    if version == LEGACY_REQUEST_VERSION:
        rebuilt = _build_legacy_request(
            theorem=value.get("theorem"),  # type: ignore[arg-type]
            k=value.get("k"),  # type: ignore[arg-type]
            max_steps=value.get("max_steps"),  # type: ignore[arg-type]
            seed=value.get("seed"),  # type: ignore[arg-type]
            sample=value.get("sample"),  # type: ignore[arg-type]
            created_at=value.get("created_at"),  # type: ignore[arg-type]
            nonce=value.get("nonce"),  # type: ignore[arg-type]
        )
    else:
        if value.get("mode") != SEARCH_MODE:
            raise ValueError(f"proof request mode must be {SEARCH_MODE!r}")
        rebuilt = build_request(
            theorem=value.get("theorem"),  # type: ignore[arg-type]
            max_new_tokens=value.get("max_new_tokens"),  # type: ignore[arg-type]
            max_steps=value.get("max_steps"),  # type: ignore[arg-type]
            seed=value.get("seed"),  # type: ignore[arg-type]
            sample=value.get("sample"),  # type: ignore[arg-type]
            search_beam_width=value.get("search_beam_width"),  # type: ignore[arg-type]
            search_candidates_per_state=value.get(  # type: ignore[arg-type]
                "search_candidates_per_state"
            ),
            search_max_model_calls=value.get("search_max_model_calls"),  # type: ignore[arg-type]
            search_max_states=value.get("search_max_states"),  # type: ignore[arg-type]
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


def _load_attested_adapter_authority(
    adapter: Path,
    canonical_statement: str,
    *,
    require_model_v2: bool,
) -> tuple[dict[str, object], str, object, object]:
    """Recover the exact fixed proof authority from the adapter manifest."""

    manifest, manifest_sha256 = trained_cli._read_adapter_manifest_snapshot(adapter)
    environment = trained_cli.attested_training_environment(manifest)
    # ``REQUEST_VERSION == 2`` names the immutable kernel-search request
    # protocol, not the policy prompt version.  Such requests were introduced
    # with model-v2, but model-v3 deliberately keeps the same bounded search
    # and publication envelope while exposing its attested 247-theorem
    # authority.  Accept only those two exact repository-owned environments;
    # a custom capability set must never acquire their trusted label here.
    if require_model_v2:
        capabilities = getattr(environment, "capabilities", None)
        label = getattr(capabilities, "label", None)
        expected_environment = (
            trained_cli.model_v2_environment()
            if label == "model-v2"
            else trained_cli.model_v3_environment()
            if label == "model-v3"
            else None
        )
        if expected_environment is None or environment != expected_environment:
            raise ValueError(
                "version-2 proof requests require the exact model-v2 or "
                "model-v3 authority"
            )
    goal = trained_cli._user_goal(canonical_statement, environment)
    return manifest, manifest_sha256, environment, goal


def _expected_adapter_provenance(
    adapter: Path,
    manifest: dict[str, object],
    manifest_sha256: str,
) -> dict[str, object]:
    """Rebuild the complete provenance recorded by the trained evaluator."""

    provenance = trained_cli.adapter_provenance(adapter, manifest)
    if provenance.get("training_manifest_sha256") != manifest_sha256:
        raise RuntimeError("adapter provenance differs from its manifest snapshot")
    import torch

    evaluation_job = trained_cli.slurm_job_identity()
    provenance["evaluation"] = {
        "sources": trained_cli._evaluation_sources(),
        "runtime": trained_cli.runtime_identity(torch),
        "job": evaluation_job,
        "training_job_binding": trained_cli._require_training_job_binding(
            manifest,
            evaluation_job,
        ),
    }
    return json.loads(
        json.dumps(
            provenance,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _goal_environment_record(goal: object) -> dict[str, object]:
    capabilities = getattr(goal, "capabilities", None)
    allowed_commands = getattr(capabilities, "allowed_commands", None)
    allowed_theorems = getattr(capabilities, "allowed_theorems", None)
    return {
        "classical": getattr(goal, "classical", None),
        "surface": getattr(capabilities, "label", None),
        "environment_sha256": trained_cli.capability_sha256(capabilities),
        "capabilities": {
            "label": getattr(capabilities, "label", None),
            "allowed_commands": (
                None if allowed_commands is None else sorted(allowed_commands)
            ),
            "allowed_theorems": (
                None if allowed_theorems is None else sorted(allowed_theorems)
            ),
        },
    }


def _expected_evaluator_identity() -> dict[str, object]:
    return {
        "source_sha256": trained_cli.evaluator.EVALUATOR_SOURCE_SHA256,
        "semantic_sources": trained_cli.evaluator.EVALUATOR_SEMANTIC_SOURCES,
        "runtime": trained_cli.evaluator.EVALUATOR_RUNTIME,
    }


def _validate_v2_report_identity(
    report: dict[str, object],
    request: dict[str, object],
    adapter: Path,
    manifest: dict[str, object],
    manifest_sha256: str,
    environment: object,
    goal: object,
    expected_search_limits: dict[str, object],
) -> None:
    """Bind a v2 report to this evaluator, adapter authority, and decoder."""

    if (
        report.get("v") != trained_cli.evaluator.EVAL_VERSION
        or report.get("evaluator") != _expected_evaluator_identity()
        or report.get("judge") != "checked_final(original_target, exact_mode)"
    ):
        raise RuntimeError("evaluation report has a missing or forged evaluator identity")
    identity = report.get("policy_identity")
    if type(identity) is not dict:
        raise RuntimeError("evaluation report lacks a policy identity")
    base = identity.get("base_policy")
    if type(base) is not dict:
        raise RuntimeError("evaluation report lacks its base-policy identity")
    policy_name = report.get("policy")
    base_name = base.get("name")
    run = manifest.get("run")
    run_name = run.get("name") if type(run) is dict else None
    expected_base_name = (
        f"peano-policy:{run_name}:{manifest_sha256[:12]}"
        if type(run_name) is str and run_name
        else None
    )
    expected_policy_name = (
        f"{expected_base_name}:kernel-guided-search"
        if expected_base_name is not None
        else None
    )
    identity_limits = identity.get("limits")
    if (
        set(identity)
        != {
            "name",
            "kind",
            "base_policy",
            "limits",
            "seed",
            "seed_schedule",
            "decoder_batching",
        }
        or identity.get("kind") != "peano-kernel-guided-search-v1"
        or policy_name != expected_policy_name
        or identity.get("name") != policy_name
        or type(identity_limits) is not dict
        or set(identity_limits) != set(expected_search_limits)
        or any(type(identity_limits.get(key)) is not int for key in expected_search_limits)
        or identity_limits != expected_search_limits
        or type(identity.get("seed")) is not int
        or identity.get("seed") != request["seed"]
        or identity.get("seed_schedule")
        != "sha256-json-v1(seed,goal_name,goal_statement)"
        or identity.get("decoder_batching")
        != "one-model-generate-call-per-search-state"
    ):
        raise RuntimeError("evaluation report has a forged kernel-search identity")

    decoding = base.get("decoding")
    provenance = base.get("provenance")
    generation = manifest.get("generation")
    if type(decoding) is not dict or type(generation) is not dict:
        raise RuntimeError("evaluation report or adapter lacks decoding identity")
    temperature = generation.get("temperature")
    top_p = generation.get("top_p")
    if (
        type(temperature) not in {int, float}
        or not math.isfinite(temperature)
        or temperature <= 0
        or type(top_p) not in {int, float}
        or not math.isfinite(top_p)
        or not 0 < top_p <= 1
    ):
        raise RuntimeError("adapter generation identity is invalid")
    expected_decoding = {
        "max_new_tokens": request["max_new_tokens"],
        "do_sample": request["sample"],
        "temperature": float(temperature),
        "top_p": float(top_p),
    }
    expected_environment = _goal_environment_record(goal)
    expected_prompt_version = getattr(environment, "prompt_version", None)
    if (
        set(base)
        != {
            "name",
            "kind",
            "prompt_version",
            "prompt_contract_sha256",
            "environment",
            "decoding",
            "provenance",
        }
        or type(base_name) is not str
        or base_name != expected_base_name
        or base.get("kind") != "peano-policy-adapter-v1"
        or base.get("prompt_version") != expected_prompt_version
        or base.get("prompt_contract_sha256")
        != prompt_contract_sha256(expected_prompt_version)
        or base.get("environment") != expected_environment
        or type(decoding.get("max_new_tokens")) is not int
        or type(decoding.get("do_sample")) is not bool
        or type(decoding.get("temperature")) is not float
        or type(decoding.get("top_p")) is not float
        or decoding != expected_decoding
        or provenance
        != _expected_adapter_provenance(adapter, manifest, manifest_sha256)
    ):
        raise RuntimeError("evaluation report has a forged adapter or decode identity")


def _exact_counter(
    record: dict[str, object],
    key: str,
    *,
    maximum: int | None = None,
) -> int:
    value = record.get(key)
    if type(value) is not int or value < 0 or (
        maximum is not None and value > maximum
    ):
        suffix = "" if maximum is None else f" at most {maximum}"
        raise RuntimeError(f"search counter {key!r} must be a nonnegative integer{suffix}")
    return value


def _validate_v2_search_accounting(
    report: dict[str, object],
    request: dict[str, object],
    authority_goal: object,
    publication: dict[str, object],
    *,
    status: int,
    expected_limits: dict[str, object],
) -> dict[str, object]:
    """Validate the complete one-goal search shape and all counter equations."""

    expected_report_fields = {
        "v",
        "policy",
        "policy_identity",
        "evaluator",
        "judge",
        "goal_set_sha256",
        "seed",
        "k",
        "max_steps",
        "goal_count",
        "attempt_count",
        "proved_goals",
        "pass@k",
        "status_counts",
        "goals",
        "mode",
        "search",
        "proof_publication",
    }
    proved = status == 0
    if (
        set(report) != expected_report_fields
        or type(report.get("seed")) is not int
        or report.get("seed") != request["seed"]
        or type(report.get("k")) is not int
        or report.get("k") != 1
        or type(report.get("max_steps")) is not int
        or report.get("max_steps") != request["max_steps"]
        or type(report.get("goal_count")) is not int
        or report.get("goal_count") != 1
        or type(report.get("attempt_count")) is not int
        or report.get("attempt_count") != 1
        or type(report.get("proved_goals")) is not int
        or report.get("proved_goals") != int(proved)
        or type(report.get("pass@k")) is not float
        or report.get("pass@k") != float(proved)
        or report.get("mode") != "kernel-guided-search"
        or report.get("proof_publication") != publication
        or report.get("goal_set_sha256")
        != trained_cli.evaluator._goal_set_sha256((authority_goal,))
    ):
        raise RuntimeError("evaluation report has a malformed one-search envelope")

    search = report.get("search")
    if type(search) is not dict or set(search) != {
        "engine",
        "budget_scope",
        "limits",
        "aggregate_upper_bound",
        "actual",
        "goals",
    }:
        raise RuntimeError("evaluation report lacks exact search accounting")
    search_limits = search.get("limits")
    if (
        search.get("engine") != "training.peano_policy.search.search-v1"
        or search.get("budget_scope") != "per-goal"
        or type(search_limits) is not dict
        or set(search_limits) != set(expected_limits)
        or any(type(search_limits.get(key)) is not int for key in expected_limits)
        or search_limits != expected_limits
    ):
        raise RuntimeError("evaluation report search engine or limits differ")

    aggregate = search.get("aggregate_upper_bound")
    expected_aggregate = {
        "model_generate_calls": request["search_max_model_calls"],
        "candidate_sequences": (
            request["search_max_model_calls"]
            * request["search_candidates_per_state"]
        ),
        "generated_sequence_tokens": (
            request["search_max_model_calls"]
            * request["search_candidates_per_state"]
            * request["max_new_tokens"]
        ),
    }
    if (
        type(aggregate) is not dict
        or set(aggregate) != set(expected_aggregate)
        or any(type(aggregate.get(key)) is not int for key in expected_aggregate)
        or aggregate != expected_aggregate
    ):
        raise RuntimeError("evaluation report has forged aggregate search bounds")

    actual = search.get("actual")
    actual_fields = {
        "model_generate_calls",
        "states_expanded",
        "states_discovered",
        "candidates_executed",
        "candidate_sequences_requested",
        "candidate_sequences_returned",
        "candidate_lines_returned",
        "malformed_sequences_rejected",
        "frontier_peak_per_goal",
    }
    if type(actual) is not dict or set(actual) != actual_fields:
        raise RuntimeError("evaluation report lacks exact aggregate search counters")

    search_goals = search.get("goals")
    search_goal = (
        search_goals[0]
        if type(search_goals) is list and len(search_goals) == 1
        else None
    )
    if type(search_goal) is not dict or set(search_goal) != {
        "name",
        "environment_sha256",
        "result",
        "decoder",
    }:
        raise RuntimeError("evaluation report lacks one exact per-goal search record")
    capabilities = getattr(authority_goal, "capabilities", None)
    if (
        search_goal.get("name") != getattr(authority_goal, "name", None)
        or search_goal.get("environment_sha256")
        != trained_cli.capability_sha256(capabilities)
    ):
        raise RuntimeError("per-goal search authority differs from the request")

    result = search_goal.get("result")
    result_fields = {
        "status",
        "theorem",
        "commands",
        "certificate_nodes",
        "diagnostics",
        "model_calls",
        "states_expanded",
        "states_discovered",
        "candidates_executed",
        "frontier_peak",
        "depth_reached",
    }
    if type(result) is not dict or set(result) != result_fields:
        raise RuntimeError("per-goal search result has an incompatible field set")
    result_status = result.get("status")
    if result_status not in {"proof", "exhausted", "limit"}:
        raise RuntimeError("per-goal search result has an invalid status")
    expected_attempt_status = {
        "proof": "proof",
        "exhausted": "failing",
        "limit": "limit",
    }[result_status]
    if (result_status == "proof") is not proved:
        raise RuntimeError("search result status disagrees with process status")
    commands = result.get("commands")
    certificate_nodes = result.get("certificate_nodes")
    if (
        result.get("theorem") != getattr(authority_goal, "statement", None)
        or type(commands) is not list
        or not all(type(command) is str for command in commands)
        or (
            proved
            and (
                not commands
                or type(certificate_nodes) is not int
                or certificate_nodes < 1
            )
        )
        or (not proved and (commands != [] or certificate_nodes is not None))
    ):
        raise RuntimeError("search result proof payload disagrees with its status")

    model_calls = _exact_counter(
        result,
        "model_calls",
        maximum=int(request["search_max_model_calls"]),
    )
    states_expanded = _exact_counter(
        result,
        "states_expanded",
        maximum=int(request["search_max_states"]),
    )
    states_discovered = _exact_counter(
        result,
        "states_discovered",
        maximum=int(request["search_max_states"]),
    )
    candidates_executed = _exact_counter(
        result,
        "candidates_executed",
        maximum=(
            model_calls * int(request["search_candidates_per_state"])
        ),
    )
    frontier_peak = _exact_counter(
        result,
        "frontier_peak",
        maximum=int(request["search_beam_width"]),
    )
    depth_reached = _exact_counter(
        result,
        "depth_reached",
        maximum=int(request["max_steps"]),
    )
    if (
        model_calls != states_expanded
        or model_calls < 1
        or states_expanded > states_discovered
        or states_discovered < 1
        or frontier_peak < 1
        or (proved and depth_reached != len(commands))
    ):
        raise RuntimeError("per-goal search counters are internally inconsistent")

    diagnostics = result.get("diagnostics")
    if type(diagnostics) is not list:
        raise RuntimeError("search diagnostics must be a list")
    for diagnostic in diagnostics:
        if type(diagnostic) is not dict or set(diagnostic) != {
            "kind",
            "depth",
            "state_sha256",
            "command",
            "message",
        }:
            raise RuntimeError("search diagnostic has an incompatible field set")
        command = diagnostic.get("command")
        if (
            type(diagnostic.get("kind")) is not str
            or not diagnostic.get("kind")
            or type(diagnostic.get("depth")) is not int
            or not 0 <= diagnostic["depth"] <= request["max_steps"]
            or type(diagnostic.get("state_sha256")) is not str
            or _REQUEST_ID_RE.fullmatch(diagnostic["state_sha256"]) is None
            or (command is not None and type(command) is not str)
            or type(diagnostic.get("message")) is not str
            or not diagnostic.get("message")
        ):
            raise RuntimeError("search diagnostic is malformed")

    decoder = search_goal.get("decoder")
    decoder_fields = {
        "model_generate_calls",
        "candidate_sequences_requested",
        "candidate_sequences_returned",
        "candidate_lines_returned",
        "malformed_sequences_rejected",
        "one_batched_call_per_search_state",
    }
    if type(decoder) is not dict or set(decoder) != decoder_fields:
        raise RuntimeError("per-goal decoder accounting has an incompatible field set")
    decoder_calls = _exact_counter(
        decoder,
        "model_generate_calls",
        maximum=int(request["search_max_model_calls"]),
    )
    sequences_requested = _exact_counter(
        decoder,
        "candidate_sequences_requested",
        maximum=int(expected_aggregate["candidate_sequences"]),
    )
    sequences_returned = _exact_counter(
        decoder,
        "candidate_sequences_returned",
        maximum=sequences_requested,
    )
    lines_returned = _exact_counter(
        decoder,
        "candidate_lines_returned",
        maximum=sequences_returned,
    )
    malformed = _exact_counter(
        decoder,
        "malformed_sequences_rejected",
        maximum=sequences_returned,
    )
    if (
        decoder.get("one_batched_call_per_search_state") is not True
        or decoder_calls != model_calls
        or sequences_requested
        != model_calls * request["search_candidates_per_state"]
        or sequences_returned > sequences_requested
        or lines_returned + malformed != sequences_returned
        or candidates_executed > lines_returned
    ):
        raise RuntimeError("per-goal decoder counters are internally inconsistent")

    if proved:
        proof_depth = len(commands)
        # Search expands the parent of every command on the winning path.  Its
        # discovered-state counter contains the root and every *open* prefix,
        # but deliberately excludes the terminal checked proof state, so the
        # exact lower bound is ``proof_depth`` rather than ``proof_depth + 1``.
        # Every winning edge must also come from one executed, complete decoder
        # candidate and therefore from one returned and requested sequence.
        if (
            model_calls < proof_depth
            or states_discovered < proof_depth
            or candidates_executed < proof_depth
            or sequences_requested < proof_depth
            or sequences_returned < proof_depth
            or lines_returned < proof_depth
        ):
            raise RuntimeError(
                "proved search counters cannot account for the winning path"
            )

    expected_actual = {
        "model_generate_calls": model_calls,
        "states_expanded": states_expanded,
        "states_discovered": states_discovered,
        "candidates_executed": candidates_executed,
        "candidate_sequences_requested": sequences_requested,
        "candidate_sequences_returned": sequences_returned,
        "candidate_lines_returned": lines_returned,
        "malformed_sequences_rejected": malformed,
        "frontier_peak_per_goal": frontier_peak,
    }
    if (
        any(type(actual.get(key)) is not int for key in expected_actual)
        or actual != expected_actual
    ):
        raise RuntimeError("aggregate search counters differ from the per-goal record")

    goals = report.get("goals")
    goal_record = goals[0] if type(goals) is list and len(goals) == 1 else None
    goal_fields = {
        "name",
        "statement",
        "classical",
        "surface_profile",
        "environment_sha256",
        "allowed_theorems",
        "passed",
        "status_counts",
        "attempts",
    }
    if type(goal_record) is not dict or set(goal_record) != goal_fields:
        raise RuntimeError("evaluation report lacks one exact goal record")
    attempts = goal_record.get("attempts")
    attempt = attempts[0] if type(attempts) is list and len(attempts) == 1 else None
    attempt_fields = {
        "sample",
        "seed",
        "status",
        "steps",
        "commands",
        "proof_nodes",
        "error",
    }
    error = attempt.get("error") if type(attempt) is dict else None
    if (
        type(attempt) is not dict
        or set(attempt) != attempt_fields
        or type(attempt.get("sample")) is not int
        or attempt.get("sample") != 0
        or type(attempt.get("seed")) is not int
        or attempt.get("seed")
        != trained_cli._stable_search_seed(int(request["seed"]), authority_goal)
        or attempt.get("status") != expected_attempt_status
        or type(attempt.get("steps")) is not int
        or attempt.get("steps") != len(commands)
        or attempt.get("commands") != commands
        or (proved and type(attempt.get("proof_nodes")) is not int)
        or (not proved and attempt.get("proof_nodes") is not None)
        or attempt.get("proof_nodes") != certificate_nodes
        or (proved and error is not None)
        or (not proved and (type(error) is not str or not error))
    ):
        raise RuntimeError("policy attempt is inconsistent with the search result")
    expected_status_counts = {
        name: int(name == expected_attempt_status)
        for name in trained_cli.evaluator.ATTEMPT_STATUSES
    }
    if (
        type(goal_record.get("status_counts")) is not dict
        or any(
            type(goal_record["status_counts"].get(name)) is not int
            for name in expected_status_counts
        )
        or type(report.get("status_counts")) is not dict
        or any(
            type(report["status_counts"].get(name)) is not int
            for name in expected_status_counts
        )
        or goal_record.get("passed") is not proved
        or goal_record.get("status_counts") != expected_status_counts
        or report.get("status_counts") != expected_status_counts
        or publication.get("status") != ("proof" if proved else "no-proof")
    ):
        raise RuntimeError("report, attempt, and publication statuses disagree")
    return result


def _validate_checked_publication(
    *,
    request_id: str,
    theorem: str,
    canonical_statement: str,
    expected_k: int,
    goal_record: dict[str, object],
    authority_goal: object,
    publication: dict[str, object],
    proof: Path,
) -> dict[str, object]:
    """Independently replay and byte-bind one claimed proof publication."""

    if set(publication) != {
        "status",
        "sample",
        "proof_nodes",
        "commands",
        "script",
        "script_sha256",
        "replay",
    }:
        raise RuntimeError("proof publication has an incompatible field set")
    sample = publication.get("sample")
    proof_nodes = publication.get("proof_nodes")
    commands = publication.get("commands")
    script = publication.get("script")
    replay_record = publication.get("replay")
    if (
        type(sample) is not int
        or not 0 <= sample < expected_k
        or type(proof_nodes) is not int
        or proof_nodes < 1
        or type(commands) is not list
        or not commands
        or not all(type(command) is str for command in commands)
        or type(script) is not str
        or type(replay_record) is not dict
    ):
        raise RuntimeError("proof publication metadata is malformed")
    command_tuple = tuple(commands)
    expected_script = "\n".join(
        (f"pa prove {canonical_statement}", *command_tuple, "qed", "")
    )
    script_payload = expected_script.encode("utf-8")
    if (
        script != expected_script
        or publication.get("script_sha256") != _sha256_bytes(script_payload)
        or not proof.is_file()
        or proof.is_symlink()
        or proof.read_bytes() != script_payload
    ):
        raise RuntimeError("published proof script is not exactly report-bound")
    attempts = goal_record.get("attempts")
    if type(attempts) is not list or not any(
        type(attempt) is dict
        and attempt.get("status") == "proof"
        and attempt.get("sample") == sample
        and attempt.get("commands") == commands
        and attempt.get("proof_nodes") == proof_nodes
        for attempt in attempts
    ):
        raise RuntimeError("proof publication is not bound to a proved policy attempt")

    capabilities = getattr(authority_goal, "capabilities", None)
    replay = trained_cli.verify_proof(
        theorem,
        command_tuple,
        request_id=f"wmi-publish-{request_id[:16]}",
        classical=getattr(authority_goal, "classical", None),
        capabilities=capabilities,
    )
    expected_environment_sha256 = trained_cli.capability_sha256(capabilities)
    expected_replay = {
        "status": "proved",
        "kernel_checked": True,
        "proof_nodes": proof_nodes,
        "surface": getattr(capabilities, "label", None),
        "environment_sha256": expected_environment_sha256,
    }
    if (
        replay.status != "proved"
        or replay.kernel_checked is not True
        or replay.theorem != canonical_statement
        or replay.proof_nodes != proof_nodes
        or replay.tactics_applied != len(command_tuple)
        or replay.failed_tactics != 0
        or replay.surface != getattr(capabilities, "label", None)
        or replay.environment_sha256 != expected_environment_sha256
        or replay_record != expected_replay
    ):
        raise RuntimeError("proof publication failed independent original-goal replay")
    return {
        "path": proof.relative_to(REPOSITORY_ROOT).as_posix(),
        "sha256": _sha256_bytes(script_payload),
    }


def run_request(request_id: str, adapter: Path) -> dict[str, object]:
    request, request_path, request_sha256 = load_request(request_id)
    target, names = trained_cli.parse_formula_with_names(str(request["theorem"]))
    canonical_statement = trained_cli.pretty_formula(target, list(names))
    manifest: dict[str, object] | None = None
    manifest_sha256: str | None = None
    environment: object | None = None
    authority_goal: object | None = None
    if request["v"] == REQUEST_VERSION:
        (
            manifest,
            manifest_sha256,
            environment,
            authority_goal,
        ) = _load_attested_adapter_authority(
            adapter,
            canonical_statement,
            require_model_v2=True,
        )
        trained_cli._recheck_adapter_snapshot(
            adapter,
            manifest,
            manifest_sha256,
        )
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
        "--max-steps",
        str(request["max_steps"]),
        "--seed",
        str(request["seed"]),
        "--output",
        str(report),
        "--proof-output",
        str(proof),
    ]
    if request["v"] == LEGACY_REQUEST_VERSION:
        arguments.extend(("--k", str(request["k"])))
    else:
        arguments.extend(
            (
                "--max-new-tokens",
                str(request["max_new_tokens"]),
                "--mode",
                "search",
                "--search-beam-width",
                str(request["search_beam_width"]),
                "--search-candidates-per-state",
                str(request["search_candidates_per_state"]),
                "--search-max-model-calls",
                str(request["search_max_model_calls"]),
                "--search-max-states",
                str(request["search_max_states"]),
            )
        )
    if request["sample"] is True:
        arguments.append("--sample")
    status = trained_cli.main(arguments)
    if status not in {0, 1}:
        raise RuntimeError(f"trained prover returned an invalid status: {status}")
    report_record, report_payload = _read_json_file(report, maximum=MAX_REPORT_BYTES)
    publication = report_record.get("proof_publication")
    expected = "proof" if status == 0 else "no-proof"
    goals = report_record.get("goals")
    goal = goals[0] if type(goals) is list and len(goals) == 1 else None
    expected_k = request["k"] if request["v"] == LEGACY_REQUEST_VERSION else 1
    expected_search_limits = (
        None
        if request["v"] == LEGACY_REQUEST_VERSION
        else {
            "max_depth": request["max_steps"],
            "beam_width": request["search_beam_width"],
            "candidates_per_state": request["search_candidates_per_state"],
            "max_model_calls": request["search_max_model_calls"],
            "max_states": request["search_max_states"],
        }
    )
    if request["v"] == LEGACY_REQUEST_VERSION and status == 0:
        (
            manifest,
            manifest_sha256,
            environment,
            authority_goal,
        ) = _load_attested_adapter_authority(
            adapter,
            canonical_statement,
            require_model_v2=False,
        )
        trained_cli._recheck_adapter_snapshot(
            adapter,
            manifest,
            manifest_sha256,
        )
    if expected_search_limits is None:
        search_matches = "mode" not in report_record and "search" not in report_record
    else:
        if (
            manifest is None
            or manifest_sha256 is None
            or environment is None
            or authority_goal is None
        ):  # pragma: no cover - branch invariant
            raise RuntimeError("v2 report lost its attested adapter authority")
        _validate_v2_report_identity(
            report_record,
            request,
            adapter,
            manifest,
            manifest_sha256,
            environment,
            authority_goal,
            expected_search_limits,
        )
        if type(publication) is not dict:
            raise RuntimeError("v2 evaluation report lacks proof publication metadata")
        _validate_v2_search_accounting(
            report_record,
            request,
            authority_goal,
            publication,
            status=status,
            expected_limits=expected_search_limits,
        )
        search_matches = True
    authority_matches = True
    if authority_goal is not None and type(goal) is dict:
        authority_capabilities = getattr(authority_goal, "capabilities", None)
        authority_allowed_theorems = getattr(
            authority_goal, "allowed_theorems", None
        )
        authority_matches = (
            goal.get("name") == getattr(authority_goal, "name", None)
            and goal.get("surface_profile")
            == getattr(authority_goal, "surface_profile", None)
            and goal.get("environment_sha256")
            == trained_cli.capability_sha256(authority_capabilities)
            and goal.get("allowed_theorems")
            == (
                None
                if authority_allowed_theorems is None
                else list(authority_allowed_theorems)
            )
        )
    if (
        type(publication) is not dict
        or publication.get("status") != expected
        or report_record.get("seed") != request["seed"]
        or report_record.get("k") != expected_k
        or report_record.get("max_steps") != request["max_steps"]
        or report_record.get("goal_count") != 1
        or not search_matches
        or not authority_matches
        or type(goal) is not dict
        or goal.get("statement") != canonical_statement
        or goal.get("classical") is not False
        or goal.get("surface_profile")
        not in {"model-v1", "model-v2", "model-v3"}
        or goal.get("passed") is not (status == 0)
    ):
        raise RuntimeError("proof request, status, and evaluation report disagree")
    proof_record: dict[str, object] | None = None
    if status == 0:
        if authority_goal is None:  # pragma: no cover - branch invariant
            raise RuntimeError("proved request lost its attested adapter authority")
        proof_record = _validate_checked_publication(
            request_id=request_id,
            theorem=str(request["theorem"]),
            canonical_statement=canonical_statement,
            expected_k=expected_k,
            goal_record=goal,
            authority_goal=authority_goal,
            publication=publication,
            proof=proof,
        )
    elif publication != {"status": "no-proof"}:
        raise RuntimeError("unproved request has forged publication metadata")
    elif os.path.lexists(proof):
        raise RuntimeError("unproved request unexpectedly published a .pa file")
    if manifest is not None and manifest_sha256 is not None:
        trained_cli._recheck_adapter_snapshot(
            adapter,
            manifest,
            manifest_sha256,
        )
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
    create.add_argument(
        "--max-new-tokens",
        type=int,
        default=DEFAULT_MAX_NEW_TOKENS,
    )
    create.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    create.add_argument(
        "--search-beam-width",
        type=int,
        default=DEFAULT_SEARCH_BEAM_WIDTH,
    )
    create.add_argument(
        "--search-candidates-per-state",
        type=int,
        default=DEFAULT_SEARCH_CANDIDATES_PER_STATE,
    )
    create.add_argument(
        "--search-max-model-calls",
        type=int,
        default=DEFAULT_SEARCH_MAX_MODEL_CALLS,
    )
    create.add_argument(
        "--search-max-states",
        type=int,
        default=DEFAULT_SEARCH_MAX_STATES,
    )
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
            max_new_tokens=args.max_new_tokens,
            max_steps=args.max_steps,
            seed=args.seed,
            sample=args.sample,
            search_beam_width=args.search_beam_width,
            search_candidates_per_state=args.search_candidates_per_state,
            search_max_model_calls=args.search_max_model_calls,
            search_max_states=args.search_max_states,
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
