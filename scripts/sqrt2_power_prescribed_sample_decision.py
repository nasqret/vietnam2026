"""AP027: decide the complete supplied fixed-scale finite sample computation.

The predicate checks an actual factorial scale, positive scale/output head,
and every field of the unchanged sample graph. It contains no accuracy or
irrationality assertion. Canonical record construction and PR interpretation
remain distinct from this unconditional HA decidability theorem.
"""
from hashlib import sha256

from sqrt2_power_finite_table_decisions import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,_and,decision,
    DECISION_ARCHIVE,COMPONENT_ARCHIVE,finite_table_decisions_source_pins,
    HELPER_SOURCES as TABLE_HELPERS,_term,
)
from sqrt2_power_atomic_computation_decisions import HELPER_SOURCES as ATOMIC_HELPERS
from sqrt2_power_approximation_component_decisions import HELPER_SOURCES as COMPONENT_HELPERS
from sqrt2_power_exp_sample import (
    GRAPH,DEFINITION_PARAMETERS as PARAMETERS,NUMERATOR,DENOMINATOR,DEGREE,
    ARGUMENT_GRAPH,ARGUMENT_OUTPUTS,definition_registry,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-prescribed-sample-decision-v1"
CHECK_PARTS=("Factorial(S(2*k),D)","~D=0",GRAPH,"~w0=0")
CHECK_SOURCE=_and(CHECK_PARTS)
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+decision(CHECK_SOURCE)
TARGET_SHA256="0bfc201f0143e0b3fb6e1b1b1a23ea925cf898cbfb266cbfb272ce264b3275cd"
HELPER_SOURCES={
    "nonzero_dec":"forall a. "+decision("~a=0"),
    "argument_dec":"forall "+" ".join(("k",)+ARGUMENT_OUTPUTS)+". "+decision(ARGUMENT_GRAPH),
    "sample_dec":"forall "+" ".join(PARAMETERS)+". "+decision(GRAPH),
}
HELPER_TARGET_SHA256={
    "nonzero_dec":"de5b2929f57fd66204fe7e3945b4d04584bbaeb19bc80372263523196f39b4d9",
    "argument_dec":"2da13adf46770a1d6862a835732e8ccbdf3919c117b089480705abbeb9d9430c",
    "sample_dec":"41201e0aebb3230b3d2c6d52ca7793493baa0be28a8cb44edd0cddfeb52ae0f9",
}
TABLE_ARCHIVE=dict(case="AP026",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-finite-table-decisions-v1/generation-process.json.gz",
    bytes=43252,sha256="f04e1bbfcd6de2f8a1cb1c9ec6685639d991f9594b492debbd8df6d4418cde84",
    raw_bytes=473322,raw_sha256="c7093221979bee69440382a9692e013e616f3112d061930e913c889483a7b85d",
    bundle_bytes=251449,bundle_sha256="602f3a841c85f0210c2c54d4c23d406e6539f247b720acc6a07b04b76c495bb2",
    nodes=133,root=132,target_ast_sha256="6dbc10516866227c027792d1af728a7e88461da6be67734ad5f93540f85317ce")
ARCHIVES=(TABLE_ARCHIVE,COMPONENT_ARCHIVE,DECISION_ARCHIVE)
ENDPOINT_SOURCES={
    **{name:ATOMIC_HELPERS[name] for name in ("eq_dec","beta_dec","power_dec","factorial_dec","sum_dec")},
    **{name:COMPONENT_HELPERS[name] for name in ("dyadic_dec","horner_dec")},
    **{name:TABLE_HELPERS[name] for name in ("coefficient_prefix_dec","weight_table_dec","term_prefix_dec")},
}
ENDPOINT_OWNERS={name:"AP024" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(dyadic_dec="AP025",horner_dec="AP025",coefficient_prefix_dec="AP026",weight_table_dec="AP026",term_prefix_dec="AP026")
HELPER_DEPENDENCIES={
    "nonzero_dec":("eq_dec",),
    "argument_dec":("dyadic_dec","coefficient_prefix_dec","horner_dec","power_dec"),
    "sample_dec":("argument_dec","weight_table_dec","term_prefix_dec","beta_dec","factorial_dec","power_dec","eq_dec","sum_dec"),
    "AP027":("factorial_dec","nonzero_dec","sample_dec"),
}


class PrescribedSampleDecisionError(ValueError):
    """Changed fixed-scale, denominator validity or actual computation graph."""


def frozen_prescribed_sample_decision_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Or
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=16 or premises or type(conclusion) is not Or or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PrescribedSampleDecisionError("AP027 exact supplied sample decision changed")
    return target


def source_contract():
    return dict(code="AP027",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_fifteen_supplied_outputs_including_invalid_candidates=True,
        exact_original_sample_graph_preserved=True,prescribed_scale="(2*k+1)!",
        positive_scale_and_output_denominator_checked=True,arbitrary_precision_including_zero=True,
        deterministic_HA_conjunction_schema=True,new_definition_ids=[],definition_admissions=0,
        new_induction_needed=False,classical_axioms_used=False,markov_principle_used=False,
        complete_supplied_sample_decision=True,canonical_record_construction_claim=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,
        analytic_limit_claim=False,original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def prescribed_sample_decision_source_pins():
    result=finite_table_decisions_source_pins()
    expected={"scripts/sqrt2_power_finite_table_decisions.py":"294757210d9efb0f023d260d0da446b455ebd89879276e10c7cf21995b1906b8",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_prescribed_sample_decision.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PrescribedSampleDecisionError("sample decision source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _nonzero_dec(s):
    from peano_lab.kernel.proofs import OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Zero
    return introduce(s,("a",),(),lambda t:OrElim(specialize(t,"eq_dec",t.term("a"),Zero()),
        OrIntroR(introduce(t.hypothesis("zero"),(),("nonzero",),lambda u:apply(u.hyp("nonzero"),u.hyp("zero")))),
        OrIntroL(t.hypothesis("nonzero").hyp("nonzero"))))


def _decision_producer(name,*terms):
    return lambda s:specialize(s,name,*(_term(s,term) for term in terms))


def sequential_conjunction_decision(s,producers,label):
    """CPS schema: never use an unannotated OrElim as an eliminand.

Each yes branch proceeds to the next *synthesizable* supplied decision.
A no branch rejects the corresponding actual field of the whole predicate.
Only ordinary HA constructors are emitted; this adds no trusted rule.
"""
    from peano_lab.kernel.proofs import OrElim,OrIntroL,OrIntroR
    from sqrt2_power_quadratic_trace_exists import conjunction,field
    if not producers:
        raise PrescribedSampleDecisionError("empty sequential conjunction")
    def loop(t,index,positives):
        if index==len(producers):
            return OrIntroL(conjunction(*(t.hyp(name) for name in positives)))
        yes=label+"_yes_"+str(index);no=label+"_no_"+str(index);whole=label+"_whole_"+str(index)
        negative=OrIntroR(introduce(t.hypothesis(no),(),(whole,),lambda u:
            apply(u.hyp(no),field(u.hyp(whole),index,len(producers)))))
        return OrElim(producers[index](t),loop(t.hypothesis(yes),index+1,positives+(yes,)),negative)
    return loop(s,0,())


def _argument_dec(s):
    return introduce(s,("k",)+ARGUMENT_OUTPUTS,(),lambda t:sequential_conjunction_decision(t,(
        _decision_producer("dyadic_dec","k","d","s"),
        _decision_producer("coefficient_prefix_dec","D","ab","ac","S(2*k)"),
        _decision_producer("horner_dec","ab","ac","3","S(2*k)","x"),
        _decision_producer("power_dec","3","S(2*k)","p")),"argument"))


def _sample_dec(s):
    return introduce(s,PARAMETERS,(),lambda t:sequential_conjunction_decision(t,(
        _decision_producer("argument_dec",*(("k",)+ARGUMENT_OUTPUTS)),
        _decision_producer("weight_table_dec",DENOMINATOR,DEGREE,"wb","wc"),
        _decision_producer("term_prefix_dec",NUMERATOR,"wb","wc","tb","tc","S "+DEGREE),
        _decision_producer("beta_dec","wb","wc","0","w0"),
        _decision_producer("beta_dec","tb","tc","0","w0"),
        _decision_producer("factorial_dec",DEGREE,"f"),
        _decision_producer("power_dec",DENOMINATOR,DEGREE,"h"),
        _decision_producer("eq_dec","w0","f*h"),
        _decision_producer("sum_dec","tb","tc","S "+DEGREE,"y")),"sample"))


def _root(s):
    return introduce(s,PARAMETERS,(),lambda t:sequential_conjunction_decision(t,(
        _decision_producer("factorial_dec","S(2*k)","D"),
        _decision_producer("nonzero_dec","D"),
        _decision_producer("sample_dec",*PARAMETERS),
        _decision_producer("nonzero_dec","w0")),"prescribed"))


def factories():
    return dict(nonzero_dec=_nonzero_dec,argument_dec=_argument_dec,sample_dec=_sample_dec,AP027=_root)


def prove_prescribed_sample_decision(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP027",target=frozen_prescribed_sample_decision_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories(),pins=prescribed_sample_decision_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
