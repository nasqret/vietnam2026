"""CV001: universal vanishing of an actually executed natural diagonal sum.

The old 27-node ancestor cone supplies complete ordinary HA bodies, not trusted
names or receipts. A new dependency-curried body proves zero from decoded
zero-prefix hypotheses. All 28 bodies must pass the original checker from the
resulting canonical bytes. Execute the producer only in the root-owned bounded
worker. This is neither rational convolution nor a formal-exp/power-table graph.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, fields, replace
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType

from sqrt2_power_automation_baseline import source_pins as base_source_pins
from sqrt2_power_binary_dag import BinaryDAGLimits, ROOT, _body_metrics, _row_preflight, formula_sha256
from sqrt2_power_definitions import PARENT, PARENT_SHA256, parse_named
from sqrt2_power_native import closed_formula
from peano_lab.kernel.formulas import Imp, pretty_formula
from peano_lab.library.proof_bundle import (
    BundleNode, ProofBundle, check_encoded_proof_bundle, decode_formula,
    decode_proof, encode_formula, encode_proof_bundle,
)

SCHEMA = "sqrt2-power-natural-convolution-vanishing-v1"
EXPECTED_LOCAL_LEMMAS = 11
SOURCE = (
    "forall ab ac L bb bc M r s i db dc n. "
    "(forall j a. Lt(j,r) -> BetaZeroExtend(ab,ac,L,j,a) -> a=0) -> "
    "(forall j b. Lt(j,s) -> BetaZeroExtend(bb,bc,M,j,b) -> b=0) -> "
    "Lt(i,r+s) -> PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,i,db,dc,S i) -> "
    "Sum(db,dc,S i,n) -> n=0"
)
CONVOLUTION_VANISHING_NAMED_SOURCE = SOURCE
SOURCE_SHA256 = "f12125e871a18ca2c7ba8ee680ec20a6799f36957943934c1990a76323eb0a12"
TARGET_SHA256 = "b5ca16c60cf9aff317a93603448843e717d17228380fb7c1a1287e31f12e5e22"
ARTIFACT = ROOT / "research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json"
ARTIFACT_BYTES = 745307
ARTIFACT_SHA256 = "55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3"
ANCESTOR_IDS = (0, 1, 2, 3, 4, 5, 6, 7, 13, 14, 16, 19, 22, 23, 30, 31,
                34, 38, 40, 41, 45, 46, 88, 120, 125, 126, 138)
ANCESTOR_IDS_SHA256 = "d0a6463d42990dc3a52a99729ba5fcbc2f04a76b76a1d269d4740cf69b484168"
ANCESTOR_ROWS_SHA256 = "2d84474e8b343436afe96ea7097991add96e01545f40c56e3c5352924d601e74"
ROOT_PINS = (
    ("le_or_lt", 38, "c970f38706674d90ce9ab8784ef502498abfc8727d9d868de82d2464f7f52103"),
    ("add_le_add_right", 30, "b5349e668e14ea5e40b1ce88708870f940dc6ad87e2217660091f3ce382e866f"),
    ("add_le_add_left", 31, "a97f86a6fe76833a577e3f2e37fd0b3cf4d0274beb2769a1a4a8a84a1c3695ec"),
    ("le_trans", 14, "0f055befded849dd804be4ad2aa4cdc48b1b82a9e85e6dd9583a32e924a43b54"),
    ("lt_not_le", 40, "1f29dec659b4a84eace0f02d2fdc09f91c3e8c917f102a86ed282da14875e84d"),
    ("mul_zero_left", 4, "bc9747ec6d522ffe76b7ff4ca024b8cd2e30ce82d474cd6901dc8045da4cdf49"),
    ("beta_repeat_sum_exact", 138, "2f69ce955259876279ae574780003c324221074e353e311afb1e26f826b74490"),
)
DEFINITION_PINS = (
    ("Le", "PD0001", ("a", "b"), "5aad83c25902bc26b2fdbd296fabd3db359880ec4c568fe7e108ce1dc11dea46"),
    ("Lt", "PD0002", ("a", "b"), "d7bdf8ed287c3672fa78951c9cabe8f8814d7fcf1fb1ffcfee2d0d3b41251531"),
    ("BetaAt", "PD0013", ("b", "c", "i", "x"), "b2a23ea9cf6373c9ee8a9c2a74cbcffde69a806b04ed3f831e7a9b00d445bdeb"),
    ("Sum", "PD0015", ("b", "c", "l", "z"), "dbcb098228addae8980ad5cc3f82757926671b6ad1ecb6116542e0e91747d571"),
    ("Repeat", "PD0019", ("b", "c", "a", "l"), "cc4b13cedf42cae46d24a19cd9d8f38d7fb0fef6139087fdb4c4c262e4955096"),
    ("BetaZeroExtend", "ND0291", ("b", "c", "L", "i", "a"), "4303982643c76ddd3bf2aafcd76da78471cb9ff98e2495042199746bf8d173f4"),
    ("PolynomialDiagonalTerm", "ND0292", ("ab", "ac", "L", "bb", "bc", "M", "i", "j", "t"), "8dbcc41c1cc1fe3fce6dd2302aaea3c0b4843ec4f4d6a3041be315af7a62cef5"),
    ("PolynomialDiagonalPrefix", "ND0293", ("ab", "ac", "L", "bb", "bc", "M", "i", "db", "dc", "l"), "7a1d1d1e47bfedb58e92da7ae0f8ee6b0ecd65e2bbb703563f389bc94c827ea0"),
)
FROZEN_SOURCE_PINS = {
    "scripts/sqrt2_power_definitions.py": "365f142974c3958aa5cad2430ed93fc3866e8abbadea0c357cb906574ff0220b",
    "scripts/sqrt2_power_binary_dag.py": "517535807fe06a317fae48c5fc5f47db944b0c32904fb8d02a0a1b102af12227",
    "scripts/sqrt2_power_native.py": "9b51adc2699bf3c83c74749b9fc4723a8a1b8e234cef6f521a3f309fe646cc73",
    "peano-lab/py/peano_lab/library/theorems.py": "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "peano-lab/py/peano_lab/library/prime_field_polynomial_convolution_candidate.py": "20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24",
    "peano-lab/py/peano_lab/library/prime_field_polynomial_candidate.py": "644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72",
    "peano-lab/py/peano_lab/library/prime_field_arithmetic_candidate.py": "d4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90",
    "peano-lab/py/peano_lab/library/prime_field_tables_candidate.py": "2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400",
    "peano-lab/py/peano_lab/library/finite_repeat_sum_candidate.py": "7e468d7ddced0220b4c6da6c7417edfa1f1392e793770b0109808ad32d84d182",
    "peano-lab/py/peano_lab/library/finite_sum_theorems.py": "0d60b7a4fa21161def737fc6759b23e0679694052e95d97b419aa1ecb293c56e",
    "peano-lab/py/peano_lab/library/finite_fold_surface.py": "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30",
    "peano-lab/py/peano_lab/library/defined_syntax.py": "86b3ee6dc17043553e730372ac0d9af884a3fb85ebe6a30813318871145fe903",
}


class ConvolutionVanishingError(ValueError):
    """Changed target, ancestry, definitions, ordinary proof, or fixed limit."""


def _canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()


def _read(path, maximum, *, size=None, digest=None):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ConvolutionVanishingError("expected a regular nonsymlink pinned input")
    before = path.stat()
    if not 0 < before.st_size <= maximum or (size is not None and before.st_size != size):
        raise ConvolutionVanishingError("pinned input size changed or exceeded its cap")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    after = path.stat()
    fingerprint = lambda item: (item.st_dev, item.st_ino, item.st_size,
                                item.st_mtime_ns, item.st_ctime_ns)
    if (len(raw) != before.st_size or fingerprint(before) != fingerprint(after)
            or (digest is not None and sha256(raw).hexdigest() != digest)):
        raise ConvolutionVanishingError("pinned input bytes changed")
    return raw


def convolution_source_pins():
    pins = base_source_pins()
    for name, digest in FROZEN_SOURCE_PINS.items():
        raw = _read(ROOT / name, 2 * 1024**2, digest=digest)
        pins[name] = {"bytes": len(raw), "sha256": digest}
    for path in (Path(__file__).resolve(), ROOT / "peano-lab/py/peano_lab/library/__init__.py",
                 ROOT / "peano-lab/py/peano_lab/library/proof_bundle.py"):
        raw = _read(path, 2 * 1024**2)
        pins[str(path.relative_to(ROOT))] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    raw = _read(PARENT, 2 * 1024**2, size=1501384, digest=PARENT_SHA256)
    pins[str(PARENT.relative_to(ROOT))] = {"bytes": len(raw), "sha256": PARENT_SHA256}
    raw = _read(ARTIFACT, ARTIFACT_BYTES, size=ARTIFACT_BYTES, digest=ARTIFACT_SHA256)
    pins[str(ARTIFACT.relative_to(ROOT))] = {"bytes": len(raw), "sha256": ARTIFACT_SHA256}
    return pins


def convolution_definitions():
    """Exact historical templates only; no additions or global mutations."""
    from peano_lab.library.defined_syntax import DEFINITIONS_BY_NAME, _definition
    from peano_lab.library import prime_field_polynomial_convolution_candidate as diagonal
    historical = {row["name"]: row for row in json.loads(
        _read(PARENT, 2 * 1024**2, size=1501384, digest=PARENT_SHA256))["reviewed_definitions"]}
    result = {name: DEFINITIONS_BY_NAME[name] for name, *_ in DEFINITION_PINS[:5]}
    builders = (diagonal.prime_field_polynomial_zero_extended_entry_relation,
                diagonal.prime_field_polynomial_diagonal_term_relation,
                diagonal.prime_field_polynomial_diagonal_prefix_relation)
    for (name, identifier, parameters, _), builder in zip(DEFINITION_PINS[5:], builders, strict=True):
        text = builder(*parameters, tag="lowercontinuation", variables=parameters)
        result[name] = _definition(stable_id=identifier, name=name, parameters=parameters,
            template_source=text, summary="Exact inherited natural diagonal template",
            category="irrationality_support", conceptual_dependencies=tuple(historical[name]["dependencies"]))
    for name, identifier, parameters, digest in DEFINITION_PINS:
        definition, old = result[name], historical[name]
        if (definition.stable_id != identifier or definition.parameters != parameters
                or old["id"] != identifier or old["parameters"] != list(parameters)
                or old["arity"] != len(parameters)
                or old["expansion_sha256"] != sha256(definition.template_source.encode()).hexdigest()
                or formula_sha256(definition.template_formula) != digest):
            raise ConvolutionVanishingError("exact historical definition/argument mapping changed: " + name)
    return MappingProxyType(result)


def frozen_convolution_vanishing_target():
    if sha256(SOURCE.encode()).hexdigest() != SOURCE_SHA256:
        raise ConvolutionVanishingError("CV001 original named source changed")
    target = parse_named(SOURCE, registry=convolution_definitions())
    if formula_sha256(target) != TARGET_SHA256:
        raise ConvolutionVanishingError("CV001 original expanded target changed")
    return target


def _root_specs():
    """Literal arithmetic extraction and one source-only finite-sum factory."""
    from peano_lab.library.finite_repeat_sum_candidate import make_finite_repeat_sum_candidate_theorems
    name = "peano-lab/py/peano_lab/library/theorems.py"
    module = ast.parse(_read(ROOT / name, 1024**2, digest=FROZEN_SOURCE_PINS[name]))
    declarations = [n for n in module.body if isinstance(n, ast.AnnAssign)
                    and isinstance(n.target, ast.Name) and n.target.id == "THEOREMS"]
    if len(declarations) != 1 or not isinstance(declarations[0].value, ast.Tuple):
        raise ConvolutionVanishingError("literal arithmetic table shape changed")
    wanted = {row[0] for row in ROOT_PINS[:-1]}
    result = {}
    for item in declarations[0].value.elts:
        if (not isinstance(item, ast.Call) or not isinstance(item.func, ast.Name)
                or item.func.id != "TheoremSpec" or item.keywords or len(item.args) != 5):
            raise ConvolutionVanishingError("nonliteral arithmetic entry")
        key = ast.literal_eval(item.args[0])
        if key in wanted:
            if key in result:
                raise ConvolutionVanishingError("duplicate selected arithmetic source")
            result[key] = tuple(ast.literal_eval(argument) for argument in item.args)
    sums = [row for row in make_finite_repeat_sum_candidate_theorems(lambda *args: args)
            if row[0] == "beta_repeat_sum_exact"]
    if len(sums) != 1 or set(result) != wanted:
        raise ConvolutionVanishingError("missing exact selected source")
    result[sums[0][0]] = sums[0]
    for key, _, digest in ROOT_PINS:
        if sha256(repr(result[key]).encode()).hexdigest() != digest:
            raise ConvolutionVanishingError("selected literal/script/dependency source changed: " + key)
    return result


def convolution_cone_data(artifact_path=ARTIFACT):
    """Read-only source/JSON inspection; never checks or creates a proof."""
    raw = _read(artifact_path, ARTIFACT_BYTES, size=ARTIFACT_BYTES, digest=ARTIFACT_SHA256)
    value = json.loads(raw)
    if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
            or value[1] != 209 or type(value[3]) is not list or len(value[3]) != 210):
        raise ConvolutionVanishingError("original bundle envelope changed")
    rows, specs = value[3], _root_specs()
    for name, position, _ in ROOT_PINS:
        if rows[position][1] != encode_formula(closed_formula(specs[name][1])):
            raise ConvolutionVanishingError("actual ancestor differs from exact source target: " + name)
    included, pending = set(), [position for _, position, _ in ROOT_PINS]
    while pending:
        position = pending.pop()
        if type(position) is not int or not 0 <= position < 210:
            raise ConvolutionVanishingError("invalid ancestor position")
        if position not in included:
            row = rows[position]
            if (type(row) is not list or len(row) != 4 or type(row[2]) is not list
                    or len(row[2]) != len(set(row[2]))
                    or any(type(d) is not int or not 0 <= d < position for d in row[2])):
                raise ConvolutionVanishingError("noncanonical ancestor dependency list")
            included.add(position)
            pending.extend(row[2])
    ids = tuple(sorted(included))
    selected = [rows[i] for i in ids]
    if (ids != ANCESTOR_IDS or sha256(_canonical(ids)).hexdigest() != ANCESTOR_IDS_SHA256
            or sha256(_canonical(selected)).hexdigest() != ANCESTOR_ROWS_SHA256
            or sum(len(row[2]) for row in selected) != 40):
        raise ConvolutionVanishingError("minimal actual ancestor cone changed")
    return dict(original_ids=ids, rows=selected, root_sources=specs,
                original_body_nodes=1146, original_max_body_depth=52,
                original_rows_bytes=40072, original_dependency_edges=40,
                authority="authenticated_ordinary_bytes_not_kernel_acceptance")


def convolution_vanishing_manifest():
    definitions = convolution_definitions()
    target, data = frozen_convolution_vanishing_target(), convolution_cone_data()
    return dict(schema=SCHEMA, id="CV001", name="natural_diagonal_sum_vanishes_below_orders",
        source=SOURCE, source_sha256=SOURCE_SHA256, expanded_source=pretty_formula(target, []),
        statement_ast=encode_formula(target), statement_ast_sha256=TARGET_SHA256,
        source_pins=convolution_source_pins(), parent="IR079",
        definition_nodes=[dict(id=d.stable_id, name=d.name, parameters=list(d.parameters),
            arity=d.arity, source=d.template_source, ast=encode_formula(d.template_formula),
            ast_sha256=formula_sha256(d.template_formula)) for d in definitions.values()],
        original_ancestor_ids=list(data["original_ids"]), ancestor_nodes=27,
        ancestor_body_nodes=data["original_body_nodes"], ancestor_max_body_depth=52,
        ancestor_rows_bytes=40072, ancestor_dependency_edges=40,
        ancestor_rows_sha256=ANCESTOR_ROWS_SHA256, source_roots=[dict(name=n, original_node=i,
            literal_spec_sha256=h, source=data["root_sources"][n][1]) for n, i, h in ROOT_PINS],
        coefficient_order="Original raw highest-degree-first prefix indices; j+h=i. No X-power-index reinterpretation.",
        coverage="universal_natural_convolution_vanishing_support",
        authority="frozen_source_and_ordinary_bytes_not_a_checked_certificate",
        ordinary_HA_checked=False, independent_lean_checked=False, library_admissions=0,
        IR_parents_closed=0, closes_IR079=False, closes_IR080=False,
        rational_convolution_claim=False, power_table_graph_claim=False,
        worker_rss_ceiling_bytes=768 * 1024**2,
        limits=dict(vars(BinaryDAGLimits())), native_budget_fit=None)


def _script(definitions):
    """Straight constructive order split, zero summand table, exact finite sum."""
    context = ("ab", "ac", "L", "bb", "bc", "M", "r", "s", "i", "db", "dc", "n")
    def have(name, source, extra=()):
        names = context + tuple(extra)
        return "have " + name + " : " + pretty_formula(parse_named(source, names, definitions), list(names))
    def call(name, *arguments):
        return tuple("specialize " + name + " " + arg for arg in arguments) + ("apply " + name,)
    commands = tuple("intro " + name for name in context)
    commands += tuple("intro " + name for name in ("hleft", "hright", "hbound", "hdiag", "hsum"))
    commands += (have("hz", "Repeat(db,dc,0,S i)"), "intro j", "intro hj",
        have("ht", "exists t. BetaAt(db,dc,j,t) /\\ PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t)", ("j",)))
    commands += call("hdiag", "j") + ("exact hj", "cases ht", "cases ht_witness", "have heq : x=0")
    term = "ht_witness_right_witness_witness_witness"
    commands += ("cases ht_witness_right", "cases ht_witness_right_witness",
                 "cases ht_witness_right_witness_witness")
    commands += tuple("cases " + term + "_right" * k for k in range(3))
    extra = ("j", "x", "x1", "x2", "x3")
    commands += (have("ho", "Le(r,j) \\/ Lt(j,r)", extra),)
    commands += call("le_or_lt", "r", "j") + ("cases ho",)
    commands += (have("hp", "Le(s,x1) \\/ Lt(x1,s)", extra),)
    commands += call("le_or_lt", "s", "x1") + ("cases hp",)
    commands += (have("ha", "Le(r+s,j+s)", extra),)
    commands += call("add_le_add_right", "r", "j", "s") + ("exact ho_left",)
    commands += (have("hb", "Le(j+s,j+x1)", extra),)
    commands += call("add_le_add_left", "s", "x1", "j") + ("exact hp_left",)
    commands += (have("hab", "Le(r+s,j+x1)", extra),)
    commands += call("le_trans", "r+s", "j+s", "j+x1") + ("exact ha", "exact hb",
        "rewrite " + term + "_left at hab", "exfalso")
    commands += call("lt_not_le", "i", "r+s") + ("exact hbound", "exact hab")
    # Right-low branch: the actual right decoded value x3 is zero.
    commands += ("have hbzero : x3=0",) + call("hright", "x1", "x3")
    commands += ("exact hp_right", "exact " + term + "_right_right_left",
                 "trans x2*x3", "exact " + term + "_right_right_right", "rewrite hbzero", "simp")
    # Left-low branch: the actual left decoded value x2 is zero.
    commands += ("have hazero : x2=0",) + call("hleft", "j", "x2")
    commands += ("exact ho_right", "exact " + term + "_right_left",
                 "trans x2*x3", "exact " + term + "_right_right_right", "rewrite hazero")
    commands += call("mul_zero_left", "x3")
    # Finish the witnessed Repeat prefix, then its exact Sum endpoint.
    # rewrite is deliberately one-occurrence-only. BetaAt contains its value
    # twice: once in the strict residue bound, once in the remainder equation.
    commands += ("rewrite heq at ht_witness_left", "rewrite heq at ht_witness_left",
                 "exact ht_witness_left", "have hn : n=(S i)*0")
    commands += call("beta_repeat_sum_exact", "db", "dc", "0", "S i", "n")
    commands += ("exact hz", "exact hsum", "trans (S i)*0", "exact hn", "simp")
    return commands


def _preserve_local_lemma_synthesis(proof, *, limits=BinaryDAGLimits()):
    """Annotate actual local lemmas with ordinary identity Cuts, not new facts.

LocalHave(P,L,B) becomes LocalHave(P,Cut(P,P,L,Hyp(0)),B), recursively.
The existing compiler preserves that typed Cut while substituting the local
lemma. Its unchanged kernel rule checks L against P and Hyp(0) against P in
the extended context. No annotation can make an incorrect L into a premise.
"""
    from peano_lab.engine.proof_reduction import LocalHave, LocalSuffices
    from peano_lab.kernel.proofs import Cut, Hyp, Proof
    if type(limits) is not BinaryDAGLimits or not isinstance(proof, Proof):
        raise ConvolutionVanishingError("local annotation requires an actual proof and unchanged limits")
    _body_metrics(proof, limits)
    memo, annotated = {}, 0

    def visit(value):
        nonlocal annotated
        identity = id(value)
        if identity in memo:
            return memo[identity]
        if type(value) is LocalSuffices:
            raise ConvolutionVanishingError("unexpected local scheduler in the exact CV001 script")
        changes = {field.name: visit(child) for field in fields(value)
                   if isinstance((child := getattr(value, field.name)), Proof)}
        result = replace(value, **changes) if changes else value
        if type(result) is LocalHave:
            annotated += 1
            result = replace(result, proof=Cut(result.proposition, result.proposition,
                                              result.proof, Hyp(0)))
        memo[identity] = result
        return result

    result = visit(proof)
    _body_metrics(result, limits)
    return result, annotated


@dataclass(frozen=True)
class ConvolutionVanishingCertificate:
    target: object
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


def prove_convolution_vanishing(*, limits=BinaryDAGLimits(), artifact_path=ARTIFACT):
    """Root-owned worker only. No historical receipt or outside premise accepted."""
    if type(limits) is not BinaryDAGLimits:
        raise ConvolutionVanishingError("expected unchanged pilot limits")
    if limits.max_nodes < 28 or limits.max_total_body_nodes <= 1146 or limits.max_depth < 52:
        raise ConvolutionVanishingError("ancestor cone already exceeds the requested smaller limits")
    before = convolution_source_pins()
    target, definitions = frozen_convolution_vanishing_target(), convolution_definitions()
    data = convolution_cone_data(artifact_path)
    remap = {old: new for new, old in enumerate(data["original_ids"])}
    nodes = tuple(BundleNode(remap[old], decode_formula(row[1], _depth=limits.max_depth),
        tuple(remap[d] for d in row[2]), decode_proof(row[3], _depth=limits.max_depth), row[0])
        for old, row in zip(data["original_ids"], data["rows"], strict=True))
    dependencies = tuple(remap[position] for _, position, _ in ROOT_PINS)
    curried = target
    for dependency in reversed(dependencies):
        curried = Imp(nodes[dependency].target, curried)
    from peano_lab.engine.state import final_certificate, start
    from peano_lab.engine.tactics import apply_tactic, enforce_live_proof_bounds
    from peano_lab.engine.proof_reduction import compile_local_cuts
    from peano_lab.kernel.checker import check
    state = start(curried)
    commands = tuple("intro " + name for name, _, _ in ROOT_PINS) + _script(definitions)
    for index, command in enumerate(commands):
        tactic, _, arguments = command.partition(" ")
        try:
            state = apply_tactic(state, tactic, arguments)
        except Exception:
            # Never format a potentially huge rejected proof state/exception.
            raise ConvolutionVanishingError("CV001 command " + str(index) + " failed: " + command) from None
    if state.goals or state.target != curried:
        raise ConvolutionVanishingError("CV001 tactic state changed its original target or remains open")
    raw_body = final_certificate(state)
    if raw_body is None:
        raise ConvolutionVanishingError("CV001 final certificate still contains a hole or metavariable")
    annotated_body, annotation_count = _preserve_local_lemma_synthesis(raw_body, limits=limits)
    if annotation_count != EXPECTED_LOCAL_LEMMAS:
        raise ConvolutionVanishingError("the exact eleven CV001 local lemmas changed")
    _row_preflight(curried, annotated_body, limits)
    body = compile_local_cuts(annotated_body)
    _body_metrics(body, limits)
    _row_preflight(curried, body, limits)
    enforce_live_proof_bounds(body)
    if not check((), body, curried):
        raise ConvolutionVanishingError("original HA rejected the annotated CV001 body at its exact curried target")
    nodes += (BundleNode(len(nodes), target, dependencies, body),)
    total, deepest = 0, 0
    for node in nodes:
        count, depth = _body_metrics(node.body, limits)
        total, deepest = total + count, max(deepest, depth)
        if total > limits.max_total_body_nodes:
            raise ConvolutionVanishingError("CV001 aggregate body cap exceeded")
        _row_preflight(node.target, node.body, limits)
    bundle = ProofBundle(nodes, len(nodes) - 1)
    payload = encode_proof_bundle(bundle, target, limits=limits.bundle_limits())
    receipt = check_encoded_proof_bundle(payload, limits=limits.bundle_limits())
    if receipt.target != target or formula_sha256(receipt.target) != TARGET_SHA256:
        raise ConvolutionVanishingError("fresh HA result differs from the original CV001 target")
    if before != convolution_source_pins():
        raise ConvolutionVanishingError("proof-producing source changed during CV001 generation")
    _read(artifact_path, ARTIFACT_BYTES, size=ARTIFACT_BYTES, digest=ARTIFACT_SHA256)
    provenance = dict(case="CV001", schema=SCHEMA,
        claim="Universal natural antidiagonal vanishing only; no rational or exp/log bridge",
        original_target_source=SOURCE, original_target_ast_sha256=TARGET_SHA256,
        source_pins=before, artifact_sha256=ARTIFACT_SHA256,
        original_ancestor_ids=list(data["original_ids"]), ancestor_rows_sha256=ANCESTOR_ROWS_SHA256,
        original_ancestor_nodes=27, original_ancestor_body_nodes=1146,
        source_roots=[dict(name=name, original_node=position, literal_spec_sha256=digest)
                      for name, position, digest in ROOT_PINS],
        original_definition_ids=[identifier for _, identifier, _, _ in DEFINITION_PINS],
        original_coefficient_order="raw highest-degree-first prefix index; j+h=i",
        local_annotation_strategy="ordinary_identity_cut_before_local_compilation",
        typed_local_lemma_cuts=annotation_count,
        ordinary_HA_checked_from_canonical_bytes=True, requires_fresh_independent_HA_replay=True,
        independent_lean_checked=False, IR_parents_closed=0, library_admissions=0,
        total_body_nodes=receipt.total_body_nodes, max_proof_depth=deepest,
        limits=dict(vars(limits)), worker_rss_ceiling_bytes=768 * 1024**2,
        worker_enforcement="external root-owned single-worker supervisor required")
    return ConvolutionVanishingCertificate(target, bundle, payload, receipt, deepest, provenance)
