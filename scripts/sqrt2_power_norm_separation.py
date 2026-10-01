"""SN002/NG001: ordinary HA witnesses for a nonzero integer norm's gap.

SN001 rules out equality of the two natural square contributions. The actual
sealed trichotomy proof supplies a strict-gap witness, with PA4 and checked
addition commutativity putting its terms in the exact requested order.
There is no real/rational interpretation, full IR032 claim, or new definition.
Execute proof producers only inside the root-owned single-worker supervisor.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path

import sqrt2_power_signed_norm as signed
from sqrt2_power_binary_dag import (
    BinaryDAGLimits, ROOT, SOURCE_PINS, _body_metrics, _row_preflight,
    formula_sha256,
)
from sqrt2_power_native import Basis, closed_formula, instantiate
from peano_lab.kernel.formulas import Formula
from peano_lab.kernel.proofs import (
    Axiom, BotElim, CongS, EqSym, EqTrans, ExistsElim, ExistsIntro,
    ForallIntro, Hyp, ImpElim, ImpIntro, OrElim, OrIntroL, OrIntroR,
)
from peano_lab.kernel.terms import Mul, Succ, Var, Zero
from peano_lab.library.proof_bundle import (
    BundleNode, ProofBundle, check_encoded_proof_bundle, decode_formula,
    decode_proof, encode_formula, encode_proof, encode_proof_bundle,
)

NATURAL_GAP_SOURCE = r"forall a b. ~(a=b) -> exists k. (a+S k=b \/ b+S k=a)"
NATURAL_GAP_TARGET_SHA256 = "f0598e325456d7992079c20535c5d15740fb9f4a35c1a2619d5983c7ac9ac64b"
NORM_SEPARATION_SOURCE = (
    "forall ap an bp bn s t. "
    "ap*ap+an*an=s+(ap*an+an*ap) -> "
    "bp*bp+bn*bn=t+(bp*bn+bn*bp) -> "
    "~(ap=an /\\ bp=bn) -> "
    "exists k. (s+S k=(S(S 0))*t \\/ (S(S 0))*t+S k=s)"
)
NORM_SEPARATION_TARGET_SHA256 = "7a0c83cccc0c50cb487d5dda5fc177677b4aeb7758ac7179e2f46023dcccd4c5"
SIGNED_NORM_PRODUCER_SHA256 = "4a042d1ba85b39816f9738bf53484e2642f602dafc22437f45503f02b2bd8294"
TRICHOTOMY_ORIGINAL_NODE = 48
TRICHOTOMY_SOURCE = r"forall a b. a = b \/ ((exists k. k + S a = b) \/ exists k. k + S b = a)"
TRICHOTOMY_TARGET_SHA256 = "5e9313378d9870a77acb3a1b8417e1ffc10414ba99624b72b17a0a0bee2d43fc"
TRICHOTOMY_ROW_SHA256 = "18dd1967c5a53c5cf792f2f2ff9f1c4160e18b77197c6710866d27aeaa515a32"
ADD_COMM_LITERAL_SHA256 = "fe0b9b47ad59a0ff1b3d7eee860c8262421e735cdf0128ba9a486958f6b077a1"


class NormSeparationError(ValueError):
    """Changed original target, ordinary dependency, source, or resource bound."""


@dataclass(frozen=True)
class NormSeparationCertificate:
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


def norm_separation_source_pins():
    """Archive only small sources; the original v28 archive is checked internally."""
    pins = signed.signed_norm_source_pins()
    producer = "scripts/sqrt2_power_signed_norm.py"
    if pins[producer]["sha256"] != SIGNED_NORM_PRODUCER_SHA256:
        raise NormSeparationError("checked SN001 producer source pin changed")
    path = Path(__file__).resolve()
    raw = path.read_bytes()
    if len(raw) > 16 * 1024**2:
        raise NormSeparationError("norm-separation producer exceeds source archival cap")
    pins[str(path.relative_to(ROOT))] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    return pins


def signed_difference_definition():
    """The same registered ND0157 identity; no new definition or registry entry."""
    return signed.signed_difference_definition()


def frozen_natural_gap_target():
    target = closed_formula(NATURAL_GAP_SOURCE)
    if formula_sha256(target) != NATURAL_GAP_TARGET_SHA256:
        raise NormSeparationError("natural-gap original target AST pin changed")
    return target


def frozen_norm_separation_target():
    # Reauthenticate the existing witness abbreviation and parent statement.
    signed.frozen_signed_norm_target()
    target = closed_formula(NORM_SEPARATION_SOURCE)
    if formula_sha256(target) != NORM_SEPARATION_TARGET_SHA256:
        raise NormSeparationError("norm-separation original target AST pin changed")
    return target


def load_frozen_trichotomy(artifact_path=signed.V28_ARTIFACT, *, limits=BinaryDAGLimits()):
    """Decode one real dependency-free ordinary body, not the whole large bundle."""
    if type(limits) is not BinaryDAGLimits:
        raise NormSeparationError("expected unchanged pilot resource limits")
    raw = signed._read_v28(artifact_path)
    value = json.loads(raw)
    del raw
    if value[0] != "peano-lab-bundle-v1" or value[1] != 861 or len(value[3]) != 862:
        raise NormSeparationError("sealed trichotomy source envelope changed")
    row = value[3][TRICHOTOMY_ORIGINAL_NODE]
    del value
    if (signed._json_hash(row) != TRICHOTOMY_ROW_SHA256 or row[2] != []
            or signed._json_hash(row[1]) != TRICHOTOMY_TARGET_SHA256):
        raise NormSeparationError("actual trichotomy row/target/dependency pins changed")
    if len(signed._canonical(row).encode()) > limits.max_payload_bytes:
        raise NormSeparationError("selected trichotomy row exceeds unchanged payload cap")
    target = decode_formula(row[1], _depth=limits.max_depth)
    body = decode_proof(row[3], _depth=limits.max_depth)
    if (target != closed_formula(TRICHOTOMY_SOURCE)
            or encode_formula(target) != row[1] or encode_proof(body) != row[3]):
        raise NormSeparationError("actual trichotomy changed under the ordinary codec")
    count, _ = _body_metrics(body, limits)
    if count != 66 or row[0] < 8 * count + 16:
        raise NormSeparationError("actual trichotomy body/fuel changed")
    _row_preflight(target, body, limits)
    return BundleNode(0, target, (), body, row[0])


def _natural_gap_body():
    """Curried dependencies: the actual trichotomy, then checked add_comm."""
    # Under forall a b and the inequality premise: Hyp0=not-equal,
    # Hyp1=add_comm, Hyp2=trichotomy. Trichotomy's equality branch is impossible.
    a, b = Var(1), Var(0)
    equality_case = BotElim(ImpElim(Hyp(1), Hyp(0)))

    def strict_case(reverse):
        # Under both disjunction branches and the existential witness:
        # k=Var0,a=Var2,b=Var1; Hyp0=k+S(lower)=upper,Hyp4=add_comm.
        lower, k = Var(1 if reverse else 2), Var(0)
        orientation = EqTrans(instantiate(Axiom("PA4"), lower, k), EqTrans(
            CongS(instantiate(Hyp(4), lower, k)),
            EqSym(instantiate(Axiom("PA4"), k, lower))))
        equation = EqTrans(orientation, Hyp(0))
        injection = OrIntroR if reverse else OrIntroL
        return ExistsElim(Hyp(0), ExistsIntro(k, injection(equation)))

    strict_cases = OrElim(Hyp(0), strict_case(False), strict_case(True))
    body = OrElim(instantiate(Hyp(2), a, b), equality_case, strict_cases)
    return ImpIntro(ImpIntro(ForallIntro(ForallIntro(ImpIntro(body)))))


def _norm_separation_body():
    """Curried dependencies SN001, NG001; three explicit mathematical premises."""
    ap, an, bp, bn, s, t = (Var(i) for i in reversed(range(6)))
    # The new local equality premise shifts the original context by one:
    # Hyp0=s=2t,1=nonzero pair,2=square B,3=square A,4=NG001,5=SN001.
    zero_pair = ImpElim(ImpElim(ImpElim(
        instantiate(Hyp(5), ap, an, bp, bn, s, t), Hyp(3)), Hyp(2)), Hyp(0))
    unequal = ImpIntro(ImpElim(Hyp(1), zero_pair))
    # Back in the three-premise context, NG001 is Hyp3.
    body = ImpElim(instantiate(Hyp(3), s, Mul(Succ(Succ(Zero())), t)), unequal)
    for _ in range(3):
        body = ImpIntro(body)
    for _ in range(6):
        body = ForallIntro(body)
    for _ in range(2):
        body = ImpIntro(body)
    return body


def _finish(bundle, target, case, before, provenance, limits, artifact_path):
    total, deepest = 0, 0
    for node in bundle.nodes:
        count, depth = _body_metrics(node.body, limits)
        total, deepest = total + count, max(deepest, depth)
        if total > limits.max_total_body_nodes:
            raise NormSeparationError("aggregate ordinary body budget exceeded")
        _row_preflight(node.target, node.body, limits)
    payload = encode_proof_bundle(bundle, target, limits=limits.bundle_limits())
    receipt = check_encoded_proof_bundle(payload, limits=limits.bundle_limits())
    expected = NATURAL_GAP_TARGET_SHA256 if case == "NG001" else NORM_SEPARATION_TARGET_SHA256
    if receipt.target != target or formula_sha256(receipt.target) != expected:
        raise NormSeparationError("canonical replay differs from exact original target")
    if before != norm_separation_source_pins():
        raise NormSeparationError("norm-separation source changed during generation")
    signed._read_v28(artifact_path)
    provenance = {**provenance,
        "case": case, "IR_parents_closed": 0, "library_admissions": 0,
        "original_target_source": NATURAL_GAP_SOURCE if case == "NG001" else NORM_SEPARATION_SOURCE,
        "original_target_ast_sha256": expected,
        "source_pins": before, "ordinary_HA_checked_from_canonical_bytes": True,
        "total_body_nodes": receipt.total_body_nodes, "max_proof_depth": deepest,
        "v28_artifact_bytes": signed.V28_ARTIFACT_SIZE,
        "v28_artifact_sha256": signed.V28_ARTIFACT_SHA256,
        "limits": dict(vars(limits)), "worker_rss_ceiling_bytes": 768 * 1024**2,
        "worker_enforcement": "external root-owned single-worker supervisor required",
    }
    return NormSeparationCertificate(target, bundle, payload, receipt, deepest, provenance)


def prove_natural_gap(basis=None, *, limits=BinaryDAGLimits(), artifact_path=signed.V28_ARTIFACT):
    """NG001: a reusable, independently checked ordinary strict-gap theorem."""
    if type(limits) is not BinaryDAGLimits:
        raise NormSeparationError("expected unchanged pilot resource limits")
    target, before = frozen_natural_gap_target(), norm_separation_source_pins()
    if limits.max_nodes < 3:
        raise NormSeparationError("natural-gap node budget exhausted before generation")
    trichotomy = load_frozen_trichotomy(artifact_path, limits=limits)
    basis = Basis() if basis is None else basis
    addition = basis.get("add_comm")
    if (addition.source_sha256 != SOURCE_PINS["peano-lab/py/peano_lab/library/theorems.py"]
            or addition.literal_spec_sha256 != ADD_COMM_LITERAL_SHA256):
        raise NormSeparationError("regenerated addition commutativity literal changed")
    bundle = ProofBundle((trichotomy,
        BundleNode(1, addition.formula, (), addition.certificate),
        BundleNode(2, target, (0, 1), _natural_gap_body())), 2)
    provenance = {
        "claim": "constructive natural strict gap only",
        "trichotomy_original_node": TRICHOTOMY_ORIGINAL_NODE,
        "trichotomy_original_name": "lt_trichotomy",
        "trichotomy_original_row_sha256": TRICHOTOMY_ROW_SHA256,
        "trichotomy_target_ast_sha256": TRICHOTOMY_TARGET_SHA256,
        "trichotomy_original_ancestor_ids": [TRICHOTOMY_ORIGINAL_NODE],
        "trichotomy_original_dependencies": [],
        "add_comm_literal_sha256": ADD_COMM_LITERAL_SHA256,
    }
    return _finish(bundle, target, "NG001", before, provenance, limits, artifact_path)


def prove_norm_separation(basis=None, *, limits=BinaryDAGLimits(), artifact_path=signed.V28_ARTIFACT):
    """SN002: return a positive integer-gap witness from the exact square premises."""
    if type(limits) is not BinaryDAGLimits:
        raise NormSeparationError("expected unchanged pilot resource limits")
    target, before = frozen_norm_separation_target(), norm_separation_source_pins()
    if limits.max_nodes < 210:
        raise NormSeparationError("norm-separation node budget exhausted before generation")
    basis = Basis() if basis is None else basis
    parent = signed.prove_signed_norm_zero(basis, limits=limits, artifact_path=artifact_path)
    gap = prove_natural_gap(basis, limits=limits, artifact_path=artifact_path)
    if (len(parent.bundle.nodes) != 206 or parent.target_ast_sha256 != signed.SIGNED_NORM_TARGET_SHA256
            or len(gap.bundle.nodes) != 3 or gap.target_ast_sha256 != NATURAL_GAP_TARGET_SHA256):
        raise NormSeparationError("actual SN001 or NG001 dependency bundle changed")
    offset = len(parent.bundle.nodes)
    nodes = parent.bundle.nodes + tuple(replace(node, node_id=node.node_id + offset,
        dependencies=tuple(d + offset for d in node.dependencies)) for node in gap.bundle.nodes)
    root_id = len(nodes)
    dependencies = (parent.bundle.root, gap.bundle.root + offset)
    bundle = ProofBundle(nodes + (BundleNode(root_id, target, dependencies, _norm_separation_body()),), root_id)
    provenance = {
        "claim": "witnessed integer norm separation only; no real/rational bound or full IR032 closure",
        "definition": {"id": "ND0157", "name": "SignedDifferenceSquare",
            "expansion_sha256": signed.DEFINITION_EXPANSION_SHA256, "new_definition": False},
        "SN001_bundle_sha256": parent.payload_sha256,
        "SN001_target_ast_sha256": parent.target_ast_sha256, "SN001_replayed_nodes": 206,
        "NG001_bundle_sha256": gap.payload_sha256,
        "NG001_target_ast_sha256": gap.target_ast_sha256, "NG001_replayed_nodes": 3,
        "trichotomy_original_node": TRICHOTOMY_ORIGINAL_NODE,
        "trichotomy_original_row_sha256": TRICHOTOMY_ROW_SHA256,
        "root_dependencies": list(dependencies),
    }
    return _finish(bundle, target, "SN002", before, provenance, limits, artifact_path)
