"""CV071: actual finite exp(x/d) terms have sum at most nine times the scale.

Retain every CV070 witness and normalization clause, and add s<=9*w0 when
d!=0 and x<=2*d. A supplied-prefix surplus induction proves the bound;
the order cancellation explicitly retains the nonzero-denominator guard.
"""
from hashlib import sha256

from sqrt2_power_scaled_exp_terms import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,scaled_exp_terms_source_pins,
    NAMED_SOURCE as CONSTRUCTED_SOURCE,OUTPUTS,WEIGHTS,TERMS,RECURRENCE,NORMALIZATION,
    COMPOSITION_ARCHIVE,
)
from sqrt2_power_composition_recurrence import RECURRENCE_ARCHIVE
from sqrt2_power_horner_tail_majorant import COMPARISON_ARCHIVE
from sqrt2_power_ratio_sum_bound import COMM_ARCHIVE,ENDPOINT_SOURCES as SUM_ENDPOINTS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain,_additive_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-scaled-exp-bound-v1"
T = ("tb","tc")
FIXED = ("d","x","N")+T+("a0",)
PREMISES = ("~d=0","Le(x,2*d)",RECURRENCE,"BetaAt(tb,tc,0,a0)")
FIELDS = (WEIGHTS,TERMS,"BetaAt(wb,wc,0,w0)","BetaAt(tb,tc,0,w0)","~w0=0",
    "Factorial(N,f)","Pow(d,N,p)","w0=f*p","Sum(tb,tc,S N,s)",RECURRENCE,"("+NORMALIZATION+")","Le(s,9*w0)")


def joined(fields):
    result = fields[-1]
    for f in reversed(fields[:-1]):
        result = f+" /\\ ("+result+")"
    return result


NAMED_SOURCE = "forall d x N. ~d=0 -> Le(x,2*d) -> exists "+" ".join(OUTPUTS)+". "+joined(FIELDS)
TARGET_SHA256 = "042906aaf5e07838dfb7be22391a4c26d6395af6e8d451e8c4322563fb810e26"
PREFIX_BOUND = "forall k y z. Le(S(S(S k)),S N) -> Sum(tb,tc,S(S(S k)),y) -> BetaAt(tb,tc,S(S k),z) -> Le(y+2*z,9*a0)"
HELPER_SOURCES = {
    "mul_le_cancel":"forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)",
    "ratio":"forall d x j a b h. ~d=0 -> Le(x,2*d) -> Le(h,S j) -> ((S j)*d)*b=x*a -> Le(h*b,2*a)",
    "first":"forall d x a b. ~d=0 -> Le(x,2*d) -> (1*d)*b=x*a -> Le(b,2*a)",
    "first_two":"forall d x a b c. ~d=0 -> Le(x,2*d) -> (1*d)*b=x*a -> (2*d)*c=x*b -> Le(b,2*a) /\\ Le(c,2*a)",
    "nine":"forall a. (a+2*a)+3*(2*a)=9*a",
    "three_bound":"forall a b c s. Le(b,2*a) -> Le(c,2*a) -> s=(a+b)+c -> Le(s+2*c,9*a)",
    "short_bound":"forall a b s. Le(b,2*a) -> s=a+b -> Le(s,9*a)",
    "sum_two":"forall tb tc s a b. Sum(tb,tc,2,s) -> BetaAt(tb,tc,0,a) -> BetaAt(tb,tc,1,b) -> s=a+b",
    "sum_three":"forall tb tc s a b c. Sum(tb,tc,3,s) -> BetaAt(tb,tc,0,a) -> BetaAt(tb,tc,1,b) -> BetaAt(tb,tc,2,c) -> s=(a+b)+c",
    "prefix_bound":"forall "+" ".join(FIXED)+". "+" -> ".join(PREMISES+(PREFIX_BOUND,)),
    "all_values":"forall "+" ".join(FIXED+("s",))+". "+" -> ".join(PREMISES+("Sum(tb,tc,S N,s)","Le(s,9*a0)")),
}
HELPER_TARGET_SHA256 = {
    "mul_le_cancel":"3733b4b496a8a5f223780704194a0b2d772fb6564b9524425101c04d073aae18",
    "ratio":"49c4e9b3f1e0ccbc691d61dd4a0ca65cc4bb96fe733820261e39cddefda60d70",
    "first":"089311edd98c3b1ff3190976c583053a86a3244819eeae78896fd755cda69a62",
    "first_two":"040173fdf39cbb5a15d727a4398369c0b9011db01abb4f9316c331c7fda1a9b5",
    "nine":"dd65003522184505c390cae2d48b54dbcaf516b3b83cc253f055dcceeec87937",
    "three_bound":"6fd4e54263885f6610b0863671eaa6535f3addef69ec8554c34116004cc487fe",
    "short_bound":"7494215dd3ae0acb8ec2b04cc77ec75da86900fc7f67d106de3d9c5fb0f4bcbe",
    "sum_two":"85709ef8132bd25cd46f0bf3a641be5106542e2503a0238cc7fb48ba3f456d0a",
    "sum_three":"584fad37584a1ace43b78be63acb590e94e091363c74ce8a9b932252a019ed73",
    "prefix_bound":"2d78e7f20cfc23cec687e4cc8f626f8eb4aabf85ac6c8e3d1cb68b2f43a0f86d",
    "all_values":"a6d338f6a52bf6824f863abfd7e665a736588f701e2cebc885f3b31089fba2d7",
}
EXP_ARCHIVE = dict(case="CV070",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-scaled-exp-terms-v1/generation-process.json.gz",
    bytes=35768,sha256="ed605e26ac83f0ab130bf0406a80b7b1820db38b247ff86916bfcdb624f593d5",
    raw_bytes=668363,raw_sha256="2ed87385d786381359414f03049c26cf71327e987e60a3137683883a7b2370e4",
    bundle_bytes=381155,bundle_sha256="2be0d10e36a67786ed5fd20800f6a2d52c10229fea219ea68edd70e832a8b075",
    nodes=144,root=143,target_ast_sha256="7f9e9c6aa4b255463768b661ebe9736b133dd810525dfd27ff94dfbe3693bf1d")
ARCHIVES = (EXP_ARCHIVE,COMPOSITION_ARCHIVE,RECURRENCE_ARCHIVE,COMPARISON_ARCHIVE,COMM_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:SUM_ENDPOINTS[name] for name in ("sum_one","sum_decompose","beta_exists","beta_unique","mul_succ_left","add_comm","add_assoc","add_left_mono","le_refl","le_succ","le_trans","zero_le","zero_or_succ")},
    "constructed":CONSTRUCTED_SOURCE,
    "factor_difference":"forall c u v r. c*u=c*v+r -> exists w. r=c*w",
    "mul_cancel":"forall a b c. ~a=0 -> a*b=a*c -> b=c",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "one_mul":"forall a. 1*a=a","mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "mul_comm":"forall a b. a*b=b*a","succ_ne_zero":"forall a. ~S a=0",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "add_right_mono":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(constructed="CV070",mul_cancel="CV002",mul_left_mono="CV063",sum_one="CV010")
HELPER_DEPENDENCIES = {
    "mul_le_cancel":("factor_difference","mul_cancel","add_comm","mul_add"),
    "ratio":("mul_right_mono","le_trans","mul_assoc","mul_comm","mul_le_cancel"),
    "first":("ratio","le_refl","one_mul"),
    "first_two":("first","ratio","le_refl","mul_le_cancel","succ_ne_zero","le_trans"),
    "nine":("mul_succ_left","one_mul","add_assoc","add_comm"),
    "three_bound":("add_left_mono","add_right_mono","mul_left_mono","le_trans","nine","mul_succ_left","add_assoc","add_comm"),
    "short_bound":("add_left_mono","le_trans","nine","add_comm"),
    "sum_two":("sum_decompose","sum_one","beta_unique"),
    "sum_three":("sum_decompose","sum_two","beta_unique"),
    "prefix_bound":("beta_exists","beta_unique","sum_three","first_two","ratio","three_bound","le_of_succ_le_succ","le_refl","le_succ","le_trans","sum_decompose","add_left_mono","add_assoc","add_comm","mul_succ_left"),
    "all_values":("zero_or_succ","sum_one","sum_two","beta_exists","first","short_bound","zero_le","le_refl","prefix_bound","le_trans","add_comm"),
    "CV071":("constructed","all_values"),
}


class ScaledExpBoundError(ValueError):
    """Changed actual computation, denominator guard or finite sum bound."""


def _n(value):
    from peano_lab.kernel.terms import Succ,Zero
    if type(value) is not int or not 0<=value<=9:
        raise ScaledExpBoundError("small numeral reconstruction bound exceeded")
    result = Zero()
    for _ in range(value):
        result = Succ(result)
    return result


def frozen_scaled_exp_bound_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=3 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ScaledExpBoundError("CV071 exact constructed finite exponential bound changed")
    return target


def source_contract():
    return dict(code="CV071",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,nonzero_denominator_required=True,argument_bound_required="x<=2*d",
        all_CV070_computation_and_normalization_data_retained=True,finite_sum_bound="s<=9*w0",
        supplied_actual_recurrence_and_sum_helper=True,zero_argument_and_zero_horizon_allowed=True,
        zero_and_one_horizons_handled_separately=True,new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",rational_division_transport_claimed=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def scaled_exp_bound_source_pins():
    result = scaled_exp_terms_source_pins()
    expected = {"scripts/sqrt2_power_scaled_exp_terms.py":"329c4e741b144823db7d43c018756dd19033aa5beca1505b5f4d05ae7cbe316a",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_scaled_exp_bound.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ScaledExpBoundError("finite exp bound source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _mul_le_cancel(s):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def gap(t):
        c,a,b,g = t.terms(("c","a","b","g"))
        eq = _chain(EqSym(t.hyp("gap")),specialize(t,"add_comm",g,Mul(c,a)))
        def factor(u):
            c,a,b,w = u.terms(("c","a","b","w"))
            eq = _chain(specialize(u,"mul_add",c,w,a),CongAdd(EqSym(u.hyp("factor")),EqRefl(Mul(c,a))),u.hyp("gap"))
            return witness((w,),apply(specialize(u,"mul_cancel",c,Add(w,a),b),u.hyp("nonzero"),eq))
        return eliminate(t,apply(specialize(t,"factor_difference",c,b,a,g),eq),("w",),"factor",factor)
    return introduce(s,("c","a","b"),("nonzero","bound"),lambda t:eliminate(t,t.hyp("bound"),("g",),"gap",gap))


def _ratio(s,registry):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        d,x,j,a,b,h = t.terms(("d","x","j","a","b","h"));two = _n(2)
        lower = apply(specialize(t,"mul_right_mono",h,Succ(j),d),t.hyp("index"))
        lower = apply(specialize(t,"mul_right_mono",Mul(h,d),Mul(Succ(j),d),b),lower)
        lower = _subst(t,registry,"Le((h*d)*b,slot)",t.hyp("recurrence"),lower)
        upper = apply(specialize(t,"mul_right_mono",x,Mul(two,d),a),t.hyp("argument"))
        bound = apply(specialize(t,"le_trans",Mul(Mul(h,d),b),Mul(x,a),Mul(Mul(two,d),a)),lower,upper)
        bound = _subst(t,registry,"Le(slot,(2*d)*a)",_multiplicative_equal(t,Mul(Mul(h,d),b),Mul(d,Mul(h,b))),bound)
        bound = _subst(t,registry,"Le(d*(h*b),slot)",_multiplicative_equal(t,Mul(Mul(two,d),a),Mul(d,Mul(two,a))),bound)
        return apply(specialize(t,"mul_le_cancel",d,Mul(h,b),Mul(two,a)),t.hyp("nonzero"),bound)
    return introduce(s,("d","x","j","a","b","h"),("nonzero","argument","index","recurrence"),finish)


def _first(s,registry):
    def finish(t):
        bound = apply(specialize(t,"ratio",*t.terms(("d","x")),_n(0),*t.terms(("a","b")),_n(1)),
            t.hyp("nonzero"),t.hyp("argument"),specialize(t,"le_refl",_n(1)),t.hyp("recurrence"))
        return _subst(t,registry,"Le(slot,2*a)",specialize(t,"one_mul",t.term("b")),bound)
    return introduce(s,("d","x","a","b"),("nonzero","argument","recurrence"),finish)


def _first_two(s):
    from peano_lab.kernel.proofs import AndIntro
    from peano_lab.kernel.terms import Mul
    def finish(t):
        d,x,a,b,c = t.terms(("d","x","a","b","c"));two = _n(2)
        first = apply(specialize(t,"first",d,x,a,b),t.hyp("nonzero"),t.hyp("argument"),t.hyp("first_eq"))
        second = apply(specialize(t,"ratio",d,x,_n(1),b,c,two),t.hyp("nonzero"),t.hyp("argument"),specialize(t,"le_refl",two),t.hyp("second_eq"))
        second = apply(specialize(t,"mul_le_cancel",two,c,b),specialize(t,"succ_ne_zero",_n(1)),second)
        return AndIntro(first,apply(specialize(t,"le_trans",c,b,Mul(two,a)),second,first))
    return introduce(s,("d","x","a","b","c"),("nonzero","argument","first_eq","second_eq"),finish)


def _nine(s):
    """Unroll only positive literal factors <=9, then ordinary additive AC."""
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        def unroll(n,v):
            if n==1:
                return v,specialize(t,"one_mul",v)
            previous,proof = unroll(n-1,v)
            return Add(previous,v),_chain(specialize(t,"mul_succ_left",_n(n-1),v),CongAdd(proof,EqRefl(v)))
        def expand(term):
            if type(term) is Add:
                a,p = expand(term.left);b,q = expand(term.right)
                return Add(a,b),CongAdd(p,q)
            if type(term) is Mul:
                n,current = 0,term.left
                while type(current) is Succ and n<10:
                    n,current = n+1,current.term
                if type(current) is Zero and 1<=n<=9:
                    v,p = expand(term.right);out,q = unroll(n,v)
                    return out,_chain(CongMul(EqRefl(term.left),p),q)
            return term,EqRefl(term)
        a = t.term("a")
        left = Add(Add(a,Mul(_n(2),a)),Mul(_n(3),Mul(_n(2),a)))
        right = Mul(_n(9),a)
        le,lp = expand(left);re,rp = expand(right)
        return _chain(lp,_additive_equal(t,le,re),EqSym(rp))
    return introduce(s,("a",),(),finish)


def _three_bound(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        a,b,c,total = t.terms(("a","b","c","s"));two,three = _n(2),_n(3)
        first = apply(specialize(t,"add_left_mono",b,Mul(two,a),a),t.hyp("first"))
        first = apply(specialize(t,"add_right_mono",Add(a,b),Add(a,Mul(two,a)),Mul(three,c)),first)
        second = apply(specialize(t,"mul_left_mono",c,Mul(two,a),three),t.hyp("second"))
        second = apply(specialize(t,"add_left_mono",Mul(three,c),Mul(three,Mul(two,a)),Add(a,Mul(two,a))),second)
        bound = apply(specialize(t,"le_trans",Add(Add(a,b),Mul(three,c)),Add(Add(a,Mul(two,a)),Mul(three,c)),Add(Add(a,Mul(two,a)),Mul(three,Mul(two,a)))),first,second)
        bound = _subst(t,registry,"Le((a+b)+3*c,slot)",specialize(t,"nine",a),bound)
        left = _chain(CongAdd(t.hyp("sum_eq"),EqRefl(Mul(two,c))),specialize(t,"add_assoc",Add(a,b),c,Mul(two,c)),
            CongAdd(EqRefl(Add(a,b)),specialize(t,"add_comm",c,Mul(two,c))),CongAdd(EqRefl(Add(a,b)),EqSym(specialize(t,"mul_succ_left",two,c))))
        return _subst(t,registry,"Le(slot,9*a)",EqSym(left),bound)
    return introduce(s,("a","b","c","s"),("first","second","sum_eq"),finish)


def _short_bound(s,registry):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        a,b,total = t.terms(("a","b","s"));upper = Add(a,Mul(_n(2),a));gap = Mul(_n(3),Mul(_n(2),a))
        bound = apply(specialize(t,"add_left_mono",b,Mul(_n(2),a),a),t.hyp("first"))
        bound = _subst(t,registry,"Le(slot,a+2*a)",EqSym(t.hyp("sum_eq")),bound)
        large = witness((gap,),_chain(specialize(t,"add_comm",gap,upper),specialize(t,"nine",a)))
        return apply(specialize(t,"le_trans",total,upper,Mul(_n(9),a)),bound,large)
    return introduce(s,("a","b","s"),("first","sum_eq"),finish)


def _sum_two(s):
    from peano_lab.kernel.proofs import CongAdd
    def chosen(t):
        data = t.hyp("data")
        first = apply(specialize(t,"sum_one",*t.terms(T+("u","a"))),field(data,1,3),t.hyp("head"))
        second = apply(specialize(t,"beta_unique",*t.terms(T),_n(1),*t.terms(("v","b"))),field(data,0,3),t.hyp("next"))
        return _chain(field(data,2,3),CongAdd(first,second))
    return introduce(s,T+("s","a","b"),("sum","head","next"),lambda t:
        eliminate(t,apply(specialize(t,"sum_decompose",*t.terms(T),_n(1),t.term("s")),t.hyp("sum")),("v","u"),"data",chosen))


def _sum_three(s):
    from peano_lab.kernel.proofs import CongAdd
    def chosen(t):
        data = t.hyp("data")
        first = apply(specialize(t,"sum_two",*t.terms(T+("u","a","b"))),field(data,1,3),t.hyp("head"),t.hyp("next"))
        last = apply(specialize(t,"beta_unique",*t.terms(T),_n(2),*t.terms(("v","c"))),field(data,0,3),t.hyp("last"))
        return _chain(field(data,2,3),CongAdd(first,last))
    return introduce(s,T+("s","a","b","c"),("sum","head","next","last"),lambda t:
        eliminate(t,apply(specialize(t,"sum_decompose",*t.terms(T),_n(2),t.term("s")),t.hyp("sum")),("v","u"),"data",chosen))


def _prefix_bound(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongMul,CongS,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ
    def base(t):
        def chosen(u):
            N,a0,b,z,y = u.terms(("N","a0","b","z","y"))
            second_index = apply(specialize(u,"le_of_succ_le_succ",_n(2),N),u.hyp("bound"))
            first_index = apply(specialize(u,"le_trans",_n(1),_n(2),N),
                apply(specialize(u,"le_succ",_n(1),_n(1)),specialize(u,"le_refl",_n(1))),second_index)
            first_eq = apply(specialize(u,"recurrence",_n(0),a0,b),first_index,u.hyp("head"),u.hyp("middle"))
            second_eq = apply(specialize(u,"recurrence",_n(1),b,z),second_index,u.hyp("middle"),u.hyp("last"))
            bounds = apply(specialize(u,"first_two",*u.terms(("d","x","a0","b","z"))),u.hyp("nonzero"),u.hyp("argument"),first_eq,second_eq)
            sum_eq = apply(specialize(u,"sum_three",*u.terms(T+("y","a0","b","z"))),u.hyp("sum"),u.hyp("head"),u.hyp("middle"),u.hyp("last"))
            return apply(specialize(u,"three_bound",a0,b,z,y),AndElimL(bounds),AndElimR(bounds),sum_eq)
        return eliminate(t,specialize(t,"beta_exists",*t.terms(T),_n(1)),("b",),"middle",chosen)
    def successor(t):
        def chosen(u):
            k,N,y,z,a0,b,c,old_sum = u.terms(("k","N","y","z","a0","b","c","u"))
            j = Succ(Succ(k));last_index = Succ(j);whole = Succ(N);two = _n(2)
            data = u.hyp("sum_data")
            earlier = apply(specialize(u,"le_trans",last_index,Succ(last_index),whole),
                apply(specialize(u,"le_succ",last_index,last_index),specialize(u,"le_refl",last_index)),u.hyp("bound"))
            old = apply(specialize(u,"IH",old_sum,c),earlier,field(data,1,3),u.hyp("previous"))
            source_index = apply(specialize(u,"le_of_succ_le_succ",last_index,N),u.hyp("bound"))
            source_eq = apply(specialize(u,"recurrence",j,c,b),source_index,u.hyp("previous"),field(data,0,3))
            gap = _chain(instantiate(Axiom("PA4"),k,_n(2)),CongS(instantiate(Axiom("PA4"),k,_n(1))),
                CongS(CongS(instantiate(Axiom("PA4"),k,_n(0)))),CongS(CongS(CongS(instantiate(Axiom("PA3"),k)))))
            ratio = apply(specialize(u,"ratio",*u.terms(("d","x")),j,c,b,_n(3)),u.hyp("nonzero"),u.hyp("argument"),witness((k,),gap),source_eq)
            lifted = apply(specialize(u,"add_left_mono",Mul(_n(3),b),Mul(two,c),old_sum),ratio)
            bz = apply(specialize(u,"beta_unique",*u.terms(T),last_index,b,z),field(data,0,3),u.hyp("last"))
            left = _chain(CongAdd(field(data,2,3),CongMul(EqRefl(two),EqSym(bz))),
                specialize(u,"add_assoc",old_sum,b,Mul(two,b)),CongAdd(EqRefl(old_sum),specialize(u,"add_comm",b,Mul(two,b))),
                CongAdd(EqRefl(old_sum),EqSym(specialize(u,"mul_succ_left",two,b))))
            lifted = _subst(u,registry,"Le(slot,u+2*c)",EqSym(left),lifted)
            return apply(specialize(u,"le_trans",Add(y,Mul(two,z)),Add(old_sum,Mul(two,c)),Mul(_n(9),a0)),lifted,old)
        index = Succ(Succ(Succ(t.term("k"))))
        return eliminate(t,apply(specialize(t,"sum_decompose",*t.terms(T),index,t.term("y")),t.hyp("sum")),("b","u"),"sum_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(T),Succ(Succ(u.term("k")))),("c",),"previous",chosen))
    motive = target
    for _ in FIXED:
        motive = motive.body
    for _ in PREMISES:
        motive = motive.right
    motive = motive.body
    row_params,row_hyps = ("y","z"),("bound","sum","last")
    return introduce(s,FIXED,("nonzero","argument","recurrence","head"),lambda t:
        Ind(motive,introduce(t,row_params,row_hyps,base),
            introduce(t,("k",),("IH",),lambda u:introduce(u,row_params,row_hyps,successor))))


def _all_values(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongS,EqSym,OrElim
    from peano_lab.kernel.terms import Add,Mul,Succ
    def zero(t):
        empty = _subst(t,registry,"Sum(tb,tc,slot,s)",CongS(t.hyp("zero")),t.hyp("sum"))
        sa = apply(specialize(t,"sum_one",*t.terms(T+("s","a0"))),empty,t.hyp("head"))
        eq = _chain(sa,EqSym(instantiate(Axiom("PA3"),t.term("a0"))))
        return apply(specialize(t,"short_bound",t.term("a0"),_n(0),t.term("s")),specialize(t,"zero_le",Mul(_n(2),t.term("a0"))),eq)
    def successor(t):
        def decoded(u):
            def one(v):
                def chosen(w):
                    N,a0,b,total = w.terms(("N","a0","b","s"))
                    N1 = _chain(w.hyp("index"),CongS(w.hyp("one")))
                    bound = _subst(w,registry,"Le(1,slot)",EqSym(N1),specialize(w,"le_refl",_n(1)))
                    recurrence = apply(specialize(w,"recurrence",_n(0),a0,b),bound,w.hyp("head"),w.hyp("middle"))
                    first = apply(specialize(w,"first",*w.terms(("d","x","a0","b"))),w.hyp("nonzero"),w.hyp("argument"),recurrence)
                    sum_two = _subst(w,registry,"Sum(tb,tc,slot,s)",CongS(N1),w.hyp("sum"))
                    eq = apply(specialize(w,"sum_two",*w.terms(T+("s","a0","b"))),sum_two,w.hyp("head"),w.hyp("middle"))
                    return apply(specialize(w,"short_bound",a0,b,total),first,eq)
                return eliminate(v,specialize(v,"beta_exists",*v.terms(T),_n(1)),("b",),"middle",chosen)
            def more(v):
                def index(w):
                    def chosen(z):
                        k,total,last,a0 = z.terms(("k","s","z","a0"));two = _n(2)
                        Nss = _chain(z.hyp("index"),CongS(z.hyp("second_index")))
                        length = Succ(Succ(Succ(k)))
                        bound = _subst(z,registry,"Le(S(S(S k)),slot)",EqSym(CongS(Nss)),specialize(z,"le_refl",length))
                        partial = _subst(z,registry,"Sum(tb,tc,slot,s)",CongS(Nss),z.hyp("sum"))
                        invariant = apply(specialize(z,"prefix_bound",*z.terms(FIXED)),z.hyp("nonzero"),z.hyp("argument"),z.hyp("recurrence"),z.hyp("head"))
                        strong = apply(instantiate(invariant,k,total,last),bound,partial,z.hyp("last"))
                        weaker = witness((Mul(two,last),),specialize(z,"add_comm",Mul(two,last),total))
                        return apply(specialize(z,"le_trans",total,Add(total,Mul(two,last)),Mul(_n(9),a0)),weaker,strong)
                    return eliminate(w,specialize(w,"beta_exists",*w.terms(T),Succ(Succ(w.term("k")))),("z",),"last",chosen)
                return eliminate(v,v.hyp("more"),("k",),"second_index",index)
            return OrElim(specialize(u,"zero_or_succ",u.term("m")),one(u.hypothesis("one")),more(u.hypothesis("more")))
        return eliminate(t,t.hyp("successor"),("m",),"index",decoded)
    return introduce(s,FIXED+("s",),("nonzero","argument","recurrence","head","sum"),lambda t:
        OrElim(specialize(t,"zero_or_succ",t.term("N")),zero(t.hypothesis("zero")),successor(t.hypothesis("successor"))))


def _root(s):
    def chosen(t):
        data = t.hyp("data")
        bound = apply(specialize(t,"all_values",*t.terms(("d","x","N")+T+("w0","s"))),
            t.hyp("nonzero"),t.hyp("argument"),field(data,9,11),field(data,3,11),field(data,8,11))
        return witness(t.terms(OUTPUTS),conjunction(*(field(data,j,11) for j in range(11)),bound))
    return introduce(s,("d","x","N"),("nonzero","argument"),lambda t:
        eliminate(t,apply(specialize(t,"constructed",*t.terms(("d","x","N"))),t.hyp("nonzero")),OUTPUTS,"data",chosen))


def prove_scaled_exp_bound(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV071",target=frozen_scaled_exp_bound_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"mul_le_cancel":_mul_le_cancel,"ratio":lambda s:_ratio(s,registry),"first":lambda s:_first(s,registry),
            "first_two":_first_two,"nine":_nine,"three_bound":lambda s:_three_bound(s,registry),"short_bound":lambda s:_short_bound(s,registry),
            "sum_two":_sum_two,"sum_three":_sum_three,
            "prefix_bound":lambda s:_prefix_bound(s,parse_named(HELPER_SOURCES["prefix_bound"],registry=registry),registry),
            "all_values":lambda s:_all_values(s,registry),"CV071":_root},
        pins=scaled_exp_bound_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
