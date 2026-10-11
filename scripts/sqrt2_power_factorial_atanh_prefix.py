"""AP022: construct the logarithm coefficient table with prescribed scale N!.

Every positive i<=N divides the actual factorial, by ordinary HA induction.
Feed that explicit common multiple to the existing coefficient constructor.
This fixes the scale, not the beta-code representation or the whole PR trace.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_supplied_exp_sample import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,supplied_exp_sample_source_pins,definition_registry as source_registry,
    HELPER_SOURCES as POSITIVITY_HELPERS,ENDPOINT_SOURCES as FACTORIAL_ENDPOINTS,
)
from sqrt2_power_exp_sample_independence import SUPPLIED_ARCHIVE
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE
from sqrt2_power_scaled_exp_tail import BOUND_ARCHIVE
from sqrt2_power_atanh_coefficients import (
    COMMON,HELPER_SOURCES as COEFFICIENT_HELPERS,atanh_coefficients_source_pins,
)
from sqrt2_power_atanh_euler import ATANH_ARCHIVE
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-factorial-atanh-prefix-v1"
NAMED_SOURCE="forall N. exists d ab ac. Factorial(N,d) /\\ (~d=0 /\\ (NatAtanhPrefix(d,ab,ac,N) /\\ NatZeroBefore(ab,ac,N,1)))"
TARGET_SHA256="717987b66df365b93849f2f28931c0d8b1ef892d210f4590b9c62997aee7989a"
HELPER_SOURCES={
    "factorial_divisor":"forall B d. Factorial(B,d) -> forall i. Le(S i,B) -> exists k. d=(S i)*k",
    "common":"forall B d. Factorial(B,d) -> "+COMMON,
}
HELPER_TARGET_SHA256={"factorial_divisor":"0b86da848346218485ea66bba5e857d318cfeb7a416842ac52607c926e6bccc5",
    "common":"18683462eaac593975d3fff9d0fa7668c9bc00767a9beb4b5cd2f547caf2afb7"}
ARCHIVES=(ATANH_ARCHIVE,EXP_ARCHIVE,SUPPLIED_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "factorial_exists":"forall n. exists f. Factorial(n,f)",
    "factorial_step":FACTORIAL_ENDPOINTS["factorial_step"],"factorial_nonzero":POSITIVITY_HELPERS["factorial_nonzero"],
    "prefix_exists":COEFFICIENT_HELPERS["prefix_exists"],"prefix_zero":COEFFICIENT_HELPERS["prefix_zero"],
    "le_zero":"forall a. Le(a,0) -> a=0","succ_ne_zero":"forall a. ~S a=0",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "le_eq_or_lt":"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)","le_refl":"forall a. Le(a,a)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "add_comm":"forall a b. a+b=b+a",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(factorial_exists="CV070",factorial_step="AP004",factorial_nonzero="AP004",prefix_exists="CV025",prefix_zero="CV025")
HELPER_DEPENDENCIES={
    "factorial_divisor":("factorial_step","le_zero","succ_ne_zero","le_of_succ_le_succ","le_eq_or_lt","mul_assoc","mul_comm"),
    "common":("factorial_divisor","add_comm"),
    "AP022":("factorial_exists","factorial_nonzero","common","prefix_exists","prefix_zero","le_refl"),
}


class FactorialAtanhPrefixError(ValueError):
    """Changed prescribed scale, divisibility or actual prefix construction."""


def definition_registry():
    source=source_registry();needed=set();pending=["Le","Factorial","NatAtanhPrefix","NatZeroBefore"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise FactorialAtanhPrefixError("factorial coefficient definition DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_factorial_atanh_prefix_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FactorialAtanhPrefixError("AP022 exact prescribed-factorial coefficient construction changed")
    return target


def source_contract():
    return dict(code="AP022",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,prescribed_scale="N!",actual_factorial_and_coefficient_table_constructed=True,
        factorial_positive_and_every_required_divisibility_proved=True,positive_divisor_induction=True,
        empty_prefix_allowed=True,zero_initial_coefficient_proved=True,code_number_canonicality_claim=False,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=True,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def factorial_atanh_prefix_source_pins():
    result=supplied_exp_sample_source_pins()
    for name,pin in atanh_coefficients_source_pins().items():
        if name in result and result[name]!=pin:
            raise FactorialAtanhPrefixError("factorial coefficient source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_supplied_exp_sample.py":"30423d296b32b21ea9d3c35802cb81dbe5dae1fb4a589f8a8abce112e93be11a",
        "scripts/sqrt2_power_exp_sample_independence.py":"e6ec0523040135408adbadfc5cf46351f4682bd6a3b1f564c08263f8cb692187",
        "scripts/sqrt2_power_scaled_exp_bound.py":"717128c4845645cca66209b12512d4de2905d6ecc4eebad8c04c197647f9ee0c",
        "scripts/sqrt2_power_scaled_exp_tail.py":"df81a3c92b26346a1955ba92e763d932201649183604309f17bd156b2abbaeb3",
        "scripts/sqrt2_power_atanh_coefficients.py":"f933ef2b4a35fa6bfe67eabb9279b200a27dcb9a32904b1c4b689b8528386abd",
        "scripts/sqrt2_power_atanh_euler.py":"d24e8fc4fcf12b22f2971877ab3bb55be42991b6b9a34938d99e97920d4cffe2",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_factorial_atanh_prefix.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FactorialAtanhPrefixError("factorial coefficient source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _factorial_divisor(s,target):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,CongMul,CongS,EqRefl,EqSym,Ind,OrElim
    from peano_lab.kernel.terms import Mul,Succ
    def base(t):
        equal=apply(specialize(t,"le_zero",Succ(t.term("i"))),t.hyp("bound"))
        return BotElim(apply(specialize(t,"succ_ne_zero",t.term("i")),equal))
    def chosen(t):
        i,B=t.terms(("i","B"));bound=apply(specialize(t,"le_of_succ_le_succ",i,B),t.hyp("bound"))
        cases=apply(specialize(t,"le_eq_or_lt",i,B),bound)
        def last(u):
            f,B=u.terms(("f","B"))
            equal=_chain(AndElimR(u.hyp("previous")),specialize(u,"mul_comm",f,Succ(B)),CongMul(CongS(EqSym(u.hyp("last"))),EqRefl(f)))
            return witness((f,),equal)
        def earlier(u):
            previous=apply(instantiate(apply(specialize(u,"IH",u.term("f")),AndElimL(u.hyp("previous"))),u.term("i")),u.hyp("earlier"))
            def quotient(v):
                i,k,B=v.terms(("i","k","B"))
                equal=_chain(AndElimR(v.hyp("previous")),CongMul(v.hyp("divides"),EqRefl(Succ(B))),specialize(v,"mul_assoc",Succ(i),k,Succ(B)))
                return witness((Mul(k,Succ(B)),),equal)
            return eliminate(u,previous,("k",),"divides",quotient)
        return OrElim(cases,last(t.hypothesis("last")),earlier(t.hypothesis("earlier")))
    def successor(t):
        B=t.term("B")
        previous=apply(specialize(t,"factorial_step",B,Succ(B),t.term("d")),EqRefl(Succ(B)),t.hyp("factorial"))
        return eliminate(t,previous,("f",),"previous",chosen)
    return Ind(target.body,
        introduce(s,("d",),("factorial",),lambda t:introduce(t,("i",),("bound",),base)),
        introduce(s,("B",),("IH",),lambda t:introduce(t,("d",),("factorial",),lambda u:introduce(u,("i",),("bound",),successor))))


def _common(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,EqSym
    from peano_lab.kernel.terms import Add,Succ
    def chosen(t):
        i,h,B=t.terms(("t","h","B"));si=Succ(i)
        predecessor=apply(instantiate(Axiom("PA2"),Add(si,h),B),_chain(EqSym(instantiate(Axiom("PA4"),si,h)),t.hyp("index")))
        bound=witness((h,),_chain(specialize(t,"add_comm",h,si),predecessor))
        return apply(instantiate(apply(specialize(t,"factorial_divisor",B,t.term("d")),t.hyp("factorial")),i),bound)
    return introduce(s,("B","d"),("factorial",),lambda t:introduce(t,("t",),("bounded_index",),lambda u:
        eliminate(u,u.hyp("bounded_index"),("h",),"index",chosen)))


def _root(s):
    from sqrt2_power_native import instantiate
    def prefix(t):
        N,d=t.terms(("N","d"))
        positive=apply(specialize(t,"factorial_nonzero",N,d),t.hyp("factorial"))
        zero=apply(specialize(t,"prefix_zero",*t.terms(("d","ab","ac","N"))),t.hyp("prefix"))
        return witness(t.terms(("d","ab","ac")),conjunction(t.hyp("factorial"),positive,t.hyp("prefix"),zero))
    def factorial(t):
        N,d=t.terms(("N","d"));common=apply(specialize(t,"common",N,d),t.hyp("factorial"))
        exists=apply(instantiate(apply(specialize(t,"prefix_exists",N,d),common),N),specialize(t,"le_refl",N))
        return eliminate(t,exists,("ab","ac"),"prefix",prefix)
    return introduce(s,("N",),(),lambda t:eliminate(t,specialize(t,"factorial_exists",t.term("N")),("d",),"factorial",factorial))


def prove_factorial_atanh_prefix(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry();target=parse_named(HELPER_SOURCES["factorial_divisor"],registry=registry)
    return assemble_mixed_certificate(code="AP022",target=frozen_factorial_atanh_prefix_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"factorial_divisor":lambda s:_factorial_divisor(s,target),"common":_common,"AP022":_root},
        pins=factorial_atanh_prefix_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
