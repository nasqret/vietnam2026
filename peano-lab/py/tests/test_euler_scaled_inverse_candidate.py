"""WMI-only five-gate audit for the pointwise Euler scaled inverse ladder."""

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
from peano_lab.library.euler_scaled_inverse_candidate import (
    make_euler_scaled_inverse_candidate_theorems,
    prime,
    scaled_fixed_point,
    scaled_inverse,
    strictly_below,
    unit_residue,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "scaled_inverse_from_unit_inverse",
    "scaled_inverse_transport_right",
    "prime_scaled_inverse_target_nonzero",
    "prime_scaled_inverse_exists",
    "prime_scaled_inverse_unique",
    "scaled_inverse_symmetric",
    "prime_scaled_inverse_involutive",
    "scaled_inverse_fixed_point_iff",
    "scaled_inverse_no_fixed_of_not_qres",
    "scaled_inverse_qres_or_fixed_free",
)

EXPECTED_DEPENDENCIES = {
    "scaled_inverse_from_unit_inverse": (
        "mod_eq_mul_left",
        "mul_assoc",
        "mul_comm",
        "mul_one",
    ),
    "scaled_inverse_transport_right": (
        "mod_eq_mul_left",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
    "prime_scaled_inverse_target_nonzero": (
        "prime_is_succ_succ",
        "mod_eq_bounded_unique",
        "succ_ne_zero",
    ),
    "prime_scaled_inverse_exists": (
        "prime_bounded_nonzero_mod_inverse",
        "scaled_inverse_from_unit_inverse",
        "prime_nonzero",
        "division_remainder_exists",
        "mul_comm",
        "remainder_decomposition_to_mod_eq",
        "scaled_inverse_transport_right",
        "prime_scaled_inverse_target_nonzero",
    ),
    "prime_scaled_inverse_unique": (
        "divisor_le_nonzero",
        "lt_not_le",
        "mod_eq_symm",
        "mod_eq_trans",
        "prime_mod_cancel",
        "mod_eq_bounded_unique",
    ),
    "scaled_inverse_symmetric": ("mul_comm",),
    "prime_scaled_inverse_involutive": (
        "scaled_inverse_symmetric",
        "prime_scaled_inverse_unique",
    ),
    "scaled_inverse_fixed_point_iff": (),
    "scaled_inverse_no_fixed_of_not_qres": ("scaled_inverse_fixed_point_iff",),
    "scaled_inverse_qres_or_fixed_free": (
        "quadratic_residue_decidable_nonzero",
        "scaled_inverse_no_fixed_of_not_qres",
    ),
}

EXPECTED_CORE_BOUNDARY = (
    "mod_eq_mul_left",
    "mul_assoc",
    "mul_comm",
    "mul_one",
    "mod_eq_symm",
    "mod_eq_trans",
    "prime_is_succ_succ",
    "mod_eq_bounded_unique",
    "succ_ne_zero",
    "prime_bounded_nonzero_mod_inverse",
    "prime_nonzero",
    "division_remainder_exists",
    "remainder_decomposition_to_mod_eq",
    "divisor_le_nonzero",
    "lt_not_le",
    "prime_mod_cancel",
    "quadratic_residue_decidable_nonzero",
)

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_CANDIDATE_SOURCE = _SOURCE_ROOT / "euler_scaled_inverse_candidate.py"
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
    return make_euler_scaled_inverse_candidate_theorems(TheoremSpec)


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
        assert depth <= MAX_USE_PROOF_DEPTH
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS
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


def test_euler_scaled_inverse_contracts_are_exact_deterministic_closed_expanded_pa() -> None:
    first = _candidate_specs()
    second = _candidate_specs()
    assert second == first
    assert tuple(spec.name for spec in first) == EXPECTED_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES
    assert first[3].statement.startswith("forall p a x.")
    assert "exists y." in first[3].statement
    assert first[4].statement.endswith("-> y = z")
    assert first[6].statement.endswith("-> z = x")
    assert "quadratic_residue_decidable_nonzero" in first[-1].dependencies

    for spec in first:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert formula == parse_formula(spec.statement)
        assert formula == _closed_formula(spec.statement)
        assert len(spec.statement) < 16_384
        assert spec.script
        assert all("DNE" not in command and not command.startswith("ring") for command in spec.script)
        assert all(
            token not in spec.statement
            for token in ("Prime(", "QRes(", "ModEq(", "<", "<=", "%", "^", "∣")
        )


def test_euler_scaled_inverse_helpers_are_hygienic_alpha_native_and_audited() -> None:
    assert strictly_below("x", "p", tag="exact") == (
        "exists esi_strict_gap_exact. esi_strict_gap_exact + S x = p"
    )
    assert unit_residue("p", "x", tag="exact") == (
        "(~(x = 0) /\\ (exists esi_strict_gap_exact_bound. "
        "esi_strict_gap_exact_bound + S x = p))"
    )
    relation = scaled_inverse("p", "a", "x", "y", tag="exact")
    fixed = scaled_fixed_point("p", "a", "x", tag="exact")
    assert "x * y" in relation and "x * x" in fixed
    assert "esi_mod_left_exact_mod" in relation
    assert "esi_mod_left_exact_square" in fixed

    alpha_pairs = (
        (prime("p", tag="alpha_left"), prime("p", tag="alpha_right")),
        (
            unit_residue("p", "x", tag="alpha_left"),
            unit_residue("p", "x", tag="alpha_right"),
        ),
        (
            scaled_inverse("p", "a", "x", "y", tag="alpha_left"),
            scaled_inverse("p", "a", "x", "y", tag="alpha_right"),
        ),
    )
    for left, right in alpha_pairs:
        assert left != right
        assert parse_formula(left) == parse_formula(right)

    for surface, expected in (
        (prime("p", tag="free"), {"p"}),
        (unit_residue("p", "x", tag="free"), {"p", "x"}),
        (relation, {"p", "a", "x", "y"}),
        (fixed, {"p", "a", "x"}),
    ):
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected

    for call in (
        lambda: strictly_below("x + 1", "p", tag="bad_lower"),
        lambda: unit_residue("p", "S x", tag="bad_value"),
        lambda: scaled_inverse("p", "a", "x", "y", tag="bad tag"),
    ):
        with pytest.raises(ValueError):
            call()
    with pytest.raises(ValueError, match="captures an argument"):
        strictly_below("esi_strict_gap_capture", "p", tag="capture")

    # Independent finite audit of the intended mathematical relation.
    for p in (3, 5, 7, 11, 13):
        for a in range(1, p):
            roots = {x for x in range(1, p) if x * x % p == a}
            for x in range(1, p):
                ys = [y for y in range(1, p) if x * y % p == a]
                assert len(ys) == 1
                y = ys[0]
                assert y * x % p == a
                assert [z for z in range(1, p) if y * z % p == a] == [x]
                assert (y == x) == (x in roots)


def test_euler_scaled_inverse_graph_is_exact_core_bounded_and_source_isolated() -> None:
    specs = _candidate_specs()
    core = _specs_by_name()
    local_names = set(EXPECTED_NAMES)
    positions = {spec.name: index for index, spec in enumerate(specs)}
    assert len(specs) == len(EXPECTED_NAMES)
    assert len(local_names) == len(EXPECTED_NAMES)
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
    assert "euler_scaled_inverse_candidate" not in (_SOURCE_ROOT / "theorems.py").read_text()


def test_euler_scaled_inverse_body_preflight_then_replays_twice_with_full_cut_closure() -> None:
    body_receipts, elapsed = _body_receipts()
    assert elapsed <= _BODY_PREFLIGHT_SECONDS
    assert tuple(receipt.name for receipt in body_receipts) == EXPECTED_NAMES
    assert all(receipt.proof_nodes > 0 and receipt.proof_depth > 0 for receipt in body_receipts)

    specs, checked, rows, local, passes = _discovery_runs()
    assert tuple(spec.name for spec in specs) == EXPECTED_NAMES
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert len(passes) == 2
    for spec in specs:
        theorem = checked[spec.name]
        _assert_cut_spine(theorem.certificate, spec, local)
        assert check((), theorem.certificate, theorem.formula)


def test_euler_scaled_inverse_rejects_false_contract_and_every_direct_cut_mutation() -> None:
    specs = _candidate_specs()
    false_spec = replace(
        specs[7],
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
