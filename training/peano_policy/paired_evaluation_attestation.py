"""Fail-closed admission of the August 2026 paired launch smoke.

This is a composition layer, not another evaluator.  It consumes the two
immutable evaluation reports, their separately produced replay attestations,
and the exact training manifest.  It checks that the trained and pretrained
comparison runs really share the frozen four-goal benchmark and all declared
search conditions, then records the deliberately narrow observed result.

The reports do not contain complete raw model-output transcripts.  Therefore
this module neither regenerates model outputs nor attributes the observed
difference causally to training.  The trained replay attestation independently
kernel-replays its three proof scripts; this layer verifies and cross-binds
that evidence.  The pretrained comparison makes no proof claim and does not
pin every base-model weight byte.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from pathlib import PurePosixPath
import subprocess
from typing import Mapping, Sequence

from .runtime import source_files_identity


REPORT_FORMAT = "peano-policy-v3-paired-launch-smoke-attestation"
REPORT_VERSION = 1
ADMITTED_RESULT = "paired_launch_smoke_admitted"

EXPECTED_SOURCE_COMMIT = "4d44609ee32d5d28726c082ef7b5649c0a1107a6"
EXPECTED_TRAINING_JOB_ID = "217859"
EXPECTED_TRAINED_EVALUATION_JOB_ID = "218171"
EXPECTED_PRETRAINED_EVALUATION_JOB_ID = "218172"

EXPECTED_TRAINED_REPORT_BYTES = 85_121
EXPECTED_TRAINED_REPORT_SHA256 = (
    "f134f8c2d8c173e2ebcee0ebd3b8dfbc59805619bd7e79706c11e51732e0956c"
)
EXPECTED_TRAINED_REPORT_RECORD_SHA256 = (
    "fee88f56e5a1cb88b2cf0ce00b713f2ea63eeacb1a0c1c507fdf19a5d250835b"
)
EXPECTED_PRETRAINED_REPORT_BYTES = 96_702
EXPECTED_PRETRAINED_REPORT_SHA256 = (
    "410be8f224d2dac6d28c4e0f55f125e95d5bc1f725b9c20851b00c15394d97b9"
)
EXPECTED_PRETRAINED_REPORT_RECORD_SHA256 = (
    "04ea8a7f2c76827c91e709bb2cadffb12954caa6d05702d4702803b176280a3a"
)
EXPECTED_TRAINING_MANIFEST_BYTES = 1_631_246
EXPECTED_TRAINING_MANIFEST_SHA256 = (
    "caa5569c98ed9ea048d413301b803c39011957d1c97307e5b109846989e18569"
)

# These two files are the final producer attestations consumed by this layer.
# Both the canonical self-hash and the serialized bytes are pinned.  The values
# are updated only when the reviewed producer artifacts themselves are rebuilt.
EXPECTED_TRAINED_ATTESTATION_BYTES = 24_869
EXPECTED_TRAINED_ATTESTATION_FILE_SHA256 = (
    "feacfdb85b5080a9c304903221b4540a19ec27b0eee5d5b0727f34880102cd02"
)
EXPECTED_TRAINED_ATTESTATION_SHA256 = (
    "e900a10241db0451992313eb2a7b0341911a7a71cd8af91e831a279874afda56"
)
EXPECTED_PRETRAINED_ATTESTATION_BYTES = 24_314
EXPECTED_PRETRAINED_ATTESTATION_FILE_SHA256 = (
    "05fe9d657842808bd69c25fd3ec47a1ca2942a8b26b6b028f30fa202b7341453"
)
EXPECTED_PRETRAINED_ATTESTATION_SHA256 = (
    "056519bc3598a390526fdf9054aa38090d499f7f837af0a2ace7af8caaa560e7"
)

EXPECTED_GOAL_SET_SHA256 = (
    "198beaf753c0abab3151b4913ca9da63094ab6f28807e949e651e629336470d5"
)
EXPECTED_ENVIRONMENT_SHA256 = (
    "72372974368a4a2b66cba42fa48baae47e24bf811a8b2dd030027ea3b7f16363"
)
EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256 = (
    "db88dcc6d47c270566bb8a6218f3238bc9be8e03db9f8d14147b9fa6639f7279"
)
EXPECTED_HELD_OUT_CONTRACT_SHA256 = (
    "351f6257d79f7e4704eb02da128697da58ae1916e1e5a1bedb1a8e60ef18103d"
)
EXPECTED_PROMPT_CONTRACT_SHA256 = (
    "c01ed3c8188cda44f798b01f449c9b07b7df6ccb00d75606ab01d1177a24d229"
)
EXPECTED_ADAPTER_SHA256 = (
    "db428e3c891166e43c1c71df7902e6fb579959f19c300cafe7ae8dcfe2dd2a70"
)
EXPECTED_BASE_MODEL_ID = "Qwen/Qwen3-1.7B-Base"
EXPECTED_BASE_MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
EXPECTED_RUN_NAME = "qwen3-1.7b-peano-lora-v3-library"
EXPECTED_SEED = 20_260_728
EXPECTED_SEARCH_LIMITS: Mapping[str, int] = {
    "beam_width": 16,
    "candidates_per_state": 8,
    "max_depth": 32,
    "max_model_calls": 512,
    "max_states": 4096,
}
EXPECTED_PROOFS: tuple[Mapping[str, object], ...] = (
    {
        "goal_index": 0,
        "name": "closed_arithmetic_seven",
        "statement": "0 · 0 + 3 + (0 · 1 + 1) + (3 + 0) = 7",
        "commands": ["norm_num"],
        "proof_nodes": 98,
    },
    {
        "goal_index": 1,
        "name": "existential_subtraction_two",
        "statement": "∃ x. 7 = x + 2",
        "commands": ["exists 5", "norm_num"],
        "proof_nodes": 29,
    },
    {
        "goal_index": 2,
        "name": "double_right_zero",
        "statement": "∀ x. x + 0 + 0 = x",
        "commands": ["intro n", "rewrite PA3", "simp"],
        "proof_nodes": 10,
    },
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ATTESTATION_CLI = Path("scripts/attest_peano_v3_paired_evaluation.py")


class PairedEvaluationAttestationError(ValueError):
    """Raised when any pinned input or pairwise binding is invalid."""


@dataclass(frozen=True)
class _Snapshot:
    path: Path
    record: dict[str, object]
    raw: bytes
    sha256: str

    def identity(self) -> dict[str, object]:
        return {
            "path": str(self.path.resolve()),
            "bytes": len(self.raw),
            "sha256": self.sha256,
            "canonical_record_sha256": _canonical_sha256(self.record),
        }


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _reject_constant(value: str) -> None:
    raise PairedEvaluationAttestationError(
        f"JSON contains the non-finite constant {value!r}"
    )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    record: dict[str, object] = {}
    for key, value in pairs:
        if key in record:
            raise PairedEvaluationAttestationError(
                f"JSON contains duplicate object key {key!r}"
            )
        record[key] = value
    return record


def _snapshot(
    path: Path,
    *,
    expected_bytes: int,
    expected_sha256: str,
    label: str,
) -> _Snapshot:
    if not path.is_file() or path.is_symlink():
        raise PairedEvaluationAttestationError(
            f"{label} is not one regular, non-symlink file"
        )
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != expected_bytes or digest != expected_sha256:
        raise PairedEvaluationAttestationError(
            f"{label} bytes differ from the pinned artifact"
        )
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PairedEvaluationAttestationError(
            f"{label} is not strict UTF-8 JSON"
        ) from exc
    if type(value) is not dict:
        raise PairedEvaluationAttestationError(f"{label} must be one JSON object")
    return _Snapshot(path=path, record=value, raw=raw, sha256=digest)


def _mapping(value: object, label: str) -> dict[str, object]:
    if type(value) is not dict:
        raise PairedEvaluationAttestationError(f"{label}: expected one object")
    return value


def _array(value: object, label: str, *, length: int | None = None) -> list[object]:
    if type(value) is not list:
        raise PairedEvaluationAttestationError(f"{label}: expected one array")
    if length is not None and len(value) != length:
        raise PairedEvaluationAttestationError(
            f"{label}: expected exactly {length} entries"
        )
    return value


def _at(record: Mapping[str, object], path: Sequence[str], label: str) -> object:
    value: object = record
    for key in path:
        value = _mapping(value, label).get(key)
    return value


def _require_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected or type(actual) is not type(expected):
        raise PairedEvaluationAttestationError(f"{label} differs")


def _validate_self_hash(
    attestation: Mapping[str, object], expected: str, label: str
) -> None:
    embedded = attestation.get("attestation_sha256")
    _require_equal(embedded, expected, f"{label} embedded self-hash")
    core = {
        key: value
        for key, value in attestation.items()
        if key != "attestation_sha256"
    }
    _require_equal(
        _canonical_sha256(core), embedded, f"{label} canonical self-hash"
    )


def _goal_shell(goal: object, label: str) -> dict[str, object]:
    record = _mapping(goal, label)
    return {
        key: deepcopy(record.get(key))
        for key in (
            "name",
            "statement",
            "allowed_theorems",
            "classical",
            "environment_sha256",
            "surface_profile",
        )
    }


def _job_from_report(report: Mapping[str, object], label: str) -> dict[str, object]:
    return _mapping(
        _at(
            report,
            ("policy_identity", "base_policy", "provenance", "evaluation", "job"),
            label,
        ),
        label,
    )


def _validate_job(
    job: Mapping[str, object], *, evaluation_job_id: str, label: str
) -> None:
    _require_equal(job.get("scheduler"), "slurm", f"{label} scheduler")
    _require_equal(job.get("job_id"), evaluation_job_id, f"{label} job id")
    submission = _mapping(job.get("submission"), f"{label} submission")
    _require_equal(
        submission.get("job_id"), evaluation_job_id, f"{label} submitted job id"
    )
    _require_equal(
        submission.get("dependency_job_id"),
        EXPECTED_TRAINING_JOB_ID,
        f"{label} training dependency",
    )
    _require_equal(
        submission.get("git_commit"), EXPECTED_SOURCE_COMMIT, f"{label} source"
    )
    source_sync = _mapping(
        _at(job, ("deployment", "source_sync"), f"{label} source sync"),
        f"{label} source sync",
    )
    _require_equal(source_sync.get("status"), "synced", f"{label} sync status")
    _require_equal(source_sync.get("git_dirty"), False, f"{label} dirty source")
    _require_equal(
        source_sync.get("git_commit"), EXPECTED_SOURCE_COMMIT, f"{label} synced source"
    )


def _validated_repository_path(value: object, label: str) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise PairedEvaluationAttestationError(f"{label}: invalid repository path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.parts[0] == ".git"
        or any(ord(character) < 32 for character in value)
    ):
        raise PairedEvaluationAttestationError(f"{label}: unsafe repository path")
    return value


def _git_blob(path: str) -> bytes:
    """Read one validated historical blob without invoking a shell."""

    try:
        completed = subprocess.run(
            ["git", "cat-file", "blob", f"{EXPECTED_SOURCE_COMMIT}:{path}"],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PairedEvaluationAttestationError(
            f"cannot read historical source blob {path!r}"
        ) from exc
    if completed.returncode != 0:
        raise PairedEvaluationAttestationError(
            f"historical source blob {path!r} is unavailable at the pinned commit"
        )
    return completed.stdout


def _source_map(
    value: object, *, label: str, expected_count: int
) -> dict[str, str]:
    record = _mapping(value, label)
    files = _mapping(record.get("files"), f"{label} files")
    if len(files) != expected_count:
        raise PairedEvaluationAttestationError(
            f"{label}: expected exactly {expected_count} files"
        )
    normalized: dict[str, str] = {}
    for raw_path, raw_digest in files.items():
        path = _validated_repository_path(raw_path, f"{label} path")
        if (
            type(raw_digest) is not str
            or len(raw_digest) != 64
            or any(character not in "0123456789abcdef" for character in raw_digest)
        ):
            raise PairedEvaluationAttestationError(
                f"{label}: invalid digest for {path!r}"
            )
        normalized[path] = raw_digest
    _require_equal(
        _canonical_sha256(normalized), record.get("sha256"), f"{label} map hash"
    )
    return normalized


def _historical_script(
    job: Mapping[str, object], *, label: str
) -> tuple[dict[str, str], dict[str, str]]:
    deployment = _mapping(job.get("deployment"), f"{label} deployment")
    job_script = _mapping(deployment.get("job_script"), f"{label} job script")
    support = _mapping(deployment.get("support_script"), f"{label} support script")
    nested_support = _mapping(
        job_script.get("support_script"), f"{label} nested support script"
    )
    _require_equal(nested_support, support, f"{label} support-script declarations")
    return (
        {
            "path": _validated_repository_path(
                job_script.get("path"), f"{label} job script path"
            ),
            "sha256": job_script.get("file_sha256"),
        },
        {
            "path": _validated_repository_path(
                support.get("path"), f"{label} support script path"
            ),
            "sha256": support.get("sha256"),
        },
    )


def _validate_historical_sources(
    trained_report: Mapping[str, object],
    pretrained_report: Mapping[str, object],
    trained_job: Mapping[str, object],
    pretrained_job: Mapping[str, object],
) -> dict[str, object]:
    maps = {
        "trained_semantic": _source_map(
            _at(
                trained_report,
                ("evaluator", "semantic_sources"),
                "trained semantic sources",
            ),
            label="trained semantic sources",
            expected_count=36,
        ),
        "pretrained_semantic": _source_map(
            _at(
                pretrained_report,
                ("evaluator", "semantic_sources"),
                "pretrained semantic sources",
            ),
            label="pretrained semantic sources",
            expected_count=36,
        ),
        "trained_evaluation": _source_map(
            _at(
                trained_report,
                (
                    "policy_identity",
                    "base_policy",
                    "provenance",
                    "evaluation",
                    "sources",
                ),
                "trained evaluation sources",
            ),
            label="trained evaluation sources",
            expected_count=61,
        ),
        "pretrained_evaluation": _source_map(
            _at(
                pretrained_report,
                (
                    "policy_identity",
                    "base_policy",
                    "provenance",
                    "evaluation",
                    "sources",
                ),
                "pretrained evaluation sources",
            ),
            label="pretrained evaluation sources",
            expected_count=62,
        ),
    }
    by_path: dict[str, set[str]] = {}
    occurrences: dict[str, int] = {}
    for source_map in maps.values():
        for path, digest in source_map.items():
            by_path.setdefault(path, set()).add(digest)
            occurrences[path] = occurrences.get(path, 0) + 1
    conflicts = [path for path, digests in by_path.items() if len(digests) != 1]
    if conflicts:
        raise PairedEvaluationAttestationError(
            "historical source maps disagree on overlapping paths"
        )
    for path, digests in sorted(by_path.items()):
        actual = hashlib.sha256(_git_blob(path)).hexdigest()
        _require_equal(actual, next(iter(digests)), f"historical blob {path}")

    trained_script, trained_support = _historical_script(
        trained_job, label="trained"
    )
    pretrained_script, pretrained_support = _historical_script(
        pretrained_job, label="pretrained"
    )
    _require_equal(
        trained_support, pretrained_support, "paired historical support script"
    )
    scripts = {
        "trained_slurm": trained_script,
        "pretrained_slurm": pretrained_script,
        "shared_support": trained_support,
    }
    for label, script in scripts.items():
        digest = script.get("sha256")
        if type(digest) is not str or len(digest) != 64:
            raise PairedEvaluationAttestationError(
                f"{label}: invalid historical script digest"
            )
        actual = hashlib.sha256(_git_blob(script["path"])).hexdigest()
        _require_equal(actual, digest, f"{label} historical blob")
    return {
        "commit": EXPECTED_SOURCE_COMMIT,
        "maps": {label: len(source_map) for label, source_map in maps.items()},
        "unique_source_blobs_verified": len(by_path),
        "overlapping_source_paths": sum(
            count > 1 for count in occurrences.values()
        ),
        "all_overlap_digests_agree": True,
        "all_declared_source_blobs_verified_with_git_cat_file": True,
        "historical_scripts": scripts,
        "historical_script_blobs_verified": len(scripts),
    }


def _manifest_authority(manifest: Mapping[str, object]) -> dict[str, object]:
    base = _mapping(manifest.get("base_model"), "training manifest base model")
    adapter = _mapping(manifest.get("adapter"), "training manifest adapter")
    run = _mapping(manifest.get("run"), "training manifest run")
    inputs = _mapping(manifest.get("inputs"), "training manifest inputs")
    dataset = _mapping(inputs.get("dataset_attestation"), "dataset attestation")
    runtime_job = _mapping(
        _at(manifest, ("runtime", "job"), "training manifest job"),
        "training manifest job",
    )
    _require_equal(
        runtime_job.get("job_id"), EXPECTED_TRAINING_JOB_ID, "training job id"
    )
    _require_equal(
        _at(inputs, ("preparation_verification", "source_commit"), "manifest source"),
        EXPECTED_SOURCE_COMMIT,
        "training source commit",
    )
    authority = {
        "training_manifest_sha256": EXPECTED_TRAINING_MANIFEST_SHA256,
        "base_model_id": base.get("id"),
        "base_model_revision": base.get("resolved_snapshot_hash"),
        "base_model_config_sha256": base.get("config_sha256"),
        "adapter": {"root": adapter.get("root"), "sha256": adapter.get("sha256")},
        "run_name": run.get("name"),
        "environment": deepcopy(dataset.get("inference_environment")),
        "held_out_contract": deepcopy(dataset.get("held_out_contract")),
        "held_out_contract_sha256": dataset.get("held_out_contract_sha256"),
        "prompt_version": manifest.get("prompt_version"),
        "prompt_contract_sha256": manifest.get("prompt_contract_sha256"),
    }
    expected = {
        "training_manifest_sha256": EXPECTED_TRAINING_MANIFEST_SHA256,
        "base_model_id": EXPECTED_BASE_MODEL_ID,
        "base_model_revision": EXPECTED_BASE_MODEL_REVISION,
        "base_model_config_sha256": (
            "a325c9f27de176887b8ca7f68d21714247f9c8106e8c120219789338da9a5dcd"
        ),
        "adapter": {"root": "adapter", "sha256": EXPECTED_ADAPTER_SHA256},
        "run_name": EXPECTED_RUN_NAME,
        "environment": authority["environment"],
        "held_out_contract": authority["held_out_contract"],
        "held_out_contract_sha256": EXPECTED_HELD_OUT_CONTRACT_SHA256,
        "prompt_version": 3,
        "prompt_contract_sha256": EXPECTED_PROMPT_CONTRACT_SHA256,
    }
    _require_equal(authority, expected, "training manifest authority")
    _require_equal(
        _canonical_sha256(authority["environment"]),
        EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256,
        "manifest environment record hash",
    )
    return authority


def _trained_pairing_authority(
    report: Mapping[str, object], attestation: Mapping[str, object]
) -> dict[str, object]:
    base_policy = _mapping(
        _at(report, ("policy_identity", "base_policy"), "trained base policy"),
        "trained base policy",
    )
    provenance = _mapping(base_policy.get("provenance"), "trained provenance")
    legacy_environment = _mapping(
        base_policy.get("environment"), "trained legacy environment"
    )
    reconstruction = _mapping(
        _at(attestation, ("compatibility", "reconstruction"), "reconstruction"),
        "reconstruction",
    )
    fields = _mapping(reconstruction.get("fields"), "reconstructed fields")
    full_environment = {**deepcopy(legacy_environment), **deepcopy(fields)}
    _require_equal(
        _canonical_sha256(full_environment),
        reconstruction.get("complete_environment_record_sha256"),
        "trained reconstructed environment hash",
    )
    _require_equal(
        _canonical_sha256(full_environment),
        EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256,
        "trained complete environment",
    )
    return {
        "training_manifest_sha256": provenance.get("training_manifest_sha256"),
        "base_model_id": provenance.get("base_model_id"),
        "base_model_revision": provenance.get("base_model_revision"),
        "adapter_sha256": provenance.get("adapter_sha256"),
        "run_name": provenance.get("run_name"),
        "environment": full_environment,
        "environment_sha256": provenance.get("environment_sha256"),
        "held_out_contract_sha256": provenance.get("held_out_contract_sha256"),
        "prompt_version": provenance.get("prompt_version"),
        "prompt_contract_sha256": provenance.get("prompt_contract_sha256"),
    }


def _pretrained_pairing_authority(report: Mapping[str, object]) -> dict[str, object]:
    comparison = _mapping(
        report.get("pretrained_base_comparison"), "pretrained comparison authority"
    )
    embedded = comparison.get("comparison_authority_sha256")
    core = {
        key: value
        for key, value in comparison.items()
        if key != "comparison_authority_sha256"
    }
    _require_equal(
        _canonical_sha256(core), embedded, "pretrained comparison authority self-hash"
    )
    base = _mapping(comparison.get("base_model"), "comparison base model")
    adapter = _mapping(comparison.get("adapter"), "comparison adapter")
    environment = _mapping(comparison.get("environment"), "comparison environment")
    return {
        "training_manifest_sha256": comparison.get("training_manifest_sha256"),
        "base_model_id": base.get("id"),
        "base_model_revision": base.get("revision"),
        "base_model_config_sha256": base.get("config_sha256"),
        "adapter": deepcopy(adapter),
        "run_name": comparison.get("comparison_run_name"),
        "environment": deepcopy(environment),
        "environment_sha256": environment.get("environment_sha256"),
        "held_out_contract": deepcopy(comparison.get("held_out_contract")),
        "held_out_contract_sha256": comparison.get("held_out_contract_sha256"),
        "prompt_version": comparison.get("prompt_version"),
        "prompt_contract_sha256": comparison.get("prompt_contract_sha256"),
    }


def _validate_trained_proofs(
    report: Mapping[str, object], attestation: Mapping[str, object]
) -> list[dict[str, object]]:
    proofs = _array(attestation.get("proofs"), "trained attested proofs", length=3)
    report_goals = _array(report.get("goals"), "trained report goals", length=4)
    search_goals = _array(
        _at(report, ("search", "goals"), "trained search goals"),
        "trained search goals",
        length=4,
    )
    admitted: list[dict[str, object]] = []
    for proof_value, expected in zip(proofs, EXPECTED_PROOFS, strict=True):
        proof = _mapping(proof_value, "trained proof")
        for key in ("goal_index", "name", "commands", "proof_nodes"):
            _require_equal(proof.get(key), expected[key], f"trained proof {key}")
        _require_equal(proof.get("theorem"), expected["statement"], "proof theorem")
        replay = _mapping(proof.get("replay"), "trained proof replay")
        _require_equal(replay.get("kernel_checked"), True, "kernel replay flag")
        _require_equal(replay.get("status"), "proved", "kernel replay status")
        _require_equal(replay.get("theorem"), expected["statement"], "replay theorem")
        _require_equal(
            replay.get("proof_nodes"), expected["proof_nodes"], "replay proof nodes"
        )
        goal_index = expected["goal_index"]
        goal = _mapping(report_goals[goal_index], "trained proved goal")
        attempt = _mapping(
            _array(goal.get("attempts"), "trained attempts", length=1)[0],
            "trained proof attempt",
        )
        _require_equal(attempt.get("status"), "proof", "report proof status")
        _require_equal(attempt.get("commands"), expected["commands"], "report commands")
        _require_equal(
            attempt.get("proof_nodes"), expected["proof_nodes"], "report proof nodes"
        )
        search_goal = _mapping(search_goals[goal_index], "trained search goal")
        search_result = _mapping(search_goal.get("result"), "trained search result")
        _require_equal(search_result.get("status"), "proof", "search proof status")
        _require_equal(
            search_result.get("commands"), expected["commands"], "search commands"
        )
        _require_equal(
            search_result.get("certificate_nodes"),
            expected["proof_nodes"],
            "search certificate nodes",
        )
        admitted.append(
            {
                "goal_index": goal_index,
                "name": expected["name"],
                "statement": expected["statement"],
                "commands": deepcopy(expected["commands"]),
                "proof_nodes": expected["proof_nodes"],
                "kernel_replayed": True,
            }
        )
    return admitted


def _validate_summaries(
    trained_report: Mapping[str, object],
    pretrained_report: Mapping[str, object],
    trained_attestation: Mapping[str, object],
    pretrained_attestation: Mapping[str, object],
) -> None:
    trained_summary = {
        "attempts": 4,
        "claimed_proofs": 3,
        "kernel_replayed_proofs": 3,
        "proved_goals": 3,
        "pass@k": 0.75,
        "status_counts": {"failing": 1, "invalid": 0, "limit": 0, "proof": 3},
    }
    pretrained_summary = {
        "attempts": 4,
        "claimed_proofs": 0,
        "kernel_replayed_proofs": 0,
        "proved_goals": 0,
        "pass@k": 0.0,
        "status_counts": {"failing": 4, "invalid": 0, "limit": 0, "proof": 0},
    }
    _require_equal(
        trained_attestation.get("summary"),
        trained_summary,
        "trained attestation summary",
    )
    _require_equal(
        pretrained_attestation.get("summary"),
        pretrained_summary,
        "pretrained attestation summary",
    )
    for report, proved, fraction, counts, label in (
        (trained_report, 3, 0.75, trained_summary["status_counts"], "trained"),
        (pretrained_report, 0, 0.0, pretrained_summary["status_counts"], "pretrained"),
    ):
        _require_equal(report.get("attempt_count"), 4, f"{label} attempt count")
        _require_equal(report.get("proved_goals"), proved, f"{label} proved goals")
        _require_equal(report.get("pass@k"), fraction, f"{label} solve fraction")
        _require_equal(report.get("status_counts"), counts, f"{label} status counts")

    _require_equal(pretrained_attestation.get("proofs"), [], "pretrained proof claims")
    goals = _array(pretrained_report.get("goals"), "pretrained goals", length=4)
    for goal_value in goals:
        goal = _mapping(goal_value, "pretrained goal")
        _require_equal(goal.get("passed"), False, "pretrained passed flag")
        attempt = _mapping(
            _array(goal.get("attempts"), "pretrained attempts", length=1)[0],
            "pretrained attempt",
        )
        _require_equal(attempt.get("status"), "failing", "pretrained attempt status")
        _require_equal(attempt.get("commands"), [], "pretrained proof commands")
        _require_equal(attempt.get("proof_nodes"), None, "pretrained proof nodes")


def _validate_pairing_records(
    *,
    trained_report: Mapping[str, object],
    pretrained_report: Mapping[str, object],
    trained_attestation: Mapping[str, object],
    pretrained_attestation: Mapping[str, object],
    training_manifest: Mapping[str, object],
) -> dict[str, object]:
    """Validate semantic cross-bindings after byte admission.

    Kept separate from byte preflight so tests can demonstrate that a direct
    trained/control mismatch is rejected by the binding logic itself.
    """

    _require_equal(
        trained_attestation.get("format"),
        "peano-policy-v3-historical-evaluation-replay",
        "trained producer format",
    )
    _require_equal(
        pretrained_attestation.get("format"),
        "peano-policy-v3-pretrained-baseline-replay",
        "pretrained producer format",
    )
    _require_equal(trained_attestation.get("status"), "passed", "trained replay status")
    _require_equal(
        pretrained_attestation.get("status"), "passed", "pretrained replay status"
    )

    manifest_authority = _manifest_authority(training_manifest)
    trained_authority = _trained_pairing_authority(
        trained_report, trained_attestation
    )
    pretrained_authority = _pretrained_pairing_authority(pretrained_report)

    direct_bindings = {
        "training_manifest_sha256": pretrained_authority["training_manifest_sha256"],
        "base_model_id": pretrained_authority["base_model_id"],
        "base_model_revision": pretrained_authority["base_model_revision"],
        "adapter_sha256": _mapping(
            pretrained_authority["adapter"], "pretrained adapter"
        ).get("sha256"),
        "run_name": pretrained_authority["run_name"],
        "environment": pretrained_authority["environment"],
        "environment_sha256": pretrained_authority["environment_sha256"],
        "held_out_contract_sha256": pretrained_authority[
            "held_out_contract_sha256"
        ],
        "prompt_version": pretrained_authority["prompt_version"],
        "prompt_contract_sha256": pretrained_authority[
            "prompt_contract_sha256"
        ],
    }
    _require_equal(
        trained_authority,
        direct_bindings,
        "pretrained comparison authority versus trained provenance",
    )
    _require_equal(
        pretrained_authority["base_model_config_sha256"],
        manifest_authority["base_model_config_sha256"],
        "comparison base config versus manifest",
    )
    _require_equal(
        pretrained_authority["adapter"],
        manifest_authority["adapter"],
        "comparison adapter versus manifest",
    )
    _require_equal(
        {
            key: pretrained_authority[key]
            for key in (
                "training_manifest_sha256",
                "base_model_id",
                "base_model_revision",
                "run_name",
                "environment",
                "held_out_contract",
                "held_out_contract_sha256",
                "prompt_version",
                "prompt_contract_sha256",
            )
        },
        {
            key: manifest_authority[key]
            for key in (
                "training_manifest_sha256",
                "base_model_id",
                "base_model_revision",
                "run_name",
                "environment",
                "held_out_contract",
                "held_out_contract_sha256",
                "prompt_version",
                "prompt_contract_sha256",
            )
        },
        "paired authority versus training manifest",
    )

    trained_job = _job_from_report(trained_report, "trained evaluation job")
    pretrained_job = _job_from_report(pretrained_report, "pretrained evaluation job")
    _validate_job(
        trained_job,
        evaluation_job_id=EXPECTED_TRAINED_EVALUATION_JOB_ID,
        label="trained evaluation",
    )
    _validate_job(
        pretrained_job,
        evaluation_job_id=EXPECTED_PRETRAINED_EVALUATION_JOB_ID,
        label="pretrained evaluation",
    )
    historical_sources = _validate_historical_sources(
        trained_report,
        pretrained_report,
        trained_job,
        pretrained_job,
    )
    for attestation, job_id, label in (
        (trained_attestation, EXPECTED_TRAINED_EVALUATION_JOB_ID, "trained"),
        (pretrained_attestation, EXPECTED_PRETRAINED_EVALUATION_JOB_ID, "pretrained"),
    ):
        evaluation = _mapping(attestation.get("evaluation"), f"{label} evaluation")
        _require_equal(evaluation.get("job_id"), job_id, f"{label} attested job")
        _require_equal(
            evaluation.get("source_commit"),
            EXPECTED_SOURCE_COMMIT,
            f"{label} attested source",
        )
        _require_equal(
            evaluation.get("goal_set_sha256"),
            EXPECTED_GOAL_SET_SHA256,
            f"{label} attested goal set",
        )

    trained_input_container = _mapping(
        trained_attestation.get("input"), "trained input link"
    )
    trained_input = trained_input_container
    pretrained_input_container = _mapping(
        pretrained_attestation.get("input"), "pretrained input link"
    )
    pretrained_input = _mapping(
        pretrained_input_container.get("evaluation_report"),
        "pretrained evaluation-report input link",
    )
    for link, sha, size, canonical, label in (
        (
            trained_input,
            EXPECTED_TRAINED_REPORT_SHA256,
            EXPECTED_TRAINED_REPORT_BYTES,
            EXPECTED_TRAINED_REPORT_RECORD_SHA256,
            "trained",
        ),
        (
            pretrained_input,
            EXPECTED_PRETRAINED_REPORT_SHA256,
            EXPECTED_PRETRAINED_REPORT_BYTES,
            EXPECTED_PRETRAINED_REPORT_RECORD_SHA256,
            "pretrained",
        ),
    ):
        _require_equal(link.get("sha256"), sha, f"{label} report cross-link hash")
        _require_equal(link.get("bytes"), size, f"{label} report cross-link bytes")
        _require_equal(
            link.get("canonical_record_sha256"),
            canonical,
            f"{label} report cross-link record hash",
        )
    for link, label in (
        (
            _mapping(
                trained_input_container.get("training_manifest"),
                "trained manifest input link",
            ),
            "trained",
        ),
        (
            _mapping(
                pretrained_input_container.get("training_manifest"),
                "pretrained manifest input link",
            ),
            "pretrained",
        ),
    ):
        _require_equal(
            link.get("sha256"),
            EXPECTED_TRAINING_MANIFEST_SHA256,
            f"{label} training-manifest cross-link hash",
        )
        _require_equal(
            link.get("bytes"),
            EXPECTED_TRAINING_MANIFEST_BYTES,
            f"{label} training-manifest cross-link bytes",
        )

    _require_equal(
        _at(
            trained_attestation,
            ("compatibility_replay_authority", "training_manifest", "manifest_sha256"),
            "trained producer manifest authority",
        ),
        EXPECTED_TRAINING_MANIFEST_SHA256,
        "trained producer manifest authority",
    )
    _require_equal(
        _at(
            trained_attestation,
            (
                "compatibility_replay_authority",
                "training_manifest",
                "base_model",
                "weight_shards_content_hashed",
            ),
            "trained producer base-weight scope",
        ),
        False,
        "trained producer base-weight scope",
    )
    _require_equal(
        _at(
            pretrained_attestation,
            ("admission", "base_weight_shards_content_attested"),
            "pretrained producer base-weight scope",
        ),
        False,
        "pretrained producer base-weight scope",
    )
    _require_equal(
        _at(
            pretrained_attestation,
            ("pretrained_base", "base_weight_shards_content_attested"),
            "pretrained base-weight scope",
        ),
        False,
        "pretrained base-weight scope",
    )
    _require_equal(
        _at(
            pretrained_attestation,
            ("pretrained_base", "adapter_attached"),
            "pretrained adapter attachment",
        ),
        False,
        "pretrained adapter attachment",
    )

    trained_goals = _array(trained_report.get("goals"), "trained goals", length=4)
    pretrained_goals = _array(
        pretrained_report.get("goals"), "pretrained goals", length=4
    )
    trained_shells = [
        _goal_shell(goal, f"trained goal {index}")
        for index, goal in enumerate(trained_goals)
    ]
    pretrained_shells = [
        _goal_shell(goal, f"pretrained goal {index}")
        for index, goal in enumerate(pretrained_goals)
    ]
    _require_equal(trained_shells, pretrained_shells, "paired frozen goals")
    goal_contract = _array(
        _mapping(
            manifest_authority["held_out_contract"], "manifest held-out contract"
        ).get("goals"),
        "manifest held-out goals",
        length=4,
    )
    compact_goals = [
        {"name": shell["name"], "statement": shell["statement"]}
        for shell in trained_shells
    ]
    _require_equal(
        compact_goals, goal_contract, "report goals versus held-out contract"
    )

    for report, label in (
        (trained_report, "trained"),
        (pretrained_report, "pretrained"),
    ):
        _require_equal(report.get("v"), 4, f"{label} evaluator version")
        _require_equal(report.get("goal_count"), 4, f"{label} goal count")
        _require_equal(
            report.get("goal_set_sha256"), EXPECTED_GOAL_SET_SHA256, f"{label} goals"
        )
        _require_equal(report.get("k"), 1, f"{label} k")
        _require_equal(report.get("seed"), EXPECTED_SEED, f"{label} seed")
        _require_equal(report.get("max_steps"), 32, f"{label} max steps")
        _require_equal(
            _at(report, ("search", "limits"), f"{label} search limits"),
            dict(EXPECTED_SEARCH_LIMITS),
            f"{label} search limits",
        )
        policy_identity = _mapping(report.get("policy_identity"), f"{label} policy")
        _require_equal(
            policy_identity.get("seed"), EXPECTED_SEED, f"{label} policy seed"
        )
        _require_equal(
            policy_identity.get("limits"),
            dict(EXPECTED_SEARCH_LIMITS),
            f"{label} policy limits",
        )
    for field in (
        "evaluator",
        "goal_set_sha256",
        "k",
        "max_steps",
        "mode",
        "judge",
        "seed",
    ):
        _require_equal(
            trained_report.get(field),
            pretrained_report.get(field),
            f"paired {field}",
        )
    _require_equal(
        _at(trained_report, ("search", "limits"), "trained search limits"),
        _at(pretrained_report, ("search", "limits"), "pretrained search limits"),
        "paired search limits",
    )
    _require_equal(
        _at(
            trained_report,
            ("policy_identity", "base_policy", "decoding"),
            "trained decoding",
        ),
        _at(
            pretrained_report,
            ("policy_identity", "base_policy", "decoding"),
            "pretrained decoding",
        ),
        "paired decoding",
    )
    def attempt_seed(goal: object) -> object:
        attempts = _array(
            _mapping(goal, "goal").get("attempts"), "attempts", length=1
        )
        return _mapping(attempts[0], "attempt").get("seed")

    trained_attempt_seeds = [attempt_seed(goal) for goal in trained_goals]
    pretrained_attempt_seeds = [attempt_seed(goal) for goal in pretrained_goals]
    _require_equal(
        trained_attempt_seeds, pretrained_attempt_seeds, "paired per-goal seeds"
    )

    _validate_summaries(
        trained_report,
        pretrained_report,
        trained_attestation,
        pretrained_attestation,
    )
    proofs = _validate_trained_proofs(trained_report, trained_attestation)
    return {
        "authority": {
            "training_manifest_sha256": EXPECTED_TRAINING_MANIFEST_SHA256,
            "base_model": {
                "id": EXPECTED_BASE_MODEL_ID,
                "revision": EXPECTED_BASE_MODEL_REVISION,
                "config_sha256": manifest_authority["base_model_config_sha256"],
            },
            "comparison_adapter": deepcopy(manifest_authority["adapter"]),
            "run_name": EXPECTED_RUN_NAME,
            "environment_sha256": EXPECTED_ENVIRONMENT_SHA256,
            "environment_record_sha256": EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256,
            "held_out_contract_sha256": EXPECTED_HELD_OUT_CONTRACT_SHA256,
            "prompt_version": 3,
            "prompt_contract_sha256": EXPECTED_PROMPT_CONTRACT_SHA256,
        },
        "benchmark": {
            "goal_set_sha256": EXPECTED_GOAL_SET_SHA256,
            "goals": compact_goals,
            "seed": EXPECTED_SEED,
            "k": 1,
            "search_limits": dict(EXPECTED_SEARCH_LIMITS),
        },
        "proofs": proofs,
        "producer_records": {
            "training_job_id": EXPECTED_TRAINING_JOB_ID,
            "trained_evaluation_job_id": EXPECTED_TRAINED_EVALUATION_JOB_ID,
            "pretrained_evaluation_job_id": EXPECTED_PRETRAINED_EVALUATION_JOB_ID,
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "trained_job_record_sha256": _canonical_sha256(trained_job),
            "pretrained_job_record_sha256": _canonical_sha256(pretrained_job),
            "historical_sources": historical_sources,
        },
    }


def _attestation_sources() -> Mapping[str, object]:
    return source_files_identity(
        (
            Path(__file__),
            REPOSITORY_ROOT / ATTESTATION_CLI,
            REPOSITORY_ROOT / "training" / "peano_policy" / "runtime.py",
        )
    )


def attest_paired_evaluation(
    *,
    trained_attestation_path: Path,
    pretrained_attestation_path: Path,
    trained_report_path: Path,
    pretrained_report_path: Path,
    training_manifest_path: Path,
) -> dict[str, object]:
    """Admit the exact paired launch smoke and return a self-hashed record."""

    sources_before = _attestation_sources()
    specifications = (
        (
            "trained_attestation",
            trained_attestation_path,
            EXPECTED_TRAINED_ATTESTATION_BYTES,
            EXPECTED_TRAINED_ATTESTATION_FILE_SHA256,
            "trained replay attestation",
        ),
        (
            "pretrained_attestation",
            pretrained_attestation_path,
            EXPECTED_PRETRAINED_ATTESTATION_BYTES,
            EXPECTED_PRETRAINED_ATTESTATION_FILE_SHA256,
            "pretrained replay attestation",
        ),
        (
            "trained_report",
            trained_report_path,
            EXPECTED_TRAINED_REPORT_BYTES,
            EXPECTED_TRAINED_REPORT_SHA256,
            "trained evaluation report",
        ),
        (
            "pretrained_report",
            pretrained_report_path,
            EXPECTED_PRETRAINED_REPORT_BYTES,
            EXPECTED_PRETRAINED_REPORT_SHA256,
            "pretrained evaluation report",
        ),
        (
            "training_manifest",
            training_manifest_path,
            EXPECTED_TRAINING_MANIFEST_BYTES,
            EXPECTED_TRAINING_MANIFEST_SHA256,
            "training manifest",
        ),
    )
    snapshots = {
        name: _snapshot(
            path,
            expected_bytes=size,
            expected_sha256=sha,
            label=label,
        )
        for name, path, size, sha, label in specifications
    }
    trained_attestation = snapshots["trained_attestation"].record
    pretrained_attestation = snapshots["pretrained_attestation"].record
    _validate_self_hash(
        trained_attestation,
        EXPECTED_TRAINED_ATTESTATION_SHA256,
        "trained replay attestation",
    )
    _validate_self_hash(
        pretrained_attestation,
        EXPECTED_PRETRAINED_ATTESTATION_SHA256,
        "pretrained replay attestation",
    )
    pairing = _validate_pairing_records(
        trained_report=snapshots["trained_report"].record,
        pretrained_report=snapshots["pretrained_report"].record,
        trained_attestation=trained_attestation,
        pretrained_attestation=pretrained_attestation,
        training_manifest=snapshots["training_manifest"].record,
    )

    sources_after = _attestation_sources()
    _require_equal(sources_after, sources_before, "paired attestation source snapshot")
    for name, path, size, sha, label in specifications:
        final = _snapshot(
            path,
            expected_bytes=size,
            expected_sha256=sha,
            label=label,
        )
        _require_equal(final.raw, snapshots[name].raw, f"{label} reread")

    core: dict[str, object] = {
        "format": REPORT_FORMAT,
        "v": REPORT_VERSION,
        "status": "passed",
        "result": ADMITTED_RESULT,
        "inputs": {
            name: snapshots[name].identity()
            for name in (
                "training_manifest",
                "trained_report",
                "trained_attestation",
                "pretrained_report",
                "pretrained_attestation",
            )
        },
        "pairing": {
            "authority": pairing["authority"],
            "benchmark": pairing["benchmark"],
            "same_goals_seed_search_limits": True,
            "training_manifest_and_provenance_cross_bound": True,
            "source_and_jobs_cross_bound": True,
        },
        "observed_result": {
            "metric": "observed_solve_fraction_at_k_1",
            "k": 1,
            "denominator": 4,
            "trained": {
                "solved": 3,
                "solve_fraction": 0.75,
                "kernel_replayed_proofs": 3,
            },
            "pretrained_comparison": {
                "solved": 0,
                "solve_fraction": 0.0,
                "proof_claims": 0,
            },
            "trained_minus_pretrained_solved": 3,
            "trained_minus_pretrained_solve_fraction": 0.75,
        },
        "trained_proofs": pairing["proofs"],
        "producer_attribution": {
            **pairing["producer_records"],
            "basis": "byte-pinned-historical-producer-source-job-records",
            "producer_attestation_self_hashes_verified": True,
            "producer_input_cross_links_verified": True,
            "paired_layer_replayed_raw_model_outputs": False,
            "model_output_transcripts_present_in_reports": False,
            "reason_raw_outputs_not_replayed": (
                "the immutable reports do not contain complete raw "
                "model-output transcripts"
            ),
            "trained_certificates_kernel_replayed_by_consumed_attestation": 3,
            "paired_layer_kernel_replay_count": 0,
        },
        "claim_scope": {
            "scope": "one frozen four-goal paired launch smoke at k=1",
            "bit_for_bit_base_weight_identity_attested": False,
            "statistical_capability_claim": False,
            "broad_theorem_proving_capability_claim": False,
            "induction_capability_claim": False,
            "causal_training_effect_claim": False,
            "simultaneous_job_execution_claim": False,
            "allowed_interpretation": (
                "under the byte-pinned declared producer records and shared smoke "
                "conditions, the trained run solved 3 of 4 goals and the pretrained "
                "comparison solved 0 of 4"
            ),
        },
        "attestation_authority": {
            "sources": sources_before,
            "tool_sources_checked_before_and_after": True,
            "all_inputs_checked_before_and_after": True,
        },
    }
    return {**core, "attestation_sha256": _canonical_sha256(core)}


__all__ = [
    "ADMITTED_RESULT",
    "EXPECTED_PRETRAINED_EVALUATION_JOB_ID",
    "EXPECTED_SOURCE_COMMIT",
    "EXPECTED_TRAINED_EVALUATION_JOB_ID",
    "EXPECTED_TRAINING_JOB_ID",
    "PairedEvaluationAttestationError",
    "REPORT_FORMAT",
    "REPORT_VERSION",
    "attest_paired_evaluation",
]
