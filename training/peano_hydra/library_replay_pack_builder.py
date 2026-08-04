"""Live-only builder for the isolated Peano Hydra library replay pack.

Unlike :mod:`training.peano_hydra.library_replay_pack`, this module is allowed
to import the living theorem catalog and tactic-engine metrics.  It reconstructs
the current publication certificates once, emits one canonical raw artifact per
theorem, then invokes the isolated pack verifier before publishing the staging
directory atomically.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable

from peano_lab.engine.state import proof_resource_metrics
from peano_lab.kernel.artifact_codec import (
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import pretty_formula
from peano_lab.library import theorems as theorem_library

from . import library_epoch
from .library_replay_pack import (
    CATALOG_FILE,
    CERTIFICATE_DIRECTORY,
    CERTIFICATE_REPRESENTATION,
    FUEL_MULTIPLIER,
    FUEL_OFFSET,
    FORBIDDEN_REPLAY_IMPORT_PREFIXES,
    LOGIC_MODE,
    MANIFEST_FILE,
    MAX_ARTIFACT_BYTES,
    MAX_CATALOG_BYTES,
    MAX_PROFILE_BYTES,
    MAX_SCHEMA_BYTES,
    PACK_STATUS,
    PROFILE_FILE,
    REPLAY_PACK_FORMAT,
    REPLAY_PACK_SCHEMA_PATH,
    REPLAY_PACK_VERSION,
    REPLAY_VERIFICATION_FORMAT,
    REPLAY_VERIFICATION_VERSION,
    REPLAY_WORKER_ISOLATION_FORMAT,
    REPLAY_WORKER_ISOLATION_VERSION,
    SCHEMA_FILE,
    SOURCE_CERTIFICATE_REPRESENTATION,
    _catalog_from_bytes,
    _decode_canonical_document,
    _profile_identity_from_bytes,
    _read_bounded_regular_file,
    canonical_document_bytes,
    live_kernel_identity,
    proof_tree_metrics,
    replay_pack_schema,
    replay_pack_schema_identity,
    replay_root_sha256,
    validate_replay_pack_id,
    validate_replay_pack_manifest,
    with_manifest_root,
)
from .profile import SEMANTIC_PROFILE_PATH


DEFAULT_PACK_ID = "authoring-l0-replay-candidate-v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "artifacts"
    / "peano-hydra"
    / "l0-replay-candidate-v1"
)
REPLAY_CLI_PATH = REPOSITORY_ROOT / "scripts" / "build_peano_hydra_replay_pack.py"
FRESH_REPLAY_TIMEOUT_SECONDS = 600
CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "artifacts"
    / "peano-library"
    / "catalog-v1.json"
)


class LibraryReplayPackBuildError(RuntimeError):
    """The living catalog could not produce one atomic checked candidate pack."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _cut_nodes(proof) -> int:
    return proof_tree_metrics(proof)["cut_nodes"]


def _matching_live_catalog(identity: dict[str, object]) -> None:
    live = library_epoch.live_tracked_catalog_identity()
    expected = {
        "artifact_sha256": live["artifact_sha256"],
        "catalog_sha256": live["catalog_sha256"],
        "ordered_root_sha256": live["ordered_root_sha256"],
        "schema": live["schema"],
        "source_root_sha256": live["source_root_sha256"],
        "theorem_count": live["theorem_count"],
    }
    if identity != {"artifact_path": CATALOG_FILE, **expected}:
        raise LibraryReplayPackBuildError(
            "packed catalog identity differs from the freshly replayed living catalog"
        )


def _construction_metrics(catalog_row: dict[str, object]) -> dict[str, object]:
    return {
        "cut_nodes": catalog_row["cut_nodes"],
        "distinct_proof_objects": catalog_row["distinct_proof_objects"],
        "proof_depth": catalog_row["proof_depth"],
        "proof_edges": catalog_row["proof_edges"],
        "proof_nodes": catalog_row["proof_nodes"],
        "reused_proof_references": catalog_row["reused_proof_references"],
        "source_certificate_representation": catalog_row[
            "certificate_representation"
        ],
        "source_certificate_sha256": catalog_row["certificate_sha256"],
    }


def _row(
    index: int,
    catalog_row: dict[str, object],
    *,
    artifact: bytes,
    formula,
    proof,
) -> dict[str, object]:
    if _sha256(repr(proof).encode("utf-8")) != catalog_row["certificate_sha256"]:
        raise LibraryReplayPackBuildError(
            f"live source certificate identity drifted at {catalog_row['name']!r}"
        )
    artifact_sha256 = _sha256(artifact)
    tree_metrics = proof_tree_metrics(proof)
    fuel = FUEL_MULTIPLIER * tree_metrics["proof_nodes"] + FUEL_OFFSET
    if tree_metrics != {
        "cut_nodes": catalog_row["cut_nodes"],
        "proof_depth": catalog_row["proof_depth"],
        "proof_nodes": catalog_row["proof_nodes"],
    }:
        raise LibraryReplayPackBuildError(
            f"packed tree metrics disagree at {catalog_row['name']!r}"
        )
    if fuel < 1:
        raise LibraryReplayPackBuildError("artifact fuel is not positive")
    canonical_statement = pretty_formula(formula, [])
    return {
        "artifact": {
            "bytes": len(artifact),
            "fuel": fuel,
            "path": (
                f"{CERTIFICATE_DIRECTORY}/{index:04d}-{catalog_row['name']}-"
                f"{artifact_sha256}.pl2"
            ),
            "sha256": artifact_sha256,
        },
        "construction_metrics": _construction_metrics(catalog_row),
        "declared_dependencies": list(catalog_row["dependencies"]),
        "formula_sha256": _sha256(encode_formula(formula)),
        "index": index,
        "layer": catalog_row["layer"],
        "name": catalog_row["name"],
        "packed_tree_metrics": tree_metrics,
        "proof_term_sha256": _sha256(encode_proof(proof)),
        "script": list(catalog_row["script"]),
        "script_sha256": catalog_row["script_sha256"],
        "statement_canonical": canonical_statement,
        "statement_canonical_sha256": _sha256(canonical_statement.encode("utf-8")),
        "statement_source": catalog_row["statement"],
        "statement_source_sha256": catalog_row["statement_sha256"],
        "summary": catalog_row["summary"],
    }


def _aggregate(rows: list[dict[str, object]]) -> dict[str, int]:
    return {
        "artifact_bytes_maximum": max(row["artifact"]["bytes"] for row in rows),
        "artifact_bytes_total": sum(row["artifact"]["bytes"] for row in rows),
        "cut_nodes_total": sum(row["packed_tree_metrics"]["cut_nodes"] for row in rows),
        "proof_depth_maximum": max(row["packed_tree_metrics"]["proof_depth"] for row in rows),
        "proof_nodes_maximum": max(row["packed_tree_metrics"]["proof_nodes"] for row in rows),
        "proof_nodes_total": sum(row["packed_tree_metrics"]["proof_nodes"] for row in rows),
    }


def _fresh_worker_report(
    staging: Path, manifest: dict[str, object]
) -> dict[str, object]:
    report_path = staging.parent / "fresh-worker-report.json"
    pycache_root = staging.parent / "fresh-worker-pycache"
    pycache_root.mkdir()
    command = [
        sys.executable,
        "-I",
        "-S",
        "-X",
        f"pycache_prefix={pycache_root}",
        str(REPLAY_CLI_PATH),
        "--verify",
        "--output",
        str(staging),
        "--report",
        str(report_path),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=FRESH_REPLAY_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise LibraryReplayPackBuildError(
            "fresh isolated replay worker could not complete"
        ) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-2_000:]
        raise LibraryReplayPackBuildError(
            "fresh isolated replay worker rejected the staged pack"
            + (f": {detail}" if detail else "")
        )
    raw = _read_bounded_regular_file(
        report_path,
        label="fresh replay-worker report",
        limit=MAX_SCHEMA_BYTES,
    )
    report = _decode_canonical_document(
        raw,
        "fresh replay-worker report",
        limit=MAX_SCHEMA_BYTES,
    )
    expected = {
        "artifact_bytes_total": manifest["aggregate"]["artifact_bytes_total"],
        "format": REPLAY_VERIFICATION_FORMAT,
        "kernel_checked_count": manifest["theorem_count"],
        "logic_mode": LOGIC_MODE,
        "manifest_root_sha256": manifest["root_sha256"],
        "replay_root_sha256": manifest["replay_root_sha256"],
        "status": "passed",
        "theorem_count": manifest["theorem_count"],
        "v": REPLAY_VERIFICATION_VERSION,
        "worker_isolation": {
            "forbidden_import_prefixes": list(FORBIDDEN_REPLAY_IMPORT_PREFIXES),
            "forbidden_modules_loaded": [],
            "format": REPLAY_WORKER_ISOLATION_FORMAT,
            "fresh_repo_pycache": True,
            "guard": "meta-path-reject",
            "python_isolated_mode": True,
            "python_no_site": True,
            "v": REPLAY_WORKER_ISOLATION_VERSION,
        },
    }
    if report != expected:
        raise LibraryReplayPackBuildError(
            "fresh isolated replay worker produced an unexpected receipt"
        )
    return report


def build_live_replay_pack(
    output: Path = DEFAULT_OUTPUT,
    *,
    pack_id: str = DEFAULT_PACK_ID,
    progress: Callable[[str], None] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Build, isolated-replay, and atomically publish one live candidate pack."""

    if not isinstance(output, Path):
        raise TypeError("replay-pack output must be a pathlib.Path")
    output = Path(output)
    validate_replay_pack_id(pack_id)
    if output.exists() or output.is_symlink():
        raise LibraryReplayPackBuildError(
            "replay-pack output already exists; verify it or choose a fresh path"
        )
    emit = (lambda _message: None) if progress is None else progress
    emit("validating the living catalog and reconstructing cached certificates")
    before_live = library_epoch.live_tracked_catalog_identity()
    try:
        catalog_raw = _read_bounded_regular_file(
            CATALOG_PATH,
            label="live theorem catalog",
            limit=MAX_CATALOG_BYTES,
        )
        profile_raw = _read_bounded_regular_file(
            SEMANTIC_PROFILE_PATH,
            label="live semantic profile",
            limit=MAX_PROFILE_BYTES,
        )
    except (OSError, ValueError) as exc:
        raise LibraryReplayPackBuildError("cannot read live pack inputs") from exc
    catalog_identity, catalog_rows = _catalog_from_bytes(catalog_raw)
    profile_identity, _ = _profile_identity_from_bytes(profile_raw)
    _matching_live_catalog(catalog_identity)
    if len(catalog_rows) != len(theorem_library.THEOREMS):
        raise LibraryReplayPackBuildError("catalog and living theorem counts differ")

    output_parent = output.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".peano-hydra-replay-pack-", dir=output_parent
    ) as temporary:
        staging = Path(temporary) / "pack"
        certificates = staging / CERTIFICATE_DIRECTORY
        certificates.mkdir(parents=True)
        schema_raw = canonical_document_bytes(
            replay_pack_schema(), limit=MAX_SCHEMA_BYTES
        )
        (staging / SCHEMA_FILE).write_bytes(schema_raw)
        (staging / CATALOG_FILE).write_bytes(catalog_raw)
        (staging / PROFILE_FILE).write_bytes(profile_raw)

        rows: list[dict[str, object]] = []
        for index, (spec, catalog_row) in enumerate(
            zip(theorem_library.THEOREMS, catalog_rows, strict=True)
        ):
            if spec.name != catalog_row["name"]:
                raise LibraryReplayPackBuildError("living theorem order drifted")
            checked = theorem_library.replay(spec.name)
            if checked.spec != spec or not check((), checked.certificate, checked.formula):
                raise LibraryReplayPackBuildError(
                    f"independent kernel rejected live theorem {spec.name!r}"
                )
            resources = proof_resource_metrics(checked.certificate)
            expected_resources = (
                catalog_row["proof_nodes"],
                catalog_row["proof_depth"],
                catalog_row["distinct_proof_objects"],
                catalog_row["proof_edges"],
                catalog_row["reused_proof_references"],
            )
            if resources != expected_resources or _cut_nodes(
                checked.certificate
            ) != catalog_row["cut_nodes"]:
                raise LibraryReplayPackBuildError(
                    f"live construction metrics drifted at {spec.name!r}"
                )
            fuel = FUEL_MULTIPLIER * catalog_row["proof_nodes"] + FUEL_OFFSET
            artifact = encode_artifact_bounded(
                fuel,
                checked.formula,
                checked.certificate,
                max_bytes=MAX_ARTIFACT_BYTES,
            )
            packed_row = _row(
                index,
                catalog_row,
                artifact=artifact,
                formula=checked.formula,
                proof=checked.certificate,
            )
            (staging / packed_row["artifact"]["path"]).write_bytes(artifact)
            rows.append(packed_row)
            if (index + 1) % 24 == 0 or index + 1 == len(catalog_rows):
                emit(f"encoded {index + 1}/{len(catalog_rows)} checked theorems")

        after_live = library_epoch.live_tracked_catalog_identity()
        if before_live != after_live:
            raise LibraryReplayPackBuildError(
                "living catalog changed during replay-pack construction"
            )
        body = {
            "aggregate": _aggregate(rows),
            "certificate_representation": CERTIFICATE_REPRESENTATION,
            "evaluation_eligible": False,
            "format": REPLAY_PACK_FORMAT,
            "id": pack_id,
            "kernel_identity": live_kernel_identity(),
            "logic_mode": LOGIC_MODE,
            "replay_root_sha256": replay_root_sha256(rows),
            "schema": replay_pack_schema_identity(),
            "semantic_profile": profile_identity,
            "source_catalog": catalog_identity,
            "status": PACK_STATUS,
            "theorem_count": len(rows),
            "theorems": rows,
            "v": REPLAY_PACK_VERSION,
        }
        manifest = validate_replay_pack_manifest(with_manifest_root(body))
        (staging / MANIFEST_FILE).write_bytes(canonical_document_bytes(manifest))
        emit("running fresh isolated byte-decoder and original-goal kernel replay")
        report = _fresh_worker_report(staging, manifest)
        if before_live != library_epoch.live_tracked_catalog_identity():
            raise LibraryReplayPackBuildError(
                "living catalog changed during isolated replay"
            )
        if manifest["kernel_identity"] != live_kernel_identity():
            raise LibraryReplayPackBuildError(
                "verifier sources changed during isolated replay"
            )
        os.replace(staging, output)
    emit(f"published replay-complete candidate pack at {output}")
    return manifest, report


__all__ = [
    "CATALOG_PATH",
    "DEFAULT_OUTPUT",
    "DEFAULT_PACK_ID",
    "LibraryReplayPackBuildError",
    "build_live_replay_pack",
]
