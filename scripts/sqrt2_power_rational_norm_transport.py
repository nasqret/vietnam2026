"""RN001: rational quadratic norms respect positive-denominator representatives.

The two IRatEq premises include all denominator validity. Four actual ND0157
square witnesses produce equality of the rational norms, including negative
norms and noncanonical signed pairs. This is representative independence, not
the full real norm identity, IR031/IR032 closure, or an Alpha admission.

Every reused theorem is an actual body from one hash-pinned v28 ancestor cone.
The new root uses ordinary proof constructors and no ring normalizer or solver.
Only the root-owned bounded worker may execute proof production/checking.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sqrt2-power-rational-norm-transport-v1"
PARAMETERS = ("ap", "an", "bp", "bn", "d", "cp", "cn", "dp", "dn", "e", "a", "b", "c", "t")
EQUIVALENCE_SOURCES = (
    r"(~(d=0) /\ (~(e=0) /\ (ap*e+cn*d=an*e+cp*d)))",
    r"(~(d=0) /\ (~(e=0) /\ (bp*e+dn*d=bn*e+dp*d)))",
)
SQUARE_SOURCES = (
    "ap*ap+an*an=a+(ap*an+an*ap)",
    "bp*bp+bn*bn=b+(bp*bn+bn*bp)",
    "cp*cp+cn*cn=c+(cp*cn+cn*cp)",
    "dp*dp+dn*dn=t+(dp*dn+dn*dp)",
)
CONCLUSION_SOURCE = (
    r"(~(d*d=0) /\ (~(e*e=0) /\ "
    "(a*(e*e)+(2*t)*(d*d)=(2*b)*(e*e)+c*(d*d))))"
)
RATIONAL_NORM_TRANSPORT_SOURCE = (
    "forall " + " ".join(PARAMETERS) + ". "
    + " -> ".join((*EQUIVALENCE_SOURCES, *SQUARE_SOURCES, CONCLUSION_SOURCE))
)
RATIONAL_NORM_TRANSPORT_NAMED_SOURCE = (
    "forall " + " ".join(PARAMETERS) + ". "
    "IRatEq(ap,an,d,cp,cn,e) -> IRatEq(bp,bn,d,dp,dn,e) -> "
    "SignedDifferenceSquare(ap,an,a) -> SignedDifferenceSquare(bp,bn,b) -> "
    "SignedDifferenceSquare(cp,cn,c) -> SignedDifferenceSquare(dp,dn,t) -> "
    "IRatEq(a,2*b,d*d,c,2*t,e*e)"
)
RATIONAL_NORM_TRANSPORT_TARGET_SHA256 = "db34efff2aecd8c2f5afdb13cad631533c9dd9cbe2de2a878318cd31ac2290da"

V28_ARTIFACT = ROOT / "research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json"
V28_ARTIFACT_SIZE = 18977050
V28_ARTIFACT_SHA256 = "e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1"
ANCESTOR_IDS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 21, 22, 27, 28, 64, 90, 272,
                276, 632, 653, 685, 691, 693, 694, 695, 696, 697, 715)
ANCESTOR_IDS_SHA256 = "a0fc08c323d443ba84c5649f5638d0c2905bce605cae2ee98cca38d3affb4bd0"
SELECTED_ROWS_SHA256 = "1df63a017c45630769684bc33272d00db9ac41197c2bb608427ed2ba31aa5437"
SELECTED_ROWS_BYTES = 160288
ENDPOINTS = {
    2: dict(name="add_comm", dependencies=(0, 1),
        target_sha256="25b3cc29a1427896f1aa3935bc167b449d4501668be477e477180454ba292f94",
        row_sha256="6d0907be710b1670092723219ae751b63a7bc5129d7f262b42ac0f875fe213e3"),
    6: dict(name="mul_comm", dependencies=(4, 5),
        target_sha256="76c2bf4923416ae2e25c1cc7ab43a0d75f52f1db5294049c34473603fa74c15f",
        row_sha256="6490fef98e2a631be475df5192804d481eb7a93a282f06182ef8e0f471635fb9"),
    8: dict(name="mul_assoc", dependencies=(7,),
        target_sha256="2b6c71f127567e55b1b676ebe3416d1db37791bfd4536896d0f8c397645f128b",
        row_sha256="18518e0ebd3a7e013a9620a4f2e5535a6eb514512baab88fe084a53a7fee1a3c"),
    64: dict(name="mul_ne_zero", dependencies=(22,),
        target_sha256="0901c1f81fda303ffe9cb9129f9db72020058bb3253843b76e8392d6833080c7",
        row_sha256="97c9c43991e2c13b967d368cb4b63d51c473e695caa0c570c4c20a0048a9fa5c"),
    691: dict(name="gaussian_signed_square_functional", dependencies=(27,),
        target_sha256="4972d4705ed8d02c12ea797d6b5a01e5b054ec1d0e1e1d68f95cce74e77fe75f",
        row_sha256="57e0efe7c9cfb6b20282881599a28a58b662be2e83827bd18ebb27137ffecb89"),
    693: dict(name="gaussian_signed_square_integer_transport", dependencies=(653, 27, 3, 2, 632),
        target_sha256="5435757168b16fea9fd60f73064881636fcdd6f40b20a29c85878db05d439725",
        row_sha256="f12a2d5d75ff44383f147b2ea679211c60f8241145ca840c3f1dde606a2e8323"),
    715: dict(name="gaussian_signed_square_scaled", dependencies=(697, 4, 0),
        target_sha256="aa3486d9b44fbf1e223937296d096c5f25cc2c92eff2ffe319fa39013044100c",
        row_sha256="1d08d0e1cf20b54091315030017c356b521bf8e98359d9b22fadb7412b826c42"),
}
ROOT_DEPENDENCIES = (2, 6, 8, 64, 691, 693, 715)
PINNED_SOURCES = {
    "scripts/sqrt2_power_native.py": "9b51adc2699bf3c83c74749b9fc4723a8a1b8e234cef6f521a3f309fe646cc73",
    "scripts/sqrt2_power_binary_dag.py": "517535807fe06a317fae48c5fc5f47db944b0c32904fb8d02a0a1b102af12227",
    "scripts/sqrt2_power_definitions.py": "365f142974c3958aa5cad2430ed93fc3866e8abbadea0c357cb906574ff0220b",
    "scripts/sqrt2_power_quadratic_norm_product.py": "2a82e6a6de97f58b0e30fd7b7e8d6380b64e0ae4d0af91bd9df336f571a1df5a",
    "peano-lab/py/peano_lab/library/theorems.py": "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "peano-lab/py/peano_lab/library/defined_syntax.py": "86b3ee6dc17043553e730372ac0d9af884a3fb85ebe6a30813318871145fe903",
    "peano-lab/py/peano_lab/library/proof_bundle.py": "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4",
    "peano-lab/py/peano_lab/kernel/checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "peano-lab/py/peano_lab/kernel/formulas.py": "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    "peano-lab/py/peano_lab/kernel/proofs.py": "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    "peano-lab/py/peano_lab/kernel/terms.py": "f49313e209a8861918e3aaca38ddfb27f147f824308af699ab5cc1aafbb6dff5",
    "peano-lab/py/peano_lab/kernel/subst.py": "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
    "book/_static/constructive-jordan-campaign-v35/definitions.json": "32da2185fd21fb1d0b400404f9b832425a4c35e75be392a3f5b5f73f8464aebf",
}


class RationalNormTransportError(ValueError):
    """Changed exact target, actual source ancestor, or unchanged resource cap."""


def canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()


def json_hash(value):
    return sha256(canonical(value)).hexdigest()


def rational_norm_transport_source_pins():
    result = {}
    for name in sorted((*PINNED_SOURCES, "scripts/sqrt2_power_rational_norm_transport.py")):
        raw = (ROOT / name).read_bytes()
        digest = sha256(raw).hexdigest()
        if len(raw) > 16 * 1024**2 or name in PINNED_SOURCES and digest != PINNED_SOURCES[name]:
            raise RationalNormTransportError("rational norm source changed: " + name)
        result[name] = dict(bytes=len(raw), sha256=digest)
    return result


def rational_norm_definitions():
    """Existing conservative definitions only; no mutation of any registry."""
    from sqrt2_power_definitions import DEFINITIONS
    from sqrt2_power_quadratic_norm_product import existing_square_definition
    from peano_lab.library.defined_syntax import _definition
    square = existing_square_definition()
    definition = _definition(stable_id=square["id"], name=square["name"],
        parameters=tuple(square["parameters"]), template_source=square["template_source"],
        summary="Existing signed difference square, reused without changing its expansion.",
        category="existing_signed_integer_arithmetic", conceptual_dependencies=())
    return {"IRatValid": DEFINITIONS["IRatValid"], "IRatEq": DEFINITIONS["IRatEq"],
            "SignedDifferenceSquare": definition}


def frozen_rational_norm_transport_target():
    """Source/AST binding only; no prover, checker, or registry execution."""
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import closed_formula, strip_target
    from peano_lab.library.proof_bundle import encode_formula
    target = closed_formula(RATIONAL_NORM_TRANSPORT_SOURCE)
    if json_hash(encode_formula(target)) != RATIONAL_NORM_TRANSPORT_TARGET_SHA256:
        raise RationalNormTransportError("RN001 exact original target changed")
    named = parse_named(RATIONAL_NORM_TRANSPORT_NAMED_SOURCE, registry=rational_norm_definitions())
    binders, premises, _ = strip_target(target)
    if named != target or binders != 14 or len(premises) != 6:
        raise RationalNormTransportError("RN001 definition expansion/binder/premise shape changed")
    return target


def rational_norm_transport_manifest():
    return dict(code="RN001", schema=SCHEMA, source=RATIONAL_NORM_TRANSPORT_SOURCE,
        named_source=RATIONAL_NORM_TRANSPORT_NAMED_SOURCE,
        statement_ast_sha256=RATIONAL_NORM_TRANSPORT_TARGET_SHA256,
        parameters=list(PARAMETERS), premise_count=6, new_definitions=0,
        definition_ids=["ND0382", "ND0383", "ND0157"],
        coverage="rational_quadratic_norm_representation_independence",
        positive_denominators="explicit conjuncts of both IRatEq premises",
        arbitrary_signed_representatives=True, allows_negative_norm=True,
        original_HA_checked=False, independent_lean_checked=False,
        closes_IR031=False, closes_IR032=False, IR_parents_closed=0,
        library_admissions=0, real_interpretation=False, resource_fit=None)


def inert_selected_rows(artifact_path=V28_ARTIFACT):
    """Hash-pinned JSON inspection; actual ancestor bodies remain in each row."""
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE + 1)
    if len(raw) != V28_ARTIFACT_SIZE or sha256(raw).hexdigest() != V28_ARTIFACT_SHA256:
        raise RationalNormTransportError("sealed v28 bytes/hash changed")
    value = json.loads(raw)
    del raw
    if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
            or value[1] != 861 or len(value[3]) != 862):
        raise RationalNormTransportError("sealed v28 envelope changed")
    selected, pending = set(), list(ENDPOINTS)
    while pending:
        old = pending.pop()
        if old not in selected:
            selected.add(old)
            pending.extend(value[3][old][2])
    ids = tuple(sorted(selected))
    if ids != ANCESTOR_IDS or json_hash(ids) != ANCESTOR_IDS_SHA256:
        raise RationalNormTransportError("RN001 actual ancestor cone changed")
    rows = tuple(value[3][old] for old in ids)
    if json_hash(rows) != SELECTED_ROWS_SHA256 or len(canonical(rows)) != SELECTED_ROWS_BYTES:
        raise RationalNormTransportError("RN001 actual selected row bytes changed")
    for old, pin in ENDPOINTS.items():
        row = value[3][old]
        if (json_hash(row) != pin["row_sha256"] or json_hash(row[1]) != pin["target_sha256"]
                or tuple(row[2]) != pin["dependencies"]):
            raise RationalNormTransportError("RN001 actual endpoint pin changed")
    return ids, rows


@dataclass(frozen=True)
class RationalNormTransportCertificate:
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


def _root_body():
    """Seven ordinary dependency hypotheses, fourteen binders, six premises."""
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import (AndElimL, AndElimR, AndIntro, CongAdd, CongMul,
        EqRefl, EqSym, EqTrans, ForallIntro, Hyp, ImpElim, ImpIntro)
    from peano_lab.kernel.terms import Mul, Succ, Var, Zero
    ap, an, bp, bn, d, cp, cn, dp, dn, e, a, b, c, t = (
        Var(i) for i in reversed(range(14)))
    dd, ee, two = Mul(d, d), Mul(e, e), Succ(Succ(Zero()))

    def law(old):
        return Hyp(6 + len(ROOT_DEPENDENCIES) - 1 - ROOT_DEPENDENCIES.index(old))

    def apply(proof, *arguments):
        for argument in arguments:
            proof = ImpElim(proof, argument)
        return proof

    def comm(left, right):
        return instantiate(law(6), left, right)

    def add_comm(left, right):
        return instantiate(law(2), left, right)

    def assoc(left, middle, right):
        return instantiate(law(8), left, middle, right)

    def scaled_square(p, n, q, m, s, u, equivalence, first, second):
        # IRatEq uses p*e+m*d=n*e+q*d, while node693 expects
        # e*p+d*m=d*q+e*n. Every orientation change is explicit.
        balance = EqTrans(CongAdd(comm(e, p), comm(d, m)), EqTrans(
            AndElimR(AndElimR(equivalence)), EqTrans(
                CongAdd(comm(n, e), comm(q, d)), add_comm(Mul(e, n), Mul(d, q)))))
        square_left = apply(instantiate(law(715), p, n, s, e), first)
        square_right = apply(instantiate(law(715), q, m, u, d), second)
        transported = apply(instantiate(law(693), Mul(e, p), Mul(e, n),
            Mul(d, q), Mul(d, m), Mul(ee, s)), balance, square_left)
        return apply(instantiate(law(691), Mul(d, q), Mul(d, m),
                     Mul(ee, s), Mul(dd, u)), transported, square_right)

    # Exactly four ND0157 witnesses: Hyp3/2 for A/B and Hyp1/0 for C/T.
    square_a = scaled_square(ap, an, cp, cn, a, c, Hyp(5), Hyp(3), Hyp(1))
    square_b = scaled_square(bp, bn, dp, dn, b, t, Hyp(4), Hyp(2), Hyp(0))
    positive = EqTrans(comm(a, ee), EqTrans(square_a, comm(dd, c)))
    negative = EqTrans(assoc(two, t, dd), EqTrans(
        CongMul(EqRefl(two), comm(t, dd)), EqTrans(
            CongMul(EqRefl(two), EqSym(square_b)), EqTrans(
                CongMul(EqRefl(two), comm(ee, b)), EqSym(assoc(two, b, ee))))))
    cross = EqTrans(CongAdd(positive, negative), add_comm(Mul(c, dd), Mul(Mul(two, b), ee)))
    valid_d = AndElimL(Hyp(5))
    valid_e = AndElimL(AndElimR(Hyp(5)))
    valid_dd = apply(instantiate(law(64), d, d), valid_d, valid_d)
    valid_ee = apply(instantiate(law(64), e, e), valid_e, valid_e)
    result = AndIntro(valid_dd, AndIntro(valid_ee, cross))
    for _ in range(6):
        result = ImpIntro(result)
    for _ in range(14):
        result = ForallIntro(result)
    for _ in ROOT_DEPENDENCIES:
        result = ImpIntro(result)
    return result


def prove_rational_norm_transport(*, limits=None, artifact_path=V28_ARTIFACT):
    """Bounded root worker: replay the entire ordinary 29-node RN001 bundle."""
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from peano_lab.library.proof_bundle import (BundleNode, ProofBundle,
        check_encoded_proof_bundle, decode_formula, decode_proof, encode_formula,
        encode_proof, encode_proof_bundle)
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise RationalNormTransportError("expected unchanged BinaryDAGLimits")
    if limits.max_nodes < len(ANCESTOR_IDS) + 1:
        raise RationalNormTransportError("RN001 node budget exhausted before construction")
    before = rational_norm_transport_source_pins()
    target = frozen_rational_norm_transport_target()
    ids, rows = inert_selected_rows(artifact_path)
    if len(canonical(rows)) > limits.max_payload_bytes:
        raise RationalNormTransportError("actual RN001 ancestors exceed payload bound")
    remap = {old: new for new, old in enumerate(ids)}
    nodes, total, deepest = [], 0, 0
    for old, row in zip(ids, rows):
        formula = decode_formula(row[1], _depth=limits.max_depth)
        proof = decode_proof(row[3], _depth=limits.max_depth)
        if encode_formula(formula) != row[1] or encode_proof(proof) != row[3]:
            raise RationalNormTransportError("actual RN001 ancestor changed through codec")
        count, depth = _body_metrics(proof, limits)
        total, deepest = total + count, max(deepest, depth)
        if total > limits.max_total_body_nodes or row[0] < 8 * count + 16:
            raise RationalNormTransportError("actual RN001 ancestor exceeds body/fuel bound")
        _row_preflight(formula, proof, limits)
        nodes.append(BundleNode(remap[old], formula, tuple(remap[d] for d in row[2]), proof, row[0]))
    if total != 2438 or deepest != 40 or sum(len(row[2]) for row in rows) != 63:
        raise RationalNormTransportError("actual RN001 ancestor metrics changed")
    body = _root_body()
    count, depth = _body_metrics(body, limits)
    total, deepest = total + count, max(deepest, depth)
    if total > limits.max_total_body_nodes:
        raise RationalNormTransportError("RN001 aggregate ordinary body bound exceeded")
    _row_preflight(target, body, limits)
    dependencies = tuple(remap[old] for old in ROOT_DEPENDENCIES)
    root = len(nodes)
    nodes.append(BundleNode(root, target, dependencies, body))
    bundle = ProofBundle(tuple(nodes), root)
    payload = encode_proof_bundle(bundle, target, limits=limits.bundle_limits())
    receipt = check_encoded_proof_bundle(payload, limits=limits.bundle_limits())
    if receipt.target != target or json_hash(encode_formula(receipt.target)) != RATIONAL_NORM_TRANSPORT_TARGET_SHA256:
        raise RationalNormTransportError("canonical replay changed RN001 exact target")
    if rational_norm_transport_source_pins() != before:
        raise RationalNormTransportError("RN001 sources changed during proof production")
    # Reauthenticate the archive too, not just the small producer sources.
    inert_selected_rows(artifact_path)
    provenance = dict(code="RN001", schema=SCHEMA,
        coverage="rational_quadratic_norm_representation_independence", source_pins=before,
        original_target_source=RATIONAL_NORM_TRANSPORT_SOURCE,
        named_source=RATIONAL_NORM_TRANSPORT_NAMED_SOURCE,
        original_target_ast_sha256=RATIONAL_NORM_TRANSPORT_TARGET_SHA256,
        original_HA_checked=True, canonical_bytes_replayed=True, empty_context=True,
        v28_artifact=dict(path=str(V28_ARTIFACT.relative_to(ROOT)), bytes=V28_ARTIFACT_SIZE,
                          sha256=V28_ARTIFACT_SHA256),
        actual_ancestor_ids=list(ids), actual_ancestor_nodes=28, actual_ancestor_body_nodes=2438,
        selected_rows_sha256=SELECTED_ROWS_SHA256, root_dependencies=list(dependencies),
        reused_endpoints={str(old): dict(pin) for old, pin in ENDPOINTS.items()},
        definition_ids=["ND0382", "ND0383", "ND0157"], new_definitions=0,
        arbitrary_signed_representatives=True, allows_negative_norm=True,
        positive_denominators="actual IRatEq conjuncts, squared by actual node64",
        internal_ring_helpers=[], ring_normalizer_calls=0, solver_calls=0,
        external_certificate_references=[], new_axioms=[], real_interpretation=False,
        IR_parents_closed=0, closes_IR031=False, closes_IR032=False,
        library_admissions=0, independent_lean_checked=False)
    return RationalNormTransportCertificate(target, bundle, payload, receipt, deepest, provenance)
