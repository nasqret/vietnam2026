"""SI001: nonzero represented integers have a nonzero represented product.

This is signed-INTEGER binary multiplication, not quadratic-field multiplication
and not a finite-product theorem. Arbitrary overlapping positive/negative input
and output representatives are allowed. Every proof dependency is an actual
ordinary body selected from the immutable v28 archive; no theorem receipt or
solver answer is admitted as a premise. No ring normalization is performed.

Only the root-owned bounded worker should invoke the proof producer. Import,
source contracts, exact target elaboration and inert cone inspection do not
produce proofs. The kernel, source archive and original resource ceilings remain
unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sqrt2-power-signed-product-nonzero-v1"
PARAMETERS = ("p", "n", "q", "m", "r", "s")
PRODUCT_BALANCE_SOURCE = "r+(p*m+n*q)=(p*q+n*m)+s"
SIGNED_PRODUCT_NONZERO_SOURCE = (
    "forall p n q m r s. " + PRODUCT_BALANCE_SOURCE
    + " -> ~(p=n) -> ~(q=m) -> ~(r=s)"
)
SIGNED_PRODUCT_NONZERO_TARGET_SHA256 = "ee1a6a3a9dfc5f7d45c67d4a040a8ff0ccf2d4422f2ddc42e1fad69334c2d581"
V28_ARTIFACT = ROOT / "research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json"
V28_ARTIFACT_SIZE = 18977050
V28_ARTIFACT_SHA256 = "e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1"
ANCESTOR_IDS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 21, 22, 27, 41, 47, 90,
                278, 632, 637, 638, 639, 640, 641, 649, 655, 685, 690, 691,
                694, 695, 696, 697, 713)
ANCESTOR_IDS_SHA256 = "43443aa2822f757f6275265dee5e9e00f62dc3cf7ca20ae28bc67b18a44856ba"
SELECTED_ROWS_SHA256 = "6ad426cd664e27aef9ca31a9f6a4df28ae16d15cef765dc5c1ee0fbadd913da6"
SELECTED_ROWS_BYTES = 151139
ENDPOINTS = {
    690: dict(name="gaussian_signed_square_exists", dependencies=(655, 641),
        source="forall p n. exists u. p*p+n*n=u+(p*n+n*p)",
        target_sha256="33fea19e85da5925360b793e8ee9205a33d306081367abf2c32797f69cf3fbb4",
        row_sha256="8a034a998690aa1a5b929e839cbc30c29a6781a9f760426ac4a7f7928d64963b"),
    697: dict(name="gaussian_signed_square_product", dependencies=(694, 695, 696),
        source=("forall p n q m u v. p*p+n*n=u+(p*n+n*p) -> "
            "q*q+m*m=v+(q*m+m*q) -> "
            "(p*q+n*m)*(p*q+n*m)+(p*m+n*q)*(p*m+n*q)="
            "u*v+((p*q+n*m)*(p*m+n*q)+(p*m+n*q)*(p*q+n*m))"),
        target_sha256="daae2a73cbcda62a388c64db597b790716b53175a664013a7318815066a3089d",
        row_sha256="1b139f3995187da519bb035255129ecebf06568ece8dcacc2cea1e6471799239"),
    713: dict(name="gaussian_signed_square_zero_iff", dependencies=(655, 641, 691, 649, 0),
        source=("forall p n u. p*p+n*n=u+(p*n+n*p) -> "
                "((u=0 -> p=n) /\\ (p=n -> u=0))"),
        target_sha256="6e133fd08a2467a89ce2bb39bd05bb3650791e8a8567d686a15a6f95910c310b",
        row_sha256="0b80902fc52623c1ddc828c0c0f675bd7f9405c1af3ec501ce5d2e7a1680f9f0"),
    22: dict(name="mul_eq_zero", dependencies=(21,),
        source="forall u v. u*v=0 -> (u=0 \\/ v=0)",
        target_sha256="d8f38724b24c621f6b1b2f5ab994325a0b88deb5caa0cfc0ad7eefa3cb839007",
        row_sha256="ba3db3f265f17c43a2b57962ac5ce942da2caaf63992b57564fd6d2a4f8a9b2a"),
    27: dict(name="add_right_cancel", dependencies=(),
        source="forall a b c. a+c=b+c -> a=b",
        target_sha256="a920f73f025468721a0836e7ab36f3b5dc37b8b633a6cca84146676afc0102ed",
        row_sha256="e9d80ab59901882c7abfcb9b57f000aef698742d5c07078fd2cd766d6fed5758"),
    2: dict(name="add_comm", dependencies=(0, 1),
        source="forall a b. a+b=b+a",
        target_sha256="25b3cc29a1427896f1aa3935bc167b449d4501668be477e477180454ba292f94",
        row_sha256="6d0907be710b1670092723219ae751b63a7bc5129d7f262b42ac0f875fe213e3"),
}
ROOT_DEPENDENCIES = (690, 697, 713, 22, 27, 2)
PINNED_SOURCES = {
    "scripts/sqrt2_power_native.py": "9b51adc2699bf3c83c74749b9fc4723a8a1b8e234cef6f521a3f309fe646cc73",
    "scripts/sqrt2_power_binary_dag.py": "517535807fe06a317fae48c5fc5f47db944b0c32904fb8d02a0a1b102af12227",
    "peano-lab/py/peano_lab/library/theorems.py": "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "peano-lab/py/peano_lab/library/gaussian_euclidean_candidate.py": "de2b9a14a7cf532cbe583d5972afa4f423703c9a5ba780b85b8f9c3c21cee4d8",
    "peano-lab/py/peano_lab/library/matrix_lattice_data_candidate.py": "4dd9eff374a53f9a1b99e8754351de66859cf731c41196d067e31666e45b3c07",
    "peano-lab/py/peano_lab/library/four_square_identity_candidate.py": "be4512db0d1cba26c5c61f282e7e7259fbbae3307e760657e4be5b1a44adf300",
    "peano-lab/py/peano_lab/library/proof_bundle.py": "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4",
    "peano-lab/py/peano_lab/kernel/checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "peano-lab/py/peano_lab/kernel/proofs.py": "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
}


class SignedProductNonzeroError(ValueError):
    """Exact source, target, real proof body or resource-bound mismatch."""


def canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()


def json_hash(value):
    return sha256(canonical(value)).hexdigest()


def signed_product_nonzero_source_pins():
    result = {}
    producer = "scripts/sqrt2_power_signed_product_nonzero.py"
    for name in sorted((*PINNED_SOURCES, producer)):
        raw = (ROOT / name).read_bytes()
        digest = sha256(raw).hexdigest()
        if len(raw) > 16 * 1024**2 or name in PINNED_SOURCES and digest != PINNED_SOURCES[name]:
            raise SignedProductNonzeroError("signed-product source changed: " + name)
        result[name] = dict(bytes=len(raw), sha256=digest)
    return result


def source_contract():
    return dict(code="SI001", schema=SCHEMA, source=SIGNED_PRODUCT_NONZERO_SOURCE,
        statement_ast_sha256=SIGNED_PRODUCT_NONZERO_TARGET_SHA256,
        parameters=list(PARAMETERS), premise_count=3,
        arbitrary_input_representatives=True, arbitrary_output_representatives=True,
        coverage="universal_signed_integer_binary_product_nonzero",
        authority="frozen_source_not_a_certificate", original_HA_checked=False,
        quadratic_field_claim=False, finite_product_claim=False,
        closes_IR046=False, closes_IR072=False, library_admissions=0)


def frozen_signed_product_nonzero_target():
    """Source-to-original-AST elaboration only: no proof is constructed."""
    from sqrt2_power_native import closed_formula
    from peano_lab.kernel.formulas import Bot, Eq, Forall, Imp
    from peano_lab.kernel.terms import Add, Mul, Var
    from peano_lab.library.proof_bundle import encode_formula
    target = closed_formula(SIGNED_PRODUCT_NONZERO_SOURCE)
    if json_hash(encode_formula(target)) != SIGNED_PRODUCT_NONZERO_TARGET_SHA256:
        raise SignedProductNonzeroError("SI001 exact original target AST changed")
    p, n, q, m, r, s = (Var(i) for i in reversed(range(6)))
    positive = Add(Mul(p, q), Mul(n, m))
    negative = Add(Mul(p, m), Mul(n, q))
    expected = Imp(Eq(Add(r, negative), Add(positive, s)),
        Imp(Imp(Eq(p, n), Bot()), Imp(Imp(Eq(q, m), Bot()), Imp(Eq(r, s), Bot()))))
    for _ in PARAMETERS:
        expected = Forall(expected)
    if target != expected:
        raise SignedProductNonzeroError("SI001 arbitrary representative or premise shape changed")
    return target


def inert_selected_rows(artifact_path=V28_ARTIFACT):
    """Pinned JSON inspection only; no ordinary proof decoding or checking."""
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE + 1)
    if len(raw) != V28_ARTIFACT_SIZE or sha256(raw).hexdigest() != V28_ARTIFACT_SHA256:
        raise SignedProductNonzeroError("sealed v28 artifact size/hash changed")
    value = json.loads(raw)
    del raw
    if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
            or value[1] != 861 or len(value[3]) != 862):
        raise SignedProductNonzeroError("sealed v28 envelope changed")
    selected, pending = set(), list(ROOT_DEPENDENCIES)
    while pending:
        node_id = pending.pop()
        if node_id not in selected:
            selected.add(node_id)
            pending.extend(value[3][node_id][2])
    ids = tuple(sorted(selected))
    if ids != ANCESTOR_IDS or json_hash(ids) != ANCESTOR_IDS_SHA256:
        raise SignedProductNonzeroError("actual signed-product ancestor cone changed")
    for node_id, pin in ENDPOINTS.items():
        row = value[3][node_id]
        if (json_hash(row) != pin["row_sha256"] or json_hash(row[1]) != pin["target_sha256"]
                or tuple(row[2]) != pin["dependencies"]):
            raise SignedProductNonzeroError("actual signed-product endpoint changed")
    rows = tuple(value[3][i] for i in ids)
    if json_hash(rows) != SELECTED_ROWS_SHA256 or len(canonical(rows)) != SELECTED_ROWS_BYTES:
        raise SignedProductNonzeroError("selected actual row bytes changed")
    return ids, rows


@dataclass(frozen=True)
class SignedProductCone:
    nodes: tuple
    original_ids: tuple
    endpoints: dict
    body_nodes: int
    max_depth: int


@dataclass(frozen=True)
class SignedProductNonzeroCertificate:
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


def load_signed_product_cone(artifact_path=V28_ARTIFACT, *, limits=None):
    """Decode exactly 33 actual rows; final canonical replay grants acceptance."""
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from sqrt2_power_native import closed_formula
    from peano_lab.library.proof_bundle import BundleNode, decode_formula, decode_proof, encode_formula, encode_proof
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise SignedProductNonzeroError("expected unchanged pilot limits")
    ids, rows = inert_selected_rows(artifact_path)
    if len(ids) > limits.max_nodes or len(canonical(rows)) > limits.max_payload_bytes:
        raise SignedProductNonzeroError("selected cone exceeds original local limits")
    remap = {old: new for new, old in enumerate(ids)}
    nodes, count, deepest = [], 0, 0
    for old, row in zip(ids, rows):
        target = decode_formula(row[1], _depth=limits.max_depth)
        body = decode_proof(row[3], _depth=limits.max_depth)
        if encode_formula(target) != row[1] or encode_proof(body) != row[3]:
            raise SignedProductNonzeroError("actual row changed through ordinary codec")
        local_count, local_depth = _body_metrics(body, limits)
        count += local_count
        deepest = max(deepest, local_depth)
        if count > limits.max_total_body_nodes or row[0] < 8 * local_count + 16:
            raise SignedProductNonzeroError("selected cone exceeds body/fuel bounds")
        _row_preflight(target, body, limits)
        nodes.append(BundleNode(remap[old], target, tuple(remap[d] for d in row[2]), body, row[0]))
    if count != 2315 or deepest != 40 or sum(len(row[2]) for row in rows) != 70:
        raise SignedProductNonzeroError("actual source-cone structural metrics changed")
    for old, pin in ENDPOINTS.items():
        if nodes[remap[old]].target != closed_formula(pin["source"]):
            raise SignedProductNonzeroError("actual endpoint differs from its literal target")
    return SignedProductCone(tuple(nodes), ids,
                             {old: remap[old] for old in ENDPOINTS}, count, deepest)


def _root_body():
    """Six dependencies, six binders, three premises, then output inequality.

    Below the two square witnesses, Hyp0 is square(q,m,v), Hyp1 square(p,n,u),
    Hyp2 r=s, Hyp3 q!=m, Hyp4 p!=n, Hyp5 the exact output balance; the six
    dependency hypotheses follow in reverse order. Only ordinary typed inference
    constructors appear. No ring, untyped local-have or solver replay is needed.
    """
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import (AndElimL, AndElimR, CongAdd, EqRefl,
        EqSym, EqTrans, ExistsElim, ForallIntro, Hyp, ImpElim, ImpIntro, OrElim)
    from peano_lab.kernel.terms import Add, Mul, Var
    p, n, q, m, r, s, u, v = (Var(i) for i in reversed(range(8)))
    positive = Add(Mul(p, q), Mul(n, m))
    negative = Add(Mul(p, m), Mul(n, q))

    def law(old_id):
        return Hyp(6 + len(ROOT_DEPENDENCIES) - 1 - ROOT_DEPENDENCIES.index(old_id))

    def apply(proof, *arguments):
        for argument in arguments:
            proof = ImpElim(proof, argument)
        return proof

    # negative+s = s+negative = r+negative = positive+s. Cancellation
    # works for overlapping representatives, including a noncanonical output.
    balanced_zero = EqTrans(instantiate(law(2), negative, s),
        EqTrans(CongAdd(EqSym(Hyp(2)), EqRefl(negative)), Hyp(5)))
    canonical_zero = EqSym(ImpElim(instantiate(law(27), negative, positive, s), balanced_zero))
    product_square = apply(instantiate(law(697), p, n, q, m, u, v), Hyp(1), Hyp(0))
    product_zero_iff = ImpElim(instantiate(law(713), positive, negative, Mul(u, v)), product_square)
    zero_product = ImpElim(AndElimR(product_zero_iff), canonical_zero)
    zero_factor = ImpElim(instantiate(law(22), u, v), zero_product)

    # Each OrElim branch adds precisely one hypothesis (u=0 or v=0).
    left_zero_iff = ImpElim(instantiate(Hyp(10), p, n, u), Hyp(2))
    right_zero_iff = ImpElim(instantiate(Hyp(10), q, m, v), Hyp(1))
    left_false = ImpElim(Hyp(5), ImpElim(AndElimL(left_zero_iff), Hyp(0)))
    right_false = ImpElim(Hyp(4), ImpElim(AndElimL(right_zero_iff), Hyp(0)))
    body = OrElim(zero_factor, left_false, right_false)

    # Before the second witness, q=Var4,m=Var3, existence law=Hyp10.
    body = ExistsElim(instantiate(Hyp(10), Var(4), Var(3)), body)
    # Before either witness, p=Var5,n=Var4, existence law=Hyp9.
    body = ExistsElim(instantiate(Hyp(9), Var(5), Var(4)), body)
    for _ in range(4):
        body = ImpIntro(body)
    for _ in PARAMETERS:
        body = ForallIntro(body)
    for _ in ROOT_DEPENDENCIES:
        body = ImpIntro(body)
    return body


def prove_signed_product_nonzero(*, limits=None, artifact_path=V28_ARTIFACT):
    """Root-owned worker only: regenerate and replay the complete SI001 bundle."""
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from peano_lab.library.proof_bundle import (BundleNode, ProofBundle,
        check_encoded_proof_bundle, encode_formula, encode_proof, encode_proof_bundle)
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise SignedProductNonzeroError("expected unchanged pilot limits")
    if len(ANCESTOR_IDS) + 1 > limits.max_nodes:
        raise SignedProductNonzeroError("SI001 node budget exhausted before construction")
    before = signed_product_nonzero_source_pins()
    target = frozen_signed_product_nonzero_target()
    cone = load_signed_product_cone(artifact_path, limits=limits)
    body = _root_body()
    local_count, local_depth = _body_metrics(body, limits)
    if cone.body_nodes + local_count > limits.max_total_body_nodes:
        raise SignedProductNonzeroError("SI001 aggregate ordinary body budget exhausted")
    _row_preflight(target, body, limits)
    dependencies = tuple(cone.endpoints[old] for old in ROOT_DEPENDENCIES)
    row_bytes = len(canonical([8 * local_count + 16, encode_formula(target), list(dependencies), encode_proof(body)])) + 1
    if SELECTED_ROWS_BYTES + row_bytes + len(canonical(encode_formula(target))) + 128 > limits.max_payload_bytes:
        raise SignedProductNonzeroError("SI001 aggregate canonical payload budget exhausted")
    root = len(cone.nodes)
    bundle = ProofBundle((*cone.nodes, BundleNode(root, target, dependencies, body)), root)
    payload = encode_proof_bundle(bundle, target, limits=limits.bundle_limits())
    receipt = check_encoded_proof_bundle(payload, limits=limits.bundle_limits())
    if receipt.target != target or json_hash(encode_formula(receipt.target)) != SIGNED_PRODUCT_NONZERO_TARGET_SHA256:
        raise SignedProductNonzeroError("fresh canonical replay changed SI001 target")
    if signed_product_nonzero_source_pins() != before:
        raise SignedProductNonzeroError("SI001 sources changed during proof production")
    provenance = dict(code="SI001", schema=SCHEMA,
        coverage="universal_signed_integer_binary_product_nonzero", source_pins=before,
        original_target_source=SIGNED_PRODUCT_NONZERO_SOURCE,
        original_target_ast_sha256=SIGNED_PRODUCT_NONZERO_TARGET_SHA256,
        original_HA_checked=True, canonical_bytes_replayed=True, empty_context=True,
        v28_artifact=dict(path=str(V28_ARTIFACT.relative_to(ROOT)), bytes=V28_ARTIFACT_SIZE,
                          sha256=V28_ARTIFACT_SHA256),
        actual_ancestor_ids=list(cone.original_ids), selected_rows_sha256=SELECTED_ROWS_SHA256,
        actual_ancestor_nodes=len(cone.nodes), actual_ancestor_body_nodes=cone.body_nodes,
        reused_endpoints={str(i): dict(pin) for i, pin in ENDPOINTS.items()},
        arbitrary_input_representatives=True, arbitrary_output_representatives=True,
        quadratic_field_claim=False, finite_product_claim=False,
        external_certificate_references=[], new_axioms=[],
        IR_parents_closed=0, closes_IR046=False, closes_IR072=False,
        library_admissions=0, independent_lean_checked=False)
    return SignedProductNonzeroCertificate(target, bundle, payload, receipt,
                                           max(cone.max_depth, local_depth), provenance)
