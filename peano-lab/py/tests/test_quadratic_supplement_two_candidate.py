"""Focused audit of constructive modulo-eight second-supplement foundations."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.eisenstein_initial_segment_count_candidate import (
    make_eisenstein_initial_segment_count_candidate_theorems,
)
from peano_lab.library.finite_bitcount_complement_candidate import (
    make_finite_bitcount_complement_candidate_theorems,
)
from peano_lab.library.gauss_lemma_bounded_candidate import (
    make_gauss_lemma_bounded_candidate_theorems,
)
from peano_lab.library.gauss_signed_division_alignment_candidate import (
    make_gauss_signed_division_alignment_candidate_theorems,
)
from peano_lab.library.quadratic_supplement_two_candidate import (
    DOUBLING_GAUSS_INITIAL_SEGMENT_COMPLEMENT_GOAL,
    DOUBLING_GAUSS_REFLECTION_COUNT_SHAPE_GOAL,
    make_quadratic_supplement_two_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "eight_mul_eq_double_four",
    "odd_mod_eight_cases",
    "doubling_gauss_count_shape_exists",
    "mod_eight_remainder_unique",
    "mod_eight_good_bad_exclusive",
    "doubling_gauss_even_count_implies_good_mod_eight",
    "doubling_gauss_odd_count_implies_bad_mod_eight",
    "doubling_gauss_count_parity_mod_eight_complete",
    "doubling_floor_below_implies_double_at_most_half",
    "doubling_floor_above_implies_double_above_half",
    "doubling_half_range_below_odd_modulus",
    "reflected_double_above_odd_half",
    "doubling_gauss_initial_segment_complement",
    "doubling_half_decomposition_lower_bound",
    "doubling_gauss_count_shape_from_initial_segment_complement",
    "doubling_gauss_reflection_count_shape",
    "quadratic_supplement_two_conditional_on_gauss_count_shape",
    "odd_prime_strictly_exceeds_two",
    "quadratic_supplement_two_half_complete",
    "quadratic_supplement_two_residue_iff_mod_eight_one_or_seven",
    "quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five",
    "quadratic_supplement_two_complete",
)

EXPECTED_DEPENDENCIES = {
    "eight_mul_eq_double_four": ("mul_assoc",),
    "odd_mod_eight_cases": (
        "parity_cases",
        "mul_add",
        "four_mul_eq_double_double",
        "eight_mul_eq_double_four",
    ),
    "doubling_gauss_count_shape_exists": ("parity_cases",),
    "mod_eight_remainder_unique": ("division_remainder_unique",),
    "mod_eight_good_bad_exclusive": ("mod_eight_remainder_unique",),
    "doubling_gauss_even_count_implies_good_mod_eight": (
        "even_successor_to_odd",
        "mul_add",
        "four_mul_eq_double_double",
        "eight_mul_eq_double_four",
    ),
    "doubling_gauss_odd_count_implies_bad_mod_eight": (
        "odd_successor_to_even",
        "mul_add",
        "four_mul_eq_double_double",
        "eight_mul_eq_double_four",
    ),
    "doubling_gauss_count_parity_mod_eight_complete": (
        "doubling_gauss_even_count_implies_good_mod_eight",
        "doubling_gauss_odd_count_implies_bad_mod_eight",
        "mod_eight_good_bad_exclusive",
        "parity_cases",
    ),
    "doubling_floor_below_implies_double_at_most_half": (
        "mul_le_mul_left",
        "add_succ_left",
    ),
    "doubling_floor_above_implies_double_above_half": (
        "mul_add",
        "add_assoc",
        "add_comm",
        "add_succ_left",
    ),
    "doubling_half_range_below_odd_modulus": ("mul_le_mul_left",),
    "reflected_double_above_odd_half": (
        "add_right_cancel",
        "mul_comm",
        "zero_add",
        "add_assoc",
        "add_comm",
        "add_succ_left",
    ),
    "doubling_gauss_initial_segment_complement": (
        "beta_range_entry_eq",
        "beta_at_unique",
        "eisenstein_initial_segment_decoded_choice",
        "doubling_half_range_below_odd_modulus",
        "odd_signed_division_branch_exact",
        "doubling_floor_above_implies_double_above_half",
        "doubling_floor_below_implies_double_at_most_half",
        "reflected_double_above_odd_half",
        "lt_not_le",
        "zero_add",
        "add_succ_left",
    ),
    "doubling_half_decomposition_lower_bound": (
        "mul_comm",
        "zero_add",
        "add_succ_left",
    ),
    "doubling_gauss_count_shape_from_initial_segment_complement": (
        "doubling_half_decomposition_lower_bound",
        "eisenstein_initial_segment_bit_count_exact",
        "complementary_bit_counts_add_length",
        "mul_comm",
        "zero_add",
        "add_succ_left",
        "add_right_cancel",
    ),
    "doubling_gauss_reflection_count_shape": (
        "parity_cases",
        "eisenstein_initial_segment_prefix_exists",
        "doubling_gauss_initial_segment_complement",
        "doubling_gauss_count_shape_from_initial_segment_complement",
    ),
    "quadratic_supplement_two_conditional_on_gauss_count_shape": (
        "doubling_gauss_count_parity_mod_eight_complete",
    ),
    "odd_prime_strictly_exceeds_two": (
        "nonzero_is_succ",
        "mul_add",
        "zero_add",
    ),
    "quadratic_supplement_two_half_complete": (
        "odd_prime_strictly_exceeds_two",
        "beta_range_exists",
        "bounded_gauss_lemma_complete",
        "doubling_gauss_reflection_count_shape",
        "quadratic_supplement_two_conditional_on_gauss_count_shape",
    ),
    "quadratic_supplement_two_residue_iff_mod_eight_one_or_seven": (
        "quadratic_supplement_two_half_complete",
    ),
    "quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five": (
        "quadratic_supplement_two_half_complete",
    ),
    "quadratic_supplement_two_complete": (
        "quadratic_supplement_two_residue_iff_mod_eight_one_or_seven",
        "quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "eight_mul_eq_double_four": (
        "e855597bfd7ffd5055cad7152ca8f8cc2e9fbb34a97f054f0e53698a730f1df1"
    ),
    "odd_mod_eight_cases": (
        "c5c8e14bd03c8405d805453d74239c312a1920d95fd6d6a042fa419f6a65402a"
    ),
    "doubling_gauss_count_shape_exists": (
        "c6e32e7398f6fead2a77f30f6de95c8ddee60a58bbaafbb3e0a52841354687a5"
    ),
    "mod_eight_remainder_unique": (
        "a28a40170b35f9dd532b0be43b88fbd59ba196554d2791a8fa1933f42ed59568"
    ),
    "mod_eight_good_bad_exclusive": (
        "f2bda38ce48a9c7235a1101a54372e135379f3ff4e6588060a47fee368bfd758"
    ),
    "doubling_gauss_even_count_implies_good_mod_eight": (
        "49010a6533f273d3a2ea04025dcbf1e51239346a1a766bc7a0bb1c556b9ae2c5"
    ),
    "doubling_gauss_odd_count_implies_bad_mod_eight": (
        "9221fcaef856417aef75584dff9989e894bd85c39ec0e6086503cdab7d0063a7"
    ),
    "doubling_gauss_count_parity_mod_eight_complete": (
        "6e9c3f633796505c9621006d86680f2f93cf701e8ab59ac702a30b9e85d55f9c"
    ),
    "doubling_floor_below_implies_double_at_most_half": (
        "f04c55cb31fcec06595f360bc5fe09e4078d5cb063827165a92455231575298b"
    ),
    "doubling_floor_above_implies_double_above_half": (
        "42bdee2de2f17c442bf5083337ded23ba4ce4aec60b55d87eb73a623ddd1bd96"
    ),
    "doubling_half_range_below_odd_modulus": (
        "0ae0029bd0c6412bd8577fbb5a18fa9d40ec6253bdd23341851f6400d5117e2a"
    ),
    "reflected_double_above_odd_half": (
        "b5e1411d4f6027c6456e11b14e209922194b018709b2edb5bfc839d13fb8e015"
    ),
    "doubling_gauss_initial_segment_complement": (
        "4e82078fb10ab261cc9516669ba89357c4c4335a20f074465a5e069cc207bd5b"
    ),
    "doubling_half_decomposition_lower_bound": (
        "f058225358138197ec1d136234b807bee2a64a55bee8cfdcd589a341653a9c58"
    ),
    "doubling_gauss_count_shape_from_initial_segment_complement": (
        "f7a938a7db1dcd6e211ac6460407b36e194cd9e752b65f18e152b3706404e9a3"
    ),
    "doubling_gauss_reflection_count_shape": (
        "8681aaac3169a14ae1dae90e15bf11ed5fed927cfd16cee2b4bed91326c796bd"
    ),
    "quadratic_supplement_two_conditional_on_gauss_count_shape": (
        "65abe8256615b1b0e6d5a71c4074c9c44d8d450957edf30cda4f59b253db2471"
    ),
    "odd_prime_strictly_exceeds_two": (
        "9a4579fcc57264c4bc27677ef42c2a28e2e983fef86cddd901c2029c185600a6"
    ),
    "quadratic_supplement_two_half_complete": (
        "62eb85561c5000ec0ac4d9dd2a16d743f1358de99cfd9eb05b0cead67a01167d"
    ),
    "quadratic_supplement_two_residue_iff_mod_eight_one_or_seven": (
        "df55b1cd3398dc6bf064dc8957ea318ad311b99ebf1b3ecffb804b463c1df532"
    ),
    "quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five": (
        "dd9b0415da856a4198e7eb027d2c055549bc34588378d301a952748eaeb80877"
    ),
    "quadratic_supplement_two_complete": (
        "146a886f8f3a54d358321b54faf68a591362016e86139bd487a5496c7af74034"
    ),
}

# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_BODY_RECEIPTS = {
    "eight_mul_eq_double_four": (1, 6, 102, 25, 102, 101, 0),
    "odd_mod_eight_cases": (4, 47, 428, 53, 363, 427, 65),
    "doubling_gauss_count_shape_exists": (1, 13, 19, 11, 19, 18, 0),
    "mod_eight_remainder_unique": (1, 23, 26, 22, 26, 25, 0),
    "mod_eight_good_bad_exclusive": (1, 104, 484, 38, 484, 483, 0),
    "doubling_gauss_even_count_implies_good_mod_eight": (
        4,
        32,
        229,
        54,
        198,
        228,
        31,
    ),
    "doubling_gauss_odd_count_implies_bad_mod_eight": (
        4,
        32,
        229,
        44,
        198,
        228,
        31,
    ),
    "doubling_gauss_count_parity_mod_eight_complete": (
        4,
        60,
        132,
        31,
        132,
        131,
        0,
    ),
    "doubling_floor_below_implies_double_at_most_half": (
        2,
        21,
        46,
        18,
        46,
        45,
        0,
    ),
    "doubling_floor_above_implies_double_above_half": (
        4,
        17,
        123,
        29,
        109,
        122,
        14,
    ),
    "doubling_half_range_below_odd_modulus": (1, 18, 34, 16, 34, 33, 0),
    "reflected_double_above_odd_half": (6, 46, 97, 28, 96, 96, 1),
    "doubling_gauss_initial_segment_complement": (
        11,
        167,
        296,
        57,
        296,
        295,
        0,
    ),
    "doubling_half_decomposition_lower_bound": (3, 25, 78, 19, 74, 77, 4),
    "doubling_gauss_count_shape_from_initial_segment_complement": (
        7,
        80,
        160,
        37,
        156,
        159,
        4,
    ),
    "doubling_gauss_reflection_count_shape": (4, 57, 68, 42, 68, 67, 0),
    "quadratic_supplement_two_conditional_on_gauss_count_shape": (
        1,
        41,
        82,
        23,
        82,
        81,
        0,
    ),
    "odd_prime_strictly_exceeds_two": (3, 20, 100, 24, 93, 99, 7),
    "quadratic_supplement_two_half_complete": (5, 71, 116, 36, 116, 115, 0),
    "quadratic_supplement_two_residue_iff_mod_eight_one_or_seven": (
        1,
        14,
        17,
        13,
        17,
        16,
        0,
    ),
    "quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five": (
        1,
        14,
        17,
        13,
        17,
        16,
        0,
    ),
    "quadratic_supplement_two_complete": (2, 12, 24, 11, 24, 23, 0),
}

_BODY_DEADLINE_SECONDS = 45


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_quadratic_supplement_two_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_eisenstein_initial_segment_count_candidate_theorems,
        make_finite_bitcount_complement_candidate_theorems,
        make_gauss_signed_division_alignment_candidate_theorems,
        make_gauss_lemma_bounded_candidate_theorems,
    ):
        core.update((item.name, item) for item in factory(TheoremSpec))
    return core


def _available_specs() -> dict[str, TheoremSpec]:
    return _dependency_core() | {
        item.name: item for item in _candidate_specs()
    }


def _curried_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


@lru_cache(maxsize=None)
def _body_certificate(name: str):
    item = next(item for item in _candidate_specs() if item.name == name)
    target = _curried_target(item)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _walk_unique(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        for item in fields(current):
            child = getattr(current, item.name)
            if isinstance(child, Proof):
                pending.append(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"second-supplement replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_second_supplement_factory_is_exact_deterministic_and_isolated() -> None:
    first = _candidate_specs()
    second = make_quadratic_supplement_two_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    assert "quadratic_supplement_two_candidate" not in Path(
        theorem_registry.__file__
    ).read_text()


def test_second_supplement_contracts_are_closed_expanded_native_ha() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "Even(",
                "Odd(",
                "ModEq(",
                "Prime(",
                "QRes(",
                "%",
                "^",
                "∣",
                "≡",
                "↔",
            )
        )

    odd_cases = _candidate_specs()[1].statement
    for residue in (1, 3, 5, 7):
        assert f"+ {residue}" in odd_cases
    positive, negative, complete = _candidate_specs()[-3:]
    for endpoint in (positive, negative, complete):
        assert endpoint.statement.startswith("forall p. (")
        assert "p = 2 * qst_odd_modulus + 1" in endpoint.statement
        assert "qst_root_two * qst_root_two" in endpoint.statement
        assert "= 2 + p * qst_mod_right_two" in endpoint.statement
        assert "h = 2 * e" not in endpoint.statement
        assert "e = S qst_count_half_shape" not in endpoint.statement
    assert "+ 1" in positive.statement and "+ 7" in positive.statement
    assert "+ 3" in negative.statement and "+ 5" in negative.statement


def test_second_supplement_endpoint_is_unconditional_and_count_bridge_is_proved() -> None:
    table = {item.name: item for item in _candidate_specs()}
    conditional = table["quadratic_supplement_two_conditional_on_gauss_count_shape"]
    endpoint = table["quadratic_supplement_two_complete"]

    assert conditional.dependencies == (
        "doubling_gauss_count_parity_mod_eight_complete",
    )
    assert conditional.statement.count("h = 2 * e") == 1
    assert conditional.statement.count("e = S qst_count_half_shape") == 1
    assert conditional.statement.count("qst_root_two * qst_root_two") == 8
    assert endpoint.dependencies == (
        "quadratic_supplement_two_residue_iff_mod_eight_one_or_seven",
        "quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five",
    )
    assert "h = 2 * e" not in endpoint.statement
    assert "e = S qst_count_half_shape" not in endpoint.statement
    assert table["quadratic_supplement_two_half_complete"].dependencies == (
        "odd_prime_strictly_exceeds_two",
        "beta_range_exists",
        "bounded_gauss_lemma_complete",
        "doubling_gauss_reflection_count_shape",
        "quadratic_supplement_two_conditional_on_gauss_count_shape",
    )


def test_second_supplement_alignment_goals_are_exact_closed_and_proved() -> None:
    complement = DOUBLING_GAUSS_INITIAL_SEGMENT_COMPLEMENT_GOAL
    count_shape = DOUBLING_GAUSS_REFLECTION_COUNT_SHAPE_GOAL

    assert sha256(complement.encode()).hexdigest() == (
        "4e82078fb10ab261cc9516669ba89357c4c4335a20f074465a5e069cc207bd5b"
    )
    assert sha256(count_shape.encode()).hexdigest() == (
        "8681aaac3169a14ae1dae90e15bf11ed5fed927cfd16cee2b4bed91326c796bd"
    )
    assert len(complement) == 4283
    assert len(count_shape) == 5556
    assert complement.startswith("forall p h a b c mb mc sb sc ib ic k.")
    assert count_shape.startswith("forall p h a b c mb mc sb sc e.")
    assert "a = 2" in complement
    assert "a = 2" in count_shape
    assert "((s = 0 /\\ t = 1) \\/ (s = 1 /\\ t = 0))" in complement
    assert "h = 2 * e" in count_shape

    table = {item.name: item for item in _candidate_specs()}
    assert table["doubling_gauss_initial_segment_complement"].statement == complement
    assert table["doubling_gauss_reflection_count_shape"].statement == count_shape
    for goal in (complement, count_shape):
        formula, free_names = parse_formula_with_names(goal)
        assert not free_names
        assert formula == parse_formula(goal)
        assert formula == _closed_formula(goal)
        assert all(
            token not in goal
            for token in (
                "BetaAt(",
                "BitCount(",
                "HalfRange(",
                "SignedHalfPrefix(",
                "QRes(",
                "<=",
                "<",
                "%",
            )
        )


def test_second_supplement_scripts_are_constructive_and_explicit() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)

    assert "apply division_remainder_unique" in commands
    assert "apply even_successor_to_odd" in commands
    assert "apply odd_successor_to_even" in commands
    assert "apply eisenstein_initial_segment_bit_count_exact" in commands
    assert "apply complementary_bit_counts_add_length" in commands
    assert "apply odd_signed_division_branch_exact" in commands
    assert "apply bounded_gauss_lemma_complete" in commands
    assert "apply doubling_gauss_reflection_count_shape" in commands
    assert "specialize parity_cases x" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_second_supplement_bodies_kernel_check_within_laptop_limit() -> None:
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_dependency_core()
        )
    observed = {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    }
    assert observed == EXPECTED_BODY_RECEIPTS


def test_second_supplement_certificates_are_dne_free_and_mutation_sensitive() -> None:
    for item in _candidate_specs():
        certificate, target = _body_certificate(item.name)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))

    table = {item.name: item for item in _candidate_specs()}
    mutations = (
        (
            table["odd_mod_eight_cases"],
            "p = 8 * qst_mod_eight_one + 1",
            "p = 8 * qst_mod_eight_one + 2",
        ),
        (
            table["doubling_gauss_even_count_implies_good_mod_eight"],
            "p = 8 * qst_mod_eight_modulus_one + 1",
            "p = 8 * qst_mod_eight_modulus_one + 3",
        ),
        (
            table["quadratic_supplement_two_conditional_on_gauss_count_shape"],
            "p = 8 * qst_mod_eight_modulus_one + 1",
            "p = 8 * qst_mod_eight_modulus_one + 3",
        ),
        (
            table["quadratic_supplement_two_residue_iff_mod_eight_one_or_seven"],
            "p = 8 * qst_mod_eight_modulus_one + 1",
            "p = 8 * qst_mod_eight_modulus_one + 3",
        ),
        (
            table["quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five"],
            "p = 8 * qst_mod_eight_modulus_three + 3",
            "p = 8 * qst_mod_eight_modulus_three + 1",
        ),
        (
            table["quadratic_supplement_two_complete"],
            "p = 8 * qst_mod_eight_modulus_one + 1",
            "p = 8 * qst_mod_eight_modulus_one + 3",
        ),
    )
    for item, correct, false in mutations:
        assert correct in item.statement
        certificate, _ = _body_certificate(item.name)
        false_statement = item.statement.replace(correct, false)
        assert not check((), certificate, _curried_target(item, false_statement))


@pytest.mark.parametrize(
    "prime_value",
    (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59),
)
def test_second_supplement_matches_actual_doubling_counts_and_roots(
    prime_value: int,
) -> None:
    half = (prime_value - 1) // 2
    reflection_count = sum(2 * value > half for value in range(1, half + 1))
    roots = tuple(
        root for root in range(prime_value) if (root * root) % prime_value == 2
    )

    assert reflection_count == (half + 1) // 2
    assert half == 2 * reflection_count or half == 2 * (reflection_count - 1) + 1
    assert (reflection_count % 2 == 0) is (prime_value % 8 in (1, 7))
    assert (reflection_count % 2 == 1) is (prime_value % 8 in (3, 5))
    assert bool(roots) is (prime_value % 8 in (1, 7))
    if roots:
        assert len(roots) == 2
        assert sum(roots) == prime_value
