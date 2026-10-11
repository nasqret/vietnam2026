"""CV039: unconditionally construct the weighted-sum interpretation.

For every A,t,N construct geometric weights, their actual power witness,
coefficient-times-weight table, Horner trace, and common endpoint/sum value.
All table hypotheses of CV037 are supplied by checked constructors.
"""
from hashlib import sha256

from sqrt2_power_geometric_weights import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,geometric_weights_source_pins,
    NAMED_SOURCE as GEOMETRIC_SOURCE,INVARIANT,WEIGHTS_ARCHIVE,
    ENDPOINT_SOURCES as GEOMETRIC_ENDPOINTS,
)
from sqrt2_power_horner_weighted_sum import NAMED_SOURCE as SUM_SOURCE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive
from sqrt2_power_convolution_unit import _subst

SCHEMA = "sqrt2-power-constructed-horner-sum-v1"
A,W,Q,H,O = ("ab","ac"),("wb","wc"),("qb","qc"),("hb","hc"),("ob","oc")
OUTPUTS = W+("p",)+Q+H+("r",)
GEOMETRIC_DATA = "NatGeometricWeightTable(t,N,wb,wc) /\\ (Pow(t,N,p) /\\ (BetaAt(wb,wc,0,p) /\\ ("+INVARIANT+")))"


def prefix(codes,length="N"):
    return "NatHornerWeightedPrefix("+",".join(A+W+codes+(length,))+")"


NAMED_SOURCE = "forall ab ac t N. exists "+" ".join(OUTPUTS)+". ("+GEOMETRIC_DATA+") /\\ ("+prefix(Q)+" /\\ (NatScaledHornerTrace(ab,ac,t,N,hb,hc) /\\ (BetaAt(hb,hc,N,r) /\\ Sum(qb,qc,N,r))))"
TARGET_SHA256 = "04e9780ee714dda23598933ee36bc81764c56ad8b2edc3632b84e8161529ddf8"
HELPER_SOURCES = {
    "extend":"forall "+" ".join(A+W+("N",)+O)+". "+prefix(O)+" -> exists qb qc. "+prefix(Q,"S N"),
    "products_exists":"forall "+" ".join(A+W+("N",))+". exists qb qc. "+prefix(Q),
}
HELPER_TARGET_SHA256 = {
    "extend":"7d0155012f2bbb5ba459981bbbbc6432c54e9580cd3009b572564266d7accf3c",
    "products_exists":"05c9ff5b0f3c1295ca8d7d3aeb64448919be5b9f3fb5a6a5fab999992d52b9ca",
}
GEOMETRIC_ARCHIVE = dict(case="CV038",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-geometric-weights-v1/generation-process.json.gz",
    bytes=25086,sha256="9eae7fe079044ca76447f79eb13dcc6baaa4be0c342cc904479a87aabd4fef15",
    raw_bytes=399460,raw_sha256="d97888ed69fa5b5c5771037f0e72cfb40576b48f93116fb15428b50463842c8a",
    bundle_bytes=233337,bundle_sha256="18b213e913d77b5362b7f2b8bfe27f7969d2379affd7519141080407eb31caa8",
    nodes=123,root=122,target_ast_sha256="917e753656a45bbae99c1856843859780ffcc5d52d3d25e45991093293a278be")
SUM_ARCHIVE = dict(case="CV037",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-weighted-sum-v1/generation-process.json.gz",
    bytes=23675,sha256="67784fc49e84120dda6bba174ab2662c5672c1073f22ef7391960a10abb79995",
    raw_bytes=360562,raw_sha256="6d06db2816bd7d07f8210003a949c5278b3f34c8b423e53b20e15d37152629f6",
    bundle_bytes=210816,bundle_sha256="1f1e394ceee77030f4f8b71ae091f587e9815c47546e2ee674f699de2c8189c6",
    nodes=115,root=114,target_ast_sha256="6f5222fbdb659a953b151731a5f8b309685813f395efda3e55af160b5757bfd8")
ARCHIVES = (GEOMETRIC_ARCHIVE,SUM_ARCHIVE,WEIGHTS_ARCHIVE)
ENDPOINT_SOURCES = {name:GEOMETRIC_ENDPOINTS[name] for name in (
    "beta_exists","beta_unique","beta_extend","le_of_succ_le_succ","le_eq_or_lt","zero_le","lt_not_le")}
ENDPOINT_SOURCES.update(geometric_exists=GEOMETRIC_SOURCE,weighted_sum=SUM_SOURCE)
ENDPOINT_OWNERS = {name:"CV022" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(geometric_exists="CV038",weighted_sum="CV037")
HELPER_DEPENDENCIES = {
    "extend":("beta_exists","beta_unique","beta_extend","le_of_succ_le_succ","le_eq_or_lt"),
    "products_exists":("zero_le","lt_not_le","extend"),
    "CV039":("geometric_exists","products_exists","weighted_sum"),
}


class ConstructedHornerSumError(ValueError):
    """Changed same-witness finite sum, product constructor or proof data."""


def frozen_constructed_horner_sum_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=4 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConstructedHornerSumError("CV039 exact unconditional weighted sum construction changed")
    return target


def source_contract():
    return dict(code="CV039",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,geometric_weights_and_actual_power_constructed=True,
        weighted_product_prefix_constructed=True,horner_trace_and_endpoint_constructed=True,
        actual_sum_for_same_endpoint_proved=True,same_witnesses_preserved=True,
        zero_multiplier_and_empty_prefix_allowed=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        multiplication_evaluation_identity=False,analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def constructed_horner_sum_source_pins():
    result = geometric_weights_source_pins()
    expected = {"scripts/sqrt2_power_geometric_weights.py":"45c1407fd4c37f187e928babd9c3ad9772e9d3820b1ffcf98c342ac44b9012a9",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_constructed_horner_sum.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConstructedHornerSumError("constructed weighted sum source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _extend(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,CongS,EqSym,OrElim
    from peano_lab.kernel.terms import Mul,Succ
    def extended(t):
        def entry(u):
            def last(v):
                first = _subst(v,registry,"BetaAt(ab,ac,slot,a)",v.hyp("last"),v.hyp("first"))
                second = _subst(v,registry,"BetaAt(wb,wc,slot,b)",CongS(v.hyp("last")),v.hyp("second"))
                third = _subst(v,registry,"BetaAt(qb,qc,slot,c)",v.hyp("last"),v.hyp("third"))
                ax = apply(specialize(v,"beta_unique",*v.terms(A+("N","a","x"))),first,v.hyp("input"))
                by = apply(specialize(v,"beta_unique",*v.terms(W),Succ(v.term("N")),*v.terms(("b","y"))),second,v.hyp("weight"))
                product = Mul(v.term("x"),v.term("y"))
                equal = apply(specialize(v,"beta_unique",*v.terms(Q+("N","c")),product),third,AndElimL(v.hyp("extension")))
                return _chain(equal,CongMul(EqSym(ax),EqSym(by)))
            def earlier(v):
                def chosen(w):
                    preserved = apply(instantiate(AndElimR(w.hyp("extension")),*w.terms(("j","r"))),w.hyp("earlier"),w.hyp("old_entry"))
                    equal = apply(specialize(w,"beta_unique",*w.terms(Q+("j","c","r"))),w.hyp("third"),preserved)
                    product = apply(specialize(w,"old",*w.terms(("j","a","b","r"))),w.hyp("earlier"),w.hyp("first"),w.hyp("second"),w.hyp("old_entry"))
                    return _chain(equal,product)
                return eliminate(v,specialize(v,"beta_exists",*v.terms(O+("j",))),("r",),"old_entry",chosen)
            lower = apply(specialize(u,"le_of_succ_le_succ",*u.terms(("j","N"))),u.hyp("bound"))
            cases = apply(specialize(u,"le_eq_or_lt",*u.terms(("j","N"))),lower)
            return OrElim(cases,last(u.hypothesis("last")),earlier(u.hypothesis("earlier")))
        return witness(t.terms(Q),introduce(t,("j","a","b","c"),("bound","first","second","third"),entry))
    return introduce(s,A+W+("N",)+O,("old",),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(A+("N",))),("x",),"input",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(W),Succ(u.term("N"))),("y",),"weight",lambda v:
                eliminate(v,specialize(v,"beta_extend",v.term("N"),*v.terms(O),Mul(v.term("x"),v.term("y"))),Q,"extension",extended))))


def _products_exists(s,target):
    from peano_lab.kernel.proofs import BotElim,Ind
    from peano_lab.kernel.terms import Zero
    def base(t):
        empty = introduce(t,("j","a","b","c"),("bound","first","second","third"),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("j"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("j")))))
        return witness((Zero(),Zero()),empty)
    def successor(t):
        return eliminate(t,t.hyp("IH"),O,"old",lambda u:apply(specialize(u,"extend",*u.terms(A+W+("N",)+O)),u.hyp("old")))
    motive = target
    for _ in A+W+("N",):
        motive = motive.body
    return introduce(s,A+W,(),lambda t:Ind(motive,base(t),introduce(t,("N",),("IH",),successor)))


def _root(s):
    def weighted(t):
        source = apply(specialize(t,"weighted_sum",*t.terms(A+("t","N")+W+Q)),field(t.hyp("geometric"),0,4),t.hyp("products"))
        return eliminate(t,source,H+("r",),"evaluation",lambda u:
            witness(u.terms(OUTPUTS),conjunction(u.hyp("geometric"),u.hyp("products"),
                *(field(u.hyp("evaluation"),i,3) for i in range(3)))))
    return introduce(s,A+("t","N"),(),lambda t:
        eliminate(t,specialize(t,"geometric_exists",*t.terms(("t","N"))),W+("p",),"geometric",lambda u:
            eliminate(u,specialize(u,"products_exists",*u.terms(A+W+("N",))),Q,"products",weighted)))


def prove_constructed_horner_sum(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"extend":lambda s:_extend(s,registry),"products_exists":lambda s:_products_exists(s,parse_named(HELPER_SOURCES["products_exists"],registry=registry)),"CV039":_root}
    return assemble_mixed_certificate(code="CV039",target=frozen_constructed_horner_sum_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,
        pins=constructed_horner_sum_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
