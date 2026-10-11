"""AP030: two actual records at one precision represent the same rational.

Open both finite computations and replay the exact sample-independence body.
Positive denominators are conclusions; beta code numbers need not be equal.
"""
from hashlib import sha256

from sqrt2_power_approximation_record_exists import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,canonical,json_hash,
    OUTPUTS,INTERNAL,definition_registry,approximation_record_exists_source_pins,
)
from sqrt2_power_exp_sample_independence import NAMED_SOURCE as INDEPENDENCE_SOURCE,exp_sample_independence_source_pins
from sqrt2_power_exp_sample_all_precision import INDEPENDENCE_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-approximation-record-independence-v1"
PARAMETERS=("n","up","ud","rb","rc","vp","vd","sb","sc")
LEFT="NatSqrt2ApproxRecord(n,up,ud,rb,rc)"
RIGHT="NatSqrt2ApproxRecord(n,vp,vd,sb,sc)"
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+LEFT+" -> "+RIGHT+" -> ~ud=0 /\\ (~vd=0 /\\ vd*up=ud*vp)"
TARGET_SHA256="a2ccad96f8bb3ab29d434fafb17dcb326788759f0a66e60ec0707f9212c8f99b"
ARCHIVES=(INDEPENDENCE_ARCHIVE,)
ENDPOINT_SOURCES={"independence":INDEPENDENCE_SOURCE}
ENDPOINT_OWNERS={"independence":"AP005"}
HELPER_DEPENDENCIES={"AP030":("independence",)}


class ApproximationRecordIndependenceError(ValueError):
    """Changed common precision, actual records or rational equality."""


def frozen_approximation_record_independence_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=9 or len(premises)!=2 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ApproximationRecordIndependenceError("AP030 exact record independence changed")
    return target


def source_contract():
    return dict(code="AP030",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,both_actual_records_required=True,common_precision_required=True,
        both_output_denominators_proved_nonzero=True,rational_output_equality="vd*up=ud*vp",
        beta_code_number_equality_claim=False,actual_AP005_body_replayed=True,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,
        analytic_limit_claim=False,original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def approximation_record_independence_source_pins():
    result=approximation_record_exists_source_pins()
    for name,pin in exp_sample_independence_source_pins().items():
        if name in result and result[name]!=pin:
            raise ApproximationRecordIndependenceError("record independence source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_approximation_record_exists.py":"a6a83ae09292398d9a690753164840f581d9e3b43aa7c5475d6514c917cb911a",
        "scripts/sqrt2_power_exp_sample_independence.py":"e6ec0523040135408adbadfc5cf46351f4682bd6a3b1f564c08263f8cb692187",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_approximation_record_independence.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ApproximationRecordIndependenceError("record independence source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from peano_lab.kernel.terms import Add,parse_term
    left=tuple("left_"+name for name in INTERNAL);right=tuple("right_"+name for name in INTERNAL)
    def values(t,prefix,num,den):
        return tuple(t.term(num if name=="y" else den if name=="w0" else prefix+name) for name in OUTPUTS)
    def opened(t):
        theorem=specialize(t,"independence",Add(t.term("n"),parse_term("8")),
            *values(t,"left_","up","ud"),*values(t,"right_","vp","vd"))
        return apply(theorem,field(t.hyp("left_body"),2,5),field(t.hyp("right_body"),2,5),
            field(t.hyp("left_body"),3,5),field(t.hyp("right_body"),3,5))
    return introduce(s,PARAMETERS,("left_record","right_record"),lambda t:
        eliminate(t,t.hyp("left_record"),left,"left_body",lambda u:
            eliminate(u,u.hyp("right_record"),right,"right_body",opened)))


def prove_approximation_record_independence(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP030",target=frozen_approximation_record_independence_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"AP030":_root},pins=approximation_record_independence_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
