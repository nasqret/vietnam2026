"""Bounded binary arithmetic certificates, not a trusted integer oracle.

Numbers are ordinary PA double-and-add terms, including small numbers. Each
operation generates equality proofs with PA3–PA6 and regenerated semiring
laws; local Cuts preserve recursive results without unary evaluation. The
unchanged kernel checks the original target before a canonical bundle returns.
Run proof-producing APIs inside the existing single-worker supervisor.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "peano-lab/py"))

from peano_lab.engine.proof_reduction import _shift_hypotheses
from peano_lab.kernel.formulas import Eq, Formula
from peano_lab.kernel.proofs import (
    Axiom, CongAdd, CongMul, CongS, Cut, EqRefl, EqSym, EqTrans,
    ExistsElim, ForallElim, Hyp, ImpIntro, OrElim, Proof,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Term, Zero
from peano_lab.library.proof_bundle import (
    BundleLimits, BundleNode, ProofBundle, check_proof_bundle, encode_proof_bundle,
)

ZERO = Zero()
ONE = Succ(ZERO)
TWO = Succ(ONE)
LAW_NAMES = ("zero_add", "add_succ_left", "mul_zero_left", "mul_one",
             "mul_add", "mul_assoc", "mul_comm")


class BinaryCertificateError(ValueError):
    pass


@dataclass(frozen=True)
class BinaryLimits:
    max_value_bits: int = 128
    max_input_nodes: int = 2048
    max_proof_nodes: int = 100000
    max_depth: int = 256
    max_payload_bytes: int = 8 * 1024**2

    def __post_init__(self):
        ceilings = (128, 2048, 100000, 256, 8 * 1024**2)
        for field, ceiling in zip(fields(self), ceilings):
            value = getattr(self, field.name)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise BinaryCertificateError("invalid or widened binary pilot limit")


@dataclass(frozen=True)
class BinaryCertificate:
    formula: Eq
    certificate: Proof
    bundle: ProofBundle
    payload: str
    value: int
    proof_nodes: int
    proof_depth: int
    seconds: float

    @property
    def payload_sha256(self):
        return sha256(self.payload.encode()).hexdigest()


def binary_term(value: int):
    """Canonical *explicit binary* term, not the historical decimal parser AST."""
    if type(value) is not int or value < 0 or value.bit_length() > 128:
        raise BinaryCertificateError("expected a natural of at most128 bits")
    return _binary_term(value)


@lru_cache(maxsize=2048)
def _binary_term(value):
    if value == 0:
        return ZERO
    if value == 1:
        return ONE
    doubled = Mul(TWO, _binary_term(value // 2))
    return Succ(doubled) if value & 1 else doubled


def binary_power_term(base: int, exponent: int):
    """Actual finite multiplication expression; no unproved Pow witness."""
    binary_term(base)
    if type(exponent) is not int or not 0 <= exponent <= 128:
        raise BinaryCertificateError("invalid fixed exponent")
    if (base > 1 and exponent * (base.bit_length() - 1) >= 128
            or pow(base, exponent).bit_length() > 128):
        raise BinaryCertificateError("fixed power exceeds128 bits")
    result = ONE
    factor = binary_term(base)
    while exponent:
        if exponent & 1:
            result = Mul(result, factor)
        exponent //= 2
        if exponent:
            factor = Mul(factor, factor)
    return result


def _instance(proof, *terms):
    for term in terms:
        proof = ForallElim(proof, term)
    return proof


def _chain(*proofs):
    if len(proofs) == 1:
        return proofs[0]
    middle = len(proofs) // 2
    return EqTrans(_chain(*proofs[:middle]), _chain(*proofs[middle:]))


def _replace_marker(proof, marker, depth=0):
    # Only builder-produced ordinary nodes enter here. Engine LocalHave and
    # LocalSuffices are never emitted or substituted by this generator.
    if type(proof) is Hyp:
        return Hyp(depth) if proof.index == marker else proof
    changes = {}
    for field in fields(proof):
        child = getattr(proof, field.name)
        if isinstance(child, Proof):
            binds = ((type(proof) in (Cut, ImpIntro, ExistsElim) and field.name == "body")
                     or (type(proof) is OrElim and field.name in ("left_case", "right_case")))
            changes[field.name] = _replace_marker(child, marker, depth + int(binds))
    return replace(proof, **changes) if changes else proof


class _Builder:
    def __init__(self, limits):
        self.limits = limits
        self.memo = {}
        self.marker = -1
        self.copy_visits = 0

    def law(self, name, *terms):
        return _instance(Hyp(LAW_NAMES.index(name)), *terms)

    def pa(self, name, *terms):
        return _instance(Axiom(name), *terms)

    def share(self, proposition, lemma, conclusion, continuation):
        marker = self.marker
        self.marker -= 1
        body = continuation(Hyp(marker))
        # Both transformations below copy a tree, even when its Python inputs
        # share objects. Reserve their full occurrence count BEFORE either
        # traversal allocates. A final certificate-size check alone is too late.
        count, _ = _proof_metrics(body, self.limits)
        required = 2 * count
        if self.copy_visits + required > self.limits.max_proof_nodes:
            raise BinaryCertificateError("binary construction copy-work budget exceeded; no certificate")
        self.copy_visits += required
        body = _replace_marker(_shift_hypotheses(body, 1), marker)
        return Cut(proposition, conclusion, lemma, body)

    def add_two(self, term):
        return _chain(self.pa("PA4", term, ONE),
                      CongS(self.pa("PA4", term, ZERO)),
                      CongS(CongS(self.pa("PA3", term))))

    def inc(self, n):
        key = ("inc", n)
        if key in self.memo:
            return self.memo[key]
        a, z = binary_term(n), binary_term(n + 1)
        if n == 0 or n > 1 and not n & 1:
            result = EqRefl(z)
        elif n == 1:
            result = EqSym(self.law("mul_one", TWO))
        else:
            half = n // 2
            h = binary_term(half)
            result = self.share(Eq(Succ(h), binary_term(half + 1)), self.inc(half), Eq(Succ(a), z),
                lambda ref: _chain(EqSym(self.add_two(Mul(TWO, h))),
                                   EqSym(self.pa("PA6", TWO, h)), CongMul(EqRefl(TWO), ref)))
        self.memo[key] = result
        return result

    def add(self, a, b):
        key = ("add", a, b)
        if key in self.memo:
            return self.memo[key]
        left, right, result_term = binary_term(a), binary_term(b), binary_term(a + b)
        goal = Eq(Add(left, right), result_term)
        if b == 0:
            result = self.pa("PA3", left)
        elif a == 0:
            result = self.law("zero_add", right)
        elif b & 1:
            previous = binary_term(b - 1)
            finish = self.inc(a + b - 1)
            result = self.share(Eq(Add(left, previous), binary_term(a + b - 1)), self.add(a, b - 1), goal,
                lambda ref: _chain(self.pa("PA4", left, previous), CongS(ref), finish))
        elif a & 1:
            previous = binary_term(a - 1)
            finish = self.inc(a + b - 1)
            result = self.share(Eq(Add(previous, right), binary_term(a + b - 1)), self.add(a - 1, b), goal,
                lambda ref: _chain(self.law("add_succ_left", previous, right), CongS(ref), finish))
        else:
            x, y = binary_term(a // 2), binary_term(b // 2)
            result = self.share(Eq(Add(x, y), binary_term((a + b) // 2)), self.add(a // 2, b // 2), goal,
                lambda ref: _chain(EqSym(self.law("mul_add", TWO, x, y)), CongMul(EqRefl(TWO), ref)))
        self.memo[key] = result
        return result

    def mul(self, a, b):
        key = ("mul", a, b)
        if key in self.memo:
            return self.memo[key]
        left, right = binary_term(a), binary_term(b)
        goal = Eq(Mul(left, right), binary_term(a * b))
        if b == 0:
            result = self.pa("PA5", left)
        elif a == 0:
            result = self.law("mul_zero_left", right)
        elif b == 1:
            result = self.law("mul_one", left)
        elif a.bit_count() < b.bit_count():
            # Recurse on the operand requiring fewer odd/addition steps. The
            # strict comparison prevents a commutation cycle, and the swap is
            # justified by the checked law rather than host arithmetic.
            result = self.share(Eq(Mul(right, left), binary_term(a * b)),
                self.mul(b, a), goal,
                lambda ref: EqTrans(self.law("mul_comm", left, right), ref))
        elif b & 1:
            previous = binary_term(b - 1)
            finish = self.add(a * (b - 1), a)
            result = self.share(Eq(Mul(left, previous), binary_term(a * (b - 1))), self.mul(a, b - 1), goal,
                lambda ref: _chain(self.pa("PA6", left, previous), CongAdd(ref, EqRefl(left)), finish))
        else:
            half = binary_term(b // 2)
            result = self.share(Eq(Mul(left, half), binary_term(a * (b // 2))), self.mul(a, b // 2), goal,
                lambda ref: _chain(EqSym(self.law("mul_assoc", left, TWO, half)),
                    CongMul(self.law("mul_comm", left, TWO), EqRefl(half)),
                    self.law("mul_assoc", TWO, left, half), CongMul(EqRefl(TWO), ref)))
        self.memo[key] = result
        return result

    def normalize(self, term, values):
        value = values[id(term)]
        canonical = binary_term(value)
        if term == canonical:
            return EqRefl(canonical)
        key = ("normalize", id(term))
        if key in self.memo:
            return self.memo[key]
        if type(term) is Succ:
            child = values[id(term.term)]
            finish = self.inc(child)
            result = self.share(Eq(term.term, binary_term(child)), self.normalize(term.term, values), Eq(term, canonical),
                lambda ref: EqTrans(CongS(ref), finish))
        else:
            a, b = values[id(term.left)], values[id(term.right)]
            same_operand = term.left == term.right
            lp = self.normalize(term.left, values)
            rp = None if same_operand else self.normalize(term.right, values)
            operation = self.add(a, b) if type(term) is Add else self.mul(a, b)
            constructor = CongAdd if type(term) is Add else CongMul
            result = self.share(Eq(term.left, binary_term(a)), lp, Eq(term, canonical),
                lambda lref: EqTrans(constructor(lref, lref if same_operand else rp), operation))
        self.memo[key] = result
        return result


def _values(equation, limits):
    values = {}
    count = 0
    def visit(term, depth=1):
        nonlocal count
        count += 1
        if count > limits.max_input_nodes or depth > limits.max_depth:
            raise BinaryCertificateError("input structure exceeds binary pilot limit")
        if type(term) is Zero:
            value = 0
        elif type(term) is Succ:
            value = visit(term.term, depth + 1) + 1
        elif type(term) in (Add, Mul):
            a, b = visit(term.left, depth + 1), visit(term.right, depth + 1)
            value = a + b if type(term) is Add else a * b
        else:
            raise BinaryCertificateError("expected exact closed PA arithmetic terms")
        if value.bit_length() > limits.max_value_bits:
            raise BinaryCertificateError("arithmetic exceeds binary pilot value bits")
        values[id(term)] = value
        return value
    left, right = visit(equation.left), visit(equation.right)
    if left != right:
        raise BinaryCertificateError("closed equality is false")
    return values, left


def _proof_metrics(proof, limits):
    stack = [(proof, 1)]
    count = deepest = 0
    while stack:
        node, depth = stack.pop()
        count += 1
        deepest = max(deepest, depth)
        if count > limits.max_proof_nodes or depth > limits.max_depth:
            raise BinaryCertificateError("generated proof exceeds original structural bounds")
        for field in fields(node):
            child = getattr(node, field.name)
            if isinstance(child, Proof):
                stack.append((child, depth + 1))
    return count, deepest


def _serialization_preflight(proof, target, limits):
    """Cap expanded syntax BEFORE a codec constructs repeated nested arrays.

    The current ordinary codec does not serialize object sharing. Sixty-four
    bytes per ordinary constructor is a deliberately conservative pilot
    allowance, not a claim that a compact proof DAG codec has been implemented.
    The existing codec still enforces its exact byte limit afterward.
    """
    pending = [proof, target, target]
    allowance = 256  # single-node canonical envelope and its scalar metadata
    while pending:
        node = pending.pop()
        allowance += 64
        if allowance > limits.max_payload_bytes:
            raise BinaryCertificateError("expanded binary syntax exceeds safe serialization budget; no certificate")
        for field in fields(node):
            child = getattr(node, field.name)
            if isinstance(child, (Proof, Formula, Term)):
                pending.append(child)
            elif type(child) is str:
                allowance += len(child.encode("utf-8"))
            elif type(child) is int:
                allowance += max(1, child.bit_length())
        if allowance > limits.max_payload_bytes:
            raise BinaryCertificateError("expanded binary syntax exceeds safe serialization budget; no certificate")


def prove_binary_equation(equation, basis, *, limits=BinaryLimits()):
    """Return actual ordinary proof and canonical bundle, after original HA checking."""
    if type(equation) is not Eq or type(limits) is not BinaryLimits:
        raise BinaryCertificateError("expected exact Eq and BinaryLimits")
    started = time.monotonic()
    values, value = _values(equation, limits)
    builder = _Builder(limits)
    left, right = builder.normalize(equation.left, values), builder.normalize(equation.right, values)
    proof = builder.share(Eq(equation.left, binary_term(value)), left, equation,
                         lambda ref: EqTrans(ref, EqSym(right)))
    for name in LAW_NAMES:
        law = basis.get(name)
        proof = Cut(law.formula, equation, law.certificate, proof)
    count, depth = _proof_metrics(proof, limits)
    _serialization_preflight(proof, equation, limits)
    bundle = ProofBundle((BundleNode(0, equation, (), proof),), 0)
    bundle_limits = BundleLimits(max_body_nodes=limits.max_proof_nodes,
        max_total_body_nodes=limits.max_proof_nodes, max_body_depth=limits.max_depth,
        max_formula_depth=limits.max_depth, max_payload_bytes=limits.max_payload_bytes)
    check_proof_bundle(bundle, equation, limits=bundle_limits)
    payload = encode_proof_bundle(bundle, equation, limits=bundle_limits)
    return BinaryCertificate(equation, proof, bundle, payload, value, count, depth, time.monotonic() - started)


def prove_add(a, b, basis, *, limits=BinaryLimits()):
    return prove_binary_equation(Eq(Add(binary_term(a), binary_term(b)), binary_term(a + b)), basis, limits=limits)


def prove_mul(a, b, basis, *, limits=BinaryLimits()):
    return prove_binary_equation(Eq(Mul(binary_term(a), binary_term(b)), binary_term(a * b)), basis, limits=limits)


def p10_difference_equation(right_exponent=88):
    """Exact product plus an explicit nonnegative gap; false P10 mutation rejected."""
    if right_exponent not in (85, 88):
        raise BinaryCertificateError("unsupported P10 instance")
    product = 2**55 * 3**11 * 7**5
    right = 2**right_exponent
    if product > right:
        raise BinaryCertificateError("P10 inequality is false")
    term = Mul(Mul(binary_power_term(2, 55), binary_power_term(3, 11)), binary_power_term(7, 5))
    return Eq(Add(term, binary_term(right - product)), binary_power_term(2, right_exponent))
