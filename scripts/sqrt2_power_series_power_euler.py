"""CV017: Euler differentiation of every actually constructed power table.

At i<H, i*P[k+1][i]=(k+1)*(EA*P[k])[i]. The unconditional root constructs
the input Euler table and all power rows. Its induction uses ordinary checked
unit, product, linearity and associativity bodies. No analytic claim follows.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_convolution_unit import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,assemble_actual_certificate,_subst,
    convolution_unit_source_pins,HELPER_SOURCES as UNIT_HELPERS,
)
from sqrt2_power_series_power_trace import (
    definition_registry as power_registry,HELPER_SOURCES as POWER_HELPERS,
    NAMED_SOURCE as POWER_SOURCE,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_series_power_vanishing import POWER_ARCHIVE
from sqrt2_power_euler_product import (
    definition_registry as euler_registry,euler_product_source_pins,
    HELPER_SOURCES as EULER_HELPERS,coefficient,euler,
)
from sqrt2_power_convolution_associative import (
    convolution_associative_source_pins,HELPER_SOURCES as ASSOC_HELPERS,
)
from sqrt2_power_convolution_linearity import (
    convolution_linearity_source_pins,HELPER_SOURCES as LINEAR_HELPERS,
)

SCHEMA = "sqrt2-power-series-power-euler-v1"
P = ("ab","ac","L","H")
B = ("pb","pc","qb","qc")
D = ("db","dc")
U,V,W = ("ub","uc"),("vb","vc"),("wb","wc")
A,EA = ("ab","ac","L"),("db","dc","L")
EULER = euler(A[:2],D,"L")


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def row(index,codes):
    return "NatPowerRow("+",".join(B+(index,)+codes)+")"


def trace(length="K"):
    return "NatPowerTrace("+",".join(P+B+(length,))+")"


def prefix(left,right,codes,length="H"):
    return "NatConvolutionPrefix("+",".join(left+right+codes+(length,))+")"


ROW_ARGS = ("k",)+U+V+("i","p","t")
ROW_PREMISES = "Lt(k,K) -> "+row("k",U)+" -> "+row("S k",V)+" -> Lt(i,H) -> BetaAt(vb,vc,i,p) -> "+coefficient(EA,U+("H",),"i","t")+" -> i*p=(S k)*t"
INVARIANT = forall(ROW_ARGS,ROW_PREMISES)
NAMED_SOURCE = forall(P+("K",),"exists "+" ".join(D+B)+". "+EULER+" /\\ ("+trace()+" /\\ ("+INVARIANT+"))")
TARGET_SHA256 = "e71ae746c83206309479f65ede0e10c2e11d077b3ac2123df4942475e453d1e6"
SCALE_RELATION = "forall j a b. Lt(j,W) -> BetaAt(xb,xc,j,a) -> BetaAt(yb,yc,j,b) -> b=k*a"
HELPER_SOURCES = {
    "trace_unit":forall(P+B+("K",)+U,trace()+" -> "+row("0",U)+" -> NatUnitPrefix(ub,uc,H)"),
    "trace_step":forall(P+B+("K","k")+U+V,trace()+" -> Lt(k,K) -> "+row("k",U)+" -> "+row("S k",V)+" -> "+prefix(A,U+("H",),V)),
    "prefix_swap":"forall ab ac L bb bc M cb cc N. NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N) -> NatConvolutionPrefix(bb,bc,M,ab,ac,L,cb,cc,N)",
    "coefficient_scale":forall(("xb","xc","yb","yc","W","db","dc","M","k","i","u","v"),"("+SCALE_RELATION+") -> "+coefficient(("xb","xc","W"),("db","dc","M"),"i","u")+" -> "+coefficient(("yb","yc","W"),("db","dc","M"),"i","v")+" -> v=k*u"),
    "power_rule":forall(P+B+D,EULER+" -> "+forall(("k","K")+U+V+("i","p","t"),trace()+" -> "+ROW_PREMISES)),
}
HELPER_TARGET_SHA256 = {
    "trace_unit":"a281439ff17b16ece3351f8a4f4b1617a93c659a34266c74e485f801282c098a",
    "trace_step":"562d8298fc9aabebaf61953a39a7563bbcffacb321eadadf280f5a279c6ff82f",
    "prefix_swap":"4ce1225c0329878f10dd32299911b5c8ddd21965ea7b5f5d393e1cf3ae8140a4",
    "coefficient_scale":"950595785d4333b62d8bb88af1d163999f547252f8340bb0b58050c6bf181896",
    "power_rule":"e96b0ba598518fdd7414820a94ea67c2e8bf63b86d89818de70156d4226cce14",
}
EULER_ARCHIVE = dict(case="CV007",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-euler-product-v1/generation-process.json.gz",
    bytes=23760,sha256="44c32ebfa13c0ff6ff9b6a45b000876ee3a454bccf4df48b599f9881e11515e9",
    raw_bytes=427887,raw_sha256="4e22977bcd8835c43c0ff2b59ff27fbc5a8310d7de827d1a97efe9d0db82012d",
    bundle_bytes=258239,bundle_sha256="140a7b41c2c895ce52fdcec8b9189af18def5d054be512c8a3dffef23bf2b169",
    nodes=123,root=122,target_ast_sha256="f8bff474361b2be3a4a2a9c81b30cdb9c317dd510ffdaf1ac64fa5762046cbea")
ASSOC_ARCHIVE = dict(case="CV014",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-associative-v1/generation-process.json.gz",
    bytes=38261,sha256="9ebf0dd5aac21365451194ceab5f86e488726a04d6a2ff046dad5c8901c3f38b",
    raw_bytes=934531,raw_sha256="e382ab8e56e7e393e47d82d00aa4900c37ac7ca0c45cf366efc5b1a8c4a748a4",
    bundle_bytes=568920,bundle_sha256="82a2a015e265224a899337bc2b375693c9881f2774e68487d87420cdf909478a",
    nodes=168,root=167,target_ast_sha256="a455e5f4420f28921f898952ebc74012686b69749b15192af32727495f22413b")
LINEAR_ARCHIVE = dict(case="CV015",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-linearity-v1/generation-process.json.gz",
    bytes=23851,sha256="adbb9bd4d6d6f54e8c129e8d04258d9865ad7b1f05270319bf538f7e11d37a8e",
    raw_bytes=433223,raw_sha256="58a45976aa411b7a473d9073575fd040e1a4a46c020a0d49b79b3233ad109840",
    bundle_bytes=261414,bundle_sha256="7f4a09006875aad735b0543e6386b8e508c35c8890e2a801ffaf91c14f6dbf84",
    nodes=123,root=122,target_ast_sha256="454dd9464f21bb867fd39a78eebb4d9eabe59aae256c134ab0624e05d8d17f91")
UNIT_ARCHIVE = dict(case="CV016",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-unit-v1/generation-process.json.gz",
    bytes=27945,sha256="4912e071887cff317db168f11fa845dd91845c1f6d61bfc0dfe193db6b359217",
    raw_bytes=548248,raw_sha256="319c1b4a34da1e0f00fb66193c473e4a83e236c7bb223623aefe126f03f07625",
    bundle_bytes=331284,bundle_sha256="354eae0281744eaefdf71202d0e84fd1e9e1ad154f712f8f8969b942294c7c77",
    nodes=142,root=141,target_ast_sha256="80e61d585bc00d1ae1a6ea2c87fb652ee553927823efe339412d1d7e39c7b5d4")
ARCHIVES = (CONVOLUTION_ARCHIVE,POWER_ARCHIVE,EULER_ARCHIVE,ASSOC_ARCHIVE,LINEAR_ARCHIVE,UNIT_ARCHIVE)
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a",
    "one_mul":"forall a. 1*a=a",
    "mul_zero_left":"forall a. 0*a=0",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b",
    "le_refl":"forall a. Le(a,a)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "padding_exists":"forall b c L i. exists a. BetaZeroExtend(b,c,L,i,a)",
    "coefficient_exists":"forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)",
    "coefficient_unique":"forall ab ac L bb bc M i n m. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n) -> NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,m) -> n=m",
    "prefix_exists":"forall ab ac L bb bc M N. exists cb cc. NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N)",
    "prefix_entry":"forall ab ac L bb bc M cb cc N i a. NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N) -> Lt(i,N) -> BetaAt(cb,cc,i,a) -> NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,a)",
    "power_exists":POWER_SOURCE,"row_decode":POWER_HELPERS["decode"],
    "euler_exists":EULER_HELPERS["euler_exists"],"euler_padding":EULER_HELPERS["euler_padding"],
    "product_rule":EULER_HELPERS["product_rule"],
    "coefficient_swap":ASSOC_HELPERS["coefficient_swap"],"associate":ASSOC_HELPERS["associate"],
    "coefficient_linearity":LINEAR_HELPERS["coefficient_linearity"],
    "unit_coefficient":UNIT_HELPERS["unit_coefficient"],
}
HELPER_DEPENDENCIES = {
    "trace_unit":("beta_unique",),"trace_step":("beta_unique",),
    "prefix_swap":("coefficient_swap",),
    "coefficient_scale":("coefficient_linearity","one_mul","mul_zero_left"),
    "power_rule":("trace_unit","trace_step","prefix_entry","padding_exists","euler_padding","unit_coefficient",
        "coefficient_swap","coefficient_unique","one_mul","row_decode","prefix_exists","euler_exists","coefficient_exists",
        "le_refl","le_succ","le_trans","beta_exists","beta_unique","prefix_swap","associate","coefficient_scale","product_rule","add_comm","mul_succ_left"),
    "CV017":("euler_exists","power_exists","power_rule"),
}


class PowerEulerError(ValueError):
    """Changed actual execution, Euler statement, dependency body or bound."""


def definition_registry():
    registry = dict(power_registry())
    for name,d in euler_registry().items():
        if name in registry and (registry[name].template_formula!=d.template_formula or registry[name].stable_id!=d.stable_id):
            raise PowerEulerError("shared conservative definition mismatch")
        registry[name] = d
    return MappingProxyType(registry)


def frozen_series_power_euler_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PowerEulerError("CV017 exact constructed power differentiation target changed")
    return target


def source_contract():
    return dict(code="CV017",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_euler_and_power_tables_constructed=True,
        all_exponents_and_coefficients_below_width=True,arbitrary_input_length=True,
        input_constant_coefficient_need_not_vanish=True,coefficientwise_euler_power_rule=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",exp_composition_recurrence=False,
        analytic_limit_claim=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def series_power_euler_source_pins():
    result = convolution_unit_source_pins()
    for pinned in (euler_product_source_pins(),convolution_associative_source_pins(),convolution_linearity_source_pins()):
        for name,pin in pinned.items():
            if name in result and result[name]!=pin:
                raise PowerEulerError("source dependency disagreement")
            result[name] = pin
    expected = {
        "scripts/sqrt2_power_convolution_unit.py":"d058762fb3641d5bb1e90c764c4581801feeaf0a103901811b3e82dbe3db8f16",
        "scripts/sqrt2_power_convolution_linearity.py":"0dea2d4d67beeb59c9345f35c302ce9a49d1936bd1251ffacb976def7fa93169",
        "scripts/sqrt2_power_euler_product.py":"c26512518de941c9f8c54bfe682732d601158748f25955166b3ea6d8290afa10",
        "scripts/sqrt2_power_convolution_associative.py":"a7a442ad853eeb7c1eb0cbd15b552eb9e7213419d44ed86e1314a7e2f1a1c931",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_series_power_euler.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PowerEulerError("power-rule source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _trace_unit(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Zero
    def decoded(t):
        equal = tuple(apply(specialize(t,"beta_unique",*t.terms(B[2*j:2*j+2]),Zero(),t.term(("zb","zc")[j]),t.term(U[j])),
            field(AndElimL(t.hyp("initial")),j,2),field(t.hyp("row"),j,2)) for j in range(2))
        value = _subst(t,registry,"NatUnitPrefix(slot,zc,H)",equal[0],AndElimR(t.hyp("initial")))
        return _subst(t,registry,"NatUnitPrefix(ub,slot,H)",equal[1],value)
    return introduce(s,P+B+("K",)+U,("trace","row"),lambda t:
        eliminate(t,AndElimL(t.hyp("trace")),("zb","zc"),"initial",decoded))


def _trace_step(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimR
    from peano_lab.kernel.terms import Succ
    def decoded(t):
        result = field(t.hyp("step"),2,3)
        old = ("wb","wc","xb","xc")
        new = U+V
        for position in range(4):
            which,component = divmod(position,2)
            index = t.term("k") if which==0 else Succ(t.term("k"))
            equal = apply(specialize(t,"beta_unique",*t.terms(B[2*component:2*component+2]),index,t.term(old[position]),t.term(new[position])),
                field(field(t.hyp("step"),which,3),component,2),field(t.hyp(("row_u","row_v")[which]),component,2))
            codes = new[:position]+("slot",)+old[position+1:]
            result = _subst(t,registry,prefix(A,codes[:2]+("H",),codes[2:]),equal,result)
        return result
    return introduce(s,P+B+("K","k")+U+V,("trace","range","row_u","row_v"),lambda t:
        eliminate(t,apply(instantiate(AndElimR(t.hyp("trace")),t.term("k")),t.hyp("range")),("wb","wc","xb","xc"),"step",decoded))


def _prefix_swap(s):
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR
    def decoded(t):
        swapped = apply(specialize(t,"coefficient_swap",*t.terms(("ab","ac","L","bb","bc","M","i","a"))),AndElimR(t.hyp("value")))
        return witness((t.term("a"),),AndIntro(AndElimL(t.hyp("value")),swapped))
    return introduce(s,("ab","ac","L","bb","bc","M","cb","cc","N"),("prefix",),lambda t:
        introduce(t,("i",),("bound",),lambda u:
            eliminate(u,apply(specialize(u,"prefix",u.term("i")),u.hyp("bound")),("a",),"value",decoded)))


def _coefficient_scale(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        def pointwise(u):
            ku = Mul(u.term("k"),u.term("a"))
            identity = apply(specialize(u,"scaled",*u.terms(("j","a","c"))),u.hyp("bound"),u.hyp("first"),u.hyp("third"))
            return _chain(specialize(u,"one_mul",u.term("c")),identity,
                EqSym(instantiate(Axiom("PA3"),ku)),CongAdd(EqRefl(ku),EqSym(specialize(u,"mul_zero_left",u.term("b")))))
        points = introduce(t,("j","a","b","c"),("bound","first","second","third"),pointwise)
        identity = apply(specialize(t,"coefficient_linearity",t.term("k"),Zero(),Succ(Zero()),
            *t.terms(("xb","xc","xb","xc","yb","yc","W","db","dc","M","i","u","u","v"))),
            points,t.hyp("source_u"),t.hyp("source_u"),t.hyp("source_v"))
        return _chain(EqSym(specialize(t,"one_mul",t.term("v"))),identity,
            CongAdd(EqRefl(Mul(t.term("k"),t.term("u"))),specialize(t,"mul_zero_left",t.term("u"))),
            instantiate(Axiom("PA3"),Mul(t.term("k"),t.term("u"))))
    return introduce(s,("xb","xc","yb","yc","W","db","dc","M","k","i","u","v"),("scaled","source_u","source_v"),finish)


def _power_rule(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,EqTrans,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    params = ("K",)+U+V+("i","p","t")
    premises = ("trace","range","row_u","row_v","index","entry","coefficient")
    def base(t):
        def value(u):
            i,a,p,tval = u.terms(("i","a","p","t"))
            unit = apply(specialize(u,"trace_unit",*u.terms(P+B+("K",)+U)),u.hyp("trace"),u.hyp("row_u"))
            pref = apply(specialize(u,"trace_step",*u.terms(P+B+("K",)),Zero(),*u.terms(U+V)),
                u.hyp("trace"),u.hyp("range"),u.hyp("row_u"),u.hyp("row_v"))
            actual_p = apply(specialize(u,"prefix_entry",*u.terms(A+U+("H",)+V+("H","i","p"))),pref,u.hyp("index"),u.hyp("entry"))
            left_unit = apply(specialize(u,"unit_coefficient",*u.terms(P+("i",)+U+("a",))),unit,u.hyp("index"),u.hyp("padded"))
            right_unit = apply(specialize(u,"coefficient_swap",*u.terms(U+("H",)+A+("i","a"))),left_unit)
            pa = apply(specialize(u,"coefficient_unique",*u.terms(A+U+("H","i","p","a"))),actual_p,right_unit)
            padded_ea = apply(specialize(u,"euler_padding",*u.terms(A[:2]+D+("L","i","a"))),u.hyp("euler"),u.hyp("padded"))
            left_ea_unit = apply(specialize(u,"unit_coefficient",*u.terms(EA+("H","i")+U),Mul(i,a)),unit,u.hyp("index"),padded_ea)
            right_ea_unit = apply(specialize(u,"coefficient_swap",*u.terms(U+("H",)+EA+("i",)),Mul(i,a)),left_ea_unit)
            ti = apply(specialize(u,"coefficient_unique",*u.terms(EA+U+("H","i","t")),Mul(i,a)),u.hyp("coefficient"),right_ea_unit)
            return _chain(CongMul(EqRefl(i),pa),EqSym(ti),EqSym(specialize(u,"one_mul",tval)))
        return eliminate(t,specialize(t,"padding_exists",*t.terms(A+("i",))),("a",),"padded",value)
    def step(t):
        def previous_bound(u):
            k,K = u.terms(("k","K"))
            small = apply(specialize(u,"le_succ",Succ(k),Succ(k)),specialize(u,"le_refl",Succ(k)))
            return apply(specialize(u,"le_trans",Succ(k),Succ(Succ(k)),K),small,u.hyp("range"))
        def previous_prefix(u):
            return apply(specialize(u,"trace_step",*u.terms(P+B+("K","k")+W+U)),
                u.hyp("trace"),previous_bound(u),u.hyp("previous"),u.hyp("row_u"))
        def finish(u):
            def scaled(v):
                def old_entry(y):
                    j,q,a,b = y.terms(("j","q","a","b"))
                    euler_value = apply(specialize(y,"euler_u",j,q),y.hyp("bound"),y.hyp("original"))
                    same = apply(specialize(y,"beta_unique",*y.terms(("eb","ec")),j,b,Mul(j,q)),y.hyp("derived"),euler_value)
                    coeff = apply(specialize(y,"prefix_entry",*y.terms(EA+W+("H","tb","tc","H")),j,a),y.hyp("inner"),y.hyp("bound"),y.hyp("inner_value"))
                    ih = apply(specialize(y,"IH",*y.terms(("K",)+W+U),j,q,a),
                        y.hyp("trace"),previous_bound(y),y.hyp("previous"),y.hyp("row_u"),y.hyp("bound"),y.hyp("original"),coeff)
                    return EqTrans(same,ih)
                return eliminate(v,specialize(v,"beta_exists",*v.terms(U+("j",))),("q",),"original",old_entry)
            def associated(v):
                z = v.term("z")
                xz = apply(specialize(v,"coefficient_unique",*v.terms(("tb","tc","H")+A+("i","x")),z),v.hyp("first_coefficient"),AndElimL(v.hyp("association")))
                zt = apply(specialize(v,"coefficient_unique",*v.terms(EA+U+("H","i")),z,v.term("t")),AndElimR(v.hyp("association")),v.hyp("coefficient"))
                rel = introduce(v,("j","a","b"),("bound","inner_value","derived"),scaled)
                local_wx = apply(specialize(v,"coefficient_scale",*v.terms(("tb","tc","eb","ec","H")+A),Succ(v.term("k")),*v.terms(("i","x","w"))),rel,v.hyp("first_coefficient"),v.hyp("second_coefficient"))
                product_prefix = apply(specialize(v,"trace_step",*v.terms(P+B+("K",)),Succ(v.term("k")),*v.terms(U+V)),v.hyp("trace"),v.hyp("range"),v.hyp("row_u"),v.hyp("row_v"))
                actual_p = apply(specialize(v,"prefix_entry",*v.terms(A+U+("H",)+V+("H","i","p"))),product_prefix,v.hyp("index"),v.hyp("entry"))
                swapped_w = apply(specialize(v,"coefficient_swap",*v.terms(("eb","ec","H")+A+("i","w"))),v.hyp("second_coefficient"))
                product = apply(specialize(v,"product_rule",*v.terms(A+U+("H",)+D+("eb","ec","i","p","t","w"))),v.hyp("euler"),v.hyp("euler_u"),actual_p,v.hyp("coefficient"),swapped_w)
                factor,tt = Succ(v.term("k")),v.term("t")
                return _chain(product,CongAdd(EqRefl(tt),local_wx),CongAdd(EqRefl(tt),CongMul(EqRefl(factor),EqTrans(xz,zt))),
                    specialize(v,"add_comm",tt,Mul(factor,tt)),EqSym(specialize(v,"mul_succ_left",factor,tt)))
            swapped_prefix = apply(specialize(u,"prefix_swap",*u.terms(A+W+("H",)+U+("H",))),previous_prefix(u))
            association = apply(specialize(u,"associate",*u.terms(EA+W+("H",)+A+("i","H","tb","tc")+U)),u.hyp("index"),u.hyp("inner"),swapped_prefix)
            return eliminate(u,association,("z",),"association",associated)
        return eliminate(t,specialize(t,"row_decode",*t.terms(B+("k",))),W,"previous",lambda u:
            eliminate(u,specialize(u,"prefix_exists",*u.terms(EA+W+("H","H"))),("tb","tc"),"inner",lambda v:
                eliminate(v,specialize(v,"euler_exists",*v.terms(U+("H",))),("eb","ec"),"euler_u",lambda w:
                    eliminate(w,specialize(w,"coefficient_exists",*w.terms(("tb","tc","H")+A+("i",))),("x",),"first_coefficient",lambda y:
                        eliminate(y,specialize(y,"coefficient_exists",*y.terms(("eb","ec","H")+A+("i",))),("w",),"second_coefficient",finish)))))
    motive = target
    for _ in P+B+D:
        motive = motive.body
    motive = motive.right.body
    return introduce(s,P+B+D,("euler",),lambda t:
        Ind(motive,introduce(t,params,premises,base),introduce(t,("k",),("IH",),lambda u:introduce(u,params,premises,step))))


def _root(s):
    from sqrt2_power_native import instantiate
    def chosen(t):
        def entry(u):
            rule = apply(specialize(u,"power_rule",*u.terms(P+B+D)),u.hyp("euler"))
            return apply(instantiate(rule,*u.terms(("k","K")+U+V+("i","p","t"))),
                *(u.hyp(h) for h in ("trace","range","row_u","row_v","index","entry","coefficient")))
        invariant = introduce(t,ROW_ARGS,("range","row_u","row_v","index","entry","coefficient"),entry)
        return witness(t.terms(D+B),conjunction(t.hyp("euler"),t.hyp("trace"),invariant))
    return introduce(s,P+("K",),(),lambda t:
        eliminate(t,specialize(t,"euler_exists",*t.terms(A)),D,"euler",lambda u:
            eliminate(u,specialize(u,"power_exists",*u.terms(P+("K",))),B,"trace",chosen)))


def prove_series_power_euler(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"trace_unit":lambda s:_trace_unit(s,registry),"trace_step":lambda s:_trace_step(s,registry),
        "prefix_swap":_prefix_swap,"coefficient_scale":_coefficient_scale,
        "power_rule":lambda s:_power_rule(s,parse_named(HELPER_SOURCES["power_rule"],registry=registry),registry),"CV017":_root}
    return assemble_actual_certificate(code="CV017",target=frozen_series_power_euler_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=series_power_euler_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
