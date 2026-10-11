"""AP042: an explicit error for a finite exponential Cauchy product.

For x+y<=d and p=2^n, construct the actual added-argument table C and
the degree-n input sums u,v. Its degree-n sum s satisfies
s<=u*v and p*(u*v)<=p*s+2*(a0*b0). The input recurrences extend through
degree 2*n+1; no infinite exponential, positive head or division is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_convolution_sum_sandwich import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,convolution_sum_sandwich_source_pins,
    NAMED_SOURCE as SANDWICH_SOURCE,
)
from sqrt2_power_exp_convolution_prefix import (
    HELPER_SOURCES as PREFIX_HELPERS,exp_convolution_prefix_source_pins,source_registry,
)
from sqrt2_power_exp_truncation import NAMED_SOURCE as TRUNCATION_SOURCE
from sqrt2_power_exp_two_error_bound import TRUNCATION_ARCHIVE,BOUND_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_log_exp_witness import conjoin
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-product-error-v1'
PARAMETERS=('d','x','y','ab','ac','bb','bc','n','a0','b0','p')
H='(S n)+n'
W='S((S n)+n)'
PREMISES=('~d=0','Le(x+y,d)',f'NatScaledExpRecurrence(d,x,ab,ac,{H})',
    f'NatScaledExpRecurrence(d,y,bb,bc,{H})','BetaAt(ab,ac,0,a0)',
    'BetaAt(bb,bc,0,b0)','Pow(2,n,p)')
PARTS=(f'NatConvolutionPrefix(ab,ac,{W},bb,bc,{W},cb,cc,{W})',
    f'NatScaledExpRecurrence(d,x+y,cb,cc,{H})','BetaAt(cb,cc,0,a0*b0)',
    'Sum(ab,ac,S n,u)','Sum(bb,bc,S n,v)','Sum(cb,cc,S n,s)',f'Sum(cb,cc,{W},t)',
    'Le(s,u*v)','Le(p*(u*v),p*s+2*(a0*b0))')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> exists cb cc u v s t. '+conjoin(PARTS)
TARGET_SHA256='d0f60d98de139b481df7189728d38390769ed3a1530b9f2346887861df4da53a'
HELPER_SOURCES={}
HELPER_TARGET_SHA256={}
SANDWICH_ARCHIVE=dict(case='AP041',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-sum-sandwich-v1/generation-process.json.gz',
    bytes=74914,sha256='94a9f8881e98ce877f1c092c0f7062410b5191c641ea37aa2cb01052453a205d',
    raw_bytes=1227080,raw_sha256='e4c4bbbbc69e735aede6e8b59c344b9dea39603cb14e562de36e78367d266441',
    bundle_bytes=693200,bundle_sha256='384a22dea45672963e1b1d54ae1c6273adc3f4abb76f484684a0c11b110f6222',
    nodes=191,root=190,target_ast_sha256='f7b106d5f635ac96c28ef758a3a64c6f827875f97e9103f80b6f48ce84f679c5')
PREFIX_ARCHIVE=dict(case='AP039',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-convolution-prefix-v1/generation-process.json.gz',
    bytes=57672,sha256='02311bd2094171afc89b87bdd638ef0c0699b125264289d37771b66d46d2abd2',
    raw_bytes=917845,raw_sha256='c62a3ddc1e6647ae9b1f2a0cccf96449b96a9962ac17e72b02123c1370f8306f',
    bundle_bytes=521875,bundle_sha256='eb3be34e7edbee2ca6fb1e7702208c35ab377dde25d37f3e7ea8225883911543',
    nodes=163,root=162,target_ast_sha256='b2b010de8d9310bb2658728077ab0ed46dd768c452df5ea955fad36a1c6b40aa')
ARCHIVES=(SANDWICH_ARCHIVE,PREFIX_ARCHIVE,TRUNCATION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'sandwich':SANDWICH_SOURCE,'recurrence':PREFIX_HELPERS['recurrence'],
    'head':PREFIX_HELPERS['head'],'truncation':TRUNCATION_SOURCE,
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)'}
ENDPOINT_OWNERS=dict(sandwich='AP041',recurrence='AP039',head='AP039',truncation='CV100',
    mul_left_mono='CV071',le_trans='CV071')
HELPER_DEPENDENCIES={'AP042':tuple(ENDPOINT_SOURCES)}


class ExpProductError(ValueError):
    """Changed finite cutoff, actual product table, argument or error scale."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatConvolutionPrefix','NatScaledExpRecurrence','Pow']
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpProductError('existing finite exponential-product definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_product_error_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=11 or len(premises)!=7 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpProductError('AP042 exact finite exponential product error changed')
    return target


def source_contract():
    return dict(code='AP042',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=7,nonzero_argument_denominator_required=True,argument_bound='x+y<=d',
        both_actual_input_recurrences_and_heads_preserved=True,
        long_input_degree='2*n+1',short_sum_degree='n',actual_cutoff_power='p=2^n',
        actual_convolution_table_recurrence_head_and_four_sums_constructed=True,
        product_head='a0*b0',natural_error='s<=u*v; p*(u*v)<=p*s+2*(a0*b0)',
        zero_arguments_heads_and_cutoff_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_exponential_addition=False,
        rational_validity_claimed=False,analytic_limit_claim=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_product_error_source_pins():
    result=convolution_sum_sandwich_source_pins()
    for name,pin in exp_convolution_prefix_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpProductError('finite exponential product error source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_convolution_sum_sandwich.py':'0112ed3d93c924f2d457160bc9a412cddf72ef5f3fc078d257bbf11fb4cbd1cc',
        'scripts/sqrt2_power_exp_convolution_prefix.py':'6da35fd211ca68878d29b7a269f4123d7368520fdca5994fbce290822d72e64c',
        'scripts/sqrt2_power_exp_truncation.py':'a54f7da9d8918d8bb7028a6694c9318aaae2cd04040f3d4513e5c4d09ff826c0',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_product_error.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpProductError('finite exponential product error source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimR,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        d,x,y,n,a0,b0,p,u,v,z,total=t.terms(('d','x','y','n','a0','b0','p','u','v','s','t'))
        L=Succ(n);H=Add(L,n);data=t.hyp('finite_sandwich')
        length=instantiate(Axiom('PA4'),L,n)
        prefix=_subst(t,registry,'NatConvolutionPrefix(ab,ac,slot,bb,bc,slot,cb,cc,slot)',length,field(data,0,7))
        recurrence=apply(specialize(t,'recurrence',*t.terms(('d','x','y','ab','ac','bb','bc')),H,*t.terms(('cb','cc'))),
            t.hyp('first_recurrence'),t.hyp('second_recurrence'),prefix)
        head=apply(specialize(t,'head',*t.terms(('ab','ac','bb','bc')),H,a0,b0,*t.terms(('cb','cc'))),
            prefix,t.hyp('first_head'),t.hyp('second_head'))
        whole=_subst(t,registry,'Sum(cb,cc,slot,t)',length,field(data,4,7))
        error=apply(specialize(t,'truncation',d,Add(x,y),*t.terms(('cb','cc')),n,n,Mul(a0,b0),z,total,p),
            t.hyp('nonzero'),t.hyp('argument'),recurrence,head,field(data,3,7),whole,t.hyp('power'))
        product=Mul(u,v);two=Succ(Succ(Zero()));upper=Add(Mul(p,z),Mul(two,Mul(a0,b0)))
        ordered=apply(specialize(t,'mul_left_mono',product,total,p),field(data,6,7))
        bound=apply(specialize(t,'le_trans',Mul(p,product),Mul(p,total),upper),ordered,AndElimR(error))
        return witness(t.terms(('cb','cc','u','v','s','t')),conjunction(prefix,recurrence,head,
            field(data,1,7),field(data,2,7),field(data,3,7),whole,field(data,5,7),bound))
    def start(t):
        L=Succ(t.term('n'));M=Add(L,L)
        data=apply(specialize(t,'sandwich',*t.terms(('ab','ac','bb','bc')),L,M),witness((L,),EqRefl(M)))
        return eliminate(t,data,('cb','cc','u','v','s','t'),'finite_sandwich',chosen)
    return introduce(s,PARAMETERS,('nonzero','argument','first_recurrence','second_recurrence','first_head','second_head','power'),start)


def prove_exp_product_error(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP042',target=frozen_exp_product_error_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP042':lambda s:_root(s,registry)},pins=exp_product_error_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
