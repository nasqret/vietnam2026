"""Regression contracts for shared-certificate capacity measurements."""

from pathlib import Path
from runpy import run_path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = run_path(str(ROOT / "scripts" / "profile_peano_certificate_capacity.py"))
profile = SCRIPT["profile"]


def test_capacity_profile_distinguishes_occurrences_from_objects() -> None:
    payload = profile(("zero_add", "add_comm"))
    rows = payload["theorems"]

    assert payload["format"] == "peano-certificate-capacity-profile"
    assert payload["version"] == 1
    assert [row["name"] for row in rows] == ["zero_add", "add_comm"]
    assert rows[0]["structural_nodes"] == rows[0]["distinct_proof_objects"]
    assert rows[1]["structural_nodes"] > rows[1]["distinct_proof_objects"]
    assert rows[1]["reused_references"] > 0


def test_capacity_profile_rejects_unknown_theorem() -> None:
    with pytest.raises(ValueError, match="unknown checked theorem"):
        profile(("not_a_theorem",))
