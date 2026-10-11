"""AP020: identify the finite logarithm quotient term by term.

Construct an actual natural sum whose normalized terms are exactly
2/((2*j+1)*3^(2*j+1)). Preserve AP019's input and output computations.
This is finite algebra, not a real logarithm identity or an accuracy axiom.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_odd_horner_quotient import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,odd_horner_quotient_source_pins,definition_registry as quotient_registry,
    NAMED_SOURCE as QUOTIENT_SOURCE,PARAMETERS,OUTPUTS as QUOTIENT_OUTPUTS,PARTS as QUOTIENT_PARTS,
    PREFIX,VALUE,ODD,_and,_chain,_subst,_multiplicative_equal,COMPOSITION_ARCHIVE,
    ENDPOINT_SOURCES as QUOTIENT_ENDPOINTS,HELPER_SOURCES as QUOTIENT_HELPERS,
)
from sqrt2_power_constructed_horner_sum import (
    NAMED_SOURCE as SUM_SOURCE,definition_registry as sum_registry,constructed_horner_sum_source_pins,
)
from sqrt2_power_horner_monomials import CONSTRUCTED_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-finite-odd-log-series-v1"
OUTPUTS=QUOTIENT_OUTPUTS+("tb","tc")
TERMS="forall j c. Lt(j,k) -> BetaAt(tb,tc,j,c) -> exists r. Pow(3,S(2*j),r) /\\ IRatEq(3*c,0,d*q,2,0,(S(2*j))*r)"
PARTS=QUOTIENT_PARTS+("Sum(tb,tc,k,y)","("+TERMS+")")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~d=0 -> "+PREFIX+" -> "+VALUE+" -> Pow(3,S(2*k),p) -> exists "+" ".join(OUTPUTS)+". "+_and(PARTS)
TARGET_SHA256="1d918aad2d021a46dc9e5a2a09b838014a15d6b30db745a7c4c5c0f2f8c34c20"
WEIGHT_INVARIANT="forall j w u. Le(j,k) -> BetaAt(wb,wc,j,w) -> Pow(9,j,u) -> w*u=q"
PRODUCTS="NatHornerWeightedPrefix(bb,bc,wb,wc,tb,tc,k)"
TERM_PARAMETERS=("d","bb","bc","k","q","wb","wc","tb","tc")
HELPER_SOURCES={
    "arithmetic":"forall d q a w u v r c i. ~d=0 -> ~q=0 -> ~r=0 -> ~i=0 -> i*a=2*d -> c=a*w -> u=v*9 -> w*u=q -> r=3*v -> IRatEq(3*c,0,d*q,2,0,i*r)",
    "terms":"forall "+" ".join(TERM_PARAMETERS)+". ~d=0 -> ~q=0 -> ("+ODD+") -> ("+WEIGHT_INVARIANT+") -> "+PRODUCTS+" -> "+TERMS,
}
HELPER_TARGET_SHA256={"arithmetic":"cf5e2c641ed8b196b99ec43cb8b8fb22c7143d72d682f3c502d08e87d67ae39e",
    "terms":"36eca1d8ea40195626b6ef318a926fafda4abb828817e982d8c133c057e1d267"}
QUOTIENT_ARCHIVE=dict(case="AP019",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-odd-horner-quotient-v1/generation-process.json.gz",
    bytes=50800,sha256="5c5ab53c4af4d88d2a8bd01bdc1c216e87203e7bb36552e3455a48191c44411b",
    raw_bytes=583628,raw_sha256="f876287912310c6d75ff45d31cac17165a15a23d3ef7ea5064b130d01efcfc31",
    bundle_bytes=310851,bundle_sha256="fd6d43b7cb41ce4722c57ebffffdde004e26d8fd5a289ffd74679af508db224a",
    nodes=142,root=141,target_ast_sha256="ef40bb286d66b9b7abd7a8521c7ef114b6ccba8d8780e5d0574178f985096c33")
ARCHIVES=(QUOTIENT_ARCHIVE,CONSTRUCTED_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={name:QUOTIENT_ENDPOINTS[name] for name in ("paired_power","power_nonzero","succ_ne_zero","mul_ne_zero","mul_assoc","mul_comm")}
ENDPOINT_SOURCES.update(odd_quotient=QUOTIENT_SOURCE,constructed_sum=SUM_SOURCE,nine_square=QUOTIENT_HELPERS["nine_square"],positive_eq=QUOTIENT_HELPERS["positive_eq"],
    beta_exists="forall b c i. exists a. BetaAt(b,c,i,a)",power_exists="forall a k. exists p. Pow(a,k,p)",
    power_step="forall a e se n. se=S e -> Pow(a,se,n) -> exists p. Pow(a,e,p) /\\ n=p*a",
    power_unique="forall a n x y. Pow(a,n,x) -> Pow(a,n,y) -> x=y",
    value_unique="forall ab ac t H x y. NatHornerValue(ab,ac,t,H,x) -> NatHornerValue(ab,ac,t,H,y) -> x=y")
ENDPOINT_OWNERS={name:"AP019" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(constructed_sum="CV039",beta_exists="CV061",power_exists="CV061",power_step="CV061",power_unique="CV061",value_unique="CV061")
HELPER_DEPENDENCIES={
    "arithmetic":("nine_square","positive_eq","mul_ne_zero","mul_assoc","mul_comm"),
    "terms":("arithmetic","beta_exists","power_exists","power_step","paired_power","nine_square","power_nonzero","succ_ne_zero"),
    "AP020":("odd_quotient","constructed_sum","value_unique","power_unique","terms"),
}


class FiniteOddLogSeriesError(ValueError):
    """Changed actual finite sum, odd term or denominator validity."""


def definition_registry():
    result=dict(quotient_registry());extra=sum_registry();needed=set();pending=["Sum","NatGeometricWeightTable","NatHornerWeightedPrefix"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(extra[name].conceptual_dependencies)
    ids={spec.stable_id for spec in result.values()}
    identity=("stable_id","parameters","template_source","template_formula","conceptual_dependencies")
    for name,spec in extra.items():
        if name not in needed:
            continue
        if name in result:
            if any(getattr(result[name],key)!=getattr(spec,key) for key in identity):
                raise FiniteOddLogSeriesError("shared finite-series definition disagreement")
            continue
        if spec.stable_id in ids or not set(spec.conceptual_dependencies)<=result.keys():
            raise FiniteOddLogSeriesError("finite-series definition collision or forward edge")
        result[name]=spec;ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_finite_odd_log_series_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FiniteOddLogSeriesError("AP020 exact finite odd-reciprocal sum target changed")
    return target


def source_contract():
    return dict(code="AP020",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,all_AP019_actual_computations_and_valid_rational_identity_preserved=True,
        actual_finite_term_table_and_sum_constructed=True,all_actual_terms_identified_with_odd_reciprocals=True,
        each_odd_denominator_power_constructed=True,all_rational_denominators_proved_nonzero=True,
        finite_series_reading="3*x/(d*p)=sum(j<k,2/((2*j+1)*3^(2*j+1)))",empty_sum_allowed=True,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_logarithm_identity_claim=False,
        analytic_limit_claim=False,original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def finite_odd_log_series_source_pins():
    result=odd_horner_quotient_source_pins()
    for name,pin in constructed_horner_sum_source_pins().items():
        if name in result and result[name]!=pin:
            raise FiniteOddLogSeriesError("finite-series source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_odd_horner_quotient.py":"2f646e44d68612e31791b15cc24e59c6c9d7ec47059e686a81a1a3fc963e7d0e",
        "scripts/sqrt2_power_constructed_horner_sum.py":"c0ee9f2e584ffa89201777e4b5f586b11832b5296199d11e8d8e4cb521800fbd",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_finite_odd_log_series.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FiniteOddLogSeriesError("finite-series source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,parse_term
    two,three=(parse_term(source) for source in ("2","3"))
    def finish(t):
        d,q,a,w,u,v,r,c,i=t.terms(("d","q","a","w","u","v","r","c","i"))
        ia=Mul(i,a);dq=Mul(d,q);ir=Mul(i,r);numerator=Mul(three,c)
        left=Mul(Mul(three,Mul(a,w)),Mul(i,Mul(three,v)))
        shuffled=Mul(ia,Mul(w,Mul(v,Mul(three,three))))
        cross=_chain(CongMul(CongMul(EqRefl(three),t.hyp("term")),CongMul(EqRefl(i),t.hyp("odd_power"))),
            _multiplicative_equal(t,left,shuffled),
            CongMul(EqRefl(ia),CongMul(EqRefl(w),CongMul(EqRefl(v),t.hyp("nine_square")))),
            CongMul(EqRefl(ia),CongMul(EqRefl(w),EqSym(t.hyp("next_power")))),
            CongMul(t.hyp("coefficient"),t.hyp("weight")),specialize(t,"mul_assoc",two,d,q))
        dnz=apply(specialize(t,"mul_ne_zero",d,q),t.hyp("d_nonzero"),t.hyp("q_nonzero"))
        enz=apply(specialize(t,"mul_ne_zero",i,r),t.hyp("i_nonzero"),t.hyp("r_nonzero"))
        return apply(specialize(t,"positive_eq",numerator,two,dq,ir),dnz,enz,cross)
    return introduce(s,("d","q","a","w","u","v","r","c","i"),
        ("d_nonzero","q_nonzero","r_nonzero","i_nonzero","coefficient","term","next_power","weight","odd_power"),finish)


def _terms(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    two,three,nine=(parse_term(source) for source in ("2","3","9"))
    def chosen(t):
        j=t.term("j");odd_index=Succ(Mul(two,j));previous=t.hyp("previous")
        squared=_subst(t,registry,"Pow(slot,j,v)",EqSym(t.hyp("nine_square")),AndElimL(previous))
        odd_power=apply(specialize(t,"paired_power",three,j,t.term("r"),t.term("v")),t.hyp("odd_denominator"),squared)
        rnz=apply(instantiate(apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",two)),odd_index,t.term("r")),t.hyp("odd_denominator"))
        coefficient=apply(instantiate(t.hyp("odd"),j,t.term("a")),t.hyp("below"),t.hyp("coefficient_entry"))
        product=apply(instantiate(t.hyp("products"),*t.terms(("j","a","w","c"))),t.hyp("below"),t.hyp("coefficient_entry"),t.hyp("weight_entry"),t.hyp("entry"))
        weight=apply(instantiate(t.hyp("invariant"),Succ(j),*t.terms(("w","u"))),t.hyp("below"),t.hyp("weight_entry"),t.hyp("successor_power"))
        equal=apply(specialize(t,"arithmetic",*t.terms(("d","q","a","w","u","v","r","c")),odd_index),
            t.hyp("d_nonzero"),t.hyp("q_nonzero"),rnz,specialize(t,"succ_ne_zero",Mul(two,j)),coefficient,product,AndElimR(previous),weight,odd_power)
        return witness((t.term("r"),),conjunction(t.hyp("odd_denominator"),equal))
    def successor(t):
        j=t.term("j")
        previous=apply(specialize(t,"power_step",nine,j,Succ(j),t.term("u")),EqRefl(Succ(j)),t.hyp("successor_power"))
        return eliminate(t,previous,("v",),"previous",lambda u:
            eliminate(u,specialize(u,"power_exists",three,Succ(Mul(two,u.term("j")))),("r",),"odd_denominator",chosen))
    def entry(t):
        return eliminate(t,specialize(t,"beta_exists",*t.terms(("bb","bc","j"))),("a",),"coefficient_entry",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(("wb","wc")),Succ(u.term("j"))),("w",),"weight_entry",lambda v:
                eliminate(v,specialize(v,"power_exists",nine,Succ(v.term("j"))),("u",),"successor_power",successor)))
    return introduce(s,TERM_PARAMETERS,("d_nonzero","q_nonzero","odd","invariant","products"),lambda t:
        introduce(t,("j","c"),("below","entry"),entry))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import parse_term
    nine=parse_term("9")
    def constructed(t):
        finite=t.hyp("finite_data");odd=t.hyp("odd_data")
        actual_value=witness(t.terms(("hb","hc")),conjunction(field(finite,2,5),field(finite,3,5)))
        same=apply(specialize(t,"value_unique",*t.terms(("bb","bc")),nine,*t.terms(("k","hv","y"))),actual_value,field(odd,2,9))
        total=_subst(t,registry,"Sum(tb,tc,k,slot)",same,field(finite,4,5))
        def invariant(u):
            geo=field(u.hyp("finite_data"),0,5);old=field(geo,3,4)
            product=apply(instantiate(old,*u.terms(("j","w","u"))),u.hyp("in_range"),u.hyp("weight"),u.hyp("power_at_index"))
            equal=apply(specialize(u,"power_unique",nine,*u.terms(("k","pw","q"))),field(geo,1,4),field(u.hyp("odd_data"),3,9))
            return _chain(product,equal)
        aligned=introduce(t,("j","w","u"),("in_range","weight","power_at_index"),invariant)
        terms=apply(specialize(t,"terms",*t.terms(TERM_PARAMETERS)),t.hyp("nonzero"),field(odd,4,9),field(odd,1,9),aligned,field(finite,1,5))
        return witness(t.terms(OUTPUTS),conjunction(*(field(odd,i,9) for i in range(9)),total,terms))
    def sliced(t):
        return eliminate(t,specialize(t,"constructed_sum",*t.terms(("bb","bc")),nine,t.term("k")),
            ("wb","wc","pw","tb","tc","hb","hc","hv"),"finite_data",constructed)
    return introduce(s,PARAMETERS,("nonzero","prefix","value","power"),lambda t:
        eliminate(t,apply(specialize(t,"odd_quotient",*t.terms(PARAMETERS)),t.hyp("nonzero"),t.hyp("prefix"),t.hyp("value"),t.hyp("power")),QUOTIENT_OUTPUTS,"odd_data",sliced))


def prove_finite_odd_log_series(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP020",target=frozen_finite_odd_log_series_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"arithmetic":_arithmetic,"terms":lambda s:_terms(s,registry),"AP020":lambda s:_root(s,registry)},
        pins=finite_odd_log_series_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
