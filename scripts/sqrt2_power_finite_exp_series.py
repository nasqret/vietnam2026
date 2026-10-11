"""AP021: actual exponential sample terms have their factorial-series values.

Construct every factorial and numerator/denominator power and prove each
normalized term is U^j/(j!*V^j). Keep the caller's actual term table and sum.
No canonical PR trace, real exponential identity or limit is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_supplied_exp_sample import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,supplied_exp_sample_source_pins,definition_registry as sample_registry,
    NAMED_SOURCE as SUPPLIED_SOURCE,PARAMETERS,GRAPH,HELPER_SOURCES as SUPPLIED_HELPERS,
    ENDPOINT_SOURCES as SUPPLIED_ENDPOINTS,
)
from sqrt2_power_exp_sample import NUMERATOR,DENOMINATOR,DEGREE,_and
from sqrt2_power_exp_sample_independence import SUPPLIED_ARCHIVE
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE
from sqrt2_power_odd_horner_quotient import odd_horner_quotient_source_pins,HELPER_SOURCES as RATIONAL_HELPERS,_chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-finite-exp-series-v1"
NORMALIZATION="forall j t f0 p0 q0. Le(j,N) -> BetaAt(tb,tc,j,t) -> Factorial(j,f0) -> Pow(V,j,p0) -> Pow(U,j,q0) -> (t*f0)*p0=w0*q0"


def term_formula(numerator,denominator,degree):
    parts=("Factorial(j,f0)",f"Pow({denominator},j,p0)",f"Pow({numerator},j,q0)","~f0=0","~p0=0","IRatEq(t,0,w0,q0,0,f0*p0)")
    return f"forall j t. Le(j,{degree}) -> BetaAt(tb,tc,j,t) -> exists f0 p0 q0. "+_and(parts)


PARTS=("~w0=0",f"~{DENOMINATOR}=0",f"Sum(tb,tc,S {DEGREE},y)","("+term_formula(NUMERATOR,DENOMINATOR,DEGREE)+")")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~D=0 -> "+GRAPH+" -> "+_and(PARTS)
TARGET_SHA256="8c30669eb1c317280a38fcade33d35967d3427cb940f0753752a02da1460daee"
HELPER_SOURCES={
    "normalize":"forall t f p w q. ~w=0 -> ~f=0 -> ~p=0 -> (t*f)*p=w*q -> IRatEq(t,0,w,q,0,f*p)",
    "terms":"forall U V w0 tb tc N. ~w0=0 -> ~V=0 -> ("+NORMALIZATION+") -> "+term_formula("U","V","N"),
}
HELPER_TARGET_SHA256={"normalize":"98c67883a7a4c2de1428576c519ceb28851fecfdb2b579aa2065e0900d940cc4",
    "terms":"040b0884ff9ec1478044355ac388b43f34e2287ae07e0c499ab611d8e7b3cb2f"}
RATIONAL_ARCHIVE=dict(case="AP019",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-odd-horner-quotient-v1/generation-process.json.gz",
    bytes=50800,sha256="5c5ab53c4af4d88d2a8bd01bdc1c216e87203e7bb36552e3455a48191c44411b",
    raw_bytes=583628,raw_sha256="f876287912310c6d75ff45d31cac17165a15a23d3ef7ea5064b130d01efcfc31",
    bundle_bytes=310851,bundle_sha256="fd6d43b7cb41ce4722c57ebffffdde004e26d8fd5a289ffd74679af508db224a",
    nodes=142,root=141,target_ast_sha256="ef40bb286d66b9b7abd7a8521c7ef114b6ccba8d8780e5d0574178f985096c33")
ARCHIVES=(SUPPLIED_ARCHIVE,EXP_ARCHIVE,RATIONAL_ARCHIVE)
ENDPOINT_SOURCES={name:SUPPLIED_ENDPOINTS[name] for name in ("power_nonzero","mul_ne_zero")}
ENDPOINT_SOURCES.update(supplied=SUPPLIED_SOURCE,factorial_nonzero=SUPPLIED_HELPERS["factorial_nonzero"],
    positive_eq=RATIONAL_HELPERS["positive_eq"],factorial_exists="forall n. exists f. Factorial(n,f)",
    power_exists="forall a k. exists p. Pow(a,k,p)",
    mul_assoc="forall a b c. (a*b)*c=a*(b*c)",mul_comm="forall a b. a*b=b*a")
ENDPOINT_OWNERS={name:"AP004" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(factorial_exists="CV070",power_exists="CV070",positive_eq="AP019",mul_assoc="AP019",mul_comm="AP019")
HELPER_DEPENDENCIES={"normalize":("positive_eq","mul_ne_zero","mul_assoc","mul_comm"),
    "terms":("normalize","factorial_exists","factorial_nonzero","power_exists","power_nonzero"),
    "AP021":("supplied","terms")}


class FiniteExpSeriesError(ValueError):
    """Changed factorial-series interpretation or actual sample graph."""


def definition_registry():
    from sqrt2_power_definitions import DEFINITIONS
    result=dict(sample_registry());ids={spec.stable_id for spec in result.values()}
    for name in ("IRatValid","IRatEq"):
        spec=DEFINITIONS[name]
        if name in result or spec.stable_id in ids or not set(spec.conceptual_dependencies)<=result.keys():
            raise FiniteExpSeriesError("finite exponential rational DAG collision or forward edge")
        result[name]=spec;ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_finite_exp_series_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=16 or len(premises)!=2 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FiniteExpSeriesError("AP021 exact finite factorial-series target changed")
    return target


def source_contract():
    return dict(code="AP021",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,actual_supplied_sample_term_table_head_and_sum_preserved=True,
        all_in_range_terms_identified_with_factorial_series=True,each_factorial_and_both_powers_constructed=True,
        output_and_each_term_denominator_proved_nonzero=True,zero_argument_and_zero_term_index_allowed=True,
        finite_series_reading="y/w0=sum(j<=k+2,U^j/(j!*V^j))",numerator=NUMERATOR,denominator=DENOMINATOR,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_exponential_identity_claim=False,
        analytic_limit_claim=False,original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def finite_exp_series_source_pins():
    result=supplied_exp_sample_source_pins()
    for name,pin in odd_horner_quotient_source_pins().items():
        if name in result and result[name]!=pin:
            raise FiniteExpSeriesError("finite exponential source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_supplied_exp_sample.py":"30423d296b32b21ea9d3c35802cb81dbe5dae1fb4a589f8a8abce112e93be11a",
        "scripts/sqrt2_power_exp_sample.py":"7062977d78a2ee1445e396d8e970460d1d366a36e8dc211c28e8c64b905adb46",
        "scripts/sqrt2_power_exp_sample_independence.py":"e6ec0523040135408adbadfc5cf46351f4682bd6a3b1f564c08263f8cb692187",
        "scripts/sqrt2_power_scaled_exp_bound.py":"717128c4845645cca66209b12512d4de2905d6ecc4eebad8c04c197647f9ee0c",
        "scripts/sqrt2_power_odd_horner_quotient.py":"2f646e44d68612e31791b15cc24e59c6c9d7ec47059e686a81a1a3fc963e7d0e",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_finite_exp_series.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FiniteExpSeriesError("finite exponential source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _normalize(s):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Mul
    def finish(u):
        t,f,p,w,q=u.terms(("t","f","p","w","q"))
        cross=_chain(EqSym(specialize(u,"mul_assoc",t,f,p)),u.hyp("normalization"),specialize(u,"mul_comm",w,q))
        nonzero=apply(specialize(u,"mul_ne_zero",f,p),u.hyp("factorial_nonzero"),u.hyp("power_nonzero_value"))
        return apply(specialize(u,"positive_eq",t,q,w,Mul(f,p)),u.hyp("head_nonzero"),nonzero,cross)
    return introduce(s,("t","f","p","w","q"),("head_nonzero","factorial_nonzero","power_nonzero_value","normalization"),finish)


def _terms(s):
    from sqrt2_power_native import instantiate
    def chosen(u):
        j,t,f,p,q=u.terms(("j","t","f0","p0","q0"))
        fnz=apply(specialize(u,"factorial_nonzero",j,f),u.hyp("factorial"))
        pnz=apply(instantiate(apply(specialize(u,"power_nonzero",u.term("V")),u.hyp("denominator_nonzero")),j,p),u.hyp("denominator_power"))
        normalized=apply(instantiate(u.hyp("normalization"),j,t,f,p,q),u.hyp("in_range"),u.hyp("entry"),u.hyp("factorial"),u.hyp("denominator_power"),u.hyp("numerator_power"))
        equal=apply(specialize(u,"normalize",t,f,p,u.term("w0"),q),u.hyp("head_nonzero"),fnz,pnz,normalized)
        return witness((f,p,q),conjunction(u.hyp("factorial"),u.hyp("denominator_power"),u.hyp("numerator_power"),fnz,pnz,equal))
    def entry(t):
        return eliminate(t,specialize(t,"factorial_exists",t.term("j")),("f0",),"factorial",lambda u:
            eliminate(u,specialize(u,"power_exists",*u.terms(("V","j"))),("p0",),"denominator_power",lambda v:
                eliminate(v,specialize(v,"power_exists",*v.terms(("U","j"))),("q0",),"numerator_power",chosen)))
    return introduce(s,("U","V","w0","tb","tc","N"),("head_nonzero","denominator_nonzero","normalization"),lambda u:
        introduce(u,("j","t"),("in_range","entry"),entry))


def _root(s):
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,three=(parse_term(source) for source in ("2","3"))
    def finish(t):
        d,D,p,root,x,k=t.terms(("d","D","p","s","x","k"));U=Mul(Mul(three,x),d);V=Mul(Mul(D,p),root);N=Add(k,two)
        laws=apply(specialize(t,"supplied",*t.terms(PARAMETERS)),t.hyp("scale_nonzero"),t.hyp("sample"))
        terms=apply(specialize(t,"terms",U,V,*t.terms(("w0","tb","tc")),N),field(laws,0,5),field(laws,1,5),field(laws,4,5))
        return conjunction(field(laws,0,5),field(laws,1,5),field(t.hyp("sample"),8,9),terms)
    return introduce(s,PARAMETERS,("scale_nonzero","sample"),finish)


def prove_finite_exp_series(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP021",target=frozen_finite_exp_series_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"normalize":_normalize,"terms":_terms,"AP021":_root},
        pins=finite_exp_series_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
