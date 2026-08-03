"""WMI-only recursive discovery audit for finite-omission candidates."""

from __future__ import annotations

import gc
import resource
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from itertools import product
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
from peano_lab.library.finite_fold_surface import beta_at as canonical_beta_at
from peano_lab.library.finite_omission_candidate import (
    _beta_at_term,
    _bounded_into_term,
    _covers_into_term,
    _inverse_choice_prefix_term,
    _lt_term,
    _omits_into_term,
    bounded_into,
    covers_into,
    inverse_choice_prefix,
    inverse_choice_prefix_successor,
    make_finite_omission_candidate_theorems,
    omits_into,
)
from peano_lab.library.finite_permutation_theorems import (
    contains_prefix,
    injective_prefix,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


SEARCH_NAME = "finite_covers_into_or_omits"
EXTEND_NAME = "finite_inverse_choice_prefix_extend"
CHOICE_NAME = "finite_inverse_choice_prefix_exists"
BOUNDED_NAME = "finite_inverse_choice_bounded_into"
INJECTIVE_NAME = "finite_inverse_choice_injective"
IMPOSSIBLE_NAME = "finite_short_cover_impossible"
OMIT_NAME = "finite_short_prefix_omits"
REQUESTED_NAME = "finite_bounded_into_injective_omits"

EXPECTED_NAMES = (
    SEARCH_NAME,
    EXTEND_NAME,
    CHOICE_NAME,
    BOUNDED_NAME,
    INJECTIVE_NAME,
    IMPOSSIBLE_NAME,
    OMIT_NAME,
    REQUESTED_NAME,
)

EXPECTED_DEPENDENCIES = {
    SEARCH_NAME: (
        "add_eq_zero_right",
        "succ_ne_zero",
        "finite_contains_decidable",
        "finite_lt_succ_eq_or_lt",
        "le_succ",
        "le_refl",
    ),
    EXTEND_NAME: ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
    CHOICE_NAME: (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        EXTEND_NAME,
    ),
    BOUNDED_NAME: (),
    INJECTIVE_NAME: ("beta_at_unique",),
    IMPOSSIBLE_NAME: (
        CHOICE_NAME,
        BOUNDED_NAME,
        INJECTIVE_NAME,
        "finite_bounded_injective_surjective",
        "le_trans",
        "le_succ",
        "le_refl",
        "beta_at_unique",
        "lt_irrefl_expanded",
    ),
    OMIT_NAME: (SEARCH_NAME, IMPOSSIBLE_NAME),
    REQUESTED_NAME: (OMIT_NAME,),
}

EXPECTED_CORE_BOUNDARY = (
    "add_eq_zero_right",
    "succ_ne_zero",
    "finite_contains_decidable",
    "finite_lt_succ_eq_or_lt",
    "le_succ",
    "le_refl",
    "beta_prefix_extend",
    "beta_at_unique",
    "finite_bounded_injective_surjective",
    "le_trans",
    "lt_irrefl_expanded",
)

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_CANDIDATE_SOURCE = _SOURCE_ROOT / "finite_omission_candidate.py"

_FALSE_CONTRACT_REWRITES = {
    SEARCH_NAME: (" \\/ ", " /\\ "),
    EXTEND_NAME: (
        "exists r s. (",
        "exists r s. 0 = 1 /\\ (",
    ),
    CHOICE_NAME: (
        "exists z d. (",
        "exists z d. 0 = 1 /\\ (",
    ),
    BOUNDED_NAME: (
        "fom_gap_bounded_result_value_bound + "
        "S (fom_value_bounded_result) = l",
        "fom_gap_bounded_result_value_bound + "
        "S (fom_value_bounded_result) = 0",
    ),
    INJECTIVE_NAME: (
        "fp_i_injective_result = fp_j_injective_result",
        "fp_i_injective_result = S fp_j_injective_result",
    ),
    IMPOSSIBLE_NAME: (
        "~(forall fom_value_impossible_cover.",
        "(forall fom_value_impossible_cover.",
    ),
    OMIT_NAME: (
        "fom_gap_short_omit_value_bound + S (fom_value_short_omit) = n",
        "fom_gap_short_omit_value_bound + S (fom_value_short_omit) = 0",
    ),
    REQUESTED_NAME: (
        "fom_gap_requested_omit_value_bound + "
        "S (fom_value_requested_omit) = n",
        "fom_gap_requested_omit_value_bound + "
        "S (fom_value_requested_omit) = 0",
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
    return make_finite_omission_candidate_theorems(TheoremSpec)


def _expected_statements() -> dict[str, str]:
    search_cover = covers_into("b", "c", "l", "n", tag="search_cover")
    search_omit = omits_into("b", "c", "l", "n", tag="search_omit")

    extend_contains = contains_prefix(
        "b", "c", "l", "k", tag="extend_contains"
    )
    extend_before = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "k", tag="extend_before"
    )
    extend_after = inverse_choice_prefix_successor(
        "b", "c", "l", "r", "s", "k", tag="extend_after"
    )

    exists_cover = covers_into("b", "c", "l", "n", tag="exists_cover")
    exists_result = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="exists_result"
    )

    bounded_choice = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="bounded_choice"
    )
    bounded_result = bounded_into("z", "d", "n", "l", tag="bounded_result")

    injective_choice = inverse_choice_prefix(
        "b", "c", "l", "z", "d", "n", tag="injective_choice"
    )
    injective_result = injective_prefix(
        "z", "d", "n", tag="injective_result"
    )

    impossible_cover = covers_into(
        "b", "c", "l", "n", tag="impossible_cover"
    )
    short_omit = omits_into("b", "c", "l", "n", tag="short_omit")

    requested_bounded = bounded_into(
        "b", "c", "l", "n", tag="requested_bounded"
    )
    requested_injective = injective_prefix(
        "b", "c", "l", tag="requested_injective"
    )
    requested_omit = omits_into(
        "b", "c", "l", "n", tag="requested_omit"
    )

    return {
        SEARCH_NAME: f"forall b c l n. ({search_cover}) \\/ ({search_omit})",
        EXTEND_NAME: (
            f"forall b c l z d k. ({extend_contains}) -> ({extend_before}) -> "
            f"exists r s. ({extend_after})"
        ),
        CHOICE_NAME: (
            f"forall b c l n. ({exists_cover}) -> exists z d. ({exists_result})"
        ),
        BOUNDED_NAME: (
            f"forall b c l z d n. ({bounded_choice}) -> ({bounded_result})"
        ),
        INJECTIVE_NAME: (
            f"forall b c l z d n. ({injective_choice}) -> ({injective_result})"
        ),
        IMPOSSIBLE_NAME: (
            "forall b c l n. (exists h. h + S l = n) -> "
            f"~({impossible_cover})"
        ),
        OMIT_NAME: (
            "forall b c l n. (exists h. h + S l = n) -> "
            f"({short_omit})"
        ),
        REQUESTED_NAME: (
            f"forall b c l n. ({requested_bounded}) -> "
            f"({requested_injective}) -> (exists h. h + S l = n) -> "
            f"({requested_omit})"
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
    """Expose deterministic recursive finite-omission evidence to WMI."""

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


def test_finite_omission_contracts_are_exact_deterministic_closed_expanded_pa() -> None:
    first = make_finite_omission_candidate_theorems(TheoremSpec)
    second = make_finite_omission_candidate_theorems(TheoremSpec)
    assert second == first
    assert len(first) == 8
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
                "BoundedInto(",
                "CoversInto(",
                "InverseChoice(",
                "OmitsInto(",
                "<",
                "<=",
                "%",
                "^",
                "∣",
            )
        )

    by_name = {spec.name: spec for spec in first}
    assert by_name[SEARCH_NAME].statement.count(" \\/ ") == 1
    assert by_name[BOUNDED_NAME].dependencies == ()
    assert by_name[IMPOSSIBLE_NAME].statement.startswith(
        "forall b c l n. (exists h. h + S l = n) -> ~("
    )
    assert by_name[REQUESTED_NAME].statement.count(
        "exists h. h + S l = n"
    ) == 1


def test_finite_omission_helpers_are_hygienic_alpha_native_and_witnesses_audited() -> None:
    assert _lt_term(
        "i", "l", tag="exact", avoid=("i", "l")
    ) == "exists fom_gap_exact. fom_gap_exact + S (i) = l"
    local_at = _beta_at_term(
        "b",
        "c",
        "i",
        "x",
        tag="local_at",
        avoid=("b", "c", "i", "x"),
    )
    public_at = canonical_beta_at("b", "c", "i", "x", tag="public_at")
    assert local_at != public_at
    assert parse_formula(local_at) == parse_formula(public_at)

    alpha_pairs = (
        (
            bounded_into("b", "c", "l", "n", tag="alpha_left"),
            bounded_into("b", "c", "l", "n", tag="alpha_right"),
        ),
        (
            covers_into("b", "c", "l", "n", tag="alpha_left"),
            covers_into("b", "c", "l", "n", tag="alpha_right"),
        ),
        (
            omits_into("b", "c", "l", "n", tag="alpha_left"),
            omits_into("b", "c", "l", "n", tag="alpha_right"),
        ),
        (
            inverse_choice_prefix(
                "b", "c", "l", "z", "d", "n", tag="alpha_left"
            ),
            inverse_choice_prefix(
                "b", "c", "l", "z", "d", "n", tag="alpha_right"
            ),
        ),
        (
            inverse_choice_prefix_successor(
                "b", "c", "l", "z", "d", "n", tag="alpha_left"
            ),
            _inverse_choice_prefix_term(
                "b",
                "c",
                "l",
                "z",
                "d",
                "S n",
                tag="alpha_right",
                avoid=("b", "c", "l", "z", "d", "n"),
            ),
        ),
    )
    for left, right in alpha_pairs:
        assert left != right
        assert parse_formula(left) == parse_formula(right)

    private_public_pairs = (
        (
            _bounded_into_term(
                "b",
                "c",
                "l",
                "n",
                tag="private_bounded",
                avoid=("b", "c", "l", "n"),
            ),
            bounded_into("b", "c", "l", "n", tag="public_bounded"),
        ),
        (
            _covers_into_term(
                "b",
                "c",
                "l",
                "n",
                tag="private_covers",
                avoid=("b", "c", "l", "n"),
            ),
            covers_into("b", "c", "l", "n", tag="public_covers"),
        ),
        (
            _omits_into_term(
                "b",
                "c",
                "l",
                "n",
                tag="private_omits",
                avoid=("b", "c", "l", "n"),
            ),
            omits_into("b", "c", "l", "n", tag="public_omits"),
        ),
    )
    for private, public in private_public_pairs:
        assert private != public
        assert parse_formula(private) == parse_formula(public)

    surfaces = {
        bounded_into("b", "c", "l", "n", tag="free_bounded"): {
            "b",
            "c",
            "l",
            "n",
        },
        covers_into("b", "c", "l", "n", tag="free_covers"): {
            "b",
            "c",
            "l",
            "n",
        },
        omits_into("b", "c", "l", "n", tag="free_omits"): {
            "b",
            "c",
            "l",
            "n",
        },
        inverse_choice_prefix(
            "b", "c", "l", "z", "d", "n", tag="free_choice"
        ): {"b", "c", "l", "z", "d", "n"},
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    invalid_calls = (
        lambda: bounded_into("b + 1", "c", "l", "n", tag="bad_code"),
        lambda: covers_into("b", "S c", "l", "n", tag="bad_scale"),
        lambda: omits_into("b", "c", "S l", "n", tag="bad_length"),
        lambda: inverse_choice_prefix(
            "b", "c", "l", "z", "d", "n", tag="bad tag"
        ),
        lambda: inverse_choice_prefix_successor(
            "b", "c", "l", "z", "d", "S n", tag="bad_predecessor"
        ),
    )
    for call in invalid_calls:
        with pytest.raises(ValueError):
            call()

    with pytest.raises(ValueError, match="captures an argument"):
        bounded_into("fom_index_capture", "c", "l", "n", tag="capture")
    with pytest.raises(ValueError, match="captures an argument"):
        _lt_term(
            "i",
            "l",
            tag="capture",
            avoid=("i", "l", "fom_gap_capture"),
        )

    by_name = {spec.name: spec for spec in _candidate_specs()}
    search_script = by_name[SEARCH_NAME].script
    extend_script = by_name[EXTEND_NAME].script
    bounded_script = by_name[BOUNDED_NAME].script
    injective_script = by_name[INJECTIVE_NAME].script
    impossible_script = by_name[IMPOSSIBLE_NAME].script
    requested_script = by_name[REQUESTED_NAME].script
    assert search_script.count("specialize finite_contains_decidable b") == 1
    assert search_script.count("exists n") == 1
    assert extend_script.count("cases beta_prefix_extend") == 1
    assert extend_script.count(
        "have hsplit : y = k \\/ exists h. h + S y = k"
    ) == 1
    assert bounded_script.count("exact hstored_witness_right_left") == 1
    assert sum(
        command.startswith("specialize beta_at_unique")
        for command in injective_script
    ) == 15
    assert impossible_script.count(
        "specialize finite_bounded_injective_surjective (S l)"
    ) == 1
    assert impossible_script.count("specialize lt_irrefl_expanded l") == 1
    assert "exact hbounded" not in requested_script
    assert "exact hinjective" not in requested_script

    # Independent finite-model audit of the omission witness and of the
    # inverse-choice construction used when a prefix really covers its bound.
    for bound in range(1, 6):
        for length in range(bound):
            for values in product(range(bound), repeat=length):
                missing = next(
                    value for value in range(bound) if value not in values
                )
                assert 0 <= missing < bound
                assert all(stored != missing for stored in values)

        covered = tuple(range(bound)) + tuple(reversed(range(bound)))
        choices = tuple(covered.index(value) for value in range(bound))
        assert all(0 <= index < len(covered) for index in choices)
        assert all(covered[choices[value]] == value for value in range(bound))
        assert len(set(choices)) == bound


def test_finite_omission_graph_is_exact_core_bounded_and_source_isolated() -> None:
    specs = _candidate_specs()
    core = _specs_by_name()
    assert len(specs) == 8
    assert tuple(spec.name for spec in specs) == EXPECTED_NAMES
    assert len({spec.name for spec in specs}) == 8
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
    assert "finite_omission_candidate" not in (
        _SOURCE_ROOT / "theorems.py"
    ).read_text()

    assert {
        dependency
        for spec in specs
        for dependency in spec.dependencies
        if dependency in local_names
    } == {
        EXTEND_NAME,
        SEARCH_NAME,
        CHOICE_NAME,
        BOUNDED_NAME,
        INJECTIVE_NAME,
        IMPOSSIBLE_NAME,
        OMIT_NAME,
    }


def test_finite_omission_stack_replays_twice_profiles_full_cut_closure() -> None:
    specs, checked, rows, local, passes, source_digest, graph_digest = (
        _discovery_runs()
    )
    print(
        "WMI FINITE OMISSION GRAPH RECEIPT "
        f"nodes={len(EXPECTED_NAMES)} graph_sha256={graph_digest} "
        f"candidate_source_sha256={source_digest}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI FINITE OMISSION PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        metadata = _row_metadata(row)
        print(
            "WMI FINITE OMISSION RECEIPT "
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


def test_finite_omission_rejects_false_contracts_and_every_direct_cut_mutation() -> None:
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
