"""Capture-safe untrusted traversals for the kernel's sharing node."""

from __future__ import annotations

from dataclasses import fields

import pytest

import peano_lab.engine.proof_reduction as reduction
from peano_lab.engine.proof_reduction import (
    LocalHave,
    LocalSuffices,
    ProofReductionError,
    erase_trusted_cuts,
    normalise_cuts,
)
from peano_lab.engine.state import (
    Hole,
    MetaVar,
    apply_proof_subst,
    holes_in,
    metas_in_proof,
    proof_metrics,
    replace_hole,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Exists, Forall, Imp, Or
from peano_lab.kernel.proofs import (
    AndIntro,
    Cut,
    EqRefl,
    EqSym,
    ExistsElim,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpElim,
    ImpIntro,
    OrElim,
    OrIntroL,
    Proof,
)
from peano_lab.kernel.terms import Succ, Var, Zero


TRUE = Eq(Zero(), Zero())


def _contains_cut(proof: Proof) -> bool:
    if type(proof) is Cut:
        return True
    return any(
        isinstance((child := getattr(proof, item.name)), Proof)
        and _contains_cut(child)
        for item in fields(proof)
    )


def test_state_term_substitution_reaches_cut_annotations_and_both_children() -> None:
    meta = MetaVar(701)
    original = Cut(
        Eq(meta, Zero()),
        Eq(Zero(), meta),
        EqRefl(meta),
        EqSym(EqRefl(meta)),
    )
    replacement = Succ(Zero())

    transformed = apply_proof_subst(original, {meta.id: replacement})

    assert transformed == Cut(
        Eq(replacement, Zero()),
        Eq(Zero(), replacement),
        EqRefl(replacement),
        EqSym(EqRefl(replacement)),
    )
    assert metas_in_proof(transformed) == ()


def test_term_shifting_respects_formula_binders_inside_cut() -> None:
    original = Cut(
        Forall(Eq(Var(1), Var(0))),
        Exists(Eq(Var(1), Var(0))),
        ForallIntro(EqRefl(Var(1))),
        ExistsIntro(Var(0), EqRefl(Var(0))),
    )

    shifted = reduction._shift_proof_terms(original, 2)

    assert shifted == Cut(
        Forall(Eq(Var(3), Var(0))),
        Exists(Eq(Var(3), Var(0))),
        ForallIntro(EqRefl(Var(3))),
        ExistsIntro(Var(2), EqRefl(Var(2))),
    )


def test_forall_beta_opening_transforms_cut_annotations_and_children() -> None:
    body = Cut(
        Forall(Eq(Var(1), Var(1))),
        Exists(Eq(Var(1), Var(1))),
        ForallIntro(EqRefl(Var(1))),
        ExistsIntro(Var(0), EqRefl(Var(0))),
    )
    raw = ForallElim(ForallIntro(body), Var(2))

    transformed = normalise_cuts(raw)

    assert transformed == Cut(
        Forall(Eq(Var(3), Var(3))),
        Exists(Eq(Var(3), Var(3))),
        ForallIntro(EqRefl(Var(3))),
        ExistsIntro(Var(2), EqRefl(Var(2))),
    )


def test_hypothesis_shifting_increments_cutoff_only_for_cut_body() -> None:
    original = Cut(
        TRUE,
        TRUE,
        Hyp(0),
        AndIntro(
            Hyp(0),
            Cut(
                TRUE,
                TRUE,
                Hyp(1),
                AndIntro(Hyp(0), AndIntro(Hyp(1), Hyp(2))),
            ),
        ),
    )

    shifted = reduction._shift_hypotheses(original, 2)

    assert shifted == Cut(
        TRUE,
        TRUE,
        Hyp(2),
        AndIntro(
            Hyp(0),
            Cut(
                TRUE,
                TRUE,
                Hyp(3),
                AndIntro(Hyp(0), AndIntro(Hyp(1), Hyp(4))),
            ),
        ),
    )


def test_imp_opening_respects_or_branches_and_nested_cut_scopes() -> None:
    redex_body = Cut(
        TRUE,
        TRUE,
        Hyp(0),
        OrElim(
            Hyp(1),
            Cut(TRUE, TRUE, Hyp(2), Hyp(3)),
            Hyp(2),
        ),
    )
    raw = ImpIntro(
        ImpIntro(ImpElim(ImpIntro(redex_body), Hyp(1)))
    )

    transformed = normalise_cuts(raw)

    assert transformed == ImpIntro(
        ImpIntro(
            Cut(
                TRUE,
                TRUE,
                Hyp(1),
                OrElim(
                    Hyp(2),
                    Cut(TRUE, TRUE, Hyp(3), Hyp(4)),
                    Hyp(3),
                ),
            )
        )
    )


def test_exists_opening_lifts_inserted_proof_terms_through_cut_body() -> None:
    reflexive = Eq(Var(0), Var(0))
    redex_body = Cut(
        reflexive,
        reflexive,
        Hyp(0),
        ExistsElim(Hyp(1), Hyp(2)),
    )
    raw = ForallIntro(
        ImpElim(ImpIntro(redex_body), EqRefl(Var(0)))
    )

    transformed = normalise_cuts(raw)

    assert transformed == ForallIntro(
        Cut(
            reflexive,
            reflexive,
            EqRefl(Var(0)),
            ExistsElim(EqRefl(Var(0)), EqRefl(Var(1))),
        )
    )


def test_state_hole_meta_and_metric_walkers_visit_both_cut_children() -> None:
    meta = MetaVar(702)
    original = Cut(
        TRUE,
        TRUE,
        Hole(801),
        Cut(TRUE, TRUE, Hole(802), EqRefl(meta)),
    )

    assert holes_in(original) == (801, 802)
    assert metas_in_proof(original) == (meta.id,)
    assert proof_metrics(original) == (5, 3)

    replaced = replace_hole(original, 801, EqRefl(Zero()))
    assert holes_in(replaced) == (802,)
    assert replaced.lemma == EqRefl(Zero())


def test_erasure_is_separate_cut_free_and_kernel_checked_under_binders() -> None:
    reflexive = Eq(Var(0), Var(0))
    witness_reflexive = Exists(Eq(Var(0), Var(0)))
    conclusion = Or(reflexive, witness_reflexive)
    target = Forall(Imp(reflexive, conclusion))
    certificate = ForallIntro(
        ImpIntro(
            Cut(
                reflexive,
                conclusion,
                Hyp(0),
                Cut(
                    reflexive,
                    conclusion,
                    Hyp(0),
                    OrIntroL(Hyp(0)),
                ),
            )
        )
    )

    erased = erase_trusted_cuts(certificate)
    normalized = normalise_cuts(erased)

    assert check((), certificate, target)
    assert not _contains_cut(erased)
    assert not _contains_cut(normalized)
    assert erased != normalized
    assert check((), erased, target)
    assert check((), normalized, target)

    existential_target = Imp(witness_reflexive, TRUE)
    existential_certificate = ImpIntro(
        ExistsElim(
            Hyp(0),
            Cut(Eq(Var(0), Var(0)), TRUE, Hyp(0), EqRefl(Zero())),
        )
    )
    existential_erased = erase_trusted_cuts(existential_certificate)
    existential_normalized = normalise_cuts(existential_erased)

    assert check((), existential_certificate, existential_target)
    assert not _contains_cut(existential_erased)
    assert not _contains_cut(existential_normalized)
    assert check((), existential_erased, existential_target)
    assert check((), existential_normalized, existential_target)


@pytest.mark.parametrize(
    "scheduled",
    (
        LocalHave(
            TRUE,
            Cut(TRUE, TRUE, EqRefl(Zero()), Hyp(0)),
            Cut(TRUE, TRUE, Hyp(0), Hyp(0)),
        ),
        LocalSuffices(
            TRUE,
            Cut(TRUE, TRUE, Hyp(0), Hyp(0)),
            Cut(TRUE, TRUE, EqRefl(Zero()), Hyp(0)),
        ),
    ),
    ids=("have", "suffices"),
)
def test_erasure_recurses_through_engine_schedulers_without_compiling_them(
    scheduled: Proof,
) -> None:

    erased = erase_trusted_cuts(scheduled)

    assert type(erased) is type(scheduled)
    assert not _contains_cut(erased)
    assert check((), normalise_cuts(erased), TRUE)


def test_erasure_rejects_partial_and_malformed_certificates_stably() -> None:
    with pytest.raises(
        ProofReductionError,
        match="^trusted-cut erasure needs an exact proof certificate$",
    ):
        erase_trusted_cuts(object())  # type: ignore[arg-type]

    with pytest.raises(
        ProofReductionError,
        match="^unsupported proof node during trusted-cut erasure: Hole$",
    ):
        erase_trusted_cuts(Hole(901))

    with pytest.raises(
        ProofReductionError,
        match=(
            "^trusted cut needs PA proposition and conclusion annotations$"
        ),
    ):
        erase_trusted_cuts(
            Cut(object(), TRUE, EqRefl(Zero()), Hyp(0))  # type: ignore[arg-type]
        )
