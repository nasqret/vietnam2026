"""Lightweight audit for the private prefix-preserving history extension.

Only the expanded statement, dependency closure, dependency-curried body, and
small standard-model witnesses are checked here.  Empty-context closure of the
large beta/CRT dependency graph is reserved for an isolated WMI job.
"""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_cell_history_prefix_preservation_candidate import (
    make_ha_cell_history_prefix_preservation_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "cell_history_extend_preserves_prefix"
EXPECTED_DEPENDENCIES = (
    "beta_prefix_extend",
    "finite_lt_succ_eq_or_lt",
    "zero_le",
    "succ_le_succ",
    "le_refl",
)
EXPECTED_STATEMENT_RECEIPT = (
    3_799,
    "3191deb1ef7c06755622ef9f277b3d5d1e358edac5437e5e337c9f29c6e395b2",
)
EXPECTED_BODY_RECEIPT = (5, 99, 139, 37, 139, 138, 0)
EXPECTED_CLOSURE_RECEIPT = (
    104,
    "110e39250834964ec050e5778f09af31fdeb02a6e7e9198c1afa5c9c1393f0ae",
)
EXPECTED_PUBLIC_CLOSURE_RECEIPT = (
    103,
    "6632eb02e03cf96f1b15173d823b58af1883727142f711622944140a280122a5",
)
FORBIDDEN_MARKERS = (
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
def _candidate_spec() -> TheoremSpec:
    (item,) = make_ha_cell_history_prefix_preservation_candidate_theorems(
        TheoremSpec
    )
    return item


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | {EXPECTED_NAME: _candidate_spec()}


def _candidate_target(statement: str | None = None):
    item = _candidate_spec()
    target = _closed_formula(item.statement if statement is None else statement)
    available = _available_specs()
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


def _body_certificate() -> tuple[Proof, object]:
    item = _candidate_spec()
    target = _candidate_target()
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


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


def _dependency_closure() -> dict[str, TheoremSpec]:
    available = _available_specs()
    pending = [EXPECTED_NAME]
    closure: dict[str, TheoremSpec] = {}
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        item = available[name]
        closure[name] = item
        pending.extend(item.dependencies)
    return closure


def _beta(code: int, scale: int, index: int, value: int) -> bool:
    modulus = 1 + (index + 1) * scale
    return value < modulus and code % modulus == value


def _cell(head: int, tail: int) -> int:
    shell = head + tail
    return 1 + shell * (shell + 1) + 2 * tail


def _history(
    terminal: int,
    length: int,
    code: int,
    scale: int,
) -> bool:
    if not _beta(code, scale, 0, 0):
        return False
    if not _beta(code, scale, length, terminal):
        return False
    for index in range(length):
        modulus = 1 + (index + 1) * scale
        next_modulus = 1 + (index + 2) * scale
        tail = code % modulus
        successor = code % next_modulus
        if not any(
            successor == _cell(head, tail)
            for head in range(successor + 1)
        ):
            return False
    return True


def test_prefix_preservation_surface_is_exact_private_and_constructive() -> None:
    item = _candidate_spec()
    assert make_ha_cell_history_prefix_preservation_candidate_theorems(
        TheoremSpec
    ) == (item,)
    assert item.name == EXPECTED_NAME
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
    ) == EXPECTED_STATEMENT_RECEIPT

    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement) == _closed_formula(
        item.statement
    )
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
    assert "d + k = l" in item.statement
    assert item.statement.count("hch_beta_height_preserve_old_entry") == 2
    assert item.statement.count("hch_beta_height_preserve_new_entry") == 2
    assert item.statement.count("exists b2 c2.") == 1
    assert item.statement.count(
        "u = S ((h + t) * S (h + t) + (t + t))"
    ) == 1
    assert (
        "hch_beta_height_preserve_after_terminal + S (u) = "
        "S ((S (S l)) * c2)"
    ) in item.statement
    assert (
        "b = hch_beta_quotient_preserve_old_entry * "
        "S ((S (k)) * c) + (v)"
    ) in item.statement
    assert (
        "b2 = hch_beta_quotient_preserve_new_entry * "
        "S ((S (k)) * c2) + (v)"
    ) in item.statement
    assert "hchpres_successor_length_argument" not in item.statement
    assert "hchpres_following_index_argument" not in item.statement
    assert item.script.count("specialize beta_prefix_extend (S l)") == 1

    public = _specs_by_name()
    assert item.name not in public
    source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_history_prefix_preservation_candidate" not in source
    assert f'"{item.name}"' not in source

    payload = "\n".join(
        (item.name, item.statement, *item.dependencies, *item.script, item.summary)
    ).casefold()
    assert all(marker not in payload for marker in FORBIDDEN_MARKERS)
    assert "cell_history_extend" not in item.dependencies


def test_prefix_preservation_closure_is_exact_and_quarantined() -> None:
    closure = _dependency_closure()
    names = sorted(closure)
    public_names = sorted(set(names) - {EXPECTED_NAME})
    assert (
        len(names),
        sha256("\n".join(names).encode()).hexdigest(),
    ) == EXPECTED_CLOSURE_RECEIPT
    assert (
        len(public_names),
        sha256("\n".join(public_names).encode()).hexdigest(),
    ) == EXPECTED_PUBLIC_CLOSURE_RECEIPT
    assert not any(
        name.startswith(FORBIDDEN_CLIENT_PREFIXES) for name in names
    )
    assert set(names).isdisjoint(
        {
            "cell_history_extend",
            "cell_history_succ_elim",
            "cell_list_length_functional",
            "beta_product_exists_unique",
            "beta_sum_exists_unique",
        }
    )
    for item in closure.values():
        payload = "\n".join(
            (
                item.name,
                item.statement,
                *item.dependencies,
                *item.script,
                item.summary,
            )
        ).casefold()
        assert all(marker not in payload for marker in FORBIDDEN_MARKERS)


def test_prefix_preservation_body_is_pinned_dne_free_and_sensitive() -> None:
    item = _candidate_spec()
    (receipt,) = replay_candidate_bodies((item,), core=dict(_specs_by_name()))
    assert (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    ) == EXPECTED_BODY_RECEIPT
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "ring", "simp", "use"}
        for command in item.script
    )

    certificate, target = _body_certificate()
    assert check((), certificate, target)
    assert not any(type(node) is DNE for node in _walk_unique(certificate))

    old = "hch_beta_height_preserve_new_entry + S (v) = "
    new = "hch_beta_height_preserve_new_entry + S (S v) = "
    assert item.statement.count(old) == 1
    mutated = item.statement.replace(old, new)
    assert not check((), certificate, _candidate_target(mutated))

    old_bound = "exists d. d + k = l"
    new_bound = "exists d. d + k = S l"
    assert item.statement.count(old_bound) == 1
    mutated_bound = item.statement.replace(old_bound, new_bound)
    assert not check((), certificate, _candidate_target(mutated_bound))


def test_prefix_preservation_small_model_uses_one_shared_recode() -> None:
    # Old history 0,1 modulo 2,3; extending by Cell(5,0,1) yields the shared
    # recode 0,1,5 modulo 3,5,7.
    assert _cell(0, 1) == 5
    assert _history(1, 1, 4, 1)
    assert _history(5, 2, 96, 2)

    old_entries = ((0, 0), (1, 1))
    assert all(_beta(4, 1, index, value) for index, value in old_entries)
    assert all(_beta(96, 2, index, value) for index, value in old_entries)
    assert _beta(96, 2, 2, 5)

    # The old code happens to decode zero at the next, out-of-prefix index.
    # The new history deliberately stores its appended cell there instead;
    # the theorem therefore preserves exactly k <= l, not arbitrary k.
    assert _beta(4, 1, 2, 0)
    assert not _beta(96, 2, 2, 0)

    # The preservation statement is value-sensitive and does not merely
    # assert that some value decodes at each old position.
    assert not _beta(96, 2, 0, 1)
    assert not _beta(96, 2, 1, 0)
