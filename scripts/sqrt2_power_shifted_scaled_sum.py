"""CV043: sum a scaled finite sequence surrounded by actual zero entries.

The three premises describe decoded entries before, inside, and after a
shifted block. Both actual sum values are constructed and y=a*x is derived
by replaying finite-sum splitting, linearity and zero-tail transport.
"""
from hashlib import sha256

from sqrt2_power_sum_zero_tail import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,canonical,json_hash,
    definition_registry,sum_zero_tail_source_pins,ZERO_SUM_SOURCE,
    NAMED_SOURCE as ZERO_TAIL_SOURCE,SPLIT_SOURCE,LINEARITY_SOURCE,_subst,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_triple_row_sum import ZERO_TAIL_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-shifted-scaled-sum-v1"
P = ("ab","ac","ub","uc","s","N","q","a")
LEADING = "forall i u. Lt(i,s) -> BetaAt(ub,uc,i,u) -> u=0"
MIDDLE = "forall j b c. Lt(j,N) -> BetaAt(ab,ac,j,b) -> BetaAt(ub,uc,s+j,c) -> c=a*b"
TRAILING = "forall j. Lt(j,q) -> BetaAt(ub,uc,(s+N)+j,0)"
NAMED_SOURCE = "forall "+" ".join(P)+". ("+LEADING+") -> ("+MIDDLE+") -> ("+TRAILING+") -> exists x y. Sum(ab,ac,N,x) /\\ (Sum(ub,uc,(s+N)+q,y) /\\ y=a*x)"
TARGET_SHA256 = "6ee048a7b7670833a6caa1ec7172b086096264b73542ae00b8122a9ea9f004fa"
HELPER_SOURCES = {
    "affine_scaling":"forall ab ac ub uc s N a x y. ("+MIDDLE+") -> Sum(ab,ac,N,x) -> NatAffineSum(ub,uc,s,1,N,y) -> y=a*x",
}
HELPER_TARGET_SHA256 = {"affine_scaling":"248042087d75ab7f3a842462e1e144faf9937c0e1ca89d3a40a15ecb467fa612"}
ARCHIVES = (ZERO_TAIL_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {
    "zero_add":"forall a. 0+a=a",
    "one_mul":"forall a. 1*a=a",
    "mul_zero_left":"forall a. 0*a=0",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "linearity":LINEARITY_SOURCE,"zero_sum":ZERO_SUM_SOURCE,
    "splitting":SPLIT_SOURCE,"zero_tail":ZERO_TAIL_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:"CV011" for name in ("linearity","zero_sum","splitting","zero_tail")})
HELPER_DEPENDENCIES = {
    "affine_scaling":("one_mul","mul_zero_left","linearity"),
    "CV043":("sum_exists","splitting","zero_sum","zero_tail","affine_scaling","zero_add"),
}


class ShiftedScaledSumError(ValueError):
    """Changed actual zero padding, block scaling or exact sum target."""


def frozen_shifted_scaled_sum_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=8 or len(premises)!=3 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ShiftedScaledSumError("CV043 exact shifted scaled sum target changed")
    return target


def source_contract():
    return dict(code="CV043",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,actual_leading_and_trailing_zero_entries_required=True,
        actual_shifted_coefficient_scaling_required=True,both_actual_sum_values_constructed=True,
        arbitrary_shift_block_tail_lengths_and_zero_scalar_allowed=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",full_convolution_evaluation=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def shifted_scaled_sum_source_pins():
    result = sum_zero_tail_source_pins()
    expected = {"scripts/sqrt2_power_sum_zero_tail.py":"a4112bbf650aa6dfedf3204463a88d4d82ec3ab9f55948ad54c9423208f7d223",
        "scripts/sqrt2_power_triple_row_sum.py":"d0ee57d361f2f714862761de9416595e4520c1abd2597986a3cbef2e39dab345",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_shifted_scaled_sum.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ShiftedScaledSumError("shifted sum source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _affine_scaling(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    registry = definition_registry()
    def chosen(t):
        def pointwise(u):
            entry = apply(instantiate(AndElimL(u.hyp("slice")),*u.terms(("j","c"))),u.hyp("bound"),u.hyp("third"))
            index = CongAdd(EqRefl(u.term("s")),specialize(u,"one_mul",u.term("j")))
            actual = _subst(u,registry,"BetaAt(ub,uc,slot,c)",index,entry)
            scaled = apply(specialize(u,"middle",*u.terms(("j","b","c"))),u.hyp("bound"),u.hyp("first"),actual)
            return _chain(specialize(u,"one_mul",u.term("c")),scaled,
                EqSym(instantiate(Axiom("PA3"),Mul(u.term("a"),u.term("b")))),
                CongAdd(EqRefl(Mul(u.term("a"),u.term("b"))),EqSym(specialize(u,"mul_zero_left",u.term("d")))))
        relation = introduce(t,("j","b","d","c"),("bound","first","second","third"),pointwise)
        identity = apply(specialize(t,"linearity",t.term("a"),Zero(),Succ(Zero()),
            *t.terms(("ab","ac","ab","ac","db","dc","N","x","x","y"))),
            t.hyp("sum"),t.hyp("sum"),AndElimR(t.hyp("slice")),relation)
        return _chain(EqSym(specialize(t,"one_mul",t.term("y"))),identity,
            CongAdd(EqRefl(Mul(t.term("a"),t.term("x"))),specialize(t,"mul_zero_left",t.term("x"))),
            instantiate(Axiom("PA3"),Mul(t.term("a"),t.term("x"))))
    return introduce(s,("ab","ac","ub","uc","s","N","a","x","y"),("middle","sum","affine"),lambda t:
        eliminate(t,t.hyp("affine"),("db","dc"),"slice",chosen))


def _root(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,EqRefl
    from peano_lab.kernel.terms import Add
    def chosen(t):
        leading = apply(specialize(t,"zero_sum",*t.terms(("ub","uc","s","u"))),field(t.hyp("split"),0,4),t.hyp("leading"))
        scaled = apply(specialize(t,"affine_scaling",*t.terms(("ab","ac","ub","uc","s","N","a","x","v"))),
            t.hyp("middle"),t.hyp("sum"),field(t.hyp("split"),1,4))
        total = _chain(field(t.hyp("split"),3,4),CongAdd(leading,EqRefl(t.term("v"))),specialize(t,"zero_add",t.term("v")),scaled)
        extended = apply(specialize(t,"zero_tail",*t.terms(("ub","uc")),Add(t.term("s"),t.term("N")),*t.terms(("q","y"))),
            field(t.hyp("split"),2,4),t.hyp("trailing"))
        return witness(t.terms(("x","y")),conjunction(t.hyp("sum"),extended,total))
    return introduce(s,P,("leading","middle","trailing"),lambda t:
        eliminate(t,specialize(t,"sum_exists",*t.terms(("ab","ac","N"))),("x",),"sum",lambda u:
            eliminate(u,specialize(u,"splitting",*u.terms(("ub","uc","s","N"))),("u","v","y"),"split",chosen)))


def prove_shifted_scaled_sum(*,limits=None):
    return assemble_mixed_certificate(code="CV043",target=frozen_shifted_scaled_sum_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"affine_scaling":_affine_scaling,"CV043":_root},
        pins=shifted_scaled_sum_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
