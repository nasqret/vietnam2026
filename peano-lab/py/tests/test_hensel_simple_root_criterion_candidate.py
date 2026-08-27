"""Exact prime simple-root criterion: no inverse or power supplied by users."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library import hensel_simple_root_criterion_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.hensel_prime_power_candidate import _mod, _power, make_hensel_prime_power_candidate_theorems
from peano_lab.library.signed_hensel_lifting_candidate import (
    _lift, make_signed_hensel_lifting_candidate_theorems,
    signed_derivative_unit_relation, signed_horner_value_derivative_relation,
    signed_simple_horner_root_relation,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


REPO = Path(__file__).resolve().parents[3]
PARENT_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
EXPECTED_NAMES = (
    "hensel_prime_blended_nonzero_derivative_is_unit",
    "hensel_prime_signed_nonzero_derivative_is_unit",
    "hensel_prime_nonsingular_root_is_simple",
    "integer_polynomial_prime_simple_root_lifts_all_positive_powers",
)
EXPECTED_NAMES_SHA256 = "335afa7e23c8259fb2e5bf170b0a5f1d132bacd911d9f73404e48f4d07d02d8b"
EXPECTED_STATEMENTS = {
    "hensel_prime_blended_nonzero_derivative_is_unit": "bf018263a6830d1fdd38d1f33c8a532c13ee229a7c6e6fcce49ebe6d7c11d6fa",
    "hensel_prime_signed_nonzero_derivative_is_unit": "87891b4b911500f2331988d2bc0d98ec188a6ce554d7fa1c8fafce44a51161e5",
    "hensel_prime_nonsingular_root_is_simple": "b6ce01164048acad568d8748760326a4d3fbf2cbb1b63715924924c887f8f9e9",
    "integer_polynomial_prime_simple_root_lifts_all_positive_powers": "158b28822061f364d34a4badf84986d5f02301b58c555b1e67ec758c786709e8",
}
POLY = ("pb", "pc", "nb", "nc")
RELATIONS = (
    (candidate.signed_derivative_nonzero_relation, ("p", "dp", "dn")),
    (candidate.signed_nonsingular_horner_root_relation, (*POLY, "a", "l", "m", "p")),
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_hensel_simple_root_criterion_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _frozen_hensel_rows() -> tuple[TheoremSpec, ...]:
    natural = make_hensel_prime_power_candidate_theorems(TheoremSpec)
    signed = make_signed_hensel_lifting_candidate_theorems(TheoremSpec)
    assert len(natural) == 19 and len(signed) == 17
    assert sha256("\n".join(row.name for row in natural).encode()).hexdigest() == "0d83fabda9745836a771e5424e8be9ba1c9ac1d2d82b66d9301a08b54f4342a3"
    assert sha256("\n".join(row.name for row in signed).encode()).hexdigest() == "1b358b5ee001b5d0db41a64f881da235fe7550031645c5509d910791a166b582"
    return natural + signed


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    raw = (REPO / "artifacts/peano-library/alpha/catalog-v26.json").read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    parent = {
        row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row.get("summary", ""))
        for row in json.loads(raw)["theorems"]
    }
    assert len(parent) == 2_138
    for row in _frozen_hensel_rows():
        assert row.name not in parent
        assert set(row.dependencies) <= set(parent)
        parent[row.name] = row
    return parent


@lru_cache(maxsize=1)
def _all() -> dict[str, TheoremSpec]:
    return _core() | {row.name: row for row in _rows()}


@lru_cache(maxsize=1)
def _receipts():
    return tuple(replay_candidate_bodies((row,), core=_all())[0] for row in _rows())


def test_exact_additive_dependency_ordered_inventory() -> None:
    assert _rows() == candidate.make_hensel_simple_root_criterion_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert sum(len(row.dependencies) for row in _rows()) == 20
    assert sum(len(row.script) for row in _rows()) == 205
    assert max(len(row.statement) for row in _rows()) == 44_068
    available = set(_core())
    for row in _rows():
        assert row.name not in available and set(row.dependencies) <= available
        formula, free = parse_formula_with_names(row.statement)
        assert not free and formula == _closed_formula(row.statement)
        assert all(not any(token in command for token in ("DNE", "sorry", "admit", "oracle", "axiom")) and not command.startswith("use ") for command in row.script)
        available.add(row.name)


def test_all_four_bodies_pass_original_heyting_kernel() -> None:
    assert tuple(receipt.name for receipt in _receipts()) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in _receipts()) == (106, 33, 60, 151)
    assert sum(receipt.proof_nodes for receipt in _receipts()) == 350
    assert max(receipt.proof_depth for receipt in _receipts()) == 38


@pytest.mark.parametrize(("name", "digest"), EXPECTED_STATEMENTS.items())
def test_statement_hashes(name: str, digest: str) -> None:
    assert sha256(_all()[name].statement.encode()).hexdigest() == digest


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_conclusion_mutation_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=f"({row.statement}) /\\ false"),), core=_all())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_body_mutation_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_all())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_removed_dependency_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, dependencies=row.dependencies[:-1]),), core=_all())


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_definitions_are_hygienic_alpha_invariant_native_relations(builder, arguments) -> None:
    first, free = parse_formula_with_names(builder(*arguments, tag="first"))
    second, other = parse_formula_with_names(builder(*arguments, tag="second"))
    assert first == second and set(free) == set(other) == set(arguments)
    assert all(token not in builder(*arguments, tag="audit") for token in ("Inverse", "Unit", "Root", "Horner", "ModEq"))


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_unsafe_arguments_rejected(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError):
        builder(fragment, *arguments[1:], tag="safe")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_unsafe_tags_rejected(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError):
        builder(*arguments, tag=fragment)


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("hsc_vp_capture", "sph_inverse_capture", "hpl_gap_capture", "ff_u_capture", "fs_q_capture", "ph_i_capture", "hd_i_capture", "pa_i_capture", "pth_i_capture", "hgcrt_i_capture", "hmi_divisor_capture", "mcp_i_capture", "fpmp_i_capture"))
def test_binder_capture_rejected(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError, match="capture"):
        builder(fragment, *arguments[1:], tag="capture")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_duplicate_argument_rejected(builder, arguments) -> None:
    with pytest.raises(ValueError, match="distinct"):
        builder(arguments[1], *arguments[1:], tag="safe")


def test_derivative_condition_is_merely_nonzero_balanced_signed_residue() -> None:
    expected = f"~({_mod('p','dp','dn',tag='audit_derivative')})"
    actual = candidate.signed_derivative_nonzero_relation("p", "dp", "dn", tag="audit_nonzero")
    assert _closed_formula("forall p dp dn. " + actual) == _closed_formula("forall p dp dn. " + expected)


def test_nonsingular_root_packages_actual_value_and_derivative_without_an_inverse() -> None:
    expected = (
        "exists vp dp vn dn. ((" + signed_horner_value_derivative_relation(*POLY, "a", "l", "vp", "dp", "vn", "dn", tag="audit_pair")
        + ") /\\ ((" + _mod("m", "vp", "vn", tag="audit_root") + ") /\\ (~(" + _mod("p", "dp", "dn", tag="audit_nonzero") + "))))"
    )
    actual = candidate.signed_nonsingular_horner_root_relation(*POLY, "a", "l", "m", "p", tag="audit_nonsingular")
    header = f"forall {' '.join((*POLY,'a','l','m','p'))}. "
    assert _closed_formula(header + actual) == _closed_formula(header + expected)


def test_prime_nonzero_derivative_really_constructs_the_unchanged_bounded_unit() -> None:
    expected = (
        f"forall p dp dn. ({prime('p',tag='audit_prime')}) -> (~({_mod('p','dp','dn',tag='audit_nonzero')})) -> "
        f"({signed_derivative_unit_relation('p','dp','dn',tag='audit_unit')})"
    )
    assert _closed_formula(_all()[EXPECTED_NAMES[1]].statement) == _closed_formula(expected)


def test_root_adapter_keeps_the_historical_unit_definition_unchanged() -> None:
    expected = (
        f"forall {' '.join((*POLY,'a','l','m','p'))}. ({prime('p',tag='audit_prime')}) -> "
        f"({candidate.signed_nonsingular_horner_root_relation(*POLY,'a','l','m','p',tag='audit_new')}) -> "
        f"({signed_simple_horner_root_relation(*POLY,'a','l','m','p',tag='audit_old')})"
    )
    assert _closed_formula(_all()[EXPECTED_NAMES[2]].statement) == _closed_formula(expected)


def test_exact_full_root_has_no_supplied_inverse_power_correction_or_trace() -> None:
    expected = (
        f"forall {' '.join((*POLY,'a','l','p','k'))}. ({prime('p',tag='audit_prime')}) -> ~(k=0) -> "
        f"({candidate._nonsingular(*POLY,'a','l','p','p',tag='audit_initial_root')}) -> "
        f"exists M. (({_power('p','k','M',tag='audit_actual_power')}) /\\ exists r. "
        f"(({_lift(*POLY,'l','p','a','M','r',tag='audit_chosen')}) /\\ forall z. "
        f"({_lift(*POLY,'l','p','a','M','z',tag='audit_other')}) -> z=r))"
    )
    actual = _closed_formula(_all()[EXPECTED_NAMES[3]].statement)
    assert actual == _closed_formula(expected)
    for _ in range(8):
        assert isinstance(actual, Forall)
        actual = actual.body
    for _ in range(3):
        assert isinstance(actual, Imp)
        actual = actual.right
    assert isinstance(actual, Exists) and isinstance(actual.body, And)
    root = actual.body.right
    assert isinstance(root, Exists) and isinstance(root.body, And)
    assert isinstance(root.body.right, Forall)


def test_full_endpoint_uses_constructive_power_and_derivative_constructors() -> None:
    row = _all()[EXPECTED_NAMES[3]]
    assert {"pow_exists", "pow_one", "nonzero_is_succ", "hensel_prime_nonsingular_root_is_simple", "integer_polynomial_prime_power_hensel_iterated_exists_unique"} <= set(row.dependencies)
    inverse = _all()[EXPECTED_NAMES[0]]
    assert {"coprime_bounded_mod_inverse", "prime_not_divides_coprime", "hensel_signed_blend_mod_iff", "hensel_signed_blend_zero_iff"} <= set(inverse.dependencies)


def _horner_pair(coefficients: tuple[int, ...], point: int) -> tuple[int, int]:
    value, derivative = 0, 0
    for coefficient in coefficients:
        value, derivative = value * point + coefficient, derivative * point + value
    return value, derivative


def _signed_coefficients(coefficients: tuple[int, ...], offset: int):
    return (
        tuple(max(c, 0) + offset + i for i, c in enumerate(coefficients)),
        tuple(max(-c, 0) + offset + i for i, c in enumerate(coefficients)),
    )


def test_nonzero_prime_derivative_inverse_examples_include_negative_components() -> None:
    for p in (2, 3, 5, 7, 11):
        for dp in range(2 * p + 1):
            for dn in range(2 * p + 1):
                if (dp - dn) % p == 0:
                    continue
                blended = dp + (p - 1) * dn
                inverse = pow(blended, -1, p)
                assert 0 <= inverse < p
                assert (dp * inverse - (1 + dn * inverse)) % p == 0


@pytest.mark.parametrize("coefficients", ((1, -1), (1, 0, -2), (-1, 0, 2), (-3, 2), (1, 0, 0, -2)))
def test_signed_simple_roots_have_unique_lifts_at_every_small_positive_precision(coefficients) -> None:
    tested = 0
    positive, negative = _signed_coefficients(coefficients, 4)
    for p in (2, 3, 5, 7):
        for a0 in range(p):
            value, derivative = _horner_pair(coefficients, a0)
            if value % p or not derivative % p:
                continue
            a = a0 + 2 * p  # An input representative larger than p is permitted.
            vp, dp = _horner_pair(positive, a)
            vn, dn = _horner_pair(negative, a)
            assert (vp-vn, dp-dn) == _horner_pair(coefficients, a)
            assert (vp-vn) % p == 0 and (dp-dn) % p != 0
            for k in (1, 2, 3):
                modulus = p**k
                roots = [r for r in range(modulus) if (r-a) % p == 0 and _horner_pair(coefficients,r)[0] % modulus == 0]
                assert len(roots) == 1
                r, previous = a % p, p
                for _ in range(1, k):
                    current, slope = _horner_pair(coefficients, r)
                    assert current % previous == 0
                    correction = (-(current // previous) * pow(slope, -1, p)) % p
                    r += previous * correction
                    previous *= p
                assert roots == [r] and 0 <= r < modulus and (r-a) % p == 0
                tested += 1
    assert tested > 0


def test_prime_and_nonsingularity_hypotheses_are_essential_in_examples() -> None:
    assert 2 % 4 != 0 and not any((2*u-1) % 4 == 0 for u in range(4))
    singular_lifts = [r for r in range(25) if r % 5 == 0 and r*r % 25 == 0]
    assert singular_lifts == [0, 5, 10, 15, 20]
    assert not [r for r in range(1) if (r-1) % 5 == 0]  # k=0 cannot retain every p-residue class.
