#!/usr/bin/env python3
"""Build replay-validated next-tactic data from binding Peano Lab traces.

This compiler never edits its raw version-1 inputs.  It accepts positive
labels only from complete ``qed: true`` sessions, removes transactional error
attempts, and replays the remaining tactic sequence through
``peano_lab.batch.run_proof``.  That boundary uses the public ``run_surface``
grammar and independently kernel-checks the final certificate against the
original theorem.  Any replay, state, or proof-size mismatch aborts the build.

The training prompt is deliberately ours rather than a model/vendor chat
template::

    <task>next_tactic</task>
    <env>peano-lab-v1;surface=model-v1;logic=intuitionistic;
    capability_sha256=...</env>
    <state>{"focus":0,"goals":["... ⊢ ..."]}</state>
    <tactic>

The completion is the exact successful tactic line followed by
``</tactic>``.  Visible names in states and binder-producing commands are
preserved, so executing a row's completion reaches the next stored state.
Trace ``focus`` describes which goal the submitted action selected; because
that is part of the label rather than the input state, policy prompts always
use the runner-owned default focus 0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = Path(__file__).resolve().parent
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, SCRIPTS_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from export_traces import (  # noqa: E402
    TraceFormatError,
    TraceSession,
    load_sessions,
    publish_text_artifact_set,
)
from peano_lab.batch import (  # noqa: E402
    BatchRequestError,
    FULL_BATCH_COMMANDS,
    MAX_REVIEWED_BATCH_TRACE_BYTES,
    capability_sha256,
    run_proof,
)
from peano_lab.engine.trace import TraceLimitError  # noqa: E402
from peano_lab.kernel.formulas import (  # noqa: E402
    Formula,
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.ui.prove import (  # noqa: E402
    SURFACE_THEOREM_NAMES,
    SurfaceCapabilities,
)
from training.peano_policy.contract import (  # noqa: E402
    canonical_held_out_formulas,
    environment_record,
    model_v3_prefix_environment,
    prompt_environment,
)
from training.peano_policy.library_identity import (  # noqa: E402
    MOD5_SOURCE_REPORT,
    PUBLIC_LIBRARY_CATALOG,
)
from training.peano_policy.prompt import (  # noqa: E402
    PEANO_PROMPT_V3,
    CapabilityIdentity,
    prompt_manifest_record,
    render_prompt,
)
from peano_lab.library.theorems import THEOREMS  # noqa: E402


DATASET_FORMAT = "peano-lab-next-tactic"
DATASET_VERSION = 1
TRACE_VERSION = 1
DEFAULT_SEED = "peano-policy-v1"
DEFAULT_VAL_FRACTION = 0.1
DEFAULT_TEST_FRACTION = 0.1
TASK = "next_tactic"
ENVIRONMENT = "peano-lab-v1"
REQUIRED_METADATA_FIELDS = (
    "session",
    "theorem",
    "family",
    "lineage",
    "classical",
    "surface",
    "environment_sha256",
    "capabilities",
)
REQUIRED_TEXT_METADATA_FIELDS = (
    "session",
    "theorem",
    "family",
    "lineage",
    "surface",
    "environment_sha256",
)
CAPABILITY_FIELDS = ("label", "allowed_commands", "allowed_theorems")
LIBRARY_IDENTITY_METADATA_FIELD = "library_identity_sha256"
V3_LIBRARY_METADATA_FIELDS = (
    "library_full_identity_sha256",
    "library_prefix_length",
    "library_size",
)
V3_CATALOG_TRAJECTORY = "catalog-predecessor-prefix-v1"
V3_SYNTHETIC_LANE = "synthetic-root-balanced"
V3_SYNTHETIC_VARIANT = "authored-v3-root-balanced"
LEGACY_SPLIT_METHOD = "sha256-ranked-genealogy-formula-prompt-components-v2"
V3_SPLIT_METHOD = "catalog-train-sha256-ranked-synthetic-components-v1"
V3_SPLIT_LANES = (V3_CATALOG_TRAJECTORY, V3_SYNTHETIC_LANE)
MODEL_V3_HELD_OUT_TARGETS = frozenset(
    parse_formula_with_names(source)[0]
    for source in canonical_held_out_formulas(PEANO_PROMPT_V3)
)
ROW_FIELDS = (
    "v",
    "task",
    "env",
    "surface",
    "environment_sha256",
    "classical",
    "capabilities",
    "split",
    "session",
    "step",
    "formula",
    "theorem",
    "family",
    "lineage",
    "state",
    "focus",
    "prompt",
    "completion",
    "metadata",
)
SplitGroup = tuple[tuple[str, ...], tuple[str, ...]]


class DatasetBuildError(RuntimeError):
    """The requested corpus cannot yield a trustworthy training dataset."""


@dataclass(frozen=True, slots=True)
class BuildResult:
    """Published files and the exact manifest returned by :func:`build_dataset`."""

    train_path: Path
    val_path: Path
    test_path: Path
    manifest_path: Path
    manifest: dict[str, object]


def _safe_text(value: object, *, nonempty: bool = False) -> bool:
    if type(value) is not str or (nonempty and not value):
        return False
    return not any(
        unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for char in value
    )


def _object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _validate_json_value(value: object, *, location: str) -> None:
    """Reject non-portable metadata values while permitting useful nesting."""

    if value is None or type(value) in {bool, int}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise DatasetBuildError(f"{location} contains a non-finite number")
        return
    if type(value) is str:
        if not _safe_text(value):
            raise DatasetBuildError(f"{location} contains unsafe text")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _validate_json_value(item, location=f"{location}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if not _safe_text(key, nonempty=True):
                raise DatasetBuildError(f"{location} contains an unsafe object key")
            _validate_json_value(item, location=f"{location}.{key}")
        return
    raise DatasetBuildError(f"{location} contains a non-JSON value")


def _capability_identity(capabilities: SurfaceCapabilities) -> dict[str, object]:
    return {
        "label": capabilities.label,
        "allowed_commands": sorted(
            FULL_BATCH_COMMANDS
            if capabilities.allowed_commands is None
            else capabilities.allowed_commands
        ),
        "allowed_theorems": sorted(
            SURFACE_THEOREM_NAMES
            if capabilities.allowed_theorems is None
            else capabilities.allowed_theorems
        ),
    }


def _capabilities_from_metadata(
    record: Mapping[str, object], *, location: str
) -> SurfaceCapabilities:
    specification = record.get("capabilities")
    if type(specification) is not dict:
        raise DatasetBuildError(f"{location}: capabilities must be an object")
    if set(specification) != set(CAPABILITY_FIELDS):
        raise DatasetBuildError(
            f"{location}: capability field set must be "
            f"{list(CAPABILITY_FIELDS)!r}, got {list(specification)!r}"
        )
    label = specification["label"]
    if not _safe_text(label, nonempty=True):
        raise DatasetBuildError(
            f"{location}: capability label must be non-empty control-free text"
        )

    normalized: dict[str, frozenset[str] | None] = {}
    for field in ("allowed_commands", "allowed_theorems"):
        value = specification[field]
        if value is None:
            normalized[field] = None
            continue
        if type(value) is not list or not all(
            _safe_text(item, nonempty=True) for item in value
        ):
            raise DatasetBuildError(
                f"{location}: {field} must be null or an array of name tokens"
            )
        if len(set(value)) != len(value):
            raise DatasetBuildError(f"{location}: {field} contains duplicate names")
        normalized[field] = frozenset(value)
    try:
        capabilities = SurfaceCapabilities(
            label=label,  # type: ignore[arg-type]
            allowed_commands=normalized["allowed_commands"],
            allowed_theorems=normalized["allowed_theorems"],
        )
    except (TypeError, ValueError) as exc:
        raise DatasetBuildError(f"{location}: invalid capabilities: {exc}") from exc

    surface = record.get("surface")
    if surface != capabilities.label:
        raise DatasetBuildError(
            f"{location}: surface {surface!r} does not match capability label "
            f"{capabilities.label!r}"
        )
    expected_hash = record.get("environment_sha256")
    actual_hash = capability_sha256(capabilities)
    if expected_hash != actual_hash:
        raise DatasetBuildError(
            f"{location}: environment_sha256 {expected_hash!r} does not match "
            f"declared capabilities {actual_hash!r}"
        )
    return capabilities


def _validate_library_identity_metadata(
    record: Mapping[str, object],
    capabilities: SurfaceCapabilities,
    *,
    location: str,
) -> None:
    try:
        identity = CapabilityIdentity.from_record(
            _capability_identity(capabilities)
        )
        environment = prompt_environment(record["classical"], identity)
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetBuildError(
            f"{location}: cannot resolve checked library identity: {exc}"
        ) from None
    expected = environment.library_sha256
    present = LIBRARY_IDENTITY_METADATA_FIELD in record
    actual = record.get(LIBRARY_IDENTITY_METADATA_FIELD)
    if expected is None:
        if present:
            raise DatasetBuildError(
                f"{location}: model-v1 metadata must not claim a library identity"
            )
        return
    if not present or actual != expected:
        raise DatasetBuildError(
            f"{location}: {LIBRARY_IDENTITY_METADATA_FIELD} {actual!r} "
            f"does not match checked model-v2 authority {expected!r}"
        )
    if environment.prompt_version == PEANO_PROMPT_V3:
        expected_v3 = {
            "library_full_identity_sha256": (
                environment.library_full_identity_sha256
            ),
            "library_prefix_length": environment.library_prefix_length,
            "library_size": environment.library_full_length,
        }
        if any(record.get(key) != value for key, value in expected_v3.items()):
            raise DatasetBuildError(
                f"{location}: model-v3 prefix metadata differs from its "
                "checked authority"
            )


def load_metadata(path: str | os.PathLike[str]) -> dict[str, dict[str, object]]:
    """Load the strict separate JSONL map keyed by raw trace session id."""

    source = Path(path)
    if not source.is_file():
        raise DatasetBuildError(f"{source}: metadata is not a regular file")
    try:
        raw = source.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise DatasetBuildError(f"{source}: metadata is not valid UTF-8") from exc
    if not raw:
        raise DatasetBuildError(f"{source}: metadata is empty")
    if not raw.endswith("\n"):
        raise DatasetBuildError(
            f"{source}: incomplete metadata JSONL (missing final newline)"
        )

    result: dict[str, dict[str, object]] = {}
    for line_number, line in enumerate(raw.split("\n")[:-1], 1):
        if not line:
            raise DatasetBuildError(
                f"{source}:{line_number}: blank metadata records are forbidden"
            )
        try:
            record = json.loads(
                line,
                object_pairs_hook=_object_from_pairs,
                parse_constant=_reject_constant,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            raise DatasetBuildError(
                f"{source}:{line_number}: invalid metadata JSON: {exc}"
            ) from exc
        if type(record) is not dict:
            raise DatasetBuildError(
                f"{source}:{line_number}: metadata record must be an object"
            )
        missing = set(REQUIRED_METADATA_FIELDS) - set(record)
        if missing:
            raise DatasetBuildError(
                f"{source}:{line_number}: missing metadata field(s): "
                + ", ".join(sorted(missing))
            )
        for field in REQUIRED_TEXT_METADATA_FIELDS:
            if not _safe_text(record[field], nonempty=True):
                raise DatasetBuildError(
                    f"{source}:{line_number}: {field} must be non-empty "
                    "control-free text"
                )
        if type(record["classical"]) is not bool:
            raise DatasetBuildError(
                f"{source}:{line_number}: classical must be a Boolean"
            )
        _validate_json_value(record, location=f"{source}:{line_number}")
        capabilities = _capabilities_from_metadata(
            record, location=f"{source}:{line_number}"
        )
        _validate_library_identity_metadata(
            record,
            capabilities,
            location=f"{source}:{line_number}",
        )
        session_id = record["session"]
        if session_id in result:
            raise DatasetBuildError(
                f"{source}:{line_number}: duplicate metadata for session "
                f"{session_id!r}"
            )
        result[session_id] = record  # type: ignore[index]
    return result


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _compiler_manifest() -> dict[str, object]:
    paths = (
        Path(__file__).resolve(),
        SCRIPTS_ROOT / "export_traces.py",
        SCRIPTS_ROOT / "generate_peano_synthetic_corpus.py",
        SCRIPTS_ROOT / "generate_peano_v3_balanced_corpus.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "contract.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "prompt.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "library_identity.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "library_identity_v3.py",
        MOD5_SOURCE_REPORT,
        PUBLIC_LIBRARY_CATALOG,
        *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
    )
    return {
        "runtime": {
            "implementation": sys.implementation.name,
            "python": ".".join(str(part) for part in sys.version_info[:3]),
        },
        "sources": {
            path.relative_to(REPOSITORY_ROOT).as_posix(): {
                "sha256": _sha256_file(path)
            }
            for path in paths
        },
    }


def _compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _line_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def _prompt(
    goals: Sequence[str],
    focus: int,
    *,
    classical: bool,
    capabilities: SurfaceCapabilities,
    environment_sha256: str,
    library_identity_sha256: object = None,
) -> tuple[str, str]:
    try:
        identity = CapabilityIdentity.from_record(
            _capability_identity(capabilities)
        )
        environment = prompt_environment(classical, identity)
    except (TypeError, ValueError) as exc:
        raise DatasetBuildError(f"cannot resolve prompt environment: {exc}") from None
    if environment.sha256 != environment_sha256:
        raise DatasetBuildError("prompt environment hash differs from trace metadata")
    if environment.library_sha256 != library_identity_sha256:
        raise DatasetBuildError(
            "prompt checked-library identity differs from trace metadata"
        )
    return environment.text, render_prompt(
        goals=goals,
        focus=focus,
        environment=environment,
    )


def _successful_steps(session: TraceSession) -> tuple[dict[str, object], ...]:
    return tuple(step for step in session.steps if step["status"] == "ok")


def _rendered_goal_target(
    rendered: object,
    *,
    location: str,
) -> Formula | None:
    """Parse one rigid trace-goal target, ignoring only flexible metavariables.

    The context to the left of the final turnstile is intentionally irrelevant:
    held-out propositions may be assumptions without becoming the supervised
    target.  A target containing ``?tN`` cannot equal one of the closed rigid
    held-outs and is not accepted by the kernel formula parser, so it is the one
    canonical trace form for which structural comparison is inapplicable.
    """

    if type(rendered) is not str:
        raise DatasetBuildError(f"{location}: trace goal must be canonical text")
    _, turnstile, target_text = rendered.rpartition("⊢")
    target_text = target_text.strip()
    if not turnstile or not target_text:
        raise DatasetBuildError(
            f"{location}: trace goal has no canonical turnstile/target"
        )
    if "?" in target_text:
        return None
    try:
        target, _ = parse_formula_with_names(target_text)
    except (ParseError, TypeError, ValueError, RecursionError) as exc:
        raise DatasetBuildError(
            f"{location}: trace goal target is not a PA formula: {exc}"
        ) from exc
    return target


def _validate_no_v3_held_out_goal_targets(
    steps: Sequence[Mapping[str, object]],
    *,
    session_id: str,
) -> None:
    """Reject a v3 proof whose transition states expose a held-out target."""

    for ordinal, step in enumerate(steps, 1):
        step_number = step.get("step", ordinal)
        for field in ("goals_before", "goals_after"):
            goals = step.get(field)
            if type(goals) is not list:
                raise DatasetBuildError(
                    f"session {session_id!r} step {step_number}: {field} must be "
                    "a canonical goal array"
                )
            for goal_index, rendered in enumerate(goals, 1):
                target = _rendered_goal_target(
                    rendered,
                    location=(
                        f"session {session_id!r} step {step_number} {field} "
                        f"goal {goal_index}"
                    ),
                )
                if target in MODEL_V3_HELD_OUT_TARGETS:
                    raise DatasetBuildError(
                        f"session {session_id!r} exposes a model-v3 held-out "
                        f"formula as a goal target at step {step_number} "
                        f"{field} goal {goal_index}"
                    )


def _validate_v3_catalog_trajectory(
    session: TraceSession,
    metadata: Mapping[str, object],
    capabilities: SurfaceCapabilities,
    commands: tuple[object, ...],
) -> None:
    """Require one exact source theorem under its strict predecessor prefix."""

    index = metadata.get("library_prefix_length")
    if metadata.get("trajectory") != V3_CATALOG_TRAJECTORY:
        raise DatasetBuildError(
            f"session {session.session_id!r} with model-v3 prefix {index!r} "
            f"must use the exact {V3_CATALOG_TRAJECTORY!r} trajectory"
        )
    if type(index) is not int or isinstance(index, bool) or not 0 <= index < len(
        THEOREMS
    ):
        raise DatasetBuildError(
            f"session {session.session_id!r} has an invalid library target index"
        )
    spec = THEOREMS[index]
    canonical_formula = pretty_formula(
        parse_formula_with_names(spec.statement)[0], []
    )
    expected_commands = tuple(
        f"use {dependency}" for dependency in spec.dependencies
    ) + spec.script
    expected_capabilities = model_v3_prefix_environment(index).capabilities
    actual_identity = CapabilityIdentity.from_record(
        _capability_identity(capabilities)
    )
    expected_metadata = {
        "theorem": spec.name,
        "library_target_index": index,
        "library_target_name": spec.name,
        "statement": canonical_formula,
        "direct_dependencies": list(spec.dependencies),
        "tactics": list(expected_commands),
        "proof_nodes": session.footer["proof_size"],
    }
    if (
        "lane" in metadata
        or session.theorem != canonical_formula
        or commands != expected_commands
        or actual_identity != expected_capabilities
        or any(metadata.get(key) != value for key, value in expected_metadata.items())
    ):
        raise DatasetBuildError(
            f"session {session.session_id!r} does not match its exact "
            "predecessor-prefix theorem trajectory"
        )


def _validate_v3_synthetic_lane(
    session: TraceSession,
    metadata: Mapping[str, object],
    commands: tuple[object, ...],
) -> None:
    """Reconstruct and bind one approved root-balanced schema instance."""

    if metadata.get("lane") != V3_SYNTHETIC_LANE:
        raise DatasetBuildError(
            f"session {session.session_id!r} at the full model-v3 prefix must "
            f"use the approved {V3_SYNTHETIC_LANE!r} lane"
        )
    forbidden = {
        "trajectory",
        "library_target_index",
        "library_target_name",
        "direct_dependencies",
    }
    if forbidden.intersection(metadata):
        raise DatasetBuildError(
            f"session {session.session_id!r} mixes synthetic and catalog markers"
        )

    template = metadata.get("template")
    parameter_index = metadata.get("parameter_index")
    if (
        not _safe_text(template, nonempty=True)
        or type(parameter_index) is not int
        or isinstance(parameter_index, bool)
        or parameter_index < 0
    ):
        raise DatasetBuildError(
            f"session {session.session_id!r} has malformed synthetic schema markers"
        )
    try:
        import generate_peano_v3_balanced_corpus as generator

        schemas = {schema.name: schema for schema in generator.SCHEMAS}
        schema = schemas.get(template)
        if schema is None:
            raise DatasetBuildError(
                f"session {session.session_id!r} names an unapproved synthetic template"
            )
        candidate = schema.build(parameter_index)
        canonical_statement, formula = generator._canonical_statement(
            candidate, schema
        )
        root = generator._root_id(schema, canonical_statement)
        first_head = candidate.tactics[0].split(maxsplit=1)[0]
        root_kind = generator._root_kind(formula, first_head, candidate)
    except DatasetBuildError:
        raise
    except Exception as exc:
        raise DatasetBuildError(
            f"session {session.session_id!r} cannot reconstruct its approved "
            f"synthetic schema: {exc}"
        ) from None

    expected_commands = tuple(candidate.tactics)
    expected_transformations = [
        "proof-first-schema-instantiation",
        *(
            ["remove-artificial-induction-gate"]
            if candidate.parameters.get("artificial_gate_removed") is True
            else []
        ),
    ]
    expected_metadata = {
        "theorem": f"synthetic.{schema.name}.{root.rsplit('/', 1)[-1]}",
        "family": root,
        "lineage": root,
        "statement": canonical_statement,
        "statement_sha256": _sha256_bytes(canonical_statement.encode("utf-8")),
        "script_sha256": _sha256_bytes(
            _compact_json(list(expected_commands)).encode("utf-8")
        ),
        "domain": schema.domain,
        "tags": list(schema.tags),
        "root": root,
        "root_first_tactic_head": first_head,
        "root_kind": root_kind,
        "variant": V3_SYNTHETIC_VARIANT,
        "parents": [],
        "transformations": expected_transformations,
        "parameters": candidate.parameters,
        "tactics": list(expected_commands),
        "tactic_rows": len(expected_commands),
        "proof_nodes": session.footer["proof_size"],
    }
    seed = metadata.get("seed")
    ordinal = metadata.get("ordinal")
    if (
        not _safe_text(seed, nonempty=True)
        or type(ordinal) is not int
        or isinstance(ordinal, bool)
        or ordinal < 1
        or session.theorem != canonical_statement
        or commands != expected_commands
        or any(metadata.get(key) != value for key, value in expected_metadata.items())
    ):
        raise DatasetBuildError(
            f"session {session.session_id!r} differs from its approved "
            "synthetic statement, tactics, hashes, or schema metadata"
        )


def _validate_v3_curriculum_session(
    session: TraceSession,
    metadata: Mapping[str, object],
    capabilities: SurfaceCapabilities,
    commands: tuple[object, ...],
) -> None:
    """Select the only allowed model-v3 lane from the checked prefix."""

    if metadata.get("surface") != "model-v3":
        return
    prefix = metadata.get("library_prefix_length")
    if type(prefix) is not int or isinstance(prefix, bool):
        raise DatasetBuildError(
            f"session {session.session_id!r} has no exact model-v3 prefix"
        )
    if prefix < len(THEOREMS):
        _validate_v3_catalog_trajectory(
            session, metadata, capabilities, commands
        )
        return
    if prefix == len(THEOREMS):
        _validate_v3_synthetic_lane(session, metadata, commands)
        return
    raise DatasetBuildError(
        f"session {session.session_id!r} exceeds the model-v3 library size"
    )


def _validate_v3_curriculum_population(
    sessions: Sequence[TraceSession],
    metadata: Mapping[str, Mapping[str, object]],
) -> None:
    """Reject duplicate catalog rungs or ambiguous synthetic populations."""

    catalog_sessions: dict[int, str] = {}
    synthetic_seeds: set[str] = set()
    synthetic_ordinals: set[int] = set()
    synthetic_roots: set[str] = set()
    synthetic_statements: set[str] = set()
    synthetic_count = 0
    for session in sessions:
        record = metadata[session.session_id]
        if record.get("surface") != "model-v3":
            continue
        prefix = record.get("library_prefix_length")
        if type(prefix) is not int or isinstance(prefix, bool):
            raise DatasetBuildError(
                f"session {session.session_id!r} has no exact model-v3 prefix"
            )
        if prefix < len(THEOREMS):
            previous = catalog_sessions.setdefault(prefix, session.session_id)
            if previous != session.session_id:
                raise DatasetBuildError(
                    f"model-v3 catalog prefix {prefix} has duplicate sessions"
                )
            continue
        if prefix != len(THEOREMS):
            raise DatasetBuildError(
                f"session {session.session_id!r} exceeds the model-v3 library size"
            )
        seed = record.get("seed")
        ordinal = record.get("ordinal")
        root = record.get("root")
        statement = record.get("statement")
        if (
            type(seed) is not str
            or type(ordinal) is not int
            or isinstance(ordinal, bool)
            or type(root) is not str
            or type(statement) is not str
        ):
            raise DatasetBuildError("model-v3 synthetic population is malformed")
        if ordinal in synthetic_ordinals:
            raise DatasetBuildError(
                f"model-v3 synthetic population has duplicate ordinal {ordinal}"
            )
        if root in synthetic_roots:
            raise DatasetBuildError(
                f"model-v3 synthetic population has duplicate root {root!r}"
            )
        if statement in synthetic_statements:
            raise DatasetBuildError(
                "model-v3 synthetic population has duplicate target statement"
            )
        synthetic_seeds.add(seed)
        synthetic_ordinals.add(ordinal)
        synthetic_roots.add(root)
        synthetic_statements.add(statement)
        synthetic_count += 1
    if len(synthetic_seeds) > 1:
        raise DatasetBuildError(
            "model-v3 data must contain exactly one synthetic population seed"
        )
    if synthetic_count and synthetic_ordinals != set(range(1, synthetic_count + 1)):
        raise DatasetBuildError(
            "model-v3 synthetic ordinals must be the exact contiguous population"
        )


def _replay(
    session: TraceSession,
    metadata: Mapping[str, object],
    capabilities: SurfaceCapabilities,
) -> tuple[dict[str, object], ...]:
    """Replay one claimed proof and return its exact successful raw steps."""

    successful = _successful_steps(session)
    if not successful:
        raise DatasetBuildError(
            f"session {session.session_id!r} claims QED without a successful tactic"
        )
    commands = tuple(step["tactic"] for step in successful)
    _validate_v3_curriculum_session(
        session, metadata, capabilities, commands
    )
    # Only an exact catalog rung that has just survived reconstruction against
    # THEOREMS[index], its authored script, and its predecessor authority may
    # use the reviewed large-certificate allowance.  In particular, neither a
    # metadata claim nor a full-prefix synthetic row can select this budget.
    replay_options: dict[str, object] = {}
    if (
        metadata.get("surface") == "model-v3"
        and metadata.get("trajectory") == V3_CATALOG_TRAJECTORY
    ):
        replay_options["trace_byte_limit"] = MAX_REVIEWED_BATCH_TRACE_BYTES
    replay_id = "dataset-" + hashlib.sha256(
        session.session_id.encode("utf-8")
    ).hexdigest()[:24]
    try:
        result = run_proof(
            session.theorem,
            commands,  # type: ignore[arg-type]
            request_id=replay_id,
            classical=metadata["classical"],  # type: ignore[arg-type]
            capabilities=capabilities,
            session_id=f"{replay_id}-trace",
            **replay_options,
        )
    except TraceLimitError:
        raise DatasetBuildError(
            f"session {session.session_id!r} theorem "
            f"{metadata['theorem']!r} exceeded its checked replay trace limit"
        ) from None
    except BatchRequestError as exc:
        raise DatasetBuildError(
            f"session {session.session_id!r} cannot enter checked replay: {exc}"
        ) from exc
    if result.status != "proved" or result.kernel_checked is not True:
        detail = result.error or result.status
        raise DatasetBuildError(
            f"session {session.session_id!r} failed checked replay: {detail}"
        )
    if result.classical is not metadata["classical"]:
        raise DatasetBuildError(
            f"session {session.session_id!r} replay changed classical authority"
        )
    if result.surface != metadata["surface"]:
        raise DatasetBuildError(
            f"session {session.session_id!r} replay surface {result.surface!r} != "
            f"metadata {metadata['surface']!r}"
        )
    if result.environment_sha256 != metadata["environment_sha256"]:
        raise DatasetBuildError(
            f"session {session.session_id!r} replay environment hash "
            f"{result.environment_sha256!r} != metadata "
            f"{metadata['environment_sha256']!r}"
        )
    if result.theorem != session.theorem:
        raise DatasetBuildError(
            f"session {session.session_id!r} replay changed the original theorem"
        )
    if result.proof_nodes != session.footer["proof_size"]:
        raise DatasetBuildError(
            f"session {session.session_id!r} replay proof size "
            f"{result.proof_nodes!r} != raw {session.footer['proof_size']!r}"
        )
    if result.trace is None:
        raise DatasetBuildError(
            f"session {session.session_id!r} replay returned no binding trace"
        )
    replay_steps = tuple(record for record in result.trace if "v" in record)
    if len(replay_steps) != len(successful):
        raise DatasetBuildError(
            f"session {session.session_id!r} replay transition count "
            f"{len(replay_steps)} != raw successful count {len(successful)}"
        )

    compared_fields = (
        "goals_before",
        "focus",
        "tactic",
        "goals_after",
        "status",
        "error",
    )
    for raw_step, replay_step in zip(successful, replay_steps, strict=True):
        for field in compared_fields:
            if replay_step[field] != raw_step[field]:
                raise DatasetBuildError(
                    f"session {session.session_id!r} raw step {raw_step['step']} "
                    f"replay mismatch in {field}: {replay_step[field]!r} != "
                    f"{raw_step[field]!r}"
                )
    if metadata.get("surface") == "model-v3":
        _validate_no_v3_held_out_goal_targets(
            replay_steps,
            session_id=session.session_id,
        )
    return successful


def _validate_fractions(val_fraction: float, test_fraction: float) -> tuple[float, float]:
    for name, value in (("val_fraction", val_fraction), ("test_fraction", test_fraction)):
        if type(value) not in {int, float} or isinstance(value, bool):
            raise TypeError(f"{name} must be a number")
        if not 0.0 <= float(value) < 1.0:
            raise ValueError(f"{name} must satisfy 0 <= {name} < 1")
    val = float(val_fraction)
    test = float(test_fraction)
    if val + test >= 1.0:
        raise ValueError("val_fraction + test_fraction must be less than 1")
    return val, test


def _split_components(
    sessions: Sequence[TraceSession],
    metadata: Mapping[str, Mapping[str, object]],
    replayed: Mapping[str, Sequence[Mapping[str, object]]],
    capabilities: Mapping[str, SurfaceCapabilities],
) -> dict[str, SplitGroup]:
    """Join sessions sharing genealogy, theorem, or an exact policy prompt."""

    parents: dict[tuple[str, str], tuple[str, str]] = {}

    def find(node: tuple[str, str]) -> tuple[str, str]:
        parents.setdefault(node, node)
        root = node
        while parents[root] != root:
            root = parents[root]
        while parents[node] != node:
            parent = parents[node]
            parents[node] = root
            node = parent
        return root

    def union(left: tuple[str, str], right: tuple[str, str]) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            # Lexical parent choice makes the component construction stable
            # even when caller/input ordering changes.
            first, second = sorted((left_root, right_root))
            parents[second] = first

    for session in sessions:
        record = metadata[session.session_id]
        family = ("family", str(record["family"]))
        union(family, ("lineage", str(record["lineage"])))
        # Producer genealogy is necessary for transformed relatives, but the
        # compiler can independently prevent the simplest metadata lie: two
        # sessions proving the exact same canonical formula may not be split
        # merely because their family/lineage labels differ.
        union(family, ("formula", session.theorem))
        session_metadata = metadata[session.session_id]
        for step in replayed[session.session_id]:
            _, prompt = _prompt(
                step["goals_before"],  # type: ignore[arg-type]
                0,
                classical=session_metadata["classical"],  # type: ignore[arg-type]
                capabilities=capabilities[session.session_id],
                environment_sha256=session_metadata["environment_sha256"],  # type: ignore[arg-type]
                library_identity_sha256=session_metadata.get(
                    LIBRARY_IDENTITY_METADATA_FIELD
                ),
            )
            # Validation/test loss must not see a policy input that training
            # already saw, even when producers assign unrelated genealogy and
            # the original theorem statements differ.
            union(family, ("prompt", prompt))

    members: dict[tuple[str, str], dict[str, set[str]]] = {}
    for node in tuple(parents):
        root = find(node)
        bucket = members.setdefault(root, {"family": set(), "lineage": set()})
        if node[0] in bucket:
            bucket[node[0]].add(node[1])

    result: dict[str, SplitGroup] = {}
    for session in sessions:
        record = metadata[session.session_id]
        root = find(("family", str(record["family"])))
        bucket = members[root]
        result[session.session_id] = (
            tuple(sorted(bucket["family"])),
            tuple(sorted(bucket["lineage"])),
        )
    return result


def _group_rank(seed: str, group: SplitGroup) -> str:
    material = _compact_json(
        {"seed": seed, "families": group[0], "lineages": group[1]}
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _held_out_count(size: int, fraction: float, available: int) -> int:
    if size == 0 or fraction == 0.0 or available == 0:
        return 0
    requested = max(1, int(size * fraction))
    return min(requested, available)


def _assign_groups(
    groups: Iterable[SplitGroup],
    *,
    seed: str,
    val_fraction: float,
    test_fraction: float,
    forced_train_groups: Iterable[SplitGroup] = (),
) -> dict[SplitGroup, str]:
    if not _safe_text(seed, nonempty=True):
        raise ValueError("seed must be non-empty control-free text")
    val_fraction, test_fraction = _validate_fractions(val_fraction, test_fraction)
    complete = set(groups)
    forced = set(forced_train_groups)
    if not forced <= complete:
        raise ValueError("forced training groups must belong to the split population")
    ordered = sorted(
        complete - forced,
        key=lambda group: (_group_rank(seed, group), group),
    )
    # Always reserve one training group when any data exists.  For tiny inputs,
    # test receives the first available holdout and validation the next.
    available = max(0, len(ordered) - 1)
    test_count = _held_out_count(len(ordered), test_fraction, available)
    available -= test_count
    val_count = _held_out_count(len(ordered), val_fraction, available)
    test_groups = set(ordered[:test_count])
    val_groups = set(ordered[test_count : test_count + val_count])
    result = {
        group: (
            "test"
            if group in test_groups
            else "val"
            if group in val_groups
            else "train"
        )
        for group in ordered
    }
    result.update((group, "train") for group in sorted(forced))
    return result


def _v3_catalog_train_groups(
    session_groups: Mapping[str, SplitGroup],
    metadata: Mapping[str, Mapping[str, object]],
) -> frozenset[SplitGroup]:
    """Return every component containing a checked catalog-prefix session."""

    return frozenset(
        group
        for session, group in session_groups.items()
        if metadata[session].get("surface") == "model-v3"
        and metadata[session].get("trajectory") == V3_CATALOG_TRAJECTORY
    )


def _v3_lane(metadata: Mapping[str, object]) -> str:
    """Classify one already-validated model-v3 curriculum session."""

    prefix = metadata.get("library_prefix_length")
    if type(prefix) is not int or isinstance(prefix, bool):
        raise DatasetBuildError("model-v3 split lane has no exact prefix")
    if prefix < len(THEOREMS):
        if metadata.get("trajectory") != V3_CATALOG_TRAJECTORY:
            raise DatasetBuildError("model-v3 catalog split lane is unmarked")
        return V3_CATALOG_TRAJECTORY
    if prefix == len(THEOREMS) and metadata.get("lane") == V3_SYNTHETIC_LANE:
        return V3_SYNTHETIC_LANE
    raise DatasetBuildError("model-v3 split lane is not an approved curriculum lane")


def _metadata_extras(metadata: Mapping[str, object]) -> dict[str, object]:
    return {
        key: metadata[key]
        for key in sorted(metadata)
        if key not in REQUIRED_METADATA_FIELDS
    }


def _make_row(
    session: TraceSession,
    step: Mapping[str, object],
    metadata: Mapping[str, object],
    capabilities: SurfaceCapabilities,
    split: str,
) -> dict[str, object]:
    classical = metadata["classical"]
    environment_sha256 = metadata["environment_sha256"]
    goals = step["goals_before"]
    # Version-1 ProofState has no persistent user-selected focus.  The trace's
    # focus is computed from the submitted command (for example ``focus 2``),
    # so feeding it to the policy would leak part of the answer.
    focus = 0
    environment, prompt = _prompt(
        goals,  # type: ignore[arg-type]
        focus,  # type: ignore[arg-type]
        classical=classical,  # type: ignore[arg-type]
        capabilities=capabilities,
        environment_sha256=environment_sha256,  # type: ignore[arg-type]
        library_identity_sha256=metadata.get(
            LIBRARY_IDENTITY_METADATA_FIELD
        ),
    )
    tactic = str(step["tactic"])
    row = {
        "v": DATASET_VERSION,
        "task": TASK,
        "env": environment,
        "surface": metadata["surface"],
        "environment_sha256": environment_sha256,
        "classical": classical,
        "capabilities": _capability_identity(capabilities),
        "split": split,
        "session": session.session_id,
        "step": step["step"],
        "formula": session.theorem,
        "theorem": metadata["theorem"],
        "family": metadata["family"],
        "lineage": metadata["lineage"],
        "state": list(goals),  # type: ignore[arg-type]
        "focus": focus,
        "prompt": prompt,
        "completion": tactic + "</tactic>",
        "metadata": _metadata_extras(metadata),
    }
    if tuple(row) != ROW_FIELDS:
        raise RuntimeError("internal dataset row field order changed")
    return row


def _paths_alias(first: Path, second: Path) -> bool:
    try:
        if first.resolve(strict=False) == second.resolve(strict=False):
            return True
    except (OSError, RuntimeError):
        pass
    try:
        return os.path.samefile(first, second)
    except OSError:
        return False


def _publish(artifacts: Sequence[tuple[Path, str]]) -> None:
    """Publish one coherent dataset set with ordinary-failure rollback."""

    try:
        publish_text_artifact_set(artifacts)
    except ValueError as exc:
        raise DatasetBuildError(
            str(exc).replace("export artifact", "dataset artifact")
        ) from exc


def build_dataset(
    inputs: Iterable[str | os.PathLike[str]],
    metadata_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    *,
    seed: str = DEFAULT_SEED,
    val_fraction: float = DEFAULT_VAL_FRACTION,
    test_fraction: float = DEFAULT_TEST_FRACTION,
) -> BuildResult:
    """Validate, replay, group-split, and publish a positive CE dataset."""

    input_values = tuple(inputs)
    sessions = load_sessions(input_values)
    metadata = load_metadata(metadata_path)
    _validate_fractions(val_fraction, test_fraction)
    if not _safe_text(seed, nonempty=True):
        raise ValueError("seed must be non-empty control-free text")

    session_ids = {session.session_id for session in sessions}
    unknown_metadata = set(metadata) - session_ids
    if unknown_metadata:
        raise DatasetBuildError(
            "metadata references unknown raw session(s): "
            + ", ".join(sorted(unknown_metadata))
        )
    positives = tuple(session for session in sessions if session.footer["qed"] is True)
    missing_metadata = {session.session_id for session in positives} - set(metadata)
    if missing_metadata:
        raise DatasetBuildError(
            "qed session(s) lack metadata: " + ", ".join(sorted(missing_metadata))
        )
    if not positives:
        raise DatasetBuildError("raw traces contain no qed:true sessions")

    session_capabilities = {
        session.session_id: _capabilities_from_metadata(
            metadata[session.session_id], location=f"session {session.session_id!r}"
        )
        for session in positives
    }
    _validate_v3_curriculum_population(positives, metadata)
    replayed: dict[str, tuple[dict[str, object], ...]] = {}
    for session in sorted(positives, key=lambda item: item.session_id):
        replayed[session.session_id] = _replay(
            session,
            metadata[session.session_id],
            session_capabilities[session.session_id],
        )

    session_groups = _split_components(
        positives,
        metadata,
        replayed,
        session_capabilities,
    )
    catalog_train_groups = _v3_catalog_train_groups(session_groups, metadata)
    assignment = _assign_groups(
        session_groups.values(),
        seed=seed,
        val_fraction=val_fraction,
        test_fraction=test_fraction,
        forced_train_groups=catalog_train_groups,
    )
    rows: dict[str, list[dict[str, object]]] = {
        "train": [],
        "val": [],
        "test": [],
    }
    split_sessions: dict[str, set[str]] = {name: set() for name in rows}
    split_groups: dict[str, set[SplitGroup]] = {name: set() for name in rows}
    session_splits: dict[str, str] = {}
    for session in sorted(
        positives,
        key=lambda item: (
            session_groups[item.session_id],
            item.session_id,
        ),
    ):
        record = metadata[session.session_id]
        group = session_groups[session.session_id]
        split = assignment[group]
        session_splits[session.session_id] = split
        split_sessions[split].add(session.session_id)
        split_groups[split].add(group)
        rows[split].extend(
            _make_row(
                session,
                step,
                record,
                session_capabilities[session.session_id],
                split,
            )
            for step in replayed[session.session_id]
        )

    texts = {
        split: "".join(_line_json(row) for row in rows[split])
        for split in ("train", "val", "test")
    }
    destination = Path(output_dir)
    output_paths = {
        split: destination / f"{split}.jsonl"
        for split in ("train", "val", "test")
    }
    manifest_path = destination / "manifest.json"
    source_paths = [Path(path) for path in input_values] + [Path(metadata_path)]
    for artifact in (*output_paths.values(), manifest_path):
        if any(_paths_alias(artifact, source) for source in source_paths):
            raise DatasetBuildError(f"refusing to overwrite input with {artifact}")

    source_entries = [
        {
            "path": str(path),
            "sha256": _sha256_file(Path(path)),
        }
        for path in sorted(input_values, key=lambda value: str(Path(value).resolve()))
    ]
    split_manifest: dict[str, object] = {}
    for split in ("train", "val", "test"):
        split_manifest[split] = {
            "groups": [
                {"families": list(group[0]), "lineages": list(group[1])}
                for group in sorted(split_groups[split])
            ],
            "sessions": len(split_sessions[split]),
            "rows": len(rows[split]),
            "sha256": _sha256_bytes(texts[split].encode("utf-8")),
        }
    dataset_digest = hashlib.sha256()
    for split in ("train", "val", "test"):
        dataset_digest.update(split.encode("ascii") + b"\0")
        dataset_digest.update(texts[split].encode("utf-8"))

    environment_sessions: dict[
        tuple[str, str, bool], set[str]
    ] = {}
    for session in positives:
        record = metadata[session.session_id]
        key = (
            str(record["surface"]),
            str(record["environment_sha256"]),
            bool(record["classical"]),
        )
        environment_sessions.setdefault(key, set()).add(session.session_id)
    environments = []
    prompt_versions: set[int] = set()
    for (surface, environment_sha256, classical), ids in sorted(
        environment_sessions.items()
    ):
        exemplar = min(ids)
        capability_record = _capability_identity(session_capabilities[exemplar])
        try:
            resolved_prompt_environment = prompt_environment(
                classical,
                CapabilityIdentity.from_record(capability_record),
            )
        except (TypeError, ValueError) as exc:
            raise DatasetBuildError(
                f"cannot resolve dataset prompt environment: {exc}"
            ) from None
        prompt_versions.add(resolved_prompt_environment.prompt_version)
        environment_entry = environment_record(resolved_prompt_environment)
        if (
            environment_entry["surface"] != surface
            or environment_entry["environment_sha256"] != environment_sha256
            or environment_entry["classical"] is not classical
            or environment_entry["capabilities"] != capability_record
        ):
            raise DatasetBuildError("dataset environment preimage is inconsistent")
        environment_entry["sessions"] = len(ids)
        environments.append(environment_entry)
    if len(prompt_versions) != 1:
        raise DatasetBuildError(
            "one dataset may use exactly one repository prompt contract"
        )
    prompt_version = next(iter(prompt_versions))

    if prompt_version == PEANO_PROMPT_V3:
        lane_sessions = {
            split: {lane: set() for lane in V3_SPLIT_LANES}
            for split in ("train", "val", "test")
        }
        lane_rows = {
            split: {lane: 0 for lane in V3_SPLIT_LANES}
            for split in ("train", "val", "test")
        }
        for session in positives:
            split = session_splits[session.session_id]
            lane = _v3_lane(metadata[session.session_id])
            if lane == V3_CATALOG_TRAJECTORY and split != "train":
                raise DatasetBuildError(
                    "model-v3 catalog trajectories must be in the training split"
                )
            lane_sessions[split][lane].add(session.session_id)
            lane_rows[split][lane] += len(replayed[session.session_id])
        for split in ("train", "val", "test"):
            split_record = split_manifest[split]
            assert type(split_record) is dict
            split_record["lane_populations"] = {
                lane: {
                    "sessions": len(lane_sessions[split][lane]),
                    "rows": lane_rows[split][lane],
                }
                for lane in V3_SPLIT_LANES
            }

    manifest: dict[str, object] = {
        "format": DATASET_FORMAT,
        "version": DATASET_VERSION,
        "trace_version": TRACE_VERSION,
        "prompt": prompt_manifest_record(prompt_version),
        "split": {
            "method": (
                V3_SPLIT_METHOD
                if prompt_version == PEANO_PROMPT_V3
                else LEGACY_SPLIT_METHOD
            ),
            "seed": seed,
            "group": (
                (
                    "catalog-containing components forced to train; only "
                    "catalog-free synthetic components are hash-ranked for "
                    "train, validation, or test before row expansion"
                )
                if prompt_version == PEANO_PROMPT_V3
                else (
                    "connected components sharing family, lineage, exact "
                    "canonical theorem, or exact policy prompt, "
                    "assigned before row expansion"
                )
            ),
            "val_fraction": float(val_fraction),
            "test_fraction": float(test_fraction),
        },
        "source": {
            "compiler": _compiler_manifest(),
            "traces": source_entries,
            "metadata": {
                "path": str(metadata_path),
                "sha256": _sha256_file(Path(metadata_path)),
                "records": len(metadata),
            },
            "sessions": len(sessions),
            "qed_true_sessions": len(positives),
            "qed_false_sessions_ignored": len(sessions) - len(positives),
            "raw_transition_records": sum(len(session.steps) for session in sessions),
        },
        "replay": {
            "attempted_qed_sessions": len(positives),
            "accepted_kernel_checked_sessions": len(positives),
            "positive_rows": sum(len(value) for value in rows.values()),
            "transactional_error_steps_ignored": sum(
                step["status"] == "error"
                for session in positives
                for step in session.steps
            ),
        },
        "environments": environments,
        "splits": split_manifest,
        "dataset_sha256": dataset_digest.hexdigest(),
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    _publish(
        (
            (output_paths["train"], texts["train"]),
            (output_paths["val"], texts["val"]),
            (output_paths["test"], texts["test"]),
            (manifest_path, manifest_text),
        )
    )
    return BuildResult(
        output_paths["train"],
        output_paths["val"],
        output_paths["test"],
        manifest_path,
        manifest,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build replay-validated Peano Lab next-tactic train/val/test JSONL."
        )
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="binding raw v1 traces")
    parser.add_argument(
        "--metadata",
        type=Path,
        required=True,
        help="separate session metadata JSONL",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="destination for train/val/test JSONL and manifest.json",
    )
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--val-fraction", type=float, default=DEFAULT_VAL_FRACTION)
    parser.add_argument("--test-fraction", type=float, default=DEFAULT_TEST_FRACTION)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = build_dataset(
            args.inputs,
            args.metadata,
            args.output_dir,
            seed=args.seed,
            val_fraction=args.val_fraction,
            test_fraction=args.test_fraction,
        )
    except (DatasetBuildError, TraceFormatError, OSError, TypeError, ValueError) as exc:
        print(f"dataset build failed: {exc}", file=sys.stderr)
        return 2
    splits = result.manifest["splits"]
    print(
        "built replay-validated dataset: "
        + ", ".join(
            f"{name}={splits[name]['rows']}"  # type: ignore[index]
            for name in ("train", "val", "test")
        )
    )
    print(f"manifest: {result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DATASET_FORMAT",
    "DATASET_VERSION",
    "DEFAULT_SEED",
    "DEFAULT_TEST_FRACTION",
    "DEFAULT_VAL_FRACTION",
    "ENVIRONMENT",
    "ROW_FIELDS",
    "BuildResult",
    "DatasetBuildError",
    "build_dataset",
    "load_metadata",
    "main",
]
