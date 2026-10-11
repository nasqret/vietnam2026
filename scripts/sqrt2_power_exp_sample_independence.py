"""AP005: finite sample rational values are independent of all encodings.

Keep both supplied complete computation graphs, with independent positive
coefficient scales and normalization heads. Apply finite continuity in both
directions at zero argument gap; ordinary antisymmetry gives value equality.
"""
from hashlib import sha256

from sqrt2_power_supplied_exp_sample import (
    ROOT,Scope,introduce,conjunction,apply,specialize,field,canonical,json_hash,_and,
    definition_registry,supplied_exp_sample_source_pins,NAMED_SOURCE as SUPPLIED_SOURCE,
    PARAMETERS as LEFT,GRAPH as LEFT_GRAPH,
)
from sqrt2_power_log_root_independence import NAMED_SOURCE as ARGUMENT_SOURCE,log_root_independence_source_pins
from sqrt2_power_exp_cross_continuity import NAMED_SOURCE as CONTINUITY_SOURCE,exp_cross_continuity_source_pins
from sqrt2_power_exp_rational_continuity import CROSS_ARCHIVE
from sqrt2_power_quadratic_trace_exists import witness
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-sample-independence-v1"
RIGHT=("k","e","t","E","bb","bc","z","q","vb","vc","ub","uc","v0","g","r","o")
PARAMETERS=LEFT+RIGHT[1:]
RIGHT_GRAPH="NatSqrt2ExpSample("+",".join(RIGHT)+")"
PARTS=("~w0=0","~v0=0","v0*y=w0*o")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~D=0 -> ~E=0 -> "+LEFT_GRAPH+" -> "+RIGHT_GRAPH+" -> "+_and(PARTS)
TARGET_SHA256="7b3f310db54974c295475b7f400dc4530ba3125902894517b92112b35c6d7383"
VALUE_PARAMETERS=("d","e","x","y","N","ab","ac","bb","bc","a0","b0","s","t")
VALUE_PREMISES=("~d=0","~e=0","x*e=y*d","Le(x,d)","Le(y,e)",
    "NatScaledExpRecurrence(d,x,ab,ac,N)","NatScaledExpRecurrence(e,y,bb,bc,N)",
    "BetaAt(ab,ac,0,a0)","BetaAt(bb,bc,0,b0)","Sum(ab,ac,S N,s)","Sum(bb,bc,S N,t)")
HELPER_SOURCES={
    "bound_two":"forall a b. Le(a,b) -> Le(a,2*b)",
    "zero_gaps":"forall d e x y. x*e=y*d -> d*y=e*x+0 /\\ e*x=d*y+0",
    "same_value":"forall "+" ".join(VALUE_PARAMETERS)+". "+" -> ".join(VALUE_PREMISES)+" -> b0*s=a0*t",
}
HELPER_TARGET_SHA256={"bound_two":"4bedee01192037e86762e6767a5e12cad0b2dc565703e855278895e255f26f17",
    "zero_gaps":"9acadfcdfe1d2c5f711f0ce4e926862578dd8fcb19e02021c4f73fd957182ec4",
    "same_value":"e49fc8ca2872c006eed007d35e4b299c9c836e1d450555ba18ed4e423534e68b"}
SUPPLIED_ARCHIVE=dict(case="AP004",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-supplied-exp-sample-v1/generation-process.json.gz",
    bytes=47760,sha256="f2d77283b61476acb79dcccd322940092bea2f94b35834c7443f1955153082b6",
    raw_bytes=670501,raw_sha256="63241daa85784b77d9601ea6ee098d492c0fa5d56f1063f126f62d330b3cc4ac",
    bundle_bytes=376642,bundle_sha256="07e3c3a0d8f95c3c80461832be66d79d54ccd6da2c213b6995af7c451fc22669",
    nodes=152,root=151,target_ast_sha256="2579d5bd54a8bf1f91831ce86386ca747605c6022da544548553dc22186cb198")
INDEPENDENCE_ARCHIVE=dict(case="AP003",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-log-root-independence-v1/generation-process.json.gz",
    bytes=47369,sha256="36d8a9ef9053fe3fbda72c2931b6c9fbc87495f59574f4ee34af3ff919efa103",
    raw_bytes=605936,raw_sha256="eba88cbeea6cd83cae6aacac7e02a6a02cd7fc70c6ea8f0d068f93b28bdf56cd",
    bundle_bytes=338239,bundle_sha256="f4e8128b5ee924559e644bcabad76116cb70ba4ab8b2c5a9f60e54c38b765a5e",
    nodes=156,root=155,target_ast_sha256="a257baf8204aa80c57093525ce2915cb7d327803c89e4469be4206000abc6665")
ARCHIVES=(SUPPLIED_ARCHIVE,INDEPENDENCE_ARCHIVE,CROSS_ARCHIVE)
ENDPOINT_SOURCES={
    "supplied":SUPPLIED_SOURCE,"argument_independence":ARGUMENT_SOURCE,"continuity":CONTINUITY_SOURCE,
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "le_antisym":"forall a b. Le(a,b) -> Le(b,a) -> a=b",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b","one_mul":"forall a. 1*a=a",
    "mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS={name:"CV098" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(supplied="AP004",argument_independence="AP003",le_antisym="AP003")
HELPER_DEPENDENCIES={
    "bound_two":("mul_succ_left","one_mul","le_trans"),"zero_gaps":("mul_comm",),
    "same_value":("bound_two","zero_gaps","continuity","le_antisym"),
    "AP005":("supplied","argument_independence","same_value"),
}


class ExpSampleIndependenceError(ValueError):
    """Changed supplied graphs, precision, positivity guards or value equality."""


def frozen_exp_sample_independence_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=31 or len(premises)!=4 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSampleIndependenceError("AP005 exact independent sample-value target changed")
    return target


def source_contract():
    return dict(code="AP005",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,both_supplied_complete_sample_graphs_preserved=True,positive_coefficient_scales_required=True,
        independent_table_codes_scales_and_output_heads_allowed=True,same_precision_required=True,
        both_output_denominators_proved_nonzero=True,exact_rational_output_value_identity=True,
        natural_identity="v0*y=w0*o",all_precision_indices_including_zero=True,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_sample_independence_source_pins():
    result=supplied_exp_sample_source_pins()
    for source in (log_root_independence_source_pins(),exp_cross_continuity_source_pins()):
        for name,pin in source.items():
            if name in result and result[name]!=pin:
                raise ExpSampleIndependenceError("sample independence source disagreement")
            result[name]=pin
    expected={"scripts/sqrt2_power_supplied_exp_sample.py":"30423d296b32b21ea9d3c35802cb81dbe5dae1fb4a589f8a8abce112e93be11a",
        "scripts/sqrt2_power_log_root_independence.py":"7c1d62bd16575e8c0aec4318715c55cd8fc009f77224aba17e879b2bc8be091a",
        "scripts/sqrt2_power_exp_cross_continuity.py":"df8ebc21517107b814a6f1e55903bb412d37a5b09917eeef6a47930b557b0bcd",
        "scripts/sqrt2_power_exp_rational_continuity.py":"70c6fce20acd01244345eb8e443a262cb6361992b806d6404bb54cabf6df11da",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_sample_independence.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSampleIndependenceError("sample independence source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _bound_two(s):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish(t):
        a,b=t.terms(("a","b"))
        double=_chain(specialize(t,"mul_succ_left",one,b),CongAdd(specialize(t,"one_mul",b),EqRefl(b)))
        upper=witness((b,),EqSym(double))
        return apply(specialize(t,"le_trans",a,b,Mul(two,b)),t.hyp("bound"),upper)
    return introduce(s,("a","b"),("bound",),finish)


def _zero_gaps(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        d,e,x,y=t.terms(("d","e","x","y"))
        left=_chain(specialize(t,"mul_comm",d,y),EqSym(t.hyp("cross")),specialize(t,"mul_comm",x,e),EqSym(instantiate(Axiom("PA3"),Mul(e,x))))
        right=_chain(specialize(t,"mul_comm",e,x),t.hyp("cross"),specialize(t,"mul_comm",y,d),EqSym(instantiate(Axiom("PA3"),Mul(d,y))))
        return conjunction(left,right)
    return introduce(s,("d","e","x","y"),("cross",),finish)


def _same_value(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Zero
    def finish(t):
        d,e,x,y,N,ab,ac,bb,bc,a0,b0,u,v=t.terms(VALUE_PARAMETERS)
        gaps=apply(specialize(t,"zero_gaps",d,e,x,y),t.hyp("cross"))
        abound=apply(specialize(t,"bound_two",x,d),t.hyp("bound_a"))
        bbound=apply(specialize(t,"bound_two",y,e),t.hyp("bound_b"))
        forward=apply(specialize(t,"continuity",d,e,x,y,Zero(),N,ab,ac,bb,bc,a0,b0,u,v),
            t.hyp("d_nonzero"),t.hyp("e_nonzero"),AndElimL(gaps),bbound,
            t.hyp("recurrence_a"),t.hyp("recurrence_b"),t.hyp("head_a"),t.hyp("head_b"),t.hyp("sum_a"),t.hyp("sum_b"))
        backward=apply(specialize(t,"continuity",e,d,y,x,Zero(),N,bb,bc,ab,ac,b0,a0,v,u),
            t.hyp("e_nonzero"),t.hyp("d_nonzero"),AndElimR(gaps),abound,
            t.hyp("recurrence_b"),t.hyp("recurrence_a"),t.hyp("head_b"),t.hyp("head_a"),t.hyp("sum_b"),t.hyp("sum_a"))
        return apply(specialize(t,"le_antisym",Mul(b0,u),Mul(a0,v)),AndElimL(forward),AndElimL(backward))
    return introduce(s,VALUE_PARAMETERS,("d_nonzero","e_nonzero","cross","bound_a","bound_b",
        "recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b"),finish)


def _root(s):
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two=Succ(Succ(Zero()));three=Succ(two)
    def finish(t):
        left=t.hyp("left");right=t.hyp("right")
        a=apply(specialize(t,"supplied",*t.terms(LEFT)),t.hyp("D_nonzero"),left)
        b=apply(specialize(t,"supplied",*t.terms(RIGHT)),t.hyp("E_nonzero"),right)
        equal=apply(specialize(t,"argument_independence",*t.terms(("k","d","s","D","ab","ac","x","p","e","t","E","bb","bc","z","q"))),
            t.hyp("D_nonzero"),t.hyp("E_nonzero"),field(left,0,9),field(right,0,9))
        k,d,root,D,x,p,e,out,E,z,q=t.terms(("k","d","s","D","x","p","e","t","E","z","q"))
        value=apply(specialize(t,"same_value",Mul(Mul(D,p),root),Mul(Mul(E,q),out),Mul(Mul(three,x),d),Mul(Mul(three,z),e),Add(k,two),
            *t.terms(("tb","tc","ub","uc","w0","v0","y","o"))),
            field(a,1,5),field(b,1,5),field(equal,5,6),field(a,2,5),field(b,2,5),
            field(a,3,5),field(b,3,5),field(left,4,9),field(right,4,9),field(left,8,9),field(right,8,9))
        return conjunction(field(a,0,5),field(b,0,5),value)
    return introduce(s,PARAMETERS,("D_nonzero","E_nonzero","left","right"),finish)


def prove_exp_sample_independence(*,limits=None):
    return assemble_mixed_certificate(code="AP005",target=frozen_exp_sample_independence_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"bound_two":_bound_two,"zero_gaps":_zero_gaps,"same_value":_same_value,"AP005":_root},
        pins=exp_sample_independence_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
