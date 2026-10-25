"""Version-pinned replay for one historical model-v3 evaluation artifact.

The trained evaluation produced by WMI job 218171 used the complete model-v3
prompt and theorem library, but its serialized adapter identity accidentally
contained only the legacy four-field environment projection.  The ordinary
replay verifier correctly rejects that incomplete identity and remains
unchanged.

This module is a deliberately narrow compatibility bridge for that one
immutable report.  It pins the report bytes, source commit, Slurm job,
historical evaluator sources, and both the legacy and complete environment
identities.  It also requires the immutable completed-training manifest and
cross-checks its run, model, adapter, tokenizer, dataset, optimizer, and job
identity against the evaluation report.  It accepts the legacy environment
only when it is the exact four-field projection of the repository's pinned
complete authority, verifies the four omitted library fields there, and
supplies the exact historical projection to a separately reconstructed replay
context.  It then invokes the existing strict replay implementation, so every
claimed proof is still checked independently by Peano Lab's kernel.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Mapping

from . import evaluation_replay as replay
from .adapter_admission import validate_manifest_adapter_admission
from .runtime import source_files_identity
from .training_evidence import (
    read_strict_training_manifest,
    validate_completed_training_evidence,
)


REPORT_FORMAT = "peano-policy-v3-historical-evaluation-replay"
REPORT_VERSION = 1
COMPATIBILITY_PROFILE = "wmi-trained-job-218171-legacy-environment-v1"

EXPECTED_REPORT_BYTES = 85_121
EXPECTED_REPORT_SHA256 = (
    "f134f8c2d8c173e2ebcee0ebd3b8dfbc59805619bd7e79706c11e51732e0956c"
)
EXPECTED_SOURCE_COMMIT = "4d44609ee32d5d28726c082ef7b5649c0a1107a6"
EXPECTED_EVALUATION_JOB_ID = "218171"
EXPECTED_TRAINING_JOB_ID = "217859"

EXPECTED_TRAINING_MANIFEST_BYTES = 1_631_246
EXPECTED_TRAINING_MANIFEST_SHA256 = (
    "caa5569c98ed9ea048d413301b803c39011957d1c97307e5b109846989e18569"
)
EXPECTED_TRAINING_RUN_NAME = "qwen3-1.7b-peano-lora-v3-library"
EXPECTED_BASE_MODEL_ID = "Qwen/Qwen3-1.7B-Base"
EXPECTED_BASE_MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
EXPECTED_BASE_CONFIG_SHA256 = (
    "a325c9f27de176887b8ca7f68d21714247f9c8106e8c120219789338da9a5dcd"
)
EXPECTED_ADAPTER_SHA256 = (
    "db428e3c891166e43c1c71df7902e6fb579959f19c300cafe7ae8dcfe2dd2a70"
)
EXPECTED_ADAPTER_FILES: Mapping[str, str] = {
    "adapter/README.md": (
        "e4c8e3ea343795c0bc7c902d380c62289a8baa427789644d2b483f28d1be3bfa"
    ),
    "adapter/adapter_config.json": (
        "0415c2d50b3717c5287bced0d835f8001f61185252df017b9e9435a470bf71fb"
    ),
    "adapter/adapter_model.safetensors": (
        "3fc38bbfb07c32fe0d198cd97427f5920e215a4f895858561b321b3916dbbfe3"
    ),
}
EXPECTED_TOKENIZER_SHA256 = (
    "2c5206dc7dda009d1a466348530a56c21f68d68057115142b2cd121838cf3f5e"
)
EXPECTED_TOKENIZER_FILES: Mapping[str, str] = {
    "tokenizer/added_tokens.json": (
        "c0284b582e14987fbd3d5a2cb2bd139084371ed9acbae488829a1c900833c680"
    ),
    "tokenizer/chat_template.jinja": (
        "87a2728cb8dc9fe424d624542f6060ec05a1d285ebbec578bb078900e33396b5"
    ),
    "tokenizer/merges.txt": (
        "8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5"
    ),
    "tokenizer/special_tokens_map.json": (
        "6676f091c8bc4d1b50146427cfde92073402866b87b6e39223227931b70083e9"
    ),
    "tokenizer/tokenizer.json": (
        "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4"
    ),
    "tokenizer/tokenizer_config.json": (
        "67e5a0a11cd35f9c00ee52e0af4cdc0baa75fea0cb5fce7d1beb251b4621d15c"
    ),
    "tokenizer/vocab.json": (
        "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910"
    ),
}
EXPECTED_DATASET_SHA256 = (
    "2e236384ecb6e7b15ccf986abab53fcfd4ec47fc97c7e00f5cc736dbbb4f224e"
)
EXPECTED_OPTIMIZER_STEPS = 649

EXPECTED_EVALUATOR_SOURCE_SHA256 = (
    "0d46da46d9d90ce69796f6a18963ddd3a256417f1a610dfcb900792e32a26e07"
)
EXPECTED_EVALUATOR_SEMANTIC_SOURCES_SHA256 = (
    "54e4075976368351501260c45117bde43b29b51348006d55fe458505f23d9d7d"
)
EXPECTED_EVALUATOR_SEMANTIC_INVENTORY_SHA256 = (
    "41db9b714f2545ab95c48a5d9853300ec2bee81379a893dbbbc6313be627e98d"
)
EXPECTED_EVALUATION_SOURCES_SHA256 = (
    "3eb973893c39de730025127bc70cbfd1fd9de0675b774aa0a954612f77e6ba37"
)
EXPECTED_EVALUATION_INVENTORY_SHA256 = (
    "8319a74f9905deec2622094e197730cb9192d7f59363665a5ef8742a509accc4"
)

EXPECTED_LEGACY_ENVIRONMENT_SHA256 = (
    "92bdedb70ab850a9548b2bc32813ed453280ae01cad43af3a70092ac941cbaa3"
)
EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256 = (
    "db88dcc6d47c270566bb8a6218f3238bc9be8e03db9f8d14147b9fa6639f7279"
)
EXPECTED_LIBRARY_IDENTITY_SHA256 = (
    "d173c2f1a32de6a9207fdee1ac77334a77cdebbf84568559eeb6066653d94c63"
)
EXPECTED_LIBRARY_PREFIX_LENGTH = 247
EXPECTED_LIBRARY_SIZE = 247

LEGACY_ENVIRONMENT_FIELDS = (
    "capabilities",
    "classical",
    "environment_sha256",
    "surface",
)
RECONSTRUCTED_ENVIRONMENT_FIELDS: Mapping[str, object] = {
    "library_full_identity_sha256": EXPECTED_LIBRARY_IDENTITY_SHA256,
    "library_identity_sha256": EXPECTED_LIBRARY_IDENTITY_SHA256,
    "library_prefix_length": EXPECTED_LIBRARY_PREFIX_LENGTH,
    "library_size": EXPECTED_LIBRARY_SIZE,
}

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPATIBILITY_CLI = Path("scripts/replay_peano_v3_legacy_evaluation.py")


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _mapping(value: object, label: str) -> dict[str, object]:
    if type(value) is not dict:
        raise replay.EvaluationReplayError(f"{label}: expected one object")
    return value


def _compatibility_sources() -> Mapping[str, object]:
    """Hash the separate bridge and CLI without altering canonical replay."""

    return source_files_identity(
        (
            Path(__file__),
            REPOSITORY_ROOT / COMPATIBILITY_CLI,
            REPOSITORY_ROOT
            / "training"
            / "peano_policy"
            / "adapter_admission.py",
            REPOSITORY_ROOT
            / "training"
            / "peano_policy"
            / "training_evidence.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "manifest.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "objective.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "prompt.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "runtime.py",
            REPOSITORY_ROOT
            / "training"
            / "peano_policy"
            / "evaluation_replay.py",
        )
    )


def _require_digest(value: object, expected: str, label: str) -> None:
    if _canonical_sha256(value) != expected:
        raise replay.EvaluationReplayError(f"{label} differs from the pinned artifact")


def _preflight_report(
    report_path: Path,
) -> tuple[
    dict[str, object],
    bytes,
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    """Reject every artifact except the exact historical WMI report."""

    report, raw = replay.load_evaluation_report(report_path)
    if len(raw) != EXPECTED_REPORT_BYTES or hashlib.sha256(raw).hexdigest() != (
        EXPECTED_REPORT_SHA256
    ):
        raise replay.EvaluationReplayError(
            "report bytes differ from the one pinned historical evaluation"
        )

    identity = _mapping(report.get("policy_identity"), "policy identity")
    base = _mapping(identity.get("base_policy"), "base policy identity")
    legacy_environment = _mapping(base.get("environment"), "legacy environment")
    if set(legacy_environment) != set(LEGACY_ENVIRONMENT_FIELDS):
        raise replay.EvaluationReplayError(
            "historical environment is not the exact four-field legacy projection"
        )
    _require_digest(
        legacy_environment,
        EXPECTED_LEGACY_ENVIRONMENT_SHA256,
        "historical environment",
    )

    evaluator = _mapping(report.get("evaluator"), "evaluator")
    if evaluator.get("source_sha256") != EXPECTED_EVALUATOR_SOURCE_SHA256:
        raise replay.EvaluationReplayError(
            "historical evaluator source differs from the pinned run"
        )
    semantic_sources = _mapping(
        evaluator.get("semantic_sources"), "evaluator semantic sources"
    )
    if semantic_sources.get("sha256") != (
        EXPECTED_EVALUATOR_SEMANTIC_INVENTORY_SHA256
    ):
        raise replay.EvaluationReplayError(
            "historical evaluator semantic inventory digest differs"
        )
    _require_digest(
        semantic_sources,
        EXPECTED_EVALUATOR_SEMANTIC_SOURCES_SHA256,
        "historical evaluator semantic sources",
    )

    provenance = _mapping(base.get("provenance"), "adapter provenance")
    evaluation = _mapping(provenance.get("evaluation"), "evaluation provenance")
    evaluation_sources = _mapping(
        evaluation.get("sources"), "historical evaluation sources"
    )
    if evaluation_sources.get("sha256") != EXPECTED_EVALUATION_INVENTORY_SHA256:
        raise replay.EvaluationReplayError(
            "historical evaluation inventory digest differs"
        )
    _require_digest(
        evaluation_sources,
        EXPECTED_EVALUATION_SOURCES_SHA256,
        "historical evaluation sources",
    )

    job = _mapping(evaluation.get("job"), "evaluation job")
    deployment = _mapping(job.get("deployment"), "evaluation deployment")
    source_sync = _mapping(deployment.get("source_sync"), "evaluation source sync")
    if (
        job.get("job_id") != EXPECTED_EVALUATION_JOB_ID
        or source_sync.get("git_commit") != EXPECTED_SOURCE_COMMIT
    ):
        raise replay.EvaluationReplayError(
            "report does not belong to the pinned source commit and Slurm job"
        )
    return report, raw, legacy_environment, semantic_sources, evaluation_sources


def _strict_training_manifest_snapshot(
    training_manifest_path: Path,
) -> tuple[dict[str, object], bytes]:
    """Use the project reader and bind it to the exact regular-file bytes."""

    try:
        before = read_strict_training_manifest(training_manifest_path)
        raw = replay._read_regular(training_manifest_path)
        after = read_strict_training_manifest(training_manifest_path)
    except (OSError, ValueError) as exc:
        raise replay.EvaluationReplayError(
            f"cannot load strict training manifest: {exc}"
        ) from None
    if before != after:
        raise replay.EvaluationReplayError(
            "training manifest changed while its byte identity was captured"
        )
    if (
        len(raw) != EXPECTED_TRAINING_MANIFEST_BYTES
        or hashlib.sha256(raw).hexdigest() != EXPECTED_TRAINING_MANIFEST_SHA256
    ):
        raise replay.EvaluationReplayError(
            "training manifest bytes differ from the pinned completed run"
        )
    return before, raw


def _training_authority(
    manifest: Mapping[str, object],
    report: Mapping[str, object],
) -> dict[str, object]:
    """Validate and join the completed run to report adapter provenance."""

    if manifest.get("v") != 1 or manifest.get("prompt_version") != 3:
        raise replay.EvaluationReplayError(
            "training manifest is not the pinned model-v3 manifest schema"
        )
    try:
        completed = validate_completed_training_evidence(manifest)
        validate_manifest_adapter_admission(manifest)
    except ValueError as exc:
        raise replay.EvaluationReplayError(
            f"training manifest semantic evidence failed: {exc}"
        ) from None

    run = _mapping(manifest.get("run"), "training run")
    base = _mapping(manifest.get("base_model"), "training base model")
    adapter = _mapping(manifest.get("adapter"), "training adapter")
    tokenizer = _mapping(manifest.get("tokenizer"), "training tokenizer")
    tokenizer_artifacts = _mapping(
        tokenizer.get("artifacts"), "training tokenizer artifacts"
    )
    inputs = _mapping(manifest.get("inputs"), "training inputs")
    dataset = _mapping(
        inputs.get("dataset_attestation"), "training dataset attestation"
    )
    inference_environment = _mapping(
        dataset.get("inference_environment"), "training inference environment"
    )
    runtime = _mapping(manifest.get("runtime"), "training runtime")
    job = _mapping(runtime.get("job"), "training job")
    job_submission = _mapping(job.get("submission"), "training job submission")
    job_deployment = _mapping(job.get("deployment"), "training job deployment")
    job_source = _mapping(
        job_deployment.get("source_sync"), "training source deployment"
    )
    metrics = _mapping(manifest.get("metrics"), "training metrics")
    steps = _mapping(completed.get("steps"), "completed optimizer steps")

    expected_base = {
        "id": EXPECTED_BASE_MODEL_ID,
        "requested_revision": EXPECTED_BASE_MODEL_REVISION,
        "resolved_snapshot_hash": EXPECTED_BASE_MODEL_REVISION,
        "config_sha256": EXPECTED_BASE_CONFIG_SHA256,
    }
    if base != expected_base:
        raise replay.EvaluationReplayError(
            "training base-model revision/config identity differs from the pinned run"
        )
    if run.get("name") != EXPECTED_TRAINING_RUN_NAME:
        raise replay.EvaluationReplayError(
            "training run name differs from the pinned run"
        )

    adapter_files = _mapping(adapter.get("files"), "training adapter files")
    if (
        adapter.get("root") != "adapter"
        or adapter.get("sha256") != EXPECTED_ADAPTER_SHA256
        or adapter_files != EXPECTED_ADAPTER_FILES
        or _canonical_sha256(adapter_files) != EXPECTED_ADAPTER_SHA256
    ):
        raise replay.EvaluationReplayError(
            "training adapter artifact tree differs from the pinned run"
        )
    tokenizer_files = _mapping(
        tokenizer_artifacts.get("files"), "training tokenizer files"
    )
    if (
        tokenizer_artifacts.get("root") != "tokenizer"
        or tokenizer_artifacts.get("sha256") != EXPECTED_TOKENIZER_SHA256
        or tokenizer_files != EXPECTED_TOKENIZER_FILES
        or _canonical_sha256(tokenizer_files) != EXPECTED_TOKENIZER_SHA256
    ):
        raise replay.EvaluationReplayError(
            "training tokenizer artifact tree differs from the pinned run"
        )
    if dataset.get("dataset_sha256") != EXPECTED_DATASET_SHA256:
        raise replay.EvaluationReplayError(
            "training dataset identity differs from the pinned run"
        )

    expected_step_record = {
        "expected_optimizer_steps": EXPECTED_OPTIMIZER_STEPS,
        "top_level_actual_optimizer_steps": EXPECTED_OPTIMIZER_STEPS,
        "train_result_global_step": EXPECTED_OPTIMIZER_STEPS,
        "trainer_state_global_step": EXPECTED_OPTIMIZER_STEPS,
        "trainer_state_max_steps": EXPECTED_OPTIMIZER_STEPS,
    }
    if (
        steps != expected_step_record
        or metrics.get("expected_optimizer_steps") != EXPECTED_OPTIMIZER_STEPS
        or metrics.get("actual_optimizer_steps") != EXPECTED_OPTIMIZER_STEPS
    ):
        raise replay.EvaluationReplayError(
            "completed optimizer steps differ from the pinned 649/649 run"
        )
    if (
        job.get("scheduler") != "slurm"
        or job.get("job_id") != EXPECTED_TRAINING_JOB_ID
        or job_submission.get("job_id") != EXPECTED_TRAINING_JOB_ID
        or job_source.get("git_commit") != EXPECTED_SOURCE_COMMIT
        or job_source.get("git_dirty") is not False
    ):
        raise replay.EvaluationReplayError(
            "training evidence does not bind the pinned clean Slurm job"
        )

    report_identity = _mapping(report.get("policy_identity"), "policy identity")
    report_base = _mapping(
        report_identity.get("base_policy"), "base policy identity"
    )
    report_provenance = _mapping(
        report_base.get("provenance"), "adapter provenance"
    )
    manifest_provenance = {
        "training_manifest_sha256": EXPECTED_TRAINING_MANIFEST_SHA256,
        "prompt_version": manifest.get("prompt_version"),
        "prompt_contract_sha256": manifest.get("prompt_contract_sha256"),
        "base_model_id": base.get("id"),
        "base_model_revision": base.get("resolved_snapshot_hash"),
        "adapter_sha256": adapter.get("sha256"),
        "run_name": run.get("name"),
        "dataset_sha256": dataset.get("dataset_sha256"),
        "environment_sha256": inference_environment.get("environment_sha256"),
        "held_out_contract_sha256": dataset.get("held_out_contract_sha256"),
        "library_snapshot_sha256": dataset.get("library_snapshot_sha256"),
    }
    mismatched = sorted(
        field
        for field, expected in manifest_provenance.items()
        if report_provenance.get(field) != expected
    )
    if mismatched:
        raise replay.EvaluationReplayError(
            "training manifest differs from report provenance fields: "
            + ", ".join(mismatched)
        )
    report_evaluation = _mapping(
        report_provenance.get("evaluation"), "report evaluation provenance"
    )
    binding = _mapping(
        report_evaluation.get("training_job_binding"),
        "report training-job binding",
    )
    if (
        binding.get("status") != "slurm-bound"
        or binding.get("training_manifest_job_id") != EXPECTED_TRAINING_JOB_ID
        or binding.get("dependency_job_id") != EXPECTED_TRAINING_JOB_ID
        or binding.get("evaluation_job_id") != EXPECTED_EVALUATION_JOB_ID
    ):
        raise replay.EvaluationReplayError(
            "training job evidence differs from report evaluation provenance"
        )

    return {
        "manifest_bytes": EXPECTED_TRAINING_MANIFEST_BYTES,
        "manifest_sha256": EXPECTED_TRAINING_MANIFEST_SHA256,
        "run_name": EXPECTED_TRAINING_RUN_NAME,
        "base_model": {
            **expected_base,
            "weight_shards_content_hashed": False,
            "identity_scope": (
                "requested/resolved revision and config SHA-256 provenance"
            ),
            "limitation": (
                "Base-weight shards are not content-hashed; this is revision/config "
                "provenance, not a bit-for-bit base-weight attestation."
            ),
        },
        "adapter": {
            "root": "adapter",
            "sha256": EXPECTED_ADAPTER_SHA256,
            "files": dict(EXPECTED_ADAPTER_FILES),
        },
        "tokenizer": {
            "root": "tokenizer",
            "sha256": EXPECTED_TOKENIZER_SHA256,
            "files": dict(EXPECTED_TOKENIZER_FILES),
        },
        "dataset_sha256": EXPECTED_DATASET_SHA256,
        "optimizer_steps": {
            "expected": EXPECTED_OPTIMIZER_STEPS,
            "actual": EXPECTED_OPTIMIZER_STEPS,
        },
        "training_job": {
            "scheduler": "slurm",
            "job_id": EXPECTED_TRAINING_JOB_ID,
            "source_commit": EXPECTED_SOURCE_COMMIT,
        },
        "report_provenance_cross_match": {
            "status": "matched",
            "fields": sorted(manifest_provenance),
            "training_job_binding": True,
        },
    }


def _validate_complete_authority(
    context: replay.ReplayContext,
    legacy_environment: Mapping[str, object],
) -> Mapping[str, object]:
    """Bind the legacy projection to the exact complete model-v3 authority."""

    full = context.authority.environment
    expected_fields = set(LEGACY_ENVIRONMENT_FIELDS) | set(
        RECONSTRUCTED_ENVIRONMENT_FIELDS
    )
    if set(full) != expected_fields:
        raise replay.EvaluationReplayError(
            "current model-v3 environment does not have the pinned complete schema"
        )
    if _canonical_sha256(full) != EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256:
        raise replay.EvaluationReplayError(
            "current complete model-v3 authority differs from the pinned authority"
        )
    projection = {field: full[field] for field in LEGACY_ENVIRONMENT_FIELDS}
    if projection != legacy_environment:
        raise replay.EvaluationReplayError(
            "legacy environment is not the exact projection of current authority"
        )
    for field, expected in RECONSTRUCTED_ENVIRONMENT_FIELDS.items():
        if full.get(field) != expected:
            raise replay.EvaluationReplayError(
                f"current complete authority has a different {field}"
            )
    if (
        context.authority.library_snapshot_sha256
        != EXPECTED_LIBRARY_IDENTITY_SHA256
        or len(context.authority.allowed_theorems) != EXPECTED_LIBRARY_SIZE
    ):
        raise replay.EvaluationReplayError(
            "current theorem library differs from the pinned model-v3 library"
        )
    return full


def _same_current_context(
    before: replay.ReplayContext,
    after: replay.ReplayContext,
) -> bool:
    return (
        after.authority == before.authority
        and after.verify_proof is before.verify_proof
        and after.evaluation_script_sha256 == before.evaluation_script_sha256
        and after.support_script_sha256 == before.support_script_sha256
        and after.replay_sources == before.replay_sources
        and after.replay_runtime == before.replay_runtime
        and after.replay_job == before.replay_job
    )


def replay_historical_evaluation_report(
    report_path: Path,
    training_manifest_path: Path,
) -> dict[str, object]:
    """Replay the single pinned report and return a distinct attestation.

    Canonical model-v3 replay is intentionally not called through its public
    entry point: it must continue rejecting the incomplete historical identity.
    Instead, its dependency-injected strict implementation receives a local,
    reconstructed legacy context after all compatibility conditions pass.
    """

    (
        report,
        raw,
        legacy_environment,
        semantic_sources,
        evaluation_sources,
    ) = _preflight_report(report_path)
    training_manifest, training_manifest_raw = _strict_training_manifest_snapshot(
        training_manifest_path
    )
    training_authority = _training_authority(training_manifest, report)
    compatibility_sources_before = _compatibility_sources()
    current_before = replay.current_replay_context()
    full_environment = _validate_complete_authority(
        current_before, legacy_environment
    )

    legacy_authority = replace(
        current_before.authority,
        environment=legacy_environment,
        evaluator_source_sha256=EXPECTED_EVALUATOR_SOURCE_SHA256,
        evaluator_semantic_sources=semantic_sources,
        evaluation_sources=evaluation_sources,
    )
    legacy_context = replace(current_before, authority=legacy_authority)
    strict_attestation = replay._replay_evaluation_report(
        report_path,
        expected_source_commit=EXPECTED_SOURCE_COMMIT,
        expected_evaluation_job_id=EXPECTED_EVALUATION_JOB_ID,
        context=legacy_context,
        recheck_context=False,
    )
    strict_input = _mapping(strict_attestation.get("input"), "strict replay input")
    if (
        strict_input.get("bytes") != EXPECTED_REPORT_BYTES
        or strict_input.get("sha256") != EXPECTED_REPORT_SHA256
    ):
        raise replay.EvaluationReplayError(
            "strict replay did not consume the pinned historical report bytes"
        )

    current_after = replay.current_replay_context()
    compatibility_sources_after = _compatibility_sources()
    if not _same_current_context(current_before, current_after):
        raise replay.EvaluationReplayError(
            "kernel, authority, runtime, or deployment changed during historical replay"
        )
    if compatibility_sources_after != compatibility_sources_before:
        raise replay.EvaluationReplayError(
            "historical compatibility replay tool changed during replay"
        )

    final_report, final_raw = replay.load_evaluation_report(report_path)
    if final_raw != raw or final_report != report:
        raise replay.EvaluationReplayError(
            "pinned historical evaluation report changed during replay"
        )
    final_training_manifest, final_training_manifest_raw = (
        _strict_training_manifest_snapshot(training_manifest_path)
    )
    if (
        final_training_manifest_raw != training_manifest_raw
        or final_training_manifest != training_manifest
    ):
        raise replay.EvaluationReplayError(
            "pinned training manifest changed during historical replay"
        )

    core = {
        key: value
        for key, value in strict_attestation.items()
        if key != "attestation_sha256"
    }
    core.update(
        {
            "format": REPORT_FORMAT,
            "v": REPORT_VERSION,
            "input": {
                **strict_attestation["input"],
                "training_manifest": {
                    "path": str(training_manifest_path.resolve()),
                    "bytes": len(training_manifest_raw),
                    "sha256": hashlib.sha256(training_manifest_raw).hexdigest(),
                    "canonical_record_sha256": _canonical_sha256(
                        training_manifest
                    ),
                },
            },
            "compatibility": {
                "profile": COMPATIBILITY_PROFILE,
                "scope": "one immutable historical trained-policy report",
                "canonical_replay_unchanged": True,
                "source_commit": EXPECTED_SOURCE_COMMIT,
                "evaluation_job_id": EXPECTED_EVALUATION_JOB_ID,
                "input_sha256": EXPECTED_REPORT_SHA256,
                "legacy_environment": {
                    "fields": list(LEGACY_ENVIRONMENT_FIELDS),
                    "record_sha256": EXPECTED_LEGACY_ENVIRONMENT_SHA256,
                },
                "reconstruction": {
                    "status": "exact-projection-of-pinned-complete-authority",
                    "fields": dict(RECONSTRUCTED_ENVIRONMENT_FIELDS),
                    "complete_environment_record_sha256": (
                        EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256
                    ),
                    "verified_complete_environment_record_sha256": (
                        _canonical_sha256(full_environment)
                    ),
                },
                "historical_sources": {
                    "evaluator_source_sha256": EXPECTED_EVALUATOR_SOURCE_SHA256,
                    "evaluator_semantic_sources_sha256": (
                        EXPECTED_EVALUATOR_SEMANTIC_SOURCES_SHA256
                    ),
                    "evaluator_semantic_inventory_sha256": (
                        EXPECTED_EVALUATOR_SEMANTIC_INVENTORY_SHA256
                    ),
                    "evaluation_sources_sha256": (
                        EXPECTED_EVALUATION_SOURCES_SHA256
                    ),
                    "evaluation_inventory_sha256": (
                        EXPECTED_EVALUATION_INVENTORY_SHA256
                    ),
                },
            },
            "compatibility_replay_authority": {
                "sources": compatibility_sources_before,
                "training_manifest": training_authority,
                "legacy_context_strict_attestation_sha256": strict_attestation[
                    "attestation_sha256"
                ],
                "current_context_checked_before_and_after": True,
                "tool_sources_checked_before_and_after": True,
                "training_manifest_checked_before_and_after": True,
            },
        }
    )
    return {**core, "attestation_sha256": _canonical_sha256(core)}


__all__ = [
    "COMPATIBILITY_PROFILE",
    "EXPECTED_EVALUATION_JOB_ID",
    "EXPECTED_REPORT_BYTES",
    "EXPECTED_REPORT_SHA256",
    "EXPECTED_SOURCE_COMMIT",
    "EXPECTED_TRAINING_MANIFEST_BYTES",
    "EXPECTED_TRAINING_MANIFEST_SHA256",
    "REPORT_FORMAT",
    "REPORT_VERSION",
    "replay_historical_evaluation_report",
]
