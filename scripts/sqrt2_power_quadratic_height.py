"""QH001: the natural coefficient mass of canonical quadratic multiplication.

H(ap,an,bp,bn)=(ap+an)+2*(bp+bn). For canonical multiplication C=A*B,
H(C)<=H(A)*H(B), witnessed by the explicit gap 2*(bp+bn)*(dp+dn).
Arbitrary signed representatives do NOT obey this bound; canonical output
equalities are an indispensable premise. Definitions share notation only.

Four <=4-variable identities use shared arithmetic laws and deterministic
additive normalization, then compose without a fifteen-variable ring call.
External solvers may check the conjecture but never provide proof authority.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_quadratic_trace_exists import (
    ROOT, A, B, C, Scope, named, forall, introduce, field, specialize, products,
    canonical, json_hash, quadratic_trace_exists_source_pins,
    definition_registry as trace_registry,
)

SCHEMA = "sqrt2-power-quadratic-height-v1"
PARAMETERS = A+B+C+("a", "b", "c")
CANONICAL_COMPONENTS = (
    "(ap*cp+an*cn)+2*(bp*dp+bn*dn)",
    "(ap*cn+an*cp)+2*(bp*dn+bn*dp)",
    "(ap*dp+an*dn)+(bp*cp+bn*cn)",
    "(ap*dn+an*dp)+(bp*cn+bn*cp)",
)
DEFINITION_ROWS = (
    (394, "IQuadCanonicalProduct", A+B+C,
     "rp=("+CANONICAL_COMPONENTS[0]+") /\\ (rn=("+CANONICAL_COMPONENTS[1]+") /\\ "
     "(sp=("+CANONICAL_COMPONENTS[2]+") /\\ sn=("+CANONICAL_COMPONENTS[3]+")))",
     "The four outputs are the explicit nonnegative component polynomials, not arbitrary equivalent representatives.",
     "64067a358d423d8b93f50c25eb8dba5da0286b01c753bdbf17d41788f8cab5e3"),
    (395, "IQuadHeight", A+("h",), "h=(ap+an)+2*(bp+bn)",
     "A natural coefficient mass for a specified signed-pair representation; no boundedness or norm claim is a clause.",
     "7af49e7b24eceb322889c219cec273439fc0a37a99203a38c48643f8c3ce3cd7"),
)
NAMED_SOURCE = forall(PARAMETERS,
    named("IQuadCanonicalProduct", *A, *B, *C) + " -> " +
    named("IQuadHeight", *A, "a") + " -> " + named("IQuadHeight", *B, "b") + " -> " +
    named("IQuadHeight", *C, "c") + " -> exists gap. gap+c=a*b")
TARGET_SHA256 = "b9459095385fa95c3e8d4d7ff638db6464c2053389c1921031dabfe88560f7e6"
HELPERS = (
    ("shuffle", "forall p q r s. (p+q)+(r+s)=(p+r)+(q+s)", "6da5717225e4cdde48c0c162806d72cd537dbb509101cf41968d2231d9a29b3f"),
    ("pair", "forall a b c d. (a*c+b*d)+(a*d+b*c)=(a+b)*(c+d)", "36084261d2aa8821a09997a583ef20b235ac334932fb6172137d78a9c8587b0d"),
    ("scaled_shuffle", "forall p q r s. (p+2*q)+(r+2*s)=(p+r)+2*(q+s)", "5710bf132aceec04184c6de2c7c1c3ac777b4ef0c5d5cbcb5001874ad93e4a41"),
    ("gap", "forall a b c d. 2*(b*d)+((a*c+2*(b*d))+2*(a*d+b*c))=(a+2*b)*(c+2*d)", "d9e5c52aa2053543cd4f3a601b6ba964321a3b5afacafb6571d9ae1f9ff13cc1"),
)
BASIS_SOURCES = {
    "add_assoc": "forall n m k. (n+m)+k=n+(m+k)",
    "add_comm": "forall n m. n+m=m+n",
    "mul_add": "forall n m k. n*(m+k)=n*m+n*k",
    "add_mul": "forall n m k. (n+m)*k=n*k+m*k",
    "mul_assoc": "forall n m k. (n*m)*k=n*(m*k)",
    "mul_comm": "forall n m. n*m=m*n",
    "mul_one": "forall n. n*1=n",
}
HELPER_DEPENDENCIES = {
    "shuffle": ("add_assoc", "add_comm"),
    "pair": ("shuffle", "mul_add", "add_mul", "add_comm"),
    "scaled_shuffle": ("shuffle", "mul_add"),
    "gap": ("add_assoc", "add_comm", "add_mul", "mul_add", "mul_assoc", "mul_comm", "double"),
}


class QuadraticHeightError(ValueError):
    """Changed conservative expansion, source, exact target or resource bound."""


def definition_registry():
    from sqrt2_power_definitions import PARENT, PARENT_SHA256, parse_named
    from peano_lab.kernel.formulas import pretty_formula, parse_formula_in_context
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(trace_registry())
    raw = PARENT.read_bytes()
    if sha256(raw).hexdigest() != PARENT_SHA256:
        raise QuadraticHeightError("immutable definition parent changed")
    parent = json.loads(raw)["reviewed_definitions"]
    used_ids = {d["id"] for d in parent} | {d.stable_id for d in registry.values()} | {f"ND{i:04d}" for i in range(382, 394)}
    used_names = {d["name"] for d in parent} | set(registry)
    for number, name, parameters, source, summary, digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if identifier in used_ids or name in used_names:
            raise QuadraticHeightError("local height definition collision")
        formula = parse_named(source, parameters, registry)
        if json_hash(encode_formula(formula)) != digest:
            raise QuadraticHeightError("canonical height definition expansion changed")
        expanded = pretty_formula(formula, list(parameters))
        definition = _definition(stable_id=identifier, name=name, parameters=parameters,
            template_source=expanded, summary=summary, category="irrationality_quadratic_heights",
            conceptual_dependencies=())
        if definition.template_formula != formula or parse_formula_in_context(expanded, list(parameters)) != formula:
            raise QuadraticHeightError("canonical height definition failed exact roundtrip")
        registry[name] = definition
        used_ids.add(identifier)
        used_names.add(name)
    return MappingProxyType(registry)


def frozen_quadratic_height_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE, registry=definition_registry())
    binders, premises, conclusion = strip_target(target)
    if (binders != 15 or len(premises) != 4 or type(conclusion) is not Exists
            or json_hash(encode_formula(target)) != TARGET_SHA256):
        raise QuadraticHeightError("QH001 original canonical-height statement changed")
    return target


def source_contract():
    return dict(code="QH001", schema=SCHEMA, source=NAMED_SOURCE,
        statement_ast_sha256=TARGET_SHA256, parameters=list(PARAMETERS), premise_count=4,
        canonical_outputs_required=True, arbitrary_representatives_bounded=False,
        coefficient_mass="(ap+an)+2*(bp+bn)", explicit_gap="2*((bp+bn)*(dp+dn))",
        new_definition_ids=["ND0394", "ND0395"], definition_admissions=0,
        original_HA_checked=False, authority="source_contract_not_proof_authority",
        finite_trace_height_bound=False, rational_denominator_claim=False, real_interpretation=False,
        closes_IR046=False, closes_IR072=False, IR_parents_closed=0, library_admissions=0)


def quadratic_height_source_pins():
    result = quadratic_trace_exists_source_pins()
    if result["scripts/sqrt2_power_quadratic_trace_exists.py"]["sha256"] != "4269d6b9a2282fad3870b408578e2894544c4b172ea76ea2891945adce25ba1a":
        raise QuadraticHeightError("actual scoped proof builder source changed")
    expected = {
        "peano-lab/py/peano_lab/library/theorems.py": "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
        "peano-lab/py/peano_lab/engine/ring.py": "7ba5c4b4085725677ba984afa8a50cee8061ce9ba333b644993ecff5fd5f249e",
    }
    for name in (*expected, "scripts/sqrt2_power_quadratic_height.py"):
        raw = (ROOT / name).read_bytes()
        digest = sha256(raw).hexdigest()
        if len(raw) > 16*1024**2 or name in expected and digest != expected[name]:
            raise QuadraticHeightError("literal ring producer source changed")
        result[name] = dict(bytes=len(raw), sha256=digest)
    return result


def _root_body():
    from peano_lab.kernel.proofs import CongAdd, CongMul, EqRefl, EqSym, EqTrans, ExistsIntro
    from peano_lab.kernel.terms import Add, Mul, Succ, Zero
    def main(s):
        ap, an, bp, bn, cp, cn, dp, dn = s.terms(A+B)
        two = Succ(Succ(Zero()))
        P, N = Add(Mul(ap, cp), Mul(an, cn)), Add(Mul(ap, cn), Mul(an, cp))
        Q, R = Add(Mul(bp, dp), Mul(bn, dn)), Add(Mul(bp, dn), Mul(bn, dp))
        W, X = Add(Mul(ap, dp), Mul(an, dn)), Add(Mul(bp, cp), Mul(bn, cn))
        Y, Z = Add(Mul(ap, dn), Mul(an, dp)), Add(Mul(bp, cn), Mul(bn, cp))
        left_real, left_radical = Add(ap, an), Add(bp, bn)
        right_real, right_radical = Add(cp, cn), Add(dp, dn)
        gap = Mul(two, Mul(left_radical, right_radical))
        real = EqTrans(specialize(s, "scaled_shuffle", P, Q, N, R),
            CongAdd(specialize(s, "pair", ap, an, cp, cn),
                CongMul(EqRefl(two), specialize(s, "pair", bp, bn, dp, dn))))
        radical = EqTrans(specialize(s, "shuffle", W, X, Y, Z),
            CongAdd(specialize(s, "pair", ap, an, dp, dn), specialize(s, "pair", bp, bn, cp, cn)))
        represented = CongAdd(CongAdd(field(s.hyp("canonical"), 0, 4), field(s.hyp("canonical"), 1, 4)),
            CongMul(EqRefl(two), CongAdd(field(s.hyp("canonical"), 2, 4), field(s.hyp("canonical"), 3, 4))))
        normalized = EqTrans(s.hyp("hc"), EqTrans(represented, CongAdd(real, CongMul(EqRefl(two), radical))))
        equation = EqTrans(CongAdd(EqRefl(gap), normalized),
            EqTrans(specialize(s, "gap", left_real, left_radical, right_real, right_radical),
                EqSym(CongMul(s.hyp("ha"), s.hyp("hb")))))
        return ExistsIntro(gap, equation)
    return introduce(Scope(), (), tuple(row[0] for row in HELPERS), lambda s:
        introduce(s, PARAMETERS, ("canonical", "ha", "hb", "hc"), main))


def _chain(*proofs):
    from peano_lab.kernel.proofs import EqTrans
    if len(proofs) == 1:
        return proofs[0]
    midpoint = len(proofs)//2
    return EqTrans(_chain(*proofs[:midpoint]), _chain(*proofs[midpoint:]))


def _sum(terms):
    from peano_lab.kernel.terms import Add
    if not terms:
        raise QuadraticHeightError("empty additive normal form")
    result = terms[-1]
    for term in reversed(terms[:-1]):
        result = Add(term, result)
    return result


def _additive_equal(scope, left, right):
    """Bounded untrusted associativity/adjacent-swap reconstruction, no oracle.

Multiplication terms are opaque atoms. Every reassociation and swap is an
ordinary application of an actual bundle dependency, replayed by the kernel.
"""
    from peano_lab.kernel.proofs import CongAdd, EqRefl, EqSym
    from peano_lab.kernel.terms import Add
    def concat(xs, ys):
        if len(xs) == 1:
            return EqRefl(Add(xs[0], _sum(ys)))
        return _chain(specialize(scope, "add_assoc", xs[0], _sum(xs[1:]), _sum(ys)),
            CongAdd(EqRefl(xs[0]), concat(xs[1:], ys)))
    def flatten(term):
        if type(term) is not Add:
            return (term,), EqRefl(term)
        xs, lp = flatten(term.left)
        ys, rp = flatten(term.right)
        if len(xs)+len(ys) > 16:
            raise QuadraticHeightError("additive reconstruction exceeds fixed sixteen-atom fragment")
        return xs+ys, _chain(CongAdd(lp, rp), concat(xs, ys))
    def adjacent(xs, index):
        if index:
            return CongAdd(EqRefl(xs[0]), adjacent(xs[1:], index-1))
        a, b = xs[:2]
        if len(xs) == 2:
            return specialize(scope, "add_comm", a, b)
        rest = _sum(xs[2:])
        return _chain(EqSym(specialize(scope, "add_assoc", a, b, rest)),
            CongAdd(specialize(scope, "add_comm", a, b), EqRefl(rest)),
            specialize(scope, "add_assoc", b, a, rest))
    def reorder(xs, ys):
        if len(xs) != len(ys) or not xs:
            raise QuadraticHeightError("additive atom inventory differs")
        if len(xs) == 1:
            if xs != ys:
                raise QuadraticHeightError("additive atom differs")
            return EqRefl(xs[0])
        moved, proofs = list(xs), []
        try:
            position = moved.index(ys[0])
        except ValueError:
            raise QuadraticHeightError("missing target additive atom") from None
        for index in reversed(range(position)):
            proofs.append(adjacent(tuple(moved), index))
            moved[index], moved[index+1] = moved[index+1], moved[index]
        proofs.append(CongAdd(EqRefl(moved[0]), reorder(tuple(moved[1:]), ys[1:])))
        return _chain(*proofs)
    xs, left_proof = flatten(left)
    ys, right_proof = flatten(right)
    return _chain(left_proof, reorder(xs, ys), EqSym(right_proof))


def _double_body():
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom, CongAdd, EqRefl
    from peano_lab.kernel.terms import Succ, Zero
    def main(s):
        one, x = Succ(Zero()), s.term("x")
        return _chain(specialize(s, "mul_comm", Succ(one), x),
            instantiate(Axiom("PA6"), x, one),
            CongAdd(specialize(s, "mul_one", x), EqRefl(x)))
    return introduce(Scope(), (), ("mul_comm", "mul_one"), lambda s: introduce(s, ("x",), (), main))


def _helper_body(name):
    from peano_lab.kernel.proofs import CongAdd, CongMul, EqRefl, EqSym
    from peano_lab.kernel.terms import Add, Mul, Succ, Zero
    def main(s):
        a, b, c, d = s.terms(("a", "b", "c", "d"))
        two = Succ(Succ(Zero()))
        if name == "shuffle":
            return _additive_equal(s, Add(Add(a,b), Add(c,d)), Add(Add(a,c), Add(b,d)))
        if name == "pair":
            ac, ad, bc, bd = Mul(a,c), Mul(a,d), Mul(b,c), Mul(b,d)
            return _chain(specialize(s, "shuffle", ac, bd, ad, bc),
                CongAdd(EqRefl(Add(ac,ad)), specialize(s, "add_comm", bd, bc)),
                CongAdd(EqSym(specialize(s, "mul_add", a,c,d)), EqSym(specialize(s, "mul_add", b,c,d))),
                EqSym(specialize(s, "add_mul", a,b,Add(c,d))))
        if name == "scaled_shuffle":
            return _chain(specialize(s, "shuffle", a,Mul(two,b),c,Mul(two,d)),
                CongAdd(EqRefl(Add(a,c)), EqSym(specialize(s, "mul_add", two,b,d))))
        if name != "gap":
            raise QuadraticHeightError("unknown deterministic height helper")
        def exchange(x, y, z):
            return _chain(EqSym(specialize(s, "mul_assoc", x,y,z)),
                CongMul(specialize(s, "mul_comm", x,y), EqRefl(z)),
                specialize(s, "mul_assoc", y,x,z))
        ac, ad, bc, bd = Mul(a,c), Mul(a,d), Mul(b,c), Mul(b,d)
        X, Y, Z, W = ac, Mul(two,bd), Mul(two,ad), Mul(two,bc)
        left_expanded = Add(Y, Add(Add(X,Y), Add(Z,W)))
        right_expanded = Add(Add(X,Z), Add(W,Add(Y,Y)))
        left = CongAdd(EqRefl(Y), CongAdd(EqRefl(Add(X,Y)), specialize(s, "mul_add", two,ad,bc)))
        right = _chain(specialize(s, "add_mul", a,Mul(two,b),Add(c,Mul(two,d))),
            CongAdd(specialize(s, "mul_add", a,c,Mul(two,d)),
                specialize(s, "mul_add", Mul(two,b),c,Mul(two,d))),
            CongAdd(CongAdd(EqRefl(X), exchange(a,two,d)),
                CongAdd(specialize(s, "mul_assoc", two,b,c),
                    _chain(specialize(s, "mul_assoc", two,b,Mul(two,d)),
                        CongMul(EqRefl(two), exchange(b,two,d)), specialize(s, "double", Y)))))
        return _chain(left, _additive_equal(s,left_expanded,right_expanded), EqSym(right))
    return introduce(Scope(), (), HELPER_DEPENDENCIES[name], lambda s:
        introduce(s, ("a", "b", "c", "d"), (), main))


@dataclass(frozen=True)
class QuadraticHeightCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_quadratic_height(*, limits=None):
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from sqrt2_power_native import Basis, closed_formula, strip_target
    from peano_lab.library.proof_bundle import (BundleNode, ProofBundle, encode_formula,
        encode_proof_bundle, check_encoded_proof_bundle)
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise QuadraticHeightError("expected unchanged BinaryDAGLimits")
    before = quadratic_height_source_pins()
    target = frozen_quadratic_height_target()
    basis, nodes, total, deepest = Basis(), [], 0, 0
    def append(statement, dependencies, body):
        nonlocal total, deepest
        count, depth = _body_metrics(body, limits)
        total, deepest = total+count, max(deepest, depth)
        if total > limits.max_total_body_nodes or len(nodes)+1 > limits.max_nodes:
            raise QuadraticHeightError("QH001 unchanged aggregate constructor/node bound exceeded")
        _row_preflight(statement, body, limits)
        nodes.append(BundleNode(len(nodes), statement, tuple(dependencies), body))
    identifiers = {}
    for name, source in BASIS_SOURCES.items():
        law = basis.get(name)
        if law.formula != closed_formula(source):
            raise QuadraticHeightError("regenerated arithmetic law differs from original formula")
        identifiers[name] = len(nodes)
        append(law.formula, (), law.certificate)
    identifiers["double"] = len(nodes)
    append(closed_formula("forall x. 2*x=x+x"),
        (identifiers["mul_comm"], identifiers["mul_one"]), _double_body())
    for name, source, digest in HELPERS:
        statement = closed_formula(source)
        binders, premises, equation = strip_target(statement)
        if binders != 4 or premises or json_hash(encode_formula(statement)) != digest:
            raise QuadraticHeightError("frozen four-variable ring helper changed: " + name)
        identifiers[name] = len(nodes)
        append(statement, tuple(identifiers[d] for d in HELPER_DEPENDENCIES[name]), _helper_body(name))
    append(target, tuple(identifiers[name] for name, _, _ in HELPERS), _root_body())
    bundle = ProofBundle(tuple(nodes), len(nodes)-1)
    payload = encode_proof_bundle(bundle, target, limits=limits.bundle_limits())
    receipt = check_encoded_proof_bundle(payload, limits=limits.bundle_limits())
    if receipt.target != target or quadratic_height_source_pins() != before:
        raise QuadraticHeightError("QH001 source/target changed during canonical replay")
    provenance = dict(source_contract(), source_pins=before, original_HA_checked=True,
        canonical_bytes_replayed=True, empty_context=True,
        strategy="shared_arithmetic_laws_and_deterministic_additive_reassociation",
        internal_ring_helpers=[dict(name=n, source=s, target_ast_sha256=h) for n, s, h in HELPERS],
        ring_normalizer_calls=0, largest_algebra_helper_variable_count=4,
        generic_ring_retry=False, original_failed_ring_observation="shared-wave-quadratic-height-v1",
        helpers_counted_as_campaign_results=False, basis=basis.manifest(),
        new_axioms=[], external_certificate_references=[], independent_lean_checked=False)
    return QuadraticHeightCertificate(target, bundle, payload, receipt, deepest, provenance)
