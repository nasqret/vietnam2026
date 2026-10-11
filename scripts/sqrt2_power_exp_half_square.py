"""AP044: construct a positive half-argument exponential prefix and square it.

For a supplied degree-n prefix at x/d<=1, construct factorial-weighted terms
at x/(2*d) through degree 2*n+1. Their degree-n sum squared differs from the
supplied prefix by the checked finite product error. Every normalization and
sum is finite data; the theorem is not exp(log(2)/2)=sqrt(2).
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_supplied_product import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,source_registry,exp_supplied_product_source_pins,
    NAMED_SOURCE as PRODUCT_SOURCE,BOUND_ARCHIVE,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_scaled_exp_terms import NAMED_SOURCE as TERMS_SOURCE
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_exp_two_sided_continuity import _left
from sqrt2_power_log_exp_witness import conjoin
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-half-square-v1'
PARAMETERS=('d','x','bb','bc','n','b0','v','p')
H='(S n)+n'
SOURCE='NatScaledExpRecurrence(d,x,bb,bc,n)'
HALF=f'NatScaledExpRecurrence(2*d,x,ab,ac,{H})'
ERROR='Le((h*h)*v,b0*(u*u)) /\\ Le(p*(b0*(u*u)),p*((h*h)*v)+2*(b0*(h*h)))'
PREMISES=('~d=0','Le(x,d)',SOURCE,'BetaAt(bb,bc,0,b0)','Sum(bb,bc,S n,v)','Pow(2,n,p)')
OUTPUTS=('wb','wc','ab','ac','h','f','q','z','u')
PARTS=('~h=0',f'NatExpWeightTable(2*d,{H},wb,wc)',f'NatPowerWeightedPrefix(x,wb,wc,ab,ac,S({H}))',
    'BetaAt(wb,wc,0,h)','BetaAt(ab,ac,0,h)',f'Factorial({H},f)',f'Pow(2*d,{H},q)',
    'h=f*q',f'Sum(ab,ac,S({H}),z)',HALF,'Sum(ab,ac,S n,u)',ERROR)
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='a0ae3b4a0d82774e120a7703228bf12483ea7f606b04303d09fac179c58075e7'
HELPER_SOURCES={
    'scale_recurrence':'forall d x f ab ac N. NatScaledExpRecurrence(d,x,ab,ac,N) -> NatScaledExpRecurrence(f*d,f*x,ab,ac,N)',
    'two_mul':'forall a. 2*a=a+a',
    'square':'forall d x ab ac bb bc n h b0 u v p. ~d=0 -> Le(x,d) -> '+HALF+' -> '+SOURCE+' -> BetaAt(ab,ac,0,h) -> BetaAt(bb,bc,0,b0) -> Sum(ab,ac,S n,u) -> Sum(bb,bc,S n,v) -> Pow(2,n,p) -> '+ERROR,
}
HELPER_TARGET_SHA256={'scale_recurrence':'1129d494a8e89b50eb3a206e77854b349725f64921cbfdd6aec6c8f26fe37f6b',
    'two_mul':'fae211aca4ff9c81c0df272bd4b8bf0b5424b2e6aefd546c721dbbc9db0b7c1c',
    'square':'1682d5ec088bf32e4ae4253fb50900d1acfa30bfb3e91699e28d503c7b15c2b6'}
PRODUCT_ARCHIVE=dict(case='AP043',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-supplied-product-v1/generation-process.json.gz',
    bytes=101602,sha256='6566896fc481f732e2fb15fdf263c11414c36670a4eb12cdee8cbf6cb4297463',
    raw_bytes=2005405,raw_sha256='252031946c95bcf052c905407a4265c74cc7dca333bc7d9772f81406a3c32553',
    bundle_bytes=1182066,bundle_sha256='7528721c11078fdd7e425f270ff142f1629aeb9c0086f3426714067128d33823',
    nodes=278,root=277,target_ast_sha256='926558364bf250779cdac1389ddfb0966bc77936da82f1e1a24e511ccefdcc45')
ARCHIVES=(PRODUCT_ARCHIVE,EXP_ARCHIVE,BOUND_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES={'product':PRODUCT_SOURCE,'terms_exists':TERMS_SOURCE,
    'sum_exists':'forall b c N. exists n. Sum(b,c,N,n)',
    'succ_ne_zero':'forall a. ~S a=0','mul_ne_zero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_succ_left':'forall a b. (S a)*b=a*b+b','one_mul':'forall a. 1*a=a'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(product='AP043',terms_exists='CV070',sum_exists='CV003')
HELPER_DEPENDENCIES={
    'scale_recurrence':('mul_assoc','mul_comm'),
    'two_mul':('mul_succ_left','one_mul'),
    'square':('product','scale_recurrence','two_mul','succ_ne_zero','mul_ne_zero','mul_left_mono'),
    'AP044':('terms_exists','sum_exists','square','succ_ne_zero','mul_ne_zero'),
}


class ExpHalfSquareError(ValueError):
    """Changed half argument, finite scale, retained computation or square error."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','NatScaledExpRecurrence','NatExpWeightTable','NatPowerWeightedPrefix','Factorial','Pow']
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpHalfSquareError('existing factorial-weighted half-exponential definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_half_square_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=8 or len(premises)!=6 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpHalfSquareError('AP044 exact constructed half-exponential square changed')
    return target


def source_contract():
    return dict(code='AP044',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=6,nonzero_argument_denominator_required=True,argument_bound='x<=d',
        supplied_whole_argument_recurrence_head_code_and_sum_preserved=True,
        half_argument='x/(2*d)',constructed_half_degree='2*n+1',compared_sums_degree='n',
        actual_weight_table_terms_factorial_power_head_and_both_sums_constructed=True,
        half_normalization_proved_nonzero=True,independent_supplied_head_allowed=True,
        square_error='(h*h)*v<=b0*(u*u); p*(b0*(u*u))<=p*((h*h)*v)+2*(b0*(h*h))',
        zero_argument_supplied_head_and_cutoff_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_half_exponential_square_identity=False,
        logarithm_or_sqrt2_identification=False,analytic_limit_claim=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_half_square_source_pins():
    result=exp_supplied_product_source_pins()
    expected={'scripts/sqrt2_power_exp_supplied_product.py':'3a05743cbfecb01fd2a4cc907dea3e7808a5c98396b5329fd908a6ec445d905f',
        'scripts/sqrt2_power_scaled_exp_terms.py':'329c4e741b144823db7d43c018756dd19033aa5beca1505b5f4d05ae7cbe316a',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_half_square.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpHalfSquareError('half-exponential square source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _scale_recurrence(s):
    from peano_lab.kernel.proofs import CongMul,EqRefl
    from peano_lab.kernel.terms import Mul,Succ
    def entry(t):
        d,x,f,j,a,b=t.terms(('d','x','f','j','a','b'));sj=Succ(j)
        rec=apply(specialize(t,'recurrence',j,a,b),t.hyp('bound'),t.hyp('first'),t.hyp('second'))
        return _chain(_multiplicative_equal(t,Mul(Mul(sj,Mul(f,d)),b),Mul(f,Mul(Mul(sj,d),b))),
            CongMul(EqRefl(f),rec),_multiplicative_equal(t,Mul(f,Mul(x,a)),Mul(Mul(f,x),a)))
    return introduce(s,('d','x','f','ab','ac','N'),('recurrence',),lambda t:
        introduce(t,('j','a','b'),('bound','first','second'),entry))


def _two_mul(s):
    from peano_lab.kernel.proofs import CongAdd,EqRefl
    from peano_lab.kernel.terms import Succ,Zero
    return introduce(s,('a',),(),lambda t:_chain(specialize(t,'mul_succ_left',Succ(Zero()),t.term('a')),
        CongAdd(specialize(t,'one_mul',t.term('a')),EqRefl(t.term('a')))))


def _square(s,registry):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        d,x,n=t.terms(('d','x','n'));one=Succ(Zero());two=Succ(one);den=Mul(two,d)
        nonzero=apply(specialize(t,'mul_ne_zero',two,d),specialize(t,'succ_ne_zero',one),t.hyp('nonzero'))
        bound=apply(specialize(t,'mul_left_mono',x,d,two),t.hyp('argument'))
        bound=_left(t,registry,bound,den,specialize(t,'two_mul',x))
        recurrence=apply(specialize(t,'scale_recurrence',d,x,two,*t.terms(('bb','bc')),n),t.hyp('whole_recurrence'))
        recurrence=_subst(t,registry,'NatScaledExpRecurrence(2*d,slot,bb,bc,n)',specialize(t,'two_mul',x),recurrence)
        return apply(specialize(t,'product',den,x,x,*t.terms(('ab','ac','ab','ac','bb','bc','n','h','h','b0','u','u','v','p'))),
            nonzero,bound,t.hyp('half_recurrence'),t.hyp('half_recurrence'),recurrence,
            t.hyp('half_head'),t.hyp('half_head'),t.hyp('whole_head'),
            t.hyp('half_sum'),t.hyp('half_sum'),t.hyp('whole_sum'),t.hyp('power'))
    return introduce(s,('d','x','ab','ac','bb','bc','n','h','b0','u','v','p'),
        ('nonzero','argument','half_recurrence','whole_recurrence','half_head','whole_head','half_sum','whole_sum','power'),finish)


def _root(s):
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        data=t.hyp('half_data')
        error=apply(specialize(t,'square',*t.terms(('d','x','ab','ac','bb','bc','n','h','b0','u','v','p'))),
            t.hyp('nonzero'),t.hyp('argument'),field(data,9,11),t.hyp('whole_recurrence'),field(data,3,11),
            t.hyp('whole_head'),t.hyp('short_sum'),t.hyp('whole_sum'),t.hyp('power'))
        return witness(t.terms(OUTPUTS),conjunction(field(data,4,11),*(field(data,i,11) for i in (0,1,2,3,5,6,7,8,9)),t.hyp('short_sum'),error))
    def constructed(t):
        return eliminate(t,specialize(t,'sum_exists',*t.terms(('ab','ac')),Succ(t.term('n'))),('u',),'short_sum',chosen)
    def start(t):
        d,x,n=t.terms(('d','x','n'));one=Succ(Zero());two=Succ(one)
        nonzero=apply(specialize(t,'mul_ne_zero',two,d),specialize(t,'succ_ne_zero',one),t.hyp('nonzero'))
        data=apply(specialize(t,'terms_exists',Mul(two,d),x,Add(Succ(n),n)),nonzero)
        return eliminate(t,data,OUTPUTS[:-1],'half_data',constructed)
    return introduce(s,PARAMETERS,('nonzero','argument','whole_recurrence','whole_head','whole_sum','power'),start)


def prove_exp_half_square(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP044',target=frozen_exp_half_square_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'scale_recurrence':_scale_recurrence,'two_mul':_two_mul,'square':lambda s:_square(s,registry),'AP044':_root},
        pins=exp_half_square_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
