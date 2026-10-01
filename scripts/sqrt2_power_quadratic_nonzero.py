"""QN001: a binary product of nonzero represented Z[sqrt(2)] elements is nonzero.

Both coordinate balances and both input-nonzero hypotheses are explicit.
Input/output signed representatives need not be normalized. This is binary
integer-quadratic algebra, not a finite-product or irrationality completion.

Three source-authenticated archives supply complete ordinary SN001, SN003 and
SI001 bodies. Their status fields/receipts are never mathematical premises.
Identical dependency-curried rows are shared, with their ordered dependencies
remapped. Archives are read sequentially with bounded decompression; the three
large generators are never rerun. The final canonical payload is decoded once,
roundtripped through the original codec and checked node-by-node by the original
HA kernel. Only a root-owned bounded worker may invoke the proof producer.
"""

from __future__ import annotations

from dataclasses import dataclass
import gc
import gzip
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sqrt2-power-quadratic-nonzero-v1"
PARAMETERS = ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn", "rp", "rn", "sp", "sn")
REAL_SOURCE = "rp+((ap*cn+an*cp)+2*(bp*dn+bn*dp))=((ap*cp+an*cn)+2*(bp*dp+bn*dn))+rn"
RADICAL_SOURCE = "sp+((ap*dn+an*dp)+(bp*cn+bn*cp))=((ap*dp+an*dn)+(bp*cp+bn*cn))+sn"
NONZERO_SOURCES = ("~(ap=an /\\ bp=bn)", "~(cp=cn /\\ dp=dn)")
CONCLUSION_SOURCE = "~(rp=rn /\\ sp=sn)"
QUADRATIC_NONZERO_SOURCE = "forall " + " ".join(PARAMETERS) + ". " + " -> ".join((
    REAL_SOURCE, RADICAL_SOURCE, *NONZERO_SOURCES, CONCLUSION_SOURCE))
NAMED_SOURCE = "forall " + " ".join(PARAMETERS) + ". " + " -> ".join((
    "IQuadProductReal(ap,an,bp,bn,cp,cn,dp,dn,rp,rn)",
    "IQuadProductRadical(ap,an,bp,bn,cp,cn,dp,dn,sp,sn)",
    *NONZERO_SOURCES, CONCLUSION_SOURCE))
TARGET_SHA256 = "f4d0bc4f03497b4b9d2b601380b0958486e631f8a2c5f4d0b647b43662f18ca9"
SHUFFLE_SOURCE = "forall a b c d. (a*b)*(c*d)=(a*c)*(b*d)"
NEGATIVE_SOURCE = "forall a b c d. a*(2*d)+(2*b)*c=2*(a*d+b*c)"
OBSERVATIONS = "research/arithmetic-library/sqrt2-power/observations/"
ARCHIVES = {
    "SN001": dict(path=OBSERVATIONS + "shared-wave-signed-norm-v1/generation-process.json.gz",
        bytes=60438, sha256="40a1db06bd465b7a996db87b9f9eb88fff5040626867a4078ed275df7cb0079a",
        raw_bytes=2304728, raw_sha256="e747adce1f4fbce73bdcd81e0c45276dadd76f2b3b4bed3050ba2d21c6fb5efe",
        bundle_bytes=1439991, bundle_sha256="5685db9bdbe1ceb79e29a25dff767c519ccf424705a1e395dad5fcb3b01911de",
        target_sha256="c948aa0e7350e5c51c464721215573a489b0921c9d1a3263c9c5181f20164941",
        nodes=206, root=205),
    "SN003": dict(path=OBSERVATIONS + "shared-wave-norm-product-v1/generation-process.json.gz",
        bytes=65511, sha256="20c2a224121e804f3187393ffd31c89a7fef9ebc574fe28560b4baaa3c0f41c5",
        raw_bytes=2903863, raw_sha256="bd074f879cfc1d377d6a74b6119d16bf4c62cca7c508645e1fb861c9f3b3b7c8",
        bundle_bytes=1794186, bundle_sha256="93465c3527692a4b2614c0b54d30457b7f70682203477afd9afe9775d3977ebf",
        target_sha256="e123c3a589c565bfb3da565b09d0d7fd4e0ca431f884f790f02899bc10711bfa",
        nodes=37, root=36),
    "SI001": dict(path=OBSERVATIONS + "shared-wave-signed-product-nonzero-v1/generation-process.json.gz",
        bytes=12423, sha256="b00c52ddc14b5eaaf24a2a9173fae551cd4f13a8a3e09f89f250a1eef7cb7dc5",
        raw_bytes=260092, raw_sha256="3b89477a46adf192df4c2f71d2f8316165bb005d69254be32d1d5a8ec7088323",
        bundle_bytes=153728, bundle_sha256="e0fd91506b33ed8a390173ed0599e8980e2c99ade59b24c37be92cf05bcfbc38",
        target_sha256="ee1a6a3a9dfc5f7d45c67d4a040a8ff0ccf2d4422f2ddc42e1fad69334c2d581",
        nodes=34, root=33),
}
MERGED_ROWS_SHA256 = "d042a9d84c1245e6978770c83bc87145699f0a96d5fe25ca9a1d049d95045ff2"
MERGED_ROWS_BYTES = 3206485
MERGED_BODY_NODES = 81031
MERGED_ENDPOINTS = dict(SN001=191, SN003=214, SI001=217, square_exists=215,
    square_zero_iff=216, mul_assoc=8, mul_comm=6, mul_add=7)
ENDPOINT_SOURCES = {
    "square_exists": "forall p n. exists u. p*p+n*n=u+(p*n+n*p)",
    "square_zero_iff": "forall p n u. p*p+n*n=u+(p*n+n*p) -> ((u=0 -> p=n) /\\ (p=n -> u=0))",
    "mul_assoc": "forall a b c. (a*b)*c=a*(b*c)",
    "mul_comm": "forall a b. a*b=b*a",
    "mul_add": "forall a b c. a*(b+c)=a*b+a*c",
}
ROOT_DEPENDENCIES = ("SN001", "SN003", "SI001", "square_exists", "square_zero_iff", "shuffle", "negative")
PINNED_SOURCES = {
    "scripts/sqrt2_power_signed_norm.py": "4a042d1ba85b39816f9738bf53484e2642f602dafc22437f45503f02b2bd8294",
    "scripts/sqrt2_power_quadratic_norm_product.py": "2a82e6a6de97f58b0e30fd7b7e8d6380b64e0ae4d0af91bd9df336f571a1df5a",
    "scripts/sqrt2_power_signed_product_nonzero.py": "09e4665821328dce0dea61967ade5a32dbe668d091a03efd3fa545f86855f022",
    "scripts/sqrt2_power_definitions.py": "365f142974c3958aa5cad2430ed93fc3866e8abbadea0c357cb906574ff0220b",
    "scripts/sqrt2_power_quadratic_definitions.py": "f57c5151a1f711a1e844e49f2cec0e1f6cae84a43331737dc62bd54808c8f84a",
    "scripts/sqrt2_power_native.py": "9b51adc2699bf3c83c74749b9fc4723a8a1b8e234cef6f521a3f309fe646cc73",
    "scripts/sqrt2_power_binary_dag.py": "517535807fe06a317fae48c5fc5f47db944b0c32904fb8d02a0a1b102af12227",
    "peano-lab/py/peano_lab/library/proof_bundle.py": "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4",
    "peano-lab/py/peano_lab/kernel/checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "peano-lab/py/peano_lab/library/defined_syntax.py": "86b3ee6dc17043553e730372ac0d9af884a3fb85ebe6a30813318871145fe903",
    "book/_static/constructive-jordan-campaign-v35/definitions.json": "32da2185fd21fb1d0b400404f9b832425a4c35e75be392a3f5b5f73f8464aebf",
}


class QuadraticNonzeroError(ValueError):
    """Fail-closed exact target, source/body, topology or bounded-resource error."""


def canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()


def json_hash(value):
    return sha256(canonical(value)).hexdigest()


def quadratic_nonzero_source_pins():
    """Small literal sources and compressed proof inputs, never large generators."""
    expected = {**PINNED_SOURCES, **{pin["path"]: pin["sha256"] for pin in ARCHIVES.values()}}
    producer = "scripts/sqrt2_power_quadratic_nonzero.py"
    result = {}
    for name in sorted((*expected, producer)):
        raw = (ROOT / name).read_bytes()
        digest = sha256(raw).hexdigest()
        if len(raw) > 16 * 1024**2 or name in expected and digest != expected[name]:
            raise QuadraticNonzeroError("QN001 source changed: " + name)
        result[name] = dict(bytes=len(raw), sha256=digest)
    return result


def source_contract():
    return dict(code="QN001", source=NAMED_SOURCE, expanded_source=QUADRATIC_NONZERO_SOURCE,
        statement_ast_sha256=TARGET_SHA256, parameters=list(PARAMETERS), premise_count=4,
        arbitrary_signed_representatives=True, binary_quadratic_integer_product=True,
        finite_product_claim=False, irrationality_claim=False, closes_IR046=False,
        closes_IR072=False, IR_parents_closed=0, library_admissions=0,
        authority="source_contract_not_proof_authority", original_HA_checked=False)


def frozen_quadratic_nonzero_target():
    """Source expansion only. No archive, producer or proof checker is invoked."""
    from sqrt2_power_native import closed_formula
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_quadratic_definitions import QUADRATIC_DEFINITIONS
    from peano_lab.library.proof_bundle import encode_formula
    target = closed_formula(QUADRATIC_NONZERO_SOURCE)
    if json_hash(encode_formula(target)) != TARGET_SHA256:
        raise QuadraticNonzeroError("QN001 exact original target AST changed")
    if parse_named(NAMED_SOURCE, registry=QUADRATIC_DEFINITIONS) != target:
        raise QuadraticNonzeroError("QN001 conservative coordinate alias changed")
    return target


def read_archived_rows(code, *, archive_paths=None):
    """Bounded inert extraction of real canonical bodies, not a receipt lookup."""
    if code not in ARCHIVES:
        raise QuadraticNonzeroError("unknown archived parent")
    pin = ARCHIVES[code]
    path = ROOT / pin["path"] if archive_paths is None else Path(archive_paths[code])
    with path.open("rb") as stream:
        packed = stream.read(pin["bytes"] + 1)
    if len(packed) != pin["bytes"] or sha256(packed).hexdigest() != pin["sha256"]:
        raise QuadraticNonzeroError("archived proof input size/hash changed: " + code)
    with gzip.GzipFile(fileobj=BytesIO(packed), mode="rb") as stream:
        raw = stream.read(pin["raw_bytes"] + 1)
    del packed
    if len(raw) != pin["raw_bytes"] or sha256(raw).hexdigest() != pin["raw_sha256"]:
        raise QuadraticNonzeroError("archived proof envelope size/hash changed: " + code)
    process = json.loads(raw)
    del raw
    output = json.loads(process["stdout"])
    del process
    if output.get("case") != code or output.get("schema") != "sqrt2-power-shared-proof-wave-v1":
        raise QuadraticNonzeroError("archived canonical-body owner changed")
    payload = output["bundle"]
    del output
    if (type(payload) is not str or len(payload.encode()) != pin["bundle_bytes"]
            or sha256(payload.encode()).hexdigest() != pin["bundle_sha256"]):
        raise QuadraticNonzeroError("archived real bundle bytes changed: " + code)
    value = json.loads(payload)
    del payload
    if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
            or value[1] != pin["root"] or len(value[3]) != pin["nodes"]
            or json_hash(value[2]) != pin["target_sha256"]):
        raise QuadraticNonzeroError("archived real bundle shape changed: " + code)
    return value[1], value[2], value[3]


# Exact ordinary proof-child positions, for inert count/depth guards. The
# unchanged ordinary codec subsequently validates every term/formula as well.
_PROOF_CHILDREN = {
    "hyp": (), "axiom": (), "eq_refl": (), "dne": (),
    "imp_intro": (1,), "and_elim_l": (1,), "and_elim_r": (1,),
    "or_intro_l": (1,), "or_intro_r": (1,), "bot_elim": (1,),
    "forall_intro": (1,), "forall_elim": (1,), "eq_sym": (1,), "cong_s": (1,),
    "imp_elim": (1, 2), "and_intro": (1, 2), "exists_elim": (1, 2),
    "eq_trans": (1, 2), "cong_add": (1, 2), "cong_mul": (1, 2),
    "or_elim": (1, 2, 3), "exists_intro": (2,), "eq_subst": (2, 3),
    "ind": (2, 3), "cut": (3, 4),
}


def _inert_body_metrics(body, limits):
    pending = [(body, 1)]
    count = deepest = 0
    while pending:
        value, depth = pending.pop()
        if type(value) is not list or not value or value[0] not in _PROOF_CHILDREN:
            raise QuadraticNonzeroError("unknown ordinary proof constructor")
        count += 1
        deepest = max(deepest, depth)
        if count > limits.max_total_body_nodes or depth > limits.max_depth:
            raise QuadraticNonzeroError("ordinary body exceeds unchanged count/depth caps")
        pending.extend((value[i], depth + 1) for i in _PROOF_CHILDREN[value[0]])
    return count, deepest


def merge_archived_rows(*, limits=None, archive_paths=None):
    """Share exact dependency-curried rows; acceptance awaits final HA replay."""
    from sqrt2_power_binary_dag import BinaryDAGLimits
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise QuadraticNonzeroError("expected unchanged BinaryDAGLimits")
    if limits.max_nodes < 218 or limits.max_payload_bytes < MERGED_ROWS_BYTES:
        raise QuadraticNonzeroError("archived-cone node/byte budget exhausted")
    rows, known, endpoints, maps = [], {}, {}, {}
    body_nodes = deepest = duplicate_rows = 0
    bytes_so_far = 2
    for code in ARCHIVES:
        parent_root, parent_target, parent_rows = read_archived_rows(code, archive_paths=archive_paths)
        remap = {}
        for old, row in enumerate(parent_rows):
            dependencies = [remap[d] for d in row[2]]
            if len(set(dependencies)) != len(dependencies):
                raise QuadraticNonzeroError("row sharing would collapse ordered dependencies")
            changed = [row[0], row[1], dependencies, row[3]]
            raw = canonical(changed)
            key = sha256(raw).hexdigest()
            mapped = known.get(key)
            if mapped is None:
                if len(rows) >= limits.max_nodes:
                    raise QuadraticNonzeroError("merged ordinary-node budget exhausted")
                count, depth = _inert_body_metrics(changed[3], limits)
                body_nodes += count
                deepest = max(deepest, depth)
                bytes_so_far += len(raw) + (1 if rows else 0)
                if body_nodes > limits.max_total_body_nodes or bytes_so_far > limits.max_payload_bytes:
                    raise QuadraticNonzeroError("merged ordinary body/byte budget exhausted")
                if type(row[0]) is not int or row[0] < 8 * count + 16:
                    raise QuadraticNonzeroError("actual parent row has insufficient ordinary fuel")
                mapped = len(rows)
                known[key] = mapped
                rows.append(changed)
            else:
                if rows[mapped] != changed:
                    raise QuadraticNonzeroError("hash collision in exact body sharing")
                duplicate_rows += 1
            remap[old] = mapped
        endpoints[code] = remap[parent_root]
        if rows[endpoints[code]][1] != parent_target:
            raise QuadraticNonzeroError("sharing changed parent conclusion")
        maps[code] = tuple(remap[i] for i in range(len(parent_rows)))
        del parent_rows, parent_target, remap, row, changed, raw
    # SI001's actual archived node numbers are separately authenticated above.
    for name, index in dict(square_exists=26, square_zero_iff=32, mul_assoc=8,
                             mul_comm=6, mul_add=7).items():
        endpoints[name] = maps["SI001"][index]
    if (endpoints != MERGED_ENDPOINTS or len(rows) != 218 or duplicate_rows != 59
            or body_nodes != MERGED_BODY_NODES or deepest != 84
            or sum(len(row[2]) for row in rows) != 590
            or bytes_so_far != MERGED_ROWS_BYTES or json_hash(rows) != MERGED_ROWS_SHA256):
        raise QuadraticNonzeroError("source-authenticated merged cone changed")
    return rows, dict(endpoints=endpoints, parent_maps=maps, duplicate_rows=duplicate_rows,
                     body_nodes=body_nodes, max_depth=deepest, row_bytes=bytes_so_far)


def _close(body, binders, premises, dependencies):
    from peano_lab.kernel.proofs import ForallIntro, ImpIntro
    for _ in range(premises):
        body = ImpIntro(body)
    for _ in range(binders):
        body = ForallIntro(body)
    for _ in range(dependencies):
        body = ImpIntro(body)
    return body


def _shuffle_body():
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import CongMul, EqRefl, EqSym, EqTrans, Hyp
    from peano_lab.kernel.terms import Mul, Var
    a, b, c, d = (Var(i) for i in reversed(range(4)))
    def assoc(x, y, z):
        return instantiate(Hyp(1), x, y, z)
    middle = EqTrans(EqSym(assoc(b, c, d)), EqTrans(
        CongMul(instantiate(Hyp(0), b, c), EqRefl(d)), assoc(c, b, d)))
    body = EqTrans(assoc(a, b, Mul(c, d)), EqTrans(
        CongMul(EqRefl(a), middle), EqSym(assoc(a, c, Mul(b, d)))))
    return _close(body, 4, 0, 2)


def _negative_body():
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import CongAdd, CongMul, EqRefl, EqSym, EqTrans, Hyp
    from peano_lab.kernel.terms import Mul, Succ, Var, Zero
    a, b, c, d = (Var(i) for i in reversed(range(4)))
    two = Succ(Succ(Zero()))
    def assoc(x, y, z):
        return instantiate(Hyp(2), x, y, z)
    left = EqTrans(EqSym(assoc(a, two, d)), EqTrans(
        CongMul(instantiate(Hyp(1), a, two), EqRefl(d)), assoc(two, a, d)))
    body = EqTrans(CongAdd(left, assoc(two, b, c)),
                   EqSym(instantiate(Hyp(0), two, Mul(a, d), Mul(b, c))))
    return _close(body, 4, 0, 3)


def _root_body():
    """Seven dependencies, twelve binders, four premises, six square witnesses.

    Below the witnesses: Hyp0..5 are squares t,r,d,c,b,a; Hyp6 says the output
    pair is zero; Hyp7/8 say the right/left input pairs are nonzero; Hyp9/10
    are the radical/real balances. The seven law hypotheses then follow in
    reverse ROOT_DEPENDENCIES order. Every inference is an ordinary HA term.
    """
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import (AndElimL, AndElimR, Axiom, CongAdd, CongMul,
        EqRefl, EqSym, EqTrans, ExistsElim, Hyp, ImpElim, ImpIntro)
    from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
    values = tuple(Var(i) for i in reversed(range(18)))
    ap, an, bp, bn, cp, cn, dp, dn, rp, rn, sp, sn, a, b, c, d, r, t = values
    two = Succ(Succ(Zero()))
    def law(name):
        return Hyp(11 + len(ROOT_DEPENDENCIES) - 1 - ROOT_DEPENDENCIES.index(name))
    def apply(proof, *premises):
        for premise in premises:
            proof = ImpElim(proof, premise)
        return proof

    # Each nonzero-norm implication has one additional equality hypothesis.
    left_pair_zero = apply(instantiate(Hyp(18), ap, an, bp, bn, a, b), Hyp(6), Hyp(5), Hyp(0))
    right_pair_zero = apply(instantiate(Hyp(18), cp, cn, dp, dn, c, d), Hyp(4), Hyp(3), Hyp(0))
    left_norm_nonzero = ImpIntro(ImpElim(Hyp(9), left_pair_zero))
    right_norm_nonzero = ImpIntro(ImpElim(Hyp(8), right_pair_zero))

    integer_identity = apply(instantiate(law("SN003"), *values),
        Hyp(5), Hyp(4), Hyp(3), Hyp(2), Hyp(1), Hyp(0), Hyp(10), Hyp(9))
    positive = CongAdd(EqRefl(Mul(a, c)), instantiate(law("shuffle"), two, b, two, d))
    negative = instantiate(law("negative"), a, b, c, d)
    balance = EqTrans(CongAdd(EqRefl(r), negative), EqTrans(integer_identity,
        CongAdd(EqSym(positive), EqRefl(Mul(two, t)))))
    nonzero_output_norm = apply(instantiate(law("SI001"), a, Mul(two, b), c, Mul(two, d), r, Mul(two, t)),
        balance, left_norm_nonzero, right_norm_nonzero)

    r_zero_iff = ImpElim(instantiate(law("square_zero_iff"), rp, rn, r), Hyp(1))
    t_zero_iff = ImpElim(instantiate(law("square_zero_iff"), sp, sn, t), Hyp(0))
    r_zero = ImpElim(AndElimR(r_zero_iff), AndElimL(Hyp(6)))
    t_zero = ImpElim(AndElimR(t_zero_iff), AndElimR(Hyp(6)))
    zero_output_norm = EqTrans(r_zero, EqTrans(EqSym(instantiate(Axiom("PA5"), two)),
        CongMul(EqRefl(two), EqSym(t_zero))))
    body = ImpElim(nonzero_output_norm, zero_output_norm)
    # At k existing witnesses the next coordinate pair has indices 11-k,10-k,
    # and the square-existence theorem has hypothesis index 8+k.
    for k in reversed(range(6)):
        body = ExistsElim(instantiate(Hyp(8 + k), Var(11 - k), Var(10 - k)), body)
    return _close(body, 12, 5, len(ROOT_DEPENDENCIES))


@dataclass(frozen=True)
class QuadraticNonzeroCertificate:
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


def prove_quadratic_nonzero(*, limits=None, archive_paths=None):
    """Root worker: assemble actual shared bodies, then replay all 221 nodes."""
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from sqrt2_power_native import closed_formula
    from peano_lab.library.proof_bundle import (check_proof_bundle, decode_proof_bundle,
        encode_formula, encode_proof, encode_proof_bundle)
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise QuadraticNonzeroError("expected unchanged BinaryDAGLimits")
    if limits.max_nodes < 221 or limits.max_total_body_nodes < MERGED_BODY_NODES:
        raise QuadraticNonzeroError("QN001 node/body budget exhausted before construction")
    before = quadratic_nonzero_source_pins()
    target = frozen_quadratic_nonzero_target()
    rows, metrics = merge_archived_rows(limits=limits, archive_paths=archive_paths)
    endpoints = dict(metrics["endpoints"])
    for name, source in ENDPOINT_SOURCES.items():
        if rows[endpoints[name]][1] != encode_formula(closed_formula(source)):
            raise QuadraticNonzeroError("actual arithmetic endpoint differs from literal source")
    total, deepest = metrics["body_nodes"], metrics["max_depth"]
    encoded_bytes = metrics["row_bytes"]
    def append(formula, dependencies, proof):
        nonlocal total, deepest, encoded_bytes
        if len(rows) >= limits.max_nodes or len(set(dependencies)) != len(dependencies):
            raise QuadraticNonzeroError("new node/dependency budget failure")
        if any(type(i) is not int or not 0 <= i < len(rows) for i in dependencies):
            raise QuadraticNonzeroError("new non-topological dependency")
        count, depth = _body_metrics(proof, limits)
        total += count
        deepest = max(deepest, depth)
        if total > limits.max_total_body_nodes:
            raise QuadraticNonzeroError("aggregate ordinary body budget exhausted")
        _row_preflight(formula, proof, limits)
        row = [8 * count + 16, encode_formula(formula), list(dependencies), encode_proof(proof)]
        encoded_bytes += len(canonical(row)) + 1
        if encoded_bytes + len(canonical(encode_formula(target))) + 128 > limits.max_payload_bytes:
            raise QuadraticNonzeroError("aggregate canonical payload budget exhausted")
        identifier = len(rows)
        rows.append(row)
        return identifier
    endpoints["shuffle"] = append(closed_formula(SHUFFLE_SOURCE),
        (endpoints["mul_assoc"], endpoints["mul_comm"]), _shuffle_body())
    endpoints["negative"] = append(closed_formula(NEGATIVE_SOURCE),
        (endpoints["mul_assoc"], endpoints["mul_comm"], endpoints["mul_add"]), _negative_body())
    dependencies = tuple(endpoints[name] for name in ROOT_DEPENDENCIES)
    root = append(target, dependencies, _root_body())
    payload = canonical(["peano-lab-bundle-v1", root, encode_formula(target), rows]).decode() + "\n"
    # Do not retain inert trees while decoding full ordinary bodies. No parent
    # certificate objects or three regenerated parent bundles coexist here.
    del rows
    gc.collect()
    bundle, decoded_target = decode_proof_bundle(payload, limits=limits.bundle_limits())
    if decoded_target != target or encode_proof_bundle(bundle, target, limits=limits.bundle_limits()) != payload:
        raise QuadraticNonzeroError("QN001 final canonical bytes failed original-codec roundtrip")
    receipt = check_proof_bundle(bundle, target, limits=limits.bundle_limits())
    if (receipt.target != target or receipt.total_body_nodes != total
            or quadratic_nonzero_source_pins() != before):
        raise QuadraticNonzeroError("QN001 exact body, target or source changed during replay")
    provenance = dict(code="QN001", schema=SCHEMA,
        coverage="binary_quadratic_integer_nonzero_not_finite_product_IR046",
        source_pins=before, original_target_source=NAMED_SOURCE,
        original_target_ast_sha256=TARGET_SHA256,
        original_HA_checked=True, canonical_bytes_replayed=True, empty_context=True,
        archived_full_bundles={code: dict(pin) for code, pin in ARCHIVES.items()},
        archive_status_is_proof_authority=False, regenerated_parent_generators=0,
        actual_shared_ancestor_nodes=218, actual_shared_ancestor_body_nodes=MERGED_BODY_NODES,
        exact_duplicate_rows_shared=59, merged_rows_sha256=MERGED_ROWS_SHA256,
        parent_root_nodes={name: endpoints[name] for name in ARCHIVES},
        actual_source_endpoint_nodes={name: endpoints[name] for name in ENDPOINT_SOURCES},
        root_dependencies=list(dependencies), internal_helpers_counted_as_campaign_results=False,
        arbitrary_signed_representatives=True, finite_product_claim=False,
        irrationality_claim=False, external_certificate_references=[], new_axioms=[],
        new_definitions=[], IR_parents_closed=0, closes_IR046=False, closes_IR072=False,
        library_admissions=0, independent_lean_checked=False,
        worker_enforcement="external root-owned single-worker supervisor required")
    return QuadraticNonzeroCertificate(target, bundle, payload, receipt, deepest, provenance)
