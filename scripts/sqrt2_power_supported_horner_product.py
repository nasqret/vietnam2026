"""CV056: exact scaled product at a support-complete shorter output length.

If A vanishes from r, B from s, r+s<=N and N+q=L+M, construct their length-N
convolution and three Horner endpoints x,y,z and p=t^q, proving p*z=t*(x*y).
The support premises and both scaling factors are retained, including t=0.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_horner_product import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as product_registry,horner_product_source_pins,
    NAMED_SOURCE as PRODUCT_SOURCE,
)
from sqrt2_power_convolution_upper_support import (
    definition_registry as upper_registry,convolution_upper_support_source_pins,
    HELPER_SOURCES as SUPPORT_HELPERS,
)
from sqrt2_power_horner_prefix_transport import (
    horner_prefix_transport_source_pins,HELPER_SOURCES as PREFIX_HELPERS,
)
from sqrt2_power_horner_zero_tail import (
    horner_zero_tail_source_pins,HELPER_SOURCES as TAIL_HELPERS,ENDPOINT_SOURCES as TAIL_ENDPOINTS,
)
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-supported-horner-product-v1"
A,B,C = ("ab","ac","L"),("bb","bc","M"),("cb","cc")
HA,HB,HC = ("ahb","ahc"),("bhb","bhc"),("chb","chc")
P = A+B+("r","s","t","N","q")
OUTPUTS = C+HA+("x",)+HB+("y",)+HC+("z","p")
FULL_OUTPUTS = C+HA+("x",)+HB+("y",)+HC+("w",)
TAIL_FIXED = A+B+("r","s","N","q")+C


def prefix(length):
    return "NatConvolutionPrefix("+",".join(A+B+C+(length,))+")"


def trace(codes,length,history):
    return "NatScaledHornerTrace("+",".join(codes+("t",length)+history)+")"


PREMISES = "NatZeroAfter(ab,ac,L,r) -> NatZeroAfter(bb,bc,M,s) -> Le(r+s,N) -> N+q=L+M -> "
ZERO_TAIL = "forall j a. Lt(j,q) -> BetaAt(cb,cc,N+j,a) -> a=0"
NAMED_SOURCE = ("forall "+" ".join(P)+". "+PREMISES+"exists "+" ".join(OUTPUTS)+". "+prefix("N")+
    " /\\ ("+trace(A[:2],"L",HA)+" /\\ (BetaAt(ahb,ahc,L,x) /\\ ("+trace(B[:2],"M",HB)+
    " /\\ (BetaAt(bhb,bhc,M,y) /\\ ("+trace(C,"N",HC)+" /\\ (BetaAt(chb,chc,N,z) /\\ (Pow(t,q,p) /\\ p*z=t*(x*y))))))))")
TARGET_SHA256 = "635fb0c8045c84285d3fe940d860ef76da985384f4e0dc4f4fbb19c8fe5c1b74"
HELPER_SOURCES = {
    "prefix_restrict":"forall "+" ".join(A+B+C+("N","T"))+". Le(N,T) -> "+prefix("T")+" -> "+prefix("N"),
    "tail_zero":"forall "+" ".join(TAIL_FIXED)+". "+PREMISES+prefix("L+M")+" -> "+ZERO_TAIL,
}
HELPER_TARGET_SHA256 = {
    "prefix_restrict":"739ddae7fe9eea747e36592b63992a95e4b553d0764b6766429d4f36451bf181",
    "tail_zero":"5bd98b4de7201d4aac955491706ffeeb40b83834469a430b270f8d947cd3ba99",
}
PRODUCT_ARCHIVE = dict(case="CV049",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-product-v1/generation-process.json.gz",
    bytes=54910,sha256="1b012515377545ad16fde6e79463fbb64c80530a20554e956d355784ca656293",
    raw_bytes=1371388,raw_sha256="9197565eea3ad15ba1405440cf35db38296ba640ec0e30de13f9a716a2ed6d2a",
    bundle_bytes=832029,bundle_sha256="07fee4d447429fe28b7c296c10327f9331046aef8d12be69574f73e21c1e09e6",
    nodes=218,root=217,target_ast_sha256="396f5d28929411112a14eafdfa700edebdae4db2f0d4669afc4dec841105c464")
SUPPORT_ARCHIVE = dict(case="CV053",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-upper-support-v1/generation-process.json.gz",
    bytes=25358,sha256="f9256a33cb0e817e438bcf35f4d87987aec2dbb0024023e756ddb26a820a0669",
    raw_bytes=437198,raw_sha256="ca1211f93b9d85010b54d66c2951d896d1222dfbec8b03081b6f18a42682d4b5",
    bundle_bytes=259719,bundle_sha256="eb53e85a3f7f6adb863962998a2b23b4c0e83382b1cec2a9e0e971829a777a45",
    nodes=127,root=126,target_ast_sha256="10fb7e6300ce6b56bf6d231d7f357343629838d1ed95469a0309b42e521c276a")
PREFIX_ARCHIVE = dict(case="CV055",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-prefix-transport-v1/generation-process.json.gz",
    bytes=20635,sha256="eea06922cc47bad7587c619ee518e49b5b40052296d6a9fd854463fc8908bb12",
    raw_bytes=312519,raw_sha256="d4225ebd6afe706984688be86d88c2666822c2282fe7bab94699e58b84e3e5dd",
    bundle_bytes=183156,bundle_sha256="6382c26066688b7d2c5cc25eb442a350ec02d7c876667e06e0b32e597dfa04f7",
    nodes=109,root=108,target_ast_sha256="6c091c8fbcbf99ab1176e5414d83f55bd66930b61f484841194d2dec7a45b4a4")
TAIL_ARCHIVE = dict(case="CV036",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-zero-tail-v1/generation-process.json.gz",
    bytes=24858,sha256="d8736c95a3d0fe2b31846befa5f453cdf32240959ddbc434bf0a0a73a48d7917",
    raw_bytes=404203,raw_sha256="e9c0f2e807b7418a5d90dbdaf4103cc6f9196da7c0c72aa493840d56739f06a4",
    bundle_bytes=237346,bundle_sha256="106c098a8896d97701ffa0444b2cadc8aafab9d4bbdab9c5603b903fb8963881",
    nodes=122,root=121,target_ast_sha256="ba1d797f495177c7c2b6f504d04e3cb81acb6460d86b60a22e46f3369a8a78d9")
ARCHIVES = (PRODUCT_ARCHIVE,SUPPORT_ARCHIVE,PREFIX_ARCHIVE,TAIL_ARCHIVE)
ENDPOINT_SOURCES = {
    "le_refl":"forall a. Le(a,a)","le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "add_comm":"forall a b. a+b=b+a","beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "full_product":PRODUCT_SOURCE,"prefix_support":SUPPORT_HELPERS["prefix_support"],
    "trace_transport":PREFIX_HELPERS["transport"],"shift_bound":TAIL_HELPERS["shift_bound"],
    "zero_tail":TAIL_HELPERS["zero_tail"],"power_exists":TAIL_ENDPOINTS["power_exists"],
}
ENDPOINT_OWNERS = {name:"CV049" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(prefix_support="CV053",trace_transport="CV055",shift_bound="CV036",zero_tail="CV036",power_exists="CV036")
HELPER_DEPENDENCIES = {
    "prefix_restrict":("le_trans",),
    "tail_zero":("prefix_support","le_trans","add_comm","shift_bound"),
    "CV056":("full_product","beta_exists","power_exists","prefix_restrict","trace_transport","tail_zero","zero_tail","add_comm","le_refl"),
}


class SupportedHornerProductError(ValueError):
    """Changed support completeness, denominator scaling or actual traces."""


def definition_registry():
    result = dict(product_registry())
    for name,d in upper_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise SupportedHornerProductError("shared product/support definitions disagree")
        result[name] = d
    return MappingProxyType(result)


def frozen_supported_horner_product_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=11 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SupportedHornerProductError("CV056 exact support-complete product target changed")
    return target


def source_contract():
    return dict(code="CV056",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,input_support_and_length_alignment_required=True,cutoff_covers_product_support_required=True,
        actual_shorter_convolution_and_three_horner_values_constructed=True,actual_scaling_power_constructed=True,
        identity="p*z=t*(x*y)",power="Pow(t,q,p)",length_alignment="N+q=L+M",
        zero_multiplier_and_empty_lengths_allowed=True,no_nonzero_factor_cancelled=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",arbitrary_truncated_product_equality=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def supported_horner_product_source_pins():
    result = horner_product_source_pins()
    for supplied in (convolution_upper_support_source_pins(),horner_prefix_transport_source_pins(),horner_zero_tail_source_pins()):
        for name,pin in supplied.items():
            if name in result and result[name]!=pin:
                raise SupportedHornerProductError("shared proof-source pins disagree")
            result[name] = pin
    expected = {"scripts/sqrt2_power_horner_product.py":"4ac5939d2b782bd459b2aed48f83852914cc06e4436ca1a1b7b5f274dfc4fbcf",
        "scripts/sqrt2_power_convolution_upper_support.py":"1d5e9cb3287218cfed8b57d1e9527cbdf7e23fe43dfc7f8fc2c90837638eb2e8",
        "scripts/sqrt2_power_horner_prefix_transport.py":"bcbb88c693bc489eae7b1f26818a9830d1cbdac42452c9c06fa60fff258d7f0a",
        "scripts/sqrt2_power_horner_zero_tail.py":"523adf2bd3c116f7de6b993b3a320ef6962bd82e75c83309634604cee44c9c3e",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_supported_horner_product.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SupportedHornerProductError("supported product source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _prefix_restrict(s):
    from peano_lab.kernel.terms import Succ
    def entry(t):
        bound = apply(specialize(t,"le_trans",Succ(t.term("i")),*t.terms(("N","T"))),t.hyp("index"),t.hyp("order"))
        return apply(specialize(t,"prefix",t.term("i")),bound)
    return introduce(s,A+B+C+("N","T"),("order","prefix"),lambda t:introduce(t,("i",),("index",),entry))


def _tail_zero(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,OrIntroL
    from peano_lab.kernel.terms import Add
    def entry(t):
        N,j = t.terms(("N","j"));index = Add(N,j)
        lower = apply(specialize(t,"le_trans",Add(t.term("r"),t.term("s")),N,index),t.hyp("cutoff"),
            witness((j,),specialize(t,"add_comm",j,N)))
        bound = apply(specialize(t,"shift_bound",N,j,t.term("q")),t.hyp("index"))
        bound = _subst(t,registry,"Lt(N+j,slot)",t.hyp("length"),bound)
        padded = OrIntroL(AndIntro(bound,t.hyp("entry")))
        support = apply(specialize(t,"prefix_support",*t.terms(A+B+("r","s")+C),Add(t.term("L"),t.term("M"))),
            t.hyp("zeroA"),t.hyp("zeroB"),t.hyp("prefix"))
        return apply(instantiate(support,index,t.term("a")),lower,padded)
    return introduce(s,TAIL_FIXED,("zeroA","zeroB","cutoff","length","prefix"),lambda t:
        introduce(t,("j","a"),("index","entry"),entry))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import EqSym,EqTrans
    from peano_lab.kernel.terms import Add
    def chosen(t):
        L,M,N,q = t.terms(("L","M","N","q"));full = Add(L,M)
        order = witness((q,),EqTrans(specialize(t,"add_comm",q,N),t.hyp("length")))
        short_prefix = apply(specialize(t,"prefix_restrict",*t.terms(A+B+C),N,full),order,field(t.hyp("product"),0,8))
        same = introduce(t,("i","a"),("index","entry"),lambda u:u.hyp("entry"))
        short_trace = apply(specialize(t,"trace_transport",*t.terms(C+C+("t",)),N,full,*t.terms(HC)),
            order,same,field(t.hyp("product"),5,8))
        tail = apply(specialize(t,"tail_zero",*t.terms(TAIL_FIXED)),t.hyp("zeroA"),t.hyp("zeroB"),t.hyp("cutoff"),t.hyp("length"),field(t.hyp("product"),0,8))
        moved_trace = _subst(t,registry,"NatScaledHornerTrace(cb,cc,t,slot,chb,chc)",EqSym(t.hyp("length")),field(t.hyp("product"),5,8))
        moved_endpoint = _subst(t,registry,"BetaAt(chb,chc,slot,w)",EqSym(t.hyp("length")),field(t.hyp("product"),6,8))
        scaling = apply(specialize(t,"zero_tail",*t.terms(C+("t","N","q")+HC+("z",))),moved_trace,t.hyp("short_value"),tail)
        endpoint = apply(instantiate(scaling,*t.terms(("q","w","p"))),specialize(t,"le_refl",q),moved_endpoint,t.hyp("power"))
        identity = EqTrans(EqSym(endpoint),field(t.hyp("product"),7,8))
        return witness(t.terms(OUTPUTS),conjunction(short_prefix,field(t.hyp("product"),1,8),field(t.hyp("product"),2,8),
            field(t.hyp("product"),3,8),field(t.hyp("product"),4,8),short_trace,t.hyp("short_value"),t.hyp("power"),identity))
    return introduce(s,P,("zeroA","zeroB","cutoff","length"),lambda t:
        eliminate(t,specialize(t,"full_product",*t.terms(A+B+("t",))),FULL_OUTPUTS,"product",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(HC+("N",))),("z",),"short_value",lambda v:
                eliminate(v,specialize(v,"power_exists",*v.terms(("t","q"))),("p",),"power",chosen))))


def prove_supported_horner_product(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV056",target=frozen_supported_horner_product_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"prefix_restrict":_prefix_restrict,"tail_zero":lambda s:_tail_zero(s,registry),"CV056":lambda s:_root(s,registry)},
        pins=supported_horner_product_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
