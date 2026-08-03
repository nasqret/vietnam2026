"""WMI-only five-gate audit for Gauss magnitude permutation candidates."""

from __future__ import annotations

import gc
import resource
import signal
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
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
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.gauss_magnitude_permutation_candidate import (
    magnitude_range_prefix,
    make_gauss_magnitude_permutation_candidate_theorems,
    predecessor_recode_prefix,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "gauss_signed_half_magnitude_range",
    "prime_scaled_same_target_unique",
    "gauss_same_sign_scaled_source_unique",
    "gauss_mixed_sign_scaled_source_impossible",
    "gauss_signed_half_magnitude_injective",
    "beta_magnitude_predecessor_recode_exists",
    "gauss_signed_half_predecessor_recode_exists",
    "beta_magnitude_predecessor_recode_reflect",
    "beta_magnitude_predecessor_recode_bounded",
    "beta_magnitude_predecessor_recode_injective",
    "beta_magnitude_predecessor_recode_surjective",
)

EXPECTED_DEPENDENCIES = {
    "gauss_signed_half_magnitude_range": (),
    "prime_scaled_same_target_unique": (
        "mod_eq_symm",
        "mod_eq_trans",
        "prime_mod_cancel",
        "mod_eq_bounded_unique",
    ),
    "gauss_same_sign_scaled_source_unique": (
        "prime_scaled_same_target_unique",
    ),
    "gauss_mixed_sign_scaled_source_impossible": (
        "mod_eq_add",
        "mul_add",
        "mul_succ_left",
        "add_comm",
        "dvd_to_mod_zero",
        "mod_eq_trans",
        "prime_mod_cancel",
        "prime_nonzero",
        "one_le_of_ne_zero",
        "mod_eq_bounded_unique",
    ),
    "gauss_signed_half_magnitude_injective": (
        "beta_at_unique",
        "beta_half_range_entry_bounds",
        "beta_range_entry_eq",
        "add_succ_left",
        "zero_add",
        "add_le_add_right",
        "add_le_add_left",
        "le_trans",
        "mul_succ_left",
        "mul_zero_left",
        "lt_of_le_of_lt",
        "add_eq_zero_left",
        "add_comm",
        "gauss_same_sign_scaled_source_unique",
        "gauss_mixed_sign_scaled_source_impossible",
        "beta_range_injective",
    ),
    "beta_magnitude_predecessor_recode_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        "ne_zero_of_one_le",
        "nonzero_is_succ",
        "finite_lt_succ_eq_or_lt",
        "beta_at_unique",
        "succ_injective",
        "beta_prefix_extend",
    ),
    "gauss_signed_half_predecessor_recode_exists": (
        "gauss_signed_half_magnitude_range",
        "beta_magnitude_predecessor_recode_exists",
    ),
    "beta_magnitude_predecessor_recode_reflect": (
        "ne_zero_of_one_le",
        "nonzero_is_succ",
        "beta_at_unique",
    ),
    "beta_magnitude_predecessor_recode_bounded": (
        "ne_zero_of_one_le",
        "nonzero_is_succ",
    ),
    "beta_magnitude_predecessor_recode_injective": (
        "beta_magnitude_predecessor_recode_reflect",
    ),
    "beta_magnitude_predecessor_recode_surjective": (
        "beta_magnitude_predecessor_recode_bounded",
        "beta_magnitude_predecessor_recode_injective",
        "finite_bounded_injective_surjective",
    ),
}

EXPECTED_CORE_BOUNDARY = (
    "mod_eq_symm",
    "mod_eq_trans",
    "prime_mod_cancel",
    "mod_eq_bounded_unique",
    "mod_eq_add",
    "mul_add",
    "mul_succ_left",
    "add_comm",
    "dvd_to_mod_zero",
    "prime_nonzero",
    "one_le_of_ne_zero",
    "beta_at_unique",
    "beta_half_range_entry_bounds",
    "beta_range_entry_eq",
    "add_succ_left",
    "zero_add",
    "add_le_add_right",
    "add_le_add_left",
    "le_trans",
    "mul_zero_left",
    "lt_of_le_of_lt",
    "add_eq_zero_left",
    "beta_range_injective",
    "add_eq_zero_right",
    "succ_ne_zero",
    "le_succ",
    "le_refl",
    "ne_zero_of_one_le",
    "nonzero_is_succ",
    "finite_lt_succ_eq_or_lt",
    "succ_injective",
    "beta_prefix_extend",
    "finite_bounded_injective_surjective",
)

EXPECTED_BODY_METRICS = {
    "gauss_signed_half_magnitude_range": (39, 25),
    "prime_scaled_same_target_unique": (48, 24),
    "gauss_same_sign_scaled_source_unique": (96, 34),
    "gauss_mixed_sign_scaled_source_impossible": (169, 50),
    "gauss_signed_half_magnitude_injective": (625, 69),
    "beta_magnitude_predecessor_recode_exists": (157, 45),
    "gauss_signed_half_predecessor_recode_exists": (31, 25),
    "beta_magnitude_predecessor_recode_reflect": (87, 30),
    "beta_magnitude_predecessor_recode_bounded": (48, 20),
    "beta_magnitude_predecessor_recode_injective": (60, 31),
    "beta_magnitude_predecessor_recode_surjective": (39, 21),
}

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_CANDIDATE_SOURCE = _SOURCE_ROOT / "gauss_magnitude_permutation_candidate.py"
_BODY_PREFLIGHT_SECONDS = 60


@dataclass(frozen=True)
class _Checked:
    formula: Formula
    certificate: Proof


@dataclass(frozen=True)
class _PassReceipt:
    duration_seconds: float
    peak_rss_kib: int
    peak_rss_growth_kib: int


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_magnitude_permutation_candidate_theorems(TheoremSpec)


def _spec_digest(spec: TheoremSpec) -> str:
    payload = "\x1f".join(
        (
            spec.name,
            spec.statement,
            "\x1e".join(spec.script),
            "\x1e".join(spec.dependencies),
        )
    )
    return sha256(payload.encode()).hexdigest()


def _graph_digest(specs: tuple[TheoremSpec, ...]) -> str:
    return sha256("\x1c".join(_spec_digest(spec) for spec in specs).encode()).hexdigest()


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"candidate body preflight exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@lru_cache(maxsize=1)
def _body_receipts():
    started = perf_counter()
    with _body_deadline(_BODY_PREFLIGHT_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs())
    return receipts, perf_counter() - started


def _fresh_replayer():
    specs = _candidate_specs()
    core = _specs_by_name()
    local = {spec.name: spec for spec in specs}

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        if name in core:
            checked = replay(name)
            return _Checked(checked.formula, checked.certificate)

        spec = local[name]
        formula = _closed_formula(spec.statement)
        target = formula
        for dependency in reversed(spec.dependencies):
            dependency_spec = local.get(dependency) or core[dependency]
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            tactic, args = _primitive(command)
            state = apply_tactic(state, tactic, args)
        certificate = checked_final(state, target)

        body = certificate
        for _ in spec.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency in reversed(spec.dependencies):
            checked_dependency = run(dependency)
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )
        assert check((), body, formula)
        return _Checked(formula, body)

    return specs, local, run


def _cold_rows():
    started = perf_counter()
    starting_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, local, run = _fresh_replayer()
    checked: dict[str, _Checked] = {}
    rows = []
    for spec in specs:
        theorem = run(spec.name)
        checked[spec.name] = theorem
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS
        assert depth <= MAX_USE_PROOF_DEPTH
        rows.append(
            (
                spec.name,
                nodes,
                depth,
                objects,
                edges,
                reused,
                cuts,
                len(spec.statement),
                _spec_digest(spec),
            )
        )
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt = _PassReceipt(
        duration_seconds=perf_counter() - started,
        peak_rss_kib=peak,
        peak_rss_growth_kib=max(0, peak - starting_peak),
    )
    return specs, checked, tuple(rows), local, receipt


@lru_cache(maxsize=1)
def _discovery_runs():
    first = _cold_rows()
    first_rows = first[2]
    first_receipt = first[4]
    del first
    gc.collect()
    second = _cold_rows()
    assert second[2] == first_rows
    return second[:4] + ((first_receipt, second[4]),)


def _assert_cut_spine(certificate: Proof, spec: TheoremSpec, local) -> None:
    body = certificate
    core = _specs_by_name()
    for dependency in spec.dependencies:
        assert type(body) is Cut
        dependency_spec = local.get(dependency) or core[dependency]
        expected = _closed_formula(dependency_spec.statement)
        assert body.proposition == expected
        assert check((), body.lemma, expected)
        body = body.body


def _mutate_cut_at(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(certificate, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(certificate, body=_mutate_cut_at(certificate.body, index - 1))


def wmi_receipt_metadata() -> dict[str, object]:
    body_receipts, body_seconds = _body_receipts()
    specs, _, rows, _, passes = _discovery_runs()
    return {
        "body_preflight_limit_seconds": _BODY_PREFLIGHT_SECONDS,
        "body_preflight_seconds": body_seconds,
        "body_receipts": [asdict(receipt) for receipt in body_receipts],
        "candidate_source_sha256": sha256(_CANDIDATE_SOURCE.read_bytes()).hexdigest(),
        "candidates": [
            {
                "name": row[0],
                "nodes": row[1],
                "depth": row[2],
                "objects": row[3],
                "edges": row[4],
                "reused": row[5],
                "cuts": row[6],
                "statement_length": row[7],
                "spec_sha256": row[8],
            }
            for row in rows
        ],
        "discovery_passes": [asdict(receipt) for receipt in passes],
        "graph_sha256": _graph_digest(specs),
        "recursive_graph_names": list(EXPECTED_NAMES),
    }


def test_gauss_magnitude_contracts_and_bodies_are_exact_native_pa() -> None:
    first = _candidate_specs()
    second = _candidate_specs()
    assert second == first
    assert tuple(spec.name for spec in first) == EXPECTED_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES

    receipts, elapsed = _body_receipts()
    assert elapsed <= _BODY_PREFLIGHT_SECONDS
    assert tuple(receipt.name for receipt in receipts) == EXPECTED_NAMES
    assert {
        receipt.name: (receipt.proof_nodes, receipt.proof_depth)
        for receipt in receipts
    } == EXPECTED_BODY_METRICS

    for spec in first:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert formula == parse_formula(spec.statement)
        assert formula == _closed_formula(spec.statement)
        assert 0 < len(spec.statement) < 8_192
        assert spec.script
        assert all("DNE" not in command and not command.startswith("ring") for command in spec.script)
        assert all(
            token not in spec.statement
            for token in ("Prime(", "BetaAt(", "ModEq(", "<", "<=", "%", "^", "∣")
        )


def test_gauss_magnitude_helpers_are_hygienic_alpha_native_and_semantic() -> None:
    left_range = magnitude_range_prefix("b", "c", "h", "l", tag="alpha_left")
    right_range = magnitude_range_prefix("b", "c", "h", "l", tag="alpha_right")
    left_recode = predecessor_recode_prefix(
        "b", "c", "z", "d", "l", tag="alpha_left"
    )
    right_recode = predecessor_recode_prefix(
        "b", "c", "z", "d", "l", tag="alpha_right"
    )
    assert left_range != right_range
    assert left_recode != right_recode
    assert parse_formula(left_range) == parse_formula(right_range)
    assert parse_formula(left_recode) == parse_formula(right_recode)

    for surface, expected in (
        (left_range, {"b", "c", "h", "l"}),
        (left_recode, {"b", "c", "z", "d", "l"}),
    ):
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected
        assert "BetaAt(" not in surface and "<" not in surface

    for call in (
        lambda: magnitude_range_prefix("b", "c", "h", "S l", tag="bad"),
        lambda: predecessor_recode_prefix("b", "c", "z", "d", "l", tag="bad tag"),
        lambda: predecessor_recode_prefix("forall", "c", "z", "d", "l", tag="bad"),
    ):
        with pytest.raises(ValueError):
            call()

    # Independent bounded arithmetic audit of the intended Gauss permutation.
    for p in (3, 5, 7, 11, 13, 17, 19):
        h = (p - 1) // 2
        for a in range(1, p):
            magnitudes = []
            for x in range(1, h + 1):
                residue = (a * x) % p
                magnitude = min(residue, p - residue)
                assert 1 <= magnitude <= h
                magnitudes.append(magnitude)
            assert sorted(magnitudes) == list(range(1, h + 1))
            assert sorted(magnitude - 1 for magnitude in magnitudes) == list(range(h))


def test_gauss_magnitude_graph_is_exact_core_bounded_and_source_isolated() -> None:
    specs = _candidate_specs()
    core = _specs_by_name()
    local_names = set(EXPECTED_NAMES)
    positions = {spec.name: index for index, spec in enumerate(specs)}
    assert len(specs) == len(EXPECTED_NAMES)
    assert all(spec.name not in core for spec in specs)
    assert all(
        dependency in core or dependency in local_names
        for spec in specs
        for dependency in spec.dependencies
    )
    assert all(
        dependency not in positions or positions[dependency] < positions[spec.name]
        for spec in specs
        for dependency in spec.dependencies
    )
    boundary = []
    for spec in specs:
        for dependency in spec.dependencies:
            if dependency not in local_names and dependency not in boundary:
                boundary.append(dependency)
    assert tuple(boundary) == EXPECTED_CORE_BOUNDARY
    assert all(name in core for name in EXPECTED_CORE_BOUNDARY)
    assert _CANDIDATE_SOURCE.is_file()
    assert "gauss_magnitude_permutation_candidate" not in (
        _SOURCE_ROOT / "theorems.py"
    ).read_text()


def test_gauss_magnitude_stack_replays_twice_profiles_full_cut_closure() -> None:
    receipts, elapsed = _body_receipts()
    assert elapsed <= _BODY_PREFLIGHT_SECONDS
    assert tuple(receipt.name for receipt in receipts) == EXPECTED_NAMES

    specs, checked, rows, local, passes = _discovery_runs()
    assert tuple(spec.name for spec in specs) == EXPECTED_NAMES
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert len(passes) == 2
    for spec in specs:
        theorem = checked[spec.name]
        _assert_cut_spine(theorem.certificate, spec, local)
        assert check((), theorem.certificate, theorem.formula)


def test_gauss_magnitude_rejects_contract_and_every_direct_cut_mutation() -> None:
    specs = _candidate_specs()
    false_spec = replace(
        specs[-1],
        statement="forall z. z = S z",
        summary="Deliberately false mutation for WMI rejection.",
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((false_spec,))

    _, checked, _, local, _ = _discovery_runs()
    for spec in specs:
        theorem = checked[spec.name]
        for index in range(len(spec.dependencies)):
            mutated = _mutate_cut_at(theorem.certificate, index)
            assert not check((), mutated, theorem.formula)
