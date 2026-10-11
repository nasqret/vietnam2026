"""CV096: quantitative finite exponential sum continuity at a common scale.

Actual supplied recurrences, heads and sums imply s<=t and
d*t<=d*s+9*(g*a0) when d!=0, y=x+g and y<=2*d. The proof uses actual
tail slices, finite sum transport and the existing majorant, not a limit law.
"""
from hashlib import sha256

from sqrt2_power_sum_linear_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,sum_linear_bound_source_pins,
    NAMED_SOURCE as SUM_BOUND_SOURCE,BOUND_ARCHIVE,COMPOSITION_ARCHIVE,
)
from sqrt2_power_exp_term_difference import NAMED_SOURCE as TERM_SOURCE
from sqrt2_power_sum_splitting import NAMED_SOURCE as SPLIT_SOURCE,sum_splitting_source_pins
from sqrt2_power_convolution_commutative import SPLIT_ARCHIVE
from sqrt2_power_scaled_exp_bound import HELPER_SOURCES as BOUND_HELPERS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-sum-continuity-v1"
A,B,TA,TB=("ab","ac"),("bb","bc"),("uab","uac"),("vbb","vbc")
FIXED=("d","x","y","g","N")+A+B+("a0",)
PARAMETERS=FIXED+("s","t")
COMMON=("~d=0","y=x+g","NatScaledExpRecurrence(d,x,ab,ac,N)","NatScaledExpRecurrence(d,y,bb,bc,N)",
    "BetaAt(ab,ac,0,a0)","BetaAt(bb,bc,0,a0)")
SLICE_A="NatAffineSlice(ab,ac,1,1,uab,uac,N)"
SLICE_B="NatAffineSlice(bb,bc,1,1,vbb,vbc,N)"
GRAPH_UPPER="NatLinearBound(d,g,d,uab,uac,bb,bc,vbb,vbc,N)"
GRAPH_LOWER="NatLinearBound(1,0,1,vbb,vbc,bb,bc,uab,uac,N)"
PREMISES=COMMON+("Le(y,2*d)","Sum(ab,ac,S N,s)","Sum(bb,bc,S N,t)")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> Le(s,t) /\\ Le(d*t,d*s+9*(g*a0))"
TARGET_SHA256="bcfe5d4711bda1d8f1b19f812c40c8a8cb6d8c2bf10fdb247fa69a32b08715d2"
HELPER_SOURCES={
    "split_head":"forall ab ac N a0 s. BetaAt(ab,ac,0,a0) -> Sum(ab,ac,S N,s) -> exists tb tc u. NatAffineSlice(ab,ac,1,1,tb,tc,N) /\\ (Sum(tb,tc,N,u) /\\ s=a0+u)",
    "prefix_below":"forall ab ac N s t. Sum(ab,ac,N,s) -> Sum(ab,ac,S N,t) -> Le(s,t)",
    "tail_graphs":"forall "+" ".join(FIXED+TA+TB)+". "+" -> ".join(COMMON+(SLICE_A,SLICE_B))+" -> "+GRAPH_UPPER+" /\\ "+GRAPH_LOWER,
    "finish_bound":"forall d g a0 s t u v w. s=a0+u -> t=a0+v -> Le(u,v) -> Le(d*v,d*u+g*w) -> Le(w,9*a0) -> Le(s,t) /\\ Le(d*t,d*s+9*(g*a0))",
}
HELPER_TARGET_SHA256={
    "split_head":"b52d820e72129d50f38b6e7297d2eeb61997aead2194c03a103753adf8a74429",
    "prefix_below":"8feb5216531bb336468511495291774c95cd9d7e54b5e6fbfc09ae69d539b0e0",
    "tail_graphs":"dca5aae2256b592f45d4e68fb28ff723a77c9e21d23c183070f7d4e5900df832",
    "finish_bound":"244852e147ecb3eba37a56a0a3d538c4004da23f057e746f8c3cbc4505fa1055",
}
TERM_ARCHIVE=dict(case="CV094",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-term-difference-v1/generation-process.json.gz",
    bytes=19637,sha256="81882c489ddff899f3793b64119b9cdbb8e002066ac76ac9dd06bef6ce0883aa",
    raw_bytes=179226,raw_sha256="a91a65763a3746c8614f6191572e76dd8b555b5899ed2a82390b24671fa87eed",
    bundle_bytes=72987,bundle_sha256="44a7cc4e855ca9dc684c975187a4d1ab6ca93a7159fb656c8487dcc8daff9ea6",
    nodes=40,root=39,target_ast_sha256="b58a497476351e3cc07a976d42021351568e27076943567eb7a2186d2dbc51d9")
SUM_BOUND_ARCHIVE=dict(case="CV095",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-sum-linear-bound-v1/generation-process.json.gz",
    bytes=17344,sha256="59d19cfef12071b9488370b7b02623e50cbbe2ae9c48df97846c6a181262ea66",
    raw_bytes=159776,raw_sha256="03cc3bbd8b358d41b599372ff254b609c3167bc4f0c0e935f6c6b29686dcec28",
    bundle_bytes=59957,bundle_sha256="58ccc2beee0e324cc56f96da7460606f35d20ba422fa0f1e4270dd9c50719edf",
    nodes=26,root=25,target_ast_sha256="5c476b035cc43d4fd6b3e03efbe6c35fb50f132bb036051a3e1bb5e3c1ad422a")
ARCHIVES=(TERM_ARCHIVE,SUM_BOUND_ARCHIVE,SPLIT_ARCHIVE,BOUND_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={
    "term_difference":TERM_SOURCE,"sum_bound":SUM_BOUND_SOURCE,"splitting":SPLIT_SOURCE,
    "exp_majorant":BOUND_HELPERS["all_values"],
    "sum_one":"forall b c u a. Sum(b,c,1,u) -> BetaAt(b,c,0,a) -> u=a",
    "sum_unique":"forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "sum_decompose":"forall b c L n. Sum(b,c,S L,n) -> exists a r. BetaAt(b,c,L,a) /\\ (Sum(b,c,L,r) /\\ n=r+a)",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c","add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "add_comm":"forall a b. a+b=b+a","one_mul":"forall a. 1*a=a","zero_mul":"forall a. 0*a=0",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(term_difference="CV094",sum_bound="CV095",splitting="CV009",
    sum_unique="CV061",sum_exists="CV061",sum_decompose="CV061")
HELPER_DEPENDENCIES={
    "split_head":("splitting","sum_one","sum_unique","add_comm"),
    "prefix_below":("sum_decompose","sum_unique","add_comm"),
    "tail_graphs":("term_difference","one_mul","add_comm","zero_mul"),
    "finish_bound":("add_left_mono","mul_left_mono","le_trans","mul_add","add_assoc","mul_assoc","mul_comm"),
    "CV096":("split_head","tail_graphs","sum_bound","sum_exists","prefix_below","exp_majorant","le_trans","finish_bound","one_mul","zero_mul"),
}


class ExpSumContinuityError(ValueError):
    """Changed actual finite sums, shared normalization or continuity bound."""


def frozen_exp_sum_continuity_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=12 or len(premises)!=9 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSumContinuityError("CV096 exact common-scale finite sum continuity changed")
    return target


def source_contract():
    return dict(code="CV096",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=9,two_supplied_recurrences_heads_and_sums_preserved=True,common_actual_initial_scale_required=True,
        nonzero_common_denominator_required=True,argument_gap="y=x+g",argument_bound="y<=2*d",
        monotonicity="s<=t",finite_difference="d*t<=d*s+9*(g*a0)",actual_tail_slices_constructed=True,
        pointwise_bound_and_sum_bound_separately_proved=True,zero_arguments_gap_head_and_degree_allowed=True,
        independent_denominator_transport_claimed=False,rational_division_claimed=False,analytic_limit_claim=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def exp_sum_continuity_source_pins():
    result=sum_linear_bound_source_pins()
    for name,pin in sum_splitting_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpSumContinuityError("finite continuity source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_sum_linear_bound.py":"3beb3be7e6e7c4de8a82c0d600f947a5df3259dccdf36603d12af56f2fdf7c92",
        "scripts/sqrt2_power_exp_term_difference.py":"d095d11d40de1b22ee992f2e47b4545725bcf6e63b159edce96047f78c48084b",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_sum_continuity.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSumContinuityError("finite continuity source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _one_plus(s,n):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongS
    from peano_lab.kernel.terms import Succ,Zero
    return _chain(specialize(s,"add_comm",Succ(Zero()),n),instantiate(Axiom("PA4"),n,Zero()),CongS(instantiate(Axiom("PA3"),n)))


def _split_head(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        N,a0,out,h,u,v=t.terms(("N","a0","s","head_sum","u","whole_sum"))
        data=t.hyp("split")
        whole=_subst(t,registry,"Sum(ab,ac,slot,whole_sum)",_one_plus(t,N),field(data,2,4))
        same=apply(specialize(t,"sum_unique",*t.terms(A),Succ(N),v,out),whole,t.hyp("sum"))
        head=apply(specialize(t,"sum_one",*t.terms(A),h,a0),field(data,0,4),t.hyp("head"))
        exact=_chain(EqSym(same),field(data,3,4),CongAdd(head,EqRefl(u)))
        return witness(t.terms(("tb","tc","u")),conjunction(AndElimL(t.hyp("tail")),AndElimR(t.hyp("tail")),exact))
    from peano_lab.kernel.terms import Zero
    return introduce(s,A+("N","a0","s"),("head","sum"),lambda t:
        eliminate(t,specialize(t,"splitting",*t.terms(A),Succ(Zero()),t.term("N")),("head_sum","u","whole_sum"),"split",lambda u:
            eliminate(u,field(u.hyp("split"),1,4),("tb","tc"),"tail",chosen)))


def _prefix_below(s):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    def chosen(t):
        N,out,full,a,r=t.terms(("N","s","t","last","previous"));data=t.hyp("decomposition")
        same=apply(specialize(t,"sum_unique",*t.terms(A),N,r,out),field(data,1,3),t.hyp("short"))
        return witness((a,),_chain(specialize(t,"add_comm",a,out),CongAdd(EqSym(same),EqRefl(a)),EqSym(field(data,2,3))))
    return introduce(s,A+("N","s","t"),("short","whole"),lambda t:
        eliminate(t,apply(specialize(t,"sum_decompose",*t.terms(A+("N","t"))),t.hyp("whole")),("last","previous"),"decomposition",chosen))


def _tail_graphs(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    one=Succ(Zero())
    def pointwise(t,upper):
        i,a,b,c=t.terms(("i","a","b","c"))
        index=_chain(CongAdd(EqRefl(one),specialize(t,"one_mul",i)),_one_plus(t,i))
        entry_a=apply(specialize(t,"slice_a",i,a),t.hyp("bound"),t.hyp("tail_a_entry"))
        entry_a=_subst(t,registry,"BetaAt(ab,ac,slot,a)",index,entry_a)
        entry_b=apply(specialize(t,"slice_b",i,c),t.hyp("bound"),t.hyp("tail_b_entry"))
        entry_b=_subst(t,registry,"BetaAt(bb,bc,slot,c)",index,entry_b)
        rows=apply(specialize(t,"term_difference",*t.terms(FIXED)),*(t.hyp(label) for label in
            ("nonzero","gap","recurrence_a","recurrence_b","head_a","head_b")))
        bounds=apply(instantiate(rows,i,a,c,b),t.hyp("bound"),entry_a,entry_b,t.hyp("previous_b"))
        if upper:
            return AndElimR(bounds)
        lower=_subst(t,registry,"Le(slot,c)",EqSym(specialize(t,"one_mul",a)),AndElimL(bounds))
        right=_chain(EqSym(instantiate(Axiom("PA3"),c)),CongAdd(EqSym(specialize(t,"one_mul",c)),EqSym(specialize(t,"zero_mul",b))))
        return _subst(t,registry,"Le(1*a,slot)",right,lower)
    def finish(t):
        upper=introduce(t,("i","a","b","c"),("bound","tail_a_entry","previous_b","tail_b_entry"),lambda u:pointwise(u,True))
        lower=introduce(t,("i","c","b","a"),("bound","tail_b_entry","previous_b","tail_a_entry"),lambda u:pointwise(u,False))
        return conjunction(upper,lower)
    return introduce(s,FIXED+TA+TB,("nonzero","gap","recurrence_a","recurrence_b","head_a","head_b","slice_a","slice_b"),finish)


def _finish_bound(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    nine=Zero()
    for _ in range(9):
        nine=Succ(nine)
    def finish(t):
        d,g,a0,out,full,u,v,w=t.terms(("d","g","a0","s","t","u","v","w"))
        lower=apply(specialize(t,"add_left_mono",u,v,a0),t.hyp("tail_monotone"))
        lower=_subst(t,registry,"Le(slot,a0+v)",EqSym(t.hyp("split_a")),lower)
        lower=_subst(t,registry,"Le(s,slot)",EqSym(t.hyp("split_b")),lower)
        da0,du,dv,gw=Mul(d,a0),Mul(d,u),Mul(d,v),Mul(g,w)
        upper=apply(specialize(t,"add_left_mono",dv,Add(du,gw),da0),t.hyp("tail_difference"))
        left=_chain(CongMul(EqRefl(d),t.hyp("split_b")),specialize(t,"mul_add",d,a0,v))
        upper=_subst(t,registry,"Le(slot,d*a0+(d*u+g*w))",EqSym(left),upper)
        right=_chain(EqSym(specialize(t,"add_assoc",da0,du,gw)),CongAdd(EqSym(specialize(t,"mul_add",d,a0,u)),EqRefl(gw)),
            CongAdd(CongMul(EqRefl(d),EqSym(t.hyp("split_a"))),EqRefl(gw)))
        upper=_subst(t,registry,"Le(d*t,slot)",right,upper)
        remainder=apply(specialize(t,"mul_left_mono",w,Mul(nine,a0),g),t.hyp("majorant"))
        remainder=_subst(t,registry,"Le(g*w,slot)",_multiplicative_equal(t,Mul(g,Mul(nine,a0)),Mul(nine,Mul(g,a0))),remainder)
        remainder=apply(specialize(t,"add_left_mono",gw,Mul(nine,Mul(g,a0)),Mul(d,out)),remainder)
        return conjunction(lower,apply(specialize(t,"le_trans",Mul(d,full),Add(Mul(d,out),gw),Add(Mul(d,out),Mul(nine,Mul(g,a0)))),upper,remainder))
    return introduce(s,("d","g","a0","s","t","u","v","w"),("split_a","split_b","tail_monotone","tail_difference","majorant"),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl
    from peano_lab.kernel.terms import Succ,Zero
    one=Succ(Zero())
    def chosen(t):
        d,g,N,a0,out,full,u,v,w=t.terms(("d","g","N","a0","s","t","u","v","w"))
        tail_a,tail_b=t.hyp("tail_a"),t.hyp("tail_b")
        graphs=apply(specialize(t,"tail_graphs",*t.terms(FIXED+TA+TB)),*(t.hyp(label) for label in
            ("nonzero","gap","recurrence_a","recurrence_b","head_a","head_b")),field(tail_a,0,3),field(tail_b,0,3))
        lower=apply(specialize(t,"sum_bound",one,Zero(),one,*t.terms(TB+B+TA),N,v,w,u),
            field(graphs,1,2),field(tail_b,1,3),t.hyp("prefix_sum"),field(tail_a,1,3))
        lower=_subst(t,registry,"Le(slot,1*v+0*w)",specialize(t,"one_mul",u),lower)
        simplify=_chain(CongAdd(specialize(t,"one_mul",v),specialize(t,"zero_mul",w)),instantiate(Axiom("PA3"),v))
        lower=_subst(t,registry,"Le(u,slot)",simplify,lower)
        upper=apply(specialize(t,"sum_bound",d,g,d,*t.terms(TA+B+TB),N,u,w,v),
            field(graphs,0,2),field(tail_a,1,3),t.hyp("prefix_sum"),field(tail_b,1,3))
        below=apply(specialize(t,"prefix_below",*t.terms(B),N,w,full),t.hyp("prefix_sum"),t.hyp("sum_b"))
        majorant=apply(specialize(t,"exp_majorant",*t.terms(("d","y","N")+B+("a0","t"))),
            t.hyp("nonzero"),t.hyp("argument_bound"),t.hyp("recurrence_b"),t.hyp("head_b"),t.hyp("sum_b"))
        from peano_lab.kernel.terms import Mul
        nine=Zero()
        for _ in range(9):
            nine=Succ(nine)
        bound=apply(specialize(t,"le_trans",w,full,Mul(nine,a0)),below,majorant)
        return apply(specialize(t,"finish_bound",d,g,a0,out,full,u,v,w),field(tail_a,2,3),field(tail_b,2,3),lower,upper,bound)
    return introduce(s,PARAMETERS,("nonzero","gap","recurrence_a","recurrence_b","head_a","head_b","argument_bound","sum_a","sum_b"),lambda t:
        eliminate(t,apply(specialize(t,"split_head",*t.terms(A+("N","a0","s"))),t.hyp("head_a"),t.hyp("sum_a")),TA+("u",),"tail_a",lambda u:
            eliminate(u,apply(specialize(u,"split_head",*u.terms(B+("N","a0","t"))),u.hyp("head_b"),u.hyp("sum_b")),TB+("v",),"tail_b",lambda v:
                eliminate(v,specialize(v,"sum_exists",*v.terms(B+("N",))),("w",),"prefix_sum",chosen))))


def prove_exp_sum_continuity(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV096",target=frozen_exp_sum_continuity_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"split_head":lambda s:_split_head(s,registry),"prefix_below":_prefix_below,
            "tail_graphs":lambda s:_tail_graphs(s,registry),"finish_bound":lambda s:_finish_bound(s,registry),"CV096":lambda s:_root(s,registry)},
        pins=exp_sum_continuity_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
