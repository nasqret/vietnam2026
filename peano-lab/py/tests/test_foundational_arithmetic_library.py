"""M20 contracts for the general foundational-arithmetic extension."""

from __future__ import annotations

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
    "add_congr",
    "mul_congr",
    "add_right_cancel",
    "add_left_cancel",
    "zero_le",
    "le_succ_self",
    "le_zero",
    "add_eq_zero_left",
    "mul_ne_zero",
    "two_large_factors_impossible",
    "prime_two",
    "multiple_zero",
    "one_multiple",
    "multiple_refl",
    "multiple_add",
    "multiple_mul_right",
    "multiple_mul_left",
    "multiple_trans",
    "not_multiple_pointwise",
    "not_multiple_from_pointwise",
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
