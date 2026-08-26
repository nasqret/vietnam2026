"""Bounded component proposals remain unauthorized until later human review."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
for import_root in (ROOT, Path(__file__).resolve().parent):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from training.peano_hydra import lineage_review as module  # noqa: E402
from training.peano_hydra.benchmark import audit_preparation, build_development_benchmark  # noqa: E402
from training.peano_hydra.epoch import freeze_epoch  # noqa: E402
from training.peano_hydra.lineage_review import (  # noqa: E402
    LineageReviewError, build_lineage_inventory, build_lineage_review,
)
from training.peano_policy.prompt import CapabilityIdentity, PromptEnvironment, render_prompt  # noqa: E402
from training.peano_policy.search import state_sha256  # noqa: E402
# Reuse the existing bounded synthetic metadata fixtures, never actual model
# weights or claimed proof replays, for preparation-byte authentication tests.
from test_peano_hydra_benchmark import _epoch, _example, _preparation  # noqa: E402


def _bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _sha(value: object) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


@pytest.fixture(scope="module")
def original_source():
    path = ROOT / "artifacts/peano-hydra/development-2026-08-27/plan.json"
    return json.loads(path.read_text(encoding="utf-8"))["source"]


@pytest.fixture
def context(tmp_path, original_source):
    epoch = _epoch(
        ("train_seed", "forall n. n = n", ()),
        ("train_alias", "forall renamed. renamed = renamed", ("train_seed",)),
        ("dev_seed", "forall n m. (n = n /\\ m = m)", ()),
        ("reserve_seed", "exists x. x = 0", ()),
    )
    benchmark = build_development_benchmark(epoch)
    row = _example(epoch, "train_seed")
    path, manifest = _preparation(tmp_path / "prepared", epoch, (row,))
    audit = audit_preparation(benchmark, path, epoch=epoch)
    inventory = build_lineage_inventory(epoch, benchmark=benchmark)
    component_for = {
        name: component["component_id"]
        for component in inventory["components"] for name in component["catalog_members"]
    }
    allocation = [
        {
            "component_id": component["component_id"],
            "split": (
                "train" if component["component_id"] == component_for["train_seed"] else
                "dev" if component["component_id"] == component_for["dev_seed"] else "quarantine"
            ),
        }
        for component in inventory["components"]
    ]
    return {
        "epoch": epoch, "benchmark": benchmark, "row": row, "path": path,
        "manifest": manifest, "audit": audit, "inventory": inventory,
        "component_for": component_for, "allocations": allocation,
        "original_source": original_source,
    }


def _review(context, **overrides):
    options = {
        "benchmark": context["benchmark"],
        "audit_receipts": (context["audit"],),
        "preparation_dirs": (context["path"],),
        "allocations": context["allocations"],
        "original_source": context["original_source"],
        **overrides,
    }
    return build_lineage_review(context["epoch"], **options)


def _replace_file(context, filename, records):
    raw = b"".join(_bytes(row) + b"\n" for row in records)
    (context["path"] / filename).write_bytes(raw)
    context["manifest"]["files"][filename] = {
        "bytes": len(raw), "rows": len(records), "sha256": hashlib.sha256(raw).hexdigest(),
    }
    (context["path"] / "manifest.json").write_bytes(_bytes(context["manifest"]))


def _refresh_audit(context):
    context["audit"] = audit_preparation(context["benchmark"], context["path"], epoch=context["epoch"])


def test_inventory_is_a_complete_partition_and_retains_original_ids_masks(context):
    inventory = context["inventory"]
    assert inventory["catalog_theorem_count"] == 4
    assert sorted(name for component in inventory["components"] for name in component["catalog_members"]) == [
        "dev_seed", "reserve_seed", "train_alias", "train_seed",
    ]
    original = {component["id"] for component in context["benchmark"]["components"]}
    assert set(inventory["original_development_component_ids"]) == original
    assert original <= {component["component_id"] for component in inventory["components"]}
    assert context["component_for"]["train_seed"] == context["component_for"]["train_alias"]
    assert inventory["structural_candidate_component_count"] == 3
    for goal in context["benchmark"]["goals"]:
        assert inventory["retained_mask_inventory"][goal["mask_sha256"]]["masked_theorems"] == goal["masked_theorems"]
    assert inventory["complete_catalog_partition"] is True
    assert inventory["eligible_for_unseen_model_comparison"] is False


def test_inventory_is_deterministic_and_detached(context):
    inventory = context["inventory"]
    assert inventory == build_lineage_inventory(context["epoch"], benchmark=context["benchmark"])
    assert inventory["inventory_sha256"] == _sha({key: value for key, value in inventory.items() if key != "inventory_sha256"})
    inventory["components"][0]["families"].clear()
    assert build_lineage_inventory(context["epoch"], benchmark=context["benchmark"])["inventory_sha256"] == inventory["inventory_sha256"]


def test_original_current_epoch_giant_and_uncertain_masks_are_never_relaxed():
    epoch = freeze_epoch(ROOT)
    benchmark = build_development_benchmark(epoch)
    inventory = build_lineage_inventory(epoch, benchmark=benchmark)
    retained = [component for component in inventory["components"] if component["goal_ids"]]
    assert len(retained) == 1
    assert retained[0]["component_id"] == benchmark["components"][0]["id"]
    assert retained[0]["catalog_member_count"] == 2_048
    assert inventory["masked_catalog_theorem_count"] == 2_061
    assert inventory["unresolved_canonical_theorem_count"] == 740
    assert inventory["catalog_theorem_count"] == 2_080
    assert retained[0]["structural_candidate_only"] is False
    assert inventory["structural_candidate_theorem_count"] <= 19


def test_valid_whole_component_proposal_is_not_reviewed_or_authorized(context):
    result = _review(context)
    assert result["status"] == "not-reviewed"
    assert result["conflicts"] == []
    assert result["original_source_workspace_and_git_authenticated"] is True
    assert result["feasibility"]["distinct_train_dev_components_exist_under_declared_relations"] is True
    assert result["model_facing_proposal"]["approved_train_rows"] == 0
    assert result["model_facing_proposal"]["approved_dev_rows"] == 0
    assert result["human_review_acknowledgment"] is None
    for field in (
        "independent_human_review_granted", "model_training_authorized", "model_comparison_authorized",
        "eligible_for_unseen_model_comparison", "semantic_equivalence_complete", "sealed_benchmark", "research_claim_eligible",
    ):
        assert result[field] is False
    assert all(item["status"] == "not-reviewed" for item in result["review_requirements"])
    assert result["review_sha256"] == _sha({key: value for key, value in result.items() if key != "review_sha256"})


def test_default_template_quarantines_public_dev_and_leaves_other_components_unassigned(context):
    result = _review(context, allocations=None)
    assert result["status"] == "blocked"
    assert result["default_unassigned_template"] is True
    assert result["model_facing_proposal"]["train_component_ids"] == []
    assert result["model_facing_proposal"]["dev_component_ids"] == []
    assert set(result["model_facing_proposal"]["quarantine_component_ids"]) == set(context["inventory"]["original_development_component_ids"])
    assert len(result["model_facing_proposal"]["unassigned_component_ids"]) == 3
    assert all(row["explicitly_proposed"] is False for row in result["allocations"])


def test_missing_allocation_is_a_traceable_conflict_not_implicit_quarantine(context):
    removed = context["allocations"].pop()
    result = _review(context)
    missing = [row for row in result["conflicts"] if row["code"] == "component_allocation_missing_or_unassigned"]
    assert len(missing) == 1
    assert missing[0]["component_id"] == removed["component_id"]
    assert missing[0]["conflict_id"] == _sha({key: value for key, value in missing[0].items() if key != "conflict_id"})
    assert result["status"] == "blocked"


def test_allocation_input_order_does_not_change_review_identity(context):
    first = _review(context)
    second = _review(context, allocations=list(reversed(context["allocations"])))
    assert first == second


@pytest.mark.parametrize("split", ("train", "dev"))
def test_original_dev_component_cannot_be_reclassified_as_model_data(context, split):
    identifier = context["inventory"]["original_development_component_ids"][0]
    for row in context["allocations"]:
        if row["component_id"] == identifier:
            row["split"] = split
    result = _review(context)
    assert result["status"] == "blocked"
    assert any(row["code"] == "component_conflicts_with_retained_benchmark_masks" and row["component_id"] == identifier for row in result["conflicts"])
    assert result["feasibility"]["current_eight_development_families_unseen"] is False


def test_exposure_outside_original_dev_components_blocks_a_new_dev_allocation(context):
    # train_seed is outside every public DEV component, but the audit's full
    # root inventory exposes it and its differently spelled canonical alias.
    for row in context["allocations"]:
        if row["split"] == "train":
            row["split"] = "dev"
        elif row["split"] == "dev":
            row["split"] = "train"
    result = _review(context)
    assert result["status"] == "blocked"
    assert any(row["code"] == "development_component_already_exposed" for row in result["conflicts"])
    assert context["component_for"]["train_seed"] not in result["feasibility"]["unexposed_structural_component_ids"]


def test_closed_intermediate_goal_alias_is_inspected_outside_old_dev_targets(context):
    row = context["row"]
    target = context["epoch"].theorem("dev_seed").statement
    goals = (f"⊢ {target}",)
    environment = PromptEnvironment(False, CapabilityIdentity(context["epoch"].surface_label, ("refl",), ()))
    prompt = render_prompt(goals=goals, focus=0, environment=environment)
    row["prompt"] = row["transition"]["prompt"] = prompt
    row["state_sha256"] = row["transition"]["state_sha256"] = state_sha256(goals)
    row["transition"]["goals_before"] = list(goals)
    row["source_transition_sha256"] = _sha(row["transition"])
    _replace_file(context, "train.jsonl", (row,))
    _refresh_audit(context)
    assert "dev_seed" not in context["audit"]["exposed_theorem_roots"]["train"]
    result = _review(context)
    identifier = context["component_for"]["dev_seed"]
    assert any(row["code"] == "development_component_already_exposed" and row["component_id"] == identifier for row in result["conflicts"])
    supplemental = result["audits"][0]["supplemental_exposure"]
    entry = next(row for row in supplemental["components"] if row["component_id"] == identifier)
    assert entry["row_reference_count"] == 1
    assert entry["row_references"][0]["file"] == "train.jsonl"
    assert entry["row_references"][0]["row"] == 1
    assert entry["row_references"][0]["source_row_sha256"] == _sha(row)


def test_unknown_candidate_derivation_blocks_even_disjoint_catalog_allocations(context):
    candidate = _example(context["epoch"], "uncataloged_candidate", source="0 = 0")
    path, manifest = _preparation(context["path"].parent / "unknown-preparation", context["epoch"], (candidate,))
    context["path"], context["manifest"] = path, manifest
    _refresh_audit(context)
    result = _review(context)
    assert result["status"] == "blocked"
    assert any(row["code"] == "uncataloged_exposure_derivations_unresolved" for row in result["conflicts"])
    assert result["feasibility"]["distinct_train_dev_components_exist_under_declared_relations"] is False


def test_no_unexposed_candidate_has_an_explicit_infeasibility_conflict(context):
    rows = tuple(_example(context["epoch"], name) for name in ("train_seed", "dev_seed", "reserve_seed"))
    path, manifest = _preparation(context["path"].parent / "all-exposed", context["epoch"], rows)
    context["path"], context["manifest"] = path, manifest
    _refresh_audit(context)
    result = _review(context)
    assert result["feasibility"]["unexposed_structural_component_count"] == 0
    assert result["feasibility"]["distinct_train_dev_components_exist_under_declared_relations"] is False
    assert any(row["code"] == "no_disjoint_train_dev_allocation_under_retained_graph" for row in result["conflicts"])
    assert result["complete_model_exposure_history_attested"] is False


@pytest.mark.parametrize("allocation", (
    [{"component_id": "theorem_name_not_a_component", "split": "train"}],
    [{"component_id": "0" * 64, "split": "dev"}],
    {"train": []},
))
def test_unknown_partial_or_nonarray_allocations_fail_before_audit(context, monkeypatch, allocation):
    monkeypatch.setattr(module, "audit_preparation", lambda *args, **kwargs: pytest.fail("invalid allocation reached data exposure"))
    with pytest.raises(LineageReviewError, match="allocation"):
        _review(context, allocations=allocation)


def test_duplicate_component_cannot_enter_train_and_dev(context):
    identifier = context["component_for"]["train_seed"]
    with pytest.raises(LineageReviewError, match="more than once or across TRAIN/DEV"):
        _review(context, allocations=[{"component_id": identifier, "split": "train"}, {"component_id": identifier, "split": "dev"}])


@pytest.mark.parametrize("split", ("sealed", "approved", "test", True, None))
def test_unknown_split_roles_never_grant_authority(context, split):
    with pytest.raises(LineageReviewError, match="allocation split"):
        _review(context, allocations=[{"component_id": context["component_for"]["train_seed"], "split": split}])


def test_agent_cannot_inject_a_human_review_field(context):
    with pytest.raises(LineageReviewError, match="exactly component_id and split"):
        _review(context, allocations=[{"component_id": context["component_for"]["train_seed"], "split": "train", "human_reviewed": True}])
    with pytest.raises(TypeError, match="human_review_acknowledgment"):
        _review(context, human_review_acknowledgment={"approved": True})


def test_original_benchmark_mask_tampering_fails_before_source_or_data(context, monkeypatch):
    changed = deepcopy(context["benchmark"])
    changed["goals"][0]["masked_theorems"] = ["invented"]
    changed["manifest_sha256"] = _sha({key: value for key, value in changed.items() if key != "manifest_sha256"})
    monkeypatch.setattr(module, "audit_preparation", lambda *args, **kwargs: pytest.fail("tampered benchmark reached row exposure"))
    with pytest.raises(LineageReviewError, match="original benchmark authentication"):
        _review(context, benchmark=changed)


def test_rehashed_audit_cannot_hide_actual_exposure(context):
    changed = deepcopy(context["audit"])
    changed["exposed_theorem_roots"]["train"] = []
    changed["audit_sha256"] = _sha({key: value for key, value in changed.items() if key != "audit_sha256"})
    with pytest.raises(LineageReviewError, match="regenerated original preparation audit"):
        _review(context, audit_receipts=(changed,))


def test_preparation_byte_tampering_fails_closed(context):
    (context["path"] / "train.jsonl").write_bytes(b"{}\n")
    with pytest.raises(LineageReviewError, match="could not be reauthenticated"):
        _review(context)


def test_duplicate_receipts_or_original_directories_are_not_multiple_observations(context):
    with pytest.raises(LineageReviewError, match="duplicate original preparation"):
        _review(context, audit_receipts=(context["audit"], context["audit"]), preparation_dirs=(context["path"], context["path"]))


def test_missing_source_or_audits_never_yields_an_approved_plan(context):
    missing_source = _review(context, original_source=None)
    assert missing_source["status"] == "blocked"
    assert any(row["code"] == "original_source_provenance_missing" for row in missing_source["conflicts"])
    missing_audit = _review(context, audit_receipts=(), preparation_dirs=())
    assert missing_audit["status"] == "blocked"
    assert any(row["code"] == "authenticated_preparation_exposure_missing" for row in missing_audit["conflicts"])
    assert missing_audit["feasibility"]["unexposed_structural_component_count"] == 0


def test_original_source_selfhash_is_not_sufficient_commit_authentication(context):
    changed = deepcopy(context["original_source"])
    changed["git_commit"] = "0" * 40
    with pytest.raises(LineageReviewError, match="authenticated from local Git"):
        _review(context, original_source=changed)


def test_frozen_source_workspace_bytes_are_rechecked(context, monkeypatch):
    monkeypatch.setattr(module, "_read_source", lambda _: b"not the frozen implementation")
    with pytest.raises(LineageReviewError, match="frozen source differs from the workspace"):
        _review(context)


@pytest.mark.parametrize("field,value", (("git_dirty", True), ("files_sha256", "0" * 64)))
def test_original_source_identity_tampering_is_rejected(context, field, value):
    changed = deepcopy(context["original_source"])
    changed[field] = value
    with pytest.raises(LineageReviewError, match="original source changed"):
        _review(context, original_source=changed)


def test_supplemental_reference_budget_is_fail_closed(context, monkeypatch):
    monkeypatch.setattr(module, "MAX_SUPPLEMENTAL_ROW_REFERENCES", 0)
    with pytest.raises(LineageReviewError, match="retained row-reference bound"):
        _review(context)


def test_conflict_and_source_outputs_are_complete_and_deterministic(context):
    first = _review(context, allocations=None)
    second = _review(context, allocations=None)
    assert first == second
    assert first["model_calls"] == first["solver_calls"] == 0
    assert first["training_corpus_replayed"] is False
    assert first["audits"][0]["audit"] == context["audit"]
    assert first["planner_source"]["sha256"] == hashlib.sha256((ROOT / first["planner_source"]["path"]).read_bytes()).hexdigest()
