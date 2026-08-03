"""Canonical, inert ``peano-lab-v2`` artifact encoding.

This module mirrors the tagged-array grammar in the verified Lean
``PeanoLab/Codec.lean`` file.  It only turns existing kernel syntax into a
unique byte representation; it does not validate a derivation and cannot
grant QED.  Call :func:`peano_lab.kernel.checker.check` independently against
the original goal before treating any encoded proof as a theorem.

Every syntax node must be one of the exact frozen kernel constructors.  In
particular, subclasses and malformed runtime values are rejected instead of
being interpreted through Python's extensible equality or serialization
protocols.  Natural numbers use their canonical non-negative decimal spelling
and a complete artifact ends in exactly one LF byte.
"""

from __future__ import annotations

from collections.abc import Callable

from .formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from .proofs import (
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
from .terms import Add, Mul, Succ, Term, Var, Zero


FORMAT_TAG = "peano-lab-v2"


class ArtifactLimitError(ValueError):
    """Canonical encoding exceeded an explicit caller-owned byte ceiling."""


def _nat_bytes(
    value: object, label: str, *, max_bytes: int | None = None
) -> bytes:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    if max_bytes is not None:
        if max_bytes < 1:
            raise ArtifactLimitError("canonical artifact exceeds its byte limit")
        # Every positive integer with b bits has at least
        # floor((b - 1) * log10(2)) + 1 decimal digits.  The deliberately
        # smaller rational 301/1000 makes this a safe rejection-only bound and
        # prevents a huge integer from allocating an equally huge chunk list.
        if value and ((value.bit_length() - 1) * 301) // 1000 + 1 > max_bytes:
            raise ArtifactLimitError("canonical artifact exceeds its byte limit")
    if value == 0:
        return b"0"

    # Converting one enormous int with str() is process-limited on modern
    # CPython.  Lean Nat is unbounded, so spell it through safely small chunks.
    chunks: list[int] = []
    while value:
        value, remainder = divmod(value, 1_000_000_000)
        chunks.append(remainder)
        if max_bytes is not None and 9 * (len(chunks) - 1) + 1 > max_bytes:
            raise ArtifactLimitError("canonical artifact exceeds its byte limit")
    if max_bytes is not None:
        exact_bytes = len(str(chunks[-1])) + 9 * (len(chunks) - 1)
        if exact_bytes > max_bytes:
            raise ArtifactLimitError("canonical artifact exceeds its byte limit")
    result = bytearray(str(chunks.pop()).encode("ascii"))
    while chunks:
        result.extend(f"{chunks.pop():09d}".encode("ascii"))
    return bytes(result)


class _Writer:
    """Append canonical bytes while rejecting cyclic syntax graphs."""

    __slots__ = ("active", "max_bytes", "output")

    def __init__(self, max_bytes: int | None = None) -> None:
        if max_bytes is not None and (type(max_bytes) is not int or max_bytes < 1):
            raise ValueError("artifact byte limit must be a positive integer")
        self.output = bytearray()
        self.active: set[int] = set()
        self.max_bytes = max_bytes

    def _extend(self, data: bytes | bytearray) -> None:
        if self.max_bytes is not None and len(self.output) + len(data) > self.max_bytes:
            raise ArtifactLimitError(
                f"canonical artifact exceeds the {self.max_bytes}-byte limit"
            )
        self.output.extend(data)

    def _nat(self, value: object, label: str) -> None:
        remaining = (
            None if self.max_bytes is None else self.max_bytes - len(self.output)
        )
        self._extend(_nat_bytes(value, label, max_bytes=remaining))

    def _enter(self, node: object) -> int:
        identity = id(node)
        if identity in self.active:
            raise ValueError("cyclic Peano Lab syntax cannot be encoded")
        self.active.add(identity)
        return identity

    def _leave(self, identity: int) -> None:
        self.active.remove(identity)

    def _open(self, tag: bytes) -> None:
        self._extend(b'["')
        self._extend(tag)
        self._extend(b'"')

    def _separator(self) -> None:
        self._extend(b",")

    def _close(self) -> None:
        self._extend(b"]")

    def _proof_children(self, tag: bytes, *children: object) -> None:
        self._open(tag)
        for child in children:
            self._separator()
            self.proof(child)

    def term(self, term: object) -> None:
        constructor = type(term)
        identity = self._enter(term)
        try:
            if constructor is Var:
                self._open(b"var")
                self._separator()
                self._nat(term.index, "variable index")
            elif constructor is Zero:
                self._open(b"zero")
            elif constructor is Succ:
                self._open(b"succ")
                self._separator()
                self.term(term.term)
            elif constructor is Add:
                self._open(b"add")
                self._separator()
                self.term(term.left)
                self._separator()
                self.term(term.right)
            elif constructor is Mul:
                self._open(b"mul")
                self._separator()
                self.term(term.left)
                self._separator()
                self.term(term.right)
            else:
                raise TypeError("expected an exact Peano Lab term constructor")
            self._close()
        finally:
            self._leave(identity)

    def formula(self, formula: object) -> None:
        constructor = type(formula)
        identity = self._enter(formula)
        try:
            if constructor is Eq:
                self._open(b"eq")
                self._separator()
                self.term(formula.left)
                self._separator()
                self.term(formula.right)
            elif constructor is Bot:
                self._open(b"bot")
            elif constructor is Imp:
                self._open(b"imp")
                self._separator()
                self.formula(formula.antecedent)
                self._separator()
                self.formula(formula.consequent)
            elif constructor is And:
                self._open(b"and")
                self._separator()
                self.formula(formula.left)
                self._separator()
                self.formula(formula.right)
            elif constructor is Or:
                self._open(b"or")
                self._separator()
                self.formula(formula.left)
                self._separator()
                self.formula(formula.right)
            elif constructor is Forall:
                self._open(b"forall")
                self._separator()
                self.formula(formula.body)
            elif constructor is Exists:
                self._open(b"exists")
                self._separator()
                self.formula(formula.body)
            else:
                raise TypeError("expected an exact Peano Lab formula constructor")
            self._close()
        finally:
            self._leave(identity)

    def proof(self, proof: object) -> None:
        constructor = type(proof)
        identity = self._enter(proof)
        try:
            if constructor is Hyp:
                self._open(b"hyp")
                self._separator()
                self._nat(proof.i, "hypothesis index")
            elif constructor is ImpIntro:
                self._proof_children(b"imp_intro", proof.body)
            elif constructor is ImpElim:
                self._proof_children(b"imp_elim", proof.f, proof.a)
            elif constructor is Cut:
                self._open(b"cut")
                self._separator()
                self.formula(proof.proposition)
                self._separator()
                self.formula(proof.conclusion)
                self._separator()
                self.proof(proof.lemma)
                self._separator()
                self.proof(proof.body)
            elif constructor is AndIntro:
                self._proof_children(b"and_intro", proof.left, proof.right)
            elif constructor is AndElimL:
                self._proof_children(b"and_elim_l", proof.pair)
            elif constructor is AndElimR:
                self._proof_children(b"and_elim_r", proof.pair)
            elif constructor is OrIntroL:
                self._proof_children(b"or_intro_l", proof.proof)
            elif constructor is OrIntroR:
                self._proof_children(b"or_intro_r", proof.proof)
            elif constructor is OrElim:
                self._proof_children(
                    b"or_elim", proof.disjunction, proof.left_case, proof.right_case
                )
            elif constructor is BotElim:
                self._proof_children(b"bot_elim", proof.absurdity)
            elif constructor is ForallIntro:
                self._proof_children(b"forall_intro", proof.body)
            elif constructor is ForallElim:
                self._open(b"forall_elim")
                self._separator()
                self.proof(proof.p)
                self._separator()
                self.term(proof.t)
            elif constructor is ExistsIntro:
                self._open(b"exists_intro")
                self._separator()
                self.term(proof.t)
                self._separator()
                self.proof(proof.p)
            elif constructor is ExistsElim:
                self._proof_children(b"exists_elim", proof.p, proof.body)
            elif constructor is EqRefl:
                self._open(b"eq_refl")
                self._separator()
                self.term(proof.t)
            elif constructor is EqSym:
                self._proof_children(b"eq_sym", proof.proof)
            elif constructor is EqTrans:
                self._proof_children(b"eq_trans", proof.first, proof.second)
            elif constructor is CongS:
                self._proof_children(b"cong_s", proof.proof)
            elif constructor is CongAdd:
                self._proof_children(b"cong_add", proof.left, proof.right)
            elif constructor is CongMul:
                self._proof_children(b"cong_mul", proof.left, proof.right)
            elif constructor is EqSubst:
                self._open(b"eq_subst")
                self._separator()
                self.formula(proof.motive)
                self._separator()
                self.proof(proof.eq_proof)
                self._separator()
                self.proof(proof.body_proof)
            elif constructor is DNE:
                self._open(b"dne")
                self._separator()
                self.formula(proof.proposition)
            elif constructor is Axiom:
                if type(proof.name) is not str or proof.name not in (
                    "PA1",
                    "PA2",
                    "PA3",
                    "PA4",
                    "PA5",
                    "PA6",
                ):
                    raise ValueError("axiom name must be exactly PA1 through PA6")
                self._open(b"axiom")
                self._separator()
                self._extend(b'"')
                self._extend(proof.name.encode("ascii"))
                self._extend(b'"')
            elif constructor is Ind:
                self._open(b"ind")
                self._separator()
                self.formula(proof.motive)
                self._separator()
                self.proof(proof.base)
                self._separator()
                self.proof(proof.step)
            else:
                raise TypeError("expected an exact Peano Lab proof constructor")
            self._close()
        finally:
            self._leave(identity)


def _finish(write: Callable[[_Writer, object], None], value: object) -> bytes:
    writer = _Writer()
    try:
        write(writer, value)
    except AttributeError as error:
        raise TypeError("malformed Peano Lab syntax node") from error
    except RecursionError as error:
        raise ValueError("Peano Lab syntax exceeds the encoder nesting limit") from error
    return bytes(writer.output)


def encode_term(term: Term) -> bytes:
    """Encode one exact term using the canonical tagged-array grammar."""

    return _finish(_Writer.term, term)


def encode_formula(formula: Formula) -> bytes:
    """Encode one exact formula using the canonical tagged-array grammar."""

    return _finish(_Writer.formula, formula)


def encode_proof(proof: Proof) -> bytes:
    """Encode one exact inert proof term without checking it."""

    return _finish(_Writer.proof, proof)


def encode_artifact(fuel: int, target: Formula, proof: Proof) -> bytes:
    """Encode a canonical Cut-aware ``peano-lab-v2`` artifact.

    The result is ASCII-compatible UTF-8 and ends in exactly one LF.  Encoding
    is deliberately independent of proof checking: callers must separately
    invoke the authoritative Python checker against ``target``.
    """

    return encode_artifact_bounded(fuel, target, proof, max_bytes=None)


def encode_artifact_bounded(
    fuel: int,
    target: Formula,
    proof: Proof,
    *,
    max_bytes: int | None,
) -> bytes:
    """Encode an artifact while optionally refusing to allocate past a ceiling.

    ``None`` preserves :func:`encode_artifact`'s unbounded canonical API.  A
    finite limit includes the mandatory terminal LF and is an availability
    boundary only: this encoder remains inert and never checks a proof.
    """

    writer = _Writer(max_bytes)
    try:
        writer._open(b"peano-lab-v2")
        writer._separator()
        writer._nat(fuel, "artifact fuel")
        writer._separator()
        writer.formula(target)
        writer._separator()
        writer.proof(proof)
        writer._close()
    except AttributeError as error:
        raise TypeError("malformed Peano Lab syntax node") from error
    except RecursionError as error:
        raise ValueError("Peano Lab syntax exceeds the encoder nesting limit") from error
    writer._extend(b"\n")
    return bytes(writer.output)


__all__ = [
    "ArtifactLimitError",
    "FORMAT_TAG",
    "encode_artifact",
    "encode_artifact_bounded",
    "encode_formula",
    "encode_proof",
    "encode_term",
]
