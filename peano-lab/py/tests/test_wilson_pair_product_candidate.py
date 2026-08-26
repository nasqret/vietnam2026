"""WMI-only recursive discovery audit for the Wilson pair-product stack."""

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
from peano_lab.library.finite_fold_surface import (
    _beta_at_term as canonical_beta_at_term,
    _product_relation_term as canonical_product_relation_term,
    beta_at as canonical_beta_at,
    product_relation as canonical_product_relation,
    product_successor_relation as canonical_product_successor_relation,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)
from peano_lab.library.wilson_pair_product_candidate import (
    _adjacent_unit_pairs_term,
    _beta_at_term,
    _mod_eq_term,
    _product_relation_term,
    _two_factor_decomposition,
    adjacent_unit_pairs,
    make_wilson_pair_product_candidate_theorems,
    mod_eq,
    product_relation,
)


DOUBLE_NAME = "beta_product_double_succ_decompose"
PAIRS_NAME = "beta_adjacent_unit_pairs_product_one"
EXPECTED_NAMES = (DOUBLE_NAME, PAIRS_NAME)

EXPECTED_DEPENDENCIES = {
    DOUBLE_NAME: ("beta_product_succ_decompose",),
    PAIRS_NAME: (
        DOUBLE_NAME,
        "beta_product_zero",
        "le_succ",
        "le_refl",
        "mod_eq_refl",
        "mod_eq_mul",
        "add_succ_left",
        "mul_assoc",
        "one_mul",
    ),
}

EXPECTED_CORE_BOUNDARY = (
    "beta_product_succ_decompose",
    "beta_product_zero",
    "le_succ",
    "le_refl",
    "mod_eq_refl",
    "mod_eq_mul",
    "add_succ_left",
    "mul_assoc",
    "one_mul",
)

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_CANDIDATE_SOURCE = _SOURCE_ROOT / "wilson_pair_product_candidate.py"

_FALSE_CONTRACT_REWRITES = {
    DOUBLE_NAME: (
        "Q = (wpp_prefix_product_two_result * "
        "wpp_left_factor_two_result) * wpp_right_factor_two_result",
        "Q = S ((wpp_prefix_product_two_result * "
        "wpp_left_factor_two_result) * wpp_right_factor_two_result)",
    ),
    PAIRS_NAME: (
        "= (1) + p * wpp_mod_right_pair_result",
        "= (S 1) + p * wpp_mod_right_pair_result",
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
    return make_wilson_pair_product_candidate_theorems(TheoremSpec)


def _expected_statements() -> dict[str, str]:
    two_product = product_relation("b", "c", "l", "Q", tag="two_product")
    two_result = _two_factor_decomposition(
        "b",
        "c",
        "k",
        "Q",
        tag="two_result",
        avoid=("b", "c", "k", "l", "Q"),
    )
    pair_hypothesis = adjacent_unit_pairs("p", "b", "c", "m", tag="pairs")
    pair_product = _product_relation_term(
        "b",
        "c",
        "m + m",
        "Q",
        tag="pair_product",
        avoid=("p", "b", "c", "m", "Q"),
    )
    pair_result = _mod_eq_term(
        "p",
        "Q",
        "1",
        tag="pair_result",
        avoid=("p", "b", "c", "m", "Q"),
    )
    return {
        DOUBLE_NAME: (
            f"forall b c k l Q. l = S (S k) -> ({two_product}) -> "
            f"({two_result})"
        ),
        PAIRS_NAME: (
            f"forall p b c m Q. ({pair_hypothesis}) -> ({pair_product}) -> "
            f"({pair_result})"
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
    """Expose deterministic recursive Wilson pair-product evidence to WMI."""

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


def test_wilson_pair_product_contracts_are_exact_deterministic_closed_expanded_pa() -> None:
    first = make_wilson_pair_product_candidate_theorems(TheoremSpec)
    second = make_wilson_pair_product_candidate_theorems(TheoremSpec)
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
                "BetaAt(",
                "Product(",
                "ModEq(",
                "Lt(",
                "%",
                "^",
                "<",
                "∣",
            )
        )

    by_name = {spec.name: spec for spec in first}
    double = by_name[DOUBLE_NAME]
    pairs = by_name[PAIRS_NAME]
    assert double.statement.startswith("forall b c k l Q. l = S (S k) ->")
    assert "Q = (wpp_prefix_product_two_result *" in double.statement
    assert pairs.statement.startswith("forall p b c m Q.")
    assert "forall l" not in pairs.statement
    assert "m + m" in pairs.statement
    assert "S (wpp_pair_pairs + wpp_pair_pairs)" in pairs.statement
    assert pairs.statement.endswith(
        "(1) + p * wpp_mod_right_pair_result)"
    )


def test_wilson_pair_product_helpers_are_exact_hygienic_alpha_equal_and_guard_normalization() -> None:
    assert mod_eq("p", "Q", "R", tag="exact") == (
        "exists wpp_mod_left_exact wpp_mod_right_exact. "
        "(Q) + p * wpp_mod_left_exact = (R) + p * wpp_mod_right_exact"
    )

    local_at = _beta_at_term(
        "b", "c", "i", "x", tag="local_at", avoid=("b", "c", "i", "x")
    )
    public_at = canonical_beta_at("b", "c", "i", "x", tag="public_at")
    assert local_at != public_at
    assert parse_formula(local_at) == parse_formula(public_at)

    local_product = product_relation("b", "c", "l", "Q", tag="local_product")
    public_product = canonical_product_relation(
        "b", "c", "l", "Q", tag="public_product"
    )
    assert local_product != public_product
    assert parse_formula(local_product) == parse_formula(public_product)

    canonical_left_entry = canonical_beta_at_term(
        "b",
        "c",
        "t + t",
        "x",
        tag="canonical_pairs_left",
        avoid=("p", "b", "c", "m", "t", "x", "y"),
    )
    canonical_right_entry = canonical_beta_at_term(
        "b",
        "c",
        "S (t + t)",
        "y",
        tag="canonical_pairs_right",
        avoid=("p", "b", "c", "m", "t", "x", "y"),
    )
    canonical_pairs = (
        "forall t x y. (exists canonical_pair_gap. "
        "canonical_pair_gap + S t = m) -> "
        f"({canonical_left_entry}) -> ({canonical_right_entry}) -> "
        "(exists canonical_pair_left canonical_pair_right. "
        "(x * y) + p * canonical_pair_left = "
        "(1) + p * canonical_pair_right)"
    )
    local_pairs = adjacent_unit_pairs(
        "p", "b", "c", "m", tag="canonical_pairs_local"
    )
    assert parse_formula(local_pairs) == parse_formula(canonical_pairs)

    canonical_two_left = canonical_beta_at_term(
        "b",
        "c",
        "k",
        "x",
        tag="canonical_two_left",
        avoid=("b", "c", "k", "Q", "x", "y", "R"),
    )
    canonical_two_right = canonical_beta_at_term(
        "b",
        "c",
        "S k",
        "y",
        tag="canonical_two_right",
        avoid=("b", "c", "k", "Q", "x", "y", "R"),
    )
    canonical_two_prefix = canonical_product_relation_term(
        "b",
        "c",
        "k",
        "R",
        tag="canonical_two_prefix",
        avoid=("b", "c", "k", "Q", "x", "y", "R"),
    )
    canonical_two = (
        f"exists x y R. ({canonical_two_left}) /\\ "
        f"(({canonical_two_right}) /\\ (({canonical_two_prefix}) /\\ "
        "Q = (R * x) * y))"
    )
    local_two = _two_factor_decomposition(
        "b",
        "c",
        "k",
        "Q",
        tag="canonical_two_local",
        avoid=("b", "c", "k", "Q"),
    )
    assert parse_formula(local_two) == parse_formula(canonical_two)

    compound_local = _product_relation_term(
        "b",
        "c",
        "m + m",
        "Q",
        tag="compound_local",
        avoid=("b", "c", "m", "Q"),
    )
    compound_canonical = canonical_product_relation_term(
        "b",
        "c",
        "m + m",
        "Q",
        tag="compound_canonical",
        avoid=("b", "c", "m", "Q"),
    )
    assert compound_local != compound_canonical
    assert parse_formula(compound_local) == parse_formula(compound_canonical)

    successor_local = _product_relation_term(
        "b",
        "c",
        "S k",
        "Q",
        tag="successor_local",
        avoid=("b", "c", "k", "Q"),
    )
    successor_canonical = canonical_product_successor_relation(
        "b", "c", "k", "Q", tag="successor_canonical"
    )
    assert parse_formula(successor_local) == parse_formula(successor_canonical)

    surfaces = {
        mod_eq("p", "Q", "R", tag="free_mod"): {"p", "Q", "R"},
        adjacent_unit_pairs("p", "b", "c", "m", tag="free_pairs"): {
            "p",
            "b",
            "c",
            "m",
        },
        compound_local: {"b", "c", "m", "Q"},
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    alpha_pairs = (
        (
            adjacent_unit_pairs("p", "b", "c", "m", tag="alpha_left"),
            adjacent_unit_pairs("p", "b", "c", "m", tag="alpha_right"),
        ),
        (
            _product_relation_term(
                "b",
                "c",
                "m + m",
                "Q",
                tag="alpha_product_left",
                avoid=("b", "c", "m", "Q"),
            ),
            _product_relation_term(
                "b",
                "c",
                "m + m",
                "Q",
                tag="alpha_product_right",
                avoid=("b", "c", "m", "Q"),
            ),
        ),
    )
    for left, right in alpha_pairs:
        assert left != right
        assert parse_formula(left) == parse_formula(right)

    raw_successor_product = _product_relation_term(
        "b",
        "c",
        "S m + S m",
        "Q",
        tag="raw_successor_product",
        avoid=("b", "c", "m", "Q"),
    )
    normalized_successor_product = _product_relation_term(
        "b",
        "c",
        "S (S (m + m))",
        "Q",
        tag="normalized_successor_product",
        avoid=("b", "c", "m", "Q"),
    )
    assert parse_formula(raw_successor_product) != parse_formula(
        normalized_successor_product
    )
    pair_script = dict((spec.name, spec.script) for spec in _candidate_specs())[
        PAIRS_NAME
    ]
    assert pair_script.count(
        "have hdouble : S m + S m = S (S (m + m))"
    ) == 1
    assert pair_script.count("simp [add_succ_left]") == 1
    assert pair_script.count(
        "specialize beta_product_double_succ_decompose (S m + S m)"
    ) == 1

    invalid_calls = (
        lambda: product_relation("b + z", "c", "l", "Q", tag="bad_code"),
        lambda: product_relation("b", "S c", "l", "Q", tag="bad_scale"),
        lambda: adjacent_unit_pairs("p", "b", "c", "S m", tag="bad_count"),
        lambda: mod_eq("p", "Q + 1", "R", tag="bad_residue"),
        lambda: mod_eq("p", "Q", "R", tag="bad tag"),
    )
    for call in invalid_calls:
        with pytest.raises(ValueError, match="Peano identifier|binder tag"):
            call()

    with pytest.raises(ValueError, match="captures an argument"):
        mod_eq("wpp_mod_left_capture", "Q", "R", tag="capture")
    with pytest.raises(ValueError, match="captures an argument"):
        product_relation(
            "wpp_trace_code_capture", "c", "l", "Q", tag="capture"
        )

    canonical_compound_at = canonical_beta_at_term(
        "b",
        "c",
        "m + m",
        "x",
        tag="canonical_compound_at",
        avoid=("b", "c", "m", "x"),
    )
    local_compound_at = _beta_at_term(
        "b",
        "c",
        "m + m",
        "x",
        tag="local_compound_at",
        avoid=("b", "c", "m", "x"),
    )
    assert parse_formula(local_compound_at) == parse_formula(canonical_compound_at)


def test_wilson_pair_product_graph_is_exact_core_bounded_and_source_isolated() -> None:
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
    assert "wilson_pair_product_candidate" not in (
        _SOURCE_ROOT / "theorems.py"
    ).read_text()

    by_name = {spec.name: spec for spec in specs}
    assert {
        dependency
        for dependency in by_name[PAIRS_NAME].dependencies
        if dependency in local_names
    } == {DOUBLE_NAME}
    assert all(
        dependency in core
        for dependency in by_name[DOUBLE_NAME].dependencies
    )


def test_wilson_pair_product_stack_replays_twice_profiles_full_cut_closure() -> None:
    specs, checked, rows, local, passes, source_digest, graph_digest = (
        _discovery_runs()
    )
    print(
        "WMI WILSON PAIR PRODUCT GRAPH RECEIPT "
        f"nodes={len(EXPECTED_NAMES)} graph_sha256={graph_digest} "
        f"candidate_source_sha256={source_digest}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI WILSON PAIR PRODUCT PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        metadata = _row_metadata(row)
        print(
            "WMI WILSON PAIR PRODUCT RECEIPT "
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


def test_wilson_pair_product_rejects_false_contracts_and_every_direct_cut_mutation() -> None:
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
