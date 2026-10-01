"""Bounded ordinary HA arithmetic, shared by topological proof-bundle nodes.

No trusted arithmetic evaluation, registry import, new axiom, proof reduction,
or whole-body Cut substitution is used. Integer evaluation chooses a proposed
derivation; the unchanged kernel replays every dependency-curried ordinary body
from canonical bytes. Execute public proof producers in the root-owned worker.

The 4096 local-node ceiling is the existing bundle default. Unlike the previous
single-body adapter, one arithmetic operation occupies one independently checked
node. This changes packaging, not the HA kernel or its inference rules.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "peano-lab/py"))

from peano_lab.kernel.formulas import Eq, Exists, Formula, parse_formula_with_names
from peano_lab.kernel.proofs import (
    Axiom, CongAdd, CongMul, CongS, EqRefl, EqSym, EqTrans,
    ExistsIntro, ForallElim, Hyp, ImpIntro, Proof,
)
from peano_lab.kernel.subst import subst_formula
from peano_lab.kernel.terms import Add, Mul, Succ, Term, Zero
from peano_lab.library.proof_bundle import (
    BundleLimits, BundleNode, ProofBundle, check_encoded_proof_bundle,
    encode_formula, encode_proof, encode_proof_bundle,
)

ZERO, ONE = Zero(), Succ(Zero())
TWO = Succ(ONE)
P10_TARGET_SHA256 = "80dd8b78cf3a77c81e05f935df83684e6c758c2614521a877530097572cb61ee"
P10_SUBLEAF_SHA256 = "a3f3a091f4bd2cfb14c494d51075d231c00a0f940973c357d04753130f167323"
# These source/literal pins are from the validated-pilot-v2 report and contracts.
# That edition recorded P10 as unelaborated: the two AST pins above are NEW.
V2_REPORT_SHA256 = "b18b2384970cbf0c9b70865995245689768b4a538adafc97484e0ddfb55e0f97"
SOURCE_PINS = {
    "scripts/sqrt2_power_native.py": "9b51adc2699bf3c83c74749b9fc4723a8a1b8e234cef6f521a3f309fe646cc73",
    "peano-lab/py/peano_lab/library/theorems.py": "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
}
LAW_PINS = {
    "zero_add": "a60ce5f8481e1ca36b7f67c945370d405115cda727bdf29fb06e1be57458aef3",
    "add_succ_left": "dd447ec544541bd02f1be2fe72e316bda715120e5abeebfba74af98c11858071",
    "mul_zero_left": "bc9747ec6d522ffe76b7ff4ca024b8cd2e30ce82d474cd6901dc8045da4cdf49",
    "mul_one": "71b277c52d72b1b3b4b161567b6bf03e9020d0523585f3d952974f4f579dc5ea",
    "mul_add": "515b74ebcffe7f7cff1861d440fae3e50f44a49cfd65bf3ce0889e72e5991c99",
    "mul_assoc": "02cba3297fd04616267d496eed53360b9eeca6d892a5f1c117f0a50f23653814",
    "mul_comm": "6844833d88b702ddda39f8c0826d11e3859ed234bf55136fef5bb79120a7fb8c",
}


class BinaryDAGError(ValueError):
    """Fail-closed statement, provenance, or construction-budget failure."""


@dataclass(frozen=True)
class BinaryDAGLimits:
    max_value_bits: int = 128
    max_input_nodes: int = 2048
    max_nodes: int = 4096
    max_total_body_nodes: int = 200000
    max_depth: int = 256
    max_payload_bytes: int = 8 * 1024**2

    def __post_init__(self):
        for field, ceiling in zip(fields(self), (128, 2048, 4096, 200000, 256, 8 * 1024**2)):
            value = getattr(self, field.name)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise BinaryDAGError("invalid or widened binary DAG limit")

    def bundle_limits(self):
        return BundleLimits(max_nodes=self.max_nodes,
            max_body_nodes=self.max_total_body_nodes,
            max_total_body_nodes=self.max_total_body_nodes,
            max_body_depth=self.max_depth, max_formula_depth=self.max_depth,
            max_payload_bytes=self.max_payload_bytes)


@dataclass(frozen=True)
class BinaryDAGCertificate:
    target: Formula
    bundle: ProofBundle
    payload: str
    receipt: object
    max_proof_depth: int
    basis_names: tuple[str, ...]
    subleaf_node: int | None = None

    @property
    def payload_sha256(self):
        return sha256(self.payload.encode()).hexdigest()

    @property
    def target_ast_sha256(self):
        return formula_sha256(self.target)


def _json(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def formula_sha256(formula):
    return sha256(_json(encode_formula(formula)).encode()).hexdigest()


def binary_term(value):
    if type(value) is not int or value < 0 or value.bit_length() > 128:
        raise BinaryDAGError("expected a natural of at most 128 bits")
    return _binary_term(value)


@lru_cache(maxsize=2048)
def _binary_term(value):
    if value == 0:
        return ZERO
    if value == 1:
        return ONE
    doubled = Mul(TWO, _binary_term(value // 2))
    return Succ(doubled) if value & 1 else doubled


def _instance(proof, *terms):
    for term in terms:
        proof = ForallElim(proof, term)
    return proof


def _chain(*proofs):
    if len(proofs) == 1:
        return proofs[0]
    middle = len(proofs) // 2
    return EqTrans(_chain(*proofs[:middle]), _chain(*proofs[middle:]))


def _pa(name, *terms):
    return _instance(Axiom(name), *terms)


def _values(equation, limits):
    if type(equation) is not Eq or type(limits) is not BinaryDAGLimits:
        raise BinaryDAGError("expected an exact closed Eq and BinaryDAGLimits")
    values = {}
    count = 0
    def visit(term, depth=1):
        nonlocal count
        count += 1
        if count > limits.max_input_nodes or depth > limits.max_depth:
            raise BinaryDAGError("input structure exceeds original pilot bounds")
        if type(term) is Zero:
            value = 0
        elif type(term) is Succ:
            value = visit(term.term, depth + 1) + 1
        elif type(term) in (Add, Mul):
            a, b = visit(term.left, depth + 1), visit(term.right, depth + 1)
            value = a + b if type(term) is Add else a * b
        else:
            raise BinaryDAGError("expected exact closed PA arithmetic terms")
        if value.bit_length() > limits.max_value_bits:
            raise BinaryDAGError("input arithmetic exceeds 128-bit pilot bound")
        values[id(term)] = value
        return value
    if visit(equation.left) != visit(equation.right):
        raise BinaryDAGError("closed arithmetic equality is false")
    return values


def verify_basis_sources():
    actual = {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCE_PINS}
    if actual != SOURCE_PINS:
        raise BinaryDAGError("regenerated Basis sources differ from frozen v2 pins")
    return actual


def _body_metrics(proof, limits):
    pending = [(proof, 1)]
    count = deepest = 0
    while pending:
        value, depth = pending.pop()
        count += 1
        deepest = max(deepest, depth)
        if count > limits.max_total_body_nodes or depth > limits.max_depth:
            raise BinaryDAGError("ordinary body exceeds original structural bounds")
        for field in fields(value):
            child = getattr(value, field.name)
            if isinstance(child, Proof):
                pending.append((child, depth + 1))
    return count, deepest


def _row_preflight(target, body, limits):
    # A small per-operation row is encoded independently. Check its fully
    # expanded syntax before allocating the codec's nested array representation.
    pending = [target, body]
    count = 0
    while pending:
        value = pending.pop()
        count += 1
        if 64 * count > limits.max_payload_bytes:
            raise BinaryDAGError("one local row exceeds safe serialization budget")
        for field in fields(value):
            child = getattr(value, field.name)
            if isinstance(child, (Formula, Proof, Term)):
                pending.append(child)


class _Builder:
    """Untrusted deterministic producer; only finish() returns checked evidence."""

    def __init__(self, basis, limits):
        self.basis, self.limits = basis, limits
        self.nodes = []
        self.formulas = {}
        self.memo = {}
        self.laws = {}
        self.total_body_nodes = 0
        self.max_proof_depth = 0
        self.encoded_bytes = 128

    def emit(self, target, dependencies, make_body):
        if target in self.formulas:
            return self.formulas[target]
        if len(self.nodes) >= self.limits.max_nodes:
            raise BinaryDAGError("local arithmetic node budget exhausted")
        dependencies = tuple(dict.fromkeys(dependencies))
        if len(dependencies) > 256 or any(type(d) is not int or not 0 <= d < len(self.nodes) for d in dependencies):
            raise BinaryDAGError("non-topological arithmetic dependency")
        refs = {node_id: Hyp(len(dependencies) - index - 1)
                for index, node_id in enumerate(dependencies)}
        body = make_body(refs.__getitem__)
        for _ in dependencies:
            body = ImpIntro(body)
        count, depth = _body_metrics(body, self.limits)
        if self.total_body_nodes + count > self.limits.max_total_body_nodes:
            raise BinaryDAGError("aggregate ordinary proof-node budget exhausted")
        _row_preflight(target, body, self.limits)
        row_bytes = len(_json([8 * count + 16, encode_formula(target), list(dependencies), encode_proof(body)]).encode()) + 1
        if self.encoded_bytes + row_bytes > self.limits.max_payload_bytes:
            raise BinaryDAGError("aggregate canonical payload budget exhausted")
        node_id = len(self.nodes)
        self.nodes.append(BundleNode(node_id, target, dependencies, body))
        self.formulas[target] = node_id
        self.total_body_nodes += count
        self.max_proof_depth = max(self.max_proof_depth, depth)
        self.encoded_bytes += row_bytes
        return node_id

    def law(self, name):
        if name not in LAW_PINS:
            raise BinaryDAGError("law outside the frozen arithmetic allowlist")
        if name not in self.laws:
            row = self.basis.get(name)
            if (row.source_sha256 != SOURCE_PINS["peano-lab/py/peano_lab/library/theorems.py"]
                    or row.literal_spec_sha256 != LAW_PINS[name]):
                raise BinaryDAGError("arithmetic law differs from its v2 literal pin")
            self.laws[name] = self.emit(row.formula, (), lambda _: row.certificate)
        return self.laws[name]

    def inc(self, n):
        key = ("inc", n)
        if key in self.memo:
            return self.memo[key]
        a, z = binary_term(n), binary_term(n + 1)
        target = Eq(Succ(a), z)
        if n == 0 or n > 1 and not n & 1:
            result = self.emit(target, (), lambda _: EqRefl(z))
        elif n == 1:
            law = self.law("mul_one")
            result = self.emit(target, (law,), lambda ref: EqSym(_instance(ref(law), TWO)))
        else:
            h = binary_term(n // 2)
            child = self.inc(n // 2)
            t = Mul(TWO, h)
            add_two = _chain(_pa("PA4", t, ONE), CongS(_pa("PA4", t, ZERO)), CongS(CongS(_pa("PA3", t))))
            result = self.emit(target, (child,), lambda ref: _chain(
                EqSym(add_two), EqSym(_pa("PA6", TWO, h)), CongMul(EqRefl(TWO), ref(child))))
        self.memo[key] = result
        return result

    def add(self, a, b):
        key = ("add", a, b)
        if key in self.memo:
            return self.memo[key]
        left, right, z = binary_term(a), binary_term(b), binary_term(a + b)
        target = Eq(Add(left, right), z)
        if b == 0:
            result = self.emit(target, (), lambda _: _pa("PA3", left))
        elif a == 0:
            law = self.law("zero_add")
            result = self.emit(target, (law,), lambda ref: _instance(ref(law), right))
        elif b & 1:
            child, finish = self.add(a, b - 1), self.inc(a + b - 1)
            result = self.emit(target, (child, finish), lambda ref: _chain(
                _pa("PA4", left, binary_term(b - 1)), CongS(ref(child)), ref(finish)))
        elif a & 1:
            child, finish, law = self.add(a - 1, b), self.inc(a + b - 1), self.law("add_succ_left")
            result = self.emit(target, (child, finish, law), lambda ref: _chain(
                _instance(ref(law), binary_term(a - 1), right), CongS(ref(child)), ref(finish)))
        else:
            child, law = self.add(a // 2, b // 2), self.law("mul_add")
            result = self.emit(target, (child, law), lambda ref: _chain(
                EqSym(_instance(ref(law), TWO, binary_term(a // 2), binary_term(b // 2))),
                CongMul(EqRefl(TWO), ref(child))))
        self.memo[key] = result
        return result

    def mul(self, a, b):
        key = ("mul", a, b)
        if key in self.memo:
            return self.memo[key]
        left, right, z = binary_term(a), binary_term(b), binary_term(a * b)
        target = Eq(Mul(left, right), z)
        if b == 0:
            result = self.emit(target, (), lambda _: _pa("PA5", left))
        elif a == 0:
            law = self.law("mul_zero_left")
            result = self.emit(target, (law,), lambda ref: _instance(ref(law), right))
        elif b == 1:
            law = self.law("mul_one")
            result = self.emit(target, (law,), lambda ref: _instance(ref(law), left))
        elif a.bit_count() < b.bit_count():
            child, law = self.mul(b, a), self.law("mul_comm")
            result = self.emit(target, (child, law), lambda ref: EqTrans(_instance(ref(law), left, right), ref(child)))
        elif b & 1:
            child, finish = self.mul(a, b - 1), self.add(a * (b - 1), a)
            result = self.emit(target, (child, finish), lambda ref: _chain(
                _pa("PA6", left, binary_term(b - 1)), CongAdd(ref(child), EqRefl(left)), ref(finish)))
        else:
            child, assoc, comm = self.mul(a, b // 2), self.law("mul_assoc"), self.law("mul_comm")
            half = binary_term(b // 2)
            result = self.emit(target, (child, assoc, comm), lambda ref: _chain(
                EqSym(_instance(ref(assoc), left, TWO, half)),
                CongMul(_instance(ref(comm), left, TWO), EqRefl(half)),
                _instance(ref(assoc), TWO, left, half), CongMul(EqRefl(TWO), ref(child))))
        self.memo[key] = result
        return result

    def normalize(self, term, values):
        key = ("normalize", term)
        if key in self.memo:
            return self.memo[key]
        n = values[id(term)]
        canonical = binary_term(n)
        target = Eq(term, canonical)
        if term == canonical:
            result = self.emit(target, (), lambda _: EqRefl(canonical))
        elif type(term) is Succ:
            child, finish = self.normalize(term.term, values), self.inc(values[id(term.term)])
            result = self.emit(target, (child, finish), lambda ref: EqTrans(CongS(ref(child)), ref(finish)))
        else:
            a, b = values[id(term.left)], values[id(term.right)]
            left, right = self.normalize(term.left, values), self.normalize(term.right, values)
            operation = self.add(a, b) if type(term) is Add else self.mul(a, b)
            congruence = CongAdd if type(term) is Add else CongMul
            result = self.emit(target, (left, right, operation), lambda ref: EqTrans(
                congruence(ref(left), ref(right)), ref(operation)))
        self.memo[key] = result
        return result

    def equality(self, equation, values):
        left, right = self.normalize(equation.left, values), self.normalize(equation.right, values)
        return self.emit(equation, (left, right), lambda ref: EqTrans(ref(left), EqSym(ref(right))))

    def finish(self, root, target, subleaf=None):
        reachable, pending = set(), [root]
        while pending:
            node_id = pending.pop()
            if node_id not in reachable:
                reachable.add(node_id)
                pending.extend(self.nodes[node_id].dependencies)
        order = sorted(reachable)
        remap = {old: new for new, old in enumerate(order)}
        bundle = ProofBundle(tuple(replace(self.nodes[old], node_id=remap[old],
            dependencies=tuple(remap[d] for d in self.nodes[old].dependencies)) for old in order), remap[root])
        if self.encoded_bytes + len(_json(encode_formula(target)).encode()) > self.limits.max_payload_bytes:
            raise BinaryDAGError("canonical envelope exceeds total payload budget")
        payload = encode_proof_bundle(bundle, target, limits=self.limits.bundle_limits())
        # Replay canonical bytes, not just in-memory producer objects. The
        # unchanged checker closes every curried body from the empty context.
        receipt = check_encoded_proof_bundle(payload, limits=self.limits.bundle_limits())
        if receipt.target != target:
            raise BinaryDAGError("canonical replay changed the exact caller target")
        verify_basis_sources()
        return BinaryDAGCertificate(target, bundle, payload, receipt, self.max_proof_depth,
            tuple(sorted(name for name, node_id in self.laws.items() if node_id in reachable)),
            None if subleaf is None else remap[subleaf])


def _basis(basis):
    verify_basis_sources()
    from sqrt2_power_native import Basis
    if basis is None:
        basis = Basis()
    if type(basis) is not Basis:
        raise BinaryDAGError("expected the frozen literal-replayed Basis")
    return basis


def prove_binary_equation(equation, basis=None, *, limits=BinaryDAGLimits()):
    """Return a same-byte HA-checked ordinary bundle for the EXACT supplied Eq."""
    values = _values(equation, limits)  # reject false/open targets before loading Basis
    builder = _Builder(_basis(basis), limits)
    root = builder.equality(equation, values)
    return builder.finish(root, equation)


def frozen_p10_targets():
    """Elaborate the original instance sources; reject even host-equal rewrites."""
    from sqrt2_power_pilot_instances import p10_instance
    sources = p10_instance()["sources"]
    formulas = []
    for source, identifier, digest in zip(sources,
            ("P10.full-closed-target", "P10.explicit-difference-subleaf"),
            (P10_TARGET_SHA256, P10_SUBLEAF_SHA256)):
        if source["id"] != identifier:
            raise BinaryDAGError("frozen P10 source order changed")
        formula, names = parse_formula_with_names(source["formula"])
        if names or formula_sha256(formula) != digest:
            raise BinaryDAGError("P10 original AST pin mismatch")
        formulas.append(formula)
    if len(sources) != 2 or len(formulas) != 2:
        raise BinaryDAGError("frozen P10 source set changed")
    target, subleaf = formulas
    if type(target) is not Exists or type(subleaf) is not Eq or type(subleaf.left) is not Add:
        raise BinaryDAGError("unexpected exact P10 existential shape")
    witness = subleaf.left.right
    if subst_formula(target.body, 0, witness) != subleaf:
        raise BinaryDAGError("explicit P10 witness does not instantiate the original target")
    return target, subleaf, witness


def prove_p10(basis=None, *, limits=BinaryDAGLimits()):
    """Close only the frozen P10 instance, NOT IR064 or full irrationality."""
    target, subleaf, witness = frozen_p10_targets()
    values = _values(subleaf, limits)
    builder = _Builder(_basis(basis), limits)
    arithmetic = builder.equality(subleaf, values)
    root = builder.emit(target, (arithmetic,), lambda ref: ExistsIntro(witness, ref(arithmetic)))
    return builder.finish(root, target, arithmetic)
