"""Determinism and fail-closed mutation tests for Alpha v2."""

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
ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v2.json"
METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v2.json"
GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v2.mmd"
CHANNELS = ARTIFACT_ROOT / "channels-v2.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _load_module(
    "build_peano_library_channels_v2_under_test",
    REPOSITORY_ROOT / "scripts" / "build_peano_library_channels_v2.py",
)
VERIFIER = _load_module(
    "verify_peano_library_channels_v2_under_test",
    REPOSITORY_ROOT / "scripts" / "verify_peano_library_channels_v2.py",
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
    """Copy every file independently opened by the v1/v2 verifiers."""

    root = tmp_path / "repository"
    alpha_v2 = _load(ALPHA)
    alpha_v1 = _load(ARTIFACT_ROOT / "alpha" / "catalog-v1.json")
    channels_v2 = _load(CHANNELS)
    channels_v1 = _load(ARTIFACT_ROOT / "channels.json")
    relative_paths = {
        descriptor["path"]
        for catalog in (alpha_v1, alpha_v2)
        for descriptor in catalog["evidence_documents"]
    }
    relative_paths.update(
        row["source"]["path"]
        for catalog in (alpha_v1, alpha_v2)
        for row in catalog["theorems"]
    )
    for channels in (channels_v1, channels_v2):
        for channel in channels["channels"].values():
            relative_paths.update(
                pointer["path"] for pointer in channel["artifacts"].values()
            )
    relative_paths.update(
        {
            "artifacts/peano-library/channels.json",
            "artifacts/peano-library/channels-v2.json",
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
    return VERIFIER.validate_channels_v2(
        root,
        paths["alpha"],
        paths["metrics"],
        paths["graph"],
        paths["channels"],
        replay_bodies=replay_bodies,
    )


def test_repository_v2_validates_with_independent_k3c_body_replay() -> None:
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
        "alpha": 902,
        "alpha_closed": 138,
        "body_checked": 331,
        "checked_use": 570,
        "k3c_replayed": 17,
        "stable": 432,
    }
    assert sha256((ARTIFACT_ROOT / "catalog-v1.json").read_bytes()).hexdigest() == (
        "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"
    )


def test_v2_builder_is_byte_deterministic_for_all_outputs() -> None:
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
    with pytest.raises(VERIFIER.ChannelV2Error, match="first 885 rows"):
        _validate(root, paths)


def test_parent_binding_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["parent_alpha_v1"]["artifact_sha256"] = "0" * 64
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV2Error, match="exactly bind sealed v1 parent"):
        _validate(root, paths)


def test_k3c_runtime_statement_is_pinned(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    row = alpha["theorems"][885]
    row["statement"] = f"({row['statement']}) /\\ true"
    row["statement_sha256"] = sha256(row["statement"].encode()).hexdigest()
    logical = {
        "dependencies": row["dependencies"],
        "name": row["name"],
        "script": row["script"],
        "statement": row["statement"],
    }
    row["logical_spec_sha256"] = sha256(
        json.dumps(logical, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV2Error, match="frozen K3C runtime"):
        _validate(root, paths)


def test_k3c_checked_use_upgrade_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][885]["checked_use"] = True
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV2Error, match="fail closed"):
        _validate(root, paths)


def test_k3c_source_byte_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    source = root / alpha["theorems"][885]["source"]["path"]
    source.write_text(source.read_text(encoding="utf-8") + "\n# mutation\n", encoding="utf-8")
    with pytest.raises(VERIFIER.ChannelV2Error, match="document byte binding"):
        _validate(root, paths)


def test_k3c_source_kind_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][885]["source"]["kind"] = "stable_registry"
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV2Error, match="source kind/path/digest semantics"):
        _validate(root, paths)


def test_k3c_fabricated_closed_theorem_link_and_fake_selector_are_rejected(
    tmp_path: Path,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    row = alpha["theorems"][885]
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
    with pytest.raises(VERIFIER.ChannelV2Error, match="evidence-link kind/role/selector"):
        _validate(root, paths)


def test_k3c_fake_proof_tag_is_rejected_after_pointer_recomputation(
    tmp_path: Path,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][885]["proof_tag"] = "PAFAKE"
    _write(paths["alpha"], alpha)
    catalog_sha = sha256(paths["alpha"].read_bytes()).hexdigest()
    metrics = _load(paths["metrics"])
    metrics["catalog_sha256"] = catalog_sha
    _write(paths["metrics"], metrics)
    metrics_sha = sha256(paths["metrics"].read_bytes()).hexdigest()
    channels = _load(paths["channels"])
    channels["channels"]["alpha"]["artifact_sha256"] = catalog_sha
    channels["channels"]["alpha"]["artifacts"]["catalog"]["sha256"] = catalog_sha
    channels["channels"]["alpha"]["artifacts"]["metrics"]["sha256"] = metrics_sha
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
    with pytest.raises(VERIFIER.ChannelV2Error, match="K3C rows are untagged"):
        _validate(root, paths)


def test_definition_surface_evidence_role_is_sealed(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    descriptor = next(
        item
        for item in alpha["evidence_documents"]
        if item["path"].endswith("ha_cell_list_membership_surface_candidate.py")
    )
    descriptor["role"] = "generic control source"
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV2Error, match="sealed control/audit-document role"):
        _validate(root, paths)


def test_body_receipt_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][885]["body_receipt"]["proof_nodes"] += 1
    _write(paths["alpha"], alpha)
    catalog_sha = sha256(paths["alpha"].read_bytes()).hexdigest()
    metrics = _load(paths["metrics"])
    metrics["catalog_sha256"] = catalog_sha
    _write(paths["metrics"], metrics)
    metrics_sha = sha256(paths["metrics"].read_bytes()).hexdigest()
    channels = _load(paths["channels"])
    channels["channels"]["alpha"]["artifact_sha256"] = catalog_sha
    channels["channels"]["alpha"]["artifacts"]["catalog"]["sha256"] = catalog_sha
    channels["channels"]["alpha"]["artifacts"]["metrics"]["sha256"] = metrics_sha
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
    with pytest.raises(VERIFIER.ChannelV2Error, match="independent kernel body replay"):
        _validate(root, paths, replay_bodies=True)


def test_reduced_graph_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    paths["graph"].write_text(
        paths["graph"].read_text(encoding="utf-8") + "%% mutation\n",
        encoding="utf-8",
    )
    with pytest.raises(VERIFIER.ChannelV2Error, match="canonical reduced"):
        _validate(root, paths)


def test_metrics_topology_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    metrics = _load(paths["metrics"])
    metrics["dependency_graph"]["declared_edge_count"] += 1
    _write(paths["metrics"], metrics)
    with pytest.raises(VERIFIER.ChannelV2Error, match="canonical topology"):
        _validate(root, paths)


@pytest.mark.parametrize("artifact", ["catalog", "metrics", "dependency_graph"])
def test_each_alpha_v2_artifact_pointer_is_byte_bound(
    tmp_path: Path,
    artifact: str,
) -> None:
    root, paths = _shadow(tmp_path)
    channels = _load(paths["channels"])
    channels["channels"]["alpha"]["artifacts"][artifact]["sha256"] = "0" * 64
    _write(paths["channels"], channels)
    with pytest.raises(VERIFIER.ChannelV2Error, match="artifact family pointers"):
        _validate(root, paths)


def test_stable_pointer_object_cannot_change(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    channels = deepcopy(_load(paths["channels"]))
    channels["channels"]["stable"]["checked_use_count"] = 431
    _write(paths["channels"], channels)
    with pytest.raises(VERIFIER.ChannelV2Error, match="exact Stable pointers"):
        _validate(root, paths)
