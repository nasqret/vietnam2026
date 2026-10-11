"""CV008: construct both orders of an arbitrary finite natural double sum.

The source cell is the actual beta lookup at (o+s*i)+t*j. All slice tables,
row/column tables and sums are constructed. Zero dimensions and strides are
allowed. Interchange is proved by ordinary induction, never a definition.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_natural_convolution import (
    ROOT, Scope, introduce, eliminate, witness, field, apply, specialize,
    canonical, json_hash, _inert_metrics, ANCESTOR_IDS as CONVOLUTION_ANCESTORS,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_sum_linearity import (
    definition_registry as linearity_registry, sum_linearity_source_pins,
    LINEARITY_SOURCE, ANCESTOR_IDS as LINEARITY_ANCESTORS,
)
from sqrt2_power_euler_product import LINEARITY_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_quadratic_product_exists import read_archive

SCHEMA = "sqrt2-power-natural-fubini-v1"


def forall(names, text):
    return "forall "+" ".join(names)+". "+text


def slice_(origin="o",stride="t",codes=("ub","uc"),length="N"):
    return "NatAffineSlice("+",".join(("ab","ac",origin,stride)+codes+(length,))+")"


def sum_(origin="o",stride="t",length="N",value="z"):
    return "NatAffineSum("+",".join(("ab","ac",origin,stride,length,value))+")"


def rows_(s="s",t="t",m="m",n="n",codes=("rb","rc")):
    return "NatAffineRowSums("+",".join(("ab","ac","o",s,t,m,n)+codes)+")"


P = ("ab","ac","o","s","t")
ROW, COL = rows_(), rows_("t","s","n","m",("cb","cc"))
DEFINITION_ROWS = (
    (411,"NatAffineSlice",("ab","ac","o","t","ub","uc","N"),
     "forall i a. Lt(i,N) -> BetaAt(ub,uc,i,a) -> BetaAt(ab,ac,o+t*i,a)",
     ("Lt","BetaAt"),"40c82f04e972cfb02f757a400f458c28da431b6117f6eb2dbbcaf89dc66694c3"),
    (412,"NatAffineSum",("ab","ac","o","t","N","z"),
     "exists ub uc. NatAffineSlice(ab,ac,o,t,ub,uc,N) /\\ Sum(ub,uc,N,z)",
     ("NatAffineSlice","Sum"),"124104404bbd80a6380b46ba736c9858d7a6f52b184c458f602aa636a3bf4ed3"),
    (413,"NatAffineRowSums",P+("m","n","rb","rc"),
     "forall i. Lt(i,m) -> exists a. BetaAt(rb,rc,i,a) /\\ NatAffineSum(ab,ac,o+s*i,t,n,a)",
     ("Lt","BetaAt","NatAffineSum"),"b98dff601a73c5c0124d5fb75d21f1e82474e94f665c74dc556f14cfbe9d5984"),
)
NAMED_SOURCE = forall(P+("m","n"),"exists rb rc cb cc z. "+ROW+" /\\ ("+COL+
    " /\\ (Sum(rb,rc,m,z) /\\ Sum(cb,cc,n,z)))")
TARGET_SHA256 = "144c71f1f4627b2ab6b53db389f1fc57d00868e5daf3716c01c6858aa379fec7"
HELPER_SOURCES = {
    "slice_exists": "forall ab ac o t N. exists ub uc. "+slice_(),
    "slice_sum_exists": "forall ab ac o t N. exists z. "+sum_(),
    "slice_sum_unique": "forall ab ac o t N u v. "+sum_(value="u")+" -> "+sum_(value="v")+" -> u=v",
    "slice_sum_zero": "forall ab ac o t z. "+sum_(length="0")+" -> z=0",
    "slice_sum_step": "forall ab ac o t N z. "+sum_(length="S N")+" -> exists a r. BetaAt(ab,ac,o+t*N,a) /\\ ("+sum_(value="r")+" /\\ z=r+a)",
    "slice_sum_successor_add": "forall ab ac o t N u a z. "+sum_(value="u")+" -> BetaAt(ab,ac,o+t*N,a) -> "+sum_(length="S N")+" -> z=u+a",
    "rows_exists": forall(P+("n","m"),"exists rb rc. "+ROW),
    "rows_lookup": forall(P+("m","n","rb","rc","i","z"),ROW+" -> Lt(i,m) -> BetaAt(rb,rc,i,z) -> "+sum_("o+s*i","t","n","z")),
    "rows_restrict": forall(P+("m","n","rb","rc"),rows_(m="S m")+" -> "+ROW),
    "zero_inner": forall(("m",)+P+("rb","rc","z"),rows_(n="0")+" -> Sum(rb,rc,m,z) -> z=0"),
    "column_step": forall(P+("m","n","cb","cc","vb","vc","db","dc"),COL+" -> "+
        slice_("o+s*m","t",("vb","vc"),"n")+" -> "+rows_("t","s","n","S m",("db","dc"))+
        " -> NatLinearTriple(1,1,1,cb,cc,vb,vc,db,dc,n)"),
    "fubini": forall(("m",)+P+("n","rb","rc","cb","cc","u","v"),ROW+" -> "+COL+
        " -> Sum(rb,rc,m,u) -> Sum(cb,cc,n,v) -> u=v"),
}
HELPER_TARGET_SHA256 = {
    "slice_exists":"e157961192d69961b563741508913c05955de3ccd9c81122319eaaade37c9be4",
    "slice_sum_exists":"98d81eab9c8da49b2e90614bba80bb1e4e1acf5b66a6b9f504acd2ca8f8e8f3d",
    "slice_sum_unique":"97907534bbab333271dbb4d4a56e052decef153c4b910a0c8d28ff9aba120a45",
    "slice_sum_zero":"6995e119d7ce25fa3565200ed2b415c7e7cdb3e315311f041296206bd737bc49",
    "slice_sum_step":"e932022a492aff6bd569055b4d73630d32e6129aabaafedc7f4ff66294ef68d2",
    "slice_sum_successor_add":"f9245f254f00f28d1d83a24f626d0fb2b68b0c05b1a02ab2487126b0f186a259",
    "rows_exists":"929fdb531a79a1b0c42fc2dd54b94cc9cb14edef8640b344dd469aed61679cbd",
    "rows_lookup":"8793fc2d7abc962f50c4bb19a2312d95c15b868a94a64caefda86fbda21136b8",
    "rows_restrict":"c006651e68e4507aed086010643add366d90a3795e21aab725914ecb41b7b01a",
    "zero_inner":"ad82780ba0915aa09fd029a9738d25270bc618e3764bf010f22a731b03c9935f",
    "column_step":"62b341a8517f6853f9e05c341661862b0190e05a872c749e2f02fb75d2aac7c7",
    "fubini":"118bc767c06b0efa80a816cd523840a21b76b22dca4e5835268d8d2dc02d84a0",
}
ENDPOINT_SOURCES = {
    "add_comm": (2,"forall a b. a+b=b+a"),
    "add_assoc": (3,"forall a b c. (a+b)+c=a+(b+c)"),
    "one_mul": (9,"forall a. 1*a=a"),
    "le_refl": (13,"forall a. Le(a,a)"),
    "zero_le": (24,"forall a. Le(0,a)"),
    "le_of_succ_le_succ": (33,"forall a b. Le(S a,S b) -> Le(a,b)"),
    "le_succ": (34,"forall a b. Le(a,b) -> Le(a,S b)"),
    "le_eq_or_lt": (37,"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)"),
    "lt_not_le": (40,"forall a b. Lt(a,b) -> Le(b,a) -> false"),
    "beta_exists": (87,"forall b c i. exists a. BetaAt(b,c,i,a)"),
    "beta_unique": (88,"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d"),
    "beta_extend": (116,"forall N b c v. exists eb ec. BetaAt(eb,ec,N,v) /\\ (forall j a. Lt(j,N) -> BetaAt(b,c,j,a) -> BetaAt(eb,ec,j,a))"),
    "sum_exists": (122,"forall b c N. exists n. Sum(b,c,N,n)"),
    "sum_unique": (124,"forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m"),
    "sum_zero": (125,"forall b c n. Sum(b,c,0,n) -> n=0"),
    "sum_decompose": (126,"forall b c N n. Sum(b,c,S N,n) -> exists a r. BetaAt(b,c,N,a) /\\ (Sum(b,c,N,r) /\\ n=r+a)"),
    "sum_transport": (137,"forall b c eb ec N n. Sum(b,c,N,n) -> (forall j a. Lt(j,N) -> BetaAt(b,c,j,a) -> BetaAt(eb,ec,j,a)) -> Sum(eb,ec,N,n)"),
}
HELPER_DEPENDENCIES = {
    "slice_exists": ("zero_le","lt_not_le","le_of_succ_le_succ","le_eq_or_lt","beta_exists","beta_unique","beta_extend"),
    "slice_sum_exists": ("slice_exists","sum_exists"),
    "slice_sum_unique": ("beta_exists","beta_unique","sum_transport","sum_unique"),
    "slice_sum_zero": ("sum_zero",),
    "slice_sum_step": ("le_refl","le_succ","sum_decompose"),
    "slice_sum_successor_add": ("slice_sum_step","slice_sum_unique","beta_unique"),
    "rows_exists": ("zero_le","lt_not_le","le_of_succ_le_succ","le_eq_or_lt","beta_extend","slice_sum_exists"),
    "rows_lookup": ("beta_unique",),
    "rows_restrict": ("le_succ",),
    "zero_inner": ("sum_zero","sum_decompose","rows_restrict","rows_lookup","slice_sum_zero","le_refl"),
    "column_step": ("rows_lookup","slice_sum_successor_add","add_assoc","add_comm","one_mul"),
    "fubini": ("sum_zero","zero_inner","sum_decompose","rows_restrict","rows_exists","rows_lookup","sum_exists","column_step","linearity","le_refl","one_mul"),
    "CV008": ("rows_exists","sum_exists","fubini"),
}


class NaturalFubiniError(ValueError):
    """Changed exact finite computation, actual body, target or resource cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(linearity_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    for number,name,parameters,source,dependencies,digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if name in registry or any(d["name"]==name or d["id"]==identifier for d in parent):
            raise NaturalFubiniError("affine finite-sum alias collision")
        formula = parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula))!=digest:
            raise NaturalFubiniError("affine finite-sum exact expansion changed: "+name)
        text = pretty_formula(formula,list(parameters))
        d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
            summary="Actual finite affine decoding/summation; no interchange equality is assumed.",
            category="irrationality_formal_series",conceptual_dependencies=dependencies)
        if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
            raise NaturalFubiniError("affine computation failed exact expansion roundtrip")
        registry[name] = d
    return MappingProxyType(registry)


def frozen_natural_fubini_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise NaturalFubiniError("CV008 unconditional double-sum construction target changed")
    return target


def source_contract():
    return dict(code="CV008",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,both_sum_orders_constructed=True,all_dimensions_and_strides_allowed=True,
        source_cell="BetaAt(ab,ac,(o+s*i)+t*j,a)",new_definition_ids=["ND0411","ND0412","ND0413"],
        definition_admissions=0,original_HA_checked=False,authority="source_contract_not_proof_authority",
        natural_convolution_associativity=False,exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def natural_fubini_source_pins():
    result = sum_linearity_source_pins()
    expected = {
        "scripts/sqrt2_power_sum_linearity.py":"5a9131119953036d5bb1c7cb2b08e26bcc4fa63fd31a8c0cbc77409f17358bc0",
        "scripts/sqrt2_power_euler_product.py":"c26512518de941c9f8c54bfe682732d601158748f25955166b3ea6d8290afa10",
        "scripts/sqrt2_power_series_power_trace.py":"557d393791fb527361bcffb4977b0e0bad591f98a426e12d1da461643cc39422",
        "scripts/sqrt2_power_quadratic_product_exists.py":"c20c38bfceb78fa16c236925024a43c12624b2df23937bb1c1e9f54393d49017",
        CONVOLUTION_ARCHIVE["path"]:CONVOLUTION_ARCHIVE["sha256"],
        LINEARITY_ARCHIVE["path"]:LINEARITY_ARCHIVE["sha256"],
    }
    for name in (*expected,"scripts/sqrt2_power_natural_fubini.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise NaturalFubiniError("finite-sum source or actual proof archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _subst(s,registry,source,equation,proof):
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import EqSubst
    return EqSubst(parse_named(source,s.variable("slot").variables,registry),equation,proof)


def _slice_exists(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,EqSym,Ind,OrElim
    from peano_lab.kernel.terms import Add,Mul,Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("i","a"),("bound","output"),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("i"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("i"))))))
    def step(t):
        def old(u):
            def value(v):
                def extended(w):
                    def entry(x):
                        def last(y):
                            at_end = _subst(y,registry,"BetaAt(ub,uc,slot,a)",y.hyp("last"),y.hyp("output"))
                            same = apply(specialize(y,"beta_unique",*y.terms(("ub","uc","N","v","a"))),AndElimL(y.hyp("extension")),at_end)
                            source = _subst(y,registry,"BetaAt(ab,ac,o+t*N,slot)",same,y.hyp("value"))
                            return _subst(y,registry,"BetaAt(ab,ac,o+t*slot,a)",EqSym(y.hyp("last")),source)
                        def earlier(y):
                            def decoded(z):
                                preserved = apply(instantiate(AndElimR(z.hyp("extension")),*z.terms(("i","b"))),z.hyp("earlier"),z.hyp("old_entry"))
                                same = apply(specialize(z,"beta_unique",*z.terms(("ub","uc","i","b","a"))),preserved,z.hyp("output"))
                                source = apply(specialize(z,"old",*z.terms(("i","b"))),z.hyp("earlier"),z.hyp("old_entry"))
                                return _subst(z,registry,"BetaAt(ab,ac,o+t*i,slot)",same,source)
                            return eliminate(y,specialize(y,"beta_exists",*y.terms(("ob","oc","i"))),("b",),"old_entry",decoded)
                        lower = apply(specialize(x,"le_of_succ_le_succ",*x.terms(("i","N"))),x.hyp("bound"))
                        cases = apply(specialize(x,"le_eq_or_lt",*x.terms(("i","N"))),lower)
                        return OrElim(cases,last(x.hypothesis("last")),earlier(x.hypothesis("earlier")))
                    return witness(w.terms(("ub","uc")),introduce(w,("i","a"),("bound","output"),entry))
                extension = specialize(v,"beta_extend",*v.terms(("N","ob","oc","v")))
                return eliminate(v,extension,("ub","uc"),"extension",extended)
            index = Add(u.term("o"),Mul(u.term("t"),u.term("N")))
            return eliminate(u,specialize(u,"beta_exists",*u.terms(("ab","ac")),index),("v",),"value",value)
        return eliminate(t,t.hyp("IH"),("ob","oc"),"old",old)
    motive = target
    for _ in range(5):
        motive = motive.body
    return introduce(s,("ab","ac","o","t"),(),lambda t:
        Ind(motive,base(t),introduce(t,("N",),("IH",),step)))


def _slice_sum_exists(s):
    from peano_lab.kernel.proofs import AndIntro
    def codes(t):
        return eliminate(t,specialize(t,"sum_exists",*t.terms(("ub","uc","N"))),("z",),"sum",lambda u:
            witness((u.term("z"),),witness(u.terms(("ub","uc")),AndIntro(u.hyp("slice"),u.hyp("sum")))))
    return introduce(s,("ab","ac","o","t","N"),(),lambda t:
        eliminate(t,specialize(t,"slice_exists",*t.terms(("ab","ac","o","t","N"))),("ub","uc"),"slice",codes))


def _slice_sum_unique(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        def entry(u):
            def value(v):
                first = apply(instantiate(AndElimL(v.hyp("first")),*v.terms(("i","a"))),v.hyp("bound"),v.hyp("input"))
                second = apply(instantiate(AndElimL(v.hyp("second")),*v.terms(("i","b"))),v.hyp("bound"),v.hyp("output"))
                index = Add(v.term("o"),Mul(v.term("t"),v.term("i")))
                same = apply(specialize(v,"beta_unique",*v.terms(("ab","ac")),index,*v.terms(("b","a"))),second,first)
                return _subst(v,registry,"BetaAt(vb,vc,i,slot)",same,v.hyp("output"))
            return eliminate(u,specialize(u,"beta_exists",*u.terms(("vb","vc","i"))),("b",),"output",value)
        pointwise = introduce(t,("i","a"),("bound","input"),entry)
        transported = apply(specialize(t,"sum_transport",*t.terms(("ub","uc","vb","vc","N","u"))),AndElimR(t.hyp("first")),pointwise)
        return apply(specialize(t,"sum_unique",*t.terms(("vb","vc","N","u","v"))),transported,AndElimR(t.hyp("second")))
    return introduce(s,("ab","ac","o","t","N","u","v"),("left","right"),lambda t:
        eliminate(t,t.hyp("left"),("ub","uc"),"first",lambda u:
            eliminate(u,u.hyp("right"),("vb","vc"),"second",finish)))


def _slice_sum_zero(s):
    from peano_lab.kernel.proofs import AndElimR
    return introduce(s,("ab","ac","o","t","z"),("input",),lambda t:
        eliminate(t,t.hyp("input"),("ub","uc"),"data",lambda u:
            apply(specialize(u,"sum_zero",*u.terms(("ub","uc","z"))),AndElimR(u.hyp("data")))))


def _slice_sum_step(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro
    from peano_lab.kernel.terms import Succ
    def data(t):
        def finish(u):
            actual = apply(instantiate(AndElimL(u.hyp("data")),*u.terms(("N","a"))),specialize(u,"le_refl",Succ(u.term("N"))),field(u.hyp("decomposed"),0,3))
            restricted = introduce(u,("i","v"),("bound","entry"),lambda v:
                apply(instantiate(AndElimL(v.hyp("data")),*v.terms(("i","v"))),
                    apply(specialize(v,"le_succ",Succ(v.term("i")),v.term("N")),v.hyp("bound")),v.hyp("entry")))
            summed = witness(u.terms(("ub","uc")),AndIntro(restricted,field(u.hyp("decomposed"),1,3)))
            return witness(u.terms(("a","r")),conjunction(actual,summed,field(u.hyp("decomposed"),2,3)))
        source = apply(specialize(t,"sum_decompose",*t.terms(("ub","uc","N","z"))),AndElimR(t.hyp("data")))
        return eliminate(t,source,("a","r"),"decomposed",finish)
    return introduce(s,("ab","ac","o","t","N","z"),("input",),lambda t:
        eliminate(t,t.hyp("input"),("ub","uc"),"data",data))


def _slice_sum_successor_add(s):
    from peano_lab.kernel.proofs import CongAdd,EqTrans
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        same_sum = apply(specialize(t,"slice_sum_unique",*t.terms(("ab","ac","o","t","N","r","u"))),field(t.hyp("decomposed"),1,3),t.hyp("old"))
        index = Add(t.term("o"),Mul(t.term("t"),t.term("N")))
        same_value = apply(specialize(t,"beta_unique",*t.terms(("ab","ac")),index,*t.terms(("b","a"))),field(t.hyp("decomposed"),0,3),t.hyp("last"))
        return EqTrans(field(t.hyp("decomposed"),2,3),CongAdd(same_sum,same_value))
    return introduce(s,("ab","ac","o","t","N","u","a","z"),("old","last","new"),lambda t:
        eliminate(t,apply(specialize(t,"slice_sum_step",*t.terms(("ab","ac","o","t","N","z"))),t.hyp("new")),("b","r"),"decomposed",finish))


def _rows_exists(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,BotElim,EqSym,Ind,OrElim
    from peano_lab.kernel.terms import Add,Mul,Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("i",),("bound",),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("i"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("i"))))))
    def step(t):
        def old(u):
            def value(v):
                def extended(w):
                    def entry(x):
                        def last(y):
                            result = witness((y.term("z"),),AndIntro(AndElimL(y.hyp("extension")),y.hyp("value")))
                            return _subst(y,registry,"exists a. BetaAt(rb,rc,slot,a) /\\ "+sum_("o+s*slot","t","n","a"),EqSym(y.hyp("last")),result)
                        def earlier(y):
                            def decoded(z):
                                kept = apply(instantiate(AndElimR(z.hyp("extension")),*z.terms(("i","a"))),z.hyp("earlier"),AndElimL(z.hyp("old_entry")))
                                return witness((z.term("a"),),AndIntro(kept,AndElimR(z.hyp("old_entry"))))
                            return eliminate(y,apply(specialize(y,"old",y.term("i")),y.hyp("earlier")),("a",),"old_entry",decoded)
                        lower = apply(specialize(x,"le_of_succ_le_succ",*x.terms(("i","m"))),x.hyp("bound"))
                        cases = apply(specialize(x,"le_eq_or_lt",*x.terms(("i","m"))),lower)
                        return OrElim(cases,last(x.hypothesis("last")),earlier(x.hypothesis("earlier")))
                    return witness(w.terms(("rb","rc")),introduce(w,("i",),("bound",),entry))
                return eliminate(v,specialize(v,"beta_extend",*v.terms(("m","ob","oc","z"))),("rb","rc"),"extension",extended)
            origin = Add(u.term("o"),Mul(u.term("s"),u.term("m")))
            return eliminate(u,specialize(u,"slice_sum_exists",*u.terms(("ab","ac")),origin,*u.terms(("t","n"))),("z",),"value",value)
        return eliminate(t,t.hyp("IH"),("ob","oc"),"old",old)
    motive = target
    for _ in range(7):
        motive = motive.body
    return introduce(s,P+("n",),(),lambda t:Ind(motive,base(t),introduce(t,("m",),("IH",),step)))


def _rows_lookup(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def finish(t):
        same = apply(specialize(t,"beta_unique",*t.terms(("rb","rc","i","a","z"))),AndElimL(t.hyp("entry")),t.hyp("value"))
        return _subst(t,registry,sum_("o+s*i","t","n","slot"),same,AndElimR(t.hyp("entry")))
    return introduce(s,P+("m","n","rb","rc","i","z"),("rows","bound","value"),lambda t:
        eliminate(t,apply(specialize(t,"rows",t.term("i")),t.hyp("bound")),("a",),"entry",finish))


def _rows_restrict(s):
    from peano_lab.kernel.terms import Succ
    return introduce(s,P+("m","n","rb","rc"),("rows",),lambda t:
        introduce(t,("i",),("bound",),lambda u:
            apply(specialize(u,"rows",u.term("i")),apply(specialize(u,"le_succ",Succ(u.term("i")),u.term("m")),u.hyp("bound")))))


def _zero_inner(s,target):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqTrans,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    parameters,premises = P+("rb","rc","z"),("rows","sum")
    def base(t):
        return apply(specialize(t,"sum_zero",*t.terms(("rb","rc","z"))),t.hyp("sum"))
    def step(t):
        def finish(u):
            restricted = apply(specialize(u,"rows_restrict",*u.terms(P+("m",)),Zero(),*u.terms(("rb","rc"))),u.hyp("rows"))
            ih = apply(specialize(u,"IH",*u.terms(P+("rb","rc","r"))),restricted,field(u.hyp("decomposed"),1,3))
            last = apply(specialize(u,"rows_lookup",*u.terms(P),Succ(u.term("m")),Zero(),*u.terms(("rb","rc","m","a"))),
                u.hyp("rows"),specialize(u,"le_refl",Succ(u.term("m"))),field(u.hyp("decomposed"),0,3))
            origin = Add(u.term("o"),Mul(u.term("s"),u.term("m")))
            zero = apply(specialize(u,"slice_sum_zero",*u.terms(("ab","ac")),origin,*u.terms(("t","a"))),last)
            return EqTrans(field(u.hyp("decomposed"),2,3),EqTrans(CongAdd(ih,zero),instantiate(Axiom("PA3"),Zero())))
        source = apply(specialize(t,"sum_decompose",*t.terms(("rb","rc","m","z"))),t.hyp("sum"))
        return eliminate(t,source,("a","r"),"decomposed",finish)
    return Ind(target.body,introduce(s,parameters,premises,base),introduce(s,("m",),("IH",),lambda t:introduce(t,parameters,premises,step)))


def _column_step(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym,EqTrans
    from peano_lab.kernel.terms import Add,Mul,Succ
    def entry(t):
        origin = Add(t.term("o"),Mul(t.term("t"),t.term("j")))
        old = apply(specialize(t,"rows_lookup",*t.terms(("ab","ac","o","t","s","n","m","cb","cc","j","a"))),t.hyp("old"),t.hyp("bound"),t.hyp("a_entry"))
        new = apply(specialize(t,"rows_lookup",*t.terms(("ab","ac","o","t","s","n")),Succ(t.term("m")),*t.terms(("db","dc","j","c"))),t.hyp("new"),t.hyp("bound"),t.hyp("c_entry"))
        actual = apply(specialize(t,"last",*t.terms(("j","b"))),t.hyp("bound"),t.hyp("b_entry"))
        o,sm,tj = t.term("o"),Mul(t.term("s"),t.term("m")),Mul(t.term("t"),t.term("j"))
        coordinate = EqTrans(specialize(t,"add_assoc",o,sm,tj),EqTrans(CongAdd(EqRefl(o),specialize(t,"add_comm",sm,tj)),EqSym(specialize(t,"add_assoc",o,tj,sm))))
        moved = _subst(t,registry,"BetaAt(ab,ac,slot,b)",coordinate,actual)
        equality = apply(specialize(t,"slice_sum_successor_add",*t.terms(("ab","ac")),origin,*t.terms(("s","m","a","b","c"))),old,moved,new)
        return EqTrans(specialize(t,"one_mul",t.term("c")),EqTrans(equality,
            CongAdd(EqSym(specialize(t,"one_mul",t.term("a"))),EqSym(specialize(t,"one_mul",t.term("b"))))))
    return introduce(s,P+("m","n","cb","cc","vb","vc","db","dc"),("old","last","new"),lambda t:
        introduce(t,("j","a","b","c"),("bound","a_entry","b_entry","c_entry"),entry))


def _fubini(s,target):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,EqRefl,EqSym,EqTrans,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    parameters,premises = P+("n","rb","rc","cb","cc","u","v"),("rows","columns","row_sum","column_sum")
    def base(t):
        left = apply(specialize(t,"sum_zero",*t.terms(("rb","rc","u"))),t.hyp("row_sum"))
        right = apply(specialize(t,"zero_inner",*t.terms(("n","ab","ac","o","t","s","cb","cc","v"))),t.hyp("columns"),t.hyp("column_sum"))
        return EqTrans(left,EqSym(right))
    def step(t):
        def row_decoded(u):
            def old_columns(v):
                def old_sum(w):
                    def last_slice(x):
                        restricted = apply(specialize(x,"rows_restrict",*x.terms(P+("m","n","rb","rc"))),x.hyp("rows"))
                        ih = apply(specialize(x,"IH",*x.terms(P+("n","rb","rc","db","dc","r","z"))),restricted,x.hyp("old_columns"),field(x.hyp("decomposed"),1,3),x.hyp("old_sum"))
                        pointwise = apply(specialize(x,"column_step",*x.terms(P+("m","n","db","dc","vb","vc","cb","cc"))),x.hyp("old_columns"),AndElimL(x.hyp("last")),x.hyp("columns"))
                        one = Succ(Zero())
                        linear = apply(specialize(x,"linearity",one,one,one,*x.terms(("db","dc","vb","vc","cb","cc","n","z","a","v"))),
                            x.hyp("old_sum"),AndElimR(x.hyp("last")),x.hyp("column_sum"),pointwise)
                        new_total = EqTrans(EqSym(specialize(x,"one_mul",x.term("v"))),EqTrans(linear,
                            CongAdd(specialize(x,"one_mul",x.term("z")),specialize(x,"one_mul",x.term("a")))))
                        return EqTrans(field(x.hyp("decomposed"),2,3),EqTrans(CongAdd(ih,EqRefl(x.term("a"))),EqSym(new_total)))
                    last = apply(specialize(w,"rows_lookup",*w.terms(P),Succ(w.term("m")),*w.terms(("n","rb","rc","m","a"))),w.hyp("rows"),specialize(w,"le_refl",Succ(w.term("m"))),field(w.hyp("decomposed"),0,3))
                    return eliminate(w,last,("vb","vc"),"last",last_slice)
                return eliminate(v,specialize(v,"sum_exists",*v.terms(("db","dc","n"))),("z",),"old_sum",old_sum)
            constructed = specialize(u,"rows_exists",*u.terms(("ab","ac","o","t","s","m","n")))
            return eliminate(u,constructed,("db","dc"),"old_columns",old_columns)
        decomposed = apply(specialize(t,"sum_decompose",*t.terms(("rb","rc","m","u"))),t.hyp("row_sum"))
        return eliminate(t,decomposed,("a","r"),"decomposed",row_decoded)
    return Ind(target.body,introduce(s,parameters,premises,base),introduce(s,("m",),("IH",),lambda t:introduce(t,parameters,premises,step)))


def _root(s,registry):
    from peano_lab.kernel.proofs import EqSym
    def finish(t):
        equality = apply(specialize(t,"fubini",*t.terms(("m",)+P+("n","rb","rc","cb","cc","z","w"))),t.hyp("rows"),t.hyp("columns"),t.hyp("row_sum"),t.hyp("column_sum"))
        same = _subst(t,registry,"Sum(cb,cc,n,slot)",EqSym(equality),t.hyp("column_sum"))
        return witness(t.terms(("rb","rc","cb","cc","z")),conjunction(t.hyp("rows"),t.hyp("columns"),t.hyp("row_sum"),same))
    def construct(t,position):
        if position==4:
            return finish(t)
        name,parameters,variables,label = (
            ("rows_exists",P+("n","m"),("rb","rc"),"rows"),
            ("rows_exists",("ab","ac","o","t","s","m","n"),("cb","cc"),"columns"),
            ("sum_exists",("rb","rc","m"),("z",),"row_sum"),
            ("sum_exists",("cb","cc","n"),("w",),"column_sum"),
        )[position]
        return eliminate(t,specialize(t,name,*t.terms(parameters)),variables,label,lambda u:construct(u,position+1))
    return introduce(s,P+("m","n"),(),lambda t:construct(t,0))


@dataclass(frozen=True)
class NaturalFubiniCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_natural_fubini(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise NaturalFubiniError("expected unchanged BinaryDAGLimits")
    before = natural_fubini_source_pins()
    registry,target = definition_registry(),frozen_natural_fubini_target()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise NaturalFubiniError("exact finite-sum helper target changed")
    formulas["CV008"] = target
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    for pin,ids in ((CONVOLUTION_ARCHIVE,CONVOLUTION_ANCESTORS),(LINEARITY_ARCHIVE,LINEARITY_ANCESTORS)):
        original = read_archive(pin)
        remap = {}
        for old,r in enumerate(original):
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise NaturalFubiniError("actual ancestor ordered dependencies changed")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if type(r[0]) is not int or r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise NaturalFubiniError("merged finite-sum ancestor body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        for name,(old,source) in ENDPOINT_SOURCES.items():
            if old not in ids:
                continue
            local = ids.index(old)
            if original[local][1]!=encode_formula(parse_named(source,registry=registry)):
                raise NaturalFubiniError("actual finite-sum endpoint source differs: "+name)
            if name in endpoints and endpoints[name]!=remap[local]:
                raise NaturalFubiniError("shared actual endpoint bodies disagree")
            endpoints[name] = remap[local]
        if pin["case"]=="CV006":
            if original[107][1]!=encode_formula(parse_named(LINEARITY_SOURCE,registry=registry)):
                raise NaturalFubiniError("actual weighted-sum linearity endpoint changed")
            endpoints["linearity"] = remap[107]
        del original,remap
        gc.collect()
    ancestor_count = len(rows)
    factories = {
        "slice_exists": lambda s:_slice_exists(s,formulas["slice_exists"],registry),
        "slice_sum_exists": _slice_sum_exists,
        "slice_sum_unique": lambda s:_slice_sum_unique(s,registry),
        "slice_sum_zero": _slice_sum_zero,
        "slice_sum_step": _slice_sum_step,
        "slice_sum_successor_add": _slice_sum_successor_add,
        "rows_exists": lambda s:_rows_exists(s,formulas["rows_exists"],registry),
        "rows_lookup": lambda s:_rows_lookup(s,registry),
        "rows_restrict": _rows_restrict,
        "zero_inner": lambda s:_zero_inner(s,formulas["zero_inner"]),
        "column_step": lambda s:_column_step(s,registry),
        "fubini": lambda s:_fubini(s,formulas["fubini"]),
        "CV008": lambda s:_root(s,registry),
    }
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise NaturalFubiniError("finite-sum aggregate ordinary body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in dependencies],encode_proof(body)])
    reachable,pending = set(),[len(rows)-1]
    while pending:
        old = pending.pop()
        if old not in reachable:
            reachable.add(old)
            pending.extend(rows[old][2])
    retained = tuple(sorted(reachable))
    remap = {old:new for new,old in enumerate(retained)}
    ancestors = tuple(old for old in retained if old<ancestor_count)
    ancestor_total = sum(_inert_metrics(rows[old][3],limits)[0] for old in ancestors)
    helper_indices = {name:remap[endpoints[name]] for name in HELPER_DEPENDENCIES}
    rows = [[rows[old][0],rows[old][1],[remap[d] for d in rows[old][2]],rows[old][3]] for old in retained]
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise NaturalFubiniError("finite-sum canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise NaturalFubiniError("decoded finite-sum target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or natural_fubini_source_pins()!=before:
        raise NaturalFubiniError("finite-sum target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,all_rectangles_interchange=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        convolution_archive=dict(CONVOLUTION_ARCHIVE),linearity_archive=dict(LINEARITY_ARCHIVE),
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),helper_bundle_indices=helper_indices,
        new_induction_count=4,ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return NaturalFubiniCertificate(target,bundle,payload,receipt,deepest,provenance)
