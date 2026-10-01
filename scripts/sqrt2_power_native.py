"""Small, deterministic HA proof producers for the irrationality pilot.

No full theorem registry import, solver trust, new axiom, or library admission.
Basic scripts are literal-extracted from their existing source and replayed.
Every output is an ordinary closed certificate, rechecked against its target.
Run expensive calls only inside the campaign's process supervisor.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "peano-lab/py"))

from peano_lab.engine.ring import RING_LAW_NAMES, RingLaw, prove_ring_equation
from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Eq, Forall, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import (
    AndIntro, CongAdd, CongMul, Cut, EqRefl, EqSym, EqTrans,
    ExistsElim, ExistsIntro, ForallElim, ForallIntro, Hyp, ImpElim, ImpIntro,
)
from peano_lab.kernel.terms import Add, Mul, Var
from peano_lab.library.proof_bundle import encode_formula

SOURCE = ROOT / "peano-lab/py/peano_lab/library/theorems.py"
BASIS_NAMES = frozenset(RING_LAW_NAMES) | {
    "add_succ_left", "mul_succ_left", "add_eq_zero_right", "mul_eq_zero", "mul_ne_zero",
}


def closed_formula(source):
    formula, free = parse_formula_with_names(source)
    if free:
        raise ValueError("free variables in a frozen pilot target: " + repr(free))
    return formula


@dataclass(frozen=True)
class BasicProof:
    formula: object
    certificate: object
    dependencies: tuple[str, ...]
    source_sha256: str
    literal_spec_sha256: str


class Basis:
    """Only a fixed small dependency-closed allowlist; no ambient theorem names."""

    def __init__(self):
        raw = SOURCE.read_bytes()
        self.source_sha256 = sha256(raw).hexdigest()
        self.specs = {}
        self.checked = {}
        module = ast.parse(raw, filename=str(SOURCE))
        declarations = [n for n in module.body if isinstance(n, ast.AnnAssign)
                        and isinstance(n.target, ast.Name) and n.target.id == "THEOREMS"]
        if len(declarations) != 1 or not isinstance(declarations[0].value, ast.Tuple):
            raise ValueError("the audited literal theorem table changed")
        for item in declarations[0].value.elts:
            if (not isinstance(item, ast.Call) or not isinstance(item.func, ast.Name)
                or item.func.id != "TheoremSpec" or item.keywords or len(item.args) != 5):
                raise ValueError("unexpected entry in the literal theorem table")
            name = ast.literal_eval(item.args[0])
            if name not in BASIS_NAMES:
                continue
            if name in self.specs:
                raise ValueError("duplicate basis name")
            values = tuple(ast.literal_eval(a) for a in item.args)
            if (not isinstance(values[1], str) or type(values[2]) is not tuple
                or type(values[3]) is not tuple or not all(type(x) is str for x in values[2] + values[3])):
                raise ValueError("nonliteral basis contract")
            self.specs[name] = values
        if set(self.specs) != BASIS_NAMES:
            raise ValueError("missing exact basic theorem")
        for values in self.specs.values():
            if not set(values[2]) <= BASIS_NAMES:
                raise ValueError("basis requires a non-allowlisted dependency")

    def get(self, name):
        if name not in BASIS_NAMES:
            raise ValueError("non-allowlisted basis request")
        if name in self.checked:
            return self.checked[name]
        _, source, dependencies, script, _ = self.specs[name]
        dep_proofs = [self.get(d) for d in dependencies]
        target = closed_formula(source)
        curried = target
        for dep in reversed(dep_proofs):
            curried = Imp(dep.formula, curried)
        state = start(curried)
        for dep in dependencies:
            state = apply_tactic(state, "intro", dep)
        for command in script:
            tactic, _, arguments = command.partition(" ")
            state = apply_tactic(state, tactic, arguments)
        certificate = checked_final(state, curried)
        for _ in dependencies:
            if type(certificate) is not ImpIntro:
                raise ValueError("dependency introduction is missing")
            certificate = certificate.body
        for dep in reversed(dep_proofs):
            certificate = Cut(dep.formula, target, dep.certificate, certificate)
        if not check((), certificate, target):
            raise ValueError("original HA kernel rejected a regenerated basis law")
        result = BasicProof(target, certificate, dependencies, self.source_sha256,
                            sha256(repr(self.specs[name]).encode()).hexdigest())
        self.checked[name] = result
        return result

    def laws(self):
        return tuple(RingLaw(n, self.get(n).formula, self.get(n).certificate) for n in RING_LAW_NAMES)

    def manifest(self):
        return [{"name": n, "source_sha256": row.source_sha256,
                 "literal_spec_sha256": row.literal_spec_sha256,
                 "formula_ast": encode_formula(row.formula),
                 "dependencies": list(row.dependencies), "ordinary_HA_checked": True,
                 "admission_claim": "none; regenerated existing arithmetic only"}
                for n, row in sorted(self.checked.items())]


def instantiate(proof, *terms):
    for term in terms:
        proof = ForallElim(proof, term)
    return proof


def strip_target(target):
    binders = 0
    while type(target) is Forall:
        binders += 1
        target = target.body
    premises = []
    while type(target) is Imp:
        premises.append(target.antecedent)
        target = target.consequent
    return binders, premises, target


def close_proof(proof, binders, premises):
    for _ in premises:
        proof = ImpIntro(proof)
    for _ in range(binders):
        proof = ForallIntro(proof)
    return proof


def ring(equation, basis):
    # Unchanged default limits. Exceeding them is a recorded decomposition need.
    return prove_ring_equation(equation, basis.laws()).certificate


def prove_p01(target, basis):
    """Full positive-denominator, signed-pair rational addition compatibility."""
    binders, premises, goal = strip_target(target)
    if binders != 12 or len(premises) != 6 or type(goal) is not And:
        raise ValueError("unexpected P01 shape")
    p, m, d, P, M, D, q, n, e, Q, N, E = [Var(i) for i in reversed(range(12))]
    equation = goal.right.right
    middle_left = Add(Mul(premises[-2].left, Mul(e, E)), Mul(premises[-1].left, Mul(d, D)))
    middle_right = Add(Mul(premises[-2].right, Mul(e, E)), Mul(premises[-1].right, Mul(d, D)))
    transport = CongAdd(CongMul(Hyp(1), EqRefl(Mul(e, E))),
                        CongMul(Hyp(0), EqRefl(Mul(d, D))))
    equality = EqTrans(ring(Eq(equation.left, middle_left), basis),
                       EqTrans(transport, ring(Eq(middle_right, equation.right), basis)))
    nonzero = basis.get("mul_ne_zero").certificate
    de = ImpElim(ImpElim(instantiate(nonzero, d, e), Hyp(5)), Hyp(4))
    DE = ImpElim(ImpElim(instantiate(nonzero, D, E), Hyp(3)), Hyp(2))
    return close_proof(AndIntro(de, AndIntro(DE, equality)), binders, premises)


def prove_p03_step(target, basis):
    binders, premises, equation = strip_target(target)
    x, y, X, Y, T = [Var(i) for i in reversed(range(5))]
    a = Add(Mul(y, premises[0].left), Mul(x, X))
    b = Add(Mul(y, premises[0].right), Mul(x, X))
    middle = CongAdd(CongMul(EqRefl(y), Hyp(0)), EqRefl(Mul(x, X)))
    return close_proof(EqTrans(ring(Eq(equation.left, a), basis),
        EqTrans(middle, ring(Eq(b, equation.right), basis))), binders, premises)


def prove_p05_step(target, basis):
    # Deterministic tactic replay substitutes only the stated coefficient values.
    state = start(target)
    for command in ("intro n", "intro a", "intro b", "intro ha", "intro hb", "rewrite ha", "rewrite hb"):
        name, _, args = command.partition(" ")
        state = apply_tactic(state, name, args)
    from peano_lab.engine.ring import ring_checked
    state = ring_checked(state, basis.laws())
    return checked_final(state, target)


def prove_transport(target, basis):
    """One explicit equality hypothesis, normalized conclusion: no SMT trust."""
    binders, premises, equation = strip_target(target)
    if len(premises) != 1 or type(premises[0]) is not Eq or type(equation) is not Eq:
        raise ValueError("unsupported equality transport")
    premise = premises[0]
    return close_proof(EqTrans(ring(Eq(equation.left, premise.left), basis),
        EqTrans(Hyp(0), ring(Eq(premise.right, equation.right), basis))), binders, premises)


def prove_mul_transport(target, basis, row):
    binders, premises, equation = strip_target(target)
    if len(premises) != 1 or type(premises[0]) is not Eq:
        raise ValueError("one explicit equality hypothesis required")
    premise = premises[0]
    factor = Var(row["factor_index"])
    left, right, proof = premise.left, premise.right, Hyp(0)
    if row["reverse_premise"]:
        left, right, proof = right, left, EqSym(proof)
    return close_proof(EqTrans(ring(Eq(equation.left, Mul(left, factor)), basis),
        EqTrans(CongMul(proof, EqRefl(factor)), ring(Eq(Mul(right, factor), equation.right), basis))), binders, premises)


def prove_exists_transport(target, basis):
    binders, premises, goal = strip_target(target)
    # Under ExistsElim, its witness and equality are both newest (index zero).
    equation, given = goal.body, premises[0].body
    body = EqTrans(ring(Eq(equation.left, given.left), basis), Hyp(0))
    proof = ExistsElim(Hyp(0), ExistsIntro(Var(0), body))
    return close_proof(proof, binders, premises)


def prove_leaf(row, basis):
    target = closed_formula(row["source"])
    method = row["native_factory"]
    if method == "p01":
        proof = prove_p01(target, basis)
    elif method == "p03_step":
        proof = prove_p03_step(target, basis)
    elif method == "p05_step":
        proof = prove_p05_step(target, basis)
    elif method == "transport":
        proof = prove_transport(target, basis)
    elif method == "mul_transport":
        proof = prove_mul_transport(target, basis, row)
    elif method == "exists_transport":
        proof = prove_exists_transport(target, basis)
    elif method == "ring":
        binders, premises, equation = strip_target(target)
        if premises:
            raise ValueError("ring leaf cannot silently drop premises")
        proof = close_proof(ring(equation, basis), binders, premises)
    else:
        raise ValueError("unknown deterministic native proof factory")
    if not check((), proof, target):
        raise ValueError("native proof failed original target check")
    return target, proof
