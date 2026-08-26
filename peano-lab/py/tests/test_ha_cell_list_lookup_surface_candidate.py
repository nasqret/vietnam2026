"""Focused structural audit for the private K3B ``ListAt`` surface.

There are deliberately no theorem candidates or certificate replays here.
The tests pin only the fully expanded predicate surface, its hygiene, and
small standard-model witnesses for zero through three exact-D06 cells.
"""

from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
from math import factorial, gcd
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And, Eq, Exists, Formula, parse_formula
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.kernel.terms import Term
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.finite_fold_surface import beta_at as checked_beta_at
from peano_lab.library.ha_cell_history_candidate import beta_at
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at


EXPECTED_RECEIPT = (
    3_331,
    54,
    210,
    "b83d91b6ec8e6b83fe637e1533c72beef54c7e7a4b41f1518bce8785cc9f11ce",
)
OUTER_BINDERS = (
    "hclook_length_surface_v1",
    "hclook_trace_code_surface_v1",
    "hclook_trace_scale_surface_v1",
    "hclook_edge_surface_v1",
    "hclook_tail_surface_v1",
    "hclook_successor_surface_v1",
)
FORBIDDEN_SURFACE_TOKENS = (
    "BetaAt(",
    "Cell(",
    "CellHistory(",
    "CellListLen(",
    "ListAt(",
    "%",
    "<",
    "hclook_following_index_argument_",
)


def _walk_pa_ast(node: Formula | Term):
    yield node
    for field in fields(node):
        child = getattr(node, field.name)
        if isinstance(child, (Formula, Term)):
            yield from _walk_pa_ast(child)


def test_list_at_surface_is_exact_alpha_stable_and_registry_isolated() -> None:
    source = cell_list_at("z", "i", "a", tag="surface_v1")
    formula, free_names = parse_formula_with_names(source)
    nodes = tuple(_walk_pa_ast(formula))

    assert (
        len(source),
        sum(isinstance(node, Formula) for node in nodes),
        len(nodes),
        sha256(source.encode("utf-8")).hexdigest(),
    ) == EXPECTED_RECEIPT
    assert free_names == ("z", "i", "a")
    assert all(token not in source for token in FORBIDDEN_SURFACE_TOKENS)
    assert source.startswith(f"exists {' '.join(OUTER_BINDERS)}. ")

    renamed = cell_list_at("z", "i", "a", tag="renamed_surface")
    assert source != renamed
    assert parse_formula(source) == parse_formula(renamed)

    public_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_list_lookup_surface_candidate" not in public_source
    assert "cell_list_at" not in public_source


def test_list_at_payload_association_and_exact_orientation_are_frozen() -> None:
    source = cell_list_at("z", "i", "a", tag="surface_v1")
    body = parse_formula(source)
    for _expected_name in OUTER_BINDERS:
        assert isinstance(body, Exists)
        body = body.body

    # CellHistory /\ (index equation /\ (current /\ (following /\ cell)))
    assert isinstance(body, And)
    assert isinstance(body.left, And)  # exact CellHistory starts with BetaAt(0,0)
    index_payload = body.right
    assert isinstance(index_payload, And)
    assert isinstance(index_payload.left, Eq)
    current_payload = index_payload.right
    assert isinstance(current_payload, And)
    assert isinstance(current_payload.left, And)  # exact current BetaAt
    following_payload = current_payload.right
    assert isinstance(following_payload, And)
    assert isinstance(following_payload.left, And)  # exact following BetaAt
    assert isinstance(following_payload.right, Eq)  # exact Cell(u,a,t)

    length, trace_code, trace_scale, edge, tail, successor = OUTER_BINDERS
    assert f"{edge} + S i = {length}" in source
    exact_cell = (
        f"{successor} = S ((a + {tail}) * S (a + {tail}) + "
        f"({tail} + {tail}))"
    )
    assert source.count(exact_cell) == 1
    reversed_cell = (
        f"{tail} = S ((a + {successor}) * S (a + {successor}) + "
        f"({successor} + {successor}))"
    )
    assert reversed_cell not in source

    current = beta_at(
        trace_code,
        trace_scale,
        edge,
        tail,
        tag="surface_v1_current",
    )
    current_checked = checked_beta_at(
        trace_code,
        trace_scale,
        edge,
        tail,
        tag="independent_current",
    )
    assert current in source
    assert parse_formula(current) == parse_formula(current_checked)

    candidate_placeholder = "candidate_following_index"
    following = beta_at(
        trace_code,
        trace_scale,
        candidate_placeholder,
        successor,
        tag="surface_v1_following",
    ).replace(candidate_placeholder, f"S {edge}")
    checked_placeholder = "checked_following_index"
    following_checked = checked_beta_at(
        trace_code,
        trace_scale,
        checked_placeholder,
        successor,
        tag="independent_following",
    ).replace(checked_placeholder, f"S {edge}")
    assert following in source
    assert parse_formula(following) == parse_formula(following_checked)


def test_list_at_surface_rejects_compounds_reserved_names_and_capture() -> None:
    with pytest.raises(ValueError, match="outer-head index"):
        cell_list_at("z", "S i", "a", tag="bad_compound")
    with pytest.raises(ValueError, match="binder tag"):
        cell_list_at("z", "i", "a", tag="forall")
    with pytest.raises(ValueError, match="lookup binder captures"):
        cell_list_at("hclook_length_capture", "i", "a", tag="capture")
    with pytest.raises(ValueError, match="helper binder captures"):
        cell_list_at(
            "z", "hch_index_capture_history", "a", tag="capture"
        )
    with pytest.raises(ValueError, match="helper binder captures"):
        cell_list_at(
            "z", "i", "hch_beta_height_capture_current", tag="capture"
        )


def _cell_code(head: int, tail: int) -> int:
    shell = head + tail
    return 1 + shell * (shell + 1) + 2 * tail


def _beta_at(code: int, scale: int, index: int, value: int) -> bool:
    modulus = 1 + (index + 1) * scale
    return value < modulus and code % modulus == value


def _encode_reverse_history(heads_inner_to_outer: tuple[int, ...]):
    values = [0]
    for head in heads_inner_to_outer:
        values.append(_cell_code(head, values[-1]))
    if not heads_inner_to_outer:
        return tuple(values), 0, 0

    # A multiple of (l+1)! makes 1+c,...,1+(l+1)c pairwise coprime;
    # increasing that multiple also puts every desired remainder in range.
    base = factorial(len(values))
    scale = ((max(values) + 1 + base - 1) // base) * base
    code = 0
    period = 1
    for index, value in enumerate(values):
        modulus = 1 + (index + 1) * scale
        assert gcd(period, modulus) == 1
        for multiplier in range(modulus):  # a deliberately bounded CRT search
            candidate = code + period * multiplier
            if candidate % modulus == value:
                code = candidate
                break
        else:  # pragma: no cover - coprimality proves this branch impossible
            raise AssertionError("bounded CRT witness was not found")
        period *= modulus
    return tuple(values), code, scale


def _history_holds(values: tuple[int, ...], code: int, scale: int) -> bool:
    return (
        _beta_at(code, scale, 0, 0)
        and _beta_at(code, scale, len(values) - 1, values[-1])
        and all(
            any(
                values[edge + 1] == _cell_code(head, values[edge])
                for head in range(values[edge + 1] + 1)
            )
            for edge in range(len(values) - 1)
        )
    )


def _list_at_holds(
    values: tuple[int, ...],
    trace_code: int,
    scale: int,
    index: int,
    head: int,
) -> bool:
    length = len(values) - 1
    if not _history_holds(values, trace_code, scale):
        return False
    return any(
        edge + index + 1 == length
        and _beta_at(trace_code, scale, edge, tail)
        and _beta_at(trace_code, scale, edge + 1, successor)
        and successor == _cell_code(head, tail)
        for edge, tail, successor in (
            (edge, values[edge], values[edge + 1])
            for edge in range(length)
        )
    )


@pytest.mark.parametrize(
    ("heads_inner_to_outer", "heads_outer_to_inner"),
    (
        ((), ()),
        ((2,), (2,)),
        ((1, 0), (0, 1)),
        ((0, 1, 2), (2, 1, 0)),
    ),
)
def test_list_at_small_reverse_history_models(
    heads_inner_to_outer: tuple[int, ...],
    heads_outer_to_inner: tuple[int, ...],
) -> None:
    values, trace_code, scale = _encode_reverse_history(heads_inner_to_outer)
    assert _history_holds(values, trace_code, scale)
    assert all(
        _list_at_holds(values, trace_code, scale, index, head)
        for index, head in enumerate(heads_outer_to_inner)
    )
    assert not _list_at_holds(
        values,
        trace_code,
        scale,
        len(heads_outer_to_inner),
        0,
    )
    if heads_outer_to_inner:
        assert not _list_at_holds(
            values,
            trace_code,
            scale,
            0,
            heads_outer_to_inner[0] + 1,
        )
