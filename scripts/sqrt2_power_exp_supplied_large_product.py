"""AP061: general-argument product error for three independently supplied sums.

Retain every supplied code, head and sum. AP059 constructs an internal Cauchy
table; AP060 identifies its value with the supplied output without a unit-
argument restriction. All comparison is by cross multiplication, including
zero heads. No infinite-product law or rational validity is assumed.
"""
from hashlib import sha256

from sqrt2_power_exp_large_argument_product import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,source_registry,NAMED_SOURCE as PRODUCT_SOURCE,H,
    exp_large_argument_product_source_pins,BOUND_ARCHIVE,
)
from sqrt2_power_exp_recurrence_independence import (
    NAMED_SOURCE as INDEPENDENCE_SOURCE,exp_recurrence_independence_source_pins,
)
from sqrt2_power_exp_two_error_bound import HELPER_SOURCES as HORIZON_HELPERS
from sqrt2_power_exp_rational_two_error import TWO_ERROR_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-supplied-large-product-v1'
PARAMETERS=('d','x','y','L','ab','ac','bb','bc','cb','cc','K','m','a0','b0','c0','u','v','w','p','B')
PREMISES=('~d=0','Le(x+y,L*d)','Le(2*L,K)',f'NatScaledExpRecurrence(d,x,ab,ac,{H})',
    f'NatScaledExpRecurrence(d,y,bb,bc,{H})','NatScaledExpRecurrence(d,x+y,cb,cc,K+m)',
    'BetaAt(ab,ac,0,a0)','BetaAt(bb,bc,0,b0)','BetaAt(cb,cc,0,c0)',
    'Sum(ab,ac,S(K+m),u)','Sum(bb,bc,S(K+m),v)','Sum(cb,cc,S(K+m),w)','Pow(2,S m,p)','Pow(L,K,B)')
CONCLUSION='Le((a0*b0)*w,c0*(u*v)) /\\ Le(p*(c0*(u*v)),p*((a0*b0)*w)+2*(B*(c0*(a0*b0))))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='5b7c88d4d5aebd8dea844bd2f45f5a1966eacf6503b969bc711e7b8e1bc1163d'
HELPER_SOURCES={'arithmetic':'forall p B a h s v w. h*s=a*w -> Le(s,v) -> Le(p*v,p*s+2*(B*a)) -> Le(a*w,h*v) /\\ Le(p*(h*v),p*(a*w)+2*(B*(h*a)))'}
HELPER_TARGET_SHA256={'arithmetic':'a9597826fe0d6cbfe3cdcfc125b7a108c85075f93a7ecb9fd39d9519ce58f2e8'}
PRODUCT_ARCHIVE=dict(case='AP059',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-large-argument-product-v1/generation-process.json.gz',
    bytes=96826,sha256='8c371a7d2f982bbb2b2d87352cff09642733d09999e0bf0b9b32d796e978eab6',
    raw_bytes=1798691,raw_sha256='cf9fb81ea3d60868d0597d5cd1831b2f906cd0a36ee70c1e35fa5eabeed1ae04',
    bundle_bytes=1042764,bundle_sha256='67a11f71c4bf3e2627a1a9312bcd6c03448719f660047da1f33d10d257b59445',
    nodes=248,root=247,target_ast_sha256='7b046134336250ad84a04def0d99f230641a6586ae277d5538980db4b66aa271')
INDEPENDENCE_ARCHIVE=dict(case='AP060',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-recurrence-independence-v1/generation-process.json.gz',
    bytes=20503,sha256='11527328b71d3e1396fa162123e08b6b35c35a6f1dd24c52e93887123939f457',
    raw_bytes=216008,raw_sha256='c8106c1f53e50d849635c76b238330f6ba1065ec10b9622c87020f451b7bb1b6',
    bundle_bytes=94980,bundle_sha256='87bd710ef99048e7cafb38dc72a681d8ea931d8054616880a6d04f87f4ecc748',
    nodes=37,root=36,target_ast_sha256='7beddbf0b9c56535b34cc9097c02c1dd441a5ba9cb163ee87131584651dfc897')
ARCHIVES=(PRODUCT_ARCHIVE,INDEPENDENCE_ARCHIVE,TWO_ERROR_ARCHIVE,BOUND_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES={'product':PRODUCT_SOURCE,'same_value':INDEPENDENCE_SOURCE,'restrict':HORIZON_HELPERS['restrict'],
    'sum_unique':'forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_add':'forall a b c. a*(b+c)=a*b+a*c'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(product='AP059',same_value='AP060',restrict='CV101',sum_unique='CV003')
HELPER_DEPENDENCIES={'arithmetic':('mul_left_mono','mul_assoc','mul_comm','mul_add'),
    'AP061':('product','same_value','restrict','sum_unique','arithmetic')}


class ExpSuppliedLargeProductError(ValueError):
    """Changed actual independent codes, argument bound, cutoff or product error."""


def frozen_exp_supplied_large_product_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=20 or len(premises)!=14 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSuppliedLargeProductError('AP061 exact independently supplied general-argument product error changed')
    return target


def source_contract():
    return dict(code='AP061',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=14,nonzero_argument_denominator_required=True,argument_bound='x+y<=L*d',
        initial_cutoff='2*L<=K',input_degree='2*(K+m)+1',output_degree='K+m',
        powers='p=2^(m+1); B=L^K',
        all_three_supplied_recurrences_heads_codes_and_sums_preserved=True,
        independent_output_code_and_head_allowed=True,unit_argument_restriction_required=False,
        internal_convolution_identified_by_unrestricted_cross_value_equality=True,
        zero_arguments_heads_and_cutoffs_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_exponential_addition=False,
        rational_validity_claimed=False,analytic_limit_claim=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_supplied_large_product_source_pins():
    result=exp_large_argument_product_source_pins()
    for name,pin in exp_recurrence_independence_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpSuppliedLargeProductError('independent recurrence source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_large_argument_product.py':'497f6b57379a24976757048f0ef10bf01d7b8e0a01bf4744cf9eb3c8a9ac39e1',
        'scripts/sqrt2_power_exp_recurrence_independence.py':'683487ceef52ea2116f955d71e185356cf15f9d82f7a27daaf9ec5871c4ca149',
        'scripts/sqrt2_power_exp_two_error_bound.py':'df3b14dbae9c98536321540ac43a1fd804550da8bb8a26a5bb0664f2a24e92d1',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_supplied_large_product.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSuppliedLargeProductError('supplied large-product source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        p,B,a,h,z,v,w=t.terms(('p','B','a','h','s','v','w'));two=Succ(Succ(Zero()))
        allowance=Mul(two,Mul(B,a));scaled_allowance=Mul(two,Mul(B,Mul(h,a)))
        lower=apply(specialize(t,'mul_left_mono',z,v,h),t.hyp('lower'))
        lower=_left(t,registry,lower,Mul(h,v),t.hyp('identity'))
        upper=apply(specialize(t,'mul_left_mono',Mul(p,v),Add(Mul(p,z),allowance),h),t.hyp('upper'))
        left=_multiplicative_equal(t,Mul(h,Mul(p,v)),Mul(p,Mul(h,v)))
        right=_chain(specialize(t,'mul_add',h,Mul(p,z),allowance),
            CongAdd(_multiplicative_equal(t,Mul(h,Mul(p,z)),Mul(p,Mul(h,z))),
                _multiplicative_equal(t,Mul(h,allowance),scaled_allowance)),
            CongAdd(CongMul(EqRefl(p),t.hyp('identity')),EqRefl(scaled_allowance)))
        upper=_left(t,registry,upper,Mul(h,Add(Mul(p,z),allowance)),left)
        upper=_right(t,registry,upper,Mul(p,Mul(h,v)),right)
        return conjunction(lower,upper)
    return introduce(s,('p','B','a','h','s','v','w'),('identity','lower','upper'),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        d,x,y,K,m,a0,b0,c0,u,v,w,p,B,z=t.terms(('d','x','y','K','m','a0','b0','c0','u','v','w','p','B','z'))
        data=t.hyp('constructed');n=Add(K,m);length=Succ(n);degree=Add(length,n);argument=Add(x,y);head=Mul(a0,b0)
        first=apply(specialize(t,'sum_unique',*t.terms(('ab','ac')),length,*t.terms(('u1','u'))),field(data,3,9),t.hyp('first_sum'))
        second=apply(specialize(t,'sum_unique',*t.terms(('bb','bc')),length,*t.terms(('v1','v'))),field(data,4,9),t.hyp('second_sum'))
        equal=CongMul(first,second)
        recurrence=apply(specialize(t,'restrict',d,argument,*t.terms(('eb','ec')),n,degree),witness((length,),EqRefl(degree)),field(data,1,9))
        same=apply(specialize(t,'same_value',d,d,argument,argument,n,*t.terms(('eb','ec','cb','cc')),head,c0,z,w),
            t.hyp('nonzero'),t.hyp('nonzero'),EqRefl(Mul(argument,d)),recurrence,t.hyp('third_recurrence'),
            field(data,2,9),t.hyp('third_head'),field(data,5,9),t.hyp('third_sum'))
        lower=_right(t,registry,field(data,7,9),z,equal)
        upper=_left(t,registry,field(data,8,9),Add(Mul(p,z),Mul(Succ(Succ(Zero())),Mul(B,head))),CongMul(EqRefl(p),equal))
        return apply(specialize(t,'arithmetic',p,B,head,c0,z,Mul(u,v),w),same,lower,upper)
    def start(t):
        data=apply(specialize(t,'product',*t.terms(('d','x','y','L','ab','ac','bb','bc','K','m','a0','b0','p','B'))),
            t.hyp('nonzero'),t.hyp('argument'),t.hyp('threshold'),t.hyp('first_recurrence'),t.hyp('second_recurrence'),
            t.hyp('first_head'),t.hyp('second_head'),t.hyp('power'),t.hyp('majorant_power'))
        return eliminate(t,data,('eb','ec','u1','v1','z','total'),'constructed',chosen)
    return introduce(s,PARAMETERS,('nonzero','argument','threshold','first_recurrence','second_recurrence','third_recurrence',
        'first_head','second_head','third_head','first_sum','second_sum','third_sum','power','majorant_power'),start)


def prove_exp_supplied_large_product(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP061',target=frozen_exp_supplied_large_product_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP061':lambda s:_root(s,registry)},
        pins=exp_supplied_large_product_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
