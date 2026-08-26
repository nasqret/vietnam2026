"""Original-kernel, hygienic, and adversarial audit of complete binary G102."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import binary_digit_extraction_candidate as candidate
from peano_lab.library import editions_v22
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "binary_digit_code_recode_exists",
    "binary_digit_prefix_recode",
    "binary_horner_prefix_recode",
    "binary_digit_prefix_append",
    "binary_digit_horner_append",
    "binary_digit_half_below_double",
    "binary_digit_bounded_prefix_exists",
    "binary_length_upper_power_bound",
    "binary_exponent_digit_prefix_at_length",
    "binary_exponent_digit_prefix_exists",
    "binary_exponent_digit_prefix_value_functional",
    "binary_canonical_exponent_length_functional",
    "binary_digit_prefix_all_bits",
    "binary_digit_prefix_bit_count_exists",
    "binary_three_times_cost_normalization",
    "binary_digit_operation_count_exists",
    "binary_digit_operation_count_functional",
    "binary_digit_operation_count_bound",
    "binary_modular_exponent_coded_execution_power_correct",
    "binary_modular_exponent_coded_execution_exists",
    "binary_modular_exponent_coded_execution_result_functional",
    "binary_modular_exponent_coded_execution_exists_unique",
    "binary_modular_execution_bitlength_bound",
    "binary_modular_execution_logarithmic_bound",
)
EXPECTED_NAMES_SHA256 = "dfca399b15ba72e14afa2beee595acd8dbb925030f6b53e16c2c0bc075412253"
EXPECTED_ROOT_STATEMENT_SHA256 = {
    "binary_digit_bounded_prefix_exists": (
        "70d6bec43aaf800d0915f268b3d90c60274e28a20bb5d7e46dbf384c41df637b"
    ),
    "binary_exponent_digit_prefix_exists": (
        "32bdeec52d9746fee467a709ae2315e25800e4f0603fe465c14fa84f03452f0d"
    ),
    "binary_digit_operation_count_bound": (
        "bfa38c8809cf8abe8209ff27e2e136972707db9889de8be549d90f01eb3ffa56"
    ),
    "binary_modular_exponent_coded_execution_exists": (
        "d2c7995fed0f8265109081af92313d7a0ff7bd740a238c578b2a06522f016a3a"
    ),
    "binary_modular_exponent_coded_execution_exists_unique": (
        "3b7d9957844c9972de1f2a4cea63b355134d634dab471fc1ad31a89b3e509bfc"
    ),
    "binary_modular_execution_bitlength_bound": (
        "f26f699912b4f5feb522f8afe77676b881747f5a997fa169d27e924c6f7acb73"
    ),
    "binary_modular_execution_logarithmic_bound": (
        "3ac6949afecc26acc6e5fb9d8d9041be9a9f2b8120dcbc918b8e771a7a1bd27d"
    ),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_binary_digit_extraction_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v22.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def _receipts():
    return replay_candidate_bodies(_rows(), core=_core())


def test_every_canonical_digit_and_complete_logarithmic_proof_passes_the_original_kernel() -> None:
    rows = _rows()
    receipts = _receipts()

    assert len(rows) == len(receipts) == len(EXPECTED_NAMES) == 24
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert sum(len(item.dependencies) for item in rows) == 63
    assert sum(len(item.script) for item in rows) == 812
    assert max(len(item.statement) for item in rows) == 49_062
    assert all(0 < item.proof_nodes <= 200 and item.proof_depth <= 50 for item in receipts)
    assert all("DNE" not in command for item in rows for command in item.script)
    available = set(_core())
    for item in rows:
        assert item.name not in available
        assert set(item.dependencies) <= available
        assert _closed_formula(item.statement)
        available.add(item.name)


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOT_STATEMENT_SHA256))
def test_actual_arbitrary_exponent_execution_and_bitcount_cost_roots_are_immutable(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)

    assert sha256(row.statement.encode()).hexdigest() == EXPECTED_ROOT_STATEMENT_SHA256[name]
    assert name not in _core()


def test_all_external_prerequisites_are_independently_checked_in_immutable_alpha_v22() -> None:
    local = set(EXPECTED_NAMES)
    external = {
        dependency
        for item in _rows()
        for dependency in item.dependencies
        if dependency not in local
    }

    assert external <= set(_core())
    assert {
        "binary_length_exists",
        "binary_length_functional",
        "binary_power_two_exists",
        "binary_modular_execution_exists",
        "binary_modular_execution_power_correct",
        "bit_count_exists",
        "bit_count_bounded",
        "beta_prefix_extend",
    } <= external
    assert all(editions_v22.ALPHA_EDITION.by_name[name].checked_use for name in external)


def test_full_g102_has_exact_canonical_digits_actual_execution_and_measured_bound() -> None:
    rows = {item.name: item for item in _rows()}
    final = rows[candidate.BINARY_MODULAR_EXECUTION_LOGARITHMIC_BOUND]

    assert candidate.BINARY_EXPONENT_DIGIT_PREFIX_EXISTS in rows
    assert candidate.BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS in rows
    assert candidate.BINARY_DIGIT_OPERATION_COUNT_BOUND in rows
    assert candidate.BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND in final.dependencies
    assert "exists l b c r operations" in final.statement
    assert "gap + operations = 3 * l + 2" in final.statement
    assert "operations = (2 + (l + l)) +" in final.statement


@pytest.mark.parametrize(
    ("builder", "arguments"),
    (
        (candidate.binary_exponent_digit_code, ("n", "l", "b", "c")),
        (candidate.binary_canonical_exponent_digit_code, ("n", "l", "b", "c")),
        (candidate.binary_execution_operation_count, ("b", "c", "l", "s")),
        (candidate.binary_complete_modular_execution, ("n", "a", "m", "l", "b", "c", "r")),
    ),
)
def test_public_digit_code_and_exact_cost_relations_are_hygienic_and_tag_independent(
    builder,
    arguments: tuple[str, ...],
) -> None:
    first, free = parse_formula_with_names(builder(*arguments, tag="first"))
    second, other = parse_formula_with_names(builder(*arguments, tag="second"))

    assert first == second
    assert set(free) == set(other) == set(arguments)
    for forbidden in ("", "S", "forall", "n+m", "0", "x y"):
        with pytest.raises(candidate.BinaryDigitExtractionError):
            builder(forbidden, *arguments[1:], tag="safe")
        with pytest.raises(candidate.BinaryDigitExtractionError):
            builder(*arguments, tag=forbidden)
    for captured in ("ff_h_capture", "pa_value"):
        with pytest.raises(candidate.BinaryDigitExtractionError, match="captures"):
            builder(captured, *arguments[1:], tag="safe")
    with pytest.raises(candidate.BinaryDigitExtractionError, match="distinct"):
        builder(arguments[0], arguments[0], *arguments[2:], tag="safe")


@pytest.mark.parametrize("name", (
    "binary_digit_bounded_prefix_exists",
    "binary_exponent_digit_prefix_exists",
    "binary_modular_exponent_coded_execution_exists",
    "binary_modular_execution_logarithmic_bound",
))
def test_false_canonical_digit_or_logarithmic_conclusions_are_rejected(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    forged = replace(row, statement="0 = 1")
    core = {**_core(), **{item.name: item for item in _rows() if item.name != name}}

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=core)


@pytest.mark.parametrize("name", (
    "binary_digit_bounded_prefix_exists",
    "binary_exponent_digit_prefix_exists",
    "binary_modular_exponent_coded_execution_exists",
    "binary_modular_execution_logarithmic_bound",
))
def test_truncated_canonical_digit_or_logarithmic_proofs_are_rejected(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    forged = replace(row, script=row.script[:-1])
    core = {**_core(), **{item.name: item for item in _rows() if item.name != name}}

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=core)


@pytest.mark.parametrize("exponent", (0, 1, 2, 3, 7, 8, 31, 32, 255, 256, 65535))
def test_actual_canonical_msb_first_digits_are_encoded_by_genuine_beta_remainders(exponent: int) -> None:
    encoded = candidate.encode_canonical_binary_digits(exponent)

    assert encoded.length == max(1, exponent.bit_length())
    assert encoded.digits == tuple(map(int, bin(exponent)[2:]))
    assert all(
        encoded.code % (1 + (index + 1) * encoded.scale) == digit
        for index, digit in enumerate(encoded.digits)
    )
    candidate.verify_canonical_binary_digit_code(encoded)


@pytest.mark.parametrize("base", (0, 1, 2, 7, 31))
@pytest.mark.parametrize("modulus", (2, 3, 5, 17, 257))
@pytest.mark.parametrize("exponent", (0, 1, 2, 3, 7, 8, 31, 32, 255, 256))
def test_canonical_execution_computes_every_power_with_exact_population_cost(
    base: int,
    modulus: int,
    exponent: int,
) -> None:
    actual = candidate.execute_canonical_binary_modular_exponentiation(base, exponent, modulus)

    assert actual.bit_length == max(1, exponent.bit_length())
    assert actual.digits == tuple(map(int, bin(exponent)[2:]))
    assert actual.one_count == exponent.bit_count()
    assert actual.operation_count == 2 + 2 * actual.bit_length + exponent.bit_count()
    assert actual.operation_count <= 3 * actual.bit_length + 2
    assert len(actual.execution.steps) == actual.bit_length
    assert actual.result == pow(base, exponent, modulus)
    candidate.verify_canonical_binary_execution(actual)


@pytest.mark.parametrize("exponent", (-1, True, False, 1.0, "1", None))
def test_non_natural_exponents_are_rejected_before_digit_allocation(exponent) -> None:
    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.encode_canonical_binary_digits(exponent)
    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.execute_canonical_binary_modular_exponentiation(2, exponent, 3)


def test_oversized_exponents_and_beta_prefixes_fail_closed_at_exact_caps() -> None:
    with pytest.raises(candidate.BinaryDigitExtractionError, match="bit cap"):
        candidate.execute_canonical_binary_modular_exponentiation(
            2, 1 << candidate.MAX_BINARY_DIGIT_EXTRACTION_BITS, 3
        )
    with pytest.raises(candidate.BinaryDigitExtractionError, match="entry cap"):
        candidate.encode_canonical_binary_digits(1 << candidate.MAX_BINARY_DIGIT_BETA_ENTRIES)


@pytest.mark.parametrize("field", ("exponent", "length", "code", "scale"))
def test_bool_or_changed_beta_metadata_never_decodes_as_an_accepted_certificate(field: str) -> None:
    encoded = candidate.encode_canonical_binary_digits(13)

    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.verify_canonical_binary_digit_code(replace(encoded, **{field: True}))
    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.verify_canonical_binary_digit_code(
            replace(encoded, **{field: getattr(encoded, field) + 1})
        )


def test_forged_or_reordered_binary_digits_fail_closed() -> None:
    encoded = candidate.encode_canonical_binary_digits(13)

    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.verify_canonical_binary_digit_code(replace(encoded, digits=(1, 1, 0, 0)))
    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.verify_canonical_binary_digit_code(replace(encoded, digits=(1, 2, 0, 1)))


@pytest.mark.parametrize("field", ("base", "exponent", "modulus", "bit_length", "one_count", "operation_count"))
def test_forged_or_boolean_execution_metadata_fails_closed(field: str) -> None:
    actual = candidate.execute_canonical_binary_modular_exponentiation(7, 13, 17)

    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.verify_canonical_binary_execution(replace(actual, **{field: True}))
    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.verify_canonical_binary_execution(
            replace(actual, **{field: getattr(actual, field) + 1})
        )


def test_forged_execution_trace_result_or_digit_order_fails_closed() -> None:
    actual = candidate.execute_canonical_binary_modular_exponentiation(7, 13, 17)
    changed_step = replace(actual.execution.steps[1], result=actual.execution.steps[1].result + 1)
    changed_execution = replace(
        actual.execution,
        steps=actual.execution.steps[:1] + (changed_step,) + actual.execution.steps[2:],
    )

    with pytest.raises(candidate.BinaryDigitExtractionError, match="transition"):
        candidate.verify_canonical_binary_execution(replace(actual, execution=changed_execution))
    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.verify_canonical_binary_execution(
            replace(actual, execution=replace(actual.execution, result=actual.result + 1))
        )
    with pytest.raises(candidate.BinaryDigitExtractionError):
        candidate.verify_canonical_binary_execution(replace(actual, digits=tuple(reversed(actual.digits))))


def test_zero_uses_exactly_one_real_zero_transition_and_four_operations() -> None:
    zero = candidate.execute_canonical_binary_modular_exponentiation(7, 0, 17)

    assert zero.digits == (0,)
    assert zero.bit_length == 1
    assert zero.operation_count == 4
    assert len(zero.execution.steps) == 1
    assert zero.result == 1
