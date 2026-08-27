"""Kernel, dependency, boundary, and constructive-witness square-factor audits."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from math import gcd, isqrt

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.coprime_square_factor_candidate import make_coprime_square_factor_candidate_theorems
from peano_lab.library.editions_v25 import ALPHA_SPECS
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "square_lt_strict",
    "square_le_reflect",
    "square_lt_reflect",
    "square_eq_injective",
    "square_zero_root",
    "coprime_square_reduced_factors",
    "coprime_square_product_factors",
    "square_divides_square_reduced_root",
    "square_divides_square_root",
)
EXPECTED_NAMES_SHA256 = "fbb5373544396749946df088999a01975c3e4e4705ecab4def8a24455ad8a5a0"
EXPECTED_BODY_NODES = (37, 41, 41, 53, 11, 332, 219, 86, 111)
EXPECTED_ROOTS = {
    "square_lt_strict": "da5a6dea231614cf22328fc30b1affa4422c5844157a25984dc7f906148a87fb",
    "square_le_reflect": "1f6624dd41ad811c8f158a2cd213e074ab1d98c16474450c876833622bc17810",
    "square_lt_reflect": "45069b2a820cb2a0cdaf6ebcf2369feea84187b3036e1e2574ce73483002dd43",
    "square_eq_injective": "0c01cdf647c9957d5522adf164644cab008de48ff22e5c18478d49c012ceaa60",
    "square_zero_root": "161e0e923b420f18222c04ad83a4b25e58ba921e7b427b68782d0bfa37332ec6",
    "coprime_square_reduced_factors": "d3516505d30287a5e78ff583bc5b6aca807f172fd467666a97025a70b0c72a34",
    "coprime_square_product_factors": "f23a9cdd943c2643d3c3c3b208b34d731715b3e316add8b4a430ec06f8361dca",
    "square_divides_square_reduced_root": "f3b305c075b0ba95da63a45d50ad9936e19ff791c041d4c1685d969867e9e8bf",
    "square_divides_square_root": "b6a82134f1758f33b30be0b733f4910c784805f0ee871400b9e4e0cc4e982b0f",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_coprime_square_factor_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {row.name: row for row in ALPHA_SPECS}


@lru_cache(maxsize=1)
def _receipts():
    return replay_candidate_bodies(_rows(), core=_core())


def _row(name: str) -> TheoremSpec:
    return next(row for row in _rows() if row.name == name)


def _all_rows() -> dict[str, TheoremSpec]:
    return _core() | {row.name: row for row in _rows()}


def test_square_candidates_are_closed_new_and_dependency_ordered() -> None:
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert len(_core()) == 2_080
    assert sum(len(row.dependencies) for row in _rows()) == 48
    assert sum(len(row.script) for row in _rows()) == 408
    available = set(_core())
    for row in _rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert _closed_formula(row.statement)
        assert all(
            command not in {"sorry", "admit"}
            and not command.startswith("use ")
            and "DNE" not in command
            for command in row.script
        )
        available.add(row.name)


def test_all_square_candidate_bodies_pass_the_original_heyting_kernel() -> None:
    receipts = _receipts()
    assert tuple(receipt.name for receipt in receipts) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in receipts) == EXPECTED_BODY_NODES
    assert sum(receipt.proof_nodes for receipt in receipts) == 931
    assert max(receipt.proof_depth for receipt in receipts) == 45


@pytest.mark.parametrize(("name", "expected"), EXPECTED_ROOTS.items())
def test_square_statement_roots_are_exact_and_frozen(name: str, expected: str) -> None:
    assert sha256(_row(name).statement.encode()).hexdigest() == expected


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_square_conclusion_cannot_reuse_an_existing_body(name: str) -> None:
    row = _row(name)
    forged = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_all_rows())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_every_square_body_requires_its_final_command(name: str) -> None:
    row = _row(name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_all_rows())


@pytest.mark.parametrize(
    ("name", "dependency"),
    tuple((row.name, dependency) for row in _rows() for dependency in row.dependencies),
)
def test_each_reported_square_dependency_is_a_real_proof_edge(name: str, dependency: str) -> None:
    row = _row(name)
    forged = replace(row, dependencies=tuple(item for item in row.dependencies if item != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_all_rows())


def test_square_product_root_has_only_coprimality_and_actual_product_premises() -> None:
    target = _closed_formula(_row("coprime_square_product_factors").statement)
    for _ in range(3):
        assert isinstance(target, Forall)
        target = target.body
    assert isinstance(target, Imp)
    target = target.right
    assert isinstance(target, Imp)
    target = target.right
    assert isinstance(target, Exists)
    assert isinstance(target.body, Exists)
    assert isinstance(target.body.body, And)


def test_square_divisibility_root_has_no_nonzero_or_coprimality_assumption() -> None:
    target = _closed_formula(_row("square_divides_square_root").statement)
    for _ in range(2):
        assert isinstance(target, Forall)
        target = target.body
    assert isinstance(target, Imp)
    assert isinstance(target.left, Exists)
    assert isinstance(target.right, Exists)


@pytest.mark.parametrize(("a", "b", "z", "expected"), ((0, 1, 0, (0, 1)), (1, 0, 0, (1, 0)), (1, 1, 1, (1, 1)), (9, 16, 12, (3, 4)), (25, 49, 35, (5, 7))))
def test_constructed_square_product_witnesses_cover_boundaries(a: int, b: int, z: int, expected: tuple[int, int]) -> None:
    assert gcd(a, b) == 1 and a * b == z * z
    if z == 0:
        actual = (0, 1) if a == 0 else (1, 0)
    else:
        common = gcd(a, z)
        actual = (a // common, z // common)
    assert actual == expected
    assert actual[0] * actual[0] == a and actual[1] * actual[1] == b


def test_reduced_gcd_algorithm_constructs_all_small_coprime_square_roots() -> None:
    for a in range(81):
        for b in range(81):
            z = isqrt(a * b)
            if gcd(a, b) != 1 or a * b != z * z:
                continue
            if z == 0:
                u, v = ((0, 1) if a == 0 else (1, 0))
            else:
                common = gcd(a, z)
                u, v = a // common, z // common
            assert (u * u, v * v) == (a, b)


def test_square_divisibility_includes_zero_and_iterated_square_divisors() -> None:
    def divides(divisor: int, value: int) -> bool:
        return value == 0 if divisor == 0 else value % divisor == 0

    for a in range(33):
        for b in range(129):
            assert divides(a * a, b * b) == divides(a, b)
            if divides((a * a) * (a * a), b * b):
                assert divides(a * a, b)


def test_coprimality_premise_is_mathematically_necessary() -> None:
    assert 2 * 2 == 2**2
    assert gcd(2, 2) != 1
    assert isqrt(2) ** 2 != 2
