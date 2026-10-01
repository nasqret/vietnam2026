"""SN001: the exact signed quadratic norm-zero bridge, in ordinary HA.

This reuses registered ND0157, the checked IR016 producer, and actual ordinary
proof bodies from a small ancestor cone in the sealed v28 archive. No receipt,
definition, host calculation, or theorem name is accepted as a proof premise.
Run proof production only inside the root-owned single-worker resource guard.
This is supporting universal algebra, not full IR030/IR032 or irrationality.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path

import sqrt2_power_even_square as even
from sqrt2_power_binary_dag import (
    BinaryDAGLimits, ROOT, SOURCE_PINS, _body_metrics, _row_preflight,
    formula_sha256,
)
from sqrt2_power_native import Basis, closed_formula, instantiate
from peano_lab.kernel.formulas import And, Eq, Formula
from peano_lab.kernel.proofs import (
    AndElimL, AndElimR, AndIntro, Axiom, CongAdd, CongMul, Cut, EqRefl,
    EqSym, EqTrans, ExistsElim, ForallIntro, Hyp, ImpElim, ImpIntro, OrElim,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.library.defined_syntax import _definition
from peano_lab.library.proof_bundle import (
    BundleNode, ProofBundle, check_encoded_proof_bundle, decode_formula,
    decode_proof, encode_formula, encode_proof, encode_proof_bundle,
)

SIGNED_NORM_SOURCE = (
    "forall ap an bp bn s t. "
    "ap*ap+an*an=s+(ap*an+an*ap) -> "
    "bp*bp+bn*bn=t+(bp*bn+bn*bp) -> "
    "s=(S(S 0))*t -> (ap=an /\\ bp=bn)"
)
SIGNED_NORM_TARGET_SHA256 = "c948aa0e7350e5c51c464721215573a489b0921c9d1a3263c9c5181f20164941"
V28_ARTIFACT = ROOT / "research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json"
V28_ARTIFACT_SIZE = 18977050
V28_ARTIFACT_SHA256 = "e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1"
ANCESTOR_IDS = (0, 1, 2, 3, 4, 5, 6, 7, 11, 27, 41, 47, 90, 278, 632,
                637, 638, 639, 640, 641, 655, 691)
ANCESTOR_IDS_SHA256 = "6c2e36b1fdf8104d5726de66123de4a7ea5dcc4f580d3cdf0c9befde587b29de"
DEFINITION_PARENT = "book/_static/constructive-jordan-campaign-v35/definitions.json"
DEFINITION_TEMPLATE = "((((p) * (p))) + (((n) * (n)))) = ((s) + (((((p) * (n))) + (((n) * (p))))))"
DEFINITION_EXPANSION_SHA256 = "747d061c8dc5bc4b70dc2664441a3a0983b4b5d0e8d16440d0a3e37cf85fa933"
PINNED_SOURCES = {
    "scripts/sqrt2_power_even_square.py": "5213db18c72a63539cb92d148e1b26e6822877298ec73efc790f4259ecbf0d1f",
    "peano-lab/py/peano_lab/library/matrix_lattice_data_candidate.py": "4dd9eff374a53f9a1b99e8754351de66859cf731c41196d067e31666e45b3c07",
    "peano-lab/py/peano_lab/library/four_square_identity_candidate.py": "be4512db0d1cba26c5c61f282e7e7259fbbae3307e760657e4be5b1a44adf300",
    "peano-lab/py/peano_lab/library/gaussian_euclidean_candidate.py": "de2b9a14a7cf532cbe583d5972afa4f423703c9a5ba780b85b8f9c3c21cee4d8",
    "scripts/constructive_lower_layer_definitions.py": "b335420c5c7b24f1981286e5da4716103ce00e6270b9a81951ec1af69302f245",
    DEFINITION_PARENT: "32da2185fd21fb1d0b400404f9b832425a4c35e75be392a3f5b5f73f8464aebf",
}
ENDPOINTS = {
    655: {
        "name": "matrix_lattice_absolute_difference_exists",
        "source": r"forall p n. exists D. (p=n+D \/ n=p+D)",
        "dependencies": (47, 41, 2),
        "target_sha256": "3adbe96b06354d59eeb637b90460c099bc21a27f1cdc3776e76951c973825fbe",
        "row_sha256": "e091a29613499a60064500e2bb13e7d24121378c9d353e3c5e1dcd0393eb9e20",
    },
    641: {
        "name": "four_square_absolute_square_balance",
        "source": r"forall p n D. (p=n+D \/ n=p+D) -> p*p+n*n=D*D+(p*n+n*p)",
        "dependencies": (639, 640),
        "target_sha256": "b671a1754d53797bbe319b3135a384f2f6dcb9f0ca7a7134bc8d301033b65955",
        "row_sha256": "66c5cf9b3fd3fc7c4340bd15e29f988aafb370792dd4986a752745b947e9be23",
    },
    691: {
        "name": "gaussian_signed_square_functional",
        "source": "forall p n s t. p*p+n*n=s+(p*n+n*p) -> p*p+n*n=t+(p*n+n*p) -> s=t",
        "dependencies": (27,),
        "target_sha256": "4972d4705ed8d02c12ea797d6b5a01e5b054ec1d0e1e1d68f95cce74e77fe75f",
        "row_sha256": "57e0efe7c9cfb6b20282881599a28a58b662be2e83827bd18ebb27137ffecb89",
    },
}
MUL_ASSOC_LITERAL_SHA256 = "02cba3297fd04616267d496eed53360b9eeca6d892a5f1c117f0a50f23653814"


class SignedNormError(ValueError):
    """Exact source, definition, statement, dependency, or budget mismatch."""


@dataclass(frozen=True)
class SignedSquareCone:
    """Decoded data, not a proof-acceptance receipt."""

    nodes: tuple[BundleNode, ...]
    original_ids: tuple[int, ...]
    endpoints: dict[int, int]


@dataclass(frozen=True)
class SignedNormCertificate:
    target: Formula
    bundle: ProofBundle
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict

    @property
    def payload_sha256(self):
        return sha256(self.payload.encode()).hexdigest()

    @property
    def target_ast_sha256(self):
        return formula_sha256(self.target)


def _canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def _json_hash(value):
    return sha256(_canonical(value).encode()).hexdigest()


def signed_norm_source_pins():
    """Small archived sources only; the 19MB v28 archive is pinned separately."""
    expected = {**even._source_pins(), **PINNED_SOURCES,
                str(even.FERMAT_ARTIFACT.relative_to(ROOT)): even.FERMAT_ARTIFACT_SHA256}
    extra = ("scripts/sqrt2_power_signed_norm.py", "scripts/sqrt2_power_binary_dag.py",
             "peano-lab/py/peano_lab/library/defined_syntax.py",
             "peano-lab/py/peano_lab/library/proof_bundle.py")
    result = {}
    for name in sorted(set(expected) | set(extra)):
        raw = (ROOT / name).read_bytes()
        digest = sha256(raw).hexdigest()
        if len(raw) > 16 * 1024**2 or (name in expected and digest != expected[name]):
            raise SignedNormError("signed-norm source pin changed: " + name)
        result[name] = {"bytes": len(raw), "sha256": digest}
    return result


def signed_difference_definition():
    """Return existing ND0157 verbatim, without registering a new definition."""
    raw = (ROOT / DEFINITION_PARENT).read_bytes()
    if sha256(raw).hexdigest() != PINNED_SOURCES[DEFINITION_PARENT]:
        raise SignedNormError("registered definition parent source changed")
    matches = [r for r in json.loads(raw)["reviewed_definitions"] if r["id"] == "ND0157"]
    if len(matches) != 1 or any(matches[0].get(k) != v for k, v in {
        "name": "SignedDifferenceSquare", "parameters": ["p", "n", "s"],
        "arity": 3, "dependencies": [], "expansion_sha256": DEFINITION_EXPANSION_SHA256,
    }.items()):
        raise SignedNormError("existing ND0157 identity or expansion changed")
    if sha256(DEFINITION_TEMPLATE.encode()).hexdigest() != DEFINITION_EXPANSION_SHA256:
        raise SignedNormError("ND0157 exact expansion source changed")
    return _definition(stable_id="ND0157", name="SignedDifferenceSquare",
        parameters=("p", "n", "s"), template_source=DEFINITION_TEMPLATE,
        summary="The natural value s of the integer square (p−n)², expressed as a subtraction-free balanced equality.",
        category="constructive_lower_layer", priority="P2", conceptual_dependencies=())


def signed_square(p, n, s):
    """Term-level instance of ND0157; no binders or new predicate identity."""
    return Eq(Add(Mul(p, p), Mul(n, n)), Add(s, Add(Mul(p, n), Mul(n, p))))


def frozen_signed_norm_target():
    definition = signed_difference_definition()
    if definition.template_formula != signed_square(Var(0), Var(1), Var(2)):
        raise SignedNormError("term-level ND0157 alias differs from registered expansion")
    target = closed_formula(SIGNED_NORM_SOURCE)
    if formula_sha256(target) != SIGNED_NORM_TARGET_SHA256:
        raise SignedNormError("signed-norm original target AST pin changed")
    return target


def _read_v28(path):
    # The immutable source archive is larger than the OUTPUT bundle cap. Never
    # decode its full ordinary bundle or relax that cap: select inert rows first.
    with Path(path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE + 1)
    if len(raw) != V28_ARTIFACT_SIZE or sha256(raw).hexdigest() != V28_ARTIFACT_SHA256:
        raise SignedNormError("sealed v28 artifact size/source hash changed")
    return raw


def load_signed_square_cone(artifact_path=V28_ARTIFACT, *, limits=BinaryDAGLimits()):
    """Decode only the pinned 22 ordinary rows; acceptance occurs on final replay."""
    if type(limits) is not BinaryDAGLimits:
        raise SignedNormError("expected unchanged pilot limits")
    raw = _read_v28(artifact_path)
    value = json.loads(raw)
    del raw
    if (value[0] != "peano-lab-bundle-v1" or value[1] != 861
            or len(value[3]) != 862):
        raise SignedNormError("sealed v28 envelope changed")
    selected, pending = set(), list(ENDPOINTS)
    while pending:
        node_id = pending.pop()
        if node_id not in selected:
            selected.add(node_id)
            pending.extend(value[3][node_id][2])
    ids = tuple(sorted(selected))
    if (ids != ANCESTOR_IDS or _json_hash(ids) != ANCESTOR_IDS_SHA256
            or sum(len(value[3][i][2]) for i in ids) != 34):
        raise SignedNormError("actual signed-square ancestor cone changed")
    for node_id, pin in ENDPOINTS.items():
        row = value[3][node_id]
        if (_json_hash(row) != pin["row_sha256"]
                or _json_hash(row[1]) != pin["target_sha256"]
                or tuple(row[2]) != pin["dependencies"]):
            raise SignedNormError("signed-square endpoint/dependency pins changed")
    rows = [value[3][i] for i in ids]
    del value
    if len(ids) > limits.max_nodes or len(_canonical(rows).encode()) > limits.max_payload_bytes:
        raise SignedNormError("selected signed-square cone exceeds original bounds")
    remap = {old: new for new, old in enumerate(ids)}
    nodes, total = [], 0
    for old, row in zip(ids, rows):
        # Unchanged ordinary codec, unchanged recursion bound; no large-archive
        # decode and no relaxed BundleLimits. Final canonical replay verifies
        # every selected body with these exact ordered dependencies and fuel.
        target = decode_formula(row[1], _depth=limits.max_depth)
        body = decode_proof(row[3], _depth=limits.max_depth)
        if encode_formula(target) != row[1] or encode_proof(body) != row[3]:
            raise SignedNormError("selected row changed under original codec")
        count, _ = _body_metrics(body, limits)
        total += count
        if total > limits.max_total_body_nodes or row[0] < 8 * count + 16:
            raise SignedNormError("selected cone exceeds body/fuel bounds")
        _row_preflight(target, body, limits)
        nodes.append(BundleNode(remap[old], target, tuple(remap[d] for d in row[2]), body, row[0]))
    for old, pin in ENDPOINTS.items():
        if nodes[remap[old]].target != closed_formula(pin["source"]):
            raise SignedNormError("selected endpoint differs from literal target")
    return SignedSquareCone(tuple(nodes), ids, {old: remap[old] for old in ENDPOINTS})


def _signed_norm_body():
    """Five curried dependencies: IR016, absolute, balance, functional, assoc."""
    # Below both ExistsElim binders: ap,an,bp,bn,s,t,x,y have indices7..0.
    ap, an, bp, bn, s, t, x, y = (Var(i) for i in reversed(range(8)))
    zero, two = Zero(), Succ(Succ(Zero()))
    xx, yy = Mul(x, x), Mul(y, y)
    # Hyp0=abs(b),1=abs(a),2=s=2t,3=square(b,t),4=square(a,s),
    # 5=assoc,6=functional,7=balance,8=absolute existence,9=IR016.
    square_x = ImpElim(instantiate(Hyp(7), ap, an, x), Hyp(1))
    square_y = ImpElim(instantiate(Hyp(7), bp, bn, y), Hyp(0))
    xx_s = ImpElim(ImpElim(instantiate(Hyp(6), ap, an, xx, s), square_x), Hyp(4))
    yy_t = ImpElim(ImpElim(instantiate(Hyp(6), bp, bn, yy, t), square_y), Hyp(3))
    input_equation = EqTrans(xx_s, EqTrans(Hyp(2), EqTrans(
        CongMul(EqRefl(two), EqSym(yy_t)),
        EqSym(instantiate(Hyp(5), two, y, y)))))
    zero_pair = ImpElim(instantiate(Hyp(9), x, y), input_equation)
    goal = And(Eq(ap, an), Eq(bp, bn))

    def recover(p, n, absolute_index, projection):
        # Under the typed zero-pair Cut and then each OrElim branch,
        # Hyp0 is its oriented absolute equation and Hyp1 the zero pair.
        magnitude_zero = projection(Hyp(1))
        left = EqTrans(Hyp(0), EqTrans(CongAdd(EqRefl(n), magnitude_zero),
                                      instantiate(Axiom("PA3"), n)))
        right = EqSym(EqTrans(Hyp(0), EqTrans(CongAdd(EqRefl(p), magnitude_zero),
                                             instantiate(Axiom("PA3"), p))))
        return OrElim(Hyp(absolute_index), left, right)

    body = Cut(And(Eq(x, zero), Eq(y, zero)), goal, zero_pair,
               AndIntro(recover(ap, an, 2, AndElimL), recover(bp, bn, 1, AndElimR)))
    # Under the first witness only: bp=Var4,bn=Var3, existence law=Hyp7.
    body = ExistsElim(instantiate(Hyp(7), Var(4), Var(3)), body)
    # Before either witness: ap=Var5,an=Var4, existence law=Hyp6.
    body = ExistsElim(instantiate(Hyp(6), Var(5), Var(4)), body)
    for _ in range(3):
        body = ImpIntro(body)
    for _ in range(6):
        body = ForallIntro(body)
    for _ in range(5):
        body = ImpIntro(body)
    return body


def prove_signed_norm_zero(basis=None, *, limits=BinaryDAGLimits(), artifact_path=V28_ARTIFACT):
    """Return exact SN001 canonical bytes and fresh HA replay of every body."""
    if type(limits) is not BinaryDAGLimits:
        raise SignedNormError("expected unchanged pilot resource limits")
    target, before = frozen_signed_norm_target(), signed_norm_source_pins()
    cone = load_signed_square_cone(artifact_path, limits=limits)
    if 182 + len(cone.nodes) + 2 > limits.max_nodes:
        raise SignedNormError("signed-norm node budget exhausted before proof generation")
    basis = Basis() if basis is None else basis
    base = even.prove_ir016(basis, limits=limits)
    if len(base.bundle.nodes) != 182 or base.target_ast_sha256 != even.IR016_TARGET_SHA256:
        raise SignedNormError("IR016 actual dependency bundle changed")
    offset = len(base.bundle.nodes)
    nodes = base.bundle.nodes + tuple(replace(n, node_id=n.node_id + offset,
        dependencies=tuple(d + offset for d in n.dependencies)) for n in cone.nodes)
    law = basis.get("mul_assoc")
    if (law.literal_spec_sha256 != MUL_ASSOC_LITERAL_SHA256
            or law.source_sha256 != SOURCE_PINS["peano-lab/py/peano_lab/library/theorems.py"]):
        raise SignedNormError("regenerated associativity literal changed")
    assoc_id, root_id = len(nodes), len(nodes) + 1
    dependencies = (base.bundle.root, *(offset + cone.endpoints[i] for i in (655, 641, 691)), assoc_id)
    nodes += (BundleNode(assoc_id, law.formula, (), law.certificate),
              BundleNode(root_id, target, dependencies, _signed_norm_body()))
    total, deepest = 0, 0
    for node in nodes:
        count, depth = _body_metrics(node.body, limits)
        total, deepest = total + count, max(deepest, depth)
        if total > limits.max_total_body_nodes:
            raise SignedNormError("signed-norm aggregate ordinary body budget exceeded")
        _row_preflight(node.target, node.body, limits)
    bundle = ProofBundle(nodes, root_id)
    payload = encode_proof_bundle(bundle, target, limits=limits.bundle_limits())
    receipt = check_encoded_proof_bundle(payload, limits=limits.bundle_limits())
    if receipt.target != target or formula_sha256(receipt.target) != SIGNED_NORM_TARGET_SHA256:
        raise SignedNormError("original HA did not accept exact signed-norm target")
    if before != signed_norm_source_pins():
        raise SignedNormError("signed-norm source changed during generation")
    _read_v28(artifact_path)
    provenance = {
        "case": "SN001", "claim": "supporting signed norm-zero algebra only",
        "IR_parents_closed": 0, "library_admissions": 0,
        "original_target_source": SIGNED_NORM_SOURCE,
        "original_target_ast_sha256": SIGNED_NORM_TARGET_SHA256,
        "definition": {"id": "ND0157", "name": "SignedDifferenceSquare",
            "expansion_sha256": DEFINITION_EXPANSION_SHA256, "new_definition": False},
        "v28_artifact_bytes": V28_ARTIFACT_SIZE, "v28_artifact_sha256": V28_ARTIFACT_SHA256,
        "v28_original_ancestor_ids": list(cone.original_ids),
        "v28_original_ancestor_ids_sha256": ANCESTOR_IDS_SHA256,
        "v28_selected_nodes": len(cone.nodes), "v28_selected_edges": 34,
        "v28_endpoints": {str(k): v for k, v in ENDPOINTS.items()},
        "ir016_bundle_sha256": base.payload_sha256,
        "ir016_target_ast_sha256": base.target_ast_sha256,
        "ir016_replayed_nodes": len(base.bundle.nodes),
        "root_dependencies": list(dependencies), "source_pins": before,
        "ordinary_HA_checked_from_canonical_bytes": True,
        "total_body_nodes": receipt.total_body_nodes, "max_proof_depth": deepest,
        "limits": dict(vars(limits)),
        "worker_rss_ceiling_bytes": 768 * 1024**2,
        "worker_enforcement": "external root-owned single-worker supervisor required",
    }
    return SignedNormCertificate(target, bundle, payload, receipt, deepest, provenance)
