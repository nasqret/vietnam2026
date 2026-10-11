"""AP028: construct a genuine beta-coded finite approximation record.

All fifteen decoded fields are consumed by the fixed factorial/sample graph.
The two beta-code components are explicit; no opaque trace, canonical code
number, accuracy claim or unproved single-natural packing is introduced.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_factorial_exp_sample import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,_and,OUTPUTS,factorial_exp_sample_source_pins,
    NAMED_SOURCE as SAMPLE_SOURCE,definition_registry as sample_registry,
)
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-approximation-record-exists-v1"
DEFINITION_ID="ND0449"
DEFINITION_NAME="NatSqrt2ApproxRecord"
DEFINITION_PARAMETERS=("n","up","ud","rb","rc")
INTERNAL=tuple(name for name in OUTPUTS if name not in ("y","w0"))
RECORD_FIELDS=tuple("up" if name=="y" else "ud" if name=="w0" else name for name in OUTPUTS)


def tuple_source(fields,b="rb",c="rc"):
    if not 1<=len(fields)<=15:
        raise ValueError("record tuple must have one through fifteen fields")
    return _and(tuple(f"BetaAt({b},{c},{i},{name})" for i,name in enumerate(fields)))


RECORD_TUPLE=tuple_source(RECORD_FIELDS)
RECORD_GRAPH="NatSqrt2ExpSample("+",".join(("n+8",)+RECORD_FIELDS)+")"
RECORD_CHECKS=(RECORD_TUPLE,"Factorial(S(2*(n+8)),D)","~D=0",RECORD_GRAPH,"~ud=0")
DEFINITION_SOURCE="exists "+" ".join(INTERNAL)+". "+_and(RECORD_CHECKS)
DEFINITION_DEPENDENCIES=("BetaAt","Factorial","NatSqrt2ExpSample")
DEFINITION_AST_SHA256="64a65448049a5b5cb095689a34832af97976dc1a92fdf1131cb9ce87ff37f381"
NAMED_SOURCE="forall n. exists up ud rb rc. NatSqrt2ApproxRecord(n,up,ud,rb,rc)"
TARGET_SHA256="6ff27609504236182a615ce1dd07fddf1b3d1c7d0161d869bb756ac824c4ef8e"
HELPER_SOURCES={"tuple_"+str(length):"forall "+" ".join(OUTPUTS[:length])+". exists rb rc. "+tuple_source(OUTPUTS[:length]) for length in range(1,16)}
HELPER_TARGET_SHA256={
    "tuple_1":"569fd90bdb5ed2d8a7b4c5006e158d9a9230a4ad7d4301958577220ecbd541e1",
    "tuple_2":"6569357a00e42a96ee81e0684858e1b42f25be4cc5404bebaafe97c65e897120",
    "tuple_3":"ae9e351078873823bdb3f7dc11cbff3648269fc852521386deaf6bd56b1d4576",
    "tuple_4":"d0d6f983a07277cb42779dbe48df00c4f973d740db429cbb4fdb60e6d908f58c",
    "tuple_5":"bfbbdac1b5dd8e1c55bc45887d0a36ea39abf72402cca0c18ecfbbe6769e6ff6",
    "tuple_6":"c9197dfde5eb66c64dad7693d6e722473bab0b692e89614de2da8f51c4236b07",
    "tuple_7":"324af33e50aa2c8600afffead916936eb094b5c9b72d99f81084a133019f55d5",
    "tuple_8":"585e64932f00d157f01b051658c92e91b25e4699a32bdc267443e54e2c5dff66",
    "tuple_9":"8acb57b37c7313f851e8c4627d2021c396b1bb3a4b08c718d25e49fcce1ac8d2",
    "tuple_10":"ca33bb2170bb4d352689ed8a27d8596f50bb995dd643e83db7ddddfb5db1c234",
    "tuple_11":"82e448f25df0bb80f95535573bbfa3ea6dbbb3fc1ad5c8afd8d4c909e5023bd3",
    "tuple_12":"98c16626f896653551d1bdc543e19abafca9eb3fb001ef3823f11f3324236041",
    "tuple_13":"f52c72c795668d90b670ed2950c9ea21798182cc0ce375b54e77134557f8a6fb",
    "tuple_14":"5dac9668ed27a86e4de3bd3c621810618207ac9acb3ef4f57a7b57c8e6a8cd0b",
    "tuple_15":"5ed6737fc88b0858b8ee87cd1beceff8817519f1afe7f793aeefffc9fda8abbc",
}
SAMPLE_ARCHIVE=dict(case="AP023",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-factorial-exp-sample-v1/generation-process.json.gz",
    bytes=56490,sha256="fdd75a3cdd71e3ef0547624d7abd0cb68bec24abe9379fdd88f33ec97c1ddf8e",
    raw_bytes=938650,raw_sha256="63455f1178fb3182eec94379c7b0f5675bb94ecf08a253a62f1eb2078a8e80de",
    bundle_bytes=543376,bundle_sha256="c16e77ecbdceec882bf43df4a345bd3a875fc7d0f4225e50983785e982294a61",
    nodes=190,root=189,target_ast_sha256="a49dec85075c8e059c999c262ce992200a03c7c1611ff0d9003643f5237b1fcf")
ARCHIVES=(SAMPLE_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={"sample_exists":SAMPLE_SOURCE,
    "beta_extend":"forall N b c v. exists eb ec. BetaAt(eb,ec,N,v) /\\ (forall j a. Lt(j,N) -> BetaAt(b,c,j,a) -> BetaAt(eb,ec,j,a))",
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)"}
ENDPOINT_OWNERS=dict(sample_exists="AP023",beta_extend="CV061",le_refl="CV061",le_succ="CV061")
HELPER_DEPENDENCIES={"tuple_1":("beta_extend",),
    **{"tuple_"+str(length):("tuple_"+str(length-1),"beta_extend","le_refl","le_succ") for length in range(2,16)},
    "AP028":("sample_exists","tuple_15")}


class ApproximationRecordExistsError(ValueError):
    """Changed consumed record field, actual computation, shift or source."""


def definition_registry():
    from sqrt2_power_definitions import PARENT,parse_named
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.library.proof_bundle import encode_formula
    result=dict(sample_registry());historical=json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids={spec.stable_id for spec in result.values()}|{row['id'] for row in historical}|{f"ND{i:04d}" for i in range(382,449)}
    if DEFINITION_ID in ids or DEFINITION_NAME in result or any(row['name']==DEFINITION_NAME for row in historical):
        raise ApproximationRecordExistsError("actual record definition collision")
    formula=parse_named(DEFINITION_SOURCE,DEFINITION_PARAMETERS,result)
    if json_hash(encode_formula(formula))!=DEFINITION_AST_SHA256:
        raise ApproximationRecordExistsError("actual record conservative expansion changed")
    source=pretty_formula(formula,list(DEFINITION_PARAMETERS))
    spec=_definition(stable_id=DEFINITION_ID,name=DEFINITION_NAME,parameters=DEFINITION_PARAMETERS,
        template_source=source,summary="Actual fifteen-field beta record of the positive fixed-factorial finite sample at n+8; no accuracy or analytic clause.",
        category="irrationality_approximation_computation",conceptual_dependencies=DEFINITION_DEPENDENCIES)
    if spec.template_formula!=formula or parse_formula_in_context(source,list(DEFINITION_PARAMETERS))!=formula or not set(DEFINITION_DEPENDENCIES)<=result.keys():
        raise ApproximationRecordExistsError("actual record failed conservative roundtrip or DAG check")
    result[DEFINITION_NAME]=spec
    return MappingProxyType(result)


def frozen_approximation_record_exists_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ApproximationRecordExistsError("AP028 exact finite record construction changed")
    return target


def source_contract():
    return dict(code="AP028",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precision_indices_including_zero=True,fixed_precision_shift=8,
        all_fifteen_decoded_fields_consumed=True,record_code_components=2,
        actual_positive_fixed_factorial_sample_constructed=True,no_opaque_unused_trace=True,
        beta_code_number_canonicality_claim=False,single_natural_record_packing_claim=False,
        new_definition_ids=[DEFINITION_ID],new_definition_ast_sha256=DEFINITION_AST_SHA256,
        definition_dependencies=list(DEFINITION_DEPENDENCIES),definition_admissions=0,new_induction_needed=False,
        new_fixed_tuple_prefix_steps=15,accuracy_is_definition_clause=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,
        analytic_limit_claim=False,original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def approximation_record_exists_source_pins():
    result=factorial_exp_sample_source_pins()
    expected={"scripts/sqrt2_power_factorial_exp_sample.py":"4398060a875c08aacc3e70aaf2b4737e0e302c5a5cd9748b60c164eb4bf73278",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_approximation_record_exists.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ApproximationRecordExistsError("actual record source or proof archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _small_bound(s,index,length):
    from peano_lab.kernel.terms import parse_term
    if not 0<=index<length<=14:
        raise ApproximationRecordExistsError("tuple bound outside the frozen fifteen-field range")
    left=parse_term(str(index+1));proof=specialize(s,"le_refl",left)
    for right in range(index+1,length):
        proof=apply(specialize(s,"le_succ",left,parse_term(str(right))),proof)
    return proof


def _tuple(s,length):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import parse_term,Zero
    fields=OUTPUTS[:length];last=length-1
    def extended(t):
        entries=[]
        for index,name in enumerate(fields[:-1]):
            entry=apply(instantiate(AndElimR(t.hyp("extension")),parse_term(str(index)),t.term(name)),
                _small_bound(t,index,last),field(t.hyp("previous_tuple"),index,last))
            entries.append(entry)
        entries.append(AndElimL(t.hyp("extension")))
        return witness(t.terms(("rb","rc")),conjunction(*entries))
    def previous(t):
        source=specialize(t,"beta_extend",parse_term(str(last)),*t.terms(("ob","oc")),t.term(fields[-1]))
        return eliminate(t,source,("rb","rc"),"extension",extended)
    def start(t):
        if length==1:
            source=specialize(t,"beta_extend",Zero(),Zero(),Zero(),t.term(fields[0]))
            return eliminate(t,source,("rb","rc"),"extension",extended)
        return eliminate(t,specialize(t,"tuple_"+str(last),*t.terms(fields[:-1])),("ob","oc"),"previous_tuple",previous)
    return introduce(s,fields,(),start)


def _root(s):
    from peano_lab.kernel.terms import Add,parse_term
    def coded(t):
        checks=conjunction(t.hyp("coded"),*(field(t.hyp("sample"),i,8) for i in range(4)))
        return witness(t.terms(("y","w0","rb","rc")),witness(t.terms(INTERNAL),checks))
    def sampled(t):
        return eliminate(t,specialize(t,"tuple_15",*t.terms(OUTPUTS)),("rb","rc"),"coded",coded)
    return introduce(s,("n",),(),lambda t:eliminate(t,specialize(t,"sample_exists",Add(t.term("n"),parse_term("8"))),OUTPUTS,"sample",sampled))


def factories():
    return {**{"tuple_"+str(length):lambda s,length=length:_tuple(s,length) for length in range(1,16)},"AP028":_root}


def prove_approximation_record_exists(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP028",target=frozen_approximation_record_exists_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories(),pins=approximation_record_exists_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
