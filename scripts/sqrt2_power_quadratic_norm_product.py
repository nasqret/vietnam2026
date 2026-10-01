"""SN003: signed integer norm multiplicativity for Z[sqrt(2)], not GNorm.

Six premises are instances of existing ND0157 SignedDifferenceSquare. Two
separate balance premises describe the real and radical product coordinates,
allowing arbitrary nonnormalized output representatives. Actual sealed node693
transports their squares. No new definition, theorem axiom, external receipt,
solver import, or rational/real IR031 conclusion is used.

The root owns every proof/solver/compiler worker. Imports, source construction,
and inert source-cone inspection do not run a proof producer. Native production
uses three small closed ring identities (at most four variables), not a ring
normalization of the eighteen-variable target. Limits remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sqrt2-power-quadratic-norm-product-v1"
PARAMETERS = ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn",
              "rp", "rn", "sp", "sn", "a", "b", "c", "d", "r", "t")
SQUARE_SOURCES = (
    "ap*ap+an*an=a+(ap*an+an*ap)",
    "bp*bp+bn*bn=b+(bp*bn+bn*bp)",
    "cp*cp+cn*cn=c+(cp*cn+cn*cp)",
    "dp*dp+dn*dn=d+(dp*dn+dn*dp)",
    "rp*rp+rn*rn=r+(rp*rn+rn*rp)",
    "sp*sp+sn*sn=t+(sp*sn+sn*sp)",
)
REAL_PRODUCT_BALANCE_SOURCE = (
    "rp+((ap*cn+an*cp)+2*(bp*dn+bn*dp))="
    "((ap*cp+an*cn)+2*(bp*dp+bn*dn))+rn"
)
RADICAL_PRODUCT_BALANCE_SOURCE = (
    "sp+((ap*dn+an*dp)+(bp*cn+bn*cp))="
    "((ap*dp+an*dn)+(bp*cp+bn*cn))+sn"
)
CONCLUSION_SOURCE = "r+2*(a*d+b*c)=(a*c+(2*2)*(b*d))+2*t"
QUADRATIC_NORM_PRODUCT_SOURCE = (
    "forall " + " ".join(PARAMETERS) + ". "
    + " -> ".join((*SQUARE_SOURCES, REAL_PRODUCT_BALANCE_SOURCE,
                   RADICAL_PRODUCT_BALANCE_SOURCE, CONCLUSION_SOURCE))
)
QUADRATIC_NORM_PRODUCT_TARGET_SHA256 = "e123c3a589c565bfb3da565b09d0d7fd4e0ca431f884f790f02899bc10711bfa"

# These are INTERNAL normalization nodes, not additional campaign completions.
# All numerals are ordinary 0/S syntax after the unchanged parser elaborates.
HELPERS = (
    dict(name="double", source="forall x. x+x=2*x", binders=1,
         target_sha256="cd36bfaa5ff0160749574a8ae99a7aa70e2453a9f928e527e717d9a375eeaf8d"),
    dict(name="double_scaled_cross", binders=4,
         source="forall p n q m. (p*(2*q)+n*(2*m))+(p*(2*q)+n*(2*m))=(2*2)*(p*q+n*m)",
         target_sha256="4b0971d29def27352c65230eacb56706426b53581e3a1ceb14b090776995e495"),
    dict(name="scale_sum_swap", source="forall x y. 2*(x+2*y)=(2*2)*y+2*x", binders=2,
         target_sha256="a70c42b35254d29e50b408dfa1fce80990fa45d25709b5bf7aed93b8eb0ddb69"),
)

V28_ARTIFACT = ROOT / "research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json"
V28_ARTIFACT_SIZE = 18977050
V28_ARTIFACT_SHA256 = "e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1"
ANCESTOR_IDS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 27, 28, 90, 272, 276, 277,
                632, 653, 685, 693, 694, 695, 696, 697, 698, 699, 700, 704,
                705, 706, 707, 708, 715)
ANCESTOR_IDS_SHA256 = "7f473b03ee2f3b8bca7aedd5362d9b20a5a60adb52043de686d7ac35d9335427"
SELECTED_ROWS_SHA256 = "05233b3d2a1830daea1343d5bc6db22aee9c162f328284d4696192bfd3f46cea"
ENDPOINTS = {
    272: dict(name="add_cross_sum_chain", dependencies=(3, 2, 28),
        target_sha256="f3ebddbe02519999f5bf1d4158a314f67a7e4f1ced5e70fbc52c6affe31be447",
        row_sha256="3a67ae0fad649f8046ca4fab78f3d22057d31de43df047aab9175ddffb85d4d1"),
    693: dict(name="gaussian_signed_square_integer_transport", dependencies=(653, 27, 3, 2, 632),
        target_sha256="5435757168b16fea9fd60f73064881636fcdd6f40b20a29c85878db05d439725",
        row_sha256="f12a2d5d75ff44383f147b2ea679211c60f8241145ca840c3f1dde606a2e8323"),
    697: dict(name="gaussian_signed_square_product", dependencies=(694, 695, 696),
        target_sha256="daae2a73cbcda62a388c64db597b790716b53175a664013a7318815066a3089d",
        row_sha256="1b139f3995187da519bb035255129ecebf06568ece8dcacc2cea1e6471799239"),
    700: dict(name="gaussian_signed_square_sum_compensation", dependencies=(698, 699, 27, 3, 2, 632),
        target_sha256="40f2a2b866185c8e39e6f9918f3e58b485bb5eabdbc86b24f89186e145105362",
        row_sha256="1bb291e4269d0fa79cb40c4c7879b13ad75f66ce3c477b278cbb267513182060"),
    708: dict(name="gaussian_signed_product_cross_interchange", dependencies=(707, 706),
        target_sha256="d8d466bbc7cf9ef4a1326944da4b4c547e1979737793ad4af83a58a74fb8310c",
        row_sha256="2ac53cf70c1db49e0b1bdf379eba6f9400fa385fac40a3f6f3c14cffb6431969"),
    715: dict(name="gaussian_signed_square_scaled", dependencies=(697, 4, 0),
        target_sha256="aa3486d9b44fbf1e223937296d096c5f25cc2c92eff2ffe319fa39013044100c",
        row_sha256="1d08d0e1cf20b54091315030017c356b521bf8e98359d9b22fadb7412b826c42"),
}
DEFINITION_PARENT = "book/_static/constructive-jordan-campaign-v35/definitions.json"
DEFINITION_TEMPLATE = "((((p) * (p))) + (((n) * (n)))) = ((s) + (((((p) * (n))) + (((n) * (p))))))"
DEFINITION_EXPANSION_SHA256 = "747d061c8dc5bc4b70dc2664441a3a0983b4b5d0e8d16440d0a3e37cf85fa933"
PINNED_SOURCES = {
    "scripts/sqrt2_power_native.py": "9b51adc2699bf3c83c74749b9fc4723a8a1b8e234cef6f521a3f309fe646cc73",
    "scripts/sqrt2_power_binary_dag.py": "517535807fe06a317fae48c5fc5f47db944b0c32904fb8d02a0a1b102af12227",
    "peano-lab/py/peano_lab/library/theorems.py": "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "peano-lab/py/peano_lab/library/gaussian_euclidean_candidate.py": "de2b9a14a7cf532cbe583d5972afa4f423703c9a5ba780b85b8f9c3c21cee4d8",
    "peano-lab/py/peano_lab/library/defined_syntax.py": "86b3ee6dc17043553e730372ac0d9af884a3fb85ebe6a30813318871145fe903",
    "peano-lab/py/peano_lab/library/proof_bundle.py": "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4",
    "peano-lab/py/peano_lab/engine/ring.py": "7ba5c4b4085725677ba984afa8a50cee8061ce9ba333b644993ecff5fd5f249e",
    "scripts/constructive_lower_layer_definitions.py": "b335420c5c7b24f1981286e5da4716103ce00e6270b9a81951ec1af69302f245",
    DEFINITION_PARENT: "32da2185fd21fb1d0b400404f9b832425a4c35e75be392a3f5b5f73f8464aebf",
}
ROOT_DEPENDENCIES = (693, 697, 700, 708, 715, 272,
                     "double", "double_scaled_cross", "scale_sum_swap")


class QuadraticNormProductError(ValueError):
    """Fail-closed definition, source, exact statement, body or resource error."""


def canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()


def json_hash(value):
    return sha256(canonical(value)).hexdigest()


def norm_product_source_pins():
    """Small sources only; the 19MB sealed archive has its separate exact pin."""
    extra = "scripts/sqrt2_power_quadratic_norm_product.py"
    result = {}
    for name in sorted((*PINNED_SOURCES, extra)):
        raw = (ROOT / name).read_bytes()
        digest = sha256(raw).hexdigest()
        if len(raw) > 16 * 1024**2 or name in PINNED_SOURCES and digest != PINNED_SOURCES[name]:
            raise QuadraticNormProductError("norm-product source changed: " + name)
        result[name] = dict(bytes=len(raw), sha256=digest)
    return result


def existing_square_definition():
    """Inspect ND0157 literally. This neither registers nor trusts a theorem."""
    raw = (ROOT / DEFINITION_PARENT).read_bytes()
    if sha256(raw).hexdigest() != PINNED_SOURCES[DEFINITION_PARENT]:
        raise QuadraticNormProductError("existing definition parent changed")
    rows = [r for r in json.loads(raw)["reviewed_definitions"] if r["id"] == "ND0157"]
    expected = dict(name="SignedDifferenceSquare", parameters=["p", "n", "s"],
                    arity=3, dependencies=[], expansion_sha256=DEFINITION_EXPANSION_SHA256)
    if (len(rows) != 1 or any(rows[0].get(k) != v for k, v in expected.items())
            or sha256(DEFINITION_TEMPLATE.encode()).hexdigest() != DEFINITION_EXPANSION_SHA256):
        raise QuadraticNormProductError("existing ND0157 definition/expansion changed")
    return dict(id="ND0157", template_source=DEFINITION_TEMPLATE, **expected)


def source_contract():
    return dict(code="SN003", source=QUADRATIC_NORM_PRODUCT_SOURCE,
        statement_ast_sha256=QUADRATIC_NORM_PRODUCT_TARGET_SHA256,
        parameters=list(PARAMETERS), premise_count=8,
        signed_square_definition=existing_square_definition(),
        real_product_balance_source=REAL_PRODUCT_BALANCE_SOURCE,
        radical_product_balance_source=RADICAL_PRODUCT_BALANCE_SOURCE,
        coverage="full_signed_integer_norm_multiplicativity",
        arbitrary_output_representatives=True, output_square_transport_node=693,
        internal_ring_helpers=[dict(row) for row in HELPERS], helpers_counted_as_campaign_results=False,
        authority="frozen_source_not_a_certificate", original_HA_checked=False,
        closes_IR031=False, closes_IR046=False, rational_or_real_claim=False,
        Gaussian_GNorm_claim=False, resource_fit=None)


def _signed_square(p, n, s):
    from peano_lab.kernel.formulas import Eq
    from peano_lab.kernel.terms import Add, Mul
    return Eq(Add(Mul(p, p), Mul(n, n)), Add(s, Add(Mul(p, n), Mul(n, p))))


def frozen_quadratic_norm_product_target():
    """Original parser/AST binding only; does not produce or check a proof."""
    from sqrt2_power_native import closed_formula, strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
    from peano_lab.library.proof_bundle import encode_formula
    existing_square_definition()
    target = closed_formula(QUADRATIC_NORM_PRODUCT_SOURCE)
    if json_hash(encode_formula(target)) != QUADRATIC_NORM_PRODUCT_TARGET_SHA256:
        raise QuadraticNormProductError("SN003 exact original target AST changed")
    binders, premises, conclusion = strip_target(target)
    if binders != 18 or len(premises) != 8:
        raise QuadraticNormProductError("SN003 binder/premise shape changed")
    ap, an, bp, bn, cp, cn, dp, dn, rp, rn, sp, sn, a, b, c, d, r, t = (
        Var(i) for i in reversed(range(18)))
    squares = ((ap, an, a), (bp, bn, b), (cp, cn, c), (dp, dn, d),
               (rp, rn, r), (sp, sn, t))
    if premises[:6] != [_signed_square(*args) for args in squares]:
        raise QuadraticNormProductError("an SN003 square premise differs from ND0157")
    two = Succ(Succ(Zero()))
    def pair(p, n, q, m):
        return Add(Mul(p, q), Mul(n, m)), Add(Mul(p, m), Mul(n, q))
    U, V, W, X = pair(ap, an, cp, cn), pair(bp, bn, dp, dn), pair(ap, an, dp, dn), pair(bp, bn, cp, cn)
    R = tuple(Add(U[i], Mul(two, V[i])) for i in range(2))
    I = tuple(Add(W[i], X[i]) for i in range(2))
    expected_product = [Eq(Add(rp, R[1]), Add(R[0], rn)), Eq(Add(sp, I[1]), Add(I[0], sn))]
    expected_conclusion = Eq(Add(r, Mul(two, Add(Mul(a, d), Mul(b, c)))),
        Add(Add(Mul(a, c), Mul(Mul(two, two), Mul(b, d))), Mul(two, t)))
    if premises[6:] != expected_product or conclusion != expected_conclusion:
        raise QuadraticNormProductError("SN003 signed product orientation/conclusion changed")
    return target


def inert_selected_rows(artifact_path=V28_ARTIFACT):
    """Select pinned inert JSON rows; no ordinary decoder or checker is run."""
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE + 1)
    if len(raw) != V28_ARTIFACT_SIZE or sha256(raw).hexdigest() != V28_ARTIFACT_SHA256:
        raise QuadraticNormProductError("sealed v28 artifact size/hash changed")
    value = json.loads(raw)
    del raw
    if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
            or value[1] != 861 or len(value[3]) != 862):
        raise QuadraticNormProductError("sealed v28 envelope changed")
    selected, pending = set(), list(ENDPOINTS)
    while pending:
        node_id = pending.pop()
        if node_id not in selected:
            selected.add(node_id)
            pending.extend(value[3][node_id][2])
    ids = tuple(sorted(selected))
    if ids != ANCESTOR_IDS or json_hash(ids) != ANCESTOR_IDS_SHA256:
        raise QuadraticNormProductError("actual signed-product ancestor cone changed")
    for node_id, pin in ENDPOINTS.items():
        row = value[3][node_id]
        if (json_hash(row) != pin["row_sha256"] or json_hash(row[1]) != pin["target_sha256"]
                or tuple(row[2]) != pin["dependencies"]):
            raise QuadraticNormProductError("selected signed-product endpoint changed")
    rows = tuple(value[3][i] for i in ids)
    if json_hash(rows) != SELECTED_ROWS_SHA256 or len(canonical(rows)) != 353005:
        raise QuadraticNormProductError("selected actual row bytes changed")
    return ids, rows


@dataclass(frozen=True)
class NormProductCone:
    nodes: tuple
    original_ids: tuple
    endpoints: dict
    body_nodes: int
    max_depth: int


@dataclass(frozen=True)
class QuadraticNormProductCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict

    @property
    def payload_sha256(self):
        return sha256(self.payload.encode()).hexdigest()

    @property
    def target_ast_sha256(self):
        from peano_lab.library.proof_bundle import encode_formula
        return json_hash(encode_formula(self.target))


def load_norm_product_cone(artifact_path=V28_ARTIFACT, *, limits=None):
    """Root worker: decode 33 actual rows; acceptance waits for final replay."""
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from peano_lab.library.proof_bundle import BundleNode, decode_formula, decode_proof, encode_formula, encode_proof
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise QuadraticNormProductError("expected unchanged pilot limits")
    ids, rows = inert_selected_rows(artifact_path)
    if len(ids) > limits.max_nodes or len(canonical(rows)) > limits.max_payload_bytes:
        raise QuadraticNormProductError("selected cone exceeds original local limits")
    remap = {old: new for new, old in enumerate(ids)}
    nodes, count, deepest = [], 0, 0
    for old, row in zip(ids, rows):
        target, body = decode_formula(row[1], _depth=limits.max_depth), decode_proof(row[3], _depth=limits.max_depth)
        if encode_formula(target) != row[1] or encode_proof(body) != row[3]:
            raise QuadraticNormProductError("selected actual row changed through the ordinary codec")
        local_count, local_depth = _body_metrics(body, limits)
        count += local_count
        deepest = max(deepest, local_depth)
        if count > limits.max_total_body_nodes or row[0] < 8 * local_count + 16:
            raise QuadraticNormProductError("selected cone exceeds body/fuel bounds")
        _row_preflight(target, body, limits)
        nodes.append(BundleNode(remap[old], target, tuple(remap[d] for d in row[2]), body, row[0]))
    if count != 4468 or deepest != 84 or sum(len(row[2]) for row in rows) != 106:
        raise QuadraticNormProductError("actual source-cone structural metrics changed")
    return NormProductCone(tuple(nodes), ids, {old: remap[old] for old in ENDPOINTS}, count, deepest)


def _helper_certificate(row, basis):
    from sqrt2_power_native import closed_formula, strip_target, ring, close_proof
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target = closed_formula(row["source"])
    if json_hash(encode_formula(target)) != row["target_sha256"]:
        raise QuadraticNormProductError("small internal helper target changed")
    binders, premises, equation = strip_target(target)
    if binders != row["binders"] or binders > 4 or premises or type(equation) is not Eq:
        raise QuadraticNormProductError("ring helper scope changed")
    return target, close_proof(ring(equation, basis), binders, premises)


def _root_body():
    """Nine ordered dependency hypotheses, eighteen binders, eight premises.

    No ring normalization is performed here. Every large-term occurrence is a
    substitution into a small existing universal equation or implication.
    """
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import (AndElimL, AndElimR, CongAdd, CongMul,
        EqRefl, EqSym, EqTrans, ForallIntro, Hyp, ImpElim, ImpIntro)
    from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
    values = tuple(Var(i) for i in reversed(range(18)))
    ap, an, bp, bn, cp, cn, dp, dn, rp, rn, sp, sn, a, b, c, d, r, t = values
    two = Succ(Succ(Zero()))
    four = Mul(two, two)
    def law(name):
        return Hyp(8 + len(ROOT_DEPENDENCIES) - 1 - ROOT_DEPENDENCIES.index(name))
    def apply(proof, *arguments):
        for argument in arguments:
            proof = ImpElim(proof, argument)
        return proof
    def product(first, second):
        p, n = first
        q, m = second
        return Add(Mul(p, q), Mul(n, m)), Add(Mul(p, m), Mul(n, q))
    A, B, C, D = (ap, an), (bp, bn), (cp, cn), (dp, dn)
    U, V, W, X = product(A, C), product(B, D), product(A, D), product(B, C)
    R = tuple(Add(U[i], Mul(two, V[i])) for i in range(2))
    I = tuple(Add(W[i], X[i]) for i in range(2))
    uv, wx = product(U, V), product(W, X)
    u, v, w, x = Mul(a, c), Mul(b, d), Mul(a, d), Mul(b, c)
    total_real, total_imag = Add(u, Mul(four, v)), Add(w, x)
    # Hyp0/1 are the exact radical/real output balances. Hyp2/3 are
    # output squares; Hyp4..7 are D,C,B,A squares, respectively.
    square_r = apply(instantiate(law(693), rp, rn, *R, r), Hyp(1), Hyp(3))
    square_i = apply(instantiate(law(693), sp, sn, *I, t), Hyp(0), Hyp(2))
    square_u = apply(instantiate(law(697), *A, *C, a, c), Hyp(7), Hyp(5))
    square_v = apply(instantiate(law(697), *B, *D, b, d), Hyp(6), Hyp(4))
    square_w = apply(instantiate(law(697), *A, *D, a, d), Hyp(7), Hyp(4))
    square_x = apply(instantiate(law(697), *B, *C, b, c), Hyp(6), Hyp(5))
    square_twov = apply(instantiate(law(715), *V, v, two), square_v)
    raw_real = apply(instantiate(law(700), *U, Mul(two, V[0]), Mul(two, V[1]),
                                 u, Mul(four, v), r), square_u, square_twov, square_r)
    real_negative = instantiate(law("double_scaled_cross"), *U, V[1], V[0])
    real_positive = instantiate(law("double_scaled_cross"), *U, *V)
    real_equation = EqTrans(EqSym(CongAdd(EqRefl(r), real_negative)),
                           EqTrans(raw_real, CongAdd(EqRefl(total_real), real_positive)))

    cross = instantiate(law(708), *A, *B, *C, *D)
    raw_imag = apply(instantiate(law(700), *W, *X, w, x, t), square_w, square_x, square_i)
    imag_negative = EqTrans(instantiate(law("double"), wx[1]),
                            CongMul(EqRefl(two), EqSym(AndElimR(cross))))
    imag_positive = EqTrans(instantiate(law("double"), wx[0]),
                            CongMul(EqRefl(two), EqSym(AndElimL(cross))))
    imag_equation = EqTrans(EqSym(CongAdd(EqRefl(t), imag_negative)),
                           EqTrans(raw_imag, CongAdd(EqRefl(total_imag), imag_positive)))

    # r+4N=U+4P and t+2N=V+2P. Scale the second equation, reverse
    # its orientation, then use the existing cancellative cross-sum theorem.
    reverse_scaled_imag = EqTrans(
        EqSym(instantiate(law("scale_sum_swap"), total_imag, uv[0])),
        EqTrans(CongMul(EqRefl(two), EqSym(imag_equation)),
                instantiate(law("scale_sum_swap"), t, uv[1])))
    result = apply(instantiate(law(272), r, total_real, Mul(four, uv[1]),
                               Mul(four, uv[0]), Mul(two, total_imag), Mul(two, t)),
                   real_equation, reverse_scaled_imag)
    for _ in range(8):
        result = ImpIntro(result)
    for _ in range(18):
        result = ForallIntro(result)
    for _ in ROOT_DEPENDENCIES:
        result = ImpIntro(result)
    return result


def prove_quadratic_norm_product(basis=None, *, limits=None, artifact_path=V28_ARTIFACT):
    """Root worker only: complete SN003 from actual proof bodies, fixed limits."""
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from sqrt2_power_native import Basis
    from peano_lab.library.proof_bundle import (BundleNode, ProofBundle,
        check_encoded_proof_bundle, encode_formula, encode_proof, encode_proof_bundle)
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise QuadraticNormProductError("expected unchanged pilot resource limits")
    before = norm_product_source_pins()
    target = frozen_quadratic_norm_product_target()
    cone = load_norm_product_cone(artifact_path, limits=limits)
    if len(cone.nodes) + len(HELPERS) + 1 > limits.max_nodes:
        raise QuadraticNormProductError("SN003 node budget exhausted before construction")
    literal_basis = Basis()
    if basis is None:
        basis = literal_basis
    if (type(basis) is not Basis or basis.source_sha256 != literal_basis.source_sha256
            or basis.specs != literal_basis.specs):
        raise QuadraticNormProductError("wrong fixed fifteen-entry arithmetic Basis")
    nodes = list(cone.nodes)
    total, deepest = cone.body_nodes, cone.max_depth
    encoded_bytes = len(canonical(inert_selected_rows(artifact_path)[1])) + 128
    def append_node(formula, dependencies, proof):
        nonlocal total, deepest, encoded_bytes
        if len(nodes) >= limits.max_nodes or len(set(dependencies)) != len(dependencies):
            raise QuadraticNormProductError("new norm-product node/dependency budget failure")
        if any(type(i) is not int or not 0 <= i < len(nodes) for i in dependencies):
            raise QuadraticNormProductError("non-topological norm-product dependency")
        count, depth = _body_metrics(proof, limits)
        total += count
        deepest = max(deepest, depth)
        if total > limits.max_total_body_nodes:
            raise QuadraticNormProductError("SN003 aggregate ordinary body budget exhausted")
        _row_preflight(formula, proof, limits)
        row_bytes = len(canonical([8 * count + 16, encode_formula(formula), list(dependencies), encode_proof(proof)])) + 1
        encoded_bytes += row_bytes
        if encoded_bytes > limits.max_payload_bytes:
            raise QuadraticNormProductError("SN003 aggregate canonical payload budget exhausted")
        node_id = len(nodes)
        nodes.append(BundleNode(node_id, formula, tuple(dependencies), proof))
        return node_id
    helper_ids = {}
    for row in HELPERS:
        helper_target, helper_proof = _helper_certificate(row, basis)
        helper_ids[row["name"]] = append_node(helper_target, (), helper_proof)
    dependencies = tuple(cone.endpoints[item] if type(item) is int else helper_ids[item]
                         for item in ROOT_DEPENDENCIES)
    root = append_node(target, dependencies, _root_body())
    if encoded_bytes + len(canonical(encode_formula(target))) > limits.max_payload_bytes:
        raise QuadraticNormProductError("SN003 canonical envelope exceeds unchanged budget")
    bundle = ProofBundle(tuple(nodes), root)
    payload = encode_proof_bundle(bundle, target, limits=limits.bundle_limits())
    receipt = check_encoded_proof_bundle(payload, limits=limits.bundle_limits())
    if receipt.target != target or json_hash(encode_formula(receipt.target)) != QUADRATIC_NORM_PRODUCT_TARGET_SHA256:
        raise QuadraticNormProductError("fresh canonical replay changed SN003 target")
    if norm_product_source_pins() != before:
        raise QuadraticNormProductError("SN003 sources changed during proof generation")
    provenance = dict(code="SN003", schema=SCHEMA,
        coverage="full_signed_integer_norm_multiplicativity", source_pins=before,
        original_target_source=QUADRATIC_NORM_PRODUCT_SOURCE,
        original_target_ast_sha256=QUADRATIC_NORM_PRODUCT_TARGET_SHA256,
        original_HA_checked=True, canonical_bytes_replayed=True, empty_context=True,
        v28_artifact=dict(path=str(V28_ARTIFACT.relative_to(ROOT)), bytes=V28_ARTIFACT_SIZE,
                          sha256=V28_ARTIFACT_SHA256),
        actual_ancestor_ids=list(cone.original_ids), selected_rows_sha256=SELECTED_ROWS_SHA256,
        actual_ancestor_nodes=len(cone.nodes), actual_ancestor_body_nodes=cone.body_nodes,
        reused_endpoints={str(i): dict(pin) for i, pin in ENDPOINTS.items()},
        arbitrary_output_representatives=True, output_square_transport_node=693,
        signed_square_definition=existing_square_definition(),
        internal_ring_helpers=[dict(row) for row in HELPERS], helpers_counted_as_campaign_results=False,
        basis=basis.manifest(), external_certificate_references=[], new_axioms=[],
        IR_parents_closed=0, closes_IR031=False, closes_IR046=False,
        rational_or_real_claim=False, Gaussian_GNorm_claim=False,
        library_admissions=0, independent_lean_checked=False)
    return QuadraticNormProductCertificate(target, bundle, payload, receipt, deepest, provenance)
