"""CV058: exact denominator-cleared evaluation of every finite power row.

At width J+1 >= 1+K*L, every row through K contains its whole support.
With x=Horner(A,t,L), p=t^L and v=t^J, actual row endpoint y satisfies
(p^k)*y=(v*t^k)*x^k. No factor is cancelled, including when t=0.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_supported_horner_values import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,canonical,json_hash,
    definition_registry as value_registry,supported_horner_values_source_pins,
    NAMED_SOURCE as PRODUCT_SOURCE,
)
from sqrt2_power_power_upper_support import (
    definition_registry as power_registry,power_upper_support_source_pins,
    HELPER_SOURCES as SUPPORT_HELPERS,ENDPOINT_SOURCES as SUPPORT_ENDPOINTS,
)
from sqrt2_power_horner_trace import NAMED_SOURCE as HORNER_SOURCE,HELPER_SOURCES as HORNER_HELPERS
from sqrt2_power_horner_zero_tail import HELPER_SOURCES as TAIL_HELPERS,ENDPOINT_SOURCES as TAIL_ENDPOINTS
from sqrt2_power_convolution_unit import HELPER_SOURCES as UNIT_HELPERS,_subst
from sqrt2_power_quadratic_trace_exists import witness,conjunction
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-finite-power-evaluation-v1"
A,P,HA = ("ab","ac","L"),("pb","pc","qb","qc"),("ahb","ahc")
U,HU,O,HO = ("ub","uc"),("uhb","uhc"),("ob","oc"),("ohb","ohc")
PARAMETERS = A+("t","J","K")
OUTPUTS = P+HA+("x","p","v")
FIXED = PARAMETERS+OUTPUTS
TRACE = "NatPowerTrace(ab,ac,L,S J,pb,pc,qb,qc,K)"
INPUT_TRACE = "NatScaledHornerTrace(ab,ac,t,L,ahb,ahc)"
ROW_TRACE = "NatScaledHornerTrace(ub,uc,t,S J,uhb,uhc)"
ALL_ROWS = ("forall k ub uc uhb uhc y a b c. Le(k,K) -> NatPowerRow(pb,pc,qb,qc,k,ub,uc) -> "+
    ROW_TRACE+" -> BetaAt(uhb,uhc,S J,y) -> Pow(p,k,a) -> Pow(t,k,b) -> Pow(x,k,c) -> a*y=(v*b)*c")
WIDTH = "Le(S(K*L),S J)"
FIXED_PREMISES = (WIDTH,TRACE,INPUT_TRACE,"BetaAt(ahb,ahc,L,x)","Pow(t,L,p)","Pow(t,J,v)")
NAMED_SOURCE = ("forall "+" ".join(PARAMETERS)+". "+WIDTH+" -> exists "+" ".join(OUTPUTS)+". "+TRACE+
    " /\\ ("+INPUT_TRACE+" /\\ (BetaAt(ahb,ahc,L,x) /\\ (Pow(t,L,p) /\\ (Pow(t,J,v) /\\ ("+ALL_ROWS+")))))")
TARGET_SHA256 = "5106a1fb454a028ea96ed82dcd34c652807316d25e5009ec9a5c5f7191df4689"
HELPER_SOURCES = {
    "unit_head":"forall ub uc J d. NatUnitPrefix(ub,uc,S J) -> BetaAt(ub,uc,0,d) -> d=1",
    "unit_value":"forall ub uc t J uhb uhc y v. NatUnitPrefix(ub,uc,S J) -> "+ROW_TRACE+
        " -> BetaAt(uhb,uhc,S J,y) -> Pow(t,J,v) -> y=v",
    "row_bound":"forall L J K k. Lt(k,K) -> "+WIDTH+" -> Le(L+S(k*L),S J)",
    "shuffle":"forall a0 p y t x h v b0 c0 a b c. p*y=t*(x*h) -> a0*h=(v*b0)*c0 -> a=a0*p -> b=b0*t -> c=c0*x -> a*y=(v*b)*c",
    "all_rows":"forall "+" ".join(FIXED)+". "+" -> ".join(FIXED_PREMISES)+" -> "+ALL_ROWS,
}
HELPER_TARGET_SHA256 = {
    "unit_head":"d01818d31d5a962d67ec815cdd621a3ecbcfb503f986e1875062cfbfea3c2418",
    "unit_value":"b6e6889bfa575bfd30d4481f821222748ac9a588f943bb6c760a4f5b11ac2d46",
    "row_bound":"4053e8d0314af8b34606560d9a040e339808fba420610891635ab15011baa170",
    "shuffle":"1aba577ab1b7203436df7265902313208d78b78f67b4874375785966cd5e44b6",
    "all_rows":"6308a287588022746c366aa4bc15d4eeed4f7f1aa592356dc0b8d1024c5dc8f7",
}
VALUE_ARCHIVE = dict(case="CV057",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-supported-horner-values-v1/generation-process.json.gz",
    bytes=60088,sha256="1899bacd3c7a65bff84640e95c745bca65ca898fe98880bfc9f42a02a95d6293",
    raw_bytes=1531694,raw_sha256="27f7f953516050aa3209c4d3a0984667892454724ab51dd58957a289499842e0",
    bundle_bytes=930343,bundle_sha256="adf11d705133f6bc0082777b36d663241bdbf3204ef1262757ea59157b4bf639",
    nodes=233,root=232,target_ast_sha256="77e93a327c7aa0811b3c17aa3152b979b62a19aa3ae70c957544ac810f17661a")
SUPPORT_ARCHIVE = dict(case="CV054",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-power-upper-support-v1/generation-process.json.gz",
    bytes=29994,sha256="e5df41c5e8b2cebfd2f95fc26c31e2a3058165b3f2688209c2f9660b9e86cccc",
    raw_bytes=602102,raw_sha256="4eeaadc1cbcc4e0f9e9da4417c2834e06616577fe124a821c66ba7bdea7d337e",
    bundle_bytes=357879,bundle_sha256="d80b5d0ed46e168bb40518f1fadabb7efc0c20f30639f2560994f933a91320e3",
    nodes=141,root=140,target_ast_sha256="ef95e6269e88a485d4fd577edb6814ce45c9bf1f61fddfcc6aae499ce488e879")
ARCHIVES = (VALUE_ARCHIVE,SUPPORT_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:TAIL_ENDPOINTS[name] for name in ("beta_exists","le_refl","le_succ","le_trans","mul_assoc","mul_comm","one_mul","power_zero","power_step","power_exists")},
    "mul_one":"forall a. a*1=a","zero_add":"forall a. 0+a=a","add_comm":"forall a b. a+b=b+a",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b","succ_ne_zero":"forall a. ~S a=0",
    "zero_le":"forall a. Le(0,a)","succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "mul_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "horner_exists":HORNER_SOURCE,"step_value":HORNER_HELPERS["step_value"],
    "zero_tail":TAIL_HELPERS["zero_tail"],"shift_bound":TAIL_HELPERS["shift_bound"],
    "product_value":PRODUCT_SOURCE,"support_rows":SUPPORT_HELPERS["all_rows"],"storage_support":SUPPORT_HELPERS["storage_support"],
    "unit_entry":UNIT_HELPERS["unit_entry"],"unit_positive":UNIT_HELPERS["unit_positive"],
    "trace_exists":SUPPORT_ENDPOINTS["power_exists"],
    **{name:SUPPORT_ENDPOINTS[name] for name in ("trace_unit","trace_step","row_decode")},
}
ENDPOINT_OWNERS = {name:"CV057" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:"CV054" for name in ("support_rows","storage_support","unit_entry","unit_positive","trace_exists","trace_unit","trace_step","row_decode")})
HELPER_DEPENDENCIES = {
    "unit_head":("zero_le","succ_le_succ","unit_entry","succ_ne_zero"),
    "unit_value":("beta_exists","zero_le","succ_le_succ","unit_head","succ_ne_zero","step_value","zero_add","add_comm","shift_bound","unit_positive","zero_tail","le_refl","mul_one"),
    "row_bound":("mul_mono","succ_le_succ","le_trans","mul_succ_left","add_comm"),
    "shuffle":("mul_assoc","mul_comm"),
    "all_rows":("trace_unit","unit_value","power_zero","one_mul","mul_one","row_decode","horner_exists","beta_exists","power_step","le_trans","le_succ","le_refl",
        "trace_step","support_rows","storage_support","row_bound","product_value","add_comm","shuffle"),
    "CV058":("trace_exists","horner_exists","beta_exists","power_exists","all_rows"),
}


class FinitePowerEvaluationError(ValueError):
    """Changed whole-support bound, actual power row or scaling equation."""


def definition_registry():
    result = dict(value_registry())
    for name,d in power_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise FinitePowerEvaluationError("shared evaluation/power definition mismatch")
        result[name] = d
    return MappingProxyType(result)


def frozen_finite_power_evaluation_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=6 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FinitePowerEvaluationError("CV058 exact all-exponents evaluation target changed")
    return target


def source_contract():
    return dict(code="CV058",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,support_complete_width="1+K*L <= J+1",actual_power_trace_constructed=True,
        actual_input_horner_and_two_scaling_powers_constructed=True,
        all_supplied_row_values_through_K=True,unit_at_exponent_zero_retained=True,
        identity="a*y=(v*b)*c",powers="p=t^L; v=t^J; a=p^k; b=t^k; c=x^k",
        zero_multiplier_and_empty_input_allowed=True,no_nonzero_factor_cancelled=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",arbitrary_truncation_evaluation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def finite_power_evaluation_source_pins():
    result = supported_horner_values_source_pins()
    for name,pin in power_upper_support_source_pins().items():
        if name in result and result[name]!=pin:
            raise FinitePowerEvaluationError("shared proof-source pin mismatch")
        result[name] = pin
    expected = {"scripts/sqrt2_power_supported_horner_values.py":"9d067bc92c6bdd04a0e7714184d9cd3c1b90eb49dcf2aad2ebdad01913adf0c4",
        "scripts/sqrt2_power_power_upper_support.py":"646f2d23f51080170bb53e7f2ab3ea9b4aa3a06aa68475e37c41e04c3b2a1925",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_finite_power_evaluation.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FinitePowerEvaluationError("finite power evaluation source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _one_add(s,x):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongS
    from peano_lab.kernel.terms import Succ,Zero
    return _chain(specialize(s,"add_comm",Succ(Zero()),x),instantiate(Axiom("PA4"),x,Zero()),CongS(instantiate(Axiom("PA3"),x)))


def _unit_head(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,EqSym,OrElim
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        zero,J = Zero(),t.term("J")
        bound = apply(specialize(t,"succ_le_succ",zero,J),specialize(t,"zero_le",J))
        cases = apply(specialize(t,"unit_entry",*t.terms(U),Succ(J),zero,t.term("d")),t.hyp("unit"),bound,t.hyp("coefficient"))
        impossible = t.hypothesis("positive")
        impossible = eliminate(impossible,impossible.hyp("positive"),("j",),"positive_data",lambda u:
            BotElim(apply(specialize(u,"succ_ne_zero",u.term("j")),EqSym(AndElimL(u.hyp("positive_data"))))))
        return OrElim(cases,AndElimR(t.hypothesis("zero_case").hyp("zero_case")),impossible)
    return introduce(s,U+("J","d"),("unit","coefficient"),chosen)


def _unit_value(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,AndIntro,CongAdd,EqRefl,EqSym,EqTrans,OrIntroL
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def tail(t):
        one,j,J = Succ(Zero()),t.term("j"),t.term("J")
        bound = apply(specialize(t,"shift_bound",one,j,J),t.hyp("index"))
        bound = _subst(t,registry,"Lt(1+j,slot)",_one_add(t,J),bound)
        nonzero = introduce(t,(),("equation",),lambda u:apply(specialize(u,"succ_ne_zero",u.term("j")),
            EqTrans(EqSym(_one_add(u,u.term("j"))),u.hyp("equation"))))
        return apply(specialize(t,"unit_positive",*t.terms(U),Succ(J),Add(one,j),t.term("w")),
            t.hyp("unit"),nonzero,OrIntroL(AndIntro(bound,t.hyp("entry"))))
    def chosen(t):
        one,zero,J = Succ(Zero()),Zero(),t.term("J")
        bound = apply(specialize(t,"succ_le_succ",zero,J),specialize(t,"zero_le",J))
        d1 = apply(specialize(t,"unit_head",*t.terms(U+("J","d"))),t.hyp("unit"),t.hyp("coefficient"))
        step = apply(instantiate(AndElimR(t.hyp("trace")),zero),bound)
        hvalue = apply(specialize(t,"step_value",*t.terms(U+("t",)+HU),zero,zero,*t.terms(("d","h"))),
            step,AndElimL(t.hyp("trace")),t.hyp("coefficient"),t.hyp("first"))
        h1 = _chain(hvalue,CongAdd(instantiate(Axiom("PA5"),t.term("t")),EqRefl(t.term("d"))),specialize(t,"zero_add",t.term("d")),d1)
        first = _subst(t,registry,"BetaAt(uhb,uhc,1,slot)",h1,t.hyp("first"))
        zeros = introduce(t,("j","w"),("index","entry"),tail)
        trace = _subst(t,registry,"NatScaledHornerTrace(ub,uc,t,slot,uhb,uhc)",EqSym(_one_add(t,J)),t.hyp("trace"))
        endpoint = _subst(t,registry,"BetaAt(uhb,uhc,slot,y)",EqSym(_one_add(t,J)),t.hyp("value"))
        invariant = apply(specialize(t,"zero_tail",*t.terms(U+("t",)),one,J,*t.terms(HU),one),trace,first,zeros)
        result = apply(instantiate(invariant,*t.terms(("J","y","v"))),specialize(t,"le_refl",J),endpoint,t.hyp("power"))
        return EqTrans(result,specialize(t,"mul_one",t.term("v")))
    return introduce(s,U+("t","J")+HU+("y","v"),("unit","trace","value","power"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(U),Zero()),("d",),"coefficient",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(HU),Succ(Zero())),("h",),"first",chosen)))


def _row_bound(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongS,EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        L,J,K,k = t.terms(("L","J","K","k"))
        mono = apply(specialize(t,"mul_mono",Succ(k),K,L),t.hyp("bound"))
        mono = apply(specialize(t,"succ_le_succ",Mul(Succ(k),L),Mul(K,L)),mono)
        order = apply(specialize(t,"le_trans",Succ(Mul(Succ(k),L)),Succ(Mul(K,L)),Succ(J)),mono,t.hyp("width"))
        equation = _chain(instantiate(Axiom("PA4"),L,Mul(k,L)),CongS(specialize(t,"add_comm",L,Mul(k,L))),CongS(EqSym(specialize(t,"mul_succ_left",k,L))))
        return _subst(t,registry,"Le(slot,S J)",EqSym(equation),order)
    return introduce(s,("L","J","K","k"),("bound","width"),finish)


def _multiplicative_equal(scope,left,right):
    """Bounded sixteen-factor AC reconstruction; ordinary proof bodies only."""
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def product(xs):
        return xs[0] if len(xs)==1 else Mul(xs[0],product(xs[1:]))
    def concat(xs,ys):
        if len(xs)==1:
            return EqRefl(Mul(xs[0],product(ys)))
        return _chain(specialize(scope,"mul_assoc",xs[0],product(xs[1:]),product(ys)),CongMul(EqRefl(xs[0]),concat(xs[1:],ys)))
    def flatten(term):
        if type(term) is not Mul:
            return (term,),EqRefl(term)
        xs,lp = flatten(term.left);ys,rp = flatten(term.right)
        if len(xs)+len(ys)>16:
            raise FinitePowerEvaluationError("multiplicative reconstruction exceeds sixteen factors")
        return xs+ys,_chain(CongMul(lp,rp),concat(xs,ys))
    def adjacent(xs,index):
        if index:
            return CongMul(EqRefl(xs[0]),adjacent(xs[1:],index-1))
        a,b = xs[:2]
        if len(xs)==2:
            return specialize(scope,"mul_comm",a,b)
        rest = product(xs[2:])
        return _chain(EqSym(specialize(scope,"mul_assoc",a,b,rest)),CongMul(specialize(scope,"mul_comm",a,b),EqRefl(rest)),specialize(scope,"mul_assoc",b,a,rest))
    def reorder(xs,ys):
        if len(xs)!=len(ys) or not xs:
            raise FinitePowerEvaluationError("multiplicative factor inventory differs")
        if len(xs)==1:
            if xs!=ys:
                raise FinitePowerEvaluationError("multiplicative factor differs")
            return EqRefl(xs[0])
        moved,proofs = list(xs),[]
        try:
            position = moved.index(ys[0])
        except ValueError:
            raise FinitePowerEvaluationError("missing target multiplicative factor") from None
        for index in reversed(range(position)):
            proofs.append(adjacent(tuple(moved),index))
            moved[index],moved[index+1] = moved[index+1],moved[index]
        proofs.append(CongMul(EqRefl(moved[0]),reorder(tuple(moved[1:]),ys[1:])))
        return _chain(*proofs)
    xs,lp = flatten(left);ys,rp = flatten(right)
    return _chain(lp,reorder(xs,ys),EqSym(rp))


def _shuffle(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        a0,p,y,t0,x,h,v,b0,c0,a,b,c = t.terms(("a0","p","y","t","x","h","v","b0","c0","a","b","c"))
        left = Mul(a0,Mul(t0,Mul(x,h)))
        grouped = Mul(Mul(t0,x),Mul(a0,h))
        replaced = Mul(Mul(t0,x),Mul(Mul(v,b0),c0))
        right = Mul(Mul(v,Mul(b0,t0)),Mul(c0,x))
        return _chain(CongMul(t.hyp("next_a"),EqRefl(y)),specialize(t,"mul_assoc",a0,p,y),
            CongMul(EqRefl(a0),t.hyp("step")),_multiplicative_equal(t,left,grouped),
            CongMul(EqRefl(Mul(t0,x)),t.hyp("old")),_multiplicative_equal(t,replaced,right),
            CongMul(CongMul(EqRefl(v),EqSym(t.hyp("next_b"))),EqSym(t.hyp("next_c"))))
    return introduce(s,("a0","p","y","t","x","h","v","b0","c0","a","b","c"),("step","old","next_a","next_b","next_c"),finish)


def _all_rows(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    row_params = U+HU+("y","a","b","c")
    row_hyps = ("bound","row","row_trace","row_value","power_a","power_b","power_c")
    fixed_hyps = ("width","trace","input_trace","input_value","power_p","power_v")
    def base(t):
        height = Succ(t.term("J"))
        unit = apply(specialize(t,"trace_unit",*t.terms(A),height,*t.terms(P+("K",)+U)),t.hyp("trace"),t.hyp("row"))
        yv = apply(specialize(t,"unit_value",*t.terms(U+("t","J")+HU+("y","v"))),unit,t.hyp("row_trace"),t.hyp("row_value"),t.hyp("power_v"))
        def power_one(base,value,label):
            return apply(specialize(t,"power_zero",t.term(base),Zero(),t.term(value)),EqRefl(Zero()),t.hyp(label))
        a1,b1,c1 = power_one("p","a","power_a"),power_one("t","b","power_b"),power_one("x","c","power_c")
        right = _chain(CongMul(CongMul(EqRefl(t.term("v")),b1),c1),specialize(t,"mul_one",Mul(t.term("v"),Succ(Zero()))),specialize(t,"mul_one",t.term("v")))
        return _chain(CongMul(a1,yv),specialize(t,"one_mul",t.term("v")),EqSym(right))
    def successor(t):
        def chosen(u):
            k,K,J,L = u.terms(("k","K","J","L"));height = Succ(J)
            previous_bound = apply(specialize(u,"le_trans",k,Succ(k),K),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            old = apply(specialize(u,"IH",*u.terms(O+HO+("h","a0","b0","c0"))),previous_bound,u.hyp("previous"),AndElimL(u.hyp("old_horner")),u.hyp("old_value"),
                AndElimL(u.hyp("data_a")),AndElimL(u.hyp("data_b")),AndElimL(u.hyp("data_c")))
            convolution = apply(specialize(u,"trace_step",*u.terms(A),height,*u.terms(P+("K","k")+O+U)),u.hyp("trace"),u.hyp("bound"),u.hyp("previous"),u.hyp("row"))
            supports = apply(specialize(u,"support_rows",*u.terms(A),height,K,*u.terms(P)),u.hyp("trace"))
            support = apply(instantiate(supports,k,*u.terms(O)),previous_bound,u.hyp("previous"))
            cutoff = apply(specialize(u,"row_bound",*u.terms(("L","J","K","k"))),u.hyp("bound"),u.hyp("width"))
            args = u.terms(A+O)+(height,)+u.terms(U)+(L,Succ(Mul(k,L)),u.term("t"),height,L)+u.terms(HA+HO+HU+("x","h","y","p"))
            step = apply(specialize(u,"product_value",*args),specialize(u,"storage_support",*u.terms(A)),support,cutoff,
                specialize(u,"add_comm",height,L),convolution,u.hyp("input_trace"),u.hyp("input_value"),AndElimL(u.hyp("old_horner")),u.hyp("old_value"),u.hyp("row_trace"),u.hyp("row_value"),u.hyp("power_p"))
            return apply(specialize(u,"shuffle",*u.terms(("a0","p","y","t","x","h","v","b0","c0","a","b","c"))),
                step,old,AndElimR(u.hyp("data_a")),AndElimR(u.hyp("data_b")),AndElimR(u.hyp("data_c")))
        def choose_powers(u):
            def step(v,base,out):
                return apply(specialize(v,"power_step",v.term(base),v.term("k"),Succ(v.term("k")),v.term(out)),EqRefl(Succ(v.term("k"))),v.hyp("power_"+out))
            return eliminate(u,step(u,"p","a"),("a0",),"data_a",lambda v:
                eliminate(v,step(v,"t","b"),("b0",),"data_b",lambda w:
                    eliminate(w,step(w,"x","c"),("c0",),"data_c",chosen)))
        return eliminate(t,specialize(t,"row_decode",*t.terms(P+("k",))),O,"previous",lambda u:
            eliminate(u,specialize(u,"horner_exists",*u.terms(O+("t",)),Succ(u.term("J"))),HO,"old_horner",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(HO),Succ(v.term("J"))),("h",),"old_value",choose_powers)))
    motive = target
    for _ in FIXED:
        motive = motive.body
    for _ in fixed_hyps:
        motive = motive.right
    motive = motive.body
    return introduce(s,FIXED,fixed_hyps,lambda t:Ind(motive,introduce(t,row_params,row_hyps,base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,row_params,row_hyps,successor))))


def _root(s):
    from peano_lab.kernel.proofs import AndElimL
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        invariant = apply(specialize(t,"all_rows",*t.terms(FIXED)),t.hyp("width"),t.hyp("trace"),AndElimL(t.hyp("horner")),t.hyp("value"),t.hyp("power_p"),t.hyp("power_v"))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("trace"),AndElimL(t.hyp("horner")),t.hyp("value"),t.hyp("power_p"),t.hyp("power_v"),invariant))
    return introduce(s,PARAMETERS,("width",),lambda t:
        eliminate(t,specialize(t,"trace_exists",*t.terms(A),Succ(t.term("J")),t.term("K")),P,"trace",lambda u:
            eliminate(u,specialize(u,"horner_exists",*u.terms(A[:2]+("t","L"))),HA,"horner",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(HA+("L",))),("x",),"value",lambda w:
                    eliminate(w,specialize(w,"power_exists",*w.terms(("t","L"))),("p",),"power_p",lambda z:
                        eliminate(z,specialize(z,"power_exists",*z.terms(("t","J"))),("v",),"power_v",chosen))))))


def prove_finite_power_evaluation(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV058",target=frozen_finite_power_evaluation_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"unit_head":_unit_head,"unit_value":lambda s:_unit_value(s,registry),"row_bound":lambda s:_row_bound(s,registry),"shuffle":_shuffle,
            "all_rows":lambda s:_all_rows(s,parse_named(HELPER_SOURCES["all_rows"],registry=registry),registry),"CV058":_root},
        pins=finite_power_evaluation_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
