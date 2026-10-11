"""CV044: construct a genuine finite Cauchy grid with explicit triangular zeros.

Cell (k,j) is the actual antidiagonal product A[j]*B[k-j] when j<=k,
and zero when k<j. Quotient/remainder coordinates and beta extension construct
the square of side N+1. The definitions contain no sum/evaluation identity.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_natural_convolution import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,canonical,json_hash,
    definition_registry as convolution_registry,natural_convolution_source_pins,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_triple_grid import HELPER_SOURCES as GRID_HELPERS
from sqrt2_power_convolution_associative import GRID_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive
from sqrt2_power_convolution_unit import _subst

SCHEMA = "sqrt2-power-cauchy-grid-v1"
P = ("ab","ac","L","bb","bc","M")


def cell(k="k",j="j",z="z"):
    return "NatCauchyCell("+",".join(P+(k,j,z))+")"


def flat(v="v",z="z"):
    return "NatCauchyFlatCell("+",".join(P+("N",v,z))+")"


def prefix(codes=("gb","gc"),length="T"):
    return "NatCauchyFlatPrefix("+",".join(P+("N",)+codes+(length,))+")"


GRID = "NatCauchyGrid("+",".join(P+("N","gb","gc"))+")"
DEFINITION_ROWS = (
    (430,"NatCauchyCell",P+("k","j","z"),
     "PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,k,j,z) \\/ (Lt(k,j) /\\ z=0)",
     ("PolynomialDiagonalTerm","Lt"),"7b2c7aec44d741de414dff6bdb56b8e729b2b9c038f96533cae2e5d4823e4fab"),
    (431,"NatCauchyFlatCell",P+("N","v","z"),
     "exists k j. v=(S N)*k+j /\\ (Lt(j,S N) /\\ "+cell()+")",
     ("Lt","NatCauchyCell"),"05478d078116813197b6086d31c681acdb4330d5c665db5384db1fc1aaba4f1a"),
    (432,"NatCauchyFlatPrefix",P+("N","gb","gc","T"),
     "forall v. Lt(v,T) -> exists z. BetaAt(gb,gc,v,z) /\\ "+flat(),
     ("Lt","BetaAt","NatCauchyFlatCell"),"e452b03a11c9ea2555d545f45cbc9d5dd12f4b80d9e36a49f2ee286d84dc60dc"),
    (433,"NatCauchyGrid",P+("N","gb","gc"),
     "forall k j z. Lt(k,S N) -> Lt(j,S N) -> BetaAt(gb,gc,(S N)*k+j,z) -> "+cell(),
     ("Lt","BetaAt","NatCauchyCell"),"21cd76b0fc4127a0ab9a922aeff93aca68631fe581a148c7a6e88527b38cd079"),
)
NAMED_SOURCE = "forall "+" ".join(P+("N",))+". exists gb gc. "+GRID
TARGET_SHA256 = "78d464d63eb29155ecd6adef39b240abfae271ca11d414e46e9ecc2be332a0a4"
HELPER_SOURCES = {
    "cell_exists":"forall "+" ".join(P+("k","j"))+". exists z. "+cell(),
    "flat_exists":"forall "+" ".join(P+("N","v"))+". exists z. "+flat(),
    "prefix_exists":"forall "+" ".join(P+("N","T"))+". exists gb gc. "+prefix(),
}
HELPER_TARGET_SHA256 = {
    "cell_exists":"f7028f54a0d00f93a3d85d35eeea48996fd985d0bab3d4516efd569cc96be67a",
    "flat_exists":"2331dfb07dd0155f3b1042c02d2c9111e43bab98ea8807900bebfc25460faf3e",
    "prefix_exists":"9cd43ed3a05a16923ee41c7dbafb28934a4da934faaa55e53f4f6909570385be",
}
ARCHIVES = (GRID_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a",
    "le_or_lt":"forall a b. Le(a,b) \\/ Lt(b,a)",
    "zero_le":"forall a. Le(0,a)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
    "le_eq_or_lt":"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)",
    "division_succ_exists":"forall a n. exists q r. n=(S a)*q+r /\\ Lt(r,S a)",
    "division_unique":"forall d n q r s t. n=d*q+r -> Lt(r,d) -> n=d*s+t -> Lt(t,d) -> q=s /\\ r=t",
    "padding_exists":"forall b c L i. exists a. BetaZeroExtend(b,c,L,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "beta_extend":"forall N b c v. exists eb ec. BetaAt(eb,ec,N,v) /\\ (forall j a. Lt(j,N) -> BetaAt(b,c,j,a) -> BetaAt(eb,ec,j,a))",
    "grid_index_bound":GRID_HELPERS["grid_index_bound"],
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["grid_index_bound"] = "CV012"
HELPER_DEPENDENCIES = {
    "cell_exists":("le_or_lt","add_comm","padding_exists"),
    "flat_exists":("division_succ_exists","cell_exists"),
    "prefix_exists":("zero_le","lt_not_le","le_of_succ_le_succ","le_eq_or_lt","beta_extend","flat_exists"),
    "CV044":("prefix_exists","grid_index_bound","division_unique","beta_unique"),
}


class CauchyGridError(ValueError):
    """Changed actual cell computation, conservative expansion or exact body."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(convolution_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    for number,name,parameters,source,dependencies,digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if name in registry or any(d["name"]==name or d["id"]==identifier for d in parent):
            raise CauchyGridError("Cauchy-grid conservative alias collision")
        formula = parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula))!=digest:
            raise CauchyGridError("Cauchy-grid exact expansion changed: "+name)
        text = pretty_formula(formula,list(parameters))
        d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
            summary="Actual zero-padded antidiagonal cell or quotient/remainder coded finite grid; no sum law.",
            category="irrationality_formal_series",conceptual_dependencies=dependencies)
        if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
            raise CauchyGridError("Cauchy-grid expansion failed exact roundtrip")
        registry[name] = d
    return MappingProxyType(registry)


def frozen_cauchy_grid_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CauchyGridError("CV044 exact unconditional Cauchy-grid target changed")
    return target


def source_contract():
    return dict(code="CV044",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_whole_cauchy_grid_constructed=True,triangular_zero_region_explicit=True,
        arbitrary_input_lengths_and_grid_parameter=True,grid_width="S N",
        new_definition_ids=["ND0430","ND0431","ND0432","ND0433"],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        row_column_sum_identities=False,full_convolution_evaluation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def cauchy_grid_source_pins():
    result = natural_convolution_source_pins()
    expected = {"scripts/sqrt2_power_natural_convolution.py":"a5498a8534df2e1618419bb2a4ee382d3ebd205fd024560cca9876ab9e4eedd1",
        "scripts/sqrt2_power_triple_grid.py":"6fa70f9b7b860a86c41931756c9c2ea1a1b43ca56c20274d147e63dc4b8f7f3d",
        "scripts/sqrt2_power_convolution_associative.py":"a7a442ad853eeb7c1eb0cbd15b552eb9e7213419d44ed86e1314a7e2f1a1c931",
        "scripts/sqrt2_power_convolution_unit.py":"d058762fb3641d5bb1e90c764c4581801feeaf0a103901811b3e82dbe3db8f16",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_cauchy_grid.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CauchyGridError("Cauchy-grid source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _cell_exists(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndIntro,EqRefl,OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Mul,Zero
    def chosen(t):
        product = Mul(t.term("a"),t.term("b"))
        index = _chain(specialize(t,"add_comm",*t.terms(("j","h"))),t.hyp("gap"))
        actual = witness(t.terms(("h","a","b")),conjunction(index,t.hyp("left"),t.hyp("right"),EqRefl(product)))
        return witness((product,),OrIntroL(actual))
    def finish(t):
        inside = t.hypothesis("inside")
        yes = eliminate(inside,inside.hyp("inside"),("h",),"gap",lambda u:
            eliminate(u,specialize(u,"padding_exists",*u.terms(("ab","ac","L","j"))),("a",),"left",lambda v:
                eliminate(v,specialize(v,"padding_exists",*v.terms(("bb","bc","M","h"))),("b",),"right",chosen)))
        outside = t.hypothesis("outside")
        no = witness((Zero(),),OrIntroR(AndIntro(outside.hyp("outside"),EqRefl(Zero()))))
        return OrElim(specialize(t,"le_or_lt",*t.terms(("j","k"))),yes,no)
    return introduce(s,P+("k","j"),(),finish)


def _flat_exists(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def chosen(t):
        return eliminate(t,specialize(t,"cell_exists",*t.terms(P+("k","j"))),("z",),"cell",lambda u:
            witness((u.term("z"),),witness(u.terms(("k","j")),conjunction(
                AndElimL(u.hyp("division")),AndElimR(u.hyp("division")),u.hyp("cell")))))
    return introduce(s,P+("N","v"),(),lambda t:
        eliminate(t,specialize(t,"division_succ_exists",*t.terms(("N","v"))),("k","j"),"division",chosen))


def _prefix_exists(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,BotElim,EqSym,Ind,OrElim
    from peano_lab.kernel.terms import Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("v",),("bound",),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("v"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("v"))))))
    def step(t):
        def old(u):
            def value(v):
                def extended(w):
                    def entry(x):
                        def last(y):
                            actual = witness((y.term("z"),),AndIntro(AndElimL(y.hyp("extension")),y.hyp("value")))
                            return _subst(y,registry,"exists a. BetaAt(gb,gc,slot,a) /\\ "+flat("slot","a"),EqSym(y.hyp("last")),actual)
                        def earlier(y):
                            def decoded(z):
                                kept = apply(instantiate(AndElimR(z.hyp("extension")),*z.terms(("v","a"))),z.hyp("earlier"),AndElimL(z.hyp("old_entry")))
                                return witness((z.term("a"),),AndIntro(kept,AndElimR(z.hyp("old_entry"))))
                            return eliminate(y,apply(specialize(y,"old",y.term("v")),y.hyp("earlier")),("a",),"old_entry",decoded)
                        lower = apply(specialize(x,"le_of_succ_le_succ",*x.terms(("v","T"))),x.hyp("bound"))
                        cases = apply(specialize(x,"le_eq_or_lt",*x.terms(("v","T"))),lower)
                        return OrElim(cases,last(x.hypothesis("last")),earlier(x.hypothesis("earlier")))
                    return witness(w.terms(("gb","gc")),introduce(w,("v",),("bound",),entry))
                return eliminate(v,specialize(v,"beta_extend",*v.terms(("T","ob","oc","z"))),("gb","gc"),"extension",extended)
            return eliminate(u,specialize(u,"flat_exists",*u.terms(P+("N","T"))),("z",),"value",value)
        return eliminate(t,t.hyp("IH"),("ob","oc"),"old",old)
    motive = target
    for _ in range(len(P)+2):
        motive = motive.body
    return introduce(s,P+("N",),(),lambda t:Ind(motive,base(t),introduce(t,("T",),("IH",),step)))


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ
    def codes(t):
        def cell_at(u):
            def value(v):
                def coordinates(w):
                    width = Succ(w.term("N"))
                    index = Add(Mul(width,w.term("k")),w.term("j"))
                    equal = apply(specialize(w,"division_unique",width,index,*w.terms(("r","q","k","j"))),
                        field(w.hyp("coordinates"),0,3),field(w.hyp("coordinates"),1,3),EqRefl(index),w.hyp("column"))
                    row = _subst(w,registry,cell("slot","q","e"),AndElimL(equal),field(w.hyp("coordinates"),2,3))
                    actual = _subst(w,registry,cell("k","slot","e"),AndElimR(equal),row)
                    entry_equal = apply(specialize(w,"beta_unique",*w.terms(("gb","gc")),index,*w.terms(("e","z"))),
                        AndElimL(w.hyp("entry")),w.hyp("value"))
                    return _subst(w,registry,cell("k","j","slot"),entry_equal,actual)
                return eliminate(v,AndElimR(v.hyp("entry")),("r","q"),"coordinates",coordinates)
            width = Succ(u.term("N"))
            index = Add(Mul(width,u.term("k")),u.term("j"))
            bound = apply(specialize(u,"grid_index_bound",width,*u.terms(("k","j"))),u.hyp("row"),u.hyp("column"))
            return eliminate(u,apply(specialize(u,"prefix",index),bound),("e",),"entry",value)
        return witness(t.terms(("gb","gc")),introduce(t,("k","j","z"),("row","column","value"),cell_at))
    def construct(t):
        width = Succ(t.term("N"))
        return eliminate(t,specialize(t,"prefix_exists",*t.terms(P+("N",)),Mul(width,width)),("gb","gc"),"prefix",codes)
    return introduce(s,P+("N",),(),construct)


def prove_cauchy_grid(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV044",target=frozen_cauchy_grid_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"cell_exists":_cell_exists,"flat_exists":_flat_exists,
            "prefix_exists":lambda s:_prefix_exists(s,parse_named(HELPER_SOURCES["prefix_exists"],registry=registry),registry),
            "CV044":lambda s:_root(s,registry)},
        pins=cauchy_grid_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
