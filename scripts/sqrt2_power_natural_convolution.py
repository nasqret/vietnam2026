"""CV003: construct an arbitrary finite natural convolution with unique values.

The historical antidiagonal and sum bodies are replayed, not imported as named
axioms. There is no field modulus and no reduction modulo a prime. The new
notation is suitable for ascending formal-series tables; no highest-first
evaluation/degree theorem is used. This is not yet power-table execution,
formal differentiation, rational coefficient transport, or the analytic limit.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType

from sqrt2_power_convolution_vanishing import (
    convolution_definitions, convolution_source_pins, ARTIFACT, ARTIFACT_BYTES, ARTIFACT_SHA256,
)
from sqrt2_power_quadratic_trace_exists import (
    ROOT, Scope, introduce, eliminate, witness, field, apply, specialize,
    canonical, json_hash, _inert_metrics, quadratic_trace_exists_source_pins,
)

SCHEMA = "sqrt2-power-natural-convolution-v1"
P = ("ab","ac","L","bb","bc","M")
O = ("cb","cc")
Q = ("eb","ec")


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def coefficient(index,value):
    return "NatConvolutionCoefficient("+",".join(P+(index,value))+")"


def prefix(codes,length):
    return "NatConvolutionPrefix("+",".join(P+codes+(length,))+")"


def preserved(old,new,length):
    return ("forall j a. Lt(j,"+length+") -> BetaAt("+",".join(old)+",j,a) -> "
        "BetaAt("+",".join(new)+",j,a)")


DEFINITION_ROWS = (
    (401,"NatConvolutionCoefficient",P+("i","n"),
     "exists db dc. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,i,db,dc,S i) /\\ Sum(db,dc,S i,n)",
     ("PolynomialDiagonalPrefix","Sum"),"87f2cddc10f40a058ec59a0cf6e0397c8d0a13f36635bcd739e73cde8f1d19f6"),
    (402,"NatConvolutionPrefix",P+O+("N",),
     "forall i. Lt(i,N) -> exists n. BetaAt(cb,cc,i,n) /\\ "+coefficient("i","n"),
     ("Lt","BetaAt","NatConvolutionCoefficient"),"aa579d06bb9cba638577aaa19261b53e6a5063982a447f8f3c731c2f823bc48c"),
)
NAMED_SOURCE = forall(P+("N",),"exists cb cc. "+prefix(O,"N")+" /\\ ("+
    forall(Q,prefix(Q,"N")+" -> ("+preserved(O,Q,"N")+"))"))
TARGET_SHA256 = "b5ad2ef80b9ae8fd100f25b2a128eac7af5d8d58a783e89d2aab7f5bf9c4b0d8"
HELPER_SOURCES = {
    "coefficient_exists": forall(P+("i",),"exists n. "+coefficient("i","n")),
    "coefficient_unique": forall(P+("i","n","m"),coefficient("i","n")+" -> "+coefficient("i","m")+" -> n=m"),
    "prefix_entry": forall(P+O+("N","i","a"),prefix(O,"N")+" -> Lt(i,N) -> BetaAt(cb,cc,i,a) -> "+coefficient("i","a")),
    "prefix_exists": forall(P+("N",),"exists cb cc. "+prefix(O,"N")),
    "prefix_unique": forall(P+O+Q+("N",),prefix(O,"N")+" -> "+prefix(Q,"N")+" -> ("+preserved(O,Q,"N")+")"),
}
HELPER_TARGET_SHA256 = {
    "coefficient_exists":"ef7b4ff210811458d8f82ed42ce2b9c4d0b8bfcb9ba510275ad33002fe1920d5",
    "coefficient_unique":"af36d7a990000ff6eddb51a22cf82d751b5ebd5f1f24a7cb2608e5fa9d6a131c",
    "prefix_entry":"4cfe45bd2a19ca40768dff3fc0d7fa6b30fc949fcd62c1f60ff2c118b18d85e8",
    "prefix_exists":"42b0065cb5fcd4af634f372832833175d34f1a6f685d48c6d1051f4eb4a60eb4",
    "prefix_unique":"67e18bb120db231152076e780996994d30dfe25a55e29695329ff7e4d6f0c43b",
}
ENDPOINT_SOURCES = {
    "le_refl": "forall a. Le(a,a)",
    "zero_le": "forall a. Le(0,a)",
    "le_of_succ_le_succ": "forall a b. Le(S a,S b) -> Le(a,b)",
    "le_eq_or_lt": "forall a b. Le(a,b) -> a=b \\/ Lt(a,b)",
    "lt_not_le": "forall a b. Lt(a,b) -> Le(b,a) -> false",
    "beta_at_exists": "forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_at_unique": "forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "beta_prefix_extend": "forall N b c v. exists eb ec. BetaAt(eb,ec,N,v) /\\ ("+preserved(("b","c"),("eb","ec"),"N")+")",
    "diagonal_exists": forall(P+("i",),"exists db dc. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,i,db,dc,S i)"),
    "diagonal_unique": forall(P+("i","db","dc","eb","ec","N"),
        "PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,i,db,dc,N) -> "
        "PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,i,eb,ec,N) -> ("+preserved(("db","dc"),Q,"N")+")"),
    "sum_exists": "forall b c N. exists n. Sum(b,c,N,n)",
    "sum_unique": "forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m",
    "sum_transport": "forall b c eb ec N n. Sum(b,c,N,n) -> ("+preserved(("b","c"),Q,"N")+") -> Sum(eb,ec,N,n)",
}
ENDPOINT_IDS = dict(le_refl=13,zero_le=24,le_of_succ_le_succ=33,le_eq_or_lt=37,
    lt_not_le=40,beta_at_exists=87,beta_at_unique=88,beta_prefix_extend=116,
    diagonal_exists=172,diagonal_unique=171,sum_exists=122,sum_unique=124,sum_transport=137)
ANCESTOR_IDS = (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,
    32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,55,56,57,58,59,60,63,65,66,67,
    68,69,70,71,72,76,78,79,80,81,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,
    104,105,106,107,108,109,110,111,112,113,114,115,116,121,122,123,124,133,137,156,157,161,162,168,170,171,172)
ANCESTOR_ROWS_SHA256 = "7978c74f26a5d6cfe517e0f90f7ed6f64409692c19929c310a534012bc75c439"
ANCESTOR_ROWS_BYTES = 214712
HELPER_DEPENDENCIES = {
    "coefficient_exists": ("diagonal_exists","sum_exists"),
    "coefficient_unique": ("diagonal_unique","sum_transport","sum_unique"),
    "prefix_entry": ("beta_at_unique",),
    "prefix_exists": ("lt_not_le","zero_le","le_refl","le_of_succ_le_succ","le_eq_or_lt","beta_prefix_extend","coefficient_exists"),
    "prefix_unique": ("beta_at_exists","prefix_entry","coefficient_unique"),
    "CV003": ("prefix_exists","prefix_unique"),
}


class NaturalConvolutionError(ValueError):
    """Wrong exact target, actual proof ancestry, definition, or resource cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.library.proof_bundle import encode_formula
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    registry = dict(convolution_definitions())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids = {d["id"] for d in parent}|{f"ND{i:04d}" for i in range(382,401)}
    names = {d["name"] for d in parent}|set(registry)|{"NatExpAtanhRecurrence"}
    for number,name,parameters,source,dependencies,digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if identifier in ids or name in names or not set(dependencies)<=registry.keys():
            raise NaturalConvolutionError("natural convolution definition collision or forward edge")
        formula = parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula))!=digest:
            raise NaturalConvolutionError("natural convolution exact expansion changed")
        text = pretty_formula(formula,list(parameters))
        d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
            summary="Actual natural antidiagonal execution; no modulus, algebraic law or correctness conclusion.",
            category="irrationality_formal_series",conceptual_dependencies=dependencies)
        if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
            raise NaturalConvolutionError("natural convolution expansion failed exact roundtrip")
        registry[name] = d
        ids.add(identifier)
        names.add(name)
    return MappingProxyType(registry)


def frozen_natural_convolution_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise NaturalConvolutionError("CV003 original unconditional statement changed")
    return target


def source_contract():
    return dict(code="CV003",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,arbitrary_input_and_output_lengths=True,coefficient_order="ascending_series",
        modulus_required=False,actual_sum_required=True,output_table_supplied=False,
        code_number_uniqueness=False,coefficientwise_uniqueness=True,new_definition_ids=["ND0401","ND0402"],
        definition_admissions=0,original_HA_checked=False,authority="source_contract_not_proof_authority",
        power_table_execution=False,rational_coefficient_transport=False,formal_derivative=False,
        analytic_limit_claim=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def natural_convolution_source_pins():
    result = convolution_source_pins()
    result.update(quadratic_trace_exists_source_pins())
    expected = {
        "scripts/sqrt2_power_quadratic_trace_exists.py":"4269d6b9a2282fad3870b408578e2894544c4b172ea76ea2891945adce25ba1a",
        "scripts/sqrt2_power_convolution_vanishing.py":"ff4e9888f43ac908c1935b29d015a3ab239eeafc6c26407e8ddab8246fa9ad72",
    }
    for name in (*expected,"scripts/sqrt2_power_natural_convolution.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise NaturalConvolutionError("natural convolution source changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def inert_convolution_rows(artifact_path=ARTIFACT):
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(ARTIFACT_BYTES+1)
    if len(raw)!=ARTIFACT_BYTES or sha256(raw).hexdigest()!=ARTIFACT_SHA256:
        raise NaturalConvolutionError("actual polynomial archive bytes changed")
    archive = json.loads(raw)
    if archive[0]!="peano-lab-bundle-v1" or archive[1]!=209 or len(archive[3])!=210:
        raise NaturalConvolutionError("actual polynomial archive envelope changed")
    seen,pending = set(),list(ENDPOINT_IDS.values())
    while pending:
        old = pending.pop()
        if type(old) is not int or not 0<=old<210:
            raise NaturalConvolutionError("invalid actual polynomial ancestor index")
        if old not in seen:
            row = archive[3][old]
            if len(row)!=4 or len(row[2])!=len(set(row[2])) or any(type(d) is not int or not 0<=d<old for d in row[2]):
                raise NaturalConvolutionError("invalid actual polynomial ordered dependencies")
            seen.add(old)
            pending.extend(row[2])
    ids = tuple(sorted(seen))
    rows = tuple(archive[3][old] for old in ids)
    if ids!=ANCESTOR_IDS or len(canonical(rows))!=ANCESTOR_ROWS_BYTES or json_hash(rows)!=ANCESTOR_ROWS_SHA256:
        raise NaturalConvolutionError("exact natural convolution ancestor cone changed")
    registry = definition_registry()
    if set(ENDPOINT_IDS)!=set(ENDPOINT_SOURCES):
        raise NaturalConvolutionError("missing actual endpoint")
    for name,source in ENDPOINT_SOURCES.items():
        if archive[3][ENDPOINT_IDS[name]][1]!=encode_formula(parse_named(source,registry=registry)):
            raise NaturalConvolutionError("actual endpoint differs from its independently frozen formula")
    return ids,rows


def _coefficient_exists(s):
    from peano_lab.kernel.proofs import AndIntro,ExistsIntro
    from peano_lab.kernel.terms import Succ
    def diagonal(t):
        def summed(u):
            return witness(u.terms(("n","db","dc")),AndIntro(u.hyp("diagonal"),u.hyp("sum")))
        return eliminate(t,specialize(t,"sum_exists",*t.terms(("db","dc")),Succ(t.term("i"))),("n",),"sum",summed)
    return introduce(s,P+("i",),(),lambda t:
        eliminate(t,specialize(t,"diagonal_exists",*t.terms(P+("i",))),("db","dc"),"diagonal",diagonal))


def _coefficient_unique(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ
    def finish(t):
        length = Succ(t.term("i"))
        equality = apply(specialize(t,"diagonal_unique",*t.terms(P+("i","db","dc","eb","ec")),length),
            AndElimL(t.hyp("first")),AndElimL(t.hyp("second")))
        transported = apply(specialize(t,"sum_transport",*t.terms(("db","dc","eb","ec")),length,t.term("n")),
            AndElimR(t.hyp("first")),equality)
        return apply(specialize(t,"sum_unique",*t.terms(("eb","ec")),length,*t.terms(("n","m"))),
            transported,AndElimR(t.hyp("second")))
    return introduce(s,P+("i","n","m"),("left","right"),lambda t:
        eliminate(t,t.hyp("left"),("db","dc"),"first",lambda u:
            eliminate(u,u.hyp("right"),("eb","ec"),"second",finish)))


def _prefix_entry(s,registry):
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqSubst
    def chosen(t):
        equal = apply(specialize(t,"beta_at_unique",*t.terms(O+("i","n","a"))),
            AndElimL(t.hyp("value")),t.hyp("entry"))
        motive = parse_named(coefficient("i","value_slot"),t.variable("value_slot").variables,registry)
        return EqSubst(motive,equal,AndElimR(t.hyp("value")))
    return introduce(s,P+O+("N","i","a"),("prefix","bound","entry"),lambda t:
        eliminate(t,apply(specialize(t,"prefix",t.term("i")),t.hyp("bound")),("n",),"value",chosen))


def _prefix_exists(s,target,registry):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import (AndIntro,AndElimL,AndElimR,BotElim,EqSubst,EqSym,Ind,OrElim,ExistsIntro)
    from peano_lab.kernel.terms import Succ,Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("j",),("bound",),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("j"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("j"))))))
    def step(t):
        def old(u):
            def value(v):
                def extended(w):
                    def entry(x):
                        def last(y):
                            def transport(source,proof):
                                motive = parse_named(source,y.variable("index_slot").variables,registry)
                                return EqSubst(motive,EqSym(y.hyp("last")),proof)
                            decoded = transport("BetaAt(cb,cc,index_slot,n)",AndElimL(y.hyp("extension")))
                            computed = transport(coefficient("index_slot","n"),y.hyp("coefficient"))
                            return ExistsIntro(y.term("n"),AndIntro(decoded,computed))
                        def earlier(y):
                            def chosen(z):
                                transported = apply(instantiate(AndElimR(z.hyp("extension")),*z.terms(("j","a"))),
                                    z.hyp("earlier"),AndElimL(z.hyp("old_value")))
                                return ExistsIntro(z.term("a"),AndIntro(transported,AndElimR(z.hyp("old_value"))))
                            return eliminate(y,apply(specialize(y,"old_prefix",y.term("j")),y.hyp("earlier")),("a",),"old_value",chosen)
                        bound = apply(specialize(x,"le_of_succ_le_succ",*x.terms(("j","N"))),x.hyp("bound"))
                        cases = apply(specialize(x,"le_eq_or_lt",*x.terms(("j","N"))),bound)
                        return OrElim(cases,last(x.hypothesis("last")),earlier(x.hypothesis("earlier")))
                    return witness(w.terms(O),introduce(w,("j",),("bound",),entry))
                extension = specialize(v,"beta_prefix_extend",*v.terms(("N","ob","oc","n")))
                return eliminate(v,extension,O,"extension",extended)
            return eliminate(u,specialize(u,"coefficient_exists",*u.terms(P+("N",))),("n",),"coefficient",value)
        return eliminate(t,t.hyp("IH"),("ob","oc"),"old_prefix",old)
    motive = target
    for _ in range(7):
        motive = motive.body
    return introduce(s,P,(),lambda t:Ind(motive,base(t),introduce(t,("N",),("IH",),step)))


def _prefix_unique(s,registry):
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import EqSubst,EqSym
    def chosen(t):
        first = apply(specialize(t,"prefix_entry",*t.terms(P+O+("N","j","a"))),t.hyp("left"),t.hyp("bound"),t.hyp("entry"))
        second = apply(specialize(t,"prefix_entry",*t.terms(P+Q+("N","j","v"))),t.hyp("right"),t.hyp("bound"),t.hyp("other"))
        equality = apply(specialize(t,"coefficient_unique",*t.terms(P+("j","a","v"))),first,second)
        motive = parse_named("BetaAt(eb,ec,j,value_slot)",t.variable("value_slot").variables,registry)
        return EqSubst(motive,EqSym(equality),t.hyp("other"))
    return introduce(s,P+O+Q+("N",),("left","right"),lambda t:
        introduce(t,("j","a"),("bound","entry"),lambda u:
            eliminate(u,specialize(u,"beta_at_exists",*u.terms(Q+("j",))),("v",),"other",chosen)))


def _root(s):
    from peano_lab.kernel.proofs import AndIntro
    def chosen(t):
        unique = introduce(t,Q,("other_prefix",),lambda u:
            apply(specialize(u,"prefix_unique",*u.terms(P+O+Q+("N",))),u.hyp("prefix"),u.hyp("other_prefix")))
        return witness(t.terms(O),AndIntro(t.hyp("prefix"),unique))
    return introduce(s,P+("N",),(),lambda t:
        eliminate(t,specialize(t,"prefix_exists",*t.terms(P+("N",))),O,"prefix",chosen))


@dataclass(frozen=True)
class NaturalConvolutionCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_natural_convolution(*,limits=None,artifact_path=ARTIFACT):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise NaturalConvolutionError("expected unchanged BinaryDAGLimits")
    before = natural_convolution_source_pins()
    registry,target = definition_registry(),frozen_natural_convolution_target()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise NaturalConvolutionError("exact natural convolution helper target changed")
    formulas["CV003"] = target
    ids,original = inert_convolution_rows(artifact_path)
    remap = {old:new for new,old in enumerate(ids)}
    rows = [[r[0],r[1],[remap[d] for d in r[2]],r[3]] for r in original]
    endpoints = {name:remap[old] for name,old in ENDPOINT_IDS.items()}
    total,deepest = 0,0
    for row in rows:
        count,depth = _inert_metrics(row[3],limits)
        total,deepest = total+count,max(deepest,depth)
        if type(row[0]) is not int or row[0]<8*count+16:
            raise NaturalConvolutionError("actual ancestor fuel does not cover its body")
    ancestor_total = total
    factories = {
        "coefficient_exists":_coefficient_exists,"coefficient_unique":_coefficient_unique,
        "prefix_entry":lambda s:_prefix_entry(s,registry),
        "prefix_exists":lambda s:_prefix_exists(s,formulas["prefix_exists"],registry),
        "prefix_unique":lambda s:_prefix_unique(s,registry),"CV003":_root,
    }
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise NaturalConvolutionError("natural convolution aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in dependencies],encode_proof(body)])
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise NaturalConvolutionError("natural convolution canonical payload bound exceeded")
    del rows,original,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise NaturalConvolutionError("natural convolution decoded target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or natural_convolution_source_pins()!=before:
        raise NaturalConvolutionError("natural convolution source/target changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,finite_convolution_constructed=True,
        actual_ancestor_nodes=len(ids),actual_ancestor_body_nodes=ancestor_total,
        ancestor_original_ids=list(ids),ancestor_rows_sha256=ANCESTOR_ROWS_SHA256,
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),root_induction_count=1,
        ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,new_axioms=[],
        external_certificate_references=[],independent_lean_checked=False)
    return NaturalConvolutionCertificate(target,bundle,payload,receipt,deepest,provenance)
