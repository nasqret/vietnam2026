"""AP014: the actual fixed shift power 2^8 dominates the finite error constant.

Construct 2^5, reconstruct its value 32 with ordinary power laws, and compare
it to the supplied 2^8. Closed arithmetic uses a deliberately tiny value-32
proof-producing evaluator; host integer evaluation is never proof authority.
No unary 256, huge beta code, new induction or enlarged kernel limit is used.
"""
from hashlib import sha256

from sqrt2_power_positive_power_comparison import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,definition_registry,
    positive_power_comparison_source_pins,NAMED_SOURCE as COMPARISON_SOURCE,ENDPOINT_SOURCES as POWER_ENDPOINTS,BOUND_ARCHIVE,
)
from sqrt2_power_approximation_power_bounds import COMPARISON_ARCHIVE
from sqrt2_power_quadratic_trace_exists import eliminate,witness,conjunction
from sqrt2_power_exp_two_sided_continuity import _left,_chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-fixed-precision-threshold-v1"
COEFFICIENT="((9*3)+2)"
NAMED_SOURCE="forall v. Pow(2,8,v) -> ~v=0 /\\ Le("+COEFFICIENT+",v)"
TARGET_SHA256="2ec3a5c39030d975d8ddf79a41d7793afd4f5fdfd25bcd49657f7335af0fba3c"
HELPER_SOURCES={"constant_bound":"Le("+COEFFICIENT+",32)","length":"5+3=8",
    "power_five":"forall v. Pow(2,5,v) -> v=32"}
HELPER_TARGET_SHA256={"constant_bound":"6991e3e2e606fd7338db837fd13f6acfe0ff205830ca4ee2588e7b531ef034a9",
    "length":"5031108d37fa8f203eeef23769e8eca6df22e3d9913afb854ddd78a82abce152",
    "power_five":"9102c8ce47fab5f40033937333c36b45be2ca8e76c84c645be0d82a8cd63b08a"}
ARCHIVES=(COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={"comparison":COMPARISON_SOURCE,
    **{n:POWER_ENDPOINTS[n] for n in ("power_zero","power_step","power_exists","power_nonzero")},
    "le_refl":"forall a. Le(a,a)","le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "succ_ne_zero":"forall a. ~S a=0"}
ENDPOINT_OWNERS={name:"AP010" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(le_refl="CV071",le_trans="CV071",succ_ne_zero="CV071")
HELPER_DEPENDENCIES={"constant_bound":(),"length":(),"power_five":("power_zero","power_step"),
    "AP014":("constant_bound","length","power_five","comparison","power_exists","power_nonzero","le_refl","le_trans","succ_ne_zero")}


class FixedPrecisionThresholdError(ValueError):
    """Changed actual fixed power, conservative threshold or small evaluator cap."""


def frozen_fixed_precision_threshold_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or len(premises)!=1 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FixedPrecisionThresholdError("AP014 exact supplied fixed-power threshold changed")
    return target


def source_contract():
    return dict(code="AP014",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,actual_supplied_eighth_power_preserved=True,actual_fifth_power_constructed=True,
        supplied_eighth_power_nonzero_proved=True,threshold="(9*3)+2 <= 2^8",ground_evaluator_max_value=32,
        ground_evaluator_max_input_nodes=512,ground_evaluator_max_depth=64,ground_evaluation_is_proof_authority=False,
        fixed_unrolling_steps=5,unary_256_introduced=False,new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def fixed_precision_threshold_source_pins():
    result=positive_power_comparison_source_pins()
    expected={"scripts/sqrt2_power_positive_power_comparison.py":"381cd294ff30012ed53978ec2590eb3d8da009339ea342af90fa3ec876bbebd4",
        "scripts/sqrt2_power_approximation_power_bounds.py":"ef4401c17fb3c3ddf0ef47aaea1ea5396a5c658ed6eb4e88d4349256cf5f9856",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_fixed_precision_threshold.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FixedPrecisionThresholdError("fixed-power threshold source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _n(value):
    from peano_lab.kernel.terms import Succ,Zero
    if type(value) is not int or not 0<=value<=32:
        raise FixedPrecisionThresholdError("fixed arithmetic value exceeds 32")
    result=Zero()
    for _ in range(value):
        result=Succ(result)
    return result


def _ground_equal(left,right):
    """Emit ordinary PA3--PA6 equality constructors for tiny closed terms only."""
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,CongS,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def add(a,b):
        if b==0:
            return instantiate(Axiom("PA3"),_n(a))
        return _chain(instantiate(Axiom("PA4"),_n(a),_n(b-1)),CongS(add(a,b-1)))
    def mul(a,b):
        if b==0:
            return instantiate(Axiom("PA5"),_n(a))
        return _chain(instantiate(Axiom("PA6"),_n(a),_n(b-1)),CongAdd(mul(a,b-1),EqRefl(_n(a))),add(a*(b-1),a))
    count=0
    def evaluate(term,depth=1):
        nonlocal count
        count+=1
        if count>512 or depth>64:
            raise FixedPrecisionThresholdError("fixed arithmetic input structure exceeds cap")
        if type(term) is Zero:
            return 0,EqRefl(term)
        if type(term) is Succ:
            value,proof=evaluate(term.term,depth+1);_n(value+1)
            return value+1,CongS(proof)
        if type(term) not in (Add,Mul):
            raise FixedPrecisionThresholdError("fixed arithmetic requires closed PA terms")
        a,pa=evaluate(term.left,depth+1);b,pb=evaluate(term.right,depth+1)
        value=a+b if type(term) is Add else a*b
        _n(value)
        return value,_chain(CongAdd(pa,pb),add(a,b)) if type(term) is Add else _chain(CongMul(pa,pb),mul(a,b))
    a,pa=evaluate(left);b,pb=evaluate(right)
    if a!=b:
        raise FixedPrecisionThresholdError("fixed arithmetic equality is false")
    return _chain(pa,EqSym(pb))


def _constant_bound(s):
    from peano_lab.kernel.terms import Add,parse_term
    return witness((_n(3),),_ground_equal(Add(_n(3),parse_term(COEFFICIENT)),_n(32)))


def _length(s):
    from peano_lab.kernel.terms import Add
    return _ground_equal(Add(_n(5),_n(3)),_n(8))


def _power_five(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl
    from peano_lab.kernel.terms import Mul
    def unroll(t,n,name,power,finish):
        if not 0<=n<=5:
            raise FixedPrecisionThresholdError("fixed power unrolling exceeds five steps")
        if n==0:
            return finish(t,apply(specialize(t,"power_zero",_n(2),_n(0),t.term(name)),EqRefl(_n(0)),power))
        variable="previous_"+str(n);label="step_"+str(n)
        step=apply(specialize(t,"power_step",_n(2),_n(n-1),_n(n),t.term(name)),EqRefl(_n(n)),power)
        def chosen(u):
            def continued(v,earlier):
                return finish(v,_chain(AndElimR(v.hyp(label)),CongMul(earlier,EqRefl(_n(2))),
                    _ground_equal(Mul(_n(2**(n-1)),_n(2)),_n(2**n))))
            # Keep existential eliminations outside synthesizing equality
            # constructors; all old hypotheses are resolved in the live scope.
            return unroll(u,n-1,variable,AndElimL(u.hyp(label)),continued)
        return eliminate(t,step,(variable,),label,chosen)
    return introduce(s,("v",),("power",),lambda t:unroll(t,5,"v",t.hyp("power"),lambda u,proof:proof))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import parse_term
    def chosen(t):
        v,x=t.terms(("v","x"));nonzero=specialize(t,"succ_ne_zero",_n(1))
        aligned=_subst(t,registry,"Pow(2,slot,v)",EqSym(t.hyp("length")),t.hyp("power"))
        bound=apply(specialize(t,"comparison",_n(2),_n(2),_n(5),_n(3),x,v),specialize(t,"le_refl",_n(2)),nonzero,t.hyp("fifth"),aligned)
        value=apply(specialize(t,"power_five",x),t.hyp("fifth"))
        bound=_left(t,registry,bound,v,value)
        bound=apply(specialize(t,"le_trans",parse_term(COEFFICIENT),_n(32),v),t.hyp("constant_bound"),bound)
        vnz=apply(instantiate(apply(specialize(t,"power_nonzero",_n(2)),nonzero),_n(8),v),t.hyp("power"))
        return conjunction(vnz,bound)
    return introduce(s,("v",),("power",),lambda t:eliminate(t,specialize(t,"power_exists",_n(2),_n(5)),("x",),"fifth",chosen))


def prove_fixed_precision_threshold(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP014",target=frozen_fixed_precision_threshold_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"constant_bound":_constant_bound,"length":_length,"power_five":_power_five,"AP014":lambda s:_root(s,registry)},
        pins=fixed_precision_threshold_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
