"""Cross-boundary regression tests for trusted Cut synthesis and sharing."""

from __future__ import annotations

from dataclasses import replace
import hashlib

from peano_lab.engine.state import Goal, Hole, MetaVar, metas_in_proof, start
from peano_lab.engine.tacticals import focus
from peano_lab.engine.tactics import checked_final, refl, split, use_checked
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Eq, Forall, Imp
from peano_lab.kernel.proofs import (
    AndElimL,
    AndIntro,
    Cut,
    EqRefl,
    EqSym,
    EqTrans,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpElim,
    ImpIntro,
)
from peano_lab.kernel.terms import Succ, Var, Zero
from peano_lab.library.theorems import replay


ZERO = Zero()
ONE = Succ(ZERO)
TWO = Succ(ONE)
P = Eq(ZERO, ZERO)
Q = Eq(ONE, ONE)


def test_cut_synthesizes_in_every_elimination_position() -> None:
    universal = Forall(Eq(Var(0), Var(0)))
    forall_source = Cut(P, universal, EqRefl(ZERO), ForallIntro(EqRefl(Var(0))))
    assert check((), ForallElim(forall_source, ONE), Q)

    conjunction = And(P, Q)
    and_source = Cut(P, conjunction, EqRefl(ZERO), AndIntro(Hyp(0), EqRefl(ONE)))
    assert check((), AndElimL(and_source), P)

    zero_one = Eq(ZERO, ONE)
    one_zero = Eq(ONE, ZERO)
    symmetric_source = Cut(P, zero_one, EqRefl(ZERO), Hyp(1))
    assert check((zero_one,), EqSym(symmetric_source), one_zero)

    one_two = Eq(ONE, TWO)
    zero_two = Eq(ZERO, TWO)
    transitive_source = Cut(P, zero_one, EqRefl(ZERO), Hyp(2))
    assert check(
        (one_two, zero_one),
        EqTrans(transitive_source, Hyp(0)),
        zero_two,
    )

    function = Imp(Q, P)
    function_source = Cut(
        P,
        function,
        EqRefl(ZERO),
        ImpIntro(Hyp(1)),
    )
    assert check((), ImpElim(function_source, EqRefl(ONE)), P)


def test_dependency_cut_replay_is_deterministic_and_mutation_is_rejected() -> None:
    replay.cache_clear()
    first = replay("add_comm")
    first_digest = hashlib.sha256(repr(first.certificate).encode()).hexdigest()

    replay.cache_clear()
    second = replay("add_comm")
    second_digest = hashlib.sha256(repr(second.certificate).encode()).hexdigest()

    assert type(first.certificate) is Cut
    assert first.certificate == second.certificate
    assert first_digest == second_digest
    assert check((), first.certificate.lemma, first.certificate.proposition)
    assert check((), first.certificate, first.formula)

    corrupted = replace(first.certificate, lemma=EqRefl(ZERO))
    assert not check((), corrupted, first.formula)


def test_use_checked_cut_annotations_follow_metavariable_resolution() -> None:
    # This emulates a current goal produced by unification while preserving the
    # rigid original target owned by the proof session.  The imported theorem
    # is closed; only the Cut conclusion and its live body contain the meta.
    meta = MetaVar(900_001)
    state = start(P)
    state = replace(state, goals=(Goal((), Eq(meta, ZERO)),))
    theorem = replay("zero_add")

    imported = use_checked(
        state,
        "zero_add",
        theorem.formula,
        theorem.certificate,
    )
    assert type(imported.partial) is Cut
    assert metas_in_proof(imported.partial) == (meta.id,)

    completed = refl(imported)
    assert dict(completed.subst) == {meta.id: ZERO}
    assert metas_in_proof(completed.partial) == ()
    assert completed.partial.conclusion == P
    assert check((), checked_final(completed, P), P)


def test_focused_use_checked_replaces_only_the_selected_branch_hole() -> None:
    target = And(P, P)
    branched = split(start(target))
    theorem = replay("zero_add")

    def import_zero_add(state, _args: str = ""):
        return use_checked(
            state,
            "zero_add",
            theorem.formula,
            theorem.certificate,
        )

    imported = focus(2, import_zero_add)(branched, "")

    assert type(imported.partial) is AndIntro
    assert type(imported.partial.left) is Hole
    assert type(imported.partial.right) is Cut
    assert imported.goals[0].context == ()
    assert imported.goals[1].context[0] == ("zero_add", theorem.formula)

    right_closed = focus(2, refl)(imported, "")
    completed = focus(1, refl)(right_closed, "")
    assert check((), checked_final(completed, target), target)
