"""AP013: uniform sample errors for every finite precision increment.

Constructive zero/successor elimination joins exact value independence at
equal precision with AP012 at strictly finer precision. Both supplied full
computation graphs and positive coefficient scales remain explicit premises.
"""
from hashlib import sha256

from sqrt2_power_exp_sample_uniform_error import (
    ROOT,Scope,introduce,conjunction,apply,specialize,field,canonical,json_hash,_and,
    definition_registry,PARAMETERS,COARSE_GRAPH,COEFFICIENT,PARTS,BOUND_ARCHIVE,
    NAMED_SOURCE as STRICT_SOURCE,exp_sample_uniform_error_source_pins,
)
from sqrt2_power_exp_sample_modulus import COARSE_PARAMETERS,FINE_OUTPUTS,SQUARE_SOURCE
from sqrt2_power_exp_sample_independence import NAMED_SOURCE as INDEPENDENCE_SOURCE,exp_sample_independence_source_pins
from sqrt2_power_quadratic_trace_exists import eliminate,witness
from sqrt2_power_exp_two_sided_continuity import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-sample-all-precision-v1"
FINE_GRAPH="NatSqrt2ExpSample(k+l,"+",".join(FINE_OUTPUTS)+")"
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~D=0 -> ~E=0 -> "+COARSE_GRAPH+" -> "+FINE_GRAPH+" -> "+_and(PARTS)
TARGET_SHA256="2ea71d464e47c52e625a986dcb55ac5c92ff24daf2fd7b95c71d36d58aad8634"
HELPER_SOURCES={"equal_bounds":"forall d x y h. x=y -> Le(d*x,d*y+"+COEFFICIENT+"*h) /\\ Le(d*y,d*x+"+COEFFICIENT+"*h)"}
HELPER_TARGET_SHA256={"equal_bounds":"2dd9f12b9fa5b9520aae1fb5c9f2051a724c6deca10ac36af5e8f3c55a492c84"}
STRICT_ARCHIVE=dict(case="AP012",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-sample-uniform-error-v1/generation-process.json.gz",
    bytes=103212,sha256="e9e80f6a9e2697fa9a0da4add07d534e1a4d5c23b56dd3fc59b8be03d1a8d671",
    raw_bytes=2223913,raw_sha256="230104a5d51b7d2dba30ab4fb5fbc340031ef88b02aec163f4533f88624f04a5",
    bundle_bytes=1339338,bundle_sha256="9de719a1127b72d5a0df0d7779b1ebf2906193ecac0502489e9b1830fd49cbe5",
    nodes=282,root=281,target_ast_sha256="309286b62c9ba3f6357861cfacebc829369cbcc7919b6c039df4852a2f7bfb99")
INDEPENDENCE_ARCHIVE=dict(case="AP005",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-sample-independence-v1/generation-process.json.gz",
    bytes=73918,sha256="28b8fec85143194adf882f6dc90e01d5362d1d2dbaefc748f27c982ba277713f",
    raw_bytes=1378379,raw_sha256="ca83a4c58eec5b8978295dca8cd80b0aa1922b93fc7e417b0ba52f546bd5ce64",
    bundle_bytes=816597,bundle_sha256="65f5079b7765f94e219fa59d809d727dfde3de1071327445909b47c1fa4a2ab8",
    nodes=228,root=227,target_ast_sha256="7b3f310db54974c295475b7f400dc4530ba3125902894517b92112b35c6d7383")
ARCHIVES=(STRICT_ARCHIVE,INDEPENDENCE_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={"strict":STRICT_SOURCE,"independence":INDEPENDENCE_SOURCE,"square":SQUARE_SOURCE,
    "zero_or_succ":"forall n. n=0 \\/ exists k. n=S k","add_comm":"forall a b. a+b=b+a"}
ENDPOINT_OWNERS=dict(strict="AP012",independence="AP005",square="AP012",zero_or_succ="CV071",add_comm="CV071")
HELPER_DEPENDENCIES={"equal_bounds":("add_comm",),"AP013":("strict","independence","square","zero_or_succ","equal_bounds")}


class ExpSampleAllPrecisionError(ValueError):
    """Changed all-increment coverage, supplied computations or uniform bound."""


def frozen_exp_sample_all_precision_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=32 or len(premises)!=4 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSampleAllPrecisionError("AP013 exact all-increment sample-error target changed")
    return target


def source_contract():
    return dict(code="AP013",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,both_supplied_complete_sample_graphs_preserved=True,positive_coefficient_scales_required=True,
        all_precision_indices_and_increments_including_zero=True,constructive_zero_successor_split=True,
        equal_precision_uses_actual_value_independence=True,uniform_two_sided_error="((9*3)+2)/d",dyadic_denominator="d=2^k",
        positive_output_denominators_proved=True,new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_sample_all_precision_source_pins():
    result=exp_sample_uniform_error_source_pins()
    for name,pin in exp_sample_independence_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpSampleAllPrecisionError("all-precision sample source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_sample_uniform_error.py":"cd6f06f57d48a78a0313db6758e45e2d245462171536a84ac2494551b82388e3",
        "scripts/sqrt2_power_exp_sample_independence.py":"e6ec0523040135408adbadfc5cf46351f4682bd6a3b1f564c08263f8cb692187",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_sample_all_precision.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSampleAllPrecisionError("all-precision source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _equal_bounds(s):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,parse_term
    coefficient=parse_term(COEFFICIENT)
    def finish(t):
        d,x,y,h=t.terms(("d","x","y","h"));error=Mul(coefficient,h)
        forward=witness((error,),_chain(specialize(t,"add_comm",error,Mul(d,x)),CongAdd(CongMul(EqRefl(d),t.hyp("equal")),EqRefl(error))))
        backward=witness((error,),_chain(specialize(t,"add_comm",error,Mul(d,y)),CongAdd(CongMul(EqRefl(d),EqSym(t.hyp("equal"))),EqRefl(error))))
        return conjunction(forward,backward)
    return introduce(s,("d","x","y","h"),("equal",),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,EqRefl,EqSym,OrElim
    from peano_lab.kernel.terms import Mul
    supplied="NatSqrt2ExpSample(slot,"+",".join(FINE_OUTPUTS)+")"
    def zero(t):
        k,d,root,w0,v0,y,o=t.terms(("k","d","s","w0","v0","y","o"))
        precision=_chain(CongAdd(EqRefl(k),t.hyp("zero")),instantiate(Axiom("PA3"),k))
        fine=_subst(t,registry,supplied,precision,t.hyp("fine"))
        independent=apply(specialize(t,"independence",*t.terms(COARSE_PARAMETERS+FINE_OUTPUTS)),
            t.hyp("D_nonzero"),t.hyp("E_nonzero"),t.hyp("coarse"),fine)
        dyadic=field(field(t.hyp("coarse"),0,9),0,4)
        square=apply(specialize(t,"square",k,d,root),dyadic)
        bounds=apply(specialize(t,"equal_bounds",d,Mul(w0,o),Mul(v0,y),Mul(w0,v0)),EqSym(field(independent,2,3)))
        return conjunction(field(square,0,6),field(independent,0,3),field(independent,1,3),AndElimL(bounds),AndElimR(bounds))
    def positive(t):
        fine=_subst(t,registry,supplied,CongAdd(EqRefl(t.term("k")),t.hyp("successor")),t.hyp("fine"))
        return apply(specialize(t,"strict",t.term("k"),t.term("increment"),*t.terms(PARAMETERS[2:])),
            t.hyp("D_nonzero"),t.hyp("E_nonzero"),t.hyp("coarse"),fine)
    def finish(t):
        left=t.hypothesis("zero");right=t.hypothesis("positive")
        return OrElim(specialize(t,"zero_or_succ",t.term("l")),zero(left),eliminate(right,right.hyp("positive"),("increment",),"successor",positive))
    return introduce(s,PARAMETERS,("D_nonzero","E_nonzero","coarse","fine"),finish)


def prove_exp_sample_all_precision(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP013",target=frozen_exp_sample_all_precision_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"equal_bounds":_equal_bounds,"AP013":lambda s:_root(s,registry)},
        pins=exp_sample_all_precision_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
