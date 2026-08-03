"""WMI-only recursive discovery audit for the seven-node Wilson inverse stack."""

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
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)
from peano_lab.library.wilson_inverse_point_candidate import (
    balanced_inverse as point_balanced_inverse,
    bounded_successor_inverse,
    inverse_index as point_inverse_index,
    make_wilson_inverse_point_candidate_theorems,
    prime as point_prime,
    strictly_below as point_strictly_below,
    successor_inverse,
    successor_strictly_below,
)
from peano_lab.library.wilson_inverse_prefix_candidate import (
    beta_at as prefix_beta_at,
    inverse_index as prefix_inverse_index,
    inverse_prefix,
    inverse_prefix_successor,
    make_wilson_inverse_prefix_candidate_theorems,
    prime as prefix_prime,
    strictly_below as prefix_strictly_below,
)


EXPECTED_NAMES = (
    "prime_inverse_index_exists",
    "bounded_mod_inverse_unique",
    "bounded_inverse_index_unique",
    "inverse_index_symmetric",
    "prime_inverse_prefix_extend",
    "prime_inverse_prefix_exists_bounded",
    "prime_inverse_prefix_exists",
)

EXPECTED_DEPENDENCIES = {
    "prime_inverse_index_exists": (
        "succ_ne_zero",
        "succ_le_succ",
        "prime_bounded_nonzero_mod_inverse",
        "nonzero_is_succ",
        "le_of_succ_le_succ",
    ),
    "bounded_mod_inverse_unique": (
        "mod_eq_symm",
        "mod_eq_mul_left",
        "mod_eq_mul_right",
        "mul_assoc",
        "mul_comm",
        "mul_one",
        "one_mul",
        "mod_eq_trans",
        "mod_eq_bounded_unique",
    ),
    "bounded_inverse_index_unique": (
        "succ_le_succ",
        "bounded_mod_inverse_unique",
        "succ_injective",
    ),
    "inverse_index_symmetric": ("mul_comm",),
    "prime_inverse_prefix_extend": (
        "prime_inverse_index_exists",
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "prime_inverse_prefix_exists_bounded": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "lt_to_le",
        "prime_inverse_prefix_extend",
    ),
    "prime_inverse_prefix_exists": (
        "le_refl",
        "prime_inverse_prefix_exists_bounded",
    ),
}

EXPECTED_CORE_BOUNDARY = (
    "succ_ne_zero",
    "succ_le_succ",
    "prime_bounded_nonzero_mod_inverse",
    "nonzero_is_succ",
    "le_of_succ_le_succ",
    "mod_eq_symm",
    "mod_eq_mul_left",
    "mod_eq_mul_right",
    "mul_assoc",
    "mul_comm",
    "mul_one",
    "one_mul",
    "mod_eq_trans",
    "mod_eq_bounded_unique",
    "succ_injective",
    "beta_prefix_extend",
    "finite_lt_succ_eq_or_lt",
    "add_eq_zero_right",
    "lt_to_le",
    "le_refl",
)

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_CANDIDATE_SOURCES = (
    ("point", _SOURCE_ROOT / "wilson_inverse_point_candidate.py"),
    ("prefix", _SOURCE_ROOT / "wilson_inverse_prefix_candidate.py"),
)

_FALSE_CONTRACT_REWRITES = {
    "prime_inverse_index_exists": (
        "= 1 + p * wip_mod_right_exists_result_inverse",
        "= S 1 + p * wip_mod_right_exists_result_inverse",
    ),
    "bounded_mod_inverse_unique": (
        "-> y = z",
        "-> y = S z",
    ),
    "bounded_inverse_index_unique": (
        "-> j = k",
        "-> j = S k",
    ),
    "inverse_index_symmetric": (
        "= 1 + p * wip_mod_right_symmetric_target_inverse",
        "= S 1 + p * wip_mod_right_symmetric_target_inverse",
    ),
    "prime_inverse_prefix_extend": (
        "= 1 + p * wip_mod_right_extend_after_inverse_mod",
        "= S 1 + p * wip_mod_right_extend_after_inverse_mod",
    ),
    "prime_inverse_prefix_exists_bounded": (
        "= 1 + p * wip_mod_right_bounded_result_inverse_mod",
        "= S 1 + p * wip_mod_right_bounded_result_inverse_mod",
    ),
    "prime_inverse_prefix_exists": (
        "= 1 + p * wip_mod_right_full_result_inverse_mod",
        "= S 1 + p * wip_mod_right_full_result_inverse_mod",
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
    return make_wilson_inverse_point_candidate_theorems(
        TheoremSpec
    ) + make_wilson_inverse_prefix_candidate_theorems(TheoremSpec)


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
    """Expose deterministic recursive inverse-stack evidence to WMI."""

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


def _expected_prefix_surface(tag: str, length_term: str) -> str:
    index = f"wip_index_{tag}"
    mate = f"wip_mate_{tag}"
    prefix_gap = f"wip_gap_{tag}_prefix_bound"
    beta_height = f"wip_beta_height_{tag}_decoded"
    beta_quotient = f"wip_beta_quotient_{tag}_decoded"
    index_gap = f"wip_gap_{tag}_inverse_index_bound"
    mate_gap = f"wip_gap_{tag}_inverse_mate_bound"
    mod_left = f"wip_mod_left_{tag}_inverse_mod"
    mod_right = f"wip_mod_right_{tag}_inverse_mod"
    beta_modulus = f"S ((S ({index})) * c)"
    prefix_bound = f"exists {prefix_gap}. {prefix_gap} + S {index} = {length_term}"
    decoded = (
        f"((exists {beta_height}. {beta_height} + S ({mate}) = {beta_modulus}) "
        f"/\\ exists {beta_quotient}. b = {beta_quotient} * {beta_modulus} + "
        f"({mate}))"
    )
    inverse = (
        f"(exists {index_gap}. {index_gap} + S {index} = n) /\\ "
        f"((exists {mate_gap}. {mate_gap} + S {mate} = n) /\\ "
        f"(exists {mod_left} {mod_right}. "
        f"((S {index}) * S {mate}) + p * {mod_left} = "
        f"1 + p * {mod_right}))"
    )
    return (
        f"forall {index}. ({prefix_bound}) -> exists {mate}. "
        f"(({decoded}) /\\ ({inverse}))"
    )


def test_wilson_inverse_contracts_are_exact_deterministic_closed_expanded_pa() -> None:
    point_first = make_wilson_inverse_point_candidate_theorems(TheoremSpec)
    point_second = make_wilson_inverse_point_candidate_theorems(TheoremSpec)
    prefix_first = make_wilson_inverse_prefix_candidate_theorems(TheoremSpec)
    prefix_second = make_wilson_inverse_prefix_candidate_theorems(TheoremSpec)
    assert point_second == point_first
    assert prefix_second == prefix_first
    assert len(point_first) == 4
    assert len(prefix_first) == 3
    first = point_first + prefix_first
    second = point_second + prefix_second
    assert second == first
    assert len(first) == 7
    assert tuple(spec.name for spec in first) == EXPECTED_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES

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
                "InvIdx(",
                "InvPrefix(",
                "Lt(",
                "ModEq(",
                "Prime(",
                "%",
                "^",
                "<",
                "∣",
            )
        )


def test_wilson_inverse_helpers_are_exact_hygienic_and_shared_alpha_equal() -> None:
    assert point_strictly_below("i", "n", tag="exact") == (
        "exists wip_strict_gap_exact. wip_strict_gap_exact + S i = n"
    )
    assert successor_strictly_below("i", "p", tag="exact") == (
        "exists wip_successor_gap_exact. wip_successor_gap_exact + S (S i) = p"
    )
    assert point_prime("p", tag="exact") == (
        "(~(p = 1) /\\ forall wip_prime_left_exact wip_prime_right_exact. "
        "p = wip_prime_left_exact * wip_prime_right_exact -> "
        "wip_prime_left_exact = 1 \\/ wip_prime_right_exact = 1)"
    )
    assert point_balanced_inverse("p", "a", "z", tag="exact") == (
        "exists wip_mod_left_exact wip_mod_right_exact. "
        "a * z + p * wip_mod_left_exact = 1 + p * wip_mod_right_exact"
    )
    assert successor_inverse("p", "i", "j", tag="exact") == (
        "exists wip_mod_left_exact wip_mod_right_exact. "
        "(S i) * S j + p * wip_mod_left_exact = 1 + p * wip_mod_right_exact"
    )
    assert bounded_successor_inverse("p", "i", tag="exact") == (
        "exists wip_inverse_exact. (~(wip_inverse_exact = 0) /\\ "
        "((exists wip_strict_gap_exact_bound. "
        "wip_strict_gap_exact_bound + S wip_inverse_exact = p) /\\ "
        "(exists wip_mod_left_exact_congruence "
        "wip_mod_right_exact_congruence. "
        "(S i) * wip_inverse_exact + p * wip_mod_left_exact_congruence = "
        "1 + p * wip_mod_right_exact_congruence)))"
    )
    assert point_inverse_index("p", "n", "i", "j", tag="exact") == (
        "((exists wip_strict_gap_exact_left_bound. "
        "wip_strict_gap_exact_left_bound + S i = n) /\\ "
        "((exists wip_strict_gap_exact_right_bound. "
        "wip_strict_gap_exact_right_bound + S j = n) /\\ "
        "(exists wip_mod_left_exact_inverse wip_mod_right_exact_inverse. "
        "(S i) * S j + p * wip_mod_left_exact_inverse = "
        "1 + p * wip_mod_right_exact_inverse)))"
    )

    assert prefix_strictly_below("i", "n", tag="exact") == (
        "exists wip_gap_exact. wip_gap_exact + S i = n"
    )
    assert prefix_prime("p", tag="exact") == point_prime("p", tag="exact")
    assert prefix_beta_at("b", "c", "i", "j", tag="exact") == (
        "((exists wip_beta_height_exact. wip_beta_height_exact + S (j) = "
        "S ((S (i)) * c)) /\\ exists wip_beta_quotient_exact. "
        "b = wip_beta_quotient_exact * S ((S (i)) * c) + (j))"
    )
    assert prefix_inverse_index("p", "n", "i", "j", tag="exact") == (
        "(exists wip_gap_exact_index_bound. "
        "wip_gap_exact_index_bound + S i = n) /\\ "
        "((exists wip_gap_exact_mate_bound. "
        "wip_gap_exact_mate_bound + S j = n) /\\ "
        "(exists wip_mod_left_exact_mod wip_mod_right_exact_mod. "
        "((S i) * S j) + p * wip_mod_left_exact_mod = "
        "1 + p * wip_mod_right_exact_mod))"
    )
    assert inverse_prefix("p", "n", "b", "c", "l", tag="exact") == (
        _expected_prefix_surface("exact", "l")
    )
    assert inverse_prefix_successor(
        "p", "n", "b", "c", "l", tag="successor_exact"
    ) == _expected_prefix_surface("successor_exact", "S l")

    surfaces = {
        point_strictly_below("i", "n", tag="free_point_bound"): {"i", "n"},
        successor_strictly_below("i", "p", tag="free_successor_bound"): {
            "i",
            "p",
        },
        point_prime("p", tag="free_point_prime"): {"p"},
        point_balanced_inverse("p", "a", "z", tag="free_inverse"): {
            "p",
            "a",
            "z",
        },
        successor_inverse("p", "i", "j", tag="free_successor_inverse"): {
            "p",
            "i",
            "j",
        },
        bounded_successor_inverse("p", "i", tag="free_bounded_inverse"): {
            "p",
            "i",
        },
        point_inverse_index("p", "n", "i", "j", tag="free_point_index"): {
            "p",
            "n",
            "i",
            "j",
        },
        prefix_strictly_below("i", "n", tag="free_prefix_bound"): {"i", "n"},
        prefix_prime("p", tag="free_prefix_prime"): {"p"},
        prefix_beta_at("b", "c", "i", "j", tag="free_beta"): {
            "b",
            "c",
            "i",
            "j",
        },
        prefix_inverse_index("p", "n", "i", "j", tag="free_prefix_index"): {
            "p",
            "n",
            "i",
            "j",
        },
        inverse_prefix("p", "n", "b", "c", "l", tag="free_prefix"): {
            "p",
            "n",
            "b",
            "c",
            "l",
        },
        inverse_prefix_successor(
            "p", "n", "b", "c", "l", tag="free_successor_prefix"
        ): {"p", "n", "b", "c", "l"},
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    alpha_pairs = (
        (
            point_strictly_below("i", "n", tag="alpha_point_left"),
            point_strictly_below("i", "n", tag="alpha_point_right"),
        ),
        (
            successor_strictly_below("i", "p", tag="alpha_successor_bound_left"),
            successor_strictly_below("i", "p", tag="alpha_successor_bound_right"),
        ),
        (
            point_prime("p", tag="alpha_point_prime_left"),
            point_prime("p", tag="alpha_point_prime_right"),
        ),
        (
            point_balanced_inverse("p", "a", "z", tag="alpha_inverse_left"),
            point_balanced_inverse("p", "a", "z", tag="alpha_inverse_right"),
        ),
        (
            successor_inverse("p", "i", "j", tag="alpha_successor_inverse_left"),
            successor_inverse("p", "i", "j", tag="alpha_successor_inverse_right"),
        ),
        (
            bounded_successor_inverse("p", "i", tag="alpha_bounded_left"),
            bounded_successor_inverse("p", "i", tag="alpha_bounded_right"),
        ),
        (
            point_inverse_index("p", "n", "i", "j", tag="alpha_index_left"),
            point_inverse_index("p", "n", "i", "j", tag="alpha_index_right"),
        ),
        (
            prefix_strictly_below("i", "n", tag="alpha_prefix_bound_left"),
            prefix_strictly_below("i", "n", tag="alpha_prefix_bound_right"),
        ),
        (
            prefix_prime("p", tag="alpha_prefix_prime_left"),
            prefix_prime("p", tag="alpha_prefix_prime_right"),
        ),
        (
            prefix_beta_at("b", "c", "i", "j", tag="alpha_beta_left"),
            prefix_beta_at("b", "c", "i", "j", tag="alpha_beta_right"),
        ),
        (
            prefix_inverse_index("p", "n", "i", "j", tag="alpha_prefix_index_left"),
            prefix_inverse_index("p", "n", "i", "j", tag="alpha_prefix_index_right"),
        ),
        (
            inverse_prefix("p", "n", "b", "c", "l", tag="alpha_prefix_left"),
            inverse_prefix("p", "n", "b", "c", "l", tag="alpha_prefix_right"),
        ),
        (
            inverse_prefix_successor(
                "p", "n", "b", "c", "l", tag="alpha_successor_left"
            ),
            inverse_prefix_successor(
                "p", "n", "b", "c", "l", tag="alpha_successor_right"
            ),
        ),
    )
    for alpha_left, alpha_right in alpha_pairs:
        assert alpha_left != alpha_right
        assert parse_formula(alpha_left) == parse_formula(alpha_right)

    point_shared = point_inverse_index(
        "p", "n", "i", "j", tag="shared_point"
    )
    prefix_shared = prefix_inverse_index(
        "p", "n", "i", "j", tag="shared_prefix"
    )
    assert point_shared != prefix_shared
    assert parse_formula(point_shared) == parse_formula(prefix_shared)

    invalid_calls = (
        lambda: point_strictly_below("S i", "n", tag="bad_point_term"),
        lambda: successor_strictly_below("i + 1", "p", tag="bad_successor"),
        lambda: point_prime("1", tag="bad_prime"),
        lambda: point_balanced_inverse("p", "a * b", "z", tag="bad_product"),
        lambda: successor_inverse("p", "S i", "j", tag="bad_index"),
        lambda: bounded_successor_inverse("1", "i", tag="bad_modulus"),
        lambda: point_inverse_index("p", "S n", "i", "j", tag="bad_length"),
        lambda: prefix_beta_at("b + 1", "c", "i", "j", tag="bad_code"),
        lambda: prefix_inverse_index("p", "n", "S i", "j", tag="bad_prefix_index"),
        lambda: inverse_prefix("p", "n", "b", "c", "S l", tag="bad_prefix"),
    )
    for call in invalid_calls:
        with pytest.raises(ValueError, match="Peano identifier"):
            call()
    with pytest.raises(ValueError, match="binder tag"):
        point_inverse_index("p", "n", "i", "j", tag="bad tag")
    with pytest.raises(ValueError, match="binder tag"):
        inverse_prefix("p", "n", "b", "c", "l", tag="bad tag")

    capture_attempts = (
        lambda: point_strictly_below(
            "wip_strict_gap_capture", "n", tag="capture"
        ),
        lambda: successor_strictly_below(
            "wip_successor_gap_capture", "p", tag="capture"
        ),
        lambda: point_prime("wip_prime_left_capture", tag="capture"),
        lambda: point_balanced_inverse(
            "wip_mod_left_capture", "a", "z", tag="capture"
        ),
        lambda: successor_inverse(
            "wip_mod_left_successor_capture",
            "i",
            "j",
            tag="successor_capture",
        ),
        lambda: bounded_successor_inverse(
            "p", "wip_inverse_capture", tag="capture"
        ),
        lambda: point_inverse_index(
            "wip_mod_left_capture_inverse", "n", "i", "j", tag="capture"
        ),
        lambda: prefix_strictly_below("wip_gap_capture", "n", tag="capture"),
        lambda: prefix_prime(
            "wip_prime_right_prefix_capture", tag="prefix_capture"
        ),
        lambda: prefix_beta_at(
            "wip_beta_quotient_capture", "c", "i", "j", tag="capture"
        ),
        lambda: prefix_inverse_index(
            "wip_mod_left_capture_mod", "n", "i", "j", tag="capture"
        ),
        lambda: inverse_prefix(
            "p", "n", "wip_index_capture", "c", "l", tag="capture"
        ),
        lambda: inverse_prefix_successor(
            "p",
            "n",
            "wip_mate_successor_capture",
            "c",
            "l",
            tag="successor_capture",
        ),
    )
    for attempt in capture_attempts:
        with pytest.raises(ValueError, match="captures an argument"):
            attempt()


def test_wilson_inverse_dependency_graph_is_exact_core_bounded_and_isolated() -> None:
    specs = _candidate_specs()
    core = _specs_by_name()
    assert len(specs) == 7
    assert tuple(spec.name for spec in specs) == EXPECTED_NAMES
    assert len({spec.name for spec in specs}) == 7
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


def test_wilson_inverse_stack_replays_twice_profiles_full_cut_closure() -> None:
    specs, checked, rows, local, passes, source_digests, graph_digest = (
        _discovery_runs()
    )
    print(
        "WMI WILSON INVERSE GRAPH RECEIPT "
        f"nodes={len(EXPECTED_NAMES)} graph_sha256={graph_digest} "
        f"point_source_sha256={dict(source_digests)['point']} "
        f"prefix_source_sha256={dict(source_digests)['prefix']}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI WILSON INVERSE PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        metadata = _row_metadata(row)
        print(
            "WMI WILSON INVERSE RECEIPT "
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


def test_wilson_inverse_stack_rejects_false_contracts_and_every_direct_cut_mutation() -> None:
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
            assert not check(
                (),
                mutated,
                theorem.formula,
            ), (
                "kernel accepted replaced live dependency edge: "
                f"{spec.name}->{dependency}"
            )
