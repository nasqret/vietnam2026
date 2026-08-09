"""Focused native audit for the first Bertrand power-valuation tranche."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from itertools import product
from time import perf_counter

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.bertrand_power_valuation_candidate import (
    at_most,
    bounded_power_valuation,
    divides,
    make_bertrand_power_valuation_candidate_theorems,
    power_divides,
    power_valuation,
    prime_power_valuation,
)
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "power_divides_decidable",
    "power_divides_zero",
    "bounded_power_valuation_search",
    "bounded_power_valuation_exists",
    "power_valuation_exists",
    "power_valuation_functional",
    "power_valuation_power_divides",
    "power_valuation_dominates",
    "prime_power_valuation_exists",
    "prime_power_valuation_functional",
)
EXPECTED_DEPENDENCIES = {
    "power_divides_decidable": ("pow_exists", "multiple_decidable", "pow_functional"),
    "power_divides_zero": ("pow_exists", "pow_zero", "one_multiple"),
    "bounded_power_valuation_search": (
        "power_divides_decidable",
        "le_zero",
        "le_refl",
        "le_eq_or_lt",
        "le_of_succ_le_succ",
        "le_succ",
    ),
    "bounded_power_valuation_exists": (
        "bounded_power_valuation_search",
        "power_divides_zero",
        "zero_le",
    ),
    "power_valuation_exists": ("bounded_power_valuation_exists",),
    "power_valuation_functional": ("le_antisymm",),
    "power_valuation_power_divides": (),
    "power_valuation_dominates": (),
    "prime_power_valuation_exists": ("power_valuation_exists",),
    "prime_power_valuation_functional": ("power_valuation_functional",),
}
EXPECTED_STATEMENT_SHA256 = {
    "power_divides_decidable": "056bf86316331243e9372e8b59cd02ca2f4a88cee0f43b5900e299ef979e227e",
    "power_divides_zero": "c1da6eefcb1b59ca8732c537ab4f565427595dfbd4c38d9b0ff5352bf799b8ef",
    "bounded_power_valuation_search": "1b8ba19947c6b40b4e3d2bbde7f110eda02a7fcc4e23bd247d13fac51e6878f5",
    "bounded_power_valuation_exists": "e3360e9cfb622363275168e8f789dc68fdbe6996c5e646ea21a1afff5e993829",
    "power_valuation_exists": "e1b175e27a5a13c926aa2215122a3a89d7a9d85fca190895f73279a3b993c306",
    "power_valuation_functional": "8aaf4591d4325dfb55dbc96098bab4be710ec0b047d37273c4a154f06a96f3cf",
    "power_valuation_power_divides": "e6209bee9e63324cdf55b24e1fe19e6e140c7f658ede37c16ed8aa46e2de12d5",
    "power_valuation_dominates": "11940140cf2fb3b274b4bc444e9c547d88c09813bdbae6245dda5ef1e4f77487",
    "prime_power_valuation_exists": "0072bb92c337a4ae40408e09ae3dfbb9fc99ee0d4bdb407999eb3c95009c7064",
    "prime_power_valuation_functional": "672f01d0365b8a359b58562b095b3b7a4f5155c696111e0986802aef752daee5",
}
EXPECTED_STATEMENT_LENGTHS = {
    "power_divides_decidable": 5851,
    "power_divides_zero": 2619,
    "bounded_power_valuation_search": 10871,
    "bounded_power_valuation_exists": 7611,
    "power_valuation_exists": 7955,
    "power_valuation_functional": 18144,
    "power_valuation_power_divides": 11027,
    "power_valuation_dominates": 11889,
    "prime_power_valuation_exists": 10587,
    "prime_power_valuation_functional": 22954,
}
EXPECTED_BODY_RECEIPTS = {
    "power_divides_decidable": (3, 33, 38, 20, 38, 37, 0),
    "power_divides_zero": (3, 22, 26, 18, 26, 25, 0),
    "bounded_power_valuation_search": (6, 122, 162, 28, 162, 161, 0),
    "bounded_power_valuation_exists": (3, 24, 28, 14, 28, 27, 0),
    "power_valuation_exists": (1, 6, 16, 10, 16, 15, 0),
    "power_valuation_functional": (1, 25, 34, 14, 34, 33, 0),
    "power_valuation_power_divides": (0, 7, 21, 13, 21, 20, 0),
    "power_valuation_dominates": (0, 12, 24, 16, 24, 23, 0),
    "prime_power_valuation_exists": (1, 15, 15, 10, 15, 14, 0),
    "prime_power_valuation_functional": (1, 15, 44, 26, 44, 43, 0),
}
EXPECTED_CLOSURE_RECEIPTS = {
    "power_divides_decidable": (63931, 89, 5537, 5789, 253),
    "power_divides_zero": (61118, 89, 5037, 5279, 243),
    "bounded_power_valuation_search": (64301, 90, 5699, 5956, 258),
    "bounded_power_valuation_exists": (125454, 91, 5862, 6123, 262),
    "power_valuation_exists": (125470, 92, 5878, 6139, 262),
    "power_valuation_functional": (252, 30, 243, 251, 9),
    "power_valuation_power_divides": (21, 13, 21, 20, 0),
    "power_valuation_dominates": (24, 16, 24, 23, 0),
    "prime_power_valuation_exists": (125485, 93, 5893, 6154, 262),
    "prime_power_valuation_functional": (296, 31, 287, 295, 9),
}
_BODY_DEADLINE_SECONDS = 60
_CLOSURE_DEADLINE_SECONDS = 60


@dataclass(frozen=True)
class _Checked:
    formula: Formula
    certificate: Proof


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_valuation_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for field in fields(proof):
        child = getattr(proof, field.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _deadline(seconds: int, label: str):
    def expired(_signum, _frame):
        raise TimeoutError(f"{label} exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _curried_body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = dict(_specs_by_name()) | {spec.name: spec for spec in _candidate_specs()}
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


@lru_cache(maxsize=1)
def _closed_candidates() -> tuple[tuple[TheoremSpec, _Checked], ...]:
    public = dict(_specs_by_name())
    local = {spec.name: spec for spec in _candidate_specs()}

    @lru_cache(maxsize=None)
    def close(name: str) -> _Checked:
        if name in public:
            theorem = replay(name)
            return _Checked(theorem.formula, theorem.certificate)
        item = local[name]
        certificate, _ = _curried_body(item)
        body = certificate
        for _dependency in item.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        formula = _closed_formula(item.statement)
        for dependency in reversed(item.dependencies):
            checked_dependency = close(dependency)
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )
        assert check((), body, formula)
        return _Checked(formula, body)

    return tuple((item, close(item.name)) for item in _candidate_specs())


def _mutate_cut_at(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(certificate, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(certificate, body=_mutate_cut_at(certificate.body, index - 1))


def test_power_valuation_factory_is_exact_ordered_and_isolated() -> None:
    specs = _candidate_specs()
    assert make_bertrand_power_valuation_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256
    assert {item.name: len(item.statement) for item in specs} == EXPECTED_STATEMENT_LENGTHS
    public = _specs_by_name()
    assert all(item.name not in public for item in specs)


def test_power_valuation_surfaces_are_hygienic_expanded_and_semantic() -> None:
    surfaces = (
        (lambda tag: at_most("e", "B", tag=tag), {"e", "B"}),
        (lambda tag: divides("r", "a", tag=tag), {"r", "a"}),
        (lambda tag: power_divides("p", "e", "a", tag=tag), {"p", "e", "a"}),
        (
            lambda tag: bounded_power_valuation("p", "a", "B", "e", tag=tag),
            {"p", "a", "B", "e"},
        ),
        (lambda tag: power_valuation("p", "a", "e", tag=tag), {"p", "a", "e"}),
        (
            lambda tag: prime_power_valuation("p", "a", "e", tag=tag),
            {"p", "a", "e"},
        ),
    )
    for build, expected_free in surfaces:
        left = build("alpha_left")
        right = build("alpha_right")
        assert left != right
        assert parse_formula(left) == parse_formula(right)
        _, free_names = parse_formula_with_names(left)
        assert set(free_names) == expected_free
        assert all(
            token not in left
            for token in ("Pow(", "Dvd(", "PVal(", "^", "<=", "∣")
        )

    with pytest.raises(ValueError, match="Peano identifier"):
        power_divides("p + 1", "e", "a", tag="bad_base")
    with pytest.raises(ValueError, match="binder tag"):
        power_valuation("p", "a", "e", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        at_most("bpv_gap_capture", "B", tag="capture")

    def nat_divides(divisor: int, value: int) -> bool:
        return value == 0 if divisor == 0 else value % divisor == 0

    for base, value, bound in product(range(5), range(10), range(7)):
        admissible = [
            exponent
            for exponent in range(bound + 1)
            if nat_divides(base**exponent, value)
        ]
        assert admissible
        selected = max(admissible)
        assert selected <= bound
        assert nat_divides(base**selected, value)
        assert all(exponent <= selected for exponent in admissible)


def test_power_valuation_contracts_and_bodies_are_native_constructive_and_exact() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement) == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("Pow(", "Dvd(", "PVal(", "Prime(", "^", "<=", "∣")
        )

    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in commands
    )
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "classical", "by_contra", "sorry")
    )

    started = perf_counter()
    with _deadline(_BODY_DEADLINE_SECONDS, "valuation body replay"):
        receipts = replay_candidate_bodies(_candidate_specs(), core=dict(_specs_by_name()))
    assert perf_counter() - started < _BODY_DEADLINE_SECONDS
    assert {
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
    } == EXPECTED_BODY_RECEIPTS


def test_power_valuation_rejects_false_conclusions_and_every_direct_cut_mutation() -> None:
    available = dict(_specs_by_name()) | {spec.name: spec for spec in _candidate_specs()}
    for item in _candidate_specs():
        false_item = replace(item, statement="forall z. z = S z")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((false_item,), core=available)

    with _deadline(_CLOSURE_DEADLINE_SECONDS, "valuation closure mutation audit"):
        closed = _closed_candidates()
    for item, theorem in closed:
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        for index, dependency in enumerate(item.dependencies):
            mutated = _mutate_cut_at(theorem.certificate, index)
            assert not check((), mutated, theorem.formula), (
                f"accepted mutated edge {item.name}->{dependency}"
            )


def test_power_valuation_empty_context_closure_is_within_current_use_limits() -> None:
    with _deadline(_CLOSURE_DEADLINE_SECONDS, "valuation closure feasibility"):
        closed = _closed_candidates()
    observed = {}
    for item, theorem in closed:
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        observed[item.name] = (nodes, depth, objects, edges, reused)
        assert check((), theorem.certificate, theorem.formula)
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert depth <= MAX_USE_PROOF_DEPTH
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS
        print(
            "BERTRAND VALUATION CLOSURE FEASIBILITY "
            f"name={item.name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused}",
            flush=True,
        )
    assert observed == EXPECTED_CLOSURE_RECEIPTS
