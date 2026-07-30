"""Independent admission audit for the isolated finite-permutation gate."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256

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
from peano_lab.library.finite_permutation_theorems import (
    bounded_prefix,
    bounded_successor_prefix,
    injective_prefix,
    injective_successor_prefix,
    make_finite_permutation_theorems,
    permutation_prefix,
    surjective_prefix,
    surjective_successor_prefix,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


# name -> structural occurrences, depth, distinct objects, object edges,
# reused object references, Cut occurrences.  These are receipts from two
# genuinely cold isolated replays, not from the public theorem registry.
EXPECTED = {
    "finite_surjective_zero": (41, 15, 41, 40, 0, 2),
    "finite_injective_prefix_succ": (105, 34, 103, 104, 2, 2),
    "finite_lt_succ_eq_or_lt": (128, 21, 124, 127, 4, 5),
    "finite_bounded_entry_lt": (1_150, 60, 721, 757, 37, 31),
    "beta_prefix_replace_exists": (30_981, 84, 4_698, 4_928, 231, 923),
    "beta_prefix_swap_last_from_entries": (
        31_221,
        85,
        4_790,
        5_023,
        234,
        931,
    ),
    "beta_prefix_swap_last_exists": (31_742, 87, 4_832, 5_066, 235, 948),
    "beta_prefix_swap_last_reflect": (1_765, 62, 1_041, 1_095, 55, 48),
    "finite_swap_last_bounded": (1_380, 61, 907, 945, 39, 37),
    "finite_swap_last_injective": (2_203, 63, 1_435, 1_491, 57, 53),
    "finite_swap_last_surjective_back": (1_929, 63, 1_161, 1_217, 57, 53),
    "finite_contains_decidable": (1_961, 64, 1_140, 1_200, 61, 60),
    "finite_bounded_prefix_without_top": (216, 23, 185, 189, 5, 8),
    "finite_bounded_last_succ": (53, 17, 53, 52, 0, 2),
    "finite_surjective_succ_intro": (243, 22, 195, 200, 6, 10),
    "finite_last_is_top_from_prefix_surjective": (
        402,
        30,
        302,
        309,
        8,
        16,
    ),
    "finite_surjective_succ_from_prefix": (678, 31, 385, 395, 11, 28),
    "finite_no_top_successor_gate": (1_054, 36, 553, 566, 14, 41),
    "finite_bounded_injective_surjective": (
        42_463,
        89,
        6_399,
        6_672,
        274,
        1_266,
    ),
}

EXPECTED_DEPENDENCIES = {
    "finite_surjective_zero": ("add_eq_zero_right", "succ_ne_zero"),
    "finite_injective_prefix_succ": ("le_succ",),
    "finite_lt_succ_eq_or_lt": ("le_of_succ_le_succ", "le_eq_or_lt"),
    "finite_bounded_entry_lt": ("beta_at_unique",),
    "beta_prefix_replace_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "finite_lt_succ_eq_or_lt",
        "beta_prefix_extend",
        "beta_at_exists",
        "beta_at_unique",
    ),
    "beta_prefix_swap_last_from_entries": (
        "beta_prefix_replace_exists",
        "le_succ",
        "le_refl",
        "lt_irrefl_expanded",
    ),
    "beta_prefix_swap_last_exists": (
        "beta_at_exists",
        "beta_prefix_swap_last_from_entries",
    ),
    "beta_prefix_swap_last_reflect": (
        "eq_decidable",
        "beta_at_exists",
        "beta_at_unique",
    ),
    "finite_swap_last_bounded": (
        "finite_bounded_entry_lt",
        "eq_decidable",
        "le_succ",
        "le_refl",
    ),
    "finite_swap_last_injective": (
        "beta_prefix_swap_last_reflect",
        "le_succ",
        "le_refl",
    ),
    "finite_swap_last_surjective_back": (
        "beta_prefix_swap_last_reflect",
        "le_succ",
        "le_refl",
    ),
    "finite_contains_decidable": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "finite_lt_succ_eq_or_lt",
        "beta_at_exists",
        "beta_at_unique",
        "eq_decidable",
        "le_refl",
        "le_succ",
    ),
    "finite_bounded_prefix_without_top": (
        "le_succ",
        "finite_lt_succ_eq_or_lt",
    ),
    "finite_bounded_last_succ": ("le_refl",),
    "finite_surjective_succ_intro": (
        "finite_lt_succ_eq_or_lt",
        "le_refl",
        "le_succ",
    ),
    "finite_last_is_top_from_prefix_surjective": (
        "finite_bounded_last_succ",
        "finite_lt_succ_eq_or_lt",
        "le_refl",
        "le_succ",
        "lt_irrefl_expanded",
    ),
    "finite_surjective_succ_from_prefix": (
        "finite_last_is_top_from_prefix_surjective",
        "finite_surjective_succ_intro",
    ),
    "finite_no_top_successor_gate": (
        "finite_bounded_prefix_without_top",
        "finite_injective_prefix_succ",
        "finite_surjective_succ_from_prefix",
    ),
    "finite_bounded_injective_surjective": (
        "finite_surjective_zero",
        "finite_contains_decidable",
        "finite_bounded_last_succ",
        "beta_prefix_swap_last_from_entries",
        "finite_swap_last_bounded",
        "finite_swap_last_injective",
        "finite_bounded_prefix_without_top",
        "finite_injective_prefix_succ",
        "finite_surjective_succ_from_prefix",
        "finite_swap_last_surjective_back",
        "finite_no_top_successor_gate",
        "beta_at_unique",
        "le_succ",
        "le_refl",
        "lt_irrefl_expanded",
    ),
}

# Exact expanded contract fingerprints.  The readable defining relations live
# beside the theorem maker; these hashes make accidental binder/surface drift
# an explicit review event without duplicating several kilobytes of formulas.
EXPECTED_STATEMENT_SHA256 = {
    "finite_surjective_zero": (
        "0a70bbe7ce32479cee16270fe43f2302208cd0e6b5a6ec5ed9864c0ed61406d5"
    ),
    "finite_injective_prefix_succ": (
        "e9eef8f111bf7cce636683e765b8565c92681a4791c771704388aedb380a4eb8"
    ),
    "finite_lt_succ_eq_or_lt": (
        "4829550fa55790a5ce617b99bbd357d27af724ca5316fbc0a5afef062fb3a1f6"
    ),
    "finite_bounded_entry_lt": (
        "258677a6c25242c72ff768d5d4226d7e5a4e46a7e5d8d801d280c6f525554f2d"
    ),
    "beta_prefix_replace_exists": (
        "442e45d43e8ed59a83a40f9cf71803e333a936da685a6ee565a1bce100f5049d"
    ),
    "beta_prefix_swap_last_from_entries": (
        "efc7ec7a02b3e966da262daa4ea0f4cd2ea5c8c01af1515a6f7ad1d6e8ac2b24"
    ),
    "beta_prefix_swap_last_exists": (
        "2a65762d947799b8ed3e735716844e4a043958ce7310b2faaec0b584be3236f5"
    ),
    "beta_prefix_swap_last_reflect": (
        "07fef8747798fde1b02094fdd63714d5c49cce5ccc7d57d10e3b6d41d4ca998d"
    ),
    "finite_swap_last_bounded": (
        "cc20084340c25cc95fdb2f5fb90769164dca9a98cebd0655ad7c58939062acb9"
    ),
    "finite_swap_last_injective": (
        "2bcb226cbd0852d6e8ba278305e71c546c3dfacb63846432beb9ed2fa3c73a12"
    ),
    "finite_swap_last_surjective_back": (
        "222b6436eb97efeff9d4fe3284bee64f5e58ea781d93c539805fe074b64b96ae"
    ),
    "finite_contains_decidable": (
        "b380408a4f2da9182b3e2c5a64cf9bf39b22efe5fd581a0803d9596318554204"
    ),
    "finite_bounded_prefix_without_top": (
        "2411dd3e45f2840f4860225062f623d149eff40c0d8621a99a775971e12b25cf"
    ),
    "finite_bounded_last_succ": (
        "c0f0a85da0b8af62f3861e835313334f20f43096d993d502d27689d0ef26e994"
    ),
    "finite_surjective_succ_intro": (
        "2c09184a9bd833d67db5d2f3ee61503eee1b56c4f13b916ce46680217a2b1af7"
    ),
    "finite_last_is_top_from_prefix_surjective": (
        "24c86ea298426ce28f9fa7366f65fd1d2ea5f8155df4cc625450f59ec4e99f56"
    ),
    "finite_surjective_succ_from_prefix": (
        "9a186aa36848e2e362baecbf084f1334d9f9fb6c7248c70728272fc0944e948d"
    ),
    "finite_no_top_successor_gate": (
        "9b8d47daab6b099597b4875c374f6a5012be4f1162d33a6266bb5d934a844c88"
    ),
    "finite_bounded_injective_surjective": (
        "9e0cad653da9de17ab7bbac3cb3bf49bc6d4a1304bda508669943b25fd247257"
    ),
}


@dataclass(frozen=True)
class _Checked:
    formula: Formula
    certificate: Proof


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _fresh_replayer():
    specs = make_finite_permutation_theorems(TheoremSpec)
    local = {spec.name: spec for spec in specs}
    core = _specs_by_name()

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
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
            checked_dependency = (
                run(dependency) if dependency in local else replay(dependency)
            )
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )

        assert check((), body, formula)
        return _Checked(formula, body)

    return specs, run


def _rows() -> tuple[tuple[str, int, int, int, int, int, int], ...]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, run = _fresh_replayer()
    rows = []
    for spec in specs:
        theorem = run(spec.name)
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth, objects, edges, reused, cuts))
    return tuple(rows)


def test_permutation_gate_replays_twice_deterministically_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_permutation_contracts_are_exact_closed_expanded_pa_surfaces() -> None:
    specs = make_finite_permutation_theorems(TheoremSpec)
    table = {spec.name: spec for spec in specs}

    assert tuple(table) == tuple(EXPECTED)
    assert set(table).isdisjoint(_specs_by_name())
    assert {name: item.dependencies for name, item in table.items()} == (
        EXPECTED_DEPENDENCIES
    )
    assert {
        name: sha256(item.statement.encode()).hexdigest()
        for name, item in table.items()
    } == EXPECTED_STATEMENT_SHA256
    for item in specs:
        assert _closed_formula(item.statement) == parse_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "BetaAt(",
                "BoundedPrefix(",
                "Contains(",
                "InjectivePrefix(",
                "Permutation(",
                "SurjectivePrefix(",
                "%",
                "^",
                "∣",
            )
        )

    bounded = bounded_prefix("b", "c", "n", tag="audit_bounded")
    injective = injective_prefix("b", "c", "n", tag="audit_injective")
    surjective = surjective_prefix("b", "c", "n", tag="audit_surjective")
    permutation = permutation_prefix("b", "c", "n", tag="audit_permutation")
    expected_permutation = f"(({bounded}) /\\ (({injective}) /\\ ({surjective})))"
    assert parse_formula(permutation) == parse_formula(expected_permutation)


def test_successor_prefix_helpers_are_hygienic_and_term_interpolation_stays_closed() -> None:
    surfaces = (
        bounded_successor_prefix("b", "c", "n", tag="successor_bounded"),
        injective_successor_prefix("b", "c", "n", tag="successor_injective"),
        surjective_successor_prefix("b", "c", "n", tag="successor_surjective"),
    )
    for source in surfaces:
        _, free_names = parse_formula_with_names(source)
        assert set(free_names) == {"b", "c", "n"}
        assert "S n" in source

    with pytest.raises(ValueError, match="Peano identifier"):
        bounded_successor_prefix("b", "c", "n + 1", tag="successor_bad")


def test_no_top_successor_gate_rejects_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    theorem = run("finite_no_top_successor_gate")
    statement = next(
        item.statement
        for item in specs
        if item.name == "finite_no_top_successor_gate"
    )
    marker = "sn = S n"
    assert statement.count(marker) == 1
    mutated_contract = parse_formula(statement.replace(marker, "sn = n"))
    assert not check((), theorem.certificate, mutated_contract)

    assert type(theorem.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated_cut = replace(
        theorem.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated_cut, theorem.formula)
