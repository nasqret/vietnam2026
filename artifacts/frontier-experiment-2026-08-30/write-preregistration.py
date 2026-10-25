"""Publish exact pre-outcome goals and criteria, without admission or approval."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-execution-20260830")
ARCHIVE = Path(__file__).absolute().parent
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]
from training.peano_hydra import frontier_benchmark_run as run
from training.peano_hydra import frontier_benchmark_protocol as protocol
from training.peano_hydra import scaling_experiment as experiment


def descriptor(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def save(path, value):
    with path.open("xb") as stream: stream.write(run.canonical(value) + b"\n")


def main():
    candidate_dir = ARCHIVE / "benchmark-candidates-build-02"
    manifest = json.loads((candidate_dir / "manifest.json").read_bytes())
    bundle = json.loads((candidate_dir / "bundle.json").read_bytes())
    audit = ARCHIVE / "benchmark-exposure-audit-01.json"
    requirements = protocol.benchmark_review_requirements(candidate_dir / "manifest.json",
        descriptor(candidate_dir / "manifest.json")["sha256"], audit, descriptor(audit)["sha256"])
    primary = protocol._projection(manifest["primary_goals"], bundle["plan"]["routes"], bundle["proofs"])
    reserve = protocol._projection(manifest["reserved_goals"], bundle["plan"]["routes"], bundle["proofs"])
    historical_path = Path("/Users/bnaskrecki/codex/test/vietnam2026-new-theorems/artifacts/peano-hydra/paired-search-v2-2026-08-29/development-plan-01.json")
    historical = json.loads(historical_path.read_bytes())
    historical_goals = [{k: row[k] for k in ("name", "source", "statement", "statement_sha256")} for row in historical["goals"]]
    assert run.digest(historical_goals) == experiment.COHORT_GOAL_SHA256["exposed-primary32"]
    diagnostic_component = run.digest({"scope": "one conservative public-exposed PRIMARY32 diagnostic component",
                                       "goal_projection_sha256": run.digest(historical_goals)})
    regression = [{**row, "lineage_sha256": diagnostic_component} for row in historical_goals]
    criteria = run.acceptance_protocol()
    criteria_path = ARCHIVE / "acceptance-protocol-01.json"
    save(criteria_path, criteria)
    design = {"schema": "peano-hydra-frontier-pre-outcome-preregistration-v1",
        "status": "targets-and-criteria-fixed-human-reference-review-pending",
        "source_commit": "278d80552ab55b080365ddbae0d1d49be2fdc396",
        "execution_origin_manifest": descriptor(ROOT / "_deploy/frontier-origin-source.json"),
        "benchmark_manifest": descriptor(candidate_dir / "manifest.json"), "benchmark_audit": descriptor(audit),
        "benchmark_review_requirements": descriptor(ARCHIVE / "benchmark-review-requirements-02.json"),
        "benchmark_binding": requirements["candidate_binding"],
        "cohorts": {
            run.COHORTS[0]: {"goals": primary, "goals_sha256": run.digest(primary), "scope": "declared-project-exposure candidate; no independently owned H1 seal"},
            run.COHORTS[1]: {"goals": regression, "goals_sha256": run.digest(regression),
                "exact_historical_projection_sha256": run.digest(historical_goals),
                "historical_source": descriptor(historical_path),
                "lineage_label_scope": "declared conservative diagnostic component, not mathematical equivalence or novelty"},
        },
        "reserved_goals": reserve, "reserved_goals_sha256": run.digest(reserve),
        "all_64_template_variants_excluded_from_all_training": True,
        "reserve_scored_by_this_pilot": False,
        "roles": ["saved-corrected", "new-frontier"], "budgets": [8, 16],
        "fixed_search": {"max_depth": 16, "beam_width": 4, "candidates_per_state": 4,
                         "max_states": 64, "max_new_tokens": 64, "seed": 20260826},
        "search_profile": "context-alpha-v1", "limits": run.LIMITS,
        "baseline_adapter_manifest_sha256": run.BASELINE_SHA, "fresh_candidate_adapter_destination": run.ADAPTER_OUTPUT,
        "acceptance_protocol": descriptor(criteria_path),
        "pending_inputs": {"accepted_lineage_review": None, "admitted_preparation": None,
                           "production_token_preflight": None, "accepted_benchmark_reference_review": None,
                           "exact_resource_approval": None, "trained_candidate_adapter": None},
        "all_positive_proofs_require_fresh_native_replay": True,
        "training_authorized": False, "gpu_execution_authorized": False,
        "human_review_asserted": False, "sealed_benchmark": False, "research_claim_eligible": False,
        "unknown_base_pretraining_exposure": True, "automatic_retry": False, "resume": False}
    design["preregistration_sha256"] = run.digest(design)
    path = ARCHIVE / "evaluation-preregistration-01.json"
    save(path, design)
    print(json.dumps({"preregistration": descriptor(path), "acceptance": descriptor(criteria_path),
        "primary_goals_sha256": run.digest(primary), "reserved_goals_sha256": run.digest(reserve),
        "historical_primary32_projection": run.digest(historical_goals), "model_execution_performed": False}, sort_keys=True))


if __name__ == "__main__": main()
