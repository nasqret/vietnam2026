"""AP024: constructive decisions for the approximation's basic computations.

Deterministically instantiate totality + value uniqueness + natural equality
decision. Every dependency body is replayed in HA; no excluded-middle axiom,
solver verdict, unbounded search program or complete CApprox verifier is used.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_sample import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,conjunction,
    canonical,json_hash,_and,definition_registry as sample_registry,exp_sample_source_pins,
)
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE
from sqrt2_power_floor_sqrt_comparison import FLOOR_ARCHIVE,floor_sqrt_comparison_source_pins
from sqrt2_power_floor_sqrt import NAMED_SOURCE as FLOOR_SOURCE
from sqrt2_power_weight_factorials import ENDPOINT_SOURCES as FACTORIAL_ENDPOINTS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-atomic-computation-decisions-v1"
FUNCTIONS={
    "beta":(("b","c","i"),"BetaAt"),
    "power":(("a","n"),"Pow"),
    "factorial":(("n",),"Factorial"),
    "sum":(("b","c","n"),"Sum"),
}


def relation(name,inputs,output):
    return name+"("+",".join(inputs+(output,))+")"


def decision(source):
    return "("+source+") \\/ ~("+source+")"


HELPER_SOURCES={
    "lt_ne":"forall a b. Lt(a,b) -> ~a=b",
    "eq_dec":"forall a b. "+decision("a=b"),
    "le_dec":"forall a b. "+decision("Le(a,b)"),
    "lt_dec":"forall a b. "+decision("Lt(a,b)"),
    "factorial_unique":"forall n f g. Factorial(n,f) -> Factorial(n,g) -> f=g",
    **{name+"_dec":"forall "+" ".join(inputs+("v",))+". "+decision(relation(rel,inputs,"v"))
       for name,(inputs,rel) in FUNCTIONS.items()},
    "floor_dec":"forall n v. "+decision("FloorSqrt(n,v)"),
}
DECISIONS=("eq_dec","le_dec","lt_dec","beta_dec","power_dec","factorial_dec","sum_dec","floor_dec")
NAMED_SOURCE=_and(tuple("("+HELPER_SOURCES[name]+")" for name in DECISIONS))
TARGET_SHA256="ed18ed2d5be19d785c821571ea8789461ac6dcc996c0e26364d9149e77d9d6f0"
HELPER_TARGET_SHA256={
    "lt_ne":"08145adb431b040edc39fa93e68702231518581d53569eb12c89037d9f62e269",
    "eq_dec":"b7a8a82fefe4ce0ee870fc55aa72286c0c27ec0086c46368d700a531364e5003",
    "le_dec":"b225a4c63c279baad411781d3f3b5db638998b19a69aa430b86839c4e3b3ab84",
    "lt_dec":"b2ee499a29360145e588cd2d70bee4f512ceeaa49aef5f464d1df0ae03ea1883",
    "factorial_unique":"9d14b49593aa7a3347256973b09711a8116f41d1574d2e63b387513861afc684",
    "beta_dec":"737b90007428bda733b7abf5cdc473475dc7d747c41788f8aa56ae9aac70e3df",
    "power_dec":"18eadec43b37446d83c77fa48c12f1281509bcf514f68ed8289b852534e4908b",
    "factorial_dec":"d463b97ab80e4afb0ff71d2097ff2d4cd241be87b29d515933a359a7f874340f",
    "sum_dec":"0ce96035bc4053cafaf7084e4f7c3241a64f7f0bce211b1b1b9bd81d699e3cfb",
    "floor_dec":"df69941c8da1aa88071773bd9aea8d7123ad9fb620849bd17ae019772085260b",
}
ARCHIVES=(COMPOSITION_ARCHIVE,EXP_ARCHIVE,FLOOR_ARCHIVE)
ENDPOINT_SOURCES={
    "le_refl":"forall a. Le(a,a)",
    "le_or_lt":"forall a b. Le(a,b) \\/ Lt(b,a)",
    "le_eq_or_lt":"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    **{name+"_exists":"forall "+" ".join(inputs)+". exists z. "+relation(rel,inputs,"z")
       for name,(inputs,rel) in FUNCTIONS.items()},
    **{name+"_unique":"forall "+" ".join(inputs+("v","z"))+". "+relation(rel,inputs,"v")+" -> "+relation(rel,inputs,"z")+" -> v=z"
       for name,(inputs,rel) in FUNCTIONS.items() if name!="factorial"},
    "factorial_zero":FACTORIAL_ENDPOINTS["factorial_zero"],
    "factorial_step":FACTORIAL_ENDPOINTS["factorial_step"],
    "floor_total_unique":FLOOR_SOURCE,
}
ENDPOINT_OWNERS={name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(factorial_exists="CV070",factorial_zero="CV070",factorial_step="CV070",floor_total_unique="SQ001")
HELPER_DEPENDENCIES={
    "lt_ne":("le_refl","lt_not_le"),
    "eq_dec":("le_or_lt","le_eq_or_lt","lt_ne"),
    "le_dec":("le_or_lt","lt_not_le"),
    "lt_dec":("le_or_lt","lt_not_le"),
    "factorial_unique":("factorial_zero","factorial_step"),
    **{name+"_dec":("eq_dec",name+"_exists",name+"_unique") for name in FUNCTIONS},
    "floor_dec":("eq_dec","floor_total_unique"),
    "AP024":DECISIONS,
}


class AtomicComputationDecisionsError(ValueError):
    """Changed constructive decision, totality dependency or definition."""


def definition_registry():
    source=sample_registry();needed=set();pending=["Le","Lt","BetaAt","Pow","Factorial","Sum","FloorSqrt"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise AtomicComputationDecisionsError("atomic computation definition DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_atomic_computation_decisions_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    if type(target) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise AtomicComputationDecisionsError("AP024 exact constructive decision target changed")
    return target


def source_contract():
    return dict(code="AP024",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,constructive_decisions=["equality","Le","Lt","BetaAt","Pow","Factorial","Sum","FloorSqrt"],
        arbitrary_natural_inputs_including_zero=True,totality_and_value_uniqueness_replayed=True,
        deterministic_proof_schema_not_oracle=True,factorial_uniqueness_by_induction=True,
        classical_axioms_used=False,markov_principle_used=False,unbounded_search_algorithm_claim=False,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=True,
        complete_CApprox_verifier_claim=False,canonical_PR_approximation_algorithm_claim=False,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def atomic_computation_decisions_source_pins():
    result=exp_sample_source_pins()
    for name,pin in floor_sqrt_comparison_source_pins().items():
        if name in result and result[name]!=pin:
            raise AtomicComputationDecisionsError("atomic decision source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_sample.py":"7062977d78a2ee1445e396d8e970460d1d366a36e8dc211c28e8c64b905adb46",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        "scripts/sqrt2_power_convolution_unit.py":"d058762fb3641d5bb1e90c764c4581801feeaf0a103901811b3e82dbe3db8f16",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_atomic_computation_decisions.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise AtomicComputationDecisionsError("atomic decision source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _lt_ne(s,registry):
    return introduce(s,("a","b"),("strict","equal"),lambda t:
        apply(specialize(t,"lt_not_le",*t.terms(("a","b"))),t.hyp("strict"),
            _subst(t,registry,"Le(slot,a)",t.hyp("equal"),specialize(t,"le_refl",t.term("a")))))


def _eq_dec(s):
    from peano_lab.kernel.proofs import OrElim,OrIntroL,OrIntroR,EqSym
    def finish(t):
        def nonstrict(u):
            def strict(v):
                return OrIntroR(apply(specialize(v,"lt_ne",*v.terms(("a","b"))),v.hyp("strict")))
            return OrElim(apply(specialize(u,"le_eq_or_lt",*u.terms(("a","b"))),u.hyp("ordered")),
                OrIntroL(u.hypothesis("equal").hyp("equal")),strict(u.hypothesis("strict")))
        def reverse(u):
            return OrIntroR(introduce(u,(),("equal",),lambda v:
                apply(specialize(v,"lt_ne",*v.terms(("b","a"))),v.hyp("reverse"),EqSym(v.hyp("equal")))))
        return OrElim(specialize(t,"le_or_lt",*t.terms(("a","b"))),
            nonstrict(t.hypothesis("ordered")),reverse(t.hypothesis("reverse")))
    return introduce(s,("a","b"),(),finish)


def _order_dec(s,strict):
    from peano_lab.kernel.proofs import OrElim,OrIntroL,OrIntroR
    def finish(t):
        if strict:
            left=OrIntroR(introduce(t.hypothesis("reverse"),(),("strict",),lambda u:
                apply(specialize(u,"lt_not_le",*u.terms(("a","b"))),u.hyp("strict"),u.hyp("reverse"))))
            right=OrIntroL(t.hypothesis("ordered").hyp("ordered"))
            names=("b","a")
        else:
            left=OrIntroL(t.hypothesis("ordered").hyp("ordered"))
            right=OrIntroR(introduce(t.hypothesis("reverse"),(),("ordered",),lambda u:
                apply(specialize(u,"lt_not_le",*u.terms(("b","a"))),u.hyp("reverse"),u.hyp("ordered"))))
            names=("a","b")
        return OrElim(specialize(t,"le_or_lt",*t.terms(names)),left,right)
    return introduce(s,("a","b"),(),finish)


def _factorial_unique(s,target):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,EqTrans,Ind
    from peano_lab.kernel.terms import Zero,Succ
    def base(t):
        left=apply(specialize(t,"factorial_zero",Zero(),t.term("f")),EqRefl(Zero()),t.hyp("left"))
        right=apply(specialize(t,"factorial_zero",Zero(),t.term("g")),EqRefl(Zero()),t.hyp("right"))
        return EqTrans(left,EqSym(right))
    def finish(t):
        equal=apply(specialize(t,"IH",*t.terms(("p","q"))),AndElimL(t.hyp("previous_left")),AndElimL(t.hyp("previous_right")))
        return EqTrans(AndElimR(t.hyp("previous_left")),EqTrans(CongMul(equal,EqRefl(Succ(t.term("n")))),EqSym(AndElimR(t.hyp("previous_right")))))
    def successor(t):
        def right(u):
            previous=apply(specialize(u,"factorial_step",u.term("n"),Succ(u.term("n")),u.term("g")),EqRefl(Succ(u.term("n"))),u.hyp("right"))
            return eliminate(u,previous,("q",),"previous_right",finish)
        previous=apply(specialize(t,"factorial_step",t.term("n"),Succ(t.term("n")),t.term("f")),EqRefl(Succ(t.term("n"))),t.hyp("left"))
        return eliminate(t,previous,("p",),"previous_left",right)
    return Ind(target.body,introduce(s,("f","g"),("left","right"),base),
        introduce(s,("n",),("IH",),lambda t:introduce(t,("f","g"),("left","right"),successor)))


def _functional_decision(s,registry,name):
    from peano_lab.kernel.proofs import OrElim,OrIntroL,OrIntroR
    inputs,rel=FUNCTIONS[name]
    def computed(t):
        def yes(u):
            return OrIntroL(_subst(u,registry,relation(rel,inputs,"slot"),u.hyp("equal"),u.hyp("computed")))
        def no(u):
            return OrIntroR(introduce(u,(),("candidate",),lambda v:
                apply(v.hyp("different"),apply(specialize(v,name+"_unique",*v.terms(inputs+("z","v"))),v.hyp("computed"),v.hyp("candidate")))))
        return OrElim(specialize(t,"eq_dec",*t.terms(("z","v"))),yes(t.hypothesis("equal")),no(t.hypothesis("different")))
    return introduce(s,inputs+("v",),(),lambda t:
        eliminate(t,specialize(t,name+"_exists",*t.terms(inputs)),("z",),"computed",computed))


def _floor_dec(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqSym,OrElim,OrIntroL,OrIntroR
    def computed(t):
        def yes(u):
            return OrIntroL(_subst(u,registry,"FloorSqrt(n,slot)",u.hyp("equal"),AndElimL(u.hyp("computed"))))
        def no(u):
            return OrIntroR(introduce(u,(),("candidate",),lambda v:
                apply(v.hyp("different"),EqSym(apply(instantiate(AndElimR(v.hyp("computed")),v.term("v")),v.hyp("candidate"))))))
        return OrElim(specialize(t,"eq_dec",*t.terms(("z","v"))),yes(t.hypothesis("equal")),no(t.hypothesis("different")))
    return introduce(s,("n","v"),(),lambda t:eliminate(t,specialize(t,"floor_total_unique",t.term("n")),("z",),"computed",computed))


def factories(registry):
    from sqrt2_power_definitions import parse_named
    unique=parse_named(HELPER_SOURCES["factorial_unique"],registry=registry)
    return dict(lt_ne=lambda s:_lt_ne(s,registry),eq_dec=_eq_dec,
        le_dec=lambda s:_order_dec(s,False),lt_dec=lambda s:_order_dec(s,True),
        factorial_unique=lambda s:_factorial_unique(s,unique),
        **{name+"_dec":lambda s,name=name:_functional_decision(s,registry,name) for name in FUNCTIONS},
        floor_dec=lambda s:_floor_dec(s,registry),AP024=lambda s:conjunction(*(s.hyp(name) for name in DECISIONS)))


def prove_atomic_computation_decisions(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP024",target=frozen_atomic_computation_decisions_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories(registry),pins=atomic_computation_decisions_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
