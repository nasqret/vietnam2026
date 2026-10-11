"""AP019: identify the actual finite log quotient with its odd Horner form.

Construct the odd coefficient slice, its base-nine value and actual power.
Pair the original base-three history and power, then prove equality of valid
rationals. Every denominator is proved positive; no real logarithm, infinite
sum identity or canonical primitive-recursive trace is asserted.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_atanh_odd_slice import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,atanh_odd_slice_source_pins,definition_registry as coefficient_registry,
    NAMED_SOURCE as SLICE_SOURCE,COMPOSITION_ARCHIVE,BOUND_ARCHIVE,_chain,_subst,
)
from sqrt2_power_paired_horner import (
    NAMED_SOURCE as HORNER_SOURCE,definition_registry as horner_registry,paired_horner_source_pins,INDEX_ARCHIVE,
)
from sqrt2_power_paired_power import NAMED_SOURCE as POWER_SOURCE,definition_registry as power_registry,paired_power_source_pins,COMPARISON_ARCHIVE
from sqrt2_power_fixed_precision_threshold import _ground_equal
from sqrt2_power_exp_two_sided_continuity import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-odd-horner-quotient-v1"
PARAMETERS=("d","ab","ac","k","x","p")
OUTPUTS=("bb","bc","y","q")
PREFIX="NatAtanhPrefix(d,ab,ac,S(2*k))"
VALUE="NatHornerValue(ab,ac,3,S(2*k),x)"
SLICE="NatAffineSlice(ab,ac,1,2,bb,bc,k)"
ODD="forall j a. Lt(j,k) -> BetaAt(bb,bc,j,a) -> (S(2*j))*a=2*d"
PARTS=(SLICE,"("+ODD+")","NatHornerValue(bb,bc,9,k,y)","Pow(9,k,q)","~q=0","~p=0",
    "x=3*y","p=3*q","IRatEq(3*x,0,d*p,3*y,0,d*q)")
def _and(parts):
    result=parts[-1]
    for part in reversed(parts[:-1]):
        result="("+part+" /\\ "+result+")"
    return result
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~d=0 -> "+PREFIX+" -> "+VALUE+" -> Pow(3,S(2*k),p) -> exists "+" ".join(OUTPUTS)+". "+_and(PARTS)
TARGET_SHA256="ef40bb286d66b9b7abd7a8521c7ef114b6ccba8d8780e5d0574178f985096c33"
HELPER_SOURCES={"nine_square":"3*3=9",
    "positive_eq":"forall a b d e. ~d=0 -> ~e=0 -> a*e=b*d -> IRatEq(a,0,d,b,0,e)",
    "quotient":"forall d p q x y. ~d=0 -> ~p=0 -> ~q=0 -> x=3*y -> p=3*q -> IRatEq(3*x,0,d*p,3*y,0,d*q)"}
HELPER_TARGET_SHA256={"nine_square":"28a0c64e236ea4346774a37b24be67765e53f9a03de242d07d298cf2ce384202",
    "positive_eq":"ebb8511015c6c8c2b1b1715c13f34ec6abc88be8851a2544407c5d0105bd10b6",
    "quotient":"90c9c246c31ec0f846fadaafbde4ebf5fe3490fd4b1f0114f7350d168abab098"}
HORNER_ARCHIVE=dict(case="AP017",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-paired-horner-v1/generation-process.json.gz",
    bytes=19060,sha256="4a930c9ad36841340d58d3cf325fa36fa987d751718cf480e8449dc0ed074eef",
    raw_bytes=166798,raw_sha256="d75666f09450819f49c2d4b0b7c4375d5850c6c798f6af127de533af056e26a6",
    bundle_bytes=62767,bundle_sha256="74390410057e6f52c8976706ee47906b16fb7699670d7602f3ac336bd25b2854",
    nodes=40,root=39,target_ast_sha256="5235c154de5a45ae307e0f3e33b64ea3ba043dd2efe3fdc302aa824d100fe5d9")
POWER_ARCHIVE=dict(case="AP018",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-paired-power-v1/generation-process.json.gz",
    bytes=32680,sha256="0b5174934441ce71e49ec59dc97cac2963201f7038beaf45da03ef351b55d93c",
    raw_bytes=205287,raw_sha256="831480dd66cb0fe1abe3a95d2275c79975e9c3b0f65a1072e407a6776922c70d",
    bundle_bytes=74072,bundle_sha256="84a656f636badc245aa0408832eadba4f4cdc185f95f94d4ba2e540ccdf4113d",
    nodes=27,root=26,target_ast_sha256="1c4010443924fa4b57d39c7f9952916050880d32d433ee211b5b5cef8a1a4f0f")
ARCHIVES=(INDEX_ARCHIVE,HORNER_ARCHIVE,POWER_ARCHIVE,COMPOSITION_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={"slice_exists":SLICE_SOURCE,"paired_horner":HORNER_SOURCE,"paired_power":POWER_SOURCE,
    "value_exists":"forall ab ac t H. exists y. NatHornerValue(ab,ac,t,H,y)",
    "power_exists":"forall a k. exists p. Pow(a,k,p)",
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0","mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0",
    "zero_mul":"forall a. 0*a=0","zero_add":"forall a. 0+a=a",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a"}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(slice_exists="AP016",paired_horner="AP017",paired_power="AP018",value_exists="CV061",power_exists="CV061",power_nonzero="AP010")
HELPER_DEPENDENCIES={"nine_square":(),"positive_eq":("zero_mul","zero_add"),
    "quotient":("positive_eq","mul_ne_zero","mul_assoc","mul_comm"),
    "AP019":("nine_square","quotient","slice_exists","paired_horner","paired_power","value_exists","power_exists","power_nonzero","succ_ne_zero")}


class OddHornerQuotientError(ValueError):
    """Changed actual odd computations, valid rational identity or positivity."""


def definition_registry():
    from sqrt2_power_definitions import DEFINITIONS
    result={};ids=set();identity=("stable_id","parameters","template_source","template_formula","conceptual_dependencies")
    for registry in (horner_registry(),coefficient_registry(),power_registry(),{name:DEFINITIONS[name] for name in ("IRatValid","IRatEq")}):
        for name,spec in registry.items():
            if name in result:
                if any(getattr(result[name],key)!=getattr(spec,key) for key in identity):
                    raise OddHornerQuotientError("shared odd-quotient definition disagreement")
                continue
            if spec.stable_id in ids or not set(spec.conceptual_dependencies)<=result.keys():
                raise OddHornerQuotientError("odd-quotient definition collision or forward dependency")
            result[name]=spec;ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_odd_horner_quotient_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise OddHornerQuotientError("AP019 exact finite odd-Horner rational target changed")
    return target


def source_contract():
    return dict(code="AP019",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,actual_supplied_prefix_horner_value_and_power_preserved=True,positive_coefficient_scale_required=True,
        actual_odd_slice_value_and_power_constructed=True,odd_quotient_equations_proved=True,
        all_rational_denominators_proved_nonzero=True,valid_rational_identity="3*x/(d*p)=3*y/(d*q)",
        value_identity="x=3*y",power_identity="p=3*q",odd_base=9,empty_odd_slice_allowed=True,
        new_definition_ids=[],reused_rational_definition_ids=["ND0382","ND0383"],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,infinite_odd_sum_identity_claim=False,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def odd_horner_quotient_source_pins():
    result=atanh_odd_slice_source_pins()
    for pins in (paired_horner_source_pins(),paired_power_source_pins()):
        for name,pin in pins.items():
            if name in result and result[name]!=pin:
                raise OddHornerQuotientError("odd-quotient source disagreement")
            result[name]=pin
    expected={"scripts/sqrt2_power_paired_horner.py":"fbc41ad5d91cc3fe8029dd93e487f4f5de29c7a2c493208421e247acf85396db",
        "scripts/sqrt2_power_paired_power.py":"ec9a3786e2c0d9820a9e0d332d155a2ea2242a79362c01bfd24895c3b8582068",
        "scripts/sqrt2_power_fixed_precision_threshold.py":"2135396cb60dc5e367407ad5a5328066d8e252e5ca58869adbac7d370080239f",
        "scripts/sqrt2_power_exp_two_sided_continuity.py":"8fd98e4b6733be1271387cf515dbf88ed4fabd48603a1169bd712b5385291086",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_odd_horner_quotient.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise OddHornerQuotientError("odd-quotient source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _positive_eq(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        a,b,d,e=t.terms(("a","b","d","e"));left,right=Mul(a,e),Mul(b,d)
        lnorm=_chain(CongAdd(EqRefl(left),specialize(t,"zero_mul",d)),instantiate(Axiom("PA3"),left))
        rnorm=_chain(CongAdd(specialize(t,"zero_mul",e),EqRefl(right)),specialize(t,"zero_add",right))
        return conjunction(t.hyp("d_nonzero"),t.hyp("e_nonzero"),_chain(lnorm,t.hyp("cross"),EqSym(rnorm)))
    return introduce(s,("a","b","d","e"),("d_nonzero","e_nonzero","cross"),finish)


def _quotient(s):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,parse_term
    three=parse_term("3")
    def finish(t):
        d,p,q,x,y=t.terms(("d","p","q","x","y"));dp,dq=Mul(d,p),Mul(d,q);a,b=Mul(three,x),Mul(three,y)
        left=Mul(Mul(three,Mul(three,y)),dq);right=Mul(b,Mul(d,Mul(three,q)))
        cross=_chain(CongMul(CongMul(EqRefl(three),t.hyp("values")),EqRefl(dq)),
            _multiplicative_equal(t,left,right),CongMul(EqRefl(b),CongMul(EqRefl(d),EqSym(t.hyp("powers")))))
        first=apply(specialize(t,"mul_ne_zero",d,p),t.hyp("d_nonzero"),t.hyp("p_nonzero"))
        second=apply(specialize(t,"mul_ne_zero",d,q),t.hyp("d_nonzero"),t.hyp("q_nonzero"))
        return apply(specialize(t,"positive_eq",a,b,dp,dq),first,second,cross)
    return introduce(s,("d","p","q","x","y"),("d_nonzero","p_nonzero","q_nonzero","values","powers"),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    two,three,eight,nine=(parse_term(source) for source in ("2","3","8","9"))
    def chosen(t):
        d,k,x,p,y,q=t.terms(("d","k","x","p","y","q"));data=t.hyp("slice_data")
        short=_subst(t,registry,"NatHornerValue(bb,bc,slot,k,y)",EqSym(t.hyp("nine_square")),t.hyp("odd_value"))
        short_power=_subst(t,registry,"Pow(slot,k,q)",EqSym(t.hyp("nine_square")),t.hyp("odd_power"))
        values=apply(specialize(t,"paired_horner",*t.terms(("ab","ac","bb","bc")),three,k,x,y),
            field(data,0,3),field(data,2,3),t.hyp("value"),short)
        powers=apply(specialize(t,"paired_power",three,k,p,q),t.hyp("power"),short_power)
        pnz=apply(instantiate(apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",two)),Succ(Mul(two,k)),p),t.hyp("power"))
        qnz=apply(instantiate(apply(specialize(t,"power_nonzero",nine),specialize(t,"succ_ne_zero",eight)),k,q),t.hyp("odd_power"))
        equal=apply(specialize(t,"quotient",d,p,q,x,y),t.hyp("nonzero"),pnz,qnz,values,powers)
        return witness(t.terms(OUTPUTS),conjunction(field(data,0,3),field(data,1,3),t.hyp("odd_value"),t.hyp("odd_power"),qnz,pnz,values,powers,equal))
    def sliced(t):
        return eliminate(t,specialize(t,"value_exists",*t.terms(("bb","bc")),nine,t.term("k")),("y",),"odd_value",lambda u:
            eliminate(u,specialize(u,"power_exists",nine,u.term("k")),("q",),"odd_power",chosen))
    return introduce(s,PARAMETERS,("nonzero","prefix","value","power"),lambda t:
        eliminate(t,apply(specialize(t,"slice_exists",*t.terms(("d","ab","ac","k"))),t.hyp("prefix")),("bb","bc"),"slice_data",sliced))


def prove_odd_horner_quotient(*,limits=None):
    from peano_lab.kernel.terms import parse_term
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP019",target=frozen_odd_horner_quotient_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"nine_square":lambda s:_ground_equal(parse_term("3*3"),parse_term("9")),"positive_eq":_positive_eq,"quotient":_quotient,"AP019":lambda s:_root(s,registry)},
        pins=odd_horner_quotient_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
