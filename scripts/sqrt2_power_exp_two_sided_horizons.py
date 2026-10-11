"""AP008: two-sided finite exponential errors across distinct horizons.

Construct the actual shorter sum of the supplied longer table. AP007 controls
the two input orders, CV100 its actual finite tail. All scales and the cutoff
power are retained. The statement is finite; it asserts no analytic limit.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_two_sided_continuity import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,canonical,json_hash,
    definition_registry as continuity_registry,exp_two_sided_continuity_source_pins,
    NAMED_SOURCE as CONTINUITY_SOURCE,_left,_right,_chain,_multiplicative_equal,
)
from sqrt2_power_exp_two_error_bound import (
    definition_registry as horizon_registry,exp_two_error_bound_source_pins,
    HELPER_SOURCES as HORIZON_HELPERS,TRUNCATION_SOURCE,
)
from sqrt2_power_exp_rational_two_error import TWO_ERROR_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-two-sided-horizons-v1"
PARAMETERS=("d","e","x","y","C","R","H","m","N","ab","ac","bb","bc","a0","b0","s","t","p")
PREMISES=("~d=0","~e=0","Le(x,d)","Le(y,e)","Le(C*(d*y),C*(e*x)+R)","Le(C*(e*x),C*(d*y)+H)",
    "NatScaledExpRecurrence(d,x,ab,ac,m)","NatScaledExpRecurrence(e,y,bb,bc,(S m)+N)",
    "BetaAt(ab,ac,0,a0)","BetaAt(bb,bc,0,b0)","Sum(ab,ac,S m,s)","Sum(bb,bc,S((S m)+N),t)","Pow(2,m,p)")
ARITHMETIC_CONCLUSION=("Le(p*(C*(D*(a0*t))),p*(C*(D*(b0*s)))+(9*(p*R)+2*(C*D))*(a0*b0)) /\\ "
    "Le(C*(D*(b0*s)),C*(D*(a0*t))+9*(H*(a0*b0)))")
CONCLUSION=ARITHMETIC_CONCLUSION.replace("D","(d*e)")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> "+CONCLUSION
TARGET_SHA256="345ef6c15b5813f3423a35a13c658fa76dd43b9bc8fc56f2aed0330e254c788a"
ARITHMETIC_PARAMETERS=("D","C","R","H","p","a0","b0","s","r","t")
ARITHMETIC_PREMISES=("Le(C*(D*(a0*r)),C*(D*(b0*s))+9*(R*(a0*b0)))",
    "Le(C*(D*(b0*s)),C*(D*(a0*r))+9*(H*(a0*b0)))","Le(r,t)","Le(p*t,p*r+2*b0)")
HELPER_SOURCES={"arithmetic":"forall "+" ".join(ARITHMETIC_PARAMETERS)+". "+" -> ".join(ARITHMETIC_PREMISES)+" -> "+ARITHMETIC_CONCLUSION}
HELPER_TARGET_SHA256={"arithmetic":"8667861303661d7b9b1b7080199cd553448800897c565c0774e654b85f3015bf"}
CONTINUITY_ARCHIVE=dict(case="AP007",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-two-sided-continuity-v1/generation-process.json.gz",
    bytes=44186,sha256="a7054532adf6a26abc55c5abef8c4c7aa7961699d2de5164336b3bba5bd5b0cb",
    raw_bytes=831759,raw_sha256="1126098f18ff1c50d381e6f36451f8daf3883df8144fbeba52a601e5e7a0225e",
    bundle_bytes=483848,bundle_sha256="147d7fa32b4cefb244f3a689bf9241c30b0170bc7eb867723c690751b82423bc",
    nodes=164,root=163,target_ast_sha256="d6c797957cd58e4b92514bcc10063e71045c1cdbe995aeeef3bff5020d434a11")
ARCHIVES=(CONTINUITY_ARCHIVE,TWO_ERROR_ARCHIVE)
ENDPOINT_SOURCES={
    "continuity":CONTINUITY_SOURCE,"truncation":TRUNCATION_SOURCE,"restrict":HORIZON_HELPERS["restrict"],
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "add_right_mono":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c","add_mul":"forall a b c. (a+b)*c=a*c+b*c",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)","add_comm":"forall a b. a+b=b+a",
    "add_succ_left":"forall a b. S a+b=S(a+b)",
}
ENDPOINT_OWNERS={name:"CV101" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["continuity"]="AP007"
HELPER_DEPENDENCIES={
    "arithmetic":("mul_left_mono","add_right_mono","le_trans","mul_assoc","mul_comm","mul_add","add_mul","add_assoc"),
    "AP008":("continuity","truncation","restrict","sum_exists","arithmetic","add_comm","add_succ_left"),
}


class ExpTwoSidedHorizonsError(ValueError):
    """Changed horizons, supplied sums, cutoff power or exact finite errors."""


def definition_registry():
    source=horizon_registry();needed=set(continuity_registry());pending=["Pow"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed}
    for name,spec in continuity_registry().items():
        if result[name]!=spec:
            raise ExpTwoSidedHorizonsError("shared finite recurrence definition differs")
    seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpTwoSidedHorizonsError("cutoff power definition dependency DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_two_sided_horizons_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=18 or len(premises)!=13 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpTwoSidedHorizonsError("AP008 exact two-sided unequal-horizon target changed")
    return target


def source_contract():
    return dict(code="AP008",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=13,both_supplied_recurrences_heads_sums_preserved=True,actual_shorter_sum_constructed=True,
        shorter_sum_uses_actual_longer_table=True,prefix_degree="m",whole_degree="m+N+1",actual_cutoff_power="p=2^m",
        common_error_multiplier_preserved=True,zero_error_multiplier_heads_and_extra_horizon_allowed=True,
        argument_monotonicity_assumed=False,independent_denominator_and_head_scales=True,
        rational_increase_reading="9*R/(C*d*e)+2/p",rational_decrease_reading="9*H/(C*d*e)",
        rational_reading_requires_separate_positivity=True,new_definition_ids=[],definition_admissions=0,
        new_induction_needed=False,analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_two_sided_horizons_source_pins():
    result=exp_two_sided_continuity_source_pins()
    for name,pin in exp_two_error_bound_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpTwoSidedHorizonsError("two-sided horizon source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_two_sided_continuity.py":"8fd98e4b6733be1271387cf515dbf88ed4fabd48603a1169bd712b5385291086",
        "scripts/sqrt2_power_exp_two_error_bound.py":"df3b14dbae9c98536321540ac43a1fd804550da8bb8a26a5bb0664f2a24e92d1",
        "scripts/sqrt2_power_exp_rational_two_error.py":"c30ca898c5180a608c49e7028a2bbb4ab8349979c8c4c6beb828d3b682cdfb65",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_two_sided_horizons.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpTwoSidedHorizonsError("two-sided horizon source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two=parse_term("2");nine=parse_term("9")
    def finish(t):
        D,C,R,H,p,a0,b0,u,r,v=t.terms(ARITHMETIC_PARAMETERS)
        cd=Mul(C,D);factor=Mul(cd,a0);heads=Mul(a0,b0)
        def value(z): return Mul(C,Mul(D,Mul(a0,z)))
        cr,ct=value(r),value(v);cs=Mul(C,Mul(D,Mul(b0,u)))
        pr,pt=Mul(p,r),Mul(p,v);left=Mul(p,ct);middle=Mul(p,cr);base=Mul(p,cs)
        arg_factor=Mul(nine,Mul(p,R));tail_factor=Mul(two,cd)
        argerr=Mul(arg_factor,heads);tailerr=Mul(tail_factor,heads)
        # The actual longer-table tail, multiplied by the common scale.
        tail=apply(specialize(t,"mul_left_mono",pt,Add(pr,Mul(two,b0)),factor),t.hyp("tail_upper"))
        tail=_left(t,registry,tail,Mul(factor,Add(pr,Mul(two,b0))),_multiplicative_equal(t,Mul(factor,pt),left))
        expanded=_chain(specialize(t,"mul_add",factor,pr,Mul(two,b0)),CongAdd(
            _multiplicative_equal(t,Mul(factor,pr),middle),_multiplicative_equal(t,Mul(factor,Mul(two,b0)),tailerr)))
        tail=_right(t,registry,tail,left,expanded)
        # The possible same-degree increase, with its independent error R.
        olderr=Mul(nine,Mul(R,heads))
        argument=apply(specialize(t,"mul_left_mono",cr,Add(cs,olderr),p),t.hyp("argument_upper"))
        expanded=_chain(specialize(t,"mul_add",p,cs,olderr),CongAdd(EqRefl(base),_multiplicative_equal(t,Mul(p,olderr),argerr)))
        argument=_right(t,registry,argument,middle,expanded)
        argument=apply(specialize(t,"add_right_mono",middle,Add(base,argerr),tailerr),argument)
        upper=apply(specialize(t,"le_trans",left,Add(middle,tailerr),Add(Add(base,argerr),tailerr)),tail,argument)
        combined=_chain(specialize(t,"add_assoc",base,argerr,tailerr),CongAdd(EqRefl(base),EqSym(specialize(t,"add_mul",arg_factor,tail_factor,heads))))
        upper=_right(t,registry,upper,left,combined)
        # Increasing the horizon cannot worsen the opposite-direction error.
        lower=apply(specialize(t,"mul_left_mono",r,v,factor),t.hyp("tail_lower"))
        lower=_left(t,registry,lower,Mul(factor,v),_multiplicative_equal(t,Mul(factor,r),cr))
        lower=_right(t,registry,lower,cr,_multiplicative_equal(t,Mul(factor,v),ct))
        backerr=Mul(nine,Mul(H,heads))
        lower=apply(specialize(t,"add_right_mono",cr,ct,backerr),lower)
        lower=apply(specialize(t,"le_trans",cs,Add(cr,backerr),Add(ct,backerr)),t.hyp("argument_lower"),lower)
        return conjunction(upper,lower)
    return introduce(s,ARITHMETIC_PARAMETERS,("argument_upper","argument_lower","tail_lower","tail_upper"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def chosen(t):
        d,e,x,y,C,R,H,m,N,ab,ac,bb,bc,a0,b0,u,v,p=t.terms(PARAMETERS);r=t.term("r");L=Add(Succ(m),N)
        horizon=witness((Succ(N),),_chain(specialize(t,"add_comm",Succ(N),m),instantiate(Axiom("PA4"),m,N),EqSym(specialize(t,"add_succ_left",m,N))))
        prefix=apply(specialize(t,"restrict",e,y,bb,bc,m,L),horizon,t.hyp("recurrence_b"))
        cross=apply(specialize(t,"continuity",d,e,x,y,C,R,H,m,ab,ac,bb,bc,a0,b0,u,r),
            *(t.hyp(n) for n in ("d_nonzero","e_nonzero","bound_a","bound_b","forward","backward")),
            t.hyp("recurrence_a"),prefix,t.hyp("head_a"),t.hyp("head_b"),t.hyp("sum_a"),t.hyp("middle_sum"))
        tail=apply(specialize(t,"truncation",e,y,bb,bc,m,N,b0,r,v,p),t.hyp("e_nonzero"),t.hyp("bound_b"),
            t.hyp("recurrence_b"),t.hyp("head_b"),t.hyp("middle_sum"),t.hyp("sum_b"),t.hyp("power"))
        return apply(specialize(t,"arithmetic",Mul(d,e),C,R,H,p,a0,b0,u,r,v),AndElimL(cross),AndElimR(cross),AndElimL(tail),AndElimR(tail))
    return introduce(s,PARAMETERS,("d_nonzero","e_nonzero","bound_a","bound_b","forward","backward",
        "recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b","power"),lambda t:
        eliminate(t,specialize(t,"sum_exists",*t.terms(("bb","bc")),Succ(t.term("m"))),("r",),"middle_sum",chosen))


def prove_exp_two_sided_horizons(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP008",target=frozen_exp_two_sided_horizons_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"arithmetic":lambda s:_arithmetic(s,registry),"AP008":_root},
        pins=exp_two_sided_horizons_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
