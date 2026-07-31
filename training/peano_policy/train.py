#!/usr/bin/env python3
"""BF16 LoRA completion SFT for a Qwen3 Peano next-tactic policy.

Heavy dependencies are imported only inside ``train``.  Importing this module
is therefore safe in documentation tools and lightweight unit tests.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import random
import stat
import tempfile
from typing import Any

from .adapter_admission import (
    BaseReloadContract,
    admit_saved_adapter,
    capture_in_memory_policy,
    restore_model_for_adapter_admission,
    select_admission_probes,
    validate_manifest_adapter_admission,
)
from .attest import attest_dataset
from .budget import (
    enforce_token_budget,
    tokenize_split,
    tokenizer_identity_record,
)
from .config import ExperimentConfig, load_config
from .corpus_eligibility import verify_sealed_corpus_eligibility
from .curriculum import load_curriculum
from .data import (
    IGNORE_INDEX,
    dataset_manifest_path,
    load_examples,
    tokenize_completion,
)
from .manifest import (
    ADAPTER_SUBDIR,
    MANIFEST_VERSION,
    TOKENIZER_SUBDIR,
    artifact_directory_hash,
    publish_staged_directory_noreplace,
    require_safetensors_adapter,
    sha256_file,
    sha256_json,
    source_hash,
    verify_artifact_directory,
    write_manifest_noreplace,
)
from .objective import (
    CompletionOnlyTrainerMixin,
    completion_objective_record,
    require_indexed_logits_support,
    single_process_trainer_runtime_record,
)
from .prompt import (
    PEANO_PROMPT_V3,
    ProofExample,
    prompt_contract_sha256,
    prompt_manifest_record,
    prompt_version_from_manifest,
)
from .recovery import (
    AdapterRecoveryCallbackMixin,
    AdapterRecoverySnapshotter,
    CLAIM_RENAME_PUBLICATION_PROFILE,
    NATIVE_PUBLICATION_PROFILE,
    recovery_snapshot_plan,
    verify_recovery_publication_preflight,
)
from .runtime import deployment_identity, runtime_identity, slurm_job_identity
from .training_evidence import (
    CUSTOM_GRADIENT_CLIP_MAX_NORM,
    TENSOR_POPULATION_FINGERPRINT_FORMAT,
    FiniteGradientAudit,
    TrainingEvidenceError,
    adapter_update_audit_record,
    completed_training_evidence_record,
    reviewed_trainer_arguments_record,
    validate_completed_training_evidence,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path(__file__).resolve().parent
RUN_IDENTITY_VERSION = 5


def _dataset_prompt_identity(
    attestation: dict[str, object],
) -> tuple[int, str]:
    """Recover the exact prompt contract independently bound by attestation."""

    version = attestation.get("prompt_version")
    contract = attestation.get("prompt_contract")
    digest = attestation.get("prompt_contract_sha256")
    try:
        recognized = prompt_version_from_manifest(contract)
    except ValueError as exc:
        raise ValueError(f"dataset prompt attestation is invalid: {exc}") from None
    if (
        version != recognized
        or digest != prompt_contract_sha256(recognized)
        or contract != prompt_manifest_record(recognized)
    ):
        raise ValueError("dataset prompt attestation hash/version mismatch")
    return recognized, str(digest)


def _require_prompt_curriculum_alignment(
    config: ExperimentConfig,
    dataset_attestation: dict[str, object],
) -> None:
    """Prevent a prompt-v3 dataset from escaping the model-v3 gates."""

    prompt_version, _ = _dataset_prompt_identity(dataset_attestation)
    if (prompt_version == PEANO_PROMPT_V3) != (config.curriculum is not None):
        raise ValueError(
            "prompt-v3 dataset identity and model-v3 curriculum must be enabled "
            "together"
        )


def _verify_final_artifact_trees(
    output_dir: Path,
    adapter_artifacts: dict[str, object],
    tokenizer_artifacts: dict[str, object],
    *,
    require_protected: bool,
) -> None:
    """Recheck the exact loader trees at the final-manifest boundary."""

    require_safetensors_adapter(adapter_artifacts)
    verify_artifact_directory(
        output_dir,
        adapter_artifacts,
        ADAPTER_SUBDIR,
        require_protected=require_protected,
    )
    verify_artifact_directory(
        output_dir,
        tokenizer_artifacts,
        TOKENIZER_SUBDIR,
        require_protected=require_protected,
    )


def _repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPOSITORY_ROOT / path


@dataclass(frozen=True, slots=True)
class ResumeDecision:
    trainer_value: str | bool
    checkpoint: str | None
    checkpoint_sha256: str | None
    global_step: int | None


@dataclass(frozen=True, slots=True)
class PreparedExamples:
    """Checked source examples plus the exact authority that admitted them."""

    train: tuple[ProofExample, ...]
    evaluation: tuple[ProofExample, ...]
    dataset_attestation: dict[str, object]
    corpus_eligibility: dict[str, object] | None
    curriculum_attestation: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class PreparedTokenization:
    """Exact model inputs and, for model-v3, their token exposure evidence."""

    train: tuple[dict[str, list[int]], ...]
    evaluation: tuple[dict[str, list[int]], ...]
    tokenized_splits: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class PreparationReports:
    """Exact WMI preparation reports authorized to admit one training job."""

    eligibility: Path
    token_audit: Path
    runtime_smoke: Path
    prepare_job_id: str


def _verify_recovery_filesystem_for_training(
    config: ExperimentConfig,
    report_path: Path | None,
    *,
    output_dir: Path,
    job_identity: dict[str, object],
) -> dict[str, object] | None:
    """Bind a live no-replace publication probe on the training filesystem."""

    scheduled = job_identity.get("scheduler") == "slurm"
    on_wmi = os.environ.get("PEANO_CLUSTER_BACKEND") == "wmi"
    if config.curriculum is None:
        if report_path is not None:
            raise ValueError(
                "recovery publication preflight is valid only for model-v3"
            )
        return None
    if report_path is None:
        if scheduled or on_wmi:
            raise ValueError(
                "scheduled model-v3 training requires a recovery filesystem preflight"
            )
        return None

    report = report_path.resolve()
    record = verify_recovery_publication_preflight(report)
    report_identity = _stable_file_identity(
        report, label="recovery publication preflight report"
    )
    filesystem = record.get("filesystem")
    platform_record = record.get("platform")
    mechanisms = record.get("mechanisms")
    publication_profile = record.get("publication_profile")
    expected_probe_root = (
        output_dir.parent / "recovery-publication-preflights"
    ).resolve()
    if (
        type(filesystem) is not dict
        or Path(str(filesystem.get("root"))).resolve() != expected_probe_root
        or filesystem.get("same_device") is not True
        or type(platform_record) is not dict
        or type(mechanisms) is not dict
        or publication_profile
        not in {NATIVE_PUBLICATION_PROFILE, CLAIM_RENAME_PUBLICATION_PROFILE}
    ):
        raise ValueError(
            "recovery publication preflight is not on the training filesystem"
        )
    try:
        output_parent_device = os.stat(output_dir.parent).st_dev
    except OSError as exc:
        raise ValueError(
            f"cannot inspect training output filesystem: {exc}"
        ) from exc
    if (
        filesystem.get("root_device") != output_parent_device
        or filesystem.get("publication_device") != output_parent_device
    ):
        raise ValueError(
            "recovery publication probe and training output use different devices"
        )
    if scheduled or on_wmi:
        job_id = job_identity.get("job_id")
        expected_name = f"peano-wmi-recovery-publication-preflight-{job_id}.json"
        if (
            type(job_id) is not str
            or not job_id.isdecimal()
            or report.name != expected_name
            or platform_record.get("os_name") != "posix"
            or not str(platform_record.get("sys_platform", "")).startswith("linux")
            or set(mechanisms) != {"directory", "regular_file"}
            or any(
                type(mechanisms.get(kind)) is not dict
                or mechanisms[kind].get("protocol") != publication_profile
                or type(mechanisms[kind].get("native_attempt")) is not dict
                or mechanisms[kind]["native_attempt"].get("syscall") != "renameat2"
                or mechanisms[kind]["native_attempt"].get("flag")
                != "RENAME_NOREPLACE"
                for kind in ("directory", "regular_file")
            )
        ):
            raise ValueError(
                "WMI recovery preflight lacks an exact admitted Linux publication profile"
            )
    return {"report": report_identity, "record": record}


def _require_recovery_filesystem_unchanged(
    verification: dict[str, object] | None,
) -> None:
    """Recheck both canonical report bytes and the retained live probe."""

    if verification is None:
        return
    identity = verification.get("report")
    expected_record = verification.get("record")
    if type(identity) is not dict or type(identity.get("path")) is not str:
        raise RuntimeError("recovery filesystem evidence is malformed")
    report = Path(identity["path"])
    if _stable_file_identity(
        report, label="recovery publication preflight report"
    ) != identity:
        raise RuntimeError("recovery publication preflight report changed")
    if verify_recovery_publication_preflight(report) != expected_record:
        raise RuntimeError("recovery publication probe changed during training")


def _stable_file_identity(path: Path, *, label: str) -> dict[str, object]:
    """Hash one regular, non-symlink file and reject a changing read."""

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuntimeError(f"cannot open {label} {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise RuntimeError(f"{label} is not a regular file: {path}")
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            while block := stream.read(1024 * 1024):
                digest.update(block)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise RuntimeError(f"cannot read {label} {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    projection = lambda value: (  # noqa: E731 - immutable stat projection
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )
    try:
        current = os.lstat(path)
    except OSError as exc:
        raise RuntimeError(f"{label} disappeared while being hashed: {path}") from exc
    if (
        stat.S_ISLNK(current.st_mode)
        or not stat.S_ISREG(current.st_mode)
        or projection(before) != projection(after)
        or projection(before) != projection(current)
    ):
        raise RuntimeError(f"{label} changed while being hashed: {path}")
    return {
        "path": str(path),
        "bytes": before.st_size,
        "sha256": digest.hexdigest(),
    }


def _prepared_source_snapshot(
    config: ExperimentConfig,
    prepared: PreparedExamples,
    *,
    train_path: Path,
    eval_path: Path,
) -> dict[str, object] | None:
    """Join the files actually loaded to seal and selector evidence.

    The seal verifier, curriculum loader, and evaluation loader each perform
    their own closed checks.  This final join prevents a same-owner file swap
    between those checks from making their individually valid records refer to
    different byte snapshots.
    """

    if config.curriculum is None:
        return None
    eligibility = prepared.corpus_eligibility
    curriculum = prepared.curriculum_attestation
    if type(eligibility) is not dict or type(curriculum) is not dict:
        raise RuntimeError("model-v3 preparation lacks source admission evidence")
    train_manifest = dataset_manifest_path(train_path)
    eval_manifest = dataset_manifest_path(eval_path)
    if train_manifest != eval_manifest:
        raise RuntimeError("model-v3 train and evaluation splits need one manifest")
    snapshot = {
        "train": _stable_file_identity(train_path, label="training split"),
        "eval": _stable_file_identity(eval_path, label="evaluation split"),
        "manifest": _stable_file_identity(
            train_manifest, label="dataset manifest"
        ),
    }
    admitted = eligibility.get("inputs")
    selected_source = curriculum.get("source")
    if type(admitted) is not dict or type(selected_source) is not dict:
        raise RuntimeError("model-v3 source evidence is malformed")
    expected_paths = {
        "train": train_path,
        "eval": eval_path,
        "manifest": train_manifest,
    }
    for role, expected_path in expected_paths.items():
        claim = admitted.get(role)
        actual = snapshot[role]
        if (
            type(claim) is not dict
            or claim.get("configured_path") != str(expected_path)
            or claim.get("bytes") != actual["bytes"]
            or claim.get("sha256") != actual["sha256"]
        ):
            raise RuntimeError(
                f"loaded model-v3 {role} differs from corpus eligibility"
            )
    for role, source_role in (("train", "train"), ("manifest", "manifest")):
        selected = selected_source.get(source_role)
        actual = snapshot[role]
        if (
            type(selected) is not dict
            or selected.get("bytes") != actual["bytes"]
            or selected.get("sha256") != actual["sha256"]
        ):
            raise RuntimeError(
                f"loaded model-v3 {role} differs from curriculum selection"
            )
    admitted_train = admitted["train"]
    selected_train = selected_source["train"]
    if selected_train.get("rows") != admitted_train.get("rows"):
        raise RuntimeError("curriculum train row count differs from corpus eligibility")
    return snapshot


def _verify_preparation_reports(
    config: ExperimentConfig,
    reports: PreparationReports | None,
    *,
    job_identity: dict[str, object],
) -> dict[str, object] | None:
    """Re-run and bind the WMI preparation verifier inside training itself."""

    if config.curriculum is None:
        if reports is not None:
            raise ValueError("preparation reports are valid only for model-v3")
        return None
    on_wmi = os.environ.get("PEANO_CLUSTER_BACKEND") == "wmi"
    scheduled = job_identity.get("scheduler") == "slurm"
    if reports is None:
        if on_wmi or scheduled:
            raise ValueError("scheduled model-v3 training requires preparation reports")
        return None
    if not reports.prepare_job_id.isdecimal():
        raise ValueError("preparation job id must be decimal text")
    if on_wmi or scheduled:
        declared = os.environ.get("PEANO_PREPARE_JOB_ID")
        submission = job_identity.get("submission")
        if (
            declared != reports.prepare_job_id
            or type(submission) is not dict
            or submission.get("dependency_job_id") != reports.prepare_job_id
        ):
            raise ValueError(
                "training job dependency differs from its preparation reports"
            )

    # The standard-library verifier is also invoked by the submitter and the
    # batch script.  Calling it here makes the exact reports part of the Python
    # process that will allocate and update the model.
    from scripts.verify_wmi_v3_sealed_preparation import verify_reports

    return verify_reports(
        eligibility_report=reports.eligibility,
        token_audit_report=reports.token_audit,
        smoke_report=reports.runtime_smoke,
        prepare_job_id=reports.prepare_job_id,
        repository_root=REPOSITORY_ROOT,
    )


def _require_preparation_agreement(
    config: ExperimentConfig,
    prepared: PreparedExamples,
    tokenization: PreparedTokenization,
    verification: dict[str, object] | None,
) -> None:
    """Require audited reports to describe the exact in-process curriculum."""

    if verification is None:
        return
    eligibility = prepared.corpus_eligibility
    curriculum = prepared.curriculum_attestation
    tokens = tokenization.tokenized_splits
    if type(eligibility) is not dict or type(curriculum) is not dict or type(tokens) is not dict:
        raise RuntimeError("preparation reports cannot bind incomplete model-v3 evidence")
    train_tokens = tokens.get("train")
    eval_tokens = tokens.get("eval")
    seal = eligibility.get("seal")
    if (
        type(train_tokens) is not dict
        or type(eval_tokens) is not dict
        or type(seal) is not dict
        or verification.get("config_sha256") != sha256_file(config.path)
        or verification.get("corpus_content_sha256") != seal.get("content_sha256")
        or verification.get("corpus_eligibility_sha256")
        != eligibility.get("eligibility_sha256")
        or verification.get("curriculum_sha256")
        != curriculum.get("curriculum_sha256")
        or verification.get("train_token_record_sha256")
        != train_tokens.get("record_sha256")
        or verification.get("eval_token_record_sha256")
        != eval_tokens.get("record_sha256")
    ):
        raise RuntimeError(
            "in-process model-v3 data differs from preparation reports"
        )
    _require_preparation_files_unchanged(verification)


def _require_preparation_files_unchanged(
    verification: dict[str, object] | None,
) -> None:
    """Rehash the three accepted reports against their parsed-byte identities."""

    if verification is None:
        return
    reports = verification.get("reports")
    if type(reports) is not dict or set(reports) != {
        "eligibility",
        "token_audit",
        "runtime_smoke",
    }:
        raise RuntimeError("preparation verification lacks exact report identities")
    for role, expected in reports.items():
        if type(expected) is not dict or type(expected.get("path")) is not str:
            raise RuntimeError(f"preparation {role} report identity is malformed")
        actual = _stable_file_identity(
            Path(expected["path"]), label=f"preparation {role} report"
        )
        if actual != expected:
            raise RuntimeError(f"preparation {role} report changed after verification")


def _prepare_examples(
    config: ExperimentConfig,
    *,
    train_path: Path,
    eval_path: Path,
) -> PreparedExamples:
    """Resolve either legacy replay data or the sealed model-v3 curriculum."""

    curriculum = config.curriculum
    if curriculum is None:
        attestation = attest_dataset(train_path, eval_path)
        train = load_examples(
            train_path,
            max_samples=config.run.max_train_samples,
            seed=config.run.seed,
        )
        evaluation = load_examples(
            eval_path,
            max_samples=config.run.max_eval_samples,
            seed=config.run.seed + 1,
        )
        return PreparedExamples(
            tuple(train),
            tuple(evaluation),
            attestation,
            None,
            None,
        )

    if config.run.max_train_samples is not None:
        raise ValueError("model-v3 curriculum forbids train-row subsampling")
    eligibility = verify_sealed_corpus_eligibility(
        _repo_path(curriculum.corpus_seal_path),
        configured_train_path=train_path,
        configured_eval_path=eval_path,
        historical_source_commit=curriculum.corpus_source_commit,
        historical_prepare_job_id=curriculum.corpus_prepare_job_id,
        sealed_content_sha256=curriculum.corpus_content_sha256,
    )
    selected = load_curriculum(
        train_path,
        seed=str(curriculum.selection_seed),
        synthetic_row_ceiling=curriculum.synthetic_row_ceiling,
    )
    evaluation = load_examples(
        eval_path,
        max_samples=config.run.max_eval_samples,
        seed=config.run.seed + 1,
    )
    return PreparedExamples(
        selected.examples,
        tuple(evaluation),
        eligibility.dataset_attestation,
        eligibility.record,
        selected.attestation,
    )


def _tokenize_prepared_examples(
    config: ExperimentConfig,
    prepared: PreparedExamples,
    tokenizer: Any,
    *,
    resolved_revision: str,
) -> PreparedTokenization:
    """Tokenize the admitted examples and enforce model-v3 exposure ceilings."""

    if not prepared.train:
        raise ValueError("the replay-validated training split is empty")
    if config.curriculum is None:
        # This is deliberately the historical path: legacy experiments retain
        # their exact capped row population and completion tokenizer behavior.
        train = tuple(
            tokenize_completion(
                example, tokenizer, max_length=config.data.max_length
            )
            for example in prepared.train
        )
        evaluation = tuple(
            tokenize_completion(
                example, tokenizer, max_length=config.data.max_length
            )
            for example in prepared.evaluation
        )
        return PreparedTokenization(train, evaluation, None)

    curriculum = config.curriculum
    tokenizer_identity = tokenizer_identity_record(
        tokenizer,
        model_id=config.model.model_id,
        revision=resolved_revision,
    )
    train, train_record = tokenize_split(
        prepared.train,
        tokenizer,
        role="train",
        max_length=config.data.max_length,
        tokenizer_identity=tokenizer_identity,
    )
    evaluation, eval_record = tokenize_split(
        prepared.evaluation,
        tokenizer,
        role="eval",
        max_length=config.data.max_length,
        tokenizer_identity=tokenizer_identity,
    )
    enforce_token_budget(
        train_record,
        max_total_tokens=curriculum.max_train_tokens,
        max_sum_squared_tokens=curriculum.max_train_squared_tokens,
        max_supervised_tokens=config.generation.max_new_tokens,
    )
    enforce_token_budget(
        eval_record,
        max_total_tokens=curriculum.max_eval_tokens,
        max_sum_squared_tokens=curriculum.max_eval_squared_tokens,
        max_supervised_tokens=config.generation.max_new_tokens,
    )
    return PreparedTokenization(
        tuple(train),
        tuple(evaluation),
        {"train": train_record, "eval": eval_record},
    )


def _curriculum_schedule_preflight(
    config: ExperimentConfig,
    *,
    train_rows: int,
    eval_rows: int,
    cuda_device_count: int,
    distributed_process_count: int,
) -> dict[str, object] | None:
    """Reject an accidental multi-pass or periodic-I/O model-v3 schedule.

    The selected curriculum is intentionally a one-GPU experiment.  Fixing
    that topology makes the expected optimizer-step count independently
    computable before ``Trainer`` is constructed.
    """

    if config.curriculum is None:
        return None
    if type(train_rows) is not int or train_rows < 1:
        raise ValueError("model-v3 schedule requires at least one training row")
    if type(eval_rows) is not int or eval_rows < 1:
        raise ValueError("model-v3 schedule requires at least one evaluation row")
    if type(cuda_device_count) is not int or cuda_device_count != 1:
        raise ValueError("model-v3 training requires exactly one visible CUDA device")
    if type(distributed_process_count) is not int or distributed_process_count != 1:
        raise ValueError("model-v3 training requires exactly one distributed process")
    if config.trainer.max_steps != -1:
        raise ValueError("model-v3 training must derive its schedule from epochs")
    if config.trainer.epochs != 1.0:
        raise ValueError("model-v3 training requires exactly one epoch")

    per_device_batch = config.trainer.per_device_train_batch_size
    accumulation = config.trainer.gradient_accumulation_steps
    micro_batches_per_epoch = math.ceil(train_rows / per_device_batch)
    optimizer_steps_per_epoch = math.ceil(micro_batches_per_epoch / accumulation)
    expected_optimizer_steps = math.ceil(
        optimizer_steps_per_epoch * config.trainer.epochs
    )
    if expected_optimizer_steps < 1:
        raise ValueError("model-v3 schedule has no optimizer steps")
    if expected_optimizer_steps % config.trainer.logging_steps != 0:
        raise ValueError(
            "model-v3 optimizer schedule must be divisible by logging_steps"
        )
    if config.trainer.eval_steps <= expected_optimizer_steps:
        raise ValueError(
            "model-v3 eval_steps must exceed the complete optimizer schedule"
        )
    if config.trainer.save_steps <= expected_optimizer_steps:
        raise ValueError(
            "model-v3 save_steps must exceed the complete optimizer schedule"
        )

    return {
        "format": "peano-policy-v3-training-schedule",
        "v": 1,
        "train_rows": train_rows,
        "eval_rows": eval_rows,
        "cuda_devices": cuda_device_count,
        "distributed_processes": distributed_process_count,
        "epochs": config.trainer.epochs,
        "per_device_train_batch_size": per_device_batch,
        "gradient_accumulation_steps": accumulation,
        "effective_train_batch_size": per_device_batch * accumulation,
        "micro_batches_per_epoch": micro_batches_per_epoch,
        "optimizer_steps_per_epoch": optimizer_steps_per_epoch,
        "expected_optimizer_steps": expected_optimizer_steps,
        "eval_steps": config.trainer.eval_steps,
        "save_steps": config.trainer.save_steps,
        "periodic_evaluations": 0,
        "periodic_checkpoints": 0,
        # These are intentionally not Trainer checkpoints: only PEFT adapter
        # safetensors are persisted, and no resume state exists.
        "adapter_recovery": recovery_snapshot_plan(expected_optimizer_steps),
    }


def _declared_process_count() -> int:
    """Resolve scheduler/launcher process declarations without initializing it."""

    declarations: dict[str, int] = {}
    for name in ("WORLD_SIZE", "LOCAL_WORLD_SIZE", "SLURM_NTASKS"):
        raw = os.environ.get(name)
        if raw is None:
            continue
        if not raw.isdecimal() or int(raw) < 1:
            raise ValueError(f"{name} must be a positive decimal process count")
        declarations[name] = int(raw)
    if len(set(declarations.values())) > 1:
        raise ValueError("distributed process declarations disagree")
    return next(iter(declarations.values()), 1)


def _require_fresh_one_shot_output(output_dir: Path, requested: str) -> None:
    """Reject a one-shot retry before attestation or any filesystem mutation."""

    if requested != "never" or not os.path.lexists(output_dir):
        return
    if not output_dir.is_dir() or output_dir.is_symlink():
        raise ValueError("resume='never' requires a fresh output directory")
    existing = sorted(entry.name for entry in output_dir.iterdir())
    detail = ", ".join(existing) if existing else "an existing empty directory"
    raise ValueError(
        "resume='never' requires a fresh output directory; found: " + detail
    )


def _claim_fresh_output_directory(output_dir: Path) -> dict[str, object]:
    """Create and bind the one output inode used by a model-v3 run."""

    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    try:
        parent_before = os.lstat(parent)
    except OSError as exc:
        raise RuntimeError(f"cannot inspect training output parent: {exc}") from exc
    if stat.S_ISLNK(parent_before.st_mode) or not stat.S_ISDIR(
        parent_before.st_mode
    ):
        raise RuntimeError("training output parent is not a safe directory")
    try:
        output_dir.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as exc:
        raise RuntimeError(
            f"refusing to reuse training output directory {output_dir}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"cannot create training output directory: {exc}") from exc
    metadata = os.lstat(output_dir)
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_dev != parent_before.st_dev
    ):
        raise RuntimeError("training output directory has an unsafe identity")
    parent_after = os.lstat(parent)
    if (
        stat.S_ISLNK(parent_after.st_mode)
        or not stat.S_ISDIR(parent_after.st_mode)
        or (parent_after.st_dev, parent_after.st_ino)
        != (parent_before.st_dev, parent_before.st_ino)
    ):
        raise RuntimeError("training output parent changed during creation")
    return {
        "path": str(output_dir),
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "mode": oct(stat.S_IMODE(metadata.st_mode)),
        "parent": str(parent),
        "parent_device": parent_after.st_dev,
        "parent_inode": parent_after.st_ino,
    }


def _require_output_directory_unchanged(identity: dict[str, object]) -> None:
    """Reject a path, mount, inode, or permission swap of the claimed output."""

    expected = {
        "path",
        "device",
        "inode",
        "mode",
        "parent",
        "parent_device",
        "parent_inode",
    }
    if type(identity) is not dict or set(identity) != expected:
        raise RuntimeError("training output-directory identity is malformed")
    path = Path(str(identity["path"]))
    parent = Path(str(identity["parent"]))
    try:
        metadata = os.lstat(path)
        parent_metadata = os.lstat(parent)
    except OSError as exc:
        raise RuntimeError(f"training output directory disappeared: {exc}") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_dev != identity["device"]
        or metadata.st_ino != identity["inode"]
        or oct(stat.S_IMODE(metadata.st_mode)) != identity["mode"]
        or stat.S_ISLNK(parent_metadata.st_mode)
        or not stat.S_ISDIR(parent_metadata.st_mode)
        or parent_metadata.st_dev != identity["parent_device"]
        or parent_metadata.st_ino != identity["parent_inode"]
    ):
        raise RuntimeError("training output directory changed during the run")


def _run_identity(
    config: ExperimentConfig,
    *,
    train_path: Path,
    eval_path: Path,
    dataset_attestation: dict[str, object],
    deployment: dict[str, object],
    corpus_eligibility: dict[str, object] | None = None,
    curriculum_attestation: dict[str, object] | None = None,
    tokenized_splits: dict[str, object] | None = None,
    schedule_preflight: dict[str, object] | None = None,
    source_snapshot: dict[str, object] | None = None,
    preparation_verification: dict[str, object] | None = None,
    recovery_filesystem_verification: dict[str, object] | None = None,
    output_directory_identity: dict[str, object] | None = None,
    job_identity: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Identity that every checkpoint in an output directory must share."""

    train_manifest = dataset_manifest_path(train_path)
    eval_manifest = dataset_manifest_path(eval_path)
    prompt_version, prompt_digest = _dataset_prompt_identity(dataset_attestation)
    return {
        "v": RUN_IDENTITY_VERSION,
        "config": {
            "path": str(config.path),
            "sha256": sha256_file(config.path),
            "resolved": {
                "run": asdict(config.run),
                "model": asdict(config.model),
                "data": asdict(config.data),
                "lora": asdict(config.lora),
                "trainer": asdict(config.trainer),
                "generation": asdict(config.generation),
                "curriculum": (
                    None
                    if config.curriculum is None
                    else asdict(config.curriculum)
                ),
            },
        },
        "model": {
            "id": config.model.model_id,
            "revision": config.model.revision,
        },
        "prompt_version": prompt_version,
        "prompt_contract_sha256": prompt_digest,
        "objective": completion_objective_record(),
        "inputs": {
            "train": sha256_file(train_path),
            "eval": sha256_file(eval_path),
            "train_manifest": sha256_file(train_manifest),
            "eval_manifest": sha256_file(eval_manifest),
            "dataset_attestation": dataset_attestation,
            "corpus_eligibility": corpus_eligibility,
            "curriculum_attestation": curriculum_attestation,
            "tokenized_splits": tokenized_splits,
            "schedule_preflight": schedule_preflight,
            "source_snapshot": source_snapshot,
            "preparation_verification": preparation_verification,
            "recovery_filesystem_verification": (
                recovery_filesystem_verification
            ),
        },
        "source": source_hash(SOURCE_ROOT),
        "deployment": deployment,
        "output_directory": output_directory_identity,
        "job": job_identity,
    }


def _ensure_run_identity(
    output_dir: Path,
    identity: dict[str, Any],
    *,
    publication_profile: str | None = None,
) -> tuple[Path, str]:
    path = output_dir / "run-identity.json"
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot validate existing run identity: {exc}") from None
        if existing != identity:
            raise ValueError(
                "output directory belongs to a different training identity"
            )
    else:
        write_manifest_noreplace(
            path,
            identity,
            publication_profile=publication_profile,
        )
    return path, sha256_file(path)


def _checkpoint_step(path: Path) -> int:
    state_path = path / "trainer_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read checkpoint trainer state {state_path}: {exc}") from None
    step = state.get("global_step") if isinstance(state, dict) else None
    if type(step) is not int or step < 0:
        raise ValueError(f"checkpoint has no valid global_step: {state_path}")
    return step


def _resume_decision(
    output_dir: Path,
    requested: str,
    get_last_checkpoint: Any,
    *,
    run_identity_sha256: str,
) -> ResumeDecision:
    if requested == "never":
        unexpected = (
            sorted(
                entry.name
                for entry in output_dir.iterdir()
                if entry.name != "run-identity.json"
            )
            if output_dir.is_dir()
            else []
        )
        if unexpected:
            raise ValueError(
                "resume='never' requires a fresh output directory; found: "
                + ", ".join(unexpected)
            )
        return ResumeDecision(False, None, None, None)
    candidate = (
        get_last_checkpoint(str(output_dir))
        if requested == "auto" and output_dir.is_dir()
        else requested
    )
    if not candidate:
        return ResumeDecision(False, None, None, None)
    checkpoint = _repo_path(str(candidate)).resolve()
    if not checkpoint.is_dir():
        raise FileNotFoundError(f"checkpoint does not exist: {checkpoint}")
    checkpoint_identity = checkpoint.parent / "run-identity.json"
    if (
        not checkpoint_identity.is_file()
        or sha256_file(checkpoint_identity) != run_identity_sha256
    ):
        raise ValueError(
            "checkpoint training identity does not match the requested run"
        )
    checkpoint_artifacts = source_hash(checkpoint)
    return ResumeDecision(
        str(checkpoint),
        str(checkpoint),
        str(checkpoint_artifacts["sha256"]),
        _checkpoint_step(checkpoint),
    )


def _set_seeds(seed: int, torch: Any, transformers_set_seed: Any) -> None:
    if os.environ.get("PYTHONHASHSEED") != str(seed):
        raise RuntimeError(
            f"launch training with PYTHONHASHSEED={seed}; setting it after "
            "interpreter startup is ineffective"
        )
    random.seed(seed)
    try:
        import numpy
    except ImportError:
        numpy = None
    if numpy is not None:
        numpy.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    transformers_set_seed(seed)


class _CompletionCollator:
    """Right-pad ids/masks while preserving the completion-only label mask."""

    def __init__(self, torch: Any, pad_token_id: int) -> None:
        self._torch = torch
        self._pad_token_id = pad_token_id

    def __call__(self, features: list[dict[str, list[int]]]) -> dict[str, Any]:
        width = max(len(feature["input_ids"]) for feature in features)

        def padded(name: str, fill: int) -> list[list[int]]:
            return [
                feature[name] + [fill] * (width - len(feature[name]))
                for feature in features
            ]

        return {
            "input_ids": self._torch.tensor(
                padded("input_ids", self._pad_token_id), dtype=self._torch.long
            ),
            "attention_mask": self._torch.tensor(
                padded("attention_mask", 0), dtype=self._torch.long
            ),
            "labels": self._torch.tensor(
                padded("labels", IGNORE_INDEX), dtype=self._torch.long
            ),
        }


@dataclass(frozen=True, slots=True)
class _TensorPopulationSnapshot:
    """Content identity for one stable trainable-parameter population."""

    names: tuple[str, ...]
    record_hashes: tuple[tuple[str, str], ...]
    population_sha256: str


def _trainable_tensor_population_snapshot(
    torch: Any,
    named_parameters: list[tuple[str, Any]],
) -> _TensorPopulationSnapshot:
    """Hash name, dtype, shape, and every raw byte of each finite tensor.

    The resulting aggregate implements
    ``TENSOR_POPULATION_FINGERPRINT_FORMAT``.  Only compact record hashes are
    retained in memory, so comparing the initial and final snapshots does not
    preserve a second copy of the adapter tensors for the duration of training.
    """

    if not named_parameters:
        raise TrainingEvidenceError(
            "tensor-population fingerprint needs trainable parameters"
        )
    by_name: dict[str, Any] = {}
    for name, parameter in named_parameters:
        if type(name) is not str or not name or name in by_name:
            raise TrainingEvidenceError(
                "trainable tensor names must be unique non-empty strings"
            )
        if not torch.is_tensor(parameter):
            raise TrainingEvidenceError(
                f"trainable parameter {name!r} is not a tensor"
            )
        if not bool(torch.isfinite(parameter.detach()).all().cpu()):
            raise TrainingEvidenceError(
                f"trainable parameter {name!r} contains a non-finite value"
            )
        by_name[name] = parameter

    records: list[dict[str, object]] = []
    record_hashes: list[tuple[str, str]] = []
    for name in sorted(by_name):
        tensor = by_name[name].detach().contiguous()
        raw = tensor.view(torch.uint8).cpu().numpy()
        content_sha256 = hashlib.sha256(raw).hexdigest()
        record = {
            "name": name,
            "dtype": str(tensor.dtype),
            "shape": list(tensor.shape),
            "content_sha256": content_sha256,
        }
        records.append(record)
        record_hashes.append((name, sha256_json(record)))
    names = tuple(record["name"] for record in records)
    if TENSOR_POPULATION_FINGERPRINT_FORMAT != (
        "sha256-canonical-json-sorted-name-dtype-shape-content-sha256-records-v1"
    ):
        raise TrainingEvidenceError(
            "tensor-population fingerprint contract changed without runner support"
        )
    return _TensorPopulationSnapshot(
        names=names,
        record_hashes=tuple(record_hashes),
        population_sha256=sha256_json(records),
    )


class _FiniteGradientCallbackMixin:
    """Audit raw gradients, apply the only clip, then audit optimizer inputs."""

    def __init__(
        self,
        *,
        torch: Any,
        named_parameters: list[tuple[str, Any]],
        audit: FiniteGradientAudit,
    ) -> None:
        self._torch = torch
        self._named_parameters = tuple(named_parameters)
        self.audit = audit

    def _finite_gradient_names(self, *, boundary: str) -> tuple[str, ...]:
        missing = [
            name
            for name, parameter in self._named_parameters
            if parameter.grad is None
        ]
        if missing:
            preview = ", ".join(missing[:5])
            raise TrainingEvidenceError(
                f"{boundary} has {len(missing)} missing trainable gradients: "
                f"{preview}"
            )
        nonfinite = [
            name
            for name, parameter in self._named_parameters
            if not bool(
                self._torch.isfinite(parameter.grad).all().detach().cpu()
            )
        ]
        if nonfinite:
            preview = ", ".join(nonfinite[:5])
            raise TrainingEvidenceError(
                f"{boundary} has {len(nonfinite)} non-finite gradients: {preview}"
            )
        return tuple(name for name, _ in self._named_parameters)

    def on_pre_optimizer_step(
        self,
        args: object,
        state: object,
        control: object,
        **kwargs: object,
    ) -> object:
        del args
        if getattr(state, "is_world_process_zero", None) is not True:
            raise TrainingEvidenceError(
                "finite-gradient audit requires the reviewed one-process Trainer"
            )
        callback_model = kwargs.get("model")
        if callback_model is None:
            raise TrainingEvidenceError(
                "finite-gradient callback did not receive the Trainer model"
            )
        live = tuple(
            (name, parameter)
            for name, parameter in callback_model.named_parameters()
            if parameter.requires_grad
        )
        if len(live) != len(self._named_parameters) or any(
            live_name != expected_name or live_parameter is not expected_parameter
            for (live_name, live_parameter), (expected_name, expected_parameter)
            in zip(live, self._named_parameters, strict=True)
        ):
            raise TrainingEvidenceError(
                "Trainer changed the trainable parameter population"
            )
        raw_names = self._finite_gradient_names(boundary="raw gradient boundary")
        parameters = [parameter for _, parameter in self._named_parameters]
        try:
            norm = self._torch.nn.utils.clip_grad_norm_(
                parameters,
                max_norm=CUSTOM_GRADIENT_CLIP_MAX_NORM,
                error_if_nonfinite=True,
            )
        except RuntimeError as exc:
            raise TrainingEvidenceError(
                "strict custom gradient clipping rejected the global norm"
            ) from exc
        norm_value = (
            float(norm.detach().float().cpu())
            if self._torch.is_tensor(norm)
            else float(norm)
        )
        if not math.isfinite(norm_value) or norm_value < 0.0:
            raise TrainingEvidenceError(
                "custom pre-clip global gradient norm is non-finite"
            )
        post_names = self._finite_gradient_names(
            boundary="post-clip gradient boundary"
        )
        global_step = getattr(state, "global_step", None)
        self.audit.observe_pre_optimizer_step(
            trainer_state_global_step=global_step,
            raw_finite_gradient_parameter_names=raw_names,
            pre_clip_global_norm=norm_value,
            post_clip_finite_gradient_parameter_names=post_names,
        )
        return control


def train(
    config: ExperimentConfig,
    *,
    resume_override: str | None = None,
    preparation_reports: PreparationReports | None = None,
    recovery_publication_preflight_report: Path | None = None,
) -> Path:
    """Run one adapter experiment and return its provenance manifest path."""

    output_dir = _repo_path(config.run.output_dir)
    train_path = _repo_path(config.data.train_path)
    eval_path = _repo_path(config.data.eval_path)
    resume_requested = resume_override or config.run.resume
    _require_fresh_one_shot_output(output_dir, resume_requested)
    deployment = deployment_identity()
    job_identity = slurm_job_identity()
    if job_identity.get("deployment") != deployment:
        raise RuntimeError("Slurm and run deployment identities disagree")
    recovery_filesystem_verification = _verify_recovery_filesystem_for_training(
        config,
        recovery_publication_preflight_report,
        output_dir=output_dir,
        job_identity=job_identity,
    )
    publication_profile: str | None = None
    if recovery_filesystem_verification is not None:
        recovery_record = recovery_filesystem_verification.get("record")
        candidate_profile = (
            recovery_record.get("publication_profile")
            if type(recovery_record) is dict
            else None
        )
        if candidate_profile not in {
            NATIVE_PUBLICATION_PROFILE,
            CLAIM_RENAME_PUBLICATION_PROFILE,
        }:
            raise RuntimeError(
                "verified recovery filesystem has no admitted publication profile"
            )
        publication_profile = candidate_profile
    preparation_verification = _verify_preparation_reports(
        config,
        preparation_reports,
        job_identity=job_identity,
    )
    prepared = _prepare_examples(
        config,
        train_path=train_path,
        eval_path=eval_path,
    )
    source_snapshot = _prepared_source_snapshot(
        config,
        prepared,
        train_path=train_path,
        eval_path=eval_path,
    )
    dataset_attestation = prepared.dataset_attestation
    _require_prompt_curriculum_alignment(config, dataset_attestation)

    # Kept lazy so static/data tooling never initializes CUDA or imports torch.
    import torch
    from peft import LoraConfig as PeftLoraConfig, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainerCallback,
        TrainingArguments,
        set_seed,
    )
    from transformers.trainer_utils import get_last_checkpoint

    class CompletionOnlyTrainer(CompletionOnlyTrainerMixin, Trainer):
        """Pinned Trainer implementation for completion-only indexed logits."""

    class AdapterRecoveryCallback(
        AdapterRecoveryCallbackMixin, TrainerCallback
    ):
        """Persist non-resumable adapter evidence after audited optimizer steps."""

    class FiniteGradientCallback(
        _FiniteGradientCallbackMixin, TrainerCallback
    ):
        """Own the raw-gradient audit and the run's only gradient clipping."""

    _set_seeds(config.run.seed, torch, set_seed)

    schedule_preflight = _curriculum_schedule_preflight(
        config,
        train_rows=len(prepared.train),
        eval_rows=len(prepared.evaluation),
        cuda_device_count=torch.cuda.device_count(),
        distributed_process_count=(
            _declared_process_count() if config.curriculum is not None else 1
        ),
    )

    tokenizer = AutoTokenizer.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        use_fast=True,
        trust_remote_code=config.model.trust_remote_code,
    )
    if tokenizer.eos_token_id is None:
        raise RuntimeError("base tokenizer has no EOS token")
    tokenizer_commit = (
        tokenizer.init_kwargs.get("_commit_hash") or config.model.revision
    )
    if tokenizer_commit != config.model.revision:
        raise RuntimeError(
            "resolved tokenizer snapshot differs from the pinned model revision"
        )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    tokenization = _tokenize_prepared_examples(
        config,
        prepared,
        tokenizer,
        resolved_revision=tokenizer_commit,
    )
    _require_preparation_agreement(
        config,
        prepared,
        tokenization,
        preparation_verification,
    )

    # The model-v3 identity is written only after every source, selection,
    # token, and schedule gate has passed, but still before allocating model
    # weights.  Legacy identities retain explicit nulls for the new evidence.
    output_directory_identity: dict[str, object] | None = None
    if schedule_preflight is not None:
        output_directory_identity = _claim_fresh_output_directory(output_dir)
        if recovery_filesystem_verification is not None:
            recovery_record = recovery_filesystem_verification.get("record")
            recovery_filesystem = (
                recovery_record.get("filesystem")
                if type(recovery_record) is dict
                else None
            )
            if (
                type(recovery_filesystem) is not dict
                or recovery_filesystem.get("publication_device")
                != output_directory_identity["device"]
            ):
                raise RuntimeError(
                    "claimed output and recovery publication use different devices"
                )
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    run_identity = _run_identity(
        config,
        train_path=train_path,
        eval_path=eval_path,
        dataset_attestation=dataset_attestation,
        deployment=deployment,
        corpus_eligibility=prepared.corpus_eligibility,
        curriculum_attestation=prepared.curriculum_attestation,
        tokenized_splits=tokenization.tokenized_splits,
        schedule_preflight=schedule_preflight,
        source_snapshot=source_snapshot,
        preparation_verification=preparation_verification,
        recovery_filesystem_verification=recovery_filesystem_verification,
        output_directory_identity=output_directory_identity,
        job_identity=job_identity,
    )
    run_identity_path, run_identity_sha256 = _ensure_run_identity(
        output_dir,
        run_identity,
        publication_profile=publication_profile,
    )
    admission_probe_plan = (
        select_admission_probes(
            admitted_train_examples=prepared.train,
            admitted_train_features=tokenization.train,
            admitted_evaluation_examples=prepared.evaluation,
            admitted_evaluation_features=tokenization.evaluation,
            max_length=config.data.max_length,
            selection_binding_sha256=run_identity_sha256,
        )
        if schedule_preflight is not None
        else None
    )
    early_resume = (
        _resume_decision(
            output_dir,
            "never",
            lambda _: None,
            run_identity_sha256=run_identity_sha256,
        )
        if resume_requested == "never"
        else None
    )

    model = AutoModelForCausalLM.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        torch_dtype=torch.bfloat16,
        attn_implementation=config.model.attn_implementation,
        trust_remote_code=config.model.trust_remote_code,
        use_safetensors=True,
    )
    require_indexed_logits_support(model)
    model_commit = getattr(model.config, "_commit_hash", None) or config.model.revision
    if model_commit != config.model.revision:
        raise RuntimeError(
            "resolved model snapshot differs from the pinned model revision"
        )
    model_config = model.config.to_dict()
    model.config.use_cache = False
    if config.trainer.gradient_checkpointing:
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False}
        )
        model.enable_input_require_grads()
    model = get_peft_model(
        model,
        PeftLoraConfig(
            r=config.lora.rank,
            lora_alpha=config.lora.alpha,
            lora_dropout=config.lora.dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=list(config.lora.target_modules),
        ),
    )

    named_trainable = [
        (name, parameter)
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    ]
    finite_gradient_audit: FiniteGradientAudit | None = None
    initial_tensor_population: _TensorPopulationSnapshot | None = None
    final_tensor_population: _TensorPopulationSnapshot | None = None
    if schedule_preflight is not None:
        initial_tensor_population = _trainable_tensor_population_snapshot(
            torch, named_trainable
        )
        finite_gradient_audit = FiniteGradientAudit(
            expected_optimizer_steps=schedule_preflight[
                "expected_optimizer_steps"
            ],
            trainable_parameter_names=initial_tensor_population.names,
        )

    train_examples = prepared.train
    eval_examples = prepared.evaluation
    train_dataset = list(tokenization.train)
    eval_dataset = list(tokenization.evaluation)
    callbacks: list[TrainerCallback] = []
    if schedule_preflight is not None:
        if finite_gradient_audit is None:
            raise RuntimeError("model-v3 finite-gradient audit was not initialized")
        callbacks.append(
            FiniteGradientCallback(
                torch=torch,
                named_parameters=named_trainable,
                audit=finite_gradient_audit,
            )
        )
        callbacks.append(
            AdapterRecoveryCallback(
                AdapterRecoverySnapshotter(
                    output_dir=output_dir,
                    run_identity_path=run_identity_path,
                    run_identity_sha256=run_identity_sha256,
                    run_identity=run_identity,
                    expected_optimizer_steps=schedule_preflight[
                        "expected_optimizer_steps"
                    ],
                    publication_profile=publication_profile,
                )
            )
        )

    arguments = TrainingArguments(
        output_dir=str(output_dir),
        overwrite_output_dir=False,
        do_train=True,
        do_eval=bool(eval_examples),
        num_train_epochs=config.trainer.epochs,
        max_steps=config.trainer.max_steps,
        per_device_train_batch_size=config.trainer.per_device_train_batch_size,
        per_device_eval_batch_size=config.trainer.per_device_eval_batch_size,
        gradient_accumulation_steps=config.trainer.gradient_accumulation_steps,
        learning_rate=config.trainer.learning_rate,
        weight_decay=config.trainer.weight_decay,
        warmup_ratio=config.trainer.warmup_ratio,
        lr_scheduler_type="cosine",
        optim="adamw_torch_fused",
        adam_beta1=0.9,
        adam_beta2=0.999,
        adam_epsilon=1e-8,
        bf16=True,
        # ``bf16_full_eval`` calls ``model.to(dtype=bfloat16)`` outside the
        # training loop in Transformers 4.53.3.  PEFT keeps LoRA weights in
        # FP32 by default, so enabling it would mutate the learned adapter
        # after its final fingerprint/save.  Normal BF16 autocast already
        # covers evaluation without changing the parameter population.
        bf16_full_eval=False,
        tf32=True,
        gradient_checkpointing=config.trainer.gradient_checkpointing,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        # Model-v3 disables Trainer's earlier, non-strict clipping.  Its first
        # callback audits raw gradients, strictly clips to 1.0, then audits the
        # exact gradients passed to fused AdamW.  Legacy runs retain Trainer's
        # historical built-in clipping behavior.
        max_grad_norm=(0.0 if schedule_preflight is not None else 1.0),
        logging_steps=config.trainer.logging_steps,
        logging_nan_inf_filter=False,
        # Evaluation is an explicit full pass after the learned adapter is
        # saved.  Periodic Trainer callbacks are outside the one-shot schedule.
        eval_strategy="no",
        eval_steps=config.trainer.eval_steps,
        # DefaultFlow requests a final checkpoint at max_steps even when
        # save_steps exceeds the run.  Disable Trainer checkpoints completely:
        # reviewed adapter-only recovery and final safetensors saves live below.
        save_strategy="no",
        save_steps=config.trainer.save_steps,
        save_total_limit=config.trainer.save_total_limit,
        save_safetensors=True,
        report_to=[],
        seed=config.run.seed,
        data_seed=config.run.seed,
        dataloader_num_workers=0,
        remove_unused_columns=False,
        prediction_loss_only=True,
        label_names=["labels"],
        average_tokens_across_devices=True,
    )
    trainer = CompletionOnlyTrainer(
        model=model,
        args=arguments,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset or None,
        data_collator=_CompletionCollator(torch, tokenizer.pad_token_id),
        callbacks=callbacks,
    )
    trainer_runtime = single_process_trainer_runtime_record(
        trainer,
        expected_gradient_accumulation_steps=(
            config.trainer.gradient_accumulation_steps
        ),
    )
    trainer_arguments = (
        reviewed_trainer_arguments_record(trainer)
        if schedule_preflight is not None
        else None
    )
    resume = early_resume or _resume_decision(
        output_dir,
        resume_requested,
        get_last_checkpoint,
        run_identity_sha256=run_identity_sha256,
    )
    train_result = trainer.train(resume_from_checkpoint=resume.trainer_value)
    if (
        schedule_preflight is not None
        and train_result.global_step
        != schedule_preflight["expected_optimizer_steps"]
    ):
        raise RuntimeError(
            "Trainer optimizer-step count differs from the audited model-v3 "
            "schedule"
        )
    adapter_update: dict[str, object] | None = None
    if schedule_preflight is not None:
        if initial_tensor_population is None or finite_gradient_audit is None:
            raise RuntimeError("model-v3 update evidence was not initialized")
        # Finalizing the callback audit here also proves that no nominal
        # Trainer step bypassed the raw/post-clip gradient boundary.
        finite_gradient_audit.record()
        final_tensor_population = _trainable_tensor_population_snapshot(
            torch, named_trainable
        )
        if final_tensor_population.names != initial_tensor_population.names:
            raise TrainingEvidenceError(
                "trainable tensor population changed during training"
            )
        initial_records = dict(initial_tensor_population.record_hashes)
        final_records = dict(final_tensor_population.record_hashes)
        changed_names = tuple(
            name
            for name in final_tensor_population.names
            if final_records[name] != initial_records[name]
        )
        adapter_update = adapter_update_audit_record(
            trainable_parameter_names=final_tensor_population.names,
            initial_tensor_population_sha256=(
                initial_tensor_population.population_sha256
            ),
            final_tensor_population_sha256=(
                final_tensor_population.population_sha256
            ),
            changed_parameter_names=changed_names,
            final_finite_parameter_names=final_tensor_population.names,
        )
    adapter_output = output_dir / ADAPTER_SUBDIR
    tokenizer_output = output_dir / TOKENIZER_SUBDIR
    for artifact_path in (adapter_output, tokenizer_output):
        if os.path.lexists(artifact_path):
            raise RuntimeError(
                f"refusing to replace final training artifact {artifact_path}"
            )
    # Preserve the completed optimizer result before the explicit full
    # validation pass.  Trainer checkpointing is disabled because it would add
    # optimizer/scheduler/RNG state; only reviewed adapter safetensors persist.
    adapter_staging = Path(
        tempfile.mkdtemp(prefix=f".{ADAPTER_SUBDIR}.partial-", dir=output_dir)
    )
    model.save_pretrained(adapter_staging, safe_serialization=True)
    publish_staged_directory_noreplace(
        adapter_staging,
        adapter_output,
        publication_profile=publication_profile,
    )
    tokenizer_staging = Path(
        tempfile.mkdtemp(prefix=f".{TOKENIZER_SUBDIR}.partial-", dir=output_dir)
    )
    tokenizer.save_pretrained(str(tokenizer_staging))
    publish_staged_directory_noreplace(
        tokenizer_staging,
        tokenizer_output,
        publication_profile=publication_profile,
    )
    if schedule_preflight is not None:
        if final_tensor_population is None:
            raise RuntimeError("model-v3 final tensor fingerprint is missing")
        post_serialization_tensor_population = (
            _trainable_tensor_population_snapshot(torch, named_trainable)
        )
        if post_serialization_tensor_population != final_tensor_population:
            raise TrainingEvidenceError(
                "final artifact serialization changed the learned adapter population"
            )
    eval_metrics = trainer.evaluate() if eval_examples else {}
    if schedule_preflight is not None:
        post_evaluation_tensor_population = (
            _trainable_tensor_population_snapshot(torch, named_trainable)
        )
        if post_evaluation_tensor_population != final_tensor_population:
            raise TrainingEvidenceError(
                "explicit evaluation changed the learned adapter population"
            )
        model = restore_model_for_adapter_admission(
            trainer=trainer,
            model=model,
        )

    tokenizer_identity = {
        "class": type(tokenizer).__name__,
        "commit": tokenizer_commit,
        "special_tokens": tokenizer.special_tokens_map,
        "vocab_size": len(tokenizer),
    }
    adapter_artifacts = artifact_directory_hash(
        output_dir,
        ADAPTER_SUBDIR,
        require_protected=(schedule_preflight is not None),
    )
    tokenizer_artifacts = artifact_directory_hash(
        output_dir,
        TOKENIZER_SUBDIR,
        require_protected=(schedule_preflight is not None),
    )
    require_safetensors_adapter(adapter_artifacts)
    prompt_version, prompt_digest = _dataset_prompt_identity(dataset_attestation)
    metrics_record = {
        "train": train_result.metrics,
        "eval": eval_metrics,
        "train_examples": len(train_examples),
        "eval_examples": len(eval_examples),
        "expected_optimizer_steps": (
            None
            if schedule_preflight is None
            else schedule_preflight["expected_optimizer_steps"]
        ),
        "actual_optimizer_steps": train_result.global_step,
    }
    training_evidence: dict[str, object] | None = None
    if schedule_preflight is not None:
        if (
            trainer_arguments is None
            or finite_gradient_audit is None
            or adapter_update is None
        ):
            raise RuntimeError("model-v3 completed-training evidence is incomplete")
        training_evidence = completed_training_evidence_record(
            top_level_metrics=metrics_record,
            train_result_global_step=train_result.global_step,
            trainer_state_global_step=trainer.state.global_step,
            trainer_state_max_steps=trainer.state.max_steps,
            trainer_runtime=trainer_runtime,
            trainer_arguments=trainer_arguments,
            finite_gradient_audit=finite_gradient_audit.record(),
            adapter_update=adapter_update,
            logging_steps=config.trainer.logging_steps,
            log_history=trainer.state.log_history,
            adapter_sha256=adapter_artifacts["sha256"],
            tokenizer_sha256=tokenizer_artifacts["sha256"],
        )
    adapter_admission: dict[str, object] | None = None
    if schedule_preflight is not None:
        if admission_probe_plan is None:
            raise RuntimeError("model-v3 adapter-admission probes are missing")
        base_reload_contract = BaseReloadContract(
            model_id=config.model.model_id,
            revision=model_commit,
            config_sha256=sha256_json(model_config),
            dtype=config.model.dtype,
            attention=config.model.attn_implementation,
            trust_remote_code=config.model.trust_remote_code,
        )
        in_memory_policy = capture_in_memory_policy(
            model=model,
            tokenizer=tokenizer,
            plan=admission_probe_plan,
            base_contract=base_reload_contract,
            torch_module=torch,
            device="cuda:0",
        )

        # The reload phase must not be able to reuse the Trainer, optimizer, or
        # original model through an accidental Python reference.  Only compact
        # hashes and ordinary evidence records cross this boundary.
        del callbacks, named_trainable, trainer, model, tokenizer
        gc.collect()
        torch.cuda.empty_cache()
        adapter_admission = admit_saved_adapter(
            output_dir=output_dir,
            adapter_artifacts=adapter_artifacts,
            tokenizer_artifacts=tokenizer_artifacts,
            plan=admission_probe_plan,
            snapshot=in_memory_policy,
            base_contract=base_reload_contract,
            device="cuda:0",
        )

    # A sync while a job is running must not let imported old code masquerade
    # as newly hashed source.  Recheck every identity-bearing input after the
    # fresh adapter reload and immediately before publishing the final manifest.
    current_source = source_hash(SOURCE_ROOT)
    if current_source != run_identity["source"]:
        raise RuntimeError("training source changed while the run was active")
    if deployment_identity() != deployment:
        raise RuntimeError("source deployment changed while the run was active")
    if slurm_job_identity() != job_identity:
        raise RuntimeError("Slurm job identity changed while the run was active")
    if (
        sha256_file(config.path) != run_identity["config"]["sha256"]
        or sha256_file(train_path) != run_identity["inputs"]["train"]
        or sha256_file(eval_path) != run_identity["inputs"]["eval"]
        or sha256_file(dataset_manifest_path(train_path))
        != run_identity["inputs"]["train_manifest"]
        or sha256_file(dataset_manifest_path(eval_path))
        != run_identity["inputs"]["eval_manifest"]
    ):
        raise RuntimeError("training configuration or dataset changed during the run")
    if (
        _prepared_source_snapshot(
            config,
            prepared,
            train_path=train_path,
            eval_path=eval_path,
        )
        != source_snapshot
    ):
        raise RuntimeError("model-v3 source snapshot changed during the run")
    _require_preparation_files_unchanged(preparation_verification)
    _require_recovery_filesystem_unchanged(recovery_filesystem_verification)
    if output_directory_identity is not None:
        _require_output_directory_unchanged(output_directory_identity)

    manifest = {
        "v": MANIFEST_VERSION,
        "prompt_version": prompt_version,
        "prompt_contract_sha256": prompt_digest,
        "objective": run_identity["objective"],
        "run": asdict(config.run),
        "curriculum": (
            None if config.curriculum is None else asdict(config.curriculum)
        ),
        "generation": asdict(config.generation),
        "base_model": {
            "id": config.model.model_id,
            "requested_revision": config.model.revision,
            "resolved_snapshot_hash": model_commit,
            "config_sha256": sha256_json(model_config),
        },
        "tokenizer": {
            "resolved_snapshot_hash": tokenizer_commit,
            "identity_sha256": sha256_json(tokenizer_identity),
            "artifacts": tokenizer_artifacts,
        },
        "adapter": adapter_artifacts,
        "inputs": {
            "dataset_attestation": dataset_attestation,
            "sealed_corpus_eligibility": prepared.corpus_eligibility,
            "curriculum_attestation": prepared.curriculum_attestation,
            "tokenized_splits": tokenization.tokenized_splits,
            "schedule_preflight": schedule_preflight,
            "source_snapshot": source_snapshot,
            "preparation_verification": preparation_verification,
            "recovery_filesystem_verification": (
                recovery_filesystem_verification
            ),
            "output_directory_identity": output_directory_identity,
            "train_data": {"path": config.data.train_path, "sha256": sha256_file(train_path)},
            "eval_data": {"path": config.data.eval_path, "sha256": sha256_file(eval_path)},
            "train_dataset_manifest": {
                "path": str(dataset_manifest_path(train_path)),
                "sha256": sha256_file(dataset_manifest_path(train_path)),
            },
            "eval_dataset_manifest": {
                "path": str(dataset_manifest_path(eval_path)),
                "sha256": sha256_file(dataset_manifest_path(eval_path)),
            },
            "config": {"path": str(config.path), "sha256": sha256_file(config.path)},
            "run_identity": {
                "path": str(run_identity_path),
                "sha256": run_identity_sha256,
            },
            "source": current_source,
            "deployment": deployment,
        },
        "runtime": {
            "torch": torch.__version__,
            "transformers": __import__("transformers").__version__,
            "peft": __import__("peft").__version__,
            "accelerate": __import__("accelerate").__version__,
            "dtype": config.model.dtype,
            "attention": config.model.attn_implementation,
            "trainer": trainer_runtime,
            "trainer_arguments": trainer_arguments,
            "resume": asdict(resume),
            "environment": runtime_identity(torch),
            "job": job_identity,
        },
        "metrics": metrics_record,
        "training_evidence": training_evidence,
        "adapter_admission": adapter_admission,
    }
    if schedule_preflight is not None:
        validate_completed_training_evidence(manifest)
        validate_manifest_adapter_admission(manifest)
    _verify_final_artifact_trees(
        output_dir,
        adapter_artifacts,
        tokenizer_artifacts,
        require_protected=(schedule_preflight is not None),
    )
    manifest_path = output_dir / "training-manifest.json"
    write_manifest_noreplace(
        manifest_path,
        manifest,
        publication_profile=publication_profile,
    )
    return manifest_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--resume-from-checkpoint",
        metavar="AUTO|NEVER|PATH",
        help="override [run].resume; AUTO discovers the latest checkpoint",
    )
    parser.add_argument("--preparation-eligibility-report", type=Path)
    parser.add_argument("--preparation-token-audit-report", type=Path)
    parser.add_argument("--preparation-runtime-smoke-report", type=Path)
    parser.add_argument("--prepare-job-id")
    parser.add_argument(
        "--recovery-publication-preflight-report",
        type=Path,
        help=(
            "canonical live-filesystem no-replace probe required by scheduled "
            "model-v3 training"
        ),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    override = args.resume_from_checkpoint
    if override is not None:
        override = {"AUTO": "auto", "NEVER": "never"}.get(override.upper(), override)
    report_values = (
        args.preparation_eligibility_report,
        args.preparation_token_audit_report,
        args.preparation_runtime_smoke_report,
        args.prepare_job_id,
    )
    if any(value is not None for value in report_values) and not all(
        value is not None for value in report_values
    ):
        raise ValueError("all four preparation report arguments are required together")
    reports = (
        None
        if report_values[0] is None
        else PreparationReports(
            eligibility=report_values[0],
            token_audit=report_values[1],
            runtime_smoke=report_values[2],
            prepare_job_id=report_values[3],
        )
    )
    path = train(
        load_config(args.config),
        resume_override=override,
        preparation_reports=reports,
        recovery_publication_preflight_report=(
            args.recovery_publication_preflight_report
        ),
    )
    print(json.dumps({"manifest": str(path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
