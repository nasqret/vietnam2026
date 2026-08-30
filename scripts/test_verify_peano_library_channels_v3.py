"""Determinism and fail-closed mutation tests for Alpha v3."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = REPOSITORY_ROOT / "artifacts" / "peano-library"
ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v3.json"
METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v3.json"
GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v3.mmd"
CHANNELS = ARTIFACT_ROOT / "channels-v3.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _load_module(
    "build_peano_library_channels_v3_under_test",
    REPOSITORY_ROOT / "scripts" / "build_peano_library_channels_v3.py",
)
VERIFIER = _load_module(
    "verify_peano_library_channels_v3_under_test",
    REPOSITORY_ROOT / "scripts" / "verify_peano_library_channels_v3.py",
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _write(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _shadow(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    """Copy every file independently opened by the v1/v2/v3 verifiers."""

    root = tmp_path / "repository"
    catalogs = [
        _load(ARTIFACT_ROOT / "alpha/catalog-v1.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v2.json"),
        _load(ALPHA),
    ]
    channel_documents = [
        _load(ARTIFACT_ROOT / "channels.json"),
        _load(ARTIFACT_ROOT / "channels-v2.json"),
        _load(CHANNELS),
    ]
    relative_paths = {
        descriptor["path"]
        for catalog in catalogs
        for descriptor in catalog["evidence_documents"]
    }
    relative_paths.update(
        row["source"]["path"]
        for catalog in catalogs
        for row in catalog["theorems"]
    )
    for channels in channel_documents:
        for channel in channels["channels"].values():
            relative_paths.update(
                pointer["path"] for pointer in channel["artifacts"].values()
            )
    relative_paths.update(
        {
            "artifacts/peano-library/channels.json",
            "artifacts/peano-library/channels-v2.json",
            "artifacts/peano-library/channels-v3.json",
        }
    )
    for relative in sorted(relative_paths):
        source = REPOSITORY_ROOT / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return root, {
        "alpha": root / ALPHA.relative_to(REPOSITORY_ROOT),
        "metrics": root / METRICS.relative_to(REPOSITORY_ROOT),
        "graph": root / GRAPH.relative_to(REPOSITORY_ROOT),
        "channels": root / CHANNELS.relative_to(REPOSITORY_ROOT),
    }


def _validate(
    root: Path,
    paths: dict[str, Path],
    *,
    replay_bodies: bool = False,
) -> dict[str, int]:
    return VERIFIER.validate_channels_v3(
        root,
        paths["alpha"],
        paths["metrics"],
        paths["graph"],
        paths["channels"],
        replay_bodies=replay_bodies,
    )


def _refresh_alpha_pointers(paths: dict[str, Path]) -> None:
    catalog_sha = sha256(paths["alpha"].read_bytes()).hexdigest()
    metrics = _load(paths["metrics"])
    metrics["catalog_sha256"] = catalog_sha
    _write(paths["metrics"], metrics)
    metrics_sha = sha256(paths["metrics"].read_bytes()).hexdigest()
    channels = _load(paths["channels"])
    alpha = channels["channels"]["alpha"]
    alpha["artifact_sha256"] = catalog_sha
    alpha["artifacts"]["catalog"]["sha256"] = catalog_sha
    alpha["artifacts"]["metrics"]["sha256"] = metrics_sha
    channels["channel_pointer_root_sha256"] = sha256(
        json.dumps(
            channels["channels"],
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()
    _write(paths["channels"], channels)


def test_repository_v3_validates_with_all_bertrand_body_replays() -> None:
    assert _validate(
        REPOSITORY_ROOT,
        {
            "alpha": ALPHA,
            "metrics": METRICS,
            "graph": GRAPH,
            "channels": CHANNELS,
        },
        replay_bodies=True,
    ) == {
        "alpha": 923,
        "alpha_closed": 138,
        "bertrand_replayed": 21,
        "body_checked": 352,
        "checked_use": 570,
        "parent_k3c_replayed": 0,
        "stable": 432,
    }


def test_v3_builder_is_byte_deterministic_for_all_outputs() -> None:
    assert BUILDER.build_payloads() == (
        ALPHA.read_text(encoding="utf-8"),
        METRICS.read_text(encoding="utf-8"),
        GRAPH.read_text(encoding="utf-8"),
        CHANNELS.read_text(encoding="utf-8"),
    )


def test_parent_prefix_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][0]["summary"] += " mutation"
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV3Error, match="first 902 rows"):
        _validate(root, paths)


def test_parent_family_binding_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["parent_alpha_v2"]["artifacts"]["metrics"]["sha256"] = "0" * 64
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV3Error, match="complete sealed v2"):
        _validate(root, paths)


def test_runtime_statement_and_dependencies_are_pinned(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    row = alpha["theorems"][902]
    row["statement"] = f"({row['statement']}) /\\ true"
    row["statement_sha256"] = sha256(row["statement"].encode()).hexdigest()
    row["dependencies"] = []
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV3Error, match="frozen Bertrand runtime"):
        _validate(root, paths)


@pytest.mark.parametrize("kind", ["source", "test", "rfc"])
def test_each_bertrand_evidence_document_is_byte_bound(
    tmp_path: Path,
    kind: str,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    row = alpha["theorems"][902]
    if kind == "source":
        relative = row["source"]["path"]
    elif kind == "test":
        relative = row["evidence_links"][1]["path"]
    else:
        relative = row["evidence_links"][2]["path"]
    document = root / relative
    document.write_text(
        document.read_text(encoding="utf-8") + "\n# mutation\n",
        encoding="utf-8",
    )
    with pytest.raises(VERIFIER.ChannelV3Error, match="document byte binding"):
        _validate(root, paths)


def test_fabricated_closure_status_checked_use_and_link_are_rejected(
    tmp_path: Path,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    row = alpha["theorems"][902]
    row["evidence_status"] = "alpha_closed"
    row["checked_use"] = True
    row["empty_context_closure"] = {"status": "checked"}
    row["evidence_links"][0].update(
        {
            "kind": "fabricated_closed_theorem",
            "role": "empty_context_closure",
            "selector": "fake",
        }
    )
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV3Error, match="evidence semantics"):
        _validate(root, paths)


def test_fake_proof_tag_is_rejected_even_with_refreshed_pointers(
    tmp_path: Path,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][902]["proof_tag"] = "PAFAKE"
    _write(paths["alpha"], alpha)
    _refresh_alpha_pointers(paths)
    with pytest.raises(VERIFIER.ChannelV3Error, match="untagged"):
        _validate(root, paths)


def test_cross_evidence_bundle_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][902]["bertrand_evidence_bundle_sha256"] = "0" * 64
    _write(paths["alpha"], alpha)
    _refresh_alpha_pointers(paths)
    with pytest.raises(VERIFIER.ChannelV3Error, match="cross-bind"):
        _validate(root, paths)


def test_body_receipt_mutation_is_rejected_by_fresh_kernel_replay(
    tmp_path: Path,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][902]["body_receipt"]["proof_nodes"] += 1
    _write(paths["alpha"], alpha)
    _refresh_alpha_pointers(paths)
    with pytest.raises(VERIFIER.ChannelV3Error, match="independent kernel body replay"):
        _validate(root, paths, replay_bodies=True)


def test_reduced_graph_and_metrics_mutations_are_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    paths["graph"].write_text(
        paths["graph"].read_text(encoding="utf-8") + "%% mutation\n",
        encoding="utf-8",
    )
    with pytest.raises(VERIFIER.ChannelV3Error, match="canonical reduced"):
        _validate(root, paths)

    root, paths = _shadow(tmp_path / "metrics")
    metrics = _load(paths["metrics"])
    metrics["dependency_graph"]["declared_edge_count"] += 1
    _write(paths["metrics"], metrics)
    with pytest.raises(VERIFIER.ChannelV3Error, match="canonical topology"):
        _validate(root, paths)


@pytest.mark.parametrize("artifact", ["catalog", "metrics", "dependency_graph"])
def test_each_alpha_v3_artifact_pointer_is_byte_bound(
    tmp_path: Path,
    artifact: str,
) -> None:
    root, paths = _shadow(tmp_path)
    channels = _load(paths["channels"])
    channels["channels"]["alpha"]["artifacts"][artifact]["sha256"] = "0" * 64
    _write(paths["channels"], channels)
    with pytest.raises(VERIFIER.ChannelV3Error, match="artifact family pointers"):
        _validate(root, paths)


def test_stable_pointer_object_cannot_change(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    channels = deepcopy(_load(paths["channels"]))
    channels["channels"]["stable"]["checked_use_count"] = 431
    _write(paths["channels"], channels)
    with pytest.raises(VERIFIER.ChannelV3Error, match="exact Stable pointers"):
        _validate(root, paths)
