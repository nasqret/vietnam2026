"""Focused mutation tests for the HA campaign manifest validator."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "arithmetic-library"
    / "ha-number-theory-campaign.json"
)
VALIDATOR_PATH = REPOSITORY_ROOT / "scripts" / "verify_ha_number_theory_campaign.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "verify_ha_number_theory_campaign_under_test",
        VALIDATOR_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


def _campaign() -> dict[str, object]:
    with CAMPAIGN_PATH.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _write_campaign(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "campaign.json"
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return path


def _install_k3_candidate(
    campaign: dict[str, object],
    *,
    module_path: str,
    factory: str,
    theorem_name: str,
) -> None:
    k3 = campaign["layers"][3]
    k3["status"] = "candidate_seed"
    k3["candidate_modules"] = [
        {
            "path": module_path,
            "factory": factory,
            "theorem_names": [theorem_name],
            "role": "Synthetic K3 anti-circularity validator mutation.",
        }
    ]


def test_repository_campaign_validates() -> None:
    summary = VALIDATOR.validate_campaign(REPOSITORY_ROOT, CAMPAIGN_PATH)
    assert summary == {
        "layers": 12,
        "public_references": 56,
        "candidate_references": 42,
        "theorem_evidence": 51,
        "validation_gates": 7,
    }


def test_candidate_statement_receipt_must_match_factory(tmp_path: Path) -> None:
    campaign = deepcopy(_campaign())
    campaign["theorem_evidence"]["theorems"][0]["statement_sha256"] = "0" * 64
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(
        VALIDATOR.CampaignError,
        match="does not match the evidence theorem statement",
    ):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


def test_public_evidence_cannot_claim_closed_candidate_status(tmp_path: Path) -> None:
    campaign = deepcopy(_campaign())
    campaign["theorem_evidence"]["theorems"][0]["status"] = (
        "closed_checked_candidate"
    )
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(
        VALIDATOR.CampaignError,
        match="is public and cannot remain a closed candidate",
    ):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


def test_forward_layer_dependency_is_rejected(tmp_path: Path) -> None:
    campaign = deepcopy(_campaign())
    campaign["layers"][1]["depends_on_layers"].append("M5")
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(VALIDATOR.CampaignError, match="must exist and precede K1"):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


def test_beta_cannot_be_a_k3_foundational_reference(tmp_path: Path) -> None:
    campaign = deepcopy(_campaign())
    k3 = campaign["layers"][3]
    k3["status"] = "existing_public_core"
    k3["public_theorem_references"] = ["beta_at_exists_unique"]
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(
        VALIDATOR.CampaignError,
        match="K3 foundational references may not use beta, CRT, division, or remainder",
    ):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


def test_innocuously_named_k3_candidate_cannot_depend_directly_on_beta(
    tmp_path: Path,
) -> None:
    campaign = deepcopy(_campaign())
    _install_k3_candidate(
        campaign,
        module_path=(
            "peano-lab/py/peano_lab/library/"
            "eisenstein_quotient_sum_identity_candidate.py"
        ),
        factory="make_eisenstein_quotient_sum_identity_candidate_theorems",
        theorem_name="distinct_odd_prime_eisenstein_quotient_sum_identity",
    )
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(
        VALIDATOR.CampaignError,
        match=(
            "K3 foundational dependency path may not use beta, CRT, division, or remainder: "
            "distinct_odd_prime_eisenstein_quotient_sum_identity -> beta_sum_exists"
        ),
    ):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


def test_innocuously_named_k3_candidate_cannot_hide_beta_transitively(
    tmp_path: Path,
) -> None:
    campaign = deepcopy(_campaign())
    _install_k3_candidate(
        campaign,
        module_path=(
            "peano-lab/py/peano_lab/library/"
            "eisenstein_transposed_column_candidate.py"
        ),
        factory="make_eisenstein_transposed_column_candidate_theorems",
        theorem_name="eisenstein_row_transposed_column_count_partition",
    )
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(
        VALIDATOR.CampaignError,
        match=(
            "K3 foundational dependency path may not use beta, CRT, division, or remainder: "
            "eisenstein_row_transposed_column_count_partition -> "
            "eisenstein_transposed_outer_column_choices -> .*beta"
        ),
    ):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


@pytest.mark.parametrize(
    "theorem_name",
    ("division_remainder_unique", "remainder_decomposition_to_mod_eq"),
)
def test_division_or_remainder_cannot_be_a_k3_foundational_reference(
    tmp_path: Path,
    theorem_name: str,
) -> None:
    campaign = deepcopy(_campaign())
    k3 = campaign["layers"][3]
    k3["status"] = "existing_public_core"
    k3["public_theorem_references"] = [theorem_name]
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(
        VALIDATOR.CampaignError,
        match=(
            "K3 foundational references may not use beta, CRT, division, or remainder: "
            f"'{theorem_name}'"
        ),
    ):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


def test_k3_public_dependency_closure_cannot_hide_division(
    tmp_path: Path,
) -> None:
    campaign = deepcopy(_campaign())
    k3 = campaign["layers"][3]
    k3["status"] = "existing_public_core"
    k3["public_theorem_references"] = ["even_odd_exclusive_pointwise"]
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(
        VALIDATOR.CampaignError,
        match=(
            "K3 foundational dependency path may not use beta, CRT, division, or remainder: "
            "even_odd_exclusive_pointwise -> division_remainder_unique"
        ),
    ):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


def test_innocuously_named_k3_candidate_cannot_hide_division_transitively(
    tmp_path: Path,
) -> None:
    campaign = deepcopy(_campaign())
    _install_k3_candidate(
        campaign,
        module_path=(
            "peano-lab/py/peano_lab/library/"
            "euler_criterion_bounded_candidate.py"
        ),
        factory="make_euler_criterion_bounded_candidate_theorems",
        theorem_name="double_predecessor_ne_one",
    )
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(
        VALIDATOR.CampaignError,
        match=(
            "K3 foundational dependency path may not use beta, CRT, division, or remainder: "
            "double_predecessor_ne_one -> even_odd_exclusive_pointwise -> "
            "division_remainder_unique"
        ),
    ):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


def test_missing_candidate_module_is_rejected(tmp_path: Path) -> None:
    campaign = deepcopy(_campaign())
    campaign["layers"][4]["candidate_modules"][0]["path"] = (
        "peano-lab/py/peano_lab/library/missing_candidate.py"
    )
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(VALIDATOR.CampaignError, match="does not exist as a file"):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)


def test_wrong_blueprint_digest_is_rejected(tmp_path: Path) -> None:
    campaign = deepcopy(_campaign())
    campaign["source_specification"]["sha256"] = "0" * 64
    path = _write_campaign(tmp_path, campaign)
    with pytest.raises(VALIDATOR.CampaignError, match="does not match the frozen"):
        VALIDATOR.validate_campaign(REPOSITORY_ROOT, path)
