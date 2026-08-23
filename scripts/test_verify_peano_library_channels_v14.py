"""Fast, fail-closed evidence-boundary mutation tests for Alpha v14.

Every mutation shallow-copies one actual Kummer frontier row.  Parent/channel
mutations stop before any proof replay; normal scans validate 13 already
recorded kernel-body receipts without recursively checking the parent.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any, Callable

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


VERIFIER = _load_module(
    "verify_peano_library_channels_v14_under_test",
    REPOSITORY_ROOT / "scripts" / "verify_peano_library_channels_v14.py",
)
BUILDER = VERIFIER.builder


@pytest.fixture(scope="module")
def release() -> dict[str, Any]:
    catalog = VERIFIER._load(BUILDER.DEFAULT_ALPHA)
    rows = catalog["theorems"][BUILDER.EXPECTED_PARENT_COUNT :]
    documents = {
        document["path"]: document
        for document in catalog["evidence_documents"]
        if type(document) is dict
    }
    return {
        "catalog": catalog,
        "rows": rows,
        "documents": documents,
        "metrics": VERIFIER._load(BUILDER.DEFAULT_ALPHA_METRICS),
        "channels": VERIFIER._load(BUILDER.DEFAULT_CHANNELS),
        "parent_channels": VERIFIER._load(BUILDER.PARENT_CHANNELS),
    }


def _mutated_rows(
    release: dict[str, Any], mutate: Callable[[dict[str, Any]], None]
) -> list[dict[str, Any]]:
    rows = list(release["rows"])
    first = dict(rows[0])
    mutate(first)
    rows[0] = first
    return rows


def _set_field(name: str, value: Any) -> Callable[[dict[str, Any]], None]:
    return lambda row: row.__setitem__(name, value)


def _set_nested_field(
    container: str, name: str, value: Any
) -> Callable[[dict[str, Any]], None]:
    def mutate(row: dict[str, Any]) -> None:
        nested = dict(row[container])
        nested[name] = value
        row[container] = nested

    return mutate


def _set_evidence_link(
    name: str, value: Any
) -> Callable[[dict[str, Any]], None]:
    def mutate(row: dict[str, Any]) -> None:
        links = list(row["evidence_links"])
        first = dict(links[0])
        first[name] = value
        links[0] = first
        row["evidence_links"] = links

    return mutate


def test_actual_frontier_has_13_valid_dependency_curried_body_receipts(
    release: dict[str, Any],
) -> None:
    receipts = VERIFIER._verify_frontier_rows(
        release["rows"], release["documents"]
    )
    assert len(receipts) == VERIFIER.FRONTIER_V14_EXPECTED_COUNT == 13
    assert set(VERIFIER.FRONTIER_V14_ROOT_NAMES) <= receipts.keys()
    assert all(
        receipt["status"] == "kernel_checked_dependency_curried_body"
        and receipt["proof_nodes"] > 0
        and receipt["proof_objects"] > 0
        for receipt in receipts.values()
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("checked_use", True),
        ("evidence_status", "alpha_closed"),
        ("evidence_status", "stable_closed"),
        ("membership", "stable"),
        ("membership", "alpha_and_stable"),
        ("empty_context_closure", {"fabricated": True}),
        ("empty_context_closure", "closed"),
        ("body_checked", False),
        ("proof_tag", "fabricated-empty-context-proof"),
        ("enrollment_origin", "stable"),
        ("provenance", ["ha", "stable"]),
        ("enrollment_index", -1),
    ),
    ids=(
        "fabricated-checked-use",
        "fabricated-alpha-closure",
        "fabricated-stable-closure",
        "fabricated-stable-membership",
        "fabricated-dual-membership",
        "fabricated-empty-context-object",
        "fabricated-empty-context-string",
        "missing-checked-body",
        "fabricated-proof-tag",
        "fabricated-stable-origin",
        "fabricated-stable-provenance",
        "wrong-enrollment-index",
    ),
)
def test_verifier_rejects_fabricated_authority(
    release: dict[str, Any], field: str, value: Any
) -> None:
    rows = _mutated_rows(release, _set_field(field, value))
    with pytest.raises(ValueError, match="body-only evidence boundary"):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("statement", "forall n. n = S(n)"),
        ("dependencies", ["fabricated_dependency"]),
        ("script", ["apply fabricated_dependency"]),
        ("summary", "fabricated theorem summary"),
        ("statement_sha256", "0" * 64),
        ("dependencies_sha256", "0" * 64),
        ("script_sha256", "0" * 64),
        ("summary_sha256", "0" * 64),
        ("logical_spec_sha256", "0" * 64),
    ),
    ids=(
        "statement",
        "dependencies",
        "script",
        "summary",
        "statement-digest",
        "dependency-digest",
        "script-digest",
        "summary-digest",
        "logical-spec-digest",
    ),
)
def test_verifier_rejects_mutated_candidate_specification(
    release: dict[str, Any], field: str, value: Any
) -> None:
    rows = _mutated_rows(release, _set_field(field, value))
    with pytest.raises(ValueError, match="exact source specification"):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (_set_field("body_receipt", None), "no actual dependency-curried receipt"),
        (
            _set_nested_field("body_receipt", "name", "fabricated_theorem"),
            "inconsistent body receipt",
        ),
        (
            _set_nested_field("body_receipt", "dependency_count", -1),
            "inconsistent body receipt",
        ),
        (
            _set_nested_field("body_receipt", "command_count", -1),
            "inconsistent body receipt",
        ),
        (
            _set_nested_field("body_receipt", "dne_command_count", 1),
            "inconsistent body receipt",
        ),
        (
            _set_nested_field("body_receipt", "status", "alpha_closed"),
            "inconsistent body receipt",
        ),
        (
            _set_nested_field("body_receipt", "proof_nodes", "1"),
            "nonnumeric proof metric",
        ),
        (
            _set_nested_field("body_receipt", "proof_depth", None),
            "nonnumeric proof metric",
        ),
        (
            _set_nested_field("body_receipt", "proof_objects", "1"),
            "nonnumeric proof metric",
        ),
        (
            _set_nested_field("body_receipt", "proof_edges", None),
            "nonnumeric proof metric",
        ),
        (_set_nested_field("body_receipt", "proof_nodes", 0), "no actual proof object"),
        (_set_nested_field("body_receipt", "proof_objects", 0), "no actual proof object"),
    ),
    ids=(
        "missing-receipt",
        "wrong-theorem",
        "wrong-dependency-count",
        "wrong-command-count",
        "nonconstructive-dne",
        "fabricated-closure-status",
        "nonnumeric-nodes",
        "nonnumeric-depth",
        "nonnumeric-objects",
        "nonnumeric-edges",
        "zero-nodes",
        "zero-objects",
    ),
)
def test_verifier_rejects_fabricated_actual_proof_receipt(
    release: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    rows = _mutated_rows(release, mutate)
    with pytest.raises(ValueError, match=message):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (_set_field("frontier_campaign", "fabricated_campaign"), "campaign partition"),
        (_set_field("frontier_factory", "fabricated_factory"), "source-factory binding"),
        (
            _set_nested_field("source", "kind", "fabricated_source"),
            "candidate source binding",
        ),
        (
            _set_nested_field("source", "path", "fabricated/source.py"),
            "candidate source binding",
        ),
        (_set_nested_field("source", "sha256", "0" * 64), "candidate source binding"),
        (_set_field("evidence_links", []), "evidence links"),
        (
            _set_evidence_link("path", "fabricated/source.py"),
            "invalid evidence link",
        ),
        (
            _set_evidence_link("document_sha256", "0" * 64),
            "invalid evidence link",
        ),
        (
            _set_field("frontier_v14_evidence_bundle_sha256", "0" * 64),
            "actual-proof evidence bundle",
        ),
    ),
    ids=(
        "wrong-campaign",
        "wrong-factory",
        "source-kind",
        "source-path",
        "source-digest",
        "missing-evidence-links",
        "evidence-link-path",
        "evidence-link-digest",
        "evidence-bundle-digest",
    ),
)
def test_verifier_rejects_mutated_source_links_campaign_factory_or_bundle(
    release: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    rows = _mutated_rows(release, mutate)
    with pytest.raises(ValueError, match=message):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


def test_verifier_rejects_missing_inventory_document(
    release: dict[str, Any],
) -> None:
    documents = dict(release["documents"])
    documents.pop(release["rows"][0]["evidence_links"][0]["path"])
    with pytest.raises(ValueError, match="invalid evidence link"):
        VERIFIER._verify_frontier_rows(release["rows"], documents)


@pytest.mark.parametrize("mutation", ("reordered", "missing", "renamed"))
def test_verifier_rejects_nonminimal_or_reordered_frontier(
    release: dict[str, Any], mutation: str
) -> None:
    rows = list(release["rows"])
    if mutation == "reordered":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "missing":
        rows.pop()
    else:
        first = dict(rows[0])
        first["name"] = "fabricated_frontier_theorem"
        rows[0] = first
    with pytest.raises(ValueError, match="minimal topological frontier order"):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


def _isolate_loaded_release(
    monkeypatch: pytest.MonkeyPatch,
    release: dict[str, Any],
    *,
    catalog: dict[str, Any] | None = None,
    channels: dict[str, Any] | None = None,
) -> None:
    actual_catalog = release["catalog"] if catalog is None else catalog
    parent = {
        "schema": "peano-library-alpha-snapshot-v13",
        "theorem_count": BUILDER.EXPECTED_PARENT_COUNT,
        "theorems": release["catalog"]["theorems"][: BUILDER.EXPECTED_PARENT_COUNT],
        "ordered_enrollment_root_sha256": BUILDER.PARENT_ALPHA_V13_ENROLLMENT_SHA256,
        "edition_identity_sha256": BUILDER.PARENT_ALPHA_V13_IDENTITY_SHA256,
    }
    loaded = {
        BUILDER.PARENT_ALPHA: parent,
        BUILDER.DEFAULT_ALPHA: actual_catalog,
        BUILDER.DEFAULT_ALPHA_METRICS: release["metrics"],
        BUILDER.DEFAULT_CHANNELS: (
            release["channels"] if channels is None else channels
        ),
        BUILDER.PARENT_CHANNELS: release["parent_channels"],
    }

    def load(path: Path) -> dict[str, Any]:
        assert path in loaded, f"unexpected release artifact read: {path}"
        return loaded[path]

    monkeypatch.setattr(VERIFIER, "_load", load)
    monkeypatch.setattr(BUILDER, "_validate_parent", lambda _parent: None)


def test_verifier_rejects_mutated_sealed_parent_prefix(
    monkeypatch: pytest.MonkeyPatch, release: dict[str, Any]
) -> None:
    catalog = dict(release["catalog"])
    rows = list(catalog["theorems"])
    first = dict(rows[0])
    first["statement"] = "fabricated sealed parent statement"
    rows[0] = first
    catalog["theorems"] = rows
    _isolate_loaded_release(monkeypatch, release, catalog=catalog)
    with pytest.raises(ValueError, match="exact 1,543-row v13 ledger"):
        VERIFIER.verify()


@pytest.mark.parametrize(
    "mutation", ("stable-pointer", "default-channel", "pointer-root")
)
def test_verifier_rejects_stable_or_default_channel_tampering_without_replay(
    monkeypatch: pytest.MonkeyPatch,
    release: dict[str, Any],
    mutation: str,
) -> None:
    channels = dict(release["channels"])
    if mutation == "stable-pointer":
        pointers = dict(channels["channels"])
        stable = dict(pointers["stable"])
        stable["theorem_count"] = -1
        pointers["stable"] = stable
        channels["channels"] = pointers
    elif mutation == "default-channel":
        channels["default_channel"] = "alpha"
    else:
        channels["channel_pointer_root_sha256"] = "0" * 64

    _isolate_loaded_release(monkeypatch, release, channels=channels)
    monkeypatch.setattr(
        VERIFIER, "_verify_frontier_rows", lambda _rows, _documents: {}
    )

    def reject_any_proof_replay(*_args: Any, **_kwargs: Any) -> None:
        pytest.fail("channel mutation unexpectedly reached kernel-body replay")

    monkeypatch.setattr(VERIFIER, "replay_candidate_bodies", reject_any_proof_replay)
    with pytest.raises(ValueError, match="sealed Stable pointer or default channel"):
        VERIFIER.verify()
