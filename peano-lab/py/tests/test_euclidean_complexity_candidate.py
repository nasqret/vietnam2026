"""Original-kernel, hygiene, complexity, beta-witness, and G101 truth audit."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from math import gcd

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Eq, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v20 as v20
from peano_lab.library import euclidean_complexity_candidate as candidate
from peano_lab.library.campaign_next_layer_closure import next_layer_closure_plan
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.continued_fraction_candidate import continued_fraction_trace
from peano_lab.library.ha_canonical_gcd_candidate import is_gcd
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _primitive


EXPECTED_NAMES = (
    "euclidean_division_step_exists",
    "euclidean_division_step_functional",
    "euclidean_next_division_step_exists",
    "euclidean_add_right_preserves_lt",
    "euclidean_two_step_quotient_nonzero",
    "euclidean_two_step_halving",
    "euclidean_trace_bound_weaken",
    "euclidean_trace_exists_up_to_linear",
    "euclidean_trace_exists_linear",
    "euclidean_execution_zero_divisor",
    "euclidean_execution_gcd_correct",
    "euclidean_execution_trace_correct",
    "euclidean_execution_exists",
    "euclidean_nonzero_execution_exists",
    "euclidean_gcd_execution_linear_bound",
)
EXPECTED_COMMAND_COUNTS = (7, 21, 10, 16, 27, 49, 19, 113, 11, 11, 10, 13, 19, 24, 22)
EXPECTED_PROOF_NODES = (15, 58, 18, 19, 37, 57, 38, 219, 11, 21, 20, 23, 38, 30, 48)
EXPECTED_PROOF_DEPTHS = (10, 34, 13, 12, 21, 30, 24, 42, 9, 14, 13, 16, 24, 18, 29)
EXPECTED_STATEMENT_SHA256 = {
    "euclidean_division_step_exists": "4712bd14f3dbec44584c99d767c0fda955a86e76efa1d84b2993d82d97cc946a",
    "euclidean_division_step_functional": "aa8ee15da1e99e2ecbe8a84ca3f167c34bed66ffea1c43f94d0e019e0d3ab3b5",
    "euclidean_next_division_step_exists": "982e3342cd5a8910da446c74ccb2f34afa5d79570e606fcb1664ad505501e1df",
    "euclidean_add_right_preserves_lt": "c484f9535731a3bebed1226d7c1fdb8cb59f3d10e6327475e4d01fab9a57175e",
    "euclidean_two_step_quotient_nonzero": "1c1b41cf5318fc913d25419bab38750710de6d15df4513ab613d9e36f3271191",
    "euclidean_two_step_halving": "a7bf1c208237e02edcfdb3b7c819e944be1d0bc8783a06bcb05cfcab5ba7df94",
    "euclidean_trace_bound_weaken": "430774c2ce5826949a7cfe7a0d627bec936328905506711a5f1779dba1c78a6b",
    "euclidean_trace_exists_up_to_linear": "f80d09c93b565e5f26b7c3014e33efdf7992165068a8b7dbae394c1e5b7a201e",
    "euclidean_trace_exists_linear": "7ef3cef1ef7133a3039600496a3e71a106471b205eccc13bfbf42019bf987c65",
    "euclidean_execution_zero_divisor": "3e0145a3f44e9bb2a8d12cd9f28b4ae320ef10b28428b3e7978a982fc40a2100",
    "euclidean_execution_gcd_correct": "cf159fb3a28894bbb8cc7d596ad858cdcbf27177fe9df0354a84fe70cd52250a",
    "euclidean_execution_trace_correct": "19cb48747e0bc9d6239a822968c1da8131117f9753a17923708f89c951fde27a",
    "euclidean_execution_exists": "380d3d82ca5d5db3bac530cbf1bc19a2a7ae6fc7121ae980a9f4f5d391ede759",
    "euclidean_nonzero_execution_exists": "ef3f24e89bb385eb4efdcf2b7b4546e9975b9ca3ea5256119109d2aebca10fa1",
    "euclidean_gcd_execution_linear_bound": "cde09bcea3d247bca7dc5d0b44a0576b1822a0464826f54f5ff3424bdeec2435",
}
EXPECTED_EXTERNAL = {
    "add_le_add_right",
    "add_succ_left",
    "continued_fraction_empty_trace_exists",
    "continued_fraction_nonzero_divisor_exists",
    "continued_fraction_trace_exists",
    "continued_fraction_trace_extend",
    "division_remainder_exists",
    "division_remainder_unique",
    "gcd_exists_relational",
    "is_gcd_zero_right",
    "le_eq_or_lt",
    "le_mul_of_one_le_right",
    "le_of_succ_le_succ",
    "le_refl",
    "le_succ",
    "le_zero",
    "lt_irrefl_expanded",
    "lt_of_lt_of_le",
    "lt_trans",
    "one_le_of_ne_zero",
    "succ_le_succ",
    "zero_add",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_euclidean_complexity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v20.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def _receipts():
    return replay_candidate_bodies(_rows(), core=_core())


def _row(name: str) -> TheoremSpec:
    return next(item for item in _rows() if item.name == name)


def _available() -> dict[str, TheoremSpec]:
    return _core() | {item.name: item for item in _rows()}


def _curried_certificate(name: str) -> tuple[Proof, object]:
    item = _row(name)
    target = _closed_formula(item.statement)
    available = _available()
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
            value
            for field in fields(current)
            if isinstance((value := getattr(current, field.name)), Proof)
        )


def test_fifteen_exact_candidates_are_dependency_ordered_closed_and_frozen() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert rows == candidate.make_euclidean_complexity_candidate_theorems(TheoremSpec)
    assert {row.name: sha256(row.statement.encode()).hexdigest() for row in rows} == (
        EXPECTED_STATEMENT_SHA256
    )
    assert sum(len(row.script) for row in rows) == 372
    assert sum(len(row.dependencies) for row in rows) == 34

    seen: set[str] = set()
    for row in rows:
        parsed, free = parse_formula_with_names(row.statement)
        assert not free
        assert parsed == _closed_formula(row.statement)
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= set(_core()) | seen
        assert row.name not in v20.ALPHA_EDITION.by_name
        assert all(
            forbidden not in row.statement
            for forbidden in (
                "Euclid(",
                "Execution(",
                "BitLen(",
                "BetaAt(",
                "Cell(",
                "IsGCD(",
                "ContinuedFractionTrace(",
                "%",
                "^",
            )
        )
        assert all("DNE" not in command for command in row.script)
        seen.add(row.name)


def test_all_fifteen_dependency_curried_bodies_pass_original_intuitionistic_kernel() -> None:
    receipts = _receipts()
    assert tuple(receipt.name for receipt in receipts) == EXPECTED_NAMES
    assert tuple(receipt.command_count for receipt in receipts) == EXPECTED_COMMAND_COUNTS
    assert tuple(receipt.proof_nodes for receipt in receipts) == EXPECTED_PROOF_NODES
    assert tuple(receipt.proof_depth for receipt in receipts) == EXPECTED_PROOF_DEPTHS
    assert sum(receipt.proof_nodes for receipt in receipts) == 652
    assert max(receipt.proof_depth for receipt in receipts) == 42
    assert all(receipt.proof_nodes == receipt.proof_objects for receipt in receipts)
    assert all(receipt.proof_edges + 1 == receipt.proof_objects for receipt in receipts)


def test_every_external_dependency_already_lives_in_v20_checked_bundle_cone() -> None:
    names = set(EXPECTED_NAMES)
    actual = {
        dependency
        for row in _rows()
        for dependency in row.dependencies
        if dependency not in names
    }
    assert actual == EXPECTED_EXTERNAL
    v20_cone = {row.name for row in next_layer_closure_plan().rows}
    assert actual <= v20_cone
    assert all(v20.ALPHA_EDITION.by_name[name].checked_use for name in actual)


@pytest.mark.parametrize(
    ("builder", "arguments", "free_names"),
    (
        (candidate.euclidean_division, ("a", "b", "q", "r"), {"a", "b", "q", "r"}),
        (candidate.euclidean_halving, ("b", "t"), {"b", "t"}),
        (candidate.euclidean_execution, ("a", "b", "g", "l"), {"a", "b", "g", "l"}),
    ),
)
def test_conservative_relations_are_hygienic_and_alpha_invariant(
    builder, arguments: tuple[str, ...], free_names: set[str]
) -> None:
    first, first_free = parse_formula_with_names(builder(*arguments, tag="first"))
    second, second_free = parse_formula_with_names(builder(*arguments, tag="second"))
    assert set(first_free) == set(second_free) == free_names
    assert first == second


@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_relations_reject_invalid_argument_fragments(fragment: str) -> None:
    with pytest.raises(ValueError):
        candidate.euclidean_division(fragment, "b", "q", "r", tag="safe")
    with pytest.raises(ValueError):
        candidate.euclidean_halving(fragment, "r", tag="safe")
    with pytest.raises(ValueError):
        candidate.euclidean_execution(fragment, "b", "g", "l", tag="safe")


@pytest.mark.parametrize("fragment", ("", "S", "forall", "tag + attack", "0", "x;y"))
def test_relations_reject_invalid_binder_tags(fragment: str) -> None:
    with pytest.raises(ValueError):
        candidate.euclidean_division("a", "b", "q", "r", tag=fragment)
    with pytest.raises(ValueError):
        candidate.euclidean_halving("b", "r", tag=fragment)
    with pytest.raises(ValueError):
        candidate.euclidean_execution("a", "b", "g", "l", tag=fragment)


def test_relations_reject_explicit_generated_binder_capture() -> None:
    with pytest.raises(ValueError, match="captures"):
        candidate.euclidean_division(
            "ff_lt_ec_capture_division", "b", "q", "r", tag="capture"
        )
    with pytest.raises(ValueError, match="captures"):
        candidate.euclidean_halving("ff_lt_ec_capture_halving", "r", tag="capture")
    with pytest.raises(ValueError, match="captures"):
        candidate.euclidean_execution("ec_list_capture", "b", "g", "l", tag="capture")


def test_execution_is_exactly_beta_history_and_original_relational_gcd() -> None:
    actual, free = parse_formula_with_names(
        candidate.euclidean_execution("a", "b", "g", "l", tag="audit")
    )
    expected, expected_free = parse_formula_with_names(
        "exists s h e. (("
        + continued_fraction_trace("a", "b", "s", "h", "e", tag="audit_expected", length="l")
        + ") /\\ ("
        + is_gcd("g", "a", "b", tag="audit_expected")
        + "))"
    )
    assert set(free) == set(expected_free) == {"a", "b", "g", "l"}
    assert actual == expected


def test_two_step_halving_and_linear_endpoint_state_exact_constructive_claims() -> None:
    halving = _closed_formula(_row(candidate.EUCLIDEAN_TWO_STEP_HALVING).statement)
    for _ in range(6):
        assert isinstance(halving, Forall)
        halving = halving.body
    assert isinstance(halving, Imp)
    assert isinstance(halving.antecedent, And)
    assert isinstance(halving.consequent, Imp)
    assert isinstance(halving.consequent.antecedent, And)
    assert isinstance(halving.consequent.consequent, Exists)
    assert "S (t + t) = b" in _row(candidate.EUCLIDEAN_TWO_STEP_HALVING).statement

    endpoint = _closed_formula(
        _row(candidate.EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND).statement
    )
    assert isinstance(endpoint, Forall)
    assert isinstance(endpoint.body, Forall)
    result = endpoint.body.body
    assert isinstance(result, Exists)
    assert isinstance(result.body, Exists)
    conjuncts = result.body.body
    assert isinstance(conjuncts, And)
    assert isinstance(conjuncts.left, Exists)
    assert isinstance(conjuncts.right, Exists)
    assert "gap + l = b" in _row(candidate.EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND).statement
    assert "BitLen" not in _row(candidate.EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND).statement


@pytest.mark.parametrize(
    "name",
    (
        candidate.EUCLIDEAN_TWO_STEP_HALVING,
        candidate.EUCLIDEAN_TRACE_EXISTS_UP_TO_LINEAR,
        candidate.EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND,
    ),
)
def test_crucial_original_kernel_certificates_contain_no_classical_dne(name: str) -> None:
    certificate, target = _curried_certificate(name)
    assert check((), certificate, target)
    assert all(not isinstance(node, DNE) for node in _proof_nodes(certificate))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_false_conclusions_are_independently_rejected(name: str) -> None:
    row = _row(name)
    forged = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_available())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_candidate_scripts_are_never_accepted(name: str) -> None:
    row = _row(name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_available())


@pytest.mark.parametrize(
    "name",
    (
        candidate.EUCLIDEAN_TWO_STEP_HALVING,
        candidate.EUCLIDEAN_TRACE_EXISTS_UP_TO_LINEAR,
        candidate.EUCLIDEAN_TRACE_EXISTS_LINEAR,
        candidate.EUCLIDEAN_EXECUTION_EXISTS,
        candidate.EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND,
    ),
)
def test_missing_declared_dependencies_fail_closed(name: str) -> None:
    row = _row(name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(row, dependencies=row.dependencies[:-1]),), core=_available()
        )


@pytest.mark.parametrize(
    ("name", "command", "replacement"),
    (
        (
            candidate.EUCLIDEAN_TWO_STEP_HALVING,
            "exact hsecond_right",
            "refl",
        ),
        (
            candidate.EUCLIDEAN_TWO_STEP_HALVING,
            "exact hstrict",
            "exists b",
        ),
        (
            candidate.EUCLIDEAN_TRACE_EXISTS_UP_TO_LINEAR,
            "exact hdivision_witness_witness_left",
            "refl",
        ),
        (
            candidate.EUCLIDEAN_TRACE_EXISTS_UP_TO_LINEAR,
            "exact hsmall_witness_witness_witness_witness_right",
            "exists S B",
        ),
        (
            candidate.EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND,
            "exact gcd_exists_relational_witness",
            "refl",
        ),
        (
            candidate.EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND,
            "exact euclidean_trace_exists_linear_witness_witness_witness_witness_right",
            "exists S b",
        ),
    ),
)
def test_division_halving_beta_trace_gcd_or_linear_budget_forgery_fails(
    name: str, command: str, replacement: str
) -> None:
    row = _row(name)
    index = row.script.index(command)
    script = row.script[:index] + (replacement,) + row.script[index + 1 :]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=script),), core=_available())


@pytest.mark.parametrize(
    ("dividend", "divisor", "expected_gcd", "expected_quotients"),
    (
        (0, 0, 0, ()),
        (9, 0, 9, ()),
        (0, 5, 5, (0,)),
        (1, 1, 1, (1,)),
        (2, 1, 1, (2,)),
        (1, 2, 1, (0, 2)),
        (48, 18, 6, (2, 1, 2)),
        (42, 30, 6, (1, 2, 2)),
        (13, 8, 1, (1, 1, 1, 1, 2)),
        (355, 113, 1, (3, 7, 16)),
        (415, 93, 1, (4, 2, 6, 7)),
        (144, 89, 1, (1, 1, 1, 1, 1, 1, 1, 1, 1, 2)),
    ),
)
def test_concrete_certificates_encode_actual_beta_histories_and_both_bounds(
    dividend: int,
    divisor: int,
    expected_gcd: int,
    expected_quotients: tuple[int, ...],
) -> None:
    certificate = candidate.certify_euclidean_execution(dividend, divisor)
    assert candidate.verify_euclidean_execution(certificate)
    assert certificate.result == expected_gcd == gcd(dividend, divisor)
    assert tuple(step.quotient for step in certificate.steps) == expected_quotients
    assert certificate.step_count == len(expected_quotients)
    assert certificate.step_count <= divisor
    assert certificate.input_bit_length == divisor.bit_length()
    if divisor:
        # This checks only the concrete example; it is not G101 proof evidence.
        assert certificate.step_count <= 2 * divisor.bit_length() + 1
    assert len(certificate.history_values) == certificate.step_count + 1
    assert all(
        certificate.history_code % (1 + (index + 1) * certificate.history_scale)
        == value
        for index, value in enumerate(certificate.history_values)
    )
    for first, second in zip(certificate.steps, certificate.steps[1:]):
        assert second.quotient > 0
        assert 2 * second.remainder < first.divisor


@pytest.mark.parametrize(
    ("field", "transform"),
    (
        ("dividend", lambda current: current + 1),
        ("divisor", lambda current: current + 1),
        ("result", lambda current: current + 1),
        ("input_bit_length", lambda current: current + 1),
        ("quotient_list", lambda current: current + 1),
        ("history_values", lambda current: current[:-1]),
        ("history_code", lambda current: current + 1),
        ("history_scale", lambda current: current + 1),
        (
            "steps",
            lambda current: (replace(current[0], remainder=current[0].remainder + 1),)
            + current[1:],
        ),
    ),
)
def test_concrete_verifier_rejects_every_mutated_witness_field(
    field: str, transform
) -> None:
    original = candidate.certify_euclidean_execution(415, 93)
    forged = replace(original, **{field: transform(getattr(original, field))})
    assert not candidate.verify_euclidean_execution(forged)


@pytest.mark.parametrize("invalid", (-1, True, False, 1.0, "7", None))
def test_concrete_certificate_rejects_non_natural_inputs(invalid: object) -> None:
    with pytest.raises(ValueError, match="nonnegative integer"):
        candidate.certify_euclidean_execution(invalid, 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="nonnegative integer"):
        candidate.certify_euclidean_execution(1, invalid)  # type: ignore[arg-type]


@pytest.mark.parametrize("position", (0, 1))
def test_concrete_certificate_enforces_input_bit_cap(position: int) -> None:
    values = [1, 1]
    values[position] = 1 << candidate.MAX_EUCLIDEAN_INPUT_BITS
    with pytest.raises(ValueError, match="input bit cap"):
        candidate.certify_euclidean_execution(*values)


@pytest.mark.parametrize(
    ("dividend", "divisor", "reason"),
    (
        (377, 233, "beta history exceeds its bit cap"),
        (610, 377, "packed state exceeds its bit cap"),
        (1597, 987, "execution exceeds its step cap"),
    ),
)
def test_fibonacci_worst_cases_fail_safely_before_unbounded_allocations(
    dividend: int, divisor: int, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        candidate.certify_euclidean_execution(dividend, divisor)


def test_numeric_verifier_rejects_invalid_and_over_budget_certificates() -> None:
    assert not candidate.verify_euclidean_execution(None)  # type: ignore[arg-type]
    good = candidate.certify_euclidean_execution(55, 34)
    assert candidate.verify_euclidean_execution(good)
    assert not candidate.verify_euclidean_execution(replace(good, dividend=-1))
    assert not candidate.verify_euclidean_execution(
        replace(good, divisor=1 << candidate.MAX_EUCLIDEAN_INPUT_BITS)
    )


def test_g101_is_honestly_partial_until_checked_bit_length_and_log_induction_exist() -> None:
    assert not any("bitlen" in row.name.lower() for row in _core().values())
    endpoint = _row(candidate.EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND)
    assert "linear bound" in endpoint.summary
    assert "BitLen bound remains open" in endpoint.summary
    assert "BitLen" not in endpoint.statement
    assert "2 *" not in endpoint.statement
