"""AP004: every supplied finite sample has the required analytic inputs.

The computation-only graph does not assume positivity or correctness laws.
Derive nonzero input/output denominators, input <= 1, the exact recurrence
and all-index normalization for every supplied graph with positive scale D.
"""
from hashlib import sha256

from sqrt2_power_exp_sample import (
    ROOT,Scope,introduce,eliminate,witness,conjunction,apply,specialize,field,canonical,json_hash,_and,
    definition_registry,exp_sample_source_pins,DEFINITION_PARAMETERS as PARAMETERS,
    GRAPH,PARTS as CONSTRUCTED_PARTS,ARGUMENT_GRAPH,ARGUMENT_OUTPUTS,
)
from sqrt2_power_log_root_argument import HELPER_SOURCES as ARGUMENT_HELPERS,BOUND_SOURCE
from sqrt2_power_dyadic_sqrt2_square_error import NAMED_SOURCE as SQUARE_SOURCE,dyadic_sqrt2_square_error_source_pins
from sqrt2_power_dyadic_sqrt2_reciprocal import SQUARE_ARCHIVE
from sqrt2_power_scaled_exp_terms import HELPER_SOURCES as EXP_HELPERS
from sqrt2_power_weight_factorials import HELPER_SOURCES as WEIGHT_HELPERS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-supplied-exp-sample-v1"
PARTS=CONSTRUCTED_PARTS[1:]
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~D=0 -> "+GRAPH+" -> "+_and(PARTS)
TARGET_SHA256="2579d5bd54a8bf1f91831ce86386ca747605c6022da544548553dc22186cb198"
HELPER_SOURCES={
    "equal_nonzero":"forall a b. a=b -> ~b=0 -> ~a=0",
    "factorial_nonzero":"forall n f. Factorial(n,f) -> ~f=0",
    "argument":"forall "+" ".join(("k",)+ARGUMENT_OUTPUTS)+". ~D=0 -> "+ARGUMENT_GRAPH+" -> ~((D*p)*s)=0 /\\ Le((3*x)*d,(D*p)*s)",
}
HELPER_TARGET_SHA256={"equal_nonzero":"c02b457ac2822dd082af17be7aad7fea120fd2d421e90d497bd1bfb6cdf68505",
    "factorial_nonzero":"c8e3edc22283f308044d98445b607e929cb442e21546943204e6a9395fc19b71",
    "argument":"40621d294640360d51c6f077ddcc36533e44a07a004e3337673d12752a504369"}
SAMPLE_ARCHIVE=dict(case="AP002",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-sample-v1/generation-process.json.gz",
    bytes=46428,sha256="5a85f9f0dca7326fb057721704cb1100726386cdc2db885b33f13b21d9a13316",
    raw_bytes=899735,raw_sha256="494be859c97d8831cabc3cfde7f77a5ad11d42de432e6acc1a11e6169317315e",
    bundle_bytes=522625,bundle_sha256="254ee848b9237c568db4089d6f5460ffcf482cbd5b4d6aa34ec8937eaaa075e9",
    nodes=186,root=185,target_ast_sha256="934fbe9c81ad757420933f697a47c0e82aa1b3e12a326f07d6080b94c7c3e24f")
ARCHIVES=(SAMPLE_ARCHIVE,SQUARE_ARCHIVE)
ENDPOINT_SOURCES={
    "argument_bounds":ARGUMENT_HELPERS["bounds"],"inner_bound":BOUND_SOURCE,"square":SQUARE_SOURCE,
    "weight_invariant":WEIGHT_HELPERS["invariant"],"recurrence":EXP_HELPERS["recurrence"],"normalization":EXP_HELPERS["normalization"],
    "factorial_zero":"forall n f. n=0 -> Factorial(n,f) -> f=1",
    "factorial_step":"forall n sn f. sn=S n -> Factorial(sn,f) -> exists g. Factorial(n,g) /\\ f=g*(S n)",
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0","mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0",
}
ENDPOINT_OWNERS={name:"AP002" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["square"]="SQ009"
HELPER_DEPENDENCIES={
    "equal_nonzero":(),"factorial_nonzero":("factorial_zero","factorial_step","succ_ne_zero","mul_ne_zero","equal_nonzero"),
    "argument":("argument_bounds","inner_bound","square","power_nonzero","succ_ne_zero"),
    "AP004":("argument","factorial_nonzero","power_nonzero","mul_ne_zero","equal_nonzero","weight_invariant","recurrence","normalization"),
}


class SuppliedExpSampleError(ValueError):
    """Changed supplied computation, scale guard, exact law or source."""


def frozen_supplied_exp_sample_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=16 or len(premises)!=2 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SuppliedExpSampleError("AP004 exact supplied-sample target changed")
    return target


def source_contract():
    return dict(code="AP004",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,positive_coefficient_scale_required=True,all_supplied_graph_witnesses_preserved=True,
        no_replacement_code_or_existential_constructor_used=True,output_and_argument_denominators_proved_nonzero=True,
        argument_bound_one_proved=True,same_table_recurrence_and_all_index_normalization_proved=True,
        new_definition_ids=[],definition_admissions=0,new_induction_count=1,
        factorial_nonzero_by_explicit_HA_induction=True,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def supplied_exp_sample_source_pins():
    result=exp_sample_source_pins()
    for name,pin in dyadic_sqrt2_square_error_source_pins().items():
        if name in result and result[name]!=pin:
            raise SuppliedExpSampleError("supplied-sample source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_sample.py":"7062977d78a2ee1445e396d8e970460d1d366a36e8dc211c28e8c64b905adb46",
        "scripts/sqrt2_power_dyadic_sqrt2_square_error.py":"8fd7a8ae82f1cfccf25dffa649624af229c3bd11069b9dee0bb8bd6df47c66e0",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_supplied_exp_sample.py","scripts/sqrt2_power_dyadic_sqrt2_reciprocal.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SuppliedExpSampleError("supplied-sample source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _equal_nonzero(s,registry):
    from peano_lab.kernel.proofs import EqSym
    return introduce(s,("a","b"),("equal","nonzero"),lambda t:
        _subst(t,registry,"~slot=0",EqSym(t.hyp("equal")),t.hyp("nonzero")))


def _factorial_nonzero(s,target):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    one=Succ(Zero())
    def base(t):
        f=t.term("f")
        equal=apply(specialize(t,"factorial_zero",Zero(),f),EqRefl(Zero()),t.hyp("factorial"))
        return apply(specialize(t,"equal_nonzero",f,one),equal,specialize(t,"succ_ne_zero",Zero()))
    def step(t):
        def chosen(u):
            n,g,f=u.terms(("n","g","f"));data=u.hyp("predecessor")
            nz=apply(specialize(u,"IH",g),AndElimL(data))
            product=apply(specialize(u,"mul_ne_zero",g,Succ(n)),nz,specialize(u,"succ_ne_zero",n))
            return apply(specialize(u,"equal_nonzero",f,Mul(g,Succ(n))),AndElimR(data),product)
        return eliminate(t,apply(specialize(t,"factorial_step",t.term("n"),Succ(t.term("n")),t.term("f")),
            EqRefl(Succ(t.term("n"))),t.hyp("factorial")),("g",),"predecessor",chosen)
    return Ind(target.body,introduce(s,("f",),("factorial",),base),
        introduce(s,("n",),("IH",),lambda t:introduce(t,("f",),("factorial",),step)))


def _argument(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()));three=Succ(two)
    def finish(t):
        k,d,root,D,ab,ac,x,p=t.terms(("k",)+ARGUMENT_OUTPUTS);graph=t.hyp("graph")
        square=apply(specialize(t,"square",k,d,root),field(graph,0,4))
        power=apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",two))
        pnz=apply(instantiate(power,Succ(Mul(two,k)),p),field(graph,3,4))
        inner=apply(specialize(t,"inner_bound",D,ab,ac,Mul(two,k),x,p),field(graph,1,4),field(graph,2,4),field(graph,3,4))
        return apply(specialize(t,"argument_bounds",D,p,x,d,root),t.hyp("scale_nonzero"),pnz,field(square,1,6),field(square,2,6),inner)
    return introduce(s,("k",)+ARGUMENT_OUTPUTS,("scale_nonzero","graph"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two=Succ(Succ(Zero()));three=Succ(two)
    def finish(t):
        graph=t.hyp("graph");k,d,root,D,x,p,w0,f,h=t.terms(("k","d","s","D","x","p","w0","f","h"))
        v=Mul(Mul(D,p),root);u=Mul(Mul(three,x),d);N=Add(k,two)
        argument=apply(specialize(t,"argument",*t.terms(("k",)+ARGUMENT_OUTPUTS)),t.hyp("scale_nonzero"),field(graph,0,9))
        vnz=AndElimL(argument)
        fnz=apply(specialize(t,"factorial_nonzero",N,f),field(graph,5,9))
        hnz=apply(instantiate(apply(specialize(t,"power_nonzero",v),vnz),N,h),field(graph,6,9))
        product=apply(specialize(t,"mul_ne_zero",f,h),fnz,hnz)
        nonzero=apply(specialize(t,"equal_nonzero",w0,Mul(f,h)),field(graph,7,9),product)
        recurrence=apply(specialize(t,"recurrence",v,u,N,*t.terms(("wb","wc","tb","tc"))),field(graph,1,9),field(graph,2,9))
        invariant=apply(specialize(t,"weight_invariant",v,N,*t.terms(("wb","wc")),w0),field(graph,1,9),field(graph,3,9))
        normalization=apply(specialize(t,"normalization",v,u,N,*t.terms(("wb","wc","tb","tc")),w0),invariant,field(graph,2,9))
        return conjunction(nonzero,vnz,AndElimR(argument),recurrence,normalization)
    return introduce(s,PARAMETERS,("scale_nonzero","graph"),finish)


def prove_supplied_exp_sample(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP004",target=frozen_supplied_exp_sample_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"equal_nonzero":lambda s:_equal_nonzero(s,registry),
            "factorial_nonzero":lambda s:_factorial_nonzero(s,parse_named(HELPER_SOURCES["factorial_nonzero"],registry=registry)),
            "argument":_argument,"AP004":_root},pins=supplied_exp_sample_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
