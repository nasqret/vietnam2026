"""Five-gate WMI audit for constructive Wilson PairOrder iteration."""

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
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.finite_omission_candidate import make_finite_omission_candidate_theorems
from peano_lab.library.gauss_magnitude_permutation_candidate import (
    make_gauss_magnitude_permutation_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)
from peano_lab.library.wilson_inverse_endpoints_candidate import (
    make_wilson_inverse_endpoints_candidate_theorems,
)
from peano_lab.library.wilson_inverse_involution_candidate import (
    make_wilson_inverse_involution_candidate_theorems,
)
from peano_lab.library.wilson_inverse_orbit_candidate import (
    make_wilson_inverse_orbit_candidate_theorems,
)
from peano_lab.library.wilson_inverse_point_candidate import (
    make_wilson_inverse_point_candidate_theorems,
)
from peano_lab.library.wilson_inverse_prefix_candidate import (
    make_wilson_inverse_prefix_candidate_theorems,
)
from peano_lab.library.wilson_pair_order_candidate import make_wilson_pair_order_candidate_theorems
from peano_lab.library.wilson_pair_order_induction_candidate import (
    _pair_order_state_term,
    make_wilson_pair_order_induction_candidate_theorems,
    pair_order_state,
)
from peano_lab.library.wilson_pair_order_iteration_candidate import (
    make_wilson_pair_order_iteration_candidate_theorems,
)
from peano_lab.library.wilson_square_one_candidate import make_wilson_square_one_candidate_theorems


ITERATION_NAMES = (
    "prime_pair_order_state_step",
    "pair_order_iteration_previous_balance",
    "pair_order_iteration_step_room",
    "prime_pair_order_iteration",
    "prime_pair_order_terminal_state_exists",
)

GAUSS_RECODE_NAMES = (
    "beta_magnitude_predecessor_recode_exists",
    "beta_magnitude_predecessor_recode_reflect",
    "beta_magnitude_predecessor_recode_bounded",
    "beta_magnitude_predecessor_recode_injective",
    "beta_magnitude_predecessor_recode_surjective",
)

EXPECTED_DEPENDENCIES = {
    "prime_pair_order_state_step": ("prime_pair_order_choose_append_state",),
    "pair_order_iteration_previous_balance": ("add_succ_left", "add_assoc", "add_comm"),
    "pair_order_iteration_step_room": ("add_succ_left", "add_assoc", "add_comm"),
    "prime_pair_order_iteration": (
        "pair_order_state_zero",
        "pair_order_iteration_previous_balance",
        "pair_order_iteration_step_room",
        "prime_pair_order_state_step",
        "pair_order_double_succ_length",
    ),
    "prime_pair_order_terminal_state_exists": ("prime_pair_order_iteration", "zero_add"),
}

EXPECTED_STATEMENT_SHA256 = {
    "prime_pair_order_state_step": "3ce90d0555a196099e0eff6de6197916512596c25c34e872c6ffdb039e691f38",
    "pair_order_iteration_previous_balance": "6f219aa058995721c0c3d22e5dd1446f047578a096f82477b95f0ea484084b17",
    "pair_order_iteration_step_room": "14fd7213841abca553c0e15326fae114838c7faee986aebd8a276d2cc3523aa1",
    "prime_pair_order_iteration": "08312020ffb162c042bb79d13907e66982acb7d333f3d848203d623f972c0011",
    "prime_pair_order_terminal_state_exists": "3b298b1fd2fab7bca4d8a7f6b8a402d468cd0d147a69e2569fe1a4a542628ef6",
}

EXPECTED_BODY_RECEIPTS = {
    "prime_pair_order_state_step": (1, 64, 95, 37, 95, 94, 0),
    "pair_order_iteration_previous_balance": (3, 3, 78, 24, 67, 77, 11),
    "pair_order_iteration_step_room": (3, 3, 68, 22, 59, 67, 9),
    "prime_pair_order_iteration": (5, 85, 148, 37, 143, 147, 5),
    "prime_pair_order_terminal_state_exists": (2, 29, 52, 26, 51, 51, 1),
}

EXPECTED_BOUNDARY = (
    "prime_pair_order_choose_append_state",
    "add_succ_left",
    "add_assoc",
    "add_comm",
    "pair_order_state_zero",
    "pair_order_double_succ_length",
    "zero_add",
)

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_CANDIDATE_SOURCES = (
    ("square_one", _SOURCE_ROOT / "wilson_square_one_candidate.py"),
    ("inverse_point", _SOURCE_ROOT / "wilson_inverse_point_candidate.py"),
    ("inverse_prefix", _SOURCE_ROOT / "wilson_inverse_prefix_candidate.py"),
    ("inverse_involution", _SOURCE_ROOT / "wilson_inverse_involution_candidate.py"),
    ("inverse_endpoints", _SOURCE_ROOT / "wilson_inverse_endpoints_candidate.py"),
    ("inverse_orbit", _SOURCE_ROOT / "wilson_inverse_orbit_candidate.py"),
    ("finite_omission", _SOURCE_ROOT / "finite_omission_candidate.py"),
    ("pair_order", _SOURCE_ROOT / "wilson_pair_order_candidate.py"),
    ("gauss_magnitude", _SOURCE_ROOT / "gauss_magnitude_permutation_candidate.py"),
    ("pair_induction", _SOURCE_ROOT / "wilson_pair_order_induction_candidate.py"),
    ("pair_iteration", _SOURCE_ROOT / "wilson_pair_order_iteration_candidate.py"),
)
_BODY_PREFLIGHT_SECONDS = 30


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


def _base_support_specs() -> tuple[TheoremSpec, ...]:
    return (
        make_wilson_square_one_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_point_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_prefix_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_involution_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_endpoints_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_orbit_candidate_theorems(TheoremSpec)
        + make_finite_omission_candidate_theorems(TheoremSpec)
    )


def _pair_specs() -> tuple[TheoremSpec, ...]:
    return make_wilson_pair_order_candidate_theorems(TheoremSpec)


def _gauss_recode_specs() -> tuple[TheoremSpec, ...]:
    selected = set(GAUSS_RECODE_NAMES)
    return tuple(
        spec
        for spec in make_gauss_magnitude_permutation_candidate_theorems(TheoremSpec)
        if spec.name in selected
    )


def _induction_specs() -> tuple[TheoremSpec, ...]:
    return make_wilson_pair_order_induction_candidate_theorems(TheoremSpec)


def _support_specs() -> tuple[TheoremSpec, ...]:
    return _base_support_specs() + _pair_specs() + _gauss_recode_specs() + _induction_specs()


def _iteration_specs() -> tuple[TheoremSpec, ...]:
    return make_wilson_pair_order_iteration_candidate_theorems(TheoremSpec)


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return _support_specs() + _iteration_specs()


def _body_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    core.update((spec.name, spec) for spec in _support_specs())
    return core


def _spec_digest(spec: TheoremSpec) -> str:
    payload = "\x1f".join(
        (spec.name, spec.statement, "\x1e".join(spec.script), "\x1e".join(spec.dependencies))
    )
    return sha256(payload.encode()).hexdigest()


def _graph_digest(specs: tuple[TheoremSpec, ...]) -> str:
    return sha256("\x1c".join(_spec_digest(spec) for spec in specs).encode()).hexdigest()


def _source_digests() -> dict[str, str]:
    return {label: sha256(path.read_bytes()).hexdigest() for label, path in _CANDIDATE_SOURCES}


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
        receipts = replay_candidate_bodies(_iteration_specs(), core=_body_core())
    return receipts, perf_counter() - started


def _fresh_replayer():
    specs = _candidate_specs()
    core = _specs_by_name()
    local: dict[str, TheoremSpec] = {}
    for spec in specs:
        assert spec.name not in core and spec.name not in local
        local[spec.name] = spec

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        if name in core:
            checked = replay(name)
            return _Checked(checked.formula, checked.certificate)
        spec = local[name]
        formula = _closed_formula(spec.statement)
        target = formula
        for dependency in reversed(spec.dependencies):
            target = Imp(_closed_formula((local.get(dependency) or core[dependency]).statement), target)
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
            body = Cut(checked_dependency.formula, formula, checked_dependency.certificate, body)
        assert check((), body, formula)
        return _Checked(formula, body)

    return specs, local, run


def _cold_rows():
    started = perf_counter()
    starting_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, local, run = _fresh_replayer()
    targets = tuple(spec for spec in specs if spec.name in ITERATION_NAMES)
    checked: dict[str, _Checked] = {}
    rows = []
    for spec in targets:
        theorem = run(spec.name)
        checked[spec.name] = theorem
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
        rows.append(
            (
                spec.name, nodes, depth, objects, edges, reused, cuts,
                len(spec.statement), _spec_digest(spec),
                sha256(spec.statement.encode()).hexdigest(),
                sha256("\n".join(spec.script).encode()).hexdigest(),
                sha256("\0".join(spec.dependencies).encode()).hexdigest(),
            )
        )
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert depth <= MAX_USE_PROOF_DEPTH
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt = _PassReceipt(perf_counter() - started, peak, max(0, peak - starting_peak))
    return targets, checked, tuple(rows), local, _source_digests(), _graph_digest(specs), receipt


@lru_cache(maxsize=1)
def _discovery_runs():
    first = _cold_rows()
    first_rows, first_sources, first_graph, first_receipt = first[2], first[4], first[5], first[6]
    del first
    gc.collect()
    second = _cold_rows()
    assert second[2] == first_rows
    assert second[4] == first_sources
    assert second[5] == first_graph
    return second[:4] + ((first_receipt, second[6]), second[4], second[5])


def _assert_cut_spine(certificate: Proof, spec: TheoremSpec, local: dict[str, TheoremSpec]) -> None:
    body = certificate
    core = _specs_by_name()
    for dependency in spec.dependencies:
        assert type(body) is Cut
        expected = _closed_formula((local.get(dependency) or core[dependency]).statement)
        assert body.proposition == expected
        assert check((), body.lemma, expected)
        body = body.body


def _mutate_cut_at(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(certificate, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(certificate, body=_mutate_cut_at(certificate.body, index - 1))


def _row_metadata(row: tuple[object, ...]) -> dict[str, object]:
    keys = (
        "name", "nodes", "depth", "objects", "edges", "reused", "cuts",
        "statement_length", "spec_sha256", "statement_sha256", "script_sha256",
        "dependencies_sha256",
    )
    return dict(zip(keys, row, strict=True))


def wmi_receipt_metadata() -> dict[str, object]:
    body_receipts, body_seconds = _body_receipts()
    _, _, rows, _, passes, sources, graph_digest = _discovery_runs()
    return {
        "body_preflight_limit_seconds": _BODY_PREFLIGHT_SECONDS,
        "body_preflight_seconds": body_seconds,
        "body_receipts": [asdict(receipt) for receipt in body_receipts],
        "candidate_source_sha256": dict(sources),
        "candidates": [_row_metadata(row) for row in rows],
        "discovery_passes": [asdict(receipt) for receipt in passes],
        "graph_sha256": graph_digest,
        "recursive_graph_names": [spec.name for spec in _candidate_specs()],
    }


def test_wilson_pair_order_iteration_contracts_and_bodies_are_exact_native_pa() -> None:
    first = _iteration_specs()
    assert _iteration_specs() == first
    assert tuple(spec.name for spec in first) == ITERATION_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES
    assert {spec.name: sha256(spec.statement.encode()).hexdigest() for spec in first} == EXPECTED_STATEMENT_SHA256
    receipts, elapsed = _body_receipts()
    assert elapsed <= _BODY_PREFLIGHT_SECONDS
    assert {
        receipt.name: (
            receipt.dependency_count, receipt.command_count, receipt.proof_nodes,
            receipt.proof_depth, receipt.proof_objects, receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == EXPECTED_BODY_RECEIPTS
    for spec in first:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert formula == parse_formula(spec.statement) == _closed_formula(spec.statement)
        assert 0 < len(spec.statement) < 16_384
        assert all("DNE" not in command for command in spec.script)
        assert all(command not in {"ring", "auto"} for command in spec.script)
        assert all(
            token not in spec.statement
            for token in ("PairOrderState(", "BetaAt(", "Prime(", "InvPrefix(", "<", "%", "^", "∣")
        )


def test_wilson_pair_order_iteration_state_is_hygienic_alpha_equal_and_semantic() -> None:
    left = pair_order_state("u", "v", "b", "c", "l", "n", tag="iteration_alpha_left")
    right = pair_order_state("u", "v", "b", "c", "l", "n", tag="iteration_alpha_right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"u", "v", "b", "c", "l", "n"}
    compound = _pair_order_state_term(
        "u", "v", "b", "c", "m + m", "n",
        tag="iteration_compound", avoid=("u", "v", "b", "c", "m", "n"),
    )
    _, compound_names = parse_formula_with_names(compound)
    assert set(compound_names) == {"u", "v", "b", "c", "m", "n"}
    with pytest.raises(ValueError, match="Peano identifier"):
        pair_order_state("u", "v", "b", "c", "m + m", "n", tag="bad_length")

    for m in range(32):
        for k in range(32):
            original = (k + k) + 2 + ((m + 1) + (m + 1))
            previous = ((k + 1) + (k + 1)) + 2 + (m + m)
            room = (1 + (k + k)) + 3 + (m + m)
            assert original == previous == room


def test_wilson_pair_order_iteration_graph_is_ordered_bounded_and_source_isolated() -> None:
    specs = _candidate_specs()
    targets = _iteration_specs()
    names = tuple(spec.name for spec in specs)
    core = _specs_by_name()
    assert len(names) == len(set(names))
    assert names[-len(ITERATION_NAMES):] == ITERATION_NAMES
    positions = {name: index for index, name in enumerate(names)}
    available = set(core) | set(names)
    assert all(dependency in available for spec in specs for dependency in spec.dependencies)
    assert all(
        dependency not in positions or positions[dependency] < positions[spec.name]
        for spec in specs for dependency in spec.dependencies
    )
    target_names = set(ITERATION_NAMES)
    boundary = []
    for spec in targets:
        for dependency in spec.dependencies:
            if dependency not in target_names and dependency not in boundary:
                boundary.append(dependency)
    assert tuple(boundary) == EXPECTED_BOUNDARY
    assert tuple(spec.name for spec in _gauss_recode_specs()) == GAUSS_RECODE_NAMES
    assert all(path.is_file() for _, path in _CANDIDATE_SOURCES)
    registry_source = (_SOURCE_ROOT / "theorems.py").read_text()
    assert "wilson_pair_order_iteration_candidate" not in registry_source
    assert all(name not in core for name in ITERATION_NAMES)


def test_wilson_pair_order_iteration_stack_replays_twice_profiles_full_cut_closure() -> None:
    specs, checked, rows, local, passes, sources, graph_digest = _discovery_runs()
    print(
        "WMI WILSON PAIR ORDER ITERATION GRAPH RECEIPT "
        f"nodes={len(_candidate_specs())} graph_sha256={graph_digest} candidate_source_sha256={sources}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI WILSON PAIR ORDER ITERATION PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        metadata = _row_metadata(row)
        print(
            "WMI WILSON PAIR ORDER ITERATION RECEIPT "
            + " ".join(f"{key}={value}" for key, value in metadata.items()),
            flush=True,
        )
        theorem = checked[spec.name]
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        _assert_cut_spine(theorem.certificate, spec, local)


def test_wilson_pair_order_iteration_rejects_false_contracts_and_direct_cut_mutations() -> None:
    specs = _iteration_specs()
    false_spec = replace(specs[-1], statement="forall z. z = S z")
    false_core = _body_core()
    false_core.update((spec.name, spec) for spec in specs[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((false_spec,), core=false_core)
    _, checked, _, _, _, _, _ = _discovery_runs()
    for spec in specs:
        theorem = checked[spec.name]
        for index, dependency in enumerate(spec.dependencies):
            mutated = _mutate_cut_at(theorem.certificate, index)
            assert not check((), mutated, theorem.formula), f"accepted mutated edge {spec.name}->{dependency}"
