"""Five-gate WMI audit for bounded PairOrder induction and coverage."""

from __future__ import annotations

import gc
import resource
from dataclasses import dataclass, fields, replace
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
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.finite_omission_candidate import (
    _bounded_into_term,
    make_finite_omission_candidate_theorems,
)
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
from peano_lab.library.wilson_pair_order_candidate import (
    _injective_prefix_term,
    _nonendpoint_prefix_term,
    _orbit_closed_prefix_term,
    make_wilson_pair_order_candidate_theorems,
)
from peano_lab.library.wilson_pair_order_induction_candidate import (
    make_wilson_pair_order_induction_candidate_theorems,
    pair_order_state,
)
from peano_lab.library.wilson_square_one_candidate import (
    make_wilson_square_one_candidate_theorems,
)


INDUCTION_NAMES = (
    "prime_pair_order_choose_append_injective",
    "pair_order_double_succ_length",
    "beta_prefix_append_two_bounded_into",
    "prime_pair_order_choose_append_state",
    "orbit_closed_prefix_zero",
    "bounded_into_zero",
    "nonendpoint_prefix_zero",
    "injective_prefix_zero",
    "pair_order_state_zero",
    "pair_order_remaining_pairs_short",
    "pair_order_terminal_double_length",
    "finite_bounded_nonendpoint_injective_coverage",
    "pair_order_state_terminal_coverage",
    "prime_pair_order_pair_count_step",
    "prime_pair_order_remaining_pair_step",
)

GAUSS_RECODE_NAMES = (
    "beta_magnitude_predecessor_recode_exists",
    "beta_magnitude_predecessor_recode_reflect",
    "beta_magnitude_predecessor_recode_bounded",
    "beta_magnitude_predecessor_recode_injective",
    "beta_magnitude_predecessor_recode_surjective",
)

EXPECTED_DEPENDENCIES = {
    "prime_pair_order_choose_append_injective": (
        "prime_pair_order_choose_append",
        "beta_prefix_append_two_injective",
    ),
    "pair_order_double_succ_length": ("add_succ_left",),
    "beta_prefix_append_two_bounded_into": ("finite_lt_succ_eq_or_lt",),
    "prime_pair_order_choose_append_state": (
        "prime_pair_order_choose_append_injective",
        "beta_prefix_append_two_bounded_into",
    ),
    "orbit_closed_prefix_zero": ("add_eq_zero_right", "succ_ne_zero"),
    "bounded_into_zero": ("add_eq_zero_right", "succ_ne_zero"),
    "nonendpoint_prefix_zero": ("add_eq_zero_right", "succ_ne_zero"),
    "injective_prefix_zero": ("add_eq_zero_right", "succ_ne_zero"),
    "pair_order_state_zero": (
        "orbit_closed_prefix_zero",
        "bounded_into_zero",
        "nonendpoint_prefix_zero",
        "injective_prefix_zero",
    ),
    "pair_order_remaining_pairs_short": (),
    "pair_order_terminal_double_length": (),
    "finite_bounded_nonendpoint_injective_coverage": (
        "one_le_of_ne_zero",
        "le_of_succ_le_succ",
        "le_eq_or_lt",
        "nonzero_is_succ",
        "beta_magnitude_predecessor_recode_exists",
        "beta_magnitude_predecessor_recode_surjective",
        "beta_magnitude_predecessor_recode_reflect",
    ),
    "pair_order_state_terminal_coverage": (
        "finite_bounded_nonendpoint_injective_coverage",
    ),
    "prime_pair_order_pair_count_step": (
        "prime_pair_order_choose_append_state",
        "pair_order_double_succ_length",
    ),
    "prime_pair_order_remaining_pair_step": (
        "pair_order_remaining_pairs_short",
        "prime_pair_order_pair_count_step",
    ),
}

EXPECTED_BODY_METRICS = {
    "prime_pair_order_choose_append_injective": (95, 40),
    "pair_order_double_succ_length": (19, 12),
    "beta_prefix_append_two_bounded_into": (69, 27),
    "prime_pair_order_choose_append_state": (90, 42),
    "orbit_closed_prefix_zero": (23, 19),
    "bounded_into_zero": (18, 14),
    "nonendpoint_prefix_zero": (20, 16),
    "injective_prefix_zero": (22, 18),
    "pair_order_state_zero": (64, 19),
    "pair_order_remaining_pairs_short": (8, 8),
    "pair_order_terminal_double_length": (12, 9),
    "finite_bounded_nonendpoint_injective_coverage": (266, 44),
    "pair_order_state_terminal_coverage": (33, 20),
    "prime_pair_order_pair_count_step": (72, 37),
    "prime_pair_order_remaining_pair_step": (51, 36),
}

EXPECTED_STATEMENT_SHA256 = {
    "prime_pair_order_choose_append_injective": "03843d78457b7845e4be57e7707738d86d69d6358bbd6bc3d7c6dd06dd2dd491",
    "pair_order_double_succ_length": "ab187ea6b8ec6b9e4faf12be57b0f18800340cbfd0c6eed38e583188cc6df66f",
    "beta_prefix_append_two_bounded_into": "2b3916cf759700e66ac753f1f7491a221ed4dec9f31e72a8a8a33c9f6c246b05",
    "prime_pair_order_choose_append_state": "3f0a3e519544c2e8f309e126939ce4921db9ad42571b55bd7c26f343f9e819cf",
    "orbit_closed_prefix_zero": "916b769348f1a7c68e918d1e67b5e85cdd1d504c64fb782eb35746424dab6dfd",
    "bounded_into_zero": "1c382d873c9cab90839891e453cabe1c950fe8d0a8921ff2a4b15fc4af9bec93",
    "nonendpoint_prefix_zero": "3f6da04ce04e19d5f96e8a630524fc79e5e284592dd22459cfa67a6b704cd92e",
    "injective_prefix_zero": "e425c596e563df501cb94cada7e1c1691607f99476e767b67334672ffe0675a2",
    "pair_order_state_zero": "7aecfd256750257cc0cf33bbb1857adcf442fc952866b88a6a0b516e2fc75cbb",
    "pair_order_remaining_pairs_short": "a3a2534c0e166f9be98161c6d7ce445e12d79559a4851eceb944640fc0c0333b",
    "pair_order_terminal_double_length": "d83feee9d71a72906acc119713bca12e0cd91963ef68e29290d75c5dfee5cb2f",
    "finite_bounded_nonendpoint_injective_coverage": "9d3c74a5d13b8ea0db14bfee4771f6eea90344ee67e000369ee932ed7950781b",
    "pair_order_state_terminal_coverage": "5752af406111da08ef5667c8e54a107163645eeaa46fc13438108943224b05ef",
    "prime_pair_order_pair_count_step": "98b3adec0efd1ac81b0bb5aa7b9084a6fb5e539c4875a4a0521a30a48f752807",
    "prime_pair_order_remaining_pair_step": "82e5a671d4e4381d3544178492d9c3a4275807dcec2c4302d61f1397a4b152a5",
}

EXPECTED_BOUNDARY = (
    "prime_pair_order_choose_append",
    "beta_prefix_append_two_injective",
    "add_succ_left",
    "finite_lt_succ_eq_or_lt",
    "add_eq_zero_right",
    "succ_ne_zero",
    "one_le_of_ne_zero",
    "le_of_succ_le_succ",
    "le_eq_or_lt",
    "nonzero_is_succ",
    "beta_magnitude_predecessor_recode_exists",
    "beta_magnitude_predecessor_recode_surjective",
    "beta_magnitude_predecessor_recode_reflect",
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
)


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


def _support_specs() -> tuple[TheoremSpec, ...]:
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


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return _support_specs() + _pair_specs() + _gauss_recode_specs() + _induction_specs()


def _spec_digest(spec: TheoremSpec) -> str:
    payload = "\x1f".join(
        (spec.name, spec.statement, "\x1e".join(spec.script), "\x1e".join(spec.dependencies))
    )
    return sha256(payload.encode()).hexdigest()


def _graph_digest(specs: tuple[TheoremSpec, ...]) -> str:
    return sha256("\x1c".join(_spec_digest(spec) for spec in specs).encode()).hexdigest()


def _source_digests() -> dict[str, str]:
    return {label: sha256(path.read_bytes()).hexdigest() for label, path in _CANDIDATE_SOURCES}


def _fresh_replayer():
    specs = _candidate_specs()
    core = _specs_by_name()
    local: dict[str, TheoremSpec] = {}
    for spec in specs:
        assert spec.name not in core
        assert spec.name not in local
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
    targets = tuple(spec for spec in specs if spec.name in INDUCTION_NAMES)
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
                spec.name,
                nodes,
                depth,
                objects,
                edges,
                reused,
                cuts,
                len(spec.statement),
                _spec_digest(spec),
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
        assert not any(type(node) is DNE for node in _walk(body.lemma))
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
    """Expose deterministic recursive induction discovery evidence to WMI."""

    _, _, rows, _, passes, sources, graph_digest = _discovery_runs()
    assert tuple(row[0] for row in rows) == INDUCTION_NAMES
    return {
        "candidate_source_sha256": dict(sources),
        "graph_sha256": graph_digest,
        "recursive_graph_names": [spec.name for spec in _candidate_specs()],
        "gauss_recode_dependencies": list(GAUSS_RECODE_NAMES),
        "discovery_passes": [
            {
                "pass_index": index,
                "duration_seconds": receipt.duration_seconds,
                "peak_rss_kib": receipt.peak_rss_kib,
                "peak_rss_growth_kib": receipt.peak_rss_growth_kib,
                "candidate_source_sha256": dict(sources),
            }
            for index, receipt in enumerate(passes, start=1)
        ],
        "candidates": [_row_metadata(row) for row in rows],
    }


def test_wilson_pair_order_induction_contracts_and_bodies_are_exact_native_pa() -> None:
    first = _induction_specs()
    second = _induction_specs()
    assert first == second
    assert tuple(spec.name for spec in first) == INDUCTION_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES
    assert {spec.name: sha256(spec.statement.encode()).hexdigest() for spec in first} == EXPECTED_STATEMENT_SHA256
    core = dict(_specs_by_name())
    core.update({spec.name: spec for spec in _support_specs() + _pair_specs() + _gauss_recode_specs()})
    receipts = replay_candidate_bodies(first, core=core)
    assert {receipt.name: (receipt.proof_nodes, receipt.proof_depth) for receipt in receipts} == EXPECTED_BODY_METRICS
    for spec in first:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert formula == parse_formula(spec.statement) == _closed_formula(spec.statement)
        assert len(spec.statement) < 16_384
        assert all("DNE" not in command for command in spec.script)
        assert all(command not in {"ring", "auto"} for command in spec.script)
        assert all(token not in spec.statement for token in ("BoundedInto(", "PairOrderState(", "BetaAt(", "<", "%", "^", "∣"))


def test_wilson_pair_order_induction_state_is_hygienic_alpha_equal_and_bounded() -> None:
    left = pair_order_state("u", "v", "b", "c", "l", "n", tag="state_left")
    right = pair_order_state("u", "v", "b", "c", "l", "n", tag="state_right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"u", "v", "b", "c", "l", "n"}
    avoid = ("u", "v", "b", "c", "l", "n")
    closed = _orbit_closed_prefix_term("u", "v", "b", "c", "l", tag="audit_closed", avoid=avoid)
    bounded = _bounded_into_term("b", "c", "l", "n", tag="audit_bounded", avoid=avoid)
    nonendpoint = _nonendpoint_prefix_term("b", "c", "l", "n", tag="audit_nonendpoint", avoid=avoid)
    injective = _injective_prefix_term("b", "c", "l", tag="audit_injective", avoid=avoid)
    expected = f"(({closed}) /\\ (({bounded}) /\\ (({nonendpoint}) /\\ ({injective}))))"
    assert parse_formula(left) == parse_formula(expected)
    with pytest.raises(ValueError, match="Peano identifier"):
        pair_order_state("u", "v", "b", "c", "S l", "n", tag="bad_length")


def test_wilson_pair_order_induction_graph_is_ordered_bounded_and_isolated() -> None:
    specs = _candidate_specs()
    targets = _induction_specs()
    names = tuple(spec.name for spec in specs)
    core = _specs_by_name()
    assert len(names) == len(set(names))
    assert names[-len(INDUCTION_NAMES):] == INDUCTION_NAMES
    positions = {name: index for index, name in enumerate(names)}
    available = set(core) | set(names)
    assert all(dependency in available for spec in specs for dependency in spec.dependencies)
    assert all(
        dependency not in positions or positions[dependency] < positions[spec.name]
        for spec in specs
        for dependency in spec.dependencies
    )
    target_names = set(INDUCTION_NAMES)
    boundary = []
    for spec in targets:
        for dependency in spec.dependencies:
            if dependency not in target_names and dependency not in boundary:
                boundary.append(dependency)
    assert tuple(boundary) == EXPECTED_BOUNDARY
    assert tuple(spec.name for spec in _gauss_recode_specs()) == GAUSS_RECODE_NAMES
    assert all(path.is_file() for _, path in _CANDIDATE_SOURCES)
    registry_source = (_SOURCE_ROOT / "theorems.py").read_text()
    assert "wilson_pair_order_induction_candidate" not in registry_source
    assert all(name not in core for name in INDUCTION_NAMES + GAUSS_RECODE_NAMES)


def test_wilson_pair_order_induction_stack_replays_twice_profiles_full_cut_closure() -> None:
    specs, checked, rows, local, passes, sources, graph_digest = _discovery_runs()
    print(
        "WMI WILSON PAIR ORDER INDUCTION GRAPH RECEIPT "
        f"nodes={len(_candidate_specs())} graph_sha256={graph_digest} candidate_source_sha256={sources}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI WILSON PAIR ORDER INDUCTION PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        metadata = _row_metadata(row)
        print(
            "WMI WILSON PAIR ORDER INDUCTION RECEIPT "
            + " ".join(f"{key}={value}" for key, value in metadata.items()),
            flush=True,
        )
        theorem = checked[spec.name]
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        assert metadata["nodes"] <= MAX_USE_CERTIFICATE_NODES
        assert metadata["depth"] <= MAX_USE_PROOF_DEPTH
        assert metadata["objects"] <= MAX_USE_CERTIFICATE_OBJECTS
        _assert_cut_spine(theorem.certificate, spec, local)


def test_wilson_pair_order_induction_rejects_false_contracts_and_direct_cut_mutations() -> None:
    specs, checked, _, _, _, _, _ = _discovery_runs()
    false_formula = parse_formula("0 = S 0")
    for spec in specs:
        theorem = checked[spec.name]
        assert false_formula != theorem.formula
        assert not check((), theorem.certificate, false_formula)
        for index, dependency in enumerate(spec.dependencies):
            mutated = _mutate_cut_at(theorem.certificate, index)
            assert not check((), mutated, theorem.formula), f"accepted mutated edge {spec.name}->{dependency}"
