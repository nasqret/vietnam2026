"""AP040: extending actual natural input prefixes increases convolution.

The beta codes stay fixed while both input lengths may grow. Prove padded
entry order, actual diagonal-product order and finite-sum order. This is a
finite comparison for the exponential addition sandwich, not a tail bound.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_sum_linear_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as source_registry,
    NAMED_SOURCE as SUM_BOUND_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_sum_continuity import SUM_BOUND_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_approximation_record_error import approximation_record_error_source_pins
from sqrt2_power_euler_product import coefficient
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-convolution-prefix-order-v1'
A,B,C,D=('ab','ac','L'),('bb','bc','M'),('ab','ac','N'),('bb','bc','O')
P=('ab','ac','L','bb','bc','M','N','O','i')
NAMED_SOURCE='forall '+' '.join(P+('u','v'))+'. Le(L,N) -> Le(M,O) -> '+coefficient(A,B,'i','u')+' -> '+coefficient(C,D,'i','v')+' -> Le(u,v)'
TARGET_SHA256='a4ddc6ed1dd2d269caed60e2cc1647676c11767abf060d3c1641e5d50ed1adb0'
LOW_TERM='PolynomialDiagonalTerm('+','.join(A+B+('i','j','u'))+')'
HIGH_TERM='PolynomialDiagonalTerm('+','.join(C+D+('i','j','v'))+')'
SUM_RELATION='forall j a b. Lt(j,N) -> BetaAt(ab,ac,j,a) -> BetaAt(bb,bc,j,b) -> Le(a,b)'
HELPER_SOURCES={
    'padded_order':'forall b c L N j a z. Le(L,N) -> BetaZeroExtend(b,c,L,j,a) -> BetaZeroExtend(b,c,N,j,z) -> Le(a,z)',
    'sum_order':'forall ab ac bb bc N u v. ('+SUM_RELATION+') -> Sum(ab,ac,N,u) -> Sum(bb,bc,N,v) -> Le(u,v)',
    'term_order':'forall '+' '.join(P+('j','u','v'))+'. Le(L,N) -> Le(M,O) -> '+LOW_TERM+' -> '+HIGH_TERM+' -> Le(u,v)',
}
HELPER_TARGET_SHA256={
    'padded_order':'bc89e439ef54cb596a43a3430a75646caacb4afca6ee08a4547bbf2d0661de19',
    'sum_order':'3a2806a0e958e1d4ab9820d541ced337440eb63ca3ec202ca42a3b906e1bd4e9',
    'term_order':'6672b2deb2411a0713672ab011a1965964b5e0dd28e0760e91879b31c82279ee'}
ARCHIVES=(CONVOLUTION_ARCHIVE,BOUND_ARCHIVE,SUM_BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    'zero_le':'forall a. Le(0,a)','le_refl':'forall a. Le(a,a)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'one_mul':'forall a. 1*a=a','zero_mul':'forall a. 0*a=0',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'padding_exists':'forall b c L i. exists a. BetaZeroExtend(b,c,L,i,a)',
    'padding_unique':'forall b c L i a d. BetaZeroExtend(b,c,L,i,a) -> BetaZeroExtend(b,c,L,i,d) -> a=d',
    'term_unique':'forall ab ac L bb bc M i j t s. PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,s) -> t=s',
    'diagonal_entry':'forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)',
    'sum_bound':SUM_BOUND_SOURCE,
}
ENDPOINT_OWNERS={name:'CV003' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(mul_left_mono='CV071',mul_right_mono='CV071',sum_bound='CV095')
HELPER_DEPENDENCIES={
    'padded_order':('le_trans','padding_unique','zero_le','le_refl'),
    'sum_order':('sum_bound','one_mul','zero_mul'),
    'term_order':('padding_exists','term_unique','padded_order','mul_right_mono','mul_left_mono','le_trans'),
    'AP040':('diagonal_entry','term_order','sum_order'),
}


class ConvolutionPrefixOrderError(ValueError):
    """Changed actual codes, ordered lengths, coefficient or source bytes."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatConvolutionCoefficient','NatLinearBound']
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ConvolutionPrefixOrderError('existing finite coefficient order definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_convolution_prefix_order_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=11 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionPrefixOrderError('AP040 exact same-code convolution prefix order changed')
    return target


def source_contract():
    return dict(code='AP040',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,both_actual_input_beta_codes_preserved=True,both_input_length_orders_required=True,
        actual_supplied_convolution_coefficients_preserved=True,arbitrary_coefficient_index=True,
        empty_input_lengths_and_equal_lengths_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,quantitative_tail_bound=False,
        analytic_exponential_addition=False,analytic_limit_claim=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def convolution_prefix_order_source_pins():
    result=approximation_record_error_source_pins()
    expected={'scripts/sqrt2_power_approximation_record_error.py':'502e49bdd7da5c8b4945e40228d81403e9df74847e1d5472d00104f9152781b4',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_convolution_prefix_order.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionPrefixOrderError('coefficient prefix order source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _padded_order(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,EqSym,OrElim,OrIntroL
    from peano_lab.kernel.terms import Succ
    def finish(t):
        def inside(u):
            L,N,j,a,z=u.terms(('L','N','j','a','z'));data=u.hyp('inside')
            bound=apply(specialize(u,'le_trans',Succ(j),L,N),AndElimL(data),u.hyp('length'))
            bigger=OrIntroL(AndIntro(bound,AndElimR(data)))
            equal=apply(specialize(u,'padding_unique',*u.terms(('b','c','N','j','a','z'))),bigger,u.hyp('long'))
            return _right(u,registry,specialize(u,'le_refl',a),a,equal)
        def outside(u):
            return _left(u,registry,specialize(u,'zero_le',u.term('z')),u.term('z'),EqSym(AndElimR(u.hyp('outside'))))
        return OrElim(t.hyp('short'),inside(t.hypothesis('inside')),outside(t.hypothesis('outside')))
    return introduce(s,('b','c','L','N','j','a','z'),('length','short','long'),finish)


def _sum_order(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        zero=Zero();one=Succ(zero)
        def normalized(u,a,b):
            return _chain(CongAdd(specialize(u,'one_mul',a),specialize(u,'zero_mul',b)),instantiate(Axiom('PA3'),a))
        def pointwise(u):
            a,b,c=u.terms(('a','b','c'))
            order=apply(specialize(u,'pointwise',u.term('j'),c,a),u.hyp('bound'),u.hyp('third'),u.hyp('first'))
            order=_left(u,registry,order,a,EqSym(specialize(u,'one_mul',c)))
            return _right(u,registry,order,Mul(one,c),EqSym(normalized(u,a,b)))
        relation=introduce(t,('j','a','b','c'),('bound','first','second','third'),pointwise)
        u,v=t.terms(('u','v'))
        bound=apply(specialize(t,'sum_bound',one,zero,one,*t.terms(('bb','bc','bb','bc','ab','ac','N','v','v','u'))),
            relation,t.hyp('long_sum'),t.hyp('long_sum'),t.hyp('short_sum'))
        bound=_left(t,registry,bound,Add(Mul(one,v),Mul(zero,v)),specialize(t,'one_mul',u))
        return _right(t,registry,bound,u,normalized(t,v,v))
    return introduce(s,('ab','ac','bb','bc','N','u','v'),('pointwise','short_sum','long_sum'),finish)


def _term_order(s,registry):
    from peano_lab.kernel.proofs import EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def chosen(t):
        k,a,b,c,d,u,v=t.terms(('k','a','b','c','d','u','v'));data=t.hyp('high_data')
        candidate=witness((k,a,b),conjunction(field(data,0,4),t.hyp('left_pad'),t.hyp('right_pad'),EqRefl(Mul(a,b))))
        same=apply(specialize(t,'term_unique',*t.terms(A+B+('i','j','u')),Mul(a,b)),t.hyp('low_term'),candidate)
        left=apply(specialize(t,'padded_order',*t.terms(('ab','ac','L','N','j','a','c'))),t.hyp('left_length'),t.hyp('left_pad'),field(data,1,4))
        right=apply(specialize(t,'padded_order',*t.terms(('bb','bc','M','O','k','b','d'))),t.hyp('right_length'),t.hyp('right_pad'),field(data,2,4))
        first=apply(specialize(t,'mul_right_mono',a,c,b),left)
        second=apply(specialize(t,'mul_left_mono',b,d,c),right)
        out=apply(specialize(t,'le_trans',Mul(a,b),Mul(c,b),Mul(c,d)),first,second)
        out=_left(t,registry,out,Mul(c,d),EqSym(same))
        return _right(t,registry,out,u,EqSym(field(data,3,4)))
    return introduce(s,P+('j','u','v'),('left_length','right_length','low_term','high_term'),lambda t:
        eliminate(t,t.hyp('high_term'),('k','c','d'),'high_data',lambda u:
            eliminate(u,specialize(u,'padding_exists',*u.terms(A+('j',))),('a',),'left_pad',lambda v:
                eliminate(v,specialize(v,'padding_exists',*v.terms(B+('k',))),('b',),'right_pad',chosen))))


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ
    def decoded(t):
        def pointwise(u):
            i,j,a,b=u.terms(('i','j','a','b'));si=Succ(i)
            low=apply(specialize(u,'diagonal_entry',*u.terms(A+B),i,*u.terms(('lb','lc')),si,j,a),
                AndElimL(u.hyp('low_data')),u.hyp('bound'),u.hyp('low_entry'))
            high=apply(specialize(u,'diagonal_entry',*u.terms(C+D),i,*u.terms(('hb','hc')),si,j,b),
                AndElimL(u.hyp('high_data')),u.hyp('bound'),u.hyp('high_entry'))
            return apply(specialize(u,'term_order',*u.terms(P+('j','a','b'))),u.hyp('left_length'),u.hyp('right_length'),low,high)
        relation=introduce(t,('j','a','b'),('bound','low_entry','high_entry'),pointwise)
        return apply(specialize(t,'sum_order',*t.terms(('lb','lc','hb','hc')),Succ(t.term('i')),*t.terms(('u','v'))),
            relation,AndElimR(t.hyp('low_data')),AndElimR(t.hyp('high_data')))
    return introduce(s,P+('u','v'),('left_length','right_length','low_coefficient','high_coefficient'),lambda t:
        eliminate(t,t.hyp('low_coefficient'),('lb','lc'),'low_data',lambda u:
            eliminate(u,u.hyp('high_coefficient'),('hb','hc'),'high_data',decoded)))


def prove_convolution_prefix_order(*,limits=None):
    registry=definition_registry()
    factories={'padded_order':lambda s:_padded_order(s,registry),'sum_order':lambda s:_sum_order(s,registry),
        'term_order':lambda s:_term_order(s,registry),'AP040':_root}
    return assemble_mixed_certificate(code='AP040',target=frozen_convolution_prefix_order_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories,pins=convolution_prefix_order_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
