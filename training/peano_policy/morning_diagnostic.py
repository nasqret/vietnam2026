#!/usr/bin/env python3
"""Bounded, non-production model-v3 training for the 2026-07-31 check.

The production curriculum remains gated on an immutable corpus seal.  This
module is a deliberately separate emergency lane: it admits the exact corpus
bytes and independent replay attestation produced by WMI job 173040, selects a
small theorem-stratified population, and records that selection in a diagnostic
sidecar.  It must never be described as the full or sealed model-v3 run.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import heapq
import importlib
import json
import os
from pathlib import Path
import random
import re
from typing import Any, Iterable

from .config import ExperimentConfig, load_config
from .data import ProofExample, example_from_record
from .manifest import sha256_file, sha256_json, write_manifest


FORMAT = "peano-policy-v3-morning-diagnostic"
VERSION = 1
CATALOG_TRAJECTORY = "catalog-predecessor-prefix-v1"
EXPECTED_CATALOG_SESSIONS = 247
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_JOB_RE = re.compile(r"[0-9]+")


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _decode_record(line: str, *, location: str) -> dict[str, Any]:
    try:
        value = json.loads(
            line,
            object_pairs_hook=_strict_object,
            parse_constant=lambda item: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON constant {item}")
            ),
        )
    except (json.JSONDecodeError, UnicodeError, ValueError) as exc:
        raise ValueError(f"{location}: invalid JSON: {exc}") from exc
    if type(value) is not dict:
        raise ValueError(f"{location}: expected one JSON object")
    return value


def _read_attestation(path: Path, expected_sha256: str) -> dict[str, object]:
    if _SHA256_RE.fullmatch(expected_sha256) is None:
        raise ValueError("dataset attestation anchor must be one SHA-256 digest")
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"attestation is not one regular file: {path}")
    if sha256_file(path) != expected_sha256:
        raise ValueError("dataset attestation differs from its admitted SHA-256")
    value = _decode_record(path.read_text(encoding="utf-8"), location=str(path))
    if (
        value.get("format") != "peano-policy-dataset-attestation"
        or value.get("v") != 2
        or value.get("prompt_version") != 3
        or value.get("independent_replay") is not True
        or value.get("held_out_contamination") != 0
    ):
        raise ValueError("historical dataset attestation is not an admitted v3 replay")
    schedule = value.get("authority_schedule")
    if (
        type(schedule) is not dict
        or schedule.get("method")
        != "catalog-predecessor-prefix-v1+full-synthetic-v1"
        or schedule.get("library_size") != EXPECTED_CATALOG_SESSIONS
        or schedule.get("training_prefixes")
        != list(range(EXPECTED_CATALOG_SESSIONS + 1))
        or schedule.get("inference_prefix") != EXPECTED_CATALOG_SESSIONS
    ):
        raise ValueError("historical authority schedule is not the reviewed v3 schedule")
    return value


def _require_digest(label: str, path: Path, expected: str) -> None:
    if _SHA256_RE.fullmatch(expected) is None:
        raise ValueError(f"{label} anchor must be one SHA-256 digest")
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"{label} is not one regular file: {path}")
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {observed} != {expected}")


def _rank(seed: int, session: object, step: object) -> int:
    payload = json.dumps(
        [seed, session, step],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest(), "big")


def _hash_sample_records(
    path: Path,
    *,
    count: int,
    seed: int,
    exclude_catalog: bool,
) -> list[tuple[int, dict[str, Any]]]:
    heap: list[tuple[int, int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            record = _decode_record(line, location=f"{path}:{line_number}")
            metadata = record.get("metadata")
            if type(metadata) is not dict:
                raise ValueError(f"{path}:{line_number}: metadata is not an object")
            if exclude_catalog and metadata.get("trajectory") == CATALOG_TRAJECTORY:
                continue
            rank = _rank(seed, record.get("session"), record.get("step"))
            item = (-rank, -line_number, record)
            if len(heap) < count:
                heapq.heappush(heap, item)
            elif item > heap[0]:
                heapq.heapreplace(heap, item)
    if len(heap) != count:
        raise ValueError(f"{path}: cannot select {count} diagnostic rows")
    return sorted((-line, record) for _, line, record in heap)


def _catalog_boundary_records(
    path: Path,
) -> list[tuple[int, dict[str, Any]]]:
    boundaries: dict[str, tuple[tuple[int, dict[str, Any]], tuple[int, dict[str, Any]]]] = {}
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            record = _decode_record(line, location=f"{path}:{line_number}")
            metadata = record.get("metadata")
            if type(metadata) is not dict:
                raise ValueError(f"{path}:{line_number}: metadata is not an object")
            if metadata.get("trajectory") != CATALOG_TRAJECTORY:
                continue
            session = record.get("session")
            step = record.get("step")
            if type(session) is not str or not session or type(step) is not int or step < 1:
                raise ValueError(f"{path}:{line_number}: malformed catalog identity")
            item = (line_number, record)
            existing = boundaries.get(session)
            if existing is None:
                boundaries[session] = (item, item)
            else:
                first, last = existing
                first_step = first[1]["step"]
                last_step = last[1]["step"]
                if step < first_step:
                    first = item
                if step > last_step:
                    last = item
                boundaries[session] = (first, last)
    if len(boundaries) != EXPECTED_CATALOG_SESSIONS:
        raise ValueError(
            f"catalog session count changed: {len(boundaries)} != "
            f"{EXPECTED_CATALOG_SESSIONS}"
        )
    selected: list[tuple[int, dict[str, Any]]] = []
    for session in sorted(boundaries):
        first, last = boundaries[session]
        selected.append(first)
        if last[1]["step"] != first[1]["step"]:
            selected.append(last)
    return selected


def _examples(
    records: Iterable[tuple[int, dict[str, Any]]],
) -> list[ProofExample]:
    return [example_from_record(record, line_number) for line_number, record in records]


def _select_training(
    path: Path,
    *,
    count: int,
    seed: int,
) -> tuple[list[ProofExample], dict[str, object]]:
    catalog = _catalog_boundary_records(path)
    if len(catalog) > count:
        raise ValueError("diagnostic row budget cannot cover catalog boundaries")
    synthetic_count = count - len(catalog)
    synthetic = _hash_sample_records(
        path,
        count=synthetic_count,
        seed=seed,
        exclude_catalog=True,
    )
    selected = _examples([*catalog, *synthetic])
    random.Random(seed).shuffle(selected)
    ids = [example.example_id for example in selected]
    if len(ids) != count or len(set(ids)) != count:
        raise ValueError("diagnostic training selection is incomplete or repeated")
    return selected, {
        "method": "catalog-first-last-plus-hashed-synthetic-v1",
        "catalog_sessions": EXPECTED_CATALOG_SESSIONS,
        "catalog_rows": len(catalog),
        "synthetic_rows": synthetic_count,
        "rows": count,
        "ordered_example_ids": ids,
        "ordered_example_ids_sha256": sha256_json(ids),
    }


def _select_evaluation(
    path: Path,
    *,
    count: int,
    seed: int,
) -> tuple[list[ProofExample], dict[str, object]]:
    selected = _examples(
        _hash_sample_records(
            path,
            count=count,
            seed=seed,
            exclude_catalog=False,
        )
    )
    random.Random(seed).shuffle(selected)
    ids = [example.example_id for example in selected]
    if len(ids) != count or len(set(ids)) != count:
        raise ValueError("diagnostic evaluation selection is incomplete or repeated")
    return selected, {
        "method": "sha256-ranked-validation-v1",
        "rows": count,
        "ordered_example_ids": ids,
        "ordered_example_ids_sha256": sha256_json(ids),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset-attestation", type=Path, required=True)
    parser.add_argument("--dataset-attestation-sha256", required=True)
    parser.add_argument("--dataset-manifest-sha256", required=True)
    parser.add_argument("--train-sha256", required=True)
    parser.add_argument("--eval-sha256", required=True)
    parser.add_argument("--historical-source-commit", required=True)
    parser.add_argument("--historical-prepare-job-id", required=True)
    return parser


def run(args: argparse.Namespace) -> Path:
    if _COMMIT_RE.fullmatch(args.historical_source_commit) is None:
        raise ValueError("historical source commit must be lowercase 40-hex")
    if _JOB_RE.fullmatch(args.historical_prepare_job_id) is None:
        raise ValueError("historical preparation job id must be decimal")
    config: ExperimentConfig = load_config(args.config)
    train_path = Path(config.data.train_path)
    eval_path = Path(config.data.eval_path)
    manifest_path = train_path.parent / "manifest.json"
    if train_path.parent != eval_path.parent:
        raise ValueError("diagnostic train and evaluation splits must be siblings")
    _require_digest("dataset manifest", manifest_path, args.dataset_manifest_sha256)
    _require_digest("training split", train_path, args.train_sha256)
    _require_digest("evaluation split", eval_path, args.eval_sha256)
    attestation = _read_attestation(
        args.dataset_attestation,
        args.dataset_attestation_sha256,
    )
    splits = attestation.get("splits")
    if (
        type(splits) is not dict
        or type(splits.get("train")) is not dict
        or splits["train"].get("sha256") != args.train_sha256
        or splits["train"].get("rows") != 64500
        or type(splits.get("val")) is not dict
        or splits["val"].get("sha256") != args.eval_sha256
        or splits["val"].get("rows") != 6948
    ):
        raise ValueError("historical attestation does not bind the admitted splits")

    expected_train = config.run.max_train_samples
    expected_eval = config.run.max_eval_samples
    if expected_train != 512 or expected_eval != 16:
        raise ValueError("morning diagnostic population must remain 512/16")
    training, training_selection = _select_training(
        train_path,
        count=expected_train,
        seed=config.run.seed,
    )
    evaluation, evaluation_selection = _select_evaluation(
        eval_path,
        count=expected_eval,
        seed=config.run.seed + 1,
    )

    train_module = importlib.import_module("training.peano_policy.train")
    original_attest = train_module.attest_dataset
    original_load = train_module.load_examples

    def cached_attestation(observed_train: Path, observed_eval: Path) -> dict[str, object]:
        if (
            observed_train.resolve() != train_path.resolve()
            or observed_eval.resolve() != eval_path.resolve()
        ):
            raise ValueError("training requested data outside the admitted corpus")
        return copy.deepcopy(attestation)

    def selected_examples(
        observed_path: Path,
        *,
        max_samples: int | None = None,
        seed: int = 0,
    ) -> list[ProofExample]:
        resolved = observed_path.resolve()
        if resolved == train_path.resolve():
            if max_samples != expected_train or seed != config.run.seed:
                raise ValueError("training selection request differs from diagnostic plan")
            return list(training)
        if resolved == eval_path.resolve():
            if max_samples != expected_eval or seed != config.run.seed + 1:
                raise ValueError("evaluation selection request differs from diagnostic plan")
            return list(evaluation)
        return original_load(observed_path, max_samples=max_samples, seed=seed)

    train_module.attest_dataset = cached_attestation
    train_module.load_examples = selected_examples
    try:
        completed_manifest = train_module.train(config, resume_override="never")
    finally:
        train_module.attest_dataset = original_attest
        train_module.load_examples = original_load

    output_dir = Path(config.run.output_dir)
    sidecar = output_dir / "morning-diagnostic.json"
    if sidecar.exists():
        raise FileExistsError(f"refusing to replace diagnostic sidecar: {sidecar}")
    record = {
        "format": FORMAT,
        "v": VERSION,
        "status": "completed-diagnostic-not-production",
        "warning": (
            "Bounded morning check over an authenticated historical corpus; "
            "not the sealed full model-v3 curriculum or final adapter."
        ),
        "historical_source_commit": args.historical_source_commit,
        "historical_prepare_job_id": args.historical_prepare_job_id,
        "corpus": {
            "attestation_path": str(args.dataset_attestation),
            "attestation_sha256": args.dataset_attestation_sha256,
            "manifest_path": str(manifest_path),
            "manifest_sha256": args.dataset_manifest_sha256,
            "train_path": str(train_path),
            "train_sha256": args.train_sha256,
            "eval_path": str(eval_path),
            "eval_sha256": args.eval_sha256,
        },
        "selection": {
            "train": training_selection,
            "eval": evaluation_selection,
        },
        "training_manifest": {
            "path": str(completed_manifest),
            "sha256": sha256_file(completed_manifest),
        },
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }
    write_manifest(sidecar, record)
    return sidecar


def main() -> int:
    sidecar = run(_parser().parse_args())
    print(json.dumps({"morning_diagnostic": str(sidecar)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
