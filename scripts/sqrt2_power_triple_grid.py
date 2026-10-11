"""CV012: construct the actual finite triple-product grid for associativity.

The (j,l) cell contains A[j]*(B[k]*C[l]) for j+(k+l)=i, and zero for
j+l>i. Quotient/remainder coordinates and beta-prefix extension construct
all cells. No sum identity or convolution associativity is assumed here.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_natural_convolution import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,
    canonical,json_hash,_inert_metrics,natural_convolution_source_pins,
    definition_registry as convolution_registry,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_quadratic_product_exists import read_archive
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE

SCHEMA = "sqrt2-power-triple-grid-v1"
P = ("ab","ac","L","bb","bc","M","cb","cc","K")


def forall(names,text):
    return "forall "+" ".join(names)+". "+text


def cell(j="j",l="l",z="z"):
    return "NatTripleCell("+",".join(P+("i",j,l,z))+")"


def flat(t="t",z="z"):
    return "NatTripleFlatCell("+",".join(P+("i",t,z))+")"


def prefix(codes=("gb","gc"),length="N"):
    return "NatTripleFlatPrefix("+",".join(P+("i",)+codes+(length,))+")"


GRID = "NatTripleGrid("+",".join(P+("i","gb","gc"))+")"
DEFINITION_ROWS = (
    (414,"NatTripleCell",P+("i","j","l","z"),
     "(exists k a b c. j+(k+l)=i /\\ (BetaZeroExtend(ab,ac,L,j,a) /\\ (BetaZeroExtend(bb,bc,M,k,b) /\\ (BetaZeroExtend(cb,cc,K,l,c) /\\ z=a*(b*c))))) \\/ (Lt(i,j+l) /\\ z=0)",
     ("BetaZeroExtend","Lt"),"55efb062bb8020bddd477ef192529eaf2b6a60834f510447985a5509bfd9b115"),
    (415,"NatTripleFlatCell",P+("i","t","z"),
     "exists j l. t=(S i)*j+l /\\ (Lt(l,S i) /\\ "+cell()+")",
     ("Lt","NatTripleCell"),"f8523f319d5e0047b7e342b3eaea038bfaf2ddc5d3b4febbb75e6664abc92207"),
    (416,"NatTripleFlatPrefix",P+("i","gb","gc","N"),
     "forall t. Lt(t,N) -> exists z. BetaAt(gb,gc,t,z) /\\ "+flat(),
     ("Lt","BetaAt","NatTripleFlatCell"),"0e29f0c9051d238b155343ddaed550b6a421964ce912c4b73e8f73434b8288c0"),
    (417,"NatTripleGrid",P+("i","gb","gc"),
     "forall j l. Lt(j,S i) -> Lt(l,S i) -> exists z. BetaAt(gb,gc,(S i)*j+l,z) /\\ "+cell(),
     ("Lt","BetaAt","NatTripleCell"),"793fcf029f0f6480dc988ec3d1c92da224424221276c6940a9f0acf6a2bf2f34"),
)
NAMED_SOURCE = forall(P+("i",),"exists gb gc. "+GRID)
TARGET_SHA256 = "ac50bc2ab4e67d47f7b5eb88eead79f814654ca2b863006b38df9015214803c2"
HELPER_SOURCES = {
    "grid_index_bound":"forall H j l. Lt(j,H) -> Lt(l,H) -> Lt(H*j+l,H*H)",
    "cell_exists":forall(P+("i","j","l"),"exists z. "+cell()),
    "flat_exists":forall(P+("i","t"),"exists z. "+flat()),
    "prefix_exists":forall(P+("i","N"),"exists gb gc. "+prefix()),
}
HELPER_TARGET_SHA256 = {
    "grid_index_bound":"c72543d7955cf9c51415ef9652aec234c60b1daabcdef7a1613cd2cedb0435ff",
    "cell_exists":"46050db960cfa311277883df053ecd173e9f48a3b40ec32f98873e816dd91cad",
    "flat_exists":"1b2c94222aeddc36dc88e4fb5f996fcf3d6b141bf9108810a99675a1c7d8cfb0",
    "prefix_exists":"4a0744e684f4cd32116b2fb6bd4a5743b286d40f468a0f35a9945e7c047a62ee",
}
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "mul_comm":"forall a b. a*b=b*a",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "mul_le_mul_right":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "le_or_lt":"forall a b. Le(a,b) \\/ Lt(b,a)",
    "division_succ_exists":"forall a n. exists q r. n=(S a)*q+r /\\ Lt(r,S a)",
    "division_unique":"forall d n q r s t. n=d*q+r -> Lt(r,d) -> n=d*s+t -> Lt(t,d) -> q=s /\\ r=t",
    "padding_exists":"forall b c L i. exists a. BetaZeroExtend(b,c,L,i,a)",
    "zero_le":"forall a. Le(0,a)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "le_eq_or_lt":"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)",
    "beta_extend":"forall N b c v. exists eb ec. BetaAt(eb,ec,N,v) /\\ (forall j a. Lt(j,N) -> BetaAt(b,c,j,a) -> BetaAt(eb,ec,j,a))",
}
HELPER_DEPENDENCIES = {
    "grid_index_bound":("add_comm","add_assoc","mul_comm","mul_le_mul_right","le_trans"),
    "cell_exists":("add_comm","add_assoc","le_or_lt","padding_exists"),
    "flat_exists":("division_succ_exists","cell_exists"),
    "prefix_exists":("zero_le","lt_not_le","le_of_succ_le_succ","le_eq_or_lt","beta_extend","flat_exists"),
    "CV012":("prefix_exists","grid_index_bound","division_unique"),
}


class TripleGridError(ValueError):
    """Changed finite cell graph, genuine proof body or resource ceiling."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(convolution_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    for number,name,parameters,source,dependencies,digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if name in registry or any(d["name"]==name or d["id"]==identifier for d in parent):
            raise TripleGridError("triple-grid conservative alias collision")
        formula = parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula))!=digest:
            raise TripleGridError("triple-grid exact expansion changed: "+name)
        text = pretty_formula(formula,list(parameters))
        d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
            summary="Actual zero-padded triple-product cell or decoded finite grid; no sum identity.",
            category="irrationality_formal_series",conceptual_dependencies=dependencies)
        if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
            raise TripleGridError("triple-grid expansion failed exact roundtrip")
        registry[name] = d
    return MappingProxyType(registry)


def frozen_triple_grid_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=10 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise TripleGridError("CV012 exact unconditional triple-grid target changed")
    return target


def source_contract():
    return dict(code="CV012",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,whole_finite_grid_constructed=True,actual_quotient_remainder_coordinates=True,
        arbitrary_input_lengths_and_index=True,grid_width="S i",
        new_definition_ids=["ND0414","ND0415","ND0416","ND0417"],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        row_column_sum_identities=False,natural_convolution_associativity=False,
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def triple_grid_source_pins():
    result = natural_convolution_source_pins()
    expected = {
        "scripts/sqrt2_power_natural_convolution.py":"a5498a8534df2e1618419bb2a4ee382d3ebd205fd024560cca9876ab9e4eedd1",
        "scripts/sqrt2_power_quadratic_height.py":"4dbca16777efcbc535bbab885accd7ad8f6a729edafb48c525365b2c56aec51c",
        "scripts/sqrt2_power_quadratic_product_exists.py":"c20c38bfceb78fa16c236925024a43c12624b2df23937bb1c1e9f54393d49017",
        "scripts/sqrt2_power_series_power_trace.py":"557d393791fb527361bcffb4977b0e0bad591f98a426e12d1da461643cc39422",
        CONVOLUTION_ARCHIVE["path"]:CONVOLUTION_ARCHIVE["sha256"],
    }
    for name in (*expected,"scripts/sqrt2_power_triple_grid.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise TripleGridError("triple-grid source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _subst(s,registry,source,equation,proof):
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import EqSubst
    return EqSubst(parse_named(source,s.variable("slot").variables,registry),equation,proof)


def _grid_index_bound(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _additive_equal,_chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym,ExistsIntro
    from peano_lab.kernel.terms import Add,Mul,Succ
    def decoded(t):
        H,j,l,g = t.terms(("H","j","l","g"))
        hj = Mul(H,j)
        equation = _chain(CongAdd(EqRefl(g),EqSym(instantiate(Axiom("PA4"),hj,l))),
            _additive_equal(t,Add(g,Add(hj,Succ(l))),Add(hj,Add(g,Succ(l)))),
            CongAdd(EqRefl(hj),t.hyp("gap")),EqSym(instantiate(Axiom("PA6"),H,j)),
            specialize(t,"mul_comm",H,Succ(j)))
        lower = ExistsIntro(g,equation)
        upper = apply(specialize(t,"mul_le_mul_right",Succ(j),H,H),t.hyp("row"))
        return apply(specialize(t,"le_trans",Succ(Add(hj,l)),Mul(Succ(j),H),Mul(H,H)),lower,upper)
    return introduce(s,("H","j","l"),("row","column"),lambda t:
        eliminate(t,t.hyp("column"),("g",),"gap",decoded))


def _cell_exists(s):
    from sqrt2_power_quadratic_height import _additive_equal
    from peano_lab.kernel.proofs import AndIntro,EqRefl,EqTrans,OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Add,Mul,Zero
    def finish(t):
        def inside(u):
            def gap(v):
                def values(w,position):
                    if position==3:
                        j,k,l = w.terms(("j","k","l"))
                        index = EqTrans(_additive_equal(w,Add(j,Add(k,l)),Add(k,Add(j,l))),w.hyp("gap"))
                        product = Mul(w.term("a"),Mul(w.term("b"),w.term("c")))
                        data = conjunction(index,w.hyp("first"),w.hyp("middle"),w.hyp("last"),EqRefl(product))
                        return witness((product,),OrIntroL(witness(w.terms(("k","a","b","c")),data)))
                    parameters,value,label = (
                        (("ab","ac","L","j"),"a","first"),
                        (("bb","bc","M","k"),"b","middle"),
                        (("cb","cc","K","l"),"c","last"),
                    )[position]
                    return eliminate(w,specialize(w,"padding_exists",*w.terms(parameters)),(value,),label,lambda x:values(x,position+1))
                return values(v,0)
            return eliminate(u,u.hyp("inside"),("k",),"gap",gap)
        def outside(u):
            return witness((Zero(),),OrIntroR(AndIntro(u.hyp("outside"),EqRefl(Zero()))))
        choice = specialize(t,"le_or_lt",Add(t.term("j"),t.term("l")),t.term("i"))
        return OrElim(choice,inside(t.hypothesis("inside")),outside(t.hypothesis("outside")))
    return introduce(s,P+("i","j","l"),(),finish)


def _flat_exists(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def coordinates(t):
        return eliminate(t,specialize(t,"cell_exists",*t.terms(P+("i","j","l"))),("z",),"cell",lambda u:
            witness((u.term("z"),),witness(u.terms(("j","l")),
                conjunction(AndElimL(u.hyp("division")),AndElimR(u.hyp("division")),u.hyp("cell")))))
    return introduce(s,P+("i","t"),(),lambda t:
        eliminate(t,specialize(t,"division_succ_exists",*t.terms(("i","t"))),("j","l"),"division",coordinates))


def _prefix_exists(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,BotElim,EqSym,Ind,OrElim
    from peano_lab.kernel.terms import Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("t",),("bound",),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("t"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("t"))))))
    def step(t):
        def old(u):
            def value(v):
                def extended(w):
                    def entry(x):
                        def last(y):
                            actual = witness((y.term("z"),),AndIntro(AndElimL(y.hyp("extension")),y.hyp("value")))
                            return _subst(y,registry,"exists a. BetaAt(gb,gc,slot,a) /\\ "+flat("slot","a"),EqSym(y.hyp("last")),actual)
                        def earlier(y):
                            def decoded(z):
                                kept = apply(instantiate(AndElimR(z.hyp("extension")),*z.terms(("t","a"))),z.hyp("earlier"),AndElimL(z.hyp("old_entry")))
                                return witness((z.term("a"),),AndIntro(kept,AndElimR(z.hyp("old_entry"))))
                            return eliminate(y,apply(specialize(y,"old",y.term("t")),y.hyp("earlier")),("a",),"old_entry",decoded)
                        lower = apply(specialize(x,"le_of_succ_le_succ",*x.terms(("t","N"))),x.hyp("bound"))
                        cases = apply(specialize(x,"le_eq_or_lt",*x.terms(("t","N"))),lower)
                        return OrElim(cases,last(x.hypothesis("last")),earlier(x.hypothesis("earlier")))
                    return witness(w.terms(("gb","gc")),introduce(w,("t",),("bound",),entry))
                return eliminate(v,specialize(v,"beta_extend",*v.terms(("N","ob","oc","z"))),("gb","gc"),"extension",extended)
            return eliminate(u,specialize(u,"flat_exists",*u.terms(P+("i","N"))),("z",),"value",value)
        return eliminate(t,t.hyp("IH"),("ob","oc"),"old",old)
    motive = target
    for _ in range(11):
        motive = motive.body
    return introduce(s,P+("i",),(),lambda t:Ind(motive,base(t),introduce(t,("N",),("IH",),step)))


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ
    def codes(t):
        def cell_at(u):
            def value(v):
                def coordinates(w):
                    width = Succ(w.term("i"))
                    index = Add(Mul(width,w.term("j")),w.term("l"))
                    identity = apply(specialize(w,"division_unique",width,index,*w.terms(("r","q","j","l"))),
                        field(w.hyp("coordinates"),0,3),field(w.hyp("coordinates"),1,3),EqRefl(index),w.hyp("column"))
                    row = _subst(w,registry,cell("slot","q","z"),AndElimL(identity),field(w.hyp("coordinates"),2,3))
                    cell_proof = _subst(w,registry,cell("j","slot","z"),AndElimR(identity),row)
                    return witness((w.term("z"),),AndIntro(AndElimL(w.hyp("entry")),cell_proof))
                return eliminate(v,AndElimR(v.hyp("entry")),("r","q"),"coordinates",coordinates)
            width = Succ(u.term("i"))
            index = Add(Mul(width,u.term("j")),u.term("l"))
            bound = apply(specialize(u,"grid_index_bound",width,*u.terms(("j","l"))),u.hyp("row"),u.hyp("column"))
            return eliminate(u,apply(specialize(u,"prefix",index),bound),("z",),"entry",value)
        return witness(t.terms(("gb","gc")),introduce(t,("j","l"),("row","column"),cell_at))
    def construct(t):
        width = Succ(t.term("i"))
        return eliminate(t,specialize(t,"prefix_exists",*t.terms(P+("i",)),Mul(width,width)),("gb","gc"),"prefix",codes)
    return introduce(s,P+("i",),(),construct)


@dataclass(frozen=True)
class TripleGridCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_triple_grid(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise TripleGridError("expected unchanged BinaryDAGLimits")
    before = triple_grid_source_pins()
    target,registry = frozen_triple_grid_target(),definition_registry()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise TripleGridError("exact finite-grid helper formula changed")
    formulas["CV012"] = target
    original = read_archive(CONVOLUTION_ARCHIVE)
    endpoints = {}
    for name,source in ENDPOINT_SOURCES.items():
        formula = encode_formula(parse_named(source,registry=registry))
        matches = [i for i,row in enumerate(original) if row[1]==formula]
        if len(matches)!=1:
            raise TripleGridError("actual full-body endpoint missing or ambiguous: "+name)
        endpoints[name] = matches[0]
    reached,pending = set(),list(endpoints.values())
    while pending:
        old = pending.pop()
        if old not in reached:
            row = original[old]
            if len(row)!=4 or len(row[2])!=len(set(row[2])) or any(type(d) is not int or not 0<=d<old for d in row[2]):
                raise TripleGridError("actual ancestor ordered dependencies changed")
            reached.add(old)
            pending.extend(row[2])
    ids = tuple(sorted(reached))
    remap = {old:new for new,old in enumerate(ids)}
    rows = [[original[old][0],original[old][1],[remap[d] for d in original[old][2]],original[old][3]] for old in ids]
    endpoint_original_ids = dict(endpoints)
    endpoints = {name:remap[old] for name,old in endpoints.items()}
    total,deepest = 0,0
    for row in rows:
        count,depth = _inert_metrics(row[3],limits)
        total,deepest = total+count,max(deepest,depth)
        if row[0]<8*count+16:
            raise TripleGridError("actual ancestor fuel does not cover its ordinary body")
    ancestor_total = total
    factories = {"grid_index_bound":_grid_index_bound,"cell_exists":_cell_exists,"flat_exists":_flat_exists,
        "prefix_exists":lambda s:_prefix_exists(s,formulas["prefix_exists"],registry),"CV012":lambda s:_root(s,registry)}
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise TripleGridError("finite-grid aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in dependencies],encode_proof(body)])
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise TripleGridError("finite-grid canonical payload bound exceeded")
    del rows,original,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise TripleGridError("decoded finite-grid target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or triple_grid_source_pins()!=before:
        raise TripleGridError("finite-grid target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,actual_triple_grid_constructed=True,
        actual_ancestor_nodes=len(ids),actual_ancestor_body_nodes=ancestor_total,
        ancestor_original_ids=list(ids),endpoint_original_ids=endpoint_original_ids,
        ordered_dependency_remapping_only=True,actual_archive=dict(CONVOLUTION_ARCHIVE),
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),
        helper_bundle_indices={name:endpoints[name] for name in HELPER_DEPENDENCIES},new_induction_count=1,
        ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,new_axioms=[],
        external_certificate_references=[],independent_lean_checked=False)
    return TripleGridCertificate(target,bundle,payload,receipt,deepest,provenance)
