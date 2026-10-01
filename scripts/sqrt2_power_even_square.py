"""Exact IR016 corollary of an existing ordinary HA Fermat-four proof.

This producer imports the actual 180-node ancestor cone from a sealed 216-node
bundle, not a receipt or a new axiom. It regenerates a small arithmetic basis,
adds two nodes, and checks every ordinary body from the resulting canonical
bytes. Execute proof production only in the root-owned bounded worker.

The result is a*a=2*b*b -> (a=0 /\ b=0), including the zero cases. It is not
a proof of the full irrationality campaign or an Alpha admission.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path

from sqrt2_power_binary_dag import (
    BinaryDAGLimits, ROOT, SOURCE_PINS, _body_metrics, _row_preflight,
    formula_sha256, verify_basis_sources,
)
from sqrt2_power_native import Basis, closed_formula, instantiate, ring
from peano_lab.kernel.formulas import And, Eq, Formula
from peano_lab.kernel.proofs import (
    AndIntro, Axiom, CongMul, Cut, EqRefl, EqSym, EqTrans, ForallIntro,
    Hyp, ImpElim, ImpIntro, OrElim,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.library.proof_bundle import (
    BundleNode, ProofBundle, check_encoded_proof_bundle, decode_proof_bundle,
    encode_proof_bundle,
)

IR016_SOURCE = r"forall a b. a*a=(S(S 0))*b*b -> (a=0 /\ b=0)"
IR016_TARGET_SHA256 = "a1aaa15b01ead79382b92dff5be1ebd105745bc26b937451e73ecdec973209b7"
FERMAT_SOURCE = r"forall a b h. a * a * a * a + b * b * b * b = h * h -> (a = 0 \/ b = 0)"
FERMAT_TARGET_SHA256 = "dcfd188d100ccdc9ef6cb91476c04d90e4d49bd5ce37773f23d30ea846519435"
FERMAT_ARTIFACT = ROOT / "research/arithmetic-library/artifacts/alpha-v26-first-wave-proof-bundle-v1.json"
FERMAT_ARTIFACT_SIZE = 364186
FERMAT_ARTIFACT_SHA256 = "59afca707b33b68df907c941683e335492f7de12ee3888219339c5dfce8ec4fc"
FERMAT_SOURCE_PATH = "peano-lab/py/peano_lab/library/fermat_four_descent_candidate.py"
FERMAT_SOURCE_SHA256 = "e1ec771d01d33063fc324d11cf50cec6f2c50ccede0ae90ed3432af4fa4a3fdb"
FERMAT_ORIGINAL_NODE = 211
FERMAT_ROW_SHA256 = "99ea7fe5691e56b3552ad0e2b827f04e662b8995ba7329c1e0d611ad2db66126"
FERMAT_ANCESTOR_IDS_SHA256 = "f9a9d24b38d81e31be8828444135696b0d07ed3b7bd2005f9e58efe294c0743d"
MUL_EQ_ZERO_LITERAL_SHA256 = "1fbd7b8a10712cbcab381b042c9dfa33fd5c2fae31d98001a4f34ffd617a5f1f"


class EvenSquareError(ValueError):
    """Changed statement, source, provenance, or fixed construction bounds."""


@dataclass(frozen=True)
class FermatCone:
    """Decoded proof data only: loading a cone is NOT a kernel acceptance."""

    nodes: tuple[BundleNode, ...]
    original_ids: tuple[int, ...]
    root: int
    source_sha256: str


@dataclass(frozen=True)
class EvenSquareCertificate:
    target: Formula
    bundle: ProofBundle
    payload: str
    receipt: object
    max_proof_depth: int
    fermat_node: int
    mul_eq_zero_node: int
    provenance: dict

    @property
    def payload_sha256(self):
        return sha256(self.payload.encode()).hexdigest()

    @property
    def target_ast_sha256(self):
        return formula_sha256(self.target)


def _json_hash(value):
    return sha256(json.dumps(value, ensure_ascii=True, allow_nan=False,
                            separators=(",", ":")).encode()).hexdigest()


def frozen_ir016_target():
    target = closed_formula(IR016_SOURCE)
    if formula_sha256(target) != IR016_TARGET_SHA256:
        raise EvenSquareError("IR016 original target AST pin changed")
    return target


def _source_pins():
    pins = verify_basis_sources()
    digest = sha256((ROOT / FERMAT_SOURCE_PATH).read_bytes()).hexdigest()
    if digest != FERMAT_SOURCE_SHA256:
        raise EvenSquareError("Fermat native factory source pin changed")
    return {**pins, FERMAT_SOURCE_PATH: digest}


def _artifact_bytes(path):
    # Read at most the pinned size plus one byte, before decoding anything.
    with Path(path).open("rb") as stream:
        raw = stream.read(FERMAT_ARTIFACT_SIZE + 1)
    if len(raw) != FERMAT_ARTIFACT_SIZE or sha256(raw).hexdigest() != FERMAT_ARTIFACT_SHA256:
        raise EvenSquareError("sealed Fermat bundle source hash changed")
    return raw


def load_frozen_fermat_cone(artifact_path=FERMAT_ARTIFACT):
    """Extract exact ordinary bodies; only prove_ir016() checks their proofs."""
    raw = _artifact_bytes(artifact_path)
    value = json.loads(raw)
    if len(value[3]) != 216 or value[1] != 215:
        raise EvenSquareError("sealed Fermat bundle envelope changed")
    if _json_hash(value[3][FERMAT_ORIGINAL_NODE]) != FERMAT_ROW_SHA256:
        raise EvenSquareError("Fermat closed node row pin changed")
    # Original codec validates canonical syntax, topology, and structural caps;
    # it intentionally does not treat decoding as proof checking.
    original, _ = decode_proof_bundle(raw.decode(), limits=BinaryDAGLimits().bundle_limits())
    endpoint = original.nodes[FERMAT_ORIGINAL_NODE]
    if (endpoint.target != closed_formula(FERMAT_SOURCE)
            or formula_sha256(endpoint.target) != FERMAT_TARGET_SHA256
            or endpoint.dependencies != (78, 208, 210)):
        raise EvenSquareError("Fermat theorem or ordered dependencies changed")
    ancestors, pending = set(), [FERMAT_ORIGINAL_NODE]
    while pending:
        node_id = pending.pop()
        if node_id not in ancestors:
            ancestors.add(node_id)
            pending.extend(original.nodes[node_id].dependencies)
    ids = tuple(sorted(ancestors))
    if (len(ids) != 180 or _json_hash(ids) != FERMAT_ANCESTOR_IDS_SHA256
            or sum(len(original.nodes[i].dependencies) for i in ids) != 450):
        raise EvenSquareError("Fermat exact ancestor cone changed")
    remap = {old: new for new, old in enumerate(ids)}
    nodes = tuple(replace(original.nodes[old], node_id=remap[old],
                          dependencies=tuple(remap[d] for d in original.nodes[old].dependencies))
                  for old in ids)
    return FermatCone(nodes, ids, remap[FERMAT_ORIGINAL_NODE], FERMAT_ARTIFACT_SHA256)


def _ir016_body(basis):
    """Body curried over Fermat first, mul_eq_zero second, then forall a b."""
    a, b, zero = Var(1), Var(0), Zero()
    two = Succ(Succ(zero))
    aa, bb, ab = Mul(a, a), Mul(b, b), Mul(a, b)
    twice_bb = Mul(Mul(two, b), b)
    b4 = Mul(Mul(Mul(b, b), b), b)
    # Here Hyp(0)=a*a=2*b*b, Hyp(1)=mul_eq_zero, Hyp(2)=Fermat.
    # The two ring certificates are closed in the hypothesis context; their
    # free term indices are bound by the two ForallIntro nodes below.
    quartic = EqTrans(
        ring(Eq(Add(b4, b4), Mul(twice_bb, bb)), basis),
        EqTrans(EqSym(CongMul(Hyp(0), EqRefl(bb))),
                ring(Eq(Mul(aa, bb), Mul(ab, ab)), basis)),
    )
    disjunction = ImpElim(instantiate(Hyp(2), b, b, ab), quartic)
    b_zero = OrElim(disjunction, Hyp(0), Hyp(0))
    goal = And(Eq(a, zero), Eq(b, zero))
    # Under this typed Cut: Hyp(0)=b=0, Hyp(1)=the original equality,
    # Hyp(2)=mul_eq_zero, Hyp(3)=Fermat. The duplicated disjunction branches
    # each expose their own equality as Hyp(0); no classical case split occurs.
    right_zero = EqTrans(CongMul(EqRefl(Mul(two, b)), Hyp(0)),
                         instantiate(Axiom("PA5"), Mul(two, b)))
    aa_zero = EqTrans(Hyp(1), right_zero)
    a_disjunction = ImpElim(instantiate(Hyp(2), a, a), aa_zero)
    a_zero = OrElim(a_disjunction, Hyp(0), Hyp(0))
    body = Cut(Eq(b, zero), goal, b_zero, AndIntro(a_zero, Hyp(0)))
    return ImpIntro(ImpIntro(ForallIntro(ForallIntro(ImpIntro(body)))))


def prove_ir016(basis=None, *, limits=BinaryDAGLimits(), artifact_path=FERMAT_ARTIFACT):
    """Return the exact canonical proof bundle and fresh original-HA receipt.

    Inputs are authenticated before and after production. The old Fermat cone
    and both new nodes are actually checked, once each, from the output bytes.
    No historical receipt grants a premise, and no kernel limits are enlarged.
    """
    if type(limits) is not BinaryDAGLimits:
        raise EvenSquareError("expected the unchanged pilot resource limits")
    target, before = frozen_ir016_target(), _source_pins()
    producer_hash = sha256(Path(__file__).read_bytes()).hexdigest()
    cone = load_frozen_fermat_cone(artifact_path)
    if len(cone.nodes) + 2 > limits.max_nodes:
        raise EvenSquareError("IR016 bundle exceeds the local node budget")
    basis = Basis() if basis is None else basis
    law = basis.get("mul_eq_zero")
    if (law.literal_spec_sha256 != MUL_EQ_ZERO_LITERAL_SHA256
            or law.source_sha256 != SOURCE_PINS["peano-lab/py/peano_lab/library/theorems.py"]):
        raise EvenSquareError("regenerated mul_eq_zero differs from its literal pin")
    law_id, root_id = len(cone.nodes), len(cone.nodes) + 1
    nodes = cone.nodes + (
        BundleNode(law_id, law.formula, (), law.certificate),
        BundleNode(root_id, target, (cone.root, law_id), _ir016_body(basis)),
    )
    total, deepest = 0, 0
    for node in nodes:
        count, depth = _body_metrics(node.body, limits)
        total, deepest = total + count, max(deepest, depth)
        if total > limits.max_total_body_nodes:
            raise EvenSquareError("IR016 aggregate ordinary body budget exceeded")
        _row_preflight(node.target, node.body, limits)
    bundle = ProofBundle(nodes, root_id)
    payload = encode_proof_bundle(bundle, target, limits=limits.bundle_limits())
    receipt = check_encoded_proof_bundle(payload, limits=limits.bundle_limits())
    if receipt.target != target or formula_sha256(receipt.target) != IR016_TARGET_SHA256:
        raise EvenSquareError("checked bundle does not prove exact original IR016")
    if (before != _source_pins()
            or producer_hash != sha256(Path(__file__).read_bytes()).hexdigest()):
        raise EvenSquareError("proof-producing source changed during generation")
    _artifact_bytes(artifact_path)
    provenance = {
        "claim": "IR016 only; no full irrationality or library admission claim",
        "original_target_source": IR016_SOURCE,
        "original_target_ast_sha256": IR016_TARGET_SHA256,
        "fermat_artifact_sha256": cone.source_sha256,
        "fermat_original_node": FERMAT_ORIGINAL_NODE,
        "fermat_original_name": "fermat_four_square_solutions_have_zero_coordinate",
        "fermat_original_row_sha256": FERMAT_ROW_SHA256,
        "fermat_target_ast_sha256": FERMAT_TARGET_SHA256,
        "fermat_original_ancestor_ids": list(cone.original_ids),
        "fermat_original_ancestor_ids_sha256": FERMAT_ANCESTOR_IDS_SHA256,
        "fermat_replayed_nodes": len(cone.nodes),
        "source_pins": before,
        "producer_source_sha256": producer_hash,
        "regenerated_basis": basis.manifest(),
        "ordinary_HA_checked_from_canonical_bytes": True,
        "limits": dict(vars(limits)),
    }
    return EvenSquareCertificate(target, bundle, payload, receipt, deepest,
                                 cone.root, law_id, provenance)
