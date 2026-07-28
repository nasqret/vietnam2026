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


ATTESTATION_VERSION = 1
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
BUILDER = REPOSITORY_ROOT / "scripts" / "build_peano_policy_dataset.py"
EXPORTER = REPOSITORY_ROOT / "scripts" / "export_traces.py"


class DatasetAttestationError(ValueError):
    """A dataset is not reproducibly authorized for the fixed policy run."""


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


def _expected_environment_record() -> dict[str, object]:
    return environment_record(model_v1_environment())


def _verify_environment(manifest: Mapping[str, object]) -> dict[str, object]:
    environments = manifest.get("environments")
    expected = _expected_environment_record()
    if type(environments) is not list or len(environments) != 1:
        raise DatasetAttestationError(
            "training data must contain exactly one fixed policy environment"
        )
    record = environments[0]
    if type(record) is not dict or type(record.get("sessions")) is not int:
        raise DatasetAttestationError("dataset environment record is malformed")
    visible = {key: record.get(key) for key in expected}
    if visible != expected or record["sessions"] < 1:
        raise DatasetAttestationError(
            "dataset environment differs from the fixed model-v1 authority"
        )
    return expected


def _stream_split(
    path: Path,
    split: str,
    split_record: Mapping[str, object],
    *,
    expected_environment: Mapping[str, object],
    forbidden_formulas: frozenset[str],
    forbidden_names: frozenset[str],
) -> tuple[int, str, frozenset[str], frozenset[str]]:
    digest = hashlib.sha256()
    rows = 0
    formulas: set[str] = set()
    prompts: set[str] = set()
    try:
        stream = path.open("rb")
    except OSError as exc:
        raise DatasetAttestationError(f"cannot open dataset split {path}: {exc}") from exc
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
            environment = {
                "classical": record["classical"],
                "surface": record["surface"],
                "environment_sha256": record["environment_sha256"],
                "capabilities": record["capabilities"],
            }
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
            rows += 1
    actual_hash = digest.hexdigest()
    if split_record.get("rows") != rows or split_record.get("sha256") != actual_hash:
        raise DatasetAttestationError(f"{path}: split counters/hash mismatch")
    return rows, actual_hash, frozenset(formulas), frozenset(prompts)


def _replay_builder(
    traces: tuple[Path, ...],
    metadata: Path,
    manifest: Mapping[str, object],
    split_paths: Mapping[str, Path],
) -> None:
    split = manifest.get("split")
    if type(split) is not dict or split.get("method") != (
        "sha256-ranked-genealogy-formula-prompt-components-v2"
    ):
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
            timeout=3_600,
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
    expected_environment = _verify_environment(manifest)
    split_table = manifest.get("splits")
    if type(split_table) is not dict or tuple(split_table) != SPLITS:
        raise DatasetAttestationError("dataset split table is not canonical")

    forbidden_formulas = frozenset(canonical_held_out_formulas())
    held_out = held_out_contract_record()
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
    for split_name in SPLITS:
        split_record = split_table[split_name]
        if type(split_record) is not dict:
            raise DatasetAttestationError(f"{split_name} split record is malformed")
        rows, digest, formulas, prompts = _stream_split(
            split_paths[split_name],
            split_name,
            split_record,
            expected_environment=expected_environment,
            forbidden_formulas=forbidden_formulas,
            forbidden_names=forbidden_names,
        )
        dataset_digest.update(split_name.encode("ascii") + b"\0")
        with split_paths[split_name].open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                dataset_digest.update(chunk)
        split_results[split_name] = {"rows": rows, "sha256": digest}
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

    _replay_builder(traces, metadata, manifest, split_paths)
    return {
        "format": "peano-policy-dataset-attestation",
        "v": ATTESTATION_VERSION,
        "manifest_sha256": sha256_file(manifest_path),
        "attestor": _attestor_manifest(),
        "compiler": compiler,
        "source_artifacts": source_hashes,
        "environment": expected_environment,
        "held_out_contract": held_out,
        "held_out_contract_sha256": held_out_contract_sha256(),
        "held_out_contamination": 0,
        "splits": split_results,
        "dataset_sha256": dataset_digest.hexdigest(),
        "independent_replay": True,
    }


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
