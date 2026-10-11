"""CV048: full finite natural convolution has the product of the input sums.

Construct the actual length-L+M convolution and all three sums. A common
Cauchy grid, finite Fubini, coefficient identification, linearity, and actual
zero-tail transport prove the product identity, including empty inputs.
"""
from hashlib import sha256

from sqrt2_power_cauchy_grid_sums import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,P,definition_registry,cauchy_grid_sums_source_pins,
    NAMED_SOURCE as GRID_SUM_SOURCE,ALL_ROWS,CONVOLUTION_ARCHIVE,_subst,
)
from sqrt2_power_sum_splitting import FUBINI_ARCHIVE
from sqrt2_power_natural_fubini import NAMED_SOURCE as FUBINI_SOURCE,HELPER_SOURCES as FUBINI_HELPERS
from sqrt2_power_sum_linearity import LINEARITY_SOURCE
from sqrt2_power_sum_zero_tail import NAMED_SOURCE as ZERO_TAIL_SOURCE
from sqrt2_power_euler_product import coefficient
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-convolution-total-v1"
A,B = P[:3],P[3:]
R,T = ("rb","rc"),("tb","tc")
FIXED = P+("N","gb","gc","y")+T
ROWS = ALL_ROWS
COLS = "forall j a. Lt(j,N) -> BetaZeroExtend(ab,ac,L,j,a) -> exists v. NatAffineSum(gb,gc,j,S N,N,v) /\\ v=a*y"
ROW_TABLE = "NatAffineRowSums(gb,gc,0,S N,1,N,N,rb,rc)"
COL_TABLE = "NatAffineRowSums(gb,gc,0,1,S N,N,N,tb,tc)"


def prefix(length="N"):
    return "NatConvolutionPrefix("+",".join(P+R+(length,))+")"


NAMED_SOURCE = "forall "+" ".join(P)+". exists rb rc x y z. "+prefix("L+M")+" /\\ (Sum(ab,ac,L,x) /\\ (Sum(bb,bc,M,y) /\\ (Sum(rb,rc,L+M,z) /\\ z=x*y)))"
TARGET_SHA256 = "074045ab4db4d6936b3447f35096441e7ed3857f9eb93287ea1335d93cbad0dc"
HELPER_SOURCES = {
    "rows_prefix":"forall "+" ".join(P+("N","gb","gc")+R)+". ("+ROWS+") -> "+ROW_TABLE+" -> "+prefix(),
    "column_entry":"forall "+" ".join(FIXED+("j","a","c"))+". ("+COLS+") -> "+COL_TABLE+
        " -> Lt(j,N) -> BetaZeroExtend(ab,ac,L,j,a) -> BetaAt(tb,tc,j,c) -> c=a*y",
    "column_linear":"forall "+" ".join(FIXED+("x","w"))+". N=L+M -> ("+COLS+") -> "+COL_TABLE+
        " -> Sum(ab,ac,L,x) -> Sum(tb,tc,L,w) -> w=x*y",
    "column_tail":"forall "+" ".join(FIXED)+". N=L+M -> ("+COLS+") -> "+COL_TABLE+
        " -> (forall h. Lt(h,M) -> BetaAt(tb,tc,L+h,0))",
}
HELPER_TARGET_SHA256 = {
    "rows_prefix":"24af4767a22eb58cbc2835e2194700bf3b9684a7621d72e374656bb32329fa93",
    "column_entry":"3c6d949dc229ab03752e726da5c895ab7833d791a7871c0d18d1e9fa5f11b878",
    "column_linear":"dc3516cf9b2c3e393a196d6ae60018539719655090f3088e12b5e22ac9749ec3",
    "column_tail":"d5d538b3c784f1cf671d206888825b8114939f68ba503d89f493a7a0173e37b8",
}
GRID_ARCHIVE = dict(case="CV047",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-cauchy-grid-sums-v2/generation-process.json.gz",
    bytes=32686,sha256="19f5afbc092fcbb647a3c16291a3b139fb086bb5ef798a5b75727e19aa6fb5d0",
    raw_bytes=663681,raw_sha256="7d97ab5d5d46e1c9cf4e6a10a70b8e4ebaaad1e2abe10674259d66d45523ac07",
    bundle_bytes=400130,bundle_sha256="3f86c41ea1d9b3740f12a7e74c131e5baf272e7b037b4bd54b45967ab9324f95",
    nodes=149,root=148,target_ast_sha256="f9641b30ca39287a97a195a21f4f444b93c513dc143c2f42166caff02b8f76a0")
ARCHIVES = (GRID_ARCHIVE,FUBINI_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {
    "zero_add":"forall a. 0+a=a","add_comm":"forall a b. a+b=b+a",
    "one_mul":"forall a. 1*a=a","mul_zero_left":"forall a. 0*a=0","mul_comm":"forall a b. a*b=b*a",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "sum_unique":"forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m",
    "slice_sum_unique":FUBINI_HELPERS["slice_sum_unique"],"rows_lookup":FUBINI_HELPERS["rows_lookup"],
    "shift_bound":"forall M k N. Lt(k,N) -> Lt(M+k,M+N)",
    "linearity":LINEARITY_SOURCE,"zero_tail":ZERO_TAIL_SOURCE,
    "grid_sums":GRID_SUM_SOURCE,"fubini":FUBINI_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(slice_sum_unique="CV008",rows_lookup="CV008",fubini="CV008",
    shift_bound="CV047",linearity="CV047",zero_tail="CV047",grid_sums="CV047")
HELPER_DEPENDENCIES = {
    "rows_prefix":("zero_add","slice_sum_unique"),
    "column_entry":("rows_lookup","one_mul","zero_add","slice_sum_unique"),
    "column_linear":("add_comm","le_trans","column_entry","one_mul","mul_comm","mul_zero_left","linearity"),
    "column_tail":("beta_exists","shift_bound","add_comm","column_entry","mul_zero_left"),
    "CV048":("grid_sums","fubini","sum_exists","rows_prefix","column_linear","column_tail","zero_tail","sum_unique"),
}


class ConvolutionTotalError(ValueError):
    """Changed exact full-length convolution, actual sums or proof ancestry."""


def frozen_convolution_total_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=6 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionTotalError("CV048 exact constructed convolution product-sum target changed")
    return target


def source_contract():
    return dict(code="CV048",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_convolution_and_all_three_sum_values_constructed=True,
        full_convolution_sum_product=True,output_length="L+M",empty_inputs_allowed=True,
        finite_fubini_replayed=True,column_zero_tail_proved=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",full_convolution_evaluation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def convolution_total_source_pins():
    result = cauchy_grid_sums_source_pins()
    expected = {"scripts/sqrt2_power_cauchy_grid_sums.py":"8be35525e0bf7e6f4bcfda291920efcf2175b738bcb76fe2692d6565eb7f4ca5",
        "scripts/sqrt2_power_natural_fubini.py":"d5cc2e21ccbe1f266cad6b535db62601f8e8ba1aa3209a7f89d794285e3805ac",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_convolution_total.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionTotalError("convolution total source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _rows_prefix(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def chosen(t):
        def at(u):
            def original(v):
                def identified(w):
                    offset = Mul(Succ(w.term("N")),w.term("k"))
                    actual = _subst(w,registry,"NatAffineSum(gb,gc,slot,1,N,r)",specialize(w,"zero_add",offset),AndElimR(w.hyp("entry")))
                    same = apply(specialize(w,"slice_sum_unique",*w.terms(("gb","gc")),offset,Succ(Zero()),*w.terms(("N","u","r"))),
                        AndElimR(w.hyp("coefficient")),actual)
                    coeff = _subst(w,registry,coefficient(A,B,"k","slot"),same,AndElimL(w.hyp("coefficient")))
                    return witness((w.term("r"),),AndIntro(AndElimL(w.hyp("entry")),coeff))
                return eliminate(v,apply(specialize(v,"known_rows",v.term("k")),v.hyp("bound")),("u",),"coefficient",identified)
            return eliminate(u,apply(specialize(u,"rows",u.term("k")),u.hyp("bound")),("r",),"entry",original)
        return introduce(t,("k",),("bound",),at)
    return introduce(s,P+("N","gb","gc")+R,("known_rows","rows"),chosen)


def _column_entry(s,registry):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,EqRefl
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        actual = apply(specialize(t,"rows_lookup",*t.terms(("gb","gc")),Zero(),Succ(Zero()),Succ(t.term("N")),
            *t.terms(("N","N","tb","tc","j","c"))),t.hyp("columns"),t.hyp("bound"),t.hyp("entry"))
        offset = _chain(CongAdd(EqRefl(Zero()),specialize(t,"one_mul",t.term("j"))),specialize(t,"zero_add",t.term("j")))
        actual = _subst(t,registry,"NatAffineSum(gb,gc,slot,S N,N,c)",offset,actual)
        same = apply(specialize(t,"slice_sum_unique",*t.terms(("gb","gc","j")),Succ(t.term("N")),*t.terms(("N","c","v"))),
            actual,AndElimL(t.hyp("value")))
        return _chain(same,AndElimR(t.hyp("value")))
    return introduce(s,FIXED+("j","a","c"),("known_columns","columns","bound","pad","entry"),lambda t:
        eliminate(t,apply(specialize(t,"known_columns",*t.terms(("j","a"))),t.hyp("bound"),t.hyp("pad")),("v",),"value",chosen))


def _column_linear(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndIntro,CongAdd,EqRefl,EqSym,OrIntroL
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def chosen(t):
        def pointwise(u):
            large = witness((u.term("M"),),_chain(specialize(u,"add_comm",*u.terms(("M","L"))),EqSym(u.hyp("length"))))
            below = apply(specialize(u,"le_trans",Succ(u.term("j")),*u.terms(("L","N"))),u.hyp("bound"),large)
            pad = OrIntroL(AndIntro(u.hyp("bound"),u.hyp("first")))
            identity = apply(specialize(u,"column_entry",*u.terms(FIXED+("j","a","c"))),
                u.hyp("known_columns"),u.hyp("columns"),below,pad,u.hyp("third"))
            ya = Mul(u.term("y"),u.term("a"))
            return _chain(specialize(u,"one_mul",u.term("c")),identity,specialize(u,"mul_comm",*u.terms(("a","y"))),
                EqSym(instantiate(Axiom("PA3"),ya)),CongAdd(EqRefl(ya),EqSym(specialize(u,"mul_zero_left",u.term("b")))))
        relation = introduce(t,("j","a","b","c"),("bound","first","second","third"),pointwise)
        total = apply(specialize(t,"linearity",t.term("y"),Zero(),Succ(Zero()),
            *t.terms(("ab","ac","ab","ac","tb","tc","L","x","x","w"))),t.hyp("left_sum"),t.hyp("left_sum"),t.hyp("prefix_sum"),relation)
        return _chain(EqSym(specialize(t,"one_mul",t.term("w"))),total,
            CongAdd(EqRefl(Mul(t.term("y"),t.term("x"))),specialize(t,"mul_zero_left",t.term("x"))),
            instantiate(Axiom("PA3"),Mul(t.term("y"),t.term("x"))),specialize(t,"mul_comm",*t.terms(("y","x"))))
    return introduce(s,FIXED+("x","w"),("length","known_columns","columns","left_sum","prefix_sum"),chosen)


def _column_tail(s,registry):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndIntro,EqRefl,EqSym,OrIntroR
    from peano_lab.kernel.terms import Add,Zero
    def chosen(t):
        h,L,M = t.terms(("h","L","M"))
        index = Add(L,h)
        below = apply(specialize(t,"shift_bound",L,h,M),t.hyp("bound"))
        below = _subst(t,registry,"Lt(L+h,slot)",EqSym(t.hyp("length")),below)
        pad = OrIntroR(AndIntro(witness((h,),specialize(t,"add_comm",h,L)),EqRefl(Zero())))
        value = apply(specialize(t,"column_entry",*t.terms(FIXED),index,Zero(),t.term("c")),
            t.hyp("known_columns"),t.hyp("columns"),below,pad,t.hyp("entry"))
        zero = _chain(value,specialize(t,"mul_zero_left",t.term("y")))
        return _subst(t,registry,"BetaAt(tb,tc,L+h,slot)",zero,t.hyp("entry"))
    return introduce(s,FIXED,("length","known_columns","columns"),lambda t:
        introduce(t,("h",),("bound",),lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(T),Add(u.term("L"),u.term("h"))),("c",),"entry",chosen)))


def _root(s,registry):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        length,known_rows,known_cols = field(t.hyp("grid_data"),0,5),field(t.hyp("grid_data"),3,5),field(t.hyp("grid_data"),4,5)
        row_table,col_table = field(t.hyp("double"),0,4),field(t.hyp("double"),1,4)
        prefix_proof = apply(specialize(t,"rows_prefix",*t.terms(P+("N","gb","gc")+R)),known_rows,row_table)
        product = apply(specialize(t,"column_linear",*t.terms(FIXED+("x","w"))),length,known_cols,col_table,t.hyp("left_sum"),t.hyp("column_prefix"))
        zeros = apply(specialize(t,"column_tail",*t.terms(FIXED)),length,known_cols,col_table)
        longer = apply(specialize(t,"zero_tail",*t.terms(T+("L","M","w"))),t.hyp("column_prefix"),zeros)
        longer = _subst(t,registry,"Sum(tb,tc,slot,w)",EqSym(length),longer)
        same = apply(specialize(t,"sum_unique",*t.terms(T+("N","z","w"))),field(t.hyp("double"),3,4),longer)
        identity = _chain(same,product)
        prefix_proof = _subst(t,registry,prefix("slot"),length,prefix_proof)
        total = _subst(t,registry,"Sum(rb,rc,slot,z)",length,field(t.hyp("double"),2,4))
        return witness(t.terms(R+("x","y","z")),conjunction(prefix_proof,t.hyp("left_sum"),field(t.hyp("grid_data"),2,5),total,identity))
    def summed(t):
        return eliminate(t,specialize(t,"sum_exists",*t.terms(A)),("x",),"left_sum",lambda u:
            eliminate(u,specialize(u,"sum_exists",*u.terms(T+("L",))),("w",),"column_prefix",chosen))
    def grid(t):
        return eliminate(t,specialize(t,"fubini",*t.terms(("gb","gc")),Zero(),Succ(t.term("N")),Succ(Zero()),*t.terms(("N","N"))),
            R+T+("z",),"double",summed)
    return introduce(s,P,(),lambda t:
        eliminate(t,specialize(t,"grid_sums",*t.terms(P)),("N","gb","gc","y"),"grid_data",grid))


def prove_convolution_total(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV048",target=frozen_convolution_total_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"rows_prefix":lambda s:_rows_prefix(s,registry),"column_entry":lambda s:_column_entry(s,registry),
            "column_linear":_column_linear,"column_tail":lambda s:_column_tail(s,registry),"CV048":lambda s:_root(s,registry)},
        pins=convolution_total_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
