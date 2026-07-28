"""Contracts for the general foundational-arithmetic extension."""

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


def test_every_foundational_certificate_is_closed_and_live_importable() -> None:
    for name in FOUNDATIONAL_NAMES:
        theorem = replay(name)
        nodes, depth = proof_metrics(theorem.certificate)

        assert check((), theorem.certificate, theorem.formula)
        assert theorem.proof_nodes == nodes
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert depth <= MAX_USE_PROOF_DEPTH


def test_prime_two_remains_an_expanded_first_order_statement() -> None:
    prime = get("prime_two")

    assert prime is not None
    assert prime.statement == "~(2 = 1) /\\ forall a b. 2 = a * b -> a = 1 \\/ b = 1"
    assert all(token not in prime.statement for token in ("prime", "%", "∣", "^"))


def test_generated_public_library_snapshot_is_current() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/build_peano_library_snapshot.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
