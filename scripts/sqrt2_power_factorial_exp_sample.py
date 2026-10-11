"""AP023: construct the full finite sample with prescribed coefficient scale.

Use D=(2*k+1)!, retain D!=0 and every original computation/normalization
field. Beta encodings are actual witnesses, not asserted canonical numbers.
This does not yet certify the complete primitive-recursive CApprox trace.
"""
from hashlib import sha256

from sqrt2_power_exp_sample import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,exp_sample_source_pins,OUTPUTS,EXP_OUTPUTS,
    ARGUMENT_OUTPUTS,PARTS as SAMPLE_PARTS,_and,ARGUMENT_ARCHIVE,EXP_ARCHIVE,
    ENDPOINT_SOURCES as EXP_ENDPOINTS,
)
from sqrt2_power_log_root_argument import PARTS as ARGUMENT_PARTS,ENDPOINT_SOURCES as ARGUMENT_ENDPOINTS,HELPER_SOURCES as ARGUMENT_HELPERS
from sqrt2_power_factorial_atanh_prefix import NAMED_SOURCE as COEFFICIENT_SOURCE,factorial_atanh_prefix_source_pins
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-factorial-exp-sample-v1"
FACTORIAL="Factorial(S(2*k),D)"
PARTS=(FACTORIAL,"~D=0")+SAMPLE_PARTS
NAMED_SOURCE="forall k. exists "+" ".join(OUTPUTS)+". "+_and(PARTS)
TARGET_SHA256="a49dec85075c8e059c999c262ce992200a03c7c1611ff0d9003643f5237b1fcf"
HELPER_SOURCES={"argument":"forall k. exists "+" ".join(ARGUMENT_OUTPUTS)+". "+_and((FACTORIAL,)+ARGUMENT_PARTS)}
HELPER_TARGET_SHA256={"argument":"a3e2da2eeb1414a9e096f1349aa0c30a94c4b8cf3670002ab2edace08dac96ef"}
FACTORIAL_ARCHIVE=dict(case="AP022",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-factorial-atanh-prefix-v1/generation-process.json.gz",
    bytes=41358,sha256="a8564ff7ca7a4a09e3bcf7c8043e89b3bd1156c12bb9c88508c9ade48ada6cb9",
    raw_bytes=432210,raw_sha256="e60b8558037fdba64eb19295fab0ba687035d33edbe37e954380c5fb034d2caa",
    bundle_bytes=227171,bundle_sha256="e60cea590e8fc2dcd2f130c163423b166de275b0d0af5036748f9e0bd034d9f5",
    nodes=124,root=123,target_ast_sha256="717987b66df365b93849f2f28931c0d8b1ef892d210f4590b9c62997aee7989a")
ARCHIVES=(FACTORIAL_ARCHIVE,ARGUMENT_ARCHIVE,EXP_ARCHIVE)
ENDPOINT_SOURCES={name:ARGUMENT_ENDPOINTS[name] for name in ("dyadic_exists","value_exists","power_exists","power_nonzero","succ_ne_zero","inner_bound")}
ENDPOINT_SOURCES.update(atanh_exists=COEFFICIENT_SOURCE,bounds=ARGUMENT_HELPERS["bounds"],exponential_exists=EXP_ENDPOINTS["exponential_exists"])
ENDPOINT_OWNERS={name:"AP001" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(atanh_exists="AP022",exponential_exists="CV070")
HELPER_DEPENDENCIES={"argument":("dyadic_exists","atanh_exists","value_exists","power_exists","power_nonzero","succ_ne_zero","inner_bound","bounds"),
    "AP023":("argument","exponential_exists")}


class FactorialExpSampleError(ValueError):
    """Changed prescribed scale, actual sample fields or positivity."""


def frozen_factorial_exp_sample_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FactorialExpSampleError("AP023 exact fixed-factorial full sample changed")
    return target


def source_contract():
    return dict(code="AP023",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,prescribed_coefficient_scale="(2*k+1)!",all_precision_indices_including_zero=True,
        all_AP002_actual_computation_and_normalization_fields_retained=True,
        positive_coefficient_scale_retained_in_conclusion=True,argument_and_output_denominators_proved_nonzero=True,
        supplied_sample_definition_unchanged=True,beta_code_number_canonicality_claim=False,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def factorial_exp_sample_source_pins():
    result=exp_sample_source_pins()
    for name,pin in factorial_atanh_prefix_source_pins().items():
        if name in result and result[name]!=pin:
            raise FactorialExpSampleError("fixed-factorial sample source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_factorial_atanh_prefix.py":"aaca476df9fe9f419337c7f665824353f3c293821f52bc32e5f21642ad86c302",
        "scripts/sqrt2_power_log_root_argument.py":"75d8f43a8b74ded5164c2d445c5dccc202eec4ec1987340c9f484b3f53024f38",
        "scripts/sqrt2_power_exp_sample.py":"7062977d78a2ee1445e396d8e970460d1d366a36e8dc211c28e8c64b905adb46",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_factorial_exp_sample.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FactorialExpSampleError("fixed-factorial sample source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _argument(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    two,three=(parse_term(source) for source in ("2","3"))
    def length(t):
        return Succ(Mul(two,t.term("k")))
    def finish(t):
        root=t.hyp("root_data");coeff=t.hyp("coefficient_data");prefix=field(coeff,2,4)
        pnz=apply(instantiate(apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",two)),length(t),t.term("p")),t.hyp("power"))
        inner=apply(specialize(t,"inner_bound",*t.terms(("D","ab","ac")),Mul(two,t.term("k")),*t.terms(("x","p"))),prefix,t.hyp("value"),t.hyp("power"))
        bounds=apply(specialize(t,"bounds",*t.terms(("D","p","x","d","s"))),field(coeff,1,4),pnz,field(root,2,6),field(root,3,6),inner)
        graph=conjunction(field(root,0,6),prefix,t.hyp("value"),t.hyp("power"))
        return witness(t.terms(ARGUMENT_OUTPUTS),conjunction(field(coeff,0,4),graph,field(root,1,6),field(root,2,6),field(coeff,1,4),pnz,AndElimL(bounds),AndElimR(bounds)))
    return introduce(s,("k",),(),lambda t:
        eliminate(t,specialize(t,"dyadic_exists",t.term("k")),("d","s"),"root_data",lambda u:
            eliminate(u,specialize(u,"atanh_exists",length(u)),("D","ab","ac"),"coefficient_data",lambda v:
                eliminate(v,specialize(v,"value_exists",*v.terms(("ab","ac")),three,length(v)),("x",),"value",lambda w:
                    eliminate(w,specialize(w,"power_exists",three,length(w)),("p",),"power",finish)))))


def _root(s):
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,three=(parse_term(source) for source in ("2","3"))
    def finish(t):
        arg=t.hyp("argument_data");exp=t.hyp("exponential_data")
        graph=conjunction(field(arg,1,8),*(field(exp,i,11) for i in (0,1,2,3,5,6,7,8)))
        return witness(t.terms(OUTPUTS),conjunction(field(arg,0,8),field(arg,4,8),graph,field(exp,4,11),field(arg,6,8),field(arg,7,8),field(exp,9,11),field(exp,10,11)))
    def argument(t):
        D,p,root,x,d,k=t.terms(("D","p","s","x","d","k"))
        constructed=apply(specialize(t,"exponential_exists",Mul(Mul(D,p),root),Mul(Mul(three,x),d),Add(k,two)),field(t.hyp("argument_data"),6,8))
        return eliminate(t,constructed,EXP_OUTPUTS,"exponential_data",finish)
    return introduce(s,("k",),(),lambda t:eliminate(t,specialize(t,"argument",t.term("k")),ARGUMENT_OUTPUTS,"argument_data",argument))


def prove_factorial_exp_sample(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP023",target=frozen_factorial_exp_sample_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"argument":_argument,"AP023":_root},pins=factorial_exp_sample_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
