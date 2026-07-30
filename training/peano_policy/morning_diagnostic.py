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
from .data import IGNORE_INDEX, ProofExample, example_from_record, tokenize_completion
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


def _token_split_record(
    *,
    role: str,
    examples: list[ProofExample],
    tokenizer: Any,
    max_length: int,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for example in examples:
        encoded = tokenize_completion(example, tokenizer, max_length=max_length)
        sequence_tokens = len(encoded["input_ids"])
        supervised_tokens = sum(
            token != IGNORE_INDEX for token in encoded["labels"]
        )
        rows.append(
            {
                "example_id": example.example_id,
                "sequence_tokens": sequence_tokens,
                "supervised_tokens": supervised_tokens,
            }
        )
    if not rows:
        raise ValueError(f"{role} token audit has no rows")
    lengths = [int(row["sequence_tokens"]) for row in rows]
    maximum = max(lengths)
    if maximum > max_length:
        raise ValueError(f"{role} selection exceeds the model token budget")
    longest = min(
        row["example_id"]
        for row in rows
        if row["sequence_tokens"] == maximum
    )
    return {
        "role": role,
        "rows": len(rows),
        "budget": max_length,
        "minimum": min(lengths),
        "maximum": maximum,
        "mean": round(sum(lengths) / len(lengths), 6),
        "longest_example_id": longest,
        "length_records_sha256": sha256_json(rows),
    }


def _audit_selected_tokens(
    config: ExperimentConfig,
    *,
    training: list[ProofExample],
    evaluation: list[ProofExample],
) -> dict[str, object]:
    """Tokenize exactly the selected 512/16 rows with the pinned tokenizer."""

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        use_fast=True,
        trust_remote_code=config.model.trust_remote_code,
    )
    resolved = tokenizer.init_kwargs.get("_commit_hash") or config.model.revision
    if resolved != config.model.revision or tokenizer.eos_token_id is None:
        raise RuntimeError("diagnostic tokenizer differs from its pinned revision")
    core = {
        "format": "peano-policy-v3-morning-selected-token-audit",
        "v": 1,
        "tokenizer": {
            "class": type(tokenizer).__name__,
            "model_id": config.model.model_id,
            "revision": resolved,
            "vocab_size": len(tokenizer),
        },
        "splits": {
            "train": _token_split_record(
                role="train",
                examples=training,
                tokenizer=tokenizer,
                max_length=config.data.max_length,
            ),
            "eval": _token_split_record(
                role="eval",
                examples=evaluation,
                tokenizer=tokenizer,
                max_length=config.data.max_length,
            ),
        },
    }
    return {**core, "token_audit_sha256": sha256_json(core)}


def _install_pending_manifest(
    completed_manifest: Path,
    *,
    diagnostic: dict[str, object],
) -> str:
    """Mark a saved adapter as non-production before attempting its reload."""

    core = dict(diagnostic)
    claimed = core.pop("diagnostic_sha256", None)
    reload_probe = diagnostic.get("reload_probe")
    if (
        diagnostic.get("format") != FORMAT
        or diagnostic.get("v") != VERSION
        or diagnostic.get("status") != "pending-reload-probe"
        or type(claimed) is not str
        or sha256_json(core) != claimed
        or type(reload_probe) is not dict
        or reload_probe.get("path") != "morning-reload-probe.json"
        or reload_probe.get("sha256") is not None
    ):
        raise ValueError("pending diagnostic authority is incomplete or inconsistent")
    if not completed_manifest.is_file() or completed_manifest.is_symlink():
        raise FileNotFoundError("completed training manifest is not one regular file")
    for unpublished in (
        completed_manifest.parent / "morning-diagnostic.json",
        completed_manifest.parent / "morning-reload-probe.json",
    ):
        if unpublished.exists() or unpublished.is_symlink():
            raise FileExistsError(f"refusing stale diagnostic artifact: {unpublished}")
    manifest = _decode_record(
        completed_manifest.read_text(encoding="utf-8"),
        location=str(completed_manifest),
    )
    if manifest.get("prompt_version") != 3 or "diagnostic" in manifest:
        raise ValueError("training manifest cannot enter pending diagnostic state")
    manifest["diagnostic"] = diagnostic
    write_manifest(completed_manifest, manifest)
    return sha256_file(completed_manifest)


def _bind_completed_manifest(
    completed_manifest: Path,
    *,
    diagnostic: dict[str, object],
) -> tuple[Path, str]:
    """Put the real selection in loader-visible authority, then add a receipt.

    The historical trainer cannot know about this emergency selection policy.
    Its initial manifest is therefore incomplete until this function adds the
    exact diagnostic record.  The sidecar points to the hash of that final
    manifest; the manifest points back to the sidecar by its fixed basename and
    remains self-sufficient if the convenience sidecar is moved or removed.
    """

    if not completed_manifest.is_file() or completed_manifest.is_symlink():
        raise FileNotFoundError("completed training manifest is not one regular file")
    manifest = _decode_record(
        completed_manifest.read_text(encoding="utf-8"),
        location=str(completed_manifest),
    )
    previous = manifest.get("diagnostic")
    if (
        manifest.get("prompt_version") != 3
        or type(previous) is not dict
        or previous.get("status") != "pending-reload-probe"
    ):
        raise ValueError("training manifest cannot admit the morning diagnostic")
    previous_core = dict(previous)
    previous_claimed = previous_core.pop("diagnostic_sha256", None)
    final_core = dict(diagnostic)
    final_claimed = final_core.pop("diagnostic_sha256", None)
    if (
        type(previous_claimed) is not str
        or sha256_json(previous_core) != previous_claimed
        or type(final_claimed) is not str
        or sha256_json(final_core) != final_claimed
        or diagnostic.get("status") != "completed-diagnostic-not-production"
    ):
        raise ValueError("diagnostic transition has invalid authority hashes")
    for key in set(previous_core) | set(final_core):
        if (
            key not in {"status", "reload_probe"}
            and previous_core.get(key) != final_core.get(key)
        ):
            raise ValueError(f"diagnostic transition changed stable field {key!r}")
    previous_probe = previous.get("reload_probe")
    final_probe = diagnostic.get("reload_probe")
    if (
        type(previous_probe) is not dict
        or previous_probe.get("path") != "morning-reload-probe.json"
        or previous_probe.get("sha256") is not None
        or type(final_probe) is not dict
        or final_probe.get("path") != "morning-reload-probe.json"
        or type(final_probe.get("sha256")) is not str
        or _SHA256_RE.fullmatch(final_probe["sha256"]) is None
    ):
        raise ValueError("diagnostic transition has malformed reload-probe authority")
    report = completed_manifest.parent / final_probe["path"]
    if (
        not report.is_file()
        or report.is_symlink()
        or sha256_file(report) != final_probe["sha256"]
    ):
        raise ValueError("reload probe differs from completed diagnostic authority")
    pending_manifest_sha256 = sha256_file(completed_manifest)
    probe = _decode_record(report.read_text(encoding="utf-8"), location=str(report))
    expected_probe_keys = {
        "format",
        "v",
        "status",
        "loader",
        "current_hardened_v3_loader_compatible",
        "pending_training_manifest_sha256",
        "pending_diagnostic_sha256",
        "slurm_job_id",
        "example_id",
        "expected_tactic",
        "generated_text",
        "parsed_tactic",
        "valid_single_tactic",
        "exact_match",
        "decode",
    }
    if (
        set(probe) != expected_probe_keys
        or probe.get("format") != "peano-policy-v3-morning-reload-probe"
        or probe.get("v") != 1
        or probe.get("status") != "probe-completed"
        or probe.get("loader") != "explicit-historical-diagnostic-admission-v1"
        or probe.get("current_hardened_v3_loader_compatible") is not False
        or probe.get("pending_training_manifest_sha256")
        != pending_manifest_sha256
        or probe.get("pending_diagnostic_sha256") != previous_claimed
        or probe.get("slurm_job_id") != previous_core.get("slurm_job_id")
        or type(probe.get("example_id")) is not str
        or not probe["example_id"]
        or type(probe.get("expected_tactic")) is not str
        or not probe["expected_tactic"]
        or type(probe.get("generated_text")) is not str
        or type(probe.get("valid_single_tactic")) is not bool
        or type(probe.get("exact_match")) is not bool
        or probe.get("decode") != {"max_new_tokens": 64, "do_sample": False}
    ):
        raise ValueError("reload probe is not valid pending-manifest evidence")
    from .prompt import extract_one_tactic

    try:
        observed_tactic = extract_one_tactic(probe["generated_text"])
        observed_valid = True
    except (TypeError, ValueError):
        observed_tactic = None
        observed_valid = False
    if (
        probe.get("parsed_tactic") != observed_tactic
        or probe.get("valid_single_tactic") is not observed_valid
        or probe.get("exact_match") is not (
            observed_tactic == probe["expected_tactic"]
        )
    ):
        raise ValueError("reload probe tactic fields are inconsistent")
    sidecar = completed_manifest.parent / "morning-diagnostic.json"
    if sidecar.exists() or sidecar.is_symlink():
        raise FileExistsError(f"refusing to replace diagnostic sidecar: {sidecar}")
    manifest["diagnostic"] = diagnostic
    write_manifest(completed_manifest, manifest)
    manifest_sha256 = sha256_file(completed_manifest)

    write_manifest(
        sidecar,
        {
            "format": FORMAT,
            "v": VERSION,
            "status": "completed-diagnostic-not-production",
            "diagnostic_sha256": diagnostic["diagnostic_sha256"],
            "training_manifest": {
                "path": str(completed_manifest),
                "sha256": manifest_sha256,
            },
        },
    )
    return sidecar, manifest_sha256


def _audit_adapter_tensors(output_dir: Path) -> dict[str, object]:
    """Require the saved LoRA population to remain FP32 after evaluation."""

    from safetensors import safe_open

    path = output_dir / "adapter" / "adapter_model.safetensors"
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError("diagnostic adapter safetensors is unavailable")
    with safe_open(path, framework="pt", device="cpu") as tensors:
        keys = sorted(tensors.keys())
        dtypes: dict[str, int] = {}
        for key in keys:
            dtype = str(tensors.get_tensor(key).dtype)
            dtypes[dtype] = dtypes.get(dtype, 0) + 1
    if not keys or set(dtypes) != {"torch.float32"}:
        raise RuntimeError(f"diagnostic LoRA tensors are not all FP32: {dtypes}")
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "tensors": len(keys),
        "dtypes": dtypes,
        "tensor_names_sha256": sha256_json(keys),
    }


def _reload_probe(
    output_dir: Path,
    *,
    example: ProofExample,
    seed: int,
    pending_training_manifest_sha256: str,
    pending_diagnostic_sha256: str,
) -> tuple[Path, str]:
    """Reload safetensors and generate once with explicit diagnostic admission."""

    import gc

    import torch

    from .contract import attested_training_environment
    from .generate import generate_raw_tactic, load_adapter
    from .prompt import extract_one_tactic

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    model, tokenizer, manifest = load_adapter(
        output_dir,
        seed=seed,
        diagnostic_mode=True,
        _allow_pending_diagnostic_probe=True,
    )
    environment = attested_training_environment(manifest)
    generated = generate_raw_tactic(
        model=model,
        tokenizer=tokenizer,
        prompt=example.prompt,
        environment=environment,
        max_new_tokens=64,
        do_sample=False,
        temperature=1.0,
        top_p=1.0,
    )
    try:
        parsed = extract_one_tactic(generated)
        valid_single_tactic = True
    except (TypeError, ValueError):
        parsed = None
        valid_single_tactic = False
    report = output_dir / "morning-reload-probe.json"
    if report.exists() or report.is_symlink():
        raise FileExistsError(f"refusing to replace reload probe: {report}")
    write_manifest(
        report,
        {
            "format": "peano-policy-v3-morning-reload-probe",
            "v": 1,
            "status": "probe-completed",
            "loader": "explicit-historical-diagnostic-admission-v1",
            "current_hardened_v3_loader_compatible": False,
            "pending_training_manifest_sha256": pending_training_manifest_sha256,
            "pending_diagnostic_sha256": pending_diagnostic_sha256,
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "example_id": example.example_id,
            "expected_tactic": example.tactic,
            "generated_text": generated,
            "parsed_tactic": parsed,
            "valid_single_tactic": valid_single_tactic,
            "exact_match": parsed == example.tactic,
            "decode": {"max_new_tokens": 64, "do_sample": False},
        },
    )
    return report, sha256_file(report)


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
    selected_token_audit = _audit_selected_tokens(
        config,
        training=training,
        evaluation=evaluation,
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
        completed_manifest = train_module.train(
            config,
            resume_override="never",
            checkpoint_strategy="no",
            bf16_full_eval_override=False,
        )
    finally:
        train_module.attest_dataset = original_attest
        train_module.load_examples = original_load

    output_dir = Path(config.run.output_dir)
    # A legacy Trainer checkpoint contains a pickle-compatible optimizer state
    # on this runtime.  This bounded lane must publish only the explicit final
    # safetensors adapter and tokenizer.
    checkpoints = sorted(output_dir.glob("checkpoint-*"))
    if checkpoints:
        raise RuntimeError(
            "morning diagnostic unexpectedly published Trainer checkpoints: "
            + ", ".join(path.name for path in checkpoints)
        )
    adapter_tensor_audit = _audit_adapter_tensors(output_dir)
    diagnostic_stable = {
        "format": FORMAT,
        "v": VERSION,
        "warning": (
            "Bounded morning check over an authenticated historical corpus; "
            "not the sealed full model-v3 curriculum or final adapter."
        ),
        "current_hardened_v3_loader_compatible": False,
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
        "selected_token_audit": selected_token_audit,
        "checkpoint_policy": "disabled-no-optimizer-pickle",
        "evaluation_dtype_policy": "bf16-full-eval-disabled-preserve-fp32-lora",
        "adapter_tensor_audit": adapter_tensor_audit,
        "sidecar": "morning-diagnostic.json",
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }
    pending_core = {
        **diagnostic_stable,
        "status": "pending-reload-probe",
        "reload_probe": {
            "path": "morning-reload-probe.json",
            "sha256": None,
        },
    }
    pending_diagnostic = {
        **pending_core,
        "diagnostic_sha256": sha256_json(pending_core),
    }
    pending_manifest_sha256 = _install_pending_manifest(
        completed_manifest,
        diagnostic=pending_diagnostic,
    )
    reload_report, reload_report_sha256 = _reload_probe(
        output_dir,
        example=evaluation[0],
        seed=config.run.seed,
        pending_training_manifest_sha256=pending_manifest_sha256,
        pending_diagnostic_sha256=pending_diagnostic["diagnostic_sha256"],
    )
    final_core = {
        **diagnostic_stable,
        "status": "completed-diagnostic-not-production",
        "reload_probe": {
            "path": reload_report.name,
            "sha256": reload_report_sha256,
        },
    }
    final_diagnostic = {
        **final_core,
        "diagnostic_sha256": sha256_json(final_core),
    }
    sidecar, final_manifest_sha256 = _bind_completed_manifest(
        completed_manifest,
        diagnostic=final_diagnostic,
    )
    print(
        json.dumps(
            {
                "final_training_manifest_sha256": final_manifest_sha256,
                "reload_probe": str(reload_report),
            },
            sort_keys=True,
        )
    )
    return sidecar


def main() -> int:
    sidecar = run(_parser().parse_args())
    print(json.dumps({"morning_diagnostic": str(sidecar)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
