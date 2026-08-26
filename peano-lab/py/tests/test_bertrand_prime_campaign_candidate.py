"""Original-kernel audit of the first two unblocked grand-campaign prime goals."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from math import comb, factorial, isqrt

import pytest

from peano_lab.kernel.formulas import (
    And,
    Exists,
    Forall,
    Imp,
    parse_formula,
    parse_formula_with_names,
)
from peano_lab.library import bertrand_prime_campaign_candidate as candidate
from peano_lab.library import editions_v19
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "bertrand_window_prime_divides_central_binom",
    "bertrand_window_prime_square_exceeds_double",
    "bertrand_window_central_valuation_at_most_one",
    "bertrand_window_central_valuation_nonzero",
    "bertrand_window_central_valuation_equals_one",
    "bertrand_window_central_valuation_one",
    "central_binom_prime_divisor_multiplicity_one_exists",
    "bertrand_chain_singleton_code_exists",
    "bertrand_chain_singleton_exists",
    "bertrand_chain_successor_preserves_guard",
    "bertrand_chain_prefix_extend",
    "bertrand_chain_prefix_terminal_exists",
    "iterated_bertrand_prime_chain_exists",
)
EXPECTED_ORDERED_NAMES_SHA256 = (
    "184855ae530d73c6f6067b88c306fe6b64fc471b659cecf66eaeaea20ba62021"
)
EXPECTED_PROOF_NODES = (
    52, 54, 56, 50, 55, 147, 47, 33, 25, 38, 116, 76, 18
)
EXPECTED_PROOF_DEPTHS = (
    27, 20, 27, 24, 28, 30, 22, 19, 17, 22, 35, 25, 11
)
EXPECTED_COMMAND_COUNTS = (
    22, 42, 45, 39, 41, 46, 32, 11, 19, 12, 83, 55, 15
)
EXPECTED_STATEMENT_SHA256 = {
    "bertrand_window_prime_divides_central_binom": (
        "5ee617a44a4917c20bee6233f3860df5d36802aa7d0e8d9ed61f1690da568733"
    ),
    "bertrand_window_prime_square_exceeds_double": (
        "c7c2dbe25a1feb6bee1f21441be4103ed867f1dcb03bd40231224004a94be31f"
    ),
    "bertrand_window_central_valuation_at_most_one": (
        "ca0713cb17701293d189e83d62137a5ad3e247f1d8bf11380e33247aed1d310c"
    ),
    "bertrand_window_central_valuation_nonzero": (
        "748126be2a84e2605ea43a130450fd6625012447e019f89e67c9421b09f0a1ab"
    ),
    "bertrand_window_central_valuation_equals_one": (
        "6a0819c1c26aee9f92e2f3f223e3445f938904bf451fa4e23e1f3f8becdd42d0"
    ),
    "bertrand_window_central_valuation_one": (
        "69c9b368307c2edf3ce29ec9bc619cbb2fca7847bedc9acb178fefb4bc659088"
    ),
    "central_binom_prime_divisor_multiplicity_one_exists": (
        "d0899600b713e85d0cb20997ada171ce02b6a6e8316364ed4ab603389724f5a8"
    ),
    "bertrand_chain_singleton_code_exists": (
        "81e0be0b2707447900b42b930c24dd9f44dbc2dc32b141bcf5fe0dbda9130dcd"
    ),
    "bertrand_chain_singleton_exists": (
        "682762e683e2950b4b98f4391d14aad487ec59ec83315abdf6c9e9bdbd432076"
    ),
    "bertrand_chain_successor_preserves_guard": (
        "9e78d2c0b4e9b69875cd1e053c9c73f396565cc860c0143221f874974079d3aa"
    ),
    "bertrand_chain_prefix_extend": (
        "ffeb06827277c3fd2760f8efc7e03deee11d0f845bb6977bb030057b39b97a7b"
    ),
    "bertrand_chain_prefix_terminal_exists": (
        "ffaa8f19c20df9168590a4e7d0f57a04163ca390f84f59aa226687403fe9b976"
    ),
    "iterated_bertrand_prime_chain_exists": (
        "02c52d46368ec2320c8d316b41d37ef7c1dbb5de32dbd15247325a17382650d2"
    ),
}
EXPECTED_CORE_BOUNDARY = {
    "add_eq_zero_right",
    "bertrand_strict",
    "beta_prefix_extend",
    "central_binom_exists",
    "central_binom_positive",
    "central_binom_prime_square_tail_valuation_le_one",
    "choose_prime_divides_between",
    "finite_lt_succ_eq_or_lt",
    "le_antisymm",
    "le_refl",
    "lt_of_lt_of_le",
    "lt_to_le",
    "lt_trans",
    "mul_comm",
    "mul_le_mul_right",
    "mul_lt_mul_right_nonzero",
    "one_le_of_ne_zero",
    "pow_exists",
    "pow_two",
    "prime_divisor_power_valuation_nonzero",
    "prime_power_valuation_exists",
    "prime_two_le",
    "succ_le_succ",
    "two_mul_eq_add_self",
    "zero_le",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_bertrand_prime_campaign_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {row.name: row for row in editions_v19.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def _receipts():
    return replay_candidate_bodies(_rows(), core=_core())


def _is_prime(value: int) -> bool:
    return value >= 2 and all(
        value % divisor for divisor in range(2, isqrt(value) + 1)
    )


def _valuation(base: int, value: int) -> int:
    exponent = 0
    while value % base == 0:
        value //= base
        exponent += 1
    return exponent


def _least_strict_bertrand_prime(value: int) -> int:
    return next(candidate for candidate in range(value + 1, 2 * value) if _is_prime(candidate))


def _beta_encode(values: tuple[int, ...]) -> tuple[int, int]:
    """Construct an actual Gödel-beta pair with witnessed pairwise CRT moduli."""

    assert values
    scale = factorial(len(values)) * (max(values) + 1)
    code = 0
    prefix_modulus = 1
    for index, value in enumerate(values):
        modulus = 1 + (index + 1) * scale
        assert value < modulus
        correction = ((value - code) * pow(prefix_modulus, -1, modulus)) % modulus
        code += prefix_modulus * correction
        prefix_modulus *= modulus
    assert all(code % (1 + (index + 1) * scale) == value for index, value in enumerate(values))
    return code, scale


def test_thirteen_candidate_rows_are_deterministic_closed_and_layer_ordered() -> None:
    rows = _rows()

    assert len(rows) == 13
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert rows == candidate.make_bertrand_prime_campaign_candidate_theorems(TheoremSpec)
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        EXPECTED_ORDERED_NAMES_SHA256
    )
    assert sum(len(row.dependencies) for row in rows) == 40
    assert sum(len(row.script) for row in rows) == 462
    assert {
        row.name: sha256(row.statement.encode()).hexdigest() for row in rows
    } == EXPECTED_STATEMENT_SHA256

    prior: set[str] = set()
    for row in rows:
        parsed, free = parse_formula_with_names(row.statement)
        assert not free
        assert parsed == _closed_formula(row.statement)
        assert set(row.dependencies) <= set(_core()) | prior
        assert row.name not in editions_v19.ALPHA_EDITION.by_name
        assert not any("DNE" in line or line.startswith("use ") for line in row.script)
        prior.add(row.name)


def test_all_thirteen_bodies_are_independently_accepted_by_original_kernel() -> None:
    receipts = _receipts()

    assert tuple(row.name for row in receipts) == EXPECTED_NAMES
    assert tuple(row.proof_nodes for row in receipts) == EXPECTED_PROOF_NODES
    assert tuple(row.proof_depth for row in receipts) == EXPECTED_PROOF_DEPTHS
    assert tuple(row.command_count for row in receipts) == EXPECTED_COMMAND_COUNTS
    assert all(row.proof_objects == row.proof_nodes for row in receipts)
    assert sum(row.proof_nodes for row in receipts) == 767
    assert max(row.proof_nodes for row in receipts) == 147
    assert max(row.proof_depth for row in receipts) == 35


def test_every_external_prerequisite_already_has_checked_v19_authority() -> None:
    local = set(EXPECTED_NAMES)
    external = {
        dependency
        for row in _rows()
        for dependency in row.dependencies
        if dependency not in local
    }

    assert external == EXPECTED_CORE_BOUNDARY
    assert len(external) == 25
    assert all(editions_v19.ALPHA_EDITION.by_name[name].checked_use for name in external)


def test_g023_endpoint_has_exact_prime_strict_window_central_value_and_valuation() -> None:
    row = _rows()[6]
    assert row.name == candidate.CENTRAL_BINOM_PRIME_DIVISOR_MULTIPLICITY_ONE_EXISTS
    assert row.dependencies == (
        "bertrand_strict",
        "central_binom_exists",
        candidate.BERTRAND_WINDOW_CENTRAL_VALUATION_ONE,
    )

    root = _closed_formula(row.statement)
    assert isinstance(root, Forall)
    assert isinstance(root.body, Imp)
    assert isinstance(root.body.antecedent, Exists)
    assert isinstance(root.body.consequent, Exists)
    assert isinstance(root.body.consequent.body, Exists)
    prime_and_window = root.body.consequent.body.body
    assert isinstance(prime_and_window, And)
    assert isinstance(prime_and_window.left, And)
    lower_and_remaining = prime_and_window.right
    assert isinstance(lower_and_remaining, And)
    assert isinstance(lower_and_remaining.left, Exists)
    upper_and_remaining = lower_and_remaining.right
    assert isinstance(upper_and_remaining, And)
    assert isinstance(upper_and_remaining.left, Exists)
    assert isinstance(upper_and_remaining.right, And)
    assert "S (p) = n + n" in row.statement
    assert "bpc_one_exponent_marker" not in row.statement
    assert "prime_total_domain" not in row.statement


def test_g024_endpoint_quantifies_arbitrary_length_and_every_strict_prime_edge() -> None:
    row = _rows()[-1]
    assert row.name == candidate.ITERATED_BERTRAND_PRIME_CHAIN_EXISTS
    assert row.dependencies == (candidate.BERTRAND_CHAIN_PREFIX_TERMINAL_EXISTS,)

    root = _closed_formula(row.statement)
    assert isinstance(root, Forall)
    assert isinstance(root.body, Forall)
    guard = root.body.body
    assert isinstance(guard, Imp)
    assert isinstance(guard.antecedent, Exists)
    assert isinstance(guard.consequent, Exists)
    assert isinstance(guard.consequent.body, Exists)
    chain = guard.consequent.body.body
    assert isinstance(chain, And)
    assert isinstance(chain.left, And)
    assert isinstance(chain.right, Forall)
    assert isinstance(chain.right.body, Imp)
    assert isinstance(chain.right.body.antecedent, Exists)
    assert isinstance(chain.right.body.consequent, Exists)
    assert isinstance(chain.right.body.consequent.body, Exists)
    edges = chain.right.body.consequent.body.body
    assert isinstance(edges, And)
    assert isinstance(edges.right, And)
    assert isinstance(edges.right.right, And)
    assert isinstance(edges.right.right.left, And)
    assert isinstance(edges.right.right.right, And)
    assert "S (bcf_previous_bpc_old_chain)" in row.statement
    assert "bcf_previous_bpc_old_chain + bcf_previous_bpc_old_chain" in row.statement


@pytest.mark.parametrize(
    ("builder", "expected_free"),
    (
        (lambda tag: candidate.bertrand_window("n", "p", tag=tag), {"n", "p"}),
        (lambda tag: candidate.power_valuation_one("p", "C", tag=tag), {"p", "C"}),
        (
            lambda tag: candidate.bertrand_chain("b", "c", "n", "k", tag=tag),
            {"b", "c", "n", "k"},
        ),
    ),
)
def test_definition_surfaces_are_hygienic_alpha_equivalent_and_conservative(
    builder, expected_free: set[str]
) -> None:
    left = builder("left")
    right = builder("right")
    _, free = parse_formula_with_names(left)

    assert left != right
    assert parse_formula(left) == parse_formula(right)
    assert set(free) == expected_free
    assert not any(
        forbidden in left
        for forbidden in (
            "Prime(",
            "Lt(",
            "Le(",
            "Seq(",
            "At(",
            "Val(",
            "^",
            "%",
            "choice",
            "oracle",
        )
    )


@pytest.mark.parametrize(
    "builder",
    (
        lambda: candidate.bertrand_window("n + 1", "p", tag="bad"),
        lambda: candidate.bertrand_window("n", "S p", tag="bad"),
        lambda: candidate.bertrand_window("n", "p", tag="bad tag"),
        lambda: candidate.bertrand_window("forall", "p", tag="bad"),
        lambda: candidate.bertrand_window("n", "p", tag="forall"),
        lambda: candidate.bertrand_window(
            "n", "bcf_lt_gap_bpc_capture_lower", tag="capture"
        ),
        lambda: candidate.power_valuation_one("p * p", "C", tag="bad"),
        lambda: candidate.power_valuation_one("p", "C + 1", tag="bad"),
        lambda: candidate.power_valuation_one("p", "C", tag="bad tag"),
        lambda: candidate.power_valuation_one(
            "bpc_one_exponent_marker", "C", tag="bad"
        ),
        lambda: candidate.bertrand_chain("b + 1", "c", "n", "k", tag="bad"),
        lambda: candidate.bertrand_chain("b", "c * 2", "n", "k", tag="bad"),
        lambda: candidate.bertrand_chain("b", "c", "n + 1", "k", tag="bad"),
        lambda: candidate.bertrand_chain("b", "c", "n", "S k", tag="bad"),
        lambda: candidate.bertrand_chain("b", "c", "n", "k", tag="bad tag"),
        lambda: candidate.bertrand_chain(
            "bcf_index_bpc_capture_chain", "c", "n", "k", tag="capture"
        ),
    ),
)
def test_definition_surfaces_reject_injection_reserved_names_and_binder_capture(
    builder,
) -> None:
    with pytest.raises(ValueError):
        builder()


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_conclusions_are_rejected_by_original_intuitionistic_kernel(
    name: str,
) -> None:
    row = next(item for item in _rows() if item.name == name)
    forged = replace(row, statement=f"({row.statement}) /\\ false")

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {item.name: item for item in _rows()})


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_scripts_never_become_accepted_proof_evidence(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    forged = replace(row, script=row.script[:-1])

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {item.name: item for item in _rows()})


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_removing_any_row_final_declared_dependency_fails_closed(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    forged = replace(row, dependencies=row.dependencies[:-1])

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {item.name: item for item in _rows()})


@pytest.mark.parametrize("index", (2, 3, 4, 5, 6, 8, 10, 16, 25, 40, 64, 100))
def test_every_numerical_strict_window_prime_has_exact_central_valuation_one(
    index: int,
) -> None:
    coefficient = comb(2 * index, index)
    window = tuple(value for value in range(index + 1, 2 * index) if _is_prime(value))

    assert window
    for divisor in window:
        assert index < divisor < 2 * index
        assert divisor * divisor > 2 * index
        assert coefficient % divisor == 0
        assert _valuation(divisor, coefficient) == 1
        assert coefficient % (divisor * divisor) != 0


@pytest.mark.parametrize(
    ("initial", "length"),
    ((2, 0), (2, 1), (2, 2), (2, 5), (3, 4), (5, 6), (10, 4), (25, 7)),
)
def test_numerical_prime_chains_have_actual_beta_codes_and_exact_strict_edges(
    initial: int, length: int
) -> None:
    values = [initial]
    for _ in range(length):
        values.append(_least_strict_bertrand_prime(values[-1]))
    code, scale = _beta_encode(tuple(values))

    assert len(values) == length + 1
    assert code % (1 + scale) == initial
    assert all(
        _is_prime(following) and previous < following < 2 * previous
        for previous, following in zip(values, values[1:], strict=False)
    )
    assert all(
        code % (1 + (index + 1) * scale) == value
        for index, value in enumerate(values)
    )


@pytest.mark.parametrize(
    ("previous", "following"),
    ((1, 2), (2, 2), (2, 4), (2, 5), (3, 4), (4, 8), (5, 10), (11, 22)),
)
def test_invalid_or_non_strict_prime_windows_are_never_valid_chain_edges(
    previous: int, following: int
) -> None:
    assert not (
        previous > 1
        and _is_prime(following)
        and previous < following < 2 * previous
    )
