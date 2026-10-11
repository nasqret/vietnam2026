"""AP029: constructively decide an arbitrary supplied approximation record.

Decode the thirteen internal fields from the supplied beta code. Functional
uniqueness transports every competing record to those actual values; the
complete finite sample decision checks the resulting body. No unbounded
existential search, Markov principle or classical axiom is used.
"""
from hashlib import sha256

from sqrt2_power_approximation_record_exists import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,_and,OUTPUTS,INTERNAL,RECORD_FIELDS,RECORD_CHECKS,
    DEFINITION_NAME,DEFINITION_PARAMETERS,definition_registry,tuple_source,
    approximation_record_exists_source_pins,COMPOSITION_ARCHIVE,
)
from sqrt2_power_prescribed_sample_decision import (
    decision,sequential_conjunction_decision,prescribed_sample_decision_source_pins,
    NAMED_SOURCE as SAMPLE_DECISION_SOURCE,
)
from sqrt2_power_atomic_computation_decisions import HELPER_SOURCES as ATOMIC_HELPERS,ENDPOINT_SOURCES as ATOMIC_ENDPOINTS
from sqrt2_power_approximation_component_decisions import DECISION_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-approximation-record-decision-v1"
PARAMETERS=DEFINITION_PARAMETERS
FULL_PARAMETERS=PARAMETERS+INTERNAL
RECORD=DEFINITION_NAME+"("+",".join(PARAMETERS)+")"
BODY=_and(RECORD_CHECKS)
TUPLE_PARAMETERS=("rb","rc")+RECORD_FIELDS
PARTIAL=_and(tuple(f"BetaAt(rb,rc,{OUTPUTS.index(name)},{name})" for name in INTERNAL))
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+decision(RECORD)
TARGET_SHA256="b08c1a483e177d9fa80cb2c787464ff0ad2f2a27dc52543517056b1184e2896e"
HELPER_SOURCES={
    "tuple_dec":"forall "+" ".join(TUPLE_PARAMETERS)+". "+decision(tuple_source(RECORD_FIELDS)),
    "body_dec":"forall "+" ".join(FULL_PARAMETERS)+". "+decision(BODY),
    "transport":"forall "+" ".join(FULL_PARAMETERS)+". ("+PARTIAL+") -> "+RECORD+" -> "+BODY,
}
HELPER_TARGET_SHA256={
    "tuple_dec":"b12ac92f618d64e31306e0b962bece636d92e00c42ce71ef968325e0b3813d49",
    "body_dec":"8ffee5405fb8c716ea26f11b82d8da0704f9ce3964022c5f9d2a7e376aa02597",
    "transport":"e2ad6d9833cdcd1ae9259e17cd1713af88f4849e40185e9c19578c188a3e96fc",
}
SAMPLE_DECISION_ARCHIVE=dict(case="AP027",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-prescribed-sample-decision-v1/generation-process.json.gz",
    bytes=52392,sha256="8968f5e8b4f510eae0b3c1a7987fecbb7d8b96fd654f0024885b930a83aed7eb",
    raw_bytes=855555,raw_sha256="a0b917e232dbbb0df7846a82302632e5a07bc703655fe25a818f60b6cd7b0e33",
    bundle_bytes=487296,bundle_sha256="8a300a0f1234e476a3ad2e12a5d7bea7320b757d76fb8138689c7b2eff25a6ce",
    nodes=174,root=173,target_ast_sha256="0bfc201f0143e0b3fb6e1b1b1a23ea925cf898cbfb266cbfb272ce264b3275cd")
ARCHIVES=(SAMPLE_DECISION_ARCHIVE,DECISION_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={"sample_decision":SAMPLE_DECISION_SOURCE,"beta_dec":ATOMIC_HELPERS["beta_dec"],
    "beta_exists":ATOMIC_ENDPOINTS["beta_exists"],"beta_unique":ATOMIC_ENDPOINTS["beta_unique"]}
ENDPOINT_OWNERS=dict(sample_decision="AP027",beta_dec="AP024",beta_exists="CV061",beta_unique="CV061")
HELPER_DEPENDENCIES={"tuple_dec":("beta_dec",),"body_dec":("tuple_dec","sample_decision"),
    "transport":("beta_unique",),"AP029":("beta_exists","body_dec","transport")}


class ApproximationRecordDecisionError(ValueError):
    """Changed decoded field, actual record body, equality transport or source."""


def frozen_approximation_record_decision_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Or
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=5 or premises or type(conclusion) is not Or or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ApproximationRecordDecisionError("AP029 exact supplied record decision changed")
    return target


def source_contract():
    return dict(code="AP029",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,arbitrary_supplied_record_codes_and_outputs=True,record_code_components=2,
        all_thirteen_internal_values_actually_decoded=True,two_output_slots_checked=True,
        all_competing_fields_transported_by_actual_beta_uniqueness=True,
        supplied_full_computation_decision_replayed=True,unbounded_existential_search_used=False,
        classical_axioms_used=False,markov_principle_used=False,new_definition_ids=[],
        reused_record_definition_id="ND0449",definition_admissions=0,new_induction_needed=False,
        single_natural_packing_claim=False,canonical_PR_approximation_algorithm_claim=False,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def approximation_record_decision_source_pins():
    result=approximation_record_exists_source_pins()
    for name,pin in prescribed_sample_decision_source_pins().items():
        if name in result and result[name]!=pin:
            raise ApproximationRecordDecisionError("record decision source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_approximation_record_exists.py":"a6a83ae09292398d9a690753164840f581d9e3b43aa7c5475d6514c917cb911a",
        "scripts/sqrt2_power_prescribed_sample_decision.py":"6d64944f6b020a42152ec829fba3c5c49890f9183b138c5959aafc51acbfd012",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_approximation_record_decision.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ApproximationRecordDecisionError("record decision source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _tuple_dec(s):
    from peano_lab.kernel.terms import parse_term
    producers=tuple(lambda t,i=i,name=name:specialize(t,"beta_dec",*t.terms(("rb","rc")),parse_term(str(i)),t.term(name)) for i,name in enumerate(RECORD_FIELDS))
    return introduce(s,TUPLE_PARAMETERS,(),lambda t:sequential_conjunction_decision(t,producers,"tuple"))


def _body_dec(s):
    from peano_lab.kernel.terms import Add,parse_term
    return introduce(s,FULL_PARAMETERS,(),lambda t:sequential_conjunction_decision(t,(
        lambda u:specialize(u,"tuple_dec",*u.terms(TUPLE_PARAMETERS)),
        lambda u:specialize(u,"sample_decision",Add(u.term("n"),parse_term("8")),*u.terms(RECORD_FIELDS))),"body"))


def body_source(mapping):
    fields=tuple(mapping.get(name,name) for name in RECORD_FIELDS)
    scale=mapping.get("D","D")
    graph="NatSqrt2ExpSample("+",".join(("n+8",)+fields)+")"
    return _and((tuple_source(fields),f"Factorial(S(2*(n+8)),{scale})",f"~{scale}=0",graph,"~ud=0"))


def _transport(s,registry):
    from peano_lab.kernel.terms import parse_term
    candidates=tuple("candidate_"+name for name in INTERNAL)
    def opened(t):
        mapping=dict(zip(INTERNAL,candidates));proof=t.hyp("record_body")
        for partial_index,name in enumerate(INTERNAL):
            slot=OUTPUTS.index(name)
            equal=apply(specialize(t,"beta_unique",*t.terms(("rb","rc")),parse_term(str(slot)),*t.terms((mapping[name],name))),
                field(field(t.hyp("record_body"),0,5),slot,15),field(t.hyp("decoded"),partial_index,len(INTERNAL)))
            motive=dict(mapping);motive[name]="slot"
            proof=_subst(t,registry,body_source(motive),equal,proof)
            mapping[name]=name
        return proof
    return introduce(s,FULL_PARAMETERS,("decoded","record"),lambda t:
        eliminate(t,t.hyp("record"),candidates,"record_body",opened))


def _root(s):
    from peano_lab.kernel.proofs import OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import parse_term
    def decoded(t):
        positive=OrIntroL(witness(t.terms(INTERNAL),t.hypothesis("valid_body").hyp("valid_body")))
        # Existential introduction uses no term binder; the witnesses remain
        # in this current decoded-value scope, including in the yes branch.
        def no(u):
            def contradiction(v):
                actual=conjunction(*(v.hyp("actual_"+name) for name in INTERNAL))
                transported=apply(specialize(v,"transport",*v.terms(FULL_PARAMETERS)),actual,v.hyp("candidate_record"))
                return apply(v.hyp("invalid_body"),transported)
            return OrIntroR(introduce(u,(),("candidate_record",),contradiction))
        return OrElim(specialize(t,"body_dec",*t.terms(FULL_PARAMETERS)),positive,no(t.hypothesis("invalid_body")))
    def decode(t,index):
        if index==len(INTERNAL):
            return decoded(t)
        name=INTERNAL[index];slot=OUTPUTS.index(name)
        actual=specialize(t,"beta_exists",*t.terms(("rb","rc")),parse_term(str(slot)))
        return eliminate(t,actual,(name,),"actual_"+name,lambda u:decode(u,index+1))
    return introduce(s,PARAMETERS,(),lambda t:decode(t,0))


def factories(registry):
    return dict(tuple_dec=_tuple_dec,body_dec=_body_dec,transport=lambda s:_transport(s,registry),AP029=_root)


def prove_approximation_record_decision(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP029",target=frozen_approximation_record_decision_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories(registry),pins=approximation_record_decision_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
