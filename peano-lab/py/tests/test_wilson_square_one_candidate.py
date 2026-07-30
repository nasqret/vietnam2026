"""WMI-only discovery audit for the isolated Wilson square-one candidate."""

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
    Formula,
    Imp,
    parse_formula,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)
from peano_lab.library.wilson_square_one_candidate import (
    make_wilson_square_one_candidate_theorems,
    positive,
    prime,
    square_one_mod,
    strictly_below,
)


EXPECTED_NAME = "prime_bounded_square_one_cases"
EXPECTED_STATEMENT = (
    "forall p n x. p = S n -> ((~(p = 1) /\\ forall "
    "wsq_prime_left_prime wsq_prime_right_prime. "
    "p = wsq_prime_left_prime * wsq_prime_right_prime -> "
    "wsq_prime_left_prime = 1 \\/ wsq_prime_right_prime = 1)) -> "
    "(exists wsq_positive_gap_positive. "
    "wsq_positive_gap_positive + 1 = x) -> "
    "(exists wsq_strict_gap_bounded. "
    "wsq_strict_gap_bounded + S x = p) -> "
    "(exists wsq_mod_left_square_one wsq_mod_right_square_one. "
    "x * x + p * wsq_mod_left_square_one = "
    "1 + p * wsq_mod_right_square_one) -> x = 1 \\/ x = n"
)
EXPECTED_DEPENDENCIES = (
    "ne_zero_of_one_le",
    "nonzero_is_succ",
    "mul_succ_left",
    "add_assoc",
    "add_comm",
    "add_left_cancel",
    "factor_difference",
    "euclid_prime_dvd_product",
    "le_succ_self",
    "lt_of_le_of_lt",
    "zero_or_succ",
    "divisor_le_nonzero",
    "lt_not_le",
    "succ_ne_zero",
    "le_antisymm",
    "succ_injective",
)

_CANDIDATE_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "peano_lab"
    / "library"
    / "wilson_square_one_candidate.py"
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


def _candidate_spec() -> TheoremSpec:
    specs = make_wilson_square_one_candidate_theorems(TheoremSpec)
    assert len(specs) == 1
    return specs[0]


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


def _source_digest() -> str:
    return sha256(_CANDIDATE_SOURCE.read_bytes()).hexdigest()


def _fresh_replayer():
    spec = _candidate_spec()
    core = _specs_by_name()
    assert spec.name not in core
    assert all(dependency in core for dependency in spec.dependencies)

    @lru_cache(maxsize=None)
    def run() -> _Checked:
        formula = _closed_formula(spec.statement)
        target = formula
        for dependency in reversed(spec.dependencies):
            target = Imp(_closed_formula(core[dependency].statement), target)

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
            checked_dependency = replay(dependency)
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )

        assert check((), body, formula)
        return _Checked(formula, body)

    return spec, core, run


def _cold_row():
    started = perf_counter()
    starting_peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    replay.cache_clear()
    _specs_by_name.cache_clear()
    spec, core, run = _fresh_replayer()
    theorem = run()
    nodes, depth = proof_metrics(theorem.certificate)
    objects, edges, reused = proof_identity_metrics(theorem.certificate)
    cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
    row = (
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
    source_digest = _source_digest()
    graph_digest = _spec_digest(spec)
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
    return spec, theorem, row, core, receipt, source_digest, graph_digest


@lru_cache(maxsize=1)
def _discovery_runs():
    first = _cold_row()
    first_row = first[2]
    first_receipt = first[4]
    first_source_digest = first[5]
    first_graph_digest = first[6]
    del first
    gc.collect()
    second = _cold_row()
    assert second[2] == first_row
    assert second[5] == first_source_digest
    assert second[6] == first_graph_digest
    return second[:4] + (
        (first_receipt, second[4]),
        second[5],
        second[6],
    )


def _assert_cut_spine(
    certificate: Proof,
    spec: TheoremSpec,
    core: dict[str, TheoremSpec],
) -> None:
    body = certificate
    for dependency in spec.dependencies:
        assert type(body) is Cut
        expected = _closed_formula(core[dependency].statement)
        assert body.proposition == expected
        assert check((), body.lemma, expected)
        assert not any(type(node) is DNE for node in _walk(body.lemma))
        body = body.body


def _mutate_cut_edge_at(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(
            certificate,
            proposition=parse_formula("0 = 0"),
            lemma=EqRefl(zero),
        )
    return replace(
        certificate,
        body=_mutate_cut_edge_at(certificate.body, index - 1),
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
    """Expose deterministic square-one discovery evidence to the WMI runner."""

    _, _, row, _, passes, source_digest, graph_digest = _discovery_runs()
    return {
        "candidate_source_sha256": source_digest,
        "graph_sha256": graph_digest,
        "direct_dependencies": list(EXPECTED_DEPENDENCIES),
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
        "candidate": _row_metadata(row),
    }


def test_wilson_square_one_contract_is_exact_deterministic_closed_expanded_pa() -> None:
    first = make_wilson_square_one_candidate_theorems(TheoremSpec)
    second = make_wilson_square_one_candidate_theorems(TheoremSpec)
    assert second == first
    assert tuple(item.name for item in first) == (EXPECTED_NAME,)
    assert first[0].statement == EXPECTED_STATEMENT
    assert first[0].dependencies == EXPECTED_DEPENDENCIES

    formula, free_names = parse_formula_with_names(first[0].statement)
    assert not free_names
    assert _closed_formula(first[0].statement) == formula
    assert formula == parse_formula(first[0].statement)
    assert len(first[0].statement) < 8_192
    assert all("DNE" not in command for command in first[0].script)
    assert all(_primitive(command)[0] != "ring" for command in first[0].script)
    square_step = first[0].script.index(
        "have hsquare : x * x = 1 + x1 * S (S x1)"
    )
    assert first[0].script[square_step + 1 : square_step + 3] == (
        "rewrite hxpred_witness",
        "rewrite hxpred_witness",
    )
    assert first[0].script.count("specialize mul_succ_left x1") == 1
    assert first[0].script.count("specialize mul_succ_left (S x1)") == 1
    assert first[0].script.count("apply PA4") == 2
    assert first[0].script.count("apply PA6") == 1
    assert all(
        token not in first[0].statement
        for token in (
            "Dvd(",
            "Lt(",
            "ModEq(",
            "Positive(",
            "Prime(",
            "SquareOne(",
            "%",
            "^",
            "<",
            "∣",
        )
    )


def test_wilson_square_one_helpers_are_exact_alpha_stable_and_fail_closed() -> None:
    assert positive("x", tag="exact") == (
        "exists wsq_positive_gap_exact. wsq_positive_gap_exact + 1 = x"
    )
    assert strictly_below("x", "p", tag="exact") == (
        "exists wsq_strict_gap_exact. wsq_strict_gap_exact + S x = p"
    )
    assert prime("p", tag="exact") == (
        "(~(p = 1) /\\ forall wsq_prime_left_exact wsq_prime_right_exact. "
        "p = wsq_prime_left_exact * wsq_prime_right_exact -> "
        "wsq_prime_left_exact = 1 \\/ wsq_prime_right_exact = 1)"
    )
    assert square_one_mod("p", "x", tag="exact") == (
        "exists wsq_mod_left_exact wsq_mod_right_exact. "
        "x * x + p * wsq_mod_left_exact = 1 + p * wsq_mod_right_exact"
    )

    surfaces = {
        positive("x", tag="free_positive"): {"x"},
        strictly_below("x", "p", tag="free_bound"): {"x", "p"},
        prime("p", tag="free_prime"): {"p"},
        square_one_mod("p", "x", tag="free_mod"): {"p", "x"},
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    alpha_pairs = (
        (
            positive("x", tag="alpha_positive_left"),
            positive("x", tag="alpha_positive_right"),
        ),
        (
            strictly_below("x", "p", tag="alpha_bound_left"),
            strictly_below("x", "p", tag="alpha_bound_right"),
        ),
        (
            prime("p", tag="alpha_prime_left"),
            prime("p", tag="alpha_prime_right"),
        ),
        (
            square_one_mod("p", "x", tag="alpha_mod_left"),
            square_one_mod("p", "x", tag="alpha_mod_right"),
        ),
    )
    for alpha_left, alpha_right in alpha_pairs:
        assert alpha_left != alpha_right
        assert parse_formula(alpha_left) == parse_formula(alpha_right)

    with pytest.raises(ValueError, match="Peano identifier"):
        positive("x + 1", tag="bad_positive_term")
    with pytest.raises(ValueError, match="Peano identifier"):
        strictly_below("x", "S p", tag="bad_bound_term")
    with pytest.raises(ValueError, match="Peano identifier"):
        prime("1", tag="bad_prime_numeral")
    with pytest.raises(ValueError, match="Peano identifier"):
        prime("S", tag="bad_prime_reserved")
    with pytest.raises(ValueError, match="Peano identifier"):
        square_one_mod("p * q", "x", tag="bad_modulus_term")
    with pytest.raises(ValueError, match="binder tag"):
        square_one_mod("p", "x", tag="bad tag")

    capture_attempts = (
        lambda: positive("wsq_positive_gap_capture", tag="capture"),
        lambda: strictly_below("wsq_strict_gap_capture", "p", tag="capture"),
        lambda: prime("wsq_prime_left_capture", tag="capture"),
        lambda: prime("wsq_prime_right_capture", tag="capture"),
        lambda: square_one_mod("wsq_mod_left_capture", "x", tag="capture"),
        lambda: square_one_mod("p", "wsq_mod_right_capture", tag="capture"),
    )
    for attempt in capture_attempts:
        with pytest.raises(ValueError, match="captures an argument"):
            attempt()


def test_wilson_square_one_dependency_boundary_is_exact_core_and_isolated() -> None:
    spec = _candidate_spec()
    core = _specs_by_name()
    assert spec.name not in core
    assert spec.dependencies == EXPECTED_DEPENDENCIES
    assert len(set(spec.dependencies)) == len(spec.dependencies)
    assert all(dependency in core for dependency in spec.dependencies)
    assert spec.name not in spec.dependencies


def test_wilson_square_one_replays_twice_profiles_full_cut_closure() -> None:
    spec, theorem, row, core, passes, source_digest, graph_digest = _discovery_runs()
    print(
        "WMI WILSON SQUARE ONE GRAPH RECEIPT "
        f"graph_sha256={graph_digest} source_sha256={source_digest}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI WILSON SQUARE ONE PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib} "
            f"source_sha256={source_digest}",
            flush=True,
        )

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
        "WMI WILSON SQUARE ONE RECEIPT "
        f"name={name} nodes={nodes} depth={depth} objects={objects} "
        f"edges={edges} reused={reused} cuts={cuts} "
        f"statement_length={length} statement_sha256={statement_digest} "
        f"script_sha256={script_digest} "
        f"dependencies_sha256={dependencies_digest}",
        flush=True,
    )
    assert name == EXPECTED_NAME
    assert nodes <= MAX_USE_CERTIFICATE_NODES
    assert depth <= MAX_USE_PROOF_DEPTH
    assert objects <= MAX_USE_CERTIFICATE_OBJECTS
    assert check((), theorem.certificate, theorem.formula)
    assert not any(type(node) is DNE for node in _walk(theorem.certificate))
    _assert_cut_spine(theorem.certificate, spec, core)


def test_wilson_square_one_rejects_contract_and_every_dependency_cut_mutation() -> None:
    spec, theorem, _, _, _, _, _ = _discovery_runs()
    marker = "x = 1 \\/ x = n"
    assert spec.statement.count(marker) == 1
    false_contract = parse_formula(
        spec.statement.replace(marker, "x = 1 \\/ x = S n")
    )
    assert not check((), theorem.certificate, false_contract)

    for index, dependency in enumerate(spec.dependencies):
        mutated_edge = _mutate_cut_edge_at(theorem.certificate, index)
        assert not check(
            (),
            mutated_edge,
            theorem.formula,
        ), f"kernel accepted replaced live dependency edge: {dependency}"
