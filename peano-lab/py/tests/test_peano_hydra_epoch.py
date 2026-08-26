"""Checked Alpha epoch freezes and explicitly scoped theorem-use authority."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.batch import run_proof  # noqa: E402
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
import training.peano_hydra.epoch as epoch_module  # noqa: E402
from training.peano_hydra.epoch import HydraEpoch, HydraEpochError, freeze_epoch  # noqa: E402


@pytest.fixture(scope="module")
def frozen_epoch() -> HydraEpoch:
    return freeze_epoch(ROOT)


def test_current_release_freezes_two_distinct_dependency_graphs(
    frozen_epoch: HydraEpoch,
) -> None:
    record = frozen_epoch.to_dict()
    theorem_graph = record["theorem_dag"]
    definitions = record["definition_dag"]

    assert frozen_epoch.version.startswith("v")
    assert len(frozen_epoch.theorems) > frozen_epoch.stable_count == 432
    assert frozen_epoch.alpha_only_count == len(frozen_epoch.theorems) - 432
    assert theorem_graph["node_count"] == len(frozen_epoch.theorems)
    assert theorem_graph["edge_count"] == sum(
        len(item.dependencies) for item in frozen_epoch.theorems
    )
    assert theorem_graph["edge_kind"] == "proof_dependency"
    assert definitions["node_count"] == len(frozen_epoch.definitions)
    assert definitions["edge_count"] == sum(
        len(item.dependencies) for item in frozen_epoch.definitions
    )
    assert definitions["edge_kind"] == "definition_uses_definition"
    assert theorem_graph["sha256"] != definitions["sha256"]
    assert record["research_claim_eligible"] is False


def test_full_epoch_graphs_preserve_exact_safe_enrollment_order(
    frozen_epoch: HydraEpoch,
) -> None:
    record = frozen_epoch.to_dict(include_graphs=True)

    assert len(record["theorem_dag"]["nodes"]) == len(frozen_epoch.theorems)
    assert len(record["definition_dag"]["nodes"]) == len(frozen_epoch.definitions)
    assert record["theorem_dag"]["nodes"][0]["name"] == "zero_add"
    assert [row["enrollment_index"] for row in record["theorem_dag"]["nodes"]] == list(
        range(len(frozen_epoch.theorems))
    )


def test_hydra_alpha_access_requires_one_full_exact_edition_identity(
    frozen_epoch: HydraEpoch,
) -> None:
    name = next(
        theorem.name
        for theorem in frozen_epoch.theorems
        if theorem.membership == "alpha_only"
    )
    capability = frozen_epoch.alpha_capabilities(
        allowed_commands=frozenset({"exact", "use"}),
        allowed_theorems=frozenset({name}),
    )

    assert capability.label == frozen_epoch.surface_label
    assert capability.allowed_theorems == frozenset({name})
    assert capability.label.endswith(frozen_epoch.edition_identity_sha256)
    with pytest.raises(ValueError, match="unknown name"):
        SurfaceCapabilities(
            allowed_commands=frozenset({"exact", "use"}),
            allowed_theorems=frozenset({name}),
        )


@pytest.mark.parametrize("field", ("allowed_commands", "allowed_theorems"))
def test_hydra_alpha_authority_never_accepts_a_wildcard(
    frozen_epoch: HydraEpoch,
    field: str,
) -> None:
    options = {
        "label": frozen_epoch.surface_label,
        "allowed_commands": frozenset({"exact", "use"}),
        "allowed_theorems": frozenset({"zero_add"}),
    }
    options[field] = None
    with pytest.raises(ValueError, match="finite tactic and theorem allowlists"):
        SurfaceCapabilities(**options)


def test_changed_or_shortened_alpha_identity_never_grants_execution(
    frozen_epoch: HydraEpoch,
) -> None:
    last = "0" if frozen_epoch.edition_identity_sha256[-1] != "0" else "1"
    wrong = frozen_epoch.edition_identity_sha256[:-1] + last
    options = {
        "allowed_commands": frozenset({"exact", "use"}),
        "allowed_theorems": frozenset({"zero_add"}),
    }
    with pytest.raises(ValueError, match="exact sealed edition identity"):
        SurfaceCapabilities(label=f"hydra-alpha-{frozen_epoch.version}-{wrong}", **options)
    with pytest.raises(ValueError, match="exact version and 64-digit"):
        SurfaceCapabilities(
            label=f"hydra-alpha-{frozen_epoch.version}-{wrong[:12]}",
            **options,
        )


def test_alpha_execution_replays_checked_theorem_against_original_formula(
    frozen_epoch: HydraEpoch,
) -> None:
    capabilities = frozen_epoch.alpha_capabilities(
        allowed_commands=frozenset({"exact", "use"}),
        allowed_theorems=frozenset({"zero_add"}),
    )
    result = run_proof(
        "forall n. 0 + n = n",
        ("use zero_add as reviewed", "exact reviewed"),
        capabilities=capabilities,
    )

    assert result.status == "proved"
    assert result.kernel_checked is True
    assert result.surface == frozen_epoch.surface_label


def test_new_alpha_only_theorem_can_actually_be_replayed_and_used(
    frozen_epoch: HydraEpoch,
) -> None:
    theorem = frozen_epoch.theorem("crt_product_witness")
    assert theorem is not None
    assert theorem.membership == "alpha_only"
    capabilities = frozen_epoch.alpha_capabilities(
        allowed_commands=frozenset({"exact", "use"}),
        allowed_theorems=frozenset({theorem.name}),
    )
    result = run_proof(
        theorem.statement,
        (f"use {theorem.name} as independently_checked", "exact independently_checked"),
        capabilities=capabilities,
    )

    assert result.status == "proved"
    assert result.kernel_checked is True
    assert result.proof_nodes is not None
    assert result.surface == frozen_epoch.surface_label


def test_execution_rejects_theorem_outside_its_frozen_allowlist(
    frozen_epoch: HydraEpoch,
) -> None:
    capabilities = frozen_epoch.alpha_capabilities(
        allowed_commands=frozenset({"exact", "use"}),
        allowed_theorems=frozenset(),
    )
    result = run_proof(
        "forall n. 0 + n = n",
        ("use zero_add as reviewed",),
        capabilities=capabilities,
    )

    assert result.status == "tactic_error"
    assert result.kernel_checked is False


def test_unknown_epoch_theorem_never_expands_a_capability(
    frozen_epoch: HydraEpoch,
) -> None:
    with pytest.raises(HydraEpochError, match="escapes its frozen epoch"):
        frozen_epoch.alpha_capabilities(
            allowed_commands=frozenset({"use"}),
            allowed_theorems=frozenset({"an_unsealed_future_candidate"}),
        )


def test_stale_definition_snapshot_fails_before_hydra_authority(
    frozen_epoch: HydraEpoch,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del frozen_epoch
    original = epoch_module._artifact

    def modified(root: Path, relative: str):
        document, digest = original(root, relative)
        if relative.endswith("/definitions.json"):
            document = {
                **document,
                "campaign_snapshot_sha256": "0" * 64,
            }
        return document, digest

    monkeypatch.setattr(epoch_module, "_artifact", modified)
    with pytest.raises(HydraEpochError, match="does not match the exact current campaign"):
        freeze_epoch(ROOT)


def test_epoch_identity_changes_when_either_mathematical_graph_changes(
    frozen_epoch: HydraEpoch,
) -> None:
    modified = "0" * 64
    if frozen_epoch.theorem_dag_sha256 == modified:
        modified = "1" * 64
    assert replace(frozen_epoch, theorem_dag_sha256=modified).epoch_sha256 != (
        frozen_epoch.epoch_sha256
    )
    assert replace(frozen_epoch, reviewed_definition_dag_sha256=modified).epoch_sha256 != (
        frozen_epoch.epoch_sha256
    )


def _sample_catalog(epoch: HydraEpoch) -> tuple[dict, dict]:
    rows = []
    for theorem in epoch.theorems[:3]:
        rows.append(
            {
                "name": theorem.name,
                "statement": theorem.statement,
                "statement_sha256": theorem.statement_sha256,
                "script": list(theorem.script),
                "script_sha256": theorem.script_sha256,
                "dependencies": list(theorem.dependencies),
                "membership": theorem.membership,
                "checked_use": True,
                "body_checked": True,
                "empty_context_closure": {"status": "checked"},
                "evidence_status": (
                    "stable_closed" if theorem.membership == "stable" else "alpha_closed"
                ),
                "enrollment_index": theorem.enrollment_index,
            }
        )
    catalog = {
        "schema": f"peano-library-alpha-snapshot-{epoch.version}",
        "channel": "alpha",
        "theorem_count": 3,
        "checked_use_count": 3,
        "edge_count": sum(len(row["dependencies"]) for row in rows),
        "theorems": rows,
    }
    channel = {"theorem_count": 3, "checked_use_count": 3}
    return catalog, channel


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("statement_sha256", "0" * 64, "sealed statement"),
        ("script_sha256", "0" * 64, "sealed proof script"),
        ("checked_use", False, "checked Stable/Alpha authority"),
        ("body_checked", False, "checked Stable/Alpha authority"),
        ("empty_context_closure", {"status": "pending"}, "checked Stable/Alpha authority"),
        ("enrollment_index", 77, "enrollment order"),
    ),
)
def test_mutated_theorem_rows_never_enter_checked_epoch(
    frozen_epoch: HydraEpoch,
    field: str,
    value: object,
    error: str,
) -> None:
    catalog, channel = _sample_catalog(frozen_epoch)
    catalog["theorems"][0][field] = value

    with pytest.raises(HydraEpochError, match=error):
        epoch_module._theorems(catalog, version=frozen_epoch.version, channel=channel)


def test_forward_theorem_dependency_cannot_be_conflated_with_definition_edge(
    frozen_epoch: HydraEpoch,
) -> None:
    catalog, channel = _sample_catalog(frozen_epoch)
    catalog["theorems"][0]["dependencies"] = [catalog["theorems"][2]["name"]]

    with pytest.raises(HydraEpochError, match="cyclic, duplicate, or unavailable"):
        epoch_module._theorems(catalog, version=frozen_epoch.version, channel=channel)
