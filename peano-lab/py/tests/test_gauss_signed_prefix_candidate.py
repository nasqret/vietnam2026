"""WMI-only recursive discovery audit for signed-half Gauss prefixes."""

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
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.finite_fold_surface import beta_at as canonical_beta_at
from peano_lab.library.gauss_half_range import _range_one
from peano_lab.library.gauss_signed_half_candidate import (
    make_gauss_signed_half_candidate_theorems,
)
from peano_lab.library.gauss_signed_prefix_candidate import (
    _beta_at_term,
    _strictly_below_term,
    _weakly_below_term,
    half_range,
    make_gauss_signed_prefix_candidate_theorems,
    not_divides,
    prime,
    signed_half_choice,
    signed_half_choices,
    signed_half_prefix,
    signed_half_successor_prefix,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


PRIOR_NAMES = (
    "odd_upper_remainder_reflection",
    "gauss_pointwise_signed_half_representative",
)
PREFIX_NAMES = (
    "gauss_pointwise_signed_half_choice",
    "gauss_half_range_signed_choices",
    "gauss_signed_half_prefix_extend",
    "gauss_signed_half_prefix_exists",
    "gauss_half_range_signed_prefix_exists",
    "gauss_signed_half_prefix_all_bits",
    "gauss_signed_half_bit_count_exists",
)
EXPECTED_NAMES = PRIOR_NAMES + PREFIX_NAMES

EXPECTED_DEPENDENCIES = {
    "odd_upper_remainder_reflection": (
        "add_assoc",
        "add_comm",
        "mul_succ_left",
        "mul_zero_left",
        "zero_add",
        "add_right_cancel",
    ),
    "gauss_pointwise_signed_half_representative": (
        "add_assoc",
        "add_comm",
        "mul_succ_left",
        "mul_one",
        "le_or_lt",
        "one_le_of_ne_zero",
        "remainder_decomposition_to_mod_eq",
        "odd_upper_remainder_reflection",
        "mod_eq_trans",
    ),
    "gauss_pointwise_signed_half_choice": (
        "gauss_pointwise_signed_half_representative",
    ),
    "gauss_half_range_signed_choices": (
        "prime_nonzero",
        "division_remainder_exists",
        "beta_half_range_entry_bounds",
        "euclid_prime_dvd_product",
        "divisor_le_nonzero",
        "lt_not_le",
        "mul_comm",
        "gauss_pointwise_signed_half_choice",
    ),
    "gauss_signed_half_prefix_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "gauss_signed_half_prefix_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        "gauss_signed_half_prefix_extend",
    ),
    "gauss_half_range_signed_prefix_exists": (
        "gauss_half_range_signed_choices",
        "gauss_signed_half_prefix_exists",
    ),
    "gauss_signed_half_prefix_all_bits": (),
    "gauss_signed_half_bit_count_exists": (
        "gauss_signed_half_prefix_all_bits",
        "bit_count_exists",
    ),
}

EXPECTED_CORE_BOUNDARY = (
    "add_assoc",
    "add_comm",
    "mul_succ_left",
    "mul_zero_left",
    "zero_add",
    "add_right_cancel",
    "mul_one",
    "le_or_lt",
    "one_le_of_ne_zero",
    "remainder_decomposition_to_mod_eq",
    "mod_eq_trans",
    "prime_nonzero",
    "division_remainder_exists",
    "beta_half_range_entry_bounds",
    "euclid_prime_dvd_product",
    "divisor_le_nonzero",
    "lt_not_le",
    "mul_comm",
    "beta_prefix_extend",
    "finite_lt_succ_eq_or_lt",
    "add_eq_zero_right",
    "succ_ne_zero",
    "le_succ",
    "le_refl",
    "bit_count_exists",
)

EXPECTED_BODY_METRICS = {
    "odd_upper_remainder_reflection": (124, 33),
    "gauss_pointwise_signed_half_representative": (116, 38),
    "gauss_pointwise_signed_half_choice": (73, 27),
    "gauss_half_range_signed_choices": (133, 39),
    "gauss_signed_half_prefix_extend": (164, 47),
    "gauss_signed_half_prefix_exists": (70, 31),
    "gauss_half_range_signed_prefix_exists": (33, 22),
    "gauss_signed_half_prefix_all_bits": (35, 25),
    "gauss_signed_half_bit_count_exists": (31, 26),
}

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_CANDIDATE_SOURCES = (
    ("signed_half", _SOURCE_ROOT / "gauss_signed_half_candidate.py"),
    ("signed_prefix", _SOURCE_ROOT / "gauss_signed_prefix_candidate.py"),
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


def _prior_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_signed_half_candidate_theorems(TheoremSpec)


def _prefix_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_signed_prefix_candidate_theorems(TheoremSpec)


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return _prior_specs() + _prefix_specs()


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
    return sha256(
        "\x1c".join(_spec_digest(spec) for spec in specs).encode()
    ).hexdigest()


def _source_digests() -> tuple[tuple[str, str], ...]:
    return tuple(
        (name, sha256(path.read_bytes()).hexdigest())
        for name, path in _CANDIDATE_SOURCES
    )


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
    """Expose deterministic recursive signed-prefix discovery evidence."""

    _, _, rows, _, passes, source_digests, graph_digest = _discovery_runs()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    return {
        "candidate_source_sha256": dict(source_digests),
        "graph_sha256": graph_digest,
        "recursive_graph_names": list(EXPECTED_NAMES),
        "discovery_passes": [
            {
                "pass_index": index,
                "duration_seconds": receipt.duration_seconds,
                "peak_rss_kib": receipt.peak_rss_kib,
                "peak_rss_growth_kib": receipt.peak_rss_growth_kib,
                "candidate_source_sha256": dict(source_digests),
            }
            for index, receipt in enumerate(passes, start=1)
        ],
        "candidates": [_row_metadata(row) for row in rows],
    }


def test_gauss_signed_prefix_contracts_and_bodies_are_exact_native_pa() -> None:
    first = _candidate_specs()
    second = _candidate_specs()
    assert second == first
    assert tuple(spec.name for spec in first) == EXPECTED_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES

    receipts = replay_candidate_bodies(first)
    assert tuple(receipt.name for receipt in receipts) == EXPECTED_NAMES
    assert {
        receipt.name: (receipt.proof_nodes, receipt.proof_depth)
        for receipt in receipts
    } == EXPECTED_BODY_METRICS

    for spec in first:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert _closed_formula(spec.statement) == formula
        assert formula == parse_formula(spec.statement)
        assert len(spec.statement) < 16_384
        assert all("DNE" not in command for command in spec.script)
        assert all(command != "ring" for command in spec.script)
        assert all(
            token not in spec.statement
            for token in (
                "AllBits(",
                "BetaAt(",
                "BitCount(",
                "DivRem(",
                "ModEq(",
                "Prime(",
                "SignedHalf(",
                "%",
                "^",
                "<",
                "<=",
                "∣",
            )
        )


def test_gauss_signed_prefix_helpers_are_hygienic_alpha_native_and_semantic() -> None:
    assert prime("p", tag="exact") == (
        "(~(p = 1) /\\ forall gsp_prime_left_exact "
        "gsp_prime_right_exact. p = gsp_prime_left_exact * "
        "gsp_prime_right_exact -> gsp_prime_left_exact = 1 \\/ "
        "gsp_prime_right_exact = 1)"
    )
    assert not_divides("p", "a", tag="exact") == (
        "~(exists gsp_divisor_factor_exact. "
        "a = p * gsp_divisor_factor_exact)"
    )
    assert _strictly_below_term(
        "i", "l", tag="exact", variables=("i", "l")
    ) == "exists gsp_lt_gap_exact. gsp_lt_gap_exact + S i = l"
    assert _weakly_below_term(
        "m", "h", tag="exact", variables=("m", "h")
    ) == "exists gsp_le_gap_exact. gsp_le_gap_exact + m = h"

    assert parse_formula(
        half_range("b", "c", "h", tag="alpha_prefix")
    ) == parse_formula(_range_one("b", "c", "h", tag="alpha_canonical"))
    assert parse_formula(
        _beta_at_term(
            "b",
            "c",
            "i",
            "x",
            tag="alpha_prefix",
            variables=("b", "c", "i", "x"),
        )
    ) == parse_formula(canonical_beta_at("b", "c", "i", "x", tag="alpha"))

    surfaces = {
        prime("p", tag="free_prime"): {"p"},
        not_divides("p", "a", tag="free_nondivisor"): {"p", "a"},
        half_range("b", "c", "h", tag="free_range"): {"b", "c", "h"},
        signed_half_choice(
            "p", "h", "a", "b", "c", "i", tag="free_choice"
        ): {"p", "h", "a", "b", "c", "i"},
        signed_half_choices(
            "p", "h", "a", "b", "c", "l", tag="free_choices"
        ): {"p", "h", "a", "b", "c", "l"},
        signed_half_prefix(
            "p",
            "h",
            "a",
            "b",
            "c",
            "mb",
            "mc",
            "sb",
            "sc",
            "l",
            tag="free_prefix",
        ): {"p", "h", "a", "b", "c", "mb", "mc", "sb", "sc", "l"},
        signed_half_successor_prefix(
            "p",
            "h",
            "a",
            "b",
            "c",
            "mb",
            "mc",
            "sb",
            "sc",
            "l",
            tag="free_successor",
        ): {"p", "h", "a", "b", "c", "mb", "mc", "sb", "sc", "l"},
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    invalid_calls = (
        lambda: prime("p + 1", tag="bad_prime"),
        lambda: not_divides("p", "a", tag="bad tag"),
        lambda: half_range("b", "c", "h + 1", tag="bad_range"),
        lambda: signed_half_choice(
            "p", "h", "a", "b", "c", "S i", tag="bad_choice"
        ),
        lambda: signed_half_prefix(
            "p", "h", "a", "b", "c", "mb", "mc", "sb", "sc", "S l",
            tag="bad_prefix",
        ),
    )
    for call in invalid_calls:
        with pytest.raises(ValueError):
            call()
    with pytest.raises(ValueError, match="captures an argument"):
        prime("gsp_prime_left_capture", tag="capture")

    table = {spec.name: spec for spec in _prefix_specs()}
    range_script = table["gauss_half_range_signed_choices"].script
    extend_script = table["gauss_signed_half_prefix_extend"].script
    assert range_script.count("intro hpzero") == 1
    assert range_script.count("exact hpzero") == 1
    assert extend_script.count("rewrite hsplit_left") == 6
    assert sum(command.startswith("have hold :") for command in extend_script) == 1
    assert table["gauss_signed_half_prefix_exists"].script.count("induction l") == 1
    assert table["gauss_signed_half_prefix_all_bits"].dependencies == ()

    # Independent bounded audit of the represented magnitude/sign family.
    for p in (3, 5, 7, 11, 13, 17, 19):
        h = (p - 1) // 2
        for a in range(1, p):
            magnitudes = []
            for value in range(1, h + 1):
                remainder = (a * value) % p
                assert remainder != 0
                if remainder <= h:
                    magnitude, sign = remainder, 0
                else:
                    magnitude, sign = p - remainder, 1
                assert 1 <= magnitude <= h
                if sign == 0:
                    assert (a * value - magnitude) % p == 0
                else:
                    assert (a * value - (2 * h) * magnitude) % p == 0
                magnitudes.append(magnitude)
            assert sorted(magnitudes) == list(range(1, h + 1))


def test_gauss_signed_prefix_graph_is_exact_core_bounded_and_isolated() -> None:
    specs = _candidate_specs()
    core = _specs_by_name()
    assert tuple(spec.name for spec in specs) == EXPECTED_NAMES
    assert len({spec.name for spec in specs}) == len(EXPECTED_NAMES)
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
    assert all(path.is_file() for _, path in _CANDIDATE_SOURCES)
    registry_source = (_SOURCE_ROOT / "theorems.py").read_text()
    assert "gauss_signed_half_candidate" not in registry_source
    assert "gauss_signed_prefix_candidate" not in registry_source

    by_name = {spec.name: spec for spec in specs}
    assert by_name["gauss_pointwise_signed_half_choice"].dependencies == (
        "gauss_pointwise_signed_half_representative",
    )
    assert by_name["gauss_half_range_signed_prefix_exists"].dependencies == (
        "gauss_half_range_signed_choices",
        "gauss_signed_half_prefix_exists",
    )
    assert by_name["gauss_signed_half_bit_count_exists"].dependencies == (
        "gauss_signed_half_prefix_all_bits",
        "bit_count_exists",
    )


def test_gauss_signed_prefix_stack_replays_twice_profiles_full_cut_closure() -> None:
    specs, checked, rows, local, passes, source_digests, graph_digest = (
        _discovery_runs()
    )
    print(
        "WMI GAUSS SIGNED PREFIX GRAPH RECEIPT "
        f"nodes={len(EXPECTED_NAMES)} graph_sha256={graph_digest} "
        f"candidate_source_sha256={dict(source_digests)}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI GAUSS SIGNED PREFIX PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        metadata = _row_metadata(row)
        print(
            "WMI GAUSS SIGNED PREFIX RECEIPT "
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


def test_gauss_signed_prefix_rejects_contract_and_every_direct_cut_mutation() -> None:
    specs, checked, _, _, _, _, _ = _discovery_runs()
    for spec in specs:
        theorem = checked[spec.name]
        strengthened = parse_formula(f"({spec.statement}) /\\ 0 = 1")
        assert strengthened != theorem.formula
        assert not check((), theorem.certificate, strengthened)

        for index, dependency in enumerate(spec.dependencies):
            mutated = _mutate_cut_at(theorem.certificate, index)
            assert not check((), mutated, theorem.formula), (
                "kernel accepted replaced live dependency edge: "
                f"{spec.name}->{dependency}"
            )
