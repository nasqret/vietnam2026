"""Focused body audit for private K3B cell-list extensionality.

All four dependencies remain ordinary hypotheses.  This file deliberately
performs no recursive closure, admission, WMI replay, or campaign-wide gate.
"""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    parse_formula,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.kernel.terms import Term
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_cell_list_equations_candidate import (
    make_ha_cell_list_equations_candidate_theorems,
)
from peano_lab.library.ha_cell_list_extensional_candidate import (
    make_ha_cell_list_extensional_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_head_candidate import (
    make_ha_cell_list_lookup_head_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_succ_candidate import (
    make_ha_cell_list_lookup_succ_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _primitive


EXPECTED_NAME = "cell_list_extensional"
EXPECTED_DEPENDENCIES = (
    "cell_list_zero_iff_nil",
    "cell_list_succ_iff_cell",
    "list_at_head_iff",
    "list_at_succ_iff",
)
EXPECTED_STATEMENT_RECEIPT = (
    15_451,
    "7033fcdf4c96a866e9d9e0b8381efbbd7b48ab060bcc4adad695ead30ff19831",
)
EXPECTED_AST_RECEIPT = (707, 192)
EXPECTED_BODY_RECEIPT = (4, 152, 386, 50, 369, 385, 17)
STRICT_BOUND = "exists k. k + S i = l"


def _pointwise(
    length: str,
    left_code: str,
    right_code: str,
    index: str,
    left_value: str,
    right_value: str,
    *,
    tag: str,
) -> str:
    left_lookup = cell_list_at(
        left_code, index, left_value, tag=f"{tag}_left"
    )
    right_lookup = cell_list_at(
        right_code, index, right_value, tag=f"{tag}_right"
    )
    return (
        f"forall {index} {left_value} {right_value}. "
        f"(exists k. k + S {index} = {length}) -> "
        f"({left_lookup}) -> ({right_lookup}) -> "
        f"{left_value} = {right_value}"
    )


def _successor_length(code: str, length: str, *, tag: str) -> str:
    placeholder = f"extensional_test_successor_length_{tag}"
    expanded = cell_list_len(code, placeholder, tag=tag)
    assert expanded.count(placeholder) > 0
    return expanded.replace(placeholder, f"S {length}")


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (item,) = make_ha_cell_list_extensional_candidate_theorems(TheoremSpec)
    return item


@lru_cache(maxsize=1)
def _available_specs() -> dict[str, TheoremSpec]:
    specs = (
        make_ha_cell_list_equations_candidate_theorems(TheoremSpec)
        + make_ha_cell_list_lookup_head_candidate_theorems(TheoremSpec)
        + make_ha_cell_list_lookup_succ_candidate_theorems(TheoremSpec)
    )
    available = {item.name: item for item in specs}
    return {name: available[name] for name in EXPECTED_DEPENDENCIES}


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


def _walk_pa_ast(node: Formula | Term):
    yield node
    for item in fields(node):
        child = getattr(node, item.name)
        if isinstance(child, (Formula, Term)):
            yield from _walk_pa_ast(child)


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_unique_proof(proof: Proof):
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


def _beta(code: int, scale: int, index: int, value: int) -> bool:
    modulus = 1 + (index + 1) * scale
    return value < modulus and code % modulus == value


def _cell(head: int, tail: int) -> int:
    shell = head + tail
    return 1 + shell * (shell + 1) + 2 * tail


def _history(values: tuple[int, ...], code: int, scale: int) -> bool:
    return (
        values[0] == 0
        and _beta(code, scale, 0, 0)
        and _beta(code, scale, len(values) - 1, values[-1])
        and all(
            any(
                values[index + 1] == _cell(head, values[index])
                for head in range(values[index + 1] + 1)
            )
            for index in range(len(values) - 1)
        )
    )


def _lookup(
    values: tuple[int, ...],
    code: int,
    scale: int,
    outer_index: int,
    value: int,
) -> bool:
    length = len(values) - 1
    return _history(values, code, scale) and any(
        edge + outer_index + 1 == length
        and _beta(code, scale, edge, values[edge])
        and _beta(code, scale, edge + 1, values[edge + 1])
        and values[edge + 1] == _cell(value, values[edge])
        for edge in range(length)
    )


def test_cell_list_extensional_surface_is_exact_closed_and_private() -> None:
    item = _candidate_spec()
    left_length = cell_list_len(
        "z", "l", tag="extensional_target_left_length"
    )
    right_length = cell_list_len(
        "w", "l", tag="extensional_target_right_length"
    )
    pointwise = _pointwise(
        "l", "z", "w", "i", "a", "d", tag="extensional_target"
    )
    expected = (
        "forall z w l. "
        f"({left_length}) -> ({right_length}) -> "
        f"({pointwise}) -> z = w"
    )

    assert make_ha_cell_list_extensional_candidate_theorems(
        TheoremSpec
    ) == (item,)
    assert item.name == EXPECTED_NAME
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert item.statement == expected
    assert (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
    ) == EXPECTED_STATEMENT_RECEIPT

    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement) == _closed_formula(
        item.statement
    )
    nodes = tuple(_walk_pa_ast(formula))
    assert (
        len(nodes),
        sum(isinstance(node, Formula) for node in nodes),
    ) == EXPECTED_AST_RECEIPT

    body = formula
    for _ in range(3):
        assert isinstance(body, Forall)
        body = body.body
    assert isinstance(body, Imp)
    assert isinstance(body.right, Imp)
    assert isinstance(body.right.right, Imp)
    assert isinstance(body.right.right.right, Eq)

    relational = body.right.right.left
    for _ in range(3):
        assert isinstance(relational, Forall)
        relational = relational.body
    assert isinstance(relational, Imp)
    assert isinstance(relational.left, Exists)
    assert isinstance(relational.right, Imp)
    assert isinstance(relational.right.right, Imp)
    assert isinstance(relational.right.right.right, Eq)

    assert item.statement.count(STRICT_BOUND) == 1
    assert item.statement.count("z = w") == 1
    assert "w = z" not in item.statement
    for tag in ("extensional_target_left", "extensional_target_right"):
        equation = f"hclook_edge_{tag} + S i = hclook_length_{tag}"
        assert item.statement.count(equation) == 1
    assert all(
        token not in item.statement
        for token in (
            "BetaAt(",
            "Cell(",
            "CellHistory(",
            "CellListLen(",
            "ListAt(",
            "<->",
            "%",
        )
    )

    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_list_extensional_candidate" not in registry_source
    assert f'"{item.name}"' not in registry_source


def test_cell_list_extensional_body_is_pinned_inductive_and_sensitive() -> None:
    item = _candidate_spec()
    (receipt,) = replay_candidate_bodies((item,), core=_available_specs())
    assert (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    ) == EXPECTED_BODY_RECEIPT

    certificate, target = _body_certificate()
    assert check((), certificate, target)
    assert not any(type(node) is DNE for node in _walk_unique_proof(certificate))
    assert item.script.count("induction l") == 1
    assert item.script.count("apply cell_list_zero_iff_nil_left") == 2
    assert item.script.count("apply cell_list_succ_iff_cell_left") == 2
    assert item.script.count("apply list_at_head_iff_right") == 2
    assert item.script.count("apply list_at_succ_iff_right") == 2
    assert item.script.count("apply IH") == 1
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in item.script
    )
    payload = "\n".join((item.statement, *item.dependencies, *item.script)).casefold()
    assert all(
        marker not in payload
        for marker in ("classical", "dne", "excluded_middle", "sorry")
    )
    assert set(item.dependencies).isdisjoint(
        {
            "list_at_domain",
            "list_at_external_bound",
            "list_at_exists",
            "list_at_functional",
            "list_at_history_independent",
        }
    )

    right_length = cell_list_len(
        "w", "l", tag="extensional_target_right_length"
    )
    unequal_lengths = item.statement.replace(
        right_length,
        _successor_length(
            "w", "l", tag="extensional_target_right_length"
        ),
    )
    assert unequal_lengths != item.statement
    assert not check((), certificate, _candidate_target(unequal_lengths))

    skipped_final = item.statement.replace(
        STRICT_BOUND, "exists k. k + S (S i) = l"
    )
    assert skipped_final != item.statement
    assert not check((), certificate, _candidate_target(skipped_final))


def test_cell_list_extensional_small_models_and_mutation_boundaries() -> None:
    values = (0, 1, 15)
    assert _history(values, 1288, 6)
    assert _history(values, 3690, 8)
    assert 1288 != 3690
    assert 6 != 8
    for index, value in ((0, 2), (1, 0)):
        assert _lookup(values, 1288, 6, index, value)
        assert _lookup(values, 3690, 8, index, value)
    assert values[-1] == values[-1]

    # Equal lengths but different entries: pointwise equality detects both.
    other = (0, 3, 19)
    assert _history(other, 819, 8)
    assert len(values) == len(other)
    assert _lookup(values, 1288, 6, 0, 2)
    assert _lookup(other, 819, 8, 0, 0)
    assert 2 != 0
    assert _lookup(values, 1288, 6, 1, 0)
    assert _lookup(other, 819, 8, 1, 1)
    assert 0 != 1
    assert values[-1] != other[-1]

    # The unequal-length mutation has a vacuous zero-length pointwise domain.
    nil_values = (0,)
    singleton_two = (0, 7)
    assert _history(nil_values, 0, 0)
    assert _history(singleton_two, 25, 4)
    assert len(nil_values) - 1 == 0
    assert len(singleton_two) - 1 == 1
    assert nil_values[-1] != singleton_two[-1]

    # Strengthening the pointwise bound skips the only entry of two distinct
    # singleton lists, so its hypothesis is vacuous while the codes differ.
    singleton_one = (0, 3)
    assert _history(singleton_one, 3, 2)
    assert _lookup(singleton_two, 25, 4, 0, 2)
    assert _lookup(singleton_one, 3, 2, 0, 1)
    assert not any(gap + 2 == 1 for gap in range(2))
    assert singleton_two[-1] != singleton_one[-1]
