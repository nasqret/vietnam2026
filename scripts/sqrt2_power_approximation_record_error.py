"""AP031: transport finite all-finer dyadic errors to the actual records.

Open both records and reuse the actual AP015 proof. Align (n+l)+8 with
(n+8)+l using ordinary addition laws, preserving the finer computation.
This is not an infinite-limit or analytic-identification theorem.
"""
from hashlib import sha256
import json

from sqrt2_power_approximation_record_exists import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,canonical,json_hash,_and,
    OUTPUTS,INTERNAL,definition_registry,
)
from sqrt2_power_exp_sample_dyadic_error import NAMED_SOURCE as ERROR_SOURCE,BOUND_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-approximation-record-error-v1"
PARAMETERS=("n","l","up","ud","rb","rc","vp","vd","sb","sc")
LEFT="NatSqrt2ApproxRecord(n,up,ud,rb,rc)"
RIGHT="NatSqrt2ApproxRecord(n+l,vp,vd,sb,sc)"
PARTS=("Pow(2,n,r)","~r=0","~ud=0","~vd=0",
    "Le(r*(ud*vp),r*(vd*up)+(ud*vd))","Le(r*(vd*up),r*(ud*vp)+(ud*vd))")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+LEFT+" -> "+RIGHT+" -> exists r. "+_and(PARTS)
TARGET_SHA256="237174f38843f6146e5511de3aa4f49bd784a08738da6ca90da7734f1b08a057"
HELPER_SOURCES={"precision":"forall n l. (n+l)+8=(n+8)+l"}
HELPER_TARGET_SHA256={"precision":"6a336e93182cd1a4c285a009c54bde788e5cb84aa74470d5f92ad2e64c2db9df"}
ERROR_ARCHIVE=dict(case="AP015",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-sample-dyadic-error-v1/generation-process.json.gz",
    bytes=116577,sha256="8e89db46de98c276dca30b4269b25a029949f740c2a72094b39a84bfdc08fe58",
    raw_bytes=2732764,raw_sha256="e8a3bad97302305c82a6bfaf1ca484dcd101b2fddf6d824ff6a322e6f0d4e68d",
    bundle_bytes=1651429,bundle_sha256="0cd67027532d8498c60bbdb9cb930631e58a7ee3b16e60982e14bbdaaf415afd",
    nodes=303,root=302,target_ast_sha256="98633f6b0d2144188f824e0f5f1f367d8113fe1999e66199a3b54eb28f615703")
ARCHIVES=(ERROR_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={"error":ERROR_SOURCE,
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)","add_comm":"forall a b. a+b=b+a"}
ENDPOINT_OWNERS=dict(error="AP015",add_assoc="CV071",add_comm="CV071")
HELPER_DEPENDENCIES={"precision":("add_assoc","add_comm"),"AP031":("error","precision")}
SOURCE_CLOSURE_PATH="research/arithmetic-library/sqrt2-power/observations/approximation-record-error-source-closure-v1.json"
SOURCE_CLOSURE_SHA256="7b6cd9e7ede273f77edf83934d4e1714e5c808ec5067f4175b4f7b2668b046d7"


class ApproximationRecordError(ValueError):
    """Changed actual records, fixed shift, power witness or dyadic bound."""


def frozen_approximation_record_error_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=10 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ApproximationRecordError("AP031 exact finite record error changed")
    return target


def source_contract():
    return dict(code="AP031",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,both_actual_records_required=True,all_precisions_and_finer_increments_including_zero=True,
        actual_power_two_to_n_constructed=True,all_three_denominators_proved_nonzero=True,
        fixed_shift_alignment_proved=True,actual_AP015_body_replayed=True,
        exact_source_closure_verified_without_recursive_repeated_reads=True,
        finite_rational_difference_bound="abs(vp/vd-up/ud)<=2^(-n)",
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,
        analytic_limit_claim=False,original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def approximation_record_error_source_pins():
    # The frozen closure was obtained from the unchanged AP028/AP015 pin
    # functions. Read and compare every actual file on EVERY invocation;
    # neither a cached result nor the manifest certifies a theorem body.
    with (ROOT/SOURCE_CLOSURE_PATH).open("rb") as stream:
        raw=stream.read(44995)
    if len(raw)!=44994 or sha256(raw).hexdigest()!=SOURCE_CLOSURE_SHA256:
        raise ApproximationRecordError("record error source closure changed")
    manifest=json.loads(raw);expected=manifest.get("source_pins",{})
    if (manifest.get("schema")!="sqrt2-power-approximation-record-error-source-closure-v1"
            or manifest.get("authority")!="source_integrity_only_not_proof_authority" or len(expected)!=270):
        raise ApproximationRecordError("record error source closure envelope changed")
    result={SOURCE_CLOSURE_PATH:dict(bytes=len(raw),sha256=SOURCE_CLOSURE_SHA256)}
    for name in (*expected,"scripts/sqrt2_power_approximation_record_error.py"):
        if name.startswith("/") or ".." in name.split("/"):
            raise ApproximationRecordError("record error source path escaped repository")
        # Some existing source pins include a historical 14 MB input artifact.
        # Hash it incrementally up to its frozen exact length, as source data;
        # this does not enlarge the 8 MiB generated-certificate limit.
        bound=expected[name]['bytes'] if name in expected else 2*1024**2
        digest=sha256();size=0
        with (ROOT/name).open("rb") as stream:
            while size<=bound:
                chunk=stream.read(min(65536,bound+1-size))
                if not chunk:
                    break
                size+=len(chunk);digest.update(chunk)
        actual=dict(bytes=size,sha256=digest.hexdigest())
        if size>bound or name in expected and actual!=expected[name]:
            raise ApproximationRecordError("record error source or actual archive changed")
        result[name]=actual
    return result


def _precision(s):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import parse_term
    eight=parse_term("8")
    return introduce(s,("n","l"),(),lambda t:_chain(
        specialize(t,"add_assoc",*t.terms(("n","l")),eight),
        CongAdd(EqRefl(t.term("n")),specialize(t,"add_comm",t.term("l"),eight)),
        EqSym(specialize(t,"add_assoc",t.term("n"),eight,t.term("l")))))


def _root(s,registry):
    left=tuple("left_"+name for name in INTERNAL);right=tuple("right_"+name for name in INTERNAL)
    def names(prefix,num,den):
        return tuple(num if name=="y" else den if name=="w0" else prefix+name for name in OUTPUTS)
    first=names("left_","up","ud");second=names("right_","vp","vd")
    finer="NatSqrt2ExpSample("+",".join(("slot",)+second)+")"
    def opened(t):
        aligned=_subst(t,registry,finer,specialize(t,"precision",*t.terms(("n","l"))),field(t.hyp("right_body"),3,5))
        theorem=specialize(t,"error",*t.terms(("n","l")+first+second))
        return apply(theorem,field(t.hyp("left_body"),2,5),field(t.hyp("right_body"),2,5),field(t.hyp("left_body"),3,5),aligned)
    return introduce(s,PARAMETERS,("left_record","right_record"),lambda t:
        eliminate(t,t.hyp("left_record"),left,"left_body",lambda u:
            eliminate(u,u.hyp("right_record"),right,"right_body",opened)))


def prove_approximation_record_error(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP031",target=frozen_approximation_record_error_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"precision":_precision,"AP031":lambda s:_root(s,registry)},pins=approximation_record_error_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
