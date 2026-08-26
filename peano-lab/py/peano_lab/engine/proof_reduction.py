"""Capture-avoiding beta reduction for untrusted proof certificates.

The kernel deliberately has no theorem environment and no reduction rule for
proof terms.  Library replay and arithmetic automation may nevertheless expose
ordinary implication and universal beta redexes while constructing
certificates. This module contracts those redexes outside the trusted kernel,
preserving both proposition-hypothesis and term-variable De Bruijn scopes.
It deliberately preserves the kernel's self-contained ``Cut`` sharing nodes.

Reduction never grants authority: every caller must still submit the result to
the independent kernel checker against the intended formula.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, fields, replace

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
    Cut,
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


@dataclass(frozen=True, slots=True)
class LocalHave(Proof):
    """Engine-only proof-first scheduling for ``have h : proposition``.

    ``proof`` is checked in the ambient context. ``body`` is checked with the
    proposition at hypothesis index zero. Local compilation substitutes the
    former into the latter before the independent kernel sees the result.
    """

    proposition: Formula
    proof: Proof
    body: Proof


@dataclass(frozen=True, slots=True)
class LocalSuffices(Proof):
    """Engine-only continuation-first scheduling for ``suffices``.

    The field order deliberately mirrors the displayed goal order: first prove
    the old target assuming ``proposition``, then prove the proposition itself.
    The node has exactly the same cut-eliminated meaning as :class:`LocalHave`.
    """

    proposition: Formula
    body: Proof
    proof: Proof


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
    if type(proof) is LocalHave:
        return LocalHave(
            formula(proof.proposition),
            _open_term_slot(proof.proof, replacement, depth),
            _open_term_slot(proof.body, replacement, depth),
        )
    if type(proof) is LocalSuffices:
        return LocalSuffices(
            formula(proof.proposition),
            _open_term_slot(proof.body, replacement, depth),
            _open_term_slot(proof.proof, replacement, depth),
        )
    if type(proof) is Cut:
        return Cut(
            formula(proof.proposition),
            formula(proof.conclusion),
            _open_term_slot(proof.lemma, replacement, depth),
            _open_term_slot(proof.body, replacement, depth),
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
        elif type(proof) in (LocalHave, LocalSuffices) and item.name == "body":
            child_cutoff += 1
        elif type(proof) is Cut and item.name == "body":
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
        elif type(proof) in (LocalHave, LocalSuffices) and item.name == "body":
            child_cutoff += 1
        elif type(proof) is Cut and item.name == "body":
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
    """Contract exposed redexes while preserving input proof-DAG sharing.

    Normalization is a pure function of a proof object: it has no ambient
    hypothesis or term-depth parameter.  Therefore two incoming references to
    the same immutable proof object must have the same normalized result.  A
    per-invocation identity memo retains that sharing instead of materializing
    one copy per structural occurrence during interactive QED.

    Each memo entry holds the original object strongly as well as its result.
    That prevents a temporary object from being collected and its Python
    ``id`` being reused for a different proof during the same normalization.
    """

    memo: dict[int, tuple[Proof, Proof]] = {}

    def normalise(value: Proof) -> Proof:
        identity = id(value)
        cached = memo.get(identity)
        if cached is not None and cached[0] is value:
            return cached[1]
        result = _normalise_forall_cuts_uncached(value, normalise)
        memo[identity] = (value, result)
        return result

    return normalise(proof)


def _normalise_forall_cuts_uncached(
    proof: Proof,
    normalise: Callable[[Proof], Proof],
) -> Proof:
    """Normalize one previously unseen proof object."""

    if type(proof) is Hyp:
        return proof
    if type(proof) is ImpIntro:
        return ImpIntro(normalise(proof.body))
    if type(proof) is ImpElim:
        function = normalise(proof.function)
        argument = normalise(proof.argument)
        if type(function) is ImpIntro:
            return normalise(_open_hypothesis(function.body, argument))
        return ImpElim(function, argument)
    if type(proof) is LocalHave:
        if not isinstance(proof.proposition, Formula):
            raise ProofReductionError("local `have` needs a PA proposition")
        lemma = normalise(proof.proof)
        body = normalise(proof.body)
        return normalise(_open_hypothesis(body, lemma))
    if type(proof) is LocalSuffices:
        if not isinstance(proof.proposition, Formula):
            raise ProofReductionError("local `suffices` needs a PA proposition")
        body = normalise(proof.body)
        lemma = normalise(proof.proof)
        return normalise(_open_hypothesis(body, lemma))
    if type(proof) is Cut:
        return Cut(
            proof.proposition,
            proof.conclusion,
            normalise(proof.lemma),
            normalise(proof.body),
        )
    if type(proof) is AndIntro:
        return AndIntro(
            normalise(proof.left),
            normalise(proof.right),
        )
    if type(proof) is AndElimL:
        return AndElimL(normalise(proof.pair))
    if type(proof) is AndElimR:
        return AndElimR(normalise(proof.pair))
    if type(proof) is OrIntroL:
        return OrIntroL(normalise(proof.proof))
    if type(proof) is OrIntroR:
        return OrIntroR(normalise(proof.proof))
    if type(proof) is OrElim:
        return OrElim(
            normalise(proof.disjunction),
            normalise(proof.left_case),
            normalise(proof.right_case),
        )
    if type(proof) is BotElim:
        return BotElim(normalise(proof.absurdity))
    if type(proof) is ForallIntro:
        return ForallIntro(normalise(proof.body))
    if type(proof) is ForallElim:
        universal = normalise(proof.universal)
        if type(universal) is ForallIntro:
            return normalise(_open_term_slot(universal.body, proof.term))
        return ForallElim(universal, proof.term)
    if type(proof) is ExistsIntro:
        return ExistsIntro(proof.term, normalise(proof.proof))
    if type(proof) is ExistsElim:
        return ExistsElim(
            normalise(proof.existential),
            normalise(proof.body),
        )
    if type(proof) is EqSym:
        return EqSym(normalise(proof.proof))
    if type(proof) is EqTrans:
        return EqTrans(
            normalise(proof.first),
            normalise(proof.second),
        )
    if type(proof) is CongS:
        return CongS(normalise(proof.proof))
    if type(proof) is CongAdd:
        return CongAdd(
            normalise(proof.left),
            normalise(proof.right),
        )
    if type(proof) is CongMul:
        return CongMul(
            normalise(proof.left),
            normalise(proof.right),
        )
    if type(proof) is EqSubst:
        return EqSubst(
            proof.motive,
            normalise(proof.equation),
            normalise(proof.body),
        )
    if type(proof) is Ind:
        return Ind(
            proof.motive,
            normalise(proof.base),
            normalise(proof.step),
        )
    if type(proof) in (EqRefl, DNE, Axiom):
        return proof
    raise ProofReductionError(
        f"unsupported proof node during normalization: {type(proof).__name__}"
    )


def _erase_trusted_cuts(proof: Proof) -> Proof:
    """Expand every trusted :class:`Cut` without reducing the result."""

    if type(proof) is Hyp:
        return proof
    if type(proof) is ImpIntro:
        return ImpIntro(_erase_trusted_cuts(proof.body))
    if type(proof) is ImpElim:
        return ImpElim(
            _erase_trusted_cuts(proof.function),
            _erase_trusted_cuts(proof.argument),
        )
    if type(proof) is Cut:
        if not isinstance(proof.proposition, Formula) or not isinstance(
            proof.conclusion, Formula
        ):
            raise ProofReductionError(
                "trusted cut needs PA proposition and conclusion annotations"
            )
        return ImpElim(
            ImpIntro(_erase_trusted_cuts(proof.body)),
            _erase_trusted_cuts(proof.lemma),
        )
    if type(proof) is LocalHave:
        return LocalHave(
            proof.proposition,
            _erase_trusted_cuts(proof.proof),
            _erase_trusted_cuts(proof.body),
        )
    if type(proof) is LocalSuffices:
        return LocalSuffices(
            proof.proposition,
            _erase_trusted_cuts(proof.body),
            _erase_trusted_cuts(proof.proof),
        )
    if type(proof) is AndIntro:
        return AndIntro(
            _erase_trusted_cuts(proof.left),
            _erase_trusted_cuts(proof.right),
        )
    if type(proof) is AndElimL:
        return AndElimL(_erase_trusted_cuts(proof.pair))
    if type(proof) is AndElimR:
        return AndElimR(_erase_trusted_cuts(proof.pair))
    if type(proof) is OrIntroL:
        return OrIntroL(_erase_trusted_cuts(proof.proof))
    if type(proof) is OrIntroR:
        return OrIntroR(_erase_trusted_cuts(proof.proof))
    if type(proof) is OrElim:
        return OrElim(
            _erase_trusted_cuts(proof.disjunction),
            _erase_trusted_cuts(proof.left_case),
            _erase_trusted_cuts(proof.right_case),
        )
    if type(proof) is BotElim:
        return BotElim(_erase_trusted_cuts(proof.absurdity))
    if type(proof) is ForallIntro:
        return ForallIntro(_erase_trusted_cuts(proof.body))
    if type(proof) is ForallElim:
        return ForallElim(
            _erase_trusted_cuts(proof.universal),
            proof.term,
        )
    if type(proof) is ExistsIntro:
        return ExistsIntro(proof.term, _erase_trusted_cuts(proof.proof))
    if type(proof) is ExistsElim:
        return ExistsElim(
            _erase_trusted_cuts(proof.existential),
            _erase_trusted_cuts(proof.body),
        )
    if type(proof) is EqSym:
        return EqSym(_erase_trusted_cuts(proof.proof))
    if type(proof) is EqTrans:
        return EqTrans(
            _erase_trusted_cuts(proof.first),
            _erase_trusted_cuts(proof.second),
        )
    if type(proof) is CongS:
        return CongS(_erase_trusted_cuts(proof.proof))
    if type(proof) is CongAdd:
        return CongAdd(
            _erase_trusted_cuts(proof.left),
            _erase_trusted_cuts(proof.right),
        )
    if type(proof) is CongMul:
        return CongMul(
            _erase_trusted_cuts(proof.left),
            _erase_trusted_cuts(proof.right),
        )
    if type(proof) is EqSubst:
        return EqSubst(
            proof.motive,
            _erase_trusted_cuts(proof.equation),
            _erase_trusted_cuts(proof.body),
        )
    if type(proof) is Ind:
        return Ind(
            proof.motive,
            _erase_trusted_cuts(proof.base),
            _erase_trusted_cuts(proof.step),
        )
    if type(proof) in (EqRefl, DNE, Axiom):
        return proof
    raise ProofReductionError(
        f"unsupported proof node during trusted-cut erasure: {type(proof).__name__}"
    )


def erase_trusted_cuts(proof: Proof) -> Proof:
    """Expand trusted sharing nodes to ordinary implication proof terms.

    This compatibility transform accepts complete certificates, not live
    engine states containing holes.  It deliberately leaves the implication
    beta redexes it creates intact; callers may normalize them in a separate
    step and must still submit the result to the kernel. Logical admissibility
    does not imply that the current bidirectional reducer can round-trip every
    accepted Cut certificate, so this diagnostic has no admission authority.
    """

    if not isinstance(proof, Proof):
        raise ProofReductionError(
            "trusted-cut erasure needs an exact proof certificate"
        )
    try:
        return _erase_trusted_cuts(proof)
    except ProofReductionError:
        raise
    except RecursionError:
        raise ProofReductionError(
            "trusted-cut erasure exceeded the host recursion limit"
        ) from None
    except (AttributeError, TypeError, ValueError):
        raise ProofReductionError(
            "malformed proof certificate during trusted-cut erasure"
        ) from None


def normalise_cuts(proof: Proof) -> Proof:
    """Contract beta/admin cuts while preserving trusted sharing nodes."""

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


def compile_local_cuts(proof: Proof) -> Proof:
    """Eliminate local-reasoning schedulers, leaving ordinary proofs untouched.

    Proofs that contain ``have``/``suffices`` nodes receive the existing full
    capture-avoiding normalization pass. Proofs without those engine-only
    nodes are returned by identity, so adding local reasoning does not silently
    change certificates produced by older scripts.
    """

    if not isinstance(proof, Proof):
        raise ProofReductionError("local-cut compilation needs an exact proof certificate")

    def contains(value: Proof) -> bool:
        if type(value) in (LocalHave, LocalSuffices):
            return True
        for item in fields(value):
            child = getattr(value, item.name)
            if isinstance(child, Proof) and contains(child):
                return True
        return False

    try:
        if not contains(proof):
            return proof
        compiled = normalise_cuts(proof)
        if contains(compiled):
            raise ProofReductionError(
                "local-cut compilation left an engine-only scheduling node"
            )
        return compiled
    except ProofReductionError:
        raise
    except RecursionError:
        raise ProofReductionError(
            "local-cut compilation exceeded the host recursion limit"
        ) from None
    except (AttributeError, TypeError, ValueError):
        raise ProofReductionError(
            "malformed proof certificate during local-cut compilation"
        ) from None


__all__ = [
    "ProofReductionError",
    "LocalHave",
    "LocalSuffices",
    "compile_local_cuts",
    "erase_trusted_cuts",
    "normalise_cuts",
]
