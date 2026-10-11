"""QF002: unconditional existence of the exact QF001 quadratic product trace.

The deterministic producer emits ordinary HA constructors only. Four decoded
components, four beta-prefix extensions, and induction construct the trace.
No nonzero hypothesis, real interpretation, solver verdict, or theorem-name
oracle enters the statement. The entire pinned beta/order ancestor cone is
replayed from actual proof bodies. Run proof production only under the wave
supervisor; imports and contract/archive inspection do not run the checker.
"""
from __future__ import annotations

from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from pathlib import Path

from sqrt2_power_quadratic_product_trace import (
    ROOT, FACTOR_PARAMETERS, TRACE_PARAMETERS, PINNED_SOURCES,
    V28_ARTIFACT, V28_ARTIFACT_SIZE, V28_ARTIFACT_SHA256,
    canonical, json_hash, definition_registry, _inert_metrics,
)

SCHEMA = "sqrt2-power-quadratic-trace-exists-v1"
F = FACTOR_PARAMETERS
U = TRACE_PARAMETERS
V = ("eb", "ec", "fb", "fc", "gb", "gc", "hb", "hc")
A = ("ap", "an", "bp", "bn")
B = ("cp", "cn", "dp", "dn")
C = ("rp", "rn", "sp", "sn")
PARAMETERS = F + ("L",)
TARGET_SHA256 = "bce1bbd903c3dd33cd47e30166931e5de2a0dde0f5d058bab6051dcfa4e6400b"
ANCESTOR_IDS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 20, 21,
    22, 23, 24, 27, 28, 29, 30, 31, 32, 34, 35, 38, 39, 40, 41, 42, 43, 48, 49,
    51, 53, 55, 56, 58, 59, 62, 63, 64, 69, 71, 72, 74, 76, 78, 79, 80, 81, 83,
    88, 90, 91, 92, 93, 94, 95, 96, 97, 112, 113, 114, 115, 116, 117, 118, 119,
    121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135,
    136, 138, 139, 140, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152)
ANCESTOR_IDS_SHA256 = "25aa3edf40f3d97a8b407f0918fc5e4df0ba59844ee4a5172f1b6b981023b4e1"
ANCESTOR_ROWS_SHA256 = "fa67117912e1048e5983f25b9125afb7d757b5671d55f8452403b9392642fcd8"
ANCESTOR_ROWS_BYTES = 150740
# Names are documentation. Exact formula AST and full row bytes bind each use.
ENDPOINTS = {
    14: ("le_refl", "forall a. exists h. h+a=a",
         "5d67d5564fa913d869e0c0eefb7a980638c6e0a27629442d3e36a23f023641ec"),
    29: ("zero_le", "forall a. exists h. h+0=a",
         "c5f9b91aa6d9d4293eef235303b65f066cf76ce58835797494ff5545914610a2"),
    38: ("succ_le_succ", "forall a b. (exists h. h+a=b) -> exists h. h+S a=S b",
         "77c127718d8f8afbf6c749fad2602e392ac8fe4491d153ff2d07cb87d137feb0"),
    39: ("le_of_succ_le_succ", "forall a b. (exists h. h+S a=S b) -> exists h. h+a=b",
         "43254c32374abad5e0f896a57898c1987b4472db1e07f6aa5ac67e24415a9552"),
    40: ("le_succ", "forall a b. (exists h. h+a=b) -> exists h. h+a=S b",
         "e4974edfb9475843a1f33a104fb835f56e7b30adc42ba3020a819ba4f0c56cf9"),
    43: ("le_eq_or_lt", "forall a b. (exists h. h+a=b) -> a=b \\/ exists h. h+S a=b",
         "298bde993ccfbe2fbfdfe65cfb41c83925afbb8bca28a4a4c11688c77c7b1b2e"),
    49: ("lt_not_le", "forall a b. (exists h. h+S a=b) -> (exists h. h+b=a) -> false",
         "97dc4a2fc69d58eeed92b8c54ddd57737f5ffa01cdacd9a7708f8e836b254c65"),
    121: ("beta_at_exists", "forall b c i. exists x. "
          "((exists h. h+S x=S((S i)*c)) /\\ exists q. b=q*S((S i)*c)+x)",
          "052dd288da25ad2b3f09d11ce47eefe05b150f19e74d144c6c3311aa378bc485"),
    152: ("beta_prefix_extend", "forall k b e s. exists z c. "
          "(((exists h. h+S s=S((S k)*c)) /\\ exists q. z=q*S((S k)*c)+s) /\\ "
          "forall i a. (exists h. h+S i=k) -> "
          "((exists h. h+S a=S((S i)*e)) /\\ exists q. b=q*S((S i)*e)+a) -> "
          "((exists h. h+S a=S((S i)*c)) /\\ exists q. z=q*S((S i)*c)+a))",
          "b759073b54b782bb29c767daad4726d5f4c54ede4c630b2268f1fc756d9703a6"),
}


def named(name, *arguments):
    return name + "(" + ",".join(arguments) + ")"


def forall(names, source):
    return "forall " + " ".join(names) + ". " + source


def exists(names, source):
    return "exists " + " ".join(names) + ". " + source


def at(codes, index, values):
    return named("IQuadAt", *codes, index, *values)


def trace(factors, codes, length):
    return named("IQuadProductTrace", *factors, *codes, length)


def preserved(old, new, length):
    return forall(("i",) + A,
        named("Lt", "i", length) + " -> " + at(old, "i", A) + " -> " + at(new, "i", A))


NAMED_SOURCE = forall(PARAMETERS, exists(U, trace(F, U, "L")))
HELPERS = (
    ("decode", forall(F + ("i",), exists(A, at(F, "i", A))), (121,)),
    ("extend", forall(U + ("L",) + C, exists(V,
        at(V, "L", C) + " /\\ (" + preserved(U, V, "L") + ")")), (152,)),
    ("transport", forall(F + U + V + ("L",),
        "(" + preserved(U, V, "S L") + ") -> " + trace(F, U, "L") + " -> " + trace(F, V, "L")),
        (29, 38, 40)),
    ("successor", forall(F + U + ("L",), trace(F, U, "L") + " -> " + exists(V, trace(F, V, "S L"))),
        (14, 39, 43, "decode", "extend", "transport")),
    ("QF002", NAMED_SOURCE, (29, 49, "extend", "successor")),
)
HELPER_TARGET_SHA256 = {
    "decode": "e864f274188cf0a1f8278bca5152d88bd33c4f98f7692b849517cfffb9a0318a",
    "extend": "e28a1f3d3dbd23aaf1084dd08d3cd5dea939f4deb695c4ac76d6367958fe9452",
    "transport": "566e8ab4bb77669aad68b5c2c03d6ec703db2aa7240268caab200224259109a3",
    "successor": "7e3553c9fc68944ab42c722125b22ea494330c1453135fc74a21ff1b652c18e9",
    "QF002": TARGET_SHA256,
}


class TraceExistsError(ValueError):
    """Frozen statement, ancestor, scoping or unchanged resource check failed."""


def frozen_quadratic_trace_exists_target():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Forall, Exists, And
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE, registry=definition_registry())
    body = target
    for kind, count in ((Forall, 9), (Exists, 8)):
        for _ in range(count):
            if type(body) is not kind:
                raise TraceExistsError("QF002 universal/existential binder shape changed")
            body = body.body
    if type(body) is not And or json_hash(encode_formula(target)) != TARGET_SHA256:
        raise TraceExistsError("QF002 unconditional exact target changed")
    return target


def source_contract():
    return dict(code="QF002", schema=SCHEMA, source=NAMED_SOURCE,
        statement_ast_sha256=TARGET_SHA256, parameters=list(PARAMETERS),
        premise_count=0, existential_stream_parameters=list(U),
        conditional_on_actual_trace=False, nonzero_factors_required=False,
        starts_at_one=True, actual_beta_transitions=True, reused_definition_ids=["ND0390", "ND0391", "ND0392"],
        original_HA_checked=False, authority="source_contract_not_proof_authority",
        real_interpretation=False, rational_denominator_claim=False, closes_IR046=False,
        closes_IR072=False, IR_parents_closed=0, library_admissions=0)


def quadratic_trace_exists_source_pins():
    expected = dict(PINNED_SOURCES)
    expected["scripts/sqrt2_power_quadratic_product_trace.py"] = "e3b2beb50afb50722d0ec8fe640402851476ba17cb33f802b45860a27c43e147"
    # The 19 MB parent is authenticated separately, not misclassified as a
    # <=16 MiB source snapshot. All selected actual bodies enter the certificate.
    result = {}
    for name in sorted((*expected, "scripts/sqrt2_power_quadratic_trace_exists.py")):
        path = ROOT / name
        cap = 16 * 1024**2
        with path.open("rb") as stream:
            raw = stream.read(cap + 1)
        digest = sha256(raw).hexdigest()
        if len(raw) > cap or name in expected and digest != expected[name]:
            raise TraceExistsError("QF002 source/input changed: " + name)
        result[name] = dict(bytes=len(raw), sha256=digest)
    return result


def inert_ancestor_rows(artifact_path=V28_ARTIFACT):
    from sqrt2_power_native import closed_formula
    from peano_lab.library.proof_bundle import encode_formula
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE + 1)
    if len(raw) != V28_ARTIFACT_SIZE or sha256(raw).hexdigest() != V28_ARTIFACT_SHA256:
        raise TraceExistsError("actual v28 proof bytes changed")
    value = json.loads(raw)
    del raw
    if value[0] != "peano-lab-bundle-v1" or value[1] != 861 or len(value[3]) != 862:
        raise TraceExistsError("actual v28 envelope changed")
    seen, pending = set(), list(ENDPOINTS)
    while pending:
        old = pending.pop()
        if old not in seen:
            seen.add(old)
            pending.extend(value[3][old][2])
    ids = tuple(sorted(seen))
    rows = tuple(value[3][old] for old in ids)
    if (ids != ANCESTOR_IDS or json_hash(ids) != ANCESTOR_IDS_SHA256
            or json_hash(rows) != ANCESTOR_ROWS_SHA256 or len(canonical(rows)) != ANCESTOR_ROWS_BYTES):
        raise TraceExistsError("actual beta/order ancestor cone changed")
    for old, (_, source, digest) in ENDPOINTS.items():
        row = value[3][old]
        if json_hash(row) != digest or row[1] != encode_formula(closed_formula(source)):
            raise TraceExistsError("beta/order endpoint differs from exact source")
    return ids, rows


@dataclass(frozen=True)
class Scope:
    """Untrusted names-to-de-Bruijn bookkeeping; never a kernel context oracle."""
    variables: tuple = ()
    hypotheses: tuple = ()

    def variable(self, name):
        if name in self.variables:
            raise TraceExistsError("reused proof eigenvariable")
        return Scope((name,) + self.variables, self.hypotheses)

    def hypothesis(self, name):
        if name in self.hypotheses:
            raise TraceExistsError("reused proof hypothesis")
        return Scope(self.variables, (name,) + self.hypotheses)

    def term(self, name):
        from peano_lab.kernel.terms import Var
        return Var(self.variables.index(name))

    def hyp(self, name):
        from peano_lab.kernel.proofs import Hyp
        return Hyp(self.hypotheses.index(name))

    def terms(self, names):
        return tuple(self.term(name) for name in names)


def introduce(scope, variables, hypotheses, finish):
    from peano_lab.kernel.proofs import ForallIntro, ImpIntro
    if variables:
        return ForallIntro(introduce(scope.variable(variables[0]), variables[1:], hypotheses, finish))
    if hypotheses:
        return ImpIntro(introduce(scope.hypothesis(hypotheses[0]), (), hypotheses[1:], finish))
    return finish(scope)


def eliminate(scope, proof, variables, label, finish):
    """Open actual existential witnesses; retain all intermediate contexts."""
    from peano_lab.kernel.proofs import ExistsElim
    if not variables:
        raise TraceExistsError("empty existential elimination")
    name = label if len(variables) == 1 else label + "_" + variables[0]
    inner = scope.variable(variables[0]).hypothesis(name)
    body = finish(inner) if len(variables) == 1 else eliminate(
        inner, inner.hyp(name), variables[1:], label, finish)
    return ExistsElim(proof, body)


def witness(terms, body):
    from peano_lab.kernel.proofs import ExistsIntro
    for term in reversed(terms):
        body = ExistsIntro(term, body)
    return body


def conjunction(*proofs):
    from peano_lab.kernel.proofs import AndIntro
    result = proofs[-1]
    for proof in reversed(proofs[:-1]):
        result = AndIntro(proof, result)
    return result


def field(proof, index, count):
    from peano_lab.kernel.proofs import AndElimL, AndElimR
    for _ in range(index):
        proof = AndElimR(proof)
    return AndElimL(proof) if index < count - 1 else proof


def apply(proof, *arguments):
    from peano_lab.kernel.proofs import ImpElim
    for argument in arguments:
        proof = ImpElim(proof, argument)
    return proof


def specialize(scope, name, *terms):
    from sqrt2_power_native import instantiate
    return instantiate(scope.hyp(name), *terms)


def products(scope):
    from peano_lab.kernel.terms import Add, Mul, Succ, Zero
    ap, an, bp, bn, cp, cn, dp, dn = scope.terms(A+B)
    two = Succ(Succ(Zero()))
    return (Add(Add(Mul(ap, cp), Mul(an, cn)), Mul(two, Add(Mul(bp, dp), Mul(bn, dn)))),
            Add(Add(Mul(ap, cn), Mul(an, cp)), Mul(two, Add(Mul(bp, dn), Mul(bn, dp)))),
            Add(Add(Mul(ap, dp), Mul(an, dn)), Add(Mul(bp, cp), Mul(bn, cn))),
            Add(Add(Mul(ap, dn), Mul(an, dp)), Add(Mul(bp, cn), Mul(bn, cp))))


def _decode(scope):
    def collect(s, component):
        if component == 4:
            return witness(s.terms(A), conjunction(*(s.hyp("value"+str(k)) for k in range(4))))
        source = specialize(s, 121, *s.terms(F[2*component:2*component+2]), s.term("i"))
        return eliminate(s, source, (A[component],), "value"+str(component), lambda t: collect(t, component+1))
    return introduce(scope, F+("i",), (), lambda s: collect(s, 0))


def _extend(scope):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL, AndElimR, AndIntro
    def collect(s, component):
        if component == 4:
            def transport(t):
                return conjunction(*(apply(instantiate(AndElimR(t.hyp("extension"+str(k))),
                    t.term("i"), t.term(A[k])), t.hyp("bound"), field(t.hyp("old"), k, 4)) for k in range(4)))
            result = AndIntro(conjunction(*(AndElimL(s.hyp("extension"+str(k))) for k in range(4))),
                introduce(s, ("i",)+A, ("bound", "old"), transport))
            return witness(s.terms(V), result)
        source = specialize(s, 152, s.term("L"), *s.terms(U[2*component:2*component+2]), s.term(C[component]))
        return eliminate(s, source, V[2*component:2*component+2], "extension"+str(component),
            lambda t: collect(t, component+1))
    return introduce(scope, U+("L",)+C, (), lambda s: collect(s, 0))


def _transport(scope):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL, AndElimR, AndIntro
    from peano_lab.kernel.terms import Succ, Zero
    def main(s):
        zero, one = Zero(), Succ(Zero())
        bound0 = apply(specialize(s, 38, zero, s.term("L")), specialize(s, 29, s.term("L")))
        initial = apply(specialize(s, "preserve", zero, one, zero, zero, zero), bound0, AndElimL(s.hyp("trace")))
        def step(t):
            source = apply(instantiate(AndElimR(t.hyp("trace")), t.term("i")), t.hyp("bound"))
            def decoded(u):
                i, length = u.term("i"), u.term("L")
                pair = u.hyp("step")
                current_bound = apply(specialize(u, 40, Succ(i), length), u.hyp("bound"))
                next_bound = apply(specialize(u, 38, Succ(i), length), u.hyp("bound"))
                current = apply(specialize(u, "preserve", i, *u.terms(A)), current_bound, field(pair, 1, 5))
                after = apply(specialize(u, "preserve", Succ(i), *u.terms(C)), next_bound, field(pair, 2, 5))
                return witness(u.terms(A+B+C), conjunction(field(pair, 0, 5), current, after,
                    field(pair, 3, 5), field(pair, 4, 5)))
            return eliminate(t, source, A+B+C, "step", decoded)
        return AndIntro(initial, introduce(s, ("i",), ("bound",), step))
    return introduce(scope, F+U+V+("L",), ("preserve", "trace"), main)


def _successor(scope, registry):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL, AndElimR, AndIntro, EqRefl, EqSubst, EqSym, OrElim
    from peano_lab.kernel.terms import Add, Succ
    def decoded(s):
        source = specialize(s, "extend", *s.terms(U), Succ(s.term("L")), *products(s))
        def appended(t):
            def old_trace(u):
                return apply(specialize(u, "transport", *u.terms(F+U+V), u.term("L")),
                    AndElimR(u.hyp("extended")), u.hyp("trace"))
            def step(u):
                le = apply(specialize(u, 39, u.term("i"), u.term("L")), u.hyp("bound"))
                split = apply(specialize(u, 43, u.term("i"), u.term("L")), le)
                v = u.hypothesis("last")
                length, result = v.term("L"), products(v)
                current = apply(instantiate(AndElimR(v.hyp("extended")), length, *v.terms(A)),
                    specialize(v, 14, Succ(length)), v.hyp("current"))
                last = witness(v.terms(A+B)+result, conjunction(v.hyp("factor"), current,
                    AndElimL(v.hyp("extended")), EqRefl(Add(result[0], result[1])),
                    EqRefl(Add(result[2], result[3]))))
                motive_scope = v.variable("position")
                motive = parse_named(named("IQuadProductStep", *F, *V, "position"),
                    motive_scope.variables, registry)
                last_case = EqSubst(motive, EqSym(v.hyp("last")), last)
                w = u.hypothesis("earlier")
                earlier = apply(instantiate(AndElimR(old_trace(w)), w.term("i")), w.hyp("earlier"))
                return OrElim(split, last_case, earlier)
            return witness(t.terms(V), AndIntro(AndElimL(old_trace(t)),
                introduce(t, ("i",), ("bound",), step)))
        return eliminate(s, source, V, "extended", appended)
    def main(s):
        source = specialize(s, "decode", *s.terms(F), s.term("L"))
        def factor(t):
            source = specialize(t, "decode", *t.terms(U), t.term("L"))
            return eliminate(t, source, A, "current", decoded)
        return eliminate(s, source, B, "factor", factor)
    return introduce(scope, F+U+("L",), ("trace",), main)


def _root(scope, target):
    from peano_lab.kernel.proofs import AndElimL, AndIntro, BotElim, Ind
    from peano_lab.kernel.terms import Succ, Zero
    motive = target
    for _ in range(9):
        motive = motive.body
    def induction(s):
        zero, one = Zero(), Succ(Zero())
        source = specialize(s, "extend", *((zero,)*8), zero, one, zero, zero, zero)
        def base(t):
            def impossible(u):
                return BotElim(apply(specialize(u, 49, u.term("i"), Zero()),
                    u.hyp("bound"), specialize(u, 29, u.term("i"))))
            return witness(t.terms(U), AndIntro(AndElimL(t.hyp("initial")),
                introduce(t, ("i",), ("bound",), impossible)))
        base_proof = eliminate(s, source, U, "initial", base)
        def successor(t):
            return eliminate(t, t.hyp("IH"), U, "trace", lambda u:
                apply(specialize(u, "successor", *u.terms(F+U), u.term("L")), u.hyp("trace")))
        return Ind(motive, base_proof, introduce(s, ("L",), ("IH",), successor))
    return introduce(scope, F, (), induction)


def helper_body(name, dependencies, target, registry):
    constructors = {"decode": _decode, "extend": _extend, "transport": _transport,
        "successor": lambda s: _successor(s, registry), "QF002": lambda s: _root(s, target)}
    return introduce(Scope(), (), dependencies, constructors[name])


@dataclass(frozen=True)
class QuadraticTraceExistsCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_quadratic_trace_exists(*, limits=None, artifact_path=V28_ARTIFACT):
    """One root-owned guarded worker, complete canonical original-HA replay."""
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Imp
    from peano_lab.kernel.checker import check
    from peano_lab.library.proof_bundle import (decode_formula, decode_proof_bundle,
        encode_formula, encode_proof, check_proof_bundle)
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise TraceExistsError("expected unchanged BinaryDAGLimits")
    before = quadratic_trace_exists_source_pins()
    target, registry = frozen_quadratic_trace_exists_target(), definition_registry()
    ids, original = inert_ancestor_rows(artifact_path)
    remap = {old: new for new, old in enumerate(ids)}
    rows = [[row[0], row[1], [remap[d] for d in row[2]], row[3]] for row in original]
    del original
    gc.collect()
    total, deepest = 0, 0
    for i, row in enumerate(rows):
        count, depth = _inert_metrics(row[3], limits)
        total, deepest = total + count, max(deepest, depth)
        if any(not 0 <= d < i for d in row[2]) or row[0] < 8*count+16:
            raise TraceExistsError("invalid actual ancestor dependency/fuel")
    ancestor_total = total
    helpers = []
    for name, source, dependencies in HELPERS:
        statement = parse_named(source, registry=registry)
        if json_hash(encode_formula(statement)) != HELPER_TARGET_SHA256[name]:
            raise TraceExistsError("QF002 frozen helper statement changed: " + name)
        body = helper_body(name, dependencies, statement, registry)
        count, depth = _body_metrics(body, limits)
        total, deepest = total+count, max(deepest, depth)
        if total > limits.max_total_body_nodes or len(rows)+1 > limits.max_nodes:
            raise TraceExistsError("QF002 unchanged aggregate body/node bound exceeded")
        _row_preflight(statement, body, limits)
        linked = tuple(remap[d] for d in dependencies)
        curried = statement
        for dependency in reversed(linked):
            curried = Imp(decode_formula(rows[dependency][1], _depth=limits.max_depth), curried)
        if not check((), body, curried):
            raise TraceExistsError("original HA rejected exact QF002 helper: " + name)
        remap[name] = len(rows)
        rows.append([8*count+16, encode_formula(statement), list(linked), encode_proof(body)])
        helpers.append(dict(name=name, node=remap[name], dependencies=list(linked),
            source=source, target_ast_sha256=json_hash(rows[-1][1]), body_nodes=count, depth=depth))
    if rows[-1][1] != encode_formula(target):
        raise TraceExistsError("final helper does not prove the original QF002 target")
    payload = canonical(["peano-lab-bundle-v1", len(rows)-1, encode_formula(target), rows]).decode()+"\n"
    if len(payload.encode()) > limits.max_payload_bytes:
        raise TraceExistsError("QF002 unchanged complete payload bound exceeded")
    del rows, body
    gc.collect()
    bundle, decoded = decode_proof_bundle(payload, limits=limits.bundle_limits())
    if decoded != target:
        raise TraceExistsError("decoded target differs from original QF002 target")
    receipt = check_proof_bundle(bundle, target, limits=limits.bundle_limits())
    with Path(artifact_path).open("rb") as stream:
        raw_parent = stream.read(V28_ARTIFACT_SIZE + 1)
    if len(raw_parent) != V28_ARTIFACT_SIZE or sha256(raw_parent).hexdigest() != V28_ARTIFACT_SHA256:
        raise TraceExistsError("actual archive changed during QF002 replay")
    del raw_parent
    if receipt.target != target or quadratic_trace_exists_source_pins() != before:
        raise TraceExistsError("target/source changed during QF002 canonical replay")
    provenance = dict(source_contract(), source_pins=before, original_HA_checked=True,
        canonical_bytes_replayed=True, empty_context=True,
        ancestor_nodes=len(ids), ancestor_body_nodes=ancestor_total,
        ancestor_original_ids=list(ids), ancestor_rows_sha256=ANCESTOR_ROWS_SHA256,
        archive_sha256=V28_ARTIFACT_SHA256, helpers=helpers,
        trace_existence_proved=True, root_induction_count=1,
        strategy="deterministic_beta_witness_construction_and_ordinary_HA_induction",
        local_have_compiler_calls=0, solver_calls=0, ring_normalizer_calls=0,
        new_axioms=[], external_certificate_references=[], independent_lean_checked=False)
    return QuadraticTraceExistsCertificate(target, bundle, payload, receipt, deepest, provenance)
