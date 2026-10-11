"""AP043: finite product error against an independently supplied prefix.

All three codes, heads and sums remain the caller's actual data. The Cauchy
table is internal: existing finite value independence identifies its short
sum with the supplied added-argument sum after cross multiplication. Zero
heads are allowed, so this does not assert rational validity or a limit law.
"""
from hashlib import sha256

from sqrt2_power_exp_product_error import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,source_registry,exp_product_error_source_pins,
    NAMED_SOURCE as PRODUCT_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_sample_independence import HELPER_SOURCES as INDEPENDENCE_HELPERS
from sqrt2_power_exp_sample_all_precision import INDEPENDENCE_ARCHIVE
from sqrt2_power_exp_two_error_bound import HELPER_SOURCES as HORIZON_HELPERS
from sqrt2_power_exp_rational_two_error import TWO_ERROR_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-supplied-product-v1'
PARAMETERS=('d','x','y','ab','ac','bb','bc','cb','cc','n','a0','b0','c0','u','v','w','p')
PREMISES=('~d=0','Le(x+y,d)','NatScaledExpRecurrence(d,x,ab,ac,(S n)+n)',
    'NatScaledExpRecurrence(d,y,bb,bc,(S n)+n)','NatScaledExpRecurrence(d,x+y,cb,cc,n)',
    'BetaAt(ab,ac,0,a0)','BetaAt(bb,bc,0,b0)','BetaAt(cb,cc,0,c0)',
    'Sum(ab,ac,S n,u)','Sum(bb,bc,S n,v)','Sum(cb,cc,S n,w)','Pow(2,n,p)')
CONCLUSION='Le((a0*b0)*w,c0*(u*v)) /\\ Le(p*(c0*(u*v)),p*((a0*b0)*w)+2*(c0*(a0*b0)))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='926558364bf250779cdac1389ddfb0966bc77936da82f1e1a24e511ccefdcc45'
HELPER_SOURCES={'arithmetic':'forall p a h s v w. h*s=a*w -> Le(s,v) -> Le(p*v,p*s+2*a) -> Le(a*w,h*v) /\\ Le(p*(h*v),p*(a*w)+2*(h*a))'}
HELPER_TARGET_SHA256={'arithmetic':'c91133edc359494ee6cf22561c0b03a1d7b1789c4ffcbacd8582d37794ed6347'}
PRODUCT_ARCHIVE=dict(case='AP042',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-product-error-v1/generation-process.json.gz',
    bytes=90608,sha256='730180d0ff1e316b87f2c04a28fe852544d6c726a55d9003de31adc15fa9d67d',
    raw_bytes=1714253,raw_sha256='98fd5eaab8d38f430c660c2e1d4321e8487f9a0e5b84966983f0abaf57bc5d97',
    bundle_bytes=997802,bundle_sha256='69283fcae5315a56746e333c6d6b9e3162d423ea3c9dc974a3218d0776975369',
    nodes=243,root=242,target_ast_sha256='d0f60d98de139b481df7189728d38390769ed3a1530b9f2346887861df4da53a')
ARCHIVES=(PRODUCT_ARCHIVE,INDEPENDENCE_ARCHIVE,TWO_ERROR_ARCHIVE,BOUND_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES={'product':PRODUCT_SOURCE,'same_value':INDEPENDENCE_HELPERS['same_value'],
    'restrict':HORIZON_HELPERS['restrict'],
    'sum_unique':'forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_add':'forall a b c. a*(b+c)=a*b+a*c'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(product='AP042',same_value='AP005',restrict='CV101',sum_unique='CV003')
HELPER_DEPENDENCIES={'arithmetic':('mul_left_mono','mul_assoc','mul_comm','mul_add'),
    'AP043':('product','same_value','restrict','sum_unique','arithmetic')}


class ExpSuppliedProductError(ValueError):
    """Changed actual supplied values, finite degree, scale or product error."""


def frozen_exp_supplied_product_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=17 or len(premises)!=12 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSuppliedProductError('AP043 exact independently supplied exponential product error changed')
    return target


def source_contract():
    return dict(code='AP043',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=12,nonzero_argument_denominator_required=True,argument_bound='x+y<=d',
        all_three_supplied_recurrences_heads_codes_and_sums_preserved=True,
        independent_output_code_and_head_allowed=True,input_degree='2*n+1',output_degree='n',
        all_supplied_sums_degree='n',actual_cutoff_power='p=2^n',
        internal_convolution_identified_by_cross_value_equality=True,
        zero_arguments_heads_and_cutoff_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_exponential_addition=False,
        rational_validity_claimed=False,analytic_limit_claim=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_supplied_product_source_pins():
    result=exp_product_error_source_pins()
    expected={'scripts/sqrt2_power_exp_product_error.py':'a22255f53ef7749da9a1cc7e25d18db4fe175a4cd73a74f638bdd0cf2d7316e7',
        'scripts/sqrt2_power_exp_sample_independence.py':'e6ec0523040135408adbadfc5cf46351f4682bd6a3b1f564c08263f8cb692187',
        'scripts/sqrt2_power_exp_two_error_bound.py':'df3b14dbae9c98536321540ac43a1fd804550da8bb8a26a5bb0664f2a24e92d1',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_supplied_product.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSuppliedProductError('supplied exponential product source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        p,a,h,z,v,w=t.terms(('p','a','h','s','v','w'));two=Succ(Succ(Zero()))
        lower=apply(specialize(t,'mul_left_mono',z,v,h),t.hyp('lower'))
        lower=_left(t,registry,lower,Mul(h,v),t.hyp('identity'))
        upper=apply(specialize(t,'mul_left_mono',Mul(p,v),Add(Mul(p,z),Mul(two,a)),h),t.hyp('upper'))
        left=_multiplicative_equal(t,Mul(h,Mul(p,v)),Mul(p,Mul(h,v)))
        right=_chain(specialize(t,'mul_add',h,Mul(p,z),Mul(two,a)),
            CongAdd(_multiplicative_equal(t,Mul(h,Mul(p,z)),Mul(p,Mul(h,z))),
                _multiplicative_equal(t,Mul(h,Mul(two,a)),Mul(two,Mul(h,a)))),
            CongAdd(CongMul(EqRefl(p),t.hyp('identity')),EqRefl(Mul(two,Mul(h,a)))))
        upper=_left(t,registry,upper,Mul(h,Add(Mul(p,z),Mul(two,a))),left)
        upper=_right(t,registry,upper,Mul(p,Mul(h,v)),right)
        return conjunction(lower,upper)
    return introduce(s,('p','a','h','s','v','w'),('identity','lower','upper'),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        d,x,y,n,a0,b0,c0,u,v,w,p,z=t.terms(('d','x','y','n','a0','b0','c0','u','v','w','p','z'))
        data=t.hyp('constructed');L=Succ(n);H=Add(L,n);argument=Add(x,y);head=Mul(a0,b0)
        first=apply(specialize(t,'sum_unique',*t.terms(('ab','ac')),L,*t.terms(('u1','u'))),field(data,3,9),t.hyp('first_sum'))
        second=apply(specialize(t,'sum_unique',*t.terms(('bb','bc')),L,*t.terms(('v1','v'))),field(data,4,9),t.hyp('second_sum'))
        equal=CongMul(first,second)
        recurrence=apply(specialize(t,'restrict',d,argument,*t.terms(('eb','ec')),n,H),witness((L,),EqRefl(H)),field(data,1,9))
        same=apply(specialize(t,'same_value',d,d,argument,argument,n,*t.terms(('eb','ec','cb','cc')),head,c0,z,w),
            t.hyp('nonzero'),t.hyp('nonzero'),EqRefl(Mul(argument,d)),t.hyp('argument'),t.hyp('argument'),
            recurrence,t.hyp('third_recurrence'),field(data,2,9),t.hyp('third_head'),field(data,5,9),t.hyp('third_sum'))
        lower=_right(t,registry,field(data,7,9),z,equal)
        upper=_left(t,registry,field(data,8,9),Add(Mul(p,z),Mul(Succ(Succ(Zero())),head)),CongMul(EqRefl(p),equal))
        return apply(specialize(t,'arithmetic',p,head,c0,z,Mul(u,v),w),same,lower,upper)
    def start(t):
        data=apply(specialize(t,'product',*t.terms(('d','x','y','ab','ac','bb','bc','n','a0','b0','p'))),
            t.hyp('nonzero'),t.hyp('argument'),t.hyp('first_recurrence'),t.hyp('second_recurrence'),
            t.hyp('first_head'),t.hyp('second_head'),t.hyp('power'))
        return eliminate(t,data,('eb','ec','u1','v1','z','total'),'constructed',chosen)
    return introduce(s,PARAMETERS,('nonzero','argument','first_recurrence','second_recurrence','third_recurrence',
        'first_head','second_head','third_head','first_sum','second_sum','third_sum','power'),start)


def prove_exp_supplied_product(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP043',target=frozen_exp_supplied_product_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP043':lambda s:_root(s,registry)},
        pins=exp_supplied_product_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
