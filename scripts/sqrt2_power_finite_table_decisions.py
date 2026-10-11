"""AP026: compile constructive decisions of the actual finite sample tables.

Decode actual beta/power values, decide their row property, then use bounded
induction for every index of the supplied table. Incorrect tables are covered,
including empty prefixes; no computation-correctness premise is assumed.
The schema generates ordinary HA proof terms, with no new logical rule.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_approximation_component_decisions import (
    ROOT,Scope,introduce,eliminate,apply,specialize,conjunction,canonical,json_hash,
    _and,decision,conjunction_decision,DECISION_ARCHIVE,COMPOSITION_ARCHIVE,
    approximation_component_decisions_source_pins,HELPER_SOURCES as COMPONENT_HELPERS,
)
from sqrt2_power_atomic_computation_decisions import HELPER_SOURCES as ATOMIC_HELPERS,ENDPOINT_SOURCES as ATOMIC_ENDPOINTS
from sqrt2_power_exp_sample import definition_registry as sample_registry
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-finite-table-decisions-v1"
ROWS={
    "coefficient":dict(fixed=("d","ab","ac"),outputs=("a",),
        computations=(("beta",("ab","ac","j")),)),
    "weight":dict(fixed=("d","wb","wc"),outputs=("a","b"),
        computations=(("beta",("wb","wc","j")),("beta",("wb","wc","S j")))),
    "term":dict(fixed=("x","wb","wc","tb","tc"),outputs=("w","p","t"),
        computations=(("beta",("wb","wc","j")),("power",("x","j")),("beta",("tb","tc","j")))),
}


def property_source(key,values,index="j"):
    if key=="coefficient":
        return f"NatAtanhCoefficient(d,{index},{values[0]})"
    if key=="weight":
        return f"{values[0]}=((S ({index}))*d)*{values[1]}"
    if key=="term":
        return f"{values[2]}={values[0]}*{values[1]}"
    raise ValueError("unknown finite-table property")


def row_source(key,index="j",length=None):
    spec=ROWS[key];outputs=spec["outputs"]
    graphs=[]
    if length is not None:
        graphs.append(f"Lt({index},{length})")
    for output,(kind,inputs) in zip(outputs,spec["computations"]):
        args=tuple(index if v=="j" else "S ("+index+")" if v=="S j" else v for v in inputs)
        graphs.append(("BetaAt" if kind=="beta" else "Pow")+"("+",".join(args+(output,))+")")
    body=" -> ".join(graphs+[property_source(key,outputs,index)])
    return "forall "+" ".join((("j",) if length is not None else ())+outputs)+". "+body


HELPER_SOURCES={
    **{key+"_row_dec":"forall "+" ".join(spec["fixed"]+("j",))+". "+decision(row_source(key)) for key,spec in ROWS.items()},
    **{key+"_prefix_dec":"forall "+" ".join(spec["fixed"]+("N",))+". "+decision(row_source(key,length="N")) for key,spec in ROWS.items()},
    "weight_table_dec":"forall d N wb wc. "+decision("NatExpWeightTable(d,N,wb,wc)"),
}
PARTS=("forall d ab ac N. "+decision("NatAtanhPrefix(d,ab,ac,N)"),
    HELPER_SOURCES["weight_table_dec"],
    "forall x wb wc tb tc N. "+decision("NatPowerWeightedPrefix(x,wb,wc,tb,tc,N)"))
NAMED_SOURCE=_and(tuple("("+source+")" for source in PARTS))
TARGET_SHA256="6dbc10516866227c027792d1af728a7e88461da6be67734ad5f93540f85317ce"
HELPER_TARGET_SHA256={
    "coefficient_row_dec":"7a89552f1850a4e7a57ea20bd0c7e53fa1b11622904025b0453b4c14155e3642",
    "weight_row_dec":"b055b7ddea77e6b37467cd5552c0e306969573cc18d6a469d7464baac98586ed",
    "term_row_dec":"ac28a3f047b329da268441fa1dc73c16e3811b6fdf8a48f60f4aaf19a04636da",
    "coefficient_prefix_dec":"a53dbe3d9673c6f3d7ab5f58a341955570be997d8e60961c96ed68607f0bb328",
    "weight_prefix_dec":"6cb818c13279cc9732a452b52a1f5832152ac6f0c2fd4be96d168b6da3fd7b50",
    "term_prefix_dec":"d87184c04c5bba0f16299fcda4f645d503233749398032bced000796f95fb0c4",
    "weight_table_dec":"66b8ad9735a422f9ef31f42651e5499c26d65b9e8ed5311aef3f8e00255001c3",
}
COMPONENT_ARCHIVE=dict(case="AP025",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-approximation-component-decisions-v1/generation-process.json.gz",
    bytes=44027,sha256="7867a1303de3dd7ade568f8e0cb48ba3e0a2d986c3e34a5de172a25aa7f4545d",
    raw_bytes=496003,raw_sha256="9383b6e1a83e2f166f02cf8a689b678f33ca1901300c6aa27d8584f01a456b28",
    bundle_bytes=266977,bundle_sha256="541015fd0e99e2c907df19bcb07a173646ac30354ddda32986fab3b496091d71",
    nodes=146,root=145,target_ast_sha256="73143d6dbbcad9e7c4558786a63cf9abc8870be8c71abd9d934090ddb9501c21")
ARCHIVES=(COMPONENT_ARCHIVE,DECISION_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={"eq_dec":ATOMIC_HELPERS["eq_dec"],"beta_dec":ATOMIC_HELPERS["beta_dec"],
    "coefficient_dec":COMPONENT_HELPERS["coefficient_dec"],
    **{name:ATOMIC_ENDPOINTS[name] for name in ("beta_exists","beta_unique","power_exists","power_unique","le_refl","le_eq_or_lt","lt_not_le")},
    "zero_le":"forall a. Le(0,a)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
}
ENDPOINT_OWNERS={name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(eq_dec="AP024",beta_dec="AP024",coefficient_dec="AP025")
BOUNDED_DEPENDENCIES=("lt_not_le","zero_le","le_succ","le_of_succ_le_succ","le_eq_or_lt","le_refl")
HELPER_DEPENDENCIES={
    "coefficient_row_dec":("beta_exists","beta_unique","coefficient_dec"),
    "weight_row_dec":("beta_exists","beta_unique","eq_dec"),
    "term_row_dec":("beta_exists","beta_unique","power_exists","power_unique","eq_dec"),
    **{key+"_prefix_dec":(key+"_row_dec",)+BOUNDED_DEPENDENCIES for key in ROWS},
    "weight_table_dec":("beta_dec","weight_prefix_dec"),
    "AP026":("coefficient_prefix_dec","weight_table_dec","term_prefix_dec"),
}


class FiniteTableDecisionsError(ValueError):
    """Changed finite domain, supplied table, computation guard or proof bytes."""


def definition_registry():
    source=sample_registry();needed=set();pending=["NatAtanhPrefix","NatExpWeightTable","NatPowerWeightedPrefix"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed}
    # Le and Lt have the same strict/nonstrict expansion used by the bounded schema.
    if "Le" not in result:
        result={name:spec for name,spec in source.items() if name in needed or name=="Le"}
    seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise FiniteTableDecisionsError("finite decision definition DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_finite_table_decisions_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    if type(target) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FiniteTableDecisionsError("AP026 exact finite table decisions changed")
    return target


def source_contract():
    return dict(code="AP026",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,constructive_decisions=["NatAtanhPrefix","NatExpWeightTable","NatPowerWeightedPrefix"],
        arbitrary_supplied_tables_including_invalid_ones=True,zero_scale_and_empty_prefix_allowed=True,
        beta_and_power_values_actually_constructed=True,value_uniqueness_replayed=True,
        deterministic_row_and_bounded_prefix_proof_schemas=True,classical_axioms_used=False,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=True,
        complete_CApprox_verifier_claim=False,canonical_PR_approximation_algorithm_claim=False,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def finite_table_decisions_source_pins():
    result=approximation_component_decisions_source_pins()
    expected={"scripts/sqrt2_power_approximation_component_decisions.py":"4a60373031dd1aaa94ea49e8b0fb61f9b87e49e20444c6e8722d6d330599ae90",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_finite_table_decisions.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FiniteTableDecisionsError("finite table decision source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _term(s,source):
    from peano_lab.kernel.terms import parse_term_in_context
    return parse_term_in_context(source,list(s.variables))


def _row_decision(s,registry,key):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import OrElim,OrIntroL,OrIntroR
    spec=ROWS[key];outputs=spec["outputs"];computed=tuple(name+"0" for name in outputs)
    hypotheses=tuple("entry_"+name for name in outputs)
    def decoded(t):
        def yes(u):
            def transport(v):
                proof=v.hyp("property_true");values=list(computed)
                for i,(output,(kind,inputs)) in enumerate(zip(outputs,spec["computations"])):
                    equal=apply(specialize(v,kind+"_unique",*(_term(v,term) for term in inputs),*v.terms((computed[i],output))),
                        v.hyp("computed_"+output),v.hyp(hypotheses[i]))
                    motive=list(values);motive[i]="slot"
                    proof=_subst(v,registry,property_source(key,tuple(motive)),equal,proof)
                    values[i]=output
                return proof
            return OrIntroL(introduce(u,outputs,hypotheses,transport))
        def no(u):
            return OrIntroR(introduce(u,(),("candidate",),lambda v:apply(v.hyp("property_false"),
                apply(specialize(v,"candidate",*v.terms(computed)),*(v.hyp("computed_"+output) for output in outputs)))))
        if key=="coefficient":
            verdict=specialize(t,"coefficient_dec",*t.terms(("d","j",computed[0])))
        else:
            equation=property_source(key,computed).split("=")
            verdict=specialize(t,"eq_dec",*(_term(t,side) for side in equation))
        return OrElim(verdict,yes(t.hypothesis("property_true")),no(t.hypothesis("property_false")))
    def compute(t,index):
        if index==len(outputs):
            return decoded(t)
        kind,inputs=spec["computations"][index]
        actual=specialize(t,kind+"_exists",*(_term(t,term) for term in inputs))
        return eliminate(t,actual,(computed[index],),"computed_"+outputs[index],lambda u:compute(u,index+1))
    return introduce(s,spec["fixed"]+("j",),(),lambda t:compute(t,0))


def _prefix_decision(s,registry,key,target):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import BotElim,EqSym,Ind,OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Succ,Zero
    spec=ROWS[key];outputs=spec["outputs"];hypotheses=tuple("entry_"+name for name in outputs)
    def base(t):
        return OrIntroL(introduce(t,("j",)+outputs,("bound",)+hypotheses,lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("j"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("j"))))))
    def successor(t):
        def previous_no(u):
            def contradiction(v):
                def restrict(w):
                    bound=apply(specialize(w,"le_succ",Succ(w.term("j")),w.term("N")),w.hyp("bound"))
                    return apply(specialize(w,"candidate",*w.terms(("j",)+outputs)),bound,*(w.hyp(name) for name in hypotheses))
                return apply(v.hyp("previous_no"),introduce(v,("j",)+outputs,("bound",)+hypotheses,restrict))
            return OrIntroR(introduce(u,(),("candidate",),contradiction))
        def previous_yes(u):
            def last_yes(v):
                def at(w):
                    bound=apply(specialize(w,"le_of_succ_le_succ",*w.terms(("j","N"))),w.hyp("bound"))
                    def last(z):
                        moved=_subst(z,registry,row_source(key,index="slot"),EqSym(z.hyp("last_index")),z.hyp("last_yes"))
                        return apply(instantiate(moved,*z.terms(outputs)),*(z.hyp(name) for name in hypotheses))
                    def earlier(z):
                        return apply(specialize(z,"previous_yes",*z.terms(("j",)+outputs)),z.hyp("earlier"),*(z.hyp(name) for name in hypotheses))
                    return OrElim(apply(specialize(w,"le_eq_or_lt",*w.terms(("j","N"))),bound),last(w.hypothesis("last_index")),earlier(w.hypothesis("earlier")))
                return OrIntroL(introduce(v,("j",)+outputs,("bound",)+hypotheses,at))
            def last_no(v):
                def contradiction(w):
                    def extract(z):
                        return apply(specialize(z,"candidate",z.term("N"),*z.terms(outputs)),specialize(z,"le_refl",Succ(z.term("N"))),*(z.hyp(name) for name in hypotheses))
                    return apply(w.hyp("last_no"),introduce(w,outputs,hypotheses,extract))
                return OrIntroR(introduce(v,(),("candidate",),contradiction))
            return OrElim(specialize(u,key+"_row_dec",*u.terms(spec["fixed"]+("N",))),last_yes(u.hypothesis("last_yes")),last_no(u.hypothesis("last_no")))
        return OrElim(t.hyp("IH"),previous_yes(t.hypothesis("previous_yes")),previous_no(t.hypothesis("previous_no")))
    motive=target
    for _ in spec["fixed"]+("N",):
        motive=motive.body
    return introduce(s,spec["fixed"],(),lambda t:Ind(motive,base(t),introduce(t,("N",),("IH",),successor)))


def _weight_table_dec(s):
    from peano_lab.kernel.terms import Succ,Zero
    return introduce(s,("d","N","wb","wc"),(),lambda t:conjunction_decision(t,(
        lambda u:specialize(u,"beta_dec",*u.terms(("wb","wc","N")),Succ(Zero())),
        lambda u:specialize(u,"weight_prefix_dec",*u.terms(("d","wb","wc","N")))),"weights"))


def factories(registry):
    from sqrt2_power_definitions import parse_named
    return {**{key+"_row_dec":lambda s,key=key:_row_decision(s,registry,key) for key in ROWS},
        **{key+"_prefix_dec":lambda s,key=key:_prefix_decision(s,registry,key,parse_named(HELPER_SOURCES[key+"_prefix_dec"],registry=registry)) for key in ROWS},
        "weight_table_dec":_weight_table_dec,
        "AP026":lambda s:conjunction(*(s.hyp(name) for name in HELPER_DEPENDENCIES["AP026"]))}


def prove_finite_table_decisions(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP026",target=frozen_finite_table_decisions_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories(registry),pins=finite_table_decisions_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=3)
