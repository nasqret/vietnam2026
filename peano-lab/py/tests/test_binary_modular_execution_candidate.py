"""Original-kernel and adversarial audit of genuinely coded binary histories."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from itertools import repeat

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import binary_modular_execution_candidate as candidate
from peano_lab.library import editions_v21
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "binary_digit_prefix_empty",
    "binary_digit_prefix_restrict",
    "binary_digit_prefix_terminal_bit",
    "binary_execution_initial_state",
    "binary_execution_step_digit",
    "binary_execution_power_zero",
    "binary_execution_even_power_invariant",
    "binary_execution_odd_power_invariant",
    "binary_execution_step_power_invariant",
    "binary_execution_prefix_extend",
    "binary_execution_prefix_exists",
    "binary_modular_execution_exists",
    "binary_modular_execution_empty",
    "binary_modular_execution_successor_decompose",
    "binary_execution_horner_digit_split",
    "binary_modular_execution_power_correct",
    "binary_modular_execution_horner_exists",
    "binary_modular_execution_result_functional",
    "binary_modular_execution_result_exists_unique",
)
EXPECTED_NAMES_SHA256 = "606055de125b92a17c8111f6b041429ad6f74d12ac1175579f2e1e42bdec9087"
EXPECTED_ROOT_STATEMENT_SHA256 = {
    "binary_execution_prefix_exists": (
        "d4021e49514a61208d99766bd84f04b3e272d3c52c151ca8f9dccf1ad04f67eb"
    ),
    "binary_modular_execution_exists": (
        "103c179820815d1978bc1f147e0e7ad6b4289a98b8fb275c72f9ed9a66dd3c7c"
    ),
    "binary_modular_execution_power_correct": (
        "8f924863e885c353860e298956baced60a6a43d56e9d3f3f1c6267deac657321"
    ),
    "binary_modular_execution_horner_exists": (
        "345afe4884b51a608ea42c66b8c56f4ba9e6031a66ab52f2fb679ec5d93138e3"
    ),
    "binary_modular_execution_result_exists_unique": (
        "10df7f702c8ab056bfaeb1d391e7b06d9c69011b5f50bd3fef12e91de53ee9ce"
    ),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_binary_modular_execution_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _receipts():
    core = {item.name: item for item in editions_v21.ALPHA_CHECKED_SPECS}
    return replay_candidate_bodies(_rows(), core=core)


def test_every_new_dependency_curried_proof_passes_the_original_kernel() -> None:
    rows = _rows()
    receipts = _receipts()

    assert len(rows) == len(receipts) == len(EXPECTED_NAMES) == 19
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert sum(len(item.dependencies) for item in rows) == 60
    assert sum(len(item.script) for item in rows) == 794
    assert max(len(item.statement) for item in rows) == 10_093
    assert all(item.proof_nodes > 0 for item in receipts)
    assert all(item.proof_nodes <= 200 and item.proof_depth <= 50 for item in receipts)
    assert all("DNE" not in command for item in rows for command in item.script)
    available = set(editions_v21.ALPHA_EDITION.by_name)
    for item in rows:
        assert item.name not in available
        assert set(item.dependencies) <= available
        assert _closed_formula(item.statement)
        available.add(item.name)


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOT_STATEMENT_SHA256))
def test_exact_checked_trace_horner_power_and_unique_endpoints_are_frozen(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)

    assert sha256(row.statement.encode()).hexdigest() == EXPECTED_ROOT_STATEMENT_SHA256[name]
    assert name not in editions_v21.ALPHA_EDITION.by_name


def test_all_external_prerequisites_are_checked_in_immutable_alpha_v21() -> None:
    local = set(EXPECTED_NAMES)
    external = {
        dependency
        for item in _rows()
        for dependency in item.dependencies
        if dependency not in local
    }

    assert external == {
        "add_eq_zero_right",
        "beta_at_exists",
        "beta_at_self_of_bound",
        "beta_at_unique",
        "beta_horner_eval_empty",
        "beta_horner_eval_exists",
        "beta_horner_eval_successor_decompose",
        "beta_prefix_extend",
        "binary_exponent_doubled_power",
        "binary_exponent_odd_power",
        "binary_modular_exponentiation_result_functional",
        "binary_modular_square_congruence",
        "binary_modular_step_exists",
        "finite_lt_succ_eq_or_lt",
        "le_refl",
        "le_succ",
        "mod_eq_mul",
        "mod_eq_refl",
        "mod_eq_trans",
        "mul_comm",
        "pow_exists",
        "pow_zero",
        "succ_le_succ",
        "succ_ne_zero",
        "two_mul_eq_add_self",
        "zero_le",
    }
    assert all(editions_v21.ALPHA_EDITION.by_name[name].checked_use for name in external)


def test_full_g102_is_not_claimed_without_exponent_digits_or_formal_complexity() -> None:
    names = set(EXPECTED_NAMES)

    assert "binary_modular_execution_power_correct" in names
    assert "binary_modular_execution_result_exists_unique" in names
    assert "binary_modular_exponent_digit_prefix_exists" not in names
    assert "binary_modular_execution_logarithmic_bound" not in names
    assert "binary_modular_execution_bitlength_bound" not in names


@pytest.mark.parametrize(
    ("builder", "arguments"),
    (
        (candidate.binary_digit_prefix, ("b", "c", "l")),
        (candidate.binary_execution_trace, ("b", "c", "a", "m", "l", "u", "v")),
        (candidate.binary_modular_execution, ("b", "c", "a", "m", "l", "r")),
        (candidate.binary_execution_power_invariant, ("b", "c", "a", "m", "l", "r")),
    ),
)
def test_public_definition_helpers_are_hygienic_tag_independent_and_exact(
    builder,
    arguments: tuple[str, ...],
) -> None:
    first, free = parse_formula_with_names(builder(*arguments, tag="one"))
    second, other_free = parse_formula_with_names(builder(*arguments, tag="two"))

    assert first == second
    assert set(free) == set(other_free) == set(arguments)
    for forbidden in ("", "S", "forall", "a+b", "0", "x y"):
        with pytest.raises(ValueError):
            builder(forbidden, *arguments[1:], tag="safe")
        with pytest.raises(ValueError):
            builder(*arguments, tag=forbidden)
    with pytest.raises(ValueError, match="distinct"):
        builder(arguments[0], arguments[0], *arguments[2:], tag="safe")


@pytest.mark.parametrize("base", (0, 1, 2, 3, 7, 31, 257))
@pytest.mark.parametrize("modulus", (2, 3, 5, 17, 257))
@pytest.mark.parametrize("digits", ((), (0,), (1,), (1, 0, 1), (0, 0, 1, 1, 0, 1)))
def test_concrete_execution_really_preserves_every_prefix_power(
    base: int,
    modulus: int,
    digits: tuple[int, ...],
) -> None:
    certificate = candidate.execute_binary_digits(base, modulus, digits)

    assert certificate.exponent == (int("".join(map(str, digits)), 2) if digits else 0)
    assert certificate.result == pow(base, certificate.exponent, modulus)
    assert len(certificate.steps) == len(digits)
    candidate.verify_binary_execution_certificate(certificate)


@pytest.mark.parametrize(
    ("base", "modulus", "digits"),
    (
        (-1, 2, (1,)),
        (True, 2, (1,)),
        (2, 0, (1,)),
        (2, 1, (1,)),
        (2, True, (1,)),
        (2, 3, (2,)),
        (2, 3, (-1,)),
        (2, 3, (True,)),
    ),
)
def test_concrete_invalid_boundaries_fail_closed(base, modulus, digits) -> None:
    with pytest.raises(candidate.BinaryModularExecutionError):
        candidate.execute_binary_digits(base, modulus, digits)


def test_changed_concrete_accumulator_or_terminal_value_fails_closed() -> None:
    actual = candidate.execute_binary_digits(7, 13, (1, 0, 1, 1))
    corrupted = replace(actual.steps[1], result=actual.steps[1].result + 1)

    with pytest.raises(candidate.BinaryModularExecutionError, match="transition"):
        candidate.verify_binary_execution_certificate(
            replace(actual, steps=actual.steps[:1] + (corrupted,) + actual.steps[2:])
        )
    with pytest.raises(candidate.BinaryModularExecutionError, match="terminal"):
        candidate.verify_binary_execution_certificate(replace(actual, result=actual.result + 1))


def test_infinite_binary_digit_iterables_stop_at_the_exact_resource_cap() -> None:
    with pytest.raises(candidate.BinaryModularExecutionError, match="resource cap"):
        candidate.execute_binary_digits(2, 3, repeat(0))


@pytest.mark.parametrize(
    ("base", "modulus"),
    (
        (1 << candidate.MAX_BINARY_EXECUTION_BASE_BITS, 3),
        (2, 1 << candidate.MAX_BINARY_EXECUTION_MODULUS_BITS),
    ),
)
def test_oversized_concrete_naturals_fail_before_any_large_execution(base: int, modulus: int) -> None:
    with pytest.raises(candidate.BinaryModularExecutionError, match="bounded"):
        candidate.execute_binary_digits(base, modulus, ())


def test_forged_formal_proof_body_never_grants_kernel_authority() -> None:
    rows = _rows()
    forged = replace(rows[0], script=("admit",))
    core = {item.name: item for item in editions_v21.ALPHA_CHECKED_SPECS}

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=core)
