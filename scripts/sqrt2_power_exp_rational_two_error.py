"""CV102: valid rational two-error estimate for independent exp computations.

From actual finite recurrences and sums, prove
s/a0 <= t/b0 <= s/a0 + 9*g/(d*e) + 2/2^m.
All denominator nonvanishing is proved, including the supplied cutoff power.
No real-number sort, analytic identity, approximation axiom or code equality.
"""
from hashlib import sha256

from sqrt2_power_exp_two_error_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,exp_two_error_bound_source_pins,PARAMETERS,
    NAMED_SOURCE as BOUND_SOURCE,PREMISES as BOUND_PREMISES,BOUND_ARCHIVE,
)
from sqrt2_power_rational_tail_majorant import (
    definition_registry,rational_tail_majorant_source_pins,HELPER_SOURCES as RATIONAL_HELPERS,
    ENDPOINT_SOURCES as RATIONAL_ENDPOINTS,
)
from sqrt2_power_composition_tail_bound import RATIONAL_TAIL_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-rational-two-error-v1"
PREMISES=BOUND_PREMISES[:2]+("~a0=0","~b0=0")+BOUND_PREMISES[2:]
LOWER="IRatLe(s,0,a0,t,0,b0)"
UPPER="IRatLe(t,0,b0,(d*e)*(p*s)+(9*(g*p)+2*(d*e))*a0,0,(d*e)*(p*a0))"
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> "+LOWER+" /\\ "+UPPER
TARGET_SHA256="f3522601cd0c5260ecf6f5cde1c301a2d74e3f5b53f165eea0ef9f3bf32c837c"
HELPER_SOURCES={"orders":"forall D p E a0 b0 s t. ~D=0 -> ~p=0 -> ~a0=0 -> ~b0=0 -> Le(b0*s,a0*t) -> Le(D*(p*(a0*t)),D*(p*(b0*s))+E*(a0*b0)) -> IRatLe(s,0,a0,t,0,b0) /\\ IRatLe(t,0,b0,D*(p*s)+E*a0,0,D*(p*a0))"}
HELPER_TARGET_SHA256={"orders":"df99b7e29e9864f3f9f6c140c57ec665e3adf89a1bce54aea04f85bc9144a33b"}
TWO_ERROR_ARCHIVE=dict(case="CV101",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-two-error-bound-v2/generation-process.json.gz",
    bytes=53195,sha256="1bfee7ad54dd54e433b84c99a5d975b165b626581dcd7ab4ce8cd2524af3cfad",
    raw_bytes=1042578,raw_sha256="82626da5c3d58fafe1f4faa83c00522fc56fea068a06c82fb541abebbe9d460d",
    bundle_bytes=613675,bundle_sha256="ac305ff130d7a1936202c1022e0aa06acc322a556ae0d6684918bc30cb5533bd",
    nodes=189,root=188,target_ast_sha256="99e2c67d567497309e07b57a9c96266fe4299a7a38f24bf605373710dc0b6857")
ARCHIVES=(TWO_ERROR_ARCHIVE,RATIONAL_TAIL_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "two_error":BOUND_SOURCE,"positive_order":RATIONAL_HELPERS["positive_order"],
    "power_nonzero":RATIONAL_ENDPOINTS["power_nonzero"],"succ_ne_zero":RATIONAL_ENDPOINTS["succ_ne_zero"],
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "add_mul":"forall a b c. (a+b)*c=a*c+b*c",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(two_error="CV101",positive_order="CV075",power_nonzero="CV075",succ_ne_zero="CV075")
HELPER_DEPENDENCIES={
    "orders":("positive_order","mul_ne_zero","mul_assoc","mul_comm","add_mul"),
    "CV102":("two_error","orders","mul_ne_zero","power_nonzero","succ_ne_zero"),
}


class ExpRationalTwoErrorError(ValueError):
    """Changed valid rational comparison, normalization or either error term."""


def frozen_exp_rational_two_error_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=16 or len(premises)!=13 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRationalTwoErrorError("CV102 exact valid rational two-error bound changed")
    return target


def source_contract():
    return dict(code="CV102",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=13,two_supplied_recurrences_heads_sums_and_cutoff_power_preserved=True,
        independent_argument_denominators_initial_scales_and_horizons=True,
        all_rational_denominators_proved_nonzero=True,actual_cutoff_power_proved_nonzero=True,
        initial_scales_required_nonzero=True,argument_gap="d*y=e*x+g",argument_bound="y<=e",
        rational_bounds="s/a0<=t/b0<=s/a0+9*g/(d*e)+2/p",cutoff_power="p=2^m",
        zero_arguments_gap_cutoff_and_extra_horizon_allowed=True,new_induction_needed=False,
        code_number_equality_claimed=False,analytic_limit_claim=False,
        reused_definition_ids=["ND0382","ND0444"],new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def exp_rational_two_error_source_pins():
    result=exp_two_error_bound_source_pins()
    for name,pin in rational_tail_majorant_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpRationalTwoErrorError("rational two-error source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_two_error_bound.py":"df3b14dbae9c98536321540ac43a1fd804550da8bb8a26a5bb0664f2a24e92d1",
        "scripts/sqrt2_power_rational_tail_majorant.py":"9dc0903202c1c4922011503b997a6ad2556a8d59c8750f0a028b50da038a1776",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_rational_two_error.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRationalTwoErrorError("rational two-error source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _orders(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        D,p,E,a0,b0,z,out=t.terms(("D","p","E","a0","b0","s","t"))
        den=Mul(D,Mul(p,a0));first=Mul(D,Mul(p,z));error=Mul(E,a0);num=Add(first,error)
        den_nz=apply(specialize(t,"mul_ne_zero",D,Mul(p,a0)),t.hyp("D_nonzero"),
            apply(specialize(t,"mul_ne_zero",p,a0),t.hyp("p_nonzero"),t.hyp("a_nonzero")))
        lower=_subst(t,registry,"Le(slot,a0*t)",specialize(t,"mul_comm",b0,z),t.hyp("lower"))
        lower=_subst(t,registry,"Le(s*b0,slot)",specialize(t,"mul_comm",a0,out),lower)
        lower=apply(specialize(t,"positive_order",z,out,a0,b0),t.hyp("a_nonzero"),t.hyp("b_nonzero"),lower)
        upper=_subst(t,registry,"Le(slot,D*(p*(b0*s))+E*(a0*b0))",
            _multiplicative_equal(t,Mul(D,Mul(p,Mul(a0,out))),Mul(out,den)),t.hyp("upper"))
        right=_chain(CongAdd(
            _multiplicative_equal(t,Mul(D,Mul(p,Mul(b0,z))),Mul(first,b0)),
            _multiplicative_equal(t,Mul(E,Mul(a0,b0)),Mul(error,b0))),EqSym(specialize(t,"add_mul",first,error,b0)))
        upper=_subst(t,registry,"Le(t*(D*(p*a0)),slot)",right,upper)
        upper=apply(specialize(t,"positive_order",out,num,b0,den),t.hyp("b_nonzero"),den_nz,upper)
        return conjunction(lower,upper)
    return introduce(s,("D","p","E","a0","b0","s","t"),("D_nonzero","p_nonzero","a_nonzero","b_nonzero","lower","upper"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one);nine=Zero()
    for _ in range(9):
        nine=Succ(nine)
    def finish(t):
        d,e,g,p,m=t.terms(("d","e","g","p","m"));D=Mul(d,e)
        bounds=apply(specialize(t,"two_error",*t.terms(PARAMETERS)),
            *(t.hyp(label) for label in ("d_nonzero","e_nonzero","gap","argument","recurrence_a","recurrence_b","head_a","head_b","prefix_a","whole_b","power")))
        dnz=apply(specialize(t,"mul_ne_zero",d,e),t.hyp("d_nonzero"),t.hyp("e_nonzero"))
        positive=apply(specialize(t,"power_nonzero",two),specialize(t,"succ_ne_zero",one))
        pnz=apply(instantiate(positive,m,p),t.hyp("power"))
        E=Add(Mul(nine,Mul(g,p)),Mul(two,D))
        return apply(specialize(t,"orders",D,p,E,*t.terms(("a0","b0","s","t"))),
            dnz,pnz,t.hyp("a_nonzero"),t.hyp("b_nonzero"),AndElimL(bounds),AndElimR(bounds))
    return introduce(s,PARAMETERS,("d_nonzero","e_nonzero","a_nonzero","b_nonzero","gap","argument","recurrence_a","recurrence_b","head_a","head_b","prefix_a","whole_b","power"),finish)


def prove_exp_rational_two_error(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV102",target=frozen_exp_rational_two_error_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"orders":lambda s:_orders(s,registry),"CV102":_root},
        pins=exp_rational_two_error_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
