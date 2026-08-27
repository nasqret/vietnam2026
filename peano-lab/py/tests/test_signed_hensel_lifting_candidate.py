"""Exact signed-polynomial Hensel statements and bounded original-HA checks."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from math import gcd
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import signed_hensel_lifting_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.hensel_prime_power_candidate import make_hensel_prime_power_candidate_theorems
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v26.json"
PARENT_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
EXPECTED_NAMES = (
    "beta_horner_coefficient_blend_exists",
    "hensel_horner_linear_successor_identity",
    "beta_horner_coefficient_blend_value_derivative",
    "hensel_signed_blend_balance",
    "hensel_signed_blend_mod_iff",
    "hensel_signed_blend_zero_iff",
    "hensel_signed_blend_unit_coprime",
    "beta_signed_horner_blend_root_equivalence",
    "beta_signed_horner_root_value_derivative_exists",
    "hensel_signed_derivative_unit_mod_transport",
    "beta_signed_horner_lift_preserves_simplicity",
    "beta_signed_horner_hensel_iterated_exists_unique",
    "beta_signed_horner_simple_root_hensel_lift_exists_unique",
    "beta_signed_horner_prime_power_hensel_lift_exists_unique",
    "beta_signed_horner_prime_power_iterated_lifts_exists_unique",
    "integer_polynomial_prime_power_hensel_lift_exists_unique",
    "integer_polynomial_prime_power_hensel_iterated_exists_unique",
)
EXPECTED_NAMES_SHA256 = "1b358b5ee001b5d0db41a64f881da235fe7550031645c5509d910791a166b582"
EXPECTED_MAJOR_STATEMENTS = {
    "beta_signed_horner_lift_preserves_simplicity": "6d48181c30d6db991ac413571f8cb319274d8b7abacd40a3addd717bbb304f06",
    "beta_signed_horner_hensel_iterated_exists_unique": "b4489a674e6ec0a8a39eb20d75d29107c54cb1941603ec362cc798629f2d410b",
    "integer_polynomial_prime_power_hensel_lift_exists_unique": "fbc1f6811c164ad5a2a9a52ed6788dd1e9b1e324b2a6cdc057043f318dbba19a",
    "integer_polynomial_prime_power_hensel_iterated_exists_unique": "6e08e64dfacb14e848089a7809fad3560041c600bc923ab665803b288868b28a",
}
EXPECTED_PROOF_NODES = (82, 37, 377, 27, 136, 31, 52, 235, 87, 65, 142, 273, 74, 81, 195, 113, 118)
EXPECTED_PROOF_DEPTHS = (39, 19, 64, 14, 33, 24, 29, 56, 35, 26, 52, 70, 45, 45, 58, 65, 68)


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_signed_hensel_lifting_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    # This small authoring inventory supplies hypothesis statements only.
    # Source-closed original-kernel and compiled-Lean admission are separate.
    raw = PARENT.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    catalog = json.loads(raw)
    assert catalog["theorem_count"] == catalog["checked_use_count"] == 2138
    assert catalog["stable_count"] == 432
    assert all(row["checked_use"] for row in catalog["theorems"])
    result = {
        row["name"]: TheoremSpec(
            row["name"], row["statement"], tuple(row["dependencies"]),
            tuple(row["script"]), row["summary"],
        )
        for row in catalog["theorems"]
    }
    for row in make_hensel_prime_power_candidate_theorems(TheoremSpec):
        assert row.name not in result and set(row.dependencies) <= set(result)
        result[row.name] = row
    return result


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_exact_seventeen_signed_bridge_and_full_hensel_theorems() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert sum(len(row.dependencies) for row in rows()) == 74
    assert sum(len(row.script) for row in rows()) == 1295


def test_real_dependency_dag_has_no_assumed_coefficient_recode_or_lifting_oracle() -> None:
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        _closed_formula(row.statement)
        assert not any(command.startswith(("use ", "admit", "sorry", "ring", "DNE")) for command in row.script)
        available.add(row.name)
    recoding = rows()[0]
    assert set(recoding.dependencies) >= {
        "beta_repeat_exists", "beta_pointwise_mul_prefix_exists", "beta_pointwise_add_prefix_exists",
    }
    linearity = rows()[2]
    assert "induction l" in linearity.script
    iteration = next(row for row in rows() if row.name == "beta_signed_horner_hensel_iterated_exists_unique")
    assert "beta_horner_hensel_iterated_exists_unique" in iteration.dependencies
    assert "beta_signed_horner_blend_root_equivalence" in iteration.dependencies


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_all_signed_rows_are_genuinely_new(name: str) -> None:
    assert name not in core()


@pytest.mark.parametrize("name,expected", EXPECTED_MAJOR_STATEMENTS.items())
def test_full_signed_root_statements_are_exact(name: str, expected: str) -> None:
    row = next(row for row in rows() if row.name == name)
    assert sha256(row.statement.encode()).hexdigest() == expected


def test_all_seventeen_bodies_pass_the_original_intuitionistic_kernel() -> None:
    actual = receipts()
    assert tuple(row.name for row in actual) == EXPECTED_NAMES
    assert tuple(row.proof_nodes for row in actual) == EXPECTED_PROOF_NODES
    assert tuple(row.proof_depth for row in actual) == EXPECTED_PROOF_DEPTHS
    assert sum(row.proof_nodes for row in actual) == 2125
    assert max(row.proof_depth for row in actual) == 70


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_signed_proofs_are_rejected(name: str) -> None:
    row = next(row for row in rows() if row.name == name)
    broken = replace(row, script=("exact invented_signed_hensel_proof",))
    with pytest.raises(CandidateBodyError, match="failed at command"):
        replay_candidate_bodies((broken,), core={**core(), **{row.name: row for row in rows()}})


@pytest.mark.parametrize("helper,arguments", (
    (candidate.horner_coefficient_blend_relation, ("pb", "pc", "nb", "nc", "gb", "gc", "h", "l")),
    (candidate.signed_horner_value_derivative_relation, ("pb", "pc", "nb", "nc", "a", "l", "vp", "dp", "vn", "dn")),
    (candidate.signed_derivative_unit_relation, ("p", "dp", "dn")),
    (candidate.signed_horner_root_relation, ("pb", "pc", "nb", "nc", "a", "l", "m")),
    (candidate.canonical_signed_horner_lift_relation, ("pb", "pc", "nb", "nc", "l", "m", "a", "M", "r")),
    (candidate.signed_simple_horner_root_relation, ("pb", "pc", "nb", "nc", "a", "l", "m", "p")),
))
def test_all_six_signed_definitions_are_hygienic_and_conservative(helper, arguments) -> None:
    first = helper(*arguments, tag="first")
    second = helper(*arguments, tag="second")
    assert parse_formula_in_context(first, list(arguments)) == parse_formula_in_context(second, list(arguments))
    assert not any(
        symbol in first for symbol in ("Horner(", "SimpleLift(", "inverse(", " - ")
    )


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "a+b", "two words", "sph_inverse_unit", "hpl_capture", "ff_capture", "mcp_capture", "fpmp_capture"))
def test_invalid_or_capturing_signed_arguments_fail_closed(bad: str) -> None:
    with pytest.raises(candidate.SignedHenselError):
        candidate.signed_derivative_unit_relation(bad, "dp", "dn", tag="test")


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "x+y", "two words"))
def test_invalid_signed_tags_fail_closed(bad: str) -> None:
    with pytest.raises(candidate.SignedHenselError):
        candidate.signed_derivative_unit_relation("p", "dp", "dn", tag=bad)


def test_duplicate_signed_arguments_fail_closed() -> None:
    with pytest.raises(candidate.SignedHenselError, match="distinct"):
        candidate.signed_derivative_unit_relation("p", "dp", "dp", tag="test")


def _evaluate(coefficients: tuple[int, ...], point: int) -> tuple[int, int]:
    value = derivative = 0
    for coefficient in coefficients:
        value, derivative = value * point + coefficient, derivative * point + value
    return value, derivative


@pytest.mark.parametrize("coefficients,p,k,seed", (
    ((1, 0, -2), 7, 1, 3), ((1, 0, -2), 7, 2, 10),
    ((-1, 0, 2), 7, 1, 3), ((-1, 0, 2), 7, 2, 10),
    ((1, 0, 0, -2), 5, 1, 3), ((1, 0, 0, -2), 5, 2, 3),
    ((-2, 1), 3, 1, 2), ((-2, 1), 3, 2, 5),
    ((1, -1), 2, 1, 1),
))
@pytest.mark.parametrize("steps", range(4))
def test_integer_coefficient_examples_have_unique_lifts_from_unrestricted_inputs(
    coefficients: tuple[int, ...], p: int, k: int, seed: int, steps: int,
) -> None:
    # Numerical regression examples, explicitly not theorem authority.
    old_modulus = p**k
    original = seed + 17 * old_modulus
    value, derivative = _evaluate(coefficients, original)
    assert value % old_modulus == 0 and gcd(derivative, p) == 1
    point, modulus = original % old_modulus, old_modulus
    for _ in range(steps):
        value, derivative = _evaluate(coefficients, point)
        digit = (-(value // modulus) * pow(derivative, -1, p)) % p
        point += modulus * digit
        modulus *= p
        value, derivative = _evaluate(coefficients, point)
        assert point < modulus and value % modulus == 0 and gcd(derivative, p) == 1
    assert modulus == p ** (k + steps)
    assert [
        x for x in range(original % old_modulus, modulus, old_modulus)
        if _evaluate(coefficients, x)[0] % modulus == 0
    ] == [point]


@pytest.mark.parametrize("coefficients", ((-2, 5, -7), (1, 0, -2), (-3, 2), (), (0,)))
@pytest.mark.parametrize("modulus", (1, 2, 6, 27))
@pytest.mark.parametrize("point", (0, 1, 4))
def test_noncanonical_signed_pairs_recode_both_value_and_derivative_exactly(
    coefficients: tuple[int, ...], modulus: int, point: int,
) -> None:
    positive = tuple(max(coefficient, 0) + index + 3 for index, coefficient in enumerate(coefficients))
    negative = tuple(max(-coefficient, 0) + index + 3 for index, coefficient in enumerate(coefficients))
    recoded = tuple(p + (modulus - 1) * n for p, n in zip(positive, negative))
    vp, dp = _evaluate(positive, point)
    vn, dn = _evaluate(negative, point)
    vg, dg = _evaluate(recoded, point)
    assert (vp - vn, dp - dn) == _evaluate(coefficients, point)
    assert vg == vp + (modulus - 1) * vn
    assert dg == dp + (modulus - 1) * dn
    assert vg + vn == vp + modulus * vn
    assert dg + dn == dp + modulus * dn
    for divisor in range(1, modulus + 1):
        if modulus % divisor == 0:
            assert vg % divisor == (vp - vn) % divisor
            assert dg % divisor == (dp - dn) % divisor
            assert (vg % divisor == 0) == ((vp - vn) % divisor == 0)


def test_repeated_roots_are_not_falsely_assigned_simple_root_authority() -> None:
    for prime in (2, 3, 5, 7):
        value, derivative = _evaluate((1, -2, 1), 1)
        assert value == 0 and gcd(derivative, prime) != 1
