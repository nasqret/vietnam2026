"""Soundness-facing tests for the trusted Peano Lab kernel."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from peano_lab.kernel.checker import axiom_formula, check
from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, Or
from peano_lab.kernel.proofs import (
    AndElimL,
    AndIntro,
    Axiom,
    BotElim,
    CongAdd,
    CongMul,
    CongS,
    EqRefl,
    EqSubst,
    EqSym,
    EqTrans,
    ExistsElim,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpIntro,
    Ind,
    OrElim,
    OrIntroL,
    OrIntroR,
)
from peano_lab.kernel.subst import shift_formula, shift_term, subst_formula, subst_term
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero


ZERO = Zero()
ONE = Succ(ZERO)


def induction_certificate_for_pa3() -> tuple[Forall, Ind]:
    """Exercise IND even though PA3 itself already states this theorem."""

    motive = Eq(Add(Var(0), ZERO), Var(0))
    base = ForallElim(Axiom("PA3"), ZERO)
    step = ForallIntro(
        ImpIntro(ForallElim(Axiom("PA3"), Succ(Var(0))))
    )
    return Forall(motive), Ind(motive, base, step)


def test_tiny_equality_certificates() -> None:
    assert check((), EqRefl(ZERO), Eq(ZERO, ZERO))
    pa3_at_one = ForallElim(Axiom("PA3"), ONE)
    assert check((), pa3_at_one, Eq(Add(ONE, ZERO), ONE))


def test_documented_certificate_keyword_signatures_remain_available() -> None:
    hypothesis = Hyp(i=0)
    elimination = ForallElim(p=Axiom("PA3"), t=ZERO)
    substitution = EqSubst(
        motive=Eq(Var(0), Var(0)),
        eq_proof=hypothesis,
        body_proof=EqRefl(t=ZERO),
    )
    assert hypothesis.index == 0
    assert elimination.term == ZERO
    assert substitution.equation == hypothesis


def test_induction_schema_acceptance_certificate() -> None:
    goal, certificate = induction_certificate_for_pa3()
    assert check((), certificate, goal)


def test_mutated_induction_certificates_all_fail() -> None:
    goal, certificate = induction_certificate_for_pa3()
    wrong_motive = Eq(Add(Var(0), ZERO), ZERO)
    mutations = [
        Ind(wrong_motive, certificate.base, certificate.step),
        Ind(certificate.motive, EqRefl(ZERO), certificate.step),
        Ind(
            certificate.motive,
            certificate.base,
            ForallIntro(ImpIntro(EqRefl(Var(0)))),
        ),
        Axiom("PA7"),
        Hyp(0),
    ]
    assert all(not check((), mutation, goal) for mutation in mutations)
    assert not check((), certificate, Forall(wrong_motive))


def test_all_six_axiom_constants_have_exact_types() -> None:
    for number in range(1, 7):
        name = f"PA{number}"
        formula = axiom_formula(name)
        assert formula is not None
        assert check((), Axiom(name), formula)
    assert axiom_formula("PA0") is None
    assert not check((), Axiom("PA0"), Eq(ZERO, ZERO))


def test_intuitionistic_connective_rules() -> None:
    p = Eq(ZERO, ZERO)
    q = Eq(ONE, ONE)

    assert check((), ImpIntro(Hyp(0)), Imp(p, p))
    assert check((), ImpIntro(AndElimL(Hyp(0))), Imp(And(p, q), p))
    assert check((), AndIntro(EqRefl(ZERO), EqRefl(ONE)), And(p, q))
    assert check((), OrIntroL(EqRefl(ZERO)), Or(p, q))
    assert check((), OrIntroR(EqRefl(ONE)), Or(p, q))

    cases = OrElim(Hyp(0), OrIntroR(Hyp(0)), OrIntroL(Hyp(0)))
    assert check((Or(p, q),), cases, Or(q, p))
    assert check((Bot(),), BotElim(Hyp(0)), p)


def test_quantifier_rules_and_eigenvariable_scoping() -> None:
    reflexive = Forall(Eq(Var(0), Var(0)))
    assert check((), ForallIntro(EqRefl(Var(0))), reflexive)
    assert check((), ExistsIntro(ZERO, EqRefl(ZERO)), Exists(Eq(Var(0), Var(0))))

    existential = Exists(Eq(Var(0), Var(0)))
    target = Imp(existential, Eq(ZERO, ZERO))
    proof = ImpIntro(ExistsElim(Hyp(0), EqRefl(ZERO)))
    assert check((), proof, target)

    # A universal introduction may not capture a free variable from a premise.
    open_premise = Eq(Var(0), ZERO)
    escaped = Forall(Eq(Var(0), ZERO))
    assert not check((open_premise,), ForallIntro(Hyp(0)), escaped)


def test_equality_rules() -> None:
    equation = Eq(ZERO, ONE)
    assert check((equation,), EqSym(Hyp(0)), Eq(ONE, ZERO))
    assert check((equation,), EqTrans(Hyp(0), EqRefl(ONE)), equation)
    assert check((equation,), CongS(Hyp(0)), Eq(Succ(ZERO), Succ(ONE)))
    assert check(
        (equation,),
        CongAdd(Hyp(0), EqRefl(ZERO)),
        Eq(Add(ZERO, ZERO), Add(ONE, ZERO)),
    )
    assert check(
        (equation,),
        CongMul(Hyp(0), EqRefl(ONE)),
        Eq(Mul(ZERO, ONE), Mul(ONE, ONE)),
    )

    motive = Eq(Var(0), Var(0))
    leibniz = ImpIntro(EqSubst(motive, Hyp(0), EqRefl(ZERO)))
    assert check((), leibniz, Imp(equation, Eq(ONE, ONE)))


def test_substitution_opens_a_slot_and_decrements_larger_indices() -> None:
    term = Add(Var(0), Var(1))
    assert subst_term(term, 0, ONE) == Add(ONE, Var(0))
    assert shift_term(Add(Var(0), Var(1)), 2, cutoff=1) == Add(Var(0), Var(3))


def test_substitution_does_not_capture_under_a_quantifier() -> None:
    # The replacement's free Var(0) must become Var(1) below forall.
    source = Forall(Eq(Var(1), Var(0)))
    assert subst_formula(source, 0, Var(0)) == Forall(Eq(Var(1), Var(0)))

    # Removing the outer slot also closes the gap above it.
    with_other_outer_var = Forall(Eq(Var(2), Var(1)))
    assert subst_formula(with_other_outer_var, 0, ZERO) == Forall(Eq(Var(1), ZERO))


def test_shifting_respects_nested_formula_binders() -> None:
    formula = Forall(Exists(Eq(Var(2), Var(1))))
    assert shift_formula(formula, 1) == Forall(Exists(Eq(Var(3), Var(1))))


@pytest.mark.parametrize(
    ("proof", "target"),
    [
        (EqRefl(ZERO), Eq(ZERO, ONE)),
        (Hyp(0), Eq(ZERO, ZERO)),
        (Axiom("PA3"), Eq(Add(ZERO, ZERO), ZERO)),
        (object(), Eq(ZERO, ZERO)),
    ],
)
def test_wrong_or_malformed_certificates_are_rejected(proof: object, target: Eq) -> None:
    assert not check((), proof, target)
    assert not check("not a context", proof, target)


def test_ast_subclasses_cannot_override_equality_at_the_trusted_boundary() -> None:
    class EvilZero(Zero):
        def __eq__(self, other: object) -> bool:
            return True

        __hash__ = Zero.__hash__

    class EvilEq(Eq):
        def __eq__(self, other: object) -> bool:
            return True

        __hash__ = Eq.__hash__

    class EvilRefl(EqRefl):
        pass

    false_equation = Eq(ZERO, ONE)
    assert not check((), EqRefl(EvilZero()), false_equation)
    assert not check((EvilEq(ZERO, ZERO),), Hyp(0), Bot())
    assert not check((), EvilRefl(ZERO), Eq(ZERO, ZERO))


def test_kernel_import_hygiene() -> None:
    kernel = Path(__file__).parents[1] / "peano_lab" / "kernel"
    forbidden = {"engine", "ui"}
    for path in kernel.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {part for alias in node.names for part in alias.name.split(".")}
            elif isinstance(node, ast.ImportFrom):
                names = set((node.module or "").split("."))
            else:
                continue
            assert names.isdisjoint(forbidden), f"forbidden kernel import in {path.name}"


def test_checker_stays_small_enough_to_read_in_one_sitting() -> None:
    checker = Path(__file__).parents[1] / "peano_lab" / "kernel" / "checker.py"
    assert len(checker.read_text(encoding="utf-8").splitlines()) <= 300
