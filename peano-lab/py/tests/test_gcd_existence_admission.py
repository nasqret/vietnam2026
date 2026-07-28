"""Independent admission audit for native relational gcd existence."""

from __future__ import annotations

from dataclasses import fields, replace
import hashlib

import driver

from peano_lab.engine.state import proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, parse_formula_with_names
from peano_lab.kernel.proofs import Axiom, Cut, DNE, EqRefl, Hyp, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.theorems import _specs_by_name, get, replay


ZERO = Zero()
TRUE = Eq(ZERO, ZERO)

EXPECTED_STATEMENTS = {
    "gcd_exists_up_to": (
        r"forall B b. (exists t. t + b = B) -> forall a. exists d. "
        r"(((exists x. a = d * x) /\ (exists y. b = d * y)) /\ "
        r"forall c. (exists u. a = c * u) -> (exists v. b = c * v) "
        r"-> exists w. d = c * w)"
    ),
    "gcd_exists_relational": (
        r"forall a b. exists d. (((exists x. a = d * x) /\ "
        r"(exists y. b = d * y)) /\ forall c. "
        r"(exists u. a = c * u) -> (exists v. b = c * v) "
        r"-> exists w. d = c * w)"
    ),
}

EXPECTED_DEPENDENCIES = {
    "gcd_exists_up_to": (
        "multiple_refl",
        "le_zero",
        "le_eq_or_lt",
        "le_of_succ_le_succ",
        "division_remainder_exists",
        "is_gcd_euclid_forward",
    ),
    "gcd_exists_relational": ("le_refl", "gcd_exists_up_to"),
}

EXPECTED_METRICS = {
    "gcd_exists_up_to": (1_232, 44),
    "gcd_exists_relational": (1_268, 46),
}


def _proof_contains(proof: Proof, node_type: type[Proof]) -> bool:
    if type(proof) is node_type:
        return True
    return any(
        isinstance((child := getattr(proof, item.name)), Proof)
        and _proof_contains(child, node_type)
        for item in fields(proof)
    )


def _cut_spine(proof: Proof) -> tuple[Cut, ...]:
    result: list[Cut] = []
    current = proof
    while type(current) is Cut:
        result.append(current)
        current = current.body
    return tuple(result)


def _replace_dependency_by_true(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        return replace(proof, proposition=TRUE, lemma=EqRefl(ZERO))
    return replace(
        proof,
        body=_replace_dependency_by_true(proof.body, index - 1),
    )


def _mutate_first(
    proof: Proof,
    predicate,
    replacement,
) -> tuple[Proof, bool]:
    if predicate(proof):
        return replacement(proof), True
    for item in fields(proof):
        child = getattr(proof, item.name)
        if not isinstance(child, Proof):
            continue
        changed_child, changed = _mutate_first(child, predicate, replacement)
        if changed:
            return replace(proof, **{item.name: changed_child}), True
    return proof, False


def _mutate_authored_body(
    proof: Proof,
    predicate,
    replacement,
) -> tuple[Proof, bool]:
    if type(proof) is Cut:
        body, changed = _mutate_authored_body(
            proof.body,
            predicate,
            replacement,
        )
        return replace(proof, body=body), changed
    return _mutate_first(proof, predicate, replacement)


def _cold_replay_rows() -> tuple[tuple[str, Proof, tuple[int, int], str], ...]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    rows = []
    for name in EXPECTED_STATEMENTS:
        theorem = replay(name)
        assert check((), theorem.certificate, theorem.formula)
        rows.append(
            (
                name,
                theorem.certificate,
                proof_metrics(theorem.certificate),
                hashlib.sha256(repr(theorem.certificate).encode()).hexdigest(),
            )
        )
    return tuple(rows)


def test_gcd_existence_declarations_have_exact_native_contracts() -> None:
    for name, statement in EXPECTED_STATEMENTS.items():
        spec = get(name)
        assert spec is not None
        formula, free_names = parse_formula_with_names(statement)

        assert free_names == ()
        assert spec.statement == statement
        assert spec.dependencies == EXPECTED_DEPENDENCIES[name]
        assert replay(name).formula == formula


def test_gcd_existence_cold_replay_is_constructive_deterministic_and_bounded() -> None:
    first = _cold_replay_rows()
    second = _cold_replay_rows()

    assert second == first
    assert {name: metrics for name, _, metrics, _ in first} == EXPECTED_METRICS
    for name, certificate, metrics, digest in first:
        assert metrics == EXPECTED_METRICS[name]
        assert len(digest) == 64
        assert not _proof_contains(certificate, DNE)
        assert check((), certificate, replay(name).formula)


def test_every_declared_dependency_is_checked_and_used_by_the_authored_body() -> None:
    for name, dependency_names in EXPECTED_DEPENDENCIES.items():
        theorem = replay(name)
        spine = _cut_spine(theorem.certificate)

        assert len(spine) == len(dependency_names)
        for index, (cut, dependency_name) in enumerate(
            zip(spine, dependency_names, strict=True)
        ):
            dependency = replay(dependency_name)
            assert cut.proposition == dependency.formula
            assert cut.conclusion == theorem.formula
            assert cut.lemma == dependency.certificate
            assert check((), cut.lemma, cut.proposition)

            # Replacing A and its valid proof by the harmless theorem 0 = 0
            # leaves the binder structure unchanged. Rejection therefore
            # demonstrates that the authored body genuinely uses this slot.
            mutation = _replace_dependency_by_true(theorem.certificate, index)
            assert not check((), mutation, theorem.formula)


def test_arithmetic_axiom_and_authored_hypothesis_mutations_are_rejected() -> None:
    bounded = replay("gcd_exists_up_to")
    bad_axiom, changed = _mutate_authored_body(
        bounded.certificate,
        lambda node: type(node) is Axiom,
        lambda node: Axiom("PA6" if node.name != "PA6" else "PA5"),
    )
    assert changed
    assert not check((), bad_axiom, bounded.formula)

    for name in EXPECTED_STATEMENTS:
        theorem = replay(name)
        bad_hypothesis, changed = _mutate_authored_body(
            theorem.certificate,
            lambda node: type(node) is Hyp,
            lambda node: Hyp(node.index + 1),
        )
        assert changed
        assert not check((), bad_hypothesis, theorem.formula)


def test_gcd_exists_relational_is_available_through_public_live_use() -> None:
    statement = EXPECTED_STATEMENTS["gcd_exists_relational"]
    session = driver.LabSession()

    assert session.run_result(f"pa prove {statement}")["failed"] is False
    imported = session.run_result("use gcd_exists_relational")
    closed = session.run_result("exact gcd_exists_relational")
    qed = session.run_result("qed")

    assert imported["failed"] is False
    assert "gcd_exists_relational" in imported["out"]
    assert closed["failed"] is False and "No open goals" in closed["out"]
    assert qed["failed"] is False and "QED." in qed["out"]
