"""Kernel, hygiene, invariant, terminal-identification, and adversarial audit."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Eq, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v21 as v21
from peano_lab.library import euclidean_gcd_transport_candidate as candidate
from peano_lab.library.campaign_advanced_layer_closure import advanced_layer_closure_plan
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.continued_fraction_candidate import (
    _state_at_term,
    continued_fraction_trace,
)
from peano_lab.library.ha_canonical_gcd_candidate import is_gcd
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _primitive


EXPECTED_NAMES = (
    "euclidean_divisor_remainder_transport",
    "euclidean_divisor_dividend_transport",
    "euclidean_common_divisor_forward",
    "euclidean_common_divisor_backward",
    "euclidean_common_divisor_iff",
    "euclidean_gcd_step_forward",
    "euclidean_gcd_step_backward",
    "euclidean_gcd_step_iff",
    "euclidean_gcd_step_output_unique",
    "euclidean_gcd_zero_terminal_unique",
    "euclidean_execution_output_unique",
    "euclidean_beta_state_functional",
    "euclidean_trace_prefix_gcd_invariant",
    "euclidean_trace_initial_state_is_gcd",
    "euclidean_trace_terminal_gcd_exists",
    "euclidean_execution_terminal_identified",
    "euclidean_anchored_execution_exists",
    "euclidean_anchored_execution_linear_bound",
    "euclidean_anchored_execution_gcd_correct",
    "euclidean_anchored_execution_state_correct",
)
EXPECTED_ORDERED_NAMES_SHA256 = (
    "723fe350c223cc4b22dbe0f786ab64f72e16e3998fd4314f9ebe6ec84be2b3c0"
)
EXPECTED_COMMAND_COUNTS = (
    18, 17, 19, 19, 25, 16, 16, 25, 25, 11, 28, 40, 84, 52, 25, 38, 31, 34, 11, 16
)
EXPECTED_PROOF_NODES = (
    44, 41, 45, 45, 61, 41, 41, 61, 29, 30, 32, 63, 168, 115, 27, 80, 41, 46, 28, 33
)
EXPECTED_PROOF_DEPTHS = (
    27, 25, 27, 27, 23, 25, 25, 23, 20, 17, 18, 25, 54, 33, 21, 26, 21, 22, 17, 21
)
EXPECTED_STATEMENT_SHA256 = {
    "euclidean_divisor_remainder_transport": "d1c3df55512fe0ed672f17a44e940037877e0fb8a39aed545b5f53b8fc2906e1",
    "euclidean_divisor_dividend_transport": "5dea8411de137ecdbb703c33d6c749def4c92ad699c18e51d7e35ecc8e5fe565",
    "euclidean_common_divisor_forward": "22390968046d5da838e0a850a1ac8219c43e6bd9278ae246728b6def51453026",
    "euclidean_common_divisor_backward": "5660aebddc66face12031640b25796cb4715f2f49b3f9a21d5dd2635d65b8dda",
    "euclidean_common_divisor_iff": "0c5e056afa412d321289bf070c293c57eabba2b940be16b556a7cae1442db449",
    "euclidean_gcd_step_forward": "c137cdb66c042b917f27037d7a7300f421aa2bf6689d0de3f34f5194504eb0c2",
    "euclidean_gcd_step_backward": "3d0d04f0f39be1948ed6e522cf84eb597117948bd6f7a2ae6b9dbcec62a755ad",
    "euclidean_gcd_step_iff": "0cd9e188122cf50fa96288705e9cfe3ada3993b775c3394f0a71e6f14892a3bc",
    "euclidean_gcd_step_output_unique": "481d89f0da3aade6b5d4eb823bedcd70cdfa906b1b431613bab45eb651920b32",
    "euclidean_gcd_zero_terminal_unique": "b6cb135be382616d2c6e327c6f906d9de2b82d000c6de7368b828d26b2b2a90f",
    "euclidean_execution_output_unique": "1c985026e673c7124113792ffc0d053669993b585b9dc41e6d813b9b6a0c5c04",
    "euclidean_beta_state_functional": "3b144a99ef1282f7b9097b8c9093a78363a11717be1cd1b40e803c497b1d5b6f",
    "euclidean_trace_prefix_gcd_invariant": "18c098b0ebf2ba96a309b3d27c464e78eb2f99965b96e4d00b3ac632ac4cc60b",
    "euclidean_trace_initial_state_is_gcd": "e4819751807259a1c534a96123e90acceabdb55853df30bedf162dd116da6ce8",
    "euclidean_trace_terminal_gcd_exists": "66cf940ab57702728d12727ad01c75ebfd27a35dcd3a7e254917e66bf3bac9f5",
    "euclidean_execution_terminal_identified": "2b051e092e5b38f1caf67f94722b9b21c844ee2c9fd8b36f805b5f6db7bfbc9d",
    "euclidean_anchored_execution_exists": "fa82bf6592c70a883cf31cb31a3ade3379bbfb4c1d55dd314682deb680ce8adb",
    "euclidean_anchored_execution_linear_bound": "f14b30ffeb6b2ead02fb92f6518e57b9049e14fe03646208de9819ff84e1675f",
    "euclidean_anchored_execution_gcd_correct": "6ba1a41ef605928fb03faafbff76898f05b9fc2b76e4d3faa9fc5809cdbec782",
    "euclidean_anchored_execution_state_correct": "5dab4edf4d42ec1908c018df15361ca39703b3842f9b953a6761a8209912e03d",
}
EXPECTED_EXTERNAL = {
    "beta_at_unique",
    "divides_linear_step",
    "divides_remainder",
    "euclidean_execution_exists",
    "euclidean_execution_gcd_correct",
    "euclidean_gcd_execution_linear_bound",
    "is_gcd_euclid_backward",
    "is_gcd_euclid_forward",
    "is_gcd_unique",
    "is_gcd_zero_right",
    "le_refl",
    "lt_to_le",
    "pair_code_injective",
}
EXPECTED_CHECKED_OUTSIDE_V21_FRONTIER_CONE = {
    "is_gcd_euclid_backward",
    "is_gcd_unique",
    "pair_code_injective",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_euclidean_gcd_transport_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v21.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def _receipts():
    return replay_candidate_bodies(_rows(), core=_core())


def _row(name: str) -> TheoremSpec:
    return next(row for row in _rows() if row.name == name)


def _available() -> dict[str, TheoremSpec]:
    return _core() | {row.name: row for row in _rows()}


def _certificate(name: str) -> tuple[Proof, object]:
    row = _row(name)
    available = _available()
    target = _closed_formula(row.statement)
    for dependency in reversed(row.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    state = start(target)
    for dependency in row.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in row.script:
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


def test_twenty_exact_candidates_are_frozen_closed_and_dependency_ordered() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert rows == candidate.make_euclidean_gcd_transport_candidate_theorems(TheoremSpec)
    assert sha256("\n".join(row.name for row in rows).encode()).hexdigest() == (
        EXPECTED_ORDERED_NAMES_SHA256
    )
    assert {row.name: sha256(row.statement.encode()).hexdigest() for row in rows} == (
        EXPECTED_STATEMENT_SHA256
    )
    assert sum(len(row.script) for row in rows) == 550
    assert sum(len(row.dependencies) for row in rows) == 32
    seen: set[str] = set()
    for row in rows:
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in v21.ALPHA_EDITION.by_name
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(_core()) | seen
        assert all(
            forbidden not in row.statement
            for forbidden in (
                "IsGCD(", "Euclid(", "Execution(", "Trace(", "BetaAt(",
                "Cell(", "Pair(", "BitLen(", "%", "^",
            )
        )
        assert all("DNE" not in command for command in row.script)
        seen.add(row.name)


def test_all_twenty_dependency_curried_bodies_pass_unchanged_intuitionistic_kernel() -> None:
    receipts = _receipts()
    assert tuple(row.name for row in receipts) == EXPECTED_NAMES
    assert tuple(row.command_count for row in receipts) == EXPECTED_COMMAND_COUNTS
    assert tuple(row.proof_nodes for row in receipts) == EXPECTED_PROOF_NODES
    assert tuple(row.proof_depth for row in receipts) == EXPECTED_PROOF_DEPTHS
    assert sum(row.proof_nodes for row in receipts) == 1071
    assert max(row.proof_nodes for row in receipts) == 168
    assert max(row.proof_depth for row in receipts) == 54
    assert all(row.proof_nodes == row.proof_objects for row in receipts)
    assert all(row.proof_edges + 1 == row.proof_objects for row in receipts)


def test_all_external_dependencies_are_checked_v21_with_honest_artifact_cone() -> None:
    names = set(EXPECTED_NAMES)
    external = {dependency for row in _rows() for dependency in row.dependencies if dependency not in names}
    assert external == EXPECTED_EXTERNAL
    assert all(v21.ALPHA_EDITION.by_name[name].checked_use for name in external)
    advanced = {row.name for row in advanced_layer_closure_plan().rows}
    assert external - advanced == EXPECTED_CHECKED_OUTSIDE_V21_FRONTIER_CONE
    assert len(external & advanced) == 10


@pytest.mark.parametrize(
    ("builder", "arguments", "names"),
    (
        (candidate.euclidean_common_divisor, ("d", "a", "b"), {"d", "a", "b"}),
        (candidate.euclidean_state_at, ("h", "e", "i", "a", "b", "s"), {"h", "e", "i", "a", "b", "s"}),
        (candidate.euclidean_anchored_execution, ("a", "b", "g", "l"), {"a", "b", "g", "l"}),
    ),
)
def test_three_relations_are_hygienic_conservative_and_alpha_invariant(
    builder, arguments: tuple[str, ...], names: set[str]
) -> None:
    first, first_free = parse_formula_with_names(builder(*arguments, tag="first"))
    second, second_free = parse_formula_with_names(builder(*arguments, tag="second"))
    assert set(first_free) == set(second_free) == names
    assert first == second


@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_all_relations_reject_malicious_or_non_identifier_arguments(fragment: str) -> None:
    with pytest.raises(ValueError):
        candidate.euclidean_common_divisor(fragment, "a", "b", tag="safe")
    with pytest.raises(ValueError):
        candidate.euclidean_state_at(fragment, "e", "i", "a", "b", "s", tag="safe")
    with pytest.raises(ValueError):
        candidate.euclidean_anchored_execution(fragment, "b", "g", "l", tag="safe")


@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "x;y"))
def test_all_relations_reject_malicious_binder_tags(fragment: str) -> None:
    with pytest.raises(ValueError):
        candidate.euclidean_common_divisor("d", "a", "b", tag=fragment)
    with pytest.raises(ValueError):
        candidate.euclidean_state_at("h", "e", "i", "a", "b", "s", tag=fragment)
    with pytest.raises(ValueError):
        candidate.euclidean_anchored_execution("a", "b", "g", "l", tag=fragment)


def test_all_relations_reject_generated_binder_capture() -> None:
    with pytest.raises(ValueError, match="captures"):
        candidate.euclidean_common_divisor("egt_factor_capture_left", "a", "b", tag="capture")
    with pytest.raises(ValueError, match="captures"):
        candidate.euclidean_state_at(
            "ff_h_cf_egt_capture_state", "e", "i", "a", "b", "s", tag="capture"
        )
    with pytest.raises(ValueError, match="captures"):
        candidate.euclidean_anchored_execution("egt_list_capture", "b", "g", "l", tag="capture")


def test_anchored_execution_is_exact_beta_trace_plus_terminal_state_plus_gcd() -> None:
    actual, free = parse_formula_with_names(
        candidate.euclidean_anchored_execution("a", "b", "g", "l", tag="actual")
    )
    trace = continued_fraction_trace("a", "b", "s", "h", "e", "l", tag="expected")
    state = _state_at_term(
        "h", "e", "0", "g", "0", "0", tag="expected", avoid=("a", "b", "g", "l", "s", "h", "e")
    )
    gcd_relation = is_gcd("g", "a", "b", tag="expected")
    expected, expected_free = parse_formula_with_names(
        f"exists s h e. (({trace}) /\\ (({state}) /\\ ({gcd_relation})))"
    )
    assert set(free) == set(expected_free) == {"a", "b", "g", "l"}
    assert actual == expected


@pytest.mark.parametrize(
    "name",
    (
        candidate.EUCLIDEAN_COMMON_DIVISOR_IFF,
        candidate.EUCLIDEAN_GCD_STEP_IFF,
    ),
)
def test_equivalence_claims_retain_both_constructive_implication_directions(name: str) -> None:
    formula = _closed_formula(_row(name).statement)
    for _ in range(5):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    assert isinstance(formula.antecedent, And)
    assert isinstance(formula.consequent, And)
    assert isinstance(formula.consequent.left, Imp)
    assert isinstance(formula.consequent.right, Imp)


def test_prefix_invariant_quantifies_every_real_beta_transition_and_gcd_state() -> None:
    row = _row(candidate.EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT)
    assert row.dependencies == (
        candidate.EUCLIDEAN_BETA_STATE_FUNCTIONAL,
        "is_gcd_zero_right",
        "lt_to_le",
        "is_gcd_euclid_forward",
    )
    assert "forall i. (exists gap. gap + i = l)" in row.statement
    assert "induction i" in row.script
    assert "specialize htrace_witness_right_right i" in row.script
    assert "specialize is_gcd_euclid_forward g" in row.script
    assert row.script.count("apply euclidean_beta_state_functional") == 1


def test_terminal_identification_is_not_merely_separately_witnessed_gcd() -> None:
    row = _row(candidate.EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED)
    assert row.dependencies == (
        candidate.EUCLIDEAN_TRACE_TERMINAL_GCD_EXISTS,
        "is_gcd_unique",
    )
    assert "specialize is_gcd_unique g" in row.script
    assert row.script.count("rewrite hequal at hterminal_witness_left") == 4
    formula = _closed_formula(row.statement)
    for _ in range(4):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    identified = formula.consequent
    for _ in range(3):
        assert isinstance(identified, Exists)
        identified = identified.body
    assert isinstance(identified, And)
    assert isinstance(identified.left, Exists)
    assert isinstance(identified.right, And)


def test_strongest_endpoint_contains_actual_terminal_gcd_and_linear_budget() -> None:
    row = _row(candidate.EUCLIDEAN_ANCHORED_EXECUTION_LINEAR_BOUND)
    assert row.dependencies == (
        "euclidean_gcd_execution_linear_bound",
        candidate.EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED,
    )
    formula = _closed_formula(row.statement)
    assert isinstance(formula, Forall)
    assert isinstance(formula.body, Forall)
    result = formula.body.body
    assert isinstance(result, Exists)
    assert isinstance(result.body, Exists)
    body = result.body.body
    assert isinstance(body, And)
    anchored = body.left
    for _ in range(3):
        assert isinstance(anchored, Exists)
        anchored = anchored.body
    assert isinstance(anchored, And)
    assert isinstance(anchored.right, And)
    assert isinstance(anchored.right.left, And)  # Actual beta-at terminal state.
    assert isinstance(body.right, Exists)
    assert "gap + l = b" in row.statement
    assert "BitLen" not in row.statement
    assert "BitLen bound remains open" in row.summary


@pytest.mark.parametrize(
    "name",
    (
        candidate.EUCLIDEAN_BETA_STATE_FUNCTIONAL,
        candidate.EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT,
        candidate.EUCLIDEAN_TRACE_INITIAL_STATE_IS_GCD,
        candidate.EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED,
        candidate.EUCLIDEAN_ANCHORED_EXECUTION_LINEAR_BOUND,
    ),
)
def test_important_proofs_are_original_kernel_checked_and_have_no_dne(name: str) -> None:
    proof, target = _certificate(name)
    assert check((), proof, target)
    assert all(not isinstance(node, DNE) for node in _proof_nodes(proof))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_false_conclusions_are_independently_rejected(name: str) -> None:
    row = _row(name)
    forged = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_available())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_authored_proofs_fail_closed(name: str) -> None:
    row = _row(name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_available())


@pytest.mark.parametrize(
    "name",
    (
        candidate.EUCLIDEAN_COMMON_DIVISOR_IFF,
        candidate.EUCLIDEAN_GCD_STEP_IFF,
        candidate.EUCLIDEAN_BETA_STATE_FUNCTIONAL,
        candidate.EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT,
        candidate.EUCLIDEAN_TRACE_INITIAL_STATE_IS_GCD,
        candidate.EUCLIDEAN_TRACE_TERMINAL_GCD_EXISTS,
        candidate.EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED,
        candidate.EUCLIDEAN_ANCHORED_EXECUTION_EXISTS,
        candidate.EUCLIDEAN_ANCHORED_EXECUTION_LINEAR_BOUND,
    ),
)
def test_missing_declared_checked_dependencies_are_rejected(name: str) -> None:
    row = _row(name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, dependencies=row.dependencies[:-1]),), core=_available())


@pytest.mark.parametrize(
    ("name", "command", "replacement"),
    (
        (candidate.EUCLIDEAN_DIVISOR_REMAINDER_TRANSPORT, "exact hstep_left", "refl"),
        (candidate.EUCLIDEAN_DIVISOR_DIVIDEND_TRANSPORT, "exact hr", "refl"),
        (candidate.EUCLIDEAN_BETA_STATE_FUNCTIONAL, "exact hleft", "refl"),
        (candidate.EUCLIDEAN_BETA_STATE_FUNCTIONAL, "exact hpacked", "refl"),
        (candidate.EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT, "exact hstart", "refl"),
        (candidate.EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT, "exact hprevbound", "exists l"),
        (
            candidate.EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT,
            "exact htransition_witness_witness_witness_witness_witness_witness_witness_left",
            "refl",
        ),
        (
            candidate.EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT,
            "exact htransition_witness_witness_witness_witness_witness_witness_witness_right_right_right_left",
            "refl",
        ),
        (
            candidate.EUCLIDEAN_TRACE_INITIAL_STATE_IS_GCD,
            "exact htrace_witness_right_left",
            "refl",
        ),
        (candidate.EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED, "exact hterminal_witness_right", "refl"),
        (candidate.EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED, "exact hterminal_witness_left", "refl"),
        (
            candidate.EUCLIDEAN_ANCHORED_EXECUTION_LINEAR_BOUND,
            "exact hidentified_witness_witness_witness_right",
            "refl",
        ),
        (
            candidate.EUCLIDEAN_ANCHORED_EXECUTION_LINEAR_BOUND,
            "exact euclidean_gcd_execution_linear_bound_witness_witness_right",
            "exists S b",
        ),
    ),
)
def test_mutated_division_beta_state_transition_gcd_or_budget_cannot_pass(
    name: str, command: str, replacement: str
) -> None:
    row = _row(name)
    index = row.script.index(command)
    script = row.script[:index] + (replacement,) + row.script[index + 1 :]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=script),), core=_available())


def test_source_uses_no_host_gcd_calculation_as_proof_authority() -> None:
    source = Path(candidate.__file__).read_text(encoding="utf-8")
    assert "from math import" not in source
    assert "math.gcd" not in source
    assert "certify_euclidean_execution" not in source
    assert "verify_euclidean_execution" not in source
    assert "def make_euclidean_gcd_transport_candidate_theorems" in source


def test_goal_g101_remains_partial_only_for_missing_checked_bit_length_analysis() -> None:
    assert not any("bitlen" in row.name.lower() for row in _core().values())
    assert candidate.EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED in EXPECTED_NAMES
    assert candidate.EUCLIDEAN_ANCHORED_EXECUTION_LINEAR_BOUND in EXPECTED_NAMES
    assert all("BitLen(" not in row.statement for row in _rows())
