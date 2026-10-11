"""AP003: log/root quotient values do not depend on coefficient encodings.

For two supplied computation graphs at the same precision and positive
coefficient scales, prove identical dyadic data/powers, positive quotient
denominators, and the exact rational cross-product identity. Code numbers
and the freely chosen coefficient scales are never equated.
"""
from hashlib import sha256

from sqrt2_power_log_root_argument import (
    ROOT,Scope,introduce,eliminate,conjunction,apply,specialize,field,canonical,json_hash,_and,
    definition_registry,log_root_argument_source_pins,OUTPUTS as LEFT,
    GRAPH as LEFT_GRAPH,DYADIC_SOURCE,
)
from sqrt2_power_exp_sample import ARGUMENT_ARCHIVE
from sqrt2_power_atanh_scale_independence import NAMED_SOURCE as SCALING_SOURCE,atanh_scale_independence_source_pins
from sqrt2_power_independent_atanh_truncation import SCALING_ARCHIVE
from sqrt2_power_dyadic_sqrt2_square_error import NAMED_SOURCE as SQUARE_SOURCE,dyadic_sqrt2_square_error_source_pins
from sqrt2_power_dyadic_sqrt2_reciprocal import SQUARE_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-log-root-independence-v1"
RIGHT=("e","t","E","bb","bc","z","h")
PARAMETERS=("k",)+LEFT+RIGHT
RIGHT_GRAPH="NatSqrt2LogArgument(k,e,t,E,bb,bc,z,h)"
IDENTITY="((3*x)*d)*((E*h)*t)=((3*z)*e)*((D*p)*s)"
PARTS=("d=e","s=t","p=h","~((D*p)*s)=0","~((E*h)*t)=0",IDENTITY)
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~D=0 -> ~E=0 -> "+LEFT_GRAPH+" -> "+RIGHT_GRAPH+" -> "+_and(PARTS)
TARGET_SHA256="a257baf8204aa80c57093525ce2915cb7d327803c89e4469be4206000abc6665"
HELPER_SOURCES={
    "equal_via":"forall a b c. a=c -> b=c -> a=b",
    "cross_product":"forall D E x z d e s t p h. d=e -> s=t -> p=h -> E*x=D*z -> "+IDENTITY,
}
HELPER_TARGET_SHA256={"equal_via":"4fe3cb0dbd798f875a17e7585d150e518bcde5c1d5a70ba1e365a3efe74581d2",
                      "cross_product":"1bbc31dc236a37059c4a0c602f0519cbc527bf712747faa302495f8b945356f4"}
ARCHIVES=(ARGUMENT_ARCHIVE,SCALING_ARCHIVE,SQUARE_ARCHIVE)
ENDPOINT_SOURCES={
    "dyadic_exists":DYADIC_SOURCE,"coefficient_scaling":SCALING_SOURCE,"square":SQUARE_SOURCE,
    "power_unique":"forall a k p q. Pow(a,k,p) -> Pow(a,k,q) -> p=q",
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0","mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS={name:"AP001" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(coefficient_scaling="CV092",square="SQ009")
HELPER_DEPENDENCIES={
    "equal_via":(),"cross_product":("mul_assoc","mul_comm"),
    "AP003":("dyadic_exists","coefficient_scaling","square","power_unique","power_nonzero","succ_ne_zero","mul_ne_zero","equal_via","cross_product"),
}


class LogRootIndependenceError(ValueError):
    """Changed supplied graphs, scale guards, value identity or actual proof."""


def frozen_log_root_independence_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=15 or len(premises)!=4 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LogRootIndependenceError("AP003 exact independent-encoding value target changed")
    return target


def source_contract():
    return dict(code="AP003",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,both_supplied_computation_graphs_preserved=True,positive_coefficient_scales_required=True,
        coefficient_scales_and_table_codes_not_equated=True,same_precision_required=True,
        dyadic_values_and_base_three_powers_equal=True,both_quotient_denominators_proved_nonzero=True,
        exact_rational_cross_product_identity=True,all_precision_indices_including_zero=True,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,exponential_output_uniqueness_claim=False,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def log_root_independence_source_pins():
    result=log_root_argument_source_pins()
    for source in (atanh_scale_independence_source_pins(),dyadic_sqrt2_square_error_source_pins()):
        for name,pin in source.items():
            if name in result and result[name]!=pin:
                raise LogRootIndependenceError("independent quotient source disagreement")
            result[name]=pin
    expected={"scripts/sqrt2_power_log_root_argument.py":"75d8f43a8b74ded5164c2d445c5dccc202eec4ec1987340c9f484b3f53024f38",
        "scripts/sqrt2_power_exp_sample.py":"7062977d78a2ee1445e396d8e970460d1d366a36e8dc211c28e8c64b905adb46",
        "scripts/sqrt2_power_atanh_scale_independence.py":"bc346b492c242367d2703c2bc9391b1ae0c289a518098e1aa30b3b70252e448d",
        "scripts/sqrt2_power_independent_atanh_truncation.py":"e51d53ad60fcc02a38ab75b6425abc92dbc58f06ba5f6309c562990cdc24c427",
        "scripts/sqrt2_power_dyadic_sqrt2_square_error.py":"8fd7a8ae82f1cfccf25dffa649624af229c3bd11069b9dee0bb8bd6df47c66e0",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_log_root_independence.py","scripts/sqrt2_power_dyadic_sqrt2_reciprocal.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise LogRootIndependenceError("independent quotient source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _equal_via(s):
    from peano_lab.kernel.proofs import EqTrans,EqSym
    return introduce(s,("a","b","c"),("left","right"),lambda t:EqTrans(t.hyp("left"),EqSym(t.hyp("right"))))


def _cross_product(s):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    three=Succ(Succ(Succ(Zero())))
    def finish(t):
        D,E,x,z,d,e,root,out,p,h=t.terms(("D","E","x","z","d","e","s","t","p","h"))
        left=Mul(Mul(Mul(three,x),d),Mul(Mul(E,h),out))
        rest=Mul(Mul(three,d),Mul(h,out))
        middle=Mul(Mul(Mul(three,z),d),Mul(Mul(D,h),out))
        return _chain(_multiplicative_equal(t,left,Mul(Mul(E,x),rest)),
            CongMul(t.hyp("coefficient_identity"),EqRefl(rest)),
            _multiplicative_equal(t,Mul(Mul(D,z),rest),middle),
            CongMul(CongMul(EqRefl(Mul(three,z)),t.hyp("same_d")),
                    CongMul(CongMul(EqRefl(D),EqSym(t.hyp("same_power"))),EqSym(t.hyp("same_root")))))
    return introduce(s,("D","E","x","z","d","e","s","t","p","h"),
                     ("same_d","same_root","same_power","coefficient_identity"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()));three=Succ(two)
    def finish(t):
        k,d,root,D,x,p,e,out,E,z,h=t.terms(("k","d","s","D","x","p","e","t","E","z","h"))
        left=t.hyp("left");right=t.hyp("right");N=Succ(Mul(two,k))
        unique=field(t.hyp("dyadic_data"),5,6)
        old=apply(instantiate(unique,d,root),field(left,0,4))
        new=apply(instantiate(unique,e,out),field(right,0,4))
        same_d=apply(specialize(t,"equal_via",d,e,t.term("d0")),AndElimL(old),AndElimL(new))
        same_s=apply(specialize(t,"equal_via",root,out,t.term("s0")),AndElimR(old),AndElimR(new))
        same_p=apply(specialize(t,"power_unique",three,N,p,h),field(left,3,4),field(right,3,4))
        square_a=apply(specialize(t,"square",k,d,root),field(left,0,4))
        square_b=apply(specialize(t,"square",k,e,out),field(right,0,4))
        nonzero=apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",two))
        pnz=apply(instantiate(nonzero,N,p),field(left,3,4));hnz=apply(instantiate(nonzero,N,h),field(right,3,4))
        dpnz=apply(specialize(t,"mul_ne_zero",D,p),t.hyp("D_nonzero"),pnz)
        ehnz=apply(specialize(t,"mul_ne_zero",E,h),t.hyp("E_nonzero"),hnz)
        vnz=apply(specialize(t,"mul_ne_zero",Mul(D,p),root),dpnz,field(square_a,1,6))
        wnz=apply(specialize(t,"mul_ne_zero",Mul(E,h),out),ehnz,field(square_b,1,6))
        scaling=apply(specialize(t,"coefficient_scaling",D,E,*t.terms(("ab","ac","bb","bc")),N,three,x,z),
                      field(left,1,4),field(right,1,4),field(left,2,4),field(right,2,4))
        cross=apply(specialize(t,"cross_product",*t.terms(("D","E","x","z","d","e","s","t","p","h"))),same_d,same_s,same_p,scaling)
        return conjunction(same_d,same_s,same_p,vnz,wnz,cross)
    return introduce(s,PARAMETERS,("D_nonzero","E_nonzero","left","right"),lambda t:
        eliminate(t,specialize(t,"dyadic_exists",t.term("k")),("d0","s0"),"dyadic_data",finish))


def prove_log_root_independence(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP003",target=frozen_log_root_independence_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"equal_via":_equal_via,"cross_product":_cross_product,"AP003":_root},
        pins=log_root_independence_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
