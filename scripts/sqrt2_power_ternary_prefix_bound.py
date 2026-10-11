"""CV089: bound every supplied base-three Horner prefix without a zero head.

If all coefficients are <=2D, an endpoint y at length n and p=3^n obey
y+D<=D*p. Empty prefixes and D=0 are included. The actual supplied value,
power and coefficient codes are preserved; there is no analytic assumption.
"""
from hashlib import sha256

from sqrt2_power_ternary_atanh_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,ternary_atanh_bound_source_pins,
    HELPER_SOURCES as TERNARY_HELPERS,ENDPOINT_SOURCES as TERNARY_ENDPOINTS,
)
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-ternary-prefix-bound-v1"
A,H=("ab","ac"),("hb","hc")
PARAMETERS=A+("D","N","y","p")
FIXED=A+("D","N")+H
NAMED_SOURCE="forall ab ac D N y p. NatBoundedPrefix(ab,ac,2*D,N) -> NatHornerValue(ab,ac,3,N,y) -> Pow(3,N,p) -> Le(y+D,D*p)"
TARGET_SHA256="5065e02e01a4babe946abf7b6ad03affafc1b509d98b79ed7d5f71995498c926"
ALL_PREFIXES="forall k y p. Le(k,N) -> BetaAt(hb,hc,k,y) -> Pow(3,k,p) -> Le(y+D,D*p)"
HELPER_SOURCES={"all_prefixes":"forall "+" ".join(FIXED)+". NatBoundedPrefix(ab,ac,2*D,N) -> NatScaledHornerTrace(ab,ac,3,N,hb,hc) -> "+ALL_PREFIXES}
HELPER_TARGET_SHA256={"all_prefixes":"5d700ab25b0e63701a613626cc9f43e458494036af6795e741288d823c4abb06"}
TERNARY_ARCHIVE=dict(case="CV086",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-ternary-atanh-bound-v1/generation-process.json.gz",
    bytes=19588,sha256="5f4114b9dbcb5347b0deea09a7c7e4e71a9181b9ddfd55dc05a76576e967bb34",
    raw_bytes=217326,raw_sha256="4fdea28c65d8e57f87e320ec245744596eecb57061b52e9258f6bfc467592a08",
    bundle_bytes=97681,bundle_sha256="914f8df1b97d191c466fcb8decab245de1e5cb08bfbd9df904e403d18d09fb48",
    nodes=46,root=45,target_ast_sha256="7a0be8c3f072412b13318d7e4c22a5a86af4e3c3a1567ad788f60fc72b41a49a")
ARCHIVES=(TERNARY_ARCHIVE,)
ENDPOINT_SOURCES={name:TERNARY_ENDPOINTS[name] for name in
    ("beta_exists","power_zero","power_step","step_value","zero_add","mul_one","le_refl","le_succ","le_trans")}
ENDPOINT_SOURCES.update(beta_unique="forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",step_bound=TERNARY_HELPERS["step_bound"])
ENDPOINT_OWNERS={name:"CV086" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES={
    "all_prefixes":tuple(ENDPOINT_SOURCES),
    "CV089":("all_prefixes","le_refl"),
}


class TernaryPrefixBoundError(ValueError):
    """Changed actual finite prefix, coefficient bound or scaling power."""


def frozen_ternary_prefix_bound_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,_=strip_target(target)
    if binders!=6 or len(premises)!=3 or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise TernaryPrefixBoundError("CV089 exact supplied ternary prefix bound changed")
    return target


def source_contract():
    return dict(code="CV089",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,supplied_coefficients_horner_value_and_power_preserved=True,
        zero_head_required=False,empty_prefix_and_zero_bound_allowed=True,
        inequality="y+D<=D*p; p=3^N; coefficients<=2*D",
        no_division=True,no_denominator_nonzero_claim=True,analytic_limit_claim=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def ternary_prefix_bound_source_pins():
    result=ternary_atanh_bound_source_pins()
    expected={"scripts/sqrt2_power_ternary_atanh_bound.py":"736d67f656e06c3f93aba52817bdce3e390fee5dab88e721818d3a43da9c97a4",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_ternary_prefix_bound.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise TernaryPrefixBoundError("ternary prefix source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _all_prefixes(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Succ,Zero
    zero=Zero();three=Succ(Succ(Succ(zero)))
    def base(t):
        D,y,p=t.terms(("D","y","p"))
        y0=apply(specialize(t,"beta_unique",*t.terms(H),zero,y,zero),t.hyp("value"),AndElimL(t.hyp("trace")))
        p1=apply(specialize(t,"power_zero",three,zero,p),EqRefl(zero),t.hyp("power"))
        equal=_chain(CongAdd(y0,EqRefl(D)),specialize(t,"zero_add",D),EqSym(specialize(t,"mul_one",D)),CongMul(EqRefl(D),EqSym(p1)))
        return _subst(t,registry,"Le(y+D,slot)",equal,specialize(t,"le_refl",Add(y,D)))
    def successor(t):
        def chosen(u):
            k,N=u.terms(("k","N"));sk=Succ(k)
            earlier=apply(specialize(u,"le_trans",k,sk,N),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            old=apply(specialize(u,"IH",*u.terms(("h","q"))),earlier,u.hyp("old_value"),AndElimL(u.hyp("power_data")))
            coefficient=apply(specialize(u,"coefficients",k,u.term("c")),u.hyp("bound"),u.hyp("coefficient"))
            step=apply(instantiate(AndElimR(u.hyp("trace")),k),u.hyp("bound"))
            next_value=apply(specialize(u,"step_value",*u.terms(A),three,*u.terms(H),k,*u.terms(("h","c","y"))),
                step,u.hyp("old_value"),u.hyp("coefficient"),u.hyp("value"))
            return apply(specialize(u,"step_bound",*u.terms(("D","h","c","q","y","p"))),old,coefficient,next_value,AndElimR(u.hyp("power_data")))
        powers=apply(specialize(t,"power_step",three,t.term("k"),Succ(t.term("k")),t.term("p")),EqRefl(Succ(t.term("k"))),t.hyp("power"))
        return eliminate(t,powers,("q",),"power_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H+("k",))),("h",),"old_value",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(A+("k",))),("c",),"coefficient",chosen)))
    motive=target
    for _ in FIXED:
        motive=motive.body
    motive=motive.right.right.body
    params,hyps=("y","p"),("bound","value","power")
    return introduce(s,FIXED,("coefficients","trace"),lambda t:
        Ind(motive,introduce(t,params,hyps,base),introduce(t,("k",),("IH",),lambda u:introduce(u,params,hyps,successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def chosen(t):
        invariant=apply(specialize(t,"all_prefixes",*t.terms(A+("D","N")+H)),t.hyp("coefficients"),AndElimL(t.hyp("trace_value")))
        return apply(instantiate(invariant,*t.terms(("N","y","p"))),specialize(t,"le_refl",t.term("N")),AndElimR(t.hyp("trace_value")),t.hyp("power"))
    return introduce(s,PARAMETERS,("coefficients","value","power"),lambda t:eliminate(t,t.hyp("value"),H,"trace_value",chosen))


def prove_ternary_prefix_bound(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV089",target=frozen_ternary_prefix_bound_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"all_prefixes":lambda s:_all_prefixes(s,parse_named(HELPER_SOURCES["all_prefixes"],registry=registry),registry),"CV089":_root},
        pins=ternary_prefix_bound_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
