"""Focused audit for private K3B history-witness independence.

The candidate body is checked with its two dependencies left as hypotheses.
No recursive closure, admission, WMI replay, or campaign-wide gate is run.
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
from peano_lab.library.ha_cell_history_candidate import beta_at, cell_history
from peano_lab.library.ha_cell_list_lookup_functional_candidate import (
    make_ha_cell_list_lookup_functional_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_history_independent_candidate import (
    make_ha_cell_list_lookup_history_independent_candidate_theorems,
)
from peano_lab.library.ha_pair_cell_seed_candidate import cell
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "list_at_history_independent"
EXPECTED_DEPENDENCIES = ("list_at_functional", "add_comm")
EXPECTED_STATEMENT_RECEIPT = (
    7_581,
    "d0a1ac158e6e0552a8e762b69b602da0157183c832ec0cf4c270586dffcc914d",
)
EXPECTED_AST_RECEIPT = (423, 111)
EXPECTED_BODY_RECEIPT = (2, 92, 171, 38, 171, 170, 0)


def _history_at(
    length: str,
    trace_code: str,
    trace_scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Independent expansion of the RFC ``HistoryAt`` surface."""

    edge = f"hclookhist_edge_{tag}"
    tail = f"hclookhist_tail_{tag}"
    successor = f"hclookhist_successor_{tag}"
    current = beta_at(
        trace_code,
        trace_scale,
        edge,
        tail,
        tag=f"{tag}_current",
    )
    placeholder = f"history_test_following_index_{tag}"
    following = beta_at(
        trace_code,
        trace_scale,
        placeholder,
        successor,
        tag=f"{tag}_following",
    )
    assert following.count(placeholder) > 0
    following = following.replace(placeholder, f"S {edge}")
    return (
        f"exists {edge} {tail} {successor}. "
        f"({edge} + S {index} = {length} /\\ "
        f"(({current}) /\\ (({following}) /\\ "
        f"({cell(successor, value, tail)}))))"
    )


def _successor_history_at(
    length: str,
    trace_code: str,
    trace_scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    placeholder = f"history_test_successor_index_{tag}"
    expanded = _history_at(
        length,
        trace_code,
        trace_scale,
        placeholder,
        value,
        tag=tag,
    )
    assert expanded.count(placeholder) > 0
    return expanded.replace(placeholder, f"S {index}")


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (item,) = (
        make_ha_cell_list_lookup_history_independent_candidate_theorems(
            TheoremSpec
        )
    )
    return item


@lru_cache(maxsize=1)
def _available_specs() -> dict[str, TheoremSpec]:
    (functional,) = make_ha_cell_list_lookup_functional_candidate_theorems(
        TheoremSpec
    )
    return {
        "list_at_functional": functional,
        "add_comm": _specs_by_name()["add_comm"],
    }


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


def _history_at_holds(
    values: tuple[int, ...],
    code: int,
    scale: int,
    outer_index: int,
    value: int,
) -> bool:
    length = len(values) - 1
    return any(
        edge + outer_index + 1 == length
        and _beta(code, scale, edge, values[edge])
        and _beta(code, scale, edge + 1, values[edge + 1])
        and values[edge + 1] == _cell(value, values[edge])
        for edge in range(length)
    )


def test_history_independence_surface_is_exact_closed_and_private() -> None:
    item = _candidate_spec()
    first_history = cell_history(
        "z", "l", "b", "c", tag="history_independent_first_history"
    )
    second_history = cell_history(
        "z", "l", "d", "e", tag="history_independent_second_history"
    )
    first_at = _history_at(
        "l", "b", "c", "i", "a", tag="history_independent_first_at"
    )
    second_at = _history_at(
        "l", "d", "e", "i", "a", tag="history_independent_second_at"
    )
    expected = (
        "forall z l b c d e i a. "
        f"({first_history}) -> ({second_history}) -> "
        f"({first_at}) -> ({second_at})"
    )

    assert make_ha_cell_list_lookup_history_independent_candidate_theorems(
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
    for _ in range(8):
        assert isinstance(body, Forall)
        body = body.body
    for _ in range(3):
        assert isinstance(body, Imp)
        body = body.right
    assert isinstance(body, Exists)

    for tag in (
        "history_independent_first_at",
        "history_independent_second_at",
    ):
        equation = f"hclookhist_edge_{tag} + S i = l"
        assert item.statement.count(equation) == 1
    assert all(
        equality not in item.statement
        for equality in ("b = d", "d = b", "c = e", "e = c")
    )
    assert all(
        token not in item.statement
        for token in (
            "BetaAt(",
            "Cell(",
            "CellHistory(",
            "HistoryAt(",
            "ListAt(",
            "<->",
            "%",
            "history_test_following_index_",
        )
    )

    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert (
        "ha_cell_list_lookup_history_independent_candidate"
        not in registry_source
    )
    assert f'"{item.name}"' not in registry_source


def test_history_independence_body_is_pinned_constructive_and_sensitive() -> None:
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
    assert item.script.count("apply list_at_functional") == 1
    assert not any(command.startswith("induction ") for command in item.script)
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
            "beta_at_unique",
            "list_at_domain",
            "list_at_external_bound",
            "list_at_exists",
            "cell_functional",
        }
    )

    second_at = _history_at(
        "l", "d", "e", "i", "a", tag="history_independent_second_at"
    )
    assert item.statement.endswith(f"({second_at})")
    raw_code_equality = item.statement[: -len(f"({second_at})")] + "b = d"
    assert not check((), certificate, _candidate_target(raw_code_equality))

    shifted = item.statement.replace(
        second_at,
        _successor_history_at(
            "l",
            "d",
            "e",
            "i",
            "a",
            tag="history_independent_second_at",
        ),
    )
    assert shifted != item.statement
    assert not check((), certificate, _candidate_target(shifted))


def test_history_independence_distinct_beta_encodings() -> None:
    values = (0, 1, 15)
    first_code, first_scale = 1288, 6
    second_code, second_scale = 3690, 8

    assert tuple(first_code % modulus for modulus in (7, 13, 19)) == values
    assert tuple(second_code % modulus for modulus in (9, 17, 25)) == values
    assert _history(values, first_code, first_scale)
    assert _history(values, second_code, second_scale)
    assert first_code != second_code
    assert first_scale != second_scale

    for index, value in ((0, 2), (1, 0)):
        assert _history_at_holds(
            values, first_code, first_scale, index, value
        )
        assert _history_at_holds(
            values, second_code, second_scale, index, value
        )

    # Shifting either valid selection changes the semantic request.
    assert not _history_at_holds(values, second_code, second_scale, 1, 2)
    assert not _history_at_holds(values, second_code, second_scale, 2, 0)
