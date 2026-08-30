#!/usr/bin/env python3
"""Generate the exact checked model-v3 theorem-ladder trajectories.

For theorem ``THEOREMS[i]`` the execution authority is exactly
``THEOREMS[:i]``.  The trajectory imports the theorem's declared direct
dependencies with ordinary ``use`` commands and then executes the authored
``TheoremSpec.script`` without alteration.  Consequently the target theorem
is neither prompt-visible nor executable while its own proof is generated.

The trace, metadata sidecar, and manifest are staged and published as one
transactional artifact set.  The metadata contract is accepted by
``build_peano_policy_dataset.py``, which independently replays every emitted
QED before turning its transitions into next-tactic rows.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, SCRIPTS_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from export_traces import publish_text_artifact_set  # noqa: E402
from peano_lab.batch import (  # noqa: E402
    MAX_REVIEWED_BATCH_TRACE_BYTES,
    MODEL_V1_COMMANDS,
    BatchResult,
    capability_sha256,
    run_proof,
)
from peano_lab.engine.trace import TRACE_VERSION, TraceLimitError  # noqa: E402
from peano_lab.kernel.formulas import (  # noqa: E402
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.library.theorems import THEOREMS, TheoremSpec  # noqa: E402
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_LIBRARY_SIZE,
    environment_record,
    model_v3_prefix_environment,
)
from training.peano_policy.prompt import PromptEnvironment  # noqa: E402


FORMAT = "peano-library-policy-corpus"
VERSION = 1
TRAJECTORY = "catalog-predecessor-prefix-v1"
CAPABILITY_FIELDS = ("label", "allowed_commands", "allowed_theorems")
METADATA_FIELDS = (
    "session",
    "theorem",
    "family",
    "lineage",
    "classical",
    "surface",
    "environment_sha256",
    "capabilities",
    "statement",
    "trajectory",
    "library_target_index",
    "library_target_name",
    "library_identity_sha256",
    "library_full_identity_sha256",
    "library_prefix_length",
    "library_size",
    "direct_dependencies",
    "tactics",
    "proof_nodes",
)


class GenerationError(RuntimeError):
    """A theorem-ladder corpus cannot be emitted under its checked contract."""


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Published artifact paths and the exact in-memory manifest."""

    trace_path: Path
    metadata_path: Path
    manifest_path: Path
    manifest: dict[str, object]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _line_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def _runtime_record() -> dict[str, str]:
    return {
        "implementation": sys.implementation.name,
        "python": ".".join(str(part) for part in sys.version_info[:3]),
    }


def _source_manifest() -> dict[str, dict[str, str]]:
    paths = (
        Path(__file__).resolve(),
        SCRIPTS_ROOT / "export_traces.py",
        SCRIPTS_ROOT / "build_peano_policy_dataset.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "contract.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "prompt.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "library_identity_v3.py",
        REPOSITORY_ROOT / "artifacts" / "peano-library" / "catalog-v1.json",
        *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
    )
    return {
        path.relative_to(REPOSITORY_ROOT).as_posix(): {
            "sha256": _sha256_file(path)
        }
        for path in paths
    }


def select_theorems(limit: int | None = None) -> tuple[TheoremSpec, ...]:
    """Return a declaration-order prefix; no limit means all 247 rungs."""

    if limit is None:
        limit = MODEL_V3_LIBRARY_SIZE
    if (
        type(limit) is not int
        or isinstance(limit, bool)
        or not 1 <= limit <= MODEL_V3_LIBRARY_SIZE
    ):
        raise ValueError(
            f"limit must be between 1 and {MODEL_V3_LIBRARY_SIZE}"
        )
    return THEOREMS[:limit]


def _canonical_statement(spec: TheoremSpec) -> str:
    formula, free_names = parse_formula_with_names(spec.statement)
    if free_names:
        raise GenerationError(
            f"library theorem {spec.name!r} is not closed: "
            + ", ".join(free_names)
        )
    return pretty_formula(formula, [])


def _surface_capabilities(
    index: int,
) -> tuple[SurfaceCapabilities, PromptEnvironment]:
    """Return the executable and prompt forms of one canonical v3 prefix."""

    environment = model_v3_prefix_environment(index)
    identity = environment.capabilities
    expected_commands = tuple(sorted(MODEL_V1_COMMANDS))
    if (
        identity.label != "model-v3"
        or identity.allowed_commands != expected_commands
        or identity.allowed_theorems is None
    ):
        raise GenerationError(f"model-v3 prefix {index} is not canonical")
    capabilities = SurfaceCapabilities(
        label="model-v3",
        allowed_commands=frozenset(MODEL_V1_COMMANDS),
        allowed_theorems=frozenset(identity.allowed_theorems),
    )
    if capability_sha256(capabilities) != environment.sha256:
        raise GenerationError(
            f"model-v3 prefix {index} prompt and execution identities differ"
        )
    return capabilities, environment


def _commands(spec: TheoremSpec, index: int) -> tuple[str, ...]:
    prior = {item.name for item in THEOREMS[:index]}
    missing = set(spec.dependencies).difference(prior)
    if missing:
        raise GenerationError(
            f"library theorem {spec.name!r} has non-predecessor dependencies: "
            + ", ".join(sorted(missing))
        )
    return tuple(f"use {name}" for name in spec.dependencies) + tuple(spec.script)


def _session_id(
    spec: TheoremSpec,
    index: int,
    statement: str,
    commands: tuple[str, ...],
    environment_sha256: str,
) -> str:
    payload = {
        "format": FORMAT,
        "version": VERSION,
        "trajectory": TRAJECTORY,
        "target_index": index,
        "target_name": spec.name,
        "statement": statement,
        "commands": list(commands),
        "environment_sha256": environment_sha256,
    }
    digest = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return f"peano-library-v3-{index:03d}-{digest[:20]}"


def _checked_result(
    result: BatchResult,
    *,
    spec: TheoremSpec,
    statement: str,
    commands: tuple[str, ...],
    capabilities: SurfaceCapabilities,
) -> None:
    if result.status != "proved" or result.kernel_checked is not True:
        detail = result.error or result.status
        raise GenerationError(
            f"library theorem {spec.name!r} did not reach checked QED: {detail}"
        )
    if result.theorem != statement:
        raise GenerationError(
            f"library theorem {spec.name!r} changed during checked execution"
        )
    if (
        result.surface != "model-v3"
        or result.environment_sha256 != capability_sha256(capabilities)
        or result.classical is not False
    ):
        raise GenerationError(
            f"library theorem {spec.name!r} escaped its predecessor authority"
        )
    if result.trace is None or not result.trace:
        raise GenerationError(f"library theorem {spec.name!r} returned no trace")
    transitions = tuple(record for record in result.trace if "v" in record)
    if tuple(record.get("tactic") for record in transitions) != commands:
        raise GenerationError(
            f"library theorem {spec.name!r} trace changed its exact tactic script"
        )
    footer = result.trace[-1]
    if (
        footer.get("qed") is not True
        or footer.get("theorem") != statement
        or footer.get("tactic_count") != len(commands)
        or footer.get("proof_size") != result.proof_nodes
    ):
        raise GenerationError(
            f"library theorem {spec.name!r} lacks a binding checked-QED footer"
        )


def _metadata_record(
    spec: TheoremSpec,
    index: int,
    statement: str,
    commands: tuple[str, ...],
    result: BatchResult,
    environment: PromptEnvironment,
) -> dict[str, object]:
    # ``environment`` is produced only by model_v3_prefix_environment.  Keep
    # this adapter local so raw traces depend on the executable Surface value,
    # while all identity metadata comes from the canonical prompt contract.
    canonical = environment_record(environment)
    record = {
        "session": result.session_id,
        "theorem": spec.name,
        "family": f"library-theorem/{spec.name}",
        "lineage": f"{TRAJECTORY}/{index:03d}/{spec.name}",
        "classical": False,
        "surface": canonical["surface"],
        "environment_sha256": canonical["environment_sha256"],
        "capabilities": canonical["capabilities"],
        "statement": statement,
        "trajectory": TRAJECTORY,
        "library_target_index": index,
        "library_target_name": spec.name,
        "library_identity_sha256": canonical["library_identity_sha256"],
        "library_full_identity_sha256": canonical[
            "library_full_identity_sha256"
        ],
        "library_prefix_length": canonical["library_prefix_length"],
        "library_size": canonical["library_size"],
        "direct_dependencies": list(spec.dependencies),
        "tactics": list(commands),
        "proof_nodes": result.proof_nodes,
    }
    if tuple(record) != METADATA_FIELDS:
        raise RuntimeError("internal library-corpus metadata field order changed")
    return record


def _paths_alias(paths: Sequence[Path]) -> bool:
    resolved: set[Path] = set()
    for path in paths:
        try:
            canonical = path.resolve(strict=False)
        except (OSError, RuntimeError):
            canonical = path.absolute()
        if canonical in resolved:
            return True
        resolved.add(canonical)
    return False


def _publish(artifacts: Sequence[tuple[Path, str]]) -> None:
    if _paths_alias([path for path, _ in artifacts]):
        raise GenerationError("trace, metadata, and manifest paths must be distinct")
    try:
        publish_text_artifact_set(artifacts)
    except ValueError as exc:
        raise GenerationError(
            str(exc).replace("export artifact", "library-corpus artifact")
        ) from exc


def generate_corpus(
    trace_output: str | os.PathLike[str],
    metadata_output: str | os.PathLike[str],
    manifest_output: str | os.PathLike[str],
    *,
    limit: int | None = None,
) -> GenerationResult:
    """Generate and atomically publish a checked declaration-order prefix."""

    selected = select_theorems(limit)
    sources = _source_manifest()
    trace_stream = io.StringIO()
    metadata: list[dict[str, object]] = []
    environments: list[dict[str, object]] = []
    tactic_heads: Counter[str] = Counter()
    proof_nodes = 0
    transition_records = 0

    for index, spec in enumerate(selected):
        statement = _canonical_statement(spec)
        commands = _commands(spec, index)
        capabilities, environment = _surface_capabilities(index)
        if spec.name in (capabilities.allowed_theorems or frozenset()):
            raise GenerationError(
                f"target theorem {spec.name!r} is available in its own prefix"
            )
        session_id = _session_id(
            spec, index, statement, commands, environment.sha256
        )
        try:
            result = run_proof(
                statement,
                commands,
                request_id=f"library-corpus:{spec.name}",
                classical=False,
                capabilities=capabilities,
                trace_sink=trace_stream,
                session_id=session_id,
                trace_byte_limit=MAX_REVIEWED_BATCH_TRACE_BYTES,
            )
        except TraceLimitError:
            raise GenerationError(
                f"library theorem {spec.name!r} exceeded the "
                "headless per-session trace limit"
            ) from None
        _checked_result(
            result,
            spec=spec,
            statement=statement,
            commands=commands,
            capabilities=capabilities,
        )
        record = _metadata_record(
            spec, index, statement, commands, result, environment
        )
        metadata.append(record)
        environment_entry = environment_record(environment)
        environment_entry["sessions"] = 1
        environments.append(environment_entry)
        transition_records += len(commands)
        proof_nodes += result.proof_nodes or 0
        tactic_heads.update(command.split(maxsplit=1)[0] for command in commands)

    trace_text = trace_stream.getvalue()
    metadata_text = "".join(_line_json(record) for record in metadata)
    if not trace_text or not trace_text.endswith("\n"):
        raise GenerationError("the checked runner returned an incomplete trace stream")
    if not metadata_text.endswith("\n"):
        raise GenerationError("the metadata sidecar is incomplete")

    trace_path = Path(trace_output)
    metadata_path = Path(metadata_output)
    manifest_path = Path(manifest_output)
    full_identity = metadata[0]["library_full_identity_sha256"]
    fingerprint_payload = {
        "format": FORMAT,
        "version": VERSION,
        "trajectory": TRAJECTORY,
        "library_full_identity_sha256": full_identity,
        "sessions": [record["session"] for record in metadata],
        "sources": sources,
    }
    run_fingerprint = hashlib.sha256(
        json.dumps(
            fingerprint_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    manifest: dict[str, object] = {
        "format": FORMAT,
        "version": VERSION,
        "trace_version": TRACE_VERSION,
        "trajectory": TRAJECTORY,
        "run_fingerprint": run_fingerprint,
        "runtime": _runtime_record(),
        "config": {
            "limit": len(selected),
            "full_library_size": MODEL_V3_LIBRARY_SIZE,
            "selection": "declaration-order-prefix-v1",
        },
        "library": {
            "full_identity_sha256": full_identity,
            "size": MODEL_V3_LIBRARY_SIZE,
            "target_authority": "strict-predecessor-prefix",
        },
        "sources": sources,
        "artifacts": {
            "trace": {
                "path": trace_path.name,
                "bytes": len(trace_text.encode("utf-8")),
                "sha256": _sha256_bytes(trace_text.encode("utf-8")),
            },
            "metadata": {
                "path": metadata_path.name,
                "bytes": len(metadata_text.encode("utf-8")),
                "sha256": _sha256_bytes(metadata_text.encode("utf-8")),
            },
        },
        "counts": {
            "sessions": len(selected),
            "kernel_checked_qed": len(selected),
            "transition_records": transition_records,
            "footer_records": len(selected),
            "proof_nodes": proof_nodes,
            "dependency_imports": sum(
                len(spec.dependencies) for spec in selected
            ),
            "authored_tactics": sum(len(spec.script) for spec in selected),
            "tactic_heads": dict(sorted(tactic_heads.items())),
        },
        "environments": environments,
        "sessions": [
            {
                "session": record["session"],
                "target_index": record["library_target_index"],
                "target_name": record["library_target_name"],
                "library_prefix_length": record["library_prefix_length"],
                "proof_nodes": record["proof_nodes"],
            }
            for record in metadata
        ],
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    _publish(
        (
            (trace_path, trace_text),
            (metadata_path, metadata_text),
            (manifest_path, manifest_text),
        )
    )
    return GenerationResult(trace_path, metadata_path, manifest_path, manifest)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-output", required=True)
    parser.add_argument("--metadata-output", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument(
        "--limit",
        type=int,
        help=(
            "generate the first N frozen model-v3 theorem sessions "
            f"(1..{MODEL_V3_LIBRARY_SIZE})"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        result = generate_corpus(
            args.trace_output,
            args.metadata_output,
            args.manifest,
            limit=args.limit,
        )
    except (GenerationError, OSError, ValueError) as exc:
        parser.exit(2, f"generation failed: {exc}\n")
    print(
        f"generated {result.manifest['counts']['sessions']} checked "
        f"model-v3 library sessions; manifest: {result.manifest_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through CLI tests
    raise SystemExit(main())
