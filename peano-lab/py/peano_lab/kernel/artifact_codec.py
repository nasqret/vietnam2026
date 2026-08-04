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
import json

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
MAX_DECODE_ARTIFACT_BYTES = 8_000_000
MAX_DECODE_NODES = 1_000_000
MAX_DECODE_DEPTH = 512
MAX_DECODE_INTEGER_DIGITS = 4_096


class ArtifactLimitError(ValueError):
    """Canonical encoding exceeded an explicit caller-owned byte ceiling."""


class ArtifactDecodeError(ValueError):
    """Untrusted bytes are not one bounded canonical kernel artifact."""


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


def _reject_decoded_float(value: str) -> object:
    raise ArtifactDecodeError(
        f"artifact contains forbidden floating-point value {value!r}"
    )


def _reject_decoded_constant(value: str) -> object:
    raise ArtifactDecodeError(f"artifact contains forbidden JSON constant {value!r}")


def _parse_decoded_integer(value: str) -> int:
    """Parse one bounded JSON integer without CPython's mutable digit limit."""

    negative = value.startswith("-")
    digits = value[1:] if negative else value
    if not digits or len(digits) > MAX_DECODE_INTEGER_DIGITS:
        raise ArtifactDecodeError(
            "artifact integer exceeds the bounded decimal-digit limit"
        )
    result = 0
    for start in range(0, len(digits), 9):
        chunk = digits[start : start + 9]
        result = result * (10 ** len(chunk)) + int(chunk)
    return -result if negative else result


class _Decoder:
    """Turn one already-parsed tagged tree into exact kernel constructors.

    This decoder is deliberately untrusted infrastructure.  Its output grants
    no theorem authority: callers must compare the decoded target with their
    separately committed target and invoke the independent kernel checker.
    Re-encoding at the public boundary makes the accepted wire spelling
    unique.
    """

    __slots__ = ("max_depth", "max_nodes", "nodes")

    def __init__(self, *, max_nodes: int, max_depth: int) -> None:
        self.max_nodes = max_nodes
        self.max_depth = max_depth
        self.nodes = 0

    def _take(self, depth: int, label: str) -> None:
        if depth > self.max_depth:
            raise ArtifactDecodeError(
                f"artifact {label} exceeds the {self.max_depth}-level depth limit"
            )
        self.nodes += 1
        if self.nodes > self.max_nodes:
            raise ArtifactDecodeError(
                f"artifact exceeds the {self.max_nodes}-node decode limit"
            )

    @staticmethod
    def _tagged(value: object, label: str) -> tuple[str, list[object]]:
        if type(value) is not list or not value or type(value[0]) is not str:
            raise ArtifactDecodeError(f"artifact {label} is not one tagged array")
        return value[0], value

    @staticmethod
    def _arity(value: list[object], expected: int, label: str) -> None:
        if len(value) != expected:
            raise ArtifactDecodeError(f"artifact {label} has the wrong arity")

    @staticmethod
    def _natural(value: object, label: str) -> int:
        if type(value) is not int or value < 0:
            raise ArtifactDecodeError(
                f"artifact {label} must be a non-negative exact integer"
            )
        return value

    def term(self, value: object, depth: int) -> Term:
        self._take(depth, "term")
        tag, node = self._tagged(value, "term")
        if tag == "var":
            self._arity(node, 2, "var")
            return Var(self._natural(node[1], "variable index"))
        if tag == "zero":
            self._arity(node, 1, "zero")
            return Zero()
        if tag == "succ":
            self._arity(node, 2, "succ")
            return Succ(self.term(node[1], depth + 1))
        if tag == "add":
            self._arity(node, 3, "add")
            return Add(
                self.term(node[1], depth + 1),
                self.term(node[2], depth + 1),
            )
        if tag == "mul":
            self._arity(node, 3, "mul")
            return Mul(
                self.term(node[1], depth + 1),
                self.term(node[2], depth + 1),
            )
        raise ArtifactDecodeError(f"artifact term has unknown tag {tag!r}")

    def formula(self, value: object, depth: int) -> Formula:
        self._take(depth, "formula")
        tag, node = self._tagged(value, "formula")
        if tag == "eq":
            self._arity(node, 3, "eq")
            return Eq(
                self.term(node[1], depth + 1),
                self.term(node[2], depth + 1),
            )
        if tag == "bot":
            self._arity(node, 1, "bot")
            return Bot()
        if tag == "imp":
            self._arity(node, 3, "imp")
            return Imp(
                self.formula(node[1], depth + 1),
                self.formula(node[2], depth + 1),
            )
        if tag == "and":
            self._arity(node, 3, "and")
            return And(
                self.formula(node[1], depth + 1),
                self.formula(node[2], depth + 1),
            )
        if tag == "or":
            self._arity(node, 3, "or")
            return Or(
                self.formula(node[1], depth + 1),
                self.formula(node[2], depth + 1),
            )
        if tag == "forall":
            self._arity(node, 2, "forall")
            return Forall(self.formula(node[1], depth + 1))
        if tag == "exists":
            self._arity(node, 2, "exists")
            return Exists(self.formula(node[1], depth + 1))
        raise ArtifactDecodeError(f"artifact formula has unknown tag {tag!r}")

    def proof(self, value: object, depth: int) -> Proof:
        self._take(depth, "proof")
        tag, node = self._tagged(value, "proof")
        if tag == "hyp":
            self._arity(node, 2, "hyp")
            return Hyp(self._natural(node[1], "hypothesis index"))
        if tag == "imp_intro":
            self._arity(node, 2, "imp_intro")
            return ImpIntro(self.proof(node[1], depth + 1))
        if tag == "imp_elim":
            self._arity(node, 3, "imp_elim")
            return ImpElim(
                self.proof(node[1], depth + 1),
                self.proof(node[2], depth + 1),
            )
        if tag == "cut":
            self._arity(node, 5, "cut")
            return Cut(
                self.formula(node[1], depth + 1),
                self.formula(node[2], depth + 1),
                self.proof(node[3], depth + 1),
                self.proof(node[4], depth + 1),
            )
        if tag == "and_intro":
            self._arity(node, 3, "and_intro")
            return AndIntro(
                self.proof(node[1], depth + 1),
                self.proof(node[2], depth + 1),
            )
        if tag == "and_elim_l":
            self._arity(node, 2, "and_elim_l")
            return AndElimL(self.proof(node[1], depth + 1))
        if tag == "and_elim_r":
            self._arity(node, 2, "and_elim_r")
            return AndElimR(self.proof(node[1], depth + 1))
        if tag == "or_intro_l":
            self._arity(node, 2, "or_intro_l")
            return OrIntroL(self.proof(node[1], depth + 1))
        if tag == "or_intro_r":
            self._arity(node, 2, "or_intro_r")
            return OrIntroR(self.proof(node[1], depth + 1))
        if tag == "or_elim":
            self._arity(node, 4, "or_elim")
            return OrElim(
                self.proof(node[1], depth + 1),
                self.proof(node[2], depth + 1),
                self.proof(node[3], depth + 1),
            )
        if tag == "bot_elim":
            self._arity(node, 2, "bot_elim")
            return BotElim(self.proof(node[1], depth + 1))
        if tag == "forall_intro":
            self._arity(node, 2, "forall_intro")
            return ForallIntro(self.proof(node[1], depth + 1))
        if tag == "forall_elim":
            self._arity(node, 3, "forall_elim")
            return ForallElim(
                self.proof(node[1], depth + 1),
                self.term(node[2], depth + 1),
            )
        if tag == "exists_intro":
            self._arity(node, 3, "exists_intro")
            return ExistsIntro(
                self.term(node[1], depth + 1),
                self.proof(node[2], depth + 1),
            )
        if tag == "exists_elim":
            self._arity(node, 3, "exists_elim")
            return ExistsElim(
                self.proof(node[1], depth + 1),
                self.proof(node[2], depth + 1),
            )
        if tag == "eq_refl":
            self._arity(node, 2, "eq_refl")
            return EqRefl(self.term(node[1], depth + 1))
        if tag == "eq_sym":
            self._arity(node, 2, "eq_sym")
            return EqSym(self.proof(node[1], depth + 1))
        if tag == "eq_trans":
            self._arity(node, 3, "eq_trans")
            return EqTrans(
                self.proof(node[1], depth + 1),
                self.proof(node[2], depth + 1),
            )
        if tag == "cong_s":
            self._arity(node, 2, "cong_s")
            return CongS(self.proof(node[1], depth + 1))
        if tag == "cong_add":
            self._arity(node, 3, "cong_add")
            return CongAdd(
                self.proof(node[1], depth + 1),
                self.proof(node[2], depth + 1),
            )
        if tag == "cong_mul":
            self._arity(node, 3, "cong_mul")
            return CongMul(
                self.proof(node[1], depth + 1),
                self.proof(node[2], depth + 1),
            )
        if tag == "eq_subst":
            self._arity(node, 4, "eq_subst")
            return EqSubst(
                self.formula(node[1], depth + 1),
                self.proof(node[2], depth + 1),
                self.proof(node[3], depth + 1),
            )
        if tag == "dne":
            self._arity(node, 2, "dne")
            return DNE(self.formula(node[1], depth + 1))
        if tag == "axiom":
            self._arity(node, 2, "axiom")
            if type(node[1]) is not str or node[1] not in {
                "PA1",
                "PA2",
                "PA3",
                "PA4",
                "PA5",
                "PA6",
            }:
                raise ArtifactDecodeError("artifact axiom name is not PA1 through PA6")
            return Axiom(node[1])
        if tag == "ind":
            self._arity(node, 4, "ind")
            return Ind(
                self.formula(node[1], depth + 1),
                self.proof(node[2], depth + 1),
                self.proof(node[3], depth + 1),
            )
        raise ArtifactDecodeError(f"artifact proof has unknown tag {tag!r}")


def _positive_decode_limit(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{label} must be a positive exact integer")
    return value


def decode_artifact(
    artifact: bytes,
    *,
    max_bytes: int = MAX_DECODE_ARTIFACT_BYTES,
    max_nodes: int = MAX_DECODE_NODES,
    max_depth: int = MAX_DECODE_DEPTH,
) -> tuple[int, Formula, Proof]:
    """Decode one bounded canonical artifact into inert kernel syntax.

    Decoding never checks the proof.  Sound callers must bind ``target`` to an
    independently committed original goal and call
    :func:`peano_lab.kernel.checker.check` with the intended logic mode.
    ``max_*`` values are availability limits rather than logical axioms.
    """

    byte_limit = _positive_decode_limit(max_bytes, "artifact byte limit")
    node_limit = _positive_decode_limit(max_nodes, "artifact node limit")
    depth_limit = _positive_decode_limit(max_depth, "artifact depth limit")
    if type(artifact) is not bytes or not artifact or len(artifact) > byte_limit:
        raise ArtifactDecodeError(
            f"artifact must be nonempty exact bytes within the {byte_limit}-byte limit"
        )
    if not artifact.endswith(b"\n") or artifact.endswith(b"\n\n"):
        raise ArtifactDecodeError("canonical artifact must end in exactly one LF")
    try:
        parsed = json.loads(
            artifact[:-1].decode("utf-8"),
            parse_int=_parse_decoded_integer,
            parse_float=_reject_decoded_float,
            parse_constant=_reject_decoded_constant,
        )
    except ArtifactDecodeError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise ArtifactDecodeError(f"artifact is not bounded strict JSON: {exc}") from None
    if (
        type(parsed) is not list
        or len(parsed) != 4
        or parsed[0] != "peano-lab-v2"
    ):
        raise ArtifactDecodeError("artifact envelope is malformed")
    fuel = _Decoder._natural(parsed[1], "fuel")
    decoder = _Decoder(max_nodes=node_limit, max_depth=depth_limit)
    target = decoder.formula(parsed[2], 1)
    proof = decoder.proof(parsed[3], 1)
    try:
        canonical = encode_artifact_bounded(
            fuel,
            target,
            proof,
            max_bytes=len(artifact),
        )
    except (ArtifactLimitError, TypeError, ValueError, RecursionError) as exc:
        raise ArtifactDecodeError(f"decoded artifact cannot be re-encoded: {exc}") from None
    if canonical != artifact:
        raise ArtifactDecodeError("artifact is not in canonical peano-lab-v2 form")
    return fuel, target, proof


__all__ = [
    "ArtifactDecodeError",
    "ArtifactLimitError",
    "FORMAT_TAG",
    "MAX_DECODE_ARTIFACT_BYTES",
    "MAX_DECODE_DEPTH",
    "MAX_DECODE_INTEGER_DIGITS",
    "MAX_DECODE_NODES",
    "decode_artifact",
    "encode_artifact",
    "encode_artifact_bounded",
    "encode_formula",
    "encode_proof",
    "encode_term",
]
