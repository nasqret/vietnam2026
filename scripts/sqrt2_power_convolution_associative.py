"""CV014: constructed natural convolution associativity below a shared width.

The actual triple grid and finite Fubini provide a common total. The proved
row rule, explicit transposition and affine-address arithmetic identify both
nested products. W>i is an explicit premise, not a hidden truncation axiom.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256

from sqrt2_power_triple_row_sum import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,_inert_metrics,read_archive,definition_registry,
    triple_row_sum_source_pins,P,A,B,C,CONVOLUTION_ARCHIVE,_subst,
    HELPER_SOURCES as ROW_HELPERS,
)
from sqrt2_power_triple_grid import NAMED_SOURCE as GRID_SOURCE
from sqrt2_power_natural_fubini import NAMED_SOURCE as FUBINI_SOURCE
from sqrt2_power_sum_splitting import FUBINI_ARCHIVE
from sqrt2_power_convolution_commutative import HELPER_SOURCES as COMM_HELPERS
from sqrt2_power_euler_product import coefficient

SCHEMA = "sqrt2-power-convolution-associative-v1"
GRID_ARCHIVE = dict(case="CV012",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-triple-grid-v1/generation-process.json.gz",
    bytes=20092,sha256="ffb6aa36d8c0d3309167792db1c6bc399604c762fdca263e2a4b59bf0a0afc9e",
    raw_bytes=300246,raw_sha256="74fe2191414c807cd9ef6d1bf371e0ff0c87343d1cbae8d85edea8ddc24c5a57",
    bundle_bytes=178964,bundle_sha256="77fdbd64eb98decdc1a310bb553b5c8bc5e675e5cdb1e252438f0538dad2b646",
    nodes=110,root=109,target_ast_sha256="ac50bc2ab4e67d47f7b5eb88eead79f814654ca2b863006b38df9015214803c2")
ROW_ARCHIVE = dict(case="CV013",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-triple-row-sum-v1/generation-process.json.gz",
    bytes=28223,sha256="38ef4cbd4901f7c560361bee05c7b79ed9723f3b339ca8dcc7371128daba42b8",
    raw_bytes=545492,raw_sha256="b48e41490b5ac0a32c72344056edc3489bbc6470d341102cd2ed99be01876c24",
    bundle_bytes=329542,bundle_sha256="39db448c4be4a9bee828be1d616a9fd4065555cd9fa7416c5ee57eb4019e41e7",
    nodes=139,root=138,target_ast_sha256="835ed495fdd7f286cacdd0a59c544660f11c1fac47fb70eac20dad374b982a57")
COMM_ARCHIVE = dict(case="CV010",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-commutative-v1/generation-process.json.gz",
    bytes=25857,sha256="9692df33332a534be235cede982b6883c569e3357d3a75297bc890ed89bc839b",
    raw_bytes=505662,raw_sha256="95acbc19c77e2daf6efe0d6ec0e5f6af61a082da3b83a0b4ee7cb314ccebcb64",
    bundle_bytes=305383,bundle_sha256="35c67ca650e7222ffedb065f157777f40bd88d06acfb746314dcb8d6c6afb093",
    nodes=133,root=132,target_ast_sha256="3e62febc17b41a970070ca88e057e05ef7888d821a65f9019ac15bfb8fc5a825")
ARCHIVES = (CONVOLUTION_ARCHIVE,GRID_ARCHIVE,FUBINI_ARCHIVE,COMM_ARCHIVE,ROW_ARCHIVE)
AB,BC = ("pb","pc","W"),("qb","qc","W")


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def prefix(left,right,codes):
    return "NatConvolutionPrefix("+",".join(left+right+codes+("W",))+")"


def grid():
    return "NatTripleGrid("+",".join(P+("i","gb","gc"))+")"


def cell(parameters=P,j="j",l="l",z="z"):
    return "NatTripleCell("+",".join(parameters+("i",j,l,z))+")"


def row_prefix(parameters=P):
    return "NatTripleRowPrefix("+",".join(parameters+("i","j","ub","uc"))+")"


def affine_rows(axis,codes=("rb","rc")):
    strides = ("S i","1") if axis=="row" else ("1","S i")
    return "NatAffineRowSums("+",".join(("gb","gc","0")+strides+("S i","S i")+codes)+")"


PREFIX_AB,PREFIX_BC = prefix(A,B,AB[:2]),prefix(B,C,BC[:2])
RESULT = coefficient(AB,C,"i","z")+" /\\ "+coefficient(A,BC,"i","z")
NAMED_SOURCE = forall(P+("i","W"),"Lt(i,W) -> exists pb pc qb qc z. "+PREFIX_AB+" /\\ ("+PREFIX_BC+" /\\ ("+RESULT+"))")
TARGET_SHA256 = "a455e5f4420f28921f898952ebc74012686b69749b15192af32727495f22413b"
HELPER_SOURCES = {
    "coefficient_swap":"forall ab ac L bb bc M i n. "+coefficient(A,B,"i","n")+" -> "+coefficient(B,A,"i","n"),
    "complement":"forall i j. Lt(j,S i) -> exists r. j+r=i",
    "cell_transpose":forall(P+("i","j","l","z"),cell()+" -> "+cell(C+B+A,"l","j")),
    "grid_entry":forall(P+("i","gb","gc","j","l","z"),grid()+" -> Lt(j,S i) -> Lt(l,S i) -> BetaAt(gb,gc,(S i)*j+l,z) -> "+cell()),
    "row_from_slice":forall(P+("i","gb","gc","j","ub","uc"),grid()+" -> Lt(j,S i) -> NatAffineSlice(gb,gc,0+(S i)*j,1,ub,uc,S i) -> "+row_prefix()),
    "column_from_slice":forall(P+("i","gb","gc","j","ub","uc"),grid()+" -> Lt(j,S i) -> NatAffineSlice(gb,gc,0+1*j,S i,ub,uc,S i) -> "+row_prefix(C+B+A)),
    "diagonal_rows":forall(P+("i","W","gb","gc","rb","rc","qb","qc"),"Lt(i,W) -> "+grid()+" -> "+affine_rows("row")+" -> "+PREFIX_BC+
        " -> PolynomialDiagonalPrefix("+",".join(A+BC+("i","rb","rc","S i"))+")"),
    "diagonal_columns":forall(P+("i","W","gb","gc","rb","rc","pb","pc"),"Lt(i,W) -> "+grid()+" -> "+affine_rows("column")+" -> "+PREFIX_AB+
        " -> PolynomialDiagonalPrefix("+",".join(C+AB+("i","rb","rc","S i"))+")"),
    "associate":forall(P+("i","W","pb","pc","qb","qc"),"Lt(i,W) -> "+PREFIX_AB+" -> "+PREFIX_BC+" -> exists z. "+RESULT),
}
HELPER_TARGET_SHA256 = {
    "coefficient_swap":"e14d891018ad5a8341bc714434869182f7b1cd28c9c5c8d06e75fbfeaa37f2bd",
    "complement":"f96b4b24de8359a8f515f522816c7dedaa5806acc3b3f5cdb90795dcfe76993f",
    "cell_transpose":"9034d509fae0abfae9ce765657636d66b9394678a8f706dcdd18a8788580af7a",
    "grid_entry":"25cafbd2283db9fbbba421bc1d36e610a67b5e18fea495e5634bbdb47dd013cd",
    "row_from_slice":"55fe7cc7dcc15e5d21081a61ae7816f864ca48f5673d09e15be18e3af10e078a",
    "column_from_slice":"f238d44825ae54ff5cbf90443ed90a0e2f25eedbc06c1b9ece613af8b983f053",
    "diagonal_rows":"b6e3b100c0a62e3364c542affebaba842faaf53622845924ff6f51aff3cc68b3",
    "diagonal_columns":"0eb6b363f6b7b0f3ca7ebd12f292d797c06744de957fbcc08f2ebbbb449d8b13",
    "associate":"fca2d61423a494de97bec1562561ae72d0b4feee89a460aae10df1e817a34b06",
}
ENDPOINT_SOURCES = {
    "zero_add":"forall a. 0+a=a",
    "add_comm":"forall a b. a+b=b+a",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "mul_comm":"forall a b. a*b=b*a",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "one_mul":"forall a. 1*a=a",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "padding_exists":"forall b c L i. exists a. BetaZeroExtend(b,c,L,i,a)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "coefficient_exists":"forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)",
    "prefix_exists":"forall ab ac L bb bc M N. exists cb cc. NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N)",
    "prefix_entry":"forall ab ac L bb bc M cb cc N i a. NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N) -> Lt(i,N) -> BetaAt(cb,cc,i,a) -> NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,a)",
    "commute":COMM_HELPERS["commute"],
    "grid_exists":GRID_SOURCE,
    "fubini":FUBINI_SOURCE,
    "row_rule":ROW_HELPERS["row_rule"],
}
HELPER_DEPENDENCIES = {
    "coefficient_swap":("coefficient_exists","commute"),
    "complement":("le_of_succ_le_succ","add_comm"),
    "cell_transpose":("add_comm","add_assoc","mul_comm","mul_assoc"),
    "grid_entry":("beta_unique",),
    "row_from_slice":("grid_entry","zero_add","one_mul"),
    "column_from_slice":("grid_entry","cell_transpose","zero_add","one_mul","add_comm"),
    "diagonal_rows":("complement","padding_exists","beta_exists","succ_le_succ","le_trans","prefix_entry","row_from_slice","row_rule","coefficient_swap"),
    "diagonal_columns":("complement","padding_exists","beta_exists","succ_le_succ","le_trans","prefix_entry","column_from_slice","row_rule"),
    "associate":("grid_exists","fubini","diagonal_rows","diagonal_columns","coefficient_swap"),
    "CV014":("prefix_exists","associate"),
}


class ConvolutionAssociativeError(ValueError):
    """Changed common-width premise, actual dependency body or resource cap."""


def frozen_convolution_associative_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=11 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionAssociativeError("CV014 exact constructed associative target changed")
    return target


def source_contract():
    return dict(code="CV014",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,coefficient_index_below_common_width_required=True,
        both_intermediate_prefixes_constructed=True,common_nested_product_value_constructed=True,
        arbitrary_input_lengths=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def convolution_associative_source_pins():
    result = triple_row_sum_source_pins()
    expected = {
        "scripts/sqrt2_power_triple_row_sum.py":"d0ee57d361f2f714862761de9416595e4520c1abd2597986a3cbef2e39dab345",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_convolution_associative.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionAssociativeError("associative source or actual proof archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _coefficient_swap(s,registry):
    from peano_lab.kernel.proofs import EqSym
    def finish(t):
        same = apply(specialize(t,"commute",*t.terms(A+B+("i","n","m"))),t.hyp("input"),t.hyp("other"))
        return _subst(t,registry,coefficient(B,A,"i","slot"),EqSym(same),t.hyp("other"))
    return introduce(s,A+B+("i","n"),("input",),lambda t:
        eliminate(t,specialize(t,"coefficient_exists",*t.terms(B+A+("i",))),("m",),"other",finish))


def _complement(s):
    from peano_lab.kernel.proofs import EqTrans
    return introduce(s,("i","j"),("bound",),lambda t:
        eliminate(t,apply(specialize(t,"le_of_succ_le_succ",*t.terms(("j","i"))),t.hyp("bound")),("r",),"gap",lambda u:
            witness((u.term("r"),),EqTrans(specialize(u,"add_comm",*u.terms(("j","r"))),u.hyp("gap")))))


def _cell_transpose(s,registry):
    from sqrt2_power_quadratic_height import _additive_equal,_chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,CongMul,EqRefl,EqSym,EqTrans,OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        def inside(u):
            def decoded(v):
                j,k,l = v.terms(("j","k","l"))
                index = EqTrans(_additive_equal(v,Add(l,Add(k,j)),Add(j,Add(k,l))),field(v.hyp("active"),0,5))
                a,b,c = v.terms(("a","b","c"))
                product = _chain(field(v.hyp("active"),4,5),EqSym(specialize(v,"mul_assoc",a,b,c)),
                    specialize(v,"mul_comm",Mul(a,b),c),CongMul(EqRefl(c),specialize(v,"mul_comm",a,b)))
                return OrIntroL(witness(v.terms(("k","c","b","a")),conjunction(index,
                    field(v.hyp("active"),3,5),field(v.hyp("active"),2,5),field(v.hyp("active"),1,5),product)))
            return eliminate(u,u.hyp("inside"),("k","a","b","c"),"active",decoded)
        def outside(u):
            bound = _subst(u,registry,"Lt(i,slot)",specialize(u,"add_comm",*u.terms(("j","l"))),AndElimL(u.hyp("outside")))
            return OrIntroR(AndIntro(bound,AndElimR(u.hyp("outside"))))
        return OrElim(t.hyp("cell"),inside(t.hypothesis("inside")),outside(t.hypothesis("outside")))
    return introduce(s,P+("i","j","l","z"),("cell",),finish)


def _grid_entry(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Mul,Succ
    def decoded(t):
        index = Add(Mul(Succ(t.term("i")),t.term("j")),t.term("l"))
        same = apply(specialize(t,"beta_unique",*t.terms(("gb","gc")),index,*t.terms(("a","z"))),AndElimL(t.hyp("entry")),t.hyp("value"))
        return _subst(t,registry,cell(z="slot"),same,AndElimR(t.hyp("entry")))
    return introduce(s,P+("i","gb","gc","j","l","z"),("grid","row","column","value"),lambda t:
        eliminate(t,apply(specialize(t,"grid",*t.terms(("j","l"))),t.hyp("row"),t.hyp("column")),("a",),"entry",decoded))


def _from_slice(s,registry,axis):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqTrans
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def entry(t):
        source = apply(specialize(t,"slice",*t.terms(("l","z"))),t.hyp("bound"),t.hyp("value"))
        if axis=="row":
            coordinate = CongAdd(specialize(t,"zero_add",Mul(Succ(t.term("i")),t.term("j"))),specialize(t,"one_mul",t.term("l")))
            source = _subst(t,registry,"BetaAt(gb,gc,slot,z)",coordinate,source)
            return apply(specialize(t,"grid_entry",*t.terms(P+("i","gb","gc","j","l","z"))),t.hyp("grid"),t.hyp("fixed"),t.hyp("bound"),source)
        offset = EqTrans(CongAdd(EqRefl(Zero()),specialize(t,"one_mul",t.term("j"))),specialize(t,"zero_add",t.term("j")))
        variable = Mul(Succ(t.term("i")),t.term("l"))
        coordinate = EqTrans(CongAdd(offset,EqRefl(variable)),specialize(t,"add_comm",t.term("j"),variable))
        source = _subst(t,registry,"BetaAt(gb,gc,slot,z)",coordinate,source)
        actual = apply(specialize(t,"grid_entry",*t.terms(P+("i","gb","gc","l","j","z"))),t.hyp("grid"),t.hyp("bound"),t.hyp("fixed"),source)
        return apply(specialize(t,"cell_transpose",*t.terms(P+("i","l","j","z"))),actual)
    return introduce(s,P+("i","gb","gc","j","ub","uc"),("grid","fixed","slice"),lambda t:
        introduce(t,("l","z"),("bound","value"),entry))


def _diagonal(s,registry,axis):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,ExistsIntro,OrIntroL
    from peano_lab.kernel.terms import Succ
    outer = A if axis=="row" else C
    inner = B+C if axis=="row" else A+B
    codes = BC[:2] if axis=="row" else AB[:2]
    row_parameters = P if axis=="row" else C+B+A
    def entry(t):
        def total(u):
            def degree(v):
                def outer_value(w):
                    def inner_value(x):
                        def slice_data(y):
                            below_i = ExistsIntro(y.term("j"),y.hyp("index"))
                            span = apply(specialize(y,"succ_le_succ",*y.terms(("r","i"))),below_i)
                            bound = apply(specialize(y,"le_trans",Succ(y.term("r")),Succ(y.term("i")),y.term("W")),span,y.hyp("width"))
                            coefficient_proof = apply(specialize(y,"prefix_entry",*y.terms(inner+codes+("W","r","b"))),y.hyp("inner"),bound,y.hyp("inner_value"))
                            if axis=="row":
                                coefficient_proof = apply(specialize(y,"coefficient_swap",*y.terms(inner+("r","b"))),coefficient_proof)
                            actual_row = apply(specialize(y,axis+"_from_slice",*y.terms(P+("i","gb","gc","j","ub","uc"))),y.hyp("grid"),y.hyp("bound"),AndElimL(y.hyp("slice_data")))
                            identity = apply(specialize(y,"row_rule",*y.terms(row_parameters+("i","j","r","a","ub","uc","b","s"))),
                                y.hyp("index"),y.hyp("outer"),actual_row,coefficient_proof,AndElimR(y.hyp("slice_data")))
                            padded = OrIntroL(AndIntro(bound,y.hyp("inner_value")))
                            term = witness(y.terms(("r","a","b")),conjunction(y.hyp("index"),y.hyp("outer"),padded,identity))
                            return witness((y.term("s"),),AndIntro(AndElimL(y.hyp("entry")),term))
                        return eliminate(x,AndElimR(x.hyp("entry")),("ub","uc"),"slice_data",slice_data)
                    return eliminate(w,specialize(w,"beta_exists",*w.terms(codes+("r",))),("b",),"inner_value",inner_value)
                return eliminate(v,specialize(v,"padding_exists",*v.terms(outer+("j",))),("a",),"outer",outer_value)
            return eliminate(u,apply(specialize(u,"complement",*u.terms(("i","j"))),u.hyp("bound")),("r",),"index",degree)
        return eliminate(t,apply(specialize(t,"rows",t.term("j")),t.hyp("bound")),("s",),"entry",total)
    return introduce(s,P+("i","W","gb","gc","rb","rc")+codes,("width","grid","rows","inner"),lambda t:
        introduce(t,("j",),("bound",),entry))


def _associate(s):
    from peano_lab.kernel.proofs import AndIntro
    from peano_lab.kernel.terms import Succ,Zero
    def grid_data(t):
        def summed(u):
            row_diagonal = apply(specialize(u,"diagonal_rows",*u.terms(P+("i","W","gb","gc","rb","rc","qb","qc"))),
                u.hyp("width"),u.hyp("grid"),field(u.hyp("totals"),0,4),u.hyp("right"))
            column_diagonal = apply(specialize(u,"diagonal_columns",*u.terms(P+("i","W","gb","gc","db","dc","pb","pc"))),
                u.hyp("width"),u.hyp("grid"),field(u.hyp("totals"),1,4),u.hyp("left"))
            right = witness(u.terms(("rb","rc")),AndIntro(row_diagonal,field(u.hyp("totals"),2,4)))
            left = witness(u.terms(("db","dc")),AndIntro(column_diagonal,field(u.hyp("totals"),3,4)))
            left = apply(specialize(u,"coefficient_swap",*u.terms(C+AB+("i","z"))),left)
            return witness((u.term("z"),),AndIntro(left,right))
        H = Succ(t.term("i"))
        actual = specialize(t,"fubini",*t.terms(("gb","gc")),Zero(),H,Succ(Zero()),H,H)
        return eliminate(t,actual,("rb","rc","db","dc","z"),"totals",summed)
    return introduce(s,P+("i","W","pb","pc","qb","qc"),("width","left","right"),lambda t:
        eliminate(t,specialize(t,"grid_exists",*t.terms(P+("i",))),("gb","gc"),"grid",grid_data))


def _root(s):
    def finish(t):
        return eliminate(t,apply(specialize(t,"associate",*t.terms(P+("i","W","pb","pc","qb","qc"))),t.hyp("width"),t.hyp("left"),t.hyp("right")),("z",),"same",lambda u:
            witness(u.terms(("pb","pc","qb","qc","z")),conjunction(u.hyp("left"),u.hyp("right"),u.hyp("same"))))
    return introduce(s,P+("i","W"),("width",),lambda t:
        eliminate(t,specialize(t,"prefix_exists",*t.terms(A+B+("W",))),("pb","pc"),"left",lambda u:
            eliminate(u,specialize(u,"prefix_exists",*u.terms(B+C+("W",))),("qb","qc"),"right",finish)))


@dataclass(frozen=True)
class ConvolutionAssociativeCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_convolution_associative(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise ConvolutionAssociativeError("expected unchanged BinaryDAGLimits")
    before = convolution_associative_source_pins()
    registry,target = definition_registry(),frozen_convolution_associative_target()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise ConvolutionAssociativeError("exact associative helper target changed")
    formulas["CV014"] = target
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    for pin in ARCHIVES:
        original = read_archive(pin)
        remap = {}
        for old,r in enumerate(original):
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise ConvolutionAssociativeError("actual ancestor ordered dependencies changed")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise ConvolutionAssociativeError("merged ancestor body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        for name,source in ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=registry))
            matches = [i for i,r in enumerate(original) if r[1]==formula]
            if len(matches)>1:
                raise ConvolutionAssociativeError("ambiguous actual endpoint: "+name)
            if matches:
                if name in endpoints and endpoints[name]!=remap[matches[0]]:
                    raise ConvolutionAssociativeError("shared actual endpoint bodies disagree")
                endpoints[name] = remap[matches[0]]
        del original,remap
        gc.collect()
    if endpoints.keys()!=ENDPOINT_SOURCES.keys():
        raise ConvolutionAssociativeError("missing actual associative ancestor endpoint")
    ancestor_count = len(rows)
    factories = {
        "coefficient_swap":lambda s:_coefficient_swap(s,registry),"complement":_complement,
        "cell_transpose":lambda s:_cell_transpose(s,registry),"grid_entry":lambda s:_grid_entry(s,registry),
        "row_from_slice":lambda s:_from_slice(s,registry,"row"),
        "column_from_slice":lambda s:_from_slice(s,registry,"column"),
        "diagonal_rows":lambda s:_diagonal(s,registry,"row"),
        "diagonal_columns":lambda s:_diagonal(s,registry,"column"),
        "associate":_associate,"CV014":_root,
    }
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise ConvolutionAssociativeError("associative aggregate body/node bound exceeded")
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
        raise ConvolutionAssociativeError("associative canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise ConvolutionAssociativeError("decoded associative target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or convolution_associative_source_pins()!=before:
        raise ConvolutionAssociativeError("associative target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,actual_natural_convolution_associativity=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        actual_archives=[dict(pin) for pin in ARCHIVES],
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),helper_bundle_indices=helper_indices,
        new_induction_count=0,ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return ConvolutionAssociativeCertificate(target,bundle,payload,receipt,deepest,provenance)
