"""AP059: finite exponential product error for arbitrary bounded arguments.

Let n=K+m and K>=2*L with x+y<=L*d. Construct the actual Cauchy table
and four sums, keeping its product head and added-argument recurrence.
For p=2^(m+1), B=L^K, the error is bounded by 2*B/p times the product
head. This is finite natural arithmetic, not an exponential addition axiom.
"""
from hashlib import sha256

from sqrt2_power_exp_product_error import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,source_registry,SANDWICH_SOURCE,PREFIX_HELPERS,
    SANDWICH_ARCHIVE,PREFIX_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_normalized_truncation import NAMED_SOURCE as TRUNCATION_SOURCE,exp_normalized_truncation_source_pins
from sqrt2_power_log_exp_witness import conjoin
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-large-argument-product-v1'
PARAMETERS=('d','x','y','L','ab','ac','bb','bc','K','m','a0','b0','p','B')
H='S(K+m)+(K+m)'
W='S(S(K+m)+(K+m))'
PREMISES=('~d=0','Le(x+y,L*d)','Le(2*L,K)',f'NatScaledExpRecurrence(d,x,ab,ac,{H})',
    f'NatScaledExpRecurrence(d,y,bb,bc,{H})','BetaAt(ab,ac,0,a0)','BetaAt(bb,bc,0,b0)','Pow(2,S m,p)','Pow(L,K,B)')
OUTPUTS=('cb','cc','u','v','s','t')
PARTS=(f'NatConvolutionPrefix(ab,ac,{W},bb,bc,{W},cb,cc,{W})',
    f'NatScaledExpRecurrence(d,x+y,cb,cc,{H})','BetaAt(cb,cc,0,a0*b0)',
    'Sum(ab,ac,S(K+m),u)','Sum(bb,bc,S(K+m),v)','Sum(cb,cc,S(K+m),s)',f'Sum(cb,cc,{W},t)',
    'Le(s,u*v)','Le(p*(u*v),p*s+2*(B*(a0*b0)))')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='7b046134336250ad84a04def0d99f230641a6586ae277d5538980db4b66aa271'
TRUNCATION_ARCHIVE=dict(case='AP057',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-normalized-truncation-v1/generation-process.json.gz',
    bytes=67570,sha256='d1c91829178a68f405c22b7a9b0eb0b6f6857195d4f0be117a05ac69e3e50856',
    raw_bytes=801026,raw_sha256='cb4089aea9cd6f88f3448559704714f3bbf25cba2f352c266a78ed901be2d525',
    bundle_bytes=422324,bundle_sha256='cc59b8f6360dec4a08b2e261e02420319cf7924020589c9285163adb763d294c',
    nodes=160,root=159,target_ast_sha256='f74987c7317766d697ca0d5792985ab700e38691f10bd6149d8c1ca141fc33b9')
ARCHIVES=(SANDWICH_ARCHIVE,PREFIX_ARCHIVE,TRUNCATION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'sandwich':SANDWICH_SOURCE,'recurrence':PREFIX_HELPERS['recurrence'],
    'head':PREFIX_HELPERS['head'],'truncation':TRUNCATION_SOURCE,
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)'}
ENDPOINT_OWNERS=dict(sandwich='AP041',recurrence='AP039',head='AP039',truncation='AP057',mul_left_mono='CV071',le_trans='CV071')
HELPER_DEPENDENCIES={'AP059':tuple(ENDPOINT_SOURCES)}


class ExpLargeArgumentProductError(ValueError):
    """Changed large-argument Cauchy product, cutoffs, powers or error bound."""


def frozen_exp_large_argument_product_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=14 or len(premises)!=9 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpLargeArgumentProductError('AP059 exact finite large-argument product error changed')
    return target


def source_contract():
    return dict(code='AP059',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=9,argument_bound='x+y<=L*d',initial_cutoff='2*L<=K',short_degree='K+m',
        long_input_degree='2*(K+m)+1',powers='p=2^(m+1); B=L^K',
        actual_convolution_recurrence_product_head_and_four_sums_constructed=True,
        finite_bounds='s<=u*v; p*(u*v)<=p*s+2*(B*(a0*b0))',
        zero_arguments_heads_and_cutoffs_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_exponential_addition=False,
        infinite_tail_or_exponential_claimed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_large_argument_product_source_pins():
    result=exp_normalized_truncation_source_pins()
    expected={'scripts/sqrt2_power_exp_normalized_truncation.py':'e8eb0a5f6c20ff2f4abbd5b2c55261484c40bb75f00e2cb9743fdc27be14d4fd',
        'scripts/sqrt2_power_exp_product_error.py':'a22255f53ef7749da9a1cc7e25d18db4fe175a4cd73a74f638bdd0cf2d7316e7',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_large_argument_product.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpLargeArgumentProductError('large-argument product source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        d,x,y,L,K,m,a0,b0,p,B,u,v,z,total=t.terms(('d','x','y','L','K','m','a0','b0','p','B','u','v','s','t'))
        n=Add(K,m);sn=Succ(n);degree=Add(sn,n);data=t.hyp('finite_sandwich')
        length=instantiate(Axiom('PA4'),sn,n)
        prefix=_subst(t,registry,'NatConvolutionPrefix(ab,ac,slot,bb,bc,slot,cb,cc,slot)',length,field(data,0,7))
        recurrence=apply(specialize(t,'recurrence',d,x,y,*t.terms(('ab','ac','bb','bc')),degree,*t.terms(('cb','cc'))),
            t.hyp('first_recurrence'),t.hyp('second_recurrence'),prefix)
        head=apply(specialize(t,'head',*t.terms(('ab','ac','bb','bc')),degree,a0,b0,*t.terms(('cb','cc'))),
            prefix,t.hyp('first_head'),t.hyp('second_head'))
        whole=_subst(t,registry,'Sum(cb,cc,slot,t)',length,field(data,4,7))
        cutoff=instantiate(Axiom('PA4'),K,m);shift=CongAdd(cutoff,EqRefl(n))
        aligned_recurrence=_subst(t,registry,'NatScaledExpRecurrence(d,x+y,cb,cc,slot)',EqSym(shift),recurrence)
        aligned_short=_subst(t,registry,'Sum(cb,cc,slot,s)',EqSym(cutoff),field(data,3,7))
        aligned_whole=_subst(t,registry,'Sum(cb,cc,S(slot),t)',EqSym(shift),whole)
        error=apply(specialize(t,'truncation',d,Add(x,y),L,*t.terms(('cb','cc')),K,Succ(m),n,Mul(a0,b0),z,total,p,B),
            t.hyp('nonzero'),t.hyp('argument'),t.hyp('threshold'),aligned_recurrence,head,aligned_short,aligned_whole,
            t.hyp('power'),t.hyp('majorant_power'))
        product=Mul(u,v);two=Succ(Succ(Zero()));upper=Add(Mul(p,z),Mul(two,Mul(B,Mul(a0,b0))))
        ordered=apply(specialize(t,'mul_left_mono',product,total,p),field(data,6,7))
        bound=apply(specialize(t,'le_trans',Mul(p,product),Mul(p,total),upper),ordered,AndElimR(error))
        return witness(t.terms(OUTPUTS),conjunction(prefix,recurrence,head,field(data,1,7),field(data,2,7),field(data,3,7),whole,field(data,5,7),bound))
    def start(t):
        length=Succ(Add(t.term('K'),t.term('m')));whole=Add(length,length)
        data=apply(specialize(t,'sandwich',*t.terms(('ab','ac','bb','bc')),length,whole),witness((length,),EqRefl(whole)))
        return eliminate(t,data,OUTPUTS,'finite_sandwich',chosen)
    return introduce(s,PARAMETERS,('nonzero','argument','threshold','first_recurrence','second_recurrence','first_head','second_head','power','majorant_power'),start)


def prove_exp_large_argument_product(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP059',target=frozen_exp_large_argument_product_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP059':lambda s:_root(s,registry)},pins=exp_large_argument_product_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
