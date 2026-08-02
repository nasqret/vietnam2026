"""Strict admission of the immutable model-v3 pretrained-base report.

The ordinary model-v3 replay gate accepts trained-adapter reports only.  It
correctly rejects the additional ``pretrained_base_comparison`` authority and
the different policy-provenance schema emitted by the separate control run.
This module does not weaken that gate.  It admits exactly one byte-pinned WMI
control artifact, validates its complete base-model/comparison/deployment
authority, and then projects only the already-validated policy envelope into
the trained gate's schema so the unchanged goal and search-accounting
validator can be reused.

No model framework or weight is loaded here.  The report claims no proofs, so
there is no certificate to kernel-replay; acceptance attests that all four
search failures and every decoder counter are internally consistent under the
same frozen benchmark and model-v3 capability surface.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Mapping

from . import evaluation_replay as replay
from . import pretrained_baseline as baseline
from .contract import (
    environment_record,
    held_out_contract_record,
    held_out_contract_sha256,
)
from .manifest import sha256_json
from .prompt import PEANO_PROMPT_V3, prompt_contract_sha256
from .runtime import source_files_identity


REPORT_FORMAT = "peano-policy-v3-pretrained-baseline-replay"
REPORT_VERSION = 1
ADMISSION_PROFILE = "wmi-pretrained-base-job-218172-v1"

EXPECTED_REPORT_BYTES = 96_702
EXPECTED_REPORT_SHA256 = (
    "410be8f224d2dac6d28c4e0f55f125e95d5bc1f725b9c20851b00c15394d97b9"
)
EXPECTED_REPORT_RECORD_SHA256 = (
    "04ea8a7f2c76827c91e709bb2cadffb12954caa6d05702d4702803b176280a3a"
)
EXPECTED_SOURCE_COMMIT = "4d44609ee32d5d28726c082ef7b5649c0a1107a6"
EXPECTED_EVALUATION_JOB_ID = "218172"
EXPECTED_TRAINING_JOB_ID = "217859"

EXPECTED_EVALUATOR_SOURCE_SHA256 = (
    "0d46da46d9d90ce69796f6a18963ddd3a256417f1a610dfcb900792e32a26e07"
)
EXPECTED_EVALUATOR_SEMANTIC_SOURCES_SHA256 = (
    "54e4075976368351501260c45117bde43b29b51348006d55fe458505f23d9d7d"
)
EXPECTED_EVALUATOR_SEMANTIC_INVENTORY_SHA256 = (
    "41db9b714f2545ab95c48a5d9853300ec2bee81379a893dbbbc6313be627e98d"
)
EXPECTED_BASELINE_SOURCES_SHA256 = (
    "878355907269946860a9374645e992b480956f83aa659d9ba1bf45f49d7f28c3"
)
EXPECTED_BASELINE_INVENTORY_SHA256 = (
    "10faf2ba3cf612f34de9d3a660dff28f70e6e275ba21fa0bfdf66d373b17f6f0"
)

EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256 = (
    "db88dcc6d47c270566bb8a6218f3238bc9be8e03db9f8d14147b9fa6639f7279"
)
EXPECTED_LIBRARY_SHA256 = (
    "d173c2f1a32de6a9207fdee1ac77334a77cdebbf84568559eeb6066653d94c63"
)
EXPECTED_LIBRARY_SIZE = 247
EXPECTED_TRAINING_MANIFEST_SHA256 = (
    "caa5569c98ed9ea048d413301b803c39011957d1c97307e5b109846989e18569"
)
EXPECTED_TRAINING_MANIFEST_BYTES = 1_631_246
EXPECTED_DATASET_SHA256 = (
    "2e236384ecb6e7b15ccf986abab53fcfd4ec47fc97c7e00f5cc736dbbb4f224e"
)
EXPECTED_RUN_NAME = "qwen3-1.7b-peano-lora-v3-library"
EXPECTED_BASE_CONFIG_SHA256 = (
    "a325c9f27de176887b8ca7f68d21714247f9c8106e8c120219789338da9a5dcd"
)
EXPECTED_ADAPTER_SHA256 = (
    "db428e3c891166e43c1c71df7902e6fb579959f19c300cafe7ae8dcfe2dd2a70"
)
EXPECTED_TOKENIZER_SHA256 = (
    "2c5206dc7dda009d1a466348530a56c21f68d68057115142b2cd121838cf3f5e"
)
EXPECTED_TOKENIZER_IDENTITY_SHA256 = (
    "8582a45bba2100c7c7ac18ac25a64d81ccec6ed03717d1d74a6a1868dc11155d"
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
EXPECTED_OPTIMIZER_STEPS = 649
EXPECTED_COMPARISON_AUTHORITY_SHA256 = (
    "4b543b7f8ab7b6f36ca9384e57b7236f5960201d3d4c4f41b06b14c390318e9c"
)
EXPECTED_COMPARISON_RECORD_SHA256 = (
    "66b25c0cc5543af46d2a30fc776eb6027222abed9b53253e16a300bae1ecec05"
)
EXPECTED_BASE_POLICY_RECORD_SHA256 = (
    "c8d4f9092fb5c1f894812ad4ce69a04078106898ab6a0fb28d35cda6e94fbc08"
)

BASELINE_EVALUATION_SCRIPT = Path(
    "slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch"
)
EXPECTED_BASELINE_SCRIPT_SHA256 = (
    "9c7f7c4bfeba8108c92d2a0d4647780a4358103477fe2861708c6cdc0e4f0331"
)
EXPECTED_BASELINE_SCRIPT_COMPOSITE_SHA256 = (
    "2af758135546f70cd907c5ae0fc9d0e439a41602be06c38e858c43f7944bd83b"
)
EXPECTED_SUPPORT_SCRIPT_SHA256 = (
    "410cecfc9a2f007d7ad43058d9172605de0c4f23fae43e4e83e6629420bae2da"
)
EXPECTED_JOB_RECORD_SHA256 = (
    "5c9498dc8e9c323d2fbd3a405513a72b860a5f91dbaa7642025969b77f9590a9"
)
EXPECTED_EVALUATION_RUNTIME_SHA256 = (
    "59033cc48201aa51c32e1572b4bf5e3090fdf9fa831f1816cdfe4a06c6641126"
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ADMISSION_CLI = Path("scripts/replay_peano_v3_pretrained_baseline.py")


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


def _exact_fields(
    record: Mapping[str, object], fields: set[str], label: str
) -> None:
    if set(record) != fields:
        raise replay.EvaluationReplayError(f"{label}: incompatible fields")


def _require_digest(value: object, expected: str, label: str) -> None:
    if _canonical_sha256(value) != expected:
        raise replay.EvaluationReplayError(f"{label} differs from the pinned run")


def _admission_sources() -> Mapping[str, object]:
    """Hash the separate admission tool and its baseline authority sources."""

    return source_files_identity(
        (
            Path(__file__),
            REPOSITORY_ROOT / ADMISSION_CLI,
            REPOSITORY_ROOT / "scripts" / "eval_pretrained_peano_policy.py",
            REPOSITORY_ROOT
            / "training"
            / "peano_policy"
            / "pretrained_baseline.py",
            REPOSITORY_ROOT
            / "training"
            / "peano_policy"
            / "adapter_admission.py",
            REPOSITORY_ROOT
            / "training"
            / "peano_policy"
            / "training_evidence.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "contract.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "manifest.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "prompt.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "runtime.py",
            REPOSITORY_ROOT
            / "training"
            / "peano_policy"
            / "evaluation_replay.py",
            REPOSITORY_ROOT / BASELINE_EVALUATION_SCRIPT,
            REPOSITORY_ROOT / replay.EXPECTED_SUPPORT_SCRIPT,
        )
    )


def _preflight_report(report_path: Path) -> tuple[dict[str, object], bytes]:
    """Reject every file except the exact immutable WMI control report."""

    report, raw = replay.load_evaluation_report(report_path)
    if (
        len(raw) != EXPECTED_REPORT_BYTES
        or hashlib.sha256(raw).hexdigest() != EXPECTED_REPORT_SHA256
        or _canonical_sha256(report) != EXPECTED_REPORT_RECORD_SHA256
    ):
        raise replay.EvaluationReplayError(
            "report bytes differ from the pinned pretrained-base evaluation"
        )
    return report, raw


def _load_pinned_training_manifest(
    manifest_path: Path,
) -> tuple[dict[str, object], bytes]:
    """Load the exact completed training authority used by both treatments."""

    manifest, raw = replay.load_evaluation_report(manifest_path)
    if (
        len(raw) != EXPECTED_TRAINING_MANIFEST_BYTES
        or hashlib.sha256(raw).hexdigest() != EXPECTED_TRAINING_MANIFEST_SHA256
    ):
        raise replay.EvaluationReplayError(
            "training manifest bytes differ from the pinned completed run"
        )
    return manifest, raw


def _validate_source_group(
    value: object,
    *,
    canonical_sha256: str,
    inventory_sha256: str,
    label: str,
) -> dict[str, object]:
    record = _mapping(value, label)
    _exact_fields(record, {"files", "sha256"}, label)
    if record.get("sha256") != inventory_sha256:
        raise replay.EvaluationReplayError(f"{label}: inventory digest differs")
    _require_digest(record, canonical_sha256, label)
    files = _mapping(record.get("files"), f"{label}.files")
    if not files:
        raise replay.EvaluationReplayError(f"{label}: empty source inventory")
    for path, digest in files.items():
        if type(path) is not str or not path or type(digest) is not str:
            raise replay.EvaluationReplayError(f"{label}: malformed source entry")
        replay._sha256(digest, f"{label} digest for {path}")
    return record


def _validate_baseline_job(
    value: object, context: replay.ReplayContext
) -> dict[str, object]:
    job = _mapping(value, "baseline evaluation job")
    _require_digest(job, EXPECTED_JOB_RECORD_SHA256, "baseline evaluation job")
    if (
        job.get("scheduler") != "slurm"
        or job.get("job_id") != EXPECTED_EVALUATION_JOB_ID
    ):
        raise replay.EvaluationReplayError("baseline belongs to a different Slurm job")

    if (
        context.support_script_sha256 != EXPECTED_SUPPORT_SCRIPT_SHA256
        or replay._sha256_file(REPOSITORY_ROOT / BASELINE_EVALUATION_SCRIPT)
        != EXPECTED_BASELINE_SCRIPT_SHA256
    ):
        raise replay.EvaluationReplayError(
            "current baseline or support Slurm script differs from the pinned run"
        )

    deployment = _mapping(job.get("deployment"), "baseline deployment")
    source = _mapping(deployment.get("source_sync"), "baseline source deployment")
    if (
        source.get("status") != "synced"
        or source.get("path") != ".peano-source-provenance.tsv"
        or source.get("git_commit") != EXPECTED_SOURCE_COMMIT
        or source.get("git_dirty") is not False
    ):
        raise replay.EvaluationReplayError(
            "baseline used a different or dirty source deployment"
        )
    replay._sha256(source.get("sha256"), "baseline source provenance hash")

    support = _mapping(deployment.get("support_script"), "baseline support script")
    expected_support = {
        "status": "declared",
        "path": replay.EXPECTED_SUPPORT_SCRIPT.as_posix(),
        "sha256": EXPECTED_SUPPORT_SCRIPT_SHA256,
        "sourced_sha256": EXPECTED_SUPPORT_SCRIPT_SHA256,
    }
    if support != expected_support:
        raise replay.EvaluationReplayError("baseline support-script binding differs")
    script = _mapping(deployment.get("job_script"), "baseline job script")
    if script != {
        "status": "declared",
        "path": BASELINE_EVALUATION_SCRIPT.as_posix(),
        "file_sha256": EXPECTED_BASELINE_SCRIPT_SHA256,
        "sha256": EXPECTED_BASELINE_SCRIPT_COMPOSITE_SHA256,
        "support_script": expected_support,
    }:
        raise replay.EvaluationReplayError("baseline Slurm-script binding differs")

    submission = _mapping(job.get("submission"), "baseline submission")
    if (
        submission.get("job_id") != EXPECTED_EVALUATION_JOB_ID
        or submission.get("dependency_job_id") != EXPECTED_TRAINING_JOB_ID
        or submission.get("git_commit") != EXPECTED_SOURCE_COMMIT
        or submission.get("git_dirty") != "false"
        or submission.get("script") != BASELINE_EVALUATION_SCRIPT.as_posix()
        or submission.get("script_sha256")
        != EXPECTED_BASELINE_SCRIPT_COMPOSITE_SHA256
    ):
        raise replay.EvaluationReplayError("baseline submission binding differs")
    ledger = _mapping(job.get("ledger"), "baseline submission ledger")
    if (
        ledger.get("path") != "logs/submissions.tsv"
        or ledger.get("row_sha256") != sha256_json(submission)
    ):
        raise replay.EvaluationReplayError("baseline submission ledger is invalid")
    return job


def _validate_training_manifest(
    manifest: Mapping[str, object],
    *,
    comparison: Mapping[str, object],
    context: replay.ReplayContext,
) -> dict[str, object]:
    """Cross-bind the completed training authority to the control report."""

    try:
        validated_environment = baseline.validate_comparison_manifest(manifest)
    except (TypeError, ValueError, RuntimeError) as exc:
        raise replay.EvaluationReplayError(
            f"completed comparison manifest is invalid: {exc}"
        ) from exc
    if (
        environment_record(validated_environment) != context.authority.environment
        or comparison.get("environment") != context.authority.environment
    ):
        raise replay.EvaluationReplayError(
            "training manifest, report, and trusted model-v3 environment differ"
        )

    run = _mapping(manifest.get("run"), "training manifest run")
    runtime = _mapping(manifest.get("runtime"), "training manifest runtime")
    training_job = _mapping(runtime.get("job"), "training manifest job")
    if (
        run.get("name") != EXPECTED_RUN_NAME
        or comparison.get("comparison_run_name") != run.get("name")
        or training_job.get("scheduler") != "slurm"
        or training_job.get("job_id") != EXPECTED_TRAINING_JOB_ID
    ):
        raise replay.EvaluationReplayError(
            "comparison run name or training Slurm job is not cross-bound"
        )
    training_submission = _mapping(
        training_job.get("submission"), "training manifest submission"
    )
    if (
        training_submission.get("job_id") != EXPECTED_TRAINING_JOB_ID
        or training_submission.get("git_commit") != EXPECTED_SOURCE_COMMIT
        or training_submission.get("git_dirty") != "false"
    ):
        raise replay.EvaluationReplayError(
            "training manifest source deployment differs from the evaluation"
        )

    base_model = _mapping(manifest.get("base_model"), "training base model")
    expected_base = {
        "id": baseline.EXPECTED_BASE_MODEL_ID,
        "requested_revision": baseline.EXPECTED_BASE_MODEL_REVISION,
        "resolved_snapshot_hash": baseline.EXPECTED_BASE_MODEL_REVISION,
        "config_sha256": EXPECTED_BASE_CONFIG_SHA256,
    }
    if base_model != expected_base or comparison.get("base_model") != {
        "id": base_model["id"],
        "revision": base_model["resolved_snapshot_hash"],
        "config_sha256": base_model["config_sha256"],
    }:
        raise replay.EvaluationReplayError(
            "training manifest base identity is not cross-bound to the report"
        )

    adapter = _mapping(manifest.get("adapter"), "training adapter artifact")
    if adapter != {
        "root": "adapter",
        "sha256": EXPECTED_ADAPTER_SHA256,
        "files": dict(EXPECTED_ADAPTER_FILES),
    } or comparison.get("adapter") != {
        "root": adapter["root"],
        "sha256": adapter["sha256"],
    }:
        raise replay.EvaluationReplayError(
            "training adapter tree and file inventory are not cross-bound"
        )

    tokenizer = _mapping(manifest.get("tokenizer"), "training tokenizer")
    tokenizer_artifacts = _mapping(
        tokenizer.get("artifacts"), "training tokenizer artifacts"
    )
    if (
        tokenizer.get("resolved_snapshot_hash")
        != baseline.EXPECTED_BASE_MODEL_REVISION
        or tokenizer.get("identity_sha256") != EXPECTED_TOKENIZER_IDENTITY_SHA256
        or tokenizer_artifacts
        != {
            "root": "tokenizer",
            "sha256": EXPECTED_TOKENIZER_SHA256,
            "files": dict(EXPECTED_TOKENIZER_FILES),
        }
        or comparison.get("tokenizer")
        != {
            "root": tokenizer_artifacts["root"],
            "sha256": tokenizer_artifacts["sha256"],
        }
    ):
        raise replay.EvaluationReplayError(
            "training tokenizer identity and artifact tree are not cross-bound"
        )

    inputs = _mapping(manifest.get("inputs"), "training manifest inputs")
    dataset_attestation = _mapping(
        inputs.get("dataset_attestation"), "training dataset attestation"
    )
    metrics = _mapping(manifest.get("metrics"), "training metrics")
    if (
        dataset_attestation.get("dataset_sha256") != EXPECTED_DATASET_SHA256
        or metrics.get("expected_optimizer_steps") != EXPECTED_OPTIMIZER_STEPS
        or metrics.get("actual_optimizer_steps") != EXPECTED_OPTIMIZER_STEPS
    ):
        raise replay.EvaluationReplayError(
            "training dataset or exact 649/649 optimizer-step evidence differs"
        )
    return {
        "run_name": run["name"],
        "training_job_id": training_job["job_id"],
        "dataset_sha256": dataset_attestation["dataset_sha256"],
        "expected_optimizer_steps": metrics["expected_optimizer_steps"],
        "actual_optimizer_steps": metrics["actual_optimizer_steps"],
        "adapter": {
            "root": adapter["root"],
            "sha256": adapter["sha256"],
            "files": adapter["files"],
        },
        "tokenizer": {
            "resolved_snapshot_hash": tokenizer["resolved_snapshot_hash"],
            "identity_sha256": tokenizer["identity_sha256"],
            "artifacts": tokenizer_artifacts,
        },
    }


def _validate_comparison_authority(
    report: Mapping[str, object], context: replay.ReplayContext
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    """Validate the full base identity and the completed-run comparison tree."""

    identity = _mapping(report.get("policy_identity"), "policy identity")
    _exact_fields(
        identity,
        {
            "name",
            "kind",
            "base_policy",
            "limits",
            "seed",
            "seed_schedule",
            "decoder_batching",
        },
        "policy identity",
    )
    base_policy = _mapping(identity.get("base_policy"), "base policy identity")
    _exact_fields(
        base_policy,
        {
            "name",
            "kind",
            "prompt_version",
            "prompt_contract_sha256",
            "environment",
            "decoding",
            "provenance",
        },
        "base policy identity",
    )
    _require_digest(
        base_policy, EXPECTED_BASE_POLICY_RECORD_SHA256, "base policy identity"
    )
    expected_base_name = f"peano-policy:pretrained-base:{EXPECTED_TRAINING_MANIFEST_SHA256[:12]}"
    if (
        report.get("policy") != f"{expected_base_name}:kernel-guided-search"
        or identity.get("name") != report.get("policy")
        or identity.get("kind") != "peano-kernel-guided-search-v1"
        or identity.get("limits") != replay.EXPECTED_SEARCH_LIMITS
        or identity.get("seed") != replay.EXPECTED_SEED
        or identity.get("seed_schedule")
        != "sha256-json-v1(seed,goal_name,goal_statement)"
        or identity.get("decoder_batching")
        != "one-model-generate-call-per-search-state"
        or base_policy.get("name") != expected_base_name
        or base_policy.get("kind") != baseline.BASELINE_POLICY_KIND
        or baseline.BASELINE_POLICY_KIND != "peano-policy-pretrained-base-v1"
    ):
        raise replay.EvaluationReplayError("pretrained-base policy identity is forged")

    prompt_sha = prompt_contract_sha256(PEANO_PROMPT_V3)
    if (
        base_policy.get("prompt_version") != PEANO_PROMPT_V3
        or base_policy.get("prompt_contract_sha256") != prompt_sha
        or base_policy.get("decoding")
        != {
            "max_new_tokens": replay.EXPECTED_MAX_NEW_TOKENS,
            "do_sample": True,
            "temperature": 1.0,
            "top_p": 1.0,
        }
    ):
        raise replay.EvaluationReplayError("pretrained-base prompt or decoder differs")

    full_environment = context.authority.environment
    if (
        base_policy.get("environment") != full_environment
        or _canonical_sha256(full_environment)
        != EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256
        or full_environment.get("environment_sha256")
        != baseline.EXPECTED_V3_ENVIRONMENT_SHA256
        or full_environment.get("library_identity_sha256")
        != EXPECTED_LIBRARY_SHA256
        or full_environment.get("library_full_identity_sha256")
        != EXPECTED_LIBRARY_SHA256
        or full_environment.get("library_prefix_length") != EXPECTED_LIBRARY_SIZE
        or full_environment.get("library_size") != EXPECTED_LIBRARY_SIZE
        or len(context.authority.allowed_theorems) != EXPECTED_LIBRARY_SIZE
    ):
        raise replay.EvaluationReplayError(
            "pretrained baseline does not use the trusted full model-v3 environment"
        )

    provenance = _mapping(base_policy.get("provenance"), "baseline provenance")
    _exact_fields(
        provenance,
        {"comparison_authority", "weights", "evaluation"},
        "baseline provenance",
    )
    comparison = _mapping(
        provenance.get("comparison_authority"), "comparison authority"
    )
    top_comparison = _mapping(
        report.get("pretrained_base_comparison"),
        "top-level comparison authority",
    )
    if comparison != top_comparison:
        raise replay.EvaluationReplayError(
            "top-level and policy comparison authorities differ"
        )
    _exact_fields(
        comparison,
        {
            "format",
            "v",
            "training_manifest_sha256",
            "comparison_run_name",
            "base_model",
            "model_runtime",
            "adapter",
            "tokenizer",
            "prompt_version",
            "prompt_contract_sha256",
            "environment",
            "held_out_contract",
            "held_out_contract_sha256",
            "goal_set_sha256",
            "seed",
            "search_limits",
            "max_new_tokens",
            "sampling",
            "comparison_authority_sha256",
        },
        "comparison authority",
    )
    _require_digest(
        comparison, EXPECTED_COMPARISON_RECORD_SHA256, "comparison authority"
    )
    unsigned = dict(comparison)
    claimed_comparison_sha = unsigned.pop("comparison_authority_sha256")
    if (
        claimed_comparison_sha != sha256_json(unsigned)
        or claimed_comparison_sha != EXPECTED_COMPARISON_AUTHORITY_SHA256
        or comparison.get("format") != baseline.BASELINE_FORMAT
        or comparison.get("v") != baseline.BASELINE_VERSION
        or comparison.get("training_manifest_sha256")
        != EXPECTED_TRAINING_MANIFEST_SHA256
        or comparison.get("comparison_run_name") != EXPECTED_RUN_NAME
    ):
        raise replay.EvaluationReplayError("comparison authority digest or run differs")

    expected_base = {
        "id": baseline.EXPECTED_BASE_MODEL_ID,
        "revision": baseline.EXPECTED_BASE_MODEL_REVISION,
        "config_sha256": EXPECTED_BASE_CONFIG_SHA256,
    }
    if (
        comparison.get("base_model") != expected_base
        or comparison.get("model_runtime")
        != {"dtype": "bfloat16", "attention": "sdpa"}
        or comparison.get("adapter")
        != {"root": "adapter", "sha256": EXPECTED_ADAPTER_SHA256}
        or comparison.get("tokenizer")
        != {"root": "tokenizer", "sha256": EXPECTED_TOKENIZER_SHA256}
    ):
        raise replay.EvaluationReplayError(
            "base revision, configuration, tokenizer, or comparison adapter differs"
        )
    if (
        comparison.get("prompt_version") != PEANO_PROMPT_V3
        or comparison.get("prompt_contract_sha256") != prompt_sha
        or comparison.get("environment") != full_environment
        or comparison.get("held_out_contract")
        != held_out_contract_record(PEANO_PROMPT_V3)
        or comparison.get("held_out_contract_sha256")
        != held_out_contract_sha256(PEANO_PROMPT_V3)
        or comparison.get("goal_set_sha256") != replay.EXPECTED_GOAL_SET_SHA256
        or comparison.get("seed") != replay.EXPECTED_SEED
        or comparison.get("search_limits") != replay.EXPECTED_SEARCH_LIMITS
        or comparison.get("max_new_tokens") != replay.EXPECTED_MAX_NEW_TOKENS
        or comparison.get("sampling")
        != {"do_sample": True, "temperature": 1.0, "top_p": 1.0}
    ):
        raise replay.EvaluationReplayError(
            "comparison prompt, benchmark, or search authority differs"
        )

    weights = _mapping(provenance.get("weights"), "baseline weights identity")
    if weights != {
        "kind": "pretrained-base-no-peft",
        "adapter_attached": False,
        "base_model_id": baseline.EXPECTED_BASE_MODEL_ID,
        "base_model_revision": baseline.EXPECTED_BASE_MODEL_REVISION,
    }:
        raise replay.EvaluationReplayError(
            "baseline weights do not identify the unattached pretrained base"
        )

    evaluation = _mapping(provenance.get("evaluation"), "baseline evaluation")
    _exact_fields(evaluation, {"sources", "runtime", "job"}, "baseline evaluation")
    sources = _validate_source_group(
        evaluation.get("sources"),
        canonical_sha256=EXPECTED_BASELINE_SOURCES_SHA256,
        inventory_sha256=EXPECTED_BASELINE_INVENTORY_SHA256,
        label="baseline evaluation sources",
    )
    runtime = replay._validate_runtime_identity(
        evaluation.get("runtime"), "baseline evaluation runtime"
    )
    _require_digest(
        runtime, EXPECTED_EVALUATION_RUNTIME_SHA256, "baseline evaluation runtime"
    )
    job = _validate_baseline_job(evaluation.get("job"), context)
    return comparison, sources, job


def _validate_evaluator(report: Mapping[str, object]) -> dict[str, object]:
    evaluator = _mapping(report.get("evaluator"), "evaluator")
    _exact_fields(evaluator, {"source_sha256", "semantic_sources", "runtime"}, "evaluator")
    if evaluator.get("source_sha256") != EXPECTED_EVALUATOR_SOURCE_SHA256:
        raise replay.EvaluationReplayError("baseline evaluator source differs")
    semantic = _validate_source_group(
        evaluator.get("semantic_sources"),
        canonical_sha256=EXPECTED_EVALUATOR_SEMANTIC_SOURCES_SHA256,
        inventory_sha256=EXPECTED_EVALUATOR_SEMANTIC_INVENTORY_SHA256,
        label="evaluator semantic sources",
    )
    replay._validate_runtime_identity(evaluator.get("runtime"), "evaluator runtime")
    return semantic


def _canonical_projection(
    report: Mapping[str, object],
    *,
    context: replay.ReplayContext,
    evaluation_sources: Mapping[str, object],
) -> dict[str, object]:
    """Project only validated baseline provenance into the canonical schema."""

    projected = deepcopy(dict(report))
    del projected["pretrained_base_comparison"]
    original_base = _mapping(
        _mapping(projected["policy_identity"], "projected policy identity").get(
            "base_policy"
        ),
        "projected base policy",
    )
    original_provenance = _mapping(
        original_base.get("provenance"), "projected provenance"
    )
    original_evaluation = _mapping(
        original_provenance.get("evaluation"), "projected evaluation"
    )
    actual_job = _mapping(original_evaluation.get("job"), "projected job")

    # The canonical trained validator owns the accounting logic but expects
    # its own Slurm script path.  The real baseline job has already been
    # validated byte-for-byte above; this synthetic job exists only to pass
    # the canonical validator's trained-policy deployment schema.
    synthetic_job = deepcopy(actual_job)
    deployment = _mapping(synthetic_job.get("deployment"), "synthetic deployment")
    job_script = _mapping(deployment.get("job_script"), "synthetic job script")
    composite = hashlib.sha256(
        f"{context.evaluation_script_sha256}\n{context.support_script_sha256}\n".encode(
            "ascii"
        )
    ).hexdigest()
    job_script.update(
        {
            "path": replay.EXPECTED_EVALUATION_SCRIPT.as_posix(),
            "file_sha256": context.evaluation_script_sha256,
            "sha256": composite,
        }
    )
    submission = _mapping(synthetic_job.get("submission"), "synthetic submission")
    submission.update(
        {
            "script": replay.EXPECTED_EVALUATION_SCRIPT.as_posix(),
            "script_sha256": composite,
        }
    )
    ledger = _mapping(synthetic_job.get("ledger"), "synthetic ledger")
    ledger["row_sha256"] = sha256_json(submission)

    run_name = EXPECTED_RUN_NAME
    manifest_sha = EXPECTED_TRAINING_MANIFEST_SHA256
    trained_base_name = f"peano-policy:{run_name}:{manifest_sha[:12]}"
    canonical_evaluation = {
        "sources": deepcopy(dict(evaluation_sources)),
        "runtime": deepcopy(original_evaluation["runtime"]),
        "job": synthetic_job,
        "training_job_binding": {
            "status": "slurm-bound",
            "training_manifest_job_id": EXPECTED_TRAINING_JOB_ID,
            "evaluation_job_id": EXPECTED_EVALUATION_JOB_ID,
            "dependency_job_id": EXPECTED_TRAINING_JOB_ID,
        },
    }
    canonical_base = {
        "name": trained_base_name,
        "kind": "peano-policy-adapter-v1",
        "prompt_version": PEANO_PROMPT_V3,
        "prompt_contract_sha256": context.authority.prompt_contract_sha256,
        "environment": deepcopy(dict(context.authority.environment)),
        "decoding": deepcopy(original_base["decoding"]),
        "provenance": {
            "training_manifest_sha256": manifest_sha,
            "prompt_version": PEANO_PROMPT_V3,
            "prompt_contract_sha256": context.authority.prompt_contract_sha256,
            "base_model_id": baseline.EXPECTED_BASE_MODEL_ID,
            "base_model_revision": baseline.EXPECTED_BASE_MODEL_REVISION,
            "adapter_sha256": EXPECTED_ADAPTER_SHA256,
            "run_name": run_name,
            "dataset_sha256": EXPECTED_DATASET_SHA256,
            "environment_sha256": baseline.EXPECTED_V3_ENVIRONMENT_SHA256,
            "held_out_contract_sha256": context.authority.held_out_contract_sha256,
            "library_snapshot_sha256": context.authority.library_snapshot_sha256,
            "evaluation": canonical_evaluation,
        },
    }
    policy_name = f"{trained_base_name}:kernel-guided-search"
    projected["policy"] = policy_name
    policy_identity = _mapping(projected["policy_identity"], "projected policy identity")
    policy_identity["name"] = policy_name
    policy_identity["base_policy"] = canonical_base
    return projected


def _same_current_context(
    before: replay.ReplayContext, after: replay.ReplayContext
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


def replay_pretrained_baseline_report(
    report_path: Path, training_manifest_path: Path
) -> dict[str, object]:
    """Validate the one pinned control report and return a distinct attestation."""

    report, raw = _preflight_report(report_path)
    training_manifest, training_manifest_raw = _load_pinned_training_manifest(
        training_manifest_path
    )
    admission_sources_before = _admission_sources()
    current_before = replay.current_replay_context()

    comparison, evaluation_sources, job = _validate_comparison_authority(
        report, current_before
    )
    training_binding = _validate_training_manifest(
        training_manifest,
        comparison=comparison,
        context=current_before,
    )
    semantic_sources = _validate_evaluator(report)
    projected = _canonical_projection(
        report,
        context=current_before,
        evaluation_sources=evaluation_sources,
    )
    historical_authority = replace(
        current_before.authority,
        evaluator_source_sha256=EXPECTED_EVALUATOR_SOURCE_SHA256,
        evaluator_semantic_sources=semantic_sources,
        evaluation_sources=evaluation_sources,
    )
    validation_context = replace(current_before, authority=historical_authority)
    claims = replay.validate_evaluation_record(
        projected,
        expected_source_commit=EXPECTED_SOURCE_COMMIT,
        expected_evaluation_job_id=EXPECTED_EVALUATION_JOB_ID,
        context=validation_context,
    )
    if claims:
        raise replay.EvaluationReplayError(
            "pretrained-base report unexpectedly contains a proof claim"
        )
    if (
        report.get("proved_goals") != 0
        or report.get("pass@k") != 0.0
        or report.get("status_counts")
        != {"proof": 0, "invalid": 0, "failing": 4, "limit": 0}
    ):
        raise replay.EvaluationReplayError(
            "pretrained-base report does not record exactly four failed searches"
        )

    current_after = replay.current_replay_context()
    admission_sources_after = _admission_sources()
    if not _same_current_context(current_before, current_after):
        raise replay.EvaluationReplayError(
            "kernel, authority, runtime, or deployment changed during baseline replay"
        )
    if admission_sources_after != admission_sources_before:
        raise replay.EvaluationReplayError(
            "pretrained-baseline admission sources changed during replay"
        )
    final_report, final_raw = replay.load_evaluation_report(report_path)
    if final_raw != raw or final_report != report:
        raise replay.EvaluationReplayError(
            "pinned pretrained-base report changed during replay"
        )
    final_manifest, final_manifest_raw = replay.load_evaluation_report(
        training_manifest_path
    )
    if (
        final_manifest_raw != training_manifest_raw
        or final_manifest != training_manifest
    ):
        raise replay.EvaluationReplayError(
            "pinned completed training manifest changed during replay"
        )

    search = _mapping(report.get("search"), "search")
    search_goals = replay._array(search.get("goals"), "search goals", maximum=4)
    search_summary = []
    for raw_goal in search_goals:
        goal = _mapping(raw_goal, "search goal")
        result = _mapping(goal.get("result"), "search result")
        decoder = _mapping(goal.get("decoder"), "search decoder")
        search_summary.append(
            {
                "name": goal["name"],
                "status": result["status"],
                "model_generate_calls": result["model_calls"],
                "states_discovered": result["states_discovered"],
                "candidates_executed": result["candidates_executed"],
                "candidate_sequences_returned": decoder[
                    "candidate_sequences_returned"
                ],
                "malformed_sequences_rejected": decoder[
                    "malformed_sequences_rejected"
                ],
            }
        )

    core: dict[str, object] = {
        "format": REPORT_FORMAT,
        "v": REPORT_VERSION,
        "status": "passed",
        "input": {
            "evaluation_report": {
                "path": str(report_path.resolve()),
                "bytes": len(raw),
                "sha256": EXPECTED_REPORT_SHA256,
                "canonical_record_sha256": EXPECTED_REPORT_RECORD_SHA256,
            },
            "training_manifest": {
                "path": str(training_manifest_path.resolve()),
                "bytes": len(training_manifest_raw),
                "sha256": EXPECTED_TRAINING_MANIFEST_SHA256,
            },
        },
        "evaluation": {
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "job_id": EXPECTED_EVALUATION_JOB_ID,
            "training_job_id": EXPECTED_TRAINING_JOB_ID,
            "job_record_sha256": _canonical_sha256(job),
            "evaluator_v": replay.EVALUATOR_VERSION,
            "mode": replay.EXPECTED_MODE,
            "goal_set_sha256": replay.EXPECTED_GOAL_SET_SHA256,
            "environment_sha256": baseline.EXPECTED_V3_ENVIRONMENT_SHA256,
            "sources": evaluation_sources,
        },
        "benchmark": {
            "goal_count": len(current_before.authority.goals),
            "goals": [
                {"name": goal.name, "statement": goal.theorem}
                for goal in current_before.authority.goals
            ],
            "search_limits": replay.EXPECTED_SEARCH_LIMITS,
        },
        "summary": {
            "attempts": 4,
            "claimed_proofs": 0,
            "kernel_replayed_proofs": 0,
            "proved_goals": 0,
            "pass@k": 0.0,
            "status_counts": report["status_counts"],
        },
        "proofs": [],
        "pretrained_base": {
            "policy_kind": baseline.BASELINE_POLICY_KIND,
            "weights_kind": "pretrained-base-no-peft",
            "adapter_attached": False,
            "base_model": comparison["base_model"],
            "tokenizer": comparison["tokenizer"],
            "comparison_adapter": comparison["adapter"],
            "training_manifest_sha256": EXPECTED_TRAINING_MANIFEST_SHA256,
            "comparison_authority_sha256": (
                EXPECTED_COMPARISON_AUTHORITY_SHA256
            ),
            "completed_training_binding": training_binding,
            "base_weight_shards_content_attested": False,
            "base_weight_attestation_limitation": (
                "HF revision, configuration digest, completed-manifest identity, "
                "and no-PEFT provenance are validated; pretrained base-model "
                "weight-shard bytes were not independently hashed before and "
                "after evaluation"
            ),
        },
        "search_accounting": {
            "canonical_validator_reused": True,
            "search_and_goal_payload_unmodified": True,
            "accounting_schema_projection": {
                "purpose": (
                    "translate the separately validated baseline policy and "
                    "deployment provenance into the unchanged trained-report "
                    "validator schema"
                ),
                "transformed_fields": [
                    "policy",
                    "policy_identity.name",
                    "policy_identity.base_policy",
                    "policy_identity.base_policy.provenance.evaluation.training_job_binding",
                    "policy_identity.base_policy.provenance.evaluation.job.deployment.job_script",
                    "policy_identity.base_policy.provenance.evaluation.job.submission.script",
                    "policy_identity.base_policy.provenance.evaluation.job.submission.script_sha256",
                    "policy_identity.base_policy.provenance.evaluation.job.ledger.row_sha256",
                    "pretrained_base_comparison (removed after separate validation)",
                ],
            },
            "actual": search["actual"],
            "goals": search_summary,
        },
        "admission": {
            "profile": ADMISSION_PROFILE,
            "scope": "one immutable pretrained-base control report",
            "canonical_trained_replay_unchanged": True,
            "original_report_edited": False,
            "full_comparison_authority_validated": True,
            "completed_training_manifest_cross_bound": True,
            "unattached_base_identity_and_provenance_validated": True,
            "base_weight_shards_content_attested": False,
            "historical_sources_validated": True,
            "deployment_and_job_validated": True,
            "zero_proof_claims_validated": True,
        },
        "replay_authority": {
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "sources": current_before.replay_sources,
            "runtime": current_before.replay_runtime,
            "job": current_before.replay_job,
        },
        "admission_authority": {
            "sources": admission_sources_before,
            "current_context_checked_before_and_after": True,
            "tool_sources_checked_before_and_after": True,
            "input_checked_before_and_after": True,
            "training_manifest_checked_before_and_after": True,
        },
    }
    return {**core, "attestation_sha256": _canonical_sha256(core)}


__all__ = [
    "ADMISSION_PROFILE",
    "EXPECTED_EVALUATION_JOB_ID",
    "EXPECTED_REPORT_BYTES",
    "EXPECTED_REPORT_SHA256",
    "EXPECTED_SOURCE_COMMIT",
    "EXPECTED_TRAINING_MANIFEST_BYTES",
    "EXPECTED_TRAINING_MANIFEST_SHA256",
    "REPORT_FORMAT",
    "REPORT_VERSION",
    "replay_pretrained_baseline_report",
]
