"""Actual tiny constructive teachers; explicitly synthetic epoch metadata."""

from __future__ import annotations

import builtins
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra import composition as native
from training.peano_hydra import frontier_benchmark_candidates as candidates
from training.peano_hydra.epoch import HydraEpoch


def _epoch():
    return HydraEpoch(version="v25", edition_identity_sha256="1" * 64,
        alpha_catalog_sha256="2" * 64, stable_catalog_sha256="3" * 64,
        definition_artifact_sha256="4" * 64, campaign_artifact_sha256="5" * 64,
        theorem_dag_sha256="6" * 64, reviewed_definition_dag_sha256="7" * 64,
        milestone_dag_sha256="8" * 64, theorems=(), definitions=(), stable_count=0,
        theorem_edge_count=0, definition_edge_count=0, milestone_count=0,
        milestone_edge_count=0, blueprint_definition_count=0,
        blueprint_definition_edge_count=0, notation_edge_count=0)


@pytest.fixture(scope="module")
def bundle():
    # Only the epoch catalog metadata are synthetic; all64 original-goal
    # native constructive kernel QEDs and complete traces are real.
    return candidates.build_candidate_bundle(_epoch())


@pytest.fixture(scope="module")
def manifest(bundle):
    artifacts = {}
    for name, record in (("bundle.json", bundle), ("plan.json", bundle["plan"])):
        raw = candidates._canonical(record) + b"\n"
        artifacts[name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    return candidates.build_candidate_manifest(bundle, artifacts=artifacts)


def _rehash(record, field):
    record[field] = candidates._digest({key: value for key, value in record.items() if key != field})
    return record


def test_metadata_import_and_validation_never_import_native_or_model_code(manifest, monkeypatch):
    name = "_candidate_metadata_only"
    module = types.ModuleType(name)
    path = ROOT / "training/peano_hydra/frontier_benchmark_candidates.py"
    module.__file__ = str(path)
    monkeypatch.setitem(sys.modules, name, module)
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        assert not name.startswith(("training", "peano_lab", "torch", "transformers", "peft", "tokenizers"))
        return original(name, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(builtins, "__import__", guarded)
        exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
        assert module.validate_manifest(manifest) is None


def test_plan_is_declared_without_proofs_and_reserves_whole_templates(bundle, monkeypatch):
    monkeypatch.setattr(native, "run_proof", lambda *a, **k: pytest.fail("planning replayed native proofs"))
    plan = candidates.candidate_plan(_epoch())
    assert plan == bundle["plan"]
    assert plan["route_count"] == 64 and plan["family_count"] == 8
    assert {row["id"] for row in plan["families"]} == {row[0] for row in candidates._FAMILIES}
    assert all(row["all_variants_excluded_from_training"] for row in plan["families"])
    assert all(row["semantic_independence_claim"] is False for row in plan["families"])
    assert all(row["known_correlated_primitive_motifs"] for row in plan["families"])
    assert all(row["use"] == "evaluation_candidate_only" for row in plan["routes"])
    assert not {"train", "dev", "sft", "preferences", "curriculum"} & set(bundle)


def test_cohort_does_not_expose_teacher_commands_or_make_reserved_test_claim(bundle):
    primary = candidates.evaluation_goals(bundle["plan"])
    reserved = candidates.evaluation_goals(bundle["plan"], cohort=candidates.RESERVED_COHORT)
    assert len(primary) == len(reserved) == 32
    assert {row["name"] for row in primary}.isdisjoint(row["name"] for row in reserved)
    assert all(row["generator_seed"] < 4 for row in primary)
    assert all(row["generator_seed"] >= 4 for row in reserved)
    assert all(not {"commands", "completion", "prompt", "action"} & set(row) for row in primary + reserved)
    assert bundle["claims"]["reserved_variants_are_independent_test"] is False


def test_all_declared_teachers_have_native_qed_and_complete_intermediate_hashes(bundle):
    assert bundle["verified_route_count"] == 64
    assert bundle["verified_decisions"] == 640
    for route, proof in zip(bundle["plan"]["routes"], bundle["proofs"]):
        result = proof["native_result"]
        assert result["kernel_checked"] is True and result["status"] == "proved"
        assert result["theorem"] == route["statement"] and result["goals"] == []
        assert result["classical"] is False and result["failed_tactics"] == 0
        assert 7 <= result["tactics_applied"] == len(route["commands"]) <= 13
        assert len(proof["intermediates"]) == len(route["commands"])
        assert proof["trace_sha256"] == candidates._digest(result["trace"])
        assert proof["intermediates_sha256"] == candidates._digest(proof["intermediates"])
        assert result["trace"][-1]["qed"] is True
        assert proof["intermediates"][-1]["after"] == []
        for step, row in enumerate(proof["intermediates"], 1):
            assert row["step"] == step
            assert row["action"] == route["commands"][step - 1]
            assert row["intermediate_sha256"] == candidates._digest({k: v for k, v in row.items() if k != "intermediate_sha256"})
            assert [goal["display"] for goal in row["before"]] == result["trace"][step - 1]["goals_before"]
            for goal in row["before"] + row["after"]:
                assert goal["display_sha256"] == hashlib.sha256(goal["display"].encode()).hexdigest()
                assert goal["target_canonical_sha256"] == hashlib.sha256(goal["target_canonical"].encode()).hexdigest()


@pytest.mark.parametrize("field", ["sealed_benchmark", "eligible_for_unseen_model_comparison", "independent_human_review",
                                  "external_owner_attested", "historical_training_exclusion_audit_complete"])
def test_rehashed_manifest_cannot_self_authorize_review_or_unseen_claim(manifest, field):
    record = deepcopy(manifest)
    record["claims"][field] = True
    _rehash(record, "manifest_sha256")
    with pytest.raises(candidates.CandidateError, match="claims"):
        candidates.validate_manifest(record)


@pytest.mark.parametrize("mutation", ["missing_goal", "duplicated_seed", "wrong_cohort", "missing_proof", "wrong_decision_count",
                                     "wrong_template", "changed_statement_hash", "unsafe_artifact", "changed_source"])
def test_rehashed_incomplete_or_misaligned_manifest_rejected(manifest, mutation):
    record = deepcopy(manifest)
    if mutation == "missing_goal":
        record["primary_goals"].pop()
    elif mutation == "duplicated_seed":
        record["primary_goals"][1] = deepcopy(record["primary_goals"][0])
    elif mutation == "wrong_cohort":
        record["primary_goals"][0]["cohort"] = candidates.RESERVED_COHORT
    elif mutation == "missing_proof":
        record["proof_references"].pop()
    elif mutation == "wrong_decision_count":
        record["verified_decisions"] -= 1
    elif mutation == "wrong_template":
        record["primary_goals"][0]["template_sha256"] = "0" * 64
    elif mutation == "changed_statement_hash":
        record["primary_goals"][0]["statement"] = "0 = 0"
    elif mutation == "unsafe_artifact":
        record["artifacts"]["../training/sft.jsonl"] = {"bytes": 1, "sha256": "0" * 64}
    elif mutation == "changed_source":
        key = next(iter(record["source_identity"]["files"]))
        record["source_identity"]["files"][key] = "0" * 64
    _rehash(record, "manifest_sha256")
    with pytest.raises(candidates.CandidateError):
        candidates.validate_manifest(record)


def test_route_mutation_rejected_before_native_execution(bundle, monkeypatch):
    route = deepcopy(bundle["plan"]["routes"][0])
    route["commands"][-1] = "refl"
    monkeypatch.setattr(native, "run_proof", lambda *a, **k: pytest.fail("altered route reached native engine"))
    with pytest.raises(candidates.CandidateError, match="declaration"):
        candidates.verify_candidate_route(_epoch(), route)


def test_real_native_failure_retained_with_exact_unproved_result(bundle, monkeypatch):
    original = native.run_proof
    def fail_first_command(source, commands, **kwargs):
        return original(source, ("refl",), **kwargs)
    monkeypatch.setattr(native, "run_proof", fail_first_command)
    route = bundle["plan"]["routes"][0]
    with pytest.raises(candidates.CandidateNativeFailure) as failure:
        candidates.verify_candidate_route(_epoch(), route)
    evidence = failure.value.evidence
    assert evidence["route"] == route and evidence["status"] == "native_proof_failed"
    assert evidence["native_result"]["status"] == "tactic_error"
    assert evidence["native_result"]["kernel_checked"] is False
    assert evidence["native_result"]["trace"][0]["tactic"] == "refl"
    assert evidence["native_result"]["goals"]


def test_manifest_builder_refuses_changed_native_original_goal(bundle, manifest):
    changed = deepcopy(bundle)
    proof = changed["proofs"][0]
    proof["native_result"]["theorem"] = "0 = 0"
    _rehash(proof, "proof_sha256")
    changed["proofs_sha256"] = candidates._digest(changed["proofs"])
    _rehash(changed, "bundle_sha256")
    with pytest.raises(candidates.CandidateError, match="proof metadata"):
        candidates.build_candidate_manifest(changed, artifacts=manifest["artifacts"])
