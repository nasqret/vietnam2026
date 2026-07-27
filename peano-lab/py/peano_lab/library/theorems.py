"""The checked Peano Lab theorem ladder.

Library entries are data: a closed statement, earlier dependencies, and a
tactic script.  Replaying an entry first proves the dependencies as
ordinary implication hypotheses.  The untrusted library layer then performs
the corresponding proof-term substitutions (cut elimination) and submits the
resulting *closed* certificate to the independent kernel against the entry's
original statement.

This indirection is deliberate.  The binding kernel has no trusted theorem
environment and no proof-ascription constructor; adding either merely for
library reuse would enlarge the soundness boundary.  A bug in replay or cut
elimination can therefore cause only rejection, never a false theorem.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache

from ..engine.state import proof_size, start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.checker import check
from ..kernel.formulas import Formula, Imp, parse_formula_with_names
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


class LibraryError(ValueError):
    """A theorem entry or replay violates the checked-library contract."""


@dataclass(frozen=True, slots=True)
class TheoremSpec:
    """One named rung of the theorem ladder."""

    name: str
    statement: str
    dependencies: tuple[str, ...]
    script: tuple[str, ...]
    summary: str


@dataclass(frozen=True, slots=True)
class CheckedTheorem:
    """A replay result whose certificate checked for the original statement."""

    spec: TheoremSpec
    formula: Formula
    certificate: Proof
    proof_nodes: int


def _closed_formula(source: str) -> Formula:
    formula, free_names = parse_formula_with_names(source)
    if free_names:
        raise LibraryError(
            "library theorem statements must be closed; free variable(s): "
            + ", ".join(free_names)
        )
    return formula


def _replace_removed_hypothesis(
    proof: Proof,
    replacement: Proof | tuple[Proof, ...],
    depth: int = 0,
) -> Proof:
    """Remove dependency slots and inline closed proofs simultaneously.

    ``depth`` counts newer proposition hypotheses introduced below the slot.
    Replacements are in declaration order, while the newest dependency is
    de Bruijn hypothesis zero.  Doing this in one traversal is essential:
    sequential passes would revisit hypotheses internal to an already-inserted
    certificate.  Every replacement is closed and already kernel-checked.
    """

    replacements = replacement if type(replacement) is tuple else (replacement,)
    if not replacements or not all(isinstance(item, Proof) for item in replacements):
        raise LibraryError("dependency substitution needs checked proof terms")

    if type(proof) is Hyp:
        relative = proof.index - depth
        if 0 <= relative < len(replacements):
            return replacements[-1 - relative]
        return Hyp(proof.index - len(replacements)) if relative >= len(replacements) else proof
    if type(proof) is ImpIntro:
        return ImpIntro(_replace_removed_hypothesis(proof.body, replacements, depth + 1))
    if type(proof) is ImpElim:
        return ImpElim(
            _replace_removed_hypothesis(proof.function, replacements, depth),
            _replace_removed_hypothesis(proof.argument, replacements, depth),
        )
    if type(proof) is AndIntro:
        return AndIntro(
            _replace_removed_hypothesis(proof.left, replacements, depth),
            _replace_removed_hypothesis(proof.right, replacements, depth),
        )
    if type(proof) is AndElimL:
        return AndElimL(_replace_removed_hypothesis(proof.pair, replacements, depth))
    if type(proof) is AndElimR:
        return AndElimR(_replace_removed_hypothesis(proof.pair, replacements, depth))
    if type(proof) is OrIntroL:
        return OrIntroL(_replace_removed_hypothesis(proof.proof, replacements, depth))
    if type(proof) is OrIntroR:
        return OrIntroR(_replace_removed_hypothesis(proof.proof, replacements, depth))
    if type(proof) is OrElim:
        return OrElim(
            _replace_removed_hypothesis(proof.disjunction, replacements, depth),
            _replace_removed_hypothesis(proof.left_case, replacements, depth + 1),
            _replace_removed_hypothesis(proof.right_case, replacements, depth + 1),
        )
    if type(proof) is BotElim:
        return BotElim(_replace_removed_hypothesis(proof.absurdity, replacements, depth))
    if type(proof) is ForallIntro:
        return ForallIntro(_replace_removed_hypothesis(proof.body, replacements, depth))
    if type(proof) is ForallElim:
        return ForallElim(
            _replace_removed_hypothesis(proof.universal, replacements, depth),
            proof.term,
        )
    if type(proof) is ExistsIntro:
        return ExistsIntro(
            proof.term,
            _replace_removed_hypothesis(proof.proof, replacements, depth),
        )
    if type(proof) is ExistsElim:
        return ExistsElim(
            _replace_removed_hypothesis(proof.existential, replacements, depth),
            _replace_removed_hypothesis(proof.body, replacements, depth + 1),
        )
    if type(proof) is EqSym:
        return EqSym(_replace_removed_hypothesis(proof.proof, replacements, depth))
    if type(proof) is EqTrans:
        return EqTrans(
            _replace_removed_hypothesis(proof.first, replacements, depth),
            _replace_removed_hypothesis(proof.second, replacements, depth),
        )
    if type(proof) is CongS:
        return CongS(_replace_removed_hypothesis(proof.proof, replacements, depth))
    if type(proof) is CongAdd:
        return CongAdd(
            _replace_removed_hypothesis(proof.left, replacements, depth),
            _replace_removed_hypothesis(proof.right, replacements, depth),
        )
    if type(proof) is CongMul:
        return CongMul(
            _replace_removed_hypothesis(proof.left, replacements, depth),
            _replace_removed_hypothesis(proof.right, replacements, depth),
        )
    if type(proof) is EqSubst:
        return EqSubst(
            proof.motive,
            _replace_removed_hypothesis(proof.equation, replacements, depth),
            _replace_removed_hypothesis(proof.body, replacements, depth),
        )
    if type(proof) is Ind:
        return Ind(
            proof.motive,
            _replace_removed_hypothesis(proof.base, replacements, depth),
            _replace_removed_hypothesis(proof.step, replacements, depth),
        )
    if type(proof) in (EqRefl, DNE, Axiom):
        return proof
    raise LibraryError(f"unsupported proof node during cut elimination: {type(proof).__name__}")


def _open_term_slot(proof: Proof, replacement: object, depth: int = 0) -> Proof:
    """Open one surrounding de Bruijn term slot throughout a certificate.

    This is proof-level substitution used only to contract a
    ``ForallElim(ForallIntro(...), term)`` redex exposed by dependency cut
    elimination.  Formula motives stored by ``EqSubst`` and ``Ind`` have their
    own distinguished variable at index zero, hence their extra cutoff.
    """

    if not isinstance(replacement, Term):
        raise LibraryError("proof-level term substitution needs a PA term")

    lifted = shift_term(replacement, depth)

    def term(value: object):
        if not isinstance(value, Term):
            raise LibraryError("malformed term stored in a proof certificate")
        return subst_term(value, depth, lifted)

    def formula(value: object, *, motive: bool = False):
        if not isinstance(value, Formula):
            raise LibraryError("malformed formula stored in a proof certificate")
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
    raise LibraryError(f"unsupported proof node during term substitution: {type(proof).__name__}")


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
            return _normalise_forall_cuts(
                _open_hypothesis(function.body, argument)
            )
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
    raise LibraryError(f"unsupported proof node during normalization: {type(proof).__name__}")


def normalise_cuts(proof: Proof) -> Proof:
    """Contract theorem-reuse cuts in an untrusted proof certificate.

    This public wrapper is shared by scripted library replay and live proof
    sessions.  Its output never receives special authority: callers must still
    submit the resulting certificate to the independent kernel checker against
    the original theorem.
    """

    if not isinstance(proof, Proof):
        raise LibraryError("cut normalization needs an exact proof certificate")
    try:
        return _normalise_forall_cuts(proof)
    except RecursionError:
        raise LibraryError("cut normalization exceeded the host recursion limit") from None


def _primitive(command: str) -> tuple[str, str]:
    pieces = command.strip().split(maxsplit=1)
    if not pieces:
        raise LibraryError("library scripts cannot contain blank commands")
    return pieces[0], pieces[1] if len(pieces) == 2 else ""


# Ladder order is pedagogical and part of the public browser index.  A
# dependency may name only an earlier entry; replay validates that invariant.
THEOREMS: tuple[TheoremSpec, ...] = (
    TheoremSpec(
        "zero_add",
        "forall n. 0 + n = n",
        (),
        ("induction n", "simp", "simp [IH]"),
        "Zero is a left identity for addition; unlike PA3, this needs induction.",
    ),
    TheoremSpec(
        "add_succ_left",
        "forall n m. S n + m = S (n + m)",
        (),
        ("intro n", "induction m", "simp", "simp [IH]"),
        "A successor can move through addition on the left.",
    ),
    TheoremSpec(
        "add_comm",
        "forall n m. n + m = m + n",
        ("zero_add", "add_succ_left"),
        (
            "intro n",
            "induction m",
            "simp [zero_add]",
            "simp [add_succ_left, IH]",
        ),
        "Addition is commutative.",
    ),
    TheoremSpec(
        "add_assoc",
        "forall n m k. (n + m) + k = n + (m + k)",
        (),
        ("intro n", "intro m", "induction k", "simp", "simp [IH]"),
        "Addition is associative.",
    ),
    TheoremSpec(
        "mul_zero_left",
        "forall n. 0 * n = 0",
        (),
        ("induction n", "simp", "simp [IH]"),
        "Zero annihilates multiplication on the left.",
    ),
    TheoremSpec(
        "mul_succ_left",
        "forall n m. S n * m = n * m + m",
        ("add_comm", "add_assoc"),
        (
            "intro n",
            "induction m",
            "simp",
            "specialize add_comm n",
            "specialize add_comm m",
            "simp [IH, add_comm, add_assoc]",
        ),
        "A successor can move through multiplication on the left.",
    ),
    TheoremSpec(
        "mul_comm",
        "forall n m. n * m = m * n",
        ("mul_zero_left", "mul_succ_left"),
        (
            "intro n",
            "induction m",
            "simp [mul_zero_left]",
            "simp [IH, mul_succ_left]",
        ),
        "Multiplication is commutative.",
    ),
    TheoremSpec(
        "mul_add",
        "forall n m k. n * (m + k) = n * m + n * k",
        ("add_assoc",),
        (
            "intro n",
            "intro m",
            "induction k",
            "simp",
            "simp [IH, add_assoc]",
        ),
        "Multiplication distributes over addition on the right.",
    ),
    TheoremSpec(
        "mul_assoc",
        "forall n m k. (n * m) * k = n * (m * k)",
        ("mul_add",),
        (
            "intro n",
            "intro m",
            "induction k",
            "simp",
            "simp [IH, mul_add]",
        ),
        "Multiplication is associative.",
    ),
    TheoremSpec(
        "succ_ne_zero",
        "forall n. ~(S n = 0)",
        (),
        ("apply PA1",),
        "No successor is zero (the reusable PA1 lemma).",
    ),
    TheoremSpec(
        "succ_injective",
        "forall n m. S n = S m -> n = m",
        (),
        ("apply PA2",),
        "Successor is injective (the reusable PA2 lemma).",
    ),
    TheoremSpec(
        "le_refl",
        "forall n. n <= n",
        ("zero_add",),
        ("intro n", "exists 0", "simp [zero_add]"),
        "The defined order is reflexive; zero is its witness.",
    ),
    TheoremSpec(
        "le_trans",
        "forall n m k. n <= m -> m <= k -> n <= k",
        ("add_assoc",),
        (
            "intro n",
            "intro m",
            "intro k",
            "intro h_nm",
            "intro h_mk",
            "cases h_nm",
            "cases h_mk",
            "exists x1 + x",
            "simp [add_assoc, h_nm_witness, h_mk_witness]",
        ),
        "Order witnesses compose by addition, so the defined order is transitive.",
    ),
    TheoremSpec(
        "no_succ_add_fixed",
        "forall p n. S p + n = n -> false",
        (),
        (
            "intro p",
            "induction n",
            "intro h",
            "apply PA1",
            "rewrite PA3 at h",
            "exact h",
            "intro h",
            "apply IH",
            "apply PA2",
            "rewrite PA4 at h",
            "exact h",
        ),
        "Adding a positive successor cannot leave a natural number fixed.",
    ),
    TheoremSpec(
        "drop_add_prefix_from_fixed",
        "forall a b n. (b + a) + n = n -> a + n = n",
        ("zero_add", "add_succ_left", "no_succ_add_fixed"),
        (
            "intro a",
            "induction b",
            "intro n",
            "intro h",
            "specialize zero_add a",
            "rewrite zero_add at h",
            "exact h",
            "intro n",
            "intro h",
            "exfalso",
            "specialize no_succ_add_fixed (b + a)",
            "specialize no_succ_add_fixed n",
            "apply no_succ_add_fixed",
            "specialize add_succ_left b",
            "specialize add_succ_left a",
            "rewrite add_succ_left at h",
            "exact h",
        ),
        "A fixed-point equation remains fixed after dropping an additive prefix.",
    ),
    TheoremSpec(
        "antisymm_from_witnesses",
        "forall a b n m. a + n = m -> b + m = n -> n = m",
        ("add_assoc", "drop_add_prefix_from_fixed"),
        (
            "intro a",
            "intro b",
            "intro n",
            "intro m",
            "intro h_anm",
            "intro h_bmn",
            "symm",
            "rewrite <- h_anm",
            "specialize drop_add_prefix_from_fixed a",
            "specialize drop_add_prefix_from_fixed b",
            "specialize drop_add_prefix_from_fixed n",
            "apply drop_add_prefix_from_fixed",
            "specialize add_assoc b",
            "specialize add_assoc a",
            "specialize add_assoc n",
            "rewrite add_assoc",
            "rewrite h_anm",
            "rewrite h_bmn",
            "refl",
        ),
        "Opposing additive witnesses force equality.",
    ),
    TheoremSpec(
        "le_antisymm",
        "forall n m. n <= m -> m <= n -> n = m",
        ("antisymm_from_witnesses",),
        (
            "intro n",
            "intro m",
            "intro h_nm",
            "intro h_mn",
            "cases h_nm",
            "cases h_mn",
            "apply antisymm_from_witnesses",
            "exact h_nm_witness",
            "exact h_mn_witness",
        ),
        "The witness-defined order is antisymmetric.",
    ),
    TheoremSpec(
        "le_total",
        "forall n m. n <= m \\/ m <= n",
        (),
        (
            "induction n",
            "intro m",
            "left",
            "exists m",
            "simp",
            "induction m",
            "right",
            "exists (S n)",
            "simp",
            "specialize IH m",
            "cases IH",
            "cases IH_left",
            "left",
            "exists x",
            "rewrite PA4",
            "congr",
            "exact IH_left_witness",
            "cases IH_right",
            "right",
            "exists x",
            "rewrite PA4",
            "congr",
            "exact IH_right_witness",
        ),
        "Every pair of natural numbers is comparable in the defined order.",
    ),
    TheoremSpec(
        "add_eq_zero_right",
        "forall a b. a + b = 0 -> b = 0",
        (),
        (
            "intro a",
            "induction b",
            "intro h",
            "refl",
            "intro h",
            "exfalso",
            "apply PA1",
            "rewrite PA4 at h",
            "exact h",
        ),
        "A sum equal to zero has zero as its right addend.",
    ),
    TheoremSpec(
        "mul_eq_zero",
        "forall n m. n * m = 0 -> n = 0 \\/ m = 0",
        ("add_eq_zero_right",),
        (
            "intro n",
            "induction m",
            "intro h",
            "right",
            "refl",
            "intro h",
            "left",
            "specialize add_eq_zero_right (n * m)",
            "specialize add_eq_zero_right n",
            "apply add_eq_zero_right",
            "rewrite PA6 at h",
            "exact h",
        ),
        "Zero products have a zero factor: the theorem-ladder capstone.",
    ),
)


def names() -> tuple[str, ...]:
    """Return canonical theorem names in ladder order."""

    return tuple(spec.name for spec in THEOREMS)


def get(name: str) -> TheoremSpec | None:
    """Look up a theorem by its exact or case-folded canonical name."""

    if not isinstance(name, str):
        return None
    wanted = name.strip().casefold()
    return next((spec for spec in THEOREMS if spec.name.casefold() == wanted), None)


def _validated_specs() -> dict[str, TheoremSpec]:
    result: dict[str, TheoremSpec] = {}
    for spec in THEOREMS:
        if not spec.name or spec.name != spec.name.strip() or any(c.isspace() for c in spec.name):
            raise LibraryError("library theorem names must be non-empty single words")
        if spec.name in result:
            raise LibraryError(f"duplicate library theorem {spec.name!r}")
        _closed_formula(spec.statement)
        if not spec.script:
            raise LibraryError(f"library theorem {spec.name!r} needs a tactic script")
        for dependency in spec.dependencies:
            if dependency not in result:
                raise LibraryError(
                    f"theorem {spec.name!r} depends on unavailable earlier theorem "
                    f"{dependency!r}"
                )
        result[spec.name] = spec
    return result


@lru_cache(maxsize=1)
def _specs_by_name() -> dict[str, TheoremSpec]:
    return _validated_specs()


def replay_target(spec: TheoremSpec) -> Formula:
    """Return the dependency-curried goal replayed by ``spec.script``."""

    table = _specs_by_name()
    target = _closed_formula(spec.statement)
    for dependency in reversed(spec.dependencies):
        target = Imp(_closed_formula(table[dependency].statement), target)
    return target


@lru_cache(maxsize=None)
def replay(name: str) -> CheckedTheorem:
    """Replay one entry and independently check its closed final certificate."""

    spec = _specs_by_name().get(name)
    if spec is None:
        raise LibraryError(f"unknown library theorem {name!r}")

    target = replay_target(spec)
    state = start(target)
    for dependency in spec.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in spec.script:
        tactic, args = _primitive(command)
        state = apply_tactic(state, tactic, args)
    certificate = checked_final(state, target)

    # Peel every generated dependency introduction, then substitute all
    # dependency slots in one pass.  Inserted certificates are consequently
    # opaque to the traversal and their own local hypotheses cannot be
    # mistaken for another ambient dependency.
    closed = certificate
    dependency_proofs = tuple(replay(item).certificate for item in spec.dependencies)
    for dependency in spec.dependencies:
        if type(closed) is not ImpIntro:
            raise LibraryError(
                f"replay for {spec.name!r} did not expose dependency {dependency!r}"
            )
        closed = closed.body
    if dependency_proofs:
        closed = normalise_cuts(
            _replace_removed_hypothesis(closed, dependency_proofs)
        )

    formula = _closed_formula(spec.statement)
    if not check((), closed, formula):
        raise LibraryError(
            f"the independent kernel rejected library theorem {spec.name!r}"
        )
    return CheckedTheorem(spec, formula, closed, proof_size(closed))


def replay_all() -> tuple[CheckedTheorem, ...]:
    """Replay the entire ladder in its deterministic dependency order."""

    return tuple(replay(spec.name) for spec in THEOREMS)


__all__ = [
    "LibraryError",
    "TheoremSpec",
    "CheckedTheorem",
    "THEOREMS",
    "names",
    "get",
    "replay_target",
    "replay",
    "replay_all",
    "normalise_cuts",
]
