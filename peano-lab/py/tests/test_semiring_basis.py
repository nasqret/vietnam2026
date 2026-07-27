"""M11's minimal checked commutative-semiring basis."""

from __future__ import annotations

import pytest

import driver
from peano_lab.kernel.checker import check
from peano_lab.library.theorems import get, replay
from peano_lab.ui import data_library


NEW_BASIS = (
    ("one_mul", "∀ x : Nat, 1 * x = x"),
    ("mul_one", "∀ x : Nat, x * 1 = x"),
    (
        "add_mul",
        "∀ x : Nat, ∀ y : Nat, ∀ z : Nat, "
        "(x + y) * z = x * z + y * z",
    ),
)


def test_semiring_basis_replays_deterministically_from_the_empty_context() -> None:
    replay.cache_clear()
    first = tuple(replay(name) for name, _ in NEW_BASIS)
    replay.cache_clear()
    second = tuple(replay(name) for name, _ in NEW_BASIS)

    assert [theorem.certificate for theorem in first] == [
        theorem.certificate for theorem in second
    ]
    assert [theorem.proof_nodes for theorem in first] == [
        theorem.proof_nodes for theorem in second
    ]
    assert all(
        check((), theorem.certificate, theorem.formula)
        for theorem in second
    )


@pytest.mark.parametrize(("name", "lean_statement"), NEW_BASIS)
def test_semiring_basis_has_exact_reproducible_lean_stubs(
    name: str,
    lean_statement: str,
) -> None:
    spec = get(name)
    assert spec is not None

    exported = data_library.lean_export(spec)

    assert exported.statement == lean_statement
    assert f"theorem «{name}» : {lean_statement} := by" in exported.code
    assert exported == data_library.lean_export(spec)


@pytest.mark.parametrize(
    ("name", "target", "terms"),
    (
        ("one_mul", "1 * x = x", ("x",)),
        ("mul_one", "S x * 1 = S x", ("S x",)),
        (
            "add_mul",
            "(x + S x) * (x + 1) = x * (x + 1) + S x * (x + 1)",
            ("x", "S x", "x + 1"),
        ),
    ),
)
def test_semiring_basis_instantiation_is_capture_safe_below_both_binder_kinds(
    name: str,
    target: str,
    terms: tuple[str, ...],
) -> None:
    session = driver.LabSession()
    session.run(f"pa prove forall x. 0 = 0 -> {target}")
    session.run("intro x")
    session.run("intro premise")
    session.run(f"use {name}")
    for term in terms:
        session.run(f"specialize {name} {term}")

    assert "No open goals" in session.run(f"exact {name}")
    assert "No open goals. QED." in session.run("qed")
