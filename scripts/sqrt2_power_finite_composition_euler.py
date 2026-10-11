"""CV021: the Euler chain rule for actually constructed finite compositions.

Construct EA, powers P, shifted outer weights d and both weighted traces Q,R.
Prove i*Q[N+1][i]=(EA*R[N])[i] below the common width. No infinite series,
rational denominator, exponential identity, or analytic interpretation enters.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_weighted_series_trace import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,weighted_series_trace_source_pins,
    definition_registry as weighted_registry,NAMED_SOURCE as WEIGHTED_SOURCE,
    CONVOLUTION_ARCHIVE,
)
from sqrt2_power_shifted_euler_prefix import (
    definition_registry as shifted_registry,shifted_euler_prefix_source_pins,
    NAMED_SOURCE as SHIFTED_SOURCE,
)
from sqrt2_power_series_power_euler import (
    definition_registry as power_registry,series_power_euler_source_pins,
    HELPER_SOURCES as POWER_EULER_HELPERS,
)
from sqrt2_power_series_power_trace import NAMED_SOURCE as POWER_SOURCE,HELPER_SOURCES as POWER_HELPERS
from sqrt2_power_euler_product import coefficient,HELPER_SOURCES as EULER_HELPERS
from sqrt2_power_convolution_linearity import HELPER_SOURCES as LINEAR_HELPERS
from sqrt2_power_convolution_associative import HELPER_SOURCES as ASSOC_HELPERS
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst,HELPER_SOURCES as UNIT_HELPERS

SCHEMA = "sqrt2-power-finite-composition-euler-v1"
A = ("ab","ac","L")
P = ("pb","pc","qb","qc")
D = ("db","dc")
EA = D+("L",)
WEIGHTS,DERIVED = ("wb","wc"),("yb","yc")
Q,R = ("tb","tc","vb","vc"),("rb","rc","sb","sc")
F,G = ("fb","fc"),("gb","gc")
FIXED = A+("H",)+P+D+WEIGHTS+DERIVED+Q+R
EULER = "NatEulerPrefix(ab,ac,db,dc,L)"


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def exists(names,source):
    return "exists "+" ".join(names)+". "+source


def row(codes,index,values):
    return "NatPowerRow("+",".join(codes+(index,)+values)+")"


def power(length):
    return "NatPowerTrace("+",".join(A+("H",)+P+(length,))+")"


def weighted(weights,acc,length):
    return "NatWeightedSeriesTrace("+",".join(("H",)+weights+P+acc+(length,))+")"


def shifted(length):
    return "NatShiftedEulerPrefix("+",".join(WEIGHTS+DERIVED+(length,))+")"


def graph(weight,source,current,output):
    return "NatLinearTriple("+",".join(("1",weight,"1")+current+source+output+("H",))+")"


INVARIANT = forall(F+G+("i","p","t"),row(Q,"S N",F)+" -> "+row(R,"N",G)+" -> Lt(i,H) -> BetaAt(fb,fc,i,p) -> "+coefficient(EA,G+("H",),"i","t")+" -> i*p=t")
NAMED_SOURCE = forall(A+("H",)+WEIGHTS+("N",),exists(D+P+DERIVED+Q+R,
    EULER+" /\\ ("+power("N")+" /\\ ("+shifted("N")+" /\\ ("+weighted(WEIGHTS,Q,"S N")+" /\\ ("+weighted(DERIVED,R,"N")+" /\\ ("+INVARIANT+")))))"))
TARGET_SHA256 = "b8aae36bc9df2d03bb7bd14cae145075883cbe46a5eb5d5881d71b46927b2a65"
STORAGE = ("H",)+WEIGHTS+P+Q
HELPER_SOURCES = {
    "weighted_zero":forall(STORAGE+("N","ub","uc"),weighted(WEIGHTS,Q,"N")+" -> "+row(Q,"0",("ub","uc"))+" -> NatZeroPrefix(ub,uc,H)"),
    "weighted_graph":forall(STORAGE+("N","k","ub","uc","eb","ec","fb","fc","w"),weighted(WEIGHTS,Q,"N")+" -> Lt(k,N) -> "+row(P,"k",("ub","uc"))+" -> "+row(Q,"k",("eb","ec"))+" -> "+row(Q,"S k",("fb","fc"))+" -> BetaAt(wb,wc,k,w) -> "+graph("w",("ub","uc"),("eb","ec"),("fb","fc"))),
    "zero_convolution":"forall ab ac L bb bc M i p. NatZeroPrefix(ab,ac,L) -> NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,p) -> p=0",
    "unit_euler_zero":"forall ub uc H i a. NatUnitPrefix(ub,uc,H) -> Lt(i,H) -> BetaAt(ub,uc,i,a) -> i*a=0",
    "weighted_value":"forall ab ac bb bc cb cc H w i a b c. NatLinearTriple(1,w,1,ab,ac,bb,bc,cb,cc,H) -> Lt(i,H) -> BetaAt(ab,ac,i,a) -> BetaAt(bb,bc,i,b) -> BetaAt(cb,cc,i,c) -> c=a+w*b",
    "multiply_zero":"forall i a w b p. p=a+w*b -> a=0 -> i*b=0 -> i*p=0",
    "multiply_weighted":"forall i a w b x y k p. p=a+w*b -> i*a=x -> i*b=(S k)*y -> i*p=x+((S k)*w)*y",
    "chain_rule":forall(FIXED,EULER+" -> "+forall(("k","N")+F+G+("i","p","t"),power("N")+" -> Le(k,N) -> "+shifted("N")+" -> "+weighted(WEIGHTS,Q,"S N")+" -> "+weighted(DERIVED,R,"N")+" -> "+row(Q,"S k",F)+" -> "+row(R,"k",G)+" -> Lt(i,H) -> BetaAt(fb,fc,i,p) -> "+coefficient(EA,G+("H",),"i","t")+" -> i*p=t")),
}
HELPER_TARGET_SHA256 = {
    "weighted_zero":"d77cb0a45f53f1e608f90f0e5979c22397a9363efd6163d6fbf5eb81d4b8cb5b",
    "weighted_graph":"03afc86d97f6344df4869ffdf33541e786118b183abd41eb9958890f8b2e732e",
    "zero_convolution":"8a0133c7eea77b41a58e9b852ecd6ef90f5f555facecea228821f2f75eb6f59d",
    "unit_euler_zero":"96c786ff4dbde2987bfd75d25db3e6d533f5873c0a9a604f14a6f66679a5d927",
    "weighted_value":"4017808189f7aa2c3c8b4118eba4098f0e9ae8fc4b88c0fe47fde2bd65b2545b",
    "multiply_zero":"8b08bf34a2afba7ed8273720ada9321c1ab7ce758015d0d8ee895dae55361dde",
    "multiply_weighted":"cebd5ed2070bd0c89b7579cb76ad6e0ee6f836228217a4ca3a69a52ebf76e2f1",
    "chain_rule":"fb97dc67658037f61c3623a3199c81833141d418256c563745ddea7b374216fc",
}
POWER_EULER_ARCHIVE = dict(case="CV017",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-series-power-euler-v1/generation-process.json.gz",
    bytes=48035,sha256="334d64508b95ebb9165feda1ac1b9fc065b328b663566829862b0bf9e67b3fbb",
    raw_bytes=1257925,raw_sha256="0fbbe2501b089a92178194c173d59e19dcdc4e9a58e9fe15ddc638c18c022c5a",
    bundle_bytes=768657,bundle_sha256="d94cbf0c9fb9f42a645258b60f5d7ba325f8ec20a54a983922da9b13c990f208",
    nodes=193,root=192,target_ast_sha256="e71ae746c83206309479f65ede0e10c2e11d077b3ac2123df4942475e453d1e6")
WEIGHTED_ARCHIVE = dict(case="CV019",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-weighted-series-trace-v1/generation-process.json.gz",
    bytes=21210,sha256="207e714825825b43014daf2fb79ec5c6d757925d36e8afae10b3cdf791db1f8b",
    raw_bytes=333624,raw_sha256="1e4ef4bb999024321f591c40e5fa369e397af1f7c75f7fa08e83c9b8c4a2802f",
    bundle_bytes=197098,bundle_sha256="b0631c667d51a9b670287b6589503801ca8d8c2fb482b4473a3ba866ca0cd9d8",
    nodes=110,root=109,target_ast_sha256="911c376cb25c2cb18aefd0e0b77325ea871669c2faefda9024ec48e53e0a0bbf")
SHIFTED_ARCHIVE = dict(case="CV020",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-shifted-euler-prefix-v1/generation-process.json.gz",
    bytes=19150,sha256="6475d1ad8b6c39927be55802ccca244529a1bc19edec23fe41f491e01eb177ee",
    raw_bytes=279180,raw_sha256="80ef185d7a5411ee9543cb45e07b3b323970ca7f102872bb3792fb8d86e3e8ba",
    bundle_bytes=164302,bundle_sha256="b0ec06a09c31f62884ee4243ba011cb43c4e99f95b1c064da395fdc4a57e3f1b",
    nodes=107,root=106,target_ast_sha256="a653a577dc205366278791e1c5bb895d21bdb2ea525bea07c4494276a051b832")
ARCHIVES = (CONVOLUTION_ARCHIVE,POWER_EULER_ARCHIVE,WEIGHTED_ARCHIVE,SHIFTED_ARCHIVE)
ENDPOINT_SOURCES = {
    "one_mul":"forall a. 1*a=a",
    "mul_zero_left":"forall a. 0*a=0",
    "mul_comm":"forall a b. a*b=b*a",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "zero_le":"forall a. Le(0,a)",
    "le_refl":"forall a. Le(a,a)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "coefficient_exists":"forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)",
    "coefficient_swap":ASSOC_HELPERS["coefficient_swap"],
    "coefficient_linearity":LINEAR_HELPERS["coefficient_linearity"],
    "row_decode":POWER_HELPERS["decode"],"power_exists":POWER_SOURCE,
    "euler_exists":EULER_HELPERS["euler_exists"],
    "trace_unit":POWER_EULER_HELPERS["trace_unit"],
    "power_rule":POWER_EULER_HELPERS["power_rule"],
    "unit_entry":UNIT_HELPERS["unit_entry"],
    "weighted_exists":WEIGHTED_SOURCE,"shifted_exists":SHIFTED_SOURCE,
}
HELPER_DEPENDENCIES = {
    "weighted_zero":("beta_unique",),"weighted_graph":("beta_unique",),
    "zero_convolution":("beta_unique","coefficient_linearity","one_mul","mul_zero_left"),
    "unit_euler_zero":("unit_entry","mul_zero_left"),
    "weighted_value":("one_mul",),
    "multiply_zero":("mul_add","mul_assoc","mul_comm"),
    "multiply_weighted":("mul_add","mul_assoc","mul_comm"),
    "chain_rule":("row_decode","beta_exists","beta_unique","zero_le","succ_le_succ","le_refl","le_succ","le_trans",
        "weighted_zero","weighted_graph","weighted_value","unit_euler_zero","trace_unit","zero_convolution",
        "coefficient_swap","coefficient_exists","coefficient_linearity","power_rule","one_mul","multiply_zero","multiply_weighted"),
    "CV021":("euler_exists","power_exists","shifted_exists","weighted_exists","chain_rule","le_refl"),
}


class FiniteCompositionError(ValueError):
    """Changed computation, finite composition assertion or actual proof body."""


def definition_registry():
    registry = dict(weighted_registry())
    for supplied in (shifted_registry(),power_registry()):
        for name,d in supplied.items():
            if name in registry and (registry[name].template_formula!=d.template_formula or registry[name].stable_id!=d.stable_id):
                raise FiniteCompositionError("shared conservative definition mismatch")
            registry[name] = d
    return MappingProxyType(registry)


def frozen_finite_composition_euler_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FiniteCompositionError("CV021 exact finite composition construction target changed")
    return target


def source_contract():
    return dict(code="CV021",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_euler_power_shift_and_both_weighted_traces_constructed=True,
        all_coefficients_below_common_width=True,arbitrary_natural_outer_weights=True,
        constant_input_coefficient_need_not_vanish=True,finite_composition_euler_identity=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",exp_composition_recurrence=False,
        rational_denominator_transport=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def finite_composition_euler_source_pins():
    result = weighted_series_trace_source_pins()
    for supplied in (shifted_euler_prefix_source_pins(),series_power_euler_source_pins()):
        for name,pin in supplied.items():
            if name in result and result[name]!=pin:
                raise FiniteCompositionError("source dependency disagreement")
            result[name] = pin
    expected = {
        "scripts/sqrt2_power_weighted_series_trace.py":"34b97b7cc1a0391e74b01db46847dd78260e751b47312acdd64fea5281958bbc",
        "scripts/sqrt2_power_shifted_euler_prefix.py":"07045825c341dc8b802fa3ee79130bca26b5d4e18f49b8e8dd0eef6aed0f2b3b",
        "scripts/sqrt2_power_series_power_euler.py":"f00d1180a96ba497a5c961b850e660941d6c608d70ebc7071a51e53344b5205c",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_finite_composition_euler.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FiniteCompositionError("finite composition source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _weighted_zero(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Zero
    def decoded(t):
        eqs = tuple(apply(specialize(t,"beta_unique",*t.terms(Q[2*j:2*j+2]),Zero(),t.term(("zb","zc")[j]),t.term(("ub","uc")[j])),
            field(AndElimL(t.hyp("initial")),j,2),field(t.hyp("row"),j,2)) for j in range(2))
        first = _subst(t,registry,"NatZeroPrefix(slot,zc,H)",eqs[0],AndElimR(t.hyp("initial")))
        return _subst(t,registry,"NatZeroPrefix(ub,slot,H)",eqs[1],first)
    return introduce(s,STORAGE+("N","ub","uc"),("trace","row"),lambda t:
        eliminate(t,AndElimL(t.hyp("trace")),("zb","zc"),"initial",decoded))


def _weighted_graph(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimR
    from peano_lab.kernel.terms import Succ
    old = ("zb","zc","ab","ac","bb","bc","z")
    new = ("ub","uc","eb","ec","fb","fc","w")
    def decoded(t):
        eqs = []
        for position in range(6):
            group,component = divmod(position,2)
            codes = P if group==0 else Q
            index = Succ(t.term("k")) if group==2 else t.term("k")
            equal = apply(specialize(t,"beta_unique",*t.terms(codes[2*component:2*component+2]),index,t.term(old[position]),t.term(new[position])),
                field(field(t.hyp("step"),group,5),component,2),field(t.hyp(("source","current","output")[group]),component,2))
            eqs.append(equal)
        eqs.append(apply(specialize(t,"beta_unique",*t.terms(WEIGHTS+("k","z","w"))),field(t.hyp("step"),3,5),t.hyp("weight")))
        value = field(t.hyp("step"),4,5)
        for position,equal in enumerate(eqs):
            names = new[:position]+("slot",)+old[position+1:]
            value = _subst(t,registry,graph(names[6],names[:2],names[2:4],names[4:6]),equal,value)
        return value
    return introduce(s,STORAGE+("N","k")+new,("trace","bound","source","current","output","weight"),lambda t:
        eliminate(t,apply(instantiate(AndElimR(t.hyp("trace")),t.term("k")),t.hyp("bound")),old,"step",decoded))


def _zero_convolution(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def finish(t):
        def pointwise(u):
            zero = apply(specialize(u,"zeros",u.term("j")),u.hyp("bound"))
            equal = apply(specialize(u,"beta_unique",*u.terms(("ab","ac","j","z")),Zero()),u.hyp("third"),zero)
            return _chain(specialize(u,"one_mul",u.term("z")),equal,EqSym(instantiate(Axiom("PA3"),Zero())),
                CongAdd(EqSym(specialize(u,"mul_zero_left",u.term("x"))),EqSym(specialize(u,"mul_zero_left",u.term("y")))))
        points = introduce(t,("j","x","y","z"),("bound","first","second","third"),pointwise)
        identity = apply(specialize(t,"coefficient_linearity",Zero(),Zero(),Succ(Zero()),
            *t.terms(("ab","ac","ab","ac","ab","ac","L","bb","bc","M","i","p","p","p"))),points,t.hyp("coefficient"),t.hyp("coefficient"),t.hyp("coefficient"))
        return _chain(EqSym(specialize(t,"one_mul",t.term("p"))),identity,
            CongAdd(specialize(t,"mul_zero_left",t.term("p")),specialize(t,"mul_zero_left",t.term("p"))),instantiate(Axiom("PA3"),Zero()))
    return introduce(s,("ab","ac","L","bb","bc","M","i","p"),("zeros","coefficient"),finish)


def _unit_euler_zero(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongMul,EqRefl,EqTrans,OrElim
    def finish(t):
        unit = apply(specialize(t,"unit_entry",*t.terms(("ub","uc","H","i","a"))),t.hyp("unit"),t.hyp("bound"),t.hyp("entry"))
        left,right = t.hypothesis("at_zero"),t.hypothesis("positive")
        first = EqTrans(CongMul(AndElimL(left.hyp("at_zero")),EqRefl(left.term("a"))),specialize(left,"mul_zero_left",left.term("a")))
        second = eliminate(right,right.hyp("positive"),("k",),"data",lambda u:
            EqTrans(CongMul(EqRefl(u.term("i")),AndElimR(u.hyp("data"))),instantiate(Axiom("PA5"),u.term("i"))))
        return OrElim(unit,first,second)
    return introduce(s,("ub","uc","H","i","a"),("unit","bound","entry"),finish)


def _weighted_value(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        equation = apply(specialize(t,"graph",*t.terms(("i","a","b","c"))),*(t.hyp(h) for h in ("bound","first","second","third")))
        return _chain(EqSym(specialize(t,"one_mul",t.term("c"))),equation,
            CongAdd(specialize(t,"one_mul",t.term("a")),EqRefl(Mul(t.term("w"),t.term("b")))))
    return introduce(s,("ab","ac","bb","bc","cb","cc","H","w","i","a","b","c"),("graph","bound","first","second","third"),finish)


def _multiply(s,mode):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym,EqTrans
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        i,a,w,b = t.terms(("i","a","w","b"))
        exchange = _chain(EqSym(specialize(t,"mul_assoc",i,w,b)),CongMul(specialize(t,"mul_comm",i,w),EqRefl(b)),specialize(t,"mul_assoc",w,i,b))
        expansion = EqTrans(CongMul(EqRefl(i),t.hyp("sum")),specialize(t,"mul_add",i,a,Mul(w,b)))
        if mode=="zero":
            first = EqTrans(CongMul(EqRefl(i),t.hyp("left")),instantiate(Axiom("PA5"),i))
            second = _chain(exchange,CongMul(EqRefl(w),t.hyp("right")),instantiate(Axiom("PA5"),w))
            return _chain(expansion,CongAdd(first,second),instantiate(Axiom("PA3"),Zero()))
        factor,y = Succ(t.term("k")),t.term("y")
        second = _chain(exchange,CongMul(EqRefl(w),t.hyp("right")),EqSym(specialize(t,"mul_assoc",w,factor,y)),CongMul(specialize(t,"mul_comm",w,factor),EqRefl(y)))
        return EqTrans(expansion,CongAdd(t.hyp("left"),second))
    names = ("i","a","w","b","p") if mode=="zero" else ("i","a","w","b","x","y","k","p")
    return introduce(s,names,("sum","left","right"),finish)


def _chain_rule(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym,EqTrans,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    HQ,JR,KP,LP = ("hb","hc"),("jb","jc"),("kb","kc"),("lb","lc")
    params = ("N",)+F+G+("i","p","t")
    premises = ("power","bound","shift","qtrace","rtrace","row_q","row_r","index","entry","coefficient")
    def step_graph(t,weights,acc,length,index,source,current,output,weight,proofs):
        return apply(specialize(t,"weighted_graph",*t.terms(("H",)+weights+P+acc),length,index,*t.terms(source+current+output),weight),*proofs)
    def base(t):
        def finish(u):
            i,a,b,w,p,tval,N = u.terms(("i","a","b","w","p","t","N"))
            zero_q = apply(specialize(u,"weighted_zero",*u.terms(("H",)+WEIGHTS+P+Q),Succ(N),*u.terms(HQ)),u.hyp("qtrace"),u.hyp("row_qzero"))
            zero_entry = apply(instantiate(zero_q,i),u.hyp("index"))
            a_zero = apply(specialize(u,"beta_unique",*u.terms(HQ),i,a,Zero()),u.hyp("old_value"),zero_entry)
            unit = apply(specialize(u,"trace_unit",*u.terms(A+("H",)+P+("N",)+KP)),u.hyp("power"),u.hyp("row_pzero"))
            euler_zero = apply(specialize(u,"unit_euler_zero",*u.terms(KP+("H","i","b"))),unit,u.hyp("index"),u.hyp("power_value"))
            bound = apply(specialize(u,"succ_le_succ",Zero(),N),specialize(u,"zero_le",N))
            relation = step_graph(u,WEIGHTS,Q,Succ(N),Zero(),KP,HQ,F,w,
                (u.hyp("qtrace"),bound,u.hyp("row_pzero"),u.hyp("row_qzero"),u.hyp("row_q"),u.hyp("weight")))
            value = apply(specialize(u,"weighted_value",*u.terms(HQ+KP+F+("H","w","i","a","b","p"))),
                relation,u.hyp("index"),u.hyp("old_value"),u.hyp("power_value"),u.hyp("entry"))
            left_zero = apply(specialize(u,"multiply_zero",i,a,w,b,p),value,a_zero,euler_zero)
            zero_r = apply(specialize(u,"weighted_zero",*u.terms(("H",)+DERIVED+P+R+("N",)+G)),u.hyp("rtrace"),u.hyp("row_r"))
            swapped = apply(specialize(u,"coefficient_swap",*u.terms(EA+G+("H","i","t"))),u.hyp("coefficient"))
            right_zero = apply(specialize(u,"zero_convolution",*u.terms(G+("H",)+EA+("i","t"))),zero_r,swapped)
            return EqTrans(left_zero,EqSym(right_zero))
        return eliminate(t,specialize(t,"row_decode",*t.terms(Q),Zero()),HQ,"row_qzero",lambda u:
            eliminate(u,specialize(u,"row_decode",*u.terms(P),Zero()),KP,"row_pzero",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(WEIGHTS),Zero()),("w",),"weight",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(HQ+("i",))),("a",),"old_value",lambda x:
                        eliminate(x,specialize(x,"beta_exists",*x.terms(KP+("i",))),("b",),"power_value",finish)))))
    def successor(t):
        def finish(u):
            k,N,i,a,b,w,p,x,y = u.terms(("k","N","i","a","b","w","p","x","y"))
            factor = Succ(k)
            derivative_weight = Mul(factor,w)
            q_bound = apply(specialize(u,"succ_le_succ",factor,N),u.hyp("bound"))
            q_relation = step_graph(u,WEIGHTS,Q,Succ(N),factor,LP,HQ,F,w,
                (u.hyp("qtrace"),q_bound,u.hyp("row_pnext"),u.hyp("row_qprev"),u.hyp("row_q"),u.hyp("weight")))
            q_value = apply(specialize(u,"weighted_value",*u.terms(HQ+LP+F+("H","w","i","a","b","p"))),
                q_relation,u.hyp("index"),u.hyp("old_value"),u.hyp("power_value"),u.hyp("entry"))
            small = apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k))
            old_bound = apply(specialize(u,"le_trans",k,factor,N),small,u.hyp("bound"))
            ih = apply(specialize(u,"IH",N,*u.terms(HQ+JR),i,a,x),
                u.hyp("power"),old_bound,u.hyp("shift"),u.hyp("qtrace"),u.hyp("rtrace"),u.hyp("row_qprev"),u.hyp("row_rprev"),u.hyp("index"),u.hyp("old_value"),u.hyp("coefficient_x"))
            power_rule = apply(specialize(u,"power_rule",*u.terms(A+("H",)+P+D)),u.hyp("euler"))
            power_identity = apply(instantiate(power_rule,k,N,*u.terms(KP+LP),i,b,y),
                u.hyp("power"),u.hyp("bound"),u.hyp("row_pcurrent"),u.hyp("row_pnext"),u.hyp("index"),u.hyp("power_value"),u.hyp("coefficient_y"))
            left = apply(specialize(u,"multiply_weighted",i,a,w,b,x,y,k,p),q_value,ih,power_identity)
            computed_weight = apply(specialize(u,"shift",k,w),u.hyp("bound"),u.hyp("weight"))
            r_relation = step_graph(u,DERIVED,R,N,k,KP,JR,G,derivative_weight,
                (u.hyp("rtrace"),u.hyp("bound"),u.hyp("row_pcurrent"),u.hyp("row_rprev"),u.hyp("row_r"),computed_weight))
            swapped = tuple(apply(specialize(u,"coefficient_swap",*u.terms(EA+codes+("H","i",value))),u.hyp(label))
                for codes,value,label in ((JR,"x","coefficient_x"),(KP,"y","coefficient_y"),(G,"t","coefficient")))
            linearity = apply(specialize(u,"coefficient_linearity",Succ(Zero()),derivative_weight,Succ(Zero()),
                *u.terms(JR+KP+G+("H",)+D+("L","i","x","y","t"))),r_relation,*swapped)
            right = _chain(EqSym(specialize(u,"one_mul",u.term("t"))),linearity,
                CongAdd(specialize(u,"one_mul",x),EqRefl(Mul(derivative_weight,y))))
            return EqTrans(left,EqSym(right))
        def construct(u,position):
            if position==9:
                return finish(u)
            if position==0:
                source,names,label = specialize(u,"row_decode",*u.terms(Q),Succ(u.term("k"))),HQ,"row_qprev"
            elif position==1:
                source,names,label = specialize(u,"row_decode",*u.terms(R+("k",))),JR,"row_rprev"
            elif position==2:
                source,names,label = specialize(u,"row_decode",*u.terms(P+("k",))),KP,"row_pcurrent"
            elif position==3:
                source,names,label = specialize(u,"row_decode",*u.terms(P),Succ(u.term("k"))),LP,"row_pnext"
            elif position==4:
                source,names,label = specialize(u,"beta_exists",*u.terms(WEIGHTS),Succ(u.term("k"))),("w",),"weight"
            elif position==5:
                source,names,label = specialize(u,"beta_exists",*u.terms(HQ+("i",))),("a",),"old_value"
            elif position==6:
                source,names,label = specialize(u,"beta_exists",*u.terms(LP+("i",))),("b",),"power_value"
            elif position==7:
                source,names,label = specialize(u,"coefficient_exists",*u.terms(EA+JR+("H","i"))),("x",),"coefficient_x"
            else:
                source,names,label = specialize(u,"coefficient_exists",*u.terms(EA+KP+("H","i"))),("y",),"coefficient_y"
            return eliminate(u,source,names,label,lambda v:construct(v,position+1))
        return construct(t,0)
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.right.body
    return introduce(s,FIXED,("euler",),lambda t:
        Ind(motive,introduce(t,params,premises,base),introduce(t,("k",),("IH",),lambda u:introduce(u,params,premises,successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        def entry(u):
            rule = apply(specialize(u,"chain_rule",*u.terms(FIXED)),u.hyp("euler"))
            return apply(instantiate(rule,u.term("N"),u.term("N"),*u.terms(F+G+("i","p","t"))),
                u.hyp("power"),specialize(u,"le_refl",u.term("N")),
                *(u.hyp(h) for h in ("shift","qtrace","rtrace","row_q","row_r","index","entry","coefficient")))
        invariant = introduce(t,F+G+("i","p","t"),("row_q","row_r","index","entry","coefficient"),entry)
        return witness(t.terms(D+P+DERIVED+Q+R),conjunction(
            *(t.hyp(h) for h in ("euler","power","shift","qtrace","rtrace")),invariant))
    def construct(t,position):
        if position==5:
            return chosen(t)
        if position==0:
            source,names,label = specialize(t,"euler_exists",*t.terms(A)),D,"euler"
        elif position==1:
            source,names,label = specialize(t,"power_exists",*t.terms(A+("H","N"))),P,"power"
        elif position==2:
            source,names,label = specialize(t,"shifted_exists",*t.terms(WEIGHTS+("N",))),DERIVED,"shift"
        elif position==3:
            source,names,label = specialize(t,"weighted_exists",*t.terms(("H",)+WEIGHTS+P),Succ(t.term("N"))),Q,"qtrace"
        else:
            source,names,label = specialize(t,"weighted_exists",*t.terms(("H",)+DERIVED+P+("N",))),R,"rtrace"
        return eliminate(t,source,names,label,lambda u:construct(u,position+1))
    return introduce(s,A+("H",)+WEIGHTS+("N",),(),lambda t:construct(t,0))


def prove_finite_composition_euler(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"weighted_zero":lambda s:_weighted_zero(s,registry),"weighted_graph":lambda s:_weighted_graph(s,registry),
        "zero_convolution":_zero_convolution,"unit_euler_zero":_unit_euler_zero,"weighted_value":_weighted_value,
        "multiply_zero":lambda s:_multiply(s,"zero"),"multiply_weighted":lambda s:_multiply(s,"weighted"),
        "chain_rule":lambda s:_chain_rule(s,parse_named(HELPER_SOURCES["chain_rule"],registry=registry)),"CV021":_root}
    return assemble_actual_certificate(code="CV021",target=frozen_finite_composition_euler_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=finite_composition_euler_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
