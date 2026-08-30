"""Digest-bound Alpha post-training, independent of the historical model-v3.

The old 247-theorem adapter has a deliberately incompatible attestor.  This
module therefore establishes its own checked Hydra authority instead of
weakening, impersonating, or bypassing that historical contract.  Every source
route is replayed again before it can become a training example.  The frozen
historical benchmark and every complete contaminated lineage are excluded from
both training and training-time validation.

Model weights are imported only by an explicit ``--execute`` invocation.  A
preflight can run on an ordinary laptop without CUDA or ML dependencies.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
for _import_root in (
    REPOSITORY_ROOT,
    REPOSITORY_ROOT / "peano-lab" / "py",
    REPOSITORY_ROOT / "scripts",
):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from peano_lab.kernel.formulas import (  # noqa: E402
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from training.peano_hydra.curriculum import (  # noqa: E402
    CURRICULUM_SCHEMA,
    MAX_DATASET_BYTES,
    MAX_PROMPT_BYTES,
    MAX_TRANSITIONS,
    PREFERENCE_SCHEMA,
    TRANSITION_SCHEMA,
    VerifiedCurriculum,
    encode_jsonl,
)
from training.peano_hydra.epoch import (  # noqa: E402
    EPOCH_SCHEMA,
    HydraEpoch,
    HydraEpochError,
    freeze_epoch,
)
from training.peano_policy.config import (  # noqa: E402
    ExperimentConfig,
    load_config,
    validate_config,
)
from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_HELD_OUT_POLICY_GOALS,
    held_out_contract_sha256,
)
from training.peano_policy.prompt import (  # noqa: E402
    COMPLETION_SUFFIX,
    PEANO_PROMPT_V1,
    CapabilityIdentity,
    ParsedPrompt,
    PromptEnvironment,
    PromptError,
    ProofExample,
    _safe_text as _prompt_safe_text,
    parse_prompt,
    render_prompt,
    validate_completion,
)
from training.peano_policy.search import state_sha256  # noqa: E402
from training.peano_policy.runtime import (  # noqa: E402
    deployment_identity,
    requirements_identity,
    runtime_identity,
    slurm_job_identity,
)


PREPARATION_SCHEMA = "peano-hydra-posttrain-preparation-v1"
EXAMPLE_SCHEMA = "peano-hydra-posttrain-example-v1"
QUARANTINE_SCHEMA = "peano-hydra-posttrain-quarantine-v1"
DISCOVERY_PROVENANCE_SCHEMA = "peano-hydra-posttrain-discovery-provenance-v1"
ADAPTER_SCHEMA = "peano-hydra-posttrain-adapter-v1"
AUTHORITY_PREPARATION_SCHEMA = "peano-hydra-posttrain-preparation-v2"
AUTHORITY_EXAMPLE_SCHEMA = "peano-hydra-posttrain-example-v2"
FRONTIER_EXAMPLE_SCHEMA = "peano-hydra-frontier-posttrain-reference-v1"
MAX_FRONTIER_MANIFEST_BYTES = 4 * 1024**2
AUTHORITY_ADAPTER_SCHEMA = "peano-hydra-posttrain-adapter-v2"
AUTHORITY_PREFLIGHT_SCHEMA = "peano-hydra-posttrain-preflight-v2"
AUTHORITY_SPLIT_POLICY = "declared-whole-composition-families-v1"
AUTHORITY_METADATA_FIELDS = (
    "authority_profile",
    "prompt_contract",
    "decoder_profile",
    "authority",
    "exposure",
    "composition",
)
AUTHORITY_PREPARATION_FIELDS = (*AUTHORITY_METADATA_FIELDS, "curriculum_identity")
RUNTIME_LOCK_SCHEMA = "peano-hydra-posttrain-runtime-lock-v1"
SPLIT_POLICY = "source-lineages-then-first-clean-lineage-held-for-dev-v1"
BASE_MODEL_ID = "Qwen/Qwen3-1.7B-Base"
BASE_MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
HISTORICAL_CHECKED_THEOREMS = 247
TEMPLATE_PATH = (
    REPOSITORY_ROOT
    / "training"
    / "peano_hydra"
    / "configs"
    / "qwen3_1_7b_alpha_posttrain.toml"
)
SOURCE_FILENAMES = (
    "epoch.json",
    "sft.jsonl",
    "preferences.jsonl",
    "discovery.jsonl",
    "manifest.json",
)
OUTPUT_FILENAMES = (
    "train.jsonl",
    "dev.jsonl",
    "preferences.jsonl",
    "discovery.jsonl",
    "quarantine.jsonl",
    "config.toml",
    "manifest.json",
)
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_CONFIGURATION_BYTES = 64 * 1024
MAX_SEQUENCE_TOKENS = 8_192
MAX_TRAIN_TOKENS = 32_000_000
MAX_DEV_TOKENS = 4_000_000
MAX_TRAIN_SQUARED_TOKENS = 100_000_000_000
MAX_DEV_SQUARED_TOKENS = 16_000_000_000
MAX_OPTIMIZER_STEPS = 2_048
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_RUN_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")


class HydraPosttrainError(ValueError):
    """The proposed model run escaped its checked Alpha or benchmark boundary."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise HydraPosttrainError(f"duplicate JSON field {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> object:
    raise HydraPosttrainError(f"non-finite JSON value {value!r}")


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise HydraPosttrainError(f"post-training evidence is not strict JSON: {error}") from None


def _pretty(value: object) -> bytes:
    try:
        return (
            json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2)
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise HydraPosttrainError(f"post-training evidence is not strict JSON: {error}") from None


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _decode(raw: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise HydraPosttrainError(f"{label} is not one strict JSON object: {error}") from None
    if type(value) is not dict:
        raise HydraPosttrainError(f"{label} must contain one JSON object")
    return value


def _read(path: Path, *, label: str, maximum: int = MAX_SOURCE_BYTES) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise HydraPosttrainError(f"{label} must be one real regular file")
    try:
        before = path.stat()
        if before.st_size > maximum:
            raise HydraPosttrainError(f"{label} exceeds its explicit byte bound")
        payload = path.read_bytes()
        after = path.stat()
    except OSError as error:
        raise HydraPosttrainError(f"cannot read {label}: {error}") from error
    if (
        len(payload) != before.st_size
        or len(payload) > maximum
        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    ):
        raise HydraPosttrainError(f"{label} changed while it was being read")
    return payload


def _rows(raw: bytes, *, label: str) -> tuple[dict[str, object], ...]:
    if raw and not raw.endswith(b"\n"):
        raise HydraPosttrainError(f"{label} must end with a complete JSONL row")
    result: list[dict[str, object]] = []
    for number, line in enumerate(raw.splitlines(), 1):
        if not line or len(line) > MAX_PROMPT_BYTES:
            raise HydraPosttrainError(f"{label} row {number} is empty or exceeds its byte bound")
        result.append(_decode(line, f"{label} row {number}"))
        if len(result) > MAX_TRANSITIONS:
            raise HydraPosttrainError(f"{label} exceeds its exact row bound")
    return tuple(result)


def _statement(source: str) -> str:
    if type(source) is not str or not source:
        raise HydraPosttrainError("a supervised theorem has no exact statement")
    try:
        formula, names = parse_formula_with_names(source)
    except (ParseError, TypeError, ValueError, RecursionError) as error:
        raise HydraPosttrainError(f"a supervised theorem is not a PA formula: {error}") from None
    if names:
        raise HydraPosttrainError("a supervised theorem is not a closed formula")
    return pretty_formula(formula, [])


def _directory(path: Path, *, label: str) -> Path:
    value = path.expanduser().absolute()
    if value.is_symlink() or not value.is_dir():
        raise HydraPosttrainError(f"{label} must be one real directory")
    return value


def _file_record(payload: bytes, *, rows: int | None = None) -> dict[str, object]:
    result: dict[str, object] = {"bytes": len(payload), "sha256": _sha256(payload)}
    if rows is not None:
        result["rows"] = rows
    return result


def _relative_or_absolute(path: Path) -> str:
    absolute = path.expanduser().absolute()
    try:
        return absolute.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return str(absolute)


@dataclass(frozen=True, slots=True)
class VerifiedSource:
    """One complete curriculum re-created from independently replayed routes."""

    directory: Path
    epoch: HydraEpoch
    curriculum: VerifiedCurriculum
    manifest: dict[str, object]
    payloads: dict[str, bytes]


def _manifest_authority_profile(
    manifest: Mapping[str, object],
    *,
    legacy_schema: str = PREPARATION_SCHEMA,
    authority_schema: str = AUTHORITY_PREPARATION_SCHEMA,
) -> str | None:
    """Never infer a new model authority from a relabelled legacy artifact."""

    if manifest.get("schema") == legacy_schema:
        if any(field in manifest for field in AUTHORITY_PREPARATION_FIELDS):
            raise HydraPosttrainError("legacy evidence cannot claim the authority-aware profile")
        return None
    if manifest.get("schema") != authority_schema:
        raise HydraPosttrainError("post-training evidence has an unsupported schema")
    from training.peano_policy.authority import AUTHORITY_PRIMITIVE_PROFILE

    if manifest.get("authority_profile") != AUTHORITY_PRIMITIVE_PROFILE:
        raise HydraPosttrainError("post-training evidence has an unsupported authority profile")
    if any(field not in manifest for field in AUTHORITY_METADATA_FIELDS):
        raise HydraPosttrainError("authority-aware evidence lost its exact source metadata")
    return AUTHORITY_PRIMITIVE_PROFILE


def _source_authority_environment(source: VerifiedSource) -> PromptEnvironment | None:
    """Read the separately replayed teacher authority, never the row's claim."""

    if source.manifest.get("schema") == CURRICULUM_SCHEMA:
        if any(field in source.manifest for field in AUTHORITY_METADATA_FIELDS):
            raise HydraPosttrainError("catalog evidence cannot claim a teacher authority")
        return None
    from training.peano_hydra.composition import COMPOSITION_SCHEMA
    from training.peano_hydra.composition_scale import SCALED_COMPOSITION_SCHEMA
    from training.peano_hydra.corrective_source import CORRECTIVE_SOURCE_SCHEMA
    from training.peano_hydra.frontier_curriculum import FRONTIER_SOURCE_SCHEMA
    from training.peano_policy.authority import (
        authority_contract_record,
        authority_profile_record,
    )
    from training.peano_policy.contract import authority_prompt_environment

    _manifest_authority_profile(
        source.manifest,
        legacy_schema=CURRICULUM_SCHEMA,
        authority_schema=(
            FRONTIER_SOURCE_SCHEMA
            if source.manifest.get("schema") == FRONTIER_SOURCE_SCHEMA
            else CORRECTIVE_SOURCE_SCHEMA
            if source.manifest.get("schema") == CORRECTIVE_SOURCE_SCHEMA
            else SCALED_COMPOSITION_SCHEMA
            if source.manifest.get("schema") == SCALED_COMPOSITION_SCHEMA
            else COMPOSITION_SCHEMA
        ),
    )
    authority = source.manifest["authority"]
    if (
        type(authority) is not dict
        or set(authority) != {"capabilities", "environment_sha256", "classical"}
        or authority["classical"] is not False
        or type(authority["capabilities"]) is not dict
        or set(authority["capabilities"])
        != {"label", "allowed_commands", "allowed_theorems"}
    ):
        raise HydraPosttrainError("teacher source has no exact finite intuitionistic authority")
    capabilities = authority["capabilities"]
    try:
        identity = CapabilityIdentity.from_record({
            field: capabilities[field]
            for field in ("label", "allowed_commands", "allowed_theorems")
        })
        if identity.allowed_commands is None or identity.allowed_theorems != ():
            raise HydraPosttrainError("compositional teachers require finite commands and no imports")
        environment = authority_prompt_environment(False, identity)
        if (
            authority["environment_sha256"] != environment.sha256
            or source.manifest["prompt_contract"] != authority_contract_record()
            or source.manifest["decoder_profile"] != authority_profile_record(environment)
        ):
            raise HydraPosttrainError("teacher prompt/decoder metadata changed its exact authority")
    except (PromptError, TypeError, ValueError) as error:
        raise HydraPosttrainError(f"invalid compositional teacher authority: {error}") from None
    for field in ("exposure", "composition"):
        if type(source.manifest[field]) is not dict:
            raise HydraPosttrainError(f"teacher source has no exact {field} identity")
    return environment


def _authority_metadata(source: VerifiedSource) -> dict[str, object]:
    """Return detached source metadata only for the independently checked profile."""

    if _source_authority_environment(source) is None:
        return {}
    return _decode(
        _canonical({field: source.manifest[field] for field in AUTHORITY_METADATA_FIELDS}),
        "compositional teacher metadata",
    )


def verify_source(source_directory: Path) -> VerifiedSource:
    """Re-run every advertised checked route and require exact source bytes."""

    directory = _directory(source_directory, label="Hydra source directory")
    manifest_raw = _read(directory / "manifest.json", label="Hydra source manifest.json")
    source_manifest = _decode(manifest_raw, "Hydra source manifest")
    if source_manifest.get("schema") != CURRICULUM_SCHEMA:
        from training.peano_hydra.composition import (
            COMPOSITION_SCHEMA,
            verify_composition_source,
        )
        from training.peano_hydra.composition_scale import (
            SCALED_COMPOSITION_SCHEMA,
            verify_scaled_composition_source,
        )
        from training.peano_hydra.corrective_source import (
            CORRECTIVE_SOURCE_SCHEMA,
            verify_corrective_source,
        )
        from training.peano_hydra.frontier_curriculum import FRONTIER_SOURCE_SCHEMA

        if source_manifest.get("schema") == FRONTIER_SOURCE_SCHEMA:
            from training.peano_hydra.scaling_admission import verify_admitted_frontier_source

            try:
                return verify_admitted_frontier_source(directory)
            except (OSError, TypeError, ValueError) as error:
                raise HydraPosttrainError(
                    f"reviewed frontier native-composition admission failed: {error}"
                ) from error

        if source_manifest.get("schema") == CORRECTIVE_SOURCE_SCHEMA:
            try:
                return verify_corrective_source(directory)
            except (OSError, TypeError, ValueError) as error:
                raise HydraPosttrainError(
                    f"independent corrective native-composition replay failed: {error}"
                ) from error

        if source_manifest.get("schema") == SCALED_COMPOSITION_SCHEMA:
            try:
                return verify_scaled_composition_source(directory)
            except (OSError, TypeError, ValueError) as error:
                raise HydraPosttrainError(
                    f"independent scaled native-composition replay failed: {error}"
                ) from error

        if source_manifest.get("schema") == COMPOSITION_SCHEMA:
            try:
                return verify_composition_source(directory)
            except (OSError, TypeError, ValueError) as error:
                raise HydraPosttrainError(
                    f"independent native-composition replay failed: {error}"
                ) from error
        raise HydraPosttrainError("Hydra source does not carry the checked curriculum schema")
    if any(field in source_manifest for field in AUTHORITY_METADATA_FIELDS):
        raise HydraPosttrainError("catalog evidence cannot impersonate a separate teacher authority")
    payloads = {
        name: manifest_raw if name == "manifest.json" else _read(directory / name, label=f"Hydra source {name}")
        for name in SOURCE_FILENAMES
    }
    catalog = source_manifest.get("catalog_training")
    if type(catalog) is not dict:
        raise HydraPosttrainError("Hydra source has no exact checked-catalog selection")
    names = catalog.get("theorem_names")
    if (
        type(names) is not list
        or any(type(name) is not str or not name for name in names)
        or len(names) != len(set(names))
        or catalog.get("checked_route_count") != len(names)
    ):
        raise HydraPosttrainError("Hydra source changed its exact checked route inventory")

    # This is the independent authority boundary: file hashes and a self-made
    # ``kernel_checked`` Boolean are never enough to authorize a model row.
    from prepare_peano_hydra import prepare

    try:
        epoch, curriculum, regenerated = prepare(
            catalog_limit=0,
            catalog_theorems=tuple(names),
        )
    except (HydraEpochError, OSError, TypeError, ValueError) as error:
        raise HydraPosttrainError(f"independent checked-catalog replay failed: {error}") from error

    epoch_document = _decode(payloads["epoch.json"], "Hydra source epoch")
    theorem_dag = epoch_document.get("theorem_dag")
    definition_dag = epoch_document.get("definition_dag")
    if type(theorem_dag) is not dict or type(definition_dag) is not dict:
        raise HydraPosttrainError("Hydra source lacks its distinct theorem and definition DAGs")
    has_theorems = "nodes" in theorem_dag
    has_definitions = "nodes" in definition_dag
    if has_theorems != has_definitions:
        raise HydraPosttrainError("Hydra source published only one of its frozen mathematical DAGs")
    if epoch_document != epoch.to_dict(include_graphs=has_theorems):
        raise HydraPosttrainError("Hydra source epoch differs from the current frozen release")
    if epoch_document.get("schema") != EPOCH_SCHEMA:
        raise HydraPosttrainError("Hydra source epoch has an unsupported schema")

    expected_files = {
        "sft.jsonl": encode_jsonl(curriculum.transitions),
        "preferences.jsonl": encode_jsonl(curriculum.preferences),
        "discovery.jsonl": encode_jsonl(curriculum.discoveries),
    }
    source_files = source_manifest.get("files")
    if type(source_files) is not dict:
        raise HydraPosttrainError("Hydra source manifest has no exact artifact inventory")
    for filename, expected in expected_files.items():
        actual = payloads[filename]
        if actual != expected:
            raise HydraPosttrainError(
                f"Hydra source {filename} differs from independently replayed proof evidence"
            )
        recorded = source_files.get(filename)
        rows = len(_rows(actual, label=f"Hydra source {filename}"))
        if recorded != _file_record(actual, rows=rows):
            raise HydraPosttrainError(f"Hydra source manifest changed the identity of {filename}")

    for key, expected in curriculum.manifest().items():
        if source_manifest.get(key) != expected:
            raise HydraPosttrainError(
                f"Hydra source manifest differs from independently checked {key} evidence"
            )
    for key in (
        "version",
        "edition_identity_sha256",
        "theorem_dag_sha256",
        "reviewed_definition_dag_sha256",
        "optimization",
        "discovery",
    ):
        if source_manifest.get(key) != regenerated.get(key):
            raise HydraPosttrainError(f"Hydra source changed its checked {key} identity")
    if (
        catalog.get("model_generated") is not False
        or catalog.get("research_claim_eligible") is not False
        or catalog.get("total_tactic_decisions")
        != regenerated["catalog_training"]["total_tactic_decisions"]
    ):
        raise HydraPosttrainError("Hydra source changed its checked catalog-route boundaries")
    historical = source_manifest.get("historical_model_authority")
    if (
        type(historical) is not dict
        or historical.get("frozen_checked_theorem_count") != HISTORICAL_CHECKED_THEOREMS
        or historical.get("silently_expanded") is not False
    ):
        raise HydraPosttrainError("Hydra source changed the immutable historical model authority")
    return VerifiedSource(directory, epoch, curriculum, source_manifest, payloads)


def _held_out_targets() -> tuple[tuple[str, str, str], ...]:
    targets = tuple(
        (name, _statement(source), _sha256(_statement(source).encode("utf-8")))
        for name, source in MODEL_V3_HELD_OUT_POLICY_GOALS
    )
    if len({canonical for _, canonical, _ in targets}) != len(targets):
        raise HydraPosttrainError("historical held-out goals contain duplicate canonical formulas")
    return targets


def _goal_target(goal: object) -> str | None:
    if type(goal) is not str or goal.count("⊢") != 1:
        raise HydraPosttrainError("a supervised proof state has no canonical goal target")
    target = goal.rsplit("⊢", 1)[1].strip()
    if not target:
        raise HydraPosttrainError("a supervised proof state has an empty goal target")
    if "?" in target:
        return None
    try:
        formula, names = parse_formula_with_names(target)
    except (ParseError, TypeError, ValueError, RecursionError) as error:
        raise HydraPosttrainError(f"a supervised goal target is malformed: {error}") from None
    return pretty_formula(formula, []) if not names else None


def _descendants(
    epoch: HydraEpoch,
    *,
    names: frozenset[str],
    statements: frozenset[str],
) -> frozenset[str]:
    excluded: set[str] = set()
    for theorem in epoch.theorems:
        if (
            theorem.name in names
            or _statement(theorem.statement) in statements
            or any(dependency in excluded for dependency in theorem.dependencies)
        ):
            excluded.add(theorem.name)
    return frozenset(excluded)


def _validated_prompt_completion(
    *,
    example_id: object,
    prompt: object,
    completion: object,
    environment_sha256: object,
) -> tuple[ParsedPrompt, str]:
    """ProofExample's exact validators, retaining the single parsed prompt.

    Transition validation also needs the parsed state and authority. Creating
    a throwaway ProofExample after parse_prompt repeated that full parse, and
    reading its tactic repeated completion validation. Reuse the same shared
    validators here; do not cache text, authority, or filesystem observations.
    Acceptance/rejection parity with ProofExample is regression-tested.
    """

    parsed = parse_prompt(prompt)
    _prompt_safe_text("example id", example_id)
    if environment_sha256 != parsed.environment_sha256:
        raise PromptError("example environment_sha256 does not match its stored prompt")
    return parsed, validate_completion(completion)


def _validate_transition(
    epoch: HydraEpoch,
    row: Mapping[str, object],
    *,
    authority_environment: PromptEnvironment | None = None,
) -> None:
    if (
        row.get("schema") != TRANSITION_SCHEMA
        or row.get("epoch_sha256") != epoch.epoch_sha256
        or row.get("kernel_checked") is not True
        or row.get("research_claim_eligible") is not False
        or type(row.get("lineage_sha256")) is not str
        or _SHA256.fullmatch(row["lineage_sha256"]) is None
        or row.get("split") not in {"train", "dev"}
    ):
        raise HydraPosttrainError("a source transition lacks checked frozen-epoch evidence")
    theorem = _statement(row.get("theorem"))
    name = row.get("theorem_name")
    if type(name) is not str or not name:
        raise HydraPosttrainError("a source transition has no exact theorem name")
    enrolled = epoch.theorem(name)
    if authority_environment is not None:
        from training.peano_policy.authority import (
            AUTHORITY_PRIMITIVE_PROFILE,
            validate_authority_tactic,
        )
        from training.peano_policy.prompt import PEANO_PROMPT_V4

        if (
            row.get("track") != "compositional_teacher"
            or row.get("source") != "independently_checked_native_composition_teacher"
            or row.get("authority_profile") != AUTHORITY_PRIMITIVE_PROFILE
            or type(row.get("family")) is not str
            or _RUN_ID.fullmatch(row["family"]) is None
            or enrolled is not None
            or authority_environment.classical is not False
            or authority_environment.capabilities.allowed_commands is None
            or authority_environment.capabilities.allowed_theorems != ()
        ):
            raise HydraPosttrainError("a teacher row escaped its separate finite no-import authority")
        expected_surface = authority_environment.capabilities.label
        expected_prompt_version = PEANO_PROMPT_V4
    elif row.get("track") == "proof_discovery":
        if enrolled is not None:
            raise HydraPosttrainError("an unadmitted discovery unexpectedly entered the Alpha DAG")
    elif enrolled is None or _statement(enrolled.statement) != theorem:
        raise HydraPosttrainError("a checked source row changed its enrolled theorem statement")
    if authority_environment is None:
        if "authority_profile" in row or row.get("track") == "compositional_teacher":
            raise HydraPosttrainError("a catalog row cannot opt into a separate teacher profile")
        expected_surface = epoch.surface_label
        expected_prompt_version = PEANO_PROMPT_V1
    goals = row.get("goals_before")
    if type(goals) is not list or not goals or any(type(goal) is not str for goal in goals):
        raise HydraPosttrainError("a source transition has no complete pre-tactic goal tuple")
    if row.get("state_sha256") != state_sha256(tuple(goals)):
        raise HydraPosttrainError("a source transition changed its complete proof state")
    action = row.get("action")
    if type(action) is not str or not action or row.get("completion") != action + COMPLETION_SUFFIX:
        raise HydraPosttrainError("a source transition changed its checked complete tactic")
    if row.get("action_head") != action.split(" ", 1)[0]:
        raise HydraPosttrainError("a source transition changed its checked tactic head")
    try:
        parsed, tactic = _validated_prompt_completion(
            example_id=f"{name}:{row.get('step')}:{row.get('state_sha256')}",
            prompt=row.get("prompt"),
            completion=row.get("completion"),
            environment_sha256=row.get("environment_sha256"),
        )
    except (PromptError, TypeError, ValueError) as error:
        raise HydraPosttrainError(f"a source transition has an invalid prompt/action: {error}") from None
    if (
        parsed.surface != expected_surface
        or parsed.classical is not False
        or parsed.prompt_version != expected_prompt_version
        or parsed.goals != tuple(goals)
        or parsed.focus != row.get("focus")
        or parsed.environment_sha256 != row.get("environment_sha256")
        or tactic != action
    ):
        raise HydraPosttrainError("a source prompt escaped its exact full-digest Alpha authority")
    if authority_environment is not None:
        try:
            if (
                row["environment_sha256"] != authority_environment.sha256
                or row["prompt"] != render_prompt(
                    goals=tuple(goals), focus=row["focus"], environment=authority_environment,
                )
                or validate_authority_tactic(action, authority_environment) != action
            ):
                raise HydraPosttrainError("a teacher action changed its exact primitive authority")
        except (PromptError, TypeError, ValueError) as error:
            raise HydraPosttrainError(f"invalid primitive teacher action: {error}") from None
    after = row.get("goals_after")
    if type(after) is not list or any(type(goal) is not str for goal in after):
        raise HydraPosttrainError("a source transition has no complete post-tactic goal tuple")


def _contamination(
    epoch: HydraEpoch,
    rows: tuple[dict[str, object], ...],
    *,
    authority_environment: PromptEnvironment | None = None,
) -> tuple[dict[str, set[str]], dict[str, set[str]], tuple[tuple[str, str, str], ...]]:
    targets = _held_out_targets()
    by_name = {name: canonical for name, canonical, _ in targets}
    by_statement = {canonical: name for name, canonical, _ in targets}
    # New-profile rows must have unenrolled names and empty theorem imports
    # (_validate_transition below). None can name a frozen-DAG descendant.
    # Keep the legacy catalog scan exact, and always check teacher formulas
    # and every pre/post goal against the historical targets themselves.
    excluded = (
        _descendants(
            epoch, names=frozenset(by_name), statements=frozenset(by_statement),
        )
        if authority_environment is None else frozenset()
    )
    reasons: dict[str, set[str]] = defaultdict(set)
    matches: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        _validate_transition(epoch, row, authority_environment=authority_environment)
        lineage = str(row["lineage_sha256"])
        name = str(row["theorem_name"])
        theorem = _statement(str(row["theorem"]))
        if name in by_name:
            reasons[lineage].add("historical-held-out-theorem-name")
            matches[lineage].add(name)
        if theorem in by_statement:
            reasons[lineage].add("historical-held-out-canonical-formula")
            matches[lineage].add(by_statement[theorem])
        if name in excluded:
            reasons[lineage].add("historical-held-out-checked-dag-descendant")
        for goal in [*row["goals_before"], *row["goals_after"]]:
            target = _goal_target(goal)
            if target in by_statement:
                reasons[lineage].add("historical-held-out-proof-goal")
                matches[lineage].add(by_statement[target])
    return dict(reasons), dict(matches), targets


def _split_lineages(
    rows: tuple[dict[str, object], ...],
    *,
    quarantined: frozenset[str],
    preserve_source_splits: bool = False,
) -> tuple[frozenset[str], frozenset[str]]:
    source_assignments: dict[str, str] = {}
    for row in rows:
        lineage = str(row["lineage_sha256"])
        previous = source_assignments.setdefault(lineage, str(row["split"]))
        if previous != row["split"]:
            raise HydraPosttrainError("one checked theorem lineage leaked between source splits")
    clean = set(source_assignments) - quarantined
    if len(clean) < 2:
        raise HydraPosttrainError(
            "post-training needs two clean checked lineages after complete benchmark quarantine; "
            "scale the Hydra catalog before preparing a model"
        )
    development = {
        lineage for lineage in clean if source_assignments[lineage] == "dev"
    }
    if not development:
        if preserve_source_splits:
            raise HydraPosttrainError("teacher preparation requires a declared whole-family dev split")
        development.add(min(clean))
    training = clean - development
    if not training:
        raise HydraPosttrainError("source development isolation leaves no clean training lineage")
    return frozenset(training), frozenset(development)


def _example(
    epoch: HydraEpoch,
    row: dict[str, object],
    *,
    split: str,
    authority_profile: str | None = None,
    source_manifest_sha256: str | None = None,
) -> dict[str, object]:
    result = {
        "schema": EXAMPLE_SCHEMA if authority_profile is None else AUTHORITY_EXAMPLE_SCHEMA,
        "epoch_sha256": epoch.epoch_sha256,
        "edition_identity_sha256": epoch.edition_identity_sha256,
        "theorem_name": row["theorem_name"],
        "theorem_statement_sha256": _sha256(_statement(str(row["theorem"])).encode("utf-8")),
        "lineage_sha256": row["lineage_sha256"],
        "split": split,
        "source_split": row["split"],
        "source_transition_sha256": _sha256(_canonical(row)),
        "state_sha256": row["state_sha256"],
        "action": row["action"],
        "prompt": row["prompt"],
        "completion": row["completion"],
        "environment_sha256": row["environment_sha256"],
        "kernel_checked": True,
        "transition": row,
    }
    if authority_profile is not None:
        result.update(authority_profile=authority_profile, family=row["family"])
    if source_manifest_sha256 is not None:
        from training.peano_policy.authority import AUTHORITY_PRIMITIVE_PROFILE
        if (authority_profile != AUTHORITY_PRIMITIVE_PROFILE
                or type(source_manifest_sha256) is not str
                or _SHA256.fullmatch(source_manifest_sha256) is None):
            raise HydraPosttrainError("frontier references need exact native source and primitive authority")
        result["schema"] = FRONTIER_EXAMPLE_SCHEMA
        result["source_manifest_sha256"] = source_manifest_sha256
        del result["transition"]
    return result


def _frontier_reference_index(source: VerifiedSource) -> tuple[str, dict[str, dict[str, object]]]:
    """Index the already freshly verified complete source, never caller rows."""
    from training.peano_hydra.frontier_curriculum import FRONTIER_SOURCE_SCHEMA
    if source.manifest.get("schema") != FRONTIER_SOURCE_SCHEMA:
        raise HydraPosttrainError("compact references belong only to a reviewed FRONTIER source")
    if not 1 <= len(source.curriculum.transitions) <= MAX_TRANSITIONS:
        raise HydraPosttrainError("frontier reference index exceeds its native row bound")
    index: dict[str, dict[str, object]] = {}
    for row in source.curriculum.transitions:
        if type(row) is not dict:
            raise HydraPosttrainError("frontier reference index lost its native transition")
        identity = _sha256(_canonical(row))
        if identity in index and index[identity] != row:
            raise HydraPosttrainError("frontier native transition identity is ambiguous")
        index[identity] = row
    return _sha256(source.payloads["manifest.json"]), index


def _resolve_frontier_example(source: VerifiedSource, example: dict[str, object], *,
                              split: str, index: tuple[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    """Require exact model-facing fields and a full-row native-source reference."""
    from training.peano_hydra.frontier_curriculum import FRONTIER_SOURCE_SCHEMA
    manifest_sha, transitions = index
    if (source.manifest.get("schema") != FRONTIER_SOURCE_SCHEMA
            or type(example) is not dict or example.get("schema") != FRONTIER_EXAMPLE_SCHEMA
            or example.get("source_manifest_sha256") != manifest_sha
            or type(example.get("source_transition_sha256")) is not str
            or "transition" in example or split not in {"train", "dev"}):
        raise HydraPosttrainError("frontier model row lost its exact source reference")
    transition = transitions.get(example["source_transition_sha256"])
    if transition is None or transition.get("split") != split:
        raise HydraPosttrainError("frontier model row references an unknown or foreign-split transition")
    expected = _example(source.epoch, transition, split=split,
                        authority_profile=source.manifest.get("authority_profile"),
                        source_manifest_sha256=manifest_sha)
    if _canonical(example) != _canonical(expected):
        raise HydraPosttrainError("frontier model fields differ from the freshly verified native transition")
    return transition


def _validate_teacher_partitions(rows: tuple[dict[str, object], ...]) -> None:
    """Keep all correlated seeds of each declared family in one source split."""

    families: dict[str, tuple[str, str]] = {}
    statements: dict[str, str] = {}
    for row in rows:
        family = str(row["family"])
        assignment = (str(row["lineage_sha256"]), str(row["split"]))
        if families.setdefault(family, assignment) != assignment:
            raise HydraPosttrainError("a compositional teacher family spans multiple lineages or splits")
        canonical = _statement(str(row["theorem"]))
        if statements.setdefault(canonical, str(row["split"])) != row["split"]:
            raise HydraPosttrainError("one canonical teacher formula appears in both exposed splits")


def _curriculum_identity(
    source: VerifiedSource,
    files: Mapping[str, object],
    splits: Mapping[str, object],
) -> dict[str, object]:
    record = {
        "method": "exact-composition-source-and-preparation-v1",
        "source_schema": source.manifest["schema"],
        "source_manifest_sha256": _sha256(source.payloads["manifest.json"]),
        "source_sft_sha256": _sha256(source.payloads["sft.jsonl"]),
        "train_sha256": files["train.jsonl"]["sha256"],
        "dev_sha256": files["dev.jsonl"]["sha256"],
        "split_policy": AUTHORITY_SPLIT_POLICY,
        "splits_sha256": _sha256(_canonical(splits)),
    }
    from training.peano_hydra.frontier_curriculum import FRONTIER_SOURCE_SCHEMA
    if source.manifest.get("schema") == FRONTIER_SOURCE_SCHEMA:
        from training.peano_hydra.scaling_admission import admission_identity

        record["review_admission"] = admission_identity(source.directory)
        record["projection_policy"] = "first-exact-epoch-environment-lineage-state-action-v1"
        record["dataset_schema"] = FRONTIER_EXAMPLE_SCHEMA
    return {**record, "sha256": _sha256(_canonical(record))}


def _validate_run_id(run_id: str | None) -> str | None:
    if run_id is not None and (
        type(run_id) is not str or _RUN_ID.fullmatch(run_id) is None
    ):
        raise HydraPosttrainError(
            "run-id must contain 1-64 lowercase letters, digits, hyphens, or underscores, "
            "starting with a letter or digit"
        )
    return run_id


def _config(
    epoch: HydraEpoch,
    *,
    output: Path,
    run_id: str | None = None,
    authority_profile: str | None = None,
) -> tuple[bytes, ExperimentConfig]:
    run_id = _validate_run_id(run_id)
    if authority_profile is not None:
        from training.peano_policy.authority import (
            AUTHORITY_PRIMITIVE_PROFILE,
            MAX_AUTHORITY_NEW_TOKENS,
        )

        if authority_profile != AUTHORITY_PRIMITIVE_PROFILE:
            raise HydraPosttrainError("post-training configuration has an unknown authority profile")
    template_raw = _read(
        TEMPLATE_PATH,
        label="reviewed Alpha post-training configuration template",
        maximum=MAX_CONFIGURATION_BYTES,
    )
    template = load_config(TEMPLATE_PATH)
    if (
        template.model.model_id != BASE_MODEL_ID
        or template.model.revision != BASE_MODEL_REVISION
        or template.curriculum is not None
    ):
        raise HydraPosttrainError("the Alpha post-training template changed its pinned Qwen authority")
    suffix = f"{epoch.version}-{epoch.epoch_sha256[:12]}"
    if run_id is not None:
        suffix += f"-{run_id}"
    if authority_profile is None:
        name = f"qwen3-1.7b-hydra-alpha-{suffix}"
        artifact_output = f"results/peano-hydra/qwen3-1.7b-alpha-{suffix}"
    else:
        name = f"qwen3-1.7b-hydra-authority-primitive-{suffix}"
        artifact_output = f"results/peano-hydra/qwen3-1.7b-authority-primitive-{suffix}"
    train = _relative_or_absolute(output / "train.jsonl")
    development = _relative_or_absolute(output / "dev.jsonl")
    substitutions = {
        'name = "qwen3-1.7b-hydra-alpha"': f"name = {json.dumps(name)}",
        'output_dir = "results/peano-hydra/qwen3-1.7b-alpha"': (
            f"output_dir = {json.dumps(artifact_output)}"
        ),
        'train_path = "_deploy/hydra-posttrain/train.jsonl"': (
            f"train_path = {json.dumps(train)}"
        ),
        'eval_path = "_deploy/hydra-posttrain/dev.jsonl"': (
            f"eval_path = {json.dumps(development)}"
        ),
    }
    if authority_profile is not None:
        substitutions['max_new_tokens = 256'] = f"max_new_tokens = {MAX_AUTHORITY_NEW_TOKENS}"
    text = template_raw.decode("utf-8")
    for old, new in substitutions.items():
        if text.count(old) != 1:
            raise HydraPosttrainError("the reviewed post-training template changed a required field")
        text = text.replace(old, new, 1)
    result = replace(
        template,
        path=(output / "config.toml").resolve(),
        run=replace(template.run, name=name, output_dir=artifact_output),
        data=replace(template.data, train_path=train, eval_path=development),
        generation=(
            template.generation if authority_profile is None
            else replace(template.generation, max_new_tokens=MAX_AUTHORITY_NEW_TOKENS)
        ),
    )
    validate_config(result)
    _validate_model_config(result)
    return text.encode("utf-8"), result


def _validate_model_config(config: ExperimentConfig) -> None:
    if (
        config.model.model_id != BASE_MODEL_ID
        or config.model.revision != BASE_MODEL_REVISION
        or config.model.dtype != "bfloat16"
        or config.model.attn_implementation != "sdpa"
        or config.model.trust_remote_code
        or config.curriculum is not None
        or config.run.resume != "never"
        or config.run.max_train_samples is not None
        or config.run.max_eval_samples is not None
        or config.trainer.epochs != 1.0
        or config.trainer.max_steps != -1
        or config.trainer.per_device_train_batch_size != 1
        or config.trainer.per_device_eval_batch_size != 1
        or not 1 <= config.trainer.gradient_accumulation_steps <= 64
        or not 128 <= config.data.max_length <= MAX_SEQUENCE_TOKENS
        or not 1 <= config.generation.max_new_tokens <= 512
        or config.run.output_dir.startswith("results/peano-policy/")
    ):
        raise HydraPosttrainError("Alpha post-training configuration escaped its bounded fresh-model contract")


@dataclass(frozen=True, slots=True)
class PreparedPosttraining:
    """Exact replayed rows with complete historical-four-goal quarantine."""

    source: VerifiedSource
    output_directory: Path
    train_rows: tuple[dict[str, object], ...]
    development_rows: tuple[dict[str, object], ...]
    quarantined_rows: tuple[dict[str, object], ...]
    payloads: dict[str, bytes]
    manifest: dict[str, object]
    config: ExperimentConfig


def prepare_posttraining(
    source_directory: Path,
    output_directory: Path,
    *,
    run_id: str | None = None,
) -> PreparedPosttraining:
    """Build a historically quarantined handoff without mutating the filesystem."""

    run_id = _validate_run_id(run_id)
    source = verify_source(source_directory)
    authority_environment = _source_authority_environment(source)
    authority_metadata = _authority_metadata(source)
    authority_profile = authority_metadata.get("authority_profile")
    from training.peano_hydra.frontier_curriculum import FRONTIER_SOURCE_SCHEMA
    frontier_projection = source.manifest.get("schema") == FRONTIER_SOURCE_SCHEMA
    frontier_example_keywords = ({"source_manifest_sha256": _sha256(source.payloads["manifest.json"])}
                                 if frontier_projection else {})
    output = output_directory.expanduser().absolute()
    if output == source.directory or output == REPOSITORY_ROOT:
        raise HydraPosttrainError("post-training output must be a separate dedicated directory")
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise HydraPosttrainError("post-training output must be a real dedicated directory")
    rows = source.curriculum.transitions
    reasons, matches, targets = _contamination(
        source.epoch, rows, authority_environment=authority_environment,
    )
    if authority_profile is not None:
        _validate_teacher_partitions(rows)
    quarantine_lineages = frozenset(reasons)
    train_lineages, development_lineages = _split_lineages(
        rows,
        quarantined=quarantine_lineages,
        preserve_source_splits=authority_profile is not None,
    )

    training: list[dict[str, object]] = []
    development: list[dict[str, object]] = []
    quarantined: dict[tuple[str, str, str], int] = defaultdict(int)
    projected_identities: set[str] = set()
    duplicate_rows: dict[str, int] = {"train": 0, "dev": 0}
    matched_source_names: set[str] = set()
    for row in rows:
        lineage = str(row["lineage_sha256"])
        if lineage in quarantine_lineages:
            key = (
                str(row["theorem_name"]),
                lineage,
                _sha256(_statement(str(row["theorem"])).encode("utf-8")),
            )
            quarantined[key] += 1
            matched_source_names.add(str(row["theorem_name"]))
            continue
        if lineage in train_lineages:
            split, examples = "train", training
        elif lineage in development_lineages:
            split, examples = "dev", development
        else:  # pragma: no cover - complete lineage partition above
            raise HydraPosttrainError("a source row escaped its complete clean/quarantine partition")
        if frontier_projection:
            # Keep complete native routes in the source. Only the new model-
            # facing FRONTIER projection removes exact repeated state/actions,
            # using the same identity and first-occurrence order as its shards.
            identity = _sha256(_canonical([
                row["epoch_sha256"], row["environment_sha256"],
                row["lineage_sha256"], row["state_sha256"], row["action"],
            ]))
            if identity in projected_identities:
                duplicate_rows[split] += 1
                continue
            projected_identities.add(identity)
        examples.append(_example(
            source.epoch, row, split=split, authority_profile=authority_profile,
            **frontier_example_keywords,
        ))

    if not training or not development:
        raise HydraPosttrainError("Alpha post-training needs nonempty safe train and dev splits")
    if (len(training) + len(development) + sum(quarantined.values())
            + sum(duplicate_rows.values()) != len(rows)):
        raise HydraPosttrainError("Alpha post-training lost a checked source transition")

    quarantine_records = tuple(
        {
            "schema": QUARANTINE_SCHEMA,
            "epoch_sha256": source.epoch.epoch_sha256,
            "theorem_name": name,
            "theorem_statement_sha256": statement,
            "lineage_sha256": lineage,
            "rows": count,
            "matched_goal_names": sorted(matches.get(lineage, set())),
            "reasons": sorted(reasons[lineage]),
        }
        for (name, lineage, statement), count in sorted(quarantined.items())
    )
    preferences = tuple(
        row
        for row in source.curriculum.preferences
        if row.get("schema") == PREFERENCE_SCHEMA
        and row.get("epoch_sha256") == source.epoch.epoch_sha256
        and row.get("lineage_sha256") in train_lineages
    )
    by_name = {
        str(row["theorem_name"]): str(row["lineage_sha256"])
        for row in rows
    }
    discoveries = tuple(
        {
            "schema": DISCOVERY_PROVENANCE_SCHEMA,
            "epoch_sha256": source.epoch.epoch_sha256,
            "name": record.get("name"),
            "theorem_statement_sha256": _sha256(
                _statement(str(record.get("theorem"))).encode("utf-8")
            ),
            "lineage_sha256": by_name.get(str(record.get("name"))),
            "kernel_checked": record.get("kernel_checked") is True,
            "quarantined": by_name.get(str(record.get("name"))) in quarantine_lineages,
            "model_training_exposed": False,
            "research_claim_eligible": False,
        }
        for record in source.curriculum.discoveries
    )
    config_bytes, config = _config(
        source.epoch, output=output, run_id=run_id, authority_profile=authority_profile,
    )
    payloads = {
        "train.jsonl": encode_jsonl(tuple(training)),
        "dev.jsonl": encode_jsonl(tuple(development)),
        "preferences.jsonl": encode_jsonl(preferences),
        "discovery.jsonl": encode_jsonl(discoveries),
        "quarantine.jsonl": encode_jsonl(quarantine_records),
        "config.toml": config_bytes,
    }
    if any(len(payload) > MAX_DATASET_BYTES for payload in payloads.values()):
        raise HydraPosttrainError("an Alpha post-training handoff exceeds its reviewed byte ceiling")
    file_records = {
        filename: _file_record(
            payload,
            rows=(
                len(_rows(payload, label=f"post-training {filename}"))
                if filename.endswith(".jsonl")
                else None
            ),
        )
        for filename, payload in payloads.items()
    }
    splits = {
        "train": {
            "rows": len(training),
            "lineages": sorted(train_lineages),
            "theorems": sorted({str(row["theorem_name"]) for row in training}),
        },
        "dev": {
            "rows": len(development),
            "lineages": sorted(development_lineages),
            "theorems": sorted({str(row["theorem_name"]) for row in development}),
        },
    }
    if authority_profile is not None:
        for split, examples in (("train", training), ("dev", development)):
            splits[split]["families"] = sorted({str(row["family"]) for row in examples})
            splits[split]["theorem_statement_sha256s"] = sorted({
                str(row["theorem_statement_sha256"]) for row in examples
            })
    source_identity = {
        "directory": _relative_or_absolute(source.directory),
        "manifest_sha256": _sha256(source.payloads["manifest.json"]),
        "epoch_file_sha256": _sha256(source.payloads["epoch.json"]),
        "sft_sha256": _sha256(source.payloads["sft.jsonl"]),
        "preferences_sha256": _sha256(source.payloads["preferences.jsonl"]),
        "discovery_sha256": _sha256(source.payloads["discovery.jsonl"]),
        "independently_replayed_catalog_routes": (
            len(source.manifest["catalog_training"]["theorem_names"])
            if authority_profile is None else 0
        ),
    }
    if authority_profile is not None:
        source_identity.update(
            schema=source.manifest["schema"],
            independently_replayed_teacher_routes=len({str(row["theorem_name"]) for row in rows}),
        )
    manifest: dict[str, object] = {
        "schema": PREPARATION_SCHEMA if authority_profile is None else AUTHORITY_PREPARATION_SCHEMA,
        "version": source.epoch.version,
        "epoch_sha256": source.epoch.epoch_sha256,
        "edition_identity_sha256": source.epoch.edition_identity_sha256,
        "theorem_dag_sha256": source.epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": source.epoch.reviewed_definition_dag_sha256,
        "surface_label": (
            source.epoch.surface_label if authority_environment is None
            else authority_environment.capabilities.label
        ),
        "model": {"model_id": BASE_MODEL_ID, "revision": BASE_MODEL_REVISION},
        "source": source_identity,
        "files": file_records,
        "split_policy": SPLIT_POLICY if authority_profile is None else AUTHORITY_SPLIT_POLICY,
        "splits": splits,
        "held_out": {
            "historical_v3_contract_sha256": held_out_contract_sha256(3),
            "excluded_goal_names": [name for name, _, _ in targets],
            "excluded_goal_statement_sha256s": [digest for _, _, digest in targets],
            "training_contamination_count": 0,
            "development_contamination_count": 0,
            "training_lineages": sorted(train_lineages),
            "development_lineages": sorted(development_lineages),
            "matched_source_theorems": sorted(matched_source_names),
            "quarantined_lineages": sorted(quarantine_lineages),
            "quarantine_rows": sum(quarantined.values()),
        },
        "historical_model_authority": source.manifest["historical_model_authority"],
        "resource_bounds": {
            "max_source_rows": MAX_TRANSITIONS,
            "max_sequence_tokens": MAX_SEQUENCE_TOKENS,
            "max_train_tokens": MAX_TRAIN_TOKENS,
            "max_dev_tokens": MAX_DEV_TOKENS,
            "max_train_squared_tokens": MAX_TRAIN_SQUARED_TOKENS,
            "max_dev_squared_tokens": MAX_DEV_SQUARED_TOKENS,
            "max_optimizer_steps": MAX_OPTIMIZER_STEPS,
            "cuda_devices": 1,
            "distributed_processes": 1,
            "epochs": 1,
        },
        "training": {
            "status": "prepared",
            "entrypoint": "training.peano_hydra.posttrain",
            "objective": "independently-checked-completion-only-bf16-lora-sft",
            "training_supported": True,
            "adapter_output_dir": config.run.output_dir,
            "consumed_artifacts": ["train.jsonl", "dev.jsonl"],
            "preferences_consumed": False,
            "discovery_consumed": False,
            "quarantine_consumed": False,
            "legacy_attestor_bypassed": False,
            "independent_alpha_attestation": True,
            "explicit_execute_required": True,
        },
        "model_trained": False,
        "research_claim_eligible": False,
        "alpha_admitted": False,
        "sealed_benchmark": False,
        "open_research_gates": list(source.manifest["open_research_gates"]),
    }
    if authority_profile is not None:
        manifest.update(authority_metadata)
        manifest["curriculum_identity"] = _curriculum_identity(source, file_records, splits)
        manifest["training"]["independent_alpha_attestation"] = False
        manifest["training"]["independent_composition_attestation"] = True
        manifest["held_out"].update(
            checked_dag_descendant_inventory_scanned=False,
            checked_dag_descendant_quarantine="not-applicable-unenrolled-no-import-teachers",
            canonical_historical_goals_checked=True,
            intermediate_historical_goals_checked=True,
            unseen_holdout_claim_eligible=False,
        )
    if frontier_projection:
        manifest["source_projection"] = {
            "policy": "first-exact-epoch-environment-lineage-state-action-v1",
            "raw_source_transitions": len(rows),
            "model_facing_transitions": len(training) + len(development),
            "quarantined_transitions": sum(quarantined.values()),
            "duplicate_transitions_removed": sum(duplicate_rows.values()),
            "duplicate_split_rows": duplicate_rows,
            "complete_native_source_preserved": True,
        }
    # Omit the optional field entirely for the original epoch-only run: its
    # already-published preparation and active adapter must retain exact bytes.
    if run_id is not None:
        manifest["run_id"] = run_id
    payloads["manifest.json"] = _canonical(manifest) + b"\n" if frontier_projection else _pretty(manifest)
    if frontier_projection and len(payloads["manifest.json"]) > MAX_FRONTIER_MANIFEST_BYTES:
        raise HydraPosttrainError("frontier preparation manifest exceeds existing 4 MiB origin/evaluation readers")
    return PreparedPosttraining(
        source,
        output,
        tuple(training),
        tuple(development),
        quarantine_records,
        payloads,
        manifest,
        config,
    )


def _write_atomic(path: Path, payload: bytes) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise HydraPosttrainError("post-training publication refuses links and non-regular files")
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise HydraPosttrainError("post-training publication target changed while being written")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _preparation_run_identity(manifest: dict[str, object]) -> tuple[object, ...]:
    """Read the immutable run destination without trusting malformed metadata."""

    authority_profile = _manifest_authority_profile(manifest)
    run_id = _validate_run_id(manifest.get("run_id"))
    if "run_id" in manifest and run_id is None:
        raise HydraPosttrainError("an explicit preparation run-id cannot be empty")
    version = manifest.get("version")
    digests = tuple(manifest.get(name) for name in (
        "epoch_sha256", "edition_identity_sha256", "theorem_dag_sha256",
        "reviewed_definition_dag_sha256",
    ))
    training = manifest.get("training")
    if (
        type(version) is not str or not version
        or any(type(digest) is not str or _SHA256.fullmatch(digest) is None for digest in digests)
        or type(training) is not dict
        or type(training.get("adapter_output_dir")) is not str
        or not training["adapter_output_dir"]
    ):
        raise HydraPosttrainError("existing preparation manifest has a malformed run identity")
    identity = (version, *digests, run_id, training["adapter_output_dir"])
    return identity if authority_profile is None else (*identity, authority_profile)


def _publish_authority_preparation(prepared: PreparedPosttraining) -> Path:
    """Publish a new-profile directory once; never repair existing payloads."""

    from training.peano_policy.manifest import publish_staged_directory_noreplace

    output = prepared.output_directory
    expected = prepared.manifest.get("files")
    if type(expected) is not dict or set(expected) != set(OUTPUT_FILENAMES) - {"manifest.json"}:
        raise HydraPosttrainError("teacher preparation changed its complete artifact inventory")
    for filename, identity in expected.items():
        payload = prepared.payloads[filename]
        actual = _file_record(
            payload,
            rows=len(_rows(payload, label=filename)) if filename.endswith(".jsonl") else None,
        )
        if identity != actual:
            raise HydraPosttrainError("teacher preparation payload changed before publication")
    if output.exists():
        if {item.name for item in output.iterdir()} != set(OUTPUT_FILENAMES):
            raise HydraPosttrainError("existing teacher preparation has a different artifact inventory")
        for filename in OUTPUT_FILENAMES:
            if _read(output / filename, label=f"existing teacher {filename}") != prepared.payloads[filename]:
                raise HydraPosttrainError("existing teacher preparation differs; use a fresh run directory")
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.partial-", dir=output.parent))
    for filename in OUTPUT_FILENAMES:
        _write_atomic(stage / filename, prepared.payloads[filename])
    publish_staged_directory_noreplace(stage, output)
    if load_config(output / "config.toml") != prepared.config:
        raise HydraPosttrainError("published teacher configuration changed its checked contract")
    return output


def publish_preparation(prepared: PreparedPosttraining) -> Path:
    """Atomically publish only the exact bounded, benchmark-safe handoff."""

    if type(prepared) is not PreparedPosttraining:
        raise TypeError("post-training publication needs one complete checked preparation")
    output = prepared.output_directory
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise HydraPosttrainError("post-training output must be one real dedicated directory")
    if set(prepared.payloads) != set(OUTPUT_FILENAMES):
        raise HydraPosttrainError("post-training publication changed its exact artifact inventory")
    incoming = _decode(prepared.payloads["manifest.json"], "prepared publication manifest")
    incoming_identity = _preparation_run_identity(incoming)
    if incoming != prepared.manifest:
        raise HydraPosttrainError("prepared publication manifest changed before publication")
    if _manifest_authority_profile(incoming) is not None:
        return _publish_authority_preparation(prepared)
    manifest_path = output / "manifest.json"
    if manifest_path.exists() or manifest_path.is_symlink():
        existing_raw = _read(manifest_path, label="existing preparation manifest")
        existing = _decode(
            existing_raw,
            "existing preparation manifest",
        )
        if _preparation_run_identity(existing) != incoming_identity:
            raise HydraPosttrainError(
                "refusing to overwrite a preparation for a different run identity; "
                "use a separate output directory"
            )
        if existing_raw != prepared.payloads["manifest.json"]:
            raise HydraPosttrainError(
                "existing preparation manifest differs from regenerated evidence; "
                "use a new run-id and separate output directory"
            )
    elif any((output / name).exists() or (output / name).is_symlink() for name in OUTPUT_FILENAMES):
        raise HydraPosttrainError(
            "existing preparation artifacts have no manifest; use a separate output directory"
        )
    output.mkdir(parents=True, exist_ok=True)
    for filename in OUTPUT_FILENAMES:
        _write_atomic(output / filename, prepared.payloads[filename])
    published = load_config(output / "config.toml")
    if published != prepared.config:
        raise HydraPosttrainError("published Alpha training configuration changed its checked contract")
    return output


def _source_path(record: object) -> Path:
    if type(record) is not str or not record:
        raise HydraPosttrainError("post-training manifest has no exact source directory")
    candidate = Path(record)
    return candidate if candidate.is_absolute() else REPOSITORY_ROOT / candidate


def load_preparation(directory: Path) -> PreparedPosttraining:
    """Revalidate published hashes and independently replay the entire source."""

    root = _directory(directory, label="Alpha post-training preparation")
    manifest_raw = _read(root / "manifest.json", label="Alpha post-training manifest")
    manifest = _decode(manifest_raw, "Alpha post-training manifest")
    _manifest_authority_profile(manifest)
    files = manifest.get("files")
    if type(files) is not dict or set(files) != set(OUTPUT_FILENAMES) - {"manifest.json"}:
        raise HydraPosttrainError("Alpha post-training manifest changed its artifact inventory")
    for filename, expected in files.items():
        if type(expected) is not dict:
            raise HydraPosttrainError(f"post-training file {filename!r} lacks a strict identity")
        payload = _read(root / filename, label=f"Alpha post-training {filename}")
        actual = _file_record(
            payload,
            rows=(
                len(_rows(payload, label=f"Alpha post-training {filename}"))
                if filename.endswith(".jsonl")
                else None
            ),
        )
        if actual != expected:
            raise HydraPosttrainError(f"Alpha post-training file {filename!r} changed its sealed bytes")
    source = manifest.get("source")
    if type(source) is not dict:
        raise HydraPosttrainError("Alpha post-training manifest has no independent source authority")
    prepared = prepare_posttraining(
        _source_path(source.get("directory")), root,
        run_id=manifest.get("run_id"),
    )
    if manifest_raw != prepared.payloads["manifest.json"]:
        raise HydraPosttrainError("post-training manifest differs from independently replayed evidence")
    for filename in set(OUTPUT_FILENAMES) - {"manifest.json"}:
        if _read(root / filename, label=f"Alpha post-training {filename}") != prepared.payloads[filename]:
            raise HydraPosttrainError(f"post-training {filename} differs from its independent replay")
    published_config = load_config(root / "config.toml")
    if published_config != prepared.config:
        raise HydraPosttrainError("published post-training configuration changed its exact authority")
    return prepared


def _preparation_authority_metadata(prepared: PreparedPosttraining) -> dict[str, object]:
    authority_profile = _manifest_authority_profile(prepared.manifest)
    source_metadata = _authority_metadata(prepared.source)
    if authority_profile != source_metadata.get("authority_profile"):
        raise HydraPosttrainError("prepared examples changed their independently replayed source profile")
    if authority_profile is not None and (
        any(prepared.manifest.get(field) != value for field, value in source_metadata.items())
        or prepared.manifest.get("surface_label")
        != source_metadata["authority"]["capabilities"]["label"]
        or prepared.manifest.get("curriculum_identity") != _curriculum_identity(
            prepared.source, prepared.manifest["files"], prepared.manifest["splits"],
        )
    ):
        raise HydraPosttrainError("prepared teacher examples changed their authority or exposure identity")
    if authority_profile is None:
        return {}
    return _decode(
        _canonical({field: prepared.manifest[field] for field in AUTHORITY_PREPARATION_FIELDS}),
        "prepared teacher authority metadata",
    )


def _adapter_profile_fields(prepared: PreparedPosttraining) -> dict[str, object]:
    """Exact additional publication fields for the new adapter, never a relabel."""

    metadata = _preparation_authority_metadata(prepared)
    return {
        "schema": AUTHORITY_ADAPTER_SCHEMA if metadata else ADAPTER_SCHEMA,
        **metadata,
    }


def _proof_examples(
    prepared: PreparedPosttraining,
    rows: tuple[dict[str, object], ...],
    *,
    split: str,
) -> tuple[ProofExample, ...]:
    authority_profile = _preparation_authority_metadata(prepared).get("authority_profile")
    authority_environment = _source_authority_environment(prepared.source)
    from training.peano_hydra.frontier_curriculum import FRONTIER_SOURCE_SCHEMA
    frontier = prepared.source.manifest.get("schema") == FRONTIER_SOURCE_SCHEMA
    reference_index = _frontier_reference_index(prepared.source) if frontier else None
    result: list[ProofExample] = []
    identities: set[str] = set()
    allowed = set(prepared.manifest["splits"][split]["lineages"])
    for position, row in enumerate(rows, 1):
        source = (_resolve_frontier_example(prepared.source, row, split=split, index=reference_index)
                  if frontier else row.get("transition"))
        if type(source) is not dict:
            raise HydraPosttrainError("an Alpha training row lost its independently replayed transition")
        if (
            row.get("schema") != (
                FRONTIER_EXAMPLE_SCHEMA if frontier
                else EXAMPLE_SCHEMA if authority_profile is None else AUTHORITY_EXAMPLE_SCHEMA
            )
            or row.get("epoch_sha256") != prepared.source.epoch.epoch_sha256
            or row.get("edition_identity_sha256") != prepared.source.epoch.edition_identity_sha256
            or row.get("split") != split
            or row.get("lineage_sha256") not in allowed
            or row.get("kernel_checked") is not True
            or row.get("source_transition_sha256") != _sha256(_canonical(source))
            or any(
                row.get(field) != source.get(field)
                for field in (
                    "theorem_name",
                    "lineage_sha256",
                    "state_sha256",
                    "action",
                    "prompt",
                    "completion",
                    "environment_sha256",
                )
            )
        ):
            raise HydraPosttrainError("an Alpha training example escaped its checked source binding")
        _validate_transition(
            prepared.source.epoch, source, authority_environment=authority_environment,
        )
        if authority_profile is not None and row != _example(
            prepared.source.epoch, source, split=split, authority_profile=authority_profile,
            **({"source_manifest_sha256": reference_index[0]} if frontier else {}),
        ):
            raise HydraPosttrainError("a teacher example differs from its exact checked transition")
        identifier = f"{split}:{position}:{row['source_transition_sha256']}"
        if identifier in identities:
            raise HydraPosttrainError("Alpha post-training contains a duplicate proof-example identity")
        identities.add(identifier)
        result.append(
            ProofExample(
                example_id=identifier,
                prompt=str(row["prompt"]),
                completion=str(row["completion"]),
                environment_sha256=str(row["environment_sha256"]),
            )
        )
    return tuple(result)


def preflight(directory: Path) -> dict[str, object]:
    """Audit every training input without importing torch or allocating CUDA."""

    prepared = load_preparation(directory)
    config = prepared.config
    _validate_model_config(config)
    train = _proof_examples(prepared, prepared.train_rows, split="train")
    development = _proof_examples(prepared, prepared.development_rows, split="dev")
    expected_steps = math.ceil(
        math.ceil(len(train) / config.trainer.per_device_train_batch_size)
        / config.trainer.gradient_accumulation_steps
    )
    if not 1 <= expected_steps <= MAX_OPTIMIZER_STEPS:
        raise HydraPosttrainError("Alpha optimizer schedule exceeds its reviewed hard bound")
    if (
        config.trainer.eval_steps <= expected_steps
        or config.trainer.save_steps <= expected_steps
    ):
        raise HydraPosttrainError("Alpha training forbids periodic checkpoint/evaluation exposure")
    output = _source_path(config.run.output_dir)
    if output.exists() or output.is_symlink():
        raise HydraPosttrainError("Alpha training requires a fresh epoch-bound adapter directory")
    held_out = prepared.manifest["held_out"]
    if (
        held_out.get("training_contamination_count") != 0
        or held_out.get("development_contamination_count") != 0
        or set(held_out["quarantined_lineages"])
        & (set(held_out["training_lineages"]) | set(held_out["development_lineages"]))
    ):
        raise HydraPosttrainError("a held-out benchmark lineage leaked into model exposure")
    result = {
        "schema": (
            "peano-hydra-posttrain-preflight-v1"
            if "authority_profile" not in prepared.manifest else AUTHORITY_PREFLIGHT_SCHEMA
        ),
        "epoch_sha256": prepared.source.epoch.epoch_sha256,
        "edition_identity_sha256": prepared.source.epoch.edition_identity_sha256,
        "surface_label": prepared.manifest["surface_label"],
        "model": prepared.manifest["model"],
        "training_rows": len(train),
        "development_rows": len(development),
        "quarantined_rows": held_out["quarantine_rows"],
        "expected_optimizer_steps": expected_steps,
        "required_pythonhashseed": str(config.run.seed),
        "adapter_output_dir": config.run.output_dir,
        "model_trained": False,
        "cuda_initialized": False,
        "historical_model_authority_changed": False,
        "research_claim_eligible": False,
        **({"run_id": prepared.manifest["run_id"]} if "run_id" in prepared.manifest else {}),
    }
    if "authority_profile" in prepared.manifest:
        result.update({field: prepared.manifest[field] for field in AUTHORITY_PREPARATION_FIELDS})
        result["preparation_manifest_sha256"] = _sha256(prepared.payloads["manifest.json"])
        result["token_budget_verified"] = False
        result["tokenizer_audit_required_before_model_weights"] = True
        result["unseen_holdout_claim_eligible"] = False
    return result


def _required_frameworks() -> None:
    missing = [
        name
        for name in ("torch", "transformers", "peft", "accelerate")
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        raise HydraPosttrainError(
            "explicit Alpha training needs the reviewed GPU environment; missing: "
            + ", ".join(missing)
        )


def _process_count() -> int:
    values: set[int] = set()
    for key in ("WORLD_SIZE", "LOCAL_WORLD_SIZE", "SLURM_NTASKS"):
        raw = os.environ.get(key)
        if raw is None:
            continue
        if not raw.isdecimal() or int(raw) < 1:
            raise HydraPosttrainError(f"{key} must declare one positive process count")
        values.add(int(raw))
    if values - {1}:
        raise HydraPosttrainError("Alpha training requires exactly one distributed process")
    return 1


def _finite_metrics(value: object) -> object:
    if type(value) is dict:
        return {str(key): _finite_metrics(item) for key, item in value.items()}
    if type(value) is list:
        return [_finite_metrics(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise HydraPosttrainError("Alpha model training produced a non-finite metric")
    return value


def _verify_runtime_lock(runtime: Mapping[str, object]) -> dict[str, object]:
    """Check the selected site lock without installing or importing ML packages.

    The historical runtime resolver owns safe lock selection, including the
    WMI overlay.  Its separately checked central Torch base must not be compared
    with Helios's different Torch pin.  PEP 508 markers are evaluated for this
    interpreter, and WMI's wheel hashes are retained through the lock digest.
    """

    identity = requirements_identity()
    if runtime.get("requirements") != identity:
        raise HydraPosttrainError("runtime and selected requirements lock disagree")
    required = any(
        os.environ.get(name) is not None
        for name in ("PEANO_HELIOS_ML_MODULE", "SLURM_JOB_ID")
    ) or os.environ.get("PEANO_CLUSTER_BACKEND") == "wmi"
    if not required:
        return {
            "schema": RUNTIME_LOCK_SCHEMA,
            "status": "not-required-local",
            "requirements": identity,
        }

    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.utils import canonicalize_name

    raw = _read(
        REPOSITORY_ROOT / identity["path"],
        label="selected training requirements lock",
        maximum=MAX_CONFIGURATION_BYTES,
    )
    if _sha256(raw) != identity["sha256"]:
        raise HydraPosttrainError("selected requirements lock changed before verification")
    packages = runtime.get("packages")
    if type(packages) is not dict:
        raise HydraPosttrainError("training runtime has no installed package inventory")
    installed = {canonicalize_name(name): version for name, version in packages.items()}
    checked: dict[str, str] = {}
    for line in raw.decode("utf-8").replace("\\\n", " ").splitlines():
        line = line.partition("#")[0].strip()
        if not line:
            continue
        line = re.sub(r"\s+--hash=sha256:[0-9a-f]{64}(?=\s|$)", "", line)
        try:
            requirement = Requirement(line)
        except InvalidRequirement as error:
            raise HydraPosttrainError(f"invalid reviewed requirements lock: {error}") from None
        specifiers = tuple(requirement.specifier)
        if (
            requirement.url is not None
            or requirement.extras
            or len(specifiers) != 1
            or specifiers[0].operator != "=="
            or "*" in specifiers[0].version
        ):
            raise HydraPosttrainError("reviewed requirements must use exact package-version pins")
        if requirement.marker is not None and not requirement.marker.evaluate():
            continue
        name = canonicalize_name(requirement.name)
        if name in checked:
            raise HydraPosttrainError(f"reviewed requirements repeat active package {name}")
        expected = specifiers[0].version
        actual = installed.get(name)
        if actual != expected:
            raise HydraPosttrainError(
                f"reviewed runtime package {name} requires {expected}; installed {actual!r}"
            )
        checked[name] = expected
    if not checked or requirements_identity() != identity:
        raise HydraPosttrainError("selected requirements lock is empty or changed during verification")
    return {
        "schema": RUNTIME_LOCK_SCHEMA,
        "status": "verified",
        "requirements": identity,
        "packages": dict(sorted(checked.items())),
        "packages_sha256": _sha256(_canonical(checked)),
    }


def _execution_provenance(torch_module: Any | None = None) -> dict[str, object]:
    """Bind the installed runtime to its exact source and submission ledger."""

    deployment = deployment_identity()
    job = slurm_job_identity()
    if job.get("deployment") != deployment:
        raise HydraPosttrainError("Alpha training source and Slurm deployment identities disagree")
    if deployment.get("mode") == "slurm":
        source = deployment.get("source_sync")
        if type(source) is not dict or source.get("git_dirty") is not False:
            raise HydraPosttrainError("scheduled Alpha training requires clean committed source")
    runtime = runtime_identity(torch_module)
    return {
        "runtime": runtime,
        "deployment": deployment,
        "job": job,
        "requirements_verification": _verify_runtime_lock(runtime),
    }


def _require_execution_provenance_unchanged(
    expected: Mapping[str, object],
    torch_module: Any | None = None,
) -> None:
    if _execution_provenance(torch_module) != expected:
        raise HydraPosttrainError("Alpha training runtime, source, or Slurm job changed during execution")


def execute(directory: Path) -> Path:
    """Actually train one fresh, checked, one-GPU BF16 completion-only adapter."""

    check = preflight(directory)
    prepared = load_preparation(directory)
    config = prepared.config
    if os.environ.get("PYTHONHASHSEED") != str(config.run.seed):
        raise HydraPosttrainError(
            f"explicit training requires PYTHONHASHSEED={config.run.seed} before Python starts"
        )
    # Reject stale sources, unrelated scheduler jobs, or package drift before
    # importing ML frameworks, loading weights, or claiming an output path.
    provenance = _execution_provenance()
    _required_frameworks()

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

    from training.peano_policy.budget import (
        enforce_token_budget,
        tokenize_split,
        tokenizer_identity_record,
    )
    from training.peano_policy.manifest import (
        ADAPTER_SUBDIR,
        TOKENIZER_SUBDIR,
        artifact_directory_hash,
        publish_staged_directory_noreplace,
        require_safetensors_adapter,
        write_manifest_noreplace,
    )
    from training.peano_policy.objective import (
        CompletionOnlyTrainerMixin,
        completion_objective_record,
        require_indexed_logits_support,
        single_process_trainer_runtime_record,
    )
    from training.peano_policy.train import (
        _CompletionCollator,
        _FiniteGradientCallbackMixin,
        _claim_fresh_output_directory,
        _require_output_directory_unchanged,
        _set_seeds,
        _trainable_tensor_population_snapshot,
    )
    from training.peano_policy.training_evidence import (
        FiniteGradientAudit,
        adapter_update_audit_record,
    )

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise HydraPosttrainError("explicit Alpha post-training requires exactly one CUDA GPU")
    if not torch.cuda.is_bf16_supported():
        raise HydraPosttrainError("the selected CUDA GPU does not support reviewed BF16 training")
    _process_count()
    _require_execution_provenance_unchanged(provenance)
    provenance = _execution_provenance(torch)
    _set_seeds(config.run.seed, torch, set_seed)

    train_examples = _proof_examples(prepared, prepared.train_rows, split="train")
    development_examples = _proof_examples(
        prepared,
        prepared.development_rows,
        split="dev",
    )
    tokenizer = AutoTokenizer.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        use_fast=True,
        trust_remote_code=False,
        local_files_only=True,
    )
    resolved_tokenizer = tokenizer.init_kwargs.get("_commit_hash") or config.model.revision
    if resolved_tokenizer != config.model.revision:
        raise HydraPosttrainError("the tokenizer resolved outside its immutable reviewed revision")
    if tokenizer.eos_token_id is None:
        raise HydraPosttrainError("the pinned Qwen tokenizer has no required EOS token")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    tokenizer_identity = tokenizer_identity_record(
        tokenizer,
        model_id=config.model.model_id,
        revision=config.model.revision,
    )
    train_features, train_tokens = tokenize_split(
        train_examples,
        tokenizer,
        role="train",
        max_length=config.data.max_length,
        tokenizer_identity=tokenizer_identity,
    )
    development_features, development_tokens = tokenize_split(
        development_examples,
        tokenizer,
        role="dev",
        max_length=config.data.max_length,
        tokenizer_identity=tokenizer_identity,
    )
    enforce_token_budget(
        train_tokens,
        max_total_tokens=MAX_TRAIN_TOKENS,
        max_sum_squared_tokens=MAX_TRAIN_SQUARED_TOKENS,
        max_supervised_tokens=config.generation.max_new_tokens,
    )
    enforce_token_budget(
        development_tokens,
        max_total_tokens=MAX_DEV_TOKENS,
        max_sum_squared_tokens=MAX_DEV_SQUARED_TOKENS,
        max_supervised_tokens=config.generation.max_new_tokens,
    )

    model = AutoModelForCausalLM.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        torch_dtype=torch.bfloat16,
        attn_implementation=config.model.attn_implementation,
        trust_remote_code=False,
        use_safetensors=True,
        local_files_only=True,
    )
    if (getattr(model.config, "_commit_hash", None) or config.model.revision) != config.model.revision:
        raise HydraPosttrainError("the base model resolved outside its immutable reviewed revision")
    require_indexed_logits_support(model)
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
    named_parameters = [
        (name, parameter)
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    ]
    initial = _trainable_tensor_population_snapshot(torch, named_parameters)
    gradient_audit = FiniteGradientAudit(
        expected_optimizer_steps=check["expected_optimizer_steps"],
        trainable_parameter_names=initial.names,
    )

    class CompletionTrainer(CompletionOnlyTrainerMixin, Trainer):
        """Existing exact indexed-logit completion-only objective."""

    class FiniteGradientCallback(_FiniteGradientCallbackMixin, TrainerCallback):
        """Existing strict finite-gradient and single-clip optimizer audit."""

    output = _source_path(config.run.output_dir)
    output_identity = _claim_fresh_output_directory(output)
    args = TrainingArguments(
        output_dir=str(output),
        overwrite_output_dir=False,
        do_train=True,
        do_eval=True,
        num_train_epochs=1.0,
        max_steps=-1,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=config.trainer.gradient_accumulation_steps,
        learning_rate=config.trainer.learning_rate,
        weight_decay=config.trainer.weight_decay,
        warmup_ratio=config.trainer.warmup_ratio,
        lr_scheduler_type="cosine",
        optim="adamw_torch_fused",
        bf16=True,
        bf16_full_eval=False,
        tf32=True,
        gradient_checkpointing=config.trainer.gradient_checkpointing,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_grad_norm=0.0,
        logging_steps=config.trainer.logging_steps,
        logging_nan_inf_filter=False,
        eval_strategy="no",
        eval_steps=config.trainer.eval_steps,
        save_strategy="no",
        save_steps=config.trainer.save_steps,
        save_total_limit=1,
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
    trainer = CompletionTrainer(
        model=model,
        args=args,
        train_dataset=train_features,
        eval_dataset=development_features,
        data_collator=_CompletionCollator(torch, tokenizer.pad_token_id),
        callbacks=[
            FiniteGradientCallback(
                torch=torch,
                named_parameters=named_parameters,
                audit=gradient_audit,
            )
        ],
    )
    trainer_runtime = single_process_trainer_runtime_record(
        trainer,
        expected_gradient_accumulation_steps=config.trainer.gradient_accumulation_steps,
    )
    trained = trainer.train(resume_from_checkpoint=False)
    if trained.global_step != check["expected_optimizer_steps"]:
        raise HydraPosttrainError("Trainer escaped its independently bounded optimizer schedule")
    gradient_evidence = gradient_audit.record()
    final = _trainable_tensor_population_snapshot(torch, named_parameters)
    if initial.names != final.names:
        raise HydraPosttrainError("training changed its reviewed LoRA parameter population")
    before = dict(initial.record_hashes)
    after = dict(final.record_hashes)
    changed = tuple(name for name in final.names if before[name] != after[name])
    update = adapter_update_audit_record(
        trainable_parameter_names=final.names,
        initial_tensor_population_sha256=initial.population_sha256,
        final_tensor_population_sha256=final.population_sha256,
        changed_parameter_names=changed,
        final_finite_parameter_names=final.names,
    )

    adapter = output / ADAPTER_SUBDIR
    tokenizer_output = output / TOKENIZER_SUBDIR
    adapter_stage = Path(tempfile.mkdtemp(prefix=".adapter.partial-", dir=output))
    model.save_pretrained(adapter_stage, safe_serialization=True)
    publish_staged_directory_noreplace(adapter_stage, adapter)
    tokenizer_stage = Path(tempfile.mkdtemp(prefix=".tokenizer.partial-", dir=output))
    tokenizer.save_pretrained(str(tokenizer_stage))
    publish_staged_directory_noreplace(tokenizer_stage, tokenizer_output)
    adapter_identity = artifact_directory_hash(output, ADAPTER_SUBDIR)
    tokenizer_artifacts = artifact_directory_hash(output, TOKENIZER_SUBDIR)
    require_safetensors_adapter(adapter_identity)
    evaluation = _finite_metrics(trainer.evaluate())
    if _trainable_tensor_population_snapshot(torch, named_parameters) != final:
        raise HydraPosttrainError("development evaluation changed the learned adapter weights")

    # Recheck the complete checked source after model work; a concurrent
    # release/publication cannot silently retarget a just-trained adapter.
    rechecked = load_preparation(prepared.output_directory)
    if rechecked.payloads != prepared.payloads or freeze_epoch(REPOSITORY_ROOT) != prepared.source.epoch:
        raise HydraPosttrainError("Alpha training inputs or frozen release changed during execution")
    _require_output_directory_unchanged(output_identity)
    _require_execution_provenance_unchanged(provenance, torch)

    manifest = {
        **_adapter_profile_fields(prepared),
        "version": prepared.source.epoch.version,
        "epoch_sha256": prepared.source.epoch.epoch_sha256,
        "edition_identity_sha256": prepared.source.epoch.edition_identity_sha256,
        "theorem_dag_sha256": prepared.source.epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": prepared.source.epoch.reviewed_definition_dag_sha256,
        "surface_label": prepared.manifest["surface_label"],
        "model": prepared.manifest["model"],
        "preparation_manifest_sha256": _sha256(prepared.payloads["manifest.json"]),
        "objective": completion_objective_record(),
        "preparation": {
            "directory": _relative_or_absolute(prepared.output_directory),
            "manifest_sha256": _sha256(prepared.payloads["manifest.json"]),
            "files": prepared.manifest["files"],
        },
        "held_out": prepared.manifest["held_out"],
        "historical_model_authority": prepared.manifest["historical_model_authority"],
        "adapter": adapter_identity,
        "tokenizer": tokenizer_artifacts,
        "token_exposure": {"train": train_tokens, "dev": development_tokens},
        "trainer_runtime": trainer_runtime,
        **provenance,
        "output_directory_identity": output_identity,
        "finite_gradient_audit": gradient_evidence,
        "adapter_update": update,
        "metrics": {
            "train": _finite_metrics(trained.metrics),
            "dev": evaluation,
            "training_rows": len(train_examples),
            "development_rows": len(development_examples),
            "expected_optimizer_steps": check["expected_optimizer_steps"],
            "actual_optimizer_steps": trained.global_step,
        },
        "model_trained": True,
        "research_claim_eligible": False,
        "alpha_admitted": False,
        "sealed_benchmark": False,
        "open_research_gates": prepared.manifest["open_research_gates"],
    }
    if "run_id" in prepared.manifest:
        manifest["run_id"] = prepared.manifest["run_id"]
    from training.peano_hydra.frontier_curriculum import FRONTIER_SOURCE_SCHEMA
    if prepared.source.manifest.get("schema") == FRONTIER_SOURCE_SCHEMA:
        if len(_canonical(manifest)) + 1 > MAX_FRONTIER_MANIFEST_BYTES:
            raise HydraPosttrainError("frontier adapter manifest exceeds existing 4 MiB origin/evaluation readers")
        return write_manifest_noreplace(output / "manifest.json", manifest, compact=True)
    return write_manifest_noreplace(output / "manifest.json", manifest)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument(
        "--preflight",
        "--dry-run",
        action="store_true",
        dest="preflight",
        help="independently replay and validate inputs without GPU/model initialization",
    )
    modes.add_argument(
        "--execute",
        action="store_true",
        help="explicitly train a fresh, bounded, one-GPU BF16 LoRA adapter",
    )
    parser.add_argument(
        "--preparation-dir",
        type=Path,
        default=REPOSITORY_ROOT / "_deploy" / "hydra-posttrain",
        metavar="PATH",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.preflight:
            result = preflight(args.preparation_dir)
        else:
            manifest_path = execute(args.preparation_dir)
            manifest = _decode(
                _read(manifest_path, label="completed Alpha adapter manifest"),
                "completed Alpha adapter manifest",
            )
            result = {
                "schema": manifest["schema"],
                "epoch_sha256": manifest["epoch_sha256"],
                "model_trained": True,
                "research_claim_eligible": False,
                "adapter_manifest": str(manifest_path),
            }
    except (HydraEpochError, HydraPosttrainError, OSError, PromptError, RuntimeError, TypeError, ValueError) as error:
        print(f"hydra-posttrain: {' '.join(str(error).split())}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
