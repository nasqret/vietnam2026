"""Independent pre-training replay and contamination gate for policy data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Mapping

from .contract import (
    canonical_held_out_formulas,
    environment_record,
    held_out_contract_record,
    held_out_contract_sha256,
    model_v1_environment,
    model_v2_environment,
    model_v3_environment,
    model_v3_prefix_environment,
    prompt_environment,
)
from .data import (
    MAX_DATASET_LINE_BYTES,
    ROW_FIELDS,
    SPLITS,
    dataset_manifest_path,
    example_from_record,
    load_dataset_manifest,
)
from .manifest import sha256_file, sha256_json, write_manifest
from .library_identity import MOD5_SOURCE_REPORT, PUBLIC_LIBRARY_CATALOG
from .prompt import (
    PEANO_PROMPT_V1,
    PEANO_PROMPT_V2,
    PEANO_PROMPT_V3,
    CapabilityIdentity,
    PromptEnvironment,
    prompt_contract_sha256,
    prompt_manifest_record,
    prompt_version_from_manifest,
)
from peano_lab.kernel.formulas import (  # noqa: E402
    Formula,
    ParseError,
    parse_formula_with_names,
)


ATTESTATION_VERSION = 2
V3_CATALOG_TRAJECTORY = "catalog-predecessor-prefix-v1"
V3_SYNTHETIC_LANE = "synthetic-root-balanced"
V3_SPLIT_LANES = (V3_CATALOG_TRAJECTORY, V3_SYNTHETIC_LANE)
LEGACY_SPLIT_METHOD = "sha256-ranked-genealogy-formula-prompt-components-v2"
V3_SPLIT_METHOD = "catalog-train-sha256-ranked-synthetic-components-v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
BUILDER = REPOSITORY_ROOT / "scripts" / "build_peano_policy_dataset.py"
EXPORTER = REPOSITORY_ROOT / "scripts" / "export_traces.py"


class DatasetAttestationError(ValueError):
    """A dataset is not reproducibly authorized for the fixed policy run."""


def _rendered_goal_target(
    rendered: object,
    *,
    location: str,
) -> Formula | None:
    """Independently parse the rigid target after a trace goal's turnstile."""

    if type(rendered) is not str:
        raise DatasetAttestationError(f"{location}: goal must be canonical text")
    _, turnstile, target_text = rendered.rpartition("⊢")
    target_text = target_text.strip()
    if not turnstile or not target_text:
        raise DatasetAttestationError(
            f"{location}: goal has no canonical turnstile/target"
        )
    if "?" in target_text:
        return None
    try:
        target, _ = parse_formula_with_names(target_text)
    except (ParseError, TypeError, ValueError, RecursionError) as exc:
        raise DatasetAttestationError(
            f"{location}: goal target is not a PA formula: {exc}"
        ) from exc
    return target


def _validate_no_held_out_goal_targets(
    goals: object,
    *,
    forbidden_targets: frozenset[Formula],
    location: str,
) -> None:
    """Reject exact held-out propositions as supervised goal targets."""

    if type(goals) is not list:
        raise DatasetAttestationError(f"{location}: state must be a goal array")
    for goal_index, rendered in enumerate(goals, 1):
        target = _rendered_goal_target(
            rendered,
            location=f"{location} goal {goal_index}",
        )
        if target in forbidden_targets:
            raise DatasetAttestationError(
                f"{location}: model-v3 held-out formula appears as goal target "
                f"{goal_index}"
            )


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _decode(text: str, location: str) -> dict[str, object]:
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise DatasetAttestationError(f"{location}: invalid JSON: {exc}") from exc
    if type(value) is not dict:
        raise DatasetAttestationError(f"{location}: expected one JSON object")
    return value


def _compiler_paths() -> tuple[Path, ...]:
    return (
        BUILDER,
        EXPORTER,
        REPOSITORY_ROOT / "scripts" / "generate_peano_synthetic_corpus.py",
        REPOSITORY_ROOT / "scripts" / "generate_peano_v3_balanced_corpus.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "contract.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "prompt.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "library_identity.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "library_identity_v3.py",
        MOD5_SOURCE_REPORT,
        PUBLIC_LIBRARY_CATALOG,
        *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
    )


def _attestor_manifest() -> dict[str, object]:
    sources = {
        path.relative_to(REPOSITORY_ROOT).as_posix(): {"sha256": sha256_file(path)}
        for path in sorted(Path(__file__).resolve().parent.glob("*.py"))
    }
    return {
        "runtime": {
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
        },
        "sources": sources,
        "sources_sha256": sha256_json(sources),
    }


def _verify_compiler(manifest: Mapping[str, object]) -> dict[str, object]:
    source = manifest.get("source")
    compiler = source.get("compiler") if type(source) is dict else None
    if type(compiler) is not dict or set(compiler) != {"runtime", "sources"}:
        raise DatasetAttestationError("dataset lacks canonical compiler provenance")
    recorded = compiler.get("sources")
    if type(recorded) is not dict:
        raise DatasetAttestationError("dataset compiler sources are malformed")
    expected = {
        path.relative_to(REPOSITORY_ROOT).as_posix(): sha256_file(path)
        for path in _compiler_paths()
    }
    if set(recorded) != set(expected):
        raise DatasetAttestationError(
            "dataset compiler source inventory differs from the current prover"
        )
    for relative, digest in expected.items():
        entry = recorded[relative]
        if type(entry) is not dict or entry != {"sha256": digest}:
            raise DatasetAttestationError(
                f"dataset compiler source hash mismatch: {relative}"
            )
    runtime = compiler.get("runtime")
    if (
        type(runtime) is not dict
        or set(runtime) != {"implementation", "python"}
        or not all(type(value) is str and value for value in runtime.values())
    ):
        raise DatasetAttestationError("dataset compiler runtime is malformed")
    return {
        "runtime": dict(runtime),
        "sources_sha256": sha256_json(recorded),
        "source_count": len(recorded),
    }


def _resolve_artifact_path(value: object, label: str) -> Path:
    if type(value) is not str or not value:
        raise DatasetAttestationError(f"{label} path must be non-empty text")
    path = Path(value)
    path = path if path.is_absolute() else REPOSITORY_ROOT / path
    if path.is_symlink():
        raise DatasetAttestationError(f"{label} artifact must not be a symlink")
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise DatasetAttestationError(f"{label} artifact is unavailable: {exc}") from exc
    if not resolved.is_file():
        raise DatasetAttestationError(f"{label} artifact is not a regular file")
    return resolved


def _verify_source_artifacts(
    manifest: Mapping[str, object],
) -> tuple[tuple[Path, ...], Path, dict[str, object]]:
    source = manifest.get("source")
    if type(source) is not dict:
        raise DatasetAttestationError("dataset has no source provenance")
    trace_records = source.get("traces")
    metadata_record = source.get("metadata")
    if type(trace_records) is not list or not trace_records:
        raise DatasetAttestationError("dataset has no raw trace artifacts")
    if type(metadata_record) is not dict:
        raise DatasetAttestationError("dataset has no metadata artifact")

    traces: list[Path] = []
    trace_hashes: list[str] = []
    for index, record in enumerate(trace_records, 1):
        if type(record) is not dict or set(record) != {"path", "sha256"}:
            raise DatasetAttestationError(f"raw trace record {index} is malformed")
        path = _resolve_artifact_path(record["path"], f"raw trace {index}")
        digest = sha256_file(path)
        if record["sha256"] != digest:
            raise DatasetAttestationError(f"raw trace {index} hash mismatch")
        traces.append(path)
        trace_hashes.append(digest)

    if not {"path", "sha256", "records"}.issubset(metadata_record):
        raise DatasetAttestationError("metadata artifact record is malformed")
    metadata = _resolve_artifact_path(metadata_record["path"], "session metadata")
    metadata_hash = sha256_file(metadata)
    if metadata_record["sha256"] != metadata_hash:
        raise DatasetAttestationError("session metadata hash mismatch")
    return tuple(traces), metadata, {
        "traces": trace_hashes,
        "metadata": metadata_hash,
    }


def _expected_environment(prompt_version: int) -> PromptEnvironment:
    if prompt_version == PEANO_PROMPT_V1:
        return model_v1_environment()
    if prompt_version == PEANO_PROMPT_V2:
        return model_v2_environment()
    if prompt_version == PEANO_PROMPT_V3:
        return model_v3_environment()
    raise DatasetAttestationError("dataset uses an unsupported prompt version")


def _verify_environments(
    manifest: Mapping[str, object],
) -> tuple[
    dict[tuple[str, str, bool], dict[str, object]],
    PromptEnvironment,
    tuple[dict[str, object], ...],
]:
    environments = manifest.get("environments")
    try:
        prompt_version = prompt_version_from_manifest(manifest.get("prompt"))
    except ValueError as exc:
        raise DatasetAttestationError(str(exc)) from None
    inference_environment = _expected_environment(prompt_version)
    if type(environments) is not list or not environments:
        raise DatasetAttestationError(
            "training data must contain policy environment records"
        )
    if prompt_version in {PEANO_PROMPT_V1, PEANO_PROMPT_V2}:
        expected = environment_record(inference_environment)
        if len(environments) != 1:
            raise DatasetAttestationError(
                "model-v1/v2 data must contain exactly one fixed environment"
            )
        record = environments[0]
        if type(record) is not dict or type(record.get("sessions")) is not int:
            raise DatasetAttestationError("dataset environment record is malformed")
        if set(record) != {*expected, "sessions"}:
            raise DatasetAttestationError(
                "dataset environment fields are not canonical"
            )
        visible = {key: record.get(key) for key in expected}
        if visible != expected or record["sessions"] < 1:
            raise DatasetAttestationError(
                f"dataset environment differs from model-v{prompt_version} authority"
            )
        key = (
            str(expected["surface"]),
            str(expected["environment_sha256"]),
            bool(expected["classical"]),
        )
        return {key: expected}, inference_environment, (dict(record),)

    verified: dict[tuple[str, str, bool], dict[str, object]] = {}
    prefixes: set[int] = set()
    canonical_records: list[dict[str, object]] = []
    for position, record in enumerate(environments, 1):
        if type(record) is not dict or type(record.get("sessions")) is not int:
            raise DatasetAttestationError(
                f"model-v3 environment {position} is malformed"
            )
        capability_record = record.get("capabilities")
        if type(capability_record) is not dict:
            raise DatasetAttestationError("model-v3 capabilities are malformed")
        canonical_capabilities = {
            "label": capability_record.get("label"),
            "allowed_commands": capability_record.get("allowed_commands"),
            "allowed_theorems": capability_record.get("allowed_theorems"),
        }
        try:
            capabilities = CapabilityIdentity.from_record(canonical_capabilities)
            resolved = prompt_environment(False, capabilities)
        except (TypeError, ValueError) as exc:
            raise DatasetAttestationError(
                f"model-v3 environment {position} is unsupported: {exc}"
            ) from None
        expected = environment_record(resolved)
        if (
            resolved.prompt_version != PEANO_PROMPT_V3
            or set(record) != {*expected, "sessions"}
            or any(record.get(key) != value for key, value in expected.items())
            or record["sessions"] < 1
        ):
            raise DatasetAttestationError(
                f"model-v3 environment {position} is not canonical"
            )
        prefix = resolved.library_prefix_length
        assert type(prefix) is int
        library_size = inference_environment.library_full_length
        assert type(library_size) is int
        if prefix < library_size and record["sessions"] != 1:
            raise DatasetAttestationError(
                f"model-v3 predecessor prefix {prefix} must contain exactly "
                "one catalog session"
            )
        if prefix in prefixes:
            raise DatasetAttestationError("duplicate model-v3 library prefix")
        prefixes.add(prefix)
        key = (
            str(expected["surface"]),
            str(expected["environment_sha256"]),
            bool(expected["classical"]),
        )
        if key in verified:
            raise DatasetAttestationError("duplicate model-v3 environment identity")
        verified[key] = expected
        canonical_records.append(dict(record))
    required_prefixes = set(range((inference_environment.library_full_length or 0) + 1))
    if prefixes != required_prefixes:
        missing = sorted(required_prefixes - prefixes)
        extra = sorted(prefixes - required_prefixes)
        raise DatasetAttestationError(
            "model-v3 authority schedule is incomplete"
            + (f"; missing={missing}" if missing else "")
            + (f"; extra={extra}" if extra else "")
        )
    return verified, inference_environment, tuple(canonical_records)


def _record_v3_curriculum_evidence(
    record: Mapping[str, object],
    evidence: dict[str, tuple[int, str, str]],
    *,
    library_size: int,
    location: str,
    split: str = "train",
) -> str | None:
    """Independently bind a dataset row to one model-v3 curriculum lane."""

    if record.get("surface") != "model-v3":
        return None
    metadata = record.get("metadata")
    if type(metadata) is not dict:
        raise DatasetAttestationError(f"{location}: model-v3 metadata is malformed")
    session = record.get("session")
    prefix = metadata.get("library_prefix_length")
    if (
        type(session) is not str
        or not session
        or type(prefix) is not int
        or isinstance(prefix, bool)
        or not 0 <= prefix <= library_size
    ):
        raise DatasetAttestationError(
            f"{location}: model-v3 curriculum prefix/session is malformed"
        )
    if prefix < library_size:
        if (
            metadata.get("trajectory") != V3_CATALOG_TRAJECTORY
            or metadata.get("library_target_index") != prefix
            or metadata.get("library_target_name") != record.get("theorem")
            or metadata.get("statement") != record.get("formula")
            or "lane" in metadata
        ):
            raise DatasetAttestationError(
                f"{location}: predecessor prefix {prefix} lacks its exact "
                "catalog trajectory evidence"
            )
        lane = V3_CATALOG_TRAJECTORY
        if split != "train":
            raise DatasetAttestationError(
                f"{location}: catalog trajectory appears outside the training split"
            )
    else:
        statement = record.get("formula")
        tactics = metadata.get("tactics")
        if (
            metadata.get("lane") != V3_SYNTHETIC_LANE
            or "trajectory" in metadata
            or metadata.get("statement") != statement
            or type(statement) is not str
            or metadata.get("statement_sha256")
            != hashlib.sha256(statement.encode("utf-8")).hexdigest()
            or type(tactics) is not list
            or not tactics
            or not all(type(tactic) is str and tactic for tactic in tactics)
            or metadata.get("script_sha256")
            != hashlib.sha256(
                json.dumps(
                    tactics,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            or metadata.get("tactic_rows") != len(tactics)
        ):
            raise DatasetAttestationError(
                f"{location}: full prefix lacks approved synthetic lane evidence"
            )
        lane = V3_SYNTHETIC_LANE
    metadata_sha256 = sha256_json(metadata)
    claimed = (prefix, lane, metadata_sha256)
    previous = evidence.setdefault(session, claimed)
    if previous != claimed:
        raise DatasetAttestationError(
            f"{location}: session {session!r} changes curriculum evidence"
        )
    return lane


def _verify_v3_curriculum_schedule(
    evidence: Mapping[str, tuple[int, str, str]],
    training_environments: tuple[dict[str, object], ...],
    inference_environment: PromptEnvironment,
) -> dict[str, object]:
    """Derive the public authority schedule only from checked row evidence."""

    library_size = inference_environment.library_full_length
    if type(library_size) is not int or library_size < 1:
        raise DatasetAttestationError("model-v3 inference library size is malformed")
    sessions_by_prefix: dict[int, set[str]] = {}
    for session, (prefix, lane, _) in evidence.items():
        expected_lane = (
            V3_CATALOG_TRAJECTORY
            if prefix < library_size
            else V3_SYNTHETIC_LANE
        )
        if lane != expected_lane:
            raise DatasetAttestationError(
                f"model-v3 prefix {prefix} uses the wrong curriculum lane"
            )
        sessions_by_prefix.setdefault(prefix, set()).add(session)
    required_prefixes = set(range(library_size + 1))
    if set(sessions_by_prefix) != required_prefixes:
        missing = sorted(required_prefixes - set(sessions_by_prefix))
        extra = sorted(set(sessions_by_prefix) - required_prefixes)
        raise DatasetAttestationError(
            "model-v3 row evidence does not cover the exact authority schedule"
            + (f"; missing={missing}" if missing else "")
            + (f"; extra={extra}" if extra else "")
        )
    for prefix in range(library_size):
        if len(sessions_by_prefix[prefix]) != 1:
            raise DatasetAttestationError(
                f"model-v3 predecessor prefix {prefix} must have exactly one "
                "catalog session"
            )
    if not sessions_by_prefix[library_size]:
        raise DatasetAttestationError(
            "model-v3 full prefix must contain synthetic sessions"
        )

    environment_counts: dict[int, int] = {}
    for record in training_environments:
        prefix = record.get("library_prefix_length")
        sessions = record.get("sessions")
        if type(prefix) is not int or type(sessions) is not int:
            raise DatasetAttestationError(
                "model-v3 training environment counts are malformed"
            )
        environment_counts[prefix] = sessions
    observed_counts = {
        prefix: len(sessions) for prefix, sessions in sessions_by_prefix.items()
    }
    if environment_counts != observed_counts:
        raise DatasetAttestationError(
            "model-v3 environment session counts differ from row evidence"
        )
    return {
        "method": "catalog-predecessor-prefix-v1+full-synthetic-v1",
        "full_library_sha256": (
            inference_environment.library_full_identity_sha256
        ),
        "library_size": library_size,
        "training_prefixes": sorted(sessions_by_prefix),
        "inference_prefix": library_size,
    }


def _verify_v3_lane_populations(
    claimed: object,
    lane_sessions: Mapping[str, set[str]],
    lane_rows: Mapping[str, int],
    *,
    location: str,
) -> dict[str, dict[str, int]]:
    """Recompute one split's exact catalog/synthetic session and row counts."""

    actual = {
        lane: {
            "sessions": len(lane_sessions[lane]),
            "rows": lane_rows[lane],
        }
        for lane in V3_SPLIT_LANES
    }
    if claimed != actual:
        raise DatasetAttestationError(
            f"{location}: split lane populations are forged or stale"
        )
    return actual


def _stream_split(
    path: Path,
    split: str,
    split_record: Mapping[str, object],
    *,
    expected_environments: Mapping[
        tuple[str, str, bool], Mapping[str, object]
    ],
    forbidden_formulas: frozenset[str],
    forbidden_names: frozenset[str],
    forbidden_goal_targets: frozenset[Formula],
    v3_curriculum_evidence: dict[str, tuple[int, str, str]] | None,
    v3_library_size: int | None,
) -> tuple[
    int,
    str,
    frozenset[str],
    frozenset[str],
    dict[str, dict[str, int]] | None,
]:
    expected_split_fields = {"groups", "sessions", "rows", "sha256"}
    if v3_curriculum_evidence is not None:
        expected_split_fields.add("lane_populations")
    if set(split_record) != expected_split_fields:
        raise DatasetAttestationError(
            f"{path}: split manifest fields are not canonical"
        )
    digest = hashlib.sha256()
    rows = 0
    formulas: set[str] = set()
    prompts: set[str] = set()
    sessions: set[str] = set()
    lane_sessions = {lane: set() for lane in V3_SPLIT_LANES}
    lane_rows = {lane: 0 for lane in V3_SPLIT_LANES}
    try:
        stream = path.open("rb")
    except OSError as exc:
        raise DatasetAttestationError(
            f"cannot open dataset split {path}: {exc}"
        ) from exc
    with stream:
        for line_number, raw in enumerate(stream, 1):
            digest.update(raw)
            if len(raw) > MAX_DATASET_LINE_BYTES:
                raise DatasetAttestationError(
                    f"{path}:{line_number}: row exceeds the byte limit"
                )
            if raw == b"\n" or not raw.endswith(b"\n"):
                raise DatasetAttestationError(
                    f"{path}:{line_number}: split is not complete strict JSONL"
                )
            try:
                text = raw[:-1].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise DatasetAttestationError(
                    f"{path}:{line_number}: split is not valid UTF-8"
                ) from exc
            record = _decode(text, f"{path}:{line_number}")
            if tuple(record) != ROW_FIELDS or record.get("split") != split:
                raise DatasetAttestationError(
                    f"{path}:{line_number}: row is not canonical {split} data"
                )
            # This revalidates prompt/completion/capability redundancy.
            example_from_record(record, line_number)
            if v3_curriculum_evidence is not None:
                if type(v3_library_size) is not int:
                    raise DatasetAttestationError(
                        "model-v3 curriculum evidence has no library size"
                    )
                lane = _record_v3_curriculum_evidence(
                    record,
                    v3_curriculum_evidence,
                    library_size=v3_library_size,
                    location=f"{path}:{line_number}",
                    split=split,
                )
                if lane is None:
                    raise DatasetAttestationError(
                        f"{path}:{line_number}: model-v3 split contains another surface"
                    )
                lane_sessions[lane].add(str(record["session"]))
                lane_rows[lane] += 1
            if forbidden_goal_targets:
                _validate_no_held_out_goal_targets(
                    record["state"],
                    forbidden_targets=forbidden_goal_targets,
                    location=f"{path}:{line_number}",
                )
            key = (
                str(record["surface"]),
                str(record["environment_sha256"]),
                bool(record["classical"]),
            )
            expected_environment = expected_environments.get(key)
            if expected_environment is None:
                raise DatasetAttestationError(
                    f"{path}:{line_number}: row uses an unattested environment"
                )
            environment: dict[str, object] = {
                "classical": record["classical"],
                "surface": record["surface"],
                "environment_sha256": record["environment_sha256"],
                "capabilities": record["capabilities"],
            }
            metadata = record["metadata"]
            for field in (
                "library_identity_sha256",
                "library_full_identity_sha256",
                "library_prefix_length",
                "library_size",
            ):
                if field in expected_environment:
                    environment[field] = metadata.get(field)
            if environment != expected_environment:
                raise DatasetAttestationError(
                    f"{path}:{line_number}: row uses another policy environment"
                )
            formula = record["formula"]
            theorem = record["theorem"]
            if formula in forbidden_formulas or theorem in forbidden_names:
                raise DatasetAttestationError(
                    f"{path}:{line_number}: held-out target contamination"
                )
            formulas.add(str(formula))
            prompts.add(str(record["prompt"]))
            sessions.add(str(record["session"]))
            rows += 1
    actual_hash = digest.hexdigest()
    if (
        split_record.get("sessions") != len(sessions)
        or split_record.get("rows") != rows
        or split_record.get("sha256") != actual_hash
    ):
        raise DatasetAttestationError(f"{path}: split counters/hash mismatch")
    lane_populations: dict[str, dict[str, int]] | None = None
    if v3_curriculum_evidence is not None:
        lane_populations = _verify_v3_lane_populations(
            split_record.get("lane_populations"),
            lane_sessions,
            lane_rows,
            location=str(path),
        )
    return (
        rows,
        actual_hash,
        frozenset(formulas),
        frozenset(prompts),
        lane_populations,
    )


def _replay_builder(
    traces: tuple[Path, ...],
    metadata: Path,
    manifest: Mapping[str, object],
    split_paths: Mapping[str, Path],
) -> None:
    split = manifest.get("split")
    try:
        prompt_version = prompt_version_from_manifest(manifest.get("prompt"))
    except ValueError as exc:
        raise DatasetAttestationError(str(exc)) from None
    expected_method = (
        V3_SPLIT_METHOD
        if prompt_version == PEANO_PROMPT_V3
        else LEGACY_SPLIT_METHOD
    )
    if type(split) is not dict or split.get("method") != expected_method:
        raise DatasetAttestationError("dataset uses an unsupported split method")
    seed = split.get("seed")
    val_fraction = split.get("val_fraction")
    test_fraction = split.get("test_fraction")
    if (
        type(seed) is not str
        or not seed
        or type(val_fraction) not in {int, float}
        or type(test_fraction) not in {int, float}
    ):
        raise DatasetAttestationError("dataset split configuration is malformed")
    with tempfile.TemporaryDirectory(prefix="peano-policy-attest-") as raw_temp:
        output = Path(raw_temp) / "rebuilt"
        command = [
            sys.executable,
            str(BUILDER),
            *(str(path) for path in traces),
            "--metadata",
            str(metadata),
            "--output-dir",
            str(output),
            "--seed",
            seed,
            "--val-fraction",
            repr(float(val_fraction)),
            "--test-fraction",
            repr(float(test_fraction)),
        ]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(PEANO_PYTHON) + (
            os.pathsep + environment["PYTHONPATH"]
            if environment.get("PYTHONPATH")
            else ""
        )
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            # The WMI model-v2 preparation established that a 100,000-row
            # replay can legitimately take longer than one hour after the
            # source corpus and first build have already succeeded.  This is a
            # watchdog, not a performance acceptance criterion: retain a hard
            # bound while allowing the independent model-v3 rebuild to finish.
            timeout=14_400,
        )
        if completed.returncode != 0:
            error = " ".join((completed.stderr or completed.stdout).split())
            raise DatasetAttestationError(
                f"independent dataset replay failed: {error[:1000]}"
            )
        for split_name, original in split_paths.items():
            rebuilt = output / f"{split_name}.jsonl"
            if (
                not rebuilt.is_file()
                or rebuilt.stat().st_size != original.stat().st_size
                or sha256_file(rebuilt) != sha256_file(original)
            ):
                raise DatasetAttestationError(
                    f"independent replay changed the {split_name} policy split"
                )


def attest_dataset(train_path: Path, eval_path: Path) -> dict[str, object]:
    """Replay source sessions and authorize one exact uncontaminated dataset."""

    train_path = train_path.resolve()
    eval_path = eval_path.resolve()
    if train_path.name != "train.jsonl" or eval_path.name != "val.jsonl":
        raise DatasetAttestationError(
            "training requires train.jsonl and val.jsonl from one builder directory"
        )
    if train_path.parent != eval_path.parent:
        raise DatasetAttestationError("train and validation must share one manifest")
    manifest_path = dataset_manifest_path(train_path)
    manifest = load_dataset_manifest(manifest_path)
    compiler = _verify_compiler(manifest)
    traces, metadata, source_hashes = _verify_source_artifacts(manifest)
    expected_environments, inference_environment, training_environments = (
        _verify_environments(manifest)
    )
    prompt_version = inference_environment.prompt_version
    split_table = manifest.get("splits")
    if type(split_table) is not dict or tuple(split_table) != SPLITS:
        raise DatasetAttestationError("dataset split table is not canonical")

    forbidden_formulas = frozenset(canonical_held_out_formulas(prompt_version))
    forbidden_goal_targets = (
        frozenset(
            parse_formula_with_names(source)[0]
            for source in forbidden_formulas
        )
        if prompt_version == PEANO_PROMPT_V3
        else frozenset()
    )
    held_out = held_out_contract_record(prompt_version)
    forbidden_names = frozenset(
        str(record["name"]) for record in held_out["goals"]  # type: ignore[index]
    )
    split_paths = {
        split: train_path.parent / f"{split}.jsonl" for split in SPLITS
    }
    split_results: dict[str, dict[str, object]] = {}
    formula_sets: dict[str, frozenset[str]] = {}
    prompt_sets: dict[str, frozenset[str]] = {}
    dataset_digest = hashlib.sha256()
    v3_curriculum_evidence: dict[str, tuple[int, str, str]] | None = (
        {} if prompt_version == PEANO_PROMPT_V3 else None
    )
    v3_library_size = (
        inference_environment.library_full_length
        if prompt_version == PEANO_PROMPT_V3
        else None
    )
    for split_name in SPLITS:
        split_record = split_table[split_name]
        if type(split_record) is not dict:
            raise DatasetAttestationError(f"{split_name} split record is malformed")
        rows, digest, formulas, prompts, lane_populations = _stream_split(
            split_paths[split_name],
            split_name,
            split_record,
            expected_environments=expected_environments,
            forbidden_formulas=forbidden_formulas,
            forbidden_names=forbidden_names,
            forbidden_goal_targets=forbidden_goal_targets,
            v3_curriculum_evidence=v3_curriculum_evidence,
            v3_library_size=v3_library_size,
        )
        dataset_digest.update(split_name.encode("ascii") + b"\0")
        with split_paths[split_name].open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                dataset_digest.update(chunk)
        split_result: dict[str, object] = {"rows": rows, "sha256": digest}
        if lane_populations is not None:
            split_result["lane_populations"] = lane_populations
        split_results[split_name] = split_result
        formula_sets[split_name] = formulas
        prompt_sets[split_name] = prompts
    for index, left in enumerate(SPLITS):
        for right in SPLITS[index + 1 :]:
            if formula_sets[left] & formula_sets[right]:
                raise DatasetAttestationError(
                    f"canonical formulas overlap between {left} and {right}"
                )
            if prompt_sets[left] & prompt_sets[right]:
                raise DatasetAttestationError(
                    f"policy prompts overlap between {left} and {right}"
                )
    if manifest.get("dataset_sha256") != dataset_digest.hexdigest():
        raise DatasetAttestationError("dataset aggregate hash mismatch")

    authority_schedule: dict[str, object] | None = None
    if prompt_version == PEANO_PROMPT_V3:
        assert v3_curriculum_evidence is not None
        authority_schedule = _verify_v3_curriculum_schedule(
            v3_curriculum_evidence,
            training_environments,
            inference_environment,
        )

    _replay_builder(traces, metadata, manifest, split_paths)
    result: dict[str, object] = {
        "format": "peano-policy-dataset-attestation",
        "v": (
            ATTESTATION_VERSION
            if prompt_version == PEANO_PROMPT_V3
            else 1
        ),
        "manifest_sha256": sha256_file(manifest_path),
        "attestor": _attestor_manifest(),
        "compiler": compiler,
        "source_artifacts": source_hashes,
        "prompt_version": prompt_version,
        "prompt_contract": prompt_manifest_record(
            prompt_version
        ),
        "prompt_contract_sha256": prompt_contract_sha256(
            prompt_version
        ),
        "library_snapshot_sha256": inference_environment.library_sha256,
        "held_out_contract": held_out,
        "held_out_contract_sha256": held_out_contract_sha256(prompt_version),
        "held_out_contamination": 0,
        "splits": split_results,
        "dataset_sha256": dataset_digest.hexdigest(),
        "independent_replay": True,
    }
    if prompt_version == PEANO_PROMPT_V3:
        result["training_environments"] = list(training_environments)
        result["training_environments_sha256"] = sha256_json(
            list(training_environments)
        )
        assert authority_schedule is not None
        result["authority_schedule"] = authority_schedule
        result["inference_environment"] = environment_record(
            inference_environment
        )
    else:
        result["environment"] = next(iter(expected_environments.values()))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="independently replay and attest one Peano policy dataset"
    )
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--eval", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    attestation = attest_dataset(args.train, args.eval)
    if args.output is None:
        print(json.dumps(attestation, ensure_ascii=False, sort_keys=True))
    else:
        write_manifest(args.output, attestation)
        print(json.dumps({"attestation": str(args.output)}, sort_keys=True))
    return 0


__all__ = [
    "ATTESTATION_VERSION",
    "DatasetAttestationError",
    "attest_dataset",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
