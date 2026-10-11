"""AP039: construct the finite convolution as an exponential prefix.

The constructed Cauchy table has head a0*b0, argument x+y and exact factorial
normalization at every retained index. Its sum is actually constructed, but
is NOT asserted equal to the product of the two truncated input sums.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_convolution_recurrence import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,canonical,json_hash,
    NAMED_SOURCE as RECURRENCE_SOURCE,exp_convolution_recurrence_source_pins,
    CONVOLUTION_ARCHIVE,source_registry,
)
from sqrt2_power_exp_recurrence_normalization import NAMED_SOURCE as NORMALIZATION_SOURCE,exp_recurrence_normalization_source_pins
from sqrt2_power_convolution_associative import COMM_ARCHIVE
from sqrt2_power_convolution_commutative import HELPER_SOURCES as COMM_HELPERS
from sqrt2_power_natural_convolution import HELPER_SOURCES as CONVOLUTION_HELPERS
from sqrt2_power_euler_product import coefficient
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_log_exp_witness import conjoin
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-convolution-prefix-v1'
PARAMETERS=('d','x','y','ab','ac','bb','bc','N','a0','b0')
A,B=('ab','ac','S N'),('bb','bc','S N')
FIRST='NatScaledExpRecurrence(d,x,ab,ac,N)'
SECOND='NatScaledExpRecurrence(d,y,bb,bc,N)'
PREFIX='NatConvolutionPrefix(ab,ac,S N,bb,bc,S N,cb,cc,S N)'
RECURRENCE='NatScaledExpRecurrence(d,x+y,cb,cc,N)'
NORMALIZATION='forall j t f p q. Le(j,N) -> BetaAt(cb,cc,j,t) -> Factorial(j,f) -> Pow(d,j,p) -> Pow(x+y,j,q) -> (t*f)*p=(a0*b0)*q'
PARTS=(PREFIX,RECURRENCE,'BetaAt(cb,cc,0,a0*b0)','Sum(cb,cc,S N,s)','('+NORMALIZATION+')')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+FIRST+' -> '+SECOND+' -> BetaAt(ab,ac,0,a0) -> BetaAt(bb,bc,0,b0) -> exists cb cc s. '+conjoin(PARTS)
TARGET_SHA256='b2b010de8d9310bb2658728077ab0ed46dd768c452df5ea955fad36a1c6b40aa'
HELPER_SOURCES={
    'zero_coefficient':'forall ab ac L bb bc M a0 b0 w. BetaZeroExtend(ab,ac,L,0,a0) -> BetaZeroExtend(bb,bc,M,0,b0) -> NatConvolutionCoefficient(ab,ac,L,bb,bc,M,0,w) -> w=a0*b0',
    'recurrence':'forall d x y ab ac bb bc N cb cc. '+FIRST+' -> '+SECOND+' -> '+PREFIX+' -> '+RECURRENCE,
    'head':'forall ab ac bb bc N a0 b0 cb cc. '+PREFIX+' -> BetaAt(ab,ac,0,a0) -> BetaAt(bb,bc,0,b0) -> BetaAt(cb,cc,0,a0*b0)',
}
HELPER_TARGET_SHA256={
    'zero_coefficient':'ca864dfcec75820d299d79c0f71eb24febd9bf8b5d13abf30229bb0ec86a854c',
    'recurrence':'290b2e1cca37d327c6e8c38f7dda3964096f84a99bbe38fedbc84290a4d0d01a',
    'head':'8edc3c5f0f53d008c2f25c30fbcdc8c1354ed213ceb8560fe0f234834058d9c2'}
RECURRENCE_ARCHIVE=dict(case='AP038',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-convolution-recurrence-v1/generation-process.json.gz',
    bytes=52480,sha256='e2130f230b3a4755cc1919caff75916cf0f4bf71c6f8925fafdb90725806eaf7',
    raw_bytes=707521,raw_sha256='52abb65f4017e7e0d6a3ce25cc038d7833042077c4bc647b0b3f698d53ef8b9f',
    bundle_bytes=392744,bundle_sha256='eb3ee35d22bb87a6c5ca3963644da32ed3fc677db0ee176185b032bb6c3910e2',
    nodes=147,root=146,target_ast_sha256='1d0487d27421420580ddbc9e31618cfe3a90ef13648ea8c02a25c5be0e87f7e0')
NORMALIZATION_ARCHIVE=dict(case='AP035',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-recurrence-normalization-v1/generation-process.json.gz',
    bytes=33222,sha256='7442c7a1680e0f3db7022cfbec8287a22c40e48f824117578888c348755cf297',
    raw_bytes=257515,raw_sha256='e12a51b6a6b812e14910642cc71f9544335c332ac788e2872f2e834c451b22bf',
    bundle_bytes=108842,bundle_sha256='9cca6b66aa1a938f46ea6ec4dc47503a586239318bc48d616d5d68f48b8ee4bc',
    nodes=36,root=35,target_ast_sha256='9b47638db02d23a2bbc549793da14c71bc39b811db179fadbf3410e4723bbdf6')
ARCHIVES=(RECURRENCE_ARCHIVE,NORMALIZATION_ARCHIVE,CONVOLUTION_ARCHIVE,COMM_ARCHIVE)
ENDPOINT_SOURCES={
    'zero_le':'forall a. Le(0,a)','le_refl':'forall a. Le(a,a)',
    'succ_le_succ':'forall a b. Le(a,b) -> Le(S a,S b)',
    'le_succ':'forall a b. Le(a,b) -> Le(a,S b)',
    'beta_exists':'forall b c i. exists a. BetaAt(b,c,i,a)',
    'sum_exists':'forall b c N. exists n. Sum(b,c,N,n)',
    'term_unique':'forall ab ac L bb bc M i j t s. PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,s) -> t=s',
    'diagonal_entry':'forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)',
    'prefix_exists':CONVOLUTION_HELPERS['prefix_exists'],'prefix_entry':CONVOLUTION_HELPERS['prefix_entry'],
    'sum_one':COMM_HELPERS['sum_one'],'coefficient_recurrence':RECURRENCE_SOURCE,'normalization':NORMALIZATION_SOURCE,
}
ENDPOINT_OWNERS={name:'CV003' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(sum_one='CV010',coefficient_recurrence='AP038',normalization='AP035')
HELPER_DEPENDENCIES={
    'zero_coefficient':('beta_exists','le_refl','diagonal_entry','term_unique','sum_one'),
    'recurrence':('le_succ','succ_le_succ','prefix_entry','coefficient_recurrence'),
    'head':('beta_exists','zero_le','succ_le_succ','prefix_entry','zero_coefficient'),
    'AP039':('prefix_exists','sum_exists','recurrence','head','normalization'),
}


class ExpConvolutionPrefixError(ValueError):
    """Changed actual product table, initial value, cutoff or normalization."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatConvolutionPrefix','NatScaledExpRecurrence','Factorial','Pow']
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpConvolutionPrefixError('existing factorial/convolution definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_convolution_prefix_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=10 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpConvolutionPrefixError('AP039 exact constructed exponential product prefix changed')
    return target


def source_contract():
    return dict(code='AP039',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,actual_convolution_prefix_and_sum_constructed=True,
        supplied_recurrences_and_heads_preserved=True,product_head='a0*b0',output_argument_numerator='x+y',
        finite_output_length='N+1',all_index_factorial_normalization_proved=True,
        zero_denominator_arguments_heads_and_horizon_allowed=True,
        truncated_output_sum_equals_product_of_input_sums=False,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        analytic_exponential_addition=False,analytic_limit_claim=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_convolution_prefix_source_pins():
    result=exp_convolution_recurrence_source_pins()
    for name,pin in exp_recurrence_normalization_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpConvolutionPrefixError('finite exponential product source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_recurrence_normalization.py':'8e9cc376cfd192274f4f28efcab5f138fedc3a968a5a741e9ef55341ef65a82f',
        'scripts/sqrt2_power_exp_convolution_recurrence.py':'363a4bbe814f00bc40656974bfee314128b4d50d5e8c5685c8914e8c04424845',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_convolution_prefix.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpConvolutionPrefixError('finite exponential product source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _zero_coefficient(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,Axiom,EqRefl
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def chosen(t):
        zero=Zero();one=Succ(zero);a,b,z=t.terms(('a0','b0','z'))
        term=apply(specialize(t,'diagonal_entry',*t.terms(('ab','ac','L','bb','bc','M')),zero,
            *t.terms(('db','dc')),one,zero,z),AndElimL(t.hyp('data')),specialize(t,'le_refl',one),t.hyp('entry'))
        candidate=witness((zero,a,b),conjunction(instantiate(Axiom('PA3'),zero),t.hyp('first_head'),t.hyp('second_head'),EqRefl(Mul(a,b))))
        same=apply(specialize(t,'term_unique',*t.terms(('ab','ac','L','bb','bc','M')),zero,zero,z,Mul(a,b)),term,candidate)
        summed=apply(specialize(t,'sum_one',*t.terms(('db','dc','w','z'))),AndElimR(t.hyp('data')),t.hyp('entry'))
        return _chain(summed,same)
    return introduce(s,('ab','ac','L','bb','bc','M','a0','b0','w'),('first_head','second_head','coefficient'),lambda t:
        eliminate(t,t.hyp('coefficient'),('db','dc'),'data',lambda u:
            eliminate(u,specialize(u,'beta_exists',*u.terms(('db','dc')),Zero()),('z',),'entry',chosen)))


def _recurrence(s):
    from peano_lab.kernel.terms import Succ
    def entry(t):
        N,j,a,b=t.terms(('N','j','a','b'));sn=Succ(N);sj=Succ(j)
        args=t.terms(('ab','ac'))+(sn,)+t.terms(('bb','bc'))+(sn,)+t.terms(('cb','cc'))+(sn,)
        low_bound=apply(specialize(t,'le_succ',sj,N),t.hyp('bound'))
        high_bound=apply(specialize(t,'succ_le_succ',sj,N),t.hyp('bound'))
        low=apply(specialize(t,'prefix_entry',*(args+(j,a))),t.hyp('prefix'),low_bound,t.hyp('low_entry'))
        high=apply(specialize(t,'prefix_entry',*(args+(sj,b))),t.hyp('prefix'),high_bound,t.hyp('high_entry'))
        return apply(specialize(t,'coefficient_recurrence',*t.terms(('d','x','y','ab','ac','bb','bc','N','j','a','b'))),
            t.hyp('first_recurrence'),t.hyp('second_recurrence'),t.hyp('bound'),low,high)
    return introduce(s,('d','x','y','ab','ac','bb','bc','N','cb','cc'),('first_recurrence','second_recurrence','prefix'),lambda t:
        introduce(t,('j','a','b'),('bound','low_entry','high_entry'),entry))


def _head(s,registry):
    from peano_lab.kernel.proofs import AndIntro,OrIntroL
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        N=t.term('N');sn=Succ(N);zero=Zero()
        bound=apply(specialize(t,'succ_le_succ',zero,N),specialize(t,'zero_le',N))
        args=t.terms(('ab','ac'))+(sn,)+t.terms(('bb','bc'))+(sn,)
        coeff=apply(specialize(t,'prefix_entry',*(args+t.terms(('cb','cc'))+(sn,zero,t.term('v')))),
            t.hyp('prefix'),bound,t.hyp('entry'))
        same=apply(specialize(t,'zero_coefficient',*(args+t.terms(('a0','b0','v')))),
            OrIntroL(AndIntro(bound,t.hyp('first_head'))),OrIntroL(AndIntro(bound,t.hyp('second_head'))),coeff)
        return _subst(t,registry,'BetaAt(cb,cc,0,slot)',same,t.hyp('entry'))
    return introduce(s,('ab','ac','bb','bc','N','a0','b0','cb','cc'),('prefix','first_head','second_head'),lambda t:
        eliminate(t,specialize(t,'beta_exists',*t.terms(('cb','cc')),Zero()),('v',),'entry',chosen))


def _root(s):
    from peano_lab.kernel.terms import Add,Mul,Succ
    def chosen(t):
        d,x,y,N,a0,b0=t.terms(('d','x','y','N','a0','b0'))
        rec=apply(specialize(t,'recurrence',*t.terms(('d','x','y','ab','ac','bb','bc','N','cb','cc'))),
            t.hyp('first_recurrence'),t.hyp('second_recurrence'),t.hyp('prefix'))
        head=apply(specialize(t,'head',*t.terms(('ab','ac','bb','bc','N','a0','b0','cb','cc'))),
            t.hyp('prefix'),t.hyp('first_head'),t.hyp('second_head'))
        norm=apply(specialize(t,'normalization',d,Add(x,y),*t.terms(('cb','cc')),N,Mul(a0,b0)),rec,head)
        return witness(t.terms(('cb','cc','s')),conjunction(t.hyp('prefix'),rec,head,t.hyp('sum'),norm))
    def prefix(t):
        return eliminate(t,specialize(t,'sum_exists',*t.terms(('cb','cc')),Succ(t.term('N'))),('s',),'sum',chosen)
    return introduce(s,PARAMETERS,('first_recurrence','second_recurrence','first_head','second_head'),lambda t:
        eliminate(t,specialize(t,'prefix_exists',*t.terms(('ab','ac')),Succ(t.term('N')),
            *t.terms(('bb','bc')),Succ(t.term('N')),Succ(t.term('N'))),('cb','cc'),'prefix',prefix))


def prove_exp_convolution_prefix(*,limits=None):
    registry=definition_registry()
    factories={'zero_coefficient':_zero_coefficient,'recurrence':_recurrence,'head':lambda s:_head(s,registry),'AP039':_root}
    return assemble_mixed_certificate(code='AP039',target=frozen_exp_convolution_prefix_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories,pins=exp_convolution_prefix_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
