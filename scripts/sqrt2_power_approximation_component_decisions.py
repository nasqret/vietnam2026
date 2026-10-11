"""AP025: decisions for the exact log coefficient, Horner and dyadic graphs.

Parity witnesses decide the coefficient relation even for invalid supplied
scales. Horner totality/uniqueness and the actual atomic decisions are replayed.
All code below only produces ordinary HA terms; it is not a proof oracle.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_atomic_computation_decisions import (
    ROOT,Scope,introduce,eliminate,apply,specialize,conjunction,canonical,json_hash,
    _and,decision,COMPOSITION_ARCHIVE,atomic_computation_decisions_source_pins,
    HELPER_SOURCES as ATOMIC_HELPERS,
)
from sqrt2_power_exp_sample import definition_registry as sample_registry
from sqrt2_power_atanh_coefficients import HELPER_SOURCES as ATANH_HELPERS
from sqrt2_power_atanh_euler import ATANH_ARCHIVE
from sqrt2_power_atanh_odd_slice import HELPER_SOURCES as INDEX_HELPERS,atanh_odd_slice_source_pins
from sqrt2_power_paired_horner import INDEX_ARCHIVE
from sqrt2_power_row_horner_values import HELPER_SOURCES as HORNER_HELPERS
from sqrt2_power_quadratic_trace_exists import witness
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-approximation-component-decisions-v1"
HELPER_SOURCES={
    "coefficient_dec":"forall d i a. "+decision("NatAtanhCoefficient(d,i,a)"),
    "horner_dec":"forall ab ac t N v. "+decision("NatHornerValue(ab,ac,t,N,v)"),
    "dyadic_dec":"forall k d s. "+decision("DyadicSqrt2(k,d,s)"),
}
NAMED_SOURCE=_and(tuple("("+source+")" for source in HELPER_SOURCES.values()))
TARGET_SHA256="73143d6dbbcad9e7c4558786a63cf9abc8870be8c71abd9d934090ddb9501c21"
HELPER_TARGET_SHA256={
    "coefficient_dec":"9cb1dcff645df02fea3e49348382bbc367dbffebd481d73ebbc263747438768c",
    "horner_dec":"214f547252218c0931dc6b4b733d4516b82a473c5250444b9d698c6be132c5b0",
    "dyadic_dec":"ca1d5425990bad8d1ec7ba7763a782a3520b85b095dcaad706a48215e13d58ba",
}
DECISION_ARCHIVE=dict(case="AP024",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-atomic-computation-decisions-v1/generation-process.json.gz",
    bytes=36596,sha256="4196d5acc017090eca340c71f33de0dcd7bdb4fd86c233a0af0d04e76a797162",
    raw_bytes=564120,raw_sha256="0cf912bbc9ed79a110fe7c32016ce03cdb0e45c5ccc2de5b0b05c376de205d7b",
    bundle_bytes=310665,bundle_sha256="e2e83ec51ce4d3cfc724c3e68e01de0d41efde85b51707031d85ee9d7b537c8c",
    nodes=153,root=152,target_ast_sha256="ed18ed2d5be19d785c821571ea8789461ac6dcc996c0e26364d9149e77d9d6f0")
ARCHIVES=(DECISION_ARCHIVE,COMPOSITION_ARCHIVE,INDEX_ARCHIVE,ATANH_ARCHIVE)
ENDPOINT_SOURCES={**{name:ATOMIC_HELPERS[name] for name in ("eq_dec","power_dec","floor_dec")},
    "parity":ATANH_HELPERS["parity"],
    **{name:INDEX_HELPERS[name] for name in ("even_coefficient","odd_coefficient")},
    "value_exists":HORNER_HELPERS["value_exists"],"value_unique":HORNER_HELPERS["value_unique"]}
ENDPOINT_OWNERS=dict(eq_dec="AP024",power_dec="AP024",floor_dec="AP024",parity="CV025",
    even_coefficient="AP016",odd_coefficient="AP016",value_exists="CV061",value_unique="CV061")
HELPER_DEPENDENCIES={
    "coefficient_dec":("parity","eq_dec","even_coefficient","odd_coefficient"),
    "horner_dec":("eq_dec","value_exists","value_unique"),
    "dyadic_dec":("power_dec","floor_dec"),
    "AP025":tuple(HELPER_SOURCES),
}


class ApproximationComponentDecisionsError(ValueError):
    """Changed exact component, constructive decision or source bytes."""


def definition_registry():
    source=sample_registry();needed=set();pending=["NatAtanhCoefficient","NatHornerValue","DyadicSqrt2"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ApproximationComponentDecisionsError("component decision definition DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_approximation_component_decisions_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    if type(target) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ApproximationComponentDecisionsError("AP025 exact component decisions changed")
    return target


def source_contract():
    return dict(code="AP025",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,constructive_decisions=["NatAtanhCoefficient","NatHornerValue","DyadicSqrt2"],
        arbitrary_natural_inputs_including_invalid_scales=True,zero_input_allowed=True,
        actual_parity_and_Horner_totality_uniqueness_replayed=True,
        deterministic_HA_term_generation=True,classical_axioms_used=False,markov_principle_used=False,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        complete_CApprox_verifier_claim=False,canonical_PR_approximation_algorithm_claim=False,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def approximation_component_decisions_source_pins():
    result=atomic_computation_decisions_source_pins()
    for name,pin in atanh_odd_slice_source_pins().items():
        if name in result and result[name]!=pin:
            raise ApproximationComponentDecisionsError("component decision source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_atomic_computation_decisions.py":"f9617252448271b4d486de11aa98c2b379e96efb0b1870dd6098d20afb3173f4",
        "scripts/sqrt2_power_atanh_odd_slice.py":"91fcf50ee5a35c19605a11497e6d7aca2970257cb468f383997b1a62d3208210",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_approximation_component_decisions.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ApproximationComponentDecisionsError("component decision source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def conjunction_decision(s,producers,label):
    """Untrusted deterministic schema for decisions of right-associated /\\."""
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,OrElim,OrIntroL,OrIntroR
    if not producers:
        raise ApproximationComponentDecisionsError("empty conjunction decision")
    if len(producers)==1:
        return producers[0](s)
    left_yes=label+"_left_yes";left_no=label+"_left_no"
    right_yes=label+"_right_yes";right_no=label+"_right_no";whole=label+"_whole"
    def positive(t):
        def yes(u):
            return OrIntroL(AndIntro(u.hyp(left_yes),u.hyp(right_yes)))
        def no(u):
            return OrIntroR(introduce(u,(),(whole,),lambda v:apply(v.hyp(right_no),AndElimR(v.hyp(whole)))))
        return OrElim(conjunction_decision(t,producers[1:],label+"_tail"),yes(t.hypothesis(right_yes)),no(t.hypothesis(right_no)))
    negative=OrIntroR(introduce(s.hypothesis(left_no),(),(whole,),lambda t:apply(t.hyp(left_no),AndElimL(t.hyp(whole)))))
    return OrElim(producers[0](s),positive(s.hypothesis(left_yes)),negative)


def _coefficient_dec(s,registry):
    from peano_lab.kernel.proofs import AndIntro,EqSym,OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Mul,Succ,Zero,parse_term
    two=parse_term("2")
    def branch(t,odd):
        def decoded(u):
            def yes(v):
                body=witness((v.term("j"),),AndIntro(v.hyp("index"),v.hyp("equal")))
                return OrIntroL(OrIntroR(body) if odd else OrIntroL(body))
            def no(v):
                def contradiction(w):
                    coefficient=_subst(w,registry,"NatAtanhCoefficient(d,slot,a)",w.hyp("index"),w.hyp("candidate"))
                    equation=apply(specialize(w,"odd_coefficient" if odd else "even_coefficient",*w.terms(("d","j","a"))),coefficient)
                    if odd:
                        equation=_subst(w,registry,"slot*a=2*d",EqSym(w.hyp("index")),equation)
                    return apply(w.hyp("different"),equation)
                return OrIntroR(introduce(v,(),("candidate",),contradiction))
            left=Mul(u.term("i"),u.term("a")) if odd else u.term("a")
            right=Mul(two,u.term("d")) if odd else Zero()
            return OrElim(specialize(u,"eq_dec",left,right),yes(u.hypothesis("equal")),no(u.hypothesis("different")))
        return eliminate(t,t.hyp("parity_case"),("j",),"index",decoded)
    return introduce(s,("d","i","a"),(),lambda t:OrElim(specialize(t,"parity",t.term("i")),
        branch(t.hypothesis("parity_case"),False),branch(t.hypothesis("parity_case"),True)))


def _horner_dec(s,registry):
    from peano_lab.kernel.proofs import OrElim,OrIntroL,OrIntroR
    inputs=("ab","ac","t","N")
    def computed(t):
        yes=lambda u:OrIntroL(_subst(u,registry,"NatHornerValue(ab,ac,t,N,slot)",u.hyp("equal"),u.hyp("computed")))
        no=lambda u:OrIntroR(introduce(u,(),("candidate",),lambda v:
            apply(v.hyp("different"),apply(specialize(v,"value_unique",*v.terms(inputs+("z","v"))),v.hyp("computed"),v.hyp("candidate")))))
        return OrElim(specialize(t,"eq_dec",*t.terms(("z","v"))),yes(t.hypothesis("equal")),no(t.hypothesis("different")))
    return introduce(s,inputs+("v",),(),lambda t:eliminate(t,specialize(t,"value_exists",*t.terms(inputs)),("z",),"computed",computed))


def _dyadic_dec(s):
    from peano_lab.kernel.terms import Mul,parse_term
    two=parse_term("2")
    return introduce(s,("k","d","s"),(),lambda t:conjunction_decision(t,(
        lambda u:specialize(u,"power_dec",two,*u.terms(("k","d"))),
        lambda u:specialize(u,"floor_dec",Mul(two,Mul(u.term("d"),u.term("d"))),u.term("s"))),"dyadic"))


def factories(registry):
    return dict(coefficient_dec=lambda s:_coefficient_dec(s,registry),horner_dec=lambda s:_horner_dec(s,registry),
        dyadic_dec=_dyadic_dec,AP025=lambda s:conjunction(*(s.hyp(name) for name in HELPER_SOURCES)))


def prove_approximation_component_decisions(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP025",target=frozen_approximation_component_decisions_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories(registry),pins=approximation_component_decisions_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
