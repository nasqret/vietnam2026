"""AP016: construct the exact odd-index reciprocal table of a supplied prefix.

The actual affine slice is constructed by the existing beta-table theorem.
Parity separation proves its odd quotient equations and the original even
zeros. No infinite sum, analytic identity, positivity or canonical code is
assumed; empty slices and a zero coefficient scale remain allowed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_atanh_scale_independence import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as source_registry,
    atanh_scale_independence_source_pins,PARITY_HELPERS,ATANH_EULER_ARCHIVE,_chain,_subst,
)
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE
from sqrt2_power_scaled_exp_tail import BOUND_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-atanh-odd-slice-v1"
PREFIX="NatAtanhPrefix(d,ab,ac,S(2*k))"
SLICE="NatAffineSlice(ab,ac,1,2,bb,bc,k)"
ODD="forall j a. Lt(j,k) -> BetaAt(bb,bc,j,a) -> (S(2*j))*a=2*d"
EVEN="forall j a. Le(j,k) -> BetaAt(ab,ac,2*j,a) -> a=0"
NAMED_SOURCE="forall d ab ac k. "+PREFIX+" -> exists bb bc. "+SLICE+" /\\ (("+ODD+") /\\ ("+EVEN+"))"
TARGET_SHA256="ebf68fd1ca1f37cd10b7e77ef28a69acf4aa4c4995cd8c215a6bc3d8a9f1d894"
HELPER_SOURCES={
    "even_coefficient":"forall d j a. NatAtanhCoefficient(d,2*j,a) -> a=0",
    "odd_coefficient":"forall d j a. NatAtanhCoefficient(d,S(2*j),a) -> (S(2*j))*a=2*d",
    "even_bound":"forall j k. Le(j,k) -> Lt(2*j,S(2*k))",
    "odd_bound":"forall j k. Lt(j,k) -> Lt(S(2*j),S(2*k))",
    "index":"forall j. 1+2*j=S(2*j)",
}
HELPER_TARGET_SHA256={"even_coefficient":"8786ee67ab37a7367ecb360a0476b245abf2edfeea87e958e660876f56d12427",
    "odd_coefficient":"83dab31e42e01b615a175864746425c56834f8028ea6adc021b0d987d34ae896",
    "even_bound":"c9a4126a8da602c25395e7a210d5cb0930585cad7139bd84e084f78810551a2b",
    "odd_bound":"f50317b4501019083944293be004fe283dfb00f40eba204cf922058b0a830dab",
    "index":"8df1e7c9f03b471aa785526b52d83dad6ab8d0ac7f1a12882dd23add2c123262"}
ARCHIVES=(ATANH_EULER_ARCHIVE,COMPOSITION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={"even_not_odd":PARITY_HELPERS["even_not_odd"],"double_succ":PARITY_HELPERS["double_succ"],
    "slice_exists":"forall ab ac o t N. exists ub uc. NatAffineSlice(ab,ac,o,t,ub,uc,N)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)","add_comm":"forall a b. a+b=b+a"}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(even_not_odd="CV026",double_succ="CV026",slice_exists="CV061")
HELPER_DEPENDENCIES={"even_coefficient":("even_not_odd",),"odd_coefficient":("even_not_odd",),
    "even_bound":("mul_left_mono","succ_le_succ"),"odd_bound":("mul_left_mono","le_succ","double_succ"),
    "index":("add_comm",),"AP016":("slice_exists","even_coefficient","odd_coefficient","even_bound","odd_bound","index")}


class AtanhOddSliceError(ValueError):
    """Changed actual odd slice, parity, quotient equations or scope."""


def definition_registry():
    source=source_registry();needed=set();pending=["NatAtanhPrefix","NatAffineSlice","Le"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed}
    seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise AtanhOddSliceError("existing odd-slice definition DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_atanh_odd_slice_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=4 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise AtanhOddSliceError("AP016 exact odd-index computation target changed")
    return target


def source_contract():
    return dict(code="AP016",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,actual_supplied_atanh_prefix_preserved=True,actual_odd_index_slice_constructed=True,
        odd_indices="1+2*j for j<k",odd_quotient_equation="(2*j+1)*a=2*d",
        even_zero_indices="2*j for j<=k",empty_slice_and_zero_scale_allowed=True,
        parity_uses_actual_even_not_odd_certificate=True,code_number_equality_claimed=False,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def atanh_odd_slice_source_pins():
    result=atanh_scale_independence_source_pins()
    expected={"scripts/sqrt2_power_atanh_scale_independence.py":"bc346b492c242367d2703c2bc9391b1ae0c289a518098e1aa30b3b70252e448d",
        "scripts/sqrt2_power_horner_splitting.py":"17d330dc31b9e7c6aca718bbce4c4cbbeab881783cb42118b3e0a76c322fe27a",
        "scripts/sqrt2_power_scaled_exp_tail.py":"df81a3c92b26346a1955ba92e763d932201649183604309f17bd156b2abbaeb3",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_atanh_odd_slice.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise AtanhOddSliceError("odd-slice source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _coefficient(s,odd):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,EqSym,OrElim
    def branch(t,is_odd):
        def chosen(u):
            if odd==is_odd:
                return AndElimR(u.hyp("data"))
            j,z=u.terms(("j","z"));equality=AndElimL(u.hyp("data"))
            if odd:
                return BotElim(apply(specialize(u,"even_not_odd",z,j),EqSym(equality)))
            return BotElim(apply(specialize(u,"even_not_odd",j,z),equality))
        return eliminate(t,t.hyp("case"),("z",),"data",chosen)
    return introduce(s,("d","j","a"),("coefficient",),lambda t:
        OrElim(t.hyp("coefficient"),branch(t.hypothesis("case"),False),branch(t.hypothesis("case"),True)))


def _even_bound(s):
    from peano_lab.kernel.terms import Mul,parse_term
    two=parse_term("2")
    def finish(t):
        j,k=t.terms(("j","k"))
        doubled=apply(specialize(t,"mul_left_mono",j,k,two),t.hyp("bound"))
        return apply(specialize(t,"succ_le_succ",Mul(two,j),Mul(two,k)),doubled)
    return introduce(s,("j","k"),("bound",),finish)


def _odd_bound(s,registry):
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    two=parse_term("2")
    def finish(t):
        j,k=t.terms(("j","k"));left=Succ(Succ(Mul(two,j)));right=Mul(two,k)
        doubled=apply(specialize(t,"mul_left_mono",Succ(j),k,two),t.hyp("bound"))
        doubled=_subst(t,registry,"Le(slot,2*k)",specialize(t,"double_succ",j),doubled)
        return apply(specialize(t,"le_succ",left,right),doubled)
    return introduce(s,("j","k"),("bound",),finish)


def _index(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongS
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        doubled=Mul(Succ(Succ(Zero())),t.term("j"))
        return _chain(specialize(t,"add_comm",Succ(Zero()),doubled),instantiate(Axiom("PA4"),doubled,Zero()),CongS(instantiate(Axiom("PA3"),doubled)))
    return introduce(s,("j",),(),finish)


def _root(s,registry):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def odd(t):
        j,a,d,k=t.terms(("j","a","d","k"));index=Succ(Mul(two,j))
        entry=apply(specialize(t,"slice",j,a),t.hyp("bound"),t.hyp("entry"))
        entry=_subst(t,registry,"BetaAt(ab,ac,slot,a)",specialize(t,"index",j),entry)
        bound=apply(specialize(t,"odd_bound",j,k),t.hyp("bound"))
        coefficient=apply(specialize(t,"prefix",index,a),bound,entry)
        return apply(specialize(t,"odd_coefficient",d,j,a),coefficient)
    def even(t):
        j,a,d,k=t.terms(("j","a","d","k"))
        bound=apply(specialize(t,"even_bound",j,k),t.hyp("bound"))
        coefficient=apply(specialize(t,"prefix",Mul(two,j),a),bound,t.hyp("entry"))
        return apply(specialize(t,"even_coefficient",d,j,a),coefficient)
    def chosen(t):
        return witness(t.terms(("bb","bc")),conjunction(t.hyp("slice"),
            introduce(t,("j","a"),("bound","entry"),odd),introduce(t,("j","a"),("bound","entry"),even)))
    return introduce(s,("d","ab","ac","k"),("prefix",),lambda t:
        eliminate(t,specialize(t,"slice_exists",*t.terms(("ab","ac")),one,two,t.term("k")),("bb","bc"),"slice",chosen))


def prove_atanh_odd_slice(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP016",target=frozen_atanh_odd_slice_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"even_coefficient":lambda s:_coefficient(s,False),"odd_coefficient":lambda s:_coefficient(s,True),
            "even_bound":_even_bound,"odd_bound":lambda s:_odd_bound(s,registry),"index":_index,"AP016":lambda s:_root(s,registry)},
        pins=atanh_odd_slice_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
