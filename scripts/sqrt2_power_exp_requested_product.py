"""AP064: finite exponential product error at a requested dyadic precision.

For degree D=K+(L*K+n), three independently supplied sums obey the two
cross-normalized product inequalities with error 2^-n. The actual dyadic
and majorant powers are constructed, and only a proved positive auxiliary
power is cancelled. Zero heads are allowed; no analytic addition is assumed.
"""
from hashlib import sha256

from sqrt2_power_exp_supplied_large_product import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,source_registry,exp_supplied_large_product_source_pins,
    NAMED_SOURCE as PRODUCT_SOURCE,
)
from sqrt2_power_exp_requested_truncation import (
    exp_requested_truncation_source_pins,HELPER_SOURCES as TRUNCATION_HELPERS,
    BUDGET_SOURCE,BUDGET_ARCHIVE,COMPARISON_ARCHIVE,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-requested-product-v1'
M='L*K+n'
D=f'K+({M})'
H=f'S({D})+({D})'
PARAMETERS=('d','x','y','L','ab','ac','bb','bc','cb','cc','K','n','a0','b0','c0','u','v','w','r')
PREMISES=('~d=0','Le(x+y,L*d)','Le(2*L,K)',f'NatScaledExpRecurrence(d,x,ab,ac,{H})',
    f'NatScaledExpRecurrence(d,y,bb,bc,{H})',f'NatScaledExpRecurrence(d,x+y,cb,cc,{D})',
    'BetaAt(ab,ac,0,a0)','BetaAt(bb,bc,0,b0)','BetaAt(cb,cc,0,c0)',
    f'Sum(ab,ac,S({D}),u)',f'Sum(bb,bc,S({D}),v)',f'Sum(cb,cc,S({D}),w)','Pow(2,n,r)')
CONCLUSION='~r=0 /\\ (Le((a0*b0)*w,c0*(u*v)) /\\ Le(r*(c0*(u*v)),r*((a0*b0)*w)+c0*(a0*b0)))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='f0434acec36b8372e936d5c8e5f08cb7bacbc68bca03a222d3af6dfa45e2d636'
PRODUCT_ARCHIVE=dict(case='AP061',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-supplied-large-product-v1/generation-process.json.gz',
    bytes=100606,sha256='ea0ec59360908b379dd12ca4d99554ec0881e0f48a2be3049c390192fea7f236',
    raw_bytes=1881161,raw_sha256='13b3121a6d9a4a4c0a95a456b710fdb05484d4583c7b62d8c0e45c7752fcc85e',
    bundle_bytes=1093896,bundle_sha256='bd5cfc30ebecd494e85593efcf0c03cd77f252288449cc975a0d04d79cc5c861',
    nodes=255,root=254,target_ast_sha256='5b7c88d4d5aebd8dea844bd2f45f5a1966eacf6503b969bc711e7b8e1bc1163d')
TRUNCATION_ARCHIVE=dict(case='AP063',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-requested-truncation-v1/generation-process.json.gz',
    bytes=71366,sha256='72b941cbd83f1a4739ea7c0246af1f082e36d8d72bee2dfde1058d4e31fdc449',
    raw_bytes=907695,raw_sha256='0449c63f8b97b8cc810aa733fd8634fc1809bc70bc68e2a8942f2d0a29fe8bf2',
    bundle_bytes=486928,bundle_sha256='b057dee9e4adb11a462fbfd234cd9eb053c0e7275d2c3171ed29df76a3870023',
    nodes=171,root=170,target_ast_sha256='87d46a5afea3d3cb839af399daa22055d469c3506826aa7404168a3b15983873')
ARCHIVES=(PRODUCT_ARCHIVE,BUDGET_ARCHIVE,TRUNCATION_ARCHIVE,COMPARISON_ARCHIVE)
ENDPOINT_SOURCES={'product':PRODUCT_SOURCE,'budget':BUDGET_SOURCE,'error_scale':TRUNCATION_HELPERS['arithmetic'],
    'power_exists':'forall d n. exists p. Pow(d,n,p)'}
ENDPOINT_OWNERS=dict(product='AP061',budget='AP062',error_scale='AP063',power_exists='AP010')
HELPER_DEPENDENCIES={'AP064':tuple(ENDPOINT_SOURCES)}


class ExpRequestedProductError(ValueError):
    """Changed independent actual sums, requested cutoff or product error."""


def frozen_exp_requested_product_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=19 or len(premises)!=13 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRequestedProductError('AP064 exact requested-precision independent product error changed')
    return target


def source_contract():
    return dict(code='AP064',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=13,argument_bound='x+y<=L*d',initial_cutoff='2*L<=K',
        degree='D=K+(L*K+n)',input_degree='2*D+1',output_degree='D',
        requested_scale='r=2^n',requested_scale_proved_nonzero=True,
        all_three_supplied_recurrences_heads_codes_and_sums_preserved=True,
        independent_output_code_and_head_allowed=True,auxiliary_powers_constructed_not_assumed=True,
        cross_normalized_error='r*(c0*(u*v))<=r*((a0*b0)*w)+c0*(a0*b0)',
        zero_arguments_heads_and_precision_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_exponential_addition=False,
        rational_validity_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_requested_product_source_pins():
    result=exp_supplied_large_product_source_pins()
    for name,pin in exp_requested_truncation_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpRequestedProductError('requested-precision dependency source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_supplied_large_product.py':'1ac37df93cbfd74f08476c9584804824ddf64bd272b69fbd13c0fc9f589e360c',
        'scripts/sqrt2_power_exp_requested_truncation.py':'c717b1459260df08516efabcebcbca3f69ee271c2122e67f404f8ef8cb20ebc7',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_requested_product.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRequestedProductError('requested-product source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        d,x,y,L,K,n,a0,b0,c0,u,v,w,r,B,p=t.terms(('d','x','y','L','K','n','a0','b0','c0','u','v','w','r','B','p'))
        m=Add(Mul(L,K),n)
        product=apply(specialize(t,'product',d,x,y,L,*t.terms(('ab','ac','bb','bc','cb','cc')),K,m,a0,b0,c0,u,v,w,p,B),
            *(t.hyp(name) for name in ('nonzero','argument','threshold','first_recurrence','second_recurrence','third_recurrence',
                'first_head','second_head','third_head','first_sum','second_sum','third_sum','cutoff_power','majorant_power')))
        budget=apply(specialize(t,'budget',L,K,n,B,r,p),t.hyp('majorant_power'),t.hyp('precision_power'),t.hyp('cutoff_power'))
        error=apply(specialize(t,'error_scale',p,r,B,Mul(c0,Mul(a0,b0)),Mul(Mul(a0,b0),w),Mul(c0,Mul(u,v))),
            field(budget,1,3),field(budget,2,3),AndElimR(product))
        return conjunction(field(budget,0,3),AndElimL(product),error)
    def start(t):
        return eliminate(t,specialize(t,'power_exists',t.term('L'),t.term('K')),('B',),'majorant_power',lambda u:
            eliminate(u,specialize(u,'power_exists',Succ(Succ(Zero())),Succ(Add(Mul(u.term('L'),u.term('K')),u.term('n')))),
                ('p',),'cutoff_power',chosen))
    return introduce(s,PARAMETERS,('nonzero','argument','threshold','first_recurrence','second_recurrence','third_recurrence',
        'first_head','second_head','third_head','first_sum','second_sum','third_sum','precision_power'),start)


def prove_exp_requested_product(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP064',target=frozen_exp_requested_product_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP064':_root},pins=exp_requested_product_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
