"""WMI-only five-gate audit for constructive Wilson PairOrder candidates."""

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
    make_finite_omission_candidate_theorems,
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
    _append_two_reflection_term,
    _append_two_trace_term,
    _injective_prefix_term,
    _nonendpoint_prefix_term,
    _orbit_closed_prefix_term,
    append_two_trace,
    make_wilson_pair_order_candidate_theorems,
    nonendpoint_prefix,
    omits_value,
    orbit_closed_prefix,
)
from peano_lab.library.wilson_square_one_candidate import (
    make_wilson_square_one_candidate_theorems,
)


PAIR_NAMES = (
    "beta_prefix_append_two_exists",
    "beta_prefix_append_two_reflect",
    "finite_prefix_choose_unused_nonendpoint",
    "prime_choose_unused_nonendpoint_orbit",
    "orbit_closed_unused_mate",
    "beta_prefix_append_two_orbit_closed",
    "beta_prefix_append_two_nonendpoint",
    "beta_prefix_append_two_injective",
    "prime_pair_order_choose_append",
)

EXPECTED_DEPENDENCIES = {
    "beta_prefix_append_two_exists": (
        "beta_prefix_extend",
        "le_refl",
        "le_succ",
    ),
    "beta_prefix_append_two_reflect": (
        "finite_lt_succ_eq_or_lt",
        "beta_at_exists",
        "beta_at_unique",
    ),
    "finite_prefix_choose_unused_nonendpoint": (
        "beta_prefix_append_two_exists",
        "finite_short_prefix_omits",
        "le_refl",
        "le_succ",
        "succ_injective",
    ),
    "prime_choose_unused_nonendpoint_orbit": (
        "finite_prefix_choose_unused_nonendpoint",
        "prime_inverse_prefix_nonendpoint_mate",
        "prime_inverse_prefix_nonendpoint_not_fixed",
        "inverse_prefix_involutive",
    ),
    "orbit_closed_unused_mate": (),
    "beta_prefix_append_two_orbit_closed": (
        "beta_prefix_append_two_reflect",
        "beta_at_unique",
        "le_refl",
        "le_succ",
    ),
    "beta_prefix_append_two_nonendpoint": ("beta_prefix_append_two_reflect",),
    "beta_prefix_append_two_injective": ("beta_prefix_append_two_reflect",),
    "prime_pair_order_choose_append": (
        "prime_choose_unused_nonendpoint_orbit",
        "orbit_closed_unused_mate",
        "beta_prefix_append_two_exists",
        "beta_prefix_append_two_orbit_closed",
        "beta_prefix_append_two_nonendpoint",
    ),
}

EXPECTED_PAIR_BOUNDARY = (
    "beta_prefix_extend",
    "le_refl",
    "le_succ",
    "finite_lt_succ_eq_or_lt",
    "beta_at_exists",
    "beta_at_unique",
    "finite_short_prefix_omits",
    "succ_injective",
    "prime_inverse_prefix_nonendpoint_mate",
    "prime_inverse_prefix_nonendpoint_not_fixed",
    "inverse_prefix_involutive",
)

EXPECTED_BODY_METRICS = {
    "beta_prefix_append_two_exists": (63, 27),
    "beta_prefix_append_two_reflect": (115, 32),
    "finite_prefix_choose_unused_nonendpoint": (113, 30),
    "prime_choose_unused_nonendpoint_orbit": (138, 43),
    "orbit_closed_unused_mate": (34, 20),
    "beta_prefix_append_two_orbit_closed": (167, 38),
    "beta_prefix_append_two_nonendpoint": (63, 31),
    "beta_prefix_append_two_injective": (202, 36),
    "prime_pair_order_choose_append": (191, 53),
}

EXPECTED_STATEMENT_SHA256 = {
    "beta_prefix_append_two_exists": "9731f9602faa3637a0401c45ff4afbdd46666e570e66abb52b6ea8a151cb9510",
    "beta_prefix_append_two_reflect": "b4951d9abe3123d7a9c77810e77e345d517bc43f671fde9561f11ae2f041f7cf",
    "finite_prefix_choose_unused_nonendpoint": "0a0cda206d07d589b9518e227f465d5c7de8f45b40f5ecedb4949e1fd9bfce16",
    "prime_choose_unused_nonendpoint_orbit": "804e9f3db2ba385f0f13196b89bb3f3bc1c2956dbe09139cb368c281a4ef3ee5",
    "orbit_closed_unused_mate": "f3df33b12f2d68d1c31335dc0584f2ce4cd8d37c83a6cb6108c8e568363aa88f",
    "beta_prefix_append_two_orbit_closed": "2952d932f23162f01b7eaf36316dcb278cc284d0627583d482f781d0f257a7c9",
    "beta_prefix_append_two_nonendpoint": "cf972d4bf4ea683bad2fb9336ee2acdf3188796eaeaace69dd24a439a404a3a8",
    "beta_prefix_append_two_injective": "de5d8055a59945ae228f5e056312d6b87f881dc9af3e839ba27365dfb3ac32a5",
    "prime_pair_order_choose_append": "3eff09c5d9c491cca8bda123c598ef329c8bc176f7366090009c94892208d112",
}

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


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return _support_specs() + _pair_specs()


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
    pair_specs = tuple(spec for spec in specs if spec.name in PAIR_NAMES)
    checked: dict[str, _Checked] = {}
    rows = []
    for spec in pair_specs:
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
    receipt = _PassReceipt(
        duration_seconds=perf_counter() - started,
        peak_rss_kib=peak,
        peak_rss_growth_kib=max(0, peak - starting_peak),
    )
    return (
        pair_specs,
        checked,
        tuple(rows),
        local,
        _source_digests(),
        _graph_digest(specs),
        receipt,
    )


@lru_cache(maxsize=1)
def _discovery_runs():
    first = _cold_rows()
    first_rows = first[2]
    first_sources = first[4]
    first_graph = first[5]
    first_receipt = first[6]
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
        dependency_spec = local.get(dependency) or core[dependency]
        expected = _closed_formula(dependency_spec.statement)
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
        "name",
        "nodes",
        "depth",
        "objects",
        "edges",
        "reused",
        "cuts",
        "statement_length",
        "spec_sha256",
        "statement_sha256",
        "script_sha256",
        "dependencies_sha256",
    )
    return dict(zip(keys, row, strict=True))


def wmi_receipt_metadata() -> dict[str, object]:
    """Expose deterministic recursive PairOrder discovery evidence to WMI."""

    _, _, rows, _, passes, sources, graph_digest = _discovery_runs()
    assert tuple(row[0] for row in rows) == PAIR_NAMES
    return {
        "candidate_source_sha256": dict(sources),
        "graph_sha256": graph_digest,
        "recursive_graph_names": [spec.name for spec in _candidate_specs()],
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


def test_wilson_pair_order_contracts_and_bodies_are_exact_native_pa() -> None:
    first = _pair_specs()
    second = _pair_specs()
    assert second == first
    assert tuple(spec.name for spec in first) == PAIR_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES
    assert {
        spec.name: sha256(spec.statement.encode()).hexdigest() for spec in first
    } == EXPECTED_STATEMENT_SHA256

    core = _specs_by_name()
    core.update({spec.name: spec for spec in _support_specs()})
    receipts = replay_candidate_bodies(first, core=core)
    assert {
        receipt.name: (receipt.proof_nodes, receipt.proof_depth)
        for receipt in receipts
    } == EXPECTED_BODY_METRICS

    for spec in first:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert formula == parse_formula(spec.statement)
        assert formula == _closed_formula(spec.statement)
        assert len(spec.statement) < 16_384
        assert all("DNE" not in command for command in spec.script)
        assert all(command not in {"ring", "auto"} for command in spec.script)
        assert all(
            token not in spec.statement
            for token in ("Append2(", "BetaAt(", "InvPrefix(", "Prime(", "<", "%", "^", "∣")
        )

    combined = first[-1]
    assert len(combined.statement) == 9_400
    assert len(combined.statement) > 8_192
    assert "exists z d i j." in combined.statement


def test_wilson_pair_order_helpers_are_hygienic_alpha_equal_and_compound_safe() -> None:
    surfaces = {
        append_two_trace("b", "c", "z", "d", "l", "a", "e", tag="free_trace"): {
            "b", "c", "z", "d", "l", "a", "e"
        },
        omits_value("b", "c", "l", "a", tag="free_omit"): {"b", "c", "l", "a"},
        orbit_closed_prefix("u", "v", "b", "c", "l", tag="free_closed"): {
            "u", "v", "b", "c", "l"
        },
        nonendpoint_prefix("b", "c", "l", "n", tag="free_nonendpoint"): {
            "b", "c", "l", "n"
        },
    }
    for surface, expected_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_names

    alpha_pairs = (
        (
            append_two_trace("b", "c", "z", "d", "l", "a", "e", tag="alpha_trace_left"),
            append_two_trace("b", "c", "z", "d", "l", "a", "e", tag="alpha_trace_right"),
        ),
        (
            orbit_closed_prefix("u", "v", "b", "c", "l", tag="alpha_closed_left"),
            orbit_closed_prefix("u", "v", "b", "c", "l", tag="alpha_closed_right"),
        ),
    )
    for left, right in alpha_pairs:
        assert left != right
        assert parse_formula(left) == parse_formula(right)

    compound_relations = (
        _orbit_closed_prefix_term(
            "u", "v", "z", "d", "S (S l)", tag="compound_closed", avoid=("u", "v", "z", "d", "l")
        ),
        _nonendpoint_prefix_term(
            "z", "d", "S (S l)", "n", tag="compound_nonendpoint", avoid=("z", "d", "l", "n")
        ),
        _injective_prefix_term(
            "z", "d", "S (S l)", tag="compound_injective", avoid=("z", "d", "l")
        ),
        _append_two_trace_term(
            "b", "c", "z", "d", "l", "a", "e", tag="compound_trace", avoid=("b", "c", "z", "d", "l", "a", "e")
        ),
        _append_two_reflection_term(
            "b", "c", "l", "a", "e", "q", "w", tag="compound_reflect", avoid=("b", "c", "l", "a", "e", "q", "w")
        ),
    )
    for relation in compound_relations:
        parse_formula(relation)

    invalid_calls = (
        lambda: append_two_trace("b + 1", "c", "z", "d", "l", "a", "e", tag="bad_code"),
        lambda: omits_value("b", "c", "l", "S a", tag="bad_value"),
        lambda: orbit_closed_prefix("u", "v", "b", "c", "S l", tag="bad_length"),
        lambda: nonendpoint_prefix("b", "c", "l", "S n", tag="bad_bound"),
    )
    for call in invalid_calls:
        with pytest.raises(ValueError, match="Peano identifier"):
            call()
    with pytest.raises(ValueError, match="captures an argument"):
        append_two_trace(
            "wpo_old_index_capture", "c", "z", "d", "l", "a", "e", tag="capture"
        )


def test_wilson_pair_order_graph_is_ordered_core_bounded_and_source_isolated() -> None:
    specs = _candidate_specs()
    pair_specs = _pair_specs()
    core = _specs_by_name()
    names = tuple(spec.name for spec in specs)
    assert len(names) == len(set(names))
    assert names[-len(PAIR_NAMES):] == PAIR_NAMES
    assert all(name not in core for name in PAIR_NAMES)

    positions = {name: index for index, name in enumerate(names)}
    available = set(core) | set(names)
    assert all(
        dependency in available
        for spec in specs
        for dependency in spec.dependencies
    )
    assert all(
        dependency not in positions or positions[dependency] < positions[spec.name]
        for spec in specs
        for dependency in spec.dependencies
    )

    pair_names = set(PAIR_NAMES)
    boundary = []
    for spec in pair_specs:
        for dependency in spec.dependencies:
            if dependency not in pair_names and dependency not in boundary:
                boundary.append(dependency)
    assert tuple(boundary) == EXPECTED_PAIR_BOUNDARY
    assert all(name in available for name in boundary)

    assert all(path.is_file() for _, path in _CANDIDATE_SOURCES)
    registry_source = (_SOURCE_ROOT / "theorems.py").read_text()
    assert "wilson_pair_order_candidate" not in registry_source
    assert all(name not in core for name in PAIR_NAMES)


def test_wilson_pair_order_stack_replays_twice_profiles_full_cut_closure() -> None:
    specs, checked, rows, local, passes, sources, graph_digest = _discovery_runs()
    print(
        "WMI WILSON PAIR ORDER GRAPH RECEIPT "
        f"nodes={len(_candidate_specs())} graph_sha256={graph_digest} "
        f"candidate_source_sha256={sources}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI WILSON PAIR ORDER PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        metadata = _row_metadata(row)
        print(
            "WMI WILSON PAIR ORDER RECEIPT "
            f"name={metadata['name']} nodes={metadata['nodes']} "
            f"depth={metadata['depth']} objects={metadata['objects']} "
            f"edges={metadata['edges']} reused={metadata['reused']} "
            f"cuts={metadata['cuts']} statement_length={metadata['statement_length']} "
            f"spec_sha256={metadata['spec_sha256']} "
            f"statement_sha256={metadata['statement_sha256']} "
            f"script_sha256={metadata['script_sha256']} "
            f"dependencies_sha256={metadata['dependencies_sha256']}",
            flush=True,
        )
        theorem = checked[spec.name]
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        assert metadata["nodes"] <= MAX_USE_CERTIFICATE_NODES
        assert metadata["depth"] <= MAX_USE_PROOF_DEPTH
        assert metadata["objects"] <= MAX_USE_CERTIFICATE_OBJECTS
        _assert_cut_spine(theorem.certificate, spec, local)


def test_wilson_pair_order_rejects_false_contracts_and_every_direct_cut_mutation() -> None:
    specs, checked, _, _, _, _, _ = _discovery_runs()
    false_formula = parse_formula("0 = S 0")
    for spec in specs:
        theorem = checked[spec.name]
        assert false_formula != theorem.formula
        assert not check((), theorem.certificate, false_formula)
        for index, dependency in enumerate(spec.dependencies):
            mutated = _mutate_cut_at(theorem.certificate, index)
            assert not check((), mutated, theorem.formula), (
                "kernel accepted replaced live dependency edge: "
                f"{spec.name}->{dependency}"
            )
