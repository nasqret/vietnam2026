"""CV061: same-witness finite composition evaluation and power monomials.

Combine whole-support powers with their actual weighted accumulation and sum.
The row-value table's entries satisfy the exact denominator-cleared monomial
law. This is still finite algebra, not an exponential or convergence theorem.
"""
from hashlib import sha256

from sqrt2_power_weighted_accumulation_evaluation import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,weighted_accumulation_evaluation_source_pins,
    NAMED_SOURCE as ACCUMULATION_SOURCE,
)
from sqrt2_power_finite_power_evaluation import (
    NAMED_SOURCE as POWER_SOURCE,HELPER_SOURCES as POWER_HELPERS,
)
from sqrt2_power_row_horner_values import EVALUATION_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-full-composition-evaluation-v1"
A,P,HA = ("ab","ac","L"),("pb","pc","qb","qc"),("ahb","ahc")
W,R,V,Z = ("wb","wc"),("rb","rc","sb","sc"),("vb","vc"),("zb","zc")
U,HU = ("ub","uc"),("uhb","uhc")
PARAMETERS = A+("t","J","K")+W
POWER_OUTPUTS = P+HA+("x","p","v")
ACCUMULATION_OUTPUTS = R+V+Z+("s",)
OUTPUTS = POWER_OUTPUTS+ACCUMULATION_OUTPUTS
FIXED = A+("t","J","K")+POWER_OUTPUTS+V
WIDTH = "Le(S(K*L),S J)"
POWER_TRACE = "NatPowerTrace(ab,ac,L,S J,pb,pc,qb,qc,K)"
INPUT_TRACE = "NatScaledHornerTrace(ab,ac,t,L,ahb,ahc)"
ROW_VALUES = "NatRowHornerPrefix(pb,pc,qb,qc,t,S J,vb,vc,K)"
ACCUMULATION_TRACE = "NatWeightedSeriesTrace(S J,wb,wc,pb,pc,qb,qc,rb,rc,sb,sc,K)"
PRODUCTS = "NatPointwiseProductPrefix(wb,wc,vb,vc,zb,zc,K)"
FINAL = "forall ub uc. NatPowerRow(rb,rc,sb,sc,K,ub,uc) -> NatHornerValue(ub,uc,t,S J,s)"
MONOMIALS = "forall k y a b c. Lt(k,K) -> BetaAt(vb,vc,k,y) -> Pow(p,k,a) -> Pow(t,k,b) -> Pow(x,k,c) -> a*y=(v*b)*c"
PARTS = (POWER_TRACE,INPUT_TRACE,"BetaAt(ahb,ahc,L,x)","Pow(t,L,p)","Pow(t,J,v)",
    ACCUMULATION_TRACE,ROW_VALUES,PRODUCTS,"Sum(zb,zc,K,s)",FINAL,MONOMIALS)


def conjoin(parts):
    return parts[0] if len(parts)==1 else "("+parts[0]+") /\\ ("+conjoin(parts[1:])+")"


NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+WIDTH+" -> exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256 = "574be3227d697f0533ee581f7baa664dcfca27230214e8992f1bab97fe4e3aaf"
HELPER_SOURCES = {
    "monomials":"forall "+" ".join(FIXED)+". "+" -> ".join((WIDTH,POWER_TRACE,INPUT_TRACE,"BetaAt(ahb,ahc,L,x)","Pow(t,L,p)","Pow(t,J,v)",ROW_VALUES,MONOMIALS)),
}
HELPER_TARGET_SHA256 = {"monomials":"746d15f2b26c6e4535767c54659caa91fc271be024ab46e5fd859969c5655b96"}
ACCUMULATION_ARCHIVE = dict(case="CV060",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-weighted-accumulation-evaluation-v1/generation-process.json.gz",
    bytes=35569,sha256="62c6a6a73f6d346f9ad38770d477d01b7a0619ad8ab40a99fe369ffeecc73486",
    raw_bytes=635906,raw_sha256="5edc637f3fdf9535cb04e68187e7a38908878e7a37cccc36d7c4863163719887",
    bundle_bytes=364611,bundle_sha256="9689e059b662da007e17f7ce588f1b8b57f671eca5beac3f9842410bc00e0fe5",
    nodes=137,root=136,target_ast_sha256="f1e9ea342059786ba3af115a2f4d0613913410b92f8bc7dbd138144349c3b7b4")
ARCHIVES = (EVALUATION_ARCHIVE,ACCUMULATION_ARCHIVE)
ENDPOINT_SOURCES = {
    "power_evaluation":POWER_SOURCE,"all_power_rows":POWER_HELPERS["all_rows"],
    "accumulation_evaluation":ACCUMULATION_SOURCE,
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
}
ENDPOINT_OWNERS = {name:"CV058" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["accumulation_evaluation"] = "CV060"
HELPER_DEPENDENCIES = {
    "monomials":("beta_unique","all_power_rows","le_refl","le_succ","le_trans"),
    "CV061":("power_evaluation","accumulation_evaluation","monomials"),
}


class FullCompositionEvaluationError(ValueError):
    """Changed same-witness composition, support bound or monomial scaling."""


def frozen_full_composition_evaluation_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=8 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FullCompositionEvaluationError("CV061 exact same-witness composition target changed")
    return target


def source_contract():
    return dict(code="CV061",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,support_complete_width="1+K*L <= J+1",same_actual_power_trace_used_by_accumulation=True,
        actual_input_value_scaling_powers_row_values_products_and_sum_constructed=True,
        all_row_value_entries_have_exact_power_identity=True,every_terminal_row_evaluates_to_same_sum=True,
        zero_multiplier_and_empty_input_allowed=True,no_nonzero_factor_cancelled=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def full_composition_evaluation_source_pins():
    result = weighted_accumulation_evaluation_source_pins()
    expected = {"scripts/sqrt2_power_weighted_accumulation_evaluation.py":"464f6bf6c392132d50a3eeeea49554d51e15763ed064908c3bd4d4993d36e0fd",
        "scripts/sqrt2_power_finite_power_evaluation.py":"6c7c7cab1eceb7d10dcfa678ffa9f7245e4a197d966ee3050d547cf5ff804fac",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_full_composition_evaluation.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FullCompositionEvaluationError("full composition source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _monomials(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        def evaluated(u):
            bound = apply(specialize(u,"le_trans",u.term("k"),Succ(u.term("k")),u.term("K")),
                apply(specialize(u,"le_succ",*u.terms(("k","k"))),specialize(u,"le_refl",u.term("k"))),u.hyp("bound"))
            same = apply(specialize(u,"beta_unique",*u.terms(V+("k","z","y"))),field(u.hyp("row_data"),2,3),u.hyp("entry"))
            endpoint = _subst(u,registry,"BetaAt(uhb,uhc,S J,slot)",same,AndElimR(u.hyp("value_data")))
            invariant = apply(specialize(u,"all_power_rows",*u.terms(A+("t","J","K")+POWER_OUTPUTS)),
                u.hyp("width"),u.hyp("trace"),u.hyp("input_trace"),u.hyp("input_value"),u.hyp("power_p"),u.hyp("power_v"))
            return apply(instantiate(invariant,*u.terms(("k",)+U+HU+("y","a","b","c"))),bound,
                field(u.hyp("row_data"),0,3),AndElimL(u.hyp("value_data")),endpoint,u.hyp("power_a"),u.hyp("power_b"),u.hyp("power_c"))
        return eliminate(t,field(t.hyp("row_data"),1,3),HU,"value_data",evaluated)
    return introduce(s,FIXED,("width","trace","input_trace","input_value","power_p","power_v","row_values"),lambda t:
        introduce(t,("k","y","a","b","c"),("bound","entry","power_a","power_b","power_c"),lambda u:
            eliminate(u,apply(specialize(u,"row_values",u.term("k")),u.hyp("bound")),U+("z",),"row_data",chosen)))


def _root(s):
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        monomials = apply(specialize(t,"monomials",*t.terms(FIXED)),t.hyp("width"),
            *(field(t.hyp("powers"),i,6) for i in range(5)),field(t.hyp("accumulation"),1,5))
        return witness(t.terms(OUTPUTS),conjunction(*(field(t.hyp("powers"),i,6) for i in range(5)),
            *(field(t.hyp("accumulation"),i,5) for i in range(5)),monomials))
    return introduce(s,PARAMETERS,("width",),lambda t:
        eliminate(t,apply(specialize(t,"power_evaluation",*t.terms(A+("t","J","K"))),t.hyp("width")),POWER_OUTPUTS,"powers",lambda u:
            eliminate(u,specialize(u,"accumulation_evaluation",Succ(u.term("J")),*u.terms(("t",)+W+P+("K",))),ACCUMULATION_OUTPUTS,"accumulation",chosen)))


def prove_full_composition_evaluation(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV061",target=frozen_full_composition_evaluation_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"monomials":lambda s:_monomials(s,registry),"CV061":_root},
        pins=full_composition_evaluation_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
