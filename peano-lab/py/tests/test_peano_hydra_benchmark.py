"""Whole-family public DEV lineage declarations and bounded exposure audits."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra import evaluation  # noqa: E402
from training.peano_hydra.benchmark import (  # noqa: E402
    HydraBenchmarkError,
    audit_preparation,
    build_development_benchmark,
    validate_benchmark,
)
from training.peano_hydra.curriculum import _lineage_index  # noqa: E402
from training.peano_hydra.epoch import EpochTheorem, HydraEpoch, freeze_epoch  # noqa: E402
from training.peano_hydra.protocol import validate_statement  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_HELD_OUT_POLICY_GOALS,
    held_out_contract_sha256,
)
from training.peano_policy.prompt import (  # noqa: E402
    COMPLETION_SUFFIX,
    PEANO_PROMPT_V3,
    CapabilityIdentity,
    PromptEnvironment,
    render_prompt,
)
from training.peano_policy.search import state_sha256  # noqa: E402


def _bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _sha(value: object) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _epoch(*specs: tuple[str, str, tuple[str, ...]]) -> HydraEpoch:
    # Synthetic metadata tests never claim these records were kernel replayed.
    theorems = tuple(
        EpochTheorem(name, statement, _sha(statement), (), _sha([]), dependencies, "stable", index)
        for index, (name, statement, dependencies) in enumerate(specs)
    )
    return HydraEpoch(
        version="v25",
        edition_identity_sha256="1" * 64,
        alpha_catalog_sha256=_sha(specs),
        stable_catalog_sha256=_sha(specs),
        definition_artifact_sha256="2" * 64,
        campaign_artifact_sha256="3" * 64,
        theorem_dag_sha256=_sha(specs),
        reviewed_definition_dag_sha256="4" * 64,
        milestone_dag_sha256="5" * 64,
        theorems=theorems,
        definitions=(),
        stable_count=len(theorems),
        theorem_edge_count=sum(len(item.dependencies) for item in theorems),
        definition_edge_count=0,
        milestone_count=0,
        milestone_edge_count=0,
        blueprint_definition_count=0,
        blueprint_definition_edge_count=0,
        notation_edge_count=0,
    )


@pytest.fixture
def synthetic_epoch() -> HydraEpoch:
    return _epoch(
        ("zero_add", "forall n. 0 + n = n", ()),
        ("add_comm", "forall n m. n + m = m + n", ("zero_add",)),
        ("add_assoc", "forall n m k. (n + m) + k = n + (m + k)", ("add_comm",)),
        ("mul_zero_left", "forall n. 0 * n = 0", ("zero_add",)),
        ("mul_comm", "forall n m. n * m = m * n", ("add_comm",)),
        ("mul_add", "forall n m k. n * (m + k) = n * m + n * k", ("add_comm",)),
        ("eq_symm", "forall n m. n = m -> m = n", ()),
        ("eq_trans", "forall n m k. n = m -> m = k -> n = k", ("eq_symm",)),
        ("add_congr", "forall n m. n = m -> n + 1 = m + 1", ("eq_symm", "add_comm")),
        ("le_refl", "forall n. n <= n", ()),
        ("le_trans", "forall n m k. n <= m -> m <= k -> n <= k", ("le_refl",)),
        ("isolated_reflexivity", "forall n. n = n", ()),
    )


def _example(epoch: HydraEpoch, name: str, *, source: str | None = None) -> dict[str, object]:
    enrolled = epoch.theorem(name)
    statement = validate_statement(source if source is not None else enrolled.statement)
    goals = (f"⊢ {statement}",)
    environment = PromptEnvironment(
        False,
        CapabilityIdentity(epoch.surface_label, ("refl",), ()),
    )
    prompt = render_prompt(goals=goals, focus=0, environment=environment)
    lineage = _lineage_index(epoch).get(name, _sha({"candidate": statement}))
    transition = {
        "schema": "peano-hydra-verified-transition-v1",
        "epoch_sha256": epoch.epoch_sha256,
        "theorem_name": name,
        "theorem": statement,
        "lineage_sha256": lineage,
        "split": "train",
        "step": 1,
        "state_sha256": state_sha256(goals),
        "goals_before": list(goals),
        "goals_after": [],
        "focus": 0,
        "action": "refl",
        "prompt": prompt,
        "completion": "refl" + COMPLETION_SUFFIX,
        "environment_sha256": environment.sha256,
        "kernel_checked": True,
    }
    return {
        "schema": evaluation.EXAMPLE_SCHEMA,
        "edition_identity_sha256": epoch.edition_identity_sha256,
        **{key: transition[key] for key in (
            "epoch_sha256", "theorem_name", "lineage_sha256", "split", "state_sha256",
            "action", "prompt", "completion", "environment_sha256", "kernel_checked",
        )},
        "theorem_statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
        "source_split": "train",
        "source_transition_sha256": _sha(transition),
        "transition": transition,
    }


def _preparation(
    path: Path, epoch: HydraEpoch, train: tuple[dict[str, object], ...] = (),
) -> tuple[Path, dict[str, object]]:
    path.mkdir()
    config_raw, config = evaluation.posttraining_config(epoch, output=path)
    files: dict[str, object] = {}
    for filename, records in (
        ("train.jsonl", train), ("dev.jsonl", ()), ("preferences.jsonl", ()),
        ("discovery.jsonl", ()), ("quarantine.jsonl", ()),
    ):
        raw = b"".join(_bytes(row) + b"\n" for row in records)
        (path / filename).write_bytes(raw)
        files[filename] = {"bytes": len(raw), "rows": len(records), "sha256": hashlib.sha256(raw).hexdigest()}
    (path / "config.toml").write_bytes(config_raw)
    files["config.toml"] = {"bytes": len(config_raw), "sha256": hashlib.sha256(config_raw).hexdigest()}
    lineages = sorted({row["lineage_sha256"] for row in train})
    heldout_digests = [hashlib.sha256(validate_statement(source).encode()).hexdigest() for _, source in MODEL_V3_HELD_OUT_POLICY_GOALS]
    manifest = {
        "schema": evaluation.PREPARATION_SCHEMA,
        "epoch_sha256": epoch.epoch_sha256,
        "edition_identity_sha256": epoch.edition_identity_sha256,
        "theorem_dag_sha256": epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": epoch.reviewed_definition_dag_sha256,
        "surface_label": epoch.surface_label,
        "version": epoch.version,
        "files": files,
        "model": {"model_id": evaluation.EXPECTED_BASE_MODEL_ID, "revision": evaluation.EXPECTED_BASE_MODEL_REVISION},
        "training": {"adapter_output_dir": config.run.output_dir},
        "splits": {
            "train": {"rows": len(train), "lineages": lineages, "theorems": sorted({row["theorem_name"] for row in train})},
            "dev": {"rows": 0, "lineages": [], "theorems": []},
        },
        "held_out": {
            "historical_v3_contract_sha256": held_out_contract_sha256(PEANO_PROMPT_V3),
            "excluded_goal_names": [name for name, _ in MODEL_V3_HELD_OUT_POLICY_GOALS],
            "excluded_goal_statement_sha256s": heldout_digests,
            "training_contamination_count": 0,
            "development_contamination_count": 0,
            "training_lineages": lineages,
            "development_lineages": [],
            "quarantined_lineages": [],
            "quarantine_rows": 0,
        },
        "model_trained": False,
        "sealed_benchmark": False,
        "research_claim_eligible": False,
        "alpha_admitted": False,
    }
    (path / "manifest.json").write_bytes(_bytes(manifest))
    return path, manifest


def _rewrite_train(path: Path, manifest: dict[str, object], rows: tuple[dict[str, object], ...]) -> None:
    payload = b"".join(_bytes(row) + b"\n" for row in rows)
    (path / "train.jsonl").write_bytes(payload)
    manifest["files"]["train.jsonl"] = {
        "bytes": len(payload), "rows": len(rows), "sha256": hashlib.sha256(payload).hexdigest(),
    }
    (path / "manifest.json").write_bytes(_bytes(manifest))


def test_predeclared_68_goals_keep_historical_and_correlated_seeds_separate(synthetic_epoch):
    result = build_development_benchmark(synthetic_epoch)
    assert result["goal_count"] == 68
    assert result["expanded_goal_count"] == 64
    assert result["historical_goal_count"] == 4
    assert result["declared_family_count"] == 8
    assert len({goal["id"] for goal in result["goals"]}) == 68
    historical = [goal for goal in result["goals"] if goal["cohort"] == "historical"]
    assert [(goal["id"], goal["source"]) for goal in historical] == list(MODEL_V3_HELD_OUT_POLICY_GOALS)
    assert all(goal["independent_of_other_family_seeds"] is False for goal in result["goals"])
    assert all(family["generator_seeds"] == list(range(8)) for family in result["families"])
    assert all(validate_statement(goal["source"]) == goal["canonical"] for goal in result["goals"])
    assert all(goal["allowed_theorems"] == goal["retrieval_allowed_theorems"] == [] for goal in result["goals"])
    assert result["construction"]["proof_scripts_supplied"] is False
    assert result["construction"]["outcomes_read"] == 0
    assert result["semantic_equivalence_complete"] is False
    assert result["eligible_for_unseen_model_comparison"] is False
    assert result["sealed_benchmark"] is False


def test_manifest_is_deterministic_detached_and_complete(synthetic_epoch):
    first = build_development_benchmark(synthetic_epoch)
    assert first == build_development_benchmark(synthetic_epoch)
    digest = first.pop("manifest_sha256")
    assert _sha(first) == digest
    first["families"][0]["catalog_anchors"].clear()
    assert build_development_benchmark(synthetic_epoch)["families"][0]["catalog_anchors"]


def test_declared_dependencies_and_authored_logic_join_entire_components(synthetic_epoch):
    result = build_development_benchmark(synthetic_epoch)
    assert result["declared_connected_component_count"] == 1
    component = result["components"][0]
    assert len(component["families"]) == 8
    assert "zero_add" in component["catalog_members"]
    assert "eq_symm" in component["catalog_members"]
    assert "isolated_reflexivity" not in component["catalog_members"]
    assert "authored_derivation" in result["lineage_relations"]
    assert "checked_dependency" in result["lineage_relations"]


def test_the_previously_observed_historical_contract_is_not_split_into_holdouts():
    result = build_development_benchmark(_epoch())
    historical = [goal for goal in result["goals"] if goal["cohort"] == "historical"]
    assert len({goal["component_id"] for goal in historical}) == 1
    assert "shared_historical_contract" in result["lineage_relations"]


def test_canonical_alias_and_descendant_are_masked_without_a_name_match():
    source = "forall renamed. (renamed + 1) + 0 = renamed + 1"
    epoch = _epoch(("renamed_target", source, ()), ("later_use", "0 = 0", ("renamed_target",)))
    result = build_development_benchmark(epoch)
    goal = next(goal for goal in result["goals"] if goal["id"] == "dev_universal_equalities_00")
    assert goal["frozen_catalog_aliases"] == ["renamed_target"]
    assert goal["target_alias_descendants"] == ["later_use", "renamed_target"]
    assert set(goal["masked_theorems"]) == {"renamed_target", "later_use"}


def test_oversized_catalog_aliases_fail_closed_without_unbounded_parsing():
    oversized = "(" * 2_100 + "0 = 0" + ")" * 2_100
    epoch = _epoch(("large_unknown", oversized, ()), ("uses_unknown", "1 = 1", ("large_unknown",)))
    result = build_development_benchmark(epoch)
    assert result["catalog_alias_audit"]["unresolved_theorems"] == ["large_unknown"]
    assert result["catalog_alias_audit"]["all_catalog_canonical_aliases_checked"] is False
    assert all({"large_unknown", "uses_unknown"} <= set(goal["masked_theorems"]) for goal in result["goals"])


@pytest.mark.parametrize("field", ("masked_theorems", "component_id", "family", "profile_sha256", "source"))
def test_rehashed_goal_tampering_does_not_authenticate(synthetic_epoch, field):
    record = build_development_benchmark(synthetic_epoch)
    record["goals"][0][field] = [] if field == "masked_theorems" else "tampered"
    record["manifest_sha256"] = _sha({key: value for key, value in record.items() if key != "manifest_sha256"})
    with pytest.raises(HydraBenchmarkError, match="complete predeclared"):
        validate_benchmark(record, synthetic_epoch)


def test_manifest_authentication_precedes_any_preparation_read(synthetic_epoch, tmp_path, monkeypatch):
    record = build_development_benchmark(synthetic_epoch)
    record["families"][0]["catalog_anchors"] = []
    monkeypatch.setattr(evaluation, "_load_preparation", lambda _: pytest.fail("rows read before complete graph authentication"))
    with pytest.raises(HydraBenchmarkError, match="complete predeclared"):
        audit_preparation(record, tmp_path, epoch=synthetic_epoch)


def test_safe_declared_empty_exposure_still_never_claims_semantic_holdout(synthetic_epoch, tmp_path):
    path, _ = _preparation(tmp_path / "prepared", synthetic_epoch)
    result = audit_preparation(build_development_benchmark(synthetic_epoch), path, epoch=synthetic_epoch)
    assert result["blocked_family_count"] == 0
    assert result["safe_under_declared_relations_family_count"] == 8
    assert result["status"] == "safe_under_declared_relations_only"
    assert result["eligible_for_unseen_model_comparison"] is False
    assert result["semantic_equivalence_complete"] is False
    assert result["training_corpus_independently_replayed_in_this_audit"] is False
    assert result["audit_sha256"] == _sha({key: value for key, value in result.items() if key != "audit_sha256"})


def test_one_exposed_catalog_root_blocks_the_whole_connected_family_group(synthetic_epoch, tmp_path):
    path, _ = _preparation(tmp_path / "prepared", synthetic_epoch, (_example(synthetic_epoch, "zero_add"),))
    result = audit_preparation(build_development_benchmark(synthetic_epoch), path, epoch=synthetic_epoch)
    assert result["blocked_family_count"] == 8
    assert result["safe_under_declared_relations_family_count"] == 0
    assert all(family["status"] == "blocked" for family in result["families"])
    assert result["components"][0]["exposure"]["train"]["catalog_roots"] == ["zero_add"]


def test_uncataloged_derivation_is_uncertainty_not_an_independence_claim(synthetic_epoch, tmp_path):
    candidate = _example(synthetic_epoch, "new_candidate", source="forall n. n = n")
    path, _ = _preparation(tmp_path / "prepared", synthetic_epoch, (candidate,))
    result = audit_preparation(build_development_benchmark(synthetic_epoch), path, epoch=synthetic_epoch)
    assert result["unresolved_uncataloged_exposure_roots"] == ["new_candidate"]
    assert result["blocked_family_count"] == 8
    assert "uncataloged_exposure_derivation_preimages_unavailable" in result["families"][0]["reasons"]


def test_exposed_closed_subgoal_is_audited_even_when_root_is_another_component(synthetic_epoch, tmp_path):
    benchmark = build_development_benchmark(synthetic_epoch)
    target = benchmark["goals"][0]["canonical"]
    row = _example(synthetic_epoch, "isolated_reflexivity")
    goals = (f"⊢ {target}",)
    environment = PromptEnvironment(False, CapabilityIdentity(synthetic_epoch.surface_label, ("refl",), ()))
    prompt = render_prompt(goals=goals, focus=0, environment=environment)
    row["prompt"] = row["transition"]["prompt"] = prompt
    row["state_sha256"] = row["transition"]["state_sha256"] = state_sha256(goals)
    row["transition"]["goals_before"] = list(goals)
    row["source_transition_sha256"] = _sha(row["transition"])
    path, _ = _preparation(tmp_path / "prepared", synthetic_epoch, (row,))
    result = audit_preparation(benchmark, path, epoch=synthetic_epoch)
    assert result["blocked_family_count"] == 8
    overlap = result["components"][0]["exposure"]["train"]
    assert overlap["catalog_roots"] == []
    assert overlap["catalog_lineages"] == []
    assert overlap["canonical_closed_goal_aliases"] == [target]


def test_classical_prompt_cannot_masquerade_as_intuitionistic_exposure(synthetic_epoch, tmp_path):
    row = _example(synthetic_epoch, "zero_add")
    goals = tuple(row["transition"]["goals_before"])
    environment = PromptEnvironment(True, CapabilityIdentity(synthetic_epoch.surface_label, ("refl",), ()))
    prompt = render_prompt(goals=goals, focus=0, environment=environment)
    row["prompt"] = row["transition"]["prompt"] = prompt
    row["source_transition_sha256"] = _sha(row["transition"])
    path, _ = _preparation(tmp_path / "prepared", synthetic_epoch, (row,))
    with pytest.raises(HydraBenchmarkError, match="intuitionistic Alpha protocol"):
        audit_preparation(build_development_benchmark(synthetic_epoch), path, epoch=synthetic_epoch)


def test_file_content_tampering_fails_before_overlap_claim(synthetic_epoch, tmp_path):
    path, _ = _preparation(tmp_path / "prepared", synthetic_epoch)
    (path / "train.jsonl").write_bytes(b"{}\n")
    with pytest.raises(HydraBenchmarkError, match="changed from its exact prepared bytes"):
        audit_preparation(build_development_benchmark(synthetic_epoch), path, epoch=synthetic_epoch)


@pytest.mark.parametrize("tamper", (False, True))
def test_preference_payloads_authenticate_their_root_and_closed_goals(synthetic_epoch, tmp_path, tamper):
    row = _example(synthetic_epoch, "zero_add")
    path, manifest = _preparation(tmp_path / "prepared", synthetic_epoch, (row,))
    preference = {
        "schema": "peano-hydra-verified-preference-v1",
        "epoch_sha256": synthetic_epoch.epoch_sha256,
        "theorem_name": row["theorem_name"],
        "theorem": "0 = 0" if tamper else row["transition"]["theorem"],
        "lineage_sha256": row["lineage_sha256"],
        "state_sha256": row["state_sha256"],
        "prompt": row["prompt"],
        "chosen": row["completion"],
        "rejected": row["completion"],
    }
    payload = _bytes(preference) + b"\n"
    (path / "preferences.jsonl").write_bytes(payload)
    manifest["files"]["preferences.jsonl"] = {"bytes": len(payload), "rows": 1, "sha256": hashlib.sha256(payload).hexdigest()}
    (path / "manifest.json").write_bytes(_bytes(manifest))
    benchmark = build_development_benchmark(synthetic_epoch)
    if tamper:
        with pytest.raises(HydraBenchmarkError, match="preference changed its exact catalog root"):
            audit_preparation(benchmark, path, epoch=synthetic_epoch)
    else:
        result = audit_preparation(benchmark, path, epoch=synthetic_epoch)
        assert result["preferences_authenticated_under_training_lineages"] == 1
        assert result["blocked_family_count"] == 8


def test_self_consistent_row_hash_cannot_change_catalog_lineage(synthetic_epoch, tmp_path):
    row = _example(synthetic_epoch, "zero_add")
    path, manifest = _preparation(tmp_path / "prepared", synthetic_epoch, (row,))
    row["lineage_sha256"] = row["transition"]["lineage_sha256"] = "0" * 64
    row["source_transition_sha256"] = _sha(row["transition"])
    _rewrite_train(path, manifest, (row,))
    with pytest.raises(HydraBenchmarkError, match="full frozen theorem-DAG component"):
        audit_preparation(build_development_benchmark(synthetic_epoch), path, epoch=synthetic_epoch)


@pytest.mark.parametrize("source", (
    "99999999999999999999999999999999 = 0",
    "99999999999999999999999999999999bad = 0",
    "９９９９９９９９９９９９９９９９ = 0",
))
def test_unsafe_numeric_payload_is_rejected_before_parser(synthetic_epoch, tmp_path, source):
    row = _example(synthetic_epoch, "zero_add")
    path, manifest = _preparation(tmp_path / "prepared", synthetic_epoch, (row,))
    row["transition"]["theorem"] = source
    _rewrite_train(path, manifest, (row,))
    with pytest.raises(HydraBenchmarkError, match="resource-dangerous"):
        audit_preparation(build_development_benchmark(synthetic_epoch), path, epoch=synthetic_epoch)


@pytest.mark.parametrize("field,value", (("epoch_sha256", "0" * 64), ("model_trained", True), ("sealed_benchmark", True)))
def test_preparation_cannot_change_epoch_or_research_authority(synthetic_epoch, tmp_path, field, value):
    path, manifest = _preparation(tmp_path / "prepared", synthetic_epoch)
    manifest[field] = value
    (path / "manifest.json").write_bytes(_bytes(manifest))
    with pytest.raises(HydraBenchmarkError, match="preparation changed"):
        audit_preparation(build_development_benchmark(synthetic_epoch), path, epoch=synthetic_epoch)


def test_symlinked_data_is_not_authenticated(synthetic_epoch, tmp_path):
    path, _ = _preparation(tmp_path / "prepared", synthetic_epoch)
    (path / "train.jsonl").unlink()
    (path / "train.jsonl").symlink_to(path / "dev.jsonl")
    with pytest.raises(HydraBenchmarkError, match="regular non-symlink"):
        audit_preparation(build_development_benchmark(synthetic_epoch), path, epoch=synthetic_epoch)


def test_current_alpha_component_and_alias_limits_remain_honest():
    epoch = freeze_epoch(ROOT)
    result = build_development_benchmark(epoch)
    assert result["goal_count"] == 68
    assert result["declared_connected_component_count"] == 1
    assert len(result["components"][0]["catalog_members"]) >= 2_000
    assert result["catalog_alias_audit"]["checked_theorems"] > 0
    assert result["catalog_alias_audit"]["unresolved_theorem_count"] > 0
    assert result["semantic_equivalence_complete"] is False
    assert "torch" not in sys.modules


def test_dangling_or_duplicate_catalog_members_fail_before_relations(synthetic_epoch):
    invalid = replace(synthetic_epoch, theorems=(*synthetic_epoch.theorems, synthetic_epoch.theorems[0]))
    with pytest.raises(HydraBenchmarkError, match="duplicate or dangling"):
        build_development_benchmark(invalid)
