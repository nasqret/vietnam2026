"""Capture-avoiding beta reduction for untrusted proof certificates.

The kernel deliberately has no theorem environment and no reduction rule for
proof terms.  Library replay and arithmetic automation may nevertheless expose
ordinary implication and universal beta redexes while inserting already
checked certificates.  This module contracts those redexes outside the
trusted kernel, preserving both proposition-hypothesis and term-variable De
Bruijn scopes.

Reduction never grants authority: every caller must still submit the result to
the independent kernel checker against the intended formula.
"""

from __future__ import annotations

from dataclasses import fields, replace

from ..kernel.formulas import Formula
from ..kernel.proofs import (
    AndElimL,
    AndElimR,
    AndIntro,
    Axiom,
    BotElim,
    CongAdd,
    CongMul,
    CongS,
    DNE,
    EqRefl,
    EqSubst,
    EqSym,
    EqTrans,
    ExistsElim,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpElim,
    ImpIntro,
    Ind,
    OrElim,
    OrIntroL,
    OrIntroR,
    Proof,
)
from ..kernel.subst import shift_formula, shift_term, subst_formula, subst_term
from ..kernel.terms import Term


class ProofReductionError(ValueError):
    """An input cannot be reduced as an exact Peano Lab proof certificate."""


def _open_term_slot(proof: Proof, replacement: object, depth: int = 0) -> Proof:
    """Open one surrounding de Bruijn term slot throughout a certificate.

    Formula motives stored by :class:`EqSubst` and :class:`Ind` have their own
    distinguished variable at index zero, hence their extra cutoff.
    """

    if not isinstance(replacement, Term):
        raise ProofReductionError("proof-level term substitution needs a PA term")

    lifted = shift_term(replacement, depth)

    def term(value: object) -> Term:
        if not isinstance(value, Term):
            raise ProofReductionError("malformed term stored in a proof certificate")
        return subst_term(value, depth, lifted)

    def formula(value: object, *, motive: bool = False) -> Formula:
        if not isinstance(value, Formula):
            raise ProofReductionError("malformed formula stored in a proof certificate")
        slot = depth + (1 if motive else 0)
        inserted = shift_term(replacement, slot)
        return subst_formula(value, slot, inserted)

    if type(proof) is Hyp:
        return proof
    if type(proof) is ImpIntro:
        return ImpIntro(_open_term_slot(proof.body, replacement, depth))
    if type(proof) is ImpElim:
        return ImpElim(
            _open_term_slot(proof.function, replacement, depth),
            _open_term_slot(proof.argument, replacement, depth),
        )
    if type(proof) is AndIntro:
        return AndIntro(
            _open_term_slot(proof.left, replacement, depth),
            _open_term_slot(proof.right, replacement, depth),
        )
    if type(proof) is AndElimL:
        return AndElimL(_open_term_slot(proof.pair, replacement, depth))
    if type(proof) is AndElimR:
        return AndElimR(_open_term_slot(proof.pair, replacement, depth))
    if type(proof) is OrIntroL:
        return OrIntroL(_open_term_slot(proof.proof, replacement, depth))
    if type(proof) is OrIntroR:
        return OrIntroR(_open_term_slot(proof.proof, replacement, depth))
    if type(proof) is OrElim:
        return OrElim(
            _open_term_slot(proof.disjunction, replacement, depth),
            _open_term_slot(proof.left_case, replacement, depth),
            _open_term_slot(proof.right_case, replacement, depth),
        )
    if type(proof) is BotElim:
        return BotElim(_open_term_slot(proof.absurdity, replacement, depth))
    if type(proof) is ForallIntro:
        return ForallIntro(_open_term_slot(proof.body, replacement, depth + 1))
    if type(proof) is ForallElim:
        return ForallElim(
            _open_term_slot(proof.universal, replacement, depth),
            term(proof.term),
        )
    if type(proof) is ExistsIntro:
        return ExistsIntro(
            term(proof.term),
            _open_term_slot(proof.proof, replacement, depth),
        )
    if type(proof) is ExistsElim:
        return ExistsElim(
            _open_term_slot(proof.existential, replacement, depth),
            _open_term_slot(proof.body, replacement, depth + 1),
        )
    if type(proof) is EqRefl:
        return EqRefl(term(proof.term))
    if type(proof) is EqSym:
        return EqSym(_open_term_slot(proof.proof, replacement, depth))
    if type(proof) is EqTrans:
        return EqTrans(
            _open_term_slot(proof.first, replacement, depth),
            _open_term_slot(proof.second, replacement, depth),
        )
    if type(proof) is CongS:
        return CongS(_open_term_slot(proof.proof, replacement, depth))
    if type(proof) is CongAdd:
        return CongAdd(
            _open_term_slot(proof.left, replacement, depth),
            _open_term_slot(proof.right, replacement, depth),
        )
    if type(proof) is CongMul:
        return CongMul(
            _open_term_slot(proof.left, replacement, depth),
            _open_term_slot(proof.right, replacement, depth),
        )
    if type(proof) is EqSubst:
        return EqSubst(
            formula(proof.motive, motive=True),
            _open_term_slot(proof.equation, replacement, depth),
            _open_term_slot(proof.body, replacement, depth),
        )
    if type(proof) is DNE:
        return DNE(formula(proof.proposition))
    if type(proof) is Ind:
        return Ind(
            formula(proof.motive, motive=True),
            _open_term_slot(proof.base, replacement, depth),
            _open_term_slot(proof.step, replacement, depth),
        )
    if type(proof) is Axiom:
        return proof
    raise ProofReductionError(
        f"unsupported proof node during term substitution: {type(proof).__name__}"
    )


def _shift_hypotheses(proof: Proof, by: int, cutoff: int = 0) -> Proof:
    """Lift the free proposition-hypothesis indices of ``proof``."""

    if type(proof) is Hyp:
        return Hyp(proof.index + by) if proof.index >= cutoff else proof
    changes: dict[str, Proof] = {}
    for item in fields(proof):
        child = getattr(proof, item.name)
        if not isinstance(child, Proof):
            continue
        child_cutoff = cutoff
        if type(proof) is ImpIntro and item.name == "body":
            child_cutoff += 1
        elif type(proof) is OrElim and item.name in {"left_case", "right_case"}:
            child_cutoff += 1
        elif type(proof) is ExistsElim and item.name == "body":
            child_cutoff += 1
        changes[item.name] = _shift_hypotheses(child, by, child_cutoff)
    return replace(proof, **changes) if changes else proof


def _shift_proof_terms(proof: Proof, by: int, cutoff: int = 0) -> Proof:
    """Lift free term indices throughout a proof, including annotations."""

    changes: dict[str, object] = {}
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            child_cutoff = cutoff
            if type(proof) is ForallIntro and item.name == "body":
                child_cutoff += 1
            elif type(proof) is ExistsElim and item.name == "body":
                child_cutoff += 1
            changes[item.name] = _shift_proof_terms(child, by, child_cutoff)
        elif isinstance(child, Term):
            changes[item.name] = shift_term(child, by, cutoff)
        elif isinstance(child, Formula):
            formula_cutoff = cutoff
            if type(proof) in (EqSubst, Ind) and item.name == "motive":
                formula_cutoff += 1
            changes[item.name] = shift_formula(child, by, formula_cutoff)
    return replace(proof, **changes) if changes else proof


def _open_hypothesis(
    proof: Proof,
    replacement: Proof,
    cutoff: int = 0,
    term_depth: int = 0,
) -> Proof:
    """Open one proposition slot without capturing proposition or term variables."""

    if type(proof) is Hyp:
        if proof.index < cutoff:
            return proof
        if proof.index == cutoff:
            lifted = _shift_hypotheses(replacement, cutoff)
            return _shift_proof_terms(lifted, term_depth)
        return Hyp(proof.index - 1)
    changes: dict[str, Proof] = {}
    for item in fields(proof):
        child = getattr(proof, item.name)
        if not isinstance(child, Proof):
            continue
        child_cutoff = cutoff
        child_term_depth = term_depth
        if type(proof) is ImpIntro and item.name == "body":
            child_cutoff += 1
        elif type(proof) is OrElim and item.name in {"left_case", "right_case"}:
            child_cutoff += 1
        elif type(proof) is ExistsElim and item.name == "body":
            child_cutoff += 1
            child_term_depth += 1
        elif type(proof) is ForallIntro and item.name == "body":
            child_term_depth += 1
        changes[item.name] = _open_hypothesis(
            child,
            replacement,
            child_cutoff,
            child_term_depth,
        )
    return replace(proof, **changes) if changes else proof


def _normalise_forall_cuts(proof: Proof) -> Proof:
    """Contract forall and implication redexes exposed by theorem substitution."""

    if type(proof) is Hyp:
        return proof
    if type(proof) is ImpIntro:
        return ImpIntro(_normalise_forall_cuts(proof.body))
    if type(proof) is ImpElim:
        function = _normalise_forall_cuts(proof.function)
        argument = _normalise_forall_cuts(proof.argument)
        if type(function) is ImpIntro:
            return _normalise_forall_cuts(_open_hypothesis(function.body, argument))
        return ImpElim(function, argument)
    if type(proof) is AndIntro:
        return AndIntro(
            _normalise_forall_cuts(proof.left),
            _normalise_forall_cuts(proof.right),
        )
    if type(proof) is AndElimL:
        return AndElimL(_normalise_forall_cuts(proof.pair))
    if type(proof) is AndElimR:
        return AndElimR(_normalise_forall_cuts(proof.pair))
    if type(proof) is OrIntroL:
        return OrIntroL(_normalise_forall_cuts(proof.proof))
    if type(proof) is OrIntroR:
        return OrIntroR(_normalise_forall_cuts(proof.proof))
    if type(proof) is OrElim:
        return OrElim(
            _normalise_forall_cuts(proof.disjunction),
            _normalise_forall_cuts(proof.left_case),
            _normalise_forall_cuts(proof.right_case),
        )
    if type(proof) is BotElim:
        return BotElim(_normalise_forall_cuts(proof.absurdity))
    if type(proof) is ForallIntro:
        return ForallIntro(_normalise_forall_cuts(proof.body))
    if type(proof) is ForallElim:
        universal = _normalise_forall_cuts(proof.universal)
        if type(universal) is ForallIntro:
            return _normalise_forall_cuts(
                _open_term_slot(universal.body, proof.term)
            )
        return ForallElim(universal, proof.term)
    if type(proof) is ExistsIntro:
        return ExistsIntro(proof.term, _normalise_forall_cuts(proof.proof))
    if type(proof) is ExistsElim:
        return ExistsElim(
            _normalise_forall_cuts(proof.existential),
            _normalise_forall_cuts(proof.body),
        )
    if type(proof) is EqSym:
        return EqSym(_normalise_forall_cuts(proof.proof))
    if type(proof) is EqTrans:
        return EqTrans(
            _normalise_forall_cuts(proof.first),
            _normalise_forall_cuts(proof.second),
        )
    if type(proof) is CongS:
        return CongS(_normalise_forall_cuts(proof.proof))
    if type(proof) is CongAdd:
        return CongAdd(
            _normalise_forall_cuts(proof.left),
            _normalise_forall_cuts(proof.right),
        )
    if type(proof) is CongMul:
        return CongMul(
            _normalise_forall_cuts(proof.left),
            _normalise_forall_cuts(proof.right),
        )
    if type(proof) is EqSubst:
        return EqSubst(
            proof.motive,
            _normalise_forall_cuts(proof.equation),
            _normalise_forall_cuts(proof.body),
        )
    if type(proof) is Ind:
        return Ind(
            proof.motive,
            _normalise_forall_cuts(proof.base),
            _normalise_forall_cuts(proof.step),
        )
    if type(proof) in (EqRefl, DNE, Axiom):
        return proof
    raise ProofReductionError(
        f"unsupported proof node during normalization: {type(proof).__name__}"
    )


def normalise_cuts(proof: Proof) -> Proof:
    """Contract cuts, returning only an untrusted transformed certificate."""

    if not isinstance(proof, Proof):
        raise ProofReductionError("cut normalization needs an exact proof certificate")
    try:
        return _normalise_forall_cuts(proof)
    except ProofReductionError:
        raise
    except RecursionError:
        raise ProofReductionError(
            "cut normalization exceeded the host recursion limit"
        ) from None
    except (AttributeError, TypeError, ValueError):
        raise ProofReductionError(
            "malformed proof certificate during cut normalization"
        ) from None


__all__ = ["ProofReductionError", "normalise_cuts"]
