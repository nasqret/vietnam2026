"""CV049: construct full convolution and prove its exact Horner product law.

For h[0]=0 and h[k+1]=t*h[k]+A[k], the output of length L+M satisfies
H(A*B)=t*(H(A)*H(B)). All three traces and the convolution are constructed;
the extra t, empty lengths and zero multiplier are retained.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_convolution_total import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as total_registry,convolution_total_source_pins,
    NAMED_SOURCE as TOTAL_SOURCE,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_weighted_convolution import (
    definition_registry as weighted_registry,weighted_convolution_source_pins,
    HELPER_SOURCES as WEIGHTED_HELPERS,products,table,
)
from sqrt2_power_constructed_horner_sum import NAMED_SOURCE as CONSTRUCTED_SOURCE
from sqrt2_power_horner_monomials import CONSTRUCTED_ARCHIVE
from sqrt2_power_natural_convolution import HELPER_SOURCES as CONVOLUTION_HELPERS
from sqrt2_power_sum_linearity import LINEARITY_SOURCE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-horner-product-v1"
A,B = ("ab","ac","L"),("bb","bc","M")
P = A+B+("t",)
C,D = ("cb","cc"),("db","dc")
WL,WR,WT = ("lb","lc"),("mb","mc"),("nb","nc")
QA,QB,QC = ("ub","uc"),("vb","vc"),("wb","wc")
HA,HB,HC = ("ahb","ahc"),("bhb","bhc"),("chb","chc")
FIXED = P+C+WL+WR+WT+QA+QB+QC+D
OUTPUTS = C+HA+("x",)+HB+("y",)+HC+("z",)


def conv(left,right,codes):
    return "NatConvolutionPrefix("+",".join(left+right+codes+("L+M",))+")"


def trace(codes,length,history):
    return "NatScaledHornerTrace("+",".join(codes+("t",length)+history)+")"


GRAPHS = (table(WL,"L"),table(WR,"M"),table(WT,"L+M"),
    products(A[:2],WL,QA,"L"),products(B[:2],WR,QB,"M"),products(C,WT,QC,"L+M"),
    conv(A,B,C),conv(QA+("L",),QB+("M",),D))
LABELS = ("tableA","tableB","tableC","productsA","productsB","productsC","convolutionC","convolutionD")
RELATION = "NatLinearTriple(t,0,1,db,dc,db,dc,wb,wc,L+M)"
NAMED_SOURCE = ("forall "+" ".join(P)+". exists "+" ".join(OUTPUTS)+". "+conv(A,B,C)+" /\\ ("+trace(A[:2],"L",HA)+
    " /\\ (BetaAt(ahb,ahc,L,x) /\\ ("+trace(B[:2],"M",HB)+" /\\ (BetaAt(bhb,bhc,M,y) /\\ ("+
    trace(C,"L+M",HC)+" /\\ (BetaAt(chb,chc,L+M,z) /\\ z=t*(x*y)))))))")
TARGET_SHA256 = "396f5d28929411112a14eafdfa700edebdae4db2f0d4669afc4dec841105c464"
HELPER_SOURCES = {"weighted_relation":"forall "+" ".join(FIXED)+". "+" -> ".join(GRAPHS)+" -> "+RELATION}
HELPER_TARGET_SHA256 = {"weighted_relation":"6d03a182e96f2b30217a0cc78958460c5dc841091e891af8b93d1fe39d203d31"}
TOTAL_ARCHIVE = dict(case="CV048",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-total-v2/generation-process.json.gz",
    bytes=37214,sha256="352c48a0dbb9429afafb0ac8ac64def227b8cdc35b47e73c260e6033ad4cfdb4",
    raw_bytes=876770,raw_sha256="ad9b677dbec7d0c6cee2cc6631d5eebb21d493551cce63fc4ce48c3507def9de",
    bundle_bytes=531668,bundle_sha256="e36b7cbb77811b8fac027866066f3e9f28703f247168785b2c003b12e2efc7d7",
    nodes=162,root=161,target_ast_sha256="074045ab4db4d6936b3447f35096441e7ed3857f9eb93287ea1335d93cbad0dc")
WEIGHTED_ARCHIVE = dict(case="CV042",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-weighted-convolution-v1/generation-process.json.gz",
    bytes=33155,sha256="2374941936b0882d13d6c10e93d5f4eab06e7d0a8631d7497f905b5f88823af2",
    raw_bytes=636139,raw_sha256="2d387c308228879e6fe8f96b6cba4c99ac32a41adcf055d4479ca1e92c3e7982",
    bundle_bytes=378143,bundle_sha256="fa0ff9d23182905616197f0cd573075710d2cd07a9c6f9fef7f31fe2bea7dc9f",
    nodes=148,root=147,target_ast_sha256="6537f190afaf524e595debbbbc01006bfd85ea9994906ff6b4aca84d7b4057af")
ARCHIVES = (TOTAL_ARCHIVE,WEIGHTED_ARCHIVE,CONSTRUCTED_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {
    "one_mul":"forall a. 1*a=a","mul_zero_left":"forall a. 0*a=0",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "sum_unique":"forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m",
    "prefix_exists":CONVOLUTION_HELPERS["prefix_exists"],"prefix_entry":CONVOLUTION_HELPERS["prefix_entry"],
    "coefficient_product":WEIGHTED_HELPERS["coefficient_product"],
    "constructed_sum":CONSTRUCTED_SOURCE,"convolution_total":TOTAL_SOURCE,"linearity":LINEARITY_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(coefficient_product="CV042",constructed_sum="CV039",convolution_total="CV048",linearity="CV048")
HELPER_DEPENDENCIES = {
    "weighted_relation":("beta_exists","prefix_entry","coefficient_product","one_mul","mul_zero_left"),
    "CV049":("prefix_exists","constructed_sum","convolution_total","weighted_relation","linearity","sum_unique","one_mul","mul_zero_left"),
}


class HornerProductError(ValueError):
    """Changed actual full convolution, homogeneous length or shared sum data."""


def definition_registry():
    registry = dict(total_registry())
    for name,d in weighted_registry().items():
        if name in registry and (registry[name].stable_id!=d.stable_id or registry[name].template_formula!=d.template_formula):
            raise HornerProductError("shared Horner/convolution definitions disagree")
        registry[name] = d
    return MappingProxyType(registry)


def frozen_horner_product_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerProductError("CV049 exact constructed full Horner product target changed")
    return target


def source_contract():
    return dict(code="CV049",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_convolution_and_all_three_horner_traces_constructed=True,
        full_convolution_evaluation=True,output_length="L+M",extra_multiplier_kept=True,
        empty_inputs_and_zero_multiplier_allowed=True,actual_sum_product_and_weight_compatibility_replayed=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",truncated_product_evaluation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def horner_product_source_pins():
    result = convolution_total_source_pins()
    for name,pin in weighted_convolution_source_pins().items():
        if name in result and result[name]!=pin:
            raise HornerProductError("shared proof-source pin disagreement")
        result[name] = pin
    expected = {"scripts/sqrt2_power_convolution_total.py":"e2302d22e2ec5a33b48177f3e5cd77b351b0748caf64c4a276c8e1b8d92cfc9a",
        "scripts/sqrt2_power_weighted_convolution.py":"006172a91c823b46f9d5419586a0149ee7e93d864a961d9a510a2b56bf5b2bee",
        "scripts/sqrt2_power_constructed_horner_sum.py":"c0ee9f2e584ffa89201777e4b5f586b11832b5296199d11e8d8e4cb521800fbd",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_horner_product.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerProductError("Horner product source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _weighted_relation(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def chosen(t):
        N = Add(t.term("L"),t.term("M"))
        original = apply(specialize(t,"prefix_entry",*t.terms(A+B+C),N,*t.terms(("i","c"))),t.hyp("convolutionC"),t.hyp("bound"),t.hyp("coefficient"))
        weighted = apply(specialize(t,"prefix_entry",*t.terms(QA),t.term("L"),*t.terms(QB),t.term("M"),*t.terms(D),N,*t.terms(("i","u"))),
            t.hyp("convolutionD"),t.hyp("bound"),t.hyp("first"))
        compatibility = apply(specialize(t,"coefficient_product",*t.terms(("t","L","M")+A[:2]+B[:2]+WL+WR+WT+QA+QB+("i","c","u","q"))),
            *(t.hyp(label) for label in LABELS[:5]),original,weighted,t.hyp("weight"))
        product = apply(specialize(t,"productsC",*t.terms(("i","c","q","w"))),t.hyp("bound"),t.hyp("coefficient"),t.hyp("weight"),t.hyp("third"))
        tu = Mul(t.term("t"),t.term("u"))
        return _chain(specialize(t,"one_mul",t.term("w")),product,compatibility,
            EqSym(instantiate(Axiom("PA3"),tu)),CongAdd(EqRefl(tu),EqSym(specialize(t,"mul_zero_left",t.term("v")))))
    return introduce(s,FIXED,LABELS,lambda t:
        introduce(t,("i","u","v","w"),("bound","first","second","third"),lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(C+("i",))),("c",),"coefficient",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(WT),Succ(v.term("i"))),("q",),"weight",chosen))))


def _root(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        N = Add(t.term("L"),t.term("M"))
        tables = [field(field(t.hyp(label),0,5),0,4) for label in ("dataA","dataB","dataC")]
        products = [field(t.hyp(label),1,5) for label in ("dataA","dataB","dataC")]
        relation = apply(specialize(t,"weighted_relation",*t.terms(FIXED)),*tables,*products,
            t.hyp("convolution"),field(t.hyp("total"),0,5))
        linear = apply(specialize(t,"linearity",t.term("t"),Zero(),Succ(Zero()),*t.terms(D+D+QC),N,*t.terms(("d","d","z"))),
            field(t.hyp("total"),3,5),field(t.hyp("total"),3,5),field(t.hyp("dataC"),4,5),relation)
        xa = apply(specialize(t,"sum_unique",*t.terms(QA+("L","xa","x"))),field(t.hyp("total"),1,5),field(t.hyp("dataA"),4,5))
        yb = apply(specialize(t,"sum_unique",*t.terms(QB+("M","yb","y"))),field(t.hyp("total"),2,5),field(t.hyp("dataB"),4,5))
        product = _chain(field(t.hyp("total"),4,5),CongMul(xa,yb))
        td = Mul(t.term("t"),t.term("d"))
        identity = _chain(EqSym(specialize(t,"one_mul",t.term("z"))),linear,
            CongAdd(EqRefl(td),specialize(t,"mul_zero_left",t.term("d"))),instantiate(Axiom("PA3"),td),
            CongMul(EqRefl(t.term("t")),product))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("convolution"),
            field(t.hyp("dataA"),2,5),field(t.hyp("dataA"),3,5),
            field(t.hyp("dataB"),2,5),field(t.hyp("dataB"),3,5),
            field(t.hyp("dataC"),2,5),field(t.hyp("dataC"),3,5),identity))
    def total(t):
        return eliminate(t,specialize(t,"convolution_total",*t.terms(QA),t.term("L"),*t.terms(QB),t.term("M")),D+("xa","yb","d"),"total",chosen)
    def constructed(t):
        return eliminate(t,specialize(t,"constructed_sum",*t.terms(A[:2]+("t","L"))),WL+("pl",)+QA+HA+("x",),"dataA",lambda u:
            eliminate(u,specialize(u,"constructed_sum",*u.terms(B[:2]+("t","M"))),WR+("pm",)+QB+HB+("y",),"dataB",lambda v:
                eliminate(v,specialize(v,"constructed_sum",*v.terms(C+("t",)),Add(v.term("L"),v.term("M"))),WT+("pn",)+QC+HC+("z",),"dataC",total)))
    return introduce(s,P,(),lambda t:
        eliminate(t,specialize(t,"prefix_exists",*t.terms(A+B),Add(t.term("L"),t.term("M"))),C,"convolution",constructed))


def prove_horner_product(*,limits=None):
    return assemble_mixed_certificate(code="CV049",target=frozen_horner_product_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"weighted_relation":_weighted_relation,"CV049":_root},
        pins=horner_product_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
