"""SQ003: construct the positive integer bracket for sqrt(2) at any scale.

For every nonzero natural d, the actual floor root of 2*d^2 is unique and
satisfies d<=s<2*d and s!=0. This is finite integer computation, with no
real-number object or approximation-accuracy premise in its definitions.
"""
from hashlib import sha256

from sqrt2_power_floor_sqrt_comparison import (
    ROOT,Scope,introduce,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,floor_sqrt_comparison_source_pins,FLOOR_ARCHIVE,
    NAMED_SOURCE as COMPARISON_SOURCE,
)
from sqrt2_power_floor_sqrt import NAMED_SOURCE as TOTAL_SOURCE,eliminate,witness
from sqrt2_power_scaled_exp_tail import BOUND_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-scaled-sqrt2-v1"
PARTS=("FloorSqrt(2*(d*d),s)","Le(d,s)","Lt(s,2*d)","~s=0","forall t. FloorSqrt(2*(d*d),t) -> t=s")
NAMED_SOURCE="forall d. ~d=0 -> exists s. "+" /\\ ".join("("+p+")" for p in PARTS)
TARGET_SHA256="4e1139169e23ee835cb5f0eb9371fa4b6a641079db34b76bcb25f692bd88efb8"
HELPER_SOURCES={
    "arithmetic":"forall d. ~d=0 -> Le(d*d,2*(d*d)) /\\ Lt(2*(d*d),(2*d)*(2*d))",
    "le_nonzero":"forall d s. ~d=0 -> Le(d,s) -> ~s=0",
}
HELPER_TARGET_SHA256={"arithmetic":"939461c08c65e343678ba931a0ba6d9045ba6185107988485c8a204786c2ec9d",
    "le_nonzero":"f602d4d078f2a4c54a94f190542854efefdd3898627236f12414b24973c87686"}
COMPARISON_ARCHIVE=dict(case="SQ002",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-floor-sqrt-comparison-v1/generation-process.json.gz",
    bytes=6984,sha256="0d6eb0bf67b344a62bea75e71178d3522a9d9b63e376f75007ba63ac65d6511b",
    raw_bytes=44057,raw_sha256="0baa51884bce75e716f7405f1d6a595f340511734dd3571bbbb024d945229e24",
    bundle_bytes=18278,bundle_sha256="ee5be134efec33276a298e8ac6119db809740d9fe595e3586e9c51d175e60f96",
    nodes=16,root=15,target_ast_sha256="87748e18b800d65594ab1288e0586b089302a29354fd0c34e978ab8a54a76e5a")
ARCHIVES=(FLOOR_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "total_unique":TOTAL_SOURCE,"comparison":COMPARISON_SOURCE,
    "le_antisym":"forall a b. Le(a,b) -> Le(b,a) -> a=b",
    "mul_lt_succ_left":"forall a b. ~a=0 -> Lt(a*b,a*(S b))",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b",
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
    "succ_ne_zero":"forall a. ~S a=0","one_mul":"forall a. 1*a=a",
    "zero_le":"forall a. Le(0,a)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(total_unique="SQ001",comparison="SQ002",le_antisym="SQ001",mul_lt_succ_left="SQ001")
HELPER_DEPENDENCIES={
    "arithmetic":("mul_succ_left","one_mul","mul_ne_zero","succ_ne_zero","mul_lt_succ_left","mul_assoc","mul_comm"),
    "le_nonzero":("le_antisym","zero_le"),
    "SQ003":("total_unique","comparison","arithmetic","le_nonzero"),
}


class ScaledSqrt2Error(ValueError):
    """Changed actual scaled floor root, nonzero guard, bound or source."""


def frozen_scaled_sqrt2_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ScaledSqrt2Error("SQ003 exact positive scaled-square-root target changed")
    return target


def source_contract():
    return dict(code="SQ003",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,nonzero_input_scale_required=True,actual_floor_root_constructed=True,
        floor_root_unique=True,root_nonzero_proved=True,integer_bounds="d<=s<2*d",
        arbitrary_positive_scale=True,new_induction_needed=False,
        reused_definition_ids=["PD0001","PD0002","PD0051"],new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        real_square_root_or_dyadic_accuracy_claim=False,analytic_limit_claim=False,
        closes_IR013=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def scaled_sqrt2_source_pins():
    result=floor_sqrt_comparison_source_pins()
    expected={"scripts/sqrt2_power_floor_sqrt_comparison.py":"350cd0fac8d4677092724768b0bb575c78520c97c1006cc5e830dcd2c7cb3556",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_scaled_sqrt2.py","scripts/sqrt2_power_scaled_exp_tail.py",
                 "scripts/sqrt2_power_finite_power_evaluation.py","scripts/sqrt2_power_quadratic_height.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ScaledSqrt2Error("scaled-square-root source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym,ExistsIntro
    from peano_lab.kernel.terms import Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish(t):
        d=t.term("d");D=Mul(d,d);A=Mul(two,D)
        double=_chain(specialize(t,"mul_succ_left",one,D),CongAdd(specialize(t,"one_mul",D),EqRefl(D)))
        lower=ExistsIntro(D,EqSym(double))
        Dnz=apply(specialize(t,"mul_ne_zero",d,d),t.hyp("nonzero"),t.hyp("nonzero"))
        Anz=apply(specialize(t,"mul_ne_zero",two,D),specialize(t,"succ_ne_zero",one),Dnz)
        upper=apply(specialize(t,"mul_lt_succ_left",A,one),Anz)
        left=_chain(specialize(t,"mul_comm",A,one),specialize(t,"one_mul",A))
        upper=_subst(t,registry,"Lt(slot,(2*(d*d))*2)",left,upper)
        right=_multiplicative_equal(t,Mul(A,two),Mul(Mul(two,d),Mul(two,d)))
        upper=_subst(t,registry,"Lt(2*(d*d),slot)",right,upper)
        return conjunction(lower,upper)
    return introduce(s,("d",),("nonzero",),finish)


def _le_nonzero(s,registry):
    from peano_lab.kernel.terms import Zero
    def finish(t):
        d=t.term("d")
        bound=_subst(t,registry,"Le(d,slot)",t.hyp("zero"),t.hyp("bound"))
        equal=apply(specialize(t,"le_antisym",d,Zero()),bound,specialize(t,"zero_le",d))
        return apply(t.hyp("nonzero"),equal)
    return introduce(s,("d","s"),("nonzero","bound","zero"),finish)


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()))
    def finish(t):
        d,root=t.terms(("d","s"));n=Mul(two,Mul(d,d))
        arithmetic=apply(specialize(t,"arithmetic",d),t.hyp("nonzero"))
        floor=AndElimL(t.hyp("data"))
        bounds=apply(specialize(t,"comparison",n,root,d,Mul(two,d)),floor,AndElimL(arithmetic),AndElimR(arithmetic))
        positive=apply(specialize(t,"le_nonzero",d,root),t.hyp("nonzero"),AndElimL(bounds))
        # The frozen source's repeated conjunction is left-associated by the
        # ordinary parser. Preserve that exact AST, not merely an equivalent
        # right-associated tuple generated by the shared conjunction helper.
        result=floor
        for part in (AndElimL(bounds),AndElimR(bounds),positive,AndElimR(t.hyp("data"))):
            result=AndIntro(result,part)
        return witness((root,),result)
    return introduce(s,("d",),("nonzero",),lambda t:
        eliminate(t,specialize(t,"total_unique",Mul(two,Mul(t.term("d"),t.term("d")))),("s",),"data",finish))


def prove_scaled_sqrt2(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="SQ003",target=frozen_scaled_sqrt2_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"arithmetic":lambda s:_arithmetic(s,registry),"le_nonzero":lambda s:_le_nonzero(s,registry),"SQ003":_root},
        pins=scaled_sqrt2_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
