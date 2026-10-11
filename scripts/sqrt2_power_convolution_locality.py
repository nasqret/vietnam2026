"""CV050: low convolution coefficients depend only on low padded inputs.

Actual input lengths and encodings may differ. Two explicit local padding
transport premises and i<H suffice; neither full products nor high-degree
tails are identified. The root constructs a common actual coefficient.
"""
from hashlib import sha256

from sqrt2_power_natural_convolution import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,
    canonical,json_hash,definition_registry,natural_convolution_source_pins,
    HELPER_SOURCES as CONVOLUTION_HELPERS,
)
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-convolution-locality-v1"
A,B,C,D = ("ab","ac","L"),("bb","bc","M"),("cb","cc","N"),("db","dc","O")
P = A+B+C+D+("H","i")


def pad(codes,index,value):
    return "BetaZeroExtend("+",".join(codes+(index,value))+")"


def match(left,right):
    return "forall j a. Lt(j,H) -> "+pad(left,"j","a")+" -> "+pad(right,"j","a")


def coefficient(left,right,value):
    return "NatConvolutionCoefficient("+",".join(left+right+("i",value))+")"


def term(left,right):
    return "PolynomialDiagonalTerm("+",".join(left+right+("i","j","v"))+")"


LEFT,RIGHT = match(A,C),match(B,D)
PREMISES = "("+LEFT+") -> ("+RIGHT+") -> Lt(i,H) -> "
NAMED_SOURCE = "forall "+" ".join(P)+". "+PREMISES+"exists n. "+coefficient(A,B,"n")+" /\\ "+coefficient(C,D,"n")
TARGET_SHA256 = "750e75f60ad34a2d8fa423359399e8fcd60a9a1c90dbde559a2faf8a856457c0"
HELPER_SOURCES = {
    "index_bounds":"forall j k i H. j+k=i -> Lt(i,H) -> Lt(j,H) /\\ Lt(k,H)",
    "term_transport":"forall "+" ".join(P+("j","v"))+". "+PREMISES+term(A,B)+" -> "+term(C,D),
    "coefficient_transport":"forall "+" ".join(P+("n",))+". "+PREMISES+coefficient(A,B,"n")+" -> "+coefficient(C,D,"n"),
}
HELPER_TARGET_SHA256 = {
    "index_bounds":"57fc0c005e3cf4e15a0df4ebaa8f8a648446997a83116d1b1af942fa41bdf475",
    "term_transport":"98184fc7e763bc532d0cd0d43ae754e03a66af8e495e0a381b9d85c43c08d2b7",
    "coefficient_transport":"c8c4003447aed1bb5e7e98c536d9ecb34bd9562a9a97d41d3c12b8e3cce8bc6c",
}
ARCHIVES = (CONVOLUTION_ARCHIVE,)
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "coefficient_exists":CONVOLUTION_HELPERS["coefficient_exists"],
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {
    "index_bounds":("add_comm","succ_le_succ","le_trans"),
    "term_transport":("index_bounds",),
    "coefficient_transport":("term_transport",),
    "CV050":("coefficient_exists","coefficient_transport"),
}


class ConvolutionLocalityError(ValueError):
    """Changed low-index bound, actual padding transport or proof ancestry."""


def frozen_convolution_locality_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=14 or len(premises)!=3 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionLocalityError("CV050 exact locally shared coefficient target changed")
    return target


def source_contract():
    return dict(code="CV050",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,two_local_padded_input_transports_required=True,strict_coefficient_bound_required=True,
        common_actual_coefficient_constructed=True,arbitrary_input_lengths_and_encodings=True,
        same_actual_diagonal_and_sum_witnesses_preserved=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",all_degree_product_equality=False,
        cross_width_power_trace_transport=False,analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def convolution_locality_source_pins():
    result = natural_convolution_source_pins()
    expected = {"scripts/sqrt2_power_natural_convolution.py":"a5498a8534df2e1618419bb2a4ee382d3ebd205fd024560cca9876ab9e4eedd1",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_convolution_locality.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionLocalityError("convolution locality source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _index_bounds(s):
    from peano_lab.kernel.proofs import AndIntro,EqTrans
    from peano_lab.kernel.terms import Succ
    def finish(t):
        j,k,i,H = t.terms(("j","k","i","H"))
        first = witness((k,),EqTrans(specialize(t,"add_comm",k,j),t.hyp("equation")))
        second = witness((j,),t.hyp("equation"))
        def strict(a,proof):
            return apply(specialize(t,"le_trans",Succ(a),Succ(i),H),
                apply(specialize(t,"succ_le_succ",a,i),proof),t.hyp("bound"))
        return AndIntro(strict(j,first),strict(k,second))
    return introduce(s,("j","k","i","H"),("equation","bound"),finish)


def _term_transport(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def decoded(t):
        bounds = apply(specialize(t,"index_bounds",*t.terms(("j","k","i","H"))),field(t.hyp("data"),0,4),t.hyp("bound"))
        left = apply(specialize(t,"left",*t.terms(("j","a"))),AndElimL(bounds),field(t.hyp("data"),1,4))
        right = apply(specialize(t,"right",*t.terms(("k","b"))),AndElimR(bounds),field(t.hyp("data"),2,4))
        return witness(t.terms(("k","a","b")),conjunction(field(t.hyp("data"),0,4),left,right,field(t.hyp("data"),3,4)))
    return introduce(s,P+("j","v"),("left","right","bound","old"),lambda t:
        eliminate(t,t.hyp("old"),("k","a","b"),"data",decoded))


def _coefficient_transport(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR
    def decoded(t):
        def prefix(u):
            def entry(v):
                changed = apply(specialize(v,"term_transport",*v.terms(P+("j","v"))),
                    v.hyp("left"),v.hyp("right"),v.hyp("bound"),AndElimR(v.hyp("entry")))
                return witness((v.term("v"),),AndIntro(AndElimL(v.hyp("entry")),changed))
            actual = apply(instantiate(AndElimL(u.hyp("data")),u.term("j")),u.hyp("index"))
            return eliminate(u,actual,("v",),"entry",entry)
        return witness(t.terms(("xb","xc")),AndIntro(introduce(t,("j",),("index",),prefix),AndElimR(t.hyp("data"))))
    return introduce(s,P+("n",),("left","right","bound","old"),lambda t:
        eliminate(t,t.hyp("old"),("xb","xc"),"data",decoded))


def _root(s):
    from peano_lab.kernel.proofs import AndIntro
    def chosen(t):
        transported = apply(specialize(t,"coefficient_transport",*t.terms(P+("n",))),
            t.hyp("left"),t.hyp("right"),t.hyp("bound"),t.hyp("coefficient"))
        return witness((t.term("n"),),AndIntro(t.hyp("coefficient"),transported))
    return introduce(s,P,("left","right","bound"),lambda t:
        eliminate(t,specialize(t,"coefficient_exists",*t.terms(A+B+("i",))),("n",),"coefficient",chosen))


def prove_convolution_locality(*,limits=None):
    return assemble_mixed_certificate(code="CV050",target=frozen_convolution_locality_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"index_bounds":_index_bounds,"term_transport":_term_transport,"coefficient_transport":_coefficient_transport,"CV050":_root},
        pins=convolution_locality_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
