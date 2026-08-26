"""WMI-only discovery audit for the two isolated native Fermat endpoints."""

from __future__ import annotations

import gc
import resource
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
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
from peano_lab.library.fermat_endpoints_candidate import (
    balanced_mod,
    divides,
    make_fermat_endpoint_candidate_theorems,
    product_pair_mod,
)
from peano_lab.library.fermat_product_balance_candidate import (
    make_fermat_product_balance_candidate_theorems,
)
from peano_lab.library.fermat_residue_map_candidate import (
    make_fermat_residue_map_candidate_theorems,
)
from peano_lab.library.fermat_residue_product_candidate import (
    make_fermat_residue_product_candidate_theorems,
)
from peano_lab.library.fermat_residue_reindex_candidate import (
    make_fermat_residue_reindex_candidate_theorems,
)
from peano_lab.library.fermat_scale_product_candidate import (
    make_fermat_scale_product_candidate_theorems,
)
from peano_lab.library.finite_product_reindex_candidate import (
    make_finite_product_reindex_candidate,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "fermat_predecessor_exponent_mod_one",
    "fermat_little_all_inputs",
)

EXPECTED_RECURSIVE_GRAPH_NAMES = (
    "beta_range_one_entry_eq_succ",
    "beta_product_pointwise_coprime",
    "prime_range_product_coprime",
    "beta_successor_lift_exists",
    "prime_mul_index_map_exists_up_to",
    "beta_product_pointwise_scale_mod",
    "fermat_index_map_bounded",
    "prime_mul_index_map_injective",
    "beta_successor_range_reindex_aligned",
    "beta_successor_range_scale_mod",
    "prime_mul_residue_reindex_exists",
    "beta_product_reindex_fixed_last",
    "beta_product_permutation_invariant",
    "prime_mul_residue_product_balance",
    "fermat_predecessor_exponent_mod_one",
    "fermat_little_all_inputs",
)

EXPECTED_DEPENDENCIES = {
    "fermat_predecessor_exponent_mod_one": (
        "factorial_exists",
        "prime_mul_residue_product_balance",
        "prime_range_product_coprime",
        "prime_nonzero",
        "mod_eq_cancel_coprime",
        "mul_comm",
        "mul_one",
    ),
    "fermat_little_all_inputs": (
        "prime_nonzero",
        "nonzero_is_succ",
        "pow_successor_decompose",
        "prime_coprime_or_divides",
        "multiple_refl",
        "fermat_predecessor_exponent_mod_one",
        "mod_eq_mul_right",
        "one_mul",
        "multiple_mul_left",
        "add_comm",
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


def _candidate_sources() -> tuple[tuple[TheoremSpec, ...], tuple[TheoremSpec, ...]]:
    prerequisites = (
        make_fermat_residue_product_candidate_theorems(TheoremSpec)
        + make_fermat_residue_map_candidate_theorems(TheoremSpec)
        + make_fermat_scale_product_candidate_theorems(TheoremSpec)
        + make_fermat_residue_reindex_candidate_theorems(TheoremSpec)
        + make_finite_product_reindex_candidate(TheoremSpec)
        + make_fermat_product_balance_candidate_theorems(TheoremSpec)
    )
    targets = make_fermat_endpoint_candidate_theorems(TheoremSpec)
    return prerequisites, targets


def _graph_digest(specs: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(
        "\x1f".join(
            (
                item.name,
                item.statement,
                "\x1e".join(item.script),
                "\x1e".join(item.dependencies),
            )
        )
        for item in specs
    )
    return sha256(payload.encode()).hexdigest()


def _fresh_replayer():
    prerequisites, targets = _candidate_sources()
    core = _specs_by_name()
    local: dict[str, TheoremSpec] = {}
    for candidate in prerequisites + targets:
        if candidate.name in core:
            assert core[candidate.name] == candidate
        else:
            assert candidate.name not in local
            local[candidate.name] = candidate
    assert all(item.name not in core for item in targets)

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

    return targets, local, core, run


def _cold_rows():
    started = perf_counter()
    starting_peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    replay.cache_clear()
    _specs_by_name.cache_clear()
    targets, local, _, run = _fresh_replayer()
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
                sha256(spec.statement.encode()).hexdigest(),
                sha256("\n".join(spec.script).encode()).hexdigest(),
                sha256("\0".join(spec.dependencies).encode()).hexdigest(),
            )
        )
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
    balance_name = "prime_mul_residue_product_balance"
    checked[balance_name] = run(balance_name)
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    prerequisites, _ = _candidate_sources()
    graph_digest = _graph_digest(prerequisites + targets)
    receipt = _PassReceipt(
        duration_seconds=perf_counter() - started,
        peak_rss_kib=peak_rss,
        peak_rss_growth_kib=max(0, peak_rss - starting_peak_rss),
    )
    return targets, checked, tuple(rows), local, graph_digest, receipt


@lru_cache(maxsize=1)
def _discovery_runs():
    first = _cold_rows()
    first_rows = first[2]
    first_graph_digest = first[4]
    first_receipt = first[5]
    del first
    gc.collect()
    second = _cold_rows()
    assert second[2] == first_rows
    assert second[4] == first_graph_digest
    return second[:4] + ((first_receipt, second[5]), second[4])


def _assert_cut_spine(certificate: Proof, spec: TheoremSpec, local) -> None:
    body = certificate
    core = _specs_by_name()
    for dependency in spec.dependencies:
        assert type(body) is Cut
        dependency_spec = local[dependency] if dependency in local else core[dependency]
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


def _mutate_cut_path(certificate: Proof, path: tuple[int, ...]) -> Proof:
    """Mutate a Cut, descending into selected dependency lemmas as requested."""

    assert path
    index, *nested = path
    if not nested:
        return _mutate_cut_at(certificate, index)
    assert type(certificate) is Cut
    if index == 0:
        return replace(
            certificate,
            lemma=_mutate_cut_path(certificate.lemma, tuple(nested)),
        )
    return replace(
        certificate,
        body=_mutate_cut_path(certificate.body, (index - 1, *nested)),
    )


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
        "statement_sha256": statement_digest,
        "script_sha256": script_digest,
        "dependencies_sha256": dependencies_digest,
    }


def wmi_receipt_metadata() -> dict[str, object]:
    """Expose deterministic endpoint discovery evidence to the WMI runner."""

    _, _, rows, _, passes, graph_digest = _discovery_runs()
    prerequisites, targets = _candidate_sources()
    graph_names = tuple(item.name for item in prerequisites + targets)
    assert graph_names == EXPECTED_RECURSIVE_GRAPH_NAMES
    return {
        "graph_sha256": graph_digest,
        "recursive_graph_names": list(graph_names),
        "discovery_passes": [
            {
                "pass_index": index,
                "duration_seconds": receipt.duration_seconds,
                "peak_rss_kib": receipt.peak_rss_kib,
                "peak_rss_growth_kib": receipt.peak_rss_growth_kib,
            }
            for index, receipt in enumerate(passes, start=1)
        ],
        "endpoints": [_row_metadata(row) for row in rows],
    }


def test_fermat_endpoint_contracts_are_deterministic_closed_expanded_pa() -> None:
    first = make_fermat_endpoint_candidate_theorems(TheoremSpec)
    second = make_fermat_endpoint_candidate_theorems(TheoremSpec)
    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES

    for item in first:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert _closed_formula(item.statement) == formula
        assert formula == parse_formula(item.statement)
        assert len(item.statement) < 8_192
        assert all(
            token not in item.statement
            for token in (
                "Dvd(",
                "ModEq(",
                "Pow(",
                "Prime(",
                "%",
                "^",
                "∣",
            )
        )


def test_fermat_endpoint_helpers_are_exact_alpha_stable_and_fail_closed() -> None:
    assert balanced_mod("p", "A", "1", tag="exact") == (
        "exists fep_mod_left_exact fep_mod_right_exact. "
        "A + p * fep_mod_left_exact = 1 + p * fep_mod_right_exact"
    )
    assert divides("p", "a", tag="exact") == (
        "exists fep_factor_exact. a = p * fep_factor_exact"
    )
    assert product_pair_mod("p", "x", "A", "x", "1", tag="exact") == (
        "exists fep_product_mod_left_exact fep_product_mod_right_exact. "
        "(x * A) + p * fep_product_mod_left_exact = "
        "(x * 1) + p * fep_product_mod_right_exact"
    )

    surfaces = {
        balanced_mod("p", "A", "1", tag="audit_mod"): {"p", "A"},
        divides("p", "a", tag="audit_divides"): {"p", "a"},
        product_pair_mod("p", "x", "A", "x", "1", tag="audit_products"): {
            "p",
            "x",
            "A",
        },
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    alpha_pairs = (
        (
            balanced_mod("p", "A", "1", tag="alpha_mod_left"),
            balanced_mod("p", "A", "1", tag="alpha_mod_right"),
        ),
        (
            divides("p", "a", tag="alpha_divides_left"),
            divides("p", "a", tag="alpha_divides_right"),
        ),
        (
            product_pair_mod(
                "p", "x", "A", "x", "1", tag="alpha_product_left"
            ),
            product_pair_mod(
                "p", "x", "A", "x", "1", tag="alpha_product_right"
            ),
        ),
    )
    for alpha_left, alpha_right in alpha_pairs:
        assert alpha_left != alpha_right
        assert parse_formula(alpha_left) == parse_formula(alpha_right)

    with pytest.raises(ValueError, match="Peano identifier"):
        balanced_mod("p", "A + 1", "1", tag="bad_term")
    with pytest.raises(ValueError, match="Peano identifier"):
        product_pair_mod("p", "x", "A", "x", "0", tag="bad_numeral")
    with pytest.raises(ValueError, match="Peano identifier"):
        balanced_mod("p", "A", "2", tag="bad_two")
    with pytest.raises(ValueError, match="Peano identifier"):
        product_pair_mod("p", "x", "A", "x", "S n", tag="bad_successor")
    with pytest.raises(ValueError, match="Peano identifier"):
        balanced_mod("1", "A", "1", tag="bad_modulus_one")
    with pytest.raises(ValueError, match="Peano identifier"):
        product_pair_mod("1", "x", "A", "x", "1", tag="bad_product_modulus")
    with pytest.raises(ValueError, match="Peano identifier"):
        divides("1", "a", tag="bad_divisor_one")
    with pytest.raises(ValueError, match="Peano identifier"):
        divides("p", "1", tag="bad_dividend_one")
    with pytest.raises(ValueError, match="binder tag"):
        divides("p", "a", tag="bad tag")

    capture_attempts = (
        lambda: balanced_mod(
            "p",
            "fep_mod_left_capture_mod_left",
            "1",
            tag="capture_mod_left",
        ),
        lambda: balanced_mod(
            "p",
            "A",
            "fep_mod_right_capture_mod_right",
            tag="capture_mod_right",
        ),
        lambda: divides(
            "p", "fep_factor_capture_factor", tag="capture_factor"
        ),
        lambda: product_pair_mod(
            "p",
            "fep_product_mod_left_capture_product_left",
            "A",
            "x",
            "1",
            tag="capture_product_left",
        ),
        lambda: product_pair_mod(
            "p",
            "x",
            "A",
            "x",
            "fep_product_mod_right_capture_product_right",
            tag="capture_product_right",
        ),
    )
    for attempt in capture_attempts:
        with pytest.raises(ValueError, match="captures an argument"):
            attempt()


def test_fermat_endpoint_dependency_boundary_is_exact_acyclic_and_isolated() -> None:
    prerequisites, targets = _candidate_sources()
    core = _specs_by_name()
    assert all(item.name not in core for item in targets)
    ordered = prerequisites + targets
    assert len(ordered) == 16
    assert tuple(item.name for item in ordered) == EXPECTED_RECURSIVE_GRAPH_NAMES
    assert len({item.name for item in ordered}) == len(ordered)
    available = set(core) | {item.name for item in ordered}
    positions = {item.name: index for index, item in enumerate(ordered)}
    assert all(
        dependency in available
        for item in ordered
        for dependency in item.dependencies
    )
    assert all(
        dependency not in positions or positions[dependency] < positions[item.name]
        for item in ordered
        for dependency in item.dependencies
    )


def test_fermat_endpoints_replay_twice_profile_and_check_cut_spines() -> None:
    specs, checked, rows, local, passes, graph_digest = _discovery_runs()
    print(
        "WMI FERMAT ENDPOINT GRAPH RECEIPT "
        f"nodes={len(EXPECTED_RECURSIVE_GRAPH_NAMES)} "
        f"graph_sha256={graph_digest}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI FERMAT ENDPOINT PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        (
            name,
            nodes,
            depth,
            objects,
            edges,
            reused,
            cuts,
            length,
            statement_digest,
            script_digest,
            dependencies_digest,
        ) = row
        print(
            "WMI FERMAT ENDPOINT RECEIPT "
            f"name={name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused} cuts={cuts} "
            f"statement_length={length} statement_sha256={statement_digest} "
            f"script_sha256={script_digest} "
            f"dependencies_sha256={dependencies_digest}",
            flush=True,
        )
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert depth <= MAX_USE_PROOF_DEPTH
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS
        _assert_cut_spine(checked[name].certificate, spec, local)


def test_fermat_endpoints_reject_contract_and_dependency_cut_mutations() -> None:
    specs, checked, _, _, _, _ = _discovery_runs()
    by_name = {item.name: item for item in specs}
    prerequisites, _ = _candidate_sources()
    prerequisite_by_name = {item.name: item for item in prerequisites}

    predecessor_spec = by_name["fermat_predecessor_exponent_mod_one"]
    predecessor = checked[predecessor_spec.name]
    predecessor_marker = "= 1 + p * fep_mod_right_predecessor_result"
    assert predecessor_spec.statement.count(predecessor_marker) == 1
    false_predecessor = parse_formula(
        predecessor_spec.statement.replace(
            predecessor_marker,
            "= S 1 + p * fep_mod_right_predecessor_result",
        )
    )
    assert not check((), predecessor.certificate, false_predecessor)
    balance_index = predecessor_spec.dependencies.index(
        "prime_mul_residue_product_balance"
    )
    assert not check(
        (),
        _mutate_cut_at(predecessor.certificate, balance_index),
        predecessor.formula,
    )

    balance_spec = prerequisite_by_name["prime_mul_residue_product_balance"]
    balance = checked[balance_spec.name]
    general_reindex_index = balance_spec.dependencies.index(
        "beta_product_permutation_invariant"
    )
    assert not check(
        (),
        _mutate_cut_path(balance.certificate, (general_reindex_index,)),
        balance.formula,
    )
    assert not check(
        (),
        _mutate_cut_path(
            predecessor.certificate,
            (balance_index, general_reindex_index),
        ),
        predecessor.formula,
    )

    all_spec = by_name["fermat_little_all_inputs"]
    all_inputs = checked[all_spec.name]
    all_marker = "= a + p * fep_mod_right_all_result"
    assert all_spec.statement.count(all_marker) == 1
    false_all = parse_formula(
        all_spec.statement.replace(
            all_marker,
            "= S a + p * fep_mod_right_all_result",
        )
    )
    assert not check((), all_inputs.certificate, false_all)
    predecessor_index = all_spec.dependencies.index(
        "fermat_predecessor_exponent_mod_one"
    )
    assert not check(
        (),
        _mutate_cut_at(all_inputs.certificate, predecessor_index),
        all_inputs.formula,
    )
    assert not check(
        (),
        _mutate_cut_path(
            all_inputs.certificate,
            (predecessor_index, balance_index, general_reindex_index),
        ),
        all_inputs.formula,
    )
