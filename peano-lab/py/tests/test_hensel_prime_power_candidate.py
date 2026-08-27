"""Bounded, non-admitting original-HA audit of canonical and iterated Hensel."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from math import gcd
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import hensel_prime_power_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v26.json"
PARENT_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
EXPECTED_NAMES = (
    "hensel_mod_add_zero_cancel",
    "hensel_coprime_mod_transport",
    "hensel_canonical_residue_exists",
    "hensel_lift_digit_bound",
    "hensel_canonical_lift_digit_decompose",
    "hensel_lift_linear_identity",
    "hensel_lift_correction_of_root",
    "hensel_canonical_horner_lift_exists_unique",
    "beta_horner_simple_canonical_representative",
    "beta_horner_simple_root_hensel_lift_exists_unique",
    "beta_horner_root_mod_transport",
    "beta_horner_root_mod_weaken",
    "beta_horner_simple_root_at_congruent_point",
    "hensel_canonical_horner_root_exists_unique",
    "hensel_positive_power_factor",
    "beta_horner_prime_power_hensel_lift_exists_unique",
    "beta_horner_simple_lift_preserves_simplicity",
    "beta_horner_hensel_iterated_exists_unique",
    "beta_horner_prime_power_iterated_lifts_exists_unique",
)
EXPECTED_NAMES_SHA256 = "0d83fabda9745836a771e5424e8be9ba1c9ac1d2d82b66d9301a08b54f4342a3"
EXPECTED_MAJOR_STATEMENTS = {
    "beta_horner_simple_root_hensel_lift_exists_unique": "0e2015d8ecd34aa6fb39d8f478e7c20f1dd878a6daf3915d3f1faf86349800a1",
    "beta_horner_prime_power_hensel_lift_exists_unique": "c73ef5c6035e888de9323dabd4f72e349fdf6ef374c4361e22879833e717f7f3",
    "beta_horner_hensel_iterated_exists_unique": "35b9d6f1bd175de921561f5f730c29e183b520e494a723393cbe4dde99d25e03",
    "beta_horner_prime_power_iterated_lifts_exists_unique": "22300cdb65e3bddb402c0e4a95b2bb487823919e489f02ee25fd7d5cb22c279d",
}
EXPECTED_PROOF_NODES = (33, 45, 35, 39, 87, 25, 103, 161, 122, 145, 53, 43, 85, 68, 48, 76, 117, 475, 187)
EXPECTED_PROOF_DEPTHS = (17, 21, 17, 20, 34, 15, 43, 56, 50, 43, 31, 27, 42, 26, 21, 38, 64, 71, 50)


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_hensel_prime_power_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    # Only dependency-curried bodies are checked here.  The immutable JSON
    # supplies exact statements with much less memory than importing every
    # edition; it is not a substitute for dependency-closed kernel/Lean proof.
    raw = PARENT.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    catalog = json.loads(raw)
    assert catalog["theorem_count"] == catalog["checked_use_count"] == 2138
    assert catalog["stable_count"] == 432
    assert all(row["checked_use"] for row in catalog["theorems"])
    return {
        row["name"]: TheoremSpec(
            row["name"], row["statement"], tuple(row["dependencies"]),
            tuple(row["script"]), row["summary"],
        )
        for row in catalog["theorems"]
    }


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_exact_nineteen_theorem_natural_hensel_frontier() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert sum(len(row.dependencies) for row in rows()) == 103
    assert sum(len(row.script) for row in rows()) == 1192


def test_dependency_dag_is_additive_and_never_assumes_a_lift_or_oracle() -> None:
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        assert not any(
            command.startswith(("use ", "admit", "sorry", "ring", "DNE"))
            for command in row.script
        )
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_candidates_are_absent_from_the_immutable_parent(name: str) -> None:
    assert name not in core()


@pytest.mark.parametrize("name,expected", EXPECTED_MAJOR_STATEMENTS.items())
def test_exact_unrestricted_and_iterated_root_statements(name: str, expected: str) -> None:
    row = next(row for row in rows() if row.name == name)
    assert sha256(row.statement.encode()).hexdigest() == expected


def test_all_bodies_are_checked_by_the_unchanged_intuitionistic_kernel() -> None:
    actual = receipts()
    assert tuple(row.name for row in actual) == EXPECTED_NAMES
    assert tuple(row.proof_nodes for row in actual) == EXPECTED_PROOF_NODES
    assert tuple(row.proof_depth for row in actual) == EXPECTED_PROOF_DEPTHS
    assert sum(row.proof_nodes for row in actual) == 1947
    assert max(row.proof_depth for row in actual) == 71


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_candidate_bodies_fail_closed(name: str) -> None:
    row = next(row for row in rows() if row.name == name)
    broken = replace(row, script=("exact forged_hensel_authority",))
    with pytest.raises(CandidateBodyError, match="failed at command"):
        replay_candidate_bodies((broken,), core={**core(), **{row.name: row for row in rows()}})


@pytest.mark.parametrize(
    "helper,arguments",
    (
        (candidate.horner_root_modulo_relation, ("b", "c", "a", "l", "m")),
        (candidate.canonical_horner_lift_relation, ("b", "c", "l", "m", "a", "M", "r")),
        (candidate.simple_horner_root_relation, ("b", "c", "a", "l", "m", "p")),
    ),
)
def test_relations_are_hygienic_exact_first_order_expansions(helper, arguments) -> None:
    first = helper(*arguments, tag="first")
    second = helper(*arguments, tag="second")
    assert parse_formula_in_context(first, list(arguments)) == parse_formula_in_context(second, list(arguments))
    assert not any(word in first for word in ("Horner", "Pow(", "SimpleLift", "oracle"))


@pytest.mark.parametrize("bad", ("", "S", "forall", "false", "0", "x+y", "two words", "hpl_value_test", "hmi_capture", "ff_capture"))
def test_bad_or_capturing_relation_arguments_fail_closed(bad: str) -> None:
    with pytest.raises(candidate.HenselPrimePowerError):
        candidate.horner_root_modulo_relation(bad, "c", "a", "l", "m", tag="test")


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "x+y", "two words"))
def test_invalid_relation_tags_fail_closed(bad: str) -> None:
    with pytest.raises(candidate.HenselPrimePowerError):
        candidate.horner_root_modulo_relation("b", "c", "a", "l", "m", tag=bad)


def test_duplicate_public_arguments_fail_closed() -> None:
    with pytest.raises(candidate.HenselPrimePowerError, match="distinct"):
        candidate.simple_horner_root_relation("b", "c", "a", "l", "m", "m", tag="test")


def test_iteration_is_a_real_ha_induction_with_a_constructed_simple_successor() -> None:
    row = next(row for row in rows() if row.name == "beta_horner_hensel_iterated_exists_unique")
    assert "induction j" in row.script
    assert "beta_horner_simple_lift_preserves_simplicity" in row.dependencies
    assert "beta_horner_simple_root_hensel_lift_exists_unique" in row.dependencies
    assert "pow_successor_decompose" in row.dependencies
    final = rows()[-1]
    assert "pow_exists" in final.dependencies and "pow_add" in final.dependencies


def _evaluate(coefficients: tuple[int, ...], point: int) -> tuple[int, int]:
    value = derivative = 0
    for coefficient in coefficients:
        value, derivative = value * point + coefficient, derivative * point + value
    return value, derivative


@pytest.mark.parametrize("coefficients,p,k,seed", (
    ((1, 1), 2, 1, 1), ((1, 1), 2, 3, 7),
    ((1, 0, 1), 5, 1, 2), ((1, 0, 1), 5, 2, 7),
    ((1, 0, 3), 7, 1, 2), ((1, 0, 3), 7, 2, 37),
))
@pytest.mark.parametrize("steps", range(4))
def test_bounded_arithmetic_models_confirm_unrestricted_input_and_unique_iteration(
    coefficients: tuple[int, ...], p: int, k: int, seed: int, steps: int,
) -> None:
    # Illustrations only: these Python computations do not certify a theorem.
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
        assert point < modulus
        value, derivative = _evaluate(coefficients, point)
        assert value % modulus == 0 and gcd(derivative, p) == 1
    assert modulus == p ** (k + steps)
    assert point % old_modulus == original % old_modulus
    assert [
        candidate for candidate in range(original % old_modulus, modulus, old_modulus)
        if _evaluate(coefficients, candidate)[0] % modulus == 0
    ] == [point]
