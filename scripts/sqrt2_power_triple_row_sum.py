"""CV013: identify an actual triple-grid row with a scaled Cauchy coefficient.

Given j+r=i and an actual padded value A[j]=a, a coded row whose cells satisfy
the unchanged triple-cell computation has total a*(C*B)[r]. Both coefficient
and row-sum witnesses are constructed. The row graph contains no sum law.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_triple_grid import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,_inert_metrics,read_archive,definition_registry as grid_registry,
    triple_grid_source_pins,P,cell,CONVOLUTION_ARCHIVE,_subst,
)
from sqrt2_power_sum_zero_tail import (
    definition_registry as tail_registry,sum_zero_tail_source_pins,NAMED_SOURCE as ZERO_TAIL_SOURCE,
)
from sqrt2_power_sum_linearity import LINEARITY_SOURCE
from sqrt2_power_euler_product import coefficient

SCHEMA = "sqrt2-power-triple-row-sum-v1"
A,B,C = P[:3],P[3:6],P[6:]
ZERO_TAIL_ARCHIVE = dict(case="CV011",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-sum-zero-tail-v1/generation-process.json.gz",
    bytes=23585,sha256="37814931ce1d3e065b2e1301e0fbe7de6385a9411858917f6b93d3a9c87f29ab",
    raw_bytes=440073,raw_sha256="aeed77fcf6c83d38880aedd470987ef1ac2a5388e15ba4c47e118e5d43ef4e87",
    bundle_bytes=264420,bundle_sha256="bdd2e9754c7c3700e19d4a26426a490e34fabfb435f0020e9b99ab26d984ff55",
    nodes=123,root=122,target_ast_sha256="a7f186fd8bb8fecb316c79650a437ffc8e7c8a66e971c9cdf9740c56e26fe28e")
ROW_PARAMETERS = P+("i","j","ub","uc")
DEFINITION_SOURCE = "forall l z. Lt(l,S i) -> BetaAt(ub,uc,l,z) -> "+cell()
DEFINITION_SHA256 = "c428073b1a9784ed4d60e18ef7a47ae0a844b5743a105d37038148410d8674d9"
ROW = "NatTripleRowPrefix("+",".join(ROW_PARAMETERS)+")"
PARAMETERS = P+("i","j","r","a","ub","uc")
PREMISES = "j+r=i -> BetaZeroExtend(ab,ac,L,j,a) -> "+ROW+" -> "
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+PREMISES+"exists t s. "+coefficient(C,B,"r","t")+" /\\ (Sum(ub,uc,S i,s) /\\ s=a*t)"
TARGET_SHA256 = "835ed495fdd7f286cacdd0a59c544660f11c1fac47fb70eac20dad374b982a57"
HELPER_SOURCES = {
    "add_bound_right":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "row_span":"forall i j r. j+r=i -> Le(S r,S i)",
    "tail_index":"forall i j r h. j+r=i -> Lt(h,j) -> Lt(S r+h,S i)",
    "cell_match":"forall "+" ".join(P+("i","j","r","a","l","t","z"))+". j+r=i -> BetaZeroExtend(ab,ac,L,j,a) -> "
        "PolynomialDiagonalTerm("+",".join(C+B+("r","l","t"))+") -> "+cell()+" -> z=a*t",
    "cell_zero":"forall "+" ".join(P+("i","j","r","l","z"))+". j+r=i -> Lt(r,l) -> "+cell()+" -> z=0",
    "row_rule":"forall "+" ".join(PARAMETERS+("t","s"))+". "+PREMISES+coefficient(C,B,"r","t")+" -> Sum(ub,uc,S i,s) -> s=a*t",
}
HELPER_TARGET_SHA256 = {
    "add_bound_right":"e6e45fb1981e9ebe3aa19bc25b7bd4e32c372966957515126a60ad7304ea86c3",
    "row_span":"c0164a32718189b76109c3fd8240f18303fc9b2a1bb0f37f961d12c5d6cecbe8",
    "tail_index":"b835ba5c8a54233e5b9caada4cdd81161c7b1a4d171da7c841ed04f7f523b92f",
    "cell_match":"ec45dafaf9df2ecee117974143b24138c517e6b6d7d9169dc39eaed53503e497",
    "cell_zero":"481f3f56ec5621645e95788e54b96834a966c44d010c4d771a7aae6479902a9e",
    "row_rule":"2a443e6421ca1da86b9d5c085cac4be82cff99857df8d55a61bdb90e471f4f5b",
}
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "add_succ_left":"forall a b. S a+b=S (a+b)",
    "mul_comm":"forall a b. a*b=b*a",
    "one_mul":"forall a. 1*a=a",
    "mul_zero_left":"forall a. 0*a=0",
    "add_left_cancel":"forall a b c. a+b=a+c -> b=c",
    "add_right_cancel":"forall a b c. a+c=b+c -> a=b",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "padding_unique":"forall b c L i a d. BetaZeroExtend(b,c,L,i,a) -> BetaZeroExtend(b,c,L,i,d) -> a=d",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "sum_unique":"forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m",
    "diagonal_entry":"forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)",
    "coefficient_exists":"forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)",
    "linearity":LINEARITY_SOURCE,
    "zero_tail":ZERO_TAIL_SOURCE,
}
HELPER_DEPENDENCIES = {
    "add_bound_right":("add_assoc",),
    "row_span":(),
    "tail_index":("add_bound_right","succ_le_succ","add_succ_left","add_comm"),
    "cell_match":("add_comm","add_assoc","add_left_cancel","add_right_cancel","padding_unique","mul_comm","lt_not_le"),
    "cell_zero":("add_left_cancel","lt_not_le"),
    "row_rule":("sum_exists","beta_exists","tail_index","cell_zero","zero_tail","add_succ_left","add_comm","row_span","le_trans","diagonal_entry","cell_match","linearity","one_mul","mul_zero_left","sum_unique"),
    "CV013":("coefficient_exists","sum_exists","row_rule"),
}


class TripleRowSumError(ValueError):
    """Changed genuine row computation, exact formula or resource cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(grid_registry())
    for name,d in tail_registry().items():
        if name in registry and (registry[name].stable_id!=d.stable_id or registry[name].template_formula!=d.template_formula):
            raise TripleRowSumError("shared finite-sum/grid definitions disagree")
        registry[name] = d
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    name,identifier = "NatTripleRowPrefix","ND0418"
    if name in registry or any(d["name"]==name or d["id"]==identifier for d in parent):
        raise TripleRowSumError("triple-row alias collision")
    formula = parse_named(DEFINITION_SOURCE,ROW_PARAMETERS,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise TripleRowSumError("triple-row exact expansion changed")
    text = pretty_formula(formula,list(ROW_PARAMETERS))
    d = _definition(stable_id=identifier,name=name,parameters=ROW_PARAMETERS,template_source=text,
        summary="A decoded finite prefix of actual triple cells; no row-sum identity.",
        category="irrationality_formal_series",conceptual_dependencies=("Lt","BetaAt","NatTripleCell"))
    if d.template_formula!=formula or parse_formula_in_context(text,list(ROW_PARAMETERS))!=formula:
        raise TripleRowSumError("row computation failed exact expansion roundtrip")
    registry[name] = d
    return MappingProxyType(registry)


def frozen_triple_row_sum_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=15 or len(premises)!=3 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise TripleRowSumError("CV013 exact constructed triple-row sum target changed")
    return target


def source_contract():
    return dict(code="CV013",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,actual_row_computation_required=True,complementary_degree_required=True,
        padded_outer_coefficient_required=True,both_sum_values_constructed=True,
        coefficient_order="C*B",new_definition_ids=["ND0418"],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        whole_grid_supplied=False,column_sum_identity=False,natural_convolution_associativity=False,
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def triple_row_sum_source_pins():
    result = triple_grid_source_pins()
    for name,pin in sum_zero_tail_source_pins().items():
        if name in result and result[name]!=pin:
            raise TripleRowSumError("shared source pin disagreement")
        result[name] = pin
    expected = {
        "scripts/sqrt2_power_triple_grid.py":"6fa70f9b7b860a86c41931756c9c2ea1a1b43ca56c20274d147e63dc4b8f7f3d",
        "scripts/sqrt2_power_sum_zero_tail.py":"a4112bbf650aa6dfedf3204463a88d4d82ec3ab9f55948ad54c9423208f7d223",
        ZERO_TAIL_ARCHIVE["path"]:ZERO_TAIL_ARCHIVE["sha256"],
    }
    for name in (*expected,"scripts/sqrt2_power_triple_row_sum.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise TripleRowSumError("triple-row source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _add_bound_right(s):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym,EqTrans,ExistsIntro
    def gap(t):
        equation = EqTrans(EqSym(specialize(t,"add_assoc",*t.terms(("g","a","c")))),CongAdd(t.hyp("gap"),EqRefl(t.term("c"))))
        return ExistsIntro(t.term("g"),equation)
    return introduce(s,("a","b","c"),("bound",),lambda t:
        eliminate(t,t.hyp("bound"),("g",),"gap",gap))


def _row_span(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongS,EqTrans,ExistsIntro
    return introduce(s,("i","j","r"),("index",),lambda t:
        ExistsIntro(t.term("j"),EqTrans(instantiate(Axiom("PA4"),*t.terms(("j","r"))),CongS(t.hyp("index")))))


def _tail_index(s,registry):
    from peano_lab.kernel.proofs import CongS,EqSym,EqTrans
    from peano_lab.kernel.terms import Add,Succ
    def finish(t):
        first,last = Add(Succ(t.term("h")),t.term("r")),Add(t.term("j"),t.term("r"))
        addition = apply(specialize(t,"add_bound_right",Succ(t.term("h")),*t.terms(("j","r"))),t.hyp("bound"))
        raised = apply(specialize(t,"succ_le_succ",first,last),addition)
        inner = EqTrans(specialize(t,"add_succ_left",*t.terms(("h","r"))),
            EqTrans(CongS(specialize(t,"add_comm",*t.terms(("h","r")))),EqSym(specialize(t,"add_succ_left",*t.terms(("r","h"))))))
        left = _subst(t,registry,"Le(slot,S (j+r))",CongS(inner),raised)
        return _subst(t,registry,"Le(S (S r+h),slot)",CongS(t.hyp("index")),left)
    return introduce(s,("i","j","r","h"),("index","bound"),finish)


def _cell_match(s,registry):
    from sqrt2_power_quadratic_height import _additive_equal,_chain
    from peano_lab.kernel.proofs import AndElimL,BotElim,CongAdd,CongMul,EqRefl,EqSym,EqTrans,ExistsIntro,OrElim
    from peano_lab.kernel.terms import Add
    def diagonal(t):
        def inside(u):
            def actual(v):
                complementary = apply(specialize(v,"add_left_cancel",v.term("j"),Add(v.term("d"),v.term("l")),v.term("r")),
                    EqTrans(field(v.hyp("active"),0,5),EqSym(v.hyp("index"))))
                equal_right = _chain(complementary,EqSym(field(v.hyp("term"),0,4)),specialize(v,"add_comm",*v.terms(("l","k"))))
                same_k = apply(specialize(v,"add_right_cancel",*v.terms(("d","k","l"))),equal_right)
                middle = _subst(v,registry,"BetaZeroExtend(bb,bc,M,slot,y)",same_k,field(v.hyp("active"),2,5))
                first = apply(specialize(v,"padding_unique",*v.terms(A+("j","x","a"))),field(v.hyp("active"),1,5),v.hyp("outer"))
                second = apply(specialize(v,"padding_unique",*v.terms(B+("k","y","b"))),middle,field(v.hyp("term"),2,4))
                third = apply(specialize(v,"padding_unique",*v.terms(C+("l","w","c"))),field(v.hyp("active"),3,5),field(v.hyp("term"),1,4))
                return _chain(field(v.hyp("active"),4,5),CongMul(first,CongMul(second,third)),
                    CongMul(EqRefl(v.term("a")),specialize(v,"mul_comm",*v.terms(("b","c")))),
                    CongMul(EqRefl(v.term("a")),EqSym(field(v.hyp("term"),3,4))))
            return eliminate(u,u.hyp("inside"),("d","x","y","w"),"active",actual)
        def outside(u):
            k,j,l = u.terms(("k","j","l"))
            equation = _chain(_additive_equal(u,Add(k,Add(j,l)),Add(j,Add(l,k))),
                CongAdd(EqRefl(j),field(u.hyp("term"),0,4)),u.hyp("index"))
            bound = ExistsIntro(k,equation)
            return BotElim(apply(specialize(u,"lt_not_le",u.term("i"),Add(j,l)),AndElimL(u.hyp("outside")),bound))
        return OrElim(t.hyp("cell"),inside(t.hypothesis("inside")),outside(t.hypothesis("outside")))
    return introduce(s,P+("i","j","r","a","l","t","z"),("index","outer","diagonal","cell"),lambda t:
        eliminate(t,t.hyp("diagonal"),("k","c","b"),"term",diagonal))


def _cell_zero(s):
    from peano_lab.kernel.proofs import AndElimR,BotElim,EqSym,EqTrans,ExistsIntro,OrElim
    from peano_lab.kernel.terms import Add
    def finish(t):
        def inside(u):
            def actual(v):
                same = apply(specialize(v,"add_left_cancel",v.term("j"),Add(v.term("k"),v.term("l")),v.term("r")),
                    EqTrans(field(v.hyp("active"),0,5),EqSym(v.hyp("index"))))
                bound = ExistsIntro(v.term("k"),same)
                return BotElim(apply(specialize(v,"lt_not_le",*v.terms(("r","l"))),v.hyp("past"),bound))
            return eliminate(u,u.hyp("inside"),("k","a","b","c"),"active",actual)
        return OrElim(t.hyp("cell"),inside(t.hypothesis("inside")),AndElimR(t.hypothesis("outside").hyp("outside")))
    return introduce(s,P+("i","j","r","l","z"),("index","past","cell"),finish)


def _row_rule(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,Axiom,CongAdd,CongS,EqRefl,EqSym,EqTrans,ExistsIntro
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def diagonal(t):
        def initial_sum(u):
            def zero_entry(v):
                def decoded(w):
                    position = Add(Succ(w.term("r")),w.term("h"))
                    bound = apply(specialize(w,"tail_index",*w.terms(("i","j","r","h"))),w.hyp("index"),w.hyp("bound"))
                    actual = apply(specialize(w,"row",position,w.term("v")),bound,w.hyp("entry"))
                    past = ExistsIntro(w.term("h"),specialize(w,"add_comm",w.term("h"),Succ(w.term("r"))))
                    zero = apply(specialize(w,"cell_zero",*w.terms(P+("i","j","r")),position,w.term("v")),w.hyp("index"),past,actual)
                    return _subst(w,registry,"BetaAt(ub,uc,S r+h,slot)",zero,w.hyp("entry"))
                position = Add(Succ(v.term("r")),v.term("h"))
                return eliminate(v,specialize(v,"beta_exists",*v.terms(("ub","uc")),position),("v",),"entry",decoded)
            zeros = introduce(u,("h",),("bound",),zero_entry)
            extended = apply(specialize(u,"zero_tail",*u.terms(("ub","uc")),Succ(u.term("r")),*u.terms(("j","u"))),u.hyp("short_sum"),zeros)
            length = _chain(specialize(u,"add_succ_left",*u.terms(("r","j"))),
                CongS(specialize(u,"add_comm",*u.terms(("r","j")))),CongS(u.hyp("index")))
            extended = _subst(u,registry,"Sum(ub,uc,slot,u)",length,extended)
            same_total = apply(specialize(u,"sum_unique",*u.terms(("ub","uc")),Succ(u.term("i")),*u.terms(("s","u"))),u.hyp("sum"),extended)
            def pointwise(v):
                span = apply(specialize(v,"row_span",*v.terms(("i","j","r"))),v.hyp("index"))
                bound = apply(specialize(v,"le_trans",Succ(v.term("l")),Succ(v.term("r")),Succ(v.term("i"))),v.hyp("bound"),span)
                actual = apply(specialize(v,"row",*v.terms(("l","z"))),bound,v.hyp("third"))
                term = apply(specialize(v,"diagonal_entry",*v.terms(C+B+("r","db","dc")),Succ(v.term("r")),*v.terms(("l","v"))),
                    AndElimL(v.hyp("diagonal")),v.hyp("bound"),v.hyp("first"))
                match = apply(specialize(v,"cell_match",*v.terms(P+("i","j","r","a","l","v","z"))),v.hyp("index"),v.hyp("outer"),term,actual)
                product = Mul(v.term("a"),v.term("v"))
                remove_zero = EqTrans(CongAdd(EqRefl(product),specialize(v,"mul_zero_left",v.term("w"))),instantiate(Axiom("PA3"),product))
                return _chain(specialize(v,"one_mul",v.term("z")),match,EqSym(remove_zero))
            relation = introduce(u,("l","v","w","z"),("bound","first","second","third"),pointwise)
            linear = apply(specialize(u,"linearity",u.term("a"),Zero(),Succ(Zero()),
                *u.terms(("db","dc","db","dc","ub","uc")),Succ(u.term("r")),*u.terms(("t","t","u"))),
                AndElimR(u.hyp("diagonal")),AndElimR(u.hyp("diagonal")),u.hyp("short_sum"),relation)
            product = Mul(u.term("a"),u.term("t"))
            short_value = _chain(EqSym(specialize(u,"one_mul",u.term("u"))),linear,
                CongAdd(EqRefl(product),specialize(u,"mul_zero_left",u.term("t"))),instantiate(Axiom("PA3"),product))
            return EqTrans(same_total,short_value)
        return eliminate(t,specialize(t,"sum_exists",*t.terms(("ub","uc")),Succ(t.term("r"))),("u",),"short_sum",initial_sum)
    return introduce(s,PARAMETERS+("t","s"),("index","outer","row","coefficient","sum"),lambda t:
        eliminate(t,t.hyp("coefficient"),("db","dc"),"diagonal",diagonal))


def _root(s):
    from peano_lab.kernel.terms import Succ
    def finish(t):
        equality = apply(specialize(t,"row_rule",*t.terms(PARAMETERS+("t","s"))),
            t.hyp("index"),t.hyp("outer"),t.hyp("row"),t.hyp("coefficient"),t.hyp("sum"))
        return witness(t.terms(("t","s")),conjunction(t.hyp("coefficient"),t.hyp("sum"),equality))
    return introduce(s,PARAMETERS,("index","outer","row"),lambda t:
        eliminate(t,specialize(t,"coefficient_exists",*t.terms(C+B+("r",))),("t",),"coefficient",lambda u:
            eliminate(u,specialize(u,"sum_exists",*u.terms(("ub","uc")),Succ(u.term("i"))),("s",),"sum",finish)))


@dataclass(frozen=True)
class TripleRowSumCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_triple_row_sum(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise TripleRowSumError("expected unchanged BinaryDAGLimits")
    before = triple_row_sum_source_pins()
    registry,target = definition_registry(),frozen_triple_row_sum_target()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise TripleRowSumError("exact triple-row helper target changed")
    formulas["CV013"] = target
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    for pin in (CONVOLUTION_ARCHIVE,ZERO_TAIL_ARCHIVE):
        original = read_archive(pin)
        remap = {}
        for old,r in enumerate(original):
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise TripleRowSumError("actual ancestor ordered dependencies changed")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise TripleRowSumError("merged ancestor body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        for name,source in ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=registry))
            matches = [i for i,r in enumerate(original) if r[1]==formula]
            if len(matches)>1:
                raise TripleRowSumError("ambiguous actual endpoint: "+name)
            if matches:
                if name in endpoints and endpoints[name]!=remap[matches[0]]:
                    raise TripleRowSumError("shared actual endpoint bodies disagree")
                endpoints[name] = remap[matches[0]]
        del original,remap
        gc.collect()
    if endpoints.keys()!=ENDPOINT_SOURCES.keys():
        raise TripleRowSumError("missing actual triple-row ancestor endpoint")
    ancestor_count = len(rows)
    factories = {"add_bound_right":_add_bound_right,"row_span":_row_span,
        "tail_index":lambda s:_tail_index(s,registry),"cell_match":lambda s:_cell_match(s,registry),
        "cell_zero":_cell_zero,"row_rule":lambda s:_row_rule(s,registry),"CV013":_root}
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise TripleRowSumError("triple-row aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in dependencies],encode_proof(body)])
    reached,pending = set(),[len(rows)-1]
    while pending:
        old = pending.pop()
        if old not in reached:
            reached.add(old)
            pending.extend(rows[old][2])
    retained = tuple(sorted(reached))
    remap = {old:new for new,old in enumerate(retained)}
    ancestors = tuple(old for old in retained if old<ancestor_count)
    ancestor_total = sum(_inert_metrics(rows[old][3],limits)[0] for old in ancestors)
    helper_indices = {name:remap[endpoints[name]] for name in HELPER_DEPENDENCIES}
    rows = [[rows[old][0],rows[old][1],[remap[d] for d in rows[old][2]],rows[old][3]] for old in retained]
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise TripleRowSumError("triple-row canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise TripleRowSumError("decoded triple-row target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or triple_row_sum_source_pins()!=before:
        raise TripleRowSumError("triple-row target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,actual_triple_row_sum_identity=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        convolution_archive=dict(CONVOLUTION_ARCHIVE),zero_tail_archive=dict(ZERO_TAIL_ARCHIVE),
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),helper_bundle_indices=helper_indices,
        new_induction_count=0,ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return TripleRowSumCertificate(target,bundle,payload,receipt,deepest,provenance)
