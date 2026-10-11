"""CV074: construct and majorize the same full finite atanh-exp composition.

At base two retain the actual inner table, factorial weights, full power and
accumulation traces, row values, products and sum. Its normalization scale is
w0*2^J and the bound is s<=9*(w0*2^J). No limit or rational division occurs.
"""
from hashlib import sha256
import re

from sqrt2_power_weighted_monomial_recurrence import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,weighted_monomial_recurrence_source_pins,
    COMPOSITION_ARCHIVE,NAMED_SOURCE as WEIGHTED_SOURCE,
)
from sqrt2_power_full_composition_evaluation import (
    NAMED_SOURCE as COMPOSITION_SOURCE,PARTS as COMPOSITION_PARTS,
    OUTPUTS as COMPOSITION_OUTPUTS,conjoin,
)
from sqrt2_power_atanh_majorant import NAMED_SOURCE as INNER_SOURCE
from sqrt2_power_weight_factorials import NAMED_SOURCE as FACTORIAL_SOURCE,INVARIANT,positive
from sqrt2_power_normalized_composition import FACTORIAL_ARCHIVE
from sqrt2_power_scaled_exp_bound import HELPER_SOURCES as EXP_HELPERS,scaled_exp_bound_source_pins
from sqrt2_power_row_horner_values import HELPER_SOURCES as ROW_HELPERS
from sqrt2_power_geometric_horner import HELPER_SOURCES as GEOMETRIC_HELPERS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-composition-majorant-v1"
A,W,V,Z = ("ab","ac"),("wb","wc"),("vb","vc"),("zb","zc")
L,K,J = "S k","S N","((S N)*(S k))"
INNER_OUTPUTS = ("d",)+A+("y","q")
WEIGHT_OUTPUTS = W+("w0","f","dn")
OUTPUTS = ("d",)+A+("q",)+WEIGHT_OUTPUTS+COMPOSITION_OUTPUTS


def at_two(source):
    """Token-exact parameter specialization; named expansion is checked below."""
    replacements = {"L":L,"K":K,"J":J,"t":"2"}
    return re.sub(r"\b(?:L|K|J|t)\b",lambda m:replacements[m.group()],source)


INNER_PARTS = ("~d=0","NatAtanhPrefix(d,ab,ac,S k)","NatZeroBefore(ab,ac,S k,1)",
    "BetaAt(ab,ac,0,0)","NatBoundedPrefix(ab,ac,2*d,S k)","NatHornerValue(ab,ac,2,S k,x)",
    "Pow(2,k,q)","Le(x+2*d,(2*d)*q)")
WEIGHT_PARTS = ("NatExpWeightTable(d,N,wb,wc)",positive(W),"BetaAt(wb,wc,0,w0)",
    "Factorial(N,f)","Pow(d,N,dn)","w0=f*dn",INVARIANT,"~w0=0")
COMPOSITION_FIELDS = tuple(at_two(p) for p in COMPOSITION_PARTS)
BOUND_PARTS = ("~p=0","~v=0","~(d*p)=0","~(w0*v)=0","p=q*2",
    "Le(x,d*p)","Le(2*x,2*(d*p))","BetaAt(zb,zc,0,w0*v)",
    "NatScaledExpRecurrence(d*p,2*x,zb,zc,N)","Le(s,9*(w0*v))")
PARTS = INNER_PARTS+WEIGHT_PARTS+COMPOSITION_FIELDS+BOUND_PARTS
NAMED_SOURCE = "forall k N. exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256 = "0a0ef5814cf4d9655010b47abf33ab8cbcb9f86f7d6f336cafcc1a6d7556273b"
HELPER_SOURCES = {
    "inner_scale":"forall d k x q p. Pow(2,k,q) -> Pow(2,S k,p) -> Le(x+2*d,(2*d)*q) -> p=q*2 /\\ (Le(x,d*p) /\\ Le(2*x,2*(d*p)))",
}
HELPER_TARGET_SHA256 = {"inner_scale":"f608e12970528cf751185d56c932d3daf930d900a4d4c426378343f71b85027a"}
INNER_ARCHIVE = dict(case="CV066",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-atanh-majorant-v1/generation-process.json.gz",
    bytes=31431,sha256="46cf5210b7ebad3075d0379aad6ada4234d8a3024b65bd188420f0957c86431e",
    raw_bytes=487473,raw_sha256="0919c835a4702b2716aec1aae860950a5977bcaebb7471e946be25191e0fee40",
    bundle_bytes=271081,bundle_sha256="775e8f82cf01abe8eecd1022c91ab0a44028d1b97d0beab802cb5f75c272f81e",
    nodes=136,root=135,target_ast_sha256="b21b3f67a0aa28eb1456681cada027f47d5323c8f0b7e3c66defa64552756e5d")
BOUND_ARCHIVE = dict(case="CV071",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-scaled-exp-bound-v1/generation-process.json.gz",
    bytes=41887,sha256="b88209eab320263de81f11ec094df9df7577dea35d68d2c80aff0ab89f93354f",
    raw_bytes=801874,raw_sha256="5ced27637c67b2b3e7dca247978358557194700719a39cb80d3840f7ae75d4fc",
    bundle_bytes=462377,bundle_sha256="4d7e1dad4315320f229e167f800afa3ac7c13c3e5b338638e81bc06fb259ec32",
    nodes=163,root=162,target_ast_sha256="042906aaf5e07838dfb7be22391a4c26d6395af6e8d451e8c4322563fb810e26")
WEIGHTED_ARCHIVE = dict(case="CV073",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-weighted-monomial-recurrence-v1/generation-process.json.gz",
    bytes=30754,sha256="ec77a2e1c61fe568df8a68cd5a871d46652c0526f8b94d05d5c488c4f1b04429",
    raw_bytes=476572,raw_sha256="24efaa9f6a6a6dd595fa18f2b58e1b80562bfc382784298b98651a13b67cb378",
    bundle_bytes=261816,bundle_sha256="3365ad973b40bee6ffab11db7b582e17939db61a4768fd46c46adb6836b31d10",
    nodes=122,root=121,target_ast_sha256="e23d9c7bce72b64cec08978482e066d449fff7b4e18c3a1cfc5bc8dc55f9d6e5")
ARCHIVES = (COMPOSITION_ARCHIVE,INNER_ARCHIVE,FACTORIAL_ARCHIVE,BOUND_ARCHIVE,WEIGHTED_ARCHIVE)
ENDPOINT_SOURCES = {
    "inner_exists":INNER_SOURCE,"factorial_weights":FACTORIAL_SOURCE,
    "composition_exists":COMPOSITION_SOURCE,"weighted_recurrence":WEIGHTED_SOURCE,
    "finite_bound":EXP_HELPERS["all_values"],"value_unique":ROW_HELPERS["value_unique"],
    "power_nonzero":GEOMETRIC_HELPERS["power_nonzero"],
    "power_step":"forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d",
    "power_unique":"forall a n x y. Pow(a,n,x) -> Pow(a,n,y) -> x=y",
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
    "succ_ne_zero":"forall a. ~S a=0","zero_le":"forall a. Le(0,a)",
    "le_refl":"forall a. Le(a,a)","le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "add_comm":"forall a b. a+b=b+a",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(inner_exists="CV066",factorial_weights="CV030",weighted_recurrence="CV073",
    finite_bound="CV071",mul_left_mono="CV071",power_nonzero="CV073")
HELPER_DEPENDENCIES = {
    "inner_scale":("power_step","power_unique","le_trans","mul_left_mono","add_comm","mul_assoc","mul_comm"),
    "CV074":("inner_exists","factorial_weights","composition_exists","weighted_recurrence","finite_bound",
        "value_unique","inner_scale","power_nonzero","mul_ne_zero","succ_ne_zero","zero_le","le_refl"),
}


class CompositionMajorantError(ValueError):
    """Changed whole-support computation, scale or finite majorant."""


def frozen_composition_majorant_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=2 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CompositionMajorantError("CV074 exact actual finite composition majorant changed")
    return target


def source_contract():
    return dict(code="CV074",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_atanh_table_and_nonzero_denominator_constructed=True,
        actual_factorial_weight_table_and_normalization_constructed=True,
        whole_support_power_and_accumulation_traces_constructed=True,
        same_actual_row_values_products_sum_and_terminal_value=True,
        all_CV061_fields_retained_at_base_two=True,inner_length="k+1",outer_terms="N+1",
        whole_degree_bound="J=(N+1)*(k+1)",normalization="w0*v; v=2^J; w0=N!*d^N",
        nonzero_normalization_proved=True,inner_scale="p=q*2; q=2^k; p=2^(k+1)",
        exponential_recurrence_denominator="d*p",exponential_recurrence_numerator="2*x",
        finite_sum_bound="s<=9*(w0*v)",new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        rational_division_transport_claimed=False,analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def composition_majorant_source_pins():
    result = weighted_monomial_recurrence_source_pins()
    for name,pin in scaled_exp_bound_source_pins().items():
        if name in result and result[name]!=pin:
            raise CompositionMajorantError("composition majorant source pin disagreement")
        result[name] = pin
    expected = {"scripts/sqrt2_power_weighted_monomial_recurrence.py":"d98f897d995cf69bcbd286d659af57deadaadff9c058326468d909ab19c10456",
        "scripts/sqrt2_power_scaled_exp_bound.py":"717128c4845645cca66209b12512d4de2905d6ecc4eebad8c04c197647f9ee0c",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_composition_majorant.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CompositionMajorantError("composition majorant source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _inner_scale(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two = Succ(Succ(Zero()))
    def chosen(u):
        d,x,q,p,r = u.terms(("d","x","q","p","r"));dd = Mul(two,d);dp = Mul(d,p)
        same = apply(specialize(u,"power_unique",two,u.term("k"),r,q),AndElimL(u.hyp("step")),u.hyp("old_power"))
        peq = _chain(AndElimR(u.hyp("step")),CongMul(same,EqRefl(two)))
        dropped = apply(specialize(u,"le_trans",x,Add(x,dd),Mul(dd,q)),
            witness((dd,),specialize(u,"add_comm",dd,x)),u.hyp("inner_bound"))
        scale = _chain(_multiplicative_equal(u,Mul(dd,q),Mul(d,Mul(q,two))),CongMul(EqRefl(d),EqSym(peq)))
        bound = _subst(u,registry,"Le(x,slot)",scale,dropped)
        doubled = apply(specialize(u,"mul_left_mono",x,dp,two),bound)
        return conjunction(peq,bound,doubled)
    return introduce(s,("d","k","x","q","p"),("old_power","new_power","inner_bound"),lambda u:
        eliminate(u,apply(specialize(u,"power_step",two,u.term("k"),Succ(u.term("k")),u.term("p")),
            EqRefl(Succ(u.term("k"))),u.hyp("new_power")),("r",),"step",chosen))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two = Succ(Succ(Zero()))
    def chosen(u):
        inner,weights,comp = u.hyp("inner"),u.hyp("weights"),u.hyp("composition")
        d,w0,v,p,x,N,k = u.terms(("d","w0","v","p","x","N","k"));J = Mul(Succ(N),Succ(k))
        value = witness(u.terms(("ahb","ahc")),conjunction(field(comp,1,11),field(comp,2,11)))
        same = apply(specialize(u,"value_unique",*u.terms(A),two,Succ(k),u.term("y"),x),field(inner,5,8),value)
        inner_bound = _subst(u,registry,"Le(slot+2*d,(2*d)*q)",same,field(inner,7,8))
        scaled = apply(specialize(u,"inner_scale",d,k,x,*u.terms(("q","p"))),field(inner,6,8),field(comp,3,11),inner_bound)
        nz2 = specialize(u,"succ_ne_zero",Succ(Zero()))
        pnz = apply(instantiate(apply(specialize(u,"power_nonzero",two),nz2),Succ(k),p),field(comp,3,11))
        vnz = apply(instantiate(apply(specialize(u,"power_nonzero",two),nz2),J,v),field(comp,4,11))
        wnz = apply(instantiate(field(weights,1,7),Zero(),w0),specialize(u,"zero_le",N),field(weights,2,7),field(inner,0,8))
        dnz = apply(specialize(u,"mul_ne_zero",d,p),field(inner,0,8),pnz)
        initial_nz = apply(specialize(u,"mul_ne_zero",w0,v),wnz,vnz)
        rec = apply(specialize(u,"weighted_recurrence",d,p,two,x,v,N,*u.terms(W+V+Z+("w0",))),
            pnz,field(comp,10,11),field(weights,0,7),field(comp,7,11),field(weights,2,7))
        bound = apply(specialize(u,"finite_bound",Mul(d,p),Mul(two,x),N,*u.terms(Z),Mul(w0,v),u.term("s")),
            dnz,field(scaled,2,3),AndElimR(rec),AndElimL(rec),field(comp,8,11))
        first = tuple(field(inner,i,8) for i in range(5))+(value,field(inner,6,8),inner_bound)
        weight_fields = tuple(field(weights,i,7) for i in range(7))+(wnz,)
        last = (pnz,vnz,dnz,initial_nz,field(scaled,0,3),field(scaled,1,3),field(scaled,2,3),AndElimL(rec),AndElimR(rec),bound)
        return witness(u.terms(OUTPUTS),conjunction(*first,*weight_fields,*(field(comp,i,11) for i in range(11)),*last))
    def composition(u):
        J = Mul(Succ(u.term("N")),Succ(u.term("k")))
        return eliminate(u,apply(specialize(u,"composition_exists",*u.terms(A),Succ(u.term("k")),two,J,Succ(u.term("N")),*u.terms(W)),
            specialize(u,"le_refl",Succ(J))),COMPOSITION_OUTPUTS,"composition",chosen)
    return introduce(s,("k","N"),(),lambda u:
        eliminate(u,specialize(u,"inner_exists",u.term("k")),INNER_OUTPUTS,"inner",lambda v:
            eliminate(v,specialize(v,"factorial_weights",*v.terms(("d","N"))),WEIGHT_OUTPUTS,"weights",composition)))


def prove_composition_majorant(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV074",target=frozen_composition_majorant_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"inner_scale":lambda s:_inner_scale(s,registry),"CV074":lambda s:_root(s,registry)},
        pins=composition_majorant_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
