"""Focused determinism and mutation tests for Stable/Alpha channel artifacts."""

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
ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v1.json"
ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics.json"
ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph.mmd"
CHANNELS = ARTIFACT_ROOT / "channels.json"
STABLE = ARTIFACT_ROOT / "catalog-v1.json"
STABLE_METRICS = ARTIFACT_ROOT / "metrics.json"
STABLE_GRAPH = ARTIFACT_ROOT / "dependency-graph.mmd"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _load_module(
    "build_peano_library_channels_under_test",
    REPOSITORY_ROOT / "scripts" / "build_peano_library_channels.py",
)
VERIFIER = _load_module(
    "verify_peano_library_channels_under_test",
    REPOSITORY_ROOT / "scripts" / "verify_peano_library_channels.py",
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
    """Copy exactly the files independently opened by the verifier."""

    root = tmp_path / "repository"
    alpha = _load(ALPHA)
    channels = _load(CHANNELS)
    relative_paths = {
        descriptor["path"] for descriptor in alpha["evidence_documents"]
    }
    relative_paths.update(
        row["source"]["path"] for row in alpha["theorems"]
    )
    for channel in channels["channels"].values():
        relative_paths.update(
            pointer["path"] for pointer in channel["artifacts"].values()
        )
    relative_paths.add("artifacts/peano-library/channels.json")
    for relative in sorted(relative_paths):
        source = REPOSITORY_ROOT / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return root, {
        "alpha": root / ALPHA.relative_to(REPOSITORY_ROOT),
        "alpha_metrics": root / ALPHA_METRICS.relative_to(REPOSITORY_ROOT),
        "alpha_graph": root / ALPHA_GRAPH.relative_to(REPOSITORY_ROOT),
        "channels": root / CHANNELS.relative_to(REPOSITORY_ROOT),
        "stable": root / STABLE.relative_to(REPOSITORY_ROOT),
        "stable_metrics": root / STABLE_METRICS.relative_to(REPOSITORY_ROOT),
        "stable_graph": root / STABLE_GRAPH.relative_to(REPOSITORY_ROOT),
    }


def _validate(root: Path, paths: dict[str, Path]) -> dict[str, int]:
    return VERIFIER.validate_channels(
        root,
        paths["alpha"],
        paths["alpha_metrics"],
        paths["alpha_graph"],
        paths["channels"],
        paths["stable"],
        paths["stable_metrics"],
        paths["stable_graph"],
    )


def test_repository_channels_validate_and_stable_bytes_remain_frozen() -> None:
    assert _validate(
        REPOSITORY_ROOT,
        {
            "alpha": ALPHA,
            "alpha_metrics": ALPHA_METRICS,
            "alpha_graph": ALPHA_GRAPH,
            "channels": CHANNELS,
            "stable": STABLE,
            "stable_metrics": STABLE_METRICS,
            "stable_graph": STABLE_GRAPH,
        },
    ) == {
        "alpha": 885,
        "alpha_closed": 138,
        "body_checked": 314,
        "checked_use": 570,
        "stable": 432,
    }
    assert sha256(STABLE.read_bytes()).hexdigest() == (
        "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"
    )


def test_generator_is_byte_deterministic_for_all_four_outputs() -> None:
    assert BUILDER.build_payloads() == (
        ALPHA.read_text(encoding="utf-8"),
        ALPHA_METRICS.read_text(encoding="utf-8"),
        ALPHA_GRAPH.read_text(encoding="utf-8"),
        CHANNELS.read_text(encoding="utf-8"),
    )


def test_release_membership_cannot_be_conflated_with_origin(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][432]["membership"] = "qr"
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelError, match="unknown membership"):
        _validate(root, paths)


def test_promotion_root_model_preserves_nonstable_enrollment_origin() -> None:
    alpha = _load(ALPHA)
    rows = alpha["theorems"]
    promoted = deepcopy(rows)
    assert promoted[432]["enrollment_origin"] == "qr"
    promoted[432]["membership"] = "stable"
    assert VERIFIER._ordered_root(promoted, include_origin=True) == (
        VERIFIER._ordered_root(rows, include_origin=True)
    )
    assert VERIFIER._ordered_root(promoted, include_origin=False) == (
        VERIFIER._ordered_root(rows, include_origin=False)
    )
    assert VERIFIER._membership_root(promoted) != VERIFIER._membership_root(rows)
    assert alpha["promotion_model"]["stable_relation"] == (
        "keyed exact subset of Alpha with its own append-only, "
        "dependency-topological release order"
    )


def test_source_sha_is_checked_against_repository_bytes(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][432]["source"]["sha256"] = "0" * 64
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelError, match="does not match source bytes"):
        _validate(root, paths)


def test_copied_closure_metrics_are_cross_bound_to_receipt(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][0]["empty_context_closure"]["proof_nodes"] += 1
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelError, match="stable closure metrics"):
        _validate(root, paths)


def test_forward_or_self_dependency_is_rejected(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["theorems"][0]["dependencies"] = ["zero_add"]
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelError, match="missing or not earlier"):
        _validate(root, paths)


def test_review_graph_is_recomputed_not_only_hashed(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    paths["alpha_graph"].write_text(
        paths["alpha_graph"].read_text(encoding="utf-8") + "%% mutation\n",
        encoding="utf-8",
    )
    with pytest.raises(VERIFIER.ChannelError, match="canonical reduced Alpha graph"):
        _validate(root, paths)


def test_metrics_are_recomputed_not_only_hashed(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    metrics = _load(paths["alpha_metrics"])
    metrics["dependency_graph"]["declared_edge_count"] += 1
    _write(paths["alpha_metrics"], metrics)
    with pytest.raises(VERIFIER.ChannelError, match="canonical Alpha topology analysis"):
        _validate(root, paths)


@pytest.mark.parametrize(
    ("channel", "artifact"),
    [
        ("stable", "catalog"),
        ("stable", "metrics"),
        ("stable", "dependency_graph"),
        ("alpha", "catalog"),
        ("alpha", "metrics"),
        ("alpha", "dependency_graph"),
    ],
)
def test_each_channel_family_pointer_is_byte_bound(
    tmp_path: Path,
    channel: str,
    artifact: str,
) -> None:
    root, paths = _shadow(tmp_path)
    channels = deepcopy(_load(paths["channels"]))
    channels["channels"][channel]["artifacts"][artifact]["sha256"] = "0" * 64
    _write(paths["channels"], channels)
    with pytest.raises(VERIFIER.ChannelError, match="does not match artifact bytes"):
        _validate(root, paths)


def test_canonical_enrollment_root_is_pinned_with_its_scheme(tmp_path: Path) -> None:
    root, paths = _shadow(tmp_path)
    alpha = _load(paths["alpha"])
    alpha["ordered_enrollment_root_scheme"]["row_separator"] = "U+000A"
    _write(paths["alpha"], alpha)
    with pytest.raises(VERIFIER.ChannelError, match="separator/field scheme changed"):
        _validate(root, paths)
