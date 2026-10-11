"""AP017: pair actual Horner steps across an odd-index coefficient slice.

For every base t, including zero, zero even entries through index 2*k give
Horner(A,t,2*k+1)=t*Horner(B,t*t,k), where B is the actual odd-index slice.
An explicit induction compares the supplied histories; no sum identity or
matching of independently encoded histories is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_atanh_odd_slice import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,atanh_odd_slice_source_pins,HELPER_SOURCES as INDEX_HELPERS,
    COMPOSITION_ARCHIVE,BOUND_ARCHIVE,_chain,_subst,
)
from sqrt2_power_horner_splitting import definition_registry as source_registry,horner_splitting_source_pins,ENDPOINT_SOURCES as HORNER_ENDPOINTS
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-paired-horner-v1"
A,B,HA,HB=("ab","ac"),("bb","bc"),("ahb","ahc"),("bhb","bhc")
PARAMETERS=A+B+("t","K","x","y")
FIXED=A+B+("t","K")+HA+HB
SLICE="NatAffineSlice(ab,ac,1,2,bb,bc,K)"
EVEN="forall j a. Le(j,K) -> BetaAt(ab,ac,2*j,a) -> a=0"
TRACE_A="NatScaledHornerTrace(ab,ac,t,S(2*K),ahb,ahc)"
TRACE_B="NatScaledHornerTrace(bb,bc,t*t,K,bhb,bhc)"
ALL_PAIRS="forall j x y. Le(j,K) -> BetaAt(ahb,ahc,S(2*j),x) -> BetaAt(bhb,bhc,j,y) -> x=t*y"
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+SLICE+" -> ("+EVEN+") -> NatHornerValue(ab,ac,t,S(2*K),x) -> NatHornerValue(bb,bc,t*t,K,y) -> x=t*y"
TARGET_SHA256="5235c154de5a45ae307e0f3e33b64ea3ba043dd2efe3fdc302aa824d100fe5d9"
HELPER_SOURCES={
    "even_entry":"forall ab ac K j. ("+EVEN+") -> Le(j,K) -> BetaAt(ab,ac,2*j,0)",
    "step_bounds":"forall j K. Le(S j,K) -> Le(j,K) /\\ (Lt(S(2*j),S(2*K)) /\\ Lt(2*(S j),S(2*K)))",
    "paired_step":"forall t x0 y0 a middle x y. x0=t*y0 -> middle=t*x0+a -> x=t*middle+0 -> y=(t*t)*y0+a -> x=t*y",
    "all_pairs":"forall "+" ".join(FIXED)+". "+SLICE+" -> ("+EVEN+") -> "+TRACE_A+" -> "+TRACE_B+" -> "+ALL_PAIRS,
}
HELPER_TARGET_SHA256={"even_entry":"45ac3d337d56447651568ea08591d972b2bf721ce7fa75fd7dd7acde850f6992",
    "step_bounds":"0bf98dfed8feeee2665fce57f385c130c1721075d9ab1d729135c69be689f295",
    "paired_step":"d66e40336479fe78720c715a975f61fd913cf9b1f4bb4dbfeadad26d6c9cd5fa",
    "all_pairs":"c8af52a0479ec10ee56d072104126f6e0a777d4447956b41254e6f0c32df81d2"}
INDEX_ARCHIVE=dict(case="AP016",path="research/arithmetic-library/sqrt2-power/observations/shared-wave-atanh-odd-slice-v1/generation-process.json.gz",
    bytes=27142,sha256="42905cf06ff3466ac93ff03819f18d989ebb08fb99e3531ecbb54ccdadd929ae",
    raw_bytes=327213,raw_sha256="4a138549094c4aec6a12d048f074f9583e75c9af9b9bac29ea504fde07934a74",
    bundle_bytes=167248,bundle_sha256="6623977ef1c4aba8612a0450d2e0fb1484d6cb00f31a5b7d14b70187c5660c00",
    nodes=113,root=112,target_ast_sha256="ebf68fd1ca1f37cd10b7e77ef28a69acf4aa4c4995cd8c215a6bc3d8a9f1d894")
ARCHIVES=(INDEX_ARCHIVE,COMPOSITION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "index":INDEX_HELPERS["index"],"even_bound":INDEX_HELPERS["even_bound"],"odd_bound":INDEX_HELPERS["odd_bound"],
    "double_succ":"forall j. 2*(S j)=S(S(2*j))",
    **{name:HORNER_ENDPOINTS[name] for name in ("beta_exists","beta_unique","step_value","mul_assoc")},
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "zero_le":"forall a. Le(0,a)","succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(index="AP016",even_bound="AP016",odd_bound="AP016",double_succ="AP016",beta_exists="CV061",beta_unique="CV061",step_value="CV061")
HELPER_DEPENDENCIES={
    "even_entry":("beta_exists",),"step_bounds":("le_refl","le_succ","le_trans","odd_bound","even_bound"),
    "paired_step":("mul_assoc",),
    "all_pairs":("even_entry","step_bounds","paired_step","index","double_succ","beta_exists","beta_unique","step_value","zero_le","succ_le_succ"),
    "AP017":("all_pairs","le_refl"),
}


class PairedHornerError(ValueError):
    """Changed actual histories, zero even entries, odd slice or paired base."""


def definition_registry():
    source=source_registry();needed=set();pending=["NatAffineSlice","NatHornerValue","Le"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed}
    seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise PairedHornerError("paired Horner conservative DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_paired_horner_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=8 or len(premises)!=4 or type(conclusion) is not Eq or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PairedHornerError("AP017 exact paired-Horner target changed")
    return target


def source_contract():
    return dict(code="AP017",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,actual_supplied_odd_slice_and_both_horner_values_preserved=True,
        zero_even_entries_through_terminal_index_required=True,paired_base="t*t",
        exact_identity="x=t*y",zero_base_and_empty_odd_slice_allowed=True,
        all_pairs_compared_by_explicit_induction=True,code_number_equality_claimed=False,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=True,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def paired_horner_source_pins():
    result=atanh_odd_slice_source_pins()
    for name,pin in horner_splitting_source_pins().items():
        if name in result and result[name]!=pin:
            raise PairedHornerError("paired-Horner source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_atanh_odd_slice.py":"91fcf50ee5a35c19605a11497e6d7aca2970257cb468f383997b1a62d3208210",
        "scripts/sqrt2_power_horner_splitting.py":"17d330dc31b9e7c6aca718bbce4c4cbbeab881783cb42118b3e0a76c322fe27a",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_paired_horner.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PairedHornerError("paired-Horner source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _even_entry(s,registry):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()))
    def chosen(t):
        value=apply(specialize(t,"even",*t.terms(("j","a"))),t.hyp("bound"),t.hyp("entry"))
        return _subst(t,registry,"BetaAt(ab,ac,2*j,slot)",value,t.hyp("entry"))
    return introduce(s,A+("K","j"),("even","bound"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(A),Mul(two,t.term("j"))),("a",),"entry",chosen))


def _step_bounds(s):
    from peano_lab.kernel.terms import Succ
    def finish(t):
        j,K=t.terms(("j","K"))
        lower=apply(specialize(t,"le_trans",j,Succ(j),K),apply(specialize(t,"le_succ",j,j),specialize(t,"le_refl",j)),t.hyp("bound"))
        return conjunction(lower,apply(specialize(t,"odd_bound",j,K),t.hyp("bound")),apply(specialize(t,"even_bound",Succ(j),K),t.hyp("bound")))
    return introduce(s,("j","K"),("bound",),finish)


def _paired_step(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        base,x0,y0,a,middle,x,y=t.terms(("t","x0","y0","a","middle","x","y"))
        inside=_chain(t.hyp("middle_eq"),CongAdd(CongMul(EqRefl(base),t.hyp("old")),EqRefl(a)),
            CongAdd(EqSym(specialize(t,"mul_assoc",base,base,y0)),EqRefl(a)),EqSym(t.hyp("short_eq")))
        return _chain(t.hyp("long_eq"),instantiate(Axiom("PA3"),Mul(base,middle)),CongMul(EqRefl(base),inside))
    return introduce(s,("t","x0","y0","a","middle","x","y"),("old","middle_eq","long_eq","short_eq"),finish)


def _all_pairs(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongMul,CongS,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    zero=Zero();one=Succ(zero);two=Succ(one)
    def base(t):
        base,K,x,y=t.terms(("t","K","x","y"))
        coefficient=apply(specialize(t,"even_entry",*t.terms(A),K,zero),t.hyp("even"),specialize(t,"zero_le",K))
        coefficient=_subst(t,registry,"BetaAt(ab,ac,slot,0)",instantiate(Axiom("PA5"),two),coefficient)
        long_value=_subst(t,registry,"BetaAt(ahb,ahc,slot,x)",CongS(instantiate(Axiom("PA5"),two)),t.hyp("left_value"))
        bound=apply(specialize(t,"succ_le_succ",zero,Mul(two,K)),specialize(t,"zero_le",Mul(two,K)))
        step=apply(instantiate(AndElimR(t.hyp("left_trace")),zero),bound)
        value=apply(specialize(t,"step_value",*t.terms(A),base,*t.terms(HA),zero,zero,zero,x),
            step,AndElimL(t.hyp("left_trace")),coefficient,long_value)
        right_zero=apply(specialize(t,"beta_unique",*t.terms(HB),zero,y,zero),t.hyp("right_value"),AndElimL(t.hyp("right_trace")))
        return _chain(value,instantiate(Axiom("PA3"),Mul(base,zero)),CongMul(EqRefl(base),EqSym(right_zero)))
    def successor(t):
        def chosen(u):
            base,K,j,x,y,x0,y0,middle,a=u.terms(("t","K","j","x","y","previous_x","previous_y","middle","coefficient"))
            even_index=Mul(two,Succ(j));odd_index=Succ(Mul(two,j));bounds=apply(specialize(u,"step_bounds",j,K),u.hyp("bound"))
            old=apply(specialize(u,"IH",x0,y0),field(bounds,0,3),u.hyp("old_left"),u.hyp("old_right"))
            coefficient=apply(specialize(u,"slice",j,a),u.hyp("bound"),u.hyp("odd_entry"))
            coefficient=_subst(u,registry,"BetaAt(ab,ac,slot,coefficient)",specialize(u,"index",j),coefficient)
            next_zero=apply(specialize(u,"even_entry",*u.terms(A),K,Succ(j)),u.hyp("even"),u.hyp("bound"))
            first_step=apply(instantiate(AndElimR(u.hyp("left_trace")),odd_index),field(bounds,1,3))
            middle_value=_subst(u,registry,"BetaAt(ahb,ahc,slot,middle)",specialize(u,"double_succ",j),u.hyp("middle_value"))
            first=apply(specialize(u,"step_value",*u.terms(A),base,*u.terms(HA),odd_index,x0,a,middle),first_step,u.hyp("old_left"),coefficient,middle_value)
            last_step=apply(instantiate(AndElimR(u.hyp("left_trace")),even_index),field(bounds,2,3))
            last=apply(specialize(u,"step_value",*u.terms(A),base,*u.terms(HA),even_index,middle,zero,x),last_step,u.hyp("middle_value"),next_zero,u.hyp("left_value"))
            short_step=apply(instantiate(AndElimR(u.hyp("right_trace")),j),u.hyp("bound"))
            short=apply(specialize(u,"step_value",*u.terms(B),Mul(base,base),*u.terms(HB),j,y0,a,y),short_step,u.hyp("old_right"),u.hyp("odd_entry"),u.hyp("right_value"))
            return apply(specialize(u,"paired_step",base,x0,y0,a,middle,x,y),old,first,last,short)
        return eliminate(t,specialize(t,"beta_exists",*t.terms(HA),Succ(Mul(two,t.term("j")))),("previous_x",),"old_left",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(HB),u.term("j")),("previous_y",),"old_right",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(HA),Mul(two,Succ(v.term("j")))),("middle",),"middle_value",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(B),w.term("j")),("coefficient",),"odd_entry",chosen))))
    motive=target
    for _ in FIXED:
        motive=motive.body
    for _ in range(4):
        motive=motive.right
    motive=motive.body
    def induction(t):
        return Ind(motive,introduce(t,("x","y"),("bound","left_value","right_value"),base),
            introduce(t,("j",),("IH",),lambda u:introduce(u,("x","y"),("bound","left_value","right_value"),successor)))
    return introduce(s,FIXED,("slice","even","left_trace","right_trace"),induction)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def chosen(t):
        pairs=apply(specialize(t,"all_pairs",*t.terms(FIXED)),t.hyp("slice"),t.hyp("even"),AndElimL(t.hyp("left_history")),AndElimL(t.hyp("right_history")))
        return apply(instantiate(pairs,*t.terms(("K","x","y"))),specialize(t,"le_refl",t.term("K")),AndElimR(t.hyp("left_history")),AndElimR(t.hyp("right_history")))
    return introduce(s,PARAMETERS,("slice","even","left_value","right_value"),lambda t:
        eliminate(t,t.hyp("left_value"),HA,"left_history",lambda u:
            eliminate(u,u.hyp("right_value"),HB,"right_history",chosen)))


def prove_paired_horner(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry();pairs=parse_named(HELPER_SOURCES["all_pairs"],registry=registry)
    return assemble_mixed_certificate(code="AP017",target=frozen_paired_horner_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"even_entry":lambda s:_even_entry(s,registry),"step_bounds":_step_bounds,"paired_step":_paired_step,
            "all_pairs":lambda s:_all_pairs(s,pairs,registry),"AP017":_root},
        pins=paired_horner_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
