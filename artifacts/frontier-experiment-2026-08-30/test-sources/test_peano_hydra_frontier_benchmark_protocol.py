"""Protocol tests with explicitly synthetic reviews/process/reference receipts.

The64 small candidate proofs are real native QEDs, but their one-theorem epoch,
worker receipt metadata, historical inventory, human assertions, and Lean/cold
evidence are TEST FIXTURES ONLY. No actual human review, Lean execution, cold
pass, readiness, approval, or model work is performed. Fixtures live only in
pytest temporary directories; no production review is generated.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, FrozenInstanceError, replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra import frontier_benchmark_candidates as candidate
from training.peano_hydra import frontier_benchmark_audit as audit_api
from training.peano_hydra import frontier_benchmark_protocol as protocol
from training.peano_hydra.epoch import EpochTheorem
from training.peano_hydra.review_runtime import ProcessLimits, RESOURCE_MEASUREMENT
from test_peano_hydra_frontier_benchmark_candidates import _epoch


def _write(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = protocol._canonical(value) + b"\n" if not isinstance(value, bytes) else value
    path.write_bytes(raw)
    return {"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _read(root, relative):
    return json.loads((root / relative).read_bytes())


def _signed(value, field):
    value[field] = protocol._digest({key: entry for key, entry in value.items() if key != field})
    return value


def _native_receipt(root, manifest, bundle_descriptor, mode):
    # Structural test receipt only. A real receipt is produced by run_bounded,
    # and no claim of real process execution is made by this fixture.
    request = {"mode": mode, "output": str(root / mode),
               "bundle": None if mode == "build" else str(root / "build/bundle.json")}
    result = {"schema": "peano-hydra-frontier-benchmark-candidate-worker-v1", "status": "verified", "mode": mode,
              "manifest_sha256": manifest["manifest_sha256"], "bundle_sha256": manifest["bundle_sha256"],
              "verified_route_count": 64, "verified_decisions": 640, "primary_goal_count": 32, "reserved_goal_count": 32,
              "prior_bundle": None if mode == "build" else {"path": request["bundle"],
                   "bytes": bundle_descriptor["bytes"], "sha256": bundle_descriptor["sha256"]},
              "forbidden_model_modules": [], "claims": manifest["claims"]}
    stdout = protocol._canonical(result) + b"\n"
    stdin = protocol._canonical(request) + b"\n"
    process = {"command": [sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null",
                           str(ROOT / "scripts/build_peano_hydra_benchmark_candidates.py"), "--worker"],
               "limits": ProcessLimits(wall_seconds=150, cpu_seconds=120, rss_bytes=1024**3, output_bytes=128 * 1024).to_dict(),
               "stdin_bytes": len(stdin), "stdin_sha256": hashlib.sha256(stdin).hexdigest(),
               "returncode": 0, "reason": "exited", "stdout": stdout.decode(), "stderr": "",
               "output_encoding": "utf-8", "raw_output_base64": None, "output_truncated": False,
               "stdout_bytes": len(stdout), "stderr_bytes": 0, "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
               "stderr_sha256": hashlib.sha256(b"").hexdigest(),
               "resources": {"wall_seconds": 0.02, "cpu_seconds": 0.01, "peak_rss_bytes": 1024**2,
                             "sampled_peak_group_rss_bytes": 1024**2, "cpu_instructions": None, "energy_joules": None},
               "observed_descendant_count": 0, "resource_measurement": RESOURCE_MEASUREMENT}
    source_names = ("training/peano_hydra/frontier_benchmark_candidates.py", "scripts/build_peano_hydra_benchmark_candidates.py",
                    "training/peano_hydra/review_runtime.py", "scripts/hydra_bounded_exec.py")
    sources = {name: manifest["source_identity"]["files"][name] for name in source_names}
    wrapper = {"schema": "peano-hydra-frontier-benchmark-candidate-process-v1", "status": "verified", "process": process,
               "request": request, "source_files_before": sources, "source_files_after": sources, "source_files_unchanged": True}
    descriptor = _write(root, mode + "/process.json", wrapper)
    result_descriptor = _write(root, mode + "/verification.json", result)
    return descriptor, result_descriptor


def _readiness_fixture(root, epoch):
    # These asserted facts and raw bytes deliberately describe no real Lean
    # run. This tests static schema joins and the explicit non-attestation claim.
    record = {"schema": protocol.READINESS_SCHEMA, "status": "human-reviewed-reference-ready",
        "reviewed_by_human": True, "reviewer_reference": "SYNTHETIC TEST ONLY - NOT A HUMAN REVIEW",
        "reviewed_at": "2026-08-30T00:00:00+00:00", "epoch_sha256": epoch["epoch_sha256"],
        "edition_identity_sha256": epoch["edition_identity_sha256"], "theorem_dag_sha256": epoch["theorem_dag"]["sha256"],
        "reviewed_definition_dag_sha256": epoch["definition_dag"]["sha256"],
        "frozen_profile": {"profile_sha256": "1" * 64, "source_files_sha256": "2" * 64,
                           "claim": "sound-theorem-prover-no-decision-claim", "reviewed": True},
        "lean": {"version": "4.31.0", "toolchain_pin": "leanprover/lean4:v4.31.0",
                 "compiler_sha256": "3" * 64, "reference_source_sha256": "4" * 64},
        "semantic_checks": {"status": "passed", "semantic_formula_count": 1000, "theorem_count": 1000,
            "decision_claim": False, "all_in_scope_results_agree": True, "false_acceptance_count": 0,
            "unresolved_semantics_count": 0, "mutation_categories": ["proof_constructors", "binders", "substitutions",
                "translations", "induction_instances", "negative_witnesses"], "required_mutations_rejected": True,
            "kernel_import_boundary_passed": True, "original_goal_tests_passed": True, "transactional_history_tests_passed": True},
        "cold_library": {"scope": "full", "epoch_target_count": 1, "target_inventory_sha256": "5" * 64,
            "fresh_workers": True, "passes": [{"pass_number": number, "checked_count": 1,
                "failed_count": 0, "unknown_count": 0, "root_sha256": "6" * 64} for number in (1, 2)]},
        "independent_verification": {"status": "passed", "fresh_reference_recheck": True, "both_full_cold_passes_rechecked": True},
        "resource_review": {"reviewed": True, "resource_envelope_sha256": "7" * 64},
        "assertion_scope": protocol._ASSERTION_SCOPE,
        "claims": {"human_identity_attested": False, "execution_attested_by_this_loader": False,
            "h0_complete": False, "h1_complete": False, "sealed_benchmark": False,
            "training_authorized": False, "compute_authorized": False}}
    cold = record["cold_library"]
    sections = [("frozen_profile", record["frozen_profile"]), ("lean_environment", record["lean"]),
                ("semantic_checks", record["semantic_checks"]), ("cold_pass_1", cold["passes"][0]),
                ("cold_pass_2", cold["passes"][1]), ("independent_verification", record["independent_verification"]),
                ("resource_review", record["resource_review"])]
    for role, section in sections:
        facts = deepcopy(section)
        if role.startswith("cold_pass_"):
            facts.update({key: cold[key] for key in ("scope", "epoch_target_count", "target_inventory_sha256", "fresh_workers")})
        raw = _write(root, "synthetic-reference/raw-" + role + ".txt", ("SYNTHETIC TEST DATA; NO EXECUTION: " + role).encode())
        envelope = {"schema": protocol.EVIDENCE_SCHEMA, "role": role, "epoch_sha256": epoch["epoch_sha256"],
                    "asserted_facts": facts, "raw_artifacts": [raw], "assertion_scope": protocol._ASSERTION_SCOPE}
        section["evidence"] = _write(root, "synthetic-reference/" + role + ".json", _signed(envelope, "evidence_sha256"))
    return _write(root, "reference-readiness.json", _signed(record, "readiness_sha256"))


@pytest.fixture(scope="module")
def archive(tmp_path_factory):
    root = tmp_path_factory.mktemp("synthetic-benchmark-protocol").resolve()
    theorem = EpochTheorem("synthetic_epoch_only", "0 = 0", hashlib.sha256(b"0 = 0").hexdigest(),
                           ("refl",), "9" * 64, (), "stable", 0)
    epoch = replace(_epoch(), theorems=(theorem,), stable_count=1)
    bundle = candidate.build_candidate_bundle(epoch)
    b = _write(root, "build/bundle.json", bundle)
    p = _write(root, "build/plan.json", bundle["plan"])
    artifacts = {"bundle.json": {key: b[key] for key in ("bytes", "sha256")},
                 "plan.json": {key: p[key] for key in ("bytes", "sha256")}}
    manifest = candidate.build_candidate_manifest(bundle, artifacts=artifacts)
    m = _write(root, "build/manifest.json", manifest)
    build, _ = _native_receipt(root, manifest, b, "build")
    verify, verification = _native_receipt(root, manifest, b, "verify")
    old = _write(root, "old-history.json", {"statement": "0 = 0"})
    exposure = audit_api.build_exposure_index([{"path": str(root / "old-history.json"), "format": "json",
        "role": "synthetic-exposure-fixture", "anchor_origin": "SYNTHETIC TEST ONLY", "sha256": old["sha256"]}],
        coverage_gaps=["Synthetic fixture only; no production history assertion."])
    (root / "old-history.json").unlink()
    identity = {"manifest": m, "plan": p, "bundle": b, "native_build_process": build,
                "native_verify_process": verify, "native_verify_result": verification,
                "manifest_sha256": manifest["manifest_sha256"], "plan_sha256": manifest["plan_sha256"],
                "bundle_sha256": manifest["bundle_sha256"], "source_identity_sha256": manifest["source_identity"]["source_files_sha256"],
                "primary_goals_sha256": protocol._digest(manifest["primary_goals"]),
                "reserved_goals_sha256": protocol._digest(manifest["reserved_goals"])}
    traces = [{**row, "theorem_name": proof["name"]} for proof in bundle["proofs"] for row in proof["native_result"]["trace"][:-1]]
    counts = {proof["name"]: proof["native_result"]["tactics_applied"] for proof in bundle["proofs"]}
    audit = audit_api.audit_candidates(exposure, bundle["plan"]["routes"], candidate_identity=identity,
        reference_records=traces, reference_expected_counts=counts)
    a = _write(root, "audit.json", audit)
    requirements = protocol.benchmark_review_requirements(root / m["path"], m["sha256"], root / a["path"], a["sha256"])
    review = {"schema": protocol.REVIEW_SCHEMA, "decision": "accept",
        "reviewer_reference": "SYNTHETIC TEST ONLY - NOT A HUMAN REVIEW", "reviewed_at": "2026-08-30T00:00:00+00:00",
        "human_assertion": {"provided_by_human": True, "identity_attested": False,
            "cryptographic_signature_verified": False, "assertion_scope": protocol._ASSERTION_SCOPE},
        "candidate_binding": requirements["candidate_binding"], "whole_template_exclusions": requirements["whole_template_exclusions"],
        "acknowledgements": requirements["required_acknowledgements"],
        "reference_readiness": _readiness_fixture(root, manifest["epoch"])}
    _write(root, "review.json", _signed(review, "review_sha256"))
    return root


def _reference(root):
    def pin(relative):
        return hashlib.sha256((root / relative).read_bytes()).hexdigest()
    return protocol.BenchmarkReference(root / "build/manifest.json", pin("build/manifest.json"),
        root / "audit.json", pin("audit.json"), root / "review.json", pin("review.json"))


def _copy(archive, tmp_path):
    root = tmp_path.resolve() / "relocated"
    shutil.copytree(archive, root)
    return root


def _replace_readiness(root, mutate):
    record = _read(root, "reference-readiness.json")
    mutate(record)
    descriptor = _write(root, "reference-readiness.json", _signed(record, "readiness_sha256"))
    review = _read(root, "review.json")
    review["reference_readiness"] = descriptor
    _write(root, "review.json", _signed(review, "review_sha256"))


def test_six_fields_portable_projection_and_explicit_non_attestation(archive):
    reference = _reference(archive)
    assert [field.name for field in fields(reference)] == ["manifest_path", "manifest_sha256", "audit_path", "audit_sha256", "review_path", "review_sha256"]
    with pytest.raises(FrozenInstanceError):
        reference.manifest_sha256 = "0" * 64
    result = reference.load()
    assert len(result["primary_goals"]) == len(result["reserved_goals"]) == 32
    assert result["heldout_goals_sha256"] == protocol._digest(result["primary_goals"])
    assert all(set(row) == {"name", "source", "statement", "statement_sha256", "lineage_sha256"} for row in result["primary_goals"])
    routes = {row["name"]: row for row in _read(archive, "build/plan.json")["routes"]}
    assert all(row["source"] == routes[row["name"]]["source"] for row in result["primary_goals"])
    assert result["audited_file_sha256"] == sorted(set(result["audited_file_sha256"]))
    assert result["claim_boundary"]["native_or_lean_execution_repeated_by_loader"] is False
    assert "not attested" in result["claim_boundary"]["human_and_reference_review"]
    assert not any("path" in key for key in reference.to_dict())
    assert reference.protected_paths() == (archive / "build", archive)


def test_all32_projected_formula_inputs_replay_in_the_actual_evaluator_worker(archive):
    # Exercise the real evaluator boundary, not a mock row or a textual label
    # check. The prior provenance-label projection fails native parsing here.
    from training.peano_hydra.capacity import replay_worker
    bundle = _read(archive, "build/bundle.json")
    routes = {row["name"]: row for row in bundle["plan"]["routes"]}
    checked = _reference(archive).load()
    for goal in checked["primary_goals"]:
        route = routes[goal["name"]]
        result = replay_worker({"source": goal["source"], "statement": goal["statement"],
            "commands": route["commands"], "id": goal["name"] + "-projected",
            "session": goal["name"] + "-projected", "capabilities": bundle["plan"]["authority"]["capabilities"]})
        assert result["status"] == "proved" and result["kernel_checked"] is True
        assert result["theorem"] == goal["statement"] and result["goals"] == []
        assert result["classical"] is False and result["failed_tactics"] == 0
        assert result["tactics_applied"] == len(route["commands"])


def test_relocation_never_requires_original_historical_paths(archive, tmp_path):
    root = _copy(archive, tmp_path)
    audit = _read(root, "audit.json")
    assert all(not Path(row["path"]).exists() for row in audit["source_inventory"])
    assert _reference(root).load() == _reference(archive).load()
    assert _reference(root).to_dict() == _reference(archive).to_dict()


@pytest.mark.parametrize("field", ["manifest_sha256", "audit_sha256", "review_sha256"])
def test_raw_external_pins_cannot_be_replaced_by_canonical_self_hashes(archive, field):
    reference = replace(_reference(archive), **{field: "0" * 64})
    with pytest.raises(protocol.BenchmarkProtocolError, match="externally pinned"):
        reference.load()


def test_requirements_prepare_no_review_or_reference_readiness(archive):
    ref = _reference(archive)
    result = protocol.benchmark_review_requirements(ref.manifest_path, ref.manifest_sha256, ref.audit_path, ref.audit_sha256)
    assert result["status"] == "pending_external_human_review_and_reference_readiness"
    assert len(result["whole_template_exclusions"]) == 64
    assert not {"decision", "reviewer_reference", "reviewed_at", "review_sha256"} & set(result)
    assert result["required_reference_readiness"]["evidence_not_present_in_native_candidate_bundle"] is True


def test_missing_human_review_fails_without_manufacturing_one(archive, tmp_path):
    root = _copy(archive, tmp_path)
    reference = _reference(root)
    (root / "review.json").unlink()
    with pytest.raises(protocol.BenchmarkProtocolError, match="human benchmark review is required"):
        reference.load()
    assert not (root / "review.json").exists()


def test_missing_reference_readiness_is_mandatory_even_after_synthetic_human_acceptance(archive, tmp_path):
    root = _copy(archive, tmp_path)
    review = _read(root, "review.json")
    review["reference_readiness"] = None
    _write(root, "review.json", _signed(review, "review_sha256"))
    with pytest.raises(protocol.BenchmarkProtocolError, match="pending reference readiness"):
        _reference(root).load()


@pytest.mark.parametrize("mutation", ["lean428", "wrong_epoch", "cold_sample", "missing_pass", "cold_unknown", "different_roots",
                                     "insufficient_semantics", "missing_mutations", "h0_claim", "human_identity_claim", "no_resource_review"])
def test_reference_assertions_cannot_substitute_compatibility_or_incomplete_evidence(archive, tmp_path, mutation):
    root = _copy(archive, tmp_path)
    def mutate(record):
        if mutation == "lean428": record["lean"]["version"] = "4.28.0"
        elif mutation == "wrong_epoch": record["epoch_sha256"] = "0" * 64
        elif mutation == "cold_sample": record["cold_library"]["scope"] = "sample"
        elif mutation == "missing_pass": record["cold_library"]["passes"].pop()
        elif mutation == "cold_unknown": record["cold_library"]["passes"][0]["unknown_count"] = 1
        elif mutation == "different_roots": record["cold_library"]["passes"][1]["root_sha256"] = "0" * 64
        elif mutation == "insufficient_semantics": record["semantic_checks"]["semantic_formula_count"] = 999
        elif mutation == "missing_mutations": record["semantic_checks"]["mutation_categories"].pop()
        elif mutation == "h0_claim": record["claims"]["h0_complete"] = True
        elif mutation == "human_identity_claim": record["claims"]["human_identity_attested"] = True
        elif mutation == "no_resource_review": record["resource_review"]["reviewed"] = False
    _replace_readiness(root, mutate)
    with pytest.raises(protocol.BenchmarkProtocolError):
        _reference(root).load()


def test_readiness_requires_exact_underlying_external_bytes(archive, tmp_path):
    root = _copy(archive, tmp_path)
    (root / "synthetic-reference/raw-cold_pass_1.txt").write_bytes(b"tampered synthetic raw output")
    with pytest.raises(protocol.BenchmarkProtocolError, match="externally pinned|bounded"):
        _reference(root).load()


@pytest.mark.parametrize("kind", ["leaf_symlink", "ancestor_symlink", "hardlink"])
def test_no_follow_and_single_link_protection(archive, tmp_path, kind):
    root = _copy(archive, tmp_path)
    reference = _reference(root)
    if kind == "leaf_symlink":
        (root / "review.json").rename(root / "real-review.json")
        (root / "review.json").symlink_to(root / "real-review.json")
    elif kind == "ancestor_symlink":
        root.rename(tmp_path / "actual")
        root.symlink_to(tmp_path / "actual", target_is_directory=True)
    else:
        os.link(root / "review.json", root / "alias-review.json")
    with pytest.raises(protocol.BenchmarkProtocolError):
        reference.load()


@pytest.mark.parametrize("mutation", ["drop_reserved_exclusion", "training_permission", "decision_reject", "identity_attestation"])
def test_rehashed_review_cannot_change_scope_or_approve_other_work(archive, tmp_path, mutation):
    root = _copy(archive, tmp_path)
    review = _read(root, "review.json")
    if mutation == "drop_reserved_exclusion": review["whole_template_exclusions"].pop()
    elif mutation == "training_permission": review["acknowledgements"]["no_training_authorization"] = False
    elif mutation == "decision_reject": review["decision"] = "reject"
    else: review["human_assertion"]["identity_attested"] = True
    _write(root, "review.json", _signed(review, "review_sha256"))
    with pytest.raises(protocol.BenchmarkProtocolError):
        _reference(root).load()


@pytest.mark.parametrize("mutation", ["exact", "template", "incomplete_coverage"])
def test_audit_cannot_admit_exposure_or_incomplete_native_trace(archive, tmp_path, mutation):
    root = _copy(archive, tmp_path)
    audit = _read(root, "audit.json")
    family = audit["families"][0]
    if mutation == "incomplete_coverage":
        family["complete_reference_state_traces"] = False
        audit["reference_state_coverage_complete"] = False
        audit["blocking_coverage_gaps"] = ["candidate_complete_reference_state_inventory_missing"]
    else:
        key = "roots" if mutation == "exact" else "logical_skeleton_review_flag"
        family["goals"][0]["matches"][key] = {"occurrences": 1, "examples": ["synthetic-history:0"]}
        family["status"] = "quarantine-exact-exposure" if mutation == "exact" else "quarantine-template-review"
        family["whole_family_quarantined"] = True
    _write(root, "audit.json", _signed(audit, "audit_sha256"))
    with pytest.raises(protocol.BenchmarkProtocolError, match="audit blocked"):
        _reference(root).load()
