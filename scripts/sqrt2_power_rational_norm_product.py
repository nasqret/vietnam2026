"""RN002: rational norm multiplication with explicit nonzero denominators.

SN003 supplies the signed integer identity. Ordinary universal semiring laws
transport its two sides and the squared product denominator into the existing
IRatMul relation. No real interpretation, new alias, axiom, or admission.
Execute producers only in the root-owned bounded single-worker supervisor.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import sqrt2_power_quadratic_norm_product as integer
from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight, formula_sha256
from sqrt2_power_definitions import DEFINITIONS, parse_named
from sqrt2_power_native import Basis, closed_formula, instantiate
from sqrt2_power_quadratic_definitions import QUADRATIC_DEFINITIONS
from sqrt2_power_signed_norm import signed_difference_definition
from peano_lab.kernel.formulas import pretty_formula
from peano_lab.kernel.proofs import AndIntro, CongAdd, CongMul, EqRefl, EqSym, EqTrans, ForallIntro, Hyp, ImpElim, ImpIntro
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.library.proof_bundle import BundleNode, ProofBundle, check_encoded_proof_bundle, encode_proof_bundle

ROOT = integer.ROOT
PARENT_PRODUCER_SHA256 = "2a82e6a6de97f58b0e30fd7b7e8d6380b64e0ae4d0af91bd9df336f571a1df5a"
PARENT_BUNDLE_SHA256 = "93465c3527692a4b2614c0b54d30457b7f70682203477afd9afe9775d3977ebf"
PARAMETERS = (*integer.PARAMETERS, "u", "v")
NAMED_SOURCE = (
    "forall " + " ".join(PARAMETERS) + ". ~(u=0) -> ~(v=0) -> "
    "SignedDifferenceSquare(ap,an,a) -> SignedDifferenceSquare(bp,bn,b) -> "
    "SignedDifferenceSquare(cp,cn,c) -> SignedDifferenceSquare(dp,dn,d) -> "
    "SignedDifferenceSquare(rp,rn,r) -> SignedDifferenceSquare(sp,sn,t) -> "
    "IQuadProductReal(ap,an,bp,bn,cp,cn,dp,dn,rp,rn) -> "
    "IQuadProductRadical(ap,an,bp,bn,cp,cn,dp,dn,sp,sn) -> "
    "IRatMul(a,2*b,u*u,c,2*d,v*v,r,2*t,(u*v)*(u*v))"
)
TARGET_SHA256 = "ab88f7b597011f85f10d543e582abb37db52852d940b4b7a8c4c2cf7ae22c335"
LAW_NAMES = ("mul_ne_zero", "mul_assoc", "mul_comm", "mul_add", "add_mul", "add_comm")
SHUFFLE_SOURCE = "forall a b c d. (a*b)*(c*d)=(a*c)*(b*d)"
NEGATIVE_SOURCE = "forall a b c d. a*(2*d)+(2*b)*c=2*(a*d+b*c)"


class RationalNormProductError(ValueError):
    """Changed exact statement, ancestor, or unchanged resource boundary."""


def definition_registry():
    square = signed_difference_definition()
    return {**DEFINITIONS, **QUADRATIC_DEFINITIONS, square.name: square}


def frozen_rational_norm_product_target():
    target = parse_named(NAMED_SOURCE, registry=definition_registry())
    if formula_sha256(target) != TARGET_SHA256:
        raise RationalNormProductError("RN002 original target AST pin changed")
    if closed_formula(pretty_formula(target, [])) != target:
        raise RationalNormProductError("RN002 exact expansion roundtrip failed")
    return target


def rational_norm_product_source_pins():
    pins = integer.norm_product_source_pins()
    if pins["scripts/sqrt2_power_quadratic_norm_product.py"]["sha256"] != PARENT_PRODUCER_SHA256:
        raise RationalNormProductError("SN003 original producer changed")
    for name in (Path(__file__).name, "sqrt2_power_definitions.py", "sqrt2_power_quadratic_definitions.py", "sqrt2_power_signed_norm.py"):
        path = ROOT / "scripts" / name
        raw = path.read_bytes()
        if len(raw) > 16*1024**2:
            raise RationalNormProductError("RN002 source exceeds archival cap")
        pins[str(path.relative_to(ROOT))] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    return pins


def _apply(proof, *premises):
    for premise in premises:
        proof = ImpElim(proof, premise)
    return proof


def _close(proof, binders, premises, dependencies):
    for _ in range(premises):
        proof = ImpIntro(proof)
    for _ in range(binders):
        proof = ForallIntro(proof)
    for _ in range(dependencies):
        proof = ImpIntro(proof)
    return proof


def _shuffle_body():
    # Dependencies: mul_assoc, mul_comm. No normalization or search.
    a,b,c,d = (Var(i) for i in reversed(range(4)))
    def assoc(x,y,z):
        return instantiate(Hyp(1),x,y,z)
    middle = EqTrans(EqSym(assoc(b,c,d)), EqTrans(
        CongMul(instantiate(Hyp(0),b,c), EqRefl(d)), assoc(c,b,d)))
    result = EqTrans(assoc(a,b,Mul(c,d)), EqTrans(
        CongMul(EqRefl(a),middle), EqSym(assoc(a,c,Mul(b,d)))))
    return _close(result,4,0,2)


def _negative_body():
    # Dependencies: mul_assoc, mul_comm, mul_add.
    a,b,c,d = (Var(i) for i in reversed(range(4)))
    two = Succ(Succ(Zero()))
    def assoc(x,y,z):
        return instantiate(Hyp(2),x,y,z)
    left = EqTrans(EqSym(assoc(a,two,d)), EqTrans(
        CongMul(instantiate(Hyp(1),a,two),EqRefl(d)), assoc(two,a,d)))
    result = EqTrans(CongAdd(left,assoc(two,b,c)),
        EqSym(instantiate(Hyp(0),two,Mul(a,d),Mul(b,c))))
    return _close(result,4,0,3)


def _root_body():
    # Ordered dependencies: SN003, six LAW_NAMES, shuffle, negative helper.
    names = ("SN003",*LAW_NAMES,"shuffle","negative")
    values = tuple(Var(i) for i in reversed(range(20)))
    *original,u,v = values
    a,b,c,d,r,t = original[-6:]
    two = Succ(Succ(Zero()))
    def law(name):
        return Hyp(10+len(names)-1-names.index(name))
    def nz(x,y,hx,hy):
        return _apply(instantiate(law("mul_ne_zero"),x,y),hx,hy)
    uu,vv,uv = Mul(u,u),Mul(v,v),Mul(u,v)
    D,E = Mul(uv,uv),Mul(uu,vv)
    kp = Add(Mul(a,c),Mul(Mul(two,b),Mul(two,d)))
    kn = Add(Mul(a,Mul(two,d)),Mul(Mul(two,b),c))
    rt = Mul(two,t)
    integer_identity = _apply(instantiate(law("SN003"),*original),*(Hyp(i) for i in reversed(range(8))))
    positive = CongAdd(EqRefl(Mul(a,c)),instantiate(law("shuffle"),two,b,two,d))
    negative = instantiate(law("negative"),a,b,c,d)
    balance = EqTrans(CongAdd(EqRefl(r),negative), EqTrans(integer_identity,
        CongAdd(EqSym(positive),EqRefl(rt))))
    denominator = instantiate(law("shuffle"),u,v,u,v)
    # r*E + kn*D = (r+kn)*E = (kp+2t)*E = 2t*E + kp*D.
    left = EqTrans(CongAdd(EqRefl(Mul(r,E)),CongMul(EqRefl(kn),denominator)),
        EqSym(instantiate(law("add_mul"),r,kn,E)))
    right = EqTrans(CongMul(instantiate(law("add_comm"),kp,rt),EqRefl(E)), EqTrans(
        instantiate(law("add_mul"),rt,kp,E),
        CongAdd(EqRefl(Mul(rt,E)),CongMul(EqRefl(kp),EqSym(denominator)))))
    cross = EqTrans(left,EqTrans(CongMul(balance,EqRefl(E)),right))
    hu,hv = Hyp(9),Hyp(8)
    huu,hvv = nz(u,u,hu,hu),nz(v,v,hv,hv)
    huv = nz(u,v,hu,hv)
    equality = AndIntro(nz(uv,uv,huv,huv),AndIntro(nz(uu,vv,huu,hvv),cross))
    result = AndIntro(huu,AndIntro(hvv,equality))
    return _close(result,20,10,len(names))


@dataclass(frozen=True)
class RationalNormProductCertificate:
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
        return formula_sha256(self.target)


def prove_rational_norm_product(*,limits=BinaryDAGLimits(),artifact_path=integer.V28_ARTIFACT):
    if type(limits) is not BinaryDAGLimits:
        raise RationalNormProductError("expected unchanged resource limits")
    before = rational_norm_product_source_pins()
    target = frozen_rational_norm_product_target()
    if limits.max_nodes < 46:
        raise RationalNormProductError("RN002 node budget exhausted before generation")
    basis = Basis()
    parent = integer.prove_quadratic_norm_product(basis,limits=limits,artifact_path=artifact_path)
    if parent.payload_sha256 != PARENT_BUNDLE_SHA256 or len(parent.bundle.nodes) != 37:
        raise RationalNormProductError("SN003 exact dependency bundle changed")
    nodes = list(parent.bundle.nodes)
    total = parent.receipt.total_body_nodes
    deepest = parent.max_proof_depth
    def append(formula,dependencies,body):
        nonlocal total,deepest
        if len(nodes) >= limits.max_nodes or len(set(dependencies)) != len(dependencies):
            raise RationalNormProductError("node/dependency budget exceeded")
        if any(type(d) is not int or not 0 <= d < len(nodes) for d in dependencies):
            raise RationalNormProductError("non-topological dependency")
        count,depth = _body_metrics(body,limits)
        total += count
        deepest = max(deepest,depth)
        if total > limits.max_total_body_nodes:
            raise RationalNormProductError("aggregate proof-body budget exceeded")
        _row_preflight(formula,body,limits)
        identifier = len(nodes)
        nodes.append(BundleNode(identifier,formula,tuple(dependencies),body))
        return identifier
    laws = {}
    for name in LAW_NAMES:
        law = basis.get(name)
        laws[name] = append(law.formula,(),law.certificate)
    shuffle = append(closed_formula(SHUFFLE_SOURCE),(laws["mul_assoc"],laws["mul_comm"]),_shuffle_body())
    negative = append(closed_formula(NEGATIVE_SOURCE),
        (laws["mul_assoc"],laws["mul_comm"],laws["mul_add"]),_negative_body())
    dependencies = (parent.bundle.root,*(laws[n] for n in LAW_NAMES),shuffle,negative)
    root = append(target,dependencies,_root_body())
    bundle = ProofBundle(tuple(nodes),root)
    payload = encode_proof_bundle(bundle,target,limits=limits.bundle_limits())
    receipt = check_encoded_proof_bundle(payload,limits=limits.bundle_limits())
    if receipt.target != target or rational_norm_product_source_pins() != before:
        raise RationalNormProductError("RN002 target/source changed during ordinary replay")
    provenance = dict(case="RN002",claim="rational norm multiplication with product denominator",
        source_pins=before,original_target_source=NAMED_SOURCE,original_target_ast_sha256=TARGET_SHA256,
        SN003_bundle_sha256=parent.payload_sha256,SN003_target_ast_sha256=parent.target_ast_sha256,
        root_dependencies=list(dependencies),complete_parent_nodes=37,
        total_body_nodes=receipt.total_body_nodes,max_proof_depth=deepest,
        limits=dict(vars(limits)),ordinary_HA_checked_from_canonical_bytes=True,
        new_definitions=[],new_axioms=[],IR_parents_closed=0,library_admissions=0,
        independent_lean_checked=False,real_interpretation=False,arbitrary_output_denominator=False,
        worker_enforcement="external root-owned single-worker supervisor required")
    return RationalNormProductCertificate(target,bundle,payload,receipt,deepest,provenance)
