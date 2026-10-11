"""CV046: exact sum of a complete, zero-padded Cauchy column.

For a decoded left value a and actual column U, if (j+M)+q=T then the
length-T column sum is a times the length-M right-input sum. The length
equality is essential: a shorter truncated column need not have that sum.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_cauchy_row_sum import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,P,cell,definition_registry as row_registry,
    cauchy_row_sum_source_pins,HELPER_SOURCES as ROW_HELPERS,CONVOLUTION_ARCHIVE,_subst,
)
from sqrt2_power_shifted_scaled_sum import NAMED_SOURCE as SHIFTED_SUM_SOURCE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-cauchy-column-sum-v1"
COLUMN_PARAMETERS = P+("j","ub","uc","T")
DEFINITION_SOURCE = "forall k z. Lt(k,T) -> BetaAt(ub,uc,k,z) -> "+cell()
DEFINITION_SHA256 = "c00ef5cd310e94d31e6114374759409ee484b9f898757c6f8247e234b9999293"
COLUMN = "NatCauchyColumn("+",".join(COLUMN_PARAMETERS)+")"
FIXED = P+("j","a","ub","uc","T","q")
PAD = "BetaZeroExtend(ab,ac,L,j,a)"
RESULT = "Sum(bb,bc,M,x) /\\ (Sum(ub,uc,T,y) /\\ y=a*x)"
NAMED_SOURCE = "forall "+" ".join(FIXED)+". "+PAD+" -> "+COLUMN+" -> (j+M)+q=T -> exists x y. "+RESULT
TARGET_SHA256 = "94eff8a4d0a0b19ee9a9c9a63604deabe5c06331fd7e9e1fd64593a4026f0b4f"
HELPER_SOURCES = {
    "cell_value":"forall "+" ".join(P+("k","j","r","a","b","z"))+". j+r=k -> "+PAD+
        " -> BetaZeroExtend(bb,bc,M,r,b) -> "+cell()+" -> z=a*b",
    "span_bounds":"forall j M q T. (j+M)+q=T -> Le(j,T) /\\ Le(j+M,T)",
}
HELPER_TARGET_SHA256 = {
    "cell_value":"816123b3e5ecc92eb8c6959bc1761684e9cf7841bcf2841b4b0ffb7b19605fa2",
    "span_bounds":"0f902c1aeabdc7c724dac3dd096d0cafe594f33a2c510f90b63b5cfd4becc986",
}
ROW_ARCHIVE = dict(case="CV045",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-cauchy-row-sum-v1/generation-process.json.gz",
    bytes=28209,sha256="812a2c7e68d7df950e762ad3d1f050e6faa32063cd66c4f73bd4790e12a43e34",
    raw_bytes=535326,raw_sha256="4cbcb7b23166f37ac421ec849fad4cc48d8df91f32d08a6851e112b05eecd330",
    bundle_bytes=321100,bundle_sha256="0ca030a7524f9c287ebb556c1577d3b530d13d8d90e9f26e53c538ef10c1da6e",
    nodes=136,root=135,target_ast_sha256="1e5bd50b1aebb4f3f9ccee2b1ed520e7c8faafdc3731a8285363a3811d4a23da")
SHIFTED_ARCHIVE = dict(case="CV043",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-shifted-scaled-sum-v1/generation-process.json.gz",
    bytes=25192,sha256="7b3c25e6dbd299ce26f2bca00e5294b1c55f39d6259219000542a57ac5c9d996",
    raw_bytes=464083,raw_sha256="761fe10d5ff93104e15ed9b9f404bb9d36b8513f81829b23a26e2ae81a4d053a",
    bundle_bytes=277659,bundle_sha256="1568eaa83e40883b44bda2ac0fa02854792abb1da4e9f099e327e168e4fac1c1",
    nodes=125,root=124,target_ast_sha256="6ee048a7b7670833a6caa1ec7172b086096264b73542ae00b8122a9ea9f004fa")
ARCHIVES = (ROW_ARCHIVE,SHIFTED_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a","add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "term_unique":"forall ab ac L bb bc M i j t s. PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,s) -> t=s",
    "cell_term":ROW_HELPERS["cell_term"],"cell_zero":ROW_HELPERS["cell_zero"],
    "shift_bound":"forall M k N. Lt(k,N) -> Lt(M+k,M+N)",
    "shifted_sum":SHIFTED_SUM_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(cell_term="CV045",cell_zero="CV045",shift_bound="CV045",shifted_sum="CV043")
HELPER_DEPENDENCIES = {
    "cell_value":("add_comm","cell_term","term_unique"),
    "span_bounds":("add_comm","add_assoc"),
    "CV046":("span_bounds","le_trans","cell_zero","cell_value","shift_bound","beta_exists","add_comm","add_assoc","shifted_sum"),
}


class CauchyColumnSumError(ValueError):
    """Changed column computation, complete-length condition or exact proof."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(row_registry())
    name,identifier = "NatCauchyColumn","ND0435"
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    if name in registry or any(d["name"]==name or d["id"]==identifier for d in parent):
        raise CauchyColumnSumError("Cauchy column alias collision")
    formula = parse_named(DEFINITION_SOURCE,COLUMN_PARAMETERS,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise CauchyColumnSumError("Cauchy column exact expansion changed")
    text = pretty_formula(formula,list(COLUMN_PARAMETERS))
    d = _definition(stable_id=identifier,name=name,parameters=COLUMN_PARAMETERS,template_source=text,
        summary="An actual beta prefix of Cauchy cells at one fixed left-input index; no sum law.",
        category="irrationality_formal_series",conceptual_dependencies=("Lt","BetaAt","NatCauchyCell"))
    if d.template_formula!=formula or parse_formula_in_context(text,list(COLUMN_PARAMETERS))!=formula:
        raise CauchyColumnSumError("Cauchy column expansion failed exact roundtrip")
    registry[name] = d
    return MappingProxyType(registry)


def frozen_cauchy_column_sum_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=12 or len(premises)!=3 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CauchyColumnSumError("CV046 exact complete-column sum target changed")
    return target


def source_contract():
    return dict(code="CV046",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,actual_left_padded_value_and_column_required=True,complete_span_equality_required=True,
        both_actual_sum_values_constructed=True,leading_and_trailing_zeros_proved=True,
        zero_value_and_empty_right_input_allowed=True,new_definition_ids=["ND0435"],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        all_grid_columns_unconditionally_constructed=False,full_convolution_evaluation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def cauchy_column_sum_source_pins():
    result = cauchy_row_sum_source_pins()
    expected = {"scripts/sqrt2_power_cauchy_row_sum.py":"48b381d8726afc8d5d19b20713b09a9554eeae2acc44d1ce215dfd7da35cac36",
        "scripts/sqrt2_power_shifted_scaled_sum.py":"24c337ec6520f86ace578a08e7d1aba1bc244188bb7a7b15eb6a60c19c18a83d",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_cauchy_column_sum.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CauchyColumnSumError("Cauchy column-sum source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _cell_value(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Mul
    def finish(t):
        lower = witness((t.term("r"),),_chain(specialize(t,"add_comm",*t.terms(("r","j"))),t.hyp("index")))
        actual = apply(specialize(t,"cell_term",*t.terms(P+("k","j","z"))),lower,t.hyp("cell"))
        product = Mul(t.term("a"),t.term("b"))
        reference = witness(t.terms(("r","a","b")),conjunction(t.hyp("index"),t.hyp("padA"),t.hyp("padB"),EqRefl(product)))
        return apply(specialize(t,"term_unique",*t.terms(P+("k","j","z")),product),actual,reference)
    return introduce(s,P+("k","j","r","a","b","z"),("index","padA","padB","cell"),finish)


def _span_bounds(s):
    from sqrt2_power_quadratic_height import _chain,_additive_equal
    from peano_lab.kernel.proofs import AndIntro
    from peano_lab.kernel.terms import Add
    def finish(t):
        j,M,q = t.terms(("j","M","q"))
        first = witness((Add(M,q),),_chain(_additive_equal(t,Add(Add(M,q),j),Add(Add(j,M),q)),t.hyp("index")))
        second = witness((q,),_chain(specialize(t,"add_comm",q,Add(j,M)),t.hyp("index")))
        return AndIntro(first,second)
    return introduce(s,("j","M","q","T"),("index",),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,AndIntro,EqRefl,EqSym,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Add,Succ,Zero
    def finish(t):
        def leading(u):
            span = apply(specialize(u,"span_bounds",*u.terms(("j","M","q","T"))),u.hyp("index"))
            below = apply(specialize(u,"le_trans",Succ(u.term("i")),*u.terms(("j","T"))),u.hyp("bound"),AndElimL(span))
            data = apply(specialize(u,"column",*u.terms(("i","z"))),below,u.hyp("entry"))
            return apply(specialize(u,"cell_zero",*u.terms(P+("i","j","z"))),u.hyp("bound"),data)
        def middle(u):
            j,h,M,T = u.terms(("j","h","M","T"))
            index = Add(j,h)
            span = apply(specialize(u,"span_bounds",*u.terms(("j","M","q","T"))),u.hyp("index"))
            first = apply(specialize(u,"shift_bound",j,h,M),u.hyp("bound"))
            below = apply(specialize(u,"le_trans",Succ(index),Add(j,M),T),first,AndElimR(span))
            data = apply(specialize(u,"column",index,u.term("c")),below,u.hyp("entry"))
            padding = OrIntroL(AndIntro(u.hyp("bound"),u.hyp("source")))
            return apply(specialize(u,"cell_value",*u.terms(P),index,*u.terms(("j","h","a","b","c"))),
                EqRefl(index),u.hyp("padA"),padding,data)
        def trailing(u):
            def decoded(v):
                j,M,h,q,z = v.terms(("j","M","h","q","z"))
                index = Add(Add(j,M),h)
                below = apply(specialize(v,"shift_bound",Add(j,M),h,q),v.hyp("bound"))
                below = _subst(v,registry,"Lt((j+M)+h,slot)",v.hyp("index"),below)
                data = apply(specialize(v,"column",index,z),below,v.hyp("entry"))
                padding = OrIntroR(AndIntro(witness((h,),specialize(v,"add_comm",h,M)),EqRefl(Zero())))
                value = apply(specialize(v,"cell_value",*v.terms(P),index,j,Add(M,h),v.term("a"),Zero(),z),
                    EqSym(specialize(v,"add_assoc",j,M,h)),v.hyp("padA"),padding,data)
                zero = _chain(value,instantiate(Axiom("PA5"),v.term("a")))
                return _subst(v,registry,"BetaAt(ub,uc,(j+M)+h,slot)",zero,v.hyp("entry"))
            return eliminate(u,specialize(u,"beta_exists",*u.terms(("ub","uc")),Add(Add(u.term("j"),u.term("M")),u.term("h"))),("z",),"entry",decoded)
        result = apply(specialize(t,"shifted_sum",*t.terms(("bb","bc","ub","uc","j","M","q","a"))),
            introduce(t,("i","z"),("bound","entry"),leading),
            introduce(t,("h","b","c"),("bound","source","entry"),middle),
            introduce(t,("h",),("bound",),trailing))
        def chosen(u):
            actual = _subst(u,registry,"Sum(ub,uc,slot,y)",u.hyp("index"),field(u.hyp("data"),1,3))
            return witness(u.terms(("x","y")),conjunction(field(u.hyp("data"),0,3),actual,field(u.hyp("data"),2,3)))
        return eliminate(t,result,("x","y"),"data",chosen)
    return introduce(s,FIXED,("padA","column","index"),finish)


def prove_cauchy_column_sum(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV046",target=frozen_cauchy_column_sum_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"cell_value":_cell_value,"span_bounds":_span_bounds,"CV046":lambda s:_root(s,registry)},
        pins=cauchy_column_sum_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
