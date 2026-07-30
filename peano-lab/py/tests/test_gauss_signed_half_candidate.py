"""WMI-only recursive discovery audit for the signed-half Gauss candidates."""

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
from peano_lab.kernel.formulas import (
    Eq,
    Formula,
    Imp,
    parse_formula,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.gauss_signed_half_candidate import (
    _balanced_mod,
    make_gauss_signed_half_candidate_theorems,
    strictly_below,
    weakly_below,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


REFLECTION_NAME = "odd_upper_remainder_reflection"
POINTWISE_NAME = "gauss_pointwise_signed_half_representative"
EXPECTED_NAMES = (REFLECTION_NAME, POINTWISE_NAME)

EXPECTED_DEPENDENCIES = {
    REFLECTION_NAME: (
        "add_assoc",
        "add_comm",
        "mul_succ_left",
        "mul_zero_left",
        "zero_add",
        "add_succ_left",
        "add_right_cancel",
    ),
    POINTWISE_NAME: (
        "add_assoc",
        "add_comm",
        "mul_succ_left",
        "mul_one",
        "le_or_lt",
        "one_le_of_ne_zero",
        "remainder_decomposition_to_mod_eq",
        REFLECTION_NAME,
        "mod_eq_trans",
    ),
}

EXPECTED_CORE_BOUNDARY = (
    "add_assoc",
    "add_comm",
    "mul_succ_left",
    "mul_zero_left",
    "zero_add",
    "add_succ_left",
    "add_right_cancel",
    "mul_one",
    "le_or_lt",
    "one_le_of_ne_zero",
    "remainder_decomposition_to_mod_eq",
    "mod_eq_trans",
)

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_CANDIDATE_SOURCE = _SOURCE_ROOT / "gauss_signed_half_candidate.py"

_FALSE_CONTRACT_REWRITES = {
    REFLECTION_NAME: ("r + m = p", "r + m = S p"),
    POINTWISE_NAME: (
        "((2 * h) * m) + p * gsh_mod_right_product_upper",
        "(S ((2 * h) * m)) + p * gsh_mod_right_product_upper",
    ),
}


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
    return make_gauss_signed_half_candidate_theorems(TheoremSpec)


def _expected_statements() -> dict[str, str]:
    reflection_positive = strictly_below("0", "m", tag="reflection_positive")
    reflection_bounded = weakly_below("m", "h", tag="reflection_bounded")
    reflection_result = (
        f"exists m. ({reflection_positive}) /\\ "
        f"(({reflection_bounded}) /\\ r + m = p)"
    )

    product_variables = ("p", "h", "a", "x", "q", "r", "m")
    product_positive = strictly_below("0", "m", tag="product_positive")
    product_bounded = weakly_below("m", "h", tag="product_bounded")
    product_lower = _balanced_mod(
        "p",
        "a * x",
        "m",
        variables=product_variables,
        tag="product_lower",
    )
    product_upper = _balanced_mod(
        "p",
        "a * x",
        "(2 * h) * m",
        variables=product_variables,
        tag="product_upper",
    )
    product_result = (
        f"exists m. ({product_positive}) /\\ "
        f"(({product_bounded}) /\\ "
        f"(({product_lower}) \\/ ({product_upper})))"
    )
    remainder_bound = strictly_below("r", "p", tag="product_remainder")

    return {
        REFLECTION_NAME: (
            "forall p h r. p = 2 * h + 1 -> "
            f"({strictly_below('r', 'p', tag='reflection_remainder')}) -> "
            f"({strictly_below('h', 'r', tag='reflection_upper')}) -> "
            f"({reflection_result})"
        ),
        POINTWISE_NAME: (
            "forall p h a x q r. p = 2 * h + 1 -> "
            "a * x = q * p + r -> "
            f"({remainder_bound}) -> ~(r = 0) -> ({product_result})"
        ),
    }


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
    payload = "\x1c".join(_spec_digest(spec) for spec in specs)
    return sha256(payload.encode()).hexdigest()


def _source_digest() -> str:
    return sha256(_CANDIDATE_SOURCE.read_bytes()).hexdigest()


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
    starting_peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
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

    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt = _PassReceipt(
        duration_seconds=perf_counter() - started,
        peak_rss_kib=peak_rss,
        peak_rss_growth_kib=max(0, peak_rss - starting_peak_rss),
    )
    return (
        specs,
        checked,
        tuple(rows),
        local,
        _source_digest(),
        _graph_digest(specs),
        receipt,
    )


@lru_cache(maxsize=1)
def _discovery_runs():
    first = _cold_rows()
    first_rows = first[2]
    first_source = first[4]
    first_graph = first[5]
    first_receipt = first[6]
    del first
    gc.collect()
    second = _cold_rows()
    assert second[2] == first_rows
    assert second[4] == first_source
    assert second[5] == first_graph
    return second[:4] + ((first_receipt, second[6]), second[4], second[5])


def _assert_cut_spine(
    certificate: Proof,
    spec: TheoremSpec,
    local: dict[str, TheoremSpec],
) -> None:
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
        return replace(
            certificate,
            proposition=Eq(zero, zero),
            lemma=EqRefl(zero),
        )
    return replace(certificate, body=_mutate_cut_at(certificate.body, index - 1))


def _row_metadata(row: tuple[object, ...]) -> dict[str, object]:
    (
        name,
        nodes,
        depth,
        objects,
        edges,
        reused,
        cuts,
        length,
        spec_digest,
        statement_digest,
        script_digest,
        dependencies_digest,
    ) = row
    return {
        "name": name,
        "nodes": nodes,
        "depth": depth,
        "objects": objects,
        "edges": edges,
        "reused": reused,
        "cuts": cuts,
        "statement_length": length,
        "spec_sha256": spec_digest,
        "statement_sha256": statement_digest,
        "script_sha256": script_digest,
        "dependencies_sha256": dependencies_digest,
    }


def wmi_receipt_metadata() -> dict[str, object]:
    """Expose deterministic recursive signed-half discovery evidence to WMI."""

    _, _, rows, _, passes, source_digest, graph_digest = _discovery_runs()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    return {
        "candidate_source_sha256": source_digest,
        "graph_sha256": graph_digest,
        "recursive_graph_names": list(EXPECTED_NAMES),
        "discovery_passes": [
            {
                "pass_index": index,
                "duration_seconds": receipt.duration_seconds,
                "peak_rss_kib": receipt.peak_rss_kib,
                "peak_rss_growth_kib": receipt.peak_rss_growth_kib,
                "candidate_source_sha256": source_digest,
            }
            for index, receipt in enumerate(passes, start=1)
        ],
        "candidates": [_row_metadata(row) for row in rows],
    }


def test_gauss_signed_half_contracts_are_exact_deterministic_closed_expanded_pa() -> None:
    first = make_gauss_signed_half_candidate_theorems(TheoremSpec)
    second = make_gauss_signed_half_candidate_theorems(TheoremSpec)
    assert second == first
    assert len(first) == 2
    assert tuple(spec.name for spec in first) == EXPECTED_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES
    assert {spec.name: spec.statement for spec in first} == _expected_statements()

    for spec in first:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert _closed_formula(spec.statement) == formula
        assert formula == parse_formula(spec.statement)
        assert len(spec.statement) < 8_192
        assert all("DNE" not in command for command in spec.script)
        assert all(
            token not in spec.statement
            for token in (
                "ModEq(",
                "DivRem(",
                "Prime(",
                "Lt(",
                "<=",
                "%",
                "^",
                "<",
                "∣",
            )
        )

    by_name = {spec.name: spec for spec in first}
    reflection = by_name[REFLECTION_NAME]
    pointwise = by_name[POINTWISE_NAME]
    assert reflection.statement.startswith("forall p h r. p = 2 * h + 1 ->")
    assert reflection.statement.endswith("r + m = p))")
    assert pointwise.statement.startswith(
        "forall p h a x q r. p = 2 * h + 1 -> a * x = q * p + r ->"
    )
    assert "~(r = 0)" in pointwise.statement
    assert "((2 * h) * m)" in pointwise.statement
    assert "p - 1" not in pointwise.statement


def test_gauss_signed_half_helpers_are_hygienic_alpha_native_and_witnesses_audited() -> None:
    assert strictly_below("r", "p", tag="exact") == (
        "exists gsh_lt_gap_exact. gsh_lt_gap_exact + S r = p"
    )
    assert strictly_below("0", "m", tag="positive") == (
        "exists gsh_lt_gap_positive. gsh_lt_gap_positive + S 0 = m"
    )
    assert weakly_below("m", "h", tag="exact") == (
        "exists gsh_le_gap_exact. gsh_le_gap_exact + m = h"
    )
    exact_mod = _balanced_mod(
        "p",
        "a * x",
        "m",
        variables=("p", "a", "x", "m"),
        tag="exact",
    )
    assert exact_mod == (
        "exists gsh_mod_left_exact gsh_mod_right_exact. "
        "(a * x) + p * gsh_mod_left_exact = "
        "(m) + p * gsh_mod_right_exact"
    )

    alpha_pairs = (
        (
            strictly_below("r", "p", tag="alpha_left"),
            strictly_below("r", "p", tag="alpha_right"),
        ),
        (
            weakly_below("m", "h", tag="alpha_left"),
            weakly_below("m", "h", tag="alpha_right"),
        ),
        (
            _balanced_mod(
                "p",
                "a * x",
                "m",
                variables=("p", "a", "x", "m"),
                tag="alpha_left",
            ),
            _balanced_mod(
                "p",
                "a * x",
                "m",
                variables=("p", "a", "x", "m"),
                tag="alpha_right",
            ),
        ),
    )
    for left, right in alpha_pairs:
        assert left != right
        assert parse_formula(left) == parse_formula(right)

    surfaces = {
        strictly_below("r", "p", tag="free_strict"): {"r", "p"},
        strictly_below("0", "m", tag="free_positive"): {"m"},
        weakly_below("m", "h", tag="free_weak"): {"m", "h"},
        exact_mod: {"p", "a", "x", "m"},
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    invalid_calls = (
        lambda: strictly_below("r + 1", "p", tag="bad_lower"),
        lambda: strictly_below("r", "S p", tag="bad_upper"),
        lambda: weakly_below("m", "h", tag="bad tag"),
        lambda: _balanced_mod(
            "p",
            "a",
            "m",
            variables=("a", "m"),
            tag="missing_modulus",
        ),
        lambda: _balanced_mod(
            "p",
            "a",
            "m",
            variables=("p", "a + 1", "m"),
            tag="bad_variable",
        ),
    )
    for call in invalid_calls:
        with pytest.raises(ValueError):
            call()

    with pytest.raises(ValueError, match="captures an argument"):
        strictly_below("gsh_lt_gap_capture", "p", tag="capture")
    with pytest.raises(ValueError, match="captures an argument"):
        _balanced_mod(
            "p",
            "a",
            "m",
            variables=("p", "a", "m", "gsh_mod_left_capture"),
            tag="capture",
        )

    by_name = {spec.name: spec for spec in _candidate_specs()}
    reflection_script = by_name[REFLECTION_NAME].script
    pointwise_script = by_name[POINTWISE_NAME].script
    assert reflection_script.count("exists (S x1)") == 1
    assert reflection_script.count("have hrm : r + S x1 = p") == 1
    assert reflection_script.count("have hmle : exists d. d + S x1 = h") == 1
    assert pointwise_script.count("exists x1") == 2
    assert pointwise_script.count("exists 1") == 1
    assert pointwise_script.count(
        "trans (r + x1) + (2 * h) * x1"
    ) == 1
    assert "ring" not in reflection_script
    assert "ring" not in pointwise_script
    assert pointwise_script.count(
        "specialize mod_eq_trans ((2 * h) * x1)"
    ) == 1

    # Independent bounded arithmetic audit of both constructive branches and
    # the exact upper balanced-congruence witnesses (u=m, v=1).
    for h in range(1, 33):
        p = 2 * h + 1
        for r in range(1, p):
            if r <= h:
                m = r
                assert 0 < m <= h
                for q in range(4):
                    value = q * p + r
                    assert value + p * 0 == m + p * q
            else:
                m = p - r
                d = r - h - 1
                assert 0 < m <= h
                assert r + m == p
                assert d + m == h
                assert r + p * m == (2 * h) * m + p * 1
                for q in range(4):
                    value = q * p + r
                    assert value + p * m == (2 * h) * m + p * (q + 1)


def test_gauss_signed_half_graph_is_exact_core_bounded_and_source_isolated() -> None:
    specs = _candidate_specs()
    core = _specs_by_name()
    assert len(specs) == 2
    assert tuple(spec.name for spec in specs) == EXPECTED_NAMES
    assert len({spec.name for spec in specs}) == 2
    assert all(spec.name not in core for spec in specs)

    local_names = set(EXPECTED_NAMES)
    available = set(core) | local_names
    positions = {spec.name: index for index, spec in enumerate(specs)}
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
    boundary = []
    for spec in specs:
        for dependency in spec.dependencies:
            if dependency not in local_names and dependency not in boundary:
                boundary.append(dependency)
    assert tuple(boundary) == EXPECTED_CORE_BOUNDARY
    assert all(name in core for name in EXPECTED_CORE_BOUNDARY)
    assert _CANDIDATE_SOURCE.is_file()
    assert "gauss_signed_half_candidate" not in (
        _SOURCE_ROOT / "theorems.py"
    ).read_text()

    by_name = {spec.name: spec for spec in specs}
    assert {
        dependency
        for dependency in by_name[POINTWISE_NAME].dependencies
        if dependency in local_names
    } == {REFLECTION_NAME}
    assert all(
        dependency in core
        for dependency in by_name[REFLECTION_NAME].dependencies
    )


def test_gauss_signed_half_stack_replays_twice_profiles_full_cut_closure() -> None:
    specs, checked, rows, local, passes, source_digest, graph_digest = (
        _discovery_runs()
    )
    print(
        "WMI GAUSS SIGNED HALF GRAPH RECEIPT "
        f"nodes={len(EXPECTED_NAMES)} graph_sha256={graph_digest} "
        f"candidate_source_sha256={source_digest}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI GAUSS SIGNED HALF PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        metadata = _row_metadata(row)
        print(
            "WMI GAUSS SIGNED HALF RECEIPT "
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
        assert metadata["nodes"] <= MAX_USE_CERTIFICATE_NODES
        assert metadata["depth"] <= MAX_USE_PROOF_DEPTH
        assert metadata["objects"] <= MAX_USE_CERTIFICATE_OBJECTS
        theorem = checked[spec.name]
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        _assert_cut_spine(theorem.certificate, spec, local)


def test_gauss_signed_half_rejects_false_contracts_and_every_direct_cut_mutation() -> None:
    specs, checked, _, _, _, _, _ = _discovery_runs()
    assert set(_FALSE_CONTRACT_REWRITES) == set(EXPECTED_NAMES)
    for spec in specs:
        theorem = checked[spec.name]
        marker, replacement = _FALSE_CONTRACT_REWRITES[spec.name]
        assert marker != replacement
        assert spec.statement.count(marker) == 1
        false_contract = parse_formula(spec.statement.replace(marker, replacement))
        assert false_contract != theorem.formula
        assert not check((), theorem.certificate, false_contract)

        for index, dependency in enumerate(spec.dependencies):
            mutated = _mutate_cut_at(theorem.certificate, index)
            assert not check((), mutated, theorem.formula), (
                "kernel accepted replaced live dependency edge: "
                f"{spec.name}->{dependency}"
            )
