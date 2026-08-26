"""Lightweight intuitionistic-HA audit for the private K3B CellHistory tranche.

The three rows are checked as dependency-curried bodies.  This test deliberately
does not close the large public beta/CRT dependency graph in the empty context:
that expensive release-gate operation belongs in an isolated worker job.
K3B is a post-K4/M3 bridge and these rows are not counted as strict K3.
"""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.finite_fold_surface import beta_at as checked_beta_at
from peano_lab.library.ha_cell_history_candidate import (
    beta_at,
    cell_history,
    cell_list_len,
    make_ha_cell_history_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "cell_history_nil",
    "cell_history_extend",
    "cell_history_succ_elim",
)
EXPECTED_DEPENDENCIES = {
    "cell_history_nil": ("add_eq_zero_right", "succ_ne_zero"),
    "cell_history_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
        "zero_le",
        "succ_le_succ",
        "le_refl",
    ),
    "cell_history_succ_elim": ("beta_at_unique", "le_refl", "le_succ"),
}
EXPECTED_STATEMENT_RECEIPTS = {
    "cell_history_nil": (
        1468,
        "18568ecbb4bcc3f923c504be74f4933a2b4f79e5d21751a1791715449374de37",
    ),
    "cell_history_extend": (
        3153,
        "50e26cefb18371aed02b5c926757bbfc22a007a51b995aafd3675c9a960bf407",
    ),
    "cell_history_succ_elim": (
        3365,
        "2f44b8405bb60e1571452cdae993c024c80cb079be6ded25edd58716888ecdee",
    ),
}
EXPECTED_HELPER_RECEIPTS = {
    "BetaAt": (
        172,
        "17706704196c2088288197f9d1a1bbd9c692e863f29a2e9a01abdb1252c3d243",
    ),
    "CellHistory": (
        1278,
        "3bd6cd64446b6acec60b2106296d12fbafe781e9caa61246835ebfb8315b6e0b",
    ),
    "CellListLen": (
        1885,
        "662411fc848c5f8e5daf438fd72fa195fba44d8301f448d9be750ab016bcc026",
    ),
}
EXPECTED_BODY_RECEIPTS = {
    "cell_history_nil": (2, 24, 135, 18, 135, 134, 0),
    "cell_history_extend": (5, 86, 122, 36, 122, 121, 0),
    "cell_history_succ_elim": (3, 43, 59, 23, 59, 58, 0),
}

# Preserved from the reviewed cold run of the nil seed.  It is intentionally
# not regenerated here: doing so recursively expands the public library.
KNOWN_NIL_CLOSED_RECEIPT = (
    155,
    18,
    155,
    154,
    0,
    2,
    "a3038bd67616f11f8e97727c98f03af09aacde863a70637d9575e2ff9d337ff8",
)

EXPECTED_CLOSURE_COUNT = 106
EXPECTED_CLOSURE_SHA256 = (
    "686d583676ca0ccbe94717c6de33d5f4c11afe9928346126dd12432f16c96d47"
)
EXPECTED_PUBLIC_CLOSURE_COUNT = 103
EXPECTED_PUBLIC_CLOSURE_SHA256 = (
    "6632eb02e03cf96f1b15173d823b58af1883727142f711622944140a280122a5"
)
FORBIDDEN_CONSTRUCTIVE_MARKERS = (
    "classical",
    "dne",
    "excluded_middle",
    "by_contra",
    "sorry",
)
FORBIDDEN_CLIENT_PREFIXES = (
    "beta_product",
    "beta_sum",
    "finite_product",
    "finite_sum",
    "fermat_",
    "euler_",
    "wilson_",
    "quadratic_",
    "prime_factorization",
    "fundamental_theorem_of_arithmetic",
    "generalized_binary_crt",
)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_cell_history_candidate_theorems(TheoremSpec)


def _local_specs() -> dict[str, TheoremSpec]:
    return {item.name: item for item in _candidate_specs()}


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local_specs()


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_unique(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(_proof_children(node))


def _candidate_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


def _body_certificate(item: TheoremSpec):
    target = _candidate_target(item)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _dependency_closure() -> dict[str, TheoremSpec]:
    public = _specs_by_name()
    local = _local_specs()
    pending = list(EXPECTED_NAMES)
    closure: dict[str, TheoremSpec] = {}
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        item = local.get(name) or public[name]
        closure[name] = item
        pending.extend(item.dependencies)
    return closure


def _beta_semantic(code: int, scale: int, index: int, value: int) -> bool:
    modulus = 1 + (index + 1) * scale
    return value < modulus and code % modulus == value


def _cell_code(head: int, tail: int) -> int:
    shell = head + tail
    return 1 + shell * (shell + 1) + 2 * tail


def _history_semantic(
    code: int,
    length: int,
    trace_code: int,
    trace_scale: int,
) -> bool:
    if not _beta_semantic(trace_code, trace_scale, 0, 0):
        return False
    if not _beta_semantic(trace_code, trace_scale, length, code):
        return False
    for index in range(length):
        current_modulus = 1 + (index + 1) * trace_scale
        next_modulus = 1 + (index + 2) * trace_scale
        tail = trace_code % current_modulus
        successor = trace_code % next_modulus
        if not any(
            successor == _cell_code(head, tail)
            for head in range(successor + 1)
        ):
            return False
    return True


def test_cell_history_helpers_are_hygienic_exact_and_macro_free() -> None:
    left = cell_history("z", "l", "b", "c", tag="alpha_left")
    right = cell_history("z", "l", "b", "c", tag="alpha_right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"z", "l", "b", "c"}

    beta_left = beta_at("b", "c", "i", "x", tag="history_beta")
    beta_right = checked_beta_at("b", "c", "i", "x", tag="fold_beta")
    assert parse_formula(beta_left) == parse_formula(beta_right)

    wrapper = cell_list_len("z", "l", tag="wrapper")
    _, wrapper_free_names = parse_formula_with_names(wrapper)
    assert set(wrapper_free_names) == {"z", "l"}

    canonical_helpers = {
        "BetaAt": beta_at("b", "c", "i", "x", tag="rfc_v1"),
        "CellHistory": cell_history("z", "l", "b", "c", tag="rfc_v1"),
        "CellListLen": cell_list_len("z", "l", tag="rfc_v1"),
    }
    assert {
        name: (len(source), sha256(source.encode()).hexdigest())
        for name, source in canonical_helpers.items()
    } == EXPECTED_HELPER_RECEIPTS

    for source in (left, beta_left, wrapper):
        assert all(
            token not in source
            for token in (
                "BetaAt(",
                "Cell(",
                "CellHistory(",
                "CellListLen(",
                "%",
                "<",
            )
        )

    with pytest.raises(ValueError):
        cell_history("hch_index_capture", "l", "b", "c", tag="capture")
    with pytest.raises(ValueError):
        cell_list_len("hch_trace_code_capture", "l", tag="capture")
    with pytest.raises(ValueError):
        beta_at("b", "c", "S i", "x", tag="compound")


def test_cell_history_factory_is_exact_closed_and_registry_isolated() -> None:
    specs = _candidate_specs()
    assert make_ha_cell_history_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: (len(item.statement), sha256(item.statement.encode()).hexdigest())
        for item in specs
    } == EXPECTED_STATEMENT_RECEIPTS

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_history_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in specs)

    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "BetaAt(",
                "Cell(",
                "CellHistory(",
                "CellListLen(",
                "%",
                "<",
            )
        )

    assert specs[0].statement.count("hch_beta_height_nil_history_start") == 2
    assert "hch_beta_height_extend_after_terminal" in specs[1].statement
    assert "hch_beta_height_succ_elim_after_terminal" in specs[2].statement


def test_cell_history_dependency_closure_is_exact_and_constructive() -> None:
    closure = _dependency_closure()
    names = sorted(closure)
    public_names = sorted(set(closure) - set(EXPECTED_NAMES))
    assert len(names) == EXPECTED_CLOSURE_COUNT
    assert sha256("\n".join(names).encode()).hexdigest() == EXPECTED_CLOSURE_SHA256
    assert len(public_names) == EXPECTED_PUBLIC_CLOSURE_COUNT
    assert (
        sha256("\n".join(public_names).encode()).hexdigest()
        == EXPECTED_PUBLIC_CLOSURE_SHA256
    )
    assert not any(
        name.startswith(FORBIDDEN_CLIENT_PREFIXES) for name in names
    )
    assert set(names).isdisjoint(
        {
            "beta_product_exists_unique",
            "beta_sum_exists_unique",
            "beta_prefix_extend_all_prime",
            "beta_prefix_extend_sorted_singleton",
            "beta_prefix_extend_sorted_succ",
        }
    )

    for item in closure.values():
        payload = "\n".join(
            (item.name, item.statement, *item.dependencies, *item.script, item.summary)
        ).casefold()
        assert all(marker not in payload for marker in FORBIDDEN_CONSTRUCTIVE_MARKERS)


def test_cell_history_bodies_are_pinned_dne_free_and_mutation_sensitive() -> None:
    receipts = replay_candidate_bodies(_candidate_specs(), core=dict(_specs_by_name()))
    assert {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == EXPECTED_BODY_RECEIPTS

    assert _candidate_specs()[0].script.count("norm_num") == 4
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "ring", "simp", "use"}
        for item in _candidate_specs()
        for command in item.script
    )

    mutations = {
        "cell_history_nil": (
            "hch_beta_height_nil_history_terminal + S (0) = ",
            "hch_beta_height_nil_history_terminal + S (S 0) = ",
        ),
        "cell_history_extend": (
            "hch_beta_height_extend_after_terminal + S (u) = ",
            "hch_beta_height_extend_after_terminal + S (S u) = ",
        ),
        "cell_history_succ_elim": (
            "u = S ((h + t) * S (h + t) + (t + t))",
            "S u = S ((h + t) * S (h + t) + (t + t))",
        ),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))

        old, new = mutations[item.name]
        assert item.statement.count(old) == 1
        mutated = item.statement.replace(old, new)
        assert not check((), certificate, _candidate_target(item, mutated))


def test_known_nil_closed_receipt_is_preserved_without_cold_replay() -> None:
    assert KNOWN_NIL_CLOSED_RECEIPT == (
        155,
        18,
        155,
        154,
        0,
        2,
        "a3038bd67616f11f8e97727c98f03af09aacde863a70637d9575e2ff9d337ff8",
    )
    nodes, depth, objects, _edges, _reused, _cuts, digest = (
        KNOWN_NIL_CLOSED_RECEIPT
    )
    assert MAX_LIVE_PROOF_NODES == MAX_USE_CERTIFICATE_NODES == 500_000
    assert MAX_LIVE_PROOF_OBJECTS == MAX_USE_CERTIFICATE_OBJECTS == 100_000
    assert MAX_LIVE_PROOF_DEPTH == MAX_USE_PROOF_DEPTH == 256
    assert nodes <= MAX_USE_CERTIFICATE_NODES
    assert objects <= MAX_USE_CERTIFICATE_OBJECTS
    assert depth <= MAX_USE_PROOF_DEPTH
    assert len(digest) == 64


def test_cell_history_nil_extend_and_succ_elim_semantics() -> None:
    assert _history_semantic(0, 0, 0, 0)
    for trace_code, trace_scale in product(range(24), range(7)):
        if _beta_semantic(trace_code, trace_scale, 0, 0):
            assert _history_semantic(0, 0, trace_code, trace_scale)

    # A one-cell history: residues 0 and 1 modulo 2 and 3.
    assert _history_semantic(1, 1, 4, 1)
    assert _cell_code(0, 0) == 1

    # Extend by Cell(0,1)=5.  The new beta witnesses encode 0,1,5 modulo
    # 3,5,7 while preserving the old prefix extensionally.
    assert _cell_code(0, 1) == 5
    assert [96 % modulus for modulus in (3, 5, 7)] == [0, 1, 5]
    assert _history_semantic(5, 2, 96, 2)

    # Successor elimination exposes t=1 and h=0 and reuses (b,c)=(96,2)
    # for the predecessor history.
    assert 5 == _cell_code(0, 1)
    assert _history_semantic(1, 1, 96, 2)

    # Nearby orientation and terminal mutations are semantically false.
    tail = 4 % 2
    successor = 4 % 3
    assert not any(tail == _cell_code(head, successor) for head in range(8))
    assert not _beta_semantic(0, 0, 0, 1)
    assert not _history_semantic(6, 2, 96, 2)
