"""Static archive integrity plus fresh native fixture checks, not a Lean run.

The separately retained verification receipt records the real fresh Lean and
cold replay. These portable regressions do not need that workstation's Lean
installation, preparation copies, or original absolute checkout location.
"""

from collections import Counter
import hashlib
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra import reference, review  # noqa: E402
from training.peano_hydra.conformance import build_conformance_cases  # noqa: E402
from training.peano_hydra.frontier import digest  # noqa: E402


RUN = ROOT / "artifacts/peano-hydra/reference-review-2026-08-27"
SOURCE = "a69e2e9bfdaf4de3b567727a214367c193478cea"
REPORT = "b705ec2e21a2089653b6b900d1bcdfdccbad51a727b4f7e69acf7e83dbcb5d6d"


@pytest.fixture(scope="module")
def evidence():
    names = ("plan", "report", "native", "native_worker", "reference_build", "reference_results", "cold", "verification")
    return {name: review.read_record(RUN / f"{name}.json") for name in names}


def test_archive_checksums_cover_exact_small_sources_and_evidence():
    expected = {"plan.json", "report.json", "cases.jsonl", "native.json", "native_worker.json",
                "reference_build.json", "reference_results.json", "cold.json", "verification.json", "README.md",
                "verification-attempt-1.json", "verification-attempt-1.log",
                "reference-source/HydraAxiomAudit.lean"}
    expected.update("reference-source/" + name for name in reference.MODULES)
    entries = {}
    for line in (RUN / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        assert match is not None
        checksum, name = match.groups()
        assert name in expected and name not in entries
        path = RUN / name
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_size <= review.MAX_BYTES
        assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum
        entries[name] = checksum
    assert set(entries) == expected and len(entries) == 21
    assert {path.relative_to(RUN).as_posix() for path in RUN.rglob("*") if path.is_file()} == expected | {"SHA256SUMS"}
    assert not list(RUN.rglob("*.olean*"))


def test_frozen_plan_report_and_native_fixture_bytes(evidence, monkeypatch):
    plan, report = evidence["plan"], evidence["report"]
    assert plan["source"]["git_commit"] == SOURCE and plan["source"]["git_dirty"] is False
    assert digest(plan["source"]["files"]) == plan["source"]["files_sha256"]
    review._signed(plan, "plan_sha256")
    review.validate_report_header(report)
    assert report["report_sha256"] == REPORT
    assert report["plan_sha256"] == plan["plan_sha256"]
    assert plan["parallel_workers"] == 1 and plan["reserved_reference_processes"] == 30
    for descriptor in (report["plan"], report["cases"], *report["evidence"].values()):
        raw = (RUN / descriptor["path"]).read_bytes()
        assert descriptor["bytes"] == len(raw) and descriptor["sha256"] == hashlib.sha256(raw).hexdigest()
    cases = build_conformance_cases()
    assert (RUN / "cases.jsonl").read_bytes() == review._case_archive(cases)
    # Static saved-command validation must not assume the CI interpreter lives
    # at the original workstation's path. Live --verify executes current code.
    recorded_python = evidence["native_worker"]["command"][0]
    monkeypatch.setattr(review, "_worker_command", lambda root: (
        recorded_python, str(Path(root) / "scripts/check_peano_hydra_review.py"), "--worker"))
    results = {name: evidence[name] for name in review.EVIDENCE_NAMES}
    review.validate_saved_results(plan, report, results)
    assert report["summary"]["native_positive_accepts"] == 1024
    assert report["summary"]["native_mutations_rejected"] == 280


def test_reference_conformance_is_complete_but_only_toolchain_compatibility(evidence):
    plan, results = evidence["plan"], evidence["reference_results"]
    manifest = plan["conformance"]
    assert manifest["case_count"] == 1321 and manifest["distinct_positive_formula_count"] == 1024
    assert manifest["certificate_mutation_count"] == 280 and manifest["wire_mutation_count"] == 17
    assert manifest["generation"]["templates"] == manifest["generation"]["seeds_per_template"] == 32
    assert "not Hydra search" in manifest["authorship"]
    assert results["status"] == "passed" and results["mismatches"] == []
    assert Counter(row["observed"] for row in results["cases"]) == {"ACCEPT": 1024, "REJECT": 282, "DECODE_ERROR": 15}
    assert "version 4.28.0," in plan["reference"]["compiler_version"]
    assert plan["reference"]["project_toolchain_pin"] == "leanprover/lean4:v4.31.0"
    assert plan["reference"]["matches_project_toolchain_pin"] is False
    assert plan["reference"]["project_git_commit"] == "d2903c8bd507b7e4458b1249f840a4e274befdbf"
    for name, descriptor in plan["reference"]["files"].items():
        raw = (RUN / "reference-source" / name).read_bytes()
        assert descriptor == {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    assert (RUN / "reference-source/HydraAxiomAudit.lean").read_text() == reference.AUDIT_SOURCE
    assert len(evidence["reference_build"]["compile_rows"]) == 8
    assert len(results["worker_rows"]) == 21


def test_lineage_inventory_does_not_invent_an_unseen_split(evidence):
    review_record = evidence["plan"]["lineage_review"]
    inventory = review_record["inventory"]
    assert inventory["component_count"] == len(inventory["components"]) == 28
    assert inventory["catalog_theorem_count"] == 2080
    assert sum(row["catalog_member_count"] for row in inventory["components"]) == 2080
    assert max(row["catalog_member_count"] for row in inventory["components"]) == 2048
    assert inventory["structural_candidate_component_count"] == 18
    assert inventory["structural_candidate_theorem_count"] == 19
    assert review_record["feasibility"]["unexposed_structural_component_count"] == 0
    assert review_record["conflict_count"] == len(review_record["conflicts"]) == 30
    assert Counter(row["split"] for row in review_record["allocations"]) == {"quarantine": 1, "unassigned": 27}
    assert review_record["status"] == "blocked" and review_record["review_status"] == "not-reviewed"
    assert review_record["human_review_acknowledgment"] is None
    assert review_record["model_training_authorized"] is False


def test_cold_sample_keeps_all_four_limit_failures_and_only_partial_roots(evidence):
    plan, cold = evidence["plan"], evidence["cold"]
    assert plan["cold_selection"]["scope"] == "sample" and plan["cold_selection"]["selected_targets"] == 16
    assert len(cold["batches"]) == 32 and len(cold["rows"]) == 28
    assert len({row["receipt"]["name"] for row in cold["rows"]}) == 14
    for row in cold["summary"]["passes"]:
        assert (row["checked"], row["unknown"], row["not_completed"]) == (14, 0, 2)
        assert row["ordered_root_sha256"] is None and row["all_selected_checked"] is False
        assert row["partial_root_sha256"] == "83a85cb70bb0ba3b4474ae8feec0f755ef9ff499b792d63f5223ed57c3515ecf"
    failures = [batch for batch in cold["batches"] if batch["worker"]["reason"] != "exited"]
    expected = {"central_binom_upper_support_package": ("rss_limit", -9),
                "three_mod_four_good_prime_exclusive": ("cpu_limit", -24)}
    assert Counter(batch["worker"]["reason"] for batch in failures) == {"rss_limit": 2, "cpu_limit": 2}
    for batch in failures:
        name = plan["cold_plan"]["targets"][batch["indices"][0]]["name"]
        assert (batch["worker"]["reason"], batch["worker"]["returncode"]) == expected[name]
        assert batch["completed_targets"] == 0
        resources = batch["worker"]["resources"]
        assert resources["cpu_seconds"] > 0 and resources["peak_rss_bytes"] > 0
        assert resources["cpu_instructions"] is resources["energy_joules"] is None
    assert 422 <= cold["wall_seconds"] < 423 and cold["wall_budget"] == 900
    assert cold["summary"]["full_epoch_replayed_twice"] is False


def test_independent_verification_is_explicitly_not_human_or_research_approval(evidence):
    verified = evidence["verification"]
    assert verified == {"status": "passed", "report_sha256": REPORT, "reference_cases_rechecked": 1321,
                        "cold_positive_receipts_reproduced": 28, "live_lineage_audits_repeated": True,
                        "fresh_reference_rebuilt": True, "model_calls": 0, "solver_calls": 0,
                        "h0_complete": False, "model_training_authorized": False, "research_claim_eligible": False}
    for name in ("plan", "report"):
        for flag in ("model_training_authorized", "independent_human_review_granted", "h0_complete",
                     "h1_complete", "sealed_benchmark", "research_claim_eligible"):
            assert evidence[name][flag] is False


def test_failed_primary_attempt_is_preserved_without_promoting_it():
    attempt = review.read_record(RUN / "verification-attempt-1.json")
    assert attempt["status"] == "failed" and attempt["exit_code"] == 2
    assert attempt["followup_source_check"]["status"] == "rejected"
    assert attempt["followup_source_check"]["path"] == "peano-lab/py/peano_lab/library/lean_proof_strand.py"
    assert attempt["research_claim_eligible"] is attempt["model_training_authorized"] is False
    log = (RUN / attempt["exact_console_log"]).read_text()
    assert "hydra-review: independent cold replay failed to reproduce a retained positive" in log


def test_review_guide_and_archive_have_no_dangling_local_links():
    for source in (RUN / "README.md", ROOT / "docs/HYDRA_REFERENCE_REVIEW.md"):
        text = source.read_text(encoding="utf-8")
        assert "not yet run" not in text.lower() and "verification is currently running" not in text.lower()
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            path = (source.parent / target.split("#", 1)[0]).resolve()
            assert path.is_relative_to(ROOT) and path.exists(), (source, target)
