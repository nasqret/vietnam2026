"""Determinism and fail-closed mutation tests for Alpha v11."""

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
ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v11.json"
METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v11.json"
GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v11.mmd"
CHANNELS = ARTIFACT_ROOT / "channels-v11.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _load_module(
    "build_peano_library_channels_v11_under_test",
    REPOSITORY_ROOT / "scripts" / "build_peano_library_channels_v11.py",
)
VERIFIER = _load_module(
    "verify_peano_library_channels_v11_under_test",
    REPOSITORY_ROOT / "scripts" / "verify_peano_library_channels_v11.py",
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
    """Copy every repository file opened by the v1-through-v11 verifiers."""

    root = tmp_path / "repository"
    catalogs = [
        _load(ARTIFACT_ROOT / "alpha/catalog-v1.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v2.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v3.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v4.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v5.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v6.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v7.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v8.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v9.json"),
        _load(ARTIFACT_ROOT / "alpha/catalog-v10.json"),
        _load(ALPHA),
    ]
    channel_documents = [
        _load(ARTIFACT_ROOT / "channels.json"),
        _load(ARTIFACT_ROOT / "channels-v2.json"),
        _load(ARTIFACT_ROOT / "channels-v3.json"),
        _load(ARTIFACT_ROOT / "channels-v4.json"),
        _load(ARTIFACT_ROOT / "channels-v5.json"),
        _load(ARTIFACT_ROOT / "channels-v6.json"),
        _load(ARTIFACT_ROOT / "channels-v7.json"),
        _load(ARTIFACT_ROOT / "channels-v8.json"),
        _load(ARTIFACT_ROOT / "channels-v9.json"),
        _load(ARTIFACT_ROOT / "channels-v10.json"),
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
            "artifacts/peano-library/channels-v4.json",
            "artifacts/peano-library/channels-v5.json",
            "artifacts/peano-library/channels-v6.json",
            "artifacts/peano-library/channels-v7.json",
            "artifacts/peano-library/channels-v8.json",
            "artifacts/peano-library/channels-v9.json",
            "artifacts/peano-library/channels-v10.json",
            "artifacts/peano-library/channels-v11.json",
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
    replay_bodies: bool = True,
    replay_offsets: tuple[int, ...] | None = None,
    validate_parent: bool = False,
) -> dict[str, int]:
    return VERIFIER.validate_channels_v11(
        root,
        paths["alpha"],
        paths["metrics"],
        paths["graph"],
        paths["channels"],
        replay_bodies=replay_bodies,
        replay_offsets=replay_offsets,
        validate_parent=validate_parent,
    )


def test_repository_v11_validates_with_all_thirty_eight_body_replays() -> None:
    assert _validate(
        REPOSITORY_ROOT,
        {
            "alpha": ALPHA,
            "metrics": METRICS,
            "graph": GRAPH,
            "channels": CHANNELS,
        },
        validate_parent=True,
    ) == {
        "alpha": 1123,
        "alpha_closed": 138,
        "bertrand_replayed": 38,
        "body_checked": 552,
        "checked_use": 570,
        "stable": 432,
    }


def test_v11_builder_is_byte_deterministic_for_all_outputs() -> None:
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
    with pytest.raises(VERIFIER.ChannelV11Error, match="first 1085 rows"):
        _validate(root, paths, replay_bodies=False)


def test_parent_family_binding_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["parent_alpha_v10"]["artifacts"]["metrics"]["sha256"] = "0" * 64
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV11Error, match="sealed v10 binding"):
        _validate(root, paths, replay_bodies=False)


@pytest.mark.parametrize(
    "index",
    [1085, 1095, 1105, 1111, 1118],
)
def test_each_source_block_runtime_specification_is_pinned(
    tmp_path: Path,
    index: int,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    row = alpha["theorems"][index]
    row["statement"] = f"({row['statement']}) /\\ false"
    row["statement_sha256"] = sha256(row["statement"].encode()).hexdigest()
    row["dependencies"] = []
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV11Error, match="runtime specification"):
        _validate(root, paths, replay_bodies=False)


@pytest.mark.parametrize("index", [1085, 1095, 1105, 1111, 1118])
@pytest.mark.parametrize("kind", ["source", "test", "rfc"])
def test_source_test_and_rfc_documents_are_byte_bound(
    tmp_path: Path,
    index: int,
    kind: str,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    row = alpha["theorems"][index]
    relative = {
        "source": row["source"]["path"],
        "test": row["evidence_links"][1]["path"],
        "rfc": row["evidence_links"][2]["path"],
    }[kind]
    document = root / relative
    document.write_text(
        document.read_text(encoding="utf-8") + "\n# mutation\n",
        encoding="utf-8",
    )
    with pytest.raises(VERIFIER.ChannelV11Error, match="document byte binding"):
        _validate(root, paths, replay_bodies=False)


@pytest.mark.parametrize(
    "index",
    [1085, 1095, 1105, 1111, 1118],
)
def test_every_source_block_document_is_byte_bound(
    tmp_path: Path,
    index: int,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    document = root / alpha["theorems"][index]["source"]["path"]
    document.write_text(
        document.read_text(encoding="utf-8") + "\n# source mutation\n",
        encoding="utf-8",
    )
    with pytest.raises(VERIFIER.ChannelV11Error, match="document byte binding"):
        _validate(root, paths, replay_bodies=False)


@pytest.mark.parametrize("index", [1085, 1095, 1105, 1111, 1118])
def test_source_test_rfc_parent_cross_bundle_mutation_is_rejected(
    tmp_path: Path,
    index: int,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][index]["bertrand_v11_evidence_bundle_sha256"] = "0" * 64
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV11Error, match="cross-bind"):
        _validate(root, paths, replay_bodies=False)


def test_fabricated_closure_checked_use_and_proof_tag_are_rejected(
    tmp_path: Path,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    row = alpha["theorems"][1085]
    row["evidence_status"] = "alpha_closed"
    row["checked_use"] = True
    row["empty_context_closure"] = {"status": "checked"}
    row["proof_tag"] = "PAFAKE"
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelV11Error, match="untagged|fabricated"):
        _validate(root, paths, replay_bodies=False)


def test_body_receipt_mutation_is_rejected_by_fresh_kernel_replay(
    tmp_path: Path,
) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][1085]["body_receipt"]["proof_nodes"] += 1
    _write(paths["alpha"], alpha)
    with pytest.raises(
        VERIFIER.ChannelV11Error,
        match="independent kernel body replay",
    ):
        _validate(root, paths, replay_bodies=True, replay_offsets=(0,))


@pytest.mark.parametrize("artifact", ["alpha", "metrics", "graph", "channels"])
def test_each_v11_artifact_mutation_is_rejected(
    tmp_path: Path,
    artifact: str,
) -> None:
    root, paths = _shadow(tmp_path)
    if artifact in {"graph", "channels"}:
        paths[artifact].write_text(
            paths[artifact].read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
    else:
        value = _load(paths[artifact])
        value["theorem_count"] = 0
        _write(paths[artifact], value)
    with pytest.raises(VERIFIER.ChannelV11Error):
        _validate(root, paths, replay_bodies=False)


def test_stable_pointer_object_cannot_change(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    channels = deepcopy(_load(paths["channels"]))
    channels["channels"]["stable"]["checked_use_count"] = 431
    _write(paths["channels"], channels)
    with pytest.raises(VERIFIER.ChannelV11Error, match="byte-canonical|Stable"):
        _validate(root, paths, replay_bodies=False)


def test_sealed_v10_parent_artifact_mutation_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    parent = root / "artifacts/peano-library/alpha/catalog-v10.json"
    parent.write_text(parent.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(VERIFIER.ChannelV11Error, match="sealed Alpha v10 parent"):
        _validate(root, paths, replay_bodies=False)
