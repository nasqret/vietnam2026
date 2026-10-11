"""CV028: construct the actual finite composition and prove its recurrence.

Construct inner coefficients, positive denominator, reverse weights, powers,
weighted accumulation and terminal row. Its actual coefficient values satisfy
(i+2)*C[i+2]=i*C[i]+2*C[i+1] in range. Initial values, factorial interpretation
and analytic limits remain separate gates; no recurrence is an input premise.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_denominator_euler import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,definition_registry as denominator_registry,
    denominator_euler_source_pins,NAMED_SOURCE as DENOMINATOR_SOURCE,
    ENDPOINT_SOURCES as DENOMINATOR_ENDPOINTS,coefficient,positive,joined,
)
from sqrt2_power_atanh_euler import (
    definition_registry as atanh_registry,atanh_euler_source_pins,
    HELPER_SOURCES as ATANH_HELPERS,ATANH_ARCHIVE,
)
from sqrt2_power_atanh_coefficients import NAMED_SOURCE as ATANH_SOURCE
from sqrt2_power_periodic_convolution import (
    definition_registry as periodic_registry,periodic_convolution_source_pins,
    NAMED_SOURCE as PERIODIC_SOURCE,HELPER_SOURCES as PERIODIC_HELPERS,
)
from sqrt2_power_logexp_recurrence import logexp_recurrence_source_pins
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst

SCHEMA = "sqrt2-power-composition-recurrence-v1"
A = ("ab","ac","N")
D = ("db","dc")
EA = D+("N",)
W,Z = ("wb","wc"),("yb","yc")
P = ("pb","pc","qb","qc")
Q,R = ("tb","tc","vb","vc"),("rb","rc","sb","sc")
C = ("cb","cc")
OUTPUTS = ("d",)+A[:2]+W+D+P+Q+C
PREFIX = "NatAtanhPrefix(d,ab,ac,N)"
EULER = "NatEulerPrefix(ab,ac,db,dc,N)"
WEIGHTS = "NatExpWeightTable(d,N,wb,wc)"
POWER = "NatPowerTrace("+",".join(A+("N",)+P+("N",))+")"
TRACE = "NatWeightedSeriesTrace("+",".join(("N",)+W+P+Q+("S N",))+")"
ROW = "NatPowerRow("+",".join(Q+("S N",)+C)+")"
ZERO = "Lt(0,N) -> BetaAt(db,dc,0,0)"
ONE = "Lt(1,N) -> BetaAt(db,dc,1,2*d)"
PERIOD = "forall j x y. Lt(S(S j),N) -> BetaAt(db,dc,j,x) -> BetaAt(db,dc,S(S j),y) -> x=y"
EQUATION = "forall j x y. Lt(j,N) -> BetaAt(cb,cc,j,x) -> "+coefficient(EA,C+("N",),"j","y")+" -> d*(j*x)=y"
RECURRENCE = "forall i a b c. Lt(S(S i),N) -> BetaAt(cb,cc,i,a) -> BetaAt(cb,cc,S i,b) -> BetaAt(cb,cc,S(S i),c) -> (S(S i))*c=i*a+2*b"
RESULT = joined(("~d=0",PREFIX,WEIGHTS,"("+positive(W)+")",EULER,POWER,TRACE,ROW,"("+EQUATION+")","("+RECURRENCE+")"))
NAMED_SOURCE = "forall N. exists "+" ".join(OUTPUTS)+". "+RESULT
TARGET_SHA256 = "52788665088b222b10bd5663fc56a1708052b6dff8d6bda63f6719cae2553927"
HELPER_SOURCES = {
    "pattern":"forall d ab ac N db dc. "+PREFIX+" -> "+EULER+" -> ("+ZERO+") /\\ (("+ONE+") /\\ ("+PERIOD+"))",
    "recurrence":"forall d db dc cb cc N i a b c. ~d=0 -> ("+ZERO+") -> ("+ONE+") -> ("+PERIOD+") -> ("+EQUATION+") -> Lt(S(S i),N) -> BetaAt(cb,cc,i,a) -> BetaAt(cb,cc,S i,b) -> BetaAt(cb,cc,S(S i),c) -> (S(S i))*c=i*a+2*b",
}
HELPER_TARGET_SHA256 = {
    "pattern":"3477b76559e43261a056c08dff615532eee442e23684b2d529d56df30805ad58",
    "recurrence":"64e91fae5af95803253743cf558e208c36f910566555e5bedf85c74bf90493ce",
}
DENOMINATOR_ARCHIVE = dict(case="CV024",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-denominator-euler-v1/generation-process.json.gz",
    bytes=63877,sha256="23a04f0cf0e47540aa31d872d3f2d8d4fe5d85b2695b68808462ce8bf09e98b4",
    raw_bytes=1729187,raw_sha256="dd1347d1e39673d86915adc3d06fa3a51a7d44aa7d6dcb98a9acb51d0c707774",
    bundle_bytes=1059704,bundle_sha256="e727513a9752a1f0ca45550447de9ad92c582a4d221c1c8380146aa1aae068c4",
    nodes=224,root=223,target_ast_sha256="b3b638e846a53d3cee1e16e8f927226ab00da021924e9c98b2978fc3a534989f")
ATANH_EULER_ARCHIVE = dict(case="CV026",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-atanh-euler-v1/generation-process.json.gz",
    bytes=20431,sha256="9be4c48a03d10828091bee7639b957ac86f3f5a0c8e8ff52afa6d49ad48e8050",
    raw_bytes=302046,raw_sha256="ec82ee992dc70bb7854997d767365dccc42ea97fd78c438dfd48f0741748e4d3",
    bundle_bytes=177857,bundle_sha256="9395c1f7fc2f6eb5e13d52f715f983964060b080a6743960bf1787349b809ca9",
    nodes=111,root=110,target_ast_sha256="5a9b991ec4dccaeb1d26ec04fa722f7dd24100442b583d871f9cb4b5887431b2")
PERIODIC_ARCHIVE = dict(case="CV027",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-periodic-convolution-v1/generation-process.json.gz",
    bytes=26912,sha256="8a9d1a24389fe4fe6fbca9b7a3638dee7435e7d4352c4d5b0ebb5f99e6063182",
    raw_bytes=512354,raw_sha256="69eae4da6a44bea0178c9b748dae5610a873a68be6f0826fb172a2b543d4256c",
    bundle_bytes=309165,bundle_sha256="48a775c9d61abf6bb9adf64eb39d170b6694988e0a2ee2dc7b654a0cca714b2f",
    nodes=137,root=136,target_ast_sha256="3850a7a9f34d3796dd4b8e08f3a80925758444d026b1c0ce93c108108af94dec")
RECURRENCE_ARCHIVE = dict(case="CV002",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-logexp-recurrence-v2/generation-process.json.gz",
    bytes=8543,sha256="4d0ea1f582fa32eea907f0bd1c1a14b2d55e5910dd0f8b011a424840adce39dd",
    raw_bytes=85372,raw_sha256="67851ea4942b998262e30810d830762d15a0f613e52ed96501f842f8eec3230d",
    bundle_bytes=46824,bundle_sha256="3e66d595d6329dd0d7fd3cb22da62e34cce7ec4cf22f89624bec0f6917f94db1",
    nodes=31,root=30,target_ast_sha256="798208f708ff6a1d8a5d5d279698ac3f19608a2c01a96bd5059fa4b582a9520a")
ARCHIVES = (DENOMINATOR_ARCHIVE,ATANH_ARCHIVE,ATANH_EULER_ARCHIVE,PERIODIC_ARCHIVE,RECURRENCE_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:DENOMINATOR_ENDPOINTS[name] for name in ("mul_assoc","mul_comm","beta_exists","row_decode")},
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "mul_cancel":"forall a b c. ~a=0 -> a*b=a*c -> b=c",
    "zero_le":"forall a. Le(0,a)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "below":PERIODIC_HELPERS["below"],"lower":PERIODIC_HELPERS["lower"],
    "even_entry":ATANH_HELPERS["even_entry"],"odd_entry":ATANH_HELPERS["odd_entry"],"period":ATANH_HELPERS["period"],
    "atanh_exists":ATANH_SOURCE,"denominator_euler":DENOMINATOR_SOURCE,"periodic_convolution":PERIODIC_SOURCE,
}
HELPER_DEPENDENCIES = {
    "pattern":("beta_exists","even_entry","odd_entry","period"),
    "recurrence":("below","lower","zero_le","succ_le_succ","periodic_convolution","mul_assoc","mul_comm","mul_add","mul_cancel"),
    "CV028":("atanh_exists","denominator_euler","row_decode","pattern","recurrence"),
}


class CompositionRecurrenceError(ValueError):
    """Changed actual composition data, construction or recurrence target."""


def definition_registry():
    result = dict(denominator_registry())
    for supplied in (atanh_registry(),periodic_registry()):
        for name,d in supplied.items():
            if name in result and (result[name].template_formula!=d.template_formula or result[name].stable_id!=d.stable_id):
                raise CompositionRecurrenceError("shared conservative definition mismatch")
            result[name] = d
    return MappingProxyType(result)


def frozen_composition_recurrence_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CompositionRecurrenceError("CV028 exact constructed composition recurrence target changed")
    return target


def source_contract():
    return dict(code="CV028",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,positive_inner_denominator_and_actual_coefficients_constructed=True,
        actual_weights_powers_accumulation_and_terminal_row_constructed=True,
        denominator_cleared_euler_equation_retained=True,actual_composition_three_term_recurrence=True,
        recurrence_is_input_premise=False,initial_composition_values_proved=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",factorial_quotient_interpretation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def composition_recurrence_source_pins():
    result = denominator_euler_source_pins()
    for supplied in (atanh_euler_source_pins(),periodic_convolution_source_pins(),logexp_recurrence_source_pins()):
        for name,pin in supplied.items():
            if name in result and result[name]!=pin:
                raise CompositionRecurrenceError("source dependency disagreement")
            result[name] = pin
    expected = {
        "scripts/sqrt2_power_denominator_euler.py":"cb58fd61791974d042dc2f0e4871d5ce41394804531ac115cc8904544e78a812",
        "scripts/sqrt2_power_atanh_euler.py":"d24e8fc4fcf12b22f2971877ab3bb55be42991b6b9a34938d99e97920d4cffe2",
        "scripts/sqrt2_power_periodic_convolution.py":"aeb95ee2da8e89f07b421c9e743d2bf87e8a765505d9c919df70b51d3ce2c02d",
        "scripts/sqrt2_power_logexp_recurrence.py":"6a9b36cab2e7589d45b75080d7eb5819f0392f849cc248661e3413115a2a6463",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_composition_recurrence.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CompositionRecurrenceError("composition recurrence source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _pattern(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongS,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    fixed = ("d","ab","ac","N","db","dc")
    def finish(t):
        def boundary(u,odd):
            index = Succ(Zero()) if odd else Zero()
            def decoded(v):
                equality = instantiate(Axiom("PA5"),Succ(Succ(Zero())))
                if odd:
                    equality = CongS(equality)
                index_eq = EqSym(equality)
                bound = _subst(v,registry,"Lt(slot,N)",index_eq,v.hyp("bound"))
                entry = _subst(v,registry,"BetaAt(db,dc,slot,a)",index_eq,v.hyp("value"))
                eq = apply(specialize(v,"odd_entry" if odd else "even_entry",*v.terms(fixed),Zero(),v.term("a")),v.hyp("prefix"),v.hyp("euler"),bound,entry)
                return _subst(v,registry,"BetaAt(db,dc,"+("1" if odd else "0")+",slot)",eq,v.hyp("value"))
            return eliminate(u,specialize(u,"beta_exists",*u.terms(D),index),("a",),"value",decoded)
        zero = introduce(t,(),("bound",),lambda u:boundary(u,False))
        one = introduce(t,(),("bound",),lambda u:boundary(u,True))
        period = introduce(t,("j","x","y"),("bound","first","second"),lambda u:
            apply(specialize(u,"period",*u.terms(fixed+("j","x","y"))),*(u.hyp(h) for h in ("prefix","euler","bound","first","second"))))
        return conjunction(zero,one,period)
    return introduce(s,fixed,("prefix","euler"),finish)


def _recurrence(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def coefficients(t):
        d,i,a,b,c,u,v = t.terms(("d","i","a","b","c","u","v"))
        bound1 = apply(specialize(t,"lower",Succ(i),t.term("N")),t.hyp("bound"))
        bound0 = apply(specialize(t,"lower",i,t.term("N")),bound1)
        first = apply(specialize(t,"equation",i,a,u),bound0,t.hyp("first"),field(t.hyp("coefficients"),0,3))
        second = apply(specialize(t,"equation",Succ(Succ(i)),c,v),t.hyp("bound"),t.hyp("third"),field(t.hyp("coefficients"),1,3))
        two = Succ(Succ(Zero()))
        distributed = _chain(CongMul(specialize(t,"mul_comm",two,d),EqRefl(b)),specialize(t,"mul_assoc",d,two,b))
        identity = _chain(second,field(t.hyp("coefficients"),2,3),CongAdd(EqSym(first),distributed),EqSym(specialize(t,"mul_add",d,Mul(i,a),Mul(two,b))))
        return apply(specialize(t,"mul_cancel",d,Mul(Succ(Succ(i)),c),Add(Mul(i,a),Mul(two,b))),t.hyp("nonzero"),identity)
    def finish(t):
        N,i = t.terms(("N","i"))
        bound0 = apply(specialize(t,"below",Zero(),Succ(Succ(i)),N),specialize(t,"zero_le",Succ(Succ(i))),t.hyp("bound"))
        small1 = apply(specialize(t,"succ_le_succ",Zero(),Succ(i)),specialize(t,"zero_le",Succ(i)))
        bound1 = apply(specialize(t,"below",Succ(Zero()),Succ(Succ(i)),N),small1,t.hyp("bound"))
        zero,one = apply(t.hyp("zero"),bound0),apply(t.hyp("one"),bound1)
        data = apply(specialize(t,"periodic_convolution",*t.terms(D+C+("N","i")),Mul(Succ(Succ(Zero())),t.term("d")),t.term("b")),
            t.hyp("bound"),zero,one,t.hyp("period"),t.hyp("second"))
        return eliminate(t,data,("u","v"),"coefficients",coefficients)
    return introduce(s,("d",)+D+C+("N","i","a","b","c"),("nonzero","zero","one","period","equation","bound","first","second","third"),finish)


def _equation(s):
    from sqrt2_power_native import instantiate
    def entry(t):
        return apply(instantiate(field(t.hyp("composition"),7,8),*t.terms(C+("j","x","y"))),
            t.hyp("row"),t.hyp("index"),t.hyp("value"),t.hyp("coefficient"))
    return introduce(s,("j","x","y"),("index","value","coefficient"),entry)


def _root(s):
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        def recurrence(u):
            pattern = apply(specialize(u,"pattern",*u.terms(("d","ab","ac","N","db","dc"))),field(u.hyp("atanh"),1,3),field(u.hyp("composition"),2,8))
            return apply(specialize(u,"recurrence",*u.terms(("d",)+D+C+("N","i","a","b","c"))),
                field(u.hyp("atanh"),0,3),*(field(pattern,j,3) for j in range(3)),_equation(u),
                *(u.hyp(h) for h in ("bound","first","second","third")))
        rule = introduce(t,("i","a","b","c"),("bound","first","second","third"),recurrence)
        result = conjunction(field(t.hyp("atanh"),0,3),field(t.hyp("atanh"),1,3),
            *(field(t.hyp("composition"),j,8) for j in (0,1,2,3,5)),t.hyp("row"),_equation(t),rule)
        return witness(t.terms(OUTPUTS),result)
    return introduce(s,("N",),(),lambda t:
        eliminate(t,specialize(t,"atanh_exists",t.term("N")),("d","ab","ac"),"atanh",lambda u:
            eliminate(u,apply(specialize(u,"denominator_euler",*u.terms(A+("d","N"))),field(u.hyp("atanh"),2,3)),W+D+P+Z+Q+R,"composition",lambda v:
                eliminate(v,specialize(v,"row_decode",*v.terms(Q),Succ(v.term("N"))),C,"row",chosen))))


def prove_composition_recurrence(*,limits=None):
    registry = definition_registry()
    factories = {"pattern":lambda s:_pattern(s,registry),"recurrence":_recurrence,"CV028":_root}
    return assemble_actual_certificate(code="CV028",target=frozen_composition_recurrence_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=composition_recurrence_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
