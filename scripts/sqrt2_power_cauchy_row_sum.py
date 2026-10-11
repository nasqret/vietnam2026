"""CV045: construct a Cauchy grid and identify all its actual row sums.

The side-N+1 row at k<=N extends the actual length-k+1 antidiagonal by
proved zero entries. Its affine sum is the actual convolution coefficient.
Column identities and the complete product-evaluation theorem are not assumed.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_cauchy_grid import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,P,cell,GRID,definition_registry as grid_registry,
    cauchy_grid_source_pins,NAMED_SOURCE as GRID_SOURCE,CONVOLUTION_ARCHIVE,_subst,
)
from sqrt2_power_sum_splitting import FUBINI_ARCHIVE
from sqrt2_power_natural_fubini import definition_registry as fubini_registry,HELPER_SOURCES as FUBINI_HELPERS
from sqrt2_power_triple_row_sum import ZERO_TAIL_ARCHIVE
from sqrt2_power_sum_zero_tail import NAMED_SOURCE as ZERO_TAIL_SOURCE
from sqrt2_power_euler_product import coefficient
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-cauchy-row-sum-v1"
A,B = P[:3],P[3:]
ROW_PARAMETERS = P+("k","ub","uc","T")
DEFINITION_SOURCE = "forall j z. Lt(j,T) -> BetaAt(ub,uc,j,z) -> "+cell()
DEFINITION_SHA256 = "79d21646606574f6521d7e6235f11603a005ee9a3ab4e80e96831f9e717d85b7"
ROW = "NatCauchyRow("+",".join(ROW_PARAMETERS)+")"
ROW_RESULT = coefficient(A,B,"k","u")+" /\\ Sum(ub,uc,T,u)"
GRID_RESULT = coefficient(A,B,"k","u")+" /\\ NatAffineSum(gb,gc,(S N)*k,1,S N,u)"
NAMED_SOURCE = "forall "+" ".join(P+("N",))+". exists gb gc. "+GRID+" /\\ (forall k. Lt(k,S N) -> exists u. "+GRID_RESULT+")"
TARGET_SHA256 = "1e5bd50b1aebb4f3f9ccee2b1ed520e7c8faafdc3731a8285363a3811d4a23da"
HELPER_SOURCES = {
    "cell_term":"forall "+" ".join(P+("k","j","z"))+". Le(j,k) -> "+cell()+" -> PolynomialDiagonalTerm("+",".join(P+("k","j","z"))+")",
    "cell_zero":"forall "+" ".join(P+("k","j","z"))+". Lt(k,j) -> "+cell()+" -> z=0",
    "row_total":"forall "+" ".join(ROW_PARAMETERS)+". Lt(k,T) -> "+ROW+" -> exists u. "+ROW_RESULT,
    "grid_row":"forall "+" ".join(P+("N","gb","gc","k"))+". "+GRID+" -> Lt(k,S N) -> exists u. "+GRID_RESULT,
}
HELPER_TARGET_SHA256 = {
    "cell_term":"97beffee609a085175d6659b6df00db9b6eacbd87a2e9dee85096e96c09c97ca",
    "cell_zero":"49784016e852a6e3810604c27961879facd9a42f9d0fa4aca47707bbf0cd5fd8",
    "row_total":"8876dce183ee5610d02b44dbe3f660a702dced1006b82c8a6a0b8a9fcd45a1fc",
    "grid_row":"69f75454ef47c1b709c10b184704d61510d996286e29b19db5e45cd0635bff5c",
}
CAUCHY_ARCHIVE = dict(case="CV044",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-cauchy-grid-v1/generation-process.json.gz",
    bytes=20424,sha256="cdcc07c7729f1280c015adad77c934596c53be7403003221e81af37a2f410569",
    raw_bytes=295163,raw_sha256="fe987d0bd01381900ec7524e777dae3d37455bbd6c9489a2e6becbe6cd73ec30",
    bundle_bytes=174288,bundle_sha256="9c96b3fa34227010da9bdd33d71361ce7d3edbae1ee2f1c230f90f46c5a74ad0",
    nodes=110,root=109,target_ast_sha256="78d464d63eb29155ecd6adef39b240abfae271ca11d414e46e9ecc2be332a0a4")
SHIFT_ARCHIVE = dict(case="CV036",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-zero-tail-v1/generation-process.json.gz",
    bytes=24858,sha256="d8736c95a3d0fe2b31846befa5f453cdf32240959ddbc434bf0a0a73a48d7917",
    raw_bytes=404203,raw_sha256="e9c0f2e807b7418a5d90dbdaf4103cc6f9196da7c0c72aa493840d56739f06a4",
    bundle_bytes=237346,bundle_sha256="106c098a8896d97701ffa0444b2cadc8aafab9d4bbdab9c5603b903fb8963881",
    nodes=122,root=121,target_ast_sha256="ba1d797f495177c7c2b6f504d04e3cb81acb6460d86b60a22e46f3369a8a78d9")
ARCHIVES = (CAUCHY_ARCHIVE,CONVOLUTION_ARCHIVE,FUBINI_ARCHIVE,ZERO_TAIL_ARCHIVE,SHIFT_ARCHIVE)
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a",
    "one_mul":"forall a. 1*a=a",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "shift_bound":"forall M k N. Lt(k,N) -> Lt(M+k,M+N)",
    "zero_tail":ZERO_TAIL_SOURCE,"slice_exists":FUBINI_HELPERS["slice_exists"],"grid_exists":GRID_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(shift_bound="CV036",zero_tail="CV011",slice_exists="CV008",grid_exists="CV044")
HELPER_DEPENDENCIES = {
    "cell_term":("lt_not_le",),"cell_zero":("add_comm","lt_not_le"),
    "row_total":("sum_exists","beta_exists","add_comm","le_trans","le_of_succ_le_succ","shift_bound","cell_term","cell_zero","zero_tail"),
    "grid_row":("slice_exists","one_mul","row_total"),
    "CV045":("grid_exists","grid_row"),
}


class CauchyRowSumError(ValueError):
    """Changed actual row decoding, diagonal boundary or exact sum target."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(grid_registry())
    for name,d in fubini_registry().items():
        if name in registry and (registry[name].stable_id!=d.stable_id or registry[name].template_formula!=d.template_formula):
            raise CauchyRowSumError("Cauchy/affine shared definitions disagree")
        registry[name] = d
    name,identifier = "NatCauchyRow","ND0434"
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    if name in registry or any(d["name"]==name or d["id"]==identifier for d in parent):
        raise CauchyRowSumError("Cauchy row alias collision")
    formula = parse_named(DEFINITION_SOURCE,ROW_PARAMETERS,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise CauchyRowSumError("Cauchy row exact expansion changed")
    text = pretty_formula(formula,list(ROW_PARAMETERS))
    d = _definition(stable_id=identifier,name=name,parameters=ROW_PARAMETERS,template_source=text,
        summary="An actual beta prefix of Cauchy cells at one fixed output index; no sum law.",
        category="irrationality_formal_series",conceptual_dependencies=("Lt","BetaAt","NatCauchyCell"))
    if d.template_formula!=formula or parse_formula_in_context(text,list(ROW_PARAMETERS))!=formula:
        raise CauchyRowSumError("Cauchy row expansion failed exact roundtrip")
    registry[name] = d
    return MappingProxyType(registry)


def frozen_cauchy_row_sum_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CauchyRowSumError("CV045 exact constructed grid and row sums changed")
    return target


def source_contract():
    return dict(code="CV045",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_whole_grid_and_all_row_sums_constructed=True,
        all_row_sums_are_actual_convolution_coefficients=True,diagonal_zero_tail_proved=True,
        arbitrary_input_lengths_and_grid_parameter=True,new_definition_ids=["ND0434"],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        column_sum_identities=False,full_convolution_evaluation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def cauchy_row_sum_source_pins():
    result = cauchy_grid_source_pins()
    expected = {"scripts/sqrt2_power_cauchy_grid.py":"9381aa2a44c3a13e49379ae9fe265e07704bd547fb32c75374694bb2607bfac4",
        "scripts/sqrt2_power_natural_fubini.py":"d5cc2e21ccbe1f266cad6b535db62601f8e8ba1aa3209a7f89d794285e3805ac",
        "scripts/sqrt2_power_sum_zero_tail.py":"a4112bbf650aa6dfedf3204463a88d4d82ec3ab9f55948ad54c9423208f7d223",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_cauchy_row_sum.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CauchyRowSumError("Cauchy row-sum source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _cell_term(s):
    from peano_lab.kernel.proofs import AndElimL,BotElim,OrElim
    def finish(t):
        u = t.hypothesis("outside")
        return OrElim(t.hyp("cell"),t.hypothesis("inside").hyp("inside"),
            BotElim(apply(specialize(u,"lt_not_le",*u.terms(("k","j"))),AndElimL(u.hyp("outside")),u.hyp("bound"))))
    return introduce(s,P+("k","j","z"),("bound","cell"),finish)


def _cell_zero(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimR,BotElim,OrElim
    def finish(t):
        def impossible(u):
            lower = witness((u.term("h"),),_chain(specialize(u,"add_comm",*u.terms(("h","j"))),field(u.hyp("term"),0,4)))
            return BotElim(apply(specialize(u,"lt_not_le",*u.terms(("k","j"))),u.hyp("bound"),lower))
        inside = t.hypothesis("inside")
        return OrElim(t.hyp("cell"),eliminate(inside,inside.hyp("inside"),("h","a","b"),"term",impossible),
            AndElimR(t.hypothesis("outside").hyp("outside")))
    return introduce(s,P+("k","j","z"),("bound","cell"),finish)


def _row_total(s,registry):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndIntro,EqRefl
    from peano_lab.kernel.terms import Add,Succ
    def chosen(t):
        def diagonal(u):
            def decoded(v):
                j,k,T,z = v.terms(("j","k","T","z"))
                below = apply(specialize(v,"le_trans",Succ(j),Succ(k),T),v.hyp("index"),v.hyp("bound"))
                data = apply(specialize(v,"row",j,z),below,v.hyp("entry"))
                lower = apply(specialize(v,"le_of_succ_le_succ",j,k),v.hyp("index"))
                term = apply(specialize(v,"cell_term",*v.terms(P+("k","j","z"))),lower,data)
                return witness((z,),AndIntro(v.hyp("entry"),term))
            return eliminate(u,specialize(u,"beta_exists",*u.terms(("ub","uc","j"))),("z",),"entry",decoded)
        coefficient_proof = witness(t.terms(("ub","uc")),AndIntro(
            introduce(t,("j",),("index",),diagonal),t.hyp("sum")))
        def tail(u):
            def decoded(v):
                k,h,q,T,z = v.terms(("k","h","q","T","z"))
                index = Add(Succ(k),h)
                total_length = _chain(specialize(v,"add_comm",Succ(k),q),v.hyp("gap"))
                below = apply(specialize(v,"shift_bound",Succ(k),h,q),v.hyp("index"))
                below = _subst(v,registry,"Lt((S k)+h,slot)",total_length,below)
                data = apply(specialize(v,"row",index,z),below,v.hyp("entry"))
                after = witness((h,),specialize(v,"add_comm",h,Succ(k)))
                zero = apply(specialize(v,"cell_zero",*v.terms(P),k,index,z),after,data)
                return _subst(v,registry,"BetaAt(ub,uc,(S k)+h,slot)",zero,v.hyp("entry"))
            return eliminate(u,specialize(u,"beta_exists",*u.terms(("ub","uc")),Add(Succ(u.term("k")),u.term("h"))),("z",),"entry",decoded)
        zeros = introduce(t,("h",),("index",),tail)
        longer = apply(specialize(t,"zero_tail",*t.terms(("ub","uc")),Succ(t.term("k")),*t.terms(("q","u"))),t.hyp("sum"),zeros)
        length = _chain(specialize(t,"add_comm",Succ(t.term("k")),t.term("q")),t.hyp("gap"))
        actual = _subst(t,registry,"Sum(ub,uc,slot,u)",length,longer)
        return witness((t.term("u"),),AndIntro(coefficient_proof,actual))
    return introduce(s,ROW_PARAMETERS,("bound","row"),lambda t:
        eliminate(t,t.hyp("bound"),("q",),"gap",lambda u:
            eliminate(u,specialize(u,"sum_exists",*u.terms(("ub","uc")),Succ(u.term("k"))),("u",),"sum",chosen)))


def _grid_row(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,CongAdd,EqRefl
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def chosen(t):
        def pointwise(u):
            entry = apply(specialize(u,"slice",*u.terms(("j","z"))),u.hyp("index"),u.hyp("entry"))
            equal = CongAdd(EqRefl(Mul(Succ(u.term("N")),u.term("k"))),specialize(u,"one_mul",u.term("j")))
            actual = _subst(u,registry,"BetaAt(gb,gc,slot,z)",equal,entry)
            return apply(specialize(u,"grid",*u.terms(("k","j","z"))),u.hyp("bound"),u.hyp("index"),actual)
        row = introduce(t,("j","z"),("index","entry"),pointwise)
        result = apply(specialize(t,"row_total",*t.terms(P+("k","ub","uc")),Succ(t.term("N"))),t.hyp("bound"),row)
        return eliminate(t,result,("u",),"data",lambda v:witness((v.term("u"),),AndIntro(
            AndElimL(v.hyp("data")),witness(v.terms(("ub","uc")),AndIntro(v.hyp("slice"),AndElimR(v.hyp("data")))))))
    return introduce(s,P+("N","gb","gc","k"),("grid","bound"),lambda t:
        eliminate(t,specialize(t,"slice_exists",*t.terms(("gb","gc")),Mul(Succ(t.term("N")),t.term("k")),Succ(Zero()),Succ(t.term("N"))),
            ("ub","uc"),"slice",chosen))


def _root(s):
    from peano_lab.kernel.proofs import AndIntro
    def chosen(t):
        rows = introduce(t,("k",),("bound",),lambda u:
            apply(specialize(u,"grid_row",*u.terms(P+("N","gb","gc","k"))),u.hyp("grid"),u.hyp("bound")))
        return witness(t.terms(("gb","gc")),AndIntro(t.hyp("grid"),rows))
    return introduce(s,P+("N",),(),lambda t:
        eliminate(t,specialize(t,"grid_exists",*t.terms(P+("N",))),("gb","gc"),"grid",chosen))


def prove_cauchy_row_sum(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV045",target=frozen_cauchy_row_sum_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"cell_term":_cell_term,"cell_zero":_cell_zero,"row_total":lambda s:_row_total(s,registry),
            "grid_row":lambda s:_grid_row(s,registry),"CV045":_root},
        pins=cauchy_row_sum_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
