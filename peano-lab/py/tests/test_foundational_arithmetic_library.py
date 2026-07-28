"""M20 contracts for the general foundational-arithmetic extension."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from peano_lab.engine.state import proof_metrics
from peano_lab.engine.tactics import MAX_USE_CERTIFICATE_NODES, MAX_USE_PROOF_DEPTH
from peano_lab.kernel.checker import check
from peano_lab.library.theorems import get, replay


ROOT = Path(__file__).resolve().parents[3]


FOUNDATIONAL_NAMES = (
    "eq_symm",
    "eq_trans",
    "succ_congr",
    "zero_or_succ",
    "nonzero_is_succ",
    "add_congr",
    "mul_congr",
    "add_right_cancel",
    "add_left_cancel",
    "zero_le",
    "le_succ_self",
    "le_zero",
    "one_le_of_ne_zero",
    "ne_zero_of_one_le",
    "le_add_left",
    "le_add_right",
    "add_le_add_right",
    "add_le_add_left",
    "succ_le_succ",
    "le_of_succ_le_succ",
    "le_succ",
    "lt_to_le",
    "add_le_cancel_right",
    "lt_irrefl_expanded",
    "le_eq_or_lt",
    "lt_of_lt_of_le",
    "lt_of_le_of_lt",
    "lt_trans",
    "le_or_lt",
    "lt_trichotomy",
    "lt_not_le",
    "le_not_lt",
    "lt_not_eq_add_middle",
    "mul_le_mul_left",
    "mul_le_mul_right",
    "mul_lt_mul_succ_left_nonzero",
    "division_remainder_succ",
    "division_remainder_exists",
    "remainder_bound_step",
    "division_block_upper",
    "positive_quotient_gap_impossible",
    "remainder_unique_same_quotient",
    "division_remainder_unique",
    "zero_remainder_implies_multiple",
    "multiple_has_zero_remainder",
    "add_eq_zero_left",
    "add_eq_zero_components",
    "mul_eq_one_components",
    "mul_ne_zero",
    "mul_left_cancel_nonzero",
    "mul_right_cancel_nonzero",
    "two_large_factors_impossible",
    "prime_two",
    "multiple_zero",
    "one_multiple",
    "multiple_refl",
    "multiple_add",
    "multiple_mul_right",
    "multiple_mul_left",
    "multiple_trans",
    "divisor_le_nonzero",
    "divisor_one",
    "multiple_antisymm",
    "factor_difference",
    "divides_remainder",
    "divides_linear_step",
    "not_multiple_pointwise",
    "not_multiple_from_pointwise",
    "is_gcd_zero_right",
    "is_gcd_symm",
    "is_gcd_dvd_left",
    "is_gcd_dvd_right",
    "is_gcd_greatest",
    "is_gcd_of_dvd",
    "is_gcd_unique",
    "is_gcd_euclid_forward",
    "is_gcd_euclid_backward",
    "gcd_exists_up_to",
    "gcd_exists_relational",
    "coprime_symm",
    "coprime_one_right",
    "coprime_one_left",
    "coprime_to_is_gcd_one",
    "is_gcd_one_to_coprime",
    "add_permute_outer",
    "balanced_bezout_euclid_step",
    "gcd_balanced_bezout_exists_up_to",
    "gcd_balanced_bezout_exists",
    "balanced_combination_scale_right",
    "common_divisor_divides_balanced_result",
    "coprime_balanced_bezout",
    "gauss_coprime_cancel",
    "eq_decidable",
    "multiple_decidable_nonzero",
    "multiple_decidable",
    "factor_property_succ",
    "factor_search_up_to",
    "prime_or_composite",
    "prime_nonzero",
    "prime_decidable",
    "factor_nonzero_left",
    "proper_factor_lt",
    "prime_divisor_exists_up_to",
    "prime_divisor_exists",
    "prime_divisor_eq_one_or_self",
    "euclid_prime_dvd_product",
    "mod_eq_refl",
    "mod_eq_symm",
    "dvd_to_mod_zero",
    "add_residue",
    "add_residue_lift",
    "square_decomp",
    "square_residue_lift",
    "square_residue_witness",
)


def test_foundational_extension_is_present_in_dependency_order() -> None:
    specs = [get(name) for name in FOUNDATIONAL_NAMES]

    assert all(spec is not None for spec in specs)
    positions = {spec.name: index for index, spec in enumerate(specs) if spec is not None}
    for spec in specs:
        assert spec is not None
        for dependency in spec.dependencies:
            if dependency in positions:
                assert positions[dependency] < positions[spec.name]


def test_every_foundational_extension_certificate_is_closed_and_live_importable() -> None:
    for name in FOUNDATIONAL_NAMES:
        theorem = replay(name)
        nodes, depth = proof_metrics(theorem.certificate)

        assert check((), theorem.certificate, theorem.formula)
        assert theorem.proof_nodes == nodes
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert depth <= MAX_USE_PROOF_DEPTH


def test_divisibility_and_residue_statements_remain_definitional_expansions() -> None:
    multiple = get("multiple_trans")
    residue = get("square_residue_witness")

    assert multiple is not None and "exists q." in multiple.statement
    assert residue is not None and "exists w." in residue.statement
    assert all(
        token not in multiple.statement + residue.statement
        for token in ("%", "∣", "^")
    )


def test_generated_library_artifacts_and_vault_notes_are_current() -> None:
    for script in (
        "scripts/build_peano_library_snapshot.py",
        "scripts/build_arithmetic_vault.py",
    ):
        completed = subprocess.run(
            [sys.executable, script, "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr


def test_library_snapshot_records_self_contained_cut_representation() -> None:
    artifact_root = ROOT / "artifacts" / "peano-library"
    catalog = json.loads((artifact_root / "catalog-v1.json").read_text())
    metrics = json.loads((artifact_root / "metrics.json").read_text())
    rows = catalog["theorems"]

    assert catalog["schema"] == "peano-library-snapshot-v2"
    assert metrics["schema"] == "peano-library-metrics-v2"
    assert catalog["certificate_representation"] == (
        "python-dataclass-repr-with-cut-v2"
    )
    assert metrics["certificate_representation"] == (
        catalog["certificate_representation"]
    )
    assert all(
        row["certificate_representation"] == catalog["certificate_representation"]
        for row in rows
    )
    assert metrics["total_cut_nodes"] == sum(row["cut_nodes"] for row in rows)
    assert metrics["maximum_cut_nodes"] == max(row["cut_nodes"] for row in rows)
    assert metrics["theorems_with_cut_nodes"] == sum(
        row["cut_nodes"] > 0 for row in rows
    )
    assert metrics["ordered_root_sha256"] == catalog["ordered_root_sha256"]
    assert "self-contained checked Cut node" in catalog["certificate_policy"]
    assert "external theorem environment" in catalog["certificate_policy"]
