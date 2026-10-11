"""CV063: exact scaled comparison of a nonnegative polynomial at two bases.

For a<=b and length r+1 construct both Horner values x at b, y at a and
actual p=a^r, q=b^r, proving p<=q and p*x<=q*y. The exponent is r,
not r+1; no division or strict positivity is used in this finite theorem.
"""
from hashlib import sha256

from sqrt2_power_horner_splitting import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,horner_splitting_source_pins,
    COMPOSITION_ARCHIVE,ENDPOINT_SOURCES as SPLIT_ENDPOINTS,
)
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-horner-base-comparison-v1"
A,HB,HA = ("ab","ac"),("hbb","hbc"),("hab","hac")
PARAMETERS = A+("a","b","r")
OUTPUTS = ("p","q","x","y")
FIXED = A+("a","b","N")+HB+HA
TRACE_B = "NatScaledHornerTrace(ab,ac,b,N,hbb,hbc)"
TRACE_A = "NatScaledHornerTrace(ab,ac,a,N,hab,hac)"
ALL_PREFIXES = "forall k p q x y. Le(S k,N) -> Pow(a,k,p) -> Pow(b,k,q) -> BetaAt(hbb,hbc,S k,x) -> BetaAt(hab,hac,S k,y) -> Le(p,q) /\\ Le(p*x,q*y)"
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". Le(a,b) -> exists p q x y. NatHornerValue(ab,ac,b,S r,x) /\\ (NatHornerValue(ab,ac,a,S r,y) /\\ (Pow(a,r,p) /\\ (Pow(b,r,q) /\\ (Le(p,q) /\\ Le(p*x,q*y)))))"
TARGET_SHA256 = "9427a92cb26d4fcfea9d3160585b295d542e0c343f466f0326c7f8acbf25bbe0"
HELPER_SOURCES = {
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "step_bound":"forall a b p0 q0 x0 y0 c p q x y. Le(a,b) -> Le(p0,q0) -> Le(p0*x0,q0*y0) -> p=p0*a -> q=q0*b -> x=b*x0+c -> y=a*y0+c -> Le(p,q) /\\ Le(p*x,q*y)",
    "all_prefixes":"forall "+" ".join(FIXED)+". Le(a,b) -> "+TRACE_B+" -> "+TRACE_A+" -> "+ALL_PREFIXES,
}
HELPER_TARGET_SHA256 = {
    "mul_left_mono":"d44d1f3b82362ce90224643bbef4c2da500ea4d6a9c65ccfc5c28d1d9205dc5a",
    "step_bound":"3a4ba6141a79c3144048d696dfd62521478bde36ed8c2a3efe59c13fbe862f25",
    "all_prefixes":"db92991a39a407694f21c31e5ea8c4235df9074054f0f7c19ce02c80eb44948b",
}
ARCHIVES = (COMPOSITION_ARCHIVE,)
ENDPOINT_SOURCES = {
    **{name:SPLIT_ENDPOINTS[name] for name in ("beta_exists","le_refl","le_succ","le_trans","power_zero","power_step","power_exists","horner_exists","step_value","mul_comm","mul_assoc","mul_add")},
    "zero_add":"forall a. 0+a=a",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "add_right_mono":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {
    "mul_left_mono":("mul_right_mono","mul_comm"),
    "step_bound":("mul_left_mono","mul_right_mono","le_trans","add_right_mono","add_left_mono","mul_add","mul_assoc","mul_comm"),
    "all_prefixes":("power_zero","beta_exists","step_value","zero_add","le_refl","le_succ","le_trans","power_step","step_bound"),
    "CV063":("horner_exists","beta_exists","power_exists","all_prefixes","le_refl"),
}


class HornerBaseComparisonError(ValueError):
    """Changed base order, exact scaling exponent or actual computation."""


def frozen_horner_base_comparison_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerBaseComparisonError("CV063 exact scaled base comparison target changed")
    return target


def source_contract():
    return dict(code="CV063",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,base_order_required=True,actual_two_horner_values_and_powers_constructed=True,
        length="r+1",scaling_exponent="r",inequalities="p<=q and p*x<=q*y; p=a^r; q=b^r",
        zero_bases_allowed=True,no_division_or_nonzero_cancellation=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def horner_base_comparison_source_pins():
    result = horner_splitting_source_pins()
    expected = {"scripts/sqrt2_power_horner_splitting.py":"17d330dc31b9e7c6aca718bbce4c4cbbeab881783cb42118b3e0a76c322fe27a",
        "scripts/sqrt2_power_finite_power_evaluation.py":"6c7c7cab1eceb7d10dcfa678ffa9f7245e4a197d966ee3050d547cf5ff804fac",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_horner_base_comparison.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerBaseComparisonError("base comparison source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _mul_left_mono(s,registry):
    def finish(t):
        bound = apply(specialize(t,"mul_right_mono",*t.terms(("a","b","c"))),t.hyp("bound"))
        bound = _subst(t,registry,"Le(slot,b*c)",specialize(t,"mul_comm",*t.terms(("a","c"))),bound)
        return _subst(t,registry,"Le(c*a,slot)",specialize(t,"mul_comm",*t.terms(("b","c"))),bound)
    return introduce(s,("a","b","c"),("bound",),finish)


def _step_bound(s,registry):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndIntro,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        a,b,p0,q0,x0,y0,c,p,q,x,y = t.terms(("a","b","p0","q0","x0","y0","c","p","q","x","y"))
        pq = apply(specialize(t,"le_trans",Mul(p0,a),Mul(q0,a),Mul(q0,b)),
            apply(specialize(t,"mul_right_mono",p0,q0,a),t.hyp("power_bound")),
            apply(specialize(t,"mul_left_mono",a,b,q0),t.hyp("base_bound")))
        pq = _subst(t,registry,"Le(slot,q0*b)",EqSym(t.hyp("next_p")),pq)
        pq = _subst(t,registry,"Le(p,slot)",EqSym(t.hyp("next_q")),pq)
        ab,px0,qy0,pc,qc = Mul(a,b),Mul(p0,x0),Mul(q0,y0),Mul(p,c),Mul(q,c)
        first = apply(specialize(t,"mul_left_mono",px0,qy0,ab),t.hyp("value_bound"))
        second = apply(specialize(t,"mul_right_mono",p,q,c),pq)
        summed = apply(specialize(t,"le_trans",Add(Mul(ab,px0),pc),Add(Mul(ab,qy0),pc),Add(Mul(ab,qy0),qc)),
            apply(specialize(t,"add_right_mono",Mul(ab,px0),Mul(ab,qy0),pc),first),
            apply(specialize(t,"add_left_mono",pc,qc,Mul(ab,qy0)),second))
        left = _chain(CongMul(EqRefl(p),t.hyp("next_x")),specialize(t,"mul_add",p,Mul(b,x0),c),
            CongAdd(CongMul(t.hyp("next_p"),EqRefl(Mul(b,x0))),EqRefl(pc)),
            CongAdd(_multiplicative_equal(t,Mul(Mul(p0,a),Mul(b,x0)),Mul(ab,px0)),EqRefl(pc)))
        right = _chain(CongMul(EqRefl(q),t.hyp("next_y")),specialize(t,"mul_add",q,Mul(a,y0),c),
            CongAdd(CongMul(t.hyp("next_q"),EqRefl(Mul(a,y0))),EqRefl(qc)),
            CongAdd(_multiplicative_equal(t,Mul(Mul(q0,b),Mul(a,y0)),Mul(ab,qy0)),EqRefl(qc)))
        summed = _subst(t,registry,"Le(slot,(a*b)*(q0*y0)+q*c)",EqSym(left),summed)
        summed = _subst(t,registry,"Le(p*x,slot)",EqSym(right),summed)
        return AndIntro(pq,summed)
    return introduce(s,("a","b","p0","q0","x0","y0","c","p","q","x","y"),
        ("base_bound","power_bound","value_bound","next_p","next_q","next_x","next_y"),finish)


def _all_prefixes(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,AndIntro,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    row_params,row_hyps = ("p","q","x","y"),("bound","power_p","power_q","value_x","value_y")
    def base(t):
        def chosen(u):
            zero = Zero()
            def first(base,codes,label,out):
                step = apply(instantiate(AndElimR(u.hyp(label)),zero),u.hyp("bound"))
                eq = apply(specialize(u,"step_value",*u.terms(A+(base,)+codes),zero,zero,u.term("c"),u.term(out)),
                    step,AndElimL(u.hyp(label)),u.hyp("coefficient"),u.hyp("value_"+out))
                return _chain(eq,CongAdd(instantiate(Axiom("PA5"),u.term(base)),EqRefl(u.term("c"))),specialize(u,"zero_add",u.term("c")))
            xc,yc = first("b",HB,"trace_b","x"),first("a",HA,"trace_a","y")
            p1 = apply(specialize(u,"power_zero",u.term("a"),zero,u.term("p")),EqRefl(zero),u.hyp("power_p"))
            q1 = apply(specialize(u,"power_zero",u.term("b"),zero,u.term("q")),EqRefl(zero),u.hyp("power_q"))
            same = _chain(p1,EqSym(q1))
            order = _subst(u,registry,"Le(p,slot)",same,specialize(u,"le_refl",u.term("p")))
            equality = _chain(CongMul(p1,xc),EqSym(CongMul(q1,yc)))
            value_order = _subst(u,registry,"Le(p*x,slot)",equality,specialize(u,"le_refl",Mul(*u.terms(("p","x")))))
            return AndIntro(order,value_order)
        return eliminate(t,specialize(t,"beta_exists",*t.terms(A),Zero()),("c",),"coefficient",chosen)
    def successor(t):
        def chosen(u):
            k,N = u.terms(("k","N"));sk = Succ(k)
            earlier = apply(specialize(u,"le_trans",sk,Succ(sk),N),apply(specialize(u,"le_succ",sk,sk),specialize(u,"le_refl",sk)),u.hyp("bound"))
            old = apply(specialize(u,"IH",*u.terms(("p0","q0","x0","y0"))),earlier,
                AndElimL(u.hyp("data_p")),AndElimL(u.hyp("data_q")),u.hyp("old_x"),u.hyp("old_y"))
            def next_value(base,codes,label,old,out):
                step = apply(instantiate(AndElimR(u.hyp(label)),sk),u.hyp("bound"))
                return apply(specialize(u,"step_value",*u.terms(A+(base,)+codes),sk,u.term(old),u.term("c"),u.term(out)),
                    step,u.hyp("old_"+out),u.hyp("coefficient"),u.hyp("value_"+out))
            return apply(specialize(u,"step_bound",*u.terms(("a","b","p0","q0","x0","y0","c","p","q","x","y"))),
                u.hyp("base_order"),AndElimL(old),AndElimR(old),AndElimR(u.hyp("data_p")),AndElimR(u.hyp("data_q")),
                next_value("b",HB,"trace_b","x0","x"),next_value("a",HA,"trace_a","y0","y"))
        def power(u,base,out):
            return apply(specialize(u,"power_step",u.term(base),u.term("k"),Succ(u.term("k")),u.term(out)),EqRefl(Succ(u.term("k"))),u.hyp("power_"+out))
        return eliminate(t,power(t,"a","p"),("p0",),"data_p",lambda u:
            eliminate(u,power(u,"b","q"),("q0",),"data_q",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(HB),Succ(v.term("k"))),("x0",),"old_x",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(HA),Succ(w.term("k"))),("y0",),"old_y",lambda z:
                        eliminate(z,specialize(z,"beta_exists",*z.terms(A),Succ(z.term("k"))),("c",),"coefficient",chosen)))))
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.right.right.right.body
    return introduce(s,FIXED,("base_order","trace_b","trace_a"),lambda t:Ind(motive,introduce(t,row_params,row_hyps,base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,row_params,row_hyps,successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        length = Succ(t.term("r"))
        invariant = apply(specialize(t,"all_prefixes",*t.terms(A+("a","b")),length,*t.terms(HB+HA)),
            t.hyp("order"),AndElimL(t.hyp("horner_b")),AndElimL(t.hyp("horner_a")))
        bounds = apply(instantiate(invariant,*t.terms(("r","p","q","x","y"))),specialize(t,"le_refl",length),t.hyp("power_p"),t.hyp("power_q"),t.hyp("value_x"),t.hyp("value_y"))
        return witness(t.terms(OUTPUTS),conjunction(witness(t.terms(HB),AndIntro(AndElimL(t.hyp("horner_b")),t.hyp("value_x"))),
            witness(t.terms(HA),AndIntro(AndElimL(t.hyp("horner_a")),t.hyp("value_y"))),t.hyp("power_p"),t.hyp("power_q"),AndElimL(bounds),AndElimR(bounds)))
    return introduce(s,PARAMETERS,("order",),lambda t:
        eliminate(t,specialize(t,"horner_exists",*t.terms(A+("b",)),Succ(t.term("r"))),HB,"horner_b",lambda u:
            eliminate(u,specialize(u,"horner_exists",*u.terms(A+("a",)),Succ(u.term("r"))),HA,"horner_a",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(HB),Succ(v.term("r"))),("x",),"value_x",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(HA),Succ(w.term("r"))),("y",),"value_y",lambda z:
                        eliminate(z,specialize(z,"power_exists",*z.terms(("a","r"))),("p",),"power_p",lambda a:
                            eliminate(a,specialize(a,"power_exists",*a.terms(("b","r"))),("q",),"power_q",chosen)))))))


def prove_horner_base_comparison(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV063",target=frozen_horner_base_comparison_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"mul_left_mono":lambda s:_mul_left_mono(s,registry),"step_bound":lambda s:_step_bound(s,registry),
            "all_prefixes":lambda s:_all_prefixes(s,parse_named(HELPER_SOURCES["all_prefixes"],registry=registry),registry),"CV063":_root},
        pins=horner_base_comparison_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
