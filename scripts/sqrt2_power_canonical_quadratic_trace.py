"""QF004: construct a finite trace with canonical quadratic outputs.

QF002 constructs balanced outputs, a deliberately weaker public statement.
This separate theorem fixes each output component to its explicit natural
polynomial. It supplies the construction needed for later iterated height
bounds; it does not put those bounds into a definition or claim them now.
Every selected ancestor body and the new ordinary induction are HA-replayed.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_quadratic_trace_exists import (
    ROOT, F, U, V, A, B, C, Scope, at, named, forall, exists, preserved,
    introduce, eliminate, witness, conjunction, field, apply, specialize,
    products, _root, ANCESTOR_IDS, canonical, json_hash, _inert_metrics,
    quadratic_trace_exists_source_pins,
)
from sqrt2_power_quadratic_product_exists import ARCHIVES, read_archive
from sqrt2_power_quadratic_height import definition_registry as height_registry

SCHEMA = "sqrt2-power-canonical-quadratic-trace-v1"
TARGET_SHA256 = "9c459742c8eb742cb4958f037c3b7492a8f773e609ef0f8e1d63f541c2e0a9b1"
PREFIX_ROWS_SHA256 = "118c5fed3a8a85059b4e5ea1bb25f3adbc5288ca4d3af64a8469588442d6a263"
PREFIX_ROWS_BYTES = 157671
DEFINITION_ROWS = (
    (396, "IQuadCanonicalStep", F+U+("i",),
     exists(A+B+C, at(F,"i",B)+" /\\ ("+at(U,"i",A)+" /\\ ("+at(U,"S i",C)+" /\\ "+
         named("IQuadCanonicalProduct",*A,*B,*C)+"))"),
     ("IQuadAt", "IQuadCanonicalProduct"),
     "An actual decoded factor/current/successor transition with all four canonical output equations.",
     "2b0e5e56cde51e1bc3cad262ef5a101d470fdbd37d10d8a28848246c30e34b70"),
    (397, "IQuadCanonicalTrace", F+U+("L",),
     at(U,"0",("1","0","0","0"))+" /\\ ("+forall(("i",),
         "Lt(i,L) -> "+named("IQuadCanonicalStep",*F,*U,"i"))+")",
     ("IQuadAt", "Lt", "IQuadCanonicalStep"),
     "An actual finite trace starts at one and uses canonical component multiplication at every step; no bound is a clause.",
     "9afc4068d8bb92eb34aae2c8745bc45d80651f4994d95f9c4e7347edc272fa1b"),
)


def trace(factors, codes, length):
    return named("IQuadCanonicalTrace",*factors,*codes,length)


NAMED_SOURCE = forall(F+("L",), exists(U,trace(F,U,"L")))
HELPERS = (
    ("transport", forall(F+U+V+("L",),
        "("+preserved(U,V,"S L")+") -> "+trace(F,U,"L")+" -> "+trace(F,V,"L")),
        (29,38,40), "0bd2896cb1e840fa6950d37bbcd15473beba1439c7d79e7e8442ee4c1cc7826a"),
    ("successor", forall(F+U+("L",),trace(F,U,"L")+" -> "+exists(V,trace(F,V,"S L"))),
        (14,39,43,"decode","extend","transport"), "38685aafa594d7dab6fb5f26db27bd00457fd420000b81a1a76404189322f9a1"),
    ("QF004", NAMED_SOURCE, (29,49,"extend","successor"), TARGET_SHA256),
)


class CanonicalTraceError(ValueError):
    """Changed exact canonical trace target, definition, body or cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import pretty_formula, parse_formula_in_context
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(height_registry())
    used = {d.stable_id for d in registry.values()} | {f"ND{i:04d}" for i in range(382,396)}
    # The authenticated v35 parent ends below the local 382--397 extension;
    # inspect its IDs too rather than relying on that historical observation.
    import json
    from sqrt2_power_definitions import PARENT
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    used |= {d["id"] for d in parent}
    names = set(registry) | {d["name"] for d in parent}
    for number,name,parameters,source,dependencies,summary,digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if identifier in used or name in names or not set(dependencies) <= registry.keys():
            raise CanonicalTraceError("canonical trace definition collision/forward reference")
        formula = parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula)) != digest:
            raise CanonicalTraceError("canonical trace definition AST changed")
        expanded = pretty_formula(formula,list(parameters))
        definition = _definition(stable_id=identifier,name=name,parameters=parameters,
            template_source=expanded,summary=summary,category="irrationality_canonical_traces",
            conceptual_dependencies=dependencies)
        if definition.template_formula != formula or parse_formula_in_context(expanded,list(parameters)) != formula:
            raise CanonicalTraceError("canonical trace definition failed ordinary roundtrip")
        registry[name] = definition
        names.add(name)
        used.add(identifier)
    return MappingProxyType(registry)


def frozen_canonical_quadratic_trace_target():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Forall,Exists,And
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    body = target
    for kind,count in ((Forall,9),(Exists,8)):
        for _ in range(count):
            if type(body) is not kind:
                raise CanonicalTraceError("QF004 unconditional binder shape changed")
            body = body.body
    if type(body) is not And or json_hash(encode_formula(target)) != TARGET_SHA256:
        raise CanonicalTraceError("QF004 original target changed")
    return target


def source_contract():
    return dict(code="QF004",schema=SCHEMA,source=NAMED_SOURCE,
        statement_ast_sha256=TARGET_SHA256,premise_count=0,canonical_outputs_constructed=True,
        new_definition_ids=["ND0396","ND0397"],definition_admissions=0,
        reused_definition_ids=["ND0390","ND0394"],
        nonzero_factors_required=False,height_bound_in_definition=False,
        finite_trace_height_bound=False,ordinary_trace_bridge_proved=False,
        real_interpretation=False,rational_denominator_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR046=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def canonical_quadratic_trace_source_pins():
    result = quadratic_trace_exists_source_pins()
    expected = {
        "scripts/sqrt2_power_quadratic_trace_exists.py": "4269d6b9a2282fad3870b408578e2894544c4b172ea76ea2891945adce25ba1a",
        "scripts/sqrt2_power_quadratic_product_exists.py": "c20c38bfceb78fa16c236925024a43c12624b2df23937bb1c1e9f54393d49017",
        "scripts/sqrt2_power_quadratic_height.py": "4dbca16777efcbc535bbab885accd7ad8f6a729edafb48c525365b2c56aec51c",
        ARCHIVES[1]["path"]: ARCHIVES[1]["sha256"],
    }
    for name in (*expected,"scripts/sqrt2_power_canonical_quadratic_trace.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(16*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>16*1024**2 or name in expected and digest != expected[name]:
            raise CanonicalTraceError("QF004 source/archive pin changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def inert_prefix_rows():
    rows = read_archive(ARCHIVES[1])[:105]
    if json_hash(rows) != PREFIX_ROWS_SHA256 or len(canonical(rows)) != PREFIX_ROWS_BYTES:
        raise CanonicalTraceError("actual QF002 beta/decode/extension prefix changed")
    for index,row in enumerate(rows):
        if len(set(row[2])) != len(row[2]) or any(type(d) is not int or not 0<=d<index for d in row[2]):
            raise CanonicalTraceError("actual prefix dependency order changed")
    return rows


def _transport(scope):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro
    from peano_lab.kernel.terms import Succ,Zero
    def main(s):
        zero,one = Zero(),Succ(Zero())
        bound0 = apply(specialize(s,38,zero,s.term("L")),specialize(s,29,s.term("L")))
        initial = apply(specialize(s,"preserve",zero,one,zero,zero,zero),bound0,AndElimL(s.hyp("trace")))
        def step(t):
            source = apply(instantiate(AndElimR(t.hyp("trace")),t.term("i")),t.hyp("bound"))
            def decoded(u):
                i,length,pair = u.term("i"),u.term("L"),u.hyp("step")
                before = apply(specialize(u,40,Succ(i),length),u.hyp("bound"))
                after = apply(specialize(u,38,Succ(i),length),u.hyp("bound"))
                current = apply(specialize(u,"preserve",i,*u.terms(A)),before,field(pair,1,4))
                following = apply(specialize(u,"preserve",Succ(i),*u.terms(C)),after,field(pair,2,4))
                return witness(u.terms(A+B+C),conjunction(field(pair,0,4),current,following,field(pair,3,4)))
            return eliminate(t,source,A+B+C,"step",decoded)
        return AndIntro(initial,introduce(s,("i",),("bound",),step))
    return introduce(scope,F+U+V+("L",),("preserve","trace"),main)


def _successor(scope,registry):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,EqRefl,EqSubst,EqSym,OrElim
    from peano_lab.kernel.terms import Succ
    def decoded(s):
        source = specialize(s,"extend",*s.terms(U),Succ(s.term("L")),*products(s))
        def appended(t):
            def old_trace(u):
                return apply(specialize(u,"transport",*u.terms(F+U+V),u.term("L")),
                    AndElimR(u.hyp("extended")),u.hyp("trace"))
            def step(u):
                le = apply(specialize(u,39,u.term("i"),u.term("L")),u.hyp("bound"))
                split = apply(specialize(u,43,u.term("i"),u.term("L")),le)
                v = u.hypothesis("last")
                length,result = v.term("L"),products(v)
                current = apply(instantiate(AndElimR(v.hyp("extended")),length,*v.terms(A)),
                    specialize(v,14,Succ(length)),v.hyp("current"))
                last = witness(v.terms(A+B)+result,conjunction(v.hyp("factor"),current,
                    AndElimL(v.hyp("extended")),conjunction(*(EqRefl(value) for value in result))))
                motive = parse_named(named("IQuadCanonicalStep",*F,*V,"position"),
                    v.variable("position").variables,registry)
                last_case = EqSubst(motive,EqSym(v.hyp("last")),last)
                w = u.hypothesis("earlier")
                earlier = apply(instantiate(AndElimR(old_trace(w)),w.term("i")),w.hyp("earlier"))
                return OrElim(split,last_case,earlier)
            return witness(t.terms(V),AndIntro(AndElimL(old_trace(t)),introduce(t,("i",),("bound",),step)))
        return eliminate(s,source,V,"extended",appended)
    def main(s):
        def factor(t):
            return eliminate(t,specialize(t,"decode",*t.terms(U),t.term("L")),A,"current",decoded)
        return eliminate(s,specialize(s,"decode",*s.terms(F),s.term("L")),B,"factor",factor)
    return introduce(scope,F+U+("L",),("trace",),main)


@dataclass(frozen=True)
class CanonicalQuadraticTraceCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_canonical_quadratic_trace(*,limits=None):
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Imp
    from peano_lab.kernel.checker import check
    from peano_lab.library.proof_bundle import decode_formula,encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise CanonicalTraceError("expected unchanged BinaryDAGLimits")
    before = canonical_quadratic_trace_source_pins()
    target,registry = frozen_canonical_quadratic_trace_target(),definition_registry()
    rows = inert_prefix_rows()
    endpoints = {old: ANCESTOR_IDS.index(old) for old in (14,29,38,39,40,43,49)}
    endpoints.update(decode=103,extend=104)
    total,deepest = 0,0
    for row in rows:
        count,depth = _inert_metrics(row[3],limits)
        total,deepest = total+count,max(deepest,depth)
        if type(row[0]) is not int or row[0]<8*count+16:
            raise CanonicalTraceError("actual ancestor fuel changed")
    helper_evidence = []
    for name,source,dependencies,digest in HELPERS:
        statement = parse_named(source,registry=registry)
        if json_hash(encode_formula(statement)) != digest:
            raise CanonicalTraceError("QF004 helper target changed")
        finish = (_transport if name=="transport" else
            (lambda s: _successor(s,registry)) if name=="successor" else lambda s: _root(s,statement))
        body = introduce(Scope(),(),dependencies,finish)
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise CanonicalTraceError("QF004 aggregate constructor/node bound exceeded")
        _row_preflight(statement,body,limits)
        linked = tuple(endpoints[d] for d in dependencies)
        curried = statement
        for dependency in reversed(linked):
            curried = Imp(decode_formula(rows[dependency][1]),curried)
        if not check((),body,curried):
            raise CanonicalTraceError("original HA rejected canonical helper: "+name)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(statement),list(linked),encode_proof(body)])
        helper_evidence.append(dict(name=name,node=endpoints[name],source=source,target_ast_sha256=digest,
            dependencies=list(linked),body_nodes=count))
    if rows[-1][1] != encode_formula(target):
        raise CanonicalTraceError("QF004 root target differs")
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise CanonicalTraceError("QF004 unchanged payload bound exceeded")
    del rows,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded != target:
        raise CanonicalTraceError("QF004 canonical target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target != target or canonical_quadratic_trace_source_pins()!=before:
        raise CanonicalTraceError("QF004 source or target changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,ancestor_rows_sha256=PREFIX_ROWS_SHA256,
        actual_ancestor_nodes=105,original_archive=dict(ARCHIVES[1]),helpers=helper_evidence,
        root_induction_count=1,solver_calls=0,ring_normalizer_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return CanonicalQuadraticTraceCertificate(target,bundle,payload,receipt,deepest,provenance)
