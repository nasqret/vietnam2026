"""CV029: initial values and all coefficients of the actual finite composition.

At width N>=2 construct the whole CV028 computation, its nonzero initial
weight z, and prove C[0]=z and C[i]=2*z at every positive i<N. The actual
recurrence and initial values are outputs, not assumptions. Identification
with exponential partial sums and analytic functions is still separate.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_composition_recurrence import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,definition_registry as composition_registry,
    composition_recurrence_source_pins,NAMED_SOURCE as COMPOSITION_SOURCE,
    RESULT,OUTPUTS as COMPUTATION_OUTPUTS,A,D,EA,W,P,Q,C,
    RECURRENCE_ARCHIVE,HELPER_SOURCES as COMPOSITION_HELPERS,
    ENDPOINT_SOURCES as COMPOSITION_ENDPOINTS,coefficient,
)
from sqrt2_power_logexp_recurrence import (
    definition_registry as recurrence_registry,NAMED_SOURCE as SOLUTION_SOURCE,
)
from sqrt2_power_series_power_vanishing import VANISHING_SOURCE
from sqrt2_power_series_power_euler import HELPER_SOURCES as POWER_HELPERS
from sqrt2_power_finite_composition_euler import HELPER_SOURCES as FOLD_HELPERS
from sqrt2_power_atanh_coefficients import HELPER_SOURCES as ATANH_HELPERS
from sqrt2_power_periodic_convolution import HELPER_SOURCES as PERIODIC_HELPERS,ENDPOINT_SOURCES as PERIODIC_ENDPOINTS
from sqrt2_power_convolution_commutative import HELPER_SOURCES as SUM_HELPERS,ENDPOINT_SOURCES as SUM_ENDPOINTS
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst,HELPER_SOURCES as UNIT_HELPERS

SCHEMA = "sqrt2-power-composition-coefficients-v1"
OUTPUTS = COMPUTATION_OUTPUTS+("z",)
RECURRENCE = "NatExpAtanhRecurrence(cb,cc,N,z)"
SOLUTION = "forall i a. Lt(i,N) -> BetaAt(cb,cc,i,a) -> ((i=0 /\\ a=z) \\/ (exists k. i=S k /\\ a=2*z))"
NAMED_SOURCE = "forall N. Lt(1,N) -> exists "+" ".join(OUTPUTS)+". ("+RESULT+") /\\ (BetaAt(wb,wc,0,z) /\\ (~z=0 /\\ ("+RECURRENCE+" /\\ ("+SOLUTION+"))))"
TARGET_SHA256 = "88f055686ab9620a1835d315530f9884d4bbd0626a5b97d2524141ff1701f83b"
F,U,V = ("fb","fc"),("ub","uc"),("eb","ec")
FOLD_FIXED = ("ab","ac","L","H")+P+W+Q


def row(codes,index,values):
    return "NatPowerRow("+",".join(codes+(index,)+values)+")"


FOLD_POWER = "NatPowerTrace("+",".join(("ab","ac","L","H")+P+("K",))+")"
FOLD_TRACE = "NatWeightedSeriesTrace("+",".join(("H",)+W+P+Q+("S K",))+")"
DIAG = "PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,T)"
INITIAL = "BetaAt(cb,cc,0,z) /\\ (BetaAt(cb,cc,1,2*z) /\\ ~z=0)"
HELPER_SOURCES = {
    "diagonal_product":"forall ab ac L bb bc M I db dc T j k a b. "+DIAG+" -> Lt(j,T) -> j+k=I -> BetaZeroExtend(ab,ac,L,j,a) -> BetaZeroExtend(bb,bc,M,k,b) -> BetaAt(db,dc,j,a*b)",
    "coefficient_one":"forall ab ac bb bc N h a b p. Lt(1,N) -> BetaAt(ab,ac,0,0) -> BetaAt(ab,ac,1,h) -> BetaAt(bb,bc,0,a) -> BetaAt(bb,bc,1,b) -> NatConvolutionCoefficient(ab,ac,N,bb,bc,N,1,p) -> p=h*a",
    "fold_constant":"forall "+" ".join(FOLD_FIXED)+". NatZeroBefore(ab,ac,L,1) -> Lt(0,H) -> forall k K fb fc a w0. "+FOLD_POWER+" -> "+FOLD_TRACE+" -> Le(k,K) -> "+row(Q,"S k",F)+" -> BetaAt(fb,fc,0,a) -> BetaAt(wb,wc,0,w0) -> a=w0",
    "initial":"forall "+" ".join(("N",)+OUTPUTS)+". ("+RESULT+") -> Lt(1,N) -> BetaAt(wb,wc,0,z) -> "+INITIAL,
}
HELPER_TARGET_SHA256 = {
    "diagonal_product":"f66c7c696a3ea7ced291250ff70035cd52df0e2442b681e5702b92150f1788bf",
    "coefficient_one":"a5e5b32746f221cef60ac77448b375de65a8b5903e59fe7811cf8bc4ac016169",
    "fold_constant":"ce33d48a9f39b09b3c05a4c26582b2e114fa3edf87cf58f92052c3a92db325f7",
    "initial":"4114a7997a13f1791f483474a09a347c6d0313cc5ac251f868b9792e0bf93ac4",
}
COMPOSITION_ARCHIVE = dict(case="CV028",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-composition-recurrence-v1/generation-process.json.gz",
    bytes=69865,sha256="e2548e38a86ef1d83e10bdeeadce2f960b9394b772152b2f0a46b1059b3367a0",
    raw_bytes=1875555,raw_sha256="662dc7319d7e38de7d95199cc3161836338ddaf7462f71662c117d892357d6a8",
    bundle_bytes=1149748,bundle_sha256="c29b4cd038b31a9cec9ead465584d49e015dc18993c8d71ddb849b591b070a89",
    nodes=245,root=244,target_ast_sha256="52788665088b222b10bd5663fc56a1708052b6dff8d6bda63f6719cae2553927")
ARCHIVES = (COMPOSITION_ARCHIVE,RECURRENCE_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:COMPOSITION_ENDPOINTS[name] for name in ("mul_assoc","mul_comm","mul_cancel","zero_le","succ_le_succ","beta_exists","row_decode")},
    **{name:PERIODIC_ENDPOINTS[name] for name in ("zero_add","beta_unique","one_mul","le_refl","le_succ","le_trans","diagonal_entry","term_unique","coefficient_exists")},
    "mul_one":"forall a. a*1=a","mul_zero_left":"forall a. 0*a=0",
    "sum_decompose":SUM_ENDPOINTS["sum_decompose"],"sum_one":SUM_HELPERS["sum_one"],
    "lower":PERIODIC_HELPERS["lower"],"unpad":PERIODIC_HELPERS["unpad"],
    "trace_unit":POWER_HELPERS["trace_unit"],"unit_zero":UNIT_HELPERS["unit_zero"],
    "weighted_zero":FOLD_HELPERS["weighted_zero"],"weighted_graph":FOLD_HELPERS["weighted_graph"],"weighted_value":FOLD_HELPERS["weighted_value"],
    "vanishing":VANISHING_SOURCE,"prefix_zero":ATANH_HELPERS["prefix_zero"],
    "pattern":COMPOSITION_HELPERS["pattern"],"composition_exists":COMPOSITION_SOURCE,"solution":SOLUTION_SOURCE,
}
HELPER_DEPENDENCIES = {
    "diagonal_product":("beta_exists","diagonal_entry","term_unique"),
    "coefficient_one":("diagonal_product","sum_decompose","sum_one","beta_unique","lower","zero_add","mul_zero_left","le_refl","le_succ"),
    "fold_constant":("row_decode","beta_exists","trace_unit","unit_zero","unpad","weighted_zero","weighted_graph","weighted_value","vanishing","zero_le","succ_le_succ","le_refl","le_succ","le_trans","zero_add","mul_one"),
    "initial":("beta_exists","coefficient_exists","prefix_zero","fold_constant","lower","le_refl","zero_le","pattern","coefficient_one","one_mul","mul_comm","mul_assoc","mul_cancel"),
    "CV029":("composition_exists","beta_exists","initial","solution"),
}


class CompositionCoefficientsError(ValueError):
    """Changed actual initial value, width bound, computation or proof body."""


def definition_registry():
    result = dict(composition_registry())
    for name,d in recurrence_registry().items():
        if name in result and (result[name].template_formula!=d.template_formula or result[name].stable_id!=d.stable_id):
            raise CompositionCoefficientsError("shared conservative definition mismatch")
        result[name] = d
    return MappingProxyType(result)


def frozen_composition_coefficients_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=1 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CompositionCoefficientsError("CV029 exact constructed composition coefficient target changed")
    return target


def source_contract():
    return dict(code="CV029",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,width_at_least_two_required=True,whole_actual_computation_constructed=True,
        initial_weight_constructed_and_nonzero=True,initial_values_proved=True,
        all_in_range_coefficients_identified=True,recurrence_and_initial_values_are_outputs=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",factorial_quotient_interpretation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def composition_coefficients_source_pins():
    result = composition_recurrence_source_pins()
    expected = {
        "scripts/sqrt2_power_composition_recurrence.py":"8989d3b556c1b00602e75b34807a98b5d730864271edfacf329c6898863f9547",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_composition_coefficients.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CompositionCoefficientsError("composition coefficient source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _diagonal_product(s,registry):
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Mul
    params = ("ab","ac","L","bb","bc","M","I","db","dc","T","j","k","a","b")
    def chosen(t):
        product = Mul(t.term("a"),t.term("b"))
        actual = apply(specialize(t,"diagonal_entry",*t.terms(params[:11]+("v",))),t.hyp("diagonal"),t.hyp("bound"),t.hyp("entry"))
        expected = witness(t.terms(("k","a","b")),conjunction(t.hyp("index"),t.hyp("first"),t.hyp("second"),EqRefl(product)))
        equal = apply(specialize(t,"term_unique",*t.terms(params[:7]+("j","v")),product),actual,expected)
        return _subst(t,registry,"BetaAt(db,dc,j,slot)",equal,t.hyp("entry"))
    return introduce(s,params,("diagonal","bound","index","first","second"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(("db","dc","j"))),("v",),"entry",chosen))


def _coefficient_one(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,AndIntro,CongAdd,EqRefl,OrIntroL
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def summed(t):
        def decomposed(u):
            one,two = Succ(Zero()),Succ(Succ(Zero()))
            N,h,a,b = u.terms(("N","h","a","b"))
            low = apply(specialize(u,"lower",Zero(),N),u.hyp("bound"))
            low_diag = apply(specialize(u,"le_succ",one,one),specialize(u,"le_refl",one))
            first = apply(specialize(u,"diagonal_product",*u.terms(("ab","ac","N","bb","bc","N")),one,*u.terms(D),two,Zero(),one,Zero(),b),
                AndElimL(u.hyp("coefficient_data")),low_diag,specialize(u,"zero_add",one),
                OrIntroL(AndIntro(low,u.hyp("zero_a"))),OrIntroL(AndIntro(u.hyp("bound"),u.hyp("one_b"))))
            first = _subst(u,registry,"BetaAt(db,dc,0,slot)",specialize(u,"mul_zero_left",b),first)
            last = apply(specialize(u,"diagonal_product",*u.terms(("ab","ac","N","bb","bc","N")),one,*u.terms(D),two,one,Zero(),h,a),
                AndElimL(u.hyp("coefficient_data")),specialize(u,"le_refl",two),instantiate(Axiom("PA3"),one),
                OrIntroL(AndIntro(u.hyp("bound"),u.hyp("one_a"))),OrIntroL(AndIntro(low,u.hyp("zero_b"))))
            r0 = apply(specialize(u,"sum_one",*u.terms(D+("r",)),Zero()),field(u.hyp("sum_data"),1,3),first)
            x = apply(specialize(u,"beta_unique",*u.terms(D),one,u.term("x"),Mul(h,a)),field(u.hyp("sum_data"),0,3),last)
            return _chain(field(u.hyp("sum_data"),2,3),CongAdd(r0,x),specialize(u,"zero_add",Mul(h,a)))
        return eliminate(t,apply(specialize(t,"sum_decompose",*t.terms(D),Succ(Zero()),t.term("p")),AndElimR(t.hyp("coefficient_data"))),
            ("x","r"),"sum_data",decomposed)
    return introduce(s,("ab","ac","bb","bc","N","h","a","b","p"),("bound","zero_a","one_a","zero_b","one_b","coefficient"),lambda t:
        eliminate(t,t.hyp("coefficient"),D,"coefficient_data",summed))


def _fold_constant(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndIntro,CongAdd,CongMul,EqRefl,Ind,OrIntroL
    from peano_lab.kernel.terms import Mul,Succ,Zero
    params = ("K",)+F+("a","w0")
    premises = ("power","trace","bound","row","entry","weight0")
    def base(t):
        def chosen(u):
            H,K,a,w0 = u.terms(("H","K","a","w0"))
            unit = apply(specialize(u,"trace_unit",*u.terms(("ab","ac","L","H")+P+("K",)+U)),u.hyp("power"),u.hyp("power_row"))
            unit_pad = apply(specialize(u,"unit_zero",*u.terms(U+("H",))),unit,u.hyp("width"))
            unit_value = apply(specialize(u,"unpad",*u.terms(U+("H",)),Zero(),Succ(Zero())),u.hyp("width"),unit_pad)
            zeros = apply(specialize(u,"weighted_zero",*u.terms(("H",)+W+P+Q),Succ(K),*u.terms(V)),u.hyp("trace"),u.hyp("zero_row"))
            zero_value = apply(instantiate(zeros,Zero()),u.hyp("width"))
            bound = apply(specialize(u,"succ_le_succ",Zero(),K),specialize(u,"zero_le",K))
            graph = apply(specialize(u,"weighted_graph",*u.terms(("H",)+W+P+Q),Succ(K),Zero(),*u.terms(U+V+F),w0),
                u.hyp("trace"),bound,u.hyp("power_row"),u.hyp("zero_row"),u.hyp("row"),u.hyp("weight0"))
            value = apply(specialize(u,"weighted_value",*u.terms(V+U+F),H,w0,Zero(),Zero(),Succ(Zero()),a),graph,u.hyp("width"),zero_value,unit_value,u.hyp("entry"))
            return _chain(value,CongAdd(EqRefl(Zero()),specialize(u,"mul_one",w0)),specialize(u,"zero_add",w0))
        return eliminate(t,specialize(t,"row_decode",*t.terms(P),Zero()),U,"power_row",lambda u:
            eliminate(u,specialize(u,"row_decode",*u.terms(Q),Zero()),V,"zero_row",chosen))
    def successor(t):
        def chosen(u):
            k,K,H,a,b,c,w,w0 = u.terms(("k","K","H","a","b","c","w","w0"))
            old_bound = apply(specialize(u,"le_trans",k,Succ(k),K),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            previous = apply(specialize(u,"IH",K,*u.terms(V),b,w0),u.hyp("power"),u.hyp("trace"),old_bound,u.hyp("old_row"),u.hyp("old_value"),u.hyp("weight0"))
            vanishing = apply(specialize(u,"vanishing",*u.terms(("ab","ac","L","H")+P)),u.hyp("zero"))
            zeros = apply(instantiate(vanishing,Succ(k),K,*u.terms(U)),u.hyp("power"),u.hyp("bound"),u.hyp("power_row"))
            bound0 = apply(specialize(u,"succ_le_succ",Zero(),k),specialize(u,"zero_le",k))
            c0 = apply(instantiate(zeros,Zero(),c),bound0,OrIntroL(AndIntro(u.hyp("width"),u.hyp("power_value"))))
            next_bound = apply(specialize(u,"succ_le_succ",Succ(k),K),u.hyp("bound"))
            graph = apply(specialize(u,"weighted_graph",*u.terms(("H",)+W+P+Q),Succ(K),Succ(k),*u.terms(U+V+F),w),
                u.hyp("trace"),next_bound,u.hyp("power_row"),u.hyp("old_row"),u.hyp("row"),u.hyp("weight"))
            value = apply(specialize(u,"weighted_value",*u.terms(V+U+F),H,w,Zero(),b,c,a),graph,u.hyp("width"),u.hyp("old_value"),u.hyp("power_value"),u.hyp("entry"))
            return _chain(value,CongAdd(EqRefl(b),CongMul(EqRefl(w),c0)),CongAdd(EqRefl(b),instantiate(Axiom("PA5"),w)),instantiate(Axiom("PA3"),b),previous)
        return eliminate(t,specialize(t,"row_decode",*t.terms(P),Succ(t.term("k"))),U,"power_row",lambda u:
            eliminate(u,specialize(u,"row_decode",*u.terms(Q),Succ(u.term("k"))),V,"old_row",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(W),Succ(v.term("k"))),("w",),"weight",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(V),Zero()),("b",),"old_value",lambda x:
                        eliminate(x,specialize(x,"beta_exists",*x.terms(U),Zero()),("c",),"power_value",chosen)))))
    motive = target
    for _ in FOLD_FIXED:
        motive = motive.body
    motive = motive.right.right.body
    return introduce(s,FOLD_FIXED,("zero","width"),lambda t:
        Ind(motive,introduce(t,params,premises,base),introduce(t,("k",),("IH",),lambda u:introduce(u,params,premises,successor))))


def _initial(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        N,d,z,c0,c1,v = t.terms(("N","d","z","c0","c1","v"))
        one,two = Succ(Zero()),Succ(Succ(Zero()))
        bound0 = apply(specialize(t,"lower",Zero(),N),t.hyp("bound"))
        input_zero = apply(specialize(t,"prefix_zero",*t.terms(("d","ab","ac","N"))),field(t.hyp("data"),1,10))
        constant = apply(specialize(t,"fold_constant",*t.terms(A),N,*t.terms(P+W+Q)),input_zero,bound0)
        c0z = apply(instantiate(constant,N,N,*t.terms(C),c0,z),field(t.hyp("data"),5,10),field(t.hyp("data"),6,10),specialize(t,"le_refl",N),
            field(t.hyp("data"),7,10),t.hyp("value0"),t.hyp("weight0"))
        first = _subst(t,registry,"BetaAt(cb,cc,0,slot)",c0z,t.hyp("value0"))
        pattern = apply(specialize(t,"pattern",*t.terms(("d","ab","ac","N","db","dc"))),field(t.hyp("data"),1,10),field(t.hyp("data"),4,10))
        ea0,ea1 = apply(field(pattern,0,3),bound0),apply(field(pattern,1,3),t.hyp("bound"))
        cv = apply(specialize(t,"coefficient_one",*t.terms(D+C),N,Mul(two,d),z,c1,v),t.hyp("bound"),ea0,ea1,first,t.hyp("value1"),t.hyp("coefficient"))
        euler = apply(instantiate(field(t.hyp("data"),8,10),one,c1,v),t.hyp("bound"),t.hyp("value1"),t.hyp("coefficient"))
        equation = _chain(CongMul(EqRefl(d),EqSym(specialize(t,"one_mul",c1))),euler,cv,
            CongMul(specialize(t,"mul_comm",two,d),EqRefl(z)),specialize(t,"mul_assoc",d,two,z))
        c1z = apply(specialize(t,"mul_cancel",d,c1,Mul(two,z)),field(t.hyp("data"),0,10),equation)
        second = _subst(t,registry,"BetaAt(cb,cc,1,slot)",c1z,t.hyp("value1"))
        nonzero = apply(instantiate(field(t.hyp("data"),3,10),Zero(),z),specialize(t,"zero_le",N),t.hyp("weight0"),field(t.hyp("data"),0,10))
        return conjunction(first,second,nonzero)
    return introduce(s,("N",)+OUTPUTS,("data","bound","weight0"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(C),Zero()),("c0",),"value0",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(C),Succ(Zero())),("c1",),"value1",lambda v:
                eliminate(v,specialize(v,"coefficient_exists",*v.terms(EA+C+("N",)),Succ(Zero())),("v",),"coefficient",finish))))


def _root(s):
    from peano_lab.kernel.terms import Zero
    def chosen(t):
        def initial_at(u):
            return apply(specialize(u,"initial",*u.terms(("N",)+OUTPUTS)),u.hyp("data"),u.hyp("bound"),u.hyp("weight0"))
        def recurrence_at(u):
            initial = initial_at(u)
            return conjunction(field(initial,0,3),field(initial,1,3),field(u.hyp("data"),9,10))
        def solution(u):
            return apply(specialize(u,"solution",*u.terms(C+("N","z","i","a"))),recurrence_at(u),u.hyp("index"),u.hyp("value"))
        all_values = introduce(t,("i","a"),("index","value"),solution)
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("data"),t.hyp("weight0"),field(initial_at(t),2,3),recurrence_at(t),all_values))
    return introduce(s,("N",),("bound",),lambda t:
        eliminate(t,specialize(t,"composition_exists",t.term("N")),COMPUTATION_OUTPUTS,"data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(W),Zero()),("z",),"weight0",chosen)))


def prove_composition_coefficients(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"diagonal_product":lambda s:_diagonal_product(s,registry),"coefficient_one":lambda s:_coefficient_one(s,registry),
        "fold_constant":lambda s:_fold_constant(s,parse_named(HELPER_SOURCES["fold_constant"],registry=registry)),
        "initial":lambda s:_initial(s,registry),"CV029":_root}
    return assemble_actual_certificate(code="CV029",target=frozen_composition_coefficients_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=composition_coefficients_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
