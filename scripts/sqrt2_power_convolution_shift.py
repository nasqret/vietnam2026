"""AP037: transport a denominator-cleared shift through a Cauchy coefficient.

Only indices through i are related. The shifted input has a proved zero head;
the input lengths may differ and all scalars may be zero. Actual diagonals,
affine slicing and finite weighted linearity derive the coefficient identity.
This is a finite prerequisite for the exponential addition recurrence.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_convolution_commutative import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,canonical,json_hash,
    definition_registry as source_registry,HELPER_SOURCES as COMM_HELPERS,_one_add,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_convolution_associative import COMM_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_euler_product import LINEARITY_ARCHIVE,coefficient
from sqrt2_power_sum_linearity import LINEARITY_SOURCE
from sqrt2_power_natural_fubini import HELPER_SOURCES as AFFINE_HELPERS
from sqrt2_power_sum_splitting import FUBINI_ARCHIVE
from sqrt2_power_log_exp_witness import log_exp_witness_source_pins
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-convolution-shift-v1'
A,B,C=('ab','ac','L'),('bb','bc','M'),('cb','cc','K')
P=('alpha','gamma')+A+B+C+('i',)
HEAD='BetaZeroExtend(cb,cc,K,0,0)'
RELATION='forall j a c. Le(j,i) -> BetaZeroExtend(ab,ac,L,j,a) -> BetaZeroExtend(cb,cc,K,S j,c) -> gamma*c=alpha*a'
NAMED_SOURCE='forall '+' '.join(P+('u','v'))+'. '+HEAD+' -> ('+RELATION+') -> '+coefficient(A,B,'i','u')+' -> '+coefficient(C,B,'S i','v')+' -> gamma*v=alpha*u'
TARGET_SHA256='d3eb18cd8e8c76b563ea0fbc13a70b6de3140d1c177e036fa23a2411b01980b2'
SUM_RELATION='forall j a b. Lt(j,N) -> BetaAt(ab,ac,j,a) -> BetaAt(bb,bc,S j,b) -> gamma*b=alpha*a'
LOW_TERM='PolynomialDiagonalTerm('+','.join(A+B+('i','j','u'))+')'
HIGH_TERM='PolynomialDiagonalTerm('+','.join(C+B+('S i','S j','v'))+')'
HELPER_SOURCES={
    'sum_shift':'forall alpha gamma ab ac bb bc N u v. Sum(ab,ac,N,u) -> Sum(bb,bc,S N,v) -> BetaAt(bb,bc,0,0) -> ('+SUM_RELATION+') -> gamma*v=alpha*u',
    'term_zero':'forall cb cc K bb bc M i v. '+HEAD+' -> PolynomialDiagonalTerm(cb,cc,K,bb,bc,M,S i,0,v) -> v=0',
    'term_shift':'forall '+' '.join(P+('j','u','v'))+'. ('+RELATION+') -> Le(j,i) -> '+LOW_TERM+' -> '+HIGH_TERM+' -> gamma*v=alpha*u',
}
HELPER_TARGET_SHA256={
    'sum_shift':'49498b99e28c88cd125fe76b74427e51481f681f8368636940a0d97374984d06',
    'term_zero':'22792c2e203ac31971844a01b928f3beab6a31c428b8ad91e5fcd2468f7d185b',
    'term_shift':'06920b69efdc86c58a1a390e83dc6499172c5dba3e4ff2c059c4340cb87ec54f'}
ARCHIVES=(CONVOLUTION_ARCHIVE,COMM_ARCHIVE,LINEARITY_ARCHIVE,FUBINI_ARCHIVE)
ENDPOINT_SOURCES={
    'zero_add':'forall a. 0+a=a','zero_mul':'forall a. 0*a=0',
    'one_mul':'forall a. 1*a=a','add_succ_left':'forall a b. S a+b=S(a+b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'zero_le':'forall a. Le(0,a)','succ_le_succ':'forall a b. Le(a,b) -> Le(S a,S b)',
    'le_of_succ':'forall a b. Le(S a,S b) -> Le(a,b)',
    'beta_exists':'forall b c i. exists a. BetaAt(b,c,i,a)',
    'padding_exists':'forall b c L i. exists a. BetaZeroExtend(b,c,L,i,a)',
    'padding_unique':'forall b c L i a d. BetaZeroExtend(b,c,L,i,a) -> BetaZeroExtend(b,c,L,i,d) -> a=d',
    'term_unique':'forall ab ac L bb bc M i j t s. PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,s) -> t=s',
    'diagonal_entry':'forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)',
    'head_tail':COMM_HELPERS['head_tail'],'slice_sum_exists':AFFINE_HELPERS['slice_sum_exists'],
    'linearity':LINEARITY_SOURCE,
}
ENDPOINT_OWNERS={name:'CV003' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(head_tail='CV010',slice_sum_exists='CV008',linearity='CV006')
HELPER_DEPENDENCIES={
    'sum_shift':('slice_sum_exists','head_tail','linearity','zero_mul','zero_add','one_mul','add_succ_left'),
    'term_zero':('padding_unique','zero_mul'),
    'term_shift':('padding_exists','term_unique','add_succ_left','mul_assoc'),
    'AP037':('sum_shift','term_zero','term_shift','beta_exists','zero_le','succ_le_succ','le_of_succ','diagonal_entry'),
}


class ConvolutionShiftError(ValueError):
    """Changed actual shift, zero head, coefficient or source evidence."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatConvolutionCoefficient','NatAffineSum','NatLinearTriple']
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ConvolutionShiftError('existing finite convolution definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_convolution_shift_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=14 or len(premises)!=4 or type(conclusion) is not Eq or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionShiftError('AP037 exact finite coefficient shift changed')
    return target


def source_contract():
    return dict(code='AP037',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,actual_supplied_coefficients_and_padded_inputs_preserved=True,
        proved_zero_shifted_head_required=True,only_indices_through_coefficient_required=True,
        arbitrary_input_lengths_and_zero_scalars_allowed=True,empty_input_lengths_allowed=True,
        exact_coefficient_identity='gamma*(C*B)[i+1]=alpha*(A*B)[i]',
        actual_diagonal_head_and_shifted_tail_used=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_exponential_identity=False,
        analytic_limit_claim=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def convolution_shift_source_pins():
    result=log_exp_witness_source_pins()
    expected={'scripts/sqrt2_power_log_exp_witness.py':'19b9cc3b4f66db42decc879fca3df056136e02c80c86e6b5fd1369c47d5df16f',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_convolution_shift.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionShiftError('coefficient-shift source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _sum_shift(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,Axiom,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def sliced(t):
        def pointwise(u):
            j,a,b=u.terms(('j','a','b'));one=Succ(Zero())
            at=apply(instantiate(AndElimL(u.hyp('sliced')),j,b),u.hyp('bound'),u.hyp('third'))
            address=_chain(CongAdd(EqRefl(one),specialize(u,'one_mul',j)),_one_add(u,j))
            at=_subst(u,registry,'BetaAt(bb,bc,slot,b)',address,at)
            equal=apply(specialize(u,'shift',j,a,b),u.hyp('bound'),u.hyp('first'),at)
            prod=Mul(u.term('alpha'),a)
            return _chain(equal,EqSym(instantiate(Axiom('PA3'),prod)),
                CongAdd(EqRefl(prod),EqSym(specialize(u,'zero_mul',u.term('ignored')))))
        relation=introduce(t,('j','a','ignored','b'),('bound','first','second','third'),pointwise)
        alpha,gamma,u,v,w=t.terms(('alpha','gamma','u','v','w'))
        scaled=apply(specialize(t,'linearity',alpha,Zero(),gamma,
            *t.terms(('ab','ac','ab','ac','sb','sc','N','u','u','w'))),
            t.hyp('prefix_sum'),t.hyp('prefix_sum'),AndElimR(t.hyp('sliced')),relation)
        normalized=_chain(scaled,CongAdd(EqRefl(Mul(alpha,u)),specialize(t,'zero_mul',u)),instantiate(Axiom('PA3'),Mul(alpha,u)))
        whole=apply(specialize(t,'head_tail',*t.terms(('bb','bc','N','v')),Zero(),w),
            t.hyp('whole_sum'),t.hyp('zero_head'),t.hyp('affine'))
        same=_chain(whole,specialize(t,'zero_add',w))
        return _chain(CongMul(EqRefl(gamma),same),normalized)
    return introduce(s,('alpha','gamma','ab','ac','bb','bc','N','u','v'),('prefix_sum','whole_sum','zero_head','shift'),lambda t:
        eliminate(t,specialize(t,'slice_sum_exists',*t.terms(('bb','bc')),Succ(Zero()),Succ(Zero()),t.term('N')),('w',),'affine',lambda u:
            eliminate(u,u.hyp('affine'),('sb','sc'),'sliced',sliced)))


def _term_zero(s):
    from peano_lab.kernel.proofs import CongMul,EqRefl
    from peano_lab.kernel.terms import Zero
    def chosen(t):
        data=t.hyp('data');c,b=t.terms(('c','b'))
        equal=apply(specialize(t,'padding_unique',*t.terms(('cb','cc','K')),Zero(),c,Zero()),field(data,1,4),t.hyp('head'))
        return _chain(field(data,3,4),CongMul(equal,EqRefl(b)),specialize(t,'zero_mul',b))
    return introduce(s,('cb','cc','K','bb','bc','M','i','v'),('head','term'),lambda t:
        eliminate(t,t.hyp('term'),('k','c','b'),'data',chosen))


def _term_shift(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def chosen(t):
        alpha,gamma,j,k,i,a,c,b,u=t.terms(('alpha','gamma','j','k','i','a','c','b','u'));data=t.hyp('high_data')
        indices=_chain(EqSym(specialize(t,'add_succ_left',j,k)),field(data,0,4))
        indices=apply(instantiate(Axiom('PA2'),Add(j,k),i),indices)
        candidate=witness((k,a,b),conjunction(indices,t.hyp('pad_a'),field(data,2,4),EqRefl(Mul(a,b))))
        same=apply(specialize(t,'term_unique',*t.terms(A+B+('i','j','u')),Mul(a,b)),t.hyp('low_term'),candidate)
        shifted=apply(specialize(t,'shift',j,a,c),t.hyp('bound'),t.hyp('pad_a'),field(data,1,4))
        return _chain(CongMul(EqRefl(gamma),field(data,3,4)),EqSym(specialize(t,'mul_assoc',gamma,c,b)),
            CongMul(shifted,EqRefl(b)),specialize(t,'mul_assoc',alpha,a,b),CongMul(EqRefl(alpha),EqSym(same)))
    return introduce(s,P+('j','u','v'),('shift','bound','low_term','high_term'),lambda t:
        eliminate(t,t.hyp('high_term'),('k','c','b'),'high_data',lambda u:
            eliminate(u,specialize(u,'padding_exists',*u.terms(A+('j',))),('a',),'pad_a',chosen)))


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ,Zero
    def decoded(t):
        def head(u):
            i=u.term('i');si=Succ(i);ssi=Succ(si)
            bound=apply(specialize(u,'succ_le_succ',Zero(),si),specialize(u,'zero_le',si))
            term=apply(specialize(u,'diagonal_entry',*u.terms(C+B),si,*u.terms(('hb','hc')),ssi,Zero(),u.term('z')),
                AndElimL(u.hyp('high_data')),bound,u.hyp('head_value'))
            zero=apply(specialize(u,'term_zero',*u.terms(C+B+('i','z'))),u.hyp('zero_head'),term)
            zero_entry=_subst(u,registry,'BetaAt(hb,hc,0,slot)',zero,u.hyp('head_value'))
            def related(v):
                j,i,a,b=v.terms(('j','i','a','b'));si=Succ(i)
                low=apply(specialize(v,'diagonal_entry',*v.terms(A+B),i,*v.terms(('lb','lc')),si,j,a),
                    AndElimL(v.hyp('low_data')),v.hyp('bound'),v.hyp('low_entry'))
                higher=apply(specialize(v,'succ_le_succ',Succ(j),si),v.hyp('bound'))
                high=apply(specialize(v,'diagonal_entry',*v.terms(C+B),si,*v.terms(('hb','hc')),Succ(si),Succ(j),b),
                    AndElimL(v.hyp('high_data')),higher,v.hyp('high_entry'))
                lower=apply(specialize(v,'le_of_succ',j,i),v.hyp('bound'))
                return apply(specialize(v,'term_shift',*v.terms(P+('j','a','b'))),v.hyp('shift'),lower,low,high)
            relation=introduce(u,('j','a','b'),('bound','low_entry','high_entry'),related)
            return apply(specialize(u,'sum_shift',*u.terms(('alpha','gamma','lb','lc','hb','hc')),si,*u.terms(('u','v'))),
                AndElimR(u.hyp('low_data')),AndElimR(u.hyp('high_data')),zero_entry,relation)
        return eliminate(t,specialize(t,'beta_exists',*t.terms(('hb','hc')),Zero()),('z',),'head_value',head)
    return introduce(s,P+('u','v'),('zero_head','shift','low_coefficient','high_coefficient'),lambda t:
        eliminate(t,t.hyp('low_coefficient'),('lb','lc'),'low_data',lambda u:
            eliminate(u,u.hyp('high_coefficient'),('hb','hc'),'high_data',decoded)))


def prove_convolution_shift(*,limits=None):
    registry=definition_registry()
    factories={'sum_shift':lambda s:_sum_shift(s,registry),'term_zero':_term_zero,'term_shift':_term_shift,'AP037':lambda s:_root(s,registry)}
    return assemble_mixed_certificate(code='AP037',target=frozen_convolution_shift_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories,pins=convolution_shift_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
