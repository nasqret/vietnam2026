"""Six local rational-equivalence goals and ordinary HA proof producers.

Only conservative expanded IRat templates enter the kernel. Existing arithmetic
scripts are literal-extracted from a fixed nineteen-name, dependency-closed
allowlist, never imported as a registry or accepted on the strength of a name.
Proof execution belongs inside the parent's existing bounded worker. Neither
this module nor its manifest claims a fresh independent replay, Lean validation,
IR001 closure, or library admission.
"""
from __future__ import annotations

import ast
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from sqrt2_power_automation_baseline import runtime, source_pins as base_pins
from sqrt2_power_definitions import DEFINITIONS, PARENT, PARENT_SHA256, parse_named, definition_manifest
from sqrt2_power_native import (
    ROOT, SOURCE, BASIS_NAMES, Basis, BasicProof, closed_formula,
    instantiate, strip_target, close_proof,
)
from sqrt2_power_pilot_contracts import canonical
from peano_lab.engine.ring import DEFAULT_RING_LIMITS, prove_ring_equation
from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Bot, Eq, Imp, pretty_formula
from peano_lab.kernel.proofs import (
    AndElimL, AndElimR, AndIntro, CongAdd, CongMul, Cut, EqRefl, EqSym, EqTrans,
    Hyp, ImpElim, ImpIntro,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.library.proof_bundle import (
    BundleLimits, BundleNode, ProofBundle, check_proof_bundle, encode_formula, encode_proof_bundle,
)

SCHEMA = "sqrt2-power-local-rational-foundations-v1"
EXTRA_LAWS = frozenset({"add_right_cancel", "mul_left_cancel_nonzero",
                        "mul_right_cancel_nonzero", "succ_ne_zero"})
LOCAL_BASIS_NAMES = BASIS_NAMES | EXTRA_LAWS
MAX_SOURCE_BYTES = 1024**2
BUNDLE_LIMITS = BundleLimits(max_nodes=32, max_body_nodes=100000,
    max_total_body_nodes=200000, max_payload_bytes=8 * 1024**2)

# Stable names and sources are the statement contract; no caller may supply a
# weaker replacement formula. Every manifest also records its expanded AST.
FOUNDATIONS = (
    ("RF001", "irat_eq_reflexive",
     "forall p m d. IRatValid(p,m,d) -> IRatEq(p,m,d,p,m,d)",
     ("IRatValid", "IRatEq"), "reflexive"),
    ("RF002", "irat_eq_symmetric",
     "forall p m d q n e. IRatEq(p,m,d,q,n,e) -> IRatEq(q,n,e,p,m,d)",
     ("IRatEq",), "symmetric"),
    ("RF003", "irat_eq_transitive",
     "forall p m d q n e r s f. IRatEq(p,m,d,q,n,e) -> IRatEq(q,n,e,r,s,f) -> IRatEq(p,m,d,r,s,f)",
     ("IRatEq",), "transitive"),
    ("RF004", "irat_eq_scale_nonzero",
     "forall p m d k. IRatValid(p,m,d) -> ~(k=0) -> IRatEq(p,m,d,p*k,m*k,d*k)",
     ("IRatValid", "IRatEq"), "scale_nonzero"),
    ("RF005", "irat_eq_numerator_shift",
     "forall p m d h. IRatValid(p,m,d) -> IRatEq(p,m,d,p+h,m+h,d)",
     ("IRatValid", "IRatEq"), "numerator_shift"),
    ("RF006", "irat_eq_negation_compatible",
     "forall p m d q n e. IRatEq(p,m,d,q,n,e) -> IRatEq(m,p,d,n,q,e)",
     ("IRatEq",), "negation_compatible"),
)


class FoundationError(ValueError):
    """Changed statement/source, unsupported syntax, or rejected ordinary proof."""


def source_pins():
    result = base_pins()
    paths = [Path(__file__).resolve(), SOURCE, PARENT]
    paths.extend(ROOT / "scripts" / name for name in (
        "sqrt2_power_definitions.py", "sqrt2_power_native.py", "sqrt2_power_pilot_contracts.py",
        "sqrt2_power_campaign_spec.py"))
    paths.extend(ROOT / "peano-lab/py/peano_lab/library" / name
                 for name in ("__init__.py", "defined_syntax.py", "proof_bundle.py"))
    for path in paths:
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    return result


def _load_literal_specs(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_SOURCE_BYTES:
        raise FoundationError("literal arithmetic source exceeds its fixed byte bound")
    module = ast.parse(raw, filename=str(SOURCE))
    declarations = [node for node in module.body if isinstance(node, ast.AnnAssign)
                    and isinstance(node.target, ast.Name) and node.target.id == "THEOREMS"]
    if len(declarations) != 1 or not isinstance(declarations[0].value, ast.Tuple):
        raise FoundationError("the original literal theorem table changed")
    specs = {}
    for item in declarations[0].value.elts:
        if (not isinstance(item, ast.Call) or not isinstance(item.func, ast.Name)
            or item.func.id != "TheoremSpec" or item.keywords or len(item.args) != 5):
            raise FoundationError("nonliteral theorem table entry")
        name = ast.literal_eval(item.args[0])
        if name not in LOCAL_BASIS_NAMES:
            continue
        if name in specs:
            raise FoundationError("duplicate allowed arithmetic theorem")
        spec = tuple(ast.literal_eval(argument) for argument in item.args)
        if (type(spec[0]) is not str or type(spec[1]) is not str or type(spec[4]) is not str
            or type(spec[2]) is not tuple or type(spec[3]) is not tuple
            or any(type(value) is not str for value in spec[2] + spec[3])
            or len(spec[2]) != len(set(spec[2])) or not set(spec[2]) <= specs.keys()):
            raise FoundationError("arithmetic prerequisites are not an earlier local closed cone")
        specs[name] = spec
    if set(specs) != LOCAL_BASIS_NAMES or len(specs) != 19:
        raise FoundationError("missing exact nineteen-law local cone")
    return specs


class RationalBasis(Basis):
    """Local extension only; the original Basis class/allowlist remain unchanged."""
    def __init__(self):
        if SOURCE.stat().st_size > MAX_SOURCE_BYTES:
            raise FoundationError("literal arithmetic source exceeds bound")
        raw = SOURCE.read_bytes()
        self.specs = _load_literal_specs(raw)
        self.source_sha256 = sha256(raw).hexdigest()
        self.checked = {}
        self._active = set()

    def get(self, name):
        if type(name) is not str or name not in LOCAL_BASIS_NAMES:
            raise FoundationError("non-allowlisted rational foundation premise")
        if name in self.checked:
            return self.checked[name]
        if name in self._active:
            raise FoundationError("cyclic literal proof prerequisites")
        self._active.add(name)
        try:
            _, source, dependencies, script, _ = self.specs[name]
            premises = [self.get(dependency) for dependency in dependencies]
            target = closed_formula(source)
            curried = target
            for premise in reversed(premises):
                curried = Imp(premise.formula, curried)
            state = start(curried)
            for dependency in dependencies:
                state = apply_tactic(state, "intro", dependency)
            for command in script:
                tactic, _, arguments = command.partition(" ")
                state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, curried)
            for _ in dependencies:
                if type(certificate) is not ImpIntro:
                    raise FoundationError("ordinary dependency introduction is absent")
                certificate = certificate.body
            for premise in reversed(premises):
                certificate = Cut(premise.formula, target, premise.certificate, certificate)
            if not check((), certificate, target):
                raise FoundationError("ordinary HA rejected regenerated local arithmetic")
            value = BasicProof(target, certificate, dependencies, self.source_sha256,
                sha256(repr(self.specs[name]).encode()).hexdigest())
            self.checked[name] = value
            return value
        finally:
            self._active.remove(name)


def _row(name):
    if type(name) is not str:
        raise FoundationError("foundation name must be exact text")
    matches = [row for row in FOUNDATIONS if row[1] == name]
    if len(matches) != 1:
        raise FoundationError("unknown frozen rational foundation")
    return matches[0]


def foundation_target(name):
    """Expand the exact named statement; no free names or alternative target."""
    return parse_named(_row(name)[2])


def foundation_manifest():
    rows = []
    for identifier, name, source, definitions, method in FOUNDATIONS:
        target = foundation_target(name)
        expanded = pretty_formula(target, [])
        if closed_formula(expanded) != target:
            raise FoundationError("expanded foundation changed on ordinary HA parsing")
        tree = encode_formula(target)
        row = dict(id=identifier, name=name, named_source=source,
            named_source_sha256=sha256(source.encode()).hexdigest(), expanded_source=expanded,
            expanded_source_sha256=sha256(expanded.encode()).hexdigest(), expanded_ast=tree,
            expanded_ast_sha256=sha256(canonical(tree)).hexdigest(),
            definitions=list(definitions), definition_ids=[DEFINITIONS[n].stable_id for n in definitions],
            native_factory=method, authority="frozen_statement_not_checked_proof",
            closes_IR001=False, independent_lean_checked=False, library_admissions=0)
        row["contract_sha256"] = sha256(canonical(row)).hexdigest()
        rows.append(row)
    return dict(schema=SCHEMA, source_pins=source_pins(), rows=rows,
        conservative_definitions=definition_manifest(), historical_definition_parent_sha256=PARENT_SHA256,
        local_arithmetic_allowlist=sorted(LOCAL_BASIS_NAMES), original_basis_unchanged=True,
        ring_limits=asdict(DEFAULT_RING_LIMITS), bundle_limits=asdict(BUNDLE_LIMITS),
        requires_fresh_ordinary_HA_replay=True, requires_independent_Lean=True,
        IR001_closed=False, library_admissions=0)


def _preflight_ring(equation):
    """Before regenerating laws: a smaller fragment within unchanged ring bounds."""
    if type(equation) is not Eq:
        raise FoundationError("ring preflight requires an exact equation")
    count, active = [0], set()
    def visit(term, depth):
        count[0] += 1
        if (count[0] > DEFAULT_RING_LIMITS.max_ast_nodes
            or depth > DEFAULT_RING_LIMITS.max_ast_depth or id(term) in active):
            raise FoundationError("ring preflight exceeded AST/depth/cycle bounds")
        active.add(id(term))
        try:
            if type(term) is Var:
                if type(term.index) is not int or not 0 <= term.index < 9:
                    raise FoundationError("ring variable is outside the nine-binder fragment")
                return 1
            if type(term) is Zero:
                return 0
            if type(term) is Succ:
                return visit(term.term, depth + 1)
            if type(term) in (Add, Mul):
                left, right = visit(term.left, depth + 1), visit(term.right, depth + 1)
                degree = max(left, right) if type(term) is Add else left + right
                if degree > 3:
                    raise FoundationError("foundation normalization exceeds degree three")
                return degree
            raise FoundationError("non-kernel term in ring preflight")
        finally:
            active.remove(id(term))
    visit(equation.left, 0)
    visit(equation.right, 0)
    return count[0]


def _ring(equation, basis, observations):
    _preflight_ring(equation)
    # Preserve the real monotonic clock and every original default bound.
    result = prove_ring_equation(equation, basis.laws(), limits=DEFAULT_RING_LIMITS)
    observations.append(dict(equation_ast=encode_formula(equation), proof_nodes=result.proof_nodes,
        proof_depth=result.proof_depth, work_units=result.work_units))
    return result.certificate


def _cross(proof):
    return AndElimR(AndElimR(proof))


def _valid_right(proof):
    return AndElimL(AndElimR(proof))


def _equivalence(valid_left, valid_right, equality):
    return AndIntro(valid_left, AndIntro(valid_right, equality))


def _reflexive(target, basis, observations):
    _, _, goal = strip_target(target)
    p, m, d = (Var(index) for index in (2, 1, 0))
    equality = instantiate(basis.get("add_comm").certificate, Mul(p, d), Mul(m, d))
    return _equivalence(Hyp(0), Hyp(0), equality)


def _symmetric(target, basis, observations):
    p, m, d, q, n, e = (Var(index) for index in reversed(range(6)))
    comm = basis.get("add_comm").certificate
    first = instantiate(comm, Mul(q, d), Mul(m, e))
    last = instantiate(comm, Mul(p, e), Mul(n, d))
    equality = EqTrans(first, EqTrans(EqSym(_cross(Hyp(0))), last))
    return _equivalence(_valid_right(Hyp(0)), AndElimL(Hyp(0)), equality)


def _transitive(target, basis, observations):
    p, m, d, q, n, e, r, s, f = (Var(index) for index in reversed(range(9)))
    first_hypothesis, second_hypothesis = Hyp(1), Hyp(0)
    binders, premises, goal = strip_target(target)
    if binders != 9 or len(premises) != 2 or type(goal) is not And:
        raise FoundationError("unexpected exact transitivity shape")
    first_eq, second_eq = premises[0].right.right, premises[1].right.right
    wanted = goal.right.right
    left, right = wanted.left, wanted.right
    common = Mul(Add(q, n), Mul(d, f))
    a, b = Mul(left, e), Mul(right, e)
    combined_left = Add(Mul(first_eq.left, f), Mul(second_eq.left, d))
    combined_right = Add(Mul(first_eq.right, f), Mul(second_eq.right, d))
    transport = CongAdd(CongMul(_cross(first_hypothesis), EqRefl(f)),
                        CongMul(_cross(second_hypothesis), EqRefl(d)))
    equation = EqTrans(_ring(Eq(Add(a, common), combined_left), basis, observations),
        EqTrans(transport, _ring(Eq(combined_right, Add(b, common)), basis, observations)))
    cancellation = basis.get("add_right_cancel")
    # This dependency-free theorem is introduction-headed. An ordinary typed
    # Cut exposes its proved formula to the bidirectional elimination checker;
    # the lemma body is retained and checked, never treated as an axiom/name.
    typed_cancellation = Cut(cancellation.formula, cancellation.formula,
                            cancellation.certificate, Hyp(0))
    add_cancel = instantiate(typed_cancellation, a, b, common)
    multiplied_equality = ImpElim(add_cancel, equation)
    mul_cancel = instantiate(basis.get("mul_right_cancel_nonzero").certificate, left, right, e)
    # Middle denominator validity is an ACTUAL conjunct, not an ambient fact.
    equality = ImpElim(ImpElim(mul_cancel, _valid_right(first_hypothesis)), multiplied_equality)
    return _equivalence(AndElimL(first_hypothesis), _valid_right(second_hypothesis), equality)


def _scale_nonzero(target, basis, observations):
    p, m, d, k = (Var(index) for index in reversed(range(4)))
    _, _, goal = strip_target(target)
    nonzero_product = ImpElim(ImpElim(instantiate(basis.get("mul_ne_zero").certificate, d, k),
                                    Hyp(1)), Hyp(0))
    return _equivalence(Hyp(1), nonzero_product, _ring(goal.right.right, basis, observations))


def _numerator_shift(target, basis, observations):
    _, _, goal = strip_target(target)
    return _equivalence(Hyp(0), Hyp(0), _ring(goal.right.right, basis, observations))


def _negation_compatible(target, basis, observations):
    return _equivalence(AndElimL(Hyp(0)), _valid_right(Hyp(0)), EqSym(_cross(Hyp(0))))


_FACTORIES = {"reflexive": _reflexive, "symmetric": _symmetric, "transitive": _transitive,
    "scale_nonzero": _scale_nonzero, "numerator_shift": _numerator_shift,
    "negation_compatible": _negation_compatible}


def prove_foundation(name):
    """Bounded-worker API: return exact target, ordinary proof, and diagnostics.

This producer checks its full canonical bundle. A separate process must still
re-elaborate foundation_target(name) and replay those identical bundle bytes.
No successful producer receipt closes IR001 or substitutes for Lean.
"""
    identifier, _, named, definitions, factory = _row(name)
    before = source_pins()
    target = foundation_target(name)
    binders, premises, _ = strip_target(target)
    basis, ring_observations = RationalBasis(), []
    body = _FACTORIES[factory](target, basis, ring_observations)
    proof = close_proof(body, binders, premises)
    bundle = ProofBundle((BundleNode(0, target, (), proof),), 0)
    # Encoding first enforces ordinary bundle AST/depth/body/byte bounds.
    payload = encode_proof_bundle(bundle, target, limits=BUNDLE_LIMITS)
    receipt = check_proof_bundle(bundle, target, limits=BUNDLE_LIMITS)
    if check((), proof, Bot()):
        raise FoundationError("foundation certificate unexpectedly proves false")
    if source_pins() != before:
        raise FoundationError("rational foundation source changed during generation")
    diagnostics = dict(schema=SCHEMA, id=identifier, name=name, named_source=named,
        expanded_source=pretty_formula(target, []), expanded_ast_sha256=sha256(canonical(encode_formula(target))).hexdigest(),
        definitions=list(definitions), source_pins=before, regenerated_arithmetic=basis.manifest(),
        ring_observations=ring_observations, bundle_sha256=sha256(payload.encode()).hexdigest(),
        bundle_bytes=len(payload.encode()), proof_nodes=receipt.total_body_nodes,
        producer_ordinary_HA_checked=True, empty_context=True, classical=False,
        independent_fresh_replay_completed=False, requires_fresh_ordinary_HA_replay=True,
        independent_lean_checked=False, IR001_closed=False, library_admissions=0,
        model_proof_search_calls=0)
    return target, proof, diagnostics
