"""CV053: construct convolution with a proved upper coefficient support.

Separate zero-after premises at r and s imply the output is zero from r+s.
The new local alias describes a padded-input property, not a computation or
an assumed convolution law. Empty lengths and cutoffs are allowed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_natural_convolution import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,
    canonical,json_hash,definition_registry as base_registry,natural_convolution_source_pins,
    HELPER_SOURCES as CONVOLUTION_HELPERS,
)
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_sum_zero_tail import ZERO_SUM_SOURCE,sum_zero_tail_source_pins
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-convolution-upper-support-v1"
A,B,C = ("ab","ac","L"),("bb","bc","M"),("cb","cc")
P = A+B+("r","s")
DEFINITION_PARAMETERS = ("b","c","L","r")
DEFINITION_SOURCE = "forall i a. Le(r,i) -> BetaZeroExtend(b,c,L,i,a) -> a=0"
DEFINITION_SHA256 = "b2db7e5b600ca17ad802a56c7e294a523e6ab84653fdacb9467e569cc377f92e"


def zeros(codes,cutoff):
    return "NatZeroAfter("+",".join(codes+(cutoff,))+")"


def coefficient(value):
    return "NatConvolutionCoefficient("+",".join(A+B+("i",value))+")"


def prefix():
    return "NatConvolutionPrefix("+",".join(A+B+C+("N",))+")"


INPUTS = zeros(A,"r")+" -> "+zeros(B,"s")+" -> "
NAMED_SOURCE = "forall "+" ".join(P+("N",))+". "+INPUTS+"exists cb cc. "+prefix()+" /\\ "+zeros(C+("N",),"r+s")
TARGET_SHA256 = "10fb7e6300ce6b56bf6d231d7f357343629838d1ed95469a0309b42e521c276a"
HELPER_SOURCES = {
    "split_indices":"forall r s i j k. j+k=i -> Le(r+s,i) -> Le(r,j) \\/ Le(s,k)",
    "term_zero":"forall "+" ".join(P+("i","j","v"))+". "+INPUTS+"Le(r+s,i) -> PolynomialDiagonalTerm("+",".join(A+B+("i","j","v"))+") -> v=0",
    "coefficient_zero":"forall "+" ".join(P+("i","v"))+". "+INPUTS+"Le(r+s,i) -> "+coefficient("v")+" -> v=0",
    "prefix_support":"forall "+" ".join(P+C+("N",))+". "+INPUTS+prefix()+" -> "+zeros(C+("N",),"r+s"),
}
HELPER_TARGET_SHA256 = {
    "split_indices":"0e2403e28b3f41b65bece2c350a966d11d6cb3e192e86a9d1a14cb981b320e4d",
    "term_zero":"94d641476989cec4f58f8ebfcf3f9911df41d5ace89f374351e9d6bc219289d8",
    "coefficient_zero":"fade8b4a036cc92cdf8aef50bf68416adb8e67fcbbb4cbfe0bd19c520395c487",
    "prefix_support":"2dcc2ba35bba212e638ee041e9e5dbb0999e0c77962b51cf2611d4eeffd3c3f0",
}
ZERO_TAIL_ARCHIVE = dict(case="CV011",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-sum-zero-tail-v1/generation-process.json.gz",
    bytes=23585,sha256="37814931ce1d3e065b2e1301e0fbe7de6385a9411858917f6b93d3a9c87f29ab",
    raw_bytes=440073,raw_sha256="aeed77fcf6c83d38880aedd470987ef1ac2a5388e15ba4c47e118e5d43ef4e87",
    bundle_bytes=264420,bundle_sha256="bdd2e9754c7c3700e19d4a26426a490e34fabfb435f0020e9b99ab26d984ff55",
    nodes=123,root=122,target_ast_sha256="a7f186fd8bb8fecb316c79650a437ffc8e7c8a66e971c9cdf9740c56e26fe28e")
VANISHING_ARCHIVE = dict(case="CV001",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-vanishing-v3/generation-process.json.gz",
    bytes=9622,sha256="555071d9f8c3c30a7c37aa078fbf6fe0ff49de7bf972c1ca880e0fdcf6e248d7",
    raw_bytes=110174,raw_sha256="dfcd706134bfd9af4a29e140d7a8145e6afce52bab5b2d3cd83f58d3105861f2",
    bundle_bytes=58402,bundle_sha256="93d3871e7c7f06fc5974b61bec48616a7a7f13e6f919bf7dbf34570624e918b6",
    nodes=28,root=27,target_ast_sha256="b5ca16c60cf9aff317a93603448843e717d17228380fb7c1a1287e31f12e5e22")
ARCHIVES = (CONVOLUTION_ARCHIVE,ZERO_TAIL_ARCHIVE,VANISHING_ARCHIVE)
ENDPOINT_SOURCES = {
    "add_succ_left":"forall a b. S a+b=S (a+b)","mul_zero_left":"forall a. 0*a=0",
    "le_or_lt":"forall a b. Le(a,b) \\/ Lt(b,a)",
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "add_le_add_right":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "add_le_add_left":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "diagonal_entry":"forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)",
    "prefix_exists":CONVOLUTION_HELPERS["prefix_exists"],"prefix_entry":CONVOLUTION_HELPERS["prefix_entry"],
    "zero_sum":ZERO_SUM_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["zero_sum"] = "CV011"
ENDPOINT_OWNERS.update(add_le_add_right="CV001",add_le_add_left="CV001")
HELPER_DEPENDENCIES = {
    "split_indices":("le_or_lt","le_refl","le_succ","le_trans","add_le_add_right","add_le_add_left","add_succ_left","lt_not_le"),
    "term_zero":("split_indices","mul_zero_left"),
    "coefficient_zero":("diagonal_entry","term_zero","zero_sum"),
    "prefix_support":("prefix_entry","coefficient_zero"),
    "CV053":("prefix_exists","prefix_support"),
}


class ConvolutionUpperSupportError(ValueError):
    """Changed zero-after predicate, actual cutoff, target or ancestor body."""


def definition_registry():
    import json
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(base_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    identifier,name = "ND0436","NatZeroAfter"
    if name in registry or identifier in {d.stable_id for d in registry.values()} or any(d["id"]==identifier or d["name"]==name for d in parent):
        raise ConvolutionUpperSupportError("zero-after local alias collision")
    formula = parse_named(DEFINITION_SOURCE,DEFINITION_PARAMETERS,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise ConvolutionUpperSupportError("zero-after exact expansion changed")
    source = pretty_formula(formula,list(DEFINITION_PARAMETERS))
    d = _definition(stable_id=identifier,name=name,parameters=DEFINITION_PARAMETERS,template_source=source,
        summary="Zero values at and above a cutoff in the actual padded table; separate from execution.",
        category="irrationality_formal_series",conceptual_dependencies=("Le","BetaZeroExtend"))
    if d.template_formula!=formula or parse_formula_in_context(source,list(DEFINITION_PARAMETERS))!=formula:
        raise ConvolutionUpperSupportError("zero-after exact expansion roundtrip failed")
    registry[name] = d
    return MappingProxyType(registry)


def frozen_convolution_upper_support_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=9 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionUpperSupportError("CV053 exact constructed upper-support target changed")
    return target


def source_contract():
    return dict(code="CV053",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,input_zero_after_properties_required=True,actual_convolution_prefix_constructed=True,
        output_zero_after_sum_of_cutoffs_proved=True,arbitrary_output_width=True,
        zero_cutoffs_and_empty_lengths_allowed=True,execution_contains_support_claim=False,
        new_definition_ids=["ND0436"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",all_power_row_upper_support=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def convolution_upper_support_source_pins():
    result = natural_convolution_source_pins()
    for name,pin in sum_zero_tail_source_pins().items():
        if name in result and result[name]!=pin:
            raise ConvolutionUpperSupportError("shared proof-source pins disagree")
        result[name] = pin
    expected = {"scripts/sqrt2_power_natural_convolution.py":"a5498a8534df2e1618419bb2a4ee382d3ebd205fd024560cca9876ab9e4eedd1",
        "scripts/sqrt2_power_sum_zero_tail.py":"a4112bbf650aa6dfedf3204463a88d4d82ec3ab9f55948ad54c9423208f7d223",
        "scripts/sqrt2_power_convolution_unit.py":"d058762fb3641d5bb1e90c764c4581801feeaf0a103901811b3e82dbe3db8f16",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_convolution_upper_support.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionUpperSupportError("upper-support source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _split_indices(s,registry):
    from peano_lab.kernel.proofs import BotElim,CongS,EqTrans,OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Add,Succ
    def finish(t):
        left = t.hypothesis("left_large")
        right = t.hypothesis("left_small")
        def second(u):
            large = u.hypothesis("right_large")
            small = u.hypothesis("right_small")
            r,sv,i,j,k = small.terms(("r","s","i","j","k"))
            weak = apply(specialize(small,"le_trans",k,Succ(k),sv),
                apply(specialize(small,"le_succ",k,k),specialize(small,"le_refl",k)),small.hyp("right_small"))
            total = apply(specialize(small,"le_trans",Add(Succ(j),k),Add(r,k),Add(r,sv)),
                apply(specialize(small,"add_le_add_right",Succ(j),r,k),small.hyp("left_small")),
                apply(specialize(small,"add_le_add_left",k,sv,r),weak))
            equal = EqTrans(specialize(small,"add_succ_left",j,k),CongS(small.hyp("equation")))
            strict = _subst(small,registry,"Le(slot,r+s)",equal,total)
            contradiction = BotElim(apply(specialize(small,"lt_not_le",i,Add(r,sv)),strict,small.hyp("bound")))
            return OrElim(specialize(u,"le_or_lt",*u.terms(("s","k"))),OrIntroR(large.hyp("right_large")),contradiction)
        return OrElim(specialize(t,"le_or_lt",*t.terms(("r","j"))),OrIntroL(left.hyp("left_large")),second(right))
    return introduce(s,("r","s","i","j","k"),("equation","bound"),finish)


def _term_zero(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongMul,EqRefl,EqTrans,OrElim
    def decoded(t):
        split = apply(specialize(t,"split_indices",*t.terms(("r","s","i","j","k"))),field(t.hyp("data"),0,4),t.hyp("bound"))
        left,right = t.hypothesis("left_large"),t.hypothesis("right_large")
        azero = apply(specialize(left,"zeroA",*left.terms(("j","a"))),left.hyp("left_large"),field(left.hyp("data"),1,4))
        bzero = apply(specialize(right,"zeroB",*right.terms(("k","b"))),right.hyp("right_large"),field(right.hyp("data"),2,4))
        first = EqTrans(field(left.hyp("data"),3,4),EqTrans(CongMul(azero,EqRefl(left.term("b"))),specialize(left,"mul_zero_left",left.term("b"))))
        second = EqTrans(field(right.hyp("data"),3,4),EqTrans(CongMul(EqRefl(right.term("a")),bzero),instantiate(Axiom("PA5"),right.term("a"))))
        return OrElim(split,first,second)
    return introduce(s,P+("i","j","v"),("zeroA","zeroB","bound","term"),lambda t:
        eliminate(t,t.hyp("term"),("k","a","b"),"data",decoded))


def _coefficient_zero(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ
    def decoded(t):
        def pointwise(u):
            term = apply(specialize(u,"diagonal_entry",*u.terms(A+B+("i","xb","xc")),Succ(u.term("i")),*u.terms(("j","a"))),
                AndElimL(u.hyp("data")),u.hyp("index"),u.hyp("entry"))
            return apply(specialize(u,"term_zero",*u.terms(P+("i","j","a"))),u.hyp("zeroA"),u.hyp("zeroB"),u.hyp("bound"),term)
        return apply(specialize(t,"zero_sum",*t.terms(("xb","xc")),Succ(t.term("i")),t.term("v")),
            AndElimR(t.hyp("data")),introduce(t,("j","a"),("index","entry"),pointwise))
    return introduce(s,P+("i","v"),("zeroA","zeroB","bound","coefficient"),lambda t:
        eliminate(t,t.hyp("coefficient"),("xb","xc"),"data",decoded))


def _prefix_support(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,OrElim
    def pointwise(t):
        inside,outside = t.hypothesis("inside"),t.hypothesis("outside")
        coefficient = apply(specialize(inside,"prefix_entry",*inside.terms(A+B+C+("N","i","a"))),
            inside.hyp("prefix"),AndElimL(inside.hyp("inside")),AndElimR(inside.hyp("inside")))
        zero = apply(specialize(inside,"coefficient_zero",*inside.terms(P+("i","a"))),inside.hyp("zeroA"),inside.hyp("zeroB"),inside.hyp("bound"),coefficient)
        return OrElim(t.hyp("padded"),zero,AndElimR(outside.hyp("outside")))
    return introduce(s,P+C+("N",),("zeroA","zeroB","prefix"),lambda t:
        introduce(t,("i","a"),("bound","padded"),pointwise))


def _root(s):
    from peano_lab.kernel.proofs import AndIntro
    def chosen(t):
        support = apply(specialize(t,"prefix_support",*t.terms(P+C+("N",))),t.hyp("zeroA"),t.hyp("zeroB"),t.hyp("prefix"))
        return witness(t.terms(C),AndIntro(t.hyp("prefix"),support))
    return introduce(s,P+("N",),("zeroA","zeroB"),lambda t:
        eliminate(t,specialize(t,"prefix_exists",*t.terms(A+B+("N",))),C,"prefix",chosen))


def prove_convolution_upper_support(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV053",target=frozen_convolution_upper_support_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"split_indices":lambda s:_split_indices(s,registry),"term_zero":_term_zero,"coefficient_zero":_coefficient_zero,
            "prefix_support":_prefix_support,"CV053":_root},
        pins=convolution_upper_support_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
