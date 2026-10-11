"""AP034: construct an actual log/exponential sum within 2^-n of two.

Construct r=2^n, choose the proved explicit degree 18*r+2, and retain the
actual logarithm and exponential computations. Cancel only the independently
proved positive comparison powers. No infinite-series identity is assumed.
"""
from hashlib import sha256

from sqrt2_power_log_exp_witness import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,conjoin,NAMED_SOURCE as WITNESS_SOURCE,
    log_exp_witness_source_pins,
)
from sqrt2_power_log_exp_budget import NAMED_SOURCE as BUDGET_SOURCE,log_exp_budget_source_pins,COMPARISON_ARCHIVE,BOUND_ARCHIVE
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-log-exp-dyadic-witness-v1'
N='S(S(18*r))'
OUTPUTS=('r','d','ab','ac','x','p','tb','tc','h','y')
COMPUTATIONS=('d','ab','ac','x','p','tb','tc','h','y','q','a')
PARTS=('Pow(2,n,r)','~r=0','~d=0',f'NatAtanhPrefix(d,ab,ac,{N})',
    f'NatHornerValue(ab,ac,3,{N},x)',f'Pow(3,{N},p)','~p=0','~h=0','~(d*p)=0','Le(3*x,d*p)',
    f'NatScaledExpRecurrence(d*p,3*x,tb,tc,{N})','BetaAt(tb,tc,0,h)',f'Sum(tb,tc,S({N}),y)',
    'Le(r*y,(r*2)*h+h)','Le((r*2)*h,r*y+h)')
NAMED_SOURCE='forall n. exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='c7f28f686ec9b7eb26f152b6aed3eecb9aa4b32a686ba022e3ba80d363e5f620'
HELPER_SOURCES={
    'natural':'forall u v a b. IRatLe(u,0,a,v,0,b) -> Le(u*b,v*a)',
    'upper':'forall r y h p a. ~p=0 -> Le(r*(9*a),p) -> Le(y*p,(2*p+9*a)*h) -> Le(r*y,(r*2)*h+h)',
    'lower':'forall r y h q. ~q=0 -> Le(r,q) -> Le(2*(h*q),y*q+h) -> Le((r*2)*h,r*y+h)',
}
HELPER_TARGET_SHA256={'natural':'c772137606e8ba3158ab66657a64b25377bf3cad2d6eea9a068d326e4020c8f5',
    'upper':'9e8c439ad4ba0a9a834f819715c52e74914726c0570178bb2a61ac4b7cc548e6',
    'lower':'c49371c96a969e8fdc917f2087aeea7993bf0487b160e29e7c9cba625e707a89'}
WITNESS_ARCHIVE=dict(case='AP032',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-exp-witness-v1/generation-process.json.gz',
    bytes=165339,sha256='240fbc37413e065f65f91f81f5f4dd138a60538e1bbe50fc4827ac034b597496',
    raw_bytes=4429671,raw_sha256='71be0b5e4d8d45a7eeadda0ccd1460c00bda660c2a020d4a3518ce13d968b837',
    bundle_bytes=2718087,bundle_sha256='9762342212b1e76b6e2d3f640b5a1086fcd5ea3957daf4e257d97d987ef5923a',
    nodes=439,root=438,target_ast_sha256='f184312da8aa97085684bf27c6b090fe30ff3df7d6afcd251bbc4309ddb1c715')
BUDGET_ARCHIVE=dict(case='AP033',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-exp-budget-v1/generation-process.json.gz',
    bytes=37503,sha256='9a6c7dfb4ea8c9c1d77f55fd1f6ef4dd26a1c7a9c001257a00ce6cc615bffca4',
    raw_bytes=312168,raw_sha256='9eac1ab9ca8db82deaf763a1c2ad6005c58c6df18df63d91561f15765f646ad9',
    bundle_bytes=139855,bundle_sha256='36caf73a72f7b03407395d92914e1fe5d1638cd8a9a23306b08ca8ec1d4d591b',
    nodes=46,root=45,target_ast_sha256='f9b1341a43e515bdb6a1c4fc11f68e15deefecb21d6e6e05e93c1be5d19f8c43')
ARCHIVES=(WITNESS_ARCHIVE,BUDGET_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    'witness':WITNESS_SOURCE,'budget':BUDGET_SOURCE,
    'power_exists':'forall a k. exists p. Pow(a,k,p)',
    'power_nonzero':'forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0',
    'succ_ne_zero':'forall a. ~S a=0',
    'zero_mul':'forall a. 0*a=0','zero_add':'forall a. 0+a=a','one_mul':'forall a. 1*a=a',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','add_mul':'forall a b c. (a+b)*c=a*c+b*c',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(witness='AP032',budget='AP033',power_exists='AP010',power_nonzero='AP010')
ARITHMETIC=('mul_left_mono','mul_right_mono','add_left_mono','le_trans','mul_le_cancel','mul_assoc','mul_comm','mul_add')
HELPER_DEPENDENCIES={'natural':('zero_mul','zero_add'),
    'upper':ARITHMETIC+('add_mul',),'lower':ARITHMETIC,
    'AP034':('witness','budget','power_exists','power_nonzero','succ_ne_zero','natural','upper','lower','mul_comm','one_mul')}


class LogExpDyadicWitnessError(ValueError):
    """Changed actual computation, dyadic precision or comparison denominator."""


def frozen_log_exp_dyadic_witness_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LogExpDyadicWitnessError('AP034 exact finite dyadic log/exponential witness changed')
    return target


def source_contract():
    return dict(code='AP034',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precisions_including_zero=True,actual_r_equals_two_to_n_constructed=True,
        explicit_auxiliary_degree='18*r+2',all_logarithm_and_exponential_computations_constructed=True,
        positive_input_output_and_dyadic_denominators_proved=True,finite_error='abs(y/h-2)<=2^(-n)',
        comparison_powers_cancelled_only_after_nonzero_proof=True,
        fixed_approximation_program_changed=False,practical_extracted_time_claim=False,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def log_exp_dyadic_witness_source_pins():
    result=log_exp_witness_source_pins()
    for name,pin in log_exp_budget_source_pins().items():
        if name in result and result[name]!=pin:
            raise LogExpDyadicWitnessError('dyadic log/exponential source disagreement')
        result[name]=pin
    expected={
        'scripts/sqrt2_power_log_exp_witness.py':'19b9cc3b4f66db42decc879fca3df056136e02c80c86e6b5fd1369c47d5df16f',
        'scripts/sqrt2_power_log_exp_budget.py':'d312576300489ff9d35d655060d9d9056d7e8e7c79b491f312ce6f0347e57be0',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_log_exp_dyadic_witness.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise LogExpDyadicWitnessError('dyadic log/exponential source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _natural(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Zero
    def finish(t):
        u,v,a,b=t.terms(('u','v','a','b'));left=Mul(u,b);right=Mul(v,a)
        lnorm=_chain(CongAdd(EqRefl(left),specialize(t,'zero_mul',a)),instantiate(Axiom('PA3'),left))
        rnorm=_chain(CongAdd(specialize(t,'zero_mul',b),EqRefl(right)),specialize(t,'zero_add',right))
        out=_left(t,registry,field(t.hyp('bound'),2,3),Add(Mul(Zero(),b),right),lnorm)
        return _right(t,registry,out,left,rnorm)
    return introduce(s,('u','v','a','b'),('bound',),finish)


def _upper(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,nine=map(parse_term,('2','9'))
    def finish(t):
        r,y,h,p,a=t.terms(('r','y','h','p','a'));ry=Mul(r,y);base=Mul(Mul(r,two),h);err=Mul(r,Mul(nine,a))
        yp=Mul(y,p);first=Mul(two,p);second=Mul(nine,a);rhs=Mul(Add(first,second),h)
        out=apply(specialize(t,'mul_left_mono',yp,rhs,r),t.hyp('bound'))
        out=_left(t,registry,out,Mul(r,rhs),_multiplicative_equal(t,Mul(r,yp),Mul(p,ry)))
        expanded=_chain(EqSym(specialize(t,'mul_assoc',r,Add(first,second),h)),
            CongMul(specialize(t,'mul_add',r,first,second),EqRefl(h)),
            specialize(t,'add_mul',Mul(r,first),err,h),
            CongAdd(_multiplicative_equal(t,Mul(Mul(r,first),h),Mul(p,base)),EqRefl(Mul(err,h))))
        out=_right(t,registry,out,Mul(p,ry),expanded)
        tail=apply(specialize(t,'mul_right_mono',err,p,h),t.hyp('budget'))
        tail=apply(specialize(t,'add_left_mono',Mul(err,h),Mul(p,h),Mul(p,base)),tail)
        joined=apply(specialize(t,'le_trans',Mul(p,ry),Add(Mul(p,base),Mul(err,h)),Add(Mul(p,base),Mul(p,h))),out,tail)
        joined=_right(t,registry,joined,Mul(p,ry),EqSym(specialize(t,'mul_add',p,base,h)))
        return apply(specialize(t,'mul_le_cancel',p,ry,Add(base,h)),t.hyp('nonzero'),joined)
    return introduce(s,('r','y','h','p','a'),('nonzero','budget','bound'),finish)


def _lower(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two=parse_term('2')
    def finish(t):
        r,y,h,q=t.terms(('r','y','h','q'));base=Mul(Mul(r,two),h);ry=Mul(r,y);yq=Mul(y,q)
        left=Mul(two,Mul(h,q));right=Add(yq,h)
        out=apply(specialize(t,'mul_left_mono',left,right,r),t.hyp('bound'))
        out=_left(t,registry,out,Mul(r,right),_multiplicative_equal(t,Mul(r,left),Mul(q,base)))
        expanded=_chain(specialize(t,'mul_add',r,yq,h),
            CongAdd(_multiplicative_equal(t,Mul(r,yq),Mul(q,ry)),EqRefl(Mul(r,h))))
        out=_right(t,registry,out,Mul(q,base),expanded)
        tail=apply(specialize(t,'mul_right_mono',r,q,h),t.hyp('budget'))
        tail=apply(specialize(t,'add_left_mono',Mul(r,h),Mul(q,h),Mul(q,ry)),tail)
        joined=apply(specialize(t,'le_trans',Mul(q,base),Add(Mul(q,ry),Mul(r,h)),Add(Mul(q,ry),Mul(q,h))),out,tail)
        joined=_right(t,registry,joined,Mul(q,base),EqSym(specialize(t,'mul_add',q,ry,h)))
        return apply(specialize(t,'mul_le_cancel',q,base,Add(ry,h)),t.hyp('nonzero'),joined)
    return introduce(s,('r','y','h','q'),('nonzero','budget','bound'),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Add,Mul,parse_term
    one,two,nine,eighteen=map(parse_term,('1','2','9','18'))
    def computed(t):
        n,r,y,h,p,q,a=t.terms(('n','r','y','h','p','q','a'));data=t.hyp('data')
        budgets=apply(specialize(t,'budget',r,a,p,q),field(data,5,16),field(data,3,16),field(data,4,16))
        upper=apply(specialize(t,'natural',y,Add(Mul(two,p),Mul(nine,a)),h,p),field(data,14,16))
        upper=apply(specialize(t,'upper',r,y,h,p,a),field(budgets,0,4),field(budgets,2,4),upper)
        other=Add(Mul(y,q),h);lower=apply(specialize(t,'natural',two,other,one,Mul(h,q)),field(data,15,16))
        lower=_right(t,registry,lower,Mul(two,Mul(h,q)),_chain(specialize(t,'mul_comm',other,one),specialize(t,'one_mul',other)))
        lower=apply(specialize(t,'lower',r,y,h,q),field(budgets,1,4),field(budgets,3,4),lower)
        rnz=apply(instantiate(apply(specialize(t,'power_nonzero',two),specialize(t,'succ_ne_zero',one)),n,r),t.hyp('power'))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp('power'),rnz,
            *(field(data,i,16) for i in (0,1,2,3,6,8,9,10,11,12,13)),upper,lower))
    def powered(t):
        return eliminate(t,specialize(t,'witness',Mul(eighteen,t.term('r'))),COMPUTATIONS,'data',computed)
    return introduce(s,('n',),(),lambda t:
        eliminate(t,specialize(t,'power_exists',two,t.term('n')),('r',),'power',powered))


def prove_log_exp_dyadic_witness(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP034',target=frozen_log_exp_dyadic_witness_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'natural':lambda s:_natural(s,registry),'upper':lambda s:_upper(s,registry),
            'lower':lambda s:_lower(s,registry),'AP034':lambda s:_root(s,registry)},
        pins=log_exp_dyadic_witness_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
