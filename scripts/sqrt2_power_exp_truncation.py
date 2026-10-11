"""CV100: a supplied exponential prefix and whole sum have a uniform tail bound.

The supplied table, two actual sums and power are retained. Construct a tail
with CV088, identify its sum by affine-sum uniqueness, and prove
s <= t and p*t <= p*s + 2*a0 for p=2^m. No infinite remainder is assumed.
"""
from hashlib import sha256

from sqrt2_power_scaled_exp_tail_decay import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,scaled_exp_tail_decay_source_pins,
    NAMED_SOURCE as DECAY_SOURCE,OUTPUTS as DECAY_OUTPUTS,BOUND_ARCHIVE,COMPOSITION_ARCHIVE,
)
from sqrt2_power_sum_splitting import NAMED_SOURCE as SPLIT_SOURCE,sum_splitting_source_pins,FUBINI_HELPERS
from sqrt2_power_convolution_commutative import SPLIT_ARCHIVE
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-truncation-v1"
A=("ab","ac")
PARAMETERS=("d","x")+A+("m","N","a0","s","t","p")
RECURRENCE="NatScaledExpRecurrence(d,x,ab,ac,(S m)+N)"
PREFIX="Sum(ab,ac,S m,s)"
WHOLE="Sum(ab,ac,S((S m)+N),t)"
PREMISES=("~d=0","Le(x,d)",RECURRENCE,"BetaAt(ab,ac,0,a0)",PREFIX,WHOLE,"Pow(2,m,p)")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> Le(s,t) /\\ Le(p*t,p*s+2*a0)"
TARGET_SHA256="38cc1a427fdb362d86fb580c3b3a939ae9e62900f35876de3390a804f26294b2"
HELPER_SOURCES={
    "supplied_split":"forall ab ac m N s t u. NatAffineSum(ab,ac,S m,1,S N,u) -> "+PREFIX+" -> "+WHOLE+" -> t=s+u",
    "finish_bound":"forall p a0 s t u. t=s+u -> Le(p*u,2*a0) -> Le(s,t) /\\ Le(p*t,p*s+2*a0)",
}
HELPER_TARGET_SHA256={
    "supplied_split":"e713560dba39bdc509abcb82597e711942498c25bdca203899673d6a3a5597d2",
    "finish_bound":"772a8330ade48e864abd1c4a9318fec3e8e32fb2fb94516bf665bf923127f62f",
}
DECAY_ARCHIVE=dict(case="CV088",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-scaled-exp-tail-decay-v1/generation-process.json.gz",
    bytes=33664,sha256="d849e2c91446341d9f88dc8e7b1b697381954c5bdc8124c1eb495da36b11045d",
    raw_bytes=512672,raw_sha256="36a7bd10d787efa0d67623660b6e2985827714432f0ffb63eacb16c52034b7ce",
    bundle_bytes=283071,bundle_sha256="b69e30c4b5c8f199bb7dc45506f4d3476edf42e8acae440e9ee5c806e00fa303",
    nodes=136,root=135,target_ast_sha256="76d2878ab4276b62e8094e3b25956fc0b58fec9c0d936f9c3af4c253fe8cc5ba")
ARCHIVES=(DECAY_ARCHIVE,SPLIT_ARCHIVE,BOUND_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={
    "decay":DECAY_SOURCE,"splitting":SPLIT_SOURCE,"slice_sum_unique":FUBINI_HELPERS["slice_sum_unique"],
    "sum_unique":"forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m",
    "power_unique":"forall a n x y. Pow(a,n,x) -> Pow(a,n,y) -> x=y",
    "add_comm":"forall a b. a+b=b+a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(decay="CV088",splitting="CV009",slice_sum_unique="CV009",sum_unique="CV061",power_unique="CV061")
HELPER_DEPENDENCIES={
    "supplied_split":("splitting","sum_unique","slice_sum_unique"),
    "finish_bound":("add_comm","mul_add","add_left_mono"),
    "CV100":("decay","supplied_split","power_unique","finish_bound"),
}


class ExpTruncationError(ValueError):
    """Changed supplied sums, truncation lengths or actual cutoff power."""


def frozen_exp_truncation_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=10 or len(premises)!=7 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpTruncationError("CV100 exact supplied finite exponential truncation changed")
    return target


def source_contract():
    return dict(code="CV100",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=7,supplied_recurrence_head_two_sums_and_power_preserved=True,
        actual_tail_constructed_and_identified_by_value_uniqueness=True,
        nonzero_argument_denominator_required=True,argument_bound="x<=d",
        prefix_length="m+1",whole_length="m+N+2",tail_length="N+1",cutoff_power="p=2^m",
        natural_bounds="s<=t; p*t<=p*s+2*a0",uniform_in_every_finite_extra_horizon=True,
        zero_argument_head_cutoff_and_extra_horizon_allowed=True,new_induction_needed=False,
        code_number_equality_claimed=False,rational_validity_claimed=False,infinite_remainder_claimed=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def exp_truncation_source_pins():
    result=scaled_exp_tail_decay_source_pins()
    for name,pin in sum_splitting_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpTruncationError("supplied truncation source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_scaled_exp_tail_decay.py":"c4374b0bbf21b8929b383b0bb3ae1806e7056b70c9144382e80a14967625da30",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_truncation.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpTruncationError("supplied truncation source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _supplied_split(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqSym
    from peano_lab.kernel.terms import Add,Succ,Zero
    def chosen(t):
        m,N,z,out,u,short,tail,whole=t.terms(("m","N","s","t","u","short","tail","whole"));sm,sn=Succ(m),Succ(N)
        data=t.hyp("split")
        first=apply(specialize(t,"sum_unique",*t.terms(A),sm,short,z),field(data,0,4),t.hyp("prefix"))
        last=apply(specialize(t,"slice_sum_unique",*t.terms(A),sm,Succ(Zero()),sn,tail,u),field(data,1,4),t.hyp("tail_sum"))
        full=_subst(t,registry,"Sum(ab,ac,slot,whole)",instantiate(Axiom("PA4"),sm,N),field(data,2,4))
        same=apply(specialize(t,"sum_unique",*t.terms(A),Succ(Add(sm,N)),whole,out),full,t.hyp("whole_sum"))
        return _chain(EqSym(same),field(data,3,4),CongAdd(first,last))
    return introduce(s,A+("m","N","s","t","u"),("tail_sum","prefix","whole_sum"),lambda t:
        eliminate(t,specialize(t,"splitting",*t.terms(A),Succ(t.term("m")),Succ(t.term("N"))),
            ("short","tail","whole"),"split",chosen))


def _finish_bound(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        p,a0,z,out,u=t.terms(("p","a0","s","t","u"));two=Succ(Succ(Zero()))
        lower=witness((u,),_chain(specialize(t,"add_comm",u,z),EqSym(t.hyp("split"))))
        upper=apply(specialize(t,"add_left_mono",Mul(p,u),Mul(two,a0),Mul(p,z)),t.hyp("tail_bound"))
        product=_chain(CongMul(EqRefl(p),t.hyp("split")),specialize(t,"mul_add",p,z,u))
        upper=_subst(t,registry,"Le(slot,p*s+2*a0)",EqSym(product),upper)
        return conjunction(lower,upper)
    return introduce(s,("p","a0","s","t","u"),("split","tail_bound"),finish)


def _root(s,registry):
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        data=t.hyp("tail_data")
        tail=witness(t.terms(("ub","uc")),conjunction(field(data,2,7),field(data,4,7)))
        split=apply(specialize(t,"supplied_split",*t.terms(A+("m","N","s","t","tail_total"))),tail,t.hyp("prefix"),t.hyp("whole"))
        same=apply(specialize(t,"power_unique",Succ(Succ(Zero())),*t.terms(("m","tail_power","p"))),field(data,0,7),t.hyp("power"))
        bound=_subst(t,registry,"Le(slot*tail_total,2*a0)",same,field(data,6,7))
        return apply(specialize(t,"finish_bound",*t.terms(("p","a0","s","t","tail_total"))),split,bound)
    def start(t):
        decay=apply(specialize(t,"decay",*t.terms(("d","x")+A+("m","N","a0"))),
            t.hyp("nonzero"),t.hyp("argument"),t.hyp("recurrence"),t.hyp("head"))
        return eliminate(t,decay,("tail_power","ub","uc","first_omitted","tail_total"),"tail_data",chosen)
    return introduce(s,PARAMETERS,("nonzero","argument","recurrence","head","prefix","whole","power"),start)


def prove_exp_truncation(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV100",target=frozen_exp_truncation_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"supplied_split":lambda s:_supplied_split(s,registry),"finish_bound":lambda s:_finish_bound(s,registry),"CV100":lambda s:_root(s,registry)},
        pins=exp_truncation_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
