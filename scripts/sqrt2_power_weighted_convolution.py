"""CV042: homogeneous weighting commutes with each actual convolution coefficient.

Given three genuine geometric tables and the two pointwise product prefixes,
construct both convolution coefficients u,v and the output weight w, and prove
u*w=t*v. Indices outside the input lengths are handled by actual zero padding.
This coefficient identity is not yet the full product-evaluation theorem.
"""
from hashlib import sha256

from sqrt2_power_convolution_weights import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,convolution_weights_source_pins,
    HELPER_SOURCES as WEIGHT_HELPERS,CONVOLUTION_ARCHIVE,table,
)
from sqrt2_power_euler_product import coefficient,LINEARITY_ARCHIVE
from sqrt2_power_sum_linearity import LINEARITY_SOURCE
from sqrt2_power_composition_recurrence import PERIODIC_ARCHIVE
from sqrt2_power_periodic_convolution import HELPER_SOURCES as PERIODIC_HELPERS
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-weighted-convolution-v1"
A,B,U,V = ("ab","ac","L"),("bb","bc","M"),("ub","uc","L"),("vb","vc","M")
WL,WR,WT = ("lb","lc"),("mb","mc"),("nb","nc")
P = ("t","L","M")+A[:2]+B[:2]+WL+WR+WT+U[:2]+V[:2]+("k",)
LABELS = ("tableL","tableR","tableT","productsL","productsR")


def products(codes,weights,out,length):
    return "NatHornerWeightedPrefix("+",".join(codes+weights+out+(length,))+")"


def pad(codes,index,value):
    return "BetaZeroExtend("+",".join(codes+(index,value))+")"


def term(left,right,index,value):
    return "PolynomialDiagonalTerm("+",".join(left+right+("k",index,value))+")"


GRAPHS = (table(WL,"L"),table(WR,"M"),table(WT,"L+M"),
    products(A[:2],WL,U[:2],"L"),products(B[:2],WR,V[:2],"M"))
PREMISES = " -> ".join(GRAPHS)+" -> "
RESULT = coefficient(A,B,"k","u")+" /\\ ("+coefficient(U,V,"k","v")+" /\\ (BetaAt(nb,nc,S k,w) /\\ u*w=t*v))"
NAMED_SOURCE = "forall "+" ".join(P)+". "+PREMISES+"exists u v w. "+RESULT
TARGET_SHA256 = "6537f190afaf524e595debbbbc01006bfd85ea9994906ff6b4aca84d7b4057af"
HELPER_SOURCES = {
    "mul_swap":"forall a b c. a*(b*c)=b*(a*c)",
    "shuffle":"forall a b t p q. (a*b)*(t*(p*q))=t*((a*p)*(b*q))",
    "padded_product":"forall "+" ".join(P+("i","j","a","b","x","y","w"))+". "+PREMISES+
        "i+j=k -> "+pad(A,"i","a")+" -> "+pad(B,"j","b")+" -> "+pad(U,"i","x")+" -> "+pad(V,"j","y")+
        " -> BetaAt(nb,nc,S k,w) -> (a*b)*w=t*(x*y)",
    "term_product":"forall "+" ".join(P+("i","x","y","w"))+". "+PREMISES+
        term(A,B,"i","x")+" -> "+term(U,V,"i","y")+" -> BetaAt(nb,nc,S k,w) -> x*w=t*y",
    "coefficient_product":"forall "+" ".join(P+("u","v","w"))+". "+PREMISES+
        coefficient(A,B,"k","u")+" -> "+coefficient(U,V,"k","v")+" -> BetaAt(nb,nc,S k,w) -> u*w=t*v",
}
HELPER_TARGET_SHA256 = {
    "mul_swap":"dacbf2e7ff423b37cf847a3b1ce181d4e71a0b0a580472b4b098a3d89c5c742f",
    "shuffle":"ccee9b7bd8e09d51f956e303503e2fe9de47f4f0b149df4b4576dc582a731e40",
    "padded_product":"0625a2d550a27fe71596b6449066458058e703d4cc418f23457b25a744a26d59",
    "term_product":"1c1608031c8b04a688e6a4a4a22f8151b9ceaea2e09b42e549e279a5895249fb",
    "coefficient_product":"f760b69d331143bcccec51ef9cc334ffa72ab20f007ee78cafb4e85b30aa7eac",
}
WEIGHT_ARCHIVE = dict(case="CV041",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-weights-v1/generation-process.json.gz",
    bytes=28976,sha256="7a32920feb43cddffa6bcf387cdb91bcbdb5ceb4d22ddb0ba3a4ae544e227014",
    raw_bytes=540833,raw_sha256="ee0fc41a0f84d907a2d055062f5cd4b6db786a67125bbd9e9ac197a561b5c803",
    bundle_bytes=319346,bundle_sha256="9d6be9a12cba3dd86cda9629336da3aa6a5c55902974c818f3fddb9f2a5d4e23",
    nodes=135,root=134,target_ast_sha256="2673216a113a76804e456d1ac260a39e3d0707fa44828c7d4e784d90e55e6f87")
ARCHIVES = (WEIGHT_ARCHIVE,CONVOLUTION_ARCHIVE,LINEARITY_ARCHIVE,PERIODIC_ARCHIVE)
ENDPOINT_SOURCES = {
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "mul_comm":"forall a b. a*b=b*a",
    "mul_zero_left":"forall a. 0*a=0",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "padding_exists":"forall b c L i. exists a. BetaZeroExtend(b,c,L,i,a)",
    "padding_unique":"forall b c L i a d. BetaZeroExtend(b,c,L,i,a) -> BetaZeroExtend(b,c,L,i,d) -> a=d",
    "term_unique":"forall ab ac L bb bc M i j t s. PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,s) -> t=s",
    "diagonal_entry":"forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)",
    "coefficient_exists":"forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)",
    "weights_product":WEIGHT_HELPERS["weights_product"],
    "unpad":PERIODIC_HELPERS["unpad"],
    "sum_linearity":LINEARITY_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(weights_product="CV041",unpad="CV027",sum_linearity="CV006")
HELPER_DEPENDENCIES = {
    "mul_swap":("mul_assoc","mul_comm"),
    "shuffle":("mul_assoc","mul_swap"),
    "padded_product":("beta_exists","padding_unique","unpad","weights_product","shuffle","mul_zero_left"),
    "term_product":("padding_exists","term_unique","padded_product"),
    "coefficient_product":("diagonal_entry","term_product","sum_linearity","mul_comm","mul_zero_left"),
    "CV042":("coefficient_exists","beta_exists","coefficient_product"),
}


class WeightedConvolutionError(ValueError):
    """Changed actual weighted terms, coefficient graph or resource contract."""


def frozen_weighted_convolution_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=len(P) or len(premises)!=5 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise WeightedConvolutionError("CV042 exact coefficient multiplication target changed")
    return target


def source_contract():
    return dict(code="CV042",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,actual_three_geometric_tables_required=True,actual_two_weighted_prefixes_required=True,
        both_actual_convolution_coefficients_and_output_weight_constructed=True,
        all_natural_indices_and_zero_multiplier_allowed=True,extra_multiplier_kept=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",full_convolution_evaluation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def weighted_convolution_source_pins():
    result = convolution_weights_source_pins()
    expected = {"scripts/sqrt2_power_convolution_weights.py":"94fd0d579a0fff2ea100d3d56688674f9f53dade0daa6145cad098bd9aeb96f3",
        "scripts/sqrt2_power_composition_recurrence.py":"8989d3b556c1b00602e75b34807a98b5d730864271edfacf329c6898863f9547",
        "scripts/sqrt2_power_periodic_convolution.py":"aeb95ee2da8e89f07b421c9e743d2bf87e8a765505d9c919df70b51d3ce2c02d",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_weighted_convolution.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise WeightedConvolutionError("weighted coefficient source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _mul_swap(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    return introduce(s,("a","b","c"),(),lambda t:_chain(
        EqSym(specialize(t,"mul_assoc",*t.terms(("a","b","c")))),
        CongMul(specialize(t,"mul_comm",*t.terms(("a","b"))),EqRefl(t.term("c"))),
        specialize(t,"mul_assoc",*t.terms(("b","a","c")))))


def _shuffle(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(u):
        a,b,t,p,q = u.terms(("a","b","t","p","q"))
        return _chain(specialize(u,"mul_swap",Mul(a,b),t,Mul(p,q)),
            CongMul(EqRefl(t),_chain(specialize(u,"mul_assoc",a,b,Mul(p,q)),
                CongMul(EqRefl(a),specialize(u,"mul_swap",b,p,q)),
                EqSym(specialize(u,"mul_assoc",a,p,Mul(b,q))))))
    return introduce(s,("a","b","t","p","q"),(),finish)


def _padded_product(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,AndIntro,CongMul,EqRefl,EqSym,OrElim,OrIntroR
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def both(t):
        a,b,x,y,w,t0,pa,pb = t.terms(("a","b","x","y","w","t","pa","pb"))
        left_bound,right_bound = AndElimL(t.hyp("insideA")),AndElimL(t.hyp("insideB"))
        actual_x = apply(specialize(t,"unpad",*t.terms(U+("i","x"))),left_bound,t.hyp("padX"))
        actual_y = apply(specialize(t,"unpad",*t.terms(V+("j","y"))),right_bound,t.hyp("padY"))
        xe = apply(specialize(t,"productsL",*t.terms(("i","a","pa","x"))),left_bound,
            AndElimR(t.hyp("insideA")),t.hyp("weightL"),actual_x)
        ye = apply(specialize(t,"productsR",*t.terms(("j","b","pb","y"))),right_bound,
            AndElimR(t.hyp("insideB")),t.hyp("weightR"),actual_y)
        weights = apply(specialize(t,"weights_product",*t.terms(("t","L","M")+WL+WR+WT)),
            *(t.hyp(label) for label in LABELS[:3]))
        we = apply(instantiate(weights,*t.terms(("i","j","k","pa","pb","w"))),left_bound,right_bound,
            t.hyp("index"),t.hyp("weightL"),t.hyp("weightR"),t.hyp("weightT"))
        return _chain(CongMul(EqRefl(Mul(a,b)),we),specialize(t,"shuffle",a,b,t0,pa,pb),
            CongMul(EqRefl(t0),CongMul(EqSym(xe),EqSym(ye))))
    def outside(t,left):
        a,b,x,y,w,t0 = t.terms(("a","b","x","y","w","t"))
        label,codes,index,value,padding = ("outsideA",U,"i","x","padX") if left else ("outsideB",V,"j","y","padY")
        outside_data = t.hyp(label)
        value_zero = apply(specialize(t,"padding_unique",*t.terms(codes+(index,value)),Zero()),t.hyp(padding),
            OrIntroR(AndIntro(AndElimL(outside_data),EqRefl(Zero()))))
        if left:
            lhs_zero = _chain(CongMul(AndElimR(outside_data),EqRefl(b)),specialize(t,"mul_zero_left",b))
            rhs_zero = _chain(CongMul(value_zero,EqRefl(y)),specialize(t,"mul_zero_left",y))
        else:
            lhs_zero = _chain(CongMul(EqRefl(a),AndElimR(outside_data)),instantiate(Axiom("PA5"),a))
            rhs_zero = _chain(CongMul(EqRefl(x),value_zero),instantiate(Axiom("PA5"),x))
        return _chain(CongMul(lhs_zero,EqRefl(w)),specialize(t,"mul_zero_left",w),
            EqSym(instantiate(Axiom("PA5"),t0)),CongMul(EqRefl(t0),EqSym(rhs_zero)))
    def inside(t):
        u = t.hypothesis("insideB")
        constructed = eliminate(u,specialize(u,"beta_exists",*u.terms(WL),Succ(u.term("i"))),("pa",),"weightL",lambda v:
            eliminate(v,specialize(v,"beta_exists",*v.terms(WR),Succ(v.term("j"))),("pb",),"weightR",both))
        return OrElim(t.hyp("padB"),constructed,outside(t.hypothesis("outsideB"),False))
    return introduce(s,P+("i","j","a","b","x","y","w"),LABELS+("index","padA","padB","padX","padY","weightT"),lambda t:
        OrElim(t.hyp("padA"),inside(t.hypothesis("insideA")),outside(t.hypothesis("outsideA"),True)))


def _term_product(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def chosen(t):
        a,b,c,d,t0 = t.terms(("a","b","c","d","t"))
        data = t.hyp("cell")
        reference = witness(t.terms(("j","c","d")),conjunction(field(data,0,4),t.hyp("padC"),t.hyp("padD"),EqRefl(Mul(c,d))))
        ye = apply(specialize(t,"term_unique",*t.terms(U+V+("k","i","y")),Mul(c,d)),t.hyp("termY"),reference)
        identity = apply(specialize(t,"padded_product",*t.terms(P+("i","j","a","b","c","d","w"))),
            *(t.hyp(label) for label in LABELS),field(data,0,4),field(data,1,4),field(data,2,4),t.hyp("padC"),t.hyp("padD"),t.hyp("weightT"))
        return _chain(CongMul(field(data,3,4),EqRefl(t.term("w"))),identity,CongMul(EqRefl(t0),EqSym(ye)))
    return introduce(s,P+("i","x","y","w"),LABELS+("termX","termY","weightT"),lambda t:
        eliminate(t,t.hyp("termX"),("j","a","b"),"cell",lambda u:
            eliminate(u,specialize(u,"padding_exists",*u.terms(U+("i",))),("c",),"padC",lambda v:
                eliminate(v,specialize(v,"padding_exists",*v.terms(V+("j",))),("d",),"padD",chosen))))


def _coefficient_product(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def chosen(t):
        def pointwise(u):
            def entry(left,right,codes,label,value):
                return apply(specialize(u,"diagonal_entry",*u.terms(left+right+("k",)+codes),Succ(u.term("k")),*u.terms(("i",value))),
                    AndElimL(u.hyp(label)),u.hyp("bound"),u.hyp(value+"_value"))
            identity = apply(specialize(u,"term_product",*u.terms(P+("i","z","x","w"))),
                *(u.hyp(label) for label in LABELS),entry(A,B,("db","dc"),"original","z"),
                entry(U,V,("eb","ec"),"weighted","x"),u.hyp("weightT"))
            return _chain(specialize(u,"mul_comm",*u.terms(("w","z"))),identity,
                EqSym(instantiate(Axiom("PA3"),Mul(u.term("t"),u.term("x")))),
                CongAdd(EqRefl(Mul(u.term("t"),u.term("x"))),EqSym(specialize(u,"mul_zero_left",u.term("y")))))
        relation = introduce(t,("i","x","y","z"),("bound","x_value","y_value","z_value"),pointwise)
        linear = apply(specialize(t,"sum_linearity",t.term("t"),Zero(),t.term("w"),
            *t.terms(("eb","ec","eb","ec","db","dc")),Succ(t.term("k")),*t.terms(("v","v","u"))),
            AndElimR(t.hyp("weighted")),AndElimR(t.hyp("weighted")),AndElimR(t.hyp("original")),relation)
        return _chain(specialize(t,"mul_comm",*t.terms(("u","w"))),linear,
            CongAdd(EqRefl(Mul(t.term("t"),t.term("v"))),specialize(t,"mul_zero_left",t.term("v"))),
            instantiate(Axiom("PA3"),Mul(t.term("t"),t.term("v"))))
    return introduce(s,P+("u","v","w"),LABELS+("coefficientA","coefficientB","weightT"),lambda t:
        eliminate(t,t.hyp("coefficientA"),("db","dc"),"original",lambda u:
            eliminate(u,u.hyp("coefficientB"),("eb","ec"),"weighted",chosen)))


def _root(s):
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        identity = apply(specialize(t,"coefficient_product",*t.terms(P+("u","v","w"))),
            *(t.hyp(label) for label in LABELS+("coefficientA","coefficientB","weightT")))
        return witness(t.terms(("u","v","w")),conjunction(t.hyp("coefficientA"),t.hyp("coefficientB"),t.hyp("weightT"),identity))
    return introduce(s,P,LABELS,lambda t:
        eliminate(t,specialize(t,"coefficient_exists",*t.terms(A+B+("k",))),("u",),"coefficientA",lambda u:
            eliminate(u,specialize(u,"coefficient_exists",*u.terms(U+V+("k",))),("v",),"coefficientB",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(WT),Succ(v.term("k"))),("w",),"weightT",chosen))))


def prove_weighted_convolution(*,limits=None):
    return assemble_mixed_certificate(code="CV042",target=frozen_weighted_convolution_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"mul_swap":_mul_swap,"shuffle":_shuffle,"padded_product":_padded_product,
            "term_product":_term_product,"coefficient_product":_coefficient_product,"CV042":_root},
        pins=weighted_convolution_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
