"""Adversarial tests for the trusted, self-contained Cut proof node."""

from __future__ import annotations

import pytest

from peano_lab.kernel.checker import check, check_classical
from peano_lab.kernel.formulas import And, Bot, Eq, Imp
from peano_lab.kernel.proofs import (
    AndIntro,
    Cut,
    DNE,
    EqRefl,
    Hyp,
    ImpElim,
    ImpIntro,
    Proof,
)
from peano_lab.kernel.terms import Succ, Zero


ZERO = Zero()
ONE = Succ(ZERO)
P = Eq(ZERO, ZERO)
Q = Eq(ONE, ONE)


def test_cut_checks_lemma_once_and_exposes_it_as_newest_body_hypothesis() -> None:
    target = And(P, Q)
    proof = Cut(P, target, EqRefl(ZERO), AndIntro(Hyp(0), Hyp(1)))

    assert check((Q,), proof, target)
    assert not check((Q,), Cut(P, target, EqRefl(ZERO), AndIntro(Hyp(1), Hyp(0))), target)


def test_cut_conclusion_annotation_supports_an_introduction_in_body() -> None:
    target = Imp(Q, And(P, Q))
    proof = Cut(P, target, EqRefl(ZERO), ImpIntro(AndIntro(Hyp(1), Hyp(0))))

    assert check((), proof, target)


@pytest.mark.parametrize(
    "proof,target",
    (
        # The lemma proves P, not the annotated proposition Q.
        (Cut(Q, P, EqRefl(ZERO), Hyp(0)), P),
        # The body proves P, not the annotated conclusion Q.
        (Cut(P, Q, EqRefl(ZERO), Hyp(0)), Q),
        (Cut(P, P, Proof(), Hyp(0)), P),
        (Cut(P, P, EqRefl(ZERO), Proof()), P),
        (Cut(object(), P, EqRefl(ZERO), Hyp(0)), P),
        (Cut(P, object(), EqRefl(ZERO), Hyp(0)), P),
    ),
)
def test_cut_rejects_wrong_annotations_and_malformed_children(
    proof: object, target: object
) -> None:
    assert not check((), proof, target)


def test_cut_cannot_smuggle_classical_authority_into_constructive_checking() -> None:
    dne_p = Imp(Imp(Imp(P, Bot()), Bot()), P)
    classical_lemma = Cut(dne_p, dne_p, DNE(P), Hyp(0))
    classical_body = Cut(P, dne_p, EqRefl(ZERO), DNE(P))

    assert not check((), classical_lemma, dne_p)
    assert not check((), classical_body, dne_p)
    assert check_classical((), classical_lemma, dne_p)
    assert check_classical((), classical_body, dne_p)


def test_cut_is_exact_type_checked_and_malformed_nodes_fail_closed() -> None:
    class EvilCut(Cut):
        pass

    class EvilEq(Eq):
        pass

    valid = Cut(P, P, EqRefl(ZERO), Hyp(0))
    subclassed = EvilCut(P, P, EqRefl(ZERO), Hyp(0))
    formula_subclass = Cut(EvilEq(ZERO, ZERO), P, EqRefl(ZERO), Hyp(0))
    malformed = object.__new__(Cut)

    assert check((), valid, P)
    assert not check((), subclassed, P)
    assert not check((), formula_subclass, P)
    assert not check((), malformed, P)


def test_cut_has_the_same_judgment_as_its_direct_conservative_erasure() -> None:
    target = And(P, Q)
    lemma = EqRefl(ZERO)
    body = AndIntro(Hyp(0), Hyp(1))
    cut = Cut(P, target, lemma, body)
    erased = ImpElim(ImpIntro(body), lemma)

    assert check((Q,), cut, target)
    assert check((Q,), erased, target)
