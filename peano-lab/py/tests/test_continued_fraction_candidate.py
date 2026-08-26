"""Kernel, hygiene, witness, and semantic audit for the complete G071 stack."""

from __future__ import annotations

from dataclasses import fields, replace
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from math import gcd, lcm

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Imp,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import continued_fraction_candidate as candidate
from peano_lab.library import editions_v19 as v19
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _primitive


EXPECTED_NAMES = (
    "continued_fraction_initial_state_exists",
    "continued_fraction_empty_trace",
    "continued_fraction_empty_trace_exists",
    "continued_fraction_trace_extend",
    "continued_fraction_trace_exists_up_to",
    "continued_fraction_trace_exists",
    "continued_fraction_nonzero_divisor_exists",
    "continued_fraction_positive_nonempty_exists",
    "continued_fraction_positive_exists",
)
EXPECTED_COMMAND_COUNTS = (11, 16, 8, 133, 100, 11, 49, 39, 14)
EXPECTED_PROOF_NODES = (33, 25, 19, 194, 200, 11, 64, 43, 16)
EXPECTED_PROOF_DEPTHS = (19, 16, 14, 57, 38, 9, 28, 23, 11)
EXPECTED_STATEMENT_SHA256 = {
    "continued_fraction_initial_state_exists": (
        "938f2d128e6e48c962d03d5b0be355179b1c57875b8c5eb1c594bea640bf977b"
    ),
    "continued_fraction_empty_trace": (
        "1a95be29d5da368e3a0cc9bc072cda5d6a8796fa0bfeed87dc65cd20b06e4328"
    ),
    "continued_fraction_empty_trace_exists": (
        "6c4a644149624c1a7d5782299eb1690cc5bc5fe0a7e31f71f1ffe7100a844190"
    ),
    "continued_fraction_trace_extend": (
        "07fad31118011dac792045ec64668c0220676fcfc1b943b9cc6ddf92d7d03104"
    ),
    "continued_fraction_trace_exists_up_to": (
        "9ab3b190b0b5f8b1b9bf8d1f0bcbec69a1e962a44cd4c54c8b28beab79e44fd6"
    ),
    "continued_fraction_trace_exists": (
        "f610c530fe5ab6da7007cc8d6d9a58577e5c8b1d2587e32a06101a64ad71b03c"
    ),
    "continued_fraction_nonzero_divisor_exists": (
        "308538df05216fca608c0ced9ce4404b206da3633fa5f8be93a53e2da2350b16"
    ),
    "continued_fraction_positive_nonempty_exists": (
        "6175792902301cca20e1eb2d0c5926711f0e702e9f536974af8ebe2b0847ac60"
    ),
    "continued_fraction_positive_exists": (
        "d3b12766820bb64d9b1437e0ef96a9068c84d6d3176e066fe70f5a4f2d9e087d"
    ),
}
EXPECTED_EXTERNAL = {
    "beta_prefix_extend",
    "cell_constructor",
    "cell_nonzero",
    "division_remainder_exists",
    "finite_lt_succ_eq_or_lt",
    "le_eq_or_lt",
    "le_of_succ_le_succ",
    "le_refl",
    "le_succ_self",
    "le_zero",
    "lt_of_lt_of_le",
    "nonzero_is_succ",
    "succ_le_succ",
    "zero_add",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_continued_fraction_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v19.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def _receipts():
    return replay_candidate_bodies(_rows(), core=_core())


def _row(name: str) -> TheoremSpec:
    return next(item for item in _rows() if item.name == name)


def _all_available() -> dict[str, TheoremSpec]:
    return _core() | {item.name: item for item in _rows()}


def _curried_certificate(name: str) -> tuple[Proof, object]:
    item = _row(name)
    available = _all_available()
    target = _closed_formula(item.statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _proof_nodes(proof: Proof):
    pending = [proof]
    visited: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in visited:
            continue
        visited.add(id(current))
        yield current
        pending.extend(
            child
            for field in fields(current)
            if isinstance((child := getattr(current, field.name)), Proof)
        )


def test_nine_exact_candidates_are_ordered_closed_and_frozen() -> None:
    actual = _rows()

    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert actual == candidate.make_continued_fraction_candidate_theorems(TheoremSpec)
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        "3e573dc07284357171fe7781f575d3a8939331ae15b6f96011f292efae4a34eb"
    )
    assert {
        item.name: sha256(item.statement.encode()).hexdigest()
        for item in actual
    } == EXPECTED_STATEMENT_SHA256
    assert sum(len(item.script) for item in actual) == 381
    assert sum(len(item.dependencies) for item in actual) == 25

    seen: set[str] = set()
    for item in actual:
        parsed, free = parse_formula_with_names(item.statement)
        assert not free
        assert parsed == _closed_formula(item.statement)
        assert len(item.dependencies) == len(set(item.dependencies))
        assert set(item.dependencies) <= set(_core()) | seen
        assert item.name not in v19.ALPHA_EDITION.by_name
        assert all(
            forbidden not in item.statement
            for forbidden in (
                "BetaAt(",
                "Cell(",
                "ContinuedFraction(",
                "Trace(",
                "Pair(",
                "%",
                "^",
            )
        )
        assert all("DNE" not in command for command in item.script)
        seen.add(item.name)


def test_all_nine_dependency_curried_bodies_pass_original_kernel() -> None:
    actual = _receipts()

    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert tuple(item.command_count for item in actual) == EXPECTED_COMMAND_COUNTS
    assert tuple(item.proof_nodes for item in actual) == EXPECTED_PROOF_NODES
    assert tuple(item.proof_depth for item in actual) == EXPECTED_PROOF_DEPTHS
    assert sum(item.proof_nodes for item in actual) == 605
    assert max(item.proof_nodes for item in actual) == 200
    assert max(item.proof_depth for item in actual) == 57
    assert all(item.proof_nodes == item.proof_objects for item in actual)
    assert all(item.proof_edges + 1 == item.proof_objects for item in actual)


def test_only_preexisting_checked_alpha_v19_prerequisites_supply_authority() -> None:
    names = set(EXPECTED_NAMES)
    external = {
        dependency
        for item in _rows()
        for dependency in item.dependencies
        if dependency not in names
    }

    assert external == EXPECTED_EXTERNAL
    assert all(v19.ALPHA_EDITION.by_name[name].checked_use for name in external)
    alpha_only = {
        name
        for name in external
        if v19.ALPHA_EDITION.by_name[name].membership.value == "alpha_only"
    }
    assert alpha_only == {"cell_constructor", "cell_nonzero"}


def test_trace_and_continued_fraction_surfaces_are_hygienic_and_alpha_equal() -> None:
    first = candidate.continued_fraction_trace(
        "a", "b", "s", "h", "e", "l", tag="first"
    )
    second = candidate.continued_fraction_trace(
        "a", "b", "s", "h", "e", "l", tag="second"
    )
    first_formula, first_free = parse_formula_with_names(first)
    second_formula, second_free = parse_formula_with_names(second)
    assert set(first_free) == set(second_free) == {"a", "b", "s", "h", "e", "l"}
    assert first_formula == second_formula

    positive = candidate.continued_fraction("a", "b", "s", tag="positive")
    renamed = candidate.continued_fraction("a", "b", "s", tag="renamed")
    positive_formula, positive_free = parse_formula_with_names(positive)
    renamed_formula, renamed_free = parse_formula_with_names(renamed)
    assert set(positive_free) == set(renamed_free) == {"a", "b", "s"}
    assert positive_formula == renamed_formula

    for fragment in ("", "S", "forall", "a + b", "0", "a;b"):
        with pytest.raises(ValueError):
            candidate.continued_fraction_trace(
                fragment, "b", "s", "h", "e", "l", tag="safe"
            )
        with pytest.raises(ValueError):
            candidate.continued_fraction(fragment, "b", "s", tag="safe")
    with pytest.raises(ValueError, match="captures"):
        candidate.continued_fraction_trace(
            "cf_gcd_capture", "b", "s", "h", "e", "l", tag="capture"
        )
    with pytest.raises(ValueError, match="captures"):
        candidate.continued_fraction("cf_a_pred_capture", "b", "s", tag="capture")


def test_exact_g071_endpoint_requires_two_positive_inputs_and_complete_trace() -> None:
    endpoint = _row(candidate.CONTINUED_FRACTION_POSITIVE_EXISTS)
    assert endpoint.dependencies == (candidate.CONTINUED_FRACTION_POSITIVE_NONEMPTY_EXISTS,)

    formula = _closed_formula(endpoint.statement)
    assert isinstance(formula, Forall)
    assert isinstance(formula.body, Forall)
    first_input = formula.body.body
    assert isinstance(first_input, Imp)
    assert isinstance(first_input.antecedent, Imp)
    assert isinstance(first_input.antecedent.antecedent, Eq)
    assert isinstance(first_input.antecedent.consequent, Bot)
    second_input = first_input.consequent
    assert isinstance(second_input, Imp)
    assert isinstance(second_input.antecedent, Imp)
    assert isinstance(second_input.antecedent.consequent, Bot)
    result = second_input.consequent
    assert isinstance(result, Exists)  # The forward, cell-coded quotient list.
    for _ in range(5):
        result = result.body
        assert isinstance(result, Exists)
    positivity = result.body
    assert isinstance(positivity, And)
    assert isinstance(positivity.left, Eq)
    assert isinstance(positivity.right, And)
    assert isinstance(positivity.right.left, Eq)
    assert isinstance(positivity.right.right, Exists)  # Initial gcd state.

    assert "cf_length_pred_positive_result" in endpoint.statement
    assert "S cf_length_pred_positive_result" in endpoint.statement
    assert "cf_old_b_positive_result_trace" in endpoint.statement
    assert "cf_new_b_positive_result_trace" in endpoint.statement
    assert "cf_quotient_positive_result_trace" in endpoint.statement


def test_stronger_root_explicitly_excludes_the_empty_quotient_list() -> None:
    formula = _closed_formula(
        _row(candidate.CONTINUED_FRACTION_POSITIVE_NONEMPTY_EXISTS).statement
    )
    assert isinstance(formula, Forall)
    assert isinstance(formula.body, Forall)
    body = formula.body.body
    assert isinstance(body, Imp)
    assert isinstance(body.consequent, Imp)
    result = body.consequent.consequent
    assert isinstance(result, Exists)
    assert isinstance(result.body, And)
    assert isinstance(result.body.right, Imp)
    assert isinstance(result.body.right.antecedent, Eq)
    assert isinstance(result.body.right.consequent, Bot)


@pytest.mark.parametrize(
    "name",
    (
        candidate.CONTINUED_FRACTION_TRACE_EXTEND,
        candidate.CONTINUED_FRACTION_TRACE_EXISTS_UP_TO,
        candidate.CONTINUED_FRACTION_POSITIVE_EXISTS,
    ),
)
def test_important_certificates_contain_no_classical_double_negation(name: str) -> None:
    certificate, target = _curried_certificate(name)
    assert check((), certificate, target)
    assert all(not isinstance(node, DNE) for node in _proof_nodes(certificate))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_candidate_conclusions_are_independently_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_all_available())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_candidate_scripts_never_become_kernel_evidence(name: str) -> None:
    original = _row(name)
    forged = replace(original, script=original.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_all_available())


@pytest.mark.parametrize(
    "name",
    tuple(name for name in EXPECTED_NAMES if name != candidate.CONTINUED_FRACTION_EMPTY_TRACE),
)
def test_missing_declared_dependencies_fail_closed(name: str) -> None:
    original = _row(name)
    forged = replace(original, dependencies=original.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_all_available())


@pytest.mark.parametrize(
    ("command", "replacement"),
    (
        ("exact hdivision", "refl"),
        ("exact hbound", "exists b"),
        ("exact hs", "refl"),
        ("exact htrace_witness_right_left", "refl"),
    ),
)
def test_trace_extension_rejects_forged_division_bound_cell_or_terminal(
    command: str, replacement: str
) -> None:
    original = _row(candidate.CONTINUED_FRACTION_TRACE_EXTEND)
    index = original.script.index(command)
    script = original.script[:index] + (replacement,) + original.script[index + 1 :]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(original, script=script),), core=_all_available())


def _pair(left: int, right: int) -> int:
    return (left + right) * (left + right + 1) + 2 * right


def _cell(head: int, tail: int) -> int:
    return 1 + _pair(head, tail)


def _pack(dividend: int, divisor: int, quotient_list: int) -> int:
    return _pair(dividend, _pair(divisor, quotient_list))


def _certificate(
    dividend: int, divisor: int
) -> tuple[list[tuple[int, int, int, int]], list[tuple[int, int, int]]]:
    divisions: list[tuple[int, int, int, int]] = []
    a, b = dividend, divisor
    while b:
        quotient, remainder = divmod(a, b)
        divisions.append((a, b, quotient, remainder))
        a, b = b, remainder

    states = [(a, 0, 0)]
    for upper, lower, quotient, remainder in reversed(divisions):
        previous_a, previous_b, previous_list = states[-1]
        assert (previous_a, previous_b) == (lower, remainder)
        states.append((upper, lower, _cell(quotient, previous_list)))
    return divisions, states


def _beta_history(values: list[int]) -> tuple[int, int]:
    scale = lcm(*range(1, len(values) + 1)) * (max(values) + 1)
    result = 0
    period = 1
    for index, value in enumerate(values):
        modulus = 1 + (index + 1) * scale
        assert value < modulus
        assert gcd(period, modulus) == 1
        correction = ((value - result) * pow(period, -1, modulus)) % modulus
        result += period * correction
        period *= modulus
    return result, scale


def _trace_semantics(
    dividend: int,
    divisor: int,
    divisions: list[tuple[int, int, int, int]],
    states: list[tuple[int, int, int]],
    history_code: int,
    history_scale: int,
) -> bool:
    if len(states) != len(divisions) + 1:
        return False
    if states[0][1:] != (0, 0):
        return False
    if states[-1][:2] != (dividend, divisor):
        return False
    for index, state in enumerate(states):
        modulus = 1 + (index + 1) * history_scale
        value = _pack(*state)
        if value >= modulus or history_code % modulus != value:
            return False
    for old, new, step in zip(states, states[1:], reversed(divisions)):
        old_a, old_b, old_list = old
        new_a, new_b, new_list = new
        expected_a, expected_b, quotient, expected_remainder = step
        if (
            (new_a, new_b, old_b) != (expected_a, expected_b, expected_remainder)
            or new_b != old_a
            or new_a != new_b * quotient + old_b
            or old_b >= new_b
            or new_list != _cell(quotient, old_list)
        ):
            return False
    return True


@pytest.mark.parametrize(
    ("dividend", "divisor", "expected"),
    (
        (0, 0, ()),
        (9, 0, ()),
        (0, 5, (0,)),
        (1, 1, (1,)),
        (2, 1, (2,)),
        (1, 2, (0, 2)),
        (42, 30, (1, 2, 2)),
        (13, 8, (1, 1, 1, 1, 2)),
        (355, 113, (3, 7, 16)),
        (415, 93, (4, 2, 6, 7)),
    ),
)
def test_actual_beta_histories_encode_exact_forward_quotients_and_boundaries(
    dividend: int, divisor: int, expected: tuple[int, ...]
) -> None:
    divisions, states = _certificate(dividend, divisor)
    assert tuple(quotient for _, _, quotient, _ in divisions) == expected
    assert states[0][0] == gcd(dividend, divisor)
    assert states[-1][:2] == (dividend, divisor)
    assert bool(states[-1][2]) == bool(divisor)

    packed = [_pack(*state) for state in states]
    history_code, history_scale = _beta_history(packed)
    assert _trace_semantics(
        dividend, divisor, divisions, states, history_code, history_scale
    )
    assert not _trace_semantics(
        dividend, divisor, divisions, states, history_code + 1, history_scale
    )

    if divisor:
        numerator, denominator = expected[-1], 1
        for quotient in reversed(expected[:-1]):
            numerator, denominator = quotient * numerator + denominator, numerator
        assert Fraction(numerator, denominator) == Fraction(dividend, divisor)
        assert expected[0] == dividend // divisor
        assert len(expected) == len(states) - 1
        if len(expected) > 1:
            assert expected[-1] > 1


def test_numeric_trace_rejects_wrong_order_remainder_and_cell_encoding() -> None:
    divisions, states = _certificate(415, 93)
    packed = [_pack(*state) for state in states]
    code, scale = _beta_history(packed)
    assert _trace_semantics(415, 93, divisions, states, code, scale)

    assert not _trace_semantics(93, 415, divisions, states, code, scale)
    assert not _trace_semantics(415, 93, list(reversed(divisions)), states, code, scale)

    broken_remainder = list(divisions)
    a, b, quotient, remainder = broken_remainder[0]
    broken_remainder[0] = (a, b, quotient, remainder + b)
    assert not _trace_semantics(415, 93, broken_remainder, states, code, scale)

    broken_list = list(states)
    a, b, encoded = broken_list[-1]
    broken_list[-1] = (a, b, encoded + 1)
    assert not _trace_semantics(415, 93, divisions, broken_list, code, scale)
