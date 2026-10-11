"""CV088: effective cutoff decay for an actual supplied finite exp tail.

Construct p=2^m and the slice from m+1. Prove p*first<=head and
p*sum<=2*head for every finite extra horizon. The output is finite data,
not an infinite sum or a hidden convergence assumption.
"""
from hashlib import sha256

from sqrt2_power_scaled_exp_tail import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,scaled_exp_tail_source_pins,
    NAMED_SOURCE as TAIL_SOURCE,HELPER_SOURCES as TAIL_HELPERS,
    ENDPOINT_SOURCES as TAIL_ENDPOINTS,COMPOSITION_ARCHIVE,BOUND_ARCHIVE,RECURRENCE,SLICE,RATIO,
)
from sqrt2_power_horner_base_comparison import HELPER_SOURCES as ORDER_HELPERS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-scaled-exp-tail-decay-v1"
T,U = ("tb","tc"),("ub","uc")
PARAMETERS = ("d","x")+T+("m","N","a0")
OUTPUTS = ("p",)+U+("a","s")
FIXED = ("d","x","L")+T+("a0",)
PARTS = ("Pow(2,m,p)","BetaAt(tb,tc,S m,a)",SLICE,RATIO,"Sum(ub,uc,S N,s)","Le(p*a,a0)","Le(p*s,2*a0)")


def conjoin(parts):
    result=parts[-1]
    for part in reversed(parts[:-1]):
        result=part+" /\\ ("+result+")"
    return result


NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". ~d=0 -> Le(x,d) -> "+RECURRENCE+" -> BetaAt(tb,tc,0,a0) -> exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256 = "76d2878ab4276b62e8094e3b25956fc0b58fec9c0d936f9c3af4c253fe8cc5ba"
DECAY = "forall k a p. Le(S k,L) -> BetaAt(tb,tc,S k,a) -> Pow(2,k,p) -> Le(p*a,a0)"
HELPER_SOURCES = {
    "term_decay":"forall "+" ".join(FIXED)+". ~d=0 -> Le(x,d) -> NatScaledExpRecurrence(d,x,tb,tc,L) -> BetaAt(tb,tc,0,a0) -> "+DECAY,
    "scaled_sum":"forall p s a a0. Le(p*a,a0) -> Le(s,2*a) -> Le(p*s,2*a0)",
}
HELPER_TARGET_SHA256 = {
    "term_decay":"aefc646669d73ffcb830075dc881bee0f552dd1561a5b94e5232541fedcb4249",
    "scaled_sum":"2f6cc84c943db29fa765d80905a495a1d55f238309b706bd852024cdb60ecbd4",
}
TAIL_ARCHIVE = dict(case="CV087",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-scaled-exp-tail-v1/generation-process.json.gz",
    bytes=30382,sha256="3d067d9e12497f0e8d1acb79233a53738e0d63ff29c4d36b2bd1040861ba2600",
    raw_bytes=405942,raw_sha256="f0603025a85bf1c7b1158c1d3c8a8858f6cfbd3e2a91babf277ee82e9ac97fd5",
    bundle_bytes=216846,bundle_sha256="842b94791215ff765f03bf71b15cffbb29af38eece82ed279ea1f9636bb90d30",
    nodes=121,root=120,target_ast_sha256="d92d8780097ceaf3810aba46e31ffe2e3c8357929685f8314972342821425d8b")
ARCHIVES = (TAIL_ARCHIVE,COMPOSITION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES = {name:TAIL_ENDPOINTS[name] for name in (
    "beta_exists","le_trans","one_mul","zero_le","le_succ","succ_le_succ","mul_assoc","mul_comm")}
ENDPOINT_SOURCES.update(tail_exists=TAIL_SOURCE,ratio=TAIL_HELPERS["ratio"],
    mul_left_mono=ORDER_HELPERS["mul_left_mono"],le_refl="forall a. Le(a,a)",
    add_comm="forall a b. a+b=b+a",
    power_zero="forall d n p. n=0 -> Pow(d,n,p) -> p=1",
    power_step="forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d",
    power_exists="forall d n. exists p. Pow(d,n,p)")
ENDPOINT_OWNERS = {name:"CV087" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(power_zero="CV061",power_step="CV061",power_exists="CV061",mul_left_mono="CV071")
HELPER_DEPENDENCIES = {
    "term_decay":("ratio","power_zero","power_step","beta_exists","le_refl","le_succ","le_trans","one_mul","mul_left_mono","zero_le","succ_le_succ","mul_assoc"),
    "scaled_sum":("mul_left_mono","mul_assoc","mul_comm","le_trans"),
    "CV088":("power_exists","beta_exists","tail_exists","term_decay","scaled_sum","add_comm"),
}


class ScaledExpTailDecayError(ValueError):
    """Changed uniform finite tail, supplied computation or actual cutoff power."""


def frozen_scaled_exp_tail_decay_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=7 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ScaledExpTailDecayError("CV088 exact cutoff-decaying finite tail changed")
    return target


def source_contract():
    return dict(code="CV088",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,supplied_term_table_and_initial_scale_preserved=True,
        actual_power_first_omitted_term_slice_ratio_and_sum_constructed=True,
        cutoff="m+1",power="p=2^m",tail_length="N+1",first_term_bound="p*a<=a0",tail_sum_bound="p*s<=2*a0",
        uniform_in_extra_finite_horizon=True,nonzero_denominator_required=True,argument_bound="x<=d",
        zero_argument_and_zero_extra_horizon_allowed=True,infinite_remainder_claimed=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_limit_claim=False,
        closes_IR072=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def scaled_exp_tail_decay_source_pins():
    result=scaled_exp_tail_source_pins()
    expected={"scripts/sqrt2_power_scaled_exp_tail.py":"df81a3c92b26346a1955ba92e763d932201649183604309f17bd156b2abbaeb3",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_scaled_exp_tail_decay.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ScaledExpTailDecayError("finite tail-decay source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _term_decay(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    zero=Zero();one=Succ(zero);two=Succ(one)
    def base(t):
        d,x,a,a0,p=t.terms(("d","x","a","a0","p"))
        eq=apply(specialize(t,"recurrence",zero,a0,a),t.hyp("bound"),t.hyp("head"),t.hyp("value"))
        bound=apply(specialize(t,"ratio",d,x,zero,a0,a,one),t.hyp("nonzero"),t.hyp("argument"),specialize(t,"le_refl",one),eq)
        bound=_subst(t,registry,"Le(slot,a0)",specialize(t,"one_mul",a),bound)
        p1=apply(specialize(t,"power_zero",two,zero,p),EqRefl(zero),t.hyp("power"))
        same=_chain(CongMul(p1,EqRefl(a)),specialize(t,"one_mul",a))
        return _subst(t,registry,"Le(slot,a0)",EqSym(same),bound)
    def successor(t):
        def chosen(u):
            d,x,k,L,a,a0,p,b,q=u.terms(("d","x","k","L","a","a0","p","b","q"));sk=Succ(k)
            earlier=apply(specialize(u,"le_trans",sk,Succ(sk),L),
                apply(specialize(u,"le_succ",sk,sk),specialize(u,"le_refl",sk)),u.hyp("bound"))
            old=apply(specialize(u,"IH",b,q),earlier,u.hyp("previous"),AndElimL(u.hyp("power_data")))
            eq=apply(specialize(u,"recurrence",sk,b,a),u.hyp("bound"),u.hyp("previous"),u.hyp("value"))
            index=apply(specialize(u,"succ_le_succ",zero,k),specialize(u,"zero_le",k))
            index=apply(specialize(u,"succ_le_succ",one,sk),index)
            ratio=apply(specialize(u,"ratio",d,x,sk,b,a,two),u.hyp("nonzero"),u.hyp("argument"),index,eq)
            lifted=apply(specialize(u,"mul_left_mono",Mul(two,a),b,q),ratio)
            result=apply(specialize(u,"le_trans",Mul(q,Mul(two,a)),Mul(q,b),a0),lifted,old)
            same=_chain(CongMul(AndElimR(u.hyp("power_data")),EqRefl(a)),specialize(u,"mul_assoc",q,two,a))
            return _subst(u,registry,"Le(slot,a0)",EqSym(same),result)
        powers=apply(specialize(t,"power_step",two,t.term("k"),Succ(t.term("k")),t.term("p")),EqRefl(Succ(t.term("k"))),t.hyp("power"))
        return eliminate(t,powers,("q",),"power_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(T),Succ(u.term("k"))),("b",),"previous",chosen))
    motive=target
    for _ in FIXED:
        motive=motive.body
    motive=motive.right.right.right.right.body
    row_params,row_hyps=("a","p"),("bound","value","power")
    return introduce(s,FIXED,("nonzero","argument","recurrence","head"),lambda t:
        Ind(motive,introduce(t,row_params,row_hyps,base),
            introduce(t,("k",),("IH",),lambda u:introduce(u,row_params,row_hyps,successor))))


def _scaled_sum(s,registry):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()))
    def finish(t):
        p,z,a,a0=t.terms(("p","s","a","a0"))
        lower=apply(specialize(t,"mul_left_mono",z,Mul(two,a),p),t.hyp("tail_bound"))
        lower=_subst(t,registry,"Le(p*s,slot)",_multiplicative_equal(t,Mul(p,Mul(two,a)),Mul(two,Mul(p,a))),lower)
        upper=apply(specialize(t,"mul_left_mono",Mul(p,a),a0,two),t.hyp("head_decay"))
        return apply(specialize(t,"le_trans",Mul(p,z),Mul(two,Mul(p,a)),Mul(two,a0)),lower,upper)
    return introduce(s,("p","s","a","a0"),("head_decay","tail_bound"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Add,Succ,Zero
    two=Succ(Succ(Zero()))
    def finished(t):
        m,N=t.terms(("m","N"));horizon=Add(Succ(m),N)
        invariant=apply(specialize(t,"term_decay",*t.terms(("d","x")),horizon,*t.terms(T+("a0",))),
            t.hyp("nonzero"),t.hyp("argument"),t.hyp("recurrence"),t.hyp("head"))
        width=witness((N,),specialize(t,"add_comm",N,Succ(m)))
        decay=apply(instantiate(invariant,m,*t.terms(("a","p"))),width,t.hyp("first"),t.hyp("power"))
        full=apply(specialize(t,"scaled_sum",*t.terms(("p","s","a","a0"))),decay,field(t.hyp("tail"),3,4))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("power"),t.hyp("first"),
            *(field(t.hyp("tail"),i,4) for i in range(3)),decay,full))
    def chosen(t):
        tail=apply(specialize(t,"tail_exists",*t.terms(("d","x")+T+("m","N","a"))),
            t.hyp("nonzero"),t.hyp("argument"),t.hyp("recurrence"),t.hyp("first"))
        return eliminate(t,tail,U+("s",),"tail",finished)
    return introduce(s,PARAMETERS,("nonzero","argument","recurrence","head"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(T),Succ(t.term("m"))),("a",),"first",lambda u:
            eliminate(u,specialize(u,"power_exists",two,u.term("m")),("p",),"power",chosen)))


def prove_scaled_exp_tail_decay(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV088",target=frozen_scaled_exp_tail_decay_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"term_decay":lambda s:_term_decay(s,parse_named(HELPER_SOURCES["term_decay"],registry=registry),registry),
            "scaled_sum":lambda s:_scaled_sum(s,registry),"CV088":_root},pins=scaled_exp_tail_decay_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
