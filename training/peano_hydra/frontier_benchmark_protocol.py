"""Portable, externally pinned benchmark-review inputs; never an approval.

This reader authenticates supplied bytes and checks their recorded joins. It
does not run native proofs, Lean, cold passes, training, or a model; nor can it
verify a human identity or manufacture a human decision. Historical exposure
paths are provenance inside a frozen review-time receipt, not files which a
remote evaluator must find on the original Mac.

An accepted new-template comparison requires a separately supplied human
benchmark review AND a human-reviewed reference-readiness descriptor. The
existing native64 candidate evidence does not meet Lean4.31, semantic-reference,
or two-full-cold-pass readiness. H0/H1 completion and final-test ownership are
not inferred by this metadata protocol.
"""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from training.peano_hydra import frontier_benchmark_candidates as candidate
from training.peano_hydra import origin_bridge as bridge


REFERENCE_SCHEMA = "peano-hydra-frontier-benchmark-reference-v1"
REVIEW_SCHEMA = "peano-hydra-frontier-benchmark-human-review-v1"
READINESS_SCHEMA = "peano-hydra-frontier-reference-readiness-assertion-v1"
EVIDENCE_SCHEMA = "peano-hydra-frontier-external-reference-evidence-v1"
REQUIREMENTS_SCHEMA = "peano-hydra-frontier-benchmark-review-requirements-v1"
MAX_MANIFEST_BYTES = 512 * 1024
MAX_AUDIT_BYTES = 16 * 1024**2
MAX_REVIEW_BYTES = 512 * 1024
MAX_EVIDENCE_BYTES = 16 * 1024**2
MAX_TOTAL_BYTES = 96 * 1024**2
MAX_FILES = 256
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_NATIVE_DESCRIPTOR_NAMES = ("manifest", "plan", "bundle", "native_build_process",
                            "native_verify_process", "native_verify_result")
_IDENTITY_HASHES = ("manifest_sha256", "plan_sha256", "bundle_sha256", "source_identity_sha256",
                    "primary_goals_sha256", "reserved_goals_sha256")
_ASSERTION_SCOPE = "externally supplied human assertion; exact evidence bytes checked, human identity and execution not attested"


class BenchmarkProtocolError(ValueError):
    """Missing review/readiness or changed evidence cannot admit a comparison."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkProtocolError(message)


def _keys(record: object, fields: set[str], label: str) -> None:
    _require(type(record) is dict and set(record) == fields, f"{label} fields changed")


def _sha(value: object, label: str) -> str:
    _require(type(value) is str and _SHA.fullmatch(value) is not None, f"{label} requires one raw lowercase SHA-256 pin")
    return value


def _canonical(record: object) -> bytes:
    return candidate._canonical(record)


def _digest(record: object) -> str:
    return hashlib.sha256(_canonical(record)).hexdigest()


def _signed(record: dict, field: str, label: str) -> None:
    _require(record.get(field) == _digest({key: value for key, value in record.items() if key != field}),
             f"{label} canonical digest changed")


def _text(value: object, label: str) -> None:
    _require(type(value) is str and 0 < len(value.encode()) <= 1024 and value.strip() == value
             and not any(ord(c) < 32 or ord(c) == 127 for c in value), f"{label} must be bounded nonempty text")


def _human_header(reference: object, date: object) -> None:
    _text(reference, "human reviewer reference")
    _require(type(date) is str and len(date) <= 64, "human review timestamp required")
    try:
        parsed = datetime.fromisoformat(date)
    except ValueError as error:
        raise BenchmarkProtocolError("human review timestamp malformed") from error
    _require(parsed.tzinfo is not None, "human review timestamp needs an explicit timezone")


def _descriptor(record: object, label: str) -> dict:
    _keys(record, {"path", "bytes", "sha256"}, label)
    bridge._relative(record["path"])
    _sha(record["sha256"], label)
    _require(type(record["bytes"]) is int and 0 < record["bytes"] <= MAX_EVIDENCE_BYTES,
             f"{label} exceeds its external file bound")
    return record


class _Inputs:
    """Hold existing no-follow directory/file identities through the whole join."""

    def __init__(self):
        self.stack = ExitStack()
        self.trees = {}
        self.files = {}

    def __enter__(self):
        return self

    def __exit__(self, *error):
        self.stack.close()

    def read(self, path: Path, *, expected: str | None = None, maximum: int = MAX_EVIDENCE_BYTES,
             retain: bool = True) -> tuple[dict, bytes | None]:
        path = bridge._absolute(path)
        if path.parent not in self.trees:
            _require(len(self.trees) < 32, "benchmark evidence directory inventory exceeds bound")
            self.trees[path.parent] = self.stack.enter_context(bridge._Tree(path.parent))
        observed, raw = self.trees[path.parent].fingerprint(path.name, maximum=maximum, retain=retain)
        entry = {key: observed[key] for key in ("bytes", "sha256")}
        if expected is not None:
            _sha(expected, "external evidence file")
            _require(entry["sha256"] == expected, f"externally pinned benchmark evidence changed: {path.name}")
        if path in self.files:
            _require(self.files[path] == entry, "benchmark evidence changed between joined reads")
        self.files[path] = entry
        _require(len(self.files) <= MAX_FILES and sum(item["bytes"] for item in self.files.values()) <= MAX_TOTAL_BYTES,
                 "aggregate benchmark evidence exceeds its file/byte reservation")
        return entry, raw

    def json(self, path: Path, *, expected: str | None = None, maximum: int = MAX_EVIDENCE_BYTES):
        entry, raw = self.read(path, expected=expected, maximum=maximum)
        value = bridge._decode(raw, maximum, "externally pinned benchmark evidence")
        return value, entry

    def described(self, parent: Path, descriptor: dict, *, label: str, retain: bool = True):
        item = _descriptor(descriptor, label)
        path = parent / item["path"]
        observed, raw = self.read(path, expected=item["sha256"], maximum=min(MAX_EVIDENCE_BYTES, item["bytes"]), retain=retain)
        _require(observed["bytes"] == item["bytes"], f"{label} byte count changed")
        return raw

    def assert_unchanged(self):
        for tree in self.trees.values():
            tree.assert_unchanged()


def _projection(goals: list[dict], routes: list[dict], proofs: list[dict]) -> list[dict]:
    """Pass the exact proved input formula to the evaluator's ``source`` field.

    ``source`` is executed by the native prover, not displayed as a provenance
    label. Family provenance remains in the candidate manifest. Parse the
    source again to join it to the original canonical theorem without running
    a proof or manufacturing a replacement formula.
    """
    from training.peano_hydra.protocol import validate_statement
    by_route = {row["name"]: row for row in routes}
    by_proof = {row["name"]: row for row in proofs}
    _require(len(by_route) == len(routes) == len(by_proof) == len(proofs) == 64
             and set(by_route) == set(by_proof), "candidate projection needs all64 distinct native source/proof identities")
    projected = []
    for row in goals:
        _require(row["name"] in by_route, "candidate projected goal has no original native source")
        route, proof = by_route[row["name"]], by_proof[row["name"]]
        source = route["source"]
        _require(type(source) is str and 1 <= len(source.encode()) <= 4096
                 and hashlib.sha256(source.encode()).hexdigest() == route["source_sha256"] == proof["source_sha256"]
                 and route["route_sha256"] == row["route_sha256"] == proof["route_sha256"]
                 and route["statement"] == proof["native_result"]["theorem"] == row["statement"]
                 and route["statement_sha256"] == proof["statement_sha256"] == row["statement_sha256"]
                 and route["lineage_sha256"] == proof["lineage_sha256"] == row["lineage_sha256"]
                 and route["family"] == proof["family"] == row["family"],
                 "candidate projected formula differs from its original native source/goal/proof binding")
        _require(validate_statement(source) == row["statement"],
                 "candidate source does not parse to the native proved original goal")
        projected.append({"name": row["name"], "source": source, "statement": row["statement"],
                          "statement_sha256": row["statement_sha256"], "lineage_sha256": row["lineage_sha256"]})
    return projected


def _claim_boundary() -> dict:
    return {"comparison_scope": "human-reviewed candidate-template comparison under the declared frozen exposure audit",
            "sealed_benchmark": False, "independent_benchmark_ownership_attested": False,
            "unseen_semantic_generalization_claim": False, "base_model_pretraining_exposure": "unknown",
            "reserved32_scored": False, "reserved32_independent_test": False,
            "h0_complete": False, "h1_complete": False, "h5_claim_available": False,
            "human_and_reference_review": _ASSERTION_SCOPE,
            "historical_audit_scope": "frozen review-time source inventory; not live source revalidation",
            "native_or_lean_execution_repeated_by_loader": False,
            "training_authorized": False, "compute_authorized": False}


def _acknowledgements() -> dict:
    return {"all64_original_sources_templates_and_intermediates_reviewed": True,
            "all64_excluded_from_train_and_dev": True, "whole_template_reservation_reviewed": True,
            "known_primitive_correlations_and_audit_limitations_reviewed": True,
            "no_complete_semantic_equivalence_or_unseen_claim": True,
            "base_model_pretraining_exposure_unknown": True,
            "independent_benchmark_ownership_not_attested": True, "final_h1_set_not_sealed": True,
            "reserved32_not_scored_in_pilot": True, "reference_readiness_separately_reviewed": True,
            "no_training_authorization": True, "no_compute_authorization": True}


def _check_native_process(record: dict, *, mode: str, manifest: dict, bundle_file: dict) -> dict:
    from training.peano_hydra.review_runtime import ProcessLimits, validate_process_record
    _keys(record, {"schema", "process", "source_files_before", "source_files_after", "request",
                   "source_files_unchanged", "status"}, "native process receipt")
    _require(record["schema"] == "peano-hydra-frontier-benchmark-candidate-process-v1"
             and record["status"] == "verified" and record["source_files_unchanged"] is True
             and record["source_files_before"] == record["source_files_after"], "candidate native process did not complete unchanged")
    expected_sources = {name: manifest["source_identity"]["files"][name] for name in (
        "training/peano_hydra/frontier_benchmark_candidates.py", "scripts/build_peano_hydra_benchmark_candidates.py",
        "training/peano_hydra/review_runtime.py", "scripts/hydra_bounded_exec.py")}
    _require(record["source_files_before"] == expected_sources, "native process source differs from candidate source identity")
    request, process = record["request"], record["process"]
    _keys(request, {"mode", "output", "bundle"}, "native process request")
    _require(request["mode"] == mode and type(request["output"]) is str and Path(request["output"]).is_absolute(),
             "native process request changed build/verify mode")
    _require(request["bundle"] is None if mode == "build" else
             type(request["bundle"]) is str and Path(request["bundle"]).is_absolute(), "native verification lost its prior bundle reference")
    command = tuple(process["command"])
    _require(len(command) == 7 and command[1:5] == ("-I", "-B", "-X", "pycache_prefix=/dev/null")
             and Path(command[5]).name == "build_peano_hydra_benchmark_candidates.py" and command[6] == "--worker",
             "native candidate process changed its fixed guarded worker")
    limits = ProcessLimits(wall_seconds=150, cpu_seconds=120, rss_bytes=1024**3, output_bytes=128 * 1024)
    validate_process_record(process, command=command, limits=limits, input_bytes=_canonical(request) + b"\n", success_codes=(0,))
    _require(not process["stderr"], "successful native receipt contains unexpected stderr")
    result = bridge._decode(process["stdout"].encode(), 128 * 1024, "native candidate worker result")
    _keys(result, {"schema", "status", "mode", "manifest_sha256", "bundle_sha256", "verified_route_count",
                   "verified_decisions", "primary_goal_count", "reserved_goal_count", "prior_bundle",
                   "forbidden_model_modules", "claims"}, "native candidate worker result")
    _require(result["schema"] == "peano-hydra-frontier-benchmark-candidate-worker-v1"
             and result["status"] == "verified" and result["mode"] == mode
             and result["manifest_sha256"] == manifest["manifest_sha256"]
             and result["bundle_sha256"] == manifest["bundle_sha256"]
             and result["verified_route_count"] == manifest["verified_route_count"] == 64
             and result["verified_decisions"] == manifest["verified_decisions"]
             and result["primary_goal_count"] == result["reserved_goal_count"] == 32
             and result["forbidden_model_modules"] == [] and result["claims"] == manifest["claims"],
             "native worker result differs from complete candidate evidence")
    if mode == "build":
        _require(result["prior_bundle"] is None, "native build reused a previous bundle")
    else:
        prior = result["prior_bundle"]
        _keys(prior, {"path", "bytes", "sha256"}, "native verification prior bundle")
        _require(prior["path"] == request["bundle"] and prior["bytes"] == bundle_file["bytes"]
                 and prior["sha256"] == bundle_file["sha256"], "fresh native verification did not bind the exact original bundle bytes")
    return result


def _check_candidate(inputs: _Inputs, manifest_path: Path, manifest_sha: str, audit_path: Path, audit_sha: str) -> dict:
    from training.peano_hydra import frontier_benchmark_audit as audit_api
    manifest, manifest_file = inputs.json(manifest_path, expected=manifest_sha, maximum=MAX_MANIFEST_BYTES)
    candidate.validate_manifest(manifest)
    audit, audit_file = inputs.json(audit_path, expected=audit_sha, maximum=MAX_AUDIT_BYTES)
    audit_api.validate_audit_record(audit)
    summary = audit_api.audit_summary(audit)
    _require(summary["status"] == "no-detected-overlap-in-declared-sources"
             and not summary["blocking_exact_overlap_families"] and not summary["template_review_flags"]
             and not summary["blocking_coverage_gaps"] and audit["reference_state_coverage_complete"] is True,
             "benchmark audit blocked by exact/state/template exposure or incomplete reference coverage")
    identity = audit["candidate_identity"]
    _keys(identity, set(_NATIVE_DESCRIPTOR_NAMES) | set(_IDENTITY_HASHES), "audit candidate identity")
    records = {}
    for name in _NATIVE_DESCRIPTOR_NAMES:
        raw = inputs.described(audit_path.parent, identity[name], label="audit " + name)
        records[name] = bridge._decode(raw, MAX_EVIDENCE_BYTES, "audit-pinned " + name)
    _require(audit_path.parent / identity["manifest"]["path"] == manifest_path
             and {k: identity["manifest"][k] for k in ("bytes", "sha256")} == manifest_file
             and records["manifest"] == manifest, "audit points to a different candidate manifest")
    for name in ("plan", "bundle"):
        _require(audit_path.parent / identity[name]["path"] == manifest_path.parent / (name + ".json")
                 and {k: identity[name][k] for k in ("bytes", "sha256")} == manifest["artifacts"][name + ".json"],
                 "audit points to a different candidate plan/bundle")
    bundle = records["bundle"]
    _require(records["plan"] == bundle["plan"], "saved candidate plan differs from native bundle")
    for name, descriptor in manifest["artifacts"].items():
        observed, _ = inputs.read(manifest_path.parent / name, expected=descriptor["sha256"],
                                  maximum=candidate.MAX_BUNDLE_BYTES, retain=False)
        _require(observed == descriptor, "candidate artifact differs from the native manifest inventory")
    rebuilt = candidate.build_candidate_manifest(bundle, artifacts=manifest["artifacts"])
    _require(rebuilt == manifest, "candidate manifest differs from its complete native proof metadata")
    expected_identity_hashes = {"manifest_sha256": manifest["manifest_sha256"], "plan_sha256": manifest["plan_sha256"],
        "bundle_sha256": manifest["bundle_sha256"], "source_identity_sha256": manifest["source_identity"]["source_files_sha256"],
        "primary_goals_sha256": _digest(manifest["primary_goals"]), "reserved_goals_sha256": _digest(manifest["reserved_goals"])}
    _require({k: identity[k] for k in _IDENTITY_HASHES} == expected_identity_hashes,
             "audit candidate digest join changed source/template/native cohort identity")
    all_goals = manifest["primary_goals"] + manifest["reserved_goals"]
    expected_goals = {row["name"]: (row["family"], row["statement"], row["statement_sha256"]) for row in all_goals}
    audited_goals = {row["id"]: (family["family"], row["statement"], row["statement_sha256"])
                     for family in audit["families"] for row in family["goals"]}
    _require(audit["candidate_count"] == 64 and audit["family_count"] == 8 and audited_goals == expected_goals,
             "audit did not cover all64 exact canonical candidate sources/templates")
    _require(identity["native_build_process"]["sha256"] != identity["native_verify_process"]["sha256"]
             and identity["native_build_process"]["path"] != identity["native_verify_process"]["path"],
             "candidate requires a distinct fresh native verification receipt")
    build = _check_native_process(records["native_build_process"], mode="build", manifest=manifest,
                                   bundle_file=identity["bundle"])
    verified = _check_native_process(records["native_verify_process"], mode="verify", manifest=manifest,
                                      bundle_file=identity["bundle"])
    _require(records["native_verify_result"] == verified
             and records["native_build_process"]["request"]["output"] != records["native_verify_process"]["request"]["output"],
             "native replay is not a distinct complete verification of the original bundle")
    primary = _projection(manifest["primary_goals"], bundle["plan"]["routes"], bundle["proofs"])
    reserved = _projection(manifest["reserved_goals"], bundle["plan"]["routes"], bundle["proofs"])
    exclusions = [{key: row[key] for key in ("name", "family", "source_sha256", "statement_sha256",
                                            "template_sha256", "lineage_sha256")}
                  for row in bundle["plan"]["routes"]]
    binding = {"manifest_file_sha256": manifest_file["sha256"], "manifest_sha256": manifest["manifest_sha256"],
               "bundle_file_sha256": identity["bundle"]["sha256"], "bundle_sha256": manifest["bundle_sha256"],
               "audit_file_sha256": audit_file["sha256"], "audit_sha256": audit["audit_sha256"],
               "epoch_sha256": manifest["epoch"]["epoch_sha256"],
               "source_identity_sha256": manifest["source_identity"]["source_files_sha256"],
               "primary_goals_sha256": _digest(primary), "reserved_goals_sha256": _digest(reserved),
               "all64_exclusions_sha256": _digest(exclusions)}
    return {"manifest": manifest, "audit": audit, "summary": summary, "binding": binding,
            "primary": primary, "reserved": reserved, "exclusions": exclusions,
            "audited_file_sha256": sorted({row["sha256"] for row in audit["source_inventory"]})}


def _read_external_evidence(inputs: _Inputs, parent: Path, descriptor: dict, *, role: str,
                            epoch_sha256: str, asserted_facts: dict) -> dict:
    """Check an external human-reviewed evidence envelope and its raw artifacts.

    This is intentionally metadata validation, not a validator for arbitrary
    Lean/native output formats. The envelope labels its facts as assertions;
    exact underlying output bytes must also be supplied and pinned.
    """
    raw = inputs.described(parent, descriptor, label="reference " + role)
    evidence = bridge._decode(raw, MAX_EVIDENCE_BYTES, "external reference evidence")
    _keys(evidence, {"schema", "role", "epoch_sha256", "asserted_facts", "raw_artifacts", "assertion_scope", "evidence_sha256"},
          "external reference evidence")
    _signed(evidence, "evidence_sha256", "external reference evidence")
    _require(evidence["schema"] == EVIDENCE_SCHEMA and evidence["role"] == role
             and evidence["epoch_sha256"] == epoch_sha256 and evidence["asserted_facts"] == asserted_facts
             and evidence["assertion_scope"] == _ASSERTION_SCOPE,
             "external reference evidence differs from the human-reviewed asserted facts")
    artifacts = evidence["raw_artifacts"]
    _require(type(artifacts) is list and 1 <= len(artifacts) <= 32, "reference evidence requires bounded pinned underlying artifacts")
    _require(len({item["path"] for item in artifacts}) == len(artifacts), "reference raw artifact inventory repeats")
    envelope_path = parent / descriptor["path"]
    for item in artifacts:
        _require(parent / _descriptor(item, "reference raw artifact")["path"] != envelope_path,
                 "reference evidence cannot substitute its own assertion for underlying output")
        inputs.described(parent, item, label="reference raw artifact", retain=False)
    return evidence


def _check_readiness(inputs: _Inputs, parent: Path, descriptor: object, epoch: dict) -> dict:
    _require(descriptor is not None,
             "pending reference readiness: accepted human review must pin Lean4.31, semantic checks and two full cold-library passes")
    raw = inputs.described(parent, _descriptor(descriptor, "required reference readiness"), label="required reference readiness")
    record = bridge._decode(raw, MAX_REVIEW_BYTES, "human-reviewed reference readiness")
    required = {"schema", "status", "reviewed_by_human", "reviewer_reference", "reviewed_at", "epoch_sha256",
                "edition_identity_sha256", "theorem_dag_sha256", "reviewed_definition_dag_sha256", "frozen_profile",
                "lean", "semantic_checks", "cold_library", "independent_verification", "resource_review",
                "assertion_scope", "claims", "readiness_sha256"}
    _keys(record, required, "required reference readiness")
    _signed(record, "readiness_sha256", "reference readiness")
    _human_header(record["reviewer_reference"], record["reviewed_at"])
    _require(record["schema"] == READINESS_SCHEMA and record["status"] == "human-reviewed-reference-ready"
             and record["reviewed_by_human"] is True and record["assertion_scope"] == _ASSERTION_SCOPE,
             "pending reference readiness: an externally supplied human-reviewed assertion is required")
    _require(record["epoch_sha256"] == epoch["epoch_sha256"]
             and record["edition_identity_sha256"] == epoch["edition_identity_sha256"]
             and record["theorem_dag_sha256"] == epoch["theorem_dag"]["sha256"]
             and record["reviewed_definition_dag_sha256"] == epoch["definition_dag"]["sha256"],
             "reference readiness does not cover the exact frozen candidate epoch")
    _require(record["claims"] == {"human_identity_attested": False, "execution_attested_by_this_loader": False,
                "h0_complete": False, "h1_complete": False, "sealed_benchmark": False,
                "training_authorized": False, "compute_authorized": False}, "reference readiness promoted a forbidden claim")
    profile = record["frozen_profile"]
    _keys(profile, {"profile_sha256", "source_files_sha256", "claim", "reviewed", "evidence"}, "frozen semantic profile")
    _sha(profile["profile_sha256"], "frozen semantic profile")
    _sha(profile["source_files_sha256"], "frozen semantic source")
    _require(profile["claim"] == "sound-theorem-prover-no-decision-claim" and profile["reviewed"] is True,
             "required semantic profile/claim boundary is not reviewed")
    lean = record["lean"]
    _keys(lean, {"version", "toolchain_pin", "compiler_sha256", "reference_source_sha256", "evidence"}, "pinned Lean environment")
    _require(lean["version"] == "4.31.0" and lean["toolchain_pin"] == "leanprover/lean4:v4.31.0",
             "pending reference readiness: Lean4.28 compatibility does not meet the pinned Lean4.31 environment")
    _sha(lean["compiler_sha256"], "Lean4.31 compiler")
    _sha(lean["reference_source_sha256"], "independent Lean reference source")
    semantic = record["semantic_checks"]
    semantic_fields = {"status", "semantic_formula_count", "theorem_count", "decision_claim", "all_in_scope_results_agree",
        "false_acceptance_count", "unresolved_semantics_count", "mutation_categories", "required_mutations_rejected",
        "kernel_import_boundary_passed", "original_goal_tests_passed", "transactional_history_tests_passed", "evidence"}
    _keys(semantic, semantic_fields, "required semantic checks")
    mutations = ["proof_constructors", "binders", "substitutions", "translations", "induction_instances", "negative_witnesses"]
    _require(semantic["status"] == "passed" and type(semantic["semantic_formula_count"]) is int
             and 1000 <= semantic["semantic_formula_count"] <= 1000000
             and type(semantic["theorem_count"]) is int and 400 <= semantic["theorem_count"] <= semantic["semantic_formula_count"]
             and semantic["decision_claim"] is False and semantic["all_in_scope_results_agree"] is True
             and type(semantic["false_acceptance_count"]) is int and semantic["false_acceptance_count"] == 0
             and type(semantic["unresolved_semantics_count"]) is int and semantic["unresolved_semantics_count"] == 0
             and semantic["mutation_categories"] == mutations
             and all(semantic[key] is True for key in ("required_mutations_rejected", "kernel_import_boundary_passed",
                       "original_goal_tests_passed", "transactional_history_tests_passed")),
             "pending reference readiness: required semantic/reference checks or mutations incomplete")
    cold = record["cold_library"]
    _keys(cold, {"scope", "epoch_target_count", "target_inventory_sha256", "fresh_workers", "passes"}, "full cold-library evidence")
    count = epoch["theorem_dag"]["node_count"]
    _require(type(count) is int and 1 <= count <= 16384 and cold["scope"] == "full"
             and type(cold["epoch_target_count"]) is int and cold["epoch_target_count"] == count
             and cold["fresh_workers"] is True and type(cold["passes"]) is list and len(cold["passes"]) == 2,
             "pending reference readiness: two full cold-library passes are required, not a sample")
    _sha(cold["target_inventory_sha256"], "full frozen target inventory")
    for index, run in enumerate(cold["passes"], 1):
        _keys(run, {"pass_number", "checked_count", "failed_count", "unknown_count", "root_sha256", "evidence"}, "cold pass")
        _require(type(run["pass_number"]) is int and run["pass_number"] == index
                 and type(run["checked_count"]) is int and run["checked_count"] == count
                 and type(run["failed_count"]) is int and run["failed_count"] == 0
                 and type(run["unknown_count"]) is int and run["unknown_count"] == 0,
                 "pending reference readiness: cold pass is not100% complete")
        _sha(run["root_sha256"], "full cold pass root")
    _require(cold["passes"][0]["root_sha256"] == cold["passes"][1]["root_sha256"], "full cold-library pass roots differ")
    verification = record["independent_verification"]
    _keys(verification, {"status", "fresh_reference_recheck", "both_full_cold_passes_rechecked", "evidence"}, "independent reference verification")
    _require(verification["status"] == "passed" and verification["fresh_reference_recheck"] is True
             and verification["both_full_cold_passes_rechecked"] is True, "pending independent reference-readiness verification")
    resources = record["resource_review"]
    _keys(resources, {"reviewed", "resource_envelope_sha256", "evidence"}, "reference resource review")
    _require(resources["reviewed"] is True, "reference execution resource envelope not reviewed")
    _sha(resources["resource_envelope_sha256"], "reference resource envelope")
    sections = [("frozen_profile", profile), ("lean_environment", lean), ("semantic_checks", semantic),
                ("cold_pass_1", cold["passes"][0]), ("cold_pass_2", cold["passes"][1]),
                ("independent_verification", verification), ("resource_review", resources)]
    evidence = []
    for role, section in sections:
        facts = {key: value for key, value in section.items() if key != "evidence"}
        if role.startswith("cold_pass_"):
            facts.update({key: cold[key] for key in ("scope", "epoch_target_count", "target_inventory_sha256", "fresh_workers")})
        evidence.append(_read_external_evidence(inputs, parent, section["evidence"], role=role,
                                                epoch_sha256=epoch["epoch_sha256"], asserted_facts=facts))
    _require(len({section["evidence"]["sha256"] for _, section in sections}) == len(sections),
             "reference readiness must retain distinct evidence for each required obligation")
    native_runs = evidence[3:6]
    _require(all(set(item["sha256"] for item in left["raw_artifacts"]).isdisjoint(
                     item["sha256"] for item in right["raw_artifacts"])
                 for index, left in enumerate(native_runs) for right in native_runs[index + 1:]),
             "cold passes and independent verification reused the same underlying output bytes")
    return record


def _check_review(inputs: _Inputs, review_path: Path, review_sha: str, checked: dict) -> tuple[dict, dict]:
    try:
        review, _ = inputs.json(review_path, expected=review_sha, maximum=MAX_REVIEW_BYTES)
    except FileNotFoundError as error:
        raise BenchmarkProtocolError("external human benchmark review is required; no accepted review was supplied") from error
    required = {"schema", "decision", "reviewer_reference", "reviewed_at", "human_assertion", "candidate_binding",
                "whole_template_exclusions", "acknowledgements", "reference_readiness", "review_sha256"}
    _keys(review, required, "human benchmark review")
    _signed(review, "review_sha256", "human benchmark review")
    _human_header(review["reviewer_reference"], review["reviewed_at"])
    _require(review["schema"] == REVIEW_SCHEMA and review["decision"] == "accept",
             "external human benchmark review has not accepted this candidate boundary")
    _require(review["human_assertion"] == {"provided_by_human": True, "identity_attested": False,
                 "cryptographic_signature_verified": False, "assertion_scope": _ASSERTION_SCOPE},
             "benchmark review must remain an external human assertion, not an identity attestation")
    _require(review["candidate_binding"] == checked["binding"]
             and review["whole_template_exclusions"] == checked["exclusions"],
             "human benchmark review does not bind all64 exact source/template exclusions and primary/reserve digests")
    _require(review["acknowledgements"] == _acknowledgements(), "benchmark review changed its exclusions or claim/authorization boundary")
    readiness = _check_readiness(inputs, review_path.parent, review["reference_readiness"], checked["manifest"]["epoch"])
    return review, readiness


@dataclass(frozen=True, slots=True)
class BenchmarkReference:
    manifest_path: Path
    manifest_sha256: str
    audit_path: Path
    audit_sha256: str
    review_path: Path
    review_sha256: str

    def __post_init__(self):
        for path_field, sha_field in (("manifest_path", "manifest_sha256"), ("audit_path", "audit_sha256"),
                                       ("review_path", "review_sha256")):
            object.__setattr__(self, path_field, bridge._absolute(getattr(self, path_field)))
            _sha(getattr(self, sha_field), sha_field)
        _require(len({self.manifest_path, self.audit_path, self.review_path}) == 3, "benchmark reference inputs must be distinct files")

    def to_dict(self) -> dict:
        """Portable raw identity only; paths do not change a transported review."""
        return {"schema": REFERENCE_SCHEMA, "manifest_file_sha256": self.manifest_sha256,
                "audit_file_sha256": self.audit_sha256, "review_file_sha256": self.review_sha256}

    def protected_paths(self) -> tuple[Path, ...]:
        return tuple(dict.fromkeys((self.manifest_path.parent, self.audit_path.parent, self.review_path.parent)))

    def load(self) -> dict:
        """Read supplied review/evidence; perform no native/reference execution."""
        try:
            with _Inputs() as inputs:
                checked = _check_candidate(inputs, self.manifest_path, self.manifest_sha256, self.audit_path, self.audit_sha256)
                review, readiness = _check_review(inputs, self.review_path, self.review_sha256, checked)
                inputs.assert_unchanged()
                result = {**self.to_dict(), "manifest_sha256": checked["manifest"]["manifest_sha256"],
                          "audit_sha256": checked["audit"]["audit_sha256"], "review_sha256": review["review_sha256"],
                          "epoch_sha256": checked["binding"]["epoch_sha256"],
                          "primary_goals": checked["primary"], "reserved_goals": checked["reserved"],
                          "heldout_goals_sha256": checked["binding"]["primary_goals_sha256"],
                          "reserved_goals_sha256": checked["binding"]["reserved_goals_sha256"],
                          "all64_exclusions_sha256": checked["binding"]["all64_exclusions_sha256"],
                          "audited_file_sha256": checked["audited_file_sha256"],
                          "reference_readiness_file_sha256": review["reference_readiness"]["sha256"],
                          "reference_readiness_sha256": readiness["readiness_sha256"],
                          "claim_boundary": _claim_boundary()}
                return json.loads(_canonical(result))
        except BenchmarkProtocolError:
            raise
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
            raise BenchmarkProtocolError(f"benchmark reference evidence unavailable or inconsistent: {error}") from error

    @property
    def goals(self) -> tuple[dict, ...]:
        return tuple(self.load()["primary_goals"])


def benchmark_review_requirements(manifest_path: Path, manifest_sha256: str,
                                  audit_path: Path, audit_sha256: str) -> dict:
    """Prepare facts to inspect, never a review record or human acceptance.

    No reviewer, timestamp, decision, signature, or readiness evidence is
    generated. Current native candidates remain pending external human review
    and the separately supplied reference-readiness obligations.
    """
    manifest_path, audit_path = bridge._absolute(manifest_path), bridge._absolute(audit_path)
    with _Inputs() as inputs:
        checked = _check_candidate(inputs, manifest_path, manifest_sha256, audit_path, audit_sha256)
        inputs.assert_unchanged()
        return {"schema": REQUIREMENTS_SCHEMA, "status": "pending_external_human_review_and_reference_readiness",
                "candidate_binding": checked["binding"], "whole_template_exclusions": checked["exclusions"],
                "required_acknowledgements": _acknowledgements(),
                "required_reference_readiness": {"schema": READINESS_SCHEMA,
                    "epoch_sha256": checked["binding"]["epoch_sha256"], "lean_version": "4.31.0",
                    "semantic_reference_checks": "required, independently checked, externally pinned evidence",
                    "cold_library": "two complete identical100%-green passes of the frozen epoch",
                    "evidence_not_present_in_native_candidate_bundle": True},
                "audited_file_sha256": checked["audited_file_sha256"], "claim_boundary": _claim_boundary()}
