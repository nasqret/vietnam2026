"""Focused soundness tests for the kernel's lazy term-binder contexts."""

from __future__ import annotations

import peano_lab.kernel.checker as checker
from peano_lab.kernel.formulas import And, Eq, Exists, Forall, Imp, Or
from peano_lab.kernel.proofs import (
    AndIntro,
    Cut,
    EqRefl,
    ExistsElim,
    ForallIntro,
    Hyp,
    ImpIntro,
    OrElim,
    OrIntroL,
    OrIntroR,
)
from peano_lab.kernel.terms import Succ, Var, Zero


ZERO = Zero()


def _record_shifts(monkeypatch):
    calls = []
    original = checker.shift_formula

    def observed(formula, by, cutoff=0):
        calls.append((formula, by, cutoff))
        return original(formula, by, cutoff)

    monkeypatch.setattr(checker, "shift_formula", observed)
    return calls


def test_unused_outer_hypothesis_is_not_shifted_under_two_foralls(monkeypatch) -> None:
    outer = Eq(Var(0), ZERO)
    target = Forall(Forall(Eq(Var(0), Var(0))))
    proof = ForallIntro(ForallIntro(EqRefl(Var(0))))
    calls = _record_shifts(monkeypatch)

    assert checker.check((outer,), proof, target)
    assert calls == []


def test_read_outer_hypothesis_materialises_one_composed_shift(monkeypatch) -> None:
    outer = Eq(Var(0), ZERO)
    proof = ForallIntro(ForallIntro(Hyp(0)))
    target = Forall(Forall(Eq(Var(2), ZERO)))
    calls = _record_shifts(monkeypatch)

    assert checker.check((outer,), proof, target)
    assert calls == [(outer, 2, 0)]

    # Neither one missing shift nor capture by the innermost binder is valid.
    assert not checker.check((outer,), proof, Forall(Forall(Eq(Var(1), ZERO))))
    assert not checker.check((outer,), proof, Forall(Forall(Eq(Var(0), ZERO))))


def test_mixed_age_outer_and_implication_hypotheses_keep_their_levels() -> None:
    outer = Eq(Var(0), ZERO)
    inner = Eq(Var(0), Var(0))
    lifted_outer = Eq(Var(1), ZERO)
    body = Imp(inner, And(lifted_outer, inner))
    proof = ForallIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0))))

    assert checker.check((outer,), proof, Forall(body))
    assert not checker.check(
        (outer,),
        ForallIntro(ImpIntro(AndIntro(Hyp(0), Hyp(1)))),
        Forall(body),
    )
    assert not checker.check(
        (outer,), proof, Forall(Imp(inner, And(outer, inner)))
    )


def test_cut_hypothesis_beneath_binder_starts_at_pending_zero() -> None:
    outer = Eq(Var(0), ZERO)
    local = Eq(Var(0), Var(0))
    target_body = And(local, Eq(Var(1), ZERO))
    proof = ForallIntro(
        Cut(
            local,
            target_body,
            EqRefl(Var(0)),
            AndIntro(Hyp(0), Hyp(1)),
        )
    )

    assert checker.check((outer,), proof, Forall(target_body))
    assert not checker.check(
        (outer,),
        ForallIntro(
            Cut(
                local,
                target_body,
                EqRefl(Var(0)),
                AndIntro(Hyp(1), Hyp(0)),
            )
        ),
        Forall(target_body),
    )


def test_both_or_elimination_branch_hypotheses_start_at_pending_zero() -> None:
    left = Eq(Var(0), Var(0))
    right = Eq(Succ(Var(0)), Succ(Var(0)))
    disjunction = Or(left, right)
    target = Forall(Imp(disjunction, disjunction))
    proof = ForallIntro(
        ImpIntro(
            OrElim(
                Hyp(0),
                OrIntroL(Hyp(0)),
                OrIntroR(Hyp(0)),
            )
        )
    )

    assert checker.check((), proof, target)
    assert not checker.check(
        (),
        ForallIntro(
            ImpIntro(
                OrElim(
                    Hyp(0),
                    OrIntroR(Hyp(0)),
                    OrIntroL(Hyp(0)),
                )
            )
        ),
        target,
    )


def test_exists_elim_shifts_only_the_selected_old_context_entry(monkeypatch) -> None:
    existential = Exists(Eq(Var(0), Var(0)))
    outer = Eq(Var(0), ZERO)
    proof = ExistsElim(Hyp(0), Hyp(2))
    calls = _record_shifts(monkeypatch)

    assert checker.check((existential, outer), proof, outer)
    # One shift forms the lifted target; one materialises the selected outer
    # hypothesis.  The unused existential context entry is never rebuilt.
    assert calls == [(outer, 1, 0), (outer, 1, 0)]
    assert not checker.check(
        (existential, outer), proof, Eq(Var(1), ZERO)
    )


def test_exists_elim_source_body_is_prepended_at_pending_zero(monkeypatch) -> None:
    target = Eq(Var(0), ZERO)
    witness_independent = Exists(Eq(Var(1), ZERO))
    proof = ExistsElim(Hyp(0), Hyp(0))
    calls = _record_shifts(monkeypatch)

    assert checker.check((witness_independent,), proof, target)
    # Only the conclusion is lifted.  The opened existential body already
    # lives beneath the witness binder and must not receive another shift.
    assert calls == [(target, 1, 0)]

    witness_dependent = Exists(Eq(Var(0), ZERO))
    assert not checker.check((witness_dependent,), proof, target)
