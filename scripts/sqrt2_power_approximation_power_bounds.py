"""AP011: the actual logarithm and exponential cutoff powers dominate 2^k.

Keep supplied computations d=2^k, p=3^(2k+1), r=2^(k+2). General power
comparison supplies d<=p and d<=r, including k=0. Positivity is proved.
"""
from hashlib import sha256

from sqrt2_power_positive_power_comparison import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,definition_registry,
    positive_power_comparison_source_pins,NAMED_SOURCE as COMPARISON_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_dyadic_sqrt2 import _and
from sqrt2_power_exp_two_sided_continuity import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-approximation-power-bounds-v1"
PARTS=("~d=0","~p=0","~r=0","Le(d,p)","Le(d,r)")
NAMED_SOURCE="forall k d p r. Pow(2,k,d) -> Pow(3,S(2*k),p) -> Pow(2,k+2,r) -> "+_and(PARTS)
TARGET_SHA256="a41d4293a571408ac987bb69b06a49ec1afd6527e75e6d2404265714b00fb69e"
HELPER_SOURCES={"length":"forall k. S(2*k)=k+S k"}
HELPER_TARGET_SHA256={"length":"9dae30a464b1f8981b09032d4f3c56695a0ccaabbfa8d79ac91bcea5d3022a52"}
COMPARISON_ARCHIVE=dict(case="AP010",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-positive-power-comparison-v1/generation-process.json.gz",
    bytes=44957,sha256="953368beb1a180881e9ef3c6a465fce1dd7b5734b83d65065cabc8467065a919",
    raw_bytes=492979,raw_sha256="e3fff5d6253eb250a0b8270cdf73c812f6ecb6e19afb18789f08ad914558375b",
    bundle_bytes=258080,bundle_sha256="340b616e44a6822279a5bef8dc9bc4e8a15d748592e8b2870b82f50ffa1268fe",
    nodes=126,root=125,target_ast_sha256="4b0cf1709336ebd3b4aa2546b4ad7107701157fb692b6db7205344456192cd25")
ARCHIVES=(COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "comparison":COMPARISON_SOURCE,"power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b","one_mul":"forall a. 1*a=a",
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "succ_ne_zero":"forall a. ~S a=0",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(comparison="AP010",power_nonzero="AP010")
HELPER_DEPENDENCIES={"length":("mul_succ_left","one_mul"),
    "AP011":("length","comparison","power_nonzero","le_refl","le_succ","succ_ne_zero")}


class ApproximationPowerBoundsError(ValueError):
    """Changed actual precision powers, zero precision or domination bounds."""


def frozen_approximation_power_bounds_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=4 or len(premises)!=3 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ApproximationPowerBoundsError("AP011 exact actual cutoff-power bounds changed")
    return target


def source_contract():
    return dict(code="AP011",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,three_supplied_power_computations_preserved=True,all_precision_indices_including_zero=True,
        all_three_denominators_proved_nonzero=True,domination_bounds="d<=p; d<=r",
        powers="d=2^k; p=3^(2*k+1); r=2^(k+2)",new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def approximation_power_bounds_source_pins():
    result=positive_power_comparison_source_pins()
    expected={"scripts/sqrt2_power_positive_power_comparison.py":"381cd294ff30012ed53978ec2590eb3d8da009339ea342af90fa3ec876bbebd4",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_approximation_power_bounds.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ApproximationPowerBoundsError("cutoff-power source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _length(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongS,EqRefl,EqSym
    from peano_lab.kernel.terms import parse_term
    def finish(t):
        k=t.term("k")
        return _chain(CongS(_chain(specialize(t,"mul_succ_left",parse_term("1"),k),
            CongAdd(specialize(t,"one_mul",k),EqRefl(k)))),EqSym(instantiate(Axiom("PA4"),k,k)))
    return introduce(s,("k",),(),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    one,two,three=(parse_term(n) for n in ("1","2","3"))
    def finish(t):
        k,d,p,r=t.terms(("k","d","p","r"));tnz=specialize(t,"succ_ne_zero",one);hnz=specialize(t,"succ_ne_zero",two)
        powers=apply(specialize(t,"power_nonzero",two),tnz)
        dnz=apply(instantiate(powers,k,d),t.hyp("dyadic"))
        pnz=apply(instantiate(apply(specialize(t,"power_nonzero",three),hnz),Succ(Mul(two,k)),p),t.hyp("logarithm"))
        rnz=apply(instantiate(powers,Add(k,two),r),t.hyp("cutoff"))
        aligned=_subst(t,registry,"Pow(3,slot,p)",specialize(t,"length",k),t.hyp("logarithm"))
        order=apply(specialize(t,"le_succ",two,two),specialize(t,"le_refl",two))
        logarithm=apply(specialize(t,"comparison",two,three,k,Succ(k),d,p),order,hnz,t.hyp("dyadic"),aligned)
        cutoff=apply(specialize(t,"comparison",two,two,k,two,d,r),specialize(t,"le_refl",two),tnz,t.hyp("dyadic"),t.hyp("cutoff"))
        return conjunction(dnz,pnz,rnz,logarithm,cutoff)
    return introduce(s,("k","d","p","r"),("dyadic","logarithm","cutoff"),finish)


def prove_approximation_power_bounds(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP011",target=frozen_approximation_power_bounds_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"length":_length,"AP011":lambda s:_root(s,registry)},
        pins=approximation_power_bounds_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
