"""CV026: the actual Euler table of the finite odd reciprocal coefficients.

Construct the Euler table, prove its two initial values when in range, and
prove period two throughout its domain. All parity separation uses actual
division uniqueness. No analytic derivative or logarithm identity is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_atanh_coefficients import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,definition_registry as atanh_registry,
    atanh_coefficients_source_pins,HELPER_SOURCES as ATANH_HELPERS,
)
from sqrt2_power_euler_product import (
    definition_registry as euler_registry,euler_product_source_pins,
    HELPER_SOURCES as EULER_HELPERS,
)
from sqrt2_power_series_power_euler import EULER_ARCHIVE
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst

SCHEMA = "sqrt2-power-atanh-euler-v1"
FIXED = ("d","ab","ac","N","db","dc")
PREFIX = "NatAtanhPrefix(d,ab,ac,N)"
EULER = "NatEulerPrefix(ab,ac,db,dc,N)"
ZERO = "Lt(0,N) -> BetaAt(db,dc,0,0)"
ONE = "Lt(1,N) -> BetaAt(db,dc,1,2*d)"
PERIOD = "forall i a b. Lt(S(S i),N) -> BetaAt(db,dc,i,a) -> BetaAt(db,dc,S(S i),b) -> a=b"
NAMED_SOURCE = "forall d ab ac N. "+PREFIX+" -> exists db dc. "+EULER+" /\\ (("+ZERO+") /\\ (("+ONE+") /\\ ("+PERIOD+")))"
TARGET_SHA256 = "5a9b991ec4dccaeb1d26ec04fa722f7dd24100442b583d871f9cb4b5887431b2"
HELPER_SOURCES = {
    "even_not_odd":"forall j k. 2*j=S(2*k) -> false",
    "double_succ":"forall j. 2*(S j)=S(S(2*j))",
    "even_entry":"forall "+" ".join(FIXED+("j","a"))+". "+PREFIX+" -> "+EULER+" -> Lt(2*j,N) -> BetaAt(db,dc,2*j,a) -> a=0",
    "odd_entry":"forall "+" ".join(FIXED+("j","a"))+". "+PREFIX+" -> "+EULER+" -> Lt(S(2*j),N) -> BetaAt(db,dc,S(2*j),a) -> a=2*d",
    "period":"forall "+" ".join(FIXED+("i","a","b"))+". "+PREFIX+" -> "+EULER+" -> Lt(S(S i),N) -> BetaAt(db,dc,i,a) -> BetaAt(db,dc,S(S i),b) -> a=b",
}
HELPER_TARGET_SHA256 = {
    "even_not_odd":"a411cd2a3db4b710c5d7b465490e6222508c99dc6ea60b278a6fe10163f4300d",
    "double_succ":"ccc150bd5bceb14b4d470aa2d53539025520b3e934e83667b5e133c5b268bb1c",
    "even_entry":"bcd81d416007f2c71a85091f117dfeaa638e8d0932294280a81c027a0560c489",
    "odd_entry":"a0d421d7e77fc83410947cebd785fed297f676f950213e649a9d2f4ad77ac898",
    "period":"e7b28e4b6994c43de4c43d3efa306684f3a2ab9032914d0e3dddb81753f702aa",
}
ATANH_ARCHIVE = dict(case="CV025",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-atanh-coefficients-v1/generation-process.json.gz",
    bytes=19131,sha256="56d2ead6b78500ead3fd14dbd7e252b7310b31b163b5be133743f2ee295be216",
    raw_bytes=277456,raw_sha256="b7c31f42b030b52747e7f5d0d6e04157e3843df68232ab1af3f8283b1d23943b",
    bundle_bytes=164433,bundle_sha256="13c0d9f6839971d10e598ca6718963146822e77ed913e89d536ffa541e01f441",
    nodes=108,root=107,target_ast_sha256="6a235e46d7ff57ccd23bfc381f5c48d024d739de8f78abded4fd58a37aea8dbd")
ARCHIVES = (ATANH_ARCHIVE,EULER_ARCHIVE)
ENDPOINT_SOURCES = {
    "succ_ne_zero":"forall a. ~S a=0",
    "le_refl":"forall a. Le(a,a)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "division_unique":"forall d n q r p s. n=d*q+r -> Lt(r,d) -> n=d*p+s -> Lt(s,d) -> q=p /\\ r=s",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "parity":ATANH_HELPERS["parity"],
    "euler_exists":EULER_HELPERS["euler_exists"],
}
HELPER_DEPENDENCIES = {
    "even_not_odd":("division_unique","le_refl","le_succ","succ_ne_zero"),
    "double_succ":(),
    "even_entry":("beta_exists","beta_unique","even_not_odd"),
    "odd_entry":("beta_exists","beta_unique","even_not_odd"),
    "period":("parity","double_succ","le_refl","le_succ","le_trans","even_entry","odd_entry"),
    "CV026":("euler_exists","beta_exists","even_entry","odd_entry","period"),
}


class AtanhEulerError(ValueError):
    """Changed finite coefficient premise, output, source or proof data."""


def definition_registry():
    result = dict(atanh_registry())
    for name,d in euler_registry().items():
        if name in result and (result[name].template_formula!=d.template_formula or result[name].stable_id!=d.stable_id):
            raise AtanhEulerError("shared conservative definition mismatch")
        result[name] = d
    return MappingProxyType(result)


def frozen_atanh_euler_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=4 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise AtanhEulerError("CV026 exact constructed Euler pattern target changed")
    return target


def source_contract():
    return dict(code="CV026",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,actual_atanh_prefix_required=True,actual_euler_table_constructed=True,
        initial_values_require_in_range=True,period_two_proved_in_range=True,zero_denominator_allowed=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",logarithm_identity=False,
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def atanh_euler_source_pins():
    result = atanh_coefficients_source_pins()
    for name,pin in euler_product_source_pins().items():
        if name in result and result[name]!=pin:
            raise AtanhEulerError("source dependency disagreement")
        result[name] = pin
    expected = {
        "scripts/sqrt2_power_atanh_coefficients.py":"f933ef2b4a35fa6bfe67eabb9279b200a27dcb9a32904b1c4b689b8528386abd",
        "scripts/sqrt2_power_euler_product.py":"c26512518de941c9f8c54bfe682732d601158748f25955166b3ea6d8290afa10",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_atanh_euler.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise AtanhEulerError("atanh Euler source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _even_not_odd(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimR,CongS,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        zero,one,two = Zero(),Succ(Zero()),Succ(Succ(Zero()))
        j,k = t.terms(("j","k"))
        first = EqSym(instantiate(Axiom("PA3"),Mul(two,j)))
        one_plus = _chain(instantiate(Axiom("PA4"),Mul(two,k),zero),CongS(instantiate(Axiom("PA3"),Mul(two,k))))
        second = _chain(t.hyp("equation"),EqSym(one_plus))
        bound0 = apply(specialize(t,"le_succ",one,one),specialize(t,"le_refl",one))
        unique = apply(specialize(t,"division_unique",two,Mul(two,j),j,zero,k,one),first,bound0,second,specialize(t,"le_refl",two))
        return apply(specialize(t,"succ_ne_zero",zero),EqSym(AndElimR(unique)))
    return introduce(s,("j","k"),("equation",),finish)


def _double_succ(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongS
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        one,two = Succ(Zero()),Succ(Succ(Zero()))
        x = Mul(two,t.term("j"))
        return _chain(instantiate(Axiom("PA6"),two,t.term("j")),instantiate(Axiom("PA4"),x,one),
            CongS(instantiate(Axiom("PA4"),x,Zero())),CongS(CongS(instantiate(Axiom("PA3"),x))))
    return introduce(s,("j",),(),finish)


def _entry(s,odd):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,BotElim,CongMul,EqRefl,EqSym,OrElim
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def index(t):
        value = Mul(Succ(Succ(Zero())),t.term("j"))
        return Succ(value) if odd else value
    def chosen(t):
        i,u = index(t),t.term("u")
        coefficient = apply(specialize(t,"prefix",i,u),t.hyp("bound"),t.hyp("input"))
        def branch(v,is_odd):
            def decoded(w):
                # Rebuild terms and the equality in the enlarged existential scope.
                iw,aw,uw = index(w),w.term("a"),w.term("u")
                dw = apply(specialize(w,"euler",iw,uw),w.hyp("bound"),w.hyp("input"))
                equal = apply(specialize(w,"beta_unique",*w.terms(("db","dc")),iw,aw,Mul(iw,uw)),w.hyp("entry"),dw)
                if odd!=is_odd:
                    j,k = w.terms(("j","k"))
                    if odd:
                        proof = apply(specialize(w,"even_not_odd",k,j),EqSym(AndElimL(w.hyp("coefficient_data"))))
                    else:
                        proof = apply(specialize(w,"even_not_odd",j,k),AndElimL(w.hyp("coefficient_data")))
                    return BotElim(proof)
                if odd:
                    return _chain(equal,AndElimR(w.hyp("coefficient_data")))
                return _chain(equal,CongMul(EqRefl(iw),AndElimR(w.hyp("coefficient_data"))),instantiate(Axiom("PA5"),iw))
            return eliminate(v,v.hyp("branch"),("k",),"coefficient_data",decoded)
        return OrElim(coefficient,branch(t.hypothesis("branch"),False),branch(t.hypothesis("branch"),True))
    return introduce(s,FIXED+("j","a"),("prefix","euler","bound","entry"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(("ab","ac")),index(t)),("u",),"input",chosen))


def _period(s,registry):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongS,EqSym,EqTrans,OrElim
    from peano_lab.kernel.terms import Succ
    def branch(t,odd):
        def decoded(u):
            i,N,j = u.terms(("i","N","j"))
            small = apply(specialize(u,"le_succ",Succ(i),Succ(i)),specialize(u,"le_refl",Succ(i)))
            small = apply(specialize(u,"le_succ",Succ(i),Succ(Succ(i))),small)
            bound = apply(specialize(u,"le_trans",Succ(i),Succ(Succ(Succ(i))),N),small,u.hyp("bound"))
            next_form = EqSym(specialize(u,"double_succ",j))
            if odd:
                next_form = CongS(next_form)
            next_form = _chain(CongS(CongS(u.hyp("index_form"))),next_form)
            left_bound = _subst(u,registry,"Lt(slot,N)",u.hyp("index_form"),bound)
            right_bound = _subst(u,registry,"Lt(slot,N)",next_form,u.hyp("bound"))
            left_entry = _subst(u,registry,"BetaAt(db,dc,slot,a)",u.hyp("index_form"),u.hyp("first"))
            right_entry = _subst(u,registry,"BetaAt(db,dc,slot,b)",next_form,u.hyp("second"))
            name = "odd_entry" if odd else "even_entry"
            left = apply(specialize(u,name,*u.terms(FIXED),j,u.term("a")),u.hyp("prefix"),u.hyp("euler"),left_bound,left_entry)
            right = apply(specialize(u,name,*u.terms(FIXED),Succ(j),u.term("b")),u.hyp("prefix"),u.hyp("euler"),right_bound,right_entry)
            return EqTrans(left,EqSym(right))
        return eliminate(t,t.hyp("parity_case"),("j",),"index_form",decoded)
    return introduce(s,FIXED+("i","a","b"),("prefix","euler","bound","first","second"),lambda t:
        OrElim(specialize(t,"parity",t.term("i")),branch(t.hypothesis("parity_case"),False),branch(t.hypothesis("parity_case"),True)))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongS,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        def boundary(u,odd):
            index = Succ(Zero()) if odd else Zero()
            def decoded(v):
                equality = instantiate(Axiom("PA5"),Succ(Succ(Zero())))
                if odd:
                    equality = CongS(equality)
                index_eq = EqSym(equality)
                bound = _subst(v,registry,"Lt(slot,N)",index_eq,v.hyp("bound"))
                entry = _subst(v,registry,"BetaAt(db,dc,slot,a)",index_eq,v.hyp("value"))
                eq = apply(specialize(v,"odd_entry" if odd else "even_entry",*v.terms(FIXED),Zero(),v.term("a")),
                    v.hyp("prefix"),v.hyp("euler"),bound,entry)
                return _subst(v,registry,"BetaAt(db,dc,"+("1" if odd else "0")+",slot)",eq,v.hyp("value"))
            return eliminate(u,specialize(u,"beta_exists",*u.terms(("db","dc")),index),("a",),"value",decoded)
        zero = introduce(t,(),("bound",),lambda u:boundary(u,False))
        one = introduce(t,(),("bound",),lambda u:boundary(u,True))
        period = introduce(t,("i","a","b"),("bound","first","second"),lambda u:
            apply(specialize(u,"period",*u.terms(FIXED+("i","a","b"))),*(u.hyp(h) for h in ("prefix","euler","bound","first","second"))))
        return witness(t.terms(("db","dc")),conjunction(t.hyp("euler"),zero,one,period))
    return introduce(s,FIXED[:4],("prefix",),lambda t:
        eliminate(t,specialize(t,"euler_exists",*t.terms(("ab","ac","N"))),("db","dc"),"euler",chosen))


def prove_atanh_euler(*,limits=None):
    registry = definition_registry()
    factories = {"even_not_odd":_even_not_odd,"double_succ":_double_succ,
        "even_entry":lambda s:_entry(s,False),"odd_entry":lambda s:_entry(s,True),
        "period":lambda s:_period(s,registry),"CV026":lambda s:_root(s,registry)}
    return assemble_actual_certificate(code="CV026",target=frozen_atanh_euler_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=atanh_euler_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
