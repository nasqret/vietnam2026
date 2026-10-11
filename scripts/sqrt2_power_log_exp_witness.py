"""AP032: actual finite logarithm/exponential computations approach two.

Reuse CV085's checked construction/evaluation stages, not its redundant
root, and connect their very product table to CV073's exponential recurrence.
The denominator, head, argument bound and both finite errors are conclusions.
This is the finite bridge toward exp(log(2))=2, not a limit assertion.
"""
from hashlib import sha256
import json

from sqrt2_power_constructed_composition_error import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,conjoin,
    HELPER_SOURCES as COMPOSITION_HELPERS,COMPUTATION_OUTPUTS,EVALUATION_PARAMETERS,VALUE_OUTPUTS,
    constructed_composition_error_source_pins,
)
from sqrt2_power_weighted_monomial_recurrence import NAMED_SOURCE as RECURRENCE_SOURCE,weighted_monomial_recurrence_source_pins
from sqrt2_power_ternary_atanh_bound import NAMED_SOURCE as ARGUMENT_SOURCE,ternary_atanh_bound_source_pins
from sqrt2_power_composition_majorant import WEIGHTED_ARCHIVE,BOUND_ARCHIVE
from sqrt2_power_ternary_prefix_bound import TERNARY_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-log-exp-witness-v1"
N="S(S K)"
OUTPUTS=("d","ab","ac","x","p","tb","tc","h","y","r","a")
PARTS=("~d=0",f"NatAtanhPrefix(d,ab,ac,{N})",f"NatHornerValue(ab,ac,3,{N},x)",
    f"Pow(3,{N},p)","Pow(3,S K,r)",f"Pow(2,{N},a)","~p=0","~r=0","~h=0","~(d*p)=0",
    "Le(3*x,d*p)",f"NatScaledExpRecurrence(d*p,3*x,tb,tc,{N})","BetaAt(tb,tc,0,h)",
    f"Sum(tb,tc,S({N}),y)","IRatLe(y,0,h,2*p+9*a,0,p)","IRatLe(2,0,1,y*r+h,0,h*r)")
NAMED_SOURCE="forall K. exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256="f184312da8aa97085684bf27c6b090fe30ff3df7d6afcd251bbc4309ddb1c715"
HELPER_SOURCES={"argument":"forall d p x. Le(3*x+3*d,d*p) -> Le(3*x,d*p)"}
HELPER_TARGET_SHA256={"argument":"92142f720c282308885514329c29ca6bbb72cb5db2bea7bde1b8314bdca422b6"}
COMPOSITION_ARCHIVE=dict(case="CV085",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-constructed-composition-error-v3/generation-process.json.gz",
    bytes=164608,sha256="ab70934fe3c50e6066221def46792f7e562a8c36f73f6ccfeccbb870895254eb",
    raw_bytes=4445230,raw_sha256="2478e36cc37c7a009816086b73be5922ffb203f7e9ac31655139dda3e3ae3e5c",
    bundle_bytes=2727157,bundle_sha256="c2e9f924a90d6c5c2580db4e5dc7d18a89a02f6936f3c0dff0ebc0d566b2d833",
    nodes=435,root=434,target_ast_sha256="390079559204a44746d65722e27b386315e6b9830542df520c3ed5acd50b4d58")
ARCHIVES=(COMPOSITION_ARCHIVE,WEIGHTED_ARCHIVE,TERNARY_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={"computation":COMPOSITION_HELPERS['computation'],"evaluation":COMPOSITION_HELPERS['evaluation'],
    "recurrence":RECURRENCE_SOURCE,"inner_bound":ARGUMENT_SOURCE,
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0",
    "add_comm":"forall a b. a+b=b+a","le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)"}
ENDPOINT_OWNERS=dict(computation="CV085",evaluation="CV085",recurrence="CV073",inner_bound="CV086",
    mul_ne_zero="CV071",add_comm="CV071",le_trans="CV071")
HELPER_DEPENDENCIES={"argument":("add_comm","le_trans"),
    "AP032":("computation","evaluation","recurrence","inner_bound","mul_ne_zero","argument")}
SOURCE_CLOSURE_PATH="research/arithmetic-library/sqrt2-power/observations/log-exp-witness-source-closure-v1.json"
SOURCE_CLOSURE_SHA256="38d2a182c9ba92427c42116af9100d0f11103b489d23268c4a2c16e4f61051dd"
SOURCE_CLOSURE_BYTES=35849
SOURCE_CLOSURE_COUNT=215


class LogExpWitnessError(ValueError):
    """Changed actual computation, finite error, source or positive scale."""


def frozen_log_exp_witness_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LogExpWitnessError("AP032 exact finite log/exp witness changed")
    return target


def source_contract():
    return dict(code="AP032",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_K_including_zero=True,inner_length="K+2",outer_degree="K+2",
        actual_coefficient_Horner_power_and_exp_term_tables_constructed=True,
        same_product_table_used_for_recurrence_and_errors=True,
        argument_numerator="3*x",argument_denominator="d*p",output_value="y/h",
        finite_upper="y/h <= 2+9*(2/3)^(K+2)",finite_lower="2 <= y/h+3^(-(K+1))",
        all_rational_denominators_proved_nonzero=True,argument_upper_one_proved=True,
        actual_CV085_stage_bodies_replayed=True,redundant_CV085_root_replayed=False,
        actual_CV073_recurrence_replayed=True,new_induction_needed=False,
        new_definition_ids=[],definition_admissions=0,analytic_logarithm_identity=False,
        analytic_limit_claim=False,original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def recursive_source_pins_for_audit():
    """Only capture the exact closure; proof workers use its streaming check."""
    result={}
    for source in (constructed_composition_error_source_pins,weighted_monomial_recurrence_source_pins,ternary_atanh_bound_source_pins):
        for name,pin in source().items():
            if name in result and result[name]!=pin:
                raise LogExpWitnessError("log/exp source disagreement")
            result[name]=pin
    for pin in ARCHIVES:
        raw=(ROOT/pin['path']).read_bytes()
        if len(raw)!=pin['bytes'] or sha256(raw).hexdigest()!=pin['sha256']:
            raise LogExpWitnessError("log/exp archive changed")
        result[pin['path']]=dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
    return result


def log_exp_witness_source_pins():
    with (ROOT/SOURCE_CLOSURE_PATH).open("rb") as stream:
        raw=stream.read(SOURCE_CLOSURE_BYTES+1)
    if len(raw)!=SOURCE_CLOSURE_BYTES or sha256(raw).hexdigest()!=SOURCE_CLOSURE_SHA256:
        raise LogExpWitnessError("log/exp source closure changed")
    manifest=json.loads(raw);expected=manifest.get('source_pins',{})
    if (manifest.get('schema')!='sqrt2-power-log-exp-witness-source-closure-v1'
            or manifest.get('authority')!='source_integrity_only_not_proof_authority' or len(expected)!=SOURCE_CLOSURE_COUNT):
        raise LogExpWitnessError("log/exp source closure envelope changed")
    result={SOURCE_CLOSURE_PATH:dict(bytes=len(raw),sha256=SOURCE_CLOSURE_SHA256)}
    for name in (*expected,"scripts/sqrt2_power_log_exp_witness.py"):
        if name.startswith('/') or '..' in name.split('/'):
            raise LogExpWitnessError("log/exp source path escaped repository")
        bound=expected[name]['bytes'] if name in expected else 2*1024**2
        digest=sha256();size=0
        with (ROOT/name).open('rb') as stream:
            while size<=bound:
                chunk=stream.read(min(65536,bound+1-size))
                if not chunk:
                    break
                size+=len(chunk);digest.update(chunk)
        actual=dict(bytes=size,sha256=digest.hexdigest())
        if size>bound or name in expected and actual!=expected[name]:
            raise LogExpWitnessError("log/exp source bytes changed")
        result[name]=actual
    return result


def _argument(s):
    from peano_lab.kernel.terms import Add,Mul,parse_term
    three=parse_term('3')
    def finish(t):
        d,p,x=t.terms(('d','p','x'));low=Mul(three,x);gap=Mul(three,d)
        first=witness((gap,),specialize(t,'add_comm',gap,low))
        return apply(specialize(t,'le_trans',low,Add(low,gap),Mul(d,p)),first,t.hyp('bound'))
    return introduce(s,('d','p','x'),('bound',),finish)


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    three=parse_term('3')
    def finished(t):
        K,d,ep,ex,ev,z=t.terms(('K','d','ep','ex','ev','z'));N=Succ(Succ(K))
        comp=t.hyp('constructed');bounds=t.hyp('bounds')
        recurrence=apply(specialize(t,'recurrence',d,ep,three,ex,ev,N,
            *t.terms(('wb','wc','evb','evc','ezb','ezc','z'))),
            field(bounds,8,15),field(bounds,5,15),field(comp,2,14),field(bounds,3,15),field(comp,3,14))
        dnz=apply(specialize(t,'mul_ne_zero',d,ep),field(comp,0,14),field(bounds,8,15))
        inner=apply(specialize(t,'inner_bound',*t.terms(('d','ab','ac')),Succ(K),ex,ep),
            field(comp,1,14),field(bounds,0,15),field(bounds,1,15))
        argument=apply(specialize(t,'argument',d,ep,ex),inner)
        out=t.terms(('d','ab','ac','ex','ep','ezb','ezc'))+(Mul(z,ev),)+t.terms(('es','p3','a2'))
        return witness(out,conjunction(field(comp,0,14),field(comp,1,14),field(bounds,0,15),field(bounds,1,15),
            field(bounds,6,15),field(bounds,7,15),field(bounds,8,15),field(bounds,10,15),field(bounds,11,15),
            dnz,argument,AndElimR(recurrence),AndElimL(recurrence),field(bounds,4,15),field(bounds,13,15),field(bounds,14,15)))
    def constructed(t):
        data=t.hyp('constructed')
        value=apply(specialize(t,'evaluation',Succ(t.term('K')),*t.terms(EVALUATION_PARAMETERS[1:])),
            *(field(data,i,14) for i in (4,9,10,11,12,13)))
        return eliminate(t,value,VALUE_OUTPUTS,'bounds',finished)
    return introduce(s,('K',),(),lambda t:
        eliminate(t,specialize(t,'computation',t.term('K')),COMPUTATION_OUTPUTS,'constructed',constructed))


def prove_log_exp_witness(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP032",target=frozen_log_exp_witness_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'argument':_argument,'AP032':_root},pins=log_exp_witness_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
