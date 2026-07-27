"""Regression checks for the consecutive-product parity size experiment."""

from pathlib import Path
from runpy import run_path

from peano_lab.engine.proof_reduction import normalise_cuts
from peano_lab.engine.state import proof_size
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import parse_formula


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = run_path(str(ROOT / "scripts" / "minimize_parity_certificate.py"))
EXPECTED_NODES = EXPERIMENT["EXPECTED_NODES"]
build_experiment = EXPERIMENT["build_experiment"]


def test_optimized_parity_certificate_is_small_cut_normal_and_checked():
    target, certificate = build_experiment()

    assert target == parse_formula("forall n. exists x. n * (n + 1) = 2 * x")
    assert proof_size(certificate) == EXPECTED_NODES == 180
    assert normalise_cuts(certificate) == certificate
    assert check((), certificate, target)


def test_optimized_parity_certificate_does_not_prove_a_mutated_goal():
    _, certificate = build_experiment()
    mutated = parse_formula("forall n. exists x. n * (n + 1) = 2 * x + 1")

    assert not check((), certificate, mutated)
