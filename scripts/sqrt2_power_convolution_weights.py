"""CV041: multiplicative compatibility of constructed geometric weights.

Construct weights and powers for L,M,L+M and prove
W_(L+M)[i+j+1]=t*(W_L[i+1]*W_M[j+1]) for i<L,j<M.
The extra t is essential for length-L+M homogeneous evaluation. The actual
Kummer power-addition proof is replayed, never admitted as an oracle.
"""
from hashlib import sha256

from sqrt2_power_horner_monomials import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,horner_monomials_source_pins,
    HELPER_SOURCES as MONOMIAL_HELPERS,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_constructed_horner_sum import GEOMETRIC_ARCHIVE
from sqrt2_power_geometric_weights import NAMED_SOURCE as GEOMETRIC_SOURCE,ENDPOINT_SOURCES as POWER_ENDPOINTS
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-convolution-weights-v1"
L,R,T = ("lb","lc"),("mb","mc"),("nb","nc")
OUTPUTS = L+("pl",)+R+("pm",)+T+("pn",)
FIXED = ("t","L","M")+L+R+T


def table(codes,length):
    return "NatGeometricWeightTable("+",".join(("t",length)+codes)+")"


def data(codes,p,length):
    b,c = codes
    return table(codes,length)+" /\\ (Pow(t,"+length+","+p+") /\\ (BetaAt("+b+","+c+",0,"+p+") /\\ (forall j w q. Le(j,"+length+") -> BetaAt("+b+","+c+",j,w) -> Pow(t,j,q) -> w*q="+p+")))"


PRODUCT = "forall i j k a b c. Lt(i,L) -> Lt(j,M) -> i+j=k -> BetaAt(lb,lc,S i,a) -> BetaAt(mb,mc,S j,b) -> BetaAt(nb,nc,S k,c) -> c=t*(a*b)"
NAMED_SOURCE = "forall t L M. exists "+" ".join(OUTPUTS)+". ("+data(L,"pl","L")+") /\\ (("+data(R,"pm","M")+") /\\ (("+data(T,"pn","L+M")+") /\\ ("+PRODUCT+")))"
TARGET_SHA256 = "2673216a113a76804e456d1ac260a39e3d0707fa44828c7d4e784d90e55e6f87"
HELPER_SOURCES = {
    "index_shuffle":"forall i j u v. S(i+j)+S(u+v)=((S i)+u)+((S j)+v)",
    "weights_product":"forall "+" ".join(FIXED)+". "+table(L,"L")+" -> "+table(R,"M")+" -> "+table(T,"L+M")+" -> "+PRODUCT,
}
HELPER_TARGET_SHA256 = {
    "index_shuffle":"1c8f542c886a050fbb2da0681aeb43d23d6a29e787c23f06dc8372a3c3b67b1a",
    "weights_product":"3721b8286abe92da901468356513b32409a944cc3474a6d6d4971f5bbeda98ee",
}
MONOMIAL_ARCHIVE = dict(case="CV040",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-monomials-v1/generation-process.json.gz",
    bytes=30227,sha256="fb82bb6fd33be8b88d999cd59fe2ca4b1db7cfc9e25bfa72564a8a7cb66c25f4",
    raw_bytes=571917,raw_sha256="041113025dcd26f783f92ae1847c1b32fdcf6d47b58359cc82a8c06b35faabbd",
    bundle_bytes=340745,bundle_sha256="c01db734918315570a4e104464a29d4f6932796b37d351bae01926e53c12e496",
    nodes=142,root=141,target_ast_sha256="76c2e7135bb0294d18ddca7f6750fc378916725dd05a107878f9dc22c55483d1")
KUMMER_ARCHIVE = dict(case="kummer-power-add-v1",format="raw-canonical",
    path="research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json",
    bytes=1528814,sha256="49fd86708fe5b289d0159526285e73b2aea008c26e0eb41ae8a053c970d4210e",
    nodes=281,root=280,target_ast_sha256="f9318d8f2aa260e18f490b9f054f648526b4f954f9816836834e0fb550739de0")
ARCHIVES = (MONOMIAL_ARCHIVE,GEOMETRIC_ARCHIVE,CONVOLUTION_ARCHIVE,KUMMER_ARCHIVE)
ENDPOINT_SOURCES = {name:POWER_ENDPOINTS[name] for name in ("power_exists","power_step","mul_comm")}
ENDPOINT_SOURCES.update(add_succ_left="forall a b. S a+b=S (a+b)",add_comm="forall a b. a+b=b+a",
    add_assoc="forall a b c. (a+b)+c=a+(b+c)",geometric_exists=GEOMETRIC_SOURCE,
    complement=MONOMIAL_HELPERS["complement"],
    power_add="forall a e f s x y z. s=e+f -> Pow(a,e,x) -> Pow(a,f,y) -> Pow(a,s,z) -> z=x*y")
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(power_exists="CV038",power_step="CV038",geometric_exists="CV038",
    complement="CV040",power_add="kummer-power-add-v1")
HELPER_DEPENDENCIES = {
    "index_shuffle":("add_succ_left","add_assoc","add_comm"),
    "weights_product":("power_exists","power_step","power_add","complement","index_shuffle","add_comm","mul_comm"),
    "CV041":("geometric_exists","weights_product"),
}


class ConvolutionWeightsError(ValueError):
    """Changed actual geometric weights, exponent law or length alignment."""


def frozen_convolution_weights_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=3 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionWeightsError("CV041 exact convolution weight construction changed")
    return target


def source_contract():
    return dict(code="CV041",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,three_geometric_tables_and_power_values_constructed=True,
        all_in_range_convolution_weights_related=True,extra_multiplier_kept=True,
        zero_multiplier_and_empty_lengths_allowed=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        archived_power_add_metadata_is_authority=False,full_convolution_evaluation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def convolution_weights_source_pins():
    result = horner_monomials_source_pins()
    expected = {"scripts/sqrt2_power_horner_monomials.py":"e3975073b1e51c13dd703502964c512ac3f5aa0d7f3b5fc6d9bf0b5f05f3ac61",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_convolution_weights.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionWeightsError("convolution weight source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _index_shuffle(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain,_additive_equal
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongS,EqSym
    from peano_lab.kernel.terms import Add,Succ
    def finish(t):
        i,j,u,v = t.terms(("i","j","u","v"))
        ij,uv,iu,jv = Add(i,j),Add(u,v),Add(i,u),Add(j,v)
        left = _chain(specialize(t,"add_succ_left",ij,Succ(uv)),CongS(instantiate(Axiom("PA4"),ij,uv)),
            CongS(CongS(_additive_equal(t,Add(ij,uv),Add(iu,jv)))))
        right = _chain(CongAdd(specialize(t,"add_succ_left",i,u),specialize(t,"add_succ_left",j,v)),
            specialize(t,"add_succ_left",iu,Succ(jv)),CongS(instantiate(Axiom("PA4"),iu,jv)))
        return _chain(left,EqSym(right))
    return introduce(s,("i","j","u","v"),(),finish)


def _weights_product(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,CongMul,CongS,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def chosen(t):
        i,j,k,u,v,t0 = t.terms(("i","j","k","u","v","t"))
        uv = Add(u,v)
        indexL = _chain(specialize(t,"add_comm",Succ(i),u),t.hyp("gapL"))
        indexR = _chain(specialize(t,"add_comm",Succ(j),v),t.hyp("gapR"))
        indexT = _chain(CongAdd(CongS(EqSym(t.hyp("index"))),EqRefl(Succ(uv))),
            specialize(t,"index_shuffle",i,j,u,v),CongAdd(indexL,indexR))
        def same(codes,length,exponent,index,value,power,table_label,entry_label,power_label):
            all_weights = apply(specialize(t,"complement",t0,length,*t.terms(codes)),t.hyp(table_label))
            return apply(instantiate(all_weights,exponent,index,t.term(value),t.term(power)),
                indexL if table_label=="tableL" else indexR if table_label=="tableR" else indexT,
                t.hyp(entry_label),t.hyp(power_label))
        a_pa = same(L,t.term("L"),u,Succ(i),"a","pa","tableL","weightL","powerL")
        b_pb = same(R,t.term("M"),v,Succ(j),"b","pb","tableR","weightR","powerR")
        c_pc = same(T,Add(t.term("L"),t.term("M")),Succ(uv),Succ(k),"c","pc","tableT","weightT","powerT")
        product = apply(specialize(t,"power_add",t0,u,v,uv,*t.terms(("pa","pb","pab"))),
            EqRefl(uv),t.hyp("powerL"),t.hyp("powerR"),AndElimL(t.hyp("power_data")))
        return _chain(c_pc,AndElimR(t.hyp("power_data")),CongMul(product,EqRefl(t0)),
            specialize(t,"mul_comm",Mul(t.term("pa"),t.term("pb")),t0),CongMul(EqRefl(t0),CongMul(EqSym(a_pa),EqSym(b_pb))))
    def powers(t):
        def decomposed(u):
            uv = Add(u.term("u"),u.term("v"))
            step = apply(specialize(u,"power_step",u.term("t"),uv,Succ(uv),u.term("pc")),EqRefl(Succ(uv)),u.hyp("powerT"))
            return eliminate(u,step,("pab",),"power_data",chosen)
        return eliminate(t,specialize(t,"power_exists",*t.terms(("t","u"))),("pa",),"powerL",lambda u:
            eliminate(u,specialize(u,"power_exists",*u.terms(("t","v"))),("pb",),"powerR",lambda v:
                eliminate(v,specialize(v,"power_exists",v.term("t"),Succ(Add(v.term("u"),v.term("v")))),("pc",),"powerT",decomposed)))
    return introduce(s,FIXED,("tableL","tableR","tableT"),lambda t:
        introduce(t,("i","j","k","a","b","c"),("boundL","boundR","index","weightL","weightR","weightT"),lambda u:
            eliminate(u,u.hyp("boundL"),("u",),"gapL",lambda v:
                eliminate(v,v.hyp("boundR"),("v",),"gapR",powers))))


def _root(s):
    from peano_lab.kernel.terms import Add
    def chosen(t):
        relation = apply(specialize(t,"weights_product",*t.terms(FIXED)),field(t.hyp("dataL"),0,4),field(t.hyp("dataR"),0,4),field(t.hyp("dataT"),0,4))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("dataL"),t.hyp("dataR"),t.hyp("dataT"),relation))
    return introduce(s,("t","L","M"),(),lambda t:
        eliminate(t,specialize(t,"geometric_exists",*t.terms(("t","L"))),L+("pl",),"dataL",lambda u:
            eliminate(u,specialize(u,"geometric_exists",*u.terms(("t","M"))),R+("pm",),"dataR",lambda v:
                eliminate(v,specialize(v,"geometric_exists",v.term("t"),Add(v.term("L"),v.term("M"))),T+("pn",),"dataT",chosen))))


def prove_convolution_weights(*,limits=None):
    return assemble_mixed_certificate(code="CV041",target=frozen_convolution_weights_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"index_shuffle":_index_shuffle,"weights_product":_weights_product,"CV041":_root},
        pins=convolution_weights_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
