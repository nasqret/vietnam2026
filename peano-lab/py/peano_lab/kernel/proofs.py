"""Proof certificates understood by the Peano Lab kernel.

The classes in this module are deliberately inert data.  Constructing a value
does *not* make it a theorem; only :func:`peano_lab.kernel.checker.check` can do
that.  Keeping certificates as small frozen trees makes them easy to inspect,
serialize, mutate in soundness tests, and check independently of the tactics
that produced them.
"""

from __future__ import annotations

from dataclasses import dataclass

from .formulas import Formula
from .terms import Term


class Proof:
    """Marker base class for proof-term constructors."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Hyp(Proof):
    """The hypothesis at ``index`` (zero is the newest hypothesis)."""

    i: int

    @property
    def index(self) -> int:
        return self.i


@dataclass(frozen=True, slots=True)
class ImpIntro(Proof):
    body: Proof


@dataclass(frozen=True, slots=True)
class ImpElim(Proof):
    f: Proof
    a: Proof

    @property
    def function(self) -> Proof:
        return self.f

    @property
    def argument(self) -> Proof:
        return self.a


@dataclass(frozen=True, slots=True)
class AndIntro(Proof):
    left: Proof
    right: Proof


@dataclass(frozen=True, slots=True)
class AndElimL(Proof):
    pair: Proof


@dataclass(frozen=True, slots=True)
class AndElimR(Proof):
    pair: Proof


@dataclass(frozen=True, slots=True)
class OrIntroL(Proof):
    proof: Proof


@dataclass(frozen=True, slots=True)
class OrIntroR(Proof):
    proof: Proof


@dataclass(frozen=True, slots=True)
class OrElim(Proof):
    disjunction: Proof
    left_case: Proof
    right_case: Proof


@dataclass(frozen=True, slots=True)
class BotElim(Proof):
    absurdity: Proof


@dataclass(frozen=True, slots=True)
class ForallIntro(Proof):
    body: Proof


@dataclass(frozen=True, slots=True)
class ForallElim(Proof):
    p: Proof
    t: Term

    @property
    def universal(self) -> Proof:
        return self.p

    @property
    def term(self) -> Term:
        return self.t


@dataclass(frozen=True, slots=True)
class ExistsIntro(Proof):
    t: Term
    p: Proof

    @property
    def term(self) -> Term:
        return self.t

    @property
    def proof(self) -> Proof:
        return self.p


@dataclass(frozen=True, slots=True)
class ExistsElim(Proof):
    p: Proof
    body: Proof

    @property
    def existential(self) -> Proof:
        return self.p


@dataclass(frozen=True, slots=True)
class EqRefl(Proof):
    t: Term

    @property
    def term(self) -> Term:
        return self.t


@dataclass(frozen=True, slots=True)
class EqSym(Proof):
    proof: Proof


@dataclass(frozen=True, slots=True)
class EqTrans(Proof):
    first: Proof
    second: Proof


@dataclass(frozen=True, slots=True)
class CongS(Proof):
    proof: Proof


@dataclass(frozen=True, slots=True)
class CongAdd(Proof):
    left: Proof
    right: Proof


@dataclass(frozen=True, slots=True)
class CongMul(Proof):
    left: Proof
    right: Proof


@dataclass(frozen=True, slots=True)
class EqSubst(Proof):
    """Leibniz substitution.

    ``motive`` has one distinguished free variable at de Bruijn index zero.
    If ``equation`` proves ``s = t`` and ``body`` proves ``motive[s]``, this
    certificate proves ``motive[t]``.
    """

    motive: Formula
    eq_proof: Proof
    body_proof: Proof

    @property
    def equation(self) -> Proof:
        return self.eq_proof

    @property
    def body(self) -> Proof:
        return self.body_proof


@dataclass(frozen=True, slots=True)
class Axiom(Proof):
    """One of the six fixed arithmetic axiom constants, ``PA1`` ... ``PA6``."""

    name: str


@dataclass(frozen=True, slots=True)
class Ind(Proof):
    """An instance of the induction schema for ``motive``.

    The motive is a formula with its induction variable at index zero.
    ``base`` proves its zero instance and ``step`` proves the universally
    quantified successor step.
    """

    motive: Formula
    base: Proof
    step: Proof


__all__ = [
    "Proof",
    "Hyp",
    "ImpIntro",
    "ImpElim",
    "AndIntro",
    "AndElimL",
    "AndElimR",
    "OrIntroL",
    "OrIntroR",
    "OrElim",
    "BotElim",
    "ForallIntro",
    "ForallElim",
    "ExistsIntro",
    "ExistsElim",
    "EqRefl",
    "EqSym",
    "EqTrans",
    "CongS",
    "CongAdd",
    "CongMul",
    "EqSubst",
    "Axiom",
    "Ind",
]
