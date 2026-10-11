"""CV047: one actual Cauchy grid with all full-length row and column sums.

Construct N=L+M and a grid of side N+1, but sum precisely N entries in
each direction. Columns at j<L use the complete-span theorem; all other
columns are proved zero. A single actual right-input sum is shared throughout.
Finite Fubini and the final product-sum identity are subsequent obligations.
"""
from hashlib import sha256

from sqrt2_power_cauchy_column_sum import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,P,cell,definition_registry,cauchy_column_sum_source_pins,
    NAMED_SOURCE as COLUMN_SOURCE,ROW_ARCHIVE,CONVOLUTION_ARCHIVE,_subst,
)
from sqrt2_power_cauchy_row_sum import HELPER_SOURCES as ROW_HELPERS,GRID_SOURCE,FUBINI_HELPERS
from sqrt2_power_sum_zero_tail import ZERO_SUM_SOURCE
from sqrt2_power_euler_product import coefficient
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-cauchy-grid-sums-v1"
A,B = P[:3],P[3:]
FIXED = P+("N","gb","gc")
GRID = "NatCauchyGrid("+",".join(FIXED)+")"


def column(length="N"):
    return "NatCauchyColumn("+",".join(P+("j","ub","uc",length))+")"


def pad(value="a"):
    return "BetaZeroExtend(ab,ac,L,j,"+value+")"


SLICE = "NatAffineSlice(gb,gc,j,S N,ub,uc,N)"
ROW_RESULT = coefficient(A,B,"k","u")+" /\\ NatAffineSum(gb,gc,(S N)*k,1,N,u)"
COL_RESULT = "NatAffineSum(gb,gc,j,S N,N,y) /\\ y=a*x"
ALL_ROWS = "forall k. Lt(k,N) -> exists u. "+ROW_RESULT
ALL_COLUMNS = "forall j a. Lt(j,N) -> "+pad()+" -> exists y. "+COL_RESULT
DATA = GRID+" /\\ (Sum(bb,bc,M,x) /\\ (("+ALL_ROWS+") /\\ ("+ALL_COLUMNS+")))"
NAMED_SOURCE = "forall "+" ".join(P)+". exists N gb gc x. N=L+M /\\ ("+DATA+")"
TARGET_SHA256 = "f9641b30ca39287a97a195a21f4f444b93c513dc143c2f42166caff02b8f76a0"
HELPER_SOURCES = {
    "cell_zero_left":"forall "+" ".join(P+("k","j","z"))+". "+pad("0")+" -> "+cell()+" -> z=0",
    "zero_column":"forall "+" ".join(P+("j","ub","uc","T"))+". "+pad("0")+" -> "+column("T")+" -> Sum(ub,uc,T,0)",
    "span":"forall L M N j. N=L+M -> Lt(j,L) -> exists q. (j+M)+q=N",
    "column_slice":"forall "+" ".join(FIXED+("j","ub","uc"))+". "+GRID+" -> Lt(j,N) -> "+SLICE+" -> "+column(),
    "row_slice":"forall "+" ".join(FIXED+("k",))+". "+GRID+" -> Lt(k,N) -> exists u. "+ROW_RESULT,
    "column_value":"forall "+" ".join(FIXED+("j","a","x"))+". N=L+M -> "+GRID+" -> Lt(j,N) -> "+pad()+" -> Sum(bb,bc,M,x) -> exists y. "+COL_RESULT,
    "construct":"forall "+" ".join(P+("N",))+". N=L+M -> exists gb gc x. "+DATA,
}
HELPER_TARGET_SHA256 = {
    "cell_zero_left":"9d922319074049b849de5cf990995578ea7134fca9d7f438a5f091945cb72d30",
    "zero_column":"135161f84ea5e7b7f12ae49ba81859a2f3fa2b3339c6aeb6a4bf5375c0689a20",
    "span":"5bcf38314c425db91b7785656072a12679ad80932e29d5687f6ac2f52a1dd875",
    "column_slice":"e1a8caf9a9b4c10f9b1f5084a0710307564dfbaf5b694fcdcec8a29df731ad52",
    "row_slice":"867ddf30f8f518a688f291633df2bd961328b50559fadeb092f52df19134fe91",
    "column_value":"f70541ba4f2a9e61ededaaca526199df3da59b366a01cd18dee7c39583f78cc5",
    "construct":"249b8100e9ec8fbf25db7981d1ddde5efb13dd30e45d25271cfccd79246b3f02",
}
COLUMN_ARCHIVE = dict(case="CV046",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-cauchy-column-sum-v1/generation-process.json.gz",
    bytes=27556,sha256="5aa59b1bec74010bffbbd59b13bda5f07f2941ac30da9ec19353dee11d2d8241",
    raw_bytes=512834,raw_sha256="1e0f6deb3365d02bb997768c36c47b33cebd5cbbe8dcd1b28e4b14bdbf3dca9d",
    bundle_bytes=307670,bundle_sha256="51a97eb9d305b9d355bd3f737745a5fb8736bf7c9d3423149e3f209882f7b742",
    nodes=133,root=132,target_ast_sha256="94eff8a4d0a0b19ee9a9c9a63604deabe5c06331fd7e9e1fd64593a4026f0b4f")
ARCHIVES = (COLUMN_ARCHIVE,ROW_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a","add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "add_succ_left":"forall a b. S a+b=S (a+b)",
    "one_mul":"forall a. 1*a=a","mul_zero_left":"forall a. 0*a=0",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "padding_unique":"forall b c L i a d. BetaZeroExtend(b,c,L,i,a) -> BetaZeroExtend(b,c,L,i,d) -> a=d",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "sum_unique":"forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m",
    "zero_sum":ZERO_SUM_SOURCE,"slice_exists":FUBINI_HELPERS["slice_exists"],
    "row_total":ROW_HELPERS["row_total"],"grid_exists":GRID_SOURCE,"column_total":COLUMN_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(zero_sum="CV046",slice_exists="CV045",row_total="CV045",grid_exists="CV045",column_total="CV046")
HELPER_DEPENDENCIES = {
    "cell_zero_left":("padding_unique","mul_zero_left"),
    "zero_column":("sum_exists","zero_sum","cell_zero_left"),
    "span":("add_comm","add_assoc","add_succ_left"),
    "column_slice":("add_comm","le_succ"),
    "row_slice":("slice_exists","one_mul","le_succ","row_total"),
    "column_value":("slice_exists","column_slice","span","column_total","sum_unique","zero_column","mul_zero_left"),
    "construct":("grid_exists","sum_exists","row_slice","column_value"),
    "CV047":("construct",),
}


class CauchyGridSumsError(ValueError):
    """Changed actual shared grid, summation width or zero-column case."""


def frozen_cauchy_grid_sums_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=6 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CauchyGridSumsError("CV047 exact constructed shared-grid sums changed")
    return target


def source_contract():
    return dict(code="CV047",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_common_grid_and_sum_witnesses_constructed=True,
        all_length_L_plus_M_row_and_column_sums_identified=True,
        shared_actual_right_input_sum=True,outside_left_support_columns_proved_zero=True,
        empty_inputs_allowed=True,grid_width="S N",summation_width="N",constructed_length="L+M",
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",full_convolution_sum_product=False,
        full_convolution_evaluation=False,analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def cauchy_grid_sums_source_pins():
    result = cauchy_column_sum_source_pins()
    expected = {"scripts/sqrt2_power_cauchy_column_sum.py":"da734d004dc74ba68409b25ebe03ff6ab395e7c0e68c8fa0e73b44fae4a6d018",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_cauchy_grid_sums.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CauchyGridSumsError("shared-grid sum source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _cell_zero_left(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimR,CongMul,EqRefl,OrElim
    from peano_lab.kernel.terms import Zero
    def finish(t):
        def decoded(u):
            azero = apply(specialize(u,"padding_unique",*u.terms(("ab","ac","L","j","a")),Zero()),field(u.hyp("term"),1,4),u.hyp("pad"))
            return _chain(field(u.hyp("term"),3,4),CongMul(azero,EqRefl(u.term("b"))),specialize(u,"mul_zero_left",u.term("b")))
        yes = t.hypothesis("inside")
        return OrElim(t.hyp("cell"),eliminate(yes,yes.hyp("inside"),("r","a","b"),"term",decoded),
            AndElimR(t.hypothesis("outside").hyp("outside")))
    return introduce(s,P+("k","j","z"),("pad","cell"),finish)


def _zero_column(s,registry):
    def chosen(t):
        def pointwise(u):
            data = apply(specialize(u,"column",*u.terms(("k","z"))),u.hyp("bound"),u.hyp("entry"))
            return apply(specialize(u,"cell_zero_left",*u.terms(P+("k","j","z"))),u.hyp("pad"),data)
        zero = apply(specialize(t,"zero_sum",*t.terms(("ub","uc","T","y"))),t.hyp("sum"),
            introduce(t,("k","z"),("bound","entry"),pointwise))
        return _subst(t,registry,"Sum(ub,uc,T,slot)",zero,t.hyp("sum"))
    return introduce(s,P+("j","ub","uc","T"),("pad","column"),lambda t:
        eliminate(t,specialize(t,"sum_exists",*t.terms(("ub","uc","T"))),("y",),"sum",chosen))


def _span(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain,_additive_equal
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongS,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Succ
    def chosen(t):
        j,M,h = t.terms(("j","M","h"))
        index = _chain(instantiate(Axiom("PA4"),Add(j,M),h),
            CongS(_additive_equal(t,Add(Add(j,M),h),Add(Add(h,j),M))),
            EqSym(specialize(t,"add_succ_left",Add(h,j),M)),
            CongAdd(EqSym(instantiate(Axiom("PA4"),h,j)),EqRefl(M)),
            CongAdd(t.hyp("gap"),EqRefl(M)),EqSym(t.hyp("length")))
        return witness((Succ(h),),index)
    return introduce(s,("L","M","N","j"),("length","bound"),lambda t:
        eliminate(t,t.hyp("bound"),("h",),"gap",chosen))


def _column_slice(s,registry):
    from peano_lab.kernel.terms import Mul,Succ
    def chosen(t):
        def entry(u):
            value = apply(specialize(u,"slice",*u.terms(("k","z"))),u.hyp("row_bound"),u.hyp("entry"))
            equal = specialize(u,"add_comm",u.term("j"),Mul(Succ(u.term("N")),u.term("k")))
            actual = _subst(u,registry,"BetaAt(gb,gc,slot,z)",equal,value)
            row_bound = apply(specialize(u,"le_succ",Succ(u.term("k")),u.term("N")),u.hyp("row_bound"))
            col_bound = apply(specialize(u,"le_succ",Succ(u.term("j")),u.term("N")),u.hyp("bound"))
            return apply(specialize(u,"grid",*u.terms(("k","j","z"))),row_bound,col_bound,actual)
        return introduce(t,("k","z"),("row_bound","entry"),entry)
    return introduce(s,FIXED+("j","ub","uc"),("grid","bound","slice"),chosen)


def _row_slice(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,CongAdd,EqRefl
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def chosen(t):
        def pointwise(u):
            entry = apply(specialize(u,"slice",*u.terms(("j","z"))),u.hyp("index"),u.hyp("entry"))
            equal = CongAdd(EqRefl(Mul(Succ(u.term("N")),u.term("k"))),specialize(u,"one_mul",u.term("j")))
            actual = _subst(u,registry,"BetaAt(gb,gc,slot,z)",equal,entry)
            row_bound = apply(specialize(u,"le_succ",Succ(u.term("k")),u.term("N")),u.hyp("bound"))
            col_bound = apply(specialize(u,"le_succ",Succ(u.term("j")),u.term("N")),u.hyp("index"))
            return apply(specialize(u,"grid",*u.terms(("k","j","z"))),row_bound,col_bound,actual)
        row = introduce(t,("j","z"),("index","entry"),pointwise)
        result = apply(specialize(t,"row_total",*t.terms(P+("k","ub","uc","N"))),t.hyp("bound"),row)
        return eliminate(t,result,("u",),"data",lambda v:witness((v.term("u"),),AndIntro(
            AndElimL(v.hyp("data")),witness(v.terms(("ub","uc")),AndIntro(v.hyp("slice"),AndElimR(v.hyp("data")))))))
    return introduce(s,FIXED+("k",),("grid","bound"),lambda t:
        eliminate(t,specialize(t,"slice_exists",*t.terms(("gb","gc")),Mul(Succ(t.term("N")),t.term("k")),Succ(Zero()),t.term("N")),
            ("ub","uc"),"slice",chosen))


def _column_value(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,CongMul,EqRefl,EqSym,OrElim,OrIntroR
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        def actual_column(u):
            return apply(specialize(u,"column_slice",*u.terms(FIXED+("j","ub","uc"))),u.hyp("grid"),u.hyp("bound"),u.hyp("slice"))
        def inside(u):
            def gap(v):
                result = apply(specialize(v,"column_total",*v.terms(P+("j","a","ub","uc","N","q"))),v.hyp("pad"),actual_column(v),v.hyp("span_witness"))
                def totals(w):
                    same = apply(specialize(w,"sum_unique",*w.terms(("bb","bc","M","x0","x"))),field(w.hyp("data"),0,3),w.hyp("right_sum"))
                    identity = _chain(field(w.hyp("data"),2,3),CongMul(EqRefl(w.term("a")),same))
                    affine = witness(w.terms(("ub","uc")),AndIntro(w.hyp("slice"),field(w.hyp("data"),1,3)))
                    return witness((w.term("y"),),AndIntro(affine,identity))
                return eliminate(v,result,("x0","y"),"data",totals)
            span = apply(specialize(u,"span",*u.terms(("L","M","N","j"))),u.hyp("length"),AndElimL(u.hyp("inside")))
            return eliminate(u,span,("q",),"span_witness",gap)
        def outside(u):
            zero_pad = OrIntroR(AndIntro(AndElimL(u.hyp("outside")),EqRefl(Zero())))
            total = apply(specialize(u,"zero_column",*u.terms(P+("j","ub","uc","N"))),zero_pad,actual_column(u))
            identity = EqSym(_chain(CongMul(AndElimR(u.hyp("outside")),EqRefl(u.term("x"))),specialize(u,"mul_zero_left",u.term("x"))))
            return witness((Zero(),),AndIntro(witness(u.terms(("ub","uc")),AndIntro(u.hyp("slice"),total)),identity))
        return OrElim(t.hyp("pad"),inside(t.hypothesis("inside")),outside(t.hypothesis("outside")))
    return introduce(s,FIXED+("j","a","x"),("length","grid","bound","pad","right_sum"),lambda t:
        eliminate(t,specialize(t,"slice_exists",*t.terms(("gb","gc","j")),Succ(t.term("N")),t.term("N")),("ub","uc"),"slice",chosen))


def _construct(s):
    def chosen(t):
        rows = introduce(t,("k",),("bound",),lambda u:
            apply(specialize(u,"row_slice",*u.terms(FIXED+("k",))),u.hyp("grid"),u.hyp("bound")))
        columns = introduce(t,("j","a"),("bound","pad"),lambda u:
            apply(specialize(u,"column_value",*u.terms(FIXED+("j","a","x"))),
                *(u.hyp(label) for label in ("length","grid","bound","pad","right_sum"))))
        return witness(t.terms(("gb","gc","x")),conjunction(t.hyp("grid"),t.hyp("right_sum"),rows,columns))
    return introduce(s,P+("N",),("length",),lambda t:
        eliminate(t,specialize(t,"grid_exists",*t.terms(P+("N",))),("gb","gc"),"grid",lambda u:
            eliminate(u,specialize(u,"sum_exists",*u.terms(("bb","bc","M"))),("x",),"right_sum",chosen)))


def _root(s):
    from peano_lab.kernel.proofs import AndIntro,EqRefl
    from peano_lab.kernel.terms import Add
    def finish(t):
        N = Add(t.term("L"),t.term("M"))
        result = apply(specialize(t,"construct",*t.terms(P),N),EqRefl(N))
        def chosen(u):
            length = Add(u.term("L"),u.term("M"))
            return witness((length,)+u.terms(("gb","gc","x")),AndIntro(EqRefl(length),u.hyp("data")))
        return eliminate(t,result,("gb","gc","x"),"data",chosen)
    return introduce(s,P,(),finish)


def prove_cauchy_grid_sums(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV047",target=frozen_cauchy_grid_sums_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"cell_zero_left":_cell_zero_left,"zero_column":lambda s:_zero_column(s,registry),"span":_span,
            "column_slice":lambda s:_column_slice(s,registry),"row_slice":lambda s:_row_slice(s,registry),
            "column_value":_column_value,"construct":_construct,"CV047":_root},
        pins=cauchy_grid_sums_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
