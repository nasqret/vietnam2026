"""CV101: combine argument and truncation errors for actual exponential sums.

Compare A through degree m with B through degree m+N+1 at ordered arguments
x/d <= y/e <= 1. Their codes and initial scales may differ. The constructed
middle B-prefix connects CV098 and CV100. This is a uniform finite bound,
not an analytic limit or a definition containing the desired error estimate.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_cross_continuity import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,exp_cross_continuity_source_pins,
    NAMED_SOURCE as CROSS_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_truncation import NAMED_SOURCE as TRUNCATION_SOURCE,exp_truncation_source_pins
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-two-error-bound-v1"
A,B=("ab","ac"),("bb","bc")
PARAMETERS=("d","e","x","y","g","m","N")+A+B+("a0","b0","s","t","p")
PREMISES=("~d=0","~e=0","d*y=e*x+g","Le(y,e)",
    "NatScaledExpRecurrence(d,x,ab,ac,m)","NatScaledExpRecurrence(e,y,bb,bc,(S m)+N)",
    "BetaAt(ab,ac,0,a0)","BetaAt(bb,bc,0,b0)","Sum(ab,ac,S m,s)",
    "Sum(bb,bc,S((S m)+N),t)","Pow(2,m,p)")
NATURAL_CONCLUSION="Le(b0*s,a0*t) /\\ Le(D*(p*(a0*t)),D*(p*(b0*s))+(9*(g*p)+2*D)*(a0*b0))"
CONCLUSION=NATURAL_CONCLUSION.replace("D","(d*e)")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> "+CONCLUSION
TARGET_SHA256="99e2c67d567497309e07b57a9c96266fe4299a7a38f24bf605373710dc0b6857"
HELPER_SOURCES={
    "restrict":"forall d x ab ac M L. Le(M,L) -> NatScaledExpRecurrence(d,x,ab,ac,L) -> NatScaledExpRecurrence(d,x,ab,ac,M)",
    "arithmetic":"forall D g p a0 b0 s r t. Le(b0*s,a0*r) -> Le(D*(a0*r),D*(b0*s)+9*(g*(a0*b0))) -> Le(r,t) -> Le(p*t,p*r+2*b0) -> "+NATURAL_CONCLUSION,
}
HELPER_TARGET_SHA256={
    "restrict":"ec57f36ac35e2432d191c6ddb2693b83f2db10e1b93f4ab958f9bd8ea0b9a800",
    "arithmetic":"08fcb1d420009b0e080e3caea576effcde9b25274bf077e7971c633a3f336b5e",
}
CROSS_ARCHIVE=dict(case="CV098",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-cross-continuity-v1/generation-process.json.gz",
    bytes=41832,sha256="e99a84d84b18f3a03e441cf9f53377ad72f291af183d407136fed3387bc1bf92",
    raw_bytes=770001,raw_sha256="cf75130bb1c25e67fcd5d19190231c5bd54b296c0599532086c47feaef0101aa",
    bundle_bytes=445508,bundle_sha256="e4d094f2bd99f93d7c2951a5a03e735e0d7ba193e0b6c117d1385ed11a50bc8d",
    nodes=156,root=155,target_ast_sha256="cd70bc49ad3f8d993f61ab9ed4f3acc069f1cd0aac88b3f00bfd88e97d93da9c")
TRUNCATION_ARCHIVE=dict(case="CV100",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-truncation-v1/generation-process.json.gz",
    bytes=37715,sha256="268acca86f21ec99562c0190767bd55bc7ead00d5ff667be966b32b546458fb5",
    raw_bytes=676729,raw_sha256="8865dc9e3a2838b5fc819df4c7b1da1fc5634c8a20d3397cdd6dae714bd43989",
    bundle_bytes=385000,bundle_sha256="a8288777d6ca50ce713634fdda4f018996ec8ff25566bf936657bfb3630e1e5d",
    nodes=155,root=154,target_ast_sha256="38cc1a427fdb362d86fb580c3b3a939ae9e62900f35876de3390a804f26294b2")
ARCHIVES=(CROSS_ARCHIVE,TRUNCATION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "cross_continuity":CROSS_SOURCE,"truncation":TRUNCATION_SOURCE,
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "add_right_mono":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c","add_mul":"forall a b c. (a+b)*c=a*c+b*c",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)","add_comm":"forall a b. a+b=b+a",
    "add_succ_left":"forall a b. S a+b=S(a+b)",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b","one_mul":"forall a. 1*a=a",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(cross_continuity="CV098",truncation="CV100")
HELPER_DEPENDENCIES={
    "restrict":("le_trans",),
    "arithmetic":("mul_left_mono","add_right_mono","le_trans","mul_assoc","mul_comm","mul_add","add_mul","add_assoc"),
    "CV101":("cross_continuity","truncation","sum_exists","restrict","arithmetic","add_comm","add_succ_left","le_trans","mul_succ_left","one_mul"),
}


class ExpTwoErrorBoundError(ValueError):
    """Changed argument gap, independent data, finite horizons or either error."""


def frozen_exp_two_error_bound_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=16 or len(premises)!=11 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpTwoErrorBoundError("CV101 exact supplied two-error finite bound changed")
    return target


def source_contract():
    return dict(code="CV101",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=11,two_supplied_recurrences_heads_sums_and_cutoff_power_preserved=True,
        independent_argument_denominators_initial_scales_and_horizons=True,
        actual_middle_prefix_sum_constructed=True,argument_gap="d*y=e*x+g",argument_bound="y<=e",
        prefix_degree="m",whole_degree="m+N+1",cutoff_power="p=2^m",
        separated_formal_error="9*g/(d*e)+2/p",only_natural_cross_products_asserted=True,
        zero_arguments_gap_heads_cutoff_and_extra_horizon_allowed=True,new_induction_needed=False,
        code_number_equality_claimed=False,rational_validity_claimed=False,analytic_limit_claim=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def _recursive_source_pins():
    result=exp_cross_continuity_source_pins()
    for name,pin in exp_truncation_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpTwoErrorBoundError("two-error bound source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_cross_continuity.py":"df8ebc21517107b814a6f1e55903bb412d37a5b09917eeef6a47930b557b0bcd",
        "scripts/sqrt2_power_exp_truncation.py":"a54f7da9d8918d8bb7028a6694c9318aaae2cd04040f3d4513e5c4d09ff826c0",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_two_error_bound.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpTwoErrorBoundError("two-error source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


_PIN_EXPECTATIONS=None


def exp_two_error_bound_source_pins():
    """Avoid repeated diamond traversals, never repeated current-file checks.

    Only the immutable expected path/size/digest inventory is retained within
    this process. Every invocation rereads every actual file and rejects any
    mismatch. Actual proof bodies are independently decoded and replayed by
    assemble_mixed_certificate; this metadata cache grants no proof authority.
    """
    global _PIN_EXPECTATIONS
    if _PIN_EXPECTATIONS is None:
        expected=_recursive_source_pins()
        if any(set(pin)!={"bytes","sha256"} or type(pin["bytes"]) is not int or
                not 0<pin["bytes"]<=16*1024**2 for pin in expected.values()):
            raise ExpTwoErrorBoundError("invalid exact source inventory")
        _PIN_EXPECTATIONS=MappingProxyType({name:MappingProxyType(dict(pin)) for name,pin in expected.items()})
    result={}
    for name,pin in _PIN_EXPECTATIONS.items():
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(pin["bytes"]+1)
        if len(raw)!=pin["bytes"] or sha256(raw).hexdigest()!=pin["sha256"]:
            raise ExpTwoErrorBoundError("current source differs from exact source inventory")
        result[name]=dict(pin)
    return result


def _restrict(s):
    from peano_lab.kernel.terms import Succ
    def row(t):
        j,M,L=t.terms(("j","M","L"))
        bound=apply(specialize(t,"le_trans",Succ(j),M,L),t.hyp("bound"),t.hyp("horizon"))
        return apply(specialize(t,"recurrence",*t.terms(("j","a","b"))),bound,t.hyp("old"),t.hyp("new"))
    return introduce(s,("d","x")+A+("M","L"),("horizon","recurrence"),lambda t:
        introduce(t,("j","a","b"),("bound","old","new"),row))


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two=Succ(Succ(Zero()));nine=Zero()
    for _ in range(9):
        nine=Succ(nine)
    def finish(t):
        D,g,p,a0,b0,z,r,out=t.terms(("D","g","p","a0","b0","s","r","t"))
        ab=Mul(a0,b0);da=Mul(D,a0);bs=Mul(b0,z);ar=Mul(a0,r);at=Mul(a0,out)
        pr,pt=Mul(p,r),Mul(p,out)
        left=Mul(D,Mul(p,at));middle=Mul(D,Mul(p,ar));base=Mul(D,Mul(p,bs))
        ngp=Mul(nine,Mul(g,p));twoD=Mul(two,D);argument_error=Mul(ngp,ab);tail_error=Mul(twoD,ab)
        lower=apply(specialize(t,"le_trans",bs,ar,at),t.hyp("argument_lower"),
            apply(specialize(t,"mul_left_mono",r,out,a0),t.hyp("tail_lower")))
        tail=apply(specialize(t,"mul_left_mono",pt,Add(pr,Mul(two,b0)),da),t.hyp("tail_upper"))
        tail=_subst(t,registry,"Le(slot,(D*a0)*(p*r+2*b0))",_multiplicative_equal(t,Mul(da,pt),left),tail)
        right=_chain(specialize(t,"mul_add",da,pr,Mul(two,b0)),CongAdd(
            _multiplicative_equal(t,Mul(da,pr),middle),_multiplicative_equal(t,Mul(da,Mul(two,b0)),tail_error)))
        tail=_subst(t,registry,"Le(D*(p*(a0*t)),slot)",right,tail)
        old_left=Mul(D,ar);old_base=Mul(D,bs);old_error=Mul(nine,Mul(g,ab))
        argument=apply(specialize(t,"mul_left_mono",old_left,Add(old_base,old_error),p),t.hyp("argument_upper"))
        argument=_subst(t,registry,"Le(slot,p*(D*(b0*s)+9*(g*(a0*b0))))",
            _multiplicative_equal(t,Mul(p,old_left),middle),argument)
        right=_chain(specialize(t,"mul_add",p,old_base,old_error),CongAdd(
            _multiplicative_equal(t,Mul(p,old_base),base),_multiplicative_equal(t,Mul(p,old_error),argument_error)))
        argument=_subst(t,registry,"Le(D*(p*(a0*r)),slot)",right,argument)
        argument=apply(specialize(t,"add_right_mono",middle,Add(base,argument_error),tail_error),argument)
        upper=apply(specialize(t,"le_trans",left,Add(middle,tail_error),Add(Add(base,argument_error),tail_error)),tail,argument)
        combined=_chain(specialize(t,"add_assoc",base,argument_error,tail_error),
            CongAdd(EqRefl(base),EqSym(specialize(t,"add_mul",ngp,twoD,ab))))
        upper=_subst(t,registry,"Le(D*(p*(a0*t)),slot)",combined,upper)
        return conjunction(lower,upper)
    return introduce(s,("D","g","p","a0","b0","s","r","t"),("argument_lower","argument_upper","tail_lower","tail_upper"),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        d,e,x,y,g,m,N,a0,b0,z,out,p,r=t.terms(("d","e","x","y","g","m","N","a0","b0","s","t","p","r"))
        sm,sn=Succ(m),Succ(N);one=Succ(Zero());two=Succ(one);L=Add(sm,N)
        horizon=witness((sn,),_chain(specialize(t,"add_comm",sn,m),instantiate(Axiom("PA4"),m,N),
            EqSym(specialize(t,"add_succ_left",m,N))))
        prefix=apply(specialize(t,"restrict",e,y,*t.terms(B),m,L),horizon,t.hyp("recurrence_b"))
        twice=_chain(specialize(t,"mul_succ_left",one,e),CongAdd(specialize(t,"one_mul",e),EqRefl(e)))
        interval=apply(specialize(t,"le_trans",y,e,Mul(two,e)),t.hyp("argument"),witness((e,),EqSym(twice)))
        cross=apply(specialize(t,"cross_continuity",d,e,x,y,g,m,*t.terms(A+B),a0,b0,z,r),
            t.hyp("nonzero_d"),t.hyp("nonzero_e"),t.hyp("gap"),interval,t.hyp("recurrence_a"),prefix,
            t.hyp("head_a"),t.hyp("head_b"),t.hyp("prefix_a"),t.hyp("middle_sum"))
        tail=apply(specialize(t,"truncation",e,y,*t.terms(B),m,N,b0,r,out,p),t.hyp("nonzero_e"),t.hyp("argument"),
            t.hyp("recurrence_b"),t.hyp("head_b"),t.hyp("middle_sum"),t.hyp("whole_b"),t.hyp("power"))
        return apply(specialize(t,"arithmetic",Mul(d,e),g,p,a0,b0,z,r,out),AndElimL(cross),AndElimR(cross),AndElimL(tail),AndElimR(tail))
    return introduce(s,PARAMETERS,("nonzero_d","nonzero_e","gap","argument","recurrence_a","recurrence_b","head_a","head_b","prefix_a","whole_b","power"),lambda t:
        eliminate(t,specialize(t,"sum_exists",*t.terms(B),Succ(t.term("m"))),("r",),"middle_sum",chosen))


def prove_exp_two_error_bound(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV101",target=frozen_exp_two_error_bound_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"restrict":_restrict,"arithmetic":lambda s:_arithmetic(s,registry),"CV101":lambda s:_root(s,registry)},
        pins=exp_two_error_bound_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
