"""CV077: majorize and bound tails using supplied atanh and weight tables.

This bridge does not replace the caller's coefficient or weight codes.
It constructs the full composition from those codes, with the caller's
nonzero initial scale and all actual finite rational tail certificates.
"""
from hashlib import sha256

from sqrt2_power_composition_tail_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,composition_tail_bound_source_pins,
    MAJORANT_ARCHIVE,COMPOSITION_ARCHIVE,HELPER_SOURCES as TAIL_HELPERS,
    U,J,ROW,VALUE,SPECIALIZED_CUTS,conjoin,
)
from sqrt2_power_composition_majorant import INNER_ARCHIVE,BOUND_ARCHIVE,WEIGHTED_ARCHIVE,HELPER_SOURCES as SCALE_HELPERS,COMPOSITION_FIELDS
from sqrt2_power_atanh_majorant import HELPER_SOURCES as INNER_HELPERS
from sqrt2_power_full_composition_evaluation import NAMED_SOURCE as COMPOSITION_SOURCE,OUTPUTS as COMPOSITION_OUTPUTS
from sqrt2_power_weighted_monomial_recurrence import NAMED_SOURCE as RECURRENCE_SOURCE
from sqrt2_power_scaled_exp_bound import HELPER_SOURCES as BOUND_HELPERS
from sqrt2_power_geometric_horner import HELPER_SOURCES as GEOMETRIC_HELPERS
from sqrt2_power_row_horner_values import HELPER_SOURCES as ROW_HELPERS
from sqrt2_power_series_power_trace import HELPER_SOURCES as POWER_HELPERS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-supplied-composition-bound-v1"
A,W,V,Z = ("ab","ac"),("wb","wc"),("vb","vc"),("zb","zc")
PARAMETERS = ("d",)+A+("k","N")+W+("w0",)
OUTPUTS = ("q",)+COMPOSITION_OUTPUTS+U
PREMISES = ("~d=0","NatAtanhPrefix(d,ab,ac,S k)","NatExpWeightTable(d,N,wb,wc)","BetaAt(wb,wc,0,w0)","~w0=0")
EXTRA_PARTS = ("NatHornerValue(ab,ac,2,S k,x)","Pow(2,k,q)","Le(x+2*d,(2*d)*q)",
    "p=q*2","~p=0","~v=0","~(d*p)=0","~(w0*v)=0","BetaAt(zb,zc,0,w0*v)",
    "NatScaledExpRecurrence(d*p,2*x,zb,zc,N)","Le(s,9*(w0*v))",ROW,VALUE,SPECIALIZED_CUTS)
PARTS = COMPOSITION_FIELDS+EXTRA_PARTS
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256 = "e21e4c6b538bc01cb88d592709a53809b0e7e69f1048918f9661e0965cd5e421"
HELPER_SOURCES,HELPER_TARGET_SHA256 = {},{}
TAIL_BOUND_ARCHIVE = dict(case="CV076",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-composition-tail-bound-v1/generation-process.json.gz",
    bytes=106298,sha256="2aeb08cdd435d9896fb5cd8eb7249308d7546e71927ab04b23a4ad54fbd45aa8",
    raw_bytes=2986198,raw_sha256="14dd671883b377f9b0c563f13ef55299b2fab09c66e58cad9102cd8ce8d1c251",
    bundle_bytes=1824130,bundle_sha256="cf5c84b108e2db80fcaf846e709839e44402011c309e596c4b9c90c74560289e",
    nodes=336,root=335,target_ast_sha256="2baa8df68b336dc9d80d78e7f1d9797fdeb2859efc39377e00c1c0a18de9f83f")
ARCHIVES = (COMPOSITION_ARCHIVE,INNER_ARCHIVE,BOUND_ARCHIVE,WEIGHTED_ARCHIVE,MAJORANT_ARCHIVE,TAIL_BOUND_ARCHIVE)
ENDPOINT_SOURCES = {
    "inner_majorant":INNER_HELPERS["prefix_majorant"],"inner_scale":SCALE_HELPERS["inner_scale"],
    "composition_exists":COMPOSITION_SOURCE,"weighted_recurrence":RECURRENCE_SOURCE,
    "finite_bound":BOUND_HELPERS["all_values"],"all_tails":TAIL_HELPERS["for_value"],
    "value_unique":ROW_HELPERS["value_unique"],"row_decode":POWER_HELPERS["decode"],
    "power_nonzero":GEOMETRIC_HELPERS["power_nonzero"],
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
    "succ_ne_zero":"forall a. ~S a=0","le_refl":"forall a. Le(a,a)",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(inner_majorant="CV066",inner_scale="CV074",weighted_recurrence="CV073",
    finite_bound="CV071",all_tails="CV076",power_nonzero="CV073")
HELPER_DEPENDENCIES = {"CV077":tuple(ENDPOINT_SOURCES)}


class SuppliedCompositionBoundError(ValueError):
    """Changed supplied computation, normalization or actual tail witness."""


def frozen_supplied_composition_bound_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=8 or len(premises)!=5 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SuppliedCompositionBoundError("CV077 exact supplied-table composition bound changed")
    return target


def source_contract():
    return dict(code="CV077",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,supplied_atanh_and_weight_codes_preserved=True,supplied_nonzero_weight_head_required=True,
        actual_whole_support_composition_and_terminal_row_constructed=True,
        all_CV061_fields_retained_at_base_two=True,finite_sum_bound="s<=9*(w0*v)",
        every_in_range_actual_tail_bound="tail(1/3)/w0 <= 9*(2/3)^M",
        nonzero_denominators_proved=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        supplied_weight_table_replaced=False,factorial_normalization_constructed=False,
        empty_tail_case_claimed=False,analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def supplied_composition_bound_source_pins():
    result = composition_tail_bound_source_pins()
    expected = {"scripts/sqrt2_power_composition_tail_bound.py":"563cea09bbf3fe787bb8b2ffa6356f3e29fe7b3c6893abb5b2a08e14e4b0b9b3",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_supplied_composition_bound.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SuppliedCompositionBoundError("supplied composition source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two = Succ(Succ(Zero()))
    def chosen(t):
        inner,comp = t.hyp("inner"),t.hyp("composition")
        d,w0,v,p,x,N,k = t.terms(("d","w0","v","p","x","N","k"));J = Mul(Succ(N),Succ(k))
        value = witness(t.terms(("ahb","ahc")),conjunction(field(comp,1,11),field(comp,2,11)))
        same = apply(specialize(t,"value_unique",*t.terms(A),two,Succ(k),t.term("y"),x),field(inner,0,3),value)
        inner_bound = _subst(t,registry,"Le(slot+2*d,(2*d)*q)",same,field(inner,2,3))
        scaled = apply(specialize(t,"inner_scale",d,k,x,*t.terms(("q","p"))),field(inner,1,3),field(comp,3,11),inner_bound)
        nz2 = specialize(t,"succ_ne_zero",Succ(Zero()))
        pnz = apply(instantiate(apply(specialize(t,"power_nonzero",two),nz2),Succ(k),p),field(comp,3,11))
        vnz = apply(instantiate(apply(specialize(t,"power_nonzero",two),nz2),J,v),field(comp,4,11))
        dnz = apply(specialize(t,"mul_ne_zero",d,p),t.hyp("nonzero_d"),pnz)
        initial_nz = apply(specialize(t,"mul_ne_zero",w0,v),t.hyp("initial_nonzero"),vnz)
        rec = apply(specialize(t,"weighted_recurrence",d,p,two,x,v,N,*t.terms(W+V+Z+("w0",))),
            pnz,field(comp,10,11),t.hyp("weights"),field(comp,7,11),t.hyp("head"))
        bound = apply(specialize(t,"finite_bound",Mul(d,p),Mul(two,x),N,*t.terms(Z),Mul(w0,v),t.term("s")),
            dnz,field(scaled,2,3),AndElimR(rec),AndElimL(rec),field(comp,8,11))
        terminal_value = apply(instantiate(field(comp,9,11),*t.terms(U)),t.hyp("row"))
        tails = apply(specialize(t,"all_tails",*t.terms(U),J,*t.terms(("w0","s","v"))),
            t.hyp("initial_nonzero"),terminal_value,field(comp,4,11),bound)
        extra = (value,field(inner,1,3),inner_bound,field(scaled,0,3),pnz,vnz,dnz,initial_nz,
            AndElimL(rec),AndElimR(rec),bound,t.hyp("row"),terminal_value,tails)
        return witness(t.terms(OUTPUTS),conjunction(*(field(comp,i,11) for i in range(11)),*extra))
    def row(t):
        return eliminate(t,specialize(t,"row_decode",*t.terms(("rb","rc","sb","sc")),Succ(t.term("N"))),U,"row",chosen)
    def composition(t):
        J = Mul(Succ(t.term("N")),Succ(t.term("k")))
        return eliminate(t,apply(specialize(t,"composition_exists",*t.terms(A),Succ(t.term("k")),two,J,Succ(t.term("N")),*t.terms(W)),
            specialize(t,"le_refl",Succ(J))),COMPOSITION_OUTPUTS,"composition",row)
    return introduce(s,PARAMETERS,("nonzero_d","prefix","weights","head","initial_nonzero"),lambda t:
        eliminate(t,apply(specialize(t,"inner_majorant",*t.terms(("d",)+A+("k",))),t.hyp("prefix")),("y","q"),"inner",composition))


def prove_supplied_composition_bound(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV077",target=frozen_supplied_composition_bound_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"CV077":lambda s:_root(s,registry)},pins=supplied_composition_bound_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
