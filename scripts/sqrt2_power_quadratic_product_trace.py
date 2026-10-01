"""QF001: nonvanishing along an actual finite Z[sqrt(2)] product trace.

Four beta streams decode each factor and each accumulator. The trace starts at
one and supplies every executed transition with both coordinate balances. Its
definition contains no nonzero condition: nonzero factors are a separate
premise. Ordinary HA induction proves nonvanishing of every supplied terminal
tuple. Trace existence, rational denominators, real interpretation and IR046
closure are not claimed.

Only the root-owned guarded worker may construct/check proofs. Imports, target
binding, definition manifests and archive inspection are inert. The complete
archived QN001 proof and actual v28 beta/order ancestors are retained, with
lossless ordered-dependency remapping; no receipt is a mathematical premise.
"""
from __future__ import annotations

from dataclasses import dataclass
import gc
import gzip
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from types import MappingProxyType


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sqrt2-power-quadratic-product-trace-v1"
FACTOR_PARAMETERS = ("ab", "ac", "bb", "bc", "cb", "cc", "db", "dc")
TRACE_PARAMETERS = ("ub", "uc", "vb", "vc", "wb", "wc", "xb", "xc")
PARAMETERS = FACTOR_PARAMETERS + TRACE_PARAMETERS + ("L", "rp", "rn", "sp", "sn")
NAMED_SOURCE = (
    "forall " + " ".join(PARAMETERS) + ". "
    "IQuadProductTrace(ab,ac,bb,bc,cb,cc,db,dc,ub,uc,vb,vc,wb,wc,xb,xc,L) -> "
    "IQuadNonzeroFactors(ab,ac,bb,bc,cb,cc,db,dc,L) -> "
    "IQuadAt(ub,uc,vb,vc,wb,wc,xb,xc,L,rp,rn,sp,sn) -> ~(rp=rn /\\ sp=sn)"
)
TARGET_SHA256 = "d27f07d45ef919c5b7597e15e774478ab7ae46fc82e18fd16fa82e860df90768"
DEFINITION_ROWS = (
    (390, "IQuadAt", FACTOR_PARAMETERS + ("i", "ap", "an", "bp", "bn"),
     "BetaAt(ab,ac,i,ap) /\\ (BetaAt(bb,bc,i,an) /\\ (BetaAt(cb,cc,i,bp) /\\ BetaAt(db,dc,i,bn)))",
     ("BetaAt",), "Four actual beta-decoded natural components represent one signed quadratic integer.",
     "be83fdac7075423329c490d6cfc3bcbddb5c96a5c3cfedc41d79fcc16d4c5c14"),
    (391, "IQuadProductStep", FACTOR_PARAMETERS + TRACE_PARAMETERS + ("i",),
     "exists ap an bp bn cp cn dp dn rp rn sp sn. "
     "IQuadAt(ab,ac,bb,bc,cb,cc,db,dc,i,cp,cn,dp,dn) /\\ "
     "(IQuadAt(ub,uc,vb,vc,wb,wc,xb,xc,i,ap,an,bp,bn) /\\ "
     "(IQuadAt(ub,uc,vb,vc,wb,wc,xb,xc,S i,rp,rn,sp,sn) /\\ "
     "(IQuadProductReal(ap,an,bp,bn,cp,cn,dp,dn,rp,rn) /\\ "
     "IQuadProductRadical(ap,an,bp,bn,cp,cn,dp,dn,sp,sn))))",
     ("IQuadAt", "IQuadProductReal", "IQuadProductRadical"),
     "One actual factor/current/successor decoding and both multiplication balances; no nonzero assumption.",
     "5c9a0f28c62bc23ddd741aeacd7123e556166c81ac84165e0580a7c2b7117f38"),
    (392, "IQuadProductTrace", FACTOR_PARAMETERS + TRACE_PARAMETERS + ("L",),
     "IQuadAt(ub,uc,vb,vc,wb,wc,xb,xc,0,1,0,0,0) /\\ "
     "(forall i. Lt(i,L) -> "
     "IQuadProductStep(ab,ac,bb,bc,cb,cc,db,dc,ub,uc,vb,vc,wb,wc,xb,xc,i))",
     ("IQuadAt", "Lt", "IQuadProductStep"),
     "A supplied length-L multiplication trace starts at one and executes every factor; existence is not assumed.",
     "bd0d3a879af54dad64319f3e8f564cd4cd3adb4700c964e41e0090d33a439091"),
    (393, "IQuadNonzeroFactors", FACTOR_PARAMETERS + ("L",),
     "forall i ap an bp bn. Lt(i,L) -> "
     "IQuadAt(ab,ac,bb,bc,cb,cc,db,dc,i,ap,an,bp,bn) -> ~(ap=an /\\ bp=bn)",
     ("Lt", "IQuadAt"),
     "Every decoded factor below L is represented nonzero; this is a separate premise, not part of the trace.",
     "9bf7d53e3cdc2fbdcb6f55355c20281e4cade06f06634ad99259d2e7d979143c"),
)
BASE_DEFINITION_PINS = {
    "Lt": ("PD0002", "d7bdf8ed287c3672fa78951c9cabe8f8814d7fcf1fb1ffcfee2d0d3b41251531"),
    "BetaAt": ("PD0013", "b2a23ea9cf6373c9ee8a9c2a74cbcffde69a806b04ed3f831e7a9b00d445bdeb"),
}
QN_SOURCE = (
    "forall ap an bp bn cp cn dp dn rp rn sp sn. "
    "rp+((ap*cn+an*cp)+2*(bp*dn+bn*dp))=((ap*cp+an*cn)+2*(bp*dp+bn*dn))+rn -> "
    "sp+((ap*dn+an*dp)+(bp*cn+bn*cp))=((ap*dp+an*dn)+(bp*cp+bn*cn))+sn -> "
    "~(ap=an /\\ bp=bn) -> ~(cp=cn /\\ dp=dn) -> ~(rp=rn /\\ sp=sn)"
)
QN_TARGET_SHA256 = "f4d0bc4f03497b4b9d2b601380b0958486e631f8a2c5f4d0b647b43662f18ca9"
# Actual first-success canonical-body archive, not the associated receipt.
QN_ARCHIVE = dict(
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-quadratic-nonzero-v1/generation-process.json.gz",
    bytes=116021, sha256="820fce36ad833e6e5add0c847bdbc4650453c6aaf8cb259fd9c076278b9bf2a7",
    raw_bytes=5158596, raw_sha256="184651346459da245600feeaeb186b8f358dd75ac788af27ca1a27a912ec57db",
    bundle_bytes=3214045, bundle_sha256="faeb2544f48735855f80ba183dc596190cc4d788f804ed57af793bd6a7b89aa3",
    nodes=221, root=220)

V28_ARTIFACT = ROOT / "research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json"
V28_ARTIFACT_SIZE = 18977050
V28_ARTIFACT_SHA256 = "e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1"
ANCESTOR_IDS = (0, 1, 2, 3, 4, 5, 6, 7, 12, 14, 20, 23, 27, 28, 40, 51, 58, 59, 122)
ANCESTOR_IDS_SHA256 = "e4c8a11df3c88703db017e65cf1316fa03ebd4f8e0794d72e026ac13ece84498"
ANCESTOR_ROWS_SHA256 = "3094a62f40003fe5005170a27bb5647071a57cd17e4b957072b7f6fd5400eb74"
ANCESTOR_ROWS_BYTES = 22720
ENDPOINTS = {
    12: dict(name="succ_ne_zero", dependencies=(), source="forall a. ~(S a=0)",
        target_sha256="1d14966fc6d0c7b29a1255ddd924cb7dd48e8d837e322e9caf54de30d93437e9",
        row_sha256="bbcec3df19f5c107243f94f2902d6236e03d066cc437fa2a281c30cf27630539"),
    14: dict(name="le_refl", dependencies=(0,), source="forall a. exists h. h+a=a",
        target_sha256="99f830530a52827ae8a3c86bb82bb71662f6f69d1910a238d7c04a455c76bde0",
        row_sha256="5d67d5564fa913d869e0c0eefb7a980638c6e0a27629442d3e36a23f023641ec"),
    40: dict(name="le_succ", dependencies=(1,),
        source="forall a b. (exists h. h+a=b) -> exists h. h+a=S b",
        target_sha256="db33a04afbac985694c01e2b057376017e100efe24741f91709c03a4390328c5",
        row_sha256="e4974edfb9475843a1f33a104fb835f56e7b30adc42ba3020a819ba4f0c56cf9"),
    122: dict(name="beta_at_unique", dependencies=(6, 59),
        source="forall b c i x y. ((exists h. h+S x=S((S i)*c)) /\\ exists q. b=q*S((S i)*c)+x) -> ((exists h. h+S y=S((S i)*c)) /\\ exists q. b=q*S((S i)*c)+y) -> x=y",
        target_sha256="e18aaa05ec7ec5a5a4b47e6a83c6279015d2f0f4f0632b38c670f7367ec1ac6b",
        row_sha256="e2b7ae7323f857c82e6cf6a273bb7511fa28fc356ae6f06e685c5286fc362a3c"),
}
ROOT_DEPENDENCIES = (12, 14, 40, 122, "QN001")
PINNED_SOURCES = {
    "scripts/sqrt2_power_native.py": "9b51adc2699bf3c83c74749b9fc4723a8a1b8e234cef6f521a3f309fe646cc73",
    "scripts/sqrt2_power_binary_dag.py": "517535807fe06a317fae48c5fc5f47db944b0c32904fb8d02a0a1b102af12227",
    "scripts/sqrt2_power_definitions.py": "365f142974c3958aa5cad2430ed93fc3866e8abbadea0c357cb906574ff0220b",
    "scripts/sqrt2_power_quadratic_definitions.py": "f57c5151a1f711a1e844e49f2cec0e1f6cae84a43331737dc62bd54808c8f84a",
    "peano-lab/py/peano_lab/library/defined_syntax.py": "86b3ee6dc17043553e730372ac0d9af884a3fb85ebe6a30813318871145fe903",
    "peano-lab/py/peano_lab/library/finite_fold_surface.py": "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30",
    "peano-lab/py/peano_lab/library/proof_bundle.py": "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4",
    "peano-lab/py/peano_lab/kernel/checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "peano-lab/py/peano_lab/kernel/formulas.py": "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    "peano-lab/py/peano_lab/kernel/proofs.py": "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    "peano-lab/py/peano_lab/kernel/terms.py": "f49313e209a8861918e3aaca38ddfb27f147f824308af699ab5cc1aafbb6dff5",
    "book/_static/constructive-jordan-campaign-v35/definitions.json": "32da2185fd21fb1d0b400404f9b832425a4c35e75be392a3f5b5f73f8464aebf",
}


class QuadraticProductTraceError(ValueError):
    """Changed exact source, full proof ancestor, definition or unchanged cap."""


def canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()


def json_hash(value):
    return sha256(canonical(value)).hexdigest()


def definition_registry():
    """Eight exact old/new templates, scoped locally, no global registration."""
    from sqrt2_power_definitions import DEFINITIONS, PARENT, PARENT_SHA256, parse_named
    from sqrt2_power_quadratic_definitions import QUADRATIC_DEFINITIONS
    from peano_lab.kernel.formulas import pretty_formula, parse_formula_in_context
    from peano_lab.library.defined_syntax import DEFINITIONS_BY_NAME, _definition
    from peano_lab.library.proof_bundle import encode_formula
    raw = PARENT.read_bytes()
    if sha256(raw).hexdigest() != PARENT_SHA256:
        raise QuadraticProductTraceError("immutable definition parent changed")
    old = json.loads(raw)["reviewed_definitions"]
    used_names = {d["name"] for d in old} | set(DEFINITIONS) | set(QUADRATIC_DEFINITIONS)
    used_ids = {d["id"] for d in old} | {d.stable_id for d in DEFINITIONS.values()} | {d.stable_id for d in QUADRATIC_DEFINITIONS.values()}
    registry = {}
    for name, (identifier, digest) in BASE_DEFINITION_PINS.items():
        definition = DEFINITIONS_BY_NAME[name]
        if definition.stable_id != identifier or json_hash(encode_formula(definition.template_formula)) != digest:
            raise QuadraticProductTraceError("existing beta/order definition changed")
        registry[name] = definition
    registry.update(QUADRATIC_DEFINITIONS)
    for number, name, parameters, source, dependencies, summary, digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if name in used_names or identifier in used_ids or not set(dependencies) <= registry.keys():
            raise QuadraticProductTraceError("trace definition collision/forward dependency")
        formula = parse_named(source, parameters, registry=registry)
        if json_hash(encode_formula(formula)) != digest:
            raise QuadraticProductTraceError("trace definition expanded AST changed")
        expanded = pretty_formula(formula, list(parameters))
        definition = _definition(stable_id=identifier, name=name, parameters=parameters,
            template_source=expanded, summary=summary, category="irrationality_quadratic_traces",
            conceptual_dependencies=dependencies)
        if definition.template_formula != formula or parse_formula_in_context(expanded, list(parameters)) != formula:
            raise QuadraticProductTraceError("trace definition failed exact ordinary roundtrip")
        registry[name] = definition
        used_names.add(name)
        used_ids.add(identifier)
    return MappingProxyType(registry)


def trace_definitions():
    registry = definition_registry()
    return MappingProxyType({row[1]: registry[row[1]] for row in DEFINITION_ROWS})


def frozen_quadratic_product_trace_target():
    """Elaborate only: no proof generation, archive read or kernel invocation."""
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And, Bot
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE, registry=definition_registry())
    binders, premises, conclusion = strip_target(target)
    # strip_target also opens the final negation: its fourth entry is the
    # represented-zero assumption discharged by the negative conclusion.
    if (json_hash(encode_formula(target)) != TARGET_SHA256 or binders != 21
            or len(premises) != 4 or type(premises[-1]) is not And or type(conclusion) is not Bot):
        raise QuadraticProductTraceError("QF001 original target/binder/premise changed")
    return target


def source_contract():
    return dict(code="QF001", schema=SCHEMA, source=NAMED_SOURCE,
        statement_ast_sha256=TARGET_SHA256, parameters=list(PARAMETERS), premise_count=3,
        conditional_on_actual_trace=True, starts_at_one=True, actual_beta_transitions=True,
        nonzero_factors_separate_premise=True, arbitrary_signed_representatives=True,
        new_definition_ids=[f"ND{row[0]:04d}" for row in DEFINITION_ROWS],
        trace_existence_proved=False, rational_denominator_claim=False, real_interpretation=False,
        closes_IR046=False, closes_IR072=False, IR_parents_closed=0, library_admissions=0,
        authority="source_contract_not_proof_authority", original_HA_checked=False)


def quadratic_product_trace_source_pins():
    expected = dict(PINNED_SOURCES)
    if QN_ARCHIVE is not None:
        expected[QN_ARCHIVE["path"]] = QN_ARCHIVE["sha256"]
    result = {}
    for name in sorted((*expected, "scripts/sqrt2_power_quadratic_product_trace.py")):
        raw = (ROOT / name).read_bytes()
        digest = sha256(raw).hexdigest()
        if len(raw) > 16 * 1024**2 or name in expected and digest != expected[name]:
            raise QuadraticProductTraceError("QF001 source/input changed: " + name)
        result[name] = dict(bytes=len(raw), sha256=digest)
    return result


def inert_beta_rows(artifact_path=V28_ARTIFACT):
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(V28_ARTIFACT_SIZE + 1)
    if len(raw) != V28_ARTIFACT_SIZE or sha256(raw).hexdigest() != V28_ARTIFACT_SHA256:
        raise QuadraticProductTraceError("actual v28 archive changed")
    value = json.loads(raw)
    del raw
    if value[0] != "peano-lab-bundle-v1" or value[1] != 861 or len(value[3]) != 862:
        raise QuadraticProductTraceError("actual v28 envelope changed")
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
        raise QuadraticProductTraceError("actual beta/order ancestor cone changed")
    for old, pin in ENDPOINTS.items():
        row = value[3][old]
        if (json_hash(row) != pin["row_sha256"] or json_hash(row[1]) != pin["target_sha256"]
                or tuple(row[2]) != pin["dependencies"]):
            raise QuadraticProductTraceError("actual beta/order endpoint changed")
    return ids, rows


def read_qn_rows(archive_path=None):
    """Return actual canonical QN001 rows, bounded and independently pinned."""
    pin = QN_ARCHIVE
    if type(pin) is not dict:
        raise QuadraticProductTraceError("QN001 first-success canonical-body archive pins are not set")
    path = ROOT / pin["path"] if archive_path is None else Path(archive_path)
    with path.open("rb") as stream:
        packed = stream.read(pin["bytes"] + 1)
    if len(packed) != pin["bytes"] or sha256(packed).hexdigest() != pin["sha256"]:
        raise QuadraticProductTraceError("archived QN001 compressed bytes changed")
    with gzip.GzipFile(fileobj=BytesIO(packed), mode="rb") as stream:
        raw = stream.read(pin["raw_bytes"] + 1)
    del packed
    if len(raw) != pin["raw_bytes"] or sha256(raw).hexdigest() != pin["raw_sha256"]:
        raise QuadraticProductTraceError("archived QN001 envelope changed")
    process = json.loads(raw)
    del raw
    output = json.loads(process["stdout"])
    del process
    if output.get("case") != "QN001" or output.get("schema") != "sqrt2-power-shared-proof-wave-v1":
        raise QuadraticProductTraceError("archived QN001 canonical-body owner changed")
    payload = output["bundle"]
    del output
    if (type(payload) is not str or len(payload.encode()) != pin["bundle_bytes"]
            or sha256(payload.encode()).hexdigest() != pin["bundle_sha256"]):
        raise QuadraticProductTraceError("archived QN001 actual bundle bytes changed")
    value = json.loads(payload)
    del payload
    if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
            or value[1] != pin["root"] or len(value[3]) != pin["nodes"]
            or json_hash(value[2]) != QN_TARGET_SHA256 or value[3][pin["root"]][1] != value[2]):
        raise QuadraticProductTraceError("archived QN001 full-body envelope changed")
    return value[1], value[2], value[3]


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


def _inert_metrics(proof, limits):
    pending, count, deepest = [(proof, 1)], 0, 0
    while pending:
        value, depth = pending.pop()
        if type(value) is not list or not value or value[0] not in _PROOF_CHILDREN:
            raise QuadraticProductTraceError("unknown ordinary proof constructor")
        count, deepest = count + 1, max(deepest, depth)
        if count > limits.max_total_body_nodes or depth > limits.max_depth:
            raise QuadraticProductTraceError("ordinary body exceeds unchanged limits")
        pending.extend((value[i], depth + 1) for i in _PROOF_CHILDREN[value[0]])
    return count, deepest


def merge_actual_rows(*, limits=None, artifact_path=V28_ARTIFACT, archive_path=None):
    """Losslessly remap complete archived rows; no acceptance is asserted."""
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from sqrt2_power_native import closed_formula
    from peano_lab.library.proof_bundle import encode_formula
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise QuadraticProductTraceError("expected unchanged BinaryDAGLimits")
    # Discard the 19MB archive envelope before retaining the larger QN001
    # tree; only the tiny selected beta/order cone survives this boundary.
    ids, ancestors = inert_beta_rows(artifact_path)
    gc.collect()
    qn_root, qn_target, rows = read_qn_rows(archive_path)
    if qn_target != encode_formula(closed_formula(QN_SOURCE)):
        raise QuadraticProductTraceError("QN001 exact caller target differs from archived target")
    row_ids = {canonical(row): i for i, row in enumerate(rows)}
    remap = {}
    for old, original in zip(ids, ancestors):
        row = [original[0], original[1], [remap[d] for d in original[2]], original[3]]
        key = canonical(row)
        found = row_ids.get(key)
        if found is None:
            found = len(rows)
            rows.append(row)
            row_ids[key] = found
        remap[old] = found
    del row_ids, ancestors
    total = deepest = 0
    for i, row in enumerate(rows):
        if (type(row) is not list or len(row) != 4 or type(row[2]) is not list
                or len(set(row[2])) != len(row[2])
                or any(type(d) is not int or not 0 <= d < i for d in row[2])):
            raise QuadraticProductTraceError("actual proof dependency order changed")
        count, depth = _inert_metrics(row[3], limits)
        total, deepest = total + count, max(deepest, depth)
        if total > limits.max_total_body_nodes or row[0] < 8 * count + 16:
            raise QuadraticProductTraceError("merged ancestor body/fuel bound exceeded")
    if len(rows) + 1 > limits.max_nodes or len(canonical(rows)) > limits.max_payload_bytes:
        raise QuadraticProductTraceError("merged ancestor node/payload bound exceeded")
    return rows, {**{old: remap[old] for old in ENDPOINTS}, "QN001": qn_root}, total, deepest


def _root_body(target):
    """One ordinary Ind; direct proof constructors only, no LocalHave compiler."""
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.formulas import Forall
    from peano_lab.kernel.proofs import (AndElimL, AndElimR, AndIntro, EqSym, EqTrans,
        ExistsElim, ForallIntro, Hyp, ImpElim, ImpIntro, Ind)
    from peano_lab.kernel.terms import Succ, Var, Zero

    def law(old, local_hypotheses):
        return Hyp(local_hypotheses + len(ROOT_DEPENDENCIES) - 1 - ROOT_DEPENDENCIES.index(old))

    def apply(proof, *arguments):
        for argument in arguments:
            proof = ImpElim(proof, argument)
        return proof

    def field(proof, index, count):
        for _ in range(index):
            proof = AndElimR(proof)
        return AndElimL(proof) if index < count - 1 else proof

    def stream_terms(extra_variables):
        return tuple(Var(extra_variables + 15 - i) for i in range(16))

    def unique(local_hypotheses, codes, component, index, first, second, left, right):
        code, scale = codes[2*component:2*component+2]
        return apply(instantiate(law(122, local_hypotheses), code, scale, index, first, second),
                     field(left, component, 4), field(right, component, 4))

    motive = target
    for _ in range(16):
        if type(motive) is not Forall:
            raise QuadraticProductTraceError("QF001 fixed stream binders changed")
        motive = motive.body
    if type(motive) is not Forall:
        raise QuadraticProductTraceError("QF001 induction binder changed")
    motive = motive.body

    # Base scope: four terminal variables; Hyp0=represented zero, Hyp1=At,
    # Hyp2=nonzero factors (unused for the empty prefix), Hyp3=trace.
    codes = stream_terms(4)[8:]
    rp, rn = Var(3), Var(2)
    start, terminal = AndElimL(Hyp(3)), Hyp(1)
    real_one = unique(4, codes, 0, Zero(), rp, Succ(Zero()), terminal, start)
    negative_zero = unique(4, codes, 1, Zero(), rn, Zero(), terminal, start)
    one_zero = EqTrans(EqSym(real_one), EqTrans(AndElimL(Hyp(0)), negative_zero))
    base = ImpElim(instantiate(law(12, 4), Zero()), one_zero)
    for _ in range(4):
        base = ImpIntro(base)
    for _ in range(4):
        base = ForallIntro(base)

    # Successor before existential elimination: Hyp0=zero, Hyp1=At,
    # Hyp2=nonzero factors, Hyp3=trace, Hyp4=IH. L is Var4.
    last_bound = instantiate(law(14, 5), Succ(Var(4)))
    step_exists = apply(instantiate(AndElimR(Hyp(3)), Var(4)), last_bound)

    # Twelve existential witnesses now occupy Var11..0 and Hyp0..11.
    # Original zero/At/nonzero/trace/IH are Hyp12/13/14/15/16.
    A = tuple(Var(i) for i in (11, 10, 9, 8))
    B = tuple(Var(i) for i in (7, 6, 5, 4))
    C = tuple(Var(i) for i in (3, 2, 1, 0))
    L = Var(16)
    caller = tuple(Var(i) for i in (15, 14, 13, 12))
    fields = tuple(field(Hyp(0), i, 5) for i in range(5))
    factor_at, previous_at, successor_at, real_balance, radical_balance = fields

    # Restriction of the actual trace to L. Inside forall i and its bound
    # premise the old trace is Hyp16 and the old L is Var17.
    lifted_bound = apply(instantiate(law(40, 18), Succ(Var(0)), Var(17)), Hyp(0))
    prefix_steps = ForallIntro(ImpIntro(apply(
        instantiate(AndElimR(Hyp(16)), Var(0)), lifted_bound)))
    prefix_trace = AndIntro(AndElimL(Hyp(15)), prefix_steps)

    # Restriction of factor nonzeroness introduces five variables and two
    # premises. Old nonzero factors become Hyp16; old L becomes Var21.
    factor_bound = apply(instantiate(law(40, 19), Succ(Var(4)), Var(21)), Hyp(1))
    prefix_nonzero = apply(instantiate(Hyp(16), Var(4), Var(3), Var(2), Var(1), Var(0)),
                           factor_bound, Hyp(0))
    for _ in range(2):
        prefix_nonzero = ImpIntro(prefix_nonzero)
    for _ in range(5):
        prefix_nonzero = ForallIntro(prefix_nonzero)
    previous_nonzero = apply(instantiate(Hyp(16), *A), prefix_trace, prefix_nonzero, previous_at)
    factor_nonzero = apply(instantiate(Hyp(14), L, *B),
                           instantiate(law(14, 17), Succ(L)), factor_at)
    successor_nonzero = apply(instantiate(law("QN001", 17), *A, *B, *C),
                              real_balance, radical_balance, previous_nonzero, factor_nonzero)

    codes = stream_terms(17)[8:]
    equalities = tuple(unique(17, codes, i, Succ(L), C[i], caller[i], successor_at, Hyp(13))
                       for i in range(4))
    real_zero = EqTrans(equalities[0], EqTrans(AndElimL(Hyp(12)), EqSym(equalities[1])))
    radical_zero = EqTrans(equalities[2], EqTrans(AndElimR(Hyp(12)), EqSym(equalities[3])))
    step = ImpElim(successor_nonzero, AndIntro(real_zero, radical_zero))
    for index in reversed(range(12)):
        step = ExistsElim(step_exists if index == 0 else Hyp(0), step)
    for _ in range(4):
        step = ImpIntro(step)
    for _ in range(4):
        step = ForallIntro(step)
    step = ForallIntro(ImpIntro(step))
    body = Ind(motive, base, step)
    for _ in range(16):
        body = ForallIntro(body)
    for _ in ROOT_DEPENDENCIES:
        body = ImpIntro(body)
    return body


@dataclass(frozen=True)
class QuadraticProductTraceCertificate:
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


def prove_quadratic_product_trace(*, limits=None, artifact_path=V28_ARTIFACT, archive_path=None):
    """Root-owned worker: ordinary induction plus full canonical ancestor replay."""
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from peano_lab.library.proof_bundle import (decode_proof_bundle, encode_formula,
        encode_proof, check_proof_bundle)
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise QuadraticProductTraceError("expected unchanged BinaryDAGLimits")
    before = quadratic_product_trace_source_pins()
    target = frozen_quadratic_product_trace_target()
    rows, endpoints, total, deepest = merge_actual_rows(
        limits=limits, artifact_path=artifact_path, archive_path=archive_path)
    ancestor_count, ancestor_total = len(rows), total
    ancestor_sha256 = json_hash(rows)
    proof = _root_body(target)
    count, depth = _body_metrics(proof, limits)
    total, deepest = total + count, max(deepest, depth)
    if total > limits.max_total_body_nodes:
        raise QuadraticProductTraceError("QF001 aggregate ordinary proof budget exceeded")
    _row_preflight(target, proof, limits)
    dependencies = tuple(endpoints[name] for name in ROOT_DEPENDENCIES)
    root = len(rows)
    rows.append([8 * count + 16, encode_formula(target), list(dependencies), encode_proof(proof)])
    payload = canonical(["peano-lab-bundle-v1", root, encode_formula(target), rows]).decode() + "\n"
    if len(payload.encode()) > limits.max_payload_bytes:
        raise QuadraticProductTraceError("QF001 complete canonical payload exceeds bound")
    del rows, proof
    gc.collect()
    bundle, decoded_target = decode_proof_bundle(payload, limits=limits.bundle_limits())
    if decoded_target != target:
        raise QuadraticProductTraceError("QF001 decoded target differs from exact caller target")
    receipt = check_proof_bundle(bundle, target, limits=limits.bundle_limits())
    if receipt.target != target or quadratic_product_trace_source_pins() != before:
        raise QuadraticProductTraceError("QF001 target/source changed during ordinary replay")
    provenance = dict(code="QF001", schema=SCHEMA,
        coverage="conditional_finite_integer_quadratic_product_trace_nonvanishing",
        original_target_source=NAMED_SOURCE, original_target_ast_sha256=TARGET_SHA256,
        source_pins=before, original_HA_checked=True, canonical_bytes_replayed=True,
        empty_context=True, actual_ancestor_nodes=ancestor_count, actual_ancestor_body_nodes=ancestor_total,
        merged_ancestor_rows_sha256=ancestor_sha256, root_dependencies=list(dependencies),
        QN001_archive=dict(QN_ARCHIVE), QN001_actual_root=endpoints["QN001"],
        v28_archive=dict(path=str(V28_ARTIFACT.relative_to(ROOT)), bytes=V28_ARTIFACT_SIZE,
                         sha256=V28_ARTIFACT_SHA256),
        beta_order_original_ids=list(ANCESTOR_IDS), beta_order_rows_sha256=ANCESTOR_ROWS_SHA256,
        new_definition_ids=[f"ND{row[0]:04d}" for row in DEFINITION_ROWS],
        root_induction_count=1, conditional_on_actual_trace=True, actual_beta_transitions=True,
        nonzero_factors_separate_premise=True, arbitrary_signed_representatives=True,
        trace_existence_proved=False, rational_denominator_claim=False, real_interpretation=False,
        local_have_compiler_calls=0, ring_normalizer_calls=0, solver_calls=0,
        new_axioms=[], external_certificate_references=[], closes_IR046=False, closes_IR072=False,
        IR_parents_closed=0, library_admissions=0, independent_lean_checked=False)
    return QuadraticProductTraceCertificate(target, bundle, payload, receipt, deepest, provenance)
