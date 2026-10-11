"""AP073: a horizon-independent majorant for every bounded rational argument.

Construct a positive reference computation at L*d, apply AP072 there and
transport AP069's cross-normalized monotonicity from the supplied table.
The actual head of the supplied table may be zero. No analytic exponential
or positivity assumption for that supplied head is inserted as an axiom.
"""
from hashlib import sha256

from sqrt2_power_exp_integer_majorant import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,canonical,json_hash,
    source_registry,definition_registry,exp_integer_majorant_source_pins,
    NAMED_SOURCE as INTEGER_SOURCE,CONSTRUCTED_SOURCE,EXP_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_relative_cross_continuity import (
    NAMED_SOURCE as RELATIVE_SOURCE,exp_relative_cross_continuity_source_pins,
)
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-bounded-majorant-v1'
PARAMETERS=('L','d','x','N','ab','ac','h','s','C')
PREMISES=('~d=0','Le(x,L*d)','NatScaledExpRecurrence(d,x,ab,ac,N)',
    'BetaAt(ab,ac,0,h)','Sum(ab,ac,S N,s)','Pow(9,S L,C)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> Le(s,C*h)'
TARGET_SHA256='b50deb3120bcff57e9f7bb87d27d0227041c2cae062f4de207339d31f41a23ff'
INTEGER_ARCHIVE=dict(case='AP072',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-integer-majorant-v1/generation-process.json.gz',
    bytes=98553,sha256='679bb471e7a8c793e05d84bd35aef016bcabb7c97de2df1a21a17eacabed5762',
    raw_bytes=1939561,raw_sha256='ed5853a617c4103df309afd6c945fac672dd028980710dad17f61fae99794a80',
    bundle_bytes=1139220,bundle_sha256='9211e4b07e0c954f47f5621b318226c957dbe6d4b59a960dfe098b91fcefa839',
    nodes=267,root=266,target_ast_sha256='0c8801ad08d671c34b8ab3b48766c6133267c4b5abfd1b796eb18c6422b8d237')
RELATIVE_ARCHIVE=dict(case='AP069',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-relative-cross-continuity-v1/generation-process.json.gz',
    bytes=38471,sha256='5308e44b0cb446c2e8ac48c35425a0af4e36ea25b2ea5e4da799d894cbbad0a4',
    raw_bytes=673583,raw_sha256='10f8a2f005a72b7f3ba609ab9afa9bb5cb1045973ee8eea765686cb6b98b30e7',
    bundle_bytes=384083,bundle_sha256='1f05df465a0a247f69b287823dcc92b3d2c728cb3808e5b3aa561dc6edcec249',
    nodes=144,root=143,target_ast_sha256='bd0a751f36b51993e4a8a1c8d3802afe6e72a7304960b031618cbee1c6e66f62')
ARCHIVES=(INTEGER_ARCHIVE,RELATIVE_ARCHIVE,EXP_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'integer':INTEGER_SOURCE,'constructed':CONSTRUCTED_SOURCE,'relative':RELATIVE_SOURCE,
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','add_comm':'forall a b. a+b=b+a',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(integer='AP072',constructed='CV070',relative='AP069')
HELPER_DEPENDENCIES={'AP073':tuple(ENDPOINT_SOURCES)}
REFERENCE_OUTPUTS=('wb','wc','bb','bc','b','f','q','t')


class ExpBoundedMajorantError(ValueError):
    """Changed supplied rational computation, integer bound or positive reference."""


def frozen_exp_bounded_majorant_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=9 or len(premises)!=6 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpBoundedMajorantError('AP073 exact horizon-independent rational-argument majorant changed')
    return target


def source_contract():
    return dict(code='AP073',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=6,actual_recurrence_head_sum_and_power_preserved=True,
        argument_upper_bound='x<=L*d',supplied_power='C=9^(L+1)',bound='s<=C*h',
        uniform_in_finite_horizon=True,majorant_independent_of_argument_denominator=True,
        actual_positive_integer_reference_constructed=True,only_reference_head_cancelled=True,
        zero_argument_supplied_head_and_horizon_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,large_ground_power_materialized=False,
        analytic_exponential_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_bounded_majorant_source_pins():
    result=exp_integer_majorant_source_pins()
    for name,pin in exp_relative_cross_continuity_source_pins().items():
        if name in result and result[name]!=pin:raise ExpBoundedMajorantError('bounded-majorant dependency source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_integer_majorant.py':'a85c1978e6b349a30ca64251239d1d2b9425fa2e71f6c0be5b0d73bf324f543f',
        'scripts/sqrt2_power_exp_relative_cross_continuity.py':'2b94325a395b0996433d4d134687fb8f222c9e8d6082ba8479919f170b60e9d5',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_bounded_majorant.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpBoundedMajorantError('bounded-majorant source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        L,d,x,N,h,out,C,k,b,v=t.terms(('L','d','x','N','h','s','C','k','b','t'))
        reference=t.hyp('reference');top=Mul(L,d);gap=Mul(d,k)
        exact=_chain(CongMul(EqRefl(d),EqSym(t.hyp('argument_gap'))),
            specialize(t,'mul_add',d,k,x),specialize(t,'add_comm',gap,Mul(d,x)))
        relative=apply(specialize(t,'relative',d,d,x,top,gap,N,*t.terms(('ab','ac','bb','bc')),h,b,out,v),
            t.hyp('nonzero'),t.hyp('nonzero'),exact,t.hyp('recurrence'),field(reference,9,11),
            t.hyp('head'),field(reference,3,11),t.hyp('sum'),field(reference,8,11))
        integer=apply(specialize(t,'integer',L,d,N,*t.terms(('bb','bc')),b,v,C),
            t.hyp('nonzero'),field(reference,9,11),field(reference,3,11),field(reference,8,11),t.hyp('power'))
        bound=apply(specialize(t,'mul_left_mono',v,Mul(C,b),h),integer)
        bound=_subst(t,registry,'Le(h*t,slot)',_multiplicative_equal(t,Mul(h,Mul(C,b)),Mul(b,Mul(C,h))),bound)
        bound=apply(specialize(t,'le_trans',Mul(b,out),Mul(h,v),Mul(b,Mul(C,h))),AndElimL(relative),bound)
        return apply(specialize(t,'mul_le_cancel',b,out,Mul(C,h)),field(reference,4,11),bound)
    def bounded(t):
        return eliminate(t,apply(specialize(t,'constructed',t.term('d'),Mul(t.term('L'),t.term('d')),t.term('N')),t.hyp('nonzero')),
            REFERENCE_OUTPUTS,'reference',finish)
    def start(t):
        return eliminate(t,t.hyp('argument_bound'),('k',),'argument_gap',bounded)
    return introduce(s,PARAMETERS,('nonzero','argument_bound','recurrence','head','sum','power'),start)


def prove_exp_bounded_majorant(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP073',target=frozen_exp_bounded_majorant_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP073':lambda s:_root(s,registry)},pins=exp_bounded_majorant_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
