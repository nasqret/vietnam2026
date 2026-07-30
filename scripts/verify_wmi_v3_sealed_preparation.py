#!/usr/bin/env python3
"""Fail closed unless a model-v3 sealed-corpus preparation is coherent.

The preparation reports are deliberately checked both before submission and
again inside the dependent training job.  This verifier uses only the Python
standard library: it does not load model code, trust a report's own filename,
or replay the proof corpus.  Instead it binds the current immutable config and
source deployment to three independently produced records:

* current-source compatibility with the historically checked corpus seal;
* the exact selected-curriculum tokenizer audit; and
* the componentwise longest-active-sequence/longest-completion A100 LoRA
  forward/backward/save/reload smoke, followed by one real bounded
  CompletionOnlyTrainer train/evaluate lifecycle on that memory envelope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
from typing import Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - WMI is Python 3.12
    import tomli as tomllib


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("training/peano_policy/configs/qwen3_1_7b_v3_library.toml")
PREPARE_SCRIPT = Path("slurm/peano_wmi_prepare_v3_sealed_training.sbatch")
SUPPORT_SCRIPT = Path("scripts/wmi_job_environment.sh")
SOURCE_PROVENANCE = Path(".peano-source-provenance.tsv")

MODEL_ID = "Qwen/Qwen3-1.7B-Base"
MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
ELIGIBILITY_FORMAT = "peano-policy-wmi-v3-sealed-corpus-eligibility"
CORPUS_ELIGIBILITY_FORMAT = "peano-policy-v3-sealed-corpus-eligibility"
TOKEN_AUDIT_FORMAT = "peano-policy-token-audit"
SMOKE_FORMAT = "peano-policy-wmi-a100-v3-smoke"
CURRICULUM_FORMAT = "peano-policy-v3-curriculum"
TOKEN_RECORD_FORMAT = "peano-policy-token-exposure"
OBJECTIVE_FORMAT = "peano-completion-only-indexed-logits"
SELECTION_ALGORITHM = "catalog-all-schema-anchor-balanced-whole-sessions-v1"
ADMISSION_FORMAT = "peano-policy-final-adapter-admission"
ADMISSION_SELECTION_FORMAT = "peano-policy-smoke-admission-selection"
ADMISSION_SELECTION_METHOD = "sha256-stratified-admitted-train-validation-v1"
TENSOR_POPULATION_FORMAT = "peano-policy-canonical-peft-tensor-population"
TENSOR_POPULATION_HASH_FORMAT = (
    "sha256-canonical-json-sorted-name-dtype-shape-content-sha256-records-v1"
)
PROJECTED_LOGITS_HASH_FORMAT = (
    "sha256-dtype-shape-header-newline-contiguous-raw-tensor-bytes-v1"
)
OUTPUT_SET_HASH_FORMAT = (
    "sha256-canonical-json-probe-sha256-loss-hex-projected-logits-records-v1"
)
HASH_CANONICALIZATION = "utf8-json-sort-keys-no-whitespace-v1"
ROOT_HEADS = (
    "compact_arith",
    "congr",
    "exists",
    "induction",
    "intro",
    "left",
    "norm_num",
    "refl",
    "rewrite",
    "right",
    "ring",
    "split",
    "symm",
    "trans",
)
SCHEMA_HEADS_SHA256 = "e674f5076d84ad0a7a99cf5c9014b173dd2ff7ae23b602deb753b526b4a30bf1"

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_JOB_ID_RE = re.compile(r"[0-9]+")
_MAX_REPORT_BYTES = 128 * 1024 * 1024


class PreparationVerificationError(ValueError):
    """The sealed preparation cannot authorize an expensive training run."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise PreparationVerificationError(
            f"preparation evidence is not canonical JSON: {exc}"
        ) from exc


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise PreparationVerificationError(f"{label}: expected one object")
    return value


def _exact_mapping(
    value: object,
    keys: set[str],
    label: str,
) -> Mapping[str, object]:
    record = _mapping(value, label)
    if set(record) != keys:
        raise PreparationVerificationError(f"{label}: malformed exact schema")
    return record


def _text(value: object, label: str) -> str:
    if (
        type(value) is not str
        or not value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise PreparationVerificationError(
            f"{label}: expected non-empty control-free text"
        )
    return value


def _sha256(value: object, label: str) -> str:
    text = _text(value, label)
    if _SHA256_RE.fullmatch(text) is None:
        raise PreparationVerificationError(f"{label}: expected lowercase SHA-256")
    return text


def _positive_integer(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise PreparationVerificationError(f"{label}: expected a positive integer")
    return value


def _nonnegative_integer(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise PreparationVerificationError(
            f"{label}: expected a non-negative integer"
        )
    return value


def _read_regular(path: Path, *, label: str, limit: int) -> bytes:
    if path.is_symlink():
        raise PreparationVerificationError(f"{label}: symlinks are forbidden")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PreparationVerificationError(f"{label}: cannot open {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise PreparationVerificationError(f"{label}: path is not a regular file")
        if before.st_size > limit:
            raise PreparationVerificationError(f"{label}: file exceeds {limit} bytes")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise PreparationVerificationError(f"{label}: cannot read {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(raw) > limit:
        raise PreparationVerificationError(f"{label}: file exceeds {limit} bytes")
    identity = lambda value: (  # noqa: E731 - compact immutable stat projection
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )
    if identity(before) != identity(after):
        raise PreparationVerificationError(f"{label}: file changed while being read")
    return raw


def _load_report(path: Path, *, label: str) -> dict[str, object]:
    raw = _read_regular(path, label=label, limit=_MAX_REPORT_BYTES)
    try:
        report = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise PreparationVerificationError(f"{label}: invalid JSON: {exc}") from exc
    if type(report) is not dict:
        raise PreparationVerificationError(f"{label}: expected one JSON object")
    expected = (
        json.dumps(
            report,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if raw != expected:
        raise PreparationVerificationError(
            f"{label}: report is not canonical write_manifest JSON"
        )
    return report


def _report_identity(path: Path, report: Mapping[str, object]) -> dict[str, object]:
    """Bind the exact canonical bytes that ``_load_report`` accepted.

    Re-serializing is safe here because ``_load_report`` has already required
    byte-for-byte ``write_manifest`` canonical JSON.  Avoiding a second read
    also means the identity cannot accidentally describe a replacement made
    after validation.
    """

    raw = (
        json.dumps(
            report,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return {
        "path": str(path.resolve()),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _load_source_commit(root: Path) -> str:
    path = root / SOURCE_PROVENANCE
    raw = _read_regular(path, label="source provenance", limit=1024)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreparationVerificationError("source provenance is not UTF-8") from exc
    if text.count("\n") != 1 or not text.endswith("\n"):
        raise PreparationVerificationError(
            "source provenance must contain exactly one complete row"
        )
    fields = text[:-1].split("\t")
    if (
        len(fields) != 3
        or _COMMIT_RE.fullmatch(fields[0]) is None
        or fields[1] != "false"
        or re.fullmatch(r"[0-9TZ:+-]+", fields[2]) is None
    ):
        raise PreparationVerificationError("source provenance is malformed or dirty")
    return fields[0]


def _load_config(root: Path) -> tuple[dict[str, object], Path, str]:
    path = root / CONFIG_PATH
    raw = _read_regular(path, label="training config", limit=128 * 1024)
    try:
        document = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise PreparationVerificationError(f"training config is invalid TOML: {exc}") from exc
    if type(document) is not dict:
        raise PreparationVerificationError("training config must be one TOML document")
    for name in ("run", "model", "data", "lora", "trainer", "generation", "curriculum"):
        _mapping(document.get(name), f"config [{name}]")

    run = _mapping(document["run"], "config [run]")
    model = _mapping(document["model"], "config [model]")
    data = _mapping(document["data"], "config [data]")
    lora = _mapping(document["lora"], "config [lora]")
    trainer = _mapping(document["trainer"], "config [trainer]")
    generation = _mapping(document["generation"], "config [generation]")
    curriculum = _mapping(document["curriculum"], "config [curriculum]")
    if (
        run.get("name") != "qwen3-1.7b-peano-lora-v3-library"
        or run.get("seed") != 20260729
        or run.get("max_eval_samples") != 512
        or run.get("resume") != "never"
        or "max_train_samples" in run
    ):
        raise PreparationVerificationError(
            "training config lacks the reviewed model-v3 one-shot run contract"
        )
    if (
        model.get("model_id") != MODEL_ID
        or model.get("revision") != MODEL_REVISION
        or model.get("dtype") != "bfloat16"
        or model.get("attn_implementation") != "sdpa"
        or model.get("trust_remote_code") is not False
    ):
        raise PreparationVerificationError("training config has an unreviewed base model")
    if data.get("max_length") != 32768:
        raise PreparationVerificationError("training config changed the 32768-token limit")
    if lora != {
        "rank": 32,
        "alpha": 64,
        "dropout": 0.05,
        "target_modules": [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    }:
        raise PreparationVerificationError(
            "training config changed the reviewed rank-32 full-projection LoRA"
        )
    if (
        trainer.get("epochs") != 1.0
        or trainer.get("max_steps") != -1
        or trainer.get("per_device_train_batch_size") != 1
        or trainer.get("per_device_eval_batch_size") != 1
        or trainer.get("gradient_accumulation_steps") != 32
        or trainer.get("learning_rate") != 0.0001
        or trainer.get("weight_decay") != 0.01
        or trainer.get("warmup_ratio") != 0.05
        or trainer.get("logging_steps") != 10
        or trainer.get("eval_steps") != 1000
        or trainer.get("save_steps") != 1000
        or trainer.get("save_total_limit") != 1
        or trainer.get("gradient_checkpointing") is not True
    ):
        raise PreparationVerificationError(
            "training config lacks the reviewed single-epoch A100 schedule"
        )
    maximum_completion = _positive_integer(
        generation.get("max_new_tokens"), "config generation.max_new_tokens"
    )
    if maximum_completion != 1024:
        raise PreparationVerificationError(
            "training config changed the reviewed 1024-token completion ceiling"
        )
    if (
        generation.get("do_sample") is not False
        or generation.get("temperature") != 1.0
        or generation.get("top_p") != 1.0
    ):
        raise PreparationVerificationError(
            "training config changed the deterministic generation contract"
        )
    if (
        curriculum.get("kind") != "model-v3-library-balanced-v1"
        or curriculum.get("selection_seed") != run.get("seed")
        or curriculum.get("synthetic_row_ceiling") != 12288
    ):
        raise PreparationVerificationError("training config has an unreviewed curriculum")
    for key in (
        "synthetic_row_ceiling",
        "max_train_tokens",
        "max_eval_tokens",
        "max_train_squared_tokens",
        "max_eval_squared_tokens",
    ):
        _positive_integer(curriculum.get(key), f"config curriculum.{key}")
    _sha256(curriculum.get("corpus_content_sha256"), "config corpus content hash")
    source_commit = _text(
        curriculum.get("corpus_source_commit"), "config historical source commit"
    )
    if _COMMIT_RE.fullmatch(source_commit) is None:
        raise PreparationVerificationError("config historical source commit is malformed")
    historical_job = _text(
        curriculum.get("corpus_prepare_job_id"), "config historical preparation job"
    )
    if _JOB_ID_RE.fullmatch(historical_job) is None:
        raise PreparationVerificationError("config historical preparation job is malformed")

    seal = _text(curriculum.get("corpus_seal_path"), "config corpus seal path")
    seal_path = Path(seal)
    if seal_path.is_absolute() or ".." in seal_path.parts:
        raise PreparationVerificationError(
            "WMI corpus seal path must be one safe repository-relative path"
        )
    expected_train = (seal_path / "data" / "train.jsonl").as_posix()
    expected_eval = (seal_path / "data" / "val.jsonl").as_posix()
    if data.get("train_path") != expected_train or data.get("eval_path") != expected_eval:
        raise PreparationVerificationError(
            "training data paths do not point exactly into the configured corpus seal"
        )
    return document, path, hashlib.sha256(raw).hexdigest()


def _verify_self_digest(
    record: Mapping[str, object], field: str, label: str
) -> str:
    core = dict(record)
    claimed = _sha256(core.pop(field, None), f"{label} digest")
    if _sha256_json(core) != claimed:
        raise PreparationVerificationError(f"{label}: self-digest mismatch")
    return claimed


def _validate_job(
    job: object,
    *,
    expected_job_id: str,
    expected_source_commit: str,
    root: Path,
) -> Mapping[str, object]:
    value = _mapping(job, "preparation job identity")
    if value.get("scheduler") != "slurm" or value.get("job_id") != expected_job_id:
        raise PreparationVerificationError("report belongs to a different Slurm job")
    deployment = _mapping(value.get("deployment"), "job deployment")
    source = _mapping(deployment.get("source_sync"), "job source deployment")
    script = _mapping(deployment.get("job_script"), "job script deployment")
    support = _mapping(deployment.get("support_script"), "job support deployment")
    source_path = root / SOURCE_PROVENANCE
    prepare_path = root / PREPARE_SCRIPT
    support_path = root / SUPPORT_SCRIPT
    source_sha = _sha256_file(source_path)
    prepare_file_sha = _sha256_file(prepare_path)
    support_sha = _sha256_file(support_path)
    composite_sha = hashlib.sha256(
        f"{prepare_file_sha}\n{support_sha}\n".encode("ascii")
    ).hexdigest()
    if (
        source.get("status") != "synced"
        or source.get("path") != SOURCE_PROVENANCE.as_posix()
        or source.get("sha256") != source_sha
        or source.get("git_commit") != expected_source_commit
        or source.get("git_dirty") is not False
    ):
        raise PreparationVerificationError("report used a different or dirty source deployment")
    if (
        script.get("status") != "declared"
        or script.get("path") != PREPARE_SCRIPT.as_posix()
        or script.get("file_sha256") != prepare_file_sha
        or script.get("sha256") != composite_sha
    ):
        raise PreparationVerificationError("report used a different preparation script")
    if (
        support.get("status") != "declared"
        or support.get("path") != SUPPORT_SCRIPT.as_posix()
        or support.get("sha256") != support_sha
    ):
        raise PreparationVerificationError("report used a different WMI support script")
    submission = _mapping(value.get("submission"), "job submission row")
    if (
        submission.get("job_id") != expected_job_id
        or submission.get("script") != PREPARE_SCRIPT.as_posix()
        or submission.get("dependency_job_id") != ""
        or submission.get("workdir") != str(root)
        or submission.get("git_commit") != expected_source_commit
        or submission.get("git_dirty") != "false"
        or submission.get("script_sha256") != composite_sha
    ):
        raise PreparationVerificationError("report differs from its preparation submission")
    ledger = _mapping(value.get("ledger"), "job ledger identity")
    if (
        ledger.get("path") != "logs/submissions.tsv"
        or ledger.get("row_sha256") != _sha256_json(dict(submission))
    ):
        raise PreparationVerificationError("report has an invalid submission-ledger binding")
    return value


def _validate_corpus_eligibility(
    value: object,
    *,
    config: Mapping[str, object],
    root: Path,
) -> Mapping[str, object]:
    record = _mapping(value, "sealed-corpus eligibility")
    if (
        record.get("format") != CORPUS_ELIGIBILITY_FORMAT
        or record.get("version") != 1
    ):
        raise PreparationVerificationError(
            "sealed-corpus eligibility has the wrong format/version"
        )
    _verify_self_digest(record, "eligibility_sha256", "sealed-corpus eligibility")
    seal = _mapping(record.get("seal"), "eligibility seal identity")
    curriculum = _mapping(config.get("curriculum"), "config [curriculum]")
    expected_root = str(root / _text(curriculum["corpus_seal_path"], "corpus seal path"))
    if (
        seal.get("root") != expected_root
        or seal.get("format") != "peano-policy-v3-corpus-seal"
        or seal.get("version") != 1
        or seal.get("content_sha256") != curriculum.get("corpus_content_sha256")
        or seal.get("historical_source_commit") != curriculum.get("corpus_source_commit")
        or seal.get("historical_prepare_job_id") != curriculum.get("corpus_prepare_job_id")
    ):
        raise PreparationVerificationError(
            "eligibility differs from the externally anchored corpus seal"
        )
    compatibility = _mapping(
        record.get("current_compatibility"), "current corpus compatibility"
    )
    compiler = _mapping(compatibility.get("compiler"), "current compiler compatibility")
    if compiler.get("status") != "exact-source-inventory-match":
        raise PreparationVerificationError("current compiler was not matched to the seal")
    inputs = _mapping(record.get("inputs"), "eligible corpus inputs")
    data = _mapping(config.get("data"), "config [data]")
    for role, config_key, sealed_path in (
        ("train", "train_path", "data/train.jsonl"),
        ("eval", "eval_path", "data/val.jsonl"),
    ):
        identity = _mapping(inputs.get(role), f"eligible {role} input")
        expected_path = str(root / _text(data[config_key], f"config data.{config_key}"))
        if (
            identity.get("configured_path") != expected_path
            or identity.get("sealed_path") != sealed_path
        ):
            raise PreparationVerificationError(
                f"eligible {role} input differs from the configured sealed file"
            )
        _positive_integer(identity.get("rows"), f"eligible {role} rows")
        _sha256(identity.get("sha256"), f"eligible {role} hash")
    manifest = _mapping(inputs.get("manifest"), "eligible manifest input")
    expected_manifest = str(
        root
        / _text(
            _mapping(config.get("curriculum"), "config [curriculum]")[
                "corpus_seal_path"
            ],
            "config corpus seal path",
        )
        / "data"
        / "manifest.json"
    )
    if (
        manifest.get("configured_path") != expected_manifest
        or manifest.get("sealed_path") != "data/manifest.json"
    ):
        raise PreparationVerificationError(
            "eligible manifest differs from the configured sealed file"
        )
    _sha256(manifest.get("sha256"), "eligible manifest hash")
    historical = _mapping(
        record.get("historical_attestation"), "historical dataset attestation"
    )
    if (
        historical.get("format") != "peano-policy-dataset-attestation"
        or historical.get("version") != 2
        or historical.get("independent_replay") is not True
        or historical.get("held_out_contamination") != 0
    ):
        raise PreparationVerificationError(
            "sealed corpus lacks its independent zero-leakage proof replay"
        )
    return record


def _validate_curriculum(
    value: object, *, config: Mapping[str, object]
) -> Mapping[str, object]:
    record = _mapping(value, "selected curriculum")
    if record.get("format") != CURRICULUM_FORMAT or record.get("v") != 1:
        raise PreparationVerificationError("curriculum has the wrong format/version")
    _verify_self_digest(record, "curriculum_sha256", "selected curriculum")
    selected = _mapping(record.get("selected"), "selected curriculum population")
    selection = _mapping(record.get("selection"), "curriculum selection")
    if selected.get("selection_sha256") != selection.get("selection_sha256"):
        raise PreparationVerificationError("curriculum selection identity is inconsistent")
    _verify_self_digest(selection, "selection_sha256", "curriculum selection")
    run = _mapping(config.get("run"), "config [run]")
    curriculum_config = _mapping(config.get("curriculum"), "config [curriculum]")
    contract = _mapping(selection.get("contract"), "curriculum selection contract")
    selection_selected = _mapping(
        selection.get("selected"), "curriculum selector population"
    )
    catalog = _mapping(selection_selected.get("catalog"), "selected catalog lane")
    synthetic = _mapping(
        selection_selected.get("synthetic"), "selected synthetic lane"
    )
    if (
        selection.get("format") != "peano-policy-v3-curriculum-selection"
        or selection.get("v") != 1
        or selection.get("algorithm") != SELECTION_ALGORITHM
        or selection.get("seed") != str(run.get("seed"))
        or contract.get("library_size") != 247
        or contract.get("expected_catalog_rows") != 8494
        or contract.get("root_heads") != list(ROOT_HEADS)
        or contract.get("schema_count") != 51
        or contract.get("schema_heads_sha256") != SCHEMA_HEADS_SHA256
        or contract.get("synthetic_row_ceiling")
        != curriculum_config.get("synthetic_row_ceiling")
    ):
        raise PreparationVerificationError(
            "curriculum used a different whole-session selector contract"
        )
    selected_rows = _positive_integer(
        selection_selected.get("rows"), "selector selected rows"
    )
    outer_rows = _positive_integer(selected.get("rows"), "selected curriculum rows")
    synthetic_rows = _positive_integer(
        synthetic.get("rows"), "selected synthetic rows"
    )
    synthetic_sessions = _positive_integer(
        synthetic.get("sessions"), "selected synthetic sessions"
    )
    head_records = _mapping(
        synthetic.get("root_heads"), "selected synthetic root heads"
    )
    session_counts = []
    head_row_counts = []
    for head in ROOT_HEADS:
        head_record = _mapping(
            head_records.get(head), f"selected synthetic root head {head}"
        )
        session_counts.append(
            _positive_integer(
                head_record.get("sessions"),
                f"selected synthetic root head {head} sessions",
            )
        )
        head_row_counts.append(
            _positive_integer(
                head_record.get("rows"),
                f"selected synthetic root head {head} rows",
            )
        )
    if (
        set(head_records) != set(ROOT_HEADS)
        or len(set(session_counts)) != 1
        or catalog.get("rows") != 8494
        or catalog.get("sessions") != 247
        or catalog.get("target_count") != 247
        or catalog.get("target_index_range") != [0, 246]
        or synthetic.get("row_ceiling")
        != curriculum_config.get("synthetic_row_ceiling")
        or synthetic_rows > int(curriculum_config["synthetic_row_ceiling"])
        or synthetic.get("schema_count") != 51
        or synthetic.get("root_head_session_imbalance") != 0
        or synthetic_sessions != sum(session_counts)
        or synthetic_rows != sum(head_row_counts)
        or selected_rows != 8494 + synthetic_rows
        or outer_rows != selected_rows
    ):
        raise PreparationVerificationError(
            "curriculum does not contain the complete catalog plus a balanced "
            "whole-session synthetic lane"
        )
    return record


def _validate_token_record(
    value: object,
    *,
    role: str,
    config: Mapping[str, object],
) -> Mapping[str, object]:
    record = _mapping(value, f"{role} token record")
    if (
        record.get("format") != TOKEN_RECORD_FORMAT
        or record.get("v") != 1
        or record.get("role") != role
        or record.get("max_length") != 32768
    ):
        raise PreparationVerificationError(f"{role} token record has the wrong contract")
    _verify_self_digest(record, "record_sha256", f"{role} token record")
    tokenizer = _mapping(record.get("tokenizer"), f"{role} tokenizer identity")
    if tokenizer.get("model_id") != MODEL_ID or tokenizer.get("revision") != MODEL_REVISION:
        raise PreparationVerificationError(f"{role} token record used a different tokenizer")
    rows = _positive_integer(record.get("rows"), f"{role} token rows")
    sequence = _mapping(record.get("sequence"), f"{role} sequence exposure")
    supervision = _mapping(record.get("supervision"), f"{role} supervision exposure")
    maximum = _positive_integer(sequence.get("maximum"), f"{role} maximum sequence")
    total = _positive_integer(sequence.get("total"), f"{role} total tokens")
    squared = _positive_integer(sequence.get("sum_squared"), f"{role} squared tokens")
    maximum_supervision = _positive_integer(
        supervision.get("maximum"), f"{role} maximum completion"
    )
    if maximum > 32768 or total < rows or squared < total:
        raise PreparationVerificationError(f"{role} token exposure is inconsistent")
    curriculum = _mapping(config.get("curriculum"), "config [curriculum]")
    prefix = "train" if role == "train" else "eval"
    if (
        total > _positive_integer(
            curriculum.get(f"max_{prefix}_tokens"), f"config max_{prefix}_tokens"
        )
        or squared
        > _positive_integer(
            curriculum.get(f"max_{prefix}_squared_tokens"),
            f"config max_{prefix}_squared_tokens",
        )
        or maximum_supervision
        > _positive_integer(
            _mapping(config.get("generation"), "config [generation]").get(
                "max_new_tokens"
            ),
            "config maximum completion",
        )
    ):
        raise PreparationVerificationError(f"{role} token exposure exceeds its config gate")
    _text(sequence.get("longest_example_id"), f"{role} longest example id")
    return record


def _validate_split_projection(
    value: object,
    *,
    token_record: Mapping[str, object],
    role: str,
) -> None:
    """Require the compact compatibility summary to equal exact token evidence."""

    summary = _mapping(value, f"{role} compact token summary")
    sequence = _mapping(token_record.get("sequence"), f"{role} sequence exposure")
    expected = {
        "rows": token_record["rows"],
        "minimum": sequence["minimum"],
        "median": sequence["median"],
        "p95": sequence["p95"],
        "p99": sequence["p99"],
        "maximum": sequence["maximum"],
        "mean": sequence["mean"],
        "budget": 32768,
        "headroom": 32768 - int(sequence["maximum"]),
    }
    if summary != expected:
        raise PreparationVerificationError(
            f"{role} compact summary differs from exact token evidence"
        )


def _validate_audit_inputs(
    value: object,
    *,
    corpus: Mapping[str, object],
    curriculum: Mapping[str, object],
    config: Mapping[str, object],
    root: Path,
) -> None:
    inputs = _mapping(value, "token audit input identities")
    if set(inputs) != {"train", "eval", "train_manifest", "eval_manifest"}:
        raise PreparationVerificationError(
            "token audit must bind the two splits and their manifests"
        )
    eligible = _mapping(corpus.get("inputs"), "eligible corpus inputs")
    data = _mapping(config.get("data"), "config [data]")
    for role, key in (("train", "train_path"), ("eval", "eval_path")):
        audited = _mapping(inputs.get(role), f"audited {role} input")
        authorized = _mapping(eligible.get(role), f"eligible {role} input")
        if (
            audited.get("path") != data.get(key)
            or audited.get("bytes") != authorized.get("bytes")
            or audited.get("sha256") != authorized.get("sha256")
        ):
            raise PreparationVerificationError(
                f"token audit {role} input differs from corpus eligibility"
            )
    authorized_manifest = _mapping(
        eligible.get("manifest"), "eligible manifest input"
    )
    expected_manifest_path = str(
        root
        / _text(
            _mapping(config.get("curriculum"), "config [curriculum]")[
                "corpus_seal_path"
            ],
            "config corpus seal path",
        )
        / "data"
        / "manifest.json"
    )
    for role in ("train_manifest", "eval_manifest"):
        audited = _mapping(inputs.get(role), f"audited {role} input")
        if (
            audited.get("path") != expected_manifest_path
            or audited.get("bytes") != authorized_manifest.get("bytes")
            or audited.get("sha256") != authorized_manifest.get("sha256")
        ):
            raise PreparationVerificationError(
                f"token audit {role} differs from corpus eligibility"
            )
    source = _mapping(curriculum.get("source"), "curriculum source")
    selected_train = _mapping(source.get("train"), "curriculum train source")
    selected_manifest = _mapping(source.get("manifest"), "curriculum manifest source")
    train = _mapping(inputs.get("train"), "audited train input")
    manifest = _mapping(inputs.get("train_manifest"), "audited manifest input")
    if any(
        selected_train.get(key) != train.get(key) for key in ("bytes", "sha256")
    ) or any(
        selected_manifest.get(key) != manifest.get(key)
        for key in ("bytes", "sha256")
    ):
        raise PreparationVerificationError(
            "selected curriculum source differs from audited sealed bytes"
        )


def _finite_number(value: object, label: str, *, positive: bool = False) -> float:
    if type(value) not in {int, float}:
        raise PreparationVerificationError(f"{label}: expected a finite number")
    converted = float(value)
    if not math.isfinite(converted) or (positive and converted <= 0.0):
        qualifier = "positive " if positive else ""
        raise PreparationVerificationError(
            f"{label}: expected a finite {qualifier}number"
        )
    return converted


def _validate_logit_fingerprint(value: object, label: str) -> Mapping[str, object]:
    fingerprint = _mapping(value, label)
    shape = fingerprint.get("shape")
    if (
        set(fingerprint) != {"dtype", "shape", "sha256"}
        or fingerprint.get("dtype") != "torch.bfloat16"
        or type(shape) is not list
        or len(shape) != 3
        or any(type(dimension) is not int or dimension < 1 for dimension in shape)
    ):
        raise PreparationVerificationError(f"{label}: malformed projected logits")
    _sha256(fingerprint.get("sha256"), f"{label} hash")
    return fingerprint


def _validate_smoke_runtime(value: object) -> None:
    runtime = _mapping(value, "runtime smoke runtime")
    if runtime.get("machine") != "x86_64":
        raise PreparationVerificationError("runtime smoke did not run on x86_64")
    packages = _mapping(runtime.get("packages"), "runtime package inventory")
    if (
        packages.get("torch") != "2.5.1"
        or packages.get("transformers") != "4.53.3"
        or packages.get("peft") != "0.16.0"
    ):
        raise PreparationVerificationError("runtime smoke used an unreviewed ML stack")
    accelerator = _mapping(runtime.get("accelerator"), "runtime accelerator")
    capability = accelerator.get("device_capability")
    if (
        accelerator.get("cuda_available") is not True
        or accelerator.get("bf16_supported") is not True
        or accelerator.get("cuda_runtime") != "12.4"
        or type(capability) is not list
        or len(capability) != 2
        or any(type(part) is not int or part < 0 for part in capability)
        or tuple(capability) < (8, 0)
        or _positive_integer(
            accelerator.get("total_memory"), "runtime accelerator memory"
        )
        < 70_000_000_000
    ):
        raise PreparationVerificationError(
            "runtime smoke lacks the reviewed BF16 A100-class accelerator"
        )
    _text(accelerator.get("nvidia_driver"), "runtime NVIDIA driver")


def _validate_artifact_group(
    value: object,
    *,
    root: str,
    label: str,
) -> Mapping[str, object]:
    artifacts = _exact_mapping(value, {"root", "sha256", "files"}, label)
    files = _mapping(artifacts.get("files"), f"{label} file inventory")
    if artifacts.get("root") != root or not files:
        raise PreparationVerificationError(f"{label}: malformed closed artifact tree")
    prefix = f"{root}/"
    for name, digest in files.items():
        if (
            type(name) is not str
            or not name.startswith(prefix)
            or Path(name).is_absolute()
            or ".." in Path(name).parts
        ):
            raise PreparationVerificationError(
                f"{label}: malformed artifact inventory path"
            )
        _sha256(digest, f"{label} artifact {name} hash")
    aggregate = _sha256(artifacts.get("sha256"), f"{label} aggregate hash")
    if _sha256_json(dict(files)) != aggregate:
        raise PreparationVerificationError(f"{label}: aggregate hash mismatch")
    return artifacts


def _validate_adapter_artifacts(value: object) -> Mapping[str, object]:
    artifacts = _validate_artifact_group(
        value,
        root="adapter",
        label="smoke adapter artifacts",
    )
    files = _mapping(artifacts.get("files"), "smoke adapter file inventory")
    safe_weights = sorted(
        name for name in files if Path(name).suffix.lower() == ".safetensors"
    )
    if (
        "adapter/adapter_config.json" not in files
        or safe_weights != ["adapter/adapter_model.safetensors"]
        or any(
            Path(name).suffix.lower() in {".bin", ".pkl", ".pickle", ".pt", ".pth"}
            for name in files
        )
    ):
        raise PreparationVerificationError(
            "runtime smoke lacks a closed safetensors adapter artifact"
        )
    return artifacts


def _validate_tokenizer_artifacts(value: object) -> Mapping[str, object]:
    return _validate_artifact_group(
        value,
        root="tokenizer",
        label="smoke tokenizer artifacts",
    )


def _validate_adapter_admission_selection(
    value: object,
    *,
    corpus: Mapping[str, object],
    curriculum: Mapping[str, object],
    train_tokens: Mapping[str, object],
    eval_tokens: Mapping[str, object],
) -> Mapping[str, object]:
    """Bind the bounded smoke probe population to all admitted data records."""

    keys = {
        "format",
        "v",
        "sealed_corpus_eligibility_sha256",
        "curriculum_sha256",
        "tokenized_train_sha256",
        "tokenized_evaluation_sha256",
        "train_candidate_policy",
        "train_candidate_ids",
        "validation_candidate_policy",
        "validation_candidate_id",
        "selection_binding_sha256",
    }
    record = _exact_mapping(value, keys, "adapter admission selection")
    _verify_self_digest(
        record,
        "selection_binding_sha256",
        "adapter admission selection",
    )
    train_sequence = _mapping(train_tokens.get("sequence"), "train sequence exposure")
    train_supervision = _mapping(
        train_tokens.get("supervision"), "train supervision exposure"
    )
    expected_train_ids: list[str] = []
    for candidate in (
        train_sequence.get("longest_example_id"),
        train_supervision.get("longest_example_id"),
    ):
        candidate_id = _text(candidate, "adapter admission train candidate id")
        if candidate_id not in expected_train_ids:
            expected_train_ids.append(candidate_id)
    validation_id = _text(
        record.get("validation_candidate_id"),
        "adapter admission validation candidate id",
    )
    if (
        record.get("format") != ADMISSION_SELECTION_FORMAT
        or record.get("v") != 1
        or record.get("sealed_corpus_eligibility_sha256")
        != corpus.get("eligibility_sha256")
        or record.get("curriculum_sha256") != curriculum.get("curriculum_sha256")
        or record.get("tokenized_train_sha256") != train_tokens.get("record_sha256")
        or record.get("tokenized_evaluation_sha256")
        != eval_tokens.get("record_sha256")
        or record.get("train_candidate_policy") != "natural-memory-extrema-v1"
        or record.get("train_candidate_ids") != expected_train_ids
        or record.get("validation_candidate_policy")
        != "lexicographically-first-example-id-v1"
        or validation_id in expected_train_ids
    ):
        raise PreparationVerificationError(
            "adapter admission selection differs from admitted corpus/token evidence"
        )
    return record


def _validate_adapter_admission(
    value: object,
    *,
    model: Mapping[str, object],
    adapter_artifacts: Mapping[str, object],
    tokenizer_artifacts: Mapping[str, object],
    selection: Mapping[str, object],
) -> Mapping[str, object]:
    """Validate the exact stdlib-only semantic saved-adapter admission record."""

    root = _exact_mapping(
        value,
        {
            "format",
            "v",
            "status",
            "base_model",
            "artifacts",
            "probes",
            "adapter_tensors",
            "reload",
            "checks",
            "hash_contract",
            "content_sha256",
        },
        "adapter admission evidence",
    )
    if (
        root.get("format") != ADMISSION_FORMAT
        or root.get("v") != 1
        or root.get("status") != "passed"
    ):
        raise PreparationVerificationError("adapter admission header is invalid")

    base = _exact_mapping(
        root.get("base_model"),
        {
            "id",
            "requested_revision",
            "resolved_snapshot_hash",
            "config_sha256",
            "dtype",
            "attention",
            "trust_remote_code",
        },
        "admitted base model",
    )
    _sha256(base.get("config_sha256"), "admitted base configuration hash")
    if base != {
        "id": model.get("id"),
        "requested_revision": model.get("requested_revision"),
        "resolved_snapshot_hash": model.get("model_commit"),
        "config_sha256": base.get("config_sha256"),
        "dtype": "bfloat16",
        "attention": "sdpa",
        "trust_remote_code": False,
    }:
        raise PreparationVerificationError(
            "adapter admission used a different pinned base model"
        )

    admitted_artifacts = _exact_mapping(
        root.get("artifacts"),
        {
            "adapter_sha256",
            "adapter_config_sha256",
            "adapter_safetensors_sha256",
            "tokenizer_sha256",
        },
        "admission artifact hashes",
    )
    adapter_files = _mapping(
        adapter_artifacts.get("files"), "smoke adapter file inventory"
    )
    if admitted_artifacts != {
        "adapter_sha256": adapter_artifacts.get("sha256"),
        "adapter_config_sha256": adapter_files.get("adapter/adapter_config.json"),
        "adapter_safetensors_sha256": adapter_files.get(
            "adapter/adapter_model.safetensors"
        ),
        "tokenizer_sha256": tokenizer_artifacts.get("sha256"),
    }:
        raise PreparationVerificationError(
            "adapter admission differs from its saved artifact trees"
        )

    probes = _exact_mapping(
        root.get("probes"),
        {
            "selection_method",
            "selection_binding_sha256",
            "candidate_population_sha256",
            "candidate_count",
            "train_candidate_count",
            "validation_candidate_count",
            "count",
            "set_sha256",
            "records",
            "original_outputs_sha256",
            "fresh_outputs_sha256",
        },
        "admission probes",
    )
    selection_binding = _sha256(
        probes.get("selection_binding_sha256"),
        "admission probe selection binding",
    )
    if (
        probes.get("selection_method") != ADMISSION_SELECTION_METHOD
        or selection_binding != selection.get("selection_binding_sha256")
    ):
        raise PreparationVerificationError(
            "adapter admission differs from its admitted selection binding"
        )
    train_ids = selection.get("train_candidate_ids")
    validation_id = selection.get("validation_candidate_id")
    if type(train_ids) is not list:
        raise PreparationVerificationError("adapter admission train candidates are malformed")
    expected_candidates = {
        *(('train', candidate) for candidate in train_ids),
        ("validation", validation_id),
    }
    expected_count = len(expected_candidates)
    count = _positive_integer(probes.get("count"), "admission probe count")
    if (
        not 2 <= count <= 3
        or probes.get("candidate_count") != expected_count
        or probes.get("train_candidate_count") != len(train_ids)
        or probes.get("validation_candidate_count") != 1
        or count != expected_count
    ):
        raise PreparationVerificationError(
            "adapter admission candidate counts differ from its selection"
        )
    records = probes.get("records")
    if type(records) is not list or len(records) != count:
        raise PreparationVerificationError("adapter admission probe records are malformed")
    exact_records: list[Mapping[str, object]] = []
    observed_candidates: set[tuple[object, object]] = set()
    observed_digests: set[str] = set()
    for index, raw in enumerate(records):
        record = _exact_mapping(
            raw,
            {
                "source",
                "example_id",
                "example_sha256",
                "feature_sha256",
                "candidate_sha256",
                "rank_sha256",
            },
            f"admission probe record {index}",
        )
        source = record.get("source")
        example_id = _text(record.get("example_id"), f"admission probe {index} id")
        example_sha = _sha256(
            record.get("example_sha256"), f"admission probe {index} example hash"
        )
        feature_sha = _sha256(
            record.get("feature_sha256"), f"admission probe {index} feature hash"
        )
        candidate_sha = _sha256(
            record.get("candidate_sha256"), f"admission probe {index} candidate hash"
        )
        rank_sha = _sha256(
            record.get("rank_sha256"), f"admission probe {index} rank hash"
        )
        expected_candidate_sha = _sha256_json(
            {
                "source": source,
                "example_sha256": example_sha,
                "feature_sha256": feature_sha,
            }
        )
        expected_rank_sha = _sha256_json(
            {
                "method": ADMISSION_SELECTION_METHOD,
                "selection_binding_sha256": selection_binding,
                "candidate_sha256": expected_candidate_sha,
            }
        )
        if (
            source not in {"train", "validation"}
            or candidate_sha != expected_candidate_sha
            or rank_sha != expected_rank_sha
        ):
            raise PreparationVerificationError(
                "adapter admission probe hash chain is inconsistent"
            )
        exact_records.append(record)
        observed_candidates.add((source, example_id))
        observed_digests.add(candidate_sha)
    if (
        observed_candidates != expected_candidates
        or len(observed_digests) != count
        or records
        != sorted(
            records,
            key=lambda record: (record["rank_sha256"], record["candidate_sha256"]),
        )
    ):
        raise PreparationVerificationError(
            "adapter admission probes differ from the selected candidates"
        )
    population_records = sorted(
        (
            {
                "source": record["source"],
                "example_id": record["example_id"],
                "candidate_sha256": record["candidate_sha256"],
                "rank_sha256": record["rank_sha256"],
            }
            for record in exact_records
        ),
        key=lambda record: (record["candidate_sha256"], record["source"]),
    )
    if (
        _sha256(probes.get("candidate_population_sha256"), "candidate population hash")
        != _sha256_json(population_records)
        or _sha256(probes.get("set_sha256"), "admission probe-set hash")
        != _sha256_json(records)
        or _sha256(
            probes.get("original_outputs_sha256"), "original admission outputs hash"
        )
        != _sha256(
            probes.get("fresh_outputs_sha256"), "fresh admission outputs hash"
        )
    ):
        raise PreparationVerificationError(
            "adapter admission population/output hashes are inconsistent"
        )

    tensors = _exact_mapping(
        root.get("adapter_tensors"),
        {
            "format",
            "v",
            "tensor_count",
            "names_sha256",
            "population_sha256",
            "population_hash_format",
        },
        "admission adapter tensor population",
    )
    if (
        tensors.get("format") != TENSOR_POPULATION_FORMAT
        or tensors.get("v") != 1
        or tensors.get("population_hash_format") != TENSOR_POPULATION_HASH_FORMAT
    ):
        raise PreparationVerificationError(
            "adapter admission tensor population contract changed"
        )
    _positive_integer(tensors.get("tensor_count"), "admission adapter tensor count")
    _sha256(tensors.get("names_sha256"), "admission adapter tensor-name hash")
    _sha256(tensors.get("population_sha256"), "admission adapter population hash")

    reload = _exact_mapping(
        root.get("reload"),
        {
            "base_model_loads",
            "adapter_loads",
            "tokenizer_loads",
            "adapter_safetensor_reads",
            "adapter_name",
            "device",
        },
        "adapter admission reload counts",
    )
    if reload != {
        "base_model_loads": 1,
        "adapter_loads": 1,
        "tokenizer_loads": 1,
        "adapter_safetensor_reads": 1,
        "adapter_name": "default",
        "device": "cuda:0",
    }:
        raise PreparationVerificationError(
            "adapter admission did not perform one exact CUDA reload"
        )

    checks = _exact_mapping(
        root.get("checks"),
        {
            "tokenizer_encoding_count",
            "exact_reload_count",
            "differs_from_base_count",
        },
        "adapter admission checks",
    )
    differs = checks.get("differs_from_base_count")
    if (
        checks.get("tokenizer_encoding_count") != count
        or checks.get("exact_reload_count") != count
        or type(differs) is not int
        or not 1 <= differs <= count
    ):
        raise PreparationVerificationError("adapter admission checks are inconsistent")

    hashes = _exact_mapping(
        root.get("hash_contract"),
        {
            "algorithm",
            "canonicalization",
            "tensor_population",
            "projected_logits",
            "output_set",
        },
        "adapter admission hash contract",
    )
    if hashes != {
        "algorithm": "sha256",
        "canonicalization": HASH_CANONICALIZATION,
        "tensor_population": TENSOR_POPULATION_HASH_FORMAT,
        "projected_logits": PROJECTED_LOGITS_HASH_FORMAT,
        "output_set": OUTPUT_SET_HASH_FORMAT,
    }:
        raise PreparationVerificationError("adapter admission hash contract changed")
    content = _sha256(root.get("content_sha256"), "adapter admission content hash")
    core = dict(root)
    del core["content_sha256"]
    if _sha256_json(core) != content:
        raise PreparationVerificationError("adapter admission content hash is inconsistent")
    return root


def _validate_smoke_probes(
    value: object,
    *,
    token_record: Mapping[str, object],
    config: Mapping[str, object],
) -> tuple[
    list[Mapping[str, object]],
    Mapping[str, object],
    float,
    float,
    int,
    int,
]:
    if type(value) is not list or not 1 <= len(value) <= 2:
        raise PreparationVerificationError(
            "runtime smoke must contain one or two extremal/envelope probes"
        )
    sequence = _mapping(token_record.get("sequence"), "train sequence exposure")
    supervision = _mapping(token_record.get("supervision"), "train supervision exposure")
    expected_roles = {
        "longest_sequence",
        "longest_completion",
        "combined_memory_envelope",
    }
    observed_roles: set[str] = set()
    observed_ids: set[str] = set()
    probes: list[Mapping[str, object]] = []
    total_seconds = 0.0
    peak_allocated = 0
    peak_reserved = 0
    configured_learning_rate = float(
        _mapping(config.get("trainer"), "config [trainer]")["learning_rate"]
    )
    for index, raw in enumerate(value, 1):
        probe = _mapping(raw, f"runtime smoke probe {index}")
        example_id = _text(probe.get("id"), f"runtime smoke probe {index} id")
        roles = probe.get("roles")
        if (
            example_id in observed_ids
            or type(roles) is not list
            or not roles
            or len(set(roles)) != len(roles)
            or any(role not in expected_roles for role in roles)
        ):
            raise PreparationVerificationError("runtime smoke probe roles are malformed")
        observed_ids.add(example_id)
        for role in roles:
            if role in observed_roles:
                raise PreparationVerificationError(
                    "runtime smoke repeats an extremal probe role"
                )
            observed_roles.add(role)
        sequence_tokens = _positive_integer(
            probe.get("sequence_tokens"), f"runtime smoke probe {index} sequence"
        )
        attended_tokens = _positive_integer(
            probe.get("attended_tokens"),
            f"runtime smoke probe {index} attended sequence",
        )
        if attended_tokens != sequence_tokens:
            raise PreparationVerificationError(
                "runtime smoke memory envelope contains inactive sequence tokens"
            )
        supervised_tokens = _positive_integer(
            probe.get("supervised_tokens"),
            f"runtime smoke probe {index} supervision",
        )
        if probe.get("projected_positions") != supervised_tokens:
            raise PreparationVerificationError(
                "runtime smoke projected positions differ from supervised tokens"
            )
        if "longest_sequence" in roles and (
            example_id != sequence.get("longest_example_id")
            or sequence_tokens != sequence.get("maximum")
        ):
            raise PreparationVerificationError(
                "runtime smoke sequence probe is not the attested extremum"
            )
        construction = probe.get("construction")
        synthetic_envelope = (
            construction
            == "attended-masked-prompt-extension-to-longest-sequence"
        )
        if "longest_completion" in roles:
            completion_id = (
                probe.get("source_example_id") if synthetic_envelope else example_id
            )
            if (
                completion_id != supervision.get("longest_example_id")
                or supervised_tokens != supervision.get("maximum")
            ):
                raise PreparationVerificationError(
                    "runtime smoke completion probe is not the attested extremum"
                )
        if "combined_memory_envelope" in roles:
            if (
                sequence_tokens != sequence.get("maximum")
                or supervised_tokens != supervision.get("maximum")
            ):
                raise PreparationVerificationError(
                    "runtime smoke memory envelope is not componentwise maximal"
                )
            if construction == "natural-row":
                if not {"longest_sequence", "longest_completion"} <= set(roles):
                    raise PreparationVerificationError(
                        "natural memory envelope lacks both extremal roles"
                    )
            elif (
                construction
                == "attended-masked-prompt-extension-to-longest-sequence"
            ):
                source_id = _text(
                    probe.get("source_example_id"),
                    "runtime memory-envelope source id",
                )
                inserted_prompt_tokens = _positive_integer(
                    probe.get("inserted_prompt_tokens"),
                    "runtime memory-envelope inserted prompt tokens",
                )
                if (
                    roles != ["longest_completion", "combined_memory_envelope"]
                    or source_id != supervision.get("longest_example_id")
                    or example_id != source_id
                    or inserted_prompt_tokens >= sequence_tokens
                ):
                    raise PreparationVerificationError(
                        "active memory-envelope construction is inconsistent"
                    )
            else:
                raise PreparationVerificationError(
                    "runtime smoke memory envelope has an unknown construction"
                )
        training = _mapping(probe.get("training"), f"runtime smoke probe {index} training")
        _finite_number(training.get("loss"), f"runtime smoke probe {index} loss")
        learning_rate = _finite_number(
            training.get("learning_rate"),
            f"runtime smoke probe {index} learning rate",
            positive=True,
        )
        if learning_rate > configured_learning_rate:
            raise PreparationVerificationError(
                "runtime smoke probe learning rate exceeds the configured peak"
            )
        seconds = _finite_number(
            training.get("seconds"),
            f"runtime smoke probe {index} seconds",
            positive=True,
        )
        allocated = _positive_integer(
            training.get("peak_cuda_allocated_bytes"),
            f"runtime smoke probe {index} CUDA allocation",
        )
        reserved = _positive_integer(
            training.get("peak_cuda_reserved_bytes"),
            f"runtime smoke probe {index} CUDA reservation",
        )
        gradients = _mapping(
            training.get("gradients"), f"runtime smoke probe {index} gradients"
        )
        _positive_integer(
            gradients.get("parameters_with_grad"),
            f"runtime smoke probe {index} gradient population",
        )
        _finite_number(
            gradients.get("norm_before_clip"),
            f"runtime smoke probe {index} gradient norm",
        )
        if gradients.get("max_norm") != 1.0 or type(gradients.get("clipped")) is not bool:
            raise PreparationVerificationError(
                "runtime smoke did not apply Trainer-compatible gradient clipping"
            )
        post_step = _mapping(
            probe.get("post_step_eval"), f"runtime smoke probe {index} post-step"
        )
        reloaded = _mapping(
            probe.get("reloaded_eval"), f"runtime smoke probe {index} reload"
        )
        post_loss = _finite_number(
            post_step.get("loss"), f"runtime smoke probe {index} post-step loss"
        )
        reload_loss = _finite_number(
            reloaded.get("loss"), f"runtime smoke probe {index} reload loss"
        )
        post_logits = _validate_logit_fingerprint(
            post_step.get("projected_logits"),
            f"runtime smoke probe {index} post-step logits",
        )
        reload_logits = _validate_logit_fingerprint(
            reloaded.get("projected_logits"),
            f"runtime smoke probe {index} reloaded logits",
        )
        if (
            reloaded.get("exact_match") is not True
            or reload_loss != post_loss
            or reload_logits != post_logits
        ):
            raise PreparationVerificationError(
                "runtime smoke reload differs from exact post-step semantics"
            )
        total_seconds += seconds
        peak_allocated = max(peak_allocated, allocated)
        peak_reserved = max(peak_reserved, reserved)
        probes.append(probe)
    if observed_roles != expected_roles:
        raise PreparationVerificationError(
            "runtime smoke did not cover both extrema and their memory envelope"
        )
    envelopes = [
        probe
        for probe in probes
        if "combined_memory_envelope" in probe.get("roles", [])
    ]
    if len(envelopes) != 1:
        raise PreparationVerificationError(
            "runtime smoke must identify exactly one memory envelope"
        )
    return (
        probes,
        envelopes[0],
        total_seconds,
        float(probes[0]["training"]["loss"]),
        peak_allocated,
        peak_reserved,
    )


def _validate_trainer_integration(
    value: object,
    *,
    envelope_probe: Mapping[str, object],
    config: Mapping[str, object],
    trainable_parameter_tensors: int,
) -> dict[str, object]:
    """Require a real one-step Trainer lifecycle on the maximal smoke batch."""

    integration = _mapping(value, "runtime Trainer integration")
    training_loss = _finite_number(
        integration.get("training_loss"),
        "runtime Trainer integration training loss",
        positive=True,
    )
    evaluation_loss = _finite_number(
        integration.get("evaluation_loss"),
        "runtime Trainer integration evaluation loss",
        positive=True,
    )
    if (
        integration.get("format")
        != "peano-completion-only-trainer-integration"
        or integration.get("v") != 1
        or integration.get("trainer")
        != "CompletionOnlyTrainerMixin+transformers.Trainer"
        or integration.get("train_global_step") != 1
    ):
        raise PreparationVerificationError(
            "runtime smoke did not run the exact CompletionOnlyTrainer lifecycle"
        )

    batch = _mapping(integration.get("batch"), "runtime Trainer integration batch")
    expected_batch = {
        "role": "componentwise-maximal-memory-envelope",
        "probe_id": envelope_probe["id"],
        "construction": envelope_probe["construction"],
        "sequence_tokens": envelope_probe["sequence_tokens"],
        "attended_tokens": envelope_probe["attended_tokens"],
        "supervised_tokens": envelope_probe["supervised_tokens"],
        "projected_positions": envelope_probe["projected_positions"],
    }
    if batch != expected_batch:
        raise PreparationVerificationError(
            "runtime Trainer integration did not use the maximal memory envelope"
        )

    configured_trainer = _mapping(config.get("trainer"), "config [trainer]")
    arguments = _mapping(
        integration.get("arguments"), "runtime Trainer integration arguments"
    )
    expected_arguments = {
        "max_steps": 1,
        "per_device_train_batch_size": 1,
        "per_device_eval_batch_size": 1,
        "gradient_accumulation_steps": 1,
        "learning_rate": configured_trainer["learning_rate"],
        "weight_decay": configured_trainer["weight_decay"],
        "bf16": True,
        "tf32": True,
        "gradient_checkpointing": True,
        "gradient_checkpointing_kwargs": {"use_reentrant": False},
        "warmup_steps": 0,
        "optimizer": "adamw_torch_fused",
        "adam_beta1": 0.9,
        "adam_beta2": 0.999,
        "adam_epsilon": 1e-8,
        "trainer_builtin_clip": "disabled",
        "trainer_builtin_max_grad_norm": 0.0,
        "custom_pre_optimizer_clip": 1.0,
        "custom_pre_optimizer_error_if_nonfinite": True,
        "average_tokens_across_devices": True,
        "logging_nan_inf_filter": False,
        "save_strategy": "no",
        "eval_strategy": "no",
    }
    if arguments != expected_arguments:
        raise PreparationVerificationError(
            "runtime Trainer integration used different bounded arguments"
        )

    runtime = _mapping(
        integration.get("runtime"), "runtime Trainer integration runtime"
    )
    expected_runtime = {
        "format": "peano-completion-only-trainer-runtime",
        "v": 1,
        "num_processes": 1,
        "visible_gpus": 1,
        "device": {"type": "cuda", "index": 0},
        "mixed_precision": "bf16",
        "distributed_type": {"name": "NO", "value": "NO"},
        "dynamo_backend": {"name": "NO", "value": "NO"},
        "plugins": {
            "deepspeed": False,
            "fsdp": False,
            "tensor_parallel": False,
        },
        "manual_trainer_accumulation": True,
        "configured_trainer_gradient_accumulation_steps": 1,
        "accelerator_backward_divisor": 1,
    }
    if runtime != expected_runtime:
        raise PreparationVerificationError(
            "runtime Trainer integration used an unreviewed Accelerator runtime"
        )

    gradients = _mapping(
        integration.get("gradients"), "runtime Trainer integration gradients"
    )
    if gradients.get("hook") != "on_pre_optimizer_step":
        raise PreparationVerificationError(
            "runtime Trainer integration clipped outside the pre-optimizer hook"
        )
    raw_gradients = _mapping(
        gradients.get("raw"), "runtime Trainer integration raw gradients"
    )
    if (
        raw_gradients.get("parameters_with_finite_grad")
        != trainable_parameter_tensors
    ):
        raise PreparationVerificationError(
            "runtime Trainer integration did not observe every LoRA gradient"
        )
    raw_names_sha256 = _sha256(
        raw_gradients.get("parameter_names_sha256"),
        "runtime Trainer integration gradient population hash",
    )
    custom_clip = _mapping(
        gradients.get("custom_pre_optimizer_clip"),
        "runtime Trainer integration custom gradient clip",
    )
    if (
        custom_clip.get("max_norm") != 1.0
        or custom_clip.get("error_if_nonfinite") is not True
        or type(custom_clip.get("clipped")) is not bool
    ):
        raise PreparationVerificationError(
            "runtime Trainer integration did not apply strict custom clipping"
        )
    _finite_number(
        custom_clip.get("norm_before_clip"),
        "runtime Trainer integration pre-clip gradient norm",
    )
    postclip = _mapping(
        custom_clip.get("postclip"),
        "runtime Trainer integration post-clip gradients",
    )
    if (
        postclip.get("parameters_with_finite_grad")
        != trainable_parameter_tensors
        or _sha256(
            postclip.get("parameter_names_sha256"),
            "runtime Trainer integration post-clip gradient population hash",
        )
        != raw_names_sha256
    ):
        raise PreparationVerificationError(
            "runtime Trainer integration did not preserve finite post-clip gradients"
        )
    update = _mapping(
        integration.get("adapter_update"),
        "runtime Trainer integration adapter update",
    )
    changed = _positive_integer(
        update.get("changed_parameter_tensors"),
        "runtime Trainer integration changed adapter tensors",
    )
    if changed > trainable_parameter_tensors:
        raise PreparationVerificationError(
            "runtime Trainer integration changed too many adapter tensors"
        )
    _sha256(
        update.get("changed_parameter_names_sha256"),
        "runtime Trainer integration changed tensor-name hash",
    )

    for role in ("train", "evaluation"):
        runtime = _mapping(
            integration.get(f"{role}_runtime"),
            f"runtime Trainer integration {role} runtime",
        )
        _finite_number(
            runtime.get("seconds"),
            f"runtime Trainer integration {role} seconds",
            positive=True,
        )
        allocated = _positive_integer(
            runtime.get("peak_cuda_allocated_bytes"),
            f"runtime Trainer integration {role} CUDA allocation",
        )
        reserved = _positive_integer(
            runtime.get("peak_cuda_reserved_bytes"),
            f"runtime Trainer integration {role} CUDA reservation",
        )
        if reserved < allocated:
            raise PreparationVerificationError(
                f"runtime Trainer integration {role} CUDA reservation is too small"
            )
    return {
        "train_global_step": 1,
        "training_loss": training_loss,
        "evaluation_loss": evaluation_loss,
    }


def verify_reports(
    *,
    eligibility_report: Path,
    token_audit_report: Path,
    smoke_report: Path,
    prepare_job_id: str,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, object]:
    """Cross-check all reports against the current source and reviewed config."""

    if _JOB_ID_RE.fullmatch(prepare_job_id) is None:
        raise PreparationVerificationError("preparation job id must be decimal text")
    root = repository_root.resolve()
    expected_names = {
        "eligibility": f"peano-wmi-v3-sealed-eligibility-{prepare_job_id}.json",
        "token audit": f"peano-wmi-v3-token-audit-{prepare_job_id}.json",
        "runtime smoke": f"peano-wmi-v3-prepare-runtime-{prepare_job_id}.json",
    }
    paths = {
        "eligibility": eligibility_report,
        "token audit": token_audit_report,
        "runtime smoke": smoke_report,
    }
    logs_root = (root / "logs").resolve()
    for label, path in paths.items():
        if path.name != expected_names[label]:
            raise PreparationVerificationError(f"{label}: unexpected report filename")
        if path.parent.resolve() != logs_root:
            raise PreparationVerificationError(
                f"{label}: report must be directly inside the repository logs directory"
            )

    config, config_path, config_sha = _load_config(root)
    source_commit = _load_source_commit(root)
    eligibility = _load_report(eligibility_report, label="eligibility report")
    audit = _load_report(token_audit_report, label="token audit report")
    smoke = _load_report(smoke_report, label="runtime smoke report")

    if (
        eligibility.get("format") != ELIGIBILITY_FORMAT
        or eligibility.get("v") != 1
        or eligibility.get("status") != "passed"
    ):
        raise PreparationVerificationError("eligibility report has the wrong contract")
    eligibility_config = _mapping(eligibility.get("config"), "eligibility config")
    if (
        eligibility_config.get("path") != str(config_path.resolve())
        or eligibility_config.get("sha256") != config_sha
    ):
        raise PreparationVerificationError("eligibility used a different training config")
    eligibility_job = _validate_job(
        eligibility.get("job"),
        expected_job_id=prepare_job_id,
        expected_source_commit=source_commit,
        root=root,
    )
    corpus = _validate_corpus_eligibility(
        eligibility.get("sealed_corpus_eligibility"), config=config, root=root
    )

    if (
        audit.get("format") != TOKEN_AUDIT_FORMAT
        or audit.get("v") != 2
        or audit.get("status") != "passed"
    ):
        raise PreparationVerificationError("token audit has the wrong v2 contract")
    audit_config = _mapping(audit.get("config"), "token audit config")
    if (
        audit_config.get("path") != str(config_path.resolve())
        or audit_config.get("sha256") != config_sha
        or audit_config.get("max_length") != 32768
    ):
        raise PreparationVerificationError("token audit used a different training config")
    if audit.get("sealed_corpus_eligibility") != corpus:
        raise PreparationVerificationError("token audit used a different corpus eligibility")
    curriculum = _validate_curriculum(audit.get("curriculum"), config=config)
    historical_attestation = _mapping(
        audit.get("sealed_dataset_attestation"),
        "sealed historical dataset attestation",
    )
    authority_schedule = _mapping(
        historical_attestation.get("authority_schedule"),
        "sealed historical authority schedule",
    )
    if (
        historical_attestation.get("format")
        != "peano-policy-dataset-attestation"
        or historical_attestation.get("v") != 2
        or historical_attestation.get("prompt_version") != 3
        or historical_attestation.get("independent_replay") is not True
        or historical_attestation.get("held_out_contamination") != 0
        or authority_schedule.get("method")
        != "catalog-predecessor-prefix-v1+full-synthetic-v1"
        or authority_schedule.get("library_size") != 247
        or authority_schedule.get("training_prefixes") != list(range(248))
        or authority_schedule.get("inference_prefix") != 247
    ):
        raise PreparationVerificationError(
            "token audit lacks the sealed zero-leakage authority schedule"
        )
    _validate_audit_inputs(
        audit.get("inputs"),
        corpus=corpus,
        curriculum=curriculum,
        config=config,
        root=root,
    )
    tokenized = _mapping(audit.get("tokenized_splits"), "tokenized split evidence")
    if set(tokenized) != {"train", "eval"}:
        raise PreparationVerificationError("token audit must bind exactly train and eval")
    train_tokens = _validate_token_record(tokenized["train"], role="train", config=config)
    eval_tokens = _validate_token_record(tokenized["eval"], role="eval", config=config)
    if _mapping(train_tokens.get("tokenizer"), "train tokenizer") != _mapping(
        eval_tokens.get("tokenizer"), "eval tokenizer"
    ) or audit.get("tokenizer") != train_tokens.get("tokenizer"):
        raise PreparationVerificationError("token audit tokenizer identities disagree")
    if train_tokens.get("rows") != _mapping(
        curriculum.get("selected"), "selected curriculum"
    ).get("rows"):
        raise PreparationVerificationError("token audit row count differs from selection")
    compact_splits = _mapping(audit.get("splits"), "compact token summaries")
    if set(compact_splits) != {"train", "eval"}:
        raise PreparationVerificationError("token audit must summarize train and eval")
    _validate_split_projection(
        compact_splits["train"], token_record=train_tokens, role="train"
    )
    _validate_split_projection(
        compact_splits["eval"], token_record=eval_tokens, role="eval"
    )
    gates = _mapping(audit.get("compute_gates"), "token audit compute gates")
    config_curriculum = _mapping(config.get("curriculum"), "config [curriculum]")
    config_generation = _mapping(config.get("generation"), "config [generation]")
    expected_gates = {
        "max_train_tokens": config_curriculum["max_train_tokens"],
        "max_eval_tokens": config_curriculum["max_eval_tokens"],
        "max_train_squared_tokens": config_curriculum["max_train_squared_tokens"],
        "max_eval_squared_tokens": config_curriculum["max_eval_squared_tokens"],
        "max_supervised_tokens": config_generation["max_new_tokens"],
    }
    if gates != expected_gates:
        raise PreparationVerificationError("token audit used different compute gates")

    if (
        smoke.get("format") != SMOKE_FORMAT
        or smoke.get("v") != 2
        or smoke.get("status") != "passed"
    ):
        raise PreparationVerificationError("runtime smoke has the wrong v2 contract")
    smoke_job = _validate_job(
        smoke.get("job"),
        expected_job_id=prepare_job_id,
        expected_source_commit=source_commit,
        root=root,
    )
    if smoke_job != eligibility_job:
        raise PreparationVerificationError("preparation reports have different job identities")
    if smoke.get("corpus_eligibility") != corpus:
        raise PreparationVerificationError("runtime smoke used a different corpus eligibility")
    if smoke.get("curriculum") != curriculum:
        raise PreparationVerificationError("runtime smoke used a different curriculum")
    if smoke.get("tokenized_train") != train_tokens:
        raise PreparationVerificationError("runtime smoke used different training tokens")
    if smoke.get("tokenized_evaluation") != eval_tokens:
        raise PreparationVerificationError("runtime smoke used different evaluation tokens")
    admission_selection = _validate_adapter_admission_selection(
        smoke.get("adapter_admission_selection"),
        corpus=corpus,
        curriculum=curriculum,
        train_tokens=train_tokens,
        eval_tokens=eval_tokens,
    )
    model = _mapping(smoke.get("model"), "runtime smoke model")
    if (
        model.get("id") != MODEL_ID
        or model.get("requested_revision") != MODEL_REVISION
        or model.get("model_commit") != MODEL_REVISION
        or model.get("tokenizer_commit") != MODEL_REVISION
    ):
        raise PreparationVerificationError("runtime smoke loaded a different model snapshot")
    example = _mapping(smoke.get("example"), "runtime smoke example")
    train_sequence = _mapping(train_tokens.get("sequence"), "train token exposure")
    if (
        example.get("selection") != "longest-reviewed-curriculum-row"
        or example.get("id") != train_sequence.get("longest_example_id")
        or example.get("sequence_tokens") != train_sequence.get("maximum")
    ):
        raise PreparationVerificationError("runtime smoke did not exercise the longest row")
    objective = _mapping(smoke.get("objective"), "runtime smoke objective")
    projection = _mapping(objective.get("projection"), "runtime smoke logit projection")
    if (
        objective.get("format") != OBJECTIVE_FORMAT
        or objective.get("v") != 1
        or projection.get("model_argument") != "logits_to_keep"
    ):
        raise PreparationVerificationError("runtime smoke did not use indexed completion loss")
    platform_contract = _mapping(
        smoke.get("platform_contract"), "runtime smoke platform contract"
    )
    if platform_contract != {
        "expected_machine": "x86_64",
        "minimum_cuda_capability": [8, 0],
        "report_format": SMOKE_FORMAT,
    }:
        raise PreparationVerificationError("runtime smoke used a different platform contract")
    _validate_smoke_runtime(smoke.get("runtime"))
    lora = _mapping(smoke.get("lora"), "runtime smoke LoRA evidence")
    configured_lora = _mapping(config.get("lora"), "config [lora]")
    if (
        lora.get("rank") != configured_lora.get("rank")
        or lora.get("alpha") != configured_lora.get("alpha")
        or lora.get("dropout") != configured_lora.get("dropout")
        or lora.get("target_modules") != configured_lora.get("target_modules")
        or _positive_integer(
            lora.get("trainable_parameters"), "runtime trainable parameter count"
        )
        < 1
    ):
        raise PreparationVerificationError("runtime smoke used a different LoRA contract")
    adapter_artifacts = _validate_adapter_artifacts(lora.get("adapter_artifacts"))
    tokenizer_artifacts = _validate_tokenizer_artifacts(
        lora.get("tokenizer_artifacts")
    )
    adapter_admission = _validate_adapter_admission(
        smoke.get("adapter_admission"),
        model=model,
        adapter_artifacts=adapter_artifacts,
        tokenizer_artifacts=tokenizer_artifacts,
        selection=admission_selection,
    )
    adapter_update = _mapping(lora.get("adapter_update"), "runtime adapter update")
    _positive_integer(
        adapter_update.get("changed_parameter_tensors"),
        "changed adapter tensor count",
    )
    _sha256(
        adapter_update.get("changed_parameter_names_sha256"),
        "changed adapter tensor-name hash",
    )
    (
        probes,
        envelope_probe,
        probe_seconds,
        first_training_loss,
        probe_peak_allocated,
        probe_peak_reserved,
    ) = _validate_smoke_probes(
        smoke.get("smoke_probes"), token_record=train_tokens, config=config
    )
    step = _mapping(smoke.get("step"), "runtime smoke optimizer step")
    memory_envelope = _mapping(
        step.get("memory_envelope"), "runtime smoke memory envelope"
    )
    expected_envelope = {
        "probe_id": envelope_probe["id"],
        "construction": envelope_probe["construction"],
        "sequence_tokens": envelope_probe["sequence_tokens"],
        "attended_tokens": envelope_probe["attended_tokens"],
        "supervised_tokens": envelope_probe["supervised_tokens"],
        "dominance": "componentwise-maxima-over-tokenized-selected-curriculum",
    }
    if (
        step.get("gradient_checkpointing") is not True
        or step.get("use_cache") is not False
        or step.get("optimizer") != "adamw_torch_fused"
        or step.get("gradient_clip_max_norm") != 1.0
        or step.get("tf32") is not True
        or step.get("probe_count") != len(probes)
        or not math.isclose(
            _finite_number(step.get("seconds"), "runtime smoke total seconds", positive=True),
            probe_seconds,
            rel_tol=0.0,
            abs_tol=0.000002 * len(probes),
        )
        or step.get("peak_cuda_allocated_bytes") != probe_peak_allocated
        or step.get("peak_cuda_reserved_bytes") != probe_peak_reserved
        or memory_envelope != expected_envelope
    ):
        raise PreparationVerificationError("runtime smoke lacks a reviewed optimizer step")
    optimizer = _mapping(smoke.get("optimizer"), "runtime optimizer evidence")
    configured_trainer = _mapping(config.get("trainer"), "config [trainer]")
    decay_parameter_tensors = _nonnegative_integer(
        optimizer.get("decay_parameter_tensors"), "decayed parameter tensors"
    )
    no_decay_parameter_tensors = _nonnegative_integer(
        optimizer.get("no_decay_parameter_tensors"),
        "non-decayed parameter tensors",
    )
    trainable_parameter_tensors = (
        decay_parameter_tensors + no_decay_parameter_tensors
    )
    if (
        optimizer.get("name") != "adamw_torch_fused"
        or optimizer.get("betas") != [0.9, 0.999]
        or optimizer.get("epsilon") != 1e-8
        or optimizer.get("learning_rate") != configured_trainer.get("learning_rate")
        or optimizer.get("weight_decay") != configured_trainer.get("weight_decay")
        or trainable_parameter_tensors < 1
    ):
        raise PreparationVerificationError("runtime smoke used a different optimizer")
    if _mapping(
        adapter_admission.get("adapter_tensors"),
        "admission adapter tensor population",
    ).get("tensor_count") != trainable_parameter_tensors:
        raise PreparationVerificationError(
            "adapter admission tensor population differs from the optimizer"
        )
    scheduler = _mapping(smoke.get("scheduler"), "runtime scheduler evidence")
    train_rows = int(train_tokens["rows"])
    updates_per_epoch = math.ceil(train_rows / 32)
    total_steps = math.ceil(float(configured_trainer["epochs"]) * updates_per_epoch)
    warmup_steps = math.ceil(total_steps * float(configured_trainer["warmup_ratio"]))
    peak_lrs = scheduler.get("probe_start_learning_rates")
    if (
        scheduler.get("name") != "cosine"
        or scheduler.get("train_rows") != train_rows
        or scheduler.get("dataloader_batches") != train_rows
        or scheduler.get("updates_per_epoch") != updates_per_epoch
        or scheduler.get("total_steps") != total_steps
        or scheduler.get("warmup_steps") != warmup_steps
        or scheduler.get("warmup_advance")
        != "optimizer-and-scheduler-steps-with-no-gradients"
        or type(scheduler.get("initial_learning_rates")) is not list
        or type(peak_lrs) is not list
        or not peak_lrs
        or any(rate != configured_trainer.get("learning_rate") for rate in peak_lrs)
    ):
        raise PreparationVerificationError("runtime smoke used a different scheduler")
    trainer_integration = _validate_trainer_integration(
        smoke.get("trainer_integration"),
        envelope_probe=envelope_probe,
        config=config,
        trainable_parameter_tensors=trainable_parameter_tensors,
    )
    losses = _mapping(smoke.get("loss"), "runtime smoke loss summary")
    first_reload = _mapping(probes[0]["reloaded_eval"], "primary reloaded probe")
    if (
        losses.get("training") != first_training_loss
        or losses.get("reloaded") != first_reload.get("loss")
    ):
        raise PreparationVerificationError("runtime smoke loss summary differs from probes")

    return {
        "format": "peano-policy-wmi-v3-sealed-preparation-verification",
        "v": 1,
        "status": "verified",
        "prepare_job_id": prepare_job_id,
        "source_commit": source_commit,
        "config_sha256": config_sha,
        "reports": {
            "eligibility": _report_identity(eligibility_report, eligibility),
            "token_audit": _report_identity(token_audit_report, audit),
            "runtime_smoke": _report_identity(smoke_report, smoke),
        },
        "corpus_content_sha256": _mapping(corpus.get("seal"), "seal identity")[
            "content_sha256"
        ],
        "corpus_eligibility_sha256": corpus["eligibility_sha256"],
        "curriculum_sha256": curriculum["curriculum_sha256"],
        "train_token_record_sha256": train_tokens["record_sha256"],
        "eval_token_record_sha256": eval_tokens["record_sha256"],
        "adapter_admission_selection_binding_sha256": admission_selection[
            "selection_binding_sha256"
        ],
        "adapter_admission_content_sha256": adapter_admission["content_sha256"],
        "longest_example_id": example["id"],
        "longest_sequence_tokens": example["sequence_tokens"],
        "trainer_integration": trainer_integration,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eligibility-report", type=Path, required=True)
    parser.add_argument("--token-audit-report", type=Path, required=True)
    parser.add_argument("--smoke-report", type=Path, required=True)
    parser.add_argument("--prepare-job-id", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_reports(
            eligibility_report=args.eligibility_report,
            token_audit_report=args.token_audit_report,
            smoke_report=args.smoke_report,
            prepare_job_id=args.prepare_job_id,
        )
    except (OSError, PreparationVerificationError) as exc:
        print(f"WMI v3 sealed preparation rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
